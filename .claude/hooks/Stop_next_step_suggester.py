#!/usr/bin/env python3
from __future__ import annotations

"""
Stop-time next step suggester.

Builds a compact /p-style options list from:
- decision patterns in response (NEW: pattern-based detection)
- last slash command suggest graph (orchestrator suggest parser, best-effort)
- task-unresolved heuristics

Presentation:
- Numbered options like /p uses (0 - ..., 1 - ...).
"""

import json
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from __lib import suggestion_utils

# Observability log file
DECISION_PATTERN_LOG = Path(__file__).resolve().parent.parent / "state" / "logs" / "decision_patterns.jsonl"

MAX_SUGGESTIONS = 5

# Domain-expert skills that provide contextual next steps (preserve their menus)
DOMAIN_EXPERT_SKILLS = {"/arch", "/s", "/code"}

# Pipeline skills that rely on hook + suggest field (hook adds value)
PIPELINE_SKILLS = {"/p", "/q", "/package", "/nse"}


class DecisionType(Enum):
    """Classification of decision patterns in assistant responses.

    Based on analysis of 907 conversation files (6.4GB, ~500,000 turns):
    - EXPLICIT_OPTIONS: 86% - "1. Do X", "2. Do Y"
    - QUESTION_ENDING: 10% - Ends with "?"
    - NEXT_STEPS_SECTION: 3% - "## Next Steps"
    - DIRECTION_REQUEST: 2% - "What would you like"
    - NO_DECISION: Single obvious action
    """
    EXPLICIT_OPTIONS = "explicit_options"  # 86% - Numbered/bulleted lists
    QUESTION_ENDING = "question_ending"  # 10% - Ends with "?"
    NEXT_STEPS_SECTION = "next_steps_section"  # 3% - "## Next Steps" header
    DIRECTION_REQUEST = "direction_request"  # 2% - "What would you like"
    NO_DECISION = "no_decision"  # Single obvious action


def _response_has_next_steps(response: str) -> bool:
    """Detect if response already has a Next Steps section.

    Matches both template format (- 0 — action) and hook format (0 - action).
    """
    if not response:
        return False

    # Pattern matches:
    # - Template: "### Next Steps:" followed by "- 0 —" or "- 1 —" etc
    # - Hook: "Next Step Options:" followed by "0 -" or "1 -" etc
    pattern = r'Next Steps.*?- \d\s*—|Next Step Options:.*?^\d+\s*-'

    return bool(re.search(pattern, response, re.MULTILINE | re.DOTALL))


def _should_append_next_steps(
    response: str, last_command: str | None, hook_options: list[str]
) -> bool:
    """Option C Enhanced: Decide whether hook should append next steps.

    Collision detection logic:
    - Domain-expert skills: Keep their contextual next steps
    - Pipeline skills: Append if no template next steps exist
    - Empty hook options: Skip (nothing valuable to add)

    Args:
        response: The full response text from the skill
        last_command: The last slash command invoked (e.g., "/arch")
        hook_options: Options the hook would generate

    Returns:
        True if hook should append, False if template already handled it
    """
    # No hook options = nothing valuable to add
    if not hook_options:
        return False

    # Check if response already has next steps
    has_template_next_steps = _response_has_next_steps(response)

    if not has_template_next_steps:
        # No template next steps → hook should add
        return True

    # Template has next steps → check skill type
    if last_command in DOMAIN_EXPERT_SKILLS:
        # Domain experts provide contextual next steps → preserve them
        return False

    if last_command in PIPELINE_SKILLS:
        # Pipeline skills have static next steps → hook provides dynamic value
        # Only append if hook has unique options not in template
        return True

    # Unknown command → default to appending (safer to provide options)
    return True


def _extract_last_command(data: dict[str, Any]) -> str | None:
    """Extract last slash command from prompt or conversation payload."""
    prompt = data.get("prompt", "")
    if isinstance(prompt, str) and prompt.strip():
        cmd = suggestion_utils.get_last_command(prompt)
        if cmd:
            return cmd

    # Fallback: inspect conversation text blocks.
    conversation = data.get("conversation", [])
    if isinstance(conversation, list):
        for item in reversed(conversation):
            text = ""
            if isinstance(item, dict):
                text = str(item.get("content", "") or item.get("text", ""))
            if text:
                cmd = suggestion_utils.get_last_command(text)
                if cmd:
                    return cmd
    return None


def _load_suggest_parser():
    try:
        import sys

        hooks_dir = Path(__file__).resolve().parent
        skills_path = hooks_dir.parent / "skills"
        if skills_path.exists():
            sys.path.insert(0, str(skills_path))
        from orchestrator.suggest_parser import SuggestFieldParser

        return SuggestFieldParser()
    except Exception:
        return None


def _get_suggest_field_commands(last_command: str | None) -> list[str]:
    if not last_command:
        return []
    parser = _load_suggest_parser()
    if parser is None:
        return []
    try:
        return [str(c) for c in parser.get_suggestions(last_command)]
    except Exception:
        return []


def _format_with_description(cmd: str, registry: dict[str, Any]) -> str:
    description = suggestion_utils.get_command_description(cmd, registry)
    if description:
        return f"{cmd} - {description}"
    return cmd


def _should_add_task_unresolved(
    response: str, last_command: str | None, signals: list[str]
) -> bool:
    if "unresolved_items_detected" in signals:
        return True
    if last_command in ("/task", "/tasks", "/todo", "/task-unresolved"):
        return True
    return bool(
        re.search(
            r"unresolved|backlog|remaining tasks|completed tasks|task list|stuck",
            response,
            re.IGNORECASE,
        )
    )


def classify_decision_point(response: str) -> DecisionType:
    """Classify the decision pattern in an assistant response.

    Uses pattern detection based on analysis of real conversations:
    - EXPLICIT_OPTIONS (86%): Numbered/bulleted lists with actions
    - QUESTION_ENDING (10%): Response ends with "?"
    - NEXT_STEPS_SECTION (3%): "## Next Steps" header present
    - DIRECTION_REQUEST (2%): "What would you like" phrases
    - NO_DECISION: Single obvious action, no choice offered

    Args:
        response: The assistant response text to classify

    Returns:
        DecisionType enum value indicating the pattern type
    """
    if not response or not response.strip():
        return DecisionType.NO_DECISION

    # Priority 1: Check for Next Steps section (3%) - must check before EXPLICIT_OPTIONS
    # because Next Steps sections contain numbered items that would match EXPLICIT_OPTIONS pattern
    if "### Next Steps" in response or "## Next Steps" in response:
        return DecisionType.NEXT_STEPS_SECTION

    # Priority 2: Check for explicit options (most common - 86%)
    # Numbered list: "1. Do X", "2. Do Y"
    if re.search(r'(?:^|\n)\s*\d+\.\s+\w+', response):
        return DecisionType.EXPLICIT_OPTIONS

    # Bulleted list with action items: "- Do X", "* Do Y"
    if re.search(r'(?:^|\n)\s*[-*]\s+[A-Z][a-z]+', response):
        return DecisionType.EXPLICIT_OPTIONS

    # Priority 3: Check for direction request (2%)
    direction_phrases = ["what would you like", "how should i", "which approach", "what should i"]
    response_lower = response.lower()
    if any(phrase in response_lower for phrase in direction_phrases):
        return DecisionType.DIRECTION_REQUEST

    # Priority 4: Check for question ending (10%)
    # Only if question mark is at end of response (not in code blocks)
    if response.strip().endswith("?"):
        return DecisionType.QUESTION_ENDING

    return DecisionType.NO_DECISION


def extract_menu_options(response: str, decision_type: DecisionType) -> list[str]:
    """Extract menu options based on decision type.

    Args:
        response: The assistant response text
        decision_type: The classified decision pattern type

    Returns:
        List of menu option strings (formatted for /p-style display)
    """
    if decision_type == DecisionType.EXPLICIT_OPTIONS:
        # Extract numbered/bulleted options
        # Pattern matches: "1. Action text" or "- Action text"
        options = re.findall(
            r'(?:^|\n)\s*(\d+\.|[-*])\s*(.+?)(?=\n|$)',
            response,
            re.MULTILINE
        )
        # Format: "1. Action text" or "- Action text"
        return [f"{num} {text.strip()[:80]}" for num, text in options]

    if decision_type == DecisionType.NEXT_STEPS_SECTION:
        # Extract items after Next Steps header
        # Split on header and get items
        next_steps = re.split(r'## Next Steps|### Next Steps', response)[-1]
        options = re.findall(
            r'(?:^|\n)\s*(\d+\.|[-*])\s*(.+?)(?=\n|$)',
            next_steps,
            re.MULTILINE
        )
        return [f"{num} {text.strip()[:80]}" for num, text in options]

    if decision_type == DecisionType.QUESTION_ENDING:
        # Parse question into yes/no choice
        question = response.strip().split("\n")[-1].rstrip("?")
        return [
            f"✓ Yes - {question}",
            "✗ No - Skip this"
        ]

    if decision_type == DecisionType.DIRECTION_REQUEST:
        # Provide context-aware options for direction requests
        return [
            "Continue with default approach",
            "Provide more context first",
            "Skip for now"
        ]

    return []  # NO_DECISION or unrecognized pattern


def _log_decision_pattern(decision_type: DecisionType, num_options: int, response_length: int) -> None:
    """Log decision pattern for production analysis.

    Creates JSONL log entry for tracking:
    - Distribution of decision types (validates 86%/10%/3%/2% assumptions)
    - Option extraction rates
    - Response length patterns

    Log format: {"timestamp": "...", "decision_type": "...", "num_options": N, "response_length": N}
    """
    try:
        DECISION_PATTERN_LOG.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "decision_type": decision_type.value,
            "num_options": num_options,
            "response_length": response_length,
        }
        with open(DECISION_PATTERN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except OSError:
        # Fail silently - logging should never break the hook
        pass


def get_next_step_options(data: dict[str, Any]) -> list[str]:
    response = str(data.get("response", "") or "")
    if not response.strip():
        return []

    registry = suggestion_utils.load_commands_registry()
    last_command = _extract_last_command(data)

    options: list[str] = []

    # 1) NEW: Pattern-based detection from response (data-driven approach).
    # This replaces signal-based detection as primary method.
    # Based on analysis of 907 conversation files showing:
    # - Explicit options: 86%, Question endings: 10%
    # - Next Steps sections: 3%, Direction requests: 2%
    decision_type = classify_decision_point(response)
    pattern_options = extract_menu_options(response, decision_type)
    options.extend(pattern_options)

    # Monitor: Log decision type for production analysis
    _log_decision_pattern(decision_type, len(pattern_options), len(response))

    # 2) Signal-based suggestions from registry (fallback for backward compatibility).
    # Only adds options if pattern detection didn't find any.
    if not pattern_options:
        signals = suggestion_utils.extract_output_signals(response)
        signal_map = registry.get("signals", {})
        for signal in signals:
            mapped = signal_map.get(signal)
            if isinstance(mapped, str) and mapped.strip():
                options.append(mapped.strip())

    # 3) Suggest-field graph suggestions from previous command.
    for cmd in _get_suggest_field_commands(last_command):
        if not cmd.startswith("/"):
            cmd = f"/{cmd.lstrip('/')}"
        options.append(_format_with_description(cmd, registry))

    # 4) Task unresolved option for task/backlog contexts.
    # Note: Pass signals even if pattern-based, for backward compatibility
    signals = suggestion_utils.extract_output_signals(response)
    if _should_add_task_unresolved(response, last_command, signals):
        options.append(_format_with_description("/task-unresolved", registry))

    # Dedupe by command token, preserve order.
    seen: set[str] = set()
    deduped: list[str] = []
    for opt in options:
        token = opt.split()[0].strip()
        if token and token not in seen:
            seen.add(token)
            deduped.append(opt)

    return deduped[:MAX_SUGGESTIONS]


def build_numeric_menu(options: list[str]) -> str:
    if not options:
        return ""
    lines = ["Next Step Options:"]
    for i, opt in enumerate(options):
        lines.append(f"{i} - {opt}")
    return "\n".join(lines)


def build_alphanumeric_menu(options: list[str]) -> str:
    """Backward-compatible alias.

    Historical callers import build_alphanumeric_menu(). We now render in numeric
    /p-style for consistency.
    """
    return build_numeric_menu(options)
