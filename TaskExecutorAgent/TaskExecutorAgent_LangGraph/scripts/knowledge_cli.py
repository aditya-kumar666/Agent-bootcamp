"""Small manual-learning CLI for the Phase 2 KnowledgeService."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.knowledge_service import KnowledgeService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="data/chroma_db")
    subparsers = parser.add_subparsers(dest="command", required=True)
    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("path", type=Path)
    search = subparsers.add_parser("search")
    search.add_argument("query")
    search.add_argument("--domain")
    search.add_argument("--top-k", type=int, default=3)
    rule = subparsers.add_parser("rule")
    rule.add_argument("rule_id")
    args = parser.parse_args()
    service = KnowledgeService(args.db)
    if args.command == "ingest":
        count = service.ingest_directory(args.path) if args.path.is_dir() else service.ingest_file(args.path)
        print(f"Indexed {count} chunks into {args.db}")
    elif args.command == "search":
        for result in service.search(args.query, args.domain, args.top_k):
            print(f"[{result['metadata']['rule_id']}] distance={result['distance']:.4f}\n{result['text']}\n")
    else:
        for result in service.get_by_rule_id(args.rule_id):
            print(result["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())