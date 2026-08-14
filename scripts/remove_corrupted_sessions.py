#!/usr/bin/env python3
"""Identify and remove all corrupted session files preventing claude-vault import."""
import json
import subprocess
from pathlib import Path

projects_dir = Path.home() / '.claude' / 'projects'

# First, get all files and their order
all_files = []
for jsonl_file in sorted(projects_dir.rglob('*.jsonl')):
    all_files.append(jsonl_file)

all_files.sort(key=lambda p: p.stat().st_mtime)

print(f'Total files: {len(all_files)}')
print('Starting corruption detection loop...\n')

removed_count = 0
max_iterations = 10

for iteration in range(max_iterations):
    print(f'--- Iteration {iteration + 1} ---')
    
    # Try import
    result = subprocess.run(['claude-vault', 'import'], capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        print('✓ Import successful!')
        break
    
    # Parse error to find which file failed
    output = result.stdout
    if 'panicked' in output or 'Processing' in output:
        # Extract position from "Processing X/Y files"
        lines = output.strip().split('\n')
        last_processing = [l for l in lines if 'Processing' in l]
        if last_processing:
            print(f'Last: {last_processing[-1]}')
            # Parse the position
            parts = last_processing[-1].split('/')
            if len(parts) >= 2:
                try:
                    current = int(parts[0].split()[-1])
                    total = int(parts[1].split()[0])
                    
                    if current > 0 and current <= len(all_files):
                        corrupt_idx = current - 1
                        corrupt_file = all_files[corrupt_idx]
                        print(f'❌ Corrupted file: {corrupt_file.name}')
                        print(f'   Full path: {corrupt_file}')
                        
                        # Delete it
                        corrupt_file.unlink()
                        print(f'   Deleted!')
                        removed_count += 1
                        
                        # Update the list
                        all_files = [f for f in all_files if f != corrupt_file]
                        print(f'   Remaining files: {len(all_files)}')
                except Exception as e:
                    print(f'Error parsing: {e}')
                    break
    else:
        print('Could not determine error position')
        break
    
    print()

print(f'\n✓ Removed {removed_count} corrupted files')
if len(all_files) > 0:
    print(f'✓ Remaining session files: {len(all_files)}')
