"""PreToolUse gate: /ask allowed_first_tools enforcement.

Blocks routing to execution tools (Bash/Python/Write/etc.) as the first substantive
tool on /ask invocations, unless the routing decision was made via the discovery path.

Triggered when ALL of:
  1. Skill context is /ask (first token in user message is /ask)
  2. No routing decision has been emitted yet in this turn
  3. First substantive tool call is an execution tool

SKILL.md: allowed_first_tools: Grep, Glob, Read, Task, WebSearch
"""

from __future__ import annotations

import os
import re

# Tools that are always allowed as first discovery action
ALLOWED_FIRST_TOOLS = frozenset({
    "Grep",
    "Glob",
    "Read",
    "Task",
    "WebSearch",
})

# Execution tools that require a routing decision first
BLOCKED_EXECUTION_TOOLS = frozenset({
    "Bash",
    "Write",
    "Edit",
    "Call",
    "Agent",
})


def _is_ask_invocation(user_message: str) -> bool:
    """Return True if the user message is an /ask invocation."""
    return bool(re.match(r"^\s*/ask\b", user_message, re.IGNORECASE))


def _has_routing_decision(user_message: str) -> bool:
    """Return True if the message already contains a routing signal.

    Covers:
      - Explicit command mentions: /arch, /rca, /search, etc.
      - Direct delegation: "use /arch", "route to /search"
      - Help/default: /ask alone, /ask help, /ask "list commands"
    """
    msg = user_message.strip()

    # Bare /ask or /ask with only help/list flags → no routing decision needed
    if re.match(r"^\s*/ask\s*(help|list|available|commands|\?)?\s*$", msg, re.IGNORECASE):
        return True

    # Explicit command delegation
    if re.search(r"\b/(\w+)\b", msg):
        return True  # mentions another slash command

    return False


def _is_first_tool_blocked(tool_name: str) -> bool:
    """Return True if tool_name is a blocked execution tool."""
    return tool_name in BLOCKED_EXECUTION_TOOLS


def evaluate(
    user_message: str,
    tool_name: str,
    skill_context: str | None,
) -> tuple[bool, str]:
    """Evaluate the PreToolUse gate.

    Returns:
        (should_block, reason)
        should_block=True  → gate blocks the tool call
        should_block=False → gate passes silently
    """
    # Only activate for /ask skill context
    if not skill_context or not _is_ask_invocation(skill_context):
        return False, ""

    # Only check the first substantive tool call per /ask turn
    # We detect "first call" by checking if ROUTING_DECISION was already emitted
    # via a prior tool result in this same turn.
    routing_decided = os.environ.get("ASK_ROUTING_DECIDED", "").strip()
    if routing_decided == "1":
        # Routing decision was already made — pass through
        return False, ""

    # Not yet routed: check if this is a blocked execution tool
    if not _is_first_tool_blocked(tool_name):
        return False, ""

    # Help/list/default path always passes
    if re.match(
        r"^\s*/ask\s*(help|list|available|commands|\?)?\s*$",
        user_message.strip(),
        re.IGNORECASE,
    ):
        return False, ""

    return True, (
        "[ASK GATE] /ask requires a discovery action (Grep/Glob/Read/Task/WebSearch) "
        "as the first tool — not an execution tool. "
        "Gate the tool call and re-prompt: apply STEP 0–2 from SKILL.md first."
    )
