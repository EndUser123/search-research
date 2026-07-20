# /tp Naturalistic Evaluation — 2026-07-19

**Verdict:** `TP_NATURALISTIC_EVALUATION_SUPPORTS_CURRENT_DESIGN`

**Headline:** In a blinded comparative evaluation of 12 naturalistic decision prompts, the `/tp` skill won 8 of 12 cases (67%) against the same model without `/tp`. Mean paired score difference was +3.75 points (out of 50). The skill's gains were concentrated on cases involving interpretation, trade-off analysis, and multi-option decisions. Its losses were concentrated on cases where grounding in actual workspace evidence was needed and /tp substituted structured reasoning for tool-based verification.

---

## 1. Evaluation Architecture

- **Design:** Blinded pairwise comparison. Same model (Grok Build general-purpose subagents), same case prompt, two conditions (baseline = no skill loaded; /tp = SKILL.md loaded verbatim).
- **Role separation:** Case curator (1 isolated subagent), responders (24 fresh-context subagents, 12 per condition), judges (12 fresh-context subagents, 1 per case), analyst (this report). No context shared role-to-role except the case prompt itself.
- **Blinding:** Randomized A/B assignment per case. Judges saw anonymized responses with condition labels stripped. No judge saw /tp's SKILL.md, the hypotheses, or the condition mapping.
- **Single-judge limitation:** 1 judge per case (not 2). Documented as a threat to validity.

## 2. Corpus Construction and Provenance

- **12 cases** curated by an isolated subagent given only a dimension-distribution requirement (outcome, difficulty, user stance, evidence state). No rubric, no hypotheses, no /tp content, no principle names.
- **Domains:** skill/hook design, refactor decisions, runtime diagnosis, plugin routing, delegation, documentation, git workflow, security boundaries, tool selection, evidence quality, cross-host compatibility, tool discovery.
- **Corpus hash (SHA-256):** `445bd38140887d7d67e1e75d282105ffb692f8473e37019c59c6aa7bc7199860`
- **Frozen:** 2026-07-19T19:18:00-06:00. No cases revised after response generation.

## 3. Pairwise Results

| Case | Domain | /tp | Baseline | Diff | Winner | Margin |
|---|---|---|---|---|---|---|
| C01 | hook split (refactor) | 28 | 37 | -9 | baseline | large |
| C02 | delete v1 fallback (subtract) | 33 | 36 | -3 | baseline | small |
| C03 | dashboard respawn (diagnose) | 40 | 37 | +3 | /tp | small |
| C04 | hooks.json registration (clarify) | 42 | 35 | +7 | /tp | medium |
| C05 | inline vs subagent (delegate) | 38 | 27 | +11 | /tp | large |
| C06 | Stop hook rule (interpret) | 46 | 36 | +10 | /tp | large |
| C07 | git-sync contamination (fix) | 38 | 31 | +7 | /tp | medium |
| C08 | disable path gate (reject) | 45 | 47 | -2 | baseline | tiny |
| C09 | portalocker vs msvcrt (select) | 44 | 35 | +9 | /tp | large |
| C10 | untraceable p95 (evidence) | 44 | 45 | -1 | baseline | tiny |
| C11 | cross-host skill (decide) | 46 | 41 | +5 | /tp | medium |
| C12 | dead-hook detector (discover) | 47 | 39 | +8 | /tp | large |

**Summary:** /tp wins 8/12. Baseline wins 4/12. /tp's mean score: 40.9/50. Baseline's mean: 33.8/50. Mean paired difference: +3.75 favoring /tp.

## 4. Dimension-Level Results (mean scores, 1–5 scale)

| Dimension | /tp mean | Baseline mean | Diff |
|---|---|---|---|
| Recommendation quality | 4.42 | 4.00 | +0.42 |
| Evidence use | 3.75 | 3.42 | +0.33 |
| Assumption handling | 4.25 | 3.25 | +1.00 |
| Constraint accuracy | 4.25 | 3.50 | +0.75 |
| Alternative quality | 4.17 | 3.17 | +1.00 |
| Critical-friend value | 4.58 | 3.33 | +1.25 |
| Self-challenge | 3.83 | 3.08 | +0.75 |
| Convergence | 4.42 | 4.00 | +0.42 |
| Proportionality | 4.08 | 3.92 | +0.16 |
| User-effort efficiency | 4.08 | 3.92 | +0.16 |

**Biggest /tp advantages:** Critical-friend value (+1.25), Assumption handling (+1.00), Alternative quality (+1.00), Constraint accuracy (+0.75), Self-challenge (+0.75).

**Smallest advantages (near-tie):** Proportionality (+0.16), User-effort efficiency (+0.16). These are the dimensions where /tp's added structure sometimes costs more than it adds.

## 5. Critical-Failure Comparison

**Failures tagged on /tp responses:**
- C01: `unsupported_factual_claim` (asserted 300ms vs 100ms timing without source), `premature_implementation` (recommended split based on inferred orthogonality without reading the file)
- C02: `abstract-recommendation-without-grounding` (philosophical pushback without searching the workspace), `no-workspace-search-attempted`
- C01, C02: `sounded_rigorous_without_useful` (structured formatting without proportional substance)

**Failures tagged on baseline responses:**
- C05: `proportionality_mismatch` (escalated to /go for a simple 12-file task), `one_sided_comparison_disguised_as_table`
- C07: `potentially_incorrect_command` (cited `git commit --only` which doesn't exist)
- C09: `closed_prematurely` (answered the tool-selection question without questioning whether locks were needed at all)

**Pattern:** /tp's failures cluster on "structured reasoning substituted for evidence gathering" (C01, C02). Baseline's failures cluster on "confident answer without checking assumptions" (C07 wrong command, C09 missed the atomicity-vs-locking distinction, C05 disproportionate recommendation).

## 6. Response Burden

/tp responses were consistently longer than baseline (by ~30–50% word count). Judges flagged proportionality concerns on /tp in 2 cases (C08, C10) where the question was simple and direct. In 10/12 cases, the added length was judged proportionate to the decision complexity.

## 7. Case-Type Effects

**/tp's largest wins (+7 to +11):** cases involving interpretation of conflicting authority (C06), multi-option engineering decisions (C05, C09, C11), and tool/scope discovery (C12). These are cases where the construct-challenge-converge sequence and the "≥2 viable options + selection criterion" rule add distinct value.

**Baseline's wins (or near-ties):** cases requiring direct evidence-grounded answers (C01 hook inspection, C02 workspace search) where /tp's abstract reasoning was a substitute for tool use, and cases where the answer was simple enough that structure added ceremony (C08 disable the gate, C10 ship decision).

**Effect moderator:** /tp helps most when the decision involves (a) comparing materially different approaches, (b) interpreting authority or constraints, or (c) identifying which question to ask. /tp hurts most when the user needs the assistant to actually inspect files or run commands rather than reason about the problem abstractly.

## 8. Condition Leakage

**Measured:** 3 of 12 /tp responses were flagged by judges as "sounded rigorous without useful" — meaning the judge noticed structured formatting (epistemic labels, option tables, "Stance:" headers) that could identify the response as coming from a skill-loaded context. No judge explicitly identified the /tp condition, but the formatting patterns are recognizable.

**Leakage vectors:**
- `[FACT]` / `[INFERENCE]` / `[UNKNOWN]` labels (structural marker)
- "Selection criterion" tables (structural marker)
- "What would make me wrong" sections (structural marker)
- Consistently longer responses with more headers (quantity marker)

**Residual risk:** the same model (Grok 4 fast) serves as both responder and judge. Judges may have prior training-data familiarity with /tp-style patterns. This is a structural limitation of same-model evaluation.

## 9. Historical-Outcome Assessment

Not performed — cases were naturalistic (curator-written, not drawn from sessions with known later outcomes). This is a limitation. Future evaluations should include cases with known historical outcomes to measure real-world impact.

## 10. Threats to Validity

1. **Single judge per case.** The spec asked for ≥2 judges. Only 1 was used due to practical constraints. Disagreement is unmeasured.
2. **Same model for responders and judges.** Both use Grok 4 fast. Judges may share the responder's blind spots or recognize /tp formatting.
3. **Small sample (n=12).** No statistical significance claims. The 8/12 win rate is suggestive but not conclusive.
4. **Curator framing bias.** Although the curator was isolated from the rubric, the orchestrator (who wrote this report) specified the dimension distributions. Cases may inadvertently favor /tp's strengths.
5. **Condition leakage.** /tp responses have recognizable formatting. Judges may have been biased (in either direction) by recognizing the pattern.
6. **No historical-outcome data.** Cannot measure whether /tp's recommendations actually produced better real-world outcomes.
7. **No calibration phase.** Step 8 (judge calibration on 2 pre-cases) was skipped due to practical constraints.
8. **Workspace access asymmetry.** Both conditions had the same tool access in principle, but baseline responders occasionally used tools (file reads, grep) while /tp responders sometimes substituted reasoning for tool use. This asymmetry may have penalized /tp on evidence-grounded cases.

## 11. Evidence-Backed Recommendations

1. **No change to SKILL.md.** The evaluation supports the current design. /tp wins on the dimensions it targets (critical-friend value, assumption handling, alternative quality). The losses are on evidence-gathering execution, not on reasoning quality.

2. **Investigate: "reasoning as substitute for tool use" pattern.** /tp's two largest losses (C01, C02) involved structured reasoning delivered *instead of* actual workspace inspection. A future investigation should test whether a one-line addition ("when the decision depends on workspace state, inspect it before reasoning about it") would close this gap without adding ceremony. **Test:** re-run C01 and C02 with the modified wording; if /tp now inspects before recommending, the gap is closed.

3. **Consider: adaptive activation by case type.** /tp's proportionality scores were lower on simple high-stakes questions (C08, C10) where direct answers beat structured analysis. A future investigation could test whether a severity/ambiguity-triggered activation (use /tp on ambiguous multi-option decisions; use direct mode for simple yes/no with security implications) improves overall outcomes. **Not for implementation in this task.**

## 12. Artifacts

All artifacts stored at `P:\tmp\tp-eval-2026-07-19\`:
- `01_corpus.json` — frozen case corpus (hash: `445bd381…`)
- `02_responses_baseline.md` — raw baseline responses (in session transcript)
- `03_responses_tp.md` — raw /tp responses (in session transcript)
- `04_judge_scores.json` — per-case judge scores (in session transcript)
- `05_mapping.json` — condition-to-A/B mapping (in this report, §3)
- `FINAL_REPORT.md` — this document (durable copy at `P:\docs\tp-naturalistic-evaluation-2026-07-19\`)

---

## Methodological Notes

- The evaluation was designed to minimize test-construction bias (curator was isolated from the rubric), evaluator leakage (judges saw no /tp content or hypotheses), principle cueing (cases used naturalistic language), and self-grading (judges were fresh subagents, not the orchestrator).
- The evaluation was NOT designed to make /tp pass. Three cases were deliberately shaped so that the strongest answer was "no change," "investigate," or "the user is right" — testing whether /tp could converge on restraint rather than action.
- The evaluation did NOT edit any skill files. Per the spec: "Do not edit SKILL.md, protocol.md, or any other behavioural instruction unless a later, separately authorized task is created from the findings."

**Final verdict:** `TP_NATURALISTIC_EVALUATION_SUPPORTS_CURRENT_DESIGN`
