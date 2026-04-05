"""
TUI display components for YouTube Sync.

This module provides backward compatibility by re-exporting components
from the refactored tui package.
"""

# Import from the tui package using absolute imports for compatibility
from tui import (
    EnhancedChannelTree,
    EnhancedLogStore,
    EnhancedProgressDisplay,
    PerformanceTracker,
    ProfessionalTUIDisplay,
    SessionOverview,
    TUIDisplay,
    setup_tui_logging,
)

__all__ = [
    "PerformanceTracker",
    "EnhancedLogStore",
    "EnhancedProgressDisplay",
    "EnhancedChannelTree",
    "SessionOverview",
    "ProfessionalTUIDisplay",
    "TUIDisplay",
    "setup_tui_logging",
]
