import ast, os
from pathlib import Path

target = Path(r'P:\packages\cc-skills-sdlc')
out_dir = Path(os.environ.get('CLAUDE_ARTIFACTS', r'P:\.claude\.artifacts')) / 'default' / 'gitpack'
out_dir.mkdir(parents=True, exist_ok=True)

name = target.name
sig_out = out_dir / (name + '_sig.md')
full_out = out_dir / (name + '_full.md')

EXCLUDE = {'__pycache__','__pypackages__','.venv','venv','env','.git','.hg','.svn','dist','build','out','target','egg-info','.pytest_cache','.mypy_cache','.ruff_cache','.tox','.idea','.vscode','.DS_Store','Thumbs.db'}

def worth(p):
    parts = p.parts
    if any(e in parts for e in EXCLUDE):
        return False
    if p.suffix in {'.pyc','.pyo','.so','.dll','.exe','.env','.log'}:
        return False
    return True

py_files = sorted([f for f in target.rglob('*.py') if worth(f)])
md_files = sorted([f for f in target.glob('*.md')])

def get_sig(fp):
    try:
        src = fp.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(src, filename=str(fp))
    except:
        return '  [error]'
    lines = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [b.attr if isinstance(b, ast.Attribute) else b.id for b in node.bases if isinstance(b, (ast.Attribute, ast.Name))]
            lines.append('  class ' + node.name + '(' + ', '.join(bases) + ')')
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in item.args.args]
                    try:
                        ret = (' -> ' + ast.unparse(item.returns)) if item.returns else ''
                    except:
                        ret = ''
                    lines.append('    def ' + item.name + '(' + ', '.join(args) + ')' + ret)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            try:
                ret = (' -> ' + ast.unparse(node.returns)) if node.returns else ''
            except:
                ret = ''
            lines.append('  def ' + node.name + '(' + ', '.join(args) + ')' + ret)
    return '\n'.join(lines) if lines else '  (empty)'

# Build signature content
header = '# ' + name + '_sig.md\n\n## PACK INFO\n- Target: ' + str(target) + '\n- Py: ' + str(len(py_files)) + ', MD: ' + str(len(md_files)) + '\n\n## SIGNATURES\n\n'
sig_content = header
full_content = header

for pf in py_files:
    rel = str(pf.relative_to(target))
    sig = get_sig(pf)
    sig_content += '\n### ' + rel + '\n```\n' + sig + '\n```\n'
    try:
        src = pf.read_text(encoding='utf-8', errors='ignore')
    except:
        src = '[error]'
    full_content += '\n### ' + rel + '\n```python\n' + src + '\n```\n'

for mf in md_files:
    rel = str(mf.relative_to(target))
    try:
        content = mf.read_text(encoding='utf-8', errors='ignore')
    except:
        content = '[error]'
    snippet = content[:500] + '...' if len(content) > 500 else content
    sig_content += '\n### ' + rel + '\n```\n' + snippet + '\n```\n'
    full_content += '\n### ' + rel + '\n```\n' + content + '\n```\n'

sig_out.write_text(sig_content, encoding='utf-8')
full_out.write_text(full_content, encoding='utf-8')

import sys
sys.stderr.write('sig: ' + str(sig_out.stat().st_size) + ' bytes\n')
sys.stderr.write('full: ' + str(full_out.stat().st_size) + ' bytes\n')
sys.stderr.write('Py: ' + str(len(py_files)) + ', MD: ' + str(len(md_files)) + '\n')