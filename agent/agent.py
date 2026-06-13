"""
WavAgent v2 - Universal Intelligence Agent
Handles: countries, companies, people, topics, breaking news
"""

from datetime import datetime

from agent.classifier_agent import QueryClassifierAgent
from agent.adaptive_orchestrator import AdaptiveOrchestrator


def run_geo_agent(country: str, language: str = "en", emit=None) -> dict:
    return run_intelligence_agent(query=country, language=language, emit=emit)


def run_intelligence_agent(query: str, language: str = "en", emit=None) -> dict:
    """
    Universal intelligence agent.
    If `emit` is provided (e.g. from the streaming endpoint), it's used
    for real-time step updates. Otherwise falls back to local logging.
    """
    try:
        steps_log = []

        def internal_emit(agent: str, message: str):
            steps_log.append({"agent": agent, "message": message})
            print(f"[{agent.upper()}] {message}")
            if emit is not None:
                emit(agent, message)  # forward to external stream

        classifier = QueryClassifierAgent()
        classification = classifier.classify(query)

        internal_emit(
            "orchestrator",
            f"🔍 Query classified: {classification['display_type']} "
            f"{classification['icon']}"
        )
        internal_emit(
            "orchestrator",
            f"📋 Strategies: {len(classification['strategies'])} search paths"
        )

        orchestrator = AdaptiveOrchestrator(internal_emit)

        report = orchestrator.run(
            query=query,
            query_type=classification["type"],
            entities=classification["entities"],
            strategies=classification["strategies"],
            language=language,
        )

        report["generated_at"] = datetime.now().isoformat()
        report["classification"] = classification
        report["steps_log"] = steps_log

        return {"success": True, "data": report}

    except Exception as e:
        print(f"[WavAgent] Error: {e}")
        if emit is not None:
            emit("orchestrator", f"❌ Fatal error: {str(e)[:100]}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "query": query, "trending_topics": [], "key_events": [],
                "social_sentiment": "neutral", "summary": f"Agent failed: {e}",
                "sources_visited": [], "agent_steps": 0,
                "language": language, "decision": None,
            },
        }