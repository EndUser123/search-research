"""CLI tests for validate_handoff.py.

These verify the CLI wrapper behaves correctly: right exit codes, output to
the right stream, argument handling. They invoke the script as a subprocess
to test the real entry path users (the model) will use.

Mutation guard: if validate_handoff.py drifts from validators.py (e.g.,
someone refactors validators and the script still imports but calls a
stale function name), the exit-code-on-invalid test will catch it because
the script will either crash or exit 0 on a bad handoff.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CLI_SCRIPT = SKILL_ROOT / "__lib" / "validate_handoff.py"

VALID_HANDOFF = textwrap.dedent("""\
    ---
    thread_id: 11111111-2222-3333-4444-555555555555
    parent_handoff_path: none
    current_session_id: 66666666-7777-8888-9999-aaaaaaaaaaaa
    current_terminal_id: term-A
    produced_at: 2026-07-20T12:34:56Z
    status: open
    handoff_type: investigation
    accurate_as_of_head: abc1234def5678
    ---

    ## Objective
    Test.

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

# Introduce one defect: bad thread_id.
INVALID_HANDOFF = VALID_HANDOFF.replace(
    "thread_id: 11111111-2222-3333-4444-555555555555",
    "thread_id: not-a-uuid",
)


def _run_cli(path: str) -> tuple[int, str, str]:
    """Run the CLI script against `path`. Returns (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT), path],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def _run_cli_no_args() -> tuple[int, str, str]:
    """Run the CLI with no arguments."""
    result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def test_cli_exits_0_on_valid_handoff(tmp_path):
    """A valid handoff produces exit code 0."""
    p = tmp_path / "valid.md"
    p.write_text(VALID_HANDOFF, encoding="utf-8")
    code, stdout, _ = _run_cli(str(p))
    assert code == 0, f"expected exit 0, got {code}\nstdout:\n{stdout}"


def test_cli_exits_1_on_invalid_handoff(tmp_path):
    """An invalid handoff produces exit code 1."""
    p = tmp_path / "invalid.md"
    p.write_text(INVALID_HANDOFF, encoding="utf-8")
    code, stdout, _ = _run_cli(str(p))
    assert code == 1, f"expected exit 1, got {code}\nstdout:\n{stdout}"


def test_cli_exits_2_on_missing_argument():
    """No path argument produces exit code 2 (usage error)."""
    code, _, stderr = _run_cli_no_args()
    assert code == 2, f"expected exit 2, got {code}\nstderr:\n{stderr}"
    assert "usage" in stderr.lower()


def test_cli_reports_validity_on_stdout(tmp_path):
    """The CLI prints 'Valid (no errors): True' or 'False' on stdout."""
    p_valid = tmp_path / "valid.md"
    p_valid.write_text(VALID_HANDOFF, encoding="utf-8")
    _, stdout, _ = _run_cli(str(p_valid))
    assert "Valid (no errors): True" in stdout

    p_invalid = tmp_path / "invalid.md"
    p_invalid.write_text(INVALID_HANDOFF, encoding="utf-8")
    _, stdout, _ = _run_cli(str(p_invalid))
    assert "Valid (no errors): False" in stdout


def test_cli_prints_issues_on_stdout(tmp_path):
    """Issues are printed to stdout with severity, field, and message."""
    p = tmp_path / "invalid.md"
    p.write_text(INVALID_HANDOFF, encoding="utf-8")
    _, stdout, _ = _run_cli(str(p))
    assert "ERROR" in stdout
    assert "thread_id" in stdout
    assert "UUID" in stdout


def test_cli_handles_nonexistent_path():
    """A path that doesn't exist fails cleanly (non-zero exit, error message)."""
    code, stdout, stderr = _run_cli(str(Path("__nonexistent_handoff__.md")))
    # Either Python raises FileNotFoundError (exit 1 via traceback) or the
    # script catches it. Either way, exit is non-zero.
    assert code != 0
    output = (stdout + stderr).lower()
    assert "no such file" in output or "error" in output or "traceback" in output


def test_cli_drift_guard(tmp_path):
    """Drift guard: CLI catches the same defects the library catches.

    If validate_handoff.py drifts from validators.py (e.g., it imports a
    stale function name and silently passes everything), this test fails
    because the CLI will exit 0 on a handoff the library rejects.
    """
    # Direct library check:
    sys.path.insert(0, str(SKILL_ROOT / "__lib"))
    try:
        from validators import is_valid
    finally:
        sys.path.pop(0)
    lib_says_invalid = not is_valid(INVALID_HANDOFF)
    assert lib_says_invalid, "test setup broken: INVALID_HANDOFF should fail library check"

    # CLI check on the same input:
    p = tmp_path / "invalid.md"
    p.write_text(INVALID_HANDOFF, encoding="utf-8")
    code, _, _ = _run_cli(str(p))
    assert code == 1, (
        "CLI drift detected: library rejects this handoff but CLI accepted it (exit 0). "
        "Check that validate_handoff.py still calls validate_handoff_file / validate_handoff_text."
    )
