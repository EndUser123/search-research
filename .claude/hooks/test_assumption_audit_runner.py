#!/usr/bin/env python3
"""
Test runner: Compare both detection methods on same inputs.
"""

import json
import os
import subprocess
from pathlib import Path

HOOK = Path("P:/.claude/hooks/test_assumption_audit.py")
LOG_FILE = Path("P:/.claude/hooks/logs/test_assumption_audit.jsonl")

def run_test(name: str, response: str, tool_sequence: list = None) -> dict:
    """Run hook and return parsed result."""

    # Build conversation with tool_use blocks if tools were used
    assistant_content = []

    # Add tool_use blocks first (to simulate tools being called)
    for tool in (tool_sequence or []):
        assistant_content.append({
            "type": "tool_use",
            "name": tool.get("tool", ""),
            "input": tool.get("input", {}),
        })

    # Add text response
    assistant_content.append({
        "type": "text",
        "text": response,
    })

    input_data = {
        "conversation": [
            {"role": "assistant", "content": assistant_content}
        ],
    }

    env = os.environ.copy()
    env["TEST_ASSUMPTION_AUDIT_ENABLED"] = "true"
    env["TEST_ASSUMPTION_AUDIT_METHOD"] = "regex"  # Act on regex
    env["TEST_ASSUMPTION_AUDIT_MODE"] = "block"

    result = subprocess.run(
        ["python", str(HOOK)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env
    )

    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stdout, "stderr": result.stderr}


def get_last_log_entry() -> dict:
    """Get the last comparison entry from log."""
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()
        for line in reversed(lines):
            entry = json.loads(line)
            if entry.get("event") == "detection_comparison":
                return entry
    except:
        pass
    return {}


# Test cases
TESTS = [
    {
        "name": "Unverified recommendation (classic case)",
        "response": """
Based on my analysis, I recommend keeping the current architecture.

Reasons:
1. Third-party CLIs don't support structured output - we have no control over their format
2. Since they may change their output format, parsing is fragile
3. Because external tools are black boxes, we can't rely on them

Therefore, the best approach is to maintain the current wrapper pattern.
""",
        "tools": [],
        "expected_regex": True,
        "expected_llm": True,
    },
    {
        "name": "Verified recommendation (has observation)",
        "response": """
I ran `qwen --help` and found it supports `--json` output format.

Based on this finding, I recommend switching to JSON output mode.

Reasons:
1. The CLI explicitly supports structured output
2. JSON parsing is more reliable than text parsing
""",
        "tools": [{"tool": "Bash", "input": {"command": "qwen --help"}}],
        "expected_regex": False,
        "expected_llm": False,
    },
    {
        "name": "Informational (no recommendation)",
        "response": """
The file contains a simple Python function that processes JSON data.
It has 3 methods: parse(), validate(), and transform().
""",
        "tools": [],
        "expected_regex": False,
        "expected_llm": False,
    },
    {
        "name": "Simple recommendation (1 reasoning pattern only)",
        "response": """
I recommend using regex because it's simpler.
""",
        "tools": [],
        "expected_regex": False,  # Only 1 reasoning pattern
        "expected_llm": True,     # Has recommendation + no observation
    },
    {
        "name": "Multiple reasoning patterns, no recommendation verb",
        "response": """
Since the API doesn't support pagination, and because the data may change,
therefore we can't cache results.
""",
        "tools": [],
        "expected_regex": False,  # No recommendation
        "expected_llm": False,    # No recommendation
    },
    {
        "name": "Recommendation with soft reasoning",
        "response": """
The best approach would be to use SQLite here.

It's lightweight and doesn't require a server.
""",
        "tools": [],
        "expected_regex": False,  # Only ~1 reasoning pattern
        "expected_llm": True,     # Has recommendation
    },
]


def main():
    # Clear log for fresh comparison
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    print("=" * 70)
    print("ASSUMPTION AUDIT: Dual Detection Comparison")
    print("=" * 70)
    print(f"{'Test':<45} {'Regex':<10} {'LLM':<10} {'Agree?':<8}")
    print("-" * 70)

    results = []

    for test in TESTS:
        # Run hook
        output = run_test(test["name"], test["response"], test["tools"])

        # Get comparison from log
        log_entry = get_last_log_entry()

        regex_triggered = log_entry.get("regex", {}).get("triggered", "?")
        llm_triggered = log_entry.get("llm", {}).get("triggered", "?")
        agree = log_entry.get("agree", "?")

        # Check expectations
        regex_correct = regex_triggered == test["expected_regex"]
        llm_correct = llm_triggered == test["expected_llm"]

        regex_str = f"{'✓' if regex_triggered else '✗'} ({test['expected_regex']})"
        llm_str = f"{'✓' if llm_triggered else '✗'} ({test['expected_llm']})"

        status = "✅" if regex_correct and llm_correct else "❌"

        print(f"{test['name']:<45} {regex_str:<10} {llm_str:<10} {agree!s:<8} {status}")

        results.append({
            "name": test["name"],
            "regex": regex_triggered,
            "llm": llm_triggered,
            "agree": agree,
            "regex_correct": regex_correct,
            "llm_correct": llm_correct,
        })

    print("-" * 70)

    # Summary
    disagreements = [r for r in results if not r["agree"]]
    if disagreements:
        print(f"\n⚠️  Methods DISAGREE on {len(disagreements)} case(s):")
        for d in disagreements:
            print(f"   - {d['name']}: regex={d['regex']}, llm={d['llm']}")

    all_correct = all(r["regex_correct"] and r["llm_correct"] for r in results)
    if all_correct:
        print("\n✅ All expectations matched!")
    else:
        print("\n❌ Some expectations failed - check test cases")


if __name__ == "__main__":
    main()
