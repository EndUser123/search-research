#!/usr/bin/env python3
"""
PostToolWrite Hook: Documentation and Verification Validation

Purpose: After code changes, validate that responses follow verification-first protocol
and don't make unverified claims about functionality.

Triggers: After Edit, Write, or Bash tool execution

Anti-patterns prevented:
- "This should fix it" without testing
- "That's the optimal solution" without verification
- Assuming code works without running it
- Documentation-first instead of verification-first

Enforced Protocols (from MEMORY.md):
- Verification First Protocol: Claim → Test → Document
- Solution Proposal Gate: All 6 checkboxes before solution claims
"""

import json
import re
import sys

# Patterns indicating unverified claims after code changes
UNVERIFIED_CLAIM_PATTERNS = [
    r"(This|That|It)\s+should\s+(fix|work|solve)",
    r"This\s+is\s+the\s+(optimal|best|correct)\s+solution",
    r"Fixed\s+the\s+(issue|problem|bug)",
    r"Resolved\s+by",
    r"That\s+(should|will|ought to)\s+fix it",
]

VERIFICATION_EVIDENCE_PATTERNS = [
    r"Test(ed|ing)?\s+(with|by|via)",
    r"Ran?\s+(the\s+)?test",
    r"Output\s+(shows|is|was)",
    r"Confirmed\s+that",
    r"Verified\s+(by|with)",
    r"Result\s+(was|is|shows)",
]

def validate_post_tool_write(tool_name: str, tool_params: dict, response_text: str) -> dict:
    """
    Validate response after tool execution for verification protocol compliance.

    Returns dict with:
    - valid: bool
    - errors: list of violation messages
    - suggestions: list of corrective actions
    """
    errors = []
    suggestions = []

    # Only check code-modifying tools
    if tool_name not in ["Edit", "Write", "Bash"]:
        return {"valid": True, "errors": [], "suggestions": []}

    # Check for unverified claims
    for pattern in UNVERIFIED_CLAIM_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            # Look for verification evidence
            has_verification = any(
                re.search(vpat, response_text, re.IGNORECASE)
                for vpat in VERIFICATION_EVIDENCE_PATTERNS
            )

            if not has_verification:
                errors.append("Unverified claim after code change")
                suggestions.append("Test the change before claiming it works")

    # Check for "optimal solution" claims without gate checklist
    if re.search(r"optimal\s+solution", response_text, re.IGNORECASE):
        # Check if Solution Proposal Gate was passed
        gate_checks = [
            "root cause" in response_text.lower(),
            any(re.search(p, response_text, re.IGNORECASE) for p in VERIFICATION_EVIDENCE_PATTERNS),
            "test" in response_text.lower() or "verified" in response_text.lower(),
        ]

        if not all(gate_checks):
            errors.append("'Optimal solution' claim without Solution Proposal Gate")
            suggestions.append("Complete all 6 Solution Proposal Gate checkboxes")

    # Check for "I think" or "probably" in conclusions
    if re.search(r"(I think|Probably|Likely)(?!.{0,100}test)", response_text, re.IGNORECASE):
        # Make sure it's not followed by testing evidence
        has_nearby_test = False
        for match in re.finditer(r"(I think|Probably|Likely)", response_text, re.IGNORECASE):
            context = response_text[match.end():match.end()+200]
            if any(re.search(p, context, re.IGNORECASE) for p in VERIFICATION_EVIDENCE_PATTERNS):
                has_nearby_test = True
                break

        if not has_nearby_test:
            errors.append("Uncertain claim without verification")
            suggestions.append("Replace 'I think' with test output")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "suggestions": suggestions
    }

def main():
    """
    PostToolWrite hook entry point.

    Read stdin for tool result JSON, validate response, exit with error code if invalid.
    """
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Not JSON - skip validation
        sys.exit(0)

    # Extract tool info
    tool_name = input_data.get("tool", "")
    tool_params = input_data.get("parameters", {})
    response_text = input_data.get("response", "")

    if not tool_name or not response_text:
        sys.exit(0)

    # Validate response
    result = validate_post_tool_write(tool_name, tool_params, response_text)

    if not result["valid"]:
        # Validation failed - show warnings (non-blocking)
        print("## VERIFICATION PROTOCOL REMINDER", file=sys.stderr)
        print(f"\nTool: {tool_name}", file=sys.stderr)

        print(f"\nIssues Found: {len(result['errors'])}", file=sys.stderr)
        for i, error in enumerate(result["errors"], 1):
            print(f"  {i}. {error}", file=sys.stderr)

        print("\nSuggestions:", file=sys.stderr)
        for i, suggestion in enumerate(result["suggestions"], 1):
            print(f"  {i}. {suggestion}", file=sys.stderr)

        print("\n📚 See MEMORY.md protocols:", file=sys.stderr)
        print("  - Verification First Protocol", file=sys.stderr)
        print("  - Solution Proposal Gate", file=sys.stderr)

        # Non-blocking - just warn, don't stop execution
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
