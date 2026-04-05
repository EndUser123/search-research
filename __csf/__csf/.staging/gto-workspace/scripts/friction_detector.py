"""Hook Friction Detection for /gto skill.

Analyzes conversation for blocks, corrections, and rework.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class FrictionDetector:
    """Detect conversation friction indicating workflow problems."""

    def __init__(self) -> None:
        """Initialize friction detector."""
        logger.info("FrictionDetector initialized")

    def detect_blocks(self, conversation: str) -> list[dict[str, Any]]:
        """Detect blocking patterns in conversation."""
        blocks = []
        block_patterns = [
            r"(?:blocked|stuck|waiting for|can't proceed|unable to)",
            r"(?:hook error|permission denied|access denied)",
            r"(?:path security|BLOCKED_PATTERN)",
        ]
        for pattern in block_patterns:
            matches = re.finditer(pattern, conversation, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(conversation), match.end() + 50)
                context = conversation[start:end].replace("\n", " ")
                blocks.append({"type": "block", "severity": "high", "context": context.strip()})
        return blocks

    def detect_corrections(self, conversation: str) -> list[dict[str, Any]]:
        """Detect correction patterns."""
        corrections = []
        patterns = [r"(?:undo|revert|roll back)", r"(?:fix that|correct that)", r"(?:actually|wait|no,)"]
        for pattern in patterns:
            matches = re.finditer(pattern, conversation, re.IGNORECASE)
            for _ in matches:
                corrections.append({"type": "correction", "severity": "medium"})
        return corrections

    def analyze_conversation(self, conversation: str) -> dict[str, Any]:
        """Perform full friction analysis."""
        blocks = self.detect_blocks(conversation)
        corrections = self.detect_corrections(conversation)
        score = len(blocks) * 10 + len(corrections) * 5
        level = "high" if score >= 30 else "medium" if score >= 15 else "low"
        return {"friction_level": level, "score": score, "blocks": len(blocks), "corrections": len(corrections)}
