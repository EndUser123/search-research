#!/usr/bin/env python3
"""Prepend the tracked IIFE onto the sidepanel bundle (byte-level, encoding-safe).

Called by re-apply-patches.ps1 for Patch 3 (sidepanel).
PowerShell's ReadAllText corrupts non-UTF-8 byte sequences in the 13MB minified
bundle; this script operates on raw bytes to avoid that.

Usage: python prepend_iife.py <sidepanel.js> <iife.js>
Exit codes: 0 = success, 1 = error
"""
import sys
from pathlib import Path

IIFE_END_MARKER = b'}catch(e){console.error("ACP UI injection failed:",e)}'
IIFE_START = b"try{(function(){"


def main():
    if len(sys.argv) != 3:
        print("Usage: prepend_iife.py <sidepanel.js> <iife.js>", file=sys.stderr)
        return 1

    sidepanel_path = Path(sys.argv[1])
    iife_path = Path(sys.argv[2])

    if not sidepanel_path.exists():
        print(f"SKIP: sidepanel not found: {sidepanel_path}", file=sys.stderr)
        return 0
    if not iife_path.exists():
        print(f"SKIP: IIFE not found: {iife_path}", file=sys.stderr)
        return 0

    sidepanel = sidepanel_path.read_bytes()
    iife = iife_path.read_bytes()

    # Strip old IIFE if present (idempotent re-apply)
    base = sidepanel
    if sidepanel[:len(IIFE_START)] == IIFE_START:
        marker_pos = sidepanel.find(IIFE_END_MARKER)
        if marker_pos >= 0:
            after = marker_pos + len(IIFE_END_MARKER)
            # Skip separator newlines
            while after < len(sidepanel) and sidepanel[after:after+1] in (b"\n", b"\r"):
                after += 1
            base = sidepanel[after:]

    # Prepend tracked IIFE + separator + base
    patched = iife + b"\n\n" + base
    sidepanel_path.write_bytes(patched)

    print(f"OK: sidepanel patched (IIFE {len(iife)}B prepended, "
          f"base {len(base)}B, total {len(patched)}B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
