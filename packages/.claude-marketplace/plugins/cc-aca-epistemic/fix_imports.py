#!/usr/bin/env python3
"""Fix import ordering in migrated files.

Rules:
1. from __future__ imports must be first (after shebang/docstring)
2. hooks_resolver imports go after __future__ but before other imports
3. Plugin header goes after __future__ in hooks
"""
import re
from pathlib import Path

PLUGIN_ROOT = Path("P:/packages/cc-aca-epistemic")

def fix_file(fpath: Path) -> bool:
    content = fpath.read_text(encoding="utf-8")
    original = content
    
    # Check if file has the issue
    if "from __future__" not in content:
        return False
    
    lines = content.split("\n")
    
    # Find and extract __future__ imports
    future_lines = []
    other_lines = []
    in_docstring = False
    docstring_closed = False
    
    i = 0
    # Skip shebang
    if lines and lines[0].startswith("#!"):
        other_lines.append(lines[0])
        i = 1
    
    # Skip initial blank lines
    while i < len(lines) and lines[i].strip() == "":
        other_lines.append(lines[i])
        i += 1
    
    # Skip docstring (triple-quoted)
    if i < len(lines) and (lines[i].startswith('"""') or lines[i].startswith("'''")):
        quote = lines[i][:3]
        other_lines.append(lines[i])
        i += 1
        # Check if docstring is single-line
        if lines[i-1].strip().endswith(quote) and len(lines[i-1].strip()) > 3:
            pass  # single line docstring
        else:
            while i < len(lines):
                other_lines.append(lines[i])
                if quote in lines[i] and i > 0:  # not the opening line
                    break
                i += 1
            i += 1
    
    # Skip blank lines after docstring
    while i < len(lines) and lines[i].strip() == "":
        other_lines.append(lines[i])
        i += 1
    
    # Now collect remaining lines
    remaining = lines[i:]
    
    # Extract __future__ imports from ALL lines
    future_imports = []
    non_future = []
    for line in remaining:
        if line.strip().startswith("from __future__"):
            future_imports.append(line)
        else:
            non_future.append(line)
    
    if not future_imports:
        return False
    
    # Check if __future__ is already in the right place
    # (after docstring, before everything else including plugin header)
    text_after_doc = "\n".join(non_future)
    if "from __future__" not in text_after_doc:
        # Already fixed or not needed
        return False
    
    # Rebuild: other_lines has shebang + docstring
    # Insert __future__ right after them
    result = other_lines + future_imports + [""] + non_future
    
    new_content = "\n".join(result)
    if new_content != original:
        fpath.write_text(new_content, encoding="utf-8")
        return True
    return False

fixed = 0
for f in PLUGIN_ROOT.rglob("*.py"):
    if "migrate_epistemic" in f.name or "fix_imports" in f.name:
        continue
    if fix_file(f):
        print(f"  FIXED: {f.relative_to(PLUGIN_ROOT)}")
        fixed += 1

print(f"\nFixed {fixed} files")
