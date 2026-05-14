# AI Equity Research Analyst — Project Plan
### An intelligent multiagent system for Indian stock market research

---

## The Vision

Most retail investors in India have a watchlist but no time to read annual reports, no way to spot hidden company relationships, and no system to cut through market noise. This project builds an AI-powered equity research analyst that does what no screener currently does — reads annual reports, maps company relationships into a knowledge graph, and generates deep investment research using a team of specialized AI agents.

> *"Tell me which stocks to buy for the long term — and show me why."*

---

## What It Does

```
User: "Suggest me stocks for long term investment"
              ↓
System screens 200 Nifty/Midcap stocks
              ↓
Agents analyze top candidates using:
  → Live market data (prices, volume, technicals)
  → Recent news sentiment
  → Annual report insights via RAG
  → Company relationship knowledge graph
              ↓
"Here are your top 3 picks, the reasoning, and the risks"
```

### Three Query Modes

| Mode | Example Query |
|---|---|
| Analyze a stock | "Analyze RELIANCE for long term investment" |
| Get recommendations | "Suggest stocks for long term investment" |
| Explore relationships | "Which small caps have deals with Tata group?" |

---

## Four Layers of Intelligence

```
Layer 1 — Prompting
  Carefully crafted system prompts per agent
  Each agent has a specific role and personality

Layer 2 — RAG (Retrieval Augmented Generation)
  Annual report chunks injected at query time
  Agent reads actual pages from actual filings

Layer 3 — Knowledge Graph
  Company relationships, deals, board members
  Subsidiaries, JVs, supplier/customer chains

Layer 4 — Live Data
  Real-time prices, recent news, volume anomalies
```

---

## System Architecture

```
                          User
                           ↓
                     React Dashboard
                     (WebSocket live updates)
                           ↓
                        FastAPI
                           ↓
                 Orchestrator Agent
                 (reasons & plans dynamically)
                /           |             \
         Market           News           Graph Query
         Agent            Agent            Agent
       (yfinance)      (Google News      (queries Neo4j
                         + Claude)        knowledge graph)
                \           |             /
                 └──────────┴─────────────┘
                            ↓
                  RAG layer injects
                  relevant AR chunks
                  into agent context
                            ↓
             ┌──────────────┴──────────────┐
             ↓                             ↓
      Fundamental                      Risk Agent
        Agent                        (spawned only if
      (financials,                    red flags found)
       PE, debt, growth)
             └──────────────┬──────────────┘
                            ↓
                      Critic Agent
                  (challenges the thesis)
                            ↓
                      Report Agent
                  (final recommendation)
                            ↓
                       Dashboard
```

---

## Two Pipelines

### Pipeline 1 — Knowledge Builder
*Runs quarterly when new annual reports are released*

```
NSE/BSE Annual Report PDFs (downloaded automatically)
          ↓
PDF Extraction — pdfplumber + PyMuPDF
  → Text, tables, financial statements
          ↓
Entity & Relationship Extraction — Claude API
  → Companies mentioned, deals signed,
    board members, subsidiaries, JVs, debt
          ↓
          ├── Knowledge Graph (Neo4j)
          │     Nodes: Companies, People, Institutions
          │     Edges: Deals, Ownership, Debt, Partnerships
          │
          └── Vector Store (ChromaDB)
                Chunked AR text for RAG retrieval
```

### Pipeline 2 — Investment Analyst
*Runs on every user query*

```
User Query
    ↓
Orchestrator plans dynamically
    ↓
Agents run in parallel (market + news + graph)
    ↓
RAG retrieves relevant annual report sections
    ↓
Orchestrator reads findings
    ↓
Red flags? → Risk Agent spawned
    ↓
Critic Agent challenges the thesis
    ↓
Report Agent writes final output
    ↓
Dashboard renders result
```

---

## Agent Breakdown

| Agent | Role | Tools Used |
|---|---|---|
| **Orchestrator** | Plans, coordinates, decides next steps dynamically | Claude reasoning |
| **Market Agent** | Price, volume, 52w high/low, moving averages | yfinance |
| **News Agent** | Fetches headlines, classifies sentiment | Google News RSS + Claude |
| **Fundamental Agent** | Revenue, profit, PE, debt, growth | Screener.in scraping |
| **Graph Query Agent** | Finds company relationships and deals | Neo4j |
| **Risk Agent** | Deep dives red flags — spawned only if needed | Claude reasoning + RAG |
| **Critic Agent** | Argues against the thesis, finds weaknesses | Claude reasoning |
| **Report Agent** | Writes final human-readable investment brief | Claude API |
| **Screener Agent** | Filters 200 stocks down to 5-8 candidates | yfinance + rules engine |
| **Universe Agent** | Pulls full Nifty 50 + Midcap 150 stock list | NSE API |

---

## Tech Stack

| Component | Tool | Why |
|---|---|---|
| Backend | Python + FastAPI | Clean async API |
| Agent LLM | Claude API (claude-sonnet-4) | Reasoning + sentiment |
| Price Data | yfinance | Free, covers NSE (.NS suffix) |
| News | Google News RSS | Free, no API key |
| Fundamentals | Screener.in scraping | Best Indian stock data |
| PDF Parsing | pdfplumber + PyMuPDF | Already in use |
| Knowledge Graph | Neo4j | Industry standard graph DB |
| Vector Store | ChromaDB | Lightweight RAG |
| Embeddings | sentence-transformers | Local, free |
| Frontend | React + Tailwind | Dashboard UI |
| Real-time | WebSockets | Live agent progress |
| Storage | PostgreSQL (later) | Start with JSON files |

---

## Folder Structure

```
equity-analyst/
├── backend/
│   ├── main.py                        # FastAPI entry point
│   ├── orchestrator.py                # Core orchestrator agent
│   ├── agents/
│   │   ├── market_agent.py            # Price & volume data
│   │   ├── news_agent.py              # Headlines + sentiment
│   │   ├── fundamental_agent.py       # Financials
│   │   ├── graph_query_agent.py       # Knowledge graph queries
│   │   ├── risk_agent.py              # Red flag deep dive
│   │   ├── critic_agent.py            # Thesis challenger
│   │   ├── report_agent.py            # Final output writer
│   │   ├── screener_agent.py          # Stock filtering
│   │   └── universe_agent.py          # Stock list fetcher
│   ├── pipelines/
│   │   ├── pdf_downloader.py          # Downloads ARs from NSE
│   │   ├── pdf_extractor.py           # pdfplumber + PyMuPDF
│   │   ├── entity_extractor.py        # Claude extracts entities
│   │   ├── graph_builder.py           # Builds Neo4j graph
│   │   └── rag_builder.py             # Builds ChromaDB store
│   ├── tools/
│   │   ├── yfinance_tool.py           # Price data wrapper
│   │   ├── news_scraper.py            # Google News RSS
│   │   ├── screener_scraper.py        # Screener.in scraper
│   │   ├── neo4j_tool.py              # Graph DB wrapper
│   │   └── chroma_tool.py             # Vector store wrapper
│   └── models/
│       └── schemas.py                 # Pydantic models
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── SearchBar.jsx          # Query input
│           ├── AgentProgress.jsx      # Live agent status
│           ├── ReportView.jsx         # Final report display
│           ├── GraphVisualizer.jsx    # Knowledge graph viewer
│           └── StockCard.jsx          # Per-stock summary card
├── data/
│   ├── annual_reports/                # Downloaded PDFs
│   └── outputs/                       # Generated reports
├── .env
├── requirements.txt
└── README.md
```

---

## Sample Output

```
📊 AI Equity Research Report — May 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After screening 180 stocks across Nifty 50 and Midcap 150,
here are your top long-term picks:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🥇 TITAN COMPANY — Strong Buy
   PE: 72 | Debt: Minimal | Revenue Growth: 20% YoY
   Promoter Holding: 52.9% (stable)

   Fundamentals: Consistent 5-year revenue compounder.
   Jewellery and watches segments both growing.

   Graph Insight: Supply agreements with 3 Tata group
   companies. Preferred vendor status in Tanishq expansion.

   Sentiment: Bullish. 4 positive articles in last 7 days
   around festive season demand outlook.

   Risk Agent: Valuation is premium. Justified only if
   growth sustains above 15% for next 3 years.

   ⚠️ Critic Note: Luxury discretionary spend is
   cyclical — any slowdown in consumer confidence
   hits Titan disproportionately.

   Confidence: 81%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🥈 DIXON TECHNOLOGIES — Buy
   PE: 89 | Debt: Low | Revenue Growth: 68% YoY

   Graph Insight (KEY): Supply agreement signed with
   Reliance Jio in 2024 Annual Report (page 47).
   3 Nifty 50 companies are active customers.
   This is NOT visible in any screener.

   Sentiment: Neutral. Limited news coverage.

   Risk Agent: High PE justified by PLI scheme tailwinds
   and order book visibility for next 2 years.

   Confidence: 74%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🥉 COAL INDIA — Moderate Buy
   PE: 7 | Debt: None | Dividend Yield: 6.2%

   Fundamentals: Deeply undervalued. Cash-generating
   machine. High dividend provides downside protection.

   ⚠️ Risk: Long-term energy transition risk.
   10+ year horizon investors should watch renewables
   share in energy mix.

   Confidence: 68%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Portfolio Note:
All 3 picks are large-cap heavy. If you have higher
risk appetite, consider adding one quality midcap.
```

---

## Build Phases

### Phase 1 — Core Multiagent Skeleton (Weeks 1–2)
*Goal: Something working end to end, even if simple*

- [ ] FastAPI project setup
- [ ] Pydantic schemas for agent inputs/outputs
- [ ] Market Agent — yfinance price data
- [ ] News Agent — Google News RSS + Claude sentiment
- [ ] Fundamental Agent — Screener.in scraper
- [ ] Basic Orchestrator — sequential coordination
- [ ] CLI output of a full report
- [ ] Test with: RELIANCE, INFY, TITAN

### Phase 2 — PDF Pipeline + RAG (Weeks 3–4)
*Goal: Agents can read actual annual reports*

- [ ] PDF downloader from NSE website
- [ ] PDF extractor using pdfplumber + PyMuPDF
- [ ] Chunk and embed annual report text
- [ ] ChromaDB vector store setup
- [ ] RAG retrieval integrated into agents
- [ ] Agents now cite specific AR pages in output

### Phase 3 — Knowledge Graph (Weeks 5–6)
*Goal: System understands company relationships*

- [ ] Neo4j setup locally (Docker)
- [ ] Entity extractor — Claude reads AR, finds companies/deals/people
- [ ] Graph builder — populates Neo4j from extracted entities
- [ ] Graph Query Agent — answers relationship questions
- [ ] Orchestrator uses graph insights in thesis
- [ ] Test query: "Which small caps have Tata group deals?"

### Phase 4 — Dynamic Orchestration (Week 7)
*Goal: Make it genuinely multiagent, not just a pipeline*

- [ ] Risk Agent — spawned conditionally on red flags
- [ ] Critic Agent — argues against the thesis
- [ ] Orchestrator reads findings and decides next agent
- [ ] Parallel agent execution with asyncio
- [ ] Report Agent polished with structured output

### Phase 5 — Product & Dashboard (Week 8)
*Goal: Looks and feels like a real product*

- [ ] React dashboard setup
- [ ] WebSocket integration for live agent progress
- [ ] Agent progress panel (shows which agent is running)
- [ ] Report view with citations and confidence scores
- [ ] Graph visualizer (interactive company relationship map)
- [ ] All three query modes working
- [ ] README and documentation

---

## What You'll Learn

| Concept | Where You'll Learn It |
|---|---|
| Multiagent orchestration | Orchestrator + dynamic agent spawning |
| RAG pipeline from scratch | PDF → ChromaDB → context injection |
| Knowledge graphs | Neo4j + entity extraction |
| PDF extraction at scale | Pipeline 1 — extends existing work |
| Async Python | FastAPI + asyncio parallel agents |
| WebSockets | Live agent progress updates |
| Prompt engineering | Each agent has its own system prompt |
| Tool use / function calling | Agents calling yfinance, Neo4j, ChromaDB |

---

## Why This Project Stands Out

- **No screener does this** — knowledge graph from annual reports is unique
- **Genuinely multiagent** — orchestrator dynamically decides, agents react to each other
- **Real data** — not mock data, actual NSE filings and live prices
- **Extends your existing work** — PDF pipeline you're building is the core data layer
- **Strong portfolio piece** — combines RAG + knowledge graphs + multiagent in one system
- **Solves a real problem** — retail investors in India genuinely need this

---

## Key Decisions Made

| Decision | Choice | Reason |
|---|---|---|
| Fine-tuning vs RAG | RAG | Claude already knows finance; RAG gives fresh, traceable data |
| Graph DB | Neo4j | Industry standard, great query language (Cypher) |
| Vector store | ChromaDB | Lightweight, no infra needed |
| Start simple | JSON files first | No DB complexity until Phase 4 |
| Agent communication | Structured JSON | Each agent returns findings + red_flags + confidence |

---

*Start with Phase 1. Ship something working fast. Add intelligence layer by layer.*
