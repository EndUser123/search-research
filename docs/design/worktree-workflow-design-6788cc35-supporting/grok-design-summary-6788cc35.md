# Design Summary — Optimal Git Worktree Usage for Concurrent Grok Build Sessions

**Design document:** [`grok-design-doc-6788cc35.md`](grok-design-doc-6788cc35.md)
**Design run ID:** `grok-design-6788cc35`
**Date:** 2026-07-22
**Relates to:** ADR-008, ADR-009, wiki concept `git-worktree-multi-terminal-best-practices.md`

---

## What was produced

A comprehensive design document at `C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\grok-design-doc-6788cc35.md` covering the optimal use of git worktrees across concurrent Grok Build sessions on the `P:\` multi-root workspace. The document resolves all flagged conflicts, addresses all 8 critical constraints from preflight, addresses 21 Round 1 issues + 6 Round 2 issues + 19 cross-section stale references, and addresses 8 critical-friend findings (7 adopted, 1 engaged with push-back).

## Problem summary (from preflight + evidence briefs)

- **10 active worktrees across 3 competing roots:** 8 at `P:/.claude/worktrees/`, 2 at `P:/.worktrees/`, plus **4 ghost dirs at `P:/worktrees/`** (`pi-task-20260710-055243-t0bedit1`, `pi-task-20260710-133714-e8704c63-go`, `pi-task-20260710-155811-bd3038ab-go`, `yt-is-throughput-cadence-accounting`). The hook (`worktree_root_policy_PreToolUse.py`) defaults to `P:/.worktrees/` and is being flouted by history.
- **24 SessionStart hooks with no coordination contract:** `SessionStart_task_identity.py:129` reads worktree branch → task mapping, but no hook owns creation or cleanup.
- **Dirty main checkout:** `git -C P: status -s` shows concurrent agents writing directly to `main`. The symptom the user wants fixed.
- **Dead-code task-worktree mapping:** `SessionStart_task_identity.py:129` reads `.claude/task-worktree-mapping.json` — but the file does not exist on disk (verified 2026-07-22 via `Test-Path`); the read is **dead code** guarded by `if mapping_file.exists():`.
- **Stale artifacts:** `grok-safe-git` SKILL.md line 99 cites a wiki page that doesn't exist; `worktree-workflow.md` rule documents a `P:/worktrees/w*/projects/<pkg>/src/` shape that doesn't match runtime.
- **ADR-008 Layer 2 deferred:** auto-commit fail-closed gate never implemented; design must include it.
- **Subagent enforcement gap:** upstream #78970 means the hook only fires on main thread; subagents bypass it.
- **Missing `repo_root` field in session registry schema:** the `_other_session_active()` algorithm reads `entry.get("repo_root")` to filter concurrent activity to the same repo, but the schema didn't define the field — would have caused silent over-triggering on the multi-root workspace.
- **Fragile hook infrastructure:** `hooks_audit` flagged 10 SYNTAX errors and 470 state-GC items older than 30 days (2026-07-22). The design's coordination contract assumes hooks run cleanly.
- **3-day-old wiki concept** (`auto-commit-authority-isolation.md`, 2026-07-19): treated as authoritative policy but unvalidated as design foundation.

## Solution (one-paragraph)

Pick `P:/.worktrees/` as the single canonical root; introduce a deterministic naming convention (`<type>-<session6>-<slug>`); build `__lib/worktree_lib.py` (a Python library imported by existing skills — NOT a 32nd slash skill) plus a thin shell CLI dispatcher (`grok-worktree.py`) for operator convenience; extend `session_registry.jsonl` with worktree fields including `repo_root` (replacing the dead-code mapping read); migrate the 8 offending worktrees via `git worktree move`; add a `hook_health_preflight.py` preflight in PR 1 to surface the 10 syntax errors before downstream PRs; add `SessionEnd_worktree_cleanup.py` with worktree-write scan (both NEW + MODIFIED file detection); add `WorktreeLib.cluster_check()` to detect session-prefix clustering; ship a single auto-commit fail-closed gate in PR 6 (the former PreToolUse lease gate was folded here per critical-friend review — one gate, one corpus, one block-mode decision); annotate the wiki concept's validation status based on PR 6's calibration corpus.

## 8 PRs (staged rollout — down from 9 after critical-friend finding 2)

| PR | Title | Stage |
|---|---|---|
| **PR 1** | Fix stale artifacts + hook-health preflight (broken wiki citation + drift rule + dead-code mapping references + syntax-error detection) | Stale cleanup |
| **PR 2** | Migrate 8 worktrees from `P:/.claude/worktrees/` to canonical `P:/.worktrees/`; resolve locked `sessionend-test` via unlock + move; delete 4 ghost dirs | Stale cleanup |
| **PR 3** | `__lib/worktree_lib.py` library + remove dead-code mapping read + `cluster_check()` instrument (no new slash skill) | Library + skill infrastructure |
| **PR 4a** | Text-only skill edits: absolute-path mandates for `/handoff`, `/grok-route`, `/aar` | Library + skill infrastructure |
| **PR 4b** | Behavior integration: `/grok-parallel`, `/grok-safe-git`, `/go` import `WorktreeLib`; path-validator implementation in `__lib/path_validator.py` | Library + skill infrastructure |
| **PR 5** | `SessionEnd_worktree_cleanup.py` + cleanup pass + worktree-write scan (structural prevention) + session-registry retention sweep | Lifecycle hooks |
| **PR 6** | Auto-commit fail-closed gate (ADR-008 Layer 2, warn-mode; lease-gate semantics folded in) — single concurrent-write gate | Warn-mode enforcement |
| **PR 7** | ADR-008 amendment + design-doc archival + hook-environment dependency note + wiki concept validation status | Documentation |

Each PR is independently reviewable and mergeable. PRs 1-5 are non-blocking and can ship immediately; PR 6 ships in warn-mode and requires corpus calibration before any block-mode flip; PR 7 is documentation + ADR amendment conditional on PR 6's outcome. PR 4 is split into 4a (text-only) and 4b (behavior) per review Issue 7.3.

## Key architectural decisions (5)

1. **Single canonical root `P:/.worktrees/`** (not project-local `.worktrees/`) — matches hook default; matches 2/10 live worktrees; avoids per-package naming explosion in multi-root host.
2. **Library + script enforcement** (`__lib/worktree_lib.py` is primary; `grok-worktree.py` shell CLI is for operator convenience only) — per critical-friend finding 1, library pattern collapses 1 user-scope skill and removes the conductor-vs-leaves inversion. Subagent bypass (upstream #78970) is the primary workflow concern, not an edge case.
3. **Auto-commit fail-closed in warn-mode** with corpus-gated block-mode — respects the gating invariant in `P:/.claude/CLAUDE.md`. Single gate (lease-gate semantics folded in per critical-friend finding 2). Wiki concept `auto-commit-authority-isolation` is a 3-day-old hypothesis, validated via PR 6's corpus per critical-friend finding 6.
4. **SessionStart hooks coordinate via `session_registry.jsonl`** — no consolidation (separate workstream); registry is the source of truth. Hook-health preflight in PR 1 surfaces the 10 syntax errors and 470 state-GC items before downstream PRs cascade (per critical-friend finding 4).
5. **Cleanup automatic at SessionEnd** — not cron-driven; operator can preview via `grok-worktree cleanup --dry-run`. `cluster_check()` instrument ships in PR 3 (not retrofitted) per critical-friend finding 7.

## Alternatives considered

- **Always-worktree vs opt-in vs hybrid** — hybrid wins (trivial Q&A stays on main; multi-file work uses worktrees; auto-commit gate adds structural enforcement for residual case).
- **Single root vs per-package roots vs status quo** — single root wins (discoverability + bounded migration cost).
- **Hook enforcement vs convention-only vs library+script** — library+script wins (subagent coverage + skill integration ergonomics + cognitive-load reduction: no 32nd slash skill).
- **Auto-commit fail-closed vs worktree-only vs hybrid** — hybrid wins (defense-in-depth; some sessions will stay on main; gate covers residual).
- **8-PR library+gate design vs 5-PR structural-block alternative** — **8 PRs is optimal long-term** (per critical-friend finding 5, engaged with push-back). The 5-PR alternative doesn't address the 2026-07-19 canonical-path-writes failure mode (needs PR 4b's path-validator), uses block-by-default (violates gating invariant's warn-mode-first discipline), and structurally depends on the same registry the 8-PR design introduces. Design notes the operator can adopt the 5-PR alternative by deleting PR 4b + flipping PR 6 to block-mode from day one.

## Critical constraints addressed

| Constraint | Addressed by |
|---|---|
| **1.** Dirty main with concurrent writes | PRs 3, 4a, 4b (skill integration makes worktree the default path); PR 6 (warn-mode enforcement) |
| **2.** Worktree root authority conflict (4 markers) | Decision 1: `P:/.worktrees/` canonical; PR 2 migrates 8 offenders via `git worktree move` |
| **3.** 24 SessionStart hooks no coordination | Decision 4: registry is source of truth; PR 3 establishes; PR 5 adds cleanup owner. Failure-mode handling for hook-disabled/hook-failed/hook-slow added. |
| **4.** Auto-commit fail-closed NOT implemented | PR 6 implements with mandatory `repo_root` field in registry schema; warn-mode first per gating invariant. Single gate (lease semantics folded in). |
| **5.** Handoff writes inside worktrees don't mandate absolute paths | PR 1 fixes broken wiki citation; PR 4a adds explicit absolute-path mandate; PR 4b implements `WorktreeLib.validate_durable_write` in `__lib/path_validator.py`; PR 5 adds worktree-write scan for structural prevention (both NEW + MODIFIED file detection) |
| **6.** Subagent enforcement gap (#78970) | Decision 2: library mandate (`WorktreeLib` imported by existing skills); strengthened in §7 failure-mode prevention table as "PRIMARY WORKFLOW CONCERN, NOT EDGE CASE" per critical-friend finding |
| **7.** Scope-adjacent plan (superpowers rototill) | Explicit deferral: native-tool preference stays with superpowers; this design focuses on Grok Build layer |
| **8.** New gates need `measured_tp_on_corpus` | PR 6 ships warn-mode; corpus collected for ≥2 weeks; archive preserved postmortem; flips to block-mode only if TP ≥1. Wiki concept's validation status explicitly noted in PR 7. |
| **9.** Hook environment fragility (10 syntax errors, 470 state-GC items) | PR 1 adds `hook_health_preflight.py`; PR 7 documents hook-environment dependency in ADR amendment |
| **10.** Wiki concept unvalidated (3 days old) | §9 caveat added; PR 6 corpus is the validation step; PR 7 annotates validation result |
| **11.** Session-prefix clustering not instrumented | `WorktreeLib.cluster_check()` ships in PR 3; prefix-cluster-warnings.jsonl is the audit trail |
| **12.** `cmd_status` false-negative on staged-not-committed files | Acknowledged in §7 Security §3; PR 3 will incorporate `git diff --cached --name-only` check |

## Critical-friend findings addressed (Round 4)

| # | Finding | Action | Rationale |
|---|---|---|---|
| 1 | `grok-worktree` as slash skill | **Adopted** | Restructured as `__lib/worktree_lib.py` + `grok-worktree.py` shell CLI. No 32nd slash skill. |
| 2 | Two gates fire on same signal | **Adopted** | Dropped `PreToolUse_lease_gate.py`; folded into PR 6's auto-commit gate. 9 PRs → 8 PRs. |
| 3 | "Fix dormant mapping" framing wrong | **Adopted** | File does not exist; read is dead code. Removed dormancy framing. |
| 4 | Fragile hook infrastructure | **Partial** | Added `hook_health_preflight.py` to PR 1; documented dependency in PR 7. Did not fix unrelated 10 syntax errors (out of scope). |
| 5 | Simpler 5-PR alternative | **Pushed back** | 8-PR design is optimal long-term; engaged with 3-point technical argument in Alternative 5. |
| 6 | Wiki concept unvalidated | **Adopted** | Added §9 caveat; PR 6 corpus is the validation step; PR 7 annotates validation result. |
| 7 | Session-prefix clustering instrument | **Adopted** | `WorktreeLib.cluster_check()` ships in PR 3. |
| 8 | `cmd_status` staged-file false-negative | **Acknowledged** | Will be fixed in PR 3's status-check implementation; documented as known limitation. |

## Document state (final)

- **Design doc:** 1,071 lines, 14,428 words, 118 KB (after Round 1 + Round 2 + Round 3 sweep + Critical-Friend revisions)
- **Review doc:** 358 lines, ~7,500 words (Round 1 + Round 2 + Round 3 sweep revisions)
- **Critique doc:** ~440 lines, ~9,500 words (8 findings + Critical-Friend Response)
- **Summary doc:** this file

## Reviews performed

1. **Senior-staff review (Round 1):** 21 issues found, all addressed (2 HIGH, 9 MEDIUM, 10 LOW)
2. **Senior-staff review (Round 2):** 6 new issues found, all addressed (1 MEDIUM blocking, 5 LOW)
3. **Mandatory consistency sweep (Round 1.5):** 19 cross-section stale references fixed
4. **Mandatory consistency sweep (Round 2.5):** 2 wording clarifications
5. **Critical-friend review (Round 4):** 8 framing issues raised, 7 adopted + 1 engaged with push-back

**Status:** Approved for implementation, contingent on PR 6's calibration corpus determining whether the auto-commit gate becomes load-bearing policy or remains advisory.

## Provenance

- **Authoring skill:** design-run subagent (grok-design-6788cc35)
- **Operator:** Bruce Thomson (solo)
- **Design-run location:** `C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\`
- **Companion design runs:** `grok-design-6bf249df` (cross-model skill siblings), `grok-design-43e11106`
- **Verification receipts:** `verified 2026-07-22 via list_dir`, `verified 2026-07-22 via grep`, `verified 2026-07-22 via Test-Path`, `verified 2026-07-22 via hooks_audit`