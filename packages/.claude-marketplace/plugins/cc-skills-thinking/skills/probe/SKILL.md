---
name: probe
description: Performance/run-data hypothesis engine — turns ambiguous gaps into ranked, testable hypotheses via quantile analysis, cross-correlated attribution, parallel-efficiency computation, and LLM-judge failure clustering. Reads RUN_INDEX.json and benchmark metrics. Use when something is slow or unexplained and you can't pinpoint where, or when "I don't know what I don't know about this data."
version: 1.2.0
status: stable
category: meta
enforcement: advisory
workflow_steps:
  - step_orient: Read RUN_INDEX.json at target root — enumerate runs, field presence, status, known issues. Fail if absent.
  - step_hypothesize: Generate ranked hypotheses with explicit confidence labels
  - step_quantile: Check distribution shape before claiming uniform effects
  - step_correlate: Cross-correlate metrics to find causal chains
  - step_refine: Narrow to smallest discriminating test
triggers:
  - /probe
  - /probe_quantile
suggest:
  - /genius
  - /reason
  - /skeptic
---

# /probe — Data-Analysis Hypothesis Engine

## Purpose

Turns ambiguous performance gaps into ranked, testable hypotheses. Generates concrete analytical questions, then finds the data to answer them — without running new benchmarks.

Use when: "I don't know what I don't know about this data", "the gap is unexplained", "something is slow but I can't pinpoint where".

Not for: trivial lookups, code implementation, or decisions already supported by strong evidence.

## The Core Problem It Solves

Most performance investigations leap to the apparent bottleneck (e.g., "extract is slow") without checking whether the bottleneck is the cause or an effect. `/probe` forces distributional and correlational thinking before diagnosis.

## The Five Techniques

### 1. Quantile Analysis (Akinshin)

**Principle:** Aggregate averages mask bimodal distributions. A system where p50=10s and p99=300s is not "slow" — it's bimodal. Different causes, different fixes.

**When to use:**
- A metric shows a large gap but the cause is unknown
- You've been told the system is "uniformly slow" — verify before believing
- A few outlier sources/workers/items are dragging down the average

**How to probe:**
1. Name the metric and its aggregate (mean, total, count)
2. State the comparison axis and scale assumption
3. Ask: is the distribution unimodal or bimodal?
4. If bimodal: what separates the fast half from the slow half?
5. If unimodal: is the variance itself informative (high variance = unstable, low variance = consistent)?

**Signal to check:** p90/p99 >> p50 → outliers dominant. p50 >> p90 → hidden bottleneck affecting most requests.

**Failure mode:** Confusing quantile spread with sample size. Small samples produce wide quantile spreads that aren't meaningful.

### 2. Cross-Correlated Attribution (LongTale)

**Principle:** Idle time correlates with slow sources? Or with worker imbalance? Attribution questions have different answers depending on what you cross-check first.

**When to use:**
- A gap appears between two groups (Pro vs Free, worker-01 vs worker-02)
- You have two candidate causes and can't distinguish them
- The obvious cause explains the effect, but the explanation feels too clean

**How to probe:**
1. List all metrics for the gap period
2. Compute pairwise correlation across workers/sources/time buckets
3. Flag which correlation is strongest — that is the most likely cause
4. State the comparison axis (per-worker, per-source, per-batch)
5. Name the falsification condition: "this would be wrong if the correlation is spurious"

**Signal to check:** If `worker_idle_wait_s` correlates strongly with `source_ready_age_s_avg`, the cause is source aging. If it correlates with `content_fetch_command_elapsed_s_avg`, the cause is command latency.

**Failure mode:** Correlation ≠ causation. A third variable (backend rate limits, network congestion) can drive both metrics independently.

### 3. Operational Analysis (Plumber)

**Principle:** Map pipeline stages and find where asynchrony or parallelism breaks down. A system where stage A takes 100s and stage B takes 10s is not a "stage B problem" — it's a stage A blocking stage B problem.

**When to use:**
- You have timing breakdowns for distinct pipeline stages
- A stage that "should be fast" dominates wall time
- Overlapping stages are running sequentially instead of in parallel

**How to probe:**
1. List all pipeline stages with their elapsed times
2. Identify which stages overlap vs. which are sequential
3. Compute overlap ratio: `(sum of stage times) / wall elapsed time`
4. If ratio >> 1: stages are running in parallel — look at resource contention
5. If ratio ≈ 1: stages are sequential — the blocking stage is the constraint
6. State the blocking stage explicitly

**Signal to check:** `overlap ratio = 2.3` means 2.3 stages worth of work fit in 1 wall-second → parallelism is working but some stage is still the constraint.

**Failure mode:** Misidentifying the blocking stage. If stage B is slow but stage A blocked it, fixing B won't help until A is addressed.

### 4. Parallel Efficiency (oh-my-claudecode pattern)

**Principle:** If multiple workers are available but throughput is far below linear, compute parallel efficiency: `(worker1_active + worker2_active + ...) / wall_elapsed_s`. If efficiency is far below the worker count, something is serializing what should be parallel work.

**Formula:** `parallel_efficiency = (sum of worker active times) / wall_elapsed_s`
- Target: close to worker count (3 workers → efficiency near 3.0)
- Flag: efficiency << worker count → workers are blocking each other or starving for work

**When to use:**
- You have multiple workers processing in parallel but throughput is sub-linear
- You want to distinguish "workers are busy but blocked" from "workers are idle"

**How to probe:**
1. Compute `parallel_efficiency` from worker idle wait and active times vs wall elapsed
2. If efficiency << worker count: workers are waiting on a shared resource (I/O, lock, rate limit)
3. If efficiency ≈ worker count but throughput is low: workers are doing redundant work

**Failure mode:** Measuring wall time that includes startup/cleanup phases that are inherently serial. Always measure only the parallel phase.

### 5. LLM-as-Judge Failure Clustering (Distributional pattern)

**Principle:** When you don't know what the failure mode looks like, use an LLM judge to scan failure logs and classify them — then cluster by mechanism, not surface error string.

**When to use:**
- You have failure logs but no explicit failure taxonomy
- `command_failed` or similar generic failure codes dominate
- You want to find the structural failure type without enumerating all error strings

**How to probe:**
1. Feed a sample of failure logs to an LLM with a classification prompt: "For each failure, identify the mechanism: timeout / rate-limit / auth / content-quality / backend-error / unknown"
2. Count cluster sizes — large clusters = common failure mechanisms
3. For each cluster: is the mechanism instrumentable, or is it a backend black box?
4. Track cluster sizes over time — a cluster that doesn't shrink after your fix = wrong mechanism

**Prompt template:** "You are a failure analyst. For each failure event below, classify it by mechanism (timeout / rate_limit / auth / content_below_threshold / backend_error / unknown). Return a count per category with one representative example."

**Failure mode:** LLM judge classifier drift — the judge changes its classification criteria between runs, making cluster size comparison unreliable across time periods.

## Workflow

### Step 0: Orient (Required — must complete before any hypothesis)

Read `RUN_INDEX.json` at the target root. If absent, look for a run index at the canonical path for this corpus.

**What to extract:**
- All available runs and their status (ok / invalidated / partial)
- Field presence matrix: which metrics are actually present vs. absent in each run
- Known issues per run
- Related runs and the comparison axes available

**What to flag immediately:**
- Any metric where presence is inconsistent across runs → non-comparable until verified
- Any run with status ≠ ok → interpret its data with appropriate skepticism
- Any run not listed in RUN_INDEX.json that exists on disk → investigate or exclude

**Orient failure mode:** If no index exists, the corpus may not follow standard orientation conventions. Stop. Do not proceed to hypothesis generation until you have enumerated what exists. Manually listing run directories and their summary files is acceptable as a fallback — but it is mandatory, not optional.

### Step 1: Hypothesize

Generate 2-3 ranked hypotheses before touching individual run data. For each:
- State the hypothesis clearly
- Name the metric(s) that would confirm or refute it
- Label your confidence: **VERIFIED / INFERRED / UNPROVEN**
- State the falsification condition: "this would be wrong if ___"

**Mechanism-invention guard:** If you generate a causal explanation (e.g., "coordination overhead," "queue ordering bias"), you must also state:
- `hypothesis_status:` VERIFIED | INFERRED | UNPROVEN | MY BET
- `falsification_condition:` "this would be wrong if ___"
- `required_evidence:` list of measurements needed to move from UNPROVEN to INFERRED

Do not present invented mechanisms as conclusions. UNPROVEN mechanisms dressed as conclusions are the highest-value failure mode in performance analysis.

### Step 2: Quantile

Check the distribution before proceeding:
- Compute p50 / p90 / p99 for the key metric
- If spread is large (>3x ratio p99/p50): outlier-dominated, not uniform
- If spread is small: claim "uniform" is defensible

**Field compatibility note:** Before comparing a metric across runs, enumerate the actual keys present in each run's aggregate. A field present in run A but absent in run B means the metric is not cross-run comparable without a migration or compatibility layer. Flag non-comparable metrics explicitly. Do not treat absent fields as zero.

### Step 3: Correlate

Cross-check metrics to find the causal chain:
- Does `worker_idle_wait_s` correlate with `source_ready_age_s`?
- Does `extract_elapsed_s` correlate with `content_fetch_command_elapsed_s`?
- Does `command_failed` correlate with source age or with account class?

### Step 4: Refine

Narrow to the smallest discriminating test:
- One metric, one comparison axis, one expected outcome
- State what result would change your recommendation
- If test is impractical, name the cheapest proxy

## Output Shape

```
HYPOTHESES
Ranked by likelihood with confidence labels

QUANTILE SIGNAL
p50 / p90 / p99 of key metric — shape description

CORRELATION SIGNAL
Strongest pairwise correlation — causal interpretation

PARALLEL EFFICIENCY
Worker count vs efficiency ratio — blocking or idle?

FAILURE CLUSTERING
LLM-judge cluster counts — common mechanisms

REFINED HYPOTHESIS
One specific question the data can answer

NEXT TEST
The single measurement that would most reduce uncertainty
```

## Evidence Labels

Every claim:
- **VERIFIED** — confirmed by data inspection
- **INFERRED** — logical from verified facts
- **UNPROVEN** — hypothesis, needs test
- **MY BET** — strong opinion on thin evidence

## Tone

Direct and specific. Named metrics, named comparisons, no hedging.

## Skip For

- Trivial questions with obvious answers
- Implementation requests (use /reason for decisions)
- When you already know the root cause and just need to implement

## Trigger Examples

```
/probe why is extract time 700s higher in Free lane vs Pro
/probe command_failed distribution across workers
/probe what explains the 366 VPH gap between Pro and Free lanes
/probe --quantile source_ready_age_s distribution across cohorts
/probe parallel efficiency across the Free lane workers
/probe cluster the failure modes in the benchmark logs
```