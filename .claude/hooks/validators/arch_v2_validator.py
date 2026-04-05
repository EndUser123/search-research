# hooks/validators/arch_v2_validator.py
import os
import re
import sys


def validate_arch_output(filepath):
    # 1. Read the file content
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"FAIL: Could not read output file {filepath}: {e}")
        sys.exit(1)

    # 2. Define the 13 Mandatory Artifacts (Patterns)
    # We look for Case-Insensitive Headers
    required_sections = [
        (r"MENTAL MODEL APPLICATION", "Mental Model Application"),
        (r"PRE-MORTEM ANALYSIS", "Pre-Mortem Analysis"),
        (r"RISK MATRIX", "Risk Matrix"),
        (r"FORCED ALTERNATIVES", "Forced Alternatives"),
        (r"ROLLBACK PLAN", "Rollback Plan"),
        (r"TECH DEBT ESTIMATION", "Tech Debt Estimation"),
        (r"TIMELINE ESTIMATION", "Timeline Estimation"),
        (r"CONSTITUTIONAL COMPLIANCE", "Constitutional Compliance"),
        (r"AUTO-DRAFT ADR", "Auto-Draft ADR"),
        (r"CWO COGNITIVE CHECKLIST", "CWO Cognitive Checklist"),
        (r"CKS KNOWLEDGE HANDOFF", "CKS Knowledge Handoff"),
        (r"CONFIDENCE CALIBRATION", "Confidence Calibration"),
        (r"ADVERSARIAL CHALLENGE", "Adversarial Challenge")
    ]

    missing = []

    # 3. Check for each section
    for pattern, name in required_sections:
        # We look for the pattern allowing for some markdown noise (##, **, [])
        # Regex: (Line Start) (Opt #/*/-) (Opt [) (Opt "1. ") PATTERN (Opt ])
        # We allow for: ## 1. Pattern, **Pattern**, [Pattern]
        regex = r"(?i)^[\#\*\s-]*\[?[\s\d\.]*" + pattern + r"[\s]*\]?"

        if not re.search(regex, content, re.MULTILINE):
            missing.append(name)

    # 4. Feedback Loop
    if missing:
        print(f"FAIL: Incomplete Architecture Analysis. Missing {len(missing)} mandatory artifacts.")
        print("MISSING SECTIONS:")
        for m in missing:
            print(f" - {m}")
        print("\nACTION REQUIRED: You MUST generate these missing sections to complete the analysis.")
        sys.exit(1)

    # 5. Quality/Constraint Checks (Optional deep validation)
    # Example: Check if Risk Score is actually a number?
    # For now, presence is the primary gate.

    # 6. Success
    print(f"PASS: All 13/13 Mandatory Artifacts present in {os.path.basename(filepath)}.")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python arch_v2_validator.py <filepath>")
        sys.exit(1)

    target = sys.argv[1]
    validate_arch_output(target)
