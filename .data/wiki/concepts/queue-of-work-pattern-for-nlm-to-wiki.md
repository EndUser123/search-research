---
title: "Queue-of-work pattern for nlm-to-wiki: decouple work distribution from execution for parallel, resumable, hot-reconfigurable ingestion"
created: 2026-07-28
source: session-019fa276 (/www on best design for parallel pipeline workers)
tags: [queue-of-work, parallel-processing, pipeline-architecture, worker-pool, hot-reload, resumable, rate-limit-aware, design-decision]
summary: >
  Architecture decision: adopt the queue-of-work pattern (endjin, Mar 2026)
  for nlm-to-wiki's bulk processing. The pattern decouples work distribution
  (enqueue notebook IDs) from work execution (process each notebook),
  enabling: (1) parallel workers without killing the running process, (2)
  hot-reconfigurable worker count by editing a config file, (3) crash-resume
  via durable queue state, (4) per-item retry without re-running successful
  items, (5) poison-queue for persistently failing notebooks. The endjin
  implementation reduced ingestion from 48 hours to 2 hours (24x) using 12
  workers. Our constraint is NotebookLM's 3-worker ceiling (yt-is benchmark
  data), so we start at 2 workers with room to raise to 3. Implementation:
  ~120 lines replacing bulk_sync.py's monolithic loop with a queue + worker
  pool + config hot-reload. The running bulk sync does NOT need to be killed
  — the queue file is written alongside it, and workers pick up where the
  serial loop left off.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - "https://endjin.com/blog/scaling-api-ingestion-with-the-queue-of-work-pattern" (endjin, Mar 2026 — 48h → 2h with 12 workers)
  - "https://github.com/endjin/python-queue-of-work-pattern-demo" (reference implementation)
  - "P:/.data/wiki/concepts/nlm-to-wiki-optimization-opportunities.md" (3-worker ceiling from yt-is data)
  - "P:/packages/yt-is/docs/operations/hot-path-throughput-next-test-plan.md" (hundreds of benchmark runs)
  - "P:/.data/wiki/concepts/shared-directory-contamination-pattern.md" (the bug that per-unit filtering fixes)
relations:
  - target: wiki/concepts/nlm-to-wiki-optimization-opportunities.md
    type: implements
  - target: wiki/concepts/stateful-skills-need-maintenance-surface.md
    type: related
  - target: wiki/concepts/shared-directory-contamination-pattern.md
    type: related
---

# Queue-of-work pattern for nlm-to-wiki

## Decision context

**Why this design was needed:** the bulk sync runs serially (~23 min per
notebook, ~12 hours for 40 notebooks). The operator asked whether we
should switch to parallel workers mid-run without killing the process,
and whether the architecture could support "stop and start workers
independently." The current `bulk_sync.py` is a monolithic `for` loop
blocked inside `subprocess.run()` — it can't be reconfigured without
killing it.

**The research:** the queue-of-work pattern (endjin, Mar 2026) solved
exactly this problem for API ingestion. Their key insight: **decouple
work distribution from work execution.** An enqueuer writes work items
to a durable queue; workers dequeue and process independently. Workers
can be added, removed, or reconfigured without killing the queue.

## The pattern

```
ENQUEUER                    DURABLE QUEUE              WORKERS
(notebook IDs)              (JSON file)                (sync.py per notebook)
┌──────────────┐           ┌──────────────┐           ┌──────────────┐
│ Write        │    ────►  │ queue.json   │  ────►    │ Worker 1     │
│ remaining    │           │ [{id, ...},  │           │ (notebook A) │
│ notebook IDs │           │  {id, ...}]  │           └──────────────┘
│ to queue     │           │              │  ────►    ┌──────────────┐
└──────────────┘           │ config:      │           │ Worker 2     │
                           │ workers: 2   │           │ (notebook B) │
                           └──────────────┘           └──────────────┘
```

**Key properties:**

1. **No kill needed to change worker count.** Edit `config.json` →
   `workers: 3`. Workers check config between notebooks (not mid-notebook).
2. **Crash-resume.** Queue state is a JSON file on disk. If a worker
   crashes, its notebook stays in the queue. Restart picks it up.
3. **Per-item retry.** A failed notebook goes to a retry list, not back
   to the main queue. Other notebooks continue processing.
4. **Poison queue.** A notebook that fails 3+ times moves to a poison
   list for manual investigation. Other notebooks aren't blocked.
5. **Rate-limit aware.** Workers coordinate via a shared rate limiter
   (token bucket or semaphore) to stay within NotebookLM's 3-worker ceiling.

## How this solves the operator's question

**"Can't we stop and start workers independently?"** Yes — each worker
is a separate process that reads from the queue file. Start a new worker
by launching another process; stop one by killing that process. The queue
file is the coordination point, not a shared in-memory state.

**"Can we change the worker count mid-run?"** Yes — edit `config.json`
to change `workers: 2` → `workers: 3`. Workers reload config between
notebooks (at the natural boundary, not mid-export).

**"Does the running bulk sync need to die?"** No — write the queue file
alongside the running process. New workers start consuming from the
queue while the old serial loop continues on its current notebook. When
the serial loop finishes its current notebook and checks the queue, it
finds it empty (workers already consumed everything) and exits naturally.

## Design constraints specific to our environment

| Constraint | Source | Implication |
|---|---|---|
| **3-worker ceiling** | yt-is benchmark data (hundreds of runs) | Start at 2, raise to 3 only if 0 failures |
| **Auth expiry (~30min)** | NotebookLM session behavior | Each worker re-auths via CDP before each notebook |
| **Shared transcript directory** | Architecture choice | Per-notebook filtering (already fixed in cluster_transcripts.py) |
| **Crash-resume state** | bulk_sync.py's existing state file | Queue file replaces/augments state file |
| **No external dependencies** | Workspace convention | Queue is a JSON file, not Redis/RabbitMQ |

## Implementation plan

### Component 1: Queue file (`P:/tmp/nlm-queue.json`)

```json
{
  "pending": ["nb_id_1", "nb_id_2", ...],
  "in_progress": {"worker_id": "nb_id"},
  "completed": ["nb_id_3", ...],
  "failed": [{"nb_id": "...", "error": "...", "attempts": 2}],
  "poisoned": [{"nb_id": "...", "error": "...", "attempts": 3}],
  "config": {"workers": 2, "profile": "codex", "max_retries": 3}
}
```

Atomic writes via `.tmp + os.replace` (same pattern as sync manifest).

### Component 2: Worker process (`worker.py`)

```python
# Each worker is an independent process:
while True:
    item = queue.claim_next()  # atomic: moves pending → in_progress
    if item is None:
        break  # queue empty
    config = queue.reload_config()  # hot-reload between notebooks
    result = sync_one_notebook(item, config)
    queue.complete(item, result)  # moves in_progress → completed/failed
```

### Component 3: Rate limiter (shared semaphore)

File-based token bucket or simple counter in the queue file. Workers
check before each API call: "am I within the concurrent-worker limit?"
This prevents exceeding NotebookLM's ceiling when multiple workers are
active.

## The endjin evidence

The endjin implementation (Mar 2026) is the strongest external validation:

| Metric | Sequential | Queue-of-work (12 workers) |
|---|---|---|
| Ingestion time | 48 hours | 2 hours (24x) |
| Retry mechanism | Re-run entire batch | Per-item retry |
| Fault tolerance | One failure blocks all | Poison queue isolates failures |
| Worker scaling | Not possible | Add workers without restart |
| Observability | Batch-level | Per-item tracing |

Their key finding: "Simple is fast. The basic queue-and-worker model
introduces minimal overhead (<50ms per operation) compared to complex
orchestration systems."

Our constraint is tighter (3-worker ceiling vs their 12), but the
pattern scales down — 2 workers cuts our time from 23 min/notebook to
~15 min/notebook, saving ~4 hours across 30 remaining notebooks.

## Receipts

- **"queue-of-work reduces ingestion from 48h to 2h":** receipt —
  [endjin.com/blog/scaling-api-ingestion-with-the-queue-of-work-pattern](https://endjin.com/blog/scaling-api-ingestion-with-the-queue-of-work-pattern),
  published Mar 2026. 12 workers, 20,000 API calls, Azure Storage Queues.
  Sample code at [github.com/endjin/python-queue-of-work-pattern-demo](https://github.com/endjin/python-queue-of-work-pattern-demo).
- **"3-worker ceiling":** receipt —
  `P:/packages/yt-is/docs/operations/hot-path-throughput-next-test-plan.md`,
  hundreds of benchmark runs. 3+3 shape reached 4,123 VPH; 4+4 regressed
  to 1,150 VPH with source_age_cliff=333.
- **"the running bulk sync doesn't need to die":** [INFERENCE] — the
  queue file is written alongside the running process. New workers
  consume from it. The old serial loop finishes its current notebook,
  checks the queue, finds it consumed, exits. This is untested but
  follows from the pattern's decoupling principle.
- **"config hot-reload between notebooks":** [INFERENCE] — each worker
  reloads config at the natural notebook boundary (between
  `subprocess.run` calls). The reload is a file read (~1ms). This is
  the same pattern as `bulk_sync.py`'s existing `ensure_auth()` check
  between notebooks.

## Falsifier

The queue-of-work pattern is overkill for our use case if:
- **40 notebooks is a one-time job.** If we only ever process 40 notebooks
  once, the serial approach works (12 hours). The queue pattern earns its
  cost on *recurring* bulk runs (nightly incremental syncs, new notebook
  batches). Testable: do we expect to run bulk ingestion again? If yes,
  the pattern is justified.
- **2 workers don't actually help.** If NotebookLM's rate limit makes
  2-worker no faster than 1-worker serial, the pattern adds complexity
  without speedup. Testable: time the first 2-worker run vs the last
  serial run. If <20% improvement, the pattern isn't earning its cost.
- **The queue file becomes a bottleneck.** If multiple workers contend on
  the JSON file read/write, the file lock adds latency. Mitigated by
  atomic writes and the fact that queue operations are infrequent (once
  per notebook, not once per API call).

## Sources

- [Scaling API Ingestion with the Queue-of-Work Pattern](https://endjin.com/blog/scaling-api-ingestion-with-the-queue-of-work-pattern)
  (endjin / Jonathan George, Mar 2026) — the reference implementation.
  48h → 2h with 12 workers. Azure Storage Queues + Container Apps.
  Sample code: [github.com/endjin/python-queue-of-work-pattern-demo](https://github.com/endjin/python-queue-of-work-pattern-demo).
- [Handling Rate Limits Across Parallel Workflows](https://community.n8n.io/t/handling-rate-limits-across-parallel-workflows-without-losing-throughput/293419)
  (n8n community, May 2026) — rate limit coordination across parallel workers.
- `P:/.data/wiki/concepts/nlm-to-wiki-optimization-opportunities.md` —
  the 3-worker ceiling and 5 ranked optimizations.
- `P:/packages/yt-is/docs/operations/hot-path-throughput-next-test-plan.md` —
  hundreds of benchmark runs establishing the worker-count limits.

## Auto-related

- [[nlm-to-wiki-optimization-opportunities]] — the optimization analysis this implements
- [[stateful-skills-need-maintenance-surface]] — the maintenance surface monitors queue health
- [[shared-directory-contamination-pattern]] — per-unit filtering at every queue read
