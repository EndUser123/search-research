#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Add hooks directory to path BEFORE importing local modules
_hooks_dir = Path(__file__).resolve().parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

try:
    from session_file_cache import SessionFileCache

    _session_cache = SessionFileCache()
except ImportError as e:
    # Fallback: disable caching if module unavailable
    _session_cache = None
    import logging

    logging.warning(f"SessionFileCache unavailable: {e}")

"""
Command Execution Validator v1.0
================================

Post-generation hook that validates slash command execution compliance.

PARTNER TO: command_directive_injector.py (pre-generation)

STRATEGY:
1. Check if a slash command was invoked this turn
2. Load command expectations from session state
3. Validate response against:
   - DO NOT rules (explicit prohibitions)
   - Description indicators (describing vs executing)
   - Execution evidence (signs of actual execution)
4. BLOCK if response violates command intent

PRINCIPLE: Enforce execution, not description

Runs at: Stop (layer 4_command_validation)
"""

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

hooks_dir = Path(__file__).resolve().parent

# === CONFIGURATION ===

ENABLED = (
    os.environ.get("COMMAND_EXECUTION_VALIDATOR_ENABLED", "true").lower() == "true"
)
LEGACY_SESSION_STATE_FILE = hooks_dir / "session_data/active_command.json"
FALLBACK_SESSION_DATA_DIR = Path(tempfile.gettempdir()) / "claude_hooks" / "session_data"
MAX_STATE_AGE_SECONDS = 300  # 5 minutes - state expires after this

# === DETECTION PATTERNS ===

# Patterns that indicate DESCRIBING a command instead of EXECUTING it
DESCRIPTION_PATTERNS = [
    (
        r"this\s+command\s+(?:provides|offers|enables|allows|supports)",
        "Describes command capabilities",
    ),
    (r"the\s+/\w+\s+command\s+(?:is|does|provides|will)", "Describes command function"),
    (
        r"let\s+me\s+(?:explain|describe|summarize)\s+(?:what|how|the)",
        "Explaining instead of executing",
    ),
    (
        r"here'?s?\s+(?:what|how)\s+(?:the\s+)?/?\w+\s+(?:works|does)",
        "Describing how command works",
    ),
    (
        r"(?:summary|overview)\s+of\s+(?:the\s+)?(?:conversation|discussion|chat)",
        "Created summary instead of executing",
    ),
    (r"conversation\s+summary", "Created conversation summary"),
    (
        r"i'?(?:ll|ve)\s+(?:create|created)\s+(?:a\s+)?(?:comprehensive\s+)?summary",
        "Created summary",
    ),
    (
        r"document(?:ing|ed)\s+(?:all|the)\s+(?:work|changes|improvements)",
        "Documenting instead of executing",
    ),
]

# Patterns that indicate SIMULATING skill output instead of using Skill tool
SIMULATION_PATTERNS = [
    (r"python\s+-c\s+['\"]", "Used python -c to simulate skill output"),
    (r"Bash\(.*python\s+-c", "Used Bash with python -c instead of Skill tool"),
    (
        r"this\s+is\s+what\s+/\w+\s+output\s+looks?\s+like",
        "Describing skill output format",
    ),
    (
        r"let\s+me\s+show\s+(?:you\s+)?(?:an?\s+)?(?:actual\s+)?/\w+\s+output",
        "Showing simulated output",
    ),
]

# Patterns that indicate actual EXECUTION
EXECUTION_PATTERNS = [
    r"TSK-\d{6}",  # TaskMaster ID
    r"Step\s+\d+:",  # Workflow step execution
    r"```(?:bash|python|shell)",  # Code execution blocks
    r"✅\s+(?:Complete|Done|Executed)",  # Completion markers with evidence
    r"Created?\s+(?:directory|file)\s+at",  # File operations
    r"Running\s+(?:step|phase|command)",  # Active execution
    r"Output:\s*\n```",  # Command output
    r"ML\s+Health:\s+\d+/\d+",  # ML health check (specific to cwo12)
]

# Commands with specific validation rules
COMMAND_SPECIFIC_RULES: dict[str, dict] = {
    "cwo12": {
        "required_patterns": [
            r"TSK-\d{6}",  # Must create/reference TSK
            r"Step\s+\d+",  # Must show step execution
        ],
        "forbidden_patterns": [
            r"conversation\s+summary",
            r"summary\s+of\s+(?:the\s+)?(?:work|session|chat)",
        ],
    },
    "exec": {
        "required_patterns": [
            r"(?:Implementing|Executing|Running)",
        ],
    },
    "truth": {
        "required_patterns": [
            r"TRUTH\s+AUDIT",
            r"(?:SUPPORTED|PARTIAL|INSUFFICIENT|FALSE)",
        ],
    },
}


def _get_terminal_id() -> str:
    """Best-effort terminal ID for session-scoped state."""
    try:
        from __lib.terminal_detection import detect_terminal_id

        return detect_terminal_id()
    except Exception:
        return os.environ.get("CLAUDE_SESSION_ID", "fallback_1")


def _get_scoped_state_file() -> Path:
    """Per-terminal state file path."""
    terminal_id = _get_terminal_id()
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", terminal_id)
    return hooks_dir / "session_data" / f"active_command_{safe_id}.json"


def _get_fallback_scoped_state_file() -> Path:
    """Fallback per-terminal state file path in temp directory."""
    terminal_id = _get_terminal_id()
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", terminal_id)
    return FALLBACK_SESSION_DATA_DIR / f"active_command_{safe_id}.json"


def _get_state_candidates() -> list[Path]:
    """State files to consult, scoped first then legacy fallback across primary/temp dirs."""
    return [
        _get_scoped_state_file(),
        _get_fallback_scoped_state_file(),
        LEGACY_SESSION_STATE_FILE,
        FALLBACK_SESSION_DATA_DIR / "active_command.json",
    ]


def load_command_state() -> dict | None:
    """Load active command state from session."""
    try:
        for state_file in _get_state_candidates():
            if not state_file.exists():
                continue

            if _session_cache:
                state = _session_cache.get(state_file, default={})
            else:
                state = json.loads(state_file.read_text(encoding="utf-8"))

            # Check if state is stale (supports both naive and timezone-aware timestamps).
            timestamp = datetime.fromisoformat(state.get("timestamp", "2000-01-01"))
            now = (
                datetime.now(timestamp.tzinfo)
                if timestamp.tzinfo is not None
                else datetime.now()
            )
            if now - timestamp > timedelta(seconds=MAX_STATE_AGE_SECONDS):
                continue

            return state
    except Exception:
        return None


def clear_command_state():
    """Clear command state after validation."""
    try:
        for state_file in _get_state_candidates():
            if state_file.exists():
                state_file.unlink()
    except Exception:
        pass


def read_last_assistant_response(transcript_path: str) -> str:
    """Read the most recent assistant response from transcript."""
    try:
        transcript = Path(transcript_path)
        if not transcript.exists():
            return ""

        content = transcript.read_text(encoding="utf-8").strip()
        if not content:
            return ""

        lines = content.split("\n")

        # Find last assistant message (JSONL format)
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("role") == "assistant":
                    msg_content = entry.get("content", "")
                    if isinstance(msg_content, list):
                        text_parts = [
                            block.get("text", "")
                            for block in msg_content
                            if block.get("type") == "text"
                        ]
                        return " ".join(text_parts)
                    return str(msg_content)
            except json.JSONDecodeError:
                continue

        return ""
    except Exception:
        return ""


def check_description_patterns(response: str) -> list[str]:
    """Check for patterns indicating description instead of execution."""
    violations = []
    response_lower = response.lower()

    for pattern, description in DESCRIPTION_PATTERNS:
        if re.search(pattern, response_lower, re.IGNORECASE):
            violations.append(description)

    return violations


def check_simulation_patterns(response: str) -> list[str]:
    """Check for patterns indicating simulation instead of actual Skill invocation."""
    violations = []

    for pattern, description in SIMULATION_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            violations.append(description)

    return violations


def check_execution_evidence(response: str) -> bool:
    """Check if response contains execution evidence."""
    for pattern in EXECUTION_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return True
    return False


def check_command_specific_rules(command_name: str, response: str) -> list[str]:
    """Check command-specific validation rules."""
    violations = []

    rules = COMMAND_SPECIFIC_RULES.get(command_name, {})

    # Check required patterns
    required = rules.get("required_patterns", [])
    for pattern in required:
        if not re.search(pattern, response, re.IGNORECASE):
            violations.append(f"Missing required pattern: {pattern}")

    # Check forbidden patterns
    forbidden = rules.get("forbidden_patterns", [])
    for pattern in forbidden:
        if re.search(pattern, response, re.IGNORECASE):
            violations.append(f"Contains forbidden pattern: {pattern}")

    return violations


def check_do_not_violations(do_not_rules: list[str], response: str) -> list[str]:
    """Check if response violates DO NOT rules."""
    violations = []
    response_lower = response.lower()

    for rule in do_not_rules:
        rule_lower = rule.lower()

        # Check for common violation patterns
        if "summarize" in rule_lower and re.search(
            r"(?:summary|summariz)", response_lower
        ):
            violations.append(f"Violated: {rule}")
        elif "describe" in rule_lower and re.search(
            r"(?:this command|let me explain)", response_lower
        ):
            violations.append(f"Violated: {rule}")
        elif "alternative" in rule_lower and re.search(
            r"(?:alternatively|instead.*could|you might)", response_lower
        ):
            violations.append(f"Violated: {rule}")

    return violations


def validate_command_execution(state: dict, response: str) -> dict | None:
    """
    Main validation function.

    Returns None if valid, or dict with decision/reason if violations found.
    """
    command_name = state.get("command_name", "unknown")
    do_not_rules = state.get("do_not_rules", [])

    # Collect all violations
    all_violations = []

    # Check 1: Description patterns (most serious)
    description_violations = check_description_patterns(response)
    if description_violations:
        all_violations.extend([f"[DESCRIPTION] {v}" for v in description_violations])

    # Check 2: DO NOT rule violations
    do_not_violations = check_do_not_violations(do_not_rules, response)
    if do_not_violations:
        all_violations.extend([f"[DO_NOT] {v}" for v in do_not_violations])

    # Check 3: Command-specific rules
    specific_violations = check_command_specific_rules(command_name, response)
    if specific_violations:
        all_violations.extend([f"[SPECIFIC] {v}" for v in specific_violations])

    # Check 4: Simulation patterns (python -c faking skill output)
    simulation_violations = check_simulation_patterns(response)
    if simulation_violations:
        all_violations.extend([f"[SIMULATION] {v}" for v in simulation_violations])

    # Check 5: Execution evidence (mitigating factor - but NOT for simulation)
    has_execution_evidence = check_execution_evidence(response)

    # Decision logic
    if not all_violations:
        return None  # All good

    # CRITICAL: Simulation violations always block, even with execution evidence
    # (because the evidence IS the simulation)
    if simulation_violations:
        return {
            "decision": "block",
            "reason": f"""[SIMULATION_DETECTED] /{command_name} was SIMULATED, not executed via Skill tool.

Violations detected:
{chr(10).join(['  • ' + v for v in all_violations[:5]])}

REQUIRED ACTION:
1. Use the Skill tool: Skill(skill="{command_name}")
2. Do NOT use Bash with python -c to fake output
3. The Skill tool reads and executes the actual SKILL.md file

This is a critical violation - simulation bypasses the skill's actual logic.""",
        }

    # If we have execution evidence AND only minor violations, warn but don't block
    if has_execution_evidence and len(all_violations) <= 1:
        return None  # Minor issue, has evidence, let it pass

    # Serious violations - block
    if description_violations:
        # Description without execution is the most serious
        violation_summary = "; ".join(all_violations[:3])
        return {
            "decision": "block",
            "reason": f"""[COMMAND_EXECUTION_VIOLATION] /{command_name} was DESCRIBED, not EXECUTED.

Violations detected:
{chr(10).join(['  • ' + v for v in all_violations[:5]])}

REQUIRED ACTION:
1. Delete the descriptive text you wrote
2. Actually EXECUTE the command directive
3. Show real output/artifacts from execution

The command directive was injected at the start of this prompt.
Read it again and EXECUTE it.""",
        }

    # Other violations
    if len(all_violations) >= 2:
        violation_summary = "; ".join(all_violations[:3])
        return {
            "decision": "block",
            "reason": f"[COMMAND_EXECUTION_VIOLATION] /{command_name}: {violation_summary}. Re-read the command directive and execute properly.",
        }

    return None


@hook_main
def main():
    if not ENABLED:
        sys.exit(0)

    input_data = json.load(sys.stdin)

    # Load command state
    state = load_command_state()

    if not state:
        # No active command - nothing to validate
        sys.exit(0)

    # Get response
    transcript_path = input_data.get("transcript_path", "")
    if not transcript_path:
        clear_command_state()
        sys.exit(0)

    response = read_last_assistant_response(transcript_path)
    if not response or len(response) < 50:
        clear_command_state()
        sys.exit(0)

    # Validate
    result = validate_command_execution(state, response)

    # Clear state after validation (one-shot)
    clear_command_state()

    if result:
        if result.get("decision") == "block":
            print(result["reason"], file=sys.stderr)
            sys.exit(2)
        else:
            print(json.dumps(result))

    sys.exit(0)

# === CLI TESTING ===


def run_tests():
    """Run built-in test cases."""

    test_cases = [
        {
            "name": "Description instead of execution",
            "command": "cwo12",
            "response": "This command provides a 15-step workflow for project execution. Let me explain how it works...",
            "should_block": True,
        },
        {
            "name": "Proper execution with TSK",
            "response": """Starting CWO12 Workflow...
TSK-251222-HealthChecks-1430
Step 1: Input Validation
✅ Complete: specify.md created""",
            "command": "cwo12",
            "should_block": False,
        },
        {
            "name": "Summary creation (violation)",
            "command": "cwo12",
            "response": "I've created a comprehensive summary of our conversation about health checks...",
            "should_block": True,
        },
        {
            "name": "Truth audit execution",
            "command": "truth",
            "response": """## TRUTH AUDIT v8.0
| Claim | Verdict | Score |
| "Tests pass" | ✅ SUPPORTED | 90 |""",
            "should_block": False,
        },
    ]

    print("Running command execution validator tests...\n")
    passed = 0
    failed = 0

    for case in test_cases:
        state = {
            "command_name": case["command"],
            "do_not_rules": ["Summarize this file", "Use alternative tools"],
            "timestamp": datetime.now().isoformat(),
        }

        result = validate_command_execution(state, case["response"])
        did_block = result is not None

        if did_block == case["should_block"]:
            print(f"✅ PASS: {case['name']}")
            passed += 1
        else:
            print(f"❌ FAIL: {case['name']}")
            print(f"   Expected block={case['should_block']}, got block={did_block}")
            if result:
                print(f"   Reason: {result.get('reason', 'N/A')[:100]}...")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
    else:
        main()
