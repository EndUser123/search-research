#!/usr/bin/env python3
"""Analyze task file naming pattern."""
import hashlib
import datetime

# The session_id is a Unix timestamp
timestamp = 1766696561
print(f'Session timestamp: {datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)}')

# The second part fbb2a7be is 8 hex chars
# This looks like a hash, not 'fallback_1'
print(f'Terminal part from task file: fbb2a7be (8 chars = MD5 prefix)')

# Maybe terminal_id is being computed as hash(something)?
print(f'MD5 of "fallback_1": {hashlib.md5("fallback_1".encode()).hexdigest()[:8]}')
print(f'MD5 of "1766696561": {hashlib.md5("1766696561".encode()).hexdigest()[:8]}')
