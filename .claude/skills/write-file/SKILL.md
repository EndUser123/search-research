---
name: write-file
description: Write files safely when Claude Code Edit/Write tools fail
version: "1.0.0"
status: stable
category: utilities
triggers:
  - /write-file
aliases:
  - /write-file

suggest:
  - /comply
  - /test
  - /git-safety
---

# Write File

Write files safely when Claude Code Edit/Write tools fail.

## Project Context

### Constitution / Constraints
- Complex File Modification Protocol: Use staging for files greater than 10 lines
- Sequential operations: One file at a time when hooks active
- Evidence-first: Verify writes succeeded

### Technical Context
- Method 1: Python atomic write via pathlib.Path.write_text()
- Method 2: Python heredoc for multi-line content
- Fallback when Edit/Write tools fail

### Architecture Alignment
- Fallback pattern: Alternative file writing
- Atomic operations: Safe file replacement

## Your Workflow
1. Receive file path and content
2. Choose appropriate method (atomic vs heredoc)
3. Execute write operation
4. Verify write succeeded

## Validation Rules
### Prohibited Actions
- Do NOT use python -c for multi-line content (greater than 10 lines)
- Do NOT use sed with complex regex substitution
- Do NOT use bash heredocs with shell tool

### Required Methods
- Simple: python3 -c with pathlib.Path.write_text()
- Multi-line: python3 heredoc with Path.write_text()


## Quick Start

```bash
/write-file <path> <content>
```

## Methods

### Option 1: Python atomic write
```bash
python3 -c "from pathlib import Path; Path('<path>').write_text('<content>', encoding='utf-8')"
```

## Multi-line Content

```bash
python3 << 'PYEOF'
from pathlib import Path
Path('<path>').write_text('''<content>''', encoding='utf-8')
PYEOF
```
