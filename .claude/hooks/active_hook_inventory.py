#!/usr/bin/env python3
"""Inventory the active Claude Code hook routing surface.

Current local contract:
settings.json -> plugin router -> hook modules.

Plugin hooks.json files are reported as declarations, but are not treated as
authoritative active routing unless they are also reached through settings or a
router. This matches the local workaround for the current plugin hooks.json
loading issue.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS_PATHS = (
    Path.home() / ".claude" / "settings.json",
    Path("P:/.claude/settings.json"),
)
DEFAULT_PLUGIN_ROOT = Path("P:/packages/.claude-marketplace/plugins")


@dataclass(frozen=True)
class HookCommand:
    settings_path: Path
    event: str
    matcher: str
    command: str
    timeout: int | None


@dataclass(frozen=True)
class RouterHook:
    router_path: Path
    plugin: str
    event: str
    hook_name: str
    hook_path: Path
    exists: bool
    enforcement_class: str


@dataclass(frozen=True)
class HooksJsonDeclaration:
    plugin: str
    path: Path
    non_empty: bool
    events: list[str]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_settings_commands(settings_paths: list[Path] | tuple[Path, ...]) -> list[HookCommand]:
    commands: list[HookCommand] = []
    for settings_path in settings_paths:
        if not settings_path.exists():
            continue
        data = _load_json(settings_path)
        hooks = data.get("hooks", {})
        if not isinstance(hooks, dict):
            continue
        for event, groups in hooks.items():
            if not isinstance(groups, list):
                continue
            for group in groups:
                if not isinstance(group, dict):
                    continue
                matcher = str(group.get("matcher") or "")
                for hook in group.get("hooks", []):
                    if not isinstance(hook, dict):
                        continue
                    if hook.get("type") != "command":
                        continue
                    command = str(hook.get("command") or "").strip()
                    if not command:
                        continue
                    timeout = hook.get("timeout")
                    commands.append(
                        HookCommand(
                            settings_path=settings_path,
                            event=str(event),
                            matcher=matcher,
                            command=command,
                            timeout=timeout if isinstance(timeout, int) else None,
                        )
                    )
    return commands


def _command_tokens(command: str) -> list[str]:
    # Current settings use simple unquoted absolute Python paths. Keep this
    # conservative; the inventory should report unknowns rather than guess.
    return command.strip().strip('"').split()


def router_invocation(command: str) -> tuple[Path, str] | None:
    tokens = _command_tokens(command)
    if len(tokens) < 3:
        return None
    if not tokens[0].lower().endswith("python"):
        return None
    router = Path(tokens[1].strip('"'))
    event = tokens[2].strip('"')
    normalized = str(router).replace("\\", "/")
    if not normalized.endswith("/router.py"):
        return None
    return router, event


def _plugin_from_router(router_path: Path) -> str:
    parts = [p.lower() for p in router_path.parts]
    try:
        idx = parts.index("plugins")
    except ValueError:
        return ""
    if idx + 1 < len(router_path.parts):
        return router_path.parts[idx + 1]
    return ""


def _plugin_root_from_router(router_path: Path) -> Path:
    plugin = _plugin_from_router(router_path)
    if not plugin:
        return router_path.parent.parent
    text = str(router_path).replace("\\", "/")
    marker = f"/plugins/{plugin}/"
    prefix = text.split(marker, 1)[0]
    return Path(f"{prefix}/plugins/{plugin}")


def _literal_string_list(node: ast.AST, names: dict[str, Any]) -> list[str] | None:
    if isinstance(node, ast.List):
        values: list[str] = []
        for elt in node.elts:
            if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
                return None
            values.append(elt.value)
        return values
    if isinstance(node, ast.Name):
        value = names.get(node.id)
        return value if isinstance(value, list) else None
    return None


def _literal_string_dict(node: ast.AST, names: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(node, ast.Dict):
        return None
    values: dict[str, Any] = {}
    for key, value in zip(node.keys, node.values):
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            return None
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            values[key.value] = value.value
        elif isinstance(value, ast.Name):
            values[key.value] = names.get(value.id)
        elif isinstance(value, ast.List):
            values[key.value] = _literal_string_list(value, names)
        else:
            return None
    return values


def _hook_subdir(router_path: Path, phase_dir: str) -> Path:
    plugin_root = _plugin_root_from_router(router_path)
    router_text = str(router_path).replace("\\", "/")
    if "/snapshot/" in router_text:
        base = plugin_root / "scripts" / "hooks"
    else:
        base = plugin_root / "hooks"
    return base / phase_dir if phase_dir else base


def _classify_hook(plugin: str, event: str, hook_name: str) -> str:
    name = f"{plugin} {event} {hook_name}".lower()
    if any(token in name for token in ("safety", "authority", "path_validator", "protected", "destructive", "risk", "permission", "deny")):
        return "safety"
    if any(token in name for token in ("tdd", "sdlc", "skill-guard", "delegation", "contract", "verification", "investigation")):
        return "authority"
    if any(token in name for token in ("model-router", "prompt", "nudge", "classify", "apply")):
        return "routing"
    if any(token in name for token in ("snapshot", "observability", "telemetry", "cache", "log")):
        return "telemetry"
    if event in {"PostToolUse", "SessionStart", "SessionEnd", "PreCompact"}:
        return "workflow"
    return "advisory"


def expand_router(router_path: Path) -> list[RouterHook]:
    if not router_path.exists():
        return []
    try:
        tree = ast.parse(router_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    names: dict[str, Any] = {}
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            continue
        target = stmt.targets[0].id
        string_list = _literal_string_list(stmt.value, names)
        if string_list is not None:
            names[target] = string_list
            continue
        string_dict = _literal_string_dict(stmt.value, names)
        if string_dict is not None:
            names[target] = string_dict

    dispatch = names.get("DISPATCH") or names.get("_DISPATCH")
    phase_dir = names.get("PHASE_DIR") or {}
    if not isinstance(dispatch, dict):
        return []

    plugin = _plugin_from_router(router_path)
    hooks: list[RouterHook] = []
    for event, hook_names in dispatch.items():
        if not isinstance(event, str) or not isinstance(hook_names, list):
            continue
        phase = phase_dir.get(event, "") if isinstance(phase_dir, dict) else ""
        if not isinstance(phase, str):
            phase = ""
        hook_dir = _hook_subdir(router_path, phase)
        for hook_name in hook_names:
            if not isinstance(hook_name, str):
                continue
            hook_path = hook_dir / hook_name
            hooks.append(
                RouterHook(
                    router_path=router_path,
                    plugin=plugin,
                    event=event,
                    hook_name=hook_name,
                    hook_path=hook_path,
                    exists=hook_path.exists(),
                    enforcement_class=_classify_hook(plugin, event, hook_name),
                )
            )
    return hooks


def find_hooks_json_declarations(plugin_root: Path) -> list[HooksJsonDeclaration]:
    declarations: list[HooksJsonDeclaration] = []
    if not plugin_root.exists():
        return declarations
    for path in sorted(plugin_root.rglob("hooks.json")):
        plugin = ""
        try:
            plugin = path.relative_to(plugin_root).parts[0]
        except ValueError:
            pass
        events: list[str] = []
        non_empty = False
        try:
            data = _load_json(path)
            root = data.get("hooks", data) if isinstance(data, dict) else {}
            if isinstance(root, dict) and root:
                non_empty = True
                events = sorted(str(k) for k in root.keys())
        except (OSError, json.JSONDecodeError):
            pass
        declarations.append(
            HooksJsonDeclaration(plugin=plugin, path=path, non_empty=non_empty, events=events)
        )
    return declarations


def build_inventory(settings_paths: list[Path], plugin_root: Path) -> dict[str, Any]:
    commands = iter_settings_commands(settings_paths)
    router_hooks: list[RouterHook] = []
    seen_router_hooks: set[tuple[str, str, str, str]] = set()
    active_router_paths: set[str] = set()
    for command in commands:
        invocation = router_invocation(command.command)
        if invocation is None:
            continue
        router_path, _event = invocation
        active_router_paths.add(str(router_path))
        for hook in expand_router(router_path):
            key = (
                str(hook.router_path).lower(),
                hook.event,
                hook.hook_name,
                str(hook.hook_path).lower(),
            )
            if key in seen_router_hooks:
                continue
            seen_router_hooks.add(key)
            router_hooks.append(hook)

    declarations = find_hooks_json_declarations(plugin_root)
    routed_plugins = {hook.plugin for hook in router_hooks if hook.plugin}
    settings_router_plugins = {
        _plugin_from_router(Path(path)) for path in active_router_paths if _plugin_from_router(Path(path))
    }
    non_authoritative = [
        declaration
        for declaration in declarations
        if declaration.non_empty and declaration.plugin not in routed_plugins | settings_router_plugins
    ]

    return {
        "settings_commands": [asdict(command) for command in commands],
        "router_hooks": [asdict(hook) for hook in router_hooks],
        "hooks_json_declarations": [asdict(declaration) for declaration in declarations],
        "non_authoritative_hooks_json": [asdict(declaration) for declaration in non_authoritative],
    }


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _print_markdown(inventory: dict[str, Any]) -> None:
    print("# Active Hook Inventory")
    print()
    print("## Settings Router Commands")
    for row in inventory["settings_commands"]:
        print(f"- {row['event']} `{row['matcher'] or '.*'}`: `{row['command']}`")
    print()
    print("## Router-Expanded Hooks")
    for row in inventory["router_hooks"]:
        status = "exists" if row["exists"] else "missing"
        print(
            f"- {row['plugin']} {row['event']} {row['hook_name']} "
            f"({row['enforcement_class']}, {status}) -> `{row['hook_path']}`"
        )
    print()
    print("## Non-Authoritative hooks.json Declarations")
    for row in inventory["non_authoritative_hooks_json"]:
        events = ", ".join(row["events"])
        print(f"- {row['plugin']}: `{row['path']}` ({events})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    parser.add_argument(
        "--settings",
        action="append",
        type=Path,
        help="Settings path to inspect. Defaults to user and P: project settings.",
    )
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_PLUGIN_ROOT)
    args = parser.parse_args()

    settings_paths = args.settings or list(DEFAULT_SETTINGS_PATHS)
    inventory = build_inventory(settings_paths, args.plugin_root)
    if args.json:
        print(json.dumps(inventory, indent=2, default=_json_default))
    else:
        _print_markdown(inventory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
