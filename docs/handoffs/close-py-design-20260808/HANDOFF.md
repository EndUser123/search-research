# HANDOFF: close-py design — Python-orchestrated session close

## Status
CLOSED — v1.0 implemented (session 019fee3d, commit b6434f8)

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

---

## Revision 2 — 2026-08-10T20:00:00Z (session 019fee3d)

**Trigger:** operator directed "we are going to create close-py based on the pattern in ship-py."

**What changed since Revision 1:**
- close-py v1.0 built and committed (`b6434f8` on ~/.grok main)
- 8-phase pipeline implemented: detect → scan → resolve(pause) → coverage → handoff-resolve(pause) → git-state → accounting(pause) → verdict
- Anti-fabrication architecture ported from ship-py: tamper-evident transition chain, inter-phase gates, mechanical verdict derivation (CLOSE COMPLETE / CLOSE INCOMPLETE)
- Consumes ship-py verdict as optional signal (design decision: optional, not required)
- Imports /close's `__lib__` scanners as dispatch targets (close_accounting, continuation_coverage)
- 20 tests passing (state management, chain validation, phase gates, verdict derivation, receipt validation)
- ruff clean, CLI verified (--help, detect --help, registry builds correctly)

**Design decisions (operator-confirmed):**
- Coexist with /close (not replace) — both import the same /close scanners
- ship-py verdict is optional signal (not required when code changed)
- Duplicate anti-fabrication patterns for v1 (shared `__lib/__anti_fabrication__` module deferred until close-py proves the pattern)

**Files created (18 total, 2994 lines):**
- `~/.grok/skills/close-py/SKILL.md` — skill definition with frontmatter, phase docs, gate matrix
- `~/.grok/skills/close-py/__lib/close_orchestrator.py` — CLI entry point with 10 subcommands
- `~/.grok/skills/close-py/__lib/close_receipt.py` — mechanical verification (validate_close_py_state, generate_receipt)
- `~/.grok/skills/close-py/__lib/phases/_shared.py` — state, gate, tamper-evident chain, session isolation
- `~/.grok/skills/close-py/__lib/phases/_registry.py` — PhaseSpec declarations (single source of truth)
- `~/.grok/skills/close-py/__lib/phases/{detect,scan,resolve,coverage,handoff_resolve,git_state,accounting,verdict,abort,run_all}.py`
- `~/.grok/skills/close-py/tests/{conftest,test_state_and_chain,test_verdict}.py`

**Status update:** CLOSED — implementation complete. The design questions from the original handoff are answered by the v1.0 implementation.

**Remaining work (deferred to future sessions):**
- Integration test end-to-end on a real session (detect → run-all → verdict on live evidence)
- Shared anti-fabrication module extraction (when ship-py + close-py pattern is proven)
- Stop hook integration (quality_gates frontmatter declared, hook not yet wired)
