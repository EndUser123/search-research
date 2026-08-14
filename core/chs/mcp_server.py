"""chs MCP server — dedicated chat-history-search over the unified CHS DB.

Two tools under server prefix `chs`:
  - chs__search(query, provider?, role?, limit?) — FTS5 over messages+turns
  - chs__read(message_id) — single message with full content

Stdio transport (FastMCP). Registered in ~/.grok/config.toml.
DB: P:/.data/chs/chat_history.db (CHS_DB_PATH overrides).
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parents[3]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("chs")

DEFAULT_DB = "P:/.data/chs/chat_history.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(os.environ.get("CHS_DB_PATH", DEFAULT_DB))
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _fts_escape(query: str) -> str:
    """Escape a free-text query into a safe FTS5 MATCH expression."""
    tokens = [t for t in query.replace('"', " ").split() if t]
    if not tokens:
        return ""
    return " ".join(f'"{t}"' for t in tokens)


@mcp.tool(description=(
    "Search past AI agent chat sessions across all hosts (Grok, Claude, Codex). "
    "Full-text search over user prompts, assistant replies, and tool activity. "
    "Use BEFORE treating any topic as new — past conversations are the primary "
    "record of what was decided and why. Returns provider, role, session, date, "
    "and a content snippet per hit."
))
def search(query: str, provider: str | None = None, role: str | None = None,
           limit: int = 10) -> str:
    """FTS5 search over messages in the unified chat-history DB."""
    match = _fts_escape(query)
    if not match:
        return "Empty query."
    limit = max(1, min(int(limit), 50))
    where = ["messages_fts MATCH ?"]
    params: list = [match]
    if provider:
        where.append("m.provider = ?")
        params.append(provider)
    if role:
        where.append("m.role = ?")
        params.append(role)
    sql = (
        "SELECT m.message_id, m.provider, m.role, m.content, m.timestamp,"
        " s.session_key, s.first_prompt"
        " FROM messages_fts f JOIN messages m ON m.rowid = f.rowid"
        " JOIN sessions s ON s.id = m.session_id"
        f" WHERE {' AND '.join(where)}"
        " ORDER BY bm25(messages_fts) LIMIT ?")
    params.append(limit)
    rows = _conn().execute(sql, params).fetchall()
    if not rows:
        return f"No results for {query!r}."
    out = [f"Found {len(rows)} hits for {query!r}:\n"]
    for mid, prov, r, content, ts, skey, fp in rows:
        snippet = content[:300].replace("\n", " ")
        date = _ts_to_date(ts)
        out.append(
            f"[{prov}/{r}] {date} session={skey[:44]}\n"
            f"  {snippet}\n  (id={mid} — use chs__read for full text)")
    return "\n".join(out)


@mcp.tool(description=(
    "Read one full chat-history message by id. Use after chs__search to get "
    "the complete content of a hit (search returns 300-char snippets)."
))
def read(message_id: str) -> str:
    """Return full content of one message."""
    row = _conn().execute(
        "SELECT m.provider, m.role, m.content, m.timestamp, s.session_key"
        " FROM messages m JOIN sessions s ON s.id = m.session_id"
        " WHERE m.message_id = ?", (message_id,)).fetchone()
    if not row:
        return f"No message with id {message_id!r}."
    prov, role, content, ts, skey = row
    return (f"[{prov}/{role}] {_ts_to_date(ts)} session={skey}\n\n{content}")


def _ts_to_date(ts) -> str:
    try:
        import datetime as _dt
        return _dt.datetime.fromtimestamp(int(ts), tz=_dt.UTC).strftime("%Y-%m-%d")
    except Exception:  # noqa: BLE001
        return str(ts)


if __name__ == "__main__":
    mcp.run(transport="stdio")
