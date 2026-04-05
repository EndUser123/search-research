# yt-fts v2.0: Developer Documentation

**Technical Implementation Guide for Contributors**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Code Organization](#code-organization)
3. [Development Setup](#development-setup)
4. [Testing Strategy](#testing-strategy)
5. [Contributing Guidelines](#contributing-guidelines)
6. [Release Process](#release-process)
7. [API Reference](#api-reference)

---

## Architecture Overview

### System Design

yt-fts is built as a modular Python application using Click for the CLI interface, SQLite for data storage, and yt-dlp for YouTube content extraction.

### Core Components

```
yt-fts/
├── src/yt_fts/
│   ├── core/              # Core business logic
│   │   ├── cli.py         # CLI command definitions
│   │   ├── database.py    # Database schema and operations
│   │   ├── search.py      # Search engine implementation
│   │   └── db_utils.py    # Database utilities
│   ├── download/          # Download subsystem
│   │   ├── download_handler.py       # Single channel downloads
│   │   ├── batch_downloader.py       # Multi-channel batch processing
│   │   ├── cookie_extractor.py       # Browser cookie extraction
│   │   └── fast_channel_resolver.py  # Channel ID resolution
│   ├── llm/               # AI/LLM integration
│   │   ├── simple_embeddings.py      # Embedding generation and search
│   │   ├── auto_embeddings.py        # Automatic embeddings management
│   │   ├── chatbot.py               # RAG chat implementation
│   │   └── summarize.py             # Video summarization
│   ├── services/          # Business services
│   │   ├── export.py                # Export functionality
│   │   ├── channel_cleaner.py       # Channel list cleaning
│   │   └── channel_cache.py         # Channel metadata caching
│   ├── ui/                # User interface
│   │   ├── dashboard.py             # Textual TUI dashboard
│   │   ├── rich_formatter.py        # Rich UI formatting
│   │   └── status_display.py        # System status display
│   └── utils/             # Utilities
│       ├── config.py                # Configuration management
│       ├── helpers.py               # Helper functions
│       └── interrupt_handler.py     # Graceful interruption handling
└── tests/                  # Test suite
```

### Data Flow

**Download Flow**:
```
CLI Command → DownloadHandler → yt-dlp → Subtitle Extraction
                                           ↓
                                    Database Storage
                                           ↓
                                (Optional) Embedding Generation
```

**Search Flow**:
```
CLI Command → SearchHandler → SQLite FTS5 (Full-text)
                           ↓
                    Vector Search (Semantic)
                           ↓
                    Result Unification → Rich Output
```

**Batch Flow**:
```
CLI Command → BatchDownloader → Channel Validation
                                 ↓
                          Parallel Downloads (ThreadPoolExecutor)
                                 ↓
                          Progress Tracking (Rich/TUI)
                                 ↓
                    Error Handling & Reporting
```

### Key Design Patterns

1. **Strategy Pattern**: Pluggable export backends (txt, vtt, future formats)
2. **Repository Pattern**: Database abstraction in `database.py`
3. **Factory Pattern**: Channel resolver in `fast_channel_resolver.py`
4. **Observer Pattern**: Progress tracking in batch operations
5. **Command Pattern**: Click CLI commands in `cli.py`

---

## Code Organization

### Entry Points

**Main CLI Entry** (`src/yt_fts/core/cli.py`):
- `cli()`: Main Click group
- Command functions: `download()`, `search()`, `vsearch()`, etc.
- Unified search implementation combining FTS and vector search
- Multi-channel search controller

**Module Structure**:

**Core Logic** (`src/yt_fts/core/`):
- `database.py`: SQLite schema, CRUD operations, FTS5 indexing
- `search.py`: Full-text search implementation
- `multi_channel_search.py`: Multi-channel search orchestration
- `db_utils.py`: Database utilities and helpers

**Download System** (`src/yt_fts/download/`):
- `download_handler.py`: `DownloadHandler` class for single channels
- `batch_downloader.py`: `BatchDownloader` class for multi-channel
- `cookie_extractor.py`: Browser cookie extraction utilities
- `fast_channel_resolver.py`: Async channel ID resolution

**AI Integration** (`src/yt_fts/llm/`):
- `simple_embeddings.py`: Embedding generation and vector search
- `auto_embeddings.py`: Automatic embeddings management
- `chatbot.py`: RAG-based chatbot implementation
- `summarize.py`: Video summarization using LLMs

**Services** (`src/yt_fts/services/`):
- `export.py`: `ExportHandler` for transcript export
- `channel_cleaner.py`: `ChannelCleaner` for list optimization
- `channel_cache.py`: Channel metadata caching
- `unified_error_handler.py`: Centralized error handling

**UI Components** (`src/yt_fts/ui/`):
- `dashboard.py`: `GoogleStitchUI` Textual TUI
- `rich_formatter.py`: Rich console formatting
- `status_display.py`: System status and health monitoring

**Utilities** (`src/yt_fts/utils/`):
- `config.py`: Configuration path management
- `helpers.py`: Helper functions (time conversion, etc.)
- `interrupt_handler.py`: Graceful shutdown handling

### Database Schema

**Tables**:

```sql
-- Channels table
CREATE TABLE channels (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT,
    channel_url TEXT,
    downloads_count INTEGER DEFAULT 0,
    logo_url TEXT,
    has_ss BOOLEAN DEFAULT 0,  -- Has semantic search
    subscribed_date TIMESTAMP
);

-- Videos table
CREATE TABLE videos (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT,
    title TEXT,
    published_at TIMESTAMP,
    duration INTEGER,
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
);

-- Subtitles table (FTS5 enabled)
CREATE VIRTUAL TABLE subtitles USING fts5(
    text,
    video_id,
    start_time,
    timestamp,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

-- Embeddings metadata (JSON storage)
-- Stored in config directory as embeddings/{channel_id}.json
```

**Indexes**:
```sql
CREATE INDEX idx_videos_channel ON videos(channel_id);
CREATE INDEX idx_videos_published ON videos(published_at);
CREATE INDEX idx_subtitles_video ON subtitles(video_id);
```

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- FFmpeg (optional, for advanced video processing)

### Environment Setup

```bash
# Clone repository
git clone https://github.com/NotJoeMartinez/yt-fts.git
cd yt-fts

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### Development Tools

**Code Quality**:
```bash
# Linting
ruff check src/

# Auto-fix linting issues
ruff check --fix src/

# Type checking
mypy src/

# Code formatting
black src/
```

**Testing**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/yt_fts --cov-report=html

# Run specific test
pytest tests/test_download.py::test_download_channel

# Run integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

### Development Workflow

**Feature Development**:
1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes with tests
3. Run linting and formatting
4. Run tests with coverage
5. Commit with conventional commits
6. Push and create PR

**Debugging**:
```bash
# Run CLI in development mode
python -m yt_fts.core.cli --help

# Enable debug logging
export YT_FTS_DEBUG=1
python -m yt_fts.core.cli download "URL"

# Use pytest debugger
pytest --pdb tests/test_failing.py
```

---

## Testing Strategy

### Test Structure

```
tests/
├── test_download.py           # Download functionality tests
├── test_search.py             # Search engine tests
├── test_vsearch.py            # Vector search tests
├── test_export.py             # Export functionality tests
├── test_embeddings.py         # Embedding tests
├── test_cli.py                # CLI command tests
├── end_to_end/                # Integration tests
│   ├── test_full_workflow.py
│   └── test_batch_operations.py
├── performance/               # Performance benchmarks
│   └── test_search_performance.py
└── compliance/                # CSF NIP compliance tests
    └── test_constitutional_compliance.py
```

### Test Categories

**Unit Tests**:
- Test individual functions and classes
- Mock external dependencies (yt-dlp, APIs)
- Fast execution (<1 second per test)

**Integration Tests**:
- Test component interactions
- Use test database
- Slower execution (1-10 seconds per test)

**End-to-End Tests**:
- Full workflow testing
- Real YouTube channels (small, stable test channels)
- Slowest execution (10-60 seconds per test)

**Performance Tests**:
- Benchmark search queries
- Measure download speeds
- Profile memory usage

### Writing Tests

**Example Unit Test**:
```python
# tests/test_search.py
import pytest
from yt_fts.core.search import SearchHandler

def test_full_text_search(db_connection):
    """Test full-text search functionality"""
    # Arrange: Add test data
    handler = SearchHandler(scope="all")

    # Act: Perform search
    results = handler.full_text_search("test query")

    # Assert: Verify results
    assert len(results) > 0
    assert results[0]["text"] is not None
```

**Example Integration Test**:
```python
# tests/end_to_end/test_full_workflow.py
import pytest
from click.testing import CliRunner
from yt_fts.core.cli import cli

@pytest.mark.integration
def test_download_and_search():
    """Test complete workflow: download, embed, search"""
    runner = CliRunner()

    # Download test channel
    result = runner.invoke(cli, [
        "download",
        "--jobs", "1",
        "--language", "en",
        "https://www.youtube.com/@TestChannel"
    ])
    assert result.exit_code == 0

    # Search downloaded content
    result = runner.invoke(cli, [
        "search",
        "test query",
        "--channel", "TestChannel"
    ])
    assert result.exit_code == 0
    assert "matches found" in result.output
```

### Test Fixtures

**conftest.py**:
```python
import pytest
import tempfile
import sqlite3

@pytest.fixture
def db_connection():
    """Provide temporary test database"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    # Create test schema
    # ... (schema creation)

    yield conn

    conn.close()
    os.unlink(db_path)

@pytest.fixture
def mock_yt_dlp(monkeypatch):
    """Mock yt-dlp download functionality"""
    def mock_download(*args, **kwargs):
        return {"subtitles": {"en": [...]}}
    monkeypatch.setattr("yt_dlp.YoutubeDL", mock_download)
```

### Coverage Goals

- **Overall Coverage**: 80%+ target
- **Critical Path Coverage**: 95%+ (download, search, database)
- **CLI Coverage**: 70%+ (complex command parsing)

---

## Contributing Guidelines

### Code Style

**Python Standards**:
- Follow PEP 8
- Use Black for formatting (line length 88)
- Use Ruff for linting
- Type hints required for public functions

**Naming Conventions**:
```python
# Functions and variables: snake_case
def download_channel(channel_id: str) -> None:
    pass

# Classes: PascalCase
class DownloadHandler:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_LANGUAGE = "en"
```

### Commit Messages

**Conventional Commits**:
```
feat: add multi-channel search support

BREAKING CHANGE: search command now uses unified interface

- Add --channels flag for multiple channels
- Combine FTS and vector search results
- Remove duplicate entries across search types

Closes #123
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build process, dependencies

### Pull Request Guidelines

**PR Title**: Use conventional commits format

**PR Description**:
```markdown
## Summary
Brief description of changes

## Changes
- Bullet list of changes
- Include breaking changes if any

## Testing
- [x] Unit tests added/updated
- [x] Integration tests pass
- [x] Manual testing performed

## Checklist
- [x] Code follows style guidelines
- [x] Self-review completed
- [x] Documentation updated
```

**Review Process**:
1. Automated checks: linting, formatting, tests
2. Code review: maintainers review code
3. Approval: at least one maintainer approval
4. Merge: squash and merge to main

### Adding New Features

**Checklist**:
1. Specification: Document feature in specify.md
2. Tests: Write tests before implementation (TDD)
3. Implementation: Write code with type hints
4. Documentation: Update docstrings and user guide
5. Examples: Provide usage examples

**Example Feature Addition**:

```python
# 1. Add CLI command in cli.py
@cli.command(name="new-feature")
@click.argument("input")
@click.option("--option", default="value")
def new_feature(input: str, option: str) -> None:
    """
    New feature description.

    Examples:
        yt-fts new-feature "input" --option custom
    """
    handler = NewFeatureHandler()
    handler.execute(input, option)

# 2. Add handler in services/
# src/yt_fts/services/new_feature.py
class NewFeatureHandler:
    def execute(self, input: str, option: str) -> None:
        """Execute new feature logic"""
        # Implementation
        pass

# 3. Add tests
# tests/test_new_feature.py
def test_new_feature_handler():
    handler = NewFeatureHandler()
    result = handler.execute("test", "value")
    assert result is not None
```

---

## Release Process

### Versioning

**Semantic Versioning**: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

**Current Version**: 0.1.62 (development)

### Pre-Release Checklist

1. **Code Quality**:
   - [ ] All tests passing
   - [ ] Coverage ≥80%
   - [ ] No linting errors
   - [ ] Type checking clean

2. **Documentation**:
   - [ ] README.md updated
   - [ ] CHANGELOG.md updated
   - [ ] API documentation current
   - [ ] User guide updated

3. **Testing**:
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   - [ ] Performance benchmarks met

4. **Security**:
   - [ ] Dependency audit (`pip-audit`)
   - [ ] No known vulnerabilities
   - [ ] API keys not hardcoded

### Release Steps

```bash
# 1. Update version
# Edit src/yt_fts/__init__.py
__version__ = "0.2.0"

# 2. Update CHANGELOG.md
# Add release notes with date and changes

# 3. Commit and tag
git add -A
git commit -m "chore: release v0.2.0"
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main --tags

# 4. Build package
python -m build

# 5. Publish to PyPI (test first)
twine check dist/*
twine upload --repository testpypi dist/*

# 6. Test from test PyPI
pip install --index-url https://test.pypi.org/simple/ yt-fts

# 7. Publish to production PyPI
twine upload dist/*

# 8. Create GitHub release
# Go to GitHub Releases, create new release from tag
# Add release notes from CHANGELOG
```

### Post-Release

1. Monitor GitHub Issues for bug reports
2. Track download statistics (PyPI dashboards)
3. Gather user feedback
4. Plan next release milestones

---

## API Reference

### Core APIs

**Database API** (`src/yt_fts/core/database.py`):
```python
def get_channel_id_from_input(channel_input: str) -> str:
    """Resolve channel input to channel ID"""

def check_if_channel_exists(channel_id: str) -> bool:
    """Check if channel exists in database"""

def delete_channel(channel_id: str) -> None:
    """Delete channel and all associated data"""

def list_channels() -> List[Dict]:
    """List all channels in database"""
```

**Search API** (`src/yt_fts/core/search.py`):
```python
class SearchHandler:
    def __init__(self, scope: str, channel: str = None, limit: int = 10):
        """Initialize search handler"""

    def full_text_search(self, query: str) -> List[Dict]:
        """Perform full-text search using SQLite FTS5"""

    def export_results(self, query: str, results: List[Dict]) -> None:
        """Export search results to CSV"""
```

**Download API** (`src/yt_fts/download/download_handler.py`):
```python
class DownloadHandler:
    def __init__(self, number_of_jobs: int, language: str, ...):
        """Initialize download handler"""

    def download_channel(self, url: str) -> None:
        """Download all videos from channel"""

    def update_channel(self, channel_id: str) -> None:
        """Update channel with new videos"""

    def vtt_to_db(self, vid_id: str, subs: List[Dict]) -> Dict:
        """Convert VTT subtitles to database entries"""
```

**Embeddings API** (`src/yt_fts/llm/simple_embeddings.py`):
```python
class SimpleEmbeddingsHandler:
    def add_embeddings_to_storage(self, channel_id: str, model_config: Dict) -> None:
        """Generate and store embeddings for channel"""

    def search_similar(self, channel_id: str, query: str, limit: int, api_key: str) -> List[Dict]:
        """Perform semantic search using embeddings"""
```

### Extension Points

**Custom Exporters**:
```python
# Add to src/yt_fts/services/export.py
class CustomExporter:
    def export(self, data: List[Dict], output_path: str) -> None:
        """Custom export implementation"""
        pass

# Register in ExportHandler
exporters = {
    "txt": TextExporter,
    "vtt": VTTExporter,
    "custom": CustomExporter,  # Add here
}
```

**Custom LLM Providers**:
```python
# Add to src/yt_fts/llm/simple_embeddings.py
def get_custom_embeddings(text: str, api_key: str) -> List[float]:
    """Custom embedding generation"""
    # Implementation
    pass

# Register in embedding generation
embedding_functions = {
    "openai": get_openai_embeddings,
    "gemini": get_gemini_embeddings,
    "custom": get_custom_embeddings,  # Add here
}
```

### Configuration API

**Config Utilities** (`src/yt_fts/utils/config.py`):
```python
def get_config_path() -> Path:
    """Get platform-specific config directory"""

def get_db_path() -> Path:
    """Get database file path"""

def get_embeddings_path() -> Path:
    """Get embeddings storage directory"""
```

**Model Configuration** (`src/yt_fts/utils/helpers.py`):
```python
def get_model_config(api_key: str = None, model: str = None) -> Dict:
    """
    Get model configuration for API calls

    Returns:
        {
            "name": "GEMINI",
            "embedding_model": "text-embedding-004",
            "chat_model": "gemini-1.5-flash",
            "api_key": "...",
            "base_url": ""
        }
    """
```

---

## Performance Considerations

### Database Optimization

**Indexing Strategy**:
```sql
-- Critical indexes for performance
CREATE INDEX idx_videos_channel ON videos(channel_id);
CREATE INDEX idx_videos_published ON videos(published_at);
CREATE INDEX idx_subtitles_video ON subtitles(video_id);

-- FTS5 full-text index (automatic)
CREATE VIRTUAL TABLE subtitles USING fts5(text, video_id, start_time);
```

**Query Optimization**:
```python
# Bad: N+1 queries
for video in videos:
    subs = db.query("SELECT * FROM subtitles WHERE video_id = ?", video.id)

# Good: Single query with JOIN
results = db.query("""
    SELECT s.*, v.title
    FROM subtitles s
    JOIN videos v ON s.video_id = v.video_id
    WHERE v.channel_id = ?
""", channel_id)
```

### Download Performance

**Parallelization**:
```python
# Optimal job count varies by use case
# Default: 2 jobs (safe for rate limits)
# High-performance: 4-8 jobs (with browser cookies)
# Conservative: 1 job (avoid rate limits)

# Rule of thumb: jobs = min(cpu_count() // 2, 4)
```

**Memory Management**:
```python
# Process transcripts in chunks
chunk_size = 100  # videos per batch
for i in range(0, len(videos), chunk_size):
    batch = videos[i:i+chunk_size]
    process_batch(batch)
```

### Search Performance

**Full-Text Search**:
- FTS5: ~50-200ms for typical queries
- NEAR queries: ~500ms-2s
- Phrase queries: ~100-300ms

**Semantic Search**:
- Local embeddings: ~200-500ms
- API embeddings: ~1-3s (network dependent)

**Optimization Tips**:
1. Use `--fts-only` for fastest results
2. Limit results with `--limit` flag
3. Use channel-specific search vs. all channels
4. Export results for repeated analysis

---

## Security Considerations

### API Key Management

**Never hardcode API keys**:
```python
# Bad
API_KEY = "AIzaSyDaGmWKa4JsXZ-HjGw7ISLn_3namBGewQe"

# Good
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")
```

### Input Validation

**Sanitize user input**:
```python
# Channel URL validation
def validate_channel_url(url: str) -> bool:
    """Validate YouTube channel URL"""
    patterns = [
        r"^https?://www\.youtube\.com/@[\w-]+$",
        r"^@[\w-]+$",
        r"^UC[\w-]{22}$"
    ]
    return any(re.match(p, url) for p in patterns)
```

### SQL Injection Prevention

**Use parameterized queries**:
```python
# Bad
query = f"SELECT * FROM channels WHERE channel_name = '{name}'"

# Good
query = "SELECT * FROM channels WHERE channel_name = ?"
cursor.execute(query, (name,))
```

### Dependency Security

**Audit dependencies**:
```bash
# Check for vulnerabilities
pip-audit

# Update dependencies
pip install --upgrade -r requirements.txt

# Check outdated packages
pip list --outdated
```

---

## Troubleshooting Development Issues

### Common Development Problems

**Import Errors**:
```bash
# Ensure editable install
pip install -e .

# Check PYTHONPATH
echo $PYTHONPATH  # Should include project root

# Verify imports
python -c "from yt_fts.core.cli import cli; print('OK')"
```

**Test Failures**:
```bash
# Run specific test with output
pytest tests/test_failing.py -v -s

# Run with pdb debugger
pytest tests/test_failing.py --pdb

# Check test isolation
pytest tests/test_failing.py --forcexit
```

**Database Locks**:
```bash
# Close all connections
# SQLite: Only one write connection at a time

# Check for open connections
lsof | grep subtitles.db  # macOS/Linux
handle subtitles.db       # Windows

# Delete lock file (caution!)
rm ~/.config/yt-fts/subtitles.db-wal
```

---

## Resources

### Internal Documentation
- `CLAUDE.md`: Development guidance for Claude Code
- `README.md`: Project overview and basic usage
- `CHANGELOG.md`: Version history and changes

### External Dependencies
- **Click**: https://click.palletsprojects.com/
- **SQLite**: https://www.sqlite.org/fts5.html
- **yt-dlp**: https://github.com/yt-dlp/yt-dlp
- **Rich**: https://rich.readthedocs.io/
- **Textual**: https://textual.textual.io/

### Related Projects
- **youtube-transcript-api**: https://github.com/pytube/pytube
- **chromadb**: https://www.trychroma.com/

---

**Document Version**: 2.0.0
**Last Updated**: December 24, 2024
**Project**: yt-fts YouTube Full-Text Search
**Repository**: https://github.com/NotJoeMartinez/yt-fts
