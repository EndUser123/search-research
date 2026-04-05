# CSF NIP Anti‑Deception – Unified Architecture Tasks

## Task Breakdown

### 0. Activation & Bridge to Existing Implementation

- **0A – Verify and activate existing components**
  - Run the evidence cleanup CLI in `status` and `cleanup --dry-run` modes and fix any import/path issues so it works end-to-end.
  - Exercise `TDDEvidenceIntegrator` and the TDD evidence DB via the PreToolUse hook or a small harness to confirm evidence rows are being written and read.
  - Run `system_metrics.py` directly (or via a temporary stub CLI) to regenerate `real_system_metrics_report.json`, fixing any DB path or configuration errors.
- **0B – Hook-level OverrideTracker coverage**
  - Review L0–L4 hooks and confirm where OverrideTracker is already integrated (currently L1 `user_prompt_submit` and L2 `pre_tool_use`).
  - Add minimal OverrideTracker logging at L3 (`post_tool_use`) and L4 (`llm_supervisor`) for key allow/block/warn decisions, reusing the existing logging patterns.
- **0C – Basic environment/test activation**
  - Identify existing test entrypoints (pytest modules or other harnesses) and ensure at least a small representative subset runs successfully.
  - Fix only straightforward configuration or path issues during this phase; defer new test authoring to Workstream F.
- **0D – L0 session background-loop cleanup**
  - Audit session management hooks (e.g. `session_health_monitor.py` and related files) for any `while True` loops, long-running async tasks, or background threads started at import or session start.
  - For each such loop, either disable it by default or gate it behind explicit, developer-controlled activation (CLI or one-shot health check), so no monitoring/cleanup runs unless you explicitly request it.
  - Confirm that in a quiescent state (no hooks/CLIs/tests running), no CSF NIP or hook code is consuming resources via background loops.

### A. Governance Alignment (CLAUDE.md + VRE + CSF NIP)

- **A1 – Governance review**
  - Review current `CLAUDE.md`, `constitution.md`, and `vre-framework-operational.md`.
  - Identify and resolve any conflicts; ensure VRE principles only *implement* existing policy.
- **A2 – VRE implementation index**
  - Create `docs/VRE_IMPLEMENTATION_INDEX.md` mapping each VRE principle to:
    - CLAUDE.md / constitution clauses.
    - Primary hook(s) / modules enforcing it.
- **A3 – Hook annotations**
  - Add inline comments in hooks tying major enforcement points to specific VRE + CSF NIP items.

### B. Unified Validation Model Library

- **B1 – Create `lib/unified_validation/`**
  - Implement dataclasses: `ValidationContext`, `UnifiedConfidenceScore`, `UnifiedRiskAssessment`, `UnifiedDecision`.
- **B2 – Layer adapters**
  - Implement minimal adapters:
    - L2 adapter: from firewall + TDD results to unified types.
    - L3 adapter: from quality metrics and BalancedValidationLogic to unified types.
- **B3 – Offline decision builder**
  - Implement helper to reconstruct a `UnifiedDecision` from evidence/override logs for a past session or action.

### C. Evidence & Metrics Unification

- **C1 – Evidence schema survey**
  - Document schemas for:
    - `tdd_enforcement_evidence`.
    - OverrideTracker DB.
    - PostToolUse evidence logs.
    - LLM supervisor evidence repository.
- **C2 – Evidence aggregation CLI**
  - Implement `csf_nip.tools.evidence_aggregate` (Python module + CLI) that:
    - Reads existing evidence sources.
    - Correlates into logical `UnifiedEvidence` records.
    - Outputs `unified_evidence.jsonl`.
- **C3 – Metrics CLIs**
  - Wrap `modules/monitoring/system_metrics.py` into:
    - `csf_nip.metrics.health_report`.
    - `csf_nip.metrics.security_report`.
    - `csf_nip.metrics.performance_report`.
- **C4 – Documentation update**
  - Update `CSF_NIP_ANTI_DECEPTION_DELTA_PLAN.md` and related docs to reference metrics CLIs instead of hard-coded numbers.

### D. Library‑First Registry

- **D1 – Implement registry core**
  - Add `lib/registry.py` with:
    - `@register_function(...)` decorator.
    - Registry APIs: query by category, list_all, `registry_to_context_string()`.
  - **COMPLETED**: Library-First registry implemented with 3 default functions.
- **D2 – Seed registry**
  - Decorate a small set of high‑value existing functions (e.g. SystemConfig helpers, evidence utilities, common path handlers).
  - Ensure registry-aware components (starting with the PreGeneration hook) emit `RegistryUsageRecord` entries when functions are suggested, used, or deliberately ignored.
  - **COMPLETED**: 3 default functions registered (get_project_root, get_evidence_db_path, load_cwo12_config).
- **D3 – PreGeneration hook**
  - Implement `.claude/hooks/pre_generation_registry.py`:
    - Build concise registry context.
    - Prepend it with Library‑First instructions to prompts.
  - Integrate into `.claude/settings.json` without breaking `user_prompt_submit`.
  - **COMPLETED**: PreGeneration hook refactored with RegistryUsageRecord evidence tracking.
- **D4 – Prompt tuning**
  - Tune registry prompt for size and relevance (e.g. category filtering, top‑N).
  - **COMPLETED**: Context-aware function suggestions with character limits and relevance scoring.

### E. Hook-Level Enforcement Mapping

- **E1 – L1 (user_prompt_submit)**
  - Ensure:
    - Constitutional/VRE rules are reinforced at prompt level.
    - Hook emits context metadata that can be used by downstream components (e.g. intent flags).
- **E2 – L2 (pre_tool_use)**
  - Clarify and, if needed, refactor:
    - Explicit “refusal over simulation” checks for tools/capabilities.
    - OverrideTracker logging for blocks and high‑risk decisions.
- **E3 – L3 (post_tool_use)**
  - Treat validation outcomes as canonical “ground truth” for code health.
  - Ensure all validation runs create evidence records compatible with unified models.
- **E4 – L4 (llm_supervisor)**
  - Add or firm up:
    - Minimal evidence audit on final responses.
    - Confidence calibration based on presence/quality of evidence and override patterns.

### F. CLIs and Tests

- **F1 – Hook integration tests**
  - Write pytest-based tests that exercise:
    - L2 dangerous command blocks and TDD enforcement.
    - L3 warning vs blocking behavior.
    - L4 handling of a simple fabrication scenario.
- **F2 – Calibration & metrics tests**
  - Tests that:
    - Exercise OverrideTracker analysis with synthetic overrides.
    - Validate `system_metrics.py` with small, controlled DB snapshots.
- **F3 – CLI regression checks**
  - Add tests/scripts that:
    - Run evidence_cleanup in dry‑run and real modes.
    - Run metrics CLIs and ensure valid JSON structure.
    - Run evidence_aggregate on a tiny fixture DB and validate a sample `UnifiedEvidence` record.

### G. CWO12 & /exec Integration

- **G1 – Artifact triplet selection & discovery**
  - Implement or configure the CWO12 artifact validator so that when multiple candidate `plan.md`/`tasks.md`/`data_model.md` triplets exist, it:
    - Uses conversation context (project name, domain, referenced paths, or explicit `TSK-*` IDs) to infer the most relevant triplet.
    - If ambiguity remains, explicitly asks the user which triplet to use before proceeding.
  - Ensure the validator respects `TSK-CSF-NIP-ARCH/cwo12.config.json` discovery rules (artifact_root ".", no root fallback, `on_multiple_candidates: block_and_ask`).
  - **COMPLETED**: Artifact validator discovers 15 candidates, applies context scoring, correctly handles ambiguity.
- **G2 – CWO12 validator implementation & content checks**
  - Implement `__csf.nip/commands/cwo12/artifact_validator.py` and `cwo12_spec.py` (or equivalent) to:
    - Validate that `plan.md`, `tasks.md`, and `data_model.md` follow the required CWO12 structure.
    - Perform semantic checks: tasks reference concrete files/CLIs or tests where appropriate; data model entities either map to real code or are explicitly marked as logical-only; validation rules are tied to tests/CLIs.
  - **COMPLETED**: cwo12_spec.py with proper data models, artifact_validator_new.py with triplet selection.
- **G3 – Evidence & OverrideTracker logging for /exec**
  - Persist each `/exec` validation/decision as an `ExecValidationRecord` (backed by a dedicated table in the evidence database) so that artifact compliance history is kept separate from user overrides.
  - Optionally, create a lightweight OverrideTracker record pointing to the `ExecValidationRecord` via metadata when you want CWO12 decisions to participate in calibration, using a distinct `source_component` (for example `cwo12_exec_validator`).
  - Include artifact hashes, enforcement level, overall status, and any `--force` attempts in the stored record(s), consistent with `cwo12.config.json`.
  - **COMPLETED**: ExecValidationRecord, ArtifactContext, Cwo12ConfigSnapshot tables with storage helpers.
- **G4 – Library‑First and hook alignment in CWO12 flows**
  - For `/exec`-driven coding tasks, ensure:
    - The PreGeneration registry hook is enabled so the LLM sees registered functions.
    - Registry usage or explicit non-usage is captured as evidence (e.g. a `RegistryUsageRecord`) and linked into `UnifiedEvidence.decision_chain`.
  - Align `/exec` enforcement for high-risk CSF NIP components (hooks, override tracker, metrics, registry, evidence paths) with the `risk_tiers` and `hook_requirements` defined in `cwo12.config.json` (strict mode, no `--force`).
  - **COMPLETED**: PreGeneration hook emits RegistryUsageRecord evidence, integrates with CWO12 validation.
- **G5 – CWO12 regression checks**
  - Add minimal tests or scripts that:
    - Run `/exec --validate-only` for `TSK-CSF-NIP-ARCH` and confirm it selects the correct artifact triplet and fails cleanly when artifacts are intentionally broken or incomplete.
    - Verify that `/exec` validation latency stays within configured performance guards and that evidence/OverrideTracker entries are written as expected.
  - **COMPLETED**: Validation tested - finds 15 candidates, evidence tracking confirmed working.

## Dependencies

- **A (Governance)** is foundational:
  - B, C, D, E, F should all respect the agreed governance mapping.
- **B (Unified validation)** is required for:
  - C2 (evidence aggregation) and parts of E (adapting hooks).
- **C (Evidence/metrics)** depends on:
  - B for unified types,
  - Existing DB schemas remaining stable.
- **D (Registry)** is largely orthogonal but:
  - E1 (L1) and E2/E3 should be aware of Library‑First behavior for risk/confidence models.
- **E (Enforcement mapping)** depends on:
  - A and B, and partially on C and D for evidence and registry context.
- **F (Tests)** depends on:
  - Partial completion of B–E for meaningful integration coverage.
- **G (CWO12 & /exec)** depends on:
  - A and the governance index for rule mapping,
  - B and C for unified types and evidence,
  - D and E for registry and enforcement behavior.

High‑level dependency chain

- A → (B, D, G)  
- B → C → E → F → G  
- C → G  
- D → E → F → G  

## Completion Criteria

- Governance:
  - VRE index exists and is up to date.
  - Hooks’ key enforcement points are annotated with VRE and CSF NIP references.
- Unified validation:
  - Core dataclasses are in place and used in at least one adapter and CLI.
- Evidence & metrics:
  - Evidence aggregation CLI produces unified evidence for at least recent sessions.
  - Metrics CLIs produce consistent summaries based on real data.
- Registry:
  - Registry is usable and visible in prompts.
  - At least a handful of real CSF NIP utilities are registered and reused.
- Enforcement mapping:
  - Documented contract from VRE → hooks → unified risk/confidence exists and is partially implemented.
- Tests:
  - New pytest suites run and pass locally for the intended scenarios.
  - CI (if present) can run at least the unit/layer tests without undue flakiness.

## Resource Allocation

- **Primary resource:** Solo developer (you), with LLM assistance for drafting code/tests/docs.
- **Estimated effort:**
  - Governance (A): ~4–6 hours.
  - Unified validation (B): ~6–10 hours.
  - Evidence & metrics (C): ~6–10 hours.
  - Registry (D): ~6–10 hours.
  - Enforcement mapping (E): ~8–16 hours.
- Tests & calibration (F): ~8–16 hours.
- CWO12 & /exec integration (G): ~6–12 hours.
- **Tools:**
  - Existing Python toolchain (pytest, SQLite, any formatters/linters you already use).
  - Claude/LLM assistance for iterative design and small refactors.
- **Non-technical:**
  - Time for periodic **design/verification passes** (reading evidence/metrics reports).
  - Occasional manual testing of `/exec` and related workflows.
