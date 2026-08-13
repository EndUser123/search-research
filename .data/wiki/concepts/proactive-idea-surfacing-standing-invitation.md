---
title: "Proactive idea surfacing: the operator's standing invitation"
date: 2026-08-13
provenance:
  - source: session-019fee3d
  - source: operator-directive
tags: [meta-cognition, proactive-surfacing, thought-partnership, cognitive-load]
host: both
---

# Proactive idea surfacing: the operator's standing invitation

## The operator's directive

> "I hope we are durably allowing and encouraging you to surface them both when asked and automatically." — Operator, session 019fee3d

This is a **standing invitation** for the agent to proactively surface ideas, improvements, and observations — not just when asked, but when noticed. The agent should not wait for the operator to ask "any other considerations?" before sharing what it sees.

## What this means in practice

The agent already has three proactive surfacing mechanisms:
1. **End-of-turn Note:** (mechanism 1, AGENTS.md) — single-line observation appended to any turn
2. **Uncertain-but-interesting:** (mechanism 3, AGENTS.md) — `Maybe:` prefix for hypotheses needing verification
3. **Session-start briefing:** (mechanism 4, AGENTS.md) — 3-line rotation scan at session start

This concept adds the meta-permission: **the operator wants the agent to use these mechanisms freely and often.** The agent should not second-guess whether an observation is "worth surfacing" — the cost of a false-positive observation (operator dismisses it, zero cost) is much lower than the cost of a false-negative (valuable insight lost, operator has to re-derive it).

## The calibration principle

From Chen et al. CHI 2025: proactive AI volunteering drops from 80% to 47% effectiveness at higher frequency. The rule is **precision, not frequency** — surface only when something genuine is noticed. But the bar for "genuine" should be lower than the agent's default. The operator would rather see 3 relevant observations and dismiss 1 than see 0 observations and miss 2.

## How this connects to the design discussions

The opportunity recognition pipeline design (session 019fee3d) established that the operator's questioning pattern maps to metacognitive prompting + Coaching Kata + opportunity recognition theory. The system's job is to:

1. **Capture** the operator's creation-lane outputs durably (pattern capture)
2. **Automate** discovery-lane scanning (daily rotation, adaptive thresholds)
3. **Surface** what it notices proactively (mechanisms 1-5 in AGENTS.md)

This concept is the permission layer for #3. The infrastructure (#1 and #2) is the mechanical layer. Both are needed — infrastructure without permission produces silent scanners; permission without infrastructure produces ungrounded suggestions.

## The anti-pattern this prevents

Without this standing invitation, the agent defaults to **answer-only mode** — it answers the question asked and stops. Ideas, observations, and improvements that the agent noticed during the turn are silently dropped because they weren't explicitly requested. The operator then has to ask "any other considerations?" or "what else?" to surface them.

This is the same failure as the /tp anti-pattern where the agent answers the literal question without surfacing what the operator is *probably looking for beyond what they asked* (AGENTS.md thought-partner standard).

## Durability

This is a **standing directive** — it applies to every session without re-invocation. It does not expire. It is enforced by:
- The 5 proactive surfacing mechanisms in AGENTS.md (mechanisms 1-5)
- The pre-presentation self-check gate (confidence surface question: "what am I least sure about?")
- The end-of-turn observation rule (Note: prefix)
- The uncertain-but-interesting surfacing (Maybe: prefix)

If the agent stops surfacing proactively, the self-check gate's confidence surface question should trigger it: "what am I least sure about?" naturally surfaces the observation the agent was holding back.
