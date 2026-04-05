# Hook Upgrade Implementation Prompt

You are implementing 4 upgrades to a Claude Code hooks framework. All files are Python 3.11+, located under `P:/.claude/hooks/`. All hooks must NEVER write to stderr (Claude Code treats stderr as hook errors). All hooks must fail open (never block on exceptions).

## Change 1: PostToolUse cognitive injection on error/empty results

**File to edit:** `P:/.claude/hooks/PostToolUse.py`

**Architecture note:** PostToolUse.py is a router that also performs inline processing (not just dispatch to subprocesses). The cognitive injection logic should be added inline to the main router body, similar to how the error signal file is written.

**Current behavior:** When a tool returns an error or empty results, the hook logs it and writes an error signal file, but outputs `{}` (no feedback to the LLM in the current turn).

**What to change:** When the tool result indicates an error OR empty/no-match results, output `hookSpecificOutput` with `additionalContext` instead of `{}`. This gives the LLM a micro-pause to rethink before its next action.

**Implementation:**

In the `main()` function, after the evidence logging block (step 1) and before the side-effects block (step 2), add logic to build an injection message. Then at the end, output it via `hookSpecificOutput.additionalContext` when present.

Detection rules:
- `success == False` (already computed) → error case
- Tool is `Grep` or `Glob` and result is empty string or contains "0 matches" or "No files found" → empty results case
- Tool is `Bash` and result contains "No such file" or exit code != 0 → error case
- Skip injection for read-only tools: `Read`, `Glob`, `Grep` when they succeed (don't inject on normal successful reads)
- Skip injection if tool is `TodoWrite`, `AskUserQuestion`, `Skill`, or `Write` (not diagnostic tools)

Message templates:
```python
ERROR_INJECTION = (
    "Tool `{tool_name}` returned an error. "
    "State your revised hypothesis in 1 sentence before your next action."
)
EMPTY_INJECTION = (
    "Tool `{tool_name}` returned no results. "
    "Your search assumption may be wrong. Revise your approach before retrying."
)
```

Output format when injecting (per PROTOCOL.md):
```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": injection_message
    }
}
print(json.dumps(output))
```

When NOT injecting, keep the existing `print("{}")`.

**Critical constraints:**
- Never write to stderr
- Never block or exit with non-zero code
- Keep total added code under 30 lines
- Use `hookSpecificOutput.additionalContext` format (PROTOCOL.md lines 114-122) — this is the standard PostToolUse advisory format

---

## Change 2: Confidence label soft advisory at Stop time

**File to edit:** `P:/.claude/hooks/Stop_advisory.py`

**Current behavior:** `check_advisories()` checks for sycophancy, hyperbole, missing tests, and shortcut patterns.

**What to add:** A new check that detects when the response contains absolutist language but no confidence labels.

**Implementation:**

Add these patterns after the existing pattern lists:

```python
# Absolutist language (claims certainty without evidence)
ABSOLUTIST_PATTERNS = [
    r"\bdefinitely\b",
    r"\bguaranteed\b",
    r"\bI'm sure\b",
    r"\bI am sure\b",
    r"\bcertainly\s+(?:is|will|does|has|can)\b",
    r"\bwithout\s+(?:a\s+)?doubt\b",
    r"\b100%\b",
    r"\bthere'?s\s+no\s+(?:way|chance|question)\b",
]

# Confidence labels (if present, absolutist check passes)
CONFIDENCE_LABELS = re.compile(
    r"\b(?:HIGH|MEDIUM|LOW)\s+confidence\b"
    r"|\bconfidence:\s*(?:HIGH|MEDIUM|LOW)\b",
    re.IGNORECASE,
)
```

Add a new check (item 5) inside `check_advisories()`:

```python
# 5. Absolutist language without confidence labels
if any(re.search(p, response_lower) for p in ABSOLUTIST_PATTERNS):
    if not CONFIDENCE_LABELS.search(response):
        suggestions.append(
            "Absolutist language detected without confidence labels. "
            "Label key claims as HIGH/MEDIUM/LOW confidence."
        )
```

**Critical constraints:**
- Only fires if absolutist language is present AND no confidence labels found anywhere in the response
- This is a soft advisory (appended to suggestions list), never a block
- ~15 lines of new code

---

## Change 3: Three new Think trigger profiles

**File to edit:** `P:/.claude/hooks/UserPromptSubmit/think_trigger.py`

**What to add:** Three new reasoning profiles: `security_review`, `performance_analysis`, and `multi_file_refactor`. Each needs strong keywords (1 match triggers), weak keywords (2+ matches trigger), and a template.

**Implementation:**

Add these entries to `_STRONG_PATTERNS` dict (BEFORE the compilation loop that starts with `for _profile in _STRONG_PATTERNS:`):

```python
"security_review": [
    r"SQL injection",
    r"XSS",
    r"cross-site",
    r"CSRF",
    r"auth(?:entication|orization)\s+(?:bug|issue|flaw|bypass|vuln)",
    r"secret(?:s)?\s+(?:leak|expos|hardcod)",
    r"OWASP",
    r"CVE-\d+",
    r"privilege\s+escalation",
    r"injection\s+(?:attack|vuln)",
],
"performance_analysis": [
    r"(?:is|runs?|seems?)\s+(?:really\s+)?slow",
    r"latency\s+(?:spike|issue|problem)",
    r"throughput\s+(?:drop|issue|problem)",
    r"memory\s+leak",
    r"O\(n[²2³3]\)",
    r"big-?O",
    r"bottleneck",
    r"(?:CPU|memory|disk)\s+(?:usage|bound|intensive)",
    r"load\s+test",
],
"multi_file_refactor": [
    r"refactor\s+across\s+(?:multiple|several|all)\s+files",
    r"rename\s+(?:across|everywhere|globally)",
    r"extract\s+(?:into|to)\s+(?:a\s+)?(?:new\s+)?(?:module|package|file|class)",
    r"split\s+(?:into|this into)\s+(?:multiple|separate)",
    r"move\s+(?:all|every)\s+",
    r"restructure\s+(?:the\s+)?(?:module|package|directory|project)",
],
```

Add these entries to `_WEAK_PATTERNS` dict (same location constraint — BEFORE the compilation loop):

```python
"security_review": [
    r"auth(?:entication|orization)?",
    r"(?:input\s+)?(?:validat|sanitiz)",
    r"encrypt",
    r"hash(?:ing)?",
    r"token",
    r"permission",
    _stem("vulnerab", "le|ility|ilities"),
    r"security",
    r"(?:data\s+)?exposure",
],
"performance_analysis": [
    r"optimiz",
    r"profil(?:e|ing)",
    r"cach(?:e|ing)",
    r"(?:query|database)\s+(?:slow|performance|optimization)",
    _stem("benchmark", "s|ing|ed"),
    r"(?:time|space)\s+complexity",
    r"N\+1",
    r"lazy\s+load",
],
"multi_file_refactor": [
    _stem("refactor", "s|ed|ing"),
    r"(?:re)?structur",
    r"reorganiz",
    _stem("consolidat", "e|ed|ing|ion"),
    r"(?:break|split)\s+(?:up|out|apart)",
    r"modulariz",
    r"(?:merge|combine)\s+(?:into|files)",
],
```

Add these entries to the `_PROFILES` dict:

```python
"security_review": """\
THINK PROFILE: SECURITY REVIEW

Security analysis checklist:
1) Entry points — What user input reaches this code? (HTTP params, file uploads, env vars, CLI args)
2) Trust boundaries — Where does trusted meet untrusted data? What crosses the boundary?
3) Data flow — Trace untrusted input through transformations to output/storage
4) Common vulnerabilities — Check for: injection (SQL/command/path), XSS, CSRF, auth bypass, insecure defaults, hardcoded secrets, missing rate limits
5) Least privilege — Does this code have more access than it needs?

Output discipline:
- Each finding: severity (CRITICAL/HIGH/MEDIUM/LOW), location, exploit scenario, fix
- If no vulnerabilities found, state what was checked and why it's believed safe
- Flag any security-relevant assumptions as [UNVERIFIED]""",

"performance_analysis": """\
THINK PROFILE: PERFORMANCE ANALYSIS

Performance investigation:
1) Hypothesis — What do you believe is slow and why? State before measuring
2) Hot path — Identify the critical path (what runs on every request/call?)
3) Complexity — What is the time/space complexity? Is there an N+1 or quadratic pattern?
4) I/O vs CPU — Is the bottleneck I/O (network, disk, DB) or CPU (computation)?
5) Measurement plan — How will you verify the bottleneck? (profiler, timers, counters)

Output discipline:
- Hypothesis first, measurement second, optimization third
- Never optimize without identifying the bottleneck
- State expected improvement with rationale
- Name one thing that could get WORSE from the optimization""",

"multi_file_refactor": """\
THINK PROFILE: MULTI-FILE REFACTOR

Refactoring plan:
1) Invariants — What behavior must be preserved? List concrete behaviors that must not change
2) Impact scan — Which files are affected? Use grep/glob to find all references
3) Dependency order — Which files must change first? (leaf to root, or root to leaf?)
4) Migration steps — Ordered list of atomic changes, each leaving the codebase in a working state
5) Rollback plan — If step N fails, how do you undo steps 1..N-1?

Output discipline:
- Each step must be independently testable
- Run tests after each step, not just at the end
- If a rename touches >10 files, consider a two-phase approach (add new + deprecate old, then remove old)""",
```

**Critical constraints:**
- Add patterns BEFORE the compilation loop (above it in the file)
- Add templates to `_PROFILES` dict (can go anywhere since it's a dict literal)
- ~90 lines total new code
- No new imports needed
- The `_stem()` helper already exists and is used in existing patterns

---

## Change 4: Stop coach note (next-turn advisory)

**File to edit:** `P:/.claude/hooks/Stop_advisory.py` and `P:/.claude/hooks/UserPromptSubmit/cognitive_enhancers.py`

**What to add:** Two new pattern checks in Stop that generate "coach notes" — specific actionable advice persisted to a file that UserPromptSubmit reads on the next turn.

**Implementation — Part A (Stop_advisory.py):**

Add these imports and functions at the top of the file (after existing imports). `re` and `Path` are already imported — only `os` needs to be added:

```python
import os  # add this to existing imports if not already present

HOOKS_DIR = Path(__file__).resolve().parent
COACH_NOTE_DIR = HOOKS_DIR / "session_data"

def _safe_id(value: str) -> str:
    """Sanitize ID for filesystem safety (matches Stop_behavior_audit.py pattern)."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)

def _coach_note_path() -> Path:
    """Return session-scoped coach note path using env vars set by Stop.py._pin_scope_env()."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "")
    scoped_name = f"coach_note_{_safe_id(session_id)}_{_safe_id(terminal_id)}.json"
    return COACH_NOTE_DIR / scoped_name

def _write_coach_note(note: str) -> None:
    """Write a single coach note for next turn. Session-scoped via env vars."""
    try:
        COACH_NOTE_DIR.mkdir(parents=True, exist_ok=True)
        _coach_note_path().write_text(note, encoding="utf-8")
    except OSError:
        pass

def _clear_coach_note() -> None:
    """Clear coach note for this session scope."""
    try:
        path = _coach_note_path()
        if path.exists():
            path.unlink(missing_ok=True)
    except OSError:
        pass

def read_and_clear_coach_note() -> str | None:
    """Read and delete the coach note. Returns note text or None."""
    try:
        path = _coach_note_path()
        if not path.exists():
            return None
        note = path.read_text(encoding="utf-8").strip()
        path.unlink(missing_ok=True)
        return note if note else None
    except OSError:
        return None
```

**Why no `data` arg:** `Stop.py` calls `_pin_scope_env(data)` before any gate runs, which sets `CLAUDE_SESSION_ID` and `CLAUDE_TERMINAL_ID` in the environment. The coach note functions read from those env vars directly — no need to thread `data` through `check_advisories()`'s signature.

Add two coach-note checks at the END of `check_advisories()`, before `return suggestions`:

```python
# Coach notes for next turn
coach_notes = []

# Coach 1: Claimed "fixed" without running tests
if "fixed" in response_lower and "test" not in response_lower:
    coach_notes.append(
        "You claimed a fix but did not run tests. "
        "Next turn: run tests before claiming success."
    )

# Coach 2: Made a plan without defining completion criteria
plan_indicators = ["plan:", "steps:", "approach:", "strategy:"]
done_indicators = ["done when", "complete when", "success criteria",
                   "acceptance criteria", "definition of done"]
if any(ind in response_lower for ind in plan_indicators):
    if not any(ind in response_lower for ind in done_indicators):
        coach_notes.append(
            "You described a plan but gave no completion criteria. "
            "Next turn: define what 'done' looks like before starting work."
        )

if coach_notes:
    _write_coach_note(coach_notes[0])  # Only persist the first/most important
else:
    _clear_coach_note()
```

**Implementation — Part B (cognitive_enhancers.py):**

Add a new registered hook at the end of the file:

```python
@register_hook("coach_note_reader", priority=5.0)
def coach_note_reader(context: HookContext) -> HookResult:
    """Inject coach note from previous Stop advisory if present."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop_advisory import read_and_clear_coach_note

        note = read_and_clear_coach_note()  # reads session scope from env vars
        if not note:
            return HookResult.empty()

        injection = f"**Coach Note** (from previous turn): {note}"
        return HookResult(context=injection, tokens=len(injection) // 4, priority=5.0)
    except Exception:
        return HookResult.empty()
```

**Critical constraints:**
- Coach note file is session-scoped: `coach_note_{safe_session}_{safe_terminal}.json` (matches `_marker_path` pattern from Stop_behavior_audit.py)
- ONE note max per session/terminal pair (no accumulation)
- Read-and-clear pattern: once read by UserPromptSubmit, the file is deleted
- Session isolation prevents cross-terminal contamination
- Never write to stderr
- The "fixed without tests" check already exists as a suggestion in check_advisories — the coach note makes it persist to the NEXT turn too (different mechanism: suggestion is for current response, coach note is for next turn)
- ~50 lines total across two files

---

## Testing

After implementing all 4 changes, verify using pytest in `P:/.claude/hooks/tests/`:

**Test file structure:**
```python
# test_hook_upgrades.py
import json
import os
import subprocess
import sys
import pytest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


def _run_posttooluse(data: dict) -> dict:
    """Run PostToolUse.py as subprocess, return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "PostToolUse.py")],
        input=json.dumps(data).encode(),
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Hook crashed: {result.stderr.decode()}"
    stdout = result.stdout.decode().strip()
    return json.loads(stdout) if stdout else {}


def test_posttooluse_error_injection():
    """PostToolUse should inject advisory on Bash error."""
    data = {
        "tool_name": "Bash",
        "tool_input": {"command": "false"},
        "tool_result": "exit code 1",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    hso = output.get("hookSpecificOutput", {})
    assert hso.get("hookEventName") == "PostToolUse"
    assert "revised hypothesis" in hso.get("additionalContext", "").lower()


def test_posttooluse_empty_grep_injects():
    """PostToolUse should inject advisory on empty Grep results."""
    data = {
        "tool_name": "Grep",
        "tool_input": {"pattern": "nonexistent"},
        "tool_result": "",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    assert "hookSpecificOutput" in output


def test_posttooluse_successful_read_no_injection():
    """PostToolUse should NOT inject on successful Read."""
    data = {
        "tool_name": "Read",
        "tool_input": {"path": "somefile.py"},
        "tool_result": "file contents here",
        "session_id": "test_session",
        "terminal_id": "test_terminal",
    }
    output = _run_posttooluse(data)
    assert "hookSpecificOutput" not in output


def test_stop_advisory_confidence_check():
    """Stop_advisory should flag absolutist language without confidence labels."""
    from Stop_advisory import check_advisories
    response = "This will definitely work and I am sure it is correct."
    suggestions = check_advisories(response)
    assert any("confidence" in s.lower() for s in suggestions)


def test_stop_advisory_confidence_passes_with_labels():
    """Stop_advisory should NOT flag when confidence labels are present."""
    from Stop_advisory import check_advisories
    response = "This will definitely work. HIGH confidence — verified via tests."
    suggestions = check_advisories(response)
    assert not any("absolutist" in s.lower() for s in suggestions)


def test_think_trigger_security_profile():
    """Think trigger should detect security review patterns."""
    from UserPromptSubmit.think_trigger import _detect_profile
    assert _detect_profile("check for SQL injection vulnerabilities") == "security_review"


def test_think_trigger_performance_profile():
    """Think trigger should detect performance analysis patterns."""
    from UserPromptSubmit.think_trigger import _detect_profile
    assert _detect_profile("this code is really slow, probably O(n²)") == "performance_analysis"


def test_think_trigger_refactor_profile():
    """Think trigger should detect multi-file refactor patterns."""
    from UserPromptSubmit.think_trigger import _detect_profile
    assert _detect_profile("refactor this function across all files in the package") == "multi_file_refactor"


def test_coach_note_round_trip():
    """Coach note should write, persist, and clear on read."""
    from Stop_advisory import _write_coach_note, read_and_clear_coach_note, _coach_note_path

    # Scope via env vars (matches how Stop.py sets them via _pin_scope_env)
    os.environ["CLAUDE_SESSION_ID"] = "test_session_123"
    os.environ["CLAUDE_TERMINAL_ID"] = "test_terminal_abc"

    test_note = "You claimed a fix but did not run tests."
    _write_coach_note(test_note)

    note_path = _coach_note_path()
    assert note_path.exists()
    assert "test_session_123" in note_path.name
    assert "test_terminal_abc" in note_path.name

    recovered = read_and_clear_coach_note()
    assert recovered == test_note
    assert not note_path.exists()  # deleted after read


def test_coach_note_terminal_isolation():
    """Coach notes must be isolated per terminal."""
    from Stop_advisory import _write_coach_note, read_and_clear_coach_note

    os.environ["CLAUDE_SESSION_ID"] = "shared_session"
    os.environ["CLAUDE_TERMINAL_ID"] = "terminal_X"
    _write_coach_note("note for X")

    os.environ["CLAUDE_TERMINAL_ID"] = "terminal_Y"
    _write_coach_note("note for Y")

    os.environ["CLAUDE_TERMINAL_ID"] = "terminal_X"
    assert read_and_clear_coach_note() == "note for X"

    os.environ["CLAUDE_TERMINAL_ID"] = "terminal_Y"
    assert read_and_clear_coach_note() == "note for Y"
```

**Run tests:**
```bash
cd P:/.claude/hooks
pytest tests/test_hook_upgrades.py -v
```

## File Summary

| File | Change Type |
|------|-------------|
| `P:/.claude/hooks/PostToolUse.py` | Edit existing `main()` |
| `P:/.claude/hooks/Stop_advisory.py` | Add patterns + coach note functions |
| `P:/.claude/hooks/UserPromptSubmit/think_trigger.py` | Add 3 profile entries to existing dicts |
| `P:/.claude/hooks/UserPromptSubmit/cognitive_enhancers.py` | Add 1 new registered hook at end of file |
