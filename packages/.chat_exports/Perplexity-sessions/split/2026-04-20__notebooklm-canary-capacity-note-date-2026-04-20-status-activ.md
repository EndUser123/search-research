---
title: "'NotebookLM Canary Capacity Note
Date: 2026-04-20
Status: Active operational note
What the canary showed
The current yt-"
date: "2026-04-20"
mode: "CONCISE"
uuid: "e98e80eb-ba52-425f-98fc-2567945fc558"
entry_count: 4
---

## Human

"NotebookLM Canary Capacity Note
Date: 2026-04-20
Status: Active operational note
What the canary showed
The current yt-is backlog canary is hitting a NotebookLM add failure in the reusable industrial path.
Observed pattern:
nlm_batch_subbatch_add_started
about 123-124s later nlm_batch_subbatch_add_completed
returncode: 1
failure_reason: add_failed
This happened with both 300-source and 150-source notebook add windows.
NotebookLM's documented notebook cap is 300 sources, so the live question is how close we can safely get before rotating to a fresh notebook.
The failure is in the NotebookLM add boundary, not in routing, Selenium scraping, or transcript fallback.
What this means
The live bottleneck is NotebookLM notebook reuse / add capacity, not the browser automation ADR ideas.
The earlier browser-automation ADR is now stale for this issue and should not be used as the next action guide.
The reusable notebook path needs a capacity guard, not a larger add window.
Practical guidance
Keep the NotebookLM add window below the size that triggers source_add_failed in live canaries.
Rotate to a fresh notebook before the reusable notebook approaches the 300-source NotebookLM cap.
Log notebook id and current source count before each add attempt so failures can be correlated with notebook fullness.
Keep using completed-worker totals and transcript-cache growth as throughput truth.
What not to do
Do not increase the add window again until notebook-capacity behavior is understood.
Do not use the stale browser-automation ADR as the primary reference for this canary failure.
Do not treat backlog-derived scan rates as throughput."


Is this something you can help with?

## Assistant

Yes, this is very much something I can help with. Based on what you pasted, you’re essentially writing an ADR-style “capacity note” for a NotebookLM-based pipeline, and you want to (a) validate the diagnosis and (b) turn it into concrete engineering guidance.

I’ll respond at three levels:

1. Interpret/validate what your canary is actually telling you  
2. Translate it into system constraints and guardrails  
3. Suggest minimal design changes to your current “reusable industrial notebook” path

I’ll assume you’re on current public NotebookLM where per-notebook limits are closer to 50 sources (for the mainstream tiers) even though your note mentions 300; the *exact* cap is a product detail that has shifted, but the pattern you’re seeing (add failures near the cap) is consistent with “hard-ish” per-notebook source limits.[1][2]

***

## 1. Interpreting the canary signal

From your note:

- You see `nlm_batch_subbatch_add_started` → ~123–124s → `nlm_batch_subbatch_add_completed`  
- `returncode: 1`  
- `failure_reason: add_failed`  
- This occurs for both 300-source and 150-source “add windows”  
- You’ve confirmed:
  - Routing OK  
  - Selenium scraping OK  
  - Transcript fallback OK  
  - Failure is at the NotebookLM add boundary

### What this implies

1. **The dominant failure mode is capacity, not transport or scraping**

   Since you’re seeing a consistent pattern tied to the *add* operation (and not varied HTTP/network errors or scraping variability), that’s a classic signature of hitting either:

   - A **per-notebook source cap** (hard limit: “cannot add more sources”)  
   - A **per-operation add cap** (batch too large: “cannot add this many at once”)  
   - A **rate/usage limit**, if Google is implementing guardrails that present as generic “failed source” states

   NotebookLM’s current public docs explicitly mention *per-notebook* source limits (e.g., 50 sources per notebook and large per-source limits), and many users report “red” or silently failing sources once they get near those limits.  That matches your observation that the bottleneck is “NotebookLM notebook reuse / add capacity.”[3][4][1]

2. **The ~2-minute latency is consistent with a backend attempting ingestion then failing**

   A ~120s latency suggests the backend is actually trying to ingest/index the batch (Gemini/embedding + indexing) before it bails with a non-zero return code. That’s consistent with:

   - Internal indexing timeouts  
   - Internal quota checks that only trigger once processing is underway  
   - “Soft” caps that aren’t validated synchronously with the initial request

3. **Your previous ADR about browser automation is now orthogonal**

   The canary provides stronger evidence that “browser automation vs. Selenium vs. routing” is not the constraint. You’re saturating the *NotebookLM per-notebook capacity surface*, not the page scraping or nav logic. Treat that ADR as informational but not prescriptive for this specific failure, exactly as your note says.

So: your diagnosis (“live bottleneck is NotebookLM notebook reuse / add capacity”) is consistent with both your logs *and* how NotebookLM’s limits and failure modes are described externally.[2][4][1]

***

## 2. Turn this into explicit system constraints

You already have good qualitative guidance in the note. I’d formalize it into explicit constraints your pipeline respects automatically.

### 2.1. Treat per-notebook capacity as a hard constraint

Given Google’s own docs and ecosystem experience:

- Per-notebook source caps are fixed and non-negotiable:  
  - Public docs talk about ~50 sources per notebook as a current cap in many tiers.[1][2][3]
  - You mention “documented” 300, which likely reflects an older or different tier/documentation you saw. Either way, you must design as if the backend *can and will* enforce a hard cap.

Assumption: In your environment, the practical usable cap is **N_effective < N_documented** because you’re seeing failures at 150–300 adds depending on reuse.

I’d explicitly define:

- `N_doc_cap`: what the docs or UI say (e.g., 50 or 300)  
- `N_empirical_cap`: what your canaries observe (source count at first consistent failure)  
- `N_guard`: your “safe” operating ceiling (e.g., 0.7–0.8 × N_empirical_cap or simply a fixed safety margin below it)

### 2.2. Translate canary into guard values

Given your observations:

- Both 300-source and 150-source *add windows* hit `add_failed`, so:
  - There’s some combination of “current notebook fullness” + “batch size” that pushes the notebook over a backend threshold.
  - You don’t yet know whether the primary driver is the *total* number of sources, the *size* of the sources, or the *batch size of the add* itself.

Your note’s proposed guidance is on point:

- “Keep the add window below the size that triggers `source_add_failed` in live canaries.”
- “Rotate to a fresh notebook before the reusable notebook approaches the cap.”
- “Log notebook id and current source count before each add attempt so failures can be correlated with notebook fullness.”

To make this operational:

1. **Log schema** (every add attempt)
   - `timestamp`  
   - `notebook_id`  
   - `current_source_count` (pre-add; even if you approximate)  
   - `batch_size` (# sources in this window)  
   - `estimated_batch_tokens` (if you can)  
   - `result` (success / failure)  
   - `failure_reason` (raw + normalized)  
   - `latency_ms`

2. **Derive:**
   - Minimal `current_source_count` at which failures begin for a given `batch_size`  
   - Minimal `batch_size` that fails for a given `current_source_count`  

3. **Set guardrails:**
   - `max_total_sources_per_notebook = min(N_empirical_cap - safety_margin, N_doc_cap - safety_margin)`  
   - `max_add_batch_size = smallest batch size that has *never* failed in canaries at high load`

Only then adjust your production guard constants. Until you’ve done this pass, your note’s “don’t increase the add window” constraint is wise.

***

## 3. Concrete changes to your “reusable notebook” path

You already separated “browser automation ADR” from “NotebookLM add capacity issue.” The action now is to *instrument and gate* the reusable path.

### 3.1. Capacity guard design

Implement a guard component around every “add sources to notebook” call:

**Inputs:**

- `notebook_id`  
- `planned_batch_sources[]` (new sources)  
- Known or estimated `current_source_count` for `notebook_id`

**Logic:**

1. Look up `current_source_count` for `notebook_id` from your own tracking store.  
   - If not known, compute by querying NotebookLM’s UI/DOM once out-of-band and then track locally.

2. If `current_source_count >= max_total_sources_per_notebook`:
   - **Action:** Do **not** call NotebookLM.  
   - Instead: create/allocate a **fresh notebook**, update routing metadata, and send the batch there.

3. Else, if `len(planned_batch_sources) > max_add_batch_size`:
   - Split into chunks `<= max_add_batch_size` and process sequentially, with state updates in between.

4. After each successful add:
   - Increment your tracked `current_source_count` for that notebook.

This is exactly what your note hints at: “reusable notebook path needs a capacity guard, not a larger add window.”

### 3.2. Notebook rotation policy

Define explicit rotation triggers:

- **Hard rotation trigger:** when `current_source_count >= N_guard`.  
- **Soft rotation trigger:** when canary error rate for a notebook exceeds X% over last Y attempts, even if count < N_guard (to catch other hidden caps like total tokens per notebook).

On rotation:

- Create a new NotebookLM notebook via UI automation.  
- Persist:
  - `notebook_id`  
  - `created_at`  
  - `source_count = 0`  
  - `logical_topic` (what this notebook is for)  
- Update routing so new sources for that logical pipeline go to the new notebook.

You lose cross-notebook querying (NotebookLM notebooks are siloed and don’t share context).  That’s a fundamental product limitation, not something you can fix. Design your analysis logic so later stages know they’re dealing with **shards**.[5][1]

### 3.3. Canary-specific guidance (refinement)

Your note’s “Practical guidance” is solid. I’d sharpen it into “rules the code must obey”:

**Practical rules:**

1. **Never size the add window by backlog.**  
   Backlog-derived rates ≠ system throughput. Your note already says “Do not treat backlog-derived scan rates as throughput.” Keep that.

2. **Use empirical caps, not marketing caps.**  
   Even if docs say “300 sources,” treat the first consistent failure boundary as `N_empirical_cap` and operate with a margin under that.

3. **Promote canary results to configuration.**  
   - Canary periodically pushes updated `max_add_batch_size` and `max_total_sources_per_notebook` into configuration for prod.
   - If canary sees worsening capacity (failures at fewer sources), you automatically tighten the guard.

4. **Pin blame on NotebookLM, not your infra, when appropriate.**  
   Given you have Selenium/scraping/routing validated, a recurring `add_failed` near capacity is signal that the remote service is the limit. Don’t waste engineering cycles on browser automation changes for this issue.

***

## 4. What I can do next, concretely

If you want deeper help, I can:

- Help you design the **logging schema and guard API** between your worker(s) and the NotebookLM automation layer.  
- Draft a minimal **“NotebookLM capacity ADR”** that supersedes your stale browser-automation ADR and encodes the rules above in your own format.  
- Work through your current pipeline step-by-step (workers → transcript cache → canary → NotebookLM add) and propose **smallest possible structural changes** that achieve:
  - capacity-awareness  
  - rotation  
  - clean failure correlation (notebook id + source count logging)

***

### Clarifying question

To make this precise, I need to know how you’re currently tracking notebook state:

- Do you already have a persistent store that tracks `notebook_id → source_count`, or are you treating NotebookLM as “stateless” and inferring fullness only from failures?

If you can tell me that, I can sketch an exact guard/rotation layer tailored to your existing architecture.

## Human

"Mostly yes, but it’s only partly reliable.
What makes sense:
It correctly identifies the problem as a NotebookLM add boundary / notebook reuse capacity issue.
It correctly says the browser-automation ADR is not the right fix for the failure we saw.
It correctly pushes toward logging source count before each add and rotating notebooks before capacity.
What I would not trust:
The claim that current public NotebookLM limits are “closer to 50 sources” is not something I’d use here.
Its external citations look shaky, and they conflict with the NotebookLM cap you already said is documented as 300.
It mixes general NotebookLM lore with your actual live canary evidence. Your logs are the stronger signal.
So the answer to your question is:
Does it make sense? Yes, at the architectural level.
Does it answer the right question? Mostly, but it needs to stop guessing external limits and focus on your live notebook reuse behavior.
What should we do? Instrument the add path and correlate failures with notebook fullness.
Concrete action items:
Log notebook_id, source count before add, batch size, return code, added_count, and failure_reason on every add attempt.
Log source count after add when available.
Add a guard that rotates to a fresh notebook before the reusable notebook approaches your safe threshold.
Re-run the canary after logging is in place and check whether failures start at a consistent notebook count.
Use that observed threshold to set the production rollover point.
My read from the current evidence:
300 is the hard product cap.
150 and 300 are both too large for the current live reusable path.
The real question now is not “is 300 allowed?” but “what is the safe rollover threshold for this pipeline?”
If you want, I can turn this into a short engineering task list or a new ADR note that strips out the questionable external claims."

## Assistant

Your meta-critique of the previous answer is correct, and your instincts about “trust the canary over the lore” are exactly right. The external limits story is clearly tier-dependent and somewhat messy (50/100/300/600 across Standard/Plus/Pro/Ultra/Enterprise), but that’s *background*, not the thing you should optimize on.[1][2][3][4][5][6]

For *your* system, the only thing that really matters is:

> At what observed notebook fullness and batch size does `add_failed` start to show up, and how do we stay under that in production?

So: I’ll drop the guessing and do what you’re asking—turn your latest note into a tight engineering task list / ADR that is entirely anchored on your live behavior.

***

## Core position (aligned with your note)

- The failure is a **NotebookLM add boundary / reuse capacity** problem, not routing/scraping.  
- The previous **browser-automation ADR is stale for this issue** and should not be used as a decision driver.  
- The correct next step is **instrumentation + capacity guard + notebook rotation**, not increasing add window size.  

Those are fully consistent with both your canary description and with how NotebookLM enforces per-notebook source caps (e.g., Pro/Enterprise limits around 300 sources per notebook).[3][4][1]

***

## Short engineering task list (implementation-focused)

You basically outlined this already; I’ll structure it so you can drop it into a ticket / doc.

### 1. Instrument the add path

**Goal:** Correlate NotebookLM add failures with notebook fullness and batch behavior.

For every add attempt (including canary and production), log:

- `timestamp`
- `notebook_id` (the target NotebookLM notebook)
- `source_count_before_add` (your *estimate* of how many sources are already in this notebook)
- `batch_size` (number of new sources you’re trying to add this call)
- `return_code` (e.g., `0` for success, non-zero for failure)
- `added_count` (how many sources NotebookLM reports as successfully added, if you can infer it)
- `failure_reason` (raw string from your pipeline: e.g., `add_failed`, `timeout`, `http_429`, etc.)
- Optionally: estimated token/size metadata (if cheap to compute)
  - `batch_total_words` or `batch_total_tokens`

**Deliverable:**  
A structured log stream (or table) you can query by `notebook_id` and `source_count_before_add`.

### 2. Track notebook fullness in your system

**Goal:** Maintain a *local* view of “how full” each notebook is, instead of treating NotebookLM as stateless.

Minimal approach:

- Introduce a small store/table keyed by `notebook_id` with:
  - `notebook_id`
  - `source_count` (your running estimate)
  - `created_at`
  - `last_updated_at`

Update rules:

- On **notebook creation** via automation:
  - Insert row with `source_count = 0`.
- On **successful add**:
  - `source_count += added_count`  
  - `last_updated_at = now`
- On **failed add**:
  - Do **not** increment `source_count`, but log the failure as above.

This doesn’t have to be perfectly correct initially; the point is to correlate “capacity-ish” failures with “source_count_before_add”.

### 3. Add a capacity guard in front of each add

**Goal:** Prevent known-bad adds before they hit NotebookLM by obeying empirically discovered limits.

Guard semantics (pseudocode):

```text
Inputs:
  notebook_id
  planned_batch_size  # len(sources_to_add)
  source_count_before = store[notebook_id].source_count

Config (to be refined after canary runs):
  MAX_TOTAL_SOURCES_PER_NOTEBOOK = TBD (empirical)
  MAX_ADD_BATCH_SIZE             = TBD (empirical)
  SAFE_ROLLOVER_THRESHOLD        = TBD (empirical, ≤ MAX_TOTAL_SOURCES_PER_NOTEBOOK)

Logic:
  if source_count_before >= SAFE_ROLLOVER_THRESHOLD:
      # rotate instead of reusing
      notebook_id = create_new_notebook()
      source_count_before = 0

  if planned_batch_size > MAX_ADD_BATCH_SIZE:
      split into sub-batches ≤ MAX_ADD_BATCH_SIZE

  for each sub-batch:
      perform add
      log attempt as in §1
      on success: source_count += added_count
```

At first, set conservative constants (e.g., a small `MAX_ADD_BATCH_SIZE`) and refine them via canary.

### 4. Re-run the canary with full logging

**Goal:** Empirically identify the safe rollover threshold *for this pipeline*, not for NotebookLM in the abstract.

Once logging is in place:

1. Re-run your backlog canary with a **fixed, conservative batch size** (e.g., the current 150/300 windows *scaled down*).
2. Collect a slice of data:
   - For each `notebook_id`, look at `(source_count_before_add, batch_size, result, failure_reason)`.
3. Identify:
   - The smallest `source_count_before_add` at which `failure_reason = add_failed` occurs *for any* `batch_size`.
   - Whether failures cluster around a particular range (e.g., “we start to see add_failed at 230–250 sources for this notebook”).

Use that as:

- `OBSERVED_FAILURE_THRESHOLD ≈ min(source_count_before_add where add_failed)`  
- `SAFE_ROLLOVER_THRESHOLD = OBSERVED_FAILURE_THRESHOLD - margin`  
  (margin could be, say, 10–20% of the threshold or a fixed number of sources)

Repeat occasionally (or continuously via canary) to detect if NotebookLM changes behavior.

### 5. Use empirical thresholds for production rollover

**Goal:** Stop using documented caps (50/300/etc.) as operational thresholds.

Once you have `SAFE_ROLLOVER_THRESHOLD`:

- In the **reusable notebook path**:
  - Rotate to a fresh notebook when `source_count >= SAFE_ROLLOVER_THRESHOLD`.
- Do **not** increase the batch/add window simply because the backlog is high.  
  That’s the “do not treat backlog-derived scan rates as throughput” rule you wrote, and it’s exactly right.

If NotebookLM changes its plan caps (e.g., you move from Standard to Plus or Enterprise—300 sources per notebook is explicitly called out for some paid tiers and enterprise).[4][1][3]
You still *only* adjust in production after you see the canary’s empirical threshold move.

***

## ADR-style summary you can paste

> **Context**  
> The yt-is backlog canary is failing at the NotebookLM add boundary in the reusable industrial path. The failure pattern (`nlm_batch_subbatch_add_started` → ~123–124s → `nlm_batch_subbatch_add_completed` with `returncode: 1`, `failure_reason: add_failed`) is consistent across both 300-source and 150-source add windows. Routing, Selenium scraping, and transcript fallback are healthy. The bottleneck is NotebookLM notebook reuse / add capacity, not browser automation.
> 
> **Decision**  
> We will treat NotebookLM notebook reuse as a capacity-constrained resource and add explicit instrumentation and guards around every add operation:
> 
> 1. Log `notebook_id`, source count before add, batch size, return code, `added_count`, and `failure_reason` on every add attempt.  
> 2. Maintain a local `source_count` per `notebook_id` in our own store and update it on successful adds.  
> 3. Introduce a capacity guard that:
>    - Rotates to a fresh notebook before the reusable notebook reaches a safe rollover threshold.  
>    - Splits add batches that exceed a configured safe batch size.  
> 4. Re-run the canary with logging enabled and use the observed failure onset (first `add_failed` vs. `source_count_before_add`) to set the production rollover threshold.  
> 
> **Status of previous ADRs**  
> The earlier browser-automation ADR is **stale for this issue** and must not be used as the primary reference for the current canary failure. The live limit is NotebookLM notebook reuse / add capacity, not browser navigation.
> 
> **Non-goals / “What not to do”**  
> - Do not increase the NotebookLM add window again until we understand notebook-capacity behavior from logs.  
> - Do not treat backlog-derived scan rates as real throughput limits.  
> - Do not chase browser automation changes (routing/Selenium) as a fix for `add_failed` at high notebook fullness.

***

## Addressing the specific points you flagged

- You’re right to **distrust the previous “50 sources” claim** as a controlling parameter for your pipeline. External sources show:  
  - Free/Standard: 50 sources per notebook.[7][8][9][6]
  - Plus/Pro/Enterprise tiers: 100–300 sources per notebook.[2][5][1][3][4]
  - Ultra: up to 600 for some high-end tiers.[2][4]
  That explains the conflict with “300 documented cap” in your note but doesn’t change your conclusion: **your canary is the stronger signal** for this pipeline.
- Your “my read from the current evidence” bullets are logically coherent:
  - “300 is the hard product cap” — consistent with several paid/enterprise docs.[1][3][4]
  - “150 and 300 are both too large for the current live reusable path” — empirically true from your canary.  
  - “The real question is the safe rollover threshold” — exactly.

***

If you’d like, next step I can do is get much more concrete:

- Assume a specific language/runtime (Python/TS) and sketch the interfaces for:
  - `NotebookStateStore` (tracking source counts)
  - `NotebookAddGuard` (wraps the actual Selenium add operation)
  - `CanaryAnalyzer` (reads logs and computes `SAFE_ROLLOVER_THRESHOLD` from a CSV / DB table)

What language and storage layer are you using around this pipeline right now (Python vs TS, Postgres vs flat logs, etc.)?

## Human

How to work around NotebookLM source limits with browser automation
What causes add boundary errors in NotebookLM automation
Best practices for reusing notebooks without capacity issues

## Assistant

Below is a focused, system-designer answer that stays away from lore where it conflicts, and leans on (a) what’s publicly clear about limits and (b) patterns people use in practice.[1][2][3][4][5][6]

I’ll break it into your three questions:

1. How to work around NotebookLM source limits with browser automation  
2. What causes add-boundary errors in NotebookLM automation  
3. Best practices for reusing notebooks without capacity issues  

***

## 1. Working around source limits with browser automation

**Fact pattern from public sources**

- Free: typically ~50 sources per notebook.[3][4][5]
- Paid tiers: higher per-notebook caps (e.g., Plus ≈ 300; Ultra ≈ 600) but still *finite* per notebook.[7][8]
- Per-source size caps are large (≈500k words), so “few big sources” is often cheaper than “many tiny sources.”[4][5][3]

Given those guardrails, the main workarounds people actually use (which you can industrialize with automation) are:

### 1.1. “Master document” strategy

**Idea:** Merge many small logical sources into a single large file so each NotebookLM “source slot” carries more payload.[5][3][4]

Operationalized with automation:

- Upstream, instead of adding 200 transcripts as 200 sources:
  - Combine N transcripts into one “master” doc per chunk (e.g., `yt_2026_q1_transcripts_part_01`), making sure each stays < 500k words.[3][4][5]
  - Upload those handful of master docs as sources.
- Browser automation task:
  - Drive Google Docs / Drive to create, populate, and link those documents.
  - Then drive NotebookLM to add each master doc as a source.

Tradeoffs:

- **Pros:** Drastically fewer sources per notebook, so you hit the source *slot* limit much later.
- **Cons:** Intra-source navigation is in-document (headings, TOC, etc.), not per-transcript. You lose some granularity.

This combines nicely with your “reusable notebook” pattern: your capacity constraint becomes “# of master docs,” not “# of raw sources.”

### 1.2. Sharding across notebooks + external meta-index

Because notebooks are siloed—no cross-notebook querying is available natively—you have to handle “global” reasoning outside NotebookLM.[5][3]

Pattern:

- Use browser automation to maintain **multiple notebooks** for a given logical corpus:
  - `project_X_shard_01`, `project_X_shard_02`, etc.
- Maintain an external **meta-index** (DB or JSON) that records:
  - `notebook_id`
  - topic/theme
  - what logical sources live where
  - counts and capacity
- When a query comes in:
  - Use your own retrieval (e.g., embeddings, tags) to choose *which* notebook to query.
  - Then use browser automation to drive the conversation in that specific notebook.

This is the only scalable pattern if you need thousands of documents; NotebookLM only ever sees a focused subset per notebook.[3][5]

### 1.3. Rotate notebooks via automation before you hit capacity

Your own canary plan already points here; public guidance points the same way (create thematic notebooks, stay below caps).[5]

Automate:

- Keep a per-notebook `source_count` (your own log/state; NotebookLM doesn’t expose it cleanly).  
- Define a safe rollover threshold (empirically from your canary; not from docs).  
- Have the browser automation:
  - Detect “current notebook is near threshold.”
  - Create a new notebook (through UI).
  - Switch subsequent adds to that new notebook.
  - Update your routing/meta-index.

This is a **browser-automation responsibility**: creating notebooks, renaming, selecting, and verifying they’re the active target before adds.

### 1.4. Consolidate / compress sources before they reach NotebookLM

Public workarounds include generating summaries, then deleting heavy originals to free slots.[2][5]

Automated variant:

- Upstream agent (outside NotebookLM):
  - Condense multiple raw transcripts into summary docs or “distillation sources.”
- Automation workflow:
  - When a notebook gets “full enough,” trigger a consolidation run:
    - Summarize older sources into a single synthesized doc.
    - Add that doc as a new source.
    - Optionally remove several older, now-redundant sources to free slots.

This is more complex, but for long-running industrial notebooks it’s often necessary.

***

## 2. Causes of add-boundary errors in NotebookLM automation

From public usage plus your canary description, there are a handful of common causes:

### 2.1. Hitting the per-notebook source slot limit

When you try to add more sources than the notebook’s plan allows, NotebookLM will:

- Refuse to add new sources (sometimes with vague error UI).[8][3][5]
- In automation logs this becomes some flavor of “add failed” or a non-zero return with partial/zero `added_count`.

This is your main suspect given:

- Errors appear with large add windows (150/300).  
- Routing/scraping are healthy.  
- There’s a stable timing pattern (~2 minutes to failure) which suggests backend ingestion/limit checks rather than immediate browser issues.

### 2.2. Hitting per-source size/format constraints

Publicly observed issues include:[6][2]

- Very long PDFs or docs that exceed size constraints.  
- Certain websites / YouTube sources failing to import.  
- Large or complex HTML sometimes causing import errors.

Automation symptoms:

- Adds for some URLs consistently fail even when the notebook isn’t near capacity.
- Retrying the same URL gives the same failure; adding smaller/cleaned versions succeeds.

Mitigation:

- Pre-normalize sources (HTML→clean text; PDFs→OCR+split; long docs→chunk into sub-docs).[2][6]

### 2.3. Rate limits / transient backend errors

Some reports mention intermittent failures when adding many sources quickly.[1][6]

Automation signs:

- Adds fail sporadically rather than at a specific capacity threshold.  
- Retry after a delay succeeds.  
- Not strongly coupled to `source_count_before_add`.

Mitigation:

- Add exponential backoff + limited retries in your add pipeline.  
- Track whether failure reasons correlate with capacity or with rate (e.g. “too many requests”).

### 2.4. UI/automation desync

Automation-specific causes (even if NotebookLM is fine):

- Notebook not actually open/selected when you think you’re adding.  
- DOM changed; selectors no longer point to the “Add source” controls correctly.  
- Notebook context switched (e.g., multi-tab issues).

Mitigation:

- Verification steps:
  - Confirm the notebook title matches expected `notebook_id` before each add.
  - Confirm “source count” increment is visible in UI after add.
- Defensive automation: explicit waits for UI completion, error banner detection, etc.[6]

***

## 3. Best practices for reusing notebooks without capacity issues

Combining public guidance and your own canary direction:[1][3][5]

### 3.1. Treat each notebook as a finite-sized shard

Don’t try to make one “mega-notebook.” Instead:

- Design **topic-scoped notebooks** (“thematic, role-specific notebooks”).[5]
- Shard large corpora across notebooks:
  - Per domain/topic/time window (e.g., `yt_2025_q1`, `yt_2025_q2`).
- Use your own orchestration layer to decide *which* shard to query, rather than forcing NotebookLM to see everything.

This matches both best-practice advice and how people work around the source limits in the wild.[1][3][5]

### 3.2. Add capacity guards + rotation (your current direction)

The mature pattern:

1. **Track notebook fullness yourself**
   - Maintain a `source_count` per notebook.
   - Log every add attempt.

2. **Define a safe threshold**
   - Use canary data to find “first consistent failure count.”
   - Set a safety margin below that as the **rollover threshold**.

3. **Rotate before you hit the wall**
   - When `source_count >= threshold`, use automation to:
     - Create a new notebook.
     - Update routing so new sources go there.

This is exactly what your existing note converges on, and it aligns with how others handle the 50/300/600 caps.[7][8][5]

### 3.3. Keep notebooks focused to improve quality *and* capacity behavior

Public commentary repeatedly notes:[2][3][5]

- NotebookLM works best when notebooks are focused on a coherent project or topic.
- Mixing lots of unrelated sources in one notebook hurts answer quality.

So “capacity” is not just a hard-limit problem; it’s a quality problem:

- Prefer more, smaller, focused notebooks over a few everything-notebooks.
- Use automation to enforce that:
  - Naming scheme: `project:topic:shard`.
  - Only route relevant sources into each.

### 3.4. Use compression / archiving workflows as notebooks age

From public workarounds:[9][2][5]

- Create “summary sources” from older material and delete the originals to free slots.
- Export and archive completed notebooks (outside of NotebookLM) once a project is done, then delete them.

In automation terms:

- Periodic maintenance job:
  - For notebooks above some age + fullness:
    - Ask NotebookLM for a “distilled summary.”
    - Save the summary as a new source.
    - Remove a set of old sources.
- Alternatively, export notebook content via UI and recreate distilled versions in a new notebook if you prefer clean slates.

***

## How this ties directly to your three bullet questions

1. **How to work around source limits with browser automation**  
   - Implement **master-doc consolidation**, **sharding across multiple notebooks**, and **automatic rotation** via browser automation.[3][1][5]
   - Add optional **compression/archiving** flows once notebooks near capacity.[9][2][5]

2. **What causes add boundary errors in NotebookLM automation**  
   - Most commonly: **hitting per-notebook source caps**, **oversized/bad sources**, **rate limits**, or **UI desync**.[6][2][3][5]
   - Your canary suggests you’re primarily in the first category.

3. **Best practices for reusing notebooks without capacity issues**  
   - Treat notebooks as **finite shards**, keep them **topic-focused**, track **fullness in your system**, and **rotate safely below the empirically observed failure threshold**, not at the “marketing cap.”[1][3][5]

***

If you tell me which stack you want to anchor on (Python/Selenium vs TS/Playwright), I can sketch exact interfaces for:

- `NotebookShardAllocator` (decides which notebook to use)  
- `NotebookCapacityGuard` (enforces thresholds & rotation)  
- `SourceConsolidator` (builds master docs / summaries upstream)

## Human

"Yes. The high-level diagnosis is useful, but the external limit lore is not the thing to optimize on.
Answers
The pipeline is Python, not TypeScript. The NotebookLM worker code lives in csf/nlm_batch.py.
The persistent state is file-backed, not Postgres.
The main durable stores I see are:
batch_status.sqlite (line 97) for batch status
reusable_nlm_notebook.json for the reusable notebook id
.logs/*.jsonl for canary traces
transcripts.sqlite for transcript cache
The repo already has notebook-capacity plumbing in place:
source-count tracking in csf/nlm_batch.py (line 392)
source-count logging before and after add in csf/nlm_batch.py (line 540) and csf/nlm_batch.py (line 566)
a capacity guard and rotation path in csf/nlm_batch.py (line 723) and csf/nlm_batch.py (line 926)
What this means
We do not need more generic architecture guessing.
We do not need to chase browser-automation ADR ideas for this failure.
We already have the right instrumentation shape; the next step is to use it to decide whether the failure is:
notebook fullness near the cap, or
batch size still too large even before the cap.
What we should do next
Inspect the live canary traces and look at the failed subbatches’ source_count_before, current_source_count, added_count, and failure_reason.
If failures are happening near the notebook cap, keep the rotation guard and lower the safe rollover threshold.
If failures happen far below the cap, reduce the add window again and rerun the canary.
Do not change the browser automation path for this issue; it is not the bottleneck.
My recommendation, based on the traces we already saw:
Next action should be a trace-driven threshold decision, not another architecture refactor.
If you want me to act immediately, I would next analyze the current 150-window failure traces and tell you whether the safe move is:
earlier notebook rotation, or
a smaller add window."

## Assistant

Given that context, the right move is to stay entirely inside your existing plumbing and treat this as a **trace-reading / threshold-tuning** problem, not an architecture problem.

I’ll stick to what you actually have:

- Python pipeline  
- `csf/nlm_batch.py` already doing:
  - source-count tracking (≈ line 392)
  - pre/post-add logging (≈ 540, 566)
  - capacity guard + rotation (≈ 723, 926)
- Durable state in:
  - `batch_status.sqlite`
  - `reusable_nlm_notebook.json`
  - `.logs/*.jsonl` (canary traces)
  - `transcripts.sqlite`

That’s exactly the shape you need; the missing piece is **reading the traces and tightening the thresholds**.

Below is what I would concretely do next if I were editing this repo.

***

## 1. Immediate next step: trace-driven diagnosis

Goal: decide between:

- “Rotate earlier” vs  
- “Shrink add window again”

You already laid this out; let’s make it explicit as a checklist.

### 1.1. Extract failed subbatch records from canary logs

From `.logs/*.jsonl` for the current canary run, filter to the failed subbatches:

- `failure_reason == "add_failed"` (or whatever string your code logs)
- or `returncode != 0`

For each failure record, you want to capture at minimum:

- `notebook_id`
- `source_count_before` (from the pre-add log; the plumbing you mentioned)
- `current_source_count` (if you log both “before” and “after” under different keys)
- `added_count` (how many were intended vs actually added; if present)
- `batch_size` / `subbatch_size` (window size the code thought it was adding)
- `failure_reason`
- `timestamp`

Given the structure you described, this should be mostly present already in those JSONL lines.

### 1.2. Build a simple view: failures vs. notebook fullness

For each failed subbatch, compute:

- `effective_before = source_count_before` (what matters for capacity)
- `effective_after = source_count_before + added_count` (intended fullness)

Then examine:

- **Are the `effective_before` values clustered near the documented cap (~300)?**  
  If so, you’re seeing classic “full notebook” behavior.
- Or are there failures at much lower `effective_before` (e.g., 50–150) with large batch sizes?

You don’t need Postgres; a one-off Python script that walks `.logs/*.jsonl` and prints a small table or histogram is enough.

***

## 2. Decision rule (what to do based on what you see)

You already sketched this, I’ll sharpen it into two explicit branches.

### Branch A: Failures near the cap → rotate earlier

If your failed subbatches mostly look like:

- `source_count_before` ≈ 260–300 (or whatever “near cap” is on your plan)  
- `batch_size` is within your current 150-window  
- Repeated failures for the same `notebook_id` as it approaches that range

Then:

1. **Keep the rotation guard logic exactly as it is.**  
   You already have a capacity guard + rotation path in `csf/nlm_batch.py` (≈ 723, 926). Use it.

2. **Lower the safe rollover threshold constant.**  
   - Find the smallest `source_count_before` value among failures for a given plan; call it `FAIL_MIN`.  
   - Set your guard threshold to something like `FAIL_MIN - safety_margin`.  
   - Safety margin could be:
     - a fixed integer (e.g., 25 sources), or  
     - a % of `FAIL_MIN` (e.g., 10–20%).

3. **Re-run the canary with the existing 150-window.**  
   - If failures disappear and throughput remains acceptable, you’ve solved this issue without touching browser automation or window logic.

In other words: treat the failure as **“we rotated too late, not too wide”**.

### Branch B: Failures far below cap → shrink add window

If failures occur at:

- `source_count_before` clearly *well below* your notebook cap (e.g., 100–150 on a 300-cap account), and  
- failures correlate better with **batch size** than with fullness (e.g., any time you push a 150-subwindow you see issues), then:

1. **Leave the rotation threshold as-is (for this pass).**  
   It’s not what’s killing you.

2. **Reduce the add window size (subbatch size) one notch.**  
   - If you’re at 150-window:
     - Consider 100 first; if still flaky, try 75 or 50.

3. **Re-run the canary with the smaller window.**  
   - If failures vanish at the same fullness levels, you’ve identified the **per-operation add boundary** as the problem rather than overall capacity.

Interpretation: the bottleneck is “too many sources in one shot,” not “too many total sources in the notebook.”

***

## 3. How this uses your existing code (no architecture refactor)

You specifically said:

> The repo already has notebook-capacity plumbing in place:
> - source-count tracking in `csf/nlm_batch.py` (line 392)  
> - source-count logging before and after add (line 540, 566)  
> - capacity guard and rotation path (line 723, 926)

Given that:

- **No new data structures are needed.**  
  You already have:
  - `reusable_nlm_notebook.json` for the id  
  - logging of counts  
  - guard+rotation logic

- **No new browser-automation ADR is needed.**  
  You’re not changing how Selenium (or whatever) drives the UI.

The only changes that might touch code are:

1. **Minor log hygiene** (if needed):  
   - Ensure the fields you care about (`source_count_before`, `added_count`, `failure_reason`) are present in the JSONL lines for both success and failure.
2. **Tuning constants in the capacity guard**:  
   - Lower `SAFE_ROLLOVER_THRESHOLD` (or equivalent) if Branch A.  
   - Lower `MAX_ADDS_PER_SUBBATCH` / `ADD_WINDOW_SIZE` if Branch B.

Everything else is analysis: reading `.logs/*.jsonl` and deciding which side of that branch you’re on.

***

## 4. Answering your “what should we do next?” directly

> Next action should be a trace-driven threshold decision, not another architecture refactor.

I agree. That’s precisely the right level.

Your next concrete move:

1. **Run a short analysis pass over the current 150-window canary failure traces** and produce a tiny table like:

   - For each failed add:
     - `notebook_id`
     - `source_count_before`
     - `batch_size`
     - `failure_reason`

2. **Look for the pattern:**

   - If failures cluster near high `source_count_before`:  
     → lower rotation threshold, keep window.

   - If failures appear at low `source_count_before` but high `batch_size`:  
     → keep rotation, shrink window.

3. **Only after that** touch the constants.

No browser automation changes; no ADR rewriting until after you make this threshold choice.

***

If you want, I can propose the exact shape of a small Python “log slicer” script that:

- Reads `.logs/*.jsonl`
- Extracts the `add` events + failures
- Prints the relevant fields in a sortable CSV so you can eyeball the pattern quickly.
