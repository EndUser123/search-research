# Learning & Patterns Analysis: yt-fts v2.0 Additional Features

**Task ID:** TSK-251224-YtFtsFeatures-1956
**Project:** YouTube Full-Text Search (yt-fts) - Python CLI tool
**Repository:** P:/projects/yt-fts/
**Version:** 2.0.0
**Date:** 2025-12-24
**Status:** Step 12 - Learning & Patterns
**Workflow Phase:** CWO12 - Complete CWO15 Workflow

---

## Executive Summary

This document captures the lessons learned, architectural patterns, and best practices from planning the implementation of 13 new features for yt-fts v2.0. The analysis spans technical decisions, process effectiveness, reusable patterns, and actionable recommendations for future projects.

**Project Scope:**
- **Duration:** 8 weeks across 4 sprints
- **Features:** 13 features across Enhanced Search, Knowledge Management, Learning Features, and Automation
- **Effort:** 294 estimated hours across 68 tasks
- **Architecture:** Python CLI tool with SQLite FTS5 backend

**Key Outcomes:**
- Modular architecture with clear service boundaries
- 100% optional dependency support with feature flags
- Constitutional compliance framework integrated throughout
- Reusable patterns for LLM integration, translation, and export backends

---

## Table of Contents

1. [Technical Lessons Learned](#1-technical-lessons-learned)
2. [Process Lessons](#2-process-lessons)
3. [Best Practices Established](#3-best-practices-established)
4. [Anti-Patterns to Avoid](#4-anti-patterns-to-avoid)
5. [Recommendations for Future Projects](#5-recommendations-for-future-projects)
6. [Reusable Patterns Catalog](#6-reusable-patterns-catalog)
7. [Knowledge Assets](#7-knowledge-assets)

---

## 1. Technical Lessons Learned

### 1.1 Architecture Patterns That Worked Well

#### Modular Monolith Pattern

**Lesson:** For CLI tools, a modular monolith provides better maintainability than microservices while avoiding the complexity of distributed systems.

**Application:**
- Clear layer separation: CLI commands, services, data layer, integrations
- Each feature (export, LLM, translation) encapsulated in its own service module
- Shared database layer with clear interface boundaries
- Easy to test individual modules in isolation

**Benefits:**
- Simple deployment (single pip install)
- No network overhead between components
- Easier debugging and tracing
- Lower cognitive load for contributors

**Pattern Structure:**
```
src/yt_fts/
├── core/              # CLI entry point, command routing
├── services/          # Business logic layer
│   ├── export/        # Export backends (Obsidian, Notion, etc.)
│   ├── llm/           # LLM provider abstractions
│   ├── translation/   # Translation service interfaces
│   └── search/        # Search logic (FTS, semantic, proximity)
├── db/                # Database layer (migrations, queries)
└── utils/             # Shared utilities (date parsing, validation)
```

#### Repository Pattern for Data Access

**Lesson:** The Repository pattern provides clean abstraction over SQLite, making database operations testable and migrations manageable.

**Implementation:**
```python
class VideoRepository:
    """Repository pattern for video data access."""

    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)

    def get_videos_by_channel(self, channel_id: str) -> List[Video]:
        """Retrieve all videos for a channel."""
        cursor = self.db.execute(
            "SELECT * FROM Videos WHERE channel_id = ?",
            (channel_id,)
        )
        return [Video.from_row(row) for row in cursor.fetchall()]

    def add_video(self, video: Video) -> None:
        """Add a new video to the database."""
        self.db.execute(
            "INSERT INTO Videos (...) VALUES (...)",
            video.to_tuple()
        )
```

**Benefits:**
- Centralized query logic
- Easy to mock in tests
- Clear separation between business logic and data access
- Simplified database migrations

#### Service Interface Pattern

**Lesson:** Define abstract base classes for external services (LLM, translation, export) to enable provider swapping and graceful degradation.

**Example: LLM Provider Interface**
```python
class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_completion(self, prompt: str) -> str:
        """Generate a completion from a prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass

    @property
    @abstractmethod
    def optional_dependency(self) -> str:
        """Name of the optional dependency package."""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT implementation."""

    optional_dependency = "openai"

    def generate_completion(self, prompt: str) -> str:
        import openai
        # Implementation...

class GeminiProvider(LLMProvider):
    """Google Gemini implementation."""

    optional_dependency = "google-generativeai"

    def generate_completion(self, prompt: str) -> str:
        import google.generativeai as genai
        # Implementation...
```

**Benefits:**
- Easy to add new providers without changing calling code
- Supports multiple providers simultaneously
- Clear fallback strategy (try local, fallback to API)
- Testable with mock implementations

### 1.2 Design Patterns Applied

#### Dependency Injection for Service Configuration

**Lesson:** Constructor-based dependency injection makes services testable and configuration explicit.

**Before (Anti-pattern):**
```python
class FlashcardGenerator:
    def generate(self):
        # Hard-coded dependency
        openai.api_key = os.getenv("OPENAI_API_KEY")
        # ...
```

**After (DI Pattern):**
```python
class FlashcardGenerator:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def generate(self):
        response = self.llm.generate_completion(prompt)
        # ...

# Usage
provider = OpenAIProvider(api_key="...")
generator = FlashcardGenerator(provider)
cards = generator.generate()
```

**Benefits:**
- Easy to inject mock providers in tests
- Configuration explicit at construction time
- Supports multiple provider instances
- Follows dependency inversion principle

#### Factory Pattern for Export Backends

**Lesson:** Factory pattern simplifies adding new export formats without modifying existing code.

**Implementation:**
```python
class ExporterFactory:
    """Factory for creating export backends."""

    _exporters: Dict[str, Type[Exporter]] = {
        "obsidian": ObsidianExporter,
        "roam": RoamResearchExporter,
        "markdown": MarkdownExporter,
        "json": JSONExporter,
        "bibtex": BibTeXExporter,
        "anki": AnkiExporter,
    }

    @classmethod
    def create(cls, format: str, **kwargs) -> Exporter:
        """Create an exporter instance for the given format."""
        exporter_class = cls._exporters.get(format)
        if not exporter_class:
            raise ValueError(f"Unknown export format: {format}")

        # Check optional dependencies
        if not exporter_class.is_available():
            missing_pkg = exporter_class.optional_dependency
            raise ClickException(
                f"Export format '{format}' requires '{missing_pkg}'. "
                f"Install with: pip install yt-fts[{format}]"
            )

        return exporter_class(**kwargs)

# Usage
exporter = ExporterFactory.create("obsidian", output_dir="./vault")
exporter.export(search_results)
```

**Benefits:**
- Open/closed principle: open for extension, closed for modification
- Centralized dependency checking
- Consistent error handling
- Easy to discover available formats

#### Strategy Pattern for Citation Styles

**Lesson:** Strategy pattern enables multiple citation formats without complex conditional logic.

**Implementation:**
```python
class CitationStrategy(ABC):
    """Abstract base for citation strategies."""

    @abstractmethod
    def format(self, video: Video) -> str:
        """Format a video citation."""
        pass

class APAStyleStrategy(CitationStrategy):
    """APA 7th edition citation format."""

    def format(self, video: Video) -> str:
        return (
            f"{video.channel_name}. "
            f"({video.publish_date.strftime('%Y, %B %d')}). "
            f"*{video.title}* [Video]. YouTube. "
            f"{video.url}"
        )

class MLAStyleStrategy(CitationStrategy):
    """MLA 9th edition citation format."""

    def format(self, video: Video) -> str:
        return (
            f'{video.channel_name}. "{video.title}." '
            f'*YouTube*, {video.publish_date.strftime("%d %b. %Y")}, '
            f'{video.url}. '
            f'Accessed {datetime.now().strftime("%d %b. %Y")}.'
        )

class BibTeXStyleStrategy(CitationStrategy):
    """BibTeX citation format."""

    def format(self, video: Video) -> str:
        safe_id = re.sub(r'[^\w]', '', video.title)[:20]
        return (
            f"@online{{{safe_id},\n"
            f"  author = {{{video.channel_name}}},\n"
            f"  title = {{{video.title}}},\n"
            f"  year = {{{video.publish_date.strftime('%Y')}}},\n"
            f"  url = {{{video.url}}},\n"
            f"  urldate = {{{datetime.now().strftime('%Y-%m-%d')}}}\n"
            f"}}"
        )

# Usage
formatter = CitationFormatter(APAStyleStrategy())
citation = formatter.cite(video)
```

**Benefits:**
- Each citation style is self-contained
- Easy to add new styles
- No complex if/elif chains
- Testable in isolation

### 1.3 Database Optimization Techniques

#### SQLite FTS5 Capabilities and Limitations

**Lesson:** Understanding FTS5's strengths and limitations prevents over-engineering.

**FTS5 Strengths:**
- **Full-text search:** Fast substring and token matching
- **BM25 ranking:** Built-in relevance scoring
- **NEAR operator:** Proximity search support
- **Trigram indexes:** Fast prefix matching
- **Compression:** Efficient storage of large text corpora

**FTS5 Limitations:**
- **Single language per table:** Tokenizers are language-specific
- **No semantic search:** Requires external embeddings
- **Write contention:** Single-writer limitation affects concurrent updates
- **Index size:** FTS5 indexes can be 2-3x the text size

**Optimization Strategies:**
```sql
-- 1. Use contentless FTS tables for read-heavy workloads
CREATE VIRTUAL TABLE Subtitles_fts USING fts5(
    text,
    content='Subtitles',
    content_rowid='rowid'
);

-- 2. Add specific tokenizers for better language support
CREATE VIRTUAL TABLE Subtitles_fts USING fts5(
    text,
    tokenize='porter unicode61'  -- English stemming + Unicode support
);

-- 3. Use external content tables for updates
CREATE VIRTUAL TABLE Subtitles_fts USING fts5(
    text,
    content=Subtitles,
    content_rowid=rowid
);

-- 4. Optimize with ANALYZE after bulk imports
ANALYZE;

-- 5. Use VACUUM to reclaim space
VACUUM;
```

**Learned Patterns:**
- Use `WITHOUT ROWID` for tables with single-column primary keys
- Create covering indexes for frequent query patterns
- Batch inserts in transactions (1000 rows per transaction)
- Use `PRAGMA optimize` periodically for query planner statistics

#### Schema Migration Patterns

**Lesson:** Incremental migrations with rollback support enable safe database evolution.

**Migration Script Template:**
```python
def migrate_to_v2(db_path: str) -> None:
    """Add language_code column to Subtitles table."""
    db = sqlite3.connect(db_path)

    try:
        # Check if migration already applied
        cursor = db.execute(
            "SELECT COUNT(*) FROM pragma_table_info('Subtitles') WHERE name='language_code'"
        )
        if cursor.fetchone()[0] > 0:
            logger.info("Migration v2 already applied")
            return

        logger.info("Applying migration v2: Add language_code support")

        # 1. Create backup
        backup_path = f"{db_path}.backup_{datetime.now().isoformat()}"
        shutil.copy2(db_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

        # 2. Apply migration
        db.execute("ALTER TABLE Subtitles ADD COLUMN language_code TEXT DEFAULT 'en'")
        db.execute("CREATE INDEX IF NOT EXISTS idx_subtitles_language ON Subtitles(language_code)")

        # 3. Update schema version
        db.execute("INSERT INTO SchemaVersion (version, description) VALUES (2, 'Add multi-language support')")

        db.commit()
        logger.info("Migration v2 completed successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {e}")
        raise
```

**Best Practices:**
- Always create backups before migration
- Use transactions for atomic migrations
- Check if migration already applied (idempotent)
- Store schema version in dedicated table
- Provide rollback scripts for each migration

### 1.4 Optional Dependency Management Strategies

**Lesson:** Lazy imports with helpful error messages provide better UX than hard requirements.

**Pattern 1: Feature Flag with Lazy Import**
```python
# At module load time
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# In function
def generate_flashcards(video_id: str):
    if not HAS_OPENAI:
        raise click.ClickException(
            "Flashcard generation requires the 'openai' package.\n"
            "Install with: pip install yt-fts[openai]\n"
            "Or use: pip install yt-fts[all]"
        )
    # Implementation...
```

**Pattern 2: Dynamic Import with Error Context**
```python
def check_import(module_name: str, extras_name: str) -> None:
    """Check if optional dependency is installed, raise helpful error if not."""
    try:
        importlib.import_module(module_name)
    except ImportError:
        raise click.ClickException(
            f"Required module '{module_name}' not found.\n"
            f"This feature requires optional dependencies.\n"
            f"Install with: pip install yt-fts[{extras_name}]\n"
            f"Or install all extras: pip install yt-fts[all]"
        )

# Usage
def export_notion(video_id: str):
    check_import("notion_client", "notion")
    from notion_client import Client
    # Implementation...
```

**Pattern 3: pyproject.toml Extras Configuration**
```toml
[project.optional-dependencies]
# Individual feature groups
notion = ["notion-client>=2.2.1"]
zotero = ["pyzotero>=1.5.21"]
anki = ["genanki>=0.13.0"]
translate-google = ["deep-translator>=1.11.4"]
translate-deepl = ["deepl>=1.15.0"]
api = ["fastapi>=0.104.0", "uvicorn[standard]>=0.24.0", "aiosqlite>=0.19.0"]

# Combined groups
knowledge = ["yt-fts[notion,zotero]"]
learning = ["yt-fts[anki,translate-google]"]
all-extras = ["yt-fts[notion,zotero,anki,translate-google,api]"]
```

**Learned Benefits:**
- Core installation remains lightweight
- Users only install what they need
- Clear installation instructions in error messages
- Easy to test with minimal dependencies
- Supports diverse use cases without bloat

### 1.5 SQLite-Specific Patterns

#### Connection Pooling for API Server

**Lesson:** SQLite's single-writer limitation requires careful connection management in API mode.

**Implementation:**
```python
class DatabaseConnectionPool:
    """Simple connection pool for SQLite."""

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._connections: List[sqlite3.Connection] = []
        self._lock = threading.Lock()

    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool."""
        with self._lock:
            if self._connections:
                return self._connections.pop()

            # Create new connection
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode
            return conn

    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool."""
        with self._lock:
            if len(self._connections) < self.pool_size:
                self._connections.append(conn)
            else:
                conn.close()

# Usage with FastAPI
@app.get("/api/v1/search")
async def search(query: str):
    pool = get_db_pool()
    conn = pool.get_connection()
    try:
        results = search_videos(conn, query)
        return results
    finally:
        pool.return_connection(conn)
```

**Key Settings for Concurrency:**
```sql
PRAGMA journal_mode=WAL;           -- Enable write-ahead logging
PRAGMA busy_timeout=5000;          -- Wait 5 seconds for lock
PRAGMA synchronous=NORMAL;         -- Balance safety and speed
PRAGMA cache_size=-64000;          -- 64MB cache
PRAGMA temp_store=MEMORY;          -- Keep temp tables in memory
```

---

## 2. Process Lessons

### 2.1 What Worked in the Planning Process

#### CWO15 Workflow Effectiveness

**Lesson:** The CWO15 workflow provided structured guidance while remaining flexible for project needs.

**Effective Phases:**
1. **Research (Steps 2-4):** User persona analysis clarified feature priorities
2. **Specification (Step 5):** Detailed requirements prevented scope creep
3. **Architecture (Step 6):** Early architecture decisions avoided rework
4. **Task Breakdown (Step 7):** Granular tasks enabled accurate estimation
5. **Risk Assessment (Step 8):** Proactive risk identification prevented blockers

**Workflow Benefits:**
- Clear progression from abstract to concrete
- Built-in quality gates between phases
- Documentation artifacts for each step
- Easy to resume after interruptions

#### Sprint Organization Effectiveness

**Lesson:** 2-week sprints with clear themes provided focus without rigidity.

**Sprint Structure:**
```
Sprint 1: Enhanced Search (Quick wins, low risk)
  ├── Time-based filters (2-3 days)
  ├── Proximity search (3-5 days)
  ├── Search history (5-7 days)
  └── JSON output (2-3 days)

Sprint 2: Knowledge Management (Integration focus)
  ├── Obsidian export (5-7 days)
  ├── Citation export (4-6 days)
  └── Notion/Zotero (7-10 days)

Sprint 3: Learning Features (LLM-heavy)
  ├── Flashcards (5-7 days)
  ├── Chapter detection (7-10 days)
  ├── Multi-language (5-7 days)
  └── Translation (7-10 days)

Sprint 4: Automation & Infrastructure (Infrastructure)
  ├── Watch mode (7-10 days)
  └── API server (10-14 days)
```

**Benefits:**
- Each sprint delivers user value
- Lower-risk features build confidence
- Higher-risk features have foundation from earlier sprints
- Easy to adjust scope based on velocity

#### Persona-Driven Prioritization

**Lesson:** Explicit user personas (Truth Seekers, Researchers, Learners) prevented feature bloat.

**Application:**
- Every feature mapped to at least one persona
- Persona stories provided acceptance criteria context
- Conflicting requirements resolved by persona priority
- Features without clear persona connection were excluded

**Impact:**
- Excluded Channel Analytics (content creator feature, not target user)
- Excluded Competitor Comparison (marketing tool, not research/learning)
- Focused on search, export, and learning features

### 2.2 Task Breakdown Quality

**Lesson:** Granular tasks (4-10 hours) enabled accurate estimation and progress tracking.

**Task Template Used:**
```json
{
  "id": "SPRINT-1-1",
  "title": "Add published_at column to Videos table",
  "sprint": 1,
  "feature": "Time-based search filters",
  "complexity": "low",
  "estimated_hours": 4,
  "dependencies": ["SPRINT-1-0"],
  "files": ["src/yt_fts/core/database.py"],
  "acceptance_criteria": [
    "Database migration adds published_at column to Videos table",
    "Column stores ISO format datetime strings",
    "Existing videos have NULL or placeholder values",
    "Database schema updated with proper indexes"
  ],
  "status": "pending",
  "assigned_to": "backend-developer"
}
```

**Benefits:**
- Clear definition of done
- Easy to identify dependencies
- Accurate time estimates
- Simple to track progress

**Lesson Learned:** 294 hours across 68 tasks = 4.3 hours average per task. This granularity is ideal for planning but requires overhead to maintain. For future projects, consider slightly larger tasks (6-12 hours) to reduce management overhead.

### 2.3 Risk Identification and Mitigation

**Lesson:** Early risk assessment prevented blockers and enabled informed decisions.

**Top Risks Identified:**

| Risk | Impact | Mitigation | Outcome |
|------|--------|------------|---------|
| LLM API costs | High | Cost estimation, caching, local model support | Features designed with fallbacks |
| External API changes | Medium | Feature flags, graceful degradation | All integrations optional |
| Database performance | Medium | Indexes, query optimization, testing | Performance targets defined |
| Breaking changes | Medium | Migration system, backward compatibility | v2.0 decision explicit |

**Risk Management Process:**
1. Identify risks during architecture phase
2. Assess impact (high/medium/low) and likelihood
3. Design mitigation strategies
4. Document assumptions and dependencies
5. Create contingency plans

**Learned Pattern:** Create a "Risk Register" document updated throughout the project.

### 2.4 Quality Gate Effectiveness

**Lesson:** Constitutional compliance quality gates prevented ethical debt.

**Quality Gates Applied:**
- **User Autonomy:** All features opt-in, no forced behavior
- **Privacy Protection:** Local-first, no telemetry, API key security
- **Transparent Operations:** Verbose logging, explainable errors
- **Optional Dependencies:** 100% support with feature flags

**Gate Enforcement:**
- Requirements analysis checked each feature against principles
- Architecture design included privacy patterns
- Task breakdown included compliance tasks
- Acceptance criteria included constitutional checks

**Outcome:**
- No features violate user autonomy
- No data leaves system without explicit consent
- All operations are auditable and explainable
- Core functionality works without any optional dependencies

**Learned:** Integrating constitutional compliance from the beginning is more effective than retrofitting.

---

## 3. Best Practices Established

### 3.1 Code Organization Patterns

#### Directory Structure for CLI Tools

**Best Practice:**
```
src/yt_fts/
├── __init__.py
├── __main__.py           # Entry point for `python -m yt_fts`
├── cli/                  # CLI command definitions
│   ├── __init__.py
│   ├── search.py         # Search commands
│   ├── export.py         # Export commands
│   ├── watch.py          # Watch mode commands
│   └── server.py         # API server commands
├── core/                 # Core business logic
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── database.py       # Database connection and queries
│   └── exceptions.py     # Custom exceptions
├── services/             # Service layer
│   ├── __init__.py
│   ├── export/           # Export backends
│   │   ├── __init__.py
│   │   ├── base.py       # Abstract Exporter class
│   │   ├── obsidian.py   # Obsidian exporter
│   │   ├── notion.py     # Notion exporter
│   │   └── ...
│   ├── llm/              # LLM providers
│   │   ├── __init__.py
│   │   ├── base.py       # Abstract LLMProvider
│   │   ├── openai.py     # OpenAI provider
│   │   └── gemini.py     # Gemini provider
│   └── translation/      # Translation services
│       ├── __init__.py
│       ├── base.py
│       ├── google.py
│       └── deepl.py
├── db/                   # Database layer
│   ├── __init__.py
│   ├── migrations/       # Migration scripts
│   │   ├── __init__.py
│   │   ├── v1_to_v2.py
│   │   └── v2_to_v3.py
│   └── repositories/     # Repository classes
│       ├── __init__.py
│       ├── videos.py
│       └── channels.py
├── utils/                # Utility functions
│   ├── __init__.py
│   ├── date_parser.py    # Date parsing utilities
│   ├── validators.py     # Input validation
│   └── formatters.py     # Output formatting
└── config/               # Configuration files
    ├── __init__.py
    ├── defaults.py       # Default configuration
    └── schemas/          # JSON schemas for validation
```

**Benefits:**
- Clear separation of concerns
- Easy to locate code by functionality
- Simple to test individual modules
- Supports multiple developers working in parallel

#### Import Organization Guidelines

**Best Practice:**
```python
# 1. Standard library imports
import argparse
import json
from datetime import datetime
from pathlib import Path

# 2. Third-party imports
import click
from rich.console import Console
import sqlite3

# 3. Local application imports
from yt_fts.core.config import get_config
from yt_fts.core.database import Database
from yt_fts.services.export.base import Exporter
```

**Benefits:**
- Clear dependency hierarchy
- Easy to spot missing dependencies
- Linting tools can verify order
- Reduces merge conflicts

### 3.2 Testing Strategies (TDD Approach)

#### Test Pyramid for CLI Tools

**Best Practice:**
```
           /\
          /E2E\        ← Few (10%)
         /------\
        /Integration\   ← Some (30%)
       /------------\
      /   Unit Tests \  ← Many (60%)
     /----------------\
```

**Unit Tests (60%):**
```python
# tests/unit/test_date_parser.py
def test_parse_iso_date():
    """Test ISO 8601 date parsing."""
    assert parse_date("2024-01-15") == datetime(2024, 1, 15)

def test_parse_relative_date_days():
    """Test relative date parsing (days)."""
    result = parse_relative_date("7d")
    assert (datetime.now() - result).days == 7

def test_parse_invalid_date():
    """Test invalid date handling."""
    with pytest.raises(ValueError, match="Invalid date format"):
        parse_date("not-a-date")
```

**Integration Tests (30%):**
```python
# tests/integration/test_search_filters.py
def test_time_based_search_integration(tmp_path):
    """Test time-based search with real database."""
    # Setup: Create test database with videos
    db = Database(tmp_path / "test.db")
    db.add_video(video_id="abc", published_at="2024-01-01")
    db.add_video(video_id="def", published_at="2024-06-01")

    # Execute: Search with time filter
    results = search_videos(
        db=db,
        query="test",
        after=datetime(2024, 3, 1)
    )

    # Assert: Only video from June returned
    assert len(results) == 1
    assert results[0]["video_id"] == "def"
```

**End-to-End Tests (10%):**
```python
# tests/e2e/test_cli_workflow.py
def test_search_export_workflow():
    """Test complete search and export workflow."""
    # Execute CLI commands
    result = subprocess.run(
        ["yt-fts", "search", "AI", "--after", "2024-01-01", "--export"],
        capture_output=True,
        text=True
    )

    # Assert: Command succeeded
    assert result.returncode == 0

    # Assert: Export file created
    assert Path("search_results.csv").exists()

    # Assert: CSV is valid
    df = pd.read_csv("search_results.csv")
    assert len(df) > 0
    assert "timestamp" in df.columns
```

**Test Organization:**
```
tests/
├── unit/                  # Fast, isolated tests
│   ├── test_date_parser.py
│   ├── test_validators.py
│   └── test_formatters.py
├── integration/           # Component interaction tests
│   ├── test_search_filters.py
│   ├── test_exporters.py
│   └── test_migrations.py
├── e2e/                   # Full workflow tests
│   ├── test_cli_workflow.py
│   └── test_api_workflow.py
└── fixtures/              # Test data and fixtures
    ├── sample_db.json
    └── test_transcripts.txt
```

### 3.3 Documentation Patterns

#### Command Help Text Standard

**Best Practice:**
```python
@click.command(
    name="search",
    help="""
    Search video transcripts using full-text search.

    Supports basic search, proximity queries (NEAR operator),
    and time-based filtering.

    \b
    Examples:
      # Basic search
      yt-fts search "machine learning"

      # Proximity search
      yt-fts search "neural NEAR/5 network"

      # Time-based filtering
      yt-fts search "AI" --after "2024-01-01"

      # Search within a channel
      yt-fts search "physics" --channel "@3Blue1Brown"

    \b
    See also:
      - vsearch: Semantic search using embeddings
      - export: Export search results
    """
)
@click.argument("query")
@click.option("--channel", "-c", help="Search within a specific channel")
@click.option("--limit", "-l", default=10, help="Maximum number of results")
@click.option("--after", help="Only show videos published after this date")
@click.option("--before", help="Only show videos published before this date")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
def search_command(query, channel, limit, after, before, json_output):
    """Search video transcripts."""
    # Implementation...
```

**Documentation Guidelines:**
- Lead with concise description
- Provide 3-4 examples covering common use cases
- Use `\b` to prevent paragraph reformatting by Click
- Include "See also" section for related commands
- Document all options with clear descriptions

#### README Structure

**Best Practice:**
```markdown
# yt-fts: YouTube Full-Text Search

[![PyPI](https://img.shields.io/pypi/v/yt-fts)](https://pypi.org/project/yt-fts/)
[![Tests](https://img.shields.io/github/actions/workflow/status/.../tests.yml)](...)

## Features

- 🔍 **Full-Text Search:** Search across entire video transcripts
- 🧠 **Semantic Search:** Find conceptually similar content
- 📚 **Export Formats:** Obsidian, Notion, BibTeX, Anki, and more
- 🌍 **Multi-Language:** Search and translate subtitles
- 🤖 **AI-Powered:** Flashcard generation and chapter detection

## Quick Start

\`\`\`bash
# Install
pip install yt-fts

# Download a channel
yt-fts download https://www.youtube.com/@3Blue1Brown

# Search
yt-fts search "neural network"
\`\`\`

## Installation

\`\`\`bash
# Basic installation
pip install yt-fts

# With all optional features
pip install yt-fts[all]

# With specific features
pip install yt-fts[notion,zotero,anki]
\`\`\`

## Usage

### Search

[Basic search examples...]

### Export

[Export examples...]

### AI Features

[AI feature examples...]

## Configuration

[Configuration file location and options...]

## API Server

[API server documentation...]

## Development

[Setup development environment, running tests...]

## License

MIT License
```

### 3.4 CLI Design Patterns

#### Command Naming Conventions

**Best Practices:**
- Use verbs for actions: `search`, `download`, `export`, `watch`
- Use nouns for entities: `channels`, `videos`, `history`
- Group related commands with `cli.group()`
- Provide short options for common flags: `-c`, `-l`, `-v`
- Use long options for clarity: `--channel`, `--limit`, `--verbose`

**Example:**
```python
@click.group()
def cli():
    """YouTube Full-Text Search CLI."""
    pass

@cli.command()
@click.argument("query")
@click.option("--channel", "-c", help="Search within a channel")
@click.option("--limit", "-l", default=10, help="Maximum results")
def search(query, channel, limit):
    """Search video transcripts."""
    pass

@cli.command()
@click.argument("url")
@click.option("--language", "-l", default="en", help="Subtitle language")
def download(url, language):
    """Download video transcripts."""
    pass

@cli.group()
def export():
    """Export search results or transcripts."""
    pass

@export.command()
@click.option("--format", "-f", type=click.Choice(["obsidian", "notion", "json"]))
@click.option("--output", "-o", help="Output directory")
def channels(format, output):
    """Export all videos from channels."""
    pass
```

#### Progress Indicators

**Best Practice:**
```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

def download_channels(channel_urls: list[str]):
    """Download multiple channels with progress tracking."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        expand=True,
    ) as progress:

        # Create overall task
        overall = progress.add_task(
            "[cyan]Downloading channels...",
            total=len(channel_urls)
        )

        for url in channel_urls:
            # Create per-channel task
            channel_task = progress.add_task(
                f"[green]Downloading {url}...",
                total=100
            )

            # Download videos
            for video in get_channel_videos(url):
                download_video(video)
                progress.advance(channel_task, 100 / len(videos))

            # Mark channel complete
            progress.update(channel_task, completed=100)
            progress.advance(overall)
```

### 3.5 API Design Patterns

#### RESTful Endpoint Design

**Best Practice:**
```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="yt-fts API", version="2.0.0")

class SearchResult(BaseModel):
    """Search result model."""
    video_id: str
    title: str
    channel: str
    timestamp: str
    text: str
    url: str

@app.get("/api/v1/search")
async def search(
    query: str = Query(..., description="Search query"),
    channel: str = Query(None, description="Filter by channel ID"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    after: str = Query(None, description="Filter by date (ISO 8601)"),
) -> dict[str, Any]:
    """
    Search video transcripts.

    Returns a list of search results matching the query.
    """
    results = search_videos(query, channel=channel, limit=limit, after=after)

    return {
        "query": query,
        "total": len(results),
        "results": [SearchResult(**r).dict() for r in results]
    }

@app.get("/api/v1/channels/{channel_id}/videos")
async def get_channel_videos(
    channel_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> dict[str, Any]:
    """Get all videos for a channel."""
    videos = get_videos_by_channel(channel_id, limit=limit, offset=offset)

    return {
        "channel_id": channel_id,
        "videos": videos,
        "total": len(videos),
        "limit": limit,
        "offset": offset
    }
```

**API Design Principles:**
- Use nouns for resources (`/channels`, `/videos`, `/search`)
- Use HTTP verbs for actions (`GET`, `POST`, `DELETE`)
- Provide pagination with `limit` and `offset`
- Use Pydantic models for request/response validation
- Return consistent error responses
- Include OpenAPI/Swagger documentation

---

## 4. Anti-Patterns to Avoid

### 4.1 Common Pitfalls Encountered

#### Pitfall 1: Tight Coupling to External APIs

**Anti-Pattern:**
```python
# BAD: Hard-coded OpenAI dependency
class FlashcardGenerator:
    def generate(self, video_id: str):
        import openai
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[...]
        )
        # ...
```

**Consequences:**
- Cannot switch providers without code changes
- Difficult to test (requires API keys)
- Vendor lock-in
- Cannot work offline

**Solution:**
```python
# GOOD: Abstract LLM provider
class FlashcardGenerator:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def generate(self, video_id: str):
        response = self.llm.generate_completion(prompt)
        # ...
```

#### Pitfall 2: Ignoring Database Performance

**Anti-Pattern:**
```python
# BAD: N+1 query problem
def get_videos_with_subtitles(channel_id: str):
    videos = db.execute(
        "SELECT * FROM Videos WHERE channel_id = ?",
        (channel_id,)
    ).fetchall()

    result = []
    for video in videos:
        # Separate query for each video!
        subtitles = db.execute(
            "SELECT * FROM Subtitles WHERE video_id = ?",
            (video["id"],)
        ).fetchall()
        result.append({**video, "subtitles": subtitles})

    return result
```

**Consequences:**
- O(n) database queries
- Slow for channels with many videos
- Unnecessary database round trips

**Solution:**
```python
# GOOD: Single query with JOIN
def get_videos_with_subtitles(channel_id: str):
    return db.execute("""
        SELECT
            Videos.*,
            Subtitles.subtitle_text
        FROM Videos
        LEFT JOIN Subtitles ON Videos.video_id = Subtitles.video_id
        WHERE Videos.channel_id = ?
        ORDER BY Videos.video_date DESC
    """, (channel_id,)).fetchall()
```

#### Pitfall 3: Poor Error Messages

**Anti-Pattern:**
```python
# BAD: Unhelpful error message
try:
    export_to_notion(results)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
```

**Consequences:**
- Users don't know what went wrong
- No guidance on how to fix
- Support burden increases
- Poor user experience

**Solution:**
```python
# GOOD: Explainable error message
try:
    export_to_notion(results)
except NotionAPIError as e:
    if e.status_code == 401:
        console.print("""
[red]❌ Notion API Authentication Failed[/red]

[b]What happened:[/b] Your Notion API token is invalid or expired.

[b]How to fix:[/b]
  1. Get a new token: https://www.notion.so/my-integrations
  2. Set environment variable:
     export NOTION_API_KEY=your_token_here
  3. Try again

[dim]Error details: {e.message}[/dim]
        """)
    elif e.status_code == 429:
        console.print("""
[yellow]⚠ Notion API Rate Limit Exceeded[/yellow]

[b]What happened:[/b] Too many requests to Notion API (3 req/sec limit).

[b]How to fix:[/b]
  1. Wait 60 seconds for rate limit to reset
  2. Reduce concurrent exports
  3. Check status: https://status.notion.com

[dim]Retry in 60 seconds...[/dim]
        """)
    sys.exit(1)
```

#### Pitfall 4: Mixing Concerns

**Anti-Pattern:**
```python
# BAD: CLI, business logic, and data access mixed
@click.command()
@click.argument("query")
def search(query):
    # CLI concern: argument parsing
    conn = sqlite3.connect("database.db")

    # Data access concern: SQL query
    results = conn.execute(
        f"SELECT * FROM Subtitles WHERE text MATCH '{query}'"
    )

    # Business logic concern: result ranking
    ranked = sorted(results, key=lambda r: r["score"], reverse=True)

    # CLI concern: output formatting
    for r in ranked:
        print(f"{r['title']}: {r['text'][:50]}...")
```

**Consequences:**
- Cannot reuse business logic
- Difficult to test (requires Click context)
- Database logic mixed with presentation
- Violates single responsibility principle

**Solution:**
```python
# GOOD: Separated concerns
# 1. CLI layer (cli/search.py)
@click.command()
@click.argument("query")
def search(query):
    """CLI command for search."""
    results = search_videos(query, limit=10)
    display_results(results)

# 2. Service layer (services/search.py)
def search_videos(query: str, limit: int = 10) -> list[dict]:
    """Business logic for search."""
    repo = VideoRepository(get_db_path())
    results = repo.search(query)

    # Apply ranking logic
    ranked = rank_results(results)

    return ranked[:limit]

# 3. Data layer (db/repositories/video.py)
class VideoRepository:
    def search(self, query: str) -> list[dict]:
        """Data access for search."""
        return self.db.execute(
            "SELECT * FROM Subtitles_fts WHERE text MATCH ?",
            (query,)
        ).fetchall()

# 4. Presentation layer (utils/display.py)
def display_results(results: list[dict]) -> None:
    """Format and display results."""
    console = Console()
    for r in results:
        console.print(f"[cyan]{r['title']}[/cyan]: {r['text'][:50]}...")
```

### 4.2 Architectural Mistakes Avoided

#### Mistake 1: Premature Optimization

**Avoided:** Early in the project, there was consideration of implementing a complex caching layer for search results. This was avoided because:
- No evidence of performance problem yet
- SQLite FTS5 is already fast (< 500ms)
- Caching adds complexity and cache invalidation overhead
- Can add later if needed (YAGNI principle)

**Lesson:** Measure first, optimize second. Don't solve problems you don't have.

#### Mistake 2: Over-Engineering Plugin System

**Avoided:** Initial plans included a full plugin system with discovery, sandboxing, and PyPI integration. This was simplified to a simple plugin API because:
- Complex plugin systems are overkill for a CLI tool
- Python entry points are sufficient for discovery
- Most users won't write plugins
- Simpler architecture is easier to maintain

**Lesson:** Keep it simple. Only add complexity when there's a clear use case.

#### Mistake 3: Ignoring SQLite Limitations

**Avoided:** There was consideration of supporting multiple concurrent writers for the API server. This was avoided because:
- SQLite has single-writer limitation
- WAL mode allows concurrent readers
- Multiple workers don't help with single-writer bottleneck
- Document limitation instead of working around it

**Lesson:** Understand your tools' limitations and design within them.

### 4.3 Performance Bottlenecks Identified

#### Bottleneck 1: FTS Index Rebuilds

**Issue:** Rebuilding FTS indexes after bulk imports can take hours for large datasets.

**Mitigation:**
- Use `INSERT` batches (1000 rows per transaction)
- Disable auto-commit during bulk imports
- Rebuild indexes in chunks if needed
- Consider using `PRAGMA synchronous=OFF` during bulk load (with backup)

#### Bottleneck 2: LLM API Latency

**Issue:** LLM API calls can take 5-10 seconds, blocking the CLI.

**Mitigation:**
- Show progress indicator while waiting
- Cache results when possible
- Use streaming responses for real-time feedback
- Provide timeout option
- Support local models for offline use

#### Bottleneck 3: Large JSON Output

**Issue:** Exporting thousands of search results as JSON can consume excessive memory.

**Mitigation:**
- Use JSONL (JSON Lines) for streaming output
- Implement pagination for large result sets
- Provide `--limit` option to restrict results
- Use generators instead of lists where possible

### 4.4 Security Vulnerabilities Prevented

#### Vulnerability 1: SQL Injection

**Prevented:** All database queries use parameterized queries.

```python
# GOOD: Parameterized query
cursor.execute(
    "SELECT * FROM Videos WHERE channel_id = ?",
    (channel_id,)
)

# BAD: String interpolation (vulnerable)
cursor.execute(
    f"SELECT * FROM Videos WHERE channel_id = '{channel_id}'"
)
```

#### Vulnerability 2: API Key Exposure

**Prevented:**
- API keys never logged
- API keys sanitized from error messages
- API keys stored with restrictive file permissions (0600)
- Support for environment variables

```python
def get_api_key(service: str) -> str:
    """Load API key securely."""
    key_file = Path.home() / ".config" / "yt-fts" / f"{service}_key.txt"

    if not key_file.exists():
        raise click.ClickException(
            f"API key not found. Set {service.upper()}_API_KEY environment variable."
        )

    # Set restrictive permissions
    key_file.chmod(0o600)

    return key_file.read_text().strip()
```

#### Vulnerability 3: Path Traversal

**Prevented:** Validate and sanitize file paths from user input.

```python
def safe_path_join(base: Path, user_path: str) -> Path:
    """Join base path with user input, preventing path traversal."""
    # Resolve user input
    full_path = (base / user_path).resolve()

    # Ensure result is within base directory
    if not str(full_path).startswith(str(base.resolve())):
        raise ValueError("Path traversal detected")

    return full_path
```

---

## 5. Recommendations for Future Projects

### 5.1 Technology Choices to Replicate

#### Core Technology Stack

**Recommended:**
- **Language:** Python 3.10+
- **CLI Framework:** Click (excellent for CLI tools)
- **Database:** SQLite (perfect for local-first apps)
- **FTS Engine:** SQLite FTS5 (built-in, fast, no dependencies)
- **Terminal UI:** Rich (beautiful console output)
- **Configuration:** TOML (human-readable, standard)
- **Testing:** pytest + pytest-cov (comprehensive testing)
- **Linting:** Ruff (fast, modern) + Black (formatting) + mypy (type checking)

**Rationale:**
- All libraries have mature, stable APIs
- Minimal dependencies for core functionality
- Strong community support
- Good documentation
- Compatible with constitutional principles (local-first, privacy-respecting)

#### Optional Technology Choices

**Recommendation:** Make all non-core features optional with feature flags.

**Pattern:**
```toml
[project.optional-dependencies]
# Group optional features by functionality
export = ["pyyaml", "jinja2"]
ai = ["openai", "anthropic"]
api = ["fastapi", "uvicorn", "aiosqlite"]
all = ["yt-fts[export,ai,api]"]
```

**Benefits:**
- Lightweight core installation
- Users only install what they need
- Reduced attack surface
- Easier to maintain

### 5.2 Processes to Reuse

#### CWO15 Workflow for Feature Planning

**Recommendation:** Use the CWO15 workflow for all feature development.

**Why it works:**
- Structured progression from research to implementation
- Built-in quality gates
- Documentation artifacts for each phase
- Easy to resume after interruptions

**Adaptation Tips:**
- Adjust depth based on project complexity
- Skip steps for trivial changes
- Emphasize research and architecture for complex features
- Use task breakdown for accurate estimation

#### Sprint-Based Development

**Recommendation:** Organize development into 2-week sprints with clear themes.

**Why it works:**
- Regular delivery of user value
- Feedback opportunities every 2 weeks
- Easy to adjust scope based on velocity
- Maintains focus without rigidity

**Sprint Planning Template:**
```
Sprint X: [Theme]
Duration: 2 weeks
Goal: [User-facing outcome]

Features:
  1. [Feature 1] (Y days)
  2. [Feature 2] (Y days)
  3. [Feature 3] (Y days)

Success Criteria:
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]
  - [ ] [Criterion 3]

Dependencies:
  - [External dependency 1]
  - [Internal dependency 2]

Risks:
  - [Risk 1] - [Mitigation]
  - [Risk 2] - [Mitigation]
```

#### Constitutional Compliance Integration

**Recommendation:** Integrate constitutional compliance from the beginning of every project.

**Framework:**
```
User Autonomy:
  - Opt-in design (no forced features)
  - Clear consent (API integrations require explicit opt-in)
  - Data control (export any data, delete any data)

Privacy Protection:
  - Local-first architecture (all data stored locally)
  - No telemetry or analytics
  - API key security (restrictive permissions, never logged)

Transparent Operations:
  - Verbose logging (--verbose flag)
  - Explainable errors (what, why, how to fix)
  - Open-source code (inspection possible)

Optional Dependencies:
  - 100% feature flag support
  - Graceful degradation
  - Clear installation instructions
```

**Benefits:**
- Prevents ethical debt
- Builds user trust
- Differentiates from competitors
- Aligns with open-source values

### 5.3 Tools to Adopt

#### Development Tools

**Essential:**
- **Ruff:** Fast Python linter (replaces flake8, isort, pyupgrade)
- **Black:** Code formatter (consistent style)
- **mypy:** Static type checker (catch bugs early)
- **pytest:** Testing framework with fixtures
- **pytest-cov:** Coverage reporting
- **pre-commit:** Git hooks for automatic checks

**Configuration Example (.pre-commit-config.yaml):**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-toml
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

#### Documentation Tools

**Recommended:**
- **mkdocs:** Static site generator for docs
- **mkdocs-material:** Beautiful theme
- **mkdocstrings:** Generate API docs from docstrings

**Setup:**
```bash
pip install mkdocs mkdocs-material mkdocstrings
mkdocs new docs
```

**mkdocs.yml:**
```yaml
site_name: yt-fts Documentation
theme:
  name: material
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
plugins:
  - mkdocstrings:
      watch: [src/yt_fts]
nav:
  - Home: index.md
  - User Guide:
      - Installation: user-guide/installation.md
      - Usage: user-guide/usage.md
  - API Reference:
      - CLI: api/cli.md
      - Services: api/services.md
```

### 5.4 Team Structures That Work

#### Role-Based Assignment

**Pattern:** Assign tasks based on expertise, not availability.

**Roles:**
- **Backend Developer:** Database, migrations, repositories
- **CLI Developer:** Click commands, argument parsing, output formatting
- **Service Developer:** LLM integration, translation, export backends
- **QA Developer:** Testing, test fixtures, CI/CD
- **Documentation:** README, API docs, user guides

**Task Assignment Example:**
```json
{
  "id": "SPRINT-1-1",
  "title": "Add published_at column to Videos table",
  "complexity": "low",
  "estimated_hours": 4,
  "assigned_to": "backend-developer"
}
```

**Benefits:**
- Developers work in areas of expertise
- Reduces context switching
- Improves code quality
- Faster development

#### Code Review Process

**Pattern:** Require code review for all changes, with clear checklist.

**Review Checklist:**
- [ ] Code follows style guide (Ruff, Black)
- [ ] All tests pass (pytest)
- [ ] New tests added (80%+ coverage)
- [ ] Documentation updated (docstrings, README)
- [ ] Constitutional compliance verified
- [ ] No hardcoded secrets or API keys
- [ ] Error messages are helpful
- [ ] Optional dependencies handled correctly
- [ ] Database migrations tested
- [ ] Git history clean (no "fix typo" commits)

**Process:**
1. Open pull request
2. Automated checks run (CI/CD)
3. Request review from relevant role
4. Address feedback
5. Approve and merge

---

## 6. Reusable Patterns Catalog

### 6.1 Exporter Backend Pattern

**Use Case:** Support multiple export formats for the same data.

**Pattern:**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Exporter(ABC):
    """Abstract base class for exporters."""

    @abstractmethod
    def export(self, data: List[Dict[str, Any]], output_path: Path) -> None:
        """Export data to the specified format."""
        pass

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if required dependencies are installed."""
        pass

    @property
    @classmethod
    @abstractmethod
    def optional_dependency(cls) -> str:
        """Name of optional dependency package."""
        pass

class ObsidianExporter(Exporter):
    """Export to Obsidian markdown format."""

    optional_dependency = None  # No extra deps

    @classmethod
    def is_available(cls) -> bool:
        return True  # Always available

    def export(self, data: List[Dict[str, Any]], output_path: Path) -> None:
        """Export search results to Obsidian markdown."""
        for item in data:
            # Create markdown with YAML frontmatter
            markdown = self._format_obsidian(item)
            file_path = output_path / f"{item['video_id']}.md"
            file_path.write_text(markdown)

    def _format_obsidian(self, item: Dict[str, Any]) -> str:
        """Format item as Obsidian markdown."""
        return f"""---
title: {item['title']}
channel: {item['channel']}
video_id: {item['video_id']}
url: {item['url']}
published_at: {item['published_at']}
tags: [{', '.join(item.get('tags', []))}]
---

# {item['title']}

{item['text']}

Source: [{item['channel']}]({item['url']})
"""
```

**Usage:**
```python
# Factory pattern for creating exporters
class ExporterFactory:
    _exporters = {
        "obsidian": ObsidianExporter,
        "notion": NotionExporter,
        "bibtex": BibTeXExporter,
        "json": JSONExporter,
    }

    @classmethod
    def create(cls, format: str) -> Exporter:
        exporter_class = cls._exporters.get(format)
        if not exporter_class:
            raise ValueError(f"Unknown format: {format}")

        if not exporter_class.is_available():
            dep = exporter_class.optional_dependency
            raise click.ClickException(
                f"Format '{format}' requires '{dep}'. "
                f"Install with: pip install yt-fts[{format}]"
            )

        return exporter_class()

# CLI usage
@click.command()
@click.option("--format", "-f", default="obsidian")
@click.option("--output", "-o", default="./exports")
def export(format: str, output: str):
    """Export search results."""
    exporter = ExporterFactory.create(format)
    exporter.export(results, Path(output))
```

**Benefits:**
- Easy to add new formats
- Centralized dependency checking
- Consistent interface
- Testable in isolation

### 6.2 LLM Provider Abstraction

**Use Case:** Support multiple LLM providers (OpenAI, Anthropic, local models).

**Pattern:**
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()

    @abstractmethod
    def generate_completion(self, prompt: str, **kwargs) -> str:
        """Generate a completion from a prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API key valid)."""
        pass

    @property
    @abstractmethod
    def optional_dependency(self) -> str:
        """Name of optional dependency package."""
        pass

    def _get_api_key(self) -> str:
        """Get API key from environment."""
        env_var = f"{self.__class__.__name__.upper()}_API_KEY"
        key = os.getenv(env_var)
        if not key:
            raise click.ClickException(
                f"API key not found. Set {env_var} environment variable."
            )
        return key

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    optional_dependency = "openai"

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        super().__init__(api_key)
        self.model = model
        self._client = None

    def is_available(self) -> bool:
        try:
            import openai
            openai.api_key = self.api_key
            # Test API with minimal request
            openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False

    def generate_completion(self, prompt: str, **kwargs) -> str:
        import openai
        openai.api_key = self.api_key

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )

        return response.choices[0].message.content

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    optional_dependency = "anthropic"

    def is_available(self) -> bool:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            # Test API
            client.completions.create(
                model="claude-3",
                prompt="test",
                max_tokens_to_sample=1
            )
            return True
        except Exception:
            return False

    def generate_completion(self, prompt: str, **kwargs) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)

        response = client.completions.create(
            model="claude-3-sonnet",
            prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
            max_tokens_to_sample=kwargs.get("max_tokens", 1000)
        )

        return response.completion
```

**Usage:**
```python
# Service layer
class FlashcardGenerator:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def generate(self, transcript: str, num_cards: int = 10) -> List[Flashcard]:
        prompt = f"""
        Generate {num_cards} flashcards from the following transcript.

        Transcript:
        {transcript}

        Format each card as:
        Q: [Question]
        A: [Answer]
        """

        response = self.llm.generate_completion(prompt)

        # Parse response into Flashcard objects
        return self._parse_flashcards(response)

# CLI usage
@click.command()
@click.option("--provider", default="openai", type=click.Choice(["openai", "anthropic"]))
@click.option("--model", default="gpt-4")
def flashcards(provider: str, model: str):
    """Generate flashcards using LLM."""

    # Create provider based on user choice
    if provider == "openai":
        llm = OpenAIProvider(model=model)
    elif provider == "anthropic":
        llm = AnthropicProvider()

    # Check availability
    if not llm.is_available():
        console.print("[red]LLM provider not available. Check API key.[/red]")
        sys.exit(1)

    # Generate flashcards
    generator = FlashcardGenerator(llm)
    cards = generator.generate(transcript)

    # Export
    export_anki(cards, "flashcards.apkg")
```

**Benefits:**
- Easy to swap providers
- Supports multiple providers simultaneously
- Clear fallback strategy
- Testable with mock providers

### 6.3 Translation Service Interface

**Use Case:** Support multiple translation services (Google, DeepL, OpenAI).

**Pattern:**
```python
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

@dataclass
class TranslationResult:
    """Result of translation operation."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    service: str

class TranslationService(ABC):
    """Abstract base class for translation services."""

    @abstractmethod
    def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> TranslationResult:
        """Translate text from source language to target language."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if service is available."""
        pass

    @property
    @abstractmethod
    def optional_dependency(self) -> str:
        """Name of optional dependency package."""
        pass

class GoogleTranslateService(TranslationService):
    """Google Cloud Translation service."""

    optional_dependency = "google-cloud-translate"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_TRANSLATE_API_KEY")
        self._client = None

    def is_available(self) -> bool:
        try:
            from google.cloud import translate_v2 as translate
            self._client = translate.Client(api_key=self.api_key)
            return True
        except Exception:
            return False

    def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> TranslationResult:
        if not self._client:
            from google.cloud import translate_v2 as translate
            self._client = translate.Client(api_key=self.api_key)

        result = self._client.translate(
            text,
            target_language=target_lang,
            source_language=source_lang
        )

        return TranslationResult(
            original_text=text,
            translated_text=result["translatedText"],
            source_language=result["detectedSourceLanguage"],
            target_language=target_lang,
            service="google"
        )

class DeepLTranslateService(TranslationService):
    """DeepL translation service."""

    optional_dependency = "deepl"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPL_API_KEY")
        self._client = None

    def is_available(self) -> bool:
        try:
            import deepl
            self._client = deepl.Translator(self.api_key)
            self._client.get_usage()
            return True
        except Exception:
            return False

    def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> TranslationResult:
        if not self._client:
            import deepl
            self._client = deepl.Translator(self.api_key)

        result = self._client.translate_text(
            text,
            target_lang=target_lang.upper(),
            source_lang=None if source_lang == "auto" else source_lang.upper()
        )

        return TranslationResult(
            original_text=text,
            translated_text=result.text,
            source_language=result.detected_source_lang.lower(),
            target_language=target_lang,
            service="deepl"
        )
```

**Usage with Caching:**
```python
from functools import lru_cache
import hashlib

class CachedTranslationService:
    """Translation service with caching to reduce API calls."""

    def __init__(self, service: TranslationService, cache_db: sqlite3.Connection):
        self.service = service
        self.cache_db = cache_db

        # Create cache table if not exists
        self.cache_db.execute("""
            CREATE TABLE IF NOT EXISTS translation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT UNIQUE,
                original_text TEXT,
                translated_text TEXT,
                source_lang TEXT,
                target_lang TEXT,
                service TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> TranslationResult:
        # Check cache first
        text_hash = hashlib.md5(f"{text}:{source_lang}:{target_lang}".encode()).hexdigest()

        cached = self.cache_db.execute(
            "SELECT translated_text FROM translation_cache WHERE text_hash = ?",
            (text_hash,)
        ).fetchone()

        if cached:
            return TranslationResult(
                original_text=text,
                translated_text=cached[0],
                source_language=source_lang,
                target_language=target_lang,
                service=f"{self.service.__class__.__name__} (cached)"
            )

        # Not in cache, call service
        result = self.service.translate(text, target_lang, source_lang)

        # Store in cache
        self.cache_db.execute(
            "INSERT INTO translation_cache (text_hash, original_text, translated_text, source_lang, target_lang, service) VALUES (?, ?, ?, ?, ?, ?)",
            (text_hash, text, result.translated_text, source_lang, target_lang, result.service)
        )
        self.cache_db.commit()

        return result
```

**Benefits:**
- Reduces API costs through caching
- Easy to swap translation providers
- Consistent interface across services
- Fallback strategy if one service fails

### 6.4 Citation Formatter Pattern

**Use Case:** Generate citations in multiple academic formats.

**Pattern:**
```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any

class CitationStyle(ABC):
    """Abstract base class for citation styles."""

    @abstractmethod
    def format(self, video: Dict[str, Any]) -> str:
        """Format a video citation in this style."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the citation style."""
        pass

class APAStyle(CitationStyle):
    """APA 7th edition citation style."""

    name = "APA 7th Edition"

    def format(self, video: Dict[str, Any]) -> str:
        publish_date = datetime.fromisoformat(video["published_at"])
        formatted_date = publish_date.strftime("%Y, %B %d")

        return (
            f"{video['channel_name']}. ({formatted_date}). "
            f"*{video['title']}* [Video]. YouTube. "
            f"{video['url']}"
        )

class MLAStyle(CitationStyle):
    """MLA 9th edition citation style."""

    name = "MLA 9th Edition"

    def format(self, video: Dict[str, Any]) -> str:
        publish_date = datetime.fromisoformat(video["published_at"])
        formatted_date = publish_date.strftime("%d %b. %Y")
        access_date = datetime.now().strftime("%d %b. %Y")

        return (
            f"{video['channel_name']}. \"{video['title']}.\" "
            f"*YouTube*, {formatted_date}, "
            f"{video['url']}. "
            f"Accessed {access_date}."
        )

class BibTeXStyle(CitationStyle):
    """BibTeX citation style."""

    name = "BibTeX"

    def format(self, video: Dict[str, Any]) -> str:
        publish_date = datetime.fromisoformat(video["published_at"])
        year = publish_date.strftime("%Y")
        month = publish_date.strftime("%B")

        # Create safe ID from title (BibTeX IDs must be alphanumeric)
        safe_id = re.sub(r'[^\w]', '', video['title'])[:20]

        return (
            f"@online{{{safe_id},\n"
            f"  author = {{{video['channel_name']}}},\n"
            f"  title = {{{video['title']}}},\n"
            f"  year = {{{year}}},\n"
            f"  month = {{{month}}},\n"
            f"  url = {{{video['url']}}},\n"
            f"  urldate = {{{datetime.now().strftime('%Y-%m-%d')}}}\n"
            f"}}"
        )

class CitationFormatter:
    """Formatter that supports multiple citation styles."""

    _styles: Dict[str, type[CitationStyle]] = {
        "apa": APAStyle,
        "mla": MLAStyle,
        "bibtex": BibTeXStyle,
    }

    @classmethod
    def format(cls, video: Dict[str, Any], style: str = "apa") -> str:
        """Format a video citation in the specified style."""
        style_class = cls._styles.get(style.lower())
        if not style_class:
            available = ", ".join(cls._styles.keys())
            raise ValueError(f"Unknown style: {style}. Available: {available}")

        formatter = style_class()
        return formatter.format(video)

    @classmethod
    def get_available_styles(cls) -> list[str]:
        """Get list of available citation styles."""
        return list(cls._styles.keys())
```

**Usage:**
```python
@click.command()
@click.argument("video_id")
@click.option("--format", "-f", default="apa", type=click.Choice(["apa", "mla", "bibtex"]))
@click.option("--output", "-o", help="Output file (default: stdout)")
def cite(video_id: str, format: str, output: Optional[str]):
    """Generate citation for a video."""

    # Get video metadata
    video = get_video_metadata(video_id)

    # Generate citation
    citation = CitationFormatter.format(video, style=format)

    # Output
    if output:
        Path(output).write_text(citation)
        console.print(f"[green]Citation saved to {output}[/green]")
    else:
        console.print(citation)
```

**Benefits:**
- Easy to add new citation styles
- Consistent interface
- No complex if/elif chains
- Testable in isolation

### 6.5 Search Filter Extension Pattern

**Use Case:** Support extensible search filters without modifying core search logic.

**Pattern:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class SearchFilter(ABC):
    """Abstract base class for search filters."""

    @abstractmethod
    def apply(self, query: str, params: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Apply filter to SQL query and parameters.

        Returns modified (query, params) tuple.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the filter."""
        pass

class TimeFilter(SearchFilter):
    """Filter by publication date."""

    name = "time"

    def apply(self, query: str, params: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        time_conditions = []

        # --after filter
        if "after" in params:
            time_conditions.append("Videos.published_at >= :after")

        # --before filter
        if "before" in params:
            time_conditions.append("Videos.published_at <= :before")

        # Add time conditions to query
        if time_conditions:
            time_clause = " AND " + " AND ".join(time_conditions)
            query = query.replace(
                "WHERE",
                f"WHERE {' AND '.join(time_conditions)}"
            )

        return query, params

class ChannelFilter(SearchFilter):
    """Filter by channel."""

    name = "channel"

    def apply(self, query: str, params: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        if "channel_id" in params:
            query += " AND Videos.channel_id = :channel_id"
        return query, params

class LanguageFilter(SearchFilter):
    """Filter by subtitle language."""

    name = "language"

    def apply(self, query: str, params: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        if "language" in params:
            query += " AND Subtitles.language_code = :language"
        return query, params

class SearchFilterChain:
    """Chain of responsibility for search filters."""

    def __init__(self):
        self._filters: List[SearchFilter] = []

    def add_filter(self, filter: SearchFilter) -> "SearchFilterChain":
        """Add a filter to the chain."""
        self._filters.append(filter)
        return self

    def apply(self, base_query: str, params: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Apply all filters in the chain."""
        query = base_query

        for filter in self._filters:
            query, params = filter.apply(query, params)

        return query, params

# Usage in search service
class SearchService:
    def __init__(self):
        self.filter_chain = SearchFilterChain()
        self.filter_chain.add_filter(TimeFilter())
        self.filter_chain.add_filter(ChannelFilter())
        self.filter_chain.add_filter(LanguageFilter())

    def search(self, query_text: str, **filters) -> List[Dict[str, Any]]:
        # Base query
        query = """
            SELECT DISTINCT Videos.*
            FROM Videos
            JOIN Subtitles ON Videos.video_id = Subtitles.video_id
            WHERE Subtitles_fts MATCH :query
        """

        params = {"query": query_text, **filters}

        # Apply filter chain
        query, params = self.filter_chain.apply(query, params)

        # Execute query
        results = db.execute(query, params).fetchall()

        return results
```

**Benefits:**
- Easy to add new filters without modifying core search logic
- Filters are composable and reusable
- Clear separation of concerns
- Testable in isolation

---

## 7. Knowledge Assets

### 7.1 Architectural Decision Records

**Decision 1: SQLite vs PostgreSQL for v2.0**

**Status:** Decided - SQLite for v2.0, PostgreSQL optional for v2.1

**Context:**
- SQLite has single-writer limitation
- API server needs concurrent read access
- Considered PostgreSQL for better concurrency

**Decision:**
- Use SQLite with WAL mode for v2.0
- Document limitation for API server (single worker)
- Plan PostgreSQL option for v2.1 if needed

**Rationale:**
- SQLite is sufficient for personal/hobbyist use cases
- WAL mode allows concurrent readers
- Simpler deployment and maintenance
- PostgreSQL adds complexity and dependencies

**Consequences:**
- API server limited to single worker (uvicorn --workers 1)
- Large-scale deployments should wait for v2.1
- Documentation must clearly state limitations

**Decision 2: Plugin System Architecture**

**Status:** Decided - Simple plugin API, no full plugin system

**Context:**
- User deferred plugin system decision: "You decide"
- Options: No plugins, simple API, full plugin system

**Decision:**
- Implement simple plugin API with base classes
- Use Python entry points for discovery
- No sandboxing or security isolation
- Community can fork and extend as needed

**Rationale:**
- Full plugin systems are overkill for CLI tools
- Simple API enables community contributions
- Low complexity, easy to maintain
- Trusted plugins (like pytest) don't need sandboxing

**Consequences:**
- Export backends pluggable via base classes
- LLM providers pluggable via abstract interface
- Translation services pluggable via interface
- No official plugin marketplace

**Decision 3: LLM Cost Management**

**Status:** Decided - Hybrid approach with local-first

**Context:**
- LLM API usage can be expensive
- Chapter detection and flashcards require many tokens
- User wants cost control

**Decision:**
- Implement local model support (Ollama) first
- Provide `--llm-provider` flag: `openai`, `anthropic`, `ollama`
- Default to local if available, fallback to API
- Clear cost estimation before running

**Rationale:**
- Local models are free after initial setup
- APIs provide higher quality when needed
- User control over costs
- Progressive enhancement (basic works locally, advanced uses API)

**Consequences:**
- Features work without API keys (using Ollama)
- Better quality available with paid APIs
- Clear documentation of costs
- Cost estimation in CLI output

**Decision 4: Multi-Language Search Strategy**

**Status:** Decided - Single FTS5 table with language filter

**Context:**
- Each language requires separate FTS5 table
- Multiple indexes increase storage and complexity
- Performance concerns with many languages

**Decision:**
- Use single FTS5 table with language_code filter
- Add language_code column to Subtitles table
- Filter with WHERE clause: `WHERE language_code = 'es'`
- Cross-language search with UNION

**Rationale:**
- Simpler architecture
- Easier maintenance
- Performance acceptable for < 5 languages
- Can optimize later if needed

**Consequences:**
- Single FTS5 index for all languages
- Language filtering in WHERE clause
- Storage efficient (single text storage)
- Query performance good for typical use cases

**Decision 5: Breaking Changes for v2.0**

**Status:** Decided - Willing to implement breaking changes

**Context:**
- Database schema changes required
- Some features require incompatible changes
- Balancing backward compatibility with improvements

**Decision:**
- Implement v2.0 with breaking changes
- Provide migration tool from v1.x to v2.0
- Clear documentation of changes
- Beta testing period before stable release

**Rationale:**
- Technical debt from v1.x limits progress
- User willing to reinstall for better features
- Migration script reduces pain
- v2.0 signals major update

**Consequences:**
- Database migration required
- Some command syntax changes
- Configuration file format changes
- Deprecation warnings for removed features

### 7.2 Code Snippets Library

#### SQLite Migration Template

```python
def migrate_to_v2(db_path: str) -> None:
    """Add language_code column to Subtitles table."""
    db = sqlite3.connect(db_path)

    try:
        # Check if migration already applied
        cursor = db.execute(
            "SELECT COUNT(*) FROM pragma_table_info('Subtitles') WHERE name='language_code'"
        )
        if cursor.fetchone()[0] > 0:
            logger.info("Migration v2 already applied")
            return

        logger.info("Applying migration v2: Add language_code support")

        # 1. Create backup
        backup_path = f"{db_path}.backup_{datetime.now().isoformat()}"
        shutil.copy2(db_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

        # 2. Apply migration
        db.execute("ALTER TABLE Subtitles ADD COLUMN language_code TEXT DEFAULT 'en'")
        db.execute("CREATE INDEX IF NOT EXISTS idx_subtitles_language ON Subtitles(language_code)")

        # 3. Update schema version
        db.execute("INSERT INTO SchemaVersion (version, description) VALUES (2, 'Add multi-language support')")

        db.commit()
        logger.info("Migration v2 completed successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {e}")
        raise
```

#### Optional Dependency Checker

```python
def check_import(module_name: str, extras_name: str) -> None:
    """Check if optional dependency is installed, raise helpful error if not."""
    try:
        importlib.import_module(module_name)
    except ImportError:
        raise click.ClickException(
            f"Required module '{module_name}' not found.\n"
            f"This feature requires optional dependencies.\n"
            f"Install with: pip install yt-fts[{extras_name}]\n"
            f"Or install all extras: pip install yt-fts[all]"
        )
```

#### Explainable Error Message

```python
def explainable_error(error: Exception, context: dict) -> None:
    """Display helpful error message with resolution steps."""

    console = Console()

    if isinstance(error, NotionAPIError):
        if error.status_code == 401:
            console.print("""
[red]❌ Notion API Authentication Failed[/red]

[b]What happened:[/b] Your Notion API token is invalid or expired.

[b]How to fix:[/b]
  1. Get a new token: https://www.notion.so/my-integrations
  2. Set environment variable:
     export NOTION_API_KEY=your_token_here
  3. Try again

[dim]Error details: {error.message}[/dim]
            """)

    elif isinstance(error, SQLiteError):
        console.print("""
[red]❌ Database Error[/red]

[b]What happened:[/b] The database operation failed.

[b]How to fix:[/b]
  1. Check database file permissions
  2. Ensure disk space is available
  3. Try running: yt-fts db vacuum
  4. Run with --verbose for more details

[dim]Error: {error}[/dim]
        """)
```

### 7.3 External References

**Tools & Libraries:**
- [Click](https://click.palletsprojects.com/) - Python CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [SQLite FTS5](https://www.sqlite.org/fts3.html) - Full-text search
- [FastAPI](https://fastapi.tiangolo.com/) - API server framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [pytest](https://docs.pytest.org/) - Testing framework

**Documentation:**
- [CWO15 Workflow](https://github.com/your-org/cwo15) - Project planning workflow
- [Keep a Changelog](https://keepachangelog.com/) - Changelog format
- [OpenAPI Specification](https://swagger.io/specification/) - API documentation

**Standards:**
- [APA 7th Edition](https://apastyle.apa.org/) - Citation format
- [MLA 9th Edition](https://style.mla.org/) - Citation format
- [BibTeX](https://www.bibtex.org/) - Reference formatting
- [ISO 8601](https://www.iso.org/standard/70907.html) - Date/time format

---

## Conclusion

This Learning & Patterns analysis captures the technical and process insights from planning the yt-fts v2.0 additional features. The patterns, lessons, and recommendations documented here form a knowledge asset that can be applied to future projects, reducing rework and accelerating development.

**Key Takeaways:**

1. **Modular Architecture Pays Off:** Clear separation between CLI, services, and data layers enables parallel development and easier maintenance.

2. **Optional Dependencies Work:** 100% feature flag support keeps the core lightweight while enabling powerful optional features.

3. **Constitutional Compliance is Achievable:** Integrating user autonomy, privacy, and transparency from the beginning prevents ethical debt.

4. **Abstract Interfaces Enable Flexibility:** Provider abstractions for LLM, translation, and export services make the system extensible and testable.

5. **Process Matters:** Structured planning workflows (CWO15) and sprint organization improve estimation and reduce risk.

**Next Steps:**

- Apply these patterns to implementation phases
- Update documentation as patterns evolve
- Share learnings with team and community
- Refine patterns based on real-world usage

**Document Version:** 1.0
**Last Updated:** 2025-12-24
**Maintained By:** Development Team

---

**END OF LEARNING & PATTERNS ANALYSIS**
