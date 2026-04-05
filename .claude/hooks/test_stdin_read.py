import json
import sys

# Test how stdin is being read
stdin_content = sys.stdin.read()
print(f"DEBUG: stdin content length: {len(stdin_content)}", file=sys.stderr)
print(f"DEBUG: stdin content: {stdin_content}", file=sys.stderr)

try:
    parsed = json.loads(stdin_content)
    print("DEBUG: Successfully parsed JSON", file=sys.stderr)
except json.JSONDecodeError as e:
    print(f"DEBUG: JSON decode error: {e}", file=sys.stderr)
    print(f"DEBUG: Error position {e.pos}: '{stdin_content[max(0, e.pos-10):e.pos+10]}'", file=sys.stderr)
