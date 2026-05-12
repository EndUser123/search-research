"""Extract factual scalars from tool output."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from .file_patterns import extract_facts_from_content


def extract_from_tool_output(
    tool_name: str,
    tool_input: str,
    tool_output: str,
    file_path: str = "",
) -> list[dict[str, Any]]:
    """Extract facts from Read/Bash/Grep output."""
    # Skip sensitive paths — no fact extraction from credentials, configs, secrets
    _SENSITIVE_PATTERNS = (
        r"\.env",
        r"\.aws[/\\]",
        r"credentials",
        r"secrets[/\\]",
        r"\.npmrc",
        r"\.pypirc",
        r"\.gitconfig",
        r"\.netrc",
        r"\.config/.\.env",
        r"settings\.local\.json",
        r"local\.json",
    )
    _SENSITIVE_RE = re.compile("|".join(_SENSITIVE_PATTERNS), re.IGNORECASE)

    if file_path and _SENSITIVE_RE.search(file_path):
        return []

    facts: list[dict[str, Any]] = []

    if tool_name in ("Read", "read_file"):
        facts.extend(extract_facts_from_content(tool_output, file_path or tool_input))

    elif tool_name in ("Bash", "bash", "bash_command"):
        facts.extend(_extract_from_bash_output(tool_output, tool_input))

    elif tool_name in ("Grep", "grep"):
        for line in tool_output.strip().split("\n"):
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    facts.append({
                        "entity": "grep_match",
                        "field": "content",
                        "value": parts[1].strip(),
                        "type": "grep",
                        "source_tool": "Grep",
                        "file": parts[0],
                    })

    # Add provenance to all facts
    for fact in facts:
        fact["provenance_type"] = "tool"
        fact["source_tool"] = tool_name
        fact["ts"] = _current_timestamp()

    return facts


def _extract_from_bash_output(output: str, input_cmd: str) -> list[dict[str, Any]]:
    """Extract structured facts from bash output."""
    facts: list[dict[str, Any]] = []

    # Try JSON first
    try:
        data = json.loads(output)
        if isinstance(data, dict):
            for k, v in data.items():
                facts.append({
                    "entity": "bash_result",
                    "field": k,
                    "value": str(v),
                    "type": "json",
                })
    except json.JSONDecodeError:
        pass

    # Key=value lines
    for line in output.split("\n"):
        if "=" in line or ":" in line:
            match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*[:=]\s*(.+)$", line)
            if match:
                key, val = match.groups()
                facts.append({
                    "entity": "bash_result",
                    "field": key,
                    "value": val.strip(),
                    "type": "assignment",
                })

    return facts


def _current_timestamp() -> str:
    """ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()
