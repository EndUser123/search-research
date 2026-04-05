import compileall
import sys
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")


def check_syntax():
    print(f"Checking syntax in {HOOKS_DIR}...")
    if not HOOKS_DIR.exists():
        print("Hooks directory not found!")
        sys.exit(1)

    # Use compileall to check syntax
    # legacy=True to write .pyc files to __pycache__ (we don't care about the files, just the success)
    # quiet=1: only print errors
    success = compileall.compile_dir(HOOKS_DIR, force=True, quiet=1, legacy=False)

    if success:
        print("✅ All files compiled successfully!")
    else:
        print("❌ Syntax errors found!")
        sys.exit(1)


if __name__ == "__main__":
    check_syntax()
