import re
import time
import requests
from tools.news_rss import search_global_news


WIKI_STRIP_PATTERNS = [
    r'\s+latest news.*$',
    r'\s+economic outlook.*$',
    r'\s+key risks.*$',
    r'\s+political situation.*$',
    r'\s+breaking news.*$',
    r'\s+news today$',
    r'\s+today$',
    r'\s+\d{4}$',  # trailing year
]


def _clean_for_wiki(query: str) -> str:
    q = query
    for pattern in WIKI_STRIP_PATTERNS:
        q = re.sub(pattern, '', q, flags=re.IGNORECASE).strip()
    return q if len(q) >= 2 else query


class WikiAgent:
    """Specialized agent for Wikipedia and background research.
    Uses direct REST API instead of wikipedia library — more reliable."""

    def __init__(self, emit):
        self.emit = emit

    def run(self, country: str) -> dict:
        wiki_query = _clean_for_wiki(country)
        self.emit("wiki", f"📚 WikiAgent researching background on {country}...")
        results = {}
        start = time.time()

        # Wikipedia via direct REST API — use cleaned query
        self.emit("wiki", f"🔎 Fetching Wikipedia article for {wiki_query}...")
        overview, wiki_url, wiki_title = self._fetch_wikipedia(wiki_query)

        if overview and overview != "Not available":
            results["overview"] = overview
            results["wiki_url"] = wiki_url
            self.emit("wiki", f"✅ Wikipedia: '{wiki_title}' ({len(overview)} chars)")
        else:
            self.emit("wiki", f"⚠️ Direct fetch failed, trying search...")
            overview, wiki_url, wiki_title = self._search_wikipedia(wiki_query)
            if overview and overview != "Not available":
                results["overview"] = overview
                results["wiki_url"] = wiki_url
                self.emit("wiki", f"✅ Wikipedia search: '{wiki_title}'")
            else:
                results["overview"] = "Not available"
                results["wiki_url"] = ""
                self.emit("wiki", f"⚠️ Wikipedia unavailable for {wiki_query}")

        # Global news context — use original query (full context helps here)
        self.emit("wiki", f"🌍 Fetching global news context for {country}...")
        try:
            global_news = search_global_news.invoke(f"{country} news")
            results["global"] = global_news
            global_count = len(re.findall(r'Title:', global_news))
            self.emit("wiki", f"✅ Global news: Found {global_count} international articles")
        except Exception:
            results["global"] = "Not available"
            self.emit("wiki", f"⚠️ Global news unavailable")

        facts = self._extract_facts(results.get("overview", ""))
        results["facts"] = facts
        if facts:
            self.emit("wiki", f"📊 Key facts extracted: {len(facts)} data points")
        else:
            self.emit("wiki", f"ℹ️ No numeric facts found in Wikipedia article")

        elapsed = round(time.time() - start, 1)
        self.emit("wiki", f"🏁 WikiAgent complete in {elapsed}s")
        return results

    def _fetch_wikipedia(self, query: str) -> tuple:
        try:
            encoded = query.strip().replace(" ", "_")
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            headers = {"User-Agent": "WavAgent/2.0 (intelligence research; contact: research@wavagent.ai)"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                title = data.get("title", query)
                extract = data.get("extract", "")
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

                if len(extract) < 300:
                    full = self._fetch_full_intro(encoded)
                    if full and len(full) > len(extract):
                        extract = full

                return extract[:2000], page_url, title

            return "Not available", "", ""

        except Exception:
            return "Not available", "", ""

    def _fetch_full_intro(self, title: str) -> str:
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query", "titles": title, "prop": "extracts",
                "exintro": True, "explaintext": True, "format": "json", "redirects": 1,
            }
            headers = {"User-Agent": "WavAgent/2.0"}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page in pages.items():
                    if page_id != "-1":
                        return page.get("extract", "")[:2000]
        except Exception:
            pass
        return ""

    def _search_wikipedia(self, query: str) -> tuple:
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query", "list": "search", "srsearch": query,
                "srlimit": 3, "format": "json",
            }
            headers = {"User-Agent": "WavAgent/2.0"}
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                if search_results:
                    top_title = search_results[0]["title"]
                    return self._fetch_wikipedia(top_title)
        except Exception:
            pass
        return "Not available", "", ""

    def _extract_facts(self, text: str) -> list:
        if not text or text == "Not available":
            return []
        facts = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for s in sentences[:30]:
            s = s.strip()
            if (re.search(r'\d', s) and 30 < len(s) < 300
                    and not s.startswith("==")
                    and "failed" not in s.lower()
                    and "error" not in s.lower()):
                facts.append(s)
            if len(facts) >= 5:
                break
        return facts