"""Persistent ChromaDB knowledge-base ingestion and retrieval service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Optional

import chromadb


RULE_HEADING = re.compile(r"^## Rule \[([^]]+)\] — (.+)$", re.MULTILINE)
FIELD = re.compile(r"^- \*\*(Severity|Tags|Domain):\*\* (.+)$", re.MULTILINE)


@dataclass(frozen=True)
class KnowledgeChunk:
    """A rule-sized document ready for vector indexing."""

    id: str
    text: str
    metadata: dict[str, str]


class KnowledgeService:
    """Ingest Markdown rules and query a persistent Chroma collection.

    Chroma's default embedding function is used unless an embedding function is
    supplied. This keeps local learning offline after Chroma's model is present.
    """

    def __init__(
        self,
        persist_directory: str | Path = "data/chroma_db",
        collection_name: str = "coding_standards",
        embedding_function: Any = None,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        options = {"name": collection_name}
        if embedding_function is not None:
            options["embedding_function"] = embedding_function
        self.collection = self.client.get_or_create_collection(**options)

    def ingest_file(self, path: str | Path, *, replace: bool = True) -> int:
        """Parse and index one Markdown file, returning its chunk count."""
        source = Path(path).resolve()
        chunks = self.parse_markdown(source)
        if not chunks:
            raise ValueError(f"No rule sections found in {source}")
        if replace:
            self.collection.delete(ids=[chunk.id for chunk in chunks])
        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
        )
        return len(chunks)

    def ingest_directory(self, directory: str | Path, *, replace: bool = True) -> int:
        """Index every Markdown file below a directory."""
        files = sorted(Path(directory).rglob("*.md"))
        return sum(self.ingest_file(path, replace=replace) for path in files)

    def search(self, query: str, domain: Optional[str] = None, top_k: int = 3) -> list[dict[str, Any]]:
        """Return nearest rules, optionally filtered by domain."""
        if not query.strip():
            raise ValueError("query must not be empty")
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        kwargs: dict[str, Any] = {"query_texts": [query], "n_results": top_k}
        if domain:
            kwargs["where"] = {"domain": domain}
        result = self.collection.query(**kwargs)
        rows: list[dict[str, Any]] = []
        for index, document in enumerate(result.get("documents", [[]])[0]):
            rows.append(
                {
                    "text": document,
                    "metadata": result["metadatas"][0][index],
                    "distance": result.get("distances", [[]])[0][index],
                }
            )
        return rows

    def get_by_rule_id(self, rule_id: str) -> list[dict[str, Any]]:
        """Return the indexed chunk(s) with an exact rule ID."""
        result = self.collection.get(where={"rule_id": rule_id}, include=["documents", "metadatas"])
        return [
            {"text": document, "metadata": result["metadatas"][index]}
            for index, document in enumerate(result.get("documents", []))
        ]

    @staticmethod
    def parse_markdown(path: Path) -> list[KnowledgeChunk]:
        text = path.read_text(encoding="utf-8")
        domain_match = re.search(r"^- \*\*Domain:\*\* `([^`]+)`$", text, re.MULTILINE)
        if not domain_match:
            raise ValueError(f"Missing Domain metadata in {path}")
        domain = domain_match.group(1)
        matches = list(RULE_HEADING.finditer(text))
        chunks: list[KnowledgeChunk] = []
        for index, match in enumerate(matches):
            section = text[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(text)].strip()
            fields = dict(FIELD.findall(section))
            rule_id = match.group(1)
            chunks.append(
                KnowledgeChunk(
                    id=rule_id,
                    text=section,
                    metadata={
                        "domain": domain,
                        "rule_id": rule_id,
                        "title": match.group(2),
                        "severity": fields.get("Severity", "unspecified"),
                        "tags": fields.get("Tags", ""),
                        "source": path.name,
                    },
                )
            )
        return chunks