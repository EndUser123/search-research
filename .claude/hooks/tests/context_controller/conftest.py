"""Pytest conftest for the context_controller test suite.

Forces all `state.py` I/O into ``tmp_path`` so tests cannot touch
``P:/.claude/state/context-controller/``. Without this guard a test that
crashes mid-write would leave a real ``policy.json`` behind and pollute the
next session's controller state.

The autouse fixture monkeypatches ``_DEFAULT_STATE_ROOT`` (the path constant
the controller uses when callers do not pass a ``state_root``) AND points
``_DEFAULT_PROJECT_ROOT`` at ``tmp_path`` so the snapshot storage resolver
stays inside the sandbox. Tests that want a different root can pass
``state_root=...`` to the public API explicitly and ignore the default.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


# Add hooks directory to sys.path so the absolute imports in state.py
# (file_lock_manager, __lib.terminal_detection) resolve. This is the
# same shim the parent conftest.py uses; we duplicate it here so this
# suite can run in isolation (e.g. `pytest context_controller/`).
_HOOKS_DIR = Path("P:/.claude/hooks")
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

# Add the context_controller package's parent so the tests can do
# `import context_controller.state` after the conftest runs.
_PARENT = _HOOKS_DIR  # context_controller/ is a direct child of hooks/


@pytest.fixture(autouse=True)
def _sandbox_state_root(tmp_path, monkeypatch):
    """Redirect state.py default roots into tmp_path for every test.

    The fixture uses ``autouse=True`` so the sandbox is enforced even on
    tests that don't ask for it. A test that needs a different root can
    pass ``state_root=...`` to the public API; the default still points
    at tmp_path so any un-sandboxed access (e.g. via a function that
    defaults to ``_DEFAULT_STATE_ROOT``) is also safe.
    """
    import context_controller.state as state_mod

    monkeypatch.setattr(
        state_mod, "DEFAULT_STATE_ROOT", tmp_path / "state" / "context-controller"
    )
    monkeypatch.setattr(
        state_mod, "DEFAULT_PROJECT_ROOT", tmp_path / "project"
    )
    # Create the project root so the snapshot storage resolver has a
    # place to read from, even if the test doesn't touch envelopes.
    (tmp_path / "project").mkdir(parents=True, exist_ok=True)
    yield


@pytest.fixture
def fake_snapshot_storage():
    """Return a ``SnapshotFileStorage``-compatible class that reads/writes
    only inside ``tmp_path``.

    The controller's ``_try_import_snapshot_storage`` is monkeypatched
    to return this class. The class mimics the real
    ``SnapshotFileStorage`` just enough for ``read_handoff_envelope`` to
    succeed: it exposes a ``load_handoff()`` method that returns either
    a stored envelope or ``None``.

    Usage::

        def test_x(monkeypatch, fake_snapshot_storage):
            Storage = fake_snapshot_storage
            Storage.envelope = {"schema_version": 1, ...}
            monkeypatch.setattr(
                state_mod, "_try_import_snapshot_storage", lambda: Storage
            )
            ...
    """
    class _FakeStorage:
        # Class-level state so multiple instantiations see the same data.
        # Per-test isolation comes from the autouse _sandbox_state_root
        # fixture: tmp_path is fresh per test.
        envelope = None

        def __init__(self, project_root, terminal_id):
            self.project_root = Path(project_root)
            self.terminal_id = terminal_id

        def load_handoff(self):
            return type(self).envelope

    return _FakeStorage
