---
title: "NotebookLM batch content extraction: no batch API, concurrent async is the optimization"
created: 2026-07-31
source: session-20260731
tags: [notebooklm, nlm, batch, content-extraction, async, asyncio, concurrent, transcript-export, optimization]
summary: >
  NotebookLM's `nlm source content` takes a single source_id — there is no batch
  content extraction API. The batchexecute RPC protocol theoretically supports
  multiple operations per POST, but the nlm client encodes exactly one per POST
  (`[[[rpc_id, params_json, null, "generic"]]]`). The correct optimization is the
  async Python client (`NotebookLMClient`) with `asyncio.gather` — one auth
  handshake, `max_concurrent_rpcs=16` semaphore handles rate limiting. The
  subprocess-per-source approach with 1.5s sleeps between each is the anti-pattern
  that produced a 168s runtime for 98 sources (87 instant cache hits + 11 NLM
  calls). Cache pre-pass (instant SQLite reads for cache hits, skip sleep) + async
  concurrent fetch for misses reduces this to ~3s.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "C:/Users/brsth/AppData/Roaming/Python/Python314/site-packages/notebooklm/rpc/encoder.py:45 — encode_rpc_request returns inner (single operation, triple-nested)"
  - "C:/Users/brsth/AppData/Roaming/Python/Python314/site-packages/notebooklm/_runtime/config.py:78 — DEFAULT_MAX_CONCURRENT_RPCS = 16"
  - "https://github.com/teng-lin/notebooklm-py/blob/main/docs/python-api.md — async re-entrant, asyncio.gather supported"
  - "https://github.com/Taitai54/notebooklm-export — practitioner bulk export tool, also per-source via MCP"
  - "Session 019fb49b export_transcripts.py run: 98 sources, 87 cache hits, 168s runtime, from_cache_count=87"
relations:
  - target: wiki/concepts/notebooklm-cli-operational-gotchas.md
    type: complements
  - target: wiki/concepts/wiki-yt-architecture-decisions-20260730.md
    type: extends
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: related
---

# NotebookLM batch content extraction: no batch API, concurrent async is the optimization

## Decision context

**Why this was needed:** during session 2026-07-31, the operator asked "Why aren't you batching the jobs?" after seeing a wiki-yt sync take 168 seconds. Investigation revealed the export script ran `subprocess.run(["nlm", "source", "content", ...])` per source with a 1.5s sleep between each — including for 87 cache hits that were instant SQLite reads. The operator then said "for NLM we can batch like 300 sources at a time." This triggered research into whether NLM has a batch content API.

## Key findings

### No batch content extraction API exists

**[FACT]** `nlm source content <source_id>` takes exactly ONE source_id. The `nlm batch` command group has no content subcommand. The MCP surface has `source_get_content` (single source). No `get_fulltext_batch` or `get_all_content` method exists anywhere in the `notebooklm` Python package.

**Receipt:** `nlm source content --help` — single `SOURCE_ID` argument. `nlm batch --help` — subcommands: query, add-source, create, delete, studio (no content). `notebooklm._sources.SourcesAPI` dir: `get_fulltext(notebook_id, source_id)` — one source_id.

### The batchexecute protocol COULD batch, but the client doesn't

The batchexecute RPC protocol theoretically supports multiple operations per POST body. But `encode_rpc_request` in `rpc/encoder.py:45` encodes exactly ONE: `return inner` (triple-nested single operation). The dedicated practitioner tool `Taitai54/notebooklm-export` also calls content extraction per-source (via MCP), confirming no batch API is available in practice.

**Receipt:** `rpc/encoder.py:45`.

### "Batch 300 sources" = bulk source ADD, not content extraction

The operator's "we can batch like 300 sources at a time" refers to `nlm source add --youtube u1 ... u300` — bulk source INGEST (one CLI call, N URLs). Content extraction has no equivalent. These are different operations: ingest = add sources to notebook; extraction = read indexed content back.

### The correct optimization: async Python client with asyncio.gather

The `notebooklm-py` package provides a fully async `NotebookLMClient`:
- **Async re-entrant on a single event loop** — `asyncio.gather` for concurrent operations
- **`DEFAULT_MAX_CONCURRENT_RPCS = 16`** — semaphore caps simultaneous HTTP POSTs, tunable to `None` for unlimited
- **NOT thread-safe** — must be async, not ThreadPoolExecutor
- **Built-in retry** — 429/5xx auto-retried with exponential backoff

**Receipt:** `python-api.md` § "Concurrency model", `_runtime/config.py:78`.

### The anti-pattern: subprocess-per-source with sleeps

The current `export_transcripts.py` spawns a new `subprocess.run(["nlm", ...])` per source. Every subprocess does its own auth handshake, process startup, and serialization. Then `time.sleep(1.5)` fires after ALL sources — even the 87 instant SQLite cache reads. Result: 168s for 98 sources.

### The fix: two-phase design

1. **Cache pre-pass** (instant): resolve all sources against the title bridge + yt-is cache in one pass. Cache hits write directly — no sleep, no subprocess, no NLM call.
2. **Concurrent NLM fetch** (for misses only): use async `NotebookLMClient` with `asyncio.gather`. One auth handshake, 16-way concurrency, no subprocesses.

**Expected:** 87 cache hits (~0s) + 11 NLM calls concurrent at 16-way (~2s wall clock) = ~3s total instead of 168s.

## What this means for our workspace

The `export_transcripts.py` subprocess-per-source pattern should be replaced with the async client. The cache-first optimization already works (shipped this session); the async fetch is the performance layer on top.

The negative-capability-claim-from-shallow-checks pattern (checking `--help`, concluding "no batch exists") is the 6th instance this session of the fabricated-claims behavior documented in `kill-unverified-capability-claims-20260730`. This finding was only reached because the operator challenged the claim and forced proper research.

## Falsifier

This finding is wrong if:
- A future `nlm` version adds a batch content extraction flag or API method
- The batchexecute protocol is extended by Google to accept multiple GET_SOURCE operations in one POST and the client adopts it
- The async client has a reliability issue at 16-way concurrency that makes it worse than serial subprocess calls

## Receipts

- `C:/Users/brsth/AppData/Roaming/Python/Python314/site-packages/notebooklm/rpc/encoder.py:45` — single-operation encoding
- `C:/Users/brsth/AppData/Roaming/Python/Python314/site-packages/notebooklm/_runtime/config.py:78` — `DEFAULT_MAX_CONCURRENT_RPCS = 16`
- `C:/Users/brsth/AppData/Roaming/Python/Python314/site-packages/notebooklm/_source/content.py:66-69` — `get_fulltext` params format: `[[source_id], [2], [2]]` (single source)
- Session 019fb49b export_transcripts.py run output: `from_cache_count=87`, runtime 168s, 98 sources
