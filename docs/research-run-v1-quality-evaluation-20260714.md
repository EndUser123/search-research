# Phase 1 research-quality evaluation — 2026-07-14

Verdict: `PASS_MECHANISM_READY_NEEDS_USAGE`

## Scope

This increment keeps the current `search-research:/all` caller and does not
rename commands, alter `/search`, change routing topology, integrate `/go`,
automate Phase 2A, add providers, or invoke `agy`. The quality layer is
additive and deterministic.

## Implemented path

`P:/tools/research_run_v1/quality.py` now provides:

- evidence-category planning for conceptual, implementation, authority,
  compatibility, maintenance, failure, and local evidence;
- a bounded plan of at most four targeted query variants;
- explicit inverse-search eligibility with `planned_not_executed` status;
- source contribution classification that distinguishes claim-linked useful
  sources, opened-but-unassessed sources, discovery-only results, and duplicates;
- conservative stopping that refuses to call opened-but-unassessed evidence
  sufficient.

`phase1.py` attaches the result as `quality` to both the real Phase 1 path and
the MMX helper. The existing lane results, source openings, assessments, and
failures remain unchanged.

## Measured evaluation

The fixed corpus contains 20 consequential agentic-coding research questions
covering adoption, repository selection, architecture, compatibility,
implementation, maintenance, local architecture, and official-document
lookups.

- Mean expected-category recall: `0.971`
- Bounded query plans: `20/20`
- Inverse-search plans: `19/20`; all are explicitly not executed
- Focused quality and Phase 1 tests: `10 passed`
- Real `/all` smoke: caller `search-research:/all`, Brave lane, 5 candidates,
  2 opened sources, 0 claim-linked useful sources, quality stop
  `insufficient`, missing category `authority`
- Smoke artifact:
  `P:/tmp/.codex/state/research-run-v1/9309e6f5-9d8f-42a1-a65c-127d15e210b5/research-run.json`

The smoke result is intentionally conservative: opening official-looking
pages did not establish an authority claim, so the quality layer did not
authorize a conclusion.

## Verification boundary

Canonical command:

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider
```

Result: `68 passed, 3 failed`. The three failures reproduce in the existing
router corpus and are outside this increment. `git diff` shows pre-existing
staged changes to `P:/tools/research_run_v1/router.py` that alter lane
selection; this task did not change that file. The failures are therefore
recorded as an unresolved workspace-scope boundary, not attributed to the
quality layer.

## Authorization

Authorized: continued manual/experimental use of the quality telemetry on the
existing `/all` Phase 1 path, with evidence-gathering authorization only.

Not authorized: automatic routing changes, production rollout, command
topology changes, Phase 2A activation, provider additions, or treating
category planning as proof of source quality. More real runs are required to
measure whether query plans increase unique useful sources or change actions.
