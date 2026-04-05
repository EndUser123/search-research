# CSF NIP Anti‑Deception – Unified Long-Term Architecture Plan

## Objectives
- Evolve the existing 5‑layer CSF NIP anti‑deception system into a **unified, evidence‑based, library‑first** architecture.
- Make **constitutional (CLAUDE.md) and CSF NIP rules operational**, not just advisory, while preserving existing effective behaviors.
- Provide a **shared validation model** (context, confidence, risk, decision) that all layers and tools can understand.
- Unify **evidence and metrics** around existing SQLite DBs and logs, with on‑demand CLIs and reports instead of always‑on services.
- Enforce **Library‑First** via a function/feature registry and pre‑generation hook so agents reliably reuse existing components.
- Integrate the CWO12 `/exec` workflow with this architecture so that artifact validation, evidence logging, and execution enforcement are consistent with CSF NIP and Library‑First policies.
- Maintain **solo‑developer feasibility**: no background daemons, no dashboards, only CLI/pytest/on‑demand workflows.
- Eliminate legacy background loops in session management (L0): no hook or CSF NIP component may start a continuous monitoring/cleanup loop or background thread outside explicit hook/CLI/test invocation.
- Maintain **solo‑developer feasibility**: no background daemons, no dashboards, only CLI/pytest/on‑demand workflows.

## Scope

### In scope
- `.claude/hooks`:
  - `session_management_*`, `user_prompt_submit.py`, `pre_tool_use.py`, `post_tool_use.py`, `llm_supervisor.py` – refinements only.
- `__csf.nip/src`:
  - `config/system_config.py`, `modules/standardization/system_config.py`.
  - `calibration/override_tracker.py`, `testing/test_quarantine.py`.
  - `lib/core_utils/*` (monitoring, calibration dashboard as needed).
  - `modules/monitoring/system_metrics.py` and metrics-related CLIs.
  - New `lib/unified_validation/*` package.
  - New CLI modules for evidence aggregation and metrics.
- New **registry** module (e.g. `lib/registry.py` or `__csf.nip/src/lib/registry.py`) plus a **PreGeneration** hook.
- **COMPLETED**: Library-First registry and PreGeneration hook fully implemented with evidence tracking.

### Out of scope
- Changing Claude Code’s core hook orchestration mechanism.
- Any always‑on servers, web dashboards, or external monitoring services.
- Major rewrites of existing CSF NIP modules beyond what’s needed to adopt unified types and registry.
- Non‑development environments (e.g., production deployment infra, external monitoring stacks).

## Success Criteria

### Technical
- **Hooks remain stable**: existing behaviors (dangerous command blocking, TDD enforcement, quality gating, supervision) continue to work with no regressions.
- A `lib/unified_validation/` package exists and is used by:
  - At least `pre_tool_use` and `post_tool_use` adapters, and
  - At least one CLI that reconstructs a `UnifiedDecision` from evidence.
- An evidence aggregation CLI (e.g. `csf_nip.tools.evidence_aggregate`) builds `unified_evidence.jsonl` from existing DBs/logs.
- Metrics CLIs (e.g. `csf_nip.metrics.health_report`) regenerate **real** metrics on demand (health, security effectiveness, TDD compliance, performance).
- A function registry and PreGeneration hook are in place:
  - Registry can list and describe registered functions.
  - Prompts in typical coding tasks show available registered functions.
  - **COMPLETED**: Registry with 3 default functions, PreGeneration hook with RegistryUsageRecord evidence tracking.
- Basic hook‑level integration tests exist for:
  - L2 dangerous command/TDD enforcement.
  - L3 quality gating (warn vs block).
  - L4 semantic supervision/fabrication handling.

### Behavioral / governance
- For critical enforcement points, hook code comments explicitly reference the relevant **VRE principle(s)** and **CSF NIP clause(s)** they implement.
- Sycophancy, blatant fabrications, and unjustified high‑confidence claims are **detectably rarer** and visible in metrics (e.g. fabrication catch tests, override tracker patterns).
- Library‑first behavior is observable: in common scenarios, registry functions are suggested and reused with justification when not reused.

### Operational
- All functionality is accessible via **CLIs and pytest**, with no persistent services.
- Execution of the most complex new CLIs (evidence aggregation, metrics) is **predictable and documented**, with clear failure modes.
- The architecture remains maintainable by a solo developer:
  - New features primarily mean adding registry entries, small adapters, tests, or new metrics—not building new infra.

## Risk Assessment

### Risk 1 – Architectural Overreach / Complexity
- **Description:** The unified validation/evidence model could become over‑engineered, increasing maintenance burden.
- **Impact:** Slower iteration; harder debugging; increased cognitive load.
- **Mitigation:**
  - Keep `lib/unified_validation/` minimal and **additive**, not mandatory.
  - Introduce adapters gradually; do not rewrite core hooks.
  - Use clear layering: types (pure data) vs adapters vs CLIs.

### Risk 2 – Regression in Existing Hooks
- **Description:** Changes in SystemConfig usage, evidence paths, or hook logic might break existing protections.
- **Impact:** Loss of safety; degraded developer trust; potential for unsafe operations.
- **Mitigation:**
  - Make path changes **one hook at a time** with immediate testing.
  - Add integration tests for key behaviors before deep refactors.
  - Use feature toggles (strict vs advisory) to soften enforcement during rollout.

### Risk 3 – Metrics / Evidence Misinterpretation
- **Description:** Metrics may be misread as guarantees, or stale reports used as truth.
- **Impact:** False sense of security; misinformed decisions.
- **Mitigation:**
  - Make metrics CLIs **regenerate on demand** with timestamps.
  - Ensure docs say “see CLI output” instead of embedding fixed numbers.
  - Include confidence intervals and sample sizes where feasible.

### Risk 4 – Registry Misuse or Drift
- **Description:** Registry not kept up to date, or overgrown registry makes prompts unwieldy.
- **Impact:** Library‑first goals not met; performance or context noise.
- **Mitigation:**
  - Make registration a **low‑friction decorator**.
  - Start with a **small, high‑value subset** of functions.
  - Add truncation/filtering strategies in PreGeneration hook (e.g. top‑N by category).

### Risk 5 – Solo‑Dev Time Constraints
- **Description:** Work exceeds realistic time budget; partially implemented features create “half architectures.”
- **Impact:** Inconsistent behavior; abandonment mid‑refactor.
- **Mitigation:**
  - Phase implementation: foundations → metrics → registry → enforcement tweaks → tests.
  - After each phase, aim for a **stable plateau** that can stand alone.
  - Prioritize **unified model, metrics, registry** workstreams that give leverage across layers.

## Timeline

(Indicative; adjust based on actual availability. Assumes ~5–8 hours/week.)

- **Phase 0: Activation & bridge to current CSF NIP implementation (first 1–2 work sessions)**
  - Treat the existing system as mostly implemented: focus on activation and wiring, not rewrites.
  - Verify SystemConfig shim, OverrideTracker, test quarantine, evidence cleanup CLI, and `system_metrics.py` all work together on your machine.
  - Fix any obvious configuration/import/path issues and add only minimal missing wiring (for example: hook OverrideTracker into key L3/L4 decision points; add thin CLIs around `system_metrics.py` that simply print current metrics).
- **Week 1–2: Foundations**
  - Governance alignment (CLAUDE.md + VRE + CSF NIP index).
  - Create `lib/unified_validation/` with core dataclasses.
- **Week 3–4: Evidence & Metrics**
  - Implement evidence aggregation CLI.
  - Implement metrics CLIs around `system_metrics.py`.
  - Align docs to point to runtime metrics.
- **Week 5–6: Library‑First Registry**
  - Implement `registry.py`.
  - Add PreGeneration hook.
  - Decorate initial set of core functions and verify behavior.
- **Week 7–8: Enforcement Mapping**
  - Carefully adopt unified types in L2/L3/L4 adapters.
  - Adjust hooks to log richer evidence tied to unified models.
- **Week 9+: Tests & Calibration**
  - Add hook‑level integration tests and calibration tests.
  - Iterate on metrics and override tracker analysis; tune thresholds and toggles.
