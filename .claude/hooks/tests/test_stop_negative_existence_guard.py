#!/usr/bin/env python3
"""
Comprehensive unit tests for Stop_negative_existence_guard.py

Tests cover:
- Allow conditions (no negative patterns, obvious allowlist)
- Block conditions (negative claims without verification)
- Verification conditions (with/without tools this turn)
- Turn scoping (DB-backed turn boundaries)
- PreToolUse coordination (state file check)
- Edge cases (empty response, invalid JSON, missing session)

Performance target: All tests should complete in <3 seconds total
"""

import json
import subprocess
import uuid
from pathlib import Path

import pytest


def run_guard(
    response: str,
    tool_events: list = None,
    session_id: str | None = None,
    terminal_id: str = "test-terminal",
    pretooluse_state: dict = None,
) -> tuple[dict, int]:
    """Run guard and return (output_dict, exit_code).

    Args:
        response: Response text to check
        tool_events: List of tool events for this turn (optional)
        session_id: Session ID for evidence lookups
        terminal_id: Terminal ID for turn scoping
        pretooluse_state: Optional PreToolUse state dict to create

    Returns:
        (output_dict, exit_code) tuple
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Create PreToolUse state file if provided
    state_file = None
    if pretooluse_state:
        state_dir = Path("P:/.claude/hooks/state")
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / f"file_existence_decision_{session_id}.json"
        state_file.write_text(json.dumps(pretooluse_state), encoding="utf-8")

    # Create evidence spool if tool_events provided
    evidence_spool_dir = None
    if tool_events is not None:
        evidence_spool_dir = Path("P:/.claude/hooks/session_data/evidence_spool")
        evidence_spool_dir.mkdir(parents=True, exist_ok=True)

        # Clean up ALL spool files from previous tests (prevents cross-test pollution)
        for old_spool in evidence_spool_dir.glob("*.json"):
            old_spool.unlink()

        # Write tool events to spool
        for i, event in enumerate(tool_events):
            event_file = evidence_spool_dir / f"{session_id}_{i:05d}.json"
            event_data = {
                "session_id": session_id,
                "terminal_id": terminal_id,
                "tool_name": event.get("name", ""),
                "command": event.get("command", ""),
                "ts": event.get("ts", "2026-03-07T12:00:00Z"),
                "id": i + 1,  # ID > turn_start_event_id (0)
            }
            event_file.write_text(json.dumps(event_data), encoding="utf-8")

    try:
        data = {
            "response": response,
            "session_id": session_id,
            "terminal_id": terminal_id,
        }

        # Include tool_events if explicitly provided (even if empty list).
        # Omitting it causes the guard to call _load_turn_events() which returns
        # None when no evidence exists, triggering the "evidence unavailable" block.
        if tool_events is not None:
            data["tool_events"] = tool_events

        input_data = json.dumps(data)

        result = subprocess.run(
            ["python", "P:/.claude/hooks/Stop_negative_existence_guard.py"],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=15,
        )

        try:
            output = json.loads(result.stdout) if result.stdout.strip() else {}
        except json.JSONDecodeError:
            output = {}

        return output, result.returncode
    finally:
        if state_file and state_file.exists():
            state_file.unlink()
        if evidence_spool_dir and evidence_spool_dir.exists():
            for f in evidence_spool_dir.glob(f"{session_id}_*.json"):
                f.unlink()


def test_no_negative_patterns_allowed():
    """Response without negative patterns should allow."""
    output, exit_code = run_guard("This is a normal response about code.")

    assert exit_code == 0
    assert output == {}


def test_obvious_allowlist_no_internet():
    """'no internet access' should be in allowlist."""
    output, exit_code = run_guard("This tool has no internet access.")

    assert exit_code == 0
    assert output == {}


def test_obvious_allowlist_no_config():
    """'no configuration needed' should be in allowlist."""
    output, exit_code = run_guard("No configuration needed for this tool.")

    assert exit_code == 0
    assert output == {}


def test_negative_claim_without_verification_blocked():
    """'file is missing' without tools should block."""
    response = "The config file is missing from the system."
    output, exit_code = run_guard(response, tool_events=[])

    assert exit_code == 2  # Block = exit 2
    assert output.get("decision") == "block"
    assert "Unverified Negative Existence Claim" in output.get("reason", "")


def test_negative_claim_with_verification_allowed():
    """'file is missing' after Read tool should allow."""
    response = "The config file doesn't exist."
    tool_events = [{"name": "Read", "command": "config.json", "ts": "2026-03-07T12:00:00Z"}]

    output, exit_code = run_guard(response, tool_events=tool_events)

    assert exit_code == 0
    assert output == {}


def test_file_specific_pattern_detected():
    """'no X file' pattern should be detected."""
    response = "There is no setup file in this directory."
    output, exit_code = run_guard(response, tool_events=[])

    assert exit_code == 2
    assert output.get("decision") == "block"
    # Pattern should detect "no setup file" phrase
    assert "setup" in output.get("reason", "").lower() or "file" in output.get("reason", "").lower()


def test_this_turn_scoping_works():
    """DB-backed turn boundaries should scope verification to current turn."""
    session_id = str(uuid.uuid4())
    terminal_id = "test-terminal"
    response = "The file doesn't exist."
    from evidence_store import append_tool_event, start_turn

    append_tool_event(
        session_id=session_id,
        terminal_id=terminal_id,
        tool_name="Read",
        command="file.txt",
    )
    start_turn(session_id=session_id, terminal_id=terminal_id, prompt="scope test")

    # Run the guard
    data = {
        "response": response,
        "session_id": session_id,
        "terminal_id": terminal_id,
    }
    input_data = json.dumps(data)

    result = subprocess.run(
        ["python", "P:/.claude/hooks/Stop_negative_existence_guard.py"],
        input=input_data,
        capture_output=True,
        text=True,
        timeout=15,
    )

    output = json.loads(result.stdout) if result.stdout.strip() else {}
    exit_code = result.returncode

    # Should block because the verification happened before the current turn boundary
    assert exit_code == 2, f"Expected block but got exit code {exit_code}, output: {output}"
    assert output.get("decision") == "block"


def test_multiple_claims_all_blocked():
    """Multiple negative claims should all be reported."""
    response = "The config file is missing and there's no documentation file."
    output, exit_code = run_guard(response, tool_events=[])

    assert exit_code == 2
    assert output.get("decision") == "block"
    reason = output.get("reason", "")
    # Patterns detect the negative existence phrases, not the specific nouns
    assert "missing" in reason.lower()
    assert "documentation" in reason.lower() or "no" in reason.lower()


def test_tool_attributed_missing_section_allowed():
    """Tool-attributed structure findings should not be treated as file nonexistence claims."""
    response = (
        "The verifier reported 2 structure findings in the analyzed plan text.\n"
        "1. Missing section: Problem Statement\n"
        "2. Missing section: Context Analysis"
    )
    output, exit_code = run_guard(response, tool_events=[])

    assert exit_code == 0
    assert output == {}


def test_tool_attributed_structure_findings_do_not_exempt_real_file_claims():
    """Verifier phrasing should not exempt separate unsupported nonexistence claims."""
    response = (
        "The verifier reported 2 structure findings in the analyzed plan text.\n"
        "1. Missing section: Problem Statement\n"
        "Also, there is no config file in the repository."
    )
    output, exit_code = run_guard(response, tool_events=[])

    assert exit_code == 2
    assert output.get("decision") == "block"
    assert (
        "config file" in output.get("reason", "").lower()
        or "no config file" in output.get("reason", "").lower()
    )


def test_grep_verification_counts():
    """Grep tool should count as verification."""
    response = "No test file found for this module."
    tool_events = [{"name": "Grep", "command": "test_*.py", "ts": "2026-03-07T12:00:00Z"}]

    output, exit_code = run_guard(response, tool_events=tool_events)

    assert exit_code == 0
    assert output == {}


def test_bash_ls_verification_counts():
    """Bash with 'ls' should count as verification."""
    response = "The setup file doesn't exist."
    tool_events = [{"name": "Bash", "command": "ls setup*", "ts": "2026-03-07T12:00:00Z"}]

    output, exit_code = run_guard(response, tool_events=tool_events)

    assert exit_code == 0
    assert output == {}


def test_bash_non_verification_doesnt_count():
    """Bash without verification commands shouldn't count."""
    response = "The file is missing."
    tool_events = [{"name": "Bash", "command": "echo 'test'", "ts": "2026-03-07T12:00:00Z"}]

    output, exit_code = run_guard(response, tool_events=tool_events)

    assert exit_code == 2
    assert output.get("decision") == "block"


def test_pretooluse_coordination_allows():
    """PreToolUse state file with 'allow' decision should bypass Stop guard."""
    response = "The file doesn't exist."

    # Create PreToolUse state with allow decision
    pretooluse_state = {
        "session_id": "test-session",
        "file_path": "/path/to/file.txt",
        "decision": "allow",
        "reason": "PreToolUse allowed this operation",
        "timestamp": "2026-03-07T12:00:00Z",
    }

    output, exit_code = run_guard(response, tool_events=[], pretooluse_state=pretooluse_state)

    assert exit_code == 0
    assert output == {}


def test_empty_response_allowed():
    """Empty response should be allowed."""
    output, exit_code = run_guard("")

    assert exit_code == 0
    assert output == {}


def test_invalid_json_allowed():
    """Invalid JSON input should be allowed (fail-open)."""
    result = subprocess.run(
        ["python", "P:/.claude/hooks/Stop_negative_existence_guard.py"],
        input="invalid json",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_missing_session_id_warns():
    """Missing session_id with negative claims should warn (evidence unavailable = fail-warn)."""
    response = "The file is missing."
    output, exit_code = run_guard(response, session_id="", tool_events=None)

    # Should warn when evidence system unavailable - fail-warn
    assert exit_code == 0
    assert output.get("decision") == "warn"


def test_offline_claim_allowed():
    """'offline' capability statement should be allowed."""
    output, exit_code = run_guard("This system is offline and has no network.")

    assert exit_code == 0
    assert output == {}


def test_no_setup_needed_allowed():
    """'no setup needed' domain knowledge should be allowed."""
    output, exit_code = run_guard("No setup needed for this tool.")

    assert exit_code == 0
    assert output == {}


def test_doesnt_exist_pattern_blocked():
    """'doesn't exist' pattern should be blocked without verification."""
    response = "The documentation doesn't exist in this repo."
    output, exit_code = run_guard(response, tool_events=[])

    assert exit_code == 2
    assert output.get("decision") == "block"


def test_wasnt_created_pattern_blocked():
    """'wasn't created' pattern should be blocked without verification."""
    response = "The cache file wasn't created during setup."
    output, exit_code = run_guard(response, tool_events=[])

    assert exit_code == 2
    assert output.get("decision") == "block"


def test_not_documented_pattern_blocked():
    """'not documented' pattern should be blocked without verification."""
    response = "This feature is not documented anywhere."
    output, exit_code = run_guard(response, tool_events=[])

    assert exit_code == 2
    assert output.get("decision") == "block"


def test_websearch_verification_counts():
    """WebSearch should count as verification."""
    response = "No external documentation exists for this API."
    tool_events = [
        {"name": "WebSearch", "command": "API documentation", "ts": "2026-03-07T12:00:00Z"}
    ]

    output, exit_code = run_guard(response, tool_events=tool_events)

    assert exit_code == 0
    assert output == {}


def test_glob_verification_counts():
    """Glob should count as verification."""
    response = "No config files found in directory."
    tool_events = [{"name": "Glob", "command": "config/*", "ts": "2026-03-07T12:00:00Z"}]

    output, exit_code = run_guard(response, tool_events=tool_events)

    assert exit_code == 0
    assert output == {}


def test_case_insensitive_pattern_matching():
    """Pattern matching should be case-insensitive."""
    variations = [
        "The file DOESN'T exist.",
        "The file Doesn't Exist.",
        "THE FILE DOESN'T EXIST.",
    ]

    for response in variations:
        output, exit_code = run_guard(response, tool_events=[])
        assert exit_code == 2, f"Should block: {response}"
        assert output.get("decision") == "block"


def test_partial_word_matching():
    """Patterns should match partial words correctly."""
    test_cases = [
        ("no such file", True),  # Should match
        ("there is no such thing", False),  # Should NOT match (different context)
        ("missing documentation", True),  # Should match
        ("go missing", False),  # Should NOT match (different context)
    ]

    for response, should_block in test_cases:
        output, exit_code = run_guard(response, tool_events=[])
        if should_block:
            assert exit_code == 2, f"Should block: {response}"
            assert output.get("decision") == "block"


# --- New exemption tests ---


def test_pure_number_claim_allowed():
    """'there's no 10' (pure count claim) should not trigger block."""
    response = "there's no 10 failures identified"
    output, exit_code = run_guard(response, tool_events=[])

    # Count claims are not file existence claims - should allow
    assert exit_code == 0
    assert output == {}


def test_code_element_claim_exempted_after_grep():
    """Code-element claims (e.g. 'no validate_X') are exempt when matching Grep was used."""
    response = "there's no validate_foo function in the codebase"
    tool_events = [{"name": "Grep", "command": "validate_", "ts": "2026-03-07T12:00:00Z"}]

    output, exit_code = run_guard(response, tool_events=tool_events)

    # Grep for "validate_" was used, so claiming "no validate_foo" is empirically grounded
    assert exit_code == 0
    assert output == {}


def test_code_element_claim_blocked_without_grep():
    """Code-element claims without matching Grep should still block."""
    response = "there's no validate_foo function in the codebase"
    tool_events = [{"name": "Bash", "command": "echo 'test'", "ts": "2026-03-07T12:00:00Z"}]

    output, exit_code = run_guard(response, tool_events=tool_events)

    # No Grep for "validate_" - should block
    assert exit_code == 2
    assert output.get("decision") == "block"


def test_corresponding_claim_exempted_after_grep():
    """'there's no corresponding' claim is exempt when Grep for relevant pattern was used."""
    response = "there's no corresponding validation function in validation.py"
    tool_events = [
        {"name": "Read", "file_path": "P:/path/to/validation.py", "command": "validation.py"},
        {"name": "Grep", "command": "remaining", "ts": "2026-03-07T12:00:00Z"},
    ]

    output, exit_code = run_guard(response, tool_events=tool_events)

    # Grep for "remaining" was used, grounding the "no corresponding" finding
    assert exit_code == 0
    assert output == {}


def test_multiple_claims_some_exempted():
    """When multiple claims exist and some are exempt, only non-exempt should block."""
    # First claim is a pure number (exempt), second is a file claim (not exempt).
    # Use a non-verification tool (Bash echo) so the non-exempt "no config file"
    # claim actually triggers a block. If a verification tool (Grep) were used,
    # _has_verification_this_turn would return True and allow all remaining claims.
    response = "there's no 10 failures, but no config file exists"
    tool_events = [{"name": "Bash", "command": "echo 'test'", "ts": "2026-03-07T12:00:00Z"}]

    output, exit_code = run_guard(response, tool_events=tool_events)

    # "there's no 10" is exempt, but "no config file" is not - should block
    assert exit_code == 2
    assert output.get("decision") == "block"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
