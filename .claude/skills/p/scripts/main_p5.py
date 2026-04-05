#!/usr/bin/env python
"""P5 Main Entry Point - Production Certification.

This is the main entry point for P5 certification phase.
Can be invoked as: python -m p5 or python P:/.claude/skills/p/scripts/main_p5.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scripts.certify import main as certify_main


if __name__ == "__main__":
    sys.exit(certify_main())
