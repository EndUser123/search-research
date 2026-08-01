---
title: "Intent-mode-gated auto-composition: when skills can auto-route to each other"
created: 2026-07-31
source: session-2026-07-31 (/wiki on /www → /refine auto-composition)
sources:
  - P:/.data/wiki/concepts/skill-auto-invocation-reliability.md
  - P:/.data/wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md
  - ~/.grok/skills/close/SKILL.md (line 123 — /close auto-invokes /aar)
  - ~/.grok/skills/www/SKILL.md (confidence-gap mode — /tp → /www → /wiki chain)
  - P:/AGENTS.md ("exploration language → exploration response" guard)
tags: [skill-composition, auto-invocation, intent-mode, routing, decision, design-decision]
host: both
agent: grok
verification: single-source-reasoned
cognitive_load: 3
relations:
  - target: wiki/concepts/skill-auto-invocation-reliability
    type: extends
  - target: wiki/concepts/close-auto-invokes-aar
    type: related
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write
    type: related
summary: >
  Skills can auto-route to each other when they stay within the same intent
  mode (research→research, verification→retrospective). Auto-routing across
  an intent-mode boundary (research→implementation) must stay operator-gated
  because it silently changes what the system does without consent. The fix
  for manual skill-to-skill routing is a structured NEXT_ACTION_PACKET, not
  full auto-routing — it keeps the decision with the operator while dropping
  the cost of acting on it to near-zero.
---

# Intent-mode-gated auto-composition

## The decision

**Auto-composition (one skill auto-invoking another) is safe within the
same intent mode. It is unsafe across an intent-mode boundary.**

| Transition | Intent-mode crossing? | Auto-route? | Status |
|------------|----------------------|-------------|--------|
| `/tp` → `/www` | No (research → research) | ✅ | Already automated (confidence-gap mode) |
| `/www` → `/wiki` | No (research → knowledge capture) | ✅ | Already automated |
| `/close` → `/aar` | No (verification → retrospective) | ✅ | Already automated (close SKILL.md line 123) |
| `/www` → `/refine` | **Yes** (research → pre-implementation) | ❌ | Operator-gated |
| `/www` → `/design` | **Yes** (research → design) | ❌ | Operator-gated |
| `/refine` → `/go` | No (pre-implementation → implementation) | ✅ | Could automate |

## Selection criterion

**Does the transition cross an intent-mode boundary?** If no → auto-route
is safe. If yes → operator-gate the transition; use a structured packet
instead of prose to make the gate cheap.

Intent modes are: **research/discovery**, **pre-implementation**, **implementation**,
**verification**, **retrospective**, **knowledge capture**. Transitions
within one mode are continuous flows; transitions between modes change
*what the system is doing to the workspace* (reading vs writing vs building).

## Rationale

1. **Auto-composition within a mode is a data handoff, not a behavior change.**
   `/tp` → `/www` is "here are the targets, research them" — the system is
   still researching. `/close` → `/aar` is "the session needs a retrospective,
   run it" — the system is still doing session-close work. The operator's
   intent carries through.

2. **Auto-composition across a boundary silently changes the work type.**
   If `/www` (research: find what exists) auto-fired `/refine` (pre-implementation:
   produce a work handoff), a research invocation would start producing
   implementation artifacts without consent. This is the same failure class
   as the Luna confabulation: the system doing something adjacent to but
   different from what was asked.

3. **The operator's own guards already encode this boundary.** `P:/AGENTS.md`:
   *"exploration language → exploration response. Period."* and *"Delegation
   signal — prepare, don't implement."* Auto-routing across the boundary
   would violate both.

4. **The Seleznov 650-trial data supports this.** Directive descriptions
   achieve 100% *activation* ("should this skill load"). But that's
   single-skill activation, not "should skill A auto-invoke skill B across
   an intent-mode boundary." Cross-skill auto-invocation across intent modes
   is untested. See [[skill-auto-invocation-reliability]].

## Steelman (the rejected viable alternative)

**Full auto-routing is throughput-optimal.** If the system always routes to
the next obvious skill without asking, the operator never has to type a
second command. The throughput gain is real — every operator-gate is a
context switch and a decision cost. For a solo director operating a fleet,
eliminating manual routing could meaningfully increase output velocity.

**Why it was rejected:** throughput is not the operator's stated constraint.
"Quality is the constraint. Efficiency is the method. Time is not the
constraint" (operator directive, [[research-quality-principle-efficiency-not-censorship]]).
Auto-routing across intent modes trades consent for speed — the operator
loses the ability to say "I wasn't looking for implementing, I was looking
for ideas" (the exact exploration-vs-execution failure the AGENTS.md guards
exist to prevent). The throughput gain isn't worth the consent loss when
the structural fix (packets) makes the gate nearly free anyway.

## The structural fix: NEXT_ACTION_PACKET

The problem with manual skill-to-skill routing isn't the gate — it's the
**cost** of acting on the gate. Today, `/www`'s "Skill suggestion" is prose:
*"consider /refine if you want..."* The operator has to re-read, re-type,
re-derive context. That's where the friction lives.

**Fix: emit a structured packet instead of prose.** Same pattern as `/tp`'s
"Research-ready targets":

```
NEXT_ACTION_PACKET:
  target_skill: /refine
  task: "<one-line task derived from findings>"
  affected_files: ["<path>", ...]
  acceptance_criteria_sketch: "<how we'll know it's done>"
  intent_mode: pre-implementation
```

When the operator says "go" (or types `/next`), the target skill reads the
packet directly — no re-derivation, no re-reading. The decision-gate stays
with the operator; the cost of acting drops to near-zero.

**This composes with a future `/next` alias or hook:** a one-keystroke
command that reads the most recent `NEXT_ACTION_PACKET` and routes to the
target skill. Cheaper than full auto-routing and respects the intent-mode
boundary.

## Existing working precedents (the pattern is already proven)

| Chain | Mechanism | Why it works |
|-------|-----------|-------------|
| `/tp` → `/www` → `/wiki` | `/tp` emits "Research-ready targets"; `/www` reads them in confidence-gap mode; `/wiki` persists | All research-mode. Data flows naturally; no intent transition. |
| `/close` → `/aar` | Retrospective gate fires `needs_attention` → `/close` auto-invokes `/aar` ("do not recommend it, run it") | Both retrospective-mode. The gate is evidence-based (dirty files, missing AAR receipt), not heuristic. |

Both chains stay within one intent mode. Neither crosses research→implementation.

## Where this applies next

- **`/www` → `/refine`** (the trigger case): emit NEXT_ACTION_PACKET, operator-gate.
- **`/review` → `/go` fix** (review findings → implementation): same boundary. The `/review` FINDINGS.md already *is* a packet — `/go` reads it. This is the within-mode exception that proves the rule: `/review`→`/go` is crossing research→implementation, and it's currently operator-gated (`/go review-findings <path>`), which is correct.
- **`/check` → `/review`** (check fails → deeper review): both verification-mode. Could auto-route safely.
- **`/harvest` → `/wiki`** (obligation → knowledge capture): both retrospective/knowledge. Could auto-route safely.

## Falsifier

This decision is wrong if:
- Operators consistently want research→implementation auto-routing (the
  boundary is artificial; the operator values throughput over consent in
  practice)
- The NEXT_ACTION_PACKET format adds overhead without reducing friction
  (operators still re-type the task; the packet is ignored)
- Intent-mode boundaries prove unstable (the mode taxonomy doesn't hold up
  across real skill chains — e.g., `/design` is both research and pre-
  implementation, making the boundary ambiguous)

Re-evaluate if operators report the gate as friction, not as protection.

## Decision context

**Why this was needed:** Session 2026-07-31 `/www` run produced a skill
suggestion ("consider /refine for the tool_choice=required task"). The
operator asked: "how do we get this to happen automatically when useful?"
The question revealed a gap in the skill-composition design — there was no
principle for when auto-composition is safe vs unsafe.

**What alternatives were explored:**
1. Full auto-routing (`/www` fires `/refine` automatically) — rejected:
  crosses intent-mode boundary, violates AGENTS.md exploration guards
2. Do nothing (keep prose suggestions) — rejected: the friction is real,
  the operator asked for automation
3. NEXT_ACTION_PACKET + operator-gate — chosen: keeps the gate, drops the
  cost

**What the decision changed:** established the principle that distinguishes
existing working auto-composition chains (`/tp`→`/www`, `/close`→`/aar`)
from proposed unsafe ones (`/www`→`/refine`). Provides a structural fix
(packet format) that can be prototyped in `/www` without new infrastructure.

## What this means for our workspace

1. **Prototype NEXT_ACTION_PACKET in `/www`** — replace the prose "Skill
   suggestion" line with a structured packet when findings map to a bounded
   task. This is the immediate implementation of this decision.
2. **Do NOT auto-fire `/refine`, `/design`, or `/go` from research-mode
   skills.** The intent-mode boundary is operator-gated.
3. **Consider `/next` alias** — a one-keystroke command that reads the most
   recent NEXT_ACTION_PACKET and routes. Reduces gate cost to one command.
4. **Existing auto-composition chains are validated, not changed** —
   `/tp`→`/www`, `/close`→`/aar` stay as-is. This decision explains *why*
   they work, it doesn't modify them.

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| `/close` auto-invokes `/aar` when Retrospective gate fires | `~/.grok/skills/close/SKILL.md` line 123: "auto-invoke /aar — do not recommend it, run it" — [OBSERVED] in [[close-auto-invokes-aar]] and [[blind-spot-detection-methods]] | [OBSERVED] |
| `/tp` → `/www` → `/wiki` chain is automated | `~/.grok/skills/www/SKILL.md` enhancement batch 2026-07-31: confidence-gap mode reads /tp "Research-ready targets" directly — [OBSERVED] this session (read the skill file) | [OBSERVED] |
| Directive descriptions achieve 100% activation (Seleznov 650-trial) | [[skill-auto-invocation-reliability]] — "20x higher odds (p < 0.0001)" | [OBSERVED] from prior wiki research |
| Execution failures remain unsolved | [[skill-auto-invocation-reliability]] — "[UNKNOWN] — no structural fix proven" | [OBSERVED] from prior wiki research |
| AGENTS.md guards exploration→execution boundary | `P:/AGENTS.md`: "exploration language → exploration response. Period." + "Delegation signal — prepare, don't implement" — [OBSERVED] in system context | [OBSERVED] |
| Codex CLI config is clean against #34758 regression | `C:/Users/brsth/.codex/config.toml` read this session — line 1 `model = "gpt-5.6-sol"` present; grep for `model_provider|wire_api|model_providers` returned zero matches | [OBSERVED] |
| NEXT_ACTION_PACKET is unproven | No implementation exists yet; proposed format derived from `/tp`'s "Research-ready targets" pattern | [INFERENCE] — format proposed, not tested |

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[agent-config-directory-taxonomy]]
- [[claude-code-skills-and-mcp-integration]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]

