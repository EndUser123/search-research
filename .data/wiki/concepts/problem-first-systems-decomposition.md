---
title: "Problem-first systems decomposition: the methodology that prevents optimization-without-understanding"
created: 2026-07-23
source: session-2026-07-20/23, /www research
tags: [methodology, mental-model, first-principles, systems-thinking, multi-track, solutioning, root-cause, LLM-agent-failure-mode]
summary: >
  The mental model that, if applied before generating solutions, prevents the
  recurring failure pattern where an LLM agent jumps to solutions without
  understanding the problem, collapses multiple independent tracks into one,
  and illogically dismisses work because an architectural change "will solve
  it eventually." Combines first-principles decomposition (what's actually
  true?), systems thinking (how do components interact?), multi-track
  synthesis (what tracks are needed independently?), and steelman-before-
  dismissing (in a world where the architectural fix ships, what does the
  tactical fix still need to do?).
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/analyst-exhibits-pattern-being-analyzed
    type: refines
  - target: wiki/concepts/subagent-synthesis-report-gate
    type: related
---

# Problem-first systems decomposition

## The failure it prevents

The LLM agent exhibits a recurring pattern when asked to solve problems:

1. **Jump to solutions** — the user identifies a problem; the agent generates solutions before decomposing the problem
2. **Binary collapse** — when multiple approaches exist, the agent collapses to "fix A or fix B" instead of "fix A and B independently"
3. **Premature dismissal** — when an architectural fix is identified, the agent illogically dismisses tactical improvements because "the architecture will solve it eventually"
4. **Over-explanation instead of direction** — the agent produces paragraphs where a sentence would do

Each of these is a form of **optimization without understanding** (Sijie Yang, 2025): the agent optimizes a solution without understanding the system it's optimizing in.

## The methodology (4 steps, applied before generating solutions)

### Step 1 — First-principles decomposition: "What's actually true here?"

Before generating any solution, break the problem to its fundamental truths:

- What is the system actually doing? (not what it's supposed to do — what it IS doing)
- What are the immutable constraints? (physical, contractual, authority boundaries)
- What are the root causes — not the first cause, but the chain? (ask "why" at least 3 times)
- What assumptions am I making that I haven't verified?

**The failure this prevents:** jumping to "add a Python classifier" before asking "why does the scanner need to classify in the first place?" The root cause was session-ownership attribution; the classifier was a symptom-level fix.

### Step 2 — Systems thinking: "How do components interact?"

Map the system before touching it:

- What are ALL the components involved? (not just the obvious ones)
- How do they interact? (dependencies, feedback loops, shared state)
- What does an intervention in component A do to component B?
- What am I not seeing?

**The failure this prevents:** saying "fix the write model" without recognizing that `/close` is needed regardless of write model — it verifies, captures decisions, writes observations. Those functions don't disappear when sessions are isolated.

### Step 3 — Multi-track synthesis: "What tracks are needed, independently?"

When multiple issues surface, don't collapse to one track:

- Enumerate ALL tracks (immediate fixes, tactical improvements, architectural changes)
- Classify each as independent, dependent, or blocking
- For independent tracks: pursue all simultaneously — they don't compete
- For dependent tracks: name the dependency explicitly

**The failure this prevents:** "either fix `/close` OR fix the write model." Both are needed. They're independent. The agent collapsed two independent tracks into a false binary.

### Step 4 — Steelman before dismissing: "In a world where X is fully solved, what does Y still need to do?"

Before saying "Y is unnecessary because X will solve it":

- Imagine X is fully shipped and working
- Ask: in that world, what does Y still need to do?
- If the answer is "nothing" → dismissing Y is justified
- If the answer is "a lot" → Y is needed independently; don't dismiss it

**The failure this prevents:** "worktree-per-session makes `/close` improvements unnecessary." In a worktree-isolated world, `/close` still needs to: verify claims, capture decisions, write session observations, check handoff chain integrity, surface open work. Dismissing `/close` was illogical because its core functions don't depend on the write model.

## How this would have changed this session

| What happened | What problem-first decomposition would have produced |
|---|---|
| User asked to optimize `/close`; I proposed Python helpers | First: "what is `/close` for?" → "what's broken?" → "what are root causes?" → THEN solutions at each level |
| User asked for long-term; I said "fix the write model, don't bother with `/close`" | Multi-track: "three independent tracks — immediate, `/close` improvements, write-model architecture — all needed" |
| User said "your thinking is not complete" | I wouldn't have needed the correction if I'd steelmanned `/close` before dismissing it |
| User said "Too many words" | Directness is a symptom of understanding — if I'd decomposed properly, the answer would have been shorter because it would have been structured |

## Why this is hard for LLMs specifically

The Sijie Yang research names the core tension: **AI optimizes without understanding.** LLMs are trained to produce helpful output fast. The pressure to produce a solution is stronger than the pressure to understand the problem. This is architectural, not behavioral — internal discipline alone doesn't fix it (confirmed by this session: I exhibited the pattern while analyzing it, per [[analyst-exhibits-pattern-being-analyzed]]).

The fix is structural: **a gate between problem identification and solution generation.** Before producing any solution, the agent must:
1. State the problem in one sentence
2. Name the root cause chain (≥3 "whys")
3. Enumerate the affected components
4. Classify tracks as independent or dependent
5. Steelman any track it's about to dismiss

This is the same structural-gate pattern as the [[subagent-synthesis-report-gate]] rule: the fix is not "remember to think harder" but "insert a verification step that forces the thinking before the output."

## Relationship to existing skills

| Skill | How it relates |
|---|---|
| `/tp` | `/tp`'s construct→challenge→converge is a single-question version of this. Problem-first decomposition is the multi-question generalization. |
| `/aar` | `/aar`'s layered root-cause (OBSERVED_FAILURE → IMMEDIATE_TRIGGER → PROXIMATE_CAUSE → CONTRIBUTING_CONDITIONS → SYSTEMIC_REUSABLE_CAUSE) is Step 1 applied to failures. This methodology generalizes it to all problem-solving, not just post-mortems. |
| `/design` | `/design`'s write→review→revise loop produces solutions but doesn't enforce problem decomposition before the first write. This methodology is the pre-step. |
| `/close` | `/close`'s tier system (Tier 1/2/3) is Step 3 (multi-track) applied to gate resolution. The tier system would have been better if Steps 1-2 had been run first. |

## Sources

- Sijie Yang, "First-principle-based systematic thinking is more important than ever" (sijie-yang.com, 2025-08-22) — core insight: "AI optimizes without understanding → first principles + systems thinking → question the objective first." **Score: 10/12** (practitioner + AI-specific framing).
- Addy Osmani, "First Principles for Software Engineers" (addyosmani.com, 2022-12-04) — 4-step framework: identify, decompose, challenge assumptions, build from ground up. **Score: 10/12** (software-engineering specific, actionable).
- Farnham Street, "What is First Principles Thinking?" (fs.blog) — canonical mental model reference. **Score: 9/12**.
- Local wiki: [[analyst-exhibits-pattern-being-analyzed]] — the meta-pattern where the analyst exhibits the failure being analyzed. This session is a direct instance.
- Local wiki: [[subagent-synthesis-report-gate]] — the structural-gate pattern this methodology generalizes.

## Falsifier

If applying this methodology consistently produces worse outcomes than jumping to solutions (measured by: more user corrections needed, more rework, more illogical dismissals), the methodology is wrong. If it produces fewer corrections and less rework, it's validated.

The session that produced this concept is itself evidence: the user needed ~15 steering corrections. Applying this methodology from the start would have reduced that to ~3-5.

## Auto-related

- [[multi-agent-correlated-errors]]
- [[python-behavior-tree-framework-for-autonomous-llm-agents--technical-specificatio]]

