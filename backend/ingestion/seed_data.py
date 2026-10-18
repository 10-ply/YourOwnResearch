import duckdb
from backend.db import get_connection, save_paper, save_citation, save_context

def seed_golden_dataset(conn: duckdb.DuckDBPyConnection):
    """
    Seeds the DuckDB instance with deterministic data for the three golden historical test cases:
    1. Cold Fusion (Fleischmann & Pons 1989) -> Refutations / FALSIFIED_DEAD_END
    2. Newtonian Gravity -> General Relativity (Einstein 1915) -> DOMAIN_CONSTRAINED
    3. Michelson-Morley 1887 Null Result -> Bedrock anchor for Special Relativity (Einstein 1905)
    """

    # --- Test Case 1: Cold Fusion (Fleischmann & Pons 1989) ---
    fp_paper = {
        "id": "10.1016/0022-0728(89)80006-3",
        "doi": "10.1016/0022-0728(89)80006-3",
        "title": "Electrochemically induced nuclear fusion of deuterium",
        "publication_year": 1989,
        "inverted_abstract": {"Electrochemically": [0], "induced": [1], "nuclear": [2], "fusion": [3]},
        "openalex_id": "W2087534212",
        "authors": ["Martin Fleischmann", "Stanley Pons"],
        "status": "UNREVIEWED"
    }
    save_paper(conn, fp_paper)

    # 10 negative replication / refutation papers targeting Fleischmann & Pons
    refutation_papers = [
        ("10.1038/340525a0", "Search for neutrons from cold nuclear fusion", 1989, "Gai et al.", "CONTESTING",
         "We performed careful neutron monitoring and found no evidence of cold fusion beyond background radiation."),
        ("10.1016/0375-9601(89)90123-X", "Limits on neutron emission in cold fusion experiments", 1989, "Koonin et al.", "CONTESTING",
         "Theoretical calculations and experimental upper bounds rule out nuclear fusion at the claimed rates."),
        ("10.1103/PhysRevLett.63.1926", "Upper limits on neutron and gamma-ray emission in cold fusion", 1989, "Lewis et al. (Caltech)", "CONTESTING",
         "Caltech experiments failed to replicate excess heat or nuclear products, contradicting Fleischmann and Pons."),
        ("10.1038/341711a0", "A search for excess heat and d-d fusion products", 1989, "Gai et al. (Yale)", "CONTESTING",
         "Independent replication showed zero anomalous heat generation."),
        ("10.1016/0022-0728(89)85001-2", "Failure to observe cold fusion in palladium electrodes", 1989, "MIT Plasma Fusion Center", "CONTESTING",
         "Comprehensive testing at MIT confirms absence of fusion neutrons or tritium."),
        ("10.1016/0375-9601(90)90234-Y", "Negative result in cold fusion search", 1990, "Harwell Laboratory", "CONTESTING",
         "Harwell multi-detector setup observed no fusion signatures over 6 months."),
        ("10.1103/PhysRevC.41.2001", "Calorimetric and nuclear measurements of cold fusion", 1990, "Redey et al.", "CONTESTING",
         "Calorimetric artifacts account for apparent excess power in earlier reports."),
        ("10.1016/0306-4522(90)90112-A", "Assessment of claims of cold fusion", 1990, "DOE Advisory Board", "CONTESTING",
         "The US Department of Energy panel concluded empirical claims of nuclear origin are unconvincing."),
        ("10.1038/344111a0", "Nuclear products search in electrochemical cells", 1990, "Barwick et al.", "CONTESTING",
         "No charged particles detected; earlier counts attributed to instrument noise."),
        ("10.1016/0022-0728(91)85012-C", "Re-examination of palladium deuteride thermodynamics", 1991, "Hansen et al.", "CONTESTING",
         "Thermodynamic calculations contradict the energy density claims of cold fusion.")
    ]

    for p_doi, p_title, p_year, p_author, pol, snippet in refutation_papers:
        save_paper(conn, {
            "id": p_doi, "doi": p_doi, "title": p_title, "publication_year": p_year,
            "inverted_abstract": {}, "openalex_id": p_doi, "authors": [p_author]
        })
        save_citation(conn, source_id=p_doi, target_id=fp_paper["id"], polarity=pol)
        save_context(conn, ctx_id=f"ctx-{p_doi}", source_id=p_doi, target_id=fp_paper["id"], snippet=snippet)

    # --- Test Case 2: Newtonian Gravity -> General Relativity ---
    newton_paper = {
        "id": "10.1098/rstl.1687.0001",
        "doi": "10.1098/rstl.1687.0001",
        "title": "Philosophiae Naturalis Principia Mathematica (Law of Universal Gravitation)",
        "publication_year": 1687,
        "inverted_abstract": {"Law": [0], "of": [1], "Gravitation": [2]},
        "openalex_id": "W16870001",
        "authors": ["Isaac Newton"],
        "status": "UNREVIEWED"
    }
    save_paper(conn, newton_paper)

    einstein_gr = {
        "id": "10.1002/andp.19163540702",
        "doi": "10.1002/andp.19163540702",
        "title": "Die Grundlage der allgemeinen Relativitatstheorie (General Relativity)",
        "publication_year": 1916,
        "inverted_abstract": {"General": [0], "Relativity": [1]},
        "openalex_id": "W19160001",
        "authors": ["Albert Einstein"],
        "status": "UNREVIEWED"
    }
    save_paper(conn, einstein_gr)

    # Citation from GR to Newton establishing DOMAIN_CONSTRAINED relationship
    save_citation(conn, source_id=einstein_gr["id"], target_id=newton_paper["id"],
                  polarity="DOMAIN_CONSTRAINED",
                  param_valid="low_velocity, weak_gravitational_field",
                  param_failed="relativistic_velocity, strong_gravitational_field, Mercury_perihelion")
    save_context(conn, ctx_id="ctx-gr-newton", source_id=einstein_gr["id"], target_id=newton_paper["id"],
                 snippet="Newtonian gravity is a valid limiting approximation under weak gravitational fields (v << c), but fails to account for Mercury's perihelion precession and strong-field curvature.")

    # Additional orbital mechanics citations with DOMAIN_CONSTRAINED polarity
    constrained_citations = [
        ("10.1038/orbital.1920.01", "Mercury's Perihelion and Relativistic Corrections", 1920, "Eddington et al.",
         "DOMAIN_CONSTRAINED", "Newtonian dynamics fails at Mercury's perihelion precession rate of 43 arcseconds per century, resolved by GR."),
        ("10.1103/PhysRevD.1.234", "Post-Newtonian Gravitational Approximations", 1970, "Will et al.",
         "DOMAIN_CONSTRAINED", "Parameterized post-Newtonian formalism delineates the exact weak-field boundary where Newton's laws hold."),
        ("10.1038/nature01234", "Binary Pulsar Tests of Gravitational Theories", 1982, "Taylor & Hulse",
         "DOMAIN_CONSTRAINED", "Strong field orbital decay in PSR B1913+16 departs from Newtonian mechanics and matches GR precisely.")
    ]
    for p_doi, p_title, p_year, p_author, pol, snippet in constrained_citations:
        save_paper(conn, {"id": p_doi, "doi": p_doi, "title": p_title, "publication_year": p_year, "inverted_abstract": {}, "openalex_id": p_doi, "authors": [p_author]})
        save_citation(conn, source_id=p_doi, target_id=newton_paper["id"], polarity=pol,
                      param_valid="v << c", param_failed="v ~ c")
        save_context(conn, ctx_id=f"ctx-{p_doi}", source_id=p_doi, target_id=newton_paper["id"], snippet=snippet)

    # Supporting classical citations for Newton
    for i in range(7):
        sup_doi = f"10.1098/classical.170{i}"
        save_paper(conn, {"id": sup_doi, "doi": sup_doi, "title": f"Classical Celestial Mechanics Validation {i}", "publication_year": 1720 + i, "inverted_abstract": {}, "openalex_id": sup_doi, "authors": ["Halley et al."]})
        save_citation(conn, source_id=sup_doi, target_id=newton_paper["id"], polarity="SUPPORTING")

    # --- Test Case 3: Michelson-Morley 1887 Foundational Null Result ---
    mm_1887 = {
        "id": "10.2475/ajs.s3-34.203.333",
        "doi": "10.2475/ajs.s3-34.203.333",
        "title": "On the Relative Motion of the Earth and the Luminiferous Ether",
        "publication_year": 1887,
        "inverted_abstract": {"Luminiferous": [0], "Ether": [1], "Relative": [2], "Motion": [3]},
        "openalex_id": "W18870001",
        "authors": ["Albert A. Michelson", "Edward W. Morley"],
        "status": "UNREVIEWED"
    }
    save_paper(conn, mm_1887)

    # Mechanical Aether Hypothesis paper (terminated by Michelson-Morley)
    aether_paper = {
        "id": "10.1098/aether.1864.0001",
        "doi": "10.1098/aether.1864.0001",
        "title": "A Dynamical Theory of the Luminiferous Ether medium",
        "publication_year": 1864,
        "inverted_abstract": {"Ether": [0], "Medium": [1]},
        "openalex_id": "W18640001",
        "authors": ["Luminiferous Theorists"],
        "status": "UNREVIEWED"
    }
    save_paper(conn, aether_paper)

    # Michelson-Morley refutes mechanical aether hypothesis
    save_citation(conn, source_id=mm_1887["id"], target_id=aether_paper["id"], polarity="CONTESTING")
    save_context(conn, ctx_id="ctx-mm-aether", source_id=mm_1887["id"], target_id=aether_paper["id"],
                 snippet="The results of the interferometry experiments show no detectable relative motion between the Earth and the luminiferous ether, refuting static mechanical aether models.")

    # Einstein 1905 Special Relativity cites Michelson-Morley as empirical foundation
    sr_1905 = {
        "id": "10.1002/andp.19053221004",
        "doi": "10.1002/andp.19053221004",
        "title": "Zur Elektrodynamik bewegter Korper (On the Electrodynamics of Moving Bodies / Special Relativity)",
        "publication_year": 1905,
        "inverted_abstract": {"Special": [0], "Relativity": [1]},
        "openalex_id": "W19050001",
        "authors": ["Albert Einstein"],
        "status": "UNREVIEWED"
    }
    save_paper(conn, sr_1905)
    save_citation(conn, source_id=sr_1905["id"], target_id=mm_1887["id"], polarity="SUPPORTING")
    save_context(conn, ctx_id="ctx-sr-mm", source_id=sr_1905["id"], target_id=mm_1887["id"],
                 snippet="Unsuccessful attempts to discover any motion of the earth relatively to the 'light medium' suggest that the phenomena of electrodynamics as well as of mechanics possess no properties corresponding to the idea of absolute rest.")

    # Additional supporting citations for Special Relativity -> Michelson Morley
    for i in range(5):
        sup_doi = f"10.1103/relativity.191{i}"
        save_paper(conn, {"id": sup_doi, "doi": sup_doi, "title": f"Experimental Verification of Constant Speed of Light {i}", "publication_year": 1910 + i, "inverted_abstract": {}, "openalex_id": sup_doi, "authors": ["Lorentz et al."]})
        save_citation(conn, source_id=sup_doi, target_id=mm_1887["id"], polarity="SUPPORTING")

    conn.commit()
