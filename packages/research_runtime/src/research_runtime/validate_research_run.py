"""CLI entrypoint for validating research-run.v1 artifacts.

Supports direct script execution and `python -m research_runtime.validate_research_run`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from research_runtime.validator import ValidationError, validate_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a research-run.v1 artifact")
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    try:
        validate_file(args.artifact)
    except ValidationError as exc:
        for error in exc.errors:
            print(f"ERROR: {error}")
        return 1
    print(f"VALID: {args.artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
