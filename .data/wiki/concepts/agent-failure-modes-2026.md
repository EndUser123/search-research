---
title: "AI Agent Failure Modes Beyond Hallucination (Saplin, 2026)"
created: 2026-07-20
source: session-2026-07-20
tags: ['agents', 'failure-modes', 'llm-substrate', 'host-agnostic', 'saplin']
summary: >
  Saplin's 22-mode failure taxonomy (dev.to, May 2026) for agentic engineering.
  Modes span planning (one-shotting, plan-drag), execution (local-patching,
  overengineering), memory (cold-start-amnesia, lossy-compaction, working-
  memory-rot), validation (false-E2E-completion, self-review-softness), and
  handoff (summary-only-handoff-loss, async-reconciliation-failure). Each mode
  has a structural fix, not a prompt fix.
agent: grok
cognitive_load: 4
verification: multi-source-verified
host: both
---

## Summary

Saplin's taxonomy of 22 distinct failure modes agentic LLMs exhibit when working on real engineering tasks. Modes are organized by lifecycle phase (planning, execution, memory, validation, handoff) and were extracted from public engineering writeups and conference talks (Anthropic harness research, Mario Zechner "Building Pi in a World of Slop", Random Labs Slate, Anthropic "Harness design for long-running apps"). This is **host-agnostic** — applies to any LLM agent substrate.

## Key Findings

### Planning failures

- **One-shotting** — Agent tries to build the entire app in one bite, runs out of context, leaves half-built mess. Source: Anthropic long-running-agents.
- **Plan drag** — Plans and task trees prevent early stopping until reality changes; the structure itself resists adaptation. Source: Random Labs Slate.
- **Ugly wish-granting** — Vague request gets literal interpretation; agent grants the wish exactly and uglier than if you hadn't asked. Source: Saplin observation.
- **Spec-deliverable confusion** — Plan/design doc treated as part of the actual deliverable; agent bundles scaffolding with what it was supposed to build. Source: Saplin observation.

### Execution failures

- **Default-fill slop** — Unspecified parts get filled with mediocre training-prior defaults (cargo-cult code, generic UI). Sources: Mario Zechner; Anthropic app harness.
- **Overengineering by default** — Agent adds abstractions, duplication, backwards compat, defense-in-depth because internet-shaped training taught it those moves. Source: Mario Zechner.
- **Local patching** — Each move looks locally reasonable while global system gets harder to reason about. Source: Mario Zechner.
- **Overdecomposition** — Planner/implementer/reviewer stacks technically work, but add ceremony, latency, and inertia. Source: Random Labs Slate.

### Memory failures

- **Cold-start amnesia** — Fresh sessions inherit neither memory nor runbook; waste time guessing what happened and how to check it. Source: Anthropic long-running-agents.
- **Working-memory rot** — Important facts sit in context but stop being reliably available as window grows. Source: Random Labs Slate.
- **Lossy compaction** — Compression keeps long runs alive by dropping state, sometimes exactly the state you needed. Source: Random Labs Slate.
- **Hidden harness control** — Tool mutates context, prompts, tools, reminders, observability, extensibility in ways the user cannot inspect or steer. Source: Mario Zechner.

### Validation failures

- **Self-review softness** — Agent grades its own mediocre work with confident praise and weak critique. Source: Anthropic app harness.
- **Validation interruption** — Diagnostics injected mid-edit confuse the model before a coherent change exists. Source: Mario Zechner.
- **False E2E completion** — Unit tests or curl pass, but actual user path is still broken. Source: Anthropic long-running-agents.
- **Functional but wrong** — Result passes checks while still being awkward, unusable, overcomplicated, or against the spirit of the task. Source: Saplin long-horizon-agents writeup.

### Handoff / coordination failures

- **Summary-only handoff loss** — Subagent returns a neat summary instead of enough real state for parent to integrate safely. Source: Random Labs Slate.
- **Async reconciliation failure** — Parallel work creates the hard question of when results are final, which branch wins, and what actually composes. Source: Random Labs Slate.
- **Blind N-step execution** — Delegated chunks run too long without feedback; agent discovers the wall only at the end. Source: Random Labs Slate.
- **Modality blind spots** — QA tooling misses bugs it cannot see, hear, or exercise like a real user. Source: Anthropic app harness.

## Structural fixes (not prompt fixes)

Per commenter consensus and Saplin's own framing, every mode has a **structural constraint**, not a better prompt:

| Fix | Helps with |
|---|---|
| Initializer/coding-agent split + progress files | Cold-start amnesia, one-shotting, premature completion |
| Feature list JSON marked `passes: false` initially | Premature victory, premature completion |
| Browser-automation E2E testing | False E2E completion, modality blind spots |
| Separate auditor session (different from writer) | Self-review softness |
| Restrict to `/data` write paths | Default-fill slop, hidden harness control |
| Mandatory verification-before-completion gate | Self-review softness, false completion claims |
| Strict capability modes (read-only subagents) | Hidden harness control, handoff loss |
| Git-based progress markers + descriptive commits | Premature completion, lost context |
| Test recency checks (test must exist + be recent) | False E2E completion |
| Pre-flight + post-write health checks | Progress-as-completion |

The meta-pattern from commenter `cart0ne` (BagHolderAI): "Every single fix is a structural constraint, not a better prompt. State files, auditor separation, verification gates, explicit briefs. The model doesn't get smarter — you build the harness that makes the failure modes harder to reach."

## Related

- [[agent-oversight-rubber-stamping]] — operator-side discipline to prevent self-review softness
- [[plan-then-execute-pattern]] — design pattern that prevents some execution failures
- [[verification-before-completion-principle]] — structural fix applied to multiple modes
- [[grok-build-cc-aca-actually-enabled]] — the cc-aca-* suite is the runtime embodiment of these structural constraints in Grok Build

## Auto-related

- [[operator-collaboration-style-and-leverage]]
- [[agent-oversight-rubber-stamping]]

## Sources

- session-2026-07-20 — Maxim Saplin's "AI Agent Failure Modes Beyond Hallucination" (dev.to, 2026-05-22) and 28-comment thread
- session-2026-07-20 — Anthropic "Effective harnesses for long-running agents" (2025-11-26)
- session-2026-07-20 — Anthropic "Harness design for long-running application development" (2026-03)
- session-2026-07-20 — Mario Zechner "Building Pi in a World of Slop" (AI Engineer conference, 2026-04)
- session-2026-07-20 — Random Labs "Slate: moving beyond ReAct and RLM" (2026-03)
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
