"""Debug script for router hook extraction."""

import re
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")

# Test: Simulate what the posttooluse extraction produces
post_init = HOOKS_DIR / "posttooluse" / "__init__.py"
src = post_init.read_text(encoding="utf-8")

# CORRECT pattern (no $ anchor)
pattern = r'registry\.register\("[^"]+",\s*(\w+)\)'
matches = list(re.finditer(pattern, src))
print(f"Regex matches in posttooluse/__init__.py: {len(matches)}")
for m in matches[:10]:
    class_name = m.group(1)
    snake = re.sub(r"(?<=[a-z])([A-Z])", r"_\1", class_name).lower()
    filename = f"{snake}.py"
    print(f"  {class_name} -> {filename}")

# Check what wired hooks look like
wired = list((HOOKS_DIR / "posttooluse").glob("*_hook.py"))
print(f"\nActual hook files in posttooluse/: {len(wired)}")
for f in wired[:10]:
    print(f"  {f.name}")

# Check router hooks for breadcrumb
router_hooks = set()
for m in re.finditer(pattern, src):
    class_name = m.group(1)
    snake = re.sub(r"(?<=[a-z])([A-Z])", r"_\1", class_name).lower()
    filename = f"{snake}.py"
    router_hooks.add(f"posttooluse/{filename}")

print(f"\nRouter hooks containing 'breadcrumb': {[h for h in router_hooks if 'breadcrumb' in h]}")
print(f"Total router hooks: {len(router_hooks)}")

# Now test _collect_orphan_hooks
import sys

sys.path.insert(0, str(HOOKS_DIR))
from SessionStart_hook_health_check import (
    _collect_orphan_hooks,
    _collect_router_hooks,
    _collect_wired_hook_files,
)

print("\n--- Running actual functions ---")
wired = _collect_wired_hook_files()
print(f"Wired count: {len(wired)}")

router = _collect_router_hooks()
router_posttooluse = [h for h in router if "posttooluse" in h]
print(f"Router posttooluse entries: {router_posttooluse[:10]}")
print(f"Total router hooks: {len(router)}")

orphans = _collect_orphan_hooks(wired)
print(f"Orphan count: {len(orphans)}")
print(f"Orphans (first 5): {[o.name for o in orphans[:5]]}")
