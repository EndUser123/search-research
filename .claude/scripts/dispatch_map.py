#!/usr/bin/env python3
"""Cross-layer hook dispatch map audit tool.

Parses all four dispatch layers and reports anomalies:
  DOUBLE_FIRE  — hook registered in both router_py and hooks_json
  PHANTOM      — registered hook file does not exist on disk
  SPLIT        — plugin uses both router_py and hooks_json for different events

Usage:
  python dispatch_map.py              # human-readable table
  python dispatch_map.py --check      # exit 1 if any anomalies found
  python dispatch_map.py --json       # JSON output
  python dispatch_map.py --plugins cc-aca-epistemic  # filter by plugin name
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SETTINGS = Path(r"C:/Users/brsth/.claude/settings.json")
STOP_PY = Path(r"P:/.claude/hooks/Stop.py")
PLUGINS_ROOT = Path(r"P:/packages/.claude-marketplace/plugins")
CACHE_ROOT = Path(r"C:/Users/brsth/.claude/plugins/cache/local")


@dataclass
class Entry:
    plugin: str
    event: str
    hook: str
    layer: str  # in_process | router_py | hooks_json | settings_subprocess
    path: Optional[Path] = None

    @property
    def exists(self) -> bool:
        if self.layer == "in_process":
            return True
        return self.path is not None and self.path.exists()


@dataclass
class Anomaly:
    kind: str  # DOUBLE_FIRE | PHANTOM | SPLIT
    plugin: str
    event: str
    hook: str
    detail: str


def _find_plugin_version(plugin_name: str) -> Optional[Path]:
    """Return the highest-versioned cache directory for a plugin."""
    cache_dir = CACHE_ROOT / plugin_name
    if not cache_dir.exists():
        return None
    versions = sorted(cache_dir.iterdir(), key=lambda p: p.name, reverse=True)
    return versions[0] if versions else None


# ---------------------------------------------------------------------------
# Layer 1: Stop.py IN_PROCESS_GATES
# ---------------------------------------------------------------------------

def parse_in_process_gates() -> list[Entry]:
    """Extract hook names from Stop.py IN_PROCESS_GATES list."""
    if not STOP_PY.exists():
        return []
    source = STOP_PY.read_text(encoding="utf-8", errors="replace")
    # Find IN_PROCESS_GATES = [...] block
    m = re.search(r"IN_PROCESS_GATES\s*=\s*\[([^\]]+)\]", source, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    names = re.findall(r'["\']([^"\']+)["\']', block)
    return [Entry(plugin="local", event="Stop", hook=n, layer="in_process") for n in names]


# ---------------------------------------------------------------------------
# Layer 2: settings.json router_py registrations
# ---------------------------------------------------------------------------

def parse_router_py_registrations() -> list[Entry]:
    """Find plugins registered via __lib/router.py in settings.json."""
    if not SETTINGS.exists():
        return []
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    hooks_cfg = data.get("hooks", {})
    entries: list[Entry] = []
    for event, matchers in hooks_cfg.items():
        if not isinstance(matchers, list):
            continue
        for matcher_block in matchers:
            for hook in matcher_block.get("hooks", []):
                cmd = hook.get("command", "")
                # Detect router.py dispatch pattern
                m = re.search(r"plugins[/\\]cache[/\\]local[/\\]([^/\\]+)[/\\][^/\\]+[/\\]__lib[/\\]router\.py", cmd)
                if m:
                    plugin_name = m.group(1)
                    entries.append(Entry(
                        plugin=plugin_name,
                        event=event,
                        hook="router.py",
                        layer="router_py",
                        path=Path(_m.group(1)) if (_m := re.search(r"python\s+(\S+router\.py)", cmd)) else None,
                    ))
    return entries


# ---------------------------------------------------------------------------
# Layer 3: Plugin hooks/hooks.json registrations
# ---------------------------------------------------------------------------

def parse_plugin_hooks_json() -> list[Entry]:
    """Parse each installed plugin's hooks/hooks.json."""
    entries: list[Entry] = []
    if not CACHE_ROOT.exists():
        return entries

    for plugin_dir in CACHE_ROOT.iterdir():
        if not plugin_dir.is_dir():
            continue
        plugin_name = plugin_dir.name
        cached = _find_plugin_version(plugin_name)
        if cached is None:
            continue
        hooks_json = cached / "hooks" / "hooks.json"
        if not hooks_json.exists():
            continue
        try:
            data = json.loads(hooks_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        plugin_hooks = data.get("hooks", {})
        if not plugin_hooks:
            continue

        for event, matchers in plugin_hooks.items():
            if not isinstance(matchers, list):
                continue
            for matcher_block in matchers:
                for hook in matcher_block.get("hooks", []):
                    cmd = hook.get("command", "")
                    # Extract hook filename from command
                    m = re.search(r"(\w[\w\-\.]*\.py)(?:\s|$)", cmd)
                    hook_name = m.group(1) if m else cmd[:60]
                    # Resolve path — expand $CLAUDE_PLUGIN_ROOT to the plugin's cache dir
                    path_m = re.search(r'python\s+["\']?(\S+\.py)["\']?', cmd)
                    hook_path: Optional[Path] = None
                    if path_m:
                        raw = path_m.group(1).strip("\"'")
                        expanded = raw.replace("$CLAUDE_PLUGIN_ROOT", str(cached))
                        hook_path = Path(expanded)
                    entries.append(Entry(
                        plugin=plugin_name,
                        event=event,
                        hook=hook_name,
                        layer="hooks_json",
                        path=hook_path,
                    ))
    return entries


# ---------------------------------------------------------------------------
# Layer 4: settings.json subprocess (non-router) hooks
# ---------------------------------------------------------------------------

def parse_settings_subprocess() -> list[Entry]:
    """Find non-router.py subprocess hooks registered directly in settings.json."""
    if not SETTINGS.exists():
        return []
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    hooks_cfg = data.get("hooks", {})
    entries: list[Entry] = []
    for event, matchers in hooks_cfg.items():
        if not isinstance(matchers, list):
            continue
        for matcher_block in matchers:
            for hook in matcher_block.get("hooks", []):
                cmd = hook.get("command", "")
                if "router.py" in cmd:
                    continue  # already captured in layer 2
                m_path = re.search(r"python\s+(\S+\.py)", cmd)
                if not m_path:
                    continue
                hook_path = Path(m_path.group(1))
                entries.append(Entry(
                    plugin="local",
                    event=event,
                    hook=hook_path.name,
                    layer="settings_subprocess",
                    path=hook_path,
                ))
    return entries


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

def detect_anomalies(all_entries: list[Entry]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []

    # PHANTOM: registered but file missing
    for e in all_entries:
        if e.layer == "in_process":
            continue
        if e.path and not e.path.exists():
            anomalies.append(Anomaly(
                kind="PHANTOM",
                plugin=e.plugin,
                event=e.event,
                hook=e.hook,
                detail=f"File not found: {e.path}",
            ))

    # Group by plugin to find DOUBLE_FIRE and SPLIT
    by_plugin: dict[str, list[Entry]] = defaultdict(list)
    for e in all_entries:
        by_plugin[e.plugin].append(e)

    for plugin, entries in by_plugin.items():
        # DOUBLE_FIRE: same event registered in both router_py and hooks_json
        router_events = {e.event for e in entries if e.layer == "router_py"}
        json_hooks = [e for e in entries if e.layer == "hooks_json"]
        for e in json_hooks:
            if e.event in router_events:
                anomalies.append(Anomaly(
                    kind="DOUBLE_FIRE",
                    plugin=plugin,
                    event=e.event,
                    hook=e.hook,
                    detail="Event registered in both router_py (settings.json) and hooks_json",
                ))

        # SPLIT: plugin uses router_py for some events and hooks_json for others
        has_router = bool(router_events)
        has_json_hooks = bool(json_hooks)
        if has_router and has_json_hooks:
            json_only_events = {e.event for e in json_hooks} - router_events
            if json_only_events:
                anomalies.append(Anomaly(
                    kind="SPLIT",
                    plugin=plugin,
                    event=", ".join(sorted(json_only_events)),
                    hook="(multiple)",
                    detail=f"Plugin uses router_py for {sorted(router_events)} but hooks_json for {sorted(json_only_events)}",
                ))

    return anomalies


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def render_table(entries: list[Entry], anomalies: list[Anomaly]) -> None:
    print(f"\n{'LAYER':<18} {'PLUGIN':<30} {'EVENT':<20} {'HOOK':<45} {'OK'}")
    print("-" * 120)
    for e in sorted(entries, key=lambda x: (x.layer, x.plugin, x.event)):
        ok = "✓" if e.exists else "✗ MISSING"
        print(f"{e.layer:<18} {e.plugin:<30} {e.event:<20} {e.hook:<45} {ok}")

    if anomalies:
        print(f"\n{'─'*120}")
        print(f"ANOMALIES ({len(anomalies)} found):")
        for a in anomalies:
            print(f"  [{a.kind}] {a.plugin} / {a.event} / {a.hook}")
            print(f"           {a.detail}")
    else:
        print(f"\n✓ No anomalies detected.")

    print(f"\nTotal entries: {len(entries)}  |  Anomalies: {len(anomalies)}")


def render_json(entries: list[Entry], anomalies: list[Anomaly]) -> None:
    out = {
        "entries": [
            {
                "layer": e.layer,
                "plugin": e.plugin,
                "event": e.event,
                "hook": e.hook,
                "path": str(e.path) if e.path else None,
                "exists": e.exists,
            }
            for e in entries
        ],
        "anomalies": [
            {
                "kind": a.kind,
                "plugin": a.plugin,
                "event": a.event,
                "hook": a.hook,
                "detail": a.detail,
            }
            for a in anomalies
        ],
        "summary": {
            "total_entries": len(entries),
            "anomaly_count": len(anomalies),
        },
    }
    print(json.dumps(out, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    as_json = "--json" in args
    check_mode = "--check" in args
    plugin_filter: Optional[str] = None
    if "--plugins" in args:
        idx = args.index("--plugins")
        if idx + 1 < len(args):
            plugin_filter = args[idx + 1]

    all_entries: list[Entry] = []
    all_entries.extend(parse_in_process_gates())
    all_entries.extend(parse_router_py_registrations())
    all_entries.extend(parse_plugin_hooks_json())
    all_entries.extend(parse_settings_subprocess())

    if plugin_filter:
        all_entries = [e for e in all_entries if plugin_filter in e.plugin]

    anomalies = detect_anomalies(all_entries)

    if as_json:
        render_json(all_entries, anomalies)
    else:
        render_table(all_entries, anomalies)

    if check_mode and anomalies:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
