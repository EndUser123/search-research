import sys
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""
CKS CLI - Cognitive Knowledge System Command Line Interface

Permanent interface for CKS hyper-graph operations across all sessions.
This is the entry point for all CKS interactions going forward.

Usage:
    python -m features.cks.cks_cli                # Interactive mode
    python -m features.cks.cks_cli stats          # Show system statistics
    python -m features.cks.cks_cli tdd            # Show TDD content
    python -m features.cks.cks_cli rebuild-index  # Rebuild compressed search index
    python -m features.cks.cks_cli backfill       # Generate embeddings for new entries
    python -m features.cks.cks_cli query X        # Search for X
    python -m features.cks.cks_cli session        # Extract lessons from current session
    python -m features.cks.cks_cli session <file> # Extract lessons from specific session file
"""


# CKS is already in the correct path structure
try:
    from .unified import CKS as UnifiedCKS
except ImportError:
    print("❌ CKS not found. Please ensure CKS is initialized.")
    sys.exit(1)

# Session lesson extractor
try:
    from .session_lesson_extractor import extract_session_lessons
except ImportError:
    print("❌ Session lesson extractor not found.")
    extract_session_lessons = None  # type: ignore[assignment]


class CKSCLI:
    """Command line interface for CKS system."""

    def __init__(self) -> None:
        self.cks = UnifiedCKS()
        self.connected = True  # Unified CKS connects automatically

    def connect(self) -> bool:
        """Connect to CKS."""
        print("✅ CKS System Connected!")
        print("🧠 Cognitive Knowledge System Ready")
        return True

    def show_statistics(self) -> dict[str, Any]:
        """Display CKS system statistics."""
        stats = self.cks.get_statistics()

        print("\n📊 CKS Statistics:")
        print("=" * 50)

        # Total entries
        total = stats.get("total_entries", 0)
        size_mb = stats.get("database_size_bytes", 0) / (1024 * 1024)
        print(f"\n📚 Total Entries: {total}")
        print(f"💾 Database Size: {size_mb:.2f} MB")

        # By type
        by_type = stats.get("by_type", {})
        if by_type:
            print("\n📋 Entries by Type:")
            for entry_type, count in sorted(by_type.items()):
                print(f"  - {entry_type}: {count}")

        return stats

    def query_tdd_content(self) -> list[dict[str, Any]]:
        """Query TDD-related content from csf.cks."""
        if not self.connected and not self.connect():
            return []

        repos = self.cks.get_tdd_repositories()
        patterns = self.cks.get_architecture_patterns()

        print("\n🔍 TDD Content Query Results:")
        print("=" * 50)

        print(f"\n📚 TDD Repositories ({len(repos)}):")
        for i, repo in enumerate(repos, 1):
            print(f"  {i}. {repo.get('name', 'Unknown')}")
            print(f"     {repo.get('description', 'No description')[:80]}...")

        print(f"\n🏗️ Architecture Patterns ({len(patterns)}):")
        for i, pattern in enumerate(patterns[:5], 1):
            print(f"  {i}. {pattern.get('name', 'Unknown')}")
            print(f"     {pattern.get('description', 'No description')[:80]}...")

        return {"repositories": repos, "patterns": patterns}

    def search(self, query: str, graph_type: str = "knowledge") -> list[dict[str, Any]]:
        """Search content across CKS."""
        print(f"\n🔍 Searching for: '{query}'")
        print("=" * 50)

        # Search using unified CKS
        results = self.cks.search(query, limit=10)
        print(f"📚 Found {len(results)} results:")

        for i, result in enumerate(results[:5], 1):
            entry_type = result.get("type", "unknown")
            title = result.get("title", "")
            content = result.get("content", result.get("answer", ""))
            display = f"{title}: {content[:80]}" if title else content[:100]
            print(f"\n  {i}. [{entry_type}] {display}...")

        return results

    def interactive_mode(self) -> None:
        """Interactive CKS query mode."""
        print("\n🎯 CKS Interactive Query Mode")
        print("=" * 50)
        print("Type 'help' for commands, 'quit' to exit")

        while True:
            try:
                user_input = input("\n🧠 CKS> ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break
                if user_input.lower() == "help":
                    self.show_help()
                elif user_input.lower() == "stats":
                    self.show_statistics()
                elif user_input.lower() == "tdd":
                    self.query_tdd_content()
                elif user_input.lower().startswith("rebuild-index"):
                    # Get optional entry type
                    parts = user_input.split()
                    entry_type = parts[1] if len(parts) > 1 else None
                    self.rebuild_index(entry_type)
                elif user_input.startswith("search "):
                    query = user_input[7:]  # Remove 'search '
                    self.search(query)
                elif user_input.startswith("add "):
                    content = user_input[4:]  # Remove 'add '
                    self.add_content(content)
                elif user_input.startswith("add --file "):
                    file_path = user_input[11:]  # Remove 'add --file '
                    self.add_from_file(file_path)
                else:
                    # Interactive query
                    result = self.cks.interactive_query(user_input)
                    print(f"\n💡 Result: {result[:300]}...")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def rebuild_index(self, entry_type: str | None = None) -> bool:
        """Rebuild the compressed IVF+PQ semantic search index.

        This command rebuilds the compressed index from the current database,
        incorporating any new entries added since the last build.

        Args:
            entry_type: Optional filter by entry type (e.g., 'memory', 'pattern', 'code')

        Returns:
            True if successful, False otherwise

        """
        print()
        print("\N{HAMMER} Rebuilding CKS Compressed Index")
        print("=" * 50)

        try:
            from cli.subprocess_helper import run_subprocess

            script_path = (
                Path(__file__).parent.parent.parent / "scripts" / "build_cks_compressed_rag.py"
            )

            if not script_path.exists():
                print(f"❌ Build script not found: {script_path}")
                return False

            cmd = [sys.executable, str(script_path)]
            if entry_type:
                cmd.extend(["--type", entry_type])

            print(f"Running: {' '.join(cmd)}")
            print()

            result = run_subprocess(cmd, capture_output=False, text=True)

            if result.returncode == 0:
                print()
                print("✅ Index rebuilt successfully!")
                print()
                print("Next steps:")
                print("  - Restart any CKS instances to use the new index")
                print("  - Semantic search will automatically use the updated index")
                return True
            print()
            print(f"❌ Index rebuild failed with exit code {result.returncode}")
            return False

        except Exception as e:
            print()
            print(f"❌ Error rebuilding index: {e}")
            import traceback

            traceback.print_exc()
            return False

    def backfill_embeddings(self, batch_size: int = 100) -> dict[str, int]:
        """Generate embeddings for entries that don't have them yet.

        Args:
            batch_size: Number of entries to process per batch

        Returns:
            Dictionary with counts: {total, backfilled, skipped, errors}

        """
        try:
            from .unified import CKS

            print("🔄 Initializing CKS for backfill...")
            cks_instance = CKS()

            print("🔄 Checking for entries without embeddings...")
            result = cks_instance.backfill_embeddings(batch_size=batch_size)

            print()
            print("📊 Backfill Results:")
            print(f"  - Total processed: {result.get('backfilled', 0)}")
            print(f"  - Already had embeddings: {result.get('skipped', 0)}")
            print(f"  - Errors: {result.get('errors', 0)}")

            if result.get("backfilled", 0) > 0:
                print()
                print("✅ Embeddings generated! Semantic search will now find these entries.")
            else:
                print()
                print("✅ All entries already have embeddings!")

            return result

        except Exception as e:
            print()
            print(f"❌ Error backfilling embeddings: {e}")
            import traceback

            traceback.print_exc()
            return {"total": 0, "backfilled": 0, "skipped": 0, "errors": 1}

    def extract_session(self, session_file: str | None = None) -> dict[str, Any]:
        """Extract lessons from Claude Code session and store in CKS.

        Analyzes the current session transcript (or a specific session file)
        and extracts learnings, insights, corrections, and patterns to store
        in the Constitutional Knowledge System.

        Args:
            session_file: Optional path to a specific session JSONL file.
                         If not provided, auto-detects the current session.

        Returns:
            Dictionary with extraction results including counts and errors.

        """
        if extract_session_lessons is None:
            print("❌ Session lesson extractor not available.")
            return {"error": "extractor_not_available", "lessons_extracted": 0, "lessons_stored": 0}

        print()
        print("🧠 Extracting Session Lessons")
        print("=" * 50)

        try:
            results = extract_session_lessons(session_file)

            if "error" in results:
                print(f"❌ {results['error']}")
                return results

            lessons_extracted = results.get("lessons_extracted", 0)
            lessons_stored = results.get("lessons_stored", 0)

            if lessons_stored > 0:
                print()
                print("✅ Session extraction complete!")
                print()
                print("Search your lessons with:")
                print('  python -m features.cks.cks_cli query "session learnings"')
                print('  /cks "<topic from session>"')
            else:
                print()
                print("ℹ️  No lessons found in this session.")

            return results

        except Exception as e:
            print()
            print(f"❌ Error extracting session lessons: {e}")
            import traceback

            traceback.print_exc()
            return {"error": str(e), "lessons_extracted": 0, "lessons_stored": 0}

    def detect_content_type(self, content: str) -> str:
        """Auto-detect content type based on patterns.

        Returns: One of: pattern, memory, code, decision, correction, insight, learning, knowledge
        """
        content_lower = content.lower()

        # Pattern: Contains "Results:", "Anti-pattern:", "%" metrics
        if any(
            kw in content_lower for kw in ["results:", "anti-pattern:", "metrics:", "benchmark:"]
        ):
            return "pattern"

        # Memory: Q&A format (What/How/Why/When/Where/Who questions)
        if any(
            content.strip().lower().startswith(q)
            for q in ["what ", "how ", "why ", "when ", "where ", "who "]
        ):
            return "memory"

        # Code: Contains function/class definitions
        if any(kw in content for kw in ["def ", "class ", "function ", "interface ", "type "]):
            return "code"

        # Decision: Choice/selection language
        if any(kw in content_lower for kw in ["decided to", "chose to", "selected", "choice:"]):
            return "decision"

        # Correction: Mistake/fix language
        if any(
            kw in content_lower for kw in ["fixed:", "correction:", "mistake:", "bug:", "resolved:"]
        ):
            return "correction"

        # Insight: Realization language
        if any(
            kw in content_lower for kw in ["realized:", "insight:", "discovered:", "found that:"]
        ):
            return "insight"

        # Learning: Lesson learned language
        if any(kw in content_lower for kw in ["learned:", "lesson:", "takeaway:", "next time:"]):
            return "learning"

        # Default: knowledge
        return "knowledge"

    def add_content(
        self,
        content: str,
        title: str | None = None,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """Add content to CKS with auto-detection of entry type.

        Args:
            content: The content to add
            title: Optional title (auto-generated if not provided)
            content_type: Optional content type (auto-detected if not provided)

        Returns:
            Dictionary with entry_id and status

        """
        print()
        print("➕ Adding to CKS")
        print("=" * 50)

        try:
            # Auto-detect type if not specified
            if content_type is None:
                content_type = self.detect_content_type(content)

            # Generate title if not provided
            if title is None:
                # Extract first line or truncate
                lines = content.strip().split("\n")
                first_line = lines[0][:80] if lines else content[:80]
                title = f"{content_type.capitalize()}: {first_line}"

            # Route to appropriate ingest method
            if content_type == "memory":
                # For memories, extract Q and A from content
                lines = content.strip().split("\n", 1)
                question = lines[0] if lines else title
                answer = lines[1] if len(lines) > 1 else content
                entry_id = self.cks.ingest_memory(question, answer)
            elif content_type == "pattern":
                entry_id = self.cks.ingest_pattern(title, content)
            elif content_type == "code":
                entry_id = self.cks.ingest_pattern(
                    title,
                    content,
                )  # Code stored as patterns for now
            elif content_type == "decision":
                entry_id = self.cks.ingest_decision(title, content)
            elif content_type == "correction":
                entry_id = self.cks.ingest_correction(title, content)
            elif content_type == "insight":
                entry_id = self.cks.ingest_insight(title, content)
            elif content_type == "learning":
                entry_id = self.cks.ingest_learning(title, content)
            else:
                # Default to knowledge (use pattern as generic container)
                entry_id = self.cks.ingest_pattern(title, content)

            print()
            print(f"✅ Added as [{content_type}]: {entry_id}")
            print()
            print("Search it with:")
            print(f'  python -m features.cks.cks_cli query "{title[:50]}"')
            print(f'  /cks "{title[:50]}"')

            return {"entry_id": entry_id, "type": content_type, "title": title}

        except Exception as e:
            print()
            print(f"❌ Error adding content: {e}")
            import traceback

            traceback.print_exc()
            return {"error": str(e)}

    def add_from_file(self, file_path: str) -> dict[str, Any]:
        """Add content from a file to CKS.

        Args:
            file_path: Path to the file to read

        Returns:
            Dictionary with entry_id and status

        """
        path = Path(file_path)

        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return {"error": "file_not_found", "path": file_path}

        try:
            content = path.read_text(encoding="utf-8")
            title = path.stem  # Filename without extension
            return self.add_content(content, title=title)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return {"error": str(e), "path": file_path}

    def show_help(self) -> None:
        """Display help information."""
        print("\n📖 CKS Commands:")
        print("  help              - Show this help")
        print("  stats             - Display system statistics")
        print("  tdd               - Show TDD-related content")
        print("  rebuild-index     - Rebuild compressed semantic search index")
        print("  rebuild-index X   - Rebuild index for entry type X (e.g., memory)")
        print("  backfill          - Generate embeddings for entries without them")
        print("  session           - Extract lessons from current session")
        print("  session <file>    - Extract lessons from specific session file")
        print("  search X          - Search for X across graphs")
        print("  query             - Interactive natural language query")
        print('  add "content"     - Add content to CKS (auto-detects type)')
        print("  add --file X      - Add content from file X")
        print("  quit              - Exit interactive mode")


def main() -> None:
    """Main entry point."""
    cks = CKSCLI()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "stats":
            cks.show_statistics()
        elif command == "tdd":
            cks.query_tdd_content()
        elif command == "rebuild-index":
            entry_type = sys.argv[2] if len(sys.argv) > 2 else None
            cks.rebuild_index(entry_type)
        elif command == "backfill":
            cks.backfill_embeddings()
        elif command == "session":
            session_file = sys.argv[2] if len(sys.argv) > 2 else None
            cks.extract_session(session_file)
        elif command == "query" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            cks.search(query)
        elif command == "add" and len(sys.argv) > 2:
            # Handle add command
            if sys.argv[2] == "--file" and len(sys.argv) > 3:
                # /cks add --file <path>
                file_path = sys.argv[3]
                cks.add_from_file(file_path)
            else:
                # /cks add "content"
                content = " ".join(sys.argv[2:])
                cks.add_content(content)
        else:
            print("Usage:")
            print("  python -m features.cks.cks_cli                 # Interactive mode")
            print("  python -m features.cks.cks_cli stats            # Show statistics")
            print("  python -m features.cks.cks_cli tdd              # Show TDD content")
            print("  python -m features.cks.cks_cli rebuild-index    # Rebuild search index")
            print("  python -m features.cks.cks_cli rebuild-index X  # Rebuild for entry type X")
            print(
                "  python -m features.cks.cks_cli backfill         # Generate embeddings for new entries",
            )
            print(
                "  python -m features.cks.cks_cli session          # Extract lessons from current session",
            )
            print(
                "  python -m features.cks.cks_cli session <file>   # Extract lessons from session file",
            )
            print("  python -m features.cks.cks_cli query X          # Search for X")
            print('  python -m features.cks.cks_cli add "content"    # Add content to CKS')
            print("  python -m features.cks.cks_cli add --file X     # Add file to CKS")
    else:
        # Interactive mode
        cks.interactive_mode()


if __name__ == "__main__":
    main()
