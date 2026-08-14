---
title: "I had different LLMs look at code.   Please rank from best to work their responses:
Gemini CLI: '
✦ I've completed my r"
date: "2026-04-14"
mode: "COPILOT"
uuid: "20db3838-a945-491e-85a0-384a56d3c2fc"
entry_count: 19
---

## Human

I had different LLMs look at code.   Please rank from best to work their responses:
Gemini CLI: "
✦ I've completed my review of the yt-is pipeline and identified several key gaps and opportunities for improvement. These
  range from inefficiencies in NotebookLM batching to missing metadata population and the lack of automated retry logic for
  failed videos. I've also highlighted opportunities for SNR triage and better handling of private or member-only videos to
  reduce overhead and improve data quality.

  1. Inefficient "Industrial" Path (NotebookLM Batching)
   * Gap: The "Industrial Path" using NotebookLM batching (300 sources/notebook) is currently implemented to process videos
     one by one in the main fetch loop.
   * Impact: This negates the speed benefits of batching, likely operating at ~100-200 v/hr instead of the theoretical
     18,000 v/hr, while also wasting NotebookLM slots.
   * Opportunity: Implement batch-aware fetching in transcript.py and group pending videos by channel in csf-source fetch
     to leverage true parallel cloud ingestion.

  2. The "Retry Deadlock" in Batch Scheduling
   * Gap: The BatchScheduler excludes any video_id present in the download_archive table, which includes all failed
     attempts.
   * Impact: Transient failures (e.g., 429 rate limits or timeouts) permanently block a video from being retried by the
     scheduler.
   * Opportunity: Introduce a triage step to clear download_archive entries for retry-able failure reasons, allowing the
     system to recover from temporary issues.

  3. Metadata Population & Persistence Gap
   * Gap: Rich metadata (title, description, duration) fetched during enumeration or by yt-dlp is often lost because the
     fetch result only returns the transcript text.
   * Impact: The analysis_status table remains under-populated, requiring redundant API calls later if metadata is needed
     for analysis.
   * Opportunity: Capture the full metadata object during the fetch phase and persist it to analysis_status upon successful
     extraction.

  4. Signal-to-Noise Ratio (SNR) Triage & Validation
   * Gap: There's no automated validation of transcript "cleanliness," despite the system knowing that some methods (like
     Selenium) produce "Dirty Data" with 40% noise.
   * Impact: Higher downstream token costs and lower quality AI summaries when "Dirty" transcripts are used.
   * Opportunity: Add a validation step that compares transcript length to video duration, flagging "Dirty" transcripts for
     re-ingestion via the cleaner NotebookLM path.

  5. Provenance-Based Re-Fetching
   * Gap: Although source_stage versioning exists, it isn't used to trigger "upgrades" of low-quality data.
   * Opportunity: Implement an upgrade path that automatically re-fetches transcripts originally obtained via "Dirty"
     methods (Selenium) when "Clean" methods (NLM) become available.

  6. "Member-Only" and "Private" Video Triage
   * Gap: The escalation chain currently attempts to fetch transcripts for videos already flagged as member_only or
     private, which are guaranteed to fail.
   * Opportunity: Pre-filter the fetch queue using the unavailable_reason metadata to avoid unnecessary bot-detection risk
     and overhead."

"Gaps & Opportunities Identified
1. Missing Orchestrator Implementation
- The code references csf.orchestrator but this module is not present in the package
- This is a critical gap as the auto-mode analysis depends on it
- Opportunity: Implement the orchestrator module for tiered provider routing
2. Incomplete Provider System
- References to providers like TranscriptProvider, GeminiSDKProvider, OcrClipProvider
- These provider classes are not implemented in the visible codebase
- Opportunity: Create provider implementations for the analysis pipeline
3. Limited Error Handling in Batch Processing
- While there's retry logic, there's no circuit breaker pattern for consistently failing videos
- No dead letter queue for repeatedly failing items
- Opportunity: Add failure tracking and isolation mechanisms
4. Missing Metrics & Monitoring
- No built-in metrics collection for pipeline performance
- Limited visibility into processing rates, failure patterns
- Opportunity: Add Prometheus metrics or similar observability
5. Configuration Centralization
- Configuration scattered across environment variables, hardcoded values
- No unified configuration management
- Opportunity: Implement centralized configuration with validation
6. Testing Gaps
- Test files exist but no clear test strategy visible
- No integration tests for the full pipeline
- Opportunity: Add comprehensive test suite covering end-to-end flows
7. Documentation Inconsistencies
- README mentions features that may not be fully implemented
- Some ADR references in code not found in docs
- Opportunity: Synchronize documentation with actual implementation
Recommendations
1. Implement Missing Orchestrator: Create csf/orchestrator.py with tiered provider routing
2. Create Provider Implementations: Build the TranscriptProvider, GeminiSDKProvider, etc.
3. Add Circuit Breaker: Implement failure tracking to isolate problematic videos
4. Enhance Observability: Add metrics collection for pipeline monitoring
5. Centralize Configuration: Create unified config management system
6. Improve Testing: Add integration tests for critical paths
7. Synchronize Documentation: Ensure docs match implementation
The pipeline shows good architectural foundations with clear separation of concerns, but the missing orchestrator and provider implementations represent significant gaps that prevent the auto-mode analysis from functioning correctly. The round-robin batch processing and escalation chains for transcript fetching are well-designed and implemented.
Would you like me to elaborate on any specific area or help implement any of the missing components?
▣  Build · nemotron-3-super-free · 3m 0s"

"Critical Gaps Identified
1. No schema migration versioning - Adding columns via ALTER TABLE leaves existing rows with NULL values, breaking downstream logic
2. Race conditions in retry queue - Terminal-scoped retry storage causes synchronization issues in multi-terminal environments
3. Missing index on last_stage - No index for the triage filter on processing stage, causing full table scans
4. No cross-ingestion coordination - Videos can be processed simultaneously by both /yt-nlm and /yt-channel fetch paths
5. Triage logic scattered - Decision criteria split across detect_gap(), batch scheduler, and retry queue
6. Missing circuit breaker - No proper circuit breaker pattern for exhausted YouTube API keys
7. No staging area for partial processing - Cannot track intermediate states (e.g., during yt-dlp downloads)
8. Inconsistent error classification - Different subsystems use different error taxonomies
Priority Opportunities
Immediate: Add processing_stage column to track exact pipeline position, implement schema migration versioning, centralize triage logic
Short-term: Implement checkpoint/Restart for all processing stages, add cross-terminal retry synchronization, create health metrics dashboard
Long-term: Build pipeline coordinator service with advisory locks, unified error taxonomy with retry policies, and comprehensive health monitoring
The current architecture handles basic operation but lacks production-grade operational visibility and coordination needed for reliable multi-terminal processing.
▣  Build · openrouter/elephant-alpha · 1m 39s"

"The review of the yt-is pipeline up to the Triage step (the decision between Surgical/Targeted fetch and Industrial/Backlog fetch) reveals the following gaps and opportunities:
1. Discovery Pipeline Gaps
*   RSS-Dependent Gap Trigger: In csf/source_enumerator.py, gap detection (detect_gap) only triggers if the RSS feed returns results. If a channel's RSS is disabled or failing, the system skips gap resolution entirely, potentially missing new videos.
*   RSS Window Limitation: The 15-video RSS limit is a known bottleneck. While gap detection triggers if any of these 15 are missing, it doesn't protect against "deep gaps" where the most recent 15 are present but older videos (since the last check) are missing.
*   Sequential Polling: RSS polling in cmd_check_all (bin/csf-source) is sequential. As the number of tracked channels grows, the "Daily Check" will experience linear latency increase.
2. Data Flow & Triage Gaps
*   Implicit Triage: "Triage Mode" as depicted in the architecture diagram is currently implicit/manual. The user decides the triage path by choosing between /yt-channel fetch (Surgical) and /yt-nlm (Industrial). There is no automated orchestration layer that analyzes the pending backlog size to select the most efficient ingestion path.
*   Redundant Gap Resolution: The cmd_check and cmd_check_all logic performs API gap resolution immediately upon detection. If a user is about to run an Industrial batch anyway, these "surgical" API calls consume quota that could be avoided by letting the Industrial pipeline handle the discovery.
3. Opportunities for Improvement
*   Automated Triage Orchestrator: Implement a triage controller that evaluates pending_count.
    *   Low Volume (< 50 videos) $\\rightarrow$ Route to fetch_transcript_chain (Surgical) for immediate, high-SNR results.
    *   High Volume ($\\ge$ 50 videos) $\\rightarrow$ Route to _fetch_via_notebooklm_batch (Industrial) to maximize throughput (18K/hr).
*   Parallel Discovery: Move RSS polling and gap detection into a ThreadPoolExecutor to reduce the wall-clock time of check-all operations.
*   API-First Fallback: Modify the discovery logic to trigger a lightweight API playlistItems check if the RSS feed is empty or returns a 404/500, ensuring gaps are caught even when RSS fails.
*   Quota-Aware Triage: Integrate the quota_tracker into the triage decision. If API keys are nearing exhaustion, the system should proactively force the Industrial (NLM) path, which consumes fewer/no API units for content fetching.
▣  Build · gemma-4-31b-it · 9m 7s"

## Assistant

1. **Overall ranking (best → worst, for your use‑case)**

1. **Gemini CLI (first, long “✦ I’ve completed my review…” block)**  
2. **Gemma‑4‑31B‑IT (“The review of the yt-is pipeline up to the Triage step…”)**  
3. **Elephant Alpha (“Critical Gaps Identified…”)**  
4. **Nemotron‑3‑Super (“Gaps & Opportunities Identified… Missing Orchestrator…”)**

Below is the reasoning so you can sanity‑check:

***

2. **Gemini CLI (Industrial path, retry deadlock, SNR, member‑only triage) – Rank #1**

**Why it’s best for you:**

- **High code‑specific grounding:** It clearly knows about **NotebookLM batching**, **300 sources/notebook**, **transcript.py**, **csf-source fetch**, **download_archive table**, **analysis_status**, **source_stage versioning**, and **unavailable_reason** handling. That level of reference almost certainly came from actually reading your repo, not generic guessing.
- **Operationally material findings:**
  - The **“Industrial Path” implemented serially in the main loop** is a real design regression from the theoretical 18k v/hr throughput you were targeting.
  - The **retry deadlock via `download_archive`** is subtle but nasty in production; the fix (triage + selective clearing) is concrete and realistic.
  - **Metadata persistence gap** is directly tied to downstream token costs and feature completeness.
  - **SNR triage based on transcript length vs duration** is exactly the sort of cheap heuristic that will save you real money and improve downstream LLM quality.
  - **Provenance‑based re‑fetching** leverages your existing **source_stage** versioning instead of inventing new machinery.
  - **Member‑only/private short‑circuiting** is a very pragmatic security / bot‑detection risk reduction.
- **Actionability:** Each point comes with a very direct **“Gap → Impact → Opportunity”** mapping; you can turn each bullet into a ticket with almost no extra design work.

**Weaknesses:** It doesn’t say much about **cross‑terminal coordination**, **schema evolution**, or **observability**, so it’s more **local pipeline optimization** than **systems‑level** diagnosis.

***

3. **Gemma‑4‑31B‑IT (Discovery/Triage orchestration) – Rank #2**

**Strengths:**

- **Understands the architecture diagram and triage semantics:** It correctly reads **“Triage step (Surgical vs Industrial)”**, **/yt-channel**, **/yt-nlm**, **cmd_check / cmd_check_all**, and **detect_gap**.
- **Finds non‑obvious discovery issues:**
  - **RSS‑dependent gap trigger** and **RSS 15‑item window** are real blind spots for long‑tail backlog catch‑up.
  - **Sequential polling** in `cmd_check_all` becomes painful as you scale the channel set.
- **Proposes sensible orchestration improvements:**
  - **Automated triage orchestrator** that reacts to `pending_count` and **quota state** to route between **Surgical** and **Industrial** is structurally aligned with what you’re already inching toward.
  - **API‑first fallback when RSS fails** is exactly the kind of robustness upgrade you’d want in production.
  - **Quota‑aware routing** is especially relevant with your API key rotation/quotas.

**Why it’s second, not first:**

- It’s somewhat **narrowly scoped**: focused on **discovery + triage** slice, not the whole system.
- The suggestions are **architecturally correct but higher‑level**; you still need to do a non‑trivial design pass to turn them into concrete PRs.
- It doesn’t touch **retry semantics**, **dirty‑vs‑clean data**, or **member‑only safety** which are covered very well by Gemini CLI #1.

***

4. **Elephant Alpha (schema, race conditions, coordination) – Rank #3**

**Strengths:**

- **Good production‑grade instincts:**
  - Calls out **missing schema migration/versioning** and the risk of **NULLs after ALTER TABLE** impacting downstream logic.
  - Flags **race conditions in retry queues** in multi‑terminal environments — very relevant for your git‑worktree + many‑terminals style.
  - Notes missing **index on `last_stage`**, **no staging area for partial processing**, and **inconsistent error taxonomy**, all of which matter once you’re at scale.
- **Solid roadmap framing:** The **Immediate / Short‑term / Long‑term** breakdown is how you’d actually phase work in reality.

**Why it’s behind the first two:**

- It’s **less clearly grounded** in specific file names / functions; some items feel like **generic distributed pipeline advice** projected onto your system.
- Several suggestions (e.g., **“pipeline coordinator service with advisory locks”**, **comprehensive health dashboard**) are **broad “platform” asks** rather than precise, local changes the way Gemini CLI’s suggestions are.
- For your current stage, it’s useful but **a bit abstract** compared to the very code‑proximate findings of Gemini CLI #1.

***

5. **Nemotron‑3‑Super (missing orchestrator/providers, tests, docs) – Rank #4**

**Strengths:**

- It correctly spots **missing `csf.orchestrator` module**, and references to **provider classes** that are not yet implemented.
- It calls out **testing gaps**, **config scattering**, **lack of metrics/monitoring**, **doc drift** — all true of most evolving codebases.
- The closing assessment that **“round‑robin batch processing and escalation chains are well‑designed”** shows it at least parsed some of the structure.

**Why it’s last:**

- Most issues are **obvious from a quick grep**: “module referenced but not present”, “providers referenced but not implemented”.
- Recommendations like **“centralize configuration”**, **“add Prometheus metrics”**, **“synchronize docs with implementation”** are **generic platform suggestions** with little yt‑is‑specific nuance.
- Compared to the other three, there’s **less depth in operational behaviour** (retry, race conditions, triage behaviour, SNR, API quotas, etc.).

***
## Summary
- #1 Gemini CLI (Industrial path / SNR / member‑only triage) – deepest, most grounded, most actionable on actual yt‑is pipeline mechanics.  
- #2 Gemma‑4‑31B‑IT (discovery & triage) – strong architectural insight into RSS‑driven discovery and triage orchestration, but narrower in scope.  
- #3 Elephant Alpha (schema & coordination) – good production‑grade concerns (migrations, races, staging, error taxonomy) but less concretely tied to your current code.  
- #4 Nemotron‑3‑Super (orchestrator/providers/tests/docs) – mostly generic missing‑pieces and hygiene issues; useful but shallow vs the others.

If you want, next step I can: (a) turn the top 5–10 issues across these reviews into a prioritized ticket list, or (b) propose a minimal orchestrator + triage-controller design that reconciles the different suggestions.

What would be most useful as a follow‑up: a **prioritized implementation roadmap** based on these findings, or a **design sketch for the triage/orchestrator layer**?

## Human

What prompt do you think I should have used instead of "please review P:/packages/yt-is, for any gaps or opportunities in the pipeline or data flow, up to the triage step."

## Assistant

1. **Core issue with your original prompt**

Your original: **“please review P:/packages/yt-is, for any gaps or opportunities in the pipeline or data flow, up to the triage step.”**  

- It’s **too broad** (“any gaps or opportunities”) and **underspecified** about:
  - Which **dimensions** to prioritize (correctness, throughput, SNR/cost, ops reliability, failure modes).  
  - How deep to go (quick scan vs architecture‑level vs SQL schema vs retry logic).  
  - What **artifacts** the model can/should read (code only? ADRs? diagrams? README?).  
- As a result, each model **picked its own frame**: some did architecture, some ops, some generic hygiene, instead of giving you directly comparable reviews.

Below is a tighter prompt that would have pushed them into the kind of review Gemini CLI actually delivered.

***

2. **Suggested replacement prompt**

Use something like this (for CLI / code‑assistant context):

> **Task**  
> You are reviewing the **yt-is** codebase in `P:/packages/yt-is`.  
> Focus on the **end‑to‑end pipeline and data flow from discovery through transcript fetching up to, but not including, the triage step**.
>  
> **1. Scope & files**  
> - Prioritize code and configuration that directly affect:  
>   - **discovery / gap detection** (e.g., `csf/source_enumerator.py`, `cmd_check`, `cmd_check_all`)  
>   - **fetch / ingest / batching paths** (e.g., `/yt-channel`, `/yt-nlm`, NotebookLM batching, transcript fetchers)  
>   - **data persistence** (DB schemas, migrations, tables like `analysis_status`, `download_archive`, any `processing_stage` / `source_stage` fields).  
> - You may also use architecture notes / diagrams or README content **only to interpret the implementation**, not to hallucinate features that don’t exist.
>  
> **2. What to find**  
> Identify **concrete gaps and opportunities** specifically in:  
> 1. **Correctness & failure handling**  
>    - Retry logic, deadlocks, stuck items, race conditions across terminals, duplicate processing paths.  
> 2. **Throughput & efficiency**  
>    - Misused batching (especially NotebookLM), unnecessary sequential operations, wasteful API calls, or redundant discovery/fetch work.  
> 3. **Data quality & SNR**  
>    - Places where “dirty” vs “clean” transcripts, missing metadata, or provenance are not tracked or not used to upgrade/triage data.  
> 4. **Persistence & schema evolution**  
>    - Schema/versioning risks (NULLs after ALTER TABLE, missing indices on hot filters, missing processing‑stage tracking).  
>  
> **3. How to report**  
> For each issue, use this structure:  
> - **Component / file(s):** …  
> - **Gap:** Describe the specific behaviour or design flaw grounded in the actual code.  
> - **Impact:** Explain the practical consequence (e.g., stuck videos, wasted NotebookLM slots, expensive dirty transcripts, API quota burn, ops brittleness).  
> - **Evidence:** Point to specific functions / tables / fields / conditions you are basing this on.  
> - **Opportunity / fix:** Propose a concrete, minimal change or pattern (e.g., triaged retry queue, provenance‑aware re‑fetch, index on `last_stage`, centralized triage function).  
>  
> **4. Constraints**  
> - Stay within the **pre‑triage** portion of the pipeline. Do not propose features for parts you cannot see in the code.  
> - Prefer **fewer, high‑leverage findings** over long generic lists. Focus on the top **5–10 issues** that would most improve reliability, throughput, and data quality.

***

3. **Why this would work better for you**

- It **forces a shared frame** (pre‑triage pipeline & data flow, not generic repo review).  
- It fixes the “generic advice” problem by demanding **file‑ and table‑level evidence** and **impact**.  
- It aligns with what you clearly care about: **SNR, cost, retries, gaps, orchestration, and multi‑terminal ops**, as seen in the reviews you liked.

If you tell me which tool (Gemini CLI, Claude Code, etc.) you’re standardizing on for these reviews, I can compress this into a minimal template tuned exactly to that tool’s options and flags.

What environment do you mainly want to optimize this for first: **Gemini CLI**, **Claude Code**, or another tool?  

## Human

Can we make it more general to other sdlc projects?  We can say things like pipeline or functions, etc, but the next project almost certainly won't have the same names.

## Assistant

1. **Goal**

Yes. Below is a **project‑agnostic** version you can drop into any SDLC repo (backend service, data pipeline, CLI tool, etc.), while still steering the model toward the kind of analysis you liked.[1][2]

***

2. **General SDLC review prompt (pipeline / data‑flow focus)**

> **Task**  
> You are reviewing a **software project** in this repository.  
> Focus on the **end‑to‑end flow of work or data** from input/discovery through processing and persistence **up to the point where results are handed off to later stages** (e.g., triage, routing, or presentation layers).  
>  
> **1. Scope**  
> - Look at the components that implement the project’s **“pipeline” or main execution path**: functions, classes, jobs, handlers, background workers, or scripts that:  
>   - discover or receive inputs  
>   - fetch / transform / enrich data or requests  
>   - store or update state in databases, queues, or files  
> - Include configuration, schemas, and infrastructure code that materially affects those flows (e.g., migrations, queue/topic definitions, job schedulers, API clients).  
>  
> **2. What to identify**  
> Find **concrete gaps and opportunities** in these areas:  
> 1. **Correctness & failure handling**  
>    - Retry behaviour, items that can get stuck, race conditions, duplicate processing, inconsistent state transitions.  
> 2. **Throughput & efficiency**  
>    - Missing batching, unnecessary sequential work, redundant API calls or I/O, N+1 patterns, avoidable re‑computation.  
> 3. **Data quality & invariants**  
>    - Places where data can be partial, stale, or low‑quality without being detected; missing validation; lack of provenance/flags needed to triage or upgrade data later.  
> 4. **Persistence & schema evolution**  
>    - Risky schema changes (e.g., new nullable columns with non‑updated code), missing indices on hot filters, lack of clear “processing stage”/status fields, or unclear lifecycle of records.  
>  
> **3. Reporting format**  
> For each issue, use this structure:  
> - **Area / component:** (file(s), module(s), or subsystem)  
> - **Gap:** Specific behaviour or design flaw grounded in the actual code/config.  
> - **Impact:** Practical effect (e.g., stuck items, wasted compute or API calls, inconsistent data, hard‑to‑operate system).  
> - **Evidence:** Concrete references (function names, tables, fields, config keys, conditions).  
> - **Opportunity / change:** A **minimal**, realistic change or pattern that would meaningfully improve things.  
>  
> **4. Constraints**  
> - Stay within the **pre‑handoff** portion of the project’s flow (before downstream consumers / presentation).  
> - Prefer **fewer, high‑leverage findings** over long generic lists; focus on the **top 5–10** issues by impact.

***

3. **How to adapt per project quickly**

You only need to tweak **two phrases** per repo:

- **“end‑to‑end flow of work or data … up to the point where results are handed off”**  
  → swap “handed off” for “queued for downstream jobs”, “returned via API”, etc., if needed.
- Optionally add 1–2 lines under **Scope** like:  
  - “In this project, the main pipeline is the background job that ingests events and writes them to the data warehouse.”

Otherwise, the prompt should work for any **service, batch pipeline, ETL, or event‑driven system** without assuming specific names.[3][4]

***

## Summary

- Your original prompt was repo‑specific; this version is **name‑agnostic**, framed around **flows**, **stages**, and **impacts**, not file names.  
- It keeps the same **high‑signal axes** you care about: **correctness, throughput, data quality, persistence**, and forces **evidence‑backed findings** over generic advice.[2][1]

Do you want a **short “CLI‑friendly” version** of this that fits in ~5–7 lines for quick runs, or are you happy using the full template?

## Human

Show me the cli-friendly version (I'll still copy paste), and tell me what outcome difference in quality I should expect?

## Assistant

Yes — and you should expect a **better signal-to-noise ratio**, not just a shorter prompt. A concise prompt with explicit scope, evidence, and output format usually produces more grounded, less generic reviews than a sprawling one, especially for code-review tasks.[1][2]

## CLI-friendly version

> Review this repository’s main **pipeline / execution flow / processing path** from input discovery through transformation, persistence, and handoff to later stages.  
> Focus on **concrete gaps and opportunities** in: correctness/failure handling, throughput/efficiency, data quality/invariants, and persistence/schema evolution.  
> Look for issues like stuck items, retry deadlocks, race conditions, redundant work, missing batching, missing validation, missing provenance, risky schema changes, and missing indices.  
> Ground every finding in specific files, functions, tables, fields, or config, and explain the practical impact plus a minimal fix.  
> Prefer the top 5–10 highest-leverage findings over generic advice.  
> Do not assume project-specific names; infer the relevant components from the codebase.  

That version is short enough for CLI, but still gives the model the **four axes** you care about and tells it to stay evidence-driven.[3][4]

## Quality difference to expect

### What should improve
- **Less generic output.** The model is less likely to give you “add tests,” “improve docs,” or other boilerplate unless it can tie them to concrete code. Specificity and constraints generally improve precision in LLM outputs.[5][3]
- **More consistent focus.** Because the prompt names the review dimensions up front, different models are more likely to inspect the same classes of issues instead of drifting into their favorite topics.[2]
- **Better comparability across projects.** Since it avoids repo-specific names, the prompt transfers better to other SDLC systems without losing the pipeline/data-flow framing.

### What may get worse
- **Less exploratory breadth.** A shorter prompt can reduce the model’s willingness to roam and discover unexpected architecture issues. You may miss some “deep” findings that a more expansive prompt would surface.[1]
- **Less project tailoring.** If a repo has unusual terminology or architecture, the general prompt may not steer the model into the most relevant corners unless you add one or two project-specific nouns.
- **More dependence on repo quality.** If the codebase is poorly organized or under-documented, the model may need a second pass with a more specific prompt to fully map the flow.

## Practical expectation

For your use case, I’d expect the CLI version to produce:
- **Fewer but higher-confidence findings**.
- **More repeatable comparisons** across models.
- **Less “maybe” language** and more concrete file/function/table references.
- A small drop in novelty, but a net gain in **actionability**.

In practice, I’d use this pattern:
1. First pass: the short CLI prompt for broad triage.
2. Second pass: a targeted prompt on the most interesting subsystem the model found.

That two-pass approach usually beats trying to force one prompt to do everything.[6][1]

Would you like a version that is even shorter, like **3 lines for CLI**, or a version optimized for **maximum review depth**?

## Human

Show me max review depth.

The 2 pass approach made me consider open ended questions.  Like "What else do you think I should know?" or "Provide a prompt that focus on the areas that need more focus.".  Things like that.  Is that a useful idea that other people do?

## Assistant

1. **Max‑depth review prompt (single pass, very deep)**

Use this when you want the model to go as deep as possible on a codebase’s pipeline / data flow, not just surface issues:

> **Task**  
> You are reviewing this software project with a focus on the **end‑to‑end flow of work or data** (pipelines, main execution paths, background jobs, event handlers, key services).  
>  
> **1. Map the system**  
> - First, identify and briefly map the main flows: where inputs come from, how they are processed or transformed, and how/where results are stored or handed off to later stages.  
> - List the key components (files, modules, services, jobs, tables, queues) that participate in these flows.  
>  
> **2. Deep review of the flows (max depth)**  
> For the most important 1–3 flows you identified, perform a **deep, implementation‑level review** and find **specific gaps and opportunities** in:  
> 1) **Correctness & failure handling** (retries, stuck items, race conditions, idempotency, duplicate processing, bad state transitions)  
> 2) **Throughput & efficiency** (sequential bottlenecks, missing batching, redundant I/O or API calls, unnecessary recomputation)  
> 3) **Data quality & invariants** (missing validation, unclear or missing invariants, low‑quality/partial data not detected or flagged, missing provenance needed for triage/upgrades)  
> 4) **Persistence & schema evolution** (risky schema changes, missing indices on hot filters, missing or unclear processing‑stage / status tracking, migration/versioning risks)  
>  
> **3. Evidence‑backed findings**  
> For each issue, use this format (and be exhaustive where it matters):  
> - **Flow & component:** which flow and which specific file(s)/function(s)/table(s)/config.  
> - **Gap:** what is wrong or missing, described in concrete terms based on the code or schema.  
> - **Impact:** how this can fail or hurt performance, cost, operability, or data quality in real usage.  
> - **Evidence:** specific references (function names, code paths, conditions, schema fields, queries).  
> - **Opportunity / change:** the **smallest realistic change** or pattern that would substantially improve things.  
>  
> **4. Prioritization & meta‑review**  
> - Rank the issues by impact (high/medium/low) and briefly explain why.  
> - Then answer: **“If I were the tech lead, what 3–5 changes would I schedule first to materially improve this system?”**  
>  
> **5. Limits**  
> - Focus on the flows and components you can see; do not invent features that aren’t implemented.  
> - Prefer **depth over breadth**: it is better to go very deep on the most critical flows than to skim the entire repo.  

This gives you mapping → deep review → evidence → prioritization, which is exactly the multi‑stage structure found to increase quality in iterative prompting and self‑critique patterns.[1][2][3]

***

2. **Are open‑ended follow‑ups like “What else should I know?” useful?**

**Yes, they are useful, and other people do this – but with structure.**

What you’re describing matches several known patterns:

- **Iterative prompting / prompt refinement loops**: start with an initial answer, then ask targeted follow‑ups to deepen or correct it.[4][5][2]
- **Self‑criticism / Self‑Refine / Chain‑of‑Verification**: ask the model to critique its own output, generate verification questions, and refine its answer.[6][7][8][9]

People don’t just ask “Anything else?”; they often use **structured meta‑questions**, for example:

- “**Critique your own review**: where are your conclusions least certain or least supported by the code? What could be wrong or incomplete about your analysis?”[10][6]
- “**Generate 5 verification questions** that, if answered, would confirm or falsify your most important claims about this pipeline.”[7][8]
- “**Propose a follow‑up prompt** that would let a second pass focus on the riskiest or most uncertain parts of the system.”[11][2]

These patterns tend to **improve accuracy and depth** versus a single-shot answer, because they push the model to examine its own blind spots and then focus subsequent work there.[2][9][7]

***

3. **How I’d combine this with your two‑pass idea**

Pass 1 (broad or normal‑depth review)  
Pass 2 (deep dive driven by open‑ended meta‑questions), for example:

> Based on your review, answer these meta‑questions:  
> 1) Which parts of the pipeline or data flow are you **least confident** you understood correctly, and why?  
> 2) Which **3–5 components** represent the **highest operational or data‑quality risk** if left as‑is?  
> 3) Propose a **single follow‑up prompt** that would let you perform a **maximum‑depth review** of those risky/uncertain areas.  

Then you take the follow‑up prompt it generates, sanity‑check it, and run that as a second, deep‑dive call.

That gives you:
- A **general, repo‑agnostic deep‑review template** (the big prompt above), and  
- A **self‑steering loop** where the model helps choose what to zoom in on next, in a way that’s aligned with established self‑critique / iterative prompting techniques.[9][6][2]

***

## Key Takeaways

- The max‑depth prompt pushes the model to **map flows**, then do **evidence‑backed, prioritized deep review** on the most important ones.  
- Open‑ended meta‑questions like “What else should I know?” **are useful**, especially when turned into **structured self‑critique and follow‑up‑prompt requests**, which is a pattern already used in self‑refine and chain‑of‑verification methods.[6][7][9]
- For your workflow, combining a **normal‑depth first pass** with a **meta‑question‑driven second pass** is likely to give you the best depth/effort ratio.

Would you like me to draft a **small library of meta‑questions** (like 5–10 reusable “second‑pass” prompts) tuned specifically for **pipelines and data flows**?

## Human

Yes create a small library of second pass meta questions

## Assistant

Yes — this is a useful pattern, and it’s common in **iterative refinement / self-critique / chain-of-verification** workflows. The key is to ask **structured open-ended questions**, not vague ones, so the model turns “what else?” into a focused second pass.[1][2][3]

## Small second-pass library

Use these after an initial review.

### 1) Missing risk
> What important risks, failure modes, or edge cases did you not fully cover in the first pass?

### 2) Highest uncertainty
> Which parts of your analysis are least certain or least supported by the code, and what would you inspect next to verify them?

### 3) Bigger opportunities
> What higher-leverage improvement opportunities exist beyond the issues you already named?

### 4) Hidden coupling
> Where do you suspect hidden coupling, shared state, or implicit assumptions could cause future bugs or maintenance pain?

### 5) Flow gaps
> What gaps in the end-to-end flow, state transitions, or handoffs are still unaddressed?

### 6) Data quality
> Where could low-quality, partial, stale, or untrusted data pass through unnoticed, and how would you detect or tag it?

### 7) Failure recovery
> What recovery paths, retries, or fallback behaviors are missing or too weak for production use?

### 8) Performance traps
> What are the likely bottlenecks, redundant computations, or avoidable I/O/API calls you would investigate next?

### 9) Schema and lifecycle
> Which schema, status, or lifecycle assumptions look fragile if the system evolves or runs at scale?

### 10) Reviewer challenge
> If you had to challenge your own review, which conclusions would you question first and why?

## Best way to use them

The highest-value pattern is:

1. Run the first review.
2. Ask 2–4 of the questions above, not all 10.
3. Feed the answers into a second prompt like:
> Expand only on the new issues or uncertainties you identified. Keep the review evidence-based and avoid repeating prior points.

That matches how self-refine and verification loops work: generate an initial answer, generate targeted checks, then revise based on what those checks reveal.[4][3][1]

## Practical note

The most useful questions are usually the ones that force the model to expose **uncertainty**, **hidden coupling**, and **missing failure modes**. Those tend to produce the best second-pass value for software reviews.[2][5]

Would you like me to turn this into a **copy-paste 2-pass template** with placeholders for any repo?

## Human

Ok, please show me your optimized phase 1 cli friendly prompt, and the follow up phase 2 cli friendly prompt.

## Assistant

Here are two tight, CLI‑friendly prompts you can copy‑paste and reuse across projects.

***

### **Phase 1: CLI‑friendly first‑pass review**

> Review this repository’s main **pipeline / execution flows** (input discovery, processing, persistence, handoff to later stages).  
> Focus on **gaps and opportunities** in: correctness/failure handling, throughput/efficiency, data quality/invariants, and persistence/schema evolution.  
> Look for stuck items, retry issues, race conditions, duplicate work, missing batching, missing validation, missing provenance, risky schema changes, and missing indices.  
> Ground every finding in specific files, functions, tables, fields, or config, and explain the impact plus a minimal fix.  
> Prefer the top 5–10 highest‑leverage issues over generic advice.  

This is designed to be **short, scoped, and evidence‑driven**, giving you a solid first‑order review without over‑broad wandering.[1][2]

***

### **Phase 2: CLI‑friendly second‑pass “meta‑questions” prompt**

> Based on your previous review, answer these meta‑questions compactly:  
> 1) Which parts of the pipeline or data flow are you **least certain** about and why?  
> 2) Which 3–5 components pose the **highest operational or data‑quality risk** if left unchanged?  
> 3) What **new issues or gaps** did you realize you missed on the first pass (e.g., hidden coupling, state transitions, error handling, data‑flow assumptions)?  
> 4) Propose **1–2 concrete follow‑up investigations** (e.g., specific flows, functions, tables, or error‑handling paths) that a next pass should drill into with max depth.  
>  
> Present this as a short list under each numbered question; do not re‑state findings from the first review.  

This second‑pass prompt is optimized to **surface uncertainty, risk, and refinement directions** rather than redundancy, which aligns with established self‑critique / verification‑loop patterns while staying CLI‑friendly.[3][4][5]

***

### How to chain them in practice

1. Phase 1: run the first prompt on the repo.  
2. Phase 2: paste the Phase‑1 output into the second prompt and run it.  
3. Then, if you want, run a **third pass** focused on the “1–2 concrete follow‑up investigations” the model recommends, using the **max‑depth prompt** from earlier.

That gives you: **broad first cut → focused self‑critique → optional deep dive** in a very reusable pattern.

## Human

show me the phase 3 cli friendly prompt

## Assistant

1. **Phase 3 goal**

**Phase 1** = good first‑pass review.  
**Phase 2** = identify uncertainty + high‑risk areas.  
**Phase 3** = **max‑depth deep dive on one specific flow/component**, using everything learned so far, similar to self‑refine / prompt‑chaining patterns.[1][2]

***

2. **Phase 3: CLI‑friendly deep‑dive prompt**

Use this after Phase 2 has named 1–2 high‑risk/uncertain areas:

> Perform a **maximum‑depth review** of the **single highest‑risk or most uncertain flow/component** you identified earlier (pick one).  
>  
> 1) **Precisely define the target**: name the flow/component and list the key files, functions, tables, queues, or configs involved.  
> 2) **Trace the end‑to‑end path** through this area: inputs → transformations/decisions → persistence → handoff, calling out state transitions and branching conditions.  
> 3) For this one area, exhaustively identify issues in:  
>    - correctness/failure handling (retries, idempotency, races, stuck items, bad states)  
>    - throughput/efficiency (bottlenecks, missing batching, redundant I/O/API calls)  
>    - data quality/invariants (validation, invariants, low‑quality or partial data, provenance)  
>    - persistence/schema (field semantics, indices, lifecycle/status fields, migration/versioning risks).  
> 4) For each issue, provide: **(a)** exact code/schema locations, **(b)** concrete gap, **(c)** real-world impact, **(d)** the smallest realistic change that would materially improve it.  
> 5) Conclude with a **ranked list of 3–5 specific changes** for this flow/component that you would implement first, and why.  
>  
> Focus only on this chosen area; go for **depth over breadth** and avoid repeating earlier high-level points.  

This matches best practices for **deep chained prompts**: narrow scope, explicit reasoning steps, and structured refinement on a prior answer.[3][2][4]

***

## Summary

- **Phase 1:** broad, evidence‑backed repo review.  
- **Phase 2:** surface uncertainty and risk; decide where to zoom in.  
- **Phase 3 (above):** single‑target, maximum‑depth drill‑down with explicit path tracing and concrete changes.  

You can drop these three prompts into any SDLC project and get a reasonably consistent review pipeline with minimal editing. Hope this helps! Let me know if you want a **security‑focused variant** of Phase 3 next.

## Human

Create phase 4 for testing and deployment

## Assistant

Yes — **Phase 4** should shift from “what might be wrong?” to “what evidence would prove this is safe to ship and operate?” That means test coverage, edge cases, deployment risk, rollback, observability, and rollout gating.[1][2][3]

## Phase 4 prompt

> Review the **testing and deployment readiness** of this project for the flow/component you previously analyzed.  
> Focus on whether the code is safe to **test, deploy, roll back, and operate** in production.  
>  
> 1) Identify the **existing test coverage** and the most important missing tests: unit, integration, regression, contract, and failure-path tests.  
> 2) Find deployment risks: config drift, environment differences, migration risk, feature-flag gaps, unsafe defaults, rollback difficulty, and observability gaps.  
> 3) For the highest-risk areas, propose **specific test cases** and **deployment safeguards** that would catch failures before production.  
> 4) Call out anything that should be added to CI/CD: automated evals, canary checks, shadow tests, smoke tests, or release gates.  
> 5) Rank the top 3–5 actions needed to make this flow safe to ship, and explain why they matter.  
>  
> Be concrete and evidence-based. Ground every claim in files, tests, configs, CI/CD definitions, or deployment artifacts. Do not repeat earlier design issues unless they directly affect testability or release safety.

## How Phase 4 differs

- **Phase 1:** broad review of pipeline gaps.  
- **Phase 2:** self-critique and missing issues.  
- **Phase 3:** deep dive on the riskiest flow.  
- **Phase 4:** determine whether the flow is **actually shippable** and **operable**.

## What this usually catches

- Missing tests for **failure paths** and **retries**.  
- Migrations that work locally but fail on real data.  
- Configuration differences between dev/staging/prod.  
- Lack of smoke tests, canaries, or rollback hooks.  
- No monitoring for the thing most likely to break after release.[4][5][6]

If you want, I can also turn this into a **very short CLI version** that matches the style of the earlier phases.

## Human

Show me the CLI-friendly version of phase 4, then Adapt phase 4 for shadow testing setup

Create phase 5 for monitoring production prompts

## Assistant

1. **Phase 4 – CLI‑friendly (testing & deployment readiness)**

> Review the **testing and deployment readiness** of the flow/component previously analyzed.  
> Identify what tests exist and the most important **missing tests** (unit, integration, regression, failure‑path, contract).  
> Find **deployment risks**: config drift, env differences, dangerous migrations, missing feature flags, unsafe defaults, weak rollback, poor observability.  
> Propose **specific test cases** and **deployment safeguards** (checks in CI, pre‑deploy smoke tests, canaries, rollbacks) that would catch failures early.  
> Recommend **3–5 concrete actions** to make this flow safe to ship, and ground each in actual tests, configs, CI/CD definitions, or scripts.  

This aligns with common guidance on treating tests + CI/CD as primary gates for safe deployment.[1][2][3]

***

2. **Phase 4 (shadow‑testing‑focused variant)**

Use this when you’re setting up **shadow mode** / traffic mirroring for a new version (model, pipeline, or service).[4][5][6][7]

> Design a **shadow testing setup** for the flow/component previously analyzed.  
> Specify: baseline vs candidate versions, and exactly **which traffic** should be mirrored (APIs, jobs, event types).  
> Describe how to **route and isolate** shadow traffic so it never affects users, and what to log from baseline vs candidate for offline comparison.  
> Define **comparison metrics and thresholds** (correctness, quality, latency, cost, error rates) that must pass before any canary or full rollout.  
> Recommend 3–5 concrete implementation steps (routing changes, log schemas, dashboards, eval scripts) needed to safely run and evaluate shadow tests.  

This matches best practices for using shadow mode before canary/A/B releases.[5][6][8][4]

***

3. **Phase 5 – Monitoring & production observability**

Phase 5 assumes the thing is live (after or beyond shadow/canary) and focuses on **what to watch and how to react**, following LLM/agent observability practices.[9][10][11][12]

**CLI‑friendly Phase 5 prompt:**

> Review how this flow/component should be **monitored in production** to detect issues early and guide future improvements.  
> Define the key **metrics and signals** to track: correctness/quality, error rates, latency, throughput, cost, and any domain‑specific KPIs.  
> Describe what needs to be **logged and correlated** (inputs, outputs, prompt/model versions, feature flags, user IDs, request IDs) to debug problems and run evals.  
> Propose **alerts and dashboards**: which conditions should page or warn (and at what thresholds), and what views operators need for fast diagnosis.  
> Suggest how to turn new failures into **regression tests/evals** and how to use production data for continuous prompt/model/pipeline refinement.  

This reflects current guidance on treating prompts and LLM flows as first‑class, observable production components with versioning, metrics, and feedback loops.[10][11][13][12][9]

***

## Summary

- **Phase 4 (CLI):** focuses on **tests + deployment risks**.  
- **Phase 4 (shadow variant):** designs **shadow traffic** and comparison criteria before rollout.  
- **Phase 5 (CLI):** defines **metrics, logging, alerts, and feedback loops** to run the system safely in production.

Hope this helps! Let me know if you want a **single consolidated “Phase 1–5” doc** you can drop into your repos.

## Human

what's a shadow testing?

Adapt phases 1 to 5 specifically for LLM pipelines

## Assistant

1. **What is shadow testing (for LLMs / services)?**

**Shadow testing** (aka **shadow mode** or **shadow deployment**) means:  
- You keep your **current production system** (baseline) serving all real users as normal.  
- You **duplicate the same real requests** to a **candidate** system (new model, new prompt, new pipeline version) **in parallel**.  
- Only the **baseline’s response** goes back to users; the candidate’s response is **logged for comparison** and analysis offline.[1][2][3][4]

In other words, it’s a **dress rehearsal with real traffic**: you see how the new LLM / pipeline behaves under real-world inputs, but there is **zero user impact** because they never see its outputs.[2][3][5][6]

For **LLM pipelines**, shadow testing is especially useful when:
- Switching **models** (e.g., GPT → Gemma) or **providers**.  
- Making big **prompt changes**, new **tooling** (agents, retrieval), or new **safety filters**.  
- You need to validate behavior on **messy, real user inputs** before any exposure.[4][5][7]

***

2. **Adapted Phases 1–5 for LLM pipelines**

Below are CLI‑friendly prompts tailored specifically to **LLM pipelines** (RAG, agents, tools, etc.). You can drop “LLM” if you reuse them for non‑LLM services.

***

### **Phase 1 – LLM pipeline first‑pass review**

> Review this repository’s main **LLM pipeline(s)**: request handling, retrieval/context building, prompt construction, model calls, tool/agent logic, and response post‑processing.  
> Focus on **gaps and opportunities** in:  
> - correctness/failure handling (timeouts, retries, tool/DB errors, partial results)  
> - throughput/efficiency (redundant calls, missing batching, unnecessary retrieval, wasted tokens)  
> - output quality & data invariants (hallucination risk, missing validation, unsafe or low‑quality outputs)  
> - persistence/schema (logging of prompts/outputs, eval data, feature flags, versioning).  
> Ground every finding in specific files/functions/configs and explain impact plus a minimal fix.  
> Prefer the top 5–10 highest‑leverage issues over generic advice.  

***

### **Phase 2 – LLM pipeline meta‑questions (self‑critique)**

> Based on your previous LLM pipeline review, answer these meta‑questions:  
> 1) Which parts of the **LLM flow** (retrieval, prompt building, model/tool calls, post‑processing) are you **least certain** about, and why?  
> 2) Which 3–5 components pose the **highest risk** for hallucinations, bad outputs, cost explosions, or outages if left unchanged?  
> 3) What important **gaps** did you miss in the first pass (e.g., prompt injection, safety filters, logging, eval hooks)?  
> 4) Propose 1–2 **concrete follow‑up investigations** (specific flows, prompts, tools, or storage paths) that a next pass should explore in depth.  
> Answer concisely; do not restate the full first‑pass review.  

This aligns with self‑refine / chain‑of‑verification style meta‑prompting for LLM systems.[8][9][10]

***

### **Phase 3 – Deep‑dive on a critical LLM flow**

> Perform a **maximum‑depth review** of the **single highest‑risk or most uncertain LLM flow** you identified (e.g., retrieval+prompting path for a key feature).  
> 1) Precisely define the target: name the flow and list key handlers, prompt builders, retrievers, tools, and model calls involved.  
> 2) Trace the **end‑to‑end path**: user input → retrieval/context → prompt(s) → model/tool calls → post‑processing → output, including state and branching.  
> 3) For this flow, exhaustively identify issues in:  
>    - correctness/failure handling (errors, retries, idempotency, partial results, bad tool outputs)  
>    - throughput/efficiency (duplicate retrieval, unnecessary model calls, token waste, latency bottlenecks)  
>    - quality/safety (hallucination risks, missing validations or policies, prompt‑injection vulnerabilities, unsafe content)  
>    - logging/evals (missing traces, lack of prompt/model versioning, no eval hooks or labels).  
> 4) For each issue: give locations, gap, real‑world impact, and the smallest realistic change that materially improves it.  
> 5) Conclude with a ranked list of **3–5 concrete changes** for this flow and why they matter.  

***

### **Phase 4 – Testing & deployment for LLM pipelines**

**4A. Normal testing + deployment readiness**

> Review the **testing and deployment readiness** of the LLM pipeline/flow analyzed above.  
> Identify existing and missing tests: unit tests for prompt builders/tools, integration tests for the full LLM pipeline, regression tests with fixed inputs/expected outputs or eval scores, and failure‑path tests.  
> Find deployment risks: model/prompt/version drift between envs, unsafe config defaults, risky migrations, missing feature flags or kill‑switches, fragile eval datasets.  
> Propose **specific tests and CI/CD checks** (golden prompts, regression evals, smoke tests) and **deployment safeguards** (feature flags, config validation, rollback plans).  
> Recommend 3–5 concrete actions to make this LLM flow safe to ship, grounded in actual tests, configs, CI, or deployment scripts.  

**4B. Shadow‑testing setup for LLM changes**

> Design a **shadow testing setup** for this LLM pipeline when introducing a new model/prompt/tooling version.  
> Specify: baseline vs candidate configuration (models, prompts, tools), and which **production requests** should be mirrored.  
> Describe how to route and isolate **shadow traffic** so users only see baseline outputs, while candidate outputs are logged for offline comparison.  
> Define comparison metrics and thresholds: quality/eval scores, latency, cost, safety violations, hallucination rates.  
> Recommend concrete implementation steps (traffic mirroring, logging schema including input/prompt/model version, comparison jobs, dashboards) to run and evaluate shadow tests safely.  

This matches current guidance for LLM shadow mode + gradual rollout.[3][5][2][4]

***

### **Phase 5 – Monitoring & observability for LLM pipelines**

> Review how this LLM pipeline should be **observed in production**.  
> Define key **metrics**: request volume, latency, token usage and cost, error rates, tool failure rates, retrieval hit quality, and downstream business KPIs.  
> Specify what to **log and trace** for each request: user input (with privacy), retrieved context, prompts, model/tool versions, outputs, eval scores/feedback, and correlation IDs.  
> Propose **dashboards and alerts**: which conditions should page or warn (e.g., spike in failures, latency, hallucination reports, eval degradation, cost anomalies), and what views operators need for fast debugging.  
> Suggest how to convert production incidents and bad outputs into **regression evals/tests**, and how to use production data to iteratively improve prompts, retrieval, and model choices.  

This aligns with LLM observability patterns: tracing, prompt analytics, evals, and feedback loops.[11][12][13][14]

***

## Summary

- **Shadow testing:** duplicate real production requests to a **candidate LLM pipeline** while users still see the **baseline**, letting you compare outputs, quality, latency, and cost with **no user risk**.[1][2][3][4]
- **Phases 1–5 (LLM‑adapted):**  
  - **1:** First‑pass LLM pipeline review.  
  - **2:** Self‑critique/meta questions to find blind spots.  
  - **3:** Deep dive on a critical LLM flow.  
  - **4:** Testing + deployment + shadow mode for LLM changes.  
  - **5:** Production monitoring, observability, and feedback loops.

Would you like a **single markdown doc** with these LLM‑specific phases formatted as a reusable “LLM Pipeline Review Playbook”?

## Human

Yes generate a single LLM pipeline review playbook doc

## Assistant

# LLM Pipeline Review Playbook

**Purpose:** A 5‑phase, CLI‑friendly prompt sequence to systematically review **LLM pipelines** (RAG, agents, tools, etc.) from code gaps → deep analysis → testing → deployment → observability.

**Usage:**  
- Copy‑paste each phase into Gemini CLI, Claude Code, or any LLM interface.  
- Feed outputs from Phase N into Phase N+1 for context.  
- Works for any repo; no project‑specific names needed.

***

## Phase 1: First‑pass pipeline review

```
Review this repository's main **LLM pipeline(s)**: request handling, retrieval/context building, prompt construction, model calls, tool/agent logic, and response post-processing.  

Focus on **gaps and opportunities** in:  
- correctness/failure handling (timeouts, retries, tool/DB errors, partial results)  
- throughput/efficiency (redundant calls, missing batching, unnecessary retrieval, wasted tokens)  
- output quality & data invariants (hallucination risk, missing validation, unsafe or low-quality outputs)  
- persistence/schema (logging of prompts/outputs, eval data, feature flags, versioning).  

Ground every finding in specific files/functions/configs and explain impact plus a minimal fix.  
Prefer the top 5–10 highest-leverage issues over generic advice.
```

**Expected output:** 5–10 concrete issues with evidence and fixes.

***

## Phase 2: Self‑critique & meta‑questions

```
Based on your previous LLM pipeline review, answer these meta-questions:  
1) Which parts of the **LLM flow** (retrieval, prompt building, model/tool calls, post-processing) are you **least certain** about, and why?  
2) Which 3–5 components pose the **highest risk** for hallucinations, bad outputs, cost explosions, or outages if left unchanged?  
3) What important **gaps** did you miss in the first pass (e.g., prompt injection, safety filters, logging, eval hooks)?  
4) Propose 1–2 **concrete follow-up investigations** (specific flows, prompts, tools, or storage paths) that a next pass should explore in depth.  

Answer concisely; do not restate the full first-pass review.
```

**Expected output:** Blind spots, top risks, and Phase 3 targets.

***

## Phase 3: Deep dive on critical flow

```
Perform a **maximum-depth review** of the **single highest-risk or most uncertain LLM flow** you identified (e.g., retrieval+prompting path for a key feature).  

1) Precisely define the target: name the flow and list key handlers, prompt builders, retrievers, tools, and model calls involved.  
2) Trace the **end-to-end path**: user input → retrieval/context → prompt(s) → model/tool calls → post-processing → output, including state and branching.  
3) For this flow, exhaustively identify issues in:  
   - correctness/failure handling (errors, retries, idempotency, partial results, bad tool outputs)  
   - throughput/efficiency (duplicate retrieval, unnecessary model calls, token waste, latency bottlenecks)  
   - quality/safety (hallucination risks, missing validations or policies, prompt-injection vulnerabilities, unsafe content)  
   - logging/evals (missing traces, lack of prompt/model versioning, no eval hooks or labels).  
4) For each issue: give locations, gap, real-world impact, and the smallest realistic change that materially improves it.  
5) Conclude with a ranked list of **3–5 concrete changes** for this flow and why they matter.  
```

**Expected output:** Detailed trace + prioritized fixes for one flow.

***

## Phase 4: Testing & deployment readiness

**4A. Normal testing + deployment**

```
Review the **testing and deployment readiness** of the LLM pipeline/flow analyzed above.  

Identify existing and missing tests: unit tests for prompt builders/tools, integration tests for the full LLM pipeline, regression tests with fixed inputs/expected outputs or eval scores, and failure-path tests.  
Find deployment risks: model/prompt/version drift between envs, unsafe config defaults, risky migrations, missing feature flags or kill-switches, fragile eval datasets.  
Propose **specific tests and CI/CD checks** (golden prompts, regression evals, smoke tests) and **deployment safeguards** (feature flags, config validation, rollback plans).  
Recommend 3–5 concrete actions to make this LLM flow safe to ship, grounded in actual tests, configs, CI, or deployment scripts.
```

**4B. Shadow‑testing setup (for new model/prompt/tooling)**

```
Design a **shadow testing setup** for this LLM pipeline when introducing a new model/prompt/tooling version.  

Specify: baseline vs candidate configuration (models, prompts, tools), and which **production requests** should be mirrored.  
Describe how to route and isolate **shadow traffic** so users only see baseline outputs, while candidate outputs are logged for offline comparison.  
Define comparison metrics and thresholds: quality/eval scores, latency, cost, safety violations, hallucination rates.  
Recommend concrete implementation steps (traffic mirroring, logging schema including input/prompt/model version, comparison jobs, dashboards) to run and evaluate shadow tests safely.
```

**Expected output:** Test plan + deployment gates, or shadow setup.

***

## Phase 5: Production monitoring & observability

```
Review how this LLM pipeline should be **observed in production**.  

Define key **metrics**: request volume, latency, token usage and cost, error rates, tool failure rates, retrieval hit quality, and downstream business KPIs.  
Specify what to **log and trace** for each request: user input (with privacy), retrieved context, prompts, model/tool versions, outputs, eval scores/feedback, and correlation IDs.  
Propose **dashboards and alerts**: which conditions should page or warn (e.g., spike in failures, latency, hallucination reports, eval degradation, cost anomalies), and what views operators need for fast debugging.  
Suggest how to convert production incidents and bad outputs into **regression evals/tests**, and how to use production data to iteratively improve prompts, retrieval, and model choices.  
```

**Expected output:** Metrics, logging, alerts, and feedback loops.

***

## Quick‑start guide

1. **Phase 1** → Get first‑pass issues.  
2. **Phase 2** → Pick a high‑risk flow.  
3. **Phase 3** → Deep‑dive that flow.  
4. **Phase 4** → Make it testable/deployable (use 4B for model changes).  
5. **Phase 5** → Plan production observability.  

**Pro tips:**  
- Always paste prior phases' outputs for context.  
- Run on **Gemini CLI** or **Claude Code** for best results.  
- Takes ~5–10 min per phase, saves hours of manual review.

***

**Sources:** Adapted from LLM evals playbooks, shadow testing guides, and production observability best practices.[1][2][3][4][5][6][7]

## Human

This is awkward phrasing.   How can this be rewritten?
"/ai-gemini please review the plan file: Review the indicated target for: request handling, retrieval/context building, prompt construction,
  model calls, tool/agent logic, and response post-processing.

  Focus on **gaps and opportunities** in:
  - correctness/failure handling (timeouts, retries, tool/DB errors, partial results)
  - throughput/efficiency (redundant calls, missing batching, unnecessary retrieval, wasted tokens)
  - output quality & data invariants (hallucination risk, missing validation, unsafe or low-quality outputs)
  - persistence/schema (logging of prompts/outputs, eval data, feature flags, versioning).

  Ground every finding in specific files/functions/configs and explain impact plus a minimal fix.
  Prefer the top 5–10 highest-leverage issues over generic advice."

## Assistant

1. **Problem with the current phrasing**

The awkwardness comes from the **nested "Review the indicated target for: ..."** structure. It feels like you're telling the LLM to review something *and* describing what to review, creating confusion in the command flow.

***

2. **Rewritten CLI‑friendly version**

```
/ai-gemini Review [plan file path] for the following LLM pipeline components:  
request handling, retrieval/context building, prompt construction, model calls, tool/agent logic, response post-processing.  

Focus on **gaps and opportunities** in:  
- correctness/failure handling (timeouts, retries, tool/DB errors, partial results)  
- throughput/efficiency (redundant calls, missing batching, unnecessary retrieval, wasted tokens)  
- output quality & data invariants (hallucination risk, missing validation, unsafe outputs)  
- persistence/schema (logging prompts/outputs, eval data, feature flags, versioning)  

Ground findings in specific files/functions/configs. Explain impact + minimal fix.  
Top 5–10 highest-leverage issues only.
```

**Key improvements:**
- **Clear command structure**: `/ai-gemini Review [file] for [components]`  
- **No nested review instruction**  
- **Direct, imperative tone**  
- **Same focus areas** from our playbook, but file‑targeted  
- **Concise CLI format** (fits in terminal without scrolling)

***

3. **Even shorter variant (if space is tight)**

```
/ai-gemini Review [plan file] LLM pipeline gaps: request→retrieval→prompt→model→tools→post-process.  
Correctness/retries, efficiency/tokens, quality/safety, logging/evals.  
Evidence + impact + fix. Top 5–10 issues.
```

**Tradeoff:** Less explicit but ~50% shorter for quick reviews.

***

## Why this works better

- Matches your **`/ai-gemini`** syntax pattern from prior workflows (reviewing plan files iteratively).[1][2]
- **Imperative + concrete**: tells the LLM exactly what to analyze, not to analyze something else.  
- **Playbook‑aligned**: uses the same focus areas as Phase 1 but scoped to your plan file.  

Use the first rewrite for maximum clarity, the second for speed.

## Human

how about if we have a skill (/ai-gemini), then a target, then the prompt?

## Assistant

```
/ai-gemini [plan file path] Review LLM pipeline gaps: request→retrieval→prompt→model→tools→post-process.  
Correctness/retries, efficiency/tokens, quality/safety, logging/evals.  
Evidence + impact + fix. Top 5–10 issues.
```

**Why this structure works:**

**1. Clean 3‑part flow:**  
- **`/ai-gemini`** → skill invocation  
- **`[plan file path]`** → target (e.g., `P:/packages/yt-is/plan.md`)  
- **Prompt** → analysis instruction  

**2. Fixes the awkwardness:**  
- No nested "review the target for..."  
- Direct: "Review LLM pipeline gaps"  
- Abbreviated but precise component chain  

**3. Matches your pattern:**  
```
/ai-gemini P:/path/to/plan.md Review [components]. [focus areas]. [output format].
```

**4. Still playbook‑complete:**  
- Covers all Phase 1 axes  
- Evidence + impact + fix  
- Prioritization constraint  

**Example usage:**
```
/ai-gemini P:/packages/yt-is/plan.md Review LLM pipeline gaps: request→retrieval→prompt→model→tools→post-process. Correctness/retries, efficiency/tokens, quality/safety, logging/evals. Evidence + impact + fix. Top 5–10 issues.
```

This is **terminal‑friendly** (one line) and **unambiguous** for your `/ai-gemini` skill.

## Human

I don't need it hyper compressed.  Just rewrite the prompt to supprot that format.

## Assistant

```
/ai-gemini [plan file path] Review the LLM pipeline components in this plan file:  
request handling, retrieval/context building, prompt construction,  
model calls, tool/agent logic, and response post‑processing.  

Focus on **gaps and opportunities** in:  
- correctness/failure handling (timeouts, retries, tool/DB errors, partial results)  
- throughput/efficiency (redundant calls, missing batching, unnecessary retrieval, wasted tokens)  
- output quality & data invariants (hallucination risk, missing validation, unsafe or low‑quality outputs)  
- persistence/schema (logging of prompts/outputs, eval data, feature flags, versioning)  

Ground every finding in specific files/functions/configs and explain impact plus a minimal fix.  
Prefer the top 5–10 highest‑leverage issues over generic advice.
```

**Format:** `/ai-gemini [target] [clear instruction]`

**What changed:**
- **Removed the nested "Review the indicated target for"** → now directly "Review the LLM pipeline components **in this plan file**"
- **Explicit target reference** early in prompt  
- **Same focus areas and structure** you wanted  
- **Clean separation** between skill → target → prompt  

**Usage:**  
```
/ai-gemini P:/packages/yt-is/plan.md [paste prompt above]
```

## Human

Your prompt doesn't make sense.  I told you I want it generalized to different sdlc type projects.  Here's an example.

## Assistant

```
/ai-gemini [plan file path] Review the indicated target for gaps and opportunities across **any SDLC project** components:  

Focus on:  
- **correctness/failure handling** (timeouts, retries, errors, partial results)  
- **throughput/efficiency** (redundant work, missing batching, unnecessary calls, resource waste)  
- **output quality & invariants** (validation gaps, unsafe outputs, data quality risks)  
- **persistence/schema** (logging, state tracking, config/versioning, storage evolution)  

Ground findings in specific files/functions/configs. Explain impact + minimal fix.  
Top 5–10 highest-leverage issues only.
```

**Why this works for the generalized format:**

1. **`/ai-gemini [target]`** → skill + file path  
2. **"Review the indicated target for gaps..."** → uses your exact phrasing but generalized  
3. **"across **any SDLC project** components"** → project‑agnostic (no LLM/RAG specifics)  
4. **Generic axes** → works for web services, pipelines, CLI tools, etc.  
5. **Same structure** as your example but universal  

**Example usage:**
```
/ai-gemini plan-update-prompt.md Review the indicated target for gaps and opportunities across **any SDLC project** components: [paste rest]
```

This stays true to your `/ai-gemini [target] [prompt]` pattern while being **fully generalized** for any SDLC project.[1]

## Human

""across any SDLC project** components"**", is that really optimal?

## Assistant

No — you're right, it's clunky.  

**Better:** `"in this project's main flows and components"`

**Full rewrite:**

```
/ai-gemini [plan file path] Review the indicated target for gaps and opportunities **in this project's main flows and components**:  

Focus on:  
- **correctness/failure handling** (timeouts, retries, errors, partial results)  
- **throughput/efficiency** (redundant work, missing batching, unnecessary calls, resource waste)  
- **output quality & invariants** (validation gaps, unsafe outputs, data quality risks)  
- **persistence/schema** (logging, state tracking, config/versioning, storage evolution)  

Ground findings in specific files/functions/configs. Explain impact + minimal fix.  
Top 5–10 highest-leverage issues only.
```

**Why "main flows and components" is optimal:**
- **Project‑agnostic** (no "LLM" or "pipeline" assumptions)  
- **Clear scope** (model reads the plan file to infer what the flows/components are)  
- **Natural phrasing** (reads smoothly)  
- **Matches your intent** (generalized SDLC review)[1]

## Human

"**in this project's main flows and components**", this doesn't sound right.  we want an expert review.  we don't know what expert we need.  can't the prompt adapt to not knowing?

## Assistant

```
/ai-gemini [plan file path] Review the indicated target for gaps and opportunities **across its core technical systems**.  

Focus on:  
- **correctness/failure handling** (timeouts, retries, errors, partial results)  
- **throughput/efficiency** (redundant work, missing batching, unnecessary calls, resource waste)  
- **output quality & invariants** (validation gaps, unsafe outputs, data quality risks)  
- **persistence/schema** (logging, state tracking, config/versioning, storage evolution)  

Ground findings in specific files/functions/configs. Explain impact + minimal fix.  
Top 5–10 highest-leverage issues only.
```

**Why "core technical systems" works:**

1. **Expert‑adaptive**: Model infers the right expertise from the plan file itself (LLM pipeline? → prompt/retrieval expert. Web service? → API/scaling expert.)  
2. **Broad but precise**: Covers pipelines, services, CLI tools, agents — any SDLC project  
3. **Authoritative tone**: Sounds like what an expert would say  
4. **No assumptions**: Lets the model discover the domain from the target file  

The model will **self‑adapt** to the right expertise because the plan file contains the context (like your `plan_update_prompt.md` with its TASK structure).[1]

## Human

please update the 5 step prompts to use the enhanced ideas.

## Assistant

# Updated LLM Pipeline Review Playbook (Enhanced)

**Key enhancements incorporated:**
- **`/ai-gemini [target]` format** for CLI execution  
- **"Review the indicated target for gaps..."** phrasing  
- **"core technical systems"** for adaptive expert inference  
- **Generalized axes** that work across SDLC types  
- **Self‑adapting expertise** (model infers domain from target file)

***

## Phase 1: First‑pass review

```
/ai-gemini [repo/plan file path] Review the indicated target for gaps and opportunities **across its core technical systems**.  

Focus on:  
- **correctness/failure handling** (timeouts, retries, errors, partial results)  
- **throughput/efficiency** (redundant work, missing batching, unnecessary calls, resource waste)  
- **output quality & invariants** (validation gaps, unsafe outputs, data quality risks)  
- **persistence/schema** (logging, state tracking, config/versioning, storage evolution)  

Ground findings in specific files/functions/configs. Explain impact + minimal fix.  
Top 5–10 highest-leverage issues only.
```

***

## Phase 2: Self‑critique & meta‑questions

```
/ai-gemini [prior output] Review the indicated target for self‑critique and meta‑analysis **across its core technical systems**.  

Answer these questions:  
1) Which parts are you **least certain** about, and why?  
2) Which 3–5 components pose the **highest risk** if unchanged?  
3) What important **gaps** did you miss in the first pass?  
4) Propose 1–2 **follow‑up investigations** for the next pass.  

Answer concisely; do not repeat prior review.
```

***

## Phase 3: Deep dive on critical area

```
/ai-gemini [prior output] Review the indicated target for **maximum‑depth analysis** of the **single highest‑risk/uncertain area** you identified **across its core technical systems**.  

1) Define the target area precisely (files/functions involved).  
2) Trace the **end‑to‑end path** through this area (inputs → processing → outputs).  
3) Exhaustively identify issues in all 4 focus areas above.  
4) For each: locations, gap, impact, smallest realistic fix.  
5) Rank **3–5 concrete changes** and explain priority.  

Focus only on this area; go deep, don't repeat earlier points.
```

***

## Phase 4: Testing & deployment readiness

```
/ai-gemini [prior output] Review the indicated target for **testing and deployment readiness** **across its core technical systems**.  

1) Identify existing/missing tests (unit, integration, regression, failure‑path).  
2) Find deployment risks (config drift, env differences, migrations, unsafe defaults, rollback gaps).  
3) Propose **specific test cases** and **deployment safeguards** (CI checks, smoke tests, canaries).  
4) Recommend **3–5 concrete actions** to make it safe to ship.  

Ground in actual tests/configs/CI/deployment artifacts.
```

**Phase 4B (Shadow testing variant):**
```
/ai-gemini [prior output] Review the indicated target for **shadow testing setup** **across its core technical systems**.  

Specify: baseline vs candidate versions, mirrored traffic, isolation strategy.  
Define comparison metrics/thresholds and implementation steps (routing, logging, comparison jobs).
```

***

## Phase 5: Production monitoring & observability

```
/ai-gemini [prior output] Review the indicated target for **production monitoring** **across its core technical systems**.  

1) Define key **metrics** (volume, latency, errors, cost, quality KPIs).  
2) Specify **logging/tracing** needed (inputs, outputs, versions, correlation IDs).  
3) Propose **dashboards/alerts** (paging thresholds, operator views).  
4) Suggest how to turn incidents into **regression tests** and use data for refinement.  

Ground in realistic observability needs for this system.
```

***

## Usage pattern

```
# Phase 1
/ai-gemini ./my-project/plan.md [Phase 1 prompt]

# Phase 2  
/ai-gemini phase1-output.md [Phase 2 prompt]  

# And so on...
```

**Key benefits of updates:**
- **Uniform structure**: Every phase starts with `/ai-gemini [target] Review... **across its core technical systems**`
- **Adaptive expertise**: Model infers the right domain from the target file  
- **SDLC‑general**: Works for LLM pipelines, web services, CLI tools, etc.  
- **CLI‑optimized**: Short, scannable, copy‑paste ready  

This gives you a **production‑ready, generalized 5‑phase review system**.
