import duckdb
from typing import Dict, Any, List, Set, Optional
from backend.db import get_connection

def trace_path_to_bedrock(conn: duckdb.DuckDBPyConnection, seed_doi: str, max_depth: int = 10) -> Dict[str, Any]:
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    visited: Set[str] = set()

    queue = [(seed_doi, 0)]

    while queue:
        curr_doi, depth = queue.pop(0)
        if curr_doi in visited or depth > max_depth:
            continue
        visited.add(curr_doi)

        paper_row = conn.execute("""
            SELECT id, doi, title, publication_year, authors, status, raw_ci, smoothed_ci, constraint_density
            FROM papers WHERE id = ? OR doi = ?
        """, (curr_doi, curr_doi)).fetchone()

        if not paper_row:
            continue

        p_id, p_doi, p_title, p_year, p_authors, p_status, r_ci, s_ci, c_den = paper_row
        nodes[p_id] = {
            "id": p_id,
            "doi": p_doi,
            "title": p_title,
            "publication_year": p_year,
            "authors": p_authors,
            "status": p_status,
            "raw_ci": r_ci,
            "smoothed_ci": s_ci,
            "constraint_density": c_den
        }

        cit_rows = conn.execute("""
            SELECT source_id, target_id, polarity, parameter_domain_valid, parameter_domain_failed, confidence
            FROM citations
            WHERE source_id = ? AND polarity IN ('SUPPORTING', 'DOMAIN_CONSTRAINED')
        """, (p_id,)).fetchall()

        for s_id, t_id, pol, p_val, p_fail, conf in cit_rows:
            edges.append({
                "source": s_id,
                "target": t_id,
                "polarity": pol,
                "parameter_domain_valid": p_val,
                "parameter_domain_failed": p_fail,
                "confidence": conf
            })
            if t_id not in visited:
                queue.append((t_id, depth + 1))

    return {
        "seed_doi": seed_doi,
        "nodes": list(nodes.values()),
        "edges": edges
    }

def identify_pruned_hypotheses(conn: duckdb.DuckDBPyConnection, topic_keyword: Optional[str] = None) -> List[Dict[str, Any]]:
    query = """
        SELECT id, doi, title, publication_year, authors, status, raw_ci, smoothed_ci
        FROM papers
        WHERE status = 'FALSIFIED_DEAD_END'
    """
    params = []
    if topic_keyword:
        query += " AND (LOWER(title) LIKE ? OR LOWER(id) LIKE ?)"
        kw = f"%{topic_keyword.lower()}%"
        params.extend([kw, kw])

    dead_end_nodes = conn.execute(query, params).fetchall()

    results = []
    for p_id, p_doi, p_title, p_year, p_authors, p_status, r_ci, s_ci in dead_end_nodes:
        term_rows = conn.execute("""
            SELECT c.source_id, p.title, p.publication_year, p.authors, ctx.snippet
            FROM citations c
            JOIN papers p ON c.source_id = p.id
            LEFT JOIN contexts ctx ON c.source_id = ctx.source_id AND c.target_id = ctx.target_id
            WHERE c.target_id = ? AND c.polarity = 'CONTESTING'
        """, (p_id,)).fetchall()

        terminating_studies = []
        for s_id, s_title, s_year, s_authors, snippet in term_rows:
            terminating_studies.append({
                "source_id": s_id,
                "title": s_title,
                "publication_year": s_year,
                "authors": s_authors,
                "snippet": snippet
            })

        results.append({
            "root_claim_node": {
                "id": p_id,
                "doi": p_doi,
                "title": p_title,
                "publication_year": p_year,
                "authors": p_authors,
                "status": p_status,
                "raw_ci": r_ci,
                "smoothed_ci": s_ci
            },
            "terminating_studies_count": len(terminating_studies),
            "terminating_studies": terminating_studies
        })

    return results
