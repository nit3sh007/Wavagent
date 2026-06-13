# WavAgent — Real-Time Decision Intelligence Engine

**Microsoft Build AI Hackathon 2026 — Theme: Agent Swarms**

WavAgent is a multi-agent intelligence platform that deploys a swarm of specialized AI agents to research any topic — a country, company, person, or breaking news event — in real time. A live agent panel shows every step of the swarm at work, while Azure AI Foundry's Phi-4-mini-instruct model synthesizes findings into a fluent intelligence briefing with risk scoring and actionable recommendations.

---

## Problem Statement

Researching a topic today means manually checking news sites, Reddit, Wikipedia, and search engines, then mentally synthesizing it all into "what does this mean and what should I do about it?" WavAgent automates this entire pipeline with a coordinated swarm of AI agents — and shows you the swarm working, live, instead of hiding it behind a spinner.

---

## Architecture — Agent Swarm

WavAgent uses **6 specialized agents** orchestrated adaptively based on query type:

```
                    ┌─────────────────────┐
                    │  Query Classifier    │
                    │  (country/company/   │
                    │   person/topic/...)  │
                    └──────────┬───────────┘
                                │
                    ┌───────────▼────────────┐
                    │  Adaptive Orchestrator   │
                    │  (selects profile based  │
                    │   on query type)         │
                    └───────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                        │                        │
   ┌────▼─────┐           ┌─────▼──────┐          ┌──────▼─────┐
   │ NewsAgent │           │ SocialAgent│          │  WikiAgent  │
   │ RSS+Tavily│           │   Reddit   │          │  Wikipedia +│
   │ +DeepDive │           │  Sentiment │          │  Global News│
   └────┬─────┘           └─────┬──────┘          └──────┬─────┘
        │                        │                        │
        └───────────────────────┼───────────────────────┘
                                 │  (all 3 run in PARALLEL)
                       ┌─────────▼──────────┐
                       │   SynthesisAgent    │
                       │  Merges findings +  │
                       │  Phi-4 AI summary   │
                       └─────────┬──────────┘
                                 │
                       ┌─────────▼──────────┐
                       │   DecisionAgent     │
                       │  Risk scoring +     │
                       │  Phi-4 risk         │
                       │  narrative + actions│
                       └─────────┬──────────┘
                                 │
                       ┌─────────▼──────────┐
                       │  Live UI — streams  │
                       │  every step via SSE │
                       └─────────────────────┘
```

### Adaptive Profiles

The orchestrator dynamically adjusts agent behavior based on detected query type:

| Profile | Behavior |
|---|---|
| **Country** | Full pipeline — news, social sentiment, Wikipedia background |
| **Company** | Business-focused actions (stock, earnings, analyst ratings) |
| **Person** | Biography + recent activity |
| **Breaking/Crisis** | Skips Wikipedia, maximizes news coverage for speed |
| **Research** | Prioritizes Wikipedia + deep context over breaking news |

### Conversational Routing

A lightweight regex-based intent filter detects casual greetings ("hi", "how are you", "what can you do") and responds directly via Phi-4-mini-instruct without deploying the full agent swarm — saving ~25 seconds and avoiding nonsensical "intelligence reports" about small talk.

---

## Key Features

- **Live agent swarm visualization** — every one of the 60+ agent steps streams to the UI in real time via Server-Sent Events, so judges (and users) see exactly what's happening
- **AI-powered intelligence summaries** — Phi-4-mini-instruct (Azure AI Foundry) writes fluent 2-3 sentence briefings from raw headlines
- **AI-powered risk assessment** — Phi-4-mini-instruct analyzes risk level + trend direction and writes a natural-language risk narrative
- **Risk scoring engine** — word-boundary-safe keyword analysis across critical/high/medium/low risk categories
- **Contextual action recommendations** — query-type-aware (geopolitical actions for countries, business actions for companies, etc.)
- **Evidence quality scoring** — tracks source count, verification rate, and average confidence
- **Click-to-research** — trending topics, key events, and follow-up suggestions are all clickable and auto-trigger new research
- **Adaptive query classification** — automatically detects country/company/person/topic/breaking news and adjusts agent strategy
- **Conversational small-talk routing** — greetings get a quick friendly reply instead of triggering a full research pipeline

---

## Tech Stack

| Layer | Technology |
|---|---|
| **AI Model** | Azure AI Foundry — **Phi-4-mini-instruct** |
| **Backend** | Python, FastAPI, Server-Sent Events (SSE) |
| **Agent Framework** | LangChain tools + custom multi-agent orchestration |
| **News Sources** | RSS feeds (BBC, NDTV, Reuters, etc.), Tavily Web Search |
| **Social Signal** | Reddit RSS feeds |
| **Background Context** | Wikipedia REST API |
| **Frontend** | Vanilla HTML/CSS/JS, custom dark-theme UI |

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Azure AI Foundry account with a **Phi-4-mini-instruct** deployment

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd WavAgent
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
# Azure AI Foundry — Phi-4-mini-instruct deployment
AZURE_OPENAI_ENDPOINT=https://your-resource.services.ai.azure.com/models
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_OPENAI_DEPLOYMENT=Phi-4-mini-instruct

# Tavily web search
TAVILY_API_KEY=your_tavily_api_key
```

### 3. Run the server

```bash
python main.py
```

### 4. Open the UI

Navigate to **http://localhost:8000/ui**

Try queries like: `India`, `Tesla`, `Elon Musk`, `Ukraine war`, `China economy 2026`

Try a greeting too: `hi`, `how are you` — WavAgent responds directly without deploying the agent swarm.

---

## AI Tools Used (Disclosure)

As required by the hackathon rules, this project was built using the following AI-assisted tools:

- **GitHub Copilot** — used for code completion and boilerplate generation throughout development
- **Azure AI Foundry (Phi-4-mini-instruct)** — core AI model powering:
  - Intelligence summary generation (`SynthesisAgent`)
  - Risk narrative generation (`DecisionAgent`)
  - Conversational reply generation for casual queries
  - Intent classification (chat vs. research) fallback
- **Claude (Anthropic)** — used as a pair-programming assistant for debugging, architecture decisions, and iterative UI development

All core agent logic, orchestration design, risk-scoring algorithms, UI/UX, and product decisions were designed and implemented by the team. AI tools accelerated development but the system architecture, prompt engineering, debugging, and integration work represent original engineering effort.

---

## Data Privacy & Handling

- **No user data is collected or stored.** Each query is processed in-memory and discarded after the response is returned.
- **No personal, sensitive, or proprietary data** is used — all data sources are public (RSS feeds, public Reddit posts, Wikipedia, public web search results).
- **API keys** are stored in `.env` (excluded from version control via `.gitignore`) and never exposed to the frontend.
- **In-memory caching** (30-minute TTL) is used only to reduce redundant API calls for repeated queries within a session — no persistent storage.

---

## Project Structure

```
WavAgent/
├── agent/
│   ├── agent.py                  # Main entry point
│   ├── classifier_agent.py       # Query type classification
│   ├── adaptive_orchestrator.py  # Orchestrates parallel agents
│   ├── news_agent.py             # RSS + Tavily web search
│   ├── social_agent.py           # Reddit sentiment analysis
│   ├── wiki_agent.py             # Wikipedia + global news
│   ├── synthesis_agent.py        # Merges findings + AI summary
│   ├── decision_agent.py         # Risk scoring + AI risk narrative
│   └── azure_client.py           # Azure AI Foundry client
├── api/
│   ├── routes.py                 # REST endpoints
│   └── stream.py                 # SSE streaming endpoint
├── tools/
│   ├── news_rss.py                # RSS feed tools
│   ├── web_search.py             # Tavily search tool
│   └── reddit.py                  # Reddit search tools
├── index.html                     # Frontend UI
├── main.py                         # FastAPI app entry point
└── requirements.txt
```

---
## License & Open Source Credits

This project uses the following open-source libraries (see `requirements.txt` for full list):
- FastAPI, Uvicorn — web framework
- LangChain — agent tool framework
- feedparser — RSS parsing
- requests — Wikipedia REST API access
- Tavily — web search API

---

**Built for Microsoft Build AI Hackathon 2026 — Agent Swarms theme.**