#!/usr/bin/env python3
"""Test PathLib.resolve() behavior with Windows extended-length paths.

This test verifies whether extended-length path prefixes (\\?\\) can bypass
security checks in the directory policy hook.
"""

import sys
from pathlib import Path


def test_regular_path():
    """Test that regular paths work normally."""
    print("Test 1 - Regular path:")
    regular_path = Path("P:/test/regular/path.txt")
    print(f"  Input: {regular_path}")
    print(f"  Resolve: {regular_path.resolve()}")
    print("  ✓ PASS\n")


def test_extended_length_prefix():
    """Test extended-length path prefix behavior."""
    print("Test 2 - Extended-length path prefix:")

    # Using raw string to avoid escape sequence issues
    extended = Path(r"\\?\P:\test\extended\path.txt")
    print(f"  Input: {extended}")

    try:
        resolved = extended.resolve()
        print(f"  Resolve: {resolved}")
        print(f"  Type: {type(resolved)}")
        print(f"  Is absolute: {resolved.is_absolute()}")

        # Check if prefix was stripped
        resolved_str = str(resolved)
        prefix = r"\\?\\"
        if not resolved_str.startswith(prefix):
            print("  ⚠ WARNING: Extended-length prefix was stripped!")
        else:
            print("  ✓ Prefix preserved")

    except Exception as e:
        print(f"  Error: {e}")

    print()


def test_boundary_check_with_extended():
    """Test boundary check with extended path."""
    print("Test 3 - Boundary check with extended path:")

    extended = Path(r"\\?\P:\test\extended\path.txt")
    project_dir = Path("P:/")

    try:
        resolved = extended.resolve()
        print(f"  Extended path: {resolved}")
        print(f"  Project dir: {project_dir}")

        rel = resolved.relative_to(project_dir)
        print(f"  Relative path: {rel}")
        print("  ⚠ WARNING: Boundary check passed (should have been blocked)")

    except ValueError as e:
        print(f"  Boundary check: BLOCKED ({e})")
        print("  ✓ PASS - Correctly blocked")

    print()


def test_attack_scenario():
    """Test path traversal attack with extended-length prefix."""
    print("=== ATTACK SCENARIO TEST ===")
    print()

    # Attack: Use extended-length prefix to escape project directory
    attack_path = Path(r"\\?\P:\..\..\..\..\windows\system32\config\sam")
    print("Attack input: Extended-length prefix + path traversal")
    print(f"Raw path: {repr(str(attack_path))}")
    print()

    try:
        resolved = attack_path.resolve()
        print(f"PathLib.resolve(): {resolved}")
        print(f"Is absolute: {resolved.is_absolute()}")

        # What our hook would see
        normalized = str(resolved).replace("\\", "/").lower()
        print(f"Hook normalization: {normalized}")
        print(f"Starts with P:/: {normalized.startswith('p:/')}")

        # Boundary check (our security control)
        project_dir = Path("P:/")
        try:
            rel = resolved.relative_to(project_dir)
            print(f"Boundary check: PASSED (relative path: {rel})")
            print("❌ SECURITY ISSUE: Attack bypassed detection!")
            return False
        except ValueError as e:
            print(f"Boundary check: BLOCKED ({e})")
            print("✓ PASS - Attack was blocked")
            return True

    except Exception as e:
        print(f"Error during attack test: {e}")
        return False

    print()


def test_unc_path():
    """Test UNC path behavior."""
    print("Test 4 - UNC path:")

    unc = Path(r"\\server\share\path.txt")
    print(f"  Input: {unc}")

    try:
        resolved = unc.resolve()
        print(f"  Resolve: {resolved}")
        print(f"  Is absolute: {resolved.is_absolute()}")
        print(f"  Is UNC: {unc.is_absolute() and str(unc).startswith('\\\\')}")
    except Exception as e:
        print(f"  Error: {e}")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("PathLib Extended-Length Path Security Tests")
    print("=" * 60)
    print()

    test_regular_path()
    test_extended_length_prefix()
    test_boundary_check_with_extended()
    test_unc_path()

    # Attack scenario test returns boolean
    attack_blocked = test_attack_scenario()

    print("=" * 60)
    print("Summary:")
    print("  - Regular paths: ✓ Work normally")
    print("  - Extended-length prefix: ⚠ Stripped by PathLib.resolve()")
    print("  - Attack scenario:", "✓ BLOCKED" if attack_blocked else "❌ BYPASSED")
    print("=" * 60)

    sys.exit(0 if attack_blocked else 1)
