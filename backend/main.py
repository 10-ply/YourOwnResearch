from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.db import get_connection
from backend.ingestion.seed_data import seed_golden_dataset
from backend.graph.metrics import update_all_node_metrics
from backend.graph.traversal import trace_path_to_bedrock, identify_pruned_hypotheses
from backend.nlp.classifier import classifier_engine

app = FastAPI(
    title="EpistemeGraph API",
    description="Automated Scientific Cladistics & Refutation Mapping Engine API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conn = get_connection()
seed_golden_dataset(conn)
update_all_node_metrics(conn)

class ClaimEvaluationRequest(BaseModel):
    hypothesis: str

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>EpistemeGraph Dashboard</title>
        <style>
            body { font-family: system-ui, sans-serif; background: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
            header { display: flex; justify-content: space-between; border-bottom: 1px solid #1e293b; padding-bottom: 12px; }
            .card { background: #1e293b; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
            .tag { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
            .VALIDATED_CORE { background: #065f46; color: #34d399; }
            .FALSIFIED_DEAD_END { background: #991b1b; color: #fca5a5; }
            .DOMAIN_CONSTRAINED { background: #5b21b6; color: #c084fc; }
            .CONTESTED_FRONTIER { background: #9a3412; color: #fcd34d; }
        </style>
    </head>
    <body>
        <header>
            <div>
                <h1 style="margin:0; color:#38bdf8;">EpistemeGraph</h1>
                <p style="margin:4px 0 0 0; color:#94a3b8;">Automated Scientific Cladistics & Refutation Mapping Engine</p>
            </div>
            <div>
                <span class="tag VALIDATED_CORE">VALIDATED_CORE</span>
                <span class="tag CONTESTED_FRONTIER">CONTESTED_FRONTIER</span>
                <span class="tag FALSIFIED_DEAD_END">FALSIFIED_DEAD_END</span>
                <span class="tag DOMAIN_CONSTRAINED">DOMAIN_CONSTRAINED</span>
            </div>
        </header>
        <main style="margin-top:20px;">
            <h2>Scientific Knowledge Graph Cladogram</h2>
            <div id="nodes-container">
                <div class="card">
                    <span class="tag FALSIFIED_DEAD_END">FALSIFIED_DEAD_END</span>
                    <h3>Electrochemically induced nuclear fusion of deuterium (Fleischmann & Pons 1989)</h3>
                    <p>Bayesian Contestation Index: 0.600 | Terminating Studies: 10</p>
                </div>
                <div class="card">
                    <span class="tag DOMAIN_CONSTRAINED">DOMAIN_CONSTRAINED</span>
                    <h3>Philosophiae Naturalis Principia Mathematica (Law of Universal Gravitation)</h3>
                    <p>Constraint Density: 36.4% | Valid in weak fields (v &lt;&lt; c)</p>
                </div>
                <div class="card">
                    <span class="tag VALIDATED_CORE">VALIDATED_CORE</span>
                    <h3>On the Relative Motion of the Earth and the Luminiferous Ether (Michelson-Morley 1887)</h3>
                    <p>Foundational Null Result | Anchor for Special Relativity (Einstein 1905)</p>
                </div>
            </div>
        </main>
    </body>
    </html>
    """

@app.get("/api/health")
def health_check():
    return {"status": "ok", "engine": "EpistemeGraph System 1 Core"}

@app.get("/api/tree/trace")
def trace_bedrock(doi: str = Query(..., description="DOI of paper to trace back to bedrock")):
    res = trace_path_to_bedrock(conn, doi)
    if not res["nodes"]:
        raise HTTPException(status_code=404, detail=f"Paper with DOI '{doi}' not found in graph.")
    return res

@app.get("/api/tree/graveyard")
def get_graveyard(topic: Optional[str] = Query(None, description="Optional topic search keyword")):
    return identify_pruned_hypotheses(conn, topic)

@app.get("/api/graph/full")
def get_full_graph():
    update_all_node_metrics(conn)
    papers = conn.execute("""
        SELECT id, doi, title, publication_year, authors, status, raw_ci, smoothed_ci, constraint_density
        FROM papers
    """).fetchall()

    nodes = []
    for p_id, p_doi, p_title, p_year, p_authors, p_status, r_ci, s_ci, c_den in papers:
        nodes.append({
            "id": p_id,
            "doi": p_doi,
            "title": p_title,
            "publication_year": p_year,
            "authors": p_authors,
            "status": p_status,
            "raw_ci": r_ci,
            "smoothed_ci": s_ci,
            "constraint_density": c_den
        })

    citations = conn.execute("""
        SELECT c.source_id, c.target_id, c.polarity, c.parameter_domain_valid, c.parameter_domain_failed, c.confidence, ctx.snippet
        FROM citations c
        LEFT JOIN contexts ctx ON c.source_id = ctx.source_id AND c.target_id = ctx.target_id
    """).fetchall()

    edges = []
    for s_id, t_id, pol, p_val, p_fail, conf, snippet in citations:
        edges.append({
            "source": s_id,
            "target": t_id,
            "polarity": pol,
            "parameter_domain_valid": p_val,
            "parameter_domain_failed": p_fail,
            "confidence": conf,
            "snippet": snippet
        })

    return {"nodes": nodes, "edges": edges}

@app.post("/api/claim/evaluate")
def evaluate_claim(req: ClaimEvaluationRequest):
    hypothesis = req.hypothesis
    sys1_res = classifier_engine.classify_citation_context(hypothesis)

    matching_papers = conn.execute("""
        SELECT id, title, status, smoothed_ci, raw_ci, c_supporting, c_contrasting
        FROM papers
        ORDER BY (c_supporting + c_contrasting) DESC
        LIMIT 5
    """).fetchall()

    nearest_nodes = []
    for p_id, p_title, p_status, p_sci, p_rci, c_sup, c_con in matching_papers:
        nearest_nodes.append({
            "id": p_id,
            "title": p_title,
            "status": p_status,
            "smoothed_ci": p_sci,
            "c_supporting": c_sup,
            "c_contrasting": c_con
        })

    return {
        "hypothesis": hypothesis,
        "system1_analysis": sys1_res,
        "nearest_graph_nodes": nearest_nodes,
        "overall_evidential_verdict": "CONTESTED" if sys1_res["polarity"] == "CONTESTING" else "SUPPORTED_OR_INCONCLUSIVE"
    }
