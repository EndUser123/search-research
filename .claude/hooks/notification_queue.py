#!/usr/bin/env python3
from __future__ import annotations

"""
Notification Queue System for Claude Code

Stores notifications as JSON in ~/.claude/notifications.json
Supports multiple notification types with selective clearing.
Centralized state management prevents re-adding recently cleared notifications.

LIMITATION: This module uses JSON file storage WITHOUT file locking.
Concurrent access from multiple terminals may cause race conditions.
This is acceptable for single-terminal solo development workflows.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

NOTIFICATION_FILE = Path.home() / ".claude" / "notifications.json"
CLEARED_STATE_FILE = Path.home() / ".claude" / ".notification_state.json"

# Cooldown period: don't re-add a notification type if cleared within this time
CLEARED_COOLDOWN_SECONDS = 60


class Notification(TypedDict):
    type: str
    message: str
    timestamp: str
    source: str
    priority: int  # 0=low, 1=normal, 2=high
    session_id: str  # Session that created this notification


def _get_cleared_time(notification_type: str) -> datetime | None:
    """Get the timestamp when a notification type was last cleared.

    Args:
        notification_type: Type of notification to check

    Returns:
        Datetime when cleared, or None if never cleared or state expired
    """
    if not CLEARED_STATE_FILE.exists():
        return None

    try:
        state = json.loads(CLEARED_STATE_FILE.read_text())
        if notification_type not in state:
            return None

        cleared_str = state[notification_type]
        cleared_time = datetime.fromisoformat(cleared_str)

        # Clean up expired entries (older than cooldown)
        if (datetime.now(UTC) - cleared_time).total_seconds() > CLEARED_COOLDOWN_SECONDS:
            del state[notification_type]
            CLEARED_STATE_FILE.write_text(json.dumps(state))
            return None

        return cleared_time
    except (json.JSONDecodeError, ValueError, Exception):
        return None


def _set_cleared_time(notification_type: str, cleared_time: datetime) -> None:
    """Record when a notification type was cleared.

    Args:
        notification_type: Type of notification that was cleared
        cleared_time: Timestamp when it was cleared
    """
    CLEARED_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Read existing state
    state: dict[str, str] = {}
    if CLEARED_STATE_FILE.exists():
        try:
            state = json.loads(CLEARED_STATE_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            state = {}

    # Update with new cleared time
    state[notification_type] = cleared_time.isoformat()

    # Clean up expired entries
    current_time = datetime.now(UTC)
    expired_types = [
        t for t, ts in state.items()
        if (current_time - datetime.fromisoformat(ts)).total_seconds() > CLEARED_COOLDOWN_SECONDS
    ]
    for t in expired_types:
        del state[t]

    CLEARED_STATE_FILE.write_text(json.dumps(state))


def mark_cleared(notification_type: str) -> None:
    """Mark a notification type as cleared (prevents re-add within cooldown).

    This should be called when a command explicitly clears its notification.
    Example: When `/learn` runs, it clears the 'lesson' notification and calls this.

    Args:
        notification_type: Type of notification that was cleared
    """
    _set_cleared_time(notification_type, datetime.now(UTC))


def add_notification(
    notification_type: str,
    message: str,
    source: str = "unknown",
    priority: int = 1,
    session_id: str = "",
) -> None:
    """Add a notification to the queue.

    Args:
        notification_type: Type of notification (lesson, commit, info, etc.)
        message: Display message for statusline
        source: Source identifier (retrospective, commit_reminder, etc.)
        priority: 0=low, 1=normal, 2=high
        session_id: Session UUID (empty string = show in all terminals)

    Note:
        If this notification type was cleared within the last 60 seconds,
        the notification will NOT be added (cooldown period).
    """
    # Check if recently cleared - skip adding during cooldown
    cleared_time = _get_cleared_time(notification_type)
    if cleared_time is not None:
        # Recently cleared, skip adding
        return

    NOTIFICATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Read existing notifications
    notifications: list[Notification] = []
    if NOTIFICATION_FILE.exists():
        try:
            notifications = json.loads(NOTIFICATION_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            notifications = []

    # Check for duplicate (same type and source) - replace if exists
    notifications = [
        n for n in notifications
        if not (n["type"] == notification_type and n["source"] == source)
    ]

    # Add new notification
    notification: Notification = {
        "type": notification_type,
        "message": message,
        "timestamp": datetime.now(UTC).isoformat(),
        "source": source,
        "priority": priority,
        "session_id": session_id,
    }
    notifications.append(notification)

    # Write back
    NOTIFICATION_FILE.write_text(json.dumps(notifications, indent=2))


def get_notifications(session_id: str = "") -> list[Notification]:
    """Get notifications, filtered by session_id, sorted by priority then timestamp.

    Args:
        session_id: Current session UUID. Empty string = show only global notifications.
                    Specific ID = show global + this session's notifications.

    Returns:
        Filtered and sorted notifications.
    """
    if not NOTIFICATION_FILE.exists():
        return []

    try:
        all_notifications: list[Notification] = json.loads(NOTIFICATION_FILE.read_text())

        # Filter: show global (empty session_id) OR this session's notifications
        filtered = [
            n for n in all_notifications
            if n.get("session_id", "") == ""  # Global
            or n.get("session_id", "") == session_id  # This session
        ]

        # Sort by priority (desc) then timestamp (asc - oldest first)
        return sorted(
            filtered,
            key=lambda n: (-n["priority"], n["timestamp"])
        )
    except (json.JSONDecodeError, Exception):
        return []


def get_display_text(session_id: str = "") -> str:
    """Get formatted text for statusline display.

    Args:
        session_id: Current session UUID. Filters to show only global + this session's notifications.

    Returns:
        Highest priority notification message, or empty string.
    """
    notifications = get_notifications(session_id)
    if not notifications:
        return ""

    # Show highest priority notification (session-filtered)
    top = notifications[0]
    return top["message"]


def clear_by_type(notification_type: str, source: str | None = None, session_id: str | None = None) -> int:
    """Clear notifications by type, source, and optionally session_id (terminal_id).

    Also marks the notification type as cleared to prevent re-add within cooldown.

    Args:
        notification_type: Type of notification to clear
        source: Optional source filter
        session_id: Optional session_id filter (used for terminal_id scoping)

    Returns count of notifications cleared.
    """
    return _clear_by_type_internal(notification_type, source, session_id, mark=True)


def clear_all() -> int:
    """Clear all notifications. Returns count cleared.

    Note: This does NOT mark types as cleared (unlike clear_by_type).
    Also clears the cleared-state file for clean test environment.
    """
    count = 0
    if NOTIFICATION_FILE.exists():
        try:
            notifications = json.loads(NOTIFICATION_FILE.read_text())
            NOTIFICATION_FILE.unlink()
            count = len(notifications)
        except Exception:
            pass

    # Also clear the state file for clean environment
    if CLEARED_STATE_FILE.exists():
        try:
            CLEARED_STATE_FILE.unlink()
        except Exception:
            pass

    return count


def _clear_by_type_internal(notification_type: str, source: str | None = None, session_id: str | None = None, mark: bool = True) -> int:
    """Internal implementation of clear_by_type.

    Args:
        notification_type: Type of notification to clear
        source: Optional source filter
        session_id: Optional session_id filter
        mark: If True, mark as cleared to prevent re-add within cooldown

    Returns count of notifications cleared.
    """
    if not NOTIFICATION_FILE.exists():
        return 0

    try:
        notifications: list[Notification] = json.loads(NOTIFICATION_FILE.read_text())

        original_count = len(notifications)

        # Filter out matching notifications
        filtered = []
        for n in notifications:
            # Check if notification matches clear criteria
            type_match = n["type"] == notification_type
            source_match = not source or n["source"] == source
            session_match = not session_id or n["session_id"] == session_id

            # Keep notification if it doesn't match ALL criteria
            if not (type_match and source_match and session_match):
                filtered.append(n)

        notifications = filtered
        cleared = original_count - len(notifications)

        if notifications:
            NOTIFICATION_FILE.write_text(json.dumps(notifications, indent=2))
        else:
            NOTIFICATION_FILE.unlink()

        # Mark as cleared to prevent re-add within cooldown (if requested)
        if cleared > 0 and mark:
            mark_cleared(notification_type)

        return cleared
    except (json.JSONDecodeError, Exception):
        return 0


def list_notifications() -> str:
    """Return formatted list of all notifications."""
    notifications = get_notifications()
    if not notifications:
        return "No notifications"

    lines = []
    for n in notifications:
        priority_icon = {0: "○", 1: "●", 2: "■"}.get(n["priority"], "?")
        lines.append(f"{priority_icon} [{n['type']}] {n['message']}")
    return "\n".join(lines)
