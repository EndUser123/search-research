# Specification: CHS Usability Improvements

## Goal
Implement 7 low-complexity improvements to Chat History Search (CHS) to enhance usability, productivity, and developer experience.

## Why
- **User Experience**: Current CHS lacks common quality-of-life features (copy, export, code extraction)
- **Productivity**: Users spend extra time manually formatting/exporting results
- **Discoverability**: No dedicated CLI command; users must invoke via Python module
- **Search Quality**: No fuzzy matching for typos; no search-within-results capability

## What

### Functional Requirements

**FR-001: Quick Copy Feature**
- Add `--copy` flag to copy search results to clipboard
- Use `pyperclip` library (no additional dependencies if available)
- Copy formatted text with timestamps and content

**FR-002: Result Export**
- Add `--export <format>` flag supporting: `json`, `markdown`, `txt`
- Export includes: query, timestamp, result count, results with metadata
- Default output filename: `chs-export-{timestamp}.{ext}`

**FR-003: Code Block Extraction**
- Extract and display code blocks separately from search results
- Add `--extract-code` flag to show only code blocks
- Parse markdown code blocks (```language ... ```)
- Display with language labels

**FR-004: Timestamp Grouping**
- Group results by day/session in display
- Add `--group-by {day,session}` flag
- Show group headers with date/session info

**FR-005: Search within Results**
- Allow piping/ chaining searches
- Read from stdin for query chaining
- Example: `chs "API" | chs "error"`

**FR-006: Fuzzy Matching**
- Add `--fuzzy` flag for approximate string matching
- Use `rapidfuzz` library (well-maintained, fast)
- Default edit distance threshold: 2
- Add `--fuzzy-threshold N` for custom distance

**FR-007: CLI Command Integration**
- Create `/chs` CLI command for easy access
- Support all existing flags via new command
- Add help text and examples

## Implementation Order

1. Quick Copy (TAX: 1.00)
2. Result Export (TAX: 1.06)
3. Timestamp Grouping (TAX: 1.04)
4. Code Block Extraction (TAX: 1.125)
5. CLI Command (TAX: 1.50)
6. Fuzzy Matching (TAX: 1.50 simplified)
7. Search within Results (TAX: 1.06)

## Out of Scope

- Conversation Threading (TAX: 2.0) - use `--context N` instead
- Saved Searches (TAX: 2.5) - use shell aliases instead
- Result Ranking with ML feedback (TAX: 1.75) - too complex for now
