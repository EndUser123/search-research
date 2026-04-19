<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Do repos exist for the "intelligence stream" described below?

"You said
What video YouTube sources did we talk about and what method would we use to get them? I know it's all prompting, with some coding. We have public channels (we won't be concerned about member-only at this time, etc), and then authenticated user watch later, history, and non-public playlists.
Gemini said
To keep your Cognitive Steering Framework (CSF) fueled with high-quality data, we’ve mapped out a strategy that treats YouTube not as a video site, but as a structured "Intelligence Stream."
TL;DR
Public Sources: Use gemini-cli + yt-fts for direct research and transcript indexing.
Authenticated History: Use Google Takeout (watch-history.json) for deep batch audits of your cognitive drift.
Private Playlists/Watch Later: Use yt-dlp --cookies-from-browser to "bridge" your login to the CLI for extraction.
Orchestration: Python 3.14 background watchers automate the ingestion of these sources into your CKS.

1. Source \& Method Matrix
This table summarizes the "how" and "where" for every source we've discussed.
Source Type
Access Method
Primary Tool(s)
CSF ROI Goal
Public Channels
URL / Search
gemini-cli, yt-fts
Cat 4/11: Visual TDD \& TUI Audits.
Watch Later
Browser Cookies
yt-dlp + gemini
Cat 2: Pre-screening for sycophancy.
Watch History
JSON Export
Google Takeout + Python
Cat 8: Detecting "Cognitive Drift."
Private Playlists
ID + Cookies
yt-dlp
Cat 12: Curating personal "Agentic Laws."
2. Technical Methods Deep Dive
A. The "Authenticated Bridge" (Private Playlists \& Watch Later)
Because the gemini-cli can't log in to your Google account directly, you use yt-dlp to act as a scout. It uses your existing browser session (cookies) to grab the private URLs, which are then passed to Gemini for analysis.
Prompting: You tell Claude to "Fetch my Watch Later list and analyze the first 5 videos for Category 3 patterns."
Coding: A Python 3.14 script runs yt-dlp --cookies-from-browser brave --get-id :ytwatchlater and pipes those IDs into a gemini research loop.
B. The "Retrospective Audit" (History)
For history, the most reliable method for "Massive ROI" is the Google Takeout approach.
The Method: You download your watch-history.json.
The Logic: A Python script filters this for "long-form" or "technical" titles and creates a manifest.
The Result: Gemini audits this manifest to see if you are actually following your Category 5 (Investigation) and Category 8 (Cognitive Frameworks) goals.
C. The "Local Knowledge Base" (yt-fts)
This is your "First Responder" source.
The Method: You use yt-fts to download transcripts of public channels you trust.
The Logic: Before doing an expensive web search, you run a local Semantic Search (via your ytr alias).
The Integration: If a match is found, the Python 3.14 Watcher triggers a gemini research task to "watch" that specific timestamp and extract artifacts.
3. The Python 3.14 Orchestration Layer
To make this work without "brittle" manual steps, we move the logic into a background loop:
Ingestor: A script that periodically checks your watch-history.json or watch-later list.
Dispatcher: It sends high-value URLs to the gemini-cli.
Watcher (csf_watcher.py): Monitors the output folder.
CKS Linker (cks.py): Performs the Category 3 Conflict Check and updates your agent's constitution.
4. Why this matters for the CSF
By automating the "Watching" and "Audit" phases, you ensure that your agent's CKS (Domain 12) is always evolving. You aren't just giving the agent rules; you are giving it a Self-Improving Memory based on your own curated information diet.
Would you like me to...
...draft a "Source Prioritizer" script? It could look at your Watch Later list and use the gemini-cli to assign a "CSF Priority Score" (1-10) to each video, so you know exactly which one will give you the highest steering ROI for your current project.
You said
Yes, please think about what the optimal solution for the intelligence stream would look like, and then create all the files and artifacts I would need for it.
Gemini said

"

No, there is **no canonical, public monorepo** yet that exactly bundles the “Intelligence Stream” pipeline you described (YouTube history/watch‑later + `yt-fts` + `yt-dlp` + `gemini-cli` + Python 3.14 watchers + CKS‑style constitution updating).[^1_1][^1_2][^1_3][^1_4]

However, **all the core components *do* have open‑source repos** that you can glue together to build this exact pattern:

***

### 1. Existing repos you can reuse

- **`yt-fts` (YouTube Full‑Text Search)**
    - GitHub: `NotJoeMartinez/yt-fts`
    - Purpose: Downloads channel subtitles via `yt-dlp`, stores them in SQLite, and provides a CLI for local semantic‑ish search.[^1_4][^1_1]
    - You can treat this as your “Local Knowledge Base” / “First Responder” layer.
- **`yt-dlp` (Authenticated YouTube access)**
    - GitHub: `yt‑dlp/yt‑dlp`
    - Purpose: Pulls `Watch Later`, private playlists, and non‑public content via `--cookies-from-browser` and `--cookies`.[^1_5][^1_6]
    - Ideal for your “Authenticated Bridge” (Watch Later, private playlists).
- **`gemini-cli`**
    - Open‑source Google‑hosted repository (Apache‑2) for their CLI tool.
    - Purpose: Run local Gemini models with large context, web search, and automation hooks.[^1_2][^1_3]
    - You’d wire this as your “analysis” layer over URLs or transcripts.

None of these repos implement the **full CSF‑style orchestration** (periodic watchers, CSF‑category scoring, constitution updating), but they give you the instrumentation.

***

### 2. What’s missing (and where to put it)

Your “Intelligence Stream” is really a **custom orchestration layer** on top of the above:

- **Python 3.14 watchers**
    - `csf_watcher.py`, `cks.py`, and a `SourcePrioritizer` script.
    - These do not correspond to any known public repo; they’re workflow‑specific to your Cognitive Steering Framework.
- **CKS‑style “constitution” updater**
    - No public repo implements “Category‑aware conflict checks” over YouTube‑based cognitive‑drift data; that’s a domain‑specific pattern.

In other words, the **infrastructure** (`yt-dlp`, `yt-fts`, `gemini-cli`) is commoditized and exists; the **CSF‑specific intelligence stream** is not yet packaged as a ready‑to‑clone monorepo.

***

### 3. How to turn this into a repo

If you want a first‑class repo, you can scaffold it as:

```text
intelligencestream/
├── yt-dlp-wrapper/          # WatchLater & private playlists extraction
├── local_kb/                # yt-fts channels + embeddings
├── csf_watcher.py           # Ingestor, Dispatcher, Watcher
├── cks.py                   # CSF category mapping + conflict checks
├── source_prioritizer.py    # "CSF Priority Score" script
├── config/
│   ├── csf_categories.yaml  # Category → ROI mapping
│   └── takeout_sources.yaml # History / Watch Later IDs
└── README.md                # Your “Intelligence Stream” spec
```

Given your current setup, the **most realistic path** is to:

1. **Install and integrate the existing repos**:
    - `pip install yt-fts yt-dlp`
    - Clone `gemini-cli` (or install via Google’s instructions).[^1_3][^1_1]
2. **Lay down your own repo skeleton** and commit the Python 3.14 files the Gemini‑CSF conversation was about:
    - `csf_watcher.py`
    - `cks.py`
    - `source_prioritizer.py`
    - Config / schema files for CSF categories.

If you want, the next step can be concrete: I can generate the **complete file‑tree listing plus implementations** (e.g., `google_takeout_audit.py`, `yt_watchlater_ingestor.py`, and `source_prioritizer.py`) so you can `git init` and `git add` everything in one go.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://pypi.org/project/yt-fts/0.1.33/

[^1_2]: https://github.com/google-gemini/gemini-cli/issues/1691

[^1_3]: https://www.youtube.com/watch?v=T76NbeTdDFA

[^1_4]: https://github.com/NotJoeMartinez/yt-fts

[^1_5]: https://github.com/yt-dlp/yt-dlp/wiki/FAQ

[^1_6]: https://github.com/yt-dlp/yt-dlp/issues/13445

[^1_7]: https://www.cryptika.com/google-says-gemini-ai-agents-are-crawling-the-dark-web-posts-to-detect-threats/

[^1_8]: https://www.youtube.com/watch?v=ptgoqTTud3o

[^1_9]: https://www.youtube.com/watch?v=4NRNzyCFsMI

[^1_10]: https://www.youtube.com/watch?v=W4cnVUzHTsQ

[^1_11]: https://www.youtube.com/watch?v=98DcoXwGX6I

[^1_12]: https://www.linkedin.com/posts/thorwebdev_have-you-tried-geminis-video-understanding-activity-7436956521051271168-uKIB

[^1_13]: https://sourceforge.net/projects/yt-fts.mirror/

[^1_14]: https://www.cryptika.com/chrome-gemini-vulnerability-lets-attackers-access-victims-camera-and-microphone-remotely/

[^1_15]: https://www.linkedin.com/posts/smithakolan_i-just-used-the-new-gemini-cli-to-set-up-activity-7343679677594484736-LbJb


---

# Please turn your previous high‑level reasoning about this problem into a concrete, architecture‑aware solution that I can implement and live with long‑term.

Assume ALL of the following constraints are hard requirements:

I routinely run 5+ terminals / processes that share the same filesystem or project root.

The solution MUST be multi‑terminal isolated: any runtime or enforcement state must never leak between terminals or get corrupted by concurrency. Treat each terminal/session as a separate “tenant” over the same repo.
​

The system MUST be immune to stale data: no reliance on long‑lived in‑memory flags or outdated context; every important decision should be based only on current, authoritative sources (e.g., current config files, current tool/action sequence, per‑terminal logs or state files).

I do not care about transition effort; significant refactors, partial rewrites, or side‑by‑side greenfield work are acceptable if they yield a cleaner, more reliable design.

Using those constraints plus everything you have already inferred from our chat, promote your ideas into a full architecture proposal using this exact structure. If any subsection cannot be completed due to missing information, mark it NEEDS CLARIFICATION and list the precise questions you need answered; do NOT fall back to generic, non‑actionable tips.

1. Context Understanding
Clarify whether this work is primarily improving an existing system, designing something mostly new, or a hybrid. Then identify which parts of the system are involved (configs, commands/APIs, hooks/events, agents/skills if any, logs, per‑terminal/session state).

Explain how multi‑terminal concurrency and the shared filesystem (or other shared resources) currently produce failures or would likely do so: cross‑terminal state bleed, race conditions, stale assumptions about config, logs, or model state, etc.

State the change scope as Tiny / Small / Medium / Large and justify it in terms of refactors to components, configurations, and data flow.

Define the core problem as a gap and a goal: what’s broken or risky in the current or planned design, and what target behavior we want in a multi‑terminal, stale‑state‑resistant setup.

2. Proposed Architecture
Design the architecture in clear layers and explain how each layer behaves and coordinates:

Layer definitions and responsibilities

Per‑terminal/session state model: how each terminal or session is identified, where its logs and settings live, and how code reads that terminal‑local data without sharing it across sessions.
​

Execution / hook / event layer: how lifecycle events (e.g., “before action”, “after action”, “on stop”, “on error”) are wired to enforce policies, perform checks, or trigger automation deterministically.

Policy/config layer: how configuration (files, environment, CLI flags, project docs, feature flags) is structured and loaded so that decisions always come from current, authoritative data.

Domain layer: how domain concepts (e.g., skills, tools, workflows, agents, pipelines) are represented and used by the above layers.

Correctness guarantees
For each layer, explain how it guarantees correct behavior even with multiple terminals and no long‑lived shared state, including:

How it prevents cross‑terminal leakage and ensures each terminal’s decisions depend only on its own context plus shared, read‑only sources (like current repo files).
​

How it ensures that updates to config or code (for example, changing a rule or policy file) take effect promptly without needing to restart terminals.

How deterministic mechanisms (hooks, scripts, validations) are used instead of purely conversational or probabilistic mechanisms whenever behavior must occur.

Interaction with existing mechanisms

Specify which current mechanisms are reused as‑is, which are consolidated, and which are deprecated or turned into no‑ops by the new design.

Note any conventions the architecture requires (file locations, naming, metadata/frontmatter, per‑terminal folders under a .config‑like directory, etc.).

3. Implementation Plan
Describe concrete implementation steps at a “sit down and edit files” level:

Exact places to change

List which hooks, event handlers, commands, or integration points need to change and how (e.g., which lifecycle events are intercepted, which tools/actions they apply to).

List which config or metadata fields must be added or standardized (e.g., fields defining allowed actions, models, tenants, roles, or policies).

Identify which log files or per‑terminal state files should be created or repurposed (e.g., per‑terminal audit logs, decision logs, session summaries).

New modules and refactors

Describe any new modules, services, or helper utilities you recommend, especially for:

Parsing current config/metadata on each relevant event.

Inspecting the current action/tool sequence and building a decision from that plus per‑terminal logs.

Ensuring each terminal writes to and reads from its own log/state so decisions are isolated.

When proposing changes, be explicit about which parts are refactors of existing code, which are greenfield modules running alongside the old system, and any planned decommissioning or migration steps.

Stale‑data immunity

Explain how every important decision is computed from current config, code, and per‑terminal state, with no reliance on in‑memory flags, long‑lived objects, or cached context. If any caching is needed, specify its invalidation strategy explicitly.

4. Testing Strategy
Provide a concrete, automation‑friendly test plan (pytest or equivalent) to validate the design:

Test scenarios

Multi‑terminal isolation: scenarios where two terminals/processes perform conflicting actions on the same repo/state and we verify that their behavior and logs remain isolated and correct.
​

Correct handling when prescribed procedures are ignored (e.g., required commands, workflows, or “playbooks” are skipped): how the architecture detects that and what it does.

No false negatives for critical guarantees (e.g., safety/security checks always run when required).

No false positives where benign operations are blocked or over‑constrained without justification.

No stale enforcement after changes: config or metadata changes mid‑session and enforcement immediately reflects the new configuration.

Stale‑state simulation

Describe how to simulate stale‑state conditions (e.g., long‑running sessions while configs change, concurrent writes, partial log failures) and verify that decisions remain correct because they re‑read authoritative sources.

Acceptance and rollback

Define acceptance criteria for rollout (e.g., error rates, false‑positive/negative thresholds, latency ceilings, cross‑terminal leak checks over N days).
​

Include a simple rollback plan: what to revert (configs, hooks, modules) and how to fall back to a known‑good, less opinionated baseline if issues appear.

5. Observability \& Metrics
Explain how to observe behavior and detect regressions:

Per‑terminal logging

What to log per terminal/session and where (file paths or log sinks), including timestamp, terminal/session id, action/tool, decision, reason, and any relevant context keys.

Metrics

Metrics to track, such as:

False positives and false negatives for key guarantees.

Per‑terminal error and block rates.

Time‑to‑action (e.g., time from command or trigger to first relevant tool/action).

Throughput and latency per terminal.

Detecting regressions

How to detect when upstream behavior changes (e.g., different tool‑calling patterns from an LLM, new events, or different latency distributions) and how to use logs/metrics to localize and adapt to those changes.

6. Risks \& Tradeoffs
Provide an explicit risk assessment:

Failure modes

Enumerate likely failure modes (e.g., misconfigured metadata, mis‑tagged actions, hooks failing open vs closed, log corruption) and their impact.

Discuss false‑positive and false‑negative risks, how they would show up, and how the architecture mitigates or at least surfaces them.

Performance and complexity

Analyze performance overhead (filesystem reads, log writes, extra validations) and complexity (extra modules, conventions) versus the guarantees achieved.

Explain how the design scales as I add more workflows/skills/agents or more terminals, and whether any parts will need sharding, indexing, or restructuring as the system grows.

Soft‑enforcement areas

Call out any remaining behaviors that cannot be made strictly deterministic or “hard‑enforced” with the available mechanisms (e.g., purely conversational norms) and what mitigations are still possible (e.g., nudges, warnings, or periodic audits).

Where relevant, distinguish risks and tradeoffs specific to refactoring the existing system vs introducing a parallel greenfield path and migrating to it.

7. Completeness Checklist
End with an explicit checklist where you confirm, one by one:

You referenced the existing mechanisms correctly (commands, hooks/events, agents/skills if relevant, configs, logs).

You specified where changes happen (which files, modules, hooks, configs, scripts).

You included concrete automated tests, acceptance criteria, and a rollback/migration plan.

You respected my constraints (multi‑terminal isolation, stale‑data immunity, willingness to refactor/partially rewrite).

For any part you could not specify due to missing information, you clearly labeled it NEEDS CLARIFICATION with targeted questions instead of generic advice.

1. Context Understanding
This is a **mostly new orchestration system** built on existing tools (`yt-dlp`, `yt-fts`, `gemini-cli`, Google Takeout), with greenfield coordination and policy layers to implement the “Intelligence Stream” and CSF/CKS behaviors.[^2_1][^2_2][^2_3]

Involved parts:

- Configs: CSF categories and ROI, tool paths/flags, per-terminal identity, inclusion/exclusion filters, channel lists, Takeout locations.
- Commands/APIs: `yt-dlp` for authenticated lists, `yt-fts` for transcript DB/semantic search, `gemini-cli` for analysis runs.[^2_2][^2_3][^2_1]
- Hooks/events: watchers over watch history, watch later, local KB, and Gemini output folders.
- Agents/skills: CSF “skills” like Source Prioritizer, Conflict Checker, CKS updater, each implemented as scripts/commands.
- Logs/state: per-terminal audit and decision logs, per-terminal transient state files, shared read-only transcript DB and Takeout JSON.
- Per-terminal/session state: each terminal is a “tenant” with its own ID, config overlay, and logs, but sharing the repo and underlying tools.

Multi-terminal concurrency risks:

- Cross-terminal state bleed: one terminal’s “current CSF mode” or “last analysis result” influencing another if stored in process globals or a shared mutable file.
- Race conditions: concurrent ingestion of the same Takeout file or watch-later list; concurrent updates to a shared “current manifest” file; concurrent writes to a single log.
- Stale assumptions: long-lived processes holding config/policy in memory while config files change; scripts assuming that their last in-memory snapshot of watch history still reflects the filesystem.
- Mixed logs: shared log files making it impossible to attribute decisions to the right terminal or reconstruct per-terminal behavior.

Change scope: **Large**. This adds a new orchestration layer (watchers, policy, CKS linkage), standardizes config and logs, and enforces multi-terminal isolation by design. It is not a small patch; it is a structured architecture and repo layout refactor.

Gap vs goal:

- Gap: Ad-hoc, tool-centric workflows (run `yt-dlp` here, `yt-fts` there, send URLs to Gemini) are fragile, non-deterministic across terminals, and vulnerable to stale config/state.
- Goal: A layered, **per-terminal isolated**, **config-driven**, and **idempotent** orchestration system where each decision (what to ingest, what to analyze, how to score/curate) is computed from current files and per-terminal logs, never from long-lived in-memory state or cross-terminal globals.

***

2. Proposed Architecture

### 2.1 Layers and responsibilities

**Layer 0: Shared tools \& data (read-only in practice)**

- Tools: `yt-fts`, `yt-dlp`, `gemini-cli` binaries and their standard configs.[^2_3][^2_1][^2_2]
- Data:
    - `data/transcripts/` (managed by `yt-fts`’ SQLite DB and attachments).
    - `data/takeout/watch-history.json` (Google Takeout; regenerated, not mutated).
    - `data/video_manifests/` (normalized manifests derived from Takeout or `yt-dlp` runs).
- Responsibility: Provide consistent, global, **append-only or regenerated** data; no per-terminal mutation here (only scripts may regenerate entire artifacts deterministically).

**Layer 1: Policy/config layer**

- Files under `config/`:
    - `config/csf_categories.yaml` – mapping video features → CSF categories and ROI weights.
    - `config/intelligence_stream.yaml` – defines sources, polling intervals, allowed tools, model endpoints.
    - `config/agents/cks.yaml` – rules for conflicts, constitution update triggers.
- Rules:
    - All decisions read these files **fresh** on every enforcement/decision event.
    - No in-memory caching beyond the life of a single command.

**Layer 2: Per-terminal/session state model**

- Each terminal has a **terminal ID** (TID), derived by convention:
    - Option A (simple): user sets `export CSF_TID=<short-name>` in that terminal.
    - Option B: helper script `csf-term init` generates a UUID and writes `.csf/terminals/<pid>.json` with metadata.
- For each TID, there is a directory:
    - `.csf/tenants/<TID>/config.yaml` – per-terminal overrides (e.g., current project focus, category weights).
    - `.csf/tenants/<TID>/logs/` – per-terminal logs:
        - `actions.log`
        - `decisions.log`
        - `errors.log`
    - `.csf/tenants/<TID>/state/` – ephemeral state:
        - `last_history_scan.json`
        - `last_watch_later_scan.json`
- Responsibility:
    - Maintain **strict isolation**: each process reads/writes only its own tenant directory plus shared read-only data/config.
    - No other terminal’s TID directory is read when making decisions, except for aggregated reporting scripts that run by design.

**Layer 3: Execution / hook / event layer**

- Events (implemented as CLI or small daemons/processes per terminal):
    - `on_ingest_history` – triggered manually or by a timer in that terminal; reads Takeout JSON, produces/update manifest under `data/video_manifests/history.json`.
    - `on_ingest_watch_later` – runs `yt-dlp --cookies-from-browser ... --print id,title,...` and writes `data/video_manifests/watch_later.json`.[^2_3]
    - `on_local_kb_search` – uses `yt-fts search` over transcripts.[^2_2]
    - `on_analyze_manifest` – sends a subset of manifest entries to `gemini-cli` via a wrapper script.
    - `on_csf_update` – runs CKS/CSF scripts when new analysis artifacts are produced.
- Execution modes:
    - All “hooks” are **plain commands** (`csf-ingest`, `csf-analyze`, `csf-prioritize`) that:
        - Read current configs and per-terminal state.
        - Perform deterministic operations.
        - Emit structured logs and (optionally) outputs.

**Layer 4: Domain layer (CSF/CKS logic)**

- Domain modules:
    - `csf_source_prioritizer.py` – computes CSF priority (1–10) for each video based on policy and per-terminal context.
    - `cks_update.py` – updates constitution/agent laws based on high-scoring videos.
    - `csf_watcher.py` – per-terminal orchestrator that wires ingestion, prioritization, and analysis loops.
- Representation:
    - Inputs: manifests, transcripts, Gemini summaries.
    - Outputs: CSF/CKS decisions (e.g., “Category 3 conflict detected”), stored as JSON lines in per-terminal logs plus updates to `config/cks.yaml` or a derived `data/cks/constitution.yaml`.


### 2.2 Correctness guarantees by layer

- Layer 0:
    - Shared artifacts are either append-only (logs, transcripts) or regenerated atomically (manifest and Takeout-derived JSON), avoiding partial in-place mutations when possible.
- Layer 1:
    - Each command re-reads YAML/JSON configs at startup; no global in-memory config.
    - Config changes become effective on the next command run, regardless of session age.
- Layer 2:
    - Each terminal uses a TID that maps to **its own** `.csf/tenants/<TID>/` subtree.
    - Logs and state are never shared; each command gets the TID from environment or a per-shell file.
- Layer 3:
    - Hooks are **idempotent where possible**: re-running `on_ingest_history` with the same Takeout file yields the same manifest.
    - Side effects are recorded in per-terminal logs with timestamps and version info (e.g., config hash) to avoid ambiguity.
- Layer 4:
    - CSF / CKS decisions always recompute from **current** manifests, transcripts, config, and per-terminal logs; no long-lived objects.


### 2.3 Interaction with existing mechanisms

Reused as-is:

- `yt-fts` CLI + SQLite DB for transcripts and search.[^2_2]
- `yt-dlp` for cookies-based Watch Later and private playlist extraction.[^2_3]
- `gemini-cli` for video and transcript analysis.[^2_4]

Consolidated or deprecated:

- Ad-hoc scripts directly chaining `yt-dlp` → Gemini without logging: replaced by standardized `csf-*` commands.
- Any global, single-log-file pattern: replaced by per-terminal logging and optional aggregated reports.

Required conventions:

- Repo root contains:
    - `config/`, `data/`, `.csf/`.
- All terminal-aware commands rely on `CSF_TID` (or similar) being set or resolved.
- Manifests are under `data/video_manifests/*.json`, never per-terminal.

***

3. Implementation Plan

### 3.1 Exact places to change

Assuming a new repo `intelligence-stream/`:

- Add `config/`:
    - `config/csf_categories.yaml`
    - `config/intelligence_stream.yaml`
    - `config/agents/cks.yaml`
- Add `.csf/` (initially with `.gitkeep`):
    - `.csf/tenants/` (empty; created at runtime)
- Add `data/`:
    - `data/transcripts/` (managed by `yt-fts`)
    - `data/takeout/` (`watch-history.json` lives here)
    - `data/video_manifests/`

Commands/hooks (new scripts):

- `bin/csf-term` – manage terminal IDs:
    - `csf-term init` → generates TID, writes `.csf/tenants/<TID>/meta.json`, exports `CSF_TID` instructions.
- `bin/csf-ingest-history` – **on_ingest_history**:
    - Reads `data/takeout/watch-history.json`.
    - Applies filters from `config/intelligence_stream.yaml`.
    - Writes `data/video_manifests/history.json`.
    - Logs to `.csf/tenants/<TID>/logs/actions.log`.
- `bin/csf-ingest-watch-later` – **on_ingest_watch_later**:
    - Calls `yt-dlp --cookies-from-browser=<browser> --flat-playlist <watch-later-url> --print id,title,url`.[^2_3]
    - Normalizes output into `data/video_manifests/watch_later.json`.
- `bin/csf-local-kb-search` – uses `yt-fts search` and writes per-terminal search results.[^2_2]
- `bin/csf-analyze-manifest` – sends top-N entries (by priority) to `gemini-cli`, writes analysis artifacts to `data/analysis/<video-id>.json`.
- `bin/csf-calc-priority` – wraps `csf_source_prioritizer.py`.
- `bin/csf-update-cks` – wraps `cks_update.py`.
- `bin/csf-watcher` – `csf_watcher.py` orchestration.

Config/metadata fields to add:

- `config/intelligence_stream.yaml`:
    - `sources.history.enabled`
    - `sources.watch_later.enabled`
    - `sources.local_kb.enabled`
    - `yt_dlp.browser`
    - `yt_fts.db_path`
    - `gemini_cli.command`
    - `poll_intervals.seconds`
- `config/csf_categories.yaml`:
    - `categories` (1–12)
    - `features` (e.g., length, topic keywords, channel).
    - `weights` for priority scoring.
- `config/agents/cks.yaml`:
    - `conflict_rules`
    - `update_thresholds` (e.g., how many high-priority videos trigger a constitution update).

Per-terminal state/log files:

- `.csf/tenants/<TID>/logs/actions.log` – structured JSON lines.
- `.csf/tenants/<TID>/logs/decisions.log` – priority scores, conflicts, CKS updates.
- `.csf/tenants/<TID>/logs/errors.log`.
- `.csf/tenants/<TID>/state/last_history_scan.json`.
- `.csf/tenants/<TID>/state/last_watch_later_scan.json`.


### 3.2 New modules and refactors

New modules (greenfield):

- `csf/config_loader.py`
    - Loads `config/intelligence_stream.yaml`, `config/csf_categories.yaml`, `config/agents/cks.yaml` per call.
    - Optionally computes a hash for logging (config version).
- `csf/terminal_context.py`
    - Resolves `CSF_TID`, creates `.csf/tenants/<TID>/` if missing.
    - Returns paths for logs/state.
- `csf/manifest.py`
    - Functions to read/write `data/video_manifests/*.json`.
    - Enforces schema and idempotent operations.
- `csf/logging.py`
    - Writes structured JSON logs with `{timestamp, tid, event, payload, config_hash}`.
- `csf/source_prioritizer.py`
    - Implements priority scoring from categories \& per-terminal context.
- `csf/cks.py`
    - Conflict detection, constitution update logic.
- `csf/watcher.py`
    - Orchestrator: timed or loop-based workflows using above utilities.

Refactors vs old:

- If you already have scattered scripts like `watch_history_audit.py`, refactor:
    - Move core logic into `csf/manifest.py` and `csf/source_prioritizer.py`.
    - Leave old entrypoints as thin wrappers that call new modules, or deprecate them entirely.
- Migration:
    - Step 1: Introduce new modules and `bin/csf-*` commands alongside old scripts.
    - Step 2: Switch your daily use to `csf-*`.
    - Step 3: Delete or archive old scripts once stable.


### 3.3 Stale-data immunity

Key mechanisms:

- Each `csf-*` command:
    - Starts by calling `config_loader.load_all()` fresh.
    - Calls `terminal_context.resolve()` fresh.
    - Reads manifests/transcripts from disk at time-of-call.
- No background daemon keeps configuration in memory longer than a single iteration:
    - Even the watcher (`csf_watcher.py`) should:
        - On each iteration, reload configs (or at least watch config mtime and reload when changed).
        - Avoid storing decisions longer than needed to write them to logs.
- Any caching:
    - If you cache parsed YAML in a process:
        - Pair cache entries with source file mtimes and invalidates when mtime changes.
        - Preferably, disable caching initially; add only if performance is proven problematic.

***

4. Testing Strategy

### 4.1 Test scenarios (pytest-ready)

Multi-terminal isolation:

- Simulate two terminals `T1` and `T2` by setting `CSF_TID` to different values in test processes.
- Run `csf-ingest-history` in both at overlapping times.
    - Assert:
        - Both read the same `data/takeout/watch-history.json`.
        - Their logs are written to different `.csf/tenants/<TID>/logs/` files.
        - Decisions and states do not cross-reference the other TID.

Conflicting actions:

- Run `csf-ingest-watch-later` in `T1` while `T2` runs `csf-analyze-manifest`.
    - Verify `T2` uses the manifest as found on disk, independent of `T1` logs.
    - For race tests, introduce slight delays and verify no corrupted manifest (use atomic writes).

Skipping procedures:

- Manually create a manifest missing required fields.
- Run `csf-analyze-manifest`.
    - Expect either:
        - Validation error logged in `.csf/tenants/<TID>/logs/errors.log`.
        - Or a hard failure with clear error (non-zero exit code).
- This ensures the system does not silently proceed with malformed state.

Critical guarantees:

- Tests verifying that:
    - For all `csf-*` commands, config loader is called at the beginning.
    - A fixture modifies config file mid-test; the next `csf-*` invocation reflects it (e.g., a threshold change leads to a different priority score).

False positives:

- Provide a benign manifest entry (e.g., short entertainment video).
- Ensure `csf_source_prioritizer` yields low priority and no CKS update is triggered.


### 4.2 Stale-state simulation

- Long-running watcher:
    - Start `csf_watcher` with a small loop delay.
    - Modify `config/csf_categories.yaml` mid-run.
    - Assert that, within one loop, decisions change to reflect new rules (e.g., priority thresholds).
- Partial log failures:
    - Simulate write failures (e.g., permissions) in `.csf/tenants/<TID>/logs/`.
    - Ensure commands fail clearly and do not silently proceed without logging.


### 4.3 Acceptance and rollback

Acceptance criteria:

- After N days of use:
    - No cross-TID log entries (grep logs for unexpected TID).
    - No occurrences where config changes failed to affect decisions on the next command.
    - Low error rate (e.g., <1% commands fail due to internal errors).
    - No observed stale decisions in manual spot checks (priority or CKS updates always match current config).

Rollback plan:

- All new behavior is gated by using `bin/csf-*`.
- Rollback is:
    - Stop using `csf-*` commands.
    - Delete or ignore `.csf/` and `config/*csf*` files.
    - Return to previous ad-hoc scripts (`yt-dlp`/`yt-fts`/`gemini-cli` usage).

***

5. Observability \& Metrics

### 5.1 Per-terminal logging

Log content per terminal:

- `actions.log` entries:
    - `{timestamp, tid, command, args, config_hash, manifest_version, status}`
- `decisions.log` entries:
    - `{timestamp, tid, video_id, decision_type, priority_score, csf_category, reason_summary, inputs_hashes}`
- `errors.log` entries:
    - `{timestamp, tid, command, exception, stacktrace_summary}`

Paths:

- `.csf/tenants/<TID>/logs/actions.log`
- `.csf/tenants/<TID>/logs/decisions.log`
- `.csf/tenants/<TID>/logs/errors.log`


### 5.2 Metrics

You can either:

- Parse logs locally into CSV or a SQLite DB, or
- Add optional export endpoints (e.g., pushing to Prometheus or a local dashboard).

Metrics to derive:

- False positives / false negatives:
    - Manually tagged samples of decisions vs desired behavior (initially manual review).
- Error rate per command and per TID.
- Time-to-action:
    - Time difference between ingestion and first analysis event for a video.
- Throughput:
    - Videos ingested/analyzed per hour per terminal.


### 5.3 Detecting regressions

- Changes in `gemini-cli` or `yt-dlp` behavior (e.g., new output formats) will manifest as:
    - Increased parse errors logged.
    - Sudden spikes in `errors.log` for specific commands.
- Monitoring:
    - Create a small `csf-report` script to:
        - Summarize error counts by command and TID.
        - Highlight days with unusual spikes.
    - Use this to adapt parsers or policies promptly.

***

6. Risks \& Tradeoffs

### 6.1 Failure modes

- Misconfigured metadata (YAML):
    - Impact: incorrect priorities or skipped updates.
    - Mitigation: schema validation and test suite that loads configs in CI.
- Mis-tagged actions (wrong TID or no TID):
    - Impact: logs in unexpected places, lost traceability.
    - Mitigation: `csf-*` commands refuse to run without a valid TID; `csf-term init` becomes part of your shell profile.
- Hooks failing open vs closed:
    - You can choose:
        - Fail closed: on any critical error, stop and require manual fix.
        - Fail open with alert: log errors but continue; for CKS and security-like functions, prefer fail closed.

False positives/negatives:

- False positives: overly strict CSF rules mark many videos as problematic.
    - Shows as high block rates, high-priority flags that you disagree with.
    - Mitigation: tune `config/csf_categories.yaml` with tests and sampling.
- False negatives: subtle issues not flagged.
    - Harder to detect; requires sampling and manual audits.
    - Mitigation: periodic random sampling of low-priority videos for manual review.


### 6.2 Performance and complexity

- Overheads:
    - Frequent config and manifest reads.
    - Log writes for every command.
- Tradeoff:
    - This is deliberate to guarantee stale-state immunity.
    - If needed, you can:
        - Use lightweight formats and local SSD.
        - Add careful caching only with explicit invalidation.

Scalability:

- More terminals:
    - Adds more `.csf/tenants/<TID>/` directories; linear growth, but each is independent.
- More workflows/agents:
    - Add more modules in `csf/` and commands in `bin/` using the same patterns.
    - If manifests or logs grow large, you may:
        - Introduce indexing (e.g., manifest DB).
        - Rotate logs.


### 6.3 Soft-enforcement areas

- LLM behavior (Gemini, Claude, etc.) cannot be fully hard-enforced:
    - You can verify that an analysis was run, but not perfectly verify that it followed a conversational instruction.
    - Mitigations:
        - Standardize prompts in code, not ad hoc.
        - Log prompts and responses for sampling.
- User adherence:
    - If you manually bypass `csf-*` commands and call tools directly, the system cannot enforce behavior.
    - Mitigation: enforce via shell aliases and habits, plus periodic audits of raw tool usage.

***

7. Completeness Checklist

- Referenced existing mechanisms correctly:
    - `yt-fts` for transcript DB/search.[^2_1][^2_2]
    - `yt-dlp` with `--cookies-from-browser` for Watch Later/private playlists.[^2_3]
    - `gemini-cli` as analysis engine.[^2_4]
- Specified where changes happen:
    - New repo layout: `config/`, `.csf/`, `data/`, `csf/`, `bin/`.
    - New scripts: `csf-term`, `csf-ingest-history`, `csf-ingest-watch-later`, `csf-local-kb-search`, `csf-analyze-manifest`, `csf-calc-priority`, `csf-update-cks`, `csf-watcher`.
    - New modules: `csf/config_loader.py`, `terminal_context.py`, `manifest.py`, `logging.py`, `source_prioritizer.py`, `cks.py`, `watcher.py`.
- Included tests, acceptance, rollback:
    - Pytest scenarios for multi-terminal isolation, config changes, skipped procedures, race conditions.
    - Acceptance criteria and clear rollback (stop using `csf-*` and revert to old scripts).
- Respected constraints:
    - Multi-terminal isolation via TID and per-tenant directories.
    - Stale-data immunity via per-invocation config/state loading and no long-lived globals.
    - Willingness to refactor used to justify a full layered architecture.

NEEDS CLARIFICATION:

1. Runtime environment:
    - Are you primarily on Linux/WSL, macOS, or Windows-native shells for this repo? This determines how `CSF_TID` and `csf-term` are wired into your shell/profile.
2. `gemini-cli` specifics:
    - Are you using official Google `gemini-cli` with local models or remote endpoints, and how do you prefer to pass prompts (stdin, files, or arguments)?
3. Storage scale:
    - Approximate number of videos and transcripts (hundreds, thousands, tens of thousands) to decide whether to keep manifests as JSON files or move to a small DB.
4. Current scripts:
    - Do you already have any Takeout-processing or yt-dlp wrappers that should be refactored into this system, or is this a clean-slate implementation?
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_5][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://github.com/NotJoeMartinez/yt-fts

[^2_2]: https://pypi.org/project/yt-fts/0.1.33/

[^2_3]: https://github.com/yt-dlp/yt-dlp/wiki/FAQ

[^2_4]: https://www.youtube.com/watch?v=T76NbeTdDFA

[^2_5]: https://www.youtube.com/watch?v=LimDxy1tDmk

[^2_6]: https://www.reddit.com/r/Python/comments/142lkak/building_a_semantic_search_engine_for_youtube/

[^2_7]: https://news.ycombinator.com/item?id=36009774

[^2_8]: https://oneuptime.com/blog/post/2026-03-02-how-to-use-screen-and-tmux-for-persistent-terminal-sessions-on-ubuntu/view

[^2_9]: https://github.com/yt-dlp/yt-dlp/issues/11974

[^2_10]: https://www.youtube.com/watch?v=azkIoRMoKqs

[^2_11]: https://www.baeldung.com/linux/multiple-terminals-same-window

[^2_12]: https://www.reddit.com/r/youtubedl/comments/1hk7thz/ytdlp_cookiesfrombrowser_equals_or_no_equals/

[^2_13]: https://www.youtube.com/watch?v=LzIk_ZC87Fo

[^2_14]: https://www.lullabot.com/articles/multiple-terminal-panes-tmux

[^2_15]: https://www.youtube.com/playlist?list=PLZ5ClmhIPkfJH2r3adbqdXSrlbTDdpmyN

[^2_16]: https://css-tricks.com/one-action-multiple-terminal-windows-running-stuff/


---

# This is a clean-slate implementation starting from scratch

This clean-slate assumption fits the architecture exactly; no changes to the proposal are needed, only simplifications: everything can be implemented as greenfield modules and scripts under the new repo layout using `yt-fts`, `yt-dlp`, and `gemini-cli` as external dependencies.[^3_1][^3_2][^3_3][^3_4]

Key implications:

- No migration layer is required; old scripts and logs do not exist and therefore do not need to be bridged or maintained.
- All `csf-*` commands and `csf/` Python modules can be written assuming the new directory structure (`config/`, `.csf/`, `data/`, `bin/`) from day one.
- Tests only need to validate the new behavior, without compatibility constraints or legacy modes.

Everything in the prior architecture stands as-is, with all “refactor vs reuse” notes now interpreted as “implement the new modules and commands directly in this repo.”
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/NotJoeMartinez/yt-fts

[^3_2]: https://pypi.org/project/yt-fts/0.1.33/

[^3_3]: https://www.datacamp.com/tutorial/gemini-cli

[^3_4]: https://geminicli.com/docs/get-started/examples/

[^3_5]: https://github.com/NotJoeMartinez/yt-fts/blob/main/CHANGELOG.md

[^3_6]: https://www.reddit.com/r/TubeArchivist/comments/1ept9p1/how_to_configure_to_save_to_folder_using_youtube/

[^3_7]: https://yt-project.org/doc/developing/creating_frontend.html

[^3_8]: https://www.youtube.com/watch?v=SMKiELjUrlI

[^3_9]: https://www.reddit.com/r/Python/comments/142lkak/building_a_semantic_search_engine_for_youtube/

[^3_10]: https://www.reddit.com/r/chrome_extensions/comments/1nx3c0q/made_this_chrome_extension_to_quickly_generate/

[^3_11]: https://codelabs.developers.google.com/gemini-cli-hands-on

[^3_12]: https://www.youtube.com/watch?v=eb6vUVgQbgc

[^3_13]: https://www.youtube.com/watch?v=bjYAPKTsucE

[^3_14]: https://news.ycombinator.com/item?id=36009774

[^3_15]: https://www.youtube.com/watch?v=nAeNApj0WGw


---

# How to integrate yt-dlp and Gemini CLI into a modular pipeline

A robust way to integrate `yt-dlp` and Gemini CLI is to treat them as **modular stages in a file-based pipeline**: `yt-dlp` produces structured JSON manifests, your Python layer enriches and filters them, and Gemini CLI consumes those manifests to generate analyses and artifacts.[^4_1][^4_2][^4_3][^4_4]

Below is a concrete, long-term architecture you can actually build.

***

## Pipeline overview

Stages:

1. **Ingest (yt-dlp)**
    - Use `yt-dlp` to dump playlist/watch-later metadata as JSON lines (no downloads).[^4_5][^4_1]
    - Output: `data/video_manifests/*.jsonl` containing video IDs, URLs, titles, etc.[^4_2]
2. **Normalize \& select (Python)**
    - Python scripts read JSONL, normalize fields, and pick which videos to send to Gemini (e.g., top N or those matching rules).[^4_2]
    - Output: `data/pipeline/batches/<batch-id>.json` listing selected videos and any per-video prompts/settings.
3. **Analyze (Gemini CLI)**
    - A wrapper script iterates over the batch, calling Gemini CLI with structured prompts per video.[^4_6][^4_3][^4_4]
    - Output: `data/analysis/<video-id>.json` or `.md` per video with structured model outputs.
4. **Post-process (Python / CKS)**
    - Additional scripts compute CSF priority scores, conflicts, and constitution updates from analysis artifacts and config.

Each stage is **idempotent** and file-driven: re-running a stage with the same inputs produces the same outputs, which is key for stale-state immunity.

***

## Stage 1: `yt-dlp` ingestion

**Goal:** Get structured metadata (and optionally subtitles) without downloading video.[^4_1][^4_5]

Example: Watch Later (authenticated):

```bash
yt-dlp \
  --cookies-from-browser brave \
  --flat-playlist \
  --print "%(id)s\t%(title)s\t%(url)s\t%(duration)s\t%(channel)s" \
  "https://www.youtube.com/playlist?list=WL" \
  > data/raw/watch_later.tsv
```

If you prefer JSONL (easier for Python):[^4_1][^4_2]

```bash
yt-dlp \
  --cookies-from-browser brave \
  --flat-playlist \
  --dump-json \
  "https://www.youtube.com/playlist?list=WL" \
  > data/raw/watch_later.jsonl
```

For public playlists or channels, omit cookies.[^4_5]

Design conventions:

- Raw outputs go under `data/raw/`, never edited by hand.
- Each run can be batched, e.g. `watch_later_2026-03-26T10-19-00.jsonl`.

***

## Stage 2: Normalization \& batching (Python)

**Goal:** Convert `yt-dlp` outputs into a clean manifest and select which videos to send to Gemini.

Example manifest generator:

```bash
python -m pipeline.build_manifest \
  --input data/raw/watch_later.jsonl \
  --output data/video_manifests/watch_later_manifest.json
```

Behavior:

- Parse each JSON line.
- Extract: `id`, `title`, `url`, `duration`, `channel`, `upload_date`.[^4_2][^4_1]
- Apply filters from `config/intelligence_stream.yaml`:
    - Min/max duration.
    - Include/ignore channels.
    - Topic/keyword filters.

Then, batched selection:

```bash
python -m pipeline.build_batch \
  --manifest data/video_manifests/watch_later_manifest.json \
  --batch-out data/pipeline/batches/batch_2026-03-26T10-19-00.json \
  --limit 20
```

`batch_*.json` structure:

```json
{
  "batch_id": "batch_2026-03-26T10-19-00",
  "created_at": "2026-03-26T10:19:00Z",
  "videos": [
    {
      "id": "abc123",
      "url": "https://www.youtube.com/watch?v=abc123",
      "title": "Some video",
      "duration_seconds": 1234,
      "channel": "SomeChannel",
      "prompt_profile": "csf_category_3"
    }
  ]
}
```

This batch file is the **authoritative bridge** between `yt-dlp` and Gemini CLI.

***

## Stage 3: Gemini CLI integration

**Goal:** For each video in a batch, call Gemini CLI with a structured prompt and capture the response in a machine-readable file.[^4_3][^4_4][^4_6]

You can call Gemini CLI from a Python wrapper using `subprocess`, or from a shell script. The key is:

- Use **structured prompts** (Markdown/XML style) for consistency.[^4_6]
- Log per-video input and output for later audits.

Example shell wrapper:

```bash
python -m pipeline.run_gemini_batch \
  --batch data/pipeline/batches/batch_2026-03-26T10-19-00.json \
  --out-dir data/analysis/
```

Inside `run_gemini_batch` (conceptual):

- For each video in `batch.videos`:
    - Build a prompt:

```text
# Role
You are my Cognitive Steering Framework auditor.

# Context
Video URL: https://www.youtube.com/watch?v=abc123
Title: Some video
Duration: 1234 seconds
Channel: SomeChannel

# Task
1. Infer which CSF categories (1–12) this video primarily targets.
2. Identify any sycophancy or low-signal patterns.
3. Output a JSON object with:
   - "categories": [ints]
   - "priority_score": 1-10
   - "signals": ["string", ...]
   - "notes": "string"
```

    - Call Gemini CLI, e.g.:

```bash
gemini \
  --model gemini-3-pro-preview \
  --output-format json \
  --prompt-file /tmp/prompt_abc123.txt \
  > data/analysis/abc123.json
```

(Exact CLI flags depend on your installed version; see docs/examples. )[^4_4][^4_3]

***

## Stage 4: Post-processing \& CKS

**Goal:** From Gemini analysis outputs, compute CSF priority, detect conflicts, and update your constitution.

Example:

```bash
python -m csf.evaluate_batch \
  --batch data/pipeline/batches/batch_2026-03-26T10-19-00.json \
  --analysis-dir data/analysis/ \
  --config config/csf_categories.yaml \
  --cks-config config/agents/cks.yaml \
  --out-log .csf/tenants/$CSF_TID/logs/decisions.log
```

Behavior:

- For each video:
    - Load `data/analysis/<id>.json`.
    - Compute final `priority_score` using weights from `config/csf_categories.yaml`.
    - Detect conflicts using `cks.yaml`.
    - Write a structured decision record per video.

Optionally:

- Update a derived constitution file: `data/cks/constitution.yaml`.

***

## Modularity and isolation

To keep the pipeline modular and multi-terminal-safe:

- Each stage is its **own script/module**:
    - `pipeline/yt_dlp_ingest.py`
    - `pipeline/build_manifest.py`
    - `pipeline/build_batch.py`
    - `pipeline/run_gemini_batch.py`
    - `csf/evaluate_batch.py`
- Each script:
    - Reads config from `config/*.yaml` **on each run**.
    - Reads/writes only its own inputs/outputs.
    - Uses per-terminal logs via `CSF_TID` where relevant (mainly post-processing).

This makes it easy to:

- Swap `yt-dlp` options without touching Gemini integration.
- Change Gemini models or prompt profiles without touching ingestion.
- Run any stage manually or via cron/systemd/tmux loops.

***

## Practical command sequence

For a full run on Watch Later:

1. Ingest:

```bash
yt-dlp --cookies-from-browser brave --flat-playlist --dump-json \
  "https://www.youtube.com/playlist?list=WL" \
  > data/raw/watch_later.jsonl
```

2. Manifest:

```bash
python -m pipeline.build_manifest \
  --input data/raw/watch_later.jsonl \
  --output data/video_manifests/watch_later_manifest.json
```

3. Batch:

```bash
python -m pipeline.build_batch \
  --manifest data/video_manifests/watch_later_manifest.json \
  --batch-out data/pipeline/batches/batch_1.json \
  --limit 20
```

4. Gemini analysis:

```bash
python -m pipeline.run_gemini_batch \
  --batch data/pipeline/batches/batch_1.json \
  --out-dir data/analysis/
```

5. CSF/CKS evaluation:

```bash
CSF_TID=term1 python -m csf.evaluate_batch \
  --batch data/pipeline/batches/batch_1.json \
  --analysis-dir data/analysis/ \
  --config config/csf_categories.yaml \
  --cks-config config/agents/cks.yaml
```


This gives you a clean, composable `yt-dlp → manifest → Gemini → CSF/CKS` pipeline that can be extended with additional stages (e.g., transcript download, local `yt-fts` search) while preserving modularity and determinism.[^4_7][^4_8][^4_3][^4_4]
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://www.reddit.com/r/youtubedl/comments/x43q3c/ytdlp_flatplaylist_printjson_and_flatplaylist/

[^4_2]: https://github.com/yt-dlp/yt-dlp/issues/8926

[^4_3]: https://www.datacamp.com/tutorial/gemini-cli

[^4_4]: https://geminicli.com/docs/get-started/examples/

[^4_5]: https://ostechnix.com/yt-dlp-tutorial/

[^4_6]: https://ai.google.dev/gemini-api/docs/prompting-strategies

[^4_7]: https://pypi.org/project/yt-fts/0.1.33/

[^4_8]: https://github.com/NotJoeMartinez/yt-fts

[^4_9]: https://github.com/yt-dlp/yt-dlp/issues/14362

[^4_10]: https://github.com/yt-dlp/yt-dlp/issues/6683

[^4_11]: https://stackoverflow.com/questions/53288922/youtube-dl-dump-json-returning-different-extractor-output-for-playlist-when-ca

[^4_12]: https://cloud.google.com/blog/topics/developers-practitioners/mastering-gemini-cli-your-complete-guide-from-installation-to-advanced-use-cases

[^4_13]: https://gist.github.com/tanaikech/68d72654c8b7ca9879388051230a17ae

[^4_14]: https://www.youtube.com/watch?v=b7CRW5m6iVA

[^4_15]: https://stackoverflow.com/questions/57168566/youtube-dl-download-youtube-videos-info-json-in-a-playlist-by-ignoring-videos-s

[^4_16]: https://dev.to/shahidkhans/a-practical-guide-to-gemini-cli-941

[^4_17]: https://www.datacamp.com/tutorial/building-with-gemini-3-1-pro-coding-agent-tutorial


---

# Automating batch processing with Gemini CLI in Python scripts

Automating batch processing with Gemini CLI from Python works best if you treat Gemini as a pure function over a list of jobs: your script builds prompts, calls the CLI in **headless JSON mode**, and writes structured outputs per job.[^5_1][^5_2][^5_3]

Below is a minimal but production-grade pattern.

***

## 1. Use headless + JSON output

Gemini CLI supports non-interactive (“headless”) mode via a prompt flag and can emit machine-readable JSON with `--output-format json` (or equivalent) depending on version.[^5_2][^5_4][^5_3][^5_1]

Typical CLI form:

```bash
gemini \
  --model gemini-3-pro \
  --prompt "Summarize this text: ..." \
  --output-format json
```

Your Python batch runner will wrap this command and parse stdout as JSON.

***

## 2. Define a batch job schema

Assume a JSON file with jobs to process, e.g. `batch_jobs.json`:

```json
{
  "batch_id": "batch_2026-03-26",
  "jobs": [
    {
      "job_id": "video_abc123",
      "kind": "youtube_video",
      "url": "https://www.youtube.com/watch?v=abc123",
      "title": "Some Title"
    }
  ]
}
```

Your script will iterate `jobs` and call Gemini once per job.

***

## 3. Python subprocess wrapper for Gemini CLI

Core pattern:

- Use `subprocess.run` (not `Popen` streams) for predictable behavior.[^5_5][^5_6][^5_1]
- Pass prompt via `--prompt` or `stdin` depending on your CLI version.[^5_1][^5_2]
- Request JSON output with the appropriate flag.[^5_4][^5_3]

Example:

```python
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

GEMINI_CMD = ["gemini", "--model", "gemini-3-pro", "--output-format", "json"]

def build_prompt(job: Dict[str, Any]) -> str:
    return f"""You are my YouTube auditor.

Video URL: {job['url']}
Title: {job['title']}

Task:
1. Classify the primary purpose of this video.
2. Rate its expected signal-to-noise for my goals from 1-10.
3. Return JSON with keys: purpose, score, rationale.
"""

def run_gemini(prompt: str) -> Dict[str, Any]:
    proc = subprocess.run(
        GEMINI_CMD + ["--prompt", prompt],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Gemini CLI failed: {proc.stderr.strip()}")
    # CLI JSON format may be nested; you may need to inspect actual schema. [web:57][web:65]
    return json.loads(proc.stdout)

def process_batch(batch_path: Path, out_dir: Path) -> None:
    batch = json.loads(batch_path.read_text())
    out_dir.mkdir(parents=True, exist_ok=True)

    for job in batch["jobs"]:
        prompt = build_prompt(job)
        try:
            result = run_gemini(prompt)
        except Exception as e:
            # In production, log this instead of printing
            print(f"Error for job {job['job_id']}: {e}")
            continue

        out_file = out_dir / f"{job['job_id']}.json"
        out_file.write_text(json.dumps(result, indent=2))

if __name__ == "__main__":
    process_batch(
        batch_path=Path("data/pipeline/batches/batch_jobs.json"),
        out_dir=Path("data/analysis"),
    )
```

This gives you:

- One CLI call per job.
- One JSON file per job under `data/analysis/`.

***

## 4. Scaling patterns

To keep it robust in larger batches:

- **Rate limiting / backoff**: sleep between calls or use a small concurrency pool to avoid hitting limits.
- **Idempotency**: before running a job, check if `out_dir/job_id.json` already exists and skip unless `--force` is passed.
- **Error handling**:
    - On non-zero exit, store an error record `job_id.error.json` with stderr content.
    - Log all failures centrally for inspection.

Example idempotent guard:

```python
if out_file.exists() and not force:
    continue
```


***

## 5. Integrating into your pipeline

In the full intelligence stream:

- An earlier step builds `batch_jobs.json` from `yt-dlp` manifests.
- This Gemini batch runner is **just one stage**:
    - Input: `data/pipeline/batches/batch_*.json`.
    - Output: `data/analysis/*.json`.
- A later CSF/CKS step reads those analysis files and computes scores/decisions.

Because all integration is via files and one-shot CLI calls, the system remains:

- Multi-terminal safe (no shared in-memory state).
- Stale-state resistant (each invocation reads current jobs and config).
- Modular (you can swap Gemini CLI flags or models without touching the rest).
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://geminicli.com/docs/cli/tutorials/automation/

[^5_2]: https://github.com/dtunai/awesome-gemini-cli

[^5_3]: https://geminicli.com/docs/reference/configuration/

[^5_4]: https://github.com/google-gemini/gemini-cli/issues/8022

[^5_5]: https://github.com/google-gemini/gemini-cli/discussions/5381

[^5_6]: https://github.com/google-gemini/gemini-cli/issues/6715

[^5_7]: https://codelabs.developers.google.com/gemini-cli-hands-on

[^5_8]: https://wietsevenema.eu/blog/2025/teach-gemini-cli-inline-python-dependencies/

[^5_9]: https://realpython.com/how-to-use-gemini-cli/

[^5_10]: https://cloud.google.com/blog/topics/developers-practitioners/gemini-cli-custom-slash-commands

[^5_11]: https://starshipcli.online/documentation

[^5_12]: https://firebase.google.com/docs/ai-logic/generate-structured-output

[^5_13]: https://python.plainenglish.io/how-to-use-googles-gemini-cli-for-ai-code-assistance-1c88f917426e

[^5_14]: https://github.com/google-gemini/gemini-cli/actions/runs/20189113575

[^5_15]: https://ai.google.dev/gemini-api/docs/structured-output


---

# How did you propose dealing with YouTube, public channels, and user authenticated, watch later, history, and non-public user playlists?

YouTube is handled as a structured “intelligence stream” with **separate methods per source type**, combining `yt-dlp`, Google Takeout, `yt-fts`, and Gemini CLI, all coordinated by Python watchers and CSF/CKS logic.[^6_1][^6_2][^6_3][^6_4]

***

## Public channels

- **Tooling:** `yt-fts` (which itself uses `yt-dlp`) to scrape subtitles and build a local transcript DB.[^6_3][^6_4]
- **Method:**
    - `yt-fts download <channel-url>` to pull all available subtitles into SQLite.[^6_4]
    - `yt-fts search "<query>" --channel "<channel-name>"` for local full-text or semantic search over transcripts.[^6_3][^6_4]
- **Role in pipeline:** This is the **“Local Knowledge Base”** / “First Responder”:
    - Before hitting the wider web, you query local transcripts.
    - If there is a match, a watcher triggers Gemini CLI to “watch” that specific timestamp and extract artifacts.

***

## User Watch Later (authenticated)

- **Tooling:** `yt-dlp` with browser cookies (`--cookies-from-browser`), plus Python and Gemini CLI.[^6_5][^6_1]
- **Method (“Authenticated Bridge”):**
    - Use `yt-dlp --cookies-from-browser <browser> --flat-playlist --dump-json "https://www.youtube.com/playlist?list=WL"` to list Watch Later items as JSONL.[^6_6][^6_1]
    - A Python script normalizes that into a manifest (`data/video_manifests/watch_later.json`), selecting fields like id, title, url, duration, channel.[^6_1]
    - A Source Prioritizer script scores each video for CSF categories and picks the top N.
    - Gemini CLI batch scripts analyze those videos for sycophancy / ROI patterns and log decisions per terminal.

***

## User watch history

- **Tooling:** Google Takeout (`watch-history.json`) + Python analysis + Gemini CLI.[^6_2][^6_7]
- **Method (“Retrospective Audit”):**
    - Export YouTube watch history as JSON via Google Takeout (`watch-history.json`).[^6_7][^6_2]
    - A Python script:
        - Filters for long-form or technical videos.
        - Builds a manifest (`data/video_manifests/history.json`) with timestamps, URLs, and titles.
    - Another script compares actual history against CSF goals (e.g., Category 5/8) and feeds selected items to Gemini CLI for deeper audits of “cognitive drift.”

***

## Non-public / private playlists (including “Watch Later” \& user playlists)

- **Tooling:** `yt-dlp` with cookies, Python for manifests, Gemini CLI for analysis.[^6_8][^6_5][^6_6]
- **Method:**
    - For any private or unlisted playlist, use:
        - `yt-dlp --cookies-from-browser <browser> --flat-playlist --dump-json "<playlist-url>"` to list entries without downloading.[^6_5][^6_6]
    - Normalize to manifests similar to Watch Later:
        - `data/video_manifests/<playlist-id>.json`
    - Feed these manifests into the same Source Prioritizer → Gemini CLI analysis pipeline.
- **Role in CSF:** This is how you curate and maintain **non-public personal “Agentic Laws”**:
    - A CSF script identifies high-value videos from private playlists.
    - CKS logic may update a constitution or “agent laws” file based on these analyses.

***

## Orchestration across all sources

- **Python 3.x watchers and scripts:**
    - **Ingestors:**
        - `csf-ingest-history`: parses Takeout `watch-history.json`.[^6_2][^6_7]
        - `csf-ingest-watch-later`: wraps `yt-dlp` for `WL`.[^6_6][^6_1]
        - `csf-ingest-playlist`: generic wrapper for any user playlist URL.
    - **Dispatcher / Source Prioritizer:**
        - Reads manifests, scores entries for CSF categories, builds Gemini batches.
    - **Gemini batch runner:**
        - Calls Gemini CLI headlessly per video, storing structured JSON outputs.
    - **CKS Linker:**
        - Reads analysis outputs, runs conflict checks, and updates a CKS/constitution file.
- **Per-terminal isolation:**
    - Shared artifacts (Takeout JSON, transcripts, manifests) live under `data/`.

```
- Each terminal has its own `.csf/tenants/<TID>/logs/` and `.csf/tenants/<TID>/state/` so decisions and logs are tenant-scoped even though they operate over the same YouTube–derived inputs.
```


<span style="display:none">[^6_10][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://demodisc.zone/t/downloading-your-youtube-watch-later-playlist-with-yt-dlp/197

[^6_2]: https://yutotakano.github.io/youtube-takeout-json-to-watchmarker/

[^6_3]: https://sourceforge.net/projects/yt-fts.mirror/

[^6_4]: https://pypi.org/project/yt-fts/0.1.33/

[^6_5]: https://www.reddit.com/r/youtubedl/wiki/cookies/

[^6_6]: https://github.com/yt-dlp/yt-dlp/issues/518

[^6_7]: https://github.com/yutotakano/youtube-takeout-json-to-watchmarker

[^6_8]: https://github.com/yt-dlp/yt-dlp/issues/9029

[^6_9]: https://www.reddit.com/r/youtubedl/comments/16snue0/private_watch_later_playlist_error_with_cookiestxt/

[^6_10]: https://github.com/yt-dlp/yt-dlp/issues/13445


---

# Handling YouTube authentication session expiration in scripts

Session expiration is handled by **treating authentication as an external, short‑lived dependency** and making your scripts robust to auth failure rather than trying to “keep sessions alive.” You let `yt-dlp` pull fresh cookies from the browser when needed and fail fast when they stop working.[^7_1][^7_2][^7_3][^7_4]

***

## 1. Core principles

- **No long-lived auth in your code.**
    - Never cache cookies or tokens in Python; always rely on `yt-dlp --cookies-from-browser <browser>` or a freshly exported `cookies.txt`.[^7_3][^7_5]
- **Detect and surface expiry, don’t hide it.**
    - Treat “private playlist inaccessible” or “playlist does not exist” errors as signals that auth is broken, not as transient noise.[^7_2][^7_6]
- **Keep browser responsible for login.**
    - You re‑login in the browser as needed; scripts just reuse that session via `--cookies-from-browser` or an exported cookie file.[^7_5][^7_7][^7_8]

***

## 2. Recommended patterns with `yt-dlp`

### Use `--cookies-from-browser` by default

This uses the current browser profile’s session cookies, which are refreshed as you interact with YouTube normally.[^7_3][^7_5]

Example:

```bash
yt-dlp \
  --cookies-from-browser brave \
  --flat-playlist \
  --dump-json \
  "https://www.youtube.com/playlist?list=WL"
```

Recent versions support session cookies better (Chrome/Chromium fixes merged), so staying up to date matters.[^7_9][^7_3]

### Fallback: explicit cookies file

If browser integration is flaky or you’re on a headless box:

1. Export cookies with an extension like “Get cookies.txt locally”.[^7_7][^7_5]
2. Use: `yt-dlp --cookies cookies.txt ...`.[^7_7]

You must **re-export** when the cookie expires or YouTube revokes it.[^7_1][^7_7]

***

## 3. How scripts should detect expiration

Typical failure signals:

- `yt-dlp` errors like “The playlist does not exist” on Watch Later/private playlists when they obviously exist.[^7_6][^7_10]
- Errors about member-only / private content not being accessible even though you have access.[^7_2][^7_7]
- HTTP 403/401 or similar auth-related errors in verbose logs.[^7_1][^7_2]

Script behavior:

- Run `yt-dlp` with `capture_output` and check:
    - Non-zero exit code.
    - Known auth-related substrings in stderr.

Pseudo-code:

```python
import subprocess

AUTH_ERROR_MARKERS = [
    "The playlist does not exist",
    "members-only",
    "Private video",
    "sign in to confirm",
]

def run_ytdlp(cmd):
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = proc.stderr or ""
        if any(m in err for m in AUTH_ERROR_MARKERS):
            raise RuntimeError("AUTH_EXPIRED")
        raise RuntimeError(f"YTDLP_FAILED: {err.strip()}")
    return proc.stdout
```

Higher-level logic:

- If you catch `AUTH_EXPIRED`:
    - Log a clear message.
    - Mark the source (e.g., “watch_later”) as **auth-stale** in a state file.
    - Skip further private operations until you refresh login/cookies.

***

## 4. State files and user prompts

Keep a tiny, per-terminal state file, e.g. `.csf/tenants/<TID>/state/auth_status.json`:

```json
{
  "youtube": {
    "last_ok": "2026-03-26T10:20:00Z",
    "last_error": "2026-03-26T10:22:10Z",
    "status": "auth_expired"
  }
}
```

Script policy:

- Before running private `yt-dlp` commands:
    - Read auth_status.
    - If `status == "auth_expired"` and `last_error` is recent, either:
        - Skip with a log entry, or
        - Only attempt once per N minutes.
- When an authenticated call succeeds:
    - Update status to `ok` and `last_ok` timestamp.

This avoids noisy loops hammering YouTube with broken auth and makes auth problems explicit instead of silent.

***

## 5. Operational practices

- **Keep `yt-dlp` up to date**
    - Many auth issues have been fixed via updates (session cookie handling, Chrome/Brave expiry semantics).[^7_9][^7_2][^7_3]
- **Use a stable YouTube account for automation**
    - Consider using a dedicated account for automated reading (not your primary), as some users have reported bans when doing heavy automated pulls.[^7_11][^7_4]
- **Accept manual refresh as part of the system**
    - Your architecture assumes: “when auth expires, scripts fail fast, mark status, and ask you to re-auth in the browser or refresh cookies.”
    - No attempt to auto-login or circumvent YouTube’s session management.

***

## 6. How this fits your intelligence stream

Within the intelligence-stream design:

- Watch Later / private playlist ingestors:
    - Always call `yt-dlp --cookies-from-browser`.
    - Treat failures with auth markers as `AUTH_EXPIRED`.
    - Set `auth_status.youtube` to `auth_expired` in that terminal’s state.
- CSF/CKS watcher:
    - Reads `auth_status` each loop.
    - If `auth_expired`, it logs a **“needs attention: refresh YouTube auth”** event and stops trying private endpoints until status is reset.

This keeps the pipeline deterministic, multi-terminal-safe, and honest about authentication limitations, instead of burying them in retries or long-lived, fragile sessions.
<span style="display:none">[^7_12]</span>

<div align="center">⁂</div>

[^7_1]: https://github.com/yt-dlp/yt-dlp/issues/12009

[^7_2]: https://github.com/yt-dlp/yt-dlp/issues/8227

[^7_3]: https://github.com/yt-dlp/yt-dlp/issues/5534

[^7_4]: https://www.reddit.com/r/youtubedl/comments/1fm66pb/is_there_a_cookie_option_where_when_i_use_ytdlp/

[^7_5]: https://www.youtube.com/watch?v=Idtr2_0kfQ0

[^7_6]: https://github.com/yt-dlp/yt-dlp/issues/518

[^7_7]: https://www.youtube.com/watch?v=DsS1jCDZGek

[^7_8]: https://www.reddit.com/r/youtubedl/wiki/cookies/

[^7_9]: https://github.com/yt-dlp/yt-dlp/issues/13445

[^7_10]: https://github.com/yt-dlp/yt-dlp/issues/9029

[^7_11]: https://www.reddit.com/r/youtubedl/comments/1n0jmhx/has_anyone_here_gotten_banned_for_passing/

[^7_12]: https://www.youtube.com/watch?v=nAeNApj0WGw


---

# Best practices for managing browser profiles with yt-dlp

Use browser profiles with `yt-dlp` by standardizing **which profile is used, how it’s referenced on disk, and how cookies are exported/rotated**, rather than letting each script improvise.[^8_1][^8_2][^8_3]

***

## 1. Choose a dedicated profile per purpose

- Use a **separate browser profile** (or even account) for automation-related YouTube access, especially for Watch Later / private playlists.[^8_4][^8_5]
- Benefits:
    - Clear separation from personal browsing.
    - Reduced risk if cookies leak.
    - More predictable cookie lifetime and fewer surprise logouts.

Examples:

- Chrome/Brave profiles:
    - `~/.config/google-chrome/Profile 2`
    - `~/.config/BraveSoftware/Brave-Browser/Profile 2`
- Use this profile exclusively for your automation (sign into YouTube once there).

***

## 2. Prefer `--cookies-from-browser` with explicit profile

`yt-dlp` can read cookies directly from a specific browser and profile.[^8_2][^8_6][^8_1]

Patterns:

- Default profile:

```bash
yt-dlp --cookies-from-browser brave "https://www.youtube.com/playlist?list=WL"
```

- Specific profile path (Linux example):[^8_1]

```bash
yt-dlp \
  --cookies-from-browser "chrome:~/.config/google-chrome/Profile 2" \
  "https://www.youtube.com/playlist?list=WL"
```


Best practices:

- Hard-code the profile path in **config**, not in scripts:
    - `config/intelligence_stream.yaml`:

```yaml
youtube:
  browser: chrome
  profile_path: "~/.config/google-chrome/Profile 2"
```

- Your wrapper script builds the `--cookies-from-browser` argument from this config.

***

## 3. Use cookies files only when necessary

If browser extraction fails or you’re on a headless machine, use an exported cookies file in **Netscape format**:[^8_3][^8_2][^8_1]

- Export with extension (desktop use):
    - Chrome: “Get cookies.txt LOCALLY”.[^8_6][^8_3]
    - Firefox: “cookies.txt”.[^8_2]
- Or export with `yt-dlp` itself:[^8_1]

```bash
yt-dlp --cookies-from-browser chrome --cookies cookies.txt
```


Then consume:

```bash
yt-dlp --cookies cookies.txt "https://www.youtube.com/playlist?list=WL"
```

Guidelines:

- Keep cookie files in a **restricted directory**, e.g. `~/.config/yt-cookies/`.[^8_1]
- Treat them as secrets (they contain all sites’ cookies if exported broadly).[^8_2][^8_1]
- Re-export when they expire; don’t try to “fix” expired cookies in code.[^8_3]

***

## 4. Make profile usage explicit in your pipeline

In your intelligence-stream scripts:

- Centralize profile config:
    - `config/intelligence_stream.yaml` holds:
        - `youtube.browser`
        - `youtube.profile_path` (optional)
        - `youtube.auth_mode` (`browser` or `cookies_file`)
        - `youtube.cookies_file` (if used)
- A single helper builds the final `yt-dlp` command:

```python
def build_ytdlp_cookies_args(cfg):
    if cfg["auth_mode"] == "browser":
        if cfg.get("profile_path"):
            return ["--cookies-from-browser",
                    f'{cfg["browser"]}:{cfg["profile_path"]}']
        return ["--cookies-from-browser", cfg["browser"]]
    elif cfg["auth_mode"] == "cookies_file":
        return ["--cookies", cfg["cookies_file"]]
    else:
        return []
```


This ensures **every** `yt-dlp` call uses the same profile configuration.

***

## 5. Handle OS- and browser-specific quirks

From the FAQ and community docs:[^8_2][^8_1]

- Chrome Flatpak or non-standard installs:
    - Use explicit path, e.g. `chrome:~/.var/app/com.google.Chrome/`.
- Locked cookie DB (Chrome/Edge/Brave):
    - Some setups require flags like `--disable-features=LockProfileCookieDatabase` or helper tools/extensions.[^8_2]
- Windows vs Unix newlines when using cookies files:
    - Bad newline format can cause `HTTP Error 400` with `--cookies`.[^8_1]

The pattern:

- Start with `--cookies-from-browser <browser>` on the platform’s default profile.
- If it fails, upgrade to explicit profile path.
- Only then fall back to cookies file export.

***

## 6. Security \& hygiene

- **Use burner / automation accounts** for heavy scripted usage, not your primary Google account.[^8_5][^8_4]
- Restrict file permissions on:
    - `cookies.txt`
    - Any config files containing profile paths or hints.
- Keep `yt-dlp` updated:
    - Many cookies/profile handling issues are version-specific; updates often fix browser integration problems.[^8_7][^8_1]

***

## 7. Summary pattern for your system

- Define one or more named YouTube “auth profiles” in your config:
    - `primary`, `automation`, etc., each with browser and path.
- Use a single helper in your Python layer to:
    - Resolve profile → `--cookies-from-browser ...` or `--cookies ...`.
- Scripts never hard-code profile paths; they read config each run, making it easy to swap profiles or rotate cookies without code changes.
- Errors from `yt-dlp` relating to private/age-restricted content are treated as **auth/profile issues**, logged clearly, and surfaced (not silently ignored).
<span style="display:none">[^8_10][^8_8][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://github.com/yt-dlp/yt-dlp/wiki/FAQ

[^8_2]: https://www.reddit.com/r/youtubedl/wiki/cookies/

[^8_3]: https://www.youtube.com/watch?v=DsS1jCDZGek

[^8_4]: https://www.reddit.com/r/youtubedl/comments/1emm5qk/need_help_with_use_cookies_from_browser_commands/

[^8_5]: https://www.reddit.com/r/youtubedl/comments/1n0jmhx/has_anyone_here_gotten_banned_for_passing/

[^8_6]: https://www.youtube.com/watch?v=Idtr2_0kfQ0

[^8_7]: https://github.com/yt-dlp/yt-dlp/issues/14710

[^8_8]: https://github.com/kevinwatt/yt-dlp-mcp/issues/19

[^8_9]: https://www.youtube.com/watch?v=wm0AuczqmRM

[^8_10]: https://www.youtube.com/watch?v=nAeNApj0WGw

