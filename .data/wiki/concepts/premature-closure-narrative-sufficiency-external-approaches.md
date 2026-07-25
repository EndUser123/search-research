---
title: "Premature closure and narrative sufficiency: external approaches to the LLM reasoning failure"
created: 2026-07-25
source: session-019f94c9-www-research
tags: [premature-closure, narrative-sufficiency, verification, llm-failure-modes, cognitive-bias, structural-fixes, external-research]
summary: >
  External research on how practitioners and researchers address the LLM failure
  pattern where a plausible narrative closes the reasoning loop before evidence
  verification. Five approaches from industry and academia, with what people like
  and don't like about each. Key finding: the medical diagnosis field has studied
  "premature closure" for decades and has the most mature mitigation literature;
  the AI agent field is rediscovering the same pattern with new terminology.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - https://www.proof.com/blog/agentic-ai-needs-verifiable-records (Proof, May 2026)
  - https://discuss.huggingface.co/t/if-unsure-ask-never-guess-ai-agent-pre-execution-checklist/176632 (Jang-woo, Jun 2026)
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC8520040/ (Webster 2021, cognitive biases in diagnosis)
  - https://cacm.acm.org/research/cognitive-biases-in-software-development/ (Chattopadhyay, CACM)
  - https://www.fhea.com/resource-center/cognitive-errors-in-clinical-diagnosis-availability-bias-and-premature-closure/ (FHEA, 2021)
  - https://openreview.net/forum?id=rwo7bVlnzo (Andrade et al., agreement bias in MLLMs)
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: extends
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: extends
---

# Premature closure and narrative sufficiency: external approaches

## Decision context

**Why this research was needed:** the operator asked how other people address the pattern where an LLM constructs a plausible narrative that closes the reasoning loop before evidence verification ("evaluation summaries say zeros → hooks must not be registered → I should wire them"). This is the same failure class documented in `reactive-pattern-matching-and-closure-pressure.md` and `plausible-narratives-substitute-for-verification.md`.

## The pattern has a name (three names, in fact)

The pattern we've been calling "narrative sufficiency" or "closure-pressure minimization" is well-studied in three fields:

| Field | Name | Key citation |
|-------|------|-------------|
| Medical diagnosis | **Premature closure** | Webster 2021 (PMC8520040, 88 citations); Al Essa (Medical Education) |
| Software engineering | **Confirmation bias** | Chattopadhyay (CACM, 20 citations); Mohan & Mache (thevaluable.dev) |
| AI agents | **Agreement bias / narrative sufficiency** | Andrade et al. (OpenReview, 4 citations); Proof (May 2026) |

**Premature closure in medicine** is defined as "arriving at a conclusion or diagnosis too early without considering all possibilities." The medical literature treats it as a cognitive bias — a hardwired mental shortcut that causes diagnostic errors. Mitigations include: forced consideration of alternatives, structured differential diagnosis, and time-delayed review.

**Confirmation bias in software engineering** is "subconsciously filtering information to favor our existing hypothesis." CACM (Chattopadhyay) found developers spend disproportionately more time on confirming evidence than disconfirming evidence. Colesoft notes: "confirmation bias causes us to see what we expect rather than what exists on the screen."

## Five external approaches (what people like and don't like)

### 1. Pre-Execution Checklist (Jang-woo, HuggingFace, Jun 2026)

**What it is:** a structured checklist that MUST be filled before any action executes. Three layers: Fixed (C1: when/case, C2: user intent, C3: provider action), Provider (execution precautions), User (custom rules). If any item is `unknown`, execution does not proceed.

**What people like:**
- Structural enforcement, not advisory — "If any unknown remains, do not proceed"
- Delegates unknowns to the right party (provider vs. user vs. AI)
- Execution Pattern table determines checklist depth by action type (self-contained output needs minimal; state-changing execution needs approval gates)
- The `unknown` label is explicit: "Unknown is not false. Unknown does not mean safe."

**What people don't like:**
- "Doesn't requiring AI to interpret the checklist still introduce inference?" (raised by readers, addressed by Jang-woo: reading a checklist to identify known vs. unknown is permitted inference; filling unknowns with guesses and executing is what's blocked)
- Completeness of the checklist-defining party is an open problem — "What if the person writing the checklist doesn't know what to check?"
- Non-determinism of matching — how does AI know which checklist applies to which action?
- Jang-woo's own assessment: these two issues "cannot be structurally blocked" and must be handled via accountability + audit trail

### 2. Verifiable Records / Cryptographic Evidence (Proof, May 2026)

**What it is:** instead of logs and explanations (which are mutable and system-controlled), produce cryptographically verifiable records that a third party can validate without trusting the system that generated them.

**What people like:**
- Shifts from "explainability" to "evidence" — "Explainability helps people understand AI behavior. Evidence proves it."
- Independence: records hold up outside the system that generated them
- Focuses on the output artifact (the record), not the process (the reasoning)

**What people don't like:**
- Cryptographic overhead — not every action warrants a verifiable record
- Identity infrastructure dependency (Proof's model requires verified human identity binding)
- Enterprise focus — "solo developers on single-repo projects will find the platform scope unnecessary"
- Overkill for most coding tasks; designed for legal/financial/compliance workflows

### 3. Differential Diagnosis / Forced Alternatives (Medical diagnosis literature)

**What it is:** the clinician must explicitly list at least 3 alternative diagnoses before committing to one. The structure forces the reasoning to stay open longer.

**What people like:**
- Proven in medicine — premature closure is the #1 cognitive error in diagnostic medicine
- Simple to implement: "before committing to diagnosis X, name Y and Z and explain why you rejected them"
- We already have this in /design (Alternatives section) and /tp (solution-space broadening)

**What people don't like:**
- Can become performative — listing strawman alternatives to satisfy the requirement
- Doesn't prevent the specific failure I made (I DID have alternatives in the design; the problem was acting on an unverified premise before reaching the alternatives stage)
- Time cost on simple cases

### 4. Agreement Bias Detection (Andrade et al., OpenReview, 2026)

**What it is:** MLLMs have a "strong tendency to over-validate agent behavior" — they agree with claims too readily. The paper proposes a two-step mitigation: (1) identify the bias, (2) apply a self-correction prompt that forces the model to argue against its initial agreement.

**What people like:**
- Directly addresses the "plausible narrative feels sufficient" mechanism — the self-correction forces the model to generate counter-evidence
- Lightweight — a prompt technique, not infrastructure

**What people don't like:**
- Self-correction is still self-applied — the same model generating the narrative is asked to challenge it
- Effectiveness degrades under closure pressure (the exact condition that produces the failure)
- "Let's think in two steps" can itself become performative

### 5. Separation of Verification from Generation (Loop engineering / Addy Osmani)

**What it is:** the model that generates the claim is not the model that verifies it. A separate verifier (different model, different context, different framing) checks the claim against evidence.

**What people like:**
- Addresses the self-evaluation capture problem directly — the verifier doesn't share the generator's narrative closure pressure
- Industry consensus: "the most useful structural thing in a loop, by far, is splitting the one who writes from the one who checks"
- We already implement this (/check verifiers, /tp fresh subagent, /review specialists)

**What people don't like:**
- Cost — every claim needs a separate model call to verify
- Latency — verification adds time to every decision
- The verifier can also be captured if it inherits the same framing

## What this means for our workspace

Our existing infrastructure already implements 4 of the 5 approaches:

| External approach | Our equivalent | Gap |
|-----------------|---------------|-----|
| Pre-Execution Checklist | Step 0.8 premise verification in /design | **PARTIAL** — runs before writer, but not before every action. The receipt-system failure this session would not have been caught by Step 0.8 because it's a runtime diagnostic, not a design premise. |
| Verifiable Records | Receipt system (shadow mode) | **WORKING** — receipts are being written; shadow comparison is running. The gap was my measurement error, not a system gap. |
| Differential Diagnosis | /design Alternatives + /tp solution-space broadening | **COVERED** — but doesn't help when the failure is before the alternatives stage |
| Agreement Bias Detection | /tp self-rationalization check | **COVERED** — but same self-application limitation |
| Separation of Verification | /check, /tp fresh subagent, /review | **COVERED** — the strongest defense; catches what self-application misses |

**The gap our infrastructure doesn't cover:** the failure I made was a **diagnostic error** (claiming "hooks not registered" from incomplete evidence), not a **design error**. Our verification infrastructure targets design decisions and session completion, not diagnostic claims made mid-session during investigation. The receipt rule exists in AGENTS.md but is advisory — it fires probabilistically, not deterministically.

**The structural fix that would have caught it:** a "diagnostic claim gate" that requires: (1) naming the claim, (2) naming the evidence that supports it, (3) naming what evidence would refute it, BEFORE acting on the claim. This is Jang-woo's pre-execution checklist applied to diagnostic conclusions, not just user-requested actions. It's also the medical diagnosis field's "premature closure" mitigation applied to AI reasoning.

But — as Jang-woo acknowledges — this gate cannot be structurally enforced for the "completeness of the checklist-defining party" problem. The gate works only if the AI knows what to check. In my case, the thing to check was "are receipt files actually being written?" — a question I didn't think to ask because the narrative closed before it formed.

## Sources

- [Proof: Agentic AI Needs Verifiable Records](https://www.proof.com/blog/agentic-ai-needs-verifiable-records) (May 2026)
- [Jang-woo: Pre-Execution Checklist](https://discuss.huggingface.co/t/if-unsure-ask-never-guess-ai-agent-pre-execution-checklist/176632) (Jun 2026)
- [Webster: Cognitive biases in diagnosis and decision making](https://pmc.ncbi.nlm.nih.gov/articles/PMC8520040/) (2021, 88 citations)
- [Chattopadhyay: Cognitive Biases in Software Development](https://cacm.acm.org/research/cognitive-biases-in-software-development/) (CACM)
- [Andrade et al.: Agreement Bias in MLLMs](https://openreview.net/forum?id=rwo7bVlnzo) (2026)
- [Addy Osmani: Loop Engineering](https://addyosmani.com/blog/loop-engineering/) (Jun 2026)
