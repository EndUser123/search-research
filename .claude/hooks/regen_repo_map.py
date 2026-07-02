#!/usr/bin/env python3
"""Generate the structural repo map for this workspace.

Emits three flat, navigational, token-bounded artifacts (no call-graph, no
whole-repo packing):
  - state/shared/repo_map.generated.md      (human/agent navigation)
  - state/shared/repo_map.generated.json    (machine consumption)
  - state/shared/canonical_paths.generated.md (where things live + where state goes)

Outputs land in .claude/state/shared/ because the directory_policy hook blocks
a separate .claude/context/ subdir. Functionally equivalent: external to the
code tree, SessionStart-readable, policy-allowed.

Shape is customized for THIS repo's architecture: plugins, routers, hooks,
skills, canonical source roots vs version-keyed cache, duplicate namespaces,
and validation commands. Reuses active_hook_inventory.build_inventory for the
hook-routing surface rather than re-deriving it.

Run:  python .claude/hooks/regen_repo_map.py
Idempotent; safe under SessionStart mtime-guard.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOOKS_DIR = Path("P:/.claude/hooks")
OUTPUT_DIR = Path("P:/.claude/state/shared")
PLUGIN_ROOT = Path("P:/packages/.claude-marketplace/plugins")
SETTINGS_PATHS = [Path.home() / ".claude" / "settings.json", Path("P:/.claude/settings.json")]

REPO_MD = OUTPUT_DIR / "repo_map.generated.md"
REPO_JSON = OUTPUT_DIR / "repo_map.generated.json"
CANON_MD = OUTPUT_DIR / "canonical_paths.generated.md"

VALIDATION_COMMANDS = [
    "python <hook.py> < sample.json   # direct-invocation smoke (catches import bugs syntax checks miss)",
    "python -m pytest tests/test_<name>.py -q   # targeted tests",
    "python __lib/<module>.py   # self-check for modules with a __main__ block",
    "python -c \"import <module>; print('ok')\"   # import sanity",
]


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _mtime(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return None


def enumerate_plugins() -> list[dict[str, Any]]:
    """One entry per plugin under PLUGIN_ROOT with version, skills, router."""
    plugins: list[dict[str, Any]] = []
    if not PLUGIN_ROOT.exists():
        return plugins
    for entry in sorted(PLUGIN_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        manifest = entry / ".claude-plugin" / "plugin.json"
        meta = _load_json(manifest) or {}
        skills: list[str] = []
        skills_dir = entry / "skills"
        if skills_dir.is_dir():
            skills = sorted(
                s.name for s in skills_dir.iterdir() if s.is_dir() and (s / "SKILL.md").exists()
            )
        router = entry / "hooks" / "__lib" / "router.py"
        plugins.append(
            {
                "name": meta.get("name", entry.name),
                "dir": str(entry).replace("\\", "/"),
                "version": meta.get("version", "?"),
                "description": (meta.get("description") or "").strip(),
                "skills": skills,
                "router": str(router).replace("\\", "/") if router.exists() else None,
                "mtime": _mtime(manifest) or _mtime(entry),
            }
        )
    return plugins


def canonical_paths() -> list[dict[str, str]]:
    """Where things live + where state/log MUST go (external to code tree)."""
    return [
        {"path": "P:/.claude/hooks/", "role": "authority hook source (PreToolUse, PostToolUse, Stop, SessionStart)"},
        {"path": "P:/.claude/hooks/__lib/", "role": "shared hook libraries (router, telemetry, logic)"},
        {"path": "P:/.claude/settings.json", "role": "hook dispatch wiring (user + project)"},
        {"path": "P:/packages/.claude-marketplace/plugins/", "role": "plugin SOURCE root (canonical)"},
        {"path": "P:/.claude/state/shared/", "role": "external state + telemetry + generated context (NOT in code tree)"},
        {"path": "P:/.claude/.artifacts/", "role": "per-terminal run artifacts"},
        {"path": "P:/.data/wiki/", "role": "wiki vault"},
        {"path": "C:/Users/brsth/.claude/projects/P--/memory/", "role": "auto-memory (persists across sessions)"},
    ]


def duplicate_namespaces(plugins: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Flag plugins whose name also appears in version-keyed cache (~/.claude)."""
    cache_root = Path.home() / ".claude" / "plugins"
    dups: list[dict[str, str]] = []
    if not cache_root.exists():
        return dups  # ponytail: cache path varies by install; record the check, not a guess
    cache_names = {p.name for p in cache_root.iterdir() if p.is_dir()}
    for plug in plugins:
        if plug["name"] in cache_names:
            dups.append(
                {
                    "name": plug["name"],
                    "source": plug["dir"],
                    "cache": str(cache_root / plug["name"]).replace("\\", "/"),
                    "note": "source wins per plugin_bidir_sync_source_wins; bump rebuilds cache",
                }
            )
    return dups


def build() -> dict[str, Any]:
    sys.path.insert(0, str(HOOKS_DIR))
    try:
        from active_hook_inventory import build_inventory, DEFAULT_SETTINGS_PATHS

        settings = list({Path(p) for p in SETTINGS_PATHS + list(DEFAULT_SETTINGS_PATHS) if Path(p).exists()})
        inventory = build_inventory(settings, PLUGIN_ROOT)
    except Exception as exc:  # pragma: no cover - inventory is best-effort
        inventory = {"error": f"active_hook_inventory unavailable: {exc}"}

    plugins = enumerate_plugins()
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "generated_at": generated_at,
        "generator": ".claude/hooks/regen_repo_map.py",
        "plugins": plugins,
        "hook_inventory": {
            "settings_commands_count": len(inventory.get("settings_commands", [])) if isinstance(inventory, dict) else 0,
            "router_hooks_count": len(inventory.get("router_hooks", [])) if isinstance(inventory, dict) else 0,
            "non_authoritative_hooks_json": (inventory.get("non_authoritative_hooks_json", []) if isinstance(inventory, dict) else []),
            "raw": inventory,
        },
        "canonical_paths": canonical_paths(),
        "duplicate_namespaces": duplicate_namespaces(plugins),
        "validation_commands": VALIDATION_COMMANDS,
    }


def render_md(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Repo Map (generated)")
    lines.append("")
    lines.append(f"_Generated by `{snapshot['generator']}` at {snapshot['generated_at']}._")
    lines.append("_Flat structural inventory. Do not edit; regenerate via `python .claude/hooks/regen_repo_map.py`._")
    lines.append("")
    lines.append("## Plugins")
    for p in snapshot["plugins"]:
        router = "router✓" if p["router"] else "no-router"
        lines.append(f"- **{p['name']}** v{p['version']} — {router} — `{p['dir']}`")
        if p["description"]:
            lines.append(f"    - {p['description'][:160]}")
        skills = ", ".join(p["skills"]) if p["skills"] else "(no skills)"
        lines.append(f"    - skills: {skills}")
    lines.append("")
    hi = snapshot["hook_inventory"]
    lines.append("## Hook Routing Surface")
    lines.append(f"- settings dispatch commands: {hi['settings_commands_count']}")
    lines.append(f"- router-expanded hooks: {hi['router_hooks_count']}")
    non_auth = hi.get("non_authoritative_hooks_json", [])
    if non_auth:
        lines.append(f"- non-authoritative hooks.json (not reached via settings/router): {len(non_auth)}")
        for decl in non_auth[:20]:
            lines.append(f"    - {decl.get('plugin')}: `{decl.get('path')}` ({', '.join(decl.get('events', []))})")
    lines.append("")
    lines.append("## Duplicate Namespaces (source vs cache)")
    dups = snapshot["duplicate_namespaces"]
    if dups:
        for d in dups:
            lines.append(f"- **{d['name']}** — source `{d['source']}` / cache `{d['cache']}` — {d['note']}")
    else:
        lines.append("_None detected._")
    lines.append("")
    lines.append("## Validation Commands")
    for cmd in snapshot["validation_commands"]:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def render_canon_md(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Canonical Paths (generated)")
    lines.append("")
    lines.append(f"_Generated at {snapshot['generated_at']}._ State/logs MUST go to the external state dir, not the code tree.")
    lines.append("")
    lines.append("| Path | Role |")
    lines.append("|------|------|")
    for row in snapshot["canonical_paths"]:
        lines.append(f"| `{row['path']}` | {row['role']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = build()
    REPO_MD.write_text(render_md(snapshot), encoding="utf-8")
    REPO_JSON.write_text(json.dumps(snapshot, indent=2, default=lambda o: str(o).replace("\\", "/") if isinstance(o, Path) else str(o)), encoding="utf-8")
    CANON_MD.write_text(render_canon_md(snapshot), encoding="utf-8")
    print(f"wrote {REPO_MD}")
    print(f"wrote {REPO_JSON}")
    print(f"wrote {CANON_MD}")
    print(f"plugins: {len(snapshot['plugins'])}, router hooks: {snapshot['hook_inventory']['router_hooks_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
