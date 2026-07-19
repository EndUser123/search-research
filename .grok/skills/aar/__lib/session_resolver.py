"""Resolve and verify the exact current Grok session identity.

Per spec Section 2: "Resolve the current session ID from a live, verified
authority available to the exact Grok process. Do not select the newest
session directory. Do not infer identity from timestamps."

Authority contract
------------------
Grok Build does **not** expose a ``GROK_SESSION_ID`` env var (verified
empirically against the running process). The authoritative identity sources,
in priority order, are:

1. **User/skill-supplied session id** (``session_id`` argument). The AAR
   skill knows its own session because Grok itself writes ``summary.json``
   into the active session directory. This is the "payload or process-
   provided" path the spec names as authoritative.
2. **Env var** ``GROK_SESSION_ID`` — checked at runtime for forward
   compatibility if Grok Build later exposes it. Currently absent.
3. **No fallback.** If neither is present, return
   ``SESSION_IDENTITY_UNVERIFIED``. We do **not** scan session directories,
   pick the newest, or infer from timestamps — those are the explicit
   anti-patterns the spec forbids.

Cross-validation
----------------
A supplied session id is verified against two co-located runtime artifacts:

* ``summary.json`` → ``info.id`` must equal the supplied id.
* ``events.jsonl`` → any ``turn_started.session_id`` must equal the supplied id.

If either check fails (different id present, or file missing/unreadable in
a way that suggests wrong directory), binding is ``UNVERIFIED`` with a
specific reason. We never silently accept a mismatch.

Isolation
---------
Foreign session directories are ignored by construction: we never scan the
parent ``sessions/`` directory. We only open the one directory the supplied
session id points at.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

__all__ = [
    "IdentityStatus",
    "SessionBinding",
    "resolve_session_dir",
    "verify_session_identity",
    "encode_workspace_path",
    "SESSION_IDENTITY_UNVERIFIED",
    "GROK_SESSIONS_ROOT",
    "ENV_VAR",
]

#: Canonical Grok sessions root (forward slashes for portable comparison).
GROK_SESSIONS_ROOT = "C:/Users/brsth/.grok/sessions"

#: Env var that Grok Build may expose in the future. Currently absent; checked
#: at runtime so the resolver gains verified identity automatically if Grok
#: later writes the current session id into the environment.
ENV_VAR = "GROK_SESSION_ID"

#: Status string emitted when identity cannot be verified. Per spec Section 2.
SESSION_IDENTITY_UNVERIFIED = "SESSION_IDENTITY_UNVERIFIED"

#: UUID v7-ish shape used by Grok session directories (8-4-4-4-12 hex).
_SESSION_ID_RE = re.compile(
    r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", re.I
)


class IdentityStatus(str, Enum):
    """Outcome of session identity resolution.

    * ``VERIFIED``        — supplied id is authoritative and cross-checks pass.
    * ``UNVERIFIED``      — no authority available, or cross-checks failed.
    * ``SUPPLIED_INVALID``— supplied value is not a UUID-shaped id.
    """

    VERIFIED = "VERIFIED"
    UNVERIFIED = SESSION_IDENTITY_UNVERIFIED
    SUPPLIED_INVALID = "SUPPLIED_INVALID"


@dataclass(frozen=True)
class SessionBinding:
    """Result of resolving and verifying session identity.

    ``session_dir`` is populated only when ``status is VERIFIED``. Callers
    MUST check status before consuming the directory path.
    """

    status: IdentityStatus
    session_id: str | None
    session_dir: str | None
    workspace_encoded: str | None
    reasons: tuple[str, ...] = field(default_factory=tuple)
    cross_checks: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "workspace_encoded": self.workspace_encoded,
            "reasons": list(self.reasons),
            "cross_checks": list(self.cross_checks),
        }


def encode_workspace_path(workspace: str) -> str:
    """Encode a workspace path the way Grok encodes the cwd into the sessions
    directory name. Empirically: URL-encoding with ``%`` for ``:`` and ``\\``
    on Windows (``P:\\`` → ``P%3A%5C``).

    Used to *locate* a session directory when the caller knows the workspace
    but not the encoded form. The caller may also pass the encoded form
    directly to :func:`resolve_session_dir`.
    """
    return workspace.replace(":", "%3A").replace("\\", "%5C").replace("/", "%5C")


def resolve_session_dir(
    *,
    session_id: str | None,
    workspace_encoded: str | None,
    sessions_root: str | Path = GROK_SESSIONS_ROOT,
    env: dict[str, str] | None = None,
) -> SessionBinding:
    """Resolve the session directory from authoritative inputs only.

    ``session_id`` is the caller-authoritative id (the AAR skill passes the
    live session id it knows). ``workspace_encoded`` is the URL-encoded cwd
    (e.g. ``P%3A%5C``). Either may be omitted; if both are present they must
    be consistent.

    Resolution order:
    1. ``session_id`` argument (highest authority).
    2. ``$GROK_SESSION_ID`` env var (forward-compatibility; currently unset).
    3. ``UNVERIFIED`` otherwise — never falls back to directory scanning.

    The supplied id is then cross-validated via :func:`verify_session_identity`.
    """
    reasons: list[str] = []
    cross_checks: list[str] = []

    # 1. Pick the candidate id from the highest-priority source available.
    sid: str | None = session_id
    authority = "argument"
    if sid is None:
        env_map = env if env is not None else __import__("os").environ
        env_val = env_map.get(ENV_VAR)
        if env_val and isinstance(env_val, str) and env_val.strip():
            sid = env_val.strip()
            authority = f"env:${ENV_VAR}"

    if sid is None:
        reasons.append(
            "no session id supplied and $" + ENV_VAR + " is not set; "
            "Grok Build does not expose the current session id via env"
        )
        return SessionBinding(
            status=IdentityStatus.UNVERIFIED,
            session_id=None,
            session_dir=None,
            workspace_encoded=workspace_encoded,
            reasons=tuple(reasons),
        )

    # 2. Validate the shape (UUID-ish). Reject garbage early.
    if not isinstance(sid, str) or not _SESSION_ID_RE.fullmatch(sid):
        reasons.append(f"supplied session id {sid!r} is not UUID-shaped")
        return SessionBinding(
            status=IdentityStatus.SUPPLIED_INVALID,
            session_id=sid,
            session_dir=None,
            workspace_encoded=workspace_encoded,
            reasons=tuple(reasons),
        )

    # 3. Compute the candidate directory.
    root = Path(sessions_root).resolve() if Path(sessions_root).exists() else Path(sessions_root)
    if workspace_encoded:
        candidate = root / workspace_encoded / sid
    else:
        # Without the encoded-workspace component we cannot locate the dir
        # deterministically (multiple encoded-workspace dirs could exist).
        # This is an UNVERIFIED outcome, not a scan.
        reasons.append(
            "workspace_encoded not supplied; cannot locate session dir without it "
            "(would require scanning, which the spec forbids)"
        )
        return SessionBinding(
            status=IdentityStatus.UNVERIFIED,
            session_id=sid,
            session_dir=None,
            workspace_encoded=None,
            reasons=tuple(reasons),
        )

    if not candidate.is_dir():
        reasons.append(f"session directory does not exist: {candidate}")
        return SessionBinding(
            status=IdentityStatus.UNVERIFIED,
            session_id=sid,
            session_dir=str(candidate).replace("\\", "/"),
            workspace_encoded=workspace_encoded,
            reasons=tuple(reasons),
        )

    # 4. Cross-validate against the runtime artifacts in the directory.
    binding = verify_session_identity(sid, candidate, authority=authority)
    if workspace_encoded and binding.workspace_encoded is None:
        # Preserve the workspace component on the returned binding.
        binding = SessionBinding(
            status=binding.status,
            session_id=binding.session_id,
            session_dir=binding.session_dir,
            workspace_encoded=workspace_encoded,
            reasons=binding.reasons,
            cross_checks=binding.cross_checks,
        )
    return binding


def verify_session_identity(
    session_id: str,
    session_dir: str | Path,
    *,
    authority: str = "argument",
) -> SessionBinding:
    """Cross-validate a session id against co-located runtime artifacts.

    Checks (each adds a cross_check note; failures add a reason and downgrade
    to ``UNVERIFIED``):

    * ``summary.json`` exists and ``info.id == session_id``.
    * ``events.jsonl`` (if present and parseable) contains at least one
      ``turn_started`` whose ``session_id`` matches. Absence of events.jsonl
      is not fatal (it may not have been written yet) but is recorded.

    Returns a :class:`SessionBinding`. ``status`` is ``VERIFIED`` only if at
    least one cross-check succeeds and none contradicts.
    """
    reasons: list[str] = []
    cross_checks: list[str] = []
    sd = Path(session_dir)
    dir_str = str(sd).replace("\\", "/")

    # --- summary.json cross-check ---
    summary_path = sd / "summary.json"
    if summary_path.is_file():
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            info = data.get("info") if isinstance(data, dict) else None
            sid_in_summary = info.get("id") if isinstance(info, dict) else None
            if sid_in_summary == session_id:
                cross_checks.append(f"summary.json info.id matches ({authority})")
            else:
                reasons.append(
                    f"summary.json info.id={sid_in_summary!r} != supplied {session_id!r}"
                )
        except (json.JSONDecodeError, OSError) as exc:
            reasons.append(f"summary.json unreadable: {exc}")
    else:
        reasons.append("summary.json absent — cannot cross-check via metadata")

    # --- events.jsonl cross-check (turn_started.session_id) ---
    events_path = sd / "events.jsonl"
    events_checked = False
    if events_path.is_file():
        # Stream the file rather than loading all 132k lines into memory.
        # Stop at the first matching turn_started for efficiency.
        try:
            with events_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if '"turn_started"' not in line:
                        continue
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if ev.get("type") != "turn_started":
                        continue
                    events_checked = True
                    ev_sid = ev.get("session_id")
                    if ev_sid == session_id:
                        cross_checks.append(
                            "events.jsonl turn_started.session_id matches"
                        )
                        break
                    if ev_sid is not None and ev_sid != session_id:
                        reasons.append(
                            f"events.jsonl turn_started.session_id={ev_sid!r} != supplied {session_id!r}"
                        )
                        break
        except OSError as exc:
            reasons.append(f"events.jsonl unreadable: {exc}")
    if not events_checked and not reasons:
        # events.jsonl absent or no turn_started yet — not fatal for a brand-
        # new session, but worth recording as a soft gap.
        cross_checks.append("events.jsonl has no turn_started yet (session may be very fresh)")

    if reasons:
        return SessionBinding(
            status=IdentityStatus.UNVERIFIED,
            session_id=session_id,
            session_dir=dir_str,
            workspace_encoded=None,
            reasons=tuple(reasons),
            cross_checks=tuple(cross_checks),
        )
    if not cross_checks:
        reasons.append("no cross-check artifact was available")
        return SessionBinding(
            status=IdentityStatus.UNVERIFIED,
            session_id=session_id,
            session_dir=dir_str,
            workspace_encoded=None,
            reasons=tuple(reasons),
            cross_checks=tuple(cross_checks),
        )
    return SessionBinding(
        status=IdentityStatus.VERIFIED,
        session_id=session_id,
        session_dir=dir_str,
        workspace_encoded=None,
        cross_checks=tuple(cross_checks),
    )
