#!/usr/bin/env python3
"""Ingest Claude Hooks documentation into CKS.

Usage:
    python scripts/ingest_hooks_doc_to_cks.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.cks.unified import CKS


def chunk_markdown(text: str, max_chunk_size: int = 2000) -> list[tuple[str, str]]:
    """Split markdown into (title, content) chunks.

    Uses headings as chunk boundaries to keep related content together.
    Returns list of (section_title, chunk_content) tuples.
    """
    chunks = []

    # Split on H2 headings (##)
    sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)

    current_title = "Introduction"
    current_content = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Check if starts with H2
        heading_match = re.match(r"^(##\s+[^\n]+)\n", section)
        if heading_match:
            title = heading_match.group(1).replace("## ", "").strip()

            # Save previous chunk if exists
            if current_content.strip():
                chunks.append((current_title, current_content.strip()))

            current_title = title
            remaining = section[len(heading_match.group(0)):]
            current_content = remaining
        else:
            current_content += "\n" + section

    # Don't forget last chunk
    if current_content.strip():
        chunks.append((current_title, current_content.strip()))

    # Further split large chunks
    final_chunks = []
    for title, content in chunks:
        if len(content) <= max_chunk_size:
            final_chunks.append((title, content))
        else:
            # Split by paragraphs within the chunk
            paragraphs = content.split("\n\n")
            current = ""
            for para in paragraphs:
                if len(current) + len(para) + 2 <= max_chunk_size:
                    current += ("\n\n" if current else "") + para
                else:
                    if current:
                        final_chunks.append((title, current.strip()))
                    current = para
            if current.strip():
                final_chunks.append((title, current.strip()))

    return final_chunks


def main() -> int:
    doc_path = Path("P:/.claude/docs/claude-hooks-v3.1.md")
    if not doc_path.exists():
        print(f"ERROR: File not found: {doc_path}")
        return 1

    content = doc_path.read_text(encoding="utf-8")

    # Extract frontmatter and body
    frontmatter_match = re.match(r"^---\n.*?\n---\n", content, re.DOTALL)
    if frontmatter_match:
        body = content[frontmatter_match.end():]
    else:
        body = content

    # Extract title from first heading
    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    doc_title = title_match.group(1) if title_match else "Claude Code Hooks Guide"

    # Extract version
    version_match = re.search(r"\*\*v([\d.]+)\s*\|", body)
    version = version_match.group(1) if version_match else "3.1"

    chunks = chunk_markdown(body)

    print(f"Claude Code Hooks Guide v{version}")
    print(f"Total chunks: {len(chunks)}")
    print()

    ingested = 0
    with CKS() as cks:
        for i, (section_title, chunk_content) in enumerate(chunks):
            entry_id = cks.ingest_pattern(
                title=f"[hooks] {section_title}",
                content=chunk_content,
                entry_type="pattern",
                source_chunk=f"claude hooks v{version} documentation",
                category="DOCUMENTATION",
                skill_source="docs",
                doc_version=version,
                doc_section=section_title,
                chunk_index=i,
                total_chunks=len(chunks),
            )
            print(f"  [{i+1}/{len(chunks)}] {section_title[:60]:60s} -> {entry_id}")
            ingested += 1

    print()
    print(f"Done. Ingested {ingested} chunks into CKS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
