---
title: "Fleet maintenance skill design: what Grok Build should have"
created: 2026-07-28
source: session-019fa94d (/www research + operator question)
sources:
  - https://ve3.global/blog/ai-agent-lifecycle-management-the-governance-gap-enterprises-need-to-close-in-2026
  - https://www.ibm.com/think/topics/agent-lifecycle-management
  - https://www.glean.com/perspectives/key-steps-for-maintaining-ai-automation-systems-effectively
  - https://naqeebali-shamsi.medium.com/stop-wasting-tokens-a-developers-guide-to-claude-code-cleanup-de842f6403e5
  - https://github.com/danielrosehill/Claude-Workspace-Foundational-Plugin
tags: [maintenance, skill-design, fleet-management, grok-build, workspace-hygiene, lifecycle]
host: grok
agent: grok
verification: web-sources-cited
cognitive_load: 3
summary: >
  The Grok Build fleet needs a `/maintain` skill that goes beyond the
  Claude-side "main" skill (diagnostic-only health checks). The design
  has three layers: DIAGNOSE (workspace-health), ACT (cleanup/rotation/
  repair), and PREVENT (growth limits, auto-cleanup triggers, scheduled
  cadence). Not a port — a purpose-built fleet maintenance orchestrator
  for a solo operator running 15+ concurrent agent sessions.
---

# Fleet maintenance skill design: what Grok Build should have

## The question

Operator asked: "What should we have for a 'maintenance' type skill?
On Claude we have a 'main' skill. What should we have on the Grok side?
It doesn't have to be the same as on the Claude side because Grok is
where better things are done."

## What exists today

| Skill | Layer | What it does | Gap |
|-------|-------|-------------|-----|
| `workspace-health` | DIAGNOSE | Surfaces problems (git, skills, wiki, config, plugins, handoffs, disk) | Diagnosis only — no action |
| `skill-prune` | ACT (partial) | Proposes merges/archives for stale/duplicate skills | Skills + wiki only; no logs, artifacts, temp files |
| AGENTS.md §Maintenance | REMIND | "Run /skill-prune monthly" | Behavioral reminder; no mechanical enforcement |

**The gap is ACT + PREVENT.** Nobody rotates logs, cleans `.data/` root,
purges stale `.artifacts/` dirs, closes ancient handoffs, or enforces
growth limits.

## What the Claude side has ("main" skill)

The Claude "main" skill (adapted into `workspace-health` on Grok) is a
**health checker** — it surfaces infrastructure problems in a scored
report. It does NOT fix them. It was the right design for Claude Code
(where hooks/plugins are more fragile and need manual diagnosis), but
on Grok Build the fleet is larger (15+ concurrent terminals) and the
operator needs **action**, not just diagnosis.

Source: [danielrosehill/Claude-Workspace-Foundational-Plugin](https://github.com/danielrosehill/Claude-Workspace-Foundational-Plugin)
— Claude workspace plugin for "setup, context/memory maintenance, report
parsing, inventory analysis." Same diagnostic-only pattern.

## What Grok Build should have: `/maintain`

**Not a port of "main".** A purpose-built fleet maintenance orchestrator.

### Three-layer architecture

```
Layer 1: DIAGNOSE (workspace-health, already exists)
  → surfaces problems with scored report

Layer 2: ACT (new — the missing layer)
  → fixes what diagnose found:
    - rotate stale logs (semantic_daemon.log 159MB, hook_debug.log 29MB)
    - organize .data/ root (move telemetry to .data/telemetry/, logs to .data/logs/)
    - purge stale .artifacts/ dirs (older than N days, no active session)
    - close ancient handoffs (status:open + >30 days + no recent activity)
    - clean temp files (P:/tmp, $env:TEMP, _tmp_*.py)
    - re-index wiki if concept count drifts from file count
    - run vulture on changed skills (advisory)

Layer 3: PREVENT (new — growth management)
  → stops problems before they recur:
    - enforce .data/ root convention (no loose files; redirect to subdirs)
    - growth alerts: skill count >1000, wiki >500 concepts, handoffs >20 open
    - log rotation policy (max 50MB per log file; rotate to .old)
    - artifact TTL (auto-clean .artifacts/ older than 7 days)
    - handoff TTL (warn on >30 day open handoffs)
```

### Design principles (why this is "better" than Claude's main)

1. **Action over diagnosis.** Claude's main surfaces problems and waits
   for the operator. Grok's `/maintain` should fix what it can and only
   escalate what needs a human decision. (Same pattern as `/close` —
   resolve gates mechanically, loop only on concrete gaps.)

2. **Fleet-aware.** Claude's main is single-session. Grok's `/maintain`
   must account for 15+ concurrent terminals — never clean files that
   belong to an active session, never rotate a log being written.

3. **Scheduled, not manual.** The operator shouldn't have to remember
   to run maintenance. `/maintain` should be invocable via
   `scheduler_create` (monthly cadence) or triggered by growth thresholds
   (skill count, disk usage, handoff count).

4. **Composable.** `/maintain` orchestrates existing skills
   (`workspace-health` for diagnosis, `skill-prune` for hygiene) rather
   than reimplementing them. New code is only the ACT + PREVENT layers.

### Invocation modes

| Mode | What runs | When |
|------|-----------|------|
| `/maintain` (default) | DIAGNOSE + safe ACT (rotate, organize, clean temp) | Monthly or when something feels off |
| `/maintain --full` | DIAGNOSE + all ACT + PREVENT (close handoffs, growth alerts) | Quarterly deep clean |
| `/maintain --check` | DIAGNOSE only (same as workspace-health) | Session start |
| `/maintain --dry-run` | DIAGNOSE + propose actions without executing | Before trusting auto-cleanup |

### What NOT to do

- Do NOT delete files without confirming (same safety as AGENTS.md §action_safety)
- Do NOT clean `.artifacts/` for the current terminal
- Do NOT rotate logs being actively written (check file lock / mtime)
- Do NOT close handoffs from other terminals (single-writer rule)
- Do NOT reimplement what `skill-prune` and `workspace-health` already do

## External research context

Enterprise AI agent lifecycle management (IBM, ve3, Teneo, Flowable)
treats agents as governed non-human identities with monitoring, update,
and retirement cycles. The solo-fleet pattern is different: the operator
IS the governance, and the "agents" are skills/hooks/configs, not
deployed microservices. The maintenance skill adapts enterprise ALM
patterns (monitor → act → prevent) to a single-workspace solo context.

Key external sources:
- [IBM: Agent Lifecycle Management](https://www.ibm.com/think/topics/agent-lifecycle-management) — "end-to-end process of managing AI agents throughout their operational life"
- [Glean: Key steps for maintaining AI automation](https://www.glean.com/perspectives/key-steps-for-maintaining-ai-automation-systems-effectively) — "ongoing operating rhythm: continuous performance monitoring, fresh knowledge sources"
- [Medium: Claude Code Cleanup](https://naqeebali-shamsi.medium.com/stop-wasting-tokens-a-developers-guide-to-claude-code-cleanup-de842f6403e5) — "cleaning up Claude Code bloat before plugins, MCP servers, hooks, and memory files eat your context window"

## Falsifier

If `/maintain` runs monthly and the `.data/` root still accumulates
20 loose files, or log files exceed 50MB without rotation, or stale
handoffs pile up past 30 days without closure — the skill has failed.
The structural fix (auto-redirect new telemetry to subdirs, growth
thresholds, TTL policies) must prevent recurrence, not just clean up
after the fact.

## Related concepts

- [[agentic-sdlc-skill-lifecycle-architecture]] — where `/maintain` sits in the SDLC (MAINTAIN stage)
- [[dead-code-detection-workflow]] — vulture integration (part of ACT layer)
- [[dynamic-wiki-driven-skill-configuration]] — wiki health as part of maintenance
- [[model-pool-selection-policy-speed-quota-diversity]] — model fleet health as part of maintenance
