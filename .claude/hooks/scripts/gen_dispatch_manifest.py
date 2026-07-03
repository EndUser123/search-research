#!/usr/bin/env python3
"""Generate dispatch manifest for the hooks system.

Reads settings.json (project + user), plugin router.py files, and local hook
dispatchers (SessionStart.py SETUP_SEQUENCE, PreToolUse.py UNIVERSAL/TOOL_HOOKS)
to produce P:/.claude/hooks/dispatch_manifest.json.

CLI:
    python gen_dispatch_manifest.py
    python gen_dispatch_manifest.py --is-live <filename>
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_SETTINGS = Path("P:/.claude/settings.json")
USER_SETTINGS = Path("C:/Users/brsth/.claude/settings.json")
PLUGINS_DIR = Path("P:/packages/.claude-marketplace/plugins")
HOOKS_DIR = Path("P:/.claude/hooks")
SESSION_START_PATH = HOOKS_DIR / "SessionStart.py"
PRETOOLUSE_PATH = HOOKS_DIR / "PreToolUse.py"
MANIFEST_PATH = HOOKS_DIR / "dispatch_manifest.json"

INPUT_PATHS: list[Path] = [
    PROJECT_SETTINGS,
    USER_SETTINGS,
    SESSION_START_PATH,
    PRETOOLUSE_PATH,
]


def _walk_list_assignments(tree: ast.AST) -> dict[str, list[str]]:
    """Collect module-level variable assignments whose value is a str list."""
    lists: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and isinstance(node.value, ast.List):
                    items = [
                        elt.value
                        for elt in node.value.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    ]
                    lists[tgt.id] = items
    return lists


def _resolve_dispatch_value(
    value: ast.expr, known_lists: dict[str, list[str]]
) -> list[str]:
    """Resolve a DISPATCH dict value to a list of hook filename strings."""
    if isinstance(value, ast.List):
        return [
            elt.value
            for elt in value.elts
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        ]
    if isinstance(value, ast.Name):
        return known_lists.get(value.id, [])
    if isinstance(value, ast.Tuple) and len(value.elts) >= 2:
        second = value.elts[1]
        if isinstance(second, ast.List):
            return [
                elt.value
                for elt in second.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
    return []


def extract_hooks_from_settings(settings_path: Path) -> dict[str, list[str]]:
    """Return {event: [command_str, ...]} from a settings.json hooks section."""
    result: dict[str, list[str]] = {}
    try:
        data = json.loads(settings_path.read_bytes())
    except (OSError, json.JSONDecodeError):
        return result
    for event, matcher_blocks in data.get("hooks", {}).items():
        targets: list[str] = []
        for block in matcher_blocks:
            for hook in block.get("hooks", []):
                cmd = hook.get("command", "")
                if cmd:
                    targets.append(cmd)
        if targets:
            result[event] = targets
    return result


def extract_from_plugin_router(
    router_path: Path,
) -> tuple[dict[str, list[str]], str | None]:
    """Return ({event: [hook_names]}, parse_error_or_None)."""
    try:
        tree = ast.parse(router_path.read_bytes(), filename=str(router_path))
    except SyntaxError as e:
        return {}, f"SyntaxError: {e}"

    known_lists = _walk_list_assignments(tree)
    dispatch: dict[str, list[str]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if not isinstance(tgt, ast.Name):
                continue
            if tgt.id not in ("DISPATCH", "_DISPATCH"):
                continue
            if not isinstance(node.value, ast.Dict):
                continue
            for key, value in zip(node.value.keys, node.value.values):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    resolved = _resolve_dispatch_value(value, known_lists)
                    if resolved:
                        dispatch[key.value] = resolved
    return dispatch, None


def extract_session_start_sequence(path: Path) -> list[str]:
    """Extract SETUP_SEQUENCE hook filenames from SessionStart.py."""
    try:
        tree = ast.parse(path.read_bytes(), filename=str(path))
    except (OSError, SyntaxError):
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "SETUP_SEQUENCE":
                    if isinstance(node.value, ast.List):
                        return [
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        ]
    return []


def extract_pretooluse_dispatch(
    path: Path,
) -> tuple[list[str], dict[str, list[str]]]:
    """Extract (UNIVERSAL list, TOOL_HOOKS dict) from PreToolUse.py."""
    try:
        tree = ast.parse(path.read_bytes(), filename=str(path))
    except (OSError, SyntaxError):
        return [], {}

    universal: list[str] = []
    tool_hooks: dict[str, list[str]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if not isinstance(tgt, ast.Name):
                continue
            if tgt.id == "UNIVERSAL" and isinstance(node.value, ast.List):
                universal = [
                    elt.value
                    for elt in node.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
            elif tgt.id == "TOOL_HOOKS" and isinstance(node.value, ast.Dict):
                for key, value in zip(node.value.keys, node.value.values):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        if isinstance(value, ast.List):
                            tool_hooks[key.value] = [
                                elt.value
                                for elt in value.elts
                                if isinstance(elt, ast.Constant)
                                and isinstance(elt.value, str)
                            ]
    return universal, tool_hooks


def plugin_name(path: Path) -> str:
    return path.parent.parent.name


def compute_inputs_hash() -> str:
    """SHA256 over sorted bytes of all input files."""
    h = hashlib.sha256()
    for p in sorted(INPUT_PATHS):
        if p.exists():
            h.update(p.read_bytes())
    for router in sorted(PLUGINS_DIR.glob("*/__lib/router.py")):
        h.update(router.read_bytes())
    return h.hexdigest()


def build_manifest() -> dict:
    """Build the full dispatch manifest."""
    parse_errors: list[str] = []
    events: dict[str, list[dict]] = {}

    # (a) Project settings
    for event, cmds in extract_hooks_from_settings(PROJECT_SETTINGS).items():
        events.setdefault(event, []).extend(
            {"target": c, "scope": "project"} for c in cmds
        )

    # (a) User settings
    for event, cmds in extract_hooks_from_settings(USER_SETTINGS).items():
        events.setdefault(event, []).extend(
            {"target": c, "scope": "user"} for c in cmds
        )

    # (b) Plugin routers
    for router_path in sorted(PLUGINS_DIR.glob("*/__lib/router.py")):
        dispatch, err = extract_from_plugin_router(router_path)
        if err:
            parse_errors.append(f"{router_path}: {err}")
        for event, hooks in dispatch.items():
            for hook in hooks:
                events.setdefault(event, []).append(
                    {"target": hook, "scope": f"router:{plugin_name(router_path)}"}
                )

    # (c) SessionStart.py SETUP_SEQUENCE (in-process sub-hooks)
    for hook in extract_session_start_sequence(SESSION_START_PATH):
        events.setdefault("SessionStart", []).append(
            {"target": hook, "scope": "inprocess"}
        )

    # (d) PreToolUse.py UNIVERSAL + TOOL_HOOKS (in-process sub-hooks)
    universal, tool_hooks = extract_pretooluse_dispatch(PRETOOLUSE_PATH)
    for hook in universal:
        events.setdefault("PreToolUse", []).append(
            {"target": hook, "scope": "inprocess"}
        )
    for hooks in tool_hooks.values():
        for hook in hooks:
            events.setdefault("PreToolUse", []).append(
                {"target": hook, "scope": "inprocess"}
            )

    # Sort entries within each event
    for event in events:
        events[event].sort(key=lambda e: (e["scope"], e["target"]))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs_hash": compute_inputs_hash(),
        "parse_errors": parse_errors,
        "events": dict(sorted(events.items())),
    }


def is_live(manifest: dict, filename: str) -> bool:
    """Check if a filename appears anywhere in the dispatch chain."""
    for event, entries in manifest["events"].items():
        for entry in entries:
            target = entry.get("target", "")
            if isinstance(target, str) and filename in target:
                return True
    return False


def do_is_live(filename: str) -> None:
    """Recompute hash and check liveness."""
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_bytes())
        if manifest.get("inputs_hash") != compute_inputs_hash():
            print("STALE MANIFEST — regenerate")
            sys.exit(1)
        print("LIVE" if is_live(manifest, filename) else "NOT-LIVE")
        sys.exit(0)
    else:
        print("STALE MANIFEST — regenerate")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--is-live", type=str, help="Check live status of a hook filename")
    args = parser.parse_args()

    if args.is_live:
        do_is_live(args.is_live)
        return

    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Manifest written to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
