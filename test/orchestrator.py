import time
import threading
from typing import Callable
from agent.news_agent import NewsAgent
from agent.social_agent import SocialAgent
from agent.wiki_agent import WikiAgent
from agent.synthesis_agent import SynthesisAgent


class OrchestratorAgent:
    """
    Master orchestrator that spawns and coordinates sub-agents.
    Runs NewsAgent, SocialAgent, WikiAgent in parallel,
    then SynthesisAgent combines all findings.
    """

    def __init__(self, emit: Callable):
        self.emit = emit
        self.steps = []

    def _tracked_emit(self, agent: str, message: str):
        """Track all agent steps and emit to stream."""
        step = {"agent": agent, "message": message, "timestamp": time.time()}
        self.steps.append(step)
        self.emit(agent, message)

    def run(self, country: str, language: str = "en") -> dict:
        start_time = time.time()

        self._tracked_emit("orchestrator", f"🚀 OrchestratorAgent activated for: {country}")
        self._tracked_emit("orchestrator", f"🧩 Spawning 3 parallel sub-agents...")
        self._tracked_emit("orchestrator", f"   → NewsAgent: will search RSS + Web + Deep dive")
        self._tracked_emit("orchestrator", f"   → SocialAgent: will analyze Reddit + sentiment")
        self._tracked_emit("orchestrator", f"   → WikiAgent: will research Wikipedia + global news")

        # Results containers
        news_result = {}
        social_result = {}
        wiki_result = {}
        errors = {}

        # Create sub-agents with tracked emitters
        news_agent = NewsAgent(lambda a, m: self._tracked_emit(a, m))
        social_agent = SocialAgent(lambda a, m: self._tracked_emit(a, m))
        wiki_agent = WikiAgent(lambda a, m: self._tracked_emit(a, m))

        # Run all 3 agents in parallel using threads
        def run_news():
            try:
                news_result.update(news_agent.run(country))
            except Exception as e:
                errors["news"] = str(e)
                self._tracked_emit("news", f"❌ NewsAgent failed: {str(e)[:100]}")

        def run_social():
            try:
                social_result.update(social_agent.run(country))
            except Exception as e:
                errors["social"] = str(e)
                self._tracked_emit("social", f"❌ SocialAgent failed: {str(e)[:100]}")

        def run_wiki():
            try:
                wiki_result.update(wiki_agent.run(country))
            except Exception as e:
                errors["wiki"] = str(e)
                self._tracked_emit("wiki", f"❌ WikiAgent failed: {str(e)[:100]}")

        # Launch threads
        threads = [
            threading.Thread(target=run_news),
            threading.Thread(target=run_social),
            threading.Thread(target=run_wiki),
        ]

        self._tracked_emit("orchestrator", f"⚡ All 3 agents running in parallel...")

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        elapsed_parallel = round(time.time() - start_time, 1)
        self._tracked_emit("orchestrator", f"✅ All agents completed in {elapsed_parallel}s")
        self._tracked_emit("orchestrator", f"🔬 Handing off to SynthesisAgent...")

        # Synthesis agent combines everything
        synthesis_agent = SynthesisAgent(lambda a, m: self._tracked_emit(a, m))
        report = synthesis_agent.run(country, news_result, social_result, wiki_result)

        # Add agent metadata
        total_time = round(time.time() - start_time, 1)
        report["agent_metadata"] = {
            "total_time_seconds": total_time,
            "agents_used": ["NewsAgent", "SocialAgent", "WikiAgent", "SynthesisAgent"],
            "parallel_execution": True,
            "total_steps": len(self.steps),
            "errors": errors,
            "language": language,
        }
        report["agent_steps"] = len(self.steps)
        report["language"] = language

        self._tracked_emit("orchestrator", f"🎯 Intelligence report complete! Total time: {total_time}s | Steps: {len(self.steps)}")

        return report
