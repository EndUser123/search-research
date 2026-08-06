---
title: "/todo error-pattern scanner extension — design 821c4024"
created: 2026-08-03
last_updated_at: 2026-08-03T21:05:00Z
status: OPEN — mechanical sources shipped, LLM layer + tests deferred
assignee: unassigned
session: 019fc79f-8091-77d0-afa6-838855c700c7
---

# /todo Error-Pattern Scanner Extension

## Goal

Extend the `/todo` workspace scanner to detect the 10 error patterns observed in session 019fc79f, so `/todo` surfaces those errors alongside existing open-work items.

## What's done

### Shipped (committed to ~/.grok)

1. **SCANNER_REGISTRY consolidation** (commit `aae46d0`) — unified the duplicated `scanners` list and `scanner_map` dict into a single `SCANNER_REGISTRY`. Fixed latent bug where `transcript` was in scanners list but not scanner_map.

2. **4 new mechanical scan sources** (commit `aae46d0`):
   - `scan_dangerous_python_c` — greps skill files for `python -c` with nested f-string quotes
   - `scan_json_inline_parse` — flags `--json` + inline `python -c` in skill docs
   - `scan_tool_failures` — scans transcript for non-zero exits, max_tokens, timeouts
   - `scan_skill_protocol_violations` — flags skill invocations without SKILL.md reads

3. **Step 3.6 inline python -c removed** (commit `62698fe`) — replaced dangerous `python -c` with per-source scanner calls

4. **Step 0 `--json` removed** (commit `3d05e27`) — scanner runs without `--json`, prints formatted output directly

5. **scan_wiki_markers path fix** — now uses `_find_session_dir()` instead of hardcoded `P%3A%5C`

6. **Multiple follow-up fixes** from sibling sessions:
   - `b90c6ba` — multi-terminal isolation (return empty instead of scanning all)
   - `4b68ddb` — json_inline_parse scanner precision (require pipe character)
   - `0c06ba6` — 4 review bugs (regex, path exclusion, marker threshold, None debt)
   - `533a3eb` — cross-source dedup
   - `fd20f5a` — consolidated to single renderer

## What's not done

### Unit 6: LLM orchestrator (`scan_session_quality.py`)

New sibling module that analyzes transcript for 6 LLM-judgment error patterns (false diagnosis, over-engineering, propagated unverified claims, defensive response, position reversal, over-processing). Invoked as subprocess via `--quality` flag. Design doc has full spec.

**Decision needed:** None — design approved (Path B). Implementation is mechanical.

### Unit 7: `/todo --quality` flag

Wires the LLM orchestrator into the `/todo` skill. Adds `--quality` to help text, Step 0, and RNS renderer mapping.

### Unit 8: Tests

Unit tests for the 4 new mechanical sources (positive + negative examples) and integration smoke test. Disposition: HANDOFF (design proposed; operator schedules deliberately).

### Open config decisions

- **DEC-07:** Confidence threshold (default 0.6) — tune after shadow mode
- **DEC-08:** `GROK_QUALITY_MODEL` — start with `parent`, switch to `agy` if same-model misses errors

## Design document

Full design doc at `C:\Users\brsth\AppData\Local\Temp\grok-design-821c4024\grok-design-doc-821c4024.md` (54KB, Revision 2). **This will be reaped by OS.** Key decisions are captured in this handoff.

## Acceptance criteria (for remaining work)

1. `scan_session_quality.py` exists at `~/.grok/skills/todo/__lib/scan_session_quality.py`
2. `GROK_QUALITY_MODEL=disabled` triggers fail-open path (returns `[]` + warning)
3. `python scan_functions.py --source dangerous_python_c` finds 0 hits on fixed /todo SKILL.md
4. `python scan_functions.py --source json_inline_parse` finds the 4 real instances in other skills
5. `python scan_functions.py --source tool_failures` finds the max_tokens truncations from this session
6. `python scan_functions.py` (all sources) runs in <3s on warm cache
7. `/todo --quality` runs LLM layer in <90s target / 120s ceiling

## How to verify what's shipped

```powershell
# All 15 sources should be registered
python ~/.grok/skills/todo/__lib/scan_functions.py --source dangerous_python_c
python ~/.grok/skills/todo/__lib/scan_functions.py --source json_inline_parse
python ~/.grok/skills/todo/__lib/scan_functions.py --source tool_failures
python ~/.grok/skills/todo/__lib/scan_functions.py --source protocol_violation

# Full scan should include new sources
python ~/.grok/skills/todo/__lib/scan_functions.py
```

## References

- Design doc: `grok-design-821c4024` (temp, will be reaped)
- Source commit: `aae46d0` in `~/.grok`
- Session: `019fc79f-8091-77d0-afa6-838855c700c7`
