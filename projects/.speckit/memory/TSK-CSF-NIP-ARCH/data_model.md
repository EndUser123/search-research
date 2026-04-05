# Data Model: CSF NIP Anti‑Deception Unified Architecture

## Entity Definitions

### SystemConfig

- **Description:** Central configuration and path management for CSF NIP.
- **Key fields:**
  - `project_root`: filesystem path.
  - `paths.evidence`, `paths.logs`, `paths.cache`, `paths.config`, `paths.src`, `paths.lib`, `paths.modules`.
  - Config values (nested dict) loaded from `settings.json`.

### FeatureToggle

- **Description:** Run‑time feature toggles (strict mode, blocking modes, performance, etc.).
- **Key fields:**
  - `name`: toggle name (e.g. `CSF_STRICT_MODE`).
  - `enabled`: boolean.
  - `source`: environment variable, config file, etc.

### HookExecution

- **Description:** A single execution of a hook at one of the five layers.
- **Key fields:**
  - `id`: unique ID.
  - `session_id`: logical session identifier.
  - `layer`: enum (L0–L4).
  - `hook_name`: e.g. `pre_tool_use`.
  - `timestamp`: execution time.
  - `input_summary`: minimal structured description of input.
  - `output_summary`: minimal structured description of output.
  - `status`: success, warning, error.

### LayerDecision

- **Description:** A decision made by a specific layer about whether to allow, warn, or block an operation.
- **Key fields:**
  - `id`: unique decision ID.
  - `hook_execution_id`: FK to `HookExecution`.
  - `decision_type`: allow | warn | block | refuse.
  - `reason`: human‑readable.
  - `severity`: info | warning | error | critical.
  - `violations`: optional structured list of violated rules.
  - `vre_refs`: list of VRE principle IDs applied.
  - `csf_nip_refs`: list of CSF NIP clauses.

### ValidationContext

- **Description:** Per‑request context shared logically across layers.
- **Key fields:**
  - `context_id`: unique ID.
  - `session_id`, `request_id`.
  - `user_intent`: classification (e.g. “edit code”, “run tests”, “refactor architecture”).
  - `target_files`: list of file paths.
  - `tools_requested`: list of tool names.
  - `security_flags`: booleans (e.g. `security_sensitive`, `data_destructive`).

### UnifiedConfidenceScore

- **Description:** Aggregated confidence across layers for a given decision.
- **Key fields:**
  - `id`.
  - `rule_confidence`: 0–1 (L2).
  - `quality_confidence`: 0–1 (L3).
  - `semantic_confidence`: 0–1 (L4).
  - `context_confidence`: 0–1 (L1).
  - `overall_confidence`: computed 0–1 (weighted).

### UnifiedRiskAssessment

- **Description:** Consolidated risk signal across layers.
- **Key fields:**
  - `id`.
  - `security_risk`: 0–1.
  - `tdd_risk`: 0–1.
  - `quality_risk`: 0–1.
  - `deception_risk`: 0–1.
  - `overall_risk`: 0–1 (weighted).
  - `risk_category`: enum (CRITICAL, HIGH, MEDIUM, LOW).
  - `should_block`, `should_warn`, `should_suggest`: booleans.

### UnifiedDecision

- **Description:** Final outcome for an operation from the system’s perspective.
- **Key fields:**
  - `id`.
  - `context_id`: FK to `ValidationContext`.
  - `allowed`: boolean.
  - `severity`: info | warning | error | critical.
  - `confidence_id`: FK to `UnifiedConfidenceScore`.
  - `risk_id`: FK to `UnifiedRiskAssessment`.
  - `primary_evidence_id`: FK to `UnifiedEvidence`.
  - `reasons`: list of human‑readable messages.

### EvidenceRecord (Layer-Specific)

- **Description:** Raw evidence at each layer (existing DB rows/logs).
- **Types:**
  - `TddEvidenceRecord` – row in `tdd_enforcement_evidence`.
  - `OverrideRecord` – row in OverrideTracker DB.
  - `ValidationEvidenceRecord` – PostToolUse validation record.
  - `SupervisorEvidenceRecord` – LLM supervisor evidence entry.
- **Common fields:**
  - `id`, `session_id`, `timestamp`.
  - `layer`, `hook_name`.
  - `payload`: JSON with layer‑specific fields.

### UnifiedEvidence

- **Description:** Correlated evidence across layers for a given decision.
- **Key fields:**
  - `id`.
  - `context_id`: FK to `ValidationContext`.
  - `tdd_evidence_ids`: list of `TddEvidenceRecord.id`.
  - `override_ids`: list of `OverrideRecord.id`.
  - `validation_evidence_ids`: list of PostToolUse evidence IDs.
  - `supervisor_evidence_ids`: list of LLM supervisor evidence IDs.
  - `decision_chain`: ordered list of `LayerDecision.id`.

### MetricSnapshot

- **Description:** A snapshot of system metrics as produced by `system_metrics.py`.
- **Key fields:**
  - `id`.
  - `timestamp`.
  - `system_health.score`.
  - `system_health.component_scores` (hook success, security effectiveness, TDD compliance, evidence completeness, performance SLOs).
  - Performance details (latency quantiles, cache hit rate, etc.).
  - Security metrics (blocked threats, pattern coverage).

### RegisteredFunction

- **Description:** An entry in the Library‑First function registry.
- **Key fields:**
  - `name`.
  - `category` (e.g. `data-parsing`, `evidence-utils`, `path-handling`).
  - `signature`.
  - `description`.
  - `module`, `file_path`.
  - `tags`: list (e.g. `pure`, `idempotent`, `side_effect_free`).

### GovernanceRule

- **Description:** Canonical reference to a governance clause (CLAUDE.md, constitution.md, or VRE principle).
- **Key fields:**
  - `id`: stable identifier (e.g. `CLAUDE-SEC-3`, `VRE-REFUSAL-2`).
  - `source`: enum (`claude`, `constitution`, `vre`).
  - `section_ref`: original document section or heading.
  - `summary`: short human-readable description of the rule.

### Cwo12ConfigSnapshot

- **Description:** Snapshot of the CWO12 configuration (from `cwo12.config.json` and environment) used for a validation or execution.
- **Implementation Status:** ✅ COMPLETED - SQLite table with storage helpers implemented in `exec_validation_store.py`.
- **Key fields:**
  - `id`.
  - `task_id`: identifier such as `TSK-CSF-NIP-ARCH`.
  - `artifact_root`: filesystem path to the artifact triplet root.
  - `enforcement_level`: strict | warn | guide | off.
  - `on_multiple_candidates`: strategy used when multiple artifact triplets are found.
  - `allow_force`, `auto_generate_missing`: booleans summarizing key enforcement toggles.
  - `risk_tiers`: JSON summary of risk tier configuration.
  - `hook_requirements`: JSON summary of per-hook requirements.

### ExecValidationRecord

- **Description:** Record of a single CWO12 `/exec` artifact validation and enforcement decision.
- **Implementation Status:** ✅ COMPLETED - SQLite table with storage helpers implemented in `exec_validation_store.py`.
- **Key fields:**
  - `id`.
  - `timestamp`.
  - `task_id`: logical task identifier.
  - `artifact_context_id`: FK to `ArtifactContext`.
  - `config_snapshot_id`: FK to `Cwo12ConfigSnapshot`.
  - `overall_status`: pass | warn | fail | ambiguous.
  - `blocking`: boolean indicating whether execution was blocked.
  - `enforcement_level`: strict | warn | guide | off.
  - `issue_codes`: list of short issue identifiers.
  - `issue_summary`: list of human-readable messages.
  - `artifact_hashes`: JSON map of artifact file paths to content hashes.
  - `override_record_id`: optional FK to a related `OverrideRecord` when the decision is also logged in OverrideTracker.

### RegistryUsageRecord

- **Description:** Record of how the Library‑First registry was used (or deliberately not used) during a coding decision.
- **Implementation Status:** ✅ COMPLETED - SQLite table with storage helpers implemented in `exec_validation_store.py`.
- **Key fields:**
  - `id`.
  - `session_id`, `request_id`.
  - `timestamp`.
  - `suggested_functions`: list of `RegisteredFunction.name` values that were presented to the model.
  - `selected_function`: optional `RegisteredFunction.name` that was actually used.
  - `ignored_functions`: list of suggested functions that were not used.
  - `justification_if_ignored`: optional free-text explanation for not using a suggested function.
  - `source_hook`: which hook or component emitted this record (e.g. `pre_generation_registry`).
  - `used_registered_function`: boolean flag.

### ArtifactContext

- **Description:** Captures how an artifact triplet (`plan.md`, `tasks.md`, `data_model.md`) was discovered and selected for a given `/exec` invocation.
- **Implementation Status:** ✅ COMPLETED - SQLite table with storage helpers implemented in `exec_validation_store.py`.
- **Key fields:**
  - `id`.
  - `selected_root`: filesystem path to the chosen artifact triplet root.
  - `plan_path`, `tasks_path`, `data_model_path`: resolved paths.
  - `inference_method`: enum (e.g. `context_inference`, `explicit`, `user_selected`).
  - `user_confirmation_obtained`: boolean indicating whether the user explicitly confirmed the selection.
  - `candidate_roots`: list of other candidate roots considered.
  - `raw_command`: the `/exec` command string that triggered discovery.
  - `conversation_summary`: optional short summary of the conversation used for inference.

## Relationships

- **SystemConfig → EvidenceRecord / MetricSnapshot**
  - SystemConfig determines evidence DB paths and metrics output locations.
- **ValidationContext → HookExecution**
  - One `ValidationContext` can be associated with many `HookExecution` entries (for each layer invoked during a request).
- **HookExecution → LayerDecision**
  - Each `HookExecution` can register zero or more `LayerDecision` records (e.g. firewall decision, TDD enforcement decision).
- **LayerDecision → EvidenceRecord**
  - A `LayerDecision` references one or more `EvidenceRecord` IDs that justify its outcome.
- **LayerDecision.vre_refs / csf_nip_refs → GovernanceRule**
  - Each VRE or CSF NIP reference on a `LayerDecision` must resolve to a concrete `GovernanceRule.id` defined in the governance index (for example, `VRE_IMPLEMENTATION_INDEX.md`).
- **UnifiedConfidenceScore / UnifiedRiskAssessment → UnifiedDecision**
  - Each `UnifiedDecision` has exactly one `UnifiedConfidenceScore` and one `UnifiedRiskAssessment`.
- **UnifiedEvidence → EvidenceRecord**
  - `UnifiedEvidence` aggregates multiple `EvidenceRecord` IDs across layers for a single context/decision.
- **UnifiedDecision → UnifiedEvidence**
  - A `UnifiedDecision` points to the primary `UnifiedEvidence` object supporting it.
- **MetricSnapshot → EvidenceRecord / UnifiedDecision**
  - A `MetricSnapshot` is derived from aggregating many `EvidenceRecord` and `UnifiedDecision` items over a time window.
- **RegisteredFunction → UnifiedDecision**
  - Optional: decisions can reference the registered functions they used or consciously ignored.
- **ExecValidationRecord → ArtifactContext / Cwo12ConfigSnapshot / OverrideRecord**
  - An `ExecValidationRecord` references the artifact discovery context, the configuration snapshot used, and optionally a related `OverrideRecord` if the decision is also captured in OverrideTracker.
- **RegistryUsageRecord → RegisteredFunction / UnifiedDecision**
  - `RegistryUsageRecord` references suggested and selected `RegisteredFunction` entries and can be linked into a corresponding `UnifiedDecision` and its `UnifiedEvidence.decision_chain`.
- **ArtifactContext → ExecValidationRecord**
  - One `ArtifactContext` can be associated with many `ExecValidationRecord` entries that reused the same selected triplet.

## CWO12 Validation Rules

### Constitutional Compliance Validation

- **Rule ID**: CWO12_CONST_001
- **Description**: Enforce solo developer constitutional principles
- **Validation**: Verify no background services exist, all monitoring is on-demand
- **Evidence Required**: ExecValidationRecord with constitutional compliance markers
- **Implementation Status**: ✅ ENFORCED - Phase 0 Task 0D completed

### Background Service Elimination

- **Rule ID**: CWO12_CONST_002
- **Description**: Background loops and continuous monitoring are forbidden
- **Validation**: Scan for `while True` loops, background threads, async tasks without developer control
- **Evidence Required**: File scan evidence, compliance markers in source code
- **Implementation Status**: ✅ ELIMINATED - All background monitoring disabled

### On-Demand Execution Requirement

- **Rule ID**: CWO12_CONST_003
- **Description**: All operations must be developer-controlled and immediate (<500ms response)
- **Validation**: Verify functions are callable only when explicitly requested
- **Evidence Required**: Performance metrics, response time measurements
- **Implementation Status**: ✅ IMPLEMENTED - On-demand methods created

### Library-First Enforcement

- **Rule ID**: CWO12_LIB_001
- **Description**: Enforce Library-First registry usage with evidence tracking
- **Validation**: Verify RegistryUsageRecord creation for all library function interactions
- **Evidence Required**: RegistryUsageRecord entries with usage analysis
- **Implementation Status**: ✅ COMPLETED - RegistryUsageRecord system active

### Evidence Tracking Compliance

- **Rule ID**: CWO12_EVID_001
- **Description**: All validation and compliance actions must generate evidence
- **Validation**: Verify evidence database entries for all CWO12 operations
- **Evidence Required**: ExecValidationRecord, ArtifactContext, RegistryUsageRecord entries
- **Implementation Status**: ✅ IMPLEMENTED - Evidence tracking system active

## Data Integrity

- All IDs (`context_id`, `decision_id`, `evidence_id`, etc.) must be **globally unique** and non‑null.
- ID formats SHOULD be collision‑resistant (for example, UUIDv4 strings, or structured IDs that combine a prefix with a timestamp and short hash); collisions must be treated as errors.
- `ValidationContext.session_id` must match the session IDs used in underlying evidence tables.
- For each `UnifiedDecision`:
  - `confidence_id` and `risk_id` must refer to existing, consistent records.
  - `primary_evidence_id` must refer to a `UnifiedEvidence` whose `context_id` matches the decision’s `context_id`.
- Evidence-like records (`EvidenceRecord`, `ExecValidationRecord`, `RegistryUsageRecord`, `MetricSnapshot`):
  - `timestamp` must be in ISO 8601 format and non‑null.
  - `layer` fields (where present) must be one of the defined layer enums (L0–L4).
  - Retention must respect CLI-configured windows (for example, evidence_cleanup retention days); records older than the window are eligible for deletion via cleanup CLIs.
- Metric snapshots:
  - `timestamp` must correspond to the time of metric computation.
  - Component scores must be derivable from underlying evidence (no arbitrary constants).
- Registered functions:
  - `name` + `category` combination must be unique.
  - `file_path` must point to an existing file at registry build time (or be explicitly marked stale).
  - A periodic validation process (manual or automated) SHOULD mark registry entries as stale if their `file_path` no longer exists.
- Governance references:
  - Every value in `LayerDecision.vre_refs` or `csf_nip_refs` must resolve to an existing `GovernanceRule.id`; dangling references are invalid.
  - `GovernanceRule` entries MUST be synchronized with the source-of-truth file (e.g. `docs/VRE_IMPLEMENTATION_INDEX.md`).

## Validation Rules

### Logical invariants

- If `UnifiedDecision.allowed == False`, then:
  - `UnifiedRiskAssessment.overall_risk` must be above a configured threshold for blocking, and/or
  - At least one `LayerDecision` in the `decision_chain` must be `block` with severity `error` or `critical`.
- If `UnifiedDecision.allowed == True` with severity `warning`:
  - `UnifiedRiskAssessment.overall_risk` must be in MEDIUM or LOW, and
  - Any HIGH or CRITICAL risk factors must be mitigated by explicit reasons/suggestions.
- For any `UnifiedDecision` with high `semantic_confidence`:
  - The corresponding `UnifiedEvidence` must show sufficient supervisor evidence; otherwise `semantic_confidence` should be downgraded.
- For any `LayerDecision` that cites a governance rule requiring refusal (e.g. refusal-over-simulation), the resulting `UnifiedDecision` for that operation must not allow the unsafe action.
- Default overall risk thresholds (tunable via configuration) SHOULD be:
  - Block when `UnifiedRiskAssessment.overall_risk` ≥ 0.8.
  - Warn when `UnifiedRiskAssessment.overall_risk` is between 0.4 and 0.8.
  - Treat as informational when `UnifiedRiskAssessment.overall_risk` < 0.4.
- Default confidence aggregation SHOULD weight components (for example: rule=0.3, quality=0.3, semantic=0.3, context=0.1) and clamp `overall_confidence` to the [0.0, 1.0] range.

### Evidence / metrics consistency

- `MetricSnapshot.system_health.component_scores` must be consistent with:
  - Counts and rates derived from recent `UnifiedDecision` and `EvidenceRecord` data.
- Security pattern effectiveness:
  - Cannot be non‑zero unless there is at least one blocked threat recorded in relevant evidence tables.
- Fabrication detection metrics (if tracked):
  - Must be based on deliberate tests or override patterns, not guessed.
- Performance metrics:
  - Latency and SLO-related values (for example, hook execution p95/p99) must be derived from actual timing data, not fixed constants.
  - When configurable SLO thresholds are exceeded, corresponding `UnifiedRiskAssessment` entries should increase performance risk and surface warnings via metrics CLIs or CI checks.

### Registry usage

- When a `UnifiedDecision` corresponds to a coding operation and relevant `RegisteredFunction` entries exist:
  - The decision should either:
    - Reference the registered function used, or
    - Explicitly record a reason for not using it (for future calibration).
- Registry selections or deliberate non-use should be logged as `EvidenceRecord` entries (for example, a `RegistryUsageRecord`) and linked into the `UnifiedEvidence.decision_chain` so library-first behavior is visible in evidence.

## Example JSON Shapes

### ExecValidationRecord (example)

```json path=null start=null
{
  "id": "execval_2025-11-28T19:30:00Z_1a2b3c4d",
  "timestamp": "2025-11-28T19:30:00Z",
  "task_id": "TSK-CSF-NIP-ARCH",
  "artifact_context_id": "artifactctx_2025-11-28T19:29:59Z_abcd1234",
  "config_snapshot_id": "cwo12cfg_2025-11-28T19:29:58Z_ef567890",
  "overall_status": "pass",               
  "blocking": false,
  "enforcement_level": "strict",         
  "issue_codes": [],
  "issue_summary": [],
  "artifact_hashes": {
    "plan.md": "sha256:...",
    "tasks.md": "sha256:...",
    "data_model.md": "sha256:..."
  },
  "override_record_id": null
}
```

### RegistryUsageRecord (example)

```json path=null start=null
{
  "id": "regusage_2025-11-28T19:31:00Z_f00baa55",
  "session_id": "sess_12345",
  "request_id": "req_67890",
  "timestamp": "2025-11-28T19:31:00Z",
  "suggested_functions": [
    "get_system_config",
    "get_evidence_database_path",
    "aggregate_evidence_for_session"
  ],
  "selected_function": "aggregate_evidence_for_session",
  "ignored_functions": [
    "get_system_config",
    "get_evidence_database_path"
  ],
  "justification_if_ignored": "Existing helper handled both config and DB path resolution in one call.",
  "source_hook": "pre_generation_registry",
  "used_registered_function": true
}
```
