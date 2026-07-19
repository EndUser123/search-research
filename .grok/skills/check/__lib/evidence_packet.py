"""Assemble a structured evidence packet from a parsed Transcript + Signals.

The packet is the single artifact that flows from the deterministic
preprocessor into the /check verifier subagents. It is:

* **Path-only friendly.** The packet is JSON-serialisable so it can be
  written to ``$runDir/packets/evidence-packet.json`` and referenced by path
  from verifier prompts (matching /check's existing path-only convention).
* **Reconcilable.** ``signal_counts`` must equal ``len(signals[kind])`` for
  every detector. The output_validator enforces this.
* **Provenance-carrying.** Source path, status, session id, and parser
  warnings travel with the data so a verifier never has to re-read the raw
  transcript to know what the evidence represents.

Wall-clock discipline
---------------------
Only ``produced_at`` is wall-clock time, and only for forensic uniqueness of
the packet file. Every other field is either copied from the transcript
(parser counts, source status) or derived deterministically (signal counts).
We do NOT invent timestamps for events — Grok JSONL has none.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from event_model import PACKET_SCHEMA_VERSION, SourceStatus, Transcript
from detectors import Signal, run_all_detectors, DETECTOR_NAMES

__all__ = ["EvidencePacket", "build_packet"]


class EvidencePacket:
    """Mutable-but-stable wrapper around the packet dict.

    The dict form (``to_dict`` / ``to_json``) is the serialisation contract.
    This class adds convenience accessors and a ``reconciles`` check used by
    ``output_validator`` and by tests.
    """

    def __init__(
        self,
        *,
        transcript: Transcript,
        signals_by_kind: dict[str, list[Signal]],
        produced_at: str | None = None,
        producer: str = "check.preprocessor",
    ) -> None:
        self._transcript = transcript
        self._signals = {k: list(v) for k, v in signals_by_kind.items()}
        self._produced_at = produced_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._producer = producer

    # --- accessors ---

    @property
    def schema_version(self) -> str:
        return PACKET_SCHEMA_VERSION

    @property
    def producer(self) -> str:
        return self._producer

    @property
    def produced_at(self) -> str:
        return self._produced_at

    @property
    def source_path(self) -> str:
        return self._transcript.source_path

    @property
    def source_status(self) -> SourceStatus:
        return self._transcript.source_status

    @property
    def session_id(self) -> str | None:
        return self._transcript.session_id

    @property
    def parse_stats(self) -> dict[str, Any]:
        return self._transcript.parse_stats.to_dict()

    @property
    def signal_counts(self) -> dict[str, int]:
        return {k: len(self._signals.get(k, ())) for k in DETECTOR_NAMES}

    @property
    def warnings(self) -> list[str]:
        # Combine parser warnings with a coarse signal-level sanity check.
        warns: list[str] = list(self._transcript.parse_stats.warnings)
        return warns

    def signals(self, kind: str) -> list[Signal]:
        """Return the signals for one detector kind (copies the list)."""
        return list(self._signals.get(kind, ()))

    def all_signals(self) -> dict[str, list[Signal]]:
        """Return all signals bucketed by kind (deep-ish copy)."""
        return {k: list(v) for k, v in self._signals.items()}

    # --- reconciliation ---

    def reconciles(self) -> bool:
        """Arithmetic check: signal_counts[kind] == len(signals[kind]).

        Also requires every detector name to be present. Proves only
        counting consistency, not signal validity.
        """
        for name in DETECTOR_NAMES:
            if name not in self._signals:
                return False
            if self.signal_counts[name] != len(self._signals[name]):
                return False
        return True

    # --- serialisation ---

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "producer": self.producer,
            "produced_at": self.produced_at,
            "source": {
                "path": self.source_path,
                "status": self.source_status.value,
                "session_id": self.session_id,
                "line_count": self._transcript.parse_stats.total_lines,
                "has_timestamps": self._transcript.parse_stats.has_timestamps,
            },
            "parse_stats": self.parse_stats,
            "signal_counts": self.signal_counts,
            "signals": {
                kind: [s.to_dict() for s in self._signals.get(kind, ())]
                for kind in DETECTOR_NAMES
            },
            "warnings": self.warnings,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)

    def write(self, path: str) -> str:
        """Write the packet as JSON to ``path``. Returns the path written.

        Atomic-ish: writes to ``<path>.tmp`` then renames, so a partial write
        never replaces a known-good packet.
        """
        import os

        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(self.to_json())
        os.replace(tmp, path)
        return path


def build_packet(
    transcript: Transcript,
    *,
    signals_by_kind: dict[str, list[Signal]] | None = None,
    produced_at: str | None = None,
    producer: str = "check.preprocessor",
) -> EvidencePacket:
    """Build an EvidencePacket from a Transcript, running detectors if needed.

    If ``signals_by_kind`` is omitted, all 10 detectors run. Pass it
    explicitly only in tests that want to exercise the assembler with
    synthetic signals.
    """
    sigs = signals_by_kind if signals_by_kind is not None else run_all_detectors(transcript)
    # Ensure every detector key is present even if empty.
    for name in DETECTOR_NAMES:
        sigs.setdefault(name, [])
    return EvidencePacket(
        transcript=transcript,
        signals_by_kind=sigs,
        produced_at=produced_at,
        producer=producer,
    )
