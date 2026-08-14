#!/usr/bin/env python3
"""Merge multiple history.jsonl files with deduplication by sessionId+uuid.

Usage:
    python -m search_research.core.chs.scripts.merge_history_jsonl \
        --output ~/.claude/history_merged.jsonl \
        --dedup-key sessionId,uuid \
        ~/.claude/history.jsonl \
        ~/.claude/history_from_k_sept_nov.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge history.jsonl files with deduplication")
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output path for merged file",
    )
    parser.add_argument(
        "--dedup-key",
        type=str,
        default="sessionId,uuid",
        help="Comma-separated fields for deduplication (default: sessionId,uuid)",
    )
    parser.add_argument(
        "input_files",
        type=str,
        nargs="+",
        help="Input JSONL files to merge",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    dedup_fields = args.dedup_key.split(",")
    logger.info(f"Deduplication key: {dedup_fields}")
    logger.info(f"Input files: {args.input_files}")

    seen_keys: set[tuple] = set()
    output_path = Path(args.output).expanduser()
    output_count = 0
    total_input = 0
    duplicates = 0

    # Process each input file
    for input_path_str in args.input_files:
        input_path = Path(input_path_str).expanduser()
        if not input_path.exists():
            logger.warning(f"File not found, skipping: {input_path}")
            continue

        file_count = 0
        logger.info(f"Processing: {input_path}")

        with open(input_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                total_input += 1

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON line, skipping")
                    continue

                # Build dedup key tuple
                key_values = []
                for field in dedup_fields:
                    value = entry.get(field, "")
                    key_values.append(str(value) if value is not None else "")
                key = tuple(key_values)

                if key in seen_keys:
                    duplicates += 1
                    continue

                seen_keys.add(key)
                file_count += 1

                # Write to output
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "a", encoding="utf-8") as out:
                    out.write(line + "\n")

        logger.info(f"  Added {file_count} entries from {input_path.name}")
        output_count += file_count

    logger.info("\n=== Merge Summary ===")
    logger.info(f"Total input entries: {total_input:,}")
    logger.info(f"Duplicates skipped: {duplicates:,}")
    logger.info(f"Unique entries written: {output_count:,}")
    logger.info(f"Output: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
