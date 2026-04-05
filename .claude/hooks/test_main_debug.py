import io
import os
import sys

# Set up environment
os.environ['PYTHON_C_VALIDATOR_ENABLED'] = 'true'

# Simulate stdin
test_json = '{"tool_name": "Bash", "tool_input": {"command": "python -c \"print({=*60})\""}}'
sys.stdin = io.StringIO(test_json)

# Now import and run the hook's main function
import PreToolUse_python_c_validator as validator

print("DEBUG: About to call main()", file=sys.stderr)
print(f"DEBUG: ENABLED = {validator.ENABLED}", file=sys.stderr)

# This will call main() which should exit with code 2
try:
    validator.main()
    print("DEBUG: main() returned (did not exit)", file=sys.stderr)
except SystemExit as e:
    print(f"DEBUG: SystemExit raised with code: {e.code}", file=sys.stderr)
    raise
