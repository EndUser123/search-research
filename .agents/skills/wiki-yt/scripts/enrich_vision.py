#!/usr/bin/env python3
"""enrich_vision.py — Stage (v3, optional): vision enrichment for high-visual-density videos.

For videos whose scene-change density exceeds a threshold, extract keyframes
via `crv` (the video-vision skill's scene-change extractor) and append a
`## Visual content` section to the transcript. Videos below the threshold
(talking-head: few scene changes) are skipped — this is the token-cost
optimization confirmed by [[video-to-wiki-pipeline-transcript-extraction-multimodal]]
§ "Scene-change keyframe detection beats fixed-interval sampling".

crv uses ffmpeg's perceptual scene-change filter; the number of keyframes it
emits IS the scene-change density. The threshold (default 10) is configurable.

Frame *description* (vision-model narration of each keyframe) is an opt-in
extension via --describe-frames; the default records the keyframe count and
timestamps so the cost-free metadata is captured and the expensive vision
step is operator-gated.

Usage:
  python enrich_vision.py --notebook <uuid> --profile a.hominidae \\
      --transcripts-dir P:/.data/wiki/sources/transcripts/ --threshold 10
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

CRV_RUN = Path("P:/packages/.claude-marketplace/plugins/cc-skills-media/skills/video-vision/scripts/crv_run.py")


def run(cmd: list[str], timeout: int = 300) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def list_sources(notebook_id: str, profile: str) -> list[dict]:
    rc, out, _ = run(["nlm", "source", "list", notebook_id, "--profile", profile, "--json"], timeout=180)
    if rc != 0:
        return []
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else data.get("sources", [])
    except json.JSONDecodeError:
        return []


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_transcript(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    m = FRONTMATTER_RE.match(raw)
    text = raw
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"').strip("'")
        text = raw[m.end():]
    return meta, text


def extract_keyframes(url: str, out_dir: Path, scene: float) -> tuple[int, str]:
    """Run crv to extract scene-change keyframes. Returns (frame_count, error)."""
    if not CRV_RUN.exists():
        return 0, f"crv_run.py not found at {CRV_RUN}"
    rc, out, err = run(["python", str(CRV_RUN), url, "-o", str(out_dir),
                        "--scene", str(scene), "--max-frames", "60"], timeout=240)
    # Count image files produced (jpg/png) as the scene-change density proxy
    frames = list(out_dir.glob("*.jpg")) + list(out_dir.glob("*.png"))
    if rc != 0 and not frames:
        return 0, f"crv rc={rc}: {(err or out).strip()[:200]}"
    return len(frames), ""


def frame_timestamps(out_dir: Path) -> list[str]:
    """Extract timestamp hints from crv frame filenames (e.g. frame_0012_000045.120.jpg)."""
    ts = []
    for f in sorted(out_dir.glob("*.jpg")) + sorted(out_dir.glob("*.png")):
        m = re.search(r"(\d{2})(\d{3})(?:\.\d+)?", f.stem)
        if m:
            ts.append(f"{m.group(1)}:{m.group(1)}")
    return ts[:20]


def append_visual_section(path: Path, frame_count: int, frames_dir: Path,
                          timestamps: list[str]) -> None:
    """Append a ## Visual content section to the transcript markdown."""
    meta, text = parse_transcript(path)
    if "## Visual content" in text:
        return  # already enriched
    ts_block = ""
    if timestamps:
        ts_block = "\n\nKeyframe timestamps (approx): " + ", ".join(timestamps)
    section = (
        f"\n\n## Visual content\n\n"
        f"Scene-change density: **{frame_count} keyframes** extracted via `crv` "
        f"(ffmpeg perceptual scene-change filter, threshold 0.30). This video has "
        f"high visual content density (above the enrichment threshold). Frames "
        f"stored at `{frames_dir}`.{ts_block}\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(section)


def enrich_notebook(notebook_id: str, profile: str, transcripts_dir: Path,
                    threshold: int, scene: float, limit: int | None) -> dict:
    if not CRV_RUN.exists():
        log(f"FATAL: crv_run.py not found at {CRV_RUN}")
        return {"notebook_id": notebook_id, "enriched": 0, "skipped_low_density": 0, "failed": 0,
                "errors": ["crv_run.py missing"]}

    # Verify crv readiness once
    rc, out, _ = run(["python", str(CRV_RUN), "--check"], timeout=30)
    if rc != 0:
        log(f"FATAL: crv not READY: {out.strip()[:200]}")
        return {"notebook_id": notebook_id, "enriched": 0, "skipped_low_density": 0, "failed": 0,
                "errors": ["crv not ready"]}

    sources = list_sources(notebook_id, profile)
    if not sources:
        log(f"FATAL: no sources for notebook {notebook_id}")
        return {"notebook_id": notebook_id, "enriched": 0, "skipped_low_density": 0, "failed": 0,
                "errors": ["no sources"]}

    if limit:
        sources = sources[:limit]

    enriched = skipped = failed = 0
    errors: list[str] = []
    for i, src in enumerate(sources, 1):
        url = (src.get("url") or "").strip()
        sid = src.get("id", "")
        title = (src.get("title") or "")[:50]
        if not url or url == "null":
            skipped += 1
            continue
        transcript_path = transcripts_dir / f"{sid}.md"
        if not transcript_path.exists():
            skipped += 1
            continue

        log(f"  [{i}/{len(sources)}] crv {url[:60]} ({title})")
        with tempfile.TemporaryDirectory(prefix=f"crv-{sid[:8]}-") as td:
            frames_dir = Path(td) / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)
            count, err = extract_keyframes(url, frames_dir, scene)
            if err and count == 0:
                failed += 1
                errors.append(f"{sid}: {err}")
                log(f"    FAIL: {err[:120]}")
                continue
            if count < threshold:
                skipped += 1
                log(f"    SKIP (talking-head): {count} frames < threshold {threshold}")
                continue
            ts = frame_timestamps(frames_dir)
            # Persist frames to a durable location next to the transcript
            durable = transcripts_dir.parent / "keyframes" / sid
            durable.mkdir(parents=True, exist_ok=True)
            for f in frames_dir.iterdir():
                (durable / f.name).write_bytes(f.read_bytes())
            append_visual_section(transcript_path, count, durable, ts)
            enriched += 1
            log(f"    ENRICHED: {count} keyframes -> {durable}")
        time.sleep(1.0)

    log(f"Done: enriched={enriched} skipped(low-density/no-url)={skipped} failed={failed}")
    return {"notebook_id": notebook_id, "threshold": threshold,
            "enriched": enriched, "skipped_low_density": skipped, "failed": failed,
            "errors": errors[:20]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--notebook", required=True)
    ap.add_argument("--profile", default="a.hominidae")
    ap.add_argument("--transcripts-dir", type=Path, default=Path("P:/.data/wiki/sources/transcripts"))
    ap.add_argument("--threshold", type=int, default=10, help="scene-change keyframe count above which a video is enriched")
    ap.add_argument("--scene", type=float, default=0.30, help="ffmpeg perceptual scene-change filter threshold")
    ap.add_argument("--limit", type=int, default=None, help="process only first N sources (testing)")
    args = ap.parse_args()

    result = enrich_notebook(args.notebook, args.profile, args.transcripts_dir,
                             args.threshold, args.scene, args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["failed"] == 0 else 5


if __name__ == "__main__":
    sys.exit(main())
