#!/usr/bin/env python3
"""Fix syntax errors in test files - missing closing parentheses."""
import re
from pathlib import Path

FILES_TO_FIX = [
    "tdd_core.py",
    "test_Stop_artifact_gate.py",
    "test_anti_deception.py",
    "test_assumption_audit_runner.py",
    "test_authority_check.py",
    "test_authority_check_notification.py",
    "test_command_execution_validator.py",
    "test_diagnostic_logging.py",
    "test_entity_correlation_fix.py",
    "test_g_fixes.py",
    "test_git_branch.py",
    "test_handoff_step.py",
    "test_hook_execution.py",
    "test_lint_router.py",
    "test_overconfidence_live.py",
    "test_principle_vs_patterns.py",
    "test_python_c_validator.py",
    "test_router_concern.py",
    "test_router_skill_enforcement.py",
    "test_signal_notifications.py",
    "test_skill_enforcement_flow.py",
    "test_stop_success_validator.py",
    "test_subprocess.py",
    "test_transcript_extraction.py",
    "test_userpromptsubmit_entrypoint.py",
]

hooks_dir = Path("P:/.claude/hooks")

fixed = []
failed = []

for filename in FILES_TO_FIX:
    filepath = hooks_dir / filename
    if not filepath.exists():
        print(f"SKIP: {filename} - not found")
        continue

    try:
        content = filepath.read_text()

        # Pattern 1: cwd=Path.cwd(,  -> cwd=Path.cwd(),
        content = re.sub(r'cwd=Path\.cwd\(\,', r'cwd=Path.cwd(),', content)

        # Pattern 2: [sys.executable, str(hook_path],  -> [sys.executable, str(hook_path)],
        content = re.sub(r'\[sys\.executable, str\(hook_path\],', r'[sys.executable, str(hook_path)],', content)

        # Pattern 3: Other similar patterns - function call ending with (,
        # This catches things like: function(arg,
        # where it should be: function(arg),
        content = re.sub(r'(\w+\([^\)]*),\s*\n\s*\)', r'\1),\n)', content)

        filepath.write_text(content)
        fixed.append(filename)
        print(f"FIXED: {filename}")
    except Exception as e:
        failed.append((filename, str(e)))
        print(f"FAILED: {filename} - {e}")

print(f"\nFixed: {len(fixed)}/{len(FILES_TO_FIX)}")
if failed:
    print(f"Failed: {len(failed)}")
    for f, err in failed:
        print(f"  {f}: {err}")
