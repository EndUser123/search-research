# research-run.v1 green-field evaluation

## Decision

The smallest justified increment is complete: a shared JSON contract, a
stdlib-only validator, representative fixtures, and harness-neutral operating
documentation. Do not add an automatic router or shared retrieval runner yet.

## Scope inspected

- Workspace root: `P:\`, revision `ce0e7f933e9a209ebbc0610c2cd17bda2d0a37ae`.
- Governing guidance: `P:\AGENTS.md`.
- New source: `P:\tools\research_run_v1\`.
- New tests and fixtures: `P:\tests\research_run_v1\`.
- New contract docs: `P:\docs\research-run-v1.md`.
- Historical Claude Code package was explicitly excluded from the source of
  truth and its task-local changes were removed.

## Evidence obtained

| Claim | Type | Evidence | Falsifier | Action allowed |
|---|---|---|---|---|
| The green-field validator accepts complete and explicit-empty artifacts | verified_fact | `pytest P:\tests\research_run_v1 -q`: 5 passed; both CLI fixture validations returned `VALID` | A valid fixture is rejected or a malformed fixture is accepted | Use the validator for manual artifact checks |
| Duplicate destination writes fail instead of overwriting | verified_fact | `test_duplicate_write_does_not_overwrite` | A second `write_run()` succeeds | Keep append-once write behavior |
| A verified claim requires an opened and verified source | verified_fact | Adversarial fixture test rejects discovery-only support | Discovery-only support is accepted for a verified claim | Keep claim status conservative |
| The contract proves source truth or provider independence | unsupported | No live cross-provider harness was built | Independent replay and source review | Evidence gathering only; no rollout claim |

## Failure and boundary review

- Empty and failed lanes are represented rather than omitted.
- Secret-like material is rejected before persistence.
- Duplicate paths fail closed.
- The artifact is one-run scoped; storage retention and cleanup are explicit
  policy fields, not hidden validator behavior.
- Provider quotas, authentication, and availability are deliberately outside
  the shared contract because they are volatile and harness-specific.

## Untested and intentionally deferred

- Native Codex citation extraction and OpenCode MCP citation extraction.
- Concurrent multi-process artifact creation beyond the exclusive-file test.
- Quota accounting, retries, planner/routing policy, and provider failover.
- Long-term retention, indexing, and artifact garbage collection.
- Automatic production configuration changes.

These require a separate live, boundary-affecting increment with explicit
authorization, lifecycle ownership, and failure testing.
