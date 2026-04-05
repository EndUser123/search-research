#!/usr/bin/env python3
"""
Stage 1: Syntax Validation

Multi-language validation routing based on file extension.
Supports: Python (.py), Markdown (.md), YAML (.yaml, .yml)

Usage:
    python stage1_syntax.py file1.py file2.md ...
    python stage1_syntax.py "file1.py,file2.py"

Exit codes:
    0 - All files valid
    1 - Syntax errors found
"""

import ast
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def validate_python(target: Path) -> bool:
    """Validate Python syntax using AST parser."""
    try:
        with open(target) as f:
            ast.parse(f.read())
        print(f'  ✅ Valid Python syntax')
        return True
    except SyntaxError as e:
        print(f'  ❌ SyntaxError at line {e.lineno}: {e.msg}')
        return False


def validate_markdown(target: Path) -> bool:
    """Validate Markdown, checking YAML frontmatter if present."""
    if yaml is None:
        print(f'  ⚠️ PyYAML not installed, skipping frontmatter check')
        return True
    
    try:
        content = target.read_text()

        if not content.startswith('---'):
            print(f'  ✅ Valid markdown (no frontmatter)')
            return True

        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            print(f'  ✅ Valid markdown (no frontmatter)')
            return True

        frontmatter = yaml.safe_load(frontmatter_match.group(1))

        # Validate required skill fields if this looks like a skill file
        if 'name' in frontmatter or 'version' in frontmatter:
            required = ['name', 'version']
            missing = [f for f in required if f not in frontmatter]

            if missing:
                print(f'  ⚠️  Missing skill fields: {missing}')
            else:
                print(f'  ✅ Valid skill frontmatter (v{frontmatter.get("version", "?")})')
        else:
            print(f'  ✅ Valid markdown (no skill frontmatter)')

        return True

    except yaml.YAMLError as e:
        print(f'  ❌ YAML parse error in frontmatter: {e}')
        return False


def validate_yaml(target: Path) -> bool:
    """Validate YAML syntax."""
    if yaml is None:
        print(f'  ⚠️ PyYAML not installed, skipping YAML validation')
        return True
    
    try:
        with open(target) as f:
            yaml.safe_load(f)
        print(f'  ✅ Valid YAML syntax')
        return True
    except yaml.YAMLError as e:
        print(f'  ❌ YAML error: {e}')
        return False


def expand_targets(targets: list[str]) -> list[Path]:
    """Expand directories to all supported files within them.

    SECURITY (SEC-001): Validates that all resolved paths stay within
    the target directory boundary to prevent path traversal attacks via
    symlinks or parent directory references.
    """
    expanded = []
    supported_extensions = {'.py', '.md', '.yaml', '.yml'}
    current_dir = Path.cwd().resolve()

    for target in targets:
        path = Path(target)

        if not path.exists():
            expanded.append(path)  # Let validation handle missing files
            continue

        if path.is_dir():
            # Recursively find all supported files in directory
            # SECURITY: Validate paths stay within target boundary (SEC-001)
            target_resolved = path.resolve()
            for ext in supported_extensions:
                for file_path in path.rglob(f'*{ext}'):
                    # Resolve path and check if within target boundary
                    resolved = file_path.resolve()
                    try:
                        resolved.relative_to(target_resolved)
                        expanded.append(file_path)  # Safe: within boundary
                    except ValueError:
                        pass  # Skip: outside boundary (traversal attempt)
        else:
            # SECURITY: Validate direct file paths stay within current directory (SEC-001)
            resolved = path.resolve()
            try:
                resolved.relative_to(current_dir)
                expanded.append(path)  # Safe: within boundary
            except ValueError:
                pass  # Skip: outside boundary (traversal attempt)

    return expanded


def main():
    # Parse arguments - support both space-separated and comma-separated
    if len(sys.argv) < 2:
        print("Usage: python stage1_syntax.py <target1> [target2] ...")
        sys.exit(1)

    # Handle comma-separated input
    targets = []
    for arg in sys.argv[1:]:
        targets.extend(arg.split(','))
    targets = [t.strip() for t in targets if t.strip()]

    # Expand directories to individual files
    file_paths = expand_targets(targets)

    if not file_paths:
        print('❌ No files found to validate')
        sys.exit(1)

    print(f'📄 Validating {len(file_paths)} file(s)')

    all_pass = True
    validated_count = 0

    for path in file_paths:
        ext = path.suffix.lower()

        # Validate based on extension
        if ext == '.py':
            if not validate_python(path):
                all_pass = False
            validated_count += 1

        elif ext == '.md':
            if not validate_markdown(path):
                all_pass = False
            validated_count += 1

        elif ext in ['.yaml', '.yml']:
            if not validate_yaml(path):
                all_pass = False
            validated_count += 1

        # Skip unsupported extensions silently

    if all_pass:
        print('\n✅ Stage 1 PASS: All files validated')
        sys.exit(0)
    else:
        print('\n❌ Stage 1 FAIL: Syntax errors found')
        sys.exit(1)


if __name__ == "__main__":
    main()
