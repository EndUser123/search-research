# Immutable evaluation-provenance increment

Observed: 2026-07-14. This increment is provenance-only. It does not change falsifier logic, provider routing, `/go`, `/search`, add providers, or invoke `agy`.

## Contract implemented

`tools/research_run_v1/immutable_evaluation.py` adds:

- exclusive run-directory reservation using unique run IDs;
- write-once JSON artifacts using exclusive file creation;
- per-run `run.json` with exact case records, requested/effective queries, normalized provider results, opened-source paths, assessments, timings, failures, provider observations, executable path, PID, revision, and source hashes;
- per-run `manifest.json` containing size and SHA-256 for every completed-run file;
- comparison artifacts bound to exact baseline/candidate run IDs and manifest hashes;
- explicit provider, corpus, policy, execution-condition, and source-result comparability labels;
- explicit preservation of the fact that the historical Phase 2A artifact cannot be reconstructed.

The existing evaluator was extended only to retain normalized lane results and opened-source metadata in its records. Search, admission, assessment, and reconciliation behavior were not changed.

## Prospective smoke evaluation

Two cases were run prospectively through the existing MMX+Brave+QMD executor:

- baseline: `phase2a-baseline-20260714-b352ee063040`
- candidate: `phase2a-candidate-20260714-8f0cbfb8fd79`
- comparison: `cmp-0a6ac38f-796d-49d7-a57e-fa27eaae14d5`

Cases: `windows-lifecycle-defects` and `official-source-comparison`.

Each run is isolated in its own directory. Both manifests contain seven hashed files, including `run.json` and captured source evidence. The runs retained 24 and 23 normalized provider results respectively, six opened sources each, six assessments each, and zero source-opening failures. Live search results differed, so provider set, corpus, and policy are directly comparable; execution conditions and source results are only partially comparable.

Artifacts:

- baseline: `P:\tmp\.codex\state\immutable-evaluations\phase2a-baseline-20260714-b352ee063040\`
- candidate: `P:\tmp\.codex\state\immutable-evaluations\phase2a-candidate-20260714-8f0cbfb8fd79\`
- comparison: `P:\tmp\.codex\state\immutable-evaluations\cmp-0a6ac38f-796d-49d7-a57e-fa27eaae14d5\comparison.json`

## Verification

Canonical command:

```text
C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\pytest.exe P:\tests\research_run_v1 -q -p no:cacheprovider
```

Result: `60 passed`.

The immutable-store tests verify exclusive run IDs, write-once files, manifest hashing, manifest binding, lost-history recording, and explicit partial comparability for live conditions. The smoke command was:

```text
python -m tools.research_run_v1.immutable_evaluation
```

## Authorization and verdict

Authorized: immutable manual/prospective evaluation artifacts and exact baseline/candidate comparison for bounded smoke runs. Not authorized: primary workflow integration, automatic routing, provider changes, falsifier changes, `agy`, or production use.

Verdict: `PASS_IMMUTABLE_EVALUATION`.

The increment proves write-once run isolation, manifest/hash binding, provenance retention, and comparison binding. It does not make live provider results deterministic or reconstruct the lost historical Phase 2A artifact; those limitations remain explicit in the comparison artifact.
