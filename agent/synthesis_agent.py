import re
import time
from agent.azure_client import azure_chat


class SynthesisAgent:
    """Combines findings from all agents into final report."""

    def __init__(self, emit):
        self.emit = emit

    def run(self, country: str, news_data: dict, social_data: dict, wiki_data: dict) -> dict:
        self.emit("synthesis", f"🧬 SynthesisAgent combining all findings...")
        start = time.time()

        all_news = news_data.get("rss", []) + news_data.get("web", [])
        deep_dive = news_data.get("deep_dive", [])

        self.emit("synthesis", f"📋 Merging {len(news_data.get('rss', []))} RSS + {len(news_data.get('web', []))} web articles...")

        self.emit("synthesis", f"📈 Identifying trending topics...")
        trending = self._build_trending(all_news, social_data.get("posts", []))
        self.emit("synthesis", f"✅ Identified {len(trending)} trending topics")

        self.emit("synthesis", f"📌 Extracting key events...")
        key_events = self._build_key_events(all_news + deep_dive)
        self.emit("synthesis", f"✅ Extracted {len(key_events)} key events")

        self.emit("synthesis", f"🔗 Cross-referencing sources for accuracy...")
        verified_events = self._cross_reference(key_events, social_data.get("raw", ""))
        self.emit("synthesis", f"✅ Cross-referenced: {len(verified_events)} events verified")

        self.emit("synthesis", f"📊 Calculating confidence scores...")
        scored_topics = self._add_confidence(
            trending, all_news,
            social_data.get("raw", ""),
            wiki_data.get("overview", "")
        )
        self.emit("synthesis", f"✅ Confidence scores assigned")

        self.emit("synthesis", f"✍️ Generating AI-powered summary...")
        summary = self._build_summary(
            country, all_news,
            social_data.get("sentiment", "neutral"),
            wiki_data.get("overview", "")
        )
        self.emit("synthesis", f"✅ Summary generated")

        sources = self._build_sources(news_data, social_data, wiki_data)
        self.emit("synthesis", f"📚 Sources visited: {', '.join(sources)}")

        elapsed = round(time.time() - start, 1)
        self.emit("synthesis", f"🏁 SynthesisAgent complete in {elapsed}s — Report ready!")

        return {
            "country": country,
            "trending_topics": scored_topics,
            "key_events": verified_events,
            "social_sentiment": social_data.get("sentiment", "neutral"),
            "summary": summary,
            "sources_visited": sources,
            "facts": wiki_data.get("facts", []),
            "social_themes": social_data.get("themes", []),
        }

    def _build_summary(self, country: str, news_items: list,
                       sentiment: str, wiki_overview: str = "") -> str:
        titles = [i["title"] for i in news_items[:6] if i.get("title")]
        if not titles:
            return f"{country} is currently under intelligence monitoring with limited data available."

        headlines = "\n".join(f"- {t}" for t in titles[:5])

        try:
            result = azure_chat(
                messages=[
                    {"role": "system", "content": "You are a news analyst. Write a concise 2-3 sentence intelligence summary. Be factual and direct."},
                    {"role": "user", "content": f"Summarize these headlines about {country} into 2-3 sentences:\n{headlines}"},
                ],
                max_tokens=150,
            )
            if result and len(result) > 40:
                return result
        except Exception:
            pass

        # Fallback
        sentiment_phrase = {
            "positive": "largely positive developments",
            "negative": "several concerning developments",
            "neutral": "mixed developments",
        }.get(sentiment, "mixed developments")

        if len(titles) >= 2:
            return (
                f"{country} is currently experiencing {sentiment_phrase}. "
                f"Key stories include: {titles[0]}. "
                f"Additionally, {titles[1][0].lower() + titles[1][1:]}."
            )
        return f"{country} is experiencing {sentiment_phrase}. Latest: {titles[0]}."

    def _build_trending(self, news_items: list, reddit_posts: list) -> list:
        trending = []
        seen = set()
        all_titles = [i["title"] for i in news_items[:4]] + reddit_posts[:3]
        for title in all_titles:
            if title and len(title) > 10 and title not in seen:
                seen.add(title)
                trending.append({
                    "topic": title[:100],
                    "sentiment": "neutral",
                    "summary": title[:200],
                    "confidence": 0.5,
                })
            if len(trending) >= 6:
                break
        return trending

    def _build_key_events(self, news_items: list) -> list:
        events = []
        seen = set()
        for item in news_items[:6]:
            if item.get("title") and item["title"] not in seen:
                seen.add(item["title"])
                # Strip markdown artifacts
                summary = (item.get("summary") or item["title"])
                summary = re.sub(r'^#+\s*', '', summary).strip()  # remove leading #
                events.append({
                    "title": item["title"],
                    "summary": summary,
                    "source": item.get("source", "Web"),
                    "url": item.get("url", ""),
                    "verified": False,
                })
        return events

    def _cross_reference(self, events: list, social_text: str) -> list:
        for event in events:
            title_words = set(event["title"].lower().split())
            social_lower = social_text.lower()
            matches = sum(1 for w in title_words if len(w) > 4 and w in social_lower)
            if matches >= 2:
                event["verified"] = True
                event["confidence"] = 0.85
            else:
                event["confidence"] = 0.6
        return events

    def _add_confidence(self, topics: list, news: list, social: str, wiki: str) -> list:
        news_text = " ".join([n.get("title","") + " " + n.get("summary","") for n in news]).lower()
        social_lower = social.lower()
        wiki_lower = wiki.lower()

        for topic in topics:
            title_words = set(topic["topic"].lower().split())
            score = 0.4
            key_words = [w for w in title_words if len(w) > 4]
            for w in key_words:
                if w in news_text: score += 0.1
                if w in social_lower: score += 0.1
                if w in wiki_lower: score += 0.05
            topic["confidence"] = min(round(score, 2), 0.99)

            text = topic["topic"].lower()
            if any(w in text for w in ["arrest", "attack", "war", "crisis", "flood", "death", "killed"]):
                topic["sentiment"] = "negative"
            elif any(w in text for w in ["growth", "win", "success", "launch", "record", "peace"]):
                topic["sentiment"] = "positive"
        return topics

    def _build_sources(self, news_data: dict, social_data: dict, wiki_data: dict) -> list:
        sources = []
        if news_data.get("rss"): sources.append("RSS News Feeds")
        if news_data.get("web"): sources.append("Tavily Web Search")
        if news_data.get("deep_dive"): sources.append("Deep Dive Search")
        if social_data.get("posts"): sources.append("Reddit")
        if social_data.get("sentiment_raw"): sources.append("Reddit Sentiment")
        if wiki_data.get("overview") not in (None, "Not available", ""): sources.append("Wikipedia")
        if wiki_data.get("global") not in (None, "Not available", ""): sources.append("Global News")
        return sources if sources else ["Web Search"]