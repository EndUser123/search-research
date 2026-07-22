---
title: "Multi-agent review: attack correlated errors, not persona diversity"
created: 2026-07-19
source: session-2026-07-19
tags: [multi-agent, review, council, red-team, llm-as-judge, ensemble, diversity, falsifier]
summary: >
  The theoretical justification for multi-agent review (council, red-team, tournament
  prompting) is uncorrelated errors across agents. Most implementations get persona
  diversity but not error-uncorrelation, so N=3 barely beats N=1. The actual levers are
  frame-diversity on inputs, falsifier-gating on outputs, and (for hard-to-reverse
  decisions) one orthogonal-model critic. LLM-as-judge margins under ~3 points are noise.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
evidence_gaps:
  - "The 'one-point margins are noise' threshold (~3 pts) is from prior knowledge of LLM-as-judge bias studies, not measured against this host's judge rubrics."
  - "No local A/B test comparing frame-diverse vs persona-diverse candidates on this stack."
  - "cc-council's agents/*.md persona files (planner, futurist, pragmatist, critic, judge, synthesizer) exist but are NOT referenced by ARCHITECTURE.md's documented Stage 2 flow (which runs 3 models on the same prompt). Either they're aspirational/legacy, or wired in engine.py (not traced this session)."
---

## Summary

The reason to run multiple agents on one task is **uncorrelated errors**: if N agents each independently catch 70% of flaws, their union catches ~97%; if their errors are correlated, N=3 catches barely more than N=1. Most council/red-team implementations pay 3× tokens for persona diversity (strategist/skeptic/operator) — which is **weak diversity**, because all members still inherit the same brief and the same model family's blind spots. The levers that actually decorrelate errors are frame mutations on the input side, falsifier-gating on the output side, and cross-family critique for irreversible decisions.

## Key Findings

### The tournament / "compete mode" pattern is real but mostly reproduces best-of-N

Triggered by a YouTube video framing "Anthropic engineers' tournament prompting" as a new trick. The pattern (N isolated candidates + blind judge + synthesis) is decades-old in ML/IR (best-of-N sampling, RLAIF judging, ensemble methods). It works for **subjective** tasks (copy, design, architecture tradeoffs). The video's evidence was thin:
- N=1 demo, evaluator not blinded to which page "won."
- Judge is a model scoring its own siblings (length preference, self-preference, position bias).
- Tournament got a post-judging revision cycle the control didn't — confounds "tournament helps" with "two passes beat one pass."
- Provenance loose ("Angela Jen, head of product" — no such person; lead-gen for a paid community).

**Implication:** don't build a `compete-mode` skill. The pattern is one paragraph of prompt, not a skill. `cc-council`, `/red-team`, `/go`, `grok-parallel` already cover it.

### Persona diversity is weak; frame diversity is strong

Persona labels (strategist/skeptic/operator) change *voice*, not *attention*. All members still anchor to the same brief. Strong diversity = **mutate the brief itself**:
- Member 1: brief verbatim.
- Member 2: deliberate steelman ("argue this is the strongest possible version before critiquing").
- Member 3: reframed brief exposing different assumptions ("assume adversarial deployment environment" or "assume cost estimate is 5× stated").

Frame mutations change what each agent attends to. Persona mutations don't. This is the highest-ROI intervention and it costs ~0 tokens.

### Falsifier-gating converts vibe-critique into testable claims

Every objection must ship with a falsifier:
> "I'd withdraw this objection if you showed X."

Objections without falsifiers get downweighted or dropped at synthesis. This:
- Forces specificity ("design feels generic" → "uses default Tailwind palette; withdraw if custom palette in CSS").
- Makes synthesis tractable (reconcile falsifiable claims against evidence, not prose against prose).
- Surfaces the 80% of critique that's aesthetic preference dressed as analysis.

### LLM-as-judge margins under ~3 points are noise

Same-family judges scoring same-family candidates produce correlated scores within the judge's bias band. The tournament video's 91/93/92 verdict is **consistent with pure noise**, not signal. Don't treat sub-3-point spreads as a meaningful ranking. Either widen the rubric (so scores actually separate) or treat near-ties as "no signal — synthesize instead of picking."

### Orthogonal-model critic is the only true error-decorrelation

Same-family critics agree on *what kind* of issue matters. A cross-family critic (Gemini via `agy`, perplexity-backed synthesis, codex) will flag different categories — different token boundaries, safety training, length/structure preferences. The `/red-team` skill already gestures at this: `adversarial (external-LLM harness divergence … PENDING: runner unbuilt, see #872/#873/#874)`. Funding that ticket is the structurally correct fix. Use cross-family critique when the decision is hard to reverse; skip it for reversible work.

### Skill-specific mappings — VERIFIED 2026-07-19

Read this session: `cc-council/ARCHITECTURE.md`, `cc-council/README.md`, all 6 `cc-council/agents/*.md`, `red-team/commands/red-team.md`.

**cc-council already implements cross-model diversity (the stronger pattern).** ARCHITECTURE.md §Stage 2: "3 models generate independent responses" — diversity comes from different model families (glm-5.2, m3, kimi-k2.7 via cc-skills-ai-api transport), not from persona prompts. The 6 persona files in `agents/` are not referenced by the documented engine flow (evidence gap: may be wired in `engine.py` but untraced). This means **Pattern B (orthogonal-model critic) is already the default for cc-council** — it's not a recommendation, it's an existing capability. The actual remaining gaps for cc-council:
- Synthesizer instruction is "resolve + surface," which still tends toward unification. Could be sharpened to require falsifiers and preserve unresolved dissent explicitly.
- No frame-mutation layer on top of the model-diversity layer (would be additive, not replacement).
- Single-round deliberation only (v1 limitation per ARCHITECTURE.md §Known Limitations).

**/red-team specialists share the brief; diversity is role-based, not frame-based.** red-team.md §2: each specialist gets "the proposal under review (or pointer to it)" — same brief. Diversity comes from distinct attack patterns per role (security/logic/state/...). **But** §1.5 Claim-refute pass adds input-side diversity at the claim layer: claims are tagged `claim_type` (existence/static-shape/behavior/non-code/scope-completeness) and routed to different verification branches. That's frame-diversity at the claim level, not the specialist level. Remaining gap for /red-team:
- Specialists could receive frame-mutated briefs (one assumes adversarial deployment, one assumes scale failure, ...) in addition to role-based attack patterns. Additive.
- The cross-family adversarial mode (#872–874) is the unbuilt orthogonal-critic path for trust verdicts — distinct from cc-council's cross-family path for opinions. Funding it closes the gap for the trust-decision use case specifically.

**Net correction to the original recommendation:** "Fund the cross-family critic" was framed as if the stack lacked it. The stack has it for opinion/consensus (cc-council default). The gap is narrower: cross-family critique for **trust verdicts** (/red-team adversarial mode). Frame-diversity and falsifier-gating remain valid as additive improvements on top of existing model-diversity.

## What would falsify this

- ~~If `cc-council` or `/red-team` already implement frame mutations and falsifier-gating, the "typical implementation" prior is wrong for this stack and the recommendation collapses to "fund the cross-family critic (#872)."~~ **Resolved 2026-07-19:** cc-council implements cross-model diversity (stronger than frame diversity) as default. /red-team has claim-type routing at the claim-refute layer. Falsifier-gating is absent from both. The narrowed recommendation is now: frame-mutation as additive layer + falsifier-gating at synthesis + fund /red-team adversarial mode for trust verdicts.
- If an A/B test on this stack showed council beating well-context-loaded single-agent by a wide margin, correlated errors aren't the bottleneck. **Still untested.**
- If same-family critics on this stack are already calibrated against past verdicts, orthogonal-model critique adds less. **Still untested — and partially moot since cc-council's default already uses different families.**

## Related

- [[solo_operator_adr_best_practices]]@related — references the "ensemble approach" for second opinions
- [[llm-as-judge-biases]]@related — position/length/self-preference biases in model judges (seed)
- [[tournament-prompting]]@related — the compete-mode pattern itself (seed)
- [[frame-mutation]]@related — input-side diversity technique (seed)
- [[falsifier-gating]]@related — output-side rigor technique (seed)
- [[cross-family-critic]]@related — error-decorrelation via orthogonal model (seed)

## Auto-related

<!-- Auto-generated by wiki_after_write.py — do not edit manually -->

## Sources

- Trigger: YouTube video transcription `Anthropic Engineers Are Using A New Claude Code Prompting Trick` (downloaded to `~/Downloads/`); analyzed in session-2026-07-19.
- Pattern justification: best-of-N sampling, ensemble methods, RLAIF judge literature (prior knowledge, not fetched this session).
- LLM-as-judge bias thresholds: prior knowledge of position/length/self-preference studies; not re-measured against this host's rubrics.
- Skill claims: **VERIFIED 2026-07-19** by reading `cc-council/ARCHITECTURE.md`, `cc-council/README.md`, all 6 `cc-council/agents/*.md`, and `red-team/commands/red-team.md`.
