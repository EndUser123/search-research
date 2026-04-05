#!/usr/bin/env python3
"""Quick test to verify is_symlink_creating_command behavior."""
import os
import sys

hooks_dir = os.path.dirname(os.path.abspath(__file__))
if hooks_dir not in sys.path:
    sys.path.insert(0, hooks_dir)

from deny_root_write import is_symlink_creating_command

test_cases = [
    ("ln /tmp /link", "ln without -s"),
    ("ln -s /tmp /link", "ln with -s"),
    ("sudo ln /tmp /link", "ln with sudo prefix"),
    ("echo link", "echo with link word"),
]

print("Testing is_symlink_creating_command:")
print("-" * 50)
for cmd, desc in test_cases:
    result = is_symlink_creating_command(cmd)
    print(f"{desc:30} | {cmd:30} | {result}")
