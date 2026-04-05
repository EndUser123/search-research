"""
BugJail Tests Module

Test suite for bug detection patterns and vulnerabilities.
"""

from .test_compliance import TestConstitutionalCompliance
from .test_integration import TestExplorationIntegration
from .test_patterns import TestBugPatterns
from .test_vulnerabilities import TestVulnerabilityScanner

__all__ = [
    "TestBugPatterns",
    "TestVulnerabilityScanner",
    "TestConstitutionalCompliance",
    "TestExplorationIntegration"
]
