---
title: "Multi-agent coordination blindness: working on shared skills without checking for active sessions"
created: 2026-08-09
source: session-019fe403 (worked on ship-py entire session without checking for sibling sessions)
tags: [multi-agent-coordination, behavioral-pattern, session-blindness, agents-md-rule, shared-workspace]
host: grok
agent: grok
verification: observed
relations:
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: instance-of — multi-terminal isolation is the invariant that was violated
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related — same class of multi-agent coordination failure
summary: >
  The agent worked on ship-py for an entire session (20+ commits) without
  checking whether another session was also working on ship-py. Another
  session had an active handoff targeting ship-py's review phase. The
  operator had to flag the collision risk. The AGENTS.md rules for checking
  active handoffs and sibling session activity exist for this exact scenario
  but did not fire under session pressure.
---

# Multi-agent coordination blindness

## The incident

Session 019fe403 spent the entire session improving ship-py: 20+ commits
across `~/.grok/skills/ship-py/`, `hooks/PreToolUse_ship_phase_gate.py`,
SKILL.md, and tests. At no point did the agent check whether another session
was also working on ship-py.

Near session end, the operator flagged that another session had created an
active handoff at `docs/handoffs/ship-pipeline-open-work-20260809/`
targeting ship-py's review phase — the same phase this session had modified
(P2-1: cross-model diversity in PAUSE_INSTRUCTIONS).

## Root cause

The AGENTS.md rules are explicit:

> "Before staging, run `git log --oneline -5 -- <path>` for files you're
> about to commit — a sibling session may have already written the same file."

> "Always read before edit... If unexpected state, integrate — do not overwrite."

The preflight DID flag `PreToolUse_ship_phase_gate.py` as dirty (another
session's work), but the agent treated it as "cosmetic" and moved on without
checking whether other sessions were actively working on ship-py itself.

**Root cause:** tunnel vision on shipping features. The agent was focused
on implementing and committing Phase 1 + Phase 2 improvements. The
coordination check (grepping for active handoffs on ship-py before starting
work) never fired because the session's momentum was entirely forward
(build, commit, build, commit). The behavioral rule existed but didn't
fire under execution pressure.

## What should have happened

1. **Before starting ship-py work:** `/handoff list` or grep for active
   handoffs mentioning "ship-py"
2. **When preflight flagged the dirty hook:** investigate WHO is editing it
   and whether they're working on the same skill
3. **Before committing:** `git log --oneline -5 -- skills/ship-py/` to check
   for sibling commits
4. **Use a worktree** for multi-session work on the same skill

## Structural fix candidates

- **Session-start handoff scan:** when a session starts working on a skill,
  automatically scan for active handoffs mentioning that skill. Surface as
  a coordination warning.
- **Pre-commit collision check:** before `git add`, check whether any file
  was modified by another session since the last read.
- **Skill-level worktree default:** when working on a skill for >30 minutes,
  suggest switching to a worktree to isolate from sibling sessions.

## Reference

This is the same class as the 2026-07-20 yt-is fetch incident: the preflight
mandate existed but didn't fire under session pressure. The fix pattern
(structural enforcement over behavioral reminder) applies here too.
