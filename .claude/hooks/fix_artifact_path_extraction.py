#!/usr/bin/env python3
"""Fix artifact path extraction regex pattern."""

# Read the file
with open(r"P:\.claude\hooks\StopHook_rca_contract.py") as f:
    content = f.read()

# Old pattern (without "on"/"from" support)
old_pattern = r'r"Read\\s+[`\\"\']([^`\\"\']+)[`\\"\']"  # Read `path`'

# New pattern (with optional "on"/"from")
new_pattern = r'r"Read\\s+(?:on\\s+)?(?:from\\s+)?[`\"\']([^`\\"\']+)[`\\"\']"  # Read `path` (with optional "on"/"from")'

# Replace the pattern
content = content.replace(old_pattern, new_pattern)

# Write back
with open(r"P:\.claude\hooks\StopHook_rca_contract.py", "w") as f:
    f.write(content)

print("Fixed artifact path extraction pattern")
