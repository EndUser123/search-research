---
title: "Trust-escalation ladder for autonomous agent work"
created: 2026-07-25
source: session-2026-07-25 (Factory repo analysis — security model + human-review boundary)
sources:
  - https://github.com/owainlewis/factory/blob/main/docs/design.md (Factory trust model: "Human review is the shipping boundary")
  - https://github.com/owainlewis/factory/blob/main/SECURITY.md
  - P:/.data/wiki/concepts/workflow-definition-over-agent-capability.md (companion principle)
tags: [trust, autonomy, agent-boundaries, handoffs, tasks, factory, shipping-boundary]
summary: >
  A ladder of agent autonomy for software work, adapted to a task+handoff control plane
  (no PRs, no tickets). Each rung delegates more to the agent: refinement, implementation,
  verification, commit, review, close. The human-reviewed handoff close is the shipping
  boundary — our equivalent of Factory's "human merges the PR." Destructive git and remote
  pushes remain human-gated always. Source: Factory's trust model translated to our control
  plane (tasks the operator assigns + handoff files at P:\docs\handoffs\).
agent: grok
host: both
cognitive_load: 2
verification: single-source-derived
relations:
  - target: wiki/concepts/workflow-definition-over-agent-capability
    type: complementary
  - target: wiki/concepts/auto-commit-authority-isolation
    type: refines
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture
    type: related
  - target: wiki/concepts/shared-root-auto-commit-assurance-boundary
    type: related
---

# Trust-escalation ladder for autonomous agent work

## The ladder

Agent autonomy for software work is not binary. It escalates in rungs, each
delegating more of the loop to the agent. The operator decides which rung a
given work stream operates at; the agent does not promote itself without
authorization.

Our control plane is **tasks the operator assigns + handoff files** at
`P:\docs\handoffs\<topic>-<date>\HANDOFF.md`. We do not use GitHub PRs or a
ticket queue. The ladder below is mapped to that control plane.

| Rung | Agent does | Agent does NOT | Handoff status transition |
|------|-----------|----------------|---------------------------|
| **0 — Refine** | Inspects codebase, reproduces bugs, tightens a rough task into an implementation-ready handoff | Implements code | `needs-refinement` → `ready-to-implement` |
| **1 — Implement** | Writes code, runs tests, commits locally | Verifies with /check, reviews with /review | (handoff written or updated) |
| **2 — Verify** | Runs `/check`, addresses findings, re-commits | Runs `/review`, closes handoff | `implementing` → `ready-for-review` |
| **3 — Review** | Runs `/review`, addresses verified findings | Closes handoff for irreversible work | `reviewing` → `verified` |
| **4 — Close** | Promotes durable findings to wiki, closes handoff | Destructive git, remote push | `verified` → `closed` (via `/handoff close`) |

## The shipping boundary

**`/handoff close` is our shipping boundary.** It is the moment the operator
(or a high-trust agent on reversible work) declares the work stream done:
durable findings are promoted to the wiki, and the handoff directory is
removed. This is the structural equivalent of Factory's "human merges the
PR" — the human-reviewed gate beyond which the work has shipped.

Factory's articulation: *"Factory-created software pull requests remain for
human review. Factory and its default workflows never merge them or enable
automatic merge. The human who merges remains accountable for what ships."*

Translated: an agent may implement, verify, and review autonomously, but the
**close** — the declaration that the work stream is complete and its lessons
are durable — is a human decision for any work that is irreversible,
cross-system, or load-bearing.

## What is always human-gated (every rung)

These never become autonomous, regardless of trust rung:

- **Destructive git** — `reset --hard`, `push --force`, `clean -fd`,
  `checkout -- <path>`, `rebase -i`, `filter-branch`. Forbidden in
  `~/.grok/AGENTS.md` § "No destructive git."
- **Remote pushes** — `git push` to shared remotes. Auto-commit is local;
  push is a publishing act.
- **Handoff close for irreversible work** — see shipping boundary above.
- **Marking a task "done" in the task store** — the operator owns task
  lifecycle completion.
- **Deleting files outside run-scoped temp** — Tier-3 in `/close`.

## Current authorized rung (this fleet)

As of 2026-07-25, this fleet operates at **Rung 2-3 by default**:

- **Rung 1 (Implement + auto-commit):** authorized as standing policy
  (`~/.grok/AGENTS.md` § "Working in the shared main tree": "Commit after
  each logical unit of work — automatically, without asking." Verified
  2026-07-24.)
- **Rung 2 (Verify):** `/check` runs on invocation; `/close` auto-invokes
  `/aar`; `/check` auto-invokes `/review` when triggers fire. The verify
  rung is semi-autonomous — the operator invokes `/check`, but the skill
  escalates to `/review` on its own when load-bearing triggers fire.
- **Rung 3 (Review):** `/review` runs on invocation or via `/check`
  auto-escalation. Findings are addressed by the agent.
- **Rung 4 (Close):** `/handoff close` and `/close` are operator-invoked.
  The agent does not close handoffs autonomously.

Rungs 0 (Refine) and full Rung 4 (autonomous close) are not yet wired —
`/refine` is a proposed skill (pre-plan stage), and autonomous close is
gated by the human-reviewed shipping boundary above.

## How to escalate trust

The operator escalates a work stream to a higher rung by stating so
explicitly ("you can close this handoff when /check passes," "run /review
and address findings without asking"). Without that statement, the default
rung applies. Agents do not self-promote to a higher rung — that is the
trust boundary.

The escalation is **per-work-stream**, not session-wide. A session may
operate at Rung 4 for a typo fix and Rung 1 for a hook system change in the
same turn.

## Why this matters

Without an explicit ladder, two failure modes recur:

1. **Under-trust** — the agent asks for permission on every reversible
   action, burning operator turns on decisions the standing policy already
   authorized (the "evidence-first default" failure mode in AGENTS.md).
2. **Over-trust** — the agent closes a handoff or marks work done without
   the operator reviewing, conflating "I finished my pass" with "the work
   shipped." This is the same failure class Factory's shipping-boundary
   rule exists to prevent.

The ladder makes the boundary explicit so neither failure recurs.

## Relation to Factory's model

| Factory | Ours |
|---|---|
| GitHub issue + label = trigger | Task assignment + handoff `status` field = trigger |
| `factory:ready-for-spec` label | `status: needs-refinement` (proposed) |
| `factory:ready-to-implement` label | `status: ready-to-implement` |
| Human merges PR | Operator runs `/handoff close` |
| Worker opens PR, never merges | Agent implements + commits, never closes handoff for irreversible work |
| Docker sandbox for untrusted work | Worktree isolation for concurrent work (local); VM sandbox deferred |

The control plane differs (labels vs handoff status); the trust model is
isomorphic.

## Falsifier

This concept is wrong if:

- The operator routinely wants agents to close handoffs autonomously,
  making Rung 4 the default rather than the exception. (Would collapse the
  shipping boundary.)
- Auto-commit authority is revoked (would drop the fleet below Rung 1).
- We adopt a ticket/PR system, making the handoff-status mapping obsolete.
- The rungs prove indistinguishable in practice (e.g., Rung 2 and Rung 3
  always fire together, collapsing the ladder).
