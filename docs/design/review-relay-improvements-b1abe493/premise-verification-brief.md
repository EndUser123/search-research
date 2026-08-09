# Premise Verification Brief (Step 0.8)

Generated: 2026-08-09
Source: `P:/packages/codex-external-delegation/src/review-relay.mjs` (1522 lines), `~/.grok/skills/review-relay/SKILL.md` (370 lines)

## [FACT] premises (verified by file:line grep this session)

1. **[FACT, receipt: review-relay.mjs:25]** `DEFAULT_LEASE_SECONDS = 600` with comment "Gerrit CI amplification research shows 5-20x overhead; 120s was too tight for LLM review turns." Wiki claim verified.

2. **[FACT, receipt: review-relay.mjs:755]** `reviewKeyFromPaths(inputPaths)` is implemented as `sha256(stableStringify(sorted normalized paths)).slice(0, 16)`. Path-derived, not content-derived. Wiki claim verified.

3. **[FACT, receipt: review-relay.mjs:41, 535, 1497]** `ready_for_parent_review` is a **status enum value**, not a boolean field. The valid statuses are: `"failed"`, `"timed_out"`, `"ready_for_parent_review"`, `"expired"`, `"needs_review"`. Line 1497 confirms partner sets this via `supplied.status === "ready_for_parent_review"`.

   **CORRECTION to wiki concept:** the wiki says "replace boolean `ready_for_parent_review` with a weighted score." This is imprecise. The field is already a status enum, not a boolean. The design should either (a) add a separate `convergence_score` field alongside status, or (b) redefine the status enum to include score bands. Writer must address.

4. **[FACT, receipt: review-relay.mjs:1026, 1374, 1391, 1417]** `previous_result` IS the partner-passing mechanism. The relay passes `previous_result_path` (file path to previous turn's result JSON), `previous_result_actor`, and `previous_result_hash` in the tick/input. Partners read the file at `previous_result_path` to see prior partner output. Wiki claim verified.

5. **[FACT, receipt: SKILL.md:438-446]** Convergence auto-detection heuristic lives in the skill, not the .mjs. Verbatim:
   > - **Converged:** both actors produced 0 new findings and 0 disputes in the last complete round
   > - **Stuck:** 0 new findings but unresolved findings remain open across 2+ rounds
   > - **Active:** new findings introduced this round. Continue the relay.

6. **[FACT, receipt: grep for findings.*state|open|rebutted|upheld|resolved|superseded returned no matches in src]** No state field exists on findings today. Findings lifecycle tracking IS a new structure.

7. **[FACT, receipt: grep for section|parallel.*dispatch|fan.out|per.section returned no matches in src]** No notion of proposal "sections" exists in the relay. Per-section parallel review IS a new structure.

8. **[FACT, receipt: grep for findings:|findings =|.findings returned no matches in src/review-relay.mjs]** **The relay is findings-agnostic.** Findings appear only in tests as part of result fixtures (`tests/review-relay.test.mjs:52` defines `findings: []` as a default result shape). The source code never parses, inspects, or manipulates findings. Partners produce them; the relay treats result content as opaque.

   **This is the load-bearing structural fact for the design:** introducing finding lifecycle tracking requires the relay to start inspecting result content (currently opaque). This is a structural shift, not an incremental change. The current architecture is "dumb pipe" — finding lifecycle tracking makes it an "inspecting pipe."

9. **[FACT, receipt: tests/review-relay.test.mjs exists]** Test file exists (referenced at line 52, 520). Writer will need to extend tests for any new state machine or convergence-score logic.

## [INFERENCE] premises (reasoned but unverified)

10. **[INFERENCE]** The "ReviewingAgents/POIROT/GPT Researcher" pattern names in the wiki concept may not be real paper names. The wiki concept was produced by a prior /www session and cites no URLs. Step 0.6 domain research subagent is verifying this in parallel. Writer should treat pattern mechanisms as design inspirations, not authoritative citations, until the domain brief returns.

11. **[INFERENCE]** "Per-section parallel review" would require either (a) splitting the proposal file into N section-files before relay start, or (b) adding a section-aware dispatch primitive to the relay. Approach (a) preserves the "dumb pipe" architecture; approach (b) deepens relay responsibility. Writer should propose both as alternatives.

## [UNKNOWN] premises

12. **[UNKNOWN]** Whether the relay's write_policy currently forbids reading other turns' directories (would block finding-lifecycle persistence to a shared location). The grep showed `forbidden_writes` is passed to partners, but the specific policy contents aren't verified. Writer should check `write_policy` definition in source.

13. **[UNKNOWN]** Whether the existing tests would break if `result.status` gains new enum values (e.g., a convergence score). Test fixtures use `"submitted"` and `"ready_for_parent_review"` — schema extension may or may not be backward-compatible depending on `RESULT_SCHEMA_VERSION` handling.

## [CONTRADICTED] premises

None. The wiki concept's framing holds, with one correction: `ready_for_parent_review` is a status enum value, not a boolean. This doesn't change the design intent but changes the proposed mechanism (add field alongside, not replace boolean).

## Highest-risk premise

**Premise 8** is the highest-risk: "relay is findings-agnostic." If true, finding lifecycle tracking is a bigger change than the wiki concept implies. The design must explicitly address whether the relay should remain a dumb pipe (lifecycle tracked in a sidecar file partners read) or become an inspecting pipe (relay parses findings from each result and maintains the state machine). This decision shapes the entire Implementation Plan.