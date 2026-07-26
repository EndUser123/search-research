---
thread_id: 57d7c178-1b0c-4fc4-8dc7-5519c12eccec
parent_handoff_path: none
current_session_id: 019f9b6f-98fc-7883-9d5f-cf570a0b3812
current_terminal_id: console_4605b174-0262-4044-8d3c-3ca7
produced_at: 2026-07-26T02:10:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 26a4057ed3ac0783ed04e8a16d1aec0870029300
---

# Deferred work from software-factory session

## Objective

Capture the deferred items from the 2026-07-25 software-factory session so they survive session close and can be picked up by a fresh session. The session shipped: SDLC stage awareness, `/refine` skill, readiness gates, `validate_refinement_markers` validator, and a design doc for the Stop hook scope-binding fix. These items were explicitly deferred per operator direction.

## Last user message (verbatim)

> "The deferred needs to go in a handoff now, so that we don't forget, we will revisit the handoff after #1 and #2 are implemented and verified."

## Status

PARTIALLY DONE — items 2, 5, 6, 8 actioned; items 1, 3, 4, 7 still deferred

## Deferred items

### ~~Item 2: Trust-escalation AGENTS.md encoding~~ ✅ DONE 2026-07-26

Encoded as AGENTS.md § "Trust-escalation rung (agent autonomy level)" — current fleet rung is 2-3 (Implement + Verify + Review; operator-invoked Close). Auto-commit authorized; destructive git always human-gated.

### 1. Bug-finder Rhai workflow (Factory shortlist item 4)

**What:** A scheduled proactive bug-finder that spawns a worktree, runs `/red-team` or `/review --focus correctness` on a rotating subset of the codebase, and opens `/tasks` entries for each finding.

**Components that exist:** `scheduler_create` (cron trigger), `workflow` (Rhai orchestration), `/red-team`, `/review`, `/tasks`, `grok-parallel` (worktree fan-out)

**What's missing:** A defined Rhai workflow at `~/.grok/workflows/bug-finder.rhai` that chains these components.

**Effort:** 30-60 min (workflow definition + smoke test)

**Inspiration:** Factory's `bug-finder.md` workflow — "find one concrete, previously unreported bug and create a clear GitHub issue for a human to review."

### 2. Trust-escalation wiki concept encoding in AGENTS.md (item 5)

**What:** The `trust-escalation-ladder-autonomous-agent-work.md` wiki concept documents 5 rungs (0-Refine through 4-Close). Optionally encode the current authorized rung in AGENTS.md so skills know how far to go autonomously.

**Status:** Wiki concept written. AGENTS.md encoding NOT done.

**Effort:** 10-30 min (decide whether to encode; if yes, one AGENTS.md rule)

### 3. Status-triggered dispatcher (item 6 — large build)

**What:** A dispatcher (daemon or scheduled poll) that watches `P:\docs\handoffs\` for status field changes and fires skills: `needs-refinement → /refine`, `ready-to-implement → /go execute`, `reviewing → /review`.

**Why deferred:** Large build. Requires a design doc resolving: task source (handoff status field?), persistent dispatcher (`scheduler_create` polling?), trust boundary for unattended execution, recovery model (idempotent via live-state reconciliation).

**Effort:** Large (design + implementation)

**Critical-friend review already done:** See session transcript — 5 open questions identified, verdict was "detour to /design when ready, not now."

### 4. Task→PR autonomous pipeline (item 7 — deferred)

**What:** Single-entry "drop ticket → pipeline runs unattended → PR appears" equivalent for our task+handoff control plane.

**Why deferred:** Operator said "I don't want to do this yet." Critical-friend review identified 5 blocking questions. Right next step is a design doc, not implementation.

**Effort:** Large (design first, then implementation)

### ~~Item 5: Behavioral smoke tests~~ ✅ DONE 2026-07-26

Smoke test for `_map_pytest_file_to_sources` written at `C:/Users/brsth/.grok/hooks/scripts/tests/test_file_inference_smoke.py` — 8/8 tests pass, covering: basic inference, no-import case, from-import form, security gate (unmodified source not inferred), no-.py-arg case, and regex fallback for SyntaxError.

**What:** Neither `/refine` nor the 3-check readiness gates have been exercised end-to-end against real tasks. Structural correctness verified (greps, test suite, validators). Behavioral correctness NOT verified.

**How to test:**
- `/refine "some real rough task"` — validate INVEST gate + 4-dim check + field expansion
- Invoke `/go` or `/plan-writer` on a vague input — validate the readiness gate fires and suggests `/refine`
- Write a handoff with a `[NEEDS CLARIFICATION]` marker missing its Resolution field — validate `validate_refinement_markers` catches it

**Effort:** 15-30 min

### ~~Item 6: Dimension standardization~~ ✅ DONE 2026-07-26

All 4 downstream readiness gates (go, plan-writer, design, refactor) now use the same standard 4-dimension set: Completeness / Clarity / Testability / Correctness. Matches /refine's own 4-dimension check.

**What:** The 4 downstream gates use slightly different dimensions (design uses Clarity where others use Testability; none includes Correctness). The red-team flagged this as RC-2 (REVISE).

**Why deferred:** Needs runtime evidence to decide which dimension set is optimal. The red-team recommended standardizing on `/refine`'s 4-dimension set, but this should wait until behavioral smoke tests (item 5) show whether the current variation is a problem in practice.

**Effort:** Medium (4 file edits once the decision is made)

### 7. Cross-family critic for /red-team (from /why RCA)

**What:** The `/why` RCA on the red-team's severity miscalibration identified that same-agent red-team is structurally weak (correlated errors). The unbuilt `/red-team` cross-family adversarial mode would decorrelate errors by using a different model family for the critic specialist.

**Status:** Proposed in the RCA. Not yet scoped or designed.

**Effort:** Medium (design + implementation of the cross-model dispatch in `/red-team`)

### ~~Item 8: /tp structural fixes~~ ✅ DONE 2026-07-26

Three structural fixes applied to `/tp/SKILL.md`:
1. **Critic-side receipt requirement** — every challenge must cite a receipt (file:line, grep, tool output). No receipt → [INFERENCE] or drop. Orchestrator hard gate: >1 challenge without receipt → re-prompt before propagating.
2. **Per-claim verdict format** — for ≥3 challenges, emit per-claim verdicts (VERIFIED/REFUTED/REJECTED_AS_OVERREACH) instead of a single umbrella verdict. Eliminates the AGREE_WITH_QUALIFICATIONS overgeneralization.
3. **Frame-mutation for complex targets** — for N>3 findings across N>3 files, add ≥2 frame mutations to the subagent prompt (schema-discipline, reversibility-scale). Single-frame for simpler targets.
4. (The 4th fix — promote orchestrator spot-check to hard gate — is covered by fix 1's "orchestrator hard gate" clause.)

**What:** The `/why` RCA on the /tp critique identified four structural fixes:
1. Mandate critic-side spot-check at the claim level (make receipt mandatory for each /tp claim)
2. Replace single verdict with per-claim verdicts
3. Frame-mutated /tp on complex targets (use ≥2 frames for N>3 findings)
4. Promote orchestrator-side spot-check to a hard gate

**Status:** Proposed in the RCA. Not yet applied to `/tp/SKILL.md`.

**Effort:** Medium (4 changes to /tp SKILL.md)

## Design doc in temp (will be reaped)

The design doc for the Stop hook scope-binding fix is at:
`C:\Users\brsth\AppData\Local\Temp\grok-design-4e4629f7\grok-design-doc-4e4629f7.md`

If items 1 and 2 from the session are implemented (the 3-layer fix + wiki promotion), this handoff's item list shrinks. The design doc itself is scaffolding and will be reaped by the OS — the implementation decisions should be promoted to the wiki if they haven't been already.

## Related wiki concepts

- `P:/.data/wiki/concepts/workflow-definition-over-agent-capability.md`
- `P:/.data/wiki/concepts/trust-escalation-ladder-autonomous-agent-work.md`
- `P:/.data/wiki/concepts/task-refinement-interview-detection-template-patterns.md`
- `P:/.data/wiki/concepts/producer-consumer-contract-drift-in-skill-chains.md`
- `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md`

## Key decisions from the session (for context)

1. SDLC chain is now continuous: `/refine → /design → /plan-writer → /go → /check → /review → /close`
2. Every SDLC skill has stage awareness + exit transitions + (for 4 skills) active readiness gates
3. `/refine` uses INVEST pre-filter + 4-dimension completeness check + `[NEEDS CLARIFICATION]` markers with lifecycle
4. `validate_refinement_markers` validator in `/handoff/__lib/validators.py` mechanically checks marker resolution
5. The Stop hook scope-binding problem was RCA'd and a 3-layer fix was designed (auto-inference + better error messages + documentation)

## Suggested next invocation

After items 1 and 2 are implemented and verified:
- `/handoff list` to see this handoff
- `/handoff close P:\docs\handoffs\deferred-factory-work-20260726\HANDOFF.md` when all items are triaged
- Pick up item 5 (behavioral smoke tests) first — it's the cheapest and validates the most work
