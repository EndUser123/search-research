# yt-is Progressive Visual Analysis Pipeline — Handoff

## Status: ready-to-implement

**Session:** 019fc99e-4f0f-7180-9c52-84ea85ee944b
**Date:** 2026-08-04
**Design doc:** `/design` run 07a67363 (in temp at `C:\Users\brsth\AppData\Local\Temp\grok-design-07a67363\grok-design-doc-07a67363.md` — will be reaped; copy if keeping)

## What was shipped this session

| Commit | Units | Description |
|--------|-------|-------------|
| `793747c` | U-00 + U-04 | Cache-hit suppression removed + provider failover with attempt log + correct attribution |
| `8a36e87` | U-01 + U-02 | 12 new orthogonal state tables + `record_status_event` API with monotonic enforcement |
| `b0e0107` | U-03 | OCR-driven profiles, versioned artifact assembly, CRV frame sampler adapter |
| `9c59308` | refactor | DRY fix: extracted `_build_ordered_candidates` shared helper |

Also shipped session resolver (`session_resolver.py` — process tree walk against `active_sessions.json`).

## What remains (U-05 through U-09)

### U-05 — Worker pool split: transcript pool + visual pool
- `csf/batch.py`: new `dispatch_transcript_pool()` and `dispatch_visual_pool()`
- `csf/batch_scheduler.py`: extend `yield_next()` to filter by `state_kind`
- `bin/csf-source`: split `cmd_fetch` into transcript + visual dispatch
- Default workers: `YTIS_TRANSCRIPT_WORKERS=4`, `YTIS_VISUAL_WORKERS=2`
- 3-worker NLM ceiling shared across both pools

### U-06 — Idempotent ingestion (`publish_artifact`)
- `csf/ingestion.py` (new): `publish_artifact(video_id, downstream, artifact_type, content_hash, payload)`
- `ingestion_receipts` table (already created in U-01)
- Idempotent on `(video_id, downstream, content_hash)`

### U-07 — Cache-hit visual enqueue with OCR-driven profile promotion
- `csf/batch.py`: on `transcript_status=acquired`, create `analysis_jobs` row + enqueue `visual_jobs`
- `csf/profiles.py::promote_profile` (already created in U-03) — reads OCR output to detect code-heavy content
- Standard profile runs first; OCR-detected code promotes to visual for Gemini full-video

### U-08 — Legacy status cutover (operator-invoked, Rung 4)
- Flip `YTIS_USE_LEGACY_STATUS=0`
- Remove legacy `analysis_status.status` reads
- Requires U-01 through U-07 all shipped

### U-09 — Tests + docs
- `test_visual_pipeline.py`, `test_profiles.py`, `test_assembly.py`
- `test_orchestrator_failover.py`, `test_worker_pool_split.py`
- `test_ingestion_idempotency.py`, `test_cache_hit_visual.py`
- `test_video_catalog_migration.py`
- Update spec.md, CHANGELOG.md, HANDOFF.md

## Key decisions (from design doc)

- DEC-01: Four independent state machines (transcript/visual/analysis/ingestion)
- DEC-02: Default profile is `standard` — cache presence does NOT suppress visual
- DEC-03: Frame sampling composes with `crv` skill — no PySceneDetect
- DEC-04: Provider failover with attempt log (shipped in U-04)
- DEC-05: Split worker pools
- DEC-06: Idempotent ingestion on content_hash
- DEC-07: transcript_cache contract unchanged
- DEC-08: OCR-driven profile promotion (not transcript-text regex)
- DEC-09: GeminiSDKProvider → GeminiFullVideoProvider rename (pending)
- DEC-10: Legacy corpus backfilled to visual_status='queued' with 200/day throttle

## Open questions

1. NLM throughput 3,788 VPH — proven optimum or observed rate? [INFERENCE]
2. Gemini token cap for long videos — 45 min threshold correct? [INFERENCE]
3. `FOR UPDATE SKIP LOCKED` referenced in design but SQLite uses `BEGIN IMMEDIATE` — verify claim pattern works
4. Promotion precision ≥80% — needs validation against labelled OCR-output sample
