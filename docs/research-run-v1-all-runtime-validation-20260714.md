# `/all` capability-routing operational validation

Date: 2026-07-14  
Caller: `search-research:/all`  
Scope: real Phase 1 execution through the consumed `/all` path; QMD, MMX, and Brave only.

## Verdict

`PASS_CAPABILITY_ROUTING_WITH_BOUNDED_COMPOSITION`

The current `/all` runtime correctly routes single-capability cases to the
minimum sufficient lane and composes complementary lanes only when the caller
supplies an explicit bounded-parallel trigger. The previously observed mixed
case failure was a concrete routing defect; the current router resolves it by
composing lane capabilities rather than requiring one provider to satisfy the
entire envelope. No new provider or routing strategy was added.

## Caller and command taxonomy

- `/all` is the current validated caller: `search-research:/all`.
- `/search` remains separate and unchanged.
- No `/explore` command exists.
- No rename specification exists.
- Command taxonomy and UX changes are explicitly deferred.

These are caller/topology facts, separate from capability-routing correctness.

## Prospective real `/all` runs

| Case | Run ID | Recommendation / execution | Sources | Runtime | Evidence result |
|---|---|---|---:|---:|---|
| Workspace implementation approaches | `8deb663b-3ef0-451d-8b7a-c5990cff6d49` | `local + mmx + brave` / bounded parallel | 19 | 29,814.1 ms | QMD, MMX, and Brave succeeded; discovered sources remained candidates until opened |
| Official Python asyncio subprocess docs | `5077fe4e-f40a-43f3-896b-cab18d748353` | `brave` / single lane | 5 | 1,901.4 ms | Official page opened; authority candidate recorded; claim remained `unverified` |

Artifacts:

- `P:/tmp/.codex/state/research-run-v1/8deb663b-3ef0-451d-8b7a-c5990cff6d49/research-run.json`
- `P:/tmp/.codex/state/research-run-v1/5077fe4e-f40a-43f3-896b-cab18d748353/research-run.json`

Both preserve caller identity, routing requirements, lane queries and
outcomes, opened-source status, assessments, failures, and timing telemetry.

## Routing analysis

### Minimum sufficient lanes

- Local-only/history/context signals select QMD only.
- Broad or conceptual external discovery selects MMX only.
- Implementation/repository/maintenance/compatibility discovery selects Brave only.
- Authority requests select Brave as an authority-candidate discovery lane;
  source opening and assessment remain separate Phase 1 responsibilities.
- The static router corpus passes 18/18 expected lane, stop, and escalation
  outcomes.

### Under-selection

The former mixed case selected no lane because each lane was judged against the
full requirement set. The current implementation fixes that concrete defect:
`local_context`, conceptual/broad discovery, and implementation discovery are
now satisfied by distinct lanes, but only with an explicit parallel trigger.
The fresh mixed `/all` run executed all three expected lanes successfully.

No current corpus case shows silent under-selection after this correction.

### Over-selection

No extra lane is added for ordinary single-role cases. Parallel selection is
limited to the explicit trigger set and stops after the required capability set
is covered. In the fresh mixed case, all three lanes were justified by distinct
requirements: local context, independent/conceptual recall, and implementation
discovery. The authority case did not add MMX merely because the claim was
important.

### Evidence contribution

Routing is not treated as verification. The mixed run contributed 5 QMD, 9 MMX,
and 5 Brave discovered/opened candidates, but produced no claim because no
claim-specific anchor was established. The authority run opened the official
Python page and produced one explicit assessment stating that source identity
alone does not establish support; the claim remained `unverified`. This is the
required conservative boundary between capability selection, source opening,
and evidence status.

## Fix scope

The concrete routing correction is present in the current provider-neutral
router and covered by the mixed-composition regression test. No command
topology, `/search`, `/go`, Phase 2A automation, or provider set was changed.

## Verification

Focused routing and integration tests:

```text
P:\tests\research_run_v1: 26 passed
```

The two prospective artifacts were written through the actual
`search-research:/all` orchestration path and each was checked with the
canonical `validate_research_run.py` validator.

## Authorization boundary

Authorized by this evaluation: continued manual/experimental `/all` use with
minimum-sufficient lane routing and explicitly bounded complementary parallel
execution.

Not authorized: automatic workflow rollout, authority claims based on source
identity alone, provider-equivalent truth, `/go` or `/search` integration,
Phase 2A automation, command taxonomy changes, or production configuration.

## Future UX/topology

The current `/all`/`/search` taxonomy is intentionally left unchanged. Any
future rename, alias, or new command would require a separate specification and
caller-coverage evaluation; it is not part of capability validation.
