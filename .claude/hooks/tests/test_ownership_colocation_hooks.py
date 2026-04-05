"""
Tests for ownership-colocation hooks.

Covers:
- UserPromptSubmit: ownership_colocation_nudge  (detection + injection)
- PreToolUse:       PreToolUse_ownership_colocation_gate  (block/allow/bypass)
- Integration:      UserPromptSubmit.py dispatch → nudge → context injection
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# UPS nudge — unit tests via direct import
# ---------------------------------------------------------------------------

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "UserPromptSubmit_modules"))


def _import_nudge():
    """Import the nudge module, registering its hook via the decorator."""
    import importlib

    return importlib.import_module("UserPromptSubmit_modules.ownership_colocation_nudge")


class TestOwnershipColocationNudge:
    """Unit tests for ownership_colocation_nudge (UPS hook)."""

    def test_no_placement_keywords_returns_empty(self):
        mod = _import_nudge()
        assert not mod._has_placement_intent("implement the new feature")
        assert not mod._has_placement_intent("fix the bug in auth module")
        assert not mod._has_placement_intent("")

    def test_proxy_keyword_triggers(self):
        mod = _import_nudge()
        assert mod._has_placement_intent("set up a proxy for the ai-api skill")

    def test_infra_keyword_triggers(self):
        mod = _import_nudge()
        assert mod._has_placement_intent("create the infrastructure for this service")
        assert mod._has_placement_intent("set up infra directory")

    def test_adapter_keyword_triggers(self):
        mod = _import_nudge()
        assert mod._has_placement_intent("build an adapter layer")

    def test_where_to_put_triggers(self):
        mod = _import_nudge()
        assert mod._has_placement_intent("where to put the config files")
        assert mod._has_placement_intent("where should I place the venv")

    def test_new_directory_triggers(self):
        mod = _import_nudge()
        assert mod._has_placement_intent("create a new directory for this")
        assert mod._has_placement_intent("make a new folder called adapters")

    def test_venv_triggers(self):
        mod = _import_nudge()
        assert mod._has_placement_intent("set up a venv for the skill")
        assert mod._has_placement_intent("create virtualenv inside the directory")

    # --- False-positive guard: context-dependent keywords must NOT fire alone ---

    def test_proxy_without_placement_verb_does_not_trigger(self):
        """'proxy' alone must not nudge — only fires when a placement verb is present."""
        mod = _import_nudge()
        # Discussions of HTTP proxies that are NOT placement decisions
        assert not mod._has_placement_intent("configure an HTTP proxy for the requests library")
        assert not mod._has_placement_intent("what is a reverse proxy server")
        assert not mod._has_placement_intent("the proxy returned a 429 error")
        assert not mod._has_placement_intent("proxy authentication is failing")
        assert not mod._has_placement_intent("how does a forward proxy differ from a reverse proxy")

    def test_venv_without_placement_verb_does_not_trigger(self):
        """'venv' alone must not nudge — only fires when a placement verb is present."""
        mod = _import_nudge()
        # Discussions of venvs that are NOT placement decisions
        assert not mod._has_placement_intent("activate the venv before running tests")
        assert not mod._has_placement_intent("the venv is missing the requests package")
        assert not mod._has_placement_intent("deactivate the venv after you're done")
        assert not mod._has_placement_intent("check if the venv has numpy installed")
        assert not mod._has_placement_intent("my venv keeps breaking after pip update")

    def test_hook_returns_context_when_triggered(self):
        from UserPromptSubmit_modules.base import HookContext

        mod = _import_nudge()
        ctx = HookContext(prompt="where to put the proxy venv", data={})
        result = mod.ownership_colocation_nudge_hook(ctx)
        assert result.context is not None
        assert "Who Exclusively Owns This" in result.context or "consumer" in result.context.lower()

    def test_hook_returns_empty_when_not_triggered(self):
        from UserPromptSubmit_modules.base import HookContext

        mod = _import_nudge()
        ctx = HookContext(prompt="run the tests please", data={})
        result = mod.ownership_colocation_nudge_hook(ctx)
        assert result.context is None or result.context == ""

    def test_nudge_text_contains_checklist_steps(self):
        from UserPromptSubmit_modules.base import HookContext

        mod = _import_nudge()
        ctx = HookContext(prompt="create a new proxy directory", data={})
        result = mod.ownership_colocation_nudge_hook(ctx)
        assert result.context is not None
        nudge = result.context
        # Must contain the three decision points
        assert "consumer" in nudge.lower()
        assert "INSIDE" in nudge or "inside" in nudge.lower()
        assert "sibling" in nudge.lower() or "peer" in nudge.lower() or "Pattern 6" in nudge


# ---------------------------------------------------------------------------
# PreToolUse gate — subprocess tests (exact wire format)
# ---------------------------------------------------------------------------

GATE_SCRIPT = HOOKS_DIR / "PreToolUse_ownership_colocation_gate.py"


def _run_gate(tool_name: str, file_path: str, prompt: str = "") -> dict:
    """Execute the gate subprocess and return parsed JSON output."""
    payload = {
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
        "prompt": prompt,
    }
    result = subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )
    return json.loads(result.stdout)


class TestOwnershipColocationGate:
    """Subprocess tests for PreToolUse_ownership_colocation_gate."""

    # --- Non-write tools pass through ---

    def test_read_tool_always_allowed(self):
        out = _run_gate("Read", ".claude/proxy/litellm/config.yaml")
        assert out["continue"] is True

    def test_bash_tool_always_allowed(self):
        out = _run_gate("Bash", ".claude/proxy/litellm/runner.py")
        assert out["continue"] is True

    # --- Writes outside monitored paths are allowed ---

    def test_write_to_skills_allowed(self):
        out = _run_gate("Write", ".claude/skills/ai-api/proxy/config.yaml")
        assert out["continue"] is True

    def test_write_to_hooks_allowed(self):
        out = _run_gate("Write", ".claude/hooks/my_hook.py")
        assert out["continue"] is True

    def test_write_to_packages_allowed(self):
        out = _run_gate("Write", "packages/some-lib/src/module.py")
        assert out["continue"] is True

    # --- STRICT_PATHS are blocked ---

    def test_write_to_claude_proxy_blocked(self):
        out = _run_gate("Write", ".claude/proxy/litellm/config.yaml")
        assert out["continue"] is False
        assert "--allow-shared-infra" in out.get("reason", "")

    def test_edit_to_claude_proxy_blocked(self):
        out = _run_gate("Edit", ".claude/proxy/litellm/runner.py")
        assert out["continue"] is False

    def test_write_to_claude_infrastructure_blocked(self):
        out = _run_gate("Write", ".claude/infrastructure/docker-compose.yml")
        assert out["continue"] is False

    def test_write_to_claude_adapters_blocked(self):
        out = _run_gate("Write", ".claude/adapters/openai/client.py")
        assert out["continue"] is False

    # --- Bypass flag allows strict-path writes ---

    def test_bypass_flag_allows_strict_path_write(self):
        out = _run_gate(
            "Write", ".claude/proxy/litellm/config.yaml", prompt="set this up --allow-shared-infra"
        )
        assert out["continue"] is True

    # --- ADVISORY_PATHS are silently allowed ---

    def test_write_to_claude_shared_allowed(self):
        out = _run_gate("Write", ".claude/shared/utils.py")
        assert out["continue"] is True

    def test_write_to_claude_lib_allowed(self):
        out = _run_gate("Write", ".claude/lib/helpers.py")
        assert out["continue"] is True

    def test_write_to_claude_double_underscore_lib_allowed(self):
        out = _run_gate("Write", ".claude/__lib/helpers.py")
        assert out["continue"] is True

    def test_write_to_claude_utils_allowed(self):
        out = _run_gate("Write", ".claude/utils/common.py")
        assert out["continue"] is True

    # --- Malformed input fails open ---

    def test_malformed_json_allows(self):
        result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT)],
            input="not json at all",
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = json.loads(result.stdout)
        assert out["continue"] is True

    def test_empty_file_path_allows(self):
        out = _run_gate("Write", "")
        assert out["continue"] is True

    # --- Block message quality ---

    def test_block_message_contains_helpful_guidance(self):
        out = _run_gate("Write", ".claude/proxy/litellm/config.yaml")
        reason = out.get("reason", "")
        assert "consumer" in reason.lower()
        assert "Pattern 6" in reason or "questioning_patterns" in reason

    # --- Windows-style backslash paths ---

    def test_windows_backslash_path_blocked(self):
        out = _run_gate("Write", r".claude\proxy\litellm\config.yaml")
        assert out["continue"] is False


# ---------------------------------------------------------------------------
# Integration test — UserPromptSubmit.py dispatch chain (Action 4)
# ---------------------------------------------------------------------------

UPS_SCRIPT = HOOKS_DIR / "UserPromptSubmit.py"


def _run_ups(prompt: str) -> dict:
    """Invoke UserPromptSubmit.py as a subprocess and return parsed JSON output."""
    payload = {"prompt": prompt}
    result = subprocess.run(
        [sys.executable, str(UPS_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(result.stdout)


class TestOwnershipColocationUPSIntegration:
    """Integration tests: UPS.py → registry → nudge → additionalContext injection."""

    def test_placement_prompt_injects_nudge_context(self):
        """End-to-end: placement-intent prompt reaches the nudge and returns context."""
        out = _run_ups("where to put the proxy venv")
        # Context is nested under hookSpecificOutput.additionalContext
        ctx = out.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert (
            "OWNERSHIP-COLOCATION" in ctx or "consumer" in ctx.lower()
        ), f"Expected nudge context, got: {ctx!r:.200}"

    def test_non_placement_prompt_returns_no_nudge_context(self):
        """Non-placement prompt must not inject the nudge (avoid noise)."""
        out = _run_ups("please run the tests")
        ctx = out.get("hookSpecificOutput", {}).get("additionalContext", "")
        # Either no context, or context from OTHER hooks — must not contain the nudge header
        assert (
            "OWNERSHIP-COLOCATION CHECK" not in ctx
        ), f"Nudge fired on non-placement prompt: {ctx!r:.200}"

    def test_nudge_context_contains_all_three_decision_points(self):
        """Nudge text in the full dispatch must include the three checklist items."""
        out = _run_ups("create a new directory for the infra")
        ctx = out.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "consumer" in ctx.lower()
        assert "INSIDE" in ctx or "inside" in ctx.lower()
        assert "sibling" in ctx.lower() or "peer" in ctx.lower() or "Pattern 6" in ctx
