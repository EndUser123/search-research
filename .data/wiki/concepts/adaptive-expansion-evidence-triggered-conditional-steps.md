---
title: "Adaptive expansion: evidence-triggered conditional steps over pre-classification dispatch"
created: 2026-07-25
source: session-019f96f5
tags: [skill-design, conditional-expansion, adaptive-expertise, bayesian-adaptive, item-response-theory, llm-behavior, failure-mode, anti-premature-closure, cross-host]
summary: >
  When an investigation skill (diagnostic, root cause, audit) dispatches into
  discrete classes at Step 0 (--bug / --agent / --pattern / --system), it
  commits to a routing decision BEFORE any evidence is gathered. That
  pre-classification is itself a closure-pressure failure mode: the LLM must
  guess the failure class from phrasing alone, and misclassification silently
  selects the wrong protocol depth for the rest of the run. Adaptive
  expansion inverts this: run a fixed light-weight core (verify, state,
  divergence, evidence inventory), then let CONDITIONAL steps fire INLINE
  based on the failure's content — detected at each step from accumulated
  evidence, not from a Step 0 guess. The principle is validated in three
  independent literatures: computerized adaptive testing (CAT/IRT — select
  next item based on information value, not a pre-test), Bayesian adaptive
  clinical trial design (Chow 2008, 660 citations — planned modifications
  based on interim data), and adaptive vs routine expertise (Hatano & Inagaki
  1986 — the capacity to reason flexibly when the situation is novel). The
  hybrid (fixed core + adaptive expansion) is the empirically-supported form;
  pure-adaptive (no fixed core) underperforms because the core steps
  (observation verification, evidence inventory) are always required. The
  /why skill's v2→v3 refactor (2026-07-25) is the worked example: v2
  dispatched at Step 0 into 4 classes; v3 drops the classes and fires the
  agent-control lens, MAST check, feedback-loop detection, and contract-map
  check INLINE when the failure content involves hooks/gates/receipts/
  verification. Misclassification at Step 0 is structurally impossible
  because there is no Step 0 classification.
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
sources:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC2422839/ (Chow 2008, adaptive design methods in clinical trials, 660 citations)
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC5968224/ (Han 2018, components of CAT item selection algorithm, 53 citations)
  - https://www.psychometrics.cam.ac.uk/system/files/documents/SSRMCGibbons2016.pdf (Gibbons 2016, IRT + CAT introduction)
  - https://link.springer.com/article/10.1186/s12909-022-03990-8 (Gamborg 2023, clinical decision-making and adaptive expertise, 32 citations)
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC8908303/ (Branzetti 2022, routine vs adaptive expertise in emergency medicine, 25 citations)
  - https://centreforfacdev.ca/pdf/TLC%20Resources/Re-examining%20the%20Integration%20of%20Routine%20and%20Adaptive%20Expertise.pdf (Jensen 2022, routine + adaptive are intertwined not mutually exclusive, 11 citations)
  - https://academic.oup.com/pmj/advance-article/doi/10.1093/postmj/qgag068/8698116 (Chow 2026, cognitive ecology of medicine: generative AI + clinical reasoning)
relations:
  - target: wiki/concepts/inline-conditional-over-dispatch-for-skill-design.md
    type: refines — theirs is the decision record (5-model synthesis: codex+mimo vs glm+agy, synthesizer chose inline on evidence-fit + reversibility); mine adds the external-literature validation (CAT/IRT, Bayesian adaptive trials, adaptive expertise). Same conclusion from independent angles.
  - target: wiki/concepts/multidimensional-root-cause-analysis-ai-agent-failures.md
    type: applies-to — adaptive expansion is the routing principle for the /why Ishikawa fan-out
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related — pre-classification dispatch is itself a closure-pressure failure mode
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: related — Step 0 dispatch guesses the class from narrative, not evidence
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: related — adaptive expansion is a structural defense against premature closure
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation.md
    type: complements — both rules argue for letting evidence drive the next step
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control.md
    type: refines — adaptive expansion is a structural prompting pattern (inline conditional, not dispatch)
---

# Adaptive expansion: evidence-triggered conditional steps over pre-classification dispatch

## Decision context

**Why this concept was needed:** the `/why` skill v2 (2026-07-25) routed every invocation at Step 0 into one of four failure classes (`--bug` / `--agent` / `--pattern` / `--system`), with each class selecting a different protocol depth. The dispatch was based on phrasing cues alone ("I keep X" → pattern, "the system has no X" → system). The operator pushed back: "shouldn't our skill be adaptive and intelligent?" — exposing the core flaw: the LLM must commit to a class BEFORE gathering any evidence, and misclassification silently selects the wrong depth for the rest of the run.

**Worked example (the failure that surfaced the pattern):** the handoff's own acceptance test — "Throughout session X, I repeatedly produced incomplete work, claimed it was complete, and when caught I patched reactively" — is a **hybrid**: the "repeatedly" phrasing suggests `--pattern`, but the expected findings (feedback loop, contract-map, fail-open, enforcement boundary) require `--agent`-class depth. Forced to pick one class, the LLM has no honest answer. Composed flags (`--pattern --agent`) work but require the operator to recognize the hybrid — the failure mode the skill is supposed to diagnose.

## The two models

### Model A — Pre-classification dispatch (v2)

```
Step 0: Detect failure class from phrasing
Step 1: Run the protocol for that class
```

**Failure modes:**
- **Misclassification is silent.** The LLM picks a class, the rest of the run uses that class's depth, and no later step checks whether the class was right.
- **Hybrid failures have no honest class.** A behavioral pattern manifesting in an agent-control system is both `--pattern` and `--agent`; forcing a single class loses depth in one dimension.
- **The dispatch itself is a closure-pressure failure mode.** The LLM is asked to classify at Step 0, with no evidence, and the rest of the run depends on that classification. This is exactly the premature-closure pattern the skill exists to diagnose.
- **The operator must recognize hybrids to compose flags.** The skill's quality depends on the operator's classification skill, which inverts the value proposition.

### Model B — Adaptive expansion (v3)

```
Step 0: Detect intent only (diagnostic vs post-mortem vs explanatory)
Step 0.5: Query wiki for known patterns (evidence-driven: a match triggers pattern mode inline)
Step 1-5: Fixed core (verify, state, divergence, evidence inventory, Ishikawa fan-out)
Step 6+: Conditional steps fire INLINE based on content:
   - Failure involves hooks/gates/receipts/verification → agent-control lens
   - Systemic/subsystem absence surfaced → contract-map check
   - Recurrence signal (wiki match or operator language) → pattern-library emphasis
```

**Why it works:** the conditional steps fire on the failure's **content** (what the evidence shows), not on a Step 0 **classification** (what the phrasing suggests). Misclassification at Step 0 is structurally impossible because there is no Step 0 classification to misclassify.

## The three validating literatures

### 1. Computerized Adaptive Testing (CAT) + Item Response Theory (IRT)

The canonical pattern from psychometrics: administer the next test item based on the examinee's responses so far, not from a pre-test classification. The next item is chosen to **maximize expected information value** given the current belief about the examinee's ability.

- **Source:** Han 2018 (PMC5968224, 53 citations) — the CAT item selection algorithm has three components: content balancing, item selection criterion (usually Fisher information), and exposure control. All three are computed dynamically per item, not pre-classified.
- **Why this validates adaptive expansion:** CAT does not pre-classify the examinee into "easy" / "medium" / "hard" buckets and then administer a fixed test for that bucket. It administers one item, updates the belief, picks the next item based on the updated belief. The investigation analog: run one step, update the evidence picture, fire the next step (or not) based on what the picture shows.
- **The information-value criterion:** in CAT, the next item is the one that maximally reduces uncertainty about the latent ability. The investigation analog: the next step is the one that maximally reduces uncertainty about the root cause. Pre-classification cannot compute this because the latent state is unknown at Step 0.

### 2. Bayesian Adaptive Clinical Trial Design

The medical literature's formalization of "modify the protocol based on accrued evidence":

- **Source:** Chow 2008 (PMC2422839, 660 citations) — "adaptive design methods in clinical trials" defines adaptive design as "designs that allow for modifications based on interim data." The modifications are planned in advance (not ad hoc), but the decision to apply them is driven by accrued evidence.
- **Berry 2025** (MDPI J Clin Med, 14 citations): "the ability to consider goals such as maximizing the expected number of successful outcomes" — the protocol adapts to maximize information value per patient enrolled.
- **Why this validates adaptive expansion:** a fixed-sample trial commits to N patients and one analysis plan before enrolling anyone. An adaptive trial enrolls, analyzes interim data, and decides whether to continue, stop, expand, or re-stratify based on what the data shows. The investigation analog: a fixed-protocol RCA commits to N steps; an adaptive RCA runs light, reads evidence, then expands (or doesn't) based on what the evidence shows.

### 3. Adaptive vs Routine Expertise (Hatano & Inagaki 1986)

The cognitive theory behind why adaptive expansion is the right model for expert reasoning:

- **Routine expertise:** efficient, accurate application of mastered procedures to familiar problems. The cognitivist analog of a fixed-protocol skill: it runs the same steps every time, fast, reliable for the class of problems it was designed for.
- **Adaptive expertise:** the capacity to reason flexibly when the situation is novel — to invent or modify procedures when the standard procedure does not fit. The cognitivist analog of adaptive expansion: run the core, observe the failure's specifics, expand the procedure based on what was observed.
- **Source:** Branzetti 2022 (PMC8908303, 25 citations, emergency medicine) — "Routine expertise is the efficient and effective use of mastered skills to consistently perform a complex task at a high level of competency. Adaptive [expertise is the capacity to innovate]."
- **Jensen 2022** (11 citations, the critical refinement): routine and adaptive expertise are **intertwined, not mutually exclusive**. The two must always be viewed as coexisting — routine expertise handles the parts of the problem that fit known patterns; adaptive expertise handles the parts that don't.

**Jensen 2022 is the falsifier for pure-adaptive.** A skill that has no fixed core (everything is adaptive) underperforms on the routine parts because it re-derives what should be procedural. A skill that has no adaptive expansion (everything is fixed) underperforms on the novel parts because it applies the wrong procedure. The empirically-supported form is **hybrid: fixed core + adaptive expansion** — exactly the `/why` v3 structure.

## Why pre-classification dispatch fails for diagnostic skills specifically

Diagnostic skills (root cause, audit, incident review) have a property that makes pre-classification uniquely bad: **the classification decision is the same cognitive act as the conclusion decision.** When the LLM classifies "this is a --bug" at Step 0, it has implicitly concluded "this is not an agent-control failure" — which is the very conclusion the investigation is supposed to test. Pre-classification short-circuits the investigation by performing its conclusion first.

This is not a problem for skills where classification and conclusion are separable. A build orchestrator can pre-classify "this is a Rust project" and then run the Rust pipeline, because "is this Rust" does not depend on what the build will find. A diagnostic skill cannot pre-classify "is this an agent-control failure" because the answer depends on what the investigation will find — and the investigation has not happened yet.

**The structural fix:** defer the classification decision to the step where evidence is available. That is what inline conditional expansion does.

## The hybrid form (the empirically-supported design)

```
FIXED CORE (always runs):
  Step 0:   Intent detection (diagnostic / post-mortem / explanatory)
            [Intent IS safely pre-classifiable — phrasing determines it]
  Step 0.5: Pattern-library query (wiki lookup — evidence-driven match)
  Step 1:   Verify observation (diagnostic intent only)
  Step 2:   State the problem in one sentence
  Step 3:   Six-layer divergence model
  Step 4:   Evidence inventory + evidence-tier system
  Step 5:   Ishikawa fan-out (5 dimensions, all investigated)

ADAPTIVE EXPANSION (conditional steps fire inline based on Step 1-5 evidence):
  Step 6:   Agent-control lens → fires when failure involves
            hooks/gates/receipts/verification/subagents/multi-repo
  Step 7:   MAST coverage check → fires when Step 6 fires
  Step 10:  Harmful feedback-loop detection → fires when Step 6 fires
  Step 13:  Contract-map check → fires when Step 6 fires

ALWAYS-RUN CLOSURE:
  Step 8:   Five Whys per dimension (runs for dimensions Step 5 found causes in)
  Step 9:   Five-way classification
  Step 11:  Competing explanations + surprise/absent-evidence checks
  Step 12:  Falsifier per cause
  Step 14:  Recommend fixes
  Step 15:  Feedback-to-wiki loop (fires when systemic cause found)
  Step 16:  Output
```

**Why the fixed core is necessary (Jensen 2022):** some steps must always run because the investigation cannot proceed without them. Observation verification is always required (Step 1). Evidence inventory is always required (Step 4) — it is the basis for the tier system that underlies every later claim. Ishikawa fan-out is always required (Step 5) — it is how causes are found. Removing the fixed core to make the skill "more adaptive" would underperform on routine bugs.

**Why adaptive expansion is necessary (CAT + Bayesian):** some steps only fire for some failures. Agent-control lens (Step 6) is irrelevant for a typo; mandatory for a hook-firing bug. Pre-classifying at Step 0 forces the LLM to commit to a class before knowing whether Step 6 applies. Inline conditional expansion lets Step 6 fire when Step 5's evidence shows hooks/gates/receipts are involved — no guess required.

## Detection triggers for the agent-control expansion

The `/why` v3 implementation uses content detection at each step:

| Trigger (content cue) | Conditional step that fires |
|------------------------|----------------------------|
| Failure description mentions hook, gate, receipt, verification, subagent, multi-repo, completion claim | Step 6 agent-control lens fires |
| Step 6 fired | Steps 7, 10, 13 fire (chained conditional) |
| Investigation surfaces systemic/architectural cause (Step 9 classification) | Step 15 feedback-to-wiki fires |
| Step 0.5 wiki query returns a high-confidence match | Pattern-library emphasis mode (start from known root cause, verify/disconfirm) |
| Operator language signals recurrence ("keeps happening", "again", "repeatedly") | Step 0.5 becomes mandatory; Step 15 threshold lowered |

These triggers are **evidence-based** — they fire on what the failure shows, not on what the LLM guessed at Step 0.

## The premature-closure defense

Adaptive expansion is also a structural defense against premature closure (the #1 cognitive error in diagnosis, Webster 2021, PMC8520040). Pre-classification at Step 0 IS premature closure — the LLM closes on a class before any evidence is in. Inline conditional expansion makes that closure structurally impossible because there is no Step 0 class to close on.

This is the same pattern as differential diagnosis: forcing the generation of alternatives AFTER evidence is gathered (Step 11) is a stronger defense than forcing them BEFORE evidence is gathered (Step 0 classification), because the alternatives are grounded in what the evidence actually shows, not in what classes the skill defines.

## When NOT to use adaptive expansion

Adaptive expansion is overhead when:
- The classification is genuinely decidable from phrasing alone (e.g., language detection — "implement this in Rust" vs "implement this in Python")
- The classes map to genuinely different procedures with no shared core (then the dispatch IS the procedure)
- The cost of running the core is high relative to the cost of misclassification (then pre-classification saves time)

For diagnostic skills, none of these hold: classification is not decidable from phrasing (the receipt-system failure was phrased as "hooks not registered" but was actually a measurement bug); the classes share a core (all RCAs need observation verification + Ishikawa fan-out); and the cost of running the core is low (a few tool calls) relative to misclassification (wrong depth for the whole run).

## The /why v2→v3 refactor as the worked example

- **v2 (commit 774eb43):** Step 0 dispatched into `--bug` / `--agent` / `--pattern` / `--system` classes. The handoff's acceptance test case (recurring behavioral pattern in agent-control system) had no honest single class.
- **v3 (commit ddf793d):** Step 0 detects intent only. Steps 6, 7, 10, 13 fire inline when Step 5's evidence shows hooks/gates/receipts are involved. The hybrid case is handled automatically — Step 6 fires because the content involves agent-control systems, Step 0.5 emphasizes pattern-library because the language signals recurrence. No composed flags needed.
- **The change was made by a 5-model synthesis** (Grok + glm-5-2 + codex + agy + mimo). Two models (codex + mimo) argued for inline conditional expansion over dispatch. The operator concurred: "shouldn't our skill be adaptive and intelligent?"

## Falsifier

This methodology is wrong if, after applying it to 5+ diagnostic skills, adaptive expansion consistently underperforms pre-classification dispatch. The specific failure modes to watch for:

- **Inline triggers never fire on real agent-control failures.** The content trigger is too narrow. Fix: broaden the trigger vocabulary; add trigger terms as new agent-control surfaces emerge.
- **Inline triggers fire on ordinary bugs.** The content trigger is too broad. Fix: tighten the trigger — require Step 5 evidence, not just Step 2 phrasing.
- **The fixed core is too heavy for trivial bugs.** The core steps (1-5) take too long for "fix this typo" investigations. Fix: add a `--quick` override that skips the core for cases the operator has pre-classified as trivial (this is the one legitimate use of a flag — when the OPERATOR, not the LLM, has made the classification).
- **Adaptive expansion re-derives the same classification every time.** If Step 6 always fires because every failure involves agent-control systems, the trigger is not discriminating. Fix: investigate whether the workspace has any non-agent-control failures; if not, the trigger is correct (the workspace is genuinely agent-control-heavy) but the skill is over-engineered for this workspace.

**Validation:** the `/why` v3 A/B test against `/why-old` (preserved at `C:\Users\brsth\.grok\skills\why-old\SKILL.md`). If v3 produces equal or deeper findings than v2 on 3+ failures without the operator needing to pass dispatch flags, adaptive expansion is validated.

## Sources

- [Chow 2008: Adaptive design methods in clinical trials](https://pmc.ncbi.nlm.nih.gov/articles/PMC2422839/) (660 citations) — the canonical medical literature on adaptive trial design: planned modifications based on interim data
- [Han 2018: Components of the CAT item selection algorithm](https://pmc.ncbi.nlm.nih.gov/articles/PMC5968224/) (53 citations) — the three components of computerized adaptive testing item selection, all computed dynamically per item
- [Gibbons 2016: Introduction to IRT and CAT](https://www.psychometrics.cam.ac.uk/system/files/documents/SSRMCGibbons2016.pdf) — accessible introduction to item response theory and why the next item is chosen based on accumulated evidence
- [Gamborg 2023: Clinical decision-making and adaptive expertise in residency](https://link.springer.com/article/10.1186/s12909-022-03990-8) (32 citations) — think-aloud study of how novice physicians develop adaptive expertise
- [Branzetti 2022: The optimal outcome of emergency medicine training](https://pmc.ncbi.nlm.nih.gov/articles/PMC8908303/) (25 citations) — defines routine vs adaptive expertise in medical education
- [Jensen 2022: Re-examining the integration of routine and adaptive expertise](https://centreforfacdev.ca/pdf/TLC%20Resources/Re-examining%20the%20Integration%20of%20Routine%20and%20Adaptive%20Expertise.pdf) (11 citations) — the critical refinement: routine and adaptive are intertwined, not mutually exclusive. This is the falsifier for pure-adaptive and the validation for the hybrid form.
- [Chow 2026: Cognitive ecology of medicine — generative AI + clinical reasoning](https://academic.oup.com/pmj/advance-article/doi/10.1093/postmj/qgag068/8698116) (1 citation) — recent extension to the LLM-as-clinician setting

## Application to other skills

This pattern applies beyond `/why`:

- **`/check`** could benefit from adaptive expansion — instead of detecting concern types upfront and spawning fixed verifiers per type, run a quick scan first and spawn verifiers based on what the scan found (code? then Phase B; doc-only? then Phase A only; contract? then schema-diff). The current skill already does some of this with concern-type tagging (F6).
- **`/review`** auto-infers lenses from the diff — that is adaptive expansion applied to the review target.
- **`/red-team`** adaptive expansion would run light first, then expand specialist categories based on what the initial scan found.
- **Any skill with dispatch classes** is a candidate. The rule of thumb: if the dispatch classification depends on evidence the skill will gather later, replace it with inline conditional expansion.

## Related concepts

- [[multidimensional-root-cause-analysis-ai-agent-failures]] — the methodology whose routing this concept refines
- [[reactive-pattern-matching-and-closure-pressure]] — the behavioral pattern that makes pre-classification a closure-pressure failure mode
- [[plausible-narratives-substitute-for-verification]] — pre-classification guesses the class from narrative, not evidence
- [[evidence-first-default-and-needless-confirmation]] — both rules argue for letting evidence drive the next step
- [[prompting-patterns-for-ai-agent-control]] — adaptive expansion is a structural prompting pattern (inline conditional, § in the patterns catalog)
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
