# CHS Command Reference

## Basic Search

```bash
/chs "query"                          # Basic search
/chs "authentication" --limit 20      # Limit results
/chs "migration" --since "7 days ago" # Date filter
/chs "migration" --until "2025-01-01" # Until date
/chs "error" --exact                  # Exact match
```

## Filter Options

```bash
# Workspace filters
/chs "deploy" --workspace tiny-vacation
/chs "api" --workspace-alias frontend

# Tool filters
/chs --tool Edit --file "*.py"
/chs --tool Bash --since "today"

# Branch filters
/chs "feature" --branch "main"
/chs "bugfix" --branch "fix/*"

# Content filters
/chs --exclude-thinking               # Exclude thinking blocks
/chs --include-tool-results           # Include tool execution results
```

## Output Options

```bash
# Detail levels
/chs "query" --depth summary          # Lightweight index only
/chs "query" --depth full             # Complete content
/chs "query" --depth auto             # Auto-detect (default)

# Context preview
/chs show <session-id> --context 10

# Summarization modes
/chs "query" --mode documentation
/chs "query" --mode short-memory
/chs "query" --mode changelog
/chs "query" --mode debug-postmortem
/chs "query" --mode onboarding

# Output formats
/chs "query" --format json            # Machine-readable
/chs "query" --format markdown        # Formatted markdown
```

## Session Management

```bash
# Show specific session
/chs show <session-id>
/chs show <session-id> --max-messages 100
/chs show <session-id> --json          # JSON output

# List recent sessions
/chs list --limit 20
/chs list --workspace tiny-vacation
/chs list --since "yesterday"

# Statistics
/chs stats
/chs stats --workspace tiny-vacation
```

## Advanced Options

```bash
# Search stages
/chs "query" --stage 1                # Index-only (fast)
/chs "query" --stage 2                # Deep scan
/chs "query" --stage auto             # Auto-select

# Rebuild index
/chs --reindex                        # Rebuild search index

# Save search results to file
/chs "query" --output results.json    # Save to file
/chs "query" --clipboard              # Copy to clipboard
```

## Session Chain Export

Export the full conversation history for the current session chain (all sessions
linked via handoff files) to a single readable markdown file.

The CLI returns JSON metadata with size estimates and a `recommendation` field:

```json
{
  "path": "~/.claude/exports/chain_20260527_143000.md",
  "session_count": 5,
  "file_size_kb": 42.3,
  "estimated_tokens": 10800,
  "context_safe": true,
  "recommendation": "read_file"
}
```

| recommendation | Action |
|---|---|
| `read_file` | Safe to read into context (<20K tokens) |
| `delegate_to_subagent` | Spawn subagent to summarize (20-100K tokens) |
| `export_is_too_large_use_filters` | Re-export with filters (>100K tokens) |

### Fidelity presets

`--fidelity` selects a bundle of rendering knobs. The default `context-safe` is
byte-identical to the legacy export. `analysis` is the rich mode for consumers
that need full signal (/debrief, /gto, /learn).

| Preset | Thinking | Tool calls/results | Timestamps | Branch | HEAD sha | Compaction |
|---|---|---|---|---|---|---|
| `context-safe` (default) | capped 300 chars | off | no | no | no | no |
| `analysis` | uncapped | full, with `tool_use.id`↔`tool_result.tool_use_id` back-refs | per-entry ISO | per-session | export-time | markers |

**Provenance note on sha:** transcripts do not record `gitSha` per session (the
field is always null). The `analysis` preset stamps the **export-time** `git
rev-parse HEAD` of the working directory, labeled as such — it is not the
session-time commit. Per-session `gitBranch` IS recoverable and is rendered
authentically.

Legacy flags still work and map onto the `context-safe` preset:
`--exclude-thinking` forces thinking off; `--include-tool-results` upgrades tool
rendering to the legacy truncated (400-char, no id) form. Passing either with
`--fidelity analysis` overrides that preset on the corresponding knob.

```bash
# Default export — context-safe, byte-identical to legacy
/chs --export

# Rich export for analysis consumers (full tool results, timestamps, branch, sha)
/chs --export --fidelity analysis

# Bounded rich export (limit chain length for context safety)
/chs --export --fidelity analysis --max-sessions 5

# Export a specific session chain
/chs --export --session-id <uuid>

# Save to a custom path (default: ~/.claude/exports/chain_<timestamp>.md)
/chs --export --output ~/my-chain.md
```

Output format: Markdown with one `## Session N` section per transcript,
messages formatted as `**User:**` / `**Assistant:**` blocks. In `analysis`
mode, each entry is prefixed with its ISO timestamp, `tool_use`/`tool_result`
pairs are linked by id, and `compact_boundary`/`away_summary` system entries
render as `### Compaction Boundary` / `### Away Summary` sections.
