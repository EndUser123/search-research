---
thread_id: 9d9c4a36-3e75-4989-a294-7ee9ec2b482a
parent_handoff_path: none
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: grok
produced_at: 2026-07-22T15:25:00+00:00
status: CLOSED
handoff_type: investigation
accurate_as_of_head: c629aa1f61ecfbdbaa2a4390d955c7a47605c880
---

# Handoff: Worktree workflow design for multi-terminal Grok Build (8 PRs)

## Objective

Implement the 8-PR design from the `/design` loop that resolves how to use git worktrees optimally across multiple concurrent Grok Build sessions, minimizing conflict and keeping worktrees clean.

## Status

OPEN — design doc complete (reviewer approved + critical friend PROCEED), implementation not started.

## Last user message (verbatim)

> /handoff new update www with youtube and ddg and other things we are missing.

(This handoff is triggered by the subsequent `/tp` audit request: "are we forgetting to document all our ideas plans actions to handoffs?")

## Producing context

- **Date:** 2026-07-22
- **Session:** `019f8082-9298-7561-b03e-3c21afc43115`
- **Design ID:** `6788cc35`
- **Design loop rounds:** 5 review rounds + 2 critical friend rounds → 0 open issues + PROCEED

## ✅ Design doc preserved (durable copy made)

The full design doc and all supporting artifacts have been copied from temp to durable locations:

| Artifact | Durable location |
|---|---|
| **Design doc** (12K words, 8 PRs) | `P:\docs\design\worktree-workflow-design-6788cc35.md` |
| Evidence brief (lossless compaction of wiki + skills + ADRs) | `P:\docs\design\worktree-workflow-design-6788cc35-supporting\evidence-brief.md` |
| Preflight brief (codebase inventory) | `P:\docs\design\worktree-workflow-design-6788cc35-supporting\preflight-brief.md` |
| Preflight inventory JSON (full audit) | `P:\docs\design\worktree-workflow-design-6788cc35-supporting\preflight-inventory.json` |
| Review file (5 rounds of findings) | `P:\docs\design\worktree-workflow-design-6788cc35-supporting\grok-design-review-6788cc35.md` |
| Critical friend critique (2 rounds) | `P:\docs\design\worktree-workflow-design-6788cc35-supporting\grok-design-critique.md` |
| Summary | `P:\docs\design\worktree-workflow-design-6788cc35-supporting\grok-design-summary-6788cc35.md` |

The temp originals (`C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\`) may still be reaped; the durable copies above are the source of truth.

## Key decisions (5)

| # | Decision | Rationale | Falsifier |
|---|---|---|---|
| 1 | **Single canonical root `P:/.worktrees/`** | Matches hook default; 2 of 10 worktrees already there; do NOT widen the hook | If `P:/packages/yt-is` starts running 5+ concurrent worktrees and naming collisions become a problem, may need per-package roots |
| 2 | **Library + script enforcement (`__lib/worktree_lib.py` + `grok-worktree.py` shell CLI), not a slash skill** | Per critical friend finding 1: user said "use the skills we have" — adding a 32nd skill inverts the conductor-vs-leaves relationship. The library is the blessed path existing skills import; the hook is the backstop. | If subagents reliably call `git worktree add` directly without going through the library, the design fails |
| 3 | **Auto-commit fail-closed in warn-mode initially; corpus-gated block-mode** | Gating invariant requires `measured_tp_on_corpus` before any new gate blocks | If corpus shows ≥1 true positive and operator declines to flip to block-mode, the design identified a real problem the operator chose to tolerate |
| 4 | **SessionStart hooks coordinate via `session_registry.jsonl` (no consolidation)** | The 24-hook problem is deferred as a separate workstream; registry is the source of truth | If the 24-hook problem creates actual race conditions, consolidation becomes necessary |
| 5 | **Cleanup is automatic at SessionEnd, not cron-driven** | SessionEnd fires reliably; cron on Windows is fragile; cleanup is <5s | If SessionEnd cleanup adds >10 seconds to session-end latency, may need background-task pattern |

## PR Plan (8 PRs, staged)

| Stage | PR | Title |
|---|---|---|
| 0 | **PR 1** | Fix stale artifacts + hook-health preflight (rewrite `worktree-workflow.md` rule, fix `grok-safe-git` wiki citation, add `hook_health_preflight.py`) |
| 0 | **PR 2** | Migrate 8 worktrees from `P:/.claude/worktrees/` to `P:/.worktrees/` via atomic `git worktree move`; delete 4 ghost dirs at `P:/worktrees/` |
| 1 | **PR 3** | Ship `WorktreeLib` library + `grok-worktree.py` shell CLI + remove dead-code mapping read + `cluster_check()` instrument |
| 1 | **PR 4a** | Skill mandate edits (text-only): `/handoff`, `/grok-route`, `/aar` Step 0.1 — explicit absolute-path mandate for durable writes inside worktrees |
| 1 | **PR 4b** | Skill behavior integration: `/grok-parallel` + `/go` import `WorktreeLib`; path-validator implementation |
| 2 | **PR 5** | `SessionEnd_worktree_cleanup.py` + `scan_worktree_writes()` (detects NEW + MODIFIED canonical-path violations) |
| 3 | **PR 6** | Warn-mode auto-commit gate with `measured_tp_on_corpus` requirement; heartbeat via every Stop hook (TTL=300s) |
| 4 | **PR 7** | ADR-008 amendment: document what shipped, what's deferred, the validation result from PR 6's corpus |

## Critical constraints addressed (8)

1. `P:` main is dirty with concurrent agent writes → PRs 3, 4, 6
2. Worktree root conflict (4 markers) → Decision 1 + PR 2
3. 24 SessionStart hooks uncoordinated → Decision 4 + PRs 3, 5
4. `auto-commit-authority-isolation` unimplemented → PR 6 (warn-mode)
5. Handoff writes inside worktrees → PR 4a mandate + PR 4b path-validator
6. Subagent enforcement gap (#78970) → documented as known limitation
7. Superpowers rototill overlap → clean scope boundary (deferred native-tool preference)
8. Gating invariant → PR 6 ships warn-mode with corpus requirement

## Read-first list

1. **`P:\docs\design\worktree-workflow-design-6788cc35.md`** — the full design doc (12K words, 8 PRs, algorithms, code snippets). Durably preserved.
2. `P:/.data/wiki/concepts/git-worktree-multi-terminal-best-practices.md` — external research synthesis (written this session)
3. `P:/docs/adrs/ADR-008-concurrent-session-worktree-isolation.md` — Layer 1 shipped, Layer 2 deferred
4. `P:/.claude/hooks/worktree_root_policy_PreToolUse.py` — primary enforcement hook
5. `P:/.claude/hooks/__lib/worktree_helper.py` — detection library

## Open decisions (from design doc, unresolved)

1. ADR-008 PowerShell scripts cited but don't exist — amend ADR or revive scripts?
2. `.worktreeinclude` content not verified — confirm in PR 1
3. Should `P:/.claude/.artifacts/session_registry.jsonl` use file locking for concurrent appends?
4. `/mmx` worktree interaction naming convention for codex bridge worktrees
5. Test-fixture worktrees — delete or preserve?
6. Operator workflow for orphan resolution (interactive prompt vs report-only)

## Dependencies

- **Requires:** nothing — can start immediately with PR 1
- **Blocks:** the broader worktree-per-session architecture (ADR-008 Layer 2)
- **Non-blocking to:** DiffusionGemma diagnosis (separate work stream), `/www` YouTube/DDG update (separate work stream)

## Other outstanding streams

- **DiffusionGemma spawn_subagent fix:** see `gemma-spawn-subagent-dgemma-diagnosis-20260722` handoff. Bug report drafted at `P:/docs/bug-reports/grok-build-nvidia-empty-content-20260722.md` (durable copy).
- **`/www` YouTube/DDG backends:** see `www-skill-add-youtube-ddg-backends-20260722` handoff.
