#!/usr/bin/env python3
"""Pack cc-model-router into a single markdown file for LLM context."""
import ast, pathlib, sys

EXCLUDE_GLOBS = ['__pycache__', '.pytest_cache', '.git', 'venv', '.venv', 'env', 'site-packages', 'dist', 'build', '.mypy_cache', '.ruff_cache']
EXCLUDE_EXTS = {'.pyc', '.pyo', '.so', '.dll', '.exe', '.coverage'}
target = pathlib.Path('P:/packages/.claude-marketplace/plugins/cc-model-router')
py_files = sorted(f for f in target.rglob('*.py') if not any(ex in str(f) for ex in EXCLUDE_GLOBS) and f.suffix not in EXCLUDE_EXTS)
json_files = sorted(f for f in target.iterdir() if f.suffix == '.json')

def get_sigs(path):
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except Exception:
        return ['<parse error>']
    sigs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = []
            for a in node.args.args:
                t = ast.unparse(a.annotation) if a.annotation else ''
                args.append(f'{a.arg}{":" + t if t else ""}')
            ret = ast.unparse(node.returns) if node.returns else ''
            sigs.append(f'def {node.name}({", ".join(args)}) -> {ret}')
        elif isinstance(node, ast.ClassDef):
            sigs.append(f'class {node.name}')
    return sigs

out = sys.stdout
out.write(f'# PACK: cc-model-router\n')
out.write(f'## SIGNATURE TOC\n')
for f in py_files:
    rel = str(f.relative_to(target)).replace('\\', '/')
    sigs = get_sigs(f)
    out.write(f'\n### {rel}\n')
    for s in sigs:
        out.write(f'  {s}\n')

out.write(f'\n## FULL SOURCE\n')
for f in py_files:
    rel = str(f.relative_to(target)).replace('\\', '/')
    content = f.read_text(encoding='utf-8')
    out.write(f'\n### {rel}\n```python\n{content.rstrip()}\n```\n')

for f in json_files:
    rel = str(f.relative_to(target)).replace('\\', '/')
    out.write(f'\n### {rel}\n```json\n{f.read_text(encoding="utf-8").rstrip()}\n```\n')
