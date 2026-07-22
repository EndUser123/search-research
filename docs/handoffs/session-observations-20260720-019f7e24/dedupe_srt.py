#!/usr/bin/env python3
"""De-duplicate YouTube's karaoke-style auto-caption SRT into clean prose.

YouTube's auto-captions typically emit each spoken span twice: once as the
'tail' of one cue and again as the 'head' of the next. This script collapses
those overlaps and writes a clean plain-text transcript.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def parse_srt(path: Path) -> list[str]:
    """Return list of cue text blocks (each may contain multiple lines)."""
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    # Split on blank line between cues
    blocks = re.split(r"\r?\n\r?\n+", raw.strip())
    cues: list[str] = []
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        # Drop the numeric index (first line) and the timecode line
        # Find the timecode line (contains '-->')
        text_lines = []
        seen_timecode = False
        for ln in lines:
            if "-->" in ln:
                seen_timecode = True
                continue
            if not seen_timecode:
                # Could be the index number
                continue
            text_lines.append(ln)
        if text_lines:
            cues.append(" ".join(text_lines))
    return cues


def dedupe_karaoke(cues: list[str]) -> str:
    """Collapse cues where each cue's leading text equals the prior cue's tail."""
    out_parts: list[str] = []
    prev = ""
    for cue in cues:
        cur = re.sub(r"\s+", " ", cue).strip()
        if not cur:
            continue
        if prev and cur.lower().startswith(prev.lower()):
            # Strip the duplicated prefix; keep only the new tail
            tail = cur[len(prev):].strip()
            if tail:
                out_parts.append(tail)
                prev = tail
            # else: pure duplicate of previous -> skip
            continue
        # Check if cur is a strict substring/whitespace-suffix of prev (full dup)
        if prev and cur.lower() == prev.lower():
            continue
        out_parts.append(cur)
        prev = cur
    text = " ".join(out_parts)
    # Collapse double spaces introduced by joins
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: dedupe_srt.py <in.srt> [out.txt]", file=sys.stderr)
        return 2
    src = Path(argv[1])
    dst = Path(argv[2]) if len(argv) > 2 else src.with_suffix(".clean.txt")
    cues = parse_srt(src)
    text = dedupe_karaoke(cues)
    dst.write_text(text, encoding="utf-8")
    print(f"wrote {len(text)} chars to {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
