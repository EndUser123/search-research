"""
Behavioral Gate Functions for Stop System

This module implements gate functions that detect specific behavioral patterns
in assistant responses. Each gate analyzes text and tool usage to determine
if a behavioral protocol was violated.

Gate Types:
- BLOCKING: Hard stop - prevents continuation
- ADVISORY: Warning only - allows continuation

Configuration:
- Environment Variables:
  - BEHAVIOR_GATES_ENABLED: "true" (default) or "false" to disable all gates
  - BEHAVIOR_GATES_MODE: "blocking" (default) or "advisory" to change Gate 3 mode
- Per-Project Blacklist: .behavior_gates_blacklist.json in working directory

Telemetry:
- Integrates with hook-audit system via P:/.claude/logs/hook_blocks.jsonl
- Advisory events logged to enforcement_events.jsonl for replay analysis

Author: Stop System Team
Created: 2025-03-01
Updated: 2025-03-01 (v2 - reduced false positives, added telemetry)
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add hooks dir to path for turn_mode import
_HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from __lib.turn_mode import classify as _classify_turn_mode

# ============================================================================
# CONFIGURATION
# ============================================================================

def _are_gates_enabled() -> bool:
    """
    Check if behavior gates are enabled via environment variable.

    Returns:
        True if gates are enabled (default), False if disabled

    Environment Variable:
        BEHAVIOR_GATES_ENABLED: "true" (default) or "false"
    """
    env_value = os.environ.get("BEHAVIOR_GATES_ENABLED", "true").lower()
    return env_value == "true"


def _get_gates_mode() -> str:
    """
    Get the gates mode (blocking or advisory).

    Returns:
        "blocking" (default) or "advisory"

    Environment Variable:
        BEHAVIOR_GATES_MODE: "blocking" (default) or "advisory"
        When "advisory", Gate 3 becomes advisory instead of blocking
    """
    env_value = os.environ.get("BEHAVIOR_GATES_MODE", "blocking").lower()
    return env_value if env_value in ("blocking", "advisory") else "blocking"


def _load_project_blacklist(working_dir: Path | None = None) -> list[str]:
    """
    Load per-project tool blacklist from working directory.

    Args:
        working_dir: Directory to search for blacklist file (defaults to cwd)

    Returns:
        List of blacklisted tool names (empty if none found)

    File Format:
        .behavior_gates_blacklist.json in working directory:
        {
            "tool_blacklist": ["CustomTool1", "CustomTool2"]
        }

    Note:
        Project blacklist is merged with global blacklist.
        Project configuration takes precedence over global defaults.
    """
    if working_dir is None:
        working_dir = Path.cwd()

    blacklist_file = working_dir / ".behavior_gates_blacklist.json"

    if not blacklist_file.exists():
        return []

    try:
        with open(blacklist_file, encoding="utf-8") as f:
            config = json.load(f)
            return config.get("tool_blacklist", [])
    except (OSError, json.JSONDecodeError) as e:
        # Log error but return empty list to prevent crashes
        print(f"Warning: Failed to load project blacklist from {blacklist_file}: {e}")
        return []


# ============================================================================
# TELEMETRY (Hook Audit Integration)
# ============================================================================

# Startup verification flag
_telemetry_verified = False


def _verify_telemetry_dirs() -> None:
    """
    Verify telemetry directories are writable on first call.

    Logs a warning on stderr if directories cannot be created.
    This is called once on the first _log_gate_violation() call.
    """
    global _telemetry_verified
    if _telemetry_verified:
        return

    try:
        # Test both log paths
        blocking_log = Path(__file__).parent / ".claude" / "logs" / "hook_blocks.jsonl"
        advisory_log = Path(__file__).parent / ".claude" / "hooks" / "session_data" / "enforcement_events.jsonl"

        for log_path in (blocking_log, advisory_log):
            log_path.parent.mkdir(parents=True, exist_ok=True)
            # Test writability by touching the file
            if not log_path.exists():
                log_path.touch()

    except Exception as e:
        print(f"[Stop] behavior_gates telemetry directory verification failed: {e}", file=sys.stderr)

    _telemetry_verified = True


def _log_gate_violation(
    gate_name: str,
    severity: str,
    reason: str,
    text: str,
    tools_used: list[str],
    working_dir: Path | None = None
) -> None:
    """
    Log gate violations to hook-audit system for compliance tracking.

    Args:
        gate_name: Name of the gate that triggered (e.g., "gate3_agreement")
        severity: "blocking" or "advisory"
        reason: Human-readable violation reason
        text: Response text that triggered the violation
        tools_used: List of tools used in the response
        working_dir: Working directory (optional, for context)

    Log Files:
        - Blocking events: P:/.claude/logs/hook_blocks.jsonl
        - Advisory events: P:/.claude/hooks/session_data/enforcement_events.jsonl
    """
    # Run startup verification on first call
    _verify_telemetry_dirs()

    try:

        # Determine log file based on severity
        if severity == "blocking":
            log_file = Path(__file__).parent / ".claude" / "logs" / "hook_blocks.jsonl"
        else:
            # Advisory events go to enforcement events for replay analysis
            log_file = Path(__file__).parent / ".claude" / "hooks" / "session_data" / "enforcement_events.jsonl"

        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create log entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "gate_name": gate_name,
            "severity": severity,
            "reason": reason,
            "response_snippet": text[:200] + "..." if len(text) > 200 else text,
            "tools_used": sorted(tools_used),
            "working_dir": str(working_dir) if working_dir else None,
        }

        # Append to log file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    except Exception as e:
        # Log to stderr for visibility (doesn't break hook)
        print(f"[Stop] behavior_gates telemetry error: {e}", file=sys.stderr)


# ============================================================================
# HELPER UTILITIES
# ============================================================================

def _extract_tools_used(tools_data: str | list | dict) -> list[str]:
    """
    Extract tool names from a tool-use block, list of tool dicts, or hook payload.

    Args:
        tools_data: Text with XML tags, list of tool dicts, or data dict

    Returns:
        List of tool names used (e.g., ["Glob", "Read", "Edit"])
    """
    # Case 1: Whole data dict passed
    if isinstance(tools_data, dict):
        # Prefer tools_used (list) then tool_calls (string)
        if "tools_used" in tools_data and isinstance(tools_data["tools_used"], list):
            tools_data = tools_data["tools_used"]
        else:
            tools_data = tools_data.get("tool_calls", "")

    # Case 2: List of tool dicts (standard hook format)
    if isinstance(tools_data, list):
        tools = []
        for tool in tools_data:
            name = tool.get("name", "") if isinstance(tool, dict) else str(tool)
            if name:
                tools.append(name)
        return tools

    # Case 3: Raw string with XML tags (regex extraction)
    if isinstance(tools_data, str):
        # Match all <tool_name> tags within tool-use blocks
        pattern = r"<tool_name>(.*?)</tool_name>"
        matches = re.findall(pattern, tools_data)
        return matches

    return []


def _normalize_text(text: str) -> str:
    """
    Normalize text for consistent pattern matching.

    Args:
        text: Raw text to normalize

    Returns:
        Normalized text with consistent spacing and case
    """
    # Replace multiple spaces with single space
    text = re.sub(r"\s+", " ", text)
    # Trim leading/trailing whitespace
    text = text.strip()
    return text


def _strip_region(text: str, start: int, end: int) -> str:
    """Remove a region from text, replacing with spaces to preserve position."""
    if start < 0 or end > len(text) or start >= end:
        return text
    return text[:start] + " " * (end - start) + text[end:]


def _strip_quoted_regions(text: str) -> tuple[str, bool]:
    # DESIGN NOTE: QUOTE / META STRIPPING CONTRACT
    #
    # Purpose
    # This function strips *non-operative* text regions before pattern matching so that
    # meta discussion and examples do not trigger agreement / commitment gates.
    #
    # Covered regions
    # We treat the following as QUOTED/META and strip them:
    #   - Fenced code blocks  (```...```)
    #   - Inline code         (`...`)
    #   - Straight ASCII quotes:  "..." and '...'
    #   - Curly Unicode quotes:
    #       "..." (U+201C / U+201D), '...' (U+2018 / U+2019)
    #   - Dollar-quoted spans: $...$
    #   - HTML entity-quoted spans:
    #       &quot;...&quot;, &apos;...&apos;, &#39;...&#39;
    #
    # Invariants
    #   - Only *paired* delimiters are stripped. Bare characters (a single curly
    #     apostrophe in I'll, a lone $, or a single &quot;) must remain intact.
    #   - Stripping a region sets the "had_meta" flag. Gate logic uses this to allow a
    #     meta-only trigger to return early (no block), while still blocking when a
    #     real, unquoted agreement/commitment appears alongside the meta.
    #   - Two regression tests encode this invariant and MUST keep passing:
    #       - real_dollar_quoted_with_real_commitment_beside_it_still_blocks
    #       - real_unicode_quoted_with_real_commitment_beside_it_still_blocks
    #
    # Why Unicode and entity forms are included
    # Real-world logs contain typographic quotes and entity-encoded quotes, so limiting
    # stripping to ASCII "..." / '...' left known false-positive paths. We normalize
    # these variants here so that only operative, unquoted agreement/commitment
    # language is visible to the gate.
    #
    # Risk boundary
    # The regexes are intentionally narrow:
    #   - Curly-quote patterns require matching open/close delimiters and exclude
    #     curly characters in the interior, so contractions with a single curly
    #     apostrophe do NOT match.
    #   - Dollar-quoted and entity-quoted patterns require both delimiters; bare $
    #     or entity tokens survive.
    #
    # If you modify this logic:
    #   - Update the corresponding tests in tests/test_gate3_quote_suppression.py
    #   - Re-run:  python -m pytest tests/test_gate3_quote_suppression.py -v
    #   - Do NOT simplify by dropping Unicode/entity handling or by broad "ignore
    #     weird text" heuristics; that reintroduces known faults.

    """
    Strip code blocks, quotes, and blockquotes before pattern matching.

    Returns:
        Tuple of (stripped_text, had_meta_content)
        - stripped_text: Text with quoted regions replaced by spaces
        - had_meta_content: True if original had code blocks/quotes that were stripped
    """
    original = text
    had_meta = False

    # Normalize line endings
    text = text.replace("\r\n", "\n")

    # Remove fenced code blocks (```...```)
    while True:
        start = text.find("```")
        if start == -1:
            break
        end = text.find("```", start + 3)
        if end == -1:
            break
        had_meta = True
        text = _strip_region(text, start, end + 3)

    # Remove inline code (`...`)
    text = re.sub(r"`[^`]*`", " ", text)

    # Remove double-quoted strings — straight ASCII
    text = re.sub(r'"[^"]*"', " ", text)

    # Remove single-quoted strings — straight ASCII
    text = re.sub(r"'[^']*'", " ", text)

    # Remove double-quoted strings — Unicode curly quotes
    text = re.sub(r'[“”][^“”]*[“”]', " ", text)

    # Remove single-quoted strings — Unicode curly quotes
    text = re.sub(r'[‘’][^‘’]*[‘’]', " ", text)

    # Remove dollar-quoted strings (LaTeX/math notation)
    text = re.sub(r"\$[^$]*\$", " ", text)

    # Remove HTML entities for quotes
    text = re.sub(r"&quot;[^&]*&quot;", " ", text)
    text = re.sub(r"&apos;[^&]*&apos;", " ", text)
    text = re.sub(r"&#39;[^&#]*&#39;", " ", text)

    # Remove blockquote lines (lines starting with >)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if re.match(r"^\s*>", line):
            had_meta = True
            lines[i] = " "
    text = "\n".join(lines)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text, had_meta or (original != text)


def _load_indicators(file_path: Path | None = None, working_dir: Path | None = None) -> dict[str, list[str]]:
    """
    Load behavioral indicator phrases from config file.

    Args:
        file_path: Path to indicators JSON file (optional)
        working_dir: Working directory for project blacklist (optional)

    Returns:
        Dictionary mapping indicator categories to phrase lists

    Note:
        If file_path is None, returns empty dict.
        Used for extensibility - can load custom indicators per project.

    Project Blacklist Integration:
        Merges global tool_blacklist with per-project blacklist from
        .behavior_gates_blacklist.json in working_dir (if present).
        Project blacklist takes precedence (tools are added to global list).
    """
    if file_path is None or not file_path.exists():
        indicators = {}
    else:
        try:
            with open(file_path, encoding="utf-8") as f:
                indicators = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            # Log error but return empty dict to prevent crashes
            print(f"Warning: Failed to load indicators from {file_path}: {e}")
            indicators = {}

    # Merge project blacklist if present
    project_blacklist = _load_project_blacklist(working_dir)
    if project_blacklist:
        # Get global blacklist (or default to ["Task"])
        global_blacklist = indicators.get("tool_blacklist", ["Task"])

        # Handle v2.0 format where tool_blacklist is a dict
        if isinstance(global_blacklist, dict):
            # v2.0 format: tool_blacklist contains patterns, not tool names
            # Use default blacklist and merge with project
            global_blacklist = ["Task"]

        # Merge: combine global + project, remove duplicates
        # Both must be lists at this point
        merged_blacklist = list(set(global_blacklist + project_blacklist))
        indicators["tool_blacklist"] = merged_blacklist

    return indicators


# ============================================================================
# GATE 3: Agreement Detection (BLOCKING)
# ============================================================================

def _has_tool_mention_in_same_sentence(text: str, tools: list[str]) -> bool:
    """
    Check if text mentions implementation tools in the same sentence as agreement.

    This reduces false positives where agent says "I'll fix it using Edit".

    Args:
        text: Response text to check
        tools: List of tool names to look for

    Returns:
        True if any tool is mentioned in the same sentence as an agreement phrase
    """
    # Split into sentences (rough heuristic)
    sentences = re.split(r'[.!?]+', text)

    # Tool name patterns to look for in text
    tool_patterns = {
        'Edit': r'\bEdit\b',
        'Write': r'\bWrite\b',
        'Bash': r'\b(?:Bash|bash)\b',
        'Task': r'\bTask\b',
    }

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Check if sentence has agreement language
        has_agreement = bool(re.search(
            r"\b(I'll|I will|Let me|I shall)\b",
            sentence,
            re.IGNORECASE
        ))

        if has_agreement:
            # Check if same sentence mentions a tool
            for tool in tools:
                if tool in tool_patterns and re.search(tool_patterns[tool], sentence, re.IGNORECASE):
                    return True

    return False


def _is_question_format(text: str) -> bool:
    """
    Check if text is in question format (should not trigger agreement gate).

    Examples:
        "Should I update X?" → True (question, not agreement)
        "I'll update X." → False (agreement)

    Args:
        text: Response text to check

    Returns:
        True if text appears to be a question
    """
    # Check for question mark
    if '?' in text:
        return True

    # Check for question-starting patterns
    question_starts = [
        r'^(?:Should|Would|Could|Can|May|Might|Do|Does|Is|Are)\b',
        r'^(?:Do you want|Would you like|Should I)\b',
    ]

    normalized = _normalize_text(text)
    for pattern in question_starts:
        if re.match(pattern, normalized, re.IGNORECASE):
            return True

    return False


def check_gate3_agreement(text: str, tools_used: list[str], working_dir: Path | None = None, user_prompt: str | None = None) -> tuple[bool, str]:
    """
    Check if assistant agreed to perform action without Edit/Write/Bash.

    Gate Type: BLOCKING by default, ADVISORY when BEHAVIOR_GATES_MODE=advisory

    Behavioral Pattern:
    - Assistant responds with agreement language ("I'll", "I will", "Let me", etc.)
    - But response contains NO Edit/Write/Bash tool calls
    - Indicates: Assistant agreed to do work but didn't actually do it

    Examples of Violations:
        "I'll update the configuration for you."
        (with no Edit/Write/Bash in tools_used)

        "Let me check the logs and fix the issue."
        (with only Read in tools_used - no Edit/Write/Bash)

    Examples of Non-Violations:
        "I'll update the configuration."
        (with Edit tool used)

        "I'll fix it using Edit."
        (tool mentioned in text - allows implementation)

        "Should I update X?"
        (question format - not an agreement)

        "Here's what I found:"
        (no agreement language - just reporting)

    v2 Improvements:
    - Tool-first ordering: Check implementation tools BEFORE pattern matching
    - Reduced false positives:
      * Ignores question format ("Should I...?")
      * Allows tool mentions in same sentence ("I'll fix it using Edit")
      * More specific patterns (excludes generic agreement words)
    - Plan-mode exemption: future commitments in plan/execution-report turns are allowed

    Args:
        text: Assistant response text to analyze
        tools_used: List of tool names used in response
        working_dir: Working directory (optional, for telemetry)
        user_prompt: User prompt text (optional, for turn-mode classification)

    Returns:
        Tuple of (is_violation, reason):
        - is_violation: True if gate triggered (blocking or advisory based on mode)
        - reason: Human-readable explanation

    Environment Variables:
        BEHAVIOR_GATES_ENABLED: "false" disables this gate (returns False, "")
        BEHAVIOR_GATES_MODE: "advisory" makes this gate advisory instead of blocking
    """
    # Check if gates are enabled
    if not _are_gates_enabled():
        return (False, "")

    # ========================================================================
    # v2: TOOL-FIRST CHECKING (fixes ordering bug)
    # ========================================================================
    # Required tools that fulfill an agreement
    required_tools = {"Edit", "Write", "Bash", "Task"}

    # Check if any required tools were used (EARLY EXIT)
    tools_set = set(tools_used)
    has_implementation = bool(tools_set & required_tools)

    if has_implementation:
        # Tools present → agreement fulfilled → no violation
        return (False, "")

    # ========================================================================
    # v2: REDUCED FALSE POSITIVES
    # ========================================================================
    # Check for question format (questions are not agreements)
    if _is_question_format(text):
        return (False, "")

    # Check for tool mentions in same sentence as agreement
    if _has_tool_mention_in_same_sentence(text, list(required_tools)):
        # Agent mentioned tools in text → likely implementing → no violation
        return (False, "")

    # Plan-mode check: skip if turn is plan or execution-report
    # (future commitments like "I'll do X next" are legitimate planning language)
    try:
        turn_mode = _classify_turn_mode({
            "user_prompt": user_prompt or "",
            "response": text,
        })
        if turn_mode in ("plan", "execution-report"):
            return (False, "")
    except Exception:
        pass  # Fail open — gate fires if classification fails

    # ========================================================================
    # PATTERN MATCHING (only if tools not found)
    # ========================================================================
    # Load agreement patterns from config
    config_path = Path(__file__).parent / ".claude" / "skills" / "code" / "behavior_gates_config.json"
    indicators = _load_indicators(config_path)

    # Get agreement patterns, or use defaults if config missing
    # v2: More specific patterns to reduce false positives
    # Support both v2.0 nested format and v1 flat format
    agreement_config = indicators.get("agreement_patterns", [])

    # Handle v2.0 nested config format
    if isinstance(agreement_config, dict):
        agreement_patterns = agreement_config.get("direct_commitments", [
            # Fallback to defaults if direct_commitments missing
            r"\bI'll\s+(?:update|fix|edit|modify|change|create|write|add|remove|delete|implement|refactor|optimize)\b",
            r"\bLet\s+me\s+(?:update|fix|edit|modify|change|create|write|add|remove|delete)\b",
            r"\bI\s+(?:will|shall)\s+(?:update|fix|edit|modify|change|create|write|implement)\b",
        ])
    else:
        # v1 flat format (backward compatibility)
        agreement_patterns = agreement_config if agreement_config else [
            r"\bI'll\s+(?:update|fix|edit|modify|change|create|write|add|remove|delete|implement|refactor|optimize)\b",
            r"\bLet\s+me\s+(?:update|fix|edit|modify|change|create|write|add|remove|delete)\b",
            r"\bI\s+(?:will|shall)\s+(?:update|fix|edit|modify|change|create|write|implement)\b",
        ]

    # v3: Strip quoted/code regions BEFORE pattern matching
    # This prevents false positives on:
    # - "The phrase "I will update" triggered the gate."
    # - Code blocks showing trigger examples
    # - Blockquotes with trigger phrases
    stripped_text, had_quoted_content = _strip_quoted_regions(text)
    normalized_stripped = _normalize_text(stripped_text)

    # Check if any agreement pattern matches on stripped text
    has_agreement = False
    matched_pattern = None
    for pattern in agreement_patterns:
        if re.search(pattern, normalized_stripped, re.IGNORECASE):
            has_agreement = True
            matched_pattern = pattern
            break

    # If agreement found ONLY in quoted regions (not in stripped text),
    # this is meta discussion about triggers, not a real agreement
    if not has_agreement and had_quoted_content:
        return (False, "")

    # Normalize original for fallback matching (if agreement was found in stripped)
    normalized_text = _normalize_text(text)

    # Check if any agreement pattern matches
    if not has_agreement:
        for pattern in agreement_patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                has_agreement = True
                matched_pattern = pattern
                break

    # If no agreement detected, no violation
    if not has_agreement:
        return (False, "")

    # ========================================================================
    # VIOLATION DETECTED
    # ========================================================================
    # Agreement detected but no implementation tools used → VIOLATION
    reason = (
        f"Agreement detected (matched pattern: {matched_pattern}) "
        f"but no implementation tools used. "
        f"Required: {', '.join(sorted(required_tools))}. "
        f"Found: {', '.join(sorted(tools_used)) if tools_used else 'none'}."
    )

    # Determine severity for telemetry
    mode = _get_gates_mode()
    severity = "advisory" if mode == "advisory" else "blocking"

    # Log to hook-audit system
    _log_gate_violation(
        gate_name="gate3_agreement",
        severity=severity,
        reason=reason,
        text=text,
        tools_used=tools_used,
        working_dir=working_dir
    )

    return (True, reason)


# ============================================================================
# GATE 1: Guidance Detection (ADVISORY)
# ============================================================================

def check_gate1_guidance(text: str, tools_used: list[str], working_dir: Path | None = None) -> tuple[bool, str]:
    """
    Check if assistant gave guidance without Read verification.

    Gate Type: ADVISORY (warns but allows continuation)

    Behavioral Pattern:
    - Assistant provides specific guidance about code/implementation
    - But response contains NO Read tool calls
    - Indicates: Guidance given without verifying current code state

    Examples of Violations:
        "You should modify the validate() function in path_validator.py"
        (with no Read in tools_used)

        "The issue is in the hook configuration"
        (with no Read in tools_used)

    Examples of Non-Violations:
        "Based on the code I just read, you should modify validate()"
        (Read was used before giving guidance)

        "Let me read that file first"
        (Read was used)

    v2 Improvements:
    - Added telemetry logging to enforcement_events.jsonl
    - Patterns now exclude qualified guidance (e.g., "Based on what I read...")

    Args:
        text: Assistant response text to analyze
        tools_used: List of tool names used in response
        working_dir: Working directory (optional, for telemetry)

    Returns:
        Tuple of (is_violation, reason):
        - is_violation: True if advisory gate triggered
        - reason: Human-readable explanation

    Environment Variables:
        BEHAVIOR_GATES_ENABLED: "false" disables this gate (returns False, "")
    """
    # Check if gates are enabled
    if not _are_gates_enabled():
        return (False, "")

    # Load guidance patterns from config
    config_path = Path(__file__).parent / ".claude" / "skills" / "code" / "behavior_gates_config.json"
    indicators = _load_indicators(config_path)

    # Get guidance patterns, or use defaults if config missing
    # Support both v2.0 nested format and v1 flat format
    guidance_config = indicators.get("guidance_patterns", [])

    # Handle v2.0 nested config format
    if isinstance(guidance_config, dict):
        guidance_patterns = guidance_config.get("direct_guidance", [
            # Fallback to defaults if direct_guidance missing
            r"\byou\s+should\s+(?:modify|change|update|edit|fix|add|remove|delete)\b",
            r"\bmodify\s+the\s+(?:function|method|class|variable|parameter)\b",
            r"\bchange\s+the\s+(?:configuration|config|settings?)\b",
            r"\bthe\s+issue\s+is\s+in\b",
            r"\bthe\s+problem\s+is\s+(?:in|at|with)\b",
            r"\byou\s+need\s+to\s+(?:update|edit|modify|fix)\b",
            r"\btry\s+(?:modifying|changing|updating|editing)\b",
            r"\bgo\s+to\s+(?:the\s+)?(?:file|function|method)\b",
            r"\bin\s+[\w./]+\s+(?:you\s+should|try|change|modify)\b",
            r"\bfix\s+the\s+(?:function|method|class|code)\b",
        ])
    else:
        # v1 flat format (backward compatibility)
        guidance_patterns = guidance_config if guidance_config else [
            r"\byou\s+should\s+(?:modify|change|update|edit|fix|add|remove|delete)\b",
            r"\bmodify\s+the\s+(?:function|method|class|variable|parameter)\b",
            r"\bchange\s+the\s+(?:configuration|config|settings?)\b",
            r"\bthe\s+issue\s+is\s+in\b",
            r"\bthe\s+problem\s+is\s+(?:in|at|with)\b",
            r"\byou\s+need\s+to\s+(?:update|edit|modify|fix)\b",
            r"\btry\s+(?:modifying|changing|updating|editing)\b",
            r"\bgo\s+to\s+(?:the\s+)?(?:file|function|method)\b",
            r"\bin\s+[\w./]+\s+(?:you\s+should|try|change|modify)\b",
            r"\bfix\s+the\s+(?:function|method|class|code)\b",
        ]

    # Normalize text for consistent matching
    normalized_text = _normalize_text(text)

    # Check if any guidance pattern matches
    has_guidance = False
    matched_pattern = None
    for pattern in guidance_patterns:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            has_guidance = True
            matched_pattern = pattern
            break

    # If no guidance detected, no violation
    if not has_guidance:
        return (False, "")

    # Check if Read tool was used
    has_read_verification = "Read" in tools_used

    # If guidance detected but no Read verification → VIOLATION
    if not has_read_verification:
        reason = (
            f"Guidance detected (matched pattern: {matched_pattern}) "
            f"without Read verification. "
            f"Guidance should be based on current code state verified with Read tool. "
            f"Tools used: {', '.join(sorted(tools_used)) if tools_used else 'none'}."
        )

        # v2: Log to hook-audit system
        _log_gate_violation(
            gate_name="gate1_guidance",
            severity="advisory",
            reason=reason,
            text=text,
            tools_used=tools_used,
            working_dir=working_dir
        )

        return (True, reason)

    # Guidance detected and verified with Read tool
    return (False, "")


# ============================================================================
# GATE 2: Tool Blacklist (ADVISORY)
# ============================================================================

def check_gate2_tools(text: str, tools_used: list[str], working_dir: Path | None = None) -> tuple[bool, str]:
    """
    Check if assistant used blacklisted tools.

    Gate Type: ADVISORY (warns but allows continuation)

    Behavioral Pattern:
    - Assistant uses tools from advisory blacklist
    - Currently: Task tool (reserved for system use, not assistant)
    - Indicates: Assistant may be circumventing intended workflows

    Examples of Violations:
        Response contains Task tool in tools_used

    Examples of Non-Violations:
        Response uses Read, Edit, Write, Bash, Glob, Grep normally

    v2 Improvements:
    - Added telemetry logging to enforcement_events.jsonl
    - Per-project blacklist merge with global blacklist

    Args:
        text: Assistant response text to analyze (currently unused but kept for consistency)
        tools_used: List of tool names used in response
        working_dir: Working directory for project blacklist (optional)

    Returns:
        Tuple of (is_violation, reason):
        - is_violation: True if advisory gate triggered
        - reason: Human-readable explanation

    Environment Variables:
        BEHAVIOR_GATES_ENABLED: "false" disables this gate (returns False, "")

    Per-Project Configuration:
        .behavior_gates_blacklist.json in working_dir can add tools to blacklist
    """
    # Check if gates are enabled
    if not _are_gates_enabled():
        return (False, "")

    # Load tool blacklist from config (with project blacklist merge)
    config_path = Path(__file__).parent / ".claude" / "skills" / "code" / "behavior_gates_config.json"
    indicators = _load_indicators(config_path, working_dir)

    # Get tool blacklist, or use defaults if config missing
    # Support both v2.0 nested format and v1 flat format
    tool_blacklist_config = indicators.get("tool_blacklist", [])

    # Handle v2.0 nested config format (tool_blacklist is now a dict of patterns, not tool names)
    # For Gate 2, we use a simple default list since v2.0 moved to pattern-based detection
    if isinstance(tool_blacklist_config, dict):
        # v2.0 format: tool_blacklist contains patterns, not tool names
        # Use default blacklist for now (pattern-based detection is handled differently)
        tool_blacklist = ["Task"]
    elif isinstance(tool_blacklist_config, list):
        # v1 flat format (backward compatibility)
        tool_blacklist = tool_blacklist_config if tool_blacklist_config else ["Task"]
    else:
        # Fallback to default
        tool_blacklist = ["Task"]

    # Check if any blacklisted tools were used
    tools_set = set(tools_used)
    blacklist_set = set(tool_blacklist)
    blacklisted_used = tools_set & blacklist_set

    # If blacklisted tools detected → VIOLATION
    if blacklisted_used:
        reason = (
            f"Blacklisted tools used: {', '.join(sorted(blacklisted_used))}. "
            f"These tools are reserved for system use and should not be invoked directly. "
            f"All tools used: {', '.join(sorted(tools_used)) if tools_used else 'none'}."
        )

        # v2: Log to hook-audit system
        _log_gate_violation(
            gate_name="gate2_tools",
            severity="advisory",
            reason=reason,
            text=text,
            tools_used=tools_used,
            working_dir=working_dir
        )

        return (True, reason)

    # No blacklisted tools used
    return (False, "")


# ============================================================================
# GATE ORCHESTRATION
# ============================================================================

def run_all_gates(text: str, tools_used: list[str], working_dir: Path | None = None) -> dict[str, tuple[bool, str]]:
    """
    Run all gate functions and aggregate results.

    Args:
        text: Assistant response text to analyze
        tools_used: List of tool names used in response
        working_dir: Working directory for project blacklist (optional)

    Returns:
        Dictionary mapping gate names to (is_violation, reason) tuples:
        {
            "gate3_agreement": (False, ""),
            "gate1_guidance": (True, "Guidance given without Read"),
            "gate2_tools": (False, "")
        }

    Environment Variables:
        BEHAVIOR_GATES_ENABLED: "false" causes all gates to return (False, "")
        BEHAVIOR_GATES_MODE: "advisory" changes Gate 3 from blocking to advisory

    v2 Changes:
    - All gates now receive working_dir for telemetry
    """
    return {
        "gate3_agreement": check_gate3_agreement(text, tools_used, working_dir),
        "gate1_guidance": check_gate1_guidance(text, tools_used, working_dir),
        "gate2_tools": check_gate2_tools(text, tools_used, working_dir),
    }


def check_blocking_gates(text: str, tools_used: list[str], working_dir: Path | None = None) -> tuple[bool, str | None]:
    """
    Check only blocking gates (Gate 3).

    Args:
        text: Assistant response text to analyze
        tools_used: List of tool names used in response
        working_dir: Working directory for project blacklist (optional)

    Returns:
        Tuple of (should_stop, reason):
        - should_stop: True if any blocking gate triggered
        - reason: First blocking violation reason, or None if no violations

    Environment Variables:
        BEHAVIOR_GATES_ENABLED: "false" causes immediate return (False, None)
        BEHAVIOR_GATES_MODE: "advisory" causes Gate 3 to be non-blocking

    v2 Changes:
    - Passes working_dir to gate functions for telemetry
    """
    # Check if gates are enabled
    if not _are_gates_enabled():
        return (False, None)

    # Check if in advisory mode (Gate 3 becomes advisory)
    mode = _get_gates_mode()
    if mode == "advisory":
        # In advisory mode, no gates are blocking
        return (False, None)

    # Check Gate 3 (blocking mode)
    is_violation, reason = check_gate3_agreement(text, tools_used, working_dir)
    if is_violation:
        return (True, reason)

    return (False, None)


def check_advisory_gates(text: str, tools_used: list[str], working_dir: Path | None = None) -> list[tuple[str, str]]:
    """
    Check only advisory gates (Gates 1 and 2).

    Also includes Gate 3 when BEHAVIOR_GATES_MODE=advisory.

    Args:
        text: Assistant response text to analyze
        tools_used: List of tool names used in response
        working_dir: Working directory for project blacklist (optional)

    Returns:
        List of (gate_name, reason) tuples for all advisory violations.
        Empty list if no violations.

    Environment Variables:
        BEHAVIOR_GATES_ENABLED: "false" causes immediate return []

    v2 Changes:
    - Passes working_dir to gate functions for telemetry
    """
    # Check if gates are enabled
    if not _are_gates_enabled():
        return []

    violations = []

    # Check Gate 1 (always advisory)
    is_violation, reason = check_gate1_guidance(text, tools_used, working_dir)
    if is_violation:
        violations.append(("gate1_guidance", reason))

    # Check Gate 2 (always advisory)
    is_violation, reason = check_gate2_tools(text, tools_used, working_dir)
    if is_violation:
        violations.append(("gate2_tools", reason))

    # Check Gate 3 (advisory only when mode is set)
    mode = _get_gates_mode()
    if mode == "advisory":
        is_violation, reason = check_gate3_agreement(text, tools_used, working_dir)
        if is_violation:
            violations.append(("gate3_agreement", reason))

    return violations
