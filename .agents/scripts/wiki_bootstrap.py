#!/usr/bin/env python3
"""Generate a cold-start bootstrap view: top 10 concepts a fresh agent should read.

Ranks by inbound [[wikilink]] count (most-referenced = most load-bearing).
Outputs to P:/.data/wiki/_state/wiki-bootstrap.md for session-start consumption.
"""
from pathlib import Path
from collections import Counter
import re

vault = Path("P:/.data/wiki/concepts")
concepts = list(vault.glob("*.md"))

# Count inbound links for each concept
inbound = Counter()
for c in concepts:
    text = c.read_text(encoding="utf-8", errors="replace")
    # Find all [[wikilinks]]
    links = re.findall(r'\[\[([^\]|@]+)', text)
    for link in links:
        slug = link.strip().lower().replace(" ", "-")
        inbound[slug] += 1

# Rank by inbound count
ranked = sorted(inbound.items(), key=lambda x: -x[1])[:15]

print("# Wiki Bootstrap — Top Concepts for Fresh Agents")
print()
print("These are the most-referenced concepts in the vault. A fresh agent")
print("should read these first to understand the workspace's core patterns.")
print()
for i, (slug, count) in enumerate(ranked, 1):
    # Find the actual file
    matches = list(vault.glob(f"*{slug[:30]}*"))
    if matches:
        name = matches[0].stem
        print(f"{i}. [[{name}]] ({count} inbound links)")
    else:
        print(f"{i}. [[{slug}]] ({count} inbound links)")

# Write to _state
state_dir = Path("P:/.data/wiki/_state")
state_dir.mkdir(parents=True, exist_ok=True)
bootstrap = state_dir / "wiki-bootstrap.md"
bootstrap.write_text("\n".join([
    "# Wiki Bootstrap — Top Concepts for Fresh Agents",
    "",
    f"Generated: 2026-08-02 from {len(concepts)} concepts",
    "",
    "Most-referenced concepts (highest inbound [[wikilink]] count):",
    "",
] + [f"{i}. [[{slug}]] ({count} refs)" for i, (slug, count) in enumerate(ranked, 1)]
), encoding="utf-8")
print(f"\nWritten to: {bootstrap}")
