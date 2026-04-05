# ADR-20260401: CHS as Unified Multi-Provider Session History Layer

**Date:** 2026-04-01
**Status:** Accepted
**Author:** Claude Code

---

## Context

### Problem Statement

Current history ownership is fragmented across multiple overlapping systems:

- Claude upstream `history.jsonl` / transcript JSONL — owned by Claude Code, subject to retention settings
- `claude-log` — wired on multiple hook events, uses unsafe shared cache files
- `claude-history` — searches Claude chat history and an SQLite DB, but depends too directly on upstream files
- CHS ingestion via `SessionStart_chs_delta_reindex.py` — directly reads `~/.claude/history.jsonl` (`SessionStart_chs_delta_reindex.py:33`)
- Hook/runtime telemetry — no unified event model

This fragmentation creates two systemic risks:

1. **Purge regression** — Claude retention settings can silently delete session history, breaking search and debugging
2. **Multi-terminal isolation violation** — shared mutable cache files in `claude-log` can cross-contaminate terminal-private state

There is also a growing requirement for multi-provider history usable for:
- debugging past sessions
- open-task and opportunity discovery
- cross-provider pattern analysis (Claude Code + Codex + Gemini Desktop)

### Current Architecture

```
search-research
  └── claude_history_backend.py (CHS client, "claude-history" name)
        │
        └── CHS (search-research/core/chs/)
              ├── CHSIndexer, CHSSearcher, CHSSearchV2
              └── db.py + schema.sql (single-provider model)
                    │
                    └── SessionStart_chs_delta_reindex.py
                          └── reads ~/.claude/history.jsonl (Claude-owned)
```

Relevant evidence:
- `claude_history_backend.py:30` — backend name is `"claude-history"`
- `SessionStart_chs_delta_reindex.py:33` — `HISTORY_JSONL = Path.home() / ".claude" / "history.jsonl"`
- `hook_ledger.py:4-10` — "Authoritative hook state for multi-terminal isolation" — SQLite WAL primary store, records tool events for verification

### Constraints

- CHS must remain the only chat-history backend exposed to `search-research` (stable interface)
- `claude-history` package is the preferred archive/search engine to evolve
- `claude-log` is non-authoritative going forward
- Retention must be local and append-only, independent of upstream Claude settings
- Provider-specific logic must live below CHS, not in `search-research`
- Multi-terminal isolation: `terminal_id + turn_id` is the correctness boundary (`hook_ledger.py:9`)
- No correctness decisions depend on shared mutable temp files

---

## Decision

**CHS remains the `search-research` chat-history backend and is upgraded into a unified multi-provider conversation-history layer.**

### Layered Architecture

```
search-research
  └── CHS (stable upward interface)
        ├── Provider orchestration + archive ingestion
        ├── Normalized event DB + projections
        └── Provider adapters (below CHS)
              ├── claude_code_raw       (upstream: Claude Code history.jsonl)
              ├── claude_code_archive    (local append-only archive)
              ├── codex_desktop
              ├── gemini_cli
              └── claude_desktop
```

### Data Model

Two-tier storage:

1. **Append-only raw archive** — local files under project ownership, non-purging, stores provenance + ingest watermarks
2. **Normalized event DB** — structured tables for conversations, sessions, turns, messages, tool events, task events, decision/opportunity events, artifact/fact bindings

Every normalized record links back to a raw archive event. The archive is the authoritative source; the normalized DB is a derived read model.

### Provider Model

Each provider implements a `ProviderProtocol` (see below). Providers are additive — no `search-research` changes required for new providers.

### Normalized Event Envelope

All events use a source-neutral envelope:

```
provider_id, source_id, native_event_id, conversation_id, session_id,
terminal_id, turn_id, occurred_at, content_hash, raw_payload, metadata_json
```

`terminal_id + turn_id` is the transient reasoning boundary. For cross-provider events where a native `terminal_id` does not exist (e.g., Codex Desktop), the provider must normalize one — see **Terminal ID Scoping Strategy** below.

### Task / Opportunity Event Types

```
task_opened, task_updated, task_blocked, task_resolved,
task_reopened, opportunity_detected, opportunity_confirmed, opportunity_dismissed
```

These are emitted by hooks during task lifecycle operations and stored in the normalized DB for projection queries.

---

## ProviderProtocol Interface

**Location:** `packages/search-research/core/chs/providers/base.py`

This protocol MUST be defined before Phase 1 begins. All providers implement it.

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass(frozen=True)
class ProviderCapabilities:
    supports_incremental: bool
    supports_backfill: bool
    has_task_events: bool
    has_tool_events: bool

@runtime_checkable
class Provider(Protocol):
    @property
    def provider_id(self) -> str: ...

    @property
    def capabilities(self) -> ProviderCapabilities: ...

    def discover(self) -> list[dict]: ...
        """Return list of available source IDs (e.g., session file paths)."""

    def ingest_since(self, watermark: dict) -> list[dict]:
        """Ingest events since watermark. Returns list of normalized event envelopes."""

    def fetch_session(self, source_id: str) -> dict: ...

    def fetch_message(self, source_id: str, message_id: str) -> dict: ...
```

**Initial providers implementing this protocol:**
- `claude_code_raw` — reads from `~/.claude/history.jsonl` and transcript JSONL files
- `claude_code_archive` — reads from the local append-only archive (Phase 2)

---

## Terminal ID Scoping Strategy (Cross-Provider Events)

**Problem:** Codex Desktop and Gemini CLI do not emit Claude Code `terminal_id` values. Cross-provider queries that filter by `terminal_id` would return empty results for non-Claude providers.

**Resolution:** Each provider normalizes a `terminal_id` using its own scoping:

| Provider | terminal_id source |
|----------|-------------------|
| `claude_code_raw` | Native `terminal_id` from Claude Code session context |
| `claude_code_archive` | Inherited from source event provenance |
| `codex_desktop` | Normalized to `codex_{workspace_hash}` — workspace-scoped, not terminal-scoped |
| `gemini_cli` | Normalized to `gemini_{session_id}` |
| `claude_desktop` | Normalized to `claude_desktop_{conversation_id}` |

**Rule:** `terminal_id` in the event envelope always reflects the local execution context that generated the event. For cross-provider tools (e.g., a task created in Codex but referenced in Claude Code), the `terminal_id` reflects where the event was observed, not where it originated.

---

## Package Ownership

| Package | Role |
|---------|------|
| `claude-history` | Main history/archive/search package under CHS architecture |
| `claude-log` | Non-authoritative — will be converted to thin ingest adapter or export tool |
| CHS | Unified backend abstraction, provider orchestration, normalized DB, projections |
| `hook_ledger` | **Live operational correctness layer that records structured events for verification** — does NOT emit events downstream to CHS; CHS reads from the archive, not from hook_ledger |

**Correction from draft:** The draft described hook_ledger as "emitting structured events downstream." This is incorrect. `hook_ledger.py` is a verification and state ledger — it records what tools ran and their outputs for later verification (`hook_ledger.py:4-10`). CHS ingestion reads from the append-only archive, not from hook_ledger.

---

## Consequences

### Positive

- Retention no longer depends on Claude purge policy — local archive is the authority
- CHS remains a stable backend for `search-research` — interface unchanged
- Multi-provider history becomes possible without changing the search orchestrator
- Append-only archive with provenance enables auditability and rebuild

### Negative

- More ingestion infrastructure required (provider adapters, archive storage)
- Migration of current `claude-log` / direct history ingestion needed
- Schema migration from current CHS single-provider schema to normalized multi-entity schema

### Neutral

- `search-research` interface stays stable — only CHS internals change

---

## Rollback Plan

If Phase 1-3 introduce regressions:

1. **Revert provider model:** Remove `ProviderProtocol` and provider adapters; restore direct `claude_history_backend.py` as sole CHS backend
2. **Revert normalized DB:** Delete new tables added in Phase 3; CHS falls back to current schema
3. **Revert archive path:** Point CHS at existing `chat_history.db`; archive path can coexist without being wired
4. **Restore claude-log:** Re-enable `claude-log` as retention authority (shared cache risk remains — this is the pre-existing bug, not the rollback risk)

**Rollback triggers:**
- `search-research` chat history queries return empty results after provider changes
- Ingest produces duplicate events on replay
- Multi-terminal activity causes cross-contamination of terminal-private state

**Rollback time estimate:** <30 minutes (restore 3-4 import/path changes, no data migration needed)

---

## Implementation Phases

See `plan-20260401-chs-history-provider-architecture.md` for full execution details.

| Phase | Focus | Blocker |
|-------|-------|---------|
| 1 | `ProviderProtocol` + registry + `claude_code_raw` | Must complete before any other provider |
| 2 | Append-only raw archive + provenance | Requires Phase 1 |
| 3 | Normalized event DB schema + ingest wiring | Requires Phase 2 |
| 4 | CHS search integration with archive-backed data | Requires Phase 3 |
| 5 | Provider expansion (codex, gemini, claude_desktop) | Additive, no blocker |
| 6 | `claude-log` de-authoritization + adapter conversion | Spike in Phase 1-2 to validate approach |
| 7 | Task and opportunity projections from normalized events | Requires Phase 3 |

**Phase 1 is the critical path.** It defines the `ProviderProtocol` that all subsequent phases depend on. Do not begin Phase 2 until Phase 1 is stable and tested.

---

## Related Documents

- `packages/search-research/core/backends/local/claude_history_backend.py`
- `packages/search-research/core/chs/__init__.py`
- `.claude/hooks/SessionStart_chs_delta_reindex.py`
- `.claude/hooks/__lib/hook_ledger.py`
- `plan-20260401-chs-history-provider-architecture.md`
