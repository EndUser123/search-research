# Reasoning-Mode Routing Table

**Purpose:** one shared answer to "which thinking command do I use for this epistemic state?" Each skill in cc-skills-thinking owns a slice of cognitive work; this table is the map between them. New skills must answer "which cell of this table do I serve?" before being added.

This is a **routing reference**, not a framework or a gate. No hook enforces it. It exists so the seven overlapping reasoning skills don't each re-derive "when to use me" in isolation.

---

## The routing table

Route on **two axes**: *epistemic state* (how confident / how off it feels) × *what you want out of the pass*.

| Epistemic state | What you want | Use |
|---|---|---|
| Clear + confident | nothing — proceed | (no skill) |
| Confident but want a self-critique pass | smarter reasoning, no external cost | **/sequential-thinking** (Generate→Critique→Improve) |
| Something feels off / answer seems too neat | strongest analysis, may call external LLMs | **/reason** (routes by confidence: local_only → single_challenger → parallel_challengers) |
| Solving the wrong problem / premise suspect | reframe, challenge premises, cross-domain analogy | **/genius** |
| Need options / multi-perspective exploration | ranked alternatives + tradeoffs | **/s** (multi-persona brainstorming) or **/tot** (parallel branch exploration) |
| Unexplained performance/data gap | ranked testable hypotheses from data | **/probe** |
| Validate AI output / catch hallucination | skeptical evidence-based review of a plan or diff | **/skeptic** |
| Verify a specific claim is true | prove/disprove with real evidence | **/truth** |
| Capture a lesson from this session | durable memory / skill improvement | **/reflect** (manual) or **/learn** |

---

## Decision shortcut

> **What's wrong, and what would fix it?**
> - *"My reasoning might be shallow"* → /sequential-thinking
> - *"I don't trust this conclusion"* → /reason
> - *"I think I'm solving the wrong problem"* → /genius
> - *"I need to see options"* → /s or /tot
> - *"Something is slow and I can't pinpoint where"* → /probe
> - *"Is this AI output actually sound?"* → /skeptic
> - *"Is this specific claim true?"* → /truth

---

## Boundary clarifications (the common confusions)

- **/reason vs /sequential-thinking**: /sequential-thinking is the *internal* Generate→Critique→Improve loop (Claude critiquing itself, no external calls). /reason is the *router* — it may run that internal loop AND escalate to external LLM challengers when confidence is low. Use /sequential-thinking when you want a cheap self-critique; use /reason when stakes are high and you want the strongest possible analysis including external challenge.

- **/reason vs /genius**: /reason produces the strongest *analysis* of a question you've framed. /genius challenges the *framing itself* — it tells you you're asking the wrong question. If your question is right, /reason. If you suspect your question is wrong, /genius first.

- **/s vs /tot**: both explore multiple perspectives. /s is multi-*persona* brainstorming (SCAMPER, Six Hats, first-principles) producing ranked strategic options. /tot is multi-*branch* reasoning (analytical/creative/skeptical/pragmatic branches evaluated in parallel). Use /s for strategic/option-generation; /tot for reasoning-path exploration on a single hard problem.

- **/skeptic vs /truth**: /skeptic reviews an *AI output* (plan, diff, analysis) for soundness broadly. /truth verifies a *specific claim* against real evidence. Review-the-artifact → /skeptic; prove-the-assertion → /truth.

- **/probe is data-shaped, not idea-shaped.** It reads RUN_INDEX.json / benchmark metrics and generates hypotheses from data distributions. Don't use it for design reasoning — use it when "something is slow/unexplained and I can't pinpoint where."

---

## When NOT to use a thinking skill

- Routine code review with file:line findings → **/review** (cc-skills-sdlc), not /skeptic.
- Adversarial trust verdict on a proposal (PROCEED/REVISE/BLOCK) → **/red-team**, not /reason. /reason analyzes; /red-team adjudicates.
- Root-cause a bug → **/rca** (cc-skills-sdlc), not /probe. /probe is data/performance; /rca is code/behavior.
- Fast risks-and-mitigations on a proposal → **/risks** (cc-skills-sdlc), not /reason. /risks is the lightweight pessimistic pass; /reason is the heavyweight analysis.

---

## Adding a new reasoning skill

Before shipping a new thinking skill, answer:
1. **Which cell of the table does it serve?** If it overlaps an existing cell, justify why it's separate (different axis, not just different framing).
2. **What is the boundary with its neighbors?** Add a line to the "Boundary clarifications" section.
3. **Does its `suggest:` field point to the right escalation path?** (Not a cyclic web — a directed graph toward deeper/cheaper alternatives.)

If a new skill can't answer #1, it probably shouldn't exist as a separate command.
