from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import hashlib
import os
from datetime import datetime

from agent.agent import run_geo_agent
from translator.translate import translate_report

app = FastAPI(
    title="WavAgent API",
    description="Multi-agent autonomous country intelligence system",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Import and register stream router AFTER app is created
from api.stream import router as stream_router
app.include_router(stream_router)

# Serve UI
@app.get("/ui")
async def serve_ui():
    return FileResponse("index.html")

# In-memory cache
cache = {}
CACHE_TTL = 1800


class IntelligenceRequest(BaseModel):
    country: str
    country_code: Optional[str] = None
    language: Optional[str] = "en"
    force_refresh: Optional[bool] = False


def get_cache_key(country: str, language: str) -> str:
    return hashlib.md5(f"{country.lower()}:{language}".encode()).hexdigest()


def is_cache_valid(key: str) -> bool:
    if key not in cache:
        return False
    age = (datetime.now() - cache[key]["timestamp"]).seconds
    return age < CACHE_TTL


@app.get("/")
async def root():
    return {
        "name": "WavAgent",
        "version": "2.0.0",
        "description": "Multi-agent autonomous country intelligence system",
        "status": "running",
        "agents": ["OrchestratorAgent", "NewsAgent", "SocialAgent", "WikiAgent", "SynthesisAgent"],
        "endpoints": {
            "ui": "GET /ui",
            "intelligence": "POST /api/agent/country-intelligence",
            "stream": "POST /api/agent/stream",
            "languages": "GET /api/agent/supported-languages",
            "health": "GET /health",
            "docs": "GET /docs",
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "2.0.0"}


@app.post("/api/agent/country-intelligence")
async def get_country_intelligence(request: IntelligenceRequest):
    try:
        country = request.country.strip()
        language = request.language or "en"

        if not country:
            raise HTTPException(status_code=400, detail="Country is required")

        cache_key = get_cache_key(country, language)
        if not request.force_refresh and is_cache_valid(cache_key):
            cached_data = cache[cache_key]["data"]
            return {
                "success": True,
                "country": country,
                "data": cached_data,
                "cached": True,
                "generated_at": cache[cache_key]["timestamp"].isoformat(),
            }

        result = run_geo_agent(country=country, language=language)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Agent failed"))

        report = result["data"]

        if language != "en":
            try:
                report = translate_report(report, language)
            except Exception:
                pass

        report["generated_at"] = datetime.now().isoformat()
        report["country"] = country

        cache[cache_key] = {"data": report, "timestamp": datetime.now()}

        return {
            "success": True,
            "country": country,
            "data": report,
            "cached": False,
            "generated_at": report["generated_at"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/supported-languages")
async def get_supported_languages():
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "Hindi"},
            {"code": "ta", "name": "Tamil"},
            {"code": "te", "name": "Telugu"},
            {"code": "bn", "name": "Bengali"},
            {"code": "gu", "name": "Gujarati"},
            {"code": "mr", "name": "Marathi"},
            {"code": "ml", "name": "Malayalam"},
            {"code": "kn", "name": "Kannada"},
            {"code": "pa", "name": "Punjabi"},
            {"code": "de", "name": "German"},
            {"code": "fr", "name": "French"},
            {"code": "es", "name": "Spanish"},
            {"code": "ja", "name": "Japanese"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ar", "name": "Arabic"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ru", "name": "Russian"},
            {"code": "ko", "name": "Korean"},
        ]
    }


@app.get("/api/agent/cache/clear")
async def clear_cache():
    cache.clear()
    return {"message": "Cache cleared successfully"}