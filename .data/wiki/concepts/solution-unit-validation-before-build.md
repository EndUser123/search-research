---
title: Solution-unit validation before build engagement
slug: solution-unit-validation-before-build
tags: [decision-pattern, alternatives-gate, generalization, solution-framing, anti-premature-build]
status: active
verification: session-derived
confidence: 0.86
source_skills: [tp]
researched: 2026-08-07
relations:
  - "[[problem-first-systems-decomposition]]"
  - "[[solution-first-before-root-cause-overengineering-failure]]"
  - "[[inference-chains-bare-numbers-destructive-write]]"
  - "[[overnight-controller-and-autonomy-tier-patterns]]"
---

# Solution-unit validation before build engagement

## The pattern (one sentence)

Before engaging thoroughly with a proposed build, test whether the
**proposed unit** (the specific thing being proposed) is the right unit —
or a special case of a more general, cheaper, more reusable capability.

## Why it needs to be explicit

Three adjacent decision-gates already exist in this workspace, and none
of them covers this case. The gap is specific:

| Existing gate | What it covers | What it misses |
|---|---|---|
| Problem-first decomposition | Decompose the *problem* before solving | Doesn't validate the *solution's unit* |
| Alternatives before architectural implementation | Emit ≥2 options + selection criterion | Emits options **within the proposed framing** — doesn't question the framing |
| Refactor dismissal gate | Don't dismiss refactors too fast | Opposite direction: don't *build* the special case too fast |

The Alternatives Gate is the closest neighbor, but it fires *inside* the
proposal's frame: "given we're building an overnight controller, here are
the options." It never asks "is 'overnight controller' the right unit?"
That question is the whole value of this pattern.

## The five questions (the technique)

Ask these **before** generating alternatives inside the proposal's framing.
If the answer to #3 is "yes," reframe to the general envelope before
engaging further.

1. **Why do we need the specific mechanism?** Challenges the load-bearing
   mechanism (the "task scheduler," the "new controller"). Often the
   mechanism is only needed for the special case.
2. **New skill/system or addition?** Challenges the "new build" framing.
   If the reusable core is already spread across existing skills, the
   answer is "addition," not "new."
3. **Reusable for non-special-case situations?** The generalization test.
   If the answer is yes, the unit is wrong — reframe to the general envelope.
4. **Usable during the normal case?** The spectrum test. If the capability
   is the same at every autonomy level, the special case is just one point
   on a spectrum, not a separate thing.
5. **Usable on a regular basis?** The frequency test. If the special case
   is rare and the general case is frequent, build the general case.

## The key structural point

This technique worked in its origin session because **the operator asked
the questions.** The agent did two research passes without asking them.
The pattern's value depends on the questions firing **mechanically at
proposal-evaluation time** — not on the agent remembering to ask them.

This is the same structural lesson as `[[evidence-first-default-and-needless-confirmation]]`
and the theatrical-contrition pattern: prose rules for cognitive moves
have a ~50% compliance ceiling under session pressure. The fix is
mechanical: the questions fire because a gate requires them, not because
the agent volunteers them.

## Reference incident (2026-08-07)

Operator asked "what can we do to work overnight on yt-is?" A sibling
session proposed a "bounded overnight controller": Task Scheduler
launcher, manifest-driven controller, morning receipt pipeline. The
agent engaged with the proposal *as framed* for three turns — two
research passes, external grounding, a wiki concept, all thorough, all
on the wrong unit.

The operator asked the five questions. The answers showed the overnight
controller was a special case of a bounded-run envelope; the envelope
was cheaper, reusable across daytime parallel waves (the frequent case),
and required only (a) a manifest table in AGENTS.md and (b) per-commit
confidence in `/close`. The expensive overnight-specific build
(scheduler + controller + morning-receipt pipeline) was deferred
entirely — and would only become worth building if the operator
genuinely hits a night wanting overnight yt-is progress.

The three-turn detour was recoverable (research became the design
vocabulary for the envelope), but the unit error cost real tokens and
time. The structural fix is to fire the five questions *before* the
research pass, not after.

## How it generalizes

The pattern is not specific to overnight work. It applies whenever a
proposal arrives shaped as a specific build:

- "Build a hook that blocks X" → is "a hook" the right unit, or is it
  "a gate in the existing dispatch chain"?
- "Create a new skill for Y" → is "a new skill" the right unit, or is it
  "a mode on an existing skill"?
- "Write a script that does Z" → is "a script" the right unit, or is it
  "an extension of the existing pipeline"?
- "Add a wiki concept for W" → is "a wiki concept" the right unit, or
  is it "a row in an existing concept's table"?

In each case the proposal may be right — but the questions must fire
before engagement, or the agent will research/build inside a frame that
might be a special case.

## Distinction from adjacent patterns

- **vs Problem-first decomposition:** that validates the *problem's*
  boundaries. This validates the *solution's* boundaries. Both run; the
  problem decomposition does not substitute for the unit check.
- **vs Solution-first-before-root-cause:** that catches the agent jumping
  to "build a system" before checking if a missing instruction explains
  the behavior. This catches the agent engaging with the right general
  direction but the wrong *specific unit* within it.
- **vs Abstraction-level check (in /tp domain 5a):** that asks "is there
  a higher abstraction that collapses the work 10×?" This asks "is the
  proposed build a special case of something more general?" They
  compose: 5a looks upward (higher abstraction), this looks sideways
  (general envelope of which the proposal is one instance).

## Where it lives mechanically

- **ALTERNATIVES GATE** (AGENTS.md): runs the unit-test as a sub-check
  *before* emitting options. This makes it fire before every build wave.
- **/tp Step B domain 5** (protocol.md): runs the unit-test as a
  sub-question when critiquing proposals. This makes it fire during
  proposal review.
- **This concept:** the durable reference both point to.

## Falsifier

This pattern is wrong if, within 6 months:
- The five questions fire on every proposal and consistently produce "no,
  the proposed unit is correct" (the test has no signal).
- The test fires and produces the general-envelope reframe, but the
  general envelope is actually worse (less clear, more coupling, etc.)
  than the special case would have been.
- The operator reports the questions are noise on routine work and
  should be gated to architectural decisions only (calibration miss).

If any appears, iterate: narrow the trigger to reversibility ≥1.75 or
to "new skill/system" proposals only.
