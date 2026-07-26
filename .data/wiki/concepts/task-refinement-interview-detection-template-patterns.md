---
title: "Task refinement for AI agents — interview, detection, and template patterns"
created: 2026-07-25
source: session-2026-07-25 (/www research on improving /refine)
sources:
  - https://github.com/mattpocock/skills (Matt Pocock, grill-me / grilling / grill-with-docs)
  - https://arxiv.org/abs/2511.08798 (SAGE-Agent, Suri et al., Adobe Research / U. Maryland, ACL Findings 2026)
  - https://aclanthology.org/2025.emnlp-main.1104.pdf (Ask-when-Needed, EMNLP 2025)
  - https://docs.github.com/en/issues/tracking-your-work-with-issues/administering-issues/triaging-an-issue-with-ai (GitHub AI Issue Intake)
  - https://docs.devin.ai/product-guides/auto-triage (Devin Auto-Triage)
  - https://github.com/github/spec-kit (GitHub Spec Kit templates)
  - https://www.prodmap.ai/blog/prds-for-ai-agents/ (Prodmap Agent-Ready PRD Checklist)
  - https://medium.com/@haberlah/how-to-write-prds-for-ai-coding-agents-d60d72efb797 (David Haberlah, Replit Agent plan-build)
  - https://www.atlassian.com/agile/project-management/definition-of-ready (Atlassian INVEST)
  - https://addyosmani.com/blog/good-spec/ (Addy Osmani, "How to write a good spec for AI agents")
  - https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/ (GitHub 2,500-repo analysis)
  - https://stackoverflow.blog/2026/05/21/coding-agents-are-giving-everyone-decision-fatigue/ (Stack Overflow, decision fatigue, May 2026)
  - https://arxiv.org/html/2605.06669v2 (educational LLM false-positive defense)
  - https://medium.com/@milesk_33/when-agents-learn-to-ask-active-questioning-in-agentic-ai-f9088e249cf7 (Miles K., Active Questioning)
  - https://www.v2solutions.com/whitepapers/ai-requirements-validation-quality-consistency-guide/ (V2 Solutions IEEE 830 framework)
  - P:/.data/wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance.md (internal: templates/validators/priming)
  - P:/.data/wiki/concepts/prompting-patterns-for-ai-agent-control.md (internal: structural prompting)
  - P:/.data/wiki/concepts/workflow-definition-over-agent-capability.md (internal: workflow > agent)
tags: [task-refinement, clarification, missing-info-detection, grill-me, templates, agentic-sdlc, refine, decision-fatigue, false-positive]
summary: >
  Four families of technique for turning a vague task into an implementation-ready
  spec: (1) interview (grill-me), (2) missing-info detection, (3) forced template
  fields, (4) question budget + redundancy penalty. Disconfirmation lands hard:
  Matt Pocock's own community is migrating AWAY from one-question-per-turn (too
  slow), and false-positive clarification is the dominant new failure mode
  ("coding agents are giving everyone decision fatigue," Stack Overflow 2026).
  The transferable synthesis: any refinement skill must ship with an information-
  gain metric or it becomes a tax. Best ideas to steal: [NEEDS CLARIFICATION]
  markers + per-requirement acceptance criteria + DO NOT CHANGE blocks +
  redundancy-tracked question budget (not one-per-turn).
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified-with-disconfirmation
relations:
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance
    type: extends — adds the refinement-specific patterns to the templates/validators/priming base
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control
    type: related — structural prompting for refinement
  - target: wiki/concepts/workflow-definition-over-agent-capability
    type: related — refinement is the leftmost SDLC stage
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture
    type: related — SDLC stage mapping
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation
    type: refines — adds the false-positive-clarification failure mode
---

# Task refinement for AI agents — interview, detection, and template patterns

## Decision context

**Why this research was needed:** the operator approved building `/refine`, a
pre-plan skill that turns a vague task into an implementation-ready handoff. The
operator named three explicit research vectors: (1) Matt Pocock's `grill-me`
skill on GitHub, (2) wiki coverage of templates/scaffolding for LLMs, (3) a new
requirement — skills that detect missing info in a handoff/prompt and suggest
`/refine` first. The research goal was to find concrete patterns to steal and
disconfirm the charismatic ones before adoption.

**What the research changed:** the grill-me interview pattern — the most
charismatic idea — is partially REFUTED by Pocock's own community (one-question-
per-turn is too slow; migrating to batched). The synthesis is a hybrid: forced
template fields + redundancy-tracked question budget + 4-dimension completeness
check, with an information-gain metric as the gating discipline.

## The four families

### Family 1 — Interview (grill-me pattern)

**Canonical source:** Matt Pocock, `github.com/mattpocock/skills`, skills
`productivity/grill-me` + `productivity/grilling` + `engineering/grill-with-docs`.

**The prompt (verbatim, 6 lines from `grilling/SKILL.md`):**
> Interview me relentlessly about every aspect of this until we reach a shared
> understanding. Walk down each branch of the decision tree, resolving
> dependencies between decisions one-by-one. For each question, provide your
> recommended answer. Ask the questions one at a time, waiting for feedback on
> each question before continuing… If a fact can be found by exploring the
> environment, look it up rather than asking me. The decisions, though, are
> mine — put each one to me and wait for my answer.

**The good parts to steal:**
- **Facts vs decisions separation** — agent looks up facts in the codebase, reserves decisions for the user. This is the structural version of our "ground every claim with file:line" rule.
- **Agent provides recommended answer alongside each question** — converts the user's role from "write the spec" to "approve or override the agent's draft." Lower cognitive tax.
- **Explicit "shared understanding" gate** before action — same shape as our "smallest missing decision" rule in `/refine`.

**The bad parts (disconfirmation):**
- **One question per turn is too slow.** Pocock's own community reports: "the process could be faster… by evaluating with subagents + bringing a set of questions to be decided at once, instead of one per run."
- **Agent "too eager to receive an answer."** The interview can be performative — agent asks, user answers, agent moves on without genuinely challenging the answer.
- **Gets trapped in loops.** "Asking more questions, but not really challenging the model."

**Verdict:** take facts-vs-decisions + agent-recommends-answer. **Drop the
one-per-turn constraint** — batch the questions instead, with each carrying its
own recommendation.

### Family 2 — Missing-info detection

**Canonical sources:** SAGE-Agent (arxiv 2511.08798, Suri et al. 2026); GitHub
AI Issue Intake (production); Devin Auto-Triage; AwN (EMNLP 2025); V2 Solutions
IEEE 830 framework.

**Five named techniques:**

| Technique | Source | What it catches |
|---|---|---|
| **SAGE-Agent (EVPI question selection)** | arxiv 2511.08798 | Models uncertainty as POMDP; asks only highest Expected Value of Perfect Information question; redundancy penalty |
| **GitHub AI Issue Intake** | GitHub Docs (prod) | Labels issues `actionable` vs `needs info` based on repro/env/scope |
| **Devin Auto-Triage** | Cognition Labs | Persistent agent + scratchpad memory; dedupes; routes; "only investigate if includes stack trace" rules |
| **Ask-when-Needed (AwN)** | EMNLP 2025 | Decision rule: when tool fails or instructions incomplete, identify missing arg, ask only that; tracks A1 (asked-when-needed) and A2 (matched-expected-gap) metrics |
| **V2 IEEE 830 framework** | V2 Solutions whitepaper | 4-dimension NLP scan: Completeness / Clarity / Testability / Correctness |

**The good parts to steal:**
- **4-dimension completeness check** (V2 / IEEE 830): scan task across completeness/clarity/testability/correctness before allowing implementation. This is the "missing-info checklist" our `/refine` lacks.
- **Redundancy tracking** (AwN, SAGE): remember what was already asked across passes. Without this, refinement pass-2 re-asks what pass-1 covered.
- **Facts-vs-decisions routing** (crossover with Family 1): missing FACTS → agent looks them up; missing DECISIONS → ask user.

**The bad parts (disconfirmation):**
- **False-positive clarification blocks legitimate work.** Uniphore: "blocking the LLM introduces unnecessary latency." TrueFoundry: PII detectors add full-model-call latency. Educational LLM research (arxiv 2605.06669) explicitly defends against false-positive blocking of legitimate student queries.
- **"Knowing but Not Showing" (Su & Cardie 2026).** LLMs recognize ambiguity when explicitly asked to judge it, but in default QA mode they overwhelmingly answer directly. Retrieved context makes this WORSE — confidence rises, clarifying questions drop. Implication: bare prompting is insufficient.
- **Question budget alone under-fires.** Miles K. (Medium 2026): "without metrics like information gain, user effort, disruption cost, an agent's behaviour is difficult to evaluate."

**Verdict:** adopt the 4-dimension check + redundancy tracking. **Reject pure
question-budget caps** unless paired with information-gain measurement (which we
do not have). Default to ONE focused question per refinement pass (our current
rule), with the option to surface more in the handoff's "Open questions" field.

### Family 3 — Forced template fields

**Canonical sources:** GitHub Spec Kit; Prodmap; Replit Haberlah; Atlassian
INVEST; Addy Osmani.

**Five templates, distilled to the stealable fields:**

| Field | Source | What it forces |
|---|---|---|
| `[NEEDS CLARIFICATION: <question>]` markers | GitHub Spec Kit | Forced disclosure of unknowns; surfaces them inline rather than burying in prose |
| Per-requirement acceptance criteria (no shared DoD) | Prodmap | Each requirement gets its own testable AC; prevents "it works" vagueness |
| Rollback plan | Prodmap | Explicit rollback procedure — most templates omit this |
| Numeric NFRs (P95 < 200ms, bundle < 50kb) | Prodmap | Forces quantification of non-functional requirements |
| `[DO NOT CHANGE]` block | Replit Haberlah | Negative-space constraint — protected functionality the agent must not touch |
| Per-phase checkpoint creation | Replit Haberlah | Forced rollback anchor after each phase |
| Three-state boundary taxonomy (`✅ Always / ⚠️ Ask first / 🚫 Never`) | Addy Osmani | More actionable than flat "constraints" list |
| INVEST gate (binary pass/fail) | Atlassian | Cheap pre-write filter: Independent / Negotiable / Valuable / Estimable / Small / Testable |

**The good parts to steal for `/refine`:**
- **`[NEEDS CLARIFICATION]` markers** — surface unknowns as a structured field, not buried in prose. Goes in the handoff's "Open questions" section with a literal marker.
- **`[DO NOT CHANGE]` block** — negative-space constraints. Belongs in `/refine`'s "Non-goals" field, expanded from a flat list to a tri-state.
- **Per-requirement AC + rollback plan** — these belong in `/refine`'s "Acceptance criteria" and "Risks/constraints" fields. The rollback plan is the field our current `/refine` omits.
- **INVEST gate as pre-refinement filter** — before doing full refinement work, check: is the task even refinable? (e.g., "fix everything" fails I, N, S.)

**The bad parts (disconfirmation):**
- **Performative filling risk.** David Lapsley (LinkedIn, 2026-11): "LLMs don't fill in gaps the way experienced engineers do." The validator (per `designing-harnesses...` Technique 2) is the structural fix — without it, the template becomes theater.
- **Template theater.** Without a quality validator, the LLM fills `[NEEDS CLARIFICATION]` with thin questions to satisfy the structure.

**Verdict:** steal the field shapes, but require a validator (per existing
`designing-harnesses` concept). Templates + validators are complementary, not
substitutes.

### Family 4 — Question budget + redundancy penalty

**Canonical sources:** SAGE-Agent λ parameter; AwN metrics; Miller's 5±2 rule.

**The pattern:** cap the number of clarifying questions; penalize redundant
ones; track what was asked across passes.

**Disconfirmation:** budget alone under-fires (Miles K.). Without an
information-gain metric, a budget either drops real gaps (cap too low) or
induces fatigue (cap too high).

**Verdict for `/refine`:** keep the current "one focused question max" rule
(per AGENTS.md "evidence-first default") — it's the conservative end of the
budget. Track asked-questions in the handoff's "Open questions" field so a
follow-up `/refine` pass doesn't re-ask. Do NOT add a higher cap without an
information-gain metric.

## The synthesis — what to actually change in `/refine`

Based on the four families + disconfirmation:

| Change | Source family | Disconfirmation-survived? |
|---|---|---|
| Add **4-dimension completeness check** (completeness/clarity/testability/correctness) before allowing `status: ready-to-implement` | Family 2 | ✅ survives (with redundancy tracking) |
| Add **`[NEEDS CLARIFICATION]` marker** convention to "Open questions" field | Family 3 | ✅ survives (with validator) |
| Add **`[DO NOT CHANGE]` block** as structured non-goals (tri-state: Always / Ask / Never) | Families 3 + Addy Osmani | ✅ survives |
| Add **rollback plan** as mandatory field for irreversible work | Family 3 (Prodmap) | ✅ survives |
| Keep **one-question-per-pass** (current rule), but track asked-questions in handoff | Families 1 + 2 + 4 | ✅ survives (rejects grill-me's one-per-turn; rejects budget-without-metric) |
| Add **INVEST gate** as pre-refinement filter (skip refinement if task is unrefinable) | Family 3 (Atlassian) | ✅ survives |
| Do NOT adopt grill-me interview loop as primary mode | Family 1 | ❌ disconfirmed (community migrating away) |
| Do NOT adopt higher question budgets without information-gain metric | Family 4 | ❌ disconfirmed |

## The new requirement — skills that detect missing info and suggest `/refine`

The operator's third vector: SDLC skills should be smart enough to know when
the handoff or prompt they get is missing useful information, and suggest the
user use `/refine` first.

**Pattern (synthesized from the research):**

Every SDLC skill's entry screening should run a **3-check readiness gate**
before accepting the work:

1. **Completeness** — does the input name acceptance criteria? affected files? scope? (4-dimension check)
2. **Testability** — are the criteria actually testable, or are they "it works" / "make it better"?
3. **Verifiability** — is there a verification command, or is "the agent will know" the implicit plan?

If any check fails, the skill emits ONE sentence: *"This task is missing
<dimension>. Run `/refine <task>` first to tighten it before `/go` spends
discovery budget."* Then proceeds if the user overrides.

This is the **structural pattern from `prompting-patterns-for-ai-agent-control.md`**
(§ "alternatives gate" / "required sequence") applied at the input layer. It's
also the **3-state boundary taxonomy** from Addy Osmani (Always proceed / Ask
first / Never proceed without refinement) translated to skill entry.

**Why this is different from `/prompt-enhancer`:** `/prompt-enhancer` operates
at the prompt-wording layer (UserPromptSubmit hook). This readiness gate
operates at the work-item substance layer (skill entry screening). A prompt may
be worded perfectly while the work item is still substantively incomplete.

## What we did NOT find

- **No production-deployed EVPI-based question selector.** SAGE-Agent is research; the production systems (GitHub, Devin) use simpler heuristics. The EVPI approach is theoretically superior but has no deployment evidence at our scale.
- **No information-gain metric for clarification questions in agentic coding.** The literature acknowledges the need (Miles K., SAGE); nobody ships it. If we built one, it would be novel.
- **No evidence that performative template-filling is solvable by template design alone.** Every source that mentions it recommends a validator as the structural fix. Templates + validators are paired; neither alone suffices.

## Falsifier

This concept is wrong if:

- The 4-dimension completeness check produces false positives at >15% rate, blocking legitimate work. (Measure: track refinement-suggestion acceptance rate over 10 sessions.)
- The `[NEEDS CLARIFICATION]` marker becomes performative (LLM fills it with thin questions to satisfy structure). (Measure: spot-check 5 refined handoffs for marker quality.)
- The INVEST gate becomes a tax (users bypass it consistently). (Measure: track override rate.)
- The 3-check readiness gate at skill entry causes decision fatigue measurable in operator pushback. (Measure: count "stop asking" / "just do it" pushbacks per session.)

If any of these recur twice, iterate this concept (or the `/refine` SKILL.md)
rather than continuing.

## Relation to existing concepts

- `[[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]]` — establishes the templates + validators + priming base. This concept applies it specifically to refinement.
- `[[prompting-patterns-for-ai-agent-control]]` — structural prompting patterns (alternatives gate, required sequence, source-of-truth directives) that the readiness gate implements.
- `[[workflow-definition-over-agent-capability]]` — refinement is the leftmost SDLC stage; making it structural (not advisory) is the workflow-definition principle.
- `[[agentic-sdlc-skill-lifecycle-architecture]]` — SDLC stage mapping where `/refine` sits.
- `[[evidence-first-default-and-needless-confirmation]]` — the false-positive-clarification failure mode this concept refines.

## Receipts

This concept makes claims about external sources (cited inline with URLs) and
about our internal state. The internal-state claims:

- **`[FACT]` `/refine` exists at `C:/Users/brsth/.grok/skills/refine/SKILL.md`** — receipt: written this session, registered in skill catalog (977 skills post-regen), verified by read-back. Has "Objective / Original task (verbatim) / Acceptance criteria / Non-goals / Affected files / Verification plan / Risks-constraints / Reproduction" fields currently.
- **`[FACT]` `/refine`'s current "one focused question max" rule** — receipt: `C:/Users/brsth/.grok/skills/refine/SKILL.md` Hard Rule #4 ("One focused question max when blocked").
- **`[FACT]` `/refine`'s current 8 handoff fields** — receipt: `~/.grok/skills/refine/SKILL.md` "Step 3 — Tighten into handoff fields" table.
- **`[FACT]` AGENTS.md "evidence-first default" rule exists** — receipt: `~/.grok/AGENTS.md` § "Evidence-first default."
- **`[FACT]` `prompting-patterns-for-ai-agent-control.md` exists and documents alternatives gate / required sequence** — receipt: file exists at `P:/.data/wiki/concepts/prompting-patterns-for-ai-agent-control.md`; alternatives gate is §7, required sequence is §2.
- **`[FACT]` `designing-harnesses...` concept documents templates + validators + priming** — receipt: file read this session (Phase 1); three techniques at lines 60-100.
- **`[INFERENCE]`** the proposed changes to `/refine` (4-dimension check, `[NEEDS CLARIFICATION]` markers, `[DO NOT CHANGE]` block, rollback plan, INVEST gate) are not yet implemented. They are the synthesis this concept recommends. Each must survive a separate implementation turn against the actual `/refine` SKILL.md before becoming `[FACT]`.
- **`[INFERENCE]`** the 3-check readiness gate at SDLC skill entry is the structural translation of Addy Osmani's three-state boundary taxonomy. Not yet implemented in any skill's entry screening.
- **`[UNKNOWN]`** false-positive rate of the 4-dimension completeness check at our scale. Needs 10+ sessions of measurement.
- **`[UNKNOWN]`** whether our existing `/check` auto-/review trigger pattern (which already detects load-bearing surfaces and routes to /review) could be extended to detect under-specified tasks and route to `/refine`. Plausible but not investigated.
