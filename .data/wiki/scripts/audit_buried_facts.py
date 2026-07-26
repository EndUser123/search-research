"""Scan wiki concepts for decision-time facts buried inside longer docs.

Per SCHEMA.md §13 principle #11: a decision-time fact (a cap, limit, default,
auth requirement, tier-specific behavior) should have its own page if a future
session would search for it by keyword.

This script scans concept pages for markers of buried decision-time facts:
  - Numbers that look like limits/caps/defaults ("up to N", "max N", "cap of N")
  - Auth-related claims ("requires auth", "expired", "login")
  - Tier-specific behaviors ("free tier", "paid account", "Plus plan")
  - API constraints ("rate limit", "quota", "throttle")

Pages with >500 chars AND containing ≥3 markers are candidates for splitting.
"""
import re
from pathlib import Path

VAULT = Path("P:/.data/wiki/concepts")

MARKER_PATTERNS = [
    (r"\b(max|maximum|cap|limit|up to|ceiling)\s+(of\s+)?\d+", "cap_or_limit"),
    (r"\b\d+\s*(sources?|items?|requests?|per\s+\w+)\b", "numeric_constraint"),
    (r"\b(free|paid|plus|pro|ultra)\s+(tier|account|plan|version)\b", "tier_specific"),
    (r"\b(authentication|login|expired?|credentials?)\s+(required|needed|failed|error)?", "auth_related"),
    (r"\b(rate\s+limit|quota|throttle|429)\b", "rate_limited"),
    (r"\b(default|defaults|by default)\b", "defaults"),
    (r"\b(requires?|must|needs?)\s+(a\s+)?(\w+\s+){0,3}(key|token|account|plan)", "requires_x"),
]


def scan_page(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    char_count = len(text)
    markers = []
    for pattern, label in MARKER_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # matches may be tuples (groups) — flatten
            n = len(matches)
            markers.append({"label": label, "count": n})
    total_markers = sum(m["count"] for m in markers)
    return {
        "path": str(path),
        "name": path.stem,
        "chars": char_count,
        "total_markers": total_markers,
        "marker_types": markers,
    }


def main():
    if not VAULT.exists():
        print(f"vault not found: {VAULT}")
        return

    pages = []
    for md in VAULT.glob("*.md"):
        info = scan_page(md)
        pages.append(info)

    # Filter: >500 chars AND ≥3 markers AND not already a "source-limits" or
    # similar fact-focused page (those are already split per principle #11)
    FACT_PAGE_KEYWORDS = ("source-limit", "rate-limit", "auth-", "tier-", "-cap", "-default")
    candidates = []
    for p in pages:
        if p["chars"] < 500:
            continue
        if p["total_markers"] < 3:
            continue
        if any(kw in p["name"].lower() for kw in FACT_PAGE_KEYWORDS):
            continue  # already a fact-focused page
        candidates.append(p)

    # Sort by marker density (markers per 1000 chars)
    candidates.sort(key=lambda p: p["total_markers"] / max(p["chars"], 1) * 1000, reverse=True)

    print(f"Scanned {len(pages)} pages in {VAULT}")
    print(f"Candidates for split-audit (>{500} chars, ≥3 markers, not already fact-focused): {len(candidates)}")
    print()
    print(f"{'Page':<55} {'chars':>6} {'markers':>8} {'types':>6}")
    print("-" * 80)
    for c in candidates[:30]:
        print(f"{c['name'][:55]:<55} {c['chars']:>6} {c['total_markers']:>8} {len(c['marker_types']):>6}")
        for m in c["marker_types"][:3]:
            print(f"    - {m['label']} ×{m['count']}")


if __name__ == "__main__":
    main()
