# Research Intelligence: Zen Suggestion Hook

## Task: TSK-251230-1639-zen-hook
**Date**: 2025-12-30
**Status**: Research Complete

---

## 1. Existing Hook Patterns Analysis

### 1.1 UserPromptSubmit Hook Structure

**Source**: `P:/.claude/hooks/user_prompt_submit_cks.py`

**Key Patterns Discovered**:

```python
#!/usr/bin/env python3
# Standard shebang for executable hooks

import json
import sys
from pathlib import Path
from typing import Any

# Hook Entry Point Pattern
def main():
    """Hook entry point - receives JSON from Claude Code."""
    try:
        # Read input from Claude Code
        input_data = json.loads(sys.stdin.read())

        # Extract fields from input (flexible field matching)
        prompt = input_data.get("prompt") or input_data.get("message") or input_data.get("content", "")

        # Process and modify input_data directly
        # (CKS injects context into input_data["prompt"])

        # Output: Always return input_data (modified or not)
        print(json.dumps(input_data))
        sys.exit(0)

    except Exception as e:
        # Error handling: Log to stderr, don't block
        print(f"Error in hook: {e}", file=sys.stderr)
        sys.exit(0)  # Non-blocking exit
```

**Critical Observations**:
1. **Input format**: JSON via stdin
2. **Field flexibility**: Check `prompt`, `message`, `content` fields
3. **Output format**: JSON dump of (possibly modified) input_data
4. **Exit code**: Always 0 (non-blocking)
5. **Error handling**: stderr for errors, stdout for data

### 1.2 Hook Registration Pattern

**Source**: `P:/.claude/settings.json`

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/user_prompt_submit_cks.py",
            "timeout": 3,
            "layer": "1d_cks_integration",
            "critical": false,
            "description": "Layer 1d: CKS integration for contextual memory"
          }
        ]
      }
    ]
  }
}
```

**Key Fields**:
- `matcher`: `".*"` for all prompts (could be regex for specific patterns)
- `type`: `"command"` for script execution
- `command`: Full path to Python script
- `timeout`: Milliseconds (3 for CKS, 1-2 for simpler hooks)
- `critical`: If true, hook errors are more significant
- `layer`: Ordering string for hook execution sequence
- `description`: Human-readable purpose

### 1.3 Pattern Detection Pattern

**Source**: `P:/.claude/hooks/PostToolUse_system2.py`

```python
import re
from typing import Final

# Compiled pattern constants (performance optimization)
ERROR_PATTERNS: Final = [
    (r"(?i)command not found", "command_not_found"),
    (r"(?i)is not recognized as an", "command_not_found"),
    (r"(?i)exit code (?:[1-9]|\d{2,})", "nonzero_exit"),
    (r"(?i)traceback\s*\(most\s*recent", "python_exception"),
    (r"(?i)error:", "generic_error"),
]

def detect_error_patterns(output: str) -> list[str]:
    """Check output against known error patterns."""
    found = []
    for pattern, name in ERROR_PATTERNS:
        if re.search(pattern, output):
            found.append(name)
    return found
```

**Key Patterns**:
1. **Tuple-based patterns**: `(regex, name)` for extensibility
2. **Case-insensitive regex**: `(?i)` flag for user input
3. **Compiled constants**: `Final` type annotation for immutability
4. **Simple function**: Returns list of matched names

### 1.4 Severity Classification Pattern

**Source**: `P:/.claude/hooks/PostToolUse_system2.py`

```python
def classify_severity(output: str) -> str:
    """
    Classify error severity to prevent advisory warnings from
    overshadowing real errors.

    CRITICAL: Exit codes, hard failures, things that prevent execution
    WARNING: Advisory messages, structural issues, things that are nice to fix
    IGNORE: Informational output
    """
    output_lower = output.lower()

    # CRITICAL: Exit codes, actual errors, exceptions
    if re.search(r"exit code [1-9]", output_lower):
        return "CRITICAL"
    if "error:" in output_lower and "warning:" not in output_lower:
        return "CRITICAL"
    if "traceback" in output_lower or "exception" in output_lower:
        return "CRITICAL"

    # WARNING: Advisory messages, structural issues
    if "warning:" in output_lower:
        return "WARNING"
    if "advisory" in output_lower:
        return "WARNING"

    # IGNORE: Normal output
    return "IGNORE"
```

**Key Patterns**:
1. **Tiered classification**: CRITICAL > WARNING > IGNORE
2. **Case normalization**: Convert to lowercase once
3. **Early returns**: Exit at first match (priority order)
4. **Clear documentation**: Docstring explains each tier

### 1.5 Goal Alignment Pattern

**Source**: `P:/.claude/hooks/pre_action_alignment.py`

```python
import json
import sys
from pathlib import Path

GOAL_STATE_FILE = Path("P:/.claude/session_data/goal_state.json")

def read_session_goal() -> str:
    """Read the current session goal from persistence."""
    try:
        if GOAL_STATE_FILE.exists():
            with open(GOAL_STATE_FILE) as f:
                data = json.load(f)
                return data.get("goal", "")
    except (OSError, json.JSONDecodeError):
        pass
    return ""

def check_alignment(tool_name: str, tool_input: dict, session_goal: str) -> dict:
    """
    Check if tool action aligns with session goal.

    Returns:
        {"action": "continue"} - Proceed
        {"action": "warn", "message": "..."} - Show warning
        {"action": "block", "message": "..."} - Block
    """
    if not session_goal:
        return {"action": "continue"}

    # Pattern matching logic...
    return {"action": "continue"}
```

**Key Patterns**:
1. **State persistence**: File-based session state
2. **Graceful degradation**: Return empty on errors
3. **Action-based responses**: `continue`, `warn`, `block`
4. **Null-safety**: Check if goal exists before processing

### 1.6 Logging Pattern

**Observed across multiple hooks**:

```python
from datetime import UTC, datetime
from pathlib import Path

log_dir = Path(".claude/logs")
log_dir.mkdir(parents=True, exist_ok=True)

def log_event(event_type: str, data: dict):
    """Append-only JSON logging."""
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event_type,
        **data
    }
    try:
        with open(log_dir / "hook_events.json", "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Non-blocking
```

**Key Patterns**:
1. **Append-only**: `"a"` mode for sequential writes
2. **One JSON per line**: Newline-delimited for `jq` analysis
3. **ISO timestamps**: UTC for consistency
4. **Silent failures**: Never block on logging errors

---

## 2. String Escaping Gotchas (Critical)

### 2.1 The Problem

From `HOOK_FIXES_SITREP.md`:
> Earlier Python fix scripts used `readlines()` which preserved `\r\n` line endings.
> When code was inserted, it created malformed string literals with actual newlines
> instead of `\n` escape sequences.

### 2.2 The Solution

```python
# WRONG - Creates literal newline:
f"Error: {error_type}\n")  # If \r\n preserved, this breaks

# RIGHT - Use hex escape:
content = b'f"Error: {error_type}\\x5cn")'
# Where \x5c = backslash (ASCII 92)
```

### 2.3 Template Pattern for Zen Hook

```python
# When writing the zen_suggestion.py hook, use this pattern:
print(f"💡 Zen suggestion: {suggestion}\\n")  # Explicit \\n

# NOT:
print(f"💡 Zen suggestion: {suggestion}
")  # Literal newline breaks syntax
```

---

## 3. Configuration File Pattern

### 3.1 JSON Structure (from decider/claude-hooks)

```json
{
  "enabled": true,
  "patterns": {
    "tier1": [
      {
        "name": "pattern_id",
        "regex": "pattern_string",
        "suggestion": "/zen-command",
        "confidence": "HIGH"
      }
    ],
    "tier2": [...]
  },
  "settings": {
    "min_confidence": "HIGH",
    "context_lookback": 3
  }
}
```

### 3.2 Config Loading Pattern

```python
from pathlib import Path
import json

DEFAULT_CONFIG = {
    "enabled": False,
    "patterns": {"tier1": [], "tier2": []},
    "min_confidence": "HIGH"
}

def load_config(config_path: Path) -> dict:
    """Load config with fallback to defaults."""
    try:
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    return DEFAULT_CONFIG.copy()
```

---

## 4. Zen Hook Specific Patterns

### 4.1 Tiered Pattern Matching

```python
from typing import Optional
import re

class ZenSuggestionHook:
    def detect_zen_patterns(self, message: str) -> Optional[str]:
        """Detect high-confidence zen patterns in current message."""

        # Check Tier 1 (highest priority)
        for pattern in self.config.get("patterns", {}).get("tier1", []):
            if self._matches_pattern(message, pattern):
                return pattern["suggestion"]

        # Check Tier 2 if Tier 1 didn't match
        for pattern in self.config.get("patterns", {}).get("tier2", []):
            if self._matches_pattern(message, pattern):
                return pattern["suggestion"]

        return None

    def _matches_pattern(self, text: str, pattern_config: dict) -> bool:
        """Check if text matches pattern with case-insensitive regex."""
        regex = pattern_config.get("regex", "")
        if not regex:
            return False
        try:
            return bool(re.search(regex, text, re.IGNORECASE))
        except re.error:
            return False
```

### 4.2 Context Analysis Pattern

```python
from typing import List

def analyze_context(self, messages: List[str]) -> Optional[str]:
    """Analyze last 2-3 messages for weak signals."""

    if not messages or len(messages) < 2:
        return None

    # Pattern: Circular discussion (same question multiple ways)
    if self._is_circular_discussion(messages):
        return "/zen-meditate"

    # Pattern: Refinement of architecture decision
    if self._is_architecture_refinement(messages):
        return "/zen-debate"

    return None

def _is_circular_discussion(self, messages: List[str]) -> bool:
    """Detect if same question is being asked multiple ways."""
    question_count = sum(1 for msg in messages[-3:] if '?' in msg)
    return question_count >= 2

def _is_architecture_refinement(self, messages: List[str]) -> bool:
    """Check if previous turns discussed architecture."""
    arch_keywords = ["microservice", "monolith", "architecture", "design", "pattern"]
    recent = " ".join(messages[-2:])
    return any(kw in recent.lower() for kw in arch_keywords)
```

### 4.3 Suggestion Cache Pattern

```python
from collections import deque
from time import time

class ZenSuggestionHook:
    def __init__(self):
        self.suggestion_cache = deque(maxlen=5)
        self.suggestion_timestamps = {}

    def should_skip_suggestion(self, suggestion: str) -> bool:
        """Don't suggest if one was just given (within cache duration)."""
        now = time()

        # Check if this exact suggestion was given recently
        if suggestion in self.suggestion_timestamps:
            elapsed = now - self.suggestion_timestamps[suggestion]
            if elapsed < 30:  # 30 second cooldown
                return True

        return False

    def record_suggestion(self, suggestion: str):
        """Record that a suggestion was made."""
        self.suggestion_cache.append(suggestion)
        self.suggestion_timestamps[suggestion] = time()
```

---

## 5. Integration with Existing Hook System

### 5.1 Layer Ordering

From `settings.json` analysis, hooks execute in this order:
1. Layer 0: Diagnostics, prompt tracking
2. Layer 1: Command directives, goal anchor, ADF trigger, anti-sycophancy
3. Layer 1d: CKS integration
4. Layer 1e: Debug guidance

**Zen hook should be**: Layer 1f (after other context injection, before processing)

### 5.2 Hook Registration Template

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/zen_suggestion.py",
            "timeout": 1,
            "layer": "1f_zen_suggestions",
            "critical": false,
            "description": "Layer 1f: Suggest zen commands at decision points",
            "exit_code_error_handling": "non_blocking"
          }
        ]
      }
    ]
  }
}
```

### 5.3 Output Format (Non-Blocking)

Unlike CKS which modifies `input_data`, zen hook should output suggestion directly:

```python
# Zen hook output pattern (stdout):
if suggestion:
    print(f"💡 Zen suggestion: {suggestion}")
    sys.exit(0)
else:
    # No suggestion - silent exit
    sys.exit(0)
```

---

## 6. Test Patterns

### 6.1 Unit Test Structure

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from zen_suggestion import ZenSuggestionHook

def test_architecture_decision():
    hook = ZenSuggestionHook()
    result = hook.detect_zen_patterns("Should I use microservices or monolith?")
    assert result == "/zen-debate"

def test_stuck_unclear():
    hook = ZenSuggestionHook()
    result = hook.detect_zen_patterns("I'm stuck on how to proceed")
    assert result == "/zen-meditate"

def test_no_match():
    hook = ZenSuggestionHook()
    result = hook.detect_zen_patterns("What's in this directory?")
    assert result is None

if __name__ == "__main__":
    test_architecture_decision()
    test_stuck_unclear()
    test_no_match()
    print("✓ All tests passed")
```

### 6.2 Manual Testing via stdin

```bash
# Test the hook directly
echo '{"prompt":"Should I use microservices?","context_messages":[]}' \
  | python P:/.claude/hooks/zen_suggestion.py

# Expected: 💡 Zen suggestion: /zen-debate
```

---

## 7. Implementation Recommendations

### 7.1 File Structure

```
P:/.claude/
├── config/
│   └── zen_suggestions.json    # Pattern library (create new)
├── hooks/
│   └── zen_suggestion.py        # Hook implementation (create new)
├── logs/
│   └── zen_suggestions.json    # Execution logs (auto-created)
└── settings.json                # Hook registration (modify)
```

### 7.2 Minimal Viable Pattern Set (Phase 1)

Start with 3 core Tier 1 patterns:
1. Architecture decision: `(should|whether to).*(microservices|monolith)` → `/zen-debate`
2. Stuck/Unclear: `(stuck|blocked|unclear).*(how|what|why)` → `/zen-meditate`
3. Code review: `(review|look at).*(code|changes)` → `/zen-code-review`

### 7.3 Success Criteria

- Hook compiles without syntax errors
- Hook executes on every UserPromptSubmit
- Suggestion appears for architecture questions
- No output for generic queries
- Exit code always 0
- Execution time < 100ms

---

## 8. Risks and Mitigations

### Risk: Pattern Too Broad
**Mitigation**: Start with 3-5 specific patterns, monitor logs

### Risk: String Escaping Errors
**Mitigation**: Use explicit `\\n` in f-strings, verify with `py_compile`

### Risk: Hook Timeout
**Mitigation**: Keep regex compilation cached, minimize I/O

### Risk: False Positives
**Mitigation**: Require multiple keywords (e.g., "should" + "microservices")

---

## Research Summary

**Patterns Adopted**:
1. Hook entry point from `user_prompt_submit_cks.py`
2. Pattern detection from `PostToolUse_system2.py`
3. Configuration structure from `decider/claude-hooks` (GitHub reference)
4. Tiered classification from severity pattern
5. Logging pattern from multiple hooks

**Key Technical Decisions**:
- JSON config for patterns (no code changes for evolution)
- Tier 1 > Tier 2 > Context fallback priority
- 30-second suggestion cache to prevent spam
- Non-blocking exit (always exit 0)
- One-line output format: `💡 Zen suggestion: /zen-command`

**Ready for**: Step 4 - Architecture Analysis

---

**Research Status**: ✅ COMPLETE
