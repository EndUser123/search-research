---
title: "FMEA fix batch — 6 CRITICAL + 3 WARN issues in workspace scripts"
type: handoff
status: open
created: 2026-08-02
priority: high
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: console_019fa8f8
thread_id: fmea-fix-batch-20260802
source: session-019fa8f8-7e86-77f0-8e81-a7609f3c3c8b14
sweep_session: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
scan_source: FMEA sweep, 2026-08-02, session 019fa8f8
tags: [fmea, workspace-scripts, i/o-safety, security, batch-fix, improvement-stream]
agent: grok
host: grok
---

# Handoff: FMEA fix batch — 6 CRITICAL + 3 WARN issues in workspace scripts

## Context

The 2026-08-02 FMEA sweep of agent-touched workspace scripts surfaced 6 CRITICAL and 3 WARN issues. All share a pattern (see `wiki/concepts/workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md`). This handoff is the **improvement stream** routing — the fixes themselves, not the meta-pattern.

The session that produced this handoff (019fa8f8) was BLOCKED on close-gates due to unrelated close-runner issues; the FMEA findings are independently actionable and ready for a fresh session.

## CRITICAL fixes (priority: high)

### CRIT-1: `launch_llm_chrome.py` — replace `os.system` with `subprocess.run`

**Files:** `P:/.agents/scripts/launch_llm_chrome.py` (lines 23-24 in the documented version)

**Current pattern (vulnerable):**
```python
os.system(f'schtasks /create /tn "{task_name}" /tr "chrome.exe --user-data-dir=P:\\.data\\chrome-llm-profile" /sc once /st 00:00 /f')
os.system(f'schtasks /run /tn "{task_name}"')
```

**Fixed pattern:**
```python
subprocess.run(
    ['schtasks', '/create', '/tn', task_name, '/tr', tr_path, '/sc', 'once', '/st', '00:00', '/f'],
    check=True, timeout=30, capture_output=True
)
subprocess.run(
    ['schtasks', '/run', '/tn', task_name],
    check=True, timeout=30, capture_output=True
)
```

**Acceptance:** ruff check passes, py_compile succeeds, no os.system calls remain in the file. Existing tests in `P:/.agents/scripts/tests/` (if any) pass.

### CRIT-2: `synthesize_subtopics.py` — atomic write for output

**File:** `P:/packages/nlm-to-wiki/scripts/synthesize_subtopics.py`

**Current pattern (corruptible):**
```python
args.output.write_text(content, encoding='utf-8')
```

**Fixed pattern:**
```python
import os, tempfile
tmp = args.output.with_suffix(args.output.suffix + '.tmp')
tmp.write_text(content, encoding='utf-8')
os.replace(tmp, args.output)
```

**Acceptance:** atomic write in place, no `write_text` calls to non-tmp paths without `os.replace`.

### CRIT-3: `log_spawn.py` — atomic append or flock for `spawn_failures.jsonl`

**File:** `P:/packages/nlm-to-wiki/scripts/log_spawn.py`

**Current pattern (concurrent-write corruptible):**
```python
with open(spawn_log_path, 'a') as f:
    f.write(json.dumps(entry) + '\n')
```

**Fixed pattern (option A — atomic write per line, simpler):**
```python
tmp = spawn_log_path.with_suffix('.tmp')
existing = spawn_log_path.read_text(encoding='utf-8') if spawn_log_path.exists() else ''
new = existing + json.dumps(entry) + '\n'
tmp.write_text(new, encoding='utf-8')
os.replace(tmp, spawn_log_path)
```

**Fixed pattern (option B — flock, scales better):**
```python
import fcntl  # POSIX; on Windows use msvcrt.locking
with open(spawn_log_path, 'a') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    f.write(json.dumps(entry) + '\n')
    f.flush()
```

**Acceptance:** no bare `open(..., 'a')` writes remain. Stress test: two parallel log_spawn.py invocations both succeed; `spawn_failures.jsonl` is valid JSONL (each line parses).

### CRIT-4: `synthesize_subtopics.py` — Unicode-aware chunk split

**File:** `P:/packages/nlm-to-wiki/scripts/synthesize_subtopics.py` — `pre_summarize_member` fallback

**Current pattern (UTF-8 boundary violation):**
```python
chunk = member_text[:4000]
```

**Fixed pattern:**
```python
# Decode to str first if member_text is bytes; split on Unicode boundaries
if isinstance(member_text, bytes):
    member_text = member_text.decode('utf-8', errors='replace')
# Use textwrap or word boundary to avoid splitting mid-character
import textwrap
chunk = member_text[:4000]
# If chunk ends mid-codepoint, walk back to a safe boundary
last_safe = chunk.rfind(' ')
if last_safe > 3500:
    chunk = chunk[:last_safe]
```

**Acceptance:** chunk output is valid UTF-8 even when source contains multi-byte characters. Add a test that includes CJK characters and verifies the chunk parses back to valid `str`.

### CRIT-5 + CRIT-6: `launch_llm_chrome.py` — timeout + error handling on `os.system`

**Subsumed by CRIT-1.** Once `os.system` is replaced with `subprocess.run(..., check=True, timeout=30)`, the timeout and error-handling issues are fixed by construction.

## WARN fixes (priority: medium)

### WARN-1: `scheduled_checks.py` — error handling in `load_registry()`

**File:** `P:/.agents/scripts/scheduled_checks.py`

**Current pattern (fragile):**
```python
def load_registry():
    return json.loads(state_file.read_text())
```

**Fixed pattern:**
```python
def load_registry():
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as e:
        log.warning(f"scheduled_checks: corrupt state file, recreating: {e}")
        return {}
```

**Acceptance:** feeding the function a malformed JSON file returns `{}` and logs a warning, not an exception.

### WARN-2: `version_check.py` — retry logic for PyPI

**File:** `P:/.agents/scripts/version_check.py`

**Current pattern (no retry):**
```python
response = urllib.request.urlopen(pypi_url)
```

**Fixed pattern:**
```python
for attempt in range(3):
    try:
        response = urllib.request.urlopen(pypi_url, timeout=10)
        break
    except (urllib.error.URLError, TimeoutError) as e:
        if attempt == 2:
            log.warning(f"version_check: PyPI unreachable after 3 attempts: {e}")
            return None
        time.sleep(2 ** attempt)
```

**Acceptance:** with network blocked, version_check returns None after 3 attempts instead of raising.

### WARN-3: `synthesize_subtopics.py` — pipe buffer deadlock

**File:** `P:/packages/nlm-to-wiki/scripts/synthesize_subtopics.py` — `call_mmx`/`call_dgemma`

**Current pattern (deadlock risk on large output):**
```python
result = subprocess.run(cmd, capture_output=True, text=True)
```

**Fixed pattern:**
```python
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
stdout, stderr = proc.communicate(timeout=300)
```

**Or with explicit buffer size:**
```python
result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
# 'timeout' forces communicate() under the hood, avoiding the deadlock
```

**Acceptance:** call_mmx with a >64KB output completes without hanging. Add a test that mocks a 100KB stdout.

## Acceptance criteria (handoff close)

1. All 6 CRITICAL fixes merged to main
2. At least 2 of 3 WARN fixes merged (CRIT takes priority)
3. New tests added for atomic write, concurrent append, UTF-8 boundary, and pipe deadlock
4. Ruff check passes on all modified files
5. Py_compile succeeds on all modified files
6. No regression in existing test suites under `P:/.agents/scripts/tests/` and `P:/packages/nlm-to-wiki/tests/`

## Estimated effort

- CRIT-1, CRIT-5, CRIT-6: 1 hour (single-file, ~30 lines changed)
- CRIT-2: 30 minutes (one-line change + test)
- CRIT-3: 1.5 hours (option B flock is Windows-unfriendly; choose A or document why B)
- CRIT-4: 1 hour (needs test fixture with CJK content)
- WARN-1, WARN-2: 30 minutes each
- WARN-3: 30 minutes (low-risk substitution)

**Total: ~6 hours** for full batch.

## Routing

This handoff is **OPEN** and ready for pickup by a fresh session. Claim with: `claim-handoff fmea-fix-batch-20260802`.

## Source

- FMEA sweep output (session 019fa8f8, 2026-08-02)
- Wiki concept: `P:/.data/wiki/concepts/workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md`
- File targets: as listed above

## Verification receipts

- FMEA sweep command: `python P:/.agents/skills/fmea/scripts/scan.py --scope P:/.agents/scripts --scope P:/packages/nlm-to-wiki/scripts --output P:/tmp/fmea-20260802.json` (verify the output file lists these 9 findings)
- Affected files (git status P:/): `launch_llm_chrome.py`, `synthesize_subtopics.py`, `log_spawn.py`, `scheduled_checks.py`, `version_check.py` (5 files modified in 24h prior to sweep)
assigned_to: grok
---
assigned_at: 2026-08-02T21:27
---
assigned_by: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
---

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T21:27 | 019fa8f8... | claimed by grok |
