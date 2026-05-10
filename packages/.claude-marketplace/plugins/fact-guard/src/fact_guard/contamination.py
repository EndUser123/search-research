"""Adjacent-entry contamination detector.

Detects when a new value for entity B matches an existing value for entity A
in the same data structure, without entity-specific evidence.
Uses difflib.SequenceMatcher for near-exact match detection.
"""

from __future__ import annotations

import difflib
import json
from typing import Any


def detect_contamination(
    proposed_facts: list[dict[str, Any]],
    existing_content: str,
    observed_facts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect if proposed facts are copied from neighboring entries without provenance.

    Returns list of contamination hits:
    [{
        'entity_b': 'Mi-Devstral',
        'field': 'quota',
        'value': '4500/5h',
        'matched_entity_a': 'MiniMax-M2.7',
        'similarity': 1.0,
        'evidence_missing': True
    }]
    """
    contamination_hits: list[dict[str, Any]] = []

    existing_facts = _parse_existing_structure(existing_content)

    for proposed in proposed_facts:
        entity_b = proposed.get("entity", "")
        field = proposed.get("field", "")
        value_b = proposed.get("value", "")

        if _is_placeholder(value_b):
            continue

        if _check_provenance(proposed, observed_facts):
            continue

        for existing in existing_facts:
            entity_a = existing.get("entity", "")
            value_a = existing.get("value", "")

            if entity_a == entity_b:
                continue

            val_b_norm = _normalize_value(value_b)
            val_a_norm = _normalize_value(value_a)

            similarity = difflib.SequenceMatcher(None, val_b_norm, val_a_norm).ratio()
            if similarity > 0.85:
                contamination_hits.append({
                    "entity_b": entity_b,
                    "field": field,
                    "value": value_b,
                    "matched_entity_a": entity_a,
                    "value_a": value_a,
                    "similarity": round(similarity, 2),
                    "evidence_missing": True,
                })
                break

    return contamination_hits


def _parse_existing_structure(content: str) -> list[dict[str, Any]]:
    """Parse existing file structure to extract all literal values."""
    facts: list[dict[str, Any]] = []

    try:
        data = json.loads(content)
        facts.extend(_extract_all_facts_recursive(data))
    except json.JSONDecodeError:
        pass

    return facts


def _extract_all_facts_recursive(obj: Any, parent_key: str = "") -> list[dict[str, Any]]:
    """Recursively extract all facts from nested structure."""
    facts: list[dict[str, Any]] = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, str) and not _is_placeholder(value):
                facts.append({
                    "entity": parent_key or "root",
                    "field": key,
                    "value": value,
                })
            elif isinstance(value, (dict, list)):
                facts.extend(_extract_all_facts_recursive(value, full_key))

    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            if isinstance(item, dict):
                facts.extend(_extract_all_facts_recursive(item, f"{parent_key}[{idx}]"))
            elif isinstance(item, str) and not _is_placeholder(item):
                facts.append({
                    "entity": parent_key or f"list[{idx}]",
                    "field": "value",
                    "value": item,
                })

    return facts


def _normalize_value(value: str) -> str:
    """Normalize value for comparison (case-insensitive, whitespace trimmed)."""
    return value.strip().lower()


def _is_placeholder(value: str) -> bool:
    """Check if value is a placeholder."""
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    placeholders = {"none", "null", "unknown", "todo", "n/a", ""}
    return normalized in placeholders


def _check_provenance(proposed: dict[str, Any], observed_facts: list[dict[str, Any]]) -> bool:
    """Check if proposed fact has matching provenance in observed facts."""
    entity = proposed.get("entity", "")
    field = proposed.get("field", "")
    value = proposed.get("value", "")

    for observed in observed_facts:
        if (
            observed.get("entity") == entity
            and observed.get("field") == field
            and observed.get("value") == value
        ):
            return True

    return False
