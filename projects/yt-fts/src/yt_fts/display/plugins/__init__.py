"""
Built-in display plugins for yt-fts.

This package contains the default plugin implementations
that ship with yt-fts.
"""
from __future__ import annotations

from .compact import CompactDisplayPlugin
from .default import DefaultDisplayPlugin
from .json_output import JsonOutputPlugin

__all__ = [
    "CompactDisplayPlugin",
    "DefaultDisplayPlugin",
    "JsonOutputPlugin",
]
