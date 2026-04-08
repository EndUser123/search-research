#!/usr/bin/env python3
"""Test script for cognitive_guardrails.py regex patterns."""

import re

# From cognitive_guardrails.py
DESIGN_INTENT_PATTERNS = [
    # Action verbs + implementation objects
    r"(?i)\b(design|architect|build|create|implement|add|make|develop)\b.{0,100}?\b(hook|skill|feature|solution|system|module|package|function|class|tool|service|command)\b",
    # Planning/approach framing
    r"(?i)\b(how should (we|i)|what'?s the (approach|solution|best way)|we need to (build|create|implement|design|add))\b",
    # Explicit design skill invocations
    r"(?:^|\s)/(arch|code|planning|adf|prd|tdd|feature-dev)\b",
]

def test_patterns():
    """Test each pattern with positive and negative cases."""

    # Pattern 1: Action verbs + implementation objects
    pattern1 = DESIGN_INTENT_PATTERNS[0]

    positive_cases_p1 = [
        "design a hook for authentication",
        "create a skill for testing",
        "implement a feature for users",
        "build a system for logging",
        "architect a module for parsing",
        "add a tool for debugging",
        "make a class for validation",
        "develop a service for API calls",
        "create a command for cleanup",
    ]

    negative_cases_p1 = [
        "the design is complete",  # No implementation object
        "design thinking workshop",  # Not about implementation
        "create a file",  # "file" not in implementation objects list
        "add water to the mix",  # Not technical context
        "make it work better",  # No implementation object
    ]

    print("Pattern 1: Action verbs + implementation objects")
    print("=" * 60)

    print("\n✅ Positive cases (should match):")
    for test in positive_cases_p1:
        match = re.search(pattern1, test)
        status = "✓" if match else "✗ FAIL"
        print(f"  {status} '{test}' -> {match.group(0) if match else 'NO MATCH'}")

    print("\n❌ Negative cases (should NOT match):")
    for test in negative_cases_p1:
        match = re.search(pattern1, test)
        status = "✓" if not match else "✗ FAIL (FALSE POSITIVE)"
        print(f"  {status} '{test}'")

    # Pattern 2: Planning/approach framing
    pattern2 = DESIGN_INTENT_PATTERNS[1]

    positive_cases_p2 = [
        "how should we design this",
        "how should i implement the feature",
        "what's the approach for testing",
        "what's the solution for logging",
        "what's the best way to handle errors",
        "we need to build a new system",
        "we need to create a module",
        "we need to implement a feature",
        "we need to design an architecture",
        "we need to add functionality",
    ]

    negative_cases_p2 = [
        "how does the system work",
        "what is the approach",
        "we need more resources",
        "what's the time",
        "how are you today",
    ]

    print("\n\nPattern 2: Planning/approach framing")
    print("=" * 60)

    print("\n✅ Positive cases (should match):")
    for test in positive_cases_p2:
        match = re.search(pattern2, test)
        status = "✓" if match else "✗ FAIL"
        print(f"  {status} '{test}' -> {match.group(0) if match else 'NO MATCH'}")

    print("\n❌ Negative cases (should NOT match):")
    for test in negative_cases_p2:
        match = re.search(pattern2, test)
        status = "✓" if not match else "✗ FAIL (FALSE POSITIVE)"
        print(f"  {status} '{test}'")

    # Pattern 3: Explicit design skill invocations
    pattern3 = DESIGN_INTENT_PATTERNS[2]

    positive_cases_p3 = [
        "/arch",
        "/code",
        "/planning",
        "/adf",
        "/prd",
        "/tdd",
        "/feature-dev",
        "use /arch for design",
        "run /code to implement",
        " /arch",  # Leading space
        "\n/arch",  # Leading newline
    ]

    negative_cases_p3 = [
        "architecture",  # Not a slash command
        "coding",  # Not a slash command
        "planning meeting",  # Not a slash command
        "/other-command",  # Not in the list
        "slasharch",  # No space or newline before /
        "http://arch.example.com",  # :// not (?:^|\s)
    ]

    print("\n\nPattern 3: Explicit design skill invocations")
    print("=" * 60)

    print("\n✅ Positive cases (should match):")
    for test in positive_cases_p3:
        match = re.search(pattern3, test)
        status = "✓" if match else "✗ FAIL"
        print(f"  {status} '{test}' -> {match.group(0) if match else 'NO MATCH'}")

    print("\n❌ Negative cases (should NOT match):")
    for test in negative_cases_p3:
        match = re.search(pattern3, test)
        status = "✓" if not match else "✗ FAIL (FALSE POSITIVE)"
        print(f"  {status} '{test}'")

    # Edge case tests
    print("\n\nEdge Cases")
    print("=" * 60)

    edge_cases = [
        ("Empty string", "", False),
        ("None-like", "None", False),
        ("Very long string between verbs", "create" + " " * 150 + "hook", False),  # Should NOT match (>100 chars)
        ("Just at boundary", "create" + " " * 99 + "hook", True),  # Should match (100 chars)
        ("Just over boundary", "create" + " " * 101 + "hook", False),  # Should NOT match (>100 chars)
    ]

    for name, test, should_match in edge_cases:
        if test == "":
            print(f"  ⚠️  '{name}': Skipping empty string test")
            continue

        # Test against pattern 1 (has .{0,100}? limit)
        match = re.search(DESIGN_INTENT_PATTERNS[0], test)
        actual_match = match is not None

        if actual_match == should_match:
            print(f"  ✓ '{name}': {'matched' if actual_match else 'no match'} (as expected)")
        else:
            print(f"  ✗ FAIL '{name}': {'matched' if actual_match else 'no match'} (expected: {'match' if should_match else 'no match'})")

if __name__ == "__main__":
    test_patterns()
