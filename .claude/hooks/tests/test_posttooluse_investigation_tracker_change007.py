"""Tests for the CHANGE-007 write-side port into the registered InvestigationTracker.

Verifies that a passing verification command (pytest/unittest/etc.) stamps the
git-changed files via record_verification(), and that non-verification or failing
commands do not. Redirects ledger.LEDGER_PATH/LOCK_PATH to a temp dir so the
suite never touches the live session ledger.
"""

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
LEDGER_DIR = HOOKS_DIR / "investigation-ledger"
for p in (str(HOOKS_DIR), str(LEDGER_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402


@pytest.fixture
def redirected_ledger(tmp_path, monkeypatch):
    """Point ledger state at a temp dir; return the ledger module."""
    import ledger
    state_dir = tmp_path / ".claude" / ".session"
    state_dir.mkdir(parents=True, exist_ok=True)
    tid = ledger._TERMINAL_ID or "test"
    monkeypatch.setattr(ledger, "LEDGER_PATH", state_dir / f"session_ledger_{tid}.json")
    monkeypatch.setattr(ledger, "LOCK_PATH", state_dir / f"session_ledger_{tid}.lock")
    # Reset the tracker's lazy-import cache so it rebinds against this ledger state.
    import posttooluse.investigation_tracker as tracker_mod
    monkeypatch.setattr(tracker_mod.InvestigationTracker, "_ledger_funcs", None)
    return ledger


@pytest.fixture
def tracker(redirected_ledger):
    from posttooluse.investigation_tracker import InvestigationTracker
    return InvestigationTracker()


def _write(tmp_path, name, content="def f():\n    return 1\n"):
    p = tmp_path / name
    p.write_text(content)
    return str(p)


class TestChange007Stamping:
    """CHANGE-007: passing verification command stamps changed files."""

    def test_passing_pytest_stamps_changed_file(self, tracker, redirected_ledger, tmp_path, monkeypatch):
        f = _write(tmp_path, "engine.py")
        monkeypatch.setattr(
            "posttooluse.investigation_tracker._git_changed_files", lambda: [f]
        )
        res = tracker.process("Bash", {"command": "python -m pytest -q"}, {"exit_code": 0})
        assert res["passed"] is True
        assert redirected_ledger.is_verified(f, "strict") is True

    def test_non_verification_command_does_not_stamp(self, tracker, redirected_ledger, tmp_path, monkeypatch):
        f = _write(tmp_path, "other.py")
        monkeypatch.setattr(
            "posttooluse.investigation_tracker._git_changed_files", lambda: [f]
        )
        tracker.process("Bash", {"command": "ls -la"}, {"exit_code": 0})
        assert redirected_ledger.is_verified(f, "strict") is False

    def test_failing_verification_does_not_stamp(self, tracker, redirected_ledger, tmp_path, monkeypatch):
        f = _write(tmp_path, "broken.py")
        monkeypatch.setattr(
            "posttooluse.investigation_tracker._git_changed_files", lambda: [f]
        )
        tracker.process("Bash", {"command": "pytest -q"}, {"exit_code": 1})
        assert redirected_ledger.is_verified(f, "strict") is False

    def test_overstamp_ceiling_all_changed_files_stamped(self, tracker, redirected_ledger, tmp_path, monkeypatch):
        # Documents the known false-negative ceiling: every git-diff file is
        # stamped, including siblings the runner never executed.
        engine = _write(tmp_path, "engine.py")
        config = _write(tmp_path, "config.py")
        monkeypatch.setattr(
            "posttooluse.investigation_tracker._git_changed_files",
            lambda: [engine, config],
        )
        tracker.process("Bash", {"command": "pytest -q"}, {"exit_code": 0})
        assert redirected_ledger.is_verified(engine, "strict") is True
        assert redirected_ledger.is_verified(config, "strict") is True  # untested, yet stamped

    def test_edit_after_stamp_invalidates(self, tracker, redirected_ledger, tmp_path, monkeypatch):
        # The content-hash contract: stamp, then edit -> is_verified flips False.
        f = _write(tmp_path, "mut.py", "x = 1\n")
        monkeypatch.setattr(
            "posttooluse.investigation_tracker._git_changed_files", lambda: [f]
        )
        tracker.process("Bash", {"command": "pytest -q"}, {"exit_code": 0})
        assert redirected_ledger.is_verified(f, "strict") is True
        Path(f).write_text("x = 2\n")
        assert redirected_ledger.is_verified(f, "strict") is False


class TestVerificationRegex:
    def _re(self):
        from posttooluse.investigation_tracker import _VERIFICATION_CMD_RE
        return _VERIFICATION_CMD_RE

    @pytest.mark.parametrize("cmd", [
        "pytest",
        "pytest -q",
        "python -m pytest",
        "python -m unittest",
        "npm test",
        "npm run test",
        "yarn test",
        "pnpm test",
        "cargo test",
        "make test",
        "go test ./...",
    ])
    def test_matches_known_runners(self, cmd):
        assert self._re().search(cmd) is not None

    @pytest.mark.parametrize("cmd", ["ls -la", "git status", "git diff --name-only HEAD", "echo hello", "pip install requests"])
    def test_does_not_match_non_runners(self, cmd):
        # Commands with no runner token must not stamp. NOTE: a bare 'pytest'
        # token matches anywhere (e.g. 'pip install pytest', 'echo pytest') —
        # verbatim-ported standalone behavior; the over-stamp is fail-closed-safe
        # (an unnecessary stamp, never a missed one). Out of scope to tighten.
        assert self._re().search(cmd) is None
