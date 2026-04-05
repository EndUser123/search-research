# Implementation Plan: CHS Usability Improvements

**TSK ID**: TSK-251230-NSE
**Date**: 2025-12-31
**ADF Assessment**: 7 improvements, total complexity tax ~8.0 (acceptable)

---

## Task Breakdown

### Phase 1: Foundation Features (Tax 1.00-1.06)

**1. Quick Copy Feature** [Tax: 1.00, 15 min]
- Add `--copy` flag to argument parser
- Implement `copy_to_clipboard()` function using pyperclip
- Format results for clipboard (plain text with timestamps)
- Add success/error message
- Handle ImportError when pyperclip unavailable

**2. Result Export** [Tax: 1.06, 20 min]
- Add `--export {json,markdown,txt}` flag
- Add `--output <path>` flag for custom filename
- Implement `export_results()` function
  - JSON: serialize results with metadata
  - Markdown: format as table with code blocks
  - TXT: plain text with separators
- Auto-generate filename: `chs-export-{timestamp}.{ext}`

**3. Timestamp Grouping** [Tax: 1.04, 15 min]
- Add `--group-by {day,session}` flag
- Implement `group_results_by_day()` function
- Modify display code to show group headers
- Integrate with existing `format_timestamp_ms()`

### Phase 2: Content Enhancement (Tax 1.125)

**4. Code Block Extraction** [Tax: 1.125, 25 min]
- Add `--extract-code` flag
- Implement `extract_code_blocks()` using regex
- Display code blocks with language labels
- Optional: `--code-only` to suppress non-code results

### Phase 3: Search Features (Tax 1.50-1.06)

**5. Search within Results** [Tax: 1.06, 20 min]
- Detect stdin input (`sys.stdin.isatty()`)
- Add support for chaining searches
- Read previous results from stdin
- Filter results based on new query

**6. Fuzzy Matching** [Tax: 1.50, 30 min]
- Add `--fuzzy` flag
- Add `--fuzzy-threshold N` flag (default: 80)
- Implement using `rapidfuzz.process.extract`
- Display similarity scores in results
- Handle ImportError when rapidfuzz unavailable

### Phase 4: Integration (Tax 1.50)

**7. CLI Command Integration** [Tax: 1.50, 30 min]
- Create `.claude/commands/chs.md`
- Document all flags with examples
- Add to command registry
- Test invocation

---

## Dependencies

```
Task 2 (Export) depends on: Task 1 (shares result formatting)
Task 3 (Grouping) depends on: Task 2 (shares display logic)
Task 4 (Code Extraction) depends on: Task 3 (display integration)
Task 5 (Search within) depends on: Task 4 (result structure)
Task 6 (Fuzzy) is independent of others
Task 7 (CLI) depends on: All previous (documentation)
```

---

## Implementation Strategy

### File Modifications

**Primary File**: `P:\__csf.nip\src\modules\analysis\chat_search\src\chat_history_search.py`

1. Add new argument flags to `search_parser` (around line 2188)
2. Add helper functions after `format_timestamp_ms()` (around line 127)
3. Modify result display in `main()` to use new features

**New File**: `.claude/commands/chs.md`
- CLI command documentation

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| pyperclip not available | Low | Graceful degradation, show message |
| rapidfuzz not available | Low | Skip fuzzy search, show message |
| Breaking existing behavior | Medium | All new flags are opt-in |
| Performance regression | Low | New features are display-only |

---

## Success Criteria

- [ ] All 7 features implemented
- [ ] Existing tests pass
- [ ] New features tested manually
- [ ] CLI command works
- [ ] Documentation complete
- [ ] No performance regression

---

## Testing Strategy

**Manual Testing**:
```bash
# Quick copy
python -m chat_history_search search "API" --copy

# Export JSON
python -m chat_history_search search "error" --export json

# Code extraction
python -m chat_history_search search "function" --extract-code

# Fuzzy matching
python -m chat_history_search search "authentcation" --fuzzy

# CLI command
/chs "API design" --export markdown
```

---

## Out of Scope (Explicitly Excluded)

- Conversation Threading (TAX: 2.0) - use `--context N` instead
- Saved Searches (TAX: 2.5) - use shell aliases instead
- ML-based Result Ranking (TAX: 1.75+) - deferred
