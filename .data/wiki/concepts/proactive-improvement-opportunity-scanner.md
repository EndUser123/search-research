---
title: "Proactive improvement opportunity scanner — the missing capture layer"
created: 2026-07-31
source: session-019fb3a8 (/tp on what skills capture system improvements)
tags: [skill-design, improvement-scanner, knowledge-capture, close-enhancement, friction, system-improvement, proactive-capture, session-review]
agent: grok
host: both
cognitive_load: 3
verification: workspace_verified
summary: >
  The fleet has reactive skills for specific capture categories (/aar for
  failures, /friction for interaction problems, /wiki for durable knowledge)
  but no proactive scanner that asks the comprehensive question: "what from
  this session, if captured, would make the system better and the operator
  love it more?" The gap is a new skill (/capture) invoked as a /close step
  that mechanically scans the session transcript for 6 categories of
  improvement opportunity and routes each to the right persistence mechanism.
relations:
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture
    type: extends
  - target: wiki/concepts/improvement-surfacing-fleet-fragmentation-routing-and-meta-improvement
    type: related
  - target: wiki/concepts/research-to-execution-ratio-self-reinforcing-pattern
    type: related
---

# Proactive improvement opportunity scanner

## Decision context

**The problem:** The operator asked "what skills tell us what we should capture so the system can get better?" The answer revealed a gap: every existing capture skill is either reactive (fires when invoked), narrow (covers one category), or behavioral (depends on the agent remembering). None asks the comprehensive question proactively.

**What alternatives were explored:**
- Making /wiki more proactive (WIKI: markers) — proven unreliable under closure pressure this session
- Adding more gates to /close — too complex, /close already has 14 gates
- Making /aar broader — /aar is backward-looking (failures), not forward-looking (improvements)
- Making /friction broader — /friction covers interaction friction but not architectural decisions, system gaps, or experience improvements

**What the research/analysis changed:** Identified that the gap is a distinct capability — a **session-level improvement opportunity scanner** — that belongs as a separate skill invoked by /close, not as modifications to existing skills. The separation of concerns keeps /close stable while allowing the scanner to evolve independently.

## The 6 categories of improvement opportunity

The scanner looks for these 6 categories in the session transcript:

### 1. Operator corrections
**Signal:** The operator corrected the agent's behavior, framing, or approach.
**What to capture:** The correction + what the agent should have done instead.
**Persistence target:** AGENTS.md rule, SKILL.md update, or wiki concept (operator-correction trigger type).
**This session example:** "Coverage needs to be meaningful, like mutation or behavioral" — corrected my shallow coverage gate. Should become durable knowledge about behavioral vs line coverage.

### 2. Repeated manual steps (friction)
**Signal:** The operator had to manually trigger something the system could have done itself.
**What to capture:** The friction point + the automation that would eliminate it.
**Persistence target:** /friction fix, AGENTS.md rule, or hook.
**This session example:** I recommended /refactor but should have known /go refactor exists — a routing gap the operator had to correct manually.

### 3. Architectural decisions
**Signal:** A design choice was made with rationale and alternatives.
**What to capture:** The decision + rationale + rejected alternatives + falsifier.
**Persistence target:** Wiki concept (decision shape) or ADR.
**This session example:** Planner-executor split (refactor analyzes, go executes) — captured as wiki concept. But "behavioral tests not line coverage" and "spec verification always runs" were NOT captured.

### 4. System gaps
**Signal:** Something that should work but doesn't, or a capability that's specified but not verified.
**What to capture:** The gap + what fixing it would require.
**Persistence target:** Handoff (for next-session work) or skill improvement.
**This session example:** /ship Phase 3 doc-check is specified but we never verified it actually runs. This is a system gap that was noticed but not captured.

### 5. Near-miss failure patterns
**Signal:** Something almost broke but was caught in time, or a failure mode was identified that could recur.
**What to capture:** The pattern + what would prevent it next time.
**Persistence target:** Wiki concept (failure pattern type) or AGENTS.md rule.
**This session example:** The rollback receipt suggesting `reset --hard` — would have destroyed concurrent-session work if copy-pasted. Caught by /tp, but the pattern (dangerous rollback in receipts) wasn't captured as durable knowledge.

### 6. Experience improvements
**Signal:** Something that, if changed, would make the operator's experience smoother, faster, or more enjoyable.
**What to capture:** The improvement + the expected impact.
**Persistence target:** Skill improvement, friction fix, or AGENTS.md rule.
**This session example:** The operator's vision of /refactor as a comprehensive analyzer (not lightweight) — this reframing made the system better but wasn't proactively captured; it required operator pushback to surface.

## Why a new skill, not modifications to existing skills

| Option | Problem |
|---|---|
| Add to /close | /close already has 14 gates + complex scanner. Adding 6 more categories would make it unwieldy and hard to maintain. |
| Add to /aar | /aar is backward-looking (what went wrong). The scanner is forward-looking (what would make things better). Different cognitive modes. |
| Add to /friction | /friction covers interaction friction only. The scanner covers decisions, system gaps, near-misses, and experience improvements — much broader. |
| Add to /wiki | /wiki captures findings/decisions but doesn't scan for opportunities. It's a persistence mechanism, not a discovery mechanism. |
| New skill invoked by /close | Clean separation. /close calls it as a step. The scanner evolves independently. /close stays stable. |

## Design: the /capture skill

**Name:** `/capture` (or `/improve` — operator's choice)
**Invocation:** Automatically by /close as a mandatory step (like /aar)
**Can also be invoked standalone:** `/capture` mid-session when the operator senses value is being produced but not persisted

### What it does

1. **Scans the session transcript** for the 6 categories above using pattern matching + LLM judgment
2. **For each finding**, checks whether it's already captured (wiki concept exists, handoff exists, AGENTS.md rule exists)
3. **Routes uncaptured findings** to the right persistence mechanism:
   - Architectural decision → wiki concept (decision shape)
   - Operator correction → AGENTS.md rule or SKILL.md update
   - System gap → handoff (for next-session work)
   - Friction → /friction fix or hook
   - Near-miss → wiki concept (failure pattern)
   - Experience improvement → skill improvement
4. **Surfaces the list** before allowing close: "Before closing, here are N improvement opportunities from this session that aren't yet captured."

### Integration with /close

/close invokes /capture as a step between the AAR and the final summary:
```
/close
  → scanner (14 gates)
  → /aar (retrospective)
  → /capture (improvement opportunity scan)  ← NEW
  → summary
```

The /capture step is mandatory (like /aar) — it can't be skipped. But its findings can be deferred ("captured in handoff for next session") if the operator chooses.

### What makes this structural, not behavioral

The existing WIKI: marker system is behavioral — it depends on the agent remembering to mark findings during the session. This session proved it doesn't fire reliably: I produced 3+ durable findings that were never marked.

/capture is structural — it mechanically scans the transcript at close time and surfaces uncaptured findings. The agent doesn't need to remember to mark anything during the session; the scanner catches what was missed.

## Falsifier

This skill is wrong if:
- The scanner consistently finds zero opportunities (sessions aren't producing uncaptured value)
- The scanner consistently finds the same opportunities /aar already catches (redundant with /aar)
- The operator consistently skips /capture because it's too slow or noisy (over-firing)
- The findings captured by /capture are never used by future sessions (low signal-to-noise)

## What this means for our workspace

The fleet currently has strong **backward-looking** capture (what went wrong) but weak **forward-looking** capture (what would make things better). /capture fills this gap. It's the structural fix for the pattern this session demonstrated: valuable improvements were produced but not persisted, and only the operator's vigilance prevented knowledge loss.

The skill should be implemented with a `__lib/capture_scanner.py` that does the mechanical transcript scanning, similar to how /close uses `close_accounting.py`. The scanner identifies candidate findings; the LLM judges whether each is worth persisting and routes it.

## Sources

- Session 019fb3a8 (this session): 3+ findings not captured as wiki concepts despite being durable
- Operator vision: "what things, if we changed, would improve our outcomes and make the user love the system more?"
- AGENTS.md § "Decision-and-fix documentation rule" — existing WIKI: marker system (behavioral, proven unreliable)
- /close SKILL.md — architecture for how skills integrate as steps
- /friction, /aar, /debrief, /harvest, /dream, /skill-dev — existing capture skills that cover individual categories but not the comprehensive scan
