import sys

# Simulate stdin input
test_json = {"tool_name": "Bash", "tool_input": {"command": "python -c \"print({=*60})\""}}

print(f"DEBUG: tool_name = {test_json.get('tool_name')}", file=sys.stderr)
print(f"DEBUG: command = {test_json.get('tool_input', {}).get('command')}", file=sys.stderr)

# Import the hook
import PreToolUse_python_c_validator as validator

print(f"DEBUG: Pattern exists = {hasattr(validator, 'PYTHON_C_PATTERN')}", file=sys.stderr)
print(f"DEBUG: Pattern = {validator.PYTHON_C_PATTERN.pattern}", file=sys.stderr)

# Test the pattern
command = test_json.get('tool_input', {}).get('command', '')
match = validator.PYTHON_C_PATTERN.search(command)
if match:
    print(f"DEBUG: Pattern matched! Groups = {match.groups()}", file=sys.stderr)
    print(f"DEBUG: Code to validate: {match.group(2)}", file=sys.stderr)
else:
    print('DEBUG: Pattern did NOT match', file=sys.stderr)
