---
thread_id: 7b2d6728-ff58-4c8d-aadd-0d9bd72f2adb
parent_handoff_path: none
current_session_id: 019fb0bd-b3a3-7600-87f7-9d56fa67cdac
current_terminal_id: grok-build-019fb0bd
produced_at: 2026-07-30T12:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 4de257ccaeb915f74a87637d380a4b528fde60d9
---

# A2b-3 Deferral Adapters — Corrected and Hermetically Proven

## Objective

Correct all 11 review areas for the A2b-3 deterministic deferral persistence adapters so they achieve `DEFERRAL_ADAPTERS_HERMETICALLY_PROVEN` and authorize static recipe simulation.

## Status

**READY_FOR_REVIEW** — Implementation complete, 118 A2b-3 tests pass, 34 A2b-2 and 46 A2b-1 regression tests pass. Review bundle prepared for the reviewing LLM. Awaiting verdict.

## Producing context

- Date: 2026-07-30
- Session: `019fb0bd-b3a3-7600-87f7-9d56fa67cdac`
- Terminal: `grok-build-019fb0bd`
- Part of: Semantic skill composition graph pilot (Phase A2b)

## Read-first list (ordered, with reasons)

1. `P:/tmp/pilot/a2b3/a2b3-characterization.md` — the completion report with all 16 required sections
2. `P:/tmp/pilot/a2b3/deferral_adapters.py` — corrected adapter source (all 11 fixes)
3. `P:/tmp/pilot/a2b3/test_a2b3.py` — 118 tests covering all required outcomes
4. `P:/tmp/pilot/a2b3/pytest-a2b3.txt` — full test output
5. `P:/tmp/pilot/a2b1/harvest_adapter.py` — extended to forward complete metadata
6. `C:/Users/brsth/.grok/skills/tasks/scripts/tasks.py` — production source with `_reconciled_existing` receipt field
7. `P:/tmp/pilot/a2b3/review-bundle-a2b3.md` — concatenated bundle for reviewer upload

## Verified facts (with source paths)

- [FACT] 118 A2b-3 tests pass (`pytest-a2b3.txt`: `118 passed in 16.38s`)
- [FACT] 34 A2b-2 tests pass (`pytest-a2b2.txt`: `34 passed in 4.35s`)
- [FACT] 46 A2b-1 tests pass (`pytest-a2b1.txt`: `46 passed in 27.49s`)
- [FACT] Production tasks.py modified with `_reconciled_existing` receipt field at lines 207, 250 (`tasks.py` read back and verified)
- [FACT] All 11 correction areas implemented: locator binding, idempotency material, harvest metadata, concurrency-safe injection, authoritative task receipt, table-driven blocking, crash recovery per backend, concurrency per backend, common validation, live-store isolation, scope preservation
- [FACT] Live-store isolation proven: recursive SHA-256 snapshots of production task, harvest, and artifacts roots unchanged before/after (tests `TestLiveStoreIsolation`)
- [INFERENCE] The `~/.grok` repo has a pre-existing unresolved merge conflict in `close_accounting.py` that prevented committing the tasks.py change — the change is persisted to disk and verified but not committed

## Current state

### What's done
- All 11 correction areas implemented in `deferral_adapters.py`
- 118 tests covering: locator binding (8), blocking (40 parametrized), idempotency distinctions (8), task metadata (3), harvest metadata (3), task receipt truth (2), crash recovery per backend (5), concurrency per backend (5), harvest root serialization (4), common validation (18 parametrized), strategy validation (5), live-store isolation (4), scope preservation (6), successful persistence (7)
- Production `create_task()` extended with non-breaking `_reconciled_existing` boolean receipt field
- Harvest adapter extended to forward complete metadata contract (session_id, check_run_id, destination, persistence_strategy, evidence_reference, follow_up_skill, harvest_rationale, harvest_authorized)
- Review bundle concatenated for single-file upload

### What's not done
- Production tasks.py change not committed (pre-existing git conflict in `~/.grok` repo blocks commits)
- Static recipe simulation not started (authorized to begin after verdict)

## Task packets

### PKT-1: Upload review bundle to reviewing LLM
- **Goal:** Get the reviewing LLM's verdict on the corrected A2b-3 adapters
- **In scope:** Upload `P:/tmp/pilot/a2b3/review-bundle-a2b3.md` (399KB) or the individual files listed in the characterization
- **Out of scope:** Implementing any further corrections until the verdict is received
- **Acceptance:** Reviewing LLM returns `DEFERRAL_ADAPTERS_HERMETICALLY_PROVEN` or specifies remaining corrections
- **Verification:** Reviewing LLM's response

### PKT-2: Commit production tasks.py change
- **Goal:** Resolve the `~/.grok` repo merge conflict and commit the `_reconciled_existing` field addition
- **In scope:** `C:/Users/brsth/.grok/skills/tasks/scripts/tasks.py`
- **Out of scope:** Any other changes in the conflicted repo
- **Acceptance:** `git log --oneline -1 -- skills/tasks/scripts/tasks.py` shows the commit
- **Verification:** `python -c "import tasks; print(tasks.create_task.__doc__)"` from the tasks scripts dir

### PKT-3: Begin static recipe simulation (Phase C)
- **Goal:** After verdict, begin the static recipe simulation phase
- **In scope:** TBD per design doc `P:/docs/semantic-skill-composition-graph-design-20260730.md`
- **Out of scope:** Production caller integration
- **Acceptance:** TBD per design doc
- **Verification:** TBD

## Open decisions

### Decision 1: Should the `_reconciled_existing` field be stripped before persisting to disk?
- **Question:** The field is added to the in-memory dict and persists to the JSON file. Should we `del task["_reconciled_existing"]` before `_atomic_write_json()`?
- **Options:** (A) Keep it in the file (informational metadata), (B) Strip it before write (clean schema)
- **Current lead:** (B) Strip it — the field is a transient receipt, not part of the task schema
- **Evidence needed:** Reviewing LLM's opinion on schema cleanliness

## Hard constraints

1. All adapters are pilot-only — no production caller integration
2. No classification, destination choice, /aar vs /debrief choice, value scoring, prioritization, or workflow routing in the adapters
3. Production roots must remain unchanged (proven by live-store isolation tests)

## Cross-reference couplings

- `P:/tmp/pilot/a2b3/deferral_adapters.py` → imports from `a2a/canonical.py`, `a2b1/harvest_adapter.py`, `a2b2/check_run_locator.py`, production `tasks.py`. If any of these change their interfaces, the adapter breaks.
- `C:/Users/brsth/.grok/skills/tasks/scripts/tasks.py` → production source. The `_reconciled_existing` field is consumed by `_persist_task()` in the adapter. If the field name changes, the adapter silently falls back to `False`.
- `P:/tmp/pilot/a2b1/harvest_adapter.py` → extended `write_event_with_idempotency()` signature. The A2b-1 tests (46) still pass, confirming backward compatibility.

## Other outstanding streams (not handed off)

- **Transcript prompt analysis and skill design** — separate handoff at `transcript-prompt-analysis-skill-design-20260730`
- **Semantic skill composition graph design** — ongoing multi-session effort, design doc at `P:/docs/semantic-skill-composition-graph-design-20260730.md`

## Explicit non-goals

- Do NOT begin static recipe simulation until the reviewing LLM returns a verdict
- Do NOT integrate adapters into any production caller
- Do NOT modify the locator (A2b-2) or the transaction foundation (A2a)

## Resumption protocol

1. Read the characterization: `P:/tmp/pilot/a2b3/a2b3-characterization.md`
2. Upload the review bundle to the reviewing LLM: `P:/tmp/pilot/a2b3/review-bundle-a2b3.md`
3. If verdict is `HERMETICALLY_PROVEN`, begin Phase C (static recipe simulation) per the design doc
4. If corrections needed, implement them in `deferral_adapters.py` and `test_a2b3.py`

## Suggested next invocation

```
The reviewing LLM returned [verdict]. [If PROVEN: Begin Phase C static recipe simulation per the design doc. If corrections: implement the specified corrections.]
```

## Last user message (verbatim)

> "we've compacted the session so you have LOTS of context window available. /go do the plan."

## Epistemic labels per claim

- All test counts: `[FACT]` (cited from pytest output files)
- Production change verification: `[FACT]` (file read back at specific lines)
- Git conflict blocking: `[FACT]` (git commit command failed with merge conflict error)
- "Static recipe simulation authorized": `[INFERENCE]` — based on characterization verdict, pending reviewer confirmation
