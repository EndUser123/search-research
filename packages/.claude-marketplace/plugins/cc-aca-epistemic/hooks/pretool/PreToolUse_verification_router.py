"""
PreToolUse Verification Router

Unified router for PreToolUse verification gates. Consolidates
verification modules with priority-based execution and in-process
module loading for performance.

Architecture:
- Module caching: _MODULE_CACHE prevents repeated imports
- Priority-based execution: HOOK_PRIORITY dict orders execution
- Early-exit optimization: Fast pre-check for non-investigation queries
- Graceful degradation: Module failures logged but don't crash router
"""
from __future__ import annotations



# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import importlib.util
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

# Configure logging (no stderr output)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# =============================================================================
# Configuration
# =============================================================================

# Module cache for loaded verification modules
_MODULE_CACHE: dict[str, Any] = {}

# Priority dict: lower number = earlier execution
HOOK_PRIORITY: dict[str, float] = {
    "investigation_verification": 4.5,
}

# Bypass flag for verification
BYPASS_FLAG = "--skip-investigation-verify"

# Router debug mode (set via environment variable)
ROUTER_DEBUG = os.environ.get("VERIFICATION_ROUTER_DEBUG", "false").lower() == "true"

# Rate limit state file path
RATE_LIMIT_STATE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "state",
    "verification_router_rate_limit.json"
)

# =============================================================================
# Module Loading
# =============================================================================

def load_verification_modules(module_name: str) -> Any | None:
    """
    Load a verification module with caching.

    Uses importlib.util for dynamic module loading with sys.modules
    caching to avoid repeated imports.

    Args:
        module_name: Name of the module to load (without .py extension)

    Returns:
        Loaded module object or None if loading fails
    """
    # Check cache first
    if module_name in _MODULE_CACHE:
        if ROUTER_DEBUG:
            print(f"[ROUTER] Cache hit for module: {module_name}", file=sys.stdout)
        return _MODULE_CACHE[module_name]

    # Construct module path
    hooks_dir = Path(__file__).resolve().parent
    module_dir = hooks_dir / "PreToolUse_verification_modules"
    module_path = module_dir / f"{module_name}.py"

    if not module_path.exists():
        logger.warning(f"Module not found: {module_path}")
        return None

    try:
        # Load module using importlib.util
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            logger.error(f"Failed to load spec for module: {module_name}")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Cache the module
        _MODULE_CACHE[module_name] = module

        if ROUTER_DEBUG:
            print(f"[ROUTER] Loaded module: {module_name}", file=sys.stdout)

        return module

    except Exception as e:
        logger.error(f"Failed to load module {module_name}: {e}")
        return None


def _run_single_module(
    module_name: str,
    data: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Run a single verification module.

    Args:
        module_name: Name of the module to run
        data: Hook input data

    Returns:
        Module result dict or None
    """
    module = load_verification_modules(module_name)
    if module is None:
        logger.warning(f"Module {module_name} not available, skipping")
        return None

    try:
        if hasattr(module, 'run'):
            result = module.run(data)
            if ROUTER_DEBUG:
                print(f"[ROUTER] Module {module_name} returned: {result}", file=sys.stdout)
            return result
        else:
            logger.warning(f"Module {module_name} missing run() function")
            return None

    except Exception as e:
        logger.error(f"Module {module_name} failed: {e}")
        # Return None to allow other modules to continue (graceful degradation)
        return None


# =============================================================================
# Priority-Based Execution
# =============================================================================

def run_verification_modules(data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Run all verification modules in priority order.

    Modules are executed in order of priority (lower number = earlier).
    Early-exit optimization skips verification for non-investigation queries.

    Args:
        data: Hook input data with userPrompt field

    Returns:
        Dict with additionalContext to inject, or None if no verification needed
    """
    # Early-exit optimization: check for investigation keywords
    if not _needs_verification(data):
        if ROUTER_DEBUG:
            print("[ROUTER] Early exit: non-investigation query", file=sys.stdout)
        return None

    # Sanitize input
    data = sanitize_input(data)

    # Rate limiting check
    if _check_rate_limit(data):
        if ROUTER_DEBUG:
            print("[ROUTER] Rate limited, skipping verification", file=sys.stdout)
        return None

    # Sort modules by priority
    sorted_modules = sorted(
        HOOK_PRIORITY.items(),
        key=lambda x: (x[1], x[0])  # (priority, name) for stable ordering
    )

    # Execute each module in priority order
    for module_name, priority in sorted_modules:
        if ROUTER_DEBUG:
            print(f"[ROUTER] Running module: {module_name} (priority {priority})", file=sys.stdout)

        result = _run_single_module(module_name, data)

        # If module returns a result, use it
        if result and isinstance(result, dict):
            if ROUTER_DEBUG:
                print(f"[ROUTER] Module {module_name} provided context", file=sys.stdout)
            return result

    # No module provided context
    return None


def _needs_verification(data: dict[str, Any]) -> bool:
    """
    Check if the query needs verification (early-exit optimization).

    Args:
        data: Hook input data with userPrompt field

    Returns:
        True if verification is needed, False otherwise
    """
    # Import here to avoid circular dependency
    from PreToolUse_verification_modules.investigation_verification import (
        has_investigation_keywords,
    )

    user_prompt = data.get("userPrompt", "")

    # Check for bypass flag first
    if BYPASS_FLAG in user_prompt:
        return False

    # Check for investigation keywords
    return has_investigation_keywords(data)


# =============================================================================
# Input Sanitization
# =============================================================================

def sanitize_input(data: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize input data to handle non-string values.

    Args:
        data: Hook input data

    Returns:
        Sanitized data with string userPrompt
    """
    if "userPrompt" in data:
        user_prompt = data["userPrompt"]
        if not isinstance(user_prompt, str):
            # Convert non-string to string (e.g., dict, list)
            data["userPrompt"] = str(user_prompt)
            if ROUTER_DEBUG:
                print(f"[ROUTER] Sanitized non-string userPrompt: {type(user_prompt)}", file=sys.stdout)

    return data


def normalize_input_fields(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize camelCase field names to snake_case.

    Claude Code may send either camelCase or snake_case field names.
    This function normalizes to snake_case for consistency.

    Args:
        data: Hook input data

    Returns:
        Data with normalized field names
    """
    normalized = {}

    for key, value in data.items():
        # Convert camelCase to snake_case
        snake_key = re.sub('([A-Z])', r'_\1', key).lower().lstrip('_')

        # Keep original if conversion didn't change anything
        if snake_key == '':
            snake_key = key

        normalized[snake_key] = value

    return normalized


# =============================================================================
# Rate Limiting
# =============================================================================

def _check_rate_limit(data: dict[str, Any]) -> bool:
    """
    Check if verification should be rate-limited.

    Simple implementation: limit verification to once per minute per session.

    Args:
        data: Hook input data

    Returns:
        True if rate limited (should skip), False otherwise
    """
    # Get session ID
    session_id = data.get("sessionId", "default")

    # Create rate limit state directory
    state_dir = Path(RATE_LIMIT_STATE).parent
    state_dir.mkdir(parents=True, exist_ok=True)

    # Simple rate limit: check last verification time
    rate_limit_file = state_dir / f"rate_limit_{session_id}.json"

    try:
        if rate_limit_file.exists():
            with open(rate_limit_file) as f:
                # TODO: Implement actual rate limiting logic
                # For now, just return False (no rate limiting)
                _ = json.load(f)  # Read but don't use (placeholder for future implementation)
                return False

    except (OSError, json.JSONDecodeError):
        pass

    return False


# =============================================================================
# JSON stdin/stdout Interface
# =============================================================================

def main() -> None:
    """
    Main entry point for JSON stdin/stdout interface.

    Reads JSON input from stdin, processes it through the verification
    router, and writes JSON output to stdout.

    Input format:
    {
        "tool_name": "Bash",
        "tool_input": {...},
        "userPrompt": "investigate error",
        ...
    }

    Output format:
    {
        "continue": true,
        "reason": "..."
    }
    """
    try:
        # Read JSON from stdin
        input_text = sys.stdin.read()
        data = json.loads(input_text)

        # Normalize field names (camelCase to snake_case)
        data = normalize_input_fields(data)

        # Run verification modules
        result = run_verification_modules(data)

        # Build output
        output = {
            "continue": True,
            "reason": "Verification complete"
        }

        # If verification module provided additional context, include it
        if result and "additionalContext" in result:
            output["additionalContext"] = result["additionalContext"]

        # Write output to stdout
        print(json.dumps(output))

    except json.JSONDecodeError as e:
        # Malformed JSON - allow continuation (fail open)
        output = {
            "continue": True,
            "reason": f"Invalid JSON: {e}"
        }
        print(json.dumps(output))

    except Exception as e:
        # Unexpected error - log but allow continuation (fail open)
        logger.error(f"Router error: {e}")
        output = {
            "continue": True,
            "reason": f"Router error: {e}"
        }
        print(json.dumps(output))


if __name__ == "__main__":
    main()
