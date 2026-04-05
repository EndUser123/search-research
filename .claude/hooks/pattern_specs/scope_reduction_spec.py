"""
Scope Reduction Pattern Specification

Defines patterns that detect unauthorized scope reductions in Claude responses.
These patterns prevent Claude from reducing work scope based on its own judgment
(time, effort, "sufficient") without explicit user authorization.

WHY Category: Solo-Dev Authority
Constitutional Principle: Complete all stages unless user explicitly requests otherwise

Source: StopHook_scope_reduction.py
Pattern Count: 8 patterns combined
"""
from __future__ import annotations

PATTERN_SPEC = {
    "pattern_name": "scope_reduction",

    "semantic_definition": """
        Detects when Claude reduces the scope of work based on its own judgment
        about time, effort, or sufficiency. This includes skipping stages/steps,
        omitting work, deferring tasks, or claiming current work is "enough."

        Constitutional violation: Claude must complete ALL stages unless the user
        explicitly requests otherwise. Patterns like "skipping to save time" or
        "this should be sufficient" indicate unauthorized scope reduction.
    """,

    "positive_examples": [
        # Skipping with justification
        "Skipping stage 3 because it's too time-consuming.",
        "Skipping step 2 since it's lengthy and expensive.",
        "I'll skip the testing phase because it's time-consuming.",
        "Skipping the deployment to save time.",
        "Stage 3 is time-consuming so I'll move on.",
        "Step 2 is time-consuming, let's skip it.",
        "The verification phase is time-consuming.",

        # Premature satisfaction claims
        "We already have enough findings.",
        "We already have sufficient data to proceed.",
        "Current results are sufficient, skipping further stages.",

        # Omitting work
        "Omitting the error handling to save time.",
        "Omitting validation because it's too much effort.",

        # Deferring without user request
        "Deferring the refactoring until later.",
        "Deferring tests to save effort.",

        # Sufficiency judgments
        "This implementation should be sufficient.",
        "The current approach should be sufficient.",

        # "Rest can be done later" pattern
        "The rest can be done later.",
    ],

    "negative_examples": [
        # Legitimate completions (no trigger words)
        "Stage 3 is complete. Moving to stage 4.",
        "All tests passed. Deployment complete.",
        "The implementation is finished and verified.",
        "Test coverage meets requirements.",
        "All requirements have been implemented.",

        # Legitimate time estimates (not scope reduction)
        "This stage may take 30 minutes to complete.",
        "Estimated time for testing is 2 hours.",
        "The deployment process requires additional time.",

        # Legitimate sufficiency assessments (not scope reduction)
        "The test results are adequate for release.",
        "Documentation meets the minimum requirements.",
        "Code quality is acceptable per the standards.",
    ],

    # Simple pattern that matches the key phrases in positive examples
    "pattern": r"(?i)(skip|skipping|omitting|deferring|time-consuming|already have (enough|sufficient)|should be sufficient|rest can be done later)",

    "complexity": 2,

    "category": "Solo-Dev Authority",

    "severity": "high",

    "notes": """
        IMPLEMENTATION NOTES:

        1. Simplified pattern using keyword detection:
           - skip/skipping/omitting/deferring (scope reduction actions)
           - time-consuming (justification for skipping)
           - already have enough/sufficient (premature completion)
           - should be sufficient (sufficiency judgment)
           - rest can be done later (deferral pattern)

        2. This is a simple, broad pattern that catches the key phrases.
           False positives are acceptable - they can be whitelisted.

        3. Complexity: Score 2 - simple alternation with word detection.
           Stays well under threshold of 5.

        4. Case Sensitivity: Uses (?i) flag for case-insensitive matching.

        5. Constitutional Alignment:
           - WHY: Solo-Dev Authority (Claude cannot decide to skip work)
           - Fails fast: Blocks immediately upon pattern match
           - No graceful degradation: Scope reduction is a hard violation

        6. Whitelist patterns (exemptions) - check BEFORE scope reduction:
           Applied at runtime to exempt user-authorized actions.
           Examples: "you requested", "per your request", "user explicitly asked"
    """,

    "whitelist_patterns": [
        r"(?i)you\s+(requested|asked|wanted|explicitly)",
        r"(?i)per\s+your\s+request",
        r"(?i)as\s+you\s+requested",
        r"(?i)user\s+(requested|said|asked)",
    ],
}
