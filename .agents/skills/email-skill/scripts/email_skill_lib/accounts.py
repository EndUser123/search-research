"""Account configuration for email-skill.

Hardcoded list of operator accounts. v1.0 intentionally avoids a config
file — three accounts, all under operator control, no need for a config
parser yet. If the operator adds a 4th account or wants to disable one,
edit this file.

Each account dict has:
    name:     short identifier used in CLI flags, defer/ignore state
              keys ("account:thread_id"), and the himalaya -a flag.
    email:    full email address.
    provider: himalaya backend hint ("gmail", "outlook", "imap").
              Used for display in `accounts` output and as a fallback
              when derive_provider() is called with a non-email string.
"""

from __future__ import annotations

ACCOUNTS = [
    {
        "name": "a-hominidae",
        "email": "a.hominidae@gmail.com",
        "provider": "gmail",
    },
    {
        "name": "troup-hominidae",
        "email": "troup.hominidae@gmail.com",
        "provider": "gmail",
    },
    {
        "name": "brsthomson",
        "email": "brsthomson@hotmail.com",
        "provider": "outlook",
    },
]


def derive_provider(email: str) -> str:
    """Derive provider type from email domain.

    Mapping:
        gmail / googlemail -> "gmail"
        outlook / hotmail / live / msn -> "outlook"
        everything else -> "imap"

    Returns "imap" if the input is not a valid email (no '@' separator).
    """
    if "@" not in email:
        return "imap"
    domain = email.split("@", 1)[1].lower()
    if "gmail" in domain or "googlemail" in domain:
        return "gmail"
    if (
        "outlook" in domain
        or "hotmail" in domain
        or "live" in domain
        or "msn" in domain
    ):
        return "outlook"
    return "imap"


def get_account(name: str) -> dict | None:
    """Look up an account by its short name. Returns None if not found."""
    for a in ACCOUNTS:
        if a["name"] == name:
            return a
    return None