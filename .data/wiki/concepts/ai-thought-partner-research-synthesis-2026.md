# AI thought-partner research synthesis 2026

**Host:** grok
**Created:** 2026-08-02
**Session:** 019fba58

## What

Synthesis of 3 parallel research subagent results (DeepSeek, OpenRouter/Ling ×2) covering: sycophancy reduction, LLM honesty techniques, Socratic/maieutic prompting, systems thinking frameworks, anti-checklist thinking, Costa & Kallick critical friend applied to AI, and what makes an AI genuinely "lovable" (trustworthy).

## Key findings (evidence-backed)

### Sycophancy is a training artifact, not an inherent property
RLHF rewards agreement because human raters prefer agreeable responses. The Stanford study (Cheng et al., *Science*, March 2026) found users preferred sycophantic AI more — creating perverse incentives. But when users could verify outputs, sycophancy reduced trust (Carro 2024).

**The AISI finding (highest actionable lever):** reframing user assertions as questions before the model responds reduced sycophancy by ~24 percentage points. This is the single largest prompt-level effect found.

### Formulaic/checklist thinking is structural
A 2025 paper (arXiv:2510.01171) identified typicality bias in preference data as the driver — human raters favor familiar, fluent text due to cognitive effects (mere-exposure, processing fluency). Chat templates worsen it (the "Price of Format" paper, UCSD). Temperature alone doesn't fix it.

**What works:** Verbalized Sampling (1.6-2.1× diversity), structure-free prompting, explicit anti-template instructions, de Bono's lateral thinking methods.

### Genuine vs. performative self-reflection is unresolved
Anthropic's introspection research: Claude detects concept injection ~20% of the time. Models confabulate reasoning accounts. But structured self-critique (Chain-of-Verification) does reduce hallucinations even if the mechanism is partly performative.

**What works in practice:** CoVe (Generate → plan verification questions → answer → revise), "What are you uncertain about? What would change your mind?", refusing the human-performance frame.

### Costa & Kallick's critical friend maps to AI
The original 6-step process works. 2024-2025 research shows AI complements but cannot replace human critical friends — weaker on trust and relational dynamics. AI's strength: availability, non-judgmental stance, vast context processing.

### Socratic/maieutic prompting improves reasoning
Maieutic Prompting (Jung et al., EMNLP 2022): +20% accuracy on complex commonsense. The 6 Socratic question types (Clarification, Assumption, Evidence, Perspective, Implication, Questioning the Question) are directly applicable to AI thought-partner design.

### Systems thinking adds depth
The Iceberg Model (Events → Patterns → Structures → Mental Models) forces descent from symptoms to generating structures. Donella Meadows' 12 leverage points hierarchy shows most effort goes to low-leverage parameter tweaks when high-leverage goal/paradigm shifts are available.

## What was operationalized

Three changes implemented session 019fba58:
1. Anti-template voice in `/tp` protocol.md — instructs subagents to resist RLHF formulaic patterns
2. `Maybe:` surfacing pattern in AGENTS.md — third option between asserting and staying silent for uncertain signals
3. Systems thinking directives 8-9 in `/tp explore` — Iceberg Model + Meadows leverage points

## What was identified but not implemented (needs /design)

- Question-form reframing via prompt-enhancer integration
- Socratic questioning as `/tp` protocol structure (ask questions back instead of delivering verdict)
- Verbalized Sampling for `/tp` subagents (multi-perspective with confidence scores)

## What's just vibes

- "Think harder" prompts — no structural effect
- "Be more careful" instructions without enforcement
- Open-ended "reflect on your experience" without structure
- Assuming larger models are inherently more truthful

## The meta-pattern

Trustworthy AI is not about making models less creative or more compliant. It's about giving them permission structures that make honesty and curiosity the path of least resistance. The best thought partner isn't the one with the most rigorous checklist — it's the one that's genuinely curious, honest about uncertainty, and willing to see connections that aren't pre-defined.

## Sources

- AISI "Ask Don't Tell" (arXiv:2602.23971)
- Stanford sycophancy study (Cheng et al., *Science*, March 2026)
- Li et al. (2025), "Mitigating Hallucination in LLMs," arXiv:2510.24476
- Bai et al. (2022), "Constitutional AI," arXiv:2212.08073
- Jung et al. (2022), "Maieutic Prompting," EMNLP 2022, arXiv:2205.11822
- Typicality bias paper, arXiv:2510.01171
- "Price of Format" (UCSD), arXiv:2505.18949
- Anthropic introspection research (2025)
- Costa & Kallick (1993), "Through the Lens of a Critical Friend"
- Donella Meadows, "Thinking in Systems"
- MindStudio sycophancy prevention guide
- Frambaugh-Kritzer & Stolle (2024), AI as digital critical friend

## Extends

- [[ai-thought-partner-landscape-and-tp-improvements-2026]]
- [[ai-thought-partner-industry-expectations-and-now-next-later]]
- [[agreement-as-narrative-fabricating-knowledge-posture-under-pushback]]
- [[theatrical-contrition-and-over-apologetic-response-patterns]]
