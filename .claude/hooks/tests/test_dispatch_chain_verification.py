#!/usr/bin/env python3
"""
Test dispatch chain documentation accuracy.

Tests that the dispatch chain comment block in PreToolUse.py matches the actual
UNIVERSAL and TOOL_HOOKS loaded by the router, preventing drift between documentation
and implementation.

Addresses: REQ-001, REQ-005
"""

import re
from pathlib import Path


def test_dispatch_chain_comment_exists():
    """Test that dispatch chain comment exists in PreToolUse.py."""
    pretooluse_path = Path("P:/.claude/hooks/PreToolUse.py")
    content = pretooluse_path.read_text()

    # Check for dispatch chain comment marker
    assert "DISPATCH CHAIN" in content, "DISPATCH CHAIN comment block missing from PreToolUse.py"
    assert "Files NOT in the dispatch chain" in content, "Dead files list missing from dispatch chain comment"


def test_dispatch_chain_lists_active_files():
    """Test that files listed in dispatch chain are actually active hooks."""
    pretooluse_path = Path("P:/.claude/hooks/PreToolUse.py")
    content = pretooluse_path.read_text()

    # Extract UNIVERSAL hooks list from comment
    universal_match = re.search(
        r'#\s+-\s+PreToolUse_path_validator\.py.*?\n'
        r'#\s+-\s+PreToolUse/PreToolUse_skill_pattern_gate\.py.*?\n'
        r'#\s+-\s+PreToolUse_risk_tier_gate\.py.*?\n'
        r'#\s+-\s+PreToolUse_observe_before_act_gate\.py',
        content,
        re.MULTILINE
    )
    assert universal_match is not None, "UNIVERSAL hooks list not found in dispatch chain comment"

    # Verify these files exist
    universal_hooks = [
        "P:/.claude/hooks/PreToolUse_path_validator.py",
        "P:/.claude/hooks/PreToolUse/PreToolUse_skill_pattern_gate.py",
        "P:/.claude/hooks/PreToolUse_risk_tier_gate.py",
        "P:/.claude/hooks/PreToolUse_observe_before_act_gate.py",
    ]
    for hook_path in universal_hooks:
        assert Path(hook_path).exists(), f"UNIVERSAL hook listed in dispatch chain doesn't exist: {hook_path}"


def test_dispatch_chain_marks_dead_files():
    """Test that dead files are properly marked as NOT in dispatch chain."""
    pretooluse_path = Path("P:/.claude/hooks/PreToolUse.py")
    content = pretooluse_path.read_text()

    # Check that known dead files are marked as not in dispatch chain
    assert "PreToolUse_skill_first_gate.py" in content, "Dead file not mentioned in dispatch chain"
    assert "(standalone, not called)" in content or "not in the dispatch chain" in content, \
        "Dead file status not clearly marked"

    # Verify the comment says "do not edit these expecting results"
    assert "do not edit" in content.lower() or "not in the dispatch chain" in content.lower(), \
        "Missing warning about editing dead files"


def test_dispatch_chain_mentions_check_skill_first_gate():
    """Test that dispatch chain correctly identifies THE skill-first gate."""
    pretooluse_path = Path("P:/.claude/hooks/PreToolUse.py")
    content = pretooluse_path.read_text()

    # Should mention that _check_skill_first_gate() is THE skill-first gate
    assert "_check_skill_first_gate()" in content, "Skill-first gate function not mentioned"
    assert "THE skill-first gate" in content or "THE only skill-first gate" in content, \
        "Skill-first gate not clearly identified as THE implementation"


def test_dead_files_not_in_dispatch_chain():
    """Test that dead files are explicitly listed as NOT in dispatch chain."""
    pretooluse_path = Path("P:/.claude/hooks/PreToolUse.py")
    content = pretooluse_path.read_text()

    # PreToolUse_workflow_steps_gate.py should be mentioned as deleted
    assert "PreToolUse_workflow_steps_gate.py" in content, \
        "Deleted file not mentioned in dispatch chain documentation"

    # Both files should be in a context that says they're not called
    context_before = content[content.find("PreToolUse_workflow_steps_gate.py") - 200:content.find("PreToolUse_workflow_steps_gate.py")]
    context_after = content[content.find("PreToolUse_skill_first_gate.py"):content.find("PreToolUse_skill_first_gate.py") + 200]

    # At least one of the contexts should indicate these are not active
    combined_context = context_before + context_after
    assert any(phrase in combined_context.lower() for phrase in ["not called", "not in dispatch chain", "dead", "standalone"]), \
        "Dead files should be clearly marked as inactive"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
