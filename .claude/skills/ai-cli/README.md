# ai-cli - Parallel Multi-LLM Command

Run qwen, gemini, codex, vibe, opencode, glm-4.7-flash in parallel and aggregate responses.

## Quick Start

```bash
# Basic query (runs 5-6 CLIs in parallel)
python "P:\.claude\skills\ai-cli\ai_cli.py" "what is 12 + 12?"

# With file context
python "P:\.claude\skills\ai-cli\ai_cli.py" "Review this plan" --context path/to/file.md

# Consensus view
python "P:\.claude\skills\ai-cli\ai_cli.py" "explain recursion" --aggregate
```

## Known Issues

### CRITICAL

| ID | Issue | Location | Status |
|----|-------|----------|--------|
| CRIT-001 | Undefined variable `latest` causes NameError in `--auto-context` | `ai_cli.py:436` | ✅ FIXED |

**Impact:** The `--auto-context` flag is completely broken and will crash with `NameError: name 'latest' is not defined`.

**Fix required:**
```python
# Line 430-440, add missing line:
def _get_auto_context() -> str:
    if not _SESSION_DIR.exists():
        return ""
    session_files = list(_SESSION_DIR.glob("*.jsonl"))
    if not session_files:
        return ""
    latest = max(session_files, key=lambda p: p.stat().st_mtime)  # ADD THIS LINE
    return _format_session_history(latest)
```

### HIGH

| ID | Issue | Location | Status |
|----|-------|----------|--------|
| HIGH-001 | `run_parallel_llm()` complexity 37 (exceeds threshold) | `ai_cli.py:671` | ✅ FIXED |
| HIGH-002 | No unit test coverage for security-critical functions | Entire module | OPEN |
| HIGH-003 | GLM API calls run sequentially instead of parallel (15s waste) | `ai_cli.py:671` | OPEN |
| HIGH-004 | File system stat() call storm (1s overhead) | `ai_cli.py:374` | OPEN |

### MEDIUM

| ID | Issue | Location | Status |
|----|-------|----------|--------|
| MED-001 | Duplicate function definitions (`_get_repo_root_for_lib` / `_get_repo_root`) | `ai_cli.py:24/83` | OPEN |
| MED-002 | Silent JSON parsing failures mask data corruption | `ai_cli.py:978-1096` | OPEN |
| MED-003 | Missing return type annotations on 3 functions | Various | OPEN |
| MED-004 | Command injection risk via shlex.quote | `ai_cli.py:599` | OPEN |

## Test Coverage

| Type | Coverage | Status |
|------|----------|--------|
| Unit tests | ~15% | Insufficient |
| Integration tests | 0% | Missing |
| E2E tests | 0% | Missing |
| Security tests | 0% | Missing |

**Test files:**
- `tests/test_complexity_characterization.py` - 44 characterization tests (passing)
- `tests/test_datetime_filename.py` - Datetime suffix tests

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.3.0 | 2025-01-27 | Refactored: extracted CLI parsers, complexity 10.07→8.29 |
| 1.2.0 | 2025-01-25 | Added datetime suffix to output filenames |
| 1.1.0 | Initial | Multi-LLM parallel execution |

## Setup

**Install external CLIs:**
```bash
npm install -g qwen-code gemini-cli opencode-ai @mistralai/vibe
pip install codex-cli
```

**Environment variables:**
- `CHUTES_API_KEY` - Required for opencode
- `ZAI_API_KEY` - Optional, enables glm-4.7-flash

## Options

| Option | Description |
|--------|-------------|
| `"<query>"` | Question or task (required, quoted) |
| `--context FILE` | File path to embed (RECOMMENDED) |
| `--summary` | Brief key answers only |
| `--aggregate` | Consensus view showing agreement/disagreement |
| `--complete` | Full raw outputs |
| `--diff` | Show differences between responses |
| `--output-format json` | Machine-readable JSON output |
| `--timeout N` | Max wait in seconds (default: auto-calculated) |
| `--qwen-only`, `--gemini-only`, etc. | Run specific CLI only |

## Validation Status

**Last validated:** 2026-01-27

**Pipeline result:** 🛑 **HALTED AT STAGE 3** (CRITICAL/HIGH findings)

See `P:\.claude\state\adversarial-*-ai-cli.json` for detailed reports.
