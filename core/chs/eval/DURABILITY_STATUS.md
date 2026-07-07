# KB Durability Status — honest scope

**Date:** 2026-07-07 · **Context:** persistent-KB architecture adoption + red-team REVISE verdict

## The claim we are NOT making

The KB is **not yet durable against a model sunset**. The durability layer is
built and tested, but parts of it are not wired into the active production
paths. This file states exactly what is and isn't operative, so nobody
(human or LLM) infers "durability ships" from the presence of the modules.

## What is built AND wired

- **Embedding run provenance (CHS sessions path):** `backfill_embeddings.py`
  records every run in `embedding_runs` + a JSON manifest
  (`<db_dir>/embedding_runs/<run_id>.json`); rows are tagged with
  `embedding_run_id`. Single-transaction writes; wrong-dim vectors are
  rejected before write (fail fast).
- **Model/dim resolution:** `--model`/`--dim` flags > active
  `embeddings_config` row > defaults. No longer requires source edits for a
  swap **on this path**.
- **Eval gate:** `backfill_embeddings.py --golden-cases <path>` runs the
  semantic-sessions golden eval after the run and exits 1 below
  `--min-recall`. The gate exists at the exact point re-embeds happen and
  filters to the model that was just written (`expected_model`).
- **Model/dim-aware read path (sessions):** `search_semantic_sessions`
  infers the query dim from the query embedding (no hardcoded 384),
  excludes dim/model-mismatched rows with a WARNING, and raises when ALL
  rows mismatch (misconfiguration, not an empty result).
- **Golden eval harness:** `core/chs/eval/retrieval_eval.py` — stable-key
  matching (message_id, content sha256, session_key), FTS and
  semantic-sessions modes, CI-friendly exit codes. Tested against synthetic
  DBs.

## What is built but DORMANT

- **SmartChunker content-addressed chunk IDs**
  (`core/chunking/smart_chunker.py`): implemented + tested, but **zero
  production consumers**. CKS document ingestion uses its own
  `DocumentChunker` with sequential `chunk_index` — positional identity that
  breaks silently on any chunker change. Decision needed: wire SmartChunker
  into CKS ingestion (with a re-chunk migration), or delete it and accept
  positional identity. Keeping it dormant is the worst option.

## What is NOT fixed (known residual gaps)

- `indexer.py:253` writes embeddings with a hardcoded model string + 384,
  independent of `embeddings_config`; it can race a backfill.
- `config.py` `DEFAULT_EMBEDDING_DIMENSIONS = 768` contradicts the CHS
  default of 384. The config-resolution order in `backfill_embeddings.py`
  sidesteps this for the backfill path only; other readers of
  `config.py` still see 768.
- `golden_cases.jsonl` is **populated** (50 real cases from 20 session
  transcripts, round-robin across sessions, March–July 2026), filtered
  to substantive multi-turn queries. Re-run the generator when the
  transcript corpus significantly changes:
  `python -m core.chs.eval.generate_golden_cases [--sessions N]`.
- Nothing runs the eval automatically outside `--golden-cases`; there is no
  hook or scheduled check.

## Cutover discipline (until the above closes)

1. Copy the DB. 2. `--re-embed --model X --dim N` against the copy.
3. `--golden-cases` gate must pass. 4. Swap paths by config, keep the old DB.
Never re-embed the live DB in place.
