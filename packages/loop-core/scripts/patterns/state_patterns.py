"""State file naming patterns for loop state management."""

import re

STATE_FILE_PATTERN = re.compile(r'^loop_state\.json$')
"""Match loop state file names"""

LOCK_FILE_PATTERN = re.compile(r'^(.+)\.lock$')
"""Match lock file names and extract base name"""
