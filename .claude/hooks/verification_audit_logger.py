#!/usr/bin/env python3
"""
Verification Audit Logger (SEC-005)
====================================

Logs verification bypass events for security monitoring.

When UNVERIFIED_STANCE_ENABLED=false or other verification is disabled,
this module logs the bypass event with:
- Timestamp
- Process ID
- Security impact level
- Reason for bypass

This provides security monitoring for verification system bypasses.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
LOG_DIR = HOOKS_DIR / "state" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_LOG_FILE = LOG_DIR / "verification_bypass.log"


class VerificationAuditLogger:
    """Audit logger for verification bypass events."""

    def __init__(self, log_file: Path | None = None):
        """Initialize audit logger.

        Args:
            log_file: Path to audit log file (defaults to verification_bypass.log)
        """
        self.log_file = log_file or AUDIT_LOG_FILE
        self._ensure_log_directory()

    def _ensure_log_directory(self) -> None:
        """Ensure log directory exists."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_bypass(
        self,
        reason: str,
        security_impact: str = "HIGH",
        action: str = "verification_bypass",
        user: str = "system"
    ) -> None:
        """Log a verification bypass event.

        Args:
            reason: Reason for bypass (e.g., "UNVERIFIED_STANCE_ENABLED=false")
            security_impact: Security impact level (HIGH/MEDIUM/LOW)
            action: Action type (verification_bypass, hook_disabled, etc.)
            user: User or system responsible (defaults to "system")
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "pid": os.getpid(),
            "security_impact": security_impact,
            "reason": reason,
            "action": action,
            "user": user
        }

        try:
            # Append to audit log
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=True) + "\n")

            # Also log to stderr for immediate visibility (bypass won't block)
            print(
                f"AUDIT: Verification bypass logged: {reason} "
                f"(impact={security_impact}, pid={os.getpid()})",
                file=sys.stderr
            )
        except OSError as e:
            # Don't fail if logging fails
            print(f"WARNING: Failed to write audit log: {e}", file=sys.stderr)

    def check_verification_status(self) -> bool:
        """Check if verification is currently enabled.

        Returns:
            True if verification is enabled, False if bypassed
        """
        unverified_stance_enabled = (
            os.environ.get("UNVERIFIED_STANCE_ENABLED", "true").lower() == "true"
        )

        e2e_verification_enabled = (
            os.environ.get("E2E_VERIFICATION_ENABLED", "false").lower() == "true"
        )

        if not unverified_stance_enabled:
            self.log_bypass(
                reason="UNVERIFIED_STANCE_ENABLED=false",
                security_impact="HIGH",
                action="unverified_stance_disabled"
            )
            return False

        return True

    def get_recent_bypasses(self, limit: int = 10) -> list[dict]:
        """Get recent bypass events from audit log.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of bypass event dictionaries (most recent first)
        """
        if not self.log_file.exists():
            return []

        bypasses = []
        try:
            with open(self.log_file, encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        bypasses.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue

            # Return most recent first
            bypasses.reverse()
            return bypasses[:limit]
        except OSError:
            return []

    def analyze_bypass_patterns(self) -> dict:
        """Analyze bypass patterns from audit log.

        Returns:
            Dictionary with bypass statistics:
            - total_bypasses: Total number of bypass events
            - unique_reasons: Set of unique bypass reasons
            - high_impact_count: Number of HIGH impact events
            - most_common_reason: Most frequent bypass reason
        """
        bypasses = self.get_recent_bypasses(limit=1000)

        if not bypasses:
            return {
                "total_bypasses": 0,
                "unique_reasons": set(),
                "high_impact_count": 0,
                "most_common_reason": None
            }

        reason_counts = {}
        high_impact_count = 0

        for bypass in bypasses:
            reason = bypass.get("reason", "unknown")
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

            if bypass.get("security_impact") == "HIGH":
                high_impact_count += 1

        most_common_reason = max(reason_counts, key=reason_counts.get) if reason_counts else None

        return {
            "total_bypasses": len(bypasses),
            "unique_reasons": set(reason_counts.keys()),
            "high_impact_count": high_impact_count,
            "most_common_reason": most_common_reason,
            "reason_counts": reason_counts
        }


# Singleton instance
_audit_logger = None


def get_audit_logger() -> VerificationAuditLogger:
    """Get singleton audit logger instance.

    Returns:
        VerificationAuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = VerificationAuditLogger()
    return _audit_logger


def log_verification_bypass(
    reason: str,
    security_impact: str = "HIGH",
    action: str = "verification_bypass",
    user: str = "system"
) -> None:
    """Log a verification bypass event (convenience function).

    Args:
        reason: Reason for bypass
        security_impact: Security impact level (HIGH/MEDIUM/LOW)
        action: Action type
        user: User or system responsible
    """
    logger = get_audit_logger()
    logger.log_bypass(
        reason=reason,
        security_impact=security_impact,
        action=action,
        user=user
    )


def check_verification_enabled() -> bool:
    """Check if verification is enabled and log bypass if not.

    Returns:
        True if verification is enabled, False if bypassed
    """
    logger = get_audit_logger()
    return logger.check_verification_status()


if __name__ == "__main__":
    # CLI interface for testing
    import argparse

    parser = argparse.ArgumentParser(description="Verification audit logger")
    parser.add_argument("--check", action="store_true", help="Check verification status")
    parser.add_argument("--recent", type=int, default=10, help="Show recent bypasses")
    parser.add_argument("--analyze", action="store_true", help="Analyze bypass patterns")
    parser.add_argument("--log", type=str, help="Log a bypass event (reason)")
    parser.add_argument("--impact", type=str, default="HIGH", help="Security impact level")

    args = parser.parse_args()

    if args.check:
        if check_verification_enabled():
            print("✅ Verification is ENABLED")
        else:
            print("⚠️  Verification is DISABLED (bypass logged)")

    elif args.recent:
        bypasses = get_audit_logger().get_recent_bypasses(limit=args.recent)
        print(f"\nRecent {len(bypasses)} bypass events:")
        for bypass in bypasses:
            print(f"  [{bypass['timestamp']}] {bypass['reason']} (impact={bypass['security_impact']})")

    elif args.analyze:
        patterns = get_audit_logger().analyze_bypass_patterns()
        print("\nBypass pattern analysis:")
        print(f"  Total bypasses: {patterns['total_bypasses']}")
        print(f"  High impact: {patterns['high_impact_count']}")
        print(f"  Unique reasons: {len(patterns['unique_reasons'])}")
        print(f"  Most common: {patterns['most_common_reason']}")
        if patterns.get('reason_counts'):
            print("\n  Reason breakdown:")
            for reason, count in patterns['reason_counts'].items():
                print(f"    {reason}: {count}")

    elif args.log:
        log_verification_bypass(reason=args.log, security_impact=args.impact)
        print(f"✅ Logged bypass: {args.log} (impact={args.impact})")

    else:
        parser.print_help()
