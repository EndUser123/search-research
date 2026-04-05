# Architecture Decision: Hook StdErr Preventive Measures

**Date:** 2026-03-07
**Template:** fast.md (LOW complexity, Generic domain)
**Query:** What's the optimal way to implement this for maximum ongoing value?

---

## Decision Statement

Implement a 3-phase preventive approach prioritizing **documentation first** (fast knowledge transfer), then **process automation** (pre-commit hooks), then **developer tools** (CLI commands). This sequence maximizes value by preventing regression immediately while building long-term guardrails.

---

## Options

### Option A: Documentation → Pre-commit → Tools

**Pro:**
- Immediate regression prevention
- Knowledge shared to team/user quickly
- Phased approach allows course correction

**Con:**
- Documentation requires time investment upfront

**Differs on:** Phased approach vs. all-at-once

### Option B: All-at-once (simultaneous implementation)

**Pro:**
- Complete solution delivered in one batch

**Con:**
- Delayed value delivery
- Higher risk of incomplete implementation

**Differs on:** Implementation sequencing

### Option C: Tools-first approach

**Pro:**
- Interactive tools available immediately

**Con:**
- No regression prevention until tools are used/adopted

**Differs on:** Tool priority vs. process priority

---

## Recommendation

**Option A** is optimal because:

1. **Documentation update** (30 min) → Immediately prevents regression via knowledge
2. **Pre-commit hook** (1 hour) → Blocks violations at commit time
3. **CLI tools** (2-3 hours) → Accelerates development workflow

This sequence matches the **precedence principle**: **knowledge → process → tools**. Documentation prevents the mistake, the hook enforces the rule, and tools make compliance easy.

---

## Implementation

### Phase 1: Documentation Updates (Immediate Value - 30 min)

#### 1. Update bugfixes.md (10 min)

Add to `C:/Users/brsth/.claude/projects/P--/memory/bugfixes.md`:

```markdown
## Hook StdErr Anti-Pattern (2026-03-07)

### Problem
Claude Code treats ANY stderr output from hooks as "hook error" message,
even when the hook succeeds. This causes false error messages after every
tool operation.

### Root Cause
Direct `print(..., file=sys.stderr)` calls in PostToolUse hooks trigger
Claude Code's error detection.

### Solution Pattern
Replace stderr writes with Python logging framework:

```python
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
log_file = HOOKS_DIR / "logs" / "hook_errors.jsonl"

# Inside error handling:
try:
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_record) + "\n")
except (OSError, IOError):
    pass  # Best-effort logging, never block
```

### Detection
Run test: `pytest P:/.claude/hooks/tests/test_no_stderr_in_hooks.py`

### Prevention
Pre-commit hook scans for `print\(.*file=sys\.stderr\)` pattern in Python files.
```

#### 2. Update CLAUDE.md hooks section (15 min)

Add to `P:/.claude/hooks/CLAUDE.md`:

```markdown
### Logging Best Practices

**Rule**: Hooks MUST NOT write to stderr. Claude Code treats stderr as error.

**Correct Pattern**:
```python
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
# File-based logging for diagnostics
```

**Anti-Pattern**:
```python
print("Error occurred", file=sys.stderr)  # ❌ TRIGGERS FALSE ERROR
```

**Debug Mode**: Use stdout for debug output when environment flag set:
```python
if ROUTER_DEBUG:
    print("Debug info", file=sys.stdout)  # ✅ OK
```
```

#### 3. Create hook development guide (5 min)

Create `P:/.claude/hooks/docs/development_guide.md`:

```markdown
# Hook Development Guide

## Hook Development Checklist

Before committing a new hook:

- [ ] No `print(..., file=sys.stderr)` anywhere in hook
- [ ] Use `logging` module with `NullHandler` for debug output
- [ ] File-based logging to `hooks/logs/*.jsonl` for errors
- [ ] Test with `pytest tests/test_no_stderr_in_hooks.py`
- [ ] Verify no "hook error" messages in Claude Code after tool operations
```

---

### Phase 2: Process Automation (Regression Prevention - 1 hour)

#### 4. Add pre-commit stderr scan (1 hour)

Append to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# StdErr scan for Python hooks
python_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)
if [ -n "$python_files" ]; then
    for file in $python_files; do
        # Skip comments
        if grep -v '^\s*#' "$file" | grep -q 'print(.*file=sys\.stderr)'; then
            echo "⛔ STDERR_WRITE_DETECTED in $file"
            echo "Hooks must not write to stderr. Use logging module instead."
            echo "See: P:/.claude/hooks/docs/development_guide.md"
            exit 1
        fi
    done
fi
```

---

### Phase 3: Developer Tools (Workflow Acceleration - 2 hours)

#### 5. Implement /hook-scan command (1 hour)

Create `P:/.claude/commands/hook_scan.py`:

```python
#!/usr/bin/env python3
"""Scan all hooks for stderr writes."""
import re
import sys
from pathlib import Path

def main():
    hooks_dir = Path("P:/.claude/hooks")
    pattern = r'print\(.*file=sys\.stderr\)'

    violations = []
    for hook_file in hooks_dir.glob("*ToolUse*.py"):
        content = hook_file.read_text()
        lines = content.split('\n')

        for i, line in enumerate(lines, start=1):
            # Skip commented lines
            if line.strip().startswith('#'):
                continue
            if re.search(pattern, line):
                violations.append((hook_file.name, i, line.strip()))

    if violations:
        print("⛔ STDERR WRITES FOUND:")
        for file, line_no, line_text in violations:
            print(f"  {file}:{line_no}: {line_text}")
        return 1
    else:
        print("✅ No stderr writes found in hooks")
        return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### 6. Implement /hook-logs command (30 min)

Create `P:/.claude/commands/hook_logs.py`:

```python
#!/usr/bin/env python3
"""View recent hook_errors.jsonl entries."""
import argparse
import json
from pathlib import Path

def main(limit=10):
    log_file = Path("P:/.claude/hooks/logs/hook_errors.jsonl")

    if not log_file.exists():
        print("No error logs found")
        return

    with open(log_file) as f:
        lines = f.readlines()[-limit:]

    for line in lines:
        record = json.loads(line)
        timestamp = record.get('timestamp', 'N/A')
        hook = record.get('hook', 'N/A')
        message = record.get('message', 'N/A')
        print(f"[{timestamp}] {hook}: {message}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="Number of recent entries")
    args = parser.parse_args()
    main(args.limit)
```

#### 7. Log rotation script (30 min)

Create `P:/.claude/hooks/scripts/rotate_logs.py`:

```python
#!/usr/bin/env python3
"""Rotate hook error logs older than 30 days."""
from pathlib import Path
from datetime import datetime, timedelta

LOG_DIR = Path("P:/.claude/hooks/logs")
MAX_AGE_DAYS = 30

def main():
    cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
    removed = 0

    for log_file in LOG_DIR.glob("*.jsonl"):
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        if mtime < cutoff:
            log_file.unlink()
            removed += 1

    print(f"Rotated {removed} log files (older than {MAX_AGE_DAYS} days)")

if __name__ == "__main__":
    main()
```

---

## Ramifications

**Breaks anything?** No - all additive changes, no breaking modifications

**Edge cases:**
- Pre-commit hook may match commented code (mitigation: skip lines starting with `#`)
- Log rotation removes diagnostic data (mitigation: 30-day retention is generous)

**Constraints:**
- Requires Python 3.10+ for pathlib patterns
- Pre-commit hook execution time: <100ms for 100 Python files
- No external dependencies required

---

## Confidence

**Confidence:** 90%

**Evidence basis:**
- Root cause documented in bugfixes.md (verified fix)
- Test infrastructure exists (`test_no_stderr_in_hooks.py` passes)
- Previous LLM attempt was incomplete (only 1/20 stderr writes fixed)
- Implementation is straightforward (no new dependencies, no architecture changes)

**Weakest assumption:** Documentation will be read before future hook development.

**If wrong:** Pre-commit hook enforces compliance regardless.

**Mitigation:** Pre-commit hook is Phase 2 (before tools), so process enforcement happens even if documentation is ignored.

---

## Success Criteria

✅ Documentation updated (bugfixes.md, CLAUDE.md, development guide)
✅ Pre-commit hook scans for stderr writes
✅ CLI tools implemented (/hook-scan, /hook-logs, log rotation)
✅ Test suite passes (`test_no_stderr_in_hooks.py`)
✅ No regression in future hook development

---

**Implementation Order:**
1. Documentation (Phase 1) — 30 min
2. Pre-commit hook (Phase 2) — 1 hour
3. CLI tools (Phase 3) — 2 hours

**Total estimated effort:** 3.5 hours
