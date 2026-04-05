#!/usr/bin/env python3
"""
Skills package root - makes skills/ a valid Python package.

All individual skills are subdirectories under this package.
"""

# Import debugRCA as debugrca for lowercase import compatibility
import sys
from importlib import import_module

# Create lowercase alias for debugRCA module
try:
    if "debugRCA" not in sys.modules:
        _debugRCA = import_module("debugRCA")
    else:
        _debugRCA = sys.modules["debugRCA"]
    sys.modules["debugrca"] = _debugRCA
except ImportError:
    pass
