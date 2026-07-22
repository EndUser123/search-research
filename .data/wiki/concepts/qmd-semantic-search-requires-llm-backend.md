---
title: "QMD semantic search requires explicit llm_backend in CLI calls"
created: 2026-07-20
source: session-2026-07-20
tags: [qmd, semantic-search, embedding, bug, configuration, wiki, auto-link]
summary: >
  QMD's CLI search command does not create or pass an LLM backend to the search
  function. All searches are BM25 (keyword) only — embeddings are computed and
  stored but never used for retrieval. The fix: pass llm_backend in cmd_search.
  Also: auto-link's 15s timeout is too short for model loading (needs 60s), and
  the default embedding model (paraphrase-multilingual-MiniLM-L12-v2) is weaker
  than the locally-available all-mpnet-base-v2.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/non-regex-hook-optimizations
    type: related
---

# QMD semantic search requires explicit llm_backend in CLI calls

## The problem

`qmd search` returns only keyword-matching results with uniformly low scores
(0.03-0.08). Semantic search appears broken even though embeddings exist in
the database. Auto-link reports "no qualifying concept neighbors found" on
every page.

## Root cause (3 layers)

### Layer 1: CLI doesn't pass LLM backend (the main bug)

`qmd/cli/main.py:cmd_search()` calls `search(db, query, ...)` without the
`llm_backend` parameter. The `search()` function in `retrieval.py` only
executes vector search when `llm_backend` is provided (lines 505-520 are
guarded by `if llm_backend`). Without it, all searches are BM25-only.

Embeddings are computed and stored correctly — they're just never queried.
The vec0 virtual table has the vectors; the search function never asks for
them.

**Fix:** create `llm_backend` in `cmd_search` and pass it through:
```python
llm_backend = create_llm_backend(getattr(args, "backend", "auto"))
results = search(db, query, ..., llm_backend=llm_backend)
```

### Layer 2: Auto-link timeout too short

`wiki_after_write.py:query_qmd()` uses `timeout=15` for the subprocess call.
After fixing Layer 1, the search loads the sentence-transformers model on
first invocation (~28 seconds on CUDA). The subprocess times out before
results come back.

**Fix:** increase to `timeout=60`.

### Layer 3: Search limit too small for mixed corpora

`wiki_after_write.py` searched with `limit + 5` (default: 10 results).
With 200 wiki documents where 150+ are source files and only 25 are concepts,
the top-10 results are dominated by source files. The concept filter strips
them all, leaving zero qualifying neighbors.

**Fix:** use `max(limit + 5, 40)` so concept pages have room to appear.

## Also: default embedding model is weak

QMD defaults to `paraphrase-multilingual-MiniLM-L12-v2` (384 dim). Switching
to `all-mpnet-base-v2` (768 dim, already downloaded in `.model_cache`) produces
much better score differentiation (0.898 for exact match vs 0.083 with the
old model).

**Fix:** patch `qmd/llm/sentence_tf.py` default `model_name` parameter.

## Symptoms after all fixes

- Search returns 10+ results with meaningful scores (0.2-0.9 range)
- Auto-link finds 1-5 concept neighbors per page
- First search invocation takes ~30s (model load); subsequent invocations
  take ~5s (model cached in process — but each CLI call is a new process,
  so every search pays the load cost unless using a daemon)

## Known issues remaining

- `qmd embed --force` has a `KeyError: 'skipped'` display bug (cosmetic)
- `--force` doesn't clear the vec0 virtual table before re-inserting,
  causing UNIQUE constraint failures if run twice without deleting the DB
- The qmd source patches are in `site-packages` and will be lost on pip update

## Related

- `non-regex-hook-optimizations` — same principle: use the right tool for semantic problems
- QMD source: `pip install qmd-py` (package name in pip)
- The fix was committed to `wiki_after_write.py` in the cc-skills-sdlc submodule

## Auto-related

- [[python-behavior-tree-framework-for-autonomous-llm-agents--technical-specificatio]]
- [[grok-build-compat-layer-marketplace-plugin-skills]]
- [[i'm-going-to-create-a-hook-to-enforce-discovery-be]]

