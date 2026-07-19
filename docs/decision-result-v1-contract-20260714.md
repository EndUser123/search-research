# Immutable decision-result.v1 contract — 2026-07-14

## 1. Workspace/runtime state

The accepted upstream contracts are `decision-request.v1` and `research-result.v1`. The canonical research runtime is under `P:/tools/research_run_v1`; the canonical design skill is under `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/design`. The workspace is concurrently dirty with unrelated changes; those changes were preserved. No plugin cache or runtime command path was modified.

The current research input used for prospective validation is `P:/tmp/.codex/state/research-result-contract-20260714/research-result.json`. Its contents were validated before chain evaluation.

## 2. Existing decision artifacts and gaps

The design package already has ADR markdown, `DesignPayload`, `ContractAuthorityPacket`, claim verification, decision metrics, and planning-handoff concepts. These are output/review or persistence mechanisms, not one immutable decision result bound to an exact request and research corpus. Existing records also use implementation-specific decision IDs and conversational/ADR output patterns.

The missing boundary was a versioned result that records the selected outcome, rejected alternatives, accepted tradeoffs, unresolved evidence, approval state, and execution boundary without claiming approval or execution.

## 3. Proposed `decision-result.v1`

The artifact contains:

| Section | Purpose | Deliberate boundary |
|---|---|---|
| `identity` | Decision ID, exact request ID and request hash, creation time | Binds output to one request; does not infer “latest” |
| `context` | Objective, scope, constraints | Decision context snapshot; request hash remains authoritative |
| `decision` | Selected option, outcome, rationale | Records decision reasoning, not approval |
| `alternatives` | Considered options, rejected IDs, rejection reasons | Prevents rejected alternatives from disappearing |
| `tradeoffs` | Accepted/rejected tradeoffs and consequences | Makes costs visible; no scoring engine |
| `evidence` | Exact research-result refs, supporting/conflicting claims, confidence, unresolved questions | Evidence remains research-owned and uncertainty is mandatory |
| `risks` | Known risks, mitigations, accepted risks | Does not convert risk acceptance into approval |
| `authority` | Decision owner, approvals, approval state | Separates decision ownership from approval status |
| `execution_boundary` | Whether implementation/planning is required and blocked items | Does not execute, plan, or authorize `/go` |
| `provenance` | Source artifacts and consistency-checked hashes | Prevents mismatched duplicate references |

The validator rejects unknown top-level fields, malformed UUIDs/hashes, empty alternatives, missing rejection reasons, missing unresolved questions, invalid approval states, and absent execution boundaries. It also checks that the request hash and research hash lists agree across identity, evidence, and provenance.

## 4. Field authority model

| Field | Writer | Storage | Reader | Authority/freshness | Failure/acceptance evidence |
|---|---|---|---|---|---|
| Identity | Future design workflow or explicit decision producer | Immutable result JSON | Future planning/review consumers | Exact request identity and creation time | Invalid/mismatched identity blocks; binding tests |
| Context | Decision owner via request/design workflow | Result snapshot plus request hash | Design/review | Request is authoritative for original context | Missing context blocks; schema test |
| Decision | Design workflow/decision owner | Result artifact | Future planning and human review | Decision owner, not research provider | Missing rationale/outcome blocks; validation test |
| Alternatives/tradeoffs | Design workflow | Result artifact | Review/planning | Explicit human/workflow reasoning | Missing rejected reasons blocks; preservation test |
| Evidence | Research producer references, design records claim use | Result artifact references immutable research results | Design/review | `research-result.v1` and its source assessments remain authoritative | Hash mismatch blocks; research-result validation and chain test |
| Risks | Design workflow/decision owner | Result artifact | Review/planning | Explicit risk statements, not generic ceremony | Missing risk arrays blocks; schema test |
| Authority | Decision owner/governance process | Result artifact | Approval gate/human | Approval state is separate from decision | Invalid state blocks; authority test |
| Execution boundary | Design workflow | Result artifact | Planning/execution gate | Planning and implementation remain downstream | Missing flags/blocked items blocks; boundary test |
| Provenance | Contract writer from exact inputs | Immutable result artifact | All downstream consumers | Hashes are consistency checked, no newest-file heuristic | Mismatch blocks; hash-binding test |

## 5. Complete-chain evaluation

Evaluation artifact: `P:/tmp/.codex/state/decision-result-contract-20260714/evaluation.json`.

Ten scenarios were checked end to end:

1. adopt an agent framework;
2. choose persistence architecture;
3. build versus buy;
4. select an external provider;
5. migrate a component;
6. accept operational risk;
7. choose between repositories;
8. introduce a new workflow;
9. reject a proposed feature;
10. defer a decision because evidence is insufficient.

All 10 had valid decision requests, valid research-result references, valid decision results, preserved uncertainty, represented authority, and explicit execution separation.

Missing-information classification:

- 5 research gaps;
- 3 decision-context gaps;
- 1 execution-planning gap;
- 1 approval/authority gap.

The deferred scenario records a deliberate defer outcome with `confidence: insufficient`; it does not pretend that lack of evidence is a positive recommendation.

## 6. Verification

Focused contract suite:

```text
$env:PYTHONPATH='P:\'; pytest P:\tests\research_run_v1\test_decision_result.py P:\tests\research_run_v1\test_decision_request.py P:\tests\research_run_v1\test_research_result.py -q -p no:cacheprovider
25 passed
```

Canonical suite:

```text
108 passed, 3 failed
```

The three failures are unchanged router-policy corpus expectations:

- `test_phase1_role_policy_corpus_matches`;
- `test_healthy_provider_roles_are_automatic_without_per_call_approval`;
- `test_realistic_router_corpus_matches_expected_decisions`.

They are unrelated to this contract and were not fixed.

## 7. Files changed

- `P:/tools/research_run_v1/decision_result.py`
- `P:/tools/research_run_v1/evaluate_decision_result.py`
- `P:/tools/research_run_v1/__init__.py`
- `P:/tests/research_run_v1/test_decision_result.py`
- this report

## 8. Exact authorized behavior

The workspace may validate and immutably store a `decision-result.v1` artifact that records an explicit decision, rationale, rejected alternatives, tradeoffs, evidence references, uncertainty, authority state, and execution boundary. It may be consumed later by a separately authorized design/planning workflow.

## 9. Exact deferred behavior

Implementing `/design`, automatically generating decisions, changing ADR persistence, adding approvals, generating plans, executing implementation, integrating `/go` or `/search`, changing research/routing/providers/evidence assessment/provenance, Phase 2A automation, and invoking `agy` remain deferred.

## 10. Verdict

`PASS_DECISION_RESULT_CONTRACT`

The decision output boundary is defined, hash-bound, immutable, tested, and evaluated across the complete request → research → decision chain. This does not mean `/design` exists, that a decision is approved, or that execution occurred.
