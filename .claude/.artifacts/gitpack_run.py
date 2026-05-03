#!/usr/bin/env python3
"""gitpack inline packer for claude.md + /git skill"""
import ast, os, sys
from pathlib import Path

TARGETS = [
    Path('P:/.claude/CLAUDE.md'),
    Path('P:/packages/.claude-marketplace/plugins/cc-skills-utils/skills/git'),
]
OUT = Path('P:/.claude/.artifacts')
OUT.mkdir(parents=True, exist_ok=True)

EXCLUDE = {'__pycache__', '.pytest_cache', '.git', 'node_modules', '.venv', 'venv', 'site-packages'}

def ast_dump(path):
    results = {}
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'), path.name)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                rets = getattr(node.returns, 'id', None) or str(node.returns) if node.returns else None
                results[f'def {node.name}({args}) -> {rets}'] = str(path)
            elif isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                results[f'class {node.name}({methods})'] = str(path)
    except Exception:
        pass
    return results

sig_lines = ['# SIGNATURE TOC\n']
full_lines = ['# FULL IMPLEMENTATIONS\n']

for target in TARGETS:
    if target.is_file() and target.suffix == '.md':
        content = target.read_text(encoding='utf-8')
        sig_lines.append(f'\n## {target.name}\n```\n{content[:3000]}\n```\n')
        full_lines.append(f'\n## {target.name}\n{content}\n')
    elif target.is_dir():
        for f in target.rglob('*.py'):
            if any(e in f.parts for e in EXCLUDE):
                continue
            sigs = ast_dump(f)
            for sig, src in sigs.items():
                sig_lines.append(f'- {sig} [{src}]\n')
            src = f.read_text(encoding='utf-8')
            full_lines.append(f'\n## {f.relative_to(target)}\n```python\n{src}\n```\n')

(OUT / 'gitpack_sig.md').write_text(''.join(sig_lines), encoding='utf-8')
(OUT / 'gitpack_full.md').write_text(''.join(full_lines), encoding='utf-8')
print(f'Written: {OUT / "gitpack_sig.md"} and {OUT / "gitpack_full.md"}')