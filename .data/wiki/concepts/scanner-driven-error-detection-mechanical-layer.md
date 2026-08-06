---
title: "Scanner-driven error detection: mechanical layer for workspace quality"
created: 2026-08-03
source: session-019fc79f
sources:
  - internal: C:\Users\brsth\.grok\skills\todo\__lib\scan_functions.py
  - internal: design-821c4024
tags: [scanner, error-detection, mechanical-layer, quality, todo, class-c, shell-quoting]
host: grok
agent: grok
verification: observed
cognitive_load: 2
summary: >
  Extending the /todo scanner with mechanical error-pattern sources is effective
  for detectable patterns (dangerous python -c, json+inline-parse, tool failures,
  protocol violations) but cannot catch LLM-judgment errors without a separate
  LLM orchestrator layer. The split is: mechanical layer always-on (pure Python,
  <3s), LLM layer opt-in via --quality flag (subprocess, <90s). Key design
  decision: scanner stays pure Python (no LLM imports), LLM layer is a sibling
  module invoked as subprocess.
---

# Scanner-driven error detection: mechanical layer for workspace quality

## The split

| Layer | What it detects | How | Latency | Always-on? |
|-------|----------------|-----|---------|------------|
| Mechanical | Dangerous code patterns, tool failures, protocol violations | grep/regex on files + transcript | <3s | Yes |
| LLM | False diagnoses, over-engineering, defensive responses, position reversals | Subagent analyzes transcript | <90s | No (`--quality` flag) |

## What mechanical detection catches

1. **`scan_dangerous_python_c`** — `python -c` with nested f-string quotes in skill files. This is the Class C pattern that caused 29 historical shell-quoting failures. Pattern: `python\s+-c.*f['"].*(?:\[\\"|\\')` with DOTALL.

2. **`scan_json_inline_parse`** — `--json` + `python -c` within 200 chars in skill docs. Catches the instruction pattern that forces the model into inline JSON parsing (the exact trigger that caused this session's original errors).

3. **`scan_tool_failures`** — Non-zero exits, max_tokens truncation, timeouts in the session transcript. Excludes expected failures (pytest, ruff, pyright, mypy, unittest).

4. **`scan_skill_protocol_violations`** — Skill invoked without SKILL.md read within 5 turns. Uses the skill catalog for known skill names to avoid false positives.

## What mechanical detection cannot catch

Errors 5-10 (false diagnosis, over-engineering, propagated unverified claims, defensive response, position reversal, over-processing) require LLM judgment. No regex can reliably catch "defensive response" or "over-processing."

## Key design decisions

### DEC-01: Scanner stays pure Python
No LLM imports in `scan_functions.py`. Standard library + sibling-module imports only. This preserves the scanner's determinism and fast-path guarantee.

### DEC-02: LLM layer is subprocess, not in-process import
`scan_session_quality.py` is invoked as a subprocess, not imported. This isolates LLM failures from mechanical failures — if the LLM layer crashes, the mechanical layer still works.

### DEC-03: LLM scan is opt-in
Default-off via `--quality` flag. The operator's primary use case for `/todo` is a quick action list; quality errors are worth finding but only when the operator has time to digest them.

### DEC-04: SCANNER_REGISTRY as single source of truth
Consolidated the duplicated `scanners` list and `scanner_map` dict. Adding a new source now requires touching 2 places (function + registry entry) instead of 4 (function + list + dict + SKILL.md table).

## Anti-patterns avoided

- **Inline `python -c` for JSON parsing** — the original /todo SKILL.md instructed `--json` + inline parse, which is the Class C hazard. Fixed by running scanner without `--json`.
- **Hardcoded session paths** — `scan_wiki_markers` used `P%3A%5C` which misses ~10% of sessions. Fixed by using `_find_session_dir()` from `scan_transcript.py`.

## Falsifier

This approach is wrong if:
- The mechanical sources produce >5% false positives on legitimate workspace patterns
- The LLM layer consistently produces unactionable noise
- Operators stop using `/todo` because the quality findings drown the signal

## Related

- [[class-c-shell-quoting-29-instances]] — the historical failure pattern the scanner detects
- [[shell-to-python-orchestration-threshold]] — when to extract from shell to Python
- [[structural-enforcement-for-skipped-rules-grok-build-2026]] — why prose rules don't fire under pressure
