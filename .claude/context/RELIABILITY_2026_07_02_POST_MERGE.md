# Agentic-Reliability — Post-Merge Stabilization Note

_2026-07-02 — short note after the A–F + `/go` preflight push. No new code in this commit; the purpose is to make the shipped state + the deliberately-deferred work + the recommended next task easy to find in 30 days._

## 1. What was pushed

**A–F agentic reliability (low-level safety rails + generated context)**

| Commit | Scope |
|---|---|
| `ef5f9a5` | PostToolUse.py wiring + 4 new hook files (PreToolUse search-before-create, SessionStart_repo_map, regen_repo_map, PreToolUse dispatch edits) |
| `21868e0` | PostToolUse.py + new `tests/test_existence_gate_repair.py` |
| `115a54c` | `PreToolUse_existence_gate.py` repair + new `__lib/agentic_reliability_telemetry.py` |
| `aa7f08e` | `PreToolUse.py` + `PreToolUse_existence_gate.py` + `tests/test_existence_gate.py` (+ the pre-existing settings.local drift, reverted in `5842a3c`) |
| `0ba3227` | Summary doc: `.claude/context/AGENTIC_RELIABILITY_AF.md` |
| `5842a3c` | Revert `.claude/settings.local.json` — drops 4 stale `cc-skills-sdlc/1.0.72` preflight permission entries |

Rollout discipline (still in force): all gates **telemetry-only by default**. `EXISTENCE_GATE_BLOCK=1` to promote read-before-edit to blocking once FP rate is measured via `agentic_reliability_telemetry.jsonl`.

**`/go --preflight-only` proposal mode (phase 1, reversible)**

| Commit | Scope |
|---|---|
| `dfa7d09` (submodule `cc-skills-sdlc`) | `scripts/preflight_propose.py` (new, stdlib-only deterministic generator) + `scripts/orchestrate.py` (`--preflight-only` flag + early-return branch in `orchestrate()` that runs BEFORE `load_or_create_task`) + 5 focused tests in `tests/test_orchestrate_dispatch.py` |
| `1ad87d1` (parent `packages/`) | Submodule pointer update capturing `dfa7d09` |

Behavior: writes run-scoped `task-proposal_<runid>.json` + `.preflight-proposed_<runid>` marker; rejects `--preflight-only` without `--prompt` (exit 2 + blocked sentinel); never dispatches, never mutates `active-task`. `agy` is never invented — only `pi`/`local`/`claude` (matches `VALID_DISPATCHES`).

## 2. What was intentionally NOT included

| Excluded | Why |
|---|---|
| Unrelated marketplace / skill churn (12 commits: `752d761`, `c7c7d33`, `c762cb2`, `3853471`, `a500bb7`, `47d2c05`, `ec791dc`, `61fc37f`, `459d00b`, `81c266d`, `d3dad64`, plus several submodule pointer updates) | Mixed in by the repo's pre-existing `auto_commit_hook` mid-session. Pushed with the rest (per your "push all 20; don't rewrite" instruction) but not authored by A–F or the preflight work. |
| Unknown `context_followup_detector.py` (commit `6b95646`, `.claude/hooks/UserPromptSubmit_modules/`) | Appeared this session, NOT written by my code; unknown authorship. Shipped inside the same auto-commit batch — flagged here so future review can investigate before relying on it firing on every user turn. |
| G — claim/validation telemetry probe | Different risk class: Stop-event response-text parsing, model-tier-gated quality machinery. Will be a low-blast telemetry probe FIRST (same pattern as read-before-edit + search-before-create), not in-place Stop-gate edits. |
| `/go` phase-2 — approval workflow / contract migration / planner-owned dispatch | Explicit non-goals of phase 1. The proposal artifact has no consumer yet — that is intentional ("generate on real prompts first, evaluate rewrite quality, then migrate architecture"). |

## 3. Current follow-up tasks

| # | Subject | Status | Purpose |
|---|---|---|---|
| **#1033** | G: claim/validation gap extension — scope decision | pending | Decision: telemetry probe (recommended) vs in-place Stop-gate edit. Will produce a tiny evidence ledger first (which existing Stop gates parse claim/validation text; where "registered/exists" is uncovered; where "not-run" should satisfy; telemetry event schema; why the probe is fail-open). |
| **#1034** | Fix `/go run_common_tail` test/source drift | pending | Pre-existing: 2 tests assert a 6-script tail sequence; source now runs 10 (`refactor-review.py`, `regression-runner.py`, `coverage-gate.py` were added later). Symptom: `At index 1 diff: 'refactor-review.py' != 'review-passes.py'`. Reliability concern: stale tests hide real source drift. |
| (new) | Sample 20 real `/go --preflight-only` prompts and inspect proposal quality | not yet created | This is the only way to know whether the deterministic rewrite is good enough to feed into phase 2. Heuristics are conservative by design; sample run will reveal FP/FN before any architectural commitment. |
| (new) | Decide whether rewritten prompts should become approval-gated execution inputs | not yet created | Gates phase 2 entirely. Should be a separate decision AFTER the 20-prompt sample is reviewed. |

## 4. Recommended next task: **#1034**

Start with `/go run_common_tail` test/source drift, because stale tests are a reliability problem and should be cleaned **before** building more `/go` behavior. Specifically:

1. **Prevents the drift from compounding.** `/go` is the orchestrator under active development (we just added preflight; phase 2 is queued). Each new gate that lands without updating the test expectations increases the surface area of "the test suite lies about how this orchestrator runs".
2. **Cheap to fix right now.** The two affected tests are well-isolated; the actual fix is updating the call-sequence assertions to the canonical 10-script order: `verify-task → simplify (if diff) → refactor-review → regression-runner → review-passes → run-qa-verification (--dry-run if `GO_QA_DRY_RUN=1`) → mutation-gate → coverage-gate → pr-artifacts → loop-check`. The per-test simplify SKIP/PASS marker checks stay intact.
3. **Unblocks confident refactoring of `/go`.** Once the tail-test expectations match reality, future changes to `run_common_tail` (e.g. adding a new gate for the proposal artifact, or wiring in the phase-2 approval workflow) get tested against a faithful baseline rather than a frozen snapshot of an older shape.
4. **Not in scope today, but cheap to keep honest.** Doing it now means the 20-prompt preflight sampling (next task) and the G telemetry probe (after that) both land against a green orchestrator test suite, so failures point at real bugs rather than background drift.

The full evidence (problem / situation / symptom / fix recipe) is already in task #1034's description from when it was created this session. Re-confirmed here for the record.

## Branch / push state (as of this note)

- All 20 unpushed commits pushed across 8 repos. No history rewrite.
- All affected repos clean against their `origin/main` (verified via `git status -sb`).
- The 4-repo `Stop.py` modification now visible in working trees is the `auto_commit_hook` capturing the most recent in-session edit; it is uncommitted, not a separate push, and will be swept into the next auto-commit.
- No pyc, no state/, no generated/, no cache/ artifacts in any push.
- Generated repo map (`repo_map.generated.*` + `canonical_paths.generated.md`) correctly gitignored; regenerates on SessionStart via mtime-guarded hook.