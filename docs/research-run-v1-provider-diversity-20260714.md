# Provider diversity evaluation for canonical `/research`

Verdict: `PASS_PROVIDER_DIVERSITY_VALIDATED`

## Decision

Evaluate whether the existing canonical Exa and DuckDuckGo implementations add
useful external discovery evidence to `/research` without creating a provider
broker, automatic run-all behavior, or a second artifact path.

## Current architecture

```text
/research
  -> evidence requirements and deterministic router
  -> QMD / MMX / Brave lane execution
  -> optional explicit Exa or DuckDuckGo lane adapter
  -> shared normalization
  -> shared source opening and assessment
  -> research-run.v1 artifact and conservative output

/all -> compatibility wrapper -> /research
```

The canonical provider implementations remain in
`packages/.claude-marketplace/plugins/search-research/core/providers/`. The new
Phase 1 adapter in `tools/research_run_v1/external_lane.py` imports those
implementations only when explicitly selected. It does not retry, substitute,
or register a generic provider broker.

## Prospective evaluation

Artifact: `P:/tmp/.codex/state/provider-diversity-20260714174739/provider-diversity-evaluation.json`

The same 20 agentic-coding research tasks were run with:

1. Baseline: bounded parallel MMX + Brave.
2. Candidate: the same baseline plus one policy-selected complement: Exa for
   semantic/conceptual discovery or DuckDuckGo for independent-index discovery.

MMX was ready with 98% interval / 100% weekly quota before the final run and
94% interval / 100% weekly quota after it. The quota change is recorded in the
artifact; the evaluation used 20 baseline waves and 20 complementary queries.

| Provider | Queries | Returned | Opened | Unique | Duplicate | Useful | Claim-linked | Decision changes | Failures | Total latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Exa | 11 | 55 | 22 | 55 | 0 | 11 | 7 | 6 | 0 | 52.0 s |
| DuckDuckGo | 9 | 45 | 15 | 44 | 1 | 7 | 4 | 5 | 3 | 76.0 s |

Across the 20 cases, the candidate lane contributed 18 complementary useful
source observations, changed 11 task-level outcomes, and exposed evidence not
seen in the baseline in 7 cases. Three DuckDuckGo source-opening failures and
two baseline source-opening failures remained visible; none were hidden as
provider success. The artifact records per-task timings, provider statuses,
source counts, duplicates, claim-linked sources, and failures.

## Findings

- Exa added useful semantic evidence on technical, conceptual, and
  compatibility questions. Its 11/11 successful queries, zero duplicate
  results in this sample, and 6 decision-changing cases support a bounded
  semantic-discovery role.
- DuckDuckGo added useful index-diverse evidence mainly on repository and
  maintenance discovery. Its 5 decision-changing cases support a bounded
  independent-index role, but its 3 source-opening failures and higher total
  latency require visible degradation and no authority promotion.
- Search results remain discovery candidates. Claims are not promoted merely
  because a complementary provider returned a URL; source opening and the
  existing assessment/authority rules remain required.
- The first evaluation run found and corrected a signal defect: Exa was
  incorrectly asked to satisfy `independent_recall`. The final run used the
  corrected semantic-only contract.
- A live cache smoke run through `skills.research.orchestration` executed Exa
  through the installed `search-research@local` cache and produced a
  `research-run.v1` artifact. The compatibility `/all` help path remained
  available.

## Authorized behavior

- `/research` may explicitly select `--external-provider exa` or
  `--external-provider duckduckgo`.
- Exa is restricted to semantic/conceptual/technical discovery.
- DuckDuckGo is restricted to independent-index/broad discovery.
- Every lane retains provider identity, source identity, timings, readiness,
  failures, source opening, and the existing immutable run artifact.
- An explicit provider request cannot silently broaden to Brave, MMX, or
  another lane when its requested role is unsupported.
- `/all` remains only a compatibility wrapper.

## Deferred behavior

- Neither provider is automatically added to every `/research` run.
- No `/design`, `/go`, or `/search` integration was added.
- No Phase 2A automation, falsifier change, `agy`, Exa/DDG broker, provider
  fallback, or command-topology change was added.
- Provider output still cannot establish factual truth, authoritative identity,
  production readiness, or a decision without claim-specific evidence.

## Verification

- Focused provider and canonicalization tests: `8 passed`.
- Canonical suite: `80 passed, 3 failed`.
- The three failures are the pre-existing router-policy/corpus expectations
  documented in the prior accepted state (`test_phase1_policy.py` and
  `test_router_corpus.py`); they predate this increment and are unrelated to
  the new external-lane tests.
- Post-change source audit: `P:/tmp/source-discovery-provider-expansion-post.json`,
  decision `proceed_with_discovery`, no conflicts or walk errors.

This verdict validates measurable provider diversity for bounded use; it does
not authorize automatic provider selection or any broader workflow rollout.
