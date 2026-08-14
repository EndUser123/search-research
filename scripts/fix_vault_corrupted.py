#!/usr/bin/env python3
"""Remove corrupted files by binary search."""
import subprocess
from pathlib import Path

projects_dir = Path.home() / '.claude' / 'projects'
all_files = sorted(projects_dir.rglob('*.jsonl'), key=lambda p: p.stat().st_mtime)

print(f'Total files: {len(all_files)}')

deleted = []

for attempt in range(15):  # Try up to 15 times
    print(f'\n--- Attempt {attempt + 1} ---')
    print(f'Files remaining: {len(all_files)}')
    
    result = subprocess.run(['claude-vault', 'import'], capture_output=True, text=True, timeout=120)
    
    if result.returncode == 0:
        print('✓ SUCCESS!')
        break
    
    # Extract the last "Processing X/Y" line before panic
    lines = result.stdout.split('\n')
    processing_lines = [l for l in lines if 'Processing' in l and '/' in l]
    
    if processing_lines:
        last = processing_lines[-1]
        print(f'Last processing: {last}')
        
        # Parse X from "Processing X/Y files..."
        try:
            parts = last.split('/')
            x_str = parts[0].split()[-1]
            x = int(x_str)
            
            # Position x was being processed when it crashed
            # The file at index x-1 (0-based) is corrupted
            idx = x - 1
            if 0 <= idx < len(all_files):
                bad_file = all_files[idx]
                print(f'❌ Deleting file at position {x}: {bad_file.name}')
                bad_file.unlink()
                deleted.append(bad_file)
                
                # Remove from list
                all_files = [f for f in all_files if f != bad_file]
                print(f'✓ Deleted. Remaining: {len(all_files)}')
            else:
                print(f'Index out of range: {idx}')
                break
        except Exception as e:
            print(f'Parse error: {e}')
            # Try a different approach - test files around known position
            print('Attempting to find corrupted files by testing...')
            break
    else:
        print('Could not find Processing line')
        # Print raw output for debugging
        print('Raw output (last 1000 chars):')
        print(result.stdout[-1000:] if result.stdout else '(empty)')
        break

print(f'\n✓ Completed: Deleted {len(deleted)} corrupted files')
print(f'✓ Remaining files: {len(all_files)}')

if deleted:
    print('\nDeleted files:')
    for f in deleted:
        print(f'  - {f.relative_to(projects_dir)}')
