"""Shim re-exporting skills.note.note_writer so /keep and /note share one module.

This file exists only because the harness makes /keep a separate command by
way of the `name: keep` frontmatter. All actual logic lives in
skills/note/note_writer.py.
"""
from skills.note.note_writer import main  # noqa: F401

if __name__ == "__main__":
    import sys
    sys.exit(main())
