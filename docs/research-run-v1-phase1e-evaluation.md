# `research-run.v1` Phase 1E evaluation

## Verdict

`PASS_TARGETED_LANE`

Brave is safely integrated as one bounded complementary external discovery
lane. The live corpus shows useful incremental value for implementation- and
authority-seeking questions, but does not justify routine parallel use. The
lane remains advisory discovery only; search snippets do not establish claim
truth or source authority.

## Scope and authority

The run used workspace `P:/`, branch `main`, HEAD
`7d8e103927d5a5dd47099a1e2e9fbd2d4ec52d38`. The worktree was already heavily
dirty with unrelated changes and active worktrees; none were reset, stashed,
cleaned, staged, or committed. The source-authority audit was run at
`P:/tmp/source-discovery-phase1e.json`; it returned `needs_review` only because
the execution owner (`phase1.py`) and evaluation owner (`evaluate_phase1.py`)
both contain the Phase 1 token. They are distinct roles and were kept distinct.

The live result is [phase1e-evaluation.json](P:/tmp/.codex/state/phase1e-evaluation-20260713/phase1e-evaluation.json).

## Candidate inspection

| Candidate | Consumed path / contract | Result |
|---|---|---|
| MMX | `C:/Users/brsth/AppData/Roaming/npm/mmx.cmd search query --q ... --output json --quiet` | Existing baseline |
| Brave gateway target | `P:/packages/installers/agentgateway/config.yaml`, MCP target `brave` | Rejected for this increment: configured, but no gateway listener was active |
| DuckDuckGo gateway target | Same config, `uvx duckduckgo-mcp-server` | Rejected: gateway inactive and browser-backed lifecycle was not a bounded consumed path |
| Brave direct client | `P:/packages/.claude-marketplace/plugins/search-research/core/providers/brave_client.py` | Selected source contract; broad package import currently fails on missing optional `jinja2` |
| Exa, Tavily, Serper | Existing plugin provider clients | Not selected: API-key clients behind the broad plugin graph; no independently verified narrow consumed path was needed after Brave passed |
| WebReader/MCP and native web | Existing plugin/harness capabilities | Not selected: no bounded `research-run.v1` executor path with preserved provider provenance |
| GitHub search | Existing plugin CLI mode | Not selected: repository/code search capability, not a distinct general discovery lane for this comparison |

Presence was not treated as activation. No AgentGateway process or listener
was started, and no production provider configuration was changed.

## Selected lane and boundary

The implementation is [brave_lane.py](P:/tools/research_run_v1/brave_lane.py).
It performs one `GET https://api.search.brave.com/res/v1/web/search` request
with `q`, bounded `count` (maximum 5 in the evaluation), an 15-second timeout,
and an in-memory `BRAVE_API_KEY`. It has no retry, fallback, broker, daemon,
background monitor, or autonomous assessment. Missing authentication or stale
readiness causes `not_attempted`; HTTP, timeout, and parse failures remain on
the Brave lane.

The adapter preserves provider, lane role, query, result ID, title, URL,
snippet, retrieval time, canonical URL identity, and provider-specific response
field/index provenance. The existing pure router remains unchanged. QMD was
not counted as an external lane; it remains local context only.

The direct client probe succeeded with five results in 834.1 ms. The earlier
package-level import failure (`ModuleNotFoundError: jinja2`) is recorded as a
plugin integration limitation; the narrow adapter avoids importing that broad
graph and does not conceal the limitation with fallback behavior.

## Live corpus and reference assessment

The corpus contains 10 real agentic-coding research questions covering
maintained repositories, implementation evidence, Windows lifecycle defects,
official-versus-secondary sources, native-capability duplication, abandonment,
authority misses, and insufficient evidence. Evaluation rules are explicit,
evaluator-supplied lexical relevance/authority rules in
`P:/tests/research_run_v1/phase1e_eval_corpus.json`. They are not a model and
do not promote snippets to verification.

The run executed 10 MMX-only cases, 10 Brave-only cases, and 3 concurrent
MMX+Brave waves. Each lane was independently bounded. MMX had 13 search
invocations total; Brave had 13 one-request invocations. End-of-run MMX state
reported 64% current-interval remaining and 100% weekly remaining.

| Mode | Cases | Candidates | Canonical duplicates | Same-underlying duplicates* | Useful | Authoritative useful | Opened primary | Contradictory | Opening failures | Lane failures | Avg total ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MMX-only | 10 | 91 | 0 | 2 | 21 | 6 | 21 | 1 | 3 | 0 | 6249.4 |
| Brave-only | 10 | 50 | 0 | 0 | 29 | 14 | 21 | 2 | 2 | 0 | 3063.0 |
| Parallel sample | 3 | 43 | 8 | 0 | 8 | 3 | 7 | 2 | 2 | 0 | 4475.1 |

`*` Same-underlying duplicates exclude exact canonical-URL duplicates. The
evaluation retains provider attribution for canonical duplicates; it does not
count a duplicated result as independent confirmation.

Per-case timing fields in the live artifact include
`mmx_lane_wall_time_ms`, `complementary_lane_wall_time_ms`,
`parallel_wave_wall_time_ms`, `source_open_time_ms`, `assessment_time_ms`,
and `total_run_time_ms`; batch artifact write timing is recorded at the
artifact level. The three parallel waves were genuinely concurrent: for
example, the maintained-repositories wave measured MMX 2343.3 ms, Brave 176.7
ms, and wave wall time 2343.7 ms.

## Material differences

Brave supplied incremental useful sources in 9 of 10 Brave/MMX-only pairs
under the evaluator's underlying-source grouping. It changed the bounded
action from `insufficient_evidence` to `usable_evidence` for:

- `authoritative-missed-source`: MMX 0 useful / Brave 2 useful;
- `insufficient-evidence`: MMX 0 useful / Brave 1 useful.

It also increased useful sources materially for `feature-implementation-
evidence` (1 to 5), and supplied distinct Windows lifecycle evidence including
the Python Windows timeout issue and an OpenAI Codex cleanup pull request.
Other cases were neutral or mixed: `production-workflow-examples` had fewer
Brave useful sources than MMX, and several cases returned mostly overlapping
obvious sources. This is why the result is targeted rather than routine
parallel adoption.

The parallel sample exposed real canonical overlap (8 exact duplicate URLs in
43 candidates) and showed wall time bounded by the slower MMX lane, while
providing no additional changed action beyond the Brave-only result in the
sample. Its value is therefore omission-sensitive follow-up value, not a
default wave.

## Evidence status

### Verified/static

- Router purity and existing MMX path remain intact.
- Brave normalization and provenance retention are deterministic.
- Readiness rejection prevents invocation.
- One request, timeout, parse failure, no-secret persistence, duplicate
  normalization, genuine parallel execution, and independent failure
  preservation are covered by tests.

### Measured/live

- Direct Brave request succeeded.
- Both lanes completed all attempted discovery calls without lane failures.
- Source opening failures remained visible and did not erase the other lane.
- Brave-only produced more useful and authoritative sources in this corpus and
  changed two evaluator actions.

### Unknown or unproven

- Brave's backend ranking/index independence is not proven merely by different
  URLs; the evaluation uses observable result differences only.
- Search snippets remain `discovery_only`; no general claim verification or
  authoritative model identity is granted.
- The parallel sample is too small for a production or routine-default claim.
- Longitudinal quota, provider policy changes, and concurrency beyond this
  bounded wave remain untested.

## Authorization and next step

Automatically authorized now: an explicit, read-only, advisory Brave discovery
request for omission-sensitive or implementation/authority-seeking research,
with one bounded request, run-scoped output, preserved provenance, and no
fallback. Routine automatic parallel routing is not authorized.

Intentionally deferred: Phase 2 disconfirmation, inverse-query planning, more
providers, `agy`, broker/fallback construction, production configuration, and
autonomous claim assessment.

Recommended next step: improve source opening and task-signal production before
considering broader Phase 1 integration. Do not begin Phase 2 on the strength
of this evaluation alone.
