#!/usr/bin/env bash
# Build NotebookLM-ready file lists under notebooklm/
# Idempotent: safe to run multiple times. Uses set -euo pipefail.
set -euo pipefail

NOTEBOOKLM_DIR="notebooklm"
mkdir -p "$NOTEBOOKLM_DIR"

# ---------------------------------------------------------------------------
# 1. High-signal repo file list  (exclude tests, binaries, lockfiles)
# ---------------------------------------------------------------------------
{
    # Files tracked by git, excluding test/binary directories
    git ls-files -z | grep -zEv '(
        ^tests/ |
        ^__tests__/ |
        ^__snapshots__/ |
        ^__mocks__/ |
        /\.pytest_cache/ |
        /node_modules/ |
        \.png$ |
        \.jpg$ |
        \.jpeg$ |
        \.gif$ |
        \.lock$ |
        \.bin$ |
        \.pyc$ |
        \.pyo$ |
        \.so$ |
        \.dll$ |
        \.exe$
    )' | grep -zv '/\.' | sort
} > "$NOTEBOOKLM_DIR/file-list.txt"

# ---------------------------------------------------------------------------
# 2. Agent / config file list
# ---------------------------------------------------------------------------
{
    # Global config at repo root
    for f in CLAUDE.md AGENTS.md .mcp.json; do
        [ -e "$f" ] && echo "$f"
    done
    # Everything under .claude/ that is a config or code file (not .evidence, etc.)
    find .claude -type f -not -path '*/\.*' -not -path '*/.evidence/*' 2>/dev/null | sort
    find .claude -type f -name '*.md' -not -path '*/.evidence/*' 2>/dev/null | sort
} > "$NOTEBOOKLM_DIR/agent-config-files.txt"

# ---------------------------------------------------------------------------
# 3. Docs file list
# ---------------------------------------------------------------------------
{
    # docs/ tree
    find docs/ -type f 2>/dev/null | sort
    # README variants at repo root
    find . -maxdepth 1 -type f -name 'README*' 2>/dev/null | sort
    # markdown files at root level that are clearly docs (skip generated/dumps)
    find . -maxdepth 1 -type f -name '*.md' \
        ! -name 'CLAUDE.md' \
        ! -name 'AGENTS.md' \
        ! -name '.mcp.json' \
        2>/dev/null | sort
} > "$NOTEBOOKLM_DIR/doc-files.txt"

echo "notebooklm/file-list.txt        ($(wc -l < "$NOTEBOOKLM_DIR/file-list.txt") entries)"
echo "notebooklm/agent-config-files.txt ($(wc -l < "$NOTEBOOKLM_DIR/agent-config-files.txt") entries)"
echo "notebooklm/doc-files.txt         ($(wc -l < "$NOTEBOOKLM_DIR/doc-files.txt") entries)"
