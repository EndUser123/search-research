# Precise Delegation Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep hard delegation enforcement, but stop blocking read-only fact gathering and stop matching quoted review text.

**Architecture:** `delegation_prospector.py` decides whether the user prompt creates a delegation obligation. `PreToolUse_delegation_gate.py` enforces that obligation only against implementation/destructive tools. Tests live beside the plugin so package behavior is verified at the source of truth.

**Tech Stack:** Python 3, pytest, Claude Code hook JSON stdin/stdout conventions.

---

## File Structure

- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/hooks/userpromptsubmit/delegation_prospector.py`
  - Add prompt normalization that strips quoted/code/table content before regex detection.
  - Keep the existing state file contract: `.claude/.artifacts/{terminal_id}/hook_state/delegation_expected.json`.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/hooks/pretool/PreToolUse_delegation_gate.py`
  - Add a small policy function that allows read-only tools and narrow diagnostic Bash while blocking implementation tools.
  - Update the block message so the required next action is precise and model-actionable.
- Create: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/tests/test_delegation_policy.py`
  - Tests quote stripping, allowed verification tools, and blocked implementation tools.

## Acceptance Criteria

- Quoted review text containing `create`, `add`, or `implement` does not create delegation state.
- `Read`, `Grep`, `Glob`, and narrow diagnostic `Bash` are allowed when delegation state exists.
- `Edit`, `Write`, `MultiEdit`, broad `Bash`, and destructive `Bash` are blocked when delegation state exists.
- `Task`, `Agent`, and `Skill` still clear delegation state.
- Tests pass from the package root with:
  - `python -m pytest tests/test_delegation_policy.py -q`

---

### Task 1: Add Regression Tests For Current Failure

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/tests/test_delegation_policy.py`

- [ ] **Step 1: Create the test file with failing tests**

Create `P:/packages/.claude-marketplace/plugins/cc-aca-authority/tests/test_delegation_policy.py` with this content:

```python
from __future__ import annotations

import importlib.util
import io
import json
import sys
import time
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PROSPECTOR_PATH = PLUGIN_ROOT / "hooks" / "userpromptsubmit" / "delegation_prospector.py"
GATE_PATH = PLUGIN_ROOT / "hooks" / "pretool" / "PreToolUse_delegation_gate.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_quoted_review_text_does_not_trigger_delegation():
    prospector = load_module("delegation_prospector_under_test", PROSPECTOR_PATH)
    prompt = '''Another LLM said:

> Stop expanding scope. First make state.py importable, add __init__.py,
> then implement policy.py, render.py, and tests.

Please identify the workflow problem.'''

    detected, pattern = prospector._detect_delegation_opportunity(prompt)

    assert detected is False
    assert pattern is None


def test_real_multi_surface_implementation_still_triggers_delegation():
    prospector = load_module("delegation_prospector_under_test_real", PROSPECTOR_PATH)

    detected, pattern = prospector._detect_delegation_opportunity(
        "implement policy.py, render.py, tests, and docs"
    )

    assert detected is True
    assert pattern is not None


def test_read_only_tools_are_allowed_when_delegation_state_exists(tmp_path, monkeypatch):
    gate = load_module("delegation_gate_under_test_readonly", GATE_PATH)
    monkeypatch.setattr(gate, "_get_artifacts_dir", lambda terminal_id_override=None: tmp_path)
    state_file = tmp_path / "delegation_expected.json"
    state_file.write_text(
        json.dumps(
            {
                "terminal_id": "term-1",
                "session_id": "session-1",
                "detected_at": time.time(),
                "matched_pattern": "matched: implementation list",
                "prompt_snippet": "implement policy.py, render.py, tests",
            }
        ),
        encoding="utf-8",
    )

    for tool_name in ("Read", "Grep", "Glob"):
        assert gate._should_block_tool(tool_name, {}) is False


def test_narrow_diagnostic_bash_is_allowed_when_delegation_state_exists():
    gate = load_module("delegation_gate_under_test_bash_allow", GATE_PATH)
    allowed_commands = [
        "python -c \"import context_controller.state\"",
        "python -m py_compile P:/.claude/hooks/context_controller/state.py",
        "git status --short",
        "rg \"resolve_terminal_key\" P:/.claude/hooks",
    ]

    for command in allowed_commands:
        assert gate._should_block_tool("Bash", {"command": command}) is False


def test_implementation_tools_and_broad_bash_are_blocked_when_delegation_state_exists():
    gate = load_module("delegation_gate_under_test_block", GATE_PATH)

    for tool_name in ("Edit", "Write", "MultiEdit"):
        assert gate._should_block_tool(tool_name, {}) is True

    blocked_commands = [
        "pytest",
        "python scripts/apply_all_fixes.py",
        "rm -rf P:/.claude/hooks/context_controller",
        "git commit -am fix",
    ]
    for command in blocked_commands:
        assert gate._should_block_tool("Bash", {"command": command}) is True


def test_task_agent_skill_clear_state_and_allow(tmp_path, monkeypatch):
    gate = load_module("delegation_gate_under_test_clear", GATE_PATH)
    monkeypatch.setattr(gate, "_get_artifacts_dir", lambda terminal_id_override=None: tmp_path)
    monkeypatch.setattr(gate, "_is_bypass_flagged", lambda data: False)
    monkeypatch.setattr(gate, "_detect_terminal_id_from_data", lambda data: "term-1")
    monkeypatch.setattr(gate, "_extract_session_id_from_data", lambda data: "session-1")
    monkeypatch.setattr(gate, "_log_gate_event", lambda *args, **kwargs: None)

    for tool_name in ("Task", "Agent", "Skill"):
        state_file = tmp_path / "delegation_expected.json"
        state_file.write_text(
            json.dumps(
                {
                    "terminal_id": "term-1",
                    "session_id": "session-1",
                    "detected_at": time.time(),
                    "matched_pattern": "matched: implementation list",
                    "prompt_snippet": "implement policy.py, render.py, tests",
                }
            ),
            encoding="utf-8",
        )
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps({"tool_name": tool_name, "terminal_id": "term-1", "session_id": "session-1"}))
        try:
            assert gate.main() == 0
        finally:
            sys.stdin = old_stdin
        assert not state_file.exists()
```

- [ ] **Step 2: Run the new tests and confirm they fail**

Run:

```bash
cd P:/packages/.claude-marketplace/plugins/cc-aca-authority
python -m pytest tests/test_delegation_policy.py -q
```

Expected:

```text
FAILED tests/test_delegation_policy.py::test_quoted_review_text_does_not_trigger_delegation
FAILED tests/test_delegation_policy.py::test_read_only_tools_are_allowed_when_delegation_state_exists
FAILED tests/test_delegation_policy.py::test_narrow_diagnostic_bash_is_allowed_when_delegation_state_exists
```

The exact failure count may differ if `_should_block_tool` does not exist yet.

---

### Task 2: Strip Quoted Content Before Delegation Detection

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/hooks/userpromptsubmit/delegation_prospector.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/tests/test_delegation_policy.py`

- [ ] **Step 1: Add a prompt normalizer near `_DELEGATION_PATTERNS`**

Add this helper above `_detect_delegation_opportunity`:

```python
def _strip_non_actionable_prompt_content(prompt: str) -> str:
    """Remove quoted/example content before matching action-intent regexes."""
    if not prompt:
        return ""

    kept: list[str] = []
    in_fence = False
    for raw_line in prompt.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith(">"):
            continue
        if stripped.startswith("|"):
            continue
        if stripped.startswith("- **") or stripped.startswith("* **"):
            continue

        kept.append(line)

    return "\n".join(kept)
```

- [ ] **Step 2: Use the normalizer in `_detect_delegation_opportunity`**

Replace the body of `_detect_delegation_opportunity` with:

```python
def _detect_delegation_opportunity(prompt: str) -> tuple[bool, str | None]:
    """Detect implicit delegation opportunities via pattern matching only.

    Matching is run on actionable user prose only. Quoted reviews, code blocks,
    and tables are evidence, not instructions.
    """
    normalized = _strip_non_actionable_prompt_content(prompt)
    if not normalized.strip():
        return False, None
    for pattern in _DELEGATION_PATTERNS:
        if pattern.search(normalized):
            return True, f"matched: {pattern.pattern[:50]}..."
    return False, None
```

- [ ] **Step 3: Run the quote regression tests**

Run:

```bash
cd P:/packages/.claude-marketplace/plugins/cc-aca-authority
python -m pytest tests/test_delegation_policy.py::test_quoted_review_text_does_not_trigger_delegation tests/test_delegation_policy.py::test_real_multi_surface_implementation_still_triggers_delegation -q
```

Expected:

```text
2 passed
```

---

### Task 3: Add Precise Hard-Block Policy

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/hooks/pretool/PreToolUse_delegation_gate.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/tests/test_delegation_policy.py`

- [ ] **Step 1: Add policy constants and helper functions above `main()`**

Add this code above `_build_block_message`:

```python
_READ_ONLY_TOOLS = {"Read", "Grep", "Glob", "LS"}
_DELEGATION_TOOLS = {"Task", "Agent", "Skill"}
_IMPLEMENTATION_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

_ALLOWED_DIAGNOSTIC_BASH_PATTERNS = [
    re.compile(r"^\s*python(?:3)?\s+-c\s+.+", re.IGNORECASE),
    re.compile(r"^\s*python(?:3)?\s+-m\s+py_compile\b", re.IGNORECASE),
    re.compile(r"^\s*git\s+(?:status|diff|show|log)\b", re.IGNORECASE),
    re.compile(r"^\s*rg\b", re.IGNORECASE),
    re.compile(r"^\s*Get-Content\b", re.IGNORECASE),
    re.compile(r"^\s*Select-String\b", re.IGNORECASE),
]

_BLOCKED_BASH_PATTERNS = [
    re.compile(r"\b(?:rm|del|Remove-Item)\b", re.IGNORECASE),
    re.compile(r"\bgit\s+(?:commit|push|reset|checkout|clean|merge|rebase)\b", re.IGNORECASE),
    re.compile(r"\bpytest\b(?:\s*$|\s+(?!.*::))", re.IGNORECASE),
    re.compile(r"\bpython(?:3)?\s+[^;&|]*apply", re.IGNORECASE),
]


def _is_allowed_diagnostic_bash(command: str) -> bool:
    """Allow narrow commands that gather evidence but do not change state."""
    if not command.strip():
        return False
    if any(pattern.search(command) for pattern in _BLOCKED_BASH_PATTERNS):
        return False
    return any(pattern.search(command) for pattern in _ALLOWED_DIAGNOSTIC_BASH_PATTERNS)


def _should_block_tool(tool_name: str, tool_input: dict) -> bool:
    """Return True only for tools that can mutate or broadly execute work."""
    if tool_name in _DELEGATION_TOOLS:
        return False
    if tool_name in _READ_ONLY_TOOLS:
        return False
    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
        return not _is_allowed_diagnostic_bash(command)
    if tool_name in _IMPLEMENTATION_TOOLS:
        return True
    return True
```

- [ ] **Step 2: Use `_should_block_tool` in `main()`**

Replace the existing "Block all other tools" section:

```python
    # Block all other tools
    block_msg = _build_block_message(tool_name, state)
    print(block_msg, file=sys.stderr)
    _log_gate_event("blocked", tool_name, state.get("matched_pattern", ""))
    return 2  # Block
```

with:

```python
    tool_input = data.get("tool_input", {}) if isinstance(data.get("tool_input", {}), dict) else {}
    if not _should_block_tool(tool_name, tool_input):
        _log_gate_event("allowed_evidence_gathering", tool_name, state.get("matched_pattern", ""))
        return 0

    block_msg = _build_block_message(tool_name, state)
    print(block_msg, file=sys.stderr)
    _log_gate_event("blocked", tool_name, state.get("matched_pattern", ""))
    return 2
```

- [ ] **Step 3: Run policy tests**

Run:

```bash
cd P:/packages/.claude-marketplace/plugins/cc-aca-authority
python -m pytest tests/test_delegation_policy.py::test_read_only_tools_are_allowed_when_delegation_state_exists tests/test_delegation_policy.py::test_narrow_diagnostic_bash_is_allowed_when_delegation_state_exists tests/test_delegation_policy.py::test_implementation_tools_and_broad_bash_are_blocked_when_delegation_state_exists -q
```

Expected:

```text
3 passed
```

---

### Task 4: Make The Block Message Actionable

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/hooks/pretool/PreToolUse_delegation_gate.py`

- [ ] **Step 1: Replace `_build_block_message`**

Replace `_build_block_message` with:

```python
def _build_block_message(tool_name: str, state: dict) -> str:
    """Build descriptive block message."""
    matched = state.get("matched_pattern", "unknown pattern")
    snippet = state.get("prompt_snippet", "")[:100]
    return f"""DELEGATION REQUIRED

A delegation opportunity was detected: {matched}

Snippet: {snippet}...

This gate blocks implementation or broad execution until delegation happens.
Allowed now: Read, Grep, Glob, and narrow diagnostic Bash commands.
Blocked now: {tool_name}

Next action:
- Use Agent/Task to delegate the independent work packets, or
- Gather read-only evidence first with Read/Grep/Glob/narrow Bash, then delegate before editing.

User override for the next turn: send --allow-inline.
"""
```

- [ ] **Step 2: Run all delegation policy tests**

Run:

```bash
cd P:/packages/.claude-marketplace/plugins/cc-aca-authority
python -m pytest tests/test_delegation_policy.py -q
```

Expected:

```text
6 passed
```

---

### Task 5: Verify Current Hook Routing And Runtime Import

**Files:**
- Read only: `P:/.claude/settings.json`
- Read only: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/hooks/pretool/PreToolUse_delegation_gate.py`
- Read only: `P:/packages/.claude-marketplace/plugins/cc-aca-authority/hooks/userpromptsubmit/delegation_prospector.py`

- [ ] **Step 1: Verify the package modules import**

Run:

```bash
cd P:/packages/.claude-marketplace/plugins/cc-aca-authority
python -c "import importlib.util, pathlib; p=pathlib.Path('hooks/pretool/PreToolUse_delegation_gate.py'); s=importlib.util.spec_from_file_location('g', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m._should_block_tool('Read', {})); print(m._should_block_tool('Edit', {}))"
```

Expected:

```text
False
True
```

- [ ] **Step 2: Verify the prospector ignores the pasted failure shape**

Run:

```bash
cd P:/packages/.claude-marketplace/plugins/cc-aca-authority
python -c "import importlib.util, pathlib; p=pathlib.Path('hooks/userpromptsubmit/delegation_prospector.py'); s=importlib.util.spec_from_file_location('d', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m._detect_delegation_opportunity('> add a.py, b.py, c.py\\nPlease identify the workflow problem.'))"
```

Expected:

```text
(False, None)
```

- [ ] **Step 3: Run the final test command**

Run:

```bash
cd P:/packages/.claude-marketplace/plugins/cc-aca-authority
python -m pytest tests/test_delegation_policy.py -q
```

Expected:

```text
6 passed
```

---

## Do Not Do

- Do not make the delegation gate purely advisory.
- Do not remove `delegation_expected.json` state unless replacing both writer and reader in the same change.
- Do not edit `P:/.claude/settings.json` for this fix unless tests show the plugin hook is not routed.
- Do not regenerate unrelated hook docs in this change.
- Do not broaden allowed Bash beyond evidence-gathering commands.

## Self-Review Checklist

- [ ] The plan preserves hard enforcement for implementation tools.
- [ ] The plan prevents the exact false positive from quoted review text.
- [ ] The plan lets the model verify facts without waiting for the user to type `--allow-inline`.
- [ ] The plan keeps changes limited to the delegation prospector, delegation gate, and package tests.
- [ ] The final verification command is package-local and repeatable.
