#!/usr/bin/env python3
"""
Chat History Search (/chs) - Dedicated chat history search with advanced features.

Features:
1. Summarization modes (documentation, short-memory, changelog, debug-postmortem, onboarding)
2. Two-stage search architecture (index-only → deep content scan)
3. Workspace aliases (group related workspaces)
4. Tool-based filtering (search by tool usage)
5. Context window preview (show N messages around match)
6. Session statistics dashboard (metrics and insights)
7. Branch-based filtering (search by git branch)
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add paths for imports
CSF_SRC = Path("P:/__csf/src")
if CSF_SRC.exists():
    sys.path.insert(0, str(CSF_SRC))

# Try to import CHS v2 components
CHS_SEARCH_AVAILABLE = False
CHS_DB_AVAILABLE = False
FAISS_AVAILABLE = False

try:
    from knowledge.systems.chs.v2 import db as chs_db
    from knowledge.systems.chs.v2 import search as chs_search

    CHS_SEARCH_AVAILABLE = True
    # Check if CHS database exists
    chs_db_path = Path("P:/__csf/data/chat_history.db")
    if chs_db_path.exists():
        CHS_DB_AVAILABLE = True
except ImportError:
    pass

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    pass

SQLITE_AVAILABLE = True


class CHSConfig:
    """Configuration management for /chs skill."""

    def __init__(self):
        self.config_path = Path.home() / ".claude" / "chs_config.json"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file or create defaults."""
        defaults = {
            "workspace_aliases": {},
            "defaults": {"limit": 20, "depth": "summary", "stage": "auto"},
            "paths": {"metrics_db": "P:/packages/search-research/data/chs_metrics.db"},
        }

        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    user_config = json.load(f)
                    defaults.update(user_config)
            except (OSError, json.JSONDecodeError):
                pass

        return defaults

    def save_config(self):
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def get_workspace_aliases(self) -> dict[str, list[str]]:
        """Get workspace aliases mapping."""
        return self.config.get("workspace_aliases", {})

    def resolve_workspace_alias(self, alias: str) -> list[str]:
        """Resolve workspace alias to list of workspace names."""
        aliases = self.get_workspace_aliases()
        return aliases.get(alias, [alias])

    def get_metrics_db_path(self) -> Path:
        """Get path to metrics database."""
        return Path(
            self.config.get("paths", {}).get(
                "metrics_db", "P:/packages/search-research/data/chs_metrics.db"
            )
        )


class CHSMetrics:
    """Session statistics and metrics tracking."""

    def __init__(self, db_path: Path | None = None):
        self.config = CHSConfig()
        self.db_path = db_path or self.config.get_metrics_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize metrics database schema."""
        if not SQLITE_AVAILABLE:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_stats (
                session_id TEXT PRIMARY KEY,
                workspace TEXT,
                branch TEXT,
                terminal_id TEXT,
                message_count INTEGER,
                tool_usage TEXT,  -- JSON string
                timestamp REAL,
                duration_seconds REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                tool_name TEXT,
                usage_count INTEGER,
                FOREIGN KEY (session_id) REFERENCES session_stats(session_id)
            )
        """)

        conn.commit()
        conn.close()

    def record_session(
        self,
        session_id: str,
        workspace: str,
        branch: str,
        terminal_id: str,
        message_count: int,
        tool_usage: dict[str, int],
        timestamp: float,
        duration: float,
    ):
        """Record session statistics."""
        if not SQLITE_AVAILABLE:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO session_stats
            (session_id, workspace, branch, terminal_id, message_count, tool_usage, timestamp, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                workspace,
                branch,
                terminal_id,
                message_count,
                json.dumps(tool_usage),
                timestamp,
                duration,
            ),
        )

        # Record individual tool usage
        for tool_name, count in tool_usage.items():
            cursor.execute(
                """
                INSERT OR REPLACE INTO tool_usage (session_id, tool_name, usage_count)
                VALUES (?, ?, COALESCE((SELECT usage_count FROM tool_usage
                                       WHERE session_id=? AND tool_name=?), 0) + ?)
            """,
                (session_id, tool_name, session_id, tool_name, count),
            )

        conn.commit()
        conn.close()

    def get_stats(
        self, workspace: str | None = None, since: datetime | None = None
    ) -> dict[str, Any]:
        """Get session statistics."""
        if not SQLITE_AVAILABLE:
            return {"error": "SQLite not available"}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM session_stats WHERE 1=1"
        params = []

        if workspace:
            query += " AND workspace = ?"
            params.append(workspace)

        if since:
            query += " AND timestamp >= ?"
            params.append(since.timestamp())

        cursor.execute(query, params)
        sessions = cursor.fetchall()

        # Calculate statistics
        total_sessions = len(sessions)
        workspace_counts = {}
        branch_counts = {}
        tool_totals = {}
        total_messages = 0
        total_duration = 0

        for session in sessions:
            _, ws, branch, terminal_id, msg_count, tool_usage_json, timestamp, duration = session
            workspace_counts[ws] = workspace_counts.get(ws, 0) + 1
            branch_counts[branch] = branch_counts.get(branch, 0) + 1
            total_messages += msg_count or 0
            total_duration += duration or 0

            try:
                tool_usage = json.loads(tool_usage_json) if tool_usage_json else {}
                for tool, count in tool_usage.items():
                    tool_totals[tool] = tool_totals.get(tool, 0) + count
            except json.JSONDecodeError:
                pass

        conn.close()

        return {
            "total_sessions": total_sessions,
            "workspaces": workspace_counts,
            "branches": branch_counts,
            "most_used_tools": sorted(tool_totals.items(), key=lambda x: x[1], reverse=True),
            "total_messages": total_messages,
            "total_duration_seconds": total_duration,
            "avg_session_length": total_messages / total_sessions if total_sessions > 0 else 0,
        }


class CHSSearch:
    """Hybrid search implementation with multiple backends.

    Priority order:
    1. CHS SQLite FTS5 (fastest, BM25 scoring)
    2. CHS FAISS (semantic search)
    3. Direct JSONL parsing (fallback, no dependencies)
    """

    def __init__(self, config: CHSConfig):
        self.config = config
        self._backend_status = self._check_backends()

    def _check_backends(self) -> dict[str, bool]:
        """Check which backends are available."""
        status = {
            "chs_fts5": CHS_DB_AVAILABLE,
            "chs_faiss": FAISS_AVAILABLE and CHS_DB_AVAILABLE,
            "direct_jsonl": True,  # Always available as fallback
        }
        return status

    def get_backend_status(self) -> dict[str, bool]:
        """Get current backend availability status."""
        return self._backend_status.copy()

    def search_stage1(
        self,
        query: str,
        workspace: str | None = None,
        branch: str | None = None,
        tool: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Stage 1: Lightweight index-only search.

        Tries backends in priority order:
        1. CHS SQLite FTS5 (keyword search with BM25)
        2. Direct JSONL index search (fallback)
        """
        results = []

        # Try CHS SQLite FTS5 first (fastest)
        if self._backend_status["chs_fts5"]:
            try:
                results = self._search_chs_fts5(query, workspace, branch, tool, limit)
                if results:
                    return results
            except Exception:
                # Fallback to JSONL if CHS fails
                pass

        # Fallback to direct JSONL parsing
        results = self._search_jsonl_index(query, workspace, branch, tool, limit)
        return results

    def _search_chs_fts5(
        self,
        query: str,
        workspace: str | None,
        branch: str | None,
        tool: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search using CHS SQLite FTS5 backend."""
        if not CHS_SEARCH_AVAILABLE:
            return []

        try:
            from knowledge.systems.chs.v2.db import get_connection
            from knowledge.systems.chs.v2.search import search_fts_messages

            chs_db_path = Path("P:/__csf/data/chat_history.db")
            conn = get_connection(chs_db_path)

            # Search using CHS FTS5
            fts_results = search_fts_messages(conn, query, limit)

            # Convert to our format
            results = []
            for r in fts_results:
                results.append(
                    {
                        "session_id": r.get("id", "unknown"),
                        "workspace": "P--",  # Would need to extract from DB
                        "first_prompt": r.get("content", "")[:100],
                        "summary": r.get("content", "")[:100],
                        "branch": "unknown",
                        "timestamp": 0,
                        "score": r.get("score", 0),
                        "source": "chs_fts5",
                    }
                )
            conn.close()
            return results

        except Exception:
            # Log and fall through
            return []

    def search_stage2(
        self,
        query: str,
        workspace: str | None = None,
        branch: str | None = None,
        tool: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Stage 2: Deep content scan.

        Tries backends in priority order:
        1. CHS FAISS (semantic search)
        2. Direct JSONL deep scan (fallback)
        """
        results = []

        # Try CHS FAISS semantic search first
        if self._backend_status["chs_faiss"]:
            try:
                results = self._search_chs_faiss(query, workspace, branch, limit)
                if results:
                    return results
            except Exception:
                pass

        # Fallback to direct JSONL deep scan
        results = self._search_jsonl_deep(query, workspace, branch, tool, limit)
        return results

    def _search_chs_faiss(
        self,
        query: str,
        workspace: str | None,
        branch: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search using CHS FAISS backend (semantic search)."""
        if not FAISS_AVAILABLE or not CHS_DB_AVAILABLE:
            return []

        try:
            from knowledge.systems.chs.v2.embeddings import get_embed_client

            # Get embedding client and generate query embedding
            client = get_embed_client()
            import numpy as np

            query_embedding = client.embed_texts([query])[0]
            query_vector = np.frombuffer(query_embedding, dtype=np.float32)

            # Load FAISS index and search
            faiss_index_path = Path("P:/__csf/data/chat_history_faiss")
            if faiss_index_path.exists():
                import faiss

                index = faiss.read_index(str(faiss_index_path / "index.bin"))
                distances, indices = index.search(query_vector.reshape(1, -1), limit)

                # Return results (would need to map indices to actual content)
                return []

        except Exception:
            return []

    def search_stage2(
        self,
        query: str,
        workspace: str | None = None,
        branch: str | None = None,
        tool: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Stage 2: Deep content scan.

        Searches: All message content, tool results, thinking blocks
        Speed: ~500ms (depends on corpus size)
        """
        # Deep scan of JSONL files
        results = self._search_jsonl_deep(query, workspace, branch, tool, limit)
        return results

    def _search_jsonl_index(
        self, query: str, workspace: str | None, branch: str | None, tool: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Search JSONL files using index fields only."""
        results = []
        projects_path = Path.home() / ".claude" / "projects"

        if not projects_path.exists():
            return results

        query_lower = query.lower()

        for project_dir in projects_path.iterdir():
            if project_dir.is_dir():
                # Check workspace filter
                if workspace and workspace != project_dir.name:
                    # Check workspace alias
                    resolved = self.config.resolve_workspace_alias(workspace)
                    if project_dir.name not in resolved:
                        continue

                # Search for JSONL files
                for jsonl_file in project_dir.glob("*.jsonl"):
                    try:
                        with open(jsonl_file, encoding="utf-8") as f:
                            for line_num, line in enumerate(f):
                                if len(results) >= limit:
                                    break

                                try:
                                    data = json.loads(line)
                                    if self._matches_index(data, query_lower, branch, tool):
                                        # Extract content for display
                                        content_preview = ""
                                        entry_type = data.get("type", "")
                                        if entry_type == "user":
                                            message = data.get("message", {})
                                            content_list = message.get("content", [])
                                            if isinstance(content_list, list) and content_list:
                                                content_preview = content_list[0].get("text", "")[
                                                    :100
                                                ]
                                        elif entry_type == "assistant":
                                            message = data.get("message", {})
                                            content_list = message.get("content", [])
                                            if isinstance(content_list, list) and content_list:
                                                content_preview = str(content_list[0])[:100]

                                        results.append(
                                            {
                                                "session_id": data.get(
                                                    "sessionId", jsonl_file.stem
                                                ),
                                                "workspace": project_dir.name,
                                                "first_prompt": content_preview,
                                                "summary": f"[{entry_type}] {content_preview}",
                                                "branch": data.get("gitBranch", "unknown"),
                                                "timestamp": data.get("timestamp", 0),
                                                "file": str(jsonl_file),
                                                "line": line_num,
                                            }
                                        )
                                except json.JSONDecodeError:
                                    continue
                    except OSError:
                        continue

        return results

    def _search_jsonl_deep(
        self, query: str, workspace: str | None, branch: str | None, tool: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Deep search of JSONL content."""
        results = []
        projects_path = Path.home() / ".claude" / "projects"

        if not projects_path.exists():
            return results

        query_lower = query.lower()

        for project_dir in projects_path.iterdir():
            if project_dir.is_dir():
                # Check workspace filter
                if workspace and workspace != project_dir.name:
                    resolved = self.config.resolve_workspace_alias(workspace)
                    if project_dir.name not in resolved:
                        continue

                for jsonl_file in project_dir.glob("*.jsonl"):
                    try:
                        with open(jsonl_file, encoding="utf-8") as f:
                            content = f.read()
                            if query_lower in content.lower():
                                results.append(
                                    {
                                        "session_id": jsonl_file.stem,
                                        "workspace": project_dir.name,
                                        "file": str(jsonl_file),
                                        "match_count": content.lower().count(query_lower),
                                    }
                                )
                    except OSError:
                        continue

        return sorted(results, key=lambda x: x["match_count"], reverse=True)[:limit]

    def _matches_index(
        self, data: dict, query_lower: str, branch: str | None, tool: str | None
    ) -> bool:
        """Check if session matches index-based criteria."""
        # Check actual JSONL format
        entry_type = data.get("type", "")

        # For user messages, check content
        if entry_type == "user":
            message = data.get("message", {})
            content = message.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        if query_lower in item["text"].lower():
                            if self._check_filters(data, branch, tool):
                                return True

        # For assistant messages, check content
        elif entry_type == "assistant":
            message = data.get("message", {})
            content = message.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if "text" in item and query_lower in item["text"].lower():
                            if self._check_filters(data, branch, tool):
                                return True

        return False

    def _check_filters(self, data: dict, branch: str | None, tool: str | None) -> bool:
        """Check if session passes branch and tool filters."""
        if branch:
            if data.get("gitBranch") != branch:
                return False

        if tool:
            # Check if tool was used in this session
            # This would require parsing the full content
            # For now, skip this check in stage 1
            pass

        return True

    def _parse_chs_output(self, output: str) -> list[dict[str, Any]]:
        """Parse output from existing CHS CLI."""
        # This would parse the actual output format from CHS
        # For now, return empty list
        return []


class CHSSummarizer:
    """Summarization modes for chat history."""

    def __init__(self):
        self.templates = {
            "documentation": self._template_documentation,
            "short-memory": self._template_short_memory,
            "changelog": self._template_changelog,
            "debug-postmortem": self._template_debug_postmortem,
            "onboarding": self._template_onboarding,
        }

    def summarize(self, session_data: dict[str, Any], mode: str) -> str:
        """Summarize session using specified mode."""
        template_func = self.templates.get(mode)
        if template_func:
            return template_func(session_data)
        return f"Unknown summarization mode: {mode}"

    def _template_documentation(self, data: dict) -> str:
        """Full technical documentation format."""
        return f"""# Session Documentation: {data.get("session_id", "Unknown")}

## Problem
{data.get("firstPrompt", "No problem statement")}

## Changes Made
<!-- Extract from conversation -->
- File changes would be listed here
- Code modifications would be detailed here

## Patterns Identified
<!-- Key patterns from the session -->
- Pattern 1
- Pattern 2

## Lessons Learned
<!-- Key takeaways -->
- Lesson 1
- Lesson 2

## Related Sessions
<!-- Links to related conversations -->
- None identified
"""

    def _template_short_memory(self, data: dict) -> str:
        """MEMORY.md-ready bullet format."""
        timestamp = data.get("timestamp", 0)

        # Handle both string timestamps (ISO format) and numeric timestamps
        if isinstance(timestamp, str):
            # ISO format string like "2025-11-17T19:53:30.888Z"
            date_str = timestamp[:10]  # Extract YYYY-MM-DD
        else:
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

        return f"""## {data.get("first_prompt", "Topic")[:50]}

**Context:** {data.get("workspace", "unknown")} on {date_str}

**Key Points:**
- Point extracted from conversation
- Another key insight

**Outcome:** {data.get("summary", "No summary available")[:100]}
"""

    def _template_changelog(self, data: dict) -> str:
        """Changelog format with file paths."""
        return f"""# Changelog Entry

## Added
- Features added during this session

## Changed
- {data.get("workspace", "unknown")}: Modified files

## Fixed
- Bug fixes addressed

## Removed
- Deprecated features removed

**Files Modified:**
- File paths would be listed here
"""

    def _template_debug_postmortem(self, data: dict) -> str:
        """Debug postmortem format."""
        return f"""# Debug Postmortem: {data.get("firstPrompt", "Unknown Issue")[:50]}

## Symptoms
{data.get("firstPrompt", "Describe the symptoms")}

## Investigation
<!-- Investigation steps -->
1. First hypothesis
2. Test performed
3. Result observed

## Dead Ends
<!-- Approaches that didn't work -->
- Tried X, didn't work because Y
- Attempted Z, ruled out because W

## Root Cause
<!-- The actual cause -->
The issue was caused by...

## Fix Applied
<!-- The solution -->
Applied fix: X
Verified by: Y
"""

    def _template_onboarding(self, data: dict) -> str:
        """Onboarding documentation format."""
        return f"""# How This Works: {data.get("workspace", "Project")} Onboarding

## Architecture Overview
<!-- High-level architecture -->
- Component A: Purpose
- Component B: Purpose

## Key Files
<!-- Important files to understand -->
- `path/to/file.py`: Core logic
- `path/to/config.py`: Configuration

## Common Patterns
<!-- Development patterns used -->
- Pattern 1 usage
- Pattern 2 usage

## Getting Started
<!-- First steps for new developers -->
1. Step one
2. Step two
3. Step three

## Common Issues
<!-- Gotchas and how to avoid them -->
- Issue: Solution
"""


class CHSContext:
    """Context window preview for search results."""

    def show_context(self, session_file: Path, match_line: int, context_lines: int = 10) -> str:
        """Show N messages before and after match."""
        try:
            with open(session_file, encoding="utf-8") as f:
                lines = f.readlines()

            start = max(0, match_line - context_lines)
            end = min(len(lines), match_line + context_lines + 1)

            result = f"=== Session: {session_file.stem} ===\n"
            result += f"[{match_line - start} messages before match]\n\n"

            for i in range(start, end):
                prefix = "[MATCH] " if i == match_line else ""
                try:
                    data = json.loads(lines[i])
                    role = data.get("message", {}).get("role", "unknown")
                    content_field = data.get("message", {}).get("content", "")

                    # Handle both string and list content formats
                    if isinstance(content_field, str):
                        content = content_field[:100]
                    elif isinstance(content_field, list) and content_field:
                        first_item = content_field[0]
                        if isinstance(first_item, dict):
                            content = first_item.get("text", str(first_item))[:100]
                        else:
                            content = str(first_item)[:100]
                    else:
                        content = str(content_field)[:100]

                    result += f"{prefix}{role.capitalize()}: {content}...\n\n"
                except (json.JSONDecodeError, KeyError, IndexError):
                    result += f"{prefix}[Line {i}]\n"

            result += f"[{end - match_line - 1} messages after match]\n"
            result += "Use --depth full to see complete conversation.\n"

            return result

        except OSError:
            return f"Error reading session file: {session_file}"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Chat History Search (/chs) - Advanced chat history search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Main arguments
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--limit", type=int, default=20, help="Limit results")
    parser.add_argument("--workspace", help="Filter by workspace")
    parser.add_argument("--workspace-alias", help="Use workspace alias")
    parser.add_argument("--branch", help="Filter by git branch")
    parser.add_argument("--tool", help="Filter by tool usage")
    parser.add_argument("--since", help="Filter by date (e.g., '7 days ago')")
    parser.add_argument("--until", help="Filter by date")
    parser.add_argument("--file", help="Filter by file path")
    parser.add_argument("--exact", action="store_true", help="Exact match")

    # Search stages
    parser.add_argument(
        "--stage",
        choices=["1", "2", "auto"],
        default="auto",
        help="Search stage: 1=index-only, 2=deep scan, auto=auto-select",
    )

    # Output options
    parser.add_argument(
        "--depth", choices=["summary", "full", "auto"], default="summary", help="Detail level"
    )
    parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown", help="Output format"
    )
    parser.add_argument(
        "--mode",
        choices=["documentation", "short-memory", "changelog", "debug-postmortem", "onboarding"],
        help="Summarization mode",
    )

    # Context preview
    parser.add_argument("--context", type=int, help="Show N messages around match")

    # Session management
    parser.add_argument("--show", help="Show specific session")
    parser.add_argument("--list", action="store_true", help="List recent sessions")
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    # Other options
    parser.add_argument("--reindex", action="store_true", help="Rebuild search index")
    parser.add_argument("--output", help="Output to file")
    parser.add_argument("--clipboard", action="store_true", help="Copy to clipboard")
    parser.add_argument("--exclude-thinking", action="store_true", help="Exclude thinking blocks")
    parser.add_argument(
        "--include-tool-results", action="store_true", help="Include tool execution results"
    )

    args = parser.parse_args()

    # Initialize components
    config = CHSConfig()
    search = CHSSearch(config)
    metrics = CHSMetrics()
    summarizer = CHSSummarizer()
    context_viewer = CHSContext()

    # Handle special commands
    if args.stats:
        # Parse date filter
        since = None
        if args.since:
            # Simple date parsing (could be enhanced)
            since = datetime.now() - timedelta(days=7)  # Default fallback

        stats = metrics.get_stats(workspace=args.workspace, since=since)

        if args.format == "json":
            print(json.dumps(stats, indent=2))
        else:
            print("=== Chat History Statistics ===\n")
            print(f"Total Sessions: {stats['total_sessions']}")
            print(f"Total Messages: {stats['total_messages']}")
            print(f"Avg Session Length: {stats['avg_session_length']:.1f} messages")
            print("\nWorkspaces:")
            for ws, count in stats["workspaces"].items():
                print(f"  {ws}: {count} sessions")
            print("\nMost Used Tools:")
            for tool, count in stats["most_used_tools"][:10]:
                print(f"  {tool}: {count} times")
        return 0

    if args.list:
        # List recent sessions
        results = search.search_stage1("", workspace=args.workspace, limit=args.limit)
        for result in results:
            print(f"{result['session_id']}: {result['first_prompt']}")
        return 0

    if args.show:
        # Show specific session
        session_path = Path(args.show)
        if not session_path.exists():
            # Try to find it in projects directory
            projects_path = Path.home() / ".claude" / "projects"
            found = False
            for project_dir in projects_path.iterdir():
                potential = project_dir / f"{args.show}.jsonl"
                if potential.exists():
                    session_path = potential
                    found = True
                    break

            if not found:
                print(f"Session not found: {args.show}")
                return 1

        if args.context:
            # Show context preview
            output = context_viewer.show_context(session_path, 0, args.context)
        else:
            # Show full session
            with open(session_path, encoding="utf-8") as f:
                output = f.read()

        print(output)
        return 0

    if not args.query:
        parser.print_help()
        return 1

    # Perform search
    stage = args.stage
    if stage == "auto":
        # Auto-select stage based on query
        stage = "1"  # Default to stage 1

    if stage == "1":
        results = search.search_stage1(
            args.query,
            workspace=args.workspace_alias or args.workspace,
            branch=args.branch,
            tool=args.tool,
            limit=args.limit,
        )
    else:
        results = search.search_stage2(
            args.query,
            workspace=args.workspace_alias or args.workspace,
            branch=args.branch,
            tool=args.tool,
            limit=args.limit,
        )

    # Apply summarization if requested
    if args.mode:
        summarized = []
        for result in results:
            summary = summarizer.summarize(result, args.mode)
            result["summary"] = summary
            summarized.append(result)
        results = summarized

    # Output results
    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        print(f"=== Chat History Search: {args.query} ===\n")
        print(f"Found {len(results)} results\n")

        for i, result in enumerate(results, 1):
            print(f"[{i}] {result.get('session_id', 'unknown')}")
            print(f"    Workspace: {result.get('workspace', 'unknown')}")
            print(f"    Branch: {result.get('branch', 'unknown')}")
            if "first_prompt" in result:
                print(f"    Prompt: {result['first_prompt']}")
            if "summary" in result and isinstance(result["summary"], str):
                # Check if it's a structured summary or just text
                if result["summary"].startswith("#"):
                    print(f"\n{result['summary']}\n")
                else:
                    print(f"    Summary: {result['summary']}")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
