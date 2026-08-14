---
title: "SDLC skills"
date: "2026-07-13"
mode: "COPILOT"
uuid: "32854362-dbf1-4d22-96b5-b14b49b7de72"
entry_count: 13
---

## Human

please review the transcript.  Do you think the skills shown represent natural boundries for developers in their sdlc?  Note I'm a solo-director with a fleet of ai-coders.

## Assistant

Short answer: yes, the skills and boundaries described in the transcript line up very cleanly with natural SDLC roles—but they’re closer to *workflow stages* than to *individual developer roles*, which actually fits your “solo‑director with a fleet of AI coders” setup well.[1]

I’ll separate FACT vs CONSENSUS vs SPECULATION as we go, and then suggest concrete next steps for tightening these boundaries in your system.

***

## What the transcript actually defines

**FACT (from the transcript)**: The consolidation leaves you with three primary recommendation surfaces: `/recap`, `/debrief`, and `/rns`, with GTO as internal detection for debrief gaps and DNE folded into `/recap check`.[1]

- `/recap`: Establish current state, what changed, what’s uncertain, and whether the work is safe to hand off.[1]
- `/debrief`: Explain gaps, causes, recurring patterns, and longer-term lessons across the work.[1]
- `/rns`: Turn evidence from recap/debrief/reviews into a ranked set of concrete next actions.[1]

The transcript explicitly maps these to SDLC language:[1]

| Surface   | Goal                                                                                  | SDLC role                                   |
|----------|----------------------------------------------------------------------------------------|---------------------------------------------|
| `/recap` | Establish what just happened and handoff readiness                                     | Review / closure gate                       |
| `/debrief` | Explain gaps, causes, recurring patterns, longer-term lessons                        | Retrospective / process improvement         |
| `/rns`   | Turn evidence into ranked, concrete next actions                                       | Planning / prioritization                   |

This is not my interpretation; it’s stated in the transcript itself.[1]

**CONSENSUS (industry practice)**: In SDLC, teams naturally converge on three recurring “thinking modes” even if they don’t name them this cleanly:

- State/closure: “What did we just do and is it ready?” (code review, test runs, release readiness).
- Learning/retrospective: “What went wrong or could be better?” (retros, incident postmortems).
- Planning/prioritization: “Given everything we know, what should we do next?” (backlog grooming, triage).

Your three surfaces are a near one‑to‑one with those modes, which is why they feel “natural.”  

**SPECULATION (high confidence)**: For a solo director + AI coders, these aren’t boundaries between *developers* so much as boundaries between *agents* or *skills* that take turns owning the SDLC loop. Confidence: high, because the transcript explicitly frames them as a pipeline and shows tests verifying that each surface stays in its lane.[1]

***

## Do these look like natural SDLC boundaries?

**FACT**: The transcript itself argues the goals “now make sense as an SDLC pipeline” and documents the intended flow:[1]

```text
work → recap → debrief (when causes/gaps matter)
     → RNS → human selection → implementation
     → recap check
```

This implies four distinct boundaries:

1. **Work → recap**: transition from “doing” to “summarizing and checking” (state and safety).
2. **Recap → debrief**: only when you care about causes, patterns, and long‑term lessons.
3. **Debrief/recap → RNS**: when you’re ready to choose specific actions and priorities.
4. **RNS → implementation → recap check**: when chosen actions are executed and audited pre‑handoff.

From an SDLC perspective:

- `/recap` matches a **review/closure gate**: static analysis + tests + “is this ready to merge / deploy / hand off?”.
- `/debrief` matches **retrospective / RCA**: incidents, failed experiments, recurring friction.
- `/rns` matches **planning / triage**: backlog shaping, “what gets done next, by whom, and why”.

**CONSENSUS**: Most mature teams eventually enforce something like:

- Don’t plan on stale data → always recap/review first.
- Don’t jump from incident to action without an RCA → debrief before change.
- Don’t deploy ad hoc fixes → prioritize and design a plan before implementation.

Your skill boundaries align with that consensus pattern.

**SPECULATION (medium confidence)**: If you wanted to map these to *human* roles, you’d get something like:

| Surface   | Human “hat”                        | Typical role archetype              |
|----------|-------------------------------------|-------------------------------------|
| `/recap` | Reviewer / release manager          | Senior dev / tech lead              |
| `/debrief` | Facilitator / incident analyst     | SRE / architect / engineering manager |
| `/rns`   | Planner / product owner / triager   | PM / EM / lead developer           |

But in your world, these are *AI skill hats* rather than different humans, which makes the boundaries even more valuable: they encode roles that your fleet of coders can “play” sequentially instead of everything happening in one blended agent.

***

## Are these “natural boundaries for developers” or for agents?

You asked specifically: “Do you think the skills shown represent natural boundaries for developers in their SDLC?”

My take, with explicit separation:

- **FACT**: The transcript treats them as *surfaces in a pipeline*, not job descriptions. They are about who owns which part of the decision flow (state, learning, choice), not about job titles.[1]
- **CONSENSUS**: Human developers *do* switch between these modes, but SDLC pain often comes from mixing them: people prioritize while still confused about the state, or do retros while secretly trying to pick actions. Boundaries that separate these modes are widely considered good practice.
- **SPECULATION (high confidence)**: For your environment, these are best thought of as **epistemic phases** rather than developer boundaries:

  - Recap: factual state and readiness (epistemic “what is true, right now?”).
  - Debrief: causal and pattern inference (epistemic “why did this happen?”).
  - RNS: normative choice (epistemic “given truths and causes, what ought we do?”).

You can absolutely *assign* different AI coders or different configurations to each phase, but that’s an orchestration decision, not a natural law of SDLC.

So I’d answer your question this way:

- **Yes**: These skills align with natural *process* boundaries in SDLC (review/closure, retrospective, planning).[1]
- **Not exactly**: They are not natural boundaries between *developers* so much as clean boundaries between kinds of thinking and responsibility.
- **For a solo director + AI fleet**: They are excellent boundaries between *skills/agents* you orchestrate—each phase can be run by different coders or different “modes” of the same coders.

Confidence: high that the mapping to SDLC phases is sound; medium that you’d want to enforce them as hard boundaries on human roles, because teams vary.

***

## What this means for your “fleet of AI coders”

Given your role (solo director) and that these coders are tool‑invoked agents, the boundaries imply a very concrete orchestration pattern:

**FACT (from transcript)**: The recommended design principle is “separate the evidence source from the decision renderer; recap and debrief own evidence collection, RNS owns turning grounded findings into selected work.”[1]

Translated into your environment:

- One **cluster of skills/agents** owns *evidence and state*:
  - Running tests, summarizing transcripts, doing impact analysis.
  - Producing a structured `HandoffPacket` as the recap output.[1]

- Another **cluster** owns *learning and improvement*:
  - Mining transcripts logs, identifying recurring failures and friction.
  - Producing a `FindingPacket` with explicit gaps and causes.[1]

- A third **cluster** owns *decision and prioritization*:
  - Accepts `HandoffPacket` + `FindingPacket` + other reviews.
  - Produces an `ActionPlan` with ranked, owner‑annotated next steps.[1]

Then your human “director” role:

- Consumes the ActionPlan.
- Makes final calls on risk, scope, and timing.
- Kicks off actual implementation agents (`/go`, task‑specific skills, etc.), then routes back through `/recap check` as a pre‑handoff audit.[1]

That’s a very natural agentic SDLC model: no single AI coder needs to both infer causes and prioritize actions and review safety; each has a well‑scoped responsibility.

***

## Concrete next steps to tighten these boundaries

All of these are grounded in improvement suggestions already present in the transcript.[1]

**FACT (from transcript)**: The thought‑partner pass explicitly recommends:

1. Making command boundaries explicit (routing rules).[1]
2. Creating shared packet contracts (HandoffPacket, FindingPacket, ActionPlan).[1]
3. Defining the canonical SDLC loop and testing it.[1]
4. Adding routing + non‑recursion tests.[1]
5. Measuring whether RNS adds value.[1]

You can turn that into actionable system work:

1. **Lock in routing rules**

   - `/recap`: always the first stop for “what happened / is this ready?”.
   - `/debrief`: the default for transcript mining, “what went wrong,” “what keeps failing?”.
   - `/rns`: only takes *structured outputs* (recap, debrief, audits, reports), not raw transcripts.

   This prevents “RNS as a second recap” or “debrief as a generic prioritizer,” which the transcript flags as a drift risk.[1]

2. **Define and implement the packet contracts**

   - Implement `HandoffPacket` schema as recap output.
   - Implement `FindingPacket` schema as debrief output.
   - Implement `ActionPlan` schema as RNS output.

   Then have RNS only accept those schemas by default, which enforces the evidence→decision separation you wanted.[1]

3. **Codify the SDLC loop in docs and tests**

   - Add explicit tests that a “debrief this transcript” route hits `/debrief`, not `/rns`.[1]
   - Add explicit tests that “What should we do next?” on a debrief artifact routes to `/rns`.[1]
   - Ensure `/recap check` stays an audit, not a second RNS surface.[1]

4. **Measure RNS’ incremental value**

   - Track how often RNS changes the prioritization compared to “quick suggestions” from recap.
   - If RNS almost always adds signal (clear ranking, dependencies, rationales), you keep it as a separate step.
   - If it doesn’t, you might merge some of its logic into recap for low‑risk tasks, keeping RNS for higher‑stakes planning only. This part is *SPECULATION* with medium confidence; you’d validate empirically.

***

One clarifier that would help me give sharper advice: are you thinking of mapping these three boundaries onto *different AI coders/skills* (i.e., distinct plugins/agents), or keeping them as modes within a single orchestrated “super‑skill” that walks the SDLC loop end‑to‑end?  

## Human

where does 'handoff' go in relation to these three skills shown?  should the skills be for the entire session across compact events, or just the latest memory context?

I think maybe I'm getting confused.  'what happened' is a differetn step from 'is this ready' from 'what went wrong', etc?

## Assistant

You’re not wrong to feel a bit confused—“what happened,” “is this ready,” and “what went wrong” *are* different steps, and the transcript is actually treating them as distinct phases with different owners.[1]

Let me anchor “handoff” in that structure, and then answer the “entire session vs latest context” question.

***

## Where “handoff” actually lives

**FACT (from the transcript)**: `/recap` is described as “the short‑horizon handoff” and later as “establish current state and handoff readiness.” DNE’s pre‑mortem logic was explicitly absorbed into `/recap check`, with its “past → future safety pass belongs immediately before handoff.”[1]

So in your three‑surface model:

- `/recap`: synthesizes **what happened** and current state.
- `/recap check`: audits **is this ready / is it safe to hand off**.
- `/debrief`: analyzes **what went wrong / what are the gaps and causes**.
- `/rns`: decides **what we should do next, and in what order**.

**CONSENSUS**: In an SDLC loop, “handoff” sits *after* recap + safety check, and *before* the next work phase:

- Dev work → recap (state) → recap check (risk/safety) → **handoff** → next owner.
- Separately, debrief and RNS can run before or after handoff depending on whether you’re closing a loop or planning new work.

So: **handoff is a step after recap (and recap‑check), not a fourth recommendation surface.** The transcript treats recap (plus its check) as the “review/closure gate” that directly precedes handoff.[1]

***

## Whole session vs latest memory context

Your question: “should the skills be for the entire session across compact events, or just the latest memory context?”

**FACT (from the transcript)**:

- The flowchart shows `/recap` attached to a “Session chain” node and describes it as a “full session‑chain walk and Resume Here contract.”[1]
- `/debrief` is invoked for “Transcript / repeated failures,” i.e., it explicitly mines broader history.[1]
- `/rns` takes “any evidence‑backed output” (recap, debrief, audits, reports) and ranks/selects actions.[1]

That implies:

- `/recap`: operates over the **session chain** but produces a *compact* summary of the relevant history and current state (not only the last turn).[1]
- `/debrief`: can span **longer windows**, especially when looking for recurring patterns or root causes across multiple events.[1]
- `/rns`: should consume whatever **scope of evidence packet** you hand it—often the recap/debrief outputs, which themselves may summarize many events.[1]

**CONSENSUS**:

- For “what happened” and “is this ready,” you usually want **enough history to explain current state** (the compact session chain), not the entire life of the repo.
- For “what went wrong / what keeps failing,” you often want **multi‑event history**, because patterns matter.
- For “what should we do next,” you want **whatever evidence is relevant to the decision horizon** (could be just the latest change, or a series of related incidents).

**SPECULATION (high confidence)**: A good rule of thumb for your environment:

- `/recap`: **compact session scope**—walk the chain, but emit a compressed “current state + key recent events” packet.
- `/recap check`: same scope, but with added risk/safety signals.
- `/debrief`: **configurable scope**—by default “this workstream / these incidents,” not necessarily full global history.
- `/rns`: driven by the **scope of the packet it receives**; it doesn’t decide scope, it respects what recap/debrief hand it.

So the skills are “session‑aware,” but their *outputs* should be compact artifacts (HandoffPacket, FindingPacket, ActionPlan) summarizing that history.[1]

***

## Untangling the steps: “what happened”, “is this ready”, “what went wrong”

You’re exactly on the key distinction. In the transcript, these are different moves:

1. **“What happened?” → recap**

   - **Goal**: establish facts and state.
   - Typical questions: What did we do? What changed? What’s the current state of the work?
   - SDLC role: review/summary over the *session chain*.[1]

2. **“Is this ready / safe to hand off?” → recap check**

   - **Goal**: apply a risk rubric on top of the recap state.
   - Typical questions: Are tests green? Are risk factors (blast radius, rollback, null/empty/zero, inversion) acceptable? Should we proceed or roll back?[1]
   - SDLC role: release/merge gate, pre‑handoff audit.

3. **“What went wrong / what are the gaps?” → debrief**

   - **Goal**: explain causes, gaps, patterns, recurring failures.
   - Typical questions: Why did incidents occur? What keeps breaking? What process changes would prevent this?[1]
   - SDLC role: retrospective / root‑cause analysis.

4. **“Given all that, what should we do next?” → RNS**

   - **Goal**: turn evidence into ranked, concrete actions.
   - Typical questions: Which actions should we take? In what order? Who owns them? What are dependencies and acceptance conditions?[1]
   - SDLC role: planning/prioritization.

You can think of it as three layers of questions:

- **Descriptive**: recap → “what happened?”
- **Evaluative/safety**: recap check → “is this ready / safe?”
- **Causal/diagnostic**: debrief → “what went wrong, why, and what does that teach?”
- **Normative/choice**: RNS → “what should we do next, given the above?”

In other words: yes, they are different steps, and your skills map is correctly trying to separate them, not collapse them.

***

## How to place “handoff” concretely in your orchestration

Putting it together for your solo‑director + AI fleet:

1. Run `/recap` on the relevant **session chain** to get a compact state summary (HandoffPacket).[1]
2. Optionally run `/recap check` to audit risk/safety right before handing off.
3. If you care about process improvement or recurring failures, run `/debrief` over a broader transcript window and get a FindingPacket.[1]
4. Feed `HandoffPacket` (and optionally `FindingPacket`) into `/rns` to produce an ActionPlan.[1]
5. You (human director) select from the ActionPlan, trigger implementation (your coding agents), and then loop back through `/recap` and `/recap check` for the next handoff.

So “handoff” is:

- **Downstream of recap + recap check**.
- **Upstream of implementation and the next cycle’s recap/debrief/RNS**.
- Not a separate skill, but a *transition* that uses recap’s output as its contract.

***

To tune this to your actual use: when you say “session,” are you usually thinking “one Claude chat transcript around a specific task,” or “a longer multi‑day workstream with several distinct change sets”? That scope choice will heavily influence how you want recap and debrief to walk history.  

## Human

session can span days.  it cross compact events.  it can even be a resumed session from another day in another terminal.  it can hold and work on many different topics.

What are the sdlc steps that should have descrete skills?

## Assistant

Given that your “session” is long‑lived, cross‑terminal, and multi‑topic, you’ll want skills that anchor **decision points**, not just “phases” in the textbook SDLC. In your environment, discrete skills should map to *reusable cognitive steps* that recur across many sessions and topics.[1][2]

Below I’ll list SDLC steps that are good candidates for distinct skills, then show how they relate to `/recap`, `/debrief`, and `/rns`.

***

## SDLC phases vs skill‑worthy steps

**FACT (industry)**: Common SDLC phases include planning/analysis, design, implementation, testing, deployment, and maintenance. Agile practice adds explicit retrospectives for “what went well / what can be improved,” and ongoing prioritization of work.[3][4][1]

That’s too broad for skills. What you want are **discrete, repeatable decision or evaluation steps** that:

- Consume evidence.
- Produce structured artifacts.
- Gate or redirect the flow of work.

From the transcript plus SDLC references, the strongest candidates are:

1. **State & context synthesis** – “What happened and where are we?”
2. **Readiness / safety gate** – “Is this ready / safe to proceed or hand off?”
3. **Causal / gap analysis** – “What went wrong, what are the gaps, and why?”
4. **Prioritization & planning** – “Given all that, what should we do next?”
5. **Design decision framing** – “What are the options, tradeoffs, and chosen design?”
6. **Change impact assessment** – “If we make this change, what will it affect?”
7. **Post‑implementation audit** – “Did this do what we intended, and what did we learn?”

You already have 1–4 partially covered:

- `/recap` → state & context synthesis.[2]
- `/recap check` → readiness/safety gate (ex‑DNE).[2]
- `/debrief` → causal/gap analysis and recurring patterns.[2]
- `/rns` → prioritization & planning.[2]

The transcript even proposes packet contracts for the first three:[2]

- Recap emits a **HandoffPacket** (state + readiness).
- Debrief emits a **FindingPacket** (gaps, causes, lessons).
- RNS emits an **ActionPlan** (ranked actions, owners, rationale).

Those are exactly the kind of “discrete skills” I’d treat as first‑class, because they define clean boundaries in a long, multi‑topic, cross‑day session.

***

## How those skills sit inside your very long sessions

You described sessions that:

- Span days.
- Cross compact events.
- Resume from other terminals.
- Hold many different topics.

**CONSENSUS**: In such a setting, skills should be **local to a slice of work**, but *session‑aware*:

- A recap skill should walk the **relevant session chain** for the current workstream, then emit a compact HandoffPacket that summarizes that slice.[2]
- A debrief skill should be able to expand scope: single incident, group of related incidents, or longer historical band for pattern mining.[2]
- An RNS skill should consume packets from recap/debrief/reviews, not arbitrary session logs, so that decisions remain grounded and compact.[2]

So for your environment:

- Skills operate **within a session**, but each invocation is scoped to “this workstream / this change / this incident,” not “everything ever.”
- The session is the *backing store*; skills pull relevant history out of it and emit structured artifacts back into it.

***

## SDLC steps that most deserve discrete skills

Grounding this in SDLC sources and your existing surfaces, these are the steps I’d give explicit skills:

### 1. Evidence synthesis / recap

- SDLC anchor: crosses planning, design, implementation, testing, deployment—whenever you need to know “what has happened so far.”[5][1]
- Skill: `/recap` (already present).
- Artifact: **HandoffPacket** (facts, state, uncertainties, recent changes).[2]
- When to call: whenever you resume a workstream, before prioritization, before a gate, or when a multi‑day session has drifted.

### 2. Readiness / safety gate

- SDLC anchor: late implementation / testing / pre‑deployment; can also guard merges for code changes.[6][7]
- Skill: `/recap check` (DNE successor).[2]
- Artifact: **HandoffPacket with risk fields** (Red/Yellow/Blue, blast radius, rollback, inversion, null/empty/zero risks).[2]
- When to call: before handoff to another agent, before deploy/merge, before giving a human the “ready” signal.

### 3. Causal / gap / incident analysis

- SDLC anchor: retrospectives, incident reviews, “lessons learned” after failures or major releases.[4][7]
- Skill: `/debrief`.
- Artifact: **FindingPacket** (gaps, root causes, patterns, durable lessons).[2]
- When to call: post‑incident, after repeated friction, or at sprint/iteration boundaries where you want process improvement.

### 4. Prioritization & action planning

- SDLC anchor: backlog grooming, sprint planning, triage, roadmap decisions.[1][3]
- Skill: `/rns`.
- Artifact: **ActionPlan** (ranked actions, owners, horizon, dependencies, acceptance criteria).[2]
- When to call: after recap/debrief/review, or when you have any structured evidence and need to decide “what next.”

### 5. Design decision framing

- SDLC anchor: design phase (architecture, interface design, integration planning).[7][6]
- Skill (you could add): e.g. `/design‑decision` or integrate into a design skill.
- Artifact: **DecisionRecord** (options, tradeoffs, chosen option, rationale, constraints).
- When to call: before a substantial change (new feature, refactor, architecture shift), especially in multi‑day sessions so future you can understand why.

### 6. Change impact assessment

- SDLC anchor: late design / early implementation, and again pre‑deployment.[8][6]
- Skill (could be distinct or a mode of recap/debrief): `/impact`.
- Artifact: **ImpactAssessment** (affected components, risks, dependencies, observability plan).
- When to call: before implementing risky changes; can feed into recap check and RNS.

### 7. Post‑implementation audit / post‑deploy check

- SDLC anchor: maintenance/operations, continuous improvement.[8][5][7]
- Skill (you partially have via `/recap check`): you might treat this as `/recap check` in a post‑deploy mode.
- Artifact: **OutcomeReport** (did the change achieve its goal, metrics, side‑effects, follow‑up actions).
- When to call: after deployment or completion of a change; feeds into debrief and RNS.

In practice, you don’t need a unique skill surface for all seven; several can be modes of existing surfaces. But **each of these steps is cognitively distinct enough to justify a dedicated skill contract**, especially in an AI‑agent fleet.

***

## How this maps to your three main skills

Given what you already have, a minimal, coherent skill topology:

| SDLC step                      | Skill surface     | Artifact          |
|--------------------------------|-------------------|-------------------|
| Evidence synthesis / recap     | `/recap`          | HandoffPacket     |
| Readiness / safety gate        | `/recap check`    | HandoffPacket+Risk|
| Causal / gap / incident analysis | `/debrief`      | FindingPacket     |
| Prioritization & planning      | `/rns`            | ActionPlan        |
| Design decision framing        | `/debrief` mode or dedicated design skill | DecisionRecord    |
| Change impact assessment       | `/recap` or `/debrief` mode | ImpactAssessment  |
| Post‑implementation audit      | `/recap check` mode | OutcomeReport     |

Your very long sessions then become **sequences of these artifacts** chained over time:

- Days 1–N: work → recap → design decision → implementation → recap check.
- Incident: debrief → FindingPacket → RNS → ActionPlan.
- Ongoing: recap to resume; RNS to reprioritize; debrief occasionally for process improvement.

***

Given this, would you rather keep expanding modes on `/recap` and `/debrief` (design, impact, outcome) or introduce 1–2 new named surfaces (e.g. `/design‑decision`, `/impact`) to keep the mental model simple for you and the AI coders?  

## Human

"That’s too broad for skills. What you want are discrete, repeatable decision or evaluation steps".  I don't understand.  Skills for claude code are the workflows for these steps are they not?  Please let me know if I'm wrong or misunderstanding, and be professionally honest.

"skills should be local to a slice of work, but session‑aware", but then how do we flip that to target the whole session?  I want to make sure we don't exclude something because we scope to a slice of work.

Please don't try to make the skill names you were shown to the sdlc.  Use best practice skill names.

## Assistant

You’re not wrong; you’re pointing at a real tension. I’ll be blunt where I think my earlier wording was misleading and then reframe in Claude‑Code terms.

***

## 1. Are skills “the workflows for these steps”?

Yes—with an important nuance.

**FACT (from your transcript)**: The skills you’re using (`/recap`, `/debrief`, `/rns`, etc.) are defined as surfaces that own particular workflows: recap walks the session chain and emits a handoff‑oriented summary; debrief does transcript mining and gap detection; RNS does ranking and selection.[1]

Where my wording was sloppy:

- When I said “SDLC phases are too broad for skills,” I meant: **“Planning / design / implementation / testing / deployment” are too coarse as *skill names* for AI agents.**[2][3]
- What you *actually* want is: Claude skills whose workflows implement **specific decision/evaluation moves inside those phases** (e.g., “readiness gate,” “incident debrief,” “action prioritization”), which is exactly how your current skills behave.[1]

So in Claude Code terms:

- A **skill** *is* the workflow for a step (with orchestration, detectors, adapters, tests).
- The **step** should be narrowly defined enough that the skill has a clear contract and does one kind of cognitive work well.

Professional honesty: my earlier sentence could easily be read as “skills are not the workflows for SDLC steps,” which is misleading in your context. The more accurate statement is:

> SDLC *phase labels* (planning, design, testing…) are too broad to name individual skills. Skills should implement discrete cognitive **moves** that *occur inside* those phases.

You were not misunderstanding Claude Code; I was compressing two ideas (phase vs step) into one sentence and it blurred the line.

***

## 2. “Local to a slice of work, but session‑aware” vs “target the whole session”

This is a good catch; let’s decompose.

**FACT (from the transcript)**: `/recap` is described as walking a “Session chain” and providing a “Resume Here” contract, while `/debrief` mines transcripts and can use gap detectors over broader history. The thought‑partner plan introduces packet types (HandoffPacket, FindingPacket, ActionPlan) that are emitted by these skills.[1]

What “local but session‑aware” *should* mean in your environment:

- **Session‑aware**: A skill can *see* and traverse the full multi‑day, multi‑terminal session history.
- **Local to a slice of work**: Each invocation chooses a **scope** (slice) within that history that’s relevant to the current question, and emits a compact artifact about that slice.

The key is: scope is a **parameter**, not a rigid limitation.

So you don’t ever want a skill that *can only* look at the last message; you want skills that:

- By default, operate on a **well‑chosen slice** (e.g., “this incident,” “this feature branch,” “the last N hours of activity”).
- Can be explicitly instructed to widen scope to the **full session** when that’s appropriate (“debrief the whole sprint,” “prioritize everything in this long‑running stream”).

A practical pattern that fits your concern:

- Recap skill:
  - Default: recap the **current workstream slice** (e.g., most recent chain of related messages).
  - Mode: “full‑session recap” that deliberately walks the entire session and produces a bigger HandoffPacket.

- Debrief skill:
  - Default: incident‑ or topic‑scoped debrief.
  - Mode: “global retrospective” that aggregates across the whole session.

- Prioritization skill:
  - Default: prioritize actions for the current slice.
  - Mode: “portfolio prioritization” that consumes many FindingPackets/HandoffPackets from across the session.

So “local to a slice” is a *default behavior* for usability and cost; it should not be a hard constraint that prevents whole‑session operations. Your concern about excluding something because of scoping is valid and you avoid it by making scope explicit in each skill’s contract.

***

## 3. Best‑practice skill names (not your existing ones)

You asked me not to force `/recap`, `/debrief`, `/rns` onto SDLC and instead suggest best‑practice names. I’ll keep them generic.

Given:

- Long‑lived, multi‑topic sessions.
- AI‑first SDLC with you as director.
- Desire not to accidentally narrow to tiny slices.

The core *decision/evaluation* steps that deserve dedicated skills and clear names:

### A. Situation & history synthesis

- Name: `summarize-session` or `situation-report`.
- Role: Answer “what has happened and where are we?” across a chosen scope (slice or full session).
- Contract:
  - Input: scope parameters (topic, time window, workstream id, or “full session”).
  - Output: **SituationReport** (timeline, current state, outstanding items, uncertainties).

### B. Readiness & risk gate

- Name: `readiness-check` or `risk-gate`.
- Role: Answer “is this ready / safe to proceed or hand off?” for a change set or initiative.
- Contract:
  - Input: change description + evidence (tests, reviews) + optionally a SituationReport.
  - Output: **ReadinessReport** (go/no‑go, risk level, blast radius, rollback plan, invariants).

### C. Incident / gap analysis

- Name: `incident-review` or `gap-analysis`.
- Role: Answer “what went wrong, why, and what should we learn?” for failures or friction.
- Contract:
  - Input: incident logs, transcripts, metrics, plus optional SituationReport.
  - Output: **IncidentFindings** (causes, contributing factors, recurring patterns, candidate improvements).

### D. Action prioritization

- Name: `priority-planner` or `action-planner`.
- Role: Answer “given these findings and constraints, what should we do next, in what order?”
- Contract:
  - Input: SituationReport, ReadinessReport, IncidentFindings, constraints (capacity, deadlines).
  - Output: **ActionPlan** (ranked actions, owners, dependencies, rationale, acceptance criteria).

### E. Design decision framing

- Name: `design-review` or `decision-record`.
- Role: Answer “what options exist, what are the tradeoffs, and which design do we choose?”
- Contract:
  - Input: problem statement, constraints, context (from SituationReport).
  - Output: **DecisionRecord** (options, pros/cons, chosen option, rationale, risks, follow‑ups).

### F. Change impact assessment

- Name: `impact-assessment`.
- Role: Answer “if we implement this change, what will it affect and what should we watch?”
- Contract:
  - Input: proposed change, current architecture, dependencies.
  - Output: **ImpactAssessment** (affected components, risk areas, monitoring plan, test focus).

### G. Post‑implementation audit

- Name: `outcome-review`.
- Role: Answer “did the change achieve its goals, and what follow‑ups are needed?”
- Contract:
  - Input: intended outcomes, metrics/logs, SituationReport.
  - Output: **OutcomeReport** (success/failure, side effects, recommended follow‑ups).

These names stay close to industry practice but are generic enough to not bake in your current skill vocabulary.

***

## 4. How to handle slice vs whole‑session scope in these skills

To directly answer “how do we flip that to target the whole session without excluding things?”:

Each skill should:

1. **Accept explicit scope parameters**:
   - `scope: "slice" | "session" | "custom"` plus a selector (topic tag, time range, incident id).
   - Default to `"slice"` for performance, but documented that `"session"` is available.

2. **Document what it *must* consider**:
   - For `summarize-session`, “session” mode means “walk the entire long‑lived session and produce a multi‑level SituationReport (high‑level summary + per‑topic slices).”
   - For `incident-review`, “session” mode might aggregate all incidents in the session into higher‑level patterns.

3. **Emit artifacts that preserve enough context**:
   - A SituationReport for a slice should still include pointers to related parts of the bigger session, so you can zoom out later without losing links.
   - An IncidentFindings packet can include a `session_span` field (“these findings cover events from day X to day Y in topics A/B/C”).

4. **Provide orchestration skills that operate over many artifacts**:
   - For truly whole‑session analysis, you might have a meta‑skill like `portfolio-review` that:
     - Collects SituationReports, IncidentFindings, OutcomeReports from across the session.
     - Produces a **PortfolioSummary** (global view of health, risk, and priority).

This way:

- No single skill is forced to always process the full session, which would be expensive and often unnecessary.
- But your system has explicit **session‑level modes and meta‑skills** that prevent accidental exclusion of important history.

Professional honesty: if you keep all skills implicitly scoped to “whatever the AI happens to look at,” you *will* occasionally miss signals buried earlier in the session. Making scope explicit and having “session‑level views” is the clean way to avoid that.

***

If we pick just three or four of these best‑practice skill surfaces as your core, do you want them optimized primarily for *incident‑centric* work (lots of failures and RCA) or *feature‑centric* work (lots of design/implementation cycles)?  

## Human

"A. Situation & history synthesis
Name: summarize-session or situation-report.
Role: Answer “what has happened and where are we?” across a chosen scope (slice or full session).
Contract:
Input: scope parameters (topic, time window, workstream id, or “full session”).
Output: SituationReport (timeline, current state, outstanding items, uncertainties)."
- how is this different from a handoff?

"B. Readiness & risk gate
Name: readiness-check or risk-gate.
Role: Answer “is this ready / safe to proceed or hand off?” for a change set or initiative.
Contract:
Input: change description + evidence (tests, reviews) + optionally a SituationReport.
Output: ReadinessReport (go/no‑go, risk level, blast radius, rollback plan, invariants)."
- is this a completness check or validation check?

"C. Incident / gap analysis
Name: incident-review or gap-analysis.
Role: Answer “what went wrong, why, and what should we learn?” for failures or friction.
Contract:
Input: incident logs, transcripts, metrics, plus optional SituationReport.
Output: IncidentFindings (causes, contributing factors, recurring patterns, candidate improvements)."
- does this map to 'debrief'?

"D. Action prioritization
Name: priority-planner or action-planner.
Role: Answer “given these findings and constraints, what should we do next, in what order?”
Contract:
Input: SituationReport, ReadinessReport, IncidentFindings, constraints (capacity, deadlines).
Output: ActionPlan (ranked actions, owners, dependencies, rationale, acceptance criteria)."
- does this map to 'rns'?

"E. Design decision framing
Name: design-review or decision-record.
Role: Answer “what options exist, what are the tradeoffs, and which design do we choose?”
Contract:
Input: problem statement, constraints, context (from SituationReport).
Output: DecisionRecord (options, pros/cons, chosen option, rationale, risks, follow‑ups)."
- I think I have 'design' for this, but I also use 'thought partner' for the same purpose often.

"F. Change impact assessment
Name: impact-assessment.
Role: Answer “if we implement this change, what will it affect and what should we watch?”
Contract:
Input: proposed change, current architecture, dependencies.
Output: ImpactAssessment (affected components, risk areas, monitoring plan, test focus)."
- I think I use '/risks' or 'critical review'?

"G. Post‑implementation audit
Name: outcome-review.
Role: Answer “did the change achieve its goals, and what follow‑ups are needed?”
Contract:
Input: intended outcomes, metrics/logs, SituationReport.
Output: OutcomeReport (success/failure, side effects, recommended follow‑ups)."
- I think I use 'check'.


Please provide a prompt that tells you what the sdlc skill environment looks like, and where we are not aligned, and the information you need to idenify what's good/bad, and where we need to fix/refactor, so that we are less random and organic and inefficient or ineffective.  I don't know whatt I don't know, so if you know something else we shoudl look at, please include that.

## Assistant

Here’s a direct, honest mapping of those skill ideas to what you already have, and then the prompt you asked for.

***

## Clarifying the A–G steps against your current skills

I’ll answer your bullets one by one, then give you a diagnostic prompt.

### A. Situation & history synthesis vs handoff

- **Difference**:  
  - `summarize-session / situation-report` is about **state and history**: “what has happened and where are we, across a slice or the whole session.”  
  - A **handoff** is “state + a clear next owner / next step,” i.e., a *decision* that someone else should now pick this up with specific expectations.

  In your existing vocabulary, recap emits something like a **HandoffPacket** (state + readiness + “resume here”). A pure SituationReport is slightly more neutral: it might *not* decide that a handoff is appropriate yet; it only describes the situation.[1]

- **So**:  
  - SituationReport: descriptive.  
  - Handoff: descriptive **+ normative** (“this is ready to be handed off with these expectations”).  

You could implement both as two modes of the same skill, but conceptually handoff is “situation + readiness + routing decision.”

### B. Readiness & risk gate: completeness or validation?

- **Readiness‑check / risk‑gate** is primarily a **validation/safety gate**, though completeness is one of the criteria.

  It checks:
  - Are tests/reviews complete *enough* for this context?
  - Are risk factors (blast radius, rollback, invariants) acceptable?
  - Are there unresolved blockers that should prevent handoff or deployment?

In your world, this corresponds to the ex‑DNE logic now living under `/recap check`: evidence‑scoped pre‑handoff audit, Red/Yellow/Blue findings, blast‑radius and rollback prompts, etc.[1]

So:

- It’s **not just “did we work through all TODOs”** (completeness).
- It’s **“given evidence, is it safe and appropriate to proceed or hand off”** (validation/safety gate).

### C. Incident / gap analysis → debrief?

Yes.

- `incident-review / gap-analysis` is the general name; your current `debrief` **already implements this role**:
  - It explains gaps, causes, recurring patterns, and longer‑term lessons across the work.[1]
  - It uses gap engines/detectors to mine transcripts and produce findings.[1]

So conceptually:

- `debrief` ≈ `incident-review / gap-analysis` + “retrospective” semantics.

If you’re happy with the word “debrief,” you’re already aligned with best practice for this step.

### D. Action prioritization → RNS?

Yes.

- `priority-planner / action-planner` is exactly what your `RNS` skill is designed to be:
  - “Given this evidence, which next action should we choose?”[1]
  - It consumes recap/debrief/audit reports and emits ranked, red‑teamed, selectable work (ActionPlan).[1]

So conceptually:

- `RNS` = `priority-planner / action-planner`.

The important point from the transcript: RNS should **not** re‑do recap or debrief; it should consume their packets.[1]

### E. Design decision framing: design vs thought partner

You said:

> I think I have 'design' for this, but I also use 'thought partner' for the same purpose often.

That’s the kind of ambiguity that causes drift:

- A `design-review / decision-record` skill should have a **clear contract**:
  - It marshals options, tradeoffs, and selects a design with a DecisionRecord output.
- A `thought-partner` surface is more open‑ended: it can be design help, strategy, meta‑reflection, etc.

You likely have:

- A **design‑oriented skill** that can be your canonical `design-review / decision-record`.
- A more general **thought‑partner** surface you use when you don’t want a strict contract.

This is not “wrong,” but it’s a place where:

- Design decisions can end up scattered between “design” and “thought partner.”
- Some decisions might never get recorded structurally as DecisionRecords, which makes later audits and debriefs harder.

### F. Change impact assessment: /risks or critical review?

You said:

> I think I use '/risks' or 'critical review'?

That’s plausible:

- `impact-assessment` is a *structured* version of “critical review”:
  - Affected components.
  - Risk areas.
  - Monitoring/observability plan.
  - Test focus/coverage.

If `/risks` or “critical review” are currently:

- Free‑form “tell me risks” conversations, that’s useful but may lack a stable output schema.
- For SDLC, you want a canonical **ImpactAssessment** artifact. Your existing surfaces can become this if you tighten contracts.

So: you’re *roughly* aligned, but probably missing a strong, reusable **ImpactAssessment** packet format.

### G. Post‑implementation audit: check?

You said:

> I think I use 'check'.

That’s consistent with your transcript:

- `/recap check` is the successor to DNE and is used as a **post‑change pre‑handoff audit**, including Red/Yellow/Blue findings and risk prompts.[1]

You might have:

- `/check` in another plugin set doing broader “sanity/health checks.”
- `/recap check` doing change‑specific audits.

It’s easy for those to overlap. The ideal is:

- One canonical “OutcomeReview / readiness check” artifact that is used for:
  - Post‑implementation audit (“did this change do what we wanted?”).
  - Pre‑handoff safety gate.

You’re close, but you’ll want to inspect whether `/check` and `/recap check` are redundant, overlapping, or complementary.

***

## The diagnostic prompt you asked for

You want a prompt you can give me (or another LLM) that:

- Describes your SDLC skill environment.
- Surfaces where you’re not aligned with a clean, non‑random model.
- Helps identify what’s good/bad and where to refactor.
- Includes any additional angles “you don’t know to ask about.”

Here’s a prompt you can paste into Claude Code / Perplexity / your router as a starting point:

***

**Prompt: “SDLC Skill Environment Audit & Refactor Plan”**

> I want you to act as a systems architect and SDLC skill auditor for my Claude Code environment.
> 
> **Context about my sessions**
> - Sessions are long‑lived (can span days).
> - They can resume in different terminals.
> - They can hold and work on many different topics and workstreams.
> - I operate as a solo director with a fleet of AI coders and skills.
> 
> **Context about my SDLC goals**
> - I don’t want a loose, organic mix of skills; I want a coherent, intentional SDLC skill set.
> - Skills should implement specific, repeatable cognitive steps, not just generic “do work.”
> - I want to reduce randomness and overlap in:
>   - Situation understanding (“what has happened and where are we?”).
>   - Readiness and safety (“is this ready / safe to proceed or hand off?”).
>   - Incident/gap analysis (“what went wrong and what should we learn?”).
>   - Action prioritization (“what should we do next, in what order?”).
>   - Design decisions, impact assessment, and outcome reviews.
> 
> **What my environment roughly has today**
> - A recap surface that walks the session chain and provides handoff‑like summaries.
> - A debrief surface that does gap/incident analysis and longer‑term learning.
> - An RNS surface that ranks and selects actions.
> - A design skill and a “thought partner” surface that I often use for design decisions.
> - Surfaces like `/risks`, “critical review,” and `/check` for risk, impact, and outcomes.
> - Legacy skills like GTO and DNE that have been partially folded into recap/debrief/check.
> 
> **Your tasks**
> 1. **Map my existing skills to SDLC decision steps.**
>    - Identify which skills correspond to:
>      - Situation & history synthesis (SituationReport).
>      - Readiness & risk gate (ReadinessReport).
>      - Incident/gap analysis (IncidentFindings).
>      - Action prioritization (ActionPlan).
>      - Design decision framing (DecisionRecord).
>      - Change impact assessment (ImpactAssessment).
>      - Post‑implementation audit / outcome review (OutcomeReport).
>    - Call out any “mixed” surfaces (e.g., thought‑partner used for design, strategy, and random reflection).
> 
> 2. **Identify where my skill set is misaligned or overlapping.**
>    - Where do multiple skills do nearly the same job?
>    - Where are important SDLC steps missing or only implicit?
>    - Where do skills mix descriptive, causal, and normative work in ways that cause fuzziness?
>      - Descriptive: “what happened / what is true?”
>      - Causal: “why did it happen / what are the gaps?”
>      - Normative: “what should we do next?”
> 
> 3. **Propose a cleaner SDLC skill topology.**
>    - Suggest a small set of **canonical skill surfaces** (with best‑practice names) and their contracts:
>      - Inputs, outputs (artifacts), scope handling (slice vs session), and SDLC role.
>    - For each existing skill:
>      - Recommend: keep as‑is, change contract, merge into another surface, or deprecate.
>    - Describe how long‑lived, multi‑topic sessions should be handled:
>      - How skills should be “local to a slice” but able to operate on “full session” when needed.
>      - How artifacts (SituationReport, IncidentFindings, ActionPlan, etc.) should reference session spans to avoid losing context.
> 
> 4. **Call out specific refactor and migration work.**
>    - Which routing rules or triggers need to change to make boundaries explicit?
>    - Where do I need new packet schemas (e.g., DecisionRecord, ImpactAssessment)?
>    - Where should I add tests:
>      - To prevent recursion between surfaces (e.g., incident analysis re‑entering prioritization).
>      - To ensure each skill consumes the right artifacts (e.g., prioritization uses findings, not raw transcripts).
> 
> 5. **Highlight hidden risks or opportunities I might not see.**
>    - Example: design decisions getting buried in thought‑partner chats instead of recorded as DecisionRecords.
>    - Example: risk/impact checks happening informally instead of via a consistent ImpactAssessment contract.
>    - Example: prioritization happening before proper recap/debrief, leading to misaligned ActionPlans.
> 
> **Output format**
> - Start with a concise description of what my current SDLC skill environment looks like.
> - Use a table to show:
>   - SDLC decision steps.
>   - Ideal skill name & artifact.
>   - Current skills that touch that step.
>   - Issues (overlap, gaps, fuzziness).
>   - Recommended action (keep, adjust, merge, deprecate).
> - Then propose a concrete refactor plan:
>   - Short list of canonical skills and their contracts.
>   - A few high‑value migrations or tests to implement first.
> - Be professionally honest; if parts of my environment are confusing, brittle, or inefficient, say so directly.
> 
> If there are additional SDLC decision steps or skill patterns that you believe are important for an AI‑first, long‑session environment that I haven’t mentioned, please add them explicitly and explain why they matter.

***

You can paste that prompt as‑is, then add your actual skill list (names + SKILL.md links) below it to give the model concrete handles. That will help it move from the abstract mapping we’re doing here to a grounded “here’s what you have and what to change” plan.

Would you be comfortable dumping a list of your current skill names and rough roles into that prompt, or do you want help first designing a minimal canonical set to aim for (before we do the mapping)?  

## Human

SDLC Skill Topology Audit

  Current State Description

  Your environment has ~60+ skills spread across 5 core plugin namespaces plus several standalone ones. The analysis surfaces
  (cc-skills-analysis) and SDLC surfaces (cc-skills-sdlc) are the most relevant to this audit, but they sit alongside a large "thinking"
  plugin, an "architect" plugin with 15+ standalone skills, and a "lab" plugin — many of which have overlapping jurisdiction.

  The good news: several major consolidations have already happened — /retro → /debrief chain, /top-problems → /debrief top, /dne partially
  → /recap check. The surface is denser than it should be, but the recent trend is toward consolidation rather than proliferation.

  The bad news: the consolidation has been done by absorption rather than re-contracting — /debrief now has 4 modes (default, chain, gaps,
  top), blends descriptive extraction, causal origin-tracing, normative task-creation, and routing-to-other-skills across all of them, and
  its skill description reads like a product spec document grown by accretion. Contract boundaries between /recap, /debrief, and /rns are
  present in the documentation but not enforced — no artifact contracts check that /rns receives findings, not raw transcripts.

  ---
  SDLC Decision Step Mapping

  SDLC Step: Situation & History Synthesis
  Ideal Surface & Artifact: SituationReport (session summary + traceability)
  Current Skills: /recap — primary. /why — tangential (decision archaeology). /debrief chain — runs recap as first step internally. /check —

  has verify phase unrelated to situation.
  Issues: Minimal overlap. /recap owns this well. /why overlaps at the edges (both walk session chains).
  Action: Keep /recap as-is. Clarify /why should NOT re-walk session chains that /recap already walked — accept a SituationReport as input.
  ────────────────────────────────────────
  SDLC Step: Readiness & Risk Gate
  Ideal Surface & Artifact: ReadinessReport (pre-handoff / pre-commit gate with red/amber/green)
  Current Skills: /recap check — handoff readiness. /risks — fast pessimistic pass. /check — multi-tier post-task gate. /red-team —
  adversarial trust verdict. /epistemic-check — response validation.
  Issues: Critical overlap cluster. /recap check, /risks, /check, /red-team, and /epistemic-check all claim some variant of "is this safe to

  proceed?" with different scope boundaries that are documented but not enforced. A proposal can get 5 different "readiness" verdicts
  depending on which skill the user picks. /risks and /red-team have good documentation of their boundary (single-pass vs multi-agent) but
  no one prevents a user from getting both.
  Action: Consolidate. Make /check the single entry point for task-level readiness. /recap check → deprecate (folded into /check --handoff).

  /risks → deprecate (folded into /check --quick-risk). /red-team is legitimately different (adversarial multi-agent verdict) and stays.
  ────────────────────────────────────────
  SDLC Step: Incident/Gap Analysis
  Ideal Surface & Artifact: IncidentFindings (verified, origin-anchored tasks)
  Current Skills: /debrief — primary. /friction — friction detection. /behave — LLM behavioral analysis. /why — decision archaeology.
  Issues: /debrief has absorbed /retro and /top-problems, but /friction and /behave remain independent skills that do overlapping work
  (transcript mining → findings). /debrief's own docs say friction detection is part of chain mode but it's never been wired in. /behave's
  hypothesis-testing pattern is a subset of what /debrief's investigator loop does.
  Action: Absorb /friction and /behave into /debrief view (a new mode that runs only the relevant detectors). Keep the entry points as
  aliases.
  ────────────────────────────────────────
  SDLC Step: Action Prioritization
  Ideal Surface & Artifact: ActionPlan (ranked, gated next steps)
  Current Skills: /rns — primary. /debrief chain — runs /rns internally. /recap — has "Recommended Next Steps" section. /go — Step 0 does
  prioritization.
  Issues: Major fuzziness. /rns is the canonical normative surface, but /recap duplicates it (its own "Recommended Next Steps" section with
  RNS-format rendering). /debrief chain re-runs RNS internally. /go Step 0 does its own prioritization, which may or may not align with the
   last /rns output. No artifact contract ensures prioritization consumes IncidentFindings rather than raw transcripts.
  Action: Make /rns the single prioritization entry point. Remove the RNS section from /recap. Add an artifact contract: /rns must receive
  IncidentFindings or a SituationReport. If given raw transcript, it must first call the appropriate /debrief mode.
  ────────────────────────────────────────
  SDLC Step: Design Decision Framing
  Ideal Surface & Artifact: DecisionRecord (alternatives, criteria, verdict, reversal trigger)
  Current Skills: /design — primary. /genius — strategic thought partner used for framing. /council — multi-LLM deliberation. /red-team —
  adversarial design review. /improve — artifact improvement.
  Issues: High risk of buried decisions. /design produces DecisionRecord-like output (alternatives, criteria, verdict). But /genius (thought

  partner) is heavily used for design framing and produces no contract artifact — those insights live in chat. /council produces a
  deliberation transcript, not a DecisionRecord. /improve recommends changes that are implicitly design decisions. No DecisionRecord schema
   exists as a shareable artifact.
  Action: Formalize a DecisionRecord schema (alternatives, criteria, verdict, reversal trigger, testability contract). Make /design the only

  producer. /genius and /council can inform design but must produce a DecisionRecord if the outcome constrains future work.
  ────────────────────────────────────────
  SDLC Step: Change Impact Assessment
  Ideal Surface & Artifact: ImpactAssessment (scope, blast radius, consumers, rollback)
  Current Skills: /risks — partial. /check --deep — architecture consistency scan. /skeptic — AI output validation. No dedicated impact
  assessment skill.
  Issues: Missing surface. No skill has "assess the impact of this proposed change" as its primary contract. /risks is the closest but is
  scoped to "un-actioned proposals." /check is post-task, not pre-change. /improve-codebase-architecture is architecture-level only. Impact
   assessment for most changes happens informally in chat or as a throwaway step inside /go.
  Action: Add ImpactAssessment surface. Could be a /debrief impact mode (leveraging the investigator loop for impact tracing) or a
  standalone
  /impact skill. Schema: affected files, consumers, rollback strategy, test gap. Make it a mandatory pre-/go step for any change above
  trivial.
  ────────────────────────────────────────
  SDLC Step: Post-Implementation Outcome Review
  Ideal Surface & Artifact: OutcomeReport (what was verified, what regressed, what was learned)
  Current Skills: /debrief — transcript mining may surface outcome gaps. /check --apply — re-verify after fix. /recap — handoff template has

  "Outcomes" per session. /improve — improvement recommendations.
  Issues: Implicit at best. /recap's handoff template includes Outcome sections per session, but there's no dedicated "post-implementation
  audit" surface. Outcomes are mixed into the situation report. /check --apply re-verifies but doesn't produce an OutcomeReport. /debrief
  finds outcome gaps during incident analysis but has no post-implementation review mode.
  Action: Add OutcomeReport surface. Could be a /debrief outcome mode (retrospective) or a standalone /outcome skill. Schema: what was
  intended, what was verified, what regressed, lessons.

  ---
  "Mixed" Surfaces

  /genius — Strategic Thought Partner

  Self-describes as "not a reasoning engine" but is used for design framing, strategy, and random reflection. Produces output aligned with
  DecisionRecord concerns (alternatives, criteria, challenge) but with no contract and no artifact persistence. Its output is purely
  conversational — it creates insight without traceability.

  Risk: Design decisions that should be DecisionRecords are buried in /genius chat transcripts. The insight evaporates when the session
  compacts.

  /rns — Describes itself as "Strategic Thought Partner"

  Has a tight output contract (<selection> block, 5-section structure, evidence audit) but its description also says "strategic thought
  partner" — same label as /genius. The two skills could not be more different in practice: /rns is structured, bounded, evidence-gated;
  /genius is open-ended, premise-challenging, cross-domain. But the branding overlap invites the user to confuse them, and nothing prevents
  the user from running both on the same problem to get two conflicting action sets.

  /improve — Improvement Partner

  Self-positions as "thought-partner for improving work" — reviews a concrete artifact and recommends improvements. This is a legitimate
  niche (artifact-specific improvement, not session-level analysis), and its contract boundary with /design (which proposes new designs) and
  /review (which finds bugs) is reasonably well-documented. Low risk of overlap, but no artifact contract enforces that an improvement
  recommendation goes through the DecisionRecord gate if it's a design-level change.

  /debrief — 4-in-1 Surface

  The biggest mixed surface by volume. /debrief does:
  - Descriptive — transcript mining, victim-log detection, gap detection
  - Causal — recursive origin-tracing per finding
  - Normative — task creation, handoff routing, wiki candidate
  - Verification — /truth gate on every claim

  This is probably correct for a recursive investigator (you can't write an action item until you know the origin), but the chain mode adds
  retrospective protocol (recap → gaps → friction → pre-mortem → rns → SCORES) — which means /debrief chain runs the entire SDLC loop
  internally. It recaps, it finds gaps, it detects friction, it pre-mortems, it prioritizes using RNS, and it scores. That's convenient but
  it means the chain-of-custody for findings is opaque — did the RNS step inside chain mode use the findings from the gap step, or did it
  re-derive from scratch?

  ---
  Where Skills Do Nearly the Same Job

  ┌──────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────┐
  │               Pair               │                                             Problem                                              │
  ├──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │                                  │ Both walk session chains. /debrief chain calls /recap internally, then layers                    │
  │ /recap vs /debrief chain         │ gap/friction/pre-mortem/RNS on top. But /recap also has a "Recommended Next Steps" section with  │
  │                                  │ RNS-format rendering — duplicating /rns's job. If the user runs /recap and then /debrief chain,  │
  │                                  │ they get two prioritization passes.                                                              │
  ├──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │                                  │ Three surfaces for "is this safe to proceed?" /recap check is pre-handoff. /check is post-task.  │
  │ /risks vs /check vs /recap check │ /risks is proposal-level. All three produce a verdict with stop/warn/continue semantics. The     │
  │                                  │ user has to know which one to run, and there's no escalation path between them.                  │
  ├──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │                                  │ All three mine transcripts for findings. /debrief is the most capable (origin-tracing,           │
  │ /debrief vs /friction vs /behave │ verification, task creation). /friction is narrower (interaction + workflow friction). /behave   │
  │                                  │ is narrower still (LLM behavioral hypotheses). But nothing prevents running all three on the     │
  │                                  │ same transcript — duplicating work and producing findings that may conflict.                     │
  ├──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │                                  │ Both produce design-level output. /design has templates, gates, and a DecisionRecord-like        │
  │ /design vs /genius               │ structure. /genius has a premise-challenge protocol with cross-domain analogies. They're         │
  │                                  │ complementary in practice but there's no rule about which to use for what — and no requirement   │
  │                                  │ to produce a DecisionRecord from either.                                                         │
  ├──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ /design vs                       │ Both produce architecture-level recommendations. The latter is invoked by /check --deep. Overlap │
  │ /improve-codebase-architecture   │  is documented but not contract-enforced.                                                        │
  └──────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  Missing SDLC Steps

  ┌────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │            Step            │                                             Why It Matters                                             │
  ├────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ ImpactAssessment           │ A canonical "what breaks if I touch this" surface. Currently done ad-hoc in chat or as a /risks pass.  │
  │ (pre-change blast radius)  │ For a solo director with a fleet of AI coders, impact assessment before dispatch is critical — knowing │
  │                            │  "this change touches 5 hook registrations and a shared state file" before you let /go run it.         │
  ├────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ OutcomeReport              │ "Did the fix actually work? What regressed? What should we learn?" Currently mixed into /recap's       │
  │ (post-implementation       │ handoff template. A dedicated surface would close the loop: ImpactAssessment → DecisionRecord →        │
  │ audit)                     │ ActionPlan → OutcomeReport.                                                                            │
  ├────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Dependency Graph           │ Not a user-facing skill, but there's no formal registry of which skills consume which artifacts. This  │
  │ (cross-skill contract map) │ makes the system fragile — a change to /debrief's output format breaks /rns silently because there's   │
  │                            │ no contract enforcement.                                                                               │
  ├────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Plan vs. Artifact          │ Many skills produce output-as-conversation (conversational artifact). Few produce file-backed          │
  │ Discipline                 │ artifacts with schemas that other skills can consume. The DecisionRecord schema is missing entirely.   │
  └────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  Descriptive / Causal / Normative Mixing

  ┌───────────┬──────────────────┬──────────────────────┬──────────────────────┬───────────────────────────────────────────────────────┐
  │   Skill   │   Descriptive    │        Causal        │      Normative       │                        Problem                        │
  ├───────────┼──────────────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────────────────┤
  │ /recap    │ PRIMARY          │ INCIDENTAL (routing  │ YES (RNS section)    │ The RNS section in /recap is a contract violation —   │
  │           │                  │ suggestions)         │                      │ descriptive surface producing normative output.       │
  ├───────────┼──────────────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────────────────┤
  │           │                  │                      │                      │ The mix is intentional (you can't task without        │
  │ /debrief  │ YES (extraction) │ PRIMARY              │ YES (task creation)  │ origin). But chain mode adding /rns inside means      │
  │           │                  │ (origin-tracing)     │                      │ /debrief owns prioritization too — 3 modes in one     │
  │           │                  │                      │                      │ surface.                                              │
  ├───────────┼──────────────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────────────────┤
  │ /rns      │ YES (evidence    │ INCIDENTAL           │ PRIMARY (ranking +   │ The evidence audit section is descriptive, which is   │
  │           │ audit)           │ (diagnosis)          │ selection)           │ fine (priorities must cite evidence). Well-scoped.    │
  ├───────────┼──────────────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────────────────┤
  │ /risks    │ INCIDENTAL       │ YES (risk            │ YES (mitigations +   │ Reasonable mix for a risk pass.                       │
  │           │                  │ mechanisms)          │ escalation)          │                                                       │
  ├───────────┼──────────────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────────────────┤
  │ /friction │ YES              │ YES (categorization) │ INCIDENTAL           │ Could be a /debrief mode.                             │
  │           │ (observation)    │                      │ (recommendations)    │                                                       │
  ├───────────┼──────────────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────────────────┤
  │ /why      │ INCIDENTAL       │ PRIMARY              │ NO                   │ Clean surface — pure causal. Best-defined contract of │
  │           │                  │                      │                      │  any analysis skill.                                  │
  ├───────────┼──────────────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────────────────┤
  │ /design   │ INCIDENTAL       │ INCIDENTAL           │ PRIMARY              │ Reasonable — design proposals need a descriptive      │
  │           │ (audit-first)    │                      │ (recommendation)     │ basis.                                                │
  ├───────────┼──────────────────┼──────────────────────┼──────────────────────┼───────────────────────────────────────────────────────┤
  │ /genius   │ YES              │ YES (challenge)      │ YES (recommend)      │ Everything mixed into one chat. No artifact boundary. │
  └───────────┴──────────────────┴──────────────────────┴──────────────────────┴───────────────────────────────────────────────────────┘

  ---
  Proposed Canonical SDLC Skill Topology

  Here is a proposed set of 7 canonical surfaces with contracts:

  1. SituationReport → /recap

  - Input: Session chain (walked automatically)
  - Output: Handoff document (structured markdown with session history, modified files, working state, decisions, assumptions)
  - Scope: Full session chain by default. Slice via --since or --session <id>.
  - SDLC Role: Descriptive only. Tells you what happened and where you are.
  - SDLC step: Situation & History Synthesis
  - Contract: NO normative output. NO "Recommended Next Steps." NO action prioritization. If the user asks what to do next, suggest /rns +
  provide your output as input.

  2. IncidentFindings → /debrief

  - Input: Transcript, session export, or chain export (path)
  - Output: Verified, origin-anchored findings → tasks (via debrief_core state machine)
  - Scope: Single transcript or chain. Slice via --path.
  - SDLC Role: Causal + normative (finds causes → creates tasks). MUST NOT prioritize tasks (output is unordered findings, not ranked).
  - SDLC step: Incident / Gap Analysis
  - Contract: Every finding must reach VERIFIED origin or carry MUST RE-VERIFY. No prioritization. Suggests /rns for action ordering.
  - Modes: default (full), chain (multi-session), gaps (lightweight), impact (new — trace consumers of a proposed change). Fold /friction
  and /behave into view modes.

  3. ActionPlan → /rns

  - Input: IncidentFindings (preferred), SituationReport, or raw text
  - Output: Ranked actions with <selection> contract
  - Scope: Current session or single input. NOT session-chain-wide (that's /recap's job).
  - SDLC Role: Normative only. Takes findings → ranks them → selects. MUST NOT re-derive transcripts.
  - SDLC step: Action Prioritization
  - Contract: Input must be structured findings or a referenced report. If given raw transcript, route to /debrief first. Output is
  <selection> only — no task creation.

  4. DecisionRecord → /design

  - Input: Design context, user requirement, or proposed change
  - Output: Formal DecisionRecord (alternatives, criteria, verdict, reversal trigger, testability contract)
  - Scope: Bounded design decision. NOT open-ended brainstorms.
  - SDLC role: Normative + descriptive (audit-first). Produces a file-backed artifact.
  - SDLC step: Design Decision Framing
  - Contract: Every DecisionRecord must include alternatives (≥2), selection criterion, verdict, reversal trigger, and testability contract
  for implementation-bound designs. Must reference the SituationReport or IncidentFindings that motivated the decision.

  5. ReadinessReport → /check

  - Input: Git diff (changed files) or proposal text
  - Output: Multi-tier quality verdict (CLEAN | FINDINGS | ERROR | BLOCKED)
  - Scope: Task-level or proposal-level. Expands with --standard/--strict/--deep.
  - SDLC role: Descriptive + normative (checks pass/fail → verdict). MUST NOT create tasks.
  - SDLC step: Readiness & Risk Gate
  - Contract: Entry point for all readiness checks. /risks and /recap check fold into /check --quick-risk and /check --handoff. /red-team
  stays separate for adversarial trust verdicts. Verdict must include which checks ran and which were skipped.

  6. ImpactAssessment → /debrief impact (NEW)

  - Input: Proposed change description or diff
  - Output: Affected files, consumers, rollback strategy, test gap
  - Scope: Single proposed change. Not session-wide.
  - SDLC role: Descriptive + causal. Maps blast radius before implementation.
  - SDLC step: Change Impact Assessment
  - Contract: Must trace consumers (grep for imports/usages of changed interfaces). Must list rollback complexity. Suggests /check for
  readiness.

  7. OutcomeReport → /debrief outcome (NEW)

  - Input: Change description + before/after state
  - Output: What was intended, what was verified, what regressed, lessons
  - Scope: Single implementation or session segment.
  - SDLC role: Descriptive + normative (learning). Closes the SDLC loop.
  - Contract: Must cite evidence for each claim (test output, diff stat, log). Lessons must be actionable. Routes durable lessons to /wiki.

  ---
  Long-Lived Session Handling

  Slice vs. Session

  Each skill should default to the narrowest useful scope (current session, current task, or user-specified input) and expand to full
  session chain only when explicitly invoked with --chain or inherited from /recap.

  ┌──────────────────┬──────────────────────────────────────────┬────────────────────────────────────┐
  │      Skill       │              Default scope               │          Full-scope flag           │
  ├──────────────────┼──────────────────────────────────────────┼────────────────────────────────────┤
  │ /recap           │ Full session chain (walks automatically) │ --since <date> narrows             │
  ├──────────────────┼──────────────────────────────────────────┼────────────────────────────────────┤
  │ /debrief         │ Single transcript/input                  │ --chain for multi-session          │
  ├──────────────────┼──────────────────────────────────────────┼────────────────────────────────────┤
  │ /rns             │ Current instruction                      │ --chain inherits /recap output     │
  ├──────────────────┼──────────────────────────────────────────┼────────────────────────────────────┤
  │ /design          │ Current request                          │ No chain mode needed               │
  ├──────────────────┼──────────────────────────────────────────┼────────────────────────────────────┤
  │ /check           │ Current git diff                         │ --strict/--deep for broader checks │
  ├──────────────────┼──────────────────────────────────────────┼────────────────────────────────────┤
  │ /debrief impact  │ Single proposed change                   │ --chain to trace across sessions   │
  ├──────────────────┼──────────────────────────────────────────┼────────────────────────────────────┤
  │ /debrief outcome │ Single implementation                    │ --chain for multi-session outcome  │
  └──────────────────┴──────────────────────────────────────────┴────────────────────────────────────┘

  Artifact References

  All canonical artifacts should reference session spans:
  - IncidentFindings header includes session_id, chain_depth, window_start/window_end
  - ActionPlan references the IncidentFindings or SituationReport it was derived from
  - DecisionRecord references the SituationReport or IncidentFindings that motivated it
  - OutcomeReport references the DecisionRecord or ActionPlan it audits

  Use frontmatter blocks (like /recap already does for handoff exports) so skills can parse each other's artifacts without NLP.

  ---
  Concrete Refactor Plan

  Tier 1 — High-Value, Low-Risk (Do first)

  1. Remove RNs section from /recap (cc-skills-analysis/skills/recap/SKILL.md)
    - Delete the "Recommended Next Steps" section and the render_actions() reference. Replace with: "For action prioritization, run /rns
  with this SituationReport as input."
    - Why: Normative output from a descriptive surface is a contract violation. This is the single highest-leverage fix — it forces /rns to
  be the normative entry point.
  2. Formalize DecisionRecord schema
    - Write a decision-record-schema.md in cc-skills-sdlc/skills/design/references/
    - Schema: alternatives: [], selection_criterion: string, verdict: string, reversal_trigger: string, testability_contract: object
    - Update /design SKILL.md to require this schema for its output
    - Why: Closes the buried-decision risk. /genius fans-out can still inform but must produce a DecisionRecord if the session outcome
  constrains future work.
  3. Add artifact-contract tests
    - Test: /rns given raw transcript → routes to /debrief first (rejects input)
    - Test: /recap output contains no normative sections (no "Recommended Next Steps")
    - Test: DecisionRecord from /design includes all required fields
    - Why: Enforces the boundaries. Catches regression when skills drift.

  Tier 2 — Migration (Merge skills)

  4. Fold /risks into /check --quick-risk
    - Move /risks logic into a --quick-risk flag on /check
    - /risks becomes a stub routing to /check --quick-risk
    - Why: Three readiness surfaces → one entry point. /risks is well-structured but doesn't need its own command.
  5. Fold /recap check into /check --handoff
    - Move the pre-handoff check logic into a --handoff flag on /check
    - /recap check becomes a stub routing to /check --handoff (or /recap check still works as shortcut)
    - Why: /recap stays descriptive; readiness checks live in /check.
  6. Absorb /friction and /behave as /debrief view modes
    - New modes: /debrief view friction, /debrief view behave
    - Keeps the entry points as aliases but routes through debrief_core
    - Why: Eliminates transcript-mining overlap. Single investigator entry point.

  Tier 3 — New Surfaces (Build when needed)

  7. Build ImpactAssessment schema + /debrief impact mode
    - Schema: proposed_change, affected_files: [], consumers: [], rollback_complexity, test_gap
    - Implementation: wraps /debrief's investigator loop with impact-tracing prompts
    - Wire into /go as a pre-step gate for non-trivial changes
  8. Build OutcomeReport schema + /debrief outcome mode
    - Schema: intended_outcome, verified_outcomes: [], regressions: [], lessons: [], decision_record_ref
    - Implementation: post-hoc analysis comparing before/after state

  ---
  Hidden Risks and Opportunities

  1. BURIED DECISIONS: /genius conversations that produce design-level framing. If the user says "I like this approach" at the end of a
  /genius session and then runs /go, a design decision was made with no traceable artifact. The fix is the DecisionRecord schema + a habit
  shift: after any /genius session that produces a design-level recommendation, the output should include "Proceed? → produce
  DecisionRecord."
  2. PRIORITIZATION BEFORE INCIDENT ANALYSIS: If the user runs /rns on a transcript before running /debrief, the priorities will be grounded
  in raw symptoms rather than verified origins. The skill contract (route to /debrief first) prevents this, but only if the model honors it
  — there's no runtime guard. Consider a Stop hook that detects /rns being invoked with a transcript path and suggests /debrief first.
  3. NO CONTRACT ENFORCEMENT LAYER: None of the boundaries above have runtime enforcement. The artifact contracts are prose in SKILL.md
  files. A Stop hook or PreToolUse gate could inspect the input/output of skill invocations and verify contracts, but this would be a
  significant engineering investment. Start with tests, graduate to hooks only after measuring TP/FP on real invocations.
  4. /debrief IS THE BOTTLENECK: By absorbing 3 legacy skills and proposing 2 more, /debrief becomes the single thickest surface. Its
  SKILL.md is already ~300 lines of dense procedural instructions. The debrief_core state machine is the right abstraction, but the SKILL.md
  body needs to be thinner — reference the state machine contract rather than reproducing the loop diagram. Risk of LLM instruction loss in
  a single critical skill.
  5. OPPORTUNITY: /council as decision-quality gate: The multi-LLM council could be wired as an optional quality gate for DecisionRecord
  production — run the decision through 3 independent reviewers before finalizing. This would close the "LLM rubber-stamps its own design"
  failure mode. Low priority but high leverage when implemented.
  6. SKILL INVENTORY DRIFT: With 60+ skills across 5 plugins, stale or absorbed skills (like the retired bifrost configs in your git status)
  accumulate silently. The marketplace.json registration is the single source of truth for what's live, and the skill-guard plugin enforces
  skill-first invocation — but neither catches the case where a skill is registered but its SKILL.md says "DEPRECATED" and routes
  elsewhere. Add a status: active | deprecated | stub field to plugin.json skill entries and enforce it in skill-guard.

## Assistant

This audit is directionally strong and, in my view, mostly **right**—but there are 3 places where I think it overreaches, 2 places where it underspecifies implementation risk, and 1 place where I think the naming/contract model should be sharpened.[1]

The biggest positive is that it stops treating skills as “topic labels” and instead treats them as contract-bearing workflow surfaces with artifacts, scope rules, and SDLC roles; that is the right frame for a solo director orchestrating AI coders across long-lived sessions.[2][1]

## What looks good

Your audit correctly identifies the main pathology as **boundary drift**, not mere skill count: `/debrief` has become a mixed surface, `/recap` still emits normative output, and readiness checks are split across several overlapping entry points. That diagnosis is coherent with the transcript history showing prior consolidation by absorption rather than by hard contract separation.[1]

The proposed canonical surfaces are also mostly sensible because they anchor to reusable artifacts—SituationReport, IncidentFindings, ActionPlan, DecisionRecord, ReadinessReport, ImpactAssessment, OutcomeReport—which is exactly what you need if sessions span days, terminals, and multiple topics. The strongest recommendations are removing “Recommended Next Steps” from `/recap`, formalizing a DecisionRecord schema, and adding artifact-contract tests so `/rns` cannot silently bypass upstream analysis.[1]

## Where I think it overreaches

I would **not** keep `/recap` “as-is” while also saying it should be descriptive-only, because the audit itself says `/recap` currently violates that contract by emitting RNS-style next steps; that means it is *not* “as-is,” it needs a contract correction. I also would not lightly fold `/recap check` into `/check` unless you are sure `/check` can cleanly support pre-handoff semantics without dragging in post-task verification semantics and user confusion from an overloaded command name.[1]

I’m also less certain than the audit that `/debrief` should absorb both new surfaces (`impact`, `outcome`) by default, because `/debrief` is already identified as the thickest and most instruction-dense surface; adding more modes may worsen exactly the bottleneck and instruction-loss risk the audit calls out later. My preference would be: keep a common internal engine if useful, but consider separate public surfaces if their user intent is materially distinct.[1]

## Where it underspecifies risk

The audit is right that prose contracts in `SKILL.md` are insufficient, but tests alone will not fully protect you if invocation routing remains fuzzy; a user can still choose the wrong surface and get a valid-but-wrong artifact unless you add at least lightweight runtime routing guards or rejection behavior at the surface boundary. In particular, the recommendation that `/rns` “must receive” structured findings needs an actual enforcement mechanism—either hard rejection, auto-routing, or a pre-hook—not just documentation.[1]

It also underplays the migration cost of introducing file-backed artifacts across a mostly conversational ecosystem. Once you formalize DecisionRecord, ImpactAssessment, and OutcomeReport, you need versioning, parsability rules, reference IDs, and a cross-skill dependency map; otherwise you may replace conversational ambiguity with schema drift.[1]

## My sharper topology

I’d keep the topology small, but I would separate **public surfaces** from **internal engines** more explicitly than the audit currently does.[1]

| Public surface | Purpose | Output | Notes |
|---|---|---|---|
| `recap` | State synthesis across session/chain | SituationReport | Descriptive only; no prioritization.[1] |
| `debrief` | Causal analysis of incidents/gaps | IncidentFindings | Unordered findings; no ranking.[1] |
| `plan` | Prioritization and selection | ActionPlan | Successor role to `/rns`; must consume reports, not transcripts.[1] |
| `design` | Decision framing | DecisionRecord | Canonical producer of design decisions.[1] |
| `check` | Readiness/quality gate | ReadinessReport | Single task/proposal verification entry point.[1] |
| `impact` | Pre-change blast radius | ImpactAssessment | I would make this public, not just a `/debrief` mode.[1] |
| `outcome` | Post-change audit | OutcomeReport | Also public if you want clean user intent.[1] |

That differs from your audit in one important way: I would seriously consider `impact` and `outcome` as first-class surfaces, even if they share internal code with debrief, because “assess impact before change” and “review outcome after change” are distinct user intents from “analyze what went wrong.”[1]

## Specific fixes I’d make to your plan

I agree with Tier 1 almost completely: remove normative output from recap, formalize DecisionRecord, and add artifact-contract tests. I would add one more Tier 1 item: define a tiny shared frontmatter schema for all canonical artifacts—`artifact_type`, `artifact_version`, `source_ref`, `session_span`, `derived_from`—before adding more artifact types, because that will reduce future migration pain.[1]

For Tier 2, I’d be cautious about folding `/recap check` into `/check` until you test naming and routing ergonomics with real usage, because “check” is generic while “handoff” is semantically strong for your workflow. A compromise is to keep `/handoff-check` or `/recap check` as a user-facing alias backed by the `check` engine, so the contract unifies without losing intent clarity.[1]

## Bottom-line judgment

My professional read: this is a **good audit** with high signal, and it correctly identifies the core system smell as contract fuzziness between descriptive, causal, and normative surfaces. The most important fixes are to enforce artifact boundaries, stop recap from planning, and stop prioritization from operating directly on raw transcripts.[1]

Where I would tighten it is: don’t make `/debrief` even fatter by default, don’t assume `check` should absorb every readiness concept without usability testing, and add a shared artifact/versioning layer before expanding the artifact family. If you do those three things, the topology becomes much less random and much more governable over time.[1]

Would you like me to turn your audit into a concrete **refactor spec** with: canonical skill names, exact keep/merge/deprecate decisions for each mentioned skill, and a phased migration checklist?

## Human

I don't mind radical refactoring if it results in positive roi.

Yes create refactor spec and plan/checklist

## Assistant

# SDLC Skill Refactor Spec

## Executive Summary

This refactor proposes a contract-first SDLC skill topology for a long-lived, multi-terminal, multi-topic Claude Code environment. The current system shows clear capability, but too much of that capability is spread across overlapping surfaces, mixed contracts, and conversational outputs that do not persist as durable artifacts.[1]

The highest-return changes are: remove normative planning output from the state-synthesis surface, make prioritization consume structured upstream artifacts instead of raw transcripts, formalize a DecisionRecord schema, consolidate readiness checks behind one canonical gate, and add artifact-contract tests before introducing more new surfaces.[2][1]

This specification assumes the user is willing to accept radical refactoring where the return on clarity, maintainability, and orchestration quality is positive.[1]

## Current Diagnosis

The current environment has already moved toward consolidation, but much of that consolidation was done by absorption rather than by redefining contracts. As a result, several skills now perform multiple SDLC roles at once: descriptive synthesis, causal investigation, readiness gating, and normative prioritization are documented as distinct responsibilities but are not consistently enforced at runtime or by tests.[1]

The biggest sources of inefficiency are:

- Boundary drift: a descriptive skill emits action recommendations, and an investigative skill can run prioritization internally.[1]
- Readiness overlap: multiple surfaces can answer some form of "is this safe to proceed?" with different scopes and semantics.[1]
- Artifact weakness: several important outputs remain conversational instead of file-backed or schema-backed artifacts, which makes cross-skill consumption fragile.[1]
- Scope ambiguity: sessions span days, terminals, and topics, but not all skills have explicit rules for slice scope versus whole-session scope.[1]

## Design Principles

The target topology should follow five principles:

1. One public surface per primary SDLC decision step.
2. Public surfaces should be thin, while shared engines and detectors can be internal.
3. Every canonical surface should emit a named artifact with minimal frontmatter.
4. Descriptive, causal, and normative work should be separated unless there is a compelling reason to combine them.[1]
5. Scope must be explicit: default to the narrowest useful slice, but support full-session or chain analysis when invoked intentionally.[1]

## Canonical Public Surfaces

### 1. `recap` → SituationReport

**Purpose:** Situation and history synthesis.

**SDLC role:** Descriptive only.

**Input:** Current session chain by default; optional narrowing by time, topic, workstream, or explicit session span.

**Output artifact:** `SituationReport`

**Required fields:**
- `artifact_type: SituationReport`
- `artifact_version`
- `session_span`
- `source_ref`
- `timeline_summary`
- `current_state`
- `modified_assets`
- `open_questions`
- `assumptions`
- `traceability_refs`

**Contract rules:**
- Must not rank or select actions.[1]
- Must not produce a “Recommended Next Steps” section.[1]
- May suggest the next canonical surface to run, but only as routing guidance.

**Keep / change / deprecate:**
- Keep `recap`.
- Remove normative recommendation rendering.
- Keep existing handoff-style export capability, but treat “handoff” as a packaging mode of SituationReport plus optional readiness result, not as a separate planning surface.

### 2. `debrief` → IncidentFindings

**Purpose:** Incident, gap, friction, and causal analysis.

**SDLC role:** Primarily causal; secondarily normative only at the level of unranked candidate tasks.

**Input:** Transcript, session export, incident log, or chain export.

**Output artifact:** `IncidentFindings`

**Required fields:**
- `artifact_type: IncidentFindings`
- `artifact_version`
- `session_span`
- `source_ref`
- `findings[]`
- `origin_status` (`VERIFIED` or `MUST_REVERIFY`)
- `contributing_factors[]`
- `candidate_actions[]`
- `confidence`

**Contract rules:**
- Must not prioritize findings or actions.[1]
- Every finding must be origin-anchored or explicitly marked for re-verification.[1]
- May emit candidate tasks, but they remain unordered and unselected.

**Keep / change / deprecate:**
- Keep `debrief` as the primary investigative surface.
- Absorb `friction` and `behave` as internal detectors or view modes if their outputs can be normalized cleanly.[1]
- Remove any internal step that performs final prioritization.

### 3. `plan` (or retained `rns`) → ActionPlan

**Purpose:** Action prioritization and selection.

**SDLC role:** Normative.

**Input:** Preferred input is `IncidentFindings`, `SituationReport`, `ReadinessReport`, `ImpactAssessment`, or `OutcomeReport`.

**Output artifact:** `ActionPlan`

**Required fields:**
- `artifact_type: ActionPlan`
- `artifact_version`
- `derived_from[]`
- `actions[]`
- `priority_order`
- `rationale`
- `dependencies`
- `acceptance_criteria`
- `selection`

**Contract rules:**
- Must not mine raw transcripts directly when a causal or state artifact is required.[1]
- If given a raw transcript, it should reject the input or route to `debrief` first.[1]
- Must not create investigative findings from scratch.

**Keep / change / deprecate:**
- Keep the function of `rns`, but consider renaming the public surface to `plan` or `prioritize` to reduce branding overlap with open-ended “thought partner” skills.[1]
- Make the current `rns` output contract the canonical ActionPlan contract.

### 4. `design` → DecisionRecord

**Purpose:** Design decision framing.

**SDLC role:** Normative with descriptive support.

**Input:** Problem statement, constraints, design context, and optionally upstream artifacts.

**Output artifact:** `DecisionRecord`

**Required fields:**
- `artifact_type: DecisionRecord`
- `artifact_version`
- `derived_from[]`
- `problem_statement`
- `alternatives[]`
- `selection_criterion`
- `verdict`
- `reversal_trigger`
- `testability_contract`
- `risks`

**Contract rules:**
- Must include at least two alternatives for implementation-bound decisions.[1]
- Must identify a reversal trigger and a verification/testability contract.[1]
- Any design-level conclusion reached through open-ended thought-partner work should be reified here before implementation.

**Keep / change / deprecate:**
- Keep `design` as the canonical design producer.
- Keep `genius` and `council` as supporting ideation or review tools, but they should not be canonical artifact producers for binding design decisions.[1]

### 5. `check` → ReadinessReport

**Purpose:** Readiness, safety, and quality gate.

**SDLC role:** Evaluative / validation gate.

**Input:** Diff, proposal text, implementation result, or upstream artifact.

**Output artifact:** `ReadinessReport`

**Required fields:**
- `artifact_type: ReadinessReport`
- `artifact_version`
- `derived_from[]`
- `checks_run[]`
- `checks_skipped[]`
- `verdict`
- `risk_level`
- `blockers[]`
- `rollback_notes`
- `invariants_checked[]`

**Contract rules:**
- Must not generate an ActionPlan.[1]
- Must enumerate which checks ran versus were skipped.[1]
- Must support explicit modes such as `--quick-risk`, `--handoff`, `--strict`, and `--deep` if consolidation proceeds.[1]

**Keep / change / deprecate:**
- Keep `check` as the canonical readiness entry point.
- Migrate `risks` into `check --quick-risk` if behavior and ergonomics remain acceptable.[1]
- Migrate `recap check` into `check --handoff` behind an alias unless the handoff semantics are clearer as a preserved front-door alias.[1]
- Keep `red-team` separate because adversarial review is a distinct trust exercise.[1]

### 6. `impact` → ImpactAssessment

**Purpose:** Pre-change blast-radius and dependency analysis.

**SDLC role:** Descriptive and causal.

**Input:** Proposed diff, change description, or target component list.

**Output artifact:** `ImpactAssessment`

**Required fields:**
- `artifact_type: ImpactAssessment`
- `artifact_version`
- `source_ref`
- `proposed_change`
- `affected_files[]`
- `consumers[]`
- `interfaces_touched[]`
- `rollback_complexity`
- `test_gap`
- `observability_notes`

**Contract rules:**
- Must trace consumers or usage sites where feasible.[1]
- Must state rollback complexity and known test gaps.[1]
- Should be required before dispatching non-trivial implementation work.

**Keep / change / deprecate:**
- Add as a new public surface, even if it shares internals with `debrief`.
- Do not hide it only as a `debrief impact` mode unless you intentionally want a smaller public surface area than clarity would otherwise justify.[1]

### 7. `outcome` → OutcomeReport

**Purpose:** Post-implementation outcome review.

**SDLC role:** Descriptive with learning-oriented follow-through.

**Input:** Intended change, before/after evidence, logs, tests, and optionally linked DecisionRecord or ActionPlan.

**Output artifact:** `OutcomeReport`

**Required fields:**
- `artifact_type: OutcomeReport`
- `artifact_version`
- `derived_from[]`
- `intended_outcome`
- `verified_outcomes[]`
- `regressions[]`
- `lessons[]`
- `follow_up_candidates[]`
- `evidence_refs[]`

**Contract rules:**
- Must cite evidence for each major claim.[1]
- Must distinguish intended result, observed result, and lessons.
- Should be the canonical loop-closing artifact after meaningful implementation.

**Keep / change / deprecate:**
- Add as a new public surface, even if implemented over shared post-analysis utilities.

## Public Surface Mapping

| Current surface | Recommended disposition | Rationale |
|---|---|---|
| `/recap` | Keep, narrow contract | Own SituationReport only; remove planning output.[1] |
| `/recap check` | Alias to `check --handoff` or retain as alias only | Keep handoff semantics, unify gate engine.[1] |
| `/debrief` | Keep, narrow contract | Own IncidentFindings; remove prioritization.[1] |
| `/debrief chain` | Refactor heavily | It currently spans too much of the SDLC loop internally.[1] |
| `/rns` | Keep function; consider rename to `plan` | Canonical ActionPlan producer; reduce overlap with “thought partner” branding.[1] |
| `/design` | Keep, formalize DecisionRecord schema | Avoid buried design decisions.[1] |
| `/genius` | Keep as advisory only | Not a canonical artifact producer for binding design choices.[1] |
| `/council` | Keep as optional review aid | Useful quality gate, not canonical decision record producer.[1] |
| `/risks` | Deprecate into `check --quick-risk` | Overlaps with readiness cluster.[1] |
| `/check` | Keep and strengthen | Canonical readiness gate.[1] |
| `/red-team` | Keep separate | Legitimately different adversarial evaluation surface.[1] |
| `/friction` | Alias into `debrief` view or detector | Transcript-mining overlap.[1] |
| `/behave` | Alias into `debrief` view or detector | Transcript-mining overlap.[1] |
| `/why` | Keep, but make artifact-aware | Strong pure-causal boundary; should consume SituationReport when relevant.[1] |
| `/improve` | Keep, but add escalation rule | Design-level changes should flow into DecisionRecord.[1] |
| `/improve-codebase-architecture` | Review for merge or strict boundary | Overlaps with design/impact depending on use.[1] |

## Shared Artifact Layer

Before introducing additional public surfaces, create a tiny shared frontmatter contract used by every canonical artifact:

```yaml
artifact_type: <SituationReport|IncidentFindings|ActionPlan|DecisionRecord|ReadinessReport|ImpactAssessment|OutcomeReport>
artifact_version: 1
source_ref:
  - skill: <surface>
  - input: <path or logical input>
session_span:
  start: <timestamp or session marker>
  end: <timestamp or session marker>
derived_from: []
confidence: <high|medium|low>
```

This gives downstream skills a parseable and versioned envelope before the body schema diverges further.[1]

## Runtime and Test Enforcement

### Tier 1: Tests first

Add tests that enforce the most failure-prone boundaries:

1. `recap` output contains no normative planning section.[1]
2. `plan`/`rns` rejects or reroutes raw transcript input to `debrief`.[1]
3. `design` always emits a valid DecisionRecord with the required fields.[1]
4. `debrief` output is unordered and contains no final priority ranking.
5. `check` output always lists checks run and skipped.[1]
6. All canonical artifacts include valid frontmatter and version fields.

### Tier 2: Lightweight runtime guards

After tests stabilize, add low-cost runtime enforcement:

- A stop hook or pre-invocation hook that warns when `plan` receives a raw transcript path instead of a canonical artifact.[1]
- A guard that warns if implementation is dispatched without either an ImpactAssessment or an explicit trivial-change bypass.
- A guard that warns when a design-level implementation proceeds without a DecisionRecord.

### Tier 3: Contract-aware registry

Longer term, maintain a dependency graph showing which skills produce and consume which artifact types. This addresses the audit’s concern that output format changes can silently break downstream surfaces when the contract only lives in prose.[1]

## Long-Lived Session Strategy

Because sessions span days, terminals, and multiple topics, scope must be explicit rather than implicit. The recommended rule is:

- `recap`: full relevant session chain by default; narrowing is opt-in.[1]
- `debrief`: current transcript or supplied input by default; chain expansion is opt-in.[1]
- `plan`: bounded to explicit upstream artifacts; it should not decide its own historical scope.[1]
- `design`, `impact`, `check`, and `outcome`: operate on the current decision or change unless explicitly widened.

This keeps each invocation economical while preserving the ability to reason over the full session when needed.[1]

## Migration Plan

### Phase 0 — Freeze and inventory

- Record every live skill, alias, and plugin registration state.
- Add a status field to the registry where possible: `active | deprecated | alias | internal`.[1]
- Capture current output shapes for `recap`, `debrief`, `rns`, `design`, `check`, and `risks`.

**Exit criteria:** inventory complete, registry diff saved, no ambiguity about what is live.

### Phase 1 — Contract correction

- Remove “Recommended Next Steps” from `recap`.[1]
- Stop `debrief` from performing embedded prioritization in chain workflows.[1]
- Formalize DecisionRecord schema for `design`.[1]
- Define shared frontmatter envelope for all canonical artifacts.

**Exit criteria:** contracts documented, major boundary violations removed from surface definitions.

### Phase 2 — Test harness

- Add artifact-contract tests for recap, debrief, plan/rns, design, and check.[1]
- Add regression tests for alias routing behavior.
- Add schema validation fixtures for all canonical artifacts.

**Exit criteria:** failing contract drift is detectable in CI.

### Phase 3 — Readiness consolidation

- Fold `risks` into `check --quick-risk`.[1]
- Fold `recap check` into `check --handoff`, preserving user-facing aliasing if helpful.[1]
- Validate that `red-team` remains distinct and is not conflated with ordinary readiness.

**Exit criteria:** one canonical readiness gate, plus separate adversarial review.

### Phase 4 — Investigative consolidation

- Normalize `friction` and `behave` outputs into `debrief` detectors or modes.[1]
- Convert current entry points into aliases or stubs if needed.
- Thin `debrief` documentation by pushing mechanics into shared internal contracts rather than a monolithic SKILL file.[1]

**Exit criteria:** transcript-mining duplication reduced without losing specialist detectors.

### Phase 5 — New surfaces

- Build `impact` and `outcome` artifacts and public surfaces.[1]
- Wire `impact` into implementation dispatch for non-trivial changes.
- Wire `outcome` into loop-closing review after significant implementations.

**Exit criteria:** pre-change and post-change gaps are explicitly covered.

### Phase 6 — Runtime governance

- Add low-noise pre-invocation contract guards.
- Maintain artifact dependency map.
- Add drift checks for deprecated or alias-only skills lingering in registries.[1]

**Exit criteria:** the topology is enforceable, not merely documented.

## Implementation Checklist

### Immediate checklist

- [ ] Remove normative “next steps” output from `recap`.[1]
- [ ] Define shared artifact frontmatter schema.
- [ ] Create DecisionRecord schema for `design`.[1]
- [ ] Add test: `plan`/`rns` rejects raw transcript input.[1]
- [ ] Add test: `recap` emits no prioritization content.[1]
- [ ] Add test: `design` emits complete DecisionRecord.[1]
- [ ] Add test: `debrief` emits no ranking.
- [ ] Add test: `check` lists checks run/skipped.[1]

### Consolidation checklist

- [ ] Merge `/risks` behavior into `check --quick-risk`.[1]
- [ ] Merge `/recap check` behavior into `check --handoff` with alias preservation if needed.[1]
- [ ] Convert `/friction` into `debrief` detector/mode.[1]
- [ ] Convert `/behave` into `debrief` detector/mode.[1]
- [ ] Remove prioritization from `debrief chain`.[1]
- [ ] Review whether `rns` should be renamed publicly to `plan` or `prioritize`.[1]

### New artifact checklist

- [ ] Implement `SituationReport` schema.
- [ ] Implement `IncidentFindings` schema.
- [ ] Implement `ActionPlan` schema.
- [ ] Implement `DecisionRecord` schema.[1]
- [ ] Implement `ReadinessReport` schema.
- [ ] Implement `ImpactAssessment` schema.[1]
- [ ] Implement `OutcomeReport` schema.[1]

### Governance checklist

- [ ] Add artifact versioning.
- [ ] Add skill registry status field (`active | deprecated | alias | internal`).[1]
- [ ] Add contract-aware dependency map.
- [ ] Add lightweight pre-invocation guards for key misroutes.[1]
- [ ] Add stale-skill drift audit to plugin maintenance workflow.[1]

## ROI Expectations

The main return on this refactor is not fewer commands by itself; it is lower orchestration ambiguity, less duplicated analysis, stronger chain-of-custody for decisions, and better long-session memory through durable artifacts. For a solo director operating many AI coders, that usually yields better ROI than merely shaving one or two prompts off a workflow, because the expensive failures come from wrong-surface invocation, buried decisions, and repeated rediscovery of context.[1]

The highest-confidence ROI items are contract correction, DecisionRecord formalization, artifact tests, and readiness consolidation. The medium-confidence ROI items are renaming `rns`, adding runtime hooks, and deciding whether `impact` and `outcome` should be fully public surfaces versus named modes on an internal investigative engine.[1]

## Human

another LLM said this.  what do you think?  "Verdict
Partially. The refactor spec moves strongly toward the goal you have been asking about: a coherent, intentional skill system for a solo director coordinating AI coders, rather than an accumulated collection of overlapping commands.
But it is currently a plausible target architecture, not an evidence-backed refactor plan.
Its strongest contribution is identifying contract drift between descriptive, causal, evaluative, and normative work. Its main weakness is that it jumps from a conversational taxonomy to prescriptive restructuring without first proving how the live skills actually behave, which mechanisms are invoked, what users and downstream skills consume, and which consolidations improve outcomes.
I would approve it as an investigation hypothesis and audit framework. I would not approve the proposed merges, new commands, or runtime gates as written.
The transcript itself repeatedly converges on separating state synthesis, causal analysis, prioritization, design decisions, readiness, impact, and outcomes. The spec then turns that into seven canonical surfaces, artifact contracts, tests, and a phased migration. That is useful progress—but the apparent precision exceeds the evidence currently presented.
What it gets right
1. It identifies the real problem as contract ambiguity
The best diagnosis is not “too many skill names.” It is:
outputs with unclear authority;
several surfaces answering similar questions;
recommendations generated before evidence is stabilized;
decisions buried in free-form conversations;
no dependable chain from one skill’s output to another skill’s input.
The spec correctly calls out boundary drift, readiness overlap, weak artifacts, and ambiguous session scope.
That matches your actual concern better than simple command consolidation. A shorter menu can still be incoherent. A coherent system can tolerate several commands when each has an earned purpose.
2. The producer–artifact–consumer idea is directionally correct
The proposed chain is valuable:
source evidence
    ↓
SituationReport / IncidentFindings / ImpactAssessment
    ↓
DecisionRecord / ActionPlan
    ↓
implementation
    ↓
ReadinessReport / OutcomeReport

This improves:
traceability;
resumability across compact events;
handoffs between coders;
validation of what evidence supported a decision;
resistance to one model silently inventing prior context.
The shared versioned envelope and dependency graph are among the best ideas in the document.
3. It distinguishes readiness from adversarial review
Keeping red-team distinct from ordinary readiness is correct.
These answer different questions:
Readiness: Is there sufficient evidence to proceed under the applicable policy?
Review: Is the implementation correct and maintainable?
Red-team: How could the reasoning, assumptions, design, or evidence fail?
Outcome: Did the change actually produce the intended real-world result?
Combining these would make the interface simpler while weakening epistemic clarity.
4. It recognizes that open-ended thought partnership cannot be binding authority
The spec’s recommendation that /genius, /council, and thought-partner work may inform a decision but should not silently become the durable design authority is sound. Binding design conclusions should be captured in something like a DecisionRecord.
That does not mean every discussion needs bureaucracy. It means implementation agents need a reliable answer to:
What decision governs this work, why was it selected, and what would cause us to reconsider it?
Where it does not yet achieve your goal
1. It proposes a topology before auditing the live system
This is the largest issue.
The spec says to:
merge /risks into check;
absorb /friction and /behave;
constrain /recap;
prevent /rns from consuming transcripts;
add impact;
add outcome;
potentially rename /rns.
But it does not show evidence that the author inspected:
the live SKILL files;
routers and aliases;
actual hooks or orchestration code;
invocation telemetry;
downstream references;
representative outputs;
tests;
real transcripts demonstrating overlap;
user usage frequency;
whether the proposed artifact consumers exist.
The spec does put inventory in Phase 0, but most architectural conclusions have already been made before that inventory.
That reverses the correct order.
Change
Turn the document from a refactor specification into an investigation-and-decision specification.
No merge or new public surface should be authorized until the implementation LLM produces an evidence table like:
Proposed changeLive source inspectedObserved overlapExisting consumersReal examplesExpected benefitRiskVerdict
Permitted verdicts should include:
KEEP
CLARIFY_CONTRACT
SHARE_INTERNAL_MECHANISM
ALIAS
MERGE
DEPRECATE
NEW_SURFACE_JUSTIFIED
NO_CHANGE
BLOCKED_EVIDENCE_INSUFFICIENT
The current spec assumes several MERGE and NEW_SURFACE_JUSTIFIED answers prematurely.
2. It optimizes conceptual purity more than user outcomes
The rule that /recap must contain no “Recommended Next Steps” is too absolute.
There is an important distinction between:
ranking or selecting future work, which belongs in planning; and
stating the immediate resume action, which is essential to a useful handoff.
A recap that says only what happened but not where to resume may be theoretically pure and practically worse.
Better contract
recap should be prohibited from:
generating a backlog;
ranking opportunities;
introducing speculative improvements;
selecting among competing strategic actions.
But it should be allowed—and often required—to state:
the last completed boundary;
the currently authorized objective;
the next already-established action;
unresolved blockers;
what evidence the next agent must reverify;
the recommended next skill/router, when applicable.
For example:
resume:
  authorized_next_action: "Run the existing integration test against the live adapter"
  authority_ref: "DecisionRecord-..."
  blocked_until: []
  suggested_surface: "check --handoff"

That is continuity, not prioritization.
3. Rejecting raw transcripts at /rns is unnecessarily brittle
The proposed rule says prioritization must reject or reroute raw transcripts to /debrief.
The intention is good: do not let prioritization fabricate findings.
But a hard rejection creates user friction and assumes the user understands the topology perfectly. That is exactly the type of cognitive load you are trying to eliminate.
Better behavior
When given a raw transcript, /rns should:
classify what upstream evidence is missing;
invoke or recommend the appropriate evidence-extraction mechanism;
preserve the original user intent and scope;
receive the produced artifact;
continue prioritization when authorized;
report the provenance chain.
For expensive inputs, it may pause before running a costly analysis. But “wrong input type” should generally trigger safe orchestration, not a dead end.
The user should be able to say:
Review this entire session and tell me what we should do next.
The system—not the user—should know whether that requires recap, debrief, impact analysis, or multiple packets.
4. Session scope is described but not operationally solved
The spec says that scope should be explicit, recap should use the “full relevant session chain,” and other skills may expand or narrow their analysis.
“Relevant” remains an unresolved mechanism.
Your environment has:
sessions spanning days;
compactions;
resumption in other terminals;
multiple topics in the same conversational session;
independent worktrees and agents;
artifacts generated in different runs.
A timestamp range and source_ref are not enough to establish identity, relevance, or completeness.
Missing contract fields
Artifacts likely need something closer to:
artifact_type:
artifact_version:

authority:
  session_id:
  run_id:
  workstream_id:
  task_id:
  repository_revision:
  worktree_path:

scope:
  requested_scope:
  resolved_scope:
  included_sources: []
  excluded_sources: []
  exclusion_reasons: []
  scope_resolution_method:

provenance:
  producer:
  produced_at:
  consumed_source_paths: []
  source_revisions: []
  parent_artifacts: []

freshness:
  valid_as_of:
  invalidation_conditions: []
  revalidation_required: false

confidence:
  level:
  unsupported_claims: []

The key requirement is not that every artifact must have every field. It is that the system has a deterministic answer to:
What history did this skill actually inspect, why was that history considered authoritative, and what might it have missed?
Without that, the artifact layer can make incomplete analysis appear more trustworthy.
5. It risks turning optional cognition into mandatory ceremony
Seven public surfaces and seven artifact types may be justified. They may also be architecture astronautics.
The spec recommends adding impact and outcome as public surfaces, while also making numerous existing skills artifact producers. It does not establish that users will invoke these surfaces correctly or that separate public commands outperform modes inside existing workflows.
You are a solo director. Your scarce resource is not committee coordination; it is attention.
Better principle
Use few public intents, many internal capabilities.
For example, the public interface might remain:
/recap
/design
/go
/review
/debrief
/rns
Internally, /go, /design, and /review may invoke:
impact analysis;
requirements completeness;
readiness evaluation;
test planning;
outcome verification;
adversarial review.
A capability deserves a separate public surface only when at least one is true:
users frequently invoke it independently;
it has materially different inputs or authority;
it produces a durable artifact independently consumed elsewhere;
separating it reduces misrouting in live tests;
it must be explicitly selected for cost, risk, or trust reasons.
The current spec treats conceptual distinctness as nearly sufficient for a separate skill. It is not.
6. The proposed topology is incomplete as an SDLC environment
The spec is strong on analytical outputs, but it does not fully model the path from user intent to verified result.
Missing or underrepresented steps include:
problem and requirements clarification;
source/codebase reconnaissance;
evidence and external research;
acceptance-criteria formation;
implementation dispatch;
test strategy;
code review;
live/runtime validation;
release/deployment;
rollback;
monitoring;
learning promotion;
abandonment or supersession of stale artifacts.
This does not necessarily mean adding twelve commands. It means the architecture must explain where these responsibilities live.
A complete end-to-end path should resemble:
User intent
  ↓
Scope + authority resolution
  ↓
Relevant source reconnaissance
  ↓
Problem / requirement contract
  ↓
Impact and design decision, when required
  ↓
Implementation plan and dispatch
  ↓
Code change
  ↓
Static and automated verification
  ↓
Independent review / red-team as required
  ↓
Live or acceptance validation
  ↓
Readiness decision
  ↓
Handoff / merge / deploy
  ↓
Outcome verification
  ↓
Debrief and prioritized improvement, when warranted

The spec currently concentrates on the report-producing nodes and underdefines the workflow connecting them.
Changes I would make
1. Replace “one public surface per decision step”
The design principle currently says one public surface per primary SDLC decision step.
Replace it with:
Every material SDLC decision must have one canonical contract and authority. It may be exposed as a standalone skill, a mode, or an internally invoked capability. Public-surface count is determined by observed routing quality and user ergonomics, not taxonomy alone.
This preserves clean ownership without proliferating commands.
2. Add a live-evidence phase before contract correction
Reorder the migration:
Phase 0 — Verify the consumed environment
Find all live skill roots and plugin registrations.
Confirm which copies are consumed.
Identify aliases, wrappers, hooks, routers, and direct callers.
Record repository revision and worktree.
Detect duplicate or stale copies.
Phase 1 — Behavioural inventory
For each relevant skill:
inspect its source;
exercise representative real inputs;
capture output;
identify upstream/downstream dependencies;
identify actual artifact writes;
classify cognitive work performed;
record latency and model/tool dependencies;
determine whether the user actually invokes it.
Phase 2 — Outcome-based evaluation
Evaluate:
routing accuracy;
omission rate;
duplicate analysis;
actionability;
correctness;
resume success after compaction;
cross-terminal isolation;
director effort;
token/model cost;
failure recovery.
Only then decide topology.
3. Treat artifact schemas as hypotheses until consumers exist
Do not implement seven schemas at once.
Start with the smallest envelope and perhaps two high-value contracts:
DecisionRecord
a generalized EvidencePacket or existing handoff artifact
Then add a specialized artifact only when:
its semantics cannot be represented cleanly;
a real producer exists;
a real consumer exists;
the consumer behaves better with it;
versioning and invalidation are defined.
Otherwise, you may build a large artifact taxonomy that is technically valid but unused.
4. Separate four kinds of validation
The current check consolidation needs a clearer internal model.
Check typeQuestion
Completeness
Did we address the requested scope and acceptance criteria?
Correctness
Does the implementation behave as intended?
Readiness
Is the evidence sufficient and risk acceptable to proceed?
Outcome
Did the deployed or real-world change achieve the intended effect?
These can share an engine, but they should not be collapsed into one vague verdict.
A ReadinessReport should reference the results of completeness and correctness checks; it should not pretend to perform all of them itself.
5. Keep handoff as a first-class transition contract
The spec treats handoff as a packaging mode of SituationReport plus optional readiness. That is close, but “optional readiness” may be too weak.
A handoff should explicitly distinguish:
continuation handoff: another agent may continue investigation or implementation;
review handoff: work is presented for evaluation, not claimed complete;
completion handoff: claimed objective has passed its required checks;
blocked handoff: work is preserved but cannot proceed;
decision handoff: the human must select among options.
A handoff is not merely a formatted summary. It is a transfer of authority and expectations.
6. Add success metrics before implementation
The document’s ROI section is mostly asserted rather than operationalized.
Define baseline and post-refactor measures:
percentage of invocations routed to the correct capability;
percentage requiring user correction;
percentage of handoffs successfully resumed without rediscovery;
missed-work rate in full-session audits;
duplicate recommendation rate;
unsupported factual claim rate;
decisions lacking durable rationale;
implementation starts without sufficient reconnaissance;
average director interventions per completed workstream;
latency and cost per successful outcome;
false blocking and false readiness rates.
Without these, you can prove that contracts were implemented but not that your outcomes improved.
Recommended near-term scope
I would not start by adding impact and outcome, renaming /rns, or merging several commands.
I would start with one bounded workstream:
SDLC Skill Topology Discovery and Contract Validation
Deliverables:
Live inventory
Every relevant skill, alias, router, hook, producer, and consumer.
Behaviour matrix
What each skill actually does on representative inputs.
Overlap and gap matrix
Based on observed behavior, not descriptions.
Workflow graph
User input → source discovery → skill → artifact → consumer → decision/action.
Contract candidates
Minimal fields only.
Refactor verdicts
Keep, clarify, share engine, alias, merge, deprecate, add, or blocked.
Baseline evaluation corpus
Several real tasks from your history and expected routing/outcomes.
One pilot correction
Preferably a high-confidence boundary such as making design decisions durable without changing the entire topology.
Before/after evidence
Demonstrating that the pilot improves a real workflow.
That would tell you whether the proposed architecture is earned.
Bottom line
The files are aiming at the right problem and contain several strong architectural ideas. The refactor spec is better than organic command accumulation, but it currently risks replacing organic ambiguity with contract-heavy bureaucracy.
The biggest change is methodological:
Do not implement the proposed taxonomy first and validate it afterward. Inspect the live system, measure representative workflows, identify actual producer–consumer contracts, and let the evidence determine which boundaries become commands, modes, internal engines, or no change.
That approach is much more likely to improve the outcomes you care about: reliable orchestration, fewer missed facts, less repeated work, lower director cognitive load, better handoffs, and higher-quality completed changes."

## Assistant

The critique is largely **correct** and, in places, more rigorous than the refactor spec itself. It’s pointing at exactly the thing you care about: evidence-backed architecture vs attractive taxonomy.[1]

I’ll break my view into where I *agree*, where I *disagree or would soften*, and what I’d actually do next.

***

## Where I strongly agree

### 1. “Plausible target architecture, not an evidence-backed refactor plan”

This is accurate. The spec I produced is a **good target topology**, but it *does* jump from:

- conversational audit of overlaps and contracts →  
- prescriptive merges, new surfaces, and gating

without first showing:

- live SKILL sources and hooks inspected,
- telemetry/usage patterns,
- representative outputs for each skill,
- concrete producer–consumer traces.

The spec has some grounding in the text audit and your transcript, but it is still mostly **design-by-reasoning**, not **design-by-observed-workflows**.[1]

For someone with your epistemic standards, the other LLM is right to call it “investigation hypothesis and audit framework,” not “approved refactor plan.”

### 2. Producer–artifact–consumer chain is directionally right

They endorse the core idea:

> SituationReport / IncidentFindings / ImpactAssessment → DecisionRecord / ActionPlan → implementation → ReadinessReport / OutcomeReport

This matches what both you and the transcript were converging on: separate *evidence* from *decision rendering* and then from *outcome verification*.[1]

I still think this chain is the right **shape** for a solo director + AI coders. It gives you:

- traceability,
- resumability across compact events,
- explicit handoffs between skills/agents,
- a way to audit “what evidence backed this decision.”

The critique agrees on that and highlights the shared envelope + dependency graph as some of the best ideas. I concur.

### 3. Red-team vs readiness vs outcome vs review

They correctly insist these are different questions:

- Readiness: “Is evidence sufficient and risk acceptable?”  
- Review: “Is implementation correct and maintainable?”  
- Red-team: “How could reasoning/design/evidence fail?”  
- Outcome: “Did the change actually work in reality?”

The spec kept red-team separate; they explicitly approve that. I’d maintain that separation and, per their suggestion, clarify that `check` is **not** “all validation rolled into one,” but a gate that *consumes* other checks.

### 4. Thought partner vs binding authority

They reinforce one of the spec’s most important points: open-ended thought partnership (`genius`, `council`, general chat) should **inform** decisions but not silently become **binding authority**.

This is key in your environment:

- Many design decisions currently happen in free-form conversation.
- Implementation agents then take that as “truth” without a durable DecisionRecord.

This *is* a real epistemic risk. The critique’s emphasis here is right, and I would keep the spec’s push toward a canonical DecisionRecord.

***

## Where I think the critique is right to push back

### 1. “It proposes topology before auditing the live system”

This is the biggest, valid criticism.

The spec:

- proposes merges (`/risks` into `/check`, `/recap check` into `/check`),
- proposes absorbing `/friction` and `/behave`,
- proposes gating `/rns` inputs,
- proposes adding `impact` and `outcome` surfaces,

**before** showing:

- actual SKILL.md content for each,
- routing/aliases/hook behavior,
- telemetry on how you actually invoke them,
- tests/outputs showing overlaps.

That’s backwards for your standard. The critique’s suggested shift—turn it into an **investigation-and-decision spec** with explicit verdict types (`KEEP`, `MERGE`, `ALIAS`, `BLOCKED_EVIDENCE_INSUFFICIENT`, etc.)—is the right methodological correction.

In other words: use the spec as a **hypothesis**, not a set of commands. Then gather real evidence to justify each `MERGE` or `NEW_SURFACE_JUSTIFIED`.

### 2. Recap must be descriptive but can *still* say “resume here”

They’re right: my “no Recommended Next Steps” rule for recap was too blunt if read literally.

There’s a distinction between:

- **Continuity**: “We finished X, the authorized objective is Y, the next established action is Z, blockers are A/B.”  
- **Prioritization/planning**: “Given all possible work, rank and choose strategic actions.”

Recap *should* give a clear “resume here / next established action” for handoff; otherwise, it becomes academically pure but practically worse for your multi-day sessions.

So the corrected contract is:

- Recap: allowed/expected to state the current objective and **next already-authorized step.**
- Recap: *not* allowed to generate a new backlog, rank opportunities, or choose between competing strategies; that’s RNS/plan territory.

The critique is right; I’d update the contract that way.

### 3. Hard-rejecting raw transcripts at `/rns` is brittle

The spec said “reject or route” raw transcripts to debrief. The critique pushes for:

- classify missing upstream evidence,
- orchestrate the right analysis,
- preserve user intent,
- then proceed with prioritization once evidence exists.

For your director role, this is more ergonomic:

- You say “Review this entire session and tell me what next.”
- The system figures out whether it needs recap, debrief, impact, etc.

So instead of *hard* rejection:

- `/rns` should be **contract-aware**:  
  - If given a transcript, it must either call debrief/recap internally or refuse to prioritize without explicit user acceptance of a shortcut.  
  - But from your UX perspective, auto-orchestration is superior to “wrong input, go back.”

Here, I’d keep the *principle* (don’t fabricate findings), but soften the behavior as the critique suggests.

### 4. Scope and artifact identity

The critique is right that “session_span + source_ref” is not enough for your multi-terminal, multi-topic, compacted sessions. You need some notion of:

- `workstream_id` or `task_id`,
- `run_id` and `repository_revision`,
- `scope_resolution_method` (how the skill chose what to look at),
- `included_sources` vs `excluded_sources` and why.

The spec’s envelope is minimal; the critique is pushing toward a **provenance-rich** artifact identity. That’s more complex but more aligned with your “I don’t know what I don’t know” concern.

I’d treat their proposed richer envelope as a **longer-term objective**, but agree that you need more than timestamps and a session id to answer “what did this skill actually inspect, and what might it have missed?”

### 5. Risk of ceremony / “architecture astronautics”

They’re right to call out a danger:

- 7 public surfaces,
- 7 artifact types,
- plus many internal capabilities

can be overkill for one solo director, if you aren’t careful. Their alternative principle:

> Few public intents; many internal capabilities.

is a good counterweight. It suggests:

- Public faces could remain `/recap`, `/design`, `/go`, `/review`, `/debrief`, `/rns`.
- Internally, those orchestrate impact, readiness, outcome, etc., depending on context and cost.

For you, that could mean:

- You don’t *always* need to think “call /impact”; sometimes `/go` or `/check` automatically invokes impact internally based on risk, while exposing it explicitly when you *do* want to see that layer.

So I agree: not every conceptual distinction should become a public skill. The spec treated “distinct SDLC step” as almost sufficient for a separate surface; the critique’s bar (distinct inputs, consumers, cost/risk, or frequent direct invocation) is better.

***

## Where I’d push back or nuance

### 1. “Incomplete as an SDLC environment”

They argue the spec underrepresents:

- problem/requirements clarification,
- source/codebase reconnaissance,
- evidence/external research,
- acceptance criteria,
- implementation dispatch,
- test strategy,
- code review, runtime validation, release, rollback, monitoring, abandonment.

That’s true: the spec is mostly about **analysis and decision surfaces**, not the full pipeline.

But that was deliberate: you already have many implem/dispatch/test skills; the spec was focusing on the noisy part of your environment—analysis, readiness, and planning surfaces that were overlapping.

I’d treat their list as a **reminder** to ensure the full pipeline is represented in your mental model, but not necessarily as a criticism of the refactor’s *scope*. You don’t need to refactor everything at once; focusing on the highest ambiguity cluster is valid.

### 2. “Don’t implement topology before inspection”

They want a full behavior inventory first. That’s ideal, but you already did a substantial audit of overlaps and partial contract mapping.[1]

I’d compromise:

- Use the spec’s topology as **hypothesis**.
- For each proposed change, actually inspect SKILL.md, hooks, and representative outputs and explicitly label the change with their suggested verdicts (`KEEP`, `MERGE`, `ALIAS`, etc.).
- This keeps the spec useful as a north star while honoring their demand for evidence before execution.

***

## What I would actually do next with both documents

Given:

- Your willingness to radically refactor if ROI is high.
- The spec (target topology and migration checklist).[1]
- This critique (methodological and UX corrections).

A practical next move:

1. **Treat the spec as a hypothesis and the critique as constraints.**

   - Spec = “this is what the system should probably look like.”
   - Critique = “here is how to validate, where to soften, and where to avoid premature proliferation.”

2. **Define a small investigation corpus.**

   - Choose 5–10 real workstreams (incidents, feature changes, design decisions) from your transcripts.
   - For each, record:
     - Which skills you actually invoked.
     - How you *wanted* them to behave.
     - Where you felt friction, duplication, or missed context.

3. **Apply the critique’s verdict table idea.**

   For each relevant skill (`recap`, `debrief`, `rns`, `check`, `risks`, `friction`, `behave`, `genius`, `design`, etc.):

   - Inspect live SKILL.md and routing.
   - Run representative inputs.
   - Fill a table:

   | Proposed change           | Live behavior evidence | Overlap/gaps | Consumers | Benefit | Risk | Verdict              |
   |---------------------------|------------------------|-------------|-----------|---------|------|----------------------|
   | `/recap` remove RNS       | SKILL.md, outputs      | Planning mix | `/rns`    | high    | low  | CLARIFY_CONTRACT     |
   | `/risks` → `check --quick`| SKILL.md, outputs      | readiness    | `/check`  | medium  | medium| MERGE or NO_CHANGE  |
   | `/friction` → `debrief`   | SKILL.md, outputs      | transcript   | `debrief` | high    | low  | SHARE_INTERNAL_MECH  |
   | `impact` new surface      | N/A                    | missing step| `/go`     | high    | medium| NEW_SURFACE_JUSTIFIED|

   This moves from taxonomy to **evidence-backed verdicts**, as the other LLM suggests.

4. **Limit immediate implementation to 2–3 changes.**

   Based on everything, I’d start with:

   - **Clarify recap contract** (allow “resume here,” disallow backlog/prioritization).
   - **Formalize DecisionRecord** and amend `design` to emit it.
   - **Add artifact frontmatter + tests for recap/debrief/rns/check**.

   These are low-ceremony, high-impact corrections that both the spec and critique agree are valuable.

5. **Delay new public surfaces (`impact`, `outcome`) until you see clear evidence they’re separately needed.**

   Meanwhile, you can:

   - Model impact as an internal mode of `debrief` or `check`.
   - Model outcome as a mode of `debrief` or `recap` + `check`.

   If you find yourself *frequently* wanting to invoke them explicitly and separately, then promote them to public surfaces.

***

## My “verdict” on the other LLM’s verdict

- **Agreement (high confidence)**:  
  - Spec is a good hypothesis, not yet an evidence-backed implementation plan.  
  - Contract drift is the core problem, and the spec’s producer–artifact–consumer framing is valuable.  
  - Recap should retain continuity (“resume here”), not be stripped to pure history.  
  - Hard rejecting raw transcripts at `/rns` is too brittle; contract-aware orchestration is better.  
  - Scope/provenance needs more structure for your cross-terminal, multi-topic sessions.  
  - There’s a real risk of ceremony and command proliferation; few public intents, many internal capabilities is a healthier bias initially.

- **Partial disagreement / nuance (medium confidence)**:  
  - The spec’s omission of implementation/testing/release details is okay for its initial scope; you don’t need to solve *every* SDLC step in one refactor.  
  - Seven artifact types are not inherently “astronautics” for your environment, as long as you treat them as *targets* and only fully implement those with real producers/consumers.  

Overall: they’re not rejecting the architectural ideas; they’re insisting on **methodology** and **UX** corrections before you treat the spec as executable truth. That’s aligned with your own epistemic stance, and I’d incorporate their constraints into how you execute the refactor.

If you like, I can synthesize both documents into a compact “Phase 0–1 plan” you can drop directly into Claude Code as a task: inventory, behavior matrix, verdicts, and 2–3 concrete, low-ceremony contract fixes to implement first.

## Human

Are there repos that can help scaffold our work?

## Assistant

Yes, there are several repos and frameworks that can **scaffold** what you’re trying to build—both on the Claude Skills side and on the SDLC/agent-orchestration side—but none will drop in your exact topology. They’re more reference architectures and pattern libraries than turnkey solutions.[1][2][3]

Given your goals (solo director, AI coders, SDLC skill topology, contract-first architecture), I’d group useful scaffolds into three buckets:

***

## 1. Claude Skills / SKILL.md ecosystems

These help with *skill design and contracts*, not SDLC per se.

- **Anthropic’s public skills repo** (`anthropics/skills`)  
  - Shows how Anthropic structures SKILL.md, modes, references, and tests.[3]
  - Good for: contract pattern, documentation style, routing conventions.

- **Community “awesome skills” lists**  
  - `awesome-claude-skills`, `awesome-skill-md`, Verdent guides.[4][5][6]
  - Good for: seeing how others separate analysis vs planning vs execution skills, and for stealing SKILL.md patterns for artifact schemas.

These won’t give you SDLC topology, but they’re **scaffolding for how to write and organize skills cleanly.**[6][3]

***

## 2. Agentic SDLC / multi-agent frameworks

These are closer to your “AI-first SDLC” concern.

- **ALMAS: Autonomous LLM-based Multi-Agent Software Dev** (research framework)  
  - Multi-agent SDLC framework that integrates with CI/CD tools, versioning, and task tracking.[7]
  - Good for: seeing how others structure agents around SDLC phases and tool integration; not Claude-specific.

- **SDLC agent frameworks and “agent-first developer toolchain” articles**  
  - Infosys SDLC Agent Framework, agent-first SDLC references.[8][9]
  - Good for: conceptual mapping of SDLC phases to agents—helps sanity-check your seven-surface model against industry thinking.

- **GitHub “sdlc” topic (multi-agent SDLC frameworks)**  
  - Includes repos with multi-agent, autonomous SDLC orchestration for coding agents.[10]
  - Good for: seeing concrete orchestrator implementations, role definitions, and artifact exchange patterns.

These won’t match your Claude Code environment, but they’re **scaffolding for multi-agent SDLC roles, orchestration graphs, and producer–consumer flows.**[7][10]

***

## 3. General agent orchestration frameworks

These help with **wiring skills/agents together and enforcing contracts**.

- **Semantic Kernel** (Microsoft)  
  - SDK for agent orchestration, skill composition, and memory management; used for embedding LLM workflows into apps.[2]
  - Good for: patterns around skills, planners, and connectors; can inform how you think about your own “skill graph.”

- **LangGraph, AutoGen, CrewAI, etc.**  
  - Libraries for graph-based workflows, multi-agent coordination, and contract-like flows.[11][2]
  - Good for: state handling, agent routing, and designing your own orchestrator in Python/TypeScript.

None of these is Claude-specific, but they’re the **best scaffolds for thinking about agent orchestration and shared artifacts** similar to your SituationReport/ActionPlan idea.

***

## How I’d use them concretely

Given your sophistication and willingness to refactor:

1. **Borrow SKILL.md structure and patterns** from `anthropics/skills` and curated lists for:
   - Mode definitions,
   - references/contract sections,
   - test layout.[3][6]

2. **Use an SDLC agent framework repo** (from the `sdlc` GitHub topic or ALMAS) as a reference for:
   - how they define roles (planner, implementer, reviewer, verifier),
   - how they pass artifacts (plans, diffs, test reports) between agents.[10][7]

3. **Pull orchestration ideas** from Semantic Kernel / LangGraph / AutoGen for:
   - contract-aware routing,
   - graph-based decision flows,
   - dependency maps between skills.[2][11]

These give you **scaffold and prior art** for multi-agent SDLC and skill contracts, but you’ll still need to adapt them into your Claude Code plugin architecture.

If you want, I can narrow this down to 3–5 specific repos (with links) that look closest to “multi-agent SDLC with evidence packets and planning surfaces,” and suggest exactly what to steal from each (e.g., roles, artifact schemas, routing patterns).

## Human

what about GSD?

## Assistant

GSD is probably the **closest existing scaffold** to what you’re trying to do, but it solves a *different* primary problem than your SDLC skill topology. It’s a spec‑driven, multi‑agent **context‑management and planning framework** for Claude Code, not an SDLC contract system.[1][2][3]

### What GSD actually does

From the current docs and ecosystem:

- GSD (“Get Shit/Stuff Done”) is a **lightweight spec‑driven development framework** built around Claude Code.[3][1]
- It:
  - Interviews you to define a project spec and roadmap.[4][3]
  - Splits work into phases and tasks, each handled in a **fresh sub‑agent context** to avoid context rot.[2][1][3]
  - Uses structured files (Markdown/XML) to persist requirements, decisions, and state across phases.[5][2]
  - Spawns multiple agents per phase (planner, executor, reviewer, UAT, etc.) and can parallelize via wave‑based execution.[6][3]
  - Provides hooks like discuss‑phase, plan‑phase, research, and guided UAT.[7][6]

One deep dive describes it as “no framework, just ~50 Markdown files” defining slash commands, agents, hooks, and persistent state. Another comparison piece notes GSD’s key decision: **separate orchestrator per phase, each under ~50% context, with state written to disk between phases.**[8][5]

So: GSD is **meta‑prompting + context engineering + multi‑agent orchestration**, using disk‑backed specs and state to keep quality consistent across many tasks.[1][2][5]

### How that relates to your SDLC skills

Your current work is about:

- Clarifying **SDLC decision steps** (recap/state, debrief/causes, plan/prioritize, design decisions, readiness, impact, outcomes).[9]
- Making these steps **skills** with clear contracts and artifacts (SituationReport, IncidentFindings, ActionPlan, DecisionRecord, etc.).[9]
- Reducing overlap and boundary drift between skills.

GSD’s focus is different:

- It cares about:
  - Project‑level **specs and phases**.
  - Context rot and state persistence.
  - Orchestrating multiple Claude sub‑agents against a shared spec.[3][5][1]
- It does have:
  - Planning phases,
  - execution phases,
  - review/UAT phases,
  - quality gates for schema drift/scope reduction.[6][5]

But it **does not** ship an SDLC skill contract model like “recap emits SituationReport, debrief emits IncidentFindings, rns consumes them,” etc. That part is yours.

### How GSD can scaffold your work

Given that, GSD can help you in three concrete ways:

1. **Phase and agent structure**

   GSD already embodies a “phased SDLC‑like workflow”:

   - Plan/spec phase.
   - Research phase.
   - Implementation waves.
   - UAT / verification.
   - Outcome review.[7][3][6]

   You can **map your canonical surfaces** onto GSD’s phases:

   - GSD spec/plan → your `SituationReport` + early `DecisionRecord`.
   - GSD execution waves → your implementation + `ImpactAssessment` and `ReadinessReport`.
   - GSD UAT → your `OutcomeReport` + `IncidentFindings` when things go wrong.

   GSD gives you a **ready‑made phase orchestration skeleton**; you plug your SDLC artifacts into those phases.

2. **Context and state management**

   You’re fighting:

   - long, cross‑terminal, multi‑topic sessions,  
   - compaction and loss of detail,  
   - “buried decisions” in free chat.

   GSD’s strength is:

   - **externalizing state** into structured files (requirements, decisions, plans).[2][5]
   - starting each phase with a fresh, high‑budget context based on those files.[5][3]

   That’s exactly the pattern you want for your artifacts:

   - `SituationReport`, `IncidentFindings`, `ActionPlan`, `DecisionRecord`, `ReadinessReport`, etc. should be **GSD‑style persistent files** that each phase’s sub‑agents read in.
   - Your recap/debrief/plan skills become **generators and consumers of those files**, inside or alongside GSD.

3. **Multi‑agent roles and model routing**

   GSD already supports:

   - multiple agent roles (planner, executor, reviewer, UAT, etc.),[3][6]
   - per‑agent model overrides (`gsd-planner: opus`, `gsd-executor: sonnet`, etc.),[10]
   - explicit cross‑provider reviews (Claude reviewing Cursor’s work, etc.).[10]

   You can reuse that:

   - Use GSD’s **agent type + model override** machinery to assign models to your SDLC roles:
     - recap/debrief on “analysis‑strong” models,
     - plan/prioritize on “budget‑friendlier” models,
     - red‑team/design review on higher‑tier models.
   - Use GSD’s **wave‑based execution** as the underlying engine for things like “run recap, then debrief, then plan, then check” across tasks.[6][5][3]

### Where GSD does **not** help directly

GSD does *not*:

- Give you an SDLC‑specific skill taxonomy or artifact schema.  
- Enforce your descriptive vs causal vs normative contracts; its quality gates are about context and spec adherence, not your recapped topology.[11][5]
- Model your multi‑plugin, 60+ skill environment; it’s a separate, more opinionated layer.

So:

- GSD is **not a drop‑in replacement** for your SDLC skill topology.
- It is a **strong scaffolding layer** for:
  - phase orchestration,
  - context management,
  - sub‑agent spawning,
  - spec/state persistence.

Your SDLC work lives **inside or alongside** that scaffold.

### Practical way to combine them

If you want positive ROI without reinventing everything:

1. Use GSD for **project/phase orchestration and context rot prevention**:
   - Let GSD own “project spec & phases, sub‑agent management, context rotation.”[1][5][3]

2. Use your SDLC skill topology for **within‑phase decision steps**:
   - Inside a GSD implementation or review phase:
     - Call `recap` to produce SituationReport.
     - Call `debrief` for IncidentFindings when something fails.
     - Call `plan`/`rns` to produce ActionPlan.
     - Call `design` for DecisionRecord when architecture changes.
     - Call `check`/`red-team` for readiness.
     - Call your future `impact`/`outcome` for blast radius and audit.

3. Persist SDLC artifacts as **GSD‑compatible state**:
   - Write each artifact to markdown/XML files in the GSD project structure.
   - Teach GSD’s orchestrators to **read those artifacts** at phase start, not just its own spec files.

This lets you leverage GSD’s battle‑tested workflow and “fresh subagent contexts,” while still enforcing your more precise SDLC contracts.

If you’re open to that, I can outline a concrete integration plan: which GSD phases should call which SDLC skills, what artifact filenames/formats to use, and how to keep your long‑lived sessions and GSD’s project directories in sync.

## Human

is GSD something that's better to look at after we rationalize our sdlc skills?

## Assistant

Short answer: yes. GSD is more valuable **after** you’ve rationalized your SDLC skills, because it’s an orchestration/context framework, not a topology designer. You’ll get better ROI if you plug a clean SDLC skill system into GSD, rather than trying to fix both at once.[1][2][3]

### Why SDLC rationalization should come first

- GSD gives you **phases and agents** (plan, discuss, execute, review, UAT) and a way to manage context and spec/state across them.[2][3][1]
- Your current problem is **contract drift** and overlapping skill responsibilities: recap vs debrief vs rns vs check vs risks etc.[4]
- If you drop GSD on top of a fuzzy skill topology:
  - GSD will happily orchestrate the *wrong* surfaces.
  - You’ll entrench the ambiguities behind more ceremony.

Rationalizing SDLC skills:

- Clarifies **who does what**:
  - Recap → SituationReport.
  - Debrief → IncidentFindings.
  - RNS/plan → ActionPlan.
  - Design → DecisionRecord.
  - Check/red-team → Readiness/Review.[4]
- Gives you **artifact contracts** GSD can treat as state files.
- Reduces the number of “maybe this skill” choices GSD has to make.

So from a systems design standpoint: **fix the contracts and boundaries first**, then let GSD orchestrate them.

### When GSD becomes useful

GSD starts to shine once you have:

- A small set of **canonical SDLC skill surfaces** with clear inputs/outputs.
- Durable artifacts (reports, decisions) that should persist across phases and compactions.[4]
- A desire to:
  - manage long projects across multiple coding and review phases,
  - keep each phase in a **clean, fresh context**,
  - spawn multiple agents per phase (planner, executor, reviewer).[3][5][1]

At that point GSD gives you:

- A structured **phase graph** to hang those skills on.
- Disk‑backed spec/state files to store your SDLC artifacts.
- per‑agent model overrides and profile switches that align with your “fleet of AI coders” idea.[6][7]

### Recommended order for you

Given you’re comfortable with radical refactoring:

1. **Rationalize SDLC skills and contracts** (recap/debrief/plan/design/check/red‑team, plus impact/outcome if justified).
2. Add **artifact schemas** and basic tests so these skills behave predictably.[4]
3. Only then bring in **GSD**, and:
   - map your SDLC surfaces into GSD’s phases,
   - wire artifacts into GSD’s spec/state files,
   - use GSD’s multi‑agent orchestration to scale execution.

If you want, I can sketch a concrete “Phase 0–1” plan that’s purely about SDLC skill rationalization, and then a “Phase 2” plan that layers GSD on top once the core is clean.

## Human

[https://github.com/levnikolaevich/claude-code-skills](https://github.com/levnikolaevich/claude-code-skills), how useful is this?

## Assistant

Usefulness: **moderate to high as a reference and plugin scaffold, low as a direct SDLC topology solution.** It’s a small, focused marketplace with workflow‑oriented skills (Agile, audits, bootstrapping) that can inform how you structure and package your own skills, but it won’t solve the contract/boundary problems you’ve been working on.[1]

Here’s the breakdown.

***

## What this repo is

From the ecosystem overview that mentions it explicitly:

- `levnikolaevich/claude-code-skills` is a **GitHub plugin marketplace repo** for Claude Code, exposing **“seven installable plugins covering Agile workflow, audits, and bootstrapping.”**[1]
- It follows the standard pattern:
  - A `.claude-plugin/marketplace.json` manifest.
  - One or more plugin bundles, each grouping multiple skills.
  - Each skill is a folder with a `SKILL.md` plus optional scripts and references.[1]

So it’s:

- Not a mega‑collection like `alirezarezvani/claude-skills` (hundreds of skills).[1]
- More of a **curated, opinionated set of workflow skills** around Agile, audits, and initial project setup.[1]

***

## How it can help you

Given your goals (SDLC skill topology, contract clarity, multi‑agent coders):

### 1. Packaging and marketplace pattern

It’s a good **concrete example** of:

- How to structure a repository as a Claude Code plugin marketplace (`marketplace.json`).[1]
- How to ship multiple related skills as a “plugin” with one install command.
- How to name and describe skills so they’re discoverable and trigger reliably.

This matters if you want to:

- Turn your SDLC skill topology into **installable bundles** (e.g. `cc-skills-sdlc`).
- Maintain clear separation between analysis surfaces, SDLC surfaces, and lab/experimental skills, the way your audit already describes.[2]

### 2. Workflow skills for Agile/audit

Because the repo focuses on:

- **Agile workflow** (likely planning/triage/board management),
- **audits** (codebase, process, or quality audits),
- **bootstrapping** (project setup / scaffolding),[1]

you can:

- Inspect how it defines **phased workflows** and roles inside skills.
- Compare its audit/Agile skills to how you’re thinking about `IncidentFindings`, `ActionPlan`, and `ReadinessReport`:
  - Does it separate evidence vs decision?
  - How does it name triggers and outputs?
  - How does it document “when to use this skill”?

This gives you **another design pattern** to contrast against your refactor spec and the critique you showed me.

### 3. Cross‑checking your SDLC ideas

Because this repo has a “full delivery workflow” focus and is cited in “Top Claude Skills for developers,” it can act as a sanity check:[3]

- How many surfaces do they expose publicly?
- How do they balance planning vs execution vs review?
- How do they avoid overlapping responsibilities?

You won’t copy it wholesale, but you can use it to ensure your topology is **not wildly off** compared to what other practitioners find usable.

***

## Where it is less useful for you

- It does **not** implement the kind of fine‑grained SDLC contracts you’re designing (SituationReport vs IncidentFindings vs ActionPlan vs DecisionRecord, etc.).[2][1]
- It is **not** a multi‑agent SDLC framework like ALMAS or GSD; it’s just a set of skills GitHub‑packaged for Claude Code.[4][5][6]
- It won’t resolve your current issues:
  - recap vs debrief vs rns boundary drift,
  - readiness vs red‑team separation,
  - artifact schema and provenance.

So it’s **not** the answer to your SDLC topology problem. It’s a **reference and scaffold** for:

- skill packaging,
- workflow skill design,
- small marketplace structure.

***

## How I’d actually use it

Given your time and ROI focus, I’d suggest:

1. **Clone and inspect it once**, focusing on:
   - Its `marketplace.json` (how bundles and skills are declared).[1]
   - SKILL.md files for Agile and audit skills—what contracts they claim, how they name triggers.[1]

2. **Lift the useful bits**:
   - Marketplace structure and naming practices for your own `cc-skills-sdlc` bundles.
   - Any audit/Agile patterns that align with your `IncidentFindings` / `ActionPlan` thinking.

3. **Do not treat it as authoritative topology**:
   - Use it as *another data point* when you evaluate your own skill set, not as a template to conform to.

So: **useful as a small, concrete example repo and marketplace scaffold; not a core architectural guide for your SDLC design.**[1]

If you want, I can propose a “minimal SDLC plugin marketplace layout” for your environment, using this repo and `anthropics/skills` as references (e.g. plugin bundles like `analysis`, `sdlc-core`, `lab`, with clear install commands and SKILL.md patterns).

## Human

Best practices for structuring private skill repos

## Assistant

For private skill repos, the best practices are less about “how many folders” and more about **clarity of contracts, separation of concerns, and governance**—especially given your SDLC goals and long‑lived sessions.[1]

I’ll keep this focused and concrete.

***

## 1. Separate plugin namespaces by *role*, not by topic

From your own environment and the transcript, you already have meaningful plugin groupings: analysis, SDLC, architect, lab, “thinking” skills.[1]

Best practice is to make those **intentional namespaces**:

- `cc-skills-analysis`: state synthesis, debrief, friction, incident review.[1]
- `cc-skills-sdlc`: recap, plan/prioritization, readiness, impact, outcome.
- `cc-skills-architect`: design, architecture, refactors.
- `cc-skills-lab`: experimental or prototype skills.[1]

Each plugin:

- Has a clear **mission statement** in its `CLAUDE.md` / `plugin.json` (“analysis surfaces”, “SDLC loop”, etc.).[1]
- Contains skills that share a **contract style** and artifact expectations.

This makes it much easier to see “which plugin should own this new skill?” and reduces accidental overlap.

***

## 2. Use SKILL.md contracts and artifacts as the **primary interface**

Private repos tend to drift when SKILL.md becomes narrative instead of a contract.

Best practice:

- Every skill folder has a **SKILL.md** that clearly defines:
  - Purpose.
  - Input assumptions.
  - Output artifact (including structure).
  - Modes (if any).
  - What it **must not** do (e.g. “no prioritization”, “no implementation”).[1]
- Internal Python/scripts libs implement that contract; they don’t define it.
- Artifact contracts live in SKILL.md and in a small shared docs file (e.g. `docs/contracts/*.md`) so your fleet of skills share a common vocabulary.[1]

For your SDLC topology, that means codifying:

- `SituationReport`, `IncidentFindings`, `ActionPlan`, `DecisionRecord`, `ReadinessReport`, `ImpactAssessment`, `OutcomeReport` as **artifact schemas** referenced from SKILL.md.[1]

***

## 3. Keep evidence vs decision vs execution **separated** across skills

Your transcript already stresses this:[1]

- Evidence surfaces: recap, debrief, impact.[1]
- Decision renderer: RNS/plan.[1]
- Execution: `/go` or task‑specific implementation skills.

Repo structure should reflect that:

- Analysis plugin: skills that **only** produce evidence artifacts.
- SDLC plugin: skills that **only** render decisions or perform readiness gates.
- Implementation plugin(s): skills that actually change code or systems.

This reduces “mixed surfaces” like a single skill doing recap, debrief, and prioritization in one go, which your debrief chain currently tends toward.[1]

***

## 4. Explicit lifecycle: `active | alias | deprecated | internal`

The transcript notes issues with deprecated skills (GTO, DNE) remaining present as husks or cache‑only state.[1]

Best practice:

- In your plugin manifest (or a small registry file), track **status** per skill:
  - `active`: canonical entry point.
  - `alias`: routes to another skill/mode.
  - `deprecated`: present only for backward compatibility; SKILL.md spells this out.
  - `internal`: not meant for direct invocation (engines, adapters).[1]
- Use this to:
  - Prevent “zombie front doors” like `/gto` surviving in cache.[1]
  - Make it clear which skills are safe to call and which exist only for reuse.

***

## 5. Route overlap into modes or shared engines, not duplicate skills

Your own consolidation work (folding `/retro`, `/top-problems`, DNE, GTO) shows the pattern you want:[1]

- When two skills do similar work:
  - Decide which one owns the capability.
  - Turn the other into an alias or mode on the canonical skill.
  - Move shared logic into a common lib/engine.

Examples from your SDLC context:

- `/friction` and `/behave` as **debrief modes** instead of standalone surfaces.[1]
- `/recap check` as a **mode or alias** onto a canonical readiness skill.[1]
- `/gto` detectors as internal engine used by `/debrief gaps`, not a public skill.[1]

This keeps the public surface area small while still letting you reuse specialized detectors.

***

## 6. Tests for routing and non‑recursion **inside the repo**

The transcript explicitly calls for:

- Routing tests: “transcript-mining → debrief”, “what should we do next on structured findings → RNS”, etc.[1]
- Non‑recursion tests: RNS must not re‑enter debrief, recap check must not become a second prioritizer.[1]

Best practice for private repos:

- Each plugin has a `tests/` directory that includes:
  - Contract tests for key skills (input/output shape, “must not” behavior).[1]
  - Routing tests that verify command phrases go to the right skill.
  - Non‑recursion tests that ensure skills don’t loop through each other improperly.[1]

Given your multi‑plugin structure, these live **inside each repo**, not just in a global “skill guard.”

***

## 7. Document canonical flows and packets in `docs/`

Your transcript sketches flows like:[1]

```text
work → recap → debrief (when causes/gaps matter)
     → RNS → human selection → implementation
     → recap check
```

Best practice is to:

- Maintain a `docs/` folder per repo (or shared) with:
  - Flow diagrams (Mermaid, text) for canonical loops.
  - Packet contracts (HandoffPacket, FindingPacket, ActionPlan).[1]
  - A claim ledger for key design decisions (similar to what you already do).[1]

This makes the repo self‑explanatory for future you and any agents that need to reason about the system.

***

## 8. Start with **few public surfaces**, many internal capabilities

The other LLM’s critique you shared is relevant here: don’t make every conceptual step a public command.[1]

In repo terms:

- Public SKILLs:
  - A handful of well‑named surfaces per plugin (e.g., `recap`, `debrief`, `rns`, `check`, `design`).
- Internal SKILLs / libs:
  - Specialized detectors, impact analyzers, outcome evaluators, etc., invoked internally.

You then expose new capabilities publicly **only** when:

- You frequently invoke them independently.
- They have clearly distinct inputs and authority.
- They produce a durable artifact consumed elsewhere.[1]

***

Given your current repos, the single highest‑value best practice to implement next is: add a **status field** and minimal artifact schemas to each private skill repo, then start routing overlap into aliases/modes on canonical surfaces instead of adding new skills. That will make the future SDLC refactor much cheaper.

Would you like a concrete repo layout template (directories + files) for `cc-skills-sdlc` that applies all of the above?
