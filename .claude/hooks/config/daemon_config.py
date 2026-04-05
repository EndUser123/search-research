"""
Daemon configuration for two-daemon architecture.

This module provides configuration for separate dreaming and search daemons
with distinct mutex names, PID files, and state management.

The two-daemon architecture allows Claude Code to run specialized background
processes concurrently without interference:
- Dreaming daemon: Handles insight generation and reflection tasks
- Search daemon: Manages search operations and indexing

Each daemon has exclusive system resources (named mutex) and maintains
separate state files to prevent conflicts.
"""

from typing import Dict, Literal

# Type alias for supported daemon types
DaemonType = Literal["dreaming", "search"]

# Daemon type configurations
DAEMON_TYPES: Dict[DaemonType, Dict[str, str]] = {
    "dreaming": {
        "mutex_name": "Global\\ClaudeInsightDaemon",
        "pid_file": "dreaming-daemon.pid",
        "state_file": "dreaming-daemon-state.json",
        "daemon_log": "dreaming-daemon.log",
    },
    "search": {
        "mutex_name": "Global\\ClaudeSearchDaemon",
        "pid_file": "search-daemon.pid",
        "state_file": "search-daemon-state.json",
        "daemon_log": "search-daemon.log",
    },
}


def get_daemon_config(daemon_type: DaemonType) -> Dict[str, str]:
    """
    Retrieve configuration for a specific daemon type.

    This function returns a copy of the configuration dictionary to prevent
    accidental modification of the global DAEMON_TYPES constant. The returned
    configuration contains all necessary file paths and system identifiers
    for daemon operation.

    Args:
        daemon_type: The type of daemon ('dreaming' or 'search').
            Use 'dreaming' for insight/reflection tasks.
            Use 'search' for search/indexing operations.

    Returns:
        A dictionary containing daemon configuration with the following keys:
            - mutex_name: Windows named mutex for daemon exclusivity (prevents
              multiple instances of the same daemon type)
            - pid_file: Filename to store the daemon's process ID
            - state_file: Filename to store daemon state and runtime data
            - daemon_log: Filename for daemon logging output

    Raises:
        ValueError: If daemon_type is not 'dreaming' or 'search'.

    Example:
        >>> config = get_daemon_config('dreaming')
        >>> print(config['mutex_name'])
        'Global\\ClaudeInsightDaemon'
        >>> print(config['pid_file'])
        'dreaming-daemon.pid'

    Note:
        The returned dictionary is a copy, so modifications to it will not
        affect the global DAEMON_TYPES configuration.
    """
    if daemon_type not in DAEMON_TYPES:
        valid_types = ", ".join(f"'{dt}'" for dt in DAEMON_TYPES.keys())
        raise ValueError(
            f"Unknown daemon type: '{daemon_type}'. "
            f"Valid types are: {valid_types}"
        )

    return DAEMON_TYPES[daemon_type].copy()
