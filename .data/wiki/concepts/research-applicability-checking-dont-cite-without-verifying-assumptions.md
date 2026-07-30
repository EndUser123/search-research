---
title: "Research applicability checking: don't cite findings without verifying their assumptions apply to your use case"
created: 2026-07-30
source: session-019fb189
tags: [research-methodology, evidence-discipline, applicability-checking, assumption-audit, llm-failure-modes, external-research, www, why, decision]
summary: >
  Research papers present findings confidently, often without clearly stating the
  conditions under which the findings hold. When an agent cites external research
  to inform a design decision (via /www or /why), it must check whether the
  research's underlying assumptions apply to its specific use case before treating
  the finding as authoritative. The failure pattern: a conditional result (e.g.,
  "multi-agent debate is dominated by voting in closed systems") gets cited as an
  unconditional conclusion ("critic-in-the-loop doesn't work"). This happened in
  session 019fb189 when the Choi et al. martingale result was applied to /why's
  critic design without checking that /why is an open, tool-calling, multi-model
  system — the opposite of the closed-system assumption the martingale proof
  depends on. The fix is a mandatory applicability check before citing research.
agent: grok
host: grok
cognitive_load: 3
verification: session-evidence
sources:
  - https://arxiv.org/abs/2508.17536 (Choi et al., NeurIPS 2025, martingale result — conditional on closed system)
  - https://arxiv.org/abs/2310.01798 (Huang et al., ICLR 2024, self-correction fails — conditional on no external feedback)
  - https://arxiv.org/html/2601.22208v1 (Riddell et al., FORGE 2026, LLM RCA failures — conditional on cloud-based simulated faults)
relations:
  - target: wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md
    type: related — the applicability check surfaced when challenging whether the martingale result applied to /why
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md
    type: extends — that concept requires local source receipts for mechanism claims; this extends to external research claims
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: related — citing research without checking applicability is a form of narrative sufficiency
---

# Research applicability checking

## Decision context

**Why this was needed:** during session 019fb189, the operator asked whether a critical agent should be in the RCA loop. The /www research cited Choi et al. (NeurIPS 2025 Spotlight) — "debate induces a martingale; all gains reduce to majority voting" — as disconfirming critic-in-the-loop. The operator challenged: "you need to challenge the assumptions that the source is based on. Do they even apply to us?"

On inspection, the martingale result assumes: (1) closed system (agents share information), (2) homogeneous models, (3) fixed-evidence tasks (math benchmarks), (4) binary correctness. Our /why use case is the opposite on every dimension: open system (tool calls produce new evidence), multi-model pool, investigative task (evidence gathered during analysis), graded correctness (causal depth, not right/wrong). The citation was an overreach — a conditional result applied unconditionally.

This is not a one-off error. Research papers routinely present findings with confidence that exceeds their scope. The agent's job is to audit that scope before citing. The cost of NOT checking: design decisions are justified by research that doesn't actually apply, leading to architectures that solve the wrong problem or reject viable approaches based on inapplicable evidence. The cost of checking: ~30 seconds per cited finding to produce one applicability row. The asymmetry favors the check.

## The failure pattern

```
Agent reads research → finds relevant-sounding conclusion → cites it as authoritative
                       ↑                                       ↑
                       doesn't check assumptions               applies unconditionally
```

The failure is structurally identical to [[reactive-pattern-matching-and-closure-pressure]]: the agent pattern-matches on a conclusion that feels relevant, then cites it without doing the work of checking whether the conditions hold. The research's confidence becomes the agent's confidence — without the research's conditions traveling with it.

This is also the same failure mode documented in [[narrative-as-signal-anti-dismissal-rule]] and [[causal-mechanism-claims-require-source-receipts-before-durable-write]] — the agent constructs a plausible narrative (the research supports my conclusion) without verifying the underlying claim (the research's assumptions match my context). The receipt rule says: before claiming a causal mechanism, cite the source code. The applicability rule extends this: before claiming research supports a design choice, cite the conditions under which the research holds and verify they match.

## The applicability check

For every external research finding cited to inform a design decision, check these dimensions:

| Dimension | Question to ask | Example (martingale result) |
|---|---|---|
| **System openness** | Does the research assume a closed system (no new information enters during the task)? Is our system open (tool calls, external data, iterative investigation)? | Research: closed system. Our use case: open (tool calls produce new evidence). **Doesn't apply.** |
| **Model homogeneity** | Does the research assume all agents are the same model? Do we have a model pool? | Research: same model. Our use case: multi-model pool (Grok + glm + codex + mmx). **Doesn't apply.** |
| **Evidence type** | Does the research use fixed-evidence tasks (answer derivable from problem statement)? Is our evidence gathered during investigation? | Research: fixed evidence (math benchmarks). Our use case: evidence gathered during analysis. **Doesn't apply.** |
| **Ground truth** | Does the research have ground truth (right/wrong answer)? Does our task have ground truth at analysis time? | Research: binary correctness. Our use case: no ground truth (root cause quality is graded, not binary). **Doesn't apply.** |
| **Task domain** | Does the research study the same domain? Math reasoning ≠ diagnostic reasoning ≠ RCA. | Research: math/QA benchmarks. Our use case: root cause analysis. **Partial overlap at best.** |
| **Scale** | Does the research test at a scale relevant to us? Lab settings ≠ production. | Research: controlled benchmarks. Our use case: production workspace with real failures. **May not transfer.** |

If ≥2 dimensions don't apply, the finding should be cited as **conditional, not authoritative**: "this result holds under conditions X, Y, Z — our use case differs on dimensions A, B, C, so applicability is uncertain."

## What "terrible research that talks as if it's great" looks like

The operator's phrase captures a real pattern in the literature. Signs to watch for:

1. **Unconditional language for conditional results.** "Multi-agent debate doesn't improve correctness" (when the actual result is "in closed systems with same-model agents on fixed-evidence tasks"). The conditions are in the paper but not in the abstract.

2. **Benchmark proxy ≠ real task.** A result on GSM8K (grade-school math) cited as evidence about RCA quality. Math has ground truth; RCA doesn't. The proxy doesn't transfer.

3. **Scale claims without scale testing.** "Our method improves reasoning" tested on 100 examples, cited as if it generalizes to all reasoning tasks.

4. **Cherry-picked ablations.** Reporting the condition that works, omitting the condition that doesn't. Reflexion reports +11% on HumanEval but the ablation showing self-reflection alone HURTS (0.60→0.52) is buried in Table 3.

5. **Conflating correlation with mechanism.** "Self-consistency improves accuracy" — but the improvement is from sampling diversity, not from the model checking its own work. The paper says this; the citation drops it.

The pattern across all five: the research's conditions (the scope of validity) are present in the paper but absent from the citation. The agent relays the headline without the conditions. This is the same structural gap as [[premature-closure-narrative-sufficiency-external-approaches]] — the agent pattern-completes on the conclusion, not on the conditions. A well-designed research-applicability gate forces the conditions to travel with the citation.

## Where this check applies

- **/www** — after Phase 2 research, before Phase 3 persistence. Every cited finding gets an applicability row.
- **/why** — when Step 0.5 (pattern library query) returns external research, or when Step 5 (Ishikawa) cites external findings.
- **/design** — when citing research to justify a design choice.
- **/red-team** — when specialists cite research in their findings.
- **Any skill that cites external sources** — the applicability check is universal.

## How to implement

Add to /www Phase 2 (after the disconfirmation pass, before Phase 3):

```
Round 2.75: Research applicability check (mandatory before persisting findings)

For each cited research finding, produce one row:
  FINDING: <one-line summary>
  CONDITIONS: <assumptions the finding depends on>
  OUR CONTEXT: <how our use case differs>
  APPLIES? <yes / partially / no / uncertain — with reason>

If ≥2 dimensions don't apply, downgrade the finding from authoritative to conditional.
State explicitly: "this result holds under X; our context differs on Y; applicability is uncertain."
```

## Worked example: the martingale applicability check (session 019fb189)

**The citation:** Choi et al. (NeurIPS 2025) — "debate induces a martingale; all gains reduce to majority voting." Originally cited as disconfirming critic-in-the-loop for /why.

**The applicability check:**

| Dimension | Research condition | Our /why context | Match? |
|---|---|---|---|
| System openness | Closed — agents share all information | Open — each tool call produces new evidence the critic can access independently | ❌ |
| Model homogeneity | Same model, same training | Multi-model pool (Grok + glm + codex + mmx) | ❌ |
| Evidence type | Fixed — answer derivable from problem statement | Investigative — evidence gathered during analysis, not given upfront | ❌ |
| Ground truth | Binary — right/wrong answer | Graded — causal depth (symptom → partial mechanism → real root) | ❌ |
| Task domain | Math/QA benchmarks (GSM8K, MMLU) | Root cause analysis (software/system failures) | ❌ (partial at best) |

**Verdict:** 5 of 5 dimensions mismatch. The martingale result does NOT apply to /why's critic-in-the-loop design. The correct citation is: "the martingale result disconfirms homogeneous closed-system debate, which is one specific implementation of critic-in-the-loop — not the pattern we'd use."

**What the corrected synthesis looks like:** instead of "concurrent critic is theater" (the unconditional reading), the synthesis should say: "a concurrent critic helps IF it brings new information (reads different files, applies a different rubric, uses a different model). Same-model same-context debate IS theater. Our system is inherently open (tool-calling, multi-model, evidence-gathering), so the martingale's closed-system assumption doesn't hold."

This is the difference between "research says don't do X" (unconditional, wrong) and "research says don't do X under conditions Y; our context violates Y; therefore the research doesn't constrain us" (conditional, correct).

This is the same structural principle as the evidence-tier system in /why: the claim's confidence cannot exceed the weakest link in its applicability chain. A research finding tested under conditions A, B, C cannot be cited as authoritative for a use case that violates A and B — the citation is Tier 4 (speculation) at best, not Tier 2 (authoritative reference). See [[convergence-gap-rca-symptom-restatement-toulmin-enforcement]] for the related pattern: a symptom-restatement dressed as a root cause is the same error as a conditional result dressed as an unconditional conclusion.

The deeper principle connects to [[problem-first-systems-decomposition]]: before applying a solution (citing a research finding), understand the system you're applying it to (your use case's actual conditions). Citing research without checking applicability is optimization without understanding — the exact failure the decomposition methodology exists to prevent.

## What this means for our workspace

1. **Every /www run** that persists findings to wiki must include applicability rows for cited research. The Round 2.75 step is mandatory, not optional.
2. **Every /why Step 0.5** that returns external research must check applicability before treating the pattern as authoritative — a wiki concept cited as pattern-library match may itself rest on research that doesn't apply.
3. **The wiki concept itself** should carry an applicability section when it cites external sources — what conditions the cited research depends on and whether they hold for our use case. This concept practices what it preaches: the Choi et al. and Huang et al. citations above include their conditions.
4. **The "terrible research" pattern is structural, not malicious.** Papers present findings confidently because that's how academic publishing works. The agent's job is to read past the confidence to the conditions — not to trust the headline.
5. **When in doubt, cite conditionally.** "This research suggests X under conditions Y; our context differs on Z; the finding may not transfer" is always safe. "Research proves X" is never safe unless all conditions match.

## Receipts

- Session 019fb189: /tp challenge by operator — "you need to challenge the assumptions that the source is based on. Do they even apply to us?"
- Choi et al. martingale: cited unconditionally in /www synthesis, corrected after /tp challenge. 5 of 5 dimensions mismatched our use case.
- Huang et al. self-correction: cited as blanket "self-correction fails," corrected to "intrinsic self-correction without external feedback fails — the condition is the key."
- Reflexion ablation: Table 3 shows self-reflection alone hurts (0.60→0.52) — the gain requires external test execution, a condition often dropped when citing the +11% headline. The headline travels; the condition doesn't.
- The operator's exact words: "some research is terrible but they talk as if they are great." This captures the core issue: confidence in presentation ≠ validity in application.

## Falsifier

If, after implementing the applicability check, the majority of cited research findings turn out to apply fully to our use case (conditions match on all dimensions), the check is unnecessary overhead. If the check consistently surfaces ≥2 mismatched dimensions per finding, it's load-bearing and should remain mandatory. Measure: run 3 /www sessions with the check; count findings where ≥2 dimensions mismatch.

If the check never surfaces mismatches, either the research genuinely applies (rare) or the agent is rubber-stamping the applicability rows (likely — the same closure pressure that causes symptom-restatement). In the latter case, the check needs an independent verifier (cross-model applicability audit).
