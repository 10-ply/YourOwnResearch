import duckdb
import os
import json
from typing import Dict, Any, List, Optional

DB_FILE = os.environ.get("EPISTEME_DB_FILE", ":memory:")

def get_connection(db_file: str = DB_FILE):
    conn = duckdb.connect(db_file)
    init_db(conn)
    return conn

def init_db(conn: duckdb.DuckDBPyConnection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id VARCHAR PRIMARY KEY,
            doi VARCHAR,
            title VARCHAR,
            publication_year INTEGER,
            inverted_abstract TEXT,
            openalex_id VARCHAR,
            authors VARCHAR,
            status VARCHAR DEFAULT 'UNREVIEWED',
            raw_ci DOUBLE DEFAULT 0.0,
            smoothed_ci DOUBLE DEFAULT 0.0,
            c_supporting INTEGER DEFAULT 0,
            c_contrasting INTEGER DEFAULT 0,
            c_constrained INTEGER DEFAULT 0,
            c_neutral INTEGER DEFAULT 0,
            constraint_density DOUBLE DEFAULT 0.0
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS citations (
            source_id VARCHAR,
            target_id VARCHAR,
            polarity VARCHAR, -- SUPPORTING, CONTESTING, DOMAIN_CONSTRAINED, NEUTRAL
            parameter_domain_valid VARCHAR,
            parameter_domain_failed VARCHAR,
            confidence DOUBLE DEFAULT 1.0,
            PRIMARY KEY (source_id, target_id)
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS contexts (
            id VARCHAR PRIMARY KEY,
            source_id VARCHAR,
            target_id VARCHAR,
            snippet TEXT
        );
    """)

def save_paper(conn: duckdb.DuckDBPyConnection, paper: Dict[str, Any]):
    conn.execute("""
        INSERT INTO papers (id, doi, title, publication_year, inverted_abstract, openalex_id, authors, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (id) DO UPDATE SET
            doi = EXCLUDED.doi,
            title = EXCLUDED.title,
            publication_year = EXCLUDED.publication_year,
            inverted_abstract = EXCLUDED.inverted_abstract,
            openalex_id = EXCLUDED.openalex_id,
            authors = EXCLUDED.authors;
    """, (
        paper["id"],
        paper.get("doi", ""),
        paper.get("title", ""),
        paper.get("publication_year", 0),
        json.dumps(paper.get("inverted_abstract", {})),
        paper.get("openalex_id", paper["id"]),
        json.dumps(paper.get("authors", [])),
        paper.get("status", "UNREVIEWED")
    ))

def save_citation(conn: duckdb.DuckDBPyConnection, source_id: str, target_id: str, polarity: str,
                  param_valid: Optional[str] = None, param_failed: Optional[str] = None, confidence: float = 1.0):
    conn.execute("""
        INSERT INTO citations (source_id, target_id, polarity, parameter_domain_valid, parameter_domain_failed, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (source_id, target_id) DO UPDATE SET
            polarity = EXCLUDED.polarity,
            parameter_domain_valid = EXCLUDED.parameter_domain_valid,
            parameter_domain_failed = EXCLUDED.parameter_domain_failed,
            confidence = EXCLUDED.confidence;
    """, (source_id, target_id, polarity, param_valid, param_failed, confidence))

def save_context(conn: duckdb.DuckDBPyConnection, ctx_id: str, source_id: str, target_id: str, snippet: str):
    conn.execute("""
        INSERT INTO contexts (id, source_id, target_id, snippet)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (id) DO UPDATE SET snippet = EXCLUDED.snippet;
    """, (ctx_id, source_id, target_id, snippet))
