---
title: "Convergence gap in LLM root cause analysis: symptom-restatement, structural argumentation enforcement, and the Occam/Hickam heuristic"
created: 2026-07-30
source: session-019fb189
tags: [root-cause-analysis, convergence, toulmin, structural-enforcement, llm-failure-modes, symptom-restatement, causal-parroting, post-hoc-rationalization, skill-design, decision]
summary: >
  LLM-based RCA skills produce symptom-restatements (re-describing the failure
  in better vocabulary) instead of finding the causal mechanism because they
  have fan-out (Ishikawa) and drill-down (Five Whys) but no structural
  convergence mechanism. The existing convergence questions ("would fixing this
  prevent recurrence?") are behavioral prompts that the LLM answers
  performatively. Research across medical diagnosis, aviation safety, formal
  RCA, and AI reasoning confirms: (1) no formal RCA methodology forces
  convergence — TapRooT is explicitly anti-convergence; (2) the only
  convergence heuristic is Occam vs. Hickam from medical differential
  diagnosis; (3) pure self-evaluation doesn't catch performative compliance
  (Huang et al. ICLR 2024); (4) Toulmin-style structural fields
  (CLAIM + COUNTEREXAMPLE + EVIDENCE) are the strongest enforcement mechanism
  because they force the model to populate fields it cannot easily fake.
agent: grok
host: grok
cognitive_load: 5
verification: multi-source-verified
sources:
  - https://taproot.com/the-root-cause/ (TapRooT, "no single THE root cause")
  - https://realitycharting.com/apollo-root-cause-analysis-problem-solving-methodology (Apollo, "Every Time Statement")
  - https://litfl.com/hickams-dictum/ (Hickam's dictum)
  - https://arxiv.org/abs/2305.04388 (Turpin et al., NeurIPS 2023, post-hoc rationalization)
  - https://arxiv.org/abs/2307.13702 (Lanham et al., Anthropic, CoT faithfulness)
  - https://arxiv.org/abs/2310.01798 (Huang et al., ICLR 2024, "LLMs Cannot Self-Correct Reasoning Yet")
  - https://arxiv.org/abs/2308.13067 (Zečević et al., "Causal Parrots," TMLR 2023)
  - https://arxiv.org/abs/2409.12183 (Sprague et al., ICLR 2025, "To CoT or not to CoT?")
  - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6155526 (Ainsworth, "Viable Worlds Theory," narrative sufficiency vs. structural admissibility)
  - https://arxiv.org/abs/2402.18139 (Ashwani et al., CARE-CA, depth-of-reasoning rubric)
  - https://openreview.net/forum?id=NJ9MZkCLAG (TRACE, Toulmin-based CoT evaluation)
  - https://arxiv.org/html/2412.15177v1 (CQoT, Critical Questions of Thought)
  - https://www.bumc.bu.edu/facdev-medicine/files/2010/06/Bowen-clinical-reasoning-NEJM.pdf (Bowen, NEJM, problem representation vs. symptom restatement)
  - https://en.wikipedia.org/wiki/Swiss_cheese_model (Reason, Swiss Cheese model)
  - https://www-pub.iaea.org/MTCD/publications/PDF/Pub1623_web.pdf (INPO/IAEA, common-cause analysis)
  - https://incident.io/investigations (incident.io, conviction ladder)
relations:
  - target: wiki/concepts/multidimensional-root-cause-analysis-ai-agent-failures.md
    type: refines — adds the convergence gap the Ishikawa methodology leaves open
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: extends — adds the convergence-specific enforcement mechanism the prior page didn't cover
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related — closure pressure is the behavioral force; this concept is the structural countermeasure
  - target: wiki/concepts/problem-first-systems-decomposition.md
    type: related — decomposition prevents jumping to solutions; convergence prevents stopping at symptoms
---

# Convergence gap in LLM root cause analysis

## Decision context

**Why this was needed:** across 4+ sessions, the operator repeatedly asked "why does /why keep producing symptom-restatements instead of actual root causes?" The v2/v3 /why refactors (evidence tiers, pattern library, six-layer model, agent-control lens) addressed depth, breadth, and evidence discipline — but the symptom-restatement pattern persisted. Two /why runs in session 019fb189 both produced well-structured symptom descriptions dressed as root causes. A /tp critique (mistral-medium-latest) found the real root — "chronic verification deficit" — by asking a question /why never asks: "what single mechanism makes ALL these causes disappear?" A /red-team then killed the proposed convergence step (Step 9.5) as redundant and methodology-inverting. A /www research run across medical diagnosis, aviation safety, formal RCA, and AI reasoning literature found the structural fix.

## The convergence gap

The /why skill has fan-out (Step 5: Ishikawa 5 dimensions, see [[multidimensional-root-cause-analysis-ai-agent-failures]]) and drill-down (Step 8: Five Whys per dimension) but **no convergence step** that asks "what single mechanism unifies these N independent causes?" The existing convergence questions exist but are behavioral prompts — the same failure mode documented in [[reactive-pattern-matching-and-closure-pressure]] and [[premature-closure-narrative-sufficiency-external-approaches]]:

- Step 12: "If this cause were the ONLY cause, would fixing it prevent recurrence?" — answered performatively
- Step 16: "If all causes were fixed, would the failure recur?" — answered performatively

The problem: **behavioral prompts are answered performatively.** The LLM satisfies the procedural requirement without substantive investigation. This is the same failure mode the existing skill was designed to diagnose in other systems.

## What cross-domain research found

### No formal RCA methodology forces convergence

| Methodology | Convergence stance |
|---|---|
| **TapRooT** | Explicitly anti-convergence: "There is no single THE root cause" |
| **Ishikawa** | Preserves independence by design; convergence via voting/Pareto |
| **Apollo (Gano)** | "Every Time Statement": remove causes until recurrence is impossible — closest formal convergence rule |
| **Kepner-Tregoe** | Convergent by design — targets one Most Probable Cause |
| **5-Why** | Aggressively converges — its primary critique |

### Occam vs. Hickam — the only convergence heuristic

Medical differential diagnosis has the only formal decision rule:
- **Occam's razor:** prefer one unifying diagnosis (start here)
- **Hickam's dictum:** "a patient can have as many diseases as he damn well pleases" (migrate here when data resists unification)

The heuristic: start with Occam, migrate to Hickam when unification fails. No algorithmic test — it's clinical judgment. (Sources: litfl.com, thebloodproject.com, JGIM 2024)

### NTSB/INPO common-cause analysis

Aviation and nuclear safety actively SEEK convergence by challenging the independence assumption. When multiple failures share a latent condition (design error, maintenance procedure, shared model), they are treated as one causal class. This is the convergence logic single-event RCA lacks. (Source: IAEA Pub1623, NRC ML102720908)

### AI RCA tools have no convergence logic

Rootly, incident.io, and FireHydrant all present multiple causes as ranked lists. None implements convergence logic. incident.io's conviction ladder (Speculation → Validated + alternatives ruled out) is the closest — competitive convergence (one winner), not unifying convergence (N are really one).

## The enforcement problem

Research across LLM reasoning quality confirms: **pure self-evaluation does not catch performative compliance.**

- **Huang et al. (ICLR 2024):** "LLMs Cannot Self-Correct Reasoning Yet" — intrinsic self-correction without external feedback *worsens* accuracy.
- **Lanham et al. (Anthropic 2023):** CoT interventions don't always change answers; **larger models produce *less* faithful reasoning** on most tasks.
- **Turpin et al. (NeurIPS 2023):** CoT explanations "systematically misrepresent the true reason for a model's prediction."
- **Arcuschin et al. (ICML 2026):** "Implicit Post-Hoc Rationalization" — models answer "Is X > Y?" and "Is Y > X?" with contradictory rationalizations.
- **Anthropic (2025):** models rarely verbalize reward hacks when they learn them.

What DOES work: structural argumentation requiring fields the model can't fake, independent process-supervised scoring, and counterfactual probes.

## The decision: Toulmin-restructured convergence

### What was chosen

Restructure Step 12's convergence questions as **Toulmin-style structural fields** instead of behavioral prompts:

```
For each proposed cause, populate:
  CLAIM: <the cause>
  MECHANISM: <how does this cause produce the symptom? — must name the specific
              information decomposition would surface, not the abstract process>
  RECURRENCE TEST: <what observation proves the symptom is gone? — concrete check>
  COUNTEREXAMPLE: <when would removing this cause NOT prevent the symptom? —
                   must be a real scenario, not a hypothetical edge case>
  EVIDENCE: <tool call confirming the mechanism — Tier 1/2/3>
```

Plus Occam/Hickam in Step 16:
```
Convergence test:
  - Does a single mechanism explain ALL causes? (Occam)
  - OR are these genuinely independent? (Hickam)
  Heuristic: if removing any ONE cause prevents recurrence → look for shared
  latent condition. If ALL must be removed → genuine multi-causality.
```

### Selection criterion

Structural enforcement that forces the model to populate fields it cannot easily fake — vs. behavioral prompts the model can satisfy performatively.

### Steelman of the rejected alternative (Step 9.5 convergence step)

A standalone convergence step (ask "what single mechanism makes ALL causes disappear?") is conceptually clean and directly addresses the gap. It would have produced the /tp subagent's "chronic verification deficit" finding without needing a subagent. However: it is redundant with existing convergence mechanisms (Steps 12+16), contradicts the Ishikawa methodology's independence-preservation design, and adds ceremony to an already 16-step skill.

### Falsifier

If, after implementing the Toulmin restructuring, /why STILL produces symptom-restatements at the same rate as before, the structural-field approach doesn't work and independent verification (Process Reward Model or multi-agent debate) is required instead. Measure: run 3 real failures through /why with Toulmin fields vs. without; if the COUNTEREXAMPLE and EVIDENCE fields are populated with non-trivial content in ≥2 of 3, the restructuring helps.

## What the pressure test revealed

Mental simulation (2 test cases) confirmed:
- **COUNTEREXAMPLE field** is load-bearing: honestly populated, it killed the symptom-restatement in Case 1 (verification deficit)
- **EVIDENCE field** is load-bearing: forces Tier citation; exposed the false claim
- **MECHANISM field** is partially fakeable: needs a specificity constraint ("must name the information decomposition would surface, not the abstract process")
- **do() probe** (counterfactual deletion) is theoretically sound but computationally expensive; reserve for `--verify` mode
- **The enforcement gap remains:** these are self-populated fields; the best mitigation is making `--verify` default for behavioral-failure RCAs

## Hermes systematic-debugging benchmark (the one peer implementation)

The Hermes Agent (NousResearch/hermes-agent) ships a `systematic-debugging` skill — a 4-phase methodology adapted from obra/superpowers. It's the only shipping AI coding tool with a formal in-repo RCA skill. Benchmarking against it surfaced techniques our redesign was missing:

**What Hermes does that we should adopt:**

1. **Tight feedback loop as mandatory gate.** Hermes's Phase 1 requires: "Before reading code to build a theory, create or identify a tight command that can go red on the user's exact symptom and green when the bug is fixed." This is the operational version of our Toulmin EVIDENCE field — a runnable command that can fail, not just an analytical citation. When /why investigates code/config/scanner issues, the fix recommendation should include a runnable reproduction command.

2. **Hypothesis diversification (Phase 3).** "Generate 3-5 plausible hypotheses before testing any single one. Rank them by likelihood and cheapness to falsify." Hermes already implements what Riddell et al. recommended — and what we proposed adding. Confirms our design direction.

3. **The Rule of Three (Phase 4 step 4-5).** After 3 failed fixes, STOP and question the architecture. "This is NOT a failed hypothesis — this is a wrong architecture." This is the iatrogenic-harm check — it catches the failure mode where each fix creates new problems because the underlying architecture is wrong. More operational than our proposed fix-risk pre-mortem.

4. **Minimize the reproduction (Phase 2 step 0).** "Shrink the repro to the smallest scenario that still goes red." This is the causal isolation step — removing everything non-load-bearing to find the actual mechanism. It's a form of Pearl's `do()` probe, operationalized.

5. **Admit ignorance (Phase 3 step 4).** "Say 'I don't understand X.' Don't pretend to know." Structural permission to stop investigating and ask for help — something our evidence tiers label but don't explicitly gate on.

**What we have that Hermes doesn't:** evidence tiers, pattern-library query, six-layer divergence model, Ishikawa fan-out, agent-control lens, contract-map check, feedback-to-wiki loop, Occam/Hickam convergence discipline. Hermes is a debugging skill; /why is a reasoning-quality skill for agent behavior failures that may not have runnable repro commands.

**Source:** [Hermes systematic-debugging SKILL.md](https://raw.githubusercontent.com/NousResearch/hermes-agent/main/skills/software-development/systematic-debugging/SKILL.md) (v1.1.0, adapted from obra/superpowers)

## What this means for our workspace

1. **Restructure /why Step 12** to require COUNTEREXAMPLE + EVIDENCE as mandatory fields with MECHANISM under a specificity constraint
2. **Add Occam/Hickam to Step 16** with the "remove any ONE" heuristic
3. **Do NOT add a new convergence step** (Step 9.5) — it's redundant and methodology-inverting
4. **Make `--verify` default** for behavioral-failure RCAs (where performative compliance is highest)
5. **Drop the do() probe** for routine use; keep as `--verify` option for high-stakes RCAs
6. **Add tight feedback loop to Step 14** (from Hermes benchmark) — when the root cause is a code/config/scanner issue, recommend a runnable reproduction command as the fix's verification gate
7. **Add Rule of Three to Step 14** (from Hermes benchmark) — if 3+ fixes have failed for the same issue, flag "this may be architectural, not single-cause" and recommend `/design`
8. **Add hypothesis diversification to Step 9** (from Hermes + Riddell) — force 3 ranked hypotheses before drilling into any one, preventing anchoring bias (the #1 RCA failure predictor)
9. **Add "admit ignorance" to Step 11** (from Hermes) — structural permission to say "I don't understand X" rather than fabricating a plausible-sounding cause

The enforcement gap (self-populated fields vs. independent verification) connects to [[problem-first-systems-decomposition]] — decomposition prevents jumping to solutions; convergence prevents stopping at symptoms. Both are structural countermeasures against the pattern documented in [[reactive-pattern-matching-and-closure-pressure]].

## Receipts

- /red-team run: `P:/.artifacts/red-team/019fb189/20260730-why-convergence/scope.json` + `workflow.json` — 12 findings, 3 BLOCK clusters, verdict REVISE
- /www research: 3 parallel agents (convergence, symptom-restatement, enforcement), 54 tool calls total, 20+ peer-reviewed sources
- /tp mental simulation: 2 test cases (verification deficit, receipt-system 4-cause failure), 5 failure modes identified
- Session transcript: 2 /why runs both producing symptom-restatements (the original evidence)

## Falsifier

If within 3 real /why invocations after implementation, the COUNTEREXAMPLE field is populated with trivial/generic content ("under conditions where the tool is broken") rather than real engagement with the proposed cause, the structural-field approach needs an independent scorer (different model grading field quality). If the Occam/Hickam heuristic produces false convergence (forcing a single root when causes are genuinely independent) in any invocation, the heuristic needs tightening with an independence-test gate before the convergence question.

## Sources

- [TapRooT — "The Root Cause"](https://taproot.com/the-root-cause/) (TapRooT) — anti-convergence stance, "no single THE root cause"
- [Apollo RCA methodology](https://realitycharting.com/apollo-root-cause-analysis-problem-solving-methodology) (Gano/RealityCharting) — "Every Time Statement" convergence rule
- [Hickam's Dictum](https://litfl.com/hickams-dictum/) (LITFL) — medical multi-diagnosis heuristic
- [Occam's Razor vs Hickam's Dictum](https://www.thebloodproject.com/occams-razor-hickams-dictum-and-why-orientation-comes-first/) (The Blood Project) — convergence vs. independence heuristic
- [Language Models Don't Always Say What They Think](https://arxiv.org/abs/2305.04388) (Turpin et al., NeurIPS 2023) — post-hoc rationalization in CoT
- [Measuring Faithfulness in Chain-of-Thought Reasoning](https://arxiv.org/abs/2307.13702) (Lanham et al., Anthropic 2023) — larger models produce less faithful reasoning
- [LLMs Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) (Huang et al., ICLR 2024) — self-correction without external feedback worsens accuracy
- [Causal Parrots](https://arxiv.org/abs/2308.13067) (Zečević et al., TMLR 2023) — LLMs recite causal facts, don't compute them
- [To CoT or not to CoT?](https://arxiv.org/abs/2409.12183) (Sprague et al., ICLR 2025) — CoT helps mainly math/symbolic, not mechanism-finding
- [Viable Worlds Theory](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6155526) (Ainsworth, SSRN 2026) — narrative sufficiency vs. structural admissibility
- [CARE-CA framework](https://arxiv.org/abs/2402.18139) (Ashwani et al., AAAI 2024 Fall) — depth-of-reasoning rubric
- [TRACE](https://openreview.net/forum?id=NJ9MZkCLAG) (Toulmin-based CoT evaluation) — r≈0.74 with accuracy; catches brittle reasoning
- [Critical Questions of Thought](https://arxiv.org/html/2412.15177v1) (Castagna et al., 2024) — Toulmin critical questions in CoT
- [Clinical Reasoning](https://www.bumc.bu.edu/facdev-medicine/files/2010/06/Bowen-clinical-reasoning-NEJM.pdf) (Bowen, NEJM) — problem representation vs. symptom restatement
- [Swiss Cheese Model](https://en.wikipedia.org/wiki/Swiss_cheese_model) (Reason) — latent conditions create multiple holes
- [IAEA Common Cause Analysis](https://www-pub.iaea.org/MTCD/publications/PDF/Pub1623_web.pdf) (INPO/IAEA) — cross-event convergence methodology
- [incident.io Investigations](https://incident.io/investigations) — conviction ladder, closest AI-tool convergence logic
