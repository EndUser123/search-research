#!/usr/bin/env python3
"""
CKS Auto-Extractor for RCA Learnings

Automatically extracts and stores learnings from resolved RCA incidents into CKS.
This closes the learning loop by capturing what worked for future reference.

Usage:
    from rca.cks_auto_extractor import extract_and_store_learning

    # After a successful fix
    extract_and_store_learning(
        session_id="rca_1234567890",
        problem_description="AttributeError: 'NoneType' object has no attribute 'x'",
        root_cause="Missing null check before accessing dict key",
        fix_applied="Added if key in dict: check before access",
        files_changed=["src/handler.py"],
    )

Author: CSF Development Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from .outcome_recorder import Outcome, get_outcome_recorder

logger = logging.getLogger(__name__)

# import CKS
try:
    from search_research.cks.unified import CKS

    CKS_AVAILABLE = True
except ImportError:
    CKS_AVAILABLE = False
    CKS = None  # type: ignore[assignment]


@dataclass
class Learning:
    """A learning extracted from a resolved RCA incident."""

    session_id: str
    problem_type: str
    problem_signature: str
    root_cause: str
    fix_applied: str
    files_changed: list[str]
    lesson: str
    extracted_at: str


class CKSAutoExtractor:
    """
    Automatically extracts and stores learnings from resolved RCA incidents.

    Features:
    - Detects when an RCA session has a RESOLVED outcome
    - Extracts key learning points (problem, cause, fix)
    - Stores in CKS as 'correction' type for future retrieval
    - Links learnings to error patterns for semantic search
    """

    ENTRY_TYPE = "correction"

    def __init__(self, cks_instance: CKS | None = None):
        """
        Initialize CKS auto-extractor.

        Args:
            cks_instance: Optional CKS instance (uses default if not provided)

        """
        if not CKS_AVAILABLE:
            logger.warning("CKS not available - auto-extraction will be disabled")
            self._cks = None
        else:
            self._cks = cks_instance if cks_instance else CKS()

        self._outcome_recorder = get_outcome_recorder()

    def extract_and_store(
        self,
        session_id: str,
        problem_description: str,
        root_cause: str,
        fix_applied: str,
        files_changed: list[str] | None = None,
        lesson: str | None = None,
    ) -> bool:
        """
        Extract and store a learning from a resolved RCA session.

        Args:
            session_id: The RCA session ID
            problem_description: What the problem was
            root_cause: What caused it
            fix_applied: What fixed it
            files_changed: List of files modified
            lesson: Optional lesson learned (auto-generated if not provided)

        Returns:
            True if stored successfully

        """
        if not self._cks:
            logger.warning("CKS not available - cannot store learning")
            return False

        # Auto-generate lesson if not provided
        if not lesson:
            lesson = self._generate_lesson(problem_description, root_cause, fix_applied)

        # Create learning record
        learning = Learning(
            session_id=session_id,
            problem_type=self._classify_problem(problem_description),
            problem_signature=self._create_signature(problem_description),
            root_cause=root_cause,
            fix_applied=fix_applied,
            files_changed=files_changed or [],
            lesson=lesson,
            extracted_at=datetime.now(tz=UTC).isoformat(),
        )

        # Store in CKS
        return self._store_learning(learning)

    def extract_from_resolved_session(self, session_id: str, rca_report: str) -> bool:
        """
        Extract learning from an RCA report for a resolved session.

        Parses the RCA report to extract problem, cause, and fix.

        Args:
            session_id: The RCA session ID
            rca_report: The full RCA report text

        Returns:
            True if learning extracted and stored

        """
        # Verify session was resolved
        outcome = self._outcome_recorder.get_outcome(session_id)
        if not outcome or outcome.outcome != Outcome.RESOLVED.value:
            logger.info(
                "Session %s not resolved (outcome: %s) - skipping extraction",
                session_id,
                outcome.outcome if outcome else "unknown",
            )
            return False

        # Parse RCA report
        parsed = self._parse_rca_report(rca_report)
        if not parsed:
            logger.warning("Could not parse RCA report for session %s", session_id)
            return False

        # Extract and store
        return self.extract_and_store(
            session_id=session_id,
            problem_description=parsed.get("problem", ""),
            root_cause=parsed.get("root_cause", ""),
            fix_applied=parsed.get("fix", ""),
            files_changed=parsed.get("files_changed", []),
            lesson=parsed.get("lesson"),
        )

    def _generate_lesson(self, problem: str, cause: str, fix: str) -> str:
        """Generate a lesson summary from problem, cause, and fix."""
        # Create concise lesson
        return f"When facing '{problem[:100]}...', remember: {fix[:200]}"

    def _classify_problem(self, problem_description: str) -> str:
        """Classify the problem type."""
        problem_lower = problem_description.lower()

        if any(
            kw in problem_lower for kw in ["attributeerror", "keyerror", "none", "null", "missing"]
        ):
            return "null_access"
        elif any(kw in problem_lower for kw in ["import", "module", "package", "dependency"]):
            return "import_error"
        elif any(kw in problem_lower for kw in ["timeout", "slow", "performance"]):
            return "performance"
        elif any(kw in problem_lower for kw in ["race", "concurrent", "deadlock"]):
            return "concurrency"
        elif any(kw in problem_lower for kw in ["type", "typeerror", "cast"]):
            return "type_error"
        else:
            return "general"

    def _create_signature(self, problem_description: str) -> str:
        """Create a signature for the problem (first 100 chars)."""
        # Normalize and truncate
        normalized = problem_description.lower().strip()
        # Remove variable names, numbers
        import re

        normalized = re.sub(r"\b\d+\b", "", normalized)
        normalized = re.sub(r"\b[a-z_]+\.", "", normalized)  # Remove module prefixes
        return normalized[:100]

    def _store_learning(self, learning: Learning) -> bool:
        """Store learning in CKS."""
        if not self._cks:
            return False

        try:
            # Create content
            content = self._format_learning_content(learning)

            # Create metadata
            metadata = {
                "session_id": learning.session_id,
                "problem_type": learning.problem_type,
                "problem_signature": learning.problem_signature,
                "root_cause": learning.root_cause,
                "fix_applied": learning.fix_applied,
                "files_changed": learning.files_changed,
                "extracted_at": learning.extracted_at,
                "learning_type": "rca_resolution",
            }

            # Ingest into CKS
            entry_id = self._cks.ingest_correction(
                title=f"RCA Learning: {learning.problem_type}",
                content=content,
                source_chunk=learning.lesson,
                **metadata,
            )

            if entry_id:
                logger.info(
                    "Stored RCA learning from session %s as CKS entry %s",
                    learning.session_id,
                    entry_id,
                )
                return True

        except Exception as e:
            logger.exception("Failed to store learning in CKS: %s", e)

        return False

    def _format_learning_content(self, learning: Learning) -> str:
        """Format learning as readable content."""
        parts = [
            "## Problem",
            learning.problem_signature,
            "",
            "## Root Cause",
            learning.root_cause,
            "",
            "## Fix Applied",
            learning.fix_applied,
        ]

        if learning.files_changed:
            parts.append("")
            parts.append("## Files Changed")
            for f in learning.files_changed:
                parts.append(f"- {f}")

        parts.append("")
        parts.append("## Lesson")
        parts.append(learning.lesson)

        return "\n".join(parts)

    def _parse_rca_report(self, rca_report: str) -> dict | None:
        """
        Parse an RCA report to extract key information.

        Looks for sections like:
        - Root Cause
        - Fix
        - Files

        Args:
            rca_report: The full RCA report text

        Returns:
            Dict with extracted info or None

        """
        import re

        result = {}

        # Extract root cause
        cause_match = re.search(
            r"#{2,}\s*Root\s+Cause\s*\n+(.*?)(?=#{2,}|\Z)", rca_report, re.DOTALL | re.IGNORECASE
        )
        if cause_match:
            result["root_cause"] = cause_match.group(1).strip()[:500]

        # Extract fix
        fix_match = re.search(
            r"#{2,}\s*Fix\s*\n+(.*?)(?=#{2,}|\Z)", rca_report, re.DOTALL | re.IGNORECASE
        )
        if fix_match:
            result["fix"] = fix_match.group(1).strip()[:500]

        # Extract files
        files_match = re.search(r"[:\-]\s+([\w/_.]+\.?\w*)", rca_report)
        if files_match:
            result["files_changed"] = [files_match.group(1)]

        # Extract problem from first line
        first_line = rca_report.split("\n")[0]
        if first_line:
            result["problem"] = first_line.strip()[:200]

        # Return None if we didn't get essential info
        if "root_cause" not in result or "fix" not in result:
            return None

        return result

    def store_negative_learning(
        self,
        session_id: str,
        problem_description: str,
        attempted_fix: str,
        why_it_failed: str,
        notes: str = "",
    ) -> bool:
        """
        Store a negative learning (what did NOT work and why).

        This prevents future sessions from repeating the same failed approaches.

        Args:
            session_id: The RCA session ID
            problem_description: What the problem was
            attempted_fix: What was tried
            why_it_failed: Why it didn't work
            notes: Additional context

        Returns:
            True if stored successfully

        """
        if not self._cks:
            logger.warning("CKS not available - cannot store negative learning")
            return False

        try:
            content = "\n".join(
                [
                    "## Problem",
                    problem_description,
                    "",
                    "## Attempted Fix (FAILED)",
                    attempted_fix,
                    "",
                    "## Why It Failed",
                    why_it_failed,
                ]
            )

            if notes:
                content += f"\n\n## Notes\n{notes}"

            title = f"NEGATIVE: {attempted_fix[:80]}"

            metadata = {
                "session_id": session_id,
                "problem_type": self._classify_problem(problem_description),
                "outcome": "failed",
                "extracted_at": datetime.now(tz=UTC).isoformat(),
                "learning_type": "negative_rca_resolution",
            }

            entry_id = self._cks.ingest_correction(
                title=title,
                content=content,
                source_chunk=f"DOES NOT WORK: {attempted_fix} for {problem_description}",
                **metadata,
            )

            if entry_id:
                logger.info(
                    "Stored negative learning from session %s as CKS entry %s",
                    session_id,
                    entry_id,
                )
                return True

        except Exception as e:
            logger.exception("Failed to store negative learning in CKS: %s", e)

        return False

    def batch_extract_resolved(self, days: int = 7, limit: int = 50) -> dict:
        """
        Batch extract learnings from recently resolved sessions.

        Args:
            days: Days to look back
            limit: Maximum sessions to process

        Returns:
            Dict with extraction results

        """
        results = {
            "processed": 0,
            "stored": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        if not self._cks:
            results["errors"].append("CKS not available")
            return results

        # Get resolved sessions from outcome recorder
        # Note: This would need to query the database for resolved outcomes
        # For now, return placeholder
        logger.info("Batch extraction not yet fully implemented")
        return results


# Singleton instance
_extractor_instance: CKSAutoExtractor | None = None


def get_cks_auto_extractor() -> CKSAutoExtractor:
    """Get or create the singleton CKS auto-extractor instance."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = CKSAutoExtractor()
    return _extractor_instance


def extract_and_store_learning(
    session_id: str,
    problem_description: str,
    root_cause: str,
    fix_applied: str,
    files_changed: list[str] | None = None,
    lesson: str | None = None,
) -> bool:
    """
    Quick function to extract and store a learning.

    Args:
        session_id: The RCA session ID
        problem_description: What the problem was
        root_cause: What caused it
        fix_applied: What fixed it
        files_changed: List of files modified
        lesson: Optional lesson learned

    Returns:
        True if stored successfully

    """
    return get_cks_auto_extractor().extract_and_store(
        session_id, problem_description, root_cause, fix_applied, files_changed, lesson
    )


if __name__ == "__main__":
    # Self-test
    print("CKS Auto-Extractor Test")

    if not CKS_AVAILABLE:
        print("CKS not available - skipping test")
    else:
        extractor = CKSAutoExtractor()

        # Test extraction
        success = extractor.extract_and_store(
            session_id="test_session_123",
            problem_description="AttributeError: 'NoneType' object has no attribute 'x'",
            root_cause="Missing null check before dict access",
            fix_applied="Added 'if key in dict:' check before accessing",
            files_changed=["src/handler.py"],
        )

        print(f"Extraction {'succeeded' if success else 'failed'}")
