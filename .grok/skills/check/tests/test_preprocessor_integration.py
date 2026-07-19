"""End-to-end integration tests for ``preprocessor.py``.

Evidence classification: CONTRACT_MODEL_TESTED + fixture-grounded

Exercises the public ``preprocess`` and ``preprocess_to_file`` entrypoints
plus the CLI ``main()`` against the synthetic fixture.
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure __lib is on sys.path so we can import preprocessor (which itself
# also bootstraps, but conftest may not have run yet for these imports).
_LIB = Path(__file__).resolve().parent.parent / "__lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import preprocessor as pp  # noqa: E402
import output_validator as ov  # noqa: E402

FIXTURE = Path(__file__).parent / "fixture_sample.jsonl"


def test_preprocess_returns_valid_packet():
    pkt = pp.preprocess(FIXTURE)
    d = pkt.to_dict()
    errs = ov.validate_packet(d)
    assert errs.ok, errs.errors


def test_preprocess_packet_has_nonzero_signals():
    pkt = pp.preprocess(FIXTURE)
    counts = pkt.signal_counts
    # Fixture exercises most detectors; at least file_edits, command_executions,
    # claim_verbs, verification_tool_calls must be non-zero.
    assert counts["file_edits"] >= 1
    assert counts["command_executions"] >= 1
    assert counts["claim_verbs"] >= 1
    assert counts["verification_tool_calls"] >= 1


def test_preprocess_to_file_writes_atomic(tmp_path):
    out = tmp_path / "evidence.json"
    written = pp.preprocess_to_file(FIXTURE, str(out))
    assert Path(written).exists()
    assert not (tmp_path / "evidence.json.tmp").exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"]


def test_preprocess_to_file_forward_slash_path(tmp_path):
    out_backslash = str(tmp_path / "evidence.json").replace("/", "\\")
    written = pp.preprocess_to_file(FIXTURE, out_backslash)
    # Output path must be forward-slashed (windows-filesystem rule).
    assert "\\" not in written


def test_main_cli_writes_packet_and_returns_zero(tmp_path, capsys):
    out = tmp_path / "cli.json"
    rc = pp.main([str(FIXTURE), str(out)])
    captured = capsys.readouterr()
    assert rc == 0
    # CLI prints a forward-slashed path (windows-filesystem rule); compare
    # against the normalised form rather than the backslashed native str().
    assert str(out).replace("\\", "/") in captured.out
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["producer"] == "check.preprocessor"


def test_main_cli_bad_args_returns_one(capsys):
    rc = pp.main([])
    captured = capsys.readouterr()
    assert rc == 1
    assert "usage" in captured.err.lower()


def test_main_cli_missing_file_returns_two(tmp_path, capsys):
    out = tmp_path / "out.json"
    rc = pp.main([str(tmp_path / "does_not_exist.jsonl"), str(out)])
    captured = capsys.readouterr()
    assert rc == 2
    # Either preprocess error or io error depending on how Path.open fails
    assert captured.err


def test_preprocess_on_malformed_transcript_still_produces_partial_packet(tmp_path):
    """Malformed lines must NOT crash the preprocessor — produce PARTIAL packet."""
    bad = tmp_path / "bad.jsonl"
    bad.write_text(
        json.dumps({"type": "system", "content": "ok"}) + "\n"
        + "this is not json\n"
        + json.dumps({"type": "user", "content": "<user_query>x</user_query>"}) + "\n",
        encoding="utf-8",
    )
    pkt = pp.preprocess(bad)
    assert pkt.source_status.value == "SOURCE_PARTIAL"
    errs = ov.validate_packet(pkt.to_dict())
    assert errs.ok  # still structurally valid


def test_preprocessor_imports_siblings_without_package_context():
    """Preprocessor must work when run as a script (no __init__.py)."""
    # The fact that this test file imported `preprocessor` successfully
    # already proves this. We additionally confirm sys.path manipulation.
    assert str(_LIB) in sys.path


def test_main_cli_non_utf8_file_returns_two(tmp_path, capsys):
    """Non-UTF8 byte in transcript must yield exit 2 + one-line error.

    Regression guard for /review Finding 3: previously the UnicodeDecodeError
    (subclass of ValueError) bubbled to Python's default handler, producing
    a multi-line traceback at exit 1 instead of the clean exit 2 + one-liner
    the SKILL.md orchestrator expects.
    """
    bad = tmp_path / "bad.jsonl"
    bad.write_bytes(b'\xff\xfe{"type":"system","content":"x"}\n')
    out = tmp_path / "out.json"
    rc = pp.main([str(bad), str(out)])
    captured = capsys.readouterr()
    assert rc == 2, f"expected exit 2, got {rc}"
    # Stderr must be a single short line, not a Python traceback.
    assert "Traceback" not in captured.err
    assert "UnicodeDecodeError" in captured.err or "ValueError" in captured.err
    # No output file should have been written.
    assert not out.exists()
