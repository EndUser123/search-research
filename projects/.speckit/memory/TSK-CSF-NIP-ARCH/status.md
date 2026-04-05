# TSK-CSF-NIP-ARCH – Implementation Status & Reality Check

This file is the **source of truth** for what has and has not been implemented for the CSF NIP Anti‑Deception unified architecture and CWO12 integration. It is designed so /exec and any LLM can quickly regain context even after losing chat history.

## 1. CWO12 `/exec` Integration (Workstream G)

### Intended (per `plan.md`, `tasks.md`, `data_model.md`, `cwo12.config.json`)

- Local CWO12 config in this task directory:
  - `cwo12.config.json` defines:
    - `artifact_root` = `.` (this TSK folder).
    - Strict enforcement, no `--force`, no auto-generate.
    - Discovery rules: **no root fallback**, `on_multiple_candidates: "block_and_ask"`.
    - Governance integration, evidence logging, library‑first, hook requirements, performance guards.
- Validator + spec code under `__csf.nip/commands/cwo12/`:
  - `artifact_validator.py`: discovers candidate `plan.md`/`tasks.md`/`data_model.md` triplets, uses conversation context + `cwo12.config.json` to pick the correct triplet, asks the user if still ambiguous.
  - `cwo12_spec.py`: defines types/enums (artifact types, enforcement levels, validation statuses), config loader, and validation report schema.
  - Behavior:
    - Validate **structure** of each artifact (required sections present).
    - Validate **semantics** (tasks link to files/tests/CLIs; data model entities map to real code or are explicitly logical‑only; validation rules tie to tests/CLIs).
    - Decide pass/warn/fail/ambiguous + blocking or not, using enforcement config + performance guards.
- Evidence logging:
  - Implement `ExecValidationRecord`, `ArtifactContext`, `Cwo12ConfigSnapshot` as **real DB tables/records**.
  - Persist each `/exec` validation to `ExecValidationRecord`, not just OverrideTracker.
  - Optionally add a small OverrideTracker record pointing to the ExecValidationRecord when you want CWO12 in calibration.

### Actual Status (code)

- `cwo12.config.json` in `TSK-CSF-NIP-ARCH` **exists and is correct**.
- `plan.md`, `tasks.md`, `data_model.md` **describe** CWO12 integration and the new entities.
- **Missing code**:
  - No `__csf.nip/commands/cwo12/artifact_validator.py`.
  - No `__csf.nip/commands/cwo12/cwo12_spec.py`.
  - No implementation of:
    - Triplet discovery/selection logic.
    - CWO12 artifact validation (structure + semantics).
    - Writing `ExecValidationRecord`, `ArtifactContext`, or `Cwo12ConfigSnapshot` into any DB.

**Conclusion:** CWO12 is **designed and configured**, but **not implemented** in code. `/exec` currently relies only on its documentation and whatever generic behavior the tool host provides.

## 2. Function Registry & PreGeneration Hook (Workstream D)

### Intended

- Central registry library (`lib/registry.py` or `__csf.nip/src/lib/registry.py`) that:
  - Provides a small `@register_function(...)` decorator.
  - Stores data in a shape consistent with `RegisteredFunction` in `data_model.md`.
  - Focuses on **project helpers** (SystemConfig helpers, evidence utilities, path handlers, etc.), not arbitrary stdlib/third‑party APIs.
- PreGeneration hook (`.claude/hooks/pre_generation_registry.py`) that:
  - Imports the central registry.
  - Builds a concise, category‑grouped, truncated registry context string.
  - Prepends Library‑First instructions + registry context to prompts.
  - Emits `RegistryUsageRecord` entries when functions are suggested, used, or deliberately ignored.

### Actual Status

1. `__csf.nip/src/lib/registry.py`

- Exists, but is **over‑engineered and off‑spec**:
  - Large "production‑ready" registry claiming O(1) lookups, stats, evidence integration.
  - Imports non‑existent modules like `.core_utils.evidence_based_validation_framework`, `.session_management`, `.hybrid_dual_map_architecture`.
  - High maintenance surface; likely **broken** if used.
  - Does **not** clearly align with the simple `RegisteredFunction` entity or `RegistryUsageRecord` model.

2. `.claude/hooks/pre_generation_registry.py`

- Exists and is **independent** of `__csf.nip/src/lib/registry.py`:
  - Builds its own ad‑hoc "registry" of:
    - Hard‑coded stdlib functions.
    - Third‑party libs (pandas, numpy, requests, FastAPI, etc.).
    - Project functions via a regex‑based scan of all `*.py` files.
  - Computes relevance scores, categories, and emits a large prompt section with stdlib/project/third‑party/pattern functions and examples.

- Problems relative to the plan:
  - **Not using the central registry or data model**:
    - No import of `lib.registry`.
    - Does not use `RegisteredFunction` schema.
  - **No `RegistryUsageRecord` evidence**:
    - Nothing writes `RegistryUsageRecord` rows; Library‑First behavior is not observable in evidence.
  - **Unnecessary third‑party coupling**:
    - Promotes pandas, FastAPI, etc., regardless of project needs.
  - **Expensive, brittle scanning**:
    - Recursively scans the project tree via regex; not the small, curated registry intended.

**Conclusion:** A registry and PreGeneration hook exist, but they **do not implement** the TSK design (central, project‑focused registry + evidence). They should be treated as **off‑spec** and candidates for replacement/simplification.

## 3. Data Model & Evidence Alignment

### Intended

- `data_model.md` defines:
  - `ExecValidationRecord`, `Cwo12ConfigSnapshot`, `ArtifactContext` for CWO12.
  - `RegistryUsageRecord` for Library‑First tracking.
  - Updated Data Integrity and Validation Rules (IDs, thresholds, retention, governance source‑of‑truth, etc.).

### Actual Status

- These entities are **defined only in documentation**.
- No code in `__csf.nip/src` currently:
  - Creates SQLite tables for `ExecValidationRecord` or `RegistryUsageRecord`.
  - Writes to or reads from such tables.
- OverrideTracker and existing evidence DBs still log only their original schemas.

**Conclusion:** Data model extensions are **architecturally specified**, but **not implemented** in persistence or in any hooks/CLIs.

## 4. Hook System (L1–L4) vs. E‑Stream

### Intended (E‑workstream)

- L1 `user_prompt_submit`: constitutional/context enforcement and metadata emission.
- L2 `pre_tool_use`: execution firewall, refusal‑over‑simulation, TDD enforcement, structured OverrideTracker logging.
- L3 `post_tool_use`: balanced quality gates, evidence logging compatible with unified models.
- L4 `llm_supervisor`: semantic supervision, evidence audit, calibration of semantic confidence vs. evidence.

### Actual Status (high‑level)

- **L1 / L2**:
  - Already integrate with SystemConfig, feature toggles, OverrideTracker, and TDD evidence.
  - Generally aligned with Workstreams A/B/C, but not yet wired into `UnifiedEvidence` / `ExecValidationRecord` / `RegistryUsageRecord`.

- **L3 / L4**:
  - Contain substantial logic (parallel validation engine, semantic supervision), but:
    - Do **not** emit the new evidence types (`UnifiedEvidence`, `ExecValidationRecord`, `RegistryUsageRecord`).
    - Have **no CWO12 awareness**.

**Conclusion:** Safety behaviors exist, but the bridge to the new unified validation model, CWO12 evidence, and Library‑First evidence is **still pending**.

## 5. Summary: What *Should* Exist vs. What *Does* Exist

- **CWO12 Core (G):**
  - ✔ Design + `cwo12.config.json` + artifacts.
  - ✘ No `artifact_validator.py` / `cwo12_spec.py` / DB wiring for ExecValidationRecord & ArtifactContext.

- **Registry & PreGeneration (D):**
  - ✔ A registry module and a PreGeneration hook **exist**, but are off‑spec.
  - ✘ No integration with new data model; PreGeneration hook uses its own ad‑hoc registry.

- **Data Model for CWO12 & Library‑First:**
  - ✔ Defined in `data_model.md`.
  - ✘ No DB schema or code writing/reading these records.

- **Hooks (E):**
  - ✔ Foundation exists (L1–L4 are sophisticated and mostly working).
  - ✘ Not yet adapted to unified_validation + CWO12 + RegistryUsageRecord evidence.

## 6. How a Future LLM Should Use This File

When resuming work on `TSK-CSF-NIP-ARCH` (for example via `/exec`):

1. **Always read these files first:**
   - `plan.md`, `tasks.md`, `data_model.md`, `cwo12.config.json`, `status.md` (this file).
2. **Treat THIS FILE as the reality check:**
   - If any prior LLM claims “CWO12 is fully implemented” or “Registry is production‑ready and evidence‑integrated”, cross‑check against this status.
3. **Next safe implementation steps (high level):**
   - Implement `__csf.nip/commands/cwo12/artifact_validator.py` + `cwo12_spec.py` consistent with `cwo12.config.json` and `data_model.md`.
   - Design and migrate to a **small, project‑focused registry** in `__csf.nip/src/lib/registry.py` that:
     - Only depends on real modules.
     - Exposes a simple `@register_function` API.
   - Rewrite `.claude/hooks/pre_generation_registry.py` to:
     - Use the central registry.
     - Emit `RegistryUsageRecord` entries.
     - Limit prompt size and avoid arbitrary third‑party suggestions.
   - Add DB schema and helpers for `ExecValidationRecord`, `ArtifactContext`, `RegistryUsageRecord` consistent with this data model.

This status file should be updated as work is actually implemented so future sessions can trust it as a ground truth log, independent of any lost LLM context.
