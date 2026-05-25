#!/usr/bin/env python3
"""
Agent Contract Validator
========================

PostToolUse hook that validates adversarial agent .md files after Write/Edit.

Ensures:
1. Specialist agents contain the "return ONLY file path" contract
   (prevents context overflow when 6+ agents run in parallel)
2. Agent frontmatter has required fields (name, description)
3. Agent name matches filename

This prevents regressions of the context overflow bug where agents returned
full JSON findings in their response text instead of just the file path.

Triggered by: Write/Edit on files matching .claude/agents/adversarial-*.md

Configuration:
    AGENT_CONTRACT_VALIDATOR_ENABLED (default: "true")
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from posttooluse.base import PostToolUseHook

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())

# The contract string that prevents context overflow
FILE_PATH_CONTRACT = "response text must contain ONLY the file path"

# Agent types that are specialists (produce findings, need the contract)
# vs orchestrator/critic (don't produce findings for aggregation)
SPECIALIST_PATTERN = re.compile(
    r"adversarial-(?!review|critic)\w+"
)

# Agents that are exempt from the contract (orchestrator, meta-analyzer)
EXEMPT_AGENTS = {"adversarial-review", "adversarial-critic"}


def _parse_frontmatter(content: str) -> dict[str, str]:
    """Extract YAML frontmatter key-value pairs."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def _get_agent_name(file_path: str) -> str | None:
    """Extract agent name from file path like .claude/agents/adversarial-logic.md"""
    path = Path(file_path)
    if path.suffix != ".md":
        return None
    return path.stem


def validate_agent_contract(file_path: str, content: str) -> dict:
    """Validate an adversarial agent file meets contract requirements.

    Returns dict with 'valid' bool and 'warnings' list.
    """
    warnings: list[str] = []
    agent_name = _get_agent_name(file_path)
    if not agent_name:
        return {"valid": True, "warnings": []}

    # 1. Check required frontmatter fields
    fm = _parse_frontmatter(content)
    if "name" not in fm:
        warnings.append(f"Agent {agent_name}: missing 'name' in frontmatter")
    elif fm["name"] != agent_name:
        warnings.append(
            f"Agent {agent_name}: frontmatter name '{fm['name']}' != filename '{agent_name}'"
        )
    if "description" not in fm:
        warnings.append(f"Agent {agent_name}: missing 'description' in frontmatter")

    # 2. Check file-path-only contract for specialist agents
    is_exempt = agent_name in EXEMPT_AGENTS
    if not is_exempt and SPECIALIST_PATTERN.match(agent_name):
        if FILE_PATH_CONTRACT not in content:
            warnings.append(
                f"Agent {agent_name}: MISSING 'return ONLY file path' contract. "
                f"Without this, the agent returns full JSON findings in response text, "
                f"causing context overflow when 6+ agents run in parallel."
            )

    # 3. Check that specialist agents define JSON output
    if not is_exempt and ".json" not in content:
        warnings.append(
            f"Agent {agent_name}: no .json output path defined. "
            f"Specialist agents must write findings to a JSON file."
        )

    return {"valid": len(warnings) == 0, "warnings": warnings}


class AgentContractValidator(PostToolUseHook):
    """PostToolUse hook to validate adversarial agent contract compliance.

    Only runs for Write/Edit operations on adversarial agent .md files.
    """

    env_var = "AGENT_CONTRACT_VALIDATOR_ENABLED"
    default_enabled = True

    # Only run for Write/Edit tools
    tool_matcher = {"Write", "Edit"}

    def process(self, tool_name: str, tool_input: dict, tool_response: dict) -> dict:
        """Validate agent contract after Write/Edit operations."""
        file_path = tool_input.get("file_path", "")
        if not file_path:
            return {"passed": True}

        # Only check adversarial agent .md files
        path = Path(file_path)
        if not (file_path.endswith(".md") and "adversarial-" in path.stem):
            return {"passed": True}

        # Read the file content
        try:
            if not path.exists():
                return {"passed": True}
            content = path.read_text(encoding="utf-8")
        except OSError:
            return {"passed": True}

        # Validate
        result = validate_agent_contract(file_path, content)

        if not result["valid"]:
            warning_text = "\n".join(f"  - {w}" for w in result["warnings"])
            return {
                "passed": False,
                "injection": (
                    f"\n\nAGENT CONTRACT VALIDATION FAILED:\n{warning_text}\n\n"
                    f"Fix the issues above before proceeding. "
                    f"To disable: export AGENT_CONTRACT_VALIDATOR_ENABLED=false\n"
                ),
            }

        return {"passed": True}


# Legacy main() for standalone execution (backward compatibility)
def main() -> None:
    """Legacy entry point for direct script execution."""
    import json
    import sys

    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    hook = AgentContractValidator()
    result = hook.run(data)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
