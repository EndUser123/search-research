#!/usr/bin/env python3
"""Unit tests for Stop_positive_existence_guard.py.

Covers:
- No positive claim -> allow
- Positive claim without direct inspection -> block
- Claim bound to remote/backup/origin/commit/branch -> block when unverified
- Direct inspection verbs (git show ref:path, git cat-file, git ls-tree,
  git ls-files, ls, cat, Read, non-empty Glob) -> allow
- Stat-only bash (git log --stat, git diff --stat, git show --stat) -> still blocks
- Bash producing fatal/does-not-exist output -> still blocks
- Empty/no-match Glob result -> still blocks
- Evidence unavailable -> warn (not block)
- Empty response / invalid JSON -> allow
"""

from __future__ import annotations

import json
import subprocess
import uuid


HOOK = "P:/.claude/hooks/Stop_positive_existence_guard.py"


def run_guard(
    response: str,
    tool_events: list | None = None,
    session_id: str | None = None,
    terminal_id: str = "test-terminal",
) -> tuple[dict, int]:
    if session_id is None:
        session_id = str(uuid.uuid4())
    data: dict = {
        "response": response,
        "session_id": session_id,
        "terminal_id": terminal_id,
    }
    if tool_events is not None:
        data["tool_events"] = tool_events

    result = subprocess.run(
        ["python", HOOK],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        timeout=15,
    )
    try:
        out = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        out = {}
    return out, result.returncode


# --- Allow cases ------------------------------------------------------------


def test_no_positive_claim_allowed():
    out, rc = run_guard("Just a normal sentence about refactoring.", tool_events=[])
    assert rc == 0
    assert out == {}


def test_plain_file_mention_without_target_binding_allowed():
    """Path mentioned without 'remote/backup/commit/origin' binding shouldn't trigger."""
    out, rc = run_guard("We could refactor foo/bar.py later.", tool_events=[])
    assert rc == 0
    assert out == {}


def test_empty_response_allowed():
    out, rc = run_guard("", tool_events=[])
    assert rc == 0
    assert out == {}


def test_invalid_json_allowed():
    result = subprocess.run(
        ["python", HOOK],
        input="not json",
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0


# --- Block cases (unverified positive claims) -------------------------------


def test_remote_has_file_without_verification_blocked():
    response = "The backup remote has PreToolUse_import_deletion_guard.py"
    out, rc = run_guard(response, tool_events=[])
    assert rc == 2
    assert out.get("decision") == "block"
    assert "Unverified Positive Existence Claim" in out.get("reason", "")


def test_exists_at_origin_main_blocked():
    response = "PreToolUse_import_deletion_guard.py exists at origin/main."
    out, rc = run_guard(response, tool_events=[])
    assert rc == 2
    assert out.get("decision") == "block"


def test_commit_includes_path_blocked():
    response = "commit abc1234 includes packages/foo/bar.py"
    out, rc = run_guard(response, tool_events=[])
    assert rc == 2
    assert out.get("decision") == "block"


def test_backup_repo_contains_path_blocked():
    response = "The backup repo has .claude/hooks/deleted_guard.py."
    out, rc = run_guard(response, tool_events=[])
    assert rc == 2
    assert out.get("decision") == "block"


# --- Stat-only bash does NOT count as verification --------------------------


def test_git_log_stat_does_not_verify():
    response = "The backup remote has PreToolUse_import_deletion_guard.py"
    events = [
        {
            "name": "Bash",
            "command": "git log --stat origin/main",
            "output_excerpt": "PreToolUse_import_deletion_guard.py | 90 +",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 2
    assert out.get("decision") == "block"


def test_stat_banner_fires_when_stat_phrasing_in_response():
    """When the response itself contains stat-style phrasing, banner should appear."""
    response = (
        "git log --stat origin/main shows the backup remote has foo/bar.py"
    )
    out, rc = run_guard(response, tool_events=[])
    assert rc == 2
    assert "stat" in out.get("reason", "").lower()


def test_git_diff_stat_does_not_verify():
    response = "The remote has X/Y/foo.py"
    events = [
        {
            "name": "Bash",
            "command": "git diff --stat HEAD~1 HEAD",
            "output_excerpt": "X/Y/foo.py | 12 +",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 2
    assert out.get("decision") == "block"


def test_git_show_stat_without_refpath_does_not_verify():
    response = "The backup remote has PreToolUse_import_deletion_guard.py"
    events = [
        {
            "name": "Bash",
            "command": "git show --stat HEAD",
            "output_excerpt": "PreToolUse_import_deletion_guard.py | 90 +",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 2
    assert out.get("decision") == "block"


# --- Direct inspection verbs DO count ---------------------------------------


def test_git_show_refpath_verifies():
    response = "The backup remote has PreToolUse_import_deletion_guard.py"
    events = [
        {
            "name": "Bash",
            "command": "git show backup/main:PreToolUse_import_deletion_guard.py",
            "output_excerpt": "#!/usr/bin/env python3\nimport sys\n",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 0
    assert out == {}


def test_git_cat_file_verifies():
    response = "origin/main has .claude/hooks/foo.py"
    events = [
        {
            "name": "Bash",
            "command": "git cat-file -e origin/main:.claude/hooks/foo.py",
            "output_excerpt": "",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 0
    assert out == {}


def test_git_ls_tree_verifies():
    response = "commit abc123 includes packages/foo/bar.py"
    events = [
        {
            "name": "Bash",
            "command": "git ls-tree abc123 -- packages/foo/bar.py",
            "output_excerpt": "100644 blob deadbeef\tpackages/foo/bar.py",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 0
    assert out == {}


def test_ls_bash_verifies():
    response = "The backup remote has foo/bar.py"
    events = [
        {
            "name": "Bash",
            "command": "ls foo/bar.py",
            "output_excerpt": "foo/bar.py",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 0
    assert out == {}


def test_read_tool_verifies():
    response = "The backup remote has .claude/hooks/deleted_guard.py"
    events = [
        {
            "name": "Read",
            "file_path": "P:/.claude/hooks/deleted_guard.py",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 0
    assert out == {}


def test_non_empty_glob_verifies():
    response = "The backup remote has .claude/hooks/deleted_guard.py"
    events = [
        {
            "name": "Glob",
            "pattern": ".claude/hooks/deleted_guard.py",
            "output_excerpt": "P:/.claude/hooks/deleted_guard.py",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 0
    assert out == {}


# --- Negative-result direct inspection does NOT verify ---------------------


def test_empty_glob_does_not_verify():
    response = "The backup remote has .claude/hooks/deleted_guard.py"
    events = [
        {
            "name": "Glob",
            "pattern": ".claude/hooks/deleted_guard.py",
            "output_excerpt": "No files found",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 2
    assert out.get("decision") == "block"


def test_bash_fatal_output_does_not_verify():
    response = "The backup remote has foo/bar.py"
    events = [
        {
            "name": "Bash",
            "command": "git show backup/main:foo/bar.py",
            "output_excerpt": "fatal: path 'foo/bar.py' does not exist in 'backup/main'",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 2
    assert out.get("decision") == "block"


def test_ls_no_such_file_output_does_not_verify():
    response = "The backup remote has foo/bar.py"
    events = [
        {
            "name": "Bash",
            "command": "ls foo/bar.py",
            "output_excerpt": "ls: cannot access 'foo/bar.py': No such file or directory",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 2
    assert out.get("decision") == "block"


# --- Evidence unavailable: warn, not block ---------------------------------


def test_evidence_unavailable_warns():
    """Empty session_id forces loader to return None -> warn, not block."""
    response = "The backup remote has PreToolUse_import_deletion_guard.py"
    # session_id empty => _load_turn_events short-circuits to None
    out, rc = run_guard(response, tool_events=None, session_id="")
    assert rc == 0
    assert out.get("decision") == "warn"


# --- Per-claim: other path verified doesn't exempt unverified path ---------


def test_unrelated_inspection_does_not_exempt_claim():
    response = "The backup remote has foo/bar.py"
    events = [
        {
            "name": "Read",
            "file_path": "P:/unrelated/other.py",
        }
    ]
    out, rc = run_guard(response, tool_events=events)
    assert rc == 2
    assert out.get("decision") == "block"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
