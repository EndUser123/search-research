#!/usr/bin/env python
"""List remaining high-severity outdated packages"""
import json
import subprocess

result = subprocess.run(
    ["pip", "list", "--outdated", "--format=json"],
    check=False, capture_output=True,
    text=True
)

outdated = json.loads(result.stdout)
high_severity = []

for pkg in outdated:
    current = pkg["version"].split(".")[0]
    latest = pkg["latest_version"].split(".")[0]
    if current != latest:
        high_severity.append(
            f"{pkg['name']}: {pkg['version']} → {pkg['latest_version']} [MAJOR]"
        )

print("\n".join(high_severity[:15]))
print(f"\n... and {len(high_severity) - 15} more" if len(high_severity) > 15 else "")
print(f"\nTotal high-severity: {len(high_severity)}")
