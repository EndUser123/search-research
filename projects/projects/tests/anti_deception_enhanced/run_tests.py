#!/usr/bin/env python3
"""
Enhanced Anti-Deception Architecture Test Suite Runner
=======================================================

Quick entry point for running the comprehensive test suite.
Usage:
    python run_tests.py [--suite all|unit|integration|performance|scenario]
"""

import os
import sys

# Add test_utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "test_utils"))

from test_runner import main

if __name__ == "__main__":
    main()
