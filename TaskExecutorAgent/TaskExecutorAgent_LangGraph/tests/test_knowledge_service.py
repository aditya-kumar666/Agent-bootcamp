from pathlib import Path

import pytest

pytest.importorskip("chromadb")

from services.knowledge_service import KnowledgeService


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "knowledge_base"


def test_ingests_rules_and_retrieves_exact_rule(tmp_path):
    service = KnowledgeService(tmp_path / "chroma")

    indexed = service.ingest_file(CORPUS / "security_owasp" / "owasp_top_10.md")

    assert indexed == 4
    result = service.get_by_rule_id("SEC-INJ-01")
    assert len(result) == 1
    assert result[0]["metadata"]["domain"] == "security_owasp"
    assert "parameterized queries" in result[0]["text"]


def test_search_supports_domain_filter(tmp_path):
    service = KnowledgeService(tmp_path / "chroma")
    service.ingest_directory(CORPUS)

    results = service.search("which HTTP status means not found", domain="api_standards")

    assert results
    assert all(item["metadata"]["domain"] == "api_standards" for item in results)
    assert any(item["metadata"]["rule_id"] == "API-HTTP-01" for item in results)