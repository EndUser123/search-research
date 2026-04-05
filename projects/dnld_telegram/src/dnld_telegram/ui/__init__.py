"""
UI module for different display types
"""

from .base import BaseUIDisplay, ConcurrentDownloadMixin, UIConfig

# Auto-register all available displays
from .factory import UIFactory, auto_register_displays

auto_register_displays()

# Dynamically build __all__ based on successfully imported displays


__all__ = [
    "BaseUIDisplay",
    "ConcurrentDownloadMixin",
    "UIFactory",
    "UIConfig",
]
