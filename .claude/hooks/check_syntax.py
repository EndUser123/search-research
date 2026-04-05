#!/usr/bin/env python3
import py_compile
from pathlib import Path

hooks_dir = Path('P:/.claude/hooks')
broken = []
checked = 0

for hook_file in hooks_dir.rglob('*.py'):
    path_str = str(hook_file)
    normalized = path_str.replace('\\', '/')
    if (hook_file.name.startswith('__')
        or 'tests' in normalized
        or '.migration_backup' in path_str
        or 'archive' in normalized):
        continue

    checked += 1
    try:
        py_compile.compile(str(hook_file), doraise=True)
    except py_compile.PyCompileError as e:
        error_msg = str(e).split('\n')[-1] if '\n' in str(e) else str(e)
        broken.append(f'{hook_file.name}: {error_msg[:100]}')

print(f'Checked: {checked}')
print(f'Broken: {len(broken)}')
for b in broken[:20]:
    print(f'  {b}')
