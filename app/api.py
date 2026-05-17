from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import shutil
from typing import List, Optional, Dict, Any

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from agents.orchestrator import OrchestratorAgent
from demo_data.generate_data import generate_all_demo_data

app = FastAPI(title="NeuralNexus API")

# Setup CORS to allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Orchestrator State
# (In a real app, use a proper session/state management system, but this works for local use)
state = {
    "orchestrator": OrchestratorAgent(),
    "initialized": False,
    "chat_history": [],
    "proactive_insights": None,
    "reconciliation_results": None,
}

def get_orch() -> OrchestratorAgent:
    return state["orchestrator"]

class QueryRequest(BaseModel):
    query: str

class InitDemoResponse(BaseModel):
    message: str
    sources_count: int

@app.get("/")
def read_root():
    return {"status": "active", "initialized": state["initialized"]}

@app.post("/api/init_demo")
def init_demo():
    orch = get_orch()
    try:
        demo_paths = generate_all_demo_data()
        result = orch.ingest_data(
            list(demo_paths.values()),
            ["Sales Database", "Financial Report", "Inventory API", "HR Headcount", "Market Feed"],
            [0.80, 0.95, 0.80, 0.75, 0.65],
        )
        state["initialized"] = True
        return InitDemoResponse(message="Demo data initialized and analyzed successfully.", sources_count=len(orch.federation.sources))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    source_name: Optional[str] = Form(None),
    credibility: float = Form(0.75)
):
    orch = get_orch()
    name = source_name if source_name else file.filename
    tmp_path = os.path.join(PROJECT_ROOT, "demo_data", "uploads", file.filename)
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
    
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        orch.federation.ingest_auto(tmp_path, source_name=name, credibility=credibility)
        state["initialized"] = True
        return {"message": f"{name} ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
def query_data(req: QueryRequest):
    orch = get_orch()
    if not state["initialized"]:
        raise HTTPException(status_code=400, detail="Fabric not initialized. Please load data first.")
    
    try:
        result = orch.process_query(req.query)
        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0),
            "contradictions_found": result.get("contradictions_found", 0),
            "retrieved_chunks": result.get("retrieved_chunks", 0),
            "specialist_insights": result.get("specialist_insights", {}),
            "review": result.get("review", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query_stream")
def query_data_stream(req: QueryRequest):
    orch = get_orch()
    if not state["initialized"]:
        raise HTTPException(status_code=400, detail="Fabric not initialized. Please load data first.")
    
    try:
        return StreamingResponse(
            orch.process_query_stream(req.query),
            media_type="application/x-ndjson"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
def run_full_analysis():
    orch = get_orch()
    if not state["initialized"] or not orch.federation.sources:
        raise HTTPException(status_code=400, detail="No data sources to analyze.")
    try:
        orch.quality_reports = orch.quality_scorer.score_all(orch.federation.sources)
        orch.contradictions = orch.contradiction_detector.detect_all(orch.federation.sources)
        orch.validator.scan_all(orch.federation.sources, orch.quality_reports)
        orch._build_knowledge_graph()
        orch._build_vector_store_local()
        orch.is_initialized = True
        return {"message": "Full analysis complete."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clear")
def clear_all_data():
    global state
    state["orchestrator"] = OrchestratorAgent()
    state["initialized"] = False
    state["chat_history"] = []
    state["proactive_insights"] = None
    state["reconciliation_results"] = None
    return {"message": "All data cleared successfully."}

@app.get("/api/quality_dashboard")
def get_quality_dashboard():
    orch = get_orch()
    if not orch.quality_reports:
        return {"reports": [], "issues": []}
    
    reports = []
    issues = []
    
    for sid, rpt in orch.quality_reports.items():
        reports.append({
            "source_id": sid,
            "source_name": rpt.source_name,
            "overall_score": rpt.overall_score,
            "grade": rpt.grade,
            "completeness_score": rpt.completeness_score,
            "consistency_score": rpt.consistency_score,
            "timeliness_score": rpt.timeliness_score,
        })
        for iss in rpt.issues:
            issues.append({
                "source_name": rpt.source_name,
                "severity": iss["severity"].upper(),
                "type": iss["type"],
                "description": iss["message"]
            })
            
    return {"reports": reports, "issues": issues}

@app.get("/api/contradictions")
def get_contradictions():
    orch = get_orch()
    if not orch.contradictions:
        return {"contradictions": [], "summary": {"total": 0, "high": 0, "medium": 0, "low": 0}}
    
    confs = []
    high = medium = low = 0
    for c in orch.contradictions:
        if c.severity == "high": high += 1
        elif c.severity == "medium": medium += 1
        else: low += 1
            
        confs.append({
            "entity": c.entity,
            "attribute": c.attribute,
            "severity": c.severity,
            "difference_pct": getattr(c, "difference_pct", None),
            "source_a_name": c.source_a_name,
            "source_a_value": c.source_a_value,
            "source_b_name": c.source_b_name,
            "source_b_value": c.source_b_value,
        })
        
    return {
        "contradictions": confs,
        "summary": {"total": len(confs), "high": high, "medium": medium, "low": low}
    }

@app.post("/api/reconcile")
def reconcile_contradictions():
    orch = get_orch()
    try:
        results = orch.reconcile_contradictions()
        state["reconciliation_results"] = results
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proactive_insights")
def get_proactive_insights():
    orch = get_orch()
    try:
        insights = orch.get_proactive_insights()
        state["proactive_insights"] = insights
        
        # Breakdown anomalies for charting
        anomaly_breakdown = {}
        if orch.validator and hasattr(orch.validator, "anomalies") and orch.validator.anomalies:
            for a in orch.validator.anomalies:
                anomaly_breakdown[a.anomaly_type] = anomaly_breakdown.get(a.anomaly_type, 0) + 1
                
        return {
            "insights": insights,
            "anomaly_breakdown": anomaly_breakdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge_graph")
def get_knowledge_graph():
    orch = get_orch()
    kg = orch.knowledge_graph
    try:
        stats = kg.get_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lineage")
def get_lineage():
    orch = get_orch()
    ld = orch.lineage_tracker.to_dict() if hasattr(orch, "lineage_tracker") and orch.lineage_tracker else {}
    
    sources = []
    if hasattr(orch, "federation") and orch.federation and orch.federation.sources:
        for src in orch.federation.sources.values():
            sources.append({
                "name": src.source_name,
                "type": src.source_type.upper(),
                "rows": src.row_count,
                "credibility": src.credibility_score,
                "ingested": src.ingested_at[:19] if src.ingested_at else None
            })
            
    return {"lineage": ld, "sources": sources}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
