---
thread_id: close-py-v1-followup-20260810
parent_handoff_path: P:/docs/handoffs/close-py-design-20260808/HANDOFF.md
current_session_id: 019fee3d-50cb-7553-83c6-558c06919132
current_terminal_id: console_16799b2f-5107-4491-a937-1794
produced_at: 2026-08-11T01:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 09900033069e30c89507329314e5f7f98428dde8
---

# HANDOFF: close-py v1.0 follow-up work

## Status
OPEN — follow-up tasks from the close-py v1.0 build

## Objective
Complete the follow-up work from the close-py v1.0 build: integration test against real /close scanner output, Stop hook quality_gates registration, and fresh-eyes review of the anti-fabrication code.

## Context
- close-py v1.0 was built and committed this session (`b6434f8` on ~/.grok). The design+build is complete (parent handoff CLOSED).
- The AAR identified 3 opportunities: O2 (integration test, ACT_NOW), O3 (Stop hook, INVESTIGATE), O1 (pattern capture, DEFER — already done via wiki concept).
- The /insight scan confirmed the same items as open work.
- The Stop hook is currently blocking session close because `/review` hasn't run on close-py (no `grok-review/**/_run.json` evidence).

## 1. Objective (one sentence)
Verify close-py end-to-end against real /close scanner output, register its quality_gates Stop hook, and review the anti-fabrication code.

## 2. Verified facts (with source paths)
- [FACT] close-py v1.0 is committed at `b6434f8` on ~/.grok main, pushed. 18 files, 20 tests passing, ruff clean. (source: git log)
- [FACT] The scan phase imports `close_accounting.scan_all`, `resolve_gates`, `compute_loop` from /close's `__lib__` but no test exercises these against real evidence. (source: `~/.grok/skills/close-py/__lib/phases/scan.py`)
- [FACT] SKILL.md declares `quality_gates` frontmatter checking for `P:/.artifacts/close-py/*/state.json`, but no Stop hook reads it. (source: `~/.grok/skills/close-py/SKILL.md` frontmatter)
- [FACT] ship-py's quality_gates are registered via `~/.grok/hooks/scripts/quality_gate.py` — close-py needs the same registration pattern. (source: `~/.grok/hooks/scripts/quality_gate.py`)
- [FACT] The Stop hook blocked session close with: `[review] /review run manifest missing — run /review before claiming review done`. (source: Stop hook feedback in session)

## 3. What now works
close-py v1.0 is built and unit-tested — state management, tamper-evident chain, inter-phase gates, verdict derivation, and receipt validation all work in isolation. The 8-phase pipeline structure is sound. The skill is registered in the catalog and invocable as `/close-py`.

## 4. Acceptance criteria
- [ ] **CF-01: Integration test.** Run `python ~/.grok/skills/close-py/__lib/close_orchestrator.py detect --session-id <UUID>` followed by `scan` on a real session. Verify the scan phase produces valid gate states (not an import error or API mismatch).
- [ ] **CF-02: Stop hook registration.** Register close-py's `quality_gates` in `~/.grok/hooks/scripts/quality_gate.py` (or wherever ship-py's are registered). Verify the Stop hook reads close-py's state.json and enforces the completion gate.
- [ ] **CF-03: Fresh-eyes review.** Run `/review` on the close-py skill to satisfy the Stop hook gate and catch edge cases the author missed (polling loop, gate logic, chain validation).

## 5. Open decisions
1. **How does quality_gate.py register per-skill gates?** Read `~/.grok/hooks/scripts/quality_gate.py` to understand the registration mechanism. Is it automatic (reads all SKILL.md frontmatter) or manual (per-skill code entry)?
2. **Should the integration test be a pytest or a manual CLI invocation?** Pytest is better for regression; manual CLI is faster for first verification.

## 6. Suggested skills
- `/review` — fresh-eyes review of close-py (satisfies Stop hook gate + catches edge cases)
- `/check` — verify close-py detect+scan against real session state

## 7. Read-first list
1. `~/.grok/skills/close-py/SKILL.md` — skill definition, phase docs, gate matrix
2. `~/.grok/skills/close-py/__lib/phases/scan.py` — the scan phase that imports /close's scanners
3. `~/.grok/skills/close-py/__lib/phases/verdict.py` — verdict derivation logic
4. `~/.grok/hooks/scripts/quality_gate.py` — how ship-py's quality_gates are registered (for CF-02)
5. `~/.grok/skills/close/__lib/close_accounting.py` — the scanner API close-py imports (verify signatures match)
6. `P:/.data/wiki/concepts/python-orchestrated-skill-build-pattern-study-replicate-test.md` — the build pattern (context for how close-py was structured)
7. `P:/docs/handoffs/close-py-design-20260808/HANDOFF.md` — parent handoff (CLOSED, documents the full build)

## 8. Other outstanding streams
- **Shared anti-fabrication module extraction** — deferred to v2, triggers when a 3rd Python-orchestrated skill confirms the pattern. Documented in the wiki concept's falsifier. No handoff needed — the trigger condition is clear.

## 9. Falsifier
This handoff is wrong if close-py's scan phase works correctly against real /close scanner output on the first try (CF-01 passes immediately), the Stop hook is already registered (CF-02 is unnecessary), or the review finds no issues worth fixing (CF-03 is just a gate-satisfier).

## Last user message (verbatim)
"/handoff"

## Suggested next invocation
```
/go Execute close-py v1.0 follow-up: (1) run detect+scan on this session to verify integration, (2) register quality_gates Stop hook, (3) run /review on close-py. Read P:/docs/handoffs/close-py-v1-followup-20260810/HANDOFF.md for details.
```
