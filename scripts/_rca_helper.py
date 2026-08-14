import json, os
DATA = {"specialist": "adversarial-rca", "findings": [], "open_questions": ["placeholder"]}
PATH = "/p/.claude/.artifacts/DESKTOP-70TFAGN-11176/pre-mortem/pre-mortem-20260606_100157/specialists/adversarial-rca-findings.json"
os.makedirs(os.path.dirname(PATH), exist_ok=True)
with open(PATH, "w", encoding="utf-8") as f:
    json.dump(DATA, f, indent=2, ensure_ascii=False)
print("stub wrote", PATH, os.path.getsize(PATH))
