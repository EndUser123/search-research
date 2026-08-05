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
