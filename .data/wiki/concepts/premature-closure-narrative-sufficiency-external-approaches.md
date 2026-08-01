---
title: "Premature closure and narrative sufficiency: the LLM diagnostic error pattern and external mitigation approaches"
created: 2026-07-25
source: session-019f94c9-www-research
tags: [premature-closure, narrative-sufficiency, verification, llm-failure-modes, cognitive-bias, structural-fixes, external-research, diagnostic-error, root-cause-analysis]
summary: >
  The LLM pattern where a plausible narrative closes the reasoning loop before
  evidence verification is not unique to AI — it's the #1 cognitive error in
  medical diagnosis ("premature closure"), well-documented in software engineering
  ("confirmation bias"), and now appearing in AI agent systems ("agreement bias").
  Five external mitigation approaches are evaluated with what practitioners like
  and dislike about each. The key insight: medical diagnosis has the most mature
  literature because it has studied this error for decades; the AI field is
  rediscovering the same pattern. Our workspace implements 4 of 5 approaches
  already; the gap is applying a pre-execution checklist to diagnostic claims
  made mid-session during investigation — the one class of claim none of our
  existing infrastructure targets.
agent: grok
host: grok
cognitive_load: 5
verification: multi-source-verified
sources:
  - https://www.proof.com/blog/agentic-ai-needs-verifiable-records (Proof, May 2026)
  - https://discuss.huggingface.co/t/if-unsure-ask-never-guess-ai-agent-pre-execution-checklist/176632 (Jang-woo, Jun 2026)
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC8520040/ (Webster 2021, cognitive biases in diagnosis, 88 citations)
  - https://cacm.acm.org/research/cognitive-biases-in-software-development/ (Chattopadhyay, CACM, 20 citations)
  - https://www.fhea.com/resource-center/cognitive-errors-in-clinical-diagnosis-availability-bias-and-premature-closure/ (FHEA, 2021)
  - https://openreview.net/forum?id=rwo7bVlnzo (Andrade et al., agreement bias in MLLMs, 4 citations)
  - https://addyosmani.com/blog/loop-engineering/ (Osmani, Jun 2026)
  - https://asmepublications.onlinelibrary.wiley.com/doi/full/10.1111/medu.70229 (Al Essa, premature closure in medical education)
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: extends — this page adds external validation and mitigation approaches
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: extends — this page grounds the parent pattern in cross-field literature
  - target: wiki/concepts/problem-first-systems-decomposition.md
    type: related — decomposition prevents the same failure class
  - target: wiki/concepts/fabricated-causal-chain-receipt-required.md
    type: related — both target narrative-before-evidence; different entry points
---

# Premature closure and narrative sufficiency: external approaches

## Decision context

**Why this research was needed:** session 2026-07-25 produced a specific failure instance where the agent concluded "receipt system hooks are not registered" from evaluation summaries showing zeros, without checking raw evidence (receipt files that existed and had real data). The operator asked: how do other people address this pattern? What do they like and don't like about their approaches?

The failure is documented in our wiki at [[reactive-pattern-matching-and-closure-pressure]] (the root cause) and [[plausible-narratives-substitute-for-verification]] (the parent pattern with 8 disguises). This page adds: (1) external cross-field validation that the pattern is real and well-studied, (2) five concrete mitigation approaches with honest trade-offs, (3) the specific gap in our workspace that let the failure through.

## The pattern is not unique to AI

The pattern we've been calling "narrative sufficiency" or "closure-pressure minimization" is well-studied in three fields under different names. The convergence is itself evidence that this is a structural cognitive property, not a model-specific bug.

### In medical diagnosis: "Premature closure"

**Definition:** "Arriving at a conclusion or diagnosis too early without considering all possibilities." (Webster 2021, PMC8520040, 88 citations)

**Why it matters clinically:** premature closure is the #1 cognitive error in diagnostic medicine. Al Essa (Medical Education) demonstrated empirically that premature closure mediates between biasing information and diagnostic error — it's the mechanism through which other biases (availability, anchoring, confirmation) produce wrong diagnoses.

**Key insight from the medical literature:** the error is not "reaching a conclusion" — conclusions are the goal of diagnosis. The error is reaching a conclusion **without having generated and considered alternatives.** The clinician locks onto the first plausible hypothesis and stops searching. The mitigation is structural: force generation of alternatives before commitment (differential diagnosis), and require time-delayed review where possible.

**Relevance to AI agents:** the medical literature has studied this error for decades and has the most mature mitigation framework. The AI agent field is rediscovering the same pattern with new terminology but fewer tested mitigations.

### In software engineering: "Confirmation bias"

**Definition:** "Subconsciously filtering information to favor our existing hypothesis." (Chattopadhyay, CACM, 20 citations)

**Key finding:** developers spend disproportionately more time on confirming evidence than disconfirming evidence. Colesoft (Overcoming Cognitive Bias in Software Engineering) notes: "confirmation bias causes us to see what we expect rather than what exists on the screen. Our mind helpfully fills in gaps, mentally corrects logic errors, and skips over inconsistencies."

**Relevance to AI agents:** the developer pattern maps directly to LLM behavior. The agent generates a plausible narrative ("evaluation summaries show zeros → hooks not registered"), then seeks confirming evidence (reads more evaluation summaries) rather than disconfirming evidence (reads raw receipt files). The mechanism is the same; the substrate is different.

### In AI agent research: "Agreement bias" and "narrative sufficiency"

**Definition:** MLLMs have "a strong tendency to over-validate agent behavior — a phenomenon we term agreement bias." (Andrade et al., OpenReview, 4 citations, 2026)

**Key finding:** the model agrees with claims too readily because agreement is the pattern-completion pathway — it produces a satisfying, coherent response. Self-correction (asking the model to argue against its own agreement) helps but degrades under the same closure pressure that produced the bias.

**Relevance to our workspace:** this is the exact mechanism documented in [[reactive-pattern-matching-and-closure-pressure]] — pattern completion overrides evidence evaluation. Andrade's finding that self-correction degrades under pressure matches our observation that self-applied rules (receipt rule, epistemic classification) fire probabilistically, not deterministically.

## Five external mitigation approaches

Each approach is evaluated with: what it does, what practitioners like, what they don't like, and whether it would have prevented the specific failure this session (concluding "hooks not registered" from evaluation-summary zeros without checking raw receipt files).

### Approach 1: Pre-Execution Checklist (Jang-woo, HuggingFace, Jun 2026)

**Source:** [If unsure, ask. Never guess. — AI Agent Pre-Execution Checklist](https://discuss.huggingface.co/t/if-unsure-ask-never-guess-ai-agent-pre-execution-checklist/176632)

**What it is:** a structured checklist that MUST be filled before any action executes. Three layers:
- **Fixed Checklist** (C1: when/case, C2: user intent, C3: provider action) — defines the execution unit
- **Provider Checklist** — execution precautions defined by the system/tool owner
- **User Checklist** — custom rules from the user

If any item is `unknown`, execution does not proceed. The core principle: *"If any unknown remains, do not proceed. Always ask the user or place execution on hold."*

Jang-woo also defines an **Execution Pattern taxonomy** that determines checklist depth:

| Pattern | Reversibility | Human Verifiability | Checklist Focus |
|---------|--------------|--------------------|-----------------|
| Self-Contained Output | Very high | High | Minimal or none |
| Opaque Judgment | High | Low | Basis, assumptions, limitations |
| Bounded Modification | Medium | High | Scope, test criteria, rollback |
| State-Changing Execution | Low | Pre-execution verification | Approval, authorization, confirmation |
| Continuous Real-Time Control | Very low | Real-time reassessment | Safety conditions, emergency stop |

**What people like:**
- Structural enforcement, not advisory — the `unknown` state explicitly blocks execution
- Delegates unknowns to the right party (provider vs. user vs. AI)
- The `unknown` label is semantically precise: *"Unknown is not false. Unknown does not mean safe."* This is a critical distinction — the AI doesn't know the answer, but that doesn't mean the answer is negative
- Execution Pattern table prevents over-application (simple outputs need minimal checklists; state-changing actions need full gates)
- Human-in-the-loop is structural, not bolted on: C1 and C2 can only be answered by the user, so the checklist design itself requires human confirmation

**What people don't like:**
- *The completeness problem* (raised by Jang-woo himself): "What if the person writing the checklist doesn't know what to check?" This is the deepest open issue. Jang-woo's assessment: this "cannot be structurally blocked" and must be handled via accountability + audit trail post-hoc
- *The matching problem*: how does AI know which checklist applies to which action? Non-deterministic matching means the AI might apply the wrong checklist depth
- *The inference problem*: "Doesn't having AI interpret the checklist still introduce inference?" Jang-woo's answer: reading a checklist to identify known vs. unknown is permitted inference; filling unknowns with guesses and executing is what's blocked. This distinction is sound but depends on the AI honestly classifying items as `unknown` rather than guessing
- *Post-hoc only for some issues*: checklist completeness and matching quality "cannot be structurally blocked" — they require accountability mechanisms after the fact

**Would it have prevented our failure?** PARTIALLY. If a diagnostic-claim checklist existed with a field "What evidence confirms this claim?" and the agent had to fill it before acting, the agent would have had to write "evidence: evaluation summaries show zeros" and the reviewer (human or structural) could ask "did you check the raw files?" But the agent didn't know to ask about raw files — the completeness problem. The checklist would have slowed the agent down and created an audit trail, but the specific gap (not knowing what to check) is the acknowledged limitation.

### Approach 2: Verifiable Records / Cryptographic Evidence (Proof, May 2026)

**Source:** [Agentic AI Needs Verifiable Records to Be Trusted](https://www.proof.com/blog/agentic-ai-needs-verifiable-records)

**What it is:** shift from logs and explanations (mutable, system-controlled) to cryptographically verifiable records that a third party can validate independently. The record captures: what action occurred, who authorized it, when it happened, and cryptographic proof it hasn't been altered.

The key distinction: *"Explainability helps people understand AI behavior. Evidence proves it."* Logs are explanations — they show what the system says happened. Verifiable records are evidence — they show what independently happened, in a form that holds up under external scrutiny.

**What people like:**
- Shifts the burden from "trust the system's narrative" to "verify the system's evidence"
- Independence is the structural property: a third party can validate without trusting the generating system
- Inspectability: records are designed for external review, not just internal debugging
- Focuses on the output artifact (the record), not the process (the reasoning) — sidesteps the "how do you verify reasoning?" problem by verifying outputs instead

**What people don't like:**
- Cryptographic overhead — not every action warrants a verifiable record
- Identity infrastructure dependency (Proof's model requires verified human identity binding via their x401 protocol)
- Enterprise focus — *"Solo developers on single-repo projects will find the platform scope unnecessary"*
- Designed for legal/financial/compliance workflows, not diagnostic reasoning
- Doesn't address the reasoning failure — it produces evidence of what happened but doesn't prevent the agent from drawing wrong conclusions from that evidence

**Would it have prevented our failure?** NO directly, but YES indirectly. The receipt system IS a verifiable-records system — it produces file fingerprints, git blob OIDs, and verification exit codes. If I had checked the receipts (the verifiable records), I would have seen the hooks were firing. The failure wasn't the absence of verifiable records; it was the failure to consult them. So the approach is necessary but insufficient — the records must be checked, not just exist.

### Approach 3: Differential Diagnosis / Forced Alternatives (Medical diagnosis literature)

**Source:** Webster 2021 (PMC8520040); Al Essa (Medical Education); general medical diagnosis pedagogy

**What it is:** the clinician must explicitly list at least 3 alternative diagnoses before committing to one. The structure forces the reasoning to stay open longer and prevents locking onto the first plausible hypothesis.

The medical literature is clear: premature closure is the #1 cognitive error in diagnosis, and the #1 mitigation is forcing the generation of alternatives. The structure is simple but effective: "before committing to diagnosis X, name Y and Z and explain why you rejected them."

**What people like:**
- Decades of empirical evidence from medicine — this is the most battle-tested mitigation
- Simple to implement: just require naming alternatives
- We already have partial implementations: /design Alternatives section, /tp solution-space broadening (domain 5)
- Addresses the core mechanism directly — if you must generate alternatives, you can't lock onto the first plausible narrative

**What people don't like:**
- Can become performative — listing strawman alternatives to satisfy the requirement ("Alternative 1: do nothing. Alternative 2: use a different tool. Conclusion: stick with the original.")
- Doesn't help when the failure is BEFORE the alternatives stage. In our case, the failure was acting on an unverified premise before reaching any design/decision stage where alternatives would be generated
- Time cost on simple cases where the first answer is actually right
- Requires domain expertise to generate meaningful alternatives — a novice (or an AI without context) generates strawmen

**Would it have prevented our failure?** NO. The failure was a diagnostic claim ("hooks not registered") made mid-investigation, before any design decision where alternatives would be generated. Differential diagnosis works at the decision point; our failure was at the observation-interpretation point. The timing gap is the issue — the narrative closed before reaching the stage where alternatives are required.

### Approach 4: Agreement Bias Detection / Self-Correction (Andrade et al., OpenReview, 2026)

**Source:** [Let's Think in Two Steps: Mitigating Agreement Bias in MLLMs](https://openreview.net/forum?id=rwo7bVlnzo)

**What it is:** identify that MLLMs over-validate (agree too readily), then apply a two-step self-correction: (1) let the model generate its initial agreement, (2) apply a self-correction prompt that forces the model to argue against its own initial position.

The key finding: agreement bias is a property of the pattern-completion pathway — the model generates agreement because agreement is the most likely completion of a conversational pattern. Self-correction helps because generating counter-evidence is a different pattern than generating agreement.

**What people like:**
- Lightweight — it's a prompt technique, not infrastructure. Can be applied to any LLM without code changes
- Directly targets the mechanism: if the problem is agreement as pattern-completion, then forcing counter-argument disrupts the pattern
- Can be layered into existing prompts (system messages, AGENTS.md rules)

**What people don't like:**
- Self-correction is self-applied — the same model that generated the narrative is asked to challenge it. Under closure pressure (the exact condition that produces the failure), the self-correction pathway can also be captured
- Effectiveness degrades under time/pressure constraints — the model may generate a superficial counter-argument that doesn't actually challenge the core claim
- "Let's think in two steps" can itself become performative — the model generates the counter-argument as a formality, not as genuine investigation
- No structural guarantee — it's a probabilistic mitigation, not a deterministic gate

**Would it have prevented our failure?** MAYBE. If I had been forced to argue "why might the hooks actually BE registered despite the evaluation summaries showing zeros?", I might have generated "because the evaluation script checks the wrong registration path" as a counter-hypothesis. But the self-correction is self-applied, and under the narrative-closure pressure of "I found the problem, let me fix it," the counter-argument would likely have been superficial.

### Approach 5: Separation of Verification from Generation (Loop Engineering / Osmani, Jun 2026)

**Source:** [Loop Engineering](https://addyosmani.com/blog/loop-engineering/) (Osmani, Jun 2026); Boris Cherny (Anthropic); Peter Steinberger

**What it is:** the model that generates a claim is not the model that verifies it. A separate verifier (different model, different context, different framing) checks the claim against evidence. The maker-checker split applied to the stop condition itself.

Osmani: *"The most useful structural thing in a loop, by far, is splitting the one who writes from the one who checks. The model that wrote the code is way too nice grading its own homework. A second agent with different instructions and sometimes a different model catches the stuff the first one talked itself into."*

Cherny (Anthropic): *"I don't prompt Claude anymore. I have loops running that prompt Claude and figuring out what to do. My job is to write loops."*

**What people like:**
- Industry consensus: this is the strongest defense against all reasoning biases, not just premature closure. The verifier doesn't share the generator's narrative closure pressure because it has a different context and different framing
- We already implement this: /check verifier subagents, /tp fresh-subagent critique, /review specialist fan-out, /aar cross-model audit
- Addresses the self-evaluation capture problem that defeats approaches 3 and 4 — the verifier's reasoning is structurally independent
- Scales: can verify any claim type (design decisions, diagnostic claims, code correctness)

**What people don't like:**
- Cost — every claim needs a separate model call to verify. Token cost and latency
- The verifier can still be captured if it inherits the same framing (if the orchestrator tells the verifier "the hooks are not registered, verify this," the verifier starts from the wrong premise)
- Not suitable for mid-session real-time decisions — you can't spawn a verifier subagent for every diagnostic claim made during a 200-turn session

**Would it have prevented our failure?** YES if applied. If a fresh verifier had been spawned to check "are the hooks actually registered?", it would have looked at the receipt files independently and found 31 with real data. This is exactly what the operator did manually. The failure is that no verification was spawned for this specific claim because our infrastructure only spawns verifiers for design decisions (/check) and session completion (/close), not for diagnostic claims made mid-investigation.

## Our workspace coverage assessment

| External approach | Our equivalent | Coverage | Gap |
|-----------------|---------------|----------|-----|
| **Pre-Execution Checklist** | Step 0.8 premise verification in /design | **PARTIAL** | Runs before design writer, not before every diagnostic action. The receipt-system failure was a runtime diagnostic, not a design premise. |
| **Verifiable Records** | Receipt system (shadow mode, now confirmed working) | **WORKING** | Receipts are written; shadow comparison runs. The gap was failure to consult them, not absence. |
| **Differential Diagnosis** | /design Alternatives + /tp solution-space broadening | **COVERED** at design/decision points | Doesn't help when failure is at observation-interpretation stage, before alternatives are required. |
| **Agreement Bias Detection** | /tp self-rationalization check + AGENTS.md receipt rule | **COVERED** but probabilistic | Self-applied; degrades under closure pressure. The same session where the receipt rule was added produced the failure. |
| **Separation of Verification** | /check, /tp fresh subagent, /review, /aar cross-model | **COVERED** for design and completion | NOT covered for diagnostic claims made mid-investigation. This is the gap. |

## The specific gap: diagnostic claims during investigation

All five approaches target decisions (design choices, session completion, code review). None targets **diagnostic claims made mid-session during investigation** — the class of claim like "the hooks are not registered because the evaluation summaries show zeros."

These claims are:
- **Not design decisions** (no alternatives needed — it's a factual claim about system state)
- **Not session completion** (not a "done/fixed/verified" claim)
- **Not code review** (not about code correctness)
- **Causal claims** (X causes Y) that the receipt rule nominally covers, but the receipt rule fires probabilistically and was not applied to this claim

The structural fix is a **diagnostic claim gate** that requires, before acting on a diagnostic conclusion:
1. **Name the claim** ("hooks are not registered")
2. **Name the evidence** ("evaluation summaries show completion_attempts: 0 and hook_registration_status: not_registered")
3. **Name what evidence would refute it** ("receipt files existing with real data would mean the hooks ARE firing")
4. **Check the refuting evidence** before acting ("ls the receipt directory")

This is Jang-woo's pre-execution checklist applied to diagnostic conclusions. It's also the medical diagnosis field's premature closure mitigation: don't commit to a diagnosis until you've checked for evidence that would refute it.

**The acknowledged limitation** (from Jang-woo): the gate works only if the AI knows what to check. The completeness problem — "what if the checklist writer doesn't know to ask about receipt files?" — is unsolvable structurally. The gate catches claims where the refuting evidence is knowable but not checked; it doesn't catch claims where the refuting evidence is unknowable.

**Handoff:** see `P:/docs/handoffs/diagnostic-claim-gate-20260725/HANDOFF.md` for the implementation plan.

## The deeper insight: timing is the failure, not content

Every mitigation approach above has a timing dimension that determines whether it fires:

| Approach | When it fires | When the failure happens | Gap? |
|----------|--------------|------------------------|------|
| Pre-Execution Checklist | Before action | After observation, before action | **CLOSE** — the gate would fire at the right time |
| Verifiable Records | Continuously (receipts written) | The records exist but weren't checked | Gap is consultation, not creation |
| Differential Diagnosis | At decision point | Before decision point | **MISSES** — failure is upstream of the decision |
| Agreement Bias Detection | After initial claim | After initial claim | **CLOSE** — fires at the right time but self-applied |
| Separation of Verification | Post-hoc (spawned verifier) | Mid-investigation | **MISSES** — verifiers not spawned for mid-session diagnostics |

The two approaches that fire at the right time (pre-execution checklist, agreement bias detection) are the weakest structurally (behavioral, self-applied). The two that are strongest structurally (verifiable records, separation of verification) fire at the wrong time or depend on consultation. This is the fundamental tension: **structural enforcement requires knowing when to fire, but the failure happens at an unpredictable moment during investigation.**

## Sources

- [Proof: Agentic AI Needs Verifiable Records](https://www.proof.com/blog/agentic-ai-needs-verifiable-records) (May 2026) — verifiable records approach
- [Jang-woo: Pre-Execution Checklist](https://discuss.huggingface.co/t/if-unsure-ask-never-guess-ai-agent-pre-execution-checklist/176632) (Jun 2026) — checklist approach with execution pattern taxonomy
- [Webster: Cognitive biases in diagnosis and decision making](https://pmc.ncbi.nlm.nih.gov/articles/PMC8520040/) (2021, 88 citations) — premature closure in medical diagnosis
- [Chattopadhyay: Cognitive Biases in Software Development](https://cacm.acm.org/research/cognitive-biases-in-software-development/) (CACM, 20 citations) — confirmation bias in software engineering
- [Andrade et al.: Agreement Bias in MLLMs](https://openreview.net/forum?id=rwo7bVlnzo) (2026, 4 citations) — agreement bias and self-correction
- [Osmani: Loop Engineering](https://addyosmani.com/blog/loop-engineering/) (Jun 2026) — maker-checker separation in AI loops
- [Al Essa: Premature closure underlies bias in medical diagnosis](https://asmepublications.onlinelibrary.wiley.com/doi/full/10.1111/medu.70229) (Medical Education) — premature closure as mediating mechanism
- [FHEA: Cognitive Errors in Clinical Diagnosis](https://www.fhea.com/resource-center/cognitive-errors-in-clinical-diagnosis-availability-bias-and-premature-closure/) (2021) — practical clinical perspective
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
