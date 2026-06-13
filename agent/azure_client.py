import os
import re
from openai import AzureOpenAI


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").replace("/models", ""),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-10-21",
        timeout=10.0,
        max_retries=0,
    )


def azure_chat(messages: list, max_tokens: int = 500) -> str:
    client = get_client()
    converted = []
    for m in messages:
        if hasattr(m, 'role') and hasattr(m, 'content'):
            converted.append({"role": m.role, "content": m.content})
        elif isinstance(m, dict):
            converted.append(m)
        else:
            converted.append({"role": "user", "content": str(m)})

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "Phi-4-mini-instruct"),
        messages=converted,
        max_tokens=max_tokens,
        timeout=10.0,
    )
    raw = response.choices[0].message.content or ""
    return _extract_answer(raw.strip())



def azure_classify(query: str) -> str:
    """
    Classify intent as 'chat' or 'research'.
    Uses few-shot examples + temperature=0 for reliable format-following
    with small instruct models.
    """
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "Phi-4-mini-instruct"),
            messages=[
                {"role": "system", "content": (
                    "You are a strict classifier. Respond with ONLY one word: "
                    "CHAT or RESEARCH. No punctuation, no explanation."
                )},
                {"role": "user", "content": "Message: hi\nAnswer:"},
                {"role": "assistant", "content": "CHAT"},
                {"role": "user", "content": "Message: how are you\nAnswer:"},
                {"role": "assistant", "content": "CHAT"},
                {"role": "user", "content": "Message: tell me a joke\nAnswer:"},
                {"role": "assistant", "content": "CHAT"},
                {"role": "user", "content": "Message: India\nAnswer:"},
                {"role": "assistant", "content": "RESEARCH"},
                {"role": "user", "content": "Message: Tesla earnings\nAnswer:"},
                {"role": "assistant", "content": "RESEARCH"},
                {"role": "user", "content": f"Message: {query}\nAnswer:"},
            ],
            max_tokens=5,
            temperature=0,
            timeout=8.0,
        )
        raw = (response.choices[0].message.content or "").strip().upper()
        return "chat" if "CHAT" in raw else "research"
    except Exception:
        return "research"

def _extract_answer(text: str) -> str:
    """Clean up model output — handles both plain and reasoning-style responses."""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]

    meta = [
        'user asked', 'user request', 'so i need', 'i need to',
        'let me', 'i should', 'we need to', 'the question', 'the conversation',
        'note that', 'note:', 'guidelines', 'it seems', 'this means',
        "i'll", 'i will', 'the task', 'they want', 'the prompt',
        'certified professionals', 'seek certified', 'sensitive topics',
        'must produce', 'i must', 'should produce',
    ]

    clean = [
        p for p in paragraphs
        if len(p) > 30 and not any(m in p.lower() for m in meta)
    ]

    if clean:
        answer = clean[-1]
        answer = re.sub(
            r'^(answer|summary|response|result|here|here are|here is)[:\s]+',
            '', answer, flags=re.IGNORECASE
        ).strip()
        sentences = re.split(r'(?<=[.!?])\s+', answer)
        return ' '.join(sentences[:3]).strip()

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 25]
    return ' '.join(sentences[-2:]) if sentences else text[:300]