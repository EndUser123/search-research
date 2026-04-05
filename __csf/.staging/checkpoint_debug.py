#!/usr/bin/env python3
"""Debug checkpoint restore detection."""
import json
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path("P:/packages/checkpoint/src")))
sys.path.insert(0, str(Path("P:/.claude/hooks")))

# Check what terminal_id would be detected
try:
    from terminal_detection import detect_terminal_id
    terminal_id = detect_terminal_id()
    print(f'Detected terminal_id: {terminal_id}')
except Exception as e:
    print(f'Could not detect terminal_id: {e}')

# Check what checkpoint files exist for this terminal
task_dir = Path('P:/.claude/state/task_tracker')
if task_dir.exists():
    files = list(task_dir.glob('*_tasks.json'))
    print(f'Found {len(files)} task files')

    # Find the most recent ones
    for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
        print(f'\n  {f.name} ({f.stat().st_size} bytes, {f.stat().st_mtime})')

        # Check if it has a continue_session task
        try:
            data = json.loads(f.read_text())
            tasks = data.get('tasks', {})
            has_continue = any(
                isinstance(t, dict) and t.get('subject', '').startswith('continue_session')
                for t in tasks.values()
            )
            print(f'    Has continue_session task: {has_continue}')

            # Show first task subjects
            for task_id, task in list(tasks.items())[:3]:
                if isinstance(task, dict):
                    subject = task.get('subject', '(no subject)')
                    print(f'    - [{task_id}] {subject}')
        except Exception as e:
            print(f'    Error reading: {e}')
