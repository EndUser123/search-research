"""
DEPRECATED — Do not import. Retained for reference only.

Superseded by: epistemic_validator.py (unified).
Only consumer was StopHook_epistemic_contract.py (also deprecated).

Epistemic Bindings Helper for debugRCA

TASK-003: Extract commitments from RCA responses with proper normalization

This helper extracts the 8 required commitment sections from RCA responses:
- Symptom
- Evidence
- Executed Path
- Alternative Hypothesis
- Falsifier
- Root Cause
- Fix
- Verification

Acceptance: Helper successfully extracts commitments from RCA responses with proper normalization
"""

from __future__ import annotations

import re
from typing import Any

# Type aliases
CommitmentsDict = dict[str, str]

# Required commitment section names (immutable tuple)
REQUIRED_COMMITMENTS = (
    "Symptom",
    "Evidence",
    "Executed Path",
    "Alternative Hypothesis",
    "Falsifier",
    "Root Cause",
    "Fix",
    "Verification",
)

# Compiled regex patterns for efficiency
SECTION_PATTERN = re.compile(r"###\s*([^\n#]+?)\s*\n(.*?)(?=\n###\s*|\Z)", re.DOTALL)
TIME_SCOPE_PATTERNS = {
    "current-state": re.compile(r"\(current-state\)|current-state", re.IGNORECASE),
    "transcript-time": re.compile(r"\(transcript-time\)|transcript-time", re.IGNORECASE),
    "inference": re.compile(r"\(inference\)|inference", re.IGNORECASE),
}
TIER_PATTERN = re.compile(r"\(Tier\s+(\d+)")
CONFIDENCE_PATTERN = re.compile(r"Tier\s+\d+,\s*(\d+)%")
FILE_LOCATION_PATTERN = re.compile(r"\(([\w./]+):(\d+)\)")
CHECKLIST_ITEM_PATTERN = re.compile(r"^\s*-\s*\[([ x])\]\s*(.+)$")


def extract_commitments(rca_response: str) -> dict[str, str]:
    """Extract all 8 commitment sections from RCA response.

    Args:
        rca_response: The full RCA response text

    Returns:
        Dictionary mapping section names to their content
    """
    commitments: dict[str, str] = {}

    # Use compiled pattern for efficiency
    sections = SECTION_PATTERN.findall(rca_response)

    for section_name, content in sections:
        # Normalize section name
        normalized_name = section_name.strip()

        # Check if this is one of our required sections (case-insensitive match)
        for required in REQUIRED_COMMITMENTS:
            if normalized_name.lower() == required.lower():
                # Clean up content
                commitments[required] = content.strip()
                break

    return commitments


def detect_time_scopes(text: str) -> set[str]:
    """Detect time-scope labels in text.

    Args:
        text: Text to search for time-scope labels

    Returns:
        Set of detected scopes: {"current-state", "transcript-time", "inference"}
    """
    scopes = set()

    # Use compiled patterns for efficiency
    for scope, pattern in TIME_SCOPE_PATTERNS.items():
        if pattern.search(text):
            scopes.add(scope)

    return scopes


def normalize_artifact_path(path: str) -> str:
    """Normalize artifact paths to consistent format.

    Args:
        path: File path to normalize

    Returns:
        Normalized path with forward slashes
    """
    # Convert backslashes to forward slashes
    normalized = path.replace("\\", "/")

    # Remove redundant ./ prefixes (but keep ../ for relative paths)
    if normalized.startswith("./"):
        normalized = normalized[2:]

    return normalized


def extract_root_cause_details(root_cause_text: str) -> dict[str, Any]:
    """Extract tier, confidence, and location from Root Cause section.

    Args:
        root_cause_text: Root Cause section content

    Returns:
        Dictionary with keys: tier, confidence, file_path, line_number
    """
    details: dict[str, Any] = {}

    # Extract tier: (Tier X, Y%)
    tier_match = TIER_PATTERN.search(root_cause_text)
    if tier_match:
        details["tier"] = int(tier_match.group(1))

    # Extract confidence: XX% (after tier)
    confidence_match = CONFIDENCE_PATTERN.search(root_cause_text)
    if confidence_match:
        details["confidence"] = int(confidence_match.group(1))

    # Extract file path: (file.py:XX)
    file_match = FILE_LOCATION_PATTERN.search(root_cause_text)
    if file_match:
        details["file_path"] = file_match.group(1)
        details["line_number"] = file_match.group(2)

    return details


def is_section_empty(text: str) -> bool:
    """Check if section content is empty or whitespace-only.

    Args:
        text: Section content to check

    Returns:
        True if section is empty/whitespace-only, False otherwise
    """
    # Strip all whitespace and check if empty
    return len(text.strip()) == 0


def extract_verification_items(verification_text: str) -> list[dict[str, Any]]:
    """Extract checklist items from Verification section.

    Args:
        verification_text: Verification section content

    Returns:
        List of dicts with keys: text, checked
    """
    items: list[dict[str, Any]] = []

    # Use compiled pattern for efficiency
    for line in verification_text.split("\n"):
        match = CHECKLIST_ITEM_PATTERN.match(line)
        if match:
            checkbox = match.group(1)
            text = match.group(2).strip()

            items.append(
                {
                    "text": text,
                    "checked": checkbox.lower() == "x",
                }
            )

    return items
