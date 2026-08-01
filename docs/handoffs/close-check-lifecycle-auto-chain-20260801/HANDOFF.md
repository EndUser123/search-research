---
thread_id: close-check-lifecycle-auto-chain-20260801
parent_handoff_path: none
current_session_id: 019f9a89-d902-7930-ad3a-bab7e682830b
current_terminal_id: console
produced_at: 2026-08-01T20:35:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 8829753f7759cf731dc2266319b5fbe9d7d72e19
---

# Handoff: Close-check lifecycle auto-chain — auto-invoke surface-only skills

## Objective

The `/close-check` workflow detects lifecycle-skill gaps (skills that should have run but didn't) but only *reports* them. The operator then has to manually invoke each one (`/harvest`, `/friction`, `/capture`, `/trace`, `/wiki`, `/handoff`). This creates friction: 7 manual commands at session close.

**Goal:** make the close-check workflow auto-invoke surface-only lifecycle skills when it detects a gap, rather than just reporting the gap for the operator to fix manually.

## Why this matters

Session 019f9a89 (2026-08-01) demonstrated the problem: the close-check workflow returned BLOCKED with 5 session-attributed findings. The operator had to manually run `/harvest`, `/friction`, `/capture`, `/wiki`, `/trace`, and `/handoff` — 6 sequential invocations that took ~15 minutes of wall-clock time and required the operator to remember which skills to run in which order.

This is exactly the "automate user meta-actions" standing goal from `P:/docs/goals/reduce-user-meta-actions-202607-20.md`.

## Evidence

- Close-check workflow report (2026-08-01): flagged `/harvest`, `/friction`, `/capture`, `/trace` as not-run [SESSION gaps]
- Friction analysis: workflow friction #5 — "Manual Skill Invocation Chain" (1 chain, HIGH automation potential)
- Capture scan: surfaced as improvement #1 — "Close-check auto-chain"

## Scope

**In scope:**
- Determine which lifecycle skills are safe to auto-invoke (surface-only, non-destructive)
- Design the auto-chain mechanism: should the workflow Rhai script invoke skills directly, or should it emit a command sequence the agent executes?
- Implement and test the auto-chain

**Out of scope:**
- Auto-invoking destructive skills (`/aar` writes receipts, `/handoff` writes files — these need agent judgment)
- Replacing the close-check workflow itself

## Classification matrix

| Skill | Safe to auto-invoke? | Why |
|-------|---------------------|-----|
| `/harvest` | ✅ Yes | Surface-only (`remediation_mode: surface-only` in SKILL.md) — reads obligations, doesn't modify |
| `/friction` | ✅ Yes | Surface-only — analyzes transcript, doesn't modify |
| `/capture` | ⚠️ Partial | `remediation_mode: auto-act` — can write wiki concepts and AGENTS.md rules. Auto-invoke but gate writes |
| `/wiki` | ❌ No | Writes files (concepts, log.md). Needs agent judgment on what to capture |
| `/trace` | ⚠️ Partial | Surface-only (`remediation_mode: surface-only`) but requires a target argument |
| `/handoff` | ❌ No | Writes files. Needs agent judgment on work-stream scope |

## Proposed approach

1. The close-check workflow Rhai script detects gaps (already done)
2. For each gap where the skill is `remediation_mode: surface-only`, the workflow auto-invokes it via an agent() call
3. For skills with `remediation_mode: auto-act` or that write files, the workflow emits a recommendation: "Run `/<skill>` now — gap detected in <domain>"
4. The workflow re-scans after auto-invocation and updates the report

## Acceptance criteria

- [ ] Close-check workflow auto-invokes `/harvest` and `/friction` when gaps are detected
- [ ] Auto-invocation results are included in the readiness report
- [ ] Skills that write files (`/wiki`, `/handoff`) are surfaced as recommendations, not auto-invoked
- [ ] The auto-chain is tested on a real session

## Read-first list

- `~/.grok/commands/close-check.md` — the command wrapper
- Workflow script: `~/.grok/sessions/P%3A%5C/<session-id>/workflows/wf_*/script.rhai`
- `~/.grok/skills/harvest/SKILL.md` — remediation_mode: surface-only
- `~/.grok/skills/friction/SKILL.md` — remediation_mode: surface-only
- `~/.grok/skills/capture/SKILL.md` — remediation_mode: auto-act
- `P:/.data/wiki/concepts/proactive-improvement-opportunity-scanner.md` — capture design

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** nothing
- **Non-blocking to:** `why-skill-adoption-gap-20260725` (if close-check auto-invokes /why, that partially closes the adoption gap)

## Status

OPEN — design identified, implementation deferred to fresh session. The classification matrix and proposed approach are ready for implementation.

## Falsifier

This handoff is wrong if the close-check workflow can already auto-invoke skills (it can't — the Rhai script only runs scan commands, not skill invocations) or if the operator prefers manual invocation (they don't — the friction analysis and the 7-command chain prove otherwise).
