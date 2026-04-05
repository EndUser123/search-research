"""Main entry point for yt-fts package.

This enables `python -m yt_fts` to work as an alternative to:
- `python -m yt_fts.core.cli`
- `python yt-fts.py`
- `yt-fts` (after pip install)
"""

if __name__ == "__main__":
    from .core.cli import cli
    cli()
