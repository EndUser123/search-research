#!/usr/bin/env python3
"""
monitor_cks_effectiveness.py - DEPRECATED

This script previously measured phantom CKS metadata fields (work_type,
claude_code_auto_immediate) that were never written to the CKS DB.
It always reported 0% and provided no useful signal.

Redirects to monitor_hook_outcomes.py which measures actual behavioral
outcomes from principle-events.jsonl.
"""

import subprocess
import sys
from pathlib import Path

REPLACEMENT = Path(__file__).parent / "monitor_hook_outcomes.py"

if __name__ == "__main__":
    result = subprocess.run([sys.executable, str(REPLACEMENT)] + sys.argv[1:])
    sys.exit(result.returncode)
