# ClaudeChainMiner

Post-compact session chain walker, exporter, and miner for Claude Code.

## The Problem

After session compaction, transcript `.jsonl` files lose their message content and become `file-history-snapshot` format. This breaks `/recap` and session chain reconstruction — the traditional approaches (scanning `sessions-index.json` or `history.jsonl`) no longer find usable content.

## The Solution

ClaudeChainMiner walks the **handoff-file chain** instead. Handoff files are written atomically by the PreCompact hook at compaction time, before the transcript is compacted. They survive compaction and preserve the `prior_transcript_path` link.

## Installation

```bash
cd P://packages/claude-chain-miner
pip install -e .
```

## CLI Usage

```bash
# Walk and print the chain
claude-chain-mine --walk --slug P--

# Walk from a deterministic Claude session anchor
claude-chain-mine --walk --slug P-- --session-id <uuid> --transcript-path <path>

# Export all sessions in the chain
claude-chain-mine --export --slug P--

# Mine the chain with a query (pattern-based, no API key needed)
claude-chain-mine --mine "webhook issues" --slug P--

# Mine with LLM synthesis (requires ANTHROPIC_API_KEY)
claude-chain-mine --mine "what problems did we solve" --slug P-- --use-llm

# List all sessions in the chain
claude-chain-mine --list --slug P--
```

## Python API

```python
from scripts.walker import get_chain_for_slug, get_current_slug
from scripts.exporter import export_chain, merge_exports
from scripts.miner import mine_transcript_chain

slug = get_current_slug()
chain, origin = get_chain_for_slug(slug)

# Export the chain
exported = export_chain([e.session_id for e in chain])

# Mine it
result = mine_transcript_chain([e.transcript_path for e in chain], query="webhook issues")
```

## Architecture

```
scripts/
  walker.py    # Handoff chain traversal + slug resolution
  exporter.py  # chscli integration + JSONL parsing
  miner.py     # Pattern + LLM extraction
```

## Key Features

- **Compact-proof**: Handoff files survive compaction and preserve prior_transcript_path
- **Self-match fix**: Detects and breaks loops from the `prior_transcript_path=N/A` bug
- **Terminal-safe**: Slug derived from cwd ensures isolation across terminals
- **Dual-path search**: Handles both `P://.claude/state/handoff/` and `~/.claude/state/handoff/`
- **Deterministic anchors**: Accepts explicit `session_id` and `transcript_path` when Claude Code provides them
- **Robust fallback chain**: Uses transcript-path env vars, session-id env vars, then `sessions.json` before mtime guessing
- **chscli integration**: Reuses chs_cli.py's file-history-snapshot parser instead of reinventing it

## Test Data

The file `C:\Users\brsth\AppData\Local\Temp\chs_chain_export.json` contains the exported chain from session `59ba4da6-8417-4c06-9dc8-f5647591ad3e` (root session, chain length = 1).
