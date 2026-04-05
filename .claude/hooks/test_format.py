import json

from assumption_audit_v2 import format_hook_output

print("Testing format_hook_output after fix:")
print("allow -> approve:")
result = format_hook_output("allow", "TEST")
print(result)
parsed = json.loads(result)
print(f"  decision value: {parsed['decision']}")
print(f"  Matches schema? {parsed['decision'] in ['approve', 'block']}")

print("\nblock -> block:")
result = format_hook_output("block", "TEST", message="Blocked message")
print(result)
parsed = json.loads(result)
print(f"  decision value: {parsed['decision']}")
print(f"  Matches schema? {parsed['decision'] in ['approve', 'block']}")
