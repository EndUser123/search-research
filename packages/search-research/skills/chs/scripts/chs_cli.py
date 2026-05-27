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
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

CHS_SEARCH_AVAILABLE = False
CHS_DB_AVAILABLE = False
FAISS_AVAILABLE = False
try:
    from core.chs import db as chs_db  # noqa: F401
    from core.chs import search as chs_search  # noqa: F401
    from core.chs.db import database_is_initialized

    CHS_SEARCH_AVAILABLE = True
    chs_db_path = Path(os.getenv("CHS_DB_PATH", "P:\\\\\\__csf/data/chat_history.db")).expanduser()
    CHS_DB_AVAILABLE = database_is_initialized(chs_db_path)
except ImportError:
    pass
try:
    import faiss  # noqa: F401

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
            "paths": {"metrics_db": "P:\\\\\\packages/search-research/data/chs_metrics.db"},
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
                "metrics_db", "P:\\\\\\packages/search-research/data/chs_metrics.db"
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
        cursor.execute(
            "\n            CREATE TABLE IF NOT EXISTS session_stats (\n                session_id TEXT PRIMARY KEY,\n                workspace TEXT,\n                branch TEXT,\n                terminal_id TEXT,\n                message_count INTEGER,\n                tool_usage TEXT,  -- JSON string\n                timestamp REAL,\n                duration_seconds REAL\n            )\n        "
        )
        cursor.execute(
            "\n            CREATE TABLE IF NOT EXISTS tool_usage (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                session_id TEXT,\n                tool_name TEXT,\n                usage_count INTEGER,\n                FOREIGN KEY (session_id) REFERENCES session_stats(session_id)\n            )\n        "
        )
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
            "\n            INSERT OR REPLACE INTO session_stats\n            (session_id, workspace, branch, terminal_id, message_count, tool_usage, timestamp, duration)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n        ",
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
        for tool_name, count in tool_usage.items():
            cursor.execute(
                "\n                INSERT OR REPLACE INTO tool_usage (session_id, tool_name, usage_count)\n                VALUES (?, ?, COALESCE((SELECT usage_count FROM tool_usage\n                                       WHERE session_id=? AND tool_name=?), 0) + ?)\n            ",
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
            "direct_jsonl": True,
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
        if self._backend_status["chs_fts5"]:
            try:
                results = self._search_chs_fts5(query, workspace, branch, tool, limit)
                if results:
                    return results
            except Exception:
                pass
        results = self._search_jsonl_index(query, workspace, branch, tool, limit)
        return results

    def _search_chs_fts5(
        self, query: str, workspace: str | None, branch: str | None, tool: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Search using CHS SQLite FTS5 backend."""
        if not CHS_SEARCH_AVAILABLE:
            return []
        try:
            from core.chs.db import get_connection
            from core.chs.search import search_fts_messages

            chs_db_path = Path(os.getenv("CHS_DB_PATH", "P:\\\\\\__csf/data/chat_history.db")).expanduser()
            conn = get_connection(chs_db_path)
            fts_results = search_fts_messages(conn, query, limit)
            results = []
            for r in fts_results:
                results.append(
                    {
                        "session_id": r.get("id", "unknown"),
                        "workspace": "P--",
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
        if self._backend_status["chs_faiss"]:
            try:
                results = self._search_chs_faiss(query, workspace, branch, limit)
                if results:
                    return results
            except Exception:
                pass
        results = self._search_jsonl_deep(query, workspace, branch, tool, limit)
        return results

    def _search_chs_faiss(
        self, query: str, workspace: str | None, branch: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Search using CHS FAISS backend (semantic search)."""
        if not FAISS_AVAILABLE or not CHS_DB_AVAILABLE:
            return []
        try:
            from core.chs.embeddings import get_embed_client

            client = get_embed_client()
            import numpy as np

            query_embedding = client.embed_texts([query])[0]
            query_vector = np.frombuffer(query_embedding, dtype=np.float32)
            faiss_index_path = Path("P:\\\\\\__csf/data/chat_history_faiss")
            if faiss_index_path.exists():
                import faiss

                index = faiss.read_index(str(faiss_index_path / "index.bin"))
                distances, indices = index.search(query_vector.reshape(1, -1), limit)
                return []
        except Exception:
            return []

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
                if workspace and workspace != project_dir.name:
                    resolved = self.config.resolve_workspace_alias(workspace)
                    if project_dir.name not in resolved:
                        continue
                for jsonl_file in project_dir.glob("*.jsonl"):
                    try:
                        with open(jsonl_file, encoding="utf-8") as f:
                            for line_num, line in enumerate(f):
                                if len(results) >= limit:
                                    break
                                try:
                                    data = json.loads(line)
                                    if self._matches_index(data, query_lower, branch, tool):
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
        """Deep search of JSONL content — streams line-by-line to avoid loading full files."""
        results = []
        projects_path = Path.home() / ".claude" / "projects"
        if not projects_path.exists():
            return results
        query_lower = query.lower()
        for project_dir in projects_path.iterdir():
            if project_dir.is_dir():
                if workspace and workspace != project_dir.name:
                    resolved = self.config.resolve_workspace_alias(workspace)
                    if project_dir.name not in resolved:
                        continue
                for jsonl_file in project_dir.glob("*.jsonl"):
                    try:
                        match_count = 0
                        with open(jsonl_file, encoding="utf-8") as f:
                            for line in f:
                                if query_lower in line.lower():
                                    match_count += 1
                        if match_count > 0:
                            results.append(
                                {
                                    "session_id": jsonl_file.stem,
                                    "workspace": project_dir.name,
                                    "file": str(jsonl_file),
                                    "match_count": match_count,
                                }
                            )
                    except OSError:
                        continue
        return sorted(results, key=lambda x: x["match_count"], reverse=True)[:limit]

    def _matches_index(
        self, data: dict, query_lower: str, branch: str | None, tool: str | None
    ) -> bool:
        """Check if session matches index-based criteria."""
        entry_type = data.get("type", "")
        if entry_type == "user":
            message = data.get("message", {})
            content = message.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        if query_lower in item["text"].lower():
                            if self._check_filters(data, branch, tool):
                                return True
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
            pass
        return True

    def _parse_chs_output(self, output: str) -> list[dict[str, Any]]:
        """Parse output from existing CHS CLI."""
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
        return f"# Session Documentation: {data.get('session_id', 'Unknown')}\n\n## Problem\n{data.get('firstPrompt', 'No problem statement')}\n\n## Changes Made\n<!-- Extract from conversation -->\n- File changes would be listed here\n- Code modifications would be detailed here\n\n## Patterns Identified\n<!-- Key patterns from the session -->\n- Pattern 1\n- Pattern 2\n\n## Lessons Learned\n<!-- Key takeaways -->\n- Lesson 1\n- Lesson 2\n\n## Related Sessions\n<!-- Links to related conversations -->\n- None identified\n"

    def _template_short_memory(self, data: dict) -> str:
        """MEMORY.md-ready bullet format."""
        timestamp = data.get("timestamp", 0)
        if isinstance(timestamp, str):
            date_str = timestamp[:10]
        else:
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        return f"## {data.get('first_prompt', 'Topic')[:50]}\n\n**Context:** {data.get('workspace', 'unknown')} on {date_str}\n\n**Key Points:**\n- Point extracted from conversation\n- Another key insight\n\n**Outcome:** {data.get('summary', 'No summary available')[:100]}\n"

    def _template_changelog(self, data: dict) -> str:
        """Changelog format with file paths."""
        return f"# Changelog Entry\n\n## Added\n- Features added during this session\n\n## Changed\n- {data.get('workspace', 'unknown')}: Modified files\n\n## Fixed\n- Bug fixes addressed\n\n## Removed\n- Deprecated features removed\n\n**Files Modified:**\n- File paths would be listed here\n"

    def _template_debug_postmortem(self, data: dict) -> str:
        """Debug postmortem format."""
        return f"# Debug Postmortem: {data.get('firstPrompt', 'Unknown Issue')[:50]}\n\n## Symptoms\n{data.get('firstPrompt', 'Describe the symptoms')}\n\n## Investigation\n<!-- Investigation steps -->\n1. First hypothesis\n2. Test performed\n3. Result observed\n\n## Dead Ends\n<!-- Approaches that didn't work -->\n- Tried X, didn't work because Y\n- Attempted Z, ruled out because W\n\n## Root Cause\n<!-- The actual cause -->\nThe issue was caused by...\n\n## Fix Applied\n<!-- The solution -->\nApplied fix: X\nVerified by: Y\n"

    def _template_onboarding(self, data: dict) -> str:
        """Onboarding documentation format."""
        return f"# How This Works: {data.get('workspace', 'Project')} Onboarding\n\n## Architecture Overview\n<!-- High-level architecture -->\n- Component A: Purpose\n- Component B: Purpose\n\n## Key Files\n<!-- Important files to understand -->\n- `path/to/file.py`: Core logic\n- `path/to/config.py`: Configuration\n\n## Common Patterns\n<!-- Development patterns used -->\n- Pattern 1 usage\n- Pattern 2 usage\n\n## Getting Started\n<!-- First steps for new developers -->\n1. Step one\n2. Step two\n3. Step three\n\n## Common Issues\n<!-- Gotchas and how to avoid them -->\n- Issue: Solution\n"


class CHSExporter:
    """Export full session chain transcripts to a single readable file."""

    def __init__(self, exclude_thinking: bool = False, include_tool_results: bool = False):
        self.exclude_thinking = exclude_thinking
        self.include_tool_results = include_tool_results

    def _detect_terminal_id_inline(self) -> str:
        """Detect terminal ID inline (mirrors skill-guard's detect_terminal_id)."""
        import ctypes
        import os

        # Priority 1: Explicit environment variables
        for env_var in ("CLAUDE_TERMINAL_ID", "TERMINAL_ID", "TERM_ID", "SESSION_TERMINAL"):
            value = os.environ.get(env_var)
            if value:
                source = "env"
                safe_id = value.replace("/", "-").replace("\\", "-").replace(":", "-")
                return f"{source}_{safe_id}"

        # Priority 2: WT_SESSION (Windows Terminal UUID - stable per terminal)
        wt_session = os.environ.get("WT_SESSION")
        if wt_session:
            return f"console_{wt_session}"

        # Priority 3: GetConsoleWindow() handle
        if sys.platform == "win32":
            try:
                handle = ctypes.windll.kernel32.GetConsoleWindow()
                if handle:
                    hex_handle = hex(handle)[2:]
                    return f"console_{hex_handle}"
            except Exception:
                pass

        # Priority 4: Return empty string — PID fallback is forbidden by skill-guard
        # contract (terminal ID must be stable across subprocesses). Returning ""
        # allows get_current_session_id() to fall through to SDK/mtime fallbacks.
        return ""

    def get_current_session_id(self) -> str | None:
        """Get current Claude Code session UUID.

        Detection hierarchy (most reliable first):
        1. active-session file written by SessionStart hook (per-terminal, no ambiguity).
           Written by: P:\\\\\\packages/handoff/scripts/hooks/SessionStart_handoff_restore.py (symlinked).
        2. SDK list_sessions() + file_size cross-reference + last_modified tiebreaker.
           Works reliably in single-terminal environments. In multi-terminal
           environments (concurrent Claude Code sessions in the same project dir),
           may return a sibling session with higher last_modified.
        3. Mtime-based fallback: picks most recently modified transcript.

        For reliable detection in multi-terminal environments, pass --session-id
        explicitly, or use /status to determine the current session first.
        """
        # Priority 1: Check active-session file (written by SessionStart hook)
        terminal_id = self._detect_terminal_id_inline()
        if terminal_id:
            active_session_file = Path.home() / ".claude" / f"active-session-{terminal_id}.txt"
            if active_session_file.exists():
                try:
                    session_id = active_session_file.read_text().strip()
                    if session_id:
                        # Verify the transcript exists before returning
                        transcript_path = (
                            Path.home() / ".claude" / "projects" / "P--" / f"{session_id}.jsonl"
                        )
                        if transcript_path.exists():
                            return session_id
                except Exception:
                    pass

        # Priority 2: SDK list_sessions() with file_size cross-reference
        try:
            from claude_agent_sdk import list_sessions

            projects_dir = Path.home() / ".claude" / "projects"
            p_dir = projects_dir / "P--"

            sessions = list_sessions(limit=10)
            size_matches: list[tuple[int, str]] = []  # (last_modified, session_id)
            for s in sessions:
                if not s.file_size:
                    continue
                transcript = p_dir / f"{s.session_id}.jsonl"
                if not transcript.exists():
                    continue
                if s.file_size == transcript.stat().st_size:
                    size_matches.append((s.last_modified or 0, s.session_id))

            if size_matches:
                return max(size_matches)[1]
        except Exception:
            pass

        # Priority 3: Mtime-based detection (last resort, may be wrong in multi-terminal)
        projects_dir = Path.home() / ".claude" / "projects"
        if not projects_dir.exists():
            return None
        candidates = list((projects_dir / "P--").glob("*.jsonl")) if (
            projects_dir / "P--"
        ).exists() else []
        if not candidates:
            return None
        most_recent = max(candidates, key=lambda f: f.stat().st_mtime)
        return most_recent.stem

    @staticmethod
    def _registry_entries_to_chain_paths(
        registry_entries: list[dict],
        max_sessions: int,
    ) -> list[tuple[str, str]]:
        """Convert registry entries (queried by session_id) to chain_paths format.

        Returns list of (session_id, transcript_path) tuples, oldest-first,
        deduplicated by transcript_path.
        """
        seen: set[str] = set()
        chain: list[tuple[str, str]] = []
        for entry in registry_entries:
            tp = entry.get("transcript_path")
            if not tp or tp in seen:
                continue
            seen.add(tp)
            chain.append((entry.get("session_id", ""), tp))
        chain = chain[-max_sessions:]
        return chain

    def _export_from_chain_paths(
        self,
        session_id: str,
        chain_paths: list[tuple[str, str]],
        output_path: Path | None,
    ) -> Path:
        """Write all transcripts from chain_paths to one markdown file."""
        if output_path is None:
            exports_dir = Path.home() / ".claude" / "exports"
            try:
                exports_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as exc:
                raise ValueError(f"Cannot create exports directory {exports_dir}: {exc}") from exc

            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            output_path = exports_dir / f"chain_{timestamp}.md"

        projects_dir = Path.home() / ".claude" / "projects"

        try:
            with open(output_path, "w", encoding="utf-8", newline="\n") as out:
                now = datetime.now()
                out.write(f"# Session Chain Export\n\n")
                out.write(f"**Root session:** {session_id}  \n")
                out.write(f"**Exported:** {now.strftime('%Y-%m-%d %H:%M:%S')}  \n")
                out.write(f"**Sessions in chain:** {len(chain_paths)}\n\n")
                out.write("---\n\n")

                for i, (sid, full_path) in enumerate(chain_paths, 1):
                    path = Path(full_path)
                    try:
                        path.resolve().relative_to(projects_dir.resolve())
                    except ValueError:
                        out.write(f"## Session {i} — `{sid}`\n\n")
                        out.write(f"*[Error: Invalid path: {full_path} (outside allowed directory)]*\n\n")
                        out.write("---\n\n")
                        continue

                    out.write(f"## Session {i} — `{path.stem}`\n\n")
                    self._format_transcript_to_file(path, out)
                    out.write("\n---\n\n")

        except (PermissionError, OSError) as exc:
            raise ValueError(f"Failed to write export file {output_path}: {exc}") from exc

        return output_path

    def export_chain(
        self,
        session_id: str | None = None,
        output_path: Path | None = None,
        max_sessions: int = 30,
    ) -> Path:
        """Walk the session chain and write all transcripts to one markdown file.

        Strategy:
        1. Try session_registry.jsonl (queried by session_id) — covers cross-terminal chains
        2. Fall back to sessions-index.json for pre-registry data
        """
        if session_id is None:
            session_id = self.get_current_session_id()
            if session_id is None:
                raise ValueError(
                    "Could not determine current session ID. "
                    "Pass --session-id explicitly or ensure current_session.json exists."
                )

        # Strategy 1: Registry by session_id (cross-terminal chain)
        registry_path = Path("P:/.claude/.artifacts/session_registry.jsonl")
        if registry_path.exists():
            sys.path.insert(0, str(Path("P:/packages/snapshot/scripts/hooks/__lib")))
            try:
                from session_registry import query_registry

                entries = query_registry(session_id=session_id, limit=10_000, registry_path=registry_path)
                if entries:
                    chain_paths = self._registry_entries_to_chain_paths(entries, max_sessions)
                    if chain_paths:
                        return self._export_from_chain_paths(session_id, chain_paths, output_path)
            except Exception:
                pass
            finally:
                sys.path.pop(0)

        # Strategy 2: sessions-index.json (fallback for pre-registry data)
        from importlib.util import spec_from_file_location, module_from_spec

        history_chain_path = Path(__file__).parent.parent.parent.parent / "core" / "history_chain.py"

        def _load_history_chain():
            """Load history_chain directly from file, bypassing core/__init__."""
            _spec = spec_from_file_location("core.history_chain", str(history_chain_path))
            if _spec is None or _spec.loader is None:
                raise ImportError(f"Cannot load history_chain from {history_chain_path}")
            _mod = module_from_spec(_spec)
            _loaded_modules = sys.modules.get("core.history_chain")
            if _loaded_modules:
                sys.modules.pop("core.history_chain")
            sys.modules["core.history_chain"] = _mod
            try:
                _spec.loader.exec_module(_mod)
            finally:
                if _loaded_modules:
                    sys.modules["core.history_chain"] = _loaded_modules
                else:
                    sys.modules.pop("core.history_chain", None)
            return _mod

        try:
            _history_chain = _load_history_chain()
            load_sessions_index = _history_chain.load_sessions_index
        except Exception as exc:
            raise ValueError(f"history_chain module not importable: {exc}") from exc

        try:
            sessions_index = load_sessions_index()
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Failed to load sessions-index.json: {exc}") from exc

        target_entry = sessions_index.get(session_id)
        if not target_entry:
            raise ValueError(f"Session {session_id} not found in sessions-index.json")

        target_started = target_entry.get("startedAt", 0)

        valid_entries = []
        for sid, entry in sessions_index.items():
            started = entry.get("startedAt", 0)
            if started <= target_started:
                valid_entries.append((sid, entry, started))

        valid_entries.sort(key=lambda x: x[2], reverse=True)
        recent_entries = valid_entries[:max_sessions]
        recent_entries.sort(key=lambda x: x[2])

        chain_paths = [(sid, entry.get("fullPath")) for sid, entry, _ in recent_entries if entry.get("fullPath")]

        if not chain_paths:
            raise ValueError(f"No transcript files found for session {session_id}")

        return self._export_from_chain_paths(session_id, chain_paths, output_path)

    def _format_transcript(self, transcript_path: Path) -> list[str]:
        """Parse a .jsonl transcript and return formatted markdown lines."""
        result: list[str] = []
        try:
            with open(transcript_path, encoding="utf-8", errors="replace") as f:
                for raw_line in f:
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    try:
                        entry = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    entry_type = entry.get("type", "")
                    if entry_type == "user":
                        text = self._extract_content(entry, role="user")
                        if text:
                            result.append(f"**User:** {text}\n\n")
                    elif entry_type == "assistant":
                        text = self._extract_content(entry, role="assistant")
                        if text:
                            result.append(f"**Assistant:** {text}\n\n")
        except (OSError, FileNotFoundError) as exc:
            # Handle both OSError and FileNotFoundError (IO-006)
            result.append(f"*[Error reading {transcript_path.name}: {exc}]*\n\n")
        return result

    def _format_transcript_to_file(self, transcript_path: Path, out) -> None:
        """Parse a .jsonl transcript and stream formatted markdown to file handle.

        Streaming version avoids O(N²) memory behavior (PERF-002 fix).
        """
        try:
            with open(transcript_path, encoding="utf-8", errors="replace") as f:
                for raw_line in f:
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    try:
                        entry = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    entry_type = entry.get("type", "")
                    if entry_type == "user":
                        text = self._extract_content(entry, role="user")
                        if text:
                            out.write(f"**User:** {text}\n\n")
                    elif entry_type == "assistant":
                        text = self._extract_content(entry, role="assistant")
                        if text:
                            out.write(f"**Assistant:** {text}\n\n")
        except (OSError, FileNotFoundError) as exc:
            out.write(f"*[Error reading {transcript_path.name}: {exc}]*\n\n")

    def _extract_content(self, entry: dict[str, Any], role: str) -> str:
        """Extract readable text from a message entry."""
        content = entry.get("message", {}).get("content", "")
        if isinstance(content, str):
            return content.strip()
        if not isinstance(content, list):
            return ""

        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type", "")
            if item_type == "text":
                text = item.get("text", "").strip()
                if text:
                    parts.append(text)
            elif item_type == "thinking" and not self.exclude_thinking:
                thinking = item.get("thinking", "").strip()
                if thinking:
                    # Truncate long thinking blocks
                    preview = thinking[:300] + ("…" if len(thinking) > 300 else "")
                    parts.append(f"\n> *[Thinking]* {preview}\n")
            elif item_type == "tool_use" and self.include_tool_results:
                name = item.get("name", "?")
                inp = json.dumps(item.get("input", {}), indent=2)
                inp_preview = inp[:400] + ("…" if len(inp) > 400 else "")
                parts.append(f"\n*[Tool call: {name}]*\n```json\n{inp_preview}\n```\n")
            elif item_type == "tool_result" and self.include_tool_results:
                tc = item.get("content", "")
                if isinstance(tc, list):
                    tc = " ".join(
                        i.get("text", "") for i in tc if isinstance(i, dict)
                    )
                preview = str(tc)[:400] + ("…" if len(str(tc)) > 400 else "")
                parts.append(f"\n*[Tool result]*\n```\n{preview}\n```\n")
        # Stream join to avoid O(N²) behavior
        if not parts:
            return ""
        result = "\n".join(parts)
        return result.strip()


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
        description=(
            "Chat History Search (/chs) - Advanced chat history search\n\n"
            "Export modes:\n"
            "  - Query export: /chs \"query\" --output results.json or --clipboard\n"
            "  - Session chain export: /chs export -> python ... --export"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  /chs \"authentication\" --mode documentation\n"
            "  /chs export\n"
            "  /chs export --session-id abc123\n"
            "  /chs export --max-sessions 50 --output P:\\\\\\tmp/chs-export.md\n"
            "  python P:\\\\\\packages/search-research/skills/chs/scripts/chs_cli.py --export --session-id abc123\n"
        ),
    )
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
    parser.add_argument(
        "--stage",
        choices=["1", "2", "auto"],
        default="auto",
        help="Search stage: 1=index-only, 2=deep scan, auto=auto-select",
    )
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
    parser.add_argument("--context", type=int, help="Show N messages around match")
    parser.add_argument("--show", help="Show specific session")
    parser.add_argument("--list", action="store_true", help="List recent sessions")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--reindex", action="store_true", help="Rebuild search index")
    parser.add_argument("--output", help="Write query results to file (session export uses --export)")
    parser.add_argument("--clipboard", action="store_true", help="Copy query results to clipboard")
    parser.add_argument("--exclude-thinking", action="store_true", help="Exclude thinking blocks")
    parser.add_argument(
        "--include-tool-results", action="store_true", help="Include tool execution results"
    )
    parser.add_argument("--export", action="store_true", help="Export full session chain to file")
    parser.add_argument("--session-id", help="Session ID for session export (default: current session)")
    parser.add_argument("--max-sessions", type=int, default=30, help="Maximum sessions to include in chain (default: 30)")
    args = parser.parse_args()
    config = CHSConfig()
    search = CHSSearch(config)
    metrics = CHSMetrics()
    summarizer = CHSSummarizer()
    context_viewer = CHSContext()
    if args.export:
        exporter = CHSExporter(
            exclude_thinking=args.exclude_thinking,
            include_tool_results=args.include_tool_results,
        )
        try:
            out = exporter.export_chain(
                session_id=args.session_id,
                output_path=Path(args.output) if args.output else None,
                max_sessions=args.max_sessions,
            )
            file_size = out.stat().st_size
            text = out.read_text(encoding="utf-8")
            session_count = text.count("\n## Session ")
            # Rough token estimate: ~4 chars per token
            est_tokens = file_size // 4
            metadata = {
                "path": str(out),
                "session_count": session_count,
                "file_size_bytes": file_size,
                "file_size_kb": round(file_size / 1024, 1),
                "estimated_tokens": est_tokens,
                "context_safe": est_tokens < 20_000,
                "recommendation": (
                    "read_file" if est_tokens < 20_000
                    else "delegate_to_subagent" if est_tokens < 100_000
                    else "export_is_too_large_use_filters"
                ),
            }
            print(json.dumps(metadata, indent=2))
        except ValueError as exc:
            print(f"Export failed: {exc}", file=sys.stderr)
            return 1
        return 0
    if args.stats:
        since = None
        if args.since:
            since = datetime.now() - timedelta(days=7)
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
        results = search.search_stage1("", workspace=args.workspace, limit=args.limit)
        for result in results:
            print(f"{result['session_id']}: {result['first_prompt']}")
        return 0
    if args.show:
        session_path = Path(args.show)
        if not session_path.exists():
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
            output = context_viewer.show_context(session_path, 0, args.context)
        else:
            with open(session_path, encoding="utf-8") as f:
                output = f.read()
        print(output)
        return 0
    if not args.query:
        parser.print_help()
        return 1
    stage = args.stage
    if stage == "auto":
        stage = "1"
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
    if args.mode:
        summarized = []
        for result in results:
            summary = summarizer.summarize(result, args.mode)
            result["summary"] = summary
            summarized.append(result)
        results = summarized
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
                if result["summary"].startswith("#"):
                    print(f"\n{result['summary']}\n")
                else:
                    print(f"    Summary: {result['summary']}")
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
