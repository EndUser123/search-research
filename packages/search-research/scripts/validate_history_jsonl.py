#!/usr/bin/env python3
"""Validate history.jsonl for corruption."""
import json
from pathlib import Path

history_file = Path.home() / '.claude' / 'history.jsonl'

if not history_file.exists():
    print(f"File not found: {history_file}")
    exit(1)

print(f"Checking {history_file} for corruption...")
print(f"File size: {history_file.stat().st_size} bytes\n")

corrupted_lines = []
total_lines = 0

with open(history_file, 'r', encoding='utf-8', errors='replace') as f:
    for line_num, line in enumerate(f, 1):
        total_lines = line_num
        if not line.strip():
            continue
        
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            corrupted_lines.append((line_num, str(e)[:80], line[:100]))

print(f"Total lines: {total_lines}")

if corrupted_lines:
    print(f"\n⚠️  FOUND {len(corrupted_lines)} CORRUPTED LINES:\n")
    for line_num, error, snippet in corrupted_lines[:10]:  # Show first 10
        print(f"Line {line_num}: {error}")
        print(f"  Snippet: {snippet}...\n")
    
    if len(corrupted_lines) > 10:
        print(f"... and {len(corrupted_lines) - 10} more")
else:
    print("✓ All lines are valid JSON")

# If corrupted lines found, the issue is likely around line 10 of history (140 - 130 projects)
# Check which session files are processed first
project_files = []
projects_dir = Path.home() / '.claude' / 'projects'
for proj_dir in projects_dir.glob('*'):
    if proj_dir.is_dir():
        for jsonl_file in proj_dir.glob('*.jsonl'):
            project_files.append(jsonl_file)

project_files.sort(key=lambda p: p.stat().st_mtime)
print(f"\nProject files processed ({len(project_files)} total):")
for i, f in enumerate(project_files[:20], 1):
    print(f"{i:3d}: {f.name}")
