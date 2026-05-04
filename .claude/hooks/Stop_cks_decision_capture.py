#!/usr/bin/env python3
"""Stop hook: Extract decisions from transcript and ingest to CKS.

This hook runs at session end and automatically:
1. Extracts decisions using Oppia 5-Step structure
2. Ingests them directly to CKS (no intermediate JSONL)
3. Reports extraction statistics

Decision types captured:
- ARCHITECTURAL (design choices)
- DEBUGGING (bug fixes, root cause analysis)
- IMPLEMENTATION (how to build something)
- PROCESS (workflow decisions)
- EXPLORATION (investigation outcomes)
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Add CSF src to path for CKS import
csf_src = Path(__file__).resolve().parent.parent.parent / "__csf" / "src"
if csf_src.exists():
    sys.path.insert(0, str(csf_src))

# Add semantic_daemon path for write signal client
semantic_daemon_path = Path(__file__).resolve().parent.parent.parent / "packages" / "search-research" / "contrib" / "semantic_daemon"
if semantic_daemon_path.exists():
    sys.path.insert(0, str(semantic_daemon_path))

# Lazy client for write signal
_write_signal_client = None


def _get_write_signal_client():
    """Get or create daemon client for write signals."""
    global _write_signal_client
    if _write_signal_client is None:
        try:
            from daemons.daemon_client import DaemonClient

            _write_signal_client = DaemonClient(auto_start=False, enable_fallback=True)
        except Exception:
            return None
    return _write_signal_client


def _send_write_signal_batch(entry_ids: list[str], session_id: str) -> None:
    """Send write signals to daemon for multiple CKS entries (fire-and-forget)."""
    client = _get_write_signal_client()
    if client is None:
        return
    try:
        for entry_id in entry_ids:
            client.send_write_signal(
                entry_id=entry_id,
                entry_type="decision",
                workspace=str(Path(__file__).resolve().parent.parent.parent),
                terminal_id=session_id,
            )
    except Exception:
        pass  # fire-and-forget, never block


@hook_main
def main() -> int:
    """Extract decisions from transcript and store in CKS."""
    raw_input = sys.stdin.read()
    raw_input = raw_input.lstrip("\ufeff").strip()

    # Stop hook contract: always emit JSON on stdout.
    def _allow(code: int = 0, note: str | None = None) -> int:
        if note:
            print(note, file=sys.stderr)
        print("{}")
        return code

    transcript = raw_input
    if raw_input:
        try:
            parsed = json.loads(raw_input)
            if isinstance(parsed, dict):
                transcript = str(parsed.get("response", "")) or raw_input
        except json.JSONDecodeError:
            pass

    if not transcript or len(transcript) < 100:
        return _allow(0, "# Transcript too short, skipping decision capture")

    try:
        from cks.unified import CKS

        # CKS database location
        db_path = Path(__file__).resolve().parent.parent.parent / "__csf" / "data" / "cks.db"

        session_id = f"S-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

        with CKS(str(db_path)) as cks:
            result = cks.extract_and_ingest_decisions(
                transcript=transcript,
                min_confidence=0.60,
                session_id=session_id,
            )

        # Send write signal to daemon for immediate FAISS refresh (fire-and-forget)
        if result["count"] > 0:
            _send_write_signal_batch(result["entry_ids"], session_id)
            return _allow(
                0,
                (
                    f"✓ Captured {result['count']} decisions to CKS; "
                    f"avg_conf={result['avg_confidence']:.2f}, "
                    f"hyp_cov={result['hypothesis_coverage']:.1%}, "
                    f"oppia={result['oppia_complete']:.1%}"
                ),
            )
        else:
            return _allow(0, "# No decisions extracted (confidence threshold: 0.60)")

    except ImportError as e:
        return _allow(1, f"# CKS not available: {e}")
    except Exception as e:
        return _allow(1, f"✗ Error: {e}")


if __name__ == "__main__":
    sys.exit(main())
