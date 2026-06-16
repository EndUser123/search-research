from __future__ import annotations

import json
from pathlib import Path

from active_hook_inventory import (
    build_inventory,
    expand_router,
    find_hooks_json_declarations,
    iter_settings_commands,
)


def test_iter_settings_commands_reads_hook_commands(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python P:/plugin/__lib/router.py PreToolUse",
                                    "timeout": 10,
                                }
                            ],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    commands = list(iter_settings_commands([settings_path]))

    assert len(commands) == 1
    assert commands[0].event == "PreToolUse"
    assert commands[0].matcher == "Bash"
    assert commands[0].command == "python P:/plugin/__lib/router.py PreToolUse"
    assert commands[0].timeout == 10


def test_expand_router_reads_simple_dispatch_table(tmp_path: Path) -> None:
    plugin_root = tmp_path / "example-plugin"
    router = plugin_root / "__lib" / "router.py"
    router.parent.mkdir(parents=True)
    (plugin_root / "hooks" / "pretool").mkdir(parents=True)
    (plugin_root / "hooks" / "stop").mkdir(parents=True)
    (plugin_root / "hooks" / "pretool" / "gate.py").write_text("", encoding="utf-8")
    (plugin_root / "hooks" / "stop" / "finish.py").write_text("", encoding="utf-8")
    router.write_text(
        """
from pathlib import Path
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_ROOT / "hooks"
PHASE_DIR = {"PreToolUse": "pretool", "Stop": "stop"}
PRETOOLUSE_HOOKS = ["gate.py"]
STOP_HOOKS = ["finish.py"]
DISPATCH = {"PreToolUse": PRETOOLUSE_HOOKS, "Stop": STOP_HOOKS}
""",
        encoding="utf-8",
    )

    expanded = expand_router(router)

    assert [(h.event, h.hook_name, h.hook_path.name, h.exists) for h in expanded] == [
        ("PreToolUse", "gate.py", "gate.py", True),
        ("Stop", "finish.py", "finish.py", True),
    ]


def test_find_hooks_json_declarations_marks_nonempty_files(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugins"
    active = plugin_root / "active" / "hooks" / "hooks.json"
    empty = plugin_root / "empty" / "hooks" / "hooks.json"
    active.parent.mkdir(parents=True)
    empty.parent.mkdir(parents=True)
    active.write_text(
        json.dumps({"hooks": {"UserPromptSubmit": [{"matcher": ".*", "hooks": []}]}}),
        encoding="utf-8",
    )
    empty.write_text(json.dumps({"hooks": {}}), encoding="utf-8")

    declarations = find_hooks_json_declarations(plugin_root)

    by_plugin = {d.plugin: d for d in declarations}
    assert by_plugin["active"].non_empty is True
    assert by_plugin["active"].events == ["UserPromptSubmit"]
    assert by_plugin["empty"].non_empty is False


def test_build_inventory_dedupes_router_implementation_rows(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugins"
    plugin = plugin_root / "example"
    router = plugin / "__lib" / "router.py"
    settings_a = tmp_path / "settings-a.json"
    settings_b = tmp_path / "settings-b.json"
    router.parent.mkdir(parents=True)
    (plugin / "hooks" / "pretool").mkdir(parents=True)
    (plugin / "hooks" / "pretool" / "gate.py").write_text("", encoding="utf-8")
    router.write_text(
        """
PHASE_DIR = {"PreToolUse": "pretool"}
PRETOOLUSE_HOOKS = ["gate.py"]
DISPATCH = {"PreToolUse": PRETOOLUSE_HOOKS}
""",
        encoding="utf-8",
    )
    settings_payload = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": ".*",
                    "hooks": [{"type": "command", "command": f"python {router} PreToolUse"}],
                }
            ]
        }
    }
    settings_a.write_text(json.dumps(settings_payload), encoding="utf-8")
    settings_b.write_text(json.dumps(settings_payload), encoding="utf-8")

    inventory = build_inventory([settings_a, settings_b], plugin_root)

    assert len(inventory["settings_commands"]) == 2
    assert len(inventory["router_hooks"]) == 1
