# Snapshot V3 Router Resilience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the snapshot plugin reliably preserve and restore Claude Code work state across manual compaction, automatic compaction, failed compaction, session restart, and first prompt after compaction.

**Architecture:** Claude Code hook activation is owned by `P:/.claude/settings.json` plus routers, not plugin `hooks.json`. Snapshot V3 keeps stable router entrypoints and refactors internals into capture, storage, restore, and diagnostics modules behind those entrypoints.

**Tech Stack:** Python 3.14, pytest, Claude Code hook JSON protocol, `P:/.claude/settings.json`, package source at `P:/packages/.claude-marketplace/plugins/snapshot`.

---

## Source Of Truth

The worker must treat these paths as authoritative:

- Runtime hook registration: `P:/.claude/settings.json`
- Local hook router/importer: `P:/.claude/hooks/__lib/hook_importer.py`
- Snapshot package source: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks`
- Snapshot package tests: `P:/packages/.claude-marketplace/plugins/snapshot/tests` and `P:/packages/.claude-marketplace/plugins/snapshot/scripts/tests`
- Snapshot package docs: `P:/packages/.claude-marketplace/plugins/snapshot/README.md`, `P:/packages/.claude-marketplace/plugins/snapshot/AGENTS.md`, and `P:/packages/.claude-marketplace/plugins/snapshot/docs`

Do not treat these as runtime authority:

- `P:/packages/.claude-marketplace/plugins/snapshot/hooks/hooks.json`
- `P:/packages/.claude-marketplace/plugins/snapshot/hooks/hooks.json.disabled`
- root-level `hooks.json` files
- stale `handoff/core` references in docs

## File Structure Target

- Modify `P:/.claude/settings.json`
  - Add a `PreCompact` matcher that invokes the snapshot router through the same explicit command style already used by other hooks.

- Modify `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py`
  - Keep this as the stable PreCompact router entrypoint.
  - Make child hook failures fail open unless a child explicitly returns `decision: block`.

- Modify `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_SessionStart.py`
  - Keep this as the stable SessionStart router entrypoint.
  - Preserve shared restore output and avoid stdout-only restore context.

- Modify `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_UserPromptSubmit.py`
  - Keep this as the stable first-prompt-after-compaction recovery path.

- Create `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib/runtime_contract.py`
  - Define active snapshot hook entrypoints and expected settings commands in one place.

- Create `P:/packages/.claude-marketplace/plugins/snapshot/scripts/doctor.py`
  - Diagnose settings registration, importability, writable state roots, latest snapshot status, and restore eligibility.

- Create `P:/packages/.claude-marketplace/plugins/snapshot/docs/router-runtime-contract.md`
  - Document why settings/router registration is authoritative and plugin `hooks.json` is not.

- Modify `P:/packages/.claude-marketplace/plugins/snapshot/README.md`
  - Replace stale `handoff/core` and `hooks.json` activation guidance with router-based activation.

- Modify `P:/packages/.claude-marketplace/plugins/snapshot/AGENTS.md`
  - Tell future agents to inspect settings/router wiring first.

- Create or modify tests:
  - `P:/packages/.claude-marketplace/plugins/snapshot/scripts/tests/test_runtime_contract.py`
  - `P:/packages/.claude-marketplace/plugins/snapshot/scripts/tests/test_router_smoke.py`
  - `P:/packages/.claude-marketplace/plugins/snapshot/scripts/tests/test_doctor.py`
  - Existing snapshot tests should remain green.

---

### Task 1: Capture Current Baseline

**Files:**
- Read: `P:/.claude/settings.json`
- Read: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py`
- Read: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_SessionStart.py`
- Read: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_UserPromptSubmit.py`

- [ ] **Step 1: Check git state**

Run:

```powershell
git -C P:\ status --short
git -C P:\packages\.claude-marketplace\plugins\snapshot status --short
```

Expected: output may show unrelated dirty files. Record only files touched by this plan and do not revert unrelated changes.

- [ ] **Step 2: Verify current live hook registration**

Run:

```powershell
rg -n '"PreCompact"|"SessionStart"|"UserPromptSubmit"|snapshot_PreCompact|snapshot_SessionStart|snapshot_UserPromptSubmit' P:\.claude\settings.json
```

Expected before implementation: `SessionStart` and `UserPromptSubmit` are present; `PreCompact` may be absent. If `PreCompact` is already present, keep the existing command only if it reaches `snapshot_PreCompact.py`.

- [ ] **Step 3: Run current focused snapshot tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_handoff_hooks.py P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_hook_schema_validation.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_handoff_integration.py -q -p no:cacheprovider
```

Expected: tests either pass or reveal pre-existing failures. If there are failures, capture the exact failing test names in the implementation notes before changing behavior.

### Task 2: Add Runtime Contract Module

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib/runtime_contract.py`
- Test: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/tests/test_runtime_contract.py`

- [ ] **Step 1: Write failing tests**

Create `scripts/tests/test_runtime_contract.py` with:

```python
from __future__ import annotations

from scripts.hooks.__lib.runtime_contract import (
    ACTIVE_SNAPSHOT_HOOKS,
    expected_settings_command,
    hook_names,
)


def test_active_snapshot_hooks_are_router_entrypoints() -> None:
    assert ACTIVE_SNAPSHOT_HOOKS["PreCompact"].endswith("scripts/hooks/snapshot_PreCompact.py")
    assert ACTIVE_SNAPSHOT_HOOKS["SessionStart"].endswith("scripts/hooks/snapshot_SessionStart.py")
    assert ACTIVE_SNAPSHOT_HOOKS["UserPromptSubmit"].endswith("scripts/hooks/snapshot_UserPromptSubmit.py")


def test_hook_names_are_stable() -> None:
    assert hook_names() == ("PreCompact", "SessionStart", "UserPromptSubmit")


def test_expected_settings_command_uses_absolute_package_path() -> None:
    command = expected_settings_command("PreCompact")
    assert "P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py" in command
    assert "$CLAUDE_PLUGIN_ROOT" not in command
    assert "hooks.json" not in command
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_runtime_contract.py -q -p no:cacheprovider
```

Expected: FAIL with `ModuleNotFoundError` for `scripts.hooks.__lib.runtime_contract`.

- [ ] **Step 3: Implement runtime contract module**

Create `scripts/hooks/__lib/runtime_contract.py`:

```python
from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path("P:/packages/.claude-marketplace/plugins/snapshot")

ACTIVE_SNAPSHOT_HOOKS: dict[str, str] = {
    "PreCompact": "scripts/hooks/snapshot_PreCompact.py",
    "SessionStart": "scripts/hooks/snapshot_SessionStart.py",
    "UserPromptSubmit": "scripts/hooks/snapshot_UserPromptSubmit.py",
}


def hook_names() -> tuple[str, ...]:
    return tuple(ACTIVE_SNAPSHOT_HOOKS.keys())


def hook_path(hook_name: str) -> Path:
    try:
        relative = ACTIVE_SNAPSHOT_HOOKS[hook_name]
    except KeyError as exc:
        raise ValueError(f"unknown snapshot hook: {hook_name}") from exc
    return PACKAGE_ROOT / relative


def expected_settings_command(hook_name: str) -> str:
    path = str(hook_path(hook_name)).replace("\\", "/")
    return f'python "{path}"'
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_runtime_contract.py -q -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\snapshot add scripts\hooks\__lib\runtime_contract.py scripts\tests\test_runtime_contract.py
git -C P:\packages\.claude-marketplace\plugins\snapshot commit -m "feat: define snapshot runtime hook contract"
```

### Task 3: Validate Live Settings Registration

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/tests/test_router_smoke.py`
- Modify: `P:/.claude/settings.json`

- [ ] **Step 1: Write failing settings validation test**

Create `scripts/tests/test_router_smoke.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path

from scripts.hooks.__lib.runtime_contract import expected_settings_command


SETTINGS_PATH = Path("P:/.claude/settings.json")


def _commands_for_event(settings: dict, event_name: str) -> list[str]:
    commands: list[str] = []
    for matcher in settings.get("hooks", {}).get(event_name, []):
        for hook in matcher.get("hooks", []):
            command = hook.get("command")
            if isinstance(command, str):
                commands.append(command.replace("\\", "/"))
    return commands


def test_precompact_registered_in_live_settings() -> None:
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    commands = _commands_for_event(settings, "PreCompact")
    expected = expected_settings_command("PreCompact").replace("\\", "/")
    assert expected in commands


def test_sessionstart_uses_snapshot_router_or_global_importer() -> None:
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    commands = _commands_for_event(settings, "SessionStart")
    joined = "\n".join(commands)
    assert "snapshot_SessionStart.py" in joined or "execute_hook('SessionStart'" in joined


def test_userpromptsubmit_uses_snapshot_router_or_global_importer() -> None:
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    commands = _commands_for_event(settings, "UserPromptSubmit")
    joined = "\n".join(commands)
    assert "snapshot_UserPromptSubmit.py" in joined or "execute_hook('UserPromptSubmit'" in joined
```

- [ ] **Step 2: Run test to verify current PreCompact gap**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_router_smoke.py::test_precompact_registered_in_live_settings -q -p no:cacheprovider
```

Expected before registration: FAIL if `PreCompact` is missing from live settings.

- [ ] **Step 3: Edit live settings to register PreCompact**

Modify `P:/.claude/settings.json` so `hooks.PreCompact` contains this matcher:

```json
"PreCompact": [
  {
    "matcher": ".*",
    "hooks": [
      {
        "type": "command",
        "command": "python \"P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py\"",
        "timeout": 45
      }
    ]
  }
]
```

If `PreCompact` already exists, add this command to the existing matcher instead of replacing unrelated commands.

- [ ] **Step 4: Run settings validation tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_router_smoke.py -q -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Commit package test changes and leave live settings unstaged unless repository policy allows it**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\snapshot add scripts\tests\test_router_smoke.py
git -C P:\packages\.claude-marketplace\plugins\snapshot commit -m "test: validate snapshot router registration"
```

Do not commit `P:/.claude/settings.json` if it contains local secrets or machine-local configuration. Record the settings change in final notes.

### Task 4: Make PreCompact Router Fail Open

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py`
- Test: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/tests/test_router_smoke.py`

- [ ] **Step 1: Add failing test for child exception behavior**

Append to `scripts/tests/test_router_smoke.py`:

```python
import importlib.util
import sys


def _load_precompact_router():
    path = Path("P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py")
    spec = importlib.util.spec_from_file_location("snapshot_precompact_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_precompact_child_exception_fails_open(monkeypatch, tmp_path) -> None:
    router = _load_precompact_router()
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text('{"type":"user","message":{"content":"continue task"}}\n', encoding="utf-8")

    def raises(_data):
        raise RuntimeError("simulated child failure")

    monkeypatch.setattr(router, "SEQUENCE", [("broken", raises)])

    payload = {
        "session_id": "test-session",
        "transcript_path": str(transcript),
        "cwd": str(tmp_path),
        "hook_event_name": "PreCompact",
        "trigger": "manual",
    }

    result = router.run_router(payload)
    assert result["decision"] == "approve"
    assert "broken" in result["reason"]
    assert "failed but compaction continues" in result["additionalContext"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_router_smoke.py::test_precompact_child_exception_fails_open -q -p no:cacheprovider
```

Expected: FAIL because `snapshot_PreCompact.py` does not expose `run_router` and currently exits/block-fails on child crash.

- [ ] **Step 3: Refactor PreCompact router into callable function**

Modify `snapshot_PreCompact.py` so it contains:

```python
def run_router(data: dict) -> dict:
    missing = _REQUIRED_INPUT_FIELDS - set(data.keys())
    if missing:
        reason = f"PreCompact: missing required fields: {', '.join(sorted(missing))}"
        _log.warning(reason)
        return {"decision": "block", "reason": reason}

    warnings = []
    for name, run_func in SEQUENCE:
        try:
            result = run_func(data)
            if result:
                if result.get("decision") == "block":
                    result.setdefault("additionalContext", "")
                    result["additionalContext"] += "\n\nCompaction issue? Run snapshot doctor to check runtime health."
                    return result
                warnings.append((name, result))
        except Exception as exc:
            _log.error("PreCompact child hook '%s' crashed: %s", name, exc, exc_info=True)
            warnings.append((
                name,
                {
                    "decision": "approve",
                    "reason": f"PreCompact child hook '{name}' failed but compaction continues: {exc}",
                    "additionalContext": f"Snapshot PreCompact child '{name}' failed but compaction continues: {exc}",
                },
            ))

    if warnings:
        final_output = dict(warnings[0][1])
        if len(warnings) > 1:
            reasons = [item[1].get("reason", item[0]) for item in warnings]
            final_output["reason"] = " + ".join(reasons)
        final_output.setdefault("decision", "approve")
        return final_output

    return {"decision": "approve", "reason": "PreCompact: all child hooks silent"}
```

Then make `main()` parse stdin and print `json.dumps(run_router(data), indent=2)`.

- [ ] **Step 4: Run focused test**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_router_smoke.py::test_precompact_child_exception_fails_open -q -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Run schema tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_hook_schema_validation.py P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_router_smoke.py -q -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\snapshot add scripts\hooks\snapshot_PreCompact.py scripts\tests\test_router_smoke.py
git -C P:\packages\.claude-marketplace\plugins\snapshot commit -m "fix: make snapshot precompact router fail open"
```

### Task 5: Add Snapshot Doctor

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/doctor.py`
- Test: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/tests/test_doctor.py`

- [ ] **Step 1: Write failing doctor tests**

Create `scripts/tests/test_doctor.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from scripts import doctor


def test_find_hook_command_detects_registered_command(tmp_path: Path) -> None:
    settings = {
        "hooks": {
            "PreCompact": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python \"P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py\"",
                        }
                    ],
                }
            ]
        }
    }
    assert doctor.find_hook_command(settings, "PreCompact", "snapshot_PreCompact.py")


def test_find_hook_command_returns_false_when_missing() -> None:
    assert not doctor.find_hook_command({"hooks": {}}, "PreCompact", "snapshot_PreCompact.py")


def test_run_checks_reports_missing_precompact(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps({"hooks": {}}), encoding="utf-8")

    report = doctor.run_checks(settings_path=settings_path, project_root=tmp_path)

    assert report["checks"]["precompact_registered"]["ok"] is False
    assert "snapshot_PreCompact.py" in report["checks"]["precompact_registered"]["message"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_doctor.py -q -p no:cacheprovider
```

Expected: FAIL because `scripts/doctor.py` does not exist.

- [ ] **Step 3: Implement doctor module**

Create `scripts/doctor.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS_PATH = Path("P:/.claude/settings.json")
DEFAULT_PROJECT_ROOT = Path("P:")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": f"{type(exc).__name__}: {exc}"}


def find_hook_command(settings: dict[str, Any], event_name: str, filename: str) -> bool:
    for matcher in settings.get("hooks", {}).get(event_name, []):
        for hook in matcher.get("hooks", []):
            command = hook.get("command", "")
            if isinstance(command, str) and filename in command.replace("\\", "/"):
                return True
    return False


def _check_settings_loaded(settings: dict[str, Any]) -> dict[str, Any]:
    if "_load_error" in settings:
        return {"ok": False, "message": settings["_load_error"]}
    return {"ok": True, "message": "settings loaded"}


def _check_writable(path: Path) -> dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".snapshot_doctor_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return {"ok": True, "message": f"writable: {path}"}
    except Exception as exc:
        return {"ok": False, "message": f"not writable: {path}: {exc}"}


def run_checks(
    settings_path: Path = DEFAULT_SETTINGS_PATH,
    project_root: Path = DEFAULT_PROJECT_ROOT,
) -> dict[str, Any]:
    settings = load_json(settings_path)
    state_root = project_root / ".claude" / ".artifacts"
    checks = {
        "settings_loaded": _check_settings_loaded(settings),
        "precompact_registered": {
            "ok": find_hook_command(settings, "PreCompact", "snapshot_PreCompact.py"),
            "message": "expected PreCompact command containing snapshot_PreCompact.py",
        },
        "sessionstart_registered": {
            "ok": find_hook_command(settings, "SessionStart", "snapshot_SessionStart.py")
            or any("execute_hook('SessionStart'" in str(hook) for hook in settings.get("hooks", {}).get("SessionStart", [])),
            "message": "expected SessionStart snapshot router or global importer",
        },
        "userpromptsubmit_registered": {
            "ok": find_hook_command(settings, "UserPromptSubmit", "snapshot_UserPromptSubmit.py")
            or any("execute_hook('UserPromptSubmit'" in str(hook) for hook in settings.get("hooks", {}).get("UserPromptSubmit", [])),
            "message": "expected UserPromptSubmit snapshot router or global importer",
        },
        "artifact_root_writable": _check_writable(state_root),
    }
    return {"ok": all(item["ok"] for item in checks.values()), "checks": checks}


def main() -> int:
    report = run_checks()
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run doctor tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_doctor.py -q -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Run doctor manually**

Run:

```powershell
python P:\packages\.claude-marketplace\plugins\snapshot\scripts\doctor.py
```

Expected after Task 3: JSON report with `"ok": true`. If `"ok": false`, fix registration before continuing.

- [ ] **Step 6: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\snapshot add scripts\doctor.py scripts\tests\test_doctor.py
git -C P:\packages\.claude-marketplace\plugins\snapshot commit -m "feat: add snapshot runtime doctor"
```

### Task 6: Add End-To-End Compaction Recovery Smoke

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/tests/test_router_smoke.py`

- [ ] **Step 1: Add test that executes PreCompact router as a process**

Append to `scripts/tests/test_router_smoke.py`:

```python
import json
import subprocess


def test_precompact_router_process_creates_recoverable_output(tmp_path: Path, monkeypatch) -> None:
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        '{"type":"user","message":{"content":"Fix the snapshot runtime registration"}}\n'
        '{"type":"assistant","message":{"content":"I am checking settings and tests"}}\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("SNAPSHOT_PROJECT_ROOT", str(tmp_path))

    payload = {
        "session_id": "session-1",
        "transcript_path": str(transcript),
        "cwd": str(tmp_path),
        "hook_event_name": "PreCompact",
        "trigger": "manual",
    }
    result = subprocess.run(
        [
            sys.executable,
            "P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py",
        ],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["decision"] == "approve"
    assert "reason" in output
```

- [ ] **Step 2: Run the process smoke test**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_router_smoke.py::test_precompact_router_process_creates_recoverable_output -q -p no:cacheprovider
```

Expected: PASS. If it fails because child capture requires additional transcript shape, update the fixture to match real transcript structure from `tests/conftest.py`.

- [ ] **Step 3: Verify existing first-prompt recovery marker coverage**

Run the existing one-shot recovery test:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\tests\test_handoff_task_injector.py::TestSuccessfulRecovery::test_marker_cleared_after_injection -q -p no:cacheprovider
```

Expected: PASS. This proves first-prompt recovery injects once and then clears the marker.

- [ ] **Step 4: Run recovery tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\tests\test_handoff_task_injector.py P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_router_smoke.py -q -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\snapshot add scripts\tests\test_router_smoke.py tests\test_handoff_task_injector.py
git -C P:\packages\.claude-marketplace\plugins\snapshot commit -m "test: cover snapshot compaction recovery path"
```

### Task 7: Document Router Runtime Contract

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/snapshot/docs/router-runtime-contract.md`
- Modify: `P:/packages/.claude-marketplace/plugins/snapshot/README.md`
- Modify: `P:/packages/.claude-marketplace/plugins/snapshot/AGENTS.md`
- Modify: `P:/packages/.claude-marketplace/plugins/snapshot/docs/adr/001-brownfield-conversion.md`

- [ ] **Step 1: Add router runtime contract doc**

Create `docs/router-runtime-contract.md`:

```markdown
# Snapshot Router Runtime Contract

Snapshot hook activation in this workspace is owned by `P:/.claude/settings.json` and router entrypoints under `scripts/hooks`.

Claude Code plugin `hooks.json` files are not the operational source of truth for this package. Keep `hooks/hooks.json` empty or archival unless Claude Code hook loading behavior changes and the change is verified with a live hook smoke test.

## Active Runtime Entry Points

- `PreCompact` -> `scripts/hooks/snapshot_PreCompact.py`
- `SessionStart` -> `scripts/hooks/snapshot_SessionStart.py`
- `UserPromptSubmit` -> `scripts/hooks/snapshot_UserPromptSubmit.py`

## Required Live Registration

`P:/.claude/settings.json` must include a `PreCompact` matcher that runs:

```json
{
  "type": "command",
  "command": "python \"P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py\"",
  "timeout": 45
}
```

`SessionStart` and `UserPromptSubmit` may run through direct snapshot commands or through the global hook importer, as long as router smoke tests prove the snapshot modules are reachable.

## Verification

Run:

```powershell
python P:\packages\.claude-marketplace\plugins\snapshot\scripts\doctor.py
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests\test_router_smoke.py -q -p no:cacheprovider
```
```

- [ ] **Step 2: Update README**

Replace stale setup sections that mention `P://packages/handoff/core` or `hooks/hooks.json` as active registration with a link to `docs/router-runtime-contract.md`. Keep feature descriptions that describe capture and restore behavior.

- [ ] **Step 3: Update AGENTS**

Add this near the top:

```markdown
## Runtime Source Of Truth

For this workspace, snapshot hooks are activated from `P:/.claude/settings.json` through router entrypoints. Do not treat plugin `hooks.json` as the active registration path. Before changing behavior, run `python scripts/doctor.py` and inspect `scripts/hooks/snapshot_PreCompact.py`, `scripts/hooks/snapshot_SessionStart.py`, and `scripts/hooks/snapshot_UserPromptSubmit.py`.
```

Remove or correct instructions that point to `P://packages/handoff/core`.

- [ ] **Step 4: Update ADR**

In `docs/adr/001-brownfield-conversion.md`, add a superseding note at the top:

```markdown
> Superseded runtime note, 2026-06-07: The original decision expected plugin `hooks/hooks.json` auto-registration. In this workspace, live activation is now owned by `P:/.claude/settings.json` and snapshot router entrypoints because plugin hook loading is not reliable enough for this package's compaction recovery role.
```

- [ ] **Step 5: Verify docs no longer point to stale runtime paths**

Run:

```powershell
rg -n "packages/handoff/core|src/handoff|hooks/hooks.json.*Hook registration|CLAUDE_PLUGIN_ROOT.*snapshot" P:\packages\.claude-marketplace\plugins\snapshot\README.md P:\packages\.claude-marketplace\plugins\snapshot\AGENTS.md P:\packages\.claude-marketplace\plugins\snapshot\docs
```

Expected: no stale activation guidance remains in README or AGENTS. Historical docs may still mention old paths only if clearly labeled historical or superseded.

- [ ] **Step 6: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\snapshot add README.md AGENTS.md docs\router-runtime-contract.md docs\adr\001-brownfield-conversion.md
git -C P:\packages\.claude-marketplace\plugins\snapshot commit -m "docs: document snapshot router runtime contract"
```

### Task 8: Characterize Before Modular Refactor

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/snapshot/tests/test_handoff_integration.py`
- Modify: `P:/packages/.claude-marketplace/plugins/snapshot/tests/test_restoration_message.py`

- [ ] **Step 1: Add characterization for restore quality contract**

Add a test to `tests/test_restoration_message.py`:

```python
def test_restore_message_contains_required_machine_sections(sample_valid_envelope):
    from scripts.hooks.__lib.snapshot_v2 import build_restore_message_compact

    message = build_restore_message_compact(sample_valid_envelope)

    assert "<compact-restore>" in message
    assert "session_identity:" in message
    assert "work_state:" in message
    assert "working_set:" in message
    assert "tool_queue:" in message
    assert "open_questions:" in message
    assert "active_decisions:" in message
```

If `sample_valid_envelope` does not exist, use the existing valid envelope helper in the file or create a local fixture with `resume_snapshot`, `decision_register`, `evidence_index`, and `checksum`.

- [ ] **Step 2: Run characterization tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\tests\test_restoration_message.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_handoff_integration.py -q -p no:cacheprovider
```

Expected: PASS before refactor. If a required section name differs, align the test with the current shared renderer and document the actual contract in `docs/router-runtime-contract.md`.

- [ ] **Step 3: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\snapshot add tests\test_restoration_message.py tests\test_handoff_integration.py
git -C P:\packages\.claude-marketplace\plugins\snapshot commit -m "test: characterize snapshot restore quality contract"
```

### Task 9: Refactor Internals Behind Stable Routers

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib/capture_pipeline.py`
- Create: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib/restore_pipeline.py`
- Modify: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/PreCompact_snapshot_capture.py`
- Modify: `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/SessionStart_snapshot_restore.py`

- [ ] **Step 1: Create capture pipeline facade**

Create `scripts/hooks/__lib/capture_pipeline.py`:

```python
from __future__ import annotations

from typing import Any

from scripts.hooks import PreCompact_snapshot_capture


def capture_snapshot(input_data: dict[str, Any]) -> dict[str, Any]:
    return PreCompact_snapshot_capture.run(input_data)
```

- [ ] **Step 2: Create restore pipeline facade**

Create `scripts/hooks/__lib/restore_pipeline.py`:

```python
from __future__ import annotations

from typing import Any

from scripts.hooks import SessionStart_snapshot_restore


def restore_snapshot(input_data: dict[str, Any]) -> dict[str, Any]:
    return SessionStart_snapshot_restore.run(input_data)
```

- [ ] **Step 3: Use facade modules in routers**

In `snapshot_PreCompact.py`, replace direct import of `PreCompact_snapshot_capture as capture` with:

```python
from scripts.hooks.__lib.capture_pipeline import capture_snapshot
```

Set:

```python
SEQUENCE = [
    ("capture", capture_snapshot),
    ("commitments", commitments.run),
]
```

In `snapshot_SessionStart.py`, replace direct import of `SessionStart_snapshot_restore as restore` with:

```python
from scripts.hooks.__lib.restore_pipeline import restore_snapshot
```

Set:

```python
SEQUENCE = [
    ("restore", restore_snapshot),
    ("tldr", tldr.run),
    ("identity_capture", identity_capture.run),
]
```

- [ ] **Step 4: Run full focused tests**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests P:\packages\.claude-marketplace\plugins\snapshot\tests\test_handoff_integration.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_handoff_full_integration.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_terminal_isolation.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_p0_filelock_toctou.py -q -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git -C P:\packages\.claude-marketplace\plugins\snapshot add scripts\hooks\__lib\capture_pipeline.py scripts\hooks\__lib\restore_pipeline.py scripts\hooks\snapshot_PreCompact.py scripts\hooks\snapshot_SessionStart.py
git -C P:\packages\.claude-marketplace\plugins\snapshot commit -m "refactor: route snapshot internals through pipeline facades"
```

### Deferred Opportunity: Low-Frequency Checkpointing

Do not implement periodic checkpointing in this plan. It should be a separate plan after live `PreCompact`, `SessionStart`, and `UserPromptSubmit` recovery pass router-level smoke tests.

The follow-up design should use `Stop` before `PostToolUse`, a minimum 10-minute interval, and a content hash over goal, active files, blockers, and pending operations. It must prove low state churn before live registration.

### Task 10: Final Verification And Handoff

**Files:**
- Read: all modified files
- Read: git status

- [ ] **Step 1: Run final focused suite**

Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\snapshot\scripts\tests P:\packages\.claude-marketplace\plugins\snapshot\tests\test_envelope_schema_validation.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_handoff_integration.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_handoff_full_integration.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_terminal_isolation.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_p0_filelock_toctou.py P:\packages\.claude-marketplace\plugins\snapshot\tests\test_restoration_message.py -q -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 2: Run doctor**

Run:

```powershell
python P:\packages\.claude-marketplace\plugins\snapshot\scripts\doctor.py
```

Expected: `"ok": true`.

- [ ] **Step 3: Verify stale path cleanup**

Run:

```powershell
rg -n "packages/handoff/core|src/handoff|CLAUDE_PLUGIN_ROOT.*snapshot|hooks/hooks.json.*auto" P:\packages\.claude-marketplace\plugins\snapshot\README.md P:\packages\.claude-marketplace\plugins\snapshot\AGENTS.md P:\packages\.claude-marketplace\plugins\snapshot\docs
```

Expected: only historical docs with explicit superseded notes, or no output.

- [ ] **Step 4: Summarize live settings delta**

Run:

```powershell
git -C P:\ diff -- P:\.claude\settings.json
```

Expected: only the intended `PreCompact` registration or no diff if settings are not tracked. Include this diff summary in the final handoff.

- [ ] **Step 5: Commit parent repo gitlink if snapshot is a submodule**

Run:

```powershell
git -C P:\ status --short
```

If `packages/.claude-marketplace/plugins/snapshot` appears as a gitlink change in `P:\`, commit it:

```powershell
git -C P:\ add packages\.claude-marketplace\plugins\snapshot
git -C P:\ commit -m "chore: update snapshot plugin"
```

If `P:/.claude/settings.json` is intentionally local-only, do not commit it.

## Rollback

Rollback should be narrow:

- To disable active capture: remove only the `PreCompact` snapshot command from `P:/.claude/settings.json`.
- To disable post-compact first-prompt restore: set `SNAPSHOT_TASK_INJECTOR_ENABLED=false`.
- To revert package changes: revert the snapshot plugin commits made by this plan.
- Do not delete snapshot state files during rollback unless the user asks; they may contain useful recovery context.

## Completion Criteria

The implementation is complete when:

- `python P:\packages\.claude-marketplace\plugins\snapshot\scripts\doctor.py` returns `"ok": true`.
- Router smoke tests prove `PreCompact` is reachable through live settings.
- Manual process smoke proves `snapshot_PreCompact.py` returns `decision: approve` and does not block compaction on child failure.
- SessionStart and first-prompt recovery share the compact restore renderer.
- README and AGENTS tell future agents to use settings/router registration, not plugin `hooks.json`.
- Focused snapshot tests pass with `-p no:cacheprovider`.
