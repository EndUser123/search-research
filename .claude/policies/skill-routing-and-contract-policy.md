# Skill Routing and Contract Policy

## Purpose

Define the mandatory routing policy for AI-assisted SDLC work in this workspace.

This policy optimizes for:

- multi-terminal isolation
- stale-data immunity
- compact-event recovery
- explicit producer/consumer contracts
- evidence-bound execution

This policy is intentionally biased toward long-term correctness over transition cost or short-term speed.

## Core Rule

No stateful, multi-terminal, resumable, or workflow-infrastructure change may proceed on implied contracts.

Every handoff between skills, sessions, hooks, plans, files, or agents must define and verify:

1. input schema
2. output schema
3. producer responsibility
4. consumer validation
5. source of truth
6. freshness and invalidation rule
7. isolation boundary
8. contract-to-test binding

If any of these are missing, the work is not ready to advance.

For contract-sensitive work, `/arch` should emit a minimal machine-readable **Contract Authority Packet**. This packet is authoritative for boundary semantics and closure status; prose is explanatory only.

## Routing Spine

### Standard Flow

Use this as the default workflow for non-trivial work:

`/recap -> /gto -> /top-problems -> /arch -> /planning -> /pre-mortem -> /code -> /critique -> /verify -> /sqa`

### Purpose by Skill

| Skill | Role | Mandatory When |
|---|---|---|
| `/recap` | Resume/reconstruct context from transcripts | After compaction, interruption, terminal handoff, or long pause |
| `/gto` | Explore current gaps and stale assumptions | Before planning or coding non-trivial work |
| `/top-problems` | Rank system-level issues across evidence | When multiple candidate problems or repeated failures exist |
| `/arch` | Close architecture and state contracts | For stateful, resumable, cross-session, hook, provider, persistence, event, or multi-terminal work |
| `/planning` | Produce executable plan artifact only after contract closure | For any work that spans multiple tasks/files/phases |
| `/pre-mortem` | Stress-test failure modes before implementation | For risky, stateful, or workflow-critical work |
| `/code` | Implement with TDD and trace | For actual code changes |
| `/critique` | Adversarial blind-spot review | Before claiming done on non-trivial work |
| `/verify` | Feature-level proof via 4 tiers | Before claiming verified |
| `/sqa` | System-level certification | For hooks, skills, workflows, orchestration, or quality infrastructure |

## Mandatory Trigger Rules

### 1. Resume and Interruption Policy

Run `/recap` first when any of the following are true:

- session compacted
- new session resumes prior work
- terminal changed
- prior work depends on transcript or handoff state
- there is uncertainty about what was completed vs only discussed

Rule:

- transcript-derived reconstruction is authoritative over memory-style summaries
- handoff envelopes are advisory until contract-validated

### 2. Explore Policy

Run `/gto` before `/planning` or `/code` when:

- the target is not trivial
- the change touches an existing subsystem
- the work follows a prior failed attempt
- the user asks for “optimal”, “best”, “what are we missing”, or “gaps”

Run `/top-problems` before `/arch` or `/planning` when:

- there are multiple recurring failures
- repeated regressions exist
- several evidence sources point to different symptoms
- the system may be optimizing a symptom rather than the root cause

### 3. Architecture Closure Policy

Run `/arch` before `/planning` for all work touching:

- persistence
- handoff/resume state
- providers or external identities
- transcripts or ledgers
- event-driven logic
- hook orchestration
- stale-data prevention
- locking, dedupe, invalidation, or replay
- multi-terminal/shared workspace state

`/arch` must close at minimum:

- identity model
- ordering contract
- dedupe contract
- freshness/invalidation contract
- event source of truth
- isolation boundary
- trigger conditions
- contract-to-test alignment notes

If `/arch` cannot close those, the design is incomplete and must not be treated as implementation-ready.

### Contract Authority Rules

- The Contract Authority Packet is authoritative for boundary closure and downstream enforcement.
- ADR prose, summaries, and recommendations are explanatory only.
- If packet and prose disagree, downstream consumers must follow the packet.
- If packet and runtime artifact state disagree, the packet's named freshness authority decides the winner.
- If freshness cannot be proven, stop and reconstruct from authoritative source rather than continuing optimistically.

### 4. Planning Policy

Run `/planning` for:

- any multi-step change
- any change spanning more than one file or subsystem
- any work that must survive interruption or compaction
- any work needing acceptance criteria or blocker remediation

`/planning` remains the sole writer of the plan artifact.

No plan may be `implementation-ready` if it contains:

- placeholders
- unresolved contract ambiguity
- unresolved architecture blockers
- tests that do not assert the named contracts
- raw review output pasted into the plan

### 5. Risk Policy

Run `/pre-mortem` before `/code` when work is:

- stateful
- resumable
- contract-heavy
- security-sensitive
- workflow-critical
- difficult to reverse

The pre-mortem must explicitly include:

- new risks introduced by the proposed fix
- warning signs
- escalation triggers
- remaining items if not fully resolved

### 6. Implementation Policy

Run `/code` only after:

- current context has been explored
- architecture is closed if stateful
- a plan exists for non-trivial work
- contract inputs/outputs are known
- acceptance/tests exist or are defined

`/code` must not invent missing cross-session or cross-component contracts mid-implementation.

### 7. Review Policy

Run `/critique` before claiming “done” for:

- hooks
- skills
- orchestration logic
- session/handoff logic
- anything stateful or resumable
- any change with high blast radius

Use critique as blind-spot detection, not as optional polish.

### 8. Verification Policy

Run `/verify` before claiming “verified”.

Run `/sqa` in addition to `/verify` when the target affects:

- hook chains
- routing/orchestration
- skill integration
- system quality infrastructure
- requirements/operational/security interactions

For workflow infrastructure, `/verify` without `/sqa` is insufficient.

## Contract Checklist

Use this checklist at every producer/consumer boundary.

### Required Contract Fields

| Field | Required Question |
|---|---|
| Contract name | What exact boundary is being crossed? |
| Producer | Who writes or emits the artifact/state/payload? |
| Consumer | Who reads, restores, routes, or depends on it? |
| Input schema | What fields/types must exist before processing starts? |
| Output schema | What fields/types are guaranteed after completion? |
| Required fields | Which fields are mandatory vs optional? |
| Ownership | Who is allowed to mutate each field? |
| Freshness authority | Which source is authoritative when values disagree? |
| Invalidation | What exact event makes this output stale? |
| Isolation boundary | Is this terminal-private, session-private, or workspace-shared? |
| Failure behavior | What happens when a required field is missing or stale? |
| Verification | Which test/check proves the contract holds? |

### Minimum Rule

No consumer may assume a field exists just because a producer was intended to emit it.

Consumers must validate required fields before acting.

### Preferred Enforcement

For local hooks and internal Python boundaries:

- use schema validation at runtime
- fail fast on missing required fields
- stop or pause instead of continuing on partial state

For higher-level workflow artifacts:

- validate artifact presence, status, freshness, and ownership before use

## Freshness and Stale-Data Policy

All skill outputs are stale unless freshness is explicitly checked.

### Freshness Rules

1. Transcript and current workspace state outrank older summaries.
2. Latest verification artifact outranks earlier commentary.
3. Git/workspace changes invalidate prior planning and review conclusions where relevant.
4. Skill coverage logs and evidence may inform routing, but never override current source state.

### Required Freshness Questions

- What source is authoritative right now?
- What event invalidates this artifact?
- Has the underlying file/state/git context changed since this was produced?
- Is this state terminal-scoped, session-scoped, or shared?

If freshness cannot be proven, rerun the producing skill.

## Multi-Terminal Isolation Policy

All state must explicitly declare its isolation level:

- terminal-private
- session-private
- workspace-shared

### Rules

1. Terminal-private state must never be reused as workspace truth.
2. Workspace-shared state must include invalidation and dedupe semantics.
3. Session recovery must not depend on another terminal’s unstated assumptions.
4. File naming, ledgers, and evidence directories must avoid collisions by terminal/session identity when appropriate.

## Compact-Event Resilience Policy

Compaction is treated as a normal failure mode, not an edge case.

### Required Behavior

1. Work must be resumable from transcript plus persisted artifacts.
2. Resumption must begin with context reconstruction, not optimistic continuation.
3. Handoff or restore artifacts must be validated before use.
4. If contract-required state is absent, stop and reconstruct via `/recap`, `/gto`, or direct source reads.

### Forbidden Behavior

- assuming the restore payload is complete
- implementing from summary prose when contract state is missing
- marking work complete when interruption may have skipped a required gate

## Phase Ownership

| Concern | Owning Skill |
|---|---|
| Resume reconstruction | `/recap` |
| Gap discovery | `/gto` |
| Problem ranking | `/top-problems` |
| Architecture and state contracts | `/arch` |
| Plan artifact and blockers | `/planning` |
| Failure prediction | `/pre-mortem` |
| Implementation and TDD | `/code` |
| Adversarial review | `/critique` |
| Feature verification | `/verify` |
| System certification | `/sqa` |

Do not let one skill silently absorb another skill's ownership.

## Delegation and Suggestion Policy

Top-level skills are expected to route to lower-level skills when appropriate.

### Rule

- Top-level skills orchestrate.
- Lower-level skills specialize.
- A top-level skill must not silently absorb a lower-level skill's core responsibility.

### Auto-Invoke vs Suggest

Use **auto-invoke** when:

- the lower skill is a hard gate for correctness
- the parent skill cannot complete truthfully without the child skill's output
- ownership is already explicitly defined for the child skill

Use **suggest only** when:

- the lower skill is exploratory, optional, or prioritization-oriented
- the user may reasonably choose among multiple next steps
- invoking the lower skill would blur phase ownership

### Examples

| Parent Skill | Child Skill | Mode | Reason |
|---|---|---|---|
| `/planning` | `/arch` | auto-invoke | Architecture blockers are a hard gate |
| `/code` | `/arch` or `/planning` | suggest or stop-and-route | `/code` must not invent architecture/plan contracts |
| `/verify` | `/arch` | suggest/fail route | Verification reports failure; architecture owns redesign |
| `/verify` | `/planning` | suggest/fail route | Planning owns plan artifact and contract matrix |
| `/gto` | `/arch`, `/planning`, `/verify`, `/critique`, `/pre-mortem` | suggest | Gap analysis routes to owners |
| `/top-problems` | `/arch`, `/planning`, `/pre-mortem`, `/critique`, `/verify` | suggest | Prioritization must not execute fixes |
| `/recap` | `/gto`, `/arch`, `/verify` | suggest | Resume context may reveal missing gates |
| `/sqa` | layer owner skill | suggest/fail route | SQA certifies; it does not rewrite architecture or plans |

### Ownership Guard

If a top-level skill routes to a lower skill:

1. name the owning skill explicitly
2. state whether the route is mandatory or advisory
3. do not rewrite the child skill's deliverable unless the policy explicitly assigns that ownership

## Required Deliverables by Phase

| Phase | Required Deliverable |
|---|---|
| `/recap` | transcript-derived summary of what actually happened |
| `/gto` | current gap artifact and health view |
| `/top-problems` | ranked problem list when multiple candidates exist |
| `/arch` | decision packet with closed contracts |
| `/planning` | implementation-ready plan artifact |
| `/pre-mortem` | risk list with warning signs and remaining items |
| `/code` | TDD evidence and traceable implementation proof |
| `/critique` | adversarial findings and recommended next steps |
| `/verify` | 4-tier verification evidence |
| `/sqa` | layered system quality report |

## Long-Term Optimization Rules

When choosing between local speed and long-term system health:

1. prefer transcript truth over narrative memory
2. prefer contract closure over flexible ambiguity
3. prefer freshness checks over cached confidence
4. prefer root-cause ranking over symptom-first repair
5. prefer system certification over single-path success

## Anti-Forgetting Rule for Inputs and Outputs

When designing or implementing any component, explicitly name:

- inputs consumed
- outputs produced
- fields required by downstream consumers
- who verifies those fields
- what breaks if they are absent or stale

If those are not written down, the design is incomplete.

That rule applies to:

- function signatures
- hook payloads
- handoff envelopes
- plan artifacts
- evidence files
- session ledgers
- subagent result files
- skill outputs

## Decision Rule

If unsure which skill to run next:

1. `/recap` if context may be incomplete
2. `/gto` if current gaps are unclear
3. `/top-problems` if prioritization is unclear
4. `/arch` if contracts/state are unclear
5. `/planning` if execution shape is unclear
6. `/pre-mortem` if risk is unclear
7. `/code` only when the above are sufficiently closed
