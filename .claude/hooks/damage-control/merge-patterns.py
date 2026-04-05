#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["pyyaml"]
# ///
"""
Merge Damage Control pattern files.

- patterns.upstream.yaml: upstream snapshot
- patterns.overlay.yaml: CSF/Windows additions
- patterns.yaml: active patterns (default base)
- Use --base patterns.upstream.yaml to regenerate from upstream
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

DEFAULT_BASE = Path(__file__).with_name("patterns.yaml")
UPSTREAM_BASE = Path(__file__).with_name("patterns.upstream.yaml")
DEFAULT_OVERLAY = Path(__file__).with_name("patterns.overlay.yaml")
DEFAULT_OUT = Path(__file__).with_name("patterns.yaml")
MERGE_KEYS = ("bashToolPatterns", "zeroAccessPaths", "readOnlyPaths", "noDeletePaths")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def item_key(item: Any) -> str:
    if isinstance(item, dict):
        if "pattern" in item:
            return f"pattern:{item['pattern']}"
        return "dict:" + json.dumps(item, sort_keys=True)
    return f"value:{item}"


def merge_list(base_list: list[Any], overlay_list: list[Any]) -> list[Any]:
    merged: list[Any] = []
    seen: set[str] = set()
    for item in base_list + overlay_list:
        key = item_key(item)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def merge_patterns(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key in MERGE_KEYS:
        base_list = merged.get(key, [])
        overlay_list = overlay.get(key, [])
        # Always merge - preserve base_list even if overlay_list is empty/missing
        if not isinstance(base_list, list):
            base_list = []
        if not isinstance(overlay_list, list):
            overlay_list = []
        merged[key] = merge_list(base_list, overlay_list)
    for key, value in overlay.items():
        if key in MERGE_KEYS:
            continue
        merged[key] = value
    return merged


def check_out_of_date(out_path: Path, merged: dict[str, Any]) -> bool:
    if not out_path.exists():
        return True
    existing = load_yaml(out_path)
    return existing != merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge damage-control patterns.")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE, help="Base patterns file")
    parser.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY, help="Overlay patterns file")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output patterns file")
    parser.add_argument("--write", action="store_true", help="Write merged patterns to --out")
    parser.add_argument("--check", action="store_true", help="Check whether --out matches merge result")
    args = parser.parse_args()

    if args.write and args.base == args.out:
        print("Refusing to overwrite output from itself. Use --base patterns.upstream.yaml to regenerate.")
        return 2

    base = load_yaml(args.base)
    overlay = load_yaml(args.overlay)
    merged = merge_patterns(base, overlay)

    if args.check:
        if check_out_of_date(args.out, merged):
            print("OUT OF DATE: patterns file does not match base + overlay")
            return 2
        print("OK: patterns file matches base + overlay")
        return 0

    if args.write:
        with args.out.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(merged, handle, sort_keys=False, default_flow_style=False, allow_unicode=True)
        print(f"Wrote merged patterns to {args.out}")
        return 0

    print("Dry run only. Use --write to update patterns.yaml or --check to verify.")
    print(f"Base: {args.base}")
    print(f"Upstream: {UPSTREAM_BASE}")
    print(f"Overlay: {args.overlay}")
    print(f"Output: {args.out}")
    for key in MERGE_KEYS:
        print(f"{key}: {len(merged.get(key, []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
