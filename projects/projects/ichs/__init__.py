"""
iCHS - The Intelligent Code Health System

A Python-based tool for automating code quality checks, trend analysis, and intelligent diagnostics.
"""

__version__ = "2.0.0"
__author__ = "iCHS Development Team"
__description__ = "Intelligent Code Health System for automated code quality monitoring"

from . import autofix, config, database, diagnostics, parsers, reporting, runner, trends

__all__ = [
    "config",
    "runner",
    "database",
    "trends",
    "diagnostics",
    "autofix",
    "reporting",
    "parsers",
]
