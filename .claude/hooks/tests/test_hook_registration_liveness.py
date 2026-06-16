#!/usr/bin/env python3
"""Liveness sweep: every REGISTERED hook module must actually load.

Unit tests prove a hook's logic; they do NOT prove its production import path is
alive. The veridical gate was dead ~2 weeks because its call site did
`from _veridical_gate import ...` — a shim that never existed, swallowed by a
fail-open try/except, so the gate silently never ran while its unit tests still
passed. Fixed in 68f8228 (now `from anti_sycophancy.veridical_gate import
check_veridical_integrity`).

Hooks are enumerated from their ACTUAL registration sources (never a hand list,
which would itself rot):
  1. P:/.claude/settings.json `hooks` blocks
  2. each plugin's hooks/hooks.json under the marketplace
  3. PreToolUse.py in-process lists (UNIVERSAL/TOOL_HOOKS/IN_PROCESS_HOOKS/
     COMPAT_POST_ROUTER_HOOKS) and Stop.py (SIDE_EFFECTS + the sibling gate
     modules its IN_PROCESS_GATES runners import lazily, e.g.
     Stop_semantic_critic.py — where the veridical import lives)

Each file is loaded in an isolated subprocess (anti-mock: real files, real
interpreter, real find_spec).
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path("P:/.claude/hooks")
SETTINGS_JSON = Path("P:/.claude/settings.json")
PRETOOLUSE = HOOKS_DIR / "PreToolUse.py"
STOP = HOOKS_DIR / "Stop.py"
PLUGINS_DIR = Path("P:/packages/.claude-marketplace/plugins")
PROBE = HOOKS_DIR / "tests" / "_hook_liveness_probe.py"

_HOOK_IMPORTER_RE = re.compile(r"execute_hook\(\s*['\"](\w+)['\"]")
_PY_TOKEN_RE = re.compile(r"(\S+\.py)")


def _resolve_command(command: str, plugin_root: Path | None = None) -> list[Path]:
    """Resolve one hooks-block `command` to the hook file(s) it runs.

    Shapes: HookImporter wrapper -> <hooks>/<EVENT>.py; hook_runner.py X.py ->
    X.py; router.py PreToolUse -> router.py; python X.py -> X.py.
    """
    m = _HOOK_IMPORTER_RE.search(command)
    if m:
        return [HOOKS_DIR / f"{m.group(1)}.py"]

    cmd = command
    if plugin_root is not None:
        root = str(plugin_root)
        cmd = cmd.replace("${CLAUDE_PLUGIN_ROOT}", root).replace("$CLAUDE_PLUGIN_ROOT", root)
    # Drop quotes AND backslash-escaped quotes (\" / \') — some hooks.json
    # commands store `python \"$CLAUDE_PLUGIN_ROOT/...py\"`, which would
    # otherwise leave a leading backslash on the parsed path token.
    cmd = re.sub(r'\\?["\']', " ", cmd)

    pys = _PY_TOKEN_RE.findall(cmd)
    if not pys:
        return []
    if any(p.endswith("hook_runner.py") for p in pys):
        wrapped = [p for p in pys if not p.endswith("hook_runner.py")]
        return [Path(wrapped[0])] if wrapped else []
    return [Path(pys[0])]


def _iter_hookblocks(blocks: object):
    if not isinstance(blocks, dict):
        return
    for groups in blocks.values():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            for hook in group.get("hooks", []) or []:
                if isinstance(hook, dict) and hook.get("type") == "command":
                    cmd = hook.get("command")
                    if isinstance(cmd, str) and cmd.strip():
                        yield cmd


def _from_settings(errors: list[str]) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    try:
        data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"settings.json parse failed: {exc}")
        return out
    for cmd in _iter_hookblocks(data.get("hooks", {})):
        for path in _resolve_command(cmd):
            out.append(("settings.json", path))
    return out


def _from_plugin_hooks(errors: list[str]) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for hooks_json in sorted(PLUGINS_DIR.glob("*/hooks/hooks.json")):
        plugin_root = hooks_json.parent.parent
        try:
            data = json.loads(hooks_json.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{hooks_json}: parse failed: {exc}")
            continue
        label = f"plugin:{plugin_root.name}"
        for cmd in _iter_hookblocks(data.get("hooks", {})):
            for path in _resolve_command(cmd, plugin_root=plugin_root):
                out.append((label, path))
    return out


def _literal_values(file_path: Path, var_names: set[str], errors: list[str]) -> list[str]:
    """Flattened string entries from module-level list/dict assignments, via AST
    (no import of the heavy hook module)."""
    values: list[str] = []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{file_path}: AST parse failed: {exc}")
        return values
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = {t.id for t in node.targets if isinstance(t, ast.Name)}
        if not (targets & var_names):
            continue
        try:
            literal = ast.literal_eval(node.value)
        except Exception:
            continue
        stack = [literal]
        while stack:
            cur = stack.pop()
            if isinstance(cur, str):
                values.append(cur)
            elif isinstance(cur, (list, tuple, set)):
                stack.extend(cur)
            elif isinstance(cur, dict):
                stack.extend(cur.values())
    return values


def _from_pretooluse_lists(errors: list[str]) -> list[tuple[str, Path]]:
    names = {"UNIVERSAL", "COMPAT_POST_ROUTER_HOOKS", "IN_PROCESS_HOOKS", "TOOL_HOOKS"}
    return [("PreToolUse.py:in_process", HOOKS_DIR / r) for r in _literal_values(PRETOOLUSE, names, errors)]


def _from_stop_sources(errors: list[str]) -> list[tuple[str, Path]]:
    """Stop.py SIDE_EFFECTS literals + sibling gate-implementation modules that
    IN_PROCESS_GATES runners import lazily (e.g. `from Stop_semantic_critic
    import run`). Resolving the runners' lazy imports is how
    Stop_semantic_critic.py — where the veridical import lives — enters the
    probe set without a hand-maintained gate->module map."""
    out: list[tuple[str, Path]] = []
    for rel in _literal_values(STOP, {"SIDE_EFFECTS"}, errors):
        out.append(("Stop.py:SIDE_EFFECTS", HOOKS_DIR / rel))

    try:
        tree = ast.parse(STOP.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Stop.py: AST parse failed: {exc}")
        return out

    # Only scan runner functions ACTUALLY registered in IN_PROCESS_GATES — not
    # every function in Stop.py. This excludes disabled/removed gate runners
    # (e.g. _run_correction_acknowledgment, kept as dead code but dropped from
    # the active list) whose imports are not a live registration.
    registered_runners: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "IN_PROCESS_GATES" for t in node.targets
        ) and isinstance(node.value, ast.List):
            for elt in node.value.elts:
                if (
                    isinstance(elt, ast.Tuple)
                    and len(elt.elts) >= 2
                    and isinstance(elt.elts[1], ast.Name)
                ):
                    registered_runners.add(elt.elts[1].id)

    sibling_mods: set[str] = set()
    for node in tree.body:
        if not (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in registered_runners):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.ImportFrom) and sub.module and sub.level == 0:
                top = sub.module.split(".")[0]
                if (HOOKS_DIR / f"{top}.py").exists():
                    sibling_mods.add(top)
            elif isinstance(sub, ast.Import):
                for alias in sub.names:
                    top = alias.name.split(".")[0]
                    if (HOOKS_DIR / f"{top}.py").exists():
                        sibling_mods.add(top)

    for mod in sorted(sibling_mods):
        out.append(("Stop.py:gate_impl", HOOKS_DIR / f"{mod}.py"))
    return out


def enumerate_registered_hooks() -> tuple[list[tuple[str, Path]], list[str]]:
    errors: list[str] = []
    entries: list[tuple[str, Path]] = []
    entries += _from_settings(errors)
    entries += _from_plugin_hooks(errors)
    entries += _from_pretooluse_lists(errors)
    entries += _from_stop_sources(errors)

    seen: dict[str, tuple[str, Path]] = {}
    for label, path in entries:
        try:
            key = str(path.resolve())
        except OSError:
            key = str(path)
        seen.setdefault(key, (label, path))
    return list(seen.values()), errors


def _run_probe(path: Path, context: Path | None = None) -> dict:
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    argv = [sys.executable, str(PROBE), str(path)]
    if context is not None:
        argv.append(str(context))
    try:
        proc = subprocess.run(
            argv,
            capture_output=True, text=True, timeout=60, creationflags=flags,
        )
    except subprocess.TimeoutExpired:
        return {"path": str(path), "ok": False, "error": "PROBE_TIMEOUT (60s)"}
    lines = (proc.stdout or "").strip().splitlines()
    if not lines:
        return {"path": str(path), "ok": False,
                "error": f"PROBE_NO_OUTPUT rc={proc.returncode}: {(proc.stderr or '')[-400:]}"}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {"path": str(path), "ok": False,
                "error": f"PROBE_BAD_JSON rc={proc.returncode}: {lines[-1][:400]}"}


@pytest.fixture(scope="session")
def probe_results() -> dict:
    assert PROBE.exists(), f"probe helper missing: {PROBE}"
    entries, errors = enumerate_registered_hooks()
    results = {}
    for label, path in entries:
        # gate_impl modules run IN-PROCESS inside Stop.py at runtime, so they
        # rely on the sys.path Stop.py sets up. Give the probe Stop.py as
        # context so the environment matches runtime (not a bare interpreter).
        context = STOP if label == "Stop.py:gate_impl" else None
        results[str(path)] = {
            "label": label, "path": path, "verdict": _run_probe(path, context=context)
        }
    return {"results": results, "enum_errors": errors, "count": len(entries)}


def test_enumeration_discovers_registered_hooks(probe_results):
    """Guard the enumerator: if a source silently yields nothing the sweep
    becomes a no-op that always passes. Assert a floor + known-critical files."""
    count = probe_results["count"]
    assert count >= 30, f"enumeration found only {count} hooks - a source likely broke"
    resolved = {Path(p).name for p in probe_results["results"]}
    for required in ("Stop.py", "PreToolUse.py", "UserPromptSubmit.py", "Stop_semantic_critic.py"):
        assert required in resolved, f"{required} not enumerated - its source regressed"


def test_all_registered_hook_modules_import(probe_results):
    """Every registered hook file must load without an import error. Failure =
    a hook registered with a dead production import path."""
    failures = []
    for info in probe_results["results"].values():
        v = info["verdict"]
        if not v.get("ok"):
            tb = v.get("traceback", "")
            last = ("\n      ..." + tb.splitlines()[-1]) if tb else ""
            failures.append(f"  [{info['label']}] {v.get('path')}\n      {v.get('error')}{last}")
    assert not failures, (
        f"{len(failures)} registered hook module(s) failed to import "
        f"(dead production import path):\n" + "\n".join(failures)
    )


def test_registered_hook_deferred_imports_resolve(probe_results):
    """First-party imports nested in hook function bodies must resolve. This is
    the veridical-gate class: a lazy `from _veridical_gate import ...` a plain
    load never executes, swallowed by a fail-open try/except."""
    failures = []
    for info in probe_results["results"].values():
        for u in info["verdict"].get("unresolved", []):
            failures.append(
                f"  [{info['label']}] {Path(info['verdict']['path']).name}:{u['line']} "
                f"-> deferred import '{u['module']}' does not resolve"
            )
    assert not failures, (
        f"{len(failures)} unresolved first-party deferred import(s) "
        f"(veridical-gate silent-death class):\n" + "\n".join(failures)
    )


def test_no_enumeration_errors_in_canonical_sources(probe_results):
    """settings.json / PreToolUse.py / Stop.py must parse."""
    fatal = [e for e in probe_results["enum_errors"]
             if any(k in e for k in ("settings.json", "PreToolUse.py", "Stop.py"))]
    assert not fatal, "canonical registration source failed to parse:\n" + "\n".join(fatal)


def test_delegation_live_routing_is_explicit_in_settings():
    """Delegation-related hooks should remain visible in the live settings graph.

    This guards the cleanup we just did: local compatibility wrappers are fine,
    but the live routing must keep showing the actual command chain so future
    audits do not guess at ownership.
    """
    data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))

    def commands_for(event: str) -> list[str]:
        blocks = data.get("hooks", {}).get(event, [])
        cmds: list[str] = []
        for entry in blocks:
            for hook in entry.get("hooks", []):
                cmd = hook.get("command")
                if isinstance(cmd, str):
                    cmds.append(cmd)
        return cmds

    ups_cmds = commands_for("UserPromptSubmit")
    pretool_cmds = commands_for("PreToolUse")

    assert any(
        "hook_importer" in cmd and "execute_hook('UserPromptSubmit')" in cmd
        for cmd in ups_cmds
    ), "UserPromptSubmit must keep the local hook_importer compatibility path"
    assert any(
        "skill_guard/__lib/router.py UserPromptSubmit" in cmd
        for cmd in ups_cmds
    ), "UserPromptSubmit must keep the skill-guard router registration"
    assert any(
        "P:/.claude/hooks/PreToolUse.py" in cmd for cmd in pretool_cmds
    ), "PreToolUse must keep the local router compatibility path"
    assert any(
        "skill_guard/__lib/router.py PreToolUse" in cmd for cmd in pretool_cmds
    ), "PreToolUse must keep the skill-guard router registration"

    wrapper = (HOOKS_DIR / "UserPromptSubmit_modules" / "delegation_prospector.py").read_text(
        encoding="utf-8"
    )
    assert "cc-aca-authority" in wrapper and "delegation_prospector.py" in wrapper


def test_cc_model_router_has_no_stop_autoswitch_registration():
    """The live settings should keep cc-model-router on the UPS apply path only."""
    data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
    stop_cmd = "P:/packages/.claude-marketplace/plugins/cc-model-router/hooks/stop/stop_model_router_autoswitch.py"
    cmds = [
        hook.get("command")
        for block in data.get("hooks", {}).get("Stop", [])
        for hook in block.get("hooks", [])
        if isinstance(hook.get("command"), str)
    ]
    assert stop_cmd not in cmds, (
        "Stop fallback registration should be removed; apply hook already owns "
        "the autoswitch path"
    )
