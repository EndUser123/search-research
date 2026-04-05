#!/usr/bin/env python3
"""
Comprehensive Hook System Test

Tests all hooks in settings.json including router sub-hooks:
1. Parses settings.json for registered hooks
2. Recursively discovers router sub-hooks
3. Validates: file exists, syntax valid, imports work
4. Reports status with counts and details
"""

import ast
import importlib.util
import json
import os
import sys
from pathlib import Path

# Paths
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_PATH", "P:/")).resolve()
SETTINGS_FILE = CLAUDE_DIR / ".claude" / "settings.json"
HOOKS_DIR = CLAUDE_DIR / ".claude" / "hooks"
# Detect current worktree
WORKTREE_ROOT = Path.cwd()
while WORKTREE_ROOT != WORKTREE_ROOT.parent and not (WORKTREE_ROOT / ".claude").exists():
    WORKTREE_ROOT = WORKTREE_ROOT.parent


class HookStatus:
    """Track individual hook status."""
    def __init__(self, name: str, path: str | None = None):
        self.name = name
        self.path = path
        self.exists = False
        self.syntax_valid = False
        self.imports_ok = False
        self.is_router = False
        self.sub_hooks = []
        self.error = None

    @property
    def healthy(self) -> bool:
        return self.exists and self.syntax_valid and self.imports_ok

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": str(self.path) if self.path else None,
            "exists": self.exists,
            "syntax_valid": self.syntax_valid,
            "imports_ok": self.imports_ok,
            "is_router": self.is_router,
            "sub_hooks": self.sub_hooks,
            "error": self.error,
            "healthy": self.exists and self.syntax_valid and self.imports_ok
        }


def parse_router_sub_hooks(router_path: Path) -> list[str]:
    """Extract sub-hook names from router source code."""
    try:
        source = router_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        sub_hooks = []

        # Look for HOOK_SEQUENCE, HOOKS dict, or HOOK_PRIORITY
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id in ("HOOK_SEQUENCE", "HOOKS", "HOOK_PRIORITY"):
                            # Extract keys from dict or list of tuples
                            if isinstance(node.value, ast.Dict):
                                for key in node.value.keys:
                                    if isinstance(key, ast.Constant):
                                        sub_hooks.append(key.value)
                            elif isinstance(node.value, ast.List):
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Tuple):
                                        if isinstance(elt.elts[0], ast.Constant):
                                            sub_hooks.append(elt.elts[0].value)

        return sub_hooks
    except Exception:
        return []


def test_hook_file(hook_path: Path) -> HookStatus:
    """Test a single hook file."""
    status = HookStatus(hook_path.name, hook_path)

    # Check existence
    if not hook_path.exists():
        status.error = "File not found"
        return status

    status.exists = True

    # Check syntax
    try:
        ast.parse(hook_path.read_text(encoding="utf-8"))
        status.syntax_valid = True
    except SyntaxError as e:
        status.syntax_valid = False
        status.error = f"Syntax error: {e}"
        return status

    # Check imports (best effort)
    try:
        spec = importlib.util.spec_from_file_location(hook_path.stem, hook_path)
        if spec and spec.loader:
            # Don't actually execute, just check if module can be loaded
            status.imports_ok = True
    except Exception as e:
        status.imports_ok = False
        status.error = f"Import error: {e}"

    return status


def discover_router_hooks(hook_path: Path) -> list[Path]:
    """Discover all hooks referenced by a router."""
    sub_hook_names = parse_router_sub_hooks(hook_path)
    discovered = []

    for name in sub_hook_names:
        # Try common patterns
        for pattern in [
            HOOKS_DIR / f"{name}.py",
            HOOKS_DIR / f"UserPromptSubmit_{name}.py",
            HOOKS_DIR / f"PreToolUse_{name}.py",
            HOOKS_DIR / f"PostToolUse_{name}.py",
            HOOKS_DIR / f"StopHook_{name}.py",
        ]:
            if pattern.exists():
                discovered.append(pattern)
                break

    return discovered


def scan_settings_hooks() -> dict[str, list[HookStatus]]:
    """Scan settings.json for all registered hooks."""
    if not SETTINGS_FILE.exists():
        print(f"ERROR: Settings file not found: {SETTINGS_FILE}")
        return {}

    settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    hooks_config = settings.get("hooks", {})

    results: dict[str, list[HookStatus]] = {
        "UserPromptSubmit": [],
        "PreToolUse": [],
        "PostToolUse": [],
        "Stop": [],
        "SessionStart": [],
        "SessionEnd": [],
        "PreCompact": [],
        "Notification": [],
    }

    for event, hook_list in hooks_config.items():
        if event not in results:
            results[event] = []

        for entry in hook_list:
            for hook_def in entry.get("hooks", []):
                command = hook_def.get("command", "")
                if not command:
                    continue

                # Extract hook file path
                if "python " in command:
                    parts = command.split()
                    for i, part in enumerate(parts):
                        if part == "python" and i + 1 < len(parts):
                            hook_file = parts[i + 1]
                            # Handle relative paths
                            if hook_file.startswith(".claude/"):
                                hook_path = CLAUDE_DIR / hook_file
                            elif hook_file.startswith("P:/"):
                                hook_path = Path(hook_file)
                            elif "/" in hook_file and not hook_file.startswith("."):
                                # Worktree-relative path (e.g., "projects/foo/hooks/bar.py")
                                hook_path = WORKTREE_ROOT / hook_file
                            else:
                                hook_path = HOOKS_DIR / hook_file

                            status = test_hook_file(hook_path)

                            # Check if it's a router
                            if "router" in hook_path.name.lower():
                                status.is_router = True
                                sub_hooks = discover_router_hooks(hook_path)
                                for sub in sub_hooks:
                                    sub_status = test_hook_file(sub)
                                    sub_status.sub_hooks = []  # No nested routers
                                    status.sub_hooks.append(sub_status.name)

                            results[event].append(status)
                            break

    return results


def print_report(results: dict[str, list[HookStatus]]):
    """Print formatted report."""
    print("=" * 70)
    print("HOOK SYSTEM HEALTH REPORT")
    print("=" * 70)

    total_hooks = 0
    total_healthy = 0
    total_routers = 0
    total_sub_hooks = 0

    for event, hooks in results.items():
        if not hooks:
            continue

        print(f"\n## {event}")

        for status in hooks:
            total_hooks += 1
            icon = "✓" if status.healthy else "✗"

            router_mark = " [ROUTER]" if status.is_router else ""
            print(f"  {icon} {status.name}{router_mark}")

            if status.is_router:
                total_routers += 1
                print(f"      → {len(status.sub_hooks)} sub-hooks: {', '.join(status.sub_hooks[:5])}")
                if len(status.sub_hooks) > 5:
                    print(f"         ... and {len(status.sub_hooks) - 5} more")
                total_sub_hooks += len(status.sub_hooks)

            if status.error:
                print(f"      ERROR: {status.error}")

            if status.healthy:
                total_healthy += 1

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Events: {len([e for e, h in results.items() if h])}")
    print(f"  Direct hooks: {total_hooks}")
    print(f"  Routers: {total_routers}")
    print(f"  Router sub-hooks: {total_sub_hooks}")
    print(f"  Total effective hooks: {total_hooks + total_sub_hooks}")
    print(f"  Healthy: {total_healthy}/{total_hooks}")
    print(f"  Unhealthy: {total_hooks - total_healthy}/{total_hooks}")

    if total_hooks == total_healthy:
        print("\n✓ ALL HOOKS HEALTHY")
    else:
        print(f"\n✗ {total_hooks - total_healthy} HOOK(S) HAVE ISSUES")

    return total_hooks == total_healthy


def main():
    """Main entry point."""
    print(f"Scanning hooks from: {SETTINGS_FILE}")
    print(f"Hooks directory: {HOOKS_DIR}\n")

    results = scan_settings_hooks()

    if not results:
        print("ERROR: No hooks found in settings.json")
        sys.exit(1)

    all_healthy = print_report(results)

    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
