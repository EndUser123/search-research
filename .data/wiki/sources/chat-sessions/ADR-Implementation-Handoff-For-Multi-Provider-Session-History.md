# ADR + Implementation Handoff For Multi-Provider Session History

## Summary

Create two handoff documents, not one:

1. **ADR** in the existing architecture-decision style, to lock the long-term design.
2. **Implementation plan** in the existing plan-file style, to give a simpler LLM a decision-complete execution spec.

Use these target paths and titles:

- `P:\.claude\arch_decisions\ADR-20260401-chs-multi-provider-history-archive.md`
  - Title: `ADR-20260401: CHS as Unified Multi-Provider Session History Layer`
- `P:\.claude\plans\plan-20260401-chs-history-provider-architecture.md`
  - Title: `Implementation Plan: CHS Multi-Provider History Archive and Search Integration`

Chosen defaults:
- **CHS remains the chat-history backend abstraction** under `search-research`
- **Claude-managed history files are upstream inputs only**, never the retention authority
- **Your own append-only archive + normalized event DB become authoritative**
- **`claude-history` is retained as the main history/search package**, but re-scoped under the CHS architecture
- **`claude-log` stops owning durable storage** and becomes either an ingest adapter or a read-only formatter/export tool

## ADR Content

Write the ADR as an accepted architectural decision in the style of the existing ADRs under `P:\.claude\arch_decisions`.

Required sections:

- **Status**
  - `Accepted`
- **Date**
  - `2026-04-01`
- **Decision**
  - CHS remains the `search-research` chat-history backend
  - CHS is upgraded into a unified multi-provider conversation-history layer
  - Conversation history must support multiple upstream providers:
    - Claude Code default history/transcripts
    - enhanced retained local archive
    - Codex history
    - Gemini history
    - Claude Desktop history
  - Retention is owned by the local archive, not by upstream app settings
- **Context**
  - Current overlap among:
    - Claude upstream `history.jsonl` / transcript JSONL
    - `claude-log`
    - `claude-history`
    - CHS ingestion
    - hook/runtime telemetry
  - Purge regression risk from Claude retention settings
  - Requirement for multi-terminal isolation and stale-data immunity
  - Requirement for non-purging detailed session history usable for:
    - debugging
    - lookup
    - open-task discovery
    - opportunity detection
- **Architecture Decision**
  - Preserve layering:
    - `search-research -> CHS -> source providers -> archive/event store -> derived indexes`
  - Introduce provider model inside CHS
  - Introduce canonical archive and normalized event DB
  - Keep search/index layers rebuildable
- **Provider Model**
  - CHS owns provider adapters
  - Initial providers:
    - `claude_code_raw`
    - `claude_code_archive`
    - `codex_desktop`
    - `gemini_cli`
    - `claude_desktop`
  - Provider contract must include:
    - source discovery
    - incremental ingest by watermark
    - stable native identifiers
    - normalized event emission
    - capability advertisement
- **Data Model**
  - Raw archive is append-only and non-purging
  - Normalized DB stores:
    - conversations
    - sessions
    - turns
    - messages
    - tool events
    - task events
    - decision/opportunity events
    - artifact/fact bindings
  - Every normalized record links back to raw provenance
- **Isolation and Staleness Rules**
  - `terminal_id + turn_id` is the transient reasoning boundary
  - workspace-shared state is separated from terminal-private state
  - every fact from file/tool observations is revision-bound and invalidatable
- **Consequences**
  - Positive:
    - retention no longer depends on Claude purge policy
    - CHS remains a stable backend for `search-research`
    - multi-provider history becomes possible without changing the search orchestrator
  - Negative:
    - more ingestion infrastructure
    - migration of current `claude-log` / direct history ingestion
  - Neutral:
    - `search-research` interface stays stable
- **Package Ownership**
  - `claude-history`: main history/archive/index package under CHS architecture
  - `claude-log`: no longer an authority
  - CHS: unified backend abstraction and provider orchestration
  - `hook_ledger`: live operational correctness layer that emits structured events downstream
- **Related Files / Prior Art**
  - `P:\packages\search-research\core\backends\local\claude_history_backend.py`
  - `P:\packages\claude-history\README.md`
  - `P:\.claude\hooks\SessionStart_chs_delta_reindex.py`
  - `P:\.claude\hooks\__lib\hook_ledger.py`

## Implementation Plan Content

Write the plan in the style of `P:\.claude\hooks\plans\plan-20260306-posttooluse-logging-fix.md`, but for a larger multi-phase architecture change. The plan must be decision-complete and targeted at a simpler LLM.

Required sections:

- **Problem Statement**
  - Current history ownership is fragmented
  - Claude retention can regress silently
  - `claude-log` uses unsafe shared cache files
  - CHS currently depends too directly on Claude-specific history inputs
- **Success Criteria**
  - CHS remains the only chat-history backend exposed to `search-research`
  - full-fidelity session history is retained locally even if upstream files purge
  - multiple providers can be ingested without changing `search-research`
  - open tasks/opportunities/debug timelines are queryable from normalized history
  - no shared mutable cache files in the correctness path
- **Current State Analysis**
  - `claude_history_backend.py` is already the correct upward boundary
  - `claude-history` currently searches Claude chat history and an SQLite DB
  - `SessionStart_chs_delta_reindex.py` currently ingests directly from `Path.home()/.claude/history.jsonl`
  - `claude-log` is currently wired on multiple hook events and should not remain a retention authority
- **Target Architecture**
  - `search-research`
    - asks CHS for chat history
  - `CHS`
    - owns provider orchestration, archive ingestion, normalized DB, projections
  - `claude-history`
    - becomes the archive/search engine package used by CHS
  - `hook_ledger`
    - remains runtime correctness state and mirrors events into CHS/archive
- **Public Interfaces / Types**
  - Define CHS provider interface with:
    - `provider_id`
    - `discover`
    - `ingest_since`
    - `fetch_session`
    - `fetch_message`
    - `capabilities`
  - Define normalized source-neutral event envelope with:
    - `provider_id`
    - `source_id`
    - `native_event_id`
    - `conversation_id`
    - `session_id`
    - `terminal_id`
    - `turn_id`
    - `occurred_at`
    - `content_hash`
    - `raw_payload`
    - `metadata_json`
  - Define task/opportunity event types:
    - `task_opened`
    - `task_updated`
    - `task_blocked`
    - `task_resolved`
    - `task_reopened`
    - `opportunity_detected`
    - `opportunity_confirmed`
    - `opportunity_dismissed`
- **Implementation Phases**

  Phase 1: CHS provider abstraction
  - add provider interface and registry under the CHS/history layer
  - keep `search-research` interface unchanged
  - add `claude_code_raw` provider first

  Phase 2: canonical archive
  - add append-only raw archive under local ownership
  - archive upstream history/transcript/provider events before indexing
  - store provenance and ingest watermarks

  Phase 3: normalized event DB
  - add normalized tables for messages, turns, sessions, tool/task/decision/opportunity events
  - ensure all normalized rows link to raw archive events

  Phase 4: CHS search integration
  - point CHS search paths at normalized/archive-backed data
  - keep support for exact search and semantic search as derived read models

  Phase 5: provider expansion
  - add `claude_code_archive`
  - add `codex_desktop`
  - add `gemini_cli`
  - add `claude_desktop`
  - all provider additions must be additive and not require `search-research` changes

  Phase 6: `claude-log` de-authoritization
  - remove shared transcript cache ownership from `claude-log`
  - either:
    - convert it to a thin ingest adapter into CHS/archive, or
    - limit it to formatting/export/debug views

  Phase 7: task and opportunity projections
  - build open-task and opportunity views from normalized events
  - avoid relying on raw grep over transcripts for task state

- **Dedupe / Merge Rules**
  - primary dedupe key:
    - `(provider_id, source_id, native_event_id)`
  - fallback fingerprint when native ids are absent:
    - provider kind + normalized role + occurred_at bucket + normalized content + session hint
  - do not dedupe across providers on text equality alone
  - merge sessions only with strong evidence, otherwise preserve separate provenance
- **Multi-Terminal Safety**
  - terminal-private state remains under `terminal_id + turn_id`
  - shared task/file/workspace history is explicitly workspace-scoped
  - no correctness decisions depend on shared mutable temp files
- **Stale-Data Immunity**
  - facts from `Read`/`Grep`/tool observations must bind to source revision or artifact revision
  - writes and external mutations invalidate old bindings
  - projections must answer “current state” and “state at prior event”
- **Test Plan**
  - provider ingest idempotency:
    - replay same source twice without duplicates
  - purge resilience:
    - ingest from Claude source, then remove upstream file, verify archive/search still work
  - multi-provider coexistence:
    - Claude + Codex + Gemini events coexist without false merges
  - CHS backend compatibility:
    - `search-research` still gets chat-history results through one backend
  - multi-terminal isolation:
    - concurrent terminal activity does not cross-contaminate terminal-private state
  - stale fact invalidation:
    - a file-backed fact becomes stale after mutation
  - task projection correctness:
    - task lifecycle view matches emitted task events
- **Acceptance Scenarios**
  - “What did we discuss about X?” returns results through CHS even after upstream Claude purge
  - “Show open tasks from last week” works from normalized history
  - “Find repeated failure patterns” works from archived hook/tool events
  - Codex/Gemini/Claude Desktop history can be added as providers without changing `search-research`
- **Rollout / Migration Notes**
  - keep old paths temporarily for compatibility, but mark them non-authoritative
  - migrate ingest first, then search, then provider expansion, then cleanup
  - no big-bang cutover required
- **Explicit Non-Goals**
  - do not redesign `search-research` orchestration
  - do not require one provider schema per upstream app at the search API level
  - do not keep multiple retention authorities

## Test Cases And Scenarios

The final docs should explicitly include these high-signal scenarios:

- ingest Claude Code default history and transcripts into local archive
- simulate upstream history purge and verify retained local search still works
- ingest same data twice and verify dedupe
- ingest overlapping content from two providers and verify separate provenance
- verify CHS remains the only backend path used by `search-research`
- verify open-task projection from chat/tool/task events
- verify opportunity detection from repeated failures
- verify terminal-scoped state remains isolated while shared workspace history remains queryable
- verify file-backed facts become stale after file mutation or later conflicting evidence

## Assumptions And Defaults

- Use the repo’s existing ADR style from `P:\.claude\arch_decisions`
- Use the repo’s existing implementation-plan style from `P:\.claude\hooks\plans`
- Keep CHS as the backend provider to `search-research`
- Treat `claude-history` as the preferred history/archive/search package to evolve
- Treat `claude-log` as non-authoritative going forward
- Make retention local and append-only, independent of upstream Claude settings
- Keep provider-specific logic below CHS, not in `search-research`
- Write the ADR as architecture rationale and the plan as a simpler-LLM implementation handoff; do not combine them into a single hybrid doc
