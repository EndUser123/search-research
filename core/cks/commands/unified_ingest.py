#!/usr/bin/env python3
"""Unified CKS Ingestion Script.
============================

The BEST way to ingest knowledge into CKS with full semantic search.

Features:
- Semantic embeddings (all-MiniLM-L6-v2)
- Query expansion (synonyms, abbreviations)
- Spell correction
- Multiple fusion methods (RRF, combsum, MMR)
- All entry types supported
- File ingestion (markdown, code, text)

Usage:
    # Ingest a file
    python unified_ingest.py --file README.md --title "Project README" --type knowledge

    # Ingest code
    python unified_ingest.py --file adapter.py --type code --tags "github,api"

    # Ingest a memory
    python unified_ingest.py --memory "How to fix X" "Do Y then Z"

    # Search with semantic + expansion
    python unified_ingest.py --search "github repo search" --semantic --expand

    # Search with spell correction
    python unified_ingest.py --search "githuh adaptar" --semantic --spell-correct

    # Show statistics
    python unified_ingest.py --stats
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add src to path for imports
# The script is at: P:\\\\\\__csf/src/features/cks/commands/unified_ingest.py
# Project root is 4 levels up
project_root = Path(__file__).parent.parent.parent.parent
src_dir = project_root / "src"

# Also add project root for imports


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

# Valid entry types for CKS
VALID_ENTRY_TYPES = [
    "memory",
    "pattern",
    "code",
    "knowledge",
    "correction",
    "decision",
    "commitment",
    "insight",
    "learning",
    "docs",
]

# Language detection for common extensions
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".ps1": "powershell",
    ".sql": "sql",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".md": "markdown",
    ".rst": "rst",
    ".txt": "text",
}


class UnifiedCKSIngestion:
    """Unified CKS ingestion with full semantic search support."""

    def __init__(self, enable_semantic: bool = True, db_path: str | Path | None = None) -> None:
        """Initialize the unified CKS ingestion system.

        Args:
            enable_semantic: Enable semantic search with embeddings.
            db_path: Optional custom database path for test isolation.

        """
        from ..unified import CKS

        self.cks = CKS(db_path=db_path, enable_semantic=enable_semantic)
        self.enable_semantic = enable_semantic and self.cks.enable_semantic

    def ingest_file(
        self,
        file_path: str | Path,
        title: str | None = None,
        entry_type: str = "knowledge",
        tags: list[str] | None = None,
        category: str | None = None,
        **metadata,
    ) -> dict[str, str]:
        """Ingest a file into CKS with semantic embedding.

        Args:
            file_path: Path to the file to ingest.
            title: Title for the entry (auto-detected from file if not provided).
            entry_type: Type of entry (knowledge, code, pattern, etc.).
            tags: List of tags for categorization.
            category: Category for the entry.
            **metadata: Additional metadata fields.

        Returns:
            Dict with entry_id and status.

        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}")

        # Auto-detect title from content if not provided
        if not title:
            title = self._extract_title(content, file_path)

        # Auto-detect language from extension
        language = LANGUAGE_MAP.get(file_path.suffix, "text")

        # Build metadata
        full_metadata = {
            "file": str(file_path),
            "language": language,
            "size": len(content),
            "ingested_at": datetime.now(UTC).isoformat(),
        }
        if tags:
            full_metadata["tags"] = tags
        if category:
            full_metadata["category"] = category
        full_metadata.update(metadata)

        # Ingest based on type
        if entry_type == "memory":
            # Memory requires question/answer format
            entry_id = self.cks.ingest_memory(
                question=title,
                answer=content,
                source_chunk=content[:2000],  # First 2k chars for embedding
                **full_metadata,
            )
        else:
            entry_id = self.cks.ingest_pattern(
                title=title,
                content=content,
                entry_type=entry_type,
                source_chunk=content[:2000],  # First 2k chars for embedding
                **full_metadata,
            )

        return {
            "entry_id": entry_id,
            "title": title,
            "type": entry_type,
            "file": str(file_path),
            "status": "success",
        }

    def ingest_memory(
        self,
        question: str,
        answer: str,
        tags: list[str] | None = None,
        category: str | None = None,
        **metadata,
    ) -> dict[str, str]:
        """Ingest a Q&A memory into CKS.

        Args:
            question: The question or task description.
            answer: The answer or solution.
            tags: List of tags.
            category: Category for the memory.
            **metadata: Additional metadata.

        Returns:
            Dict with entry_id and status.

        """
        full_metadata = {"ingested_at": datetime.now(UTC).isoformat()}
        if tags:
            full_metadata["tags"] = tags
        if category:
            full_metadata["category"] = category
        full_metadata.update(metadata)

        entry_id = self.cks.ingest_memory(
            question=question,
            answer=answer,
            source_chunk=answer[:2000],
            **full_metadata,
        )

        return {
            "entry_id": entry_id,
            "question": question,
            "type": "memory",
            "status": "success",
        }

    def ingest_pattern(
        self,
        title: str,
        content: str,
        entry_type: str = "pattern",
        tags: list[str] | None = None,
        category: str | None = None,
        **metadata,
    ) -> dict[str, str]:
        """Ingest a pattern or knowledge entry.

        Args:
            title: Title of the entry.
            content: Content of the entry.
            entry_type: Type of entry (pattern, code, knowledge, etc.).
            tags: List of tags.
            category: Category for the entry.
            **metadata: Additional metadata.

        Returns:
            Dict with entry_id and status.

        """
        full_metadata = {"ingested_at": datetime.now(UTC).isoformat()}
        if tags:
            full_metadata["tags"] = tags
        if category:
            full_metadata["category"] = category
        full_metadata.update(metadata)

        entry_id = self.cks.ingest_pattern(
            title=title,
            content=content,
            entry_type=entry_type,
            source_chunk=content[:2000],
            **full_metadata,
        )

        return {
            "entry_id": entry_id,
            "title": title,
            "type": entry_type,
            "status": "success",
        }

    def search(
        self,
        query: str,
        semantic: bool = True,
        expand: bool = False,
        spell_correct: bool = False,
        limit: int = 10,
        entry_type: str | None = None,
        fusion_method: str | None = None,
        diversity: float | None = None,
    ) -> list[dict]:
        """Search CKS with advanced options.

        Args:
            query: Search query.
            semantic: Use semantic search (vs keyword search).
            expand: Use query expansion.
            spell_correct: Apply spell correction.
            limit: Maximum results.
            entry_type: Filter by entry type.
            fusion_method: Fusion method (rrf, combsum, adaptive, mmr).
            diversity: Diversity factor for MMR (0.0-1.0).

        Returns:
            List of search results.

        """
        if semantic and self.enable_semantic:
            results = self.cks.search_semantic(
                query=query,
                entry_type=entry_type,
                limit=limit,
                expand_query=expand,
                spell_correct=spell_correct,
                fusion_method=fusion_method,
                diversity=diversity,
            )
        else:
            results = self.cks.search(query=query, entry_type=entry_type, limit=limit)

        return results

    def get_statistics(self) -> dict:
        """Get CKS statistics."""
        cursor = self.cks.conn.cursor()

        stats = {"total_entries": 0, "by_type": {}, "with_embeddings": 0}

        # Total entries
        cursor.execute("SELECT COUNT(*) FROM entries")
        stats["total_entries"] = cursor.fetchone()[0]

        # By type
        cursor.execute("SELECT type, COUNT(*) FROM entries GROUP BY type")
        for row in cursor.fetchall():
            stats["by_type"][row[0]] = row[1]

        # With embeddings
        cursor.execute("SELECT COUNT(*) FROM entries WHERE embedding IS NOT NULL")
        stats["with_embeddings"] = cursor.fetchone()[0]

        stats["semantic_enabled"] = self.enable_semantic

        return stats

    def _extract_title(self, content: str, file_path: Path) -> str:
        """Extract title from content or use filename.

        Args:
            content: File content.
            file_path: Path to the file.

        Returns:
            Extracted or generated title.

        """
        # Try markdown headers
        for line in content.split("\n")[:20]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            if line.startswith("## "):
                return line[3:].strip()

        # Use filename without extension
        return file_path.stem.replace("_", " ").replace("-", " ").title()


def format_result(result: dict, show_similarity: bool = False) -> str:
    """Format a search result for display.

    Args:
        result: Result dict from csf.cks.
        show_similarity: Show similarity score.

    Returns:
        Formatted string.

    """
    lines = []
    title = result.get("title") or result.get("metadata", {}).get("title", "Untitled")
    entry_type = result.get("type", "unknown")
    created = result.get("created_at", "unknown")

    lines.append(f"  📄 {title}")
    lines.append(f"     Type: {entry_type} | Created: {created}")

    if show_similarity and "similarity" in result:
        sim = result["similarity"]
        emoji = "🟢" if sim > 0.5 else "🟡" if sim > 0.3 else "⚪"
        lines.append(f"     Similarity: {sim:.3f} {emoji}")

    # Show tags if available
    metadata = result.get("metadata", {}) or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}
    if "tags" in metadata:
        tags = metadata["tags"]
        if isinstance(tags, list):
            lines.append(f"     Tags: {', '.join(tags)}")

    # Show file if available
    if "file" in metadata:
        lines.append(f"     File: {metadata['file']}")

    # Show question for memory type
    if entry_type == "memory" and "question" in metadata:
        lines.append(f"     Q: {metadata['question'][:80]}...")

    return "\n".join(lines)


def ingest_multiple_files(
    ingestion: UnifiedCKSIngestion,
    pattern: str,
    entry_type: str,
    category: str | None = None,
    tags: list[str] | None = None,
    recursive: bool = False,
) -> list[dict]:
    """Ingest multiple files matching a pattern.

    Args:
        ingestion: UnifiedCKSIngestion instance.
        pattern: Glob pattern for files.
        entry_type: Entry type for all files.
        category: Category for entries.
        tags: Tags for entries.
        recursive: Search recursively.

    Returns:
        List of ingest results.

    """
    base_path = Path(pattern).parent if "/" in pattern or "\\" in pattern else Path()
    glob_pattern = Path(pattern).name

    files = list(base_path.rglob(glob_pattern)) if recursive else list(base_path.glob(glob_pattern))

    results = []
    for file_path in files:
        if file_path.is_file():
            try:
                result = ingestion.ingest_file(
                    file_path=file_path,
                    entry_type=entry_type,
                    category=category,
                    tags=tags,
                )
                results.append(result)
                print(f"✅ {file_path}")
            except Exception as e:
                print(f"❌ {file_path}: {e}")
                results.append({"file": str(file_path), "status": "error", "error": str(e)})

    return results


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified CKS Ingestion with Full Semantic Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--file", "-f", help="File to ingest")
    input_group.add_argument("--pattern", "-p", help="Glob pattern for multiple files")
    input_group.add_argument(
        "--memory", "-m", nargs=2, metavar=("Q", "A"), help="Ingest Q&A memory"
    )
    input_group.add_argument(
        "--pattern-text", nargs=2, metavar=("TITLE", "CONTENT"), help="Ingest pattern/knowledge"
    )
    input_group.add_argument("--search", "-s", help="Search CKS")
    input_group.add_argument("--stats", action="store_true", help="Show CKS statistics")

    # Ingestion options
    parser.add_argument("--title", "-t", help="Title for the entry")
    parser.add_argument(
        "--type", "-T", default="knowledge", choices=VALID_ENTRY_TYPES, help="Entry type"
    )
    parser.add_argument("--category", "-c", help="Category for the entry")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursive file search")

    # Search options
    parser.add_argument(
        "--keyword", action="store_true", help="Use keyword search instead of semantic"
    )
    parser.add_argument("--expand", "-e", action="store_true", help="Enable query expansion")
    parser.add_argument("--spell-correct", action="store_true", help="Enable spell correction")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max results")
    parser.add_argument("--entry-type", help="Filter by entry type")
    parser.add_argument(
        "--fusion", choices=["rrf", "combsum", "adaptive", "mmr"], help="Fusion method"
    )
    parser.add_argument("--diversity", type=float, help="Diversity factor (0.0-1.0)")

    # General options
    parser.add_argument("--no-semantic", action="store_true", help="Disable semantic search")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Parse tags
    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",")]

    # Initialize ingestion system
    ingestion = UnifiedCKSIngestion(enable_semantic=not args.no_semantic)

    try:
        # Statistics
        if args.stats:
            stats = ingestion.get_statistics()
            print("\n📊 CKS Statistics")
            print(f"   Total entries: {stats['total_entries']}")
            print(f"   With embeddings: {stats['with_embeddings']}")
            print(f"   Semantic enabled: {stats['semantic_enabled']}")
            print("\n   By type:")
            for entry_type, count in sorted(stats["by_type"].items()):
                print(f"     {entry_type}: {count}")
            return

        # Search
        if args.search:
            print(f"\n🔍 Searching for: {args.search}\n")

            results = ingestion.search(
                query=args.search,
                semantic=not args.keyword,
                expand=args.expand,
                spell_correct=args.spell_correct,
                limit=args.limit,
                entry_type=args.entry_type,
                fusion_method=args.fusion,
                diversity=args.diversity,
            )

            if not results:
                print("  No results found.")
                return

            print(f"  Found {len(results)} result(s):\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {format_result(result, show_similarity=not args.keyword)}\n")
            return

        # Ingest single file
        if args.file:
            result = ingestion.ingest_file(
                file_path=args.file,
                title=args.title,
                entry_type=args.type,
                tags=tags,
                category=args.category,
            )
            print("\n✅ Ingested successfully!")
            print(f"   Entry ID: {result['entry_id']}")
            print(f"   Title: {result['title']}")
            print(f"   Type: {result['type']}")
            if tags:
                print(f"   Tags: {', '.join(tags)}")
            return

        # Ingest multiple files
        if args.pattern:
            print(f"\n📁 Ingesting files matching: {args.pattern}\n")
            results = ingest_multiple_files(
                ingestion=ingestion,
                pattern=args.pattern,
                entry_type=args.type,
                category=category,
                tags=tags,
                recursive=args.recursive,
            )
            success = sum(1 for r in results if r.get("status") == "success")
            print(f"\n✅ Ingested {success}/{len(results)} files")
            return

        # Ingest memory
        if args.memory:
            question, answer = args.memory
            result = ingestion.ingest_memory(
                question=question,
                answer=Path(answer).read_text() if Path(answer).exists() else answer,
                tags=tags,
                category=args.category,
            )
            print("\n✅ Memory ingested!")
            print(f"   Entry ID: {result['entry_id']}")
            print(f"   Q: {question[:80]}...")
            return

        # Ingest pattern/knowledge
        if args.pattern_text:
            title, content_file = args.pattern_text
            content = (
                Path(content_file).read_text() if Path(content_file).exists() else content_file
            )
            result = ingestion.ingest_pattern(
                title=title,
                content=content,
                entry_type=args.type,
                tags=tags,
                category=args.category,
            )
            print("\n✅ Pattern ingested!")
            print(f"   Entry ID: {result['entry_id']}")
            print(f"   Title: {title}")
            return

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
