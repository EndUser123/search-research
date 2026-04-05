#!/usr/bin/env python
"""
iCHS - The Intelligent Code Health System
Main executable entrypoint.
"""

import asyncio

if __name__ == "__main__":
    from ichs import cli

    asyncio.run(cli.main())
