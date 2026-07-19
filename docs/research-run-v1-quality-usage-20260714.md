# Phase 1 research-quality usage evaluation — 2026-07-14

Verdict: `PASS_USAGE_EVIDENCE_ONLY`

The quality mechanism behaved safely under real `/all` use, but this run did
not prove measurable research-outcome improvement. The correct authorization
is continued manual evaluation only.

## 1. Workspace and regression attribution

- Workspace: `P:/`
- HEAD: `7d8e103927d5a5dd47099a1e2e9fbd2d4ec52d38`
- Main worktree: dirty, with extensive staged and unstaged changes from other
  workstreams.
- Active worktrees include `P:/.claude/worktrees/ai-task-20260713-133947`,
  `P:/.claude/worktrees/sdlc-audit`, and other locked test worktrees.
- The current quality files are untracked; the failing router files are
  independently staged/modified files.

Exact failing tests, reproduced in isolation:

1. `test_phase1_role_policy_corpus_matches`: expected `['mmx']`, actual `[]`.
2. `test_healthy_provider_roles_are_automatic_without_per_call_approval`:
   expected `['automatic']`, actual `[]`.
3. `test_realistic_router_corpus_matches_expected_decisions`: expected lane
   `mmx`, actual `None`.

The first two failures use `evaluate_policy.py`, `router.py`, and
`phase1_policy_corpus.json`. The third uses `evaluate_router.py`, `router.py`,
and `router_corpus.json`. None imports `phase1.py` or `quality.py`.

The relevant router diff adds role/capability composition and changes
recommendation selection from a single eligible lane to capability coverage
composition. It also changes capability naming and rejection behavior. Those
changes directly explain why the corpus expects `mmx` while current evaluation
returns no recommendation. The quality increment only imports `quality.py`
from `phase1.py`; it does not write or read router inputs, evaluator inputs, or
corpus expectations. Therefore the failures are independently attributable to
the existing router work, not to the quality increment. No router fix was made.

## 2. Consumed runtime path

The evaluated path was:

```text
search-research:/all
  -> skills.all.search_executor.execute_phase1_for_all
  -> tools.research_run_v1.phase1.run_phase1
  -> existing router and bounded lane execution
  -> source opening and assessment
  -> additive quality telemetry
```

No command topology, `/search`, `/go`, provider set, or Phase 2A activation was
changed. `agy` was not invoked.

## 3. Real-use corpus and retained evidence

Twelve real agentic-coding tasks were run through `/all`:

| Case | Lane(s) | Returned/opened | Useful linked | Stop | Reviewed finding |
|---|---:|---:|---:|---|---|
| local architecture | QMD | 1/1 | 0 | insufficient | category and stop correct; no claim assessment |
| broad conceptual | MMX | 10/2 | 0 | insufficient | bounded plan useful; variants not executed |
| repository discovery | Brave | 5/2 | 0 | insufficient | maintenance and implementation remained unproven |
| authority lookup | Brave | 5/2 | 0 | insufficient | authority candidate remained unverified |
| maintenance | Brave | 5/2 | 0 | insufficient | failure/maintenance evidence remained missing |
| compatibility | Brave | 5/2 | 0 | insufficient | compatibility and failure evidence remained missing |
| mixed local/external implementation | QMD+Brave | 10/4 | 0 | insufficient | parallel composition ran; no claim-linked evidence |
| evidence-sufficient candidate | Brave | 5/2 | 0 | insufficient | prior evidence was only stated in the query, not supplied as input |
| insufficient model-identity question | Brave | 5/2 | 0 | insufficient | authority-category omission fixed after review |
| duplicate-heavy documentation query | Brave | 5/2 | 0 | insufficient | no exact duplicate identity observed |
| explicit inverse candidate | MMX | 9/2 | 0 | insufficient | inverse plan recorded but not automatic |
| no-inverse definition lookup | Brave | 5/2 | 0 | insufficient | inverse correctly not eligible |

Raw records and exact per-run artifacts are retained in:

- [real-use capture](P:/tmp/research-quality-real-use-20260714.json)
- [inverse companion capture](P:/tmp/research-quality-inverse-companions-20260714.json)
- each run's immutable `research-run.json` under
  `P:/tmp/.codex/state/research-run-v1/`

The run batch took `84.9s` wall time for 12 cases. Runtime values are retained
per case in the capture and in each run artifact.

## 4. Baseline versus quality

The quality layer runs after the existing query, lane, source-opening, and
assessment work. Consequently, for this bounded comparison:

| Metric | Existing behavior | With quality layer | Result |
|---|---:|---:|---|
| executed query variants | 1 per single lane; 2 same-query lanes for mixed case | same | no execution delta |
| useful opened sources | 0/12 cases | 0/12 cases | no improvement measured |
| redundant sources | 0 observed | 0 observed | no demonstrated duplicate benefit |
| missing evidence detected | not represented as categories | all 12 stopped with missing categories | safer visibility, not outcome improvement |
| unsupported claims avoided | no promoted claims in these runs | no promoted claims | safe/conservative, no delta |
| sufficient stops | 0 | 0 | sufficient branch untested |
| action/conclusion changes | 0 | 0 | no measured change |

The targeted query plans were recorded but not executed. Therefore query
quality is not yet demonstrated to improve evidence acquisition; it only
improves planning visibility.

## 5. Inverse-search evaluation

Two explicit companion searches were run manually outside automatic `/all`
activation:

- Windows subprocess adoption limitations: 9 results, 2 opened, no claims or
  assessments, insufficient.
- Production use of an agentic coding library: 5 results, 2 opened, no claims
  or assessments, insufficient.

The first produced mostly secondary failure commentary; the second produced
mixed secondary/community material. Neither yielded claim-linked material
contradiction, changed a conclusion, narrowed a claim, or changed the next
action. This is evidence that inverse execution can add retrieval noise unless
source assessment is performed, not evidence that inverse search is useless.

## 6. Defect fixed

The model-identity case exposed a category-extraction omission: “authoritative
backend model identity” was classified only as conceptual. Authority terms
now include authoritative/authority/identity/backend, with a regression test.

The corpus still measures `0.971` mean category recall because one case’s
expected conceptual label is not lexically expressed in its question. That is
reported as evaluator-label sensitivity, not hidden as a success.

## 7. Stopping and evidence contribution

All 14 runs (12 primary plus 2 companions) stopped conservatively. No run
claimed sufficiency merely because its query or source budget was exhausted.
No duplicate/diminishing-return stop or provider/source-opening failure stop
was observed, so those branches remain unvalidated.

Opened-but-unassessed sources were not counted as useful. This produced zero
claim-linked useful sources across the batch and correctly prevented authority
or production conclusions.

## 8. Verification

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider
```

Result: `69 passed, 3 failed`.

Focused quality tests: `4 passed`.

The three failures are the independently attributed router-corpus failures
listed above. The quality change did not alter their dependency path.

## 9. Authorization

Authorized now:

- manual/experimental quality telemetry on the existing
  `search-research:/all` path;
- explicit human-selected inverse companion searches;
- evidence-gathering only.

Still experimental/not authorized:

- automatic execution of targeted query variants;
- automatic inverse search or Phase 2A;
- claims based on opened-but-unassessed sources;
- production rollout or routing changes;
- command renames or `/search`/`/go` integration;
- adding providers or invoking `agy`.

Recommended next step: resolve the unrelated staged router-corpus work in its
own task, then run a second bounded evaluation with a supplied evidence corpus
that can exercise sufficient, duplicate-stop, and failure-stop branches.
