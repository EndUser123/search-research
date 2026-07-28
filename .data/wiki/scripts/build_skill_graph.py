"""
Build a skill dependency graph from SKILL.md files.

Extracts three edge types by scanning skill bodies:
1. delegates_to    — skill A calls skill B (e.g., /www delegates to /web)
2. consumes_provider — skill A uses MCP/CLI tool B (e.g., /web uses firecrawl)
3. references_wiki   — skill A references wiki concept B (e.g., /why references pattern-library)

Output: P:/.data/wiki/concepts/skill-graph.md (human-readable + embedded JSON)

Run after adding/removing skills or when dependencies change:
    python P:/.data/wiki/scripts/build_skill_graph.py

Design: edges are lexical (extracted from text patterns), not semantic.
False positives are cheap to dismiss; false negatives from manual upkeep
are expensive (proven session 2026-07-28: 8 files needed updates when
web-search-prime was disabled, but nothing tracked the dependencies).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

VAULT = Path("P:/.data/wiki")
GRAPH_PATH = VAULT / "concepts" / "skill-graph.md"

# Reuse the same scope list as index_skills.py
SCOPES = [
    ("grok-user", Path("C:/Users/brsth/.grok/skills")),
    ("grok-bundled", Path("C:/Users/brsth/.grok/bundled/skills")),
    ("grok-project", Path("P:/.grok/skills")),
    ("grok-agents", Path("P:/.agents/skills")),
    ("marketplace", Path("P:/packages/.claude-marketplace/plugins")),
]

# Patterns for edge extraction
# delegates_to: /web, /wiki, /why, /tp, /aar, /go, /design, /handoff, etc.
SKILL_REF_PATTERN = re.compile(
    r'(?:delegates?\s+to|calls?|invokes?|via)\s+/?'
    r'(web|wiki|why|tp|aar|go|design|handoff|crawl4ai|firecrawl'
    r'|search-fleet|grok-parallel|grok-verify|grok-safe-git'
    r'|grok-discovery|grok-route|check|close|review|plan-writer'
    r'|refine|red-team|notice|create-skill|packet|mmx|agy|codex'
    r'|debrief|maintain|wargame|skill-dev|skill-prune|model-benchmark'
    r'|recover|preflight|todo|tasks|imagine|help)'
    r'|/?(web|wiki|why|tp|aar|go|design|handoff|crawl4ai'
    r'|search-fleet|grok-parallel|grok-verify|grok-safe-git'
    r'|grok-discovery|grok-route|check|close|review|plan-writer'
    r'|refine|red-team|notice|create-skill|packet|mmx|agy|codex)'
    r'(?:\s+skill|\(|\s)',
    re.IGNORECASE,
)

# Simpler, more reliable pattern: find /skill-name references
SLASH_SKILL_PATTERN = re.compile(
    r'/(web|wiki|why|tp|aar|go|design|handoff|crawl4ai'
    r'|search-fleet|grok-parallel|grok-verify|grok-safe-git'
    r'|grok-discovery|grok-route|check|close|review|plan-writer'
    r'|refine|red-team|notice|create-skill|packet|mmx|agy|codex'
    r'|debrief|maintain|wargame|skill-dev|skill-prune|model-benchmark'
    r'|recover|preflight|todo|tasks|imagine|help)'
    r'\b',
    re.IGNORECASE,
)

# consumes_provider: MCP tools, CLI tools, built-in tools
PROVIDER_PATTERN = re.compile(
    r'(firecrawl|web-search-prime|web_search|minimax-search|minimax.search'
    r'|ddg|duckduckgo|exa|tavily|brave|serper|search-research'
    r'|mmx|agy|codex|context7|episodic-memory|chrome-devtools'
    r'|notebooklm|nlm|perplexity|pwm)'
    r'(?:__|\.|\s+(?:search|query|mcp|cli|api))',
    re.IGNORECASE,
)

# references_wiki: [[concept-slug]] or wiki/concepts/slug
WIKI_REF_PATTERN = re.compile(
    r'\[\[([a-z0-9-]+)\]\]|wiki/concepts/([a-z0-9-]+)\.md',
    re.IGNORECASE,
)

# Known skill names for filtering false positives from slash pattern
KNOWN_SKILLS = {
    'web', 'wiki', 'why', 'tp', 'aar', 'go', 'design', 'handoff',
    'crawl4ai', 'search-fleet', 'grok-parallel', 'grok-verify',
    'grok-safe-git', 'grok-discovery', 'grok-route', 'check', 'close',
    'review', 'plan-writer', 'refine', 'red-team', 'notice',
    'create-skill', 'packet', 'mmx', 'agy', 'codex', 'debrief',
    'maintain', 'wargame', 'skill-dev', 'skill-prune',
    'model-benchmark', 'recover', 'preflight', 'todo', 'tasks',
    'imagine', 'help',
}

# Known providers for filtering
KNOWN_PROVIDERS = {
    'firecrawl', 'web-search-prime', 'web_search', 'minimax-search',
    'ddg', 'duckduckgo', 'exa', 'tavily', 'brave', 'serper',
    'search-research', 'mmx', 'agy', 'codex', 'context7',
    'episodic-memory', 'chrome-devtools', 'notebooklm', 'nlm',
    'perplexity', 'pwm',
}


class SkillNode:
    def __init__(self, name: str, path: str, scope: str):
        self.name = name
        self.path = path
        self.scope = scope
        self.delegates_to: set[str] = set()
        self.consumes_provider: set[str] = set()
        self.references_wiki: set[str] = set()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "scope": self.scope,
            "delegates_to": sorted(self.delegates_to),
            "consumes_provider": sorted(self.consumes_provider),
            "references_wiki": sorted(self.references_wiki),
        }


def find_skills() -> list[SkillNode]:
    """Scan all scope directories for SKILL.md files."""
    skills = []
    for scope, root in SCOPES:
        if not root.exists():
            continue
        # Direct skills: <root>/<skill-name>/SKILL.md
        for skill_dir in sorted(root.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists() and skill_dir.name != "__pycache__":
                skills.append(SkillNode(skill_dir.name, str(skill_file), scope))
        # Plugin skills: <root>/<plugin>/skills/<skill>/SKILL.md
        if root.name == "plugins":
            for plugin_dir in sorted(root.iterdir()):
                skills_sub = plugin_dir / "skills"
                if skills_sub.exists():
                    for skill_dir in sorted(skills_sub.iterdir()):
                        skill_file = skill_dir / "SKILL.md"
                        if skill_file.exists():
                            skills.append(SkillNode(
                                skill_dir.name, str(skill_file), scope
                            ))
    return skills


def extract_edges(skill: SkillNode) -> None:
    """Scan a SKILL.md body and extract edges."""
    try:
        full_text = Path(skill.path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return

    body = full_text.lower()

    # Phase 1: Read structured frontmatter as ground truth (if present)
    import re as _re
    parts = full_text.split("---", 2)
    if len(parts) >= 3:
        fm = parts[1]
        dep_match = _re.search(r"depends_on:\s*\[([^\]]*)\]", fm)
        con_match = _re.search(r"consumes:\s*\[([^\]]*)\]", fm)
        if dep_match:
            for dep in dep_match.group(1).split(","):
                dep = dep.strip().strip("'\"").lower()
                if dep and dep != skill.name:
                    skill.delegates_to.add(dep)
        if con_match:
            for con in con_match.group(1).split(","):
                con = con.strip().strip("'\"").lower()
                if con:
                    skill.consumes_provider.add(con)

    # Phase 2: Lexical scan as linter — detects undeclared edges
    # These add to the frontmatter-derived set, flagging gaps
    for m in SLASH_SKILL_PATTERN.finditer(body):
        target = m.group(1).lower()
        if target in KNOWN_SKILLS and target != skill.name:
            skill.delegates_to.add(target)

    # Also check "delegates to" / "calls" / "via" patterns
    for m in SKILL_REF_PATTERN.finditer(body):
        target = (m.group(1) or m.group(2) or "").lower()
        if target in KNOWN_SKILLS and target != skill.name:
            skill.delegates_to.add(target)

    # Extract consumes_provider
    for m in PROVIDER_PATTERN.finditer(body):
        provider = m.group(1).lower()
        if provider in KNOWN_PROVIDERS:
            skill.consumes_provider.add(provider)

    # Extract references_wiki
    for m in WIKI_REF_PATTERN.finditer(body):
        slug = (m.group(1) or m.group(2) or "").lower()
        if slug:
            skill.references_wiki.add(slug)


def build_reverse_index(skills: list[SkillNode]) -> dict:
    """Build reverse lookups: provider → skills that use it, skill → skills that delegate to it."""
    provider_consumers: dict[str, list[str]] = defaultdict(list)
    skill_callers: dict[str, list[str]] = defaultdict(list)
    wiki_referencers: dict[str, list[str]] = defaultdict(list)

    for skill in skills:
        for provider in skill.consumes_provider:
            provider_consumers[provider].append(skill.name)
        for target in skill.delegates_to:
            skill_callers[target].append(skill.name)
        for wiki in skill.references_wiki:
            wiki_referencers[wiki].append(skill.name)

    return {
        "provider_consumers": {k: sorted(set(v)) for k, v in provider_consumers.items()},
        "skill_callers": {k: sorted(set(v)) for k, v in skill_callers.items()},
        "wiki_referencers": {k: sorted(set(v)) for k, v in wiki_referencers.items()},
    }


def generate_markdown(skills: list[SkillNode], reverse: dict) -> str:
    """Generate the human-readable wiki concept."""
    today = date.today().isoformat()

    # Provider blast-radius table
    provider_lines = []
    for provider in sorted(reverse["provider_consumers"]):
        consumers = reverse["provider_consumers"][provider]
        provider_lines.append(
            f"| `{provider}` | {len(consumers)} | {', '.join(f'`{c}`' for c in consumers)} |"
        )

    # Skill delegation table
    delegation_lines = []
    for target in sorted(reverse["skill_callers"]):
        callers = reverse["skill_callers"][target]
        delegation_lines.append(
            f"| `{target}` | {len(callers)} | {', '.join(f'`{c}`' for c in callers)} |"
        )

    # Per-skill edges
    skill_lines = []
    for skill in sorted(skills, key=lambda s: s.name):
        d = ', '.join(f'`{t}`' for t in sorted(skill.delegates_to)) or '—'
        p = ', '.join(f'`{pr}`' for pr in sorted(skill.consumes_provider)) or '—'
        skill_lines.append(f"| `{skill.name}` | {d} | {p} |")

    # Embed JSON for machine consumption
    graph_json = json.dumps(
        {
            "nodes": [s.to_dict() for s in skills],
            "reverse": reverse,
        },
        indent=2,
    )

    return f"""---
title: "Skill dependency graph: who calls what and who consumes which providers"
created: {today}
source: auto-generated
generator: P:/.data/wiki/scripts/build_skill_graph.py
tags: [skill-graph, dependencies, providers, delegation, blast-radius, maintenance, reference]
summary: >
  Auto-generated dependency graph of all workspace skills. Three edge
  types: delegates_to (skill calls skill), consumes_provider (skill uses
  MCP/CLI tool), references_wiki (skill cites wiki concept). Use for
  blast-radius analysis when a provider changes status. Rebuild:
  python P:/.data/wiki/scripts/build_skill_graph.py
agent: grok
host: grok
cognitive_load: 2
verification: auto-generated
---

# Skill dependency graph

> **Auto-generated** from SKILL.md files. Edges are lexical (extracted
> from text patterns), not semantic — false positives are cheap to dismiss.
> Rebuild after skill changes: `python P:/.data/wiki/scripts/build_skill_graph.py`

## How to use this

**Blast-radius analysis:** when a provider changes status (disabled, broken,
migrated), look it up in the "Provider consumers" table. Every skill listed
references that provider and may need updating.

**Delegation tracing:** when a skill changes behavior, look it up in the
"Delegation targets" table. Every caller depends on it and may need review.

## Provider consumers (who uses what)

When a provider is disabled/broken/migrated, these skills need updates:

| Provider | Consumer count | Skills |
|----------|---------------|--------|
{chr(10).join(provider_lines) if provider_lines else '| — | 0 | — |'}

## Delegation targets (who calls this skill)

When a skill changes its interface or behavior, these callers are affected:

| Target skill | Caller count | Called by |
|-------------|-------------|-----------|
{chr(10).join(delegation_lines) if delegation_lines else '| — | 0 | — |'}

## Per-skill edges

| Skill | Delegates to | Consumes provider |
|-------|-------------|------------------|
{chr(10).join(skill_lines) if skill_lines else '| — | — | — |'}

## Machine-readable graph

```json
{graph_json}
```

## Falsifier

This graph is wrong if:
- A skill delegates to another but no edge appears (false negative — pattern
  didn't match the phrasing). Fix: extend the pattern in build_skill_graph.py.
- An edge appears that doesn't represent a real dependency (false positive —
  skill mentions a tool name in a comment, not an active code path).
  Acceptable for discovery — verify before acting on any single edge.
- The graph is not regenerated after skill changes (drift). Run the script
  after any skill addition, removal, or dependency change.

## Provenance

Built 2026-07-28 after the web-search-prime disablement revealed that 8+
files needed updates but nothing tracked the dependency chain. The graph
answers "who uses this provider?" in one lookup instead of grepping the
entire workspace.
"""


def main():
    print("Scanning skills...")
    skills = find_skills()
    print(f"  Found {len(skills)} skills")

    print("Extracting edges...")
    for skill in skills:
        extract_edges(skill)

    total_delegations = sum(len(s.delegates_to) for s in skills)
    total_providers = sum(len(s.consumes_provider) for s in skills)
    total_wiki = sum(len(s.references_wiki) for s in skills)
    print(f"  {total_delegations} delegation edges")
    print(f"  {total_providers} provider edges")
    print(f"  {total_wiki} wiki-reference edges")

    print("Building reverse index...")
    reverse = build_reverse_index(skills)

    print(f"Generating graph at {GRAPH_PATH}...")
    markdown = generate_markdown(skills, reverse)
    GRAPH_PATH.write_text(markdown, encoding="utf-8")
    print(f"  Written {len(markdown)} bytes")

    print("Done.")


if __name__ == "__main__":
    main()
