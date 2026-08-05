# Handoff — PreToolUse hook: block Select-String on large files

## Status
OPEN — implementation needed.

## Objective

Build a PreToolUse hook that blocks PowerShell `Select-String` on large text
files (`.jsonl`, `.log`, `.csv`, `.txt` >50KB) and recommends `rg` or Python
`grep` instead.

## Why

Session 2026-08-05: agent used `Select-String -Recurse` across session
transcript files. The scan ran 18 minutes (1095s). The equivalent `rg`
command would complete in <1 second. This is a recurring pattern —
`Select-String` is 100-1000x slower than `rg` on large text files because
it loads entire files into memory line-by-line, while `rg` uses memory-mapped
I/O and parallel search.

AGENTS.md rule was considered but rejected: prose rules have a ~50% compliance
ceiling under session pressure (documented in `[[mechanical-enforcement-over-
behavioral-reminder]]`). A PreToolUse hook is the structural fix.

## Design

### Hook: `PreToolUse_select_string_guard.py`

Registered for `run_terminal_command` events. Fires when:

1. Command contains `Select-String` (case-insensitive)
2. AND the command targets files matching `.jsonl`, `.log`, `.csv`, or `.txt`
3. OR the command uses `-Recurse` flag (which scans potentially large directory trees)

### Exit behavior

- **Block (exit 2):** print stderr message:
  ```
  Select-String is extremely slow on large files. Use rg (ripgrep) or Python grep instead.
  
  Example:
    rg "pattern" <file>              # ripgrep — 100x faster
    python -c "import re; ..."       # Python — flexible
  
  For the specific file types, rg is the correct tool.
  ```
- **Allow (exit 0):** for all other commands, including Select-String on
  small files or non-text targets (e.g., `Get-ChildItem | Select-String`
  on small pipeline output).

### Registration

File: `~/.grok/hooks/select-string-guard.json`
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "run_terminal_command",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.grok/hooks/scripts/select_string_guard.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Implementation notes

- The hook reads the tool_input JSON from stdin (standard PreToolUse contract)
- Extract `command` field from the JSON
- Check for `Select-String` pattern + file extension match
- Keep it fast (<5ms) — pure string matching, no file I/O

## Acceptance criteria

1. Hook blocks `Select-String` on `.jsonl` files with the rg recommendation
2. Hook allows `Select-String` on small files or non-file patterns
3. Hook registered and active in the active surface snapshot
4. Test: simulate a Select-String command on a .jsonl file and verify block

## Key files
- `~/.grok/hooks/UserPromptSubmit_quota_availability.py` — reference pattern for hook structure
- `~/.grok/hooks/scripts/minimal_bias_gate.py` — reference for PreToolUse/Stop hook structure
- `P:/.data/wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md` — rationale

## Handoff is wrong if
- The hook produces too many false positives (blocking legitimate Select-String on small files)
- Grok Build doesn't support PreToolUse hooks for run_terminal_command (verify in user-guide docs)
