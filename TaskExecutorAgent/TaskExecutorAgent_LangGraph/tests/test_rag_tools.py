from plugins.rag_tools import RagToolsPlugin


class FakeCollection:
    def get(self, *, where, include):
        assert where == {"domain": "api_standards"}
        return {
            "documents": ["Status code guidance"],
            "metadatas": [{"rule_id": "API-HTTP-01", "title": "Status codes", "domain": "api_standards", "severity": "high"}],
        }


class FakeService:
    collection = FakeCollection()

    def search(self, query, domain=None, top_k=3):
        assert query == "SQL injection"
        assert domain == "security_owasp"
        assert top_k == 2
        return [{
            "text": "Use parameterized queries.",
            "metadata": {"rule_id": "SEC-INJ-01", "title": "Prevent injection", "domain": domain, "severity": "critical"},
            "distance": 0.12,
        }]

    def get_by_rule_id(self, rule_id):
        if rule_id == "SEC-INJ-01":
            return [{
                "text": "Use parameterized queries.",
                "metadata": {"rule_id": rule_id, "title": "Prevent injection", "domain": "security_owasp", "severity": "critical"},
            }]
        return []


def test_search_tool_formats_cited_markdown():
    result = RagToolsPlugin(FakeService()).search_standards("SQL injection", "security_owasp", 2)

    assert "[SEC-INJ-01]" in result
    assert "distance: `0.1200`" in result
    assert "parameterized queries" in result


def test_domain_and_exact_rule_tools():
    tools = RagToolsPlugin(FakeService())

    assert "API-HTTP-01" in tools.get_guidelines_by_domain("api_standards")
    assert "SEC-INJ-01" in tools.get_rule("SEC-INJ-01")
    assert "No guideline found" in tools.get_rule("MISSING-01")