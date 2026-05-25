import json
import sys

# Simulate what subprocess.run passes to the hook
test_input = {"tool_name": "Bash", "tool_input": {"command": "python -c \"print({=*60})\""}}

# This is how subprocess.run passes input (as encoded bytes)
json_str = json.dumps(test_input)
_logger.debug("JSON string being passed: %s", json_str)
print(f"DEBUG: JSON string length: {len(json_str)}", file=sys.stderr)

# Test if this JSON can be parsed back
try:
    parsed = json.loads(json_str)
    _logger.debug("Successfully parsed JSON")
    print(f"DEBUG: Parsed command: {parsed.get('tool_input', {}).get('command')}", file=sys.stderr)
except json.JSONDecodeError as e:
    _logger.debug("JSON decode error: %s", e)
