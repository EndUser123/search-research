#!/usr/bin/env python3
"""
iCHS - The Intelligent Code Health System
Main entry point for the application
"""

import asyncio

from ichs.cli import main as cli_main

if __name__ == "__main__":
    asyncio.run(cli_main())
