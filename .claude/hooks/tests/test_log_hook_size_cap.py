"""Tests for log_hook size cap (Finding 1 regression).

The size cap must truncate an oversized log WITHOUT touching the transcript
diff baseline — resetting the baseline forced a full transcript re-dump on the
next run, which re-inflated the file (the 435GB regrowth churn).
"""
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "log_hook", str(Path(__file__).resolve().parent.parent / "log_hook.py")
)
assert _SPEC and _SPEC.loader
log_hook = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(log_hook)


def test_oversized_log_is_truncated(tmp_path):
    log = tmp_path / "claude-log.jsonl"
    log.write_text("x" * 100, encoding="utf-8")
    assert log_hook._enforce_size_cap(log, max_bytes=10) is True
    assert not log.exists()


def test_undersized_log_is_kept(tmp_path):
    log = tmp_path / "claude-log.jsonl"
    log.write_text("x" * 5, encoding="utf-8")
    assert log_hook._enforce_size_cap(log, max_bytes=10) is False
    assert log.exists()


def test_cap_does_not_touch_transcript_baseline(tmp_path):
    # The regression: capping the log must NOT delete the diff baseline.
    log = tmp_path / "claude-log.jsonl"
    baseline = tmp_path / "claude-log.transcript.jsonl"
    log.write_text("x" * 100, encoding="utf-8")
    baseline.write_text("line1\nline2\n", encoding="utf-8")
    log_hook._enforce_size_cap(log, max_bytes=10)
    assert baseline.exists()
    assert baseline.read_text(encoding="utf-8") == "line1\nline2\n"


def test_missing_log_is_noop(tmp_path):
    assert log_hook._enforce_size_cap(tmp_path / "absent.jsonl", max_bytes=10) is False


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
