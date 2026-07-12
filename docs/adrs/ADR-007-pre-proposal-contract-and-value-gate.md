# ADR-007: Pre-Proposal Contract-and-Value Gate for Cross-Component Mechanism Changes

**Date:** 2026-07-11
**Status:** Proposed (v2, revised after internal review of v1)
**Decider:** Bruce Thomson

## Context and Problem Statement

Three incidents in a single session shared one root cause: **architectural hypotheses were promoted to code without evidence of real-world value.**

1. **`estimated_tokens`** (prompt-enhancer `EnhancementResult`) — a field added on the assumption the model would use it "for context budget tracking." Lived 10+ plugin versions. Zero production consumers ever read the value. Snapshot carried it as an opaque blob; no code inspected it.
2. **Referent inference** (`resolve_referent` / `extract_subject` in deleted `context.py`) — a pronoun-resolution chain built on the assumption "first file reference in the prior prompt = discourse subject." One confirmed false positive (`"fix it directly"` → `console_*.jsonl`). Entire chain deleted.
3. **`Intent` line** (`build_additional_context`) — initially classified as dead-weight restatement. Source inspection revealed it is the sole carrier of the destructive target on the `confirm` hook path, asserted by `test_confirm_has_additional_context`. Near-miss removal.

The common anti-pattern: a developer (human or LLM) writes field/mechanism A on component 1, *imagines* component 2 will use it, ships both, and nobody ever verifies whether component 2 actually reads A — or whether the signal A produces is correct.

### The deeper finding (liveness ≠ value)

**Field liveness is necessary but insufficient.** The referent-inference chain was fully "live" — producer existed, the model consumed the injected context, storage and hook path existed. The defect was that the *signal was wrong*. No grep-based consumer check catches a wrong signal.

This problem appears at two levels:
- **Tier 1 (cheap, structural):** dead fields — no reader exists. Solvable by static liveness.
- **Tier 2 (hard, behavioral):** live-but-wrong signals — reader exists, value unproven or negative. Solvable only by evidence scaled to consumer type.

Any gate that stops at Tier 1 would have caught `estimated_tokens` and sailed past the referent bug. This ADR addresses both tiers.

### What an earlier proposal got wrong (two errors)

A first-pass fix proposed a hand-maintained `CROSS_COMPONENT_CONTRACTS` dict in `mechanism_manifest.py` plus inline consumer annotations in `schemas.py`. An adversarial review caught two errors:

1. **Error 1 — manual drift.** A hand-maintained registry is the exact "architect intent instead of measurement" anti-pattern this ADR exists to remove. It drifts; a stale registry in the prompt is worse than none. *Compute, never hand-maintain.*
2. **Error 2 — liveness-as-value at the meta-level.** The ADR's own taxonomy claimed `behavioral` consumers "prove value unconditionally." This contradicts the `liveness ≠ value` finding at the concept level: a behavioral reader can consume a wrong signal, a dead code path, or a harmful value. The taxonomy recreated the error it was designed to remove, one level up.

This revised ADR fixes both.

### `liveness ≠ value` applies to every enforcement stage

The following design rules all follow from that single invariant:

- A grep match is not a consumer. A consumer is not a value. A value for one consumer type does not satisfy another.
- `NO_CHANGE` requires the same evidence standard as a new mechanism — "an existing path exists" is not "the existing path works correctly."
- `REMOVAL_REQUIRES_DEPENDENCY_PROOF` is not satisfied by local-tree-only search — external, generated, persisted, runtime, and cache consumers also count.
- Fail-open is acceptable for quality gates (Tier 1), unsafe for required contracts (Tier 2) — a "mandatory" contract that silently bypasses on error is not mandatory.
- A computed consumer map (grep / tree-sitter) has a known ceiling — it cannot discover dynamic access, aliases, JSON/CLI/API consumers, generated code, plugin-cache copies, or cross-repo consumers. Honest output requires a coverage grade, not implicit completeness.

### Scope boundary

This gate fires only when a candidate would add, modify, or remove cross-component state:

- persisted or shared state
- a schema or artifact field
- a registry or whitelist entry
- cross-plugin / cross-component data flow
- hook-provided `additionalContext`
- identity, freshness, authority, or cache state

Ordinary local-surgical tasks receive no contract review and no extra context injection.

## Decision

Add a **task-scoped, pre-proposal Contract-and-Value Review** to the existing `/go` mechanism-change preflight path, plus a narrow **PreToolUse schema-field gate** for edit-time enforcement.

Two principles govern the design:

1. **Compute, never hand-maintain.** Any producer→consumer map is derived at runtime (grep / tree-sitter), stamped with a coverage grade. No hand-maintained `CROSS_COMPONENT_CONTRACTS` dict.
2. **Evidence scales with consumer type.** Existence of a reader is the floor, not the ceiling. Every behavior-changing consumer — LLM or code — requires an outcome probe.

### Provisionally rejected

- **OPA/Conftest.** Deferred. A narrow Python validator suffices until the decision-rule set becomes hard to maintain. Revisit only when policy logic crosses ~12 rules.
- **Spec Kit / OpenSpec.** Declined. Both overlap `/go`'s existing classification and preflight. Borrow OpenSpec's proposal-artifact shape; do not replace `/go`.
- **Always-injected global catalog.** Rejected for v1. Context bloat degrades unrelated prompts. One invariant sentence is injected globally; detail is task-scoped.

## Consumer-Type Taxonomy

Every consumer must be classified before it counts. The taxonomy is the ADR's central diagnostic tool — it is what separates "snapshot carried `estimated_tokens`" from "something used `estimated_tokens`."

| Type | Proves executable use? | Requires outcome probe? | Example |
|------|------------------------|-------------------------|---------|
| `proves_executable_use` | Yes — code reads the value and changes behavior | **Yes** — code-level use is necessary but not sufficient; the behavioral change must also be correct on a measured corpus | hook gates injection on `confidence`; referent inference injecting subjects |
| `model_context` | Conditionally | **Yes** — must measure TP/FP on real session transcripts; grep cannot prove the model consumed the signal | `additionalContext` injected into the prompt |
| `opaque_carrier` | No | Never — transports without interpreting | snapshot carries `prompt_enhancement` |
| `persistence` | No | Never — stores/restores only | `active_enhancement.json` on disk |
| `policy_boundary` | No | Never — recognizes key name only | `FORBIDDEN_POLICY_KEYS` |
| `diagnostic` | No | Never — human/observability only | a logging field |
| `compatibility` | No | Never — kept for schema roundtrip | retained for old-snapshot readers |

`proves_executable_use` and `model_context` both require a measurable behavioral probe (see probe contract below). The other five establish liveness but **not** value — and must be labeled as such. A proposal whose only consumer type is one of those five is `ADVISORY_OPAQUE_ONLY` (which defaults to rejection unless an explicit exemption applies).

## Behavioral Probe Contract

Any claim of executable or model-context value MUST ship with a measurable probe. The probe contract has required fields:

| Field | Requirement |
|-------|-------------|
| **Corpus source** | Directory path and selection criteria; must be representative of real session data |
| **Minimum corpus size** | ≥20 unrelated prompts/sessions (or explicit justification for fewer) |
| **Gold-label protocol** | How human labels were obtained, inter-labeler agreement, and what "correct" means |
| **Baseline comparison** | What existing mechanism was measured as the baseline, and the measured metric |
| **Measurable metric** | Precision, recall, TP/FP, or harm count — with absolute values and (if applicable) latency P95 |
| **Acceptable threshold** | What precision/recall/harm rate is acceptable for this gate to pass |
| **Label-unavailable fallback** | When labels cannot be obtained, what proxy evidence suffices (must be pre-approved by the decider) |
| **Privacy/redaction** | How PII, tokens, and sensitive paths are handled in the corpus |
| **Falsifier** | A concrete result that, if observed, would prove the mechanism ineffective or harmful |

The probe contract is the **only** way to satisfy `BLOCKED_VALUE_UNVERIFIED`. Grep matches alone do not count.

This directly enforces the `measured_tp_on_corpus` field rule added to CLAUDE.md (every new enforcement gate must ship with a measured TP/FP on a real held-out corpus before it can block).

## Consumer Map Coverage Grade

The runtime consumer map (grep / tree-sitter) must stamp every output with a coverage grade:

| Grade | Meaning |
|-------|---------|
| `local_source` | match found in this repo's `.py` files (excluding tests and the producer file) |
| `masked` | access pattern detected that grep/tree-sitter cannot resolve (dynamic attribute, alias, reflection, generated code) |
| `cross_repo` | potential consumer in a different repository (warn, not block) |
| `runtime_only` | consumer exists only at runtime (plugin cache, generated artifact, CLI/config reader) — no static match possible |
| `no_match` | no consumer found in any scanned source |

`no_match` does **not** mean "no consumer exists" — only that none was found within the tool's known ceiling. This is surfaced as `UNKNOWN_CONSUMER_SURFACE` (see decision rules).

## The Contract-and-Value Section (Tier 1 + Tier 2)

Extends `/go` preflight (`preflight_propose.py`). Populated per affected boundary:

```yaml
boundary_id:        <stable id>
change_kind:        add | modify | remove

value_claim:        <observable outcome that should improve>
producer:           <file:function that creates the value>
transport_or_storage: <artifact | hook payload | prompt injection | cache | file | API>
consumer:           <file:function or model-context boundary>
consumer_type:      proves_executable_use | model_context | opaque_carrier |
                    persistence | policy_boundary | diagnostic | compatibility
consumer_coverage:  local_source | masked | cross_repo | runtime_only | no_match
authority:          <source authoritative when sources disagree>
identity_scope:     <session_id | run_id | task_id | repo/worktree>
freshness_and_versioning: <how stale data / old schemas are detected>
failure_direction:  per-state-enum below

existing_mechanism: <current mechanism inspected, and why it cannot satisfy the goal>
evidence:           <source inspection proving the current path>

# Required if consumer_type is proves_executable_use or model_context:
acceptance_probe:
  corpus_source:    <path and selection criteria>
  corpus_size:      <N>
  gold_label_protocol: <how and by whom>
  baseline:         <existing mechanism and its measured metric>
  measured_metric:  <precision / recall / TP / FP / harm count / latency P95>
  threshold:        <pass condition>
  label_unavailable_fallback: <proxy evidence, decider-approved>
  privacy_protocol: <how PII / tokens / sensitive paths are handled>
  falsifier:        <concrete result that would disprove value>
```

Stored in the **existing run-scoped proposal/discovery artifact** under the current `run_id`, bound by the same `session_id` discipline `/go` already uses. No new global registry.

### Failure direction enum

Every boundary must declare what happens in each error class. Enum values: `block` | `warn` | `fail_open` | `irrelevant`:

| Error class | Required? | Default |
|-------------|-----------|---------|
| Producer absent | required | `block` |
| Artifact absent | required | `warn` |
| Consumer absent | required | `block` |
| Consumer malformed | required | `block` |
| Stale data (< run-scoped) | required | `block` |
| Foreign session data | required | `fail_open` (ignore silently) |
| Incompatible schema version | required | `block` |
| Scan/read error | required | `block` for Tier 2 / `fail_open` for Tier 1 |
| Unknown consumer type | required | `block` |

The "mandatory contract, fail-open on error" contradiction from v1 is eliminated: a required contract uses `block` as its default for all non-foreign error classes.

## Decision Rules

The preflight renderer emits exactly **one outcome per boundary**. Outcomes have the following dominance order (higher wins when boundaries conflict):

```
BLOCKED_VALUE_UNVERIFIED > BLOCKED_CONSUMER_UNVERIFIED >
BLOCKED_AUTHORITY_UNKNOWN > REMOVAL_REQUIRES_DEPENDENCY_PROOF >
UNKNOWN_CONSUMER_SURFACE > ADVISORY_OPAQUE_ONLY > READY_TO_PROPOSE >
NO_CHANGE
```

| Outcome | Meaning | Default action |
|---------|---------|----------------|
| `BLOCKED_VALUE_UNVERIFIED` | `proves_executable_use` or `model_context` consumer lacks a behavioral probe meeting the contract above | Block proposal |
| `BLOCKED_CONSUMER_UNVERIFIED` | consumer is merely assumed (no verified file:function, or consumer_coverage is `no_match` with no `runtime_only` justification) | Block proposal |
| `BLOCKED_AUTHORITY_UNKNOWN` | source, identity, or freshness authority is unresolved | Block proposal |
| `REMOVAL_REQUIRES_DEPENDENCY_PROOF` | removal proposed without checking all forests: local source, external clients, generated artifacts, persisted historical data, migrations, cache copies, user configuration, runtime-loaded plugin versions | Block removal |
| `UNKNOWN_CONSUMER_SURFACE` | consumer_map returned `no_match` or `masked` with no `runtime_only` override — actual consumer status is unknown | Warn, do not block |
| `ADVISORY_OPAQUE_ONLY` | the only "consumers" are opaque/persistence/policy/diagnostic/compatibility — no one reads the value for behavioral effect | **Reject unless** the proposal explicitly identifies one of: **persistence** (must survive compaction), **compatibility** (must exist for old-snapshot roundtrip), **diagnostic** (must be human-readable in artifacts). Each exemption carries its own evidence burden. |
| `READY_TO_PROPOSE` | all checks pass | Allow |
| `NO_CHANGE` | an existing mechanism satisfies the requirement | **Must meet same evidence standard as a new mechanism.** Shape-fit alone is insufficient; the existing path must have a measured behavioral probe or an audit confirming correctness on real data. If the existing path is unproven, emit `BLOCKED_VALUE_UNVERIFIED` instead. |

A blocking outcome withholds only the **mechanism proposal**, not the entire unrelated task. `UNKNOWN_CONSUMER_SURFACE` and `ADVISORY_OPAQUE_ONLY` produce an advisory report but do not block — unless the decider has set enforceability for that component to `blocking` (env-var gated, same pattern as task_self_doc_gate).

## Edit-Time Enforcement (PreToolUse schema gate — Tier 1 only)

To act *before* code is written, not only before the proposal is shown:

- **Trigger:** `Edit`/`Write`/`MultiEdit` on files matching `schemas.py` or containing Pydantic `BaseModel` / `@dataclass` definitions.
- **Action:** parse the proposed diff for newly added field definitions.
- **Verification:** for each new field, run a source-tree grep (excluding the edited file and tests). If no match found, **validate the model's response** rather than trusting it: the model must cite an actual existing file:function that references the field. If the cited path does not exist or does not contain the field name, treat it as `BLOCKED_CONSUMER_UNVERIFIED`.
- **Exemptions** (with evidence burden on the proposer):
  - **persistence-only**: field must survive compaction (prove the artifact path and restoration logic exist)
  - **compatibility-only**: field must exist for old-snapshot roundtrip (prove the schema version that depends on it)
  - **diagnostic-only**: field must be human-readable (prove the log/artifact output and the OOB/alert path)
  - **future-public-api**: field is part of a published plugin API with a versioning plan (prove the version contract and deprecation path)
  - **external-consumer**: the consumer is in a different repository or runtime (document the known consumer and the coordination channel)
- If no exemption applies and no verified consumer is found: **blocking** decision.

The gate is deliberately **Tier 1 only** — it evaluates liveness, not signal quality. Tier 2 is the preflight's job. Blocking on Tier 1 is safe because a zero-reader field that is not exempted by one of the above categories is dead code by definition.

## Global Injection

One invariant sentence in `mechanism_manifest.py`. Nothing else injected globally:

> Before recommending a new cross-component field, artifact, state path, or prompt injection, inspect and name its producer, transport/storage, behavioral consumer, authority, freshness, failure behavior, and real acceptance probe. Treat opaque transport as transport — not proof of value. Mark any unverified dependency as blocking before presenting the proposal.

No catalog, no table, no per-field registry. Detailed facts are discovered from the task's actual source tree at preflight time.

## Implementation Plan

### Phase 0 — Perf attribution hook narrowing

**Goal:** Remove false-positive triggers on rhetorical statements before adding new gates.

| Step | File | Change | Test |
|------|------|--------|------|
| 0.1 | `.claude/hooks/Stop_perf_attribution_gate.py` (verify exact path first) | Narrow trigger regex to match only concrete system timings (e.g. `\b\d+\s*(ms|seconds?|minutes?)\b` near bottleneck/throughput/dominant keyword), plus experiment IDs. Exempt generic tool-speed statements. | Add test for each exempted pattern (e.g. "takes 30 seconds" referring to grep, not a measured latency). |

**Dependencies:** none.
**Verification:** all three incident reviewers mentioned this — confirmed trigger against mid-session false positive.

---

### Phase 1 — Preflight contract section + decision rules (warning mode)

**Goal:** Extend `/go`'s mechanism-change preflight with the Contract-and-Value section. Run read-only for calibration before blocking.

#### Step 1.1 — Runtime consumer map helper

| Item | Detail |
|------|--------|
| **New file** | `packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/consumer_map.py` |
| **API** | `build_consumer_map(schema_fields: list[str], search_roots: list[Path], exclude_patterns: list[str]) -> dict[str, CoverageGrade]` |
| **Behavior** | For each field name, run `rg --include="*.py" -l <field>` across `search_roots`. Filter out matches in `exclude_patterns` (the producer file, `**/tests/**`, `**/__pycache__/**`). Classify each result into a `CoverageGrade` (see below). |
| **CoverageGrade** | `local_source` (found), `masked` (dynamic access pattern detected via heuristic: `getattr`, `__getattribute__`, `model_dump`, `model_validate`, square-bracket subscript on dict), `cross_repo` (match in a directory outside this repo), `runtime_only` (match only in `.json` files, generated cache dirs like `.artifacts/` or `__pycache__`), `no_match` (no result). |
| **Output** | `ConsumerMap` dataclass: `fields: dict[str, list[ConsumerMatch]]` where `ConsumerMatch` has `file: str`, `line: int | None`, `grade: CoverageGrade`. |
| **Edge cases** | No `schema_fields` → return empty dict. `search_roots` nonexistent → log warning, return empty. rg not on PATH → `no_match` for all fields, warn to stderr. UTF-16 files on Windows → skip with debug log (rg's default binary detection). |

**Tests** (`tests/test_consumer_map.py`):
- Field present in one consumer file → `local_source`
- Field only in producer file + tests → `no_match`
- Field accessed via `getattr` or `model_dump` → `masked`
- Field only in `.json` artifact → `runtime_only`
- Empty field list → empty result
- Nonexistent search root → warning logged, empty result
- rg not installed → `no_match` for all, warning

#### Step 1.2 — Behavioral probe validator

| Item | Detail |
|------|--------|
| **New file** | `packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/probe_validator.py` |
| **API** | `validate_probe(probe: dict) -> ValidationResult` |
| **Validation** | Checks that all 10 required fields are present (see probe contract section above). Rejects if: `corpus_size < 20` with no justification; `gold_label_protocol` is empty; `baseline` is empty; `threshold` is empty; `falsifier` is empty. Returns `is_valid: bool` + `missing: list[str]` + `warnings: list[str]`. |
| **Edge cases** | Empty probe dict → `is_valid=False`, all 10 missing. Partially filled probe → list only missing fields. |

**Tests** (`tests/test_probe_validator.py`):
- Complete probe → valid
- Empty probe → invalid, 10 missing
- Partial probe → invalid, correct missing list
- `corpus_size=5` with no justification → warning, not invalid
- `corpus_size=5` with justification → valid if other fields present
- Probe with extra unknown fields → ignored (permissive)

#### Step 1.3 — Decision-rule renderer

| Item | Detail |
|------|--------|
| **New file** | `packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/contract_value_renderer.py` |
| **API** | `render(proposal: dict) -> list[BoundaryResult]` |
| **Input** | The Contract-and-Value YAML section as a dict (one `boundaries` list). |
| **Logic per boundary** | 1. Validate shape (all required keys present). 2. Run `consumer_map.build_consumer_map(fields, ...)` if `consumer` is a file path. 3. Run `probe_validator.validate_probe(probe)` if consumer_type is `proves_executable_use` or `model_context`. 4. Apply decision-rule dominance ordering. 5. Emit `BoundaryResult`. |
| **Dominance resolution** | Multiple boundaries → pick the highest-ranking outcome per the order in the Decision Rules section. |
| **Output** | `list[BoundaryResult]` — each has `boundary_id: str`, `outcome: Outcome`, `rationale: str`, `missing_fields: list[str]`. |
| **Edge cases** | Empty boundaries list → empty result (no error — no mechanism changes). Missing `boundary_id` → assign `boundary_0` with a warning. Unknown consumer_type → `BLOCKED_AUTHORITY_UNKNOWN`. `consumer_map` returns `no_match` for all fields → `UNKNOWN_CONSUMER_SURFACE` unless consumer_type explains why (runtime_only override). Proposal dict missing entire `boundaries` key → empty result (skip for non-mechanism tasks). |

**Tests** (`tests/test_contract_value_renderer.py`):
- Empty boundaries → empty result
- Single boundary, all valid → `READY_TO_PROPOSE`
- `proves_executable_use` consumer, no probe → `BLOCKED_VALUE_UNVERIFIED`
- `opaque_carrier` only, no exemption → `ADVISORY_OPAQUE_ONLY`
- `opaque_carrier` with persistence exemption → `ADVISORY_OPAQUE_ONLY` (exemption noted, outcome unchanged — decider sees exemption rationale)
- Consumer map returns `no_match` → `UNKNOWN_CONSUMER_SURFACE`
- Consumer map returns `masked` → `UNKNOWN_CONSUMER_SURFACE`
- Multiple boundaries with conflicting outcomes → highest-wins dominance correct
- Proposal with no `boundaries` key → empty result (skip)
- `model_context` with grep-only evidence (no probe) → `BLOCKED_VALUE_UNVERIFIED`
- `NO_CHANGE` on unproven existing path → `BLOCKED_VALUE_UNVERIFIED`

#### Step 1.4 — Wire into preflight_propose.py

| Item | Detail |
|------|--------|
| **File** | `packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/preflight_propose.py` |
| **Change** | In the existing mechanism-change classification branch, after the step-9.x audit modules (`omission_audit`, `capability_claim_audit`), call `contract_value_renderer.render()`. Include the rendered outcomes in the preflight report. |
| **Warning mode env var** | `CONTRACT_VALUE_GATE_MODE` — `warning` (Phase 1 default) or `blocking` (Phase 2). In warning mode: render outcomes, append to report, never block. In blocking mode: render outcomes, `sys.exit(2)` if any outcome is blocking. |
| **Edge cases** | `CONTRACT_VALUE_GATE_MODE` unset → treat as `warning` (safe default). Renderer raises exception → log, append failure note to report, do not block (fail-open for quality gate). No `boundaries` key in proposal → skip, no report section. |

#### Step 1.5 — Global invariant sentence

| Item | Detail |
|------|--------|
| **File** | `.claude/hooks/mechanism_manifest.py` |
| **Change** | Add one paragraph: "Before recommending a new cross-component field, artifact, state path, or prompt injection, inspect and name its producer, transport/storage, behavioral consumer, authority, freshness, failure behavior, and real acceptance probe. Treat opaque transport as transport — not proof of value. Mark any unverified dependency as blocking before presenting the proposal." |
| **Test** | Unit test in `tests/test_mechanism_manifest.py` asserting the invariants string is present in `build_manifest()` output. This proves it reaches `/go` proposals. |

#### Step 1.6 — Frozen acceptance-test fixtures

| Fixture | File | Contents |
|---------|------|----------|
| `estimated_tokens` proposal | `packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/fixtures/estimated_tokens_proposal.json` | A Contract-and-Value section dict for the `EnhancementResult.estimated_tokens` field as it would have appeared at its introduction. Producer: `prompt_enhancer.py`. Consumer: `snapshot_v2.py` (opaque). No probe. Expected outcome: `ADVISORY_OPAQUE_ONLY`. |
| Referent inference proposal | `packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/fixtures/referent_inference_proposal.json` | Contract section for the deleted `resolve_referent` chain. Producer: `context.py`. Consumer: `model_context` (the LLM receives injection). No probe. Expected outcome: `BLOCKED_VALUE_UNVERIFIED`. |
| `Intent` removal proposal | `packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/fixtures/intent_removal_proposal.json` | Contract section for removing `clarified_intent` from `build_additional_context()`. Carrier: the `confirm` hook path. Expected outcome: `REMOVAL_REQUIRES_DEPENDENCY_PROOF` unless the dependency graph proves no path depends on it. |
| Safe local-surgical task | `packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/fixtures/local_surgical_task.json` | A proposal with no `boundaries` key. Expected outcome: empty result, no preflight invocation. |

#### Step 1.7 — Integration test: two concurrent terminals

| File | Change |
|------|--------|
| `tests/test_terminal_isolation.py` | Spawn two parallel subprocesses writing run-scoped evidence artifacts to separate session_ids. Verify each renderer call reads only its own scope. |

---

### Phase 2 — Preflight blocking mode

**Goal:** Flip the contract gate from advisory to blocking after calibration.

| Step | File | Change |
|------|------|--------|
| 2.1 | `preflight_propose.py` | Change default of `CONTRACT_VALUE_GATE_MODE` from `warning` to `blocking` once FP rate < 20% and FN count < 3/week over 2 weeks. |
| 2.2 | Acceptance test runner | Add a CI step that replays all frozen fixtures and asserts expected outcomes. Pact: every fixture must pass before the blocking flag is toggled. |

**Rollback:** Set `CONTRACT_VALUE_GATE_MODE=warning` in env. Reverts to Phase 1 behavior immediately. No code change needed.

---

### Phase 3 — PreToolUse schema gate

**Goal:** Block schema edits that add fields with zero verified consumers at edit time (Tier 1 enforcement).

#### Step 3.1 — Consumer map integration

**(Reuses Phase 1 Step 1.1).** No additional code — the `consumer_map.py` helper already exists.

#### Step 3.2 — PreToolUse gate

| Item | Detail |
|------|--------|
| **New file** | `.claude/hooks/PreToolUse_schema_consumer_gate.py` |
| **Pattern** | Mirror `PreToolUse_task_self_doc_gate.py` structure: `run(data) -> dict | None`. |
| **Trigger** | `tool_name` in (`Edit`, `Write`, `MultiEdit`) AND `tool_input.file_path` matches `*schemas*.py` or content contains `BaseModel` / `@dataclass`. |
| **Parsing** | Regex on the proposed diff (new lines starting with `    <name>:` after a class definition). Extract `field_name`. |
| **Verification** | For each `field_name`, call `consumer_map.build_consumer_map([field_name], [repo_root], exclude=[file, tests])`. |
| **Validation** | If the model provides a consumer path (in the tool_input or prior response), verify the file exists AND contains the field name via `rg -l field_name consumer_path`. If the claim is false → `BLOCKED_CONSUMER_UNVERIFIED`. |
| **Exemptions** | Check against typed list: `persistence-only`, `compatibility-only`, `diagnostic-only`, `future-public-api`, `external-consumer`. Proposer names the exemption type and provides evidence path (e.g. "artifact path at `.artifacts/*/prompt-enhancer/active_enhancement.json`"). Evidence path is NOT validated at edit time (too expensive) — logged for audit. |
| **Enforcement** | `consumer_map` returns no matches, no exemption given, no valid consumer cited → `{"decision": "block", "reason": "BLOCKED_CONSUMER_UNVERIFIED: new field <X> has no verified consumer. Cite file:function or use an exemption (persistence/compatibility/diagnostic/future-public-api/external-consumer)."}` |
| **Env var** | `SCHEMA_CONSUMER_GATE_MODE` — `warning` (Phase 3 default) or `blocking`. |

**Tests** (`tests/test_schema_consumer_gate.py`):
- Edit adding a field that already has a consumer → allow
- Edit adding a field with zero consumers, no cited path → block
- Edit adding a field with zero consumers, cited path valid → allow
- Edit adding a field with zero consumers, cited path invalid (does not exist or does not contain field) → block
- Edit adding a field with valid persistence exemption → allow
- Gate disabled via env var → allow
- Edit on a non-schema file (e.g. README.md) → skip
- MultiEdit touching one schema file + one non-schema → only scan schema file
- Write creating a new schema file with new fields → block if no consumers
- Proposed diff parse: multiline field defs, type-annotated fields, implicit `Optional` fields

#### Step 3.3 — Wire into PreToolUse.py

| Item | Detail |
|------|--------|
| **File** | `.claude/hooks/PreToolUse.py` |
| **Change** | Register `PreToolUse_schema_consumer_gate.run` in the TOOL hooks section, before the task_self_doc_gate (so consumer check runs before creation validation). Same register-unless-disabled pattern: `schema_gate_enabled = os.environ.get("SCHEMA_CONSUMER_GATE_ENABLED", "true")`. |

---

### Plan-level dependencies

```
Phase 0  ─── no deps
Phase 1  ─── no deps (builds new modules)
Phase 2  ─── depends on Phase 1 calibration data + passing fixtures
Phase 3  ─── depends on consumer_map.py (Phase 1.1) but not on preflight
```

Phases 0 and 1 can be built in parallel. Phase 3 can start as soon as consumer_map.py is stable — does not need preflight calibration to complete.

### Windows / runtime constraints (explicit)

- repository-relative paths; no hardcoded `P:/...` registry values
- `pathlib`-based discovery, not shell path translation
- UTF-8 / Windows line-ending safe
- source-vs-plugin-cache authority respected (source canonical; see memory `plugin_bidir_sync_source_wins`)
- session/run-scoped evidence — no machine-wide "newest state" lookup (see memory `terminal_id_not_per_session`)
- read-only / fail-silent for unrelated sessions and prompts; fail-blocking for required contracts on error
- coverage grade `no_match` → `UNKNOWN_CONSUMER_SURFACE`, never implicit "no consumer exists"
- new gates run in **warning mode** for ≥2 weeks before blocking (see Rollout section for calibration metrics)
- `rg` dependency: if `ripgrep` is not on PATH, consumer_map returns `no_match` for all fields (honest ceiling, not silent skip); `SCHEMA_CONSUMER_GATE_MODE` controls whether this blocks or warns

## Historical Acceptance Tests (frozen fixtures)

Any implementation must be replayed against frozen fixtures before it ships:

| Incident | Required outcome | Fixture source | Notes |
|----------|------------------|----------------|-------|
| `estimated_tokens` addition | `BLOCKED_CONSUMER_UNVERIFIED` or `ADVISORY_OPAQUE_ONLY` | capture of the EnhancementResult schema at the PR that added the field | snapshot carrying the field is `opaque_carrier`, not behavioral consumption; if exempted as compatibility, must prove the old-snapshot version |
| Referent-inference proposal | must not pass `READY_TO_PROPOSE` — requires `BLOCKED_VALUE_UNVERIFIED` | frozen proposal from `git show e87dfc7^:packages/.../context.py` + the incident prompt "fix it directly" + the prior-turn transcript that produced the wrong anchor | liveness alone is insufficient; must demonstrate the probe contract was absent |
| `Intent` line removal | `REMOVAL_REQUIRES_DEPENDENCY_PROOF` | dependency graph of `build_additional_context()` showing the confirm-path test is the sole carrier of the destructive target | removal must prove all carriers accounted for; a negative test proving the confirm path breaks when the line is removed confirms correctness |

Additional cases (run each cycle):
- ordinary local-surgical task (e.g., fix a one-line bug): zero contract artifacts created
- two concurrent Windows terminals: isolated run-scoped evidence, no cross-talk
- stale/foreign run artifact: ignored silently (failure_direction = `fail_open`)
- `model_context` consumer with only grep evidence → `BLOCKED_VALUE_UNVERIFIED`
- consumer map returns `no_match` → `UNKNOWN_CONSUMER_SURFACE`, not implicit absence
- new gate env vars disable cleanly: `fail_open` on unknown/error for Tier 1; `block` for Tier 2
- consumer map grades from a codebase with dynamic Pydantic access → at least one `masked`

## Consequences

### Schema-additive, behavior-changing

This proposal is **schema-additive** (no existing schema or artifact fields change) but **behavior-changing** for proposers and hooks:

- Existing mechanism-change proposals gain a required Contract-and-Value section (previously absent).
- Existing schema edits that add fields without a verified consumer are now blocked by the PreToolUse gate.
- Ordinary local-surgical tasks are unaffected — no new fields, no extra prompts, no extra gate.

**Added:**
- Contract-and-Value section in `/go` mechanism-change preflight
- Decision-rule renderer with 8 outcomes (including `UNKNOWN_CONSUMER_SURFACE`)
- Behavioral probe contract with 10 required fields
- Consumer-map coverage-grade system (5 grades)
- `PreToolUse_schema_consumer_gate.py` with typed exemptions
- One global invariant sentence in `mechanism_manifest.py`
- Frozen acceptance-test fixtures for the three incidents
- Failure-direction enum per boundary with 9 error classes

**Removed (from v1 of this ADR, never shipped):**
- The `CROSS_COMPONENT_CONTRACTS` dict proposal
- The claim that `behavioral` proves value unconditionally
- The implicit completeness assumption in consumer maps
- The "backwards compatible" label
- The ambiguous injection location ("or standing instructions")

**Cost:** preflight runs only on mechanism-change-classified tasks; the PreToolUse gate runs a cross-file grep per schema edit. No always-on injection overhead on ordinary prompts. No new runtime dependency.

## Rollout (phased, with metrics)

### Phase 0 — perf hook narrowing (pre-requisite)
Narrow the perf-attribution Stop hook trigger to concrete system timings/throughput/experiment IDs; exempt rhetorical tool-speed statements. Filed as task #1443. Removes a live friction source before adding new gates.

### Phase 1 — warning mode, data collection
Preflight contract section + decision rules run read-only. No blocking. Collect real violations for ~2 weeks.

**Calibration metrics (required before Phase 2 can start):**

| Metric | Definition | Who labels | Promotion threshold |
|--------|------------|------------|---------------------|
| FP (false positive) | a boundary flagged as having no consumer/value when a real consumer/value exists and would have been discoverable with reasonable effort | Decider reviews sample of violations weekly | FP rate < 20% over at least 30 flagged boundaries before moving to Phase 2 |
| FN (false negative) | a boundary that should have been flagged but was not (discovered retroactively) | Decider, during incident review | FN count < 3 per week before moving to Phase 2 |
| `ADVISORY_OPAQUE_ONLY` overrides | boundaries flagged as opaque-only that the proposer successfully exempted (persistence/compatibility/diagnostic) | Decider | Track — no promotion threshold; used to tune exemption taxonomy |
| `UNKNOWN_CONSUMER_SURFACE` share | boundaries where consumer map returned `no_match` or `masked` | Automatic | Track — high share triggers a tree-sitter upgrade |

### Phase 2 — blocking mode, calibrated
Flip preflight to blocking once:
- Historical acceptance tests all pass (frozen fixtures).
- FP rate < 20% over ≥30 flagged boundaries.
- FN count < 3/week.

### Phase 3 — PreToolUse gate, warning then blocking
Same calibration cadence as Phases 1→2. Independent env-var gating.

Each phase is independently shippable and reversible (env-var gated, same pattern as existing hooks).

## Why Not the Other Solutions

**Hand-maintained consumer registry (`CROSS_COMPONENT_CONTRACTS` dict + inline annotations).** Rejected. It is the anti-pattern this ADR removes: a manually copied map drifts from the real source of truth and eventually injects falsehoods. *Compute, never hand-maintain.*

**Always-injected global catalog.** Rejected. Context bloat degrades reasoning on unrelated prompts; the signal is noise outside design/refactor tasks; and a catalog cannot mechanically evaluate a not-yet-proposed field. Inject only the one-sentence invariant globally; inject detail task-scoped.

**Liveness checker as the headline fix.** Demoted to an implementation detail of the PreToolUse gate. Liveness catches dead fields (Tier 1) but is silent on wrong signals (Tier 2). Treating it as the root-cause fix would have caught `estimated_tokens` and missed the referent bug — the more important failure.

**Adopt OPA/Conftest now.** Deferred. A narrow Python validator suffices until the decision-rule set grows past ~12 rules.

**Adopt Spec Kit / OpenSpec wholesale.** Declined. Both overlap `/go`'s existing classification and preflight. Borrow OpenSpec's proposal-artifact shape; do not replace `/go`.

## Verification

```bash
# 1. Replay acceptance tests — all three incidents produce their required outcome against frozen fixtures.
# 2. Ordinary local-surgical task: preflight not invoked, no extra context injected.
# 3. Two concurrent terminals: isolated run-scoped evidence; no cross-talk.
# 4. Foreign/stale run artifact: failure_direction = fail_open, ignored silently.
# 5. model_context consumer with only grep evidence: BLOCKED_VALUE_UNVERIFIED.
# 6. opaque_carrier-only consumer with no exemption: ADVISORY_OPAQUE_ONLY (rejected unless exemption proven).
# 7. Consumer map with no matches: UNKNOWN_CONSUMER_SURFACE, not implicit "no consumer."
# 8. NO_CHANGE on an unproven existing mechanism: BLOCKED_VALUE_UNVERIFIED, not skip.
# 9. Consumer map on dynamic-attribute-heavy codebase: at least one masked grade returned.
#10. PreToolUse gate with model-proposed consumer path that does not exist: blocked.
```

## Follow-Up

- If the decision-rule set grows beyond ~12 rules or becomes hard to express in Python, revisit OPA/Conftest.
- If the `UNKNOWN_CONSUMER_SURFACE` share stays high after Phase 1, upgrade consumer map from grep to tree-sitter.
- After the gate is live and calibrated, sweep the existing codebase once for Tier-1 dead fields (`opaque_carrier`-only with zero `proves_executable_use` or `model_context` readers) as a one-off cleanup.
- Link this ADR from the Plugin Mutation Checklist (step 6) so schema/artifact changes route through the contract section.
- Build the `measured_tp_on_corpus` field into the PreToolUse gate's logging as a standing data-collection tool, even in warning mode — so we have real corpus data before the gate flips to blocking.
