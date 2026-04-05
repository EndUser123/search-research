#!/usr/bin/env python3
"""Fix PreToolUse_path_validator.py to check consent for all violations."""

from pathlib import Path

# Read current file
file_path = Path('P:/.claude/hooks/PreToolUse_path_validator.py')
content = file_path.read_text(encoding='utf-8')

# The old section to replace (exact match from file)
old_section = '''    if not result["is_safe"]:
        violation = result.get("violation_type")
        if violation == "CLAUDE_SENSITIVE_EDIT":
            has_consent, _, canonical_path = pre_tool_use_logic.check_claude_edit_consent(data, file_path)
            if has_consent:
                return None

            relative_hint = canonical_path.removeprefix("p:/.claude/")
            return {
                "decision": "block",
                "message": (
                    f"⚠️ SENSITIVE FILE: {canonical_path}\\n"
                    "This file is protected. To proceed, reply exactly:\\n"
                    f"approve edit {relative_hint}"
                ),
            }

        return {
            "decision": "block",
            "message": f"Path Security Violation: {violation}\\nPath: {file_path}"
        }
    return None'''

# The new section with consent check for ALL violations
new_section = '''    if not result["is_safe"]:
        violation = result.get("violation_type")

        # Check edit consent for ALL violations, not just CLAUDE_SENSITIVE_EDIT
        has_consent, consent_reason, canonical_path = pre_tool_use_logic.check_claude_edit_consent(data, file_path)
        if has_consent:
            return None

        # If no consent and it's a sensitive edit, show consent request
        if violation == "CLAUDE_SENSITIVE_EDIT":
            relative_hint = canonical_path.removeprefix("p:/.claude/")
            return {
                "decision": "block",
                "message": (
                    f"⚠️ SENSITIVE FILE: {canonical_path}\n"
                    "This file is protected. To proceed, reply exactly:\n"
                    f"approve edit {relative_hint}"
                ),
            }

        # For other violations without consent, show the violation message
        return {
            "decision": "block",
            "message": f"Path Security Violation: {violation}\nPath: {file_path}"
        }
    return None'''

if old_section in content:
    updated_content = content.replace(old_section, new_section)
    file_path.write_text(updated_content, encoding='utf-8')
    print("✅ Successfully updated PreToolUse_path_validator.py")
    print("The file now checks edit consent for ALL violations, not just CLAUDE_SENSITIVE_EDIT")
else:
    print("❌ Pattern not found - file may have already been modified")
    # Show current content around the target area for debugging
    idx = content.find('if not result["is_safe"]')
    if idx > 0:
        print("\nCurrent content:")
        print(content[idx:idx+600])
