"""Type stubs for notification_queue module."""

from typing import Any, Dict, List

Notification = Dict[str, Any]

def add_notification(
    notification_type: str,
    message: str,
    source: str = "unknown",
    priority: int = 1,
    session_id: str = "",
) -> None: ...

def get_notifications(session_id: str = "") -> List[Notification]: ...

def get_display_text(session_id: str = "") -> str: ...

def clear_by_type(level: str, notification_type: str = "") -> int: ...

def clear_all() -> int: ...

def clear_by_id(notification_id: str) -> bool: ...

def _cleanup_old() -> int: ...
