---
title: "You are helping maintain and refine a set of SDLC skills for Claude Code: /go, /planning, /design, and /code.
The user c"
date: "2026-04-27"
mode: "CONCISE"
uuid: "a909837e-c383-4b61-9517-adc4cce8a06b"
entry_count: 3
---

## Human

You are helping maintain and refine a set of SDLC skills for Claude Code: /go, /planning, /design, and /code.
The user can provide you with:
Signatures-only packs like design_sig.md, planning_sig.md (Python signatures + embedded markdown).
Full SKILL.md files and implementation source for each skill.
Diagrams for the /code pipeline (Mermaid or screenshots).
Context and current architecture
/go
Owns worktree lifecycle: creates git worktrees per plan, dispatches subagents into those worktrees, and enforces that all downstream work (including /code) runs with cwd = worktree for /go-backed calls.
Mechanism: creates P:/worktrees/${PLAN_ID}, adds a git worktree, then spawns a subagent whose cwd is that worktree.
When /code is invoked via /go, it is already inside the correct worktree.
/go may provide a CLI guard (e.g., go-safe.sh) that checks git worktree list vs pwd, but that guard is outside /code.
/design
Already implemented as a contract-sensitive architecture closure skill.
Emits and validates:
ContractAuthorityPacket and related schemas (see schemas.py).
ADRs with stage-based validation (arch_validate.py, Stage 1.8 Closure Consistency, Stage 1.8b adversarial pre-check).
Planning Handoff Packets for /planning when architecture is contract-sensitive.
Ensures:
No contract-sensitive design is handed to /planning without a closed Contract Authority Packet.
ADRs are rejected if safety policy, router precision, packet/summary consistency, or downstream alignment gates fail.
When invoked by /planning, /design returns decision packets, not modified plans, and assumes automatic return-to-caller.
/planning remains the only writer of the executable plan artifact.
/planning
Already implemented as a strict plan generator and readiness gate.
Produces implementation plans with:
Explicit boundary matrices (boundary, contract authority packet, producer, consumer, input/output schema, freshness authority, invalidation triggers, failure behavior, packet alignment, test binding).
Recommended Next Steps (RNS) when there are blockers or non-ready status.
Additional required decisions for stateful/history/provider/multi-terminal plans: identity model, ordering contract, dedupe contract, freshness/invalidation, source of truth, isolation boundary, contract-to-test alignment, triggerability.
A plan cannot be marked implementation-ready while:
It contains placeholders, unresolved blockers, raw review output, or implied producer/consumer contracts.
Required CAP references are missing or drifted.
/planning owns: plan rewrites, status corrections, matrix completion, and disposition cleanup.
/code (current state and intent)
/code is a single-task TDD implementation engine that will:
Accept a plan or a direct prompt (or plan derived from /planning).
Run TDD phases (RED → GREEN → REFACTOR) while delegating actual code work to an external LLM executor (ai-pCLI).
Important constraints:
/code should be an orchestrator, not a heavy thinker:
It should normalize inputs, enforce preconditions, ensure it is in the right environment, then delegate work.
TDD phases should be modeled as:
/code orchestrator step → ai-pCLI execution step → /code validation step.
When invoked via /go, worktree guarantee is provided by /go’s dispatch; /code must not attempt to create or switch worktrees itself.
When invoked standalone, /code runs in whatever directory the user is in; this mode is intentionally “unsafe but convenient” for quick local tasks. No mandatory worktree check.
Desired behavior:
If a valid implementation plan exists from /planning, /code should use it and not re-plan or re-interpret architecture text.
If no plan exists and the task is non-trivial, /code should route to /planning to create one.
For truly trivial tasks, /code may generate a micro-plan internally (1–3 steps), but heavy decomposition belongs to /planning.
Delegation of implementation should go to ai-pCLI / external coding LLMs, with /code focusing on spec building, result validation, and routing decisions.
What needs to be done
The goal for this session is not to redesign /design or /planning (they already implement the proposals) but to:
Clarify and document /code’s role and contracts in a way that is consistent with the existing /design and /planning systems.
Define /code’s pipeline and state machine so that:
It consumes plans and packets coming from /planning and /design.
It treats /go as the worktree owner without adding unnecessary friction.
It cleanly separates orchestrator vs executor work for TDD phases.
Concretely, the user wants from you:
A precise description of /code’s responsibilities and non-responsibilities, in terms of:
/go (worktree lifecycle and environment).
/planning (plan generation and readiness).
/design (architecture closure, CAP, planning-handoff packets).
An updated /code execution pipeline, at the level of SKILL.md and diagrams, that includes:
Input resolution (plan vs direct prompt vs chat context).
The pre-execution checklist / readiness gate, including where it routes to /planning or /design and where it proceeds.
How and when /code interacts with the worktree (assumptions vs checks) for:
/go-backed calls (worktree guaranteed), and
standalone /code calls (no guarantee, but allowed).
The orchestrator/executor split for TDD RED, GREEN, and REFACTOR:
/code step naming and responsibilities.
ai-pCLI/external LLM step and how /code validates its results.
Terminal states and error paths (when to route back to /planning, when to surface failure).
A SKILL.md-ready section (you can draft it in markdown) that the user can paste into /code’s SKILL file, covering:
“What /code assumes when invoked via /go.”
“How /code behaves when invoked standalone.”
“How /code consumes plans from /planning and decisions/packets from /design.”
A brief TDD-phase description with the two-box pattern: /code orchestrator node + external executor node.
Optionally, a Mermaid diagram or similar text diagram of the /code pipeline that:
Starts from “task + plan status + invocation mode” and ends at “task result written.”
Shows the worktree assumption for /go-backed calls.
Shows the delegation edges to ai-pCLI for TDD phases.
How to work
Assume the existing /design and /planning contracts in the provided signature/source packs are authoritative; do not try to re-invent them, only align /code with them.
Use the signature packs and SKILL.md/source files the user provides as the source of truth.
Keep /code as lean as possible: orchestration, routing, validation, and delegation, not deep architecture or planning.
When in doubt:
/design owns architecture and CAPs.
/planning owns plans and readiness gating.
/go owns worktree and environment.
/code owns “given a ready plan and environment, run TDD using external LLMs and report back.”
Please start by summarizing your understanding of the current /go–/design–/planning–/code stack as described above, then propose a concrete /code SKILL.md “Execution & Routing” section and corresponding pipeline diagram that satisfies these constraints.

## Assistant

Your current stack is already **well-factored**: `/go` owns execution environment and worktree lifecycle, `/design` owns architecture closure and Contract Authority Packets, `/planning` owns executable plan artifacts and readiness gating, and `/code` should remain a narrow TDD delivery orchestrator that consumes ready inputs and delegates actual coding work to an external executor rather than re-planning or re-designing locally.[1]

## Stack model

`/go` is the outer execution controller for plan-backed delivery: it creates the git worktree, dispatches the subagent into that worktree, selects tasks, controls loop behavior, and keeps ownership of downstream orchestration concerns like review and PR artifacts. `/code` therefore inherits the correct working directory for `/go`-backed calls and does not need to create, switch, or independently enforce worktree isolation in that mode.[1]

`/design` is the authority for architecture closure on contract-sensitive work, including CAP production and planning handoff packets, while `/planning` is the sole writer of executable plan artifacts and the owner of readiness state, matrix completion, and plan rewrites. `/code` should therefore consume plan and packet outputs as authoritative inputs, not reinterpret architecture prose, not mutate plan semantics, and not substitute its own decomposition when `/planning` has already declared the work implementation-ready.[1]

## `/code` role

The cleanest role statement is: `/code` owns “given a sufficiently ready task and the current environment, execute one TDD implementation cycle through external coding agents, validate the result, and emit a task result.” That aligns with the existing code skill text that describes `/code` as a “spec-and-validate orchestrator,” not the component that writes tests or implementation logic itself.[1]

Its responsibilities should be limited to:
- Resolve input source: ready plan task, direct prompt, or lightweight standalone task context.[1]
- Perform a pre-execution readiness check on clarity, scope, code location, and testability.[1]
- Route non-ready or ambiguous work back to `/planning`, and to `/design` only indirectly via `/planning` when architecture closure is missing.[1]
- Run RED, GREEN, and REFACTOR as orchestrator stages with external executor delegation in each phase.[1]
- Validate each phase with concrete test or smoke evidence before proceeding.[1]
- Emit completion, blocked, or failed results in a machine-consumable artifact for `/go` or the user.[1]

Its non-responsibilities should be explicit:
- No worktree creation, switching, or branch isolation logic; `/go` owns that.[1]
- No plan authoring, multi-task decomposition, readiness graduation, or plan rewriting; `/planning` owns those.[1]
- No architecture closure, CAP generation, ADR closure, or contract authority decisions; `/design` owns those.[1]
- No autonomous multi-task loop or portfolio-style orchestration; `/go` owns task selection and loop control.[1]

## SKILL.md draft

### Execution & Routing

```md
## Execution & Routing

/code is a single-task TDD implementation orchestrator. Its job is to take a ready implementation task plus the current execution environment, run RED -> GREEN -> REFACTOR through an external coding executor, validate each phase, and emit a task result artifact. It is not a planning skill, not an architecture skill, and not a worktree-management skill. [file:1]

### Ownership Boundaries

- `/go` owns worktree lifecycle, environment isolation, task selection, outer-loop orchestration, and post-code review flow. When `/code` is invoked by `/go`, `/code` assumes the current working directory is already the correct isolated worktree and must not create, switch, or re-home worktrees. [file:1]
- `/planning` owns executable plan generation, plan rewrites, readiness status, boundary-matrix completeness, and Recommended Next Steps. `/code` consumes plan tasks; it does not rewrite or “improve” the plan on its own. [file:1]
- `/design` owns architecture decision closure, Contract Authority Packets, ADR closure, and planning handoff packets for contract-sensitive work. `/code` may rely on design-produced packets only as already-consumed upstream authority, normally via `/planning`; it must not replace or reinterpret design authority. [file:1]

### Invocation Modes

#### 1. `/go`-backed invocation
When invoked through `/go`, `/code` assumes:
- the current process is already running inside the correct git worktree;
- task selection has already been completed upstream;
- any required plan context has already been chosen upstream;
- downstream tools invoked by `/code` inherit the same working directory automatically. [file:1]

In this mode, `/code` performs no worktree switching and no mandatory worktree verification. It may log the current directory for traceability, but that log is diagnostic only and must not become a blocking precondition. This keeps `/go` as the sole owner of environment isolation. [file:1]

#### 2. Standalone invocation
When invoked directly by the user, `/code` runs in the user's current directory as-is. This mode is intentionally less safe but convenient for quick local implementation tasks. `/code` does not require a worktree check in standalone mode and must not force the user through `/go` just to make local progress. [file:1]

### Input Resolution

`/code` resolves inputs in this order:

1. A selected implementation task from an existing ready plan.
2. A direct user request that names a narrow, bounded implementation task.
3. Current session/chat context when the task is still obviously trivial and local.

If a valid implementation-ready plan task exists, `/code` must use that task contract as authoritative and must not re-plan from architecture prose or freeform notes. If no such plan exists and the work is non-trivial, stateful, cross-boundary, or likely to require decomposition, `/code` routes to `/planning` instead of inventing a larger plan internally. [file:1]

For truly trivial work, `/code` may form a micro-plan internally, but only as execution scaffolding for the current task. Micro-plans are not substitutes for `/planning` on multi-step or contract-sensitive work. [file:1]

### Pre-Execution Readiness Gate

Before starting TDD, `/code` checks:

1. Do I understand what “done” looks like?
2. Do I know where the relevant code lives?
3. Is the scope clear and bounded?
4. Do I need exploration first?
5. Are there existing tests or a clear validation path? [file:1]

Interpretation rules:
- If Q1, Q2, or Q5 fail in a way that can be repaired by brief local exploration, `/code` may perform bounded exploration first. [file:1]
- If Q3 fails because scope is unclear, acceptance criteria are ambiguous, decomposition is missing, or the task appears larger than a single TDD unit, `/code` must stop and route to `/planning`. [file:1]
- If the blocking issue is architectural authority, missing CAP closure, unresolved boundary semantics, or other design-class ambiguity, `/code` routes back through `/planning`, which remains responsible for invoking `/design` when required. [file:1]

`/code` must not guess past failed readiness gates. If the task becomes non-ready mid-execution, it emits a replan request artifact and stops rather than silently broadening scope. [file:1]

### Plan and Packet Consumption

When `/planning` has produced an implementation-ready plan, `/code` consumes:
- the selected task's objective, scope, acceptance criteria, and verification hints;
- any explicit contract references already attached to the plan;
- any design decisions already normalized into the plan artifact. [file:1]

When contract-sensitive packets exist:
- the latest CAP remains authoritative for boundary semantics;
- the latest planning handoff packet remains authoritative for normalized extraction into the plan;
- `/code` uses those only through the task and plan contract it receives, not by inventing alternate interpretations. [file:1]

If plan text, packet references, and observed workspace reality conflict, `/code` should not repair authority locally. It should stop, surface the mismatch, and route back to `/planning` for correction, with `/planning` escalating to `/design` if the mismatch is architectural. [file:1]

### TDD Two-Box Pattern

Every TDD phase follows the same two-box pattern:

1. `/code` orchestrator step  
   - defines the phase objective, constraints, touched files, acceptance target, and validation method;
   - builds a precise executor prompt/spec for the current phase only;
   - limits scope to the current task and current phase. [file:1]

2. External executor step (`ai-pCLI` / coding LLM)  
   - performs the concrete code or test edit;
   - returns modified artifacts and execution notes for the requested phase only. [file:1]

3. `/code` validation step  
   - runs the relevant tests, checks diffs against phase intent, and confirms the expected state transition before advancing. [file:1]

### Phase Semantics

#### RED
`/code` defines the failing behavior to prove, instructs the external executor to add or adjust tests that encode the acceptance criteria, and then validates that the test fails for the expected reason. RED is incomplete if no failing proof exists or if the failure is unrelated to the target behavior. [file:1]

#### GREEN
`/code` instructs the external executor to make the minimal implementation change needed to satisfy the RED test set, then validates that the targeted tests now pass. GREEN is incomplete if passing requires scope creep, hidden architectural changes, or unresolved regressions outside the agreed task boundary. [file:1]

#### REFACTOR
`/code` instructs the external executor to improve structure while preserving behavior, then validates that tests still pass and that no contract or scope boundary was widened. REFACTOR is behavior-preserving cleanup, not opportunistic redesign. [file:1]

### Exploration Rules

Exploration is allowed only to answer local execution questions such as file location, existing test patterns, or nearby implementation conventions. Exploration must not turn into hidden planning, hidden architecture work, or broad repository archaeology. If exploration reveals that the task is bigger, cross-cutting, or underspecified, `/code` stops and routes to `/planning`. [file:1]

### Terminal States

`/code` ends in one of these terminal states:

- `completed`: RED, GREEN, and REFACTOR are validated; the task result artifact is written. [file:1]
- `blocked`: execution cannot continue without upstream planning or architecture clarification; emit a replan request or equivalent blocker artifact. [file:1]
- `failed`: executor output, tests, or validation failed in a way that cannot be safely recovered within the current single-task scope. [file:1]

Routing rules:
- Route to `/planning` when scope, acceptance criteria, decomposition, sequencing, or task boundaries are unclear. [file:1]
- Route back through `/planning` for CAP drift, missing architectural closure, boundary ambiguity, or packet-authority mismatch, because `/planning` owns the executable artifact and `/design` owns architecture closure. [file:1]
- Surface direct failure to the caller when the task was ready, the environment was usable, but implementation/validation still failed after bounded retries. [file:1]

### Worktree Interaction Policy

`/code` never creates or switches worktrees. [file:1]

- In `/go`-backed mode, worktree correctness is assumed from process inheritance and treated as an upstream guarantee. [file:1]
- In standalone mode, the user's current directory is accepted as the execution root without mandatory safety checks. [file:1]

This preserves convenience for standalone usage while keeping `/go` as the sole owner of safe isolated delivery. [file:1]
```

## Pipeline diagram

This version keeps `/code` lean and routes authority back to the existing owners instead of duplicating them. The key design choice is that `/code` only decides between “proceed,” “bounded explore,” “route to planning,” and “fail/block”; it does not acquire new planning or design ownership.[1]

```mermaid
flowchart TD
    A[Start: task + plan status + invocation mode] --> B{Invocation mode?}

    B -->|via /go| C[/go-backed environment assumed correct worktree/]
    B -->|standalone| D[Use current directory as-is]

    C --> E[Resolve input]
    D --> E

    E --> F{Ready task available?}
    F -->|Yes: implementation-ready plan task| G[Consume task contract from /planning]
    F -->|No, but trivial and bounded| H[Create micro-plan for this task only]
    F -->|No, non-trivial or cross-boundary| I[Route to /planning]

    G --> J[Pre-execution checklist]
    H --> J

    J --> K{Checklist outcome}
    K -->|Need bounded local exploration| L[Explore relevant code/tests only]
    K -->|Scope unclear or decomposition missing| I
    K -->|Architecture/CAP authority unclear| M[Return to /planning; /planning may invoke /design]
    K -->|Ready| N[TDD RED orchestrator step]

    L --> J

    N --> O[ai-pCLI executor: write failing test]
    O --> P[/code validation: test fails for expected reason?]
    P -->|No| Q[Blocked or failed]
    P -->|Yes| R[TDD GREEN orchestrator step]

    R --> S[ai-pCLI executor: minimal implementation]
    S --> T[/code validation: target tests pass?]
    T -->|No| Q
    T -->|Yes| U[TDD REFACTOR orchestrator step]

    U --> V[ai-pCLI executor: behavior-preserving cleanup]
    V --> W[/code validation: tests still pass and scope preserved?]
    W -->|No| Q
    W -->|Yes| X[Smoke validation]

    X --> Y{Smoke/result valid?}
    Y -->|Yes| Z[Write task result artifact]
    Y -->|No, now reveals plan/scope ambiguity| I
    Y -->|No, implementation failure| Q

    I --> I2[Stop current execution and hand off to /planning]
    M --> I2
    Q --> Q2[Surface blocked/failed result]
    Z --> Z2[Task result written]
```

## Tightening points

A few points are worth stating explicitly in the final `/code` text because they prevent future overlap creep.

First, `/code` should consume plans, not “understand architecture from scratch.” The moment a ready plan exists, `/code` should treat it as the authoritative executable surface and avoid reinterpretation of ADR prose, CAP prose, or narrative design text. That follows the current planning contract that planning owns the executable artifact and consumes design packets authoritatively.[1]

Second, the worktree policy should be asymmetric by design: assumed-and-nonblocking under `/go`, permissive-and-unsafe in standalone mode. That matches the existing code text that says `/go` enforces isolation externally and standalone code uses the current directory intentionally.[1]

Third, routing to `/design` should usually be indirect. The stack you described already places `/planning` between architecture closure and executable work, so the safest statement is that `/code` detects authority gaps and routes to `/planning`, which then invokes `/design` when architecture closure is actually required. That preserves a single writer for plan artifacts and avoids `/code` becoming a second planning surface.[1]

Would you like me to turn this into a stricter drop-in replacement block that matches your existing `/code` SKILL.md voice and formatting conventions line-for-line?

## Human

First, what am I supposed to do with what you provided?  Give it to the implementing LLM?

## Assistant

Yes — the main thing to do with what I gave you is **hand it to the implementing LLM as the target contract/spec** for `/code`, then have it rewrite the `/code` SKILL.md and any accompanying diagram/docs to match that contract. The reason that works is that your current stack already gives ownership boundaries to `/go`, `/planning`, and `/design`, and `/code` is already defined as a single-task TDD engine plus spec/validate orchestrator, so the missing piece is mainly alignment and codification, not a fresh redesign.[1]

## What it is for

Treat my previous answer as a **design brief for the `/code` skill rewrite**, not as end-user prose and not as runtime behavior by itself. The implementing LLM should convert it into concrete repo artifacts: updated `/code/SKILL.md`, any Mermaid diagram or reference markdown you keep beside it, and only the smallest supporting implementation changes needed to make the docs and behavior consistent.[1]

Do **not** give it as “please think about this generally.” Give it as “update `/code` so it matches these boundaries: `/go` owns worktrees, `/planning` owns plans/readiness, `/design` owns CAP/architecture closure, `/code` owns single-task TDD orchestration and validation.” That matches the authoritative ownership split already present in your pack.[1]

## What to ask for

A good instruction to the implementing LLM is:

- Update `/code` SKILL.md to add an “Execution & Routing” section.
- Preserve existing ownership: `/go` = worktree/environment, `/planning` = plan artifact/readiness, `/design` = architecture/CAP, `/code` = single-task TDD orchestration.[1]
- Keep `/code` lean: no worktree creation, no plan rewriting, no architecture closure, no outer loop.[1]
- Make explicit the two invocation modes: `/go`-backed assumes inherited worktree cwd; standalone accepts current directory as-is.[1]
- Make TDD phases use the two-box pattern: `/code` orchestrator step -> external executor step -> `/code` validation step.[1]
- Add terminal states and routing rules: complete, blocked, failed; route ambiguity to `/planning`, not ad hoc local reasoning.[1]

That is the minimum useful ask because it translates the conceptual material into a patchable implementation target.[1]

## What not to do

Do not hand my answer to the implementing LLM as if it should become a new planning system or new architecture framework. Your pack is already explicit that `/planning` owns executable plans and readiness, and that `/design` owns architecture closure and CAP semantics, so any `/code` rewrite that starts doing its own decomposition or contract interpretation would be regression-by-overlap.[1]

Also do not treat my draft as authoritative over your repo if the full `/code` source or full SKILL.md disagrees in some detail. The pack you provided is signatures-only, so my proposal should be used as an alignment draft against the actual source of `/code`, not blindly pasted without checking local wording, hooks, flags, and artifact names.[1]

## Best next step

The best next step is to give the implementing LLM a **tight editing task**, not an open-ended architecture question. For example: “Rewrite the `/code` SKILL.md Execution & Routing section so it explicitly says `/go` owns worktree isolation, `/planning` owns plans/readiness, `/design` owns architecture/CAP closure, and `/code` is a single-task TDD spec/validate orchestrator that delegates RED/GREEN/REFACTOR to ai-pCLI and validates each phase.” That is directly supported by the current `/code` pack language around single-task TDD, standalone mode, pre-execution checklist, and inherited worktree isolation under `/go`.[1]

If you want, I can next produce the **exact implementer prompt** you should paste into Claude Code or another coding LLM, optimized to minimize drift and overreach.

## Human

yes please

## Assistant

Yes — here is the prompt I’d give the implementing LLM.

## Implementer prompt

```md
You are updating the `/code` SDLC skill so it aligns cleanly with the already-established `/go`, `/planning`, and `/design` contracts.

Your job is NOT to redesign the system. Your job is to make `/code` explicit, lean, and contract-aligned.

## Authoritative ownership model

Treat these boundaries as fixed:

- `/go` owns worktree lifecycle, environment isolation, task selection, outer-loop orchestration, simplify/review/PR flow, and dispatch into the correct cwd/worktree. [file:1]
- `/planning` owns executable plan generation, plan rewrites, readiness status, matrix completion, and Recommended Next Steps. It is the only writer of the executable plan artifact. [file:1]
- `/design` owns architecture closure, ADR closure, Contract Authority Packets (CAP), and planning handoff packets for contract-sensitive work. [file:1]
- `/code` owns single-task implementation execution: given a ready task and current environment, run TDD through external coding executors, validate each phase, and emit a task result. [file:1]

Do not weaken or blur those boundaries.

## Existing `/code` behavior to preserve

Preserve and clarify these existing truths already present in the pack:

- `/code` is a single-task TDD implementation engine. [file:1]
- `/code` is a spec-and-validate orchestrator, not the primary deep thinker or planner. [file:1]
- `/code` should consume a task contract from `/go` when invoked that way. [file:1]
- `/code` already has a pre-execution checklist with five questions around done-state clarity, code location, scope boundedness, exploration need, and existing tests. [file:1]
- When checklist failure indicates unclear scope, `/code` should emit a replan request and route to planning rather than guessing. [file:1]
- When `/code` is invoked via `/go`, worktree isolation is inherited from process cwd and should not be reimplemented inside `/code`. [file:1]
- When `/code` is invoked standalone, it runs in the user’s current directory as-is; this is intentionally less safe but convenient. [file:1]

## Required outcome

Update `/code` so its SKILL.md and any closely related docs clearly describe:

1. `/code` responsibilities and non-responsibilities.
2. Input resolution: plan task vs direct prompt vs session/chat context.
3. Pre-execution readiness gate and routing behavior.
4. `/go`-backed vs standalone worktree assumptions.
5. TDD RED -> GREEN -> REFACTOR as a two-box pattern:
   - `/code` orchestrator step
   - external executor step (ai-pCLI / coding LLM)
   - `/code` validation step
6. Terminal states and error/reroute behavior.
7. How `/code` consumes plans from `/planning` and design-derived packet authority without re-planning or re-designing locally.

## Critical constraints

### Keep `/code` lean
Do NOT add any of the following to `/code`:

- worktree creation
- git worktree switching
- branch-management logic
- plan rewriting
- plan readiness graduation
- CAP generation
- ADR generation
- architecture closure logic
- autonomous multi-task loop behavior
- simplify gating
- 7-pass review ownership
- PR artifact generation

Those belong elsewhere in the stack. [file:1]

### Routing rules
Implement the narrative and wording so these rules are explicit:

- If a valid implementation-ready plan task exists, `/code` should consume it as authoritative and should not re-plan from freeform architecture or ADR prose. [file:1]
- If no ready plan exists and the work is non-trivial, cross-boundary, stateful, or under-scoped, `/code` should route to `/planning`. [file:1]
- If ambiguity is architectural, CAP-related, boundary-related, or contract-authority-related, `/code` should not invent answers; it should route back through `/planning`, which remains the owner of executable artifacts and can invoke `/design` when required. [file:1]
- For truly trivial work only, `/code` may form a micro-plan internally, but only as lightweight execution scaffolding, not as a substitute for `/planning`. [file:1]

### Worktree policy
Make this explicit:

- In `/go`-backed mode, `/code` assumes cwd is already the correct worktree and does not perform mandatory worktree checks or switching. `/go` owns that. [file:1]
- In standalone mode, `/code` uses the current directory as-is and does not force `/go`. [file:1]

### TDD delegation model
Make the phase model explicit and repeatable:

For each of RED, GREEN, REFACTOR:
1. `/code` defines the phase objective, scope, constraints, acceptance target, and validation method.
2. External coding executor performs the concrete edit.
3. `/code` validates the result before progressing.

Validation expectations:
- RED must prove the relevant failing test exists and fails for the expected reason.
- GREEN must prove targeted tests pass without unauthorized scope creep.
- REFACTOR must preserve behavior and keep tests passing. [file:1]

### Terminal states
Document these terminal states:

- `completed`
- `blocked`
- `failed`

And make the routing behavior clear:
- route to `/planning` for unclear scope/decomposition/acceptance boundaries;
- route back through `/planning` for architecture/CAP/authority mismatch;
- surface direct failure when the task was ready but execution/validation still failed within bounded retries. [file:1]

## Deliverables

Produce these outputs:

1. An updated `/code/SKILL.md` section titled `Execution & Routing` or equivalent, ready to paste into the skill.
2. If there is an existing pipeline diagram for `/code`, update it to match the new contract.
3. If there are nearby helper docs or reference markdown files describing `/code` flow, update only the minimal set necessary to stay consistent.
4. Do not change unrelated skill ownership docs unless a wording mismatch makes `/code` inconsistent with an already authoritative contract.

## Preferred editing style

- Prefer minimal necessary edits over sweeping rewrites.
- Reuse existing wording where possible if it already matches the required contract.
- Tighten ambiguous language like “may think through” or “understand architecture” if it suggests `/code` owns planning or design.
- Replace vague wording with owner-specific wording.
- Keep implementation behavior and documentation aligned.

## Suggested SKILL.md content goals

The resulting `/code` text should clearly answer:

- What `/code` assumes when invoked via `/go`.
- How `/code` behaves when invoked standalone.
- How `/code` consumes plan tasks from `/planning`.
- How `/code` relies on design-derived authority without taking ownership of design.
- What `/code` does in RED, GREEN, and REFACTOR.
- When `/code` stops and emits a replan request instead of guessing.

## Optional diagram shape

If you update a Mermaid diagram, the flow should roughly be:

Start: task + plan status + invocation mode
-> invocation mode split (`/go`-backed vs standalone)
-> input resolution
-> ready task? yes/no
-> pre-execution checklist
-> route to planning if not ready
-> RED orchestrator -> external executor -> validation
-> GREEN orchestrator -> external executor -> validation
-> REFACTOR orchestrator -> external executor -> validation
-> smoke validation
-> write task result
-> completed / blocked / failed

The diagram must show:
- `/go`-backed worktree guarantee as an assumption, not as a `/code` action.
- delegation edges to ai-pCLI/external executor for each TDD phase.
- routing back to `/planning` when execution reveals scope or authority ambiguity.

## Guardrails against overreach

Before finalizing, check your own output against these questions:

- Did I accidentally make `/code` a planner?
- Did I accidentally make `/code` a design authority?
- Did I accidentally make `/code` manage worktrees?
- Did I accidentally move loop/review/simplify/PR responsibilities out of `/go`?
- Did I accidentally let `/code` reinterpret ready plan artifacts instead of consuming them?

If yes, fix it before final output.

Now inspect the existing `/code` skill text and supporting docs, then produce the minimal patch set needed to implement this alignment.
```

## How to use it

Paste that prompt into the implementing LLM **along with the real `/code` files**, not just the signatures pack, because the signatures-only pack gives the contract shape but may omit wording or helper-file details that matter during editing. The prompt is strongest when the model can diff the current `/code` SKILL.md against the target behavior instead of generating a fresh replacement from scratch.[1]

If you want tighter control, add one final instruction: “Show me a proposed diff plan before editing files.” That usually reduces overreach and helps catch the exact failure mode you’re worried about, which is the implementing model silently turning `/code` into a planner or worktree manager.[1]

## One caution

My confidence is high on the ownership split and the prompt framing, but moderate on exact file-level edit scope because I only saw the signatures pack, not your full `/code` implementation tree. The prompt is therefore best used as an **alignment-and-edit contract**, then checked against actual source before you accept the changes.[1]

Would you like a second version of this prompt that is shorter and more forceful, optimized for Claude Code specifically?
