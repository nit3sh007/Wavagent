import time
import threading
from typing import Callable
from agent.news_agent import NewsAgent
from agent.social_agent import SocialAgent
from agent.wiki_agent import WikiAgent
from agent.synthesis_agent import SynthesisAgent
from agent.decision_agent import DecisionAgent


# Adaptive strategy profiles per query type
ADAPTIVE_PROFILES = {
    "breaking": {
        "skip_wiki": True,
        "boost_news": True,
        "max_news_results": 8,
        "description": "Breaking news mode — maximizing speed and news coverage",
    },
    "country": {
        "skip_wiki": False,
        "boost_news": True,
        "max_news_results": 6,
        "description": "Country intelligence mode — full pipeline active",
    },
    "company": {
        "skip_wiki": False,
        "boost_news": True,
        "max_news_results": 6,
        "description": "Company intelligence mode — financial signals prioritized",
    },
    "person": {
        "skip_wiki": False,
        "boost_news": True,
        "max_news_results": 5,
        "description": "Person intelligence mode — biography + recent activity",
    },
    "crisis": {
        "skip_wiki": True,
        "boost_news": True,
        "max_news_results": 8,
        "description": "Crisis mode — speed and breadth maximized",
    },
    "research": {
        "skip_wiki": False,
        "boost_news": False,
        "max_news_results": 4,
        "description": "Deep research mode — Wikipedia + context prioritized",
    },
    "topic": {
        "skip_wiki": False,
        "boost_news": True,
        "max_news_results": 6,
        "description": "Topic analysis mode — multi-source synthesis",
    },
}


def detect_profile(query: str, query_type: str) -> str:
    q = query.lower()
    if any(w in q for w in ["breaking", "just now", "live", "happening now"]):
        return "breaking"
    if any(w in q for w in ["war", "attack", "crisis", "disaster", "emergency"]):
        return "crisis"
    if any(w in q for w in ["research", "history", "background", "explain", "what is"]):
        return "research"
    return query_type if query_type in ADAPTIVE_PROFILES else "topic"


class AdaptiveOrchestrator:
    """
    Adaptive orchestrator that changes agent behavior based on query type.
    Implements: parallel execution, adaptive profiles, decision layer.
    """

    def __init__(self, emit: Callable):
        self.emit = emit
        self.steps = []

    def _tracked_emit(self, agent: str, message: str):
        step = {"agent": agent, "message": message, "timestamp": time.time()}
        self.steps.append(step)
        self.emit(agent, message)

    def run(self, query: str, query_type: str = "topic",
            entities: dict = None, strategies: list = None,
            language: str = "en") -> dict:

        start_time = time.time()
        entities = entities or {"primary": query, "keywords": []}
        strategies = strategies or [query, f"{query} latest news 2026"]

        # Detect adaptive profile
        profile_key = detect_profile(query, query_type)
        profile = ADAPTIVE_PROFILES.get(profile_key, ADAPTIVE_PROFILES["topic"])

        self._tracked_emit("orchestrator", f"🚀 AdaptiveOrchestrator activated")
        self._tracked_emit("orchestrator", f"🔍 Query: '{query[:60]}'")
        self._tracked_emit("orchestrator", f"🏷️ Type: {query_type.upper()} | Profile: {profile_key.upper()}")
        self._tracked_emit("orchestrator", f"⚙️ Mode: {profile['description']}")
        self._tracked_emit("orchestrator", f"🧩 Spawning parallel sub-agents...")

        skip_wiki = profile.get("skip_wiki", False)
        if skip_wiki:
            self._tracked_emit("orchestrator", f"⚡ Wiki skipped (speed mode active)")
            self._tracked_emit("orchestrator", f"   → NewsAgent + SocialAgent running in parallel")
        else:
            self._tracked_emit("orchestrator", f"   → NewsAgent + SocialAgent + WikiAgent in parallel")

        # Result containers
        news_result = {}
        social_result = {}
        wiki_result = {}
        errors = {}

        # Create agents
        news_agent = NewsAgent(lambda a, m: self._tracked_emit(a, m))
        social_agent = SocialAgent(lambda a, m: self._tracked_emit(a, m))
        wiki_agent = WikiAgent(lambda a, m: self._tracked_emit(a, m))

        def run_news():
            try:
                news_result.update(news_agent.run(query))
            except Exception as e:
                errors["news"] = str(e)
                self._tracked_emit("news", f"❌ Failed: {str(e)[:80]}")

        def run_social():
            try:
                social_result.update(social_agent.run(query))
            except Exception as e:
                errors["social"] = str(e)
                self._tracked_emit("social", f"❌ Failed: {str(e)[:80]}")

        def run_wiki():
            if skip_wiki:
                wiki_result["overview"] = "Skipped in speed mode"
                wiki_result["facts"] = []
                return
            try:
                wiki_result.update(wiki_agent.run(query))
            except Exception as e:
                errors["wiki"] = str(e)
                self._tracked_emit("wiki", f"❌ Failed: {str(e)[:80]}")

        # Launch in parallel
        threads = [
            threading.Thread(target=run_news),
            threading.Thread(target=run_social),
            threading.Thread(target=run_wiki),
        ]

        self._tracked_emit("orchestrator", f"⚡ All agents running in parallel...")
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        elapsed_parallel = round(time.time() - start_time, 1)
        self._tracked_emit("orchestrator", f"✅ Parallel phase complete in {elapsed_parallel}s")

        # Synthesis
        self._tracked_emit("orchestrator", f"🔬 Handing off to SynthesisAgent...")
        synthesis_agent = SynthesisAgent(lambda a, m: self._tracked_emit(a, m))
        report = synthesis_agent.run(query, news_result, social_result, wiki_result)

        # Decision layer
        self._tracked_emit("orchestrator", f"⚡ Running DecisionAgent...")
        decision_agent = DecisionAgent(lambda a, m: self._tracked_emit(a, m))
        decision = decision_agent.run(query, report, query_type)

        # Merge decision into report
        report["decision"] = decision
        report["query_type"] = query_type
        report["adaptive_profile"] = profile_key
        report["query"] = query

        # Metadata
        total_time = round(time.time() - start_time, 1)
        report["agent_metadata"] = {
            "total_time_seconds": total_time,
            "agents_used": ["NewsAgent", "SocialAgent", "WikiAgent", "SynthesisAgent", "DecisionAgent"],
            "parallel_execution": True,
            "total_steps": len(self.steps),
            "adaptive_profile": profile_key,
            "errors": errors,
            "language": language,
        }
        report["agent_steps"] = len(self.steps)
        report["language"] = language

        self._tracked_emit("orchestrator",
            f"🎯 Complete! Time: {total_time}s | Steps: {len(self.steps)} | "
            f"Risk: {decision['risk']['level'].upper()}")

        return report
