import os
import requests
from langchain.tools import tool


def translate_with_deepl(text: str, target_language: str) -> str:
    """Translate text using DeepL API"""
    try:
        api_key = os.getenv("DEEPL_API_KEY")
        if not api_key:
            return text

        url = "https://api-free.deepl.com/v2/translate"
        
        response = requests.post(
            url,
            data={
                "auth_key": api_key,
                "text": text,
                "target_lang": target_language.upper(),
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result["translations"][0]["text"]
        return text

    except Exception:
        return text


def translate_with_sarvam(text: str, target_language: str) -> str:
    """Translate text using Sarvam AI for Indian languages"""
    try:
        api_key = os.getenv("SARVAM_API_KEY")
        if not api_key:
            return text

        indian_languages = {
            "hi": "hi-IN",
            "ta": "ta-IN",
            "te": "te-IN",
            "bn": "bn-IN",
            "gu": "gu-IN",
            "mr": "mr-IN",
            "ml": "ml-IN",
            "kn": "kn-IN",
            "pa": "pa-IN",
            "or": "or-IN",
        }

        if target_language not in indian_languages:
            return text

        url = "https://api.sarvam.ai/translate"
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "input": text,
            "source_language_code": "en-IN",
            "target_language_code": indian_languages[target_language],
            "speaker_gender": "Male",
            "mode": "formal",
            "model": "mayura:v1",
            "enable_preprocessing": True,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            return response.json().get("translated_text", text)
        return text

    except Exception:
        return text


INDIAN_LANGUAGES = ["hi", "ta", "te", "bn", "gu", "mr", "ml", "kn", "pa", "or"]


def translate_report(report: dict, target_language: str) -> dict:
    """Translate entire report to target language"""
    if target_language == "en":
        return report

    try:
        translated = report.copy()

        # Translate summary
        if report.get("summary"):
            if target_language in INDIAN_LANGUAGES:
                translated["summary"] = translate_with_sarvam(
                    report["summary"], target_language
                )
            else:
                translated["summary"] = translate_with_deepl(
                    report["summary"], target_language
                )

        # Translate trending topics
        translated_topics = []
        for topic in report.get("trending_topics", []):
            t = topic.copy()
            if topic.get("summary"):
                if target_language in INDIAN_LANGUAGES:
                    t["summary"] = translate_with_sarvam(
                        topic["summary"], target_language
                    )
                else:
                    t["summary"] = translate_with_deepl(
                        topic["summary"], target_language
                    )
            translated_topics.append(t)
        translated["trending_topics"] = translated_topics

        # Translate key events
        translated_events = []
        for event in report.get("key_events", []):
            e = event.copy()
            if event.get("summary"):
                if target_language in INDIAN_LANGUAGES:
                    e["summary"] = translate_with_sarvam(
                        event["summary"], target_language
                    )
                else:
                    e["summary"] = translate_with_deepl(
                        event["summary"], target_language
                    )
            translated_events.append(e)
        translated["key_events"] = translated_events

        translated["language"] = target_language
        return translated

    except Exception:
        return report