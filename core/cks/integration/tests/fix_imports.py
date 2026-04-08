#!/usr/bin/env python3
"""Fix import issues in CKS project context adapter.

This script fixes:
1. @contextmanager -> @contextlib.contextmanager
2. Relative imports to conditional imports
"""

from pathlib import Path

# Paths
project_context_path = (
    PROJECT_ROOT
    / "__csf"
    / "src"
    / "features"
    / "cks"
    / "integration"
    / "adapters"
    / "project_context"
)


# Computed project root (Python 3.12+)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent


def fix_file(filepath) -> bool:
    """Fix imports in a single file."""
    print(f"Fixing: {filepath.name}")

    content = filepath.read_text(encoding="utf-8")
    original = content

    # Fix 1: @contextmanager -> @contextlib.contextmanager
    content = content.replace("@contextmanager\n", "@contextlib.contextmanager\n")

    # Fix 2: Add conditional imports for repository files
    if filepath.name in ["project_context_repository.py", "checkpoint_repository.py"]:
        # Check if it already has the conditional import pattern
        if "except ImportError:" not in content:
            # Find the import section and add conditional imports
            lines = content.split("\n")
            new_lines = []
            i = 0

            while i < len(lines):
                line = lines[i]

                # Check if this is a relative import line
                if line.strip().startswith("from .") and "import" in line:
                    # Collect consecutive import lines
                    import_lines = []
                    while i < len(lines) and (
                        lines[i].strip().startswith("from .") or lines[i].strip().startswith("#")
                    ):
                        import_lines.append(lines[i])
                        i += 1

                    # Create conditional import block
                    indent = len(line) - len(line.lstrip())
                    " " * indent

                    new_lines.append(
                        "# Try relative imports first (for package usage), then absolute (for standalone)"
                    )
                    new_lines.append("try:")

                    # Add relative imports with proper indentation
                    for imp_line in import_lines:
                        if imp_line.strip() and not imp_line.strip().startswith("#"):
                            new_lines.append(f"    {imp_line}")
                        else:
                            new_lines.append(imp_line)

                    new_lines.append("except ImportError:")
                    new_lines.append("    # Standalone execution - use absolute imports")

                    # Add absolute imports
                    for imp_line in import_lines:
                        if imp_line.strip() and not imp_line.strip().startswith("#"):
                            # Convert relative to absolute
                            abs_import = imp_line.replace("from .", "from ")
                            abs_import = abs_import.replace("from ..", "from ")
                            new_lines.append(f"    {abs_import}")
                        else:
                            new_lines.append(imp_line)

                    continue

                new_lines.append(line)
                i += 1

            content = "\n".join(new_lines)

    # Write back if changed
    if content != original:
        filepath.write_text(content, encoding="utf-8")
        print("  ✅ Fixed")
        return True
    print("  ✓ No changes needed")
    return False


def main() -> None:
    """Fix all files."""
    print("=" * 70)
    print("Fixing CKS Project Context Adapter Imports")
    print("=" * 70)

    # Files to fix
    files_to_fix = [
        project_context_path / "repositories" / "project_context_repository.py",
        project_context_path / "repositories" / "checkpoint_repository.py",
    ]

    fixed_count = 0
    for filepath in files_to_fix:
        if filepath.exists():
            if fix_file(filepath):
                fixed_count += 1
        else:
            print(f"❌ File not found: {filepath}")

    print("\n" + "=" * 70)
    print(f"Fixed {fixed_count} file(s)")
    print("=" * 70)


if __name__ == "__main__":
    main()
