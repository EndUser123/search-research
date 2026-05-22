#!/usr/bin/env python3
"""Inline AST packer for gto and gto_v2 skills."""
from __future__ import annotations

import ast
import os
from pathlib import Path
from datetime import datetime

EXCLUSIONS = {
    '__pycache__', '*.pyc', '*.pyo', '.git', '.venv', 'venv', 'env', 'site-packages',
    'dist', 'build', 'out', 'target', 'egg-info', '.pytest_cache', '.mypy_cache',
    '.ruff_cache', '.tox', '.idea', '.vscode', '.DS_Store', 'Thumbs.db', '.env',
    '.env.*', '*.log'
}


def is_excluded(p: Path) -> bool:
    name = p.name
    for e in EXCLUSIONS:
        if e.startswith('*') and name.endswith(e[1:]):
            return True
        if name == e or f'.{name}' == e:
            return True
    return False


def extract_signatures(filepath: Path) -> list[str]:
    try:
        with open(filepath, encoding='utf-8') as f:
            src = f.read()
        tree = ast.parse(src)
    except Exception:
        return []

    sigs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            ret_str = ''
            if node.returns:
                try:
                    ret_str = f' -> {ast.unparse(node.returns)}'
                except Exception:
                    ret_str = ' -> ...'
            is_prop = any('property' in (ast.get_source_segment(src, d) or '') for d in node.decorator_list)
            if is_prop:
                ret_str = ' -> property'
            sigs.append(f'  def {node.name}({args}){ret_str}')
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in item.args.args if a.arg != 'self']
                    ret = ''
                    if item.returns:
                        try:
                            ret = f' -> {ast.unparse(item.returns)}'
                        except Exception:
                            ret = ' -> ...'
                    methods.append(f'    def {item.name}({args}){ret}')
            if methods:
                sigs.append(f'  class {node.name}:')
                sigs.extend(methods[:10])
    return sigs


def pack_skill(name: str, root_path: Path) -> int:
    out_dir = Path('P:/.claude/.artifacts')
    out_dir.mkdir(parents=True, exist_ok=True)
    out_sig = out_dir / f'{name}_sig.md'
    out_full = out_dir / f'{name}_full.md'

    py_files = [
        p for p in Path(root_path).rglob('*.py')
        if not is_excluded(p) and '__pycache__' not in str(p)
    ]

    sigs_all = []
    file_toc = []

    for pf in sorted(py_files):
        rel = pf.relative_to(root_path).as_posix()
        sigs_all.append(f'\n## {rel}')
        sigs = extract_signatures(pf)
        if sigs:
            sigs_all.extend(sigs)
            sigs_all.append('')
        else:
            sigs_all.append('  (no top-level functions/classes)')
            sigs_all.append('')
        file_toc.append(f'- `{rel}`')

    sig_md = f'''# {name.upper()} — Signature Pack

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Files: {len(py_files)}

## FILE INDEX
'''
    sig_md += '\n'.join(file_toc)
    sig_md += '\n\n## SIGNATURES\n'
    sig_md += '\n'.join(sigs_all)
    sig_md += '\n\n## APPENDIX: FULL SOURCE (see _full.md)'
    out_sig.write_text(sig_md, encoding='utf-8')

    full_md = f'''# {name.upper()} — Full Source Pack

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Files: {len(py_files)}

## FILE INDEX
'''
    full_md += '\n'.join(file_toc)
    full_md += '\n\n## SIGNATURES\n'
    full_md += '\n'.join(sigs_all)
    full_md += '\n\n## APPENDIX: FULL SOURCE\n\n'

    for pf in sorted(py_files):
        rel = pf.relative_to(root_path).as_posix()
        try:
            content = pf.read_text(encoding='utf-8')
        except Exception:
            content = '(error reading file)'
        full_md += f'\n### {rel}\n\n```python\n{content}\n```\n\n'

    out_full.write_text(full_md, encoding='utf-8')
    return len(py_files)


if __name__ == '__main__':
    gto_root = Path('P:/packages/.claude-marketplace/plugins/cc-skills-analysis/skills/gto')
    gto_v2_root = Path('P:/packages/.claude-marketplace/plugins/cc-skills-analysis/skills/gto_v2')

    n1 = pack_skill('gto', gto_root)
    n2 = pack_skill('gto_v2', gto_v2_root)

    print(f'gto: {n1} files -> P:/.claude/.artifacts/gto_sig.md and gto_full.md')
    print(f'gto_v2: {n2} files -> P:/.claude/.artifacts/gto_v2_sig.md and gto_v2_full.md')