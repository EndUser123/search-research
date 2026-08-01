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

## Open work

### 1. agy stream-json wrapper (NOT STARTED)
agy times out at 300s on long analytical prompts (GitHub issues #266, #594). The `--output-format stream-json` approach hasn't been tried. Build `~/.grok/skills/tp/__lib/agy_lens.py` — Python wrapper that captures stream-json, extracts agent_message, writes to file. Preserves context firewall.

### 2. /tp SKILL.md refactor (NOT STARTED — 92KB, largest skill)
Extract session-review protocol + explore directives into `reference/` files. Main SKILL.md should be ~15-20KB routing layer. Section analysis done: 226 lines for Step 2, 93 for explore directives, 92 for Step 3 synthesis — all candidates for extraction.

### 3. Review findings from /review (5 HIGH findings at P:/.artifacts/review/tp-session-review/FINDINGS.md)
- H1: _extract_py_structure strips module-level control flow (if __name__, conditional imports)
- H2: SKILL.md contradicts itself on what CLI lenses return
- H3: ImportError silently returns empty
- H4: Exception messages bypass redaction
- H5: --repo default "P:/" fragile

### 4. Live 3-lens end-to-end test
Never ran all 3 lenses to completion in a single /tp invocation. agy timed out every time (3 attempts). Need to verify the full parallel panel works.

### 5. Wiki concept: task-aware context detail levels
The --detail flag pattern (signatures/structure/full) is transferable to any skill that packs context for cross-model dispatch. Not yet captured.

## Acceptance criteria

1. agy_lens.py wrapper built and tested with a real /tp critique
2. /tp SKILL.md refactored to <30KB with reference/ files
3. H1-H5 review findings fixed or triaged
4. At least one successful 3/3 lens parallel panel run documented

## Constraints

- Use agy properly (stream-json wrapper) before considering alternatives
- The premature-recommendation handoff applies: investigate before replacing
