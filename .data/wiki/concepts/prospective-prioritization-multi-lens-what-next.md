---
title: "Prospective multi-lens prioritization: the 'what should I do next?' gap"
created: 2026-07-21
source: session-2026-07-21
sources:
  - https://agility-at-scale.com/ai/strategy/ai-use-case-identification-and-prioritization/
  - https://www.unframe.ai/blog/task-solving-vs-goal-driven-agents-enterprise-ai
  - https://daily.dev/blog/weighted-scoring-model-guide-for-developers/
  - https://dev.to/alvarolorentedev/the-strategic-vs-tactical-mindset-39m9
  - https://machinelearningmastery.com/the-complete-ai-agent-decision-framework/
  - P:/.data/wiki/concepts/multi-agent-correlated-errors.md
  - P:/.data/wiki/concepts/plan-then-execute-pattern.md
  - P:/.data/wiki/concepts/deliberation-waste-re-deriving-same-answer.md
tags: [prioritization, decision-making, what-next, multi-lens, tactical, strategic, roi, weighted-scoring, solo-operator]
host: both
agent: grok
verification: web_sources_cited
cognitive_load: 4
summary: "How to answer 'what should I do next?' for a solo operator directing an AI fleet. The structural gap: existing skills do multi-lens work RETROSPECTIVELY (/risks, /debrief) or build opportunity landscapes at SESSION END (/aar), but none do PROSPECTIVE multi-lens prioritization with horizon detection. Research synthesis: separate discovery from prioritization, decompose value/effort into named drivers, sequence quick wins then big bets, detect tactical vs strategic horizon, and start with single-lens before building multi-lens."
---

# Prospective multi-lens prioritization: the "what should I do next?" gap

## The gap (what's missing in our skill stack)

Asking "what should I do?" needs three things held simultaneously:

| Component | What it means | Closest existing skill | Gap |
|---|---|---|---|
| Multiple perspectives/lenses | Risk, learning, debt, momentum, strategic — applied *simultaneously* | `/risks` (8 specialists), `/debrief` (5 lens subagents) | Both are **retrospective/adversarial**, not prospective prioritizers |
| ROI/impact ranking | Weight lenses so the answer isn't "everything matters equally" | `/aar` opportunity dispositions | `/aar` builds the landscape at **session end**, not as a live "next?" question |
| Context intelligence (tactical vs strategic) | Detect horizon from current work, adapt the lens weighting | Nothing | **Missing entirely** |

`/tp` critiques a *chosen* option (assumes the set is decided). `/plan` plans *one* thing (assumes the choice is made). `/go` orchestrates execution, doesn't decide what to execute. No skill does prospective multi-lens prioritization with horizon detection.

## The two-unknowns frame (why "what next?" is hard)

| Unknown | Meaning | Coverage |
|---|---|---|
| What's open? | The option set (handoffs, AAR opportunities, tasks, debt) | ✅ `/handoff list`, AAR dispositions, tasks store — data exists |
| What's "best"? | The criterion (risk reduction? forward progress? learning? cleanup?) | ❌ None — and this is the binding one |

Without a named criterion, any recommendation is a coin flip dressed up. Past "what should I do?" answers felt bad because they picked a criterion implicitly (often "whatever's in front of me") and optimized for it silently.

## Do's (from research + our patterns)

### 1. Separate discovery from prioritization

Source: [agility-at-scale.com](https://agility-at-scale.com/ai/strategy/ai-use-case-identification-and-prioritization/).

Discovery rewards breadth (surface everything); prioritization rewards ruthlessness (fund almost nothing). Teams that collapse them fund whatever surfaces most loudly — the loudest executive's pet, the demo that impressed in a workshop — not the highest-scoring candidate.

**For us:** `preflight` is discovery; the missing piece is a *prioritization* step that runs after preflight produces the option set, not before.

### 2. Decompose axes into named drivers

Source: agility-at-scale.com, [daily.dev weighted scoring](https://daily.dev/blog/weighted-scoring-model-guide-for-developers/).

A dot plotted on a bare 2×2 (value vs effort) is an opinion. The defensible version decomposes each axis:

**Impact drivers** (so "value" stops being a mystery number):
- Forward progress on a named goal
- Risk reduction (debt, auth, blockers)
- Learning / pattern validation
- Cleanup / future-maintenance reduction

**Effort drivers** (so "effort" doesn't collapse distinct obstacles):
- Data availability (do we have what we need?)
- Integration complexity (how many systems touched?)
- Technical readiness (can we do this today?)
- Reversibility (how hard to undo if wrong?)

Two raters scoring the same candidate reach the same number for the same reasons only if the drivers are named.

### 3. Sequence quick wins → big bets → fill-ins; kill money pits

Source: agility-at-scale.com (impact/effort matrix quadrants).

- **Quick wins** (high impact, low effort) → fund first, build momentum and credibility
- **Big bets** (high impact, high effort) → strategic core; sequence after quick wins because they need data/integration/readiness
- **Fill-ins** (low impact, low effort) → safe experimentation fodder, never the headline
- **Money pits** (low impact, high effort) → the quadrant discipline exists to kill

### 4. Detect horizon and adapt lens weighting

Source: [dev.to strategic vs tactical](https://dev.to/alvarolorentedev/the-strategic-vs-tactical-mindset-39m9).

| Horizon | Question | Lens weighting |
|---|---|---|
| Tactical (now/today) | "What do we need to do?" | Risk + blockers dominate |
| Strategic (quarter/year) | "Where do we need to go?" | Learning + momentum dominate |

Career-progression data (dev.to): early career 99% tactical → directors 5% tactical. For a solution architect directing an AI fleet, the ratio should skew strategic but never hit 0% tactical — the fleet still needs unblocking daily.

### 5. Start simple, evolve based on real use

Source: [machinelearningmastery.com](https://machinelearningmastery.com/the-complete-ai-agent-decision-framework/).

> "Start with the simplest solution that could work. Build a minimal version. Measure real performance against your success metrics. Only then add complexity based on actual limitations, not theoretical concerns."

**For us:** before building a multi-lens fan-out prioritizer, try a single-lens "name the criterion, rank against it" pass. Escalate to multi-lens only if single-lens consistently feels insufficient.

### 6. Name a default criterion and act on it

Cross-reference: [[evidence-first-default-and-needless-confirmation]] — when you've stated a default, act rather than ask. For "what next?" without a stated criterion, the operator's default appears to be "whatever's in front of me"; the structural fix is to name a better default explicitly (likely: risk reduction, per debt-first discipline).

## Don'ts (failure modes)

### 1. Don't collapse discovery and prioritization

Symptom: brainstorming and choosing in one step. Result: loudest option wins.

### 2. Don't score on bare gut feel

Symptom: "value = 8" with no sub-drivers. Result: two raters measure different things, disagreement is unresolvable because it's unnamed.

### 3. Don't mistake task completion for goal achievement

Source: [unframe.ai](https://www.unframe.ai/blog/task-solving-vs-goal-driven-agents-enterprise-ai).

> "AI agents currently fail to reliably complete most office tasks, with failure rates approaching 70%" (Carnegie Mellon)
> "The average organization scrapped 46% of AI proof-of-concepts before reaching production" (S&P Global, 2025)

The signature: "agents completing tasks while problems persist." This maps directly to our [[fabricated-causal-chain-receipt-required]] pattern — declaring "done" because tasks completed, without checking the goal moved.

### 4. Don't build the multi-lens fan-out before trying single-lens

Source: machinelearningmastery.com — "Common Decision Mistakes: Choosing Multi-Agent Too Early."

> "My task has three steps, so I need three agents" — adds coordination complexity, latency, cost. Debugging becomes exponentially harder.

**For us:** building a `/prioritize` skill with 5 lens subagents before validating that single-lens "name the criterion" is insufficient is exactly this anti-pattern. Try the lightweight version first.

### 5. Don't get stuck in either tactical or strategic mode

Source: dev.to.

- **Over-tactical:** lack of bigger picture, lost opportunities, increased baseline (quick fixes over sustainable solutions), crisis management loop, burnout
- **Over-strategic:** analysis paralysis, missed details, disconnect from the team, frustration

For a solo operator, over-tactical is the bigger risk because the tactical queue is always full and the strategic work never surfaces unless explicitly protected.

### 6. Don't pilot-sprawl

Source: agility-at-scale.com.

Funding a dozen low-value proofs-of-concept in parallel feels like progress (activity is high, demos ship) but value stays flat because the portfolio has no concentration. **For us:** this is the "spawn 5 subagents on 5 different things" failure mode — feels productive, delivers nothing concentrated.

### 7. Don't use >7 criteria in the weighted scoring model

Source: daily.dev. More than 5-7 criteria means the model is unfocused — collapse related criteria or drop the weakest.

## The synthesis (what to actually do)

Three methods, cheapest to most expensive:

1. **Direct synthesis (no tooling)** — Read `/handoff list` + open AAR opportunities + tasks; operator states the criterion in one phrase; recommend with reasoning. Cost: one turn.
2. **Lightweight variant (`/tp prioritize`)** — Extend `/tp` with a prospective mode that fans out lenses over open streams + criterion-weighting + horizon detection in one pass. Reuses proven `/risks` fan-out shape. Cost: ~1 session to build and test.
3. **Standalone skill (`/prioritize`)** — First-class skill with its own SKILL.md. Only justified after method 2 validates the pattern. Higher investment.

**Selection criterion:** proven-pattern-reuse vs greenfield-investment. Method 2 wins on this axis IF the question recurs as a standing need. Method 1 wins if it's a one-off.

**Falsifier for the whole framing:** if the real need is just "give me a better ad-hoc answer right now," all three methods are overkill. The build path only makes sense if "what should I do?" genuinely recurs as a standing need.

## Relationship to existing concepts

- [[plan-then-execute-pattern]] — adjacent; this concept is "what to plan," that one is "plan then execute."
- [[multi-agent-correlated-errors]] — informs the multi-lens fan-out: attack correlated errors, not persona diversity.
- [[deliberation-waste-re-deriving-same-answer]] — the prioritizer must not become a new site of deliberation waste; single-pass ranking, not re-deliberation.
- [[evidence-first-default-and-needless-confirmation]] — the "name a default criterion and act" pattern is a direct application.
- [[fabricated-causal-chain-receipt-required]] — the "task completion ≠ goal achievement" don't is a receipt problem.
- [[solo_operator_adr_best_practices]] — solo context; no committee to reconcile with.

## Open questions

- Does "what should I do?" recur enough to justify a dedicated skill, or is it a `preflight` + `/tp` chain?
- Where does horizon detection live — in the user's prompt ("tactical: what now?" vs "strategic: what next quarter?"), or auto-detected from current work?
- Should the prioritizer re-rank mid-session as work completes, or only fire on explicit invocation?

## Sources (full list)

- [AI Use Case Identification and Prioritization](https://agility-at-scale.com/ai/strategy/ai-use-case-identification-and-prioritization/) — agility-at-scale.com. Source for: discovery vs prioritization split, pilot sprawl, impact/effort quadrants, named drivers, quick wins → big bets sequencing, risk/strategic-fit secondary axes.
- [Task-Solving vs. Goal-Driven Agents](https://www.unframe.ai/blog/task-solving-vs-goal-driven-agents-enterprise-ai) — unframe.ai, 2026-03-31. Source for: task completion ≠ goal achievement, supervision bottleneck, 70% failure rate (Carnegie Mellon), 46% PoC scrap rate (S&P Global 2025).
- [Weighted Scoring Model: Guide for Developers](https://daily.dev/blog/weighted-scoring-model-guide-for-developers/) — daily.dev, 2024-08-22. Source for: concrete weighted-scoring mechanics (criteria, weights, 1-5 scale), 5-7 criteria limit, anti-patterns (never updating weights, no documentation).
- [The Strategic Vs. Tactical Mindset](https://dev.to/alvarolorentedev/the-strategic-vs-tactical-mindset-39m9) — dev.to. Source for: horizon detection frame, over-tactical failure modes (crisis loop, burnout), over-strategic failure modes (analysis paralysis, disconnect), career-progression ratio shift.
- [The Complete AI Agent Decision Framework](https://machinelearningmastery.com/the-complete-ai-agent-decision-framework/) — machinelearningmastery.com, 2025-11-15. Source for: three-question decision narrowing, "start simple, evolve" principle, multi-agent-too-early anti-pattern, decision-mistakes table.

## Auto-related

- [[multi-agent-correlated-errors]]
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
