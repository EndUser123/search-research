# Handoff: /tp parallel lens panel + tp_dispatch.py + --detail flag

**Status:** OPEN — shipped with bugs fixed, needs live 3-lens end-to-end test + SKILL.md refactor  
**Created:** 2026-08-01  
**Source session:** 019fb177-e5d5-7520-92f5-0158f87639c9  
**Related:** `fleet-dispatch-improvements-20260731`, `premature-recommendation-pattern-20260801`

## Objective

The /tp skill was upgraded with a parallel lens panel (3 lenses: spawn + codex + agy firing simultaneously), a pre-packing dispatch helper (tp_dispatch.py), and a content-level extraction system (--detail flag on /packet's file_extractor.py). All shipped and committed. Needs live testing and SKILL.md size management.

## What was shipped (commits)

- `62fb4c7` — tp_dispatch.py (392 lines) + parallel panel SKILL.md rewrite
- `0becb3a` — --detail flag: signatures/structure/full extraction levels
- `f496e8b` — 4 bug fixes (invalid Python from structure extraction, module docstrings stripped, bundle/target not redacted, silent transcript fallback)
- `cff67e1` — mandatory pre-flight verification before skipping any lens
- `5049000` — wiki capture framing flip (skip→capture when in doubt)
- `3645183` — **5 HIGH review findings fixed** (see Revision 1 below)

## Open work

### 1. agy stream-json wrapper (NOT STARTED)
agy times out at 300s on long analytical prompts (GitHub issues #266, #594). The `--output-format stream-json` approach hasn't been tried. Build `~/.grok/skills/tp/__lib/agy_lens.py` — Python wrapper that captures stream-json, extracts agent_message, writes to file. Preserves context firewall. Pattern: `dgemma_read.py`.

### 2. /tp SKILL.md refactor (NOT STARTED — 92KB, largest skill)
Extract session-review protocol + explore directives into `reference/` files. Main SKILL.md should be ~15-20KB routing layer. Section analysis done: 226 lines for Step 2, 93 for explore directives, 92 for Step 3 synthesis — all candidates for extraction.

### 3. ~~Review findings H1-H5~~ (FIXED — commit `3645183`)
All 5 HIGH findings from `P:/.artifacts/review/tp-session-review/FINDINGS.md` are fixed and verified:
- H1: `_extract_py_structure` now handles module-level `if`/`for`/`while`/`with`/`match`/`try` (entry-point guards preserved)
- H2: SKILL.md CLI dispatch lane reconciled with parallel panel (no more contradiction)
- H3: `tp_dispatch.extract_file_sections` now emits stderr warning on ImportError
- H4: `tp_dispatch.extract_transcript_slices` exception messages wrapped in `redact()`
- H5: `--repo` normalized via `Path.resolve()` before subprocess call
- Receipts: 7 ast.parse-valid edge cases, 3 existing tests pass, both modified files produce valid structure output

### 4. Live 3-lens end-to-end test (BLOCKED by item 1)
Never ran all 3 lenses to completion in a single /tp invocation. agy timed out every time (3 attempts). Need the agy wrapper (item 1) to verify the full parallel panel works.

### 5. ~~Wiki concept: task-aware context detail levels~~ (REJECTED after assessment)
Assessed during /wiki run. The --detail flag is already documented in code comments and the /packet SKILL.md. A separate wiki concept would duplicate existing documentation. Not wiki-worthy per the quality gate (inferable from code).

### 6. MEDIUM review findings (9 items, M1-M9)
Not yet addressed. Most impactful: M1 (dead Try branch code — now fixed as part of H1), M8 (no tests for --detail flag). See FINDINGS.md for the full list.

## Acceptance criteria

1. agy_lens.py wrapper built and tested with a real /tp critique
2. /tp SKILL.md refactored to <30KB with reference/ files
3. ~~H1-H5 review findings fixed or triaged~~ (DONE — commit `3645183`)
4. At least one successful 3/3 lens parallel panel run documented

## Constraints

- Use agy properly (stream-json wrapper) before considering alternatives
- The premature-recommendation handoff applies: investigate before replacing

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-01 (early) | 019fb177... | created |
| 2026-08-02T04:00 | 019fb177... | updated — H1-H5 fixed (commit 3645183); item 5 rejected after wiki assessment; item 3 marked DONE; M1 noted as fixed via H1; added item 6 (MEDIUM findings) |

## Revision history

### Revision 1 — 2026-08-02T04:00Z — continued session 019fb177

- **Fixed:** H1-H5 review findings (commit `3645183` in `~/.grok`). All 5 HIGH findings from the /review are resolved with verification receipts (7 ast.parse-valid edge cases, 3 existing tests pass).
- **Rejected:** Item 5 (wiki concept for --detail flag) — assessed during /wiki and rejected as inferable from code. Not wiki-worthy.
- **Noted:** M1 (dead Try branch code) was incidentally fixed as part of H1. Remaining 8 MEDIUM findings still open.
- **Updated:** Item 4 (live 3-lens test) now explicitly blocked by item 1 (agy wrapper).
