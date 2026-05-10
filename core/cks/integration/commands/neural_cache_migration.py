#!/usr/bin/env python3
"""Neural Cache Migration to CKS.

Migrates the Neural Cache section from csf-integration SKILL.md
to the CKS vector data store for semantic search and knowledge retrieval.

Constitutional Requirements:
- Solo developer optimization (simple CLI interface)
- Evidence-based implementation (TDD approach with tests)
- Force multiplier integration (CKS semantic search)
- No enterprise bloat (direct Python implementation)

Usage:
    python -m cks.integration.commands.neural_cache_migration --dry-run
    python -m cks.integration.commands.neural_cache_migration --migrate
    python -m cks.integration.commands.neural_cache_migration --stats
"""

import hashlib
import json
import logging
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class EntryType(Enum):
    """Neural Cache entry types."""

    FIX = "FIX"
    PATTERN = "PATTERN"
    SUCCESS = "SUCCESS"
    INSIGHT = "INSIGHT"
    ANTIPATTERN = "ANTIPATTERN"
    PRACTICE = "PRACTICE"
    UX = "UX"
    PERF = "PERF"
    ARCH = "ARCH"
    DISPLAY = "DISPLAY"
    BUG = "BUG"
    DOCS = "DOCS"
    LESSON = "LESSON"

    @classmethod
    def from_string(cls, value: str) -> "EntryType | None":
        """Parse EntryType from string."""
        try:
            return cls[value]
        except KeyError:
            return None


@dataclass
class NeuralCacheEntry:
    """A single entry from the Neural Cache section."""

    entry_type: str  # FIX, PATTERN, SUCCESS, etc.
    date: str  # YYYY-MM-DD
    topic: str  # The bold/descriptive part
    description: str  # The explanation
    file_reference: str | None  # File path and line reference if present
    original_line: str  # Original line for reference


@dataclass
class MigrationStats:
    """Statistics from a migration run."""

    total_entries: int
    entries_by_type: dict[str, int]
    entries_with_file_refs: int
    date_range: tuple[str, str]  # (earliest, latest)


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success: bool
    ingested_count: int = 0
    failed_count: int = 0
    entries_with_metadata: int = 0
    categories: dict[str, int] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    message: str = ""


class NeuralCacheParser:
    """Parse Neural Cache section from SKILL.md file."""

    # Regex pattern for entry lines
    # Format: - [TYPE YYYY-MM-DD] **Topic**: Description - file_ref:line
    ENTRY_PATTERN = re.compile(
        r"^-\s*\[([A-Z]+)\s+(\d{4}-\d{2}-\d{2})\]\s+\*\*([^*]+)\*\*:\s*(.+?)(?:\s*-\s*([^\s]+(?:\:\d+(?:-\d+)?)?))?$",
    )

    def __init__(self, skill_file: str | Path) -> None:
        """Initialize parser with path to SKILL.md file.

        Args:
            skill_file: Path to the SKILL.md file

        """
        self.skill_file = Path(skill_file)
        self.entries: list[NeuralCacheEntry] = []
        self._valid_types = {e.name for e in EntryType}

    def parse(self) -> list[NeuralCacheEntry]:
        """Parse Neural Cache section and extract entries.

        Returns:
            List of parsed NeuralCacheEntry objects

        Raises:
            FileNotFoundError: If skill_file doesn't exist

        """
        if not self.skill_file.exists():
            raise FileNotFoundError(f"Skill file not found: {self.skill_file}")

        content = self.skill_file.read_text(encoding="utf-8")
        self.entries = self._extract_neural_cache_entries(content)
        return self.entries

    def _extract_neural_cache_entries(self, content: str) -> list[NeuralCacheEntry]:
        """Extract Neural Cache entries from markdown content.

        Args:
            content: Full markdown content of SKILL.md

        Returns:
            List of parsed entries

        """
        entries = []
        in_neural_cache = False
        lines = content.split("\n")

        for line in lines:
            # Find Neural Cache section start
            if "## Neural Cache" in line or "## 🧠 Neural Cache" in line:
                in_neural_cache = True
                continue

            # Exit at next major heading
            if in_neural_cache and line.startswith("## ") and "Neural Cache" not in line:
                break

            if not in_neural_cache:
                continue

            # Skip empty lines and sub-headings
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "###")):
                continue

            # Try to parse as entry
            entry = self._parse_entry_line(line)
            if entry:
                entries.append(entry)

        return entries

    def _parse_entry_line(self, line: str) -> NeuralCacheEntry | None:
        """Parse a single entry line.

        Args:
            line: Raw line from markdown file

        Returns:
            NeuralCacheEntry if valid, None otherwise

        """
        match = self.ENTRY_PATTERN.match(line.strip())
        if not match:
            return None

        entry_type, date, topic, description, file_ref = match.groups()

        # Validate entry type
        if entry_type not in self._valid_types:
            return None

        return NeuralCacheEntry(
            entry_type=entry_type,
            date=date,
            topic=topic.strip(),
            description=description.strip(),
            file_reference=file_ref.strip() if file_ref else None,
            original_line=line.strip(),
        )

    def get_stats(self) -> MigrationStats:
        """Get statistics about parsed entries.

        Returns:
            MigrationStats with entry information

        """
        if not self.entries:
            try:
                self.parse()
            except FileNotFoundError:
                return MigrationStats(0, {}, 0, ("", ""))

        entries_by_type: dict[str, int] = {}
        dates = []

        for entry in self.entries:
            entries_by_type[entry.entry_type] = entries_by_type.get(entry.entry_type, 0) + 1
            dates.append(entry.date)

        date_range = ("", "")
        if dates:
            date_range = (min(dates), max(dates))

        return MigrationStats(
            total_entries=len(self.entries),
            entries_by_type=entries_by_type,
            entries_with_file_refs=sum(1 for e in self.entries if e.file_reference),
            date_range=date_range,
        )


class NeuralCacheMigrator:
    """Migrate Neural Cache entries to CKS database."""

    # Main CKS database path (where all queries happen)
    DB_PATH = PROJECT_ROOT / "__csf" / "data" / "cks.db"

    # Category mappings for CKS
    CATEGORY_MAPPING = {
        "FIX": "bug_fix",
        "PATTERN": "design_pattern",
        "SUCCESS": "success_case",
        "INSIGHT": "insight",
        "ANTIPATTERN": "anti_pattern",
        "PRACTICE": "best_practice",
        "UX": "user_experience",
        "PERF": "performance",
        "ARCH": "architecture",
        "DISPLAY": "display",
        "BUG": "bug_report",
        "DOCS": "documentation",
        "LESSON": "lesson_learned",
    }

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize migrator.

        Args:
            db_path: Optional custom database path

        """
        self.db_path = db_path or self.DB_PATH
        self.conn: sqlite3.Connection | None = None
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection, creating if needed."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self._initialize_database()
        return self.conn

    def _initialize_database(self) -> None:
        """Initialize CKS database tables if they don't exist."""
        if self.conn is None:
            return

        cursor = self.conn.cursor()

        # Knowledge nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Knowledge edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Vector nodes table for semantic search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_nodes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                vector_id TEXT UNIQUE,
                model_name TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def _generate_entry_id(self, entry: NeuralCacheEntry) -> str:
        """Generate unique entry ID."""
        content = f"{entry.entry_type}_{entry.date}_{entry.topic}_{hash(entry.description)}"
        return f"nc_{hashlib.md5(content.encode()).hexdigest()[:16]}"

    def ingest_entries(
        self,
        entries: list[NeuralCacheEntry],
        dry_run: bool = False,
    ) -> MigrationResult:
        """Ingest Neural Cache entries into CKS.

        Args:
            entries: List of NeuralCacheEntry objects
            dry_run: If True, don't actually write to database

        Returns:
            MigrationResult with ingestion statistics

        """
        result = MigrationResult(success=True)

        for entry in entries:
            try:
                if not dry_run:
                    self._ingest_single_entry(entry)

                result.ingested_count += 1
                result.entries_with_metadata += 1

                # Track categories
                cat = self.CATEGORY_MAPPING.get(entry.entry_type, entry.entry_type.lower())
                result.categories[cat] = result.categories.get(cat, 0) + 1

            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"{entry.topic}: {e}")

        return result

    def _ingest_single_entry(self, entry: NeuralCacheEntry) -> None:
        """Ingest a single entry into CKS database.

        Args:
            entry: NeuralCacheEntry to ingest

        """
        conn = self._get_connection()
        cursor = conn.cursor()

        entry_id = self._generate_entry_id(entry)
        category = self.CATEGORY_MAPPING.get(entry.entry_type, entry.entry_type.lower())

        # Prepare metadata
        metadata = {
            "title": entry.topic,
            "category": category,
            "source": "neural_cache",
            "entry_type": entry.entry_type,
            "date": entry.date,
            "file_reference": entry.file_reference,
            "ingestion_date": datetime.now().isoformat(),
            "original_line": entry.original_line,
        }

        # Prepare structured content
        structured_content = json.dumps(
            {
                "title": entry.topic,
                "content": entry.description,
                "entry_type": entry.entry_type,
                "date": entry.date,
                "file_reference": entry.file_reference,
            }
        )

        # Insert knowledge node
        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge_nodes (id, type, content, metadata, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (
                entry_id,
                category,
                structured_content,
                json.dumps(metadata),
            ),
        )

        # Create vector node for semantic search
        vector_id = f"vector_{entry_id}"
        vector_content = f"{entry.topic} {entry.description} {entry.entry_type}"

        cursor.execute(
            """
            INSERT OR REPLACE INTO vector_nodes (id, content, vector_id, model_name, metadata)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                vector_id,
                vector_content,
                vector_id,
                "neural_cache_ready",
                json.dumps({"source_entry_id": entry_id, "category": category}),
            ),
        )

        conn.commit()

    def migrate_from_skill_file(
        self,
        skill_file: Path,
        dry_run: bool = False,
    ) -> MigrationResult:
        """Full migration from SKILL.md file.

        Args:
            skill_file: Path to SKILL.md file
            dry_run: If True, parse but don't write

        Returns:
            MigrationResult with statistics

        """
        try:
            # Parse entries
            parser = NeuralCacheParser(skill_file)
            entries = parser.parse()
            stats = parser.get_stats()

            # Ingest entries
            result = self.ingest_entries(entries, dry_run=dry_run)

            # Add stats to result
            result.stats = {
                "total_entries": stats.total_entries,
                "entries_by_type": stats.entries_by_type,
                "entries_with_file_refs": stats.entries_with_file_refs,
                "date_range": stats.date_range,
            }

            result.message = (
                f"Migrated {result.ingested_count} entries, " f"{result.failed_count} failed"
            )

            return result

        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Migration failed: {e}",
                errors=[str(e)],
            )

    def get_db_stats(self) -> dict[str, Any]:
        """Get current CKS database statistics.

        Returns:
            Dictionary with database statistics

        """
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Count nodes by type
        cursor.execute("SELECT type, COUNT(*) FROM knowledge_nodes GROUP BY type")
        stats["nodes_by_type"] = dict(cursor.fetchall())

        # Total counts
        cursor.execute("SELECT COUNT(*) FROM knowledge_nodes")
        stats["total_knowledge_nodes"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vector_nodes")
        stats["total_vector_nodes"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM knowledge_edges")
        stats["total_relationships"] = cursor.fetchone()[0]

        # Count neural cache entries specifically
        cursor.execute("""
            SELECT COUNT(*) FROM knowledge_nodes
            WHERE json_extract(metadata, '$.source') = 'neural_cache'
        """)
        stats["neural_cache_entries"] = cursor.fetchone()[0] or 0

        return stats

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


def print_stats(stats: dict[str, Any]) -> None:
    """Print statistics in formatted way."""
    print("\n📊 CKS Database Statistics:")
    print(f"  Total Knowledge Nodes: {stats.get('total_knowledge_nodes', 0)}")
    print(f"  Total Vector Nodes: {stats.get('total_vector_nodes', 0)}")
    print(f"  Total Relationships: {stats.get('total_relationships', 0)}")
    print(f"  Neural Cache Entries: {stats.get('neural_cache_entries', 0)}")

    if stats.get("nodes_by_type"):
        print("\n  Nodes by Type:")
        for node_type, count in sorted(stats["nodes_by_type"].items()):
            print(f"    {node_type}: {count}")


def main() -> None:
    """CLI entry point."""
    import argparse

    # Default skill file path (at P:\\\\\\ root, not __csf)
    # PROJECT_ROOT is P:\\\\\\__csf, so we go to parent for P:\\\\\\
    default_skill = PROJECT_ROOT.parent / ".claude" / "skills" / "csf-integration" / "SKILL.md"

    parser = argparse.ArgumentParser(
        description="Migrate Neural Cache to CKS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be migrated
  python -m cks.integration.commands.neural_cache_migration --dry-run

  # Perform migration
  python -m cks.integration.commands.neural_cache_migration --migrate

  # Show database stats
  python -m cks.integration.commands.neural_cache_migration --stats

  # Use custom skill file
  python -m cks.integration.commands.neural_cache_migration --migrate --file custom.md
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and show what would be migrated without writing",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Perform the migration to CKS database",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show CKS database statistics",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=default_skill,
        help="Path to SKILL.md file (default: csf-integration/SKILL.md)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    migrator = NeuralCacheMigrator()

    try:
        if args.stats:
            stats = migrator.get_db_stats()
            print_stats(stats)

        elif args.dry_run or args.migrate:
            if not args.file.exists():
                logger.error(f"Skill file not found: {args.file}")
                sys.exit(1)

            result = migrator.migrate_from_skill_file(
                args.file,
                dry_run=args.dry_run,
            )

            if not result.success:
                logger.error(f"Migration failed: {result.message}")
                for error in result.errors:
                    logger.error(f"  - {error}")
                sys.exit(1)

            # Print results
            print(f"\n{'🔍 DRY RUN' if args.dry_run else '✅ MIGRATION COMPLETE'}")
            print(f"  Ingested: {result.ingested_count} entries")
            print(f"  Failed: {result.failed_count} entries")

            if result.stats:
                print("\n  Source Statistics:")
                print(f"    Total entries: {result.stats['total_entries']}")
                print(
                    f"    Date range: {result.stats['date_range'][0]} to {result.stats['date_range'][1]}"
                )
                print(f"    With file refs: {result.stats['entries_with_file_refs']}")

                if result.stats["entries_by_type"]:
                    print("\n    Entries by Type:")
                    for entry_type, count in sorted(result.stats["entries_by_type"].items()):
                        print(f"      {entry_type}: {count}")

            if result.categories:
                print("\n  Categories Created:")
                for cat, count in sorted(result.categories.items()):
                    print(f"    {cat}: {count}")

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)
    finally:
        migrator.close()


if __name__ == "__main__":
    main()
