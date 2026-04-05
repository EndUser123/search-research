---
name: planning
description: Build and verify implementation plans with strict readiness gating. Produces separate artifacts: plan, review results, and findings. A plan cannot be marked implementation-ready while containing placeholders, unresolved blockers, raw review output, implied producer/consumer contracts, or missing required Contract Authority Packet consumption.
category: planning
enforcement: advisory
depends_on:
  - sdlc: ">=0.1.0"
triggers:
  - /planning
  - /planning-v2
  - "create a plan for"
  - "break this down"
  - "how do I implement"
  - "plan the implementation"
  - "steps to build"
  - "task decomposition"
aliases:
  - /planning
  - /planning-v2
metadata:
  version: "5.5.0"
  compatibility: "claude-code"
  status: "accepted"

workflow_steps:
  - detect_topic: Infer topic from conversation history when not explicitly provided
  - draft_plan: Generate initial plan draft (NOT placeholder normalization — concrete content only)
  - verify: Run auto_verify.py for deterministic checks (sections, placeholders, contradictions)
  - contract_boundary_check: Reject plans with implied producer/consumer boundaries, missing artifact schemas, missing required Contract Authority Packet consumption, or missing freshness/invalidation rules
  - remediate_blockers: Route architecture blockers to /arch for decision closure; planning keeps sole ownership of plan edits
  - auto_fix: Apply only non-semantic repairs (header normalization, metadata, and optional ordering when explicitly requested)
  - adversarial_review: Dispatch 6 adversarial subagents via Agent tool in parallel
  - synthesize: Rewrite plan incorporating accepted findings; remove stale steps; rerun verification
  - recommended_next_steps: When the plan is blocked, routed, or below implementation-ready, emit numbered Recommended Next Steps with owner, why, apply, proof, and `0 = apply all`
  - present_results: Show status header, verification result, and path to plan artifact only
  - cleanup_artifacts: |
      After adversarial_review completes, call cleanup_plan_artifacts() from __lib/auto_verify.py.
      Removes *.review.findings.json, *.review.summary.md, *.review.result.json files
      older than 7 days (604800s). Concurrent-session safe (atomic unlink).
      Run: python -c "from pathlib import Path,sys;sys.path.insert(0,str(Path('P:/.claude/skills/planning/__lib')));from auto_verify import cleanup_plan_artifacts;print(cleanup_plan_artifacts())"

hooks: {}

suggest:
  - /search (context discovery for planning)
  - /r
  - /p --phase=4
---

# Plan Workflow v2

## Purpose

Create and verify implementation plans with strict readiness gating. A plan cannot be marked `implementation-ready` while it contains placeholders, unresolved blocker findings, raw review output, implied producer/consumer contracts, or missing required Contract Authority Packet consumption.

## Orchestration Model

```
Claude assembles draft -> Claude calls auto_verify.py -> if architecture blockers exist, Claude invokes /arch
-> Claude rewrites the plan -> Claude dispatches adversarial agents
-> Claude synthesizes changes -> Claude presents results (plan path + status only)
```

**Claude's responsibilities:**
- Generate initial draft with concrete content (no placeholder scaffolding)
- Call verification scripts when needed
- Invoke `/arch` automatically when verification reports architecture-class blockers
- Rewrite the plan itself after consuming `/arch` decisions; `/arch` must not directly edit the plan
- Dispatch adversarial subagents via Task tool in a single message
- Synthesize accepted findings into a rewritten plan
- Present only the plan path and status -- NOT raw findings

**Tool responsibilities:**
- `auto_verify.py`: Placeholder detection, contradiction checks, disposition checks, plan-purity checks
- `auto_fix.py`: Non-semantic repairs only (header normalization, frontmatter metadata updates, and section ordering only when explicitly requested)
- Custom subagents: Adversarial agents defined in `.claude/agents/`

**Remediation boundary:**
- `/arch` owns architecture decision closure
- `/planning` owns the plan artifact and all plan rewrites
- `auto_verify.py` decides when the blocker set requires `/arch`

**Authoritative precedence:**
- The latest `auto_verify.py` result is authoritative for current blocker state
- The latest `Contract Authority Packet` from `/arch` is authoritative for closed boundary semantics on contract-sensitive work
- Current workspace files are authoritative over notes embedded in the plan
- Older review notes, “false positive” commentary, or stale summaries are non-authoritative once verification has been rerun

Readiness is computed, not asserted by prose. If frontmatter, review artifacts, the contract matrix, or the active packet disagree, the validator result wins and the plan must be downgraded until rewritten.

If `next_action.type` is `invoke_arch_then_rewrite_plan`, `/planning` must not debate whether those architecture blockers are “real enough.” It must invoke `/arch` with the listed blocker IDs and rewrite the plan from the returned decision packet.

If `/arch` emits a `Contract Authority Packet`, `/planning` must consume it as authoritative for boundary semantics. The plan may restate or organize those semantics, but it must not weaken, replace, or contradict them.

For stateful/history/provider/multi-terminal plans, `/planning` must reject drafts that leave identity, ordering, dedupe, invalidation, event-source, or isolation-boundary decisions ambiguous. It must also reject plans whose tests contradict those contracts or whose freshness/replay/invalidation mechanics cannot actually fire under the stated invariants. Those are readiness gates, not polish issues.

For plans with hooks, handoff envelopes, restore artifacts, ledgers, evidence files, subagent outputs, or any other producer/consumer boundary, `/planning` must also reject drafts that leave these ambiguous:

- producer
- consumer
- input schema
- output schema
- required fields
- freshness authority
- invalidation trigger
- failure behavior
- contract-to-test mapping
- contract authority source when `/arch` marked the boundary contract-sensitive

Those are readiness gates, not polish issues.

## Routing Behavior

`/planning` auto-invokes `/arch` for architecture-class blockers because that is a hard gate.

`/planning` may suggest:

- `/pre-mortem` when the plan is risky, stateful, or hard to reverse
- `/code` only when the plan is actually implementation-ready and any required `Contract Authority Packet` has been consumed

`/planning` owns the plan artifact and must not offload plan writing to downstream skills.

When routing or remediation is required, `/planning` must emit a numbered `✅ RECOMMENDED NEXT STEPS` section instead of leaving the user with a generic "go use `/arch`" handoff. The section must name the owning skill, the reason, the exact apply action, the proof action, and a `0` option for applying the full set in dependency order.

## Quick Start

```
/planning "implement X"
```

Claude will:
1. Generate a concrete plan draft (no placeholder content)
2. Run deterministic verification
3. If architecture blockers are found, invoke `/arch`, then rewrite the plan and re-verify
4. Launch adversarial review agents automatically
5. Synthesize findings into a rewritten plan
6. Present the plan path and status

If the final result is still blocked, routed, or below `implementation-ready`, `/planning` must also present numbered Recommended Next Steps so the user can choose `1`, `2`, etc., or `0` to apply all.

## Commands

| Command | What It Does |
|---------|--------------|
| `/planning "do X"` | Create draft, run verification, adversarial review, synthesize, present results |
| `/planning <path>` | Create plan from ADR/topic, run full workflow |
| `/planning build "do X"` | Create draft only, skip verification (manual control) |
| `/planning review` | Re-verify existing plan (path inferred from context) |
| `/planning review <path>` | Re-verify specific plan |

## Context-Aware Behavior (When No Topic Provided)

When invoked without a topic argument (e.g., just `/planning`):

1. **Read pre-injected conversational context** -- The `[CONVERSATIONAL CONTEXT]` block at the top of the prompt (injected by the UserPromptSubmit hook) provides detected skills and topics from prior conversation.
2. **Check for existing plans related to inferred topic** -- if a plan exists that matches the detected context, use it
3. **If exactly one candidate** -- use it automatically
4. **If multiple candidates OR no conversational context** -- ask user to specify
5. **Resume from appropriate phase**:
   - If plan exists and `draft` -> continue from verification
   - If plan exists and `in-review` -> continue from adversarial review
   - If plan exists and `implementation-ready` -> offer to proceed to implementation

**Context inference (for /planning without arguments):**
- Context is pre-injected by the UserPromptSubmit hook via `[CONVERSATIONAL CONTEXT]` block
- Detected skills and topics come from the hook's transcript analysis
- The hook computes context before skill execution, so no direct transcript reading needed

## ADR-Aware Behavior

When invoked with an **ADR file path** (e.g., `/planning path/to/ADR-002-chs-consolidation.md`):

1. **Detect ADR format** -- filename patterns: `ADR-XXX`, `XXX-title`, `arch_decisions/` directory
2. **Generate draft** -- extract content into canonical plan format, but mark as `draft` until concrete tasks replace scaffolding
3. **Create separate plan file** -- `~/.claude/plans/plan-adr-XXX-title.md`
4. **DO NOT merge findings into the plan artifact**

## Verification Workflow (Steps 1-3)

Steps 1-3 cover draft generation, auto_verify checks, and auto_fix scope.

**Step 1**: Generate a concrete draft with actual content, NOT placeholder scaffolding.
**Step 2**: Run `auto_verify.py` for deterministic checks (placeholders, contradictions, dispositions, plan-purity, and state-model contract closure for applicable plans).
**Step 2.5**: Run contract boundary check for producer/consumer artifacts and handoffs.
**Step 3**: Run `auto_fix.py` for non-semantic repairs only (headers, metadata, and ordering only when explicitly requested).

See `references/verification-workflow.md` for full details on each check and what auto_fix does/does not do.

`auto_verify.py` also treats stale sibling review artifacts as non-authoritative. If an existing `.review.summary.md` contradicts the latest verification result, `/planning` must treat it as stale and regenerate it rather than debating which artifact is true.

## Blocker Remediation Loop

When `auto_verify.py` returns architecture-class blockers, `/planning` must:
1. Extract the blocking findings and relevant plan excerpts
2. Invoke `/arch` automatically to close the architecture decisions
3. Require `/arch` to return a decision packet, not plan edits
4. Rewrite the plan itself using that decision packet
5. Remove any now-resolved open questions
6. Re-run `auto_verify.py`

**Architecture-class blockers that should route to `/arch`:**
- `contract_ambiguity`
- `state_model`
- `schema_consistency`
- `identity_boundary`
- `contract_test_coherence`
- `mechanism_triggerability`
- state-model `open_questions` findings that leave source-of-truth, ordering, dedupe, invalidation, or event-source decisions unresolved
- `boundary_contract_ambiguity`
- `artifact_schema_gap`
- `consumer_validation_gap`

**Do NOT invoke `/arch` for:**
- placeholders
- missing sections
- malformed frontmatter
- RTM/acceptance-criteria gaps
- raw review output merged into the plan

**Execution rules for simpler LLMs:**
- Always rerun `auto_verify.py` before reasoning about blocker state
- Treat `next_action` as the workflow controller, not as advisory commentary
- If the plan or sibling artifacts changed since the last verification run, discard the previous blocker model and rerun verification
- When both architecture blockers and artifact/status blockers exist, resolve the architecture blockers first, then rerun verification, then clean up the remaining artifact/status blockers
- Do not create workaround notes arguing a verifier finding is a false positive; either satisfy the contract or escalate to `/arch`

## Adversarial Review (Step 4)

### Step 4a: Pre-create per-plan findings directory with terminal isolation

```bash
# Create per-plan adversarial subdirectory: P:/.claude/plans/adversarial/{sanitized_plan_name}/{terminal_id}/
# Terminal ID ensures findings from different terminals don't collide
# Workflow stage file records current step so compaction resumes correctly
python -c "
import os, re, sys, json
from pathlib import Path

# Auto-detect terminal_id using same logic as hook_ledger.py
def _detect_terminal_id():
    wt = os.environ.get('WT_SESSION', '')
    if wt:
        return f'console_{wt}'
    return 'unknown'

plan_path = sys.argv[1]
terminal_id = _detect_terminal_id()
name = os.path.splitext(os.path.basename(plan_path))[0]
safe = re.sub(r'[^A-Za-z0-9_.-]', '_', name)
base = Path(f'P:/.claude/plans/adversarial/{safe}/{terminal_id}')
base.mkdir(parents=True, exist_ok=True)
# Write workflow stage checkpoint
stage_file = base / 'workflow_stage.json'
stage_file.write_text(json.dumps({'stage': 'step_4a', 'plan_path': plan_path, 'terminal_id': terminal_id}))
print(str(base))
" '${PLAN_PATH}'
```

### Step 4b: Dispatch adversarial agents in TWO phases

**CRITICAL**: Use the prompts from `references/adversarial-agent-prompts.md` VERBATIM. Do not paraphrase or modify the prompts — the idempotency checks, file paths, and field names are all specified in the reference and must match exactly for the retry protocol to work.

**Phase 1 — Parallel dispatch (6 agents)**:
Dispatch all 6 non-critic agents in ONE message using the Agent tool:

Each agent writes findings to file and returns ONLY the path. Each agent checks: if output file exists, skip and return path immediately.

The 6 parallel agents are: adversarial-compliance, adversarial-logic, adversarial-testing, adversarial-quality, adversarial-performance, adversarial-security.

**IMPORTANT — File naming**: The reference prompts write to `{agent}-findings.json` (e.g., `compliance-findings.json`, `logic-findings.json`). Do NOT use `adversarial-{agent}.json` naming.

**After Phase 1 completes**: Record stage checkpoint:
```python
# Write stage file: adversarial-findings-complete
base / 'workflow_stage.json' → {"stage": "step_4b_phase1_done", "agents": [...]}
```

**Phase 2 — Series dispatch (critic agent)**:
After Phase 1 agents complete and their findings are available, dispatch the critic agent using the prompt from `references/adversarial-agent-prompts.md`.

The critic's role is to evaluate the consensus from the 6 parallel agents. Running the critic in series (after the others) allows it to review all findings and identify blind spots, consensus gaps, and contradictions.

**After critic completes**: Record stage checkpoint:
```python
base / 'workflow_stage.json' → {"stage": "step_4b_critic_done"}
```

**Stage checkpoint on compaction**: If session compacts during dispatch, read `workflow_stage.json` to determine where to resume:
- `step_4a`: re-run step 4a, then dispatch agents
- `step_4b_phase1_done`: re-run Phase 1 (idempotency ensures completed agents skip)
- `step_4b_critic_done`: skip to synthesize

### Step 4c: Synthesize

After collecting findings, Claude must:
1. Read all findings files
2. Produce a consolidated change list -- NOT content to paste into the plan
3. Rewrite the plan incorporating accepted findings
4. Remove stale steps flagged by reviewers
5. Rerun auto_verify to confirm `implementation-ready` or identify remaining blockers
6. Write findings to `*.review.findings.json`
7. Write summary to `*.review.summary.md`

See `references/artifact-contract.md` for disposition table format required in `*.review.summary.md`.

## Step 5: Present Results

If the plan is `implementation-ready`, present ONLY:
- Plan artifact path
- Status: `draft` | `in-review` | `implementation-ready`
- Unresolved blocker count
- Summary of changes made (not raw findings)

```
plan: C:\Users\brsth\.claude\plans\plan-name.md
status: implementation-ready
unresolved_blockers: 0

Changes incorporated: 4 findings accepted, 2 rejected with rationale, 1 deferred to follow-up.
```

If the plan is blocked, routed to `/arch`, or otherwise below `implementation-ready`, present the same summary plus:

```md
## ✅ RECOMMENDED NEXT STEPS

1 (/arch|/planning|/code|/verify) - Short action title
  Owner: `/arch` | `/planning` | `/code` | `/verify`
  Why: Concrete reason this step is needed.
  Apply: Exact change or command to perform.
  Proof: Exact validation that confirms the step worked.

2 (...) - ...

0 - Apply ALL Recommended Next Steps
```

Example:

```md
plan: C:\Users\brsth\.claude\plans\plan-name.md
status: in-review
unresolved_blockers: 3

## ✅ RECOMMENDED NEXT STEPS

1 (/arch) - Close stale CAP semantics for `plan-artifact`
  Owner: `/arch`
  Why: The active packet drifts from current `/planning` readiness semantics.
  Apply: Reinvoke `/arch` to revise the `plan-artifact` boundary and return an updated Contract Authority Packet.
  Proof: Re-run `/planning review` and confirm packet alignment is `Exact match to CAP`.

2 (/planning) - Repair matrix schema
  Owner: `/planning`
  Why: Required contract-boundary fields are missing from the plan artifact.
  Apply: Add per-row `Contract authority packet` and `Test binding` entries to the matrix.
  Proof: `auto_verify.py` returns no matrix-schema findings.

3 (/planning) - Downgrade invalid readiness claim
  Owner: `/planning`
  Why: The plan cannot remain `implementation-ready` while blockers remain unresolved.
  Apply: Rewrite status/frontmatter to the validator-supported readiness level.
  Proof: `verify_status = READY` and `claimed_status` matches the validator result.

0 - Apply ALL Recommended Next Steps
```

## Status Lifecycle

```
draft -> in-review -> implementation-ready
                   \-> (if blockers found) -> draft (with updated blocker count)
```

| Status | Meaning | Can advance to |
|--------|---------|----------------|
| `draft` | Contains placeholders or missing content | `in-review` |
| `in-review` | Under adversarial review | `implementation-ready` or back to `draft` |
| `implementation-ready` | Concrete content, all blockers resolved or deferred | -- |

A plan cannot be marked `implementation-ready` while:
- Any placeholder text remains
- Any blocker/high finding is unresolved
- Raw adversarial findings are merged into the plan
- Any required contract boundary matrix entry is missing
- Contract-sensitive work lacks a required `Contract Authority Packet` reference
- Any producer/consumer boundary relies on implied fields or unstated freshness rules
- Any plan statement contradicts the active `Contract Authority Packet`
- Phase-precondition metadata is used without recognized readiness vocabulary

Optional frontmatter for phased rollout planning:
- `phase_ready_through: <integer>` — only valid when the plan intentionally models phased rollout readiness
- `next_phase_blockers: <count or ids>` — explanatory only until validator support confirms the shape

Unrecognized ad hoc readiness fields do not weaken the blocking rules above.

## Required Plan Sections (v2 Shape)

Each implementation change must specify:
- **Goal**: What this change aims to achieve
- **Current state with evidence**: Concrete description with file/symbol references
- **Design decisions and invariants**: Named decisions with rationale; explicit concurrency/lifecycle/containment for stateful work
- **Implementation changes**: Per-change scope -- touched files/components, ordering/dependencies, failure handling, cleanup/lifecycle, acceptance checks. Use `**TASK-###**`, `**CHANGE-###**`, or heading-style `### TASK-###:` / `### CHANGE-###:` blocks.
- **Test matrix**: What tests cover this change and how they are run
- **Contract authority reference**: Required for contract-sensitive work; cite the active `Contract Authority Packet` version/path or explicitly state `not contract-sensitive`
- **Contract boundary matrix**: Each producer/consumer boundary with schema, required fields, freshness/invalidation, and consumer validation. Structural plans that do not change boundaries may explicitly mark this section `Not applicable`.
- **Assumptions/defaults**: What is assumed to be true; what defaults apply if unspecified
- **Open questions**: What is unknown that could affect the plan

### Contract Boundary Matrix (Required for Artifact or Handoff Work)

If the plan includes hooks, handoff envelopes, restore artifacts, ledgers, evidence files, subagent outputs, or any cross-phase file/payload, the plan must include a contract boundary matrix.

If `/arch` produced a `Contract Authority Packet` for those boundaries, the matrix must derive from that packet rather than planner inference.

Minimum fields:

| Field | Requirement |
|-------|-------------|
| Boundary | Name the exact handoff or artifact |
| Contract authority packet | Cite the packet id/version/path when required |
| Producer | Name the writer/emitter |
| Consumer | Name the reader/restorer/router |
| Input schema | Preconditions before production |
| Output schema | Fields/types delivered to consumer |
| Required fields | Mandatory fields only |
| Freshness authority | Which source is authoritative |
| Invalidation trigger | What makes this stale |
| Failure behavior | Stop, retry, reconstruct, or reject |
| Packet alignment | State whether the row matches the packet exactly or explain why `/arch` must be reinvoked |
| Test binding | Which test/trace proves the contract |

Plans that say "consumer will use this" without naming the expected fields are not implementation-ready.
Plans that omit a required `Contract Authority Packet` reference or drift from packet semantics are not implementation-ready.
Plans that hand-author stale boundary semantics copied from an older packet are not implementation-ready; `/arch` must be reinvoked when the active packet drifts from the current skill contract.

## Recommended Next Steps (RNS)

When `/planning` ends with blockers, routing, or non-ready status, it must emit a numbered RNS section.

Rules:

- Number every actionable step.
- Every item must include `Owner`, `Why`, `Apply`, and `Proof`.
- Use `/arch` as the owner for CAP drift, state-model closure, identity/ordering/dedupe/invalidation gaps, and stale boundary semantics.
- Use `/planning` as the owner for plan rewrites, status corrections, matrix completion, and disposition cleanup.
- Use `/code` or `/verify` only when the plan is already ready enough for those skills to act without first routing back through `/planning` or `/arch`.
- `0` means "apply the entire recommended set in dependency order."
- If an action depends on a prior one, order it later rather than hiding the dependency in prose.
- Do not emit freeform prose recommendations when RNS is required.

### Additional Required Contracts For Stateful / History / Provider / Multi-Terminal Plans

If the plan touches persistence, retention, ingest, providers, transcripts, event logs, replay, multi-terminal state, or stale-data immunity, it must also make these decisions explicit in the plan body:
- **Identity model**: `provider_id`, `source_id`, `conversation_id`, `session_id`, `terminal_id`, `turn_id`, and `provider_instance_id` if no real terminal exists
- **Ordering contract**: one mandatory ordering/watermark rule only
- **Dedupe contract**: exact event identity semantics and matching schema constraints
- **Freshness / invalidation contract**: authority of truth, invalidation trigger, replay trigger, stale-row behavior
- **Event source of truth**: authoritative source for task/opportunity projections
- **Isolation boundary**: terminal-private vs workspace-shared state boundaries
- **Contract-to-test alignment**: acceptance scenarios that assert the same behavior as the named contracts
- **Triggerability**: reachable trigger conditions for freshness, replay, invalidation, dedupe fallback, and lock recovery mechanisms

Plans missing any of those for applicable topics remain `draft`.

## Constraint Classification (Required)

Every plan must classify its constraints explicitly:

| Constraint | Type | Reason | Could This Be False? |
|------------|------|--------|---------------------|
| {boundary} | hard/soft/assumed | {why it exists} | {evidence or "no"} |

- **Hard**: Physics, platform limits, API contracts. These don't bend.
- **Soft**: Design decisions, tech debt, time pressure. Negotiable with effort.
- **Assumed**: "We've always done it this way." Must be questioned.

**Rule**: Plans with 3+ assumed constraints flagged as hard → flag for review. Assumptions treated as facts cause plan failures.

## Bias Detection Check (Before Synthesis)

Before synthesizing the final plan, check for cognitive biases:

| Bias | Detection Signal | Mitigation |
|------|-----------------|------------|
| **Anchoring** | First approach is the only approach considered | Generate at least 2 alternatives |
| **Sunk Cost** | "We already started X, let's continue" | Evaluate from current state, not past investment |
| **Confirmation** | Only seeking evidence that supports the plan | Actively seek disconfirming evidence |
| **Complexity Bias** | Defaulting to the more sophisticated solution | Start with simplest viable approach |

If any bias is detected, flag in the plan: `"BIAS FLAG: {type} — {mitigation applied}"`.

## Step Confidence Scoring

Each plan step gets a confidence badge:

| Badge | Criteria | Implication |
|-------|----------|-------------|
| `[HIGH]` | Well-understood, existing patterns, clear acceptance criteria | Execute directly |
| `[MED]` | Some unknowns, depends on external state | Add checkpoint before proceeding |
| `[LOW]` | Research needed, unproven approach | Prototype or spike first |

Plans with any `[LOW]` steps in the critical path → status remains `draft` until those steps are validated.

## Artifact Contract

Plans, findings, and review summaries are stored as separate files. See `references/artifact-contract.md` for:
- v1 vs v2 differences table
- Artifact file types and their purposes
- Required plan artifact structure (status header, must-include/must-not-include)
- Disposition table format for review summaries

## File Locations

```
.claude/skills/planning/
├── SKILL.md                      # This file
├── __lib/
│   ├── auto_verify.py           # Placeholder/contradiction/disposition/purity checks
│   └── auto_fix.py              # Non-semantic-only repairs
├── references/
│   ├── adversarial-agent-prompts.md  # 6 agent prompts + retry protocol
│   ├── artifact-contract.md          # Artifact structure and v1/v2 differences
│   ├── verification-workflow.md      # Steps 1-3: draft, verify, fix
│   └── version-history.md            # Detailed changelog
└── tests/
    ├── test_auto_fix_v2.py     # Non-semantic-only tests
    ├── test_auto_verify_v2.py  # Placeholder + contradiction tests
    └── test_planning_integration_v2.py  # Strict readiness gate tests
```
