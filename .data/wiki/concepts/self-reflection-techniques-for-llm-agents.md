---
title: "Self-reflection techniques for LLM agents: metacognitive prompting, skill distillation, and self-improvement architectures"
created: 2026-08-11
source: session-2026-08-11 /www research (motivated by /todo and /tp self-reflection implementation)
tags: [self-reflection, metacognition, self-improvement, reflexion, self-refine, hermes, skill-distillation, agent-architecture, research]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  Self-reflection in LLM agents spans five architectural layers: (1) prompt-based
  metacognitive prompting (understand → answer → reflect → justify → self-grade),
  (2) memory-augmented reflection loops (Reflexion, Self-Refine), (3) skill
  distillation from episodic memory (Hermes Agent), (4) hierarchical meta-agent
  coordination (ReMA, task agent + meta agent), and (5) model-level self-improvement
  via RL/DPO trajectories (Atropos pipeline). The key insight for our workspace:
  we already have the components (two-lens critique, self-reflection steps in
  /todo and /tp, compaction summaries, cross-skill propagation) — the missing
  piece is the FEEDBACK LOOP that makes reflection persistent (stored, retrieved,
  applied next time) rather than ephemeral (computed, displayed, forgotten).
sources:
  - "https://arxiv.org/abs/2506.05109" (ICML 2025 position: intrinsic metacognitive capabilities)
  - "https://aclanthology.org/2026.acl-long.1329/" (MARS: Metacognitive Agent Reflective Self-improvement)
  - "https://www.emergentmind.com/topics/metacognitive-capabilities-in-llms" (comprehensive survey of metacognitive techniques)
  - "https://hermes-agent.ai/features/learning-loop" (Hermes Agent learning loop architecture)
  - "https://github.com/NousResearch/hermes-agent-self-evolution" (DSPy + GEPA evolutionary self-improvement)
  - "https://arxiv.org/html/2607.28576" (Sample More Reflect Less — self-refine loses to repeated sampling at equal token cost)
  - "https://github.com/XMUDeepLIT/Awesome-Self-Evolving-Agents" (curated repo of self-evolving agent frameworks)
  - "https://selfimproving-agent.github.io/" (survey of self-improvement in agentic systems)
  - "https://arxiv.org/html/2607.11881" (Metacognition in LLMs: foundations, progress, opportunities)
  - "https://www.nature.com/articles/s44387-025-00045-3" (dual-loop reflection: extrospection + introspection)
  - "https://aclanthology.org/2026.acl-long.1636/" (Echo Trap: credit assignment failure in multi-turn self-reflection)
relations:
  - target: wiki/concepts/specification-gaming-in-llm-agent-pipelines.md
    type: extends — self-reflection is the behavioral layer; specification gaming is what happens when it's absent
  - target: wiki/concepts/adaptive-orchestration-task-shape-classification.md
    type: extends — adaptive orchestration uses metacognitive monitoring to route ceremony
  - target: wiki/concepts/making-llm-agents-honestly-execute-skills-solution-stack.md
    type: companion — the solution stack makes fabrication impossible; self-reflection makes the agent WANT to find gaps
---

# Self-reflection techniques for LLM agents

## Decision context

**The problem:** we added self-reflection steps to `/todo` (Step 1c) and `/tp` (Step 3.5) that force the agent to ask "what am I missing?" before delivering output. These steps are behavioral — they fire every run but they're ephemeral. The agent computes its reflection, adds a line to the output, and moves on. Next session, the same miss class might recur because the reflection wasn't stored or retrieved.

**The question this research answered:** what techniques exist for making LLM agent self-reflection persistent, structural, and self-improving? What are Hermes, MARS, and the broader field doing? How do we make our self-reflection steps compound rather than repeat?

## Key findings

### 1. Five architectural layers of self-reflection

**[HIGH confidence — multiple converging sources]**

| Layer | What it does | Example | Our workspace equivalent |
|---|---|---|---|
| **1. Prompt-based metacognition** | Multi-stage prompts: understand → answer → reflect → justify → self-grade | Wang et al. 2023 five-stage protocol | Our `/tp` core domains + "could you be wrong?" (Hills 2026) |
| **2. Memory-augmented loops** | Attempt → reflect → store reflection → retry with reflection injected | Reflexion (Shinn 2023), Self-Refine (Madaan 2023) | Our compaction segments + wiki pattern library |
| **3. Skill distillation** | Observe repeated patterns → distill into reusable skill → refine from feedback | Hermes Agent learning loop | Our SKILL.md skills + `/skill-dev` |
| **4. Hierarchical meta-agents** | Task agent (execution) + meta agent (strategic oversight, planning) | ReMA (Wan 2025), HyperAgents (Meta) | Our `/tp` two-lens (fresh subagent = meta agent) |
| **5. Model-level improvement** | Rate responses → train via RL/DPO → improve base model | Atropos pipeline (Hermes) | [NOT IMPLEMENTED — requires fine-tuning infrastructure] |

**Key insight:** our workspace implements layers 1-4 through different skills (`/tp`, `/todo`, `/skill-dev`, `/wiki`). Layer 5 (model fine-tuning) is out of scope for a prompt-based fleet. The gap is between layers 2 and 3 — our reflections are computed but not distilled into persistent, retrieved skills.

### 2. MARS: principle-based + procedural reflection

**[HIGH confidence — ACL 2026 paper]**

MARS (Metacognitive Agent with Reflective Self-improvement, ACL 2026) splits reflection into two types:
- **Principle-based reflection:** "what should I AVOID?" (failure patterns, anti-patterns)
- **Procedural reflection:** "what should I DO?" (success patterns, best practices)

**This maps directly to our workspace:**
- Principle-based = our AGENTS.md hard rules (learned from past failures)
- Procedural = our SKILL.md files (captured best practices)

The MARS contribution: it generates BOTH types in a single reflection pass and stores them separately. Our wiki captures procedural knowledge well but principle-based knowledge (failure patterns) is scattered across concepts with inconsistent naming.

### 3. Hermes Agent: the observe → distill → reuse → refine loop

**[HIGH confidence — NousResearch documentation + GitHub]**

Hermes Agent (NousResearch) implements a learning loop:
1. **Observe:** tracks multi-step tasks in episodic memory (tool calls, decisions, corrections)
2. **Distill:** after 3+ successful completions of a similar pattern, generates a SKILL.md capturing the procedure + pitfalls + verification steps
3. **Reuse:** skill available as slash command with progressive disclosure
4. **Refine:** agent patches its own skills mid-session when it discovers a better approach

**Critical design choice:** Hermes does NOT rewrite its own code. It builds and improves skills — "that's what makes the improvement safe and inspectable." This mirrors our design principle: skills are the unit of improvement, not the orchestrator.

**Hermes Self-Evolution (separate repo):** uses DSPy + GEPA for evolutionary optimization of prompts, skills, and code. This is layer 5 — automated prompt optimization. Different from the learning loop (which is layer 3 — skill distillation).

### 4. The "Sample More, Reflect Less" challenge

**[HIGH confidence — arXiv 2607.28576]**

A 2025 paper shows Self-Refine and Reflexion lose to repeated sampling at equal token cost (from 1.5B to 7B models). At the same token budget, generating N independent samples and picking the best outperforms reflecting on and refining a single sample.

**Implication for our workspace:** our `/tp` two-lens critique is a form of reflection. The paper suggests that for tasks where correctness is verifiable, running 3 independent critiques and taking the consensus (which we do via the parallel lens panel) is more effective than refining a single critique. This validates our 3-lens parallel design but challenges the "refine the synthesis" step.

**Counter-evidence:** the paper's finding applies to tasks where correctness IS verifiable (code, math). For tasks where correctness is NOT verifiable (design decisions, prioritization), reflection adds value because the external signal (sample quality) doesn't exist. Our `/tp` operates primarily on non-verifiable tasks — so reflection remains valuable for our use case.

### 5. The Echo Trap: credit assignment failure in multi-turn reflection

**[HIGH confidence — ACL 2026]**

"Escaping the Echo Trap" (ACL 2026) identifies a failure mode in multi-turn self-reflection: the agent assigns credit for improvements to its own reflection, when the improvement actually came from external feedback or task structure. This creates a "reflection theater" where the agent thinks its self-reflection is working when it's actually not.

**This maps to our `/tp` self-reflection step (Step 3.5):** the step asks "what am I missing?" but if the agent consistently reports "no gaps found," it may be because the external checks (scanner sources, /tp two-lens) are doing the work, not the self-reflection itself.

**Mitigation:** the self-reflection output should distinguish between gaps the agent found vs. gaps the external checks found. Our current implementation doesn't do this — it asks one question ("what am I missing?") without separating internal discovery from external surfacing.

### 6. What repos and practitioners are doing

**[HIGH confidence — multiple GitHub repos]**

| Framework | Self-improvement approach | Relevance to us |
|---|---|---|
| **Hermes Agent** (NousResearch) | Learning loop + skill distillation + Atropos RL | Most directly comparable — our skills + `/skill-dev` |
| **EvoAgentX** | Memory modules for cross-interaction reflection | Our wiki + handoffs |
| **HyperAgents** (Meta) | Self-referential agents that modify own code | [OUT OF SCOPE — we don't modify orchestrator code in-session] |
| **Darwin Gödel Machine** | Evolutionary self-improvement (modify own code, test, keep if better) | Interesting but too risky for shared multi-agent host |
| **AgentEvolver** (modelscope) | Multi-agent evolution framework | Research reference |
| **LangGraph Reflection** | Write → critique → iterate until score threshold | Our `/review` → fix loop in ship-py |

### 7. Prime Router and routing-based self-improvement

**[MEDIUM confidence — search results show model routing, not self-improvement routing]**

"Prime Router" appears to be a model routing framework (route prompts to the best model), not a self-improvement system. The self-improvement angle in routing is: the router LEARNS which model handles which task type best over time. This is relevant to our `pick_model.py` + model-quota skill — we could add a learning layer that tracks which models succeed on which task types and adjusts routing accordingly.

**EvoRoute** (arXiv 2601.02695) is the most relevant: an "experience-driven self-routing" system where the agent's own experience (which models worked, which failed) feeds back into routing decisions. This is a form of layer-2 self-reflection applied to model selection.

## What this means for our workspace specifically

### The gap: reflections are ephemeral, not distilled

Our self-reflection steps (Step 1c in `/todo`, Step 3.5 in `/tp`) compute gaps at output time but don't store them. Next session, the same miss class might recur. The fix is a **reflection ledger** — a persistent store of identified gaps that future reflection steps query before computing.

**Concrete design:**
1. When Step 1c or Step 3.5 identifies a gap, write it to `~/.grok/state/reflection-ledger.jsonl`
2. Before next run's Step 1c/3.5, read the ledger and check: "did I miss this class last time too?"
3. When a gap is systematically addressed (a scanner source is added, a rule is written), mark it resolved

This converts ephemeral reflection into layer-2 (memory-augmented) reflection.

### The technique map: which existing techniques apply where

| Our technique | Self-reflection use | Current implementation |
|---|---|---|
| **Pre-mortem** (/tp core domain 3a) | "What will go wrong?" — ask BEFORE acting | Fires conditionally (horizon≠now) |
| **Steelman** (/tp core domain 4a) | "What's the strongest version of the opposing view?" | Fires conditionally |
| **Second-order effects** (/tp core domain 2a) | "What happens after the first-order effect?" | Fires conditionally |
| **de Bono lateral thinking** (/tp explore directive 11) | "What lateral connection am I not seeing?" | Fires in explore mode |
| **TRIZ contradictions** (/tp explore directive 10) | "What apparent tradeoff can be dissolved?" | Fires in explore mode |
| **"Could you be wrong?"** (Hills 2026, in AGENTS.md) | "What specific evidence would disconfirm this?" | Mandatory per AGENTS.md |
| **Self-Ask decomposition** (/www Phase 1.5) | "What sub-topics am I not covering?" | Fires in /www |

**The missing technique: Reflexion-style feedback storage.** None of our techniques store the reflection for future retrieval. Reflexion's key innovation was the MEMORY step — the reflection is written to an episodic memory and injected on the next attempt. We have compaction segments (which store session history) but no structured reflection memory that the NEXT session's self-reflection step queries.

### The Hermes-inspired improvement: observe → distill → reuse → refine for skills

Hermes creates skills after 3+ successful completions of a similar pattern. We could implement a similar trigger in `/skill-dev`:

1. **Observe:** when a task pattern recurs across sessions (detected via AAR or handoff analysis), log it
2. **Distill:** after 3+ instances, propose a new skill or skill refinement
3. **Reuse:** the skill is immediately available
4. **Refine:** `/skill-dev measure` identifies defects; fix them

This is the `/dream` skill's territory — it already reads handoffs and AARs to find cross-session patterns. The missing piece is the **automatic proposal** when a pattern crosses the 3-instance threshold.

## Falsifier

This analysis is wrong if:
- Self-reflection consistently provides no signal beyond what the scanner/sources already provide (the Echo Trap)
- The overhead of a reflection ledger exceeds the value of stored reflections
- The field moves to model-level self-improvement (layer 5) and prompt-based self-reflection becomes obsolete

## Receipts

- **Reflexion (Shinn et al., 2023):** verbal self-reflection as reinforcement signal, episodic memory. HumanEval 80% → 91% on GPT-4.
- **Self-Refine (Madaan et al., 2023):** single LLM as generator + critic + refiner. 20% absolute improvement across 7 tasks.
- **MARS (ACL 2026):** principle-based + procedural reflection. Single-pass cycle: error diagnosis → failure clustering → synthesis.
- **Hermes learning loop:** observe → distill (3+ attempts) → reuse → refine. Skills in ~/.hermes/skills/.
- **Sample More Reflect Less (arXiv 2607.28576):** self-refine loses to repeated sampling at equal token cost (1.5B to 7B).
- **Echo Trap (ACL 2026):** credit assignment failure in multi-turn self-reflection.
- **ReMA (Wan et al., 2025):** hierarchical meta-agent coordination (task agent + meta agent) via MARL.
- **Intrinsic metacognition position (ICML 2025):** self-assessment + learning strategy selection + evaluation of learning effectiveness.
- **Metacognitive prompting (Wang et al., 2023):** five-stage protocol (understand → answer → reflect → justify → self-grade).
- **Dual-loop reflection (Nature 2025):** extrospection (external feedback) + introspection (self-assessment).

## Sources

- [Truly Self-Improving Agents Require Intrinsic Metacognitive Capabilities](https://arxiv.org/abs/2506.05109) (ICML 2025 position paper)
- [Learn Like Humans: MARS](https://aclanthology.org/2026.acl-long.1329/) (ACL 2026)
- [Metacognitive Capabilities in LLMs](https://www.emergentmind.com/topics/metacognitive-capabilities-in-llms) (EmergentMind survey)
- [Hermes Agent Learning Loop](https://hermes-agent.ai/features/learning-loop) (NousResearch)
- [Hermes Agent Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution) (DSPy + GEPA)
- [Sample More, Reflect Less](https://arxiv.org/html/2607.28576) (self-refine vs repeated sampling)
- [Awesome Self-Evolving Agents](https://github.com/XMUDeepLIT/Awesome-Self-Evolving-Agents) (curated repo)
- [Self-Improvements in Modern Agentic Systems](https://selfimproving-agent.github.io/) (survey hub)
- [Metacognition in LLMs: Foundations](https://arxiv.org/html/2607.11881) (comprehensive review)
- [Escaping the Echo Trap](https://aclanthology.org/2026.acl-long.1636/) (credit assignment failure)
- [EvoRoute: Experience-Driven Self-Routing](https://arxiv.org/html/2601.02695) (routing + self-improvement)
- [Self-Reflection Enhances LLMs](https://www.nature.com/articles/s44387-025-00045-3) (Nature, dual-loop reflection)
