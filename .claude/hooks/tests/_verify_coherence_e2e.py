#!/usr/bin/env python3
"""End-to-end verification of first-tool coherence flow."""

import os
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "PreToolUse"))

os.environ["CLAUDE_TERMINAL_ID"] = "test_coherence_e2e"

from PreToolUse_skill_pattern_gate import _check_first_tool_coherence
from skill_guard.skill_execution_state import clear_state, read_pending_state, set_skill_loaded

# Clean any stale state
clear_state()

# === SCENARIO 1: /ask blocks Bash, allows Grep ===
print("=== SCENARIO 1: /ask ===")
set_skill_loaded("ask")
state = read_pending_state()
assert state is not None, "State should exist after set_skill_loaded"
assert state["skill"] == "ask"
assert state["allowed_first_tools"] == ["Grep", "Glob", "Read", "Task", "WebSearch"]
assert state["first_tool_validated"] is False
print("  State created correctly")

# Bash should be BLOCKED as first tool
result = _check_first_tool_coherence("Bash", state)
assert result.get("block"), f"Bash should be blocked for /ask, got: {result}"
print("  Bash blocked: OK")

# Grep should PASS as first tool
result2 = _check_first_tool_coherence("Grep", state)
assert not result2.get("block"), f"Grep should be allowed for /ask, got: {result2}"
print("  Grep allowed: OK")

# After validation, state should show first_tool_validated=True
state2 = read_pending_state()
assert state2["first_tool_validated"] is True, "first_tool_validated should be True after Grep"
print("  first_tool_validated=True: OK")

# Now Bash should be allowed (first tool already validated)
result3 = _check_first_tool_coherence("Bash", state2)
assert not result3.get("block"), f"Bash should be allowed after validation, got: {result3}"
print("  Bash allowed after validation: OK")

clear_state()

# === SCENARIO 2: /test allows Bash ===
print("\n=== SCENARIO 2: /test ===")
set_skill_loaded("test")
state = read_pending_state()
assert state is not None
assert "Bash" in state["allowed_first_tools"]

result = _check_first_tool_coherence("Bash", state)
assert not result.get("block"), f"Bash should be allowed for /test, got: {result}"
print("  Bash allowed for /test: OK")

clear_state()

# === SCENARIO 3: /standards (no allowed_first_tools) - no state created ===
print("\n=== SCENARIO 3: /standards (no enforcement) ===")
set_skill_loaded("standards")
state = read_pending_state()
assert state is None, f"Standards should NOT create state, got: {state}"
print("  No state for /standards: OK")

# === SCENARIO 4: Skill not loaded - no enforcement ===
print("\n=== SCENARIO 4: No skill loaded ===")
clear_state()
result = _check_first_tool_coherence("Bash", {})
assert not result.get("block"), "Should allow when no allowed_first_tools"
print("  No enforcement without state: OK")

# === SCENARIO 5: /discover blocks Edit ===
print("\n=== SCENARIO 5: /discover ===")
set_skill_loaded("discover")
state = read_pending_state()
assert state is not None
result = _check_first_tool_coherence("Edit", state)
assert result.get("block"), f"Edit should be blocked for /discover, got: {result}"
print("  Edit blocked for /discover: OK")

result2 = _check_first_tool_coherence("Glob", state)
assert not result2.get("block"), f"Glob should be allowed for /discover, got: {result2}"
print("  Glob allowed for /discover: OK")

clear_state()

print("\n=== ALL E2E CHECKS PASSED ===")
