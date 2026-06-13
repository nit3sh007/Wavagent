import re
import time
from tools.news_rss import get_country_news
from tools.web_search import search_country_news


class NewsAgent:
    """Specialized agent for gathering news from multiple sources."""

    def __init__(self, emit):
        self.emit = emit  # callback to stream updates

    def run(self, country: str) -> dict:
        self.emit("news", f"📰 NewsAgent starting research on {country}...")
        results = {}
        start = time.time()

        # RSS News
        self.emit("news", f"📡 Fetching RSS feeds for {country}...")
        try:
            rss_data = get_country_news.invoke(country)
            items = self._parse_news(rss_data)
            results["rss"] = items
            self.emit("news", f"✅ RSS: Found {len(items)} articles from local news feeds")
        except Exception as e:
            results["rss"] = []
            self.emit("news", f"⚠️ RSS feeds unavailable, trying web search...")

        # Web Search
        self.emit("news", f"🌐 Web searching: '{country} latest news 2026'...")
        try:
            web_data = search_country_news.invoke(f"{country} latest news 2026")
            web_items = self._parse_web(web_data)
            results["web"] = web_items
            self.emit("news", f"✅ Web: Found {len(web_items)} results from Tavily search")
        except Exception as e:
            results["web"] = []
            self.emit("news", f"⚠️ Web search failed: {str(e)[:50]}")

        # Deep dive on top topic
        all_titles = [i["title"] for i in results.get("rss", [])[:2] + results.get("web", [])[:2]]
        if all_titles:
            top_topic = all_titles[0]
            self.emit("news", f"🔍 Deep diving into top story: '{top_topic[:60]}...'")
            try:
                deep = search_country_news.invoke(f"{country} {top_topic[:50]}")
                deep_items = self._parse_web(deep)
                results["deep_dive"] = deep_items[:2]
                self.emit("news", f"✅ Deep dive: Found {len(deep_items)} additional sources")
            except Exception:
                results["deep_dive"] = []

        elapsed = round(time.time() - start, 1)
        total = len(results.get("rss", [])) + len(results.get("web", []))
        self.emit("news", f"🏁 NewsAgent complete in {elapsed}s — {total} articles gathered")
        return results

    def _parse_news(self, text: str) -> list:
        items = []
        blocks = re.split(r'\n---\n', text)
        for block in blocks[:6]:
            title = re.search(r'Title:\s*(.+)', block)
            url = re.search(r'URL:\s*(https?://\S+)', block)
            summary = re.search(r'Summary:\s*(.+)', block)
            if title and len(title.group(1).strip()) > 10:
                items.append({
                    "title": title.group(1).strip()[:120],
                    "url": url.group(1).strip() if url else "",
                    "summary": summary.group(1).strip()[:200] if summary else "",
                    "source": "RSS News",
                })
        return items

    def _parse_web(self, text: str) -> list:
        items = []
        blocks = re.split(r'\n---\n', text)
        for block in blocks[:6]:
            title = re.search(r'Title:\s*(.+)', block)
            url = re.search(r'URL:\s*(https?://\S+)', block)
            content = re.search(r'Content:\s*(.+)', block)
            if title and len(title.group(1).strip()) > 10:
                items.append({
                    "title": title.group(1).strip()[:120],
                    "url": url.group(1).strip() if url else "",
                    "summary": content.group(1).strip()[:200] if content else "",
                    "source": "Web Search",
                })
        return items
