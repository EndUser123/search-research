#!/usr/bin/env python3
"""Analyze hook environment for drift and optimization opportunities."""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Computed project root (Python 3.12+)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
def analyze_hooks():
    settings = json.loads(PROJECT_ROOT / ".claude" / "settings.json".read_text())
    hooks_dir = PROJECT_ROOT / ".claude" / "hooks"

    print('=' * 70)
    print('HOOK ENVIRONMENT ANALYSIS')
    print(f'Generated: {datetime.now().isoformat()}')
    print('=' * 70)

    # === SECTION 1: Registered Hooks Analysis ===
    print('\n## 1. REGISTERED HOOKS BY EVENT\n')

    hooks_by_event = defaultdict(list)
    total_timeout = 0
    critical_count = 0
    all_registered = []

    for event_type, matchers in settings.get('hooks', {}).items():
        event_timeout = 0
        for matcher_entry in matchers:
            for hook in matcher_entry.get('hooks', []):
                timeout = hook.get('timeout', 5)
                critical = hook.get('critical', False)
                layer = hook.get('layer', 'unknown')
                cmd = hook.get('command', '')
                py_file = cmd.split('/')[-1].split()[0] if '.py' in cmd else cmd[:30]

                hooks_by_event[event_type].append({
                    'file': py_file,
                    'layer': layer,
                    'timeout': timeout,
                    'critical': critical,
                    'matcher': matcher_entry.get('matcher', '.*')
                })
                all_registered.append((event_type, py_file))
                event_timeout += timeout
                if critical:
                    critical_count += 1

        total_timeout += event_timeout

    print(f"{'Event Type':<20} | {'Hooks':>5} | {'Timeout':>8} | {'Critical':>8}")
    print('-' * 55)
    for event, hooks in sorted(hooks_by_event.items()):
        total_t = sum(h['timeout'] for h in hooks)
        crit = sum(1 for h in hooks if h['critical'])
        print(f"{event:<20} | {len(hooks):>5} | {total_t:>6}s  | {crit:>8}")

    total_hooks = sum(len(h) for h in hooks_by_event.values())
    print('-' * 55)
    print(f"{'TOTAL':<20} | {total_hooks:>5} | {total_timeout:>6}s  | {critical_count:>8}")

    # === SECTION 2: Stop Hooks (Critical Path) ===
    print('\n## 2. STOP HOOKS (Critical Validation Path)\n')

    stop_hooks = hooks_by_event.get('Stop', [])
    for h in sorted(stop_hooks, key=lambda x: x['layer']):
        crit = '[CRITICAL]' if h['critical'] else ''
        print(f"  {h['layer']:<35} {h['file']:<35} {crit}")

    # === SECTION 3: File Inventory ===
    print('\n## 3. FILE INVENTORY\n')

    py_files = set(f.name for f in hooks_dir.glob('*.py')
                   if not f.name.startswith('_') and f.name != '__init__.py')
    registered_files = set(f for _, f in all_registered)

    unregistered = py_files - registered_files
    archived_count = len(list(hooks_dir.glob('_archive_v1/*.py')))

    print(f"  Python files in hooks/: {len(py_files)}")
    print(f"  Registered hooks: {len(registered_files)}")
    print(f"  Unregistered files: {len(unregistered)}")
    print(f"  Archived files: {archived_count}")

    # === SECTION 4: Multi-Registration Check ===
    print('\n## 4. MULTI-REGISTRATION CHECK\n')

    file_events = defaultdict(list)
    for event, f in all_registered:
        file_events[f].append(event)

    multi = [(f, events) for f, events in file_events.items() if len(events) > 1]
    if multi:
        print("  Hooks registered for multiple events:")
        for f, events in multi:
            print(f"    {f}: {', '.join(events)}")
    else:
        print("  No multi-event registrations found.")

    # === SECTION 5: Unregistered Files Analysis ===
    print('\n## 5. UNREGISTERED FILES (potential bloat)\n')

    # Categorize unregistered files
    categories = {
        'debug/test': [],
        'observability': [],
        'utilities': [],
        'validators': [],
        'other': []
    }

    for f in sorted(unregistered):
        f_lower = f.lower()
        if 'test' in f_lower or 'debug' in f_lower:
            categories['debug/test'].append(f)
        elif 'obs' in f_lower or 'monitor' in f_lower or 'log' in f_lower:
            categories['observability'].append(f)
        elif 'util' in f_lower or 'helper' in f_lower or 'cache' in f_lower:
            categories['utilities'].append(f)
        elif 'valid' in f_lower or 'check' in f_lower or 'guard' in f_lower:
            categories['validators'].append(f)
        else:
            categories['other'].append(f)

    for cat, files in categories.items():
        if files:
            print(f"  {cat} ({len(files)}):")
            for f in files[:5]:
                print(f"    - {f}")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")

    # === SECTION 6: Critical Path Analysis ===
    print('\n## 6. CRITICAL PATH (What actually enforces our rules?)\n')

    enforcement_hooks = [
        ('execution_evidence_gate.py', 'Stop', 'PART L - Blocks success claims without execution'),
        ('constitutional_enforcer.py', 'Stop', 'Parts A,C,L - Sycophancy, excuses, hyperbole'),
        ('command_execution_validator.py', 'Stop', 'Validates slash commands executed'),
        ('tool_sequence_tracker.py', 'PostToolUse', 'Tracks tools for evidence gate'),
        ('goal_anchor.py', 'UserPromptSubmit', 'Injects goal context'),
        ('pre_tool_use.py', 'PreToolUse', 'TDD enforcement'),
    ]

    print("  Core enforcement hooks:")
    for hook, event, purpose in enforcement_hooks:
        registered = hook in registered_files
        status = '✅' if registered else '❌'
        print(f"    {status} {hook:<35} ({event})")
        print(f"       {purpose}")

    # === SECTION 7: Recommendations ===
    print('\n## 7. DRIFT ASSESSMENT\n')

    issues = []

    # Check hook count vs design principle
    if total_hooks > 20:
        issues.append(f"Hook count ({total_hooks}) exceeds design target (~6-10)")

    if total_timeout > 30:
        issues.append(f"Worst-case timeout ({total_timeout}s) may cause latency")

    if len(unregistered) > 20:
        issues.append(f"Many unregistered files ({len(unregistered)}) - potential cruft")

    # Check for success_validator in wrong place
    if 'success_validator.py' in registered_files:
        issues.append("success_validator.py registered but should be archived (merged into constitutional_enforcer)")

    if issues:
        print("  ⚠️  Issues detected:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✅ No major drift issues detected")

    print('\n## 8. OPTIMAL ARCHITECTURE (Recommended)\n')
    print("""
  Minimal Viable Hook Set (6 hooks):
  
  UserPromptSubmit:
    1. goal_anchor.py [CRITICAL] - Goal extraction + solo-dev context
    
  PreToolUse:
    2. pre_tool_use.py [CRITICAL] - TDD enforcement, path protection
    
  PostToolUse:
    3. tool_sequence_tracker.py - Tracks tools for Stop validation
    
  Stop:
    4. execution_evidence_gate.py [CRITICAL] - PART L structural enforcement
    5. constitutional_enforcer.py [CRITICAL] - Unified rule validation
    
  Optional (high-value):
    6. command_directive_injector.py - Slash command enforcement
    7. subagent_constitution_injector.py - Subagent compliance
    """)

    return {
        'total_hooks': total_hooks,
        'critical_hooks': critical_count,
        'unregistered': len(unregistered),
        'issues': issues
    }


if __name__ == '__main__':
    result = analyze_hooks()

    print('=' * 70)
    print('SUMMARY')
    print('=' * 70)
    print(f"  Registered: {result['total_hooks']} hooks ({result['critical_hooks']} critical)")
    print(f"  Unregistered files: {result['unregistered']}")
    print(f"  Issues found: {len(result['issues'])}")
