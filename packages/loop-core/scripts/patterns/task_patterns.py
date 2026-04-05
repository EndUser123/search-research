"""Task detection regex patterns for plan parsing."""

import re

# Task detection patterns
TASK_PATTERN = re.compile(
    r'- \[([ xX])\][\s]+(.*?)(?:[\s]+#\s*(.+))?$',
    re.MULTILINE
)
"""Match markdown task items. Groups: checkbox (x/space), task text, tags/comment"""

TAG_PATTERN = re.compile(r'\[tag:([^\]]+)\]')
"""Match [tag:name] syntax in task text"""

DEPENDENCY_PATTERN = re.compile(r'after:([A-Z0-9\-]+)')
"""Match after:TASK-ID dependency syntax"""

TASK_ID_PREFIX_PATTERN = re.compile(r'^TASK-[0-9]+\s+')
"""Match task ID prefix like TASK-001 at the start of text"""
