# ADR-007: Pre-Proposal Contract-and-Value Gate for Cross-Component Mechanism Changes

**Date:** 2026-07-11
**Status:** Proposed
**Decider:** Bruce Thomson

## Context and Problem Statement

Three incidents in a single session shared one root cause: **architectural hypotheses were promoted to code without evidence of real-world value.**

1. **`estimated_tokens`** (prompt-enhancer `EnhancementResult`) — a field added on the assumption the model would use it "for context budget tracking." Lived 10+ plugin versions. Zero production consumers ever read the value. Snapshot carried it as an opaque blob; no code inspected it.
2. **Referent inference** (`resolve_referent` / `extract_subject` in deleted `context.py`) — a pronoun-resolution chain built on the assumption "first file reference in the prior prompt = discourse subject." One confirmed false positive (`"fix it directly"` → `console_*.jsonl`). Entire chain deleted.
3. **`Intent` line** (`build_additional_context`) — initially classified as dead-weight restatement. Source inspection revealed it is the sole carrier of the destructive target on the `confirm` hook path, asserted by `test_confirm_has_additional_context`. Near-miss removal.

The common anti-pattern: a developer (human or LLM) writes field/mechanism A on component 1, *imagines* component 2 will use it, ships both, and nobody ever verifies whether component 2 actually reads A — or whether the signal A produces is correct.

### What an initial proposal got wrong

A first-pass fix proposed a hand-maintained `CROSS_COMPONENT_CONTRACTS` dict in `mechanism_manifest.py` plus inline consumer annotations in `schemas.py`. Three independent reviewers (Perplexity, Z.ai, OpenAI) unanimously rejected it: **a hand-maintained registry is the exact "architect intent instead of measurement" anti-pattern this ADR exists to remove.** It drifts, and injecting a stale registry into the model's prompt is worse than injecting nothing.

### The deeper finding (liveness ≠ value)

OpenAI's review identified the critical gap any consumer-registry design must confront: **field liveness is necessary but insufficient.** The referent-inference chain was fully "live" — producer existed, the model consumed the injected context, storage and hook path existed. The defect was that the *signal was wrong*. No grep-based consumer check catches a wrong signal.

This is acute when the consumer is an LLM (`model_context` consumer): grep cannot prove consumption at all, because the "reader" is the model's reasoning over injected text. Only a behavioral probe (real-corpus TP/FP) can.

Therefore the problem has two tiers:
- **Tier 1 (cheap, structural):** dead fields — no reader exists. Solvable by static liveness.
- **Tier 2 (hard, behavioral):** live-but-wrong signals — reader exists, value unproven or negative. Solvable only by evidence scaled to consumer type.

Any gate that stops at Tier 1 would have caught `estimated_tokens` and sailed past the referent bug. This ADR addresses both tiers.

## Decision

Add a **task-scoped, pre-proposal Contract-and-Value Review** to the existing `/go` mechanism-change preflight path, plus a narrow **PreToolUse schema-field gate** for edit-time enforcement. Reject any design that relies on a hand-maintained consumer registry.

Two principles govern the design:

1. **Compute, never hand-maintain.** Any producer→consumer map is derived at runtime from the source tree (grep / tree-sitter), or it does not exist. There is no `CROSS_COMPONENT_CONTRACTS` dict.
2. **Evidence scales with consumer type.** Existence of a reader is the floor, not the ceiling. When the consumer is an LLM or another behavioral boundary, a real probe is required — grep does not count.

## Consumer-Type Taxonomy

Not all "consumers" prove value. Every consumer must be classified before it counts:

| Type | Proves value? | Example in this codebase |
|------|---------------|--------------------------|
| `behavioral` | Yes — code reads the value and changes behavior | hook gates injection on `confidence` |
| `model_context` | Conditionally — requires a behavioral probe (TP/FP on real corpus) | `additionalContext` injected into the prompt |
| `opaque_carrier` | No — transports the value without interpreting it | snapshot captures/restores `prompt_enhancement` |
| `persistence` | No — stores or restores data | `active_enhancement.json` on disk |
| `policy_boundary` | No — recognizes the container/key, not field contents | `FORBIDDEN_POLICY_KEYS` denylist |
| `diagnostic` | No — human/observability inspection only | a log field |
| `compatibility` | No — accepted to preserve schema shape for old readers | a field kept for roundtrip safety |

Only `behavioral` unconditionally proves value. `model_context` proves value only with an accompanying behavioral probe. The other five establish liveness but **not** value — and must be labeled as such.

This single distinction is what separates "snapshot carried `estimated_tokens`" from "something used `estimated_tokens`."

## The Contract-and-Value Section (Tier 1 + Tier 2)

Extends `/go` preflight (`preflight_propose.py`). Triggered only when a candidate would add, modify, or remove:

- persisted or shared state
- a schema or artifact field
- a registry or whitelist entry
- cross-plugin / cross-component data flow
- hook-provided `additionalContext`
- identity, freshness, authority, or cache state

For every affected boundary, the proposal must populate:

```yaml
boundary_id:        <stable id>
change_kind:        add | modify | remove

value_claim:        <observable outcome that should improve>
producer:           <file:function that creates the value>
transport_or_storage: <artifact | hook payload | prompt injection | cache | file | API>
consumer:           <file:function or model-context boundary>
consumer_type:      behavioral | model_context | opaque_carrier |
                    persistence | policy_boundary | diagnostic | compatibility
authority:          <source authoritative when sources disagree>
identity_scope:     <session_id | run_id | task_id | repo/worktree>
freshness_and_versioning: <how stale data / old schemas are detected>
failure_direction:  <what happens if producer/artifact/consumer absent,
                    malformed, stale, foreign-session, or incompatible>
existing_mechanism: <current mechanism inspected, and why it cannot satisfy the goal>
evidence:           <source inspection proving the current path>
acceptance_probe:   <real runtime evidence that would prove the value claim>
falsifier:          <concrete result that would show the mechanism is
                    ineffective or harmful>
```

Stored in the **existing run-scoped proposal/discovery artifact** under the current `run_id`, bound by the same `session_id` discipline `/go` already uses. No new global registry.

## Decision Rules

The preflight renderer emits exactly one outcome per boundary:

| Outcome | Meaning |
|---------|---------|
| `NO_CHANGE` | an existing mechanism already satisfies the requirement |
| `READY_TO_PROPOSE` | producer, path, consumer, authority, and verification are grounded |
| `BLOCKED_CONSUMER_UNVERIFIED` | a consumer is merely assumed |
| `BLOCKED_VALUE_UNVERIFIED` | a `model_context`/`behavioral` claim lacks a real probe |
| `BLOCKED_AUTHORITY_UNKNOWN` | source, identity, or freshness authority is unresolved |
| `ADVISORY_OPAQUE_ONLY` | the only "consumer" transports/preserves the value but does not use it |
| `REMOVAL_REQUIRES_DEPENDENCY_PROOF` | all readers, carriers, registrations, tests, docs, and compatibility paths have not been checked |

A blocking outcome withholds the **mechanism proposal**, not the entire unrelated task.

## Edit-Time Enforcement (PreToolUse schema gate)

To act *before* code is written — not only before the proposal is shown — add a narrow `PreToolUse` gate modeled on the existing `PreToolUse_task_self_doc_gate.py` pattern.

- **Trigger:** `Edit`/`Write`/`MultiEdit` on files matching `schemas.py` or containing Pydantic `BaseModel` / `@dataclass` definitions.
- **Action:** parse the proposed diff for newly added field definitions.
- **Verification:** for each new field, run a source-tree grep (excluding the edited file and tests) for the field name.
- **Enforcement:** if zero non-test readers are found, return a blocking decision requiring the model to name the intended consumer (file:line) or justify the producer-only status.

This is the "before work is done" lever. It is deliberately Tier-1 only — it cannot evaluate signal quality, only liveness. Tier 2 remains the preflight's job.

## Global Injection

One invariant sentence in `mechanism_manifest.py` (or standing instructions). Nothing else injected globally:

> Before recommending a new cross-component field, artifact, state path, or prompt injection, inspect and name its producer, transport/storage, behavioral consumer, authority, freshness, failure behavior, and real acceptance probe. Treat opaque transport as transport — not proof of value. Mark any unverified dependency as blocking before presenting the proposal.

No catalog, no table, no per-field registry. Detailed facts are discovered from the task's actual source tree at preflight time.

## Implementation

| Component | Location | Notes |
|-----------|----------|-------|
| Contract-and-Value section | extend `preflight_propose.py` (`cc-skills-sdlc/skills/go/scripts/`) | sibling to `omission_audit.py`, `capability_claim_audit.py` |
| Decision-rule renderer | new module in same `scripts/` dir | wired into `orchestrate.py run_common_tail` per the step-9.x pattern |
| PreToolUse schema gate | new `PreToolUse_schema_consumer_gate.py` | registered in `PreToolUse.py` UNIVERSAL/TOOL hooks |
| Runtime consumer map | helper, grep-based initially; tree-sitter if grep proves insufficient | computed, never stored |
| Global invariant | one line in `mechanism_manifest.py` | replaces any catalog-style injection |

**Windows / runtime constraints (must be handled explicitly):**
- repository-relative paths; no hardcoded `P:/...` registry values
- `pathlib`-based discovery, not shell path translation
- UTF-8 / Windows line-ending safe
- source-vs-plugin-cache authority respected (source canonical; see memory `plugin_bidir_sync_source_wins`)
- session/run-scoped evidence — no machine-wide "newest state" lookup (see memory `terminal_id_not_per_session`)
- read-only / fail-silent for unrelated sessions and prompts
- new gates run in **warning mode** for ~2 weeks before blocking (see Rollout)

## Historical Acceptance Tests

Any implementation must be replayed against the three incidents before it ships:

| Incident | Required outcome |
|----------|------------------|
| `estimated_tokens` addition | `BLOCKED_CONSUMER_UNVERIFIED` — snapshot carrying the field is `opaque_carrier`, not behavioral consumption |
| Referent inference proposal | not approved on liveness alone — requires a real transcript corpus, TP/FP measurement, compaction cases, and a falsifier for wrong-anchor injection (`BLOCKED_VALUE_UNVERIFIED` otherwise) |
| `Intent` line removal | held under `REMOVAL_REQUIRES_DEPENDENCY_PROOF` until the confirm-path hook and its test establish whether the line is the sole carrier of the destructive target |

Additional cases: ordinary local-surgical tasks receive no contract review and no extra noise; two simultaneous Windows terminals produce isolated review evidence; stale/foreign run artifacts are ignored; grep alone cannot satisfy `model_context` consumer evidence.

## Why Not the Other Solutions

**Hand-maintained consumer registry (`CROSS_COMPONENT_CONTRACTS` dict + inline annotations).** Rejected unanimously. It is the anti-pattern this ADR removes: a manually copied map drifts from the real source of truth and eventually injects falsehoods. The environment has already learned this lesson (hardcoded registry shims become brittle when the real authority lives elsewhere). *Compute, never hand-maintain.*

**Always-injected global catalog.** Rejected. Context bloat degrades reasoning on every unrelated prompt; the signal is noise outside design/refactor tasks; and a catalog cannot mechanically evaluate a not-yet-proposed field. Inject only the one-sentence invariant globally; inject detail task-scoped.

**Liveness checker as the headline fix.** Demoted to an implementation detail of the PreToolUse gate. Liveness catches dead fields (Tier 1) but is silent on wrong signals (Tier 2). Treating it as the root-cause fix would have caught `estimated_tokens` and missed the referent bug — the more important failure.

**Adopt OPA/Conftest now.** Deferred. A narrow Python validator in `preflight_propose.py` suffices until the policy set grows. Revisit only if the decision-rule set becomes hard to maintain in pure Python.

**Adopt Spec Kit / OpenSpec wholesale.** Declined. Both overlap `/go`'s existing classification and preflight. Borrow OpenSpec's proposal-artifact shape; do not replace `/go`.

## Consequences

**Added:**
- Contract-and-Value section in `/go` mechanism-change preflight
- Decision-rule renderer with seven outcomes
- `PreToolUse_schema_consumer_gate.py` (warning mode first)
- One global invariant sentence

**Removed:**
- The (never-shipped) `CROSS_COMPONENT_CONTRACTS` dict proposal
- Any future hand-maintained per-field consumer registry

**Cost:** preflight runs only on mechanism-change-classified tasks; the PreToolUse gate runs a grep per schema edit. No always-on injection overhead on ordinary prompts. No new runtime dependency.

**Backwards compatible:** purely additive for proposers; no existing schema or artifact changes required. Existing mechanism-change tasks gain a required section; ordinary tasks are unaffected.

## Rollout (phased)

1. **Narrow the perf-attribution Stop hook trigger** — restrict to concrete system timings/throughput/experiment IDs; exempt rhetorical tool-speed statements. (Separate fix; already filed as task #1443. Removes a live friction source before adding new gates.)
2. **Preflight contract section + decision rules, warning mode.** Run read-only for ~2 weeks; collect real violations; tune the consumer-type classifier and the opaque-carrier heuristic.
3. **Flip preflight to blocking** once the historical acceptance tests pass and the FP rate is acceptable.
4. **PreToolUse schema gate, warning mode**, then blocking, on the same calibration cadence.

Each phase is independently shippable and reversible (gates are env-var-gated, same as existing hooks).

## Verification

```bash
# 1. Replay acceptance tests — all three incidents produce their required outcome.
# 2. Ordinary local-surgical task: preflight not invoked, no extra context injected.
# 3. Two concurrent terminals: isolated run-scoped evidence; no cross-talk.
# 4. Foreign/stale run artifact: ignored silently.
# 5. model_context consumer with only grep evidence: BLOCKED_VALUE_UNVERIFIED.
# 6. opaque_carrier-only consumer: ADVISORY_OPAQUE_ONLY.
# 7. New gate env vars disable cleanly (fail-open on unknown/error per existing convention).
```

## Follow-Up

- If the decision-rule set grows beyond ~12 rules or becomes hard to express in Python, revisit OPA/Conftest.
- If grep proves insufficient for dynamic/Pydantic attribute access, migrate the runtime consumer map to tree-sitter (Aider repo-map pattern).
- After the gate is live and calibrated, sweep the existing codebase once for Tier-1 dead fields (`opaque_carrier`-only with zero behavioral readers) as a one-off cleanup — the same audit that found `estimated_tokens`.
- Link this ADR from the Plugin Mutation Checklist (step 6) so schema/artifact changes route through the contract section.
