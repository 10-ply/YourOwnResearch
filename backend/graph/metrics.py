import duckdb
from typing import Dict, Any, Tuple
from backend.db import get_connection

def compute_raw_contestation_index(c_contrasting: int, c_supporting: int) -> float:
    total = c_contrasting + c_supporting
    if total == 0:
        return 0.0
    return float(c_contrasting) / float(total)

def compute_bayes_smoothed_ci(c_contrasting: int, c_supporting: int,
                              alpha: float = 2.0, beta: float = 8.0) -> float:
    return float(c_contrasting + alpha) / float(c_contrasting + c_supporting + alpha + beta)

def compute_constraint_density(c_constrained: int, total_active_edges: int) -> float:
    if total_active_edges == 0:
        return 0.0
    return float(c_constrained) / float(total_active_edges)

def classify_node_status(c_contrasting: int, c_supporting: int, c_constrained: int,
                         total_active_edges: int, alpha: float = 2.0, beta: float = 8.0) -> Tuple[str, float, float, float]:
    total_eval = c_contrasting + c_supporting
    raw_ci = compute_raw_contestation_index(c_contrasting, c_supporting)
    smoothed_ci = compute_bayes_smoothed_ci(c_contrasting, c_supporting, alpha, beta)
    constraint_density = compute_constraint_density(c_constrained, total_active_edges)

    status = "UNREVIEWED"

    if constraint_density >= 0.20 and total_active_edges >= 3:
        status = "DOMAIN_CONSTRAINED"
    elif smoothed_ci >= 0.45 and total_eval >= 5:
        status = "FALSIFIED_DEAD_END"
    elif smoothed_ci <= 0.15 and total_eval >= 10:
        status = "VALIDATED_CORE"
    elif 0.15 < smoothed_ci < 0.45 and total_eval >= 3:
        status = "CONTESTED_FRONTIER"
    else:
        status = "UNREVIEWED"

    return status, raw_ci, smoothed_ci, constraint_density

def update_all_node_metrics(conn: duckdb.DuckDBPyConnection, alpha: float = 2.0, beta: float = 8.0):
    rows = conn.execute("""
        SELECT
            target_id,
            SUM(CASE WHEN polarity = 'SUPPORTING' THEN 1 ELSE 0 END) as c_sup,
            SUM(CASE WHEN polarity = 'CONTESTING' THEN 1 ELSE 0 END) as c_con,
            SUM(CASE WHEN polarity = 'DOMAIN_CONSTRAINED' THEN 1 ELSE 0 END) as c_dom,
            SUM(CASE WHEN polarity = 'NEUTRAL' THEN 1 ELSE 0 END) as c_neu,
            COUNT(*) as total_edges
        FROM citations
        GROUP BY target_id
    """).fetchall()

    for target_id, c_sup, c_con, c_dom, c_neu, total_edges in rows:
        active_edges = c_sup + c_con + c_dom
        status, raw_ci, smoothed_ci, density = classify_node_status(
            c_con, c_sup, c_dom, active_edges, alpha, beta
        )

        conn.execute("""
            UPDATE papers SET
                c_supporting = ?,
                c_contrasting = ?,
                c_constrained = ?,
                c_neutral = ?,
                raw_ci = ?,
                smoothed_ci = ?,
                constraint_density = ?,
                status = ?
            WHERE id = ?;
        """, (c_sup, c_con, c_dom, c_neu, raw_ci, smoothed_ci, density, status, target_id))

    conn.commit()
