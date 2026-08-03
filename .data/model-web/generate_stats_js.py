#!/usr/bin/env python3
"""Generate model-stats.js (JSONP) from model-stats.json source of truth.

Usage: python generate_stats_js.py
Reads:  P:/.data/model-web/model-stats.json
Writes: ~/.grok/skills/model-web/model-stats.js

The launcher.html loads model-stats.js via <script> tag (relative path,
same directory — no CORS issue with file:// protocol).
"""
import json
from pathlib import Path

SOURCE = Path("P:/.data/model-web/model-stats.json")
DEST = Path.home() / ".grok" / "skills" / "model-web" / "model-stats.js"

def main():
    if not SOURCE.exists():
        print(f"Source not found: {SOURCE}")
        return 1

    stats = json.loads(SOURCE.read_text(encoding="utf-8"))

    # JSONP: window.MODEL_STATS = {...};
    js_content = f"window.MODEL_STATS = {json.dumps(stats, indent=2)};\n"
    DEST.write_text(js_content, encoding="utf-8")
    print(f"Generated {DEST} ({len(stats)} models)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
