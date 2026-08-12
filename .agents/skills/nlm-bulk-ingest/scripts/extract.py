#!/usr/bin/env python3
"""extract.py — Stage 0: extract ALL videos from a YouTube channel.

YouTube channels split content across multiple tabs: /videos, /shorts,
/streams (and sometimes /podcasts, /playlists). Scraping only /videos
misses content — this script hits every tab automatically, dedupes by
video ID across tabs, and emits canonical.jsonl ready for cluster.py.

Usage:
  python extract.py <channel-url> [-o canonical.jsonl] [--yt-dlp PATH]
      [--profile NAME] [--tabs videos,shorts,streams]

Examples:
  python extract.py https://www.youtube.com/@moondevonyt
  python extract.py https://www.youtube.com/@moondevonyt -o canonical.jsonl
  python extract.py https://www.youtube.com/@moondevonyt --tabs videos

Notes:
  - Default tabs: videos, shorts, streams. Pass --tabs to override.
  - A tab that doesn't exist (404 or empty) is skipped with a warning.
  - Dedup is by YouTube video ID — cross-tab duplicates are collapsed.
  - Output format matches normalize.py's canonical JSONL shape, so
    cluster.py can consume the output directly.
  - Requires yt-dlp on PATH (or pass --yt-dlp /path/to/yt-dlp).

Incident that motivated this script (session 2026-08-12): a 1,019-video
channel was scraped via /videos only, yielding 351. The missing 668 were
in /shorts (662) and /streams (6). The agent declared done at 351. This
script makes that mistake structurally impossible — it hits all tabs by
default and reports the per-tab breakdown.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_TABS = ["videos", "shorts", "streams"]
SAFE_DELIM = "|||"  # avoids PowerShell pipe-encoding corruption of \t


def log(msg: str) -> None:
    print(msg, flush=True)


def run(cmd: list[str], timeout: int = 600) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8"
        )
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"


def resolve_yt_dlp(explicit: str | None) -> str:
    if explicit:
        return explicit
    found = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    if found:
        return found
    # Common Windows install location
    candidate = Path.home() / "AppData/Roaming/Python/Python314/Scripts/yt-dlp.exe"
    if candidate.exists():
        return str(candidate)
    sys.exit("ERROR: yt-dlp not found on PATH. Install it or pass --yt-dlp /path.")


def fetch_tab(ytdlp: str, channel: str, tab: str) -> list[dict]:
    """Fetch one tab via yt-dlp --flat-playlist. Returns list of {id,title}."""
    url = f"{channel.rstrip('/')}/{tab}"
    # --print-to-file writes directly, bypassing PowerShell pipe encoding
    tmp = Path(sys.argv[0]).resolve().parent / f"_extract_{tab}.txt"
    cmd = [
        ytdlp,
        "--flat-playlist",
        "--print-to-file",
        f"%(id)s{SAFE_DELIM}%(title)s",
        str(tmp),
        "--no-warnings",
        url,
    ]
    rc, _, err = run(cmd, timeout=600)
    if rc != 0 or not tmp.exists():
        log(f"  [{tab}] skipped (rc={rc}: {err.strip()[:120]})")
        if tmp.exists():
            tmp.unlink()
        return []
    items = []
    for line in tmp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or SAFE_DELIM not in line:
            continue
        vid, title = line.split(SAFE_DELIM, 1)
        vid = vid.strip()
        if vid:
            items.append({"id": vid, "title": title.strip()})
    tmp.unlink()
    log(f"  [{tab}] {len(items)} videos")
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("channel", help="Channel URL (e.g. https://www.youtube.com/@name)")
    ap.add_argument(
        "-o", "--output", default="canonical.jsonl", help="Output JSONL path"
    )
    ap.add_argument("--yt-dlp", default=None, help="Path to yt-dlp binary")
    ap.add_argument(
        "--tabs",
        default=",".join(DEFAULT_TABS),
        help=f"Comma-separated tabs to fetch (default: {','.join(DEFAULT_TABS)})",
    )
    ap.add_argument(
        "--profile",
        default=None,
        help="nlm profile name (unused by extract, recorded in source field)",
    )
    args = ap.parse_args()

    ytdlp = resolve_yt_dlp(args.yt_dlp)
    tabs = [t.strip() for t in args.tabs.split(",") if t.strip()]
    log(f"Channel: {args.channel}")
    log(f"Tabs: {', '.join(tabs)}")
    log(f"yt-dlp: {ytdlp}")
    log("")

    # Fetch each tab
    by_tab: dict[str, list[dict]] = {}
    for tab in tabs:
        by_tab[tab] = fetch_tab(ytdlp, args.channel, tab)

    # Dedupe by video ID across tabs, preserving first-seen order
    seen: dict[str, dict] = {}
    order: list[str] = []
    for tab in tabs:
        for item in by_tab[tab]:
            vid = item["id"]
            if vid in seen:
                # Record that this ID appeared on another tab
                seen[vid]["tabs"].add(tab)
                continue
            seen[vid] = {
                "id": vid,
                "title": item["title"],
                "url": f"https://www.youtube.com/watch?v={vid}",
                "tabs": {tab},
            }
            order.append(vid)

    total = len(order)
    tab_totals = {t: len(v) for t, v in by_tab.items()}
    log("")
    log("=== Summary ===")
    for t, n in tab_totals.items():
        log(f"  /{t}: {n}")
    cross_dup = sum(1 for r in seen.values() if len(r["tabs"]) > 1)
    log(f"  cross-tab duplicates (collapsed): {cross_dup}")
    log(f"  TOTAL UNIQUE: {total}")

    if total == 0:
        log("ERROR: no videos extracted. Check the channel URL and yt-dlp version.")
        return 1

    # Write canonical JSONL (normalize.py-compatible shape)
    out = Path(args.output)
    with out.open("w", encoding="utf-8") as f:
        for vid in order:
            rec = seen[vid]
            tabs_str = "+".join(
                tabs_order for tabs_order in [t for t in tabs if t in rec["tabs"]]
            )
            canonical = {
                "id": rec["id"],
                "title": rec["title"],
                "url": rec["url"],
                "source": f"{args.channel.rstrip('/')} ({tabs_str})",
            }
            f.write(json.dumps(canonical, ensure_ascii=False) + "\n")

    log(f"\nOutput: {out} ({total} records)")
    log("Next: python cluster.py " + str(out) + " --max-size 300 -o clusters.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
