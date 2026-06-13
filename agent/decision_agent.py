import re
from agent.azure_client import azure_chat


RISK_KEYWORDS = {
    "critical": ["war", "nuclear", "attack", "missile", "explosion", "coup",
                 "assassination", "collapse", "default", "pandemic",
                 "catastrophe", "invasion", "genocide"],
    "high": ["conflict", "crisis", "protest", "sanctions", "flood",
             "earthquake", "crash", "riot", "strike", "terrorism",
             "recession", "drought", "wildfire", "tension", "tensions"],
    "medium": ["concern", "warning", "dispute", "uncertainty", "decline",
               "slowdown", "investigation", "arrest", "controversy",
               "volatility", "shortage"],
    "low": ["growth", "development", "agreement", "progress", "peace",
            "recovery", "investment", "innovation", "partnership",
            "reform", "election"],
}

ACTION_TEMPLATES = {
    "geopolitical": [
        "Monitor diplomatic developments closely",
        "Track military movement and troop deployment reports",
        "Watch for economic sanctions and trade restriction updates",
        "Follow UN Security Council emergency session announcements",
    ],
    "economic": [
        "Monitor currency exchange rate fluctuations",
        "Track commodity prices — oil, gold, grain",
        "Watch central bank policy statements and rate decisions",
        "Follow trade agreement and tariff developments",
    ],
    "technology": [
        "Track regulatory and antitrust responses",
        "Monitor competitor product and strategy reactions",
        "Watch for patent disputes and IP litigation",
        "Follow investor sentiment and funding signals",
    ],
    "crisis": [
        "Monitor humanitarian aid and relief operation responses",
        "Track international coalition and alliance formation",
        "Watch for ceasefire or negotiation breakthroughs",
        "Follow displacement and refugee movement reports",
    ],
    "business": [
        "Monitor stock price and market cap movements",
        "Track analyst rating changes and price target updates",
        "Watch for earnings guidance and revenue revisions",
        "Follow supply chain and logistics disruption signals",
    ],
    "default": [
        "Monitor situation for further developments",
        "Track expert commentary and think-tank analysis",
        "Watch for policy and regulatory responses",
        "Follow related economic and market indicators",
    ],
}


def count_word(text: str, word: str) -> int:
    """Count whole-word occurrences only — avoids 'war' matching 'warranty'."""
    return len(re.findall(r'\b' + re.escape(word) + r'\b', text))


def has_any_word(text: str, words: list) -> bool:
    return any(count_word(text, w) > 0 for w in words)


class DecisionAgent:
    """
    Converts raw intelligence into decision-ready output.
    Uses Phi-4-mini-instruct for AI-powered risk narrative.
    """

    def __init__(self, emit):
        self.emit = emit

    def run(self, query: str, report: dict, query_type: str) -> dict:
        self.emit("decision", f"⚡ DecisionAgent analyzing: '{query[:50]}'...")

        all_text = self._collect_text(report)

        self.emit("decision", f"⚠️ Calculating risk level...")
        risk = self._assess_risk(all_text)
        self.emit("decision", f"✅ Risk: {risk['level'].upper()} (score: {risk['score']:.2f})")

        self.emit("decision", f"📈 Detecting trend direction...")
        trend = self._detect_trend(all_text)
        self.emit("decision", f"✅ Trend: {trend['direction'].upper()} — {trend['description']}")

        self.emit("decision", f"🎯 Generating AI-powered recommendations...")
        actions = self._generate_actions(query, query_type, risk, all_text)
        self.emit("decision", f"✅ {len(actions)} recommendations generated")

        self.emit("decision", f"🔍 Checking for contradictions...")
        contradictions = self._detect_contradictions(report)
        msg = f"⚠️ {len(contradictions)} contradicting signals" if contradictions else "✅ No major contradictions"
        self.emit("decision", msg)

        self.emit("decision", f"📊 Scoring evidence quality...")
        evidence = self._score_evidence(report)
        self.emit("decision", f"✅ Evidence: {evidence['quality'].upper()} "
                              f"({evidence['source_count']} sources, {evidence['verified_count']} verified)")

        self.emit("decision", f"🤖 Generating AI risk assessment...")
        risk["ai_assessment"] = self._ai_risk_assessment(query, report, risk, trend)
        self.emit("decision", f"✅ AI assessment complete")

        indicators = self._extract_indicators(all_text, query_type)
        self.emit("decision", f"🏁 DecisionAgent complete — Decision intelligence ready")

        return {
            "risk": risk,
            "trend": trend,
            "actions": actions,
            "contradictions": contradictions,
            "evidence": evidence,
            "indicators": indicators,
        }

    def _ai_risk_assessment(self, query: str, report: dict,
                            risk: dict, trend: dict) -> str:
        events = report.get("key_events", [])
        top_events = "; ".join([e.get("title", "") for e in events[:3]])
        risk_level = risk["level"].upper()
        trend_dir = trend["direction"]

        try:
            result = azure_chat(
                messages=[
                    {"role": "system", "content": "You are an analyst. Give a brief, direct 1-2 sentence assessment. No preamble, no headers, no bold text."},
                    {"role": "user", "content": (
                        f"Topic: {query}\n"
                        f"Risk level: {risk_level}, Trend: {trend_dir}\n"
                        f"Key events: {top_events}\n\n"
                        f"In 1-2 plain sentences, what should someone watching this topic pay attention to next?"
                    )},
                ],
                max_tokens=100,
            )
            if result and len(result) > 20:
                return result
        except Exception:
            pass

        return f"{risk_level} risk — {risk.get('description', 'Monitor closely')}. Trend is {trend_dir}."

    def _collect_text(self, report: dict) -> str:
        parts = [report.get("summary", "")]
        for t in report.get("trending_topics", []):
            parts.append(t.get("topic", "") + " " + t.get("summary", ""))
        for e in report.get("key_events", []):
            parts.append(e.get("title", "") + " " + e.get("summary", ""))
        return " ".join(parts).lower()

    def _assess_risk(self, text: str) -> dict:
        scores = {l: 0 for l in RISK_KEYWORDS}
        matches = {l: [] for l in RISK_KEYWORDS}

        for level, keywords in RISK_KEYWORDS.items():
            for kw in keywords:
                count = count_word(text, kw)
                if count > 0:
                    scores[level] += count
                    matches[level].append(kw)

        weighted = (scores["critical"]*4 + scores["high"]*3 +
                    scores["medium"]*2 + scores["low"]*1)
        total = max(sum(scores.values()), 1)
        risk_score = min(weighted / (total * 4), 1.0)

        if scores["critical"] >= 2:
            level, color, icon = "critical", "#ff4444", "🔴"
        elif scores["critical"] >= 1 or scores["high"] >= 3:
            level, color, icon = "high", "#ff8800", "🟠"
        elif scores["high"] >= 1 or scores["medium"] >= 3:
            level, color, icon = "medium", "#ffcc00", "🟡"
        else:
            level, color, icon = "low", "#00cc44", "🟢"

        all_matches = []
        for l in ["critical", "high", "medium"]:
            all_matches.extend(matches[l][:2])
        description = (f"Signals: {', '.join(all_matches[:4])}"
                       if all_matches else "Based on current intelligence")

        return {
            "level": level, "score": round(risk_score, 2),
            "icon": icon, "color": color,
            "triggers": (matches[level][:3] + matches["high"][:2]),
            "description": description,
        }

    def _detect_trend(self, text: str) -> dict:
        escalating_words = ["escalating", "escalation", "rising", "increasing",
                            "worsening", "deteriorating", "surge", "spike",
                            "accelerating", "intensifying", "spreading"]
        deescalating_words = ["ceasefire", "agreement", "peace", "resolution",
                              "calm", "stabilizing", "recovering", "improving",
                              "easing", "deescalating"]

        esc = sum(count_word(text, w) for w in escalating_words)
        deesc = sum(count_word(text, w) for w in deescalating_words)

        if esc > deesc + 1:
            return {"direction": "escalating", "icon": "📈", "color": "#ff6b6b",
                    "description": "Situation appears to be intensifying",
                    "momentum": min(esc/5, 1.0)}
        elif deesc > esc + 1:
            return {"direction": "de-escalating", "icon": "📉", "color": "#51cf66",
                    "description": "Situation showing signs of improvement",
                    "momentum": min(deesc/5, 1.0)}
        else:
            return {"direction": "stable", "icon": "➡️", "color": "#74c0fc",
                    "description": "Situation remains relatively stable",
                    "momentum": 0.5}

    def _generate_actions(self, query: str, query_type: str,
                          risk: dict, text: str) -> list:
        actions = []

        # Use query_type as PRIMARY signal — much more reliable than keyword sniffing
        type_to_template = {
            "company": "business",
            "person": "technology",
            "country": "geopolitical",
        }

        if query_type in type_to_template:
            key = type_to_template[query_type]
        elif has_any_word(text, ["war", "military", "conflict", "sanctions", "nato", "invasion"]):
            key = "geopolitical"
        elif has_any_word(text, ["stock", "economy", "gdp", "inflation", "market", "trade"]):
            key = "economic"
        elif has_any_word(text, ["tech", "ai", "software", "startup", "openai", "app"]):
            key = "technology"
        elif has_any_word(text, ["crisis", "disaster", "flood", "earthquake", "pandemic"]):
            key = "crisis"
        elif has_any_word(text, ["earnings", "revenue", "profit", "ipo", "acquisition"]):
            key = "business"
        else:
            key = "default"

        if risk["level"] in ["critical", "high"]:
            actions.append({
                "priority": "URGENT",
                "action": f"Immediate attention required — {risk['level'].upper()} risk detected",
                "icon": "🚨",
            })

        for i, action in enumerate(ACTION_TEMPLATES[key][:3]):
            actions.append({
                "priority": ["HIGH", "MEDIUM", "LOW"][i],
                "action": action,
                "icon": ["🎯", "📋", "ℹ️"][i],
            })

        actions.append({
            "priority": "MONITOR",
            "action": f"Set up alerts for '{query[:40]}' updates",
            "icon": "🔔",
        })
        return actions[:5]

    def _detect_contradictions(self, report: dict) -> list:
        contradictions = []
        events = report.get("key_events", [])
        sentiment = report.get("social_sentiment", "neutral")
        all_text = " ".join([e.get("title","").lower() for e in events[:5]])

        neg = has_any_word(all_text, ["war","crisis","attack","death","collapse"])
        pos = has_any_word(all_text, ["growth","record","success","peace","win"])

        if sentiment == "positive" and neg:
            contradictions.append({
                "type": "sentiment_mismatch",
                "description": "Social sentiment positive but news contains negative signals",
                "severity": "medium",
            })
        elif sentiment == "negative" and pos:
            contradictions.append({
                "type": "sentiment_mismatch",
                "description": "Social sentiment negative but news shows positive developments",
                "severity": "low",
            })
        if neg and pos:
            contradictions.append({
                "type": "mixed_signals",
                "description": "Both positive and negative developments detected simultaneously",
                "severity": "low",
            })
        return contradictions

    def _score_evidence(self, report: dict) -> dict:
        events = report.get("key_events", [])
        sources = report.get("sources_visited", [])

        source_count = len(sources)
        verified_count = sum(1 for e in events if e.get("verified", False))
        has_url_count = sum(1 for e in events if e.get("url", ""))
        avg_confidence = sum(e.get("confidence", 0.5) for e in events) / max(len(events), 1)

        quality_score = (
            min(source_count/7, 1.0)*0.3 +
            min(has_url_count/5, 1.0)*0.3 +
            avg_confidence*0.4
        )
        quality = "high" if quality_score >= 0.75 else "medium" if quality_score >= 0.5 else "low"

        return {
            "quality": quality, "score": round(quality_score, 2),
            "source_count": source_count, "verified_count": verified_count,
            "has_url_count": has_url_count, "avg_confidence": round(avg_confidence, 2),
        }

    def _extract_indicators(self, text: str, query_type: str) -> list:
        indicators = []
        patterns = {
            "💰 Financial": r'\$[\d,.]+\s*(?:billion|million|trillion|crore|lakh)?',
            "📅 Date": r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:,\s*\d{4})?\b',
            "📊 Percentage": r'\d+(?:\.\d+)?%',
            "🔢 Count": r'\b\d+(?:,\d+)*\s+(?:people|soldiers|casualties|companies|countries|nations)\b',
        }
        for label, pattern in patterns.items():
            for match in re.findall(pattern, text, re.IGNORECASE)[:2]:
                indicators.append({"type": label, "value": match.strip()})
            if len(indicators) >= 6:
                break
        return indicators[:6]