# Quality-guided execution evaluation — 2026-07-14

Verdict: `PASS_SAFE_BUT_UNPROVEN`

## Experiment design

This was an evaluation-only A/B harness. It did not change the consumed
`search-research:/all` caller, routing policy, command topology, `/search`,
`/go`, Phase 2A activation, provider set, or `agy` behavior.

- Control: existing `/all` Phase 1 execution using the original question.
- Candidate: the same `/all` Phase 1 execution using one supplemental query
  selected from the deterministic quality plan.
- Same source-opening and assessment rules were retained per run.
- Candidate query budget was bounded to one supplemental query per task.
- Inverse searches remained `planned_not_executed`.
- Control and candidate artifacts are separate immutable `research-run.json`
  files; the comparison capture retains exact paths, queries, lanes, sources,
  claims, failures, and timings.

## Real corpus

Fifteen real agentic-coding tasks covered repository adoption, architecture,
implementation comparison, official documentation, compatibility,
maintenance, local/external research, insufficient-evidence cases,
duplicate-heavy documentation, failure modes, and authority-sensitive lookup.

Raw comparison capture:

[research-quality-execution-evaluation-20260714.json](P:/tmp/research-quality-execution-evaluation-20260714.json)

## Results

| Metric | Control | Candidate | Delta |
|---|---:|---:|---:|
| cases | 15 | 15 | 0 |
| opened sources | 32 | 32 | 0 |
| claim-linked useful sources | 0 | 0 | 0 |
| primary/authority sources opened | 6 | 7 | +1 |
| provider/source failures | 0 | 0 | 0 |
| aggregate elapsed time | 102.2s | 111.9s | +9.6s / +9.4% |
| stop/action changes | 0 | 0 | 0 |

The candidate added one authority candidate, but it remained unverified and was
not claim-linked as useful evidence. No answer, authorization, stop decision,
or next action changed. The candidate therefore did not demonstrate improved
research outcomes.

One raw comparison record showed a claim-status detail changing from empty to
`unverified`; that was not counted as a decision change after review. The
evaluation harness now defines decision change as a changed stop/action, with
claim-status detail retained separately.

## Quality findings

Query planning successfully generated bounded category-specific queries, but
one supplemental query per case was not enough to produce more useful evidence.
The experiment did not optimize for result count, and it found no reduction in
irrelevant or redundant opened sources.

Evidence-category planning improved observability and surfaced missing
categories, but all cases remained insufficient. The authority-sensitive
candidate gained one primary source candidate without establishing authority.

Source-contribution accounting remained conservative: opened-but-unassessed
sources were not counted as useful. No unsupported conclusion was promoted.

Stopping remained safe. No candidate stopped as sufficient merely due to query
or source budgets. Sufficient, duplicate/diminishing-return, and provider
failure stop branches were not exercised by this corpus.

## Defects found and fixed

- Corrected A/B evaluator bookkeeping so claim-status differences do not count
  as decision changes.
- Added a regression test for that distinction.

No production or `/all` behavior was changed.

## Verification

Focused:

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1\test_quality.py P:\tests\research_run_v1\test_quality_execution.py -q -p no:cacheprovider
```

Result: `7 passed`.

Canonical:

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider
```

Result: `72 passed, 3 failed`. The three failures remain the independently
attributed, unrelated router-policy/router-corpus failures documented in the
prior quality-usage report. No router changes were made here.

## Authorization

Authorized:

- manual evaluation of quality-guided query execution;
- explicit, bounded supplemental queries in experiments;
- evidence-gathering only.

Not authorized:

- integrating candidate execution into normal `/all`;
- automatic query expansion;
- automatic inverse search or Phase 2A;
- provider additions, `agy`, `/go`, `/search`, or command-topology changes;
- production claims or rollout.

Recommended next step: retain the candidate as experimental until a corpus
with claim-linked useful evidence demonstrates a repeatable improvement in
authority, useful-source yield, or decision quality without unacceptable cost.
