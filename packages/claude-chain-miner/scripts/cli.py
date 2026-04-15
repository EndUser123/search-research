#!/usr/bin/env python3
"""ClaudeChainMiner — CLI for post-compact session chain mining.

Usage:
    claude-chain-mine --slug P-- --mine "webhook issues"
    claude-chain-mine --slug P-- --walk
    claude-chain-mine --slug P-- --export
    claude-chain-mine --slug P-- --list
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add package root to path for imports
_package_root = Path(__file__).resolve().parents[1]
if str(_package_root) not in sys.path:
    sys.path.insert(0, str(_package_root))

from scripts.walker import (
    get_chain_for_slug,
    get_current_slug,
    walk_handoff_chain,
)
from scripts.exporter import export_chain as export_chain_via_chscli
from scripts.fts import index_chain as fts_index_chain, fts_mine as fts_run_mine

__version__ = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("claude-chain-mine")


# ---------------------------------------------------------------------------
# Compact-proof transcript parser
# ---------------------------------------------------------------------------

def _parse_transcript_entries(transcript_path: Path) -> list[dict]:
    """Parse a .jsonl transcript, handling both full and file-history-snapshot.

    For file-history-snapshot entries (post-compaction), extracts whatever
    fields are available (type, message, content, parentUuid, sessionId, etc.).
    """
    entries = []
    if not transcript_path.exists():
        return entries

    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except OSError as exc:
        logger.warning("Failed to read %s: %s", transcript_path, exc)

    return entries


# ---------------------------------------------------------------------------
# Mine patterns from transcripts
# ---------------------------------------------------------------------------

_MINING_PATTERNS = {
    "problem": [
        r"\*\*What was the problem\?\*\*[:\s]*(.+)",
        r"Problem: (.+)",
        r"#+ Problem[:\s]*(.+)",
    ],
    "fix": [
        r"\*\*What was the fix\?\*\*[:\s]*(.+)",
        r"Fix: (.+)",
        r"#+ Fix[:\s]*(.+)",
    ],
    "action": [
        r"\*\*What did we do\?\*\*[:\s]*(.+)",
        r"Action: (.+)",
        r"#+ Action[:\s]*(.+)",
    ],
    "decision": [
        r"\*\*Decision[:\s]*(.+)",
        r"Decision: (.+)",
    ],
    "outcome": [
        r"\*\*Outcome[:\s]*(.+)",
        r"Outcome: (.+)",
    ],
}


def _mine_patterns(text: str) -> dict[str, str]:
    """Extract structured pattern matches from text."""
    import re

    results = {}
    for pattern_name, pattern_list in _MINING_PATTERNS.items():
        for pat in pattern_list:
            m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
            if m:
                results[pattern_name] = m.group(1).strip()
                break
    return results


def _extract_full_text(entries: list[dict]) -> str:
    """Concatenate all user/assistant message text from transcript entries."""
    parts = []
    for entry in entries:
        entry_type = entry.get("type", "")
        if entry_type not in ("user", "assistant"):
            continue
        msg = entry.get("message", {})
        if isinstance(msg, dict):
            content = msg.get("content", [])
        elif isinstance(msg, str):
            content = msg
        else:
            content = ""

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_result":
                        text = block.get("content", "")
                        if isinstance(text, str):
                            parts.append(text)
        elif isinstance(content, str):
            parts.append(content)

    return "\n".join(parts)


def mine_chain(
    slug: str,
    query: str | None = None,
    max_depth: int = 20,
    use_llm: bool = False,
    start_session_id: str | None = None,
    start_transcript_path: str | None = None,
) -> dict:
    """Walk the chain and mine it for patterns or LLM-based query.

    Args:
        slug: Terminal slug
        query: Optional natural-language query (LLM-based mining)
        max_depth: Maximum chain depth
        use_llm: Whether to use LLM for mining (requires API key)

    Returns:
        dict with 'entries', 'chain', 'mine_results' keys
    """
    chain, origin = get_chain_for_slug(
        slug,
        max_depth=max_depth,
        start_session_id=start_session_id,
        start_transcript_path=start_transcript_path,
    )
    if not chain:
        return {"slug": slug, "entries": [], "chain": [], "mine_results": {}}

    session_ids = [e.session_id for e in chain]

    # Export each session via chscli
    exported = export_chain_via_chscli(session_ids)

    mine_results = {}
    if query:
        # Build combined text from exported chain files
        combined_parts = []
        for ep in exported:
            try:
                combined_parts.append(ep.read_text(encoding="utf-8"))
            except OSError:
                continue

        combined_text = "\n\n---\n\n".join(combined_parts)

        if use_llm:
            try:
                from anthropic import Anthropic

                client = Anthropic()
                response = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=1024,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Query: {query}\n\nChain content:\n{combined_text[:8000]}",
                        }
                    ],
                )
                mine_results["llm_response"] = response.content[0].text
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM mining failed: %s", exc)
                mine_results["llm_error"] = str(exc)
        else:
            mine_results["query"] = query
            mine_results["combined_length"] = len(combined_text)
            mine_results["note"] = "Use --use-llm for full LLM-based extraction"

    else:
        # Pattern-based mining across all chain entries
        all_entries_text = {}
        for entry in chain:
            entries = _parse_transcript_entries(entry.transcript_path)
            text = _extract_full_text(entries)
            patterns = _mine_patterns(text)
            if patterns:
                all_entries_text[entry.session_id] = patterns

        mine_results["patterns"] = all_entries_text

    return {
        "entries": [
            {
                "session_id": e.session_id,
                "transcript_path": str(e.transcript_path),
                "parent_transcript_path": str(e.parent_transcript_path) if e.parent_transcript_path else None,
                "created": e.created,
            }
            for e in chain
        ],
        "chain": session_ids,
        "origin_session_id": origin,
        "mine_results": mine_results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="claude-chain-mine",
        description="Post-compact session chain miner — walks handoff chains, exports and mines session transcripts.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--slug", default=None, help="Terminal slug (default: auto-detect from cwd)")
    parser.add_argument("--mine", default=None, metavar="QUERY", help="Mine chain with query string")
    parser.add_argument("--walk", action="store_true", help="Walk and print chain entries")
    parser.add_argument("--export", action="store_true", help="Export chain via chscli")
    parser.add_argument("--list", action="store_true", help="List available sessions for slug")
    parser.add_argument("--max-depth", type=int, default=20, help="Max chain depth (default: 20)")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for mining (requires ANTHROPIC_API_KEY)")
    parser.add_argument(
        "--transcript-path",
        default=None,
        help="Explicit current transcript path anchor (preferred over mtime guessing)",
    )
    parser.add_argument("--output", default=None, help="Output file for --walk/--mine (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output JSON for --walk/--mine")
    parser.add_argument(
        "--session-id",
        default=None,
        help="Explicit Claude session ID anchor (used to resolve transcript path)",
    )
    parser.add_argument("--fts-index", action="store_true", help="Build FTS5 index over chain exports")
    parser.add_argument("--fts-mine", default=None, metavar="QUERY", help="FTS5 query over indexed chain")
    parser.add_argument("--fts-db", default=None, help="Path to FTS5 database (default: exports/fts-chain.db)")

    args = parser.parse_args()

    if args.slug is None:
        args.slug = get_current_slug()

    logger.info("Using slug: %s", args.slug)

    # --list
    if args.list:
        entries, origin = get_chain_for_slug(
            args.slug,
            max_depth=args.max_depth,
            start_session_id=args.session_id,
            start_transcript_path=args.transcript_path,
        )
        print(f"Chain for slug '{args.slug}':")
        for e in entries:
            print(f"  {e.session_id}  {e.transcript_path}")
        if origin:
            print(f"Origin: {origin}")
        return 0

    # --walk
    if args.walk:
        entries, origin = get_chain_for_slug(
            args.slug,
            max_depth=args.max_depth,
            start_session_id=args.session_id,
            start_transcript_path=args.transcript_path,
        )
        result = {
            "slug": args.slug,
            "origin_session_id": origin,
            "depth": len(entries),
            "entries": [
                {
                    "session_id": e.session_id,
                    "transcript_path": str(e.transcript_path),
                    "parent_transcript_path": str(e.parent_transcript_path) if e.parent_transcript_path else None,
                    "created": e.created,
                }
                for e in entries
            ],
        }
        output = json.dumps(result, indent=2) if args.json else _format_walk_output(result)
        _write_output(output, args.output)
        return 0

    # --mine
    if args.mine:
        result = mine_chain(
            slug=args.slug,
            query=args.mine,
            max_depth=args.max_depth,
            use_llm=args.use_llm,
            start_session_id=args.session_id,
            start_transcript_path=args.transcript_path,
        )
        output = json.dumps(result, indent=2) if args.json else _format_mine_output(result)
        _write_output(output, args.output)
        return 0

    # --export
    if args.export:
        entries, origin = get_chain_for_slug(
            args.slug,
            max_depth=args.max_depth,
            start_session_id=args.session_id,
            start_transcript_path=args.transcript_path,
        )
        if not entries:
            print("No chain found.")
            return 1
        session_ids = [e.session_id for e in entries]
        exported = export_chain_via_chscli(session_ids)
        print(f"Exported {len(exported)} sessions:")
        for ep in exported:
            print(f"  {ep}")
        return 0

    # --fts-index
    if args.fts_index:
        indexed = fts_index_chain(args.slug, db_path=args.fts_db)
        print(f"Indexed {indexed} sessions into FTS5")
        return 0

    # --fts-mine
    if args.fts_mine:
        results = fts_run_mine(
            query=args.fts_mine,
            slug=args.slug,
            db_path=args.fts_db,
        )
        if not results:
            print("No results found.")
            return 1
        print(f"FTS5 results for '{args.fts_mine}':")
        for r in results:
            print(f"  [{r['session_id']}] {r['snippet']}")
        return 0

    # No action specified
    parser.print_help()
    return 0


def _format_walk_output(result: dict) -> str:
    lines = [f"Chain: {result['slug']} (depth={result['depth']}, origin={result['origin_session_id']})", ""]
    for e in result["entries"]:
        lines.append(f"  Session: {e['session_id']}")
        lines.append(f"    Transcript: {e['transcript_path']}")
        if e["parent_transcript_path"]:
            lines.append(f"    Parent:      {e['parent_transcript_path']}")
        if e["created"]:
            lines.append(f"    Created: {e['created']}")
        lines.append("")
    return "\n".join(lines)


def _format_mine_output(result: dict) -> str:
    lines = [f"Chain mining results for: {result['slug']}", ""]
    for sid, data in result.get("mine_results", {}).get("patterns", {}).items():
        lines.append(f"  {sid}:")
        for k, v in data.items():
            lines.append(f"    {k}: {v}")
        lines.append("")
    if "llm_response" in result.get("mine_results", {}):
        lines.append("")
        lines.append("LLM Response:")
        lines.append(result["mine_results"]["llm_response"])
    return "\n".join(lines)


def _write_output(text: str, path: str | None) -> None:
    if path:
        Path(path).write_text(text, encoding="utf-8")
        logger.info("Output written to %s", path)
    else:
        print(text)


if __name__ == "__main__":
    sys.exit(main())
