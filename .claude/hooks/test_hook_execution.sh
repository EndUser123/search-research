#!/bin/bash
# Comprehensive hook execution test with logging
LOG_FILE="P:/.claude/hooks/logs/diagnostics/hook_execution_test_$(date +%Y%m%d_%H%M%S).log"

echo "=== Hook Execution Test ===" | tee -a "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 1: Import test
echo "TEST 1: Import PreToolUse_dependency_verification_gate" | tee -a "$LOG_FILE"
cd P:/.claude/hooks
python3 -c "
import sys
print('Python version:', sys.version)
print('sys.path:', sys.path[:3])
try:
    import PreToolUse_dependency_verification_gate
    print('✓ Import successful')
    # Check if detect_terminal_id is available
    import inspect
    source = inspect.getsource(PreToolUse_dependency_verification_gate)
    if 'detect_terminal_id' in source:
        print('✓ detect_terminal_id found in source')
    else:
        print('✗ detect_terminal_id NOT found in source')
except Exception as e:
    print(f'✗ Import failed: {e}')
    import traceback
    traceback.print_exc()
" 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"

# Test 2: Check if function is actually callable
echo "TEST 2: Check detect_terminal_id function" | tee -a "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, 'P:/packages/skill-guard/src')
try:
    from skill_guard.utils.terminal_detection import detect_terminal_id
    print('✓ Can import detect_terminal_id from skill_guard')
    result = detect_terminal_id()
    print(f'✓ Function returned: {result}')
except ImportError as e:
    print(f'✗ Cannot import from skill_guard: {e}')
    print('Checking skill-guard package location...')
    import os
    skill_guard_path = 'P:/packages/skill-guard/src'
    if os.path.exists(skill_guard_path):
        print(f'✓ Path exists: {skill_guard_path}')
        files = os.listdir(skill_guard_path)
        print(f'  Contents: {files[:5]}')
    else:
        print(f'✗ Path does NOT exist: {skill_guard_path}')
except Exception as e:
    print(f'✗ Error: {e}')
" 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"

# Test 3: Verify source file has the import
echo "TEST 3: Check source file for import statement" | tee -a "$LOG_FILE"
grep -n "from skill_guard.utils.terminal_detection import detect_terminal_id" \
    "P:/.claude/hooks/PreToolUse_dependency_verification_gate.py" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"

# Test 4: Check for any .pyc files
echo "TEST 4: Check for bytecode cache files" | tee -a "$LOG_FILE"
find P:/.claude/hooks -name "*dependency_verification*.pyc" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Test Complete ===" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE"
