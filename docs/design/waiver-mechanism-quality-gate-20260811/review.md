# Design Review (Round 2) — Optimal Waiver Mechanism for Stop-Hook Review Quality Gate

**Design run:** 62d39214
**Date:** 2026-08-11
**Reviewer:** design-doc reviewer (rigorous implementation-readiness)
**Scope:** re-review after writer addressed all 36 prior issues

Receipts verified against source:
- `C:/Users/brsth/.grok/hooks/scripts/quality_gate/gate_diagnostics.py`
- `C:/Users/brsth/.grok/hooks/scripts/quality_gates_frontmatter.py` (lines 595-615, 800-805)
- `C:/Users/brsth/.grok/hooks/scripts/quality_gate/main.py`
- `C:/Users/brsth/.grok/scripts/waiver_gate.py`
- **`C:/Users/brsth/.grok/docs/user-guide/10-hooks.md` (lines 250-270) — critical F-36 verification**

---

## Re-review summary

**Previous round:** 35 issues + 1 writer-initiated (N-01) = 36 findings, all marked addressed.

**This round:** the writer's resolutions themselves surface new issues. The most important is F-36, which contradicts the F-01 resolution. Several other resolutions introduced inconsistencies that were not present in the prior version.

The writer closed F-01 by replacing `decision: warn` with `hookSpecificOutput.additionalContext`, citing `10-hooks.md:254-262` as the receipt. The doc was correctly read for the four supported output forms, but the writer misread what "non-error feedback" means in this protocol — it is NOT non-blocking. See F-36 below for the detailed falsifier.

---

## F-36 — Severity: critical
- Section: Recommended Approach → "Operator-visible change" / DEC-04 / Premise Verification → P8
- Description: The F-01 "resolution" is incorrect. The writer correctly identified that `decision: warn` is not a supported Stop-hook output, and correctly read the four output forms from `~/.grok/docs/user-guide/10-hooks.md:254-262`. However, the writer then substituted `hookSpecificOutput.additionalContext` as "the only non-blocking feedback mechanism." This misreads the docs. Per `10-hooks.md:257` (verbatim):
  > **Non-error feedback**: `{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "..."}}`. **Also keeps the agent working**, but is surfaced as hook feedback rather than a hook error.
  And `10-hooks.md:262`:
  > After **8 continuations** (blocks or non-error feedback) in one turn the gate is overridden and the turn ends.

  Both `decision: block` AND `hookSpecificOutput.additionalContext` keep the agent working AND both count toward the 8-continuation cap. The semantic difference is only in HOW the agent receives the feedback (as a user message vs. as hook context) — not in whether the agent is allowed to end its turn. Therefore the F-01 swap does NOT resolve the original critical issue; it swaps one mechanism that keeps the agent working (the would-be `decision: warn`) for another that keeps the agent working (`additionalContext`). The "block → non-blocking feedback downgrade" framing in DEC-04 is factually wrong: there is NO non-blocking feedback mechanism for Stop hooks on this host. The only way to allow the stop is `exit 0 with no output` (`10-hooks.md:259`), which loses the audit signal at the hook boundary entirely.

  **Consequence:** if the new mechanism emits `additionalContext` on every matched fire, the agent will be kept working for up to 8 rounds per turn (since `invoked_skills` is reconstructed from the full transcript each round — P1 — and the gate will re-match the same waiver each round). This re-introduces the exact anti-loop failure mode the original 30-min freshness fix was designed to prevent. The design's `consumed_count` increment will still happen on each fire, but the agent will not be able to make forward progress until the 8-continuation cap is hit. After 8 rounds, the turn ends *without* the gate's decision being honored (line 262: "hooks are not consulted for that final, forced stop") — so the audit is still partial.

  The writer's verification (`~/.grok/docs/user-guide/10-hooks.md:254-262`) is real and was performed, but the inference ("non-error feedback = non-blocking") is false. This is a narrative-closure error, not a doc-reading error: the writer wanted the swap to work, so they interpreted the ambiguous label "non-error feedback" as "non-blocking" rather than reading the body sentence ("Also keeps the agent working").
- Suggestion: The F-01 "resolution" must be re-opened. Three viable paths:
  1. **Accept that there is no non-blocking feedback mechanism on this host.** Use silent-allow (`exit 0 with no output`) as the only mechanism that lets the agent proceed, and surface the audit exclusively via the sidecar file (`quality-gate-warns-{sid}.jsonl`) plus the `consumption_audit` array in the waiver file. The "operator-visible signal at the hook boundary" justification in DEC-04 is dropped; the operator sees the bypass post-hoc via `/maintain` weekly scans, not in real-time. Update P8's resolution accordingly: "There is NO non-blocking feedback mechanism. The bypass is silent at the hook boundary and visible only via the audit log."
  2. **Use a different hook event** (e.g., a custom `PostToolUse` advisory hook that fires on completion-claim text matches but does not block). This decouples audit-visibility from the blocking decision.
  3. **Accept the 8-continuation cap as the new anti-loop floor.** The design ships as-is; the agent is allowed to be kept working for up to 8 rounds per turn (instead of being blocked indefinitely); the bypass audit row is still recorded on each fire; the agent may eventually end the turn after 8 rounds. This is a worse UX but technically implementable.

  Option 1 is the closest to the design's original intent and should be the default. Update DEC-04, the Goal statement, and the Premise Verification section to reflect that the design no longer claims "non-blocking feedback" and instead claims "silent allow + post-hoc audit."
- Status: open

## F-37 — Severity: critical
- Section: Problem Framing & Core Tension → "Self-authorization: when is it acceptable?" / DEC-08 / Unit 2
- Description: The F-03 resolution adopted option (b) from the original review: the `GROK_SELF_AUTH_ALLOWED` env var (default `1`; set to `0` to refuse self-authorization). The writer's response says "the `waiver_gate.py` script refuses to write a waiver with `--authorized-by agent` (exit code 2)." However, this is a config-toggle bypass unless the env var is set in a way the agent cannot override. Specifically:
  1. **Env var override at invocation:** an agent invokes `GROK_SELF_AUTH_ALLOWED=1 python ~/.grok/scripts/waiver_gate.py --gate review --milestone-id X ...`. The script reads the env var, sees `1`, and writes the waiver. The env var set in `$PROFILE` is overridden. Unless the host runtime enforces env-var inheritance (it doesn't on this host per `~/.grok/AGENTS.md` — agents control their own invocation context), this is bypassable.
  2. **`--authorized-by operator` bypass:** the check in `waiver_gate.py` only refuses `--authorized-by agent`. An agent that wants to bypass just uses `--authorized-by operator`. The script does not verify the operator's presence (e.g., no check that `$OPERATOR_SESSION_ID` matches the agent's session, no check that an operator-side approval was recorded). The agent self-issues operator authorization.
  3. **No mechanism to set the env var externally:** the design does not specify WHO sets `GROK_SELF_AUTH_ALLOWED=0`. The operator would have to set it manually before each session (or in `$PROFILE`), but the agent can override. There is no Stop hook check that refuses to honor a waiver written when the env var was `1` at write time.

  This is the pattern the user prompt explicitly asked about: "Whether the self-authorization env var (`GROK_SELF_AUTH_ALLOWED`) is a sound resolution or just a config-toggle bypass." The answer is: as stated, it is a config-toggle bypass. The design does not address how the env var is set in a way the agent cannot override.
- Suggestion: Pick one of:
  (a) **Operator-presence attestation:** require the waiver to include a signature or nonce that only an operator-side action can produce (e.g., the operator types a confirmation in their terminal; the confirmation is captured by the host runtime and exposed as an env var that the agent cannot forge). This is essentially OQ-04's synchronous approval channel, made minimal.
  (b) **Post-hoc gate on bypass budget:** drop the runtime check entirely; rely on `bypass_budget.py` to flag sessions with excessive self-authorization, and the operator manually reviews. The env var becomes informational only.
  (c) **Hook-side check:** add a Stop hook or `PostToolUse` hook that verifies each `waiver_gate.py` invocation's env var against a host-controlled baseline (e.g., read from `$PROFILE` or a file the agent cannot write). If the env var was set by the agent, refuse the bypass.

  Option (c) is the lightest-weight structural fix and is implementable with the existing hook infrastructure. Document the check site (the hook that fires when `waiver_gate.py` is invoked) and the baseline source.
- Status: open

## F-38 — Severity: major
- Section: Implementation Plan → Unit 2 (Call-chain compatibility) AND Detailed Mechanism Design → "File: `~/.grok/scripts/waiver_gate.py`"
- Description: The path reconciliation in F-08 was claimed resolved. The "Recommended Approach" section says "Canonical waiver path is `~/.grok/hooks/state/quality-gate-waiver-{session_id}.json`" (verified against `quality_gates_frontmatter.py:596` source). The Detailed Mechanism Design for `waiver_gate.py` correctly states the script writes to the canonical path. BUT the Implementation Plan's Unit 2 "Call-chain compatibility" subsection says: "Output: writes `~/.grok/hooks/state/{gate}-waiver-{session_id}.json` — same path pattern as before." The `{gate}` placeholder resolves to `review` for the review gate, producing `review-waiver-{session_id}.json` — NOT `quality-gate-waiver-{session_id}.json`. These are two different filenames. If `gate_diagnostics.py:582` is updated to glob `quality-gate-waiver-{sid}.json` (per the design's path reconciliation) but `waiver_gate.py` keeps writing `{gate}-waiver-{sid}.json` (per Unit 2's stale call-chain note), then the gate will NEVER find a written waiver — the freshness check always finds nothing, the gate always falls through to the legacy block path, and the new mechanism is silently inert. The path reconciliation is INCOMPLETE.
- Suggestion: Update Unit 2's "Call-chain compatibility" to: "Output: writes `~/.grok/hooks/state/quality-gate-waiver-{session_id}.json` — the canonical path (F-08). The `{gate}-waiver-{session_id}.json` path used by the legacy script is deprecated and merged into the canonical path." Verify by reading the actual `waiver_gate.py` source (current line 60-65) which uses `{args.gate}-waiver-{session_id}.json` — this must change to `quality-gate-waiver-{session_id}.json`. The Unit 2 acceptance criteria should include "Output path matches canonical path (`quality-gate-waiver-{session_id}.json`) — assert with `os.path.basename(os.readlink(path)) == 'quality-gate-waiver-{sid}.json'`."
- Status: open

## F-39 — Severity: major
- Section: Implementation Plan → Unit 1a / Unit 1b / Unit 1 (legacy combined)
- Description: The Implementation Plan now lists THREE versions of Unit 1:
  - **Unit 1a**: Refactor `_quality_gate_check` into 3 functions, no behavior change (F-29 split).
  - **Unit 1b**: New scope-bound waiver mechanism, behavior change (F-29 split).
  - **Unit 1 (legacy combined)**: The original single-unit version with the 3-tuple signature, F-04 caller enumeration, and `GROK_REVIEW_GATE_SCOPED_WAIVER` feature flag (with 3-state semantics).

  The "legacy combined" was supposed to be superseded by 1a+1b, but it is still present in the doc as a separate unit. This creates three problems: (1) ambiguity about which unit is actually committed (the implementer might commit the combined version, defeating the F-29 split); (2) the 3-state feature flag is in the combined unit but is logically part of Unit 1b (the mechanism), not Unit 1a (the refactor); (3) the caller enumeration (F-04) is in the combined unit but applies to both 1a and 1b since the signature change is in 1b. The split is partial, not complete.
- Suggestion: Either (a) delete "Unit 1 (legacy combined)" entirely and inline its content into the appropriate 1a/1b unit (F-04 caller enumeration goes with 1b; feature flag goes with 1b), or (b) keep the combined version but explicitly mark it as "DEPRECATED — see Units 1a + 1b; do not commit this version." Option (a) is cleaner. The Traceability Matrix already references Units 1a and 1b correctly, so removing the combined version does not break traceability.
- Status: open

## F-40 — Severity: minor
- Section: Detailed Mechanism Design → "File: `~/.grok/hooks/scripts/quality_gates_frontmatter.py`" (F-30 response) / Coupling & Code-Smell Inventory
- Description: The F-30 resolution states: "write_waiver() is preserved (not deleted) because it is still called by check_quality_gates() at line 803 for any callers that depend on the `quality-gate-waiver-{session_id}.json` file path." This claim is factually incorrect. Reading `quality_gates_frontmatter.py:803` (verified):
  ```python
  # Read waiver
  waiver = read_waiver(session_id)
  waived = set(waiver.get("waived_skills", []))
  ```
  Line 803 calls `read_waiver()`, NOT `write_waiver()`. The function `write_waiver()` (defined at line 614) has no callers in the visible codebase — `waiver_gate.py` uses its own atomic-write logic (lines 60-70), and no other module calls `write_waiver()`. So `write_waiver()` is genuinely dormant code, not "called by check_quality_gates()". Per the cleanup protocol (dormant code should be deleted, not preserved as compat), the F-30 resolution's rationale is wrong.

  This also affects the Coupling & Code-Smell Inventory's touch-point count: if `write_waiver()` is deleted, the touch-point count for `quality_gates_frontmatter.py` decreases by 1, which might bring the gate_diagnostics touch-point count (5) back into alignment with the threshold justification.
- Suggestion: Either (a) delete `write_waiver()` (line 614-640) per the cleanup protocol, OR (b) cite an actual caller (not line 803, which calls `read_waiver()`). If option (b) is taken, the caller must be enumerated (per F-04's discipline of enumerating all call sites). Note that if `write_waiver()` is deleted, the `write_scoped_waiver()` helper is the only waiver writer, which is also more consistent with the design's "consolidated waiver path" goal (F-08).
- Status: open

## F-41 — Severity: minor
- Section: Recommended Approach → `consumption_audit` schema / Detailed Mechanism Design
- Description: The consumption_audit mechanism (per F-18 fix) records three outcomes: `warn` (matched scope), `block_skipped` (waiver existed but didn't match), and `allow` (no missing evidence). The design says "Each gate fire appends one row regardless of outcome." But `consumption_audit` is a field inside the waiver file. If the waiver file does not exist (e.g., a fresh session with no waiver written), there is no `consumption_audit` array to append to. So `allow` entries (which happen when the gate isn't blocked at all — including the common case where there's no waiver) cannot be stored in `consumption_audit`. The only place they can go is the sidecar log. The design's intent (record all fires) cannot be implemented with `consumption_audit` as the storage location for `allow` entries — `allow` entries will only appear in the sidecar log. This creates an asymmetry: `warn` and `block_skipped` go to BOTH `consumption_audit` (in waiver file) and sidecar log, while `allow` goes ONLY to sidecar log.

  Additionally, the 1000-entry cap with pruning (Component 7) handles overflow, but the pruning strategy is not specified (FIFO-by-timestamp? LIFO? random?). The pruning happens in `_consume_waiver()` per the design's "oldest entries are pruned on append when cap is exceeded" — but the design doesn't specify which entries (oldest by timestamp) or how the SHA-based tamper detection handles the pruned entries (the SHA would change when entries are pruned, but bypass_budget.py compares SHAs — so the SHA needs to be a rolling hash or the comparison would always fail after pruning).
- Suggestion: Either (a) split storage explicitly: `consumption_audit` records `warn` and `block_skipped` only (waiver-relevant fires); sidecar log records all fires (including `allow`). Document this in DEC-02. Or (b) move `consumption_audit` to a separate file (e.g., `~/.grok/hooks/state/quality-gate-consumption-{sid}.jsonl`) so it can exist independently of the waiver file. Option (a) is simpler. Also: specify the pruning strategy (FIFO by timestamp) and the SHA computation method (rolling hash over the live entries, or recompute the SHA from current entries without the pruned ones).
- Status: open

## F-42 — Severity: minor
- Section: Rollout → "Shadow mode (intermediate safety)" / DEC-06
- Description: DEC-06 specifies shadow mode: "the new mechanism runs and logs decisions to the sidecar, but the legacy mechanism's decision is the one emitted on stdout." The legacy mechanism emits `decision: block` (when blocked) or silent-allow (when not blocked). It does NOT emit `hookSpecificOutput.additionalContext`. So in shadow mode, the new mechanism's `additionalContext` decision is computed and logged to the sidecar, but never emitted to the agent. The operator cannot see the new mechanism's decision at the hook boundary — they only see the legacy decision. The "intermediate safety" benefit (catching regressions before the feature flag flips) is illusory: the operator validates the legacy mechanism's behavior (which hasn't changed), not the new mechanism's behavior (which is the whole point of shadow mode).

  Worse, given F-36's finding that `additionalContext` keeps the agent working (same as block), shadow mode would either: (i) emit `decision: block` (legacy) → agent blocked; or (ii) emit silent-allow (legacy, when waiver matches by freshness) → agent proceeds. The new mechanism's `additionalContext` decision is computed and discarded. The shadow mode provides no validation of the new mechanism's actual behavior at the hook boundary.
- Suggestion: Either (a) drop shadow mode (the rollout goes off → on directly), or (b) redefine shadow mode as "the new mechanism's decision is emitted to the sidecar AND the agent receives the legacy decision; if the new mechanism disagrees with the legacy, a warning is logged" — but this still doesn't validate the new mechanism's behavior. The fundamental issue is that shadow mode requires the new mechanism to actually emit something the operator can see, but the Stop-hook protocol has no "advisory" output (per F-36). If shadow mode is dropped, the rollout simplifies to off → on (with a 1-week observation window), which is acceptable.
- Status: open

## F-43 — Severity: minor
- Section: Key Decisions → DEC-04 → Rationale
- Description: DEC-04's rationale says: "The break-glass pattern (P6) explicitly says the bypass should convert `block → warn`-style non-blocking feedback, not `block → allow`. The current Stop hook emits only `block` (with `sys.exit(0)` after) or allows silently." This conflates the LITERATURE's prescription (P6 says bypass should convert block to warn-style feedback) with the HOST's capability (Stop hook does/doesn't support warn-style feedback). The literature says non-blocking feedback is the right pattern; the host doesn't support it. The design's "resolution" claims to satisfy both — it doesn't; it satisfies neither cleanly. The DEC-04 rationale should acknowledge this contradiction explicitly: "P6 prescribes non-blocking feedback; the host protocol does not support it; we accept the closest available mechanism (additionalContext, which keeps the agent working with hook-context-style feedback) as the best available approximation."

  Given F-36's finding that `additionalContext` keeps the agent working (same as block), the "closest available approximation" claim is wrong too. The honest framing is: "P6's prescription is not implementable on this host. The closest mechanisms either keep the agent working (block, additionalContext) or silently allow (exit 0). The design chooses silent allow + post-hoc audit; this is a known gap from P6 that is documented as a design limitation."
- Suggestion: Rewrite DEC-04's rationale to acknowledge the P6-vs-host contradiction honestly. If the design proceeds with `additionalContext` despite F-36, the rationale must say "the design accepts keeping the agent working (up to 8 rounds per turn) as the cost of operator-visible feedback at the hook boundary — this is a known trade-off from the literature prescription (P6) which presumes a host that supports non-blocking feedback." If the design switches to silent-allow per F-36's option 1, the rationale is "the design accepts losing operator-visible feedback at the hook boundary in exchange for the anti-loop property; this is a known gap from P6."
- Status: open

## F-44 — Severity: minor
- Section: Design Intent Contract → Success Metrics (second bullet)
- Description: The success metric says: "Zero ship-time claims that bypass review without an audit row (`grep` of `review-waiver-*.json` shows `1` row per ship claim when bypass used)." The `grep` target is `review-waiver-*.json`, which is the LEGACY path. The F-08 path reconciliation made the canonical path `quality-gate-waiver-{sid}.json`. The metric's verification command grep's the OLD path — it would always return zero rows after the new mechanism is deployed, because new waivers are written to the canonical path, not the legacy path. This metric cannot be measured post-deploy with the command shown.
- Suggestion: Update the metric to: "Zero ship-time claims that bypass review without an audit row (`grep` of `quality-gate-waiver-*.json` shows `1` row per ship claim when bypass used — F-44, post-F-08 canonical path)." Verify by running the grep against a test deployment before declaring the metric operational.
- Status: open

## F-45 — Severity: nit
- Section: Premise Verification → P8
- Description: P8's status is "VERIFIED FALSE" but its label is `[INFERENCE]`. The label `[INFERENCE]` for a premise that has been falsified is semantically odd. A premise that has been tested and found false should arguably be marked `[DISCONFIRMED]` or `[REFUTED]`, distinct from `[INFERENCE]` (which means "reasoned conclusion with stated supporting evidence and explicit uncertainty"). The current labeling is internally consistent with the taxonomy (an inference CAN be wrong) but doesn't communicate the falsification status to the reader. The Premise Labels Reference appendix should add `[DISCONFIRMED]` to the taxonomy (or accept `[INFERENCE]` as covering both possibilities and document that falsification is signaled via the status field, not the label).
- Suggestion: Either (a) add `[DISCONFIRMED]` to the Premise Labels Reference appendix and re-label P8 as `[DISCONFIRMED]`, or (b) keep `[INFERENCE]` and add a sentence to P8's entry: "This inference has been falsified against `10-hooks.md:254-262`. The design uses the correct mechanism despite the falsification of this premise." Option (b) preserves the existing label taxonomy.
- Status: open

## F-46 — Severity: nit
- Section: File Change Inventory → Quality Gate Report row
- Description: The File Change Inventory has 9 rows but the Unit numbers in the "Unit" column are inconsistent: some rows reference "Unit 1a + 1b" (split unit), others reference "Unit 6a" (split unit), and others reference "Unit 1 (legacy)" implicitly via the "Unit" column header being unclear. Given F-39 (Unit 1 duplication), the inventory should be reconciled to use the new unit numbers (1a, 1b, 6a) consistently.
- Status: open

---

## Resolution status of prior issues (re-verification)

The following prior issues were claimed resolved but warrant re-listing because the resolution introduced a new problem or was based on a misunderstanding:

| Prior ID | Status | Reason |
|---|---|---|
| F-01 | RE-OPENED as F-36 | The `additionalContext` substitution is not a non-blocking mechanism. |
| F-03 | RE-OPENED as F-37 | The env var is a config-toggle bypass unless set externally. |
| F-08 | RE-OPENED as F-38 | Path reconciliation incomplete; Unit 2's call-chain note is stale. |
| F-29 | PARTIALLY ADDRESSED — F-39 | Split done, but legacy combined unit not removed. |
| F-30 | RE-OPENED as F-40 | `write_waiver()` is NOT called by `check_quality_gates()` at line 803. |

The following prior issues appear genuinely addressed (no re-listing):

| Prior ID | Resolution status |
|---|---|
| F-02 | Addressed (3 mutually exclusive branches; consumption via consumption_audit, not deletion). Note: this fix is still correct; the consumption semantics are sound even if the underlying emission mechanism is broken (F-36). |
| F-04 | Addressed (caller enumeration in Unit 1 preconditions). |
| F-05 | Addressed (touch-point count recomputed to 5 with explicit justification; Unit 1 split). |
| F-06 | Addressed (bypass budget exceedance row added; regression test added). |
| F-07 | Addressed (3 new component failure-mode tables). |
| F-09 | Addressed (Code-Path tables restructured with explicit branches). |
| F-10 | Addressed (modified_files source clarified). |
| F-11 | Addressed (inline comment in Unit 3 pseudocode). |
| F-12 | Addressed (DEC-06 specifies 3 states with implementation example). |
| F-13 | Addressed (11 explicit tests in Unit 4). |
| F-14 | Addressed (Unit 6 split into 6a/6b). |
| F-15 | Addressed (`[RESEARCH]` label defined). |
| F-16 | Addressed (P11 promoted with supporting evidence). |
| F-17 | Addressed (over-broadening case documented). |
| F-18 | Addressed (`consumption_audit` schema extended). |
| F-19 | Addressed (multi-agent row downgraded to "best-effort isolation"). |
| F-20 | Addressed (handoff path cited). |
| F-21 | Addressed (Unit 5 expanded). |
| F-22 | Addressed (DEC-04 explicitly states 3 mutually exclusive branches). |
| F-23 | Addressed (OQ-01 cost-of-deferring disclosed). |
| F-24 | Addressed (Test column added to Traceability Matrix). |
| F-25 | Addressed (deprecation documented). |
| F-26 | Addressed (format verification deferred to pre-commit). |
| F-27 | Addressed (metric reclassified as judgment threshold). |
| F-28 | Addressed (glob tightened). |
| F-31 | Addressed (P3 receipt cites more specific range). |
| F-32 | Addressed (parser pattern specified). |
| F-33 | Addressed (rotation strategy added). |
| F-34 | Addressed (cost estimates added to all OQs). |
| F-35 | Addressed (failure condition expanded). |
| N-01 | The P8 was correctly identified as false; the FIX is incorrect (see F-36). |

---

## New findings summary

| ID | Severity | Section |
|---|---|---|
| F-36 | critical | F-01 resolution incorrect (`additionalContext` keeps agent working) |
| F-37 | critical | F-03 resolution is a config-toggle bypass |
| F-38 | major | F-08 path reconciliation incomplete (Unit 2 stale) |
| F-39 | major | F-29 split done but legacy combined unit not removed |
| F-40 | minor | F-30 `write_waiver()` claim is false (line 803 calls `read_waiver`) |
| F-41 | minor | consumption_audit storage asymmetry for `allow` entries |
| F-42 | minor | Shadow mode provides no intermediate safety |
| F-43 | minor | DEC-04 rationale conflates literature prescription with host capability |
| F-44 | minor | Success metric grep's the old path |
| F-45 | nit | P8 label `[INFERENCE]` is misleading for a falsified premise |
| F-46 | nit | File Change Inventory unit numbers inconsistent |

**Severity breakdown:**
- critical: 2 (F-36, F-37)
- major: 2 (F-38, F-39)
- minor: 6 (F-40 through F-45)
- nit: 2 (F-45, F-46)

**Total new findings:** 11

---

## Overall assessment

The writer addressed 31 of 35 prior findings correctly. The four partially-addressed findings (F-01, F-03, F-08, F-29, F-30) all suffer from a common root cause: the writer performed the doc verification (cited source lines, read the relevant files) but the inference from the verification was incorrect or incomplete. This is the same narrative-closure pattern flagged in `~/.grok/AGENTS.md` ("Claims require receipts; narrative sufficiency is not verification") — the writer found the receipt but did not let the receipt falsify the prior commitment to the mechanism.

**Critical issues that must be resolved before shipping:**

1. **F-36:** The F-01 "resolution" is broken. `hookSpecificOutput.additionalContext` keeps the agent working (per `10-hooks.md:257, 262`), same as `decision: block`. Both count toward the 8-continuation cap. The design's "block → non-blocking feedback" framing is incorrect. The Stop-hook protocol on this host has NO non-blocking feedback mechanism. The design must either accept silent-allow + post-hoc audit (drop the hook-boundary visibility claim) or accept that the agent will be kept working for up to 8 rounds per turn (degrade UX).

3. **F-37:** The `GROK_SELF_AUTH_ALLOWED` env var is a config-toggle bypass. The agent can override the env var at invocation time, and `--authorized-by operator` is not verified. The env var must be set externally (operator-controlled) AND the operator's authorization must be verified (e.g., via a hook that checks the invocation context).

**Major issues that should be addressed:**

- F-38 (path reconciliation incomplete — Unit 2 still references the legacy path; if shipped as-is, the new mechanism is silently inert).
- F-39 (Unit 1 duplication — three versions of Unit 1 in the Implementation Plan creates commit ambiguity).

**Verdict:** The design is close to ready but cannot ship as-is due to F-36 and F-37. Both are correctness issues, not style or completeness issues. Resolving F-36 (likely to silent-allow per option 1) would invalidate several downstream decisions (DEC-04 rationale, the Operator-visible Change section, the success metric that assumes operator visibility). Resolving F-37 (env var hardening) is a smaller change but equally necessary for the design's stated security boundary. F-38 should be fixed before any code is committed (otherwise the new mechanism will not match any written waiver).