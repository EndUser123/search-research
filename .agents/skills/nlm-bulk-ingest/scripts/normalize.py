#!/usr/bin/env python3
"""normalize.py — Stage 1-2: convert any input to canonical JSONL + dedup + filter.

Input → canonical.jsonl with shape:
  {"id": str, "title": str, "url": str, "source": str, "raw": {...}}

Usage:
  python normalize.py <input> [--format auto] [--id/title/url/source-field NAME]
      [--drop-dead] [-o canonical.jsonl]

Supported formats (auto-detected by content/extension unless --format given):
  youtube-wl   YouTube watch-later JSON export
  csv          CSV (auto-detect url/title columns or use field flags)
  jsonl        one JSON object per line; specify fields via --*-field
  json-array   JSON array of objects
  url-list     one URL per line
  rss          RSS/Atom feed
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


# ---------- format detection ----------

def detect_format(path: Path, hint: str | None) -> str:
    if hint and hint != "auto":
        return hint
    name = path.name.lower()
    if name.endswith(".csv"):
        return "csv"
    if name.endswith(".jsonl") or name.endswith(".ndjson"):
        return "jsonl"
    if name.endswith(".xml") or name.endswith(".rss"):
        return "rss"
    if name.endswith(".txt"):
        return "url-list"
    # JSON: array or single object — sniff
    try:
        with path.open(encoding="utf-8") as f:
            head = f.read(2048).strip()
        if head.startswith("["):
            return "json-array"
        if head.startswith("{") and "\"videoId\"" in head[:2000]:
            return "youtube-wl"
        if head.startswith("{"):
            return "json-array"  # single object wrapped, treat as 1-element array
    except Exception:
        pass
    # line-based sniff
    try:
        with path.open(encoding="utf-8") as f:
            line1 = f.readline().strip()
            line2 = f.readline().strip()
        if line1.startswith("{") and line2.startswith("{"):
            return "jsonl"
        if line1.startswith("http://") or line1.startswith("https://"):
            return "url-list"
    except Exception:
        pass
    raise SystemExit(f"Could not auto-detect format for {path}; pass --format explicitly")


# ---------- parsers (each yields raw dicts) ----------

def parse_youtube_wl(path: Path):
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit("youtube-wl: expected JSON array")
    for e in data:
        yield {
            "id": e.get("videoId") or e.get("id"),
            "title": e.get("title", ""),
            "url": e.get("url") or (f"https://www.youtube.com/watch?v={e['videoId']}" if e.get("videoId") else ""),
            "source": e.get("channel") or e.get("channelId") or "",
            "raw": e,
        }


def parse_jsonl(path: Path, id_field, title_field, url_field, source_field):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"WARN: skipping unparseable line: {exc}", file=sys.stderr)
                continue
            yield {
                "id": e.get(id_field) if id_field else e.get("id"),
                "title": e.get(title_field) if title_field else e.get("title", ""),
                "url": e.get(url_field) if url_field else e.get("url", ""),
                "source": e.get(source_field) if source_field else (e.get("source") or e.get("channel") or e.get("author") or ""),
                "raw": e,
            }


def parse_json_array(path: Path, id_field, title_field, url_field, source_field):
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise SystemExit("json-array: expected list or single object")
    for e in data:
        yield {
            "id": e.get(id_field) if id_field else e.get("id"),
            "title": e.get(title_field) if title_field else e.get("title", ""),
            "url": e.get(url_field) if url_field else e.get("url", ""),
            "source": e.get(source_field) if source_field else (e.get("source") or e.get("channel") or e.get("author") or ""),
            "raw": e,
        }


def parse_csv(path: Path, id_field, title_field, url_field, source_field):
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Auto-detect columns if not specified
        cols = reader.fieldnames or []
        url_col = url_field or next((c for c in cols if "url" in c.lower() or "link" in c.lower()), None)
        title_col = title_field or next((c for c in cols if "title" in c.lower() or "name" in c.lower()), None)
        id_col = id_field or next((c for c in cols if c.lower() in ("id", "video_id", "videoid")), None)
        src_col = source_field or next((c for c in cols if any(k in c.lower() for k in ("channel", "author", "source"))), None)
        if not url_col:
            raise SystemExit(f"csv: no URL column found in {cols}; pass --url-field")
        for e in reader:
            yield {
                "id": e.get(id_col) if id_col else None,
                "title": e.get(title_col, "") if title_col else "",
                "url": e.get(url_col, ""),
                "source": e.get(src_col, "") if src_col else "",
                "raw": e,
            }


def parse_url_list(path: Path):
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            # Title from path
            parsed = urlparse(url)
            title = parsed.path.rstrip("/").split("/")[-1].replace("-", " ") or url
            yield {
                "id": hashlib.sha1(url.encode("utf-8")).hexdigest()[:16],
                "title": title,
                "url": url,
                "source": parsed.netloc,
                "raw": {"url": url},
            }


def parse_rss(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    # Strip namespaces for item lookups
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for item in items:
        # NOTE: do NOT use `or` chaining on XML elements — Element.__bool__ is
        # False when the element has no children, so `a or b` always evaluates b.
        # Use explicit `is not None` checks.
        title_el = item.find("title")
        if title_el is None:
            title_el = item.find("{http://www.w3.org/2005/Atom}title")
        link_el = item.find("link")
        if link_el is None:
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
        guid_el = item.find("guid")
        if guid_el is None:
            guid_el = item.find("{http://www.w3.org/2005/Atom}id")
        url = ""
        if link_el is not None:
            url = link_el.text or (link_el.get("href") or "")
        title = title_el.text if title_el is not None else ""
        guid = guid_el.text if guid_el is not None else hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
        yield {
            "id": guid,
            "title": title,
            "url": url,
            "source": urlparse(url).netloc if url else "",
            "raw": {"title": title, "link": url, "guid": guid},
        }


# ---------- normalize + dedup + filter ----------

DEAD_TITLE_MARKERS = ("[Deleted video]", "[Private video]", "[Deleted]", "[Private]")
UNKNOWN_SOURCE = "[unknown]"


def normalize_title(t: str) -> str:
    t = (t or "").lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def normalize_source(s: str) -> str:
    return (s or "").lower().strip()


def is_addable(entry: dict, drop_dead: bool) -> bool:
    if not entry.get("url"):
        return False
    if drop_dead:
        title = (entry.get("title") or "").strip()
        source = (entry.get("source") or "").strip()
        if title in DEAD_TITLE_MARKERS:
            return False
        if source == UNKNOWN_SOURCE:
            return False
    return True


def stable_id(entry: dict) -> str:
    """Stable dedup key: prefer explicit id, else hash of normalized (title, url)."""
    raw_id = entry.get("id")
    if raw_id:
        return str(raw_id)
    key = f"{normalize_title(entry['title'])}|{entry.get('url', '')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("--format", default="auto",
                    choices=["auto", "youtube-wl", "csv", "jsonl", "json-array", "url-list", "rss"])
    ap.add_argument("--id-field")
    ap.add_argument("--title-field")
    ap.add_argument("--url-field")
    ap.add_argument("--source-field")
    ap.add_argument("--drop-dead", action="store_true",
                    help="Drop items that can't be ingested (deleted/private/unknown source)")
    ap.add_argument("-o", "--output", type=Path, default=Path("canonical.jsonl"))
    args = ap.parse_args()

    fmt = detect_format(args.input, args.format)
    print(f"Format: {fmt}", file=sys.stderr)

    if fmt == "youtube-wl":
        raw_items = parse_youtube_wl(args.input)
    elif fmt == "jsonl":
        raw_items = parse_jsonl(args.input, args.id_field, args.title_field, args.url_field, args.source_field)
    elif fmt == "json-array":
        raw_items = parse_json_array(args.input, args.id_field, args.title_field, args.url_field, args.source_field)
    elif fmt == "csv":
        raw_items = parse_csv(args.input, args.id_field, args.title_field, args.url_field, args.source_field)
    elif fmt == "url-list":
        raw_items = parse_url_list(args.input)
    elif fmt == "rss":
        raw_items = parse_rss(args.input)
    else:
        raise SystemExit(f"unknown format: {fmt}")

    seen: set[str] = set()
    kept: list[dict] = []
    dropped_dead = 0
    dropped_dup = 0

    for entry in raw_items:
        if not is_addable(entry, args.drop_dead):
            dropped_dead += 1
            continue
        sid = stable_id(entry)
        if sid in seen:
            dropped_dup += 1
            continue
        seen.add(sid)
        entry["id"] = sid
        kept.append(entry)

    with args.output.open("w", encoding="utf-8") as f:
        for e in kept:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"Kept: {len(kept)}", file=sys.stderr)
    print(f"Dropped duplicates: {dropped_dup}", file=sys.stderr)
    print(f"Dropped dead/unaddable: {dropped_dead}", file=sys.stderr)
    print(f"Output: {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
