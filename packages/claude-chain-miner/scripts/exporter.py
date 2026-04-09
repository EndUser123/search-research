"""Exporter module — uses chs_cli.py to export session transcripts."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

# Resolve package root for intra-package imports
_PKG_ROOT = Path(__file__).resolve().parents[1]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_CHS_CLI = Path("P:/packages/search-research/skills/chs/scripts/chs_cli.py")
_CLAUDE_BASE = Path.home() / ".claude"
_EXPORTS_DIR = _CLAUDE_BASE / "exports"


# ---------------------------------------------------------------------------
# chscli integration
# ---------------------------------------------------------------------------

def export_session(session_id: str, output_path: Path | None = None) -> Path | None:
    """Export a single session transcript via chscli.

    Args:
        session_id: The session UUID
        output_path: Path to write output to (default: exports_dir/session_id.md)

    Returns:
        Path to the exported file, or None on failure.
    """
    if output_path is None:
        _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = _EXPORTS_DIR / f"session_{session_id}.md"

    if not _CHS_CLI.exists():
        logger.error("chs_cli.py not found at %s", _CHS_CLI)
        return None

    result = subprocess.run(
        [sys.executable, str(_CHS_CLI), "--export", "--session-id", session_id, "--output", str(output_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.warning("chscli export failed for %s (rc=%d): %s", session_id, result.returncode, result.stderr[:200])
        return None

    if not output_path.exists():
        logger.warning("chscli reported success but output file not found: %s", output_path)
        return None

    logger.info("Exported session %s → %s", session_id, output_path)
    return output_path


def export_chain(session_ids: list[str]) -> list[Path]:
    """Export multiple sessions in sequence.

    Returns list of successfully exported file paths.
    """
    results: list[Path] = []
    for sid in session_ids:
        ep = export_session(sid)
        if ep:
            results.append(ep)
    return results


def merge_exports(exported_paths: list[Path], output_path: Path | None = None) -> Path:
    """Merge multiple exported markdown files into one chain document.

    Args:
        exported_paths: List of exported .md file paths
        output_path: Final merged output path

    Returns:
        Path to the merged file.
    """
    if output_path is None:
        _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = _EXPORTS_DIR / f"merged_chain_{timestamp}.md"

    parts: list[str] = [
        "# Session Chain Export\n",
        f"Sessions: {len(exported_paths)}\n\n",
        "---\n\n",
    ]

    for ep in exported_paths:
        if ep.exists():
            content = ep.read_text(encoding="utf-8")
            parts.append(f"## {ep.stem}\n\n")
            parts.append(content)
            parts.append("\n\n---\n\n")

    output_path.write_text("".join(parts), encoding="utf-8")
    logger.info("Merged %d sessions → %s", len(exported_paths), output_path)
    return output_path


# ---------------------------------------------------------------------------
# Parse compact-proof transcripts
# ---------------------------------------------------------------------------

def parse_transcript_jsonl(jsonl_path: Path) -> list[dict[str, Any]]:
    """Parse a .jsonl transcript file.

    Handles both full message transcripts and file-history-snapshot entries
    (post-compaction format with no message content).
    """
    entries: list[dict[str, Any]] = []
    if not jsonl_path.exists():
        return entries

    try:
        with open(jsonl_path, encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except OSError as exc:
        logger.warning("Failed to parse %s: %s", jsonl_path, exc)

    return entries


def extract_messages(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Extract user/assistant messages from transcript entries.

    Returns list of {role, content} dicts.
    Works for both full transcripts (with message.content blocks) and
    file-history-snapshot entries (structured summary only).
    """
    messages: list[dict[str, str]] = []

    for entry in entries:
        entry_type = entry.get("type", "")
        if entry_type not in ("user", "assistant"):
            continue

        msg = entry.get("message", {})
        content: str | list = ""

        if isinstance(msg, dict):
            content = msg.get("content", [])
        elif isinstance(msg, str):
            content = msg
        else:
            content = ""

        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_result":
                        tool_content = block.get("content", "")
                        if isinstance(tool_content, str):
                            text_parts.append(tool_content)
            content = "\n".join(text_parts)
        elif not isinstance(content, str):
            content = str(content) if content else ""

        if content:
            messages.append({"role": entry_type, "content": content})

    return messages
