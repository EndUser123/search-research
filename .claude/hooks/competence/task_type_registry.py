#!/usr/bin/env python3
"""
Competence Layer - Task Type Registry
====================================

Central registry for task types, output contracts, and competence templates.
Maps skills to task types and provides reasoning guidance per task type.

Follows the same patterns as skill_execution_state.py:
- Module-level cache for registry data
- Path-based file access
- Type hints throughout
- Fail-open error handling
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# =============================================================================
# CONFIGURATION
# =============================================================================

REGISTRY_PATH = Path(__file__).resolve().parent / "templates" / "task_type_registry.json"
_REGISTRY_CACHE: dict[str, Any] | None = None

# Task types with no competence template (no guidance injected)
META_TASK_TYPE = "meta"

# =============================================================================
# REGISTRY LOADING
# =============================================================================


def load_registry() -> dict[str, Any]:
    """Load the task type registry from JSON.

    Returns:
        Registry dict with task_types, skill_mappings, category_mappings

    Note:
        Results are cached at module level for performance.
    """
    global _REGISTRY_CACHE

    if _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE

    if not REGISTRY_PATH.exists():
        # Fail open - return empty registry
        return {
            "task_types": {},
            "skill_mappings": {},
            "category_mappings": {},
        }

    try:
        content = REGISTRY_PATH.read_text(encoding="utf-8")
        _REGISTRY_CACHE = json.loads(content)
        return _REGISTRY_CACHE
    except (json.JSONDecodeError, OSError):
        # Fail open on error
        return {
            "task_types": {},
            "skill_mappings": {},
            "category_mappings": {},
        }


# =============================================================================
# TASK TYPE RESOLUTION
# =============================================================================


def get_task_type_for_skill(skill_name: str, category: str | None = None) -> str | None:
    """Map a skill name to its task type.

    Resolution order:
    1. Direct skill_mappings lookup (exact name match)
    2. category_mappings lookup (using provided category)
    3. Return None (unknown skill, treated as meta)

    Args:
        skill_name: Name of the skill (e.g., "research", "debugrca")
        category: Optional category from SKILL.md frontmatter

    Returns:
        Task type string (e.g., "research", "analysis") or None
    """
    registry = load_registry()
    skill_mappings = registry.get("skill_mappings", {})
    category_mappings = registry.get("category_mappings", {})

    # Normalize skill name to lowercase for lookup
    skill_key = skill_name.lower().strip()

    # Direct skill mapping (highest priority)
    if skill_key in skill_mappings:
        return skill_mappings[skill_key]

    # Category fallback (if category provided)
    if category:
        category_key = category.lower().strip()
        if category_key in category_mappings:
            return category_mappings[category_key]

    # Unknown skill - return None (will be treated as meta)
    return None


# =============================================================================
# OUTPUT CONTRACTS
# =============================================================================


def get_output_contract(task_type: str) -> dict[str, Any]:
    """Get the output contract for a task type.

    Args:
        task_type: Task type string (e.g., "research", "analysis")

    Returns:
        Dict with required_fields, optional_fields, verification_method
        Returns empty dict if task_type not found
    """
    registry = load_registry()
    task_types = registry.get("task_types", {})

    if task_type not in task_types:
        return {}

    return task_types[task_type].get("output_contract", {})


def get_required_fields(task_type: str) -> list[dict[str, Any]]:
    """Get required output fields for a task type.

    Args:
        task_type: Task type string

    Returns:
        List of field dicts with 'name' and 'synonyms' keys
        Returns empty list if task_type not found
    """
    contract = get_output_contract(task_type)
    return contract.get("required_fields", [])


def get_optional_fields(task_type: str) -> list[str]:
    """Get optional output fields for a task type.

    Args:
        task_type: Task type string

    Returns:
        List of optional field names (strings)
        Returns empty list if task_type not found
    """
    contract = get_output_contract(task_type)
    return contract.get("optional_fields", [])


# =============================================================================
# ENFORCEMENT MODE
# =============================================================================


def get_enforcement_mode(skill_name: str) -> str:
    """Get the enforcement mode for a skill.

    Resolution order:
    1. Skill-specific override (in skill_mappings as object)
    2. Task type default
    3. "advisory" (default fallback)

    Args:
        skill_name: Name of the skill

    Returns:
        Enforcement mode: "advisory", "warn", "block", or "none"
    """
    registry = load_registry()
    skill_mappings = registry.get("skill_mappings", {})
    task_types = registry.get("task_types", {})

    skill_key = skill_name.lower().strip()

    # Check for skill-specific override
    mapping = skill_mappings.get(skill_key)
    if isinstance(mapping, dict):
        # Skill has explicit override with task_type and enforcement_mode
        if "enforcement_mode" in mapping:
            return mapping["enforcement_mode"]
        # Get default from mapped task type
        task_type = mapping.get("task_type")
        if task_type and task_type in task_types:
            return task_types[task_type].get("default_enforcement_mode", "advisory")
    elif isinstance(mapping, str):
        # Skill maps directly to task type, get task type's default
        if mapping in task_types:
            return task_types[mapping].get("default_enforcement_mode", "advisory")

    # Fallback to advisory
    return "advisory"


# =============================================================================
# COMPETENCE TEMPLATES
# =============================================================================


def get_competence_template(task_type: str) -> dict[str, Any]:
    """Get the competence template for a task type.

    Args:
        task_type: Task type string

    Returns:
        Dict with lifecycle_steps, questions, output_format
        Returns empty dict if task_type not found or is meta
    """
    if task_type == META_TASK_TYPE:
        # Meta types have no template
        return {}

    registry = load_registry()
    task_types = registry.get("task_types", {})

    if task_type not in task_types:
        return {}

    return task_types[task_type].get("competence_template", {})


# =============================================================================
# TEMPLATE RENDERING
# =============================================================================


def render_template(
    task_type: str,
    minimal: bool = False,
    context_signals: dict[str, bool] | None = None,
) -> str:
    """Render a competence template as injectable markdown text.

    Args:
        task_type: Task type string
        minimal: If True, render only output contract fields.
                 If False, render full template with lifecycle.
        context_signals: Optional dict of boolean flags indicating context:
            - error_encountered: A recent tool call failed or returned an error
            - fix_requested: User prompt contains fix/debug/error intent
            - previous_block: Previous response was blocked by behavior audit
            - greenfield_intent: User prompt suggests building new rather than modifying
            These signals trigger conditional injection of principles,
            preventing habituation from constant injection.

    Returns:
        Markdown text ready for injection, or empty string for meta types
    """
    if task_type == META_TASK_TYPE:
        # Meta types get no template
        return ""

    registry = load_registry()
    task_types = registry.get("task_types", {})

    if task_type not in task_types:
        return ""

    type_info = task_types[task_type]
    core_question = type_info.get("core_question", "")

    # Build sections
    sections = []

    # Header
    type_name = task_type.upper().replace("_", " ")
    sections.append(f"**COMPETENCE GUIDANCE FOR {type_name} TASKS**")
    sections.append("")
    sections.append(f"**Core Question**: {core_question}")
    sections.append("")

    if minimal:
        # Minimal template: just output fields
        sections.append("**Required Output**")
        contract = type_info.get("output_contract", {})
        required = contract.get("required_fields", [])

        for field in required:
            name = field.get("name", "")
            sections.append(f"- **{name}**")
        sections.append("")
    else:
        # Full template: lifecycle + anti-avoidance + questions + gates

        # 5-Step Lifecycle
        template = type_info.get("competence_template", {})
        lifecycle = template.get("lifecycle_steps", [])

        if lifecycle:
            sections.append("**5-Step Lifecycle**")
            for step in lifecycle:
                sections.append(f"{step}")
            sections.append("")

        # Anti-Avoidance Principles (task-type targeted to prevent habituation)
        # Each principle injects only for task types where it prevents real failure modes
        anti_avoidance = []

        # Synthesize before deferring - prevents "I need more data" loops
        # Most relevant: research, analysis (information-gathering tasks)
        if task_type in ("research", "analysis", "planning"):
            anti_avoidance.append(
                "> **Synthesize before deferring.** After 3+ tool calls or findings, "
                "you MUST state your best hypothesis with a confidence level before "
                "requesting more data from the user. \"I believe X because Y (Medium "
                "confidence)\" is always better than \"I need to see the logs.\" Only "
                "ask the user for information you genuinely cannot obtain yourself."
            )

        # Verify before asserting - prevents confident-but-wrong claims
        # Most relevant: analysis, validation (making truth claims)
        if task_type in ("analysis", "validation", "research"):
            anti_avoidance.append(
                "> **Verify before asserting, then hold what you've verified.** Before "
                "claiming something is true, try to verify it (re-read the file, re-run "
                "the test, check the actual output). When the user challenges a *verified* "
                "conclusion, don't abandon it — restate with adjusted confidence: \"I "
                "verified X by [method] and still believe Y (Medium confidence), but you "
                "raise a valid concern about Z.\" However, if you *haven't* verified your "
                "claim, say so honestly: \"I believed X but I haven't actually confirmed "
                "it — let me check.\" Never defend an unverified assertion; never abandon "
                "a verified one without counter-evidence."
            )

        # Knowledge cutoff - prevents "that product can't do X" mistakes
        # Most relevant: research (external products/services)
        if task_type in ("research",):
            anti_avoidance.append(
                "> **Knowledge cutoff: search before contradicting.** Your training data "
                "has a cutoff date. When a user claims a product, service, or tool can do "
                "something you believe it cannot — DO NOT assert they are wrong. Your "
                "belief may be outdated. Instead: (1) acknowledge your knowledge cutoff, "
                "(2) use WebSearch or WebFetch to check current capabilities, (3) respond "
                "based on what you find."
            )

        # Follow through before reporting - prevents "the cause is X" without checking X
        # Most relevant: analysis, implementation (action-oriented tasks)
        if task_type in ("analysis", "implementation"):
            anti_avoidance.append(
                "> **Follow through before reporting.** When you identify a cause, source, "
                "or next step — ask yourself: \"Can I take the next step myself, or does "
                "the user need to?\" If you can take it (check the logs, read the file, "
                "run the test, verify the fix), do it now instead of reporting it as a "
                "finding or next step. **Stopping rule**: Take ONE follow-through action "
                "per finding — the most diagnostic or resolving step. If that step reveals "
                "more steps, report your updated findings with a prioritized \"remaining "
                "next steps\" list rather than chasing a chain."
            )

        # Context awareness before asking - prevents "what should I trace?" when context is obvious
        # Most relevant: analysis, implementation, planning, validation (tasks with clarifying questions)
        if task_type in ("analysis", "implementation", "planning", "validation"):
            anti_avoidance.append(
                "> **Context awareness before asking.** Scan the last 5-10 turns of conversation "
                "to identify the obvious target from recent work. **Rule**: Recent work = default target. "
                "When a command is invoked immediately after implementing/fixing something, that "
                "something is the target. State the assumption briefly, then proceed. Only ask if "
                "there's genuine ambiguity (e.g., 3 different files modified)."
            )

        if anti_avoidance:
            sections.append("**Anti-Avoidance Principle**")
            sections.append("")
            for principle in anti_avoidance:
                sections.append(principle)
                sections.append("")

        # Reasoning Questions
        questions = template.get("questions", [])
        if questions:
            sections.append("**Reasoning Checklist**")
            for q in questions:
                sections.append(f"- {q}")
            sections.append("")

        # Conditional Library-First Gate (only when greenfield intent detected)
        # Same pattern as Root-Cause Obligation: signal-based to prevent habituation
        signals = context_signals or {}
        if signals.get("greenfield_intent") and task_type in (
            "implementation", "planning", "analysis",
        ):
            sections.append("**Library-First Gate**")
            sections.append(
                "> Before proposing new code: (1) search first (`/search`, Grep, Glob), "
                "(2) check existing backends/skills/tools, (3) extend existing solutions "
                "when they cover ~70%+, and (4) if you still build new, state why existing "
                "options are insufficient. Greenfield proposals without a search pass are prohibited."
            )
            sections.append("")

        # Synthesis Gate - for tasks that produce conclusions/hypotheses
        if task_type in ("research", "analysis", "planning"):
            sections.append("**Synthesis Gate**")
            sections.append("> Do I have enough evidence to state a hypothesis? If yes, state it now with confidence level and verification status (verified/unverified). Do NOT ask the user for more data without first presenting what you believe and why.")
            sections.append("")

        # Follow-through Gate - for tasks that identify next actions
        if task_type in ("analysis", "implementation"):
            sections.append("**Follow-through Gate**")
            sections.append("> Is there an obvious next step I can take myself right now? (Check the log, read the file, run the test, verify the fix.) If yes, do it before responding — but limit to ONE follow-through step per response.")
            sections.append("")

        # Proxy Variable Gate - prevents association-based proxy checks
        # Implementation: choosing HOW to detect/check/achieve something
        # Analysis: interpreting what evidence actually means
        # Planning: choosing what checks/verifications to include in a plan
        # The failure mode: "commit hook exists" proves nothing about commit state
        if task_type in ("analysis", "implementation", "planning"):
            sections.append("**Proxy Variable Gate**")
            sections.append(
                "> Ask: **\"What does this actually prove?\"** "
                "Run the falsification test: \"Under what conditions would my check succeed but the actual goal fail?\" "
                "If you can answer this, you're measuring a proxy — find the direct mechanism instead."
            )
            sections.append("")

        # Conditional Root-Cause Obligation (only when signals indicate risk)
        signals = context_signals or {}
        if any(signals.get(k) for k in ("error_encountered", "fix_requested", "previous_block")):
            sections.append("**Root-Cause Obligation**")
            sections.append(
                "> On errors or failures, fix the source. \"Cosmetic\", \"known issue\", "
                "and \"workaround only\" are not resolutions. If root-cause fix is blocked, "
                "provide evidence of the blocker (e.g., upstream bug link or platform limit) "
                "and explain why a workaround is required."
            )
            sections.append("")

        # Anti-Clarification-Theater (only for debug/fix contexts)
        # Prevents asking "what issue?" when the user's prompt already contains the error
        if signals.get("fix_requested") or signals.get("previous_block"):
            sections.append("**Anti-Clarification Gate**")
            sections.append(
                "> If the user's prompt contains the error message, target file, or problem "
                "description — DO NOT ask \"what issue are you experiencing?\" or \"could you "
                "clarify the problem?\" Restate the target from their prompt and proceed "
                "immediately. Only ask for clarification when there is genuine ambiguity "
                "(e.g., multiple unrelated errors mentioned, no specific target identifiable)."
            )
            sections.append("")

        # Falsification-Over-Confirmation (only for debug/fix contexts)
        # Prevents "works for me" conclusions that miss the user's failure path
        if signals.get("fix_requested"):
            sections.append("**Falsification Gate**")
            sections.append(
                "> When investigating a reported bug: test the FAILING path, not just the "
                "passing path. If you can only reproduce success, say so — do not conclude "
                "\"not a bug.\" Ask for the user's exact reproduction steps. A test that "
                "passes does not disprove a bug; it only proves one path works."
            )
            sections.append("")

        # Output Format Suggestion
        output_format = template.get("output_format", "")
        if output_format:
            sections.append("**Suggested Output Format**")
            sections.append("```")
            sections.append(output_format)
            sections.append("```")
            sections.append("")

        # Anti-Cargo-Culting Note
        sections.append("*Each section should contain substantive content — not just a rephrasing of the question. If you have nothing meaningful for a section, say 'N/A — [reason]' rather than padding with filler.*")
        sections.append("")

    # Escape hatch for mismatched intent
    sections.append("---")
    sections.append("*If this template doesn't fit the user's actual intent, state the mismatch and follow the approach that matches their intent. The template is guidance, not a straitjacket.*")
    sections.append("")

    return "\n".join(sections)


# =============================================================================
# FIELD DETECTION (for contract verification)
# =============================================================================


def check_field_present(
    response: str,
    field_name: str,
    synonyms: list[str] | None = None
) -> bool:
    """Check if a required field is present in the response.

    Uses flexible regex patterns to detect field names in multiple formats:
    - Markdown headers: ## Field_Name, ## field_name
    - Bold text: **Field_Name**, **field_name**
    - Colon labels: Field_Name:, field_name:

    Args:
        response: The response text to check
        field_name: The primary field name to look for
        synonyms: Optional list of synonym strings to also match

    Returns:
        True if field (or any synonym) is detected, False otherwise
    """
    if not response:
        return False

    # Build list of terms to check (primary + synonyms)
    terms = [field_name]
    if synonyms:
        terms.extend(synonyms)

    # Regex patterns for each term
    for term in terms:
        # Escape special regex characters in the term
        escaped = re.escape(term)

        # Pattern 1: Markdown header (## Field Name or ## field name)
        # Case-insensitive, allows optional colon
        header_pattern = rf"^##\s*{escaped}\s*:"
        if re.search(header_pattern, response, re.IGNORECASE | re.MULTILINE):
            return True

        # Pattern 2: Bold text (**Field Name** or **field name**)
        bold_pattern = rf"\*\*{escaped}\*\*"
        if re.search(bold_pattern, response, re.IGNORECASE):
            return True

        # Pattern 3: Colon label (Field Name: or field name:)
        # Must be at start of line or after whitespace
        label_pattern = rf"(?<!\w){escaped}\s*:"
        if re.search(label_pattern, response, re.IGNORECASE):
            return True

        # Pattern 4: Standalone word with boundary
        # More permissive - catches field names as standalone words
        word_pattern = rf"\b{escaped}\b"
        if re.search(word_pattern, response, re.IGNORECASE):
            return True

    return False


def check_contract_completeness(
    response: str,
    task_type: str,
    _enforcement_mode: str = "advisory",
) -> dict[str, Any]:
    """Check if a response contains all required output contract fields.

    Args:
        response: The response text to check
        task_type: Task type to get contract for
        _enforcement_mode: Reserved for future use (caller-provided enforcement mode)

    Returns:
        Dict with:
        - complete (bool): Whether all required fields are present
        - missing_fields (list[str]): Names of missing fields
        - detected_fields (list[str]): Names of fields that were detected
    """
    if task_type == META_TASK_TYPE:
        # Meta types have no contract
        return {
            "complete": True,
            "missing_fields": [],
            "detected_fields": [],
        }

    required = get_required_fields(task_type)
    if not required:
        # No required fields defined
        return {
            "complete": True,
            "missing_fields": [],
            "detected_fields": [],
        }

    missing = []
    detected = []

    for field_spec in required:
        name = field_spec.get("name", "")
        synonyms = field_spec.get("synonyms", [])

        if check_field_present(response, name, synonyms):
            detected.append(name)
        else:
            missing.append(name)

    return {
        "complete": len(missing) == 0,
        "missing_fields": missing,
        "detected_fields": detected,
    }
