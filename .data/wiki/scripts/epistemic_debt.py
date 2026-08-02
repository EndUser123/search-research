#!/usr/bin/env python3
"""
epistemic_debt.py — Scan wiki concepts for epistemic debt.

Computes a debt score for each wiki concept based on:
  - Verification tier (inferred > single-source > multi-source)
  - Age (older concepts accrue more debt)
  - Evidence gaps (each gap adds penalty)
  - Downstream dependencies (more dependents = higher stakes if wrong)

Outputs top-N highest-debt concepts with specific re-verification targets.
Writes to _state/research-suggestions.json for /todo and /www consumption.

Usage:
    python epistemic_debt.py                    # top-20, print + write JSON
    python epistemic_debt.py --top 50           # top-50
    python epistemic_debt.py --threshold 0.6    # only debt > 0.6
    python epistemic_debt.py --json             # JSON only (no human output)
    python epistemic_debt.py --dry-run          # print only, don't write JSON
"""

import argparse
import json
import re
import sys
from datetime import datetime, date
from pathlib import Path

WIKI_CONCEPTS = Path("P:/.data/wiki/concepts")
SUGGESTIONS_FILE = Path("P:/.data/wiki/_state/research-suggestions.json")

# Verification tier → base debt
VERIFICATION_DEBT = {
    "inferred-only": 0.8,
    "inferred": 0.8,
    "local-only": 0.6,
    "single-source-verified": 0.5,
    "single-source": 0.5,
    "observed": 0.4,
    "multi-source-verified": 0.2,
    "multi-source": 0.2,
}
DEFAULT_VERIFICATION_DEBT = 0.5  # unknown verification

# Relation type → dependency weight
RELATION_WEIGHTS = {
    "extends": 3,
    "supersedes": 3,
    "refines": 2,
    "complements": 1,
    "related": 1,
    "supports": 2,
    "contradicts": 0,  # already contested — not a dependency
}


def parse_frontmatter(content):
    """Extract YAML frontmatter as a dict (lightweight parser, no PyYAML dependency)."""
    fm = {}
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return fm
    yaml_text = match.group(1)
    
    # Simple key-value extraction
    for line in yaml_text.splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val and not val.startswith("[") and not val.startswith(">"):
                fm[key] = val
            elif val.startswith("["):
                # list field — count items
                items = [x.strip().strip('"').strip("'") for x in val.strip("[]").split(",") if x.strip()]
                fm[key] = items
    
    # Extract verification specifically
    for line in yaml_text.splitlines():
        if line.strip().startswith("verification:"):
            fm["verification"] = line.split(":", 1)[1].strip()
    
    # Count evidence_gaps (list items under evidence_gaps:)
    in_gaps = False
    gap_count = 0
    for line in yaml_text.splitlines():
        if re.match(r"^evidence_gaps:\s*$", line):
            in_gaps = True
            continue
        if in_gaps:
            if line.strip().startswith("- "):
                gap_count += 1
            elif line.strip() and not line.strip().startswith("-"):
                in_gaps = False
    fm["_evidence_gap_count"] = gap_count
    
    # Count relations (list items under relations:)
    in_relations = False
    relation_count = 0
    relation_types = {}
    for line in yaml_text.splitlines():
        if re.match(r"^relations:\s*$", line):
            in_relations = True
            continue
        if in_relations:
            if line.strip().startswith("- target:") or line.strip().startswith("- "):
                relation_count += 1
                # Extract type if present
                type_match = re.search(r"type:\s*(\w+)", line)
                if type_match:
                    rtype = type_match.group(1)
                    relation_types[rtype] = relation_types.get(rtype, 0) + 1
            elif line.strip() and not line.strip().startswith("-") and not line.strip().startswith("target:"):
                in_relations = False
    fm["_relation_count"] = relation_count
    fm["_relation_types"] = relation_types
    
    return fm


def parse_date(date_str):
    """Parse a date string, return date object or None."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(date_str[:len(fmt.replace("%", "0"))], fmt).date()
        except ValueError:
            continue
    return None


def compute_debt(fm, today=None):
    """Compute epistemic debt score for a concept based on its frontmatter.
    
    Returns: dict with debt score (0.0-1.0), breakdown, and re-verify targets.
    """
    if today is None:
        today = date.today()
    
    # 1. Base debt from verification tier
    verification = fm.get("verification", "").lower()
    base_debt = VERIFICATION_DEBT.get(verification, DEFAULT_VERIFICATION_DEBT)
    
    # 2. Age factor (0.0 for new, 1.0 for 1+ year old)
    created_str = fm.get("created", "")
    created_date = parse_date(created_str)
    if created_date:
        days_old = (today - created_date).days
        age_factor = min(1.0, days_old / 365.0)
    else:
        age_factor = 0.5  # unknown age
    
    # 3. Evidence gap penalty
    gap_count = fm.get("_evidence_gap_count", 0)
    gap_penalty = gap_count * 0.05
    
    # 4. Dependency weight (from relations)
    relation_types = fm.get("_relation_types", {})
    dependency_weight = sum(
        RELATION_WEIGHTS.get(rtype, 1) * count
        for rtype, count in relation_types.items()
    )
    dependency_factor = min(1.0, dependency_weight / 20.0)
    
    # 5. Confidence field (if present — new concepts from 2026-08-02+)
    confidence = fm.get("confidence", "")
    try:
        confidence_val = float(confidence)
        # If confidence is explicitly set, it overrides verification-derived base
        base_debt = min(base_debt, 1.0 - confidence_val)
    except (ValueError, TypeError):
        pass  # no confidence field — use verification-derived base
    
    # Final formula
    debt = base_debt * (0.5 + 0.3 * age_factor + 0.2 * dependency_factor) + gap_penalty
    debt = min(1.0, debt)  # cap at 1.0
    
    # Build re-verify targets
    targets = []
    if verification in ("inferred-only", "inferred", ""):
        targets.append(f"Verification is '{verification or 'missing'}' — claims need empirical checking")
    if gap_count > 0:
        targets.append(f"{gap_count} evidence gaps documented")
    if dependency_weight >= 10:
        targets.append(f"{dependency_weight} weighted downstream dependents — high blast radius if wrong")
    if age_factor >= 0.8:
        targets.append(f"Created {created_str} — may cite outdated sources")
    if not targets:
        targets.append("No specific re-verify targets — general re-check recommended")
    
    return {
        "debt": round(debt, 3),
        "breakdown": {
            "base_debt": round(base_debt, 3),
            "age_factor": round(age_factor, 3),
            "dependency_factor": round(dependency_factor, 3),
            "gap_penalty": round(gap_penalty, 3),
            "verification": verification or "missing",
            "dependency_weight": dependency_weight,
        },
        "re_verify_targets": targets,
    }


def scan_concepts():
    """Scan all wiki concepts, return list of (path, frontmatter, debt_info)."""
    results = []
    
    if not WIKI_CONCEPTS.exists():
        return results
    
    for md_file in sorted(WIKI_CONCEPTS.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        
        fm = parse_frontmatter(content)
        if not fm.get("title"):
            continue
        
        debt_info = compute_debt(fm)
        
        # Count incoming wikilinks (how many other concepts reference this one)
        slug = md_file.stem
        incoming = 0
        for other_file in WIKI_CONCEPTS.glob("*.md"):
            if other_file == md_file:
                continue
            try:
                other_content = other_file.read_text(encoding="utf-8")
                if f"[[{slug}]]" in other_content or f"[[{slug}|" in other_content:
                    incoming += 1
            except Exception:
                pass
        
        debt_info["incoming_links"] = incoming
        # Boost debt by incoming links (more referenced = higher stakes)
        incoming_boost = min(0.15, incoming * 0.02)
        debt_info["debt"] = round(min(1.0, debt_info["debt"] + incoming_boost), 3)
        
        results.append({
            "slug": slug,
            "title": fm.get("title", slug),
            "path": str(md_file),
            "verification": fm.get("verification", "missing"),
            "created": fm.get("created", "unknown"),
            "evidence_gaps": fm.get("_evidence_gap_count", 0),
            "outgoing_relations": fm.get("_relation_count", 0),
            "incoming_links": incoming,
            **debt_info,
        })
    
    return results


def format_output(results, top_n=20, threshold=0.0):
    """Format results for human-readable output."""
    filtered = [r for r in results if r["debt"] >= threshold]
    filtered.sort(key=lambda x: x["debt"], reverse=True)
    top = filtered[:top_n]
    
    if not top:
        return "No concepts above debt threshold.\n"
    
    lines = []
    lines.append(f"Epistemic Debt Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Scanned {len(results)} concepts. Showing top {len(top)} by debt (threshold: {threshold}).")
    lines.append("")
    
    for i, r in enumerate(top, 1):
        debt_emoji = "🔴" if r["debt"] >= 0.7 else "🟡" if r["debt"] >= 0.4 else "🟢"
        lines.append(f"{i:2d}. {debt_emoji} [{r['debt']:.2f}] [[{r['slug']}]]")
        lines.append(f"    Title: {r['title']}")
        lines.append(f"    Verification: {r['verification']} | Created: {r['created']} | Incoming links: {r['incoming_links']}")
        lines.append(f"    Evidence gaps: {r['evidence_gaps']} | Outgoing relations: {r['outgoing_relations']}")
        for target in r["re_verify_targets"][:3]:
            lines.append(f"    → {target}")
        lines.append("")
    
    return "\n".join(lines)


def write_suggestions(results, top_n=20, threshold=0.5):
    """Write debt-sorted suggestions to research-suggestions.json."""
    filtered = [r for r in results if r["debt"] >= threshold]
    filtered.sort(key=lambda x: x["debt"], reverse=True)
    top = filtered[:top_n]
    
    suggestions = []
    for r in top:
        suggestions.append({
            "topic": r["title"],
            "reason": f"Epistemic debt {r['debt']:.2f}: {r['re_verify_targets'][0]}",
            "suggested_skill": "/www",
            "confidence": "high" if r["debt"] >= 0.7 else "medium",
            "source_concept": r["path"],
            "debt_score": r["debt"],
            "debt_breakdown": r["breakdown"],
        })
    
    # Merge with existing suggestions
    SUGGESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if SUGGESTIONS_FILE.exists():
        try:
            existing = json.loads(SUGGESTIONS_FILE.read_text(encoding="utf-8"))
            # Remove old epistemic_debt entries
            existing = [s for s in existing if s.get("source") != "epistemic_debt"]
        except Exception:
            existing = []
    
    for s in suggestions:
        s["source"] = "epistemic_debt"
    
    merged = existing + suggestions
    
    tmp = SUGGESTIONS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    tmp.replace(SUGGESTIONS_FILE)
    
    return len(suggestions)


def main():
    parser = argparse.ArgumentParser(description="Epistemic debt scanner for wiki concepts")
    parser.add_argument("--top", type=int, default=20, help="Number of top-debt concepts to show")
    parser.add_argument("--threshold", type=float, default=0.0, help="Minimum debt score to include")
    parser.add_argument("--json", action="store_true", help="JSON output only")
    parser.add_argument("--dry-run", action="store_true", help="Print only, don't write suggestions file")
    args = parser.parse_args()
    
    print("Scanning wiki concepts...", file=sys.stderr)
    results = scan_concepts()
    print(f"Scanned {len(results)} concepts.", file=sys.stderr)
    
    if args.json:
        filtered = [r for r in results if r["debt"] >= args.threshold]
        filtered.sort(key=lambda x: x["debt"], reverse=True)
        print(json.dumps(filtered[:args.top], indent=2, default=str))
    else:
        print(format_output(results, args.top, args.threshold))
    
    if not args.dry_run:
        written = write_suggestions(results, top_n=args.top, threshold=max(args.threshold, 0.5))
        print(f"\nWrote {written} suggestions to {SUGGESTIONS_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
