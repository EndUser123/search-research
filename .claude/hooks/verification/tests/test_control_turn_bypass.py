"""Tests for _is_control_turn() in StopHook_unverified_stance.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from StopHook_unverified_stance import _is_control_turn


class TestControlTurnDetection:
    def test_stop(self):
        assert _is_control_turn("stop") is True

    def test_yes(self):
        assert _is_control_turn("yes") is True

    def test_no(self):
        assert _is_control_turn("no") is True

    def test_ok(self):
        assert _is_control_turn("ok") is True

    def test_okay(self):
        assert _is_control_turn("okay") is True

    def test_done(self):
        assert _is_control_turn("done") is True

    def test_continue(self):
        assert _is_control_turn("continue") is True

    def test_go_ahead(self):
        assert _is_control_turn("go ahead") is True

    def test_proceed(self):
        assert _is_control_turn("proceed") is True

    def test_skip(self):
        assert _is_control_turn("skip") is True

    def test_single_y(self):
        assert _is_control_turn("y") is True

    def test_single_n(self):
        assert _is_control_turn("n") is True


class TestWhitespaceHandling:
    def test_leading_trailing_spaces(self):
        assert _is_control_turn("  yes  ") is True

    def test_mixed_case(self):
        assert _is_control_turn("  YeS  ") is True

    def test_tab_whitespace(self):
        assert _is_control_turn("\tstop\t") is True


class TestNonControlTurns:
    def test_medium_response(self):
        assert _is_control_turn("I'll update the file and run tests") is False

    def test_long_response(self):
        text = "This is a longer response that clearly contains verifiable claims about the codebase"
        assert _is_control_turn(text) is False

    def test_exactly_30_chars(self):
        # 30 chars should be allowed through (<=30 check)
        assert _is_control_turn("a" * 30) is False  # "aaa...a" is not a control word


class TestEdgeCases:
    def test_empty_string(self):
        assert _is_control_turn("") is True

    def test_whitespace_only(self):
        assert _is_control_turn("   ") is True

    def test_cancel(self):
        assert _is_control_turn("cancel") is True

    def test_abort(self):
        assert _is_control_turn("abort") is True

    def test_true_false(self):
        assert _is_control_turn("true") is True
        assert _is_control_turn("false") is True

    def test_zero_one(self):
        assert _is_control_turn("0") is True
        assert _is_control_turn("1") is True
