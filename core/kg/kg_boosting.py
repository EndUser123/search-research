"""
KG (Knowledge Graph) Result Boosting Module.

This module provides functionality to boost search results based on entity
affinity from KG data. It includes:
- Loading entity-to-conversation mappings from KG data
- Loading entity-to-type mappings for type filtering
- Calculating affinity boost scores based on Jaccard similarity
- Applying boosting to search results with entity type filtering
- Feature flag control via SEARCH_ENABLE_KG_BOOSTING environment variable
- Entity type filtering via SEARCH_KG_BOOST_ENTITY_TYPES environment variable
"""

import json
import os
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

# Default entity types to boost (high-value entities)
# Excludes low-value types like FILE_PATH, URL, FILE_EXTENSION
DEFAULT_ALLOWED_ENTITY_TYPES = {"TECHNOLOGY", "COMMAND", "CSF"}


def load_kg_affinity_data(kg_data_path: str) -> dict[str, set[str]]:
    """
    Load KG affinity data and build entity-to-conversations mapping.

    Args:
        kg_data_path: Path to the KG data directory containing
                     conversation_entities.json

    Returns:
        Dictionary mapping entity names to sets of conversation IDs.
        Returns empty dict if path doesn't exist or file not found.

    Raises:
        FileNotFoundError: If the kg_data_path directory doesn't exist
    """
    kg_path = Path(kg_data_path)

    if not kg_path.exists():
        raise FileNotFoundError(f"KG data path not found: {kg_data_path}")

    entity_to_convs: dict[str, set[str]] = defaultdict(set)

    # Load conversation_entities.json to build the mapping
    conv_entities_path = kg_path / "conversation_entities.json"

    if conv_entities_path.exists():
        with open(conv_entities_path, encoding="utf-8") as f:
            conversation_entities = json.load(f)

        for conv_id, entities in conversation_entities.items():
            for entity_name in entities:
                entity_to_convs[entity_name].add(conv_id)

    return dict(entity_to_convs)


def load_kg_entity_type_data(kg_data_path: str) -> dict[str, str]:
    """
    Load KG entity type data.

    Args:
        kg_data_path: Path to the KG data directory containing entities.json

    Returns:
        Dictionary mapping entity names to their entity types.
        Returns empty dict if path doesn't exist or file not found.

    Raises:
        FileNotFoundError: If the kg_data_path directory doesn't exist
    """
    kg_path = Path(kg_data_path)

    if not kg_path.exists():
        raise FileNotFoundError(f"KG data path not found: {kg_data_path}")

    entity_to_types: dict[str, str] = {}

    # Load entities.json to build the type mapping
    entities_path = kg_path / "entities.json"

    if entities_path.exists():
        with open(entities_path, encoding="utf-8") as f:
            entities = json.load(f)

        for entity in entities:
            entity_text = entity.get("text", "")
            entity_type = entity.get("type", "")
            if entity_text:
                entity_to_types[entity_text] = entity_type

    return entity_to_types


def get_allowed_entity_types() -> set[str]:
    """
    Get the set of allowed entity types for boosting.

    Reads from SEARCH_KG_BOOST_ENTITY_TYPES environment variable.
    If not set, returns DEFAULT_ALLOWED_ENTITY_TYPES.

    Returns:
        Set of entity type names that should be boosted.
    """
    env_value = os.environ.get("SEARCH_KG_BOOST_ENTITY_TYPES", "")

    if not env_value:
        return DEFAULT_ALLOWED_ENTITY_TYPES.copy()

    # Parse comma-separated list
    allowed = {t.strip().upper() for t in env_value.split(",") if t.strip()}
    return allowed


def calculate_affinity_boost(
    result_entities: list[str], query_entities: list[str], entity_to_convs: dict[str, set[str]]
) -> float:
    """
    Calculate affinity boost score based on Jaccard similarity.

    The affinity score measures how closely related result entities are to
    query entities based on their co-occurrence in conversations.

    Formula: Jaccard similarity = intersection / union
    Where:
    - intersection = conversations shared by result and query entities
    - union = all unique conversations containing either entity

    Args:
        result_entities: List of entity names in the search result
        query_entities: List of entity names extracted from the query
        entity_to_convs: Mapping of entity names to conversation IDs

    Returns:
        Affinity score between 0 and 1.
        Returns 0 if either list is empty or no shared conversations.
    """
    # Return 0 if either list is empty
    if not result_entities or not query_entities:
        return 0.0

    # Normalize entity names to lowercase for case-insensitive matching
    entity_to_convs_lower = {k.lower(): v for k, v in entity_to_convs.items()}

    # Collect all conversations for result entities
    result_conv_ids: set[str] = set()
    for entity in result_entities:
        entity_lower = entity.lower()
        if entity_lower in entity_to_convs_lower:
            result_conv_ids.update(entity_to_convs_lower[entity_lower])

    # Collect all conversations for query entities
    query_conv_ids: set[str] = set()
    for entity in query_entities:
        entity_lower = entity.lower()
        if entity_lower in entity_to_convs_lower:
            query_conv_ids.update(entity_to_convs_lower[entity_lower])

    # Return 0 if no conversations for either
    if not result_conv_ids or not query_conv_ids:
        return 0.0

    # Calculate Jaccard similarity
    intersection = result_conv_ids & query_conv_ids
    union = result_conv_ids | query_conv_ids

    if not union:
        return 0.0

    return len(intersection) / len(union)


@lru_cache(maxsize=1024)
def _build_entity_pattern(entity_lower: str) -> re.Pattern[str]:
    """
    Build a cached regex pattern for entity matching with word boundaries.

    Args:
        entity_lower: Lowercase entity name to build pattern for.

    Returns:
        Compiled regex pattern with appropriate word boundaries.
    """
    escaped = re.escape(entity_lower)
    if " " in entity_lower:
        # Multi-word entity: use lookaround to match exact phrase
        # (?<!\w) = not preceded by word char
        # (?=\s|$) = followed by space or end
        return re.compile(r"(?<!\w)" + escaped + r"(?=\s|$)")
    # Single word: use word boundaries
    return re.compile(r"\b" + escaped + r"\b")


def extract_entities_from_query(query: str, known_entities: set[str]) -> list[str]:
    """
    Extract entities from query string using word boundary matching.
    """
    if not query:
        return []

    query_lower = query.lower()
    found_entities = []

    # Sort entities by length (descending) to match longer first
    sorted_entities = sorted(known_entities, key=len, reverse=True)

    for entity in sorted_entities:
        pattern = _build_entity_pattern(entity.lower())
        if pattern.search(query_lower):
            found_entities.append(entity)

    return found_entities


def filter_entities_by_type(
    entities: list[str], entity_to_types: dict[str, str], allowed_types: set[str]
) -> list[str]:
    """
    Filter entities to only those with allowed types.

    Args:
        entities: List of entity names to filter
        entity_to_types: Mapping of entity names to their types
        allowed_types: Set of entity type names that are allowed

    Returns:
        List of entity names that have allowed types.
        Returns all entities if entity_to_types is empty or allowed_types is empty.
    """
    # If no type mapping or no filtering, return all entities
    if not entity_to_types or not allowed_types:
        return entities

    # Normalize for case-insensitive matching
    entity_to_types_lower = {k.lower(): v.upper() for k, v in entity_to_types.items()}
    allowed_types_upper = {t.upper() for t in allowed_types}

    filtered = []
    for entity in entities:
        entity_lower = entity.lower()
        if entity_lower in entity_to_types_lower:
            entity_type = entity_to_types_lower[entity_lower]
            if entity_type in allowed_types_upper:
                filtered.append(entity)

    return filtered


def get_boost_alpha() -> float:
    """
    Get the alpha parameter for non-linear boosting.

    Reads from SEARCH_KG_BOOST_ALPHA environment variable.
    If not set, returns 1.0 (linear boosting).

    Returns:
        Alpha value for non-linear scaling. Higher values reduce
        impact of low affinity scores.

        - alpha=1: Linear (new_score = original * (1 + affinity))
        - alpha=2: Squared (new_score = original * (1 + affinity^2))
    """
    env_value = os.environ.get("SEARCH_KG_BOOST_ALPHA", "1")
    try:
        return float(env_value)
    except ValueError:
        return 1.0


def apply_kg_boosting(
    results: list[dict[str, Any]],
    query: str,
    entity_to_convs: dict[str, set[str]],
    *,
    entity_to_types: dict[str, str] | None = None,
    boosting_enabled: bool | None = None,
    debug_mode: bool = False,
) -> list[dict[str, Any]]:
    """
    Apply KG-based boosting to search results.

    For each result:
    1. Extract entities from result metadata
    2. Extract entities from the query
    3. Filter entities by type if entity_to_types provided
    4. Calculate affinity boost between result entities and query entities
    5. Apply formula: new_score = original_score * (1 + affinity_score^alpha)

    The boosting is controlled by the SEARCH_ENABLE_KG_BOOSTING environment
    variable. When set to "1", boosting is applied. Otherwise, results
    are returned unchanged.

    Entity type filtering is controlled by the SEARCH_KG_BOOST_ENTITY_TYPES
    environment variable. If set, only entities of those types are boosted.

    Non-linear scaling is controlled by SEARCH_KG_BOOST_ALPHA (default: 1.0).
    Higher alpha values reduce the impact of low affinity scores.

    Args:
        results: List of search result dictionaries. Each result should have
                'score' and optionally 'entities' in metadata or at top level.
        query: The search query string
        entity_to_convs: Mapping of entity names to conversation IDs
        entity_to_types: Optional mapping of entity names to their types.
                        If provided, entities are filtered by allowed types.
        boosting_enabled: Override for feature flag. None uses env var.
        debug_mode: If True, adds enhanced debug metadata including query_entities,
                    query_entities_filtered, result_entities, allowed_types, and alpha value.

    Returns:
        List of boosted results with added metadata:
        - original_score: The score before boosting
        - boost_factor: The affinity score used for boosting (raised to alpha power)
        - kg_debug: Enhanced debug metadata if debug_mode is True
    """
    # Check feature flag (allow override via parameter)
    if boosting_enabled is None:
        boosting_enabled = os.environ.get("SEARCH_ENABLE_KG_BOOSTING", "0") == "1"

    # Get known entities for extraction
    known_entities = set(entity_to_convs.keys())

    # Extract query entities
    query_entities = extract_entities_from_query(query, known_entities)

    # Filter query entities by type if type mapping provided
    allowed_types = None
    if entity_to_types:
        allowed_types = get_allowed_entity_types()
        query_entities_filtered = filter_entities_by_type(
            query_entities, entity_to_types, allowed_types
        )
    else:
        query_entities_filtered = query_entities

    boosted_results = []

    for result in results:
        # Create a copy to avoid modifying original
        boosted_result = result.copy()

        original_score = result.get("score", 0.0)

        # Extract entities from result
        # First check if entities are at result level
        if "entities" in result:
            result_entities = result["entities"]
        # Then check metadata
        elif "metadata" in result and isinstance(result["metadata"], dict):
            result_entities = result["metadata"].get("entities", [])
        else:
            result_entities = []

        # Ensure entities is a list
        if not isinstance(result_entities, list):
            result_entities = []

        # Filter result entities by type if type mapping provided
        # Note: allowed_types was computed before the loop (line 342)
        if entity_to_types and result_entities and allowed_types:
            result_entities = filter_entities_by_type(
                result_entities, entity_to_types, allowed_types
            )

        # Calculate affinity boost
        if boosting_enabled and query_entities_filtered and result_entities:
            affinity_score = calculate_affinity_boost(
                result_entities, query_entities_filtered, entity_to_convs
            )
        else:
            affinity_score = 0.0

        # Get alpha for non-linear scaling
        alpha = get_boost_alpha()

        # Apply boosting formula: new_score = original_score * (1 + affinity^alpha)
        # Store the raw affinity score before applying alpha
        raw_affinity = affinity_score
        scaled_affinity = affinity_score**alpha if alpha != 1 else affinity_score

        new_score = original_score * (1 + scaled_affinity)

        # Update result (store raw affinity for transparency)
        boosted_result["score"] = new_score
        boosted_result["original_score"] = original_score
        boosted_result["boost_factor"] = raw_affinity

        # Add debug metadata if debug mode is enabled
        if debug_mode:
            boosted_result["kg_debug"] = {
                "query_entities": list(query_entities),
                "query_entities_filtered": list(query_entities_filtered),
                "result_entities": list(result_entities),
                "allowed_types": list(allowed_types) if allowed_types else None,
                "alpha": alpha,
                "raw_affinity": raw_affinity,
                "scaled_affinity": scaled_affinity,
                "score_change": new_score - original_score,
            }

        boosted_results.append(boosted_result)

    return boosted_results
