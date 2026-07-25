#!/usr/bin/env python3
"""parse_report.py — Stage B: parse Report markdown + Data-Table CSV into concept records.

Input:
  --report <path>     concepts-report.md from extract.py
  --data-table <path> optional facts.csv from extract.py
  --notebook <uuid>
  --notebook-title <str>

Output (stdout): JSON array of concept records:
  [{
    "slug": "nlm-<nb_short>-<concept-slug>",
    "title": "<Concept Name>",
    "definition": "<1-3 sentence definition from report>",
    "details": ["<bullet 1>", "<bullet 2>"],
    "values": [{"name": "...", "value": "..."}],
    "related": ["<other concept name>"],
    "citations": [{"claim": "...", "source_id": "...", "cited_text": "..."}],
    "source_section": "<raw markdown of the ## section>"
  }]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


def slugify(text: str, max_len: int = 50) -> str:
    text = text.lower().strip()
    # Normalize separators (spaces, hyphens, underscores) → single space first,
    # then strip non-alphanumeric, then collapse to hyphens. This way
    # "Machine-learning" and "Machine Learning" produce the same slug.
    text = re.sub(r"[\s\-_]+", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    if len(text) > max_len:
        # cut at word boundary
        cut = text[:max_len].rsplit("-", 1)[0]
        text = cut or text[:max_len]
    return text or "concept"


def short_uuid(uuid_str: str, n: int = 8) -> str:
    return uuid_str.replace("-", "")[:n]


def split_concepts(markdown: str) -> list[tuple[str, str]]:
    """Split markdown on '## ' headings. Returns [(title, body), ...]."""
    # Strip any leading content before the first ##
    idx = markdown.find("\n## ")
    if idx < 0:
        return []
    body = markdown[idx + 1:]
    parts = re.split(r"^## ", body, flags=re.MULTILINE)
    out = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        nl = part.find("\n")
        if nl < 0:
            continue
        title = part[:nl].strip().lstrip("#").strip()
        content = part[nl + 1:].strip()
        if title and content:
            out.append((title, content))
    return out


def parse_concept_body(body: str) -> dict:
    """Extract definition, details, values, related, citations from a concept body.

    Heuristic parser — Report prompt asks for numbered sections, but actual output
    varies. We extract by line patterns.
    """
    lines = body.splitlines()
    definition = ""
    details = []
    values = []
    related = []
    citations = []

    # Find a leading paragraph (before any list/heading) as definition
    para_lines = []
    for line in lines:
        s = line.strip()
        if not s:
            if para_lines:
                break
            continue
        if s.startswith(("#", "-", "*", "•", "1.", "2.")):
            break
        para_lines.append(s)
    if para_lines:
        definition = " ".join(para_lines)

    # Walk rest of body extracting items
    citation_re = re.compile(r"\[([^\]]+)\]\s*\(([^)]+)\)|\[?\[(\d+)\]?\]?")
    value_re = re.compile(r"([A-Z][\w\s-]{2,40}):\s*([0-9][\w.%/\- ]{0,30}|[a-z][\w-]{1,20})")

    current_section = None
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        # Section header (### or **Header:**)
        m = re.match(r"^(?:###\s+|\*\*)([\w ]+?)(?:\*\*|:)\s*$", s)
        if m:
            current_section = m.group(1).lower()
            continue
        # Bullet/numbered item
        if re.match(r"^[-*•]|\d+\.", s):
            item = re.sub(r"^[-*•]\s+|\d+\.\s+", "", s).strip()
            if "citation" in (current_section or "").lower() or item.startswith("["):
                # Citation line — best-effort parse
                cm = citation_re.search(item)
                if cm:
                    citations.append({
                        "claim": item[:300],
                        "source_id": cm.group(2) or cm.group(3) or "",
                        "cited_text": "",
                    })
                else:
                    citations.append({"claim": item[:300], "source_id": "", "cited_text": ""})
            elif "relat" in (current_section or "").lower():
                # Split on commas/semicolons
                for r in re.split(r"[,;]| and ", item):
                    r = r.strip()
                    if r:
                        related.append(r)
            elif "value" in (current_section or "").lower():
                vm = value_re.match(item)
                if vm:
                    values.append({"name": vm.group(1).strip(), "value": vm.group(2).strip()})
                else:
                    details.append(item)
            else:
                # Default: detail
                vm = value_re.match(item)
                if vm and len(vm.group(2)) < 30:
                    values.append({"name": vm.group(1).strip(), "value": vm.group(2).strip()})
                else:
                    details.append(item)

    return {
        "definition": definition,
        "details": details,
        "values": values,
        "related": related,
        "citations": citations,
    }


def merge_data_table(concepts: list[dict], dt_path: Path) -> None:
    """Merge tabular facts into concept records (in-place by name match)."""
    if not dt_path.exists():
        return
    by_name = {}
    try:
        with dt_path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Match on any column containing "concept" or "name"
                key = None
                for k, v in row.items():
                    if k and "concept" in k.lower() or (k and "name" in k.lower()):
                        key = (v or "").strip().lower()
                        break
                if key:
                    by_name[key] = row
    except Exception as exc:
        print(f"WARN: data-table parse failed: {exc}", file=sys.stderr)
        return

    for c in concepts:
        title_key = c["title"].lower()
        # Try exact and prefix match
        match = by_name.get(title_key) or next(
            (v for k, v in by_name.items() if title_key.startswith(k) or k.startswith(title_key)),
            None)
        if not match:
            continue
        # Merge values
        for k, v in match.items():
            if not v or not k:
                continue
            k_low = k.lower()
            if "value" in k_low and v.strip():
                for piece in v.split(";"):
                    piece = piece.strip()
                    if piece and not any(d["value"] == piece for d in c["values"]):
                        c["values"].append({"name": "from_data_table", "value": piece})
            elif "source" in k_low and v.strip() and v.strip() not in [c2["source_id"] for c2 in c["citations"]]:
                c["citations"].append({"claim": "(from data-table)", "source_id": v.strip(), "cited_text": ""})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--data-table", type=Path)
    ap.add_argument("--notebook", required=True)
    ap.add_argument("--notebook-title", required=True)
    args = ap.parse_args()

    markdown = args.report.read_text(encoding="utf-8")
    sections = split_concepts(markdown)
    if not sections:
        print("[]")
        print(f"WARN: no '## ' concept sections found in {args.report}", file=sys.stderr)
        return 1

    nb_short = short_uuid(args.notebook)
    concepts = []
    seen_slugs: set[str] = set()
    for title, body in sections:
        parsed = parse_concept_body(body)
        base_slug = f"nlm-{nb_short}-{slugify(title)}"
        slug = base_slug
        n = 2
        while slug in seen_slugs:
            slug = f"{base_slug}-{n}"
            n += 1
        seen_slugs.add(slug)
        concepts.append({
            "slug": slug,
            "title": title,
            "definition": parsed["definition"],
            "details": parsed["details"],
            "values": parsed["values"],
            "related": parsed["related"],
            "citations": parsed["citations"],
            "source_section": f"## {title}\n{body}",
            "notebook_id": args.notebook,
            "notebook_title": args.notebook_title,
        })

    if args.data_table:
        merge_data_table(concepts, args.data_table)

    json.dump(concepts, sys.stdout, ensure_ascii=False, indent=2)
    print(f"\nParsed {len(concepts)} concepts", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
