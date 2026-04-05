"""Integration tests for pre-mortem adversarial agent dispatch.

Validates that:
1. All 8 adversarial agents exist and are dispatchable
2. Agent prompts follow the token-efficient pattern (file paths, not full content)
3. Agent types match the documented set in SKILL.md
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def test_all_adversarial_agents_exist() -> dict[str, Any]:
    """Verify all 8 adversarial agents exist in the agents directory.

    Returns:
        Test results with status and list of missing agents
    """
    # The pre-mortem skill is in user settings: C:\Users\brsth\.claude\skills\pre-mortem
    # But the agents are in the project: P:\.claude\agents
    # We need to find the project root from the current working directory

    # Try multiple possible locations for agents
    possible_agent_dirs = [
        Path.cwd() / ".claude" / "agents",  # P:\.claude\agents (project root)
        Path("P:/") / ".claude" / "agents",  # Explicit P:\.claude\agents
        Path.home() / ".claude" / "agents",  # User settings fallback
    ]

    expected_agents = [
        "adversarial-compliance",
        "adversarial-logic",
        "adversarial-performance",
        "adversarial-security",
        "adversarial-testing",
        "adversarial-quality",
        "adversarial-critic",
        "adversarial-qa",
    ]

    # Find the first agent directory that exists
    agents_dir = None
    for dir_path in possible_agent_dirs:
        if (dir_path / "adversarial-compliance.md").exists():
            agents_dir = dir_path
            break

    if agents_dir is None:
        return {
            "status": "FAIL",
            "missing_agents": expected_agents,
            "expected_count": len(expected_agents),
            "found_count": 0,
            "checked_directories": [str(d) for d in possible_agent_dirs],
            "reason": "No agent directory found",
        }

    missing_agents = []
    for agent in expected_agents:
        agent_file = agents_dir / f"{agent}.md"
        if not agent_file.exists():
            missing_agents.append(agent)

    return {
        "status": "PASS" if not missing_agents else "FAIL",
        "missing_agents": missing_agents,
        "expected_count": len(expected_agents),
        "found_count": len(expected_agents) - len(missing_agents),
        "checked_directory": str(agents_dir),
    }


def test_skill_md_documents_correct_agents() -> dict[str, Any]:
    """Verify SKILL.md documents the correct 8 adversarial agents.

    Returns:
        Test results with status and any discrepancies found
    """
    skill_path = Path.home() / ".claude" / "skills" / "pre-mortem" / "SKILL.md"

    if not skill_path.exists():
        return {
            "status": "SKIP",
            "reason": "SKILL.md not found",
        }

    content = skill_path.read_text(encoding="utf-8")

    # Expected agent types in SKILL.md Step 7
    expected_patterns = [
        r"adversarial-compliance",
        r"adversarial-logic",
        r"adversarial-performance",
        r"adversarial-security",
        r"adversarial-testing",
        r"adversarial-quality",
        r"adversarial-critic",
        r"adversarial-qa",
    ]

    missing_in_doc = []
    for pattern in expected_patterns:
        if pattern not in content:
            missing_in_doc.append(pattern)

    # Check for deprecated agent types in Step 7 (exclude version history)
    # Find Step 7 section to limit search scope
    step_7_match = re.search(
        r"\*\*Step 7\*\*:.*?(?=\*\*Step \d+|\Z|\Z)", content, re.DOTALL | re.IGNORECASE
    )
    step_7_content = step_7_match.group(0) if step_7_match else ""

    deprecated_agents = ["code-critic", "qa-engineer"]
    found_deprecated = []
    for agent in deprecated_agents:
        # Only check Step 7, not version history
        if agent in step_7_content:
            found_deprecated.append(agent)

    return {
        "status": "PASS" if not missing_in_doc and not found_deprecated else "FAIL",
        "missing_in_documentation": missing_in_doc,
        "deprecated_agents_found": found_deprecated,
    }


def test_token_efficient_pattern_used() -> dict[str, Any]:
    """Verify prompts use file paths instead of full content.

    Checks that prompts say "Review pre-mortem at <analysis_path>..."
    instead of passing the full analysis content.

    Returns:
        Test results with status and evidence of token efficiency
    """
    skill_path = Path.home() / ".claude" / "skills" / "pre-mortem" / "SKILL.md"

    if not skill_path.exists():
        return {
            "status": "SKIP",
            "reason": "SKILL.md not found",
        }

    content = skill_path.read_text(encoding="utf-8")

    # Look for token-efficient pattern: file path references
    token_efficient_pattern = r"Review pre-mortem at <analysis_path>"
    has_efficient_pattern = bool(re.search(token_efficient_pattern, content))

    # Look for inefficient patterns that suggest passing full content
    inefficient_indicators = [
        r"Review this pre-mortem analysis:",
        r"Review the following pre-mortem:",
        r"Here is the pre-mortem analysis:",
    ]
    has_inefficient_pattern = any(re.search(pattern, content) for pattern in inefficient_indicators)

    return {
        "status": "PASS" if has_efficient_pattern and not has_inefficient_pattern else "FAIL",
        "uses_file_path_pattern": has_efficient_pattern,
        "has_inefficient_pattern": has_inefficient_pattern,
    }


def test_explicit_agent_dispatch_pattern() -> dict[str, Any]:
    """Verify SKILL.md uses explicit Agent() calls, not Python loops.

    The correct pattern is explicit Agent() calls (one per line).
    Python loops with tuples don't work with the Agent tool subprocess wrapper.

    Returns:
        Test results with status and pattern detection
    """
    skill_path = Path.home() / ".claude" / "skills" / "pre-mortem" / "SKILL.md"

    if not skill_path.exists():
        return {
            "status": "SKIP",
            "reason": "SKILL.md not found",
        }

    content = skill_path.read_text(encoding="utf-8")

    # Look for explicit Agent() calls
    explicit_agent_pattern = r'Agent\(subagent_type="adversarial-'
    has_explicit_calls = bool(re.search(explicit_agent_pattern, content))

    # Look for problematic loop patterns
    loop_patterns = [
        r"for.*in.*agents:",
        r"\[.*Agent\(.*\).*for.*in",
    ]
    has_loop_pattern = any(re.search(pattern, content, re.MULTILINE) for pattern in loop_patterns)

    return {
        "status": "PASS" if has_explicit_calls and not has_loop_pattern else "FAIL",
        "uses_explicit_agent_calls": has_explicit_calls,
        "has_problematic_loop_pattern": has_loop_pattern,
    }


def run_all_tests() -> dict[str, Any]:
    """Run all adversarial dispatch integration tests.

    Returns:
        Combined test results with summary
    """
    tests = [
        ("All agents exist", test_all_adversarial_agents_exist),
        ("SKILL.md documents correct agents", test_skill_md_documents_correct_agents),
        ("Token-efficient pattern used", test_token_efficient_pattern_used),
        ("Explicit Agent() dispatch pattern", test_explicit_agent_dispatch_pattern),
    ]

    results = {}
    passed = 0
    failed = 0
    skipped = 0

    for test_name, test_func in tests:
        result = test_func()
        results[test_name] = result

        if result["status"] == "PASS":
            passed += 1
        elif result["status"] == "FAIL":
            failed += 1
        else:
            skipped += 1

    return {
        "summary": {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "overall": "PASS" if failed == 0 else "FAIL",
        },
        "tests": results,
    }


if __name__ == "__main__":
    import json

    results = run_all_tests()
    print(json.dumps(results, indent=2))
