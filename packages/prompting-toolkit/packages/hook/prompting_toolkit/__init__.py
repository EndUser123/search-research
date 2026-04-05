"""
Prompting Toolkit - Hook Package

Real-time prompt enhancement for Claude Code.
This package provides automatic prompt improvement with domain detection,
complexity analysis, and interactive choice UI.
"""

from __future__ import annotations

__version__ = "1.0.0"

# Import main enhancement module
# This module is compatible with both router-based and default Claude Code installations
try:
    from .enhancement import (
        ROUTER_AVAILABLE,
        process_prompt,
        prompt_enhancement_hook,
    )

    __all__ = [
        "process_prompt",
        "prompt_enhancement_hook",
        "ROUTER_AVAILABLE",
    ]
except ImportError:
    # If enhancement module is not available, package can still be imported
    # This allows graceful degradation
    __all__ = []

# Export configuration keys
ENABLED_KEY = "PROMPT_ENHANCEMENT_ENABLED"
DEBUG_KEY = "PROMPT_ENHANCEMENT_DEBUG"
CHOICE_ENABLED_KEY = "PROMPT_CHOICE_ENABLED"
