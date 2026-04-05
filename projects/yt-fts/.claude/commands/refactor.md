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

- `docs/REFACTORING.md` - Complete refactoring best practices
- `docs/TEST_PATTERNS.md` - Test patterns and conventions
- `P:/.claude/skills/tdd-cycle/SKILL.md` - Full TDD workflow

## Workflow

1. **Check CC**: Use `/complexity <module>` to verify function exceeds threshold
2. **Write Characterization Tests**: Capture current behavior in `tests/yt_fts/<module>/test_<name>_characterization.py`
3. **Extract**: Create new module/class with extracted logic
4. **Verify**: Run tests to confirm behavior preserved
5. **Code Flow**: Use `grep -n "pattern" file.py` to verify execution path

## Example

```
/refactor BatchDownloader._format_db_stats
```

Creates characterization tests, extracts ChannelStatisticsManager class, verifies all tests pass.
