# yt-is / wiki-yt Synthesis Quality Gate Handoff

Date: 2026-08-09
Status: implemented and offline-verified

## Decision

The synthesis path now fails closed on provenance-quality failures instead of
accepting a concept with no usable citations or silently presenting a
transcript-head fallback as equivalent to a full pre-summary. The existing
partial-result safety contract is unchanged: a nonzero synthesis result does
not reconcile, write, advance the manifest, rename the notebook, or mark the
queue item complete.

This is an offline reliability change. It did not invoke NotebookLM, fetch
external metadata, retry source-add failures, or alter authentication.

## Changes

- `P:/.agents/skills/wiki-yt/scripts/synthesize_subtopics.py`
  - requires at least one citation with a non-empty claim and excerpt;
  - accepts a known `source_id` or one unambiguous known source title;
  - includes `source_id` in the synthesis prompt contract;
  - classifies map-reduce head fallback as `synthesis_degraded`;
  - emits `FAILURE_CLASS=citation_invalid` or
    `FAILURE_CLASS=synthesis_degraded` or
    `FAILURE_CLASS=synthesis_backend_exhausted` for queue consumers.
- `P:/.agents/skills/wiki-yt/scripts/bin/queue_sync.py`
  - preserves those stable failure classes in retry records.
- `P:/.agents/skills/wiki-yt/scripts/sync.py` and `maintenance.py`
  - serialize manifest writes with an interprocess lock; sync merges the latest
    per-notebook update and maintenance reloads before repairs/prunes.
- `P:/.agents/skills/wiki-yt/SKILL.md`
  - documents the quality gate, fail-closed semantics, and queue-exclusive
    maintenance rule.

## Evidence and verification

| Claim | Type | Evidence | Confidence | Falsifier |
|---|---|---|---|---|
| Empty/unmapped citations cannot be accepted by the synthesizer | verified_fact | `validate_citations()` and focused tests | high | A valid fixture passes without a resolvable source |
| Degraded pre-summary context is classified separately | verified_fact | `pre_summarize_member()` and marker path | high | A fallback fixture returns success without the marker |
| Queue retains the stable class | verified_fact | `classify_sync_result()` and queue tests | high | Marker input is classified as generic success |
| Existing partial-write safety remains intact | verified_fact | unchanged `sync.py` nonzero gate and full wiki suite | high | A synthesis rc=5 advances the manifest |

Commands:

```powershell
python -m pytest P:/.agents/skills/wiki-yt/tests/test_synthesize_context.py -q
python -m pytest P:/.agents/skills/wiki-yt/tests/test_ytis_nlm.py -q
python -m pytest P:/.agents/skills/wiki-yt/tests -q
python -m py_compile P:/.agents/skills/wiki-yt/scripts/synthesize_subtopics.py P:/.agents/skills/wiki-yt/scripts/bin/queue_sync.py
python -m pytest P:/.agents/skills/wiki-yt/tests/test_sync_manifest.py -q
python -m py_compile P:/.agents/skills/wiki-yt/scripts/maintenance.py
```

Results: `22 passed`, `12 passed`, `44 passed` for the full wiki suite,
`2 passed` for manifest concurrency, and compilation clean.

## Remaining work

- Queue workers now propagate an explicit per-notebook Stage-C checkpoint for
  named retries. The checkpoint is identity-validated and does not bypass
  citation or degraded-output gates.
- The named `4017aa6e-35fb-426d-bc53-34620bec405e` quality-debt record was
  completed by the bounded MMX checkpoint-resume run16. The queue now reports
  `poisoned=0` and `needs_resynthesis=0`; five pages passed normal validation
  with complete four-hop provenance. Citation coverage remains `19/36`, so
  this is not complete source-coverage proof. Receipt:
  `P:/.logs/wiki-yt-queue/20260811/semantic-resynthesis-4017-mmx-run16-result_receipt.md`.
- The two profileless legacy failed records remain blocked and require an exact
  historical receipt or current ownership evidence before any retry.
- Citation quality on already-synced historical pages has not been rewritten
  by this change. Audit or repair it as a separate scoped operation.
- The 2026-08-09 queue run is terminal; its separate receipt and manifest
  reconciliation are recorded in
  `P:/docs/handoffs/yt-is-wiki-queue-live-20260809/HANDOFF.md`.
