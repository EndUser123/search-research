#!/usr/bin/env python3
"""
verification_metrics.py - Verification gate telemetry collection

TASK-010: Monitoring & Iteration

SECURITY FIX (SEC-003):
- Metrics log created with owner-only permissions (0600)
- Sensitive data sanitized before writing (commands, paths, content)
- Data minimization: Only tier, blocked, timestamp, confidence, category

Metrics collected:
- Blocked claims by type (component vs e2e)
- False positive rate
- Verification tier distribution
- Workflow success rates
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# SEC-003: Owner-only permissions (0600 = read/write for owner only)
SECURE_PERMISSIONS = 0o600

# Default metrics file location
HOOKS_DIR = Path(__file__).resolve().parent.parent
DEFAULT_METRICS_FILE = HOOKS_DIR / "state" / "logs" / "verification_gate_metrics.jsonl"

# Fields to preserve after sanitization (SEC-003)
SAFE_FIELDS = {
    "tier",           # Verification tier (tier1_component, tier2_e2e, tier3_orchestration)
    "blocked",        # Whether the claim was blocked (True/False)
    "confidence",     # Detection confidence score (0.0-1.0)
    "category",       # Claim category (completion_claim, stance_verification, etc.)
    "reason",         # Generic reason (sanitized)
    "timestamp",      # ISO timestamp
}

# Fields to remove (SEC-003: Sensitive data)
SENSITIVE_FIELDS = {
    "command",        # Bash commands (may contain paths, secrets)
    "file_path",      # File paths (user directory structure)
    "response_text",  # User response content (may contain secrets)
    "user_content",   # Any user-provided content
    "session_id",     # Session identifiers
    "terminal_id",    # Terminal identifiers
}


def sanitize_metric_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a metric entry by removing sensitive data (SEC-003).

    Args:
        entry: Raw metric entry with potentially sensitive fields

    Returns:
        Sanitized entry with only safe fields preserved

    Example:
        >>> entry = {
        ...     "tier": "tier1_component",
        ...     "blocked": True,
        ...     "command": "python P:/secret/script.py",
        ...     "file_path": "P:/user/config.py"
        ... }
        >>> sanitize_metric_entry(entry)
        {"tier": "tier1_component", "blocked": True, "timestamp": "..."}
    """
    sanitized = {}

    for key, value in entry.items():
        if key in SENSITIVE_FIELDS:
            # Skip sensitive fields entirely
            continue
        elif key in SAFE_FIELDS:
            # Preserve safe fields
            sanitized[key] = value
        else:
            # Unknown fields: skip (fail-closed for security)
            continue

    # Ensure timestamp is present
    if "timestamp" not in sanitized:
        sanitized["timestamp"] = datetime.now().isoformat()

    return sanitized


class VerificationMetrics:
    """Verification gate metrics collector with security fixes (SEC-003)."""

    def __init__(self, metrics_file: str | Path | None = None):
        """Initialize metrics collector.

        Args:
            metrics_file: Path to metrics JSONL file (default: DEFAULT_METRICS_FILE)
        """
        self.metrics_file = Path(metrics_file or DEFAULT_METRICS_FILE)

        # Ensure parent directory exists
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        # SEC-003: Set secure permissions if file doesn't exist
        if not self.metrics_file.exists():
            self.metrics_file.touch()
            _set_secure_permissions(self.metrics_file)

    def record_event(
        self,
        tier: str,
        blocked: bool,
        confidence: float,
        category: str = "",
        reason: str = "",
        **kwargs: Any
    ) -> None:
        """Record a verification event (sanitized before writing).

        Args:
            tier: Verification tier (tier1_component, tier2_e2e, tier3_orchestration)
            blocked: Whether the claim was blocked
            confidence: Detection confidence score (0.0-1.0)
            category: Claim category (completion_claim, stance_verification, etc.)
            reason: Generic reason for blocking/allowing
            **kwargs: Additional fields (will be sanitized)

        Example:
            >>> metrics = VerificationMetrics()
            >>> metrics.record_event(
            ...     tier="tier1_component",
            ...     blocked=True,
            ...     confidence=0.95,
            ...     category="completion_claim"
            ... )
        """
        # Build entry with all provided data
        entry = {
            "tier": tier,
            "blocked": blocked,
            "confidence": confidence,
            "category": category,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            **kwargs  # Include additional fields (will be sanitized)
        }

        # SEC-003: Sanitize entry before writing
        sanitized = sanitize_metric_entry(entry)

        # Write to JSONL file (one JSON per line)
        with open(self.metrics_file, "a", encoding="utf-8") as f:
            json.dump(sanitized, f)
            f.write("\n")

        # SEC-003: Ensure permissions remain secure
        _set_secure_permissions(self.metrics_file)


def collect_verification_metric(
    tier: str,
    blocked: bool,
    confidence: float,
    category: str = "",
    reason: str = "",
    **kwargs: Any
) -> None:
    """Helper function to collect a verification metric.

    This is the main entry point for hooks to record metrics.

    Args:
        tier: Verification tier (tier1_component, tier2_e2e, tier3_orchestration)
        blocked: Whether the claim was blocked
        confidence: Detection confidence score (0.0-1.0)
        category: Claim category (completion_claim, stance_verification, etc.)
        reason: Generic reason for blocking/allowing
        **kwargs: Additional fields (will be sanitized)

    Example:
        >>> collect_verification_metric(
        ...     tier="tier1_component",
        ...     blocked=True,
        ...     confidence=0.95,
        ...     category="completion_claim"
        ... )
    """
    collector = VerificationMetrics()
    collector.record_event(
        tier=tier,
        blocked=blocked,
        confidence=confidence,
        category=category,
        reason=reason,
        **kwargs
    )


def get_metrics_summary(metrics_file: str | Path | None = None) -> dict[str, Any]:
    """Generate summary statistics from metrics file.

    Args:
        metrics_file: Path to metrics JSONL file (default: DEFAULT_METRICS_FILE)

    Returns:
        Dictionary with summary statistics:
        {
            "total_events": int,
            "blocked_count": int,
            "allowed_count": int,
            "block_rate": float,
            "by_tier": {...},
            "confidence_distribution": {...}
        }

    Example:
        >>> summary = get_metrics_summary()
        >>> print(f"Block rate: {summary['block_rate']:.1%}")
    """
    metrics_file = Path(metrics_file or DEFAULT_METRICS_FILE)

    if not metrics_file.exists():
        return {
            "total_events": 0,
            "blocked_count": 0,
            "allowed_count": 0,
            "block_rate": 0.0,
            "by_tier": {},
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0}
        }

    events = []
    with open(metrics_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # Skip malformed lines

    total = len(events)
    blocked = sum(1 for e in events if e.get("blocked", False))
    allowed = total - blocked

    # Breakdown by tier
    by_tier: dict[str, dict[str, Any]] = {}
    for event in events:
        tier = event.get("tier", "unknown")
        if tier not in by_tier:
            by_tier[tier] = {"count": 0, "blocked": 0}
        by_tier[tier]["count"] += 1
        if event.get("blocked", False):
            by_tier[tier]["blocked"] += 1

    # Confidence distribution
    confidence_dist = {"high": 0, "medium": 0, "low": 0}
    for event in events:
        conf = event.get("confidence", 0.0)
        if conf >= 0.8:
            confidence_dist["high"] += 1
        elif conf >= 0.5:
            confidence_dist["medium"] += 1
        else:
            confidence_dist["low"] += 1

    return {
        "total_events": total,
        "blocked_count": blocked,
        "allowed_count": allowed,
        "block_rate": blocked / total if total > 0 else 0.0,
        "by_tier": by_tier,
        "confidence_distribution": confidence_dist
    }


def _set_secure_permissions(file_path: Path) -> None:
    """Set owner-only permissions on file (SEC-003).

    Args:
        file_path: Path to file to secure

    Note:
        On Windows, this uses os.chmod() which may not enforce
        Unix-style permissions. On Unix-like systems, this sets
        mode to 0600 (read/write for owner only).
    """
    try:
        # Set owner-only permissions (0600)
        file_path.chmod(SECURE_PERMISSIONS)
    except OSError:
        # On Windows or systems without chmod, fail silently
        # The file will still be created, just without Unix permissions
        pass


if __name__ == "__main__":
    # CLI interface for manual testing
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        summary = get_metrics_summary()
        print(json.dumps(summary, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Record a test event
        collect_verification_metric(
            tier="tier1_component",
            blocked=True,
            confidence=0.95,
            category="test_event"
        )
        print("Test metric recorded")
    else:
        print("Usage: python verification_metrics.py [summary|test]")
        print("  summary  - Show metrics summary")
        print("  test     - Record a test metric")
