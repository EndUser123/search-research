"""Build current-turn tool events from a Stop hook's transcript_path.

WHY THIS EXISTS
  The real Claude Code **Stop** payload carries NO `tool_events` key (verified
  2026-06-18 via runtime PROBE; see memory `stop-payload-no-tool-events.md`).
  Gates that read `data["tool_events"]` therefore get `[]` and silently degrade
  toward false positives (intent_artifact_alignment, overconfidence_detector).
  `transcript_path` IS present and authoritative — parse the current turn's
  tool calls from it.

SCHEMA
  Returns FLAT-schema events (the shape both consumers expect), NOT the nested
  {name, input} form:
      {"name", "command", "file_path", "skill", "output_excerpt"}
  - command       : Bash command string ("" otherwise)
  - file_path     : Edit/Write/Read path ("" otherwise)
  - skill         : Skill name ("" otherwise)
  - output_excerpt: the paired tool_result text (bounded), "" if none

SAFETY
  Fail-open: any error returns []. Bounded tail read so a multi-MB transcript is
  never loaded in full on a latency-sensitive Stop.
"""
from __future__ import annotations

import json
from pathlib import Path

# One turn's tail is small; never load a multi-MB transcript in full.
_TAIL_BYTES = 1_000_000
# Bound each captured tool-result excerpt.
_EXCERPT_CHARS = 2000


def _result_text(content: object) -> str:
    """Extract plain text from a tool_result content field (str or block list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if isinstance(b.get("text"), str):
                    parts.append(b["text"])
                elif isinstance(b.get("content"), str):
                    parts.append(b["content"])
        return "\n".join(parts)
    return ""


def build_turn_tool_events(transcript_path: str) -> list[dict]:
    """Return the CURRENT turn's tool calls as flat-schema events. Fail-open."""
    if not transcript_path:
        return []
    try:
        p = Path(transcript_path)
        if not p.exists():
            return []
        size = p.stat().st_size
        with p.open("rb") as fh:
            if size > _TAIL_BYTES:
                fh.seek(size - _TAIL_BYTES)
                raw = fh.read().split(b"\n", 1)[-1]  # drop partial first line
            else:
                raw = fh.read()
        lines = raw.decode("utf-8", errors="ignore").splitlines()

        objs = []
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                objs.append(json.loads(ln))
            except Exception:
                continue

        # Map tool_use_id -> output excerpt from every tool_result in the tail.
        excerpts: dict[str, str] = {}
        for o in objs:
            msg = o.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        tuid = b.get("tool_use_id", "")
                        if tuid:
                            excerpts[tuid] = _result_text(b.get("content"))[:_EXCERPT_CHARS]

        # Find the current turn's start: the last real user prompt (a `user`
        # entry whose content is NOT a tool_result block).
        start = 0
        for i in range(len(objs) - 1, -1, -1):
            o = objs[i]
            if o.get("type") != "user":
                continue
            msg = o.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            is_tool_result = isinstance(content, list) and any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content
            )
            if not is_tool_result:
                start = i
                break

        # Collect assistant tool_use blocks from the current turn, in order.
        events: list[dict] = []
        for o in objs[start:]:
            if o.get("type") != "assistant":
                continue
            msg = o.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                name = b.get("name", "")
                inp = b.get("input", {}) or {}
                if not isinstance(inp, dict):
                    inp = {}
                events.append({
                    "name": name,
                    "command": str(inp.get("command", "") or ""),
                    "file_path": str(inp.get("file_path", "") or ""),
                    "skill": str(inp.get("skill", "") or ""),
                    "output_excerpt": excerpts.get(b.get("id", ""), ""),
                })
        return events
    except Exception:
        return []
