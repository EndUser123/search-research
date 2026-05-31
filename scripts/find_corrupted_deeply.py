#!/usr/bin/env python3
"""Find the corrupted session file at position 140."""
import json
from pathlib import Path

projects_dir = Path.home() / '.claude' / 'projects'
all_files = []

# Collect all .jsonl files recursively
for jsonl_file in sorted(projects_dir.rglob('*.jsonl')):
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
        with open(test_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            print(f'Total lines: {len(lines)}')
            
            # Try parsing each line
            corrupted = False
            for i, line in enumerate(lines, 1):
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    print(f'❌ CORRUPTED at line {i}: {str(e)[:100]}')
                    print(f'  Line content: {line[:200]}...')
                    corrupted = True
                    break
            
            if not corrupted:
                print('✓ All lines parse successfully')
    except Exception as e:
        print(f'Error reading file: {e}')
else:
    print(f'Not enough files. Total: {len(all_files)}')

# Show files around position 140
print(f'\nFiles near position 140:')
for i in range(max(0, 135), min(len(all_files), 145)):
    f = all_files[i]
    try:
        size = f.stat().st_size
        # Quick validation - just check first line
        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
            first_line = fh.readline()
            try:
                json.loads(first_line)
                status = '✓'
            except:
                status = '❌'
    except:
        status = '❌'
        size = 0
    
    rel_path = str(f.relative_to(projects_dir))
    print(f'{i+1:3d}: {status} {rel_path}')
