"""FastAPI backend for BillFlow RAG services with Contract Intelligence."""

from typing import List, Literal, Optional, Dict, Any
import os
import json
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from openai import AzureOpenAI

from rag_chat import get_chain, ask
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    INDEX_DIR,
    COLLECTION_NAME,
)
from contract_intelligence import get_intelligence_service
from revenue_intelligence import get_revenue_intelligence

app = FastAPI(title="BillFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global chain and retriever once
CHAIN_TUPLE = get_chain()


def _refresh_chain():
    global CHAIN_TUPLE
    CHAIN_TUPLE = get_chain()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    session_id: Optional[str] = None


class Source(BaseModel):
    source: str
    page: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]


class STTResponse(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/contracts")
def list_contracts():
    """Return lightweight contract metadata for browsing."""
    path = os.path.join(os.path.dirname(__file__), "contract_data.json")
    if not os.path.exists(path):
        return {"contracts": []}
    
    with open(path, "r") as f:
        data = json.load(f)
    
    # Handle both old (ISP consumer) and new (B2B billing) formats
    contracts = []
    for c in data:
        # New B2B billing format
        if "client_name" in c:
            contracts.append({
                "id": c["index"],
                "company": c["client_name"],
                "contract_number": c["contract_number"],
                "client_tier": c["client_tier"],
                "billing_model": c["billing_model"],
                "our_monthly_revenue": c["our_monthly_revenue"],
                "annual_contract_value": c["annual_contract_value"],
                "subscriber_count": c["subscriber_count"],
                "term_months": c["contract_length_months"],
                "end_date": c["end_date"],
                "billing_accuracy_sla": c["billing_accuracy_sla"],
                "city": c["city"],
                "state": c["state"],
            })
        # Old ISP consumer format (backwards compatibility)
        else:
            contracts.append({
                "id": c["index"],
                "company": c["company_name"],
                "contract_number": c["contract_number"],
                "client_tier": c.get("plan_name", "Standard"),
                "billing_model": "Flat Fee",
                "our_monthly_revenue": c.get("price", 0),
                "annual_contract_value": c.get("annual_cost", c.get("price", 0) * 12),
                "subscriber_count": 1,
                "term_months": c["contract_length_months"],
                "end_date": c["end_date"],
                "billing_accuracy_sla": 99.5,
                "city": c["city"],
                "state": c["state"],
            })
    return {"contracts": contracts, "total": len(contracts)}


@app.get("/metrics")
def get_metrics():
    """Return portfolio metrics for billing contractor dashboard."""
    path = os.path.join(os.path.dirname(__file__), "contract_data.json")
    if not os.path.exists(path):
        return {"error": "No contract data"}
    
    with open(path, "r") as f:
        data = json.load(f)
    
    # Check format
    is_b2b = "client_name" in data[0] if data else False
    
    if is_b2b:
        total_acv = sum(c["annual_contract_value"] for c in data)
        total_monthly = sum(c["our_monthly_revenue"] for c in data)
        total_subscribers = sum(c["subscriber_count"] for c in data)
        avg_sla = sum(c["billing_accuracy_sla"] for c in data) / len(data)
        
        # Contracts by tier
        tiers = {}
        for c in data:
            tier = c["client_tier"]
            tiers[tier] = tiers.get(tier, 0) + 1
        
        # Expiring soon (next 90 days) - simplified check
        expiring_count = sum(1 for c in data if "2024" in c["end_date"] and "December" in c["end_date"])
        
        return {
            "total_contracts": len(data),
            "total_acv": round(total_acv, 2),
            "monthly_revenue": round(total_monthly, 2),
            "total_subscribers": total_subscribers,
            "avg_billing_accuracy_sla": round(avg_sla, 2),
            "contracts_by_tier": tiers,
            "expiring_soon": expiring_count,
        }
    else:
        # Legacy format
        return {
            "total_contracts": len(data),
            "total_acv": 0,
            "monthly_revenue": 0,
            "total_subscribers": 0,
            "avg_billing_accuracy_sla": 99.5,
            "contracts_by_tier": {},
            "expiring_soon": 0,
        }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Main chat endpoint."""
    history_tuples = [(m.role, m.content) for m in req.history]

    answer, docs = ask(CHAIN_TUPLE, req.message, history_tuples)

    sources = []
    for d in docs:
        meta = getattr(d, "metadata", {}) or {}
        sources.append(
            Source(
                source=str(meta.get("source", "?")),
                page=meta.get("page"),
            )
        )

    return ChatResponse(answer=answer, sources=sources)


@app.post("/regenerate", response_model=ChatResponse)
def regenerate(req: ChatRequest):
    """Regenerate response for the same last user message."""
    return chat(req)


@app.post("/upload")
async def upload_file(
    session_id: Optional[str] = Form(default="default"),
    file: UploadFile = File(...),
):
    """
    Upload a PDF or image and add its contents to the vector store.

    PDFs are parsed directly; images currently need a manual OCR/vision
    pass and are acknowledged but not embedded.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    filename = file.filename
    content_type = file.content_type or ""

    # Handle PDFs: parse and embed immediately.
    if filename.lower().endswith(".pdf") or "pdf" in content_type:
        # Save to a temp file so PyPDFLoader can read it
        suffix = ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
            )
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            docs = splitter.split_documents(docs)

            # Tag docs with session for future filtering if needed
            for d in docs:
                d.metadata = d.metadata or {}
                d.metadata.setdefault("session_id", session_id)

            embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_KEY,
                api_version=AZURE_OPENAI_API_VERSION,
                model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            )

            db = Chroma(
                persist_directory=INDEX_DIR,
                collection_name=COLLECTION_NAME,
                embedding_function=embeddings,
            )
            db.add_documents(docs)
        finally:
            os.unlink(tmp_path)

        # Reload chain so new docs are visible to retriever
        _refresh_chain()

        return {"filename": filename, "session_id": session_id, "embedded": True}

    # For now, images are acknowledged but not embedded.
    if content_type.startswith("image/"):
        return {
            "filename": filename,
            "session_id": session_id,
            "embedded": False,
            "note": "Image upload acknowledged; add OCR/vision pipeline to embed.",
        }

    raise HTTPException(status_code=400, detail="Unsupported file type")


@app.post("/stt", response_model=STTResponse)
async def speech_to_text(file: UploadFile = File(...)):
    """Speech-to-text using Azure/OpenAI audio transcription."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No audio provided")

    audio_bytes = await file.read()

    client = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION,
    )

    model = os.getenv("AZURE_OPENAI_STT_DEPLOYMENT")
    if not model:
        # Fallback: echo-only if no STT deployment is configured
        return STTResponse(text="[STT model not configured]")

    try:
        result = client.audio.transcriptions.create(
            model=model,
            file=audio_bytes,
        )
        return STTResponse(text=result.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")


class ScenarioRequest(BaseModel):
    scenario: Literal["early_termination"]
    month: int
    client_names: List[str]


@app.post("/scenario")
def scenario(req: ScenarioRequest):
    """
    Simple scenario simulator using structured contract_data.json.

    Currently supports:
    - early_termination: compute total cost if cancelling at a given month for B2B billing clients.
    """
    path = os.path.join(os.path.dirname(__file__), "contract_data.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="contract_data.json not found")

    with open(path, "r") as f:
        data = json.load(f)

    # Support both B2B format (client_name) and legacy format (company_name)
    contracts = {}
    for c in data:
        name = c.get("client_name") or c.get("company_name")
        if name:
            contracts[name] = c
    
    missing = [n for n in req.client_names if n not in contracts]
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown clients: {', '.join(missing)}")

    if req.scenario == "early_termination":
        rows = []
        for name in req.client_names:
            c = contracts[name]
            months = c["contract_length_months"]
            paid_months = min(req.month, months)
            # B2B format uses our_monthly_revenue; legacy uses price
            monthly = c.get("our_monthly_revenue") or c.get("price", 0)
            etf = c.get("early_termination_fee", 0) if req.month < months else 0
            total_paid = round(paid_months * monthly, 2)
            total_cost = round(total_paid + etf, 2)
            rows.append(
                {
                    "client_name": name,
                    "contract_number": c.get("contract_number", "N/A"),
                    "monthly_revenue": monthly,
                    "contract_months": months,
                    "cancel_month": req.month,
                    "amount_paid": total_paid,
                    "early_termination_fee": etf,
                    "total_cost": total_cost,
                }
            )

        # Sort by total cost ascending
        rows.sort(key=lambda r: r["total_cost"])
        return {
            "scenario": req.scenario,
            "rows": rows,
            "lowest_cost_client": rows[0]["client_name"] if rows else None,
        }

    raise HTTPException(status_code=400, detail="Unsupported scenario type")


# =============================================================================
# CONTRACT INTELLIGENCE ENDPOINTS
# =============================================================================

# Feature 1 & 2: Risk Scoring and Clause Analysis
@app.get("/intelligence/risk")
def get_portfolio_risk():
    """Get risk analysis for entire portfolio with clause extraction."""
    service = get_intelligence_service()
    return service.get_portfolio_risk_analysis()


@app.get("/intelligence/risk/{contract_id}")
def get_contract_risk(contract_id: int):
    """Get risk analysis for a specific contract."""
    service = get_intelligence_service()
    result = service.get_contract_risk(contract_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# Feature 3: Churn Prediction
@app.get("/intelligence/churn")
def get_portfolio_churn():
    """Get churn predictions for entire portfolio."""
    service = get_intelligence_service()
    return service.get_portfolio_churn_analysis()


@app.get("/intelligence/churn/{contract_id}")
def get_contract_churn(contract_id: int):
    """Get churn prediction for a specific contract."""
    service = get_intelligence_service()
    result = service.get_contract_churn(contract_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# Feature 4: Scenario Simulation
class ScenarioSimRequest(BaseModel):
    scenario_type: Literal["rate_change", "client_loss", "sla_standardization", "revenue_forecast"]
    params: Dict[str, Any]


@app.post("/intelligence/simulate")
def simulate_scenario_advanced(req: ScenarioSimRequest):
    """
    Run what-if scenario simulations.
    
    Scenario types:
    - rate_change: { tier?: string, billing_model?: string, rate_change_pct: number }
    - client_loss: { client_names: string[] }
    - sla_standardization: { target_sla: number }
    - revenue_forecast: { months: number, churn_rate_pct: number, growth_rate_pct: number }
    """
    service = get_intelligence_service()
    result = service.simulate_scenario(req.scenario_type, req.params)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# Feature 5: Contract Generation
class GenerateContractRequest(BaseModel):
    description: str


@app.post("/intelligence/generate")
def generate_contract(req: GenerateContractRequest):
    """
    Generate a new contract from natural language description.
    
    Example: "Create a Business tier contract for TechCorp with 75,000 subscribers,
    3% revenue share, 99.7% billing SLA, and 36-month term"
    """
    service = get_intelligence_service()
    try:
        result = service.generate_contract(req.description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


# Feature 6: Contract Comparison
class CompareContractsRequest(BaseModel):
    contract_id_a: int
    contract_id_b: int


@app.post("/intelligence/compare")
def compare_contracts(req: CompareContractsRequest):
    """Compare two contracts and highlight differences."""
    service = get_intelligence_service()
    result = service.compare_contracts(req.contract_id_a, req.contract_id_b)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# Benchmarks
@app.get("/intelligence/benchmarks")
def get_benchmarks():
    """Get portfolio benchmarks for comparison."""
    service = get_intelligence_service()
    return service.get_benchmarks()


# Refresh intelligence data
@app.post("/intelligence/refresh")
def refresh_intelligence():
    """Reload contract data and recalculate benchmarks."""
    service = get_intelligence_service()
    service.refresh_contracts()
    return {"status": "refreshed", "contracts_loaded": len(service.contracts)}


# =============================================================================
# REVENUE INTELLIGENCE ENDPOINTS - Next-Gen CRM Engine
# =============================================================================

@app.get("/revenue/command-center")
def get_revenue_command_center():
    """
    The main revenue intelligence dashboard.
    Returns: leakages, opportunities, signals, action queue, genome analysis.
    """
    service = get_revenue_intelligence()
    return service.get_revenue_command_center()


@app.get("/revenue/executive-summary")
def get_executive_summary():
    """High-level executive summary of portfolio revenue health."""
    service = get_revenue_intelligence()
    return service.get_executive_summary()


@app.get("/revenue/leakage")
def get_leakage_report():
    """Detailed revenue leakage analysis - where money is being lost."""
    service = get_revenue_intelligence()
    return service.get_leakage_report()


@app.get("/revenue/opportunities")
def get_opportunity_report():
    """Detailed opportunity analysis - where money is available."""
    service = get_revenue_intelligence()
    return service.get_opportunity_report()


@app.get("/revenue/signals")
def get_signal_report():
    """All detected client signals - early warnings and opportunities."""
    service = get_revenue_intelligence()
    return service.get_signal_report()


@app.get("/revenue/actions")
def get_action_queue():
    """Prioritized action queue - what to do next."""
    service = get_revenue_intelligence()
    return service.get_action_queue()


@app.get("/revenue/genome")
def get_all_genomes():
    """Deal genome analysis for all contracts."""
    service = get_revenue_intelligence()
    return service.get_genome_analysis()


@app.get("/revenue/genome/{contract_id}")
def get_contract_genome(contract_id: int):
    """Deal genome analysis for a specific contract."""
    service = get_revenue_intelligence()
    result = service.get_genome_analysis(contract_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


class GenerateOutreachRequest(BaseModel):
    action_id: str


@app.post("/revenue/generate-outreach")
def generate_outreach(req: GenerateOutreachRequest):
    """Generate personalized outreach script for an action using AI."""
    service = get_revenue_intelligence()
    result = service.generate_outreach(req.action_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


