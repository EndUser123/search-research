#!/usr/bin/env python3
"""
Main entry point for log_chunker when run as a module.
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add src directory to path for proper package resolution
    src_dir = Path(__file__).parent.parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from log_chunker.log_chunker import main

    main()
