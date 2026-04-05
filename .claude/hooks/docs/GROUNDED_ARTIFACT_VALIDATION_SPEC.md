# Grounded Artifact Validation (GAV) - Implementation Specification

## What You're Building

A mechanical grounding system for Claude Code hooks that prevents the LLM from writing confident explanations about the **wrong artifact**. The pattern is:

```
Ground (deterministic) → Echo (LLM, constrained) → Validate (deterministic) → Narrate (LLM, free)
```

**The bug this fixes**: When a tool call is blocked by a hook, the LLM sometimes ignores the actual blocked command and instead writes an elaborate RCA about something else entirely (e.g., it sees "hook blocked Bash" and writes about a git safety issue when the actual blocked command was `python -c "import sys..."`). The LLM pattern-matches on prior context instead of reading the specific artifact.

**The fix**: Deterministic code captures the exact artifact. The LLM must echo it back verbatim. Deterministic code verifies the echo matches. Only then can the LLM narrate freely.

## Existing System Context

You are working in `P:/.claude/hooks/`. The hook system works like this:

### Hook Types & When They Run
- **PreToolUse**: Runs BEFORE a tool executes. Can block execution. Receives `tool_name`, `tool_input` on stdin as JSON.
- **PostToolUse**: Runs AFTER a tool executes. Receives `tool_name`, `tool_input`, `tool_result` on stdin as JSON.
- **Stop**: Runs when the LLM tries to stop. Can block stopping (force continuation).
- **UserPromptSubmit**: Runs when the user sends a message. Can inject context.

### Hook Data Flow (stdin JSON)
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "cd \"P:\\.claude\\hooks\" && python -c \"import sys...\""
  },
  "tool_result": "...",  // Only in PostToolUse
  "session": {
    "id": "session-uuid-here"
  }
}
```

### How Blocking Works
A PreToolUse hook blocks by returning JSON to stdout:
```json
{"decision": "block", "reason": "...", "blocking_hook": "PreToolUse_my_hook.py"}
```
And exiting with code 2. The `reason` field is shown to the LLM.

### How PostToolUse Injects Context
PostToolUse hooks inject context into the LLM's next turn via:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Your message here - this is shown to the LLM"
  }
}
```

### Existing Cross-Hook Communication
Hooks communicate via files in `P:/.claude/hooks/state/` and `P:/.claude/state/signals/`. Files are keyed by session ID to support multiple terminals. Pattern:
```python
import re
session_id = data.get("session", {}).get("id", "") or os.environ.get("CLAUDE_SESSION_ID", "")
safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
artifact_path = STATE_DIR / f"grounded_artifact_{safe_session}.json"
```

### Settings.json Hook Wiring
Hooks are configured in `P:/.claude/settings.json` under the `hooks` key:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/PreToolUse_my_hook.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Key Constraints
1. **stderr = error**: Claude Code treats ANY stderr output from hooks as a hook error. Hooks must NEVER write to stderr. Use stdout for output.
2. **JSON only on stdout**: Hooks output JSON to stdout. Non-JSON stdout is ignored (for allow) or treated as the reason string (for blocks).
3. **Multi-terminal**: Multiple Claude Code terminals may run simultaneously. All state files must be keyed by session ID. No TTL-based expiry (stale data risk). Use explicit write/delete lifecycle.
4. **Performance**: PreToolUse hooks run on EVERY tool call. Keep them fast (< 100ms ideally).
5. **Windows paths**: The system runs on Windows. Use `Path` objects, not string concatenation. Forward slashes work in Python `Path` but backslashes appear in user-visible paths.

## What To Build

### Component 1: Artifact Grounder (writes the struct)

**File**: `P:/.claude/hooks/__lib/artifact_grounder.py`

A pure Python module (no LLM involvement) that extracts a canonical artifact struct from hook data. Called by PreToolUse when it blocks a tool call.

**Schemas** (implement as dataclasses or typed dicts):

```python
# Schema 1: Blocked Tool Command
{
    "schema": "blocked_command",
    "version": 1,
    "timestamp": 1709000000.0,
    "session_id": "abc-123",
    "tool_name": "Bash",
    "tool_input": {
        "command": "cd \"P:\\.claude\\hooks\" && python -c \"import sys...\""
    },
    "blocking_hook": "PreToolUse_authorization_gate.py",
    "raw_reason": "Blocked: command requires authorization",
    "command_tokens": ["cd", "python", "-c", "import", "sys"]  # top 5-10 significant tokens
}

# Schema 2: Test Failure
{
    "schema": "test_failure",
    "version": 1,
    "timestamp": 1709000000.0,
    "session_id": "abc-123",
    "tool_name": "Bash",
    "tool_input": {
        "command": "pytest tests/test_foo.py"
    },
    "exit_code": 1,
    "failing_tests": ["test_foo::test_bar", "test_foo::test_baz"],
    "raw_output_head": "FAILED tests/test_foo.py::test_bar - AssertionError...",
    "test_runner": "pytest"
}

# Schema 3: Git Safety Block
{
    "schema": "git_safety_block",
    "version": 1,
    "timestamp": 1709000000.0,
    "session_id": "abc-123",
    "tool_name": "Bash",
    "tool_input": {
        "command": "git status --porcelain"
    },
    "blocking_hook": "PreToolUse_git_safety.py",
    "git_subcommand": "status",
    "raw_reason": "Git safety gate: Global 'git status' without path limiter"
}
```

**API**:
```python
def ground_blocked_command(data: dict, blocking_hook: str, reason: str) -> dict:
    """Build a grounded artifact struct for a blocked tool command.

    Args:
        data: The hook stdin data (contains tool_name, tool_input, session)
        blocking_hook: Name of the hook that blocked
        reason: The block reason string

    Returns:
        A canonical artifact struct dict
    """

def ground_test_failure(data: dict, exit_code: int, raw_output: str) -> dict:
    """Build a grounded artifact struct for a test failure."""

def ground_git_safety_block(data: dict, blocking_hook: str, reason: str) -> dict:
    """Build a grounded artifact struct for a git safety block."""

def extract_command_tokens(command: str, max_tokens: int = 10) -> list[str]:
    """Extract significant tokens from a command string.

    Strips quotes, paths, and common shell syntax to get meaningful words.
    Used for drift detection (if the RCA talks about concepts not in these tokens,
    it's suspicious).
    """
```

**Storage**: Write the struct to `P:/.claude/hooks/state/grounded_artifact_{safe_session}.json`. Overwrite on each new block (only the latest matters). Delete when the LLM's next tool call succeeds (in PostToolUse).

**Lifecycle (CRITICAL - no TTL)**:
- **Created by**: PreToolUse router (`PreToolUse.py`) when any hook returns a block decision
- **Read by**: PostToolUse validator when it sees an RCA/explanation tool output
- **Deleted by**: PostToolUse when the next successful (non-blocked) tool call happens, OR by SessionEnd cleanup
- **Never expires by time** — only by explicit lifecycle events
- **Multi-terminal safe**: keyed by session ID, so terminal A's artifact doesn't interfere with terminal B

### Component 2: PreToolUse Integration (writes artifact on block)

**File**: Modify `P:/.claude/hooks/PreToolUse.py`

In the existing `main()` function, after a hook returns a block decision (around line 492), add artifact grounding:

```python
# After: if res.get("decision") == "block":
# Add: Ground the artifact
try:
    from __lib.artifact_grounder import ground_blocked_command, ground_git_safety_block

    blocking_hook_name = res.get("blocking_hook", hook)
    reason = res.get("reason", "")

    # Choose schema based on blocking hook
    if "git_safety" in blocking_hook_name.lower():
        artifact = ground_git_safety_block(data, blocking_hook_name, reason)
    else:
        artifact = ground_blocked_command(data, blocking_hook_name, reason)

    # Write to state (session-scoped)
    _write_grounded_artifact(data, artifact)
except Exception:
    pass  # Grounding is best-effort, never block the block
```

Add a helper function:
```python
def _write_grounded_artifact(data: dict, artifact: dict) -> None:
    """Write grounded artifact to session-scoped state file."""
    session_id = _resolve_session_id(data)
    safe_session = _safe_id(session_id or "unknown")

    state_dir = HOOKS_DIR / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
```

### Component 3: PostToolUse Artifact Validator

**File**: `P:/.claude/hooks/PostToolUse_artifact_validator.py`

This hook runs after tool calls and does TWO things:

#### 3A: Inject grounding context when an artifact exists

When there's a grounded artifact from a recent block, inject it into the LLM's context so it HAS the artifact to echo:

```python
def check_and_inject_artifact(data: dict) -> dict | None:
    """If a grounded artifact exists, inject it as context for the LLM."""
    artifact = _read_grounded_artifact(data)
    if not artifact:
        return None

    schema = artifact.get("schema", "unknown")

    if schema == "blocked_command":
        tool_name = artifact.get("tool_name", "?")
        command = artifact.get("tool_input", {}).get("command", "?")
        hook = artifact.get("blocking_hook", "?")
        reason = artifact.get("raw_reason", "?")

        injection = (
            f"GROUNDED ARTIFACT (mechanical - not LLM generated):\n"
            f"  Tool: {tool_name}\n"
            f"  Command: {command}\n"
            f"  Blocked by: {hook}\n"
            f"  Reason: {reason}\n\n"
            f"When explaining this block, you MUST quote the exact command above. "
            f"Do not reference commands or hooks from elsewhere in your context."
        )
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": injection
            }
        }

    return None
```

#### 3B: Cleanup on successful tool call

When a tool call succeeds (not blocked), delete the grounded artifact — the LLM has moved on:

```python
def cleanup_stale_artifact(data: dict) -> None:
    """Delete grounded artifact when the LLM makes a successful tool call."""
    artifact_path = _artifact_path(data)
    if artifact_path and artifact_path.exists():
        artifact_path.unlink(missing_ok=True)
```

#### 3C: Validate RCA output (defense-in-depth)

When the tool output looks like an RCA or explanation (e.g., from a Skill tool call for `/debugRCA`), validate that it references the correct artifact:

```python
def validate_rca_against_artifact(data: dict) -> dict | None:
    """Check if RCA output references the correct grounded artifact.

    Returns None if valid or no artifact. Returns injection message if drift detected.
    """
    artifact = _read_grounded_artifact(data)
    if not artifact:
        return None

    tool_result = str(data.get("tool_result", ""))
    if not tool_result or len(tool_result) < 50:
        return None

    # Only validate if this looks like an RCA/explanation
    rca_markers = ["root cause", "rca", "blocked", "why this happened", "diagnosis"]
    result_lower = tool_result.lower()
    if not any(marker in result_lower for marker in rca_markers):
        return None

    # Check: does the RCA mention the actual command?
    actual_command = artifact.get("tool_input", {}).get("command", "")
    if not actual_command:
        return None

    # Extract a meaningful substring (first 40 chars or first significant segment)
    command_snippet = actual_command[:60]

    if command_snippet not in tool_result:
        # DRIFT DETECTED: RCA doesn't mention the actual command
        # Check concept drift too
        artifact_tokens = set(artifact.get("command_tokens", []))
        if artifact_tokens:
            result_words = set(result_lower.split())
            overlap = artifact_tokens & result_words
            overlap_ratio = len(overlap) / len(artifact_tokens) if artifact_tokens else 0

            if overlap_ratio < 0.3:
                # Strong drift - the RCA is talking about something completely different
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            f"WARNING: Your explanation may reference the wrong artifact.\n"
                            f"The ACTUAL blocked command was: {actual_command}\n"
                            f"The blocking hook was: {artifact.get('blocking_hook', '?')}\n"
                            f"Please verify your explanation matches this specific command."
                        )
                    }
                }

    return None
```

### Component 4: Settings.json Wiring

Add the new PostToolUse hook to the existing config. It should run for all tool types since it needs to both inject context (after blocks) and clean up (after successes):

```json
{
  "PostToolUse": [
    {
      "matcher": ".*",
      "hooks": [
        {
          "type": "command",
          "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PostToolUse_artifact_validator.py",
          "timeout": 5
        }
      ]
    }
  ]
}
```

**IMPORTANT**: This must be ADDED to the existing PostToolUse hooks, not replace them. The existing `Edit|Write` and `Bash` matchers stay. This new `.*` matcher runs in addition to them.

### Component 5: SessionEnd Cleanup

**File**: Modify `P:/.claude/hooks/SessionEnd_cleanup.py`

Add cleanup of grounded artifact files:

```python
# In the cleanup logic, add:
import glob

state_dir = Path("P:/.claude/hooks/state")
for artifact_file in state_dir.glob("grounded_artifact_*.json"):
    try:
        artifact_file.unlink(missing_ok=True)
    except Exception:
        pass
```

## Detailed Implementation Notes

### Multi-Terminal Safety

Every state file is keyed by session ID:
```
grounded_artifact_{safe_session_id}.json
```

Session ID resolution (copy this pattern from existing hooks):
```python
def _resolve_session_id(data: dict) -> str:
    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in ("session_id", "sessionId", "CLAUDE_SESSION_ID"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_SESSION_ID", "").strip()

def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)
```

### No TTL - Explicit Lifecycle Only

**DO NOT** use timestamp-based expiry. The artifact is:
- Created when a tool call is blocked
- Deleted when the next tool call succeeds
- Deleted on session end

This is immune to stale data because:
- Each session has its own file (multi-terminal safe)
- Success clears the file (no orphans during normal flow)
- SessionEnd cleans up (no orphans from crashed sessions)

### Error Handling Philosophy

All GAV code is **best-effort, never-blocking**:
- If grounding fails → the block still happens, just without the artifact
- If validation fails → the RCA still shows, just without the drift warning
- If cleanup fails → worst case is an extra artifact file that gets cleaned up on session end
- NEVER write to stderr (Claude Code treats it as hook error)
- Wrap everything in try/except with `pass`

### Token Extraction for Drift Detection

```python
import shlex
import re

def extract_command_tokens(command: str, max_tokens: int = 10) -> list[str]:
    """Extract significant tokens from a shell command."""
    # Remove path prefixes
    cleaned = re.sub(r'[A-Z]:\\[^\s"]*\\', '', command)  # Windows paths
    cleaned = re.sub(r'/[^\s"]*/', '', cleaned)  # Unix paths

    # Remove quotes and common shell syntax
    cleaned = re.sub(r'["\']', '', cleaned)
    cleaned = re.sub(r'[|&;><]', ' ', cleaned)

    # Split and filter
    words = cleaned.split()
    stopwords = {'cd', 'echo', '&&', '||', '--', '-c', '-e', '-f'}
    tokens = [w.lower() for w in words if len(w) > 1 and w.lower() not in stopwords]

    # Deduplicate preserving order
    seen = set()
    unique = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique[:max_tokens]
```

## Testing Plan

### Unit Tests

**File**: `P:/.claude/hooks/tests/test_artifact_validation_hooks.py`

NOTE: This file already exists. Check its contents first — extend it rather than overwrite.

```python
import json
import pytest
from pathlib import Path

# Test artifact_grounder
class TestArtifactGrounder:
    def test_ground_blocked_command_basic(self):
        """Basic blocked command grounding."""
        from __lib.artifact_grounder import ground_blocked_command

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": 'python -c "import sys; print(sys.version)"'},
            "session": {"id": "test-session-1"}
        }
        result = ground_blocked_command(data, "PreToolUse_auth.py", "Requires auth")

        assert result["schema"] == "blocked_command"
        assert result["tool_name"] == "Bash"
        assert "python" in result["tool_input"]["command"]
        assert result["blocking_hook"] == "PreToolUse_auth.py"

    def test_ground_blocked_command_preserves_exact_command(self):
        """The command in the artifact must be EXACTLY what was in tool_input."""
        from __lib.artifact_grounder import ground_blocked_command

        cmd = 'cd "P:\\.claude\\hooks" && python -c "import sys; print(42)"'
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": cmd},
            "session": {"id": "test-session-2"}
        }
        result = ground_blocked_command(data, "hook.py", "blocked")
        assert result["tool_input"]["command"] == cmd  # EXACT match

    def test_extract_command_tokens(self):
        """Token extraction gets meaningful words."""
        from __lib.artifact_grounder import extract_command_tokens

        tokens = extract_command_tokens('python -c "import sys; print(sys.version)"')
        assert "python" in tokens
        assert "import" in tokens or "sys" in tokens

    def test_ground_git_safety_block(self):
        """Git safety blocks include subcommand."""
        from __lib.artifact_grounder import ground_git_safety_block

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status --porcelain"},
            "session": {"id": "test-session-3"}
        }
        result = ground_git_safety_block(data, "PreToolUse_git_safety.py", "no path limiter")
        assert result["schema"] == "git_safety_block"
        assert result["git_subcommand"] == "status"

# Test artifact lifecycle
class TestArtifactLifecycle:
    def test_write_and_read_artifact(self, tmp_path):
        """Artifact can be written and read back."""
        # Use tmp_path as state dir to avoid polluting real state
        artifact = {"schema": "blocked_command", "tool_name": "Bash", "session_id": "test"}
        path = tmp_path / "grounded_artifact_test.json"
        path.write_text(json.dumps(artifact))

        loaded = json.loads(path.read_text())
        assert loaded["schema"] == "blocked_command"

    def test_cleanup_removes_artifact(self, tmp_path):
        """Successful tool call removes the artifact."""
        path = tmp_path / "grounded_artifact_test.json"
        path.write_text('{"schema": "blocked_command"}')
        assert path.exists()

        path.unlink(missing_ok=True)
        assert not path.exists()

# Test drift detection
class TestDriftDetection:
    def test_no_drift_when_command_mentioned(self):
        """No drift warning when RCA mentions the actual command."""
        artifact = {
            "tool_input": {"command": "python -c \"import sys\""},
            "command_tokens": ["python", "import", "sys"]
        }
        rca_text = "The command `python -c \"import sys\"` was blocked because..."

        # command_snippet is in rca_text → no drift
        assert artifact["tool_input"]["command"][:60] in rca_text

    def test_drift_when_wrong_command(self):
        """Drift detected when RCA talks about a different command."""
        artifact = {
            "tool_input": {"command": "python -c \"import sys\""},
            "command_tokens": ["python", "import", "sys"]
        }
        rca_text = "The global git status command was blocked by the git safety gate..."

        # command_snippet NOT in rca_text → drift
        assert artifact["tool_input"]["command"][:60] not in rca_text

        # Token overlap check
        result_words = set(rca_text.lower().split())
        overlap = set(artifact["command_tokens"]) & result_words
        ratio = len(overlap) / len(artifact["command_tokens"])
        assert ratio < 0.3  # Low overlap = high drift
```

### End-to-End Test (Manual)

1. Trigger a PreToolUse block (e.g., run a command that gets blocked by authorization)
2. Check that `P:/.claude/hooks/state/grounded_artifact_*.json` was created
3. Check that the next LLM response includes the injected artifact context
4. Run a successful tool call and verify the artifact file is deleted

## Rollout Plan

### Phase 1: Grounder + Injection (low risk)
1. Create `P:/.claude/hooks/__lib/artifact_grounder.py`
2. Modify `PreToolUse.py` to write artifacts on block
3. Create `PostToolUse_artifact_validator.py` with injection + cleanup only (NO validation yet)
4. Wire in settings.json
5. Test: blocks should now inject artifact context

### Phase 2: Drift Detection (medium risk)
1. Add the validation logic to `PostToolUse_artifact_validator.py`
2. Start in **warning mode** only (inject warnings, don't block)
3. Monitor for false positives over several sessions
4. Tune token extraction and drift thresholds

### Phase 3: Extend to Test Failures
1. Add test failure grounding to PostToolUse (when Bash output contains pytest/jest failures)
2. Same inject → validate pattern
3. New schema, same lifecycle

### Phase 4: Extend to Other Schemas
1. Git safety blocks (dedicated schema)
2. Linter/type-checker output
3. Build failures

## Limitations

### What This Fixes
- LLM writes RCA about wrong command/tool (the exact bug that triggered this design)
- LLM fabricates evidence from prior context instead of the actual artifact
- LLM names the wrong blocking hook

### What This Does NOT Fix
- LLM correctly identifies the command but gives wrong diagnosis (right artifact, wrong reasoning)
- LLM hallucinations within the correct scope (e.g., invents a reason that sounds plausible but is wrong)
- Subtle misattribution where the echo passes substring check but the analysis is still associative
- Cases with no clear artifact to ground on (vague questions, architectural discussions)

### Tradeoffs
- **Performance**: One extra file write on block + one file read on every PostToolUse. Both are < 1ms. Acceptable.
- **False positives in drift detection**: The substring + token overlap check is heuristic. May flag valid RCAs that paraphrase heavily. Start in warning mode to tune.
- **Complexity**: Adds ~3 files and ~200 lines of code. The alternative (more prompt text) has been tried and failed.

## File Summary

| File | Action | Purpose |
|------|--------|---------|
| `P:/.claude/hooks/__lib/artifact_grounder.py` | CREATE | Deterministic artifact struct builder |
| `P:/.claude/hooks/PostToolUse_artifact_validator.py` | CREATE | Injection + cleanup + drift detection |
| `P:/.claude/hooks/PreToolUse.py` | MODIFY | Write artifact on block (add ~15 lines) |
| `P:/.claude/hooks/PostToolUse.py` | MODIFY | Delete artifact on success (add ~5 lines) |
| `P:/.claude/hooks/SessionEnd_cleanup.py` | MODIFY | Clean up orphaned artifacts |
| `P:/.claude/settings.json` | MODIFY | Wire new PostToolUse hook |
| `P:/.claude/hooks/tests/test_artifact_validation_hooks.py` | MODIFY/EXTEND | Unit tests |
