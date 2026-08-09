# HANDOFF: close-py design — Python-orchestrated session close

## Status
OPEN — design needed

## Objective
Design close-py: a Python-orchestrated session close skill analogous to ship-py for publish-readiness. The operator stated this is planned.

## Context
- ship-py (at `~/.grok/skills/ship-py/`) is the existing Python-orchestrated verify-and-publish pipeline
- `/close` (at `~/.grok/skills/close/`) is the existing prose-based session close skill
- close-py would be the Python-controlled version of `/close`, applying the same anti-fabrication architecture developed for ship-py this session

## Key design questions
1. **What does close-py control that /close doesn't?** /close already has a scanner, accounting, and gate resolution. close-py would add: Python-controlled phase ordering, polling loop at judgment phases, anti-fabrication gates (suspicion gates, transition chain).
2. **Ship-py integration:** close-py should consume ship-py's verdict (SHIP DONE / SHIP VERIFIED / SHIP BLOCKED) as a signal. If ship-py was never invoked, close-py should note that but not require it.
3. **Shared anti-fabrication patterns:** the tamper-evident chain, suspicion gates, and polling loop pattern are reusable. Consider extracting to a shared `__lib/__anti_fabrication__` module that both ship-py and close-py import.
4. **What phases does close-py have?** Candidates: handoff-scan → wiki-capture → git-push-check → session-accounting → close-verdict.

## Acceptance criteria
- Design document produced via `/design`
- Reuses ship-py's polling loop and anti-fabrication patterns
- Consumes ship-py state as input
- Documents the integration contract between ship-py and close-py

## Suggested next invocation
```
/design close-py: Python-orchestrated session close consuming ship-py verdict, with anti-fabrication architecture
```

## References
- `~/.grok/skills/ship-py/` — existing pipeline to model after
- `~/.grok/skills/close/` — existing prose-based close skill
- `P:/.data/wiki/concepts/making-llm-agents-honestly-execute-skills-solution-stack.md` — anti-fabrication architecture
- `P:/.data/wiki/concepts/specification-gaming-in-llm-agent-pipelines.md` — specification gaming diagnosis

---

## Revision 1 — 2026-08-09T20:35:00Z (session 019fe664)

**Trigger:** auto-update — session 019fe664 ran preflight discovery on the close-py design topic and fixed the preflight tooling that was blocking the design phase.

**What changed since the original:**
- The preflight `discovery_audit.py` was broken (phantom conflicts from misclassified session-ledger JSON + silent inventory loss from unpruned venvs). It now works: `needs_review` on real signal, all scopes covered. The `/design` discovery phase for close-py can now run reliably.
- Ship-py's `validator_dispatch.py` had a deleted-file-hiding bug in `build_diff_summary` — fixed this session (commit `df72e52`). The diff summary that close-py would consume now includes deletions.
- Two wiki concepts written this session are directly relevant to close-py's design:
  - `[[denylist-drift-in-workspace-scanners]]` — close-py's scanner should use the allowlist classification model (default derived, source roots opt-in), not a denylist. The preflight fix demonstrates why.
  - `[[mechanical-tool-output-is-hypothesis-not-measurement]]` — close-py's gates should treat scanner output as a hypothesis requiring validation, not as a measurement. The 23.3%→2-6% correction in this session's evidence-correction scan is the canonical example.

**Updated evidence:**
- Preflight now returns `needs_review` (exit 2) on real signal for the close-py scope, not `blocked` on phantom conflicts
- Ship-py `build_diff_summary` now shows file deletions correctly
- Commits: `1166b27`, `6cd7817` (preflight fix + review fixes), `df72e52` (ship-py fix) — all on P:/ and ~/.grok main, pushed

**Status update:** unchanged — OPEN, design still needed. The blocking tooling issue is resolved; the design phase can proceed.

**New open items:** none beyond the original acceptance criteria.
