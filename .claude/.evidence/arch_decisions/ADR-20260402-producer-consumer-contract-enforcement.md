# ADR-20260402: Producer/Consumer Contract Enforcement Architecture

**Date:** 2026-04-02
**Status:** Accepted
**Type:** Architecture Decision
**Decider:** Bruce Thomson

---

## Context

The codebase lacks a unified mechanism to enforce that **producers** emit artifacts matching **consumer** expectations, with both-side proof. Existing partial solutions exist:

| Component | Exists | Gap |
|-----------|--------|-----|
| `/handoff` V2 envelope validation | Yes | Schema version + state machine, but no contract field validation |
| `/skill-guard` breadcrumb enforcement | Yes | Enforces breadcrumb step completion only — NOT cross-skill contracts |
| SKILL.md `contract_boundary_check` steps | Partial | /planning blocks on missing Contract Authority Packet (readiness gate); /code, /verify, /sqa advisory in Phase 1 |
| `skill-routing-and-contract-policy.md` | Yes | Defines 8 mandatory contract fields but no enforcement engine |
| `/contract-primitives` package | **No** | Gap — no shared primitives for validation |
| Cross-boundary producer/consumer proof | **No** | Gap — no both-side validation |

---

## Decision

**Three-layer enforcement architecture** with thin routing hooks, skill-owned validators, and a shared `contract-primitives` package:

```
Layer 0: PreToolUse Router (blocking, Phase 3)
  └── Activation trigger: tool use targets a skill boundary (handoff dispatch, skill invocation, or cross-boundary artifact read/write)
  └── Non-activation criteria: tool use is intra-skill, read-only, or purely conversational (no boundary crossing)
  └── Ambiguous classification behavior: default to BLOCK with "unclassified" error, require explicit routing rules
  └── Routing failure behavior: BLOCK if no validator handles the boundary type; do not fall back silently
  └── Routes to skill validators

Layer 1: Skill Validators (blocking, after Phase 2)
  ├── /planning: contract_boundary_check step → BLOCKING (Phase 2)
  ├── /code: producer/consumer trace gate → BLOCKING (Phase 2)
  ├── /verify: Tier 4 contract check → BLOCKING (Phase 2)
  ├── /sqa: Layer 7 validator existence check → BLOCKING (Phase 2)
  └── /handoff: validate_envelope() already exists (current state)

Layer 2: contract-primitives Package (shared)
  └── Schema definitions, validation helpers, event logging
```

### What Belongs in `skill-guard` vs Outside

| Capability | Belongs in skill-guard | Belongs Outside |
|------------|----------------------|-----------------|
| Breadcrumb workflow step completion (MINIMAL/STANDARD/STRICT) | ✅ Yes | |
| `enforcement: strict/advisory/none` tier validation | ✅ Yes | |
| Cross-skill contract field validation | | ❌ No — skill-owned |
| `enforcement: blocking` value (Phase 3) | | ❌ No — architecture owns |
| Handoff V2 envelope validation | | ❌ No — /handoff owns |
| Evidence schema validation | | ❌ No — /verify owns |
| Plan artifact contract checks | | ❌ No — /planning owns |
| Hook output schema validation | | ❌ No — hook owns its output |

**Rationale:** `skill-guard` scope is correctly bounded to breadcrumb enforcement. Expanding it to cross-skill contracts would create a second-rate validation system living alongside first-rate skill-specific validators. The 8 contract fields require semantic understanding of each skill's domain, which `skill-guard` does not and should not have.

**Note on `enforcement: blocking`:** The current `skill_guard` validates `enforcement: strict/advisory/none` as a frontmatter field (returning warnings for invalid values) but does not read these values to trigger blocking. `enforcement: blocking` is a **net-new value added by this ADR** and lives in the Phase 3 `PreToolUse_contract_router` (architecture layer), not in `skill_guard`. Phase 2 frontmatter changes (`advisory → blocking`) are necessary preconditions but are not sufficient alone — Phase 3 must wire `enforcement: blocking` into the dispatch chain for actual blocking to occur.

---

## Boundary/Ownership Matrix

| Boundary | Producer | Consumer | Input Schema | Output Schema | Required Fields | Freshness Authority | Invalidation Trigger | Failure Behavior |
|----------|----------|----------|--------------|---------------|-----------------|--------------------|-----------------------|------------------|
| **Handoff** | Any skill emitting handoff envelope | /handoff restoring or routing | `transcript_path`, `session_id`, `goal`, `current_task`, `active_files` | `HandoffEnvelopeV2` | `transcript_path`, `session_id`, `goal`, `current_task`, `schema_version`, `snapshot_id`, `terminal_id`, `source_session_id`, `status` | Transcript path (source of truth) | New envelope emitted | Envelope rejected, gap flagged |
| **Evidence** | Any skill producing evidence | /verify, /sqa consuming | `Finding` dataclass | Evidence store | `finding_id`, `severity`, `layer`, `evidence_tier` | Evidence store | New evidence supersedes | Test gap flagged |
| **Plan** | /planning writing plan | /code, /verify reading | Plan artifact schema | Plan artifact | `goals`, `tasks`, `acceptance_criteria` | Plan file | New plan version | Blocker for /code, /verify |
| **Hook** | Hook emitting output | Claude Code consuming | Hook output schema | Hook output | `decision`, `reason` | Hook output | New output emitted | Action blocked or warned |
| **Subagent Dispatch** | Parent dispatching subagent | Subagent executing | Subagent task schema | Subagent task | `task`, `agent_type` | Parent context | Task completion | Fallback or escalation |
| **Subagent Result** | Subagent returning result | Parent receiving result | Subagent result schema | Subagent result | `result`, `status`, `artifacts` | Subagent result artifact | New result for same task_id | Treat as untrusted; parent retries or escalates |
| **Breadcrumb** | Skill reporting step | skill-guard tracking | `step`, `status`, `enforcement_level` | Breadcrumb trail | `skill_name`, `step`, `status` | Breadcrumb trail | Step marked complete | Enforcement level applied |

---

## Freshness and Stale-Data Enforcement

**Stale-data immunity** is preserved by design:
1. **Handoff V2:** `transcript_path` is authoritative — transcript is never stale
2. **Evidence:** Supersedes rule — newer evidence replaces older
3. **Plans:** Plan file is authoritative — in-memory state is reconstructed from file
4. **Hook output:** Each hook event is point-in-time — no stale accumulation

**What does NOT change under this architecture:**
- Multi-terminal isolation (each terminal has isolated state files)
- Compact/resume immunity (transcript_path links ensure continuity)
- Breadcrumb enforcement (already works, unchanged)

---

## Evidence Event Strategy

Four event types for observability:

| Event | When | Payload |
|-------|------|---------|
| `contract_produced` | Producer emits valid contract | `{boundary, producer, schema_version, fields_validated}` |
| `contract_consumed` | Consumer successfully validates | `{boundary, consumer, schema_version, validation_time_ms}` |
| `contract_rejected` | Consumer rejects due to missing/invalid fields | `{boundary, consumer, missing_fields, rejection_reason}` |
| `contract_proof` | Both-side proof established | `{boundary, producer, consumer, proof_schema}` |

Events logged to `P:/.claude/state/contract_events_{terminal_id}.jsonl` (terminal-scoped, no cross-terminal bleed).

---

## Failure Modes

| Mode | Detection | Response | Severity |
|------|----------|----------|----------|
| Missing required field | Layer 1 validator | BLOCK with field name (see Contract Authority Packet for per-boundary required_fields) | HIGH |
| Schema version mismatch | Layer 1 validator | BLOCK with version info | HIGH |
| Invalid state transition | /handoff validate_envelope() | BLOCK with valid transitions | CRITICAL |
| Producer emits, no consumer | Meta-synthesis (Layer M) | WARN with gap report | MEDIUM |
| Consumer expects, no producer | Meta-synthesis (Layer M) | WARN with gap report | MEDIUM |
| Stale artifact used (any boundary) | Layer 1 validator (freshness check) | BLOCK with invalidation trigger — implements conflict_semantics stale_artifact rule (line 342) | HIGH |
| Validation timeout | Layer 1 validator | BLOCK (degraded path not safe — timeout means validator cannot confirm contract, so boundary is treated as unvalidated; caller retries or surfaces gap) | HIGH |
| Evidence gap (no finding for claim) | /verify Tier 2 | ADVISORY warning with gap report | MEDIUM |
| Subagent result schema mismatch | Parent skill (dispatcher) | Fallback or escalate to parent | MEDIUM |
| Hook output schema invalid | Hook itself | Action blocked or warned per hook configuration | HIGH |

---

## Implementation Phases

### Phase 1: contract-primitives Package (New Package)
**Owner:** /architecture  
**Files:** `P:/packages/contract-primitives/src/contract_primitives/__init__.py`, `schemas.py`, `validators.py`, `events.py`  
**Exit Criteria:** Package exists, exports `validate_contract()`, `ContractSchema`, `ContractEvent`, `BOUNDARIES` enum

### Phase 2: Skill Validator Integration (Blocking Workflow Steps)
**Owner:** /planning, /code, /verify, /sqa
**Precondition:** This phase cannot begin until Phase 1 contract-primitives package exists. Phase 3 must wire `enforcement: blocking` into the dispatch chain — frontmatter changes alone are necessary but not sufficient.
**Required Frontmatter Changes (precondition for blocking behavior):**
- `/planning` SKILL.md frontmatter: `enforcement: advisory` → `enforcement: blocking`
- `/code` SKILL.md frontmatter: `enforcement: advisory` → `enforcement: blocking`
- `/verify` SKILL.md frontmatter: add `enforcement: blocking` for Tier 4 contract-sensitive targets
- `/sqa` SKILL.md frontmatter: `enforcement: none` → `enforcement: blocking` for Layer 7 contract-sensitive boundaries
- `/handoff` SKILL.md frontmatter: add `enforcement: blocking` for validate_envelope() (already exists at runtime)
**Changes:**
- `/planning`: `contract_boundary_check` step becomes BLOCKING — blocks plans with missing CAP consumption, implied boundaries, or missing artifact schemas (scope expansion, not purely a severity change)
- `/code`: `consumer_contract_precheck` step becomes BLOCKING; `producer_consumer_trace_verification` step becomes BLOCKING
- `/verify`: `run_contract_integrity_check` (Tier 4) becomes BLOCKING for contract-sensitive targets
- `/sqa`: Layer 7 adds blocking `contract_boundary_check` for contract-sensitive boundaries (validators must exist and produce passing results)
**Exit Criteria:** All four skills declare `enforcement: blocking` in frontmatter. "Blocking" behavior requires Phase 3 router wiring — Phase 2 frontmatter changes are the signal, Phase 3 hook is the enforcement mechanism.

### Phase 3: Global Gate Hook (Thin Router)
**Owner:** /architecture  
**File:** New PreToolUse hook `PreToolUse_contract_router.py`  
**Exit Criteria:** Hook routes to skill validators without duplicating validation logic

### Phase 4: Meta-Synthesis Layer (Consensus Detection)
**Owner:** /sqa  
**Changes:** Layer M implements consensus and blind-spot detection  
**Exit Criteria:** 2-layer consensus correctly identified, blind spots flagged

### Phase 5: Evidence Events and Observability
**Owner:** /architecture  
**Changes:** Event logging to `contract_events_{terminal_id}.jsonl`  
**Exit Criteria:** Events visible in diagnostics, no cross-terminal bleed

---

## Rejected Alternatives

| Alternative | Reason Rejected |
|-------------|-----------------|
| **Giant global hook** | Duplicates skill-specific validation, creates second-rate contract system, violates single-responsibility |
| **skill-guard absorbs all validation** | Wrong abstraction level — breadcrumb enforcement is workflow-level, not contract-level |
| **Documentation only** | Policy exists (`skill-routing-and-contract-policy.md`) but no enforcement — gap remains |

---

## Contract Authority Packet

```yaml
contract_authority_packet:
  packet_version: "1"
  contract_sensitive: true
  packet_date: "2026-04-02"
  authority:
    closure_source: "contract_authority_packet"
    prose_role: "explanatory_only"

boundaries:
  - boundary_id: "handoff-envelope"
    producer: "Any skill emitting handoff envelope"
    consumer: "/handoff (restore or route)"
    schema:
      id: "handoff-envelope"
      version: "2"
    required_fields:
      - transcript_path
      - session_id
      - goal
      - current_task
      - schema_version
      - snapshot_id
      - terminal_id
      - source_session_id
      - status
    optional_fields:
      - active_files
      - resume_snapshot
      - lifecycle_phase
    freshness_authority: "transcript_path (source of truth)"
    invalidation_trigger: "New envelope emitted for same session_id"
    precedence_rule: "transcript_path beats stale envelope summary"
    failure_behavior: "reject envelope, surface gap via HandoffValidationError"
    validator_owner: "/handoff (validate_envelope at handoff_v2.py:147)"
    proof_owner: "/verify --contracts (Tier 3 e2e + run_contract_integrity_check step)"
    downstream_consumers: ["/planning", "/code", "/verify", "/sqa"]

  - boundary_id: "evidence-artifact"
    producer: "Any skill producing Finding dataclass"
    consumer: "/verify, /sqa"
    schema:
      id: "evidence-finding"
      version: "1"
    required_fields:
      - finding_id
      - severity
      - layer
      - evidence_tier
    optional_fields:
      - title
      - description
      - location
      - consensus
      - category
    freshness_authority: "Evidence store (latest supersedes)"
    invalidation_trigger: "New evidence with same finding_id supersedes"
    precedence_rule: "Latest evidence by timestamp wins"
    failure_behavior: "Missing required fields → BLOCK with missing field name (HIGH); Evidence gap (no finding for claim) → advisory warning (MEDIUM)"
    validator_owner: "/verify (Tier 2 integration check)"
    proof_owner: "/sqa (Layer 7 validator existence)"
    downstream_consumers: ["/verify", "/sqa"]

  - boundary_id: "plan-artifact"
    producer: "/planning (write plan)"
    consumer: "/code, /verify (read plan)"
    schema:
      id: "plan-artifact"
      version: "1"
    required_fields:
      - goals
      - tasks
      - acceptance_criteria
    optional_fields:
      - context
      - constraints
      - dependencies
    freshness_authority: "Plan file (in-memory state reconstructed from file)"
    invalidation_trigger: "New plan version written by /planning"
    precedence_rule: "Plan file beats in-memory state"
    failure_behavior: "Blocker for /code and /verify; advisory warning in /planning"
    validator_owner: "/planning (contract_boundary_check step → BLOCKING in Phase 2)"
    proof_owner: "/verify --contracts (Tier 3 e2e + run_contract_integrity_check step)"
    downstream_consumers: ["/code", "/verify"]

  - boundary_id: "hook-output"
    producer: "Hook emitting output"
    consumer: "Claude Code (tool execution engine)"
    schema:
      id: "hook-output"
      version: "1"
    required_fields:
      - decision
      - reason
    optional_fields:
      - blocking_hook
      - additional_context
    freshness_authority: "Hook output (point-in-time, no stale accumulation)"
    invalidation_trigger: "New hook event fires"
    precedence_rule: "Latest hook output wins per event"
    failure_behavior: "Action blocked (block) or warned (advisory)"
    validator_owner: "Hook itself (validate_hook_output at hook_schema.py)"
    proof_owner: "/verify --contracts (Tier 3 e2e + run_contract_integrity_check step)"
    downstream_consumers: ["Claude Code tool execution engine"]

  - boundary_id: "breadcrumb-trail"
    producer: "Skill reporting workflow step"
    consumer: "skill-guard (breadcrumb tracker)"
    schema:
      id: "breadcrumb-trail"
      version: "1"
    required_fields:
      - skill_name
      - step
      - status
      - enforcement_level
    optional_fields:
      - timestamp
      - terminal_id
    freshness_authority: "Breadcrumb trail file"
    invalidation_trigger: "Step marked complete"
    precedence_rule: "Trail file is authoritative"
    failure_behavior: "Enforcement level applied per MINIMAL/STANDARD/STRICT"
    validator_owner: "skill-guard (breadcrumb/enforcement.py)"
    proof_owner: "/verify (Tier 2 integration check)"
    downstream_consumers: ["skill-guard", "/verify"]

  - boundary_id: "subagent-dispatch"
    producer: "Parent dispatching subagent"
    consumer: "Subagent executing task"
    schema:
      id: "subagent-task"
      version: "1"
    required_fields:
      - task
      - agent_type
    optional_fields:
      - context
      - constraints
    freshness_authority: "Parent context"
    invalidation_trigger: "Task completion or timeout"
    precedence_rule: "Parent context wins on conflict"
    failure_behavior: "Fallback or escalation to parent"
    validator_owner: "Parent skill (dispatcher validates dispatch schema completeness before sending)"
    proof_owner: "/verify (Tier 2 integration check)"
    downstream_consumers: ["Parent skill", "/sqa (Layer 7)"]

  - boundary_id: "subagent-result"
    producer: "Subagent returning result"
    consumer: "Parent receiving result"
    schema:
      id: "subagent-result"
      version: "1"
    required_fields:
      - result
      - status
      - artifacts
    optional_fields:
      - error
      - logs
    freshness_authority: "Subagent result artifact"
    invalidation_trigger: "New result artifact emitted for same task_id"
    precedence_rule: "Latest result wins"
    failure_behavior: "Treat result as untrusted; parent retries, surfaces gap, or escalates"
    validator_owner: "Parent skill (validates result schema completeness and signatures before accepting)"
    proof_owner: "/verify (Tier 2 integration check; Tier 3 e2e for cross-boundary result artifacts)"
    downstream_consumers: ["Parent skill", "/sqa (Layer 7)"]

conflict_semantics:
  transcript_vs_artifact: "transcript_path beats stale envelope summary"
  schema_mismatch: "BLOCK with version info (HIGH severity)"
  validator_timeout: "BLOCK (degraded path not safe — timeout means validator cannot confirm contract, so boundary is treated as unvalidated; caller retries or surfaces gap)"
  stale_artifact: "BLOCK with invalidation trigger (HIGH severity)"
```

---

## Evidence

- `P:/packages/skill-guard/src/skill_guard/breadcrumb/enforcement.py` — Verified: `verify_with enforcement()` and `get_enforcement_level()` implement breadcrumb step enforcement only (MINIMAL/STANDARD/STRICT), NOT cross-skill contracts
- `P:/packages/handoff/scripts/hooks/__lib/handoff_v2.py:18` — Verified: `SCHEMA_VERSION = 2`
- `P:/packages/handoff/scripts/hooks/__lib/handoff_v2.py:147` — Verified: `validate_envelope()` validates schema_version match at line 192, calls `_require_fields()` for required envelope fields
- `P:/packages/handoff/scripts/hooks/__lib/hook_schema.py` — Verified: `DECISION_APPROVE = "approve"`, `DECISION_BLOCK = "block"`, `validate_hook_output()`
- `P:/.claude/policies/skill-routing-and-contract-policy.md` — Verified: 8 mandatory contract fields defined at lines 21-30 (input schema, output schema, producer responsibility, consumer validation, source of truth, freshness/invalidation rule, isolation boundary, contract-to-test binding)
- `P:/__csf/arch_decisions/` — Verified: directory exists with existing ADR files
- `P:/packages/skill-guard/src/skill_guard/__init__.py` — Verified: exports `discover_all_skills`, `get_skill_config`, `verify_with_enforcement`, `get_enforcement_level`
- Skills at `P:/.claude/skills/` — Verified via grep: `/planning` has `contract_boundary_check` (workflow_steps line 27); `/code` has `consumer_contract_precheck` (line 37) and `producer_consumer_trace_verification` (line 46); `/verify` has `run_contract_integrity_check` (tier-workflow line 43); `/sqa` Layer 7 checks validator existence only — none are blocking by default
