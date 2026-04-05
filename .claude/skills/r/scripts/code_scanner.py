"""Code pattern scanner for detecting TODO, FIXME, HACK, XXX, NOTE markers.

This module scans Python files for code markers and extracts metadata
including risk assessment using the /t skill risk scoring system.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Any

# Import risk scoring from /t skill
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "t"))
from risk_scoring import (
    ChangeContext,
    Kind,
    Size,
    Tier,
    calculate_risk_score,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Pattern to match code markers in comments
# Matches: # MARKER: description or # MARKER description
MARKER_PATTERN = re.compile(
    r'^\s*#\s*(TODO|FIXME|HACK|XXX|NOTE):\s*(.+)$',
    re.IGNORECASE
)

# State impact keywords for detecting high-impact issues
STATE_IMPACT_KEYWORDS = ['error', 'fix', 'crash', 'fail', 'bug', 'issue']

# Risk score thresholds for severity classification
SEVERITY_HIGH_THRESHOLD = 0.7
SEVERITY_MEDIUM_THRESHOLD = 0.4

# Risk score mapping thresholds (0.0-1.0 scale to 0-5 integer scale)
RISK_SCALE_1_THRESHOLD = 0.2
RISK_SCALE_2_THRESHOLD = 0.4
RISK_SCALE_3_THRESHOLD = 0.6
RISK_SCALE_4_THRESHOLD = 0.8

# File extension filter
PYTHON_FILE_EXTENSION = '.py'

# =============================================================================
# Public API
# =============================================================================


def scan_code_patterns(session_files: list[str]) -> list[dict[str, Any]]:
    """Scan Python files for TODO, FIXME, HACK, XXX, NOTE markers.

    For each marker found, extracts type, location, description, and calculates
    risk score using the /t skill risk scoring system.

    Args:
        session_files: List of file paths to scan.

    Returns:
        List of findings, each containing:
            - type: Marker type (TODO/FIXME/HACK/XXX/NOTE).
            - file_path: Path to the file containing the marker.
            - line_number: Line number where marker was found.
            - description: Description text after the marker.
            - risk_score: Risk score (0-5 scale).
            - rollback_complexity: Rollback complexity level.
            - state_impact: State impact level.
            - severity: Severity level (high/medium/low).

    Example:
        >>> files = ["example.py"]
        >>> findings = scan_code_patterns(files)
        >>> for f in findings:
        ...     print(f"{f['type']}: {f['description']}")
    """
    findings: list[dict[str, Any]] = []

    for file_path in session_files:
        # Skip non-Python files
        if not file_path.endswith(PYTHON_FILE_EXTENSION):
            logger.debug(f"Skipping non-Python file: {file_path}")
            continue

        # Skip non-existent files
        path = Path(file_path)
        if not path.exists():
            logger.debug(f"Skipping non-existent file: {file_path}")
            continue

        # Scan file for markers
        try:
            with open(path, encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                match = MARKER_PATTERN.match(line)
                if match:
                    marker_type = match.group(1).upper()
                    description = match.group(2).strip()

                    # Build ChangeContext for risk scoring
                    ctx = _build_change_context(marker_type, file_path)

                    # Calculate risk score
                    risk_score = calculate_risk_score(ctx)

                    # Determine severity from risk score
                    severity = _determine_severity(risk_score)

                    # Override state_impact if keywords detected
                    state_impact = _detect_state_impact(description)

                    # Map risk score to 0-5 scale
                    risk_score_5scale = _map_risk_score_to_5scale(risk_score)

                    finding: dict[str, Any] = {
                        'type': marker_type,
                        'file_path': file_path,
                        'line_number': line_num,
                        'description': description,
                        'risk_score': risk_score_5scale,
                        'rollback_complexity': _map_rollback_complexity(risk_score),
                        'state_impact': state_impact,
                        'severity': severity
                    }

                    findings.append(finding)
                    logger.debug(
                        f"Found {marker_type} at {file_path}:{line_num} - "
                        f"risk={risk_score_5scale}, severity={severity}"
                    )

        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
            continue

    return findings


# =============================================================================
# Helper Functions
# =============================================================================


def _build_change_context(
    marker_type: str,
    file_path: str
) -> ChangeContext:
    """Build a ChangeContext object for risk scoring.

    Maps marker types to appropriate tier/size/kind values for risk assessment.

    Args:
        marker_type: Type of marker (TODO/FIXME/HACK/XXX/NOTE).
        file_path: Path to the file containing the marker.

    Returns:
        ChangeContext object with appropriate risk assessment metadata.
    """
    # Map marker types to risk assessment metadata
    tier_map: dict[str, Tier] = {
        'TODO': Tier.T3_NICE_TO_HAVE,
        'FIXME': Tier.T2_IMPORTANT,
        'HACK': Tier.T1_CRITICAL,
        'XXX': Tier.T2_IMPORTANT,
        'NOTE': Tier.T3_NICE_TO_HAVE
    }

    size_map: dict[str, Size] = {
        'TODO': Size.L_LINE,
        'FIXME': Size.M_FUNCTION,
        'HACK': Size.M_FUNCTION,
        'XXX': Size.M_FUNCTION,
        'NOTE': Size.L_LINE
    }

    kind_map: dict[str, Kind] = {
        'TODO': Kind.EDGE_CASE,
        'FIXME': Kind.ERROR_PATH,
        'HACK': Kind.CORE_LOGIC,
        'XXX': Kind.INTEGRATION,
        'NOTE': Kind.EDGE_CASE
    }

    return ChangeContext(
        git_state="full_scan",  # Session-scoped, assume full scan
        tier=tier_map.get(marker_type, Tier.T3_NICE_TO_HAVE),
        size=size_map.get(marker_type, Size.L_LINE),
        kind=kind_map.get(marker_type, Kind.EDGE_CASE),
        file_path=file_path
    )


def _determine_severity(risk_score: float) -> str:
    """Determine severity level from risk score.

    Args:
        risk_score: Risk score from 0.0 to 1.0.

    Returns:
        Severity level: "high", "medium", or "low".
    """
    if risk_score >= SEVERITY_HIGH_THRESHOLD:
        return "high"
    elif risk_score >= SEVERITY_MEDIUM_THRESHOLD:
        return "medium"
    else:
        return "low"


def _detect_state_impact(description: str) -> str:
    """Detect state impact level from description keywords.

    Args:
        description: Marker description text.

    Returns:
        State impact level: "high", "medium", or "low".
    """
    description_lower = description.lower()

    for keyword in STATE_IMPACT_KEYWORDS:
        if keyword in description_lower:
            return "high"

    return "low"


def _map_risk_score_to_5scale(risk_score: float) -> int:
    """Map 0.0-1.0 risk score to 0-5 integer scale.

    Args:
        risk_score: Risk score from 0.0 to 1.0.

    Returns:
        Integer risk score from 0 to 5.
    """
    # Map risk score ranges to 0-5 scale
    if risk_score < RISK_SCALE_1_THRESHOLD:
        return 1
    elif risk_score < RISK_SCALE_2_THRESHOLD:
        return 2
    elif risk_score < RISK_SCALE_3_THRESHOLD:
        return 3
    elif risk_score < RISK_SCALE_4_THRESHOLD:
        return 4
    else:
        return 5


def _map_rollback_complexity(risk_score: float) -> str:
    """Map risk score to rollback complexity level.

    Args:
        risk_score: Risk score from 0.0 to 1.0.

    Returns:
        Rollback complexity: "low", "medium", or "high".
    """
    if risk_score < 0.3:
        return "low"
    elif risk_score < 0.7:
        return "medium"
    else:
        return "high"
