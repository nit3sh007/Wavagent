import re
import time
from tools.reddit import search_reddit_country, get_reddit_sentiment


# Megathread patterns to filter out
SKIP_PATTERNS = [
    "Thread", "Weekly", "Daily", "Monthly", "Support",
    "Megathread", "Discussion Thread", "Ask India",
    "Advice", "Rant", "Vent", "Pinned"
]


class SocialAgent:
    """Specialized agent for social media sentiment analysis."""

    def __init__(self, emit):
        self.emit = emit

    def run(self, country: str) -> dict:
        self.emit("social", f"💬 SocialAgent analyzing social media for {country}...")
        results = {}
        start = time.time()

        # Reddit discussions
        self.emit("social", f"🔴 Scanning Reddit for {country} discussions...")
        try:
            reddit_data = search_reddit_country.invoke(country)
            posts = re.findall(r'Post:\s*(.+)', reddit_data)
            # Filter megathreads
            posts = [p for p in posts if not any(skip in p for skip in SKIP_PATTERNS)]
            results["posts"] = posts[:10]
            results["raw"] = reddit_data
            self.emit("social", f"✅ Reddit: Found {len(posts)} relevant posts (filtered megathreads)")
        except Exception as e:
            results["posts"] = []
            results["raw"] = ""
            self.emit("social", f"⚠️ Reddit unavailable: {str(e)[:50]}")

        # Sentiment analysis
        self.emit("social", f"🧠 Running sentiment analysis...")
        try:
            sentiment_data = get_reddit_sentiment.invoke(country)
            sentiment = self._analyze_sentiment(sentiment_data + results.get("raw", ""))
            results["sentiment"] = sentiment
            results["sentiment_raw"] = sentiment_data
            self.emit("social", f"✅ Sentiment detected: {sentiment.upper()} based on {len(results['posts'])} posts")
        except Exception as e:
            results["sentiment"] = "neutral"
            results["sentiment_raw"] = ""
            self.emit("social", f"⚠️ Sentiment defaulting to neutral")

        # Key themes
        themes = self._extract_themes(results.get("posts", []))
        results["themes"] = themes
        if themes:
            self.emit("social", f"🏷️ Top social themes: {', '.join(themes[:3])}")
        else:
            self.emit("social", f"ℹ️ No specific social themes detected")

        elapsed = round(time.time() - start, 1)
        self.emit("social", f"🏁 SocialAgent complete in {elapsed}s")
        return results

    def _analyze_sentiment(self, text: str) -> str:
        text_lower = text.lower()
        positive = ["growth", "success", "peace", "win", "development",
                    "progress", "agreement", "boost", "record", "celebrate",
                    "hope", "rise", "improve", "landmark", "achieve"]
        negative = ["crisis", "conflict", "war", "attack", "flood", "protest",
                    "disaster", "death", "arrest", "violence", "tensions",
                    "collapse", "strike", "bomb", "killed", "injured"]
        pos = sum(text_lower.count(w) for w in positive)
        neg = sum(text_lower.count(w) for w in negative)
        if pos > neg + 2: return "positive"
        if neg > pos + 2: return "negative"
        return "neutral"

    def _extract_themes(self, posts: list) -> list:
        if not posts:
            return []
        keywords = {}
        for post in posts:
            # Extract meaningful noun phrases
            words = re.findall(r'\b[A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]{3,})*\b', post)
            for word in words:
                if not any(skip.lower() in word.lower() for skip in SKIP_PATTERNS):
                    keywords[word] = keywords.get(word, 0) + 1
        sorted_themes = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_themes[:5]]