from langchain.tools import tool
import feedparser
import requests
import os

# Country to news RSS feed mapping
COUNTRY_NEWS_FEEDS = {
    "india": [
        "https://feeds.feedburner.com/ndtvnews-top-stories",
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://www.thehindu.com/news/feeder/default.rss",
    ],
    "japan": [
        "https://www3.nhk.or.jp/rss/news/cat0.xml",
        "https://japantoday.com/feed",
    ],
    "usa": [
        "https://feeds.npr.org/1001/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    ],
    "uk": [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://www.theguardian.com/uk/rss",
    ],
    "brazil": [
        "https://feeds.folha.uol.com.br/folha/mundo/rss091.xml",
    ],
    "germany": [
        "https://www.dw.com/en/news/rss-feed/s-9097",
    ],
    "france": [
        "https://www.france24.com/en/rss",
    ],
    "china": [
        "https://www.chinadaily.com.cn/rss/world_rss.xml",
    ],
    "australia": [
        "https://www.abc.net.au/news/feed/51120/rss.xml",
    ],
    "canada": [
        "https://www.cbc.ca/cmlink/rss-topstories",
    ],
    "russia": [
        "https://tass.com/rss/v2.xml",
    ],
    "south korea": [
        "https://koreajoongangdaily.joins.com/rss/feeds/topstories.xml",
    ],
}

# Global fallback feeds
GLOBAL_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.cnn.com/rss/edition_world.rss",
    "https://feeds.reuters.com/Reuters/worldNews",
]

@tool
def get_country_news(country: str) -> str:
    """..."""
    try:
        country_lower = country.lower().strip()
        feeds = COUNTRY_NEWS_FEEDS.get(country_lower, GLOBAL_FEEDS)
        all_articles = []

        for feed_url in feeds[:2]:
            try:
                response = requests.get(feed_url,
                    headers={"User-Agent": "WavAgent/1.0"}, timeout=10)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    query_words = [w for w in country_lower.split() if len(w) > 2]
                    
                    for entry in feed.entries[:10]:
                        title = entry.get('title', '')
                        summary = entry.get('summary', '')
                        
                        # RELEVANCE CHECK — only include if query word appears
                        combined = (title + " " + summary).lower()
                        is_relevant = any(w in combined for w in query_words)
                        
                        # For known country feeds, include all; 
                        # for global feeds, require relevance
                        if country_lower in COUNTRY_NEWS_FEEDS or is_relevant:
                            import re
                            clean_summary = re.sub('<[^<]+?>', '', summary)[:400]
                            all_articles.append(f"""
Title: {title}
Summary: {clean_summary}
URL: {entry.get('link', '')}
""")
            except Exception:
                continue

        # Only fall back to global if we have a real country/topic
        if not all_articles and len(country_lower) > 3:
            for feed_url in GLOBAL_FEEDS[:2]:
                try:
                    response = requests.get(feed_url,
                        headers={"User-Agent": "WavAgent/1.0"}, timeout=10)
                    if response.status_code == 200:
                        feed = feedparser.parse(response.content)
                        query_words = [w for w in country_lower.split() if len(w) > 3]
                        for entry in feed.entries[:15]:
                            title = entry.get('title', '').lower()
                            if any(w in title for w in query_words):
                                all_articles.append(f"""
Title: {entry.get('title', '')}
Summary: {entry.get('summary', '')[:400]}
URL: {entry.get('link', '')}
""")
                except Exception:
                    continue

        if not all_articles:
            return f"No relevant news found for '{country}'."

        return f"Latest news for '{country}':\n\n" + "\n---\n".join(all_articles[:6])

    except Exception as e:
        return f"News fetch failed: {str(e)}"
@tool
def search_global_news(query: str) -> str:
    """
    Search global news feeds for a specific topic or country.
    Use this as fallback when country specific news is not available.
    Input should be a search query like 'Brazil economy 2026'
    """
    try:
        all_articles = []
        
        for feed_url in GLOBAL_FEEDS:
            try:
                response = requests.get(
                    feed_url,
                    headers={"User-Agent": "WavAgent/1.0"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    
                    query_words = query.lower().split()
                    
                    for entry in feed.entries[:15]:
                        title = entry.get('title', '').lower()
                        summary = entry.get('summary', '').lower()
                        
                        # Check if any query word matches
                        if any(word in title or word in summary 
                               for word in query_words):
                            all_articles.append(f"""
Title: {entry.get('title', '')}
Summary: {entry.get('summary', '')[:400]}
URL: {entry.get('link', '')}
""")
                            
            except Exception:
                continue
        
        if not all_articles:
            return f"No global news found for query: {query}"
            
        return f"Global news for '{query}':\n\n" + "\n---\n".join(all_articles[:6])
        
    except Exception as e:
        return f"Global news search failed: {str(e)}"