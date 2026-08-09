---
title: "Class C shell quoting guard: structural enforcement for python -c hazards"
created: 2026-08-09
source: session-2026-08-09
tags: [hook-system, shell-quoting, class-c-hazard, structural-enforcement, pretooluse, windows, powershell]
host: grok
agent: grok
cognitive_load: 1
verification: directly-verified
summary: >
  A PreToolUse hook that blocks multi-line/nested-quote python -c payloads before they
  reach the shell. Structural enforcement of the AGENTS.md Class C rule, which has a
  ~50% prose compliance ceiling. Detects multi-line payloads, nested quotes, f-string
  subscripts (the specific session-breaking pattern), and PowerShell here-strings.
---

# Class C shell quoting guard: structural enforcement for python -c hazards

## Decision context

The AGENTS.md documents Class C shell quoting as a prose rule: "for multi-line or
nested-quote shell payloads, write to a temp file and invoke against the file." This
rule fired incorrectly multiple times in a single session — the model used `python -c`
with nested quotes that broke in PowerShell, then recovered via the documented temp-file
workaround.

The prose rule has a ~50% compliance ceiling under session pressure (documented in
AGENTS.md). The structural fix is a PreToolUse hook that blocks the pattern before it
reaches the shell.

## The hook

`~/.grok/hooks/PreToolUse_class_c_quoting_guard.py` — matches `run_terminal_command`
and `Bash` tools. Checks the command string for:

1. Multi-line `python -c` (newline in payload)
2. Nested quotes (single inside double-quoted -c, or vice versa)
3. f-string subscripts (the session-breaking pattern: `f'{x[0]}'`)
4. PowerShell here-strings (`@'...'@`)

Safe single-expression `python -c "print(2+2)"` is allowed.

## Why f-string subscripts specifically

The initial implementation blocked all brackets (`[`, `]`) in `python -c`. This was
too broad — it blocked safe list literals (`python -c "x = [1, 2, 3]; print(x)"`) and
list comprehensions. The actual hazard is f-string subscripts that combine bracket +
nested quote context to break PowerShell parsing. Plain brackets in properly-quoted
strings are safe in PowerShell.

## Receipts

- `~/.grok/hooks/PreToolUse_class_c_quoting_guard.py` — the hook
- `~/.grok/hooks/class-c-quoting-guard.json` — registration
- 11 tests pass (5 blocked patterns + 6 allowed patterns)

## Falsifier

This hook is wrong if it blocks legitimate single-line `python -c` commands that are
safe in PowerShell. The f-string subscript detection is narrow enough that only the
actual hazard pattern triggers it.

## Auto-related

- [[hook-block-observability-per-session-logging-escalation-path]] — same per-session block logging pattern
