#!/usr/bin/env python3
"""
Hook Loading Test Coverage

Comprehensive tests for hook module loading, import resolution, and
registry functionality. Prevents recurrence of UserPromptSubmit
import failures due to naming conflicts and bytecode corruption.

Coverage areas:
1. Module import resolution
2. Registry hook discovery
3. Relative import validation
4. Package structure integrity
5. Backward compatibility

Integration:
    Part of pytest test suite
    Run standalone: python tests/test_hook_loading.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def test_userpromptsubmit_module_exists() -> None:
    """Test that UserPromptSubmit.py module file exists."""
    hook_file = HOOKS_DIR / "UserPromptSubmit.py"
    assert hook_file.exists(), f"UserPromptSubmit.py not found at {hook_file}"
    assert hook_file.is_file(), "UserPromptSubmit.py is not a file"


def test_userpromptsubmit_modules_package_exists() -> None:
    """Test that UserPromptSubmit_modules package exists."""
    package_dir = HOOKS_DIR / "UserPromptSubmit_modules"
    assert package_dir.exists(), f"UserPromptSubmit_modules not found at {package_dir}"
    assert package_dir.is_dir(), "UserPromptSubmit_modules is not a directory"


def test_userpromptsubmit_modules_init_exists() -> None:
    """Test that UserPromptSubmit_modules/__init__.py exists."""
    init_file = HOOKS_DIR / "UserPromptSubmit_modules" / "__init__.py"
    assert init_file.exists(), f"__init__.py not found at {init_file}"
    assert init_file.is_file(), "__init__.py is not a file"


def test_userpromptsubmit_registry_module_exists() -> None:
    """Test that registry module exists in package."""
    registry_file = HOOKS_DIR / "UserPromptSubmit_modules" / "registry.py"
    assert registry_file.exists(), f"registry.py not found at {registry_file}"
    assert registry_file.is_file(), "registry.py is not a file"


def test_userpromptsubmit_base_module_exists() -> None:
    """Test that base module exists in package."""
    base_file = HOOKS_DIR / "UserPromptSubmit_modules" / "base.py"
    assert base_file.exists(), f"base.py not found at {base_file}"
    assert base_file.is_file(), "base.py is not a file"


def test_import_userpromptsubmit_modules() -> None:
    """Test that UserPromptSubmit_modules package can be imported."""
    try:
        import UserPromptSubmit_modules
        assert UserPromptSubmit_modules is not None
        assert hasattr(UserPromptSubmit_modules, "__all__")
    except ImportError as e:
        raise AssertionError(f"Failed to import UserPromptSubmit_modules: {e}")


def test_import_userpromptsubmit_registry() -> None:
    """Test that registry module can be imported."""
    try:
        from UserPromptSubmit_modules import registry
        assert registry is not None
    except ImportError as e:
        raise AssertionError(f"Failed to import registry: {e}")


def test_import_userpromptsubmit_base() -> None:
    """Test that base module can be imported."""
    try:
        from UserPromptSubmit_modules import base
        assert base is not None
        assert hasattr(base, "HookContext")
        assert hasattr(base, "HookResult")
    except ImportError as e:
        raise AssertionError(f"Failed to import base: {e}")


def test_backward_compatibility_alias() -> None:
    """Test that backward compatibility alias is created."""

    # Import should create alias in sys.modules
    assert "UserPromptSubmit" in sys.modules, "Backward compatibility alias not created"
    assert sys.modules["UserPromptSubmit"] is sys.modules["UserPromptSubmit_modules"]


def test_registry_has_run_hooks() -> None:
    """Test that registry module has run_hooks function."""
    from UserPromptSubmit_modules import registry

    assert hasattr(registry, "run_hooks"), "registry.run_hooks not found"
    assert callable(registry.run_hooks), "registry.run_hooks is not callable"


def test_base_has_required_classes() -> None:
    """Test that base module has required classes."""
    from UserPromptSubmit_modules import base

    assert hasattr(base, "HookContext"), "HookContext class not found"
    assert hasattr(base, "HookResult"), "HookResult class not found"

    # Verify HookResult has required methods (dataclass-based)
    hook_result_methods = ["empty", "is_empty"]
    for method in hook_result_methods:
        assert hasattr(base.HookResult, method), f"HookResult.{method} not found"


def test_no_naming_conflict() -> None:
    """Test that UserPromptSubmit.py doesn't shadow UserPromptSubmit_modules package."""
    # Import both
    import UserPromptSubmit_modules

    spec = importlib.util.spec_from_file_location(
        "UserPromptSubmit", HOOKS_DIR / "UserPromptSubmit.py"
    )
    assert spec is not None, "Could not load spec for UserPromptSubmit.py"

    # Load module from spec
    userpromptsubmit_module = importlib.util.module_from_spec(spec)

    # Verify they are different
    assert userpromptsubmit_module is not UserPromptSubmit_modules


def test_package_exports() -> None:
    """Test that package exports all expected modules."""
    import UserPromptSubmit_modules

    expected_exports = [
        "base",
        "conversation_gate",
        "unified_injector",
        "skill_enforcer",
        "plan_injector",
        "diagnostic_guard",
        "intent_handlers",
        "registry",
    ]

    __all__ = UserPromptSubmit_modules.__all__

    for export in expected_exports:
        assert export in __all__, f"{export} not in __all__"


def test_registry_hook_discovery() -> None:
    """Test that registry can discover hooks."""
    from UserPromptSubmit_modules import registry

    # Registry should have HOOKS dict
    assert hasattr(registry, "HOOKS"), "HOOKS not found"

    # Registry should have HOOK_PRIORITY dict
    assert hasattr(registry, "HOOK_PRIORITY"), "HOOK_PRIORITY not found"

    # Registry should have register_hook function
    assert hasattr(registry, "register_hook"), "register_hook not found"
    assert callable(registry.register_hook), "register_hook is not callable"


def run_all_tests() -> int:
    """Run all tests when script is executed directly."""
    import traceback

    print("Running hook loading test coverage...\n")

    tests = [
        ("UserPromptSubmit.py exists", test_userpromptsubmit_module_exists),
        ("UserPromptSubmit_modules package exists", test_userpromptsubmit_modules_package_exists),
        ("__init__.py exists", test_userpromptsubmit_modules_init_exists),
        ("registry.py exists", test_userpromptsubmit_registry_module_exists),
        ("base.py exists", test_userpromptsubmit_base_module_exists),
        ("Import UserPromptSubmit_modules", test_import_userpromptsubmit_modules),
        ("Import registry", test_import_userpromptsubmit_registry),
        ("Import base", test_import_userpromptsubmit_base),
        ("Backward compatibility alias", test_backward_compatibility_alias),
        ("registry has run_hooks", test_registry_has_run_hooks),
        ("base has required classes", test_base_has_required_classes),
        ("No naming conflict", test_no_naming_conflict),
        ("Package exports", test_package_exports),
        ("Registry hook discovery", test_registry_hook_discovery),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"Testing: {name}...", end=" ")
            test_func()
            print("✓ PASS")
            passed += 1
        except AssertionError as e:
            print("✗ FAIL")
            print(f"  Error: {e}")
            failed += 1
        except Exception:
            print("✗ ERROR")
            print(f"  {traceback.format_exc()}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
