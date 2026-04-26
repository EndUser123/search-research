#!/usr/bin/env python3
"""Deep audit of hooks for logging gaps and anti-patterns."""

import json
import re
from pathlib import Path

# Get all hooks from settings.json
cfg = json.load(open(r"P:\.claude\settings.json"))
hooks_config = cfg.get("hooks", {})

all_hooks = set()
for hook_type, matchers in hooks_config.items():
    for matcher in matchers:
        for hook in matcher.get("hooks", []):
            if hook.get("type") == "command":
                cmd = hook.get("command", "")
                if "python" in cmd:
                    parts = cmd.split()
                    for p in parts[1:]:
                        if p.endswith(".py"):
                            all_hooks.add(p)
                            break

issues = {
    "missing_hook_main": [],
    "broad_except": [],
    "silent_except": [],  # except: pass or except Exception: pass
    "no_error_logging": [],  # Has except but no log_error call
}

for hook_path in sorted(all_hooks):
    # Normalize path
    if hook_path.startswith(".claude"):
        full_path = Path("P:") / hook_path
    elif hook_path.startswith("P:"):
        full_path = Path(hook_path)
    else:
        full_path = Path("P:") / hook_path

    if not full_path.exists():
        continue

    try:
        content = full_path.read_text(encoding="utf-8")

        # Check for @hook_main
        has_hook_main = "@hook_main" in content
        if not has_hook_main:
            issues["missing_hook_main"].append(hook_path)

        # Check for broad except (except Exception or bare except)
        if re.search(r"except\s*:", content) or re.search(
            r"except\s+Exception\s*:", content
        ):
            issues["broad_except"].append(hook_path)

        # Check for silent except (except: pass)
        if re.search(r"except.*:\s*\n\s*pass", content):
            issues["silent_except"].append(hook_path)

        # Check for except without log_error (if not using @hook_main)
        if not has_hook_main:
            if "except" in content and "log_error" not in content:
                issues["no_error_logging"].append(hook_path)

    except Exception as e:
        print(f"Error reading {hook_path}: {e}")

print("=" * 70)
print("HOOKS LOGGING AUDIT - GAPS & OPPORTUNITIES")
print("=" * 70)

print(f"\n1. MISSING @hook_main ({len(issues['missing_hook_main'])} hooks)")
print("   → Exceptions won't be logged automatically")
for h in issues["missing_hook_main"]:
    print(f"      ❌ {h}")

print(f"\n2. BROAD EXCEPT CLAUSES ({len(issues['broad_except'])} hooks)")
print("   → May swallow unexpected errors")
for h in issues["broad_except"]:
    print(f"      ⚠️  {h}")

print(f"\n3. SILENT EXCEPT (pass) ({len(issues['silent_except'])} hooks)")
print("   → Errors completely hidden")
for h in issues["silent_except"]:
    print(f"      🔇 {h}")

print(
    f"\n4. NO log_error CALL (missing @hook_main + has except) ({len(issues['no_error_logging'])} hooks)"
)
print("   → Has try/except but errors aren't logged")
for h in issues["no_error_logging"]:
    print(f"      📝 {h}")

# Priority recommendations
print("\n" + "=" * 70)
print("PRIORITY FIX RECOMMENDATIONS")
print("=" * 70)

# Find hooks that are in multiple categories (most risky)
risky = set(issues["missing_hook_main"]) & set(issues["no_error_logging"])
print(f"\n🔴 HIGH PRIORITY ({len(risky)}) - Missing decorator AND no logging:")
for h in sorted(risky):
    print(f"   → {h}")

# Medium: missing hook_main but has some error handling
medium = set(issues["missing_hook_main"]) - risky
print(
    f"\n🟡 MEDIUM PRIORITY ({len(medium)}) - Missing decorator (may have try/except):"
)
for h in sorted(medium):
    print(f"   → {h}")
