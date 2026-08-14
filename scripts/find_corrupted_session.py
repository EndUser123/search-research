#!/usr/bin/env python3
"""Find and report the corrupted session file causing claude-vault crash."""
import json
from pathlib import Path

projects_dir = Path.home() / '.claude' / 'projects'
all_files = []

# Collect all .jsonl files from all project directories
for proj_dir in projects_dir.glob('*'):
    if proj_dir.is_dir():
        for jsonl_file in proj_dir.glob('*.jsonl'):
            all_files.append(jsonl_file)

# Sort by modification time (how claude-vault likely processes them)
all_files.sort(key=lambda p: p.stat().st_mtime)

print(f'Total session files found: {len(all_files)}')

# Check file 140 (0-indexed = 139)
if len(all_files) > 139:
    test_file = all_files[139]
    print(f'\nFile #140: {test_file.name}')
    print(f'Full path: {test_file}')
    print(f'Size: {test_file.stat().st_size} bytes')
    
    # Try to validate the file
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f'Total lines: {len(lines)}')
            
            # Try parsing each line
            for i, line in enumerate(lines, 1):
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    print(f'❌ CORRUPTED at line {i}: {str(e)[:100]}')
                    print(f'  Line content: {line[:200]}...')
                    break
            else:
                print('✓ All lines parse successfully')
    except Exception as e:
        print(f'Error reading file: {e}')
else:
    print(f'Not enough files. Total: {len(all_files)}')

# Also check files around position 140
print(f'\nFiles near position 140:')
for i in range(max(0, 135), min(len(all_files), 145)):
    f = all_files[i]
    try:
        size = f.stat().st_size
        # Quick validation
        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
            lines = fh.readlines()
            status = '✓' if all(json.loads(line) or True for line in lines[:1]) else '❌'
    except:
        status = '❌'
        lines = ['error']
    print(f'{i+1:3d}: {status} {f.name} ({size} bytes, {len(lines)} lines)')
