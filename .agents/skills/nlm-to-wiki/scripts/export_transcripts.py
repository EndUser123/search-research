#!/usr/bin/env python3
"""export_transcripts.py — Stage A (v3): export raw source transcripts from a notebook.

Replaces v2's extract.py (which triggered NotebookLM Report + Data-Table
synthesis). v3 exports the *primary* content: the raw transcript of each
source via `nlm source content <source_id>`. Transcripts are written to
`wiki/sources/transcripts/<source_id>.md` with provenance frontmatter, per
the wiki SCHEMA rule that sources/ holds verbatim material and concepts/
holds distilled synthesis.

The export primitive is verified correct: NotebookLM's `nlm source content`
returns the raw indexed text of each source (the actual transcript), not an
LLM synthesis. See [[video-to-wiki-pipeline-transcript-extraction-multimodal]]
§ "Export raw transcripts, don't synthesize at the source".

Usage:
  python export_transcripts.py --notebook <uuid> --profile codex \\
      --out P:/.data/wiki/sources/transcripts/

Crash-resumable: sources whose transcript file already exists are skipped
unless --force. Rate-limited via --spacing (default 1.5s between calls) to
avoid hitting NotebookLM's per-account request ceiling.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path


def run(cmd: list[str], timeout: int = 180) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True, file=sys.stderr)


def list_sources(notebook_id: str, profile: str) -> list[dict]:
    """Return the notebook's sources via `nlm source list --json`.

    Handles both list and {"sources": [...]} envelope shapes (defensive
    against nlm version drift — sync.py uses the same dual-shape parse).
    """
    rc, out, err = run(["nlm", "source", "list", notebook_id,
                        "--profile", profile, "--json"], timeout=180)
    if rc != 0:
        log(f"  source list failed rc={rc}: {(err or out).strip()[:300]}")
        return []
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else data.get("sources", [])
    except json.JSONDecodeError:
        log(f"  source list output not JSON: {out.strip()[:200]}")
        return []


def fetch_content(source_id: str, profile: str) -> tuple[str, str]:
    """Fetch raw transcript for one source.

    Returns (content_text, error_message). Tries --json first (structured),
    falls back to plain text. `nlm source content` returns the raw indexed
    text — verified against yt-nlm/SKILL.md which documents this as the
    correct extraction primitive.
    """
    # Try structured first
    rc, out, err = run(["nlm", "source", "content", source_id,
                        "--profile", profile, "--json"], timeout=120)
    if rc == 0 and out.strip():
        try:
            data = json.loads(out)
            # Common envelope keys across nlm versions
            for key in ("content", "text", "body", "transcript", "data"):
                val = data.get(key) if isinstance(data, dict) else None
                if isinstance(val, str) and val.strip():
                    return val, ""
            # If the JSON IS the content (a bare string) or has no known key,
            # dump the parsed object as the transcript text.
            if isinstance(data, str):
                return data, ""
            # Structured but unknown shape — fall through to text mode for fidelity
        except json.JSONDecodeError:
            pass  # not JSON; treat stdout as raw text below

    # Plain text fallback
    rc, out, err = run(["nlm", "source", "content", source_id,
                        "--profile", profile], timeout=120)
    if rc == 0 and out.strip():
        return out, ""
    return "", (err or out or f"rc={rc}").strip()[:300]


def fetch_via_ytdlp(source: dict) -> tuple[str, str]:
    """Recover a transcript via yt-dlp when NotebookLM failed to index it.

    Triggered for sources with status=3 (NotebookLM import failure). Recovers
    the YouTube video ID from the source title when NotebookLM stored the raw
    URL as the title (happens when it couldn't parse the video metadata). Falls
    back to yt-dlp's auto-subtitle download.

    Returns (transcript_text, error_message). Empty transcript + non-empty
    error means recovery failed (video unavailable, no captions, or no URL
    recoverable from the title).
    """
    import re as _re
    title = source.get("title", "")
    # Extract 11-char YouTube video ID from URL-shaped titles
    m = _re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", title)
    if not m:
        return "", f"no video_id in title (title is descriptive, not a URL)"
    vid = m.group(1)
    url = f"https://www.youtube.com/watch?v={vid}"

    # Fetch auto-generated captions via yt-dlp (no video download)
    rc, out, err = run(
        ["yt-dlp", "--write-auto-sub", "--sub-lang", "en", "--skip-download",
         "--sub-format", "vtt", "-o", "-", url],
        timeout=60)
    if rc != 0 or not out.strip():
        # Try manual subs as fallback
        rc, out, err = run(
            ["yt-dlp", "--write-sub", "--sub-lang", "en", "--skip-download",
             "--sub-format", "vtt", "-o", "-", url],
            timeout=60)
    if rc != 0 or not out.strip():
        return "", f"yt-dlp failed for {vid}: {(err or 'no captions').strip()[:150]}"

    # Strip VTT timestamps + tags to produce plain text
    lines = []
    seen = set()
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in line:  # timestamp line
            continue
        if line.startswith("<"):  # VTT cue tag
            continue
        if line.isdigit():  # cue index
            continue
        # Deduplicate consecutive repeated lines (auto-caption artifact)
        clean = _re.sub(r"<[^>]+>", "", line).strip()
        if clean and clean not in seen:
            seen.add(clean)
            lines.append(clean)
    text = " ".join(lines)
    if len(text) < 10:
        return "", f"yt-dlp captions too short for {vid} ({len(text)} chars)"
    return text, ""


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def build_transcript_md(source: dict, notebook_id: str, content: str) -> str:
    """Render a transcript markdown file with provenance frontmatter."""
    sid = source.get("id", "")
    title = (source.get("title") or "").replace('"', "'")
    url = source.get("url") or ""
    stype = source.get("type") or "unknown"
    fm = [
        "---",
        f'source_id: "{sid}"',
        f'title: "{title}"',
        f"notebook_id: {notebook_id}",
        f"url: {url or 'null'}",
        f"type: {stype}",
        f"exported: {date.today().isoformat()}",
        "---",
        "",
        f"# {title or sid}",
        "",
    ]
    return "\n".join(fm) + content.rstrip() + "\n"


def export_notebook(notebook_id: str, profile: str, out_dir: Path,
                    spacing: float, force: bool, limit: int | None) -> dict:
    sources = list_sources(notebook_id, profile)
    if not sources:
        log(f"FATAL: no sources for notebook {notebook_id}")
        return {"notebook_id": notebook_id, "exported": 0, "skipped": 0, "failed": 0, "errors": ["no sources"]}

    log(f"Found {len(sources)} sources in notebook {notebook_id}")
    if limit:
        sources = sources[:limit]
        log(f"  --limit {limit}: processing first {len(sources)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    exported = skipped = failed = 0
    errors: list[str] = []
    for i, src in enumerate(sources, 1):
        sid = src.get("id")
        if not sid:
            log(f"  [{i}/{len(sources)}] SKIP (no id): {src.get('title', '')[:60]}")
            failed += 1
            continue
        out_path = out_dir / f"{sid}.md"
        if out_path.exists() and not force:
            skipped += 1
            if i % 25 == 0 or i == len(sources):
                log(f"  [{i}/{len(sources)}] skip (exists): {sid[:12]}  (exported={exported} skipped={skipped})")
            continue
        title = (src.get("title") or "")[:50]
        log(f"  [{i}/{len(sources)}] export {sid[:12]} ({title})")
        content, err = fetch_content(sid, profile)
        if not content:
            # yt-dlp fallback for sources NotebookLM failed to index (status=3).
            # Recovers the video ID from URL-shaped titles; fetches auto-captions.
            log(f"    nlm failed ({err[:80]}); trying yt-dlp fallback...")
            content, ytdlp_err = fetch_via_ytdlp(src)
            if content:
                log(f"    yt-dlp recovered ({len(content)} chars)")
            else:
                failed += 1
                errors.append(f"{sid}: nlm={err}; ytdlp={ytdlp_err}")
                log(f"    FAIL (both): {ytdlp_err[:120]}")
                time.sleep(spacing)
                continue
        atomic_write(out_path, build_transcript_md(src, notebook_id, content))
        exported += 1
        time.sleep(spacing)

    log(f"Done: exported={exported} skipped={skipped} failed={failed}")
    return {
        "notebook_id": notebook_id,
        "source_count": len(sources),
        "exported": exported,
        "skipped": skipped,
        "failed": failed,
        "transcripts_dir": str(out_dir),
        "errors": errors[:20],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--notebook", required=True)
    ap.add_argument("--profile", default="codex")
    ap.add_argument("--out", type=Path, default=Path("P:/.data/wiki/sources/transcripts"))
    ap.add_argument("--spacing", type=float, default=1.5, help="seconds between source content calls")
    ap.add_argument("--force", action="store_true", help="re-export even if transcript file exists")
    ap.add_argument("--limit", type=int, default=None, help="export only first N sources (testing)")
    args = ap.parse_args()

    result = export_notebook(args.notebook, args.profile, args.out,
                             args.spacing, args.force, args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["failed"] == 0 else 5


if __name__ == "__main__":
    sys.exit(main())
