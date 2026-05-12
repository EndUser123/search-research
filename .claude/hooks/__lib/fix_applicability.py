#!/usr/bin/env python3
"""Fix the corrupted epistemic_applicability.py"""

import re

# Read the broken file
with open('P:/.claude/hooks/__lib/epistemic_applicability.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Fix the wasn pattern - four apostrophes to one
# The pattern was: wasn[''\x27\xE2\x80\x99]t which has 4 apostrophes in a char class
# It should be: wasn['\x27\xE2\x80\x99]t (one straight apostrophe)
old_wasn = r"wasn[''\x27\xE2\x80\x99]t"
new_wasn = r"wasn['\x27\xE2\x80\x99]t"
content = content.replace(old_wasn, new_wasn)

# Fix 2: Fix the \. back to [:\s] in limitations?, deliverables?, files? patterns
# These were changed incorrectly
content = content.replace(r"limitations?\.\s*$", r"limitations?[:\s]\s*$")
content = content.replace(r"deliverables?\.\s*$", r"deliverables?[:\s]\s*$")
content = content.replace(r"files?\s+(?:modified|created|added)\.\s*$", r"files?[:\s]+(?:modified|created|added)[:\s]*$")

# Fix 3: Remove the garbage unindented line " that are quoting prior gate output"
lines = content.split('\n')
fixed_lines = []
for line in lines:
    stripped = line.strip()
    if stripped == "that are quoting prior gate output":
        continue  # skip garbage line
    fixed_lines.append(line)

content = '\n'.join(fixed_lines)

# Write the fixed file
with open('P:/.claude/hooks/__lib/epistemic_applicability.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File fixed successfully")

# Verify by trying to import
import sys
sys.path.insert(0, 'P:/.claude/hooks')
try:
    from __lib.epistemic_applicability import is_simple_epistemic_response, is_grounded_delivery_summary
    print("Import successful!")
    # Run self-test
    import subprocess
    result = subprocess.run(
        [sys.executable, 'P:/.claude/hooks/__lib/epistemic_applicability.py'],
        capture_output=True, text=True, cwd='P:/.claude/hooks'
    )
    print("Self-test output:")
    print(result.stdout)
    if result.stderr:
        print("Stderr:", result.stderr)
except Exception as e:
    print(f"Error: {e}")