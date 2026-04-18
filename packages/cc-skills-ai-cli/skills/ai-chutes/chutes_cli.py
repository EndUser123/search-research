#!/usr/bin/env python3
"""Chutes CLI entry point - can be run directly."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from cli import main

if __name__ == "__main__":
    sys.exit(main())
