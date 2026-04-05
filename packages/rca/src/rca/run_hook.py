#!/usr/bin/env python3
"""Compatibility shim to package-level hook launcher."""

from __future__ import annotations

import sys

from rca.hook_launcher import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
