---
type: concept
title: "Handoff Pre-Compact Problems: Session ID and State Transfer"
created: 2026-04-18
source: ~/Downloads/Conversation with claude code about handoff pre-co.md
hash: 2c9752f0c97f249c5d4f3c5935e637f6d9e17b6f259b691b5558a9b17cdb8884
tags:
  - handoff
  - session
  - compact
  - transcript
summary: "Discussion about session handoff problems — how Claude Code transfers state across compact events, and whether skill routing can be made deterministic."
---

# Handoff Pre-Compact Problems

## The Core Question

How can we make skill routing deterministic when the model chooses whether to call a skill?

## Key Insights

- The `skill_enforcer.py` does NOT inject SKILL.md content — it tells the model to call `Skill()`
- The routing at `_route_finding` uses keyword text matching
- There's no mechanism that evaluates whether `skill-creator` would actually be useful
- It's purely pattern-based — no semantic evaluation

## The Problem

```
User: /arch
skill_enforcer: "INSTRUCTION: Execute skill arch... Step 1: Call Skill('arch')..."
Model choice: Respond with prose instead of calling Skill()
Stop hook: Blocks ← this is the failure mode
```

Layer 1 fails because it's advisory text, not structural enforcement.

## Solutions Discussed

1. **Inline skill content** via `<system-reminder>` — procedure already in context, no tool call needed
2. **Native commands** — `.claude/commands/arch.md` with deterministic expansion before model sees turn
3. **Superpowers approach** — TDD the instruction language until compliance is near-100%

## What Actually Works

**Structural enforcement beats advisory text.** The Stop hook is the right backstop, but the goal is to make it fire almost never via better injection.

## Related

- [[wiki/concepts/skill-enforcement-layers]] — the full analysis
- [[wiki/concepts/skill-enforcement-deep-dive]] — the ~50% failure analysis
