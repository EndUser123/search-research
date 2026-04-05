#!/usr/bin/env python3
"""
Temporal Check - Week 3 RCA Enhancement

Validates that proposed fixes use current APIs, not deprecated ones.
Implements temporal freshness checking for RCA hypotheses.

Author: CSF Development Team
Version: 1.0.0
Part of: Week 3 RCA Enhancements
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TemporalVerdict(Enum):
    """Verdict for temporal freshness check."""
    VALID = "VALID"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


@dataclass
class TemporalWarning:
    """Warning about deprecated API usage."""
    api: str
    severity: str  # "low", "medium", "high"
    suggestion: str
    reason: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "api": self.api,
            "severity": self.severity,
            "suggestion": self.suggestion,
            "reason": self.reason
        }


class DeprecationDatabase:
    """Knowledge base of deprecated APIs across languages."""

    def __init__(self):
        """Initialize deprecation database with known deprecated APIs."""
        self.database = self._build_deprecation_db()

    def _build_deprecation_db(self) -> dict:
        """Known deprecations by language/framework."""
        return {
            'python': {
                'os.path': {
                    'deprecated_in': '3.4',
                    'modern': 'pathlib.Path',
                    'reason': 'More Pythonic, object-oriented API'
                },
                'os.path.join': {
                    'deprecated_in': '3.4',
                    'modern': 'pathlib.Path',
                    'reason': 'Use pathlib for better path handling'
                },
                'os.path.exists': {
                    'deprecated_in': '3.4',
                    'modern': 'Path.exists()',
                    'reason': 'pathlib provides cleaner API'
                },
                'asyncio.run': {
                    'deprecated_in': None,
                    'available_in': '3.7+',
                    'fallback': 'asyncio.get_event_loop().run_until_complete()',
                    'reason': 'Requires Python 3.7+'
                },
                'toml': {
                    'deprecated_in': '3.11',
                    'modern': 'tomllib (built-in)',
                    'reason': 'Native support added in 3.11'
                },
                'typing.Dict': {
                    'deprecated_in': '3.9',
                    'modern': 'dict (builtin generic)',
                    'reason': 'Use lowercase dict since 3.9'
                },
                'typing.List': {
                    'deprecated_in': '3.9',
                    'modern': 'list (builtin generic)',
                    'reason': 'Use lowercase list since 3.9'
                },
                'SafeConfigParser': {
                    'deprecated_in': '3.2',
                    'modern': 'ConfigParser',
                    'reason': 'SafeConfigParser renamed to ConfigParser'
                },
                'configparser.SafeConfigParser': {
                    'deprecated_in': '3.2',
                    'modern': 'ConfigParser',
                    'reason': 'SafeConfigParser renamed to ConfigParser'
                }
            },
            'typescript': {
                'any': {
                    'deprecated_in': None,
                    'modern': 'unknown or specific type',
                    'reason': 'Defeats type safety'
                },
                'interface': {
                    'note': 'Not deprecated, but consider type for simpler structures',
                    'alternative': 'type'
                }
            },
            'javascript': {
                'XMLHttpRequest': {
                    'deprecated_in': 'ES6',
                    'modern': 'fetch API',
                    'reason': 'Native, promise-based'
                },
                'var': {
                    'deprecated_in': 'ES6',
                    'modern': 'const/let',
                    'reason': 'Block scoping, prevent hoisting issues'
                },
                'Promise.then chains': {
                    'note': 'Consider async/await for readability',
                    'modern': 'async/await'
                }
            },
            'numpy': {
                'np.int': {
                    'deprecated_in': '1.20',
                    'modern': 'np.int_ or built-in int',
                    'reason': 'Alias removed in NumPy 1.20'
                },
                'np.float': {
                    'deprecated_in': '1.20',
                    'modern': 'np.float64 or built-in float',
                    'reason': 'Alias removed in NumPy 1.20'
                }
            }
        }

    def get_entry(self, language: str, api: str) -> dict | None:
        """Get deprecation entry for API."""
        return self.database.get(language, {}).get(api)

    def search_apis(self, text: str) -> list[tuple]:
        """Search for deprecated APIs in text."""
        found = []
        text_lower = text.lower()

        for language, apis in self.database.items():
            for api, info in apis.items():
                # Case-insensitive search for API names
                if api.lower() in text_lower:
                    found.append((language, api, info))

        return found


class VersionExtractor:
    """Extracts version information from code and environment."""

    def __init__(self):
        self.version_cache = {}

    def extract_python_version(self) -> str:
        """Extract current Python version."""
        try:
            result = subprocess.run(
                ['python', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() or result.stderr.strip()
        except Exception:
            return "unknown"

    def extract_imports(self, code: str) -> list[str]:
        """Extract imports from code snippet."""
        imports = []

        # Match "from X import Y"
        imports.extend(re.findall(r'from\s+(\w+(?:\.\w+)*)\s+import', code))

        # Match "import X"
        imports.extend(re.findall(r'import\s+(\w+)', code))

        # Split dotted imports to get base module
        base_imports = []
        for imp in imports:
            base = imp.split('.')[0]
            if base not in base_imports:
                base_imports.append(base)

        return list(set(base_imports))

    def extract_versions(self, error_context: str) -> dict[str, str]:
        """Extract package versions from error and environment."""
        versions = {}

        # Python version
        versions['python'] = self.extract_python_version()

        # Extract imports from error context
        imports = self.extract_imports(error_context)

        for pkg in imports:
            if pkg in self.version_cache:
                versions[pkg] = self.version_cache[pkg]
                continue

            try:
                result = subprocess.run(
                    ['pip', 'show', pkg],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            version = line.split(': ')[1].strip()
                            versions[pkg] = version
                            self.version_cache[pkg] = version
                            break
            except Exception:
                pass

        return versions

    def parse_python_version(self, version_str: str) -> tuple:
        """Parse Python version string to tuple."""
        # Handle "Python 3.14.0" or "3.14.0"
        match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', version_str)
        if match:
            major, minor, patch = match.groups()
            return (int(major), int(minor), int(patch) if patch else 0)
        return (0, 0, 0)


@dataclass
class TemporalCheckResult:
    """Result of temporal freshness check."""
    verdict: TemporalVerdict
    warnings: list[TemporalWarning] = field(default_factory=list)
    confidence: float = 0.0
    checked_at: datetime = field(default_factory=datetime.now)

    def has_warnings(self) -> bool:
        """Check if any warnings were generated."""
        return len(self.warnings) > 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "verdict": self.verdict.value,
            "warnings": [w.to_dict() for w in self.warnings],
            "confidence": self.confidence,
            "checked_at": self.checked_at.isoformat()
        }


class TemporalCheck:
    """
    Validate that proposed fixes use current APIs, not deprecated ones.

    Performs temporal freshness checking on RCA hypotheses to ensure
    proposed solutions use modern, supported APIs rather than deprecated
    alternatives.
    """

    def __init__(self):
        """Initialize temporal checker with deprecation database."""
        self.deprecation_db = DeprecationDatabase()
        self.version_extractor = VersionExtractor()

    def check(
        self,
        hypothesis: str,
        context: dict | None = None
    ) -> TemporalCheckResult:
        """
        Check hypothesis for deprecated API usage.

        Args:
            hypothesis: Proposed solution text to check
            context: Optional context (python_version, etc.)

        Returns:
            TemporalCheckResult with verdict and warnings
        """
        context = context or {}
        warnings = []

        # Search for deprecated APIs
        found_apis = self.deprecation_db.search_apis(hypothesis)

        for _language, api, info in found_apis:
            severity = self._calculate_severity(info, context)
            suggestion = self._build_suggestion(api, info)

            warning = TemporalWarning(
                api=api,
                severity=severity,
                suggestion=suggestion,
                reason=info.get('reason', 'Deprecated API')
            )
            warnings.append(warning)

        # Determine verdict
        verdict = self._determine_verdict(warnings, hypothesis)

        # Calculate confidence
        confidence = self._calculate_confidence(warnings, hypothesis)

        return TemporalCheckResult(
            verdict=verdict,
            warnings=warnings,
            confidence=confidence
        )

    def _calculate_severity(self, info: dict, context: dict) -> str:
        """Calculate severity based on deprecation info and context."""
        # High severity if clearly deprecated
        if 'deprecated_in' in info and info['deprecated_in']:
            return 'high'

        # Medium severity if version-specific
        if 'available_in' in info:
            python_version = context.get('python_version', '')
            if python_version:
                # Check if current version supports the API
                required = info['available_in'].rstrip('+')
                if self._is_version_compatible(python_version, required):
                    return 'low'
                else:
                    return 'high'

        # Default to medium
        return 'medium'

    def _is_version_compatible(self, current: str, required: str) -> bool:
        """Check if current version meets required version."""
        current_parsed = self.version_extractor.parse_python_version(current)
        required_parsed = self.version_extractor.parse_python_version(required)

        return current_parsed >= required_parsed

    def _build_suggestion(self, api: str, info: dict) -> str:
        """Build suggestion message for deprecated API."""
        if 'modern' in info:
            return f"Use {info['modern']} instead of {api}"
        elif 'fallback' in info:
            return f"Consider: {info['fallback']}"
        elif 'alternative' in info:
            return info['alternative']
        else:
            return f"Review usage of {api}"

    def _determine_verdict(
        self,
        warnings: list[TemporalWarning],
        hypothesis: str
    ) -> TemporalVerdict:
        """Determine overall verdict based on warnings."""
        if not warnings:
            # No deprecated APIs found - check if any APIs were mentioned at all
            api_keywords = ['import', 'use', 'call', 'api', 'function', 'method']
            has_api_mentions = any(kw in hypothesis.lower() for kw in api_keywords)

            if has_api_mentions:
                # Mentions APIs but none deprecated - valid
                return TemporalVerdict.VALID
            else:
                # No clear API mentions - unknown
                return TemporalVerdict.UNKNOWN

        # Check severity of warnings
        high_severity = sum(1 for w in warnings if w.severity == 'high')
        medium_severity = sum(1 for w in warnings if w.severity == 'medium')

        if high_severity > 0:
            return TemporalVerdict.REJECTED
        elif medium_severity > 1:
            # Multiple medium warnings = reject
            return TemporalVerdict.REJECTED
        else:
            return TemporalVerdict.REJECTED

    def _calculate_confidence(
        self,
        warnings: list[TemporalWarning],
        hypothesis: str
    ) -> float:
        """Calculate confidence in the verdict."""
        if not warnings:
            # No warnings but hypothesis is generic
            if len(hypothesis) < 50:
                return 0.3
            return 0.6

        # Higher confidence with more specific API mentions
        base_confidence = 0.7
        specificity_bonus = min(len(warnings) * 0.1, 0.2)

        return min(base_confidence + specificity_bonus, 1.0)


def run_temporal_check(
    hypothesis: str,
    context: dict | None = None
) -> TemporalCheckResult:
    """
    Convenience function to run temporal check.

    Args:
        hypothesis: Proposed solution to check
        context: Optional version context

    Returns:
        TemporalCheckResult with verdict
    """
    checker = TemporalCheck()
    return checker.check(hypothesis, context)


if __name__ == "__main__":
    # Self-test
    print("=== Temporal Check Self-Test ===\n")

    checker = TemporalCheck()

    # Test 1: Deprecated os.path
    print("Test 1: Deprecated os.path usage")
    result = checker.check("Use os.path.join to build paths")
    print(f"Verdict: {result.verdict.value}")
    print(f"Warnings: {len(result.warnings)}")
    if result.warnings:
        for w in result.warnings:
            print(f"  - {w.api}: {w.suggestion}")
    print()

    # Test 2: Modern pathlib
    print("Test 2: Modern pathlib usage")
    result = checker.check("Use pathlib.Path for path operations")
    print(f"Verdict: {result.verdict.value}")
    print(f"Warnings: {len(result.warnings)}")
    print()

    # Test 3: XMLHttpRequest
    print("Test 3: Deprecated XMLHttpRequest")
    result = checker.check("Use XMLHttpRequest for AJAX")
    print(f"Verdict: {result.verdict.value}")
    print(f"Warnings: {len(result.warnings)}")
    if result.warnings:
        for w in result.warnings:
            print(f"  - {w.api}: {w.suggestion}")
    print()

    # Test 4: Modern fetch
    print("Test 4: Modern fetch API")
    result = checker.check("Use fetch() for HTTP requests")
    print(f"Verdict: {result.verdict.value}")
    print(f"Warnings: {len(result.warnings)}")
    print()

    print("=== Self-Test Complete ===")
