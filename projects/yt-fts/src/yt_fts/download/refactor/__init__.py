"""
Refactoring infrastructure for yt-fts.

This module provides tools and scripts for safe, incremental refactoring:
- LibCST: Format-preserving AST transformations
- Rope: Semantic validation and safe refactoring
- Semgrep: Pattern-based verification and progress tracking

Layers:
1. Add config dataclasses
2. Update constructor signature
3. Migrate call sites
4. Cleanup old signature
"""
from __future__ import annotations

__all__ = []
