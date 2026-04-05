# Specification: Documentation Enhancements Phase 2

## Goal
Add 6 advanced documentation features to the `/doc` command to improve documentation quality and developer experience.

## Why
- **Developer Experience**: Documentation is often stale, incomplete, or hard to navigate
- **Quality Assurance**: No automated way to check docstring quality or coverage
- **Workflow Integration**: Documentation tools exist in isolation; need integration with existing `/doc` command
- **Maintainability**: Large codebases need automated detection of stale documentation

## What

### FR-001: Documentation Coverage Report
- Generate metrics on docstring coverage by module
- Track documentation trends over time
- Identify undocumented public APIs
- Flag files missing documentation entirely

### FR-002: Docstring Quality Checker
- Detect empty/placeholder docstrings (`"TODO"`, `"..."`, `"pass"`)
- Validate docstring format consistency (Google/NumPy/Sphinx)
- Check for missing sections (Args, Returns, Raises)
- Suggest improvements for vague descriptions

### FR-003: Interactive Documentation Preview
- Live preview of markdown as it would render
- Validate local links before commit
- Check code block syntax
- Verify image references

### FR-004: Documentation Search (CKS-Integrated)
- Full-text search across all documentation
- Semantic search with related terms
- Jump-to-file capability
- **Note**: Should leverage existing CKS infrastructure rather than duplicate

### FR-005: API Diff Generator
- Auto-generate changelog entries for API changes
- Detect breaking changes in signatures
- Compare docstrings between versions
- Generate migration guides

### FR-006: Documentation Linter
- Spell checking with technical dictionary
- Terminology enforcement
- Heading hierarchy validation
- Code example execution testing

## All Needed Context

### Files
- `P:/__csf.nip/src/modules/document_system/doc_suggest_agent.py` - Existing doc suggestion agent
- `P:/__csf.nip/src/commands/nip/doc_command.py` - CLI entry point
- `P:/__csf.nip/src/modules/document_system/unified_doc_system.py` - Core document system

### APIs
- DocSuggestAgent - Base agent for documentation analysis
- UnifiedDocumentSystem - Main document processing orchestrator
- DocumentAgent - Generic document processing interface

### Existing Patterns
- Enhancement classes added in Phase 1: `RevertDetector`, `ConventionalCommitsMapper`, `XRefValidator`, `VersionDriftDetector`, `SemanticDocFinder`, `ChangelogSummarizer`
- Lazy mode pattern for `/doc` (no target = analyze and suggest)
- Flag-based CLI options (`--autodoc`, `--verbose`, etc.)

### Gotchas
- CKS already has search/discovery capabilities - should integrate, not duplicate
- Some tools may require external dependencies (e.g., `pyspellchecker`, `markdown` for preview)
- Performance concerns for large codebases - need caching/indexing

## Implementation Blueprint

### 1. DocCoverageReporter (FR-001)
```python
class DocCoverageReporter:
    """Generate documentation coverage metrics."""
    def __init__(self, repo_root: Path)
    def generate_coverage_report(self, paths: list[Path]) -> dict
    def get_undocumented_apis(self, module: str) -> list[str]
    def get_trend_data(self, days: int) -> dict
```
- **Input**: List of Python source paths
- **Output**: Coverage percentage, missing docstrings, trend data
- **Tests**: Verify coverage calculation matches manual inspection

### 2. DocstringQualityChecker (FR-002)
```python
class DocstringQualityChecker:
    """Validate docstring quality."""
    def __init__(self, style: str = "google")  # google, numpy, sphinx
    def check_file(self, path: Path) -> list[Issue]
    def validate_format(self, docstring: str) -> bool
    def suggest_improvements(self, docstring: str) -> list[str]
```
- **Input**: Python source file or docstring text
- **Output**: List of issues (empty, wrong format, missing sections)
- **Tests**: Known bad docstrings are flagged, good ones pass

### 3. DocPreviewGenerator (FR-003)
```python
class DocPreviewGenerator:
    """Generate live preview of documentation."""
    def __init__(self, repo_root: Path)
    def generate_preview(self, doc_path: Path) -> str  # HTML
    def validate_links(self, content: str) -> list[InvalidLink]
    def check_code_blocks(self, content: str) -> list[BlockIssue]
```
- **Input**: Markdown file path
- **Output**: HTML preview, link validation results
- **Tests**: Valid markdown renders, broken links detected

### 4. CKSDocumentationSearch (FR-004)
```python
class CKSDocumentationSearch:
    """Search documentation using CKS infrastructure."""
    def __init__(self, cks_db: Path)
    def search(self, query: str, limit: int = 10) -> list[Result]
    def semantic_search(self, query: str) -> list[Result]
```
- **Input**: Search query string
- **Output**: Relevant documentation excerpts with file references
- **Tests**: Search returns relevant results for known queries
- **CKS Integration**: Use existing CKS `search` API, don't reimplement

### 5. APIChangelogGenerator (FR-005)
```python
class APIChangelogGenerator:
    """Generate changelog entries from API changes."""
    def __init__(self, repo_root: Path)
    def generate_diff(self, old_ref: str, new_ref: str) -> ChangelogEntry
    def detect_breaking_changes(self, diff: GitDiff) -> list[BreakingChange]
    def compare_docstrings(self, old: str, new: str) -> DocstringDiff
```
- **Input**: Git refs (commit SHAs, tags, branches)
- **Output**: Structured changelog with breaking change detection
- **Tests**: Known API changes generate correct changelog entries

### 6. DocumentationLinter (FR-006)
```python
class DocumentationLinter:
    """Lint documentation files."""
    def __init__(self, config: LintConfig)
    def lint_file(self, path: Path) -> list[LintIssue]
    def check_spelling(self, text: str) -> list[SpellError]
    def validate_structure(self, doc: str) -> list[StructureIssue]
```
- **Input**: Documentation file path
- **Output**: List of lint issues (spelling, structure, terminology)
- **Tests**: Known issues are detected, false positives minimized

## CLI Integration

### New Flags for `/doc` Command
```bash
# Coverage report
/doc --coverage-report [--output coverage.json]
/doc --coverage-module src/mymodule

# Docstring checking
/doc --check-docstrings [--style google] [--fix]
/doc --check-docstrings src/module.py

# Preview
/doc --preview README.md
/doc --preview --validate-links

# Search (CKS-integrated)
/doc --search "authentication flow"
/doc --semantic-search "user management"

# API diff
/doc --api-diff HEAD~1 HEAD
/doc --api-diff v1.0 v1.1 --output changelog/

# Linting
/doc --lint [--fix] [--dictionary technical.txt]
/doc --lint docs/
```

## Validation Loop

### Level 1 (Syntax)
```bash
python -m py_compile src/modules/document_system/*.py
```

### Level 2 (Unit)
```bash
pytest tests/modules/document_system/test_doc_coverage.py
pytest tests/modules/document_system/test_docstring_checker.py
pytest tests/modules/document_system/test_doc_preview.py
pytest tests/modules/document_system/test_doc_search.py
pytest tests/modules/document_system/test_api_diff.py
pytest tests/modules/document_system/test_doc_linter.py
```

### Level 3 (Integration)
```bash
# Test coverage report
/doc --coverage-report --output /tmp/coverage.json

# Test docstring checker
/doc --check-docstrings src/commands/nip/doc_command.py

# Test preview (if dependencies available)
/doc --preview README.md

# Test search (requires CKS)
/doc --search "documentation"

# Test API diff
/doc --api-diff HEAD~1 HEAD

# Test linter
/doc --lint docs/
```

## BDD Scenarios

### Scenario 1: Coverage Report for Module
**Given** a Python module with mixed documentation
**When** running `/doc --coverage-report src/mymodule`
**Then** output shows coverage percentage and lists undocumented functions

### Scenario 2: Detect Bad Docstrings
**Given** a file with placeholder docstrings ("TODO", "...")
**When** running `/doc --check-docstrings`
**Then** issues are reported with specific line numbers

### Scenario 3: Preview Markdown
**Given** a markdown file with links
**When** running `/doc --preview --validate-links`
**Then** HTML preview is generated and broken links are reported

### Scenario 4: Search Documentation via CKS
**Given** existing documentation in CKS
**When** running `/doc --search "authentication"`
**Then** relevant documentation sections are returned

### Scenario 5: Generate API Changelog
**Given** two commits with API changes
**When** running `/doc --api-diff commit_a commit_b`
**Then** changelog entry lists API changes and breaking changes

### Scenario 6: Lint Documentation
**Given** a documentation file with typos
**When** running `/doc --lint`
**Then** spelling errors are reported with suggestions

## CKS Integration Question

**User Question**: "Shouldn't that be in CKS?"

**Analysis**: Feature #4 (Documentation Search) should absolutely integrate with CKS rather than reimplement search. The value CKS provides is:
- Persistent knowledge storage across sessions
- Semantic search capabilities
- Cross-reference tracking
- Knowledge graph relationships

**Decision**:
- FR-004 will use CKS search APIs directly
- No separate search index to maintain
- Documentation will be ingested into CKS for discoverability
- `/doc --search` becomes a convenience wrapper around CKS search

## Dependencies

### External (Optional)
- `markdown` - For preview rendering (can fall back to basic parsing)
- `pyspellchecker` - For spell checking (can skip if unavailable)
- `rich` - For pretty output formatting (already in project)

### Internal
- `DocSuggestAgent` - For integrating with existing analysis
- `ChangelogSummarizer` - For API diff change categorization
- `CKS database` - For search functionality (FR-004)

## Success Criteria
1. All 6 features functional via CLI flags
2. Integration with existing `/doc` lazy mode
3. CKS integration for search (no duplication)
4. Graceful fallback when optional dependencies unavailable
5. Test coverage >80% for new code
