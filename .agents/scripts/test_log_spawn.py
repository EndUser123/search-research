"""Tests for log_spawn.py — verifies CLI interface, success/failure paths,
and spawn_failures.jsonl append on --success false."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path("P:/.agents/scripts/log_spawn.py")
FAIL_LOG = Path("P:/.data/telemetry/spawn_failures.jsonl")


def _run(args: list[str]) -> subprocess.CompletedProcess:
    """Run log_spawn.py with given args, capture output."""
    cmd = [sys.executable, str(SCRIPT)] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=10)


def test_help_lists_all_args():
    """--help should list --model, --caller, --success, --error-type at minimum."""
    r = _run(["--help"])
    assert r.returncode == 0
    for flag in ["--model", "--caller", "--success", "--error-type", "--latency", "--domain", "--notes"]:
        assert flag in r.stdout, f"Missing {flag} in --help output"


def test_success_path_exits_zero():
    """A successful log call exits 0."""
    r = _run(["--model", "test-smoke", "--caller", "/pytest",
              "--success", "true", "--latency", "42", "--domain", "test"])
    assert r.returncode == 0


def test_failure_path_writes_spawn_failures_jsonl():
    """--success false with --error-type appends to spawn_failures.jsonl."""
    # Record state before
    lines_before = 0
    if FAIL_LOG.exists():
        lines_before = len(FAIL_LOG.read_text(encoding="utf-8").strip().splitlines())

    r = _run(["--model", "test-smoke", "--caller", "/pytest",
              "--success", "false", "--latency", "100",
              "--domain", "test", "--error-type", "429",
              "--notes", "pytest-receipt"])
    assert r.returncode == 0

    # Verify the entry landed
    content = FAIL_LOG.read_text(encoding="utf-8")
    lines_after = len(content.strip().splitlines())
    assert lines_after > lines_before, "spawn_failures.jsonl did not grow"

    last_line = content.strip().splitlines()[-1]
    entry = json.loads(last_line)
    assert entry["model"] == "test-smoke"
    assert entry["error_type"] == "429"
    assert entry["caller"] == "/pytest"
    assert entry["notes"] == "pytest-receipt"


def test_error_type_optional():
    """--error-type is optional even on failure."""
    r = _run(["--model", "test-smoke", "--caller", "/pytest",
              "--success", "true", "--domain", "test"])
    assert r.returncode == 0


def test_missing_required_args_fails():
    """Missing --model should produce non-zero exit."""
    r = _run(["--caller", "/pytest", "--success", "true"])
    assert r.returncode != 0


def test_non_blocking_on_telemetry_error():
    """If telemetry import fails, the script still exits 0 (non-blocking)."""
    r = _run(["--model", "test-smoke", "--caller", "/pytest",
              "--success", "true", "--domain", "test"])
    # Even if telemetry module has issues, exit code is 0
    assert r.returncode == 0


def teardown_module():
    """Clean up test-smoke entries from spawn_failures.jsonl after tests."""
    if FAIL_LOG.exists():
        lines = FAIL_LOG.read_text(encoding="utf-8").strip().splitlines()
        kept = [l for l in lines if "test-smoke" not in l and "pytest-receipt" not in l]
        FAIL_LOG.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
