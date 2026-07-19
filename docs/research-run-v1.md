# research-run.v1

`research-run.v1` is a harness-neutral, append-once evidence record for Codex,
OpenCode, or another agent. It records what was asked, which retrieval lanes
were attempted, what each lane returned (including failure or empty results),
which sources were merely discovered versus opened or verified, and which
claims are actually authorized.

## Contract

Each artifact contains:

- question, requested decision, and authorization level sought;
- workspace revision and the authority/lifecycle contract;
- every retrieval lane, its independence group, exact query, timestamps, status,
  sources, and failures;
- source title, direct/local URL, type, publication date when present, discovery
  status, retrieval time, and opening/verification method;
- claims with status, supporting and contradicting source references,
  verification method, and falsifier;
- uncertainty, stop reason, and whether the requested authorization is supported.

The validator is `P:\tools\research_run_v1\validate_research_run.py`:

```powershell
python P:\tools\research_run_v1\validate_research_run.py P:\path\to\run.json
```

Use `write_run()` for producer code. It validates before writing and opens the
destination with exclusive creation, so a duplicate path fails instead of
silently overwriting another run. Do not put credentials, cookies, bearer
tokens, or secret-like values in an artifact.

## Manual production

1. Capture the research question, decision, authorization sought, workspace
   revision, and the authority fields before retrieval.
2. Run independent lanes with exact commands/queries. Keep each lane separate;
   do not merge failures into successful results.
3. Record each returned source as `discovery_only`. Mark it `opened` only after
   opening the direct source, and `verified` only after the relevant claim was
   checked against that source.
4. Record empty and failed lanes explicitly. An empty lane is not evidence of
   absence.
5. Add claims only with source references and a falsifier. A verified claim must
   have at least one supporting source.
6. Validate the completed JSON before using it to authorize the next action.

## Harness use

Codex may use its native web/browser capability, local commands such as MMX or
QMD, and configured skills such as NotebookLM. OpenCode may use its shell,
MCP, CLI, or configured agent lanes. Each producer writes the same artifact;
the contract does not assume that either harness exposes the other harness's
tool names, citations, quota counters, or authentication state. An adapter may
translate native output into this contract, but the adapter must preserve the
exact query, lane status, source discovery status, and verification evidence.

This is intentionally an evidence contract, not an automatic router. Provider
selection remains adaptive to the capabilities actually available in the
current harness and to the user's authorization.

## Provider-neutral recommendation governor

`P:\tools\research_run_v1\router.py` provides the Phase 1 routing policy. It
is a pure recommendation function: the caller supplies capability records and
task signals, and receives explainable role-matched lanes plus explicit
rejections.
It does not probe, invoke, authenticate, retry, or fall back between providers.

Capability records carry the provider role, independence group, supported task
signals, circuit state, readiness, authentication, automatic eligibility,
authority class, readiness observation/expiry, observation method, recent
anomalies, recent verified values, supported task roles, and optional quota
reserve. Unknown or stale
readiness is not active. The circuit states are:

- `CLOSED`: normal bounded use;
- `RESTRICTED`: explicit selection or an accepted recorded advisory role only;
- `OPEN`: rejected without invocation;
- `PROBE`: rejected unless the task explicitly requests a bounded probe.

Eligibility gates run before ranking: invalid or open/restricted circuit,
unknown or stale readiness, missing authentication, quota below reserve,
sensitive-task boundary, authority level above evidence gathering,
advisory-role restrictions, explicit-selection restrictions, prior failure, and
missing capabilities or requested roles. Ranking is stable and signal-based;
the governor returns one lane by default. It returns two lanes only when the
caller supplies `allow_parallel=true`, a recognized `parallel_trigger`, and
two role-matching lanes; the wave remains bounded and caller-owned.

The conservative default inventory represents local inspection and
harness-native web as available candidates, MMX as an automatically eligible
broad/conceptual external lane only when the caller supplies fresh healthy
runtime state, Brave as an automatically eligible targeted implementation,
authority, maintenance, compatibility, repository, or omission-sensitive lane
when its fresh state is healthy, an unprobed NotebookLM capability as
unavailable, and `agy` as restricted advisory review.
The default MMX record is still unknown/unready, so it cannot be selected merely
because it exists in the inventory. These are defaults, not live claims: a
caller should replace readiness, authentication, quota, and circuit inputs with
current harness evidence before using a recommendation.

The selection fields have distinct meanings. `automatic` means the lane may be
chosen by policy when its supplied runtime state is healthy; it does not perform
a probe or invocation. `requested_roles` is the task's evidence need, not a
provider selection. `recorded_role` authorizes a bounded advisory role such as
`AGY_SEARCH_ADVERSARIAL`; it is not human approval and does not make advisory
output authoritative. `explicit_lane` and `agent_selected` record a caller's
lane choice. `human_authorized` records a boundary approval already obtained;
ordinary healthy read-only MMX, Brave, and QMD recommendations do not require
per-call human authorization.

The caller should also pass the task's current time, attempted and failed lanes,
and whether evidence is already sufficient. This lets the governor skip a
redundant lane and preserve a failed lane as a visible rejection without
silently substituting another provider.

### Bounded MMX state adapter

`P:\tools\research_run_v1\mmx_state.py` is a direct, non-persistent observer
for the installed MMX CLI. It runs only:

```text
mmx.cmd --version
mmx.cmd auth status --output json --quiet
mmx.cmd quota show --output json --quiet
```

The adapter records sanitized command metadata, version, authentication method
and source, quota percentages by returned model group, observation time, and a
five-minute reuse expiry. It never stores or emits the masked key returned by
the status command, raw stdout/stderr, or any credential material. It derives a
conservative router quota from the minimum interval and weekly percentages and
rejects missing, malformed, nonzero-status, out-of-range, or contradictory
quota data. The observed quota is shared-account scoped and returned by model
group; fixed search-count semantics are not inferred. The state includes
`quota_scope=shared_account`, `concurrent_consumers_possible=true`, and
`quota_delta_attributable_to_current_run=false`. A caller may record its known
top-level call count and shared before/after observations, but the adapter
labels any percentage delta `indeterminate_concurrent_usage`; it never treats
that delta as this run's cost.

The adapter has no cache, watcher, daemon, scheduler, or automatic refresh.
The immutable observation object may be passed to multiple readers, but this
increment does not prove cross-process freshness coordination. A caller must
discard it at `valid_until`, on an observed authentication/quota failure, or
when the relevant account or CLI configuration changes.

### Phase 1 execution slice

`P:\tools\research_run_v1\phase1.py` is the first bounded execution layer. It
acquires or receives fresh MMX state, asks the pure router for permission, runs
one explicit `mmx search query`, normalizes `organic[]` results, deduplicates
canonical URLs, opens one selected candidate directly, and writes one
run-scoped artifact with exclusive creation. Search snippets remain
`discovery_only`; a source becomes `anchor_confirmed` only when the caller
supplies an explicit anchor that is found in the opened source. This is not
general `verified` status and cannot by itself authorize a verified claim.

The layer has no provider registry, retry loop, automatic fallback, claim
engine, disconfirmation planner, or production route. `execute_parallel()` is
only a bounded helper for an explicitly supplied wave and preserves each
lane's failure; it does not select additional providers. Direct source bodies
are bounded to 2 MB and stored below the run UUID directory. A stale or
router-rejected provider is never invoked.

Phase 1 evaluation telemetry separates `lane_wall_time_ms`,
`source_open_time_ms`, `assessment_time_ms`, `artifact_write_time_ms`, and
`total_run_time_ms`. The evaluation harness reports zero for assessment and
artifact-writing phases when it is measuring lane comparison only; those zeros
mean those phases were outside that benchmark, not that they were free in a
full run.

Evidence assessment uses `P:\tools\research_run_v1\assessment.py`. It binds
each relationship to a run, source ID/location, passage or anchor, authority,
currency, method, basis, and limitations. `anchor_confirmed` and `opened` are
not support relationships. Only deterministic aggregation can assign a final
claim status; model-assisted and anchor-only assessments remain advisory.

For bounded `agy` trials, use the contract as an advisory ledger. Record the
role (`AGY_SEARCH_INDEPENDENT`, `AGY_SEARCH_DEEP`, or
`AGY_SEARCH_ADVERSARIAL`), preserve provider failures as
`researcher_unavailable`, and keep the first independent pass blind to other
providers' candidate results. A successful subprocess proves runtime
viability only; it does not establish backend model identity, transcript
binding, process-tree cleanup, concurrent isolation, write containment, or
authorization for automatic routing.

## Authority and lifecycle

The producer is the current agent or tool invocation. Acquisition is the exact
provider command/API/browser action. Serialization is this JSON contract.
Storage is a harness-scoped artifact directory; the consumer is a human or
reviewing agent that trusts the schema plus source inspection. Scope is one run,
the lifetime is from creation through immutable retention, duplicate run/path
collisions fail closed, and retrieval failures degrade to an explicit partial
record rather than an invented conclusion.

Validity proves structural completeness and explicit provenance. For advisory
`agy` artifacts, the validator additionally checks invocation-scoped packet and
evidence paths, packet hash and invocation identity, non-empty parsed findings
for success, zero exit and no timeout, visible failure states, conservative
authorization, and the separation of requested model from backend identity. It
still does not prove source truth, freshness, provider independence, full
process-tree cleanup, or that an authorization decision is wise. Those require
review of the cited sources and the claim ledger.

## Deliberate non-goals

This increment does not add provider invocation, automatic fallback, a planner,
a shared retrieval runner, quota scheduling, live readiness probes, or a claim
synthesizer. Those are separate boundary-affecting changes requiring live
activation and failure testing.
