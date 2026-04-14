from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit_modules.base import HookResult


def _load_router_module():
    router_path = _hooks_dir / "UserPromptSubmit.py"
    spec = importlib.util.spec_from_file_location("userpromptsubmit_router_under_test", router_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_strips_known_tags_without_overstripping(monkeypatch) -> None:
    ups = _load_router_module()

    def fake_run_hooks(data, prompt):
        return [
            HookResult(
                context="[ASUM] [CYNE]\nWhy: diagnostic intent detected\n\nFramework body [TODO]",
                tokens=12,
            ),
            HookResult(
                context="[SEQ]\n**Use [SEQ]** to mark sequential reasoning.\n\nStepwise body [NOTE]",
                tokens=10,
            ),
        ]

    monkeypatch.setattr(ups.registry, "run_hooks", fake_run_hooks)
    monkeypatch.setattr(ups, "check_user_pushback", lambda data, prompt: None)

    payload = {
        "prompt": "Refactor the behavior contract so it is leaner and more explicit.",
        "transcript_path": "C:\\tmp\\session-claude-sonnet-4-6.jsonl",
    }

    stdout = io.StringIO()
    stdin = io.StringIO(json.dumps(payload))
    old_stdin = sys.stdin

    try:
        sys.stdin = stdin
        with contextlib.redirect_stdout(stdout):
            ups.main()
    finally:
        sys.stdin = old_stdin

    output = json.loads(stdout.getvalue())
    text = output["hookSpecificOutput"]["additionalContext"]

    assert "**Active context:**" not in text
    assert "[ASUM]" not in text
    assert "[CYNE]" not in text
    assert "[SEQ]" not in text
    assert "[TODO]" in text
    assert "[NOTE]" in text
    assert "Framework body" in text
    assert "Stepwise body" in text
