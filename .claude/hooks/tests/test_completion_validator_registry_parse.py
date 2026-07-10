"""Regression test: completion_validator must parse the FULL core_hook_modules list.

Bug (2026-07-10): _verify_module_registered used the non-greedy regex
`core_hook_modules\\s*=\\s*\\[(.*?)\\]`, which stops at the FIRST ']' after the
list opens. A comment inside the list containing "[PLAN]/[RATIONALE]"
(registry.py:776) truncated the capture, so every module registered after
that line (e.g. mechanism_manifest, registry.py:802) produced a false
"MODULE NOT REGISTERED - WILL NOT EXECUTE" warning while demonstrably
running live. Fixed by parsing registry.py with ast (comments are inert).
"""
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from posttooluse.completion_validator import CompletionValidator  # noqa: E402


def _validator_for(tmp_path: Path, registry_source: str) -> CompletionValidator:
    v = CompletionValidator()
    reg = tmp_path / "registry.py"
    reg.write_text(textwrap.dedent(registry_source), encoding="utf-8")
    v.registry_file = reg
    v._registry_cache = None
    return v


def test_module_after_bracket_bearing_comment_is_visible(tmp_path):
    """The exact failure shape: entry AFTER a comment containing ']'."""
    v = _validator_for(
        tmp_path,
        '''
        def load():
            core_hook_modules = [
                "early_module",
                "plan_mode_schema",  # Inject [PLAN]/[RATIONALE] schema for planning-style prompts
                "late_module",  # registered AFTER the bracket-bearing comment
            ]
        ''',
    )
    assert v._verify_module_registered("late_module") is True
    assert v._verify_module_registered("early_module") is True


def test_unregistered_module_still_flagged(tmp_path):
    v = _validator_for(
        tmp_path,
        '''
        core_hook_modules = [
            "only_module",  # comment with ] bracket
        ]
        ''',
    )
    assert v._verify_module_registered("ghost_module") is False


def test_live_registry_contains_mechanism_manifest():
    """Pin against the real registry: the module that triggered the FP."""
    v = CompletionValidator()
    assert v._verify_module_registered("mechanism_manifest") is True


def test_parse_error_fails_open_as_unregistered(tmp_path):
    v = _validator_for(tmp_path, "def broken(:\n")
    assert v._verify_module_registered("anything") is False
