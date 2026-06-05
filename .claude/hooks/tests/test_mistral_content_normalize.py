"""Regression test for _normalize_mistral_content in Stop_semantic_critic.py.

Locks the 2026-06-03 fix: Mistral returns message.content as a str for normal
completions but as a LIST of content chunks under reasoning_effort="high".
The old code called .strip() on the list -> 'list' object has no attribute 'strip',
silently killing the critic's Mistral half. No mocks (real strings/dicts/objects).
"""
import importlib.util
import pathlib
import sys

_P = pathlib.Path(__file__).resolve().parents[1] / "Stop_semantic_critic.py"
_spec = importlib.util.spec_from_file_location("ssc_norm_test", _P)
_ssc = importlib.util.module_from_spec(_spec)
sys.modules["ssc_norm_test"] = _ssc
_spec.loader.exec_module(_ssc)
norm = _ssc._normalize_mistral_content


class _Chunk:
    """Real lightweight stand-in for an SDK content chunk (not a Mock)."""
    def __init__(self, text):
        self.text = text


def test_plain_string():
    assert norm("hello") == "hello"


def test_string_is_stripped():
    assert norm("  hi \n") == "hi"


def test_none_returns_empty():
    assert norm(None) == ""


def test_empty_list_returns_empty():
    assert norm([]) == ""


def test_list_of_dicts():
    assert norm([{"text": "a"}, {"text": "b"}]) == "ab"


def test_list_of_objects():
    assert norm([_Chunk("x"), _Chunk("y")]) == "xy"


def test_list_skips_chunks_without_text():
    assert norm([_Chunk("a"), {"notext": 1}, {"text": "b"}]) == "ab"


def test_reasoning_then_answer_chunks_concatenated():
    assert norm([{"text": "reason "}, {"text": "answer"}]) == "reason answer"


def test_non_str_non_list_returns_empty():
    assert norm(123) == ""
