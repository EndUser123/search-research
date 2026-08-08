---
title: "Hook-block observability: per-session logging with escalation path to centralized and OTel"
created: 2026-08-08
source: session-2026-08-08
tags: [hook-observability, session-scoping, multi-terminal-isolation, logging, opentelemetry, multi-tenant, architecture, decision]
host: grok
agent: grok
cognitive_load: 2
verification: directly-verified
relations:
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: implements
  - target: wiki/concepts/pipeline-session-scoping-each-layer-independently.md
    type: complements
  - target: wiki/concepts/hook-fleet-io-failure-modes-cascade-amplification.md
    type: refines
  - target: wiki/concepts/verification-state-tracking-content-identity-vs-temporal-proxies.md
    type: related
summary: >
  PreToolUse hooks that block (exit code 2) now write a session-scoped JSONL
  log record before blocking. The pattern: hook-blocks-{session_id}.jsonl,
  one file per session, zero cross-session contamination. This is the local
  optimum for this host — the escalation path to centralized+session-tag and
  then to OpenTelemetry tracing is documented with triggers and reasons.
---

# Hook-block observability: per-session logging with escalation path

## Decision context

A PreToolUse hook (`dead_zone_guard.py`) blocked a write to `docs/designs/`
during a design-review session. The operator saw "failed with exit code 1"
in the TUI health-check display but couldn't determine: which session
produced the block, what file was blocked, or what the message was. There
was no persistent record of the block — the stderr message was ephemeral.

The operator asked: "we should have logs or observability enabled for you
to check for the hook error." Investigation revealed that PreToolUse hook
blocks are the one category of hook event with no logging infrastructure.
PostToolUseFailure has `spawn-errors.jsonl`, the spawn gate has
`spawn-blocks.jsonl`, but PreToolUse blocks produce nothing persistent.
The [[hook-fleet-io-failure-modes-cascade-amplification]] concept documents
the broader pattern of advisory bare-except writes across the hook fleet —
this is the observability gap that results.

## The pattern: per-session file

Each hook that exits with code 2 (BLOCKED) writes a JSONL record to:

```
~/.grok/hooks/state/hook-blocks-{session_id}.jsonl
```

The `session_id` comes from the hook payload (`data.get("sessionId", "")`),
NOT from environment variables (`$env:GROK_SESSION_ID` is empty on this
host — verified). Every Grok Build hook receives the session ID in its
stdin JSON payload.

Record schema:

```json
{
  "ts": 1723123456.789,
  "hook": "dead_zone_guard",
  "tool": "write",
  "file_path": "P:/docs/designs/example.md",
  "exit_code": 2,
  "message": "BLOCKED: ..."
}
```

### Why per-session file (not centralized + session tag)

| Factor | Per-session file | Centralized + session tag |
|--------|-----------------|--------------------------|
| Isolation | Strong (filename IS the filter) | Logical (field-based, requires filtering) |
| Cross-session queries | Requires scanning all files | Easy (grep one file) |
| Filtering complexity | Zero (open your file) | Every reader must filter |
| Contamination risk | Zero (structural) | Non-zero (forgot-to-filter bug) |
| Consistency with existing hooks | Matches 6 existing hook families | New pattern for this host |

The per-session-file pattern is the **"silo per tenant"** multi-tenant
strategy (AWS S3 dedicated-bucket-per-tenant). It's the strongest isolation
and matches what 6 existing hook families already do:
`mutation-receipts-{session_id}.jsonl`, `quality-nudge-{session_id}.jsonl`,
`quality-obligation-{session_id}.json`, `quality-receipts-{session_id}/`.

### Why NOT OpenTelemetry (yet)

OpenTelemetry's GenAI semantic conventions (OTel SIG, 2024-2026) define
the industry-standard approach: each agent action emits a span with
`trace_id` + `span_id` + parent-child context. Spans go to a centralized
collector (Jaeger, Tempo, Langfuse). Cross-session tracing is native.

The OTel approach is the right long-term target but requires:
- An OTel collector (Docker container)
- A storage backend (Jaeger/Tempo/Langfuse)
- SDK instrumentation in every hook (`@opentelemetry/api`)
- Configuration of exporters, sampling, retention

For hook-block logging today, this is infrastructure overkill. The
per-session-file pattern gives 90% of the value (session-scoped block
records, queryable, persistent) at 10% of the cost (10 lines of Python
per hook, no new infrastructure).

## Escalation path

Three patterns, each appropriate at a different scale:

| Pattern | When to use | Trigger to escalate |
|---------|------------|-------------------|
| **Per-session file** (current) | Single-host, <50 concurrent sessions, consumers are single-session | Cross-session hook analysis becomes a frequent operation (e.g., `/maintain` or `/check` needs fleet-wide hook health) |
| **Centralized + session tag** | Cross-session queries needed, still single-host | Multi-host fleet (Grok + Codex + PI on different machines) OR token/cost attribution per hook needed |
| **OpenTelemetry tracing** | Multi-host, multi-agent, full distributed tracing | Agent observability investment is justified (token attribution, decision-graph tracing, stuck-loop detection) |

### Trigger 1: per-session → centralized

**When:** an operator or skill needs to query hook blocks across all
sessions (e.g., "show me every dead_zone block in the last hour across
the fleet").

**Why per-session files fail at this scale:** with 50+ session files,
scanning all of them is slow and fragile (filename globbing, concurrent
writes, stale sessions).

**Migration:** change filename from `hook-blocks-{session_id}.jsonl` to
`hook-blocks.jsonl`. Add `"session_id": session_id` to each record.
Readers filter by session_id when they need isolation. The data model
doesn't change — only the file layout and the filtering discipline.

### Trigger 2: centralized → OpenTelemetry

**When:** the fleet spans multiple hosts (Grok Build + Codex CLI + PI on
different machines), OR when token/cost attribution per hook is needed,
OR when the operator wants distributed-trace visualization (decision
graphs, parent-child spans across agents).

**Why centralized JSONL fails at this scale:** no cross-host aggregation,
no trace context propagation, no span hierarchy, no token attribution.

**Migration:** add `@opentelemetry/api` SDK to each hook. Replace the
JSONL write with a span emission. Configure an OTel collector + backend
(Jaeger or Langfuse self-hosted). The GenAI semantic conventions define
the span attributes (`gen_ai.operation.name`, `gen_ai.agent.name`,
`gen_ai.tool.name`, etc.).

Reference: OpenTelemetry GenAI Semantic Conventions SIG (Zylos research,
Feb 2026 — full instrumentation patterns for Node.js/TypeScript agent
systems with hierarchical span trees, tail sampling, and context
propagation).

## What this means for our workspace

- **`dead_zone_guard.py` is the reference implementation.** It extracts
  `sessionId` from the payload, writes a JSONL record before `sys.exit(2)`,
  and uses the same per-session filename pattern as the existing hooks.

- **Other PreToolUse hooks that exit 2 should adopt the same pattern.**
  The `_log_block()` function is generic — it takes session_id, hook_name,
  tool_name, file_path, exit_code, message. Any blocking hook can call it.

- **Consumers (`/why`, `/check`, `/close`) can read the session's block log**
  to answer "what hooks blocked in this session?" without scanning other
  sessions' files. The filename is deterministic:
  `~/.grok/hooks/state/hook-blocks-{session_id}.jsonl`.

- **GC:** per-session files should be cleaned up at session end
  (`quality_cleanup.py` already handles this pattern for other per-session
  files). Add `hook-blocks-*.jsonl` to its cleanup glob. See
  [[verification-state-tracking-content-identity-vs-temporal-proxies]] for
  the content-hash-based staleness pattern that could apply to block records
  if freshness tracking is needed.

## Falsifier

This pattern is wrong if:
- The operator consistently needs cross-session hook analysis (per-session
  files make this slow — escalate to centralized)
- Sessions start using worktrees that change the session-id propagation
  model (the payload's sessionId might not be available — verify)
- Grok Build changes its hook payload format (sessionId field renamed or
  removed — the hook fails open, which is correct)

## Receipts

- `~/.grok/hooks/scripts/dead_zone_guard.py:20-21` — `import time` + `from pathlib import Path` added
- `~/.grok/hooks/scripts/dead_zone_guard.py:109-131` — `_log_block()` function
- `~/.grok/hooks/scripts/dead_zone_guard.py:140` — `session_id = data.get("sessionId", "")`
- `~/.grok/hooks/scripts/dead_zone_guard.py:156-164` — dead-zone block path calls `_log_block()` before `sys.exit(2)`
- `~/.grok/hooks/scripts/dead_zone_guard.py:174-182` — root-block path calls `_log_block()` before `sys.exit(2)`
- Verified: test payload with `sessionId` + new file in `docs/designs/` → exit 2 + JSON log record written to `hook-blocks-{session_id}.jsonl`
- `$env:GROK_SESSION_ID` is empty on this host (verified: `Write-Host $env:GROK_SESSION_ID` → empty); session ID comes from hook payload stdin JSON
- [[multi-terminal-isolation-stale-data-immunity]] — the wiki concept documenting per-session isolation
- [[pipeline-session-scoping-each-layer-independently]] — each layer must independently scope
- Splunk "Observability Challenges in Multi Agentic Environments" (June 2026) — 4 observability categories
- Zylos "OpenTelemetry for AI Agents" (Feb 2026) — GenAI semantic conventions, instrumentation patterns

## Auto-related

- [[skill-graph]]
- [[opentelemetry-logging-patterns]]
- [[opentelemetry-structured-logging-patterns]]
- [[opentelemetry-logging]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]

