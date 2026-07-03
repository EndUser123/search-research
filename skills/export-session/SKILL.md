---
name: export-session
description: Export the current (or specified) Claude Code session chain to a markdown file. Trigger when the user says "export session", "export conversation", "export chat", "export transcript", "save session", "dump session", or types /export-session. Produces a cross-terminal, cross-compaction session-chain markdown export for analysis consumers (/debrief, /gto, /learn) or archival.
enforcement: advisory
workflow_steps:
  - Resolve target session (current session unless --session-id is given)
  - Invoke chs_cli.py --export with the chosen fidelity and bounds
  - Report the export path and metadata; honor the context-safety recommendation
---

# Export Session (/export-session)

Thin, task-centric entry point over the `/chs` export pipeline. Exports the full
**session chain** — every transcript linked to the session across all terminals and
compactions — to a single markdown file.

`/chs export` is the in-skill alias for the same pipeline; both call
`chs_cli.py --export`. `/export-session` exists because "export this session" is the
dominant mental model and leading with the verb is easier to recall than
`<acronym> <subcommand>`.

## Exact CLI mapping

```bash
python "P:/packages/.claude-marketplace/plugins/search-research/skills/chs/scripts/chs_cli.py" \
  --export [--session-id <id>] [--output <path>] [--max-sessions N] \
  [--fidelity {context-safe,analysis}]
```

## Defaults (no flags needed)

- **Fidelity:** `analysis` (default) — full tool results with
  `tool_use`↔`tool_result` id back-refs, uncapped thinking, per-entry ISO
  timestamps, per-session git branch, export-time HEAD sha, and compaction-boundary
  markers. Use `--fidelity context-safe` for a compact, byte-identical-to-legacy
  export when reading the file directly into context.
- **Session:** the current session when `--session-id` is omitted.
- **Output:** `~/.claude/exports/chain_<timestamp>.md` when `--output` is omitted.
- **Max sessions:** the 30 most-recent transcripts in the chain (newest kept,
  oldest silently dropped). Raise with `--max-sessions N` for very long-lived
  sessions.

## Cross-terminal + session resume

The chain is reconstructed from `P:/.claude/.artifacts/session_registry.jsonl`
(written by the PreCompact hook), aggregated by `session_id` across **all**
terminals. Resumes and compactions are all included — every transcript segment in
the session's lifetime is reassembled, deduplicated by transcript path.

## Context protection

The CLI returns JSON metadata with `context_safe` and `recommendation` fields.

**Default behavior:** report the export path and metadata. Do NOT read the file into
context unless `context_safe` is true. When `recommendation` is
`delegate_to_subagent`, spawn a subagent to read and summarize rather than loading
the file into main context.

| `recommendation` | Action |
|---|---|
| `read_file` | Safe to read into context (<20K tokens) |
| `delegate_to_subagent` | Spawn a subagent to read, summarize, and return key findings |
| `export_is_too_large_use_filters` | Re-export with `--fidelity context-safe` or a targeted `--session-id` |

## Common invocations

```bash
# Default — analysis export of the current session chain
/export-session

# Compact export for direct in-context reading
/export-session --fidelity context-safe

# Export a specific session chain
/export-session --session-id <uuid>

# Bounded for very long sessions
/export-session --max-sessions 5
```

## Provenance note on sha

Transcripts do not record `gitSha` per session (the field is always null). The
`analysis` preset stamps the **export-time** `git rev-parse HEAD` of the working
directory, labeled as such — it is not the session-time commit. Per-session
`gitBranch` is authentic. If a future consumer needs true session-time sha, that
must come from a hook recording it at session start, not from the export.
