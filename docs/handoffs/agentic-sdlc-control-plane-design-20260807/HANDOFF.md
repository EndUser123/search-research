---
thread_id: agentic-sdlc-control-plane-design-20260807
parent_handoff_path: none
produced_at: 2026-08-07
status: open
handoff_type: design
accurate_as_of_head: 688686f83cf206c1191f6316056316c3952ff215
---

# Handoff - Agentic SDLC Control Plane / Software Factory

## Objective

Design, then implement in staged increments, a cross-host Agentic SDLC Control
Plane that makes software work resumable, evidence-gated, cost-aware, and
safe to run for long periods, including unattended overnight work. The design
must improve real work such as `yt-is` throughput optimization without making
chat history the source of truth.

This is a design handoff. It is not an implementation report, does not
authorize live `yt-is` benchmarks, and does not authorize automatic merges,
pushes, external fetches, or user authentication.

## Status

**OPEN - DESIGN PROPOSAL ONLY.**

The workspace already has useful skills, handoffs, delegation packets,
experiment gates, and worktree conventions. They are distributed across
hosts and repositories. No single controller, task manifest, capability
broker, or overnight supervisor was verified as the governing implementation
for this proposal.

## Producing context

This handoff was created after inspecting the existing Grok handoff format in
the following representative files:

- `P:/docs/handoffs/agent-proactivity-improvements-20260731/HANDOFF.md`
- `P:/docs/handoffs/adaptive-escalation-experiment-20260724/HANDOFF.md`
- `P:/docs/handoffs/cross-model-dispatch-improvements-20260801/HANDOFF.md`
- `P:/docs/handoffs/claim-verification-layer3-design-20260807/HANDOFF.md`
- `P:/docs/handoffs/batch-skill-defect-cleanup-20260806/HANDOFF.md`

The proposed control plane is informed by the following existing capability
surfaces. These are inputs to design, not proof that they already compose into
one system:

- `C:/Users/brsth/.agents/skills/cost-aware-delegation/SKILL.md`
- `C:/Users/brsth/.agents/skills/delegation-packet-runner/SKILL.md`
- `P:/.agents/skills/preflight/SKILL.md`
- `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/evidence-driven-experiment-loop/SKILL.md`
- `C:/Users/brsth/.codex/skills/review-packet-runner/SKILL.md`
- `P:/packages/codex-external-delegation/skill/SKILL.md`

## Why this matters

Repeated work across Codex, Grok Build, Claude Code, and delegated models has
exposed the same class of failure:

- useful context exists, but a cold-start agent does not reliably discover it;
- a handoff or chat summary can drift from the source code and runtime;
- a goal can exceed the receiving interface's character limit;
- a worker can report `done` after tests pass without proving live routing,
  runtime identity, transitive isolation, or artifact persistence;
- expensive work can be repeated after an auth, tool, cohort, or environment
  problem that was already solved or already ruled out;
- a dirty shared worktree makes ownership and integration unclear;
- retry duplication, tainted data, stale summaries, and tautological metrics
  can produce confident but invalid performance conclusions;
- prompt rules alone do not provide durable state, idempotent resume, or
  machine-checkable authority boundaries.

The control plane should turn these lessons into state, receipts, validators,
and bounded transitions rather than relying on a stronger prompt alone.

## Verified existing capabilities

The following are verified characteristics of the inspected handoff and skill
surfaces:

- Existing Grok handoffs use YAML front matter with a thread identifier,
  parent handoff, production date, status, handoff type, and sometimes source
  transcript and repository head.
- Existing handoffs are cold-start documents: they include read-first files,
  verified facts, current state, dependencies, constraints, task packets,
  acceptance criteria, open decisions, and a resumption protocol.
- `cost-aware-delegation` keeps strategy, risk acceptance, final judgment, and
  integration parent-owned while allowing bounded low-cost work to be
  delegated.
- `delegation-packet-runner` provides a structured packet shape for objective,
  context, scope, allowed actions, forbidden actions, stop conditions,
  verification, and final reporting.
- `preflight` requires discovery of implementations, callers, registrations,
  state/default consumers, caches, tests, and competing plans before a
  non-trivial change; it also calls for re-checking at implementation start
  and completion.
- `evidence-driven-experiment-loop` supplies lifecycle gates for experiments,
  explicit authorization, falsifiers, adversarial review, handoffs, and a
  bounded goal compiler. Its goal output must be checked against the receiving
  interface limit rather than assumed to fit.
- `review-packet-runner` turns review and assessment requests into evidence-
  grounded packets and requires preflight when a review can authorize action.
- `codex-pi` already supports structured delegated packets, provider-aware
  route records, worktree isolation, no silent fallback, and parent
  verification for its supported execution path.
- The current workspace root is at commit
  `688686f83cf206c1191f6316056316c3952ff215` when this handoff was produced.

## Current state

### Facts

- Useful building blocks exist, but their source, installation, host runtime,
  and enforcement strength are distributed.
- Existing skills are mostly advisory workflows; their presence does not prove
  that a given host loaded or enforced them in a live session.
- Existing handoffs improve continuity, but a handoff is not a scheduler,
  receipt store, mutation authority, or proof of completion.
- The `yt-is` investigation has already demonstrated the value of decision
  packets, falsifiers, abort gates, promotion rules, raw-artifact provenance,
  adversarial review, and explicit parent-owned live-run authorization.

### Proposal

The control plane should be a versioned, host-adapted execution protocol with
five durable objects:

1. **Task manifest** - the authoritative objective, scope, authority paths,
   capabilities, budget, dependencies, gates, and next action.
2. **Execution state** - an append-only or transactionally updated record of
   phase transitions, attempts, blockers, resumes, and terminal disposition.
3. **Evidence receipts** - command identity, working directory, arguments,
   runtime/model identity, exit result, duration, output artifacts, and
   verification outcomes.
4. **Mutation lease** - explicit authority for a worker to write a path,
   modify a branch/worktree, use an external capability, or integrate a
   result.
5. **Handoff packet** - a rendered cold-start view of the manifest, state,
   evidence, open decisions, and next executable action.

These objects should be validated by code. `AGENTS.md`, `CLAUDE.md`, and skills
should explain invariants and workflows, but should not be the only enforcement
layer.

## Proposed lifecycle

The initial state machine is:

`DISCOVERY -> PLANNED -> AUTHORIZED -> EXECUTING -> VERIFIED -> REVIEWED -> INTEGRATED`

Side states are:

`BLOCKED`, `NEEDS_INPUT`, `PARTIAL`, `PAUSED`, `REJECTED`, and `CLOSED`.

Required transition evidence:

- `DISCOVERY -> PLANNED`: authority paths, existing implementations, risks,
  dependencies, and scope are recorded.
- `PLANNED -> AUTHORIZED`: allowed capabilities, budget, stop conditions,
  verification, and owner are explicit.
- `AUTHORIZED -> EXECUTING`: the actual runtime, model route, worktree, and
  manifest revision are recorded.
- `EXECUTING -> VERIFIED`: required commands and outcome-bearing artifact
  checks pass; a passing unit test is not treated as live activation.
- `VERIFIED -> REVIEWED`: claim ledger and adversarial review are complete.
- `REVIEWED -> INTEGRATED`: an explicit owner authorizes stage, commit, merge,
  push, or deployment; the control plane does not infer that authority.

## Proposed manifest fields

The first schema should include, at minimum:

- `task_id`, `parent_task_id`, `objective`, `created_at`, `owner`
- `workspace`, `repository`, `base_ref`, `worktree_path`
- `authority_paths`, `read_paths`, `write_paths`, `artifact_paths`
- `allowed_actions`, `forbidden_actions`, `external_capabilities`
- `dependencies`, `branches`, `stop_conditions`, `resume_policy`
- `model_policy`, `route_policy`, `budget`, `time_limit`, `quota_limit`
- `verification_commands`, `required_receipts`, `review_requirements`
- `status`, `phase`, `attempt`, `next_action`, `last_receipt_id`

Every field needs an owner and an invalid/missing value policy. A default that
silently broadens authority is a defect.

## Proposed subsystems

### 1. Discovery and preflight engine

Build a machine-readable inventory of source-of-truth files, active runtime
paths, registries, callers, tests, worktrees, dirty files, known handoffs,
skills, and external capabilities. Detect conflicts before authorization.

### 2. Worktree and mutation broker

Give workers path-scoped write leases in isolated worktrees. Reject writes to
the protected main checkout, unrelated paths, or files outside the manifest.
Require an explicit parent-owned integration step for stage/commit/merge/push.
Preserve pre-existing dirty work and record ownership instead of resetting it.

### 3. Adaptive delegation engine

Represent work as a dependency DAG rather than a fixed wave. Route bounded,
low-ambiguity tasks to cheaper models and reserve stronger reasoning for
architecture, synthesis, adversarial review, and final decisions. Record the
requested route and the host-verified route separately. Do not silently
fallback, retry, or claim a model was used without a receipt.

### 4. Evidence and claim ledger

Persist receipts and claims together. Every important claim has a type,
evidence path, verification method, confidence, falsifier, and allowed action.
Reject a transition that promotes an inference or hypothesis to an
implementation or live-benchmark authorization without a discriminating test.

### 5. Verification and adversarial review gates

Require scope checks, syntax/tests, caller reachability, runtime identity,
artifact existence, diff hygiene, and relevant live-path checks. Before
`ready_for_parent_review`, attack the 1-3 load-bearing claims: test for
tautologies, double counting, retry/attempt duplication, cohort degeneracy,
stale artifacts, tainted data, alternative explanations, and unmeasured
overhead. Weaken the decision when the review finds a real limitation.

### 6. Overnight supervisor and resume engine

Run only authorized phases, checkpoint after every material action, enforce
timeouts and process-tree cleanup, detect no-progress loops, preserve logs,
and resume idempotently from state rather than replaying chat. Pause at auth,
quota, destructive, ambiguous, or parent-decision boundaries.

### 7. Host adapters and distribution

Keep one canonical protocol and provide thin adapters for Codex, Grok Build,
and Claude Code. Verify each host's actual hook, skill, command, worktree, and
terminal behavior. Do not assume a Claude feature exists in Grok or that a
skill in one catalog is installed and active in another.

## `yt-is` pilot path

The first useful pilot should exercise the protocol on the existing throughput
workflow without assuming that it will improve VPH:

1. Discover `yt-is` authority docs, active command/config paths, auth/profile
   names, worktree state, current decision packets, and quota boundaries.
2. Create an isolated task manifest for “find a higher sustained VPH.”
3. Delegate offline code/artifact inventory to bounded workers.
4. Synthesize a claim ledger and rank only evidence-backed mechanisms.
5. Implement a justified mechanism in the isolated worktree.
6. Run focused tests, runtime/path checks, and adversarial review.
7. Stop for parent authorization before auth, external quota use, or live
   benchmark execution.
8. If authorized, run the smallest packet-defined smoke with abort gates.
9. Analyze raw artifacts, update the decision packet and registry, and classify
   the branch as promoted, negative, blocked, partial, or closed.
10. Render a cold-start handoff and leave the integration decision explicit.

This pilot can demonstrate control-plane correctness and reduced churn. It
cannot prove that the current implementation is globally optimal or that a
future mechanism will beat the current observed VPH without fresh evidence.

## Task packets

### ACP-01 - Preflight and architecture inventory

**Objective:** Map existing skills, plugins, handoffs, runners, worktree rules,
hooks, receipts, and state stores. Identify canonical source versus cache and
which capabilities are actually active per host.

**Allowed work:** Read-only searches, config inspection, and small inventory
reports. No code edits, external calls, auth, stage, commit, or push.

**Acceptance:** A source-of-truth map, enforcement map, dependency graph, and
gap list with file paths and verification commands. Every “missing” claim must
show the search roots used.

**Falsifier:** A supposedly absent controller or receipt store is found in a
canonical root; update the design rather than inventing a duplicate.

### ACP-02 - Manifest, state machine, and receipt schema

**Objective:** Specify versioned schemas, transition rules, invalid-state
handling, idempotency keys, and migration/version policy.

**Acceptance:** Schema examples, validators, sample receipts, state diagrams,
and tests or executable validation fixtures. Include failure and resume cases.

**Falsifier:** Any transition can be reached without the required evidence, or
replaying a receipt can duplicate a write or expensive operation.

### ACP-03 - Worktree and capability broker

**Objective:** Design the least-authority mechanism for path writes, process
execution, external APIs, auth, quota, and integration actions.

**Acceptance:** Threat model, lease format, rejection behavior, dirty-tree
handling, process cleanup, and isolated tests proving out-of-scope writes and
unapproved capabilities are rejected.

**Falsifier:** A worker can modify protected paths, silently use quota, or
continue after the broker is unavailable.

### ACP-04 - Delegation router and cost accounting

**Objective:** Connect existing delegation skills to a dependency-aware router
with explicit model/effort selection and route receipts.

**Acceptance:** Cost/risk policy, route decision record, no-fallback behavior,
bounded retries, concurrency/backpressure rules, and a replayable packet.

**Falsifier:** The system cannot distinguish requested route from actual route,
or it hides provider failure behind an unverified fallback.

### ACP-05 - Verification, claim, and adversarial-review gates

**Objective:** Make completion and parent handoff machine-checkable while
preserving human judgment for strategy and integration.

**Acceptance:** Claim-ledger schema, gate validators, review packet format,
ready/needs-fix/blocked rules, and fixtures for tautological metrics, stale
artifacts, retry duplication, cohort degeneracy, and false live activation.

**Falsifier:** A worker can report `ready_for_parent_review` with a failed or
missing required gate, unsupported causal claim, or unverified runtime path.

### ACP-06 - Overnight supervisor and resume

**Objective:** Run authorized DAG branches overnight with durable checkpoints,
bounded progress, and safe pause/resume behavior.

**Acceptance:** Supervisor design or implementation, crash/restart replay tests,
timeout/process-tree cleanup, no-progress detection, quota/auth pause states,
and a morning report containing done, partial, blocked, and not-started work.

**Falsifier:** Restarting repeats an expensive completed phase, loses artifacts,
or proceeds through a user-auth or quota boundary without authorization.

### ACP-07 - Host adapters and skill migration

**Objective:** Define canonical protocol ownership and thin adapters for Codex,
Grok Build, and Claude Code. Migrate only after source/installation parity is
verified.

**Acceptance:** Host capability matrix, adapter contracts, installation and
active-surface checks, backward-compatible handoff rendering, and a migration
plan that does not edit caches as if they were source.

**Falsifier:** A host claims enforcement that its runtime does not load, or
adapter behavior changes the canonical authority model.

### ACP-08 - `yt-is` pilot and controlled evaluation

**Objective:** Evaluate whether the control plane reduces false completion,
duplicate expensive work, unsafe writes, and handoff loss on a real workflow.

**Acceptance:** Pre-registered scenarios, offline-first execution, no-quota
control, optional parent-authorized live boundary, outcome receipts, and a
critic-friend comparison against the current process.

**Falsifier:** The control plane adds ceremony without reducing failure/rework,
or improves reporting while weakening safety or slowing the critical path
without a measured benefit.

## Open decisions

- Extend the existing `cc-skills-sdlc` plugin, create a workspace package, or
  use a separate control-plane repository?
- Use JSON files, SQLite, or an event log plus materialized views for state?
- Is the mutation broker a process supervisor, a Git/worktree service, or a
  capability layer composed from existing tools?
- Which host APIs are stable enough for native adapters, and where should
  subprocess adapters be the fallback?
- Which capabilities always require parent/user approval: auth, external
  fetches, quota, destructive operations, stage/commit/push, and live runs?
- Should the goal compiler target a conservative 3800-character output so
  generated goals fit interfaces whose nominal maximum is 4000?
- What measurable threshold justifies the control plane's operational cost?

## Dependencies

- Existing skill source and installed-surface inventory.
- Workspace and repository worktree policy.
- Model, quota, and provider routing registry.
- Existing experiment-loop lifecycle and goal compiler.
- Host-specific runtime and hook documentation.
- `P:/packages/yt-is/AGENTS.md`, `P:/packages/yt-is/CLAUDE.md`, and
  `P:/packages/yt-is/HANDOFF.md` for the pilot only.
- A protected integration owner; workers must not infer merge authority.

## Hard constraints

- Read source-of-truth code, configuration, and runtime paths before making a
  diagnosis or proposal.
- Do not treat a skill, prompt, hook, or handoff as active enforcement without
  verifying that the target host loads it.
- Preserve concurrent and pre-existing dirty work. Never use destructive Git
  cleanup to make a report look clean.
- Workers write only through an authorized lease and isolated worktree.
- No automatic login, cookie copying, external fetch, quota use, live benchmark,
  stage, commit, merge, push, or deployment without explicit manifest
  capability and the required owner authorization.
- Parent/user owns strategy, risk acceptance, final judgment, and integration.
- Every completion claim needs outcome-bearing receipts. Focused tests alone do
  not prove runtime activation, transitive isolation, or production behavior.
- A hypothesis or inference may authorize evidence gathering, not an
  implementation or live experiment by itself.
- The control plane must fail closed at authority boundaries and fail visibly
  when its own receipts or validators are unavailable.

## Explicit non-goals

- An unbounded autonomous programmer that merges or deploys its own changes.
- A replacement for source control, CI, code review, or human ownership.
- Silent model/provider failover or fabricated cost/token accounting.
- Automatic user authentication or transfer of browser state.
- A prompt-only solution to state, authority, or evidence problems.
- A claim that the `yt-is` throughput problem is solved or globally optimal.

## Acceptance criteria for the overall design

The design is ready for implementation only when:

- a cold-start agent can resume from the manifest and handoff without the
  original chat transcript;
- every state transition has explicit required evidence and invalid-state
  behavior;
- protected worktrees and capabilities are rejected by executable tests;
- requested and host-verified model/runtime identity are both recorded;
- completed work is not repeated after restart unless the manifest says why;
- blocked, partial, and needs-input states are first-class and actionable;
- adversarial review is required before `ready_for_parent_review`;
- generated delegated goals are validated below the receiver's character limit;
- a held-out replay of known incidents shows fewer false-complete, unsafe-write,
  duplicate-work, or lost-handoff outcomes;
- the `yt-is` pilot can run offline first and pause cleanly at auth/quota/live
  boundaries.

## Design falsifiers

Reject or revise the design if any of the following is true:

- a worker can edit the protected main checkout or an unleased path;
- the state machine reaches `VERIFIED`, `REVIEWED`, or `INTEGRATED` without its
  required receipts;
- a resume repeats a completed expensive phase or loses its artifacts;
- missing runtime/model identity is accepted as if it were verified;
- the system silently falls back to another model/provider or capability;
- a stale, tainted, duplicated, or tautological metric can authorize action;
- the control plane only increases ceremony and does not reduce measured rework,
  unsafe operations, or false completion;
- a host adapter claims enforcement that its runtime does not actually load.

## Resumption protocol

1. Read this file completely before proposing implementation.
2. Read the existing handoffs listed under `Producing context` and the source
   skills listed there; distinguish source from installed/cache copies.
3. Run ACP-01 as a read-only inventory. Do not implement a controller before
   resolving canonical ownership and active-surface conflicts.
4. Record verified facts, inferences, hypotheses, and unsupported claims in a
   claim ledger. Do not use a proposal as evidence that a capability exists.
5. Implement one packet at a time in an isolated worktree, with tests and
   adversarial review before advancing the state.
6. Keep `yt-is` live work out of the design phase. Its pilot requires its own
   current decision packet and parent authorization at any auth/quota/live
   boundary.
7. End every session with a new handoff or an update to this handoff that
   states decision, files, commands, verification, risks, and next action.

## Suggested next invocation

Use a bounded first goal, not the entire design as one unverified coding task:

```text
/goal Build ACP-01 for the Agentic SDLC Control Plane. Read this handoff and the five representative Grok handoffs first. Then inspect the canonical source and active installation paths for cost-aware-delegation, delegation-packet-runner, preflight, evidence-driven-experiment-loop, review-packet-runner, and codex-pi. Produce a read-only inventory of source-of-truth files, active host surfaces, existing state/receipt/worktree/delegation mechanisms, conflicts, and gaps. Do not edit code, use external APIs, authenticate, run live yt-is work, stage, commit, or push. Use verified facts with file paths, separate inference from proposal, run an adversarial review of the inventory, and write a cold-start handoff with acceptance criteria and the next packet. Keep the goal under 3800 characters.
```

## Epistemic labels

Use these labels in future packets and reports:

- `[FACT]` - directly verified from source, config, artifact, or command output.
- `[MEASURED]` - derived from raw data with reproducible calculation.
- `[INFERENCE]` - plausible explanation not directly proven.
- `[HYPOTHESIS]` - candidate mechanism requiring a discriminating test.
- `[HISTORICAL]` - useful prior context that is not current authority.
- `[PROPOSAL]` - design choice not yet implemented or validated.
- `[UNSUPPORTED]` - must not drive implementation, authorization, or release.

## Changelog

| Date | Change |
|---|---|
| 2026-08-07 | Created as an open design handoff using the current Grok handoff format. No control-plane implementation performed. |

## Provenance

- Workspace head recorded at handoff creation:
  `688686f83cf206c1191f6316056316c3952ff215`.
- Format was derived from the representative `P:/docs/handoffs/*/HANDOFF.md`
  files listed under `Producing context`.
- This document is a proposal and must not be cited as proof that any proposed
  controller, broker, schema, or overnight supervisor already exists.
