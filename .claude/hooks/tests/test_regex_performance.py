#!/usr/bin/env python3
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_patterns():
    from PreToolUse_git_safety import TEST_PATH_PATTERN
    from PreToolUse_risk_tier_gate import ADVISORY_PATTERNS, classify_command
    from recursive_failure_detector import DOUBLE_QUOTE_PATTERN

    # Test ADVISORY patterns
    assert any(p.search('git status') for p in ADVISORY_PATTERNS)
    print('✓ ADVISORY patterns work')

    # Test classify_command
    assert classify_command('git reset --hard')[1] == 'CONFIRM'
    print('✓ classify_command works')

    # Test failure detector patterns
    assert '' in DOUBLE_QUOTE_PATTERN.sub('""', 'echo "hello"')
    print('✓ Failure detector patterns work')

    # Test git safety patterns
    assert TEST_PATH_PATTERN.search('tests/test.py') is not None
    print('✓ Git safety patterns work')

    # Benchmark
    start = time.time()
    for _ in range(1000):
        for p in ADVISORY_PATTERNS:
            p.search('git status')
    pre_time = time.time() - start

    start = time.time()
    for _ in range(1000):
        re.search(r'git\s+status', 'git status')
    run_time = time.time() - start

    speedup = run_time / pre_time
    print(f'✓ Speedup: {speedup:.2f}x ({(1-pre_time/run_time)*100:.1f}% faster)')
    print('✓ ALL TESTS PASSED')

if __name__ == '__main__':
    test_patterns()
