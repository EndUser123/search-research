import json
import sys

# Simulate what subprocess.run passes to the hook
test_input = {"tool_name": "Bash", "tool_input": {"command": "python -c \"print({=*60})\""}}

# This is how subprocess.run passes input (as encoded bytes)
json_str = json.dumps(test_input)
print(f"DEBUG: JSON string being passed: {json_str}", file=sys.stderr)
print(f"DEBUG: JSON string length: {len(json_str)}", file=sys.stderr)

# Test if this JSON can be parsed back
try:
    parsed = json.loads(json_str)
    print("DEBUG: Successfully parsed JSON", file=sys.stderr)
    print(f"DEBUG: Parsed command: {parsed.get('tool_input', {}).get('command')}", file=sys.stderr)
except json.JSONDecodeError as e:
    print(f"DEBUG: JSON decode error: {e}", file=sys.stderr)
