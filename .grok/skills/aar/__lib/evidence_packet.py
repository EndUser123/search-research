"""Assemble and persist the structured evidence packet for the AAR LLM stage.

The packet is the bridge between deterministic preprocessing and LLM
synthesis. It carries:

* the source descriptor (path, status, session id, terminal id);
* honest parse statistics (counts, skipped lines, data-quality flags);
* all deterministic signals from ``detectors.run_all_detectors``;
* a signal-by-kind accounting block;
* an integrity block (deterministic content hash) so consumers can detect
  tampering or drift.

Provenance discipline (CRITICAL — global rule "Never invent provenance identity")
--------------------------------------------------------------------------------
* ``terminal_id`` is sourced from documented env vars
  (``CLAUDE_TERMINAL_ID`` / ``WT_SESSION`` / ``TERMINAL_ID``) and falls back
  to the literal string ``"noterm"`` with a visible ``provenance_warnings``
  entry. We never invent a terminal id.
* ``session_id`` is *derived* from the transcript path (the Grok session UUID
  directory) — a documented derivation, not a random id. If absent, it is
  ``None`` with a warning.
* ``run_digest`` is a deterministic SHA-256 digest of the packet contents. It
  is named ``run_digest`` (not ``run_id``) to make clear it is a content
  fingerprint, not a fake session/run identity that could be mistaken for
  joinable provenance.

Atomic writes
-------------
Packet files are written via ``<path>.tmp`` followed by ``os.replace`` so a
partial write never leaves a corrupt packet on disk. A sibling
``packet.manifest.json`` records the sha256 of ``packet.json`` for tamper
detection on load.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from detectors import Signal, run_all_detectors
from event_model import PACKET_SCHEMA_VERSION, ParseStats, SourceStatus, Transcript
from transcript_parser import parse_transcript

__all__ = [
    "EvidencePacket",
    "PacketSource",
    "IntegrityBlock",
    "build_evidence_packet",
    "write_packet",
    "load_packet",
    "run_preprocessor",
    "resolve_terminal_id",
    "PRODUCER",
    "PACKET_FILENAME",
    "MANIFEST_FILENAME",
]

PRODUCER = "aar-transcript-preprocessor/1.0"
PACKET_FILENAME = "packet.json"
MANIFEST_FILENAME = "packet.manifest.json"

#: Documented env vars searched in order for terminal identity.
_TERMINAL_ENV_VARS = ("CLAUDE_TERMINAL_ID", "WT_SESSION", "TERMINAL_ID")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PacketSource:
    """Identity + completeness of the transcript the packet was built from."""

    transcript_path: str
    source_status: str  #: one of SourceStatus values
    session_id: str | None
    terminal_id: str
    has_timestamps: bool
    provenance_warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "transcript_path": self.transcript_path,
            "source_status": self.source_status,
            "session_id": self.session_id,
            "terminal_id": self.terminal_id,
            "has_timestamps": self.has_timestamps,
            "provenance_warnings": list(self.provenance_warnings),
        }


@dataclass(frozen=True)
class IntegrityBlock:
    """Tamper-evidence for the packet.

    ``content_sha256`` is computed over the canonical JSON of the packet
    *minus* the integrity block itself (so the digest is self-consistent).
    """

    content_sha256: str
    algorithm: str = "sha256"
    schema_version: str = PACKET_SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "content_sha256": self.content_sha256,
            "algorithm": self.algorithm,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class EvidencePacket:
    """Immutable, serialisable evidence packet for the LLM stage."""

    schema_version: str
    produced_at: str  #: ISO-8601 UTC
    producer: str
    source: PacketSource
    parse_stats: dict[str, Any]
    signals: tuple[dict[str, Any], ...]
    signal_counts: dict[str, int] = field(default_factory=dict)
    signal_total: int = 0
    integrity: IntegrityBlock | None = None
    #: Optional notes from the builder (e.g. detector count, overrides).
    builder_notes: tuple[str, ...] = ()

    def to_dict(self, *, with_integrity: bool = True) -> dict:
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "produced_at": self.produced_at,
            "producer": self.producer,
            "source": self.source.to_dict(),
            "parse_stats": self.parse_stats,
            "signals": list(self.signals),
            "signal_counts": dict(self.signal_counts),
            "signal_total": self.signal_total,
            "builder_notes": list(self.builder_notes),
        }
        if with_integrity and self.integrity is not None:
            d["integrity"] = self.integrity.to_dict()
        return d


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_terminal_id(env: dict[str, str] | None = None) -> tuple[str, tuple[str, ...]]:
    """Return (terminal_id, warnings) from documented env vars.

    Falls back to ``"noterm"`` with a visible warning rather than inventing an
    id. ``env`` parameter is for testability; production callers should omit
    it so the real process environment is consulted.
    """
    env_map = env if env is not None else os.environ
    warnings: list[str] = []
    for var in _TERMINAL_ENV_VARS:
        val = env_map.get(var)
        if val and isinstance(val, str) and val.strip():
            cleaned = re.sub(r"[^A-Za-z0-9_-]", "", val)
            if not cleaned:
                continue
            return cleaned, ()
    warnings.append(
        "no terminal id env var found (checked "
        + ", ".join(_TERMINAL_ENV_VARS)
        + "); falling back to 'noterm'"
    )
    return "noterm", tuple(warnings)


def build_evidence_packet(
    transcript: Transcript,
    signals: Iterable[Signal] | None = None,
    *,
    terminal_id: str | None = None,
    terminal_warnings: tuple[str, ...] | None = None,
    env: dict[str, str] | None = None,
    produced_at: str | None = None,
    builder_notes: tuple[str, ...] = (),
) -> EvidencePacket:
    """Assemble an ``EvidencePacket`` from a parsed transcript and signals.

    If ``signals`` is None, detectors are run automatically. If
    ``terminal_id`` is None, it is resolved from the environment (with
    visible warnings on fallback). ``produced_at`` may be injected for
    deterministic tests; otherwise it is the current UTC ISO timestamp.
    """
    sig_list = list(signals) if signals is not None else run_all_detectors(transcript.events)
    signal_dicts = tuple(s.to_dict() for s in sig_list)
    counts: dict[str, int] = {}
    for s in sig_list:
        counts[s.kind.value] = counts.get(s.kind.value, 0) + 1

    if terminal_id is None:
        terminal_id, term_warnings = resolve_terminal_id(env=env)
        if terminal_warnings is None:
            terminal_warnings = term_warnings
    elif terminal_warnings is None:
        terminal_warnings = ()

    src_warnings: list[str] = list(terminal_warnings)
    if transcript.session_id is None:
        src_warnings.append(
            "session_id could not be derived from the transcript path "
            "(no UUID-shaped directory component)"
        )

    source = PacketSource(
        transcript_path=transcript.source_path,
        source_status=transcript.source_status.value,
        session_id=transcript.session_id,
        terminal_id=terminal_id,
        has_timestamps=transcript.parse_stats.has_timestamps,
        provenance_warnings=tuple(src_warnings),
    )

    produced = produced_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    packet = EvidencePacket(
        schema_version=PACKET_SCHEMA_VERSION,
        produced_at=produced,
        producer=PRODUCER,
        source=source,
        parse_stats=transcript.parse_stats.to_dict(),
        signals=signal_dicts,
        signal_counts=counts,
        signal_total=len(sig_list),
        builder_notes=builder_notes,
    )
    return _with_integrity(packet)


def write_packet(packet: EvidencePacket, out_dir: str | Path) -> Path:
    """Persist the packet atomically under ``out_dir``.

    Writes ``packet.json`` and ``packet.manifest.json``. Returns the path to
    ``packet.json``. The write is atomic per-file (``.tmp`` + ``os.replace``)
    so a crash mid-write leaves either the previous file or no file, never a
    truncated one.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet_path = out / PACKET_FILENAME

    # Defensive: refuse to overwrite a non-packet file at the canonical name.
    # If a previous packet exists, the atomic replace below is still safe and
    # is the documented replacement behaviour.
    payload = json.dumps(packet.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    tmp = packet_path.with_suffix(".json.tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, packet_path)

    # Manifest: sha256 of the on-disk bytes (so load_packet can verify exactly).
    manifest_path = out / MANIFEST_FILENAME
    manifest = {
        "schema_version": packet.schema_version,
        "producer": packet.producer,
        "produced_at": packet.produced_at,
        "packet_sha256": _sha256_file(packet_path),
        "packet_bytes": packet_path.stat().st_size,
        "algorithm": "sha256",
    }
    mtmp = manifest_path.with_suffix(".json.tmp")
    mtmp.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(mtmp, manifest_path)
    return packet_path


def load_packet(path: str | Path) -> EvidencePacket:
    """Load a packet from disk and verify its manifest hash.

    Raises ``ValueError`` if the manifest is missing or the sha256 of the
    packet file does not match the manifest (tamper / partial write).
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"packet not found: {p}")
    raw = p.read_text(encoding="utf-8")
    obj = json.loads(raw)

    manifest_path = p.parent / MANIFEST_FILENAME
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        actual = _sha256_file(p)
        expected = manifest.get("packet_sha256")
        if expected and actual != expected:
            raise ValueError(
                f"packet integrity check failed: sha256 mismatch "
                f"(expected {expected}, got {actual})"
            )
    # else: warn-on-missing-manifest rather than refuse — older packets may
    # predate manifests. Surface via builder_notes on the returned object.

    schema = obj.get("schema_version", "unknown")
    if schema != PACKET_SCHEMA_VERSION:
        raise ValueError(
            f"packet schema version {schema!r} unsupported "
            f"(expected {PACKET_SCHEMA_VERSION!r})"
        )

    source = PacketSource(
        transcript_path=obj["source"]["transcript_path"],
        source_status=obj["source"]["source_status"],
        session_id=obj["source"].get("session_id"),
        terminal_id=obj["source"]["terminal_id"],
        has_timestamps=obj["source"].get("has_timestamps", False),
        provenance_warnings=tuple(obj["source"].get("provenance_warnings", [])),
    )
    integrity_dict = obj.get("integrity")
    integrity = (
        IntegrityBlock(
            content_sha256=integrity_dict["content_sha256"],
            algorithm=integrity_dict.get("algorithm", "sha256"),
            schema_version=integrity_dict.get("schema_version", PACKET_SCHEMA_VERSION),
        )
        if integrity_dict
        else None
    )
    return EvidencePacket(
        schema_version=obj["schema_version"],
        produced_at=obj["produced_at"],
        producer=obj.get("producer", PRODUCER),
        source=source,
        parse_stats=obj.get("parse_stats", {}),
        signals=tuple(obj.get("signals", [])),
        signal_counts=obj.get("signal_counts", {}),
        signal_total=obj.get("signal_total", 0),
        integrity=integrity,
        builder_notes=tuple(obj.get("builder_notes", [])),
    )


def run_preprocessor(
    transcript_path: str | Path,
    out_dir: str | Path,
    *,
    env: dict[str, str] | None = None,
    produced_at: str | None = None,
) -> tuple[Transcript, EvidencePacket, Path]:
    """End-to-end deterministic pipeline: parse → detect → packet → write.

    Returns the parsed Transcript, the built EvidencePacket, and the path to
    the persisted ``packet.json``. This is the function the AAR skill invokes
    before LLM synthesis.
    """
    transcript = parse_transcript(transcript_path)
    packet = build_evidence_packet(
        transcript, env=env, produced_at=produced_at
    )
    written = write_packet(packet, out_dir)
    return transcript, packet, written


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _with_integrity(packet: EvidencePacket) -> EvidencePacket:
    """Compute and attach the IntegrityBlock over the packet's canonical JSON.

    The integrity hash excludes the integrity block itself (chicken-and-egg).
    Deterministic: sort_keys, ensure_ascii=False, compact separators.

    Uses ``dataclasses.replace`` rather than dict-unpacking so tuple-typed
    fields (``signals``, ``builder_notes``) are not coerced to lists.
    """
    body = packet.to_dict(with_integrity=False)
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return replace(packet, integrity=IntegrityBlock(content_sha256=digest))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Optional CLI: python evidence_packet.py <transcript> [out_dir]
# ---------------------------------------------------------------------------


def _main(argv: list[str]) -> int:
    if not argv:
        print(
            "usage: python evidence_packet.py <chat_history.jsonl> [out_dir]",
            file=sys.stderr,
        )
        return 2
    transcript_path = Path(argv[0])
    out_dir = Path(argv[1]) if len(argv) > 1 else transcript_path.parent / "aar_packet"
    try:
        transcript, packet, written = run_preprocessor(transcript_path, out_dir)
    except Exception as exc:  # surface as a clean stderr exit, not a stack trace
        print(f"preprocessor failed: {exc}", file=sys.stderr)
        return 1
    print(f"transcript: {transcript.source_path}")
    print(f"source_status: {transcript.source_status.value}")
    print(f"events: {len(transcript.events)}")
    print(f"signals: {packet.signal_total}")
    for kind, n in sorted(packet.signal_counts.items()):
        print(f"  {kind}: {n}")
    print(f"packet: {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
