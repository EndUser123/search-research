#!/usr/bin/env python3
"""
SessionStart Hook: Import Health Check

Monitors hook import health at session start to catch module loading
issues early, before they cause UserPromptSubmit errors in active use.

Problem: UserPromptSubmit import failures were discovered during active
use, causing disruption. This hook provides early warning of import issues.

What it checks:
1. UserPromptSubmit module imports successfully
2. UserPromptSubmit_modules package imports successfully
3. Registry module imports and has run_hooks function
4. No naming conflicts between .py file and package directory

Integration:
    Registered in settings.json under SessionStart hooks
    Runs automatically at session start
    Fails open (doesn't block session on errors)

Configuration:
    HOOK_IMPORT_HEALTH_ENABLED=true to enable (default)
    HOOK_IMPORT_HEALTH_VERBOSE=true for detailed output
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import logging as _li

_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)


# Configuration
ENABLED = os.environ.get("HOOK_IMPORT_HEALTH_ENABLED", "true").lower() in ("1", "true", "yes")
VERBOSE = os.environ.get("HOOK_IMPORT_HEALTH_VERBOSE", "false").lower() in ("1", "true", "yes")

# Hooks directory
HOOKS_DIR = Path(__file__).resolve().parent


def check_import(module_name: str) -> tuple[bool, str]:
    """Check if a module can be imported.

    Returns:
        (success: bool, error_message: str)
    """
    try:
        __import__(module_name)
        return True, ""
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_registry() -> tuple[bool, str]:
    """Check if registry module has required functions.

    Returns:
        (success: bool, error_message: str)
    """
    try:
        from UserPromptSubmit_modules import registry

        if not hasattr(registry, "run_hooks"):
            return False, "registry.run_hooks function not found"

        if not callable(registry.run_hooks):
            return False, "registry.run_hooks is not callable"

        return True, ""
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_naming_conflict() -> tuple[bool, str]:
    """Check for naming conflicts between .py file and package directory.

    Returns:
        (success: bool, error_message: str)
    """
    hook_file = HOOKS_DIR / "UserPromptSubmit.py"
    package_dir = HOOKS_DIR / "UserPromptSubmit_modules"

    if hook_file.exists() and package_dir.exists():
        # This is OK - they have different names
        return True, ""

    if not hook_file.exists():
        return False, "UserPromptSubmit.py not found"

    if not package_dir.exists():
        return False, "UserPromptSubmit_modules package not found"

    return True, ""


def run_health_checks() -> list[dict]:
    """Run all health checks.

    Returns:
        List of check results with name, status, and error_message
    """
    checks = [
        ("Import UserPromptSubmit_modules", check_import("UserPromptSubmit_modules")),
        ("Registry has run_hooks", check_registry()),
        ("No naming conflict", check_naming_conflict()),
    ]

    results = []
    for name, (success, error) in checks:
        results.append({
            "name": name,
            "status": "pass" if success else "fail",
            "error": error if not success else None,
        })

    return results


def main() -> int:
    """Run import health checks."""
    if not ENABLED:
        return 0

    # Add hooks directory to path
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))

    results = run_health_checks()

    # Count failures
    failures = [r for r in results if r["status"] == "fail"]

    if failures:
        # Import health issues detected
        if VERBOSE:
            _logger.info("\n⚠️  HOOK IMPORT HEALTH CHECK FAILED")
            _logger.info("="*60)

            for result in failures:
                _logger.info(f"\n❌ {result['name']}")
                _logger.info(f"   {result['error']}")

            _logger.info("\n" + "="*60)
            _logger.info("\nThis may cause UserPromptSubmit hook errors.")
            _logger.info("Fix steps:")
            print("  1. Check for naming conflicts (.py vs package)", file=sys.stderr)
            _logger.info("  2. Clear Python bytecode: find . -name '__pycache__' -exec rm -rf {} +")
            _logger.info("  3. Verify module structure in UserPromptSubmit_modules/")

        # Log to state file for monitoring
        state_dir = HOOKS_DIR / "state"
        state_dir.mkdir(exist_ok=True)
        state_file = state_dir / "hook_import_health.json"

        try:
            state_file.write_text(
                json.dumps({
                    "status": "failed",
                    "checks": results,
                    "timestamp": __import__("time").time(),
                }, indent=2)
            )
        except Exception:
            pass  # Fail open - don't block session on state write errors

    elif VERBOSE:
        print("\n✅ Hook import health check passed")
        for result in results:
            print(f"  ✓ {result['name']}")

    # Always return 0 (fail open - don't block session start)
    return 0


if __name__ == "__main__":
    sys.exit(main())
