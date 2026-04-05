---
name: refactor
description: Safe refactoring with automatic characterization test generation
usage: /refactor <function_name> [--cc <threshold>]
invokes: tdd
examples:
  - /refactor vtt_to_db
  - /refactor get_playlist_data --cc 30
  - /refactor _download_handle_direct
---

# /refactor - Safe Refactoring Command

Invokes the `tdd` skill to safely refactor code with characterization tests.

## Usage

```
/refactor <function_name> [--cc <threshold>]
```

- `function_name`: Name of the function to refactor
- `--cc <threshold>`: Only refactor if CC exceeds this threshold (default: 15)

## See Also

- `P:/.claude/skills/tdd/SKILL.md` - Full TDD workflow
- `tests/test_refactor_safety.py` - Characterization tests
