"""Intent Extraction Hook for CKS Knowledge Capture

Detects and extracts work intent from user prompts to provide context
for CKS storage. This bridges the gap between "what changed" and "why changed".
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

# Import base classes directly (no registry dependency)
try:
    from UserPromptSubmit_modules.base import HookContext, HookResult
except ImportError:
    # Fallback for standalone testing
    HookContext = None
    HookResult = None

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import state path utilities for session-scoped state management (TASK-005)
try:
    from __lib.state_paths import get_session_state_path
except ImportError:
    # Fallback for development
    get_session_state_path = None

# Import terminal detection for getting session_id
try:
    from __lib.hook_base import get_terminal_id
except ImportError:
    # Fallback for development
    def get_terminal_id(data=None):
        return data.get("terminal_id", "") if data else ""

# Hooks directory reference
HOOKS_DIR = Path(__file__).resolve().parent.parent


def _get_session_id(context: HookContext) -> str:
    """Get session ID from hook context.

    Priority:
    1. session.id (from hook data)
    2. session_id (from hook data)
    3. sessionId (from hook data)
    4. CLAUDE_SESSION_ID (environment variable)
    5. "unknown" (fallback)

    Args:
        context: Hook context containing session information

    Returns:
        Session ID string
    """
    if not context:
        return os.environ.get("CLAUDE_SESSION_ID", "") or "unknown"

    data = context.data or {}
    session_obj = data.get("session")

    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    for key in ("session_id", "sessionId", "CLAUDE_SESSION_ID"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return os.environ.get("CLAUDE_SESSION_ID", "") or "unknown"


# Intent detection patterns
INTENT_PATTERNS = {
    "bugfix": [
        r"fix(?:ed)?\s+(?:the\s+)?(?:bug|issue|problem|error)",
        r"fix(?:ed)?\s+(?:the\s+)?[\w\s]+",  # General: "fix X" where X is anything
        r"debug(?:ging)?\s+\w+",
        r"resolve\s+\w+",
        r"correct(?:ing)?\s+(?:the\s+)?",
        r"repair\s+\w+",
    ],
    "feature": [
        r"(?:add|implement|create)\s+(?:new\s+)?(?:feature|functionality|capability)",
        r"build\s+(?:a\s+)?(?:new\s+)?",
        r"(?:develop|write)\s+(?:a\s+)?(?:feature|module|component)",
        r"add\s+support\s+for",
    ],
    "refactor": [
        r"refactor(?:ing)?\s+\w+",
        r"re(?:write|structure)\s+\w+",
        r"clean\s+up\s+\w+",
        r"improve\s+(?:the\s+)?(?:code|structure|design)",
        r"simplify\s+\w+",
        r"extract\s+(?:a\s+)?",
    ],
    "documentation": [
        r"(?:add|update|write)\s+(?:docs?|documentation|comment)",
        r"document\s+\w+",
        r"explain\s+(?:how|what|why)",
        r"readme|\.md(?:\s+file)?",
    ],
    "test": [
        r"(?:add|write|create)\s+(?:test|spec)",
        r"test\s+(?:for|that)",
        r"coverage\s+for",
        r"(?:unit|integration)\s+test",
    ],
    "optimization": [
        r"optimi[sz]e\s+(?:for)?",
        r"improve\s+(?:performance|speed|efficiency)",
        r"speed\s+up",
        r"(?:reduce|eliminate)\s+(?:overhead|latency|delay)",
    ],
}


def parse_work_intent(prompt: str) -> dict:
    """Extract work intent from user prompt.

    Returns:
        Dictionary with work_type, target, problem, and original prompt.
    """
    prompt_lower = prompt.lower()

    # Detect work type
    work_type = "unknown"
    for intent_type, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, prompt_lower):
                work_type = intent_type
                break
        if work_type != "unknown":
            break

    # Extract target (file, module, feature)
    target = extract_target(prompt)

    # Extract problem/description
    problem = extract_problem(prompt)

    return {
        "work_type": work_type,
        "target": target,
        "problem": problem,
        "user_prompt": prompt.strip(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def extract_target(prompt: str) -> str:
    """Extract the target of the work from prompt."""
    # Look for file paths, module names, feature names
    # File patterns: quotes, backticks, or common path patterns
    patterns = [
        r"['\"]([^'\"]+)['\"]",  # Quoted strings
        r"`([^`]+)`",            # Backtick strings
        r"\b([a-z_][a-z0-9_]*\.py)\b",  # Python files
        r"\b([a-z_][a-z0-9_]*\.ts)\b",  # TypeScript files
        r"\b(\w+(?:\.\w+)*)\s+(?:file|module|hook|class)",  # "X file/module"
    ]

    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(1)

    # Fallback: extract first noun phrase after common verbs
    # "fix the X in Y" → X in Y
    # "implement X for Y" → X for Y
    for pattern in [
        r"(?:add|implement|fix|create|update|write)\s+(?:the\s+)?(\w+(?:\s+\w+)*)",
        r"(?:for|in)\s+(\w+(?:\s+\w+)*)",
    ]:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(1)

    return "unspecified"


def extract_problem(prompt: str) -> str:
    """Extract the problem statement from prompt."""
    # Remove common verbs to get to the core problem
    problem = prompt

    # Strip leading verbs
    for verb in ["fix", "add", "implement", "create", "update", "write", "debug", "refactor", "optimize"]:
        problem = re.sub(rf"^{verb}(?:ed|ing|s)?\s+(?:the\s+)?", "", problem, flags=re.IGNORECASE)

    # Clean up
    problem = problem.strip()

    # Truncate if too long
    if len(problem) > 200:
        problem = problem[:197] + "..."

    return problem if problem else "Not specified"


def save_intent_state(intent: dict, context: HookContext | None = None) -> None:
    """Save intent to session state for PostToolUse access.

    Uses session-scoped state directory structure (TASK-005 migration):
    - New path: state/sessions/{session_id}/intent_state.json
    - Legacy path: session_data/intent_state.json (cleaned up after migration)

    Args:
        intent: Intent dictionary with work_type, target, problem, etc.
        context: Hook context for getting session_id
    """
    try:
        # Get session_id from context
        session_id = _get_session_id(context)

        # Try to use new session-scoped path if available
        if get_session_state_path and session_id:
            intent_state_file = get_session_state_path(session_id, "intent_state.json")
            intent_state_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Fallback to legacy flat structure
            intent_state_file = HOOKS_DIR / "session_data" / "intent_state.json"
            intent_state_file.parent.mkdir(parents=True, exist_ok=True)

        # Read existing state
        if intent_state_file.exists():
            with open(intent_state_file) as f:
                state = json.load(f)
        else:
            state = {}

        # Update with current intent
        state["current_intent"] = intent
        state["last_updated"] = datetime.now(UTC).isoformat()

        # Write back
        with open(intent_state_file, 'w') as f:
            json.dump(state, f, indent=2)

        # Clean up legacy file if using new path (TASK-005 migration)
        if get_session_state_path and session_id:
            legacy_file = HOOKS_DIR / "session_data" / "intent_state.json"
            try:
                legacy_file.unlink(missing_ok=True)
            except Exception:
                pass  # Best-effort cleanup

    except Exception as e:
        # Fail silently - don't break hook for state issues
        print(f"[Intent Extractor] State save failed: {e}", file=sys.stdout)


if HookContext is None:
    HookContext = type("HookContext", (object,), {"prompt": ""})
    HookResult = type("HookResult", (object,), {"empty": lambda: HookResult()})

def intent_extractor_hook(context: HookContext) -> HookResult:
    """Extract work intent from user prompt and store for CKS capture."""
    # Check if CKS integration is enabled
    if os.environ.get("CKS_INTEGRATION_ENABLED", "true").lower() not in ("1", "true", "yes"):
        return None

    prompt = context.prompt

    # Only extract from substantive prompts (> 15 chars)
    if len(prompt.strip()) < 15:
        return None

    # Skip if already processed (avoid re-extraction)
    if prompt.strip().startswith(("CKS entry stored", "Intent extracted", "##")):
        return None

    try:
        # Extract intent
        intent = parse_work_intent(prompt)

        # Only store if we detected something meaningful
        if intent.get("work_type") != "unknown" or intent.get("target") != "unspecified":
            # Save to session state for PostToolUse
            save_intent_state(intent, context)

            # Debug logging (if enabled)
            if os.environ.get("CKS_DEBUG", "0") == "1":
                print(f"[Intent Extractor] Detected: {intent['work_type']} - {intent.get('target', 'N/A')}", file=sys.stdout)

        return None

    except Exception as e:
        # Fail silently - don't break hook for parsing errors
        print(f"[Intent Extractor] Parse failed: {e}", file=sys.stdout)
        return None


# Register via decorator (imported by registry)
def register():
    """Registration function for manual import."""
    from . import registry
    registry.register_hook("intent_extractor", priority=3.0)(intent_extractor_hook)


# Auto-register if loaded directly
try:
    from . import registry
    registry.register_hook("intent_extractor", priority=3.0)(intent_extractor_hook)
except ImportError:
    # Will be registered manually by registry
    pass

