"""
Migration module for assumption_audit_v2.py

Provides drop-in replacement functions for entity extraction
that use the new tiered extraction system.

Usage in assumption_audit_v2.py:
    # Replace old imports with:
    from entity_extraction.migrate import (
        extract_entities_from_text,
        extract_entities_from_claims,
        extract_entities_from_evidence,
        check_entity_overlap,
    )
"""

import os
from typing import List, Set, Tuple

# Feature flag for rollback
USE_NEW_EXTRACTION = os.environ.get("USE_NEW_ENTITY_EXTRACTION", "true").lower() == "true"
DEBUG = os.environ.get("ENTITY_EXTRACTOR_DEBUG", "false").lower() == "true"

# Lazy-loaded extractor
_extractor = None

def _get_extractor():
    """Get or create the entity extractor."""
    global _extractor
    if _extractor is None:
        if USE_NEW_EXTRACTION:
            try:
                from .extractor import EntityExtractor
                _extractor = EntityExtractor()
            except ImportError:
                # Fallback to old behavior
                _extractor = "legacy"
        else:
            _extractor = "legacy"
    return _extractor


def extract_entities_from_text(text: str) -> Set[str]:
    """
    Extract entities from arbitrary text.
    
    Drop-in replacement for assumption_audit_v2.extract_entities_from_text
    
    Key change: Only returns high-confidence (structural + semantic validated) entities.
    """
    extractor = _get_extractor()

    if extractor == "legacy":
        # Import original function for fallback
        from assumption_audit_v2 import extract_entities_from_text as legacy_extract
        return legacy_extract(text)

    result = extractor.extract(text, context_type='claim')
    # Return only high-confidence entities (structural + semantic validated)
    # This prevents prose words from being flagged as uncovered
    return result.high_confidence()


def extract_entities_from_claims(claims: List[str], response_text: str) -> Set[str]:
    """
    Extract entities from detected claims and response text.
    
    Drop-in replacement for assumption_audit_v2.extract_entities_from_claims
    """
    extractor = _get_extractor()

    if extractor == "legacy":
        from assumption_audit_v2 import extract_entities_from_claims as legacy_extract
        return legacy_extract(claims, response_text)

    entities = set()

    # Extract from claims
    for claim in claims:
        result = extractor.extract(claim, context_type='claim')
        entities.update(result.all_normalized())

    # Extract from response (structural only for prose)
    result = extractor.extract(response_text, context_type='claim')
    # For claims, we want higher confidence entities
    entities.update(result.structural)  # Only add high-confidence structural

    if DEBUG:
        print(f"[migrate] Claim entities: {entities}")

    return entities


def extract_entities_from_evidence(tool_sequence: List[dict]) -> Set[str]:
    """
    Extract entities from tool outputs.
    
    Drop-in replacement for assumption_audit_v2.extract_entities_from_evidence
    """
    extractor = _get_extractor()

    if extractor == "legacy":
        from assumption_audit_v2 import extract_entities_from_evidence as legacy_extract
        return legacy_extract(tool_sequence)

    entities = set()

    # Observation tools to consider
    OBSERVATION_TOOLS = {"Read", "Bash", "Grep", "Glob", "Search", "WebFetch"}
    READ_ONLY_BASH_PREFIXES = (
        "git status", "git log", "git diff", "git show", "git branch",
        "ls", "cat ", "head ", "tail ", "grep ", "find ", "wc ", "stat ", "pwd",
        "echo ", "type ", "dir ", "Get-Content", "Get-ChildItem", "Test-Path",
        "python -c", "pytest",
    )

    for tool in tool_sequence:
        if not isinstance(tool, dict):
            continue

        name = tool.get("name", "")
        command = tool.get("command", "")
        output = tool.get("output", "")
        cwd = tool.get("cwd", "")

        # Check if observational
        is_observational = name in OBSERVATION_TOOLS
        if name == "Bash":
            cmd = str(command).strip()
            is_observational = any(cmd.startswith(p) for p in READ_ONLY_BASH_PREFIXES)

        if not is_observational:
            continue

        # Extract from command/path (structural entities)
        if command:
            result = extractor.extract(str(command), context_type='evidence')
            entities.update(result.structural)

        if cwd:
            result = extractor.extract(str(cwd), context_type='evidence')
            entities.update(result.structural)

        # Extract from output (cap for performance)
        if output:
            output_sample = str(output)[:2000]
            result = extractor.extract(output_sample, context_type='evidence')
            entities.update(result.structural)

    if DEBUG:
        print(f"[migrate] Evidence entities: {entities}")

    return entities


def check_entity_overlap(
    claim_entities: Set[str],
    evidence_entities: Set[str],
    coverage_threshold: float = 0.5
) -> Tuple[bool, Set[str], Set[str]]:
    """
    Check if claim entities have overlap with evidence entities.
    
    Drop-in replacement for assumption_audit_v2.check_entity_overlap
    
    Returns: (has_sufficient_overlap, overlapping, uncovered)
    """
    if not claim_entities:
        # No specific entities in claims - allow
        return True, set(), set()

    if not evidence_entities:
        # Claims have entities but no evidence - fail
        return False, set(), claim_entities

    # Direct overlap
    overlapping = claim_entities & evidence_entities

    # Fuzzy overlap: substring matching
    fuzzy_overlap = set()
    for claim_ent in claim_entities:
        for ev_ent in evidence_entities:
            # Full containment
            if claim_ent in ev_ent or ev_ent in claim_ent:
                fuzzy_overlap.add(claim_ent)
                break

            # Basename matching (for paths)
            claim_base = claim_ent.rsplit("/", 1)[-1] if "/" in claim_ent else claim_ent
            ev_base = ev_ent.rsplit("/", 1)[-1] if "/" in ev_ent else ev_ent
            if claim_base == ev_base and len(claim_base) > 3:
                fuzzy_overlap.add(claim_ent)
                break

    all_covered = overlapping | fuzzy_overlap
    uncovered = claim_entities - all_covered

    # Coverage calculation
    coverage_ratio = len(all_covered) / len(claim_entities) if claim_entities else 1.0

    # Threshold logic
    if len(claim_entities) >= 3:
        has_sufficient = coverage_ratio >= coverage_threshold
    else:
        has_sufficient = len(all_covered) >= 1

    if DEBUG:
        print(f"[migrate] Overlap: {all_covered}, Uncovered: {uncovered}, Ratio: {coverage_ratio:.2f}")

    return has_sufficient, all_covered, uncovered
