"""note_writer.py - /note and /keep write-side module.

CLI for the CKS deliberate-write path. Both /note and /keep resolve to this
module's CLI. The skill's SKILL.md drives the dry-run + confirm flow at the
model layer; this module is the deterministic ingest.

Run from the cache-resolved plugin root:

    python -m skills.note.note_writer --title "Use CKS for decisions" --body "..." --type pattern
    python -m skills.keep.note_writer --title "..." --body "..." --type memory
    python -m skills.note.note_writer --help

The module re-exports from skills/note/note_writer.py via skills/keep/note_writer.py
so both skill dirs resolve the same code.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal

# Make the plugin root importable so `from core.cks.unified import CKS` resolves
# regardless of where this module is invoked from.
_HERE = Path(__file__).resolve()
_PLUGIN_ROOT = _HERE.parents[2]  # skills/note/note_writer.py -> skills/note -> skills -> <plugin_root>
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from core.cks.unified import CKS  # noqa: E402

# Mirrors the canonical CKS entry-type vocabulary. Kept here (not imported
# from CKS internals) so note_writer stays decoupled from CKS class refactors.
EntryType = Literal["memory", "pattern", "correction", "decision", "insight", "code", "knowledge"]
_VALID_TYPES: tuple[str, ...] = ("memory", "pattern", "correction", "decision", "insight", "code")


def render_preview(title: str, body: str, entry_type: str) -> str:
    """Format the dry-run preview shown to the user before ingest.

    Kept as a pure function so it's trivially testable and the model layer
    (which follows the SKILL.md workflow) can show a deterministic preview
    before invoking the actual ingest path.
    """
    safe_title = (title or "").strip() or "(untitled)"
    safe_body = (body or "").strip()
    body_preview = safe_body if len(safe_body) <= 240 else safe_body[:237] + "..."
    return (
        f"  type:    {entry_type}\n"
        f"  title:   {safe_title}\n"
        f"  body:    {body_preview}\n"
    )


def ingest(title: str, body: str, entry_type: str, source: str = "skill:/note") -> str:
    """Perform the actual CKS ingest. Returns the entry id.

    Routing per CKS unified API:
        memory     -> cks.ingest_memory(question=title, answer=body)
        pattern    -> cks.ingest_pattern(title=title, content=body, entry_type="pattern")
        code       -> cks.ingest_pattern(title=title, content=body, entry_type="code")
        correction -> cks.ingest_correction(title=title, content=body)
        decision   -> cks.ingest_decision(title=title, content=body)
        insight    -> cks.ingest_insight(title=title, content=body)
        knowledge  -> cks.ingest_pattern(title=title, content=body, entry_type="knowledge")

    `source` is recorded in metadata for retrieval-by-source later.
    """
    if not title or not title.strip():
        raise SystemExit("error: --title is required (non-empty)")
    if not body or not body.strip():
        raise SystemExit("error: --body is required (non-empty)")
    if entry_type not in _VALID_TYPES:
        raise SystemExit(
            f"error: --type must be one of {_VALID_TYPES}; got {entry_type!r}"
        )

    title = title.strip()
    body = body.strip()
    metadata = {"source": source, "entry_source": "skill-note-or-keep"}

    with CKS() as cks:
        if entry_type == "memory":
            return cks.ingest_memory(question=title, answer=body, **metadata)
        if entry_type == "pattern":
            return cks.ingest_pattern(
                title=title, content=body, entry_type="pattern", **metadata
            )
        if entry_type == "code":
            return cks.ingest_pattern(
                title=title, content=body, entry_type="code", **metadata
            )
        if entry_type == "correction":
            return cks.ingest_correction(title=title, content=body, **metadata)
        if entry_type == "decision":
            return cks.ingest_decision(title=title, content=body, **metadata)
        if entry_type == "insight":
            return cks.ingest_insight(title=title, content=body, **metadata)
        # Reachable in practice only if entry_type is added to _VALID_TYPES above.
        raise SystemExit(f"error: unhandled type {entry_type!r}")  # pragma: no cover


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="note_writer",
        description=(
            "Deliberate CKS write path for /note and /keep skills. "
            "Run with --dry-run to preview without ingesting. "
            "Pipe --body from stdin if --body-file omitted."
        ),
    )
    parser.add_argument("--title", required=False, default=None, help="CKS entry title")
    parser.add_argument(
        "--body", default=None, help="Inline body text. Mutually exclusive with --body-file and stdin."
    )
    parser.add_argument(
        "--body-file",
        type=Path,
        default=None,
        help="Read body from a file. Use '-' to read from stdin.",
    )
    parser.add_argument(
        "--type",
        dest="entry_type",
        choices=_VALID_TYPES,
        default="memory",
        help="CKS entry type. Default: memory.",
    )
    parser.add_argument("--source", default="skill:/note", help="Provenance tag for retrieval.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the preview that would be ingested; do not write to CKS.",
    )
    args = parser.parse_args(argv)

    # Body resolution: --body > --body-file > stdin
    body: str | None = args.body
    if body is None and args.body_file is not None:
        if str(args.body_file) == "-":
            body = sys.stdin.read()
        else:
            body = args.body_file.read_text(encoding="utf-8")
    if body is None and not sys.stdin.isatty():
        # Fall back to stdin if no --body / --body-file given AND stdin piped.
        body = sys.stdin.read()

    if args.title is None:
        parser.error("the following argument is required: --title")
    if body is None or not body.strip():
        parser.error("--body (or --body-file, or stdin) is required and must be non-empty")

    if args.dry_run:
        sys.stdout.write("--- DRY RUN (no CKS write) ---\n")
        sys.stdout.write(render_preview(args.title, body, args.entry_type))
        sys.stdout.write("--- end ---\n")
        return 0

    entry_id = ingest(
        title=args.title, body=body, entry_type=args.entry_type, source=args.source
    )
    sys.stdout.write(f"ok: ingested {args.entry_type} entry {entry_id}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
