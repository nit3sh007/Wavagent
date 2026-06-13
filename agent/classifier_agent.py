import re

QUERY_TYPES = {
    "country": "🌍", "company": "🏢", "person": "👤",
    "topic": "📰", "event": "🎯", "trending": "🔥",
}

COUNTRIES = {
    "india","usa","united states","america","china","russia","japan","germany",
    "france","brazil","uk","united kingdom","australia","canada","italy","spain",
    "mexico","south korea","korea","pakistan","iran","israel","ukraine","turkey",
    "saudi arabia","egypt","nigeria","indonesia","argentina","poland","taiwan",
    "netherlands","sweden","norway","switzerland","bangladesh","vietnam","thailand",
}

COMPANY_KEYWORDS = {
    "apple","google","microsoft","amazon","meta","tesla","nvidia","openai",
    "anthropic","samsung","sony","netflix","twitter","x","tata","reliance",
    "infosys","wipro","inc","corp","ltd","company","startup","stock","shares",
    "earnings","ipo","revenue","profit","ceo","founder",
}

PERSON_KEYWORDS = {
    "modi","trump","biden","putin","xi","musk","zuckerberg","cook","gates",
    "bezos","altman","sunak","macron","zelensky","netanyahu","minister",
    "president","prime minister","chancellor","senator","ceo","founder",
    "billionaire","politician","leader",
}

TRENDING_KEYWORDS = {
    "today","right now","latest","breaking","trending","happening",
    "current","live","just now","this week","2026",
}

QUESTION_PATTERNS = [
    r'^(?:where|what|who|how|when|why)\s+is\s+',
    r'^(?:where|what|who|how|when|why)\s+are\s+',
    r'^(?:where|what|who|how|when|why)\s+was\s+',
    r'^tell\s+me\s+about\s+',
    r'^(?:give|show)\s+me\s+(?:info|news|details)?\s*(?:about|on)?\s+',
    r'^(?:latest|recent|current)\s+news\s+(?:about|on)?\s+',
    r'^news\s+(?:about|on)\s+',
    r'^(?:search|find|look\s+up)\s+',
    r'^(?:what\'s|whats)\s+(?:happening|going on)\s+(?:in|with)?\s+',
    r'^(?:tell|explain|describe)\s+',
]


class QueryClassifierAgent:

    def classify(self, query: str) -> dict:
        query = self._sanitize_query(query)
        q = query.lower().strip()
        query_type = self._detect_type(q)
        entities = self._extract_entities(query, q, query_type)
        strategies = self._build_strategies(query, query_type, entities)
        return {
            "original_query": query,
            "type": query_type,
            "icon": QUERY_TYPES.get(query_type, "🔍"),
            "entities": entities,
            "strategies": strategies,
            "display_type": query_type.upper(),
        }

    def _sanitize_query(self, query: str) -> str:
        """Strip question words and punctuation, extract the real entity."""
        # Strip trailing punctuation
        q = query.strip().rstrip('?!.')

        # Apply question pattern stripping
        for pattern in QUESTION_PATTERNS:
            cleaned = re.sub(pattern, '', q, flags=re.IGNORECASE).strip()
            if len(cleaned) >= 2:
                q = cleaned
                break  # only apply first matching pattern

        # Capitalize first letter back
        if q:
            q = q[0].upper() + q[1:]

        return q if len(q) >= 2 else query.strip()

    def _detect_type(self, q: str) -> str:
        # Company BEFORE trending — "Tesla latest news" is company not trending
        if any(w in q for w in COMPANY_KEYWORDS):
            return "company"
        if any(w in q for w in PERSON_KEYWORDS):
            return "person"
        if q in COUNTRIES or any(c in q for c in COUNTRIES):
            return "country"
        if any(w in q for w in TRENDING_KEYWORDS) and len(q.split()) <= 4:
            return "trending"
        return "topic"

    def _extract_entities(self, query: str, q: str, query_type: str) -> dict:
        entities = {"primary": query, "keywords": []}
        caps = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', query)
        entities["keywords"] = list(set(caps))[:5]
        if query_type == "country":
            for country in COUNTRIES:
                if country in q:
                    entities["country"] = country.title()
                    break
        elif query_type == "company":
            # Extract the company name (first capitalized word or known keyword)
            for kw in COMPANY_KEYWORDS:
                if kw in q:
                    entities["company"] = kw.title()
                    break
        elif query_type == "person":
            for kw in PERSON_KEYWORDS:
                if kw in q:
                    entities["person"] = kw.title()
                    break
        return entities

    def _build_strategies(self, query: str, query_type: str, entities: dict) -> list:
        year = "2026"
        if query_type == "country":
            target = entities.get("country", query)
            return [
                f"{target} latest news {year}",
                f"{target} current events politics economy",
                f"{target} trending social media",
                f"{target} breaking news today",
            ]
        elif query_type == "person":
            return [
                f"{query} latest news {year}",
                f"{query} recent statements actions",
                f"{query} controversy scandal achievement",
            ]
        elif query_type == "company":
            target = entities.get("company", query)
            return [
                f"{target} latest news {year}",
                f"{target} stock earnings revenue",
                f"{target} product launch strategy",
                f"{target} CEO announcement",
            ]
        elif query_type == "trending":
            return [
                f"breaking news today {year}",
                f"top trending topics worldwide {year}",
                f"major world events this week",
            ]
        else:
            return [
                f"{query} latest news {year}",
                f"{query} recent developments update",
                f"{query} analysis expert opinion",
            ]