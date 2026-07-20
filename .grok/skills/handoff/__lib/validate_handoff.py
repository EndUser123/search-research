"""Smoke-test validator: run validators on a handoff file and print results."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

from validators import validate_handoff_file, is_valid  # noqa: E402

if len(sys.argv) < 2:
    print("usage: python validate_handoff.py <path>", file=sys.stderr)
    sys.exit(2)

path = sys.argv[1]
text = Path(path).read_text(encoding="utf-8")
issues = validate_handoff_file(path)
valid = is_valid(text)

print(f"File: {path}")
print(f"Valid (no errors): {valid}")
print(f"Total issues: {len(issues)}")
errors = [i for i in issues if i["severity"] == "error"]
warnings = [i for i in issues if i["severity"] == "warn"]
print(f"  Errors: {len(errors)}")
print(f"  Warnings: {len(warnings)}")
for i in issues:
    print(f"  [{i['severity'].upper()}] {i['field']}: {i['message']}")

sys.exit(0 if valid else 1)
