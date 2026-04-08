#!/usr/bin/env python3
"""CKS CLI Command Specification.

Constitutional Knowledge System command-line interface for:
- Semantic and keyword search
- Memory management (add, list, update)
- Entity filtering and management
- Statistics and diagnostics
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Add paths
from .entity_filter import CKSEntityFilter
from .unified import CKS


@dataclass
class CKSSearchSpec:
    """Specification for CKS search operations."""

    query: str
    use_keyword: bool = False
    entity_slug: str | None = None
    entry_type: str | None = None
    limit: int = 5
    auto_detect: bool = True
    show_metadata: bool = False
    json_output: bool = False

    # Phase 1 enhancement parameters
    expand_query: bool = False
    fusion_method: str | None = None
    diversity: float | None = None

    def validate(self) -> tuple[bool, list[str]]:
        """Validate search specification."""
        errors = []

        if not self.query or not self.query.strip():
            errors.append("Query cannot be empty")

        if self.limit < 1 or self.limit > 100:
            errors.append("Limit must be between 1 and 100")

        if self.entry_type:
            valid_types = [
                "memory",
                "pattern",
                "code",
                "knowledge",
                "correction",
                "decision",
                "commitment",
                "insight",
                "learning",
            ]
            if self.entry_type not in valid_types:
                errors.append(f"Invalid type. Must be one of: {', '.join(valid_types)}")

        # Validate Phase 1 & 2 parameters
        valid_fusion_methods = ("rrf", "adaptive", "weighted-average", "combsum")
        if self.fusion_method and self.fusion_method not in valid_fusion_methods:
            errors.append(f"fusion_method must be one of: {', '.join(valid_fusion_methods)}")

        if self.diversity is not None and (self.diversity < 0 or self.diversity > 1):
            errors.append("diversity must be between 0.0 and 1.0")

        return len(errors) == 0, errors


@dataclass
class CKSAddSpec:
    """Specification for adding entries to CKS."""

    question: str
    answer: str
    entry_type: str = "memory"
    source_chunk: str | None = None
    entity_slug: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> tuple[bool, list[str]]:
        """Validate add specification."""
        errors = []

        if not self.question or not self.question.strip():
            errors.append("Question cannot be empty")

        if not self.answer or not self.answer.strip():
            errors.append("Answer cannot be empty")

        valid_types = [
            "memory",
            "pattern",
            "code",
            "knowledge",
            "correction",
            "decision",
            "commitment",
            "insight",
            "learning",
        ]

        if self.entry_type not in valid_types:
            errors.append(f"Invalid type. Must be one of: {', '.join(valid_types)}")

        return len(errors) == 0, errors


@dataclass
class CKSListSpec:
    """Specification for listing CKS entries."""

    entry_type: str | None = None
    entity_slug: str | None = None
    limit: int = 20
    offset: int = 0
    order_by: str = "created_at"
    order_dir: str = "DESC"
    json_output: bool = False

    # Phase 1 enhancement parameters
    expand_query: bool = False
    fusion_method: str | None = None
    diversity: float | None = None

    def validate(self) -> tuple[bool, list[str]]:
        """Validate list specification."""
        errors = []

        if self.limit < 1 or self.limit > 100:
            errors.append("Limit must be between 1 and 100")

        if self.offset < 0:
            errors.append("Offset must be non-negative")

        if self.entry_type:
            valid_types = [
                "memory",
                "pattern",
                "code",
                "knowledge",
                "correction",
                "decision",
                "commitment",
                "insight",
                "learning",
            ]
            if self.entry_type not in valid_types:
                errors.append(f"Invalid type. Must be one of: {', '.join(valid_types)}")

        # Validate Phase 1 & 2 parameters
        valid_fusion_methods = ("rrf", "adaptive", "weighted-average", "combsum")
        if self.fusion_method and self.fusion_method not in valid_fusion_methods:
            errors.append(f"fusion_method must be one of: {', '.join(valid_fusion_methods)}")

        if self.diversity is not None and (self.diversity < 0 or self.diversity > 1):
            errors.append("diversity must be between 0.0 and 1.0")

        return len(errors) == 0, errors


@dataclass
class CKSEntitySpec:
    """Specification for entity operations."""

    action: str  # list, link, unlink
    entry_id: str | None = None
    entity_slug: str | None = None
    json_output: bool = False

    # Phase 1 enhancement parameters
    expand_query: bool = False
    fusion_method: str | None = None
    diversity: float | None = None

    def validate(self) -> tuple[bool, list[str]]:
        """Validate entity specification."""
        errors = []

        valid_actions = ["list", "link", "unlink"]

        if self.action not in valid_actions:
            errors.append(f"Invalid action. Must be one of: {', '.join(valid_actions)}")

        if self.action in ["link", "unlink"]:
            if not self.entry_id:
                errors.append("Entry ID required for link/unlink operations")
            if not self.entity_slug:
                errors.append("Entity slug required for link/unlink operations")

        return len(errors) == 0, errors


class CKSCommandExecutor:
    """Execute CKS CLI commands."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize executor with CKS instance."""
        self.cks = CKS(db_path)
        self.entity_filter = CKSEntityFilter(self.cks)

    def execute_search(self, spec: CKSSearchSpec) -> dict[str, Any]:
        """Execute search command."""
        valid, errors = spec.validate()
        if not valid:
            return {"success": False, "errors": errors}

        try:
            if spec.use_keyword:
                results = self.cks.search(
                    spec.query,
                    entry_type=spec.entry_type,
                    limit=spec.limit,
                )
            # Use entity filter if entity specified
            elif spec.entity_slug:
                results = self.entity_filter.search_with_entity_filter(
                    spec.query,
                    entity_slug=spec.entity_slug,
                    entry_type=spec.entry_type,
                    limit=spec.limit,
                    auto_detect=spec.auto_detect,
                )
            else:
                # Check if Phase 1 features are enabled
                results = self.cks.search_semantic(
                    spec.query,
                    entry_type=spec.entry_type,
                    limit=spec.limit,
                    expand_query=spec.expand_query,
                    fusion_method=spec.fusion_method,
                    diversity=spec.diversity,
                    entity_slug=spec.entity_slug,
                )

            return {
                "success": True,
                "query": spec.query,
                "results": results,
                "count": len(results),
            }

        except Exception as e:
            return {
                "success": False,
                "errors": [f"Search failed: {e!s}"],
            }

    def execute_add(self, spec: CKSAddSpec) -> dict[str, Any]:
        """Execute add command."""
        valid, errors = spec.validate()
        if not valid:
            return {"success": False, "errors": errors}

        try:
            # Add metadata
            metadata = {
                "source": "cks_cli",
                "created_at": datetime.now().isoformat(),
                **spec.metadata,
            }

            # Determine which ingest method to use based on type
            if spec.entry_type == "memory":
                entry_id = self.cks.ingest_memory(
                    spec.question,
                    spec.answer,
                    source_chunk=spec.source_chunk or spec.question,
                    **metadata,
                )
            elif spec.entry_type == "pattern":
                entry_id = self.cks.ingest_pattern(
                    spec.question,
                    spec.answer,
                    source_chunk=spec.source_chunk or spec.question,
                    **metadata,
                )
            elif spec.entry_type == "code":
                entry_id = self.cks.ingest_code(
                    spec.question,
                    spec.answer,
                    source_chunk=spec.source_chunk or spec.question,
                    **metadata,
                )
            else:
                # Use knowledge for other types
                entry_id = self.cks.ingest_memory(
                    spec.question,
                    spec.answer,
                    source_chunk=spec.source_chunk or spec.question,
                    type=spec.entry_type,
                    **metadata,
                )

            # Link to entity if specified
            if spec.entity_slug and entry_id:
                self.entity_filter.link_entity(entry_id, spec.entity_slug)

            return {
                "success": True,
                "entry_id": entry_id,
                "message": f"Entry added: {entry_id}",
            }

        except Exception as e:
            return {
                "success": False,
                "errors": [f"Add failed: {e!s}"],
            }

    def execute_list(self, spec: CKSListSpec) -> dict[str, Any]:
        """Execute list command."""
        valid, errors = spec.validate()
        if not valid:
            return {"success": False, "errors": errors}

        try:
            cursor = self.cks.conn.cursor()

            # Build query
            conditions = []
            params = []

            if spec.entry_type:
                conditions.append("type = ?")
                params.append(spec.entry_type)

            if spec.entity_slug:
                conditions.append("""
                    id IN (SELECT entry_id FROM entry_entities WHERE entity_slug = ?)
                """)
                params.append(spec.entity_slug)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT id, type, title, created_at, usage_count
                FROM entries
                {where_clause}
                ORDER BY {spec.order_by} {spec.order_dir}
                LIMIT ? OFFSET ?
            """

            params.extend([spec.limit, spec.offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append(
                    {
                        "id": row["id"],
                        "type": row["type"],
                        "title": row["title"],
                        "created_at": row["created_at"],
                        "usage_count": row["usage_count"] or 0,
                    }
                )

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM entries {where_clause}"
            cursor.execute(count_query, params[:-2])  # Exclude limit/offset
            total = cursor.fetchone()["total"]

            return {
                "success": True,
                "results": results,
                "count": len(results),
                "total": total,
                "limit": spec.limit,
                "offset": spec.offset,
            }

        except Exception as e:
            return {
                "success": False,
                "errors": [f"List failed: {e!s}"],
            }

    def execute_stats(self) -> dict[str, Any]:
        """Execute stats command."""
        try:
            stats = self.cks.get_statistics()

            return {
                "success": True,
                "stats": stats,
            }

        except Exception as e:
            return {
                "success": False,
                "errors": [f"Stats failed: {e!s}"],
            }

    def execute_entities(self, spec: CKSEntitySpec) -> dict[str, Any]:
        """Execute entity command."""
        valid, errors = spec.validate()
        if not valid:
            return {"success": False, "errors": errors}

        try:
            if spec.action == "list":
                cursor = self.cks.conn.cursor()
                cursor.execute("SELECT slug, name, type FROM entities ORDER BY slug")
                rows = cursor.fetchall()

                entities = []
                for row in rows:
                    entities.append(
                        {
                            "slug": row["slug"],
                            "name": row["name"],
                            "type": row["type"],
                        }
                    )

                return {
                    "success": True,
                    "entities": entities,
                    "count": len(entities),
                }

            if spec.action == "link":
                result = self.entity_filter.link_entity(spec.entry_id, spec.entity_slug)
                return {
                    "success": result,
                    "message": f"Linked {spec.entry_id} to {spec.entity_slug}"
                    if result
                    else "Link failed",
                }

            if spec.action == "unlink":
                result = self.entity_filter.unlink_entity(spec.entry_id, spec.entity_slug)
                return {
                    "success": result,
                    "message": f"Unlinked {spec.entry_id} from {spec.entity_slug}"
                    if result
                    else "Unlink failed",
                }

        except Exception as e:
            return {
                "success": False,
                "errors": [f"Entity operation failed: {e!s}"],
            }


def format_output(result: dict[str, Any], json_output: bool = False) -> str:
    """Format command output for display."""
    if json_output:
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy(obj):
            import numpy as np

            if isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_numpy(v) for v in obj]
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj) if isinstance(obj, np.floating) else int(obj)
            if hasattr(obj, "item"):  # numpy scalar
                return obj.item()
            return obj

        return json.dumps(convert_numpy(result), indent=2)

    if not result.get("success"):
        return "Error:\n" + "\n".join(f"  - {e}" for e in result.get("errors", []))

    output = []

    # Search results
    if "results" in result:
        results = result["results"]
        output.append(f"Found {result['count']} result(s):\n")

        for i, r in enumerate(results, 1):
            title = r.get("title", "N/A")
            entry_type = r.get("type", "memory")
            sim = r.get("similarity", 0)
            content = r.get("content", r.get("answer", ""))[:100]

            output.append(f"{i}. [{entry_type}] {title}")
            if sim > 0:
                output.append(f"   Similarity: {sim:.3f}")
            output.append(f"   {content}...")

            if r.get("entities"):
                entities = ", ".join([e["slug"] for e in r["entities"]])
                output.append(f"   Entities: {entities}")

            output.append("")

    # Add result
    if "entry_id" in result:
        output.append(result.get("message", "Entry added"))

    # List results
    if "results" in result and "total" in result:
        results = result["results"]
        total = result["total"]
        output.append(f"Showing {len(results)} of {total} entries:\n")

        for r in results:
            output.append(f"- [{r['type']}] {r['title'][:60]}")
            output.append(
                f"  ID: {r['id'][:12]}... | Created: {r['created_at'][:10]} | Used: {r['usage_count']}"
            )

    # Stats
    if "stats" in result:
        stats = result["stats"]
        output.append("CKS Statistics:\n")
        output.append(f"  Total entries: {stats.get('total_entries', 0)}")
        output.append(f"  Database size: {stats.get('database_size_mb', 0):.2f} MB")
        output.append(
            f"  Semantic search: {'enabled' if stats.get('semantic_enabled') else 'disabled'}"
        )

        if "by_type" in stats:
            output.append("\n  By type:")
            for entry_type, count in stats["by_type"].items():
                output.append(f"    {entry_type}: {count}")

    # Entities
    if "entities" in result:
        entities = result["entities"]
        output.append(f"Entities ({len(entities)}):\n")
        for e in entities:
            output.append(f"- {e['slug']} ({e['type']})")
            output.append(f"  {e['name']}")

    return "\n".join(output)


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="cks",
        description="Constitutional Knowledge System CLI - Semantic search with Phase 1 enhancements",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

    # Search subcommand
    search_parser = subparsers.add_parser(
        "search",
        help="Search CKS memories (with smart Phase 1 & 2 enhancements enabled by default)",
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--keyword", action="store_true", help="Use keyword search")
    search_parser.add_argument("--entity", help="Filter by entity")
    # Phase 1 enhancement arguments
    # Phase 1 enhancement arguments
    search_parser.add_argument(
        "--expand-query",
        action="store_true",
        help="[Smart Default: Auto-enabled for abbreviations] Enable query expansion using synonyms and domain knowledge (+20-30%% recall)",
    )
    search_parser.add_argument(
        "--fusion-method",
        choices=["rrf", "adaptive", "weighted-average", "combsum"],
        help="[Smart Default: adaptive] Fusion method: 'adaptive'=intelligent selection, 'rrf'=comprehensive, 'weighted-average'=precision",
    )
    search_parser.add_argument(
        "--diversity",
        type=float,
        help="[Smart Default: Auto-enabled for broad queries] MMR diversity 0.0-1.0: 0=relevance, 1=variety (avoids redundant results)",
    )
    search_parser.add_argument(
        "--type",
        help="[Smart Default: Auto-detected] Filter by entry type (memory, pattern, code, knowledge, correction, decision, etc.)",
    )
    search_parser.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    search_parser.add_argument("--json", action="store_true", help="JSON output")

    # Add subcommand
    add_parser = subparsers.add_parser("add", help="Add memory to CKS")
    add_parser.add_argument("--question", required=True, help="Question/title")
    add_parser.add_argument("--answer", required=True, help="Answer/content")
    add_parser.add_argument("--type", default="memory", help="Entry type (default: memory)")
    add_parser.add_argument("--source", help="Original user question")
    add_parser.add_argument("--entity", help="Link to entity")
    add_parser.add_argument("--json", action="store_true", help="JSON output")

    # List subcommand
    list_parser = subparsers.add_parser("list", help="List CKS entries")
    list_parser.add_argument("--type", help="Filter by entry type")
    list_parser.add_argument("--entity", help="Filter by entity")
    list_parser.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    list_parser.add_argument("--offset", type=int, default=0, help="Pagination offset")
    list_parser.add_argument("--json", action="store_true", help="JSON output")

    # Stats subcommand
    stats_parser = subparsers.add_parser("stats", help="Show CKS statistics")
    stats_parser.add_argument("--json", action="store_true", help="JSON output")

    # Entities subcommand
    entity_parser = subparsers.add_parser("entities", help="Entity management")
    entity_parser.add_argument("action", choices=["list", "link", "unlink"], help="Entity action")
    entity_parser.add_argument("--entry", help="Entry ID (for link/unlink)")
    entity_parser.add_argument("--entity", help="Entity slug (for link/unlink)")
    entity_parser.add_argument("--json", action="store_true", help="JSON output")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        return 1

    executor = CKSCommandExecutor()

    # Route to appropriate handler
    if args.subcommand == "search":
        spec = CKSSearchSpec(
            query=args.query,
            use_keyword=args.keyword,
            entity_slug=args.entity,
            entry_type=args.type,
            limit=args.limit,
            json_output=args.json,
            expand_query=getattr(args, "expand_query", False),
            fusion_method=getattr(args, "fusion_method", None),
            diversity=getattr(args, "diversity", None),
        )
        result = executor.execute_search(spec)

    elif args.subcommand == "add":
        spec = CKSAddSpec(
            question=args.question,
            answer=args.answer,
            entry_type=args.type,
            source_chunk=args.source,
            entity_slug=args.entity,
        )
        result = executor.execute_add(spec)

    elif args.subcommand == "list":
        spec = CKSListSpec(
            entry_type=args.type,
            entity_slug=args.entity,
            limit=args.limit,
            offset=args.offset,
            json_output=args.json,
        )
        result = executor.execute_list(spec)

    elif args.subcommand == "stats":
        result = executor.execute_stats()

    elif args.subcommand == "entities":
        spec = CKSEntitySpec(
            action=args.action,
            entry_id=args.entry,
            entity_slug=args.entity,
            json_output=args.json,
        )
        result = executor.execute_entities(spec)

    # Format and print output
    output = format_output(result, getattr(args, "json", False))
    print(output)

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
