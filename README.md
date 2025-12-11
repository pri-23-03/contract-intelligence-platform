# BillFlow - Autonomous Revenue Intelligence Platform

> **The Next Generation of CRM** - Not a dashboard. Not a report. An AI that finds money you're losing, discovers money you're missing, tells you exactly what to do, and does it for you.

## 🧠 What Makes This Different

Traditional CRMs track what happened. BillFlow **tells you what to do next** and **does it automatically**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    REVENUE COMMAND CENTER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   💸 LEAKAGE DETECTED          💰 OPPORTUNITIES FOUND           │
│   ━━━━━━━━━━━━━━━━━━━━        ━━━━━━━━━━━━━━━━━━━━              │
│   $847,000/year                $1.2M/year                       │
│   Money being lost             Ready to capture                  │
│                                                                  │
│   ⚡ CRITICAL ACTIONS          🧬 PORTFOLIO HEALTH               │
│   ━━━━━━━━━━━━━━━━━━━━        ━━━━━━━━━━━━━━━━━━━━              │
│   7 require immediate          72/100                           │
│   attention                    Genome score                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Core Capabilities

### 1. Revenue Leakage Detection
AI finds every way you're losing money:
- **Pricing Leakage** - Below-market rates, missed escalations
- **Volume Leakage** - Unused thresholds, unpriced growth
- **Billing Leakage** - Late payments, uncollected fees
- **SLA Leakage** - Over-delivery without compensation
- **Term Leakage** - Unfavorable terms costing money

### 2. Revenue Opportunity Discovery
AI finds money you're not capturing:
- **Tier Upgrades** - Clients ready to move up
- **Volume Expansion** - Growth trajectory capture
- **Model Optimization** - Better billing model fits
- **Term Extensions** - Commitment incentives
- **Service Upsells** - Compliance, premium support

### 3. Signal Detection Engine
Early warnings before problems manifest:
- Renewal risk signals
- Engagement drops
- Payment delays
- Expansion indicators
- Competitor mentions (coming soon)

### 4. Autonomous Action Queue
AI-prioritized actions with one-click execution:
- Critical/High/Medium/Opportunity urgency levels
- Revenue impact for every action
- Prerequisites and success metrics
- **AI-generated outreach scripts** (email + call)
- Auto-executable actions (with approval)

### 5. Deal Genome Analyzer
DNA of every contract:
- Success score (0-100)
- 6 genome markers (pricing, terms, SLA, compliance, payment, growth)
- Similar deal pattern matching
- Predicted outcome
- Optimization suggestions

### 6. Contract Intelligence Suite
- Risk scoring & red flag detection
- Churn prediction engine
- What-if scenario simulation
- Contract comparison (20+ fields)
- Natural language contract generation

## Quick Start

```bash
# Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add Azure keys

python generate_contracts.py  # Generate portfolio
python ingestion.py           # Build vector store
uvicorn backend_api:app --reload --port 8001

# Frontend
cd frontend && npm install && npm run dev
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │Dashboard │ │ RAG Chat │ │Intel Hub │ │ Revenue Command  │   │
│  │          │ │          │ │          │ │     Center       │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INTELLIGENCE LAYER                          │
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────────────────────┐   │
│  │  RAG Engine     │     │   Revenue Intelligence Engine   │   │
│  │  • MMR Retrieval│     │   • Leakage Detector           │   │
│  │  • LLM Reasoning│     │   • Opportunity Finder         │   │
│  │  • Context Fusion│    │   • Signal Detector            │   │
│  └─────────────────┘     │   • Action Engine              │   │
│                          │   • Genome Analyzer            │   │
│  ┌─────────────────┐     │   • Script Generator           │   │
│  │Contract Intel   │     └─────────────────────────────────┘   │
│  │  • Risk Scoring │                                           │
│  │  • Churn Predict│                                           │
│  │  • Scenarios    │                                           │
│  │  • Generation   │                                           │
│  └─────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       ┌─────────────┐                 ┌─────────────┐
       │  ChromaDB   │                 │ Azure OpenAI│
       │ (Embeddings)│                 │ (LLM + Gen) │
       └─────────────┘                 └─────────────┘
```

## API Reference

### Revenue Intelligence
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/revenue/command-center` | GET | Full command center data |
| `/revenue/executive-summary` | GET | High-level summary |
| `/revenue/leakage` | GET | Detailed leakage report |
| `/revenue/opportunities` | GET | Opportunity pipeline |
| `/revenue/signals` | GET | All detected signals |
| `/revenue/actions` | GET | Prioritized action queue |
| `/revenue/genome` | GET | All deal genomes |
| `/revenue/genome/{id}` | GET | Single contract genome |
| `/revenue/generate-outreach` | POST | AI outreach script |

### Contract Intelligence
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/intelligence/risk` | GET | Portfolio risk analysis |
| `/intelligence/churn` | GET | Churn predictions |
| `/intelligence/simulate` | POST | What-if scenarios |
| `/intelligence/compare` | POST | Contract comparison |
| `/intelligence/generate` | POST | Generate from NL |

### Core
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | RAG conversation |
| `/contracts` | GET | Contract list |
| `/metrics` | GET | Portfolio metrics |
| `/upload` | POST | Add new contracts |

## Files

| File | Purpose |
|------|---------|
| `revenue_intelligence.py` | **Core** - Leakage, opportunities, signals, actions, genome |
| `contract_intelligence.py` | Risk scoring, churn prediction, scenarios, generation |
| `rag_chat.py` | RAG chain with domain prompts |
| `backend_api.py` | FastAPI with all endpoints |
| `frontend/src/App.tsx` | React UI with 4 views |

## What's Next

### Coming Soon
- [ ] **Email Integration** - Auto-draft and send from action queue
- [ ] **Calendar Integration** - Auto-schedule meetings from actions
- [ ] **CRM Sync** - Bidirectional Salesforce/HubSpot sync
- [ ] **Competitor Intelligence** - Detect when clients are shopping
- [ ] **Voice Actions** - "Generate renewal proposal for Sky Digital"
- [ ] **Mobile Alerts** - Push notifications for critical signals
- [ ] **Slack/Teams Bot** - Query revenue intelligence from chat

### The Vision
This isn't software. It's a **revenue operations AI** that:
1. **Sees** everything happening in your contract portfolio
2. **Understands** patterns humans miss
3. **Recommends** the highest-impact actions
4. **Executes** with your approval
5. **Learns** from every outcome

## Tech Stack

- **FastAPI** - High-performance API
- **React + Tailwind** - Modern, responsive UI
- **LangChain** - RAG with MMR retrieval
- **ChromaDB** - Vector embeddings
- **Azure OpenAI** - GPT + embeddings
- **Python 3.11+** - Intelligence engines
