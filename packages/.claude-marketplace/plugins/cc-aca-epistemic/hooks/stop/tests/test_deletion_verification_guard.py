"""Regression tests for Stop_deletion_verification_guard.

Covers the four fixes shipped in v0.2.76 plus the original 2026-07-03
false-positive suppression path:
  * FP-suppression: deletion prose + path-likes but NO deletion command -> allow.
  * #3 seen_verb leak across an embedded command boundary (rm dir/a; ls b.py).
  * #5 unverifiable construct emits an advisory BEFORE target verification.
  * #6 a literal file whose name contains glob chars (file[1].txt) is not
    expanded away (a failed deletion of it is still blocked).
  * #8 bare $VAR is flagged as an unverifiable construct.

Loads the SOURCE guard via importlib keyed on this file's location, so the
test is path-agnostic and does not depend on the version-keyed cache.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_GUARD = Path(__file__).resolve().parent.parent / "Stop_deletion_verification_guard.py"


@pytest.fixture(scope="module")
def guard():
    spec = importlib.util.spec_from_file_location("_deletion_guard_under_test", _GUARD)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_deletion_guard_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


# --- FP suppression: the original 2026-07-03 pointer-cleanup block ---------------

def test_prose_deletion_claim_without_command_allows(guard):
    """Deletion prose + path-likes but no deletion command ran -> None.

    Regression for the 2026-07-03 FP that blocked on CLAUDE.md and
    P:\\.claude\\.artifacts\\ which were never rm'd.
    """
    data = {
        "assistant_response": (
            "I cleaned up the stale pointers. I removed the old CLAUDE.md "
            "backup and deleted the P:\\.claude\\.artifacts\\ temp files."
        ),
        "tool_events": [],
    }
    assert guard.check(data) is None


# --- #3: seen_verb does not leak across an embedded command boundary --------------

def test_embedded_semicolon_does_not_leak_next_command(guard):
    """`rm dir/a; ls b.py` captures dir/a but NOT b.py from the next command."""
    targets, unverifiable = guard._parse_deletion_targets("rm dir/a; ls b.py")
    assert unverifiable is False
    assert "dir/a" in targets
    assert "b.py" not in targets
    assert all(";" not in t for t in targets), targets


# --- #5: unverifiable construct -> advisory BEFORE verification -------------------

def test_unverifiable_find_exec_emits_advisory_not_block(guard):
    """find -exec names no literal target -> fail-open advisory, never block."""
    data = {
        "assistant_response": "I deleted the old build artifacts.",
        "tool_events": [{"input": {"command": r"find . -exec rm {} \;"}}],
    }
    result = guard.check(data)
    assert result is not None
    assert result.get("decision") != "block"
    ctx = result.get("hookSpecificOutput", {}).get("additionalContext", "")
    assert "not literally present" in ctx, result


# --- #6: literal file with glob chars is not expanded as a wildcard ---------------

def test_literal_bracket_filename_not_treated_as_charclass(guard, tmp_path, monkeypatch):
    """A real file named file[1].txt must be seen as existing (block), not
    glob-expanded to nothing (which would falsely allow a failed deletion)."""
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    f = tmp_path / "file[1].txt"
    f.write_text("x", encoding="utf-8")
    data = {
        "assistant_response": "I deleted file[1].txt.",
        "tool_events": [{"input": {"command": f"rm {f.as_posix()}"}}],
    }
    result = guard.check(data)
    assert result is not None
    assert result.get("decision") == "block", result
    assert "file[1].txt" in result.get("reason", "")


# --- #8: bare $VAR is an unverifiable construct -----------------------------------

def test_bare_dollar_var_is_unverifiable(guard):
    _, unverifiable = guard._parse_deletion_targets("rm $FILE")
    assert unverifiable is True


def test_braced_dollar_var_is_unverifiable(guard):
    _, unverifiable = guard._parse_deletion_targets("rm ${FILE}")
    assert unverifiable is True
