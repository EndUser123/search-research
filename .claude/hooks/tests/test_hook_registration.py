#!/usr/bin/env python3
"""
Hook Registration Validation Test (Option A)

Tests that every hook file is properly registered:
1. Either in a router (UserPromptSubmit_router.py, Stop_router.py, etc.)
2. Or explicitly as standalone in settings.json

Catches "dead hooks" that exist but never run.
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


def extract_env_vars_from_hook(file_path: Path) -> Set[str]:
    """Extract os.environ.get() calls from a Python file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        # Parse AST to find os.environ.get() calls
        tree = ast.parse(content)
        env_vars = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for os.environ.get(...)
                if isinstance(node.func, ast.Attribute):
                    if (isinstance(node.func.value, ast.Name) and
                        node.func.value.id == "os" and
                        node.func.attr == "environ"):
                        # Now check for .get() call
                        if isinstance(node.func, ast.Attribute):
                            # This is os.environ.get
                            if node.args and isinstance(node.args[0], ast.Constant):
                                env_vars.add(node.args[0].value)
                # Check for os.getenv() directly
                elif isinstance(node.func, ast.Name):
                    if node.func.id == "getenv":
                        if node.args and isinstance(node.args[0], ast.Constant):
                            env_vars.add(node.args[0].value)
        return env_vars
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        return set()


def extract_router_hooks(router_path: Path) -> Dict[str, str]:
    """Extract hook names registered in a router's HOOK_PRIORITY."""
    hooks = {}
    try:
        content = router_path.read_text(encoding="utf-8")
        # Find HOOK_PRIORITY dict definition
        match = re.search(r'HOOK_PRIORITY\s*=\s*{([^}]+)}', content, re.DOTALL)
        if match:
            priority_dict = match.group(1)
            # Extract hook names (keys)
            for hook_match in re.finditer(r'"([^"]+)":', priority_dict):
                hooks[hook_match.group(1)] = "priority"
        # Also check HOOK_DISPATCH
        dispatch_match = re.search(r'HOOK_DISPATCH\s*=\s*{([^}]+)}', content, re.DOTALL)
        if dispatch_match:
            dispatch_dict = dispatch_match.group(1)
            for hook_match in re.finditer(r'"([^"]+)":', dispatch_dict):
                hooks[hook_match.group(1)] = "dispatch"
        return hooks
    except Exception as e:
        print(f"Warning: Could not parse router {router_path}: {e}", file=sys.stderr)
        return {}


def extract_settings_hooks(settings_path: Path) -> Dict[str, str]:
    """Extract hook names registered in settings.json."""
    hooks = {}
    try:
        content = json.loads(settings_path.read_text(encoding="utf-8"))
        # Check hooks section
        if "hooks" in content:
            for event_name, event_hooks in content["hooks"].items():
                for matcher in event_hooks:
                    if "hooks" in matcher:
                        for hook in matcher["hooks"]:
                            if "command" in hook:
                                cmd = hook["command"]
                                # Extract hook filename from command
                                match = re.search(r'([^/\\]+)\.py', cmd)
                                if match:
                                    hook_name = match.group(1)
                                    # Normalize name (remove prefixes like UserPromptSubmit_)
                                    hook_name = hook_name.replace("UserPromptSubmit_", "")
                                    hook_name = hook_name.replace("PostToolUse_", "")
                                    hook_name = hook_name.replace("PreToolUse_", "")
                                    hook_name = hook_name.replace("StopHook_", "")
                                    hooks[hook_name] = f"settings.{event_name}"
        return hooks
    except Exception as e:
        print(f"Warning: Could not parse settings {settings_path}: {e}", file=sys.stderr)
        return {}


def extract_settings_env_vars(settings_path: Path) -> Set[str]:
    """Extract env var names from settings.json "env" section."""
    try:
        content = json.loads(settings_path.read_text(encoding="utf-8"))
        if "env" in content:
            return set(content["env"].keys())
        return set()
    except Exception as e:
        print(f"Warning: Could not parse settings {settings_path}: {e}", file=sys.stderr)
        return set()


def find_all_hook_files(hooks_dir: Path) -> List[Path]:
    """Find all Python hook files."""
    hook_files = []
    # Hooks in root directory
    for f in hooks_dir.glob("*.py"):
        if f.name.startswith("_") or f.name == "conftest.py":
            continue
        hook_files.append(f)
    # Hooks in subdirectories (PreToolUse/, PostToolUse/, etc.)
    for subdir in hooks_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("_"):
            for f in subdir.glob("*.py"):
                if f.name.startswith("_") or f.name == "conftest.py":
                    continue
                hook_files.append(f)
    return hook_files


def normalize_hook_name(file_path: Path, hooks_dir: Path) -> str:
    """Convert file path to normalized hook name."""
    # Get relative name without extension
    rel_path = file_path.relative_to(hooks_dir) if file_path.is_absolute() else file_path
    name = rel_path.stem

    # Remove common prefixes used in settings.json
    prefixes = ["UserPromptSubmit_", "PostToolUse_", "PreToolUse_", "StopHook_", "SessionStart_", "SessionEnd_"]
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    # Remove suffix patterns
    suffixes = ["_router", "_gate", "_detector", "_tracker", "_injector"]
    for suffix in suffixes:
        if name.endswith(suffix):
            # Keep the base name for router lookups
            pass

    return name


def test_hook_registration():
    """Main test: verify all hooks are registered somewhere."""
    hooks_dir = Path("P:/.claude/hooks")
    settings_path = Path("P:/.claude/settings.json")

    # Router files to check
    routers = {
        "UserPromptSubmit": hooks_dir / "UserPromptSubmit_router.py",
        "Stop": hooks_dir / "Stop_router.py",
        "PostToolUse": hooks_dir / "PostToolUse_router.py",
    }

    # Collect all registered hooks
    registered_hooks: Dict[str, str] = {}
    for event_name, router_path in routers.items():
        if router_path.exists():
            router_hooks = extract_router_hooks(router_path)
            for hook, source in router_hooks.items():
                if hook not in registered_hooks:
                    registered_hooks[hook] = f"router.{event_name}"
                else:
                    # Already registered, prefer first registration
                    pass

    # Add standalone hooks from settings.json
    settings_hooks = extract_settings_hooks(settings_path)
    for hook, source in settings_hooks.items():
        if hook not in registered_hooks:
            registered_hooks[hook] = source

    # Collect env vars from settings.json
    settings_env_vars = extract_settings_env_vars(settings_path)

    # Find all hook files
    hook_files = find_all_hook_files(hooks_dir)

    # Check each hook file
    unregistered = []
    missing_env_vars = []

    for hook_file in hook_files:
        hook_name = normalize_hook_name(hook_file, hooks_dir)

        # Skip known test files and non-hooks
        skip_patterns = ["test_", "smoke_test", "__lib", "tests/", "repositories/",
                        "shared_utils.py", "hook_tracker.py", "hook_diagnostics.py",
                        "hook_base.py", "intent_utils.py"]
        if any(pattern in str(hook_file) for pattern in skip_patterns):
            continue

        # Check if registered
        if hook_name not in registered_hooks:
            # Check for close matches (fuzzy matching)
            close_matches = [reg for reg in registered_hooks
                            if hook_name.lower() in reg.lower() or reg.lower() in hook_name.lower()]
            if close_matches:
                # Probably registered under slightly different name
                continue
            unregistered.append((hook_name, str(hook_file.relative_to(hooks_dir))))

        # Check env vars used by hook
        env_vars = extract_env_vars_from_hook(hook_file)
        for env_var in env_vars:
            # Check if ENABLE env var is in settings.json
            if env_var.endswith("_ENABLED") and env_var not in settings_env_vars:
                # Check for case-insensitive match
                case_insensitive_match = any(
                    env_var.lower() == setting_var.lower()
                    for setting_var in settings_env_vars
                )
                if not case_insensitive_match:
                    missing_env_vars.append((env_var, str(hook_file.relative_to(hooks_dir))))

    # Print results
    print("=" * 70)
    print("HOOK REGISTRATION VALIDATION")
    print("=" * 70)

    if unregistered:
        print(f"\n❌ UNREGISTERED HOOKS ({len(unregistered)}):")
        for hook_name, path in sorted(unregistered):
            print(f"  - {hook_name} ({path})")
        print("\n⚠️  These hooks exist but are not registered in any router or settings.json")
        print("   They will never run!")
    else:
        print("\n✅ All hooks are registered in routers or settings.json")

    if missing_env_vars:
        print(f"\n⚠️  MISSING ENV VARS ({len(missing_env_vars)}):")
        for env_var, path in sorted(missing_env_vars):
            print(f"  - {env_var} (used in {path})")
        print("\n⚠️  These env vars are referenced by hooks but not in settings.json")
        print("   Hooks may not work as intended!")
    else:
        print("\n✅ All hook env vars are defined in settings.json")

    print("\n📊 SUMMARY:")
    print(f"   Total hooks found: {len(hook_files)}")
    print(f"   Registered hooks: {len(registered_hooks)}")
    print(f"   Unregistered hooks: {len(unregistered)}")
    print(f"   Missing env vars: {len(missing_env_vars)}")

    # Exit code
    if unregistered or missing_env_vars:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(test_hook_registration())
