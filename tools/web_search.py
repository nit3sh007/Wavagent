from langchain.tools import tool
from tavily import TavilyClient
import os


def get_tavily_client():
    return TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def search_country_news(query: str) -> str:
    """
    Search for latest news and information about a country.
    Use this to find current events, trending topics, and news.
    Input should be a specific search query like 'Japan latest news 2026'
    """
    try:
        client = get_tavily_client()
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )

        results = response.get("results", [])

        if not results:
            return "No results found. Try a different search query."

        formatted = []
        for r in results:
            formatted.append(f"""
Source: {r.get('url', 'unknown')}
Title: {r.get('title', 'unknown')}
Content: {r.get('content', 'No content')[:400]}
""")

        # Also include Tavily's answer if available
        answer = response.get("answer", "")
        prefix = f"Summary: {answer}\n\n---\n" if answer else ""

        return prefix + "\n---\n".join(formatted)

    except Exception as e:
        return f"Search failed: {str(e)}. Try alternative search terms."