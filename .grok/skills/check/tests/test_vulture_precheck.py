"""Tests for advisory vulture pre-check helper."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parents[1] / "__lib"
sys.path.insert(0, str(_LIB))

import vulture_precheck as vp  # noqa: E402


def test_line_re_parses_windows_paths():
    line = r"D:\.code\Keep-Smaller-Copy\app.py:174: unused variable 'CSS' (60% confidence)"
    m = vp._LINE_RE.match(line)
    assert m is not None
    assert m.group("line") == "174"
    assert m.group("confidence") == "60"
    assert "CSS" in m.group("message")


def test_framework_fp_exact_names():
    assert vp._is_framework_fp("unused method 'compose'", "compose") is True
    assert vp._is_framework_fp("unused variable 'BINDINGS'", "BINDINGS") is True
    assert vp._is_framework_fp("unused method 'watch_busy'", "watch_busy") is True


def test_decorated_handler_names(tmp_path: Path):
    src = tmp_path / "ui.py"
    src.write_text(
        "from textual import on\n"
        "class A:\n"
        "    @on(Button.Pressed, '#x')\n"
        "    def _start_scan(self):\n"
        "        pass\n"
        "    def real_dead(self):\n"
        "        pass\n",
        encoding="utf-8",
    )
    names = vp._decorated_handler_names(str(src))
    assert "_start_scan" in names
    assert "real_dead" not in names


def test_run_vulture_on_self_is_ok():
    self_path = str(_LIB / "vulture_precheck.py")
    result = vp.run_vulture([self_path], min_confidence=80)
    assert result["status"] in ("ok", "skipped")
    assert result["advisory"] is True
    assert result["blocks_check"] is False


def test_missing_file_skipped():
    result = vp.run_vulture([r"P:\definitely_missing_xyz.py"], min_confidence=80)
    assert result["status"] == "skipped"
    assert result["advisory"] is True
