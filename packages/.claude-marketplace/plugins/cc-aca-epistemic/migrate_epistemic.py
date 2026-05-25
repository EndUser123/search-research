#!/usr/bin/env python3
"""Migration script for cc-aca-epistemic plugin.

Copies epistemic hooks and modules from P:/.claude/hooks/ and P:/packages/fact-guard/
into the plugin structure at P:/packages/cc-aca-epistemic/, adjusting import paths.

Usage:
    python migrate_epistemic.py          # Run all migrations
    python migrate_epistemic.py --verify  # Verify existing migration
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")
PLUGIN_ROOT = Path("P:/packages/cc-aca-epistemic")
PLUGIN_LIB = PLUGIN_ROOT / "lib"
FACT_GUARD_ROOT = Path("P:/packages/fact-guard")

# --- Source file definitions ---

CORE_MODULES = [
    "epistemic_validator.py",
    "unified_claim_verifier.py",
    "empirical_claims_gate.py",
    "assumption_audit_v2.py",
    "self_verification_gate.py",
    "evidence_store.py",
    "evidence_scope.py",
    "turn_scoped_evidence.py",
    "verify_claims.py",
    "verification_audit_logger.py",
]

PRETOOL_HOOKS = [
    "PreToolUse_evidence_hierarchy_gate.py",
    "PreToolUse_verification_router.py",
    "PreToolUse_investigation_gate.py",
    "PreToolUse_dependency_verification_gate.py",
    "PreToolUse_file_existence_guard.py",
    "PreToolUse_command_intent_gate.py",
    "PreToolUse_type_validator.py",
]

STOP_HOOKS = [
    "StopHook_unverified_stance.py",
    "StopHook_cross_validator.py",
    "Stop_comparative_claim_guard.py",
    "Stop_deletion_verification_guard.py",
    "StopHook_cited_content_guard.py",
    "Stop_fake_done_detector.py",
    "Stop_diagnostic_analysis_quality_gate.py",
    "StopHook_perf_attribution_gate.py",
    "Stop_skill_dir_correlation_gate.py",
    "Stop_git_diff_reground.py",
    "Stop_artifact_enforcement.py",
    "Stop_cks_correction_anchor.py",
]

POSTTOOL_HOOKS = [
    "PostToolUse_artifact_validator.py",
    # These 3 don't exist in hooks dir — skip silently
    # "PostToolUse_edit_verifier.py",
    # "PostToolUse_evidence_capture.py",
    # "PostToolUse_quality_check.py",
]

USERPROMPTSUBMIT_HOOKS = [
    "UserPromptSubmit_claim_classifier.py",
]

LIB_DIRS = {
    "verification": "verification",       # hooks/verification/ -> lib/verification/
    "anti_sycophancy": "anti_sycophancy",  # hooks/anti_sycophancy/ -> lib/anti_sycophancy/
}

# Anti-sycophancy files to EXCLUDE (non-epistemic)
ANTI_SYCOPHANCY_EXCLUDE = {"toggle.py"}

# Fact-guard files to absorb
FACT_GUARD_HOOKS = [
    ("hooks/fact-guard_PreToolUse.py", "hooks/pretool/fact-guard_PreToolUse.py"),
    ("hooks/fact-guard_PostToolUse.py", "hooks/posttool/fact-guard_PostToolUse.py"),
]
FACT_GUARD_LIB = [
    ("src/fact_guard/provenance.py", "lib/provenance.py"),
    ("src/fact_guard/contamination.py", "lib/contamination.py"),
]


def adjust_hook_imports(content: str, source_type: str) -> str:
    """Adjust import paths in a hook file for plugin location.

    source_type: 'hooks_dir' for P:/.claude/hooks/ files
                 'fact_guard' for P:/packages/fact-guard/ files
    """
    lines = content.split("\n")
    new_lines = []
    skip_next = False
    inserted_plugin_header = False

    # Plugin header to insert at the top (after shebang/docstring)
    plugin_header = """
# --- cc-aca-epistemic plugin path setup ---
import sys as _sys
from pathlib import Path as _Path
_PLUGIN_LIB = _Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_PLUGIN_LIB) not in _sys.path:
    _sys.path.insert(0, str(_PLUGIN_LIB))
from hooks_resolver import get_hooks_dir as _get_hooks_dir
_hd = _get_hooks_dir()
if str(_hd) not in _sys.path:
    _sys.path.insert(0, str(_hd))
# --- end plugin path setup ---
"""

    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue

        # Replace HOOKS_DIR = Path(__file__).resolve().parent with plugin-aware version
        if re.match(r'^\s*HOOKS_DIR\s*=\s*Path\(__file__\)\.resolve\(\)\.parent\s*$', line):
            new_lines.append('HOOKS_DIR = _get_hooks_dir()  # resolved via plugin hooks_resolver')
            continue

        # Replace sys.path.insert(0, str(HOOKS_DIR)) — already handled by plugin header
        if re.match(r'^\s*sys\.path\.insert\(0,\s*str\(HOOKS_DIR\)\)\s*$', line):
            continue  # skip, plugin header handles this

        # Replace sys.path.insert(0, str(Path(__file__).parent / "__lib"))
        if re.match(r'^\s*sys\.path\.insert\(0,\s*str\(Path\(__file__\)\.parent\s*/\s*"__lib"\)\)\s*$', line):
            # Already handled by plugin header (hooks dir has __lib)
            continue

        # Replace sys.path.insert(0, str(Path(__file__).parent))
        if re.match(r'^\s*sys\.path\.insert\(0,\s*str\(Path\(__file__\)\.parent\)\)\s*$', line):
            continue  # skip, plugin header handles this

        # Replace sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))
        if re.match(r'^\s*sys\.path\.insert\(0,\s*str\(Path\(__file__\)\.parent\.parent\s*/\s*"__lib"\)\)\s*$', line):
            continue

        # Replace sys.path.insert(0, str(hook_dir / "src"))  (fact-guard pattern)
        if re.match(r'^\s*sys\.path\.insert\(0,\s*str\(hook_dir\s*/\s*"src"\)\)\s*$', line):
            continue  # fact-guard src modules now in plugin lib/

        # Skip hook_dir = Path(__file__).parent.parent  (fact-guard pattern)
        if re.match(r'^\s*hook_dir\s*=\s*Path\(__file__\)\.parent\.parent\s*$', line):
            continue

        # Insert plugin header before first import or after docstring
        if not inserted_plugin_header:
            # Detect first non-shebang, non-docstring, non-blank line that's an import
            if (line.startswith("import ") or line.startswith("from ") or
                (line.startswith("from __future__") and i > 0 and not lines[i-1].startswith('"""'))):
                # Check if there's a docstring above
                new_lines.append(plugin_header)
                inserted_plugin_header = True

        # Fix fact-guard imports: from fact_guard.X import Y -> from X import Y
        if source_type == "fact_guard":
            line = re.sub(r'from fact_guard\.(\w+) import', r'from \1 import', line)
            line = re.sub(r'from \.(\w+) import', r'from \1 import', line)

        new_lines.append(line)

    # If header was never inserted (no imports found), append at end of file prefix
    if not inserted_plugin_header:
        # Find end of docstring block and insert there
        for i, line in enumerate(new_lines):
            if line.strip() == '"""' and i > 0:
                # Closing triple-quote of module docstring
                new_lines.insert(i + 1, plugin_header)
                break
        else:
            new_lines.insert(0, plugin_header)

    return "\n".join(new_lines)


def adjust_core_module_paths(content: str) -> str:
    """Adjust HOOKS_DIR and state paths in core modules for plugin location."""
    # Replace HOOKS_DIR = Path(__file__).resolve().parent with resolver
    content = re.sub(
        r'^HOOKS_DIR\s*=\s*Path\(__file__\)\.resolve\(\)\.parent',
        'HOOKS_DIR = _get_hooks_dir()',
        content,
        flags=re.MULTILINE,
    )

    # Add resolver import if HOOKS_DIR was replaced
    if '_get_hooks_dir()' in content:
        # Add import at top if not already there
        if 'from hooks_resolver import' not in content:
            # Find first import line and insert before it
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    lines.insert(i, "from hooks_resolver import get_hooks_dir as _get_hooks_dir")
                    break
            content = "\n".join(lines)

    return content


def copy_file_with_adjustments(src: Path, dst: Path, adjuster=None, source_type: str = "hooks_dir") -> bool:
    """Copy a file, optionally adjusting its content."""
    if not src.exists():
        print(f"  SKIP (not found): {src}")
        return False

    content = src.read_text(encoding="utf-8")
    if adjuster:
        if source_type:
            # Hook adjusters take (content, source_type)
            try:
                content = adjuster(content, source_type)
            except TypeError:
                content = adjuster(content)
        else:
            content = adjuster(content)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")
    print(f"  COPIED: {src.name} -> {dst.relative_to(PLUGIN_ROOT)}")
    return True


def migrate_core_modules() -> int:
    """Copy core epistemic modules to plugin lib/."""
    print("\n=== Migrating Core Modules -> lib/ ===")
    count = 0
    for name in CORE_MODULES:
        src = HOOKS_DIR / name
        dst = PLUGIN_LIB / name
        if copy_file_with_adjustments(src, dst, adjust_core_module_paths):
            count += 1
    return count


def migrate_hooks() -> int:
    """Copy hooks to plugin hooks/{phase}/."""
    total = 0

    for phase, hooks in [
        ("pretool", PRETOOL_HOOKS),
        ("stop", STOP_HOOKS),
        ("posttool", POSTTOOL_HOOKS),
        ("userpromptsubmit", USERPROMPTSUBMIT_HOOKS),
    ]:
        print(f"\n=== Migrating {phase.title()} Hooks ===")
        for name in hooks:
            src = HOOKS_DIR / name
            dst = PLUGIN_ROOT / "hooks" / phase / name
            if copy_file_with_adjustments(src, dst, adjust_hook_imports, "hooks_dir"):
                total += 1

    return total


def migrate_lib_dirs() -> int:
    """Copy verification/ and anti_sycophancy/ directories to plugin lib/."""
    print("\n=== Migrating Library Directories ===")
    count = 0
    for src_name, dst_name in LIB_DIRS.items():
        src_dir = HOOKS_DIR / src_name
        dst_dir = PLUGIN_LIB / dst_name
        if not src_dir.exists():
            print(f"  SKIP (dir not found): {src_dir}")
            continue

        dst_dir.mkdir(parents=True, exist_ok=True)
        for f in src_dir.iterdir():
            if f.suffix != ".py":
                continue
            if src_name == "anti_sycophancy" and f.name in ANTI_SYCOPHANCY_EXCLUDE:
                print(f"  EXCLUDE: {f.name} (non-epistemic)")
                continue
            if f.name == "__init__.py":
                continue  # already created
            content = f.read_text(encoding="utf-8")
            # Adjust HOOKS_DIR references in library files too
            content = adjust_core_module_paths(content)
            (dst_dir / f.name).write_text(content, encoding="utf-8")
            print(f"  COPIED: {src_name}/{f.name}")
            count += 1

    return count


def migrate_fact_guard() -> int:
    """Copy fact-guard hooks and lib modules."""
    print("\n=== Migrating Fact-Guard ===")
    count = 0

    # Hooks
    for src_rel, dst_rel in FACT_GUARD_HOOKS:
        src = FACT_GUARD_ROOT / src_rel
        dst = PLUGIN_ROOT / dst_rel
        if copy_file_with_adjustments(src, dst, adjust_hook_imports, "fact_guard"):
            count += 1

    # Lib modules
    for src_rel, dst_rel in FACT_GUARD_LIB:
        src = FACT_GUARD_ROOT / src_rel
        dst = PLUGIN_ROOT / dst_rel
        # Fact-guard lib modules need both HOOKS_DIR and import path adjustments
        if src.exists():
            content = src.read_text(encoding="utf-8")
            # Fix relative imports: from .state -> from state
            content = re.sub(r'from \.(\w+) import', r'from \1 import', content)
            # Adjust any HOOKS_DIR references
            content = adjust_core_module_paths(content)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8")
            print(f"  COPIED: {src.name} -> {dst.relative_to(PLUGIN_ROOT)}")
            count += 1
        else:
            print(f"  SKIP (not found): {src}")

    return count


def create_compatibility_wrappers() -> int:
    """Create thin wrappers in P:/.claude/hooks/ that delegate to plugin."""
    print("\n=== Creating Compatibility Wrappers ===")
    count = 0

    all_hooks = []
    for phase, hooks in [
        ("pretool", PRETOOL_HOOKS),
        ("stop", STOP_HOOKS),
        ("posttool", POSTTOOL_HOOKS),
        ("userpromptsubmit", USERPROMPTSUBMIT_HOOKS),
    ]:
        for name in hooks:
            all_hooks.append((name, phase))
    # Add fact-guard hooks
    for src_rel, _ in FACT_GUARD_HOOKS:
        all_hooks.append((Path(src_rel).name, None))

    for hook_name, phase in all_hooks:
        src = HOOKS_DIR / hook_name
        wrapper_path = src  # same location, overwrite with wrapper

        if not src.exists():
            print(f"  SKIP (source not found): {hook_name}")
            continue

        # Determine plugin path
        if phase:
            plugin_hook = f"hooks/{phase}/{hook_name}"
        elif hook_name.startswith("fact-guard_PreToolUse"):
            plugin_hook = f"hooks/pretool/{hook_name}"
        elif hook_name.startswith("fact-guard_PostToolUse"):
            plugin_hook = f"hooks/posttool/{hook_name}"
        else:
            plugin_hook = f"hooks/stop/{hook_name}"

        # Backup original
        backup = src.with_suffix(src.suffix + ".pre-epistemic")
        if not backup.exists():
            shutil.copy2(src, backup)

        # Write wrapper
        module_path = plugin_hook.replace("/", ".").replace(".py", "")
        # Use path-based import instead of dot notation
        wrapper_content = f'''#!/usr/bin/env python3
"""Compatibility wrapper — delegates to cc-aca-epistemic plugin."""
import sys
from pathlib import Path

_PLUGIN_ROOT = Path("P:/packages/cc-aca-epistemic")
_plugin_hook = _PLUGIN_ROOT / "{plugin_hook}"

# Add plugin lib to path for imports
_plugin_lib = _PLUGIN_ROOT / "lib"
if str(_plugin_lib) not in sys.path:
    sys.path.insert(0, str(_plugin_lib))

import importlib.util
_spec = importlib.util.spec_from_file_location("{module_path}", _plugin_hook)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

if hasattr(_mod, "main"):
    main = _mod.main
elif hasattr(_mod, "run"):
    main = _mod.run
'''

        wrapper_path.write_text(wrapper_content, encoding="utf-8")
        print(f"  WRAPPER: {hook_name}")
        count += 1

    return count


def create_hooks_json() -> None:
    """Create hooks.json registration manifest."""
    print("\n=== Creating hooks.json ===")

    hooks = []

    # PreToolUse hooks
    for name in PRETOOL_HOOKS:
        hooks.append({
            "matcher": "PreToolUse",
            "hooks": [{"type": "command", "command": f'python "$CLAUDE_PLUGIN_ROOT/hooks/pretool/{name}"'}]
        })
    hooks.append({
        "matcher": "PreToolUse",
        "hooks": [{"type": "command", "command": 'python "$CLAUDE_PLUGIN_ROOT/hooks/pretool/fact-guard_PreToolUse.py"'}]
    })

    # PostToolUse hooks
    for name in POSTTOOL_HOOKS:
        hooks.append({
            "matcher": "PostToolUse",
            "hooks": [{"type": "command", "command": f'python "$CLAUDE_PLUGIN_ROOT/hooks/posttool/{name}"'}]
        })
    hooks.append({
        "matcher": "PostToolUse",
        "hooks": [{"type": "command", "command": 'python "$CLAUDE_PLUGIN_ROOT/hooks/posttool/fact-guard_PostToolUse.py"'}]
    })

    # Stop hooks
    for name in STOP_HOOKS:
        hooks.append({
            "matcher": "Stop",
            "hooks": [{"type": "command", "command": f'python "$CLAUDE_PLUGIN_ROOT/hooks/stop/{name}"'}]
        })

    # UserPromptSubmit hooks
    for name in USERPROMPTSUBMIT_HOOKS:
        hooks.append({
            "matcher": "UserPromptSubmit",
            "hooks": [{"type": "command", "command": f'python "$CLAUDE_PLUGIN_ROOT/hooks/userpromptsubmit/{name}"'}]
        })

    import json
    hooks_json = {"hooks": hooks}
    dst = PLUGIN_ROOT / "hooks" / "hooks.json"
    dst.write_text(json.dumps(hooks_json, indent=2) + "\n", encoding="utf-8")
    print(f"  CREATED: hooks/hooks.json ({len(hooks)} hook entries)")


def verify_migration() -> None:
    """Verify all expected files exist in the plugin."""
    print("\n=== Verification ===")
    missing = []
    found = 0

    for name in CORE_MODULES:
        p = PLUGIN_LIB / name
        if p.exists():
            found += 1
        else:
            missing.append(f"lib/{name}")

    for name in PRETOOL_HOOKS:
        p = PLUGIN_ROOT / "hooks/pretool" / name
        if p.exists():
            found += 1
        else:
            missing.append(f"hooks/pretool/{name}")

    for name in STOP_HOOKS:
        p = PLUGIN_ROOT / "hooks/stop" / name
        if p.exists():
            found += 1
        else:
            missing.append(f"hooks/stop/{name}")

    for name in POSTTOOL_HOOKS:
        p = PLUGIN_ROOT / "hooks/posttool" / name
        if p.exists():
            found += 1
        else:
            missing.append(f"hooks/posttool/{name}")

    for name in USERPROMPTSUBMIT_HOOKS:
        p = PLUGIN_ROOT / "hooks/userpromptsubmit" / name
        if p.exists():
            found += 1
        else:
            missing.append(f"hooks/userpromptsubmit/{name}")

    # Check key infrastructure
    for p in [
        PLUGIN_ROOT / "lib/hooks_resolver.py",
        PLUGIN_ROOT / "lib/provenance.py",
        PLUGIN_ROOT / "lib/contamination.py",
        PLUGIN_ROOT / "hooks/pretool/fact-guard_PreToolUse.py",
        PLUGIN_ROOT / "hooks/posttool/fact-guard_PostToolUse.py",
        PLUGIN_ROOT / ".claude-plugin/plugin.json",
        PLUGIN_ROOT / "hooks/hooks.json",
    ]:
        if p.exists():
            found += 1
        else:
            missing.append(str(p.relative_to(PLUGIN_ROOT)))

    total = found + len(missing)
    print(f"  Found: {found}/{total}")
    if missing:
        print(f"  Missing ({len(missing)}):")
        for m in missing:
            print(f"    - {m}")
    else:
        print("  All files present!")


def main() -> int:
    args = sys.argv[1:]
    verify_only = "--verify" in args

    if verify_only:
        verify_migration()
        return 0

    print(f"Plugin root: {PLUGIN_ROOT}")
    print(f"Hooks source: {HOOKS_DIR}")
    print(f"Fact-guard source: {FACT_GUARD_ROOT}")

    total_files = 0
    total_files += migrate_core_modules()
    total_files += migrate_hooks()
    total_files += migrate_lib_dirs()
    total_files += migrate_fact_guard()

    create_hooks_json()
    wrappers = create_compatibility_wrappers()

    print(f"\n=== Summary ===")
    print(f"Files migrated to plugin: {total_files}")
    print(f"Compatibility wrappers created: {wrappers}")

    verify_migration()
    return 0


if __name__ == "__main__":
    sys.exit(main())
