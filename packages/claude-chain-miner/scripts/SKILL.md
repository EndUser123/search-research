---
name: chain-mine
description: Walk, export, and mine post-compact Claude Code session chains via handoff files
version: 0.1.0
enforcement: advisory
workflow_steps:
  - Walk the handoff-file chain for a given slug
  - Export each session via chs_cli.py --export
  - Parse exported markdown or raw JSONL for patterns
  - Return mined results (pattern-based or LLM-based)
---

# Chain Mine

Walk, export, and mine post-compact session chains.

## Usage

```bash
/chain-mine --walk --slug P--
/chain-mine --export --slug P--
/chain-mine --mine "webhook issues" --slug P--
```

## As a Python library

```python
from scripts.walker import get_chain_for_slug, get_current_slug

slug = get_current_slug()  # e.g. "p----Users----brsth"
chain, origin = get_chain_for_slug(slug)

for entry in chain:
    print(entry.session_id, entry.transcript_path)
```
