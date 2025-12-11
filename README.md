# BillFlow

A full-stack contract intelligence platform demonstrating RAG architecture, AI-powered analytics, and modern web development.

![Dashboard](screenshots/dashboard.png)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│              TypeScript · Tailwind CSS · Vite                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                          │
│                    REST API · Async · CORS                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │   RAG Chain  │ │  Intelligence│ │   Revenue    │
        │   LangChain  │ │    Engine    │ │    Engine    │
        └──────────────┘ └──────────────┘ └──────────────┘
                │               │               │
                └───────────────┼───────────────┘
                                ▼
        ┌──────────────────────────────────────────────┐
        │              ChromaDB Vector Store           │
        │         Embeddings · MMR Retrieval           │
        └──────────────────────────────────────────────┘
                                │
                                ▼
        ┌──────────────────────────────────────────────┐
        │              Azure OpenAI                    │
        │       GPT-5-nano · text-embedding-3-small   │
        └──────────────────────────────────────────────┘
```

## Features

### RAG-Powered Document Q&A
![Chat](screenshots/chat.png)

- Natural language queries across 100+ contract documents
- MMR (Maximal Marginal Relevance) retrieval for diverse, relevant results
- Source citation with document references
- Conversation context maintained across queries

### Contract Risk Analysis
![Intelligence](screenshots/intelligence.png)

- Automated risk scoring based on contract terms
- Churn probability prediction with contributing factors
- Side-by-side contract comparison
- What-if scenario modeling for term changes
- AI-assisted contract generation from natural language

### Revenue Analytics Dashboard
![Revenue Command Center](screenshots/revenue.png)

- Multi-tab analytics interface (Leakage, Opportunities, Signals, Actions)
- Prioritized action queue with impact scoring
- Client signal detection and alerting
- AI-generated outreach content

#### Drill-Down Views

| Leakage Detection | Opportunity Identification |
|-------------------|---------------------------|
| ![Leakage](screenshots/revenue-leakage.png) | ![Opportunities](screenshots/revenue-opportunities.png) |

| Signal Monitoring | Action Queue |
|-------------------|--------------|
| ![Signals](screenshots/revenue-signals.png) | ![Actions](screenshots/revenue-actions.png) |

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React 18, TypeScript, Tailwind CSS, Vite |
| **Backend** | FastAPI, Python 3.12, Pydantic |
| **AI/ML** | LangChain, Azure OpenAI (GPT-5-nano), ChromaDB |
| **Document Processing** | PyPDF, tiktoken, text-splitters |

## Implementation Highlights

### RAG Pipeline
- Chunking strategy: 1500 characters with 200 overlap
- Embedding model: `text-embedding-3-small` (1536 dimensions)
- Retrieval: MMR with k=60 for multi-document comparison queries
- Vector store: ChromaDB with persistent local storage

### API Design
- RESTful endpoints with Pydantic validation
- Async request handling
- Structured error responses
- CORS configuration for frontend integration

### Frontend Architecture
- Single-page application with client-side routing
- Real-time state management with React hooks
- Responsive design with Tailwind utilities
- Dark mode UI for analytics dashboards

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Natural language contract queries |
| `GET` | `/contracts` | List contracts with metadata |
| `GET` | `/metrics` | Portfolio aggregations |
| `GET` | `/intelligence/risk` | Risk analysis results |
| `GET` | `/intelligence/churn` | Churn predictions |
| `POST` | `/intelligence/simulate` | What-if scenario modeling |
| `POST` | `/intelligence/compare` | Contract comparison |
| `POST` | `/intelligence/generate` | AI contract generation |
| `GET` | `/revenue/command-center` | Revenue analytics data |
| `POST` | `/revenue/generate-outreach` | AI-generated outreach content |

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Azure OpenAI API access

### Setup

```bash
# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure Azure OpenAI credentials

# Generate sample data
python generate_contracts.py
python ingestion.py

# Start API server
uvicorn backend_api:app --port 8001
```

```bash
# Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Project Structure

```
├── backend_api.py           # FastAPI application
├── rag_chat.py              # LangChain RAG implementation
├── contract_intelligence.py # Risk and churn analysis
├── revenue_intelligence.py  # Revenue analytics engine
├── ingestion.py             # Document processing pipeline
├── config.py                # Configuration management
├── generate_contracts.py    # Synthetic data generation
├── data/                    # Contract documents
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main application
│   │   ├── main.tsx         # Entry point
│   │   └── index.css        # Tailwind styles
│   └── package.json
└── screenshots/
```

---

[![LangChain](https://img.shields.io/badge/LangChain-Framework-blue)](https://langchain.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-Language-3178C6)](https://www.typescriptlang.org)
