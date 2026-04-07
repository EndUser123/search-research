#!/usr/bin/env python3
"""
List all available Claude Code agents from 4 sources.

Sources:
  1. P:/.claude/agents/     (user agents, bare name)
  2. ~/.claude/agents/      (user agents, bare name)
  3. P:/.claude/plugins/cache/*/agents/*.md  (plugin agents, namespace:name)
  4. ~/.claude/plugins/cache/*/agents/*.md   (plugin agents, namespace:name)

Output: JSON with name, subagent_type, description, source, source_type
"""

#!/usr/bin/env python3
"""
List all available Claude Code agents from 4 sources.

Sources:
  1. P:/.claude/agents/     (user agents, bare name)
  2. ~/.claude/agents/      (user agents, bare name)
  3. P:/.claude/plugins/cache/*/agents/*.md  (plugin agents, namespace:name)
  4. ~/.claude/plugins/cache/*/agents/*.md   (plugin agents, namespace:name)

Output: JSON to stdout (default)
Flags:
  --json       Force JSON output
  --names      Print just agent names, one per line
  --filter STR Filter agents by name or description (case-insensitive)
  --source SRC Filter by source type: user, plugin, builtin, all
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path("P:/")
HOME_ROOT = Path("C:/Users/brsth/.claude")

# Built-in agents loaded from config file at runtime (not hardcoded)
def _load_builtins() -> list[dict]:
    """Load built-in agents from config file. Falls back to embedded list if missing."""
    config_path = HOME_ROOT / "skills" / "skill-ship" / "config" / "builtins.json"
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("agents", [])
    except Exception:
        pass
    return []  # Empty fallback — dynamically discovered agents still work

BUILTIN_AGENTS = _load_builtins()

# Plugins whose agents should be excluded (marketplace/internal)
EXCLUDED_PLUGINS = {"skill-creator", "huggingface"}


def extract_frontmatter(md_text: str) -> dict:
    """Extract name and description from YAML frontmatter."""
    match = re.match(r"^---\n(.*?)\n---", md_text, re.DOTALL)
    if not match:
        return {}
    frontmatter = match.group(1)
    result = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def scan_user_agents(agents_dir: Path) -> list[dict]:
    """Scan a user agents directory (bare names, no namespace)."""
    agents = []
    if not agents_dir.is_dir():
        return agents
    for md_file in sorted(agents_dir.glob("*.md")):
        if md_file.stem in ("readme", "_README"):  # Skip README
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
            fm = extract_frontmatter(text)
            agents.append({
                "name": md_file.stem,
                "subagent_type": md_file.stem,
                "description": fm.get("description", ""),
                "source": str(md_file),
                "source_type": "user",
            })
        except Exception:
            pass
    return agents


def scan_plugin_agents(plugins_dir: Path) -> list[dict]:
    """Scan plugin cache for agents (namespace:name format)."""
    agents = []
    cache_dir = plugins_dir / "cache"
    if not cache_dir.is_dir():
        return agents
    for plugin_dir in sorted(cache_dir.iterdir()):
        if plugin_dir.name in EXCLUDED_PLUGINS or not plugin_dir.is_dir():
            continue
        # Find all agents/ directories under this plugin
        for agents_dir in plugin_dir.rglob("agents"):
            if agents_dir.is_dir():
                plugin_name = plugin_dir.name
                for md_file in sorted(agents_dir.glob("*.md")):
                    agent_name = md_file.stem
                    try:
                        text = md_file.read_text(encoding="utf-8")
                        fm = extract_frontmatter(text)
                        agents.append({
                            "name": agent_name,
                            "subagent_type": f"{plugin_name}:{agent_name}",
                            "description": fm.get("description", ""),
                            "source": str(md_file),
                            "source_type": "plugin",
                        })
                    except Exception:
                        pass
    return agents


def main(args=None):
    parser = argparse.ArgumentParser(description="List all available Claude Code agents.")
    parser.add_argument("--json", action="store_true", help="Output full JSON (default when no flags)")
    parser.add_argument("--names", action="store_true", help="Print just subagent_type names, one per line")
    parser.add_argument("--filter", metavar="STR", help="Filter agents by name or description (case-insensitive)")
    parser.add_argument("--source", choices=["user", "plugin", "builtin", "all"], default="all",
                        help="Filter by source type (default: all)")
    parsed = parser.parse_args(args)

    all_agents = []

    # Source 1: P:/.claude/agents/
    all_agents.extend(scan_user_agents(REPO_ROOT / ".claude" / "agents"))

    # Source 2: ~/.claude/agents/
    all_agents.extend(scan_user_agents(HOME_ROOT / "agents"))

    # Source 3: P:/.claude/plugins/cache/*/agents/
    all_agents.extend(scan_plugin_agents(REPO_ROOT / ".claude" / "plugins"))

    # Source 4: ~/.claude/plugins/cache/*/agents/
    all_agents.extend(scan_plugin_agents(HOME_ROOT / "plugins"))

    # Add built-in agents
    for a in BUILTIN_AGENTS:
        all_agents.append({
            "name": a["name"],
            "subagent_type": a["name"],
            "description": a["description"],
            "source": "builtin",
            "source_type": "builtin",
        })

    # Apply filters
    if parsed.source != "all":
        all_agents = [a for a in all_agents if a["source_type"] == parsed.source]
    if parsed.filter:
        f = parsed.filter.lower()
        all_agents = [
            a for a in all_agents
            if f in a["name"].lower() or f in a["description"].lower()
        ]

    if parsed.names:
        for a in all_agents:
            print(a["subagent_type"])
    else:
        output = {
            "total": len(all_agents),
            "by_source": {
                "user_p_drive": sum(1 for a in all_agents if a["source_type"] == "user" and a["source"].startswith("P:")),
                "user_home": sum(1 for a in all_agents if a["source_type"] == "user" and a["source"].startswith("C:")),
                "plugin_p_drive": sum(1 for a in all_agents if a["source_type"] == "plugin" and a["source"].startswith("P:")),
                "plugin_home": sum(1 for a in all_agents if a["source_type"] == "plugin" and a["source"].startswith("C:")),
                "builtin": sum(1 for a in all_agents if a["source_type"] == "builtin"),
            },
            "agents": all_agents,
        }
        json.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
