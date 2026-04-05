#!/usr/bin/env python3
"""
PII Scanner - Credential and Personal Data Detection
====================================================

Fast scanner for detecting Personally Identifiable Information (PII)
and credentials in responses before they reach the user.

Based on LLM Guard PII scanning patterns:
https://github.com/protectai/llm-guard

Patterns detected:
- API keys (OpenAI, Anthropic, GitHub, AWS, etc.)
- Tokens and Bearer strings
- Passwords and secrets
- Email addresses
- IP addresses (optional)
- SSN/SIN numbers
- Credit card numbers

Performance: ~1ms per scan
"""

import re

from .base_scanner import BaseScanner, ScanResult, ScanStatus


class PIIScanner(BaseScanner):
    """
    Fast PII and credential detection scanner.

    Detects patterns that should NOT appear in model responses:
    - API keys and tokens
    - Passwords and secrets
    - Personal identifiers (emails, SSNs, etc.)
    """

    # PII patterns with their regex and descriptions
    PATTERNS: list[tuple[str, str, str]] = [
        # API Keys
        (r'(sk-|pk-)[a-zA-Z0-9]{32,}', 'HIGH', 'OpenAI API key'),
        (r'(sk-ant-)[a-zA-Z0-9\-_]{30,}', 'HIGH', 'Anthropic API key'),
        (r'ghp_[a-zA-Z0-9]{36,}', 'HIGH', 'GitHub Personal Access Token'),
        (r'gho_[a-zA-Z0-9]{36,}', 'HIGH', 'GitHub OAuth token'),
        (r'ghu_[a-zA-Z0-9]{36,}', 'HIGH', 'GitHub user token'),
        (r'AKIA[0-9A-Z]{16}', 'HIGH', 'AWS Access Key ID'),
        (r'[0-9a-zA-Z/+]{40}', 'MEDIUM', 'AWS Secret Access Key (possible)'),
        (r'xox[baprs]-[0-9]{10,12}-[0-9a-zA-Z]{24,}', 'HIGH', 'Slack token'),
        (r'AKFV[0-9A-Z]{20}', 'HIGH', 'Aliyun Access Key'),

        # Bearer tokens and JWT
        (r'Bearer [a-zA-Z0-9\-._~+/]+=*', 'HIGH', 'Bearer token'),
        (r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', 'MEDIUM', 'JWT token'),

        # Generic token patterns
        (r'"?token"?\s*[:=]\s*["\']?[a-zA-Z0-9\-._~+/]{20,}["\']?', 'HIGH', 'Generic token'),
        (r'"?api_?key"?\s*[:=]\s*["\']?[a-zA-Z0-9\-._~+/]{20,}["\']?', 'HIGH', 'Generic API key'),
        (r'"?secret"?\s*[:=]\s*["\']?[a-zA-Z0-9\-._~+/]{20,}["\']?', 'HIGH', 'Generic secret'),

        # Passwords (common assignment patterns)
        (r'"?password"?\s*[:=]\s*["\']?[^\s"\']{8,}["\']?', 'HIGH', 'Password'),
        (r'"?pass"?\s*[:=]\s*["\']?[^\s"\']{8,}["\']?', 'HIGH', 'Password (short form)'),
        (r'"?passwd"?\s*[:=]\s*["\']?[^\s"\']{8,}["\']?', 'HIGH', 'Password (alt)'),

        # Email addresses
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'LOW', 'Email address'),

        # IP addresses
        (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', 'LOW', 'IP address'),

        # SSN/SIN (US Social Security, Canada SIN)
        (r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b', 'MEDIUM', 'SSN/SIN pattern'),

        # Credit card numbers (Luhn algorithm would be more precise)
        (r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9]{2})[0-9]{12})\b', 'HIGH', 'Credit card number'),

        # Database connection strings (contains credentials)
        (r'(?:postgresql|mysql|mongodb|redis)://[^\s\'"]+:[^\s\'"]+@[^\s\'"]+', 'HIGH', 'Database connection string'),

        # Private keys (beginnings of PEM files)
        (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', 'HIGH', 'Private key PEM'),
    ]

    # Compile patterns for performance
    _COMPILED_PATTERNS = [
        (re.compile(pattern, re.IGNORECASE), severity, description)
        for pattern, severity, description in PATTERNS
    ]

    def __init__(self, enabled: bool = True, exclude_low_severity: bool = True):
        """
        Initialize PII scanner.

        Args:
            enabled: Whether scanner is active
            exclude_low_severity: Skip LOW severity patterns (emails, IPs)
        """
        super().__init__(enabled)
        self.exclude_low_severity = exclude_low_severity

    def scan(self, text: str, context: dict = None) -> ScanResult:
        """
        Scan text for PII and credentials.

        Args:
            text: The text to scan
            context: Optional context (not used for PII scanning)

        Returns:
            ScanResult with validation outcome
        """
        if not self.enabled:
            return ScanResult(ScanStatus.SKIP, self.name)

        for pattern, severity, description in self._COMPILED_PATTERNS:
            # Skip LOW severity if configured
            if self.exclude_low_severity and severity == "LOW":
                continue

            match = pattern.search(text)
            if match:
                matched_text = match.group(0)

                # Truncate long matches for readability
                display_text = matched_text
                if len(display_text) > 50:
                    display_text = display_text[:47] + "..."

                return ScanResult(
                    status=ScanStatus.FAIL,
                    scanner_name=self.name,
                    matched_text=display_text,
                    reason=f"{description} detected in response",
                    severity=severity,
                    suggestion=(
                        "Remove this credential/PII from the response. "
                        "Use environment variables or secret management."
                    ),
                )

        return ScanResult(ScanStatus.PASS, self.name)

    def get_pattern_count(self) -> int:
        """Get number of detection patterns."""
        return len(self.PATTERNS)


# Convenience function for quick scanning
def scan_for_pii(text: str, exclude_low: bool = True) -> bool:
    """
    Quick check if text contains PII/credentials.

    Args:
        text: Text to check
        exclude_low: Exclude LOW severity patterns (emails, IPs)

    Returns:
        True if PII/credentials detected
    """
    scanner = PIIScanner(exclude_low_severity=exclude_low)
    result = scanner.scan(text)
    return not result.is_valid()
