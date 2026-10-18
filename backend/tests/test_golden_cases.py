import pytest
import duckdb
from backend.db import get_connection
from backend.ingestion.seed_data import seed_golden_dataset
from backend.graph.metrics import update_all_node_metrics, compute_raw_contestation_index, compute_bayes_smoothed_ci
from backend.graph.traversal import trace_path_to_bedrock, identify_pruned_hypotheses
from backend.nlp.classifier import classifier_engine

@pytest.fixture
def test_db():
    conn = duckdb.connect(":memory:")
    from backend.db import init_db
    init_db(conn)
    seed_golden_dataset(conn)
    update_all_node_metrics(conn)
    return conn

def test_golden_case_1_cold_fusion_falsified_dead_end(test_db):
    """
    Test Case 1: Cold Fusion (Fleischmann & Pons 1989)
    - Seed: 10.1016/0022-0728(89)80006-3
    - Incoming citations: 10 contesting replication studies
    - Bayesian Contestation Index: ~0.60 (>= 0.45)
    - Expected Node Status: FALSIFIED_DEAD_END
    """
    fp_doi = "10.1016/0022-0728(89)80006-3"
    row = test_db.execute("""
        SELECT status, smoothed_ci, c_contrasting, c_supporting
        FROM papers WHERE id = ?
    """, (fp_doi,)).fetchone()

    assert row is not None
    status, smoothed_ci, c_con, c_sup = row

    assert c_con >= 10
    assert smoothed_ci >= 0.45
    assert status == "FALSIFIED_DEAD_END"

    # Verify graveyard / pruned hypothesis traversal returns this dead end
    graveyard = identify_pruned_hypotheses(test_db)
    assert len(graveyard) >= 1
    root_ids = [item["root_claim_node"]["id"] for item in graveyard]
    assert fp_doi in root_ids

def test_golden_case_2_domain_constraint_newton_gr(test_db):
    """
    Test Case 2: Domain Constraint (Newtonian Gravity -> General Relativity)
    - Seed: Newton's Law of Universal Gravitation (10.1098/rstl.1687.0001)
    - System detects high DOMAIN_CONSTRAINT density when linked to GR & orbital mechanics
    - Expected Node Status: DOMAIN_CONSTRAINED
    """
    newton_doi = "10.1098/rstl.1687.0001"
    row = test_db.execute("""
        SELECT status, constraint_density, c_constrained
        FROM papers WHERE id = ?
    """, (newton_doi,)).fetchone()

    assert row is not None
    status, constraint_density, c_dom = row

    assert c_dom >= 3
    assert constraint_density >= 0.20
    assert status == "DOMAIN_CONSTRAINED"

def test_golden_case_3_foundational_null_result_michelson_morley(test_db):
    """
    Test Case 3: Foundational Null Result (Michelson-Morley 1887)
    - Seed: Michelson & Morley 1887 (10.2475/ajs.s3-34.203.333)
    - System does not mark this paper as a dead end; recognizes it as bedrock for Special Relativity (Einstein 1905)
    - Path to Bedrock from Einstein 1905 reaches Michelson-Morley
    """
    mm_doi = "10.2475/ajs.s3-34.203.333"
    sr_doi = "10.1002/andp.19053221004"

    mm_row = test_db.execute("""
        SELECT status, smoothed_ci
        FROM papers WHERE id = ?
    """, (mm_doi,)).fetchone()

    assert mm_row is not None
    status, smoothed_ci = mm_row

    assert status != "FALSIFIED_DEAD_END"

    # Trace path to bedrock from Special Relativity
    bedrock_trace = trace_path_to_bedrock(test_db, sr_doi)
    node_ids = [n["id"] for n in bedrock_trace["nodes"]]
    assert sr_doi in node_ids
    assert mm_doi in node_ids

def test_system_1_nlp_classifier():
    """
    Tests System 1 choice primitive on citation context snippets
    """
    refutation_snippet = "We performed careful measurements and failed to replicate the claimed excess heat, contradicting earlier results."
    res = classifier_engine.classify_citation_context(refutation_snippet)
    assert res["polarity"] == "CONTESTING"
    assert res["confidence"] > 0.5

    constraint_snippet = "Newtonian mechanics is a valid approximation under weak gravitational field limits, but breaks down near relativistic velocities."
    res2 = classifier_engine.classify_citation_context(constraint_snippet)
    assert res2["polarity"] == "DOMAIN_CONSTRAINED"
