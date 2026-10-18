import requests
import duckdb
from typing import Dict, Any, List, Optional
from backend.db import get_connection, save_paper, save_citation, save_context

OPENALEX_API_BASE = "https://api.openalex.org/works"

class OpenAlexClient:
    def __init__(self, conn: Optional[duckdb.DuckDBPyConnection] = None, email: Optional[str] = "epistemegraph@example.org"):
        self.conn = conn or get_connection()
        self.headers = {"User-Agent": f"EpistemeGraph/1.0 (mailto:{email})"}

    def fetch_work_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        clean_doi = doi.replace("https://doi.org/", "").strip()
        url = f"{OPENALEX_API_BASE}/https://doi.org/{clean_doi}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                paper = self._normalize_work(data)
                save_paper(self.conn, paper)
                return paper
        except Exception as e:
            print(f"Error fetching OpenAlex work for DOI {doi}: {e}")
        return None

    def fetch_ancestry(self, doi: str, depth: int = 2) -> List[Dict[str, Any]]:
        visited = set()
        to_visit = [(doi, 0)]
        results = []

        while to_visit:
            curr_doi, curr_depth = to_visit.pop(0)
            if curr_doi in visited or curr_depth > depth:
                continue
            visited.add(curr_doi)

            work = self.fetch_work_by_doi(curr_doi)
            if not work:
                continue
            results.append(work)

            if curr_depth < depth and "referenced_works" in work:
                for ref in work.get("referenced_works", []):
                    ref_doi = ref if ref.startswith("10.") or ref.startswith("https://") else None
                    if ref_doi:
                        to_visit.append((ref_doi, curr_depth + 1))

        return results

    def fetch_descendants(self, doi: str, depth: int = 2) -> List[Dict[str, Any]]:
        clean_doi = doi.replace("https://doi.org/", "").strip()
        url = f"{OPENALEX_API_BASE}?filter=cites:https://doi.org/{clean_doi}&per_page=50"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                normalized = []
                for item in results:
                    paper = self._normalize_work(item)
                    save_paper(self.conn, paper)
                    save_citation(self.conn, paper["id"], doi, "NEUTRAL")
                    normalized.append(paper)
                return normalized
        except Exception as e:
            print(f"Error fetching descendants for DOI {doi}: {e}")
        return []

    def _normalize_work(self, data: Dict[str, Any]) -> Dict[str, Any]:
        doi = data.get("doi") or ""
        doi = doi.replace("https://doi.org/", "")
        openalex_id = data.get("id", "")
        title = data.get("title") or "Untitled Work"
        pub_year = data.get("publication_year") or 0
        inv_abstract = data.get("abstract_inverted_index") or {}

        authors = []
        for ship in data.get("authorships", []):
            author_name = ship.get("author", {}).get("display_name")
            if author_name:
                authors.append(author_name)

        referenced_works = data.get("referenced_works", [])

        return {
            "id": doi if doi else openalex_id,
            "doi": doi,
            "title": title,
            "publication_year": pub_year,
            "inverted_abstract": inv_abstract,
            "openalex_id": openalex_id,
            "authors": authors,
            "referenced_works": referenced_works
        }
