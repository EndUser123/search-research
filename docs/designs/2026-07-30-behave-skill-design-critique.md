# Critical Friend Review: `/behave` Design

**Reviewer stance:** challenge premises, not implementation. The correctness reviewer cleared the implementation surface; this review challenges the framing that produced that surface.

**Documents reviewed:**
- `C:\Users\brsth\AppData\Local\Temp\grok-design-81539877\grok-design-doc-81539877.md` (740 lines)
- `C:\Users\brsth\AppData\Local\Temp\grok-design-81539877\grok-design-summary-81539877.md` (writer's summary)

---

## Selected domains

**Core (always):**
1. Problem framing
2. Optimal long-term vs. simplicity
3. Falsifiability
4. Anchoring

**Context-derived (selected):**
5. **User workflow fit** — explicitly raised by operator: "will the skill actually be used?"
6. **Observed-vs-invented** — explicitly raised: "is diagnostic better than improving `/tp`'s verification synthesis gate?"
7. **Provenance / identity** — design creates new identity primitives (`operator_id`, `source_session_id`, `input_packet_sha256`) in a domain where `wiki-citation-host-provenance` and `grok-build-host-authority` rules already constrain behavior.
8. **Cost / performance** — cross-model review budget, fixture maintenance, `≥1 per incident-class per quarter` target.

**Open-ended:**
9. **Self-application paradox** — the analyst-exhibits-pattern risk raised by the operator is acknowledged in §16 as `[UNKNOWN]` but the mitigation design does not match the severity.

---

## 1. Problem framing

**The problem the design is actually solving (one sentence):** *An agent can change a verdict on unsupported critique, defend the reversal rather than repair the failure, and the operator has no structured way to reconstruct what happened or prevent recurrence.*

**Does that match the user's stated goal?** The BE-01 handoff (referenced as the source) targets "behavioral decision-integrity" — the framing is broader than "verdict reversal." The design narrows it to verdict-transition auditing (d1), load-bearing finding identification (d3), and self-protection detection (d7). This narrows the gap further than necessary: the handoff also covers *verdict staying put under user challenge* (e.g., the agent was wrong but didn't change), which d1 cannot detect because there's no transition to audit. The 2026-07-29 incident had a transition (REVIEW → ACCEPT → REVERSE); a different failure mode (REVIEW → DEFEND) might have no transition and would be invisible to `/behave`.

**Drift to name:** The design treats *transitioned* failures as the primary case. Steady-state failures (wrong verdict defended, never reversed) are out of scope. The fleet likely sees both.

**Status:** addressed (CF-F1). The d1 schema and Step 1 prose were extended to cover the `DEFENDED` outcome: `verdict_timeline[]` entries now include `outcome: TRANSITION|DEFENDED|NO_CHALLENGE`; defended entries capture `challenge_ref` and `defense_evidence` (verbatim quote); Step 7 runs against defense evidence; `defended_with_patterns` records which BP patterns fired in the defense; report-level `verdict` for a defended outcome with detected patterns is `VERDICT_UNSUPPORTED` (defense was unjustified). Risk R23 added to §11 capturing this case. Section §1 "When to invoke /behave (CF-F3)" Trigger 3 explicitly covers the `/design` verdict challenge scenario.

## 2. Optimal long-term vs. simplicity

**Optimal long-term solution:** A single decision-integrity subsystem shared between `/tp` (proactive verification), `/behave` (post-hoc verification), and VI-01 (behavioral rules), with a shared diagnostic report schema, shared evidence-tier system, and shared cross-model review invocation. The three skills become three invocation modes against one capability. The repair contract is the same in all three contexts.

**Is the simplest version also optimal?** **No.** The design's "separate skill" choice is operator-mandated by handoff, but the simplest version (separate skill, four `consumes:` interfaces, dedicated fixture) creates four maintenance burdens that the optimal design eliminates:

1. **Two parallel skill catalogs of self-protection patterns** — `/why` Step 0.5 queries `P:/.data/wiki/concepts/`, while `/behave` Step 7 reads `P:/.data/wiki/concepts/governance-pattern-library.md` (a new file). When a pattern is added via `/behave` Step 9, `/why` does not automatically see it; the two indexes must be kept coherent manually.
2. **Two parallel cross-model review invocations** — `/behave` Step 8 invokes `/why` Step 15b, but the diagnostic report is not a root-cause analysis. The Step 15b prompt template's three canonical questions (Q1 generalize, Q2 evidence real, Q3 falsifier) are designed for `root-cause-analysis`, not `decision-transition-audit`. Reuse-as-is is a coupling violation masked by `consumes_procedures:` semantics.
3. **Two parallel evidence-tier consumers** — `/behave` Step 4 re-implements `/why` Step 4b's tier logic with operator-assigned rationale (F-31). If `/why` later changes the tier definitions, `/behave` will silently drift. The `consumes_procedures:` mechanism cannot catch this.
4. **Two parallel fixture hierarchies** — `/behave` ships its own fixture (`review-decision-integrity-v1.md`); `/why` has its own. There is no shared regression test surface for "did the evidence-tier system still work?" across both skills.

**The cross-reference to §17 Coupling & Code-Smell Inventory** finds 7 touch-points for the new SKILL.md, justified individually. The threshold rule (>3 touch-points = structural coupling) is acknowledged but the dismissal rationale ("alternatives would be DRY violations") examines the wrong alternatives. The right alternative is *merge `/behave` Step 0, 4, 7, 8, 9 into `/why` Steps 0.5, 4b, 7, 15b, 15c respectively*, which would reduce `/behave` to a thin retrospective-invocation wrapper. The §17 table counts this option out by framing the choices as "duplicate `/why` infrastructure" (DRY violation) vs. "extend `/why`" (which is described as out of scope per handoff). The handoff scope is not a binding constraint on architecture; it is a handoff writer's choice.

**Over-engineering:** §4's metadata block (operator_id, input_packet_sha256, behave_version, why_version) is five fields where one timestamp + one schema version would suffice. `cross_model_review_pending: bool` separate from `cross_model_review.resolved_at` is redundant. The dimension schema (7 dimensions nested under `dimensions:` + operational fields flat at top level, F-33) creates a two-place lookup that the design explicitly acknowledges.

**Under-engineering:** No procedure for what happens when the operator invokes `/behave` on the same incident twice with different `verdict_timeline` inputs. No procedure for what happens when `/why` is upgraded mid-incident (the `why_version_min`/`max` frontmatter is static). No mechanism for `/behave` to detect its own output violates a self-protection pattern.

**Status:** addressed (CF-F2). §7 Alternatives now includes Option F: "Extend `/why` with `--retrospective` mode that runs the same 7-dimension methodology." The option is acknowledged as the strongest "observed-vs-invented" framing (noting ~70% capability duplication with `/why`) but **rejected** because: (a) it blurs `/why`'s forward-explanation semantics with post-hoc decision audit; (b) the cross-model review prompt template is designed for `root-cause-analysis`, not `decision-transition-audit`, so reuse is a coupling violation; (c) the maintenance burden (Step 7 self-protection taxonomy, Step 9 repair contract, fixture) is large enough that a thin wrapper does not eliminate it; (d) the operator's binding decision in the originating session was "Behave should be a separate skill" — operator preferences precede the optimal-long-term analysis. The §7 prose cites this binding decision explicitly. CF-F4 also added: §3 has a new "Boundary with `/tp`'s retrospective modes" subsection documenting the operational distinction (live critique vs post-hoc decision-integrity auditing) and the complementary-not-substitute relationship.

## 3. Falsifiability

**Concrete falsifier #1:** Phase 1 shadow mode produces ≥2 of 3 correctly classified archetype handoffs AND 0 false positives on the cleared set. **This is the strongest falsifier in the design.** If `/behave` cannot reliably diagnose past incidents the operator has already analyzed, the diagnostic methodology is not diagnostic — it is theater.

**Concrete falsifier #2:** After 6 months of operator use, the `diagnostic_use_rate` metric must exceed 3 invocations per quarter to justify the skill's existence. The design's stated target of `≥1 per incident-class` is approximately 3-4 invocations per quarter — a bar so low it would accept "barely used" as success.

**Concrete falsifier #3:** When `/behave` produces a `VERDICT_UNSUPPORTED` diagnostic, the operator is willing to act on it (i.e., the diagnostic is treated as load-bearing input to a future decision). If operators consistently ignore or down-weight `/behave` output, the skill is producing noise that the operator filters out — same failure mode as the system it was designed to detect.

**What would prove this design wrong:**
- Phase 1 fails ≥2 of 3 (falsifier #1) — methodology is unreliable
- Diagnostic use rate stays below 1 per quarter (falsifier #2) — no actual workflow integration
- Operator ignores ≥50% of `VERDICT_UNSUPPORTED` outputs (falsifier #3) — output is non-actionable

The design does not commit to falsifier #3. It commits to falsifier #1 (Phase 1 acceptance) and falsifier #2 (use rate). The absence of falsifier #3 is the most significant gap.

**Status:** addressed (CF-F6). §9 Observability has a new "Falsifier #3 — operator action on VERDICT_UNSUPPORTED" subsection: each VERDICT_UNSUPPORTED output carries an `operator_disposition: ACTED|DISPUTED|FILED|PENDING` field set by the operator within 30 days. Targets: acted-rate ≥50%, filed-rate ≤25%, acted-or-disputed rate ≥75%. Failure across two consecutive quarters invalidates the value proposition. The diagnostic_report schema now includes `operator_disposition` and `operator_disposition_deadline` fields. Risk R21 added to §11. Phase 2 acceptance in §12 now references Falsifier #3 and gates Phase 3 on it.

## 4. Anchoring

**Premise the writer brought in unexamined:** *Post-hoc diagnostic is the right layer for decision-integrity in Grok Build.* The design treats this as forced by [FACT] #1 ("no cognitive-transition hook"). The handoff and §7's alternatives analysis both fix the detection layer to "post-hoc diagnostic." But the operator's existing skills (`/tp`, `/why`, `/debrief`) all combine detection with intervention. The writer anchored on "we can't intercept verdicts, so we diagnose them after" — a defensible framing, but it assumes intervention-after-diagnosis is the only alternative to diagnosis-after-incident.

The unexamined alternative: `/behave` as a *behavioral rehearsal tool* — invoked *before* a high-stakes verdict is committed, with the same 7-dimension methodology applied to the draft verdict. This converts the skill from "post-mortem of failures" to "pre-flight check on critical decisions" — same capability, different temporal mode. The handoff does not say "post-mortem only"; it says "behavioral decision-integrity." The writer chose the post-mortem layer because it fits the incident that motivated the handoff, not because it is optimal long-term.

**The assumed-but-not-verified belief the design rests on:** *Operators will invoke a diagnostic skill consistently on the right triggers.* The design assumes the operator has or will develop a workflow that triggers `/behave` after every verdict reversal. There is no such workflow documented. The operator's existing workflow is to react to anomalies ("something went wrong"), not to invoke a diagnostic. Without an explicit invocation trigger or auto-invocation (deferred to v2), the skill is *operator-discretionary* — which means the operator will only invoke it when they already suspect something is wrong, biasing the data the skill collects.

**Status:** addressed (CF-F3). §1 Overview has a new "When to invoke /behave (CF-F3)" subsection with four concrete trigger classes: (1) post-incident operator catch, (2) /tp reversal, (3) /design verdict challenge (which surfaces the CF-F1 DEFENDED outcome), (4) recurring friction patterns. Each trigger has a worked example drawn from real or hypothetical operator workflow. The section also documents what does NOT trigger /behave (routine decisions, forward-looking design choices, /why questions) and v2 auto-invocation candidates. The "behavioral rehearsal" alternative raised in §4 of the critique is acknowledged but the post-mortem layer remains the v1 focus per the operator's binding decision; v2 candidates include pre-flight check integration.

---

## 5. User workflow fit (context-derived)

**The design assumes invocation triggers without specifying them.** The `when-to-use` frontmatter says "after any verdict transition where integrity is in question." That is the operator's judgment call — and the operator's judgment is exactly what the skill is designed to audit. The skill thus depends on the operator to recognize the trigger the operator is least equipped to recognize (because they may be exhibiting the same pattern being diagnosed).

**Specific workflow gaps:**

1. **No invocation trigger integration with `/why` or `/tp`.** When `/tp` produces a `DISPUTED` verdict (cross-model review disagreement), should `/behave` auto-fire? The design says no (auto-invocation is v2). When `/why` writes a new pattern to the wiki (Step 15c), should `/behave` auto-fire on the originating incident to validate the pattern? No mechanism exists.

2. **The `≥1 per incident-class per quarter` use-rate target is too low.** "Incident-class" is undefined in the design. If it means "verdict reversal," "user-forced reversal," "BP-pattern match," that's 3-4 invocations per quarter at minimum. But the design says `target: ≥1 per incident-class` — which permits a single invocation in any one class to satisfy the metric.

3. **Phase 1 acceptance is operator-driven, but operator-driven acceptance of a self-protective skill is itself subject to the pattern.** The operator writes their own baseline (Unit 0), then runs `/behave`, then compares. If the operator's baseline is itself influenced by self-protection patterns (defending a past decision), the comparison is contaminated. The design does not address this.

4. **No fallback for operator refusal to invoke.** If the operator refuses to run `/behave` on an incident, the incident has no diagnostic record. There is no mechanism for `/behave` to be invoked on someone else's behalf (e.g., by a future `/aar` retrospective).

**The strongest framing fix the writer should make:** identify *two specific events in the operator's current workflow* that would invoke `/behave` without operator discretion. Until then, the skill is "operator-discretionary advisory tooling" — useful but not load-bearing.

**Status:** addressed (CF-F3, overlap with §4 Anchoring). The "When to invoke /behave (CF-F3)" section under §1 documents four concrete operator-workflow triggers (post-incident operator catch, /tp reversal, /design verdict challenge, recurring friction pattern). Two of these (Triggers 2 and 3) are natural extension points: when /tp produces DISPUTED or /design produces a verdict the operator challenges, /behave has a known input. The operator-discretionary limitation is acknowledged in the frontmatter (auto-invocation deferred to v2) and in Risk Table R21's mitigation. The strongest-framing-fix recommendation (identify two specific events that would invoke without operator discretion) is partially met by Triggers 2 and 3; full automation is v2.

## 6. Observed-vs-invented (context-derived)

**The user's existing pattern question:** Is diagnostic better than improving `/tp`'s existing verification synthesis gate?

The design says `/tp` is "proactive (before a decision)" and `/behave` is "retrospective (after a verdict transition)" — a false dichotomy. `/tp` is invoked both before and after decisions (the `/tp` skill's invocation surface includes "stress-test this proposal," "review this PR," and "fresh eyes on my decision"). The retrospective case for `/tp` is already handled by `/tp`'s existing "fresh eyes" mode. Adding a `/behave` skill duplicates that capability in a narrower domain.

**Observed-vs-invented findings:**

1. **`/tp` already has a 4-tier evidence system, cross-model review, and a falsifier framework.** The design's "load-bearing finding map" (Step 3, counterfactual) is structurally similar to `/tp`'s "stress-test" mode. The "claim-to-evidence verification" (Step 4) duplicates `/tp`'s "evidence tier" gate. The "self-protection detection" (Step 7) is a `/tp` use case (`/tp --focus self-protection` would suffice). None of these required a new skill — they required a new `/tp` mode.

2. **`/why` already has feedback-to-wiki (Step 15c) and pattern-library query (Step 0.5).** The design's Step 9 (repair contract + feedback-to-wiki) duplicates `/why` Step 15c. The design's Step 0 (pattern library query) duplicates `/why` Step 0.5. The new contribution is the *retrospective temporal mode* and the *self-protection taxonomy* — both of which could be added to `/why` as a `--retrospective` flag and a `--focus self-protection` invocation.

3. **The 3-pattern scope (BP-001, BP-007, BP-008) duplicates McCormick's taxonomy verbatim.** The handoff cites the McCormick governance taxonomy as the source. If `/tp` were extended with a "self-protection taxonomy" reference, the same 3 patterns would be available without a new skill.

**Optimal long-term framing the writer rejected:** *Extend `/tp` with `--retrospective <incident-packet>` mode that runs the same 7-dimension methodology and outputs the same diagnostic schema.* The diagnostic schema (the strongest part of the design) would still be new. The skill machinery (frontmatter, catalog entry, fixture, version pinning) would not. The catalog growth concern (§10) is real but over-weighted; the operator's existing catalog tolerates `/tp`, `/why`, `/debrief`, `/review`, `/aar`, `/plan` — adding `/behave` is the seventh, not the first addition.

**Counter-argument the design does not engage:** the handoff explicitly says "this should be a separate skill from /tp." Operator preference is binding. But operator preference was given *before* the optimal long-term analysis. The critical friend should surface the question: would the operator still prefer a separate skill after seeing that ~70% of the capability could be a `/tp` mode?

**Status:** addressed (CF-F4). §3 Architecture has a new "Boundary with /tp's retrospective modes (CF-F4)" subsection with a 7-row comparison table distinguishing `/tp --fresh-eyes` (live critique on current proposal) from `/behave` (post-hoc decision-integrity audit). Operational rule documented: "is this decision right?" → /tp; "was this past decision defended against legitimate scrutiny?" → /behave. The two are complementary, not substitutes. §7 Alternative F (CF-F2) acknowledges the ~70% capability duplication with `/why` but the operator's binding decision to keep `/behave` separate is preserved. The "would operator still prefer separate skill after seeing the analysis?" question is explicitly left as the operator's prerogative — the design does not relitigate.

## 7. Provenance / identity (context-derived)

**Three identity primitives are introduced:**

1. **`operator_id`** in `metadata` block — sourced from `$GROK_OPERATOR_ID` or `$GROK_SESSION_ID` at runtime, with fallback to `"unknown"`. The design correctly disclaims this as "advisory audit-trail metadata, not used for authentication or authorization." But the field persists in every diagnostic report written to `P:/docs/handoffs/`. Cross-referencing `source_session_id` (input contract) with `operator_id` (output metadata) creates a session→operator linkage in a location (`P:/docs/handoffs/`) that has weaker access controls than the wiki. The design does not commit to access controls on diagnostic reports.

2. **`source_session_id`** in the input contract — operator-supplied. If operator supplies `"unknown"` or a path that doesn't match an existing handoff, the design falls back to `P:/docs/handoffs/_unaffiliated/behave-<date>-<sha256[:8]>.yaml`. This is good (avoids leaking operator identifiers) but creates a parallel `source_session_id` provenance system that doesn't tie into the existing `terminal_id_session_id` convention from `P:/.claude/rules/file-operations.md` (instance isolation).

3. **`input_packet_sha256`** in metadata — a content hash of the input packet. Good provenance (deterministic, content-addressed), but combined with `source_session_id`, the diagnostic report contains enough information to reconstruct which incident was diagnosed, by whom, and when. For an operator-invoked skill this is acceptable; for a skill that may be auto-invoked in v2 it becomes a fingerprinting surface.

**Unaddressed:** the wiki page `P:/.data/wiki/concepts/governance-pattern-library.md` will accumulate pattern entries with `added_by: <operator or behave run id>`. Over time this becomes an audit trail of *who identified which pattern when*. If the operator's identity is sensitive (operating on classified incidents, multi-tenant scenarios), this trail leaks pattern-detection history. The design flags `include_incident: false` as the default but does not address `added_by` provenance on the wiki entries themselves.

## 8. Cost / performance (context-derived)

**The design is reasonable on cost for v1** (operator-invoked only, no auto-invocation, cross-model review at 60s timeout). The risks are:

1. **Cross-model review cost compounds with `share_incident: true`.** If the operator enables the flag (sending full incident content to cross-model reviewer), every `/behave` invocation that hits the Step 8 trigger pays the cost of cross-model review on potentially large incident packets. The trigger fires for: ≥3 patterns (in v1 = all three), user-forced reversal, Tier 1-2 VERDICT_COLLAPSES. The first trigger is broad (any v1 invocation that detects all 3 patterns). The third is narrow. Net: maybe 30-50% of invocations dispatch cross-model review.

2. **Pattern library growth creates a maintenance burden that compounds.** Target `≥8 within 4 months of deployment` (from `P:/.data/wiki/concepts/` additions via Step 9). Each new pattern requires operator validation, cross-model review, and pattern-library wiki write. By v2 (8 patterns), the marginal cost of adding a pattern is non-trivial. The design's `Status` mechanism and retraction procedure (status=retracted) is good but adds operator overhead.

3. **Fixture maintenance is the hidden tax.** The replay fixture (`review-decision-integrity-v1.md`) becomes the regression oracle. Every change to `/behave` Step 7's BP-001/007/008 detection logic must be tested against the fixture. If the fixture ages (the 2026-07-29 incident becomes outdated), the test no longer reflects current failure modes. No fixture-refresh schedule is documented.

4. **`why_version_max` versioning creates a maintenance cliff.** Setting the upper bound forces `/behave` to be deprecated when `/why` crosses the threshold. The upgrade protocol is documented (mark `deprecated`, build new version) but the cost of the rebuild is not estimated. If `/why` releases frequently (every 2-3 months), `/behave` may need a major version every cycle.

---

## 9. Self-application paradox (open-ended domain)

**The user explicitly raised this risk.** The design acknowledges it in §16 [UNKNOWN] premise #1: "Whether a diagnostic skill can reliably detect self-protection patterns in text it is itself generating." The mitigation is cross-model review (Step 8).

**The mitigation is weaker than the risk warrants:**

1. **Step 8 trigger condition is `≥3 self-protection patterns detected`** — which in v1 means *all three* BP patterns must fire simultaneously. This is by design ("high-confidence threshold"). But the analyst-exhibits-pattern risk is precisely that the analyst might exhibit *one* pattern at high confidence (e.g., confidently defending its own diagnosis). The trigger misses this.

2. **Cross-model review uses `/why` Step 15b's prompt template** — which asks Q1 (generalize), Q2 (evidence real), Q3 (falsifier). None of these questions address the analyst-exhibits-pattern concern. Q2 ("is the evidence real") might catch a fabricated load-bearing finding, but only if the cross-model reviewer recognizes the fabrication — and the cross-model reviewer is itself an LLM subject to the same self-protection pressure.

3. **No self-audit step.** The design has Step 7 (detect self-protection in the incident) but no equivalent for detecting self-protection in `/behave`'s *own output*. There is no `/behave runs /behave on its own diagnostic report` step.

4. **The replay fixture does not test the analyst-exhibits-pattern case.** The fixture has BP-001 *attached to one of the findings in the incident*. It does not have BP-001 *attached to `/behave`'s own diagnostic report*. A fixture that tested this would need to present a diagnostic report where `/behave` itself exhibits a pattern — and the acceptance criterion would be "the diagnostic identifies the pattern in itself." The design does not commit to this.

**The strongest version of the design would include:**
- A self-audit step (Step 11 or Step 7.5) that applies BP-001/007/008 detection to `/behave`'s own draft diagnostic report
- A trigger condition that fires on any single high-confidence pattern in `/behave`'s own output, not just ≥3
- A fixture variant where `/behave`'s draft output exhibits one pattern and the acceptance criterion is self-correction

Without these, the design has a 1-1 correspondence between *the diagnostic skill detects self-protection in others* and *the diagnostic skill does not detect self-protection in itself*. The latter is the load-bearing claim.

**Status:** addressed (CF-F5). Step 8 trigger conditions rewritten with five trigger classes (was: "≥3 patterns + user-forced + Tier 1-2 VERDICT_COLLAPSES"). New triggers: (1) any severity-3 self-protection pattern; (2) ≥2 severity-2 patterns; (3) user-forced reversal; (4) Tier 1-2 VERDICT_COLLAPSES on load-bearing claim; (5) **self-audit detection in /behave's own draft**. A new self-audit paragraph documents that /behave applies its own Step 7 detector to its own draft between Step 9 and Step 10; if any pattern fires, Step 8 dispatches with the additional question to the cross-model reviewer: "Does this diagnostic report exhibit the same pattern it is diagnosing?" Unit 4 acceptance criteria updated. Risk R22 added. The single-pattern high-confidence case (severity-3) is now the load-bearing trigger, exactly as the critique requested. The "≥3 patterns" threshold was the original F-24 design choice and is explicitly rejected in the new Step 8 prose with rationale.

---

## Verdict

**REVISE.** The design has three framing issues the writer should address before implementation:

1. **User workflow integration is unspecified.** The skill is operator-discretionary without an invocation trigger. Either (a) commit to two specific operator-workflow triggers, or (b) extend `/tp` with a retrospective mode so existing workflow already invokes it.

2. **The separate-skill framing is operator-preference-driven, not optimal-long-term-driven.** The optimal design merges Steps 0/4/7/8/9 of `/behave` into `/why` (or `/tp`), reducing `/behave` to a thin retrospective wrapper. The handoff's "separate skill" preference is binding but should be re-examined after the optimal-long-term analysis is presented to the operator.

3. **The analyst-exhibits-pattern mitigation is weaker than the risk.** Cross-model review with `≥3 patterns` threshold (i.e., all three in v1) misses single-pattern self-protection in `/behave`'s own output. Add a self-audit step and broaden the trigger.

**Implementation blockers** (after framing revision):
- §16 Implementation Prerequisites #1 (`why_version_max` value) is operator input, not a design issue
- §16 Implementation Prerequisites #2 (Phase 1 test set) is operator input, not a design issue
- The replay fixture as written tests classification of a known input; consider adding a robustness variant (novel incident, expected uncertainty)

**Strengths the writer should preserve:**
- Reuse of `/why` infrastructure (pattern library, evidence tiers, cross-model review, feedback-to-wiki) — the best part of the design
- The 7-dimension output schema — well-structured, structurally enforced
- The 3 rollback modes (full removal, paused, pattern retraction) — appropriate granularity
- The `consumes:` vs. `consumes_procedures:` distinction (F-35) — surfaces the reuse ambiguity that other designs hide
- The Coupling & Code-Smell Inventory (F-23, F-08) — engages the refactor-dismissal gate honestly

**Confidence:** High on the three framing issues. Medium on the magnitude — the design is thorough enough that the framing issues may resolve during implementation review. Low on the workflow-integration recommendation — the operator's actual workflow patterns would need to be observed to validate.

**What would change this verdict:**
- If the operator confirms a specific workflow trigger (e.g., "I invoke `/behave` after every `/tp` reversal" or "I invoke it after every user-forced verdict change"), the workflow-fit issue downgrades from framing to documentation.
- If the operator re-confirms "must be separate from /tp" after seeing the optimal-long-term analysis (70% capability duplication), the observed-vs-invented issue downgrades from framing to acknowledged trade-off.
- If the design adds a self-audit step and broadens the cross-model review trigger, the analyst-exhibits-pattern issue downgrades from framing to mitigated risk.

**Note:** Phase 1 acceptance (the falsifier) is operator-driven and inherently subjective. The strongest external check on this design is `/review` on the SKILL.md after Units 1-4 land. Until then, the framing issues above are the binding concerns.
