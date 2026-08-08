# Semantic Skill Composition Graph: Corrected Design (v3)

**Created:** 2026-07-30
**Revised:** 2026-07-30 (v4 — transaction-integrity correction: per-node lifecycle, idempotency keys, A1/A2 phase split, proportional evaluation, refined branch statuses, staged readiness milestones)
**Author:** session 019fb0bd (Grok)
**Status:** Design + audit + bounded pilot specification
**Verification:** semantic-equivalence audit, runtime-duplication trace, and persistence-entry-point inspection performed this session

> **Why v3.1 exists:** v3.0's recipe had six structural defects: (1) "zero runtime
> duplication" was too strong; (2) atomic_write verdict was premature; (3) the DAG
> mixed workflow inputs with executable components; (4) it lacked a check-run
> discovery step; (5) branch actions were prose strings, not real components; (6)
> terminal semantics allowed completion without persistence receipts. v3.1 corrects
> all six. The persistence-entry-point inspection found that only 2 of 5 branch
> destinations have real programmatic entry points, blocking the "ready for
> implementation" verdict.

---

## 1. Executive verdict

**Final recommendation: `BUILD_COMPONENT_FOUNDATION_AND_MANUAL_RECIPE_PILOT`**

**Recipe verdict: `MANUAL_RECIPE_DESIGN_NEEDS_MORE_EVIDENCE`**

The overall direction is correct. The hierarchy, semantic-equivalence audit, separation of shared libraries / static recipes / dynamic planning, and two-loop improvement model all hold. But the recipe design is not yet ready for implementation because:

1. Three of five branch destinations (`persist-handoff-continuation`, `persist-opportunity-candidate`, `persist-causal-learning-candidate`) lack deterministic programmatic entry points. Handoff writing is LLM-prose-only; opportunity candidates and causal learning have no dedicated store. Phase A does not implement the missing domain writers. It designs and, in the isolated pilot phase, implements deferral adapters that persist actionable follow-up obligations through existing todo or harvest stores. The underlying handoff, opportunity and causal-learning entry points remain missing.
2. The atomic_write characterization needs caller verification before extraction.
3. The recipe must be tested against hermetic fixtures before touching production.

The next step is Phase A: recipe and caller characterization, including building the missing entry points for handoff, opportunity, and causal-learning persistence.

---

## 2. Corrected runtime-duplication terminology

**v3.0 said:** "zero runtime duplication in this route"

**Correction:** Some operations are repeated independently across skills, including inexpensive session-identity handling. No material redundant runtime work was demonstrated in the `/check → /close` route. Some repeated checks are intentional defense-in-depth and must remain separate. Runtime cost and semantic redundancy are different questions.

| Operation | Repeated across skills? | Material redundancy? | Assessment |
|-----------|----------------------|---------------------|------------|
| Session-identity handling | Yes (5 skills) | No — <1ms each, separate invocations | Inexpensive; independent by design |
| Transcript file access | Yes (6 skills access `chat_history.jsonl`) | Partially — `/aar` re-parses independently | Semantic overlap exists; runtime cost is context-dependent |
| Git state queries | Yes | No — different queries (diff vs status vs log) | Different purposes |
| Atomic file writes | Yes (11 skills) | No — writes to different paths | Same pattern, different targets |
| Output validation | Yes | No — different output formats | Independent checks must remain separate |

**Key correction:** "no material redundant runtime work" replaces "zero runtime duplication." The distinction matters because defense-in-depth checks (independent session validation, independent validators) are intentional, not waste to eliminate.

---

## 3. Tightened atomic-write verdict

**v3.0 said:** `IDENTICAL_AND_SHAREABLE`

**Correction:** `IDENTICAL_CORE_PATTERN — SHAREABILITY_PENDING_CALLER_CHARACTERIZATION`

The core pattern (tmp + os.replace, PID suffix, UTF-8) is identical across all observed implementations. Safe extraction still depends on caller semantics that have not been verified:

| Caller concern | Status |
|---------------|--------|
| Parent-directory assumptions | TO_VERIFY — does every caller ensure the parent dir exists? |
| JSON/text formatting | OBSERVED — some use `json.dumps(indent=2)`, some use `json.dumps()` |
| Encoding and newline behavior | TO_VERIFY — Windows newline handling in tmp files |
| Exception handling | TO_VERIFY — what happens when os.replace fails? |
| Cleanup of failed temporary files | TO_VERIFY — orphaned .tmp files on crash |
| Same-process concurrent writes | TO_VERIFY — PID suffix prevents collision but not same-PID |
| Same-path concurrent writes | TO_VERIFY — os.replace is atomic, but concurrent writers race |
| Destination filesystem assumptions | TO_VERIFY — NTFS vs FAT32 behavior |
| Permissions behavior | TO_VERIFY — does the tmp file inherit parent permissions? |
| Return values relied on by callers | TO_VERIFY — some callers check success, some don't |

**Extraction proceeds only if caller characterization finds no material differences.** If differences exist, compatibility wrappers are required.

**Atomic write remains a primitive, not a graph-visible component.** It does not participate in workflow composition.

---

## 4. Workflow inputs and policy model

### Removed from DAG: `accept-authoritative-session-id`

Session identity is a **workflow input**, not an executable component. It must not be "discovered" by scanning directories or selecting newest state.

```yaml
workflow_inputs:
  session_id:
    required: true
    authority: current-runtime-context
    inference_forbidden: true
    description: >
      The authoritative session ID obtained from the Grok system context
      (prompt file path, compaction segment paths). Must NOT be inferred
      from directory scanning, mtime heuristics, or foreign terminal state.
  check_run_id:
    required: false
    description: >
      Explicit check-run identifier when the operator or caller knows which
      run to process. When omitted, the discovery component enumerates all
      runs for the session.
```

### Policy constraints

```yaml
policy:
  - "No component may acquire authority by scanning directories"
  - "No component may select by newest-file or mtime heuristic"
  - "No component may read another terminal's session context"
  - "Ambiguous identity blocks or downgrades the route to advisory"
  - "Model-based classification must be persisted before any side effect"
```

The first executable component is `validate-session-binding`, which validates the supplied session_id against runtime artifacts (summary.json cross-validation, per the AAR SessionResolver pattern).

---

## 5. Check-run discovery contract

### New component: `locate-session-check-runs`

v3.0's recipe invoked `read-check-lifecycle(run_dir)` without any component producing `run_dir`. This gap is corrected:

```yaml
components:
  - id: locate-session-check-runs
    owner_skill: close
    kind: deterministic
    entry_point: "TBD — extract from close_accounting.py:scan_check_receipts rglob logic"
    
    inputs:
      - name: session_id
        required: true
        authority: workflow-input
      - name: check_run_id
        required: false
        description: "Explicit run to select when multiple exist"
    
    outputs:
      - name: runs
        type: list[dict]
        description: "All check-run.json manifests bound to this session"
      - name: selected_run
        type: dict | None
        description: "Single run when unambiguous; None when ambiguous or empty"
      - name: disposition
        enum: [SINGLE, MULTIPLE_REQUIRES_SELECTION, NONE_FOUND, AMBIGUOUS]
    
    artifact_consumes:
      - artifact_type: check-run-manifest
        binding: session_id
        required: false
    
    preconditions:
      - "session_id is authoritative (from workflow input, not inferred)"
    
    postconditions:
      SINGLE: "exactly one run found; selected_run is populated"
      MULTIPLE_REQUIRES_SELECTION: "multiple runs found; caller must select"
      NONE_FOUND: "no runs bound to this session"
      AMBIGUOUS: "runs found but cannot determine which to process"
    
    authority_domain: check
    binding_keys: [session_id]
    
    rules:
      - "Enumerates only check manifests explicitly bound to session_id"
      - "Never selects by newest-file or mtime"
      - "Accepts explicit check_run_id when supplied"
      - "Ignores foreign-session runs"
      - "Reports malformed manifests visibly (not silently skipped)"
      - "Returns AMBIGUOUS when multiple candidates require disposition"
```

### Pilot scope decision

The pilot operates on **one explicitly identified check run**. When multiple runs exist for a session, the recipe reports `MULTIPLE_REQUIRES_SELECTION` and stops. Processing every unresolved run is a future enhancement, not the initial pilot.

---

## 6. Real branch component contracts

### Persistence entry-point inventory (inspected this session)

| Branch destination | Entry point | Store | Status |
|-------------------|------------|-------|--------|
| `persist-todo-action` | `tasks/scripts/tasks.py:cmd_add` | `~/.claude/tasks/project-main-tasks/*.json` | **EXISTS** — CLI with locking, atomic write |
| `persist-harvest-obligation` | `harvest/scripts/store.py:write_event` | `P:/.data/harvest/events/*.json` | **EXISTS** — Python function with fsync + claim |
| `persist-handoff-continuation` | **NONE** | `P:/docs/handoffs/*/HANDOFF.md` | **MISSING** — handoffs are written by the LLM in prose; no programmatic writer exists |
| `persist-opportunity-candidate` | **NONE** | No dedicated store | **MISSING** — opportunities live in AAR reports or harvest events, not a separate store |
| `persist-causal-learning-candidate` | **NONE** | `/aar` and `/debrief` are full skills | **MISSING** — no component-level entry point; invoking the full skill defeats the purpose of component composition |
| `record-no-new-work-disposition` | N/A | Workflow artifact only | **EXISTS** — disposition record written to workflow outcome |

### Contracts for existing entry points

#### persist-todo-action

```yaml
- id: persist-todo-action
  owner_skill: tasks
  kind: deterministic
  entry_point: "tasks.scripts.tasks.cmd_add"  # CLI function — adapter required
  adapter_required: true
  adapter_reason: >
    cmd_add takes argparse.Namespace, not keyword arguments.
    An adapter must construct the namespace or extract the core write logic
    into a callable function. Do not assume the CLI function is directly
    reusable as a component entry point.
  
  inputs:
    - {name: subject, required: true}
    - {name: description, required: true}
    - {name: active_form, required: false}
    - {name: owner, required: false}
  
  outputs:
    - {name: task_id, type: str}           # parsed from "created T-N: <subject>" stdout
    - {name: task_path, type: str}         # STORE / f"{task_id}.json"
  
  authority_domain: tasks
  binding_keys: []                    # tasks are not session-bound
  idempotent: false                   # same subject creates duplicate (no dedup exists)
  concurrency_safe: true              # file locking via O_CREAT|O_EXCL on .lock sentinel
  retry_eligible: true
  failure_behavior: "lock contention → exit 2; stale lock → --force breaks after 300s"
  compensation: "tasks.py done <task_id>"
  persistent_store: "~/.claude/tasks/project-main-tasks/*.json"
  return_value_source: "stdout string 'created T-N: <subject>' — no structured return"
  
  duplicate_detection: "DESIGN/TBD — no duplicate detection exists in tasks.py; BY_SUBJECT is proposed, not implemented"
```

**Code-verified findings (this session):**
- `cmd_add` signature: `def cmd_add(args: argparse.Namespace) -> None`
- No return value — prints to stdout; caller must parse `"created T-N: <subject>"`
- Locking: `_try_lock()` via `O_CREAT|O_EXCL` on `.lock` sentinel; stale lock breakable with `--force`
- Atomic write: `_atomic_write_json(path, payload)` — tmp + os.replace
- Watermark: `_read_watermark()` → increment → `_write_watermark()`; race handled by existence check + retry
- **No duplicate detection**: the function creates a new task unconditionally
- **Optional `metadata` object field exists** in the task schema — idempotency key can go here without changing required fields

#### Todo adapter design (bounded extraction)

Stdout parsing is not a robust component contract. Design a bounded extraction:

```python
# In tasks/scripts/tasks.py — extract from cmd_add

def create_task(
    *,
    subject: str,
    description: str,
    active_form: str | None = None,
    owner: str | None = None,
    source_workflow_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Create a task with structured return and idempotency reconciliation.
    
    Retains existing locking and watermark logic.
    cmd_add() calls this function and preserves current CLI behavior.
    
    Idempotency: if idempotency_key is provided, search active tasks for
    a matching key in metadata before creating. If found, return existing.
    """
    # ... existing lock + watermark + atomic write logic ...
    # payload["metadata"] = {"source_workflow_id": ..., "idempotency_key": ...}
    # return payload  # structured dict, not stdout
```

**`cmd_add()` remains as a compatibility wrapper** calling `create_task()` and printing the result.

Required properties:
- Structured return (dict, not stdout)
- Existing locking retained
- Existing task ID allocation retained
- Backward-compatible CLI
- Idempotency reconciliation via metadata.idempotency_key
- Characterization tests before refactoring
- Rollback path

**If modifying tasks internals is outside the pilot authorization boundary**, mark the todo adapter as unresolved rather than pretending stdout parsing is a robust contract.

**Idempotency recovery scenario:**
```
side effect persisted (task written)
→ process crashes before branch receipt
→ recovery searches active tasks for matching idempotency_key
→ finds existing task
→ records receipt from existing task
→ does not create duplicate
```

#### persist-harvest-obligation

```yaml
- id: persist-harvest-obligation
  owner_skill: harvest
  kind: deterministic
  entry_point: "harvest.scripts.store.write_event"
  adapter_required: false              # clean Python function, directly callable
  
  inputs:
    - {name: event, required: true, enum: [ADD]}
    - {name: item_id, required: true}
    - {name: parent_event_id, type: str | None, required: false}
    - {name: title, required: true}          # passed via **fields
    - {name: obligation, required: true}     # passed via **fields
    - {name: operation, required: true}      # passed via **fields (GENERALIZE, FIX, INVESTIGATE)
    - {name: source, required: true}         # passed via **fields
    - {name: recoverable_value, type: float, required: false}  # via **fields
  
  outputs:
    - {name: event_id, type: str}            # record["event_id"] — ULID
    - {name: event_path, type: str}          # EVENTS / f"{event_id}.json"
  
  authority_domain: harvest
  binding_keys: []                    # harvest events are globally scoped
  idempotent: false                   # ULID prevents file collision but not semantic duplicate
  concurrency_safe: true              # fsync + atomic publish (os.replace) + claim
  retry_eligible: true
  failure_behavior: "ULID collision → retry (up to 8 attempts in-loop); disk full → RuntimeError/OSError"
  compensation: "harvest store resolve/drop <event_id>"
  persistent_store: "P:/.data/harvest/events/*.json"
  return_value_source: "dict record with event_id, item_id, claimed fields"
  
  duplicate_detection: "DESIGN/TBD — no duplicate detection exists in write_event; BY_TITLE_AND_SOURCE is proposed, not implemented"
```

**Code-verified findings (this session):**
- `write_event` signature: `def write_event(event, item_id, parent_event_id, **fields) -> dict`
- Returns a dict record directly — no stdout parsing needed
- Publish-before-claim protocol: event written + fsync'd + os.replace'd before claim attempted
- ULID generation with 8-attempt collision retry
- **No duplicate detection**: `write_event` creates a new event unconditionally; `item_id` is caller-supplied and not checked for existing open items

#### Harvest reconciliation semantics

Harvest's publish-before-claim protocol creates a subtlety: an event may be durably written even if the claim is lost. The adapter must distinguish:

| Scenario | Branch status | Meaning |
|----------|--------------|---------|
| Event written + claim acquired | `PERSISTED` | Event is durable and authoritative |
| Event written + claim lost (valid conflict sibling) | `PERSISTED_WITH_CONFLICT` | Event is durable but not authoritative; may require reconciliation |
| Event written + claim not attempted (crash before claim) | `PERSISTED_UNCLAIMED` | Event is durable; claim state unknown; recovery must attempt claim or inspect |
| No durable event | `FAILED` | Nothing persisted |

**Idempotency-key contract for harvest:**

```
idempotency_key = hash(workflow_id + accepted_classification_version + "harvest" + normalized_payload)
```

- Include `idempotency_key` and `source_workflow_id` in event fields (via `**fields`)
- Before writing, reconcile existing events: search for an event with the same `idempotency_key`
- If found: return its receipt (do not create duplicate)
- If not found: write new event with the key
- After write, distinguish claim outcome per the table above

**Recovery scenario:**
```
harvest event written + fsync'd + os.replace'd
→ process crashes before claim attempted
→ recovery searches events for matching idempotency_key
→ finds durable event (PERSISTED_UNCLAIMED)
→ attempts claim or records conflict status
→ records receipt
→ does not create duplicate
```

### Idempotency-key contract (all side-effecting branches)

```
idempotency_key = hash(workflow_id + accepted_classification_version + destination + normalized_payload)
```

| Store | How key is recorded | How key is reconciled |
|-------|-------------------|----------------------|
| Tasks | `metadata.idempotency_key` in task JSON | Search active tasks for matching key before creating |
| Harvest | `idempotency_key` field in event JSON | Search events for matching key before writing |
| Deferral (via todo) | Same as tasks | Same as tasks |
| Deferral (via harvest) | Same as harvest | Same as harvest |

**Do not claim crash-safe retry until this path is mechanically proven against hermetic fixtures.**

### Contracts for missing entry points (designs, not implementations)

These three destinations need entry points before the recipe can claim readiness:

#### persist-handoff-continuation (DESIGN — needs implementation)

```yaml
- id: persist-handoff-continuation
  owner_skill: handoff
  kind: hybrid                       # requires LLM to generate handoff content
  entry_point: "TBD — no programmatic writer exists"
  
  inputs:
    - {name: session_id, required: true}
    - {name: topic, required: true}
    - {name: status, required: true, default: "open"}
    - {name: continuation_context, required: true}
  
  outputs:
    - {name: handoff_path, type: str}
  
  authority_domain: lifecycle
  binding_keys: [session_id]
  idempotent: false
  concurrency_safe: true              # atomic write to unique path
  retry_eligible: false               # LLM content generation is not safely retryable
  
  problem: >
    The handoff skill has NO programmatic writer. Handoffs are written by the
    LLM following SKILL.md instructions. A deterministic component cannot
    generate handoff content. This destination requires either: (a) a model-based
    component that generates and validates structured handoff content, or
    (b) deferral to the LLM with a structured receipt after the LLM writes the file.
```

#### persist-opportunity-candidate (DESIGN — needs store)

```yaml
- id: persist-opportunity-candidate
  owner_skill: aar                    # or new
  kind: deterministic
  entry_point: "TBD — no dedicated opportunity store exists"
  
  problem: >
    Opportunities currently live inside AAR reports (prose) or as harvest events
    (obligation-flavored). There is no dedicated opportunity-candidate store.
    This requires either: (a) reusing the harvest store with operation=INVESTIGATE,
    or (b) creating a lightweight opportunity registry. Option (a) is preferred
    (no new store). If harvest store is used, this component is a thin adapter
    over persist-harvest-obligation with a different operation field.
```

#### persist-causal-learning-candidate (DESIGN — needs component-level entry)

```yaml
- id: persist-causal-learning-candidate
  owner_skill: aar                    # or debrief
  kind: hybrid
  entry_point: "TBD — /aar and /debrief are full skills, not callable components"
  
  problem: >
    Causal learning requires analysis depth that a deterministic component
    cannot provide. The full /aar or /debrief skill produces this, but invoking
    them defeats component composition. This destination requires either:
    (a) accepting that causal learning routes to the full skill (not a component),
    or (b) extracting a lightweight learning-recording component from /aar.
    Option (a) is more honest: the recipe records a pointer ("run /aar for causal
    learning") rather than pretending it composed a component.
```

### Implication for recipe verdict

Three of five branch destinations lack deterministic entry points. The recipe can handle:
- `persist-todo-action` ✓
- `persist-harvest-obligation` ✓
- `record-no-new-work-disposition` ✓ (disposition record only)

The recipe must **defer**:
- `persist-handoff-continuation` → flag for LLM follow-up
- `persist-opportunity-candidate` → route to harvest store as adapter, or flag
- `persist-causal-learning-candidate` → flag for `/aar` invocation

This means the recipe is **not fully component-composed** for all branches. The verdict reflects this: `MANUAL_RECIPE_DESIGN_NEEDS_MORE_EVIDENCE`.

---

## 7. Workflow lifecycle manifest

### The problem

The recipe currently writes its aggregated outcome only at the end (`persist-workflow-outcome`). A crash before finalization could make the workflow invisible — the same gap that `/check` had before `check_lifecycle.py`.

### The solution: workflow-run.json

Following the same principle as `/check`'s lifecycle: `start evidence → intermediate evidence → mechanical finalization`.

A durable lifecycle artifact is created before the first executable component and updated after every completed node:

```yaml
# workflow-run.json — written atomically at initialization
schema_version: "1"
workflow_id: "check-failure-to-close-readiness-019fb0bd"
recipe_id: "check-failure-to-close-readiness"
recipe_version: "1.3"
session_id: "019fb0bd-..."
check_run_id: "20260729-120000-000"     # null if not yet located

status: PLANNED                          # PLANNED → RUNNING → CLASSIFIED → BRANCHING
                                         # → READY_FOR_CLOSE | NOT_READY_FOR_CLOSE
                                         # | INCOMPLETE | FAILED

active_nodes: []                         # convenience list of currently-running node IDs
started_at: "2026-07-30T15:00:00Z"
updated_at: "2026-07-30T15:00:00Z"
finalized_at: null

accepted_classification_ref: null        # path to persisted classification JSON
                                         # committed BEFORE any branch fires

branch_states: {}                        # {destination: PENDING|RUNNING|PERSISTED|PERSISTED_UNCLAIMED|PERSISTED_WITH_CONFLICT|DEFERRED_WITH_OBLIGATION|NO_ACTION|FAILED}
branch_receipts: []                      # appended as each branch completes

close_readiness: null                    # populated by derive-close-readiness

evaluation_obligations: []               # appended as evaluation contracts are persisted

failure: null                            # reason string if status is FAILED or INCOMPLETE

# Per-node lifecycle state (authoritative for recovery)
nodes:
  validate-session-binding:
    status: PENDING                      # PENDING | RUNNING | COMPLETE | FAILED | SKIPPED
    attempt: 0
    started_at: null
    updated_at: null
    completed_at: null
    input_refs: []                       # references to consumed artifacts/inputs
    output_refs: []                      # references to produced artifacts/outputs
    idempotency_key: null                # for side-effecting nodes
    failure: null
  locate-session-check-runs:
    status: PENDING
    attempt: 0
    # ... same schema per node
  # ... one entry per DAG node
```

### Requirements

| Requirement | Enforcement |
|-------------|------------|
| Written atomically at workflow initialization | Before `validate-session-binding` executes; tmp + os.replace |
| Updated after every completed node | Status transitions to RUNNING after first node; updated_at refreshed |
| Classification reference committed before branch execution | `accepted_classification_ref` set before any branch node starts |
| Each branch status recorded independently | `branch_states[destination]` updated per branch receipt |
| Crash recovery resumes only from durable completed-node state | Resume reads manifest, skips completed nodes, continues from `current_node` |
| Malformed manifests fail visibly | Validator rejects; does not silently proceed |
| Foreign-session manifests ignored | Session-ID binding enforced |
| Terminal outcome derived from manifest + receipts | `persist-workflow-outcome` reads manifest, does not independently compute |
| Absence of finalization remains visible | A manifest with status RUNNING after workflow process dies is detectable as incomplete |

### Crash recovery protocol (per-node lifecycle state)

Per-node states are authoritative. The `active_nodes` list is a convenience, not the recovery source.

```
Node state transitions:
  PENDING → RUNNING → COMPLETE
  PENDING → SKIPPED
  RUNNING → FAILED
  FAILED → RUNNING    (only when retry policy permits)

Recovery rules:
  1. Read workflow-run.json
  2. If workflow status is terminal: report current state; do not resume
  3. For each node in dependency order:
     COMPLETE: never rerun
     SKIPPED: never run
     PENDING: execute when all dependencies are COMPLETE
     RUNNING after process loss:
       → reconcile side effects before deciding
       → if side effect found (by idempotency key search): mark COMPLETE, record receipt
       → if side effect absent: mark PENDING, re-execute
     FAILED: block or retry according to contract retry policy
  4. If manifest is missing or malformed: report WORKFLOW_LOST; cannot recover
  5. If manifest session_id ≠ current session: ignore (foreign session)
```

**Do not say "resume from current_node."** A branching workflow cannot recover safely from a single `current_node` field because multiple branches may be in different states.

### Why this follows the established pattern

`/check` solved this exact problem with `check_lifecycle.py`:

| `/check` lifecycle | Workflow lifecycle |
|--------------------|-------------------|
| `check-run.json` manifest at start | `workflow-run.json` manifest at start |
| `verifier-*.json` per-verifier evidence | Branch receipts per-destination |
| `check-state.md` derived receipt | Workflow outcome derived from manifest |
| INCOMPLETE when finalization fails | INCOMPLETE when branch persistence fails |
| `/close` scans both artifacts | Crash recovery scans workflow-run.json |

The workflow lifecycle manifest applies the same proven pattern at the workflow level.

---

## 8. Corrected DAG

```yaml
recipe:
  id: check-failure-to-close-readiness
  goal: "validate check failure, classify significance, route obligation, derive close readiness"
  authority: go
  version: "1.1"
  scope: close-readiness    # NOT "safe close"
  
  workflow_inputs:
    session_id:
      required: true
      authority: current-runtime-context
      inference_forbidden: true
    check_run_id:
      required: false
  
  policy:
    - "No directory scanning for identity"
    - "No newest-file selection"
    - "No foreign-session access"
    - "Model output persisted before side effects"
  
  components:
    # --- Phase 1: validate and locate ---
    - id: validate-session-binding
      kind: deterministic
      entry_point: "session_resolver.resolve_session_dir"
      consumes: [session-summary]
      produces: [session-binding]
      authority: session
    
    - id: locate-session-check-runs
      kind: deterministic
      consumes: [check-run-manifest]
      produces: [selected-run]
      authority: check
      on_ambiguous: STOP_AND_REPORT
    
    # --- Phase 2: read and reconcile ---
    - id: read-check-lifecycle
      kind: deterministic
      entry_point: "check_lifecycle.read_manifest"
      consumes: [check-run-manifest]
      produces: [manifest-state]
      authority: check
    
    - id: reconcile-check-evidence
      kind: deterministic
      entry_point: "close_accounting.scan_check_receipts"
      consumes: [check-state-receipt, check-run-manifest]
      produces: [reconciled-evidence]
      authority: check
    
    # --- Phase 3: classify (model-based, persisted before side effects) ---
    - id: classify-check-outcome
      kind: hybrid
      produces: [outcome-classification]
      authority: check
      commit_protocol: PERSIST_BEFORE_BRANCH
    
    - id: classify-improvement-output
      kind: hybrid
      produces: [destinations, rationale]
      authority: improvement
      commit_protocol: PERSIST_BEFORE_BRANCH
    
    # --- Phase 4: persist selected branches ---
    - id: persist-todo-action
      kind: deterministic
      condition: "destinations contains 'todo'"
      produces: [todo-receipt]
      authority: tasks
    
    - id: persist-harvest-obligation
      kind: deterministic
      condition: "destinations contains 'harvest'"
      produces: [harvest-receipt]
      authority: harvest
    
    - id: defer-handoff-continuation
      kind: deterministic
      condition: "destinations contains 'handoff'"
      produces: [deferral-receipt]
      authority: lifecycle
      note: "No programmatic writer; records deferral for LLM follow-up"
    
    - id: defer-opportunity-candidate
      kind: deterministic
      condition: "destinations contains 'opportunity'"
      produces: [deferral-receipt]
      authority: improvement
      note: "No dedicated store; records deferral or routes to harvest adapter"
    
    - id: defer-causal-learning
      kind: deterministic
      condition: "destinations contains 'causal_learning'"
      produces: [deferral-receipt]
      authority: improvement
      note: "Full /aar needed; records pointer for operator"
    
    - id: record-no-new-work-disposition
      kind: deterministic
      condition: "destinations contains 'no_new_work'"
      produces: [disposition-receipt]
      authority: improvement
    
    # --- Phase 5: derive close readiness ---
    - id: derive-close-readiness
      kind: deterministic
      entry_point: "close_accounting.resolve_gates"
      consumes: [reconciled-evidence]
      produces: [close-readiness-state]
      authority: close
    
    # --- Phase 6: persist outcome ---
    - id: persist-workflow-outcome
      kind: deterministic
      produces: [workflow-run-record]
      authority: workflow
  
  dag:
    - node: validate-session-binding
      inputs: [session_id]
    - node: locate-session-check-runs
      depends_on: [validate-session-binding]
      inputs: [session_id, check_run_id]
    - node: read-check-lifecycle
      depends_on: [locate-session-check-runs]
    - node: reconcile-check-evidence
      depends_on: [validate-session-binding]
    - node: classify-check-outcome
      depends_on: [read-check-lifecycle, reconcile-check-evidence]
    - node: classify-improvement-output
      depends_on: [classify-check-outcome]
      branch_persist_first: true       # classification persisted before any branch fires
    # Branch nodes — only fire for selected destinations
    - node: persist-todo-action
      depends_on: [classify-improvement-output]
      condition: "destinations contains 'todo'"
    - node: persist-harvest-obligation
      depends_on: [classify-improvement-output]
      condition: "destinations contains 'harvest'"
    - node: defer-handoff-continuation
      depends_on: [classify-improvement-output]
      condition: "destinations contains 'handoff'"
    - node: defer-opportunity-candidate
      depends_on: [classify-improvement-output]
      condition: "destinations contains 'opportunity'"
    - node: defer-causal-learning
      depends_on: [classify-improvement-output]
      condition: "destinations contains 'causal_learning'"
    - node: record-no-new-work-disposition
      depends_on: [classify-improvement-output]
      condition: "destinations contains 'no_new_work'"
    - node: derive-close-readiness
      depends_on: [classify-check-outcome, reconcile-check-evidence]
    - node: persist-workflow-outcome
      depends_on: [derive-close-readiness, ALL_BRANCH_NODES]
  
  terminal_conditions:
    - "check evidence reconciled"
    - "close readiness truthfully derived"
    - "every selected destination is: PERSISTED, DEFERRED_WITH_OBLIGATION, or NO_ACTION"
    - "every required evaluation has a persisted consumer obligation (todo or harvest)"
    - "workflow-run.json references all destination and evaluation receipts"
  
  terminal_states:
    READY_FOR_CLOSE:
      conditions:
        - "no blocking check/close conditions"
        - "all branches PERSISTED, DEFERRED_WITH_OBLIGATION, or NO_ACTION"
        - "all evaluations have persisted consumer obligations"
        - "workflow-run.json finalized with all receipts"
      meaning: "/close may proceed"
    
    NOT_READY_FOR_CLOSE:
      conditions:
        - "blocking check/close conditions found"
        - "but workflow completed (all branches dispositioned)"
      meaning: "/close should not proceed; operator must address blockers"
    
    WORKFLOW_INCOMPLETE:
      conditions:
        - "one or more branches FAILED"
        - "or evaluation consumer could not be persisted"
        - "or workflow-run.json missing/malformed"
      meaning: "workflow did not complete; manual intervention required"
    
    FAILED:
      conditions:
        - "workflow itself crashed"
        - "or classification rejected"
        - "or session binding invalid"
      meaning: "workflow cannot proceed; report failure reason"
```

---

## 8. Branch completion receipts and deferral obligations

`persist-workflow-outcome` must depend on ALL branch nodes, not just the classification step. A classification without completed persistence is `WORKFLOW_INCOMPLETE`, not success.

### Receipt statuses

| Status | Meaning | Permits terminal |
|--------|---------|----------------|
| `PERSISTED` | Destination outcome durably persisted; claim acquired (harvest) or write confirmed (tasks) | READY_FOR_CLOSE (if no other blockers) |
| `PERSISTED_UNCLAIMED` | Event durable but claim state unknown (harvest crash before claim) | NOT_READY_FOR_CLOSE (requires reconciliation) |
| `PERSISTED_WITH_CONFLICT` | Event durable but not authoritative (lost claim, valid conflict sibling) | NOT_READY_FOR_CLOSE (conflict requires resolution) |
| `DEFERRED_WITH_OBLIGATION` | Destination lacks deterministic component; follow-up obligation persisted to existing store | READY_FOR_CLOSE (if obligation is durable) |
| `NO_ACTION` | Disposition recorded; no follow-up needed | READY_FOR_CLOSE |
| `FAILED` | Neither outcome nor obligation persisted | INCOMPLETE |

**A durable write is not a pure persistence failure merely because a later claim step failed.** A harvest event that was fsync'd and os.replace'd is durable — the claim outcome determines whether it's `PERSISTED`, `PERSISTED_UNCLAIMED`, or `PERSISTED_WITH_CONFLICT`.

**A deferral does not persist the intended destination outcome.** It persists an unresolved obligation to perform that destination later. Three distinct claims must not be conflated:

| Claim | What it means | Store |
|-------|--------------|-------|
| Domain outcome persisted | The actual handoff, opportunity, or learning was written to its primary store | Handoff file, opportunity store, AAR report |
| Follow-up obligation persisted | A todo or harvest record tells the operator to perform the destination later | Tasks store, harvest events |
| Workflow evidence persisted | The workflow artifact records what happened | workflow-run.json |

**The workflow artifact is evidence, not the primary obligation store.** Every deferral must create an actionable obligation through an existing persistent store whenever possible.

### Default deferral mapping

| Destination | Deferral action | Obligation store |
|-------------|----------------|-----------------|
| handoff unavailable | Create todo action: "Invoke /handoff for <topic>, referencing workflow <id> and session <id>" | todo |
| causal-learning unavailable | Create todo action or harvest obligation: "Run /aar or /debrief for causal analysis of <classification>" | todo or harvest |
| opportunity store unavailable | If genuinely unrealized value → harvest with `operation=INVESTIGATE`; otherwise → todo: "Investigate and disposition opportunity <description>" | harvest or todo |
| no-new-work | Record disposition only | workflow-run.json |

### Deferral receipt schema

```yaml
branch_receipt:
  destination: handoff
  status: DEFERRED_WITH_OBLIGATION
  obligation_store: todo          # todo | harvest
  obligation_id: "task-43"        # task_id or event_id from the store
  workflow_ref: "check-failure-to-close-readiness-019fb0bd"
  session_id: "019fb0bd-..."
  reason: "No programmatic handoff writer exists; LLM must invoke /handoff"
  required_follow_up: "Operator invokes /handoff <topic> to create continuation"
  timestamp: "2026-07-30T..."
```

**If the follow-up obligation cannot be persisted** (e.g., todo store is locked, harvest store is corrupt), the branch is `FAILED`, not deferred.

### PERSISTED receipt example

```yaml
branch_receipt:
  destination: todo
  status: PERSISTED
  receipt_ref: "task-42"          # task_id from tasks store
  workflow_ref: "check-failure-to-close-readiness-019fb0bd"
  session_id: "019fb0bd-..."
  timestamp: "2026-07-30T..."
```

### NO_ACTION receipt example

```yaml
branch_receipt:
  destination: no_new_work
  status: NO_ACTION
  workflow_ref: "check-failure-to-close-readiness-019fb0bd"
  session_id: "019fb0bd-..."
  reason: "Classification determined no new work is warranted"
  timestamp: "2026-07-30T..."
```

The workflow outcome aggregates all branch receipts. If any selected destination has status `FAILED`, the workflow terminal state is `WORKFLOW_INCOMPLETE`.

---

## 9. Close-readiness terminal states (not "safe close")

**v3.0 said:** the recipe reaches "safe close."

**Correction:** the pilot scope is `check-failure-to-close-readiness`. It derives whether `/close` may proceed but does not execute `/close`. Its terminal states are:

| State | Meaning |
|-------|---------|
| `READY_FOR_CLOSE` | No blocking conditions; all branches dispositioned; all evaluations have consumers; workflow-run.json finalized |
| `NOT_READY_FOR_CLOSE` | Blocking issues found but workflow completed; `/close` should not proceed |
| `WORKFLOW_INCOMPLETE` | One or more branches FAILED or evaluation consumer missing; manual intervention required |
| `FAILED` | Workflow crashed, classification rejected, or session binding invalid |

A later integration may invoke `/close` after the recipe mechanics are proven. The recipe does not claim the session was closed.

---

## 10. Model-classification commit protocol

For `classify-check-outcome` and `classify-improvement-output`:

1. **Persist structured model output before any side effect.** The classification is written to a JSON file in the run directory before any branch node executes.
2. **Validate against schema and allowed destinations.** If the model output does not match the schema or includes unknown destinations, the classification is rejected and the workflow stops.
3. **Retain all retry attempts.** If the model is re-invoked, prior attempts are kept in the run directory for audit.
4. **Designate one accepted classification version.** The first classification that passes validation is the accepted version. Subsequent attempts must explicitly supersede with a reason.
5. **Branch only from the accepted version.** All branch nodes consume the accepted classification.
6. **Prohibit silent reclassification after side effects begin.** Once any branch node has persisted, the classification is frozen. If new evidence emerges, an explicit compensation/reconciliation step is required.
7. **Prefer deterministic rules for clear cases.** Use rules for obvious classifications (e.g., manifest status INCOMPLETE → `missing_verification`). Use model judgment only for ambiguous cases.

---

## 11. Learning/evaluation contract with persisted consumer

The workflow outcome includes an evaluation section for each destination. **Every evaluation must have a persisted consumer obligation** — `owner_or_consumer: operator` is memory-dependent and insufficient.

### Corrected evaluation contract

```yaml
evaluation:
  hypothesis: "A todo action will prevent recurrence of this check failure"
  expected_outcome: "Next check run for the same concern passes"
  observation_source: "next /check run for the same session chain"
  success_measure: "same concern does not FAIL in subsequent check"
  recurrence_measure: "count of FAIL verdicts for same concern in next 3 sessions"
  review_trigger: "if recurrence > 0 within 3 sessions"
  
  # Persisted consumer — NOT just "operator"
  obligation_store: todo              # todo | harvest
  obligation_id: "task-44"            # task_id or event_id
  consumer_skill: todo                # todo | harvest | aar
  workflow_ref: "check-failure-to-close-readiness-019fb0bd"
  
  retain_modify_retire_criteria:
    retain: "recurrence = 0 after fix applied"
    modify: "classification was wrong → adjust rules"
    retire: "concern resolved permanently → no longer needed"
```

### Proportional evaluation rules

Not every destination requires a new evaluation obligation. Evaluation must be proportional to risk:

```yaml
evaluation_required: true | false
evaluation_reason: "..."          # why evaluation is or isn't needed
evaluation_risk: low | medium | high
```

| Situation | evaluation_required | Rationale |
|-----------|-------------------|-----------|
| Repeated, uncertain, systemic, or behavior-changing outcome | true | High risk of recurrence; needs follow-up |
| Deferred obligation already carrying a follow-up | false | Reuse the destination's follow-up obligation if it includes evaluation criteria |
| Trivial deterministic NO_ACTION with high confidence | false | Passive workflow telemetry sufficient; record why |
| Low-confidence NO_ACTION or recurrence risk | true | Uncertainty warrants active follow-up |
| Destination persisted (todo/harvest) with its own tracking | false if destination obligation includes review criteria | Avoid duplicate evaluation and destination obligations for same future action |

**When `evaluation_required=true`**, a persisted consumer (todo or harvest) is mandatory.
**When `evaluation_required=false`**, the evaluation contract records why passive evidence is sufficient.

### Destination-specific evaluation examples

| Destination | Hypothesis | Obligation store | Consumer |
|-------------|-----------|-----------------|----------|
| todo | "Fixing the code eliminates the check failure" | todo | todo (follow-up to verify fix held) |
| harvest | "The unrealized value is later recovered" | harvest | harvest (track resolution) |
| opportunity | "The pattern is investigated and accepted or rejected" | todo | todo (investigate within 30 days) |
| no-new-work | "The issue does not recur" | todo | todo (check for recurrence in 3 sessions) |

**If no valid consumer can be persisted**, the workflow branch is `INCOMPLETE`, not complete.

---

## 12. Revised implementation phases

### Phase A1 — characterization and contracts

- Characterize all atomic-write callers (the 11 verification concerns above)
- Verify todo and harvest API descriptions (signatures, return values, locking, dedup status)
- Design workflow-run.json manifest schema with per-node lifecycle state
- Design branch-receipt schema with idempotency keys
- Design evaluation-obligation schema with proportional rules
- Design deferral-adapter contracts (entry points, schemas, existing-store writes)
- Design session-bound check-run locator
- Design idempotency-key computation and reconciliation protocol
- Build fixture corpus (all fixtures from Section 14)
- Write negative-test specification (all tests from Section 15)
- Write contract-validator skeleton

**No executable pilot components. No production behavior changes. Characterization and design only.**

**Effort:** ~6 hours

### Phase A2 — isolated pilot components

- Implement todo adapter with structured `create_task()` extraction
- Validate direct harvest adapter with idempotency-key reconciliation
- Implement deferral adapters (handoff, opportunity, causal-learning)
- Implement session-bound check-run locator
- Implement per-node lifecycle state in workflow-run.json
- Implement idempotency-key recording and reconciliation for all side-effecting branches
- Test only against hermetic stores and fixtures

**A2 adds executable pilot code but changes no existing caller or production workflow behavior.** No invocation from `/go`, `/check`, `/close`, or other production skills.

**Effort:** ~12 hours

### Phase B — one primitive extraction

- Extract atomic-write only if A1 caller characterization passes
- Retain compatibility wrappers initially
- Run differential and existing tests
- Provide rollback path

**Effort:** ~2 hours (conditional on A1)

### Phase C — recipe simulation

- Execute the recipe against hermetic fixtures (no production writes)
- Test all branches, recovery paths, and idempotency scenarios
- Verify terminal conditions fire correctly
- Verify crash recovery from per-node lifecycle state

**Effort:** ~8 hours

### Phase D — one real pilot

- Run against one real current-session check failure or incomplete run
- Compare result to the existing manual whole-skill workflow
- Record user corrections and missed classifications

**Effort:** ~4 hours

### Phase E — repeat or reject

- Repeat enough times to assess recipe usefulness
- Planner remains out of scope

**Gate:** recipe earns continuation only if it improves correctness, reliability, or user burden vs the existing manual workflow.

**Transcript-parser common-core work is a separate refactor candidate.** It is not a prerequisite for this recipe because the recipe does not require shared transcript parsing.

---

## 13. Comparison: corrected recipe vs existing manual workflow

| Dimension | Existing manual workflow | Corrected recipe (simulated) |
|-----------|------------------------|------------------------------|
| Classification correctness | Depends on operator judgment reading /check output + /close gate | Rules + model; deterministic for clear cases; persisted |
| Obligations routed correctly | Operator manually decides: todo? harvest? handoff? | classify-improvement-output routes; operator can override |
| Duplicate work created | Possible (operator creates harvest event for something already tracked) | Current stores do not prevent semantic duplicates. Adapter-level duplicate detection via idempotency keys is DESIGN/TBD. Duplicate-work reduction is unknown until implemented and tested |
| Missed close gates | Possible (operator forgets to check verify gate) | derive-close-readiness is mechanical |
| User intervention | Operator invokes each skill manually | Operator reads one workflow report; deferrals flagged |
| Durable receipts | Separate per skill (check-state.md, harvest event, handoff file) | One workflow artifact aggregating all receipts |
| Recovery after interruption | Manual — re-run from scratch | DAG resume from last completed node |
| Cognitive burden | High — operator juggles 3+ skills per failure | Lower — one workflow report; but 3 destinations deferred to LLM |
| Maintenance burden | Zero additional (existing skills) | Medium (contracts + recipe + runner + fixtures) |

**The recipe earns continuation only if simulated runs show fewer missed classifications and fewer missed gates than the manual workflow.** Demonstrating a DAG runner is not sufficient.

---

## 14. Required fixtures

| Fixture | Purpose |
|---------|---------|
| PASS run | check-run.json COMPLETE + verdict PASS; check-state.md present |
| FAIL run | check-run.json COMPLETE + verdict FAIL; check-state.md present with issue |
| INCOMPLETE run | check-run.json INCOMPLETE; no check-state.md |
| FINALIZE_FAILED run | check-run.json FINALIZE_FAILED; no check-state.md |
| Inconsistent receipt/manifest | manifest COMPLETE but receipt says FAIL |
| Malformed manifest | check-run.json contains invalid JSON |
| Multiple current-session runs | two check-run.json bound to same session_id |
| Foreign-session run | check-run.json bound to different session_id |
| No matching run | no check-run.json for session |
| Todo destination | classification selects todo |
| Harvest destination | classification selects harvest |
| Handoff deferral | classification selects handoff (no writer) |
| Opportunity deferral | classification selects opportunity (no store) |
| Causal-learning deferral | classification selects causal_learning |
| Multiple destinations | classification selects todo + harvest simultaneously |
| No-new-work (high confidence) | classification selects no_new_work; evaluation_required=false |
| No-new-work (low confidence) | classification selects no_new_work; evaluation_required=true |
| Persisted conflict | harvest event durable but claim lost |

---

## 15. Negative tests

| # | Test | Expected result |
|---|------|----------------|
| 1 | Workflow initialized, crash before first node | workflow-run.json exists with all nodes PENDING; recovery starts from first node |
| 2 | Classification persisted, crash before branches | Recovery reads classification ref; branches start from PENDING |
| 3 | Task persisted, crash before receipt, recovery by idempotency key | Recovery searches tasks for key; finds existing; records receipt; no duplicate |
| 4 | Harvest event persisted, claim lost, recovery classification | Recovery finds event by key; classifies as PERSISTED_UNCLAIMED or PERSISTED_WITH_CONFLICT |
| 5 | Same branch retried with same idempotency key | Adapter returns existing receipt; no duplicate created |
| 6 | Same payload under different workflow IDs | Different idempotency keys → both persist (different workflows) |
| 7 | Same workflow and destination with changed classification version | Different idempotency key (classification version in hash) → both persist if retry is legitimate |
| 8 | Task stdout wording changes but structured API remains stable | create_task() return is stable; CLI display may change without breaking adapter |
| 9 | Node marked RUNNING with side effect absent | Recovery: side effect search finds nothing → mark PENDING, re-execute |
| 10 | Node marked RUNNING with side effect present | Recovery: side effect search finds existing → mark COMPLETE, record receipt |
| 11 | Two branch nodes active concurrently where allowed | Both write to different stores; idempotency keys prevent collision |
| 12 | Evaluation obligation reuses existing destination obligation | No duplicate created; evaluation references destination obligation_id |
| 13 | High-confidence no-new-work creates no follow-up obligation | evaluation_required=false; no todo/harvest written; passive telemetry only |
| 14 | Low-confidence no-new-work creates an evaluation todo | evaluation_required=true; todo created with evaluation criteria |
| 15 | Duplicate-detection adapter disabled | Idempotency key not checked; duplicate created; test documents the risk |
| 16 | Workflow has a persisted conflict that blocks close readiness | PERSISTED_WITH_CONFLICT → terminal = NOT_READY_FOR_CLOSE (not READY) |
| 17 | Destination deferred but follow-up obligation write fails | Branch receipt status=FAILED; terminal = INCOMPLETE |
| 18 | READY_FOR_CLOSE attempted with an unpersisted branch | Terminal check fails; status remains INCOMPLETE |
| 19 | Foreign-session workflow manifest | Ignored; session-ID binding enforced |
| 20 | Malformed workflow lifecycle artifact | Recovery reports WORKFLOW_LOST |
| 21 | Accepted classification changes after side effect | Rejected — frozen after first branch persists |
| 22 | Multiple check runs without explicit selection | MULTIPLE_REQUIRES_SELECTION; workflow stops |
| 23 | Model returns unknown destination | Classification rejected; workflow stops |

---

## 16. Phase A1 output

Phase A1 produces the following artifacts. **No executable pilot components. No production behavior changes. No atomic-write extraction. No runner implementation.**

| # | Artifact | Description |
|---|----------|-------------|
| 1 | Corrected design document (this file) | v4 with all transaction-integrity corrections applied |
| 2 | Atomic-write caller-characterization results | All 11 callers checked against the 10-point verification checklist |
| 3 | Verified todo persistence API contract | Code-verified: cmd_add takes argparse.Namespace; metadata field exists; adapter design with create_task() |
| 4 | Verified harvest persistence API contract | Code-verified: write_event is clean callable; no dedup; claim semantics documented |
| 5 | workflow-run.json schema | Per-node lifecycle state; not current_node |
| 6 | Branch-receipt schema | PERSISTED / PERSISTED_UNCLAIMED / PERSISTED_WITH_CONFLICT / DEFERRED_WITH_OBLIGATION / NO_ACTION / FAILED |
| 7 | Evaluation-obligation schema | Proportional: evaluation_required flag; persisted consumer when required |
| 8 | Idempotency-key contract | hash(workflow_id + classification_version + destination + normalized_payload); per-store reconciliation |
| 9 | Deferral-adapter designs | Entry points, schemas, existing-store write, idempotency keys |
| 10 | Fixture corpus | All 18 fixtures from Section 14 |
| 11 | Negative-test specification | All 23 tests from Section 15 |
| 12 | Contract-validator skeleton | Checks entry points, schemas, authority, bindings, branch receipts, idempotency, terminal conditions |

**Phase A1 does NOT:**
- Extract atomic-write (Phase B)
- Implement any executable code (Phase A2)
- Implement the workflow runner (Phase C)
- Change any production caller

---

## 17. Readiness verdict

### Staged readiness milestones

The recipe advances through staged verdicts. Do not skip stages.

| Stage | Verdict | When |
|-------|---------|------|
| After A1 (characterization + contracts) | `COMPONENT_FOUNDATION_CHARACTERIZED` | Schemas designed, APIs verified, fixtures built, tests specified |
| After A2 (isolated pilot components) | `PILOT_COMPONENTS_HERMETICALLY_PROVEN` | Adapters + locator + idempotency pass hermetic tests |
| After contract validation | `RECIPE_READY_FOR_SIMULATION` | Validator confirms all contracts match code |
| After full fixture simulation (Phase C) | `MANUAL_RECIPE_READY_FOR_REAL_PILOT` | All branches + recovery paths + negative tests pass |
| After real pilot evidence (Phase D-E) | `MANUAL_RECIPE_PILOT_PROVEN` or `MANUAL_RECIPE_PILOT_NOT_JUSTIFIED` | Real-session comparison shows improvement (or not) |

**Current verdict: `MANUAL_RECIPE_DESIGN_NEEDS_MORE_EVIDENCE`** — A1 has not been completed. The recipe cannot advance to `COMPONENT_FOUNDATION_CHARACTERIZED` until schemas are designed, APIs verified, and the fixture corpus built.

**Do not say the recipe becomes ready for implementation after implementation components have already been built.** The readiness milestones are sequential.

---

## 18. PROVEN / INFERRED / UNKNOWN / FAILED

| Claim | Label | Evidence |
|-------|-------|---------|
| Source duplication exists | OBSERVED | scan_duplication.py output |
| Atomic-write core pattern is identical | OBSERVED | audit_atomic_write.py — all use tmp + os.replace + PID |
| Atomic-write caller semantics are compatible | TO_VERIFY | Not yet inspected for all 11 callers |
| `/check → /close` has no material redundant runtime work | INFERRED | Runtime trace showed different operations, but "material" is a judgment |
| `tasks.py:cmd_add` takes argparse.Namespace, not kwargs | OBSERVED | Code inspection: `def cmd_add(args: argparse.Namespace)` — adapter required |
| `tasks.py` has NO duplicate detection | OBSERVED | cmd_add creates task unconditionally; no subject lookup before write |
| `harvest/store.py:write_event` is directly callable | OBSERVED | `def write_event(event, item_id, parent_event_id, **fields) -> dict` — clean API |
| `harvest/store.py` has NO duplicate detection | OBSERVED | write_event creates event unconditionally; item_id is caller-supplied, not checked |
| Tasks returns task_id via stdout, not structured return | OBSERVED | `print(f"created T-{new_id}")` — no return value |
| Harvest returns structured dict | OBSERVED | `return record` with event_id, item_id, claimed fields |
| Handoff has no programmatic writer | OBSERVED | grep of handoff/__lib for write/create/save/persist: no matches |
| No opportunity-candidate store exists | OBSERVED | Directory scan of P:/.data; no opportunity store found |
| 3 of 5 branch destinations lack deterministic entry points | OBSERVED | Persistence inventory (Section 6) |
| Recipe simulation will show fewer missed classifications | UNKNOWN | Requires Phase D execution |
| Recipe reduces cognitive burden | UNKNOWN | Requires Phase E operator feedback |
| Dynamic planner adds value over static recipe | UNKNOWN | Not evaluated (out of scope per v3) |

---

## 19. Exact next implementation step

**Phase A1: characterization and contracts**

1. Write the atomic-write caller characterization script (check all 11 concerns from Section 3 against each implementation)
2. Design the per-node workflow-run.json lifecycle schema (Section 7)
3. Design the idempotency-key computation and per-store reconciliation protocol (Section 6)
4. Design the todo adapter with `create_task()` bounded extraction (Section 6)
5. Design the harvest adapter with claim-outcome reconciliation (Section 6)
6. Design deferral adapters with idempotency support
7. Design the `locate-session-check-runs` component
8. Build fixture corpus (all 18 fixtures from Section 14)
9. Write negative-test specification (all 23 tests from Section 15)
10. Write the contract-validator skeleton

No production callers change in A1. No executable code. No extraction. This is characterization and design only.

---

## Final verdict

### Recipe verdict: `MANUAL_RECIPE_DESIGN_NEEDS_MORE_EVIDENCE`

The recipe cannot advance to `COMPONENT_FOUNDATION_CHARACTERIZED` until A1 completes:
- Per-node lifecycle schema validated against crash scenarios
- Idempotency-key reconciliation mechanically proven against hermetic stores
- Deferral adapters designed with real entry points and tests
- Fixture corpus built and all negative tests specified
- Duplicate detection either implemented in adapters or explicitly removed from the contract

**The design can recover from a crash after a todo or harvest side effect without duplicating the outcome** — but only after A2 implements idempotency-key reconciliation and the recovery path is mechanically proven. Until then, crash-safe retry is a DESIGN claim, not a PROVEN fact.

### Overall: `BUILD_COMPONENT_FOUNDATION_AND_MANUAL_RECIPE_PILOT`

Preserved from v3.0. The direction is correct; the recipe needs A1 (characterization + contracts) before A2 (isolated implementation).

---

## Final design verdict

### `TRANSACTION_INTEGRITY_DESIGN_READY_FOR_A1`

The design specifies:
- Per-node lifecycle state (not single `current_node`)
- Idempotency keys for every side-effecting branch
- Crash recovery that reconciles side effects before deciding COMPLETE vs retry
- Refined branch statuses distinguishing durable-but-unclaimed from failed
- Proportional evaluation (not every destination needs a new obligation)
- Staged readiness milestones (A1 → A2 → simulation → real pilot)
- Todo adapter design with bounded extraction (not stdout parsing)

**The design can recover from a crash after a todo or harvest side effect without duplicating the outcome** — via idempotency-key search during recovery. This path is designed but not yet mechanically proven. A1 produces the characterization and contracts; A2 implements and proves it against hermetic stores.

Phase A1 is the exact next authorized implementation step.
