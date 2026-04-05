#!/usr/bin/env python3
"""Verify TASK-013 documentation quality."""

from pathlib import Path

base = Path('P:/.claude/skills')
files = [
    (base / 'plan-workflow' / 'SKILL.md', '## RTM Enforcement in Post-Hoc Verification'),
    (base / 'code' / 'SKILL.md', '## TSR Calculation for Post-Hoc Verification'),
    (base / 'verify' / 'SKILL.md', '## Troubleshooting Post-Hoc Verification')
]

print('TASK-013 Documentation Quality Verification')
print('=' * 60)

for file_path, section_title in files:
    with open(file_path) as f:
        lines = f.readlines()

    # Find section start line
    section_start = None
    for i, line in enumerate(lines):
        if section_title in line:
            section_start = i
            break

    if section_start is None:
        print(f'ERROR: {file_path} - Section not found')
        continue

    # Find section end (next ## at same level or EOF)
    section_end = len(lines)
    for i in range(section_start + 1, len(lines)):
        if lines[i].startswith('## ') and not lines[i].startswith('### '):
            section_end = i
            break

    # Extract section content
    section_lines = lines[section_start:section_end]
    section_text = ''.join(section_lines)

    lines = len(section_lines)
    code_blocks = section_text.count('```') // 2
    subheadings = sum(1 for line in section_lines if line.startswith('###'))

    has_code = code_blocks >= 2
    has_structure = subheadings >= 3
    has_content = lines >= 50

    status = 'PASS' if all([has_code, has_structure, has_content]) else 'REVIEW'

    print(f'{file_path.relative_to(base)}: {status}')
    print(f'  Lines: {lines}')
    print(f'  Code blocks: {code_blocks} (min: 2)')
    print(f'  Subheadings: {subheadings} (min: 3)')
    print()

print('All documentation sections verified.')
