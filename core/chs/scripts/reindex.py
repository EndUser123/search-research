#!/usr/bin/env python3
"""Unified CHS reindexer — all providers into one DB with provider tagging.

Builds P:/.data/chs/chat_history.db (or --db-path) from every registered
history provider (claude_code_raw, codex_desktop, claude_log, grok_sessions)
using the provider protocol's discover()/fetch_session(), populating
projects/sessions/messages/turns + FTS via schema triggers.

Incremental: per-source checkpoint (size, mtime) in chs_reindex_checkpoint;
unchanged sources are skipped, so repeat runs only process new/changed files.

Usage:
    python -m core.chs.scripts.reindex [--db-path PATH] [--providers id ...]
                                       [--full-rebuild] [--limit N]
"""
from __future__ import annotations

import argparse
import logging
import re
import sqlite3
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("reindex")

_PKG_ROOT = Path(__file__).resolve().parents[3]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

DEFAULT_DB_PATH = Path("P:/.data/chs/chat_history.db")
SCHEMA_PATH = _PKG_ROOT / "core" / "chs" / "schema.sql"
COMMIT_EVERY = 20  # sources

# Synthetic-context prefixes that should not become first_prompt
_SYNTHETIC_PREFIXES = ("<user_info>", "<system-reminder>", "<git_status>",
                       "<skill_information>", "<rules>")

_CODE_RE = re.compile(r"```|\bdef \w+\(|\bclass \w+:|\bimport \w+|\bSELECT .* FROM\b")
_ERR_RE = re.compile(r"\berror\b|\btraceback\b|\bexception\b|\bfail(?:ed|ure)?\b", re.I)


def _entry_role(entry: dict) -> str | None:
    """Map a provider entry to a CHS role, or None to skip."""
    role = entry.get("role")
    if role in ("user", "assistant", "tool", "system"):
        return role
    t = entry.get("type", "")
    mapped = {"user": "user", "assistant": "assistant",
              "tool": "tool", "tool_result": "tool",
              "system": "system"}.get(t)
    if mapped:
        return mapped
    # prompt-history shapes (~/.claude/history.jsonl 'display',
    # ~/.codex/history.jsonl 'text'): user prompts only
    if "display" in entry or "text" in entry:
        return "user"
    return None


def _entry_content(entry: dict, extract_fn) -> str:
    """Extract text from a provider entry (normalized or raw shape)."""
    content = entry.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        text = "\n".join(parts)
    elif "display" in entry and entry["display"]:
        text = str(entry["display"])
    elif "text" in entry and entry["text"]:
        text = str(entry["text"])
    elif "message" in entry and entry["message"] is not None:
        text = extract_fn(entry["message"])
    else:
        text = str(content) if content is not None else ""
    tool_calls = entry.get("tool_calls")
    if isinstance(tool_calls, list):
        for tc in tool_calls:
            if isinstance(tc, dict):
                name = tc.get("name", "unknown")
                args = tc.get("arguments", "")
                if isinstance(args, str) and len(args) > 200:
                    args = args[:200] + "..."
                text = (text + f"\n[Tool: {name}] {args}").strip()
    return text


def _entry_ts(entry: dict, default: float) -> int:
    ts = entry.get("timestamp")
    if ts is not None:
        try:
            return int(float(ts) / (1000 if float(ts) > 1e11 else 1))
        except (TypeError, ValueError):
            pass
    return int(default)


def _turns_from_messages(rows: list[tuple[int, str, str]]) -> list[tuple[int, int, int, int, str, int, int]]:
    """Group messages (id, role, content) into user→assistant turns.

    Returns tuples: (start_mid, end_mid, ts_start, ts_end, content, has_code, has_error)
    Timestamps are added by caller (parallel list) — here rows carry (id, role, content)
    and we return ids only; caller joins timestamps by message id.
    """
    out = []
    cur: list[int] = []
    cur_content: list[str] = []

    def flush():
        if cur and cur_content:
            text = "\n".join(cur_content)
            out.append((cur[0], cur[-1], text,
                        1 if _CODE_RE.search(text) else 0,
                        1 if _ERR_RE.search(text) else 0))
        cur.clear()
        cur_content.clear()

    for mid, role, content in rows:
        if role == "user" and cur:
            flush()
        cur.append(mid)
        cur_content.append(f"[{role}] {content}" if role != "user" else content)
        if role != "user" and len(cur_content) >= 40:
            flush()
    flush()
    return out


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chs_reindex_checkpoint ("
        " provider TEXT NOT NULL, source_id TEXT NOT NULL,"
        " size INTEGER NOT NULL, mtime REAL NOT NULL, message_count INTEGER,"
        " PRIMARY KEY (provider, source_id))")
    conn.commit()
    return conn


def reindex(db_path: Path, providers: list[str] | None, limit: int | None,
            full_rebuild: bool) -> None:
    from core.chs.providers import discover_all
    from core.chs.providers import claude_code_raw, codex_desktop  # extract fns

    extractors = {
        "claude_code_raw": claude_code_raw._extract_text_content,
        # codex_desktop has no exported extractor; raw 'message' fields on
        # codex entries are plain strings, so str() suffices
        "codex_desktop": lambda m: m if isinstance(m, str) else str(m),
    }

    conn = init_db(db_path)
    all_provs = discover_all()
    if providers:
        all_provs = [p for p in all_provs if p.provider_id in providers]
    logger.info("providers: %s -> %s", [p.provider_id for p in discover_all()],
                [p.provider_id for p in all_provs])

    stats: dict[str, dict[str, int]] = {}
    for prov in all_provs:
        pid = prov.provider_id
        stats[pid] = {"sources": 0, "skipped": 0, "messages": 0, "turns": 0,
                      "first_prompt": 0}
        sources = prov.discover()
        if limit:
            sources = sources[:limit]
        logger.info("[%s] %d sources", pid, len(sources))

        for src in sources:
            sid = src["source_id"]
            # locate the backing file for change detection
            file_path = None
            for key in ("path", "file_path"):
                if src.get(key):
                    file_path = Path(src[key])
                    break
            if file_path is None:
                # fall back: providers expose discover()'s source dicts without
                # paths; use occurred_at + source count heuristics — treat as
                # changed unless message_count matches checkpoint
                pass

            if file_path and file_path.exists():
                st = file_path.stat()
                size, mtime = st.st_size, st.st_mtime
            else:
                size, mtime = -1, float(src.get("occurred_at_ts", time.time()))

            if not full_rebuild and file_path is not None:
                row = conn.execute(
                    "SELECT size, mtime FROM chs_reindex_checkpoint"
                    " WHERE provider=? AND source_id=?", (pid, sid)).fetchone()
                if row and row[0] == size and abs(row[1] - mtime) < 1e-6:
                    stats[pid]["skipped"] += 1
                    continue
                if row and row[0] == -1 and size == -1:
                    stats[pid]["skipped"] += 1
                    continue

            try:
                session = prov.fetch_session(sid)
            except Exception as e:  # noqa: BLE001 — per-source isolation
                logger.debug("[%s] fetch failed %s: %s", pid, sid, e)
                continue
            entries = session.get("entries", [])
            if not entries:
                continue

            cwd = session.get("cwd") or src.get("cwd") or f"~/{pid}"
            project = session.get("project") or src.get("project") or pid
            base_ts = session.get("mtime_ts") or (
                file_path.stat().st_mtime if file_path and file_path.exists()
                else time.time())

            cur = conn.execute("SELECT id FROM projects WHERE path=?", (cwd,)).fetchone()
            if cur:
                project_id = cur[0]
            else:
                project_id = conn.execute(
                    "INSERT INTO projects (path, label) VALUES (?,?)",
                    (cwd, project)).lastrowid

            session_key = f"{pid}:{sid}"
            conn.execute(
                "DELETE FROM turns WHERE session_id IN"
                " (SELECT id FROM sessions WHERE session_key=?)", (session_key,))
            conn.execute(
                "DELETE FROM messages WHERE session_id IN"
                " (SELECT id FROM sessions WHERE session_key=?)", (session_key,))
            conn.execute("DELETE FROM sessions WHERE session_key=?", (session_key,))
            session_id = conn.execute(
                "INSERT INTO sessions (session_key, project_id, provider,"
                " started_at, message_count) VALUES (?,?,?,?,?)",
                (session_key, project_id, pid, int(float(base_ts)),
                 len(entries))).lastrowid

            first_prompt = None
            msg_rows = []  # (id, ts, role, content)
            extract_fn = extractors.get(pid)
            for i, entry in enumerate(entries):
                role = _entry_role(entry)
                if role is None:
                    continue
                content = _entry_content(entry, extract_fn or (lambda m: str(m)))
                if not content or not content.strip():
                    continue
                ts = _entry_ts(entry, base_ts)
                if (role == "user" and first_prompt is None
                        and not content.lstrip().startswith(_SYNTHETIC_PREFIXES)
                        and "<user_query>" not in content[:2000].split("\n")[0]):
                    first_prompt = content.strip()[:500]
                mid = conn.execute(
                    "INSERT INTO messages (message_id, session_id, project_id,"
                    " timestamp, role, provider, content) VALUES (?,?,?,?,?,?,?)",
                    (f"{pid}:{sid}:{i}", session_id, project_id, ts, role, pid,
                     content)).lastrowid
                msg_rows.append((mid, ts, role, content))
                stats[pid]["messages"] += 1

            if first_prompt:
                conn.execute("UPDATE sessions SET first_prompt=? WHERE id=?",
                             (first_prompt, session_id))
                stats[pid]["first_prompt"] += 1

            # build turns
            plain = [(m[0], m[2], m[3]) for m in msg_rows]
            ts_map = {m[0]: m[1] for m in msg_rows}
            for start_mid, end_mid, text, has_code, has_error in _turns_from_messages(plain):
                conn.execute(
                    "INSERT OR IGNORE INTO turns (session_id, project_id,"
                    " start_message_id, end_message_id, timestamp_start,"
                    " timestamp_end, content, has_code, has_error)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (session_id, project_id, start_mid, end_mid,
                     ts_map[start_mid], ts_map[end_mid], text, has_code,
                     has_error))
                stats[pid]["turns"] += 1

            conn.execute(
                "INSERT OR REPLACE INTO chs_reindex_checkpoint"
                " (provider, source_id, size, mtime, message_count)"
                " VALUES (?,?,?,?,?)",
                (pid, sid, size, mtime, len(entries)))
            stats[pid]["sources"] += 1
            if stats[pid]["sources"] % COMMIT_EVERY == 0:
                conn.commit()
                logger.info("[%s] %d sources done (%d skipped, %d msgs)",
                            pid, stats[pid]["sources"], stats[pid]["skipped"],
                            stats[pid]["messages"])
        conn.commit()

    conn.close()
    logger.info("==== summary ====")
    for pid, s in stats.items():
        logger.info(
            "%-16s sources=%d skipped=%d messages=%d turns=%d first_prompt=%d",
            pid, s["sources"], s["skipped"], s["messages"], s["turns"],
            s["first_prompt"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Unified CHS reindex (all providers)")
    ap.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    ap.add_argument("--providers", nargs="*", default=None,
                    help="subset of provider ids (default: all)")
    ap.add_argument("--limit", type=int, default=None, help="max sources per provider")
    ap.add_argument("--full-rebuild", action="store_true",
                    help="ignore checkpoints and reindex everything")
    args = ap.parse_args()
    reindex(args.db_path, args.providers, args.limit, args.full_rebuild)


if __name__ == "__main__":
    main()
