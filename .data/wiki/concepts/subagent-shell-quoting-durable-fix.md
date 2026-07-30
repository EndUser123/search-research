---
title: "Subagent shell-quoting durable fix: shared scripts over inline python -c"
created: 2026-07-30
source: session-2026-07-30 (378s wasted on failed subagent due to PowerShell quoting)
tags: [shell-quoting, class-c, powershell, subagent, ddgs, durable-fix, windows, anti-pattern]
agent: grok
host: both
cognitive_load: 2
verification: workspace_verified
summary: >
  Subagents dispatched on Windows PowerShell waste entire budgets (378s in
  session 019fb3a8) trying to run inline `python -c "from ddgs import DDGS;
  list(DDGS().text('query'))"` — the nested quotes collide with PowerShell's
  string handling. The durable fix: shared script files that subagents call
  as plain arguments. Created `P:/.agents/scripts/ddgs_search.py` as the first
  instance. The general principle: any Python subagents run should be a file,
  not inline `-c`.
relations:
  - target: wiki/concepts/shell-quoting-and-non-persisting-edits
    type: extends
---

## The failure mode

Subagents on Windows PowerShell receive prompts like:

> "Search the web using DDG: `from ddgs import DDGS; results = list(DDGS().text('query', max_results=10))`"

The subagent tries to run this as:

```powershell
python -c "from ddgs import DDGS; results = list(DDGS().text('query', max_results=10))"
```

**This fails.** PowerShell sees the outer double-quotes as string delimiters. The single quotes inside are Python string delimiters. When the query itself contains apostrophes, quotes, or special characters, the quoting collapses. The subagent retries with different escaping strategies, each failing, until its entire budget (378s in session 019fb3a8) is exhausted with zero useful output.

This is the Class C quoting hazard from AGENTS.md, applied to subagent-dispatched Python.

## The durable fix

**Move the Python code into a file. Pass the query as a plain argument.**

```
# Before (fails on PowerShell):
python -c "from ddgs import DDGS; list(DDGS().text('query'))"

# After (works everywhere):
python P:/.agents/scripts/ddgs_search.py "query" --max 10
```

The query is a single double-quoted positional argument — PowerShell handles this cleanly. No nested quotes, no escaping, no ambiguity.

### Artifact: ddgs_search.py

Created at `P:/.agents/scripts/ddgs_search.py` (session 2026-07-30). Verified working:
- `python P:/.agents/scripts/ddgs_search.py "query" --max 10` → JSON output
- `--site reddit.com` for site-restricted search
- `--text` for human-readable output
- `--stdin` for piped input
- Standalone: no workspace imports, just stdlib + ddgs

### The general principle

This applies beyond DDG. Any Python that subagents run should be a file, not inline `python -c`:

| Pattern | Status |
|---|---|
| DDG searches | ✅ Fixed: `ddgs_search.py` |
| JSON parsing of tool output | Use existing scripts or write to `P:/tmp/parse.py` |
| Multi-line Python (loops, conditionals) | Write to `P:/tmp/script.py`, then execute |
| Git operations requiring Python orchestration | Write to `P:/tmp/git_op.py`, then execute |

The spawn template in `/go` H4 should include: "For any Python, write a temp `.py` file to `P:/tmp/` and execute it. Never use inline `python -c` with nested quotes."

## Why this is durable

1. **Artifact layer:** the script exists on disk — it doesn't depend on the model remembering the quoting rule
2. **Template layer:** updating `/go`'s H4 spawn template to reference the script means every dispatched subagent sees the instruction
3. **Pattern layer:** this wiki concept documents the general principle for future script authors

## Falsifier

This fix is wrong if:
- `ddgs_search.py` proves unreliable on specific query patterns (special characters, Unicode)
- Subagents continue using inline `python -c` despite the template instruction (would need a hook-level enforcement)
- The ddgs package API changes and breaks the script (mitigated: script is simple, ~80 lines)
