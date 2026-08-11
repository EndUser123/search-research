---
thread_id: ship-py-pipeline-integration-gaps-20260810
parent_handoff_path: none
current_session_id: 019fe4c1-43c3-7432-b211-926e806dd7a6
produced_at: 2026-08-10T00:00:00Z
last_updated_at: 2026-08-10T00:00:00Z
status: OPEN
handoff_type: implementation_plan
---

# HANDOFF: ship-py pipeline integration gaps

## Status
OPEN — three integration gaps identified during ship-py-on-itself testing (session 019fe4c1).

## Objective
Close the three remaining integration gaps that prevent the ship-py pipeline from completing end-to-end in post-commit verification mode.

## Background

Session 019fe4c1 converted all 6 analysis phases to orchestrator-controlled dispatch, added provenance gates, dispatch accounting, and lazy imports. The pipeline now has working dispatch infrastructure (pi PATH resolution, shared dispatch_base.py, centralized empty-diff handling). But three gaps remain:

## Gap 1: Model pool expansion (critic lane)

**Problem:** `pick_model.py critic` returns only `nim-openai-gpt-oss-20b`. All DeepSeek variants are retired (`zen-deepseek-v4-flash-free`: lifecycle=retired) or serde-broken (`nim-deepseek-ai-deepseek-v4-flash`: fails via Grok Build spawn serde). The single eligible model returns `empty_response` on refactor/review prompts.

**Fix:** Either:
- Update the model pool registry to add eligible critic-lane models that are currently healthy
- Fix the serde issue for nim-deepseek-ai-deepseek-v4-flash (if fixable)
- Add `codex-opencode-go-deepseek-v4-flash` to the critic lane (it has quota: 0.7 headroom)

**Files:** `P:/.data/wiki/capabilities/critic-model-pool.md`, pick_model.py registry
**Acceptance:** `pick_model.py critic` returns ≥2 eligible models, at least one responds reliably to analysis prompts

## Gap 2: Chain reconciliation for session ID reuse

**Problem:** The tamper-evident transition chain in `_shared.py` assumes a single run-all execution. When detect is re-run on the same session ID (common during debugging), the chain has gaps and the verdict phase blocks with `TAMPER-EVIDENT CHAIN BROKEN`. This happened 5+ times during session 019fe4c1.

**Fix:** When run-all starts and the chain has gaps from prior detect calls, reconcile by accepting the latest genesis entry as the new chain start. The chain still catches external state manipulation (deleting state.json), but tolerates the legitimate re-detect pattern.

**Alternative:** Use a fresh session UUID for each pipeline run (operational discipline, no code change).

**Files:** `phases/_shared.py` (validate_transition_chain), `phases/run_all.py` (chain entry creation)
**Acceptance:** Re-running detect + run-all on the same session ID doesn't chain-break (the latest detect starts a fresh chain)

## Gap 3: Proper commit-range diff for build_diff_summary

**Problem:** `build_diff_summary` in `validator_dispatch.py` uses `git diff` (working tree). In post-commit verification mode, changes are already committed → `git diff` returns nothing. Current workaround: fall back to `HEAD~1..HEAD`, then to file-contents (cat the files). The workaround works but is suboptimal — file-contents sends the full file, not the diff, so the model sees the current state rather than what changed.

**Fix:** Store the session's commit range in detect phase state (e.g., `state["session_commit_range"] = "abc123..def456"`). In `build_diff_summary`, when post-commit mode is detected (`state["already_shipped"]`), use `git diff <session_commit_range>` instead of bare `git diff`.

**Files:** `phases/detect.py` (store commit range), `validator_dispatch.py` (use it in build_diff_summary)
**Acceptance:** Post-commit verification mode produces a real diff from the session's commits, not file-contents fallback

## What's already done (don't re-do)

All architectural fixes from session 019fe4c1 are shipped:
- pi PATH resolution (shutil.which)
- Provenance gate (check_provenance in dispatch_base.py)
- Dispatch provenance accounting (_dispatch_log at verdict)
- Centralized empty-diff handling (try_orchestrator_dispatch)
- Lazy phase imports (ship_orchestrator.py)
- Shared dispatch primitives (dispatch_base.py, -757 lines)
- Post-commit diff fallback (HEAD~1..HEAD + file-contents)

119 tests pass, ruff clean, all committed and pushed.

## Suggested next invocation

```
/go Read P:/docs/handoffs/ship-py-pipeline-integration-gaps-20260810/HANDOFF.md and implement gap 3 (commit-range diff) first — it's the root cause of the empty-diff cascade. Then gap 1 (model pool). Gap 2 (chain reconciliation) is lowest priority.
```
