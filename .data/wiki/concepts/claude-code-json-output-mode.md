---
title: "Claude Code JSON Output Mode"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, claude]
summary: >
  Claude Code JSON Output Mode is a non-interactive invocation shape of Claude Code (`claude -p`) in which responses, tool invocations, and results are emitted as newline-delimited JSON (JSONL) events on stdout, enabling programmatic pipelines, headless automation, hooks, and downstream tools to consu
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 3c6d83d9-9945-43d7-a6a0-d8a446ce9d3a" (ext-Agentic-Platforms, synced 2026-08-09)
  - "NotebookLM source 2f1842cd-0291-4f7f-9763-7c163df37ba1" (OpenHands-OpenHands.md, synced 2026-08-09)
  - "NotebookLM source 3907f045-965c-4775-a724-8449ac120d6a" (affaan-m-everything-claude-code-part-2.md, synced 2026-08-09)
  - "NotebookLM source 3aa28bb6-8887-405d-a8fa-3d003ccd4131" (PrefectHQ-fastmcp-part-1.md, synced 2026-08-09)
  - "NotebookLM source 4f38480a-a1b3-48f0-917e-56733ee9aa93" (affaan-m-everything-claude-code-part-1.md, synced 2026-08-09)
  - "NotebookLM source 58923561-8a3f-4f2b-86d5-7b92c878fcc0" (ComposioHQ_awesome-claude-skills_part-002.md, synced 2026-08-09)
  - "NotebookLM source 6b5e26d6-2017-41da-bc06-d8e0490088f2" (affaan-m-everything-claude-code-part-5.md, synced 2026-08-09)
  - "NotebookLM source 7d6a98e2-67f0-41d8-96ba-0ab5117bc072" (OpenBMB-RepoAgent.md, synced 2026-08-09)
  - "NotebookLM source 899cdffa-e5a0-4270-8114-dce3dcd1d6d1" (VoltAgent-voltagent-part-2.md, synced 2026-08-09)
  - "NotebookLM source 95e220c4-f0a5-4d8b-bb6d-b7dd6ba978b0" (assafelovic-gpt-researcher-part-2.md, synced 2026-08-09)
  - "NotebookLM source a1a4235c-7696-4e93-b91b-a02dd347fe50" (ComposioHQ_awesome-claude-skills_part-001.md, synced 2026-08-09)
  - "NotebookLM source ab8da581-3d9a-447c-bc2f-64ce342557c5" (assafelovic-gpt-researcher-part-1.md, synced 2026-08-09)
  - "NotebookLM source bc069a6a-440b-491f-80a2-5a0de384b965" (VoltAgent-voltagent-part-1.md, synced 2026-08-09)
  - "NotebookLM source be38af1a-0bbf-4f88-8751-30ef0ea0982b" (affaan-m-everything-claude-code-part-4.md, synced 2026-08-09)
  - "NotebookLM source cf639a80-3551-4d88-b5d1-3c2379f6230e" (affaan-m-everything-claude-code-part-3.md, synced 2026-08-09)
  - "NotebookLM source e5ccd4bb-2e83-419d-8455-a4ac76a79c32" (PrefectHQ-fastmcp-part-2.md, synced 2026-08-09)
  - "NotebookLM source ecaa5406-fba9-4fd1-93eb-0eddd51e97a9" (ComposioHQ_awesome-claude-skills_part-003.md, synced 2026-08-09)
  - "NotebookLM source f291d5bc-4a82-4290-8df2-c6d9feb4e47f" (VoltAgent-voltagent-part-3.md, synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: claude-code-json-output-mode
    - level: notebook
      id: 3c6d83d9-9945-43d7-a6a0-d8a446ce9d3a
      title: ext-Agentic-Platforms
      url: https://notebooklm.google.com/notebook/3c6d83d9-9945-43d7-a6a0-d8a446ce9d3a
    - level: cluster
      id: 0
      name: claude-code-json
relations:
  - target: wiki/concepts/claude-code-stream-json-output.md
    type: related
  - target: wiki/concepts/claude-code-hooks-(pretooluse/posttooluse).md
    type: related
  - target: wiki/concepts/claude-code-mcp-server-configuration.md
    type: related
---

# Claude Code JSON Output Mode

## Decision context

**Definition:** Claude Code JSON Output Mode is a non-interactive invocation shape of Claude Code (`claude -p`) in which responses, tool invocations, and results are emitted as newline-delimited JSON (JSONL) events on stdout, enabling programmatic pipelines, headless automation, hooks, and downstream tools to consume structured data instead of free-form text.

Synthesized from **17 contributing transcripts** in NotebookLM notebook *ext-Agentic-Platforms*, clustered into the "claude-code-json" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Activation uses the CLI flag `--output-format json` (with `--verbose` for per-turn usage blocks) or `--output-format stream-json` for live event streaming; print mode is enabled with `claude -p "<prompt>"`
- Each stdout line is one JSON object with a top-level `type` (`system`, `user`, `assistant`, `result`, `error`), an optional `subtype` (`init`, `tool_use`, `tool_result`, `text`, `success`, `error_max_turns`), `session_id`, `cwd`, `timestamp`, and a `message` payload
- `assistant`/`user` message payloads carry `content` arrays of typed blocks: `{type: "text", text}`, `{type: "tool_use", id, name, input}`, and `{type: "tool_result", tool_use_id, content, is_error}`
- `system/init` events announce available `tools`, `model`, `permission_mode`, and the `session_id`; consumers cache tool schemas from this event rather than re-deriving them
- `result` events signal end-of-turn with `subtype: "success"` or `"error_max_turns"`, plus aggregated `cost_usd`, `duration_ms`, `num_turns`, and token usage; non-streaming invocation exits with code 0 on success, non-zero on failure
- `--verbose` adds per-turn `usage` blocks with `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens` for cost tracking
- Hooks receive the same JSON shape on stdin (with `session_id`, `transcript_path`, `cwd`, `tool_name`, `tool_input`, optional `tool_output`) and must echo valid JSON to stdout to remain non-blocking
- The transcript is persisted to `transcript_path` announced in `system/init`; session managers and cost trackers read this file directly rather than re-querying the API
- Parser pattern: split stdout on newlines, `JSON.parse` each line, dispatch on `event.type` then `event.subtype`, accumulate `tool_use`/`tool_result` pairs by id, and treat the final `result` event as the terminator
- Antipatterns documented in sources: parsing stdout as a single JSON blob (it is JSONL), assuming `content` is always a string, ignoring `tool_result.is_error`, treating `result.subtype === "error_max_turns"` as success

## Verifiable values

| Name | Value |
|---|---|
| default context window (Claude Sonnet) | `~200k tokens` |
| recommended MCP cap per project | `under 10 enabled` |
| recommended active tools cap | `under 80` |
| context shrinkage with heavy MCP usage | `down to ~70k tokens` |
| MAX_THINKING_TOKENS default | `31,999` |
| MAX_THINKING_TOKENS recommended cap | `10,000` |
| CLAUDE_AUTOCOMPACT_PCT_OVERRIDE default | `95` |
| CLAUDE_AUTOCOMPACT_PCT_OVERRIDE recommended | `50` |
| strategic-compact tool-call threshold | `50 (then every 25)` |
| TDD coverage threshold | `80% minimum (100% for financial/auth/security-critical)` |
| hook input schema fields | `tool_name, tool_input (command|file_path|old_string|new_string|content), tool_output (PostToolUse only)` |
| exit code 0 semantics | `allow tool call` |
| exit code 2 semantics | `block tool call (PreToolUse only)` |
| blocking PreToolUse/Stop hook latency target | `under 200ms` |
| async hook timeout ceiling | `30s` |

## Related concepts

- claude-code-stream-json-output — Claude Code stream-json output
- [[claude-code-hooks-(pretooluse/posttooluse)]] — Claude Code hooks (PreToolUse/PostToolUse)
- [[claude-code-mcp-server-configuration]] — Claude Code MCP server configuration
- [[claude-code-session-persistence-(transcript_path)]] — Claude Code session persistence (transcript_path)
- [[claude-code-headless-automation-(`claude--p`)]] — Claude Code headless automation (`claude -p`)
- claude-code-setting.json-and-plugin.json — Claude Code setting.json and plugin.json

## Citations (from contributing transcripts)

- **Claim:** Claude Code JSON output is structured, line-delimited JSON (JSONL) — one JSON object per line — used to stream events like tool invocations, results, and assistant messages for programmatic consumption.
  - Source: Part 12 of transcripts
  - Context: Claude Code JSON output is structured, line-delimited JSON (JSONL) — one JSON object per line — used to stream events like tool invocations, results, and assistant messages for programmatic consumption.
- **Claim:** The recommended way to enable JSON output is the `--output-format json` flag (with `--verbose` for full event detail), or piping `stream-json` / receiving `assistant` / `user` / `result` messages on stdout.
  - Source: Part 12 of transcripts
  - Context: The recommended way to enable JSON output is the `--output-format json` flag (with `--verbose` for full event detail), or piping `stream-json` / receiving `assistant` / `user` / `result` messages on stdout.
- **Claim:** A typical JSONL event has top-level fields: `type` (e.g., "system", "user", "assistant", "result", "error"), `subtype` (e.g., "init", "tool_use", "tool_result", "text"), `session_id`, `cwd`, `timestamp`, and a `message` payload.
  - Source: Part 12 of transcripts
  - Context: A typical JSONL event has top-level fields: `type` (e.g., "system", "user", "assistant", "result", "error"), `subtype` (e.g., "init", "tool_use", "tool_result", "text"), `session_id`, `cwd`, `timestamp`, and a `message` payload.
- **Claim:** `tool_result` blocks carry the tool output verbatim (often wrapped in `<tool_use_error>` tags when failing); parse the inner string rather than assuming JSON.
  - Source: Part 12 of transcripts
  - Context: `tool_result` blocks carry the tool output verbatim (often wrapped in `<tool_use_error>` tags when failing); parse the inner string rather than assuming JSON.
- **Claim:** Use `--verbose` to surface per-turn `usage` blocks with `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens` — essential for cost tracking.
  - Source: Part 12 of transcripts
  - Context: Use `--verbose` to surface per-turn `usage` blocks with `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens` — essential for cost tracking.
- **Claim:** For non-interactive/headless mode use `claude -p "prompt"` (print mode), which still streams JSONL when combined with `--output-format json` and exits with code 0 on success / non-zero on failure.
  - Source: Part 12 of transcripts
  - Context: For non-interactive/headless mode use `claude -p "prompt"` (print mode), which still streams JSONL when combined with `--output-format json` and exits with code 0 on success / non-zero on failure.
- **Claim:** Hooks receive the same JSON shape on stdin (with `session_id`, `transcript_path`, `cwd`, `tool_name`, `tool_input`) and must echo valid JSON to stdout to remain non-blocking.
  - Source: Part 12 of transcripts
  - Context: Hooks receive the same JSON shape on stdin (with `session_id`, `transcript_path`, `cwd`, `tool_name`, `tool_input`) and must echo valid JSON to stdout to remain non-blocking.
- **Claim:** Pair `--output-format stream-json` with stdin prompts to build interactive TUIs or pipelines (e.g., `claude -p --output-format stream-json | jq ...`); the stream emits newline-delimited JSON objects as events occur.
  - Source: Part 12 of transcripts
  - Context: Pair `--output-format stream-json` with stdin prompts to build interactive TUIs or pipelines (e.g., `claude -p --output-format stream-json | jq ...`); the stream emits newline-delimited JSON objects as events occur.
- **Claim:** The transcript JSONL is persisted to a path announced in the `system/init` event (`transcript_path`); downstream tools like session managers and cost trackers read this file directly rather than re-querying the API.
  - Source: Part 12 of transcripts
  - Context: The transcript JSONL is persisted to a path announced in the `system/init` event (`transcript_path`); downstream tools like session managers and cost trackers read this file directly rather than re-querying the API.
- **Claim:** Avoid these antipatterns: parsing stdout as a single JSON blob (it's JSONL), assuming `content` is always a string (it's an array of blocks), ignoring `tool_result.is_error`, or treating `result.subtype === "error_max_turns"` as success.
  - Source: Part 12 of transcripts
  - Context: Avoid these antipatterns: parsing stdout as a single JSON blob (it's JSONL), assuming `content` is always a string (it's an array of blocks), ignoring `tool_result.is_error`, or treating `result.subtype === "error_max_turns"` as success.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `3c6d83d9-9945-43d7-a6a0-d8a446ce9d3a`
(cluster `claude-code-json`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: wiki-yt/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [ext-Agentic-Platforms](https://notebooklm.google.com/notebook/3c6d83d9-9945-43d7-a6a0-d8a446ce9d3a)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
