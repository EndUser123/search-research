"""Shared secret-matching engine for AAR detectors (Phase 2).

This module is the SOLE authoritative implementation of secret-pattern
detection in the AAR skill. Per Phase 2 design, no other module duplicates
the regex logic; source-specific adapters call into this engine.

Design contract
---------------
- The engine accepts ``text`` plus ``source_metadata`` (which event the
  text came from, what role, etc.).
- It returns a list of ``SecretFinding`` dataclass instances.
- Each finding carries:
  - a **redacted fingerprint** (first 4 chars + ``…`` + last 2 chars +
    sha256-prefix-8) — sufficient for deduplication, never the full value
  - the source classification (USER_PASTED / TOOL_RETURNED /
    ASSISTANT_REPEATED / WRITTEN_TO_FILE / SOURCE_INSUFFICIENT)
  - the event index and role
- The full secret value is NEVER serialized into the finding. Outputs are
  safe to write to artifacts, logs, or LLM context.
- Known placeholders and synthetic test markers are suppressed via the
  ``_PLACEHOLDER_RE`` regex.

Source classification rules
---------------------------
The engine does NOT infer provenance on its own. The caller passes a
``source_kind`` hint based on which adapter is calling:
- ``user_content`` adapter → ``USER_PASTED``
- ``assistant_content`` adapter → ``ASSISTANT_REPEATED``
- ``tool_result`` adapter → ``TOOL_RETURNED``
- ``tool_call_args`` adapter → ``WRITTEN_TO_FILE`` (when the call writes a file)
  or ``SOURCE_INSUFFICIENT`` (when the call structure is ambiguous)
- ``file_diff`` adapter → ``WRITTEN_TO_FILE``

Adding a new credential form
----------------------------
Extend ``SECRET_PATTERN`` (the master regex). The pattern names are stable
identifiers used in fingerprints.

Non-goals
---------
- The engine does NOT rotate, validate, or report credentials externally.
- The engine does NOT distinguish "live" vs "expired" credentials — that
  requires external verification and is out of scope.
- The engine does NOT encrypt or store the full value anywhere.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Pattern


class SecretSource(str, Enum):
    """Where the secret-bearing text came from."""

    USER_PASTED = "USER_PASTED"
    TOOL_RETURNED = "TOOL_RETURNED"
    ASSISTANT_REPEATED = "ASSISTANT_REPEATED"
    WRITTEN_TO_FILE = "WRITTEN_TO_FILE"
    SOURCE_INSUFFICIENT = "SOURCE_INSUFFICIENT"


# Master credential regex. Order matters for stable group names.
# Each alternative is a credential form. Adding a new form requires:
# (1) adding the pattern here, (2) updating tests, (3) bumping version.
SECRET_PATTERN: Pattern[str] = re.compile(
    r"(?P<SK_OPENAI>sk-[a-zA-Z0-9]{20,})"
    r"|(?P<AWS_AKIA>AKIA[A-Z0-9]{16})"
    r"|(?P<GITHUB_TOKEN>ghp_[a-zA-Z0-9]{36})"
    r"|(?P<SLACK_TOKEN>xox[bpoa]-[a-zA-Z0-9-]{10,})"
    r"|(?P<GCP_TOKEN>AIza[a-zA-Z0-9_-]{35})"
    r"|(?P<GENERIC_KEY>(?:[A-Z_]{3,}_(?:API_KEY|SECRET|TOKEN))\s*=\s*[\"']?[A-Za-z0-9/+=]{16,}[\"']?)"
    r"|(?P<BEARER>Bearer\s+[a-zA-Z0-9._-]{20,})"
    r"|(?P<PASSWORD_ASSIGN>password\s*=\s*[\"']?[^\s\"']{8,}[\"']?)",
    re.IGNORECASE,
)


# Placeholders, examples, and synthetic test markers that should NOT fire.
# If a match is fully contained within one of these patterns, suppress it.
_PLACEHOLDER_RE: Pattern[str] = re.compile(
    r"(?:sk-(?:test|example|placeholder|dummy|sample|REDACTED)[a-zA-Z0-9-]*)"
    r"|(?:YOUR_API_KEY|EXAMPLE_KEY|TEST_KEY|PLACEHOLDER|XXXX|<token>)"
    r"|(?:sk-test[a-zA-Z0-9]{16,})"  # test fixtures use sk-test prefix
    r"|(?:AKIA(?:TEST|EXAMPLE|PLACEHOLDER)[A-Z0-9]*)"
    r"|(?:ghp_(?:test|example|placeholder)[a-zA-Z0-9]*)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SecretFinding:
    """One detected secret occurrence.

    The ``fingerprint`` is the ONLY representation of the secret value
    that ever leaves this engine. It is structured as:
    ``<kind>:<first4>…<last2>#<sha256[:8]>``
    """

    kind: str               # e.g. "SK_OPENAI", "AWS_AKIA"
    source_kind: SecretSource
    fingerprint: str        # redacted representation
    event_index: int | None = None
    event_role: str | None = None  # "user", "assistant", "tool_result", etc.
    raw_length: int = 0     # length of matched value (for entropy signal)


@dataclass
class ScanResult:
    """All findings from a single scan pass."""

    findings: list[SecretFinding] = field(default_factory=list)

    @property
    def deduplicated(self) -> list[SecretFinding]:
        """Return one finding per unique (kind, fingerprint) pair.

        When the same secret appears multiple times in the same source,
        we keep the first occurrence and drop subsequent duplicates.
        """
        seen: set[tuple[str, str]] = set()
        out: list[SecretFinding] = []
        for f in self.findings:
            key = (f.kind, f.fingerprint)
            if key in seen:
                continue
            seen.add(key)
            out.append(f)
        return out


def _make_fingerprint(kind: str, value: str) -> str:
    """Build a redacted fingerprint for a matched secret value.

    Format: ``<kind>:<first4>…<last2>#<sha256[:8]>``
    """
    if len(value) <= 6:
        # Very short match — show even less to avoid reconstruction
        return f"{kind}:{value[:2]}…#{hashlib.sha256(value.encode()).hexdigest()[:8]}"
    prefix = value[:4]
    suffix = value[-2:]
    digest = hashlib.sha256(value.encode()).hexdigest()[:8]
    return f"{kind}:{prefix}…{suffix}#{digest}"


def _is_placeholder(context_text: str, match_start: int, match_end: int) -> bool:
    """Return True if the match is fully contained within a placeholder pattern."""
    for pm in _PLACEHOLDER_RE.finditer(context_text):
        if pm.start() <= match_start and match_end <= pm.end():
            return True
    return False


def scan_text(
    text: str,
    *,
    source_kind: SecretSource,
    event_index: int | None = None,
    event_role: str | None = None,
) -> ScanResult:
    """Scan a single text blob for credential patterns.

    Parameters
    ----------
    text : str
        The text to scan.
    source_kind : SecretSource
        Classification of where this text came from. The engine does not
        infer this; the caller (adapter) decides based on event role.
    event_index : int, optional
        Event index for traceability.
    event_role : str, optional
        Role of the event ("user", "assistant", "tool_result", etc.).

    Returns
    -------
    ScanResult
        All findings (including duplicates). Use ``.deduplicated`` for
        the unique-fingerprint view.
    """
    result = ScanResult()
    if not text:
        return result
    for m in SECRET_PATTERN.finditer(text):
        if _is_placeholder(text, m.start(), m.end()):
            continue
        # Find which named group matched
        kind = "UNKNOWN"
        for name, val in m.groupdict().items():
            if val is not None:
                kind = name
                break
        # Extract the actual secret-bearing substring for fingerprinting.
        # For composite patterns (GENERIC_KEY, PASSWORD_ASSIGN), the value
        # is the whole assignment; we still fingerprint the assignment
        # rather than parsing it further.
        value = m.group(0)
        fingerprint = _make_fingerprint(kind, value)
        result.findings.append(
            SecretFinding(
                kind=kind,
                source_kind=source_kind,
                fingerprint=fingerprint,
                event_index=event_index,
                event_role=event_role,
                raw_length=len(value),
            )
        )
    return result


def scan_many(
    items: Iterable[tuple[str, SecretSource, int | None, str | None]],
) -> ScanResult:
    """Scan many (text, source_kind, event_index, event_role) tuples.

    Returns a combined result. Deduplication is across the combined set.
    """
    combined = ScanResult()
    for text, source_kind, event_index, event_role in items:
        sub = scan_text(
            text,
            source_kind=source_kind,
            event_index=event_index,
            event_role=event_role,
        )
        combined.findings.extend(sub.findings)
    return combined


# ---------------------------------------------------------------------------
# Adapters — call scan_text with the correct source_kind for each event type
# ---------------------------------------------------------------------------


def scan_user_content(text: str, *, event_index: int | None = None) -> ScanResult:
    """Scan user message text. Findings are classified USER_PASTED."""
    return scan_text(
        text, source_kind=SecretSource.USER_PASTED,
        event_index=event_index, event_role="user",
    )


def scan_assistant_content(text: str, *, event_index: int | None = None) -> ScanResult:
    """Scan assistant message text. Findings are classified ASSISTANT_REPEATED."""
    return scan_text(
        text, source_kind=SecretSource.ASSISTANT_REPEATED,
        event_index=event_index, event_role="assistant",
    )


def scan_tool_result(text: str, *, event_index: int | None = None) -> ScanResult:
    """Scan tool_result text. Findings are classified TOOL_RETURNED."""
    return scan_text(
        text, source_kind=SecretSource.TOOL_RETURNED,
        event_index=event_index, event_role="tool_result",
    )


def scan_tool_call_args(
    args_text: str,
    *,
    event_index: int | None = None,
    write_tool: bool = False,
) -> ScanResult:
    """Scan tool-call argument text. Findings are classified WRITTEN_TO_FILE
    when the tool is a write tool (write/edit/search_replace), otherwise
    SOURCE_INSUFFICIENT (we cannot determine if the value was persisted)."""
    kind = SecretSource.WRITTEN_TO_FILE if write_tool else SecretSource.SOURCE_INSUFFICIENT
    return scan_text(
        args_text, source_kind=kind,
        event_index=event_index, event_role="tool_call_args",
    )


def scan_file_diff(diff_text: str, *, event_index: int | None = None) -> ScanResult:
    """Scan file-write diff content. Findings are classified WRITTEN_TO_FILE."""
    return scan_text(
        diff_text, source_kind=SecretSource.WRITTEN_TO_FILE,
        event_index=event_index, event_role="file_diff",
    )
