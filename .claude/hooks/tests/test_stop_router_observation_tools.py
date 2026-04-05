"""
Tests for OBSERVATION_TOOL_NAMES constant in Stop_router.py.

These tests verify the constant includes View/WebFetch but remediation text
doesn't mention them - a documentation inconsistency.

Run with: pytest P:/.claude/hooks/tests/test_stop_router_observation_tools.py -v
"""

import ast
import re


def test_observation_tool_names_exists():
    """
    Test that OBSERVATION_TOOL_NAMES exists as a frozenset.

    Given: Stop_router.py is imported
    When: Checking OBSERVATION_TOOL_NAMES
    Then: It should exist and be a frozenset
    """
    # Read the file and extract the constant
    with open(r"P:\.claude\hooks\Stop_router.py") as f:
        content = f.read()

    # Parse the file to find OBSERVATION_TOOL_NAMES
    tree = ast.parse(content)

    observation_tools = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "OBSERVATION_TOOL_NAMES":
                    # Found the assignment
                    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                        if node.value.func.id == "frozenset":
                            observation_tools = node.value
                            break

    assert observation_tools is not None, "OBSERVATION_TOOL_NAMES should exist"


def test_observation_tool_names_contains_six_tools():
    """
    Test that OBSERVATION_TOOL_NAMES contains 6 expected tools.

    Given: OBSERVATION_TOOL_NAMES constant
    When: Counting the tools
    Then: Should contain exactly 6 tools: Read, Grep, Glob, Bash, View, WebFetch
    """
    with open(r"P:\.claude\hooks\Stop_router.py") as f:
        content = f.read()

    # Extract the value using regex
    pattern = r'OBSERVATION_TOOL_NAMES\s*=\s*frozenset\((\{[^}]+\})\)'
    match = re.search(pattern, content)

    assert match is not None, "Could not find OBSERVATION_TOOL_NAMES definition"

    set_content = match.group(1)
    # Extract tool names from the set
    tools = re.findall(r'"([^"]+)"', set_content)

    expected_tools = {"Read", "Grep", "Glob", "Bash", "View", "WebFetch"}
    assert set(tools) == expected_tools, f"Expected {expected_tools}, got {set(tools)}"
    assert len(tools) == 6, f"Should have exactly 6 tools, got {len(tools)}"


def test_remediation_text_should_include_all_observation_tools():
    """
    Test that remediation text includes all 6 observation tools.

    Given: The consolidated observation block remediation text (around line 868)
    When: Checking which tools are mentioned
    Then: Should mention all 6 tools from OBSERVATION_TOOL_NAMES

    This is a FAILING test (RED phase) - the remediation text is missing View and WebFetch.
    """
    with open(r"P:\.claude\hooks\Stop_router.py") as f:
        content = f.read()

    # Find the remediation text in _build_consolidated_observation_block
    # Looking for the line that says "Remediation: run one Read/Grep/Glob/Bash/View/WebFetch observation"
    pattern = r'Remediation: run one ([A-Z][a-z]+(?:/[A-Z][a-zA-Z]+)*) observation'
    match = re.search(pattern, content)

    assert match is not None, "Could not find remediation text"

    mentioned_tools = match.group(1).split('/')
    mentioned_tools_set = set(mentioned_tools)

    # The test SHOULD expect all 6 tools to be mentioned
    expected_tools = {"Read", "Grep", "Glob", "Bash", "View", "WebFetch"}

    # This assertion FAILS because View and WebFetch are missing from remediation
    assert mentioned_tools_set == expected_tools, (
        f"Remediation text mentions {mentioned_tools_set}. "
        f"Expected {expected_tools} - View and WebFetch are missing!"
    )

    # Verify that View and WebFetch ARE mentioned (this will FAIL)
    assert "View" in mentioned_tools_set, "View should be mentioned in remediation text"
    assert "WebFetch" in mentioned_tools_set, "WebFetch should be mentioned in remediation text"


def test_observation_tools_should_match_remediation_text():
    """
    Test that remediation text mentions all tools from OBSERVATION_TOOL_NAMES.

    Given: OBSERVATION_TOOL_NAMES constant and remediation text
    When: Comparing the two
    Then: Remediation text should mention all tools in OBSERVATION_TOOL_NAMES

    This test FAILS because remediation text is incomplete (missing View/WebFetch).
    """
    with open(r"P:\.claude\hooks\Stop_router.py") as f:
        content = f.read()

    # Get tools from OBSERVATION_TOOL_NAMES
    pattern_tools = r'OBSERVATION_TOOL_NAMES\s*=\s*frozenset\((\{[^}]+\})\)'
    match_tools = re.search(pattern_tools, content)
    assert match_tools is not None

    set_content = match_tools.group(1)
    defined_tools = set(re.findall(r'"([^"]+)"', set_content))

    # Get tools from remediation text
    pattern_remediation = r'Remediation: run one ([A-Z][a-z]+(?:/[A-Z][a-zA-Z]+)*) observation'
    match_remediation = re.search(pattern_remediation, content)
    assert match_remediation is not None

    mentioned_tools = set(match_remediation.group(1).split('/'))

    # The test SHOULD expect no missing tools
    # This will FAIL because View and WebFetch are missing
    assert defined_tools == mentioned_tools, (
        f"OBSERVATION_TOOL_NAMES has {defined_tools} but remediation only mentions {mentioned_tools}. "
        f"Missing: {defined_tools - mentioned_tools}"
    )

    # Explicitly check that there are no missing tools
    missing_tools = defined_tools - mentioned_tools
    assert len(missing_tools) == 0, (
        f"Remediation text should mention all tools from OBSERVATION_TOOL_NAMES. "
        f"Missing: {missing_tools}"
    )
