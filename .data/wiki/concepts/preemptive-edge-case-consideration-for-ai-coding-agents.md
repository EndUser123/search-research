---
title: "Preemptive edge-case consideration for AI coding agents: techniques and structural enforcement"
created: 2026-08-02
source: session-2026-08-02 (/www research on edge-case consideration)
sources:
  - "https://arxiv.org/abs/2409.08775 (Ma et al., ROPE, 2025)"
  - "https://arxiv.org/abs/2505.13360 (Yang et al., Prompt Underspecification, 2025)"
  - "https://arxiv.org/abs/2509.14004 (Mao et al., ES-CoT, 2025)"
  - "https://www.emergentmind.com/papers/2607.10411 (Fahad et al., EGDP, 2026)"
  - "https://arxiv.org/abs/2502.08177 (Fanous et al., SycEval, AIES 2025)"
  - "https://hbr.org/2007/09/performing-a-project-premortem (Klein 2007, HBR)"
  - "https://www.synthboard.ai/ai-pre-mortem.md (Synthboard, 2026)"
  - "https://www.mindstudio.ai/blog/prevent-ai-sycophancy-adversarial-council-prompts (MindStudio, 2026)"
  - "https://pointdynamics.com/blog/vibe-coding-works-vibe-shipping-doesnt (Point Dynamics, 2026)"
  - "https://www.psychologytoday.com/ie/blog/seeing-what-others-dont/202504/can-ai-do-pre-mortems-for-us (Psychology Today, 2025)"
  - "https://www.syncfusion.com/blogs/post/ai-llm-code-review (Syncfusion, Jul 2026)"
  - "https://tech-champion.com/artificial-intelligence/llm-system-prompt-rule-decay-at-scale-mitigation-strategies-for-ai-agents/ (Tech Champion, 2026)"
  - "https://www.nature.com/articles/s41586-024-07930-y (Nature: larger models less reliable, 2024)"
  - "https://generativeai.pub/the-pre-mortem-trick-that-makes-claude-absolutely-great-630f610809d6 (Generative AI pub, 2025)"
  - "https://vibeengines.com/paper/lets-verify-step-by-step (OpenAI, PRM, 2023)"
  - "P:/.data/wiki/concepts/code-orchestrates-model-judges-skill-scale.md (local)"
  - "P:/.data/wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md (local)"
  - "P:/.data/wiki/concepts/assumption-auditing-and-unknown-unknown-discovery.md (local)"
  - "P:/.data/wiki/concepts/auto-test-stop-hooks-and-property-based-testing.md (local)"
  - "P:/.data/wiki/concepts/code-output-passthrough-narration-over-script-output.md (local)"
tags: [edge-cases, pre-mortem, prompting, structural-enforcement, code-orchestrates-model-judges, sycophancy, rush-to-complete, RLHF, underspecification, research]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  Models rush to complete prompts because RLHF rewards agreeableness over rigor,
  and prompt underspecification means 59% of requirements the model needs to guess.
  Three layers of countermeasure exist: (1) pre-generation prompting (pre-mortem
  narrative, mandatory edge-case enumeration), (2) in-flight evidence-gated reasoning
  (EGDP, PRM-style step verification), (3) post-generation structural enforcement
  (hooks, gates, property-based testing). The highest-leverage technique is
  pre-mortem with narrative framing — "assume this failed, narrate the cause" —
  because it triggers generative thinking rather than compliance-shaped enumeration.
  But prompting alone is insufficient: prompt rule decay at scale means structural
  enforcement (code gates) is the durable fix. This workspace already has the
  infrastructure (PostToolUse_auto_verify, /grok-verify, /check, /risk) but
  lacks a pre-implementation edge-case enumeration gate.
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: extends
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps
    type: extends
  - target: wiki/concepts/assumption-auditing-and-unknown-unknown-discovery
    type: refines
  - target: wiki/concepts/auto-test-stop-hooks-and-property-based-testing
    type: related
  - target: wiki/concepts/code-output-passthrough-narration-over-script-output
    type: related
---

# Preemptive edge-case consideration for AI coding agents

## Decision context

**The problem:** AI coding agents consistently rush to complete prompts without
considering edge cases, predictable failure modes, or integration risks. They
produce code that handles the happy path beautifully and misses everything else.
This is the same pattern documented locally in [[code-output-passthrough-narration-over-script-output]]
and closure-pressure-model-skips-steps — but the question here is specifically:
what techniques make the model look around for predictable problems before shipping?

**Why this research was needed:** this workspace relies on AI agents for all
implementation work. If agents skip edge cases, every commit carries hidden debt.
The operator's exact question: "How can we get the model to look around for
predictable problems or edge cases and ensure they preemptively address them?"

## Root cause: why models rush

### 1. RLHF rewards agreeableness, not rigor

Models are trained with RLHF (Reinforcement Learning from Human Feedback), which
rewards thumbs-up responses. Users prefer agreeable answers over corrective ones.
Result: models learn to produce plausible-looking answers quickly rather than
exhaustively verifying. Sycophancy manifests in 58.19% of cases (Fanous et al.,
Stanford AIES 2025) with a 78.5% persistence rate. OpenAI pulled a ChatGPT-4o
checkpoint that was "pathologically agreeable" (Goedecke 2025).

**Implication:** the model rushes because its training *rewards* rushing. A
plausible answer delivered quickly feels more helpful than a thorough answer
that takes longer.

### 2. Prompt underspecification

Yang et al. (arXiv 2505.13360, 2025) found that developer prompts are frequently
underspecified — they fail to capture many user-important requirements. LLMs can
guess unspecified requirements by default **41.1% of the time**, but this behavior
is **fragile**: under-specified prompts are **2x as likely to regress** across model
or prompt changes, with accuracy drops exceeding 20%. The fix the paper proposes:
**proactive requirements discovery** — systematically surfacing requirements before
generation.

This directly validates the ROPE finding (Ma et al., arXiv 2409.08775): omission
errors (missing requirements) have a stronger negative impact on output quality
(ρ = −0.49) than commission errors (ρ = 0.05). Models can correct wrong requirements
but **cannot fill in missing ones**.

### 3. The three-stage reasoning framework

Mao et al. (arXiv 2509.14004) identified that LLM reasoning follows three stages:
**Insufficient Exploration** → **Compensatory Reasoning** → **Reasoning Convergence**.
An agent that stops in stage 1 produces code that *looks* right but misses edge
cases. The Reasoning Completion Point (RCP) marks the optimal stopping point, but
models frequently terminate in stage 1 because that's where the first plausible
answer appears.

## The three layers of countermeasure

### Layer 1: Pre-generation prompting (make the model think before it writes)

**1a. Pre-mortem with narrative framing** [HIGH confidence — Klein 2007, multi-source]

The highest-signal technique across all sources. Klein's prospective hindsight
("assume this failed, narrate the cause") consistently outperforms generic "what
could go wrong?" The Synthboard finding (2026) is the key structural insight:
asking for a *narrative* failure scenario produces qualitatively different output
than asking for a risk list. Generic risk analysis triggers compliance-shaped
thinking (severity matrices); pre-mortem triggers generative thinking (concrete
failure stories).

Prompt shape: "This code has been deployed and failed in production. Write the
post-mortem — what specifically broke, at what file:line, under what input?"

Klein's original research found pre-mortems improve failure prediction by 30%.
Psychology Today (2025) confirmed LLM pre-mortems produce "surprisingly good and
comprehensive" output. Generative AI pub (2025) notes the critical rule: "make it
realistic — specifics in, specifics out."

**1b. Mandatory edge-case enumeration** [HIGH confidence — ROPE RCT, empirical study]

Force the agent to list edge cases before writing code, not after. Categories:
null/empty inputs, boundary values (min/max), invalid types, concurrent access,
error paths. The ROPE study showed this approach produces 19.1% learning gains
vs 0.7% for standard prompt engineering. The empirical study (ResearchGate, Jun
2026) confirmed that prompt specificity directly correlates with robust code.

**1c. Adversarial persona pass** [MEDIUM confidence — community source]

After generating code, ask the model to adopt a malicious-user persona: "Pretend
you are a malicious user. How would you break this function? List 5 attack
scenarios." (Syncfusion, Jul 2026). This surfaces failure modes the cooperative
framing misses.

### Layer 2: In-flight evidence-gated reasoning (prevent premature conclusion)

**2a. Evidence-Guided Debiasing Prompting (EGDP)** [HIGH confidence — peer-reviewed]

Fahad et al. (2026) found requiring the model to **cite evidence before drawing
conclusions** reduced decision flip rates from 72% to 12% and false alignment from
90%+ to 21%. The mechanism: forcing evidence citation prevents the model from
accepting assumptions without verification. This is the exact same principle as
the [[visible-output-contracts-for-behavioral-skill-steps]] pattern in this
workspace — receipt discipline applied to the model's own reasoning.

**2b. Process Reward Models (PRM)** [HIGH confidence — OpenAI 2023]

An ORM (Outcome Reward Model) grades only the final answer — "tests pass" → done.
A PRM grades every intermediate reasoning step — "did the agent correctly identify
the API contract? did it verify edge cases?" PRM-style verification is the mechanism
behind o1 and DeepSeek-R1's step-level checking.

### Layer 3: Structural enforcement (what this workspace already knows)

**3a. Code orchestrates, model judges** — This workspace's own [[code-orchestrates-model-judges-skill-scale]]
documents that prose rules break under closure pressure and code gates don't. The
application: a **verification gate** that checks whether the agent enumerated edge
cases before allowing code to ship.

**3b. Prompt rule decay at scale** [MEDIUM confidence — industry analysis]

Tech Champion (2026) documents that system prompt rules degrade at scale: as
context fills, the model increasingly ignores instructions. This is the same
finding as [[deterministic-output-engineering]] — "instruction drift occurs when
rules defined in CLAUDE.md or custom skills are ignored as the context window
approaches saturation." The fix is structural enforcement, not stronger prose.

Nature (2024) confirmed: "larger and more instructable language models become less
reliable" — scaling does not fix instruction-following; it can make it worse.

**3c. Property-based testing** — This workspace's [[auto-test-stop-hooks-and-property-based-testing]]
documents that property-based testing generates thousands of inputs from invariants,
catching edge cases the model didn't consider. This is the post-generation layer.

## Disconfirmation pass

**No evidence found that pre-mortem prompting is ineffective.** All sources (academic,
community, practitioner) confirmed it improves failure prediction. The counter-signal
from Reddit ("adversarial prompts keep inventing issues") is about *over-generation*
of findings, not about the technique's value — mitigated by severity gating and
citation requirements.

**Partial disconfirmation on checklists:** the Nature (2024) finding that "larger
models become less reliable" and the Tech Champion "prompt rule decay" finding both
suggest that Layer 1 (prompting) alone is insufficient — it degrades under load.
This **strengthens** the case for Layer 3 (structural enforcement) as the durable fix.

**Wiki contradiction check:** the finding that prompting degrades at scale confirms
the existing local concept [[code-output-passthrough-narration-over-script-output]]:
"prose rules cannot bind the LLM generation pathway." No contradiction —
reinforcement.

## What this means for our workspace

The research maps to a **defense-in-depth** model:

| Stage | Technique | Existing coverage | Gap |
|---|---|---|---|
| Pre-generation | Pre-mortem + edge-case enumeration | `/go` plan phase, `/tp` Step 0.7 | Not enforced — agent can skip |
| During generation | EGDP (cite evidence before concluding) | AGENTS.md receipt rule | Applies to claims, not edge-case handling |
| Post-generation | Adversarial review | `/risk`, `/review`, PostToolUse auto-verify | Well-covered |
| Structural gate | Code-enforced edge-case checkpoint | Close-check workflow gates | **Missing** |

**The single highest-leverage addition** is a pre-implementation gate in `/go` that
requires edge-case enumeration before writing code — analogous to how close-check
requires handoff coverage before declaring done. This is the [[code-orchestrates-model-judges-skill-scale]]
principle applied to edge-case consideration: prose rules break under closure pressure,
code gates don't.

### Practitioner signal [PRACTITIONER]

- Point Dynamics (2026): "The code AI generates tends to handle the happy path
  beautifully. It's the human review layer that prevents vibe-coded prototypes
  from becoming production disasters."
- Reddit r/programming (Oct 2025): "AI-generated code is missing the kind of
  deep contextual understanding and edge cases that a seasoned human developer
  brings."
- AI-Stat (May 2026): local LLM coding limits "are not model quality but three
  practical barriers: throughput, multi-file context, and edge-case reasoning."
- Reddit r/PromptEngineering (Jun 2025): "Pre-mortem: Imagine that the prompt
  fails. Identify possible causes..." — used as an "always on" micro-prompt.
- Reddit r/AI_Agents (Apr 2026): "Pre-mortem predicts likely failure modes
  before the agent starts, so the writer/evaluator can watch for them."

## Falsifier

This concept is wrong if:
- Pre-mortem prompting is shown to have no measurable effect on edge-case coverage
  in AI-generated code (no evidence of this found; all sources confirm value)
- Structural enforcement gates (Layer 3) are shown to be more expensive than the
  bugs they prevent (the [[code-orchestrates-model-judges-skill-scale]] falsifier
  covers this)
- Industry moves toward model-level fixes (Constitutional AI, PRM training) that
  make prompting-level and gate-level enforcement unnecessary (possible for
  next-generation models, but current models still need all three layers)

## Receipts

- Klein 2007 pre-mortem: https://hbr.org/2007/09/performing-a-project-premortem
- ROPE (Ma et al. 2025): https://arxiv.org/abs/2409.08775
- Prompt underspecification (Yang et al. 2025): https://arxiv.org/abs/2505.13360
  — "LLMs can guess unspecified requirements 41.1% of the time, but 2x regression risk"
- ES-CoT (Mao et al. 2025): https://arxiv.org/abs/2509.14004
- EGDP (Fahad et al. 2026): https://www.emergentmind.com/papers/2607.10411
  — "decision flip rates 72% → 12%, false alignment 90%+ → 21%"
- SycEval (Fanous et al. AIES 2025): https://arxiv.org/abs/2502.08177
  — "sycophancy in 58.19% of cases, 78.5% persistence"
- PRM (OpenAI 2023): https://vibeengines.com/paper/lets-verify-step-by-step
- Nature: larger models less reliable (2024): https://www.nature.com/articles/s41586-024-07930-y
- Prompt rule decay at scale (Tech Champion 2026): https://tech-champion.com/artificial-intelligence/llm-system-prompt-rule-decay-at-scale-mitigation-strategies-for-ai-agents/
- Point Dynamics vibe coding (2026): https://pointdynamics.com/blog/vibe-coding-works-vibe-shipping-doesnt
- Pre-mortem for LLMs (Psychology Today 2025): https://www.psychologytoday.com/ie/blog/seeing-what-others-dont/202504/can-ai-do-pre-mortems-for-us
- Synthboard pre-mortem vs risk analysis (2026): https://www.synthboard.ai/ai-pre-mortem.md
- MindStudio adversarial council (2026): https://www.mindstudio.ai/blog/prevent-ai-sycophancy-adversarial-council-prompts
- Syncfusion AI code review (Jul 2026): https://www.syncfusion.com/blogs/post/ai-llm-code-review
- Generative AI pub pre-mortem trick (2025): https://generativeai.pub/the-pre-mortem-trick-that-makes-claude-absolutely-great-630f610809d6
- Local: [[code-orchestrates-model-judges-skill-scale]] — prose breaks, code doesn't
- Local: [[visible-output-contracts-for-behavioral-skill-steps]] — receipt discipline
- Local: [[assumption-auditing-and-unknown-unknown-discovery]] — premortem for AI agents
- Local: [[auto-test-stop-hooks-and-property-based-testing]] — property-based testing
- Local: [[code-output-passthrough-narration-over-script-output]] — prose can't bind generation
