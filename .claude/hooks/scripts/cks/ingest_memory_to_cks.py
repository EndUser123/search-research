#!/usr/bin/env python3
r"""
Memory to CKS Ingestion Script
==============================

Ingests memory files from C:/Users/brsth/.claude/projects/P--/memory/
into the Constitutional Knowledge System (CKS) for semantic search.

Usage:
    python P:\.claude\hooks\scripts\ingest_memory_to_cks.py [--test-run]
"""

import sys
from pathlib import Path

# Add CKS core to path (CSF migrated from P:/__csf/src to the search-research plugin)
_csf_src = Path("P:/packages/.claude-marketplace/plugins/search-research/core")
if not _csf_src.exists():
    print(f"❌ CKS core not found at {_csf_src}")
    sys.exit(1)

sys.path.insert(0, str(_csf_src))

try:
    from cks.unified import CKS
except ImportError:
    print(f"❌ Cannot import CKS from {_csf_src}/cks/unified.py")
    sys.exit(1)


# Memory directory
MEMORY_DIR = Path("C:/Users/brsth/.claude/projects/P--/memory")

# Skip these files (index, non-content)
SKIP_FILES = {"MEMORY.md"}

# Map memory files to entry types
ENTRY_TYPE_MAP = {
    # Patterns and best practices
    "questioning_patterns.md": "pattern",
    "working_principles.md": "pattern",
    "discovery_patterns.md": "pattern",
    "learning_patterns.md": "pattern",
    "testing_patterns.md": "pattern",
    "test_isolation_patterns.md": "pattern",
    "tool_usage_patterns.md": "pattern",
    "lazy_patterns.md": "pattern",
    "reasoning_flaws.md": "pattern",
    "behavioral_principles.md": "pattern",
    "debugging_protocol_architecture.md": "pattern",
    "integration_verification.md": "pattern",
    "memory_safeguards.md": "pattern",
    "memory_management.md": "pattern",

    # Architecture and docs
    "hook_architecture.md": "knowledge",
    "hooks_conceptual_guide.md": "knowledge",
    "hooks_operational_guide.md": "knowledge",
    "hook_debugging_lessons.md": "knowledge",
    "constitution.md": "knowledge",
    "workflow_clarification.md": "knowledge",

    # Bug fixes and corrections
    "bugfixes.md": "correction",
    "claude_code_cli_issues.md": "correction",
    "mcp_consolidation.md": "correction",
    "mcp_design_lessons.md": "correction",
    "process_improvements.md": "correction",
    "refactor_plan_review.md": "correction",
    "proactive-honesty.md": "correction",

    # Knowledge and references
    "api_integration_best_practices.md": "knowledge",
    "windows_mcp_patterns.md": "knowledge",
    "mcp_zai_integration.md": "knowledge",
    "verification_tiers.md": "knowledge",
    "display_templates.md": "knowledge",
    "aid_files.md": "knowledge",
    "chutes_provider.md": "knowledge",
    "recruiter_perception.md": "knowledge",
    "registry-integration-verification.md": "knowledge",

    # Technical guidance
    "pytest_stuck_prevention.md": "knowledge",
    "markdown-rendering-practice.md": "knowledge",
    "feedback_skill_first_slash_commands.md": "knowledge",
    "cognitive_frameworks_integration.md": "knowledge",
}


def chunk_by_headers(content: str, filename: str) -> list[tuple[str, str]]:
    """Chunk markdown content by ## headers.

    Returns:
        List of (title, content) tuples for each chunk
    """
    chunks = []

    # Get file-level title from first # header
    lines = content.split('\n')
    file_title = filename
    for line in lines:
        if line.startswith('#'):
            file_title = line.lstrip('#').strip()
            break

    # Split by ## headers
    current_chunk = []
    current_title = file_title
    in_code_block = False

    for line in content.split('\n'):
        # Track code blocks (don't split inside them)
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            current_chunk.append(line)
            continue

        # ## header (but not inside code block)
        if not in_code_block and line.startswith('## '):
            # Save previous chunk if non-empty
            if current_chunk:
                chunk_content = '\n'.join(current_chunk).strip()
                if chunk_content:
                    chunks.append((current_title, chunk_content))

            # Start new chunk
            current_title = line.lstrip('#').strip()
            current_chunk = []
        else:
            current_chunk.append(line)

    # Don't forget the last chunk
    if current_chunk:
        chunk_content = '\n'.join(current_chunk).strip()
        if chunk_content:
            chunks.append((current_title, chunk_content))

    return chunks


def ingest_memory_file(filepath: Path, cks: CKS, test_run: bool = False) -> dict:
    """Ingest a single memory file into CKS.

    Returns:
        Dict with ingestion stats
    """
    filename = filepath.name

    if filename in SKIP_FILES:
        return {"skipped": True, "reason": "index file"}

    entry_type = ENTRY_TYPE_MAP.get(filename, "knowledge")

    try:
        content = filepath.read_text(encoding="utf-8")

        # Check file size
        if len(content) < 500:
            # Small file - ingest as single entry
            title = f"{filename}: {filepath.stem.replace('_', ' ').title()}"
            if not test_run:
                cks.ingest_pattern(title, content, metadata={"source_file": str(filepath)})
            return {"chunks": 1, "type": entry_type}

        # Large file - chunk by headers
        chunks = chunk_by_headers(content, filename)

        if not chunks:
            return {"skipped": True, "reason": "no chunks found"}

        if not test_run:
            for chunk_title, chunk_content in chunks:
                full_title = f"{filename}: {chunk_title}"
                cks.ingest_pattern(
                    full_title,
                    chunk_content,
                    metadata={"source_file": str(filepath), "chunk_title": chunk_title}
                )

        return {"chunks": len(chunks), "type": entry_type}

    except Exception as e:
        return {"error": str(e), "type": entry_type}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Ingest memory files into CKS")
    parser.add_argument("--test-run", action="store_true", help="Parse files without ingesting")
    parser.add_argument("--file", type=str, help="Ingest only specific file")
    args = parser.parse_args()

    if not MEMORY_DIR.exists():
        print(f"❌ Memory directory not found: {MEMORY_DIR}")
        sys.exit(1)

    # Collect memory files
    if args.file:
        memory_files = [MEMORY_DIR / args.file]
        if not memory_files[0].exists():
            print(f"❌ File not found: {memory_files[0]}")
            sys.exit(1)
    else:
        memory_files = [f for f in MEMORY_DIR.glob("*.md") if f.name not in SKIP_FILES]

    print(f"📚 Found {len(memory_files)} memory files to process")

    if args.test_run:
        print("🧪 TEST RUN - No actual ingestion")

    # Ingest files
    stats = {
        "total": len(memory_files),
        "success": 0,
        "skipped": 0,
        "errors": 0,
        "chunks": 0,
        "by_type": {}
    }

    try:
        with CKS() as cks:
            for filepath in memory_files:
                result = ingest_memory_file(filepath, cks, test_run=args.test_run)

                if "error" in result:
                    print(f"  ❌ {filepath.name}: {result['error']}")
                    stats["errors"] += 1
                elif result.get("skipped"):
                    print(f"  ⏭️  {filepath.name}: {result['reason']}")
                    stats["skipped"] += 1
                else:
                    chunks = result.get("chunks", 1)
                    entry_type = result.get("type", "unknown")
                    print(f"  ✅ {filepath.name}: {chunks} chunk(s) as {entry_type}")
                    stats["success"] += 1
                    stats["chunks"] += chunks
                    stats["by_type"][entry_type] = stats["by_type"].get(entry_type, 0) + chunks

    except Exception as e:
        print(f"❌ CKS error: {e}")
        sys.exit(1)

    # Print summary
    print("\n📊 Summary:")
    print(f"  Files processed: {stats['success']}/{stats['total']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Total chunks: {stats['chunks']}")
    print(f"  By type: {stats['by_type']}")

    if args.test_run:
        print("\n✅ Test run complete. To ingest, run:")
        print(f"  python {' '.join(sys.argv)}".replace(" --test-run", ""))


if __name__ == "__main__":
    main()
