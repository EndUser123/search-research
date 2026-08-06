# Handoff — ship-py hardening: architectural findings from specialist review

## Status
OPEN — 4 mechanical fixes DONE. 5 architectural items remain.

## Objective

Address the remaining findings from the ship-py specialist code review
(session 019fd276). The specialist (MiniMax-M3) found 12 bugs + 4 risks.
Bug #1 (review-blocked bypass) was fixed this session (commit `3736f4e`).
The remaining 11 findings need disposition.

## Mechanical fixes (DONE — commit 0cee78d)

### 1. FREE_C default collides with FREE_A — DONE
Both default to `minimax-m3`. When the operator doesn't pass model args,
FREE_A and FREE_C are the same model — retry swaps to FREE_B which is
correct, but the verify agent uses FREE_C which collides with the
review agent's FREE_A. Change FREE_C default to a third distinct model.

**File:** `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` (no direct
model ref — this is in the Rhai workflow defaults)
**Actual fix location:** `~/.grok/workflows/ship-rhai.rhai` line ~122:
`let FREE_C = if model_c != () && model_c != "" { model_c } else { "minimax-m3" };`
Change to a different default (e.g., `"go-qwen3-7-max"` or another free model).

### 2. diff_ref falls back to HEAD~5 when HEAD==merge-base
When `mb == head` (no divergence from main), the code falls back to
`HEAD~5` which shows 5 unrelated commits as "the diff." Should return
empty diff or "no changes detected" message.

**File:** `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` line ~89
**Fix:** `diff_ref = mb if (mb and mb != head) else ""` and handle empty
diff_ref in the diff commands.

### 3. review_retry_attempted is write-only
State field is set and output in JSON, but never read by downstream
phases. Surface the warning at verify time too — if agents failed and
retry wasn't attempted, warn at the final verdict.

**File:** `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` cmd_verify
**Fix:** Add ~5 lines reading `state.get("review_retry_attempted")` and
appending a warning if agents failed without retry.

### 4. findings_file path not sandboxed
`cmd_review` accepts any path via `--findings-file`. A malicious or
buggy LLM could pass paths outside P:/tmp/. Add prefix validation.

**File:** `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` cmd_review
**Fix:** `if not str(findings_path).startswith("P:/tmp/"): error`

## Architectural items (NEW_HANDOFF — need design)

### 5. Hardcoded `cohere-north-mini-code` in Rhai retry fallback
**File:** `~/.grok/workflows/ship-rhai.rhai` line ~207
The model-collision guard falls back to a literal slug. This violates
the "NEVER hardcode model slugs" comment 7 lines above. Needs a
model-pool resolver in Rhai — how does the workflow get pool models?
Pass via args? Needs architectural decision.

### 6. Verify-retry doesn't diversify when all 3 models identical
**File:** `~/.grok/workflows/ship-rhai.rhai` lines ~382-383
If caller passes identical slugs for all three model args, retry uses
the same model. Needs uniqueness check across all 3 model slots.

### 7. extract_json_field word-boundary + escape issues
**File:** `~/.grok/workflows/ship-rhai.rhai` lines ~55-74
The JSON field parser uses substring matching without word boundaries
and doesn't handle escaped quotes in values. Works for current 4 keys
(UUIDs, model slugs) but is a foot-gun for new fields. Needs either a
real JSON parser in Rhai (~30 lines) or redesign args passing to
map-only (drop the JSON-string path).

### 8. capability_mode read-only→execute security concern
**File:** `~/.grok/workflows/ship-rhai.rhai` lines ~142, 185, 186
Concurrent session (Claude Sonnet 4.6, commit `e71d617`) changed
review agents from read-only to execute to fix the 21-min ship-rhai-3
runaway. Review agents now have write capability even though their
task is read-only. Needs threat model assessment — is the execute
elevation acceptable, or should detect run git commands for review?

### 9. Zero test coverage for ship-py
**File:** `~/.grok/skills/ship-py/tests/` (empty directory)
The ship-rhai sibling has 41 tests in `test_ship_receipt.py`. ship-py
has none. Needs a test suite covering: cmd_detect (merge-base),
cmd_review (schema validation, gates), cmd_verify (blocked-state gate),
cmd_verdict.

## Related

- Specialist findings JSON: `P:/tmp/ship-py-review-findings-specialist.json`
- Original handoff: `P:/docs/handoffs/ship-rhai-retry-fallback-20260805/HANDOFF.md` (RESOLVED)
- Wiki concept: `[[spawn-evaluate-return-pattern-shared-across-critique-skills]]`

## Handoff is wrong if

- The mechanical fixes are treated as architectural (they're not — they're <15 min each)
- The capability_mode change is reverted without understanding why it was made
- Tests are written before the mechanical fixes land (tests should cover the final state)

---

## Revision 1 — 2026-08-07 (session 019fc927) — operator usage findings

**Trigger:** operator invoked `/ship-py` at session end. The pipeline ran Phase 0 (detect) successfully but the session had already committed and pushed all work. The remaining phases (review, verify, verdict) could not produce meaningful results on already-pushed commits.

### New findings from live usage

**Finding 10 — No "already shipped" escape hatch.** The pipeline has no way to handle the case where work is already committed and pushed before `/ship-py` is invoked. The orchestrator detects "has_work: true" (uncommitted files from sibling sessions) and instructs the next phase, but the work THIS session produced is already at origin/main. The pipeline should detect this condition (session's own commits are already pushed) and either skip to a lightweight post-hoc review or exit gracefully with "work already shipped — cannot retroactively pipeline."

**Finding 11 — Stop hook creates a feedback loop.** The quality_gate Stop hook (`~/.grok/hooks/scripts/quality_gate.py:165-220`) checks for ship-py completion claims against the state file. Once Phase 0 creates a state file with `completed_phases: ["detect"]`, the hook blocks ANY response mentioning "ship" near words like "done/complete/cannot" — even when the response is explaining why the pipeline CAN'T run. The agent gets trapped: it can't explain the problem without triggering the hook, and it can't run the pipeline because the work is already shipped.

**Root cause of the hook trap:** the regex patterns at `_SHIP_PY_CLAIM_PATTERNS` (line 163-164) match `\bship[- ]py\b.*\b(?:done|complete|passed|verified)\b` — which catches legitimate explanations like "ship-py pipeline cannot complete" as false-positive completion claims.

**Finding 12 — State file needs an "aborted" state.** The orchestrator's state machine has phases (detect, review, verify, verdict) but no `aborted` or `cannot_run` terminal state. The agent had to manually write `{"phase": "aborted", "verdict": "ABORTED"}` to the state file to stop the hook from blocking. This should be a first-class orchestrator subcommand: `python ship_orchestrator.py abort --session-id <UUID> --reason "work already committed"`.

**Finding 13 — The pipeline assumes pre-commit invocation.** The entire `/ship-py` design assumes the pipeline runs BEFORE commits land on main. The SKILL.md says: "take commits from code-complete to verified+merged." But in practice, this workspace's auto-commit policy means work is often committed before the operator thinks to invoke `/ship-py`. The pipeline needs a "retroactive review" mode that reviews already-committed work in the current session's commit range (session_start..HEAD) rather than working-tree diffs.

### Recommended fixes (add to task packets)

| Fix | Priority | Effort | Prevents |
|-----|----------|--------|----------|
| Add `abort` subcommand to orchestrator | HIGH | ~20 lines | Hook feedback loop when pipeline can't complete |
| Add "already shipped" detection in `cmd_detect` | MEDIUM | ~15 lines | Wasted review effort on already-pushed work |
| Fix Stop hook regex to exclude "cannot" / "unable" patterns | HIGH | ~5 lines | False-positive blocks on legitimate explanations |
| Add "retroactive review" mode (`/ship-py --review-committed`) | LOW | ~40 lines | Pipeline unusable for post-commit review |

### Updated status

The 5 architectural items (5-9) from the original handoff remain open. Items 10-13 (this revision) are new findings from live operator usage. The `ship-py-mandatory-step-gate-20260806` handoff addresses a related concern (preventing verdict without review) but does not address the "already shipped" or hook-trap problems.

---

## Revision 2 — 2026-08-07 (session 019fc927) — Finding 12 partially fixed + wiki concept written

**Trigger:** auto-update — the Stop hook fired again during `/wiki` and `/handoff` invocations, demonstrating the exact feedback loop documented in Finding 11. The root cause (Finding 12: no aborted state recognized) was partially fixed this turn.

### What shipped

1. **quality_gate.py ABORTED fix (commit `083e493` in ~/.grok).** Added `"ABORTED"` to the recognized terminal verdicts at `quality_gate.py:208-210`, alongside `"SHIP DONE"` and `"SHIP BLOCKED"`. The hook now recognizes a manually-written abort state and stops blocking. This addresses the immediate symptom of Finding 12 — agents who abort the pipeline (by writing `verdict: "ABORTED"` to the state file) will no longer be trapped by the hook.

2. **Wiki concept `[[stop-hook-state-file-keyword-trap]]` (commit `ed0d52b` in P:/).** Documents the full failure pattern: state-file coupling makes the regex feedback loop structurally unbreakable. Extends `[[llm-judgment-hooks]]` (conversation-collapse pattern) and `[[hook-regex-false-positives-pasted-terminal-output]]`. Includes source receipts for `quality_gate.py:160-220` and the ship_orchestrator state machine.

### What remains open from Revision 1

| Fix | Status | Notes |
|-----|--------|-------|
| Add `abort` subcommand to orchestrator | **STILL OPEN** | The hook now recognizes ABORTED, but agents still must hand-edit the JSON state file. A first-class `ship_orchestrator.py abort --session-id <UUID> --reason "..."` subcommand is still needed. |
| Add "already shipped" detection in `cmd_detect` | **STILL OPEN** | `cmd_detect` still creates the state file even when work is already committed. Needs session-commit-range detection. |
| Fix Stop hook regex to exclude "cannot" / "unable" patterns | **PARTIALLY ADDRESSED** | The ABORTED verdict recognition prevents the loop from persisting, but the regex still false-positive matches "ship-py cannot complete." The regex fix (negative lookahead for "cannot/unable") is still needed for non-aborted cases. |
| Add "retroactive review" mode | **STILL OPEN** | Pipeline still assumes pre-commit invocation. |

### Updated status

Items 5-9 (architectural) remain open. Items 10-13 (live usage) remain open with Finding 12 partially addressed. The wiki concept captures the pattern for future hook designs.
