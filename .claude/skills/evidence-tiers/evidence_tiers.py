#!/usr/bin/env python3
"""
evidence_tiers.py - Evidence Tiers Reference

Executable wrapper for the /evidence-tiers skill.
Returns proper dict format for StopRouter.
"""

import json
import sys
from pathlib import Path

def main():
    """Return evidence tiers as dict format."""
    skill_file = Path(__file__).parent / "SKILL.md"

    result = {
        "statusLine": "📋 Evidence Tiers loaded",
        "internalPrompt": skill_file.read_text(encoding='utf-8') if skill_file.exists() else "# Evidence Tiers not found"
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
