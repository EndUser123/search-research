# Research-to-design handoff contract — 2026-07-14

## 1. Goal and decision

This increment defines and validates an immutable `research-result.v1` projection for a future `/design` consumer. It does not implement `/design`, change `/research` routing, add providers, or authorize a decision. The existing `research-run.v1` execution artifact remains the source of truth for execution evidence.

## 2. Scope and inspected revisions

Inspected the canonical `/research` source at `P:/packages/.claude-marketplace/plugins/search-research`, the runtime under `P:/tools/research_run_v1`, and the canonical tests under `P:/tests/research_run_v1`. The workspace root was at `7d8e103927d5a5dd47099a1e2e9fbd2d4ec52d38`; the search-research package had pre-existing dirty changes and was not modified in this increment. The current real smoke input was `P:/tmp/.codex/state/research-run-v1/743907c5-9ac8-4f21-8eaf-0e3b9f6a6717/research-run.json`.

The historical Phase 2A raw artifact was previously lost and cannot be reconstructed. This contract does not backfill or reinterpret it.

## 3. Existing artifact analysis

`research-run.v1` already preserves the research question, requested decision, authorization level, runtime, retrieval lanes, source identities and discovery statuses, claims, assessments, uncertainty, stop reason, routing telemetry, and failures. It is an execution/provenance record. It is not a suitable direct design input because it mixes internal routing/runtime detail with consumer-facing evidence and contains no explicit decision boundary.

The smoke run had five Exa results, two opened sources, no claim-specific findings, and an insufficient quality stop. The projection therefore produces zero options and explicit unresolved evidence; it does not manufacture a recommendation.

## 4. `research-result.v1` contract

The projection contains:

| Field | Meaning | Decision boundary |
|---|---|---|
| `context` | Question, requested decision, scope, constraints, assumptions | Describes the problem; does not choose an answer |
| `evidence_requirements` | Required/fulfilled capabilities and unresolved requirements | Shows what evidence is still missing |
| `findings` | Claim statements, statuses, confidence, source IDs, assessment IDs, limitations | Evidence claims only; no decision record |
| `options` | Explicitly known options, if a producer supplied them | Empty when absent; never inferred |
| `risks` | Uncertainty and evidence risks | Research risk, not a design decision |
| `unresolved_questions` | Missing evidence and open questions | Must remain visible to the downstream consumer |
| `provenance` | Run ID, artifact hash, workspace revision, sources, assessments, lanes, failures | Binds every finding back to the run evidence |
| `stopping` | Quality stop status, reason, and measured runtime where available | Explains why research ended |
| `authorization` | Research may recommend, but may not decide | Downstream consumer owns decision authority |

The result is validated independently and stored with exclusive creation. A second write to the same path fails rather than overwriting the prior result.

## 5. Authority model

| Boundary field | Writer | Storage | Reader | Authority/freshness | Failure and acceptance evidence |
|---|---|---|---|---|---|
| Run identity and context | `build_research_result()` from validated run | Immutable JSON result sidecar | Future `/design` | Original run; run-scoped timestamps and workspace revision | Missing identity fails validation; fixture round-trip test |
| Findings | Existing validated claims projected by the runtime module | Same sidecar | Future `/design` | Claim status is authoritative only to the extent of source/assessment evidence | Unknown claims remain unresolved; provenance test |
| Sources and assessments | Existing Phase 1 execution and assessment paths | Embedded provenance plus original run | Future `/design` or reviewer | Original source IDs, locations, assessment relationships, and run ID | Missing provenance fails validation; source preservation test |
| Requirements and unresolved evidence | Existing routing/quality fields plus uncertainty | Embedded result | Future `/design` | Fresh for this immutable run | Missing requirements are explicit; unresolved-evidence test |
| Options and decisions | No writer in this increment | Empty `options`; no decision field | Future `/design` | No research authority to invent or select | Decision-field injection is rejected; separation test |
| Result file | Contract writer using exclusive create | Run-specific artifact directory | Validator and future consumer | Immutable once written | Duplicate write test proves no overwrite |

The future `/design` consumer must treat the result as evidence input, re-check whether unresolved requirements matter to its decision, and write its own decision artifact. No `/design` reader currently exists in the inspected research package; that is intentionally deferred.

## 6. Ten representative future design inputs

The evaluation artifact is `P:/tmp/.codex/state/research-result-contract-20260714/contract-evaluation.json`. All ten cases preserved context, provenance, and claim/decision separation. All ten correctly required more evidence or downstream option definition because the real smoke run had unresolved evidence and no options:

1. agent framework selection
2. cross-session persistence architecture
3. provider adoption
4. local/web retrieval choice
5. process lifecycle and cleanup ownership
6. research schema migration
7. build versus buy for extraction
8. credential and workspace isolation
9. latency and quota budget
10. limited-pilot readiness

This is the intended result: the handoff improves decision quality by making evidence and gaps reusable without pretending that research made the design decision.

## 7. Verification

Focused contract tests: `7 passed`.

```text
$env:PYTHONPATH='P:\'; pytest P:\tests\research_run_v1\test_research_result.py -q -p no:cacheprovider
7 passed in 0.22s
```

The canonical suite was then run. It remains `90 passed, 3 failed`; the three failures are pre-existing router-policy corpus expectations (`test_phase1_role_policy_corpus_matches`, `test_healthy_provider_roles_are_automatic_without_per_call_approval`, and `test_realistic_router_corpus_matches_expected_decisions`). They do not exercise this contract and were not changed.

## 8. Changed files

- `P:/tools/research_run_v1/research_result.py`
- `P:/tools/research_run_v1/evaluate_research_result_contract.py`
- `P:/tools/research_run_v1/__init__.py`
- `P:/tests/research_run_v1/test_research_result.py`
- this report

No plugin cache, command topology, routing policy, provider set, `/go`, `/search`, Phase 2A, or `agy` path was changed.

## 9. Authorized behavior

The runtime may project a validated `research-run.v1` into an immutable evidence-only `research-result.v1` artifact for later human or future design consumption. The result may support a recommendation by a downstream consumer but cannot authorize implementation or claim that a decision was made.

## 10. Deferred behavior

Implementing `/design`, consuming the result automatically, defining a decision/ADR schema, adding options from inference, routing changes, provider expansion, Phase 2A automation, and `/go` integration are deferred. The future consumer must be added only with its own authority, freshness, failure, and acceptance tests.

## 11. Verdict

`PASS_RESEARCH_DESIGN_CONTRACT`

The contract boundary is implemented and tested, including backward-compatible projection from existing runs, provenance preservation, explicit unresolved evidence, decision separation, and immutable storage. This verdict means the handoff contract is ready for a separately authorized `/design` implementation; it does not mean `/design` exists or that research can decide.
