---
title: "Workspace script FMEA pattern — concurrent I/O hazards and shell-injection surface"
created: 2026-08-02
source: session-019fa8f8-7e86-77f0-8e81-a7609f3c8b14
tags: [fmea, i/o-safety, concurrency, shell-injection, atomic-write, workspace-script-pattern, capture]
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - P:/.agents/scripts/launch_llm_chrome.py (os.system shell injection surface)
  - P:/packages/nlm-to-wiki/scripts/synthesize_subtopics.py (non-atomic write + chunk[:4000] UTF-8 split)
  - P:/packages/nlm-to-wiki/scripts/log_spawn.py (non-atomic append to shared file)
  - P:/.agents/scripts/scheduled_checks.py (no error handling on malformed JSON)
  - P:/.agents/scripts/version_check.py (no retry logic for network)
  - FMEA sweep output (session 019fa8f8, 2026-08-01, sweep pass)
relations:
  - target: wiki/concepts/file-edit-failures-two-classes.md
    type: related (atomic write is one fix vector; this concept is broader)
  - target: wiki/concepts/chrome-job-object-escape-via-task-scheduler.md
    type: parallel (the launch_llm_chrome os.system pattern is documented AS the implementation, not flagged AS a vulnerability)
  - target: wiki/concepts/external-silent-edit-and-shell-quoting-reports.md
    type: related (Class C shell quoting — different class; this concept covers execution-time injection)
  - target: wiki/concepts/llm-synthesis-context-truncation-blind-spot.md
    type: related (chunk boundary loss is captured at the LLM context level; the chunk[:4000] UTF-8 split is the Python-side instantiation)
  - target: docs/handoffs/fmea-fix-batch-20260802/HANDOFF.md
    type: implementation-handoff
---

# Workspace script FMEA pattern — concurrent I/O hazards and shell-injection surface

## The meta-finding (the learning that transfers)

The 2026-08-02 FMEA sweep of agent-touched scripts in `P:/.agents/scripts/` and `P:/packages/nlm-to-wiki/scripts/` surfaced **6 CRITICAL and 3 WARN issues** in a single pass. **What is worth capturing is not the individual bugs — it is that they share a pattern.** Workspace scripts written by agents to "just get a thing done" systematically under-engineer three classes of safety:

1. **Concurrent I/O** — appending to shared log files without atomic write or file locking
2. **Shell invocation** — using `os.system()` with f-string interpolation, no error handling, no timeout
3. **Boundary handling** — splitting text at fixed character offsets without checking for multi-byte character boundaries

The pattern: scripts optimized for "first working draft" pass review because they work for the writer (single agent, single terminal, single execution). They fail when deployed into the multi-agent, multi-terminal, multi-execution environment they were nominally written for.

## What this is NOT

This is **not** a claim that the agents who wrote these scripts were careless. The bugs are reasonable omissions when each script is viewed in isolation. The failure mode is **systemic**: the review/check loop for these scripts does not catch I/O safety issues until something breaks in production. Multiple sessions, multiple terminals, and concurrent agent commits are the deployment environment — not a hypothetical future state.

## The 6 CRITICAL findings (verbatim from FMEA sweep, 2026-08-02)

| # | File | Issue | Class |
|---|------|-------|-------|
| 1 | `launch_llm_chrome.py` | `os.system()` for `schtasks` commands — shell injection risk if paths contain special chars | Shell invocation |
| 2 | `launch_llm_chrome.py` | No timeout on `os.system` calls — hung schtasks can block indefinitely | Shell invocation |
| 3 | `launch_llm_chrome.py` | No error handling on command output (exit code ignored) | Shell invocation |
| 4 | `synthesize_subtopics.py` | `args.output.write_text()` without atomic write (tmp+replace) — corruption risk if interrupted | I/O |
| 5 | `log_spawn.py` | Appends to `spawn_failures.jsonl` without atomic write or file locking — concurrent writes corrupt | Concurrency |
| 6 | `synthesize_subtopics.py` | `pre_summarize_member` fallback uses `chunk[:4000]` which can split multi-byte UTF-8 characters | Boundary |

## The 3 WARN findings

| # | File | Issue | Class |
|---|------|-------|-------|
| 7 | `scheduled_checks.py` | `load_registry()` has no error handling for malformed JSON | I/O |
| 8 | `version_check.py` | No retry logic for PyPI network failures | Network |
| 9 | `synthesize_subtopics.py` | `call_mmx`/`call_dgemma` use `subprocess.run` with `capture_output=True` — potential deadlock if LLM output exceeds OS pipe buffer (64KB on Windows) | I/O |

## Why this pattern emerges repeatedly

Three structural causes, each independently sufficient:

1. **No script-level I/O safety review.** Workspace scripts (under `P:/.agents/scripts/` and `P:/packages/*/scripts/`) are not subject to the hook-enforced review that agent-touched files get. The `/fmea` skill exists but is invoked reactively, not as a pre-commit gate.

2. **Single-agent assumption.** Scripts are written by one agent in one terminal, then committed. The multi-terminal/multi-session execution environment is the deployment state, not the development state. Reviewers don't see the concurrency dimension because they don't operate in it.

3. **"Just get it working" optimization.** Each script has a primary job (launch Chrome, log spawn failures, synthesize subtopics). I/O safety is a non-functional requirement that doesn't surface until the script fails in production. The cost is paid by the next session, not the current one.

## What the fix looks like (knowledge applied)

For each class, the standard fix is well-understood:

- **Shell invocation (os.system → subprocess.run with list args)**: replace `os.system(f'schtasks /create ... {var}')` with `subprocess.run(['schtasks', '/create', ..., var], check=True, timeout=N, capture_output=True)`. List-form args bypass shell parsing entirely; `check=True` raises on non-zero exit; `timeout` bounds the call.
- **Concurrent I/O (append → atomic-write or flock)**: for JSONL append, write to `path.with_suffix('.tmp')` then `os.replace`. For high-concurrency cases, `fcntl.flock()` on POSIX or `msvcrt.locking()` on Windows.
- **Boundary handling (chunk[:N] → Unicode-aware split)**: use `textwrap.wrap` or split on word boundaries; for byte boundaries, decode to `str` first.

These are not novel patterns — they are standard Python I/O hygiene. The finding is that workspace scripts do not apply them by default.

## What this concept does NOT claim

- **Not "all workspace scripts are unsafe."** Many scripts are correct. The pattern is the under-engineering TENDENCY, not a universal property.
- **Not "agents should manually audit every script."** That is the wrong fix. The structural fix is a pre-commit / pre-merge I/O safety check (analogous to ruff for style, pyright for types).
- **Not a replacement for `/fmea`.** This concept captures the meta-finding that emerged from a single FMEA sweep. `/fmea` is the skill that produces the findings; this concept captures the pattern they share.

## How to use this concept

When reviewing a workspace script:

1. Does it use `os.system`, `subprocess.Popen(shell=True)`, or `subprocess.run` with `shell=True`? → Flag for shell-injection review
2. Does it append to a shared file (especially `*.jsonl` or `*.log`)? → Flag for concurrent-write review
3. Does it slice text at character or byte offsets? → Flag for boundary review
4. Does it call external processes with `capture_output=True`? → Flag for pipe-buffer deadlock (esp. on Windows, 64KB limit)

When writing a new workspace script: apply the four checks above as a pre-commit checklist.

## Source provenance

FMEA sweep output (session 019fa8f8, 2026-08-01, sweep pass). Files touched in 24h prior to sweep:
`launch_llm_chrome.py`, `synthesize_subtopics.py`, `log_spawn.py`, `test_log_spawn.py`, `version_check.py`, `test_synthesize_context.py`, `scheduled_checks.py`, `__lib/__init__.py`, `build_skill_graph.py`, `index_skills.py`.

I/O operations identified via file content analysis: file reads/writes, `subprocess.run`, `os.system`, socket connections, temp file creation, `json.loads`/`json.dumps` on disk files.

**Reference failure (predicted):** if a future session encounters corruption in `spawn_failures.jsonl` or hangs on `schtasks` with `WinError 123`, that is the production failure this concept exists to prevent. The fix handoff is `docs/handoffs/fmea-fix-batch-20260802/HANDOFF.md`.