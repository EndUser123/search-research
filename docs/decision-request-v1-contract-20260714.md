# Decision intake contract — 2026-07-14

## 1. Goal and current state

This increment defines the minimum durable input boundary for a future `/design` workflow. It preserves the accepted separation:

```text
research ≠ decision
evidence ≠ recommendation
recommendation ≠ approval
design choice ≠ execution
```

The existing chain remains:

```text
question → /research → research-result.v1 → future /design → decision
```

No `/design` behavior was implemented or changed.

## 2. Workspace/runtime state and inspected authority

Inspected the canonical `cc-skills-sdlc` design skill at `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/design`, its `schemas.py`, validation tests, ADR resources, planning handoff parsers, `/go` routing references, and the existing `research-result.v1` implementation under `P:/tools/research_run_v1`.

Verified existing concepts:

- `/design` has an existing `DesignPayload`, ADR markdown validation, `ContractAuthorityPacket`, claim-verification fields, and optional planning handoff.
- `contract-primitives` already parses contract-authority and planning-handoff packets.
- Existing documentation says there is no persistent DecisionRecord consumer.
- `research-result.v1` is the evidence-only upstream artifact and already carries run identity, sources, assessments, failures, workspace revision, and artifact hash.

The proposed `decision-request.v1` is therefore an intake boundary, not a replacement for the existing design output payload or ADR format. No current runtime reader consumes it yet.

Discovery reports were run over the research runtime/tests and the canonical design skill. They found no conflicting decision-request owner; the workspace remains heavily dirty from unrelated work and those changes were preserved.

## 3. Current gaps

The existing design payload describes design output and review evidence, but does not provide a stable, validated input that names the decision owner, constraints, explicit alternatives, evidence dependency, and approval boundary before design reasoning begins.

Without this boundary, a future workflow could:

- treat a research recommendation as an approval;
- invent constraints or options from an incomplete research result;
- silently broaden research instead of reporting an evidence gap;
- mix implementation sequencing into the architecture decision;
- lose the exact research run that informed the decision.

## 4. Proposed `decision-request.v1`

```json
{
  "schema_version": "decision-request.v1",
  "request_id": "UUID",
  "created_at": "ISO-8601",
  "decision_context": {
    "objective": "string",
    "desired_outcome": "string",
    "decision_type": "architecture | technology_selection | migration | workflow | operational_risk | build_or_buy | provider_strategy",
    "scope": "string"
  },
  "constraints": {
    "technical": ["string"],
    "operational": ["string"],
    "compatibility": ["string"],
    "cost": ["string"],
    "timeline": ["string"],
    "reversibility": ["string"]
  },
  "options": {
    "considered": [{"option_id": "string", "label": "string"}],
    "excluded": ["string"],
    "alternatives": ["string"]
  },
  "priorities": {
    "reliability": "string",
    "simplicity": "string",
    "performance": "string",
    "maintainability": "string",
    "cost": "string"
  },
  "authority": {
    "decision_owner": "string",
    "approval_requirements": ["string"],
    "irreversible_actions": ["string"]
  },
  "research_dependency": {
    "required": true,
    "result_refs": [{"run_id": "UUID", "artifact_sha256": "SHA-256"}],
    "unresolved_evidence_acknowledged": true,
    "freshness_requirement": "string"
  }
}
```

Every constraint category is required; an empty array means “considered and currently none known,” which is safer than silently omitting a constraint. Required research must include at least one exact `research-result.v1` run/hash reference. The contract does not copy the research claims or source text.

The validator rejects unknown top-level fields, malformed run/hash references, empty considered options, missing constraint categories, missing authority, and decision fields added outside the contract. It does not score options, recommend one, approve one, or create an ADR.

## 5. Field-by-field authority model

| Field | Writer | Storage | Reader | Authority/freshness | Failure behavior and acceptance evidence |
|---|---|---|---|---|---|
| `schema_version`, `request_id`, `created_at` | Intake producer/future `/design` caller | Immutable request JSON | Future `/design` | Request identity and creation time | Invalid identity blocks intake; schema and round-trip tests |
| `decision_context` | User or decision owner | Request artifact | `/design` | User-authoritative scope and objective | Missing field blocks; required-section tests |
| `constraints` | User/owner, optionally a reviewed planning input | Request artifact | `/design` | Explicit stated constraints; empty means considered-none | Missing group blocks; missing-constraint test |
| `options` | User, prior design input, or explicit research-derived candidates | Request artifact | `/design` | Candidate set, not a recommendation | Empty considered set blocks; option validation test |
| `priorities` | Decision owner | Request artifact | `/design` | Preference criteria, not a numeric scoring engine | Missing priority blocks; required-field tests |
| `authority` | Decision owner/governance process | Request artifact | `/design`, approval gate | Names who may decide and what needs approval | Missing owner blocks; authority tests |
| `research_dependency.result_refs` | Research producer or intake caller | Request artifact, referencing immutable research result | `/design` | Exact run/hash; evidence remains authoritative in `research-result.v1` | Malformed or absent required reference blocks; provenance-reference test |
| `research_dependency.unresolved_evidence_acknowledged` | Intake caller after reading result status | Request artifact | `/design` | Acknowledgement, not clearance | False/missing value blocks validation; unresolved evidence remains a design input concern |
| `research_dependency.freshness_requirement` | Decision owner | Request artifact | `/design` | Owner-defined freshness criterion | Missing value blocks; required-field test |
| Request storage | Contract writer with exclusive create | Run/session artifact directory | Validator and future consumer | Immutable after creation | Duplicate writes fail; immutable-storage test |

Research owns evidence acquisition and assessment. `/design` owns tradeoff reasoning and recommendation. A human or explicit approval mechanism owns approval. Planning owns implementation sequencing, work breakdown, rollback detail, and execution prerequisites. `/go` remains outside this contract.

## 6. Ten representative scenario evaluation

Evaluation artifact: `P:/tmp/.codex/state/decision-request-contract-20260714/evaluation.json`.

| Scenario | Intake status | Could research supply evidence? | Missing information class |
|---|---|---|---|
| Adopt an agent framework | valid | yes | research problem |
| Choose persistence architecture | valid | yes | decision context problem |
| Build vs buy | valid | yes | research problem |
| Select provider strategy | valid | yes | research problem |
| Migrate an existing component | valid | yes | execution planning problem |
| Introduce a new workflow | valid | yes | decision context problem |
| Accept operational risk | valid | yes | decision context problem |
| Choose between repositories | valid | yes | research problem |
| Choose process lifecycle ownership | valid | yes | execution planning problem |
| Authorize a limited pilot | valid | yes | decision context problem |

All ten inputs preserve the decision boundary. The current referenced smoke result is insufficient for a final decision, so the evaluator marks the current input as needing more evidence. It does not silently run research or fill the missing fields. Four gaps are research problems, four are decision-context problems, and two are execution-planning problems.

## 7. Tests and verification

Focused intake plus existing handoff tests:

```text
$env:PYTHONPATH='P:\'; pytest P:\tests\research_run_v1\test_decision_request.py P:\tests\research_run_v1\test_research_result.py -q -p no:cacheprovider
19 passed
```

The canonical suite was run after implementation: `102 passed, 3 failed`. The three failures are the existing router-policy corpus expectations:

- `test_phase1_role_policy_corpus_matches`
- `test_healthy_provider_roles_are_automatic_without_per_call_approval`
- `test_realistic_router_corpus_matches_expected_decisions`

They are unrelated to decision intake and were not changed.

## 8. Files changed

- `P:/tools/research_run_v1/decision_request.py`
- `P:/tools/research_run_v1/evaluate_decision_request.py`
- `P:/tools/research_run_v1/__init__.py`
- `P:/tests/research_run_v1/test_decision_request.py`
- this report

No plugin cache, `/research`, routing, provider, evidence assessment, provenance, `/go`, `/search`, Phase 2A, or `agy` path was changed.

## 9. Exact authorized behavior

The workspace may validate and immutably store an explicit `decision-request.v1` document that references one or more exact research-result runs. A future design consumer may use it to compare declared options, evaluate tradeoffs, and formulate a recommendation while preserving evidence and authority boundaries.

## 10. Exact deferred behavior

Implementing or wiring `/design`, automatically consuming the request, automatic recommendations, scoring engines, memory/KB changes, decision approval, ADR persistence changes, planning generation, `/go` integration, provider changes, routing changes, and research fallback behavior are deferred.

## 11. Verdict

`PASS_DECISION_INTAKE_CONTRACT`

The minimum durable decision boundary is defined and tested. The contract is ready for a separately authorized `/design` implementation, but it does not itself make, approve, or execute a decision.
