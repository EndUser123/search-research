#!/usr/bin/env python3
"""Fix syntax error in PreToolUse_path_validator.py"""

from pathlib import Path

file_path = Path("P:/.claude/hooks/PreToolUse_path_validator.py")
content = file_path.read_text(encoding='utf-8')

# The broken section - f-string split across lines incorrectly
old_broken = '''                "message": (
                    f"⚠️ SENSITIVE FILE: {canonical_path}
"
                    "This file is protected. To proceed, reply exactly:
"
                    f"approve edit {relative_hint}"
                ),'''

# The fixed version - proper f-string with escaped newlines
new_fixed = '''                "message": (
                    f"⚠️ SENSITIVE FILE: {canonical_path}\\n"
                    "This file is protected. To proceed, reply exactly:\\n"
                    f"approve edit {relative_hint}"
                ),'''

# Also need to fix the broken f-string at line 283-284
old_broken2 = '''            "message": f"Path Security Violation: {violation}
Path: {file_path}"'''

new_fixed2 = '''            "message": f"Path Security Violation: {violation}\\nPath: {file_path}"'''

if old_broken in content:
    content = content.replace(old_broken, new_fixed)
    print("✅ Fixed first f-string")
else:
    print("⚠️  First f-string pattern not found (may already be fixed)")

if old_broken2 in content:
    content = content.replace(old_broken2, new_fixed2)
    print("✅ Fixed second f-string")
else:
    print("⚠️  Second f-string pattern not found (may already be fixed)")

file_path.write_text(content, encoding='utf-8')
print("✅ File updated successfully")
