#!/usr/bin/env python3
from __future__ import annotations

"""
Drift Detector Hook - Agent Alignment Monitor
=============================================

Detects when Claude agents drift off-task across multiple terminals.
Uses LLM API (Groq Llama 3.1 8b) for fast "vibes check" on alignment.

Features:
- Monitors agent actions against original goal
- Uses Groq llama-3.1-8b-instant (~150ms latency)
- Writes status to %%TEMP%%\\cc_drift_<PID>.json
- Statusline reads this to show ⚠️ when agents drift

Architecture:
- PostToolUse hook: Runs after Edit/Write/Bash commands
- Uses llm_providers shared library directly (no zen_integration layer)
- File-per-process strategy: Each Claude instance writes its own status
- TTL-based cleanup: Stale files are ignored by statusline
"""

import asyncio
import json
import os
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

# Add lib path for llm_providers
lib_path = Path(__file__).resolve().parent.parent.parent / "__csf" / "src" / "lib"
sys.path.insert(0, str(lib_path))

# Configuration
PROVIDER_TYPE = "groq"  # Uses GroqProvider from llm_providers
MODEL = "llama-3.1-8b-instant"  # Fast inference via Groq
API_KEY_ENV = "GROQ_API_KEY"  # Environment variable for API key
TEMP_DIR = os.environ.get("TEMP", "/tmp")
CHECK_INTERVAL = 10  # Check every N tool uses
DRIFT_TTL_SECONDS = 120  # How long drift status persists


def get_parent_pid() -> int:
    """Get the parent PowerShell PID on Windows."""
    try:
        import psutil
        current = psutil.Process()
        parent = current.parent()
        if parent and "pwsh" in parent.name().lower():
            return parent.pid
        # Fallback to current PID if parent isn't PowerShell
        return os.getppid() if hasattr(os, 'getppid') else current.pid
    except ImportError:
        # Fallback without psutil - use environment variable
        return int(os.environ.get("CLAUDE_PARENT_PID", os.getpid()))


def get_goal_from_state() -> str | None:
    """
    Extract the current goal from goal anchor state.

    Returns the original goal if found, None otherwise.
    """
    try:
        state_file = Path(__file__).resolve().parent.parent / "hooks" / "state" / "goal_anchor.json"
        if state_file.exists():
            with open(state_file) as f:
                data = json.load(f)
                return data.get("current_goal")
    except Exception:
        pass

    # Try reading from session data
    try:
        session_file = Path(__file__).resolve().parent.parent / "current_session.json"
        if session_file.exists():
            with open(session_file) as f:
                data = json.load(f)
                return data.get("anchored_goal")
    except Exception:
        pass

    return None


async def check_alignment(goal: str, recent_actions: list[str]) -> dict:
    """
    Use LLM API to check if recent actions align with the goal.

    Args:
        goal: The original goal/anchor
        recent_actions: List of recent tool actions

    Returns:
        Dict with 'aligned' (bool), 'reason' (str), 'confidence' (float)
    """
    try:
        # Import llm_providers directly (no zen_integration layer)
        from llm_providers import ProviderConfig, ProviderFactory

        # Load API key from .env file
        env_file = Path(__file__).resolve().parent.parent.parent / "__csf" / ".env"
        api_key = os.environ.get(API_KEY_ENV)

        # If not in environment, try loading from .env
        if not api_key and env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                api_key = os.environ.get(API_KEY_ENV)
            except ImportError:
                # Fallback: parse .env manually
                with open(env_file) as f:
                    for line in f:
                        if line.startswith(f"{API_KEY_ENV}="):
                            api_key = line.split("=", 1)[1].strip()
                            break

        if not api_key:
            return {
                "aligned": True,
                "reason": f"{API_KEY_ENV} not found - skipping check",
                "confidence": 0.0
            }

        # Create provider config
        config = ProviderConfig(
            provider_type=PROVIDER_TYPE,
            api_key=api_key,
        )

        # Create provider instance
        provider = ProviderFactory.create_provider(PROVIDER_TYPE, config)

        # Build prompt for LLM
        actions_summary = "\n".join(f"- {action}" for action in recent_actions[-5:])
        prompt = f"""You are a drift detection system. Check if the following actions align with the original goal.

ORIGINAL GOAL:
{goal}

RECENT ACTIONS:
{actions_summary}

Respond in JSON format:
{{"aligned": true/false, "reason": "brief explanation", "confidence": 0.0-1.0}}

Be lenient - actions may explore subtasks. Only mark as drifted if clearly off-topic."""

        # Call LLM directly via llm_providers
        response = await provider.generate_response(
            prompt=prompt,
            model=MODEL,
            temperature=0.3,
            max_tokens=200
        )

        content = response.content

        # Parse JSON response
        try:
            # Extract JSON from markdown code block if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            return {
                "aligned": result.get("aligned", True),
                "reason": result.get("reason", "No reason provided"),
                "confidence": result.get("confidence", 0.5)
            }
        except json.JSONDecodeError:
            # Fallback: analyze text response
            content_lower = content.lower()
            aligned = not any(word in content_lower for word in ["not aligned", "drifted", "off task", "off-topic"])
            return {
                "aligned": aligned,
                "reason": content[:200],
                "confidence": 0.5
            }

    except Exception as e:
        # On any error, default to aligned (don't block work)
        return {
            "aligned": True,
            "reason": f"Check skipped: {str(e)[:100]}",
            "confidence": 0.0
        }


def write_drift_status(parent_pid: int, status: dict):
    """Write drift status to temp file for statusline to read."""
    drift_file = Path(TEMP_DIR) / f"cc_drift_{parent_pid}.json"

    try:
        with open(drift_file, "w") as f:
            json.dump({
                "status": status.get("aligned", True),
                "reason": status.get("reason", ""),
                "confidence": status.get("confidence", 0.0),
                "timestamp": datetime.now(UTC).isoformat(),
                "pid": parent_pid
            }, f)
    except Exception:
        pass  # Don't fail if we can't write status


def get_recent_actions(transcript: str) -> list[str]:
    """Extract recent tool actions from transcript."""
    actions = []
    lines = transcript.split("\n")

    for line in reversed(lines[-50:]):  # Last 50 lines
        line = line.strip()
        # Look for tool use patterns
        if line.startswith("I'll use") or line.startswith("Let me"):
            actions.append(line[:100])
        elif any(cmd in line for cmd in ["Bash(", "Edit(", "Write(", "Grep(", "Glob("]):
            actions.append(line[:100])

        if len(actions) >= 5:
            break

    return list(reversed(actions))


def get_transcript_excerpt() -> str:
    """Get recent conversation transcript."""
    try:
        # Try reading from Claude's context
        context_file = os.environ.get("CLAUDE_CONTEXT_FILE")
        if context_file and Path(context_file).exists():
            with open(context_file) as f:
                return f.read()[-5000:]  # Last 5000 chars
    except Exception:
        pass

    return ""


# Global counter for check interval
_check_counter = 0

# Internal action tracking - stores recent tool uses
_action_history: list[str] = []
_MAX_HISTORY = 20  # Keep last 20 actions


def record_action(tool_name: str, tool_input: dict) -> None:
    """Record a tool action in internal history."""
    action_desc = _format_action(tool_name, tool_input)
    _action_history.append(action_desc)
    # Keep only recent history
    if len(_action_history) > _MAX_HISTORY:
        _action_history.pop(0)


def _format_action(tool_name: str, tool_input: dict) -> str:
    """Format a tool action as a descriptive string."""
    if tool_name == "Edit":
        path = tool_input.get("file_path", tool_input.get("path", "unknown"))
        return f"Edit: {path}"
    elif tool_name == "Write":
        path = tool_input.get("file_path", tool_input.get("path", "unknown"))
        return f"Write: {path}"
    elif tool_name == "Bash":
        cmd = tool_input.get("command", tool_input.get("cmd", ""))
        # Truncate long commands
        if len(cmd) > 60:
            cmd = cmd[:57] + "..."
        return f"Bash: {cmd}"
    elif tool_name == "Read":
        path = tool_input.get("file_path", tool_input.get("path", "unknown"))
        return f"Read: {path}"
    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", "")
        return f"Grep: {pattern} in {path}"
    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        return f"Glob: {pattern}"
    elif tool_name == "Task":
        subagent = tool_input.get("subagent_type", "unknown")
        return f"Task: {subagent}"
    else:
        return f"{tool_name}: {str(tool_input)[:50]}"


def get_recent_actions_tracked() -> list[str]:
    """Get recent actions from internal tracking."""
    return list(_action_history)


def post_tool_use(tool_name: str, tool_input: dict, tool_response: dict) -> dict:
    """
    Main hook entry point - called after tool execution.

    Args:
        tool_name: Name of the tool that was just used
        tool_input: Input parameters passed to the tool
        tool_response: Output returned by the tool

    Returns:
        Dict with drift status (may be empty if check not performed)
    """
    global _check_counter

    # Record every action for tracking (all tool types)
    record_action(tool_name, tool_input)

    _check_counter += 1

    # Only check periodically
    if _check_counter % CHECK_INTERVAL != 0:
        return {}

    # Only check on significant tools
    if tool_name not in ("Edit", "Write", "Bash", "Task"):
        return {}

    try:
        # Get the current goal
        goal = get_goal_from_state()
        if not goal:
            return {}  # No goal = can't check drift

        # Get recent actions from internal tracking
        recent_actions = get_recent_actions_tracked()

        if not recent_actions:
            return {}  # Not enough context

        # Run async check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                check_alignment(goal, recent_actions)
            )
        finally:
            loop.close()

        # Write status file
        parent_pid = get_parent_pid()
        write_drift_status(parent_pid, result)

        # Only return user message if drifted
        if not result.get("aligned", True):
            return {
                "drift_detector": {
                    "drifted": True,
                    "reason": result.get("reason", ""),
                    "confidence": result.get("confidence", 0.0)
                },
                "user_message": f"\n⚠️ Drift detected: {result.get('reason', 'Actions may not align with goal')}"
            }

    except Exception as e:
        # Silently fail - don't break normal workflow
        debug_log = Path(__file__).resolve().parent / "logs" / "drift_detector.log"
        debug_log.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(debug_log, "a") as f:
                f.write(f"{datetime.now(UTC).isoformat()} - ERROR: {e}\n{traceback.format_exc()}\n")
        except Exception:
            pass

    return {}


# Standalone test interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Drift Detector Hook")
    parser.add_argument("--test", action="store_true", help="Run test check")
    parser.add_argument("--goal", help="Test goal")
    parser.add_argument("--actions", nargs="+", help="Test actions")

    args = parser.parse_args()

    if args.test:
        print("=== Testing Drift Detector Hook ===\n")

        test_goal = args.goal or "Implement a user authentication system with JWT tokens"
        test_actions = args.actions or [
            "Bash: npm install express",
            "Edit: src/auth/jwt.js - added token validation",
            "Write: src/middleware/auth.js - created auth middleware",
            "Read: package.json - checking dependencies"
        ]

        print(f"Goal: {test_goal}")
        print(f"Actions: {len(test_actions)}")
        for action in test_actions:
            print(f"  - {action}")
        print()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                check_alignment(test_goal, test_actions)
            )
            print(f"Aligned: {result.get('aligned')}")
            print(f"Reason: {result.get('reason')}")
            print(f"Confidence: {result.get('confidence')}")
        finally:
            loop.close()
