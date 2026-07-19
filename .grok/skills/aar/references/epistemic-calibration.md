# Epistemic Calibration (conditional reference)

**Loaded when:** any of these triggers fire:
- Material architectural change proposed
- Durable-rule / AGENTS.md / CLAUDE.md / wiki promotion claimed
- High-severity defect (HIGH severity signal that materially affected the user)
- Cross-session aggregation or pattern claim
- Headline lesson makes a comparative claim ("X is better/more reliable than Y")
- Explicit user request for "deep root-cause" or "continual-improvement analysis"

**Authority for:** 4-dimension confidence schema, causal hierarchy, temporal-evidence reconstruction, prevention-interception test, workflow-value/process-theater test, decision-vs-outcome-quality, policy-promotion levels, full cross-field consistency invariants, final contradiction audit.

**Not authority for:** the 3-line compressed invariants in SKILL.md core (those are always loaded; this reference expands them).

---

## Multidimensional confidence (4 dimensions, each with rationale)

Replace any single "confidence" field with four separate dimensions:

| Dimension | Question | Values |
|---|---|---|
| **evidence_confidence** | How certain are we the event/condition/pattern occurred? | `VERY_HIGH` `HIGH` `MEDIUM` `LOW` `UNKNOWN` |
| **causal_confidence** | How certain are we the proposed cause explains it? | same |
| **intervention_confidence** | How certain are we the proposed intervention would help? | same |
| **scope_confidence** | How certain are we this applies beyond the observed episode? | same |

Each dimension requires a short evidence-specific rationale. Bare labels without reasons are invalid.

### Confidence guidance

| Level | Use for |
|---|---|
| `VERY_HIGH` | Direct reproducible evidence: exact failing code, reproducible exit-status failure, two runs writing same path, failing test before fix / passing after, path/naming contradiction in active source |
| `HIGH` | Strong evidence with limited unresolved alternatives: repeated isolation failure, repeated duplicate work, format gate exposing absent field, workflow step repeatedly producing no unique output |
| `MEDIUM` | Plausible but incompletely demonstrated: workflow step likely reduces load, format gate probably would have prevented recommendation, two skills appear redundant, behavioral rule likely reduces recurrence but untested |
| `LOW` | Partial, anecdotal, highly interpretive, or narrow evidence |
| `UNKNOWN` | Confidence cannot responsibly be estimated. Do not force certainty. |

### Worked contrast examples

Reproducible technical defect:
```
evidence_confidence: VERY_HIGH — two executions resolved to the same directory
causal_confidence: VERY_HIGH — run identifier was the only variable path component
intervention_confidence: HIGH — collision-resistant suffix removes the collision path
scope_confidence: HIGH — same path logic applies to every invocation
```

Workflow-theater candidate:
```
evidence_confidence: HIGH — across three runs produced no unique output
causal_confidence: MEDIUM — redundancy plausible, but task simplicity may explain it
intervention_confidence: MEDIUM — removal should reduce effort, rare cases untested
scope_confidence: LOW — evidence covers only three similar tasks
```

## Causal hierarchy

Every material causal pattern must distinguish:

| Level | Meaning |
|---|---|
| `ROOT_CAUSE` | The originating condition that, if removed, prevents the failure |
| `CONTRIBUTING_FACTOR` | Increased likelihood or severity but is not sufficient alone |
| `MANIFESTATION` | The observable symptom of the root cause |
| `CONSEQUENCE` | Downstream effect of the manifestation |

For each attached episode, state its relationship to the pattern. Do not label a symptom or consequence as root cause without an explicit causal mechanism. Permit multiple independent root causes — do not force one dominant explanation.

## Temporal evidence reconstruction

For each material decision, failure, and lesson, classify what was knowable:

| Category | Meaning |
|---|---|
| `KNOWN_AT_THE_TIME` | Evidence was available and usable at the decision point |
| `DISCOVERABLE_AT_THE_TIME` | Evidence existed but was not found |
| `LEARNED_LATER` | Evidence only appeared after the decision |
| `NOT_REASONABLY_KNOWABLE` | Evidence was not available through any reasonable effort |

Do not say "the agent already knew" unless evidence was `KNOWN_AT_THE_TIME`. Do not say "the failure was preventable" when the needed fact was `LEARNED_LATER`.

## Prevention-interception test

Every proposed prevention or intervention must specify:

```
Observed failure path: <how the failure occurred>
Interception point: <where the mechanism would act>
Mechanism: <what the mechanism does>
Would it intercept this exact path?: yes | no | partially
Prevention confidence: DEMONSTRATED | STRONGLY_SUPPORTED | PLAUSIBLE | SPECULATIVE | NOT_SUPPORTED
Residual bypass: <how the failure could still occur despite the mechanism>
```

A model can fill a format gate with plausible nonsense. Format presence alone is not proof of prevention. A generic rule with no identified interception point must not be described as preventive.

## Workflow-value and process-theater test

When recommending removal, merger, simplification, or retention of a workflow step, require:

| Field | Question |
|---|---|
| Unique output | Does it produce anything no other step produces? |
| Unique decision value | Does it change a decision no other step changes? |
| Unique risk reduction | Does it catch a defect no other step catches? |
| Downstream consumer | Who/what consumes its output? |
| Frequency of use | How often is it invoked? |
| Time or compute cost | What does it cost? |
| Cognitive burden | Does it add significant mental load? |
| Failure if removed | What breaks? |
| Evidence horizon | How many runs inform this assessment? |
| Rare-event value | Has it ever caught something severe? |

Classify: `PROVEN_VALUE` / `LIKELY_VALUE` / `UNCERTAIN_VALUE` / `LOW_OBSERVED_VALUE` / `REDUNDANT` / `PROCESS_THEATER_CANDIDATE`

Rules:
- Do not call a step "process theater" from one run.
- High-confidence removal requires repeated evidence: no unique output, no decision change, no unique defect caught, no required consumer, measurable burden — all across multiple comparable runs.
- A rare but severe catch may justify retaining a low-frequency step.
- Absence of a finding is not proof of absence of value for preventive steps.

## Decision quality vs outcome quality

For material episodes, evaluate separately:

| Dimension | Question |
|---|---|
| `decision_quality` | Was the decision reasonable given what was known at the time? |
| `execution_quality` | Was the implementation correct and efficient? |
| `outcome_quality` | Did the result achieve the intended goal? |
| `luck_or_external_effect` | Did external factors (good or bad) affect the outcome? |

A good result does not prove the process was good. A bad result does not prove the original decision was unreasonable.

## Policy-promotion levels

Every lesson or proposed durable rule must be assigned:

| Level | Criteria |
|---|---|
| `SESSION_NOTE` | Single observation, weak evidence, one-off context |
| `LOCAL_PRACTICE` | Useful for current skill/project/harness/problem class |
| `CANDIDATE_RULE` | Repeated pattern, severe event, demonstrated mechanism, or strong external evidence; requires continued validation |
| `DURABLE_POLICY` | Requires: repeated validated failures, demonstrated prevention, severe single-event exception with strong evidence, credible external evidence, clear ownership, low maintenance burden, known rollback criteria. A single session should rarely produce this. |

Do not promote AAR conclusions directly into AGENTS.md, wiki, skills, or hooks without separate authorization and the required promotion level.

## Cross-field consistency invariants (full set)

1. `NO_COMPARISON` cannot support "more reliable than" / "better than" / "superior to" / ranking intervention classes.
2. `SOURCE_PARTIAL` cannot support exhaustive coverage, "all gaps found," zero false negatives, or universal conclusions.
3. `LOW` or `UNKNOWN` causal confidence cannot directly support `DURABLE_POLICY`, irreversible structural change, or confident root-cause wording.
4. `LOW` or `UNKNOWN` intervention confidence cannot support automatic implementation or mandatory workflow changes.
5. A headline or verdict cannot have higher confidence or broader scope than its supporting body claims.
6. Reconciled accounting proves only arithmetic consistency — not completeness, correct classification, causal validity, absence of duplication, or correct promotion.
7. User input must be classified as `AUTHORITY_DECISION` / `DOMAIN_EVIDENCE` / `HYPOTHESIS` / `PREFERENCE`. User authority governs goals, constraints, and approval. Technical claims may still need verification.
8. Repeated symptoms do not prove a common root cause without a shared mechanism.
9. A simpler selected fix does not prove that its intervention class is generally superior.
10. `SPECULATIVE` prevention cannot be described as demonstrated.
11. `PROCESS_THEATER_CANDIDATE` cannot become `REDUNDANT` without sufficient repeated evidence or demonstrated lack of unique function.
12. `GENERAL` scope requires: repeated independent sessions, meaningful comparison, credible external evidence, or a mechanically universal local invariant.
13. Empty boilerplate ("no competing explanation," "high confidence," "likely works") does not satisfy a calibration field.

## Final contradiction audit (before emitting headline/verdict)

Compare all calibrated fields against each other. Flag and correct:
- confidence upgrades (headline stronger than body)
- scope upgrades (verdict broader than evidence)
- unsupported comparative language
- actions stronger than their evidence
- body caveats omitted from the headline
- claimed prevention without an interception mechanism
- completeness claims from partial evidence
- durable-policy promotion from one weak session
- process-theater claims without repeated value evidence

If unresolved, downgrade the conclusion or mark it `UNKNOWN`.
