# Increasing Hot-Path VPH

- **Created:** 8/13/2026, 7:48:42 AM
- **Exported:** 8/13/2026, 7:48:44 AM
- **Messages:** 2
- **Source:** browser_extension

---

## #1 · user

yt-is throughput brainstorming — context brief

What the system does: yt-is is a transcript ingestion pipeline that downloads YouTube video transcripts via Google NotebookLM. Videos are processed in batches: sources are added to a notebook, materialized (polled until ready), then content is fetched via nlm source content. The pipeline runs multiple worker profiles across Pro and Free NotebookLM accounts in parallel.

Headline metric: combined.hot_path_videos_per_hour (VPH) — completed videos per hour, excluding Whisper fallback.

Current performance:
- Operational leader: 3636.16 VPH (source-age cadence, thresholds 160/190/5, 3+3 Pro+Free lanes, batch 200, serial reusable pipeline)
- Diagnostic soak: 3788.53 VPH (ungated launch, smoke gate failed)
- Historical HWM: 5572.04 VPH (old metric contract, never reproduced in 10+ attempts)

Approaches ruled out (all have live negative evidence):
1. Margin/projection sweeps (15-60s) — guard fires, no VPH improvement
2. First-window cap — increased churn without reducing age pressure
3. Source-age rotation at 180s — too late at boundary
4. Shared retry pool — worsened age pressure
5. Warmup-state preservation — no warmup effect
6. Auth-refresh intervals (30-75s) — not the bottleneck
7. Worker-balance A/B — assignment order irrelevant
8. Age-cap-200 validation — didn’t reproduce
9. Profile-order swap — regressed to 1249 VPH
10. Browser-default profile — regressed to 2752 VPH
11. Active windows (25, 50) — controls age but stays below ceiling
12. Extract windows (no reset) — stays below ceiling
13. Source-age cadence tuning (40/80 to 60/120) — calibration branch, not ceiling

Blocked lever: Batch-1 old-window nlm source content command latency. Inter-attempt source-age guard already exists at line 5225. Already as narrow as possible.

Key constants: Source-age cliff 200s. Retry 4 attempts, 30s timeout each, 1s-8s delay, 30s budget. Batch size 50. Backoff 0.5s-60s. Materialization timeout 600s.

Question: What mechanism — from outside the current search space — could increase sustained hot-path VPH above 3636? We need ideas we haven’t tried.

## #2 · assistant

## Best candidate: stop optimizing the scheduler and change the **unit of transport**

Your experiments have mostly explored **when to issue the same expensive operation**. The remaining high-value axis is **how that operation is executed**.

The 3,636.16 VPH result is a major clue:

- 
3,636.16 VPH = **0.990 s/video**

- 
3,788.53 VPH = **0.950 s/video**

- 
5,572.04 VPH = **0.646 s/video**

That looks remarkably like a serialized ~1-second service center.

My current best hypothesis is:

> 
**`nlm source content` itself has become the throughput governor. The next breakthrough comes from removing per-video command/RPC serialization, not improving source-age scheduling.**

The current `nlm` implementation supports that hypothesis. `source content` ultimately calls `get_source_fulltext(source_id)` for one source. [[GitHub]

GitHub+1](https://raw.githubusercontent.com/jacob-bd/gemini-notebook-mcp-cli/main/src/notebooklm_tools/services/sources.py) The client then constructs an HTTP `batchexecute` request containing exactly **one RPC entry** and performs one POST. [[GitHub]

GitHub+1](https://raw.githubusercontent.com/jacob-bd/gemini-notebook-mcp-cli/main/src/notebooklm_tools/core/base.py)

### I would investigate these in this order

| Rank | Mechanism | Confidence | Potential |
| --- | --- | --- | --- |
| 1 | Persistent in-process NotebookLM client | High | High |
| 2 | True multi-source batchexecute | Medium | Very high |
| 3 | 2–4 concurrent hizoJc reads/profile | High testability | High |
| 4 | Remove batch materialization→extract barrier | Medium-high | Moderate-high |
| 5 | Fuse readiness polling with extraction | Medium | Moderate |

### 1. Eliminate `nlm source content` subprocesses entirely

Do **not** call:

```
nlm source content <source-id>
nlm source content <next-source-id>
...
```

from the hot path.

Instead, maintain **one long-lived NotebookLM client per profile** and call the underlying source-fulltext method directly.

This matters because the library has a reusable `httpx.Client`, but that reuse exists only for the lifetime of the `NotebookLMClient` instance. [[GitHub]

GitHub](https://raw.githubusercontent.com/jacob-bd/gemini-notebook-mcp-cli/main/src/notebooklm_tools/core/base.py) Its own architecture documentation also says session/CSRF state is refreshed during client initialization. [[GitHub]

GitHub](https://github.com/jacob-bd/gemini-notebook-mcp-cli/blob/main/CLAUDE.md) A fresh process destroys everything you would want to amortize: Python startup/imports, CLI parsing, client construction, auth setup, connection establishment, response formatting, process teardown, and parent/child IPC.

The competing implementation `notebooklm-py` already exposes this directly as an asynchronous Python API:

```
fulltext = await client.sources.get_fulltext(notebook_id, source_id)
```

and is explicitly designed around a long-lived client context. [[GitHub]

GitHub](https://github.com/teng-lin/notebooklm-py/blob/main/docs/python-api.md?utm_source=chatgpt.com)

**Discriminating experiment:** take 200 already-materialized source IDs. No adds. No age logic. No rotation.

Run:

```
A. nlm subprocess × 200, serial
B. one persistent client × 200, serial
```

Measure only:

```
wall_seconds
videos/sec
p50/p95 get_fulltext latency
errors / empty content
```

If B falls from ~950–990 ms/video toward ~650 ms/video, you have probably explained much of the mysterious old HWM without reproducing its scheduler at all.

## 2. More interesting: batch `hizoJc` itself

This is the lever I would be most excited to probe.

Google's endpoint isn't merely called `batchexecute`; the protocol genuinely supports putting **multiple RPC calls into one HTTP request**. A generic implementation demonstrates an `f.req` containing RPC1 and RPC2 together, with one POST and separately indexed responses. [[GitHub]

GitHub](https://github.com/pndurette/pybatchexecute)

But the current NotebookLM client deliberately constructs:

```
[[[
    rpc_id,
    params_json,
    null,
    "generic"
]]]
```

—exactly one operation. [[GitHub]

GitHub](https://raw.githubusercontent.com/jacob-bd/gemini-notebook-mcp-cli/main/src/notebooklm_tools/core/base.py)

And `hizoJc` is the RPC that returns the actual indexed full text. [[GitHub]

GitHub](https://raw.githubusercontent.com/jacob-bd/gemini-notebook-mcp-cli/main/src/notebooklm_tools/core/sources.py)

So there are **two probes** worth doing.

### Probe 2A — multiple IDs in one `hizoJc`

Current arguments are:

```
[[source_id], [2], [2]]
```

The first parameter is already list-shaped.

Try, experimentally:

```
[[source_id_1, source_id_2], [2], [2]]
```

I have **not verified that NotebookLM accepts this**. It may simply be a protobuf repeated-field wrapper that semantically expects one ID.

But this costs almost nothing to falsify.

### Probe 2B — multiple `hizoJc` RPCs in one `batchexecute`

If 2A fails, construct one HTTP batch containing:

```
hizoJc(source1)
hizoJc(source2)
hizoJc(source3)
...
```

with distinct batch request indices.

Generic Google `batchexecute` definitely supports multiple RPC entries. [[GitHub]

GitHub](https://github.com/pndurette/pybatchexecute) What remains **unverified** is whether NotebookLM accepts repeated instances of the same `hizoJc` RPC and how large a batch it tolerates.

Test:

```
batch size = 1, 2, 4, 8, 16
```

Don't jump to 50.

If one HTTP request can retrieve eight transcripts, even if Google's backend processes the eight somewhat serially, you have removed much of the fixed request/transport overhead. If Google processes them concurrently internally, this could be a much larger jump.

This is genuinely outside the search space you've described.

## 3. Content-only concurrency, not more workers

This is importantly different from your failed worker-count experiments.

Don't increase:

```
source adds
materialization load
retry pools
active windows
```

Instead, keep all of that exactly at the 3+3 leader configuration and change only this:

```
ready source IDs
      ↓
persistent client
      ↓
Semaphore(1 → 2 → 4)
      ↓
hizoJc
```

The current operation is read-only fulltext retrieval. NotebookLM's other Python implementation is async, so this is straightforward to test independently of the orchestration system. [[GitHub]

GitHub](https://github.com/teng-lin/notebooklm-py/blob/main/docs/python-api.md?utm_source=chatgpt.com)

Run a **ready-only benchmark**:

```
C=1
C=2
C=4
C=8
```

Predictions:

- 
If `C=2` approaches 2× throughput, the current ceiling is client-side serialization.

- 
If latency doubles and throughput stays flat, Google is serializing/throttling per profile.

- 
If `C=2` improves substantially but `C=4` regresses, you've found the actual read-concurrency knee.

- 
If RESOURCE_EXHAUSTED rises immediately, the server is enforcing a read-side quota.

This experiment is much cleaner than an end-to-end worker A/B because the source-age cliff can't contaminate the result.

## 4. Remove the batch barrier

Your pipeline description suggests:

```
ADD 50
   ↓
WAIT until materialized
   ↓
FETCH 50
```

I would change the model to:

```
ADD batch
   ↓
poll notebook
   ↓
source A ready ──────→ FETCH A
source B ready ──────→ FETCH B
source C not ready
source D ready ──────→ FETCH D
...
```

In other words, **materialization becomes a producer of source-ready events**, rather than a barrier separating two pipeline phases.

The extractor consumes those events immediately with bounded concurrency.

This is not another active-window policy. It removes a synchronization point.

The relevant measurement is:

```
source_ready_at → source_content_start_at
```

If that distribution currently contains meaningful tens-of-seconds delays for early-ready sources, the barrier is feeding your 200-second age cliff.

If the delay is already approximately zero, kill this idea immediately.

## 5. Collapse “is it ready?” and “give me the content”

The current source-content service itself has a `wait` mode that repeatedly calls `get_source_fulltext()` until content exists. [[GitHub]

GitHub](https://raw.githubusercontent.com/jacob-bd/gemini-notebook-mcp-cli/main/src/notebooklm_tools/services/sources.py) Separately, the Python API provides multi-source readiness waiting. [[GitHub]

GitHub](https://github.com/teng-lin/notebooklm-py/blob/main/docs/python-api.md?utm_source=chatgpt.com)

That suggests another architecture:

```
add source
    ↓
start future/task for content
    ↓
hizoJc → empty/not-ready
    ↓
backoff
    ↓
hizoJc → transcript
```

instead of:

```
add
→ poll notebook status
→ declare materialized
→ enqueue content command
→ hizoJc
```

I wouldn't implement this before #1–#3, because poorly chosen polling could recreate the retry-pressure problem you already saw. But coupled with bounded async tasks it could remove one coordination stage and eliminate the "old-window Batch-1" phenomenon entirely.

# The experiment I would run next

Not another 200-video end-to-end soak.

Create a **source-content service-time benchmark** using already-ready sources:

```
200 source IDs from one healthy profile

Mode A: existing nlm subprocess, serial
Mode B: persistent client, serial
Mode C: persistent client, concurrency=2
Mode D: persistent client, concurrency=4
Mode E: batchexecute batch=2
Mode F: batchexecute batch=4
Mode G: batchexecute batch=8
```

Record:

```
completed
wall_time
effective VPH
request count
p50/p95/p99 request latency
p50/p95 per-source completion latency
HTTP 429
RPC RESOURCE_EXHAUSTED
empty/not-ready
other errors
bytes returned
```

Use the **same already-ready source population** for every mode.

That gives you a genuinely discriminating result:

```
Persistent serial wins
    → CLI/process/auth/connection overhead was the bottleneck.

Concurrency wins
    → backend supports parallel independent reads;
      current serialization was artificial.

RPC batching wins
    → fixed per-request overhead was dominant.

Nothing wins
    → ~1 sec is probably a provider-side per-source service-time
      or per-account serialization constraint.
```

Only in that last case would I return to pipeline-level mechanisms such as barrier elimination.

## One architectural point I would change immediately in the mental model

I would stop describing the blocked lever as:

> 
"Batch-1 old-window `nlm source content` command latency; already as narrow as possible."

It isn't necessarily as narrow as possible.

The **command** is narrow.

The **transport granularity is not**.

The implementation currently maps:

```
1 video
→ 1 CLI operation
→ 1 get_source_fulltext()
→ 1 hizoJc
→ 1 batchexecute HTTP POST
```

and Google provides a transport explicitly capable of carrying multiple RPC operations per POST. [[GitHub]

GitHub+2[GitHub]

GitHub+2](https://raw.githubusercontent.com/jacob-bd/gemini-notebook-mcp-cli/main/src/notebooklm_tools/core/sources.py)

That is the first place I would spend engineering effort.

### Critical-thinking check

**Current belief:** the ~3.6–3.8k ceiling is probably a serialized source-content service-time ceiling rather than an optimal source-age cadence.

**Strongest alternative:** Google's backend itself serializes or rate-limits `hizoJc` per account at approximately this rate; local subprocess/RPC serialization is merely exposing that limit.

**Discriminating test:** ready-only persistent-client + concurrency + multi-RPC benchmark above.

**What would change my mind:** persistent client, concurrency=2/4, and true `batchexecute` batching all produce essentially the same ~1 source/sec/profile behavior without increased errors.

If that happens, I would stop optimizing the `hizoJc` client entirely and move the next search into **server-side queue independence / notebook topology / overlapping source creation and extraction**, because then the ceiling has been demonstrated to live on Google's side rather than yours.
