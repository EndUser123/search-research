"""CLI tests for list_handoffs.py.

Mirrors the test_cli.py pattern: invoke the script as a subprocess against a
temporary handoffs root, verify exit codes and output content. These guard:
  - the script doesn't crash on real inputs
  - it surfaces the right fields per row
  - the MISMATCH flag fires when work is terminal but file is open
  - sorting is newest-first
  - missing fields degrade gracefully (no crash, "?" placeholder)
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CLI_SCRIPT = SKILL_ROOT / "__lib" / "list_handoffs.py"

VALID_HANDOFF = textwrap.dedent("""\
    ---
    thread_id: 11111111-2222-3333-4444-555555555555
    parent_handoff_path: none
    current_session_id: 66666666-7777-8888-9999-aaaaaaaaaaaa
    current_terminal_id: console_aaaa-bbbb
    produced_at: {produced_at}
    status: open
    handoff_type: investigation
    accurate_as_of_head: abc1234def5678
    ---

    ## Objective
    Ship the widget.

    ## Status
    OPEN

    ## Producing context
    - Date: 2026-07-20

    ## Read-first list
    1. `file.ts`

    ## Verified facts
    - [FACT] something

    ## Current state
    Done.

    ## Task packets

    ### T-1: do it

    - goal: do it
    - in scope: x
    - out of scope: y
    - files / anchors: x.ts
    - acceptance: pass
    - falsifier: if fail
    - verification level required: UNIT_TEST

    ## Open decisions
    None.

    ## Hard constraints
    - None

    ## Cross-reference couplings
    - None identified.

    ## Explicit non-goals
    - Nothing

    ## Resumption protocol
    1. Read x.ts

    ## Suggested next invocation
    `/go x`

    ## Last user message (verbatim)
    > please do the thing

    ## Epistemic labels
    - [FACT] x
""")


def _make_handoff(produced_at: str, status_yaml: str = "open",
                  work_status: str = "OPEN", objective: str = "Ship the widget.",
                  terminal_id: str = "console_aaaa-bbbb") -> str:
    """Build a handoff body with configurable fields."""
    body = VALID_HANDOFF.format(produced_at=produced_at)
    body = body.replace("status: open", f"status: {status_yaml}")
    body = body.replace("OPEN\n\n## Producing context",
                        f"{work_status}\n\n## Producing context")
    body = body.replace("Ship the widget.", objective)
    body = body.replace("console_aaaa-bbbb", terminal_id)
    return body


def _run_cli(handoffs_root: Path) -> tuple[int, str, str]:
    """Run the CLI against `handoffs_root`. Returns (exit, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT), str(handoffs_root)],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def _run_cli_default() -> tuple[int, str, str]:
    """Run with no path arg (default-root mode)."""
    result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT)],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


# ---------------------------------------------------------------------------
# Exit-code and usage tests
# ---------------------------------------------------------------------------

def test_cli_exits_0_on_valid_root(tmp_path):
    """A root with handoffs exits 0 and prints rows."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z"), encoding="utf-8")
    code, stdout, _ = _run_cli(tmp_path)
    assert code == 0
    assert "topic-20260720" in stdout


def test_cli_exits_0_on_empty_root(tmp_path):
    """An empty root prints '(no handoffs under ...)' and exits 0."""
    code, stdout, _ = _run_cli(tmp_path)
    assert code == 0
    assert "no handoffs" in stdout


def test_cli_exits_2_on_missing_root(tmp_path):
    """A nonexistent root exits 2 with a stderr message."""
    missing = tmp_path / "does-not-exist"
    code, _, stderr = _run_cli(missing)
    assert code == 2
    assert "not found" in stderr.lower()


def test_cli_exits_2_on_too_many_args(tmp_path):
    """More than 3 argv tokens is a usage error (exit 2)."""
    result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT), str(tmp_path), "extra", "another"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 2
    assert "usage" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Field extraction tests
# ---------------------------------------------------------------------------

def test_cli_extracts_yaml_status(tmp_path):
    """yaml:open appears on the row."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z", status_yaml="open"), encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "yaml:open" in stdout


def test_cli_extracts_work_status_keyword(tmp_path):
    """The Status section's leading keyword is extracted, not the whole line."""
    (tmp_path / "topic-20260720").mkdir()
    body = _make_handoff("2026-07-20T12:00:00Z",
                         work_status="**READY_FOR_REVIEW** \u2014 design done.")
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(body, encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "work:READY_FOR_REVIEW" in stdout


def test_cli_extracts_objective(tmp_path):
    """Objective first line appears on the row."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z",
                      objective="Build the migration tool."),
        encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "Build the migration tool." in stdout


def test_cli_shows_relative_time_recent(tmp_path):
    """A handoff produced recently shows 'just now' or '<int>m' or '<int>h'."""
    (tmp_path / "topic-20260720").mkdir()
    # 30 minutes ago in UTC
    recent = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff(recent), encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    # Accept any of the recent forms; the exact value depends on test latency.
    assert ("30m" in stdout) or ("just now" in stdout) or ("3" in stdout[:80] and "m" in stdout[:80])


def test_cli_shows_terminal_short(tmp_path):
    """terminal_id is shortened to the prefix before first underscore."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z", terminal_id="console_aaaa-bbbb"),
        encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "console" in stdout


# ---------------------------------------------------------------------------
# MISMATCH flag tests
# ---------------------------------------------------------------------------

def test_cli_flags_mismatch_when_work_closed_but_yaml_open(tmp_path):
    """MISMATCH appears when yaml=open but body Status=CLOSED."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z", status_yaml="open",
                      work_status="CLOSED"),
        encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "MISMATCH" in stdout
    assert "1 mismatch" in stdout  # summary line


def test_cli_no_mismatch_when_both_open(tmp_path):
    """No MISMATCH when yaml=open and work=OPEN."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z", status_yaml="open",
                      work_status="OPEN"),
        encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "MISMATCH" not in stdout
    assert "0 mismatch" in stdout


def test_cli_no_mismatch_when_work_ready_for_review(tmp_path):
    """READY_FOR_REVIEW is not terminal; no mismatch even if yaml=open."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z", status_yaml="open",
                      work_status="READY_FOR_REVIEW"),
        encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "MISMATCH" not in stdout


# ---------------------------------------------------------------------------
# Sorting and degradation tests
# ---------------------------------------------------------------------------

def test_cli_sorts_newest_first(tmp_path):
    """Newest produced_at appears at the top."""
    older = tmp_path / "older-20260719"
    newer = tmp_path / "newer-20260720"
    older.mkdir()
    newer.mkdir()
    (older / "HANDOFF.md").write_text(
        _make_handoff("2026-07-19T12:00:00Z", objective="OLDER"), encoding="utf-8")
    (newer / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z", objective="NEWER"), encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    older_pos = stdout.find("OLDER")
    newer_pos = stdout.find("NEWER")
    assert newer_pos < older_pos, f"expected NEWER before OLDER\n{stdout}"


def test_cli_degrades_on_missing_status_section(tmp_path):
    """Missing body Status section shows 'work:?' not a crash."""
    (tmp_path / "topic-20260720").mkdir()
    body = _make_handoff("2026-07-20T12:00:00Z")
    # Delete the Status section content
    body = body.replace("## Status\nOPEN\n", "## Status\n\n")
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(body, encoding="utf-8")
    code, stdout, _ = _run_cli(tmp_path)
    assert code == 0
    assert "work:?" in stdout


def test_cli_degrades_on_malformed_frontmatter(tmp_path):
    """A handoff with no parseable frontmatter still produces a row, not a crash."""
    (tmp_path / "broken-20260720").mkdir()
    (tmp_path / "broken-20260720" / "HANDOFF.md").write_text(
        "# This file has no frontmatter\n\nJust body text.",
        encoding="utf-8")
    code, stdout, _ = _run_cli(tmp_path)
    assert code == 0
    assert "broken-20260720" in stdout
    # All fields should be "?" or empty
    assert "yaml:?" in stdout


def test_cli_tolerates_future_timestamp(tmp_path):
    """A timestamp slightly in the future shows 'just now' not '?'."""
    (tmp_path / "topic-20260720").mkdir()
    # 2 hours in the future — within the 48h tolerance
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff(future), encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "just now" in stdout


def test_cli_handles_numbered_section_headings(tmp_path):
    """`## 2. Status` works as well as `## Status`."""
    (tmp_path / "topic-20260720").mkdir()
    body = _make_handoff("2026-07-20T12:00:00Z")
    body = body.replace("## Objective", "## 1. Objective")
    body = body.replace("## Status", "## 2. Status")
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(body, encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "work:OPEN" in stdout
    assert "Ship the widget." in stdout


# ---------------------------------------------------------------------------
# HEAD-drift detection tests
# ---------------------------------------------------------------------------

def test_cli_head_drift_shown_when_sha_differs(tmp_path):
    """head:DRIFT appears when accurate_as_of_head differs from --head arg."""
    (tmp_path / "topic-20260720").mkdir()
    body = _make_handoff("2026-07-20T12:00:00Z")
    body = body.replace("accurate_as_of_head: abc1234def5678",
                        "accurate_as_of_head: different_commit_sha")
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(body, encoding="utf-8")
    _, stdout, _ = _run_cli_with_head(tmp_path, "current_head_sha_here")
    assert "head:DRIFT" in stdout
    assert "1 HEAD-drift" in stdout


def test_cli_head_no_drift_when_sha_matches(tmp_path):
    """No head:DRIFT flag when accurate_as_of_head matches --head."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z"), encoding="utf-8")  # uses abc1234def5678
    _, stdout, _ = _run_cli_with_head(tmp_path, "abc1234def5678")
    assert "head:DRIFT" not in stdout
    assert "0 HEAD-drift" in stdout


def test_cli_head_no_drift_on_short_sha_prefix_match(tmp_path):
    """Short-sha prefix comparison: first 12 chars matching = ok."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z"), encoding="utf-8")
    # Handoff has abc1234def5678; pass the same first 12 chars with extra suffix.
    _, stdout, _ = _run_cli_with_head(tmp_path, "abc1234def5678extended")
    assert "head:DRIFT" not in stdout


def test_cli_head_unknown_when_accurate_as_of_head_missing(tmp_path):
    """head:? appears when accurate_as_of_head is absent (pre-v0.1.1 schema)."""
    (tmp_path / "topic-20260720").mkdir()
    body = _make_handoff("2026-07-20T12:00:00Z")
    # Remove the accurate_as_of_head line entirely
    body = body.replace("accurate_as_of_head: abc1234def5678\n", "")
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(body, encoding="utf-8")
    _, stdout, _ = _run_cli_with_head(tmp_path, "current_head_sha_here")
    assert "head:?" in stdout
    assert "1 no-head-field" in stdout
    assert "DRIFT" not in stdout


def test_cli_head_check_skipped_without_flag(tmp_path):
    """Without --head, no head column appears and no head summary."""
    (tmp_path / "topic-20260720").mkdir()
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(
        _make_handoff("2026-07-20T12:00:00Z"), encoding="utf-8")
    code, stdout, _ = _run_cli(tmp_path)
    assert code == 0
    assert "head:" not in stdout
    assert "HEAD-drift" not in stdout


def test_cli_head_requires_sha_argument(tmp_path):
    """--head with no sha is a usage error."""
    result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT), str(tmp_path), "--head"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 2
    assert "requires a sha" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Claim consistency tests
# ---------------------------------------------------------------------------

def test_cli_hides_claim_when_assignment_fields_inconsistent(tmp_path):
    """claimed: marker is hidden when assigned_to is set but assigned_at/by are missing."""
    (tmp_path / "topic-20260720").mkdir()
    body = _make_handoff("2026-07-20T12:00:00Z")
    # Inject assigned_to only (no assigned_at or assigned_by)
    body = body.replace("accurate_as_of_head: abc1234def5678",
                        "assigned_to: grok\naccurate_as_of_head: abc1234def5678")
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(body, encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "claimed:grok" not in stdout, f"claim should be hidden when inconsistent\n{stdout}"


def test_cli_shows_claim_when_assignment_fields_consistent(tmp_path):
    """claimed: marker appears when all three assignment fields are present."""
    (tmp_path / "topic-20260720").mkdir()
    body = _make_handoff("2026-07-20T12:00:00Z")
    body = body.replace("accurate_as_of_head: abc1234def5678",
                        "assigned_to: grok\n"
                        "assigned_at: 2026-07-20T10:00:00Z\n"
                        "assigned_by: 11111111-2222-3333-4444-555555555555\n"
                        "accurate_as_of_head: abc1234def5678")
    (tmp_path / "topic-20260720" / "HANDOFF.md").write_text(body, encoding="utf-8")
    _, stdout, _ = _run_cli(tmp_path)
    assert "claimed:grok" in stdout


def _run_cli_with_head(handoffs_root: Path, head_sha: str) -> tuple[int, str, str]:
    """Run the CLI with --head flag. Returns (exit, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT), str(handoffs_root), "--head", head_sha],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


# ---------------------------------------------------------------------------
# Library-level unit tests for the new helper
# ---------------------------------------------------------------------------

def test_extract_section_body_returns_section_content():
    """validators.extract_section_body returns text under the named heading."""
    sys.path.insert(0, str(SKILL_ROOT / "__lib"))
    try:
        from validators import extract_section_body
    finally:
        sys.path.pop(0)
    body = "## Objective\nDo X\n\n## Status\nOPEN\n\n## Next\nfoo"
    assert "OPEN" in extract_section_body(body, "Status")
    assert "Do X" in extract_section_body(body, "Objective")
    assert extract_section_body(body, "Nonexistent") == ""


def test_extract_section_body_strips_numbered_prefix():
    """Numbered section headings are matched after stripping the prefix."""
    sys.path.insert(0, str(SKILL_ROOT / "__lib"))
    try:
        from validators import extract_section_body
    finally:
        sys.path.pop(0)
    body = "## 1. Objective\nDo X\n\n## 2. Status\nOPEN"
    assert "OPEN" in extract_section_body(body, "Status")
    assert "Do X" in extract_section_body(body, "Objective")
