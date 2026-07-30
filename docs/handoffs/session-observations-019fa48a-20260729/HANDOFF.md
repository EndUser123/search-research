# Session Observations: 019fa48a (2026-07-29, post-compaction continuation)

**Status:** OPEN — observations captured. All work shipped, reviewed, and committed.
**Date:** 2026-07-29

## Session arc

| Topic | Outcome | Commits |
|-------|---------|---------|
| AGENTS.md refactor | 1,679→620 lines (63% cut). Claude compat disabled. | Pre-compaction |
| Receipt-loop fix | quality_gate.py capability derivation fixed | Pre-compaction |
| Behavioral hook fixes | lastAssistantMessage payload bug in behavioral_check + wiki_persistence_check | Pre-compaction |
| /design run d8173a98 | Search-before-proposing hook design, 59 findings, 3 rounds, CF PROCEED | `740761c` (skill fixes) |
| PGM payload bug fix | PGM silently dead since ship. Fixed. 117/117 tests. | `0f5ce16` |
| Design skill workflow fixes | 5 failure modes fixed in design SKILL.md + tool-fallbacks | `740761c` |
| Behavioral FP tuning | 19+5 false positives eliminated, 5 patterns narrowed | `60450b8` |
| /check | PASS — both verifiers confirmed | — |
| /review | 7 findings (2 bugs, 5 risks) — all fixed | `0ab0e09`, `6cfc5fb`, `a0ec600` |
| Wiki concepts | 5 concepts created | `e0da76b`, `249aacc`, `a0ec600`, `f006a54` |
| OQ-9/OQ-10 resolved | Proxy labels + tracking-only operator_directive | `b87b7fc` |

## Shipped artifacts

### Code changes (~/.grok)
- `plugins/proposal-grounding-monitor/scripts/stop_detect.py` — 5-tier payload extraction
- `plugins/proposal-grounding-monitor/tests/test_stop.py` — camelCase test fixture
- `plugins/proposal-grounding-monitor/tests/conftest.py` — make_stop_payload uses lastAssistantMessage
- `hooks/scripts/behavioral_check.py` — narrowed FP-prone patterns, added missing phrasings
- `skills/design/SKILL.md` — 5 workflow failure fixes
- `tool-fallbacks.md` — gemini-2 404 + MiniMax-M3 resume truncation

### Handoffs
- `pgm-payload-fix-and-scope-extension-20260729` — Units 1 shipped, 2-5 ready, OQ-9/10 resolved, review fixes applied

### Wiki concepts (5)
- `stop-hook-lastassistantmessage-payload-field-2026` — canonical 4-tier extraction pattern
- `advisory-vs-blocking-enforcement-decision-2026` — measurement-first strategy
- `regex-cannot-detect-context-dependent-behavioral-patterns` — structural regex limitation
- `multi-subagent-orchestration-workflow-failure-patterns` — 5 failure modes from /design run
- `silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap` — PGM silently dead, fleet monitoring gap

## Observations

1. **Three hooks had the same payload bug** — systematic, not one-off. Code ported from Claude Code (snake_case) to Grok Build (camelCase) without verifying the payload contract.
2. **PGM was silently dead for its entire production life** — 117 tests passed, config enabled, but every real session produced zero detections. No fleet monitoring caught it.
3. **The /design critical friend caught the framing was wrong** — "mechanical enforcement" was incorrect; the design delivers advisory + measurement infrastructure. Blocking is Phase 4.
4. **Behavioral FP tuning eliminated 24 false positives** — FABRICATED_FATIGUE matched "session" + "complete" in any context; NARRATIVE_CLOSURE fired on /close reports where the phrase is correct.
5. **Design skill writer spawned read-only** — silently failed to persist. Fixed by adding capability warning to SKILL.md.

## What a fresh session should know

- PGM is now LIVE for the first time. Fleet will see advisory systemMessages.
- Behavioral check FP rate should drop dramatically (42 detections → ~5-8 expected).
- PGM Units 2-5 are ready for implementation (see handoff).
- The design doc is in temp at `C:\Users\brsth\AppData\Local\Temp\grok-design-d8173a98\` — will be reaped by OS.
