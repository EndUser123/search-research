#!/usr/bin/env python3
"""
Automated revert script for hook optimizations applied 2026-01-23.

Usage:
    python revert_optimizations.py --all              # Revert everything
    python revert_optimizations.py --tdd-eval         # Revert TDD eval only
    python revert_optimizations.py --cks-timeout      # Revert CKS timeout only
    python revert_optimizations.py --hook-timeouts    # Revert hook timeouts only
"""

import argparse
import json
from pathlib import Path

# Original values
ORIGINAL_TDD_INSTRUCTION = '''"""
════════════════════════════════════════════════════════════════════
🔴 TDD MANDATORY SKILL ACTIVATION SEQUENCE
════════════════════════════════════════════════════════════════════

STEP 1 - EVALUATE:
For each available skill, state: [skill-name] - YES/NO - [reason]

STEP 2 - ACTIVATE:
IF tdd-cycle skill is YES → Use Skill("tdd-cycle") tool NOW

STEP 3 - IMPLEMENT:
Only after Step 2 is complete, proceed with implementation.
════════════════════════════════════════════════════════════════════
""".strip()'''

OPTIMIZED_TDD_INSTRUCTION = '"TDD REQUIRED: Evaluate tdd-cycle skill. If YES, use Skill(\'tdd-cycle\') before implementing."'

ORIGINAL_CKS_TIMEOUT = "3000"
OPTIMIZED_CKS_TIMEOUT = "1500"

HOOK_TIMEOUT_CHANGES = {
    "auto_commit_hook": {"original": 30, "optimized": 10},
    "PostToolUse_drift_detector": {"original": 15, "optimized": 8},
    "SessionStart_router": {"original": 15, "optimized": 8},
    "Stop_router": {"original": 10, "optimized": 5}
}

def revert_tdd_eval():
    """Revert TDD eval message to original verbose version."""
    router_file = Path("P:/.claude/hooks/UserPromptSubmit_router.py")

    content = router_file.read_text(encoding='utf-8')

    # Replace optimized with original
    content = content.replace(
        f'instruction = {OPTIMIZED_TDD_INSTRUCTION}',
        f'instruction = {ORIGINAL_TDD_INSTRUCTION}'
    )

    router_file.write_text(content, encoding='utf-8')
    print("✅ Reverted TDD eval message to original")

def revert_cks_timeout():
    """Revert CKS timeout to original 3000ms."""
    settings_file = Path("P:/.claude/settings.json")

    with open(settings_file, encoding='utf-8') as f:
        settings = json.load(f)

    settings['env']['CKS_HOOK_TIMEOUT_MS'] = ORIGINAL_CKS_TIMEOUT

    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print(f"✅ Reverted CKS timeout: {OPTIMIZED_CKS_TIMEOUT}ms → {ORIGINAL_CKS_TIMEOUT}ms")

def revert_hook_timeouts():
    """Revert hook timeouts to original values."""
    settings_file = Path("P:/.claude/settings.json")

    with open(settings_file, encoding='utf-8') as f:
        settings = json.load(f)

    hooks = settings['hooks']
    reverted = []

    # Auto commit hook (Stop layer)
    for hook_config in hooks.get('Stop', []):
        for hook in hook_config.get('hooks', []):
            if 'auto_commit_hook' in hook.get('command', ''):
                if hook['timeout'] == HOOK_TIMEOUT_CHANGES['auto_commit_hook']['optimized']:
                    hook['timeout'] = HOOK_TIMEOUT_CHANGES['auto_commit_hook']['original']
                    reverted.append(f"auto_commit_hook: {HOOK_TIMEOUT_CHANGES['auto_commit_hook']['optimized']}s → {HOOK_TIMEOUT_CHANGES['auto_commit_hook']['original']}s")

    # Drift detector (PostToolUse layer)
    for hook_config in hooks.get('PostToolUse', []):
        for hook in hook_config.get('hooks', []):
            if 'drift_detector' in hook.get('command', ''):
                if hook['timeout'] == HOOK_TIMEOUT_CHANGES['PostToolUse_drift_detector']['optimized']:
                    hook['timeout'] = HOOK_TIMEOUT_CHANGES['PostToolUse_drift_detector']['original']
                    reverted.append(f"drift_detector: {HOOK_TIMEOUT_CHANGES['PostToolUse_drift_detector']['optimized']}s → {HOOK_TIMEOUT_CHANGES['PostToolUse_drift_detector']['original']}s")

    # SessionStart router
    for hook_config in hooks.get('SessionStart', []):
        for hook in hook_config.get('hooks', []):
            if 'SessionStart_router' in hook.get('command', ''):
                if hook['timeout'] == HOOK_TIMEOUT_CHANGES['SessionStart_router']['optimized']:
                    hook['timeout'] = HOOK_TIMEOUT_CHANGES['SessionStart_router']['original']
                    reverted.append(f"SessionStart_router: {HOOK_TIMEOUT_CHANGES['SessionStart_router']['optimized']}s → {HOOK_TIMEOUT_CHANGES['SessionStart_router']['original']}s")

    # Stop router
    for hook_config in hooks.get('Stop', []):
        for hook in hook_config.get('hooks', []):
            if hook.get('layer', '').startswith('0_stop_router'):
                if hook['timeout'] == HOOK_TIMEOUT_CHANGES['Stop_router']['optimized']:
                    hook['timeout'] = HOOK_TIMEOUT_CHANGES['Stop_router']['original']
                    reverted.append(f"Stop_router: {HOOK_TIMEOUT_CHANGES['Stop_router']['optimized']}s → {HOOK_TIMEOUT_CHANGES['Stop_router']['original']}s")

    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    if reverted:
        print("✅ Reverted hook timeouts:")
        for change in reverted:
            print(f"   {change}")
    else:
        print("⚠️  No hook timeouts needed reverting (already at original values)")

def main():
    parser = argparse.ArgumentParser(description="Revert hook optimizations")
    parser.add_argument('--all', action='store_true', help='Revert all changes')
    parser.add_argument('--tdd-eval', action='store_true', help='Revert TDD eval only')
    parser.add_argument('--cks-timeout', action='store_true', help='Revert CKS timeout only')
    parser.add_argument('--hook-timeouts', action='store_true', help='Revert hook timeouts only')

    args = parser.parse_args()

    if not any([args.all, args.tdd_eval, args.cks_timeout, args.hook_timeouts]):
        parser.print_help()
        return

    print("🔄 Hook Optimization Revert Script")
    print("=" * 50)

    try:
        if args.all or args.tdd_eval:
            revert_tdd_eval()

        if args.all or args.cks_timeout:
            revert_cks_timeout()

        if args.all or args.hook_timeouts:
            revert_hook_timeouts()

        print("\n✅ Revert complete!")
        print("\n💡 Restart Claude Code session for changes to take effect")

    except Exception as e:
        print(f"\n❌ Revert failed: {e}")
        raise

if __name__ == "__main__":
    main()
