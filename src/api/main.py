"""
Pharma Agentic AI - FastAPI Backend
REST API for programmatic access to the multi-agent system.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infra.tasks import submit_job
from src.infra.state import job_state_store, JobStatus
from src.services.logging_config import setup_logging
from src.config.settings import settings
from src.services.orchestrator import MasterOrchestrator

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pharma Agentic AI API",
    description="Multi-Agent Intelligence Platform for Pharmaceutical Strategy",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for agent queries."""
    query: str
    generate_pdf: bool = False
    generate_excel: bool = False


class QueryResponse(BaseModel):
    """Response model for agent queries."""
    query: str
    response: str
    agents_used: List[str]
    sources: List[str]
    reports: List[Dict[str, str]]
    timestamp: str
    execution_time_ms: float


class ToolQueryRequest(BaseModel):
    """Request model for direct tool queries."""
    tool_name: str
    parameters: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str


class JobRequest(BaseModel):
    """Async job submission request."""
    query: str
    context: Optional[Dict[str, Any]] = None


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    updated_at: Optional[float] = None


# Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health check."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.post("/jobs", response_model=JobSubmitResponse)
async def submit_job_endpoint(request: JobRequest):
    """Submit an asynchronous multi-agent job."""
    # If async queue disabled, run synchronously and store result
    if not settings.USE_ASYNC_QUEUE:
        job_id = uuid4().hex
        orchestrator = MasterOrchestrator()
        result_obj = orchestrator.process_query(request.query, request.context)
        job_state_store.set(
            job_id,
            JobStatus.DONE,
            result=str(result_obj.content),
            meta={"finished_at": int(datetime.now().timestamp() * 1000), "duration_ms": 0},
        )
        return JobSubmitResponse(
            job_id=job_id,
            status=JobStatus.DONE,
            submitted_at=datetime.now().isoformat(),
        )

    job_info = submit_job(request.query, request.context or {})
    return JobSubmitResponse(
        job_id=job_info["job_id"],
        status=JobStatus.QUEUED,
        submitted_at=datetime.now().isoformat(),
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Check status/result for a previously submitted job."""
    state = job_state_store.get(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatusResponse(
        job_id=job_id,
        status=state.status,
        result=state.result,
        error=state.error,
        updated_at=state.updated_at,
    )


@app.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    """
    Run a multi-agent query.
    
    This endpoint orchestrates multiple specialized agents to answer
    complex pharmaceutical strategy questions.
    """
    start_time = datetime.now()
    orchestrator = MasterOrchestrator()

    try:
        result_obj = orchestrator.process_query(request.query)
        response_text = result_obj.content
        agents_used = [r.agent_type.value for r in result_obj.individual_responses if r.success]

        source_map = {
            "market": "IQVIA Market Database",
            "patent": "USPTO Patent Database",
            "clinical": "Clinical Trials Registry",
            "patient": "Patient Forums & Social Media",
            "competitor": "Competitive Intelligence Reports",
            "internal": "Internal Strategy Documents",
            "trade": "EXIM Trade Database",
            "web": "Web Intelligence",
            "general": "General LLM"
        }
        sources = [source_map.get(a.lower(), a) for a in agents_used]

        reports = []
        if request.generate_pdf:
            from src.services.report_generator import generate_pdf_report
            pdf_path = generate_pdf_report(
                title="Pharma Strategy Analysis",
                query=request.query,
                content=response_text,
                metadata={"agents_used": agents_used}
            )
            if pdf_path and not pdf_path.startswith("Error"):
                reports.append({"type": "PDF", "path": pdf_path})

        if request.generate_excel:
            from src.services.report_generator import generate_excel_report
            data = {"findings": [], "recommendations": []}
            excel_path = generate_excel_report(
                title="Pharma Strategy Analysis",
                query=request.query,
                data=data,
                metadata={"agents_used": agents_used}
            )
            if excel_path and not excel_path.startswith("Error"):
                reports.append({"type": "Excel", "path": excel_path})

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return QueryResponse(
            query=request.query,
            response=response_text,
            agents_used=agents_used,
            sources=sources,
            reports=reports,
            timestamp=datetime.now().isoformat(),
            execution_time_ms=round(execution_time, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: ToolQueryRequest):
    """
    Directly call a specific tool.
    
    Available tools:
    - query_iqvia_market
    - query_patents
    - query_exim_trade
    - query_clinical_trials
    - query_social_media
    - query_competitor_intel
    - search_internal_docs
    - web_search
    """
    try:
        # Import tools
        from src.tools import (
            query_iqvia_market,
            query_patents,
            query_exim_trade,
            query_clinical_trials,
            query_social_media,
            query_competitor_intel,
            search_internal_docs
        )
        from src.tools.web_tool import web_search
        
        tools = {
            "query_iqvia_market": query_iqvia_market,
            "query_patents": query_patents,
            "query_exim_trade": query_exim_trade,
            "query_clinical_trials": query_clinical_trials,
            "query_social_media": query_social_media,
            "query_competitor_intel": query_competitor_intel,
            "search_internal_docs": search_internal_docs,
            "web_search": web_search
        }
        
        if tool_name not in tools:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found. Available: {list(tools.keys())}"
            )
        
        tool_func = tools[tool_name]
        result = tool_func._run(**request.parameters)
        
        return {
            "tool": tool_name,
            "parameters": request.parameters,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents")
async def list_agents():
    """List all available agents and their capabilities."""
    return {
        "agents": [
            {
                "id": "iqvia",
                "name": "IQVIA Market Agent",
                "role": "Market Data Specialist",
                "capabilities": ["Market size analysis", "CAGR trends", "Competitor mapping", "Whitespace identification"]
            },
            {
                "id": "patent",
                "name": "Patent Landscape Agent",
                "role": "IP Legal Analyst",
                "capabilities": ["Patent expiry tracking", "FTO assessment", "Generic entry analysis"]
            },
            {
                "id": "exim",
                "name": "EXIM Trade Agent",
                "role": "Supply Chain Analyst",
                "capabilities": ["Import/export volumes", "Pricing trends", "Supply chain risk assessment"]
            },
            {
                "id": "clinical",
                "name": "Clinical Trials Agent",
                "role": "R&D Pipeline Analyst",
                "capabilities": ["Trial landscape analysis", "Repurposing opportunities", "Competition density"]
            },
            {
                "id": "social",
                "name": "Social Listening Agent",
                "role": "Patient Voice Analyst",
                "capabilities": ["Sentiment analysis", "Complaint themes", "Innovation opportunities"]
            },
            {
                "id": "competitor",
                "name": "Competitor Agent",
                "role": "Strategic War Gamer",
                "capabilities": ["Competitor prediction", "War gaming", "Threat assessment"]
            },
            {
                "id": "internal",
                "name": "Internal Knowledge Agent",
                "role": "Corporate Strategist",
                "capabilities": ["Document search", "Strategy alignment", "Institutional knowledge"]
            },
            {
                "id": "web",
                "name": "Web Intelligence Agent",
                "role": "External Researcher",
                "capabilities": ["News monitoring", "FDA approvals", "Market developments"]
            }
        ]
    }


@app.get("/examples")
async def get_examples():
    """Get example queries for testing."""
    return {
        "examples": [
            {
                "name": "Whitespace Analysis",
                "query": "Which respiratory diseases show low competition but high patient burden in India?",
                "expected_agents": ["iqvia", "clinical"]
            },
            {
                "name": "Repurposing Opportunities",
                "query": "Identify potential repurposing opportunities for Pembrolizumab.",
                "expected_agents": ["clinical", "patent"]
            },
            {
                "name": "FTO Check",
                "query": "Check patent expiry for Sitagliptin in the US.",
                "expected_agents": ["patent"]
            },
            {
                "name": "Patient Voice",
                "query": "What are patients complaining about regarding current Diabetes injectables?",
                "expected_agents": ["social"]
            },
            {
                "name": "War Game",
                "query": "Simulate a launch of generic Rivaroxaban in 2025. What will competitors do?",
                "expected_agents": ["competitor", "patent"]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
