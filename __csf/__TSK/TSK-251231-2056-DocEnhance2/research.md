# Research: Documentation Enhancements Phase 2

## Existing Patterns in Doc System

### Current Enhancement Classes (from Phase 1)
Located in `src/modules/document_system/doc_suggest_agent.py`:

```python
# Pattern: All detectors take repo_root and cache results
class RevertDetector:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self._revert_cache: dict[str, list[str]] = {}

class ConventionalCommitsMapper:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self._commit_cache: dict[str, dict[str, Any]] = {}

# Pattern: Validators check specific quality aspects
class XRefValidator:
    MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    def validate_references(self, doc_file: Path) -> list[dict[str, Any]]
```

### CLI Integration Pattern
Located in `src/commands/nip/doc_command.py`:

```python
# Flag registration pattern
parser.add_argument(
    "--autodoc",
    nargs="?",
    const="docs/api",
    help="Generate API documentation using lazydocs",
)

# Handler pattern in run()
async def run(self, args: argparse.Namespace) -> int:
    if args.autodoc is not None:
        return await self._generate_api_docs(args)
```

## CKS Integration Research

### CKS Database Location
- Path: `P:/__csf.nip/data/cks.db`
- Need to verify schema for search functionality

### Existing CKS Usage Patterns
From codebase search:

```python
# CKS is used via ConsolidatedKnowledgeSystem
from modules.cks.consolidated_knowledge_system import ConsolidatedKnowledgeSystem

cks = ConsolidatedKnowledgeSystem()
results = cks.search(query)
```

**Decision**: Use `ConsolidatedKnowledgeSystem` for FR-004 rather than direct DB access.

## Python AST Patterns for Docstrings

### Standard Library Approach
```python
import ast

def extract_docstrings(file_path: Path) -> dict:
    """Extract docstrings from Python file."""
    with open(file_path) as f:
        tree = ast.parse(f.read())

    result = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            name = getattr(node, 'name', 'module')
            docstring = ast.get_docstring(node)
            if docstring:
                result[name] = {
                    'docstring': docstring,
                    'lineno': node.lineno,
                    'type': type(node).__name__
                }
    return result
```

### Public vs Private Detection
```python
def is_public_api(name: str) -> bool:
    """Determine if a name is a public API."""
    return not name.startswith('_')
```

## Git Diff Patterns for API Changes

### Signature Change Detection
```python
def detect_signature_changes(old_ref: str, new_ref: str) -> list:
    """Detect function signature changes between refs."""
    import subprocess

    # Get diff of Python files
    result = subprocess.run([
        'git', 'diff', '-U0', old_ref, new_ref, '--', '*.py'
    ], capture_output=True, text=True)

    # Parse for def/function changes
    pattern = re.compile(r'^[\+\-]\s*def\s+(\w+)\s*\((.*?)\):')
    changes = []
    for line in result.stdout.split('\n'):
        match = pattern.match(line)
        if match:
            changes.append({
                'name': match.group(1),
                'signature': match.group(2),
                'added': line.startswith('+')
            })
    return changes
```

### Breaking Change Indicators
- Removed parameters (in `-` lines, not in `+` lines)
- Changed parameter types (for typed code)
- Changed return types
- Removed functions/classes

## Markdown Preview Options

### Option 1: `markdown` Package
```python
import markdown

def render_markdown(content: str) -> str:
    """Render markdown to HTML."""
    md = markdown.Markdown(extensions=['fenced_code', 'tables'])
    return md.convert(content)
```

### Option 2: Basic Rendering (fallback)
If `markdown` unavailable, use basic regex for link validation.

## Docstring Format Detection

### Google Style
```python
def func(arg1: str, arg2: int) -> bool:
    """Summary line.

    Args:
        arg1: Description of arg1.
        arg2: Description of arg2.

    Returns:
        Description of return value.
    """
```

### NumPy Style
```python
def func(arg1: str, arg2: int) -> bool:
    """Summary line.

    Parameters
    ----------
    arg1 : str
        Description of arg1.
    arg2 : int
        Description of arg2.

    Returns
    -------
    bool
        Description of return value.
    """
```

### Detection Strategy
```python
def detect_docstring_style(docstring: str) -> str:
    """Auto-detect docstring format."""
    if 'Args:' in docstring or 'Returns:' in docstring:
        return 'google'
    elif 'Parameters' in docstring or 'Returns' in docstring:
        return 'numpy'
    elif ':param' in docstring or ':return:' in docstring:
        return 'sphinx'
    else:
        return 'unknown'
```

## External Dependencies

| Package | Install Command | Required For |
|---------|-----------------|--------------|
| `markdown` | `pip install markdown` | Preview rendering |
| `pyspellchecker` | `pip install pyspellchecker` | Spell checking |
| `rich` | Already in project | Pretty output |

## Similar Tools (for reference)

| Tool | Features | Notes |
|------|----------|-------|
| `interrogate` | Coverage reports | MIT licensed, can借鉴patterns |
| `pydocstyle` | Docstring style checking | PEP 257 compliant |
| `docstr-coverage` | Coverage metrics | Simple, focused |
| `pylint` | General linting with docstring checks | Heavy dependency |

**Decision**: Build focused, lightweight implementations rather than import heavy tools.

## Implementation Insights

### 1. Coverage Report
- Use `ast` module for parsing
- Count functions/classes with/without docstrings
- Report by module and overall

### 2. Docstring Checker
- Detect style first (Google/NumPy/Sphinx)
- Validate required sections based on signature
- Flag common placeholders

### 3. Preview
- Try `markdown` package, fallback to basic
- Validate links using `XRefValidator` (already exists!)
- Check code blocks for valid syntax highlighting spec

### 4. Search
- Use `ConsolidatedKnowledgeSystem.search()`
- Add document type filter
- Return results with file paths

### 5. API Diff
- Use git diff with `-U0` for minimal context
- Parse both `+` and `-` lines for signatures
- Compare to detect breaking changes

### 6. Linter
- Spell check: try `pyspellchecker`, skip if unavailable
- Structure: validate heading hierarchy (multiple `#` in sequence)
- Terminology: configurable word list for consistency

## Gotchas Found

1. **Docstring extraction**: `ast.get_docstring()` returns `None` if no docstring, handle this
2. **Git diff parsing**: Function definitions can span multiple lines in diff
3. **CKS availability**: Database may not exist, handle gracefully
4. **Optional dependencies**: Don't hard-fail if `markdown` or `pyspellchecker` missing

## Reusable Code from Phase 1

| Component | File | Reuse For |
|-----------|------|-----------|
| `XRefValidator` | `doc_suggest_agent.py` | Link validation in preview |
| `ChangelogSummarizer` | `doc_suggest_agent.py` | Categorize API changes |
| `_find_repo_root()` | `doc_suggest_agent.py` | Git operations |
| Pattern: `_cache` attributes | All detector classes | Performance optimization |
