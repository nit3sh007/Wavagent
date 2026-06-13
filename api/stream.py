import json
import asyncio
import re
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import threading

from agent.azure_client import azure_classify, azure_chat

router = APIRouter()

AGENT_ICONS = {
    "orchestrator": "🎯",
    "news": "📰",
    "social": "💬",
    "wiki": "📚",
    "synthesis": "🧬",
    "decision": "⚡",
    "classifier": "🔍",
}

OBVIOUS_CHAT_PATTERNS = [
    r'^hi+\b', r'^hey+\b', r'^hello+\b', r'^howdy', r'^yo\b',
    r'how are you', r"how'?s it going", r"what'?s up",
    r'^thanks?\b', r'thank you', r'^bye+$', r'^goodbye',
    r'who are you', r'what can you do', r'what do you do',
    r'^ok(ay)?$', r'^sup$', r'good (morning|afternoon|evening|night)',
    r'^tell me a joke', r'^are you (ok|okay|alright|fine|there)',
    r'what are you doing', r"what'?re you (up to|doing)",
    r'how do you work', r'what is your purpose',
    r'^are you (real|human|alive|sentient)',
    r'^do you (like|love|hate)',
    r'^can you (talk|chat|speak)',
    r'^nice to meet you', r'^pleased to meet you',
    r'^how old are you', r'^where are you from',
    r'^what is your favorite', r"^what'?s your favorite",
]


class StreamRequest(BaseModel):
    query: str
    country: Optional[str] = None


def make_sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def is_obvious_chat(q: str) -> bool:
    return any(re.search(p, q) for p in OBVIOUS_CHAT_PATTERNS)


@router.post("/api/agent/stream")
async def stream_intelligence(request: StreamRequest):
    query = (request.query or request.country or "").strip()
    query_lower = query.lower().strip()

    if len(query) < 2 or not any(c.isalpha() for c in query):
        async def _err():
            yield make_sse({
                "type": "error",
                "message": "Please enter a meaningful query — e.g. 'India', 'Tesla', 'Ukraine war'.",
                "timestamp": datetime.now().isoformat(),
            })
        return StreamingResponse(_err(), media_type="text/event-stream",
                                  headers={"Cache-Control": "no-cache"})

    # Fast regex pre-filter (instant, free) — fall back to LLM for ambiguous cases
    intent = "chat" if is_obvious_chat(query_lower) else azure_classify(query)

    if intent == "chat":
        async def _chat():
            yield make_sse({
                "type": "step", "agent": "orchestrator", "icon": "💬",
                "message": "Casual message detected — responding directly, no agents needed",
                "timestamp": datetime.now().isoformat(),
            })
            try:
                reply = azure_chat(
                    messages=[
                        {"role": "system", "content": (
                            "You are WavAgent, a friendly real-time intelligence assistant. "
                            "Reply naturally and briefly in 1-2 sentences, then invite the user "
                            "to ask about a country, company, person, or news topic."
                        )},
                        {"role": "user", "content": query},
                    ],
                    max_tokens=80,
                )
                if not reply or len(reply) < 5:
                    raise ValueError("empty reply")
            except Exception:
                reply = (
                    "I'm doing great, thanks! Ask me about a country, company, "
                    "person, or news topic — like 'India', 'Tesla', or 'Ukraine war'."
                )

            yield make_sse({
                "type": "chat",
                "message": reply,
                "timestamp": datetime.now().isoformat(),
            })
            yield make_sse({"type": "done"})

        return StreamingResponse(_chat(), media_type="text/event-stream",
                                  headers={"Cache-Control": "no-cache"})

    async def event_generator():
        event_buffer = []
        buffer_lock = threading.Lock()
        agent_done = threading.Event()

        def emit(agent: str, message: str):
            event = {
                "type": "step",
                "agent": agent,
                "icon": AGENT_ICONS.get(agent, "🤖"),
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
            with buffer_lock:
                event_buffer.append(event)

        result_container = {}
        error_container = {}

        def run_agent():
            try:
                from agent.agent import run_intelligence_agent
                result = run_intelligence_agent(query=query, emit=emit)
                result_container.update(result)
            except Exception as e:
                error_container["error"] = str(e)
                emit("orchestrator", f"❌ Fatal error: {str(e)[:100]}")
            finally:
                agent_done.set()

        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()

        yield make_sse({
            "type": "start",
            "query": query,
            "message": f"Deploying intelligence agents for: '{query}'...",
            "timestamp": datetime.now().isoformat(),
        })

        while not agent_done.is_set() or event_buffer:
            with buffer_lock:
                pending = event_buffer.copy()
                event_buffer.clear()
            for event in pending:
                yield make_sse(event)
            if not pending:
                yield make_sse({"type": "ping", "timestamp": datetime.now().isoformat()})
            await asyncio.sleep(0.1)

        with buffer_lock:
            pending = event_buffer.copy()
            event_buffer.clear()
        for event in pending:
            yield make_sse(event)

        if error_container:
            yield make_sse({
                "type": "error",
                "message": error_container.get("error", "Unknown error"),
                "timestamp": datetime.now().isoformat(),
            })
        else:
            data = result_container.get("data", {})
            data["generated_at"] = datetime.now().isoformat()
            yield make_sse({
                "type": "complete",
                "data": data,
                "timestamp": datetime.now().isoformat(),
            })

        yield make_sse({"type": "done"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )