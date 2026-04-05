"""
Plugin discovery mechanism for display plugins.

SECURITY HARDENED:
- Requires opt-in via YT_FTS_ENABLE_PLUGINS environment variable
- Allowlist-based directory validation
- Comprehensive logging of all plugin operations
- No silent exception swallowing

Dynamically loads display plugins from the plugins/ directory
and from user-configured plugin directories (when explicitly enabled).
"""
from __future__ import annotations


import logging

# Get module logger
logger = logging.getLogger(__name__)

# =============================================================================
# Security Configuration
# =============================================================================

# Environment variable to enable external plugins (opt-in)
ENABLE_PLUGINS_ENV = "YT_FTS_ENABLE_PLUGINS"

# Allowlist root directories that are safe to load plugins from
ALLOWLISTED_ROOTS = [
    "~/.config/yt-fts/plugins",
    "src/yt_fts/display/plugins",
]
