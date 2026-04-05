# Architecture Design: Documentation Enhancements Phase 2

## Components

### 1. DocCoverageReporter
```python
class DocCoverageReporter:
    """Generate documentation coverage metrics."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self._ast_cache: dict[Path, ast.Module] = {}

    def generate_coverage_report(self, paths: list[Path] | None = None) -> CoverageReport:
        """Generate comprehensive coverage report.

        Returns CoverageReport with:
            - overall_coverage: float (percentage)
            - by_module: dict[str, ModuleCoverage]
            - undocumented_apis: list[str] (public APIs without docs)
            - trend_data: dict | None (if git history available)
        """
```

### 2. DocstringQualityChecker
```python
class DocstringQualityChecker:
    """Validate docstring quality and format."""

    STYLE_PATTERNS = {
        "google": {"args": r"Args:\s*\n", "returns": r"Returns:\s*\n"},
        "numpy": {"params": r"Parameters\s*\n-+\s*\n", "returns": r"Returns\s*\n-+\s*\n"},
        "sphinx": {"params": r":param", "returns": r":return:"}
    }

    PLACEHOLDER_PATTERNS = [
        r"^(TODO|FIXME|XXX|XXX|TBD)\b",
        r"^\.{3,}$",
        r"^(pass|none|n/a)\b",
        r"^NotImplementedError\b"
    ]

    def __init__(self, style: str | None = None, repo_root: Path | None = None) -> None:
        self._style = style
        self._repo_root = repo_root or Path.cwd()

    def check_file(self, path: Path) -> list[DocstringIssue]:
        """Check all docstrings in a file.

        Returns list of DocstringIssue:
            - lineno: int
            - name: str (function/class name)
            - type: str (missing, empty, placeholder, format, missing_section)
            - message: str (description)
            - suggestion: str | None (how to fix)
        """
```

### 3. DocPreviewGenerator
```python
class DocPreviewGenerator:
    """Generate HTML preview and validate markdown docs."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self._xref_validator = XRefValidator(repo_root)  # Reuse!
        self._markdown_available = self._check_markdown()

    def generate_preview(self, doc_path: Path) -> PreviewResult:
        """Generate HTML preview from markdown.

        Returns PreviewResult with:
            - html: str (rendered HTML)
            - title: str (extracted from first heading)
            - word_count: int
            - estimated_read_time: int (seconds)
        """

    def validate_for_preview(self, doc_path: Path) -> list[PreviewIssue]:
        """Validate document for preview issues.

        Checks:
            - Broken links (via XRefValidator)
            - Invalid code blocks
            - Missing image files
            - Malformed markdown
        """
```

### 4. CKSDocumentationSearch
```python
class CKSDocumentationSearch:
    """Search documentation via CKS infrastructure."""

    def __init__(self, cks_path: Path | None = None) -> None:
        self._cks = self._init_cks(cks_path)
        self._available = self._cks is not None

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Full-text search documentation.

        Returns list of SearchResult:
            - file_path: str
            - excerpt: str (matching text)
            - relevance_score: float
            - line_number: int | None
        """

    def semantic_search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Semantic search using CKS knowledge graph.

        Expands query with related terms from knowledge graph.
        """
```

### 5. APIChangelogGenerator
```python
class APIChangelogGenerator:
    """Generate changelog entries from API changes."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self._summarizer = ChangelogSummarizer(repo_root)  # Reuse!

    def generate_diff(self, old_ref: str, new_ref: str) -> ChangelogEntry:
        """Generate changelog entry between two refs.

        Returns ChangelogEntry with:
            - version: str (derived from refs)
            - changes: list[APIChange]
            - breaking_changes: list[BreakingChange]
            - summary: str (categorized summary)
        """

    def detect_breaking_changes(self, diff: GitDiff) -> list[BreakingChange]:
        """Detect breaking API changes.

        Breaking indicators:
            - Removed public functions/classes
            - Removed parameters from signatures
            - Changed parameter types (if typed)
            - Return type changes
        """
```

### 6. DocumentationLinter
```python
class DocumentationLinter:
    """Lint documentation files for quality issues."""

    PLACEHOLDER_PATTERNS = [
        r"^(TODO|FIXME|XXX)\b",
        r"^\.{3,}$",
    ]

    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$')

    def __init__(self, config: LintConfig | None = None) -> None:
        self._config = config or LintConfig()
        self._spell_checker = self._init_spell_checker()

    def lint_file(self, path: Path) -> list[LintIssue]:
        """Lint a documentation file.

        Returns list of LintIssue:
            - lineno: int
            - column: int | None
            - type: str (spelling, structure, terminology, formatting)
            - message: str
            - suggestion: str | None
        """

    def check_spelling(self, text: str) -> list[SpellError]:
        """Check spelling with technical dictionary."""

    def validate_structure(self, content: str) -> list[StructureIssue]:
        """Validate document structure.

        Checks:
            - Heading hierarchy (no skipped levels)
            - Consecutive headings
            - Empty sections
        """
```

## Interfaces

### CLI Flag Interface (doc_command.py)
```python
# Add to argument parser
parser.add_argument("--coverage-report", action="store_true")
parser.add_argument("--coverage-module", default=None)
parser.add_argument("--check-docstrings", action="store_true")
parser.add_argument("--docstring-style", default="google")
parser.add_argument("--preview", action="store_true")
parser.add_argument("--search", metavar="QUERY")
parser.add_argument("--api-diff", nargs=2, metavar=("OLD", "NEW"))
parser.add_argument("--lint", action="store_true")
```

### Data Models
```python
@dataclass
class CoverageReport:
    overall_coverage: float
    by_module: dict[str, "ModuleCoverage"]
    undocumented_apis: list[str]
    total_functions: int
    documented_functions: int
    total_classes: int
    documented_classes: int

@dataclass
class ModuleCoverage:
    path: str
    coverage: float
    functions: int
    documented_functions: int
    classes: int
    documented_classes: int

@dataclass
class DocstringIssue:
    lineno: int
    name: str
    type: str
    message: str
    suggestion: str | None = None

@dataclass
class SearchResult:
    file_path: str
    excerpt: str
    relevance_score: float
    line_number: int | None = None

@dataclass
class APIChange:
    type: str  # "added", "removed", "modified"
    name: str
    signature: str
    file_path: str

@dataclass
class BreakingChange:
    name: str
    description: str
    migration_guide: str | None = None
```

## Data Flow

```
┌─────────────┐
│   /doc      │
│  CLI flags  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         DocCommand.run()                │
│  Route to appropriate handler           │
└──────┬──────────────────────────────────┘
       │
       ├──► --coverage-report ──► DocCoverageReporter
       ├──► --check-docstrings ──► DocstringQualityChecker
       ├──► --preview ────────────► DocPreviewGenerator
       ├──► --search ─────────────► CKSDocumentationSearch
       ├──► --api-diff ───────────► APIChangelogGenerator
       └──► --lint ───────────────► DocumentationLinter
                │
                ▼
         ┌──────────────┐
         │   Output     │
         │  (JSON/TTY)  │
         └──────────────┘
```

## Integration Points

### With Existing Classes
| Existing Class | Used By New Class | Purpose |
|----------------|-------------------|---------|
| `XRefValidator` | `DocPreviewGenerator` | Link validation |
| `ChangelogSummarizer` | `APIChangelogGenerator` | Change categorization |
| `_find_repo_root()` | All classes | Git repo location |
| `ConsolidatedKnowledgeSystem` | `CKSDocumentationSearch` | Search backend |

### CKS Integration (FR-004)
```
/doc --search "query"
    │
    ▼
CKSDocumentationSearch.search()
    │
    ▼
ConsolidatedKnowledgeSystem.search(query)
    │
    ▼
Results with file references
```

**Key Decision**: No separate search index. CKS is the source of truth.

## File Structure
```
src/modules/document_system/
├── doc_suggest_agent.py          # Existing (Phase 1 classes)
├── doc_coverage.py               # NEW: DocCoverageReporter
├── docstring_checker.py          # NEW: DocstringQualityChecker
├── doc_preview.py                # NEW: DocPreviewGenerator
├── doc_search.py                 # NEW: CKSDocumentationSearch
├── api_changelog.py              # NEW: APIChangelogGenerator
└── doc_linter.py                 # NEW: DocumentationLinter

src/commands/nip/
└── doc_command.py                # MODIFY: Add new flags and handlers
```

## Error Handling Strategy

| Scenario | Behavior |
|----------|----------|
| CKS unavailable | Error message, suggest `--init-cks` |
| Optional dep missing | Warning, fallback to basic mode |
| Invalid git ref | Error with valid ref suggestions |
| Parse error | Report file and line, continue processing |
| Large codebase | Progress indicator, consider caching |

## Performance Considerations

1. **AST Parsing**: Cache parsed ASTs by file modification time
2. **Git Diff**: Use `-U0` for minimal context
3. **CKS Search**: Let CKS handle indexing, don't duplicate
4. **Large Projects**: Process in batches, show progress

## Security Considerations

1. **Git Command Injection**: Validate ref names before passing to git
2. **Path Traversal**: Validate all file paths
3. **Code Execution**: Don't execute code blocks during preview validation
4. **CKS Query Injection**: Sanitize search queries (parameterized queries)
