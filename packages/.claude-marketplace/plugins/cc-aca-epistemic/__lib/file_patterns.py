"""Structured file detection and fact extraction from file content."""

from __future__ import annotations

import json
import os
import re
from typing import Any


STRUCTURED_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini"}
STRUCTURED_NAME_PATTERNS = [
    "routes", "probe", "config", "provider", "quota", "pricing", "capabilities",
    "manifest", "spec", "schema", "settings", "model", "agent",
]


def is_structured_file(path: str) -> bool:
    """Check if file is a structured data file worth guarding."""
    _, ext = os.path.splitext(path)

    if ext.lower() in STRUCTURED_EXTENSIONS:
        return True

    basename = os.path.basename(path).lower()
    for pattern in STRUCTURED_NAME_PATTERNS:
        if pattern in basename:
            return True

    return False


def extract_facts_from_content(content: str, file_path: str) -> list[dict[str, Any]]:
    """Extract factual scalars from structured content."""
    facts: list[dict[str, Any]] = []

    # Try JSON first
    try:
        data = json.loads(content)
        facts.extend(_extract_from_json(data, file_path))
        return facts
    except json.JSONDecodeError:
        pass

    # Fallback: key=value / key: value patterns
    facts.extend(_extract_from_lines(content, file_path))
    return facts


def _extract_from_json(obj: Any, file_path: str, entity_context: str = "") -> list[dict[str, Any]]:
    """Recursively extract facts from JSON structure.

    entity_context tracks the immediate parent dict key (the entity name),
    not the full path. This ensures entities are "MiniMax-M2.7" not "providers.MiniMax-M2.7".
    """
    facts: list[dict[str, Any]] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if _is_factual_value(value):
                facts.append({
                    "entity": entity_context or "root",
                    "field": key,
                    "value": str(value),
                    "type": type(value).__name__,
                    "file": file_path,
                })
            elif isinstance(value, dict):
                # Key is the entity name for nested values
                facts.extend(_extract_from_json(value, file_path, entity_context=key))
            elif isinstance(value, list):
                facts.extend(_extract_from_json(value, file_path, entity_context))

    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            if isinstance(item, dict):
                facts.extend(_extract_from_json(item, file_path, entity_context))
            elif _is_factual_value(item):
                facts.append({
                    "entity": entity_context or f"list[{idx}]",
                    "field": "value",
                    "value": str(item),
                    "type": type(item).__name__,
                    "file": file_path,
                })

    return facts


def _extract_from_lines(content: str, file_path: str) -> list[dict[str, Any]]:
    """Extract key=value or key: value patterns from text."""
    facts: list[dict[str, Any]] = []
    pattern = r"""(\w+)\s*[:=]\s*(['"]?)([^'"\n]+)\2"""

    for match in re.finditer(pattern, content):
        key, _, value = match.groups()
        value = value.strip()
        if _is_factual_value_str(value):
            facts.append({
                "entity": "config",
                "field": key,
                "value": value,
                "type": "string",
                "file": file_path,
            })

    return facts


def _is_factual_value(value: Any) -> bool:
    """Check if a value is factual (numeric, quota, version, etc.)."""
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, str):
        return _is_factual_value_str(value)
    return False


def _is_factual_value_str(value: str) -> bool:
    """Check if string is a factual literal."""
    value = value.strip()

    if value.lower() in ("none", "null", "unknown", "todo", "n/a", ""):
        return False

    # Quota patterns
    if re.match(r"^\d+(/\d+[hms]|[\s\w/]+)?$", value):
        return True

    # Version patterns
    if re.match(r"^v?\d+\.\d+", value):
        return True

    # Short identifiers (model/provider IDs)
    if re.match(r"^[A-Z][a-zA-Z0-9\-]*$", value) and 2 <= len(value) <= 50:
        return True

    # UUID or hash strings
    if re.match(r"^[a-f0-9]{8,}$", value):
        return True

    return False
