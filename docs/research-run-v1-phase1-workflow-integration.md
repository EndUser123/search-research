# Phase 1 workflow integration

Date: 2026-07-14  
Verdict: `PASS_PHASE1_WORKFLOW_INTEGRATION`

## Scope and caller

The selected caller is `/all` from the canonical `search-research` plugin:

`P:\packages\.claude-marketplace\plugins\search-research\skills\all\orchestration.py`

Its existing behavior was a three-layer local/web search: execute the package
router, cluster results, optionally apply context filtering, and format the
results as a string. The integration keeps that formatter and layer controls;
the Phase 1 path now supplies the result objects and exact artifact reference.
The non-Phase-1 path remains available as an explicit test/compatibility escape
(`phase1_enabled=False`) and no other caller was changed.

## Boundary and authority

`skills.all.orchestration` calls `execute_phase1_for_all`, which translates the
query into `TaskSignals` and calls `tools.research_run_v1.phase1.run_phase1`.
That function uses the existing pure router, observed MMX/Brave state, the
existing QMD wiki command, bounded lane executors, source opening, and
`research-run.v1` validation/write-once artifact emission.

The returned path is consumed directly. There is no newest-file search,
machine-wide cache lookup, or silent provider fallback. The artifact writer is
`research_run_v1.phase1`; its reader is the `/all` adapter; its scope is the
single run ID under `P:\tmp\.codex\state\research-run-v1\<run-id>`.
Completed artifacts remain exclusive and run-scoped. Multiple terminals get
different UUID directories and do not share a mutable “current result”.

## Automatic and manual policy

Automatic Phase 1 behavior is limited to the accepted lanes:

- QMD/local is selected for local-context requests.
- MMX is selected for broad/conceptual external discovery when ready.
- Brave is selected for implementation, repository, compatibility,
  authoritative-source, maintenance, or omission-sensitive roles when the
  existing router admits it.
- Parallel selection remains conditional on the existing deterministic router
  trigger; it is not routine.

Phase 2A is not inferred from impact, implementation intent, compatibility
research, or omission sensitivity. Only explicit challenge language sets the
adversarial signal. When that signal is present, `run_phase1` invokes the
existing stabilized Phase 2A evaluator through an injectable manual runner;
ordinary Phase 1 calls never invoke it. If the manual evaluator is unavailable,
the failure remains visible rather than becoming ordinary search.

`agy` was not invoked and no provider or production configuration was added.

## Evaluation evidence

Static/router evaluation covered 14 cases: local-only, broad external,
implementation, official-source, Windows compatibility, already-sufficient,
MMX-only, Brave-only, bounded parallel, provider unavailable, source-open
failure, explicit disconfirmation, consequential without explicit challenge,
and foreign-artifact handling.

Observed outcomes included local → `local`, broad external → `mmx`,
implementation/Windows → `brave`, evidence sufficient → no lane, unavailable
MMX → visible Brave selection, invalid URL → `failed`, ordinary consequential
work → Phase 2A false, and explicit challenge → Phase 2A true.

Real bounded smoke execution used the plugin's canonical virtualenv and
`/all ... --mode local-only`. QMD returned five candidates; five source bodies
were handled, with two opened as usable in the displayed top results and the
remaining candidates retained as discovery-only where local source identity
could not be opened. The exact artifact was validated successfully:

`P:\tmp\.codex\state\research-run-v1\f537abed-7452-4d58-8484-8f8e0ec46e2c\research-run.json`

The first system-Python attempt failed before the caller because the plugin's
optional `jinja2` dependency was absent. Re-running through the consumed
plugin virtualenv succeeded; this is an environment prerequisite, not a
hidden fallback.

Focused and canonical tests:

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider
65 passed
```

## Preserved and deferred

Preserved: `/all` arguments, layer controls, result formatting, non-research
paths, other callers, immutable artifact semantics, and conservative
discovery-only status.

Deferred: `/go`, `/search`, `/web`, and all other caller integrations;
automatic Phase 2A; new providers; `agy`; adaptive learning; broker/daemon or
scheduler work; and production provider configuration.

The next step should be to collect real `/all` usage evidence before either
integrating another caller or revisiting Phase 2A. Refining source opening is
also appropriate if local QMD records continue to remain discovery-only.
