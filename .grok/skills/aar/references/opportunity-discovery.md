# Opportunity Discovery (conditional reference)

**Loaded when:** any trigger in SKILL.md core §promotion-triggers fires, OR the user explicitly asks for the opportunity landscape, OR the session is a successful-efficiency case where amplification/reuse/generalization opportunities are sought.

**Authority for:** opportunity source classes, 8 discovery passes, opportunity schema, expected-value dimensions, recommendation revisions, lifecycle blocks, opportunity-cost rule, rejection ledger.

**Not authority for:** the trigger itself (SKILL.md core owns that); the promotion-gate semantics (SKILL.md core owns that).

---

## Source classes (every opportunity cites ≥1)

| Source class | Example trigger |
|---|---|
| `FAILURE_DERIVED` | A command repeatedly fails because credentials are checked too late |
| `FRICTION_DERIVED` | Two review stages repeatedly produce the same findings |
| `SUCCESS_DERIVED` | A targeted external-source check overturned a bad assumption quickly |
| `CAPABILITY_DERIVED` | A security scanner was discovered inside a package whose larger orchestration may not be needed |
| `REUSE_DERIVED` | An existing detector works well and could be reused in another skill |
| `COMBINATION_DERIVED` | Native marketplace + external scanning are more valuable together than either alone |
| `SIMPLIFICATION_DERIVED` | Two stages duplicate work; one can be removed or conditionalized |
| `RISK_DERIVED` | A rare but severe failure mode has no current mitigation |
| `USER_EXPERIENCE_DERIVED` | The user had to restate a constraint that could have been asked up front |
| `LEARNING_DERIVED` | The final answer improved only after the user clarified a fact |
| `STRATEGIC_OPTION_DERIVED` | A new design space opened |
| `EXTERNAL_EVIDENCE_DERIVED` | Internet research corrected a local assumption |

## Discovery passes (optional lenses, not mandatory subsections)

Empty passes are valid. Do not pad any pass with placeholders.

| Pass | Question |
|---|---|
| A. Failure/risk | What should prevent recurrence or reduce exposure? |
| B. Friction/efficiency | What consumed effort without proportional value? |
| C. Success amplification | What worked and could become easier, reusable, or scalable? |
| D. Capability/reuse | What existing tools/artifacts/mechanisms could be reused elsewhere? |
| E. Combination | What existing capabilities become more valuable when combined? |
| F. User experience | What could reduce correction burden, ambiguity, cognitive load? |
| G. Continual learning | What should be measured across future sessions to confirm a pattern? |
| H. Preservation/no-change | What is already working and should explicitly remain unchanged? |

## Opportunity vs gap (mandatory separation)

A gap is observed. An opportunity is the hypothesised improvement. Do not jump from symptom to solution.

## Opportunity schema (mandatory; enforced by the validator)

```text
opportunity_id
title                       (concrete target; generic phrases rejected)
source_classes              (≥1 from above)
horizon                     (IMMEDIATE_LOCAL | NEAR_TERM_WORKFLOW |
                             CROSS_SKILL_REUSE | SYSTEM_CAPABILITY |
                             STRATEGIC_OPTION | CONTINUAL_LEARNING)
mechanism                   (REMOVE | SIMPLIFY | MERGE | RESEQUENCE |
                             AUTOMATE | VALIDATE | INSTRUMENT | REUSE |
                             GENERALIZE | SPECIALIZE | INTEGRATE |
                             EXPERIMENT | DOCUMENT | TRAIN_OR_PROMPT |
                             CHANGE_DECISION_RULE | NO_CHANGE_PRESERVE)
supporting_event_ids        (canonical event ids from the packet)
supporting_signal_ids       (optional; detector signals that prompted this)
observed_evidence           (what was seen — distinct from interpretation)
interpretation              (the hypothesised improvement; must differ from observed_evidence)
value_expected              (concrete future benefit, not "improves things")
beneficiary                 (who/what benefits — user, workflow, skill, etc.)
frequency_or_reach          (how often or how wide)
cost_or_burden              (implementation + maintenance + cognitive)
confidence                  (OBSERVED | INFERRED | SPECULATIVE)
key_assumptions
falsifier                   (what observation would make this not-an-opportunity)
next_evidence_needed        (what would shift confidence)
disposition                 (see Lifecycle block below)
expected_value              (≥1 ExpectedValueDimension with rating + rationale)
existing_capability_status   (optional; ABSENT | EXISTS_AND_EFFECTIVE |
                             EXISTS_BUT_NOT_INVOKED | EXISTS_BUT_INEFFECTIVE |
                             PARTIAL_OVERLAP | UNKNOWN)
existing_capability_evidence (optional; 1-sentence rationale)
```

## Expected-value dimensions (bounded ordinal ratings, no fake ROI)

Rate every applicable dimension (`VERY_HIGH` / `HIGH` / `MEDIUM` / `LOW` / `NEGLIGIBLE` / `UNKNOWN`) with a one-line rationale:

| Dimension | Question |
|---|---|
| `outcome_impact` | How much does the outcome improve? |
| `frequency_or_reach` | How often / how wide does it apply? |
| `reliability_gain` | Does it reduce failure modes? |
| `efficiency_gain` | Does it reduce effort, calls, or steps? |
| `user_experience_gain` | Does it reduce correction burden / cognitive load? |
| `learning_or_reuse_gain` | Does it compound across future sessions? |
| `implementation_cost` | How expensive to build? (HIGH = bad) |
| `maintenance_cost` | How expensive to maintain? (HIGH = bad) |
| `cognitive_burden` | Does it add mental load? (HIGH = bad) |
| `risk_of_harm` | Could it break something? (HIGH = bad) |
| `reversibility` | How easily undone? (HIGH = good) |
| `evidence_strength` | How strong is the supporting evidence? |

Do not automatically prioritise high-frequency minor improvements over rare severe-risk controls.

## Recommendation revisions classification

When a recommendation changed materially during the session, classify the revision:

| Classification | When to use |
|---|---|
| `HEALTHY_UPDATE_NEW_INFORMATION` | New user info or genuinely new evidence caused the revision |
| `HEALTHY_UPDATE_USER_PREFERENCE` | User clarified a preference |
| `AVOIDABLE_UPDATE_MISSED_AVAILABLE_EVIDENCE` | Evidence was available in-session but unexamined before the first rec |
| `AVOIDABLE_UPDATE_UNVERIFIED_ASSUMPTION` | First rec rested on an unchecked assumption that should have been verified |
| `AMBIGUOUS_REVISION` | Cannot responsibly classify |

Healthy updating is good. Do not classify every revision as a failure.

## Generic opportunities are rejected

The validator rejects opportunities whose title matches a generic phrase: `improve communication`, `do more research`, `automate this`, `add validation`, `use better prompts`, `be more careful`, `improve quality`, `do better`, `fix the process`. Concrete targets escape the blocklist.

## Lifecycle blocks (required for these dispositions)

For `MONITOR` / `BOUNDED_EXPERIMENT` / `INVESTIGATE` / `DEFER`:

```text
hypothesis              what we think will happen
evidence_needed         what future observation would shift confidence
success_signal          what would confirm the hypothesis
failure_signal          what would disconfirm it
review_trigger          when to revisit
retirement_condition    when to drop the hypothesis entirely
```

## Disposition values (every opportunity gets exactly one)

| Disposition | Meaning |
|---|---|
| `ACT_NOW` | High-confidence, small intervention; implement this session if authorized |
| `BOUNDED_EXPERIMENT` | Run a bounded experiment; compare before promoting |
| `INVESTIGATE` | Promising but needs more evidence |
| `MONITOR` | Watch for recurrence across future sessions before acting |
| `REUSE_EXISTING` | An existing capability already addresses this; route to it |
| `SIMPLIFY_OR_REMOVE` | Remove a step / merge / retire rather than add |
| `PRESERVE` | Already working; document for future reference |
| `DEFER` | Real opportunity but lower priority than other work |
| `REJECT` | Cost exceeds benefit; explicitly park |
| `NOT_WORTH_DOING` | Outside operating model |

## Opportunity cost (mandatory for major recommendations)

For every `ACT_NOW` or high-cost opportunity, answer:
- What higher-value work would this displace?
- What maintenance burden does it create?
- Is it additive, substitutive, or eliminative?
- Could a smaller intervention capture most of the value?
- Is it reversible?

## Rejection ledger (prevent re-proposal)

Every `REJECT` / `NOT_WORTH_DOING` opportunity must be recorded in `rejected_opportunities` with a normalised fingerprint. Future AARs check this ledger before emitting; a re-proposal must cite new evidence.

## Promotion challenge (still mandatory before any ACT_NOW)

Test all nine:
1. Is this actually unresolved?
2. Is it a duplicate manifestation of an existing pattern?
3. Is it a decision rather than a defect?
4. Is an existing mechanism already sufficient?
5. Would the proposed intervention have actually prevented / enabled the observed outcome?
6. Is there a smaller intervention?
7. Does it introduce shared state, stale-state, authority, concurrency, or maintenance risk?
8. Is there evidence of material user impact (or credible severe-risk reduction)?
9. Can future success be observed?
