#!/usr/bin/env python3
"""
Scan all external SKILL.md files (Claude plugins, bundled, installed-plugins,
agents skills) for capability frontmatter coverage and heuristic domain classification.

Purpose: identify which external skills provide capabilities (provides:/uses_capabilities:)
and which could be mapped to existing fleet capability domains via keyword matching.

This is pure code (no LLM). Keyword heuristics classify unmatched skills into
existing domains. Skills with no keyword match are flagged for manual review.

Usage:
    python scan_external_skills.py                    # summary report
    python scan_external_skills.py --json             # JSON output
    python scan_external_skills.py --by-domain        # group by inferred domain
    python scan_external_skills.py --unmatched        # only unmatched skills
"""
from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import re
import json
import argparse

# Roots to scan (all locations where SKILL.md files exist)
SCAN_ROOTS = [
    Path("C:/Users/brsth/.claude/skills"),
    Path("C:/Users/brsth/.claude/plugins/cache"),
    Path("C:/Users/brsth/.claude/plugins/marketplaces"),
    Path("C:/Users/brsth/.grok/installed-plugins"),
    Path("C:/Users/brsth/.grok/bundled/skills"),
    Path("C:/Users/brsth/.grok/skills"),  # our fleet (for comparison)
    Path("P:/.grok/skills"),
    Path("P:/.agents/skills"),
]

# Existing fleet capability domains (from capabilities/)
FLEET_DOMAINS = [
    "discovery", "review", "orchestration", "design", "cross-model",
    "fleet-ops", "infrastructure", "knowledge", "communication",
    "content", "verification", "coding",
]

# Keyword -> domain mapping for heuristic classification
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "discovery": ["search", "research", "web", "scrape", "crawl", "firecrawl",
                  "discover", "inventory", "marketplace", "model-discover"],
    "review": ["review", "critique", "critic", "audit", "code-review", "lint",
               "adversarial", "red-team", "stress-test"],
    "orchestration": ["orchestrat", "pipeline", "workflow", "sdlc", "go ",
                      "dispatch", "parallel", "delegate"],
    "design": ["design", "plan", "architect", "spec", "blueprint", "brainstorm"],
    "cross-model": ["codex", "gemini", "antigravity", "minimax", "mmx",
                    "agy", "openai", "second-opinion", "cross-model"],
    "fleet-ops": ["benchmark", "telemetry", "monitor", "health", "maintain",
                  "prune", "recover", "close", "workspace-health", "aar",
                  "retro", "debrief", "after-action", "performance", "perf",
                  "latency", "cost", "usage"],
    "infrastructure": ["git", "hook", "mcp", "server", "config", "plugin",
                       "permission", "auth", "route", "chrome", "devtools",
                       "browser", "skill", "create", "init", "setup"],
    "knowledge": ["wiki", "notebook", "nlm", "memory", "concept", "handoff",
                  "log", "index", "document"],
    "communication": ["email", "slack", "notify", "notice", "alert", "message"],
    "content": ["image", "video", "pdf", "docx", "pptx", "game", "asset",
                "generate", "imagine", "front-end", "ui"],
    "verification": ["test", "verify", "check", "validate", "assert",
                     "tdd", "pytest", "completion", "evidence", "experiment",
                     "probe"],
    "coding": ["code", "debug", "refactor", "implement", "develop", "programming",
               "function", "class", "method", "sdk", "api"],
}


def extract_frontmatter(body: str) -> dict:
    """Extract key frontmatter fields from a SKILL.md body."""
    parts = body.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = parts[1]
    result = {}

    # name
    m = re.search(r'^name:\s*(.+)$', fm, re.MULTILINE)
    result["name"] = m.group(1).strip().strip("'\"") if m else ""

    # description (first line only for speed)
    m = re.search(r'description:\s*>?\s*\n?\s*(.+?)(?:\n\n|\n\w)', fm, re.DOTALL)
    result["description"] = m.group(1).strip()[:200] if m else ""

    # provides
    m = re.search(r'provides:\s*\[([^\]]*)\]', fm)
    result["provides"] = [x.strip().strip("'\"").lower() for x in m.group(1).split(",") if x.strip()] if m else []

    # uses_capabilities
    m = re.search(r'uses_capabilities:\s*\[([^\]]*)\]', fm)
    result["uses_capabilities"] = [x.strip().strip("'\"").lower() for x in m.group(1).split(",") if x.strip()] if m else []

    # consumes
    m = re.search(r'consumes:\s*\[([^\]]*)\]', fm)
    result["consumes"] = [x.strip().strip("'\"").lower() for x in m.group(1).split(",") if x.strip()] if m else []

    # domain
    m = re.search(r'domain:\s*(\S+)', fm)
    result["domain"] = m.group(1).strip().strip("'\"") if m else ""

    return result


def classify_domain(name: str, description: str, existing_domain: str = "") -> str:
    """Heuristic domain classification using keyword matching."""
    if existing_domain and existing_domain in FLEET_DOMAINS:
        return existing_domain

    text = f"{name} {description}".lower()
    scores: dict[str, int] = defaultdict(int)
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[domain] += 1

    if scores:
        return max(scores, key=scores.get)
    return "unmatched"


def scan_all_roots() -> list[dict]:
    """Walk all scan roots and extract skill metadata."""
    skills = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for sf in root.rglob("SKILL.md"):
            try:
                body = sf.read_text(encoding="utf-8", errors="replace")
                fm = extract_frontmatter(body)
                if not fm:
                    continue

                root_name = str(root).replace("\\", "/")
                # Categorize the root
                if "installed-plugins" in root_name or "plugins/cache" in root_name or "marketplaces" in root_name:
                    source = "plugin"
                elif "bundled" in root_name:
                    source = "bundled"
                elif ".grok/skills" in root_name:
                    source = "grok-fleet"
                elif ".agents/skills" in root_name:
                    source = "agents"
                elif ".claude/skills" in root_name:
                    source = "claude-user"
                else:
                    source = "other"

                domain = classify_domain(
                    fm.get("name", sf.parent.name),
                    fm.get("description", ""),
                    fm.get("domain", ""),
                )

                skills.append({
                    "name": fm.get("name", sf.parent.name),
                    "path": str(sf),
                    "source": source,
                    "provides": fm.get("provides", []),
                    "uses_capabilities": fm.get("uses_capabilities", []),
                    "consumes": fm.get("consumes", []),
                    "declared_domain": fm.get("domain", ""),
                    "inferred_domain": domain,
                    "has_capability_frontmatter": bool(fm.get("provides") or fm.get("uses_capabilities")),
                })
            except Exception:
                continue
    return skills


def print_summary(skills: list[dict]):
    """Print a summary report."""
    total = len(skills)
    by_source = defaultdict(int)
    by_domain = defaultdict(int)
    with_caps = 0
    unmatched = []

    for s in skills:
        by_source[s["source"]] += 1
        by_domain[s["inferred_domain"]] += 1
        if s["has_capability_frontmatter"]:
            with_caps += 1
        if s["inferred_domain"] == "unmatched":
            unmatched.append(s)

    print(f"Total SKILL.md files scanned: {total}")
    print(f"With capability frontmatter (provides/uses_capabilities): {with_caps}")
    print(f"Without: {total - with_caps}")
    print()
    print("By source:")
    for source, count in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  {source:20s}: {count}")
    print()
    print("By inferred domain:")
    for domain, count in sorted(by_domain.items(), key=lambda x: -x[1]):
        print(f"  {domain:20s}: {count}")
    print()
    print(f"Unmatched (no keyword hit): {len(unmatched)}")
    if len(unmatched) <= 30:
        for s in sorted(unmatched, key=lambda x: x["name"]):
            desc = s.get("path", "")
            print(f"  {s['name']:30s} {desc}")


def print_by_domain(skills: list[dict]):
    """Group by inferred domain."""
    by_domain = defaultdict(list)
    for s in skills:
        by_domain[s["inferred_domain"]].append(s)
    for domain in sorted(by_domain.keys()):
        items = by_domain[domain]
        print(f"\n## {domain} ({len(items)} skills)")
        for s in sorted(items, key=lambda x: x["name"]):
            caps = ", ".join(s["provides"]) if s["provides"] else ""
            cap_note = f" [provides: {caps}]" if caps else ""
            print(f"  {s['name']:35s} ({s['source']}){cap_note}")


def print_unmatched(skills: list[dict]):
    """Print only unmatched skills for manual review."""
    unmatched = [s for s in skills if s["inferred_domain"] == "unmatched"]
    print(f"Unmatched skills ({len(unmatched)}):")
    for s in sorted(unmatched, key=lambda x: x["name"]):
        print(f"  {s['name']:35s} {s['path']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan external skills for capability coverage")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--by-domain", action="store_true", help="Group by inferred domain")
    parser.add_argument("--unmatched", action="store_true", help="Only unmatched skills")
    args = parser.parse_args()

    skills = scan_all_roots()

    if args.json:
        print(json.dumps(skills, indent=2))
    elif args.by_domain:
        print_by_domain(skills)
    elif args.unmatched:
        print_unmatched(skills)
    else:
        print_summary(skills)
