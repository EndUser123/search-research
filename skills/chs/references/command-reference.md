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

```bash
# Export current session's chain (bounded for context safety)
/chs --export --max-sessions 5 --exclude-thinking

# Export a specific session chain
/chs --export --session-id <uuid>

# Save to a custom path (default: ~/.claude/exports/chain_<timestamp>.md)
/chs --export --output ~/my-chain.md

# Filter content in the export
/chs --export --exclude-thinking          # Omit thinking blocks
/chs --export --include-tool-results      # Include tool calls and results
```

Output format: Markdown with one `## Session N` section per transcript,
messages formatted as `**User:**` / `**Assistant:**` blocks.
