"""Pre-mortem validation utilities.

Ensures pre-mortem output meets quality standards and enforces
structural requirements like action-to-priority mapping.
"""

from __future__ import annotations

import re
from typing import Any


def validate_action_mapping(pre_mortem_output: str) -> tuple[bool, list[str]]:
    """Validate that every TOP PRIORITY has a corresponding recommended action.

    Args:
        pre_mortem_output: The pre-mortem output text to validate

    Returns:
        (is_valid, errors): Validation result and list of error messages
    """
    errors = []

    # Extract TOP PRIORITIES section
    priorities = _extract_top_priorities(pre_mortem_output)
    priority_count = len(priorities)

    # Extract Recommended Next Steps section
    actions = _extract_recommended_actions(pre_mortem_output)
    action_count = len(actions)

    # Validate mapping
    if action_count < priority_count:
        errors.append(
            f"Action mapping incomplete: {action_count} actions for {priority_count} top priorities. "
            f"Each RISK≥6 priority must have a specific mitigation."
        )

    # Validate action specificity (reject generic actions)
    generic_actions = _detect_generic_actions(actions)
    if generic_actions:
        errors.append(
            f"Generic actions detected: {', '.join(generic_actions)}. "
            f"Actions must be specific to the risk (e.g., 'Add ImportError handling' not 'improve testing')."
        )

    return (len(errors) == 0, errors)


def _extract_top_priorities(output: str) -> list[dict[str, Any]]:
    """Extract TOP PRIORITIES (RISK ≥ 6) from pre-mortem output.

    Looks for patterns like:
    - 🔴 RISK:9 - [Failure description]
    - 🟡 RISK:6 - [Failure description]
    - RISK:9 - [Failure description] (emoji optional)
    - Risk: 9 - [Failure description] (case flexible)
    - [RISK 9] [Failure description] (alternative format)

    PM-004 FIX: Made regex more flexible to handle user variations.
    """
    priorities = []
    # Multiple patterns to handle different user formats
    patterns = [
        # Original: emoji + RISK:N - description
        r"[🔴🟡]\s*RISK:(\d+)\s*-\s*(.+?)(?=\n|$)",
        # Emoji optional + case insensitive
        r"[🔴🟡]?\s*risk[:\s]+(\d+)\s*[-:—–]\s*(.+?)(?=\n|$)",
        # Bracket format: [RISK N] or [Risk N]
        r"\[?\s*[Rr]isk\s*[:\s]\s*(\d+)\s*\]?\s*[-:—–]?\s*(.+?)(?=\n|$)",
        # ID format: TECH-001 | Risk 9
        r"\w+-\d+\s*\|\s*[Rr]isk\s*[:\s]\s*(\d+)\s*[-:—–]?\s*(.+?)(?=\n|$)",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, output, re.IGNORECASE):
            risk_score = int(match.group(1))
            if risk_score >= 6:
                description = match.group(2).strip()
                # Avoid duplicates across patterns
                if not any(p["description"] == description for p in priorities):
                    priorities.append({"risk_score": risk_score, "description": description})

    return priorities


def _extract_recommended_actions(output: str) -> list[str]:
    """Extract recommended actions from pre-mortem output.

    Looks for patterns like:
    - 1a: [Action name] → [Skill suggestion]
    - 1b: [Alternative action] → [Alternative skill]
    """
    actions = []
    action_pattern = r"\s+[0-9]+[a-z]:\s*(.+?)\s*→"

    for match in re.finditer(action_pattern, output):
        action = match.group(1).strip()
        actions.append(action)

    return actions


def _detect_generic_actions(actions: list[str]) -> list[str]:
    """Detect generic non-specific actions.

    Generic patterns that don't address specific risks:
    - "Add tests"
    - "Improve testing"
    - "Add documentation"
    - "Review code"
    - "Monitor performance"

    Extended patterns (v4.6) - 10+ additional patterns:
    - "Refactor code" - too broad, no specific target
    - "Optimize performance" - what specifically?
    - "Handle errors" - which errors?
    - "Add validation" - what validation?
    - "Fix bugs" - which bugs?
    - "Improve security" - too vague
    - "Update dependencies" - which ones?
    - "Clean up code" - what needs cleaning?
    - "Add comments" - where and why?
    - "Improve error handling" - generic
    - "Add logging" - where and what?
    - "Refactor" - single word, too broad
    - "Optimize" - single word, too broad
    - "Fix" - single word, too broad
    """
    generic_patterns = [
        # Original 7 patterns
        r"^add tests?$",
        r"^improve testing$",
        r"^add documentation$",
        r"^review code$",
        r"^monitor performance$",
        r"^write tests?$",
        r"^add logging$",
        # Extended patterns (v4.6)
        r"^refactor code$",
        r"^optimize performance$",
        r"^handle errors$",
        r"^add validation$",
        r"^fix bugs$",
        r"^improve security$",
        r"^update dependencies$",
        r"^clean up code$",
        r"^add comments$",
        r"^improve error handling$",
        r"^refactor$",
        r"^optimize$",
        r"^fix$",
    ]

    generic_actions = []
    for action in actions:
        action_lower = action.lower()
        for pattern in generic_patterns:
            if re.match(pattern, action_lower):
                generic_actions.append(action)
                break

    return generic_actions


def _get_action_context(action: str) -> str:
    """Provide contextual feedback for generic actions.

    Helps users understand why an action is generic and how to make it specific.

    Args:
        action: The generic action detected

    Returns:
        Context string explaining why this action is generic and how to fix it
    """
    action_lower = action.lower()

    context_map = {
        "add tests": "Tests must target specific risks (e.g., 'Add ImportError handling for auth.py')",
        "improve testing": "Specify what aspect needs testing (e.g., 'Add edge case tests for user login timeout')",
        "add documentation": "Document what specifically (e.g., 'Document JWT validation flow in SKILL.md')",
        "review code": "Which code? (e.g., 'Review session_manager.py for race conditions')",
        "monitor performance": "What metric? (e.g., 'Add response time monitoring for /search endpoint')",
        "write tests": "Same as 'add tests' - be specific about what's being tested",
        "add logging": "Where and what? (e.g., 'Add debug logging to handoff chain imports')",
        "refactor code": "What needs refactoring? (e.g., 'Extract hardcoded config to constants.py')",
        "optimize performance": "What bottleneck? (e.g., 'Cache repeated API calls in get_predictions()')",
        "handle errors": "Which errors? (e.g., 'Add try-except for FileNotFoundError in load_config()')",
        "add validation": "Validate what? (e.g., 'Add input validation for project names in store_prediction()')",
        "fix bugs": "Which bugs? (e.g., 'Fix off-by-one error in date parsing logic')",
        "improve security": "What vulnerability? (e.g., 'Sanitize user input before filename generation')",
        "update dependencies": "Which ones? (e.g., 'Update pytest from 8.0 to 9.0 for compatibility')",
        "clean up code": "What needs cleaning? (e.g., 'Remove unused imports in validation.py')",
        "add comments": "Where and why? (e.g., 'Add docstring to _parse_predictions_from_file()')",
        "improve error handling": "How? (e.g., 'Add specific exception types instead of bare except')",
        "refactor": "Single-word refactor - specify target and goal (e.g., 'Extract regex patterns to constants')",
        "optimize": "Single-word optimize - what bottleneck? (e.g., 'Reduce regex compilation in loop')",
        "fix": "Single-word fix - what specifically? (e.g., 'Fix path separator handling for Windows paths')",
    }

    # Find matching context
    for generic_term, context in context_map.items():
        if generic_term in action_lower:
            return f"❌ Generic: '{action}' → {context}"

    return f"❌ Generic: '{action}' → Be specific about what, where, and why"


def validate_action_mapping_with_context(
    pre_mortem_output: str,
) -> tuple[bool, list[str], list[str]]:
    """Validate action mapping and provide contextual feedback.

    Enhanced version of validate_action_mapping that includes specific feedback
    for each generic action detected.

    Args:
        pre_mortem_output: The pre-mortem output text to validate

    Returns:
        (is_valid, errors, context_messages): Validation result, errors, and contextual feedback
    """
    errors = []
    context_messages = []

    # Extract TOP PRIORITIES section
    priorities = _extract_top_priorities(pre_mortem_output)
    priority_count = len(priorities)

    # Extract Recommended Next Steps section
    actions = _extract_recommended_actions(pre_mortem_output)
    action_count = len(actions)

    # Validate mapping
    if action_count < priority_count:
        errors.append(
            f"Action mapping incomplete: {action_count} actions for {priority_count} top priorities. "
            f"Each RISK≥6 priority must have a specific mitigation."
        )

    # Validate action specificity with context
    generic_actions = _detect_generic_actions(actions)
    if generic_actions:
        for action in generic_actions:
            context_messages.append(_get_action_context(action))
        errors.append(
            f"Generic actions detected: {len(generic_actions)} actions lack specificity. "
            f"See contextual feedback below for improvement suggestions."
        )

    return (len(errors) == 0, errors, context_messages)


def validate_kill_criteria_defined(pre_mortem_output: str) -> tuple[bool, list[str]]:
    """Validate that kill criteria are defined (Step 0.7).

    Args:
        pre_mortem_output: The pre-mortem output text to validate

    Returns:
        (is_valid, errors): Validation result and list of error messages
    """
    errors = []

    # Look for kill criteria section
    kill_criteria_pattern = r"(?:Kill Criteria|Time-Based Kill Criteria|Value-Based Kill Criteria)"
    if not re.search(kill_criteria_pattern, pre_mortem_output, re.IGNORECASE):
        errors.append(
            "Kill criteria not defined (Step 0.7). "
            "Solo dev projects need pre-commit abandonment criteria to prevent sunk cost fallacy."
        )

    return (len(errors) == 0, errors)


def validate_temporal_failure_modes(pre_mortem_output: str) -> tuple[bool, list[str]]:
    """Validate temporal failure mode analysis (Step 2.7).

    Checks that:
    1. If temporal failures are discussed, there are turn-number citations
    2. Citations use format: "turn N" adjacent to temporal failure claims
    3. If no temporal failures found, that's acceptable (but must check)

    QA-006 FIX: Added validation function for Step 2.7 temporal failure modes.
    This was identified as a BLOCKER - Step 2.7 had zero validation.

    Args:
        pre_mortem_output: The pre-mortem output text to validate

    Returns:
        (is_valid, errors): Validation result and list of error messages
    """
    errors = []

    # Check if Step 2.7 section exists
    temporal_section_patterns = [
        r"Step 2\.7[:\s]",
        r"Temporal Failure",
        r"temporal failure",
    ]
    has_temporal_section = any(
        re.search(pattern, pre_mortem_output, re.IGNORECASE)
        for pattern in temporal_section_patterns
    )

    if not has_temporal_section:
        # No temporal failure analysis at all - that's a gap
        errors.append(
            "Step 2.7 (Temporal Failure Modes) not detected. "
            "Pre-mortems should analyze: LLM forgets requirements from 50+ turns ago, "
            "context window exceeded, AI contradicts earlier decision."
        )
        return (False, errors)

    # Temporal section exists - now check for turn-number citations
    # Pattern: "turn N" where N is a number, appearing near temporal claims
    temporal_claim_patterns = [
        r"(?:forgot|forgets|dropped|exceeded|contradict|forgotten)\b.*\bturn\s+\d+",
        r"\bturn\s+\d+.*(?:forgot|forgets|dropped|exceeded|contradict|forgotten)",
        r"(?:context|constraint|requirement).*?\bturn\s+\d+",
        r"\bturn\s+\d+.*(?:context|constraint|requirement)",
    ]

    # Look for turn citations near temporal keywords
    found_citation = False
    for pattern in temporal_claim_patterns:
        if re.search(pattern, pre_mortem_output, re.IGNORECASE):
            found_citation = True
            break

    # Alternative: look for standalone turn citations in Step 2.7 section
    if not found_citation:
        # Extract Step 2.7 section
        step27_match = re.search(
            r"Step 2\.7.*?(?=\n##|\n#|\Z)", pre_mortem_output, re.IGNORECASE | re.DOTALL
        )
        if step27_match:
            section_text = step27_match.group(0)
            # Check for standalone turn citations
            if re.search(r"\bturn\s+\d+", section_text, re.IGNORECASE):
                found_citation = True

    if not found_citation:
        errors.append(
            "Temporal failure analysis present but no turn-number citations found. "
            "When claiming temporal failures, cite specific turns: 'turn 47' or '#47'. "
            "This enables validation that the failure was actually detected."
        )

    return (len(errors) == 0, errors)


def validate_operational_verification(pre_mortem_output: str) -> tuple[bool, list[str]]:
    """Validate operational verification status (Step 3.8).

    Args:
        pre_mortem_output: The pre-mortem output text to validate

    Returns:
        (is_valid, warnings): Validation result and list of warnings
    """
    warnings = []

    # Check if this is a planning pre-mortem (no code exists yet)
    planning_indicators = [
        "REQUIRES OPERATIONAL VERIFICATION AFTER IMPLEMENTATION",
        "planning pre-mortem",
        "pure planning",
    ]

    is_planning = any(indicator in pre_mortem_output for indicator in planning_indicators)

    if is_planning:
        warnings.append(
            "Planning pre-mortem detected - remember to run operational verification "
            "after implementation (test results, code review, log analysis)."
        )
    else:
        # For implementation pre-mortems, check for evidence mentions
        evidence_patterns = [
            r"test (result|output|passed|failed)",
            r"pytest",
            r"evidence",
            r"verified",
            r"validated",
        ]

        has_evidence = any(
            re.search(pattern, pre_mortem_output, re.IGNORECASE) for pattern in evidence_patterns
        )

        if not has_evidence:
            warnings.append(
                "No operational evidence detected. Implementation pre-mortems require "
                "empirical verification (test results, code review, log analysis)."
            )

    return (True, warnings)


def run_all_validations(pre_mortem_output: str) -> dict[str, Any]:
    """Run all pre-mortem validations.

    PM-005 FIX: Now uses validate_action_mapping_with_context() to provide
    helpful feedback for generic actions instead of just rejecting them.

    Args:
        pre_mortem_output: The pre-mortem output text to validate

    Returns:
        Validation results with is_valid flag, errors, warnings, and context_messages
    """
    results = {"is_valid": True, "errors": [], "warnings": [], "context_messages": []}

    # Action mapping validation with context (CRITICAL)
    # PM-005 FIX: Use enhanced version that provides contextual feedback
    is_valid, errors, context_messages = validate_action_mapping_with_context(pre_mortem_output)
    results["is_valid"] = results["is_valid"] and is_valid
    results["errors"].extend(errors)
    results["context_messages"].extend(context_messages)

    # Kill criteria validation
    is_valid, errors = validate_kill_criteria_defined(pre_mortem_output)
    results["is_valid"] = results["is_valid"] and is_valid
    results["errors"].extend(errors)

    # Temporal failure modes validation (QA-006 BLOCKER fix)
    # Step 2.7 was documented but had zero validation
    is_valid, errors = validate_temporal_failure_modes(pre_mortem_output)
    results["is_valid"] = results["is_valid"] and is_valid
    results["errors"].extend(errors)

    # Operational verification (warnings only)
    _, warnings = validate_operational_verification(pre_mortem_output)
    results["warnings"].extend(warnings)

    return results
