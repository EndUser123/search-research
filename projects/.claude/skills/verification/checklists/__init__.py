"""
Shared checklist library structure for verification checklists.

This module provides the base classes and data structures for domain-specific
verification checklists (skills, hooks, features).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class ChecklistResult:
    """Result of a verification checklist execution.

    Attributes:
        status: Overall verification status (e.g., 'pass', 'fail', 'partial')
        items_checked: Total number of items verified
        items_passed: Number of items that passed verification
        findings: List of issues, discoveries, or warnings
    """
    status: str
    items_checked: int
    items_passed: int
    findings: List[str]


class VerificationChecklist(ABC):
    """Abstract base class for domain-specific verification checklists.

    Subclasses must implement the verify_target() method to perform
    actual verification logic for specific target types.
    """

    #: Supported domain types for checklist retrieval
    VALID_DOMAINS: List[str] = ["skill", "hook", "feature"]

    @abstractmethod
    def verify_target(self, target_type: str, target_path: str) -> ChecklistResult:
        """Verify a target against the checklist.

        Args:
            target_type: Type of target being verified
            target_path: Path to the target to verify

        Returns:
            ChecklistResult with verification outcomes
        """

    def get_checklist(self, domain: str) -> Dict[str, Any]:
        """Get the checklist for a specific domain.

        Args:
            domain: Domain to get checklist for (supports: 'skill', 'hook', 'feature')

        Returns:
            Dictionary containing the checklist for the domain

        Raises:
            ValueError: If domain is not one of the supported domains
        """
        if domain not in self.VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain: {domain}. Must be one of {self.VALID_DOMAINS}"
            )

        return {"domain": domain, "items": []}
