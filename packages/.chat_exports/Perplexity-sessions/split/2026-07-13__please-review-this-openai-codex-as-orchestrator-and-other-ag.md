---
title: "please review this openai codex as orchestrator and other agentic cli harnesses with external LLM models discussion. Wha"
date: "2026-07-13"
mode: "COPILOT"
uuid: "c8b5fea1-716c-4a90-9f93-8ecddac3b408"
entry_count: 1
---

## Human

please review this openai codex as orchestrator and other agentic cli harnesses with external LLM models discussion. What do you think the optimal solution is?


what infromation should we use for our delegation solution? I think we had settled on opencode vs PI, but I don't know what conversation that was.

8:20 PM

Worked for 1m 14s
Yes—we found the decision conversation. It was in the Olana profile’s main delegation session:

Olana delegation session

The settled architecture was:

Codex/OpenAI remains the control plane for planning, ambiguity, architecture, debugging, security decisions, integration, and final verification.
OpenCode becomes the preferred external worker for MiniMax, Zai, OpenCode Go/Zen, OpenRouter, and similar provider-backed models.
PI remains the compatibility/specialized lane for llama.cpp, unusual providers, custom APIs, SDK embedding, and programmable extensions.
Codex generates the complete packet automatically: objective, context, allowed paths, forbidden actions, response schema, timeout, verification commands, fallback, and acceptance rules.
External workers handle bounded execution only: extraction, classification, read-only exploration, test runs, documentation drafts, and mechanical changes.
Read-only is the default. Writes require an explicit scope and isolated worktree/staging directory.
Full headless approval is acceptable for trusted work; approval and containment are separate concerns.
Only idempotent read-only infrastructure failures may retry once through the fallback lane.
The current plan reflects that decision:

delegation plan

However, I found an important implementation mismatch:

The plan says OpenCode-first.
The current live skill still says worker: "pi" and minimax/MiniMax-M3 by default.
Live OpenCode/PI smoke tests and default activation were not yet proven.
So the correct conclusion is: OpenCode was settled as the preferred lane, but the implementation has not yet been fully aligned with that decision. The next corrective step should be to make OpenCode the skill/router default, retain PI as explicit fallback, then run the bounded live smoke tests.

8:21 PM
yes, sorta. except if opencode fails we should halt for now, don't try PI. But were there repos that already solved this solution?

8:28 PM

Worked for 55s
Yes, but no repo appears to solve our exact architecture end-to-end.

Our requirement is unusually specific:

Codex parent
-> generate bounded packet
-> OpenCode worker
-> structured result + artifacts
-> parent verification
-> halt on any OpenCode failure
The closest reusable projects are:

OpenCode Swarm — closest to gated execution, separate reviewer/test agents, resumable state, and evidence. It is OpenCode-native, though; it does not provide Codex’s external-worker handoff boundary. It also has more orchestration than we currently need.

Q00/Ouroboros — closest to our contract/ledger/runtime idea. It treats actions as auditable, replayable events and has a multi-runtime adapter. Its OpenCode runtime launches opencode run --format json and parses structured output. This is conceptually the strongest reference, but likely too large for our solo-director workflow. OpenCode runtime

Agent Orchestrator — strongest reference for process lifecycle, Windows support, worktrees, session ownership, and failure routing. It is designed for fleets of parallel coding agents and PR/CI automation, not one Codex parent delegating a bounded task.

am-will/swarms — useful for context handoff, dependency-aware waves, and parent verification. It is a Codex/Claude workflow skill, not an OpenCode provider bridge.

pi-open-agents — useful for agent definitions, per-agent models, thinking levels, permissions, and OpenCode-compatible agent files. It does not solve our Codex-parent packet, artifact, failure, or acceptance protocol.

My recommendation remains: reuse patterns, not adopt one of these wholesale.

We should keep our small bridge and borrow:

Ouroboros’s event/ledger concepts.
Agent Orchestrator’s lifecycle and worktree handling.
OpenCode Swarm’s evidence and gate structure.
pi-open-agents’s agent-file conventions only if we later revive PI.
The new failure policy should be:

OpenCode succeeds -> inspect and verify result
OpenCode fails -> halt and report
PI -> explicit manual override only
Important: our current implementation is not yet aligned with that policy. The plan still permits fallback workers, and the skill still defaults to PI. Those should be changed before calling the system live.

This conclusion is based on the public projects above; it is a bounded search, not proof that no other private or less-visible repo exists.

8:28 PM
should we change our protocols? are they that valuable that we should build our own system?

8:32 PM

Worked for 49s
Yes—but build a thin custom control-plane protocol, not a new general-purpose agent framework.

The valuable part is our boundary:

Codex decides and verifies
↓
OpenCode executes one bounded task
↓
structured evidence returns
↓
Codex accepts, rejects, or escalates
Public projects solve adjacent pieces:

OpenCode Swarm: gated planning, coding, review, tests, and evidence inside OpenCode.
Agent Orchestrator: process/session lifecycle, Windows support, worktrees, CI/review routing.
Q00/Ouroboros: versioned runtime adapters, event ledgers, auditability, replayable actions.
am-will/swarms: context handoff, dependency-aware waves, and parent verification.
None matches our exact requirement: Codex already has the reasoning context, OpenCode is an external bounded worker, and OpenCode failure must halt rather than silently switch runtimes.

So I would change our protocol now:

Make OpenCode the only automatic worker.
Set on_failure: "halt" and max_attempts: 1.
Remove automatic fallback_worker behavior.
Keep PI only as an explicit manual override, not a fallback.
Separate these statuses:
launch_status
protocol_status
worker_status
verification_status
acceptance_status
Keep the packet, artifact, timeout, structured-result, and independent-verification contracts.
Do not build provider abstraction, parallel swarms, dashboards, or a task database yet.
The current implementation is not aligned yet: SKILL.md still defaults to PI, and runner.mjs still supports automatic fallback. The plan also still describes PI as an automatic fallback.

Claim ledger:

Claim Type Confidence
Public repos solve useful subsystems verified fact High
One public repo matches our full design unsupported; none found High
A small custom protocol is valuable for us recommendation High
A full custom orchestration framework is justified unsupported High
My recommendation: own the small protocol and OpenCode adapter, reuse public ideas for lifecycle and evidence, and deliberately postpone everything else.

8:33 PM
I'm very surprised that there are not codex based solutions for what we are looking for. codex orchestrates and delegates, we get proof back and verify it, how hard is that?

8:35 PM

Worked for 1m 7s
You’re right to be surprised. I was too categorical earlier: there are now Codex-specific projects that solve much of the parent-orchestrator side.

The core loop is easy:

Codex plans
→ dispatches bounded worker
→ receives structured handoff
→ runs verification
→ accepts, rejects, or halts
The hard part is making that loop trustworthy across restarts, stale state, timeouts, malformed output, worktree ownership, and provider failures.

The most relevant discoveries are:

indiekitai/codex-orchestrator is very close to the Codex parent side: bounded worker tasks, isolated worktrees, persistent ledgers, heartbeat monitoring, evidence labels, review routines, acceptance states, and explicit stop conditions. It even treats Pi/DeepSeek/Claude reviewers as advisory evidence rather than automatic authority. It does not currently provide our OpenCode worker adapter.

ZypherHQ/agent-orchestration-skill provides an explicit Codex orchestration skill plus a local control room with run ledgers, dispatches, handoffs, evidence, gates, memory, usage, and session import. Its own documentation says the package does not make model calls; it provides the orchestration layer.

dyngai/handoffkit is relevant for message passing, ownership transfer, budgets, supervision, dead letters, cancellation, and tracing. However, its Codex transport is explicitly described as reverse-engineered and unsupported, so I would reuse ideas, not depend on its transport.

shanraisshan/codex-cli-best-practice covers Codex agents, skills, hooks, and orchestration patterns, but it is more of a reference/workflow repository than a complete delegation runtime.

There is also an official signal that this seam is not fully built into Codex yet: skill-driven automatic delegation remains an open Codex issue.

So my revised conclusion is:

We should not build the entire system ourselves.

We should probably reuse or closely model codex-orchestrator or agent-orchestration-skill for:

parent orchestration;
run ledgers;
handoff records;
evidence labels;
acceptance gates;
stop conditions;
session continuity.
Then we only build the genuinely missing adapter:

Codex orchestration layer
↓
OpenCode subprocess adapter
↓
structured result/artifact parser
↓
Codex verifier and acceptance gate
That adapter should implement our specific policy:

OpenCode succeeds → verify
OpenCode fails → halt
PI → explicit manual mode only
The current custom bridge is therefore probably too ambitious in its protocol scope, but not unnecessary. We should shrink it from “our own orchestration system” to “an OpenCode execution adapter and evidence boundary,” while reusing the Codex orchestration model already present in those projects.

Claim ledger:

Claim Type Confidence
Codex-based orchestration solutions now exist verified fact High
One already handles our Codex → OpenCode boundary unsupported; none found High
The adapter seam is small enough to own recommendation High
We should continue expanding our full custom orchestration layer rejected recommendation High
8:36 PM

















Environment

Changes

Local

main

Commit or push

Compare branch

Sources

AI Multi-Instance.lnk

github.com/indiekitai/codex-orchestrator

api.github.com/repos/am-will/swarms

View all

## Assistant

The optimal solution is a **thin custom delegation protocol** on top of an existing Codex-oriented orchestration layer, with OpenCode as the only automatic worker lane and PI kept as a manual override only. That conclusion still fits your earlier decision trail, but I’d tighten it further now that there is better evidence on what public repos actually solve and what they do not solve.

## What you already settled

Your prior decision history points to a stable core: Codex/OpenAI should remain the control plane, OpenCode should be the preferred external execution lane, and PI should exist only for compatibility or explicit specialist use rather than as a normal fallback. Your more recent preference also adds an important constraint: when OpenCode fails, the system should halt rather than silently retry through PI, because fallback changes the semantics of the run and weakens verification clarity.

The memory evidence also supports keeping one orchestrator command as the user-facing surface, which fits a single-control-plane design better than a symmetric multi-harness mesh. That matters because your real problem is not “how do we run many agents,” but “how do we preserve one authoritative delegator, one evidence boundary, and one acceptance decision.”

## What public repos solve

There are now real public projects that cover significant parts of the orchestration problem, so “build everything yourself” is no longer justified. ZypherHQ’s `agent-orchestration-skill` explicitly describes itself as an explicit-only Codex orchestration control room with local run ledgers, dispatches, handoffs, evidence, gates, memory, usage tracking, and Codex session import; it also states that the root Codex thread remains the orchestrator and spawned workers are leaf-only, while the package itself does not make model calls.

Ouroboros is broader and more mature: it presents itself as a local-first runtime layer for replayable, observable, policy-bound execution across Codex CLI, OpenCode, Pi, and other runtimes, and it is built around immutable specs, ledgers, and staged evaluation gates. It is strong evidence that the runtime/ledger/adaptation layer is already well explored in the open, but it is also much larger and more opinionated than your bounded “Codex parent → OpenCode worker → verify or halt” workflow.[1]

Indiekitai’s `claude-orchestrator` is not your target harness, but it is useful as a reference for dispatch discipline: bounded task contracts, isolated worktrees, evidence levels kept separate, conservative merge gates, and mandatory cross-model review after each batch. Its README also says the harness-agnostic core lives in a separate orchestration playbook and that this repo is just the Claude Code adapter, which is exactly the architecture pattern you want: one core discipline, thin harness adapters.

## What is still missing

None of the sources above gives you your exact end-to-end requirement out of the box: a Codex-led parent that emits your specific bounded packet format, invokes OpenCode as the single automatic worker, accepts structured artifacts/results back, and halts on any OpenCode execution failure without runtime substitution. `agent-orchestration-skill` is closest on the Codex control-plane side, but it explicitly does not make model calls itself, so it does not provide your OpenCode worker adapter.

Ouroboros supports both Codex and OpenCode and already has a multi-runtime adapter model, but its value proposition is much broader than your need: interview/seed/evaluate/evolve, multi-runtime OS semantics, and persistent evolutionary loops. That makes it a strong reference implementation for ledger/event/runtime ideas, but likely too heavyweight if your main goal is a narrow delegation seam with strict halt semantics.

So the key correction to earlier thinking is: the hard part is not “can Codex orchestrate and verify,” because that pattern clearly exists in public now; the missing part is your exact **adapter contract and failure policy**. That is small enough to own.

## Recommended architecture

I would use this stack:

| Layer | Recommendation | Why |
|---|---|---|
| Control plane | Codex orchestration skill/control room, preferably modeled on `agent-orchestration-skill` | It already matches explicit orchestration, ledgers, handoffs, evidence, and session continuity.  |
| Execution worker | OpenCode only, automatic | Matches your settled decision and keeps one deterministic external lane.  |
| Fallback policy | Halt on OpenCode failure | Preserves protocol integrity and avoids cross-runtime ambiguity.  |
| Compatibility lane | PI manual override only | Keeps uncommon providers and llama.cpp/custom API flexibility without contaminating normal runs.  |
| Protocol you own | Thin packet/result schema + verifier boundary | This is the part public repos do not cleanly provide for your exact workflow.  |

The packet should be minimal but strict:
- Objective and task type.
- Context bundle, including exact files or excerpts, not just paths when feasible.
- Allowed paths and explicit write scope.
- Forbidden actions.
- Expected output schema.
- Acceptance tests or verification commands.
- Timeout, max attempts = 1.
- Failure mode = halt.
- Artifact contract, including logs, diffs, test output, and touched files.

The result schema should also be strict:
- `launch_status`
- `worker_status`
- `artifact_status`
- `verification_status`
- `acceptance_status`
- `touched_files`
- `commands_run`
- `artifacts`
- `claims`
- `known_uncertainties`

That status separation is valuable because it prevents the classic lie of “task failed but produced useful-looking text.” A worker can launch successfully, fail verification, and still return artifacts; those are different states and should not collapse into one boolean. This is exactly the kind of protocol value that is worth building yourself.

## What information to use

For your delegation solution, I would treat the following as the authoritative inputs:

1. Your prior architectural decision: OpenCode-first, PI manual only, Codex as control plane.
2. Your workflow preference for a single orchestrator command and scalable agent routing.
3. The public reference patterns:
- `agent-orchestration-skill` for Codex run ledgers, handoffs, evidence, gates, and session import.
- Ouroboros for event/ledger/runtime adapter concepts and replayability.
- Indiekitai orchestration discipline for bounded task contracts, isolated worktrees, and evidence-level separation.
4. Your recent broader research that `mcp-broker` is likely the best candidate for cross-client MCP-style transport unification, especially across Codex, Claude Code, and Windows-oriented local environments. That is relevant if you want the transport/control integration layer standardized, but it is adjacent to the worker protocol itself rather than a substitute for it.[2]

So the “conversation we had” you were trying to recover is basically this distilled rule set:

- Codex owns planning, delegation, and final acceptance.
- OpenCode is the default worker lane.
- OpenCode failure halts the run.
- PI is manual override only.
- Reuse orchestration ledgers/evidence patterns from existing projects, but own the adapter seam.

## My view

FACT: there are now public Codex-oriented orchestration systems with ledgers, handoffs, evidence, and gates, so building a full orchestration framework from scratch is unnecessary.

CONSENSUS: the valuable custom part in agent systems is usually the boundary contract, not the generic orchestration shell; your needs fit that pattern unusually well because your key differentiator is the strict worker packet, evidence return, and halt-on-failure policy.

SPECULATION, high confidence: the optimal path is to **adopt or imitate an existing Codex orchestration shell and build only an OpenCode execution adapter plus your verifier contract**. That gives you leverage without surrendering the one part that actually defines correctness in your workflow.

Concretely, I would not choose “OpenCode vs PI” as a fresh decision anymore; I would treat that as already settled operational policy. The real next decision is whether your parent layer should be modeled more closely on `agent-orchestration-skill` or whether you want a lighter bespoke shell with only the pieces you actually use. Based on your bias toward minimal necessary modifications, I would start by borrowing the `agent-orchestration-skill` model for ledger/handoff/state and then add one custom `OpenCodeAdapter` with `on_failure: halt`.

Would you like me to turn this into a concrete delegation spec next, with a TypeScript packet schema, result schema, and failure-state machine?
