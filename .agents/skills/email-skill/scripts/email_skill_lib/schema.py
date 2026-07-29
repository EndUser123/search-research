"""JSON envelope constants for email-skill CLI output.

Every --json output from email-skill is wrapped in a versioned envelope so
consumers can detect schema changes. The envelope is intentionally flat:
schema_version + command + the command's own payload.

Consumers that parse email-skill JSON should:
    1. Check schema_version matches the version they were written against.
    2. Dispatch on `command` to know which payload fields to expect.
    3. Ignore unknown fields (forward compat).
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "1.0"


def make_envelope(command: str, **kwargs: Any) -> dict:
    """Create a standard JSON envelope for CLI output.

    Reserved keys (schema_version, command) are always first. Any kwargs
    passed in become the payload. Callers should NOT pass 'command' or
    'schema_version' as kwargs — they would silently overwrite.

    Example:
        make_envelope("scan-inbox", items=[...], cache_hit=True)
        -> {"schema_version": "1.0", "command": "scan-inbox",
            "items": [...], "cache_hit": True}
    """
    envelope: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "command": command,
    }
    envelope.update(kwargs)
    return envelope