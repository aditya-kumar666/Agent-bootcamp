from pathlib import Path

from agents.review_agent import ReviewAgent


ROOT = Path(__file__).resolve().parents[1]


def test_review_prompt_requires_rag_citations():
    prompt = (ROOT / "prompts" / "review.txt").read_text(encoding="utf-8")

    assert "rag_tools.search_standards" in prompt
    assert "rag_tools.get_rule" in prompt
    assert "exact rule ID" in prompt
    assert "Identify code characteristics" in prompt


def test_rule_citation_guidance_preserves_cited_output():
    output = "Findings:\n- [Severity: High] [SEC-INJ-01] Unsafe query construction."

    assert ReviewAgent._ensure_rule_citation_guidance(output) == output


def test_rule_citation_guidance_flags_uncited_output():
    result = ReviewAgent._ensure_rule_citation_guidance("Status: PASS\nFindings:\n- No issues found.")

    assert "CitationNote:" in result
    assert "exact returned rule ID" in result


def test_review_appends_retrieved_rule_ids():
    agent = ReviewAgent.__new__(ReviewAgent)
    agent.last_tool_rule_ids = ["SEC-INJ-01", "TEST-EDGE-01"]

    result = agent._append_used_rule_ids("Status: FAIL")

    assert "RAG_RULE_IDS_USED: SEC-INJ-01, TEST-EDGE-01" in result