SYSTEM_PROMPT = """You are GeoAgent, an autonomous web intelligence agent.
Your job is to research any country and build a comprehensive intelligence report."""
REPORT_FORMAT = """
Analyze the research data above and produce a JSON report for the country.

OUTPUT ONLY THIS JSON (replace example values with real data from research):

{
    "country": "India",
    "trending_topics": [
        {
            "topic": "actual topic from research",
            "sentiment": "positive",
            "summary": "actual summary from research data"
        }
    ],
    "key_events": [
        {
            "title": "actual event title from research",
            "summary": "actual event description from research",
            "source": "actual source name",
            "url": "actual url from research"
        }
    ],
    "social_sentiment": "positive",
    "summary": "Write 2-3 actual sentences summarizing what you found in the research data above.",
    "sources_visited": ["Wikipedia", "RSS News", "Reddit", "Web Search"]
}

DO NOT copy the example values above. Replace every field with REAL data from the research.
DO NOT output anything except the JSON object.
DO NOT include thinking or explanation.
"""