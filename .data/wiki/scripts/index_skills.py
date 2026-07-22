"""
Index all skills across the workspace into the wiki.

Produces two outputs:
1. Lightweight stubs at P:/.data/wiki/sources/skills/<scope>-<name>.md
   (frontmatter only — name, description, path, scope). These let qmd
   semantically search skill descriptions without duplicating full SKILL.md
   content (which would drift).

2. A catalog concept at P:/.data/wiki/concepts/skill-catalog.md
   (human-readable index grouped by scope, with one-line summaries and paths).

Regenerate after adding/removing skills:
    python P:/.data/wiki/scripts/index_skills.py

Design choice: stubs contain only frontmatter (name, description, path) —
NOT the full SKILL.md body. This prevents drift. The source of truth stays
in the actual SKILL.md file; the stub is a searchable pointer.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import NamedTuple

VAULT = Path("P:/.data/wiki")
STUBS_DIR = VAULT / "sources" / "skills"
CATALOG_PATH = VAULT / "concepts" / "skill-catalog.md"

# (scope_label, root_path, plugin_relative_path_or_None)
# If plugin_relative is set, skills live at <root>/<plugin>/<rel>/<skill>/SKILL.md
SCOPES = [
    # Grok user
    ("grok-user", Path("C:/Users/brsth/.grok/skills"), None),
    ("grok-bundled", Path("C:/Users/brsth/.grok/bundled/skills"), None),
    ("grok-installed-plugins", Path("C:/Users/brsth/.grok/installed-plugins"), "skills"),
    # Grok project
    ("grok-project", Path("P:/.grok/skills"), None),
    ("grok-agents", Path("P:/.agents/skills"), None),
    # Claude user
    ("claude-user", Path("C:/Users/brsth/.claude/skills"), None),
    # Claude project
    ("claude-project", Path("P:/.claude/skills"), None),
    # Codex user
    ("codex-user", Path("C:/Users/brsth/.codex/skills"), None),
    # Codex automations (treated as skills)
    ("codex-automations", Path("C:/Users/brsth/.codex/automations"), None),
    # Claude plugin caches — each plugin dir contains skills/<skill>/SKILL.md
    ("claude-cache-antigravity", Path("C:/Users/brsth/.claude/plugins/cache/antigravity-for-claude-code"), "skills"),
    ("claude-cache-official", Path("C:/Users/brsth/.claude/plugins/cache/claude-plugins-official"), "skills"),
    ("claude-cache-karpathy", Path("C:/Users/brsth/.claude/plugins/cache/karpathy-skills"), "skills"),
    ("claude-cache-local", Path("C:/Users/brsth/.claude/plugins/cache/local"), "skills"),
    ("claude-cache-minimax", Path("C:/Users/brsth/.claude/plugins/cache/minimax-skills"), "skills"),
    ("claude-cache-openai-codex", Path("C:/Users/brsth/.claude/plugins/cache/openai-codex"), "skills"),
    ("claude-cache-pi", Path("C:/Users/brsth/.claude/plugins/cache/pi-plugin-cc"), "skills"),
    ("claude-cache-ponytail", Path("C:/Users/brsth/.claude/plugins/cache/ponytail"), "skills"),
    ("claude-cache-superpowers", Path("C:/Users/brsth/.claude/plugins/cache/superpowers-marketplace"), "skills"),
    ("claude-cache-zai", Path("C:/Users/brsth/.claude/plugins/cache/zai-coding-plugins"), "skills"),
    # Claude marketplaces (separate from cache — same plugins, different staging)
    ("claude-mkt-local", Path("C:/Users/brsth/.claude/plugins/marketplaces/local/plugins"), "skills"),
    ("claude-mkt-quickstop", Path("C:/Users/brsth/.claude/plugins/marketplaces/quickstop/plugins"), "skills"),
    ("claude-mkt-thedotmack", Path("C:/Users/brsth/.claude/plugins/marketplaces/thedotmack"), "skills"),
    # Project marketplace (canonical plugin source)
    ("marketplace", Path("P:/packages/.claude-marketplace/plugins"), "skills"),
]


class SkillEntry(NamedTuple):
    scope: str
    name: str
    path: str
    description: str
    plugin: str | None  # for plugin-sourced skills


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)
_DESC_RE = re.compile(
    r"^description:\s*(.+?)(?=^\w+:|\Z)", re.MULTILINE | re.DOTALL
)


def parse_frontmatter(text: str) -> tuple[str, str]:
    """Extract name and description from SKILL.md frontmatter."""
    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        return ("", "")
    fm = fm_match.group(1)
    name_match = _NAME_RE.search(fm)
    desc_match = _DESC_RE.search(fm)
    name = name_match.group(1).strip() if name_match else ""
    desc = desc_match.group(1).strip() if desc_match else ""
    # strip YAML multi-line indicators
    desc = desc.strip("- >\n|")
    # collapse whitespace
    desc = re.sub(r"\s+", " ", desc).strip()
    # cap length for the stub
    if len(desc) > 500:
        desc = desc[:497] + "..."
    return (name, desc)


def scan_scope(scope: str, root: Path, plugin_rel: str | None) -> list[SkillEntry]:
    """Find all SKILL.md files under a scope root via deep glob.

    Robust to varying directory structures:
    - <root>/<skill>/SKILL.md (flat)
    - <root>/<plugin>/skills/<skill>/SKILL.md (plugin-nested)
    - <root>/<plugin>/<...>/skills/<skill>/SKILL.md (deeper)
    """
    if not root.exists():
        return []
    entries: list[SkillEntry] = []
    for skill_md in root.rglob("SKILL.md"):
        rel = skill_md.relative_to(root)
        parts = rel.parts
        # The skill name is the immediate parent of SKILL.md
        name_from_dir = parts[-2] if len(parts) >= 2 else root.name
        # Detect plugin: walk parts to find first non-'skills' segment
        plugin: str | None = None
        if plugin_rel:
            # Expecting <plugin>/skills/<skill>/SKILL.md or <plugin>/<version>/skills/<skill>/SKILL.md
            # or <plugin>/<sub>/skills/<skill>/SKILL.md
            # Plugin identifier is everything before the 'skills' segment, joined by '/'
            if "skills" in parts:
                skills_idx = parts.index("skills")
                if skills_idx > 0:
                    plugin = "/".join(parts[:skills_idx])
                else:
                    plugin = None
            elif len(parts) >= 3:
                plugin = parts[0]
        else:
            # No plugin nesting expected; if there are >2 parts, the first might still be a grouping dir
            if len(parts) > 2:
                plugin = parts[0]
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        name, desc = parse_frontmatter(text)
        entries.append(
            SkillEntry(
                scope=scope,
                name=name or name_from_dir,
                path=str(skill_md).replace("\\", "/"),
                description=desc,
                plugin=plugin,
            )
        )
    return entries


def slugify(scope: str, plugin: str | None, name: str) -> str:
    """Make a filesystem-safe stub filename.

    For cached plugins with version-hash subdirs (e.g. plugin-dev/779a5e7f15a0/...),
    include the version hash to prevent collisions across versions of the same plugin.
    For non-cached plugins, use the plugin name without hash.
    """
    parts = [scope]
    if plugin:
        # Plugin identifier may contain '/' (e.g., "plugin-dev/779a5e7f15a0") — make it filename-safe
        plugin_safe = plugin.replace("/", "-")
        parts.append(plugin_safe)
    name_clean = re.sub(r"[^a-z0-9-]", "-", name.lower())
    name_clean = re.sub(r"-+", "-", name_clean).strip("-")
    parts.append(name_clean)
    return "-".join(parts)


def write_stub(entry: SkillEntry) -> Path:
    """Write a lightweight stub file for qmd indexing."""
    slug = slugify(entry.scope, entry.plugin, entry.name)
    path = STUBS_DIR / f"{slug}.md"
    plugin_note = f"plugin: {entry.plugin}\n" if entry.plugin else ""
    content = f"""---
type: skill-reference
scope: {entry.scope}
{plugin_note}skill_name: {entry.name}
source_path: {entry.path}
indexed_date: {date.today().isoformat()}
---

# Skill: {entry.name}

**Scope:** {entry.scope}{f" (plugin: {entry.plugin})" if entry.plugin else ""}
**Path:** `{entry.path}`

{entry.description if entry.description else '(no description in frontmatter)'}

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_catalog(entries: list[SkillEntry]) -> None:
    """Write the human-readable catalog concept."""
    by_scope: dict[str, list[SkillEntry]] = {}
    for e in entries:
        by_scope.setdefault(e.scope, []).append(e)

    today = date.today().isoformat()
    lines = [
        "---",
        'title: "Skill catalog: index of all skills across the workspace"',
        f"created: 2026-07-21",
        f"updated: {today}",
        "source: auto-generated by P:/.data/wiki/scripts/index_skills.py",
        "tags: [skill-catalog, index, skills, plugins]",
        "host: both",
        "agent: grok",
        f"verification: generated_{today}",
        "cognitive_load: 3",
        f"summary: Auto-generated index of {len(entries)} skills across {len(by_scope)} directories. For semantic search of skill descriptions, query qmd; for human reference, scan the tables below.",
        "---",
        "",
        "# Skill catalog",
        "",
        f"Auto-generated on {today} by `python P:/.data/wiki/scripts/index_skills.py`. "
        f"Regenerate after adding or removing skills.",
        "",
        f"**Total skills:** {len(entries)} across {len(by_scope)} scopes.",
        "",
        "## How to use this catalog",
        "",
        "- **Semantic search:** `qmd search \"<capability>\" -c wiki` — returns matching skills from `sources/skills/` stubs",
        "- **Authoritative source:** always read the actual `SKILL.md` at the listed path (stubs may lag)",
        "- **Scope meanings:** see the table at the bottom of this page",
        "",
    ]

    for scope in [
        "grok-user",
        "grok-bundled",
        "grok-installed-plugins",
        "grok-project",
        "grok-agents",
        "claude-user",
        "claude-project",
        "codex-user",
        "codex-automations",
        "claude-cache-antigravity",
        "claude-cache-official",
        "claude-cache-karpathy",
        "claude-cache-local",
        "claude-cache-minimax",
        "claude-cache-openai-codex",
        "claude-cache-pi",
        "claude-cache-ponytail",
        "claude-cache-superpowers",
        "claude-cache-zai",
        "claude-mkt-local",
        "claude-mkt-quickstop",
        "claude-mkt-thedotmack",
        "marketplace",
    ]:
        scope_entries = by_scope.get(scope, [])
        if not scope_entries:
            continue
        lines.append(f"## {scope} ({len(scope_entries)} skills)")
        lines.append("")
        lines.append("| Skill | Description (truncated) | Path |")
        lines.append("|---|---|---|")
        for e in scope_entries:
            desc_short = e.description[:120] + ("..." if len(e.description) > 120 else "")
            desc_short = desc_short.replace("|", "\\|").replace("\n", " ")
            name_cell = f"**{e.name}**"
            if e.plugin:
                name_cell += f" _[{e.plugin}]_"
            path_short = e.path.replace("C:/Users/brsth", "~")
            path_short = path_short.replace("P:/packages/.claude-marketplace/plugins", "…/marketplace")
            lines.append(f"| {name_cell} | {desc_short} | `{path_short}` |")
        lines.append("")

    lines.extend([
        "## Scope definitions",
        "",
        "| Scope | Path | What lives here |",
        "|---|---|---|",
        "| `grok-user` | `~/.grok/skills/` | User-installed Grok skills, available in all projects |",
        "| `grok-bundled` | `~/.grok/bundled/skills/` | Skills bundled with Grok Build |",
        "| `grok-installed-plugins` | `~/.grok/installed-plugins/` | Skills from installed Grok plugins (firecrawl, superpowers, etc.) |",
        "| `grok-project` | `P:/.grok/skills/` | Project-specific Grok skills (aar, check, handoff, refactor, review) |",
        "| `grok-agents` | `P:/.agents/skills/` | Standalone agent skills (notebooklm, preflight, etc.) |",
        "| `claude-user` | `~/.claude/skills/` | User-installed Claude skills |",
        "| `claude-project` | `P:/.claude/skills/` | Project-specific Claude skills |",
        "| `codex-user` | `~/.codex/skills/` | Codex user skills |",
        "| `codex-automations` | `~/.codex/automations/` | Codex automation scripts treated as skills |",
        "| `claude-cache-*` | `~/.claude/plugins/cache/<source>/` | Cached skills from Claude plugin marketplaces |",
        "| `claude-mkt-*` | `~/.claude/plugins/marketplaces/<source>/` | Marketplaces not yet in cache (staging) |",
        "| `marketplace` | `P:/packages/.claude-marketplace/plugins/` | Canonical plugin source for this workspace |",
        "",
        "**Note on cache vs marketplace:** plugin caches hold installed-and-resolved plugins. The `marketplaces/` directory holds source-stage plugins that may not yet be promoted to cache. The same plugin can appear in both with different versions.",
        "",
        "## Related concepts",
        "",
        "- [[skill-authoring-patterns-dos-and-donts]] — do's and don'ts for writing skills",
        "- [[compound-skill-improvement-patterns]] — improvement patterns for compound/orchestrator skills",
        "- [[skill-techniques-index]] — techniques we've developed or adopted, indexed for reuse",
        "- [[skill-development-portfolio]] — what our skill-writing and skill-improving skills do",
        "- [[skill-enforcement-layers]] — Claude Code skill enforcement layer analysis",
        "",
        "## Regeneration",
        "",
        "```bash",
        "python P:/.data/wiki/scripts/index_skills.py",
        "```",
        "",
        "This script re-scans all 24 scope directories (Grok + Claude + Codex), writes stubs to `wiki/sources/skills/`, "
        "and rewrites this catalog. Run after adding or removing skills. Stubs are lightweight "
        "(frontmatter only) and won't drift from the source SKILL.md files. Also runs automatically "
        "as part of every `/wiki` invocation.",
        "",
    ])

    CATALOG_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    STUBS_DIR.mkdir(parents=True, exist_ok=True)
    # Clear old stubs to handle deletions
    for old in STUBS_DIR.glob("*.md"):
        old.unlink()

    all_entries: list[SkillEntry] = []
    for scope, root, plugin_rel in SCOPES:
        entries = scan_scope(scope, root, plugin_rel)
        for e in entries:
            write_stub(e)
        all_entries.extend(entries)
        print(f"{scope}: {len(entries)} skills")

    write_catalog(all_entries)
    print(f"\nTotal: {len(all_entries)} skills")
    print(f"Stubs written to: {STUBS_DIR}")
    print(f"Catalog written to: {CATALOG_PATH}")


if __name__ == "__main__":
    main()
