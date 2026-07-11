"""cc-lazy-closure-debt gate-residue store — FP-feedback loop for gate blocks.

Surfaces prior Stop-hook BLOCKS (from diagnostics.db + stop_blocks.jsonl) as
"residue" so the model can tell when a gate block was a likely false positive.
A block is `confirmed_fp` only when a subsequent turn ran a referencing tool
(an artifact) — a prose-only "that's by design" rebuttal stays `disputed`,
and a block with no follow-up stays `unresolved`. (The /rns regression: no
artifact => never confirmed_fp.)

Scope (v1): Stop blocks ONLY. PreToolUse blocks are not captured in
diagnostics.db (0 rows there) and are a documented v2 gap.

State path: <state_root>/cc-lazy-closure-debt/cc-gate-residue/{terminal_id}.jsonl
Watermark:  <state_root>/cc-lazy-closure-debt/cc-gate-residue/{terminal_id}.watermark.json

Concurrency model copied from debt_store: append + flush + fsync, no in-place
rewrite, so concurrent UPS-hook appends never race. Classifications and
promotions are appended as update records keyed by ledger_id; recent_residue
folds the newest update over its block row (append-only, last-write-wins).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from debt_store import DEFAULT_STATE_ROOT, _next_seq, _safe_id

PLUGIN_NAME = "cc-lazy-closure-debt"
RESIDUE_SUBDIR = "cc-gate-residue"

# Sources (director-verified this session). Overridable via env for tests.
DIAGNOSTICS_DB = Path(
    os.environ.get("CC_GATE_RESIDUE_DB", "P:/.claude/hooks/logs/diagnostics/diagnostics.db")
)
STOP_BLOCKS_JSONL = Path(
    os.environ.get(
        "CC_GATE_RESIDUE_JSONL", "P:/.claude/hooks/logs/diagnostics/stop_blocks.jsonl"
    )
)

# Tools whose input can refute a block. Task/Write/Edit count as acting on the
# artifact; the classic refutation is Grep/Read/Glob/Bash on the claimed target.
REFERENCING_TOOLS = {"Bash", "Grep", "Glob", "Read", "Task", "Write", "Edit"}

# A token is "specific enough" to count as a block reference if it is long and
# looks like an identifier/path (has '_' or '.' or a digit). Generic prose words
# ("deleted", "claim", "the") are excluded so a coincidental Grep doesn't升级 a
# block to confirmed_fp. ponytail: tuned to the #1415 calibration (clip_client.py)
# and the /rns regression (no specific token => no artifact).
_SPECIFIC_TOKEN = re.compile(r"[A-Za-z0-9_./\-]{5,}")


def _residue_dir(state_root: Optional[Path] = None) -> Path:
    base = Path(state_root) if state_root is not None else DEFAULT_STATE_ROOT
    p = base / PLUGIN_NAME / RESIDUE_SUBDIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def _ledger_path(terminal_id: str, state_root: Optional[Path] = None) -> Path:
    return _residue_dir(state_root) / f"{_safe_id(terminal_id)}.jsonl"


def _watermark_path(terminal_id: str, state_root: Optional[Path] = None) -> Path:
    return _residue_dir(state_root) / f"{_safe_id(terminal_id)}.watermark.json"


def _load_watermark(terminal_id: str, state_root: Optional[Path] = None) -> dict:
    p = _watermark_path(terminal_id, state_root)
    if not p.exists():
        return {"db_max_id": 0, "jsonl_byte_offset": 0}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"db_max_id": 0, "jsonl_byte_offset": 0}


def _write_watermark(
    terminal_id: str, wm: dict, state_root: Optional[Path] = None
) -> None:
    p = _watermark_path(terminal_id, state_root)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(wm), encoding="utf-8")
    os.replace(tmp, p)  # atomic


def _append_row(path: Path, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def _block_tokens(gate_name: str, reason: str) -> tuple[set[str], set[str]]:
    """Block-specific tokens, split by why they'd be specific in a tool input.

    Returns (path_tokens, prose_tokens):
      path_tokens — path/identifier-shaped tokens (>=5 chars, underscore/dot/digit
        in the token). These can appear in tool inputs and signal a genuine reference
        to a file/path mentioned in the block reason.
      prose_tokens — short identifier tokens from reason text (>=3 chars, common
        English words excluded). These are ONLY used for prose-match (the disputed
        branch) to avoid false artifact links when e.g. "read" in the block reason
        is a substring of "README.md" in tool input.

    The split prevents the /rns regression: a tool call on an unrelated path whose
    name happens to contain an English word from the block reason must NOT count as
    a referencing artifact.
    """
    _STOPWORDS = frozenset({
        "the", "and", "for", "was", "are", "has", "had", "but", "not",
        "you", "all", "any", "can", "use", "used", "may", "see", "say",
        "set", "get", "put", "run", "via", "its", "per", "out", "one",
        "two", "new", "old", "too", "how", "why", "now", "far", "end",
        "yet", "way", "own", "let", "did", "got", "try", "ask", "big",
        "fpx", "ded", "ref", "xxx", "fix", "bug", "doc", "log", "msg",
        "claim", "deleted", "before", "removed", "removal", "because",
        "during", "module", "system", "plugin", "package", "library",
    })
    path_tokens: set[str] = set()
    prose_tokens: set[str] = set()
    text = f"{gate_name}\n{reason or ''}"

    # Path tokens: long, contain a path-specific character
    for m in _SPECIFIC_TOKEN.findall(text):
        if len(m) >= 5 and any(c in m for c in "_./0123456789"):
            path_tokens.add(m.casefold())

    # Prose tokens: short identifiers from reason text (not path tokens).
    # NOT used for tool-input matching — only for prose rebuttal detection.
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]{2,}", text):
        token = m.group(0).casefold()
        if token not in path_tokens and len(token) >= 3 and token not in _STOPWORDS and not token.startswith("stop"):
            prose_tokens.add(token)

    return path_tokens, prose_tokens


def _tool_input_text(tool_block: dict) -> str:
    """Join the referenceable fields of a tool_use block into one search string."""
    inp = tool_block.get("input") or {}
    if not isinstance(inp, dict):
        return ""
    parts = []
    for key in ("command", "file_path", "path", "query", "pattern", "notebook_path"):
        val = inp.get(key)
        if isinstance(val, str):
            parts.append(val)
    return " ".join(parts)


def classify_block(
    block_row: dict,
    post_block_turn_tools: list[dict],
    post_block_turn_text: str,
) -> tuple[str, Optional[dict]]:
    """Classify a block against the follow-up turn's tools + text.

    Returns (classification, artifact). Pure: writes nothing.
      - confirmed_fp: a referencing tool_use targets a block-specific token.
      - disputed: prose rebuttal only (text references the block, no tool).
      - unresolved: nothing references the block.
    """
    gate_name = str(block_row.get("gate_name", ""))
    reason = str(block_row.get("block_reason_excerpt", ""))
    path_tokens, prose_tokens = _block_tokens(gate_name, reason)

    for pos, tool in enumerate(post_block_turn_tools or []):
        if not isinstance(tool, dict):
            continue
        name = str(tool.get("name", ""))
        if name not in REFERENCING_TOOLS:
            continue
        haystack = _tool_input_text(tool).casefold()
        if not haystack:
            continue
        # Path tokens use substring matching (specific identifiers in paths).
        hit = next((t for t in path_tokens if t and t in haystack), None)
        # Prose tokens use WORD-BOUNDARY matching only — a common English word
        # from the block reason must NOT match as a substring of a filename
        # (e.g. "read" in "README.md").
        if not hit:
            hit = next(
                (t for t in prose_tokens if t and re.search(rf"(?<!\w){re.escape(t)}(?!\w)", haystack)),
                None,
            )
        if hit:
            target = hit
            # Prefer a path-like target when present (more actionable).
            for key in ("file_path", "path", "notebook_path"):
                v = (tool.get("input") or {}).get(key) if isinstance(tool.get("input"), dict) else None
                if isinstance(v, str) and v:
                    target = v
                    break
            return (
                "confirmed_fp",
                {
                    "tool": name,
                    "target": target[:200],
                    "transcript_pos": pos,
                },
            )

    # Prose rebuttal: text references a block-specific token OR the gate name.
    text_cf = (post_block_turn_text or "").casefold()
    if text_cf.strip():
        gate_token = re.sub(r"[^a-zA-Z0-9]+", " ", gate_name).split()
        gate_token_cf = [g for g in (w.casefold() for w in gate_token) if len(g) >= 5]
        if any(t and t in text_cf for t in (path_tokens | prose_tokens)) or any(
            g and g in text_cf for g in gate_token_cf
        ):
            return ("disputed", None)

    return ("unresolved", None)


def _make_ledger_id(gate_name: str, response_hash: Optional[str], fallback: str) -> str:
    if response_hash:
        # Use a short, stable slice (matches spec example: 8 hex chars).
        short = re.sub(r"[^a-zA-Z0-9]", "", response_hash)[:8]
        if short:
            return f"{gate_name}:{short}"
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(fallback))[:32]
    return f"{gate_name}:{safe}"


def _normalize_gate_name(raw: str) -> str:
    """Normalize a gate/hook-name across sink variants for merge-key dedupe.

    Handles every pair found in live data (verified 2026-07-10):
      StopHook_cross_validator.py ↔ cross_validator  → cross_validator
      Stop.py:epistemic_contract   ↔ epistemic_contract → epistemic_contract
      StopHook_unverified_stance.py ↔ unverified_stance  → unverified_stance
      Stop.py:semantic_critic      ↔ semantic_critic    → semantic_critic
      Stop.py:proposal_critique_gate ↔ proposal_critique_gate → proposal_critique_gate
      Stop.py:cjk_drift_detector   ↔ cjk_drift_detector  → cjk_drift_detector
      Stop.py:skill_first_stop_gate ↔ skill_first_stop_gate → skill_first_stop_gate
      Stop.py:safety_gate          ↔ Stop_safety_gate.py   → safety_gate
      Stop_deletion_verification_guard ↔ deletion_verification_guard → deletion_verification_guard
      skill-guard_Stop:slash_gate                              → slash_gate
    Non-merging pairs (genuinely different gate names):
      StopHook_perf_attribution_gate vs perf_attribution  → different names
      Stop_removal_completeness_guard vs removal_completeness  → different names
      Stop_diagnostic_analysis_quality_gate.py vs diagnostic_analysis_quality  → different names
    """
    name = str(raw or "").strip()
    for prefix in ["skill-guard_Stop:", "StopHook_", "Stop.py:", "Stop_"]:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    if name.endswith(".py"):
        name = name[:-3]
    return name.casefold()


def _row_from_db(r: sqlite3.Row, terminal_id: str) -> dict:
    gate_name = str(r["hook_name"] or "unknown_gate")
    reason = str(r["reason"] or "")
    ts_str = str(r["timestamp"] or "")
    ts_ms = _parse_ts_ms(ts_str)
    session_id = str(r["session_id"] or "")
    normalized = _normalize_gate_name(gate_name)
    # diagnostics.db has no response_hash; use (id, session_id) as the discriminator.
    ledger_id = _make_ledger_id(gate_name, None, f"db-{r['id']}-{session_id}")
    return {
        "ts": int(ts_ms // 1000),
        "ts_ms": ts_ms,
        "seq": _next_seq(),
        "terminal_id": _safe_id(terminal_id),
        "ledger_id": ledger_id,
        "gate_name": gate_name,
        "normalized_gate": normalized,
        # R2: event_second rounded to 5s bucket to handle wall-clock drift
        # between the two write paths (Stop.py:296 → diagnostics.db,
        # stop_block_log.py:102 → stop_blocks.jsonl). Same block event
        # recorded in both sinks stays within a couple seconds.
        "event_second": int(ts_ms // 5000) * 5,
        "block_reason_excerpt": reason[:300],
        "source_ref": {
            "sink": "diagnostics.db",
            "row_id": int(r["id"]),
            "session_id": session_id,
            "transcript_path": "",
        },
        "artifact": None,
        "classification": "unresolved",
        "classified_ts": 0,
    }


def _row_from_jsonl(obj: dict) -> dict:
    gate_name = str(obj.get("gate_name") or "unknown_gate")
    reason = str(obj.get("reason") or "")
    ts_ms = _parse_ts_ms(str(obj.get("timestamp") or ""))
    normalized = _normalize_gate_name(gate_name)
    ledger_id = _make_ledger_id(
        gate_name, obj.get("response_hash"), str(obj.get("timestamp") or "")
    )
    return {
        "ts": int(ts_ms // 1000),
        "ts_ms": ts_ms,
        "seq": _next_seq(),
        "terminal_id": _safe_id(obj.get("terminal_id") or "unknown"),
        "ledger_id": ledger_id,
        "gate_name": gate_name,
        "normalized_gate": normalized,
        # R2: event_second rounded to 5s bucket to handle wall-clock drift
        # between the two write paths (Stop.py:296 → diagnostics.db,
        # stop_block_log.py:102 → stop_blocks.jsonl). Same block event
        # recorded in both sinks stays within a couple seconds.
        "event_second": int(ts_ms // 5000) * 5,
        "block_reason_excerpt": reason[:300],
        "source_ref": {
            "sink": "stop_blocks.jsonl",
            "row_id": obj.get("line") if "line" in obj else None,
            "response_hash": str(obj.get("response_hash") or ""),
            "transcript_path": str(obj.get("transcript_path") or ""),
        },
        "artifact": None,
        "classification": "unresolved",
        "classified_ts": 0,
    }


def _parse_ts_ms(ts_str: str) -> int:
    """Best-effort ISO8601 -> epoch ms; falls back to int(parse) or 0."""
    if not ts_str:
        return 0
    # Numeric already?
    digits = ts_str.strip()
    if digits.isdigit():
        v = int(digits)
        return v if v > 10**12 else v * 1000  # seconds -> ms heuristic
    # ISO8601, e.g. 2026-06-18T18:40:05.351939+00:00
    try:
        from datetime import datetime

        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError):
        return 0


def _seed_watermark(terminal_id: str, state_root: Optional[Path] = None) -> dict:
    """R3: seed a fresh terminal's watermark at the CURRENT max of both sinks.

    A brand-new terminal has no actionable history; blocks of interest happen
    during live sessions. Returns the seeded watermark and writes it.
    """
    db_max = 0
    jsonl_end = 0
    if DIAGNOSTICS_DB.exists():
        try:
            con = sqlite3.connect(str(DIAGNOSTICS_DB))
            row = con.execute("SELECT MAX(id) FROM hooks").fetchone()
            if row and row[0]:
                db_max = int(row[0])
            con.close()
        except sqlite3.Error:
            pass
    if STOP_BLOCKS_JSONL.exists():
        try:
            jsonl_end = STOP_BLOCKS_JSONL.stat().st_size
        except OSError:
            pass
    wm = {"db_max_id": db_max, "jsonl_byte_offset": jsonl_end}
    _write_watermark(terminal_id, wm, state_root)
    return wm


def ingest_new_blocks(
    terminal_id: str,
    state_root: Optional[Path] = None,
    max_age_h: float = 24.0,
) -> list[dict]:
    """Incremental ingest of new Stop-blocks for this terminal.

    Reads diagnostics.db rows with id > watermark (action='block') and
    stop_blocks.jsonl bytes > watermark. R3: on first run for a terminal,
    seeds the watermark at the current max so only FUTURE events are ingested.

    R2: rows from both sinks are deduped by (normalized_gate, event_second).
    When a db row and a jsonl row merge, the jsonl row is primary (has
    response_hash + fuller reason) and is enriched with the db row's session_id.

    O(new bytes) — no full rescans. Failures are swallowed (advisory).
    """
    wm = _load_watermark(terminal_id, state_root)
    # R3: no watermark file yet = fresh terminal — seed at current sink max
    # so only future events are ingested. Tests that pre-seed (write a
    # watermark file with zeros) bypass seeding.
    wm_file = _watermark_path(terminal_id, state_root)
    if not wm_file.exists():
        wm = _seed_watermark(terminal_id, state_root)

    ledger = _ledger_path(terminal_id, state_root)
    new_rows: list[dict] = []
    db_max_id = int(wm.get("db_max_id", 0))

    # Collect raw rows from both sinks, then merge-dedupe by (norm_gate, event_second).
    db_rows: list[dict] = []
    jsonl_rows: list[dict] = []

    # --- diagnostics.db delta (id > watermark, action='block') ---
    if DIAGNOSTICS_DB.exists():
        try:
            con = sqlite3.connect(str(DIAGNOSTICS_DB))
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(
                "SELECT id, hook_name, timestamp, session_id, reason "
                "FROM hooks WHERE id > ? AND action = 'block' "
                "AND timestamp >= datetime('now', ?) ORDER BY id",
                (db_max_id, f"-{int(max_age_h)} hours"),
            )
            max_id = db_max_id
            for r in cur.fetchall():
                row = _row_from_db(r, terminal_id)
                db_rows.append(row)
                if int(r["id"]) > max_id:
                    max_id = int(r["id"])
            con.close()
            db_max_id = max_id
        except (sqlite3.Error, OSError):
            pass

    # --- stop_blocks.jsonl delta (bytes > watermark) ---
    jsonl_offset = int(wm.get("jsonl_byte_offset", 0))
    if STOP_BLOCKS_JSONL.exists():
        try:
            with open(STOP_BLOCKS_JSONL, "rb") as f:
                f.seek(jsonl_offset)
                chunk = f.read()
                new_offset = f.tell()
            text = chunk.decode("utf-8", errors="replace")
            lines = text.splitlines()
            cutoff_ts = time.time() - max_age_h * 3600
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                ts_str = str(obj.get("timestamp") or "")
                if ts_str:
                    ts_ms = _parse_ts_ms(ts_str)
                    if ts_ms > 0 and ts_ms / 1000 < cutoff_ts:
                        continue
                obj["line"] = i
                row = _row_from_jsonl(obj)
                jsonl_rows.append(row)
            jsonl_offset = new_offset
        except OSError:
            pass

    # --- R2: merge-dedupe by (normalized_gate, event_second) ---
    merged: dict[str, dict] = {}
    for row in jsonl_rows + db_rows:  # jsonl first = primary preference
        key = f"{row.get('normalized_gate', '')}:{row.get('event_second', 0)}"
        if key not in merged:
            merged[key] = row
        else:
            # Enrich: if jsonl row is primary, add db row's session_id if missing.
            existing = merged[key]
            if existing.get("source_ref", {}).get("sink") == "stop_blocks.jsonl":
                db_sess = row.get("source_ref", {}).get("session_id", "")
                if db_sess and not existing.get("source_ref", {}).get("session_id"):
                    existing.setdefault("source_ref", {})["session_id"] = db_sess

    for row in merged.values():
        _append_row(ledger, row)
        new_rows.append(row)

    _write_watermark(
        terminal_id,
        {"db_max_id": db_max_id, "jsonl_byte_offset": jsonl_offset},
        state_root,
    )
    return new_rows


def record_classification(
    terminal_id: str,
    ledger_id: str,
    classification: str,
    artifact: Optional[dict],
    state_root: Optional[Path] = None,
) -> None:
    """Append a classification update record (last-write-wins on ledger_id)."""
    record = {
        "ts": int(time.time()),
        "ts_ms": int(time.time() * 1000),
        "seq": _next_seq(),
        "terminal_id": _safe_id(terminal_id),
        "kind": "classification",
        "ledger_id": str(ledger_id),
        "classification": classification,
        "artifact": artifact,
        "classified_ts": int(time.time()),
    }
    _append_row(_ledger_path(terminal_id, state_root), record)


def mark_promoted(
    terminal_id: str, ledger_id: str, state_root: Optional[Path] = None
) -> None:
    """Append a promotion tombstone so a ledger_id yields at most one task."""
    record = {
        "ts": int(time.time()),
        "ts_ms": int(time.time() * 1000),
        "seq": _next_seq(),
        "terminal_id": _safe_id(terminal_id),
        "kind": "promoted",
        "ledger_id": str(ledger_id),
    }
    _append_row(_ledger_path(terminal_id, state_root), record)


def _fold_ledger(path: Path) -> tuple[list[dict], set[str], set[str]]:
    """Read the ledger; fold classifications + promotions over block rows.

    Returns (block_rows, promoted_ledger_ids, seen_ledger_ids).
    A block with a promotion tombstone is dropped from the result entirely.
    """
    if not path.exists():
        return [], set(), set()
    blocks: dict[str, dict] = {}
    promoted: set[str] = set()
    seen: set[str] = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                kind = obj.get("kind")
                lid = str(obj.get("ledger_id") or "")
                if kind == "promoted":
                    if lid:
                        promoted.add(lid)
                    continue
                if kind == "classification":
                    if lid and lid in blocks:
                        blocks[lid]["classification"] = obj.get("classification")
                        blocks[lid]["artifact"] = obj.get("artifact")
                        blocks[lid]["classified_ts"] = int(obj.get("classified_ts", 0))
                    continue
                # Block row (default).
                if lid:
                    seen.add(lid)
                    blocks[lid] = obj
    except OSError:
        return [], set(), set()
    rows = [b for lid, b in blocks.items() if lid not in promoted]
    return rows, promoted, seen


def recent_residue(
    terminal_id: str,
    max_age_h: float = 24.0,
    max_count: int = 5,
    state_root: Optional[Path] = None,
) -> list[dict]:
    """Return up to max_count residue rows newer than max_age_h, newest first.

    Promoted rows are excluded. Duplicate ledger_ids collapse to the single row.
    """
    rows, _promoted, _seen = _fold_ledger(_ledger_path(terminal_id, state_root))
    cutoff = int(time.time()) - int(max_age_h * 3600)
    rows = [r for r in rows if int(r.get("ts", 0)) >= cutoff]
    rows.sort(key=lambda r: (int(r.get("ts_ms", 0)), int(r.get("seq", 0))), reverse=True)
    return rows[:max_count]


def promoted_ledger_ids(
    terminal_id: str, state_root: Optional[Path] = None
) -> set[str]:
    """ledger_ids already promoted (used to avoid duplicate TaskCreate directives)."""
    _rows, promoted, _seen = _fold_ledger(_ledger_path(terminal_id, state_root))
    return promoted
