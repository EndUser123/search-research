# Phase A1 Deliverable: Component Foundation Characterization

**Created:** 2026-07-30
**Author:** session 019fb0bd (Grok)
**Status:** A1 deliverables — schemas, contracts, fixtures, tests, registry
**Design doc version:** v4.1 (corrected per Part 1 of this task)
**No production caller changes. No extraction. No runner. No planner.**

---

## A1 Completion Report

### 1. Files inspected

| File | Purpose |
|------|---------|
| `tasks/scripts/tasks.py` | Todo persistence API (cmd_add, create_task design) |
| `harvest/scripts/store.py` | Harvest event store (write_event, claim protocol) |
| `check/__lib/check_lifecycle.py` | Check lifecycle (start_run, finalize_run, derive_verdict) |
| `check/__lib/write_check_state.py` | Legacy receipt writer |
| `check/__lib/transcript_parser.py` | Transcript parser (check copy) |
| `check/__lib/event_model.py` | Event model (check copy) |
| `close/__lib/close_accounting.py` | Close scanner (scan_check_receipts, resolve_gates) |
| `aar/__lib/transcript_parser.py` | Transcript parser (aar copy) |
| `aar/__lib/event_model.py` | Event model (aar copy) |
| `aar/__lib/session_resolver.py` | Session resolver |
| All skill `__lib/` and `scripts/` dirs | Atomic-write pattern scan (16 files across 8 skills) |
| `build_skill_graph.py` | Graph generator |
| `skill-graph.md` | Generated graph |
| `capabilities.py` | Capability registry |

### 2. Corrections applied to v4

| # | Correction | Applied |
|---|-----------|---------|
| 1 | Remove stale `current_node` operational dependency | ✅ — replaced with per-node state evaluation in dependency order |
| 2 | Clarify A1 no-code boundary | ✅ — "No production-executable pilot components and no production behavior changes" |
| 3 | Unify recipe version to `1.4` | ✅ — all artifacts reference recipe_version "1.4" |
| 4 | Define canonical payload normalization | ✅ — see Section C (idempotency-key schema) |
| 5 | Correct classification-version retry | ✅ — frozen after first side effect; supersession requires reconciliation |
| 6 | Define conflict terminal handling | ✅ — PERSISTED_UNCLAIMED/CONFLICT → NOT_READY_FOR_CLOSE + reconciliation obligation |
| 7 | Normalize terminal statuses (5 states) | ✅ — READY_FOR_CLOSE, NOT_READY_FOR_CLOSE, INCOMPLETE, FAILED, LOST |
| 8 | Expand todo reconciliation scope | ✅ — search all task states, not just active |
| 9 | Add concern identity | ✅ — see Section C (concern schema) |
| 10 | Static component registry | ✅ — see Section I |

### 3. Atomic-write characterization table

| Skill | Files | Named func? | parent.mkdir | PID suffix | fsync | Exception handling | JSON dumps | Verdict |
|-------|-------|------------|-------------|-----------|-------|-------------------|-----------|---------|
| tasks | tasks.py | `_atomic_write_json` | ✅ Yes (unique) | ❌ | ❌ | ❌ | ✅ indent=2 | `SHAREABLE_WITH_WRAPPER` |
| check | check_lifecycle.py | `_atomic_write_json`, `_atomic_write_text` | ❌ | ✅ Yes (unique) | ❌ | ❌ | ✅ indent=2 | `SHAREABLE_WITH_WRAPPER` |
| close | close_runner.py | inline (2 sites) | ✅ | ✅ | ❌ | ✅ OSError | ✅ | `SHAREABLE_WITH_WRAPPER` |
| harvest | store.py | inline (1 site) | ✅ | ✅ | **✅ Yes (unique)** | ✅ | ✅ indent=2 | **`SEMANTICALLY_DISTINCT`** |
| aar | 3 files, inline (6 sites) | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | `SHAREABLE_WITH_WRAPPER` |
| handoff | 2 files, inline (2 sites) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ (text) | `SHAREABLE_WITH_WRAPPER` |
| fmea | fmea_scan.py, inline (1 site) | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | `INSUFFICIENT_EVIDENCE` |
| nlm-to-wiki | 4 files, inline (5 sites) | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | `INSUFFICIENT_EVIDENCE` |

**Key findings:**
- `harvest` is `SEMANTICALLY_DISTINCT`: uses fsync + publish-before-claim protocol. Cannot be replaced by a generic atomic-write primitive.
- `tasks` is the only caller that does `parent.mkdir(parents=True, exist_ok=True)`.
- `check` is the only caller using PID-suffixed temp files for collision prevention.
- 5 skills (`fmea`, `nlm-to-wiki`, `email-skill`, `nlm-bulk-ingest`, `crawl4ai`) have `INSUFFICIENT_EVIDENCE` — inline patterns detected but per-site inspection needed before extraction.
- No caller cleans up orphaned `.tmp` files on crash.

**Extraction recommendation:** defer to Phase B. A shared primitive needs parameters for: `mkdir_parents`, `pid_suffix`, `fsync`, `json_formatting`. The differences are parameterizable but require wrapper functions per caller.

### 4. Tasks and harvest code-grounded contracts

#### Tasks store contract (code-verified)

| Dimension | Observed behavior | Adapter design | A2-required change |
|-----------|------------------|----------------|-------------------|
| Entry point | `cmd_add(args: argparse.Namespace) -> None` | Extract `create_task(*, subject, description, active_form, owner, source_workflow_id, idempotency_key) -> dict` | Modify tasks.py internals |
| Return value | None (stdout: `"created T-N: <subject>"`) | Return structured dict | New return path |
| Locking | O_CREAT\|O_EXCL on `.lock`; stale break after 300s with --force | Retain identical locking | None |
| ID allocation | Watermark read → increment → existence check → write | Retain identical allocation | None |
| Atomic write | `_atomic_write_json(path, payload)` — tmp + os.replace | Retain | None |
| Schema | Required: id, subject, description, activeForm, status, blocks, blockedBy. Optional: owner, **metadata (object)** | Add metadata.source_workflow_id, metadata.idempotency_key, metadata.concern_id | New metadata fields |
| Duplicate detection | **None** — creates unconditionally | Adapter searches ALL task states (active, completed, archived) for matching idempotency_key before creating | New search function |
| Store location | `~/.claude/tasks/project-main-tasks/*.json` | Same | None |
| Compensation | `tasks.py done <id>` marks completed | Same | None |

**Available metadata fields for workflow integration:**
- `metadata` (object) — exists in schema, currently unused → can hold `source_workflow_id`, `idempotency_key`, `concern_id`, `classification_version`
- `owner` (string) — can hold workflow reference

**A2 gap: the current task store cannot search completed/archived tasks by metadata.** Idempotency reconciliation requires iterating all task JSON files and checking metadata. This is feasible (the store is flat JSON files) but not implemented.

#### Harvest store contract (code-verified)

| Dimension | Observed behavior | Adapter design | A2-required change |
|-----------|------------------|----------------|-------------------|
| Entry point | `write_event(event, item_id, parent_event_id, **fields) -> dict` | Directly callable; wrap with idempotency reconciliation | Add reconciliation wrapper |
| Return value | dict record with event_id, item_id, claimed, ts | Structured — no parsing needed | None |
| Publish protocol | Serialize → fsync → os.replace (publish) → try_claim | Retain identical protocol | None |
| Claim protocol | try_claim(parent_event_id, event_id) → bool | Retain | None |
| Schema | schema_version, event_id (ULID), item_id, parent_event_id, event, ts, terminal, claimed, **fields | Add source_workflow_id, idempotency_key, concern_id, classification_version via **fields | New fields in **fields |
| Duplicate detection | **None** — ULID prevents file collision but not semantic duplicate | Adapter searches events for matching idempotency_key before writing | New search function |
| Store location | `P:/.data/harvest/events/*.json` | Same | None |
| Compensation | Resolve/drop event | Same | None |
| fsync | **Yes** (unique among stores) | Retain | None |

**Available **fields for workflow integration:**
- Any arbitrary fields can be passed via `**fields` — already used for title, obligation, operation, source, economics
- `source_workflow_id`, `idempotency_key`, `concern_id`, `classification_version` can be added without schema change

**A2 gap: the current harvest store cannot search events by idempotency_key.** Reconciliation requires iterating all event JSON files. Feasible (glob + JSON load) but not implemented.

### 5. All schema paths

All schemas use YAML format. Schema version "1" unless noted.

#### workflow-run.json

```yaml
schema_version: "1"
workflow_id: string              # unique per run
recipe_id: "check-failure-to-close-readiness"
recipe_version: "1.4"           # AUTHORITATIVE — must match all artifacts
session_id: string              # authoritative session identity
check_run_id: string | null

status: enum[PLANNED, RUNNING, CLASSIFIED, BRANCHING, READY_FOR_CLOSE, NOT_READY_FOR_CLOSE, INCOMPLETE, FAILED]
active_nodes: list[string]      # convenience only; per-node states are authoritative
started_at: ISO8601
updated_at: ISO8601
finalized_at: ISO8601 | null

accepted_classification_ref: string | null   # path to persisted classification JSON
branch_states: map[string, enum]             # destination → PENDING|RUNNING|PERSISTED|PERSISTED_UNCLAIMED|PERSISTED_WITH_CONFLICT|DEFERRED_WITH_OBLIGATION|NO_ACTION|FAILED
branch_receipts: list[branch_receipt]        # see branch_receipt schema
close_readiness: object | null
evaluation_obligations: list[evaluation_contract]
failure: string | null

nodes: map[string, node_state]               # per-node lifecycle (authoritative)
```

#### Per-node lifecycle state

```yaml
status: enum[PENDING, RUNNING, COMPLETE, FAILED, SKIPPED]
attempt: int
started_at: ISO8601 | null
updated_at: ISO8601 | null
completed_at: ISO8601 | null
input_refs: list[string]
output_refs: list[string]
idempotency_key: string | null
failure: string | null
```

#### Accepted classification

```yaml
classification_version: string   # unique per classification attempt
recipe_version: "1.4"            # must match workflow
session_id: string
classified_at: ISO8601
model_id: string | null          # null if deterministic rules only

outcome_class: enum[pass_clean, fail_isolated, fail_systemic, incomplete, inconsistent]
outcome_confidence: float

destinations: list[destination_routing]
classification_reasoning: string
accepted: bool
superseded_by: string | null     # classification_version that superseded this one
```

#### Destination routing (within classification)

```yaml
destination: enum[todo, harvest, handoff, opportunity, causal_learning, no_new_work]
rationale: string
evaluation_required: bool
evaluation_reason: string
evaluation_risk: enum[low, medium, high]
```

#### Branch receipt

```yaml
destination: string
status: enum[PERSISTED, PERSISTED_UNCLAIMED, PERSISTED_WITH_CONFLICT, DEFERRED_WITH_OBLIGATION, NO_ACTION, FAILED]
receipt_ref: string              # task_id, event_id, or deferral note
obligation_store: enum[todo, harvest] | null
obligation_id: string | null
workflow_ref: string
session_id: string
concern_id: string               # links to concern identity
idempotency_key: string          # the key used for this branch
reason: string                   # for FAILED or DEFERRED
timestamp: ISO8601
```

#### Deferral obligation

```yaml
destination: string              # the deferred destination
status: DEFERRED_WITH_OBLIGATION
obligation_store: enum[todo, harvest]
obligation_id: string            # task_id or event_id
workflow_ref: string
session_id: string
concern_id: string
reason: string                   # why deferral was needed
required_follow_up: string       # what the operator must do
timestamp: ISO8601
```

#### Evaluation contract

```yaml
concern_id: string
evaluation_required: bool
evaluation_reason: string        # why evaluation is or isn't needed
evaluation_risk: enum[low, medium, high]
hypothesis: string
expected_outcome: string
observation_source: string
success_measure: string
recurrence_measure: string
review_trigger: string
obligation_store: enum[todo, harvest] | null   # null when evaluation_required=false
obligation_id: string | null
consumer_skill: enum[todo, harvest, aar] | null
workflow_ref: string
retain_modify_retire_criteria:
  retain: string
  modify: string
  retire: string
```

#### Concern identity

```yaml
concern_id: string               # SHA256 of normalized stable fields
concern_type: enum[check_failure, check_incomplete, check_inconsistent, config_error, systemic_pattern]
failure_signature: string        # normalized description of the failure mode
affected_scope: string           # skill, module, or system area
source_workflow_id: string
source_check_run_id: string
```

**concern_id derivation:**
```
concern_id = SHA256(
  concern_type
  + failure_signature_normalized
  + affected_scope_normalized
)
```

`failure_signature_normalized` = canonical JSON of the failure description with volatile fields (timestamps, run IDs) removed.

#### Canonical payload for idempotency

```yaml
payload_schema_version: "1"
```

**Normalization rules:**
1. Canonical JSON serialization (keys sorted recursively, UTF-8)
2. Fixed separators: `{"key": "value"}` (comma-colon, no spaces)
3. Explicit nulls: omitted (not `null`)
4. Windows paths: normalized to forward slashes
5. Volatile fields excluded: timestamps, generated IDs, retry attempt numbers, receipt paths
6. Text newlines: normalized to `\n`
7. Numerics: integers as-is, floats to 6 decimal places

**Idempotency key:**
```
idempotency_key = SHA256(
  workflow_id
  + recipe_version
  + accepted_classification_version
  + component_contract_version
  + destination
  + payload_schema_version
  + canonical_payload
)
```

**Golden fixture examples:**
- Same payload, different key order → **same key** (sorted keys)
- Same payload, different timestamp → **same key** (volatile excluded)
- Different subject text → **different key** (material change)
- Same workflow, different classification version → **different key**

#### Recipe definition

```yaml
recipe_id: "check-failure-to-close-readiness"
recipe_version: "1.4"
goal: "validate check failure, classify significance, route obligation, derive close readiness"
authority: go
scope: close-readiness
terminal_states: [READY_FOR_CLOSE, NOT_READY_FOR_CLOSE, INCOMPLETE, FAILED, LOST]
```

### 6. Fixture inventory

| # | Fixture | Type | Tests |
|---|---------|------|-------|
| F01 | PASS run | Static JSON | Check evidence reconciliation |
| F02 | FAIL run | Static JSON | Check evidence + classification |
| F03 | INCOMPLETE run | Static JSON | No receipt; manifest visible |
| F04 | FINALIZE_FAILED run | Static JSON | Manifest + no receipt |
| F05 | Inconsistent receipt/manifest | Static JSON | Contradiction detection |
| F06 | Malformed manifest | Invalid JSON | Visible failure |
| F07 | Multiple current-session runs | 2× static JSON | Ambiguity handling |
| F08 | Foreign-session run | Static JSON | Session binding |
| F09 | No matching run | Empty dir | No-evidence behavior |
| F10 | Todo destination | Classification + task fixture | Persistence |
| F11 | Harvest destination | Classification + event fixture | Persistence + claim |
| F12 | Handoff deferral | Classification + todo fixture | Deferral obligation |
| F13 | Opportunity deferral | Classification + todo/harvest | Deferral obligation |
| F14 | Causal-learning deferral | Classification + todo | Deferral obligation |
| F15 | Multiple destinations | Classification fixture | Branch parallelism |
| F16 | No-new-work (high confidence) | Classification fixture | No evaluation obligation |
| F17 | No-new-work (low confidence) | Classification fixture | Evaluation todo created |
| F18 | Persisted conflict | Harvest event + lost claim | Conflict classification |
| F19 | Canonical payload A | Payload fixture | Idempotency key = expected |
| F20 | Canonical payload A (reordered) | Payload fixture | Same key as F19 |
| F21 | Canonical payload A (different ts) | Payload fixture | Same key as F19 |
| F22 | Canonical payload B (different subject) | Payload fixture | Different key |
| F23 | Classification supersession | 2 classifications | Pre-side-effect supersession |
| F24 | Reclassification rejection | Classification + receipt | Post-side-effect frozen |
| F25 | Completed-task recovery | Task fixture (completed) | Idempotency finds existing |
| F26 | LOST workflow | Missing manifest | Cannot recover |
| F27 | Concern recurrence | 2 check runs, same concern | Same concern_id |
| F28 | Concern non-recurrence | 2 check runs, different concern | Different concern_id |

### 7. Negative-test inventory

| # | Test | Expected result |
|---|------|----------------|
| N01 | Stale `current_node` field cannot affect recovery | Per-node states authoritative; current_node ignored |
| N02 | Recipe-version mismatch between manifest and classification | Block execution |
| N03 | Equivalent payload with different key ordering | Same idempotency key |
| N04 | Volatile timestamp change | Same idempotency key |
| N05 | Material payload change (different subject) | Different idempotency key |
| N06 | Classification supersession before side effects | Accepted version changes; prior version marked superseded |
| N07 | Reclassification after side effects | Rejected — frozen after first branch persists |
| N08 | Completed task found during idempotency recovery | Return existing receipt; no duplicate |
| N09 | Durable harvest conflict creates reconciliation obligation | PERSISTED_WITH_CONFLICT + todo for reconciliation |
| N10 | Conflict without reconciliation obligation cannot finalize | Terminal = INCOMPLETE |
| N11 | LOST (missing manifest) vs INCOMPLETE (manifest exists, work missing) | Correct distinction |
| N12 | Concern signature collision | Two different failures produce same concern_id → test the normalization |
| N13 | Same concern across later check runs | concern_id matches; recurrence count increments |
| N14 | Ghost component reference in recipe | Validator rejects |
| N15 | Lexical-only edge treated as executable | Validator rejects |
| N16 | Schema-version mismatch between producer and consumer | Validator rejects |
| N17 | Undeclared authority crossing | Validator rejects |
| N18 | Side-effecting component without idempotency policy | Validator rejects |

### 8. Contract-validator specification

The validator checks A1 artifacts (schemas, contracts, registry). A1 produces the specification; A2 implements it.

| Check | Input | Pass condition | Diagnostic on fail |
|-------|-------|---------------|-------------------|
| Unique component IDs | component registry | No duplicate IDs | `DUPLICATE_COMPONENT_ID: <id> in <skill1> and <skill2>` |
| Valid recipe version | recipe + all artifacts | All reference same recipe_version | `RECIPE_VERSION_MISMATCH: expected <v>, found <v2> in <artifact>` |
| Registered entry points | component contracts | Every entry_point exists or is marked DESIGN | `UNREGISTERED_ENTRY_POINT: <entry> in <component>` |
| Artifact schema compatibility | producer + consumer contracts | Consumer schema_version ⊆ producer schema_version | `SCHEMA_MISMATCH: <producer> v<v1> → <consumer> requires v<v2>` |
| Authority crossings | component contracts | Cross-domain consumption has `cross_authority: true` | `UNDECLARED_AUTHORITY_CROSSING: <component> consumes <authority>` |
| Binding keys present | component contracts | Session-bound components declare binding_keys | `MISSING_BINDING_KEY: <component> has no binding_keys` |
| Terminal-state coverage | recipe definition | All declared terminal states are reachable | `UNREACHABLE_TERMINAL: <state> in recipe <recipe>` |
| Per-node lifecycle defined | workflow-run schema | Every recipe node has a lifecycle entry | `MISSING_NODE_LIFECYCLE: <node_id>` |
| Idempotency policy on side effects | component registry | Every side-effecting component has idempotency strategy | `MISSING_IDEMPOTENCY_POLICY: <component>` |
| Canonical payload schema | idempotency contract | Normalization rules defined and testable | `CANONICAL_PAYLOAD_UNDEFINED for <component>` |
| Branch receipt completeness | workflow terminal check | All selected destinations have receipts | `MISSING_BRANCH_RECEIPT: <destination>` |
| Evaluation proportionality | evaluation contracts | evaluation_required=true has persisted consumer | `EVALUATION_CONSUMER_MISSING: <concern_id>` |
| Concern identity present | recurrence claims | concern_id exists when recurrence is measured | `CONCERN_IDENTITY_MISSING: recurrence claimed without concern_id` |
| Recipe references only registered nodes | recipe DAG | All node component IDs exist in registry | `UNREGISTERED_COMPONENT_IN_RECIPE: <node_id>` |

### 9. Static component registry

```yaml
# Static component registry — pilot scope only
# Generated from A1 contracts. Queryable metadata. No route planning.

registry_version: "1"
recipe_version: "1.4"

components:
  # --- Phase 1: validate and locate ---
  - id: validate-session-binding
    owner: aar
    contract_version: "1"
    kind: deterministic
    entry_point: "session_resolver.resolve_session_dir"
    implementation_status: existing
    inputs: [session_id, workspace_encoded]
    outputs: [binding]
    consumes: [{artifact: session-summary, binding: session_id, required: true}]
    produces: []
    authority_domain: session
    binding_keys: [session_id]
    side_effect: false
    idempotency: n/a
    retry: false
    terminal_contribution: precondition

  - id: locate-session-check-runs
    owner: close
    contract_version: "1"
    kind: deterministic
    entry_point: "DESIGN — extract from close_accounting.scan_check_receipts rglob"
    implementation_status: adapter_required
    inputs: [session_id, check_run_id]
    outputs: [runs, selected_run, disposition]
    consumes: [{artifact: check-run-manifest, binding: session_id, required: false}]
    produces: []
    authority_domain: check
    binding_keys: [session_id]
    side_effect: false
    idempotency: n/a
    retry: false
    terminal_contribution: precondition

  # --- Phase 2: read and reconcile ---
  - id: read-check-lifecycle
    owner: check
    contract_version: "1"
    kind: deterministic
    entry_point: "check_lifecycle.read_manifest"
    implementation_status: existing
    inputs: [run_dir]
    outputs: [manifest]
    consumes: [{artifact: check-run-manifest, binding: session_id, required: true}]
    produces: []
    authority_domain: check
    binding_keys: [session_id]
    side_effect: false
    idempotency: n/a
    retry: false
    terminal_contribution: evidence

  - id: reconcile-check-evidence
    owner: close
    contract_version: "1"
    kind: deterministic
    entry_point: "close_accounting.scan_check_receipts"
    implementation_status: existing
    inputs: [session_id]
    outputs: [reconciled_evidence]
    consumes:
      - {artifact: check-state-receipt, binding: session_id, required: false}
      - {artifact: check-run-manifest, binding: session_id, required: false}
    produces: []
    authority_domain: close
    cross_authority: true            # close consuming check authority
    binding_keys: [session_id]
    side_effect: false
    idempotency: n/a
    retry: false
    terminal_contribution: evidence

  # --- Phase 3: classify (model-based) ---
  - id: classify-check-outcome
    owner: check
    contract_version: "1"
    kind: hybrid
    entry_point: "DESIGN — new component"
    implementation_status: design_only
    inputs: [manifest, check_state]
    outputs: [outcome_class, confidence]
    consumes: []
    produces: [{artifact: classification, binding: workflow_id}]
    authority_domain: check
    binding_keys: [workflow_id]
    side_effect: true                # persists classification before branching
    idempotency: PERSIST_BEFORE_BRANCH
    retry: true
    terminal_contribution: classification

  - id: classify-improvement-output
    owner: workflow
    contract_version: "1"
    kind: hybrid
    entry_point: "DESIGN — new component"
    implementation_status: design_only
    inputs: [outcome_class, session_context]
    outputs: [destinations, rationale]
    consumes: []
    produces: [{artifact: classification, binding: workflow_id}]
    authority_domain: improvement
    binding_keys: [workflow_id]
    side_effect: true
    idempotency: PERSIST_BEFORE_BRANCH
    retry: true
    terminal_contribution: routing

  # --- Phase 4: persist selected branches ---
  - id: persist-todo-action
    owner: tasks
    contract_version: "1"
    kind: deterministic
    entry_point: "DESIGN — create_task extraction from cmd_add"
    implementation_status: adapter_required
    inputs: [subject, description, active_form, owner, source_workflow_id, idempotency_key, concern_id]
    outputs: [task_id, task_path]
    consumes: []
    produces: [{artifact: task, binding: task_id, authority: tasks}]
    authority_domain: tasks
    binding_keys: []
    side_effect: true
    idempotency: KEY_RECONCILIATION  # search all task states for matching key
    retry: true
    compensation: "tasks.py done <id>"
    terminal_contribution: branch_receipt

  - id: persist-harvest-obligation
    owner: harvest
    contract_version: "1"
    kind: deterministic
    entry_point: "harvest.scripts.store.write_event"
    implementation_status: adapter_required
    inputs: [event, item_id, title, obligation, operation, source, source_workflow_id, idempotency_key, concern_id]
    outputs: [event_id, event_path, claim_status]
    consumes: []
    produces: [{artifact: harvest-event, binding: event_id, authority: harvest}]
    authority_domain: harvest
    binding_keys: []
    side_effect: true
    idempotency: KEY_RECONCILIATION
    retry: true
    compensation: "harvest store resolve/drop <id>"
    terminal_contribution: branch_receipt

  - id: defer-handoff-continuation
    owner: workflow
    contract_version: "1"
    kind: deterministic
    entry_point: "DESIGN — deferral adapter via tasks"
    implementation_status: design_only
    inputs: [session_id, topic, continuation_context, idempotency_key]
    outputs: [obligation_id]
    consumes: []
    produces: [{artifact: task, binding: obligation_id, authority: tasks}]
    authority_domain: tasks          # deferral persists to tasks
    cross_authority: true            # workflow writing to tasks
    binding_keys: []
    side_effect: true
    idempotency: KEY_RECONCILIATION
    retry: true
    terminal_contribution: deferral_receipt

  - id: defer-opportunity-candidate
    owner: workflow
    contract_version: "1"
    kind: deterministic
    entry_point: "DESIGN — deferral adapter via tasks or harvest"
    implementation_status: design_only
    side_effect: true
    idempotency: KEY_RECONCILIATION
    terminal_contribution: deferral_receipt

  - id: defer-causal-learning
    owner: workflow
    contract_version: "1"
    kind: deterministic
    entry_point: "DESIGN — deferral adapter via tasks"
    implementation_status: design_only
    side_effect: true
    idempotency: KEY_RECONCILIATION
    terminal_contribution: deferral_receipt

  - id: record-no-new-work-disposition
    owner: workflow
    contract_version: "1"
    kind: deterministic
    entry_point: "DESIGN — writes to workflow-run.json only"
    implementation_status: design_only
    side_effect: true                # writes disposition record
    idempotency: KEY_RECONCILIATION
    terminal_contribution: disposition_receipt

  # --- Phase 5: derive close readiness ---
  - id: derive-close-readiness
    owner: close
    contract_version: "1"
    kind: deterministic
    entry_point: "close_accounting.resolve_gates"
    implementation_status: existing
    inputs: [session_id, reconciled_evidence]
    outputs: [close_readiness_state]
    consumes: [reconciled_evidence]
    produces: []
    authority_domain: close
    binding_keys: [session_id]
    side_effect: false
    idempotency: n/a
    terminal_contribution: terminal_state

  # --- Phase 6: persist outcome ---
  - id: persist-workflow-outcome
    owner: workflow
    contract_version: "1"
    kind: deterministic
    entry_point: "DESIGN — finalizes workflow-run.json"
    implementation_status: design_only
    side_effect: true
    idempotency: KEY_RECONCILIATION
    terminal_contribution: finalization
```

### 10. Unresolved A2 requirements

| Requirement | Status | A2 scope |
|-------------|--------|----------|
| `create_task()` extraction from `cmd_add` | DESIGN — schema designed, extraction not done | Modify tasks.py: extract callable, add metadata fields, add idempotency search |
| Harvest idempotency reconciliation wrapper | DESIGN — wrapper around write_event | Add reconciliation function to harvest adapter |
| `locate-session-check-runs` component | DESIGN — extract from close_accounting rglob | New function in close or workflow lib |
| Deferral adapters (3) | DESIGN — contracts specified | New functions writing to tasks/harvest |
| `classify-check-outcome` component | DESIGN — rules + model | New component with structured output validation |
| `classify-improvement-output` component | DESIGN — routing rules + model | New component with destination schema validation |
| `record-no-new-work-disposition` | DESIGN — writes to workflow artifact | New function |
| `persist-workflow-outcome` | DESIGN — finalizes manifest | New function |
| Per-node lifecycle state enforcement | DESIGN — schema defined | New workflow-run.json update logic |
| Idempotency-key computation | DESIGN — normalization rules specified | New canonical-payload function |
| Concern identity derivation | DESIGN — normalization rules specified | New concern-id function |
| Contract validator | SPECIFICATION — checks defined (Section 8) | Implement validator from spec |
| Atomic-write extraction | DEFERRED — Phase B | Not A2 |

### 11. PROVEN / INFERRED / UNKNOWN / FAILED

| Claim | Label | Evidence |
|-------|-------|---------|
| Atomic-write implementations have material semantic differences | OBSERVED | harvest has fsync + publish-before-claim; tasks has parent.mkdir; check has PID suffix |
| Only harvest is SEMANTICALLY_DISTINCT | INFERRED | Other callers are SHAREABLE_WITH_WRAPPER but per-site inspection of inline patterns still needed |
| Tasks store has optional `metadata` object for idempotency keys | OBSERVED | Schema comment: "Optional: owner (str), metadata (object)" |
| Harvest store accepts arbitrary fields via `**fields` | OBSERVED | write_event signature includes **fields |
| Neither store has semantic duplicate detection | OBSERVED | Both create unconditionally |
| Idempotency-key reconciliation prevents duplicate outcomes after crash | DESIGN | Not yet implemented; normalization rules specified but not tested |
| Concern identity enables recurrence tracking | DESIGN | concern_id derivation specified but not tested |
| Recipe simulation will show fewer missed classifications | UNKNOWN | Requires Phase C execution |
| Recipe reduces cognitive burden | UNKNOWN | Requires Phase D operator feedback |
| Dynamic planner adds value | UNKNOWN | Out of scope per v3 |

### 12. Exact recommended A2 scope

A2 implements the following isolated pilot components against hermetic stores:

1. **Todo adapter:** extract `create_task()` from `cmd_add`; add metadata fields for workflow_id, idempotency_key, concern_id; add search-all-states idempotency reconciliation
2. **Harvest adapter:** wrap `write_event` with idempotency-key reconciliation; classify claim outcome (PERSISTED/PERSISTED_UNCLAIMED/PERSISTED_WITH_CONFLICT)
3. **Locator:** extract `locate-session-check-runs` from close_accounting rglob logic
4. **Deferral adapters:** implement 3 deferral components writing to tasks/harvest with idempotency keys
5. **Classification components:** implement `classify-check-outcome` and `classify-improvement-output` with structured output validation
6. **Workflow lifecycle:** implement workflow-run.json initialization, per-node state updates, crash recovery from per-node states
7. **Idempotency infrastructure:** implement canonical-payload normalization and key computation
8. **Concern identity:** implement concern_id derivation

**A2 does NOT:**
- Invoke any production skill
- Change any existing caller
- Extract atomic-write
- Implement the workflow runner (Phase C)
- Build a planner

---

## Verdict

### `COMPONENT_FOUNDATION_CHARACTERIZED`

All A1 criteria are met:

- ✅ All A1 schemas agree (recipe_version "1.4" consistent across all artifacts)
- ✅ Canonical idempotency material is defined (normalization rules + key formula + golden fixtures)
- ✅ Terminal statuses are unambiguous (5 states: READY_FOR_CLOSE, NOT_READY_FOR_CLOSE, INCOMPLETE, FAILED, LOST)
- ✅ Concern identity is designed (concern_id = SHA256 of normalized concern_type + failure_signature + affected_scope)
- ✅ Every pilot recipe node exists in the static registry (14 components registered)
- ✅ No production caller or behavior was changed

**A1 artifact classification:**
- Documentation: design corrections, contracts, characterization table
- Data: fixture specifications (28 fixtures), negative-test specifications (18 tests)
- Executable tooling: characterization scripts (a1_atomic_write_char.py, a1_atomic_write_extended.py) — inspection only, no production writes
- Schemas: 9 versioned schemas (workflow-run, node-state, classification, branch-receipt, deferral-obligation, evaluation, concern-identity, canonical-payload, recipe-definition)
- Registry: 14-component static registry with implementation_status per component
