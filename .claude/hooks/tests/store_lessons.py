#!/usr/bin/env python3
"""Store critique execution lessons to CKS."""

import sys

sys.path.insert(0, "P:/__csf/src")

from knowledge.systems.cks.unified import ingest_pattern

lessons = [
    {
        "title": "Critique execution directive pattern",
        "content": """# Critique Execution Directive Pattern

## Problem
When `/critique` produces findings with "0 — Do ALL Recommended Next Steps", AI incorrectly treats this as a consultation request ("Should I proceed with Domain 6, or skip to Domain 7?") instead of an execution directive.

## Root Cause
Defaulted to consultation pattern instead of execution pattern. Failed to recognize that "0" means "execute ALL recommended next steps — starting with CRASH PREVENTION (domain 1) and working through each domain."

## Correct Behavior
- Read "0" as "begin implementing these fixes now"
- Start next domain without asking
- No ambiguity exists when user says "0"

## Evidence
From critique p3.md:490-494:
**0** - Execute ALL Recommended Next Steps
**When you respond "0", the skill will begin implementing these fixes — starting with CRASH PREVENTION (domain 1) and working through each domain. This is an execution directive, not a display request.**

## Date
2026-03-23

## Keywords
critique, execution-directive, consultation-pattern, skill-workflow
""",
        "entry_type": "pattern",
        "source": "critique_execution",
        "fix_date": "2026-03-23",
        "files_modified": [],
        "keywords": ["critique", "execution", "directive", "consultation", "pattern"],
    },
    {
        "title": "os.getcwd() crash prevention pattern",
        "content": """# os.getcwd() Crash Prevention Pattern

## Problem
PreToolUse_directory_policy.py line 219 calls `os.getcwd()` without error handling. If CWD is deleted/inaccessible, hook crashes completely.

## Impact
Complete hook failure affects ALL tool operations, not just directory policy.

## Solution
Wrap `os.getcwd()` in try/except with fallback to `CLAUDE_PROJECT_DIR`:

```python
if tool_name == 'Bash':
    try:
        working_dir = os.getcwd().replace('\\\\', '/')
    except (OSError, FileNotFoundError) as e:
        working_dir = os.environ.get('CLAUDE_PROJECT_DIR', 'P:/').replace('\\\\', '/')
        print(f'Warning: CWD inaccessible ({e}), using project_dir: {working_dir}', file=sys.stdout)
```

## Lesson
Always wrap `os.getcwd()` in error handling with fallback. CWD can be deleted, ejected, become unavailable (network timeout), or have permission issues.

## Date
2026-03-23

## Keywords
os.getcwd, crash, hook, error-handling, fallback, cwd
""",
        "entry_type": "pattern",
        "source": "critique_execution",
        "fix_date": "2026-03-23",
        "files_modified": ["PreToolUse_directory_policy.py"],
        "keywords": ["os.getcwd", "crash", "hook", "error", "fallback"],
    },
    {
        "title": "Thread safety for module-level globals",
        "content": """# Thread Safety for Module-Level Globals

## Problem
`ALLOWED_EXTERNAL_PATTERNS` is a module-level global loaded at import time without locking. Multi-terminal concurrent execution could cause race conditions.

## Solution
Add `threading.Lock()` for thread-safe access:

```python
# Thread safety lock for ALLOWED_EXTERNAL_PATTERNS access
_ALLOWED_EXTERNAL_PATTERNS_LOCK = threading.Lock()

def is_allowed_external_path(file_path: str) -> bool:
    # Thread-safe access to ALLOWED_EXTERNAL_PATTERNS
    with _ALLOWED_EXTERNAL_PATTERNS_LOCK:
        if not ALLOWED_EXTERNAL_PATTERNS:
            return False
        # Copy the list to avoid holding lock during iteration
        patterns = list(ALLOWED_EXTERNAL_PATTERNS)
    # ... rest of function
```

## Lesson
Module-level globals without locks are concurrency anti-patterns in multi-terminal environments. CLAUDE.md states "This codebase runs multiple terminals simultaneously."

## Date
2026-03-23

## Keywords
thread-safety, module-level, globals, locking, multi-terminal, race-condition
""",
        "entry_type": "pattern",
        "source": "critique_execution",
        "fix_date": "2026-03-23",
        "files_modified": ["PreToolUse_directory_policy.py"],
        "keywords": ["thread", "safety", "global", "locking", "concurrency"],
    },
]

for lesson in lessons:
    entry_id = ingest_pattern(**lesson)
    print(f"Stored: {entry_id} - {lesson['title']}")
