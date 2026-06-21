#!/usr/bin/env python3
"""Delegates to cc-aca-epistemic plugin."""
import sys
sys.path.insert(0, "P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib")
from compat_loader import delegate

if __name__ == "__main__":
    delegate(__file__)
