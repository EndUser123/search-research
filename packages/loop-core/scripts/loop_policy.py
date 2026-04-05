"""Loop policy enforcement for Ralph-style autonomous loops.

This module implements policy-based exit conditions and verification triggers
for autonomous loops. It loads configuration from .claude/loop/config.yaml and
enforces exit policy based on task completion, completion indicators, exit signals,
and verification status.

Key Functions:
--------------
- load_config(): Load and validate configuration from YAML file
- should_exit(): Check if loop should exit based on policy flags
- should_run_verifier(): Check if verification should run
- parse_plan_with_cache(): Parse plan file with caching for performance

Exit Policy Flags:
------------------
The exit decision is controlled by 4 boolean flags (16 combinations):

1. min_completion_indicators (int): Minimum completion indicators required
2. require_exit_signal (bool): Require EXIT_SIGNAL: true in RALPH_STATUS
3. require_all_tasks_complete (bool): Require all tasks marked complete
4. require_verification_pass (bool): Require verification to pass

All conditions must be met for the loop to exit.

Config Schema:
--------------
See .claude/loop/config.yaml for full schema documentation.

Performance:
------------
- Plan parsing is cached using file modification time
- Config is loaded fresh on each call (no module-level caching)
- This allows config changes to take effect mid-run
- Cache invalidation on file changes is automatic
"""

from pathlib import Path
from typing import Any

import yaml

from scripts.plan_parser import parse_plan_tasks


class ConfigLoadError(Exception):
    """Exception raised when config file cannot be loaded."""

    pass


class ConfigIntegrityError(Exception):
    """Exception raised when config file fails integrity validation."""

    pass


# Global cache for plan parsing: {file_path: (mtime, tasks)}
_plan_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load and validate loop configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses .claude/loop/config.yaml

    Returns:
        Dictionary containing validated configuration

    Raises:
        ConfigLoadError: If config file not found or cannot be parsed
        ConfigIntegrityError: If config fails integrity validation

    Config Schema:
        - version (int): Config version (must be 1)
        - exit_policy (dict): Exit policy configuration
            - min_completion_indicators (int): Minimum indicators (>= 1)
            - require_exit_signal (bool): Require EXIT_SIGNAL in plan
            - require_all_tasks_complete (bool): Require all tasks complete
            - require_verification_pass (bool): Require verification pass
        - verification (dict): Verification configuration
            - enabled (bool): Verification enabled
            - skill (str): Verification skill name
            - write_report (str): Report output path
        - plans (dict): Plan configuration
            - default_plan (str): Default plan file path
            - allow_per_terminal_plan (bool): Allow per-terminal plans
        - logging (dict): Logging configuration
            - decision_log (str): Decision log path
            - verifier_log (str): Verifier log path
    """
    if config_path is None:
        # Use default path
        config_path = ".claude/loop/config.yaml"

    config_file = Path(config_path)

    if not config_file.exists():
        raise ConfigLoadError(f"Config file not found: {config_file}")

    try:
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigLoadError(f"Failed to parse config file {config_file}: {e}") from e
    except OSError as e:
        raise ConfigLoadError(f"Failed to read config file {config_file}: {e}") from e

    if not isinstance(config_data, dict):
        raise ConfigIntegrityError("Config file must contain a dictionary")

    # Validate required sections
    required_sections = ["version", "exit_policy", "verification", "plans", "logging"]
    for section in required_sections:
        if section not in config_data:
            raise ConfigIntegrityError(f"Missing required config section: {section}")

    # Validate enforcement section (optional)
    if "enforcement" in config_data:
        enforcement = config_data.get("enforcement")
        if not isinstance(enforcement, dict):
            raise ConfigIntegrityError(f"Invalid type for field enforcement: expected dict, got {type(enforcement).__name__}")

        if "enabled" in enforcement:
            enabled = enforcement.get("enabled")
            if not isinstance(enabled, bool):
                raise ConfigIntegrityError(f"Invalid type for field enforcement.enabled: expected bool, got {type(enabled).__name__}")

    # Validate version
    version = config_data.get("version")
    if not isinstance(version, int):
        raise ConfigIntegrityError(f"Invalid type for field version: expected int, got {type(version).__name__}")
    if version != 1:
        raise ConfigIntegrityError(f"Unsupported config version: {version} (supported: 1)")

    # Validate exit_policy
    exit_policy = config_data.get("exit_policy")
    if not isinstance(exit_policy, dict):
        raise ConfigIntegrityError(f"Invalid type for field exit_policy: expected dict, got {type(exit_policy).__name__}")

    required_exit_policy_fields = [
        "min_completion_indicators",
        "require_exit_signal",
        "require_all_tasks_complete",
        "require_verification_pass",
    ]
    for field in required_exit_policy_fields:
        if field not in exit_policy:
            raise ConfigIntegrityError(f"Missing required exit_policy field: {field}")

    # Validate min_completion_indicators
    min_indicators = exit_policy.get("min_completion_indicators")
    if not isinstance(min_indicators, int):
        raise ConfigIntegrityError(f"Invalid type for field min_completion_indicators: expected int, got {type(min_indicators).__name__}")
    if min_indicators < 1:
        raise ConfigIntegrityError(f"min_completion_indicators must be >= 1, got {min_indicators}")

    # Validate boolean fields
    for field in ["require_exit_signal", "require_all_tasks_complete", "require_verification_pass"]:
        value = exit_policy.get(field)
        if not isinstance(value, bool):
            raise ConfigIntegrityError(f"Invalid type for field {field}: expected bool, got {type(value).__name__}")

    # Validate verification section
    verification = config_data.get("verification")
    if not isinstance(verification, dict):
        raise ConfigIntegrityError(f"Invalid type for field verification: expected dict, got {type(verification).__name__}")

    if "enabled" not in verification:
        raise ConfigIntegrityError("Missing required verification field: enabled")
    if not isinstance(verification["enabled"], bool):
        raise ConfigIntegrityError(f"Invalid type for field verification.enabled: expected bool, got {type(verification['enabled']).__name__}")

    # Validate plans section
    plans = config_data.get("plans")
    if not isinstance(plans, dict):
        raise ConfigIntegrityError(f"Invalid type for field plans: expected dict, got {type(plans).__name__}")

    # Validate logging section
    logging_config = config_data.get("logging")
    if not isinstance(logging_config, dict):
        raise ConfigIntegrityError(f"Invalid type for field logging: expected dict, got {type(logging_config).__name__}")

    return config_data


def should_exit(
    tasks: list[dict[str, Any]], loop_state: dict[str, Any], config: dict[str, Any]
) -> bool:
    """Check if loop should exit based on exit policy.

    Evaluates all exit policy flags to determine if the loop should exit.
    All enabled conditions must be met for exit to proceed.

    Args:
        tasks: List of task dictionaries from parse_plan_tasks()
        loop_state: Loop state dictionary with keys:
            - completion_indicators (int): Current completion indicator count
            - ralph_status (dict, optional): RALPH_STATUS section with EXIT_SIGNAL
            - verification_status (dict, optional): Verification status with passed flag
            - metadata (dict, optional): Contains plan_path and transcript_path
        config: Configuration dictionary from load_config()

    Returns:
        True if all enabled exit conditions are met, False otherwise

    Exit Conditions:
        1. completion_indicators >= min_completion_indicators (always required)
        2. EXIT_SIGNAL: true in RALPH_STATUS (if require_exit_signal is true)
        3. All tasks marked complete (if require_all_tasks_complete is true)
        4. Verification passed (if require_verification_pass is true)
           - Uses practical verification: plan requirements + chat concerns

    Enforcement Modes:
        - enforcement.enabled=true: Full policy (all exit conditions apply)
        - enforcement.enabled=false: Minimal policy (EXIT_SIGNAL + completion_indicators only)

    Examples:
        >>> # All conditions met
        >>> should_exit(tasks, loop_state, config)
        True

        >>> # Missing EXIT_SIGNAL
        >>> should_exit(tasks, loop_state, config)
        False
    """
    exit_policy = config.get("exit_policy", {})
    enforcement = config.get("enforcement", {})
    enforcement_enabled = enforcement.get("enabled", True)  # Default to enabled

    # Condition 1: Minimum completion indicators (always required)
    min_indicators = exit_policy.get("min_completion_indicators", 2)
    current_indicators = loop_state.get("completion_indicators", 0)

    if current_indicators < min_indicators:
        return False

    # Minimal policy mode (enforcement disabled)
    if not enforcement_enabled:
        # Only require EXIT_SIGNAL, ignore all other conditions
        ralph_status = loop_state.get("ralph_status", {})
        exit_signal = ralph_status.get("EXIT_SIGNAL", False)
        return exit_signal

    # Full policy mode (enforcement enabled)
    # Condition 2: Exit signal (if required)
    if exit_policy.get("require_exit_signal", True):
        ralph_status = loop_state.get("ralph_status", {})
        exit_signal = ralph_status.get("EXIT_SIGNAL", False)
        if not exit_signal:
            return False

    # Condition 3: All tasks complete (if required)
    if exit_policy.get("require_all_tasks_complete", True):
        incomplete_tasks = [task for task in tasks if not task.get("complete", False)]
        if incomplete_tasks:
            return False

    # Condition 4: Verification passed (if required)
    if exit_policy.get("require_verification_pass", True):
        verification_config = config.get("verification", {})

        # Use practical verification if enabled
        if verification_config.get("enabled", True):
            # Check if we should run practical verification
            verification_status = loop_state.get("verification_status", {})

            # If verification already ran and passed, use that result
            if verification_status.get("passed", False):
                return True

            # Run practical verification
            plan_path = loop_state.get("metadata", {}).get("plan_path")
            if plan_path:
                try:
                    # Extract requirements from plan
                    requirements = parse_plan_requirements(plan_path)

                    # Verify completion against requirements
                    completion_check = verify_completion_against_requirements(tasks, requirements)

                    # Check for user concerns in chat
                    transcript_path = loop_state.get("metadata", {}).get("transcript_path")
                    user_concerns = extract_user_concerns_from_chat(transcript_path, lookback_turns=10)

                    # Block exit if requirements not met OR user has concerns
                    if not completion_check["all_requirements_met"]:
                        # Update verification status with failure
                        verification_status["passed"] = False
                        verification_status["reason"] = "Requirements not met"
                        verification_status["missing_criteria"] = completion_check["missing_criteria"]
                        loop_state["verification_status"] = verification_status
                        return False

                    if user_concerns:
                        # Block exit if user has blockers/issues
                        verification_status["passed"] = False
                        verification_status["reason"] = "User concerns detected"
                        verification_status["concerns"] = user_concerns
                        loop_state["verification_status"] = verification_status
                        return False

                    # All checks passed
                    verification_status["passed"] = True
                    verification_status["reason"] = "Practical verification passed"
                    verification_status["completion_rate"] = completion_check["completion_rate"]
                    loop_state["verification_status"] = verification_status

                except (FileNotFoundError, OSError):
                    # Plan or transcript not accessible - fail gracefully
                    # Don't block exit due to verification system issues
                    pass

            # Legacy verification status check (for backward compatibility)
            verification_passed = verification_status.get("passed", False)
            if not verification_passed:
                return False

    return True


def should_run_verifier(loop_state: dict[str, Any], config: dict[str, Any]) -> bool:
    """Check if verification should run.

    Determines whether verification should be triggered based on:
    - Verification enabled in config
    - Verification required by exit policy
    - Previous verification status (don't re-run if already passed)

    Args:
        loop_state: Loop state dictionary with optional verification_status
        config: Configuration dictionary from load_config()

    Returns:
        True if verification should run, False otherwise

    Examples:
        >>> # First time, verification enabled and required
        >>> should_run_verifier(loop_state, config)
        True

        >>> # Already passed, don't re-run
        >>> loop_state['verification_status'] = {'passed': True}
        >>> should_run_verifier(loop_state, config)
        False
    """
    # Check if verification is enabled
    verification_config = config.get("verification", {})
    if not verification_config.get("enabled", True):
        return False

    # Check if verification is required by exit policy
    exit_policy = config.get("exit_policy", {})
    if not exit_policy.get("require_verification_pass", True):
        return False

    # Check if verification already passed
    verification_status = loop_state.get("verification_status")
    if verification_status:
        # If already passed, don't re-run
        if verification_status.get("passed", False):
            return False
        # If failed, allow retry

    # Verification should run
    return True


def parse_plan_with_cache(plan_path: str | Path) -> list[dict[str, Any]]:
    """Parse plan file with caching for performance.

    Caches parsed tasks based on file modification time to avoid re-parsing
    unchanged plan files. Cache is automatically invalidated when file changes.

    Args:
        plan_path: Path to plan markdown file

    Returns:
        List of task dictionaries from parse_plan_tasks()

    Raises:
        PlanParseError: If plan file cannot be parsed

    Examples:
        >>> tasks = parse_plan_with_cache("plan.md")
        >>> len(tasks)
        3

        >>> # Second call uses cache
        >>> tasks2 = parse_plan_with_cache("plan.md")
        >>> tasks == tasks2
        True
    """
    plan_file = Path(plan_path)

    # Get file modification time
    try:
        mtime = plan_file.stat().st_mtime
    except OSError as e:
        raise FileNotFoundError(f"Plan file not found: {plan_file}") from e

    # Check cache
    cache_key = str(plan_file.absolute())
    if cache_key in _plan_cache:
        cached_mtime, cached_tasks = _plan_cache[cache_key]
        if cached_mtime == mtime:
            # Cache hit - file hasn't changed
            return cached_tasks

    # Cache miss - parse plan
    tasks = parse_plan_tasks(plan_file)

    # Update cache
    _plan_cache[cache_key] = (mtime, tasks)

    return tasks


def clear_plan_cache() -> None:
    """Clear the plan parsing cache.

    Useful for testing or when external file changes need to be detected.
    """
    global _plan_cache
    _plan_cache.clear()


# ============================================================================
# Practical Verification Functions
# ============================================================================

def parse_plan_requirements(plan_path: str | Path) -> dict[str, Any]:
    """Extract requirements from plan.md for practical verification.

    Parses plan file to extract acceptance criteria, success metrics, and
    constraints. This enables verification without requiring a separate PRD document.

    Args:
        plan_path: Path to plan markdown file

    Returns:
        Dictionary with keys:
            - acceptance_criteria (list[str]): Acceptance criteria checkboxes
            - success_metrics (list[str]): Success metric checkboxes
            - constraints (list[str]): Constraint descriptions
            - requirements (list[str]): All requirement checkboxes combined

    Raises:
        FileNotFoundError: If plan file doesn't exist
        PlanParseError: If plan file cannot be parsed

    Examples:
        >>> reqs = parse_plan_requirements("plan.md")
        >>> reqs["acceptance_criteria"]
        ['All tests pass', 'Documentation complete']
    """
    from scripts.plan_parser import PlanParseError

    plan_file = Path(plan_path)

    if not plan_file.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_file}")

    try:
        plan_text = plan_file.read_text(encoding="utf-8")
    except OSError as e:
        raise PlanParseError(f"Failed to read plan file {plan_file}: {e}") from e

    requirements = {
        "acceptance_criteria": [],
        "success_metrics": [],
        "constraints": [],
        "requirements": [],
    }

    # Extract acceptance criteria section
    acceptance_section = _extract_section(plan_text, "Acceptance Criteria")
    if acceptance_section:
        requirements["acceptance_criteria"] = _extract_checkboxes(acceptance_section)

    # Extract success metrics section
    metrics_section = _extract_section(plan_text, "Success Metrics")
    if metrics_section:
        requirements["success_metrics"] = _extract_checkboxes(metrics_section)

    # Extract constraints section
    constraints_section = _extract_section(plan_text, "Constraints")
    if constraints_section:
        requirements["constraints"] = _extract_constraints(constraints_section)

    # Combine all requirements for easy checking
    requirements["requirements"] = (
        requirements["acceptance_criteria"] +
        requirements["success_metrics"]
    )

    return requirements


def _extract_section(text: str, section_name: str) -> str:
    """Extract a section from plan text by section name.

    Args:
        text: Full plan text
        section_name: Name of section to extract (e.g., "Acceptance Criteria")

    Returns:
        Section text as string, or empty string if not found
    """
    import re

    # Match section header (## or ###) followed by section name
    # Don't escape the section name to allow flexible matching
    pattern = rf"^##\s+{re.escape(section_name)}\s*$"
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)

    if not match:
        return ""

    # Find the start of the next section (or end of file)
    section_start = match.end()
    next_section = re.search(r"^##\s+", text[section_start:], re.MULTILINE)

    if next_section:
        section_end = section_start + next_section.start()
        return text[section_start:section_end].strip()
    else:
        # Section goes to end of file
        return text[section_start:].strip()


def _extract_checkboxes(text: str) -> list[str]:
    """Extract checkbox text from markdown section.

    Args:
        text: Section text containing checkboxes

    Returns:
        List of checkbox descriptions (without [ ] or [x] markers)
    """
    import re

    # Match markdown checkboxes: - [ ] or - [x] followed by text
    pattern = r"^[\s]*[-*+]\s*\[[ xX]\]\s*(.+)$"
    matches = re.findall(pattern, text, re.MULTILINE)

    return [match.strip() for match in matches]


def _extract_constraints(text: str) -> list[str]:
    """Extract constraint descriptions from section.

    Args:
        text: Constraints section text

    Returns:
        List of constraint descriptions
    """
    # Split by lines and filter out empty lines and headers
    lines = text.split("\n")
    constraints = []

    for line in lines:
        line = line.strip()
        # Skip empty lines, headers, and markdown list markers
        if not line or line.startswith("#") or line.startswith("-") or line.startswith("*"):
            if line.startswith("-") or line.startswith("*"):
                # Remove list marker and keep the text
                constraint_text = line.lstrip("-*").strip()
                if constraint_text:
                    constraints.append(constraint_text)
            continue

        # Regular text line might be a constraint
        if line:
            constraints.append(line)

    return constraints


def verify_completion_against_requirements(
    tasks: list[dict[str, Any]],
    requirements: dict[str, Any]
) -> dict[str, Any]:
    """Check if all plan requirements are satisfied by completed tasks.

    Compares completed tasks against acceptance criteria and success metrics
    extracted from the plan file.

    Args:
        tasks: List of task dictionaries from parse_plan_tasks()
        requirements: Requirements dictionary from parse_plan_requirements()

    Returns:
        Dictionary with keys:
            - all_requirements_met (bool): True if all requirements satisfied
            - missing_criteria (list[str]): Requirements not yet met
            - matched_criteria (list[str]): Requirements that are met
            - completion_rate (float): Percentage of requirements met

    Examples:
        >>> tasks = [{"text": "Implement feature X", "complete": True}]
        >>> reqs = {"requirements": ["Implement feature X", "Write tests"]}
        >>> result = verify_completion_against_requirements(tasks, reqs)
        >>> result["all_requirements_met"]
        False
        >>> result["missing_criteria"]
        ['Write tests']
    """
    # Get completed task texts
    completed_tasks = [task for task in tasks if task.get("complete", False)]
    completed_texts = [task.get("text", "").strip().lower() for task in completed_tasks]

    # Check each requirement
    missing_criteria = []
    matched_criteria = []

    for requirement in requirements.get("requirements", []):
        requirement_lower = requirement.strip().lower()

        # Check if any completed task matches this requirement
        # Use flexible matching: substring matching OR keyword overlap
        is_matched = False

        for completed_text in completed_texts:
            # Method 1: Direct substring matching (exact match or substring)
            if requirement_lower in completed_text or completed_text in requirement_lower:
                is_matched = True
                break

            # Method 2: Keyword overlap (split by spaces and check for common words)
            # Require 80% overlap to avoid false positives from common words
            requirement_words = set(requirement_lower.split())
            completed_words = set(completed_text.split())

            # If 80% or more of requirement words appear in completed text, consider it matched
            # This higher threshold reduces false matches from common words like "task", "complete"
            if requirement_words and completed_words:
                overlap = requirement_words & completed_words
                overlap_ratio = len(overlap) / len(requirement_words)
                if overlap_ratio >= 0.8:
                    is_matched = True
                    break

        if is_matched:
            matched_criteria.append(requirement)
        else:
            missing_criteria.append(requirement)

    # Calculate completion rate
    total_requirements = len(requirements.get("requirements", []))
    completion_rate = (
        len(matched_criteria) / total_requirements if total_requirements > 0 else 1.0
    )

    return {
        "all_requirements_met": len(missing_criteria) == 0,
        "missing_criteria": missing_criteria,
        "matched_criteria": matched_criteria,
        "completion_rate": completion_rate,
    }


def extract_user_concerns_from_chat(
    transcript_path: str | None,
    lookback_turns: int = 10
) -> list[dict[str, Any]]:
    """Extract user-reported issues from recent conversation.

    Parses transcript to find user concerns, blockers, and negative feedback
    from recent conversation turns. This enables practical verification by
    catching "that's not what I wanted" cases before declaring done.

    Args:
        transcript_path: Path to conversation transcript file (optional)
        lookback_turns: Number of recent turns to analyze (default: 10)

    Returns:
        List of concern dictionaries with keys:
            - turn_id (int): Turn number in conversation
            - concern (str): User's concern text (truncated to 200 chars)
            - severity (str): "blocker", "issue", or "correction"

    Examples:
        >>> concerns = extract_user_concerns_from_chat("transcript.jsonl")
        >>> len(concerns)
        2
        >>> concerns[0]["severity"]
        'blocker'
    """
    concerns = []

    if not transcript_path:
        # No transcript available
        return concerns

    transcript_file = Path(transcript_path)

    if not transcript_file.exists():
        # Transcript file doesn't exist yet
        return concerns

    try:
        # Read transcript (JSONL format from handoff system)
        import json

        turns = []
        with open(transcript_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        turn = json.loads(line)
                        turns.append(turn)
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue

        # Get last N turns
        recent_turns = turns[-lookback_turns:] if len(turns) > lookback_turns else turns

        # Look for user concerns
        for i, turn in enumerate(recent_turns):
            if turn.get("role") == "user":
                content = turn.get("content", "")

                # Check for concern indicators
                concern_indicators = {
                    "blocker": ["blocker", "blocked", "can't proceed", "stuck", "doesn't work"],
                    "issue": ["wrong", "bug", "error", "issue", "problem", "not working"],
                    "correction": ["fix this", "change this", "not what I wanted", "try again"],
                }

                for severity, indicators in concern_indicators.items():
                    if any(indicator in content.lower() for indicator in indicators):
                        concerns.append({
                            "turn_id": turns.index(turn) + 1,  # 1-based turn number
                            "concern": content[:200],  # Truncate to 200 chars
                            "severity": severity,
                        })
                        break  # Only record highest severity concern

    except (OSError, json.JSONDecodeError):
        # Fail silently - transcript issues shouldn't break loop
        pass

    return concerns
