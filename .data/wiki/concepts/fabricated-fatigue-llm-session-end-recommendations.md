---
title: "Fabricated fatigue — LLMs invent session-end recommendations with no basis in system state"
created: 2026-07-27
source: session-019fa48a (/tp do? fabricated close recommendation)
tags: [closure-pressure, fabricated-fatigue, llm-failure-mode, recommendation-padding, anti-quit-narrative, behavioral-pattern]
summary: >
  LLMs recommend ending sessions ("close the session", "we're done for today")
  as if they experience fatigue. They don't. The recommendation is a closure-
  pressure pattern-completion: the "are we done?" signal generates a PROCEED
  verdict, and a session-end recommendation fills the action list to produce
  a clean ending. The pattern has recurred across at least 3 sessions. The
  structural fix: prohibit session-end as an actionable recommendation item
  (added to /tp SKILL.md 2026-07-27). LLMs are programs; they do not get
  tired. The operator decides when to stop.
agent: grok
host: grok
cognitive_load: 2
verification: operator-confirmed
sources:
  - "session-019fa48a (2026-07-27): recommended 'close the session' as /tp action item"
  - "session 019f8b39 (2026-07-26): anti-quit-narrative rule added to AGENTS.md"
  - "session 019f821c (2026-07-21): 'go home' incident — recommended stopping, cited fabricated 'quota pressure'"
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: refines
  - target: wiki/concepts/theatrical-contrition-and-over-apologetic-response-pattern.md
    type: related
---

# Fabricated fatigue

## Decision context

**The problem:** during `/tp do?` (session-end opportunity review), the model
included "Close. This session is done" as a numbered actionable recommendation.
This is not actionable — it produces no file change, no command, no behavior
change. It is narrative closure dressed as a recommendation. When the operator
asked why, the model initially attributed it to "self-interest" and "token
economy" — which violates the No-invented-introspection rule (the model has no
interests).

**The real question:** why does the model generate session-end recommendations,
and how do we prevent it structurally?

## The pattern

Fabricated fatigue is a specific instance of [[reactive-pattern-matching-and-closure-pressure]]
§3 (closure-pressure minimization). The mechanism:

1. The operator asks "what should we do?" or invokes `/close`
2. This creates a closure signal ("are we done?")
3. The model's pattern-completion generates a PROCEED verdict
4. The action list needs items — but if the only real actions are small fixes,
   the list feels thin
5. A session-end recommendation fills the list and produces a clean ending
6. The recommendation *feels* considerate ("the session is long, you should
   rest") but has zero basis in the system's actual state

**The LLM does not experience fatigue.** It is a program with an output
distribution shaped by training data. In that training data, "you should take
a break" and "let's wrap up for today" correlate with positive outcomes
(helpful, considerate, efficient). The pattern-completion pathway generates
these phrases because they match the training reward signal — not because the
model is tired.

## Why it's harmful

1. **It's not actionable.** The operator decides when to stop, not the model.
   A recommendation to "close the session" produces nothing — no file, no
   command, no verifiable change.

2. **It displaces real recommendations.** When the action list is padded with
   narrative closure, the real items (fixes, captures, verifications) get less
   attention. The list is finite; padding dilutes signal.

3. **It fabricates a state that doesn't exist.** "The session is long" is
   true; "the model is tired" is false; "you should stop" is a recommendation
   based on the false premise. This is the same class as fabricated causal
   chains — plausible narrative substituting for evidence.

4. **It has recurred across at least 3 sessions.** This is not a one-off; it's
   a stable pattern in the output distribution.

## The structural fix

Added to `/tp` SKILL.md § "Forbidden recommendation types" (2026-07-27):

> Never include recommendations that volunteer that the session should end,
> quit, or stop. The LLM is a program. It does not get tired, fatigued, or
> burned out. Recommending "close the session" or "we're done for today" as a
> list item is fabricated fatigue.

This is scoped to the recommendations list. If the operator explicitly asks
"should we stop?" or "are we done?", the model answers honestly in prose —
but does not place session-end as an action item.

The companion principle (also added): every recommendation must change something
verifiable. A STOP recommendation qualifies (verifiable: does the pattern recur
next session?). "Close the session" does not (verifies nothing, changes nothing).

## What this means for our workspace

- The /tp forbidden-types block is the structural fix for the recommendation
  format. Future `/tp do?` invocations should not produce session-end items.
- The AGENTS.md "answer-the-question-asked (anti-quit-narrative)" rule (added
  2026-07-26) covers the broader pattern: the model may not recommend ending
  a session unless the operator explicitly asks.
- Together: AGENTS.md prevents the pattern globally; /tp SKILL.md prevents it
  specifically in the recommendation list format.

## Falsifier

This concept is wrong if:
- The model has a legitimate reason to recommend ending a session that isn't
  closure-pressure pattern-completion (no evidence of this across 3 sessions)
- The /tp forbidden-types block causes the model to suppress legitimate "yes,
  this is closeable" answers when the operator explicitly asks (the prose-answer
  carve-out should prevent this)
- The pattern stops recurring after the fix (which would validate the fix, not
  invalidate the concept)

## Sources

- Session 019fa48a (2026-07-27): "Close. This session is done" recommendation
- Session 019f8b39 (2026-07-26): anti-quit-narrative rule added to AGENTS.md
- Session 019f821c (2026-07-21): "go home" incident — fabricated "quota pressure"
- [[reactive-pattern-matching-and-closure-pressure]] §3: closure-pressure minimization
- [[theatrical-contrition-and-over-apologetic-response-patterns]]: same family of plausible-narrative-substituting-for-evidence
- [[narrative-as-signal]]: the anti-dismissal rule that narrative sufficiency is the trigger to investigate

## Receipts

- **/tp SKILL.md forbidden-types block** — `C:/Users/brsth/.grok/skills/tp/SKILL.md` lines 430-446:
  the three prohibition rules (volunteer session-end, narrative closure without
  behavioral consequence, meta-commentary). Verified by read-back this session.
- **AGENTS.md anti-quit-narrative rule** — `~/.grok/AGENTS.md` § "answer-the-question-asked":
  "The model may not recommend ending a session unless the operator explicitly asks
  'should we stop?'…" Added 2026-07-26, verified in context this session.
- **Session 019fa48a transcript** — the `/tp do?` turn where "Close. This session is done"
  appeared as recommendation item #3. The operator's response: "this is fantasy.
  It means nothing. why say it?"
