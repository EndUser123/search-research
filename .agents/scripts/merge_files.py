#!/usr/bin/env python3
"""Merge files into a single temp file for cross-model specialist dispatch.

When dispatching to a CLI-based model (agy, codex, mmx), each tool-call
round-trip counts as an API request against quota. Merging N files into
1 temp file reduces the cost from N reads to 1 read — measured 9x quota
reduction on agy (15.6% → 1.6% per run).

Usage:
    python merge_files.py <output_path> <input_path1> <input_path2> ...
    python merge_files.py P:/tmp/merged-source.py path/a.py path/b.py path/c.py

Each file is prefixed with a header:
    === FILE: <relative_or_absolute_path> ===

Exit codes:
    0 = success
    1 = no input files provided
    2 = input file not found
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def merge_files(output_path: str, input_paths: list[str]) -> str:
    """Merge input files into output_path with section headers.

    Args:
        output_path: where to write the merged file
        input_paths: list of file paths to merge

    Returns:
        The output_path (for chaining)

    Raises:
        FileNotFoundError: if any input file doesn't exist
    """
    parts: list[str] = []

    for input_path in input_paths:
        p = Path(input_path)
        if not p.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        content = p.read_text(encoding="utf-8")
        parts.append(f"=== FILE: {input_path} ===\n{content}")

    merged = "\n\n".join(parts)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(merged, encoding="utf-8")

    return output_path


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "Usage: python merge_files.py <output_path> <input_path1> <input_path2> ...",
            file=sys.stderr,
        )
        return 1

    output_path = sys.argv[1]
    input_paths = sys.argv[2:]

    # Validate all inputs exist before writing anything
    for ip in input_paths:
        if not Path(ip).exists():
            print(f"Error: input file not found: {ip}", file=sys.stderr)
            return 2

    try:
        result = merge_files(output_path, input_paths)
        size = Path(result).stat().st_size
        print(f"Merged {len(input_paths)} files -> {result} ({size:,} bytes)")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
