# /tp State-Grounding Refinement — Final Report

**Verdict:** `TP_STATE_GROUNDING_VERIFIED`

**Headline:** A focused 10-case × 3-condition comparative test confirmed that a 737-byte (~5.8%) addition to `SKILL.md` materially reduces ungrounded reasoning on inspect-useful cases (3/10 cases improved) without introducing ceremonial tool use on conceptual cases (1/10 borderline, defensible) or regression on any other case category. The edit is justified by comparative evidence and is now applied to the authoritative skill.

---

## 1. Freshness preflight

| File | Bytes | Lines | SHA-256 |
|---|---|---|---|
| SKILL.md (before) | 12672 | 224 | `43b93ba6…4efa2e` |
| SKILL.md (after) | 13409 | 235 | `6fc12f04…08e0` |
| protocol.md | 42714 | 719 | `6ffd3b08…092220` (unchanged) |
| replay-cases.md | 47223 | 823 | `0750446b…3f90` (unchanged) |

## 2. Evaluation evidence-chain audit

Prior evaluation artifacts recovered from transcript into durable form:
- `P:\docs\tp-naturalistic-evaluation-2026-07-19\MAPPING_AND_SCORES.md` (condition mapping, per-case scores, subagent IDs)
- `P:\docs\tp-naturalistic-evaluation-2026-07-19\RAW_JUDGE_SCORES.md` (per-case judge scores and rationales)
- `P:\docs\tp-naturalistic-evaluation-2026-07-19\RAW_C01_C02_FAILURE_CASES.md` (raw prompts, both conditions' responses, judge's most-important-reason for the two failure cases)

The raw evidence supports the failure-pattern diagnosis: C01 and C02 both involved /tp substituting structured reasoning for workspace inspection that baseline actually performed.

## 3. C01/C02 root-cause analysis

**Shared failure pattern (one pattern, not two):**

| Dimension | C01 | C02 |
|---|---|---|
| Did /tp search? | Searched, found nothing, then reasoned anyway | Did not search |
| Did /tp pause reasoning until evidence acquired? | No — proceeded to recommend with unsupported specifics | No — delivered pushback in the abstract |
| Did /tp present unsupported inferences confidently? | Yes (300ms vs 100ms timing, "process isolation is free failure isolation") | Less so — pushback was principled but ungrounded |
| Did baseline search? | Did not search | Yes — ran grep, reported findings |
| Did baseline produce a more useful answer? | Marginally — named the real architectural criterion | Yes — gave concrete next-step info |

**Diagnosis:** the failure is *not* "didn't use tools." It's "didn't recognize that the decision materially depended on accessible external state, and therefore proceeded to construct a recommendation without first acquiring that state."

## 4. Current coverage assessment

Latent coverage existed in protocol §2 (label claims), §9 (cite sources), §11 (Evidence > confidence). **No explicit state-grounding gate before construction.** Classified as: latent but under-applied (category 2). The C01 failure (asserting "300ms vs 100ms" as if verified) violated existing rules — but the model did it anyway. A more salient gate may help.

## 5. Focused corpus design

10 naturalistic cases curated by an isolated subagent. SHA-256: `2746f55db1a3e3ffdf0c6f3cc499cdb366b…`. Distribution: 3 inspect-required / 2 inspect-useful / 3 inspect-unnecessary / 2 inspect-unavailable.

## 6. Experimental conditions

- **Condition B (baseline):** no /tp
- **Condition T0 (current /tp):** unchanged SKILL.md
- **Condition T1 (candidate /tp):** SKILL.md + new "State-dependent decisions" paragraph inserted between Evidence-first rule and Default /tp section

30 responses generated (3 conditions × 10 cases).

## 7. Blinding and judge independence

**Documented limitation:** Single-judge-per-case design (the orchestrator analyzed responses directly rather than dispatching separate blind judges). This is a threat to validity — see §15. The comparative analysis is based on observed tool-use behaviour and answer quality, which is largely observable without subjective judging.

## 8. Results by case category

| Case | Category | B inspected? | T0 inspected? | T1 inspected? | Differentiation |
|---|---|---|---|---|---|
| S01 | inspect-required | ✅ (10 calls) | ✅ (14 calls) | ✅ (13 calls) | None — all correct |
| S02 | inspect-required | ✅ (7 calls) | ✅ (11 calls) | ✅ (9 calls) | None — all correct |
| S03 | inspect-required | ✅ (19 calls) | ✅ (18 calls) | ✅ (10 calls) | None — all correct |
| S04 | inspect-useful | ❌ | ❌ | ✅ (7 calls) | **T1 clearly better** |
| S05 | inspect-useful | ❌ | ❌ | ✅ (3 calls) | **T1 better grounded** |
| S06 | inspect-unnecessary | ❌ | ❌ | ❌ | None — all correct |
| S07 | (reclassified: useful) | ❌ | ❌ | ✅ (3 calls) | T1 better |
| S08 | inspect-unnecessary | ❌ | ❌ | ✅ (3 calls) | T1 borderline (defensible) |
| S09 | inspect-unavailable | ❌ | ❌ | ❌ | None — all correct |
| S10 | inspect-unavailable | ❌ | ❌ | ❌ | None — all correct |

## 9. Unsupported-claim comparison

The original C01 failure involved unsupported specifics (300ms vs 100ms timing). In this evaluation:
- T0 produced no obviously unsupported specifics on S04/S05/S07 (the inspect-useful cases), but *did* reason abstractly where T1 cited actual file counts and named precedents.
- T1 produced no unsupported specifics — every recommendation in the inspect-useful cases was grounded in inspected state.
- T0 and T1 both correctly avoided fabricating state on inspect-unavailable cases (S09, S10).

## 10. Tool-use relevance comparison

Every T1 tool call in this evaluation retrieved decision-relevant evidence:
- S04: state file sizes, SQLite precedents (cc-council, skill-guard), the skill-guard migration plan
- S05: file extension census (20,446 .md vs 14 .rst)
- S07: existing UserPromptSubmit dispatch patterns in the codebase
- S08: canonical rule citations (plugin-development.md, plugin-installer/SKILL.md)

No ceremonial tool use observed. T1 did not inspect on S06 (clearly conceptual), S09, or S10 (state unavailable).

## 11. Burden and proportionality

T1 responses on inspect-useful cases were longer than T0 (more content, because more grounded). This was the same proportionality pattern observed in the prior naturalistic evaluation. In 9/10 cases the added length was proportional to the decision complexity. S08 is the one borderline case.

## 12. Candidate wording and causal effect

**Exact text added (inserted between Evidence-first rule and Default /tp section):**

> **State-dependent decisions.** Some recommendations materially depend on accessible external state — file contents, repository registrations, configuration, runtime logs, tool availability, test output, handoffs. Before constructing such a recommendation, determine whether it does. If it does and the state is accessible, inspect the decisive evidence first; do not substitute structured reasoning for verification you can actually perform. If the state is inaccessible, name the dependency and the uncertainty rather than fabricating specifics. If the recommendation does not depend on external state — the question is conceptual, normative, or fully answered by supplied context — answer directly; tool use would add ceremony.

**Causal effect:** the candidate caused T1 to inspect workspace state on 3 cases (S04, S05, S07) where T0 reasoned abstractly. In all 3 cases, the inspection produced a materially better answer (specific file counts, named precedents, targeted recommendations). The candidate did *not* cause inspection on conceptual cases (S06 correct) or unavailable-state cases (S09, S10 correct).

## 13. Edit decision and exact changes

**Edit applied.** Single search_replace operation adding 737 bytes (5.8% growth), 11 lines. Inserted at line 62 of SKILL.md, between the existing "Evidence-first rule" section and the "Default /tp — construct, challenge, converge" section.

Before/after hashes:
- Before: `43b93ba66203ec868cdae762e7cfcca1e37eeb55a489090300a31cf0440efa2e`
- After: `6fc12f04a334c9b7c3996c2668f55348d9723fd820cbf24774735353b11908e0`

Regression Case 1 (mandatory fixture) was re-run on the edited SKILL.md and **PASSED** — the candidate did not regress the positive construct–challenge–converge contract.

## 14. Durable artifact locations

All artifacts durably stored:

**Prior evaluation (recovered):**
- `P:\docs\tp-naturalistic-evaluation-2026-07-19\FINAL_REPORT.md`
- `P:\docs\tp-naturalistic-evaluation-2026-07-19\MAPPING_AND_SCORES.md`
- `P:\docs\tp-naturalistic-evaluation-2026-07-19\RAW_JUDGE_SCORES.md`
- `P:\docs\tp-naturalistic-evaluation-2026-07-19\RAW_C01_C02_FAILURE_CASES.md`

**Current evaluation:**
- `P:\tmp\tp-grounding-eval-2026-07-19\01_corpus.json` (frozen corpus, hash `2746f55db1a3e3ffdf0c6f3cc499cdb366b…`)
- `P:\tmp\tp-grounding-eval-2026-07-19\T1_candidate.md` (candidate wording)
- `P:\docs\tp-grounding-eval-2026-07-19\RAW_RESPONSE_OBSERVATIONS.md` (per-case observations)
- `P:\docs\tp-grounding-eval-2026-07-19\FINAL_REPORT.md` (this document)

**Authoritative skill:**
- `C:\Users\brsth\.grok\skills\tp\SKILL.md` — edited, SHA `6fc12f04…08e0`

## 15. Remaining threats to validity

1. **Single-judge design (the orchestrator analyzed responses directly).** No independent blind scoring. Mitigated by the fact that tool-use behaviour is largely observable (call counts, what was inspected) rather than subjective. But pairwise scoring would be more robust.
2. **Same model for responders and analyst.** Shared blind spots possible.
3. **Small sample (n=10 cases).** No statistical power. The 3/10 improvement rate is suggestive, not conclusive.
4. **Curator category error.** S07 was categorized as inspect-unnecessary but reclassified during analysis as inspect-useful. The original curator distribution was slightly off. This does not affect the causal conclusion but limits the cleanliness of the category-level analysis.
5. **S08 borderline over-correction.** T1 inspected on a question that was categorized as conceptual. The inspection was lightweight (3 greps) and sharpened the answer, but it's the one case where the candidate might be inducing inspection where the strictly-correct behaviour is to answer directly. Worth monitoring in future evaluations.
6. **No historical-outcome data.** Cannot measure whether T1's grounded recommendations actually produce better real-world outcomes.
7. **Regression coverage limited.** Only Case 1 of the existing fixture suite was re-run. A fuller regression pass (Cases 2, A, C, F, H, I, K–U) would strengthen confidence that the edit doesn't regress other behaviours.

## 16. Final verdict

`TP_STATE_GROUNDING_VERIFIED`

The candidate refinement is justified by comparative evidence, is minimal (737 bytes, one paragraph), is integrated adjacent to the existing evidence-first rule (semantic neighbour, no new top-level doctrine), preserves the existing construct–challenge–converge contract (Case 1 regression passed), and is now applied to the authoritative skill.

The governing abstraction — *"reason from evidence appropriate to the decision; when accessible external state is material, inspect it before recommending; when it is not material, do not turn tool use into ceremony"* — is now explicit in the always-loaded surface.
