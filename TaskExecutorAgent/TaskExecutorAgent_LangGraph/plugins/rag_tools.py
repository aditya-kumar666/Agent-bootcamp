"""Agent-facing tools for searching the curated engineering knowledge base."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


class RagToolsPlugin:
    """Expose KnowledgeService operations as formatted tool results."""

    def __init__(self, service: Any = None, workspace_root: Optional[Path] = None) -> None:
        if service is None:
            from services.knowledge_service import KnowledgeService

            root = workspace_root or Path(__file__).resolve().parents[1]
            service = KnowledgeService(root / "data" / "chroma_db")
        self.service = service

    def search_standards(self, query: str, domain: str = "", top_k: int = 3) -> str:
        """Search standards semantically and return Markdown with rule citations."""
        results = self.service.search(query, domain=domain or None, top_k=top_k)
        if not results:
            return "No matching standards found."
        heading = f"# Standards search: {query}"
        if domain:
            heading += f" (domain: `{domain}`)"
        return heading + "\n\n" + "\n\n".join(self._format_result(result) for result in results)

    def get_guidelines_by_domain(self, domain: str) -> str:
        """Return all indexed rules for a domain in a stable Markdown format."""
        results = self.service.collection.get(
            where={"domain": domain},
            include=["documents", "metadatas"],
        )
        documents = results.get("documents", [])
        metadata = results.get("metadatas", [])
        if not documents:
            return f"No guidelines found for domain `{domain}`."
        items = [self._format_result({"text": text, "metadata": metadata[index]}) for index, text in enumerate(documents)]
        return f"# Guidelines: `{domain}`\n\n" + "\n\n".join(items)

    def get_rule(self, rule_id: str) -> str:
        """Return one exact rule by its explicit rule ID."""
        results = self.service.get_by_rule_id(rule_id)
        if not results:
            return f"No guideline found for rule `{rule_id}`."
        return self._format_result(results[0])

    @staticmethod
    def _format_result(result: dict[str, Any]) -> str:
        metadata = result["metadata"]
        distance = result.get("distance")
        score = f" | distance: `{distance:.4f}`" if isinstance(distance, (int, float)) else ""
        return (
            f"## [{metadata.get('rule_id', 'UNKNOWN')}] {metadata.get('title', '')}\n"
            f"**Domain:** `{metadata.get('domain', '')}` | "
            f"**Severity:** `{metadata.get('severity', 'unspecified')}`{score}\n\n"
            f"{result['text']}"
        )