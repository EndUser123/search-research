#!/usr/bin/env python3
"""export_transcripts.py — Stage A (v3): export raw source transcripts from a notebook.

Replaces v2's extract.py (which triggered NotebookLM Report + Data-Table
synthesis). v3 exports the *primary* content: the raw transcript of each
source via the YTIS direct source-fulltext client. Transcripts are written to
`wiki/sources/transcripts/<source_id>.md` with provenance frontmatter, per
the wiki SCHEMA rule that sources/ holds verbatim material and concepts/
holds distilled synthesis.

The export primitive returns the raw indexed text of each source (the actual
transcript), not an LLM synthesis. See
[[video-to-wiki-pipeline-transcript-extraction-multimodal]] § "Export raw
transcripts, don't synthesize at the source".

Usage:
  python export_transcripts.py --notebook <uuid> --account-profile a.hominidae \\
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
from typing import Any

from ytis_nlm import (
    account_client,
    ensure_account_session,
    get_source_content,
    get_source_content_from_client,
    list_sources as list_canonical_sources,
    list_sources_from_client,
)


def run(cmd: list[str], timeout: int = 180) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True, file=sys.stderr)


def list_sources(notebook_id: str, profile: str, client: Any | None = None) -> list[dict]:
    """Return sources through the YTIS canonical direct client."""
    try:
        if client is not None:
            return list_sources_from_client(client, notebook_id)
        return list_canonical_sources(profile, notebook_id, worker_id="wiki-yt-export-list")
    except Exception as exc:
        log(f"  canonical source list failed: {str(exc)[:300]}")
        raise


def fetch_content(
    source_id: str,
    profile: str,
    notebook_id: str,
    client: Any | None = None,
) -> tuple[str, str]:
    """Fetch raw transcript for one source.

    Returns (content_text, error_message) through the package-owned direct
    client. The notebook ID is required by the direct API even though the
    legacy CLI accepted only a globally unique source ID.
    """
    try:
        if client is not None:
            content = get_source_content_from_client(client, notebook_id, source_id)
        else:
            content = get_source_content(
                profile,
                notebook_id,
                source_id,
                worker_id=f"wiki-yt-export-{source_id[:8]}",
            )
        if content.strip():
            return content, ""
        return "", "canonical source content was empty"
    except Exception as exc:
        marker = f"{type(exc).__name__}: {exc}".lower()
        if "autherror" in marker or "authentication" in marker or "not authenticated" in marker:
            raise RuntimeError(f"canonical account authentication failed: {exc}") from exc
        return "", f"canonical source content failed: {type(exc).__name__}: {str(exc)[:240]}"


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
        return "", "no video_id in title (title is descriptive, not a URL)"
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


def _export_notebook(notebook_id: str, profile: str, out_dir: Path,
                     spacing: float, force: bool, limit: int | None,
                     client: Any) -> dict:
    sources = list_sources(notebook_id, profile, client=client)
    if not sources:
        log(f"FATAL: no sources for notebook {notebook_id}")
        return {"notebook_id": notebook_id, "exported": 0, "skipped": 0, "failed": 0, "errors": ["no sources"]}

    log(f"Found {len(sources)} sources in notebook {notebook_id}")
    if limit:
        sources = sources[:limit]
        log(f"  --limit {limit}: processing first {len(sources)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    exported = skipped = failed = 0
    from_cache_count = 0
    errors: list[str] = []

    # Build yt-is title bridge once for forward-sync (skip NLM for cached transcripts)
    _forward_sync_bridge = None
    try:
        # Add the scripts directory to path for the forward-sync import
        _scripts_dir = Path(__file__).resolve().parent
        if str(_scripts_dir) not in sys.path:
            sys.path.insert(0, str(_scripts_dir))
        from yt_is_forward_sync import build_bridge_once, fetch_from_yt_is_cache
        log("Building yt-is title bridge for forward-sync...")
        _forward_sync_bridge = build_bridge_once()
        log(f"  bridge: {len(_forward_sync_bridge)} titles")
    except Exception as e:
        log(f"  forward-sync unavailable (fail-through to NLM): {e}")

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

        # Forward-sync: check yt-is cache before calling NotebookLM
        content = ""
        _from_cache = False
        if _forward_sync_bridge is not None:
            try:
                content, cache_vid = fetch_from_yt_is_cache(src, _forward_sync_bridge)
                if content:
                    from_cache_count += 1
                    _from_cache = True
                    if i % 25 == 0 or i <= 3:
                        log(f"    [cache] hit video_id={cache_vid} ({len(content)} chars)")
            except Exception:
                pass  # fail-through to NLM

        if not content:
            content, err = fetch_content(sid, profile, notebook_id, client=client)
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

        # Feed-forward: populate yt-is cache so future syncs skip this fetch
        fed_to_cache = False
        if _forward_sync_bridge is not None:
            try:
                from yt_is_forward_sync import _resolve_video_id
                vid = _resolve_video_id(src, _forward_sync_bridge)
                if vid:
                    from csf.cache import set_cached_transcript
                    set_cached_transcript(
                        vid, "en", "notebooklm", content,
                        metadata={"source": "wiki-yt:feed-forward",
                                  "nlm_source_id": sid,
                                  "title": src.get("title", "")},
                        bind_verified=True,
                    )
                    fed_to_cache = True
            except Exception:
                pass  # feed-forward is best-effort; never block the pipeline

        exported += 1
        if fed_to_cache and (i <= 3 or i % 25 == 0):
            log(f"    [feed] cached video_id={vid}")
        # Only rate-limit after NLM API calls — cache hits are instant SQLite reads
        if not _from_cache:
            time.sleep(spacing)

    log(f"Done: exported={exported} skipped={skipped} failed={failed} from_cache={from_cache_count}")
    return {
        "notebook_id": notebook_id,
        "source_count": len(sources),
        "exported": exported,
        "skipped": skipped,
        "failed": failed,
        "from_cache_count": from_cache_count,
        "transcripts_dir": str(out_dir),
        "errors": errors[:20],
    }


def export_notebook(notebook_id: str, profile: str, out_dir: Path,
                    spacing: float, force: bool, limit: int | None) -> dict:
    """Probe once, then reuse one canonical client for the whole export."""
    try:
        probe = ensure_account_session(profile, worker_id="wiki-yt-export-preflight")
    except Exception as exc:
        log(f"FATAL canonical auth probe failed for account '{profile}': {exc}")
        return {"notebook_id": notebook_id, "exported": 0, "skipped": 0,
                "failed": 0, "auth_failed": True, "errors": [str(exc)]}
    if not probe.ok:
        message = (
            f"canonical auth unavailable for account '{profile}': {probe.reason}; "
            "non-interactive durable repair was attempted"
        )
        log(f"FATAL {message}")
        return {"notebook_id": notebook_id, "exported": 0, "skipped": 0,
                "failed": 0, "auth_failed": True, "errors": [message]}

    try:
        with account_client(profile, worker_id=f"wiki-yt-export-{notebook_id[:8]}") as client:
            return _export_notebook(notebook_id, profile, out_dir, spacing, force, limit, client)
    except Exception as exc:
        message = f"canonical export client failed: {type(exc).__name__}: {str(exc)[:300]}"
        log(f"FATAL {message}")
        return {"notebook_id": notebook_id, "exported": 0, "skipped": 0,
                "failed": 0, "fatal_error": True, "errors": [message]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--notebook", required=True)
    ap.add_argument("--profile", "--account-profile", dest="profile", default="a.hominidae",
                    help="exact account identity (a.hominidae, troup.hominidae, or brsthomson)")
    ap.add_argument("--out", type=Path, default=Path("P:/.data/wiki/sources/transcripts"))
    ap.add_argument("--spacing", type=float, default=1.5, help="seconds between source content calls")
    ap.add_argument("--force", action="store_true", help="re-export even if transcript file exists")
    ap.add_argument("--limit", type=int, default=None, help="export only first N sources (testing)")
    args = ap.parse_args()

    result = export_notebook(args.notebook, args.profile, args.out,
                             args.spacing, args.force, args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("auth_failed") or result.get("fatal_error"):
        return 2
    return 0 if result["failed"] == 0 else 5


if __name__ == "__main__":
    sys.exit(main())
