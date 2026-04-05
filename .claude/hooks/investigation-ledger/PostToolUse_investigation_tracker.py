"""
PostToolUse Hook: Investigation Ledger Tracker
Records file reads, searches, and executions to the investigation ledger.

Integrates with Claude Code hook system via JSON stdin/stdout.
"""

import json
import os
import sys
from pathlib import Path

# Add ledger module to path
HOOK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_DIR))

from ledger import record_execution, record_file_read, record_search


def extract_tool_data(hook_input: dict) -> tuple:
    """Extract tool name and relevant data from hook input."""
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    tool_result = hook_input.get("tool_result", {})

    return tool_name, tool_input, tool_result


def handle_file_read(tool_input: dict, tool_result: dict) -> bool:
    """Record file read operations."""
    # Extract path from various tool input formats
    path = (
        tool_input.get("path") or
        tool_input.get("file_path") or
        tool_input.get("filePath") or
        ""
    )

    if path:
        # Check if read was successful (no error in result)
        result_str = str(tool_result)
        if "error" not in result_str.lower() and "not found" not in result_str.lower():
            return record_file_read(path)

    return False


def handle_search(tool_input: dict, tool_result: dict) -> bool:
    """Record search operations."""
    query = (
        tool_input.get("query") or
        tool_input.get("pattern") or
        tool_input.get("search") or
        ""
    )

    if query:
        # Count results if available
        results_count = 0
        if isinstance(tool_result, dict):
            results = tool_result.get("results", tool_result.get("matches", []))
            if isinstance(results, list):
                results_count = len(results)

        return record_search(query, results_count)

    return False


def handle_execution(tool_input: dict, tool_result: dict) -> bool:
    """Record command executions."""
    command = (
        tool_input.get("command") or
        tool_input.get("cmd") or
        ""
    )

    if command:
        # Extract exit code
        exit_code = -1
        if isinstance(tool_result, dict):
            exit_code = tool_result.get("exit_code", tool_result.get("exitCode", -1))
        elif isinstance(tool_result, str):
            # Assume success if no error indicators
            if "error" not in tool_result.lower() and "failed" not in tool_result.lower():
                exit_code = 0

        return record_execution(command, exit_code)

    return False


def main():
    """Main hook entry point."""
    # Check if investigation ledger is enabled
    if os.environ.get("INVESTIGATION_LEDGER_ENABLED", "true").lower() != "true":
        print(json.dumps({"continue": True}))
        return

    try:
        # Read hook input from stdin
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            # No input - pass through
            print(json.dumps({"continue": True}))
            return

        hook_input = json.loads(raw_input)
        tool_name, tool_input, tool_result = extract_tool_data(hook_input)

        # Route to appropriate handler based on tool name
        tool_lower = tool_name.lower()

        # File read tools
        if any(t in tool_lower for t in ["read", "view", "cat", "get_file"]):
            handle_file_read(tool_input, tool_result)

        # Search tools
        elif any(t in tool_lower for t in ["search", "grep", "find", "ripgrep"]):
            handle_search(tool_input, tool_result)

        # Execution tools
        elif any(t in tool_lower for t in ["bash", "shell", "exec", "run", "terminal"]):
            handle_execution(tool_input, tool_result)

        # Also check for multi-tool results
        elif "read" in str(tool_result).lower()[:100]:
            # Might be a compound operation that includes reads
            handle_file_read(tool_input, tool_result)

        # Always continue - this hook is observational only
        print(json.dumps({"continue": True}))

    except json.JSONDecodeError as e:
        # Invalid JSON input - log and continue
        print(json.dumps({
            "continue": True,
            "warning": f"Investigation ledger: JSON parse error: {e}"
        }))
    except Exception as e:
        # Graceful degradation - don't block on ledger errors
        print(json.dumps({
            "continue": True,
            "warning": f"Investigation ledger error: {e}"
        }))


if __name__ == "__main__":
    main()
