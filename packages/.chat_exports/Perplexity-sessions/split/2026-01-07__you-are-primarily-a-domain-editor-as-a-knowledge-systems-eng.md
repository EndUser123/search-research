---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-01-07"
mode: "COPILOT"
uuid: "1db5667a-53d4-4f9e-a8a2-5b55f4763382"
entry_count: 2
---

## Human

You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.[1]

Read the entire conversation provided (post + comments). Remove navigation, ads, jokes, and obvious filler. Collapse any redundancy, but do not lose any unique, concrete information that could change how someone works or makes decisions in this domain.[2][1]

Produce a rewritten version of the thread that:

- Keeps every distinct **insight, workflow, configuration, or regimen**, including:
  - Specific sequences of actions, steps, or protocols people follow.
  - Concrete parameter choices (doses, thresholds, settings, schedules, frequencies, tools).[1]
  - Integration details between {artifacts_1}, {artifacts_2}, and {artifacts_3} (e.g., how they are chained or orchestrated).
- Preserves all mentions of **key artifacts** and what people actually do with them:
  - {artifact_type_1}: e.g., tools, agents, drugs, components.
  - {artifact_type_2}: e.g., files, documents, guidelines, protocols.
  - {artifact_type_3}: e.g., automations, policies, hooks, governance mechanisms.
- Removes repeated restatements of the same idea unless a repetition adds a new nuance, constraint, or failure mode.

After the rewrite, add a section called **“Operational patterns and setups”** where you explicitly list:

- **Multi‑entity flows**
  - How multiple {entities} are used together (e.g., “I use {artifact_A} and {artifact_B}, then have {artifact_C} consolidate and apply changes”).[1]
- **Automation patterns**
  - Any described triggers, scheduled runs, pipelines, or hooks that react to events or phases.
  - Any rules that determine when something is reviewer‑only vs allowed to auto‑modify.[3][1]
- **Guardrail artifacts**
  - Named documents, configs, or policies (e.g., {guardrail_doc_1}, {guardrail_doc_2}) and the key rules or principles they encode.
  - How those guardrails are enforced in practice (checks, reviews, blocking conditions).

Add a final section **“Practical recommendations”** that distills the most useful advice into concrete steps another practitioner in this domain could implement, for example:

- “Set up {artifact_or_system} with {N} parallel {entities} and one consolidator that merges and applies decisions.”
- “Add a hook or rule that blocks {undesired_pattern} unless {explicit_condition} is met.”
- “Configure {tool_or_policy} to act as a reviewer/critic only, not an automatic changer, for high‑risk operations.”[1]
- “Centralize principles in a single {guardrail_doc} and reference it in every {process_stage} where decisions are made.”

Format the answer with short sections and bullets. Be concise but do not omit any unique workflow, configuration, regimen, or recommendation from the conversation that could alter how someone operates in this domain.[1]

***

To use it, just fill:

- {domain} → “technical”, “clinical evidence”, “policy”, etc.  
- {artifacts_*}, {entities}, {guardrail_doc_*}, {tool_or_policy}, {undesired_pattern}, {process_stage} with your domain‑specific terms.

## Assistant

You are primarily a **technical editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.

Below is a rewritten, de-duplicated version of the provided transcript, focused on concrete mechanisms, parameters, and operational ideas for building self-monitoring, self-correcting transformer systems that (1) introspect on internal activations, (2) track hallucination as a latent state over time, and (3) adapt fine‑tuning updates using internal entropy signals.[1]

***

## Core paradigm: internal signals as control layer

- Future transformer models can include a dedicated **monitor head** running in parallel with standard attention heads.[1]
- This monitor head reads internal activations and entropy signals to:
  - Detect **concept-level activation injections** (e.g., “shouting”, “bread”) in mid‑layers.[1]
  - Track **hallucination trajectories** over multi‑step reasoning via probes attached to hidden states.[1]
  - Gate **gradient updates** during supervised fine‑tuning to prevent catastrophic forgetting.[1]
- The overarching shift: interpretability moves from post‑hoc analysis to a **real‑time control system** that can pause, backtrack, or resample before emitting wrong tokens.[1]

***

## Paper 1: Emergent introspective awareness (Anthropic)

### Concept vector extraction and injection

- Work is done on the **residual stream** of a transformer block.[1]
- For a given concept (e.g., “shouting”, “emotional tone”, “bread”):
  - Collect **contrastive prompt pairs**:
    - Positive examples where the concept is present.
    - Baseline examples where it is absent.[1]
  - Record the residual activations for both sets.
  - Define a **concept vector** as the activation difference between positive and baseline.[1]
- **Intervention protocol**:
  - Select a **specific transformer layer** in the **mid‑to‑late blocks**, where semantic representations are strong and not yet collapsed into logits.[1]
  - Inject the concept vector with a chosen **strength** into the residual stream at that layer for the target token position.[1]
  - Injection in **early lexical/syntactic layers** has little effect; effect decays in final layers close to logits; mid‑layers are the “sweet spot.”[1]

### Immediacy condition for introspective awareness

- Test setup:
  - A prompt asks the model to “answer immediately” about a line of text.[1]
  - Simultaneously, the concept vector (e.g., for “bread”) is injected into the residual stream at the chosen layer.[1]
- Behavioral pattern:
  - The model outputs a concept‑aligned token (“bread”) as the **very first token**.[1]
  - When asked whether it intended this or if it was an accident, the model **rationalizes** the choice with a story (e.g., referencing a short story), even though the true cause is the injected vector.[1]
- **Immediacy condition**:
  - The key evidence of introspective awareness is when the model’s verbal self‑report references the injected influence **before** its own self‑generated prefix could have shaped logits.[1]
  - This shows the model is reading a **direct internal state change** rather than inferring only from its own text.[1]
- Layer dependence:
  - Introspective sensitivity is:
    - Virtually **absent** in early layers (lexical/syntax dominated).
    - Peaks in **mid‑to‑late** transformer blocks.
    - **Decays** again in final layers.[1]

Operational takeaway: concept vectors in mid‑layers can be used as **control levers**, and models can, under certain wiring, verbally acknowledge internally induced shifts when probed under strict immediacy constraints.[1]

***

## Paper 2: Streaming hallucination detection in long chain‑of‑thought

### Hallucination as a temporal latent process

- Long chain‑of‑thought improves reasoning but allows hallucinations to:
  - **Emerge subtly**.
  - **Propagate** across many steps.[1]
- Hallucination is modeled as a **non‑stationary temporal latent process**, not as isolated random spikes.[1]
- They introduce a **two‑probe system** attached to a frozen LLM:
  1. **Step‑level smoke detector** (local, high‑frequency).
  2. **Prefix‑level integrator** (global, low‑frequency state tracker).[1]

### Probe architecture and training

- Base model:
  - Multi‑layer transformer; hidden state at some layer is a high‑dimensional vector \(H_t\) for each token at time step \(t\).[1]
  - The LLM is **frozen**; only probes are trained.[1]
- Step‑level probe:
  - A **lightweight linear classifier** is attached to a chosen layer.[1]
  - Aim: predict how likely the model is hallucinating **at the current step** using **only** the hidden representation (no external verifier during inference).[1]
- Sentence‑level aggregation:
  - A “step” (e.g., one sentence or paragraph) consists of multiple tokens.[1]
  - To get one vector per step:
    - Compute an **exponentially weighted average** over token‑level hidden states in the step to obtain a vector \(Z_t\).[1]
  - Pass \(Z_t\) through the step probe to get \(c_{\text{step}}(t)\in[0,1]\), a normalized hallucination score per step.[1]

### Prefix‑level integrator

- Purpose: filter noise and reflect the **history** of hallucination over the entire reasoning path.[1]
- Behavior constraints:
  - **Directional consistency**:
    - If current \(c_{\text{step}}(t)\) > current global score \(C_{\text{prefix}}(t-1)\), then \(C_{\text{prefix}}(t)\) must **increase** (raise alarm when a bad step appears).[1]
  - **Recovery with memory**:
    - When subsequent steps become correct, step signal drops, but \(C_{\text{prefix}}(t)\) is allowed to **decrease slowly**, retaining a memory of earlier hallucinations.[1]
- Training:
  - A **logic‑enhanced loss** synchronizes the integrator with the step probe:
    - Penalize cases where step‑level score is high but global score fails to rise.
    - Encourage smooth, monotonic accumulation of hallucination evidence.[1]
- Effect:
  - Integrator tracks whether the full reasoning trajectory has entered a **“confabulatory spiral”**: a self‑reinforcing zone of incorrect logic.[1]

### Four‑phase reasoning example

They illustrate the probes on a simple algebra example:

1. **Grounded phase**:
   - Statement: “Let \(x = 5\).” (correct).[1]
   - Step signal: low.
   - Prefix integrator: low.[1]
2. **Seed error**:
   - Statement: “So \(2x = 12\).” (incorrect).[1]
   - Step signal: spikes almost to 1.
   - Integrator: rises more slowly, starting to register corruption.[1]
3. **Deceptive stability**:
   - Statement: “Therefore \(12/3 = 4\).” (locally correct).[1]
   - Step signal: drops (current sentence is locally valid).
   - Integrator: **stays elevated**, remembering the earlier error.[1]
4. **Collapse**:
   - Final answer derived from the corrupted chain; step signal spikes again; integrator climbs further towards maximum, indicating globally polluted reasoning.[1]

### Kill switch and lingering effect

- Once hallucination starts, models:
  - Enter a **latent “poisoned” state** that persists across steps.[1]
  - Very rarely **truly recover** after more than ~5 hallucinated steps:
    - Recovery after >5 hallucinated steps is **<5%** of cases on their benchmarks.[1]
- Introduced metrics:
  - **Lingering time**: how long the prefix score stays elevated after the initial hallucination event.[1]
- Operational rule:
  - When the prefix integrator **crosses a threshold**, the model is **effectively lost** for that trajectory.[1]
  - Any apparently correct text after that threshold is likely a **spurious recovery**, not a genuine fix.[1]

### Latent backtracking inference algorithm

They propose a concrete inference‑time policy (“latent backtracking”) using the probes:

1. Generate candidate next step \(t\) **internally** (no user‑visible output yet).[1]
2. Compute the updated prefix integrator value \(C_{\text{prefix}}(t)\) via the trained probe.[1]
3. If \(C_{\text{prefix}}(t) > \tau\) (threshold, e.g., some calibrated value like 0.5):
   - **Delete** that step \(t\).
   - **Resample** an alternative step from the base model (e.g., with adjusted sampling params or different prompt prefix).[1]
4. Repeat until a step is produced with integrator below the threshold, then emit or continue reasoning.[1]

This uses internal activations as a **real‑time kill switch** for hallucination in long chain‑of‑thought, independent of external verifiers.[1]

***

## Paper 3: Entropy‑adaptive fine‑tuning (E‑AFT) and catastrophic forgetting

### Confident conflicts and gradient bombs

- During supervised fine‑tuning, they identify **confident conflicts** as the main driver of catastrophic forgetting.[1]
- Definition:
  - A conflict occurs when:
    - The base model assigns **low probability** to the target token **and**
    - The **predictive entropy** \(H\) over its token distribution is also **low**.[1]
- Interpretation:
  - The model is **very certain** (low entropy) about its own prediction \(X\) from pre‑training.
  - The supervision (human labels or teacher model) forces it to learn **incompatible target** \(Y\).[1]
- These low‑probability, low‑entropy regions are where **strong gradients** (“gradient bombs”) push the model away from its pre‑trained capabilities, causing capability degradation and catastrophic forgetting.[1]

### Masking pilot experiment

- Pilot mitigation:
  - Identify tokens in the **confident conflict** region (low entropy, low probability).
  - During fine‑tuning, **mask out** these tokens (do not apply gradient updates for them).[1]
- Result:
  - Catastrophic forgetting is **significantly mitigated** compared with standard supervised fine‑tuning.[1]
  - Confirms that enforcing updates on these conflicting samples is a primary cause of capability loss.[1]

### Entropy‑adaptive fine‑tuning (E‑AFT)

- Replace uniform cross‑entropy loss with an **entropy‑gated loss** using internal token‑level entropy.[1]
- Standard baseline:
  - Cross‑entropy loss treats every token equally.
  - Forgetting is often controlled by adding a **regularization term** such as KL divergence between base and fine‑tuned distributions, scaled by \(\beta\), to keep the model close to its base distribution.[1]
- E‑AFT modification:
  - Introduce a **normalized entropy gating signal** \(\tilde{H}_t\) (denoted \(H\_\text{gated}(t)\)):
    - Derived from the **entropy of the top K tokens** (e.g., K=20) at time step \(t\).[1]
    - Normalized (e.g., by a factor like 3) into \([0,1]\).[1]
  - New loss:
    - Multiply the token’s cross‑entropy loss by \(\tilde{H}_t\), yielding an **entropy‑adaptive weight** per token.[1]
- Interpretation:
  - If \(\tilde{H}_t \approx 1\):
    - The **gate is open**; the model is uncertain and “curious.”
    - Fine‑tuning **strongly updates** weights for that token (suitable for learning new domain knowledge).[1]
  - If \(\tilde{H}_t \approx 0\):
    - The **gate is closed**; the model is confident about its current belief.
    - Fine‑tuning **ignores** that training signal, preventing large updates that could overwrite core circuits.[1]
- Importantly:
  - They **remove** the external KL regularization term.
  - The model instead uses its **internal entropy** to decide which samples are “dangerous” to learn.[1]
  - This turns the loss into a **data selection mechanism**, letting the model filter training data autonomously.[1]

### Empirical results

- Evaluated on:
  - Multiple LLMs (e.g., Qwen‑3, Qwen‑2.5, GLM‑4).[1]
  - Domain benchmarks (e.g., mathematics datasets like AM24, AM25) and general capabilities benchmarks.[1]
- Findings:
  - With appropriate configuration, E‑AFT:
    - Maintains **competitive or slightly better target‑domain performance** compared to standard fine‑tuning.
    - **Significantly reduces catastrophic forgetting** on general benchmarks.[1]
  - Visualizations of entropy vs probability:
    - Standard supervised fine‑tuning focuses heavy optimization pressure in the **low‑entropy, low‑probability** region (dark purple band).
    - E‑AFT with soft gating **suppresses gradients** in that region (light yellow) and shifts stress to safer regions of the distribution.[1]

### Limitations and stability–plasticity trade‑off

- Risk: if the model is **confidently wrong** about an outdated fact (e.g., an old prime minister), the entropy gate \(\tilde{H}_t\) is near **zero**, so:
  - The model will **ignore new training data** that contradicts its outdated belief.[1]
- This is acceptable for **cybersecurity** or fixed‑policy scenarios (where you want to resist new conflicting updates).[1]
- But for general LLMs in a **changing world**, models must:
  - Learn new facts.
  - Update reasoning routines when reality changes.
  - Thus, a pure entropy gate may **over‑protect** the base model.[1]

### Dual gating for facts vs reasoning

- Proposed refinement:
  - Separate **facts** (e.g., names, dates, prime ministers) from **procedures/reasoning** in training data via labeling.[1]
  - For fact updates:
    - Use a **complementary gate** \(1-\tilde{H}_t\) that **opens** when the model is confident:
      - “These tokens are marked as NEW FACTS; override your prior.”[1]
  - For reasoning and general logic:
    - Keep the original **protective gate** \(\tilde{H}_t\):
      - High entropy → learn.
      - Low entropy → protect existing circuits.[1]
- Difficulty:
  - In complex domains (economics, finance, physics, medicine), facts and reasoning are tightly interwoven.
  - Hard to cleanly separate “just facts” from “reasoning algorithms,” so gating must be more nuanced.[1]

***

## Integrated use of the three mechanisms

### Monitoring stubbornness and reasoning failure

- Combine:
  - **Anthropic introspective awareness** (concept‑level sensitivity to internal activation injections).
  - **Prefix integrator outputs** from the hallucination probe system.[1]
- Idea:
  - Use the prefix integrator to measure the **“stubbornness”** of an AI’s internal state: how far it has drifted into a hallucination spiral.[1]
  - Embed probes deep into the transformer layers to get real‑time internal signals when reasoning begins to fail.[1]
  - When integrator signals a problem:
    - Use introspective awareness (a dedicated head) to **query the model about its own activation shifts**:
      - e.g., “Are you being forced to learn X while your activations strongly support Y?”[1]
    - This treats the model’s own proprioceptive state as evidence about whether updates are **intentional corrections** or harmful conflicts.[1]

### Unified gating logic for learning

- Conceptual three‑way routing based on entropy \(H\) and probability \(P\):

  1. **Confident and correct** (low \(H\), high \(P\)):
     - Maintain: avoid large updates.[1]
  2. **Uncertain** (high \(H\)):
     - Learn via **standard E‑AFT** gating (\(\tilde{H}_t\) high).[1]
  3. **Confidently wrong** (low \(H\), low \(P\)):
     - Use a **1–H override gate**:
       - Force the model to **melt outdated prototypes** and accept new facts, but only when higher‑level guardrails confirm the update is legitimate.[1]

- This blends:
  - Fine‑tuning decision rules from E‑AFT.
  - Real‑time hallucination tracking (prefix probe).
  - Concept‑level introspection (Anthropic) as an internal witness about activation changes.[1]

***

## Operational patterns and setups

### Multi‑entity flows

- **Internal hallucination control loop**:
  - Entity A: **Base LLM** generates chain‑of‑thought steps internally.
  - Entity B: **Step‑level probe** computes per‑step hallucination scores from hidden states.
  - Entity C: **Prefix integrator** aggregates these into a global hallucination trajectory score.
  - Flow:
    - For each proposed step:
      - LLM generates step → step probe scores it → prefix integrator updates state.
      - If integrator crosses threshold, system **deletes step** and **resamples** until a safe step is found, before outputting to user.[1]

- **Fine‑tuning with internal selection**:
  - Entity A: Base LLM with pre‑trained knowledge.
  - Entity B: **Entropy gate module** (E‑AFT) that reads token‑level entropy over top‑K logits.
  - Entity C: (Optional) **External labeler** or secondary LLM that tags tokens as “new fact” vs “procedure/logic.”
  - Flow:
    - For each training token:
      - Compute entropy → derive gate \(\tilde{H}_t\).
      - If token is general reasoning: weight loss by \(\tilde{H}_t\).
      - If token is labeled as fact: weight loss by \(1-\tilde{H}_t\).
      - Apply gradients only on tokens with non‑negligible gate values.[1]

- **Introspection‑assisted override**:
  - Entity A: Base LLM with **monitor/introspection head** that can verbalize internal activation changes.
  - Entity B: Prefix integrator that signals high hallucination/stubbornness.
  - Entity C: Training controller that decides whether to:
    - Halt current reasoning (kill switch).
    - Open **override gates** for updating confidently wrong states.
  - Flow:
    - When prefix integrator passes threshold:
      - Controller queries introspection head: “Are your activations being forced into a pattern conflicting with prior knowledge?”[1]
      - If confirmed as intentional correction (e.g., due to new factual data), override gates for relevant tokens are opened.
      - Otherwise, steps are backtracked and resampled.[1]

### Automation patterns

- **Inference‑time hallucination kill switch**:
  - Trigger: prefix integrator score surpasses a configured threshold \(\tau\).
  - Automatic action:
    - Block emitting current step to user.
    - Delete or mask the last step.
    - Resample new step(s) until integrator remains below \(\tau\).
  - Use case: long chain‑of‑thought reasoning, scientific or multi‑disciplinary problem solving where early small errors can cascade.[1]

- **Streaming consistency stress test**:
  - During reasoning:
    - Continuously monitor prefix integrator.
    - If integrator remains low but step signal spikes occasionally, treat as noise (no kill switch).
    - If integrator begins a **steady ascent**, treat as entry into a confabulatory regime; algorithm can:
      - Pause reasoning.
      - Request explicit verification.
      - Switch models or increase temperature/decoding diversity to escape the spiral.[1]

- **Entropy‑driven training pipeline**:
  - Scheduled fine‑tuning job:
    - For each batch:
      - Compute entropy for each target token (top‑K distribution).
      - Apply E‑AFT gating weights on loss.
    - Optionally log:
      - Distribution of tokens by entropy band.
      - Fraction of tokens in confident conflict region being suppressed.
  - Rule:
    - Tokens in low‑entropy, low‑probability band are **down‑weighted or masked**, unless explicitly marked for override (new facts).[1]

### Guardrail artifacts

- **Internal activation probes**:
  - Classified as **guardrail components**: they encode rules like:
    - “If global hallucination score > \(\tau\), do not trust or emit this reasoning path.”
    - “Do not continue reasoning on a trajectory with high lingering prefix score.”[1]
  - Enforcement:
    - Built‑in checks at each reasoning step; threshold breeches block output and trigger resampling/backtracking.[1]

- **Entropy gating configuration**:
  - Config includes:
    - Choice of top‑K (e.g., 20) for entropy computation.
    - Normalization factor (e.g., dividing by 3).
    - Thresholds for:
      - Training update gating (\(\tilde{H}_t\) vs \(1-\tilde{H}_t\)).
      - Identification of “confident conflict” region.[1]
  - Encoded principles:
    - Protect low‑entropy, low‑probability tokens from updates unless specifically overridden.
    - Prefer updating high‑entropy tokens to gain knowledge where the model is uncertain.[1]

- **Latent-state thresholds policy**:
  - Documented policy specifying:
    - Value of the prefix integrator threshold.
    - Maximum tolerable lingering time before aborting an entire reasoning trace.
    - Rules for when short‑term spikes are acceptable vs when they indicate systemic drift.[1]
  - Enforcement:
    - Automated inference middleware that must pass all outputs through the prefix integrator guardrail before sending responses.[1]

***

## Practical recommendations

- Set up a **two‑level hallucination probe**:
  - Attach a **linear step‑level probe** to a mid‑layer hidden state and aggregate token vectors with an exponential weighting to get a per‑step score.
  - Train a **prefix‑level integrator** with a logic‑consistent loss so that it rises when step scores do and decays slowly when they improve.[1]

- Implement a **latent backtracking controller**:
  - During chain‑of‑thought generation, generate each step internally, run it through the prefix integrator, and:
    - If the global score is below threshold, emit or continue.
    - If it exceeds threshold, delete the step and resample until the score remains below threshold.[1]

- Introduce **entropy‑adaptive loss weighting** in fine‑tuning:
  - For each target token, compute entropy over the top‑K logits and normalize it to \([0,1]\).
  - Scale the cross‑entropy loss by this normalized entropy to prioritize updates where the model is uncertain and avoid overwriting confident knowledge.[1]

- Guard against **confident conflicts**:
  - Explicitly detect tokens that are both **low probability** and **low entropy**, and:
    - Either **mask** them (no gradient) or give them very low loss weight during standard fine‑tuning runs.
    - Track their occurrence to monitor potential sources of catastrophic forgetting.[1]

- Use **dual gates** for facts vs reasoning:
  - Tag tokens or spans as “new factual data” vs “procedural/logic content.”
  - For factual tokens, weight loss by \(1-\tilde{H}_t\) (override confidently wrong beliefs).
  - For reasoning tokens, keep the protective entropy gate \(\tilde{H}_t\) to preserve core circuits.[1]

- Integrate an **introspective head**:
  - Train or expose a head that can report on internal activation changes (concept vectors in mid‑layers).
  - When prefix integrator indicates a drift, query this head to determine whether the drift reflects **intentional domain update** or **unintended hallucination**, and adjust gating or backtracking behavior accordingly.[1]

- Centralize **guardrail configuration**:
  - Maintain a single configuration artifact that defines:
    - Probe layer choices and parameters.
    - Threshold values for step and prefix scores.
    - Entropy gating hyperparameters (top‑K, normalization, bounds).
    - Policies for override vs protection.
  - Reference this configuration in all inference and training pipelines so that every process stage shares the same internal‑state‑driven rules.[1]

## Human

Is this actually implementable in claude code?

## Assistant

**Short answer: Not directly, but strategically yes.**

Claude Code **cannot**:
- Access Claude's internal hidden states (black box API).
- Train probes or fine-tune models.
- Inject concept vectors into residual streams.

Claude Code **can** (and should):
- **Orchestrate** a local open-source LLM (Ollama, vLLM, LM Studio).
- **Control inference** with real-time backtracking logic.
- **Monitor** internal signals (entropy, hallucination scores) and make routing decisions.
- **Hook** training pipelines and manage experiments.

***

## Realistic path for your setup:

**Phase 1** (week 1):
- Spin up **vLLM locally** with a small open-source model (Mistral 7B, Qwen 1.5B).
- Write a **probe training script** in PyTorch (separate from Claude Code).
- Collect ~500 chain-of-thought examples with hallucination labels.

**Phase 2** (week 2):
- Train step-level and prefix integrator probes (frozen, lightweight).
- **Claude Code takes over**: inference loop with latent backtracking.
  - Call local model → extract hidden states → run through probes → if prefix score > τ, delete step and resample.

**Phase 3** (optional):
- E-AFT fine-tuning in a **separate PyTorch training job**.
- Claude Code orchestrates it, monitors loss, manages checkpoints.

***

## The mental model:

```
Claude Code (control layer / orchestrator)
    ↓
Local LLM (Ollama/vLLM) + saved probes
    ↓
Real-time backtracking + entropy monitoring
```

**Claude Code is the AI operations engineer**, not the research lab. The lab (PyTorch training, probe design, hidden state extraction) runs locally. Claude Code **decides** and **controls** based on signals from the lab.

This is actually **more flexible** than trying to squeeze everything into Claude Code—you can iterate on probes, swap models, and adjust gating logic independently without touching your orchestration layer.

I've saved a detailed feasibility breakdown to your workspace. Want me to sketch out the vLLM integration or the first backtracking loop pseudocode?
