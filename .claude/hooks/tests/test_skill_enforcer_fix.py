#!/usr/bin/env python3
"""Test skill_enforcer after removing pre-execution injection."""

import sys
from pathlib import Path

# Add hooks to path
hooks_dir = Path("P:/.claude/hooks")
sys.path.insert(0, str(hooks_dir))

# Import after path setup
from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.skill_enforcer import build_command_context


def test_skill_enforcer_forces_tool_call():
    """Test that skill_enforcer forces Skill() tool calls, not content injection."""
    print("Testing skill_enforcer behavior...")
    print()

    # Test with /gto command
    context = HookContext(prompt="/gto", data={})
    result = build_command_context("gto", "", context)

    print("=== Skill Enforcer Output ===")
    print(result)
    print()

    # Check what's in the output
    has_instruction = "INSTRUCTION: Execute skill" in result
    has_skill_call = "Skill(" in result or 'Skill("' in result
    has_pre_execution = "⚡ SKILL LOADED" in result or "SKILL LOADED:" in result
    has_workflow_steps = "workflow_steps" in result

    print("=== Analysis ===")
    print(f"✓ Contains INSTRUCTION: Execute skill: {has_instruction}")
    print(f"✓ Forces Skill() tool call: {has_skill_call}")
    print(f"✗ Contains pre-execution injection: {has_pre_execution}")
    print(f"✓ Has workflow_steps advisory: {has_workflow_steps}")
    print()

    # Verify expectations
    if has_instruction and has_skill_call and not has_pre_execution:
        print("✅ SUCCESS: Skill enforcer now forces actual Skill() tool calls")
        print("   - INSTRUCTION present: tells AI to call Skill()")
        print("   - SLASH_EXECUTION_LANE template used (EVALUATION_DIRECTIVE removed)")
        print("   - Pre-execution injection removed: no content bypass")
        return True
    else:
        print("❌ FAIL: Unexpected behavior")
        if not has_instruction:
            print("   - Missing INSTRUCTION")
        if not has_skill_call:
            print("   - Missing Skill() call directive")
        if has_pre_execution:
            print("   - Still doing pre-execution injection (should be removed)")
        return False


if __name__ == "__main__":
    success = test_skill_enforcer_forces_tool_call()
    sys.exit(0 if success else 1)
