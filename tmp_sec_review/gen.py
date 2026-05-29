import json, os
out = r"P:\\.claude\\.artifacts\\console_a34a525e-5ffc-402d-89d7-adb1f388c588\\pre-mortem\\pre-mortem-20260526_112221\\specialists\\adversarial-security-findings.json"
with open(out, "r", encoding="utf-8") as fh:
    data = json.load(fh)
findings = []
