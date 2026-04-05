#!/usr/bin/env python3
"""Batch add @hook_main decorator to hooks that are missing it."""

import re
from pathlib import Path

# High priority hooks to fix
HIGH_PRIORITY = [
    "P:/.claude/hooks/PostToolUse/task_contract_generator.py",
    "P:/.claude/hooks/PostToolUse_code_verification_gate.py",
    "P:/.claude/hooks/PostToolUse_falsification_assessor.py",
    "P:/.claude/hooks/PostToolUse_hook_protection_gate.py",
    "P:/.claude/hooks/PostToolUse_next_command_suggester.py",
    "P:/.claude/hooks/PreToolUse/contract_enforcer.py",
    "P:/.claude/hooks/PreToolUse_hook_protection_gate.py",
    "P:/.claude/hooks/PreToolUse_syntax_gate.py",
    "P:/.claude/hooks/Stop/contract_validator.py",
    "P:/.claude/hooks/StopHook_cross_validator.py",
    "P:/.claude/hooks/checkpoint/PreCompact_checkpoint_capture.py",
    "P:/.claude/hooks/post_tool_use_change_propagation.py",
    "P:/.claude/hooks/pre_generation_registry.py",
    "P:/.claude/hooks/pretooluse_tdd_gate.py",
    "P:/.claude/hooks/Stop_cks_decision_capture.py",
    "P:/.claude/hooks/repositories/doc_cks_ingester.py",
]

# Medium priority
MEDIUM_PRIORITY = [
    "P:/.claude/hooks/PostToolUse/contract_tracker.py",
    "P:/.claude/hooks/PreToolUse_write_router.py",
    "P:/.claude/hooks/Stop_router.py",
]

ALL_HOOKS = HIGH_PRIORITY + MEDIUM_PRIORITY


def add_hook_main_decorator(file_path: Path) -> tuple[bool, str]:
    """Add @hook_main decorator to a hook file.

    Returns: (success, message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    content = file_path.read_text(encoding="utf-8")

    # Skip if already has @hook_main
    if "@hook_main" in content:
        return True, "Already has @hook_main"

    # Find the main() function definition
    main_pattern = r"^def main\s*\([^)]*\)\s*(?:->.*?)?:"
    match = re.search(main_pattern, content, re.MULTILINE)

    if not match:
        return False, "No main() function found"

    # Check if there's already an import for hook_base
    has_import = (
        "from __lib.hook_base import" in content
        or "from __lib import hook_base" in content
    )

    # Find the position to insert
    main_pos = match.start()

    # Add the decorator before main()
    # First, determine proper indentation (should be at column 0 for module-level main)
    lines = content[:main_pos].split("\n")
    last_line = lines[-1] if lines else ""
    indent = len(last_line) - len(last_line.lstrip())

    # Build the insertion
    if not has_import:
        # Find a good place to add the import - after other imports or at start of hook section
        # Look for the last import statement
        import_section_end = 0
        for m in re.finditer(r"^(?:from|import)\s+.+$", content, re.MULTILINE):
            import_section_end = max(import_section_end, m.end())

        if import_section_end > 0:
            # Add import after existing imports
            import_line = "\n\n# Import auto-logging decorator\nfrom __lib.hook_base import hook_main\n"
            content = (
                content[:import_section_end]
                + import_line
                + content[import_section_end:]
            )
            # Recalculate main position
            match = re.search(main_pattern, content, re.MULTILINE)
            main_pos = match.start()
        else:
            # Add at the very beginning after shebang/docstring
            import_line = "from __lib.hook_base import hook_main\n\n"
            # Find end of docstring or shebang
            doc_end = 0
            if content.startswith("#!"):
                doc_end = content.find("\n") + 1
            elif content.startswith('"""') or content.startswith("'''"):
                quote = content[:3]
                end_quote = content.find(quote, 3)
                if end_quote > 0:
                    doc_end = end_quote + 3
            content = content[:doc_end] + "\n" + import_line + content[doc_end:]
            match = re.search(main_pattern, content, re.MULTILINE)
            main_pos = match.start()

    # Add @hook_main decorator
    decorator = " " * indent + "@hook_main\n"
    content = content[:main_pos] + decorator + content[main_pos:]

    # Write back
    file_path.write_text(content, encoding="utf-8")
    return True, "Added @hook_main decorator"


def main():
    print("=" * 70)
    print("BATCH ADDING @hook_main DECORATOR")
    print("=" * 70)

    success = []
    failed = []

    for hook_path in ALL_HOOKS:
        path = Path(hook_path)
        ok, msg = add_hook_main_decorator(path)

        if ok:
            success.append((hook_path, msg))
            print(f"✅ {path.name}: {msg}")
        else:
            failed.append((hook_path, msg))
            print(f"❌ {path.name}: {msg}")

    print("\n" + "=" * 70)
    print(f"SUMMARY: {len(success)} succeeded, {len(failed)} failed")
    print("=" * 70)

    if failed:
        print("\nFailed hooks need manual attention:")
        for path, msg in failed:
            print(f"  - {path}: {msg}")


if __name__ == "__main__":
    main()
