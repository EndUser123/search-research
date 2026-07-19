# Evidence-aware capability routing

Verdict: `PASS_EVIDENCE_AWARE_ROUTING`

## Scope and consumed paths

Canonical source:
`P:/packages/.claude-marketplace/plugins/search-research`

Consumed runtime cache:
`C:/Users/brsth/.claude/plugins/cache/local/search-research/0.1.121`

Phase 1 router and artifact engine:
`P:/tools/research_run_v1`

The real caller remains `search-research:/research`; `/all` remains a
compatibility wrapper. No new provider, `/design`, `/go`, `/search`, Phase 2A
automation, or `agy` was added.

## Routing changes

The capability model is now:

| Capability | Automatic lane | Policy |
|---|---|---|
| local context | QMD | automatic local lane |
| broad/conceptual discovery | MMX | automatic |
| semantic external discovery | Exa | promoted automatic candidate |
| implementation/repository/maintenance/authority discovery | Brave | automatic |
| independent-index discovery | DDG | conditional only |

Exa no longer claims implementation authority. Semantic-plus-implementation
questions select Brave and Exa in a bounded parallel wave; implementation-only
questions remain Brave-only.

DDG can be selected only when the request records one of:
`conflicting_sources`, `omission_risk`, `high_consequence`, or
`insufficient_after_primary`. Its selection mode is recorded as `conditional`.

The router now rejects partially covering lane plans instead of executing a
lane while leaving a required capability unresolved.

## Evidence-aware telemetry

Each Phase 1 artifact now records `routing.lane_decision` entries containing:

- required capability;
- selected lane;
- rejected lanes and reasons;
- evidence gap;
- evidence obtained;
- stop reason.

Provider output remains discovery only. Source opening, assessment, claim
status, and authority boundaries are unchanged.

## 25-task evaluation

Artifact:
`P:/tmp/.codex/state/evidence-aware-routing-20260714211757/evaluation.json`

The corpus contains semantic, conceptual, repository, implementation,
authority, maintenance, local, mixed, and conditional independent-index tasks.

| Measure | Baseline | Candidate |
|---|---:|---:|
| Provider calls | 18 | 28 |
| Lane-set changes | — | 11 |
| Minimum-sufficient cases | — | 25/25 |
| Unnecessary lane executions | — | 0 |
| Automatic Exa semantic selections | 0 | 7 |
| Conditional DDG selections | 0 | 4 |

The additional calls are attributable to seven newly supported semantic gaps,
two bounded mixed local/semantic cases, and four explicit DDG evidence-gap
triggers. The candidate did not add a redundant lane in any case.

The prior 20-task provider-value artifact remains the evidence basis for
quality: Exa contributed 11 useful sources and 6 decision changes; DDG
contributed 7 useful sources and 5 decision changes, with DDG source-opening
failures preserved visibly. The new 25-task evaluation measures routing and
efficiency; it does not reinterpret discovery as authority.

## Runtime validation

Installed-cache `/research` smoke:

- query: `semantic similarity retrieval approaches`;
- selected provider: Exa;
- provider output: 5 candidates;
- artifact: `P:/tmp/.codex/state/research-run-v1/743907c5-9ac8-4f21-8eaf-0e3b9f6a6717/research-run.json`;
- lane decisions: 5;
- stop: `single_best_eligible_lane`.

## Authorized behavior

- Exa may be automatically selected for semantic external discovery.
- Brave remains the implementation, repository, maintenance, and authority
  candidate lane.
- MMX remains the broad/conceptual lane.
- QMD remains the local lane.
- DDG remains conditional and must carry a recorded trigger.
- Incomplete capability coverage is refused rather than silently degraded.
- All provider and source provenance remains bound to the existing artifact.

## Deferred behavior

- DDG is not promoted to default automatic routing.
- No provider broker, fallback chain, or maximum-parallelism policy was added.
- No authority promotion, factual-truth claim, production routing, or workflow
  integration outside `/research` was authorized.

## Verification

- Focused routing/provider/canonicalization tests: `24 passed`.
- The 25-task evaluator reports `25/25` minimum-sufficient cases and zero
  unnecessary candidate lane executions.
- The full canonical suite was run after implementation; its three known
  router-policy/corpus failures remain separately reported and are unrelated
  to this increment.
- Canonical suite result: `83 passed, 3 pre-existing router-policy/corpus failures`.
- Post-change source-authority audit: `P:/tmp/source-discovery-evidence-aware-routing-post.json`;
  `proceed_with_discovery`, zero conflicts, zero walk errors.
