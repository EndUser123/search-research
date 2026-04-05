"""
Channel File Updater - Main Interface

This module provides the main ChannelFileUpdater interface that imports
the actual implementation from the services module. This maintains backward
compatibility while organizing the code properly.
"""
from __future__ import annotations

from rich.console import Console

# Import the actual implementation
from .channel_service import ChannelFileUpdater as _ChannelFileUpdaterImpl


class ChannelFileUpdater(_ChannelFileUpdaterImpl):
    """
    Channel File Updater - Main interface class.

    This class inherits from the actual implementation in services/channel_service.py
    to maintain backward compatibility while providing a clean interface.
    """

    def __init__(self, console: Console | None = None):
        """Initialize the ChannelFileUpdater with optional console."""
        super().__init__(console)

    # All methods are inherited from the parent class in services/channel_service.py
    # including:
    # - get_discovered_handle(original_input, channel_id=None)
    # - record_discovery(original_input, channel_id, discovered_handle, ...)
    # - update_channel_file(channel_id, channel_name, channel_url)
    # - add_channel_to_file(channel_input, channel_info)
    # - remove_channel_from_file(channel_input)
    # - display_optimization_stats()
    # - cleanup_cache()
    # - get_channel_mappings()
    # - verify_channel_in_database(channel_id)
