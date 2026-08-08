"""Top-level entrypoint for the /check deterministic transcript preprocessor.

Ties together parser → detectors → packet → validator and exposes a small
surface for the /check orchestrator to call:

* ``preprocess(path)`` — parse a JSONL transcript, run all detectors, build
  the packet, validate it, return an ``EvidencePacket``.
* ``preprocess_to_file(path, out_path)`` — same, plus write JSON to disk
  (atomic rename) and return the path written.
* CLI: ``python preprocessor.py <chat_history.jsonl> <output.json>``

This module is the only import the /check SKILL.md needs to reference. All
internal module structure (event_model, transcript_parser, detectors,
evidence_packet, output_validator) is an implementation detail.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sibling modules importable when run as a script (no package context).
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from detectors import run_all_detectors  # noqa: E402
from evidence_packet import build_packet  # noqa: E402
from output_validator import ValidationError, assert_valid_packet  # noqa: E402
from transcript_parser import parse_file  # noqa: E402

__all__ = [
    "preprocess",
    "preprocess_to_file",
    "PreprocessError",
    "main",
]


class PreprocessError(RuntimeError):
    """Raised when preprocessing fails structurally (e.g. invalid packet)."""


def preprocess(transcript_path: str | Path) -> "object":  # EvidencePacket
    """Parse + detect + build + validate. Returns an EvidencePacket.

    Raises ``PreprocessError`` if the resulting packet fails validation —
    this is a "the preprocessor is broken" signal, not a "the transcript is
    weird" signal. Weird transcripts produce PARTIAL/UNVERIFIED source
    status and parser warnings, not exceptions.
    """
    transcript = parse_file(transcript_path)
    # build_packet runs detectors by default.
    packet = build_packet(transcript)
    try:
        assert_valid_packet(packet.to_dict())
    except ValidationError as e:
        raise PreprocessError(str(e)) from e
    return packet


def preprocess_to_file(
    transcript_path: str | Path,
    output_path: str | Path,
) -> str:
    """Preprocess and write the packet as JSON to ``output_path``.

    Returns the forward-slash output path written. Atomic via tmp+rename
    (see ``EvidencePacket.write``).
    """
    packet = preprocess(transcript_path)
    out = str(output_path).replace("\\", "/")
    return packet.write(out)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint: ``python preprocessor.py <in.jsonl> <out.json>``.

    Exit codes:
      0 — packet built and validated
      1 — usage error (wrong arg count)
      2 — preprocessing/structural error (reported on stderr)
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        sys.stderr.write(
            "usage: python preprocessor.py <chat_history.jsonl> <output.json>\n"
        )
        return 1
    in_path, out_path = args
    try:
        written = preprocess_to_file(in_path, out_path)
    except PreprocessError as e:
        sys.stderr.write(f"preprocess error: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"io error: {e}\n")
        return 2
    except (UnicodeDecodeError, ValueError) as e:
        # UnicodeDecodeError: non-UTF8 byte in transcript (subclass of ValueError).
        # ValueError covers any other malformed-payload error from the parser.
        sys.stderr.write(f"preprocess error: {type(e).__name__}: {e}\n")
        return 2
    sys.stdout.write(written + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
