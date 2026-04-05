# Specification: yt-fts Additional Features Research & Implementation

**TSK:** TSK-251224-YtFtsFeatures-1956
**Created:** 2024-12-24
**Status:** Draft
**Version:** 2.0.0

---

## Overview

YouTube Full-Text Search (yt-fts) is a Python CLI tool for searching YouTube video transcripts using SQLite FTS5. This specification defines the strategic implementation of 13 additional features organized into 4 sprints, targeting truth seekers, researchers, and learners while maintaining constitutional compliance (user autonomy, privacy protection, transparent operations).

**Key Decisions:**
- Excluding content creator features (analytics, competitor comparison)
- Strategic approach willing to implement v2.0 breaking changes
- 100% optional dependency support with feature flags
- Plugin system decision deferred based on technical efficiency analysis

---

## Requirements

### Functional Requirements by Sprint

#### Sprint 1: Enhanced Search (Quick Wins)

**FR-1.1: Time-Based Search Filters**
- System shall support `--after DATE` filter to restrict results to videos published after specified date
- System shall support `--before DATE` filter to restrict results to videos published before specified date
- System shall support `--last DURATION` shorthand (e.g., `--last 30d`, `--last 6m`)
- Date formats supported: ISO 8601 (YYYY-MM-DD), relative dates
- Database schema updated with `published_at` column and index

**FR-1.2: Proximity Search (NEAR Queries)**
- System shall support NEAR queries using SQLite FTS5 syntax: `NEAR(term1 term2, distance)`
- Default proximity distance: 10 tokens
- CLI option: `--proximity N` to set custom distance
- CLI option: `--near "term"` to find terms near each other
- Performance baseline: NEAR queries <2 seconds on 100K+ subtitle database

**FR-1.3: Search History and Saved Queries**
- System shall maintain search history in SQLite table with timestamp, query, filters, result count
- System shall provide `history` command to display recent searches with `--limit` option
- System shall provide `history save "query name"` to save frequently used queries
- System shall provide `history run "query name"` to re-run saved queries
- Search history can be disabled via configuration (`search_history_enabled = false`)
- Automatic retention policy: configurable, default 90 days

**FR-1.4: JSON Output Mode**
- System shall support `--json` flag on all search and export commands
- JSON output format: structured with query metadata, results array, timestamps, performance metrics
- jq-compatible streaming output via `--jsonl` flag
- Error responses in JSON format with error message, query, and timestamp
- Standard fields: video_id, title, url, channel, timestamp, text, published_at

#### Sprint 2: Knowledge Management

**FR-2.1: Obsidian/Roam Research Markdown Export**
- System shall export transcripts as Markdown with YAML frontmatter
- Frontmatter includes: title, youtube_id, url, channel, published_at, duration, tags
- Timestamps formatted as `[[HH:MM:SS]]` for clickable video links
- Wikilinks to related videos using `[[Video Title]]` syntax
- CLI command: `export obsidian --channel "@3Blue1Brown" --output "./MyVault/"`
- Batch export support for channels and search results
- Roam Research compatibility mode with `#[[page references]]` syntax

**FR-2.2: Citation Export (BibTeX, APA, MLA)**
- System shall generate BibTeX entries with `@misc{youtube_ID}` format
- System shall generate APA 7th edition citations
- System shall generate MLA 9th edition citations
- System shall generate CSL-JSON for Zotero/Pandoc integration
- CLI command: `cite --video "VIDEO_ID" --format {bibtex|apa|mla|csl-json}`
- Batch citation generation: `cite --channel "@Channel" --format bibtex > references.bib`
- Timestamp references supported for direct quotes

**FR-2.3: Notion/Zotero Integration**
- System shall export transcripts to Notion pages via official API
- Notion integration requires NOTION_API_KEY environment variable
- System shall create Notion databases for video collections
- System shall export to Zotero via REST API (ZOTERO_LIBRARY_ID, ZOTERO_API_KEY)
- Alternative: BibTeX export for manual Zotero import
- CLI commands:
  - `export notion --video "VIDEO_ID" --page-id "PAGE_ID"`
  - `export zotero --video "VIDEO_ID"`

#### Sprint 3: Learning Features

**FR-3.1: Flashcard Generation (Anki Export)**
- System shall generate Anki-compatible CSV with front/back fields
- Flashcards generated from transcript key concepts using LLM extraction
- Each card includes timestamp link back to source video
- Deck organization: by channel, topic, or custom
- CLI command: `export anki --video "VIDEO_ID" --max-cards 20`
- Tags: youtube, channel name, auto-extracted topics
- Basic mode (no LLM) generates simple Q&A from chapter summaries

**FR-3.2: Chapter/Segment Detection**
- System shall extract YouTube auto-generated chapters when available
- System shall detect chapters using sentence transformer embeddings (optional)
- System shall detect chapters using LLM summarization (optional)
- CLI command: `chapters --video "VIDEO_ID" --method {youtube|embeddings|llm}`
- Database storage: chapters table with start_time, end_time, title, summary
- Export chapters to YouTube chapter format file

**FR-3.3: Multi-Language Subtitle Support**
- System shall download multiple subtitle tracks per video
- System shall list available languages: `languages --video "VIDEO_ID"`
- Database schema: subtitles table extended with language_code, is_generated columns
- Language metadata table tracks available languages per video
- Search scoped to specific language: `search "query" --language es`

**FR-3.4: Translation Layer**
- System shall translate subtitles from source language to target language
- Translation services: Google Translate (free), DeepL (paid), OpenAI (paid)
- Pre-index translation: translate and store on download
- Query-time translation: translate query, search in multiple languages
- CLI command: `translate --video "VIDEO_ID" --target-lang en --service google`
- Cross-language search: `search "query" --cross-lang --languages en,es,fr`

#### Sprint 4: Automation & Infrastructure

**FR-4.1: Watch Mode / Auto-Update**
- System shall monitor channels for new uploads periodically
- System shall auto-download new video transcripts
- Persistent job storage (SQLite) survives restarts
- CLI commands:
  - `watch add --channel "@Channel" --interval 60` (minutes)
  - `watch list` - show all scheduled jobs
  - `watch remove --job-id JOB_ID`
  - `watch start` - run as background daemon
- Scheduling libraries: `schedule` (simple) or `apscheduler` (production)
- Cron expression support for advanced scheduling

**FR-4.2: API Server Mode**
- System shall provide FastAPI REST API for all CLI operations
- Async SQLite using aiosqlite for non-blocking operations
- OpenAPI/Swagger documentation at `/docs` and `/redoc`
- WebSocket endpoint for real-time search results
- CLI command: `serve --host 127.0.0.1 --port 8000`
- Authentication: API key header (optional, for production)
- Rate limiting: configurable, default 100 req/min

### Non-Functional Requirements

**NFR-1: Performance**
- FTS5 search queries: <500ms for typical queries
- NEAR queries: <2 seconds
- Semantic search: <2 seconds
- API response time: <200ms for search, <1s for exports
- Database indexing: proper indexes on timestamps, language codes, channels

**NFR-2: Reliability**
- Error handling: graceful degradation for missing optional dependencies
- Database transactions: ACID compliance for data integrity
- Download failures: continue-on-error philosophy with categorized error reporting
- Rate limit recovery: exponential backoff for external APIs

**NFR-3: Maintainability**
- Code coverage: 80%+ for new features
- Type hints: all public functions annotated
- Documentation: docstrings for all modules and functions
- Modular architecture: clear separation of concerns (CLI, services, data)

**NFR-4: Usability**
- CLI consistency: existing command patterns maintained
- Help text: examples for all new commands
- Progress indicators: Rich progress bars for long operations
- Error messages: actionable, explain what went wrong and how to fix

**NFR-5: Extensibility**
- Plugin architecture: exporter backends pluggable
- LLM providers: swappable (OpenAI, Anthropic, local models)
- Citation styles: loadable CSL JSON files
- Translation services: unified interface for multiple providers

---

## User Stories

### Truth Seeker: Finding Factual Information Across Time

**US-TS-1: Temporal Search for Fact Verification**
**As a** truth seeker researching a claim
**I want** to search for mentions of a topic within a specific date range
**So that** I can verify when information was discussed and track narrative changes

**Acceptance Criteria:**
- [ ] User can run: `search "climate change" --after "2020-01-01" --before "2023-12-31"`
- [ ] Results are filtered by video publish date
- [ ] Shorthand supported: `search "AI safety" --last 90d`
- [ ] Relative dates work: `--last 6m`, `--last 1y`

### Researcher: Academic Citation Management

**US-R-1: Export Video Sources with Proper Citations**
**As a** academic researcher writing a paper
**I want** to export video transcripts with academic citations
**So that** I can properly cite YouTube sources in my bibliography

**Acceptance Criteria:**
- [ ] User can run: `cite --video "dQw4w9WgXcQ" --format bibtex`
- [ ] Output includes author, title, publication date, URL
- [ ] APA format: `3Blue1Brown. (2024, January 15). Title [Video]. YouTube. URL`
- [ ] Batch export: `cite --channel "@3Blue1Brown" --format apa > references.txt`
- [ ] Timestamp references included for direct quotes

**US-R-2: Build Knowledge Base in Obsidian**
**As a** researcher building a personal knowledge base
**I want** to export transcripts as Obsidian markdown with wikilinks
**So that** I can cross-reference videos in my PKM system

**Acceptance Criteria:**
- [ ] User can run: `export obsidian --channel "@CrashCourse" --output "./MyVault/"`
- [ ] Markdown files include YAML frontmatter with metadata
- [ ] Timestamps formatted as wikilinks: `[[10:30]]`
- [ ] Related videos linked: `- [[Related Video Title]]`
- [ ] Tags extracted from video content: `tags: [physics, education]`

### Learner: Study with Flashcards

**US-L-1: Generate Study Materials from Videos**
**As a** student studying from educational videos
**I want** to generate flashcards from video transcripts
**So that** I can study key concepts using Anki

**Acceptance Criteria:**
- [ ] User can run: `export anki --video "VIDEO_ID" --max-cards 20`
- [ ] Flashcards exported in Anki CSV format
- [ ] Each card includes link to timestamp in video
- [ ] Cards tagged by channel and topic
- [ ] Basic mode works without LLM: simple Q&A from chapters

**US-L-2: Navigate Long Videos with Chapters**
**As a** learner watching a 2-hour lecture
**I want** to see chapter breakdowns with timestamps
**So that** I can jump to specific topics

**Acceptance Criteria:**
- [ ] User can run: `chapters --video "VIDEO_ID" --method youtube`
- [ ] YouTube auto-chapters extracted when available
- [ ] Optional LLM-based chapter detection for videos without chapters
- [ ] Export chapters to text file or display in CLI

### Researcher: Multi-Language Analysis

**US-R-3: Search Across Languages**
**As a** researcher studying global perspectives
**I want** to search for the same topic across multiple languages
**So that** I can compare how topics are discussed differently

**Acceptance Criteria:**
- [ ] User can download: `download --video "VIDEO_ID" --languages es,de,fr`
- [ ] Search in specific language: `search "IA" --language es`
- [ ] Cross-language search: `search "AI" --cross-lang --languages en,es,fr`
- [ ] Translate and index: `translate --video "VIDEO_ID" --target-lang en`

### Power User: Automation and API Access

**US-P-1: Keep Library Updated Automatically**
**As a** power user with a large video library
**I want** to auto-download new videos from favorite channels
**So that** my library stays current without manual intervention

**Acceptance Criteria:**
- [ ] User can run: `watch add --channel "@3Blue1Brown" --interval 60`
- [ ] Watch daemon runs in background, checks for new videos
- [ ] New videos automatically downloaded and indexed
- [ ] Persistent job storage survives system restarts

**US-P-2: Integrate with Custom Tools**
**As a** developer building custom tools on top of yt-fts
**I want** to access search and export via REST API
**So that** I can integrate yt-fts into my applications

**Acceptance Criteria:**
- [ ] User can run: `serve --port 8080`
- [ ] API documentation available at `http://localhost:8080/docs`
- [ ] Search endpoint: `GET /api/v1/search?query=machine+learning`
- [ ] Export endpoint: `POST /api/v1/export/{video_id}?format=json`
- [ ] WebSocket endpoint for real-time search results

---

## Scope

### In Scope

**Sprint 1 - Enhanced Search:**
1. Time-based search filters (--after, --before, --last)
2. Proximity search using SQLite FTS5 NEAR queries
3. Search history storage and saved queries
4. JSON output mode for all commands

**Sprint 2 - Knowledge Management:**
5. Obsidian/Roam markdown export with YAML frontmatter
6. Citation generation (BibTeX, APA, MLA, CSL-JSON)
7. Notion API integration (optional)
8. Zotero integration via REST API or BibTeX export (optional)

**Sprint 3 - Learning Features:**
9. Anki CSV flashcard generation
10. Chapter detection (YouTube auto-chapters, LLM-based optional)
11. Multi-language subtitle download and indexing
12. Translation layer (Google, DeepL, OpenAI)

**Sprint 4 - Automation & Infrastructure:**
13. Watch mode with scheduling (schedule or apscheduler)
14. FastAPI REST API server with async SQLite

**Architecture & Infrastructure:**
- Database schema changes (new tables, indexes)
- Migration system for v1.x to v2.0 upgrade
- Optional dependency management with feature flags
- Configuration file system (TOML)
- Modular architecture with services layer

### Out of Scope

**Excluded by User Request:**
- Channel analytics dashboard
- Competitor comparison tools
- Plugin/extension system
- Distributed processing

**Future Considerations (Not v2.0):**
- Advanced NLP features (topic modeling, sentiment analysis)
- Social features (sharing, collaboration)
- Mobile apps
- Cloud synchronization
- Video download acceleration
- Live stream support

---

## Success Criteria

### Quantitative Metrics

- **Feature Coverage:** All 13 features implemented and tested
- **Test Coverage:** 80%+ code coverage for new features
- **Performance:**
  - FTS5 search: <500ms (95th percentile)
  - NEAR queries: <2s (95th percentile)
  - API response: <200ms (p50), <1s (p95)
- **Reliability:** 99%+ uptime for API server
- **Documentation:** 100% of commands have help text and examples

### Qualitative Outcomes

- **User Adoption:** Truth seekers, researchers, learners successfully use features
- **Constitutional Compliance:** 100% compliance with user autonomy, privacy, transparency
- **Backward Compatibility:** Migration path from v1.x to v2.0 documented and tested
- **Developer Experience:** Clear contribution guidelines, modular code, comprehensive docs

### Acceptance Testing

- **Sprint 1:** Can search with date filters, use NEAR queries, access history, export JSON
- **Sprint 2:** Can export to Obsidian, generate citations, integrate with Notion/Zotero
- **Sprint 3:** Can generate Anki cards, detect chapters, download multi-language subs, translate
- **Sprint 4:** Can run watch mode, access API server endpoints

---

## Technical Considerations

### Database Schema Changes

**New Tables:**
```sql
-- Search history
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    results_count INTEGER,
    filters TEXT  -- JSON: {"after": "2024-01-01", "channel_id": "UC..."}
);
CREATE INDEX idx_search_history_timestamp ON search_history(timestamp DESC);

-- Multi-language support
ALTER TABLE subtitles ADD COLUMN language_code TEXT DEFAULT 'en';
ALTER TABLE subtitles ADD COLUMN is_generated INTEGER DEFAULT 0;
CREATE INDEX idx_subtitles_language ON subtitles(video_id, language_code);

CREATE TABLE subtitle_languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    language_code TEXT NOT NULL,
    language_name TEXT,
    is_generated INTEGER,
    download_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id),
    UNIQUE(video_id, language_code)
);

-- Chapters
CREATE TABLE chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    title TEXT,
    start_time REAL NOT NULL,
    end_time REAL,
    summary TEXT,
    detection_method TEXT,  -- 'youtube', 'embeddings', 'llm'
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);
CREATE INDEX idx_chapters_video ON chapters(video_id, start_time);

-- Videos metadata
ALTER TABLE videos ADD COLUMN published_at TEXT;
CREATE INDEX idx_videos_published_at ON videos(published_at);
```

### Optional Dependencies Strategy

**Feature Groups:**
```toml
[project.optional-dependencies]
# Knowledge management
export-markdown = []  # No extra deps
notion = ["notion-client>=2.2.1"]
zotero = ["pyzotero>=1.5.21"]

# Learning features
anki = []  # No extra deps (CSV is stdlib)
chapters-embeddings = ["sentence-transformers>=2.2.0", "torch>=2.0.0"]
chapters-llm = ["openai>=1.0.0"]

# Translation
translate-google = ["deep-translator>=1.11.4"]
translate-deepl = ["deepl>=1.15.0"]
translate-openai = ["openai>=1.0.0"]

# Scheduling
schedule = ["schedule>=1.2.0"]
apscheduler = ["apscheduler>=3.10.0"]

# API server
api = ["fastapi>=0.104.0", "uvicorn[standard]>=0.24.0", "aiosqlite>=0.19.0"]

# All extras
all = [
    "yt-fts[export-markdown,notion,zotero,anki,chapters-llm,translate-google,apscheduler,api]"
]
```

**Feature Flag Pattern:**
```python
# Lazy import with helpful error
def check_import(module_name, package_name=None):
    try:
        __import__(module_name)
        return True
    except ImportError:
        raise click.ClickException(
            f"Required module '{module_name}' not found. "
            f"Install with: pip install yt-fts[{package_name}]"
        )

# Usage
def export_notion(video_id):
    check_import("notion_client", "notion")
    from notion_client import Client
    # ... implementation
```

### Breaking Changes for v2.0

**Database Migrations:**
- Automatic migration on first run of v2.0
- User prompted: "Database needs migration. Backup created. Continue? [Y/n]"
- Migration rollback capability

**CLI Changes:**
- Existing commands remain compatible
- New flags added (non-breaking)
- Deprecated commands warned but not removed

**Configuration:**
- Old config file migration tool provided
- Environment variable naming: prefix with `YTF_FTS_`

### Performance Optimization

**Database Indexing:**
- Index on published_at for time-based filters
- Index on language_code for multi-language search
- Composite index on (video_id, language_code)

**Query Optimization:**
- Prepared statements for repeated queries
- Connection pooling for API server
- Query result caching (optional Redis)

**External API Limits:**
- Rate limit handling with exponential backoff
- Response caching to reduce API calls
- Cost estimation for LLM features

### Security Considerations

**API Key Management:**
- Environment variables for all API keys
- Never log or display API keys
- Key validation on startup

**Data Privacy:**
- Local-first architecture: all data stored locally
- No telemetry or analytics
- User controls search history retention

**API Server Security:**
- API key authentication for production deployments
- CORS configuration for web clients
- Rate limiting to prevent abuse
- Input validation and sanitization

---

## Open Questions

### Q1: Plugin System Architecture
**Question:** Should we implement a plugin system for extensibility?

**Context:** User deferred this decision: "4 You decide."

**Options:**
- **A: No formal plugin system** - Use Python entry points, community can fork
- **B: Simple plugin API** - Hooks for exporters, citation styles
- **C: Full plugin system** - Plugin discovery, sandboxing, PyPI integration

**Recommendation:** Option B (Simple plugin API)
- Low complexity, enables community contributions
- Define interfaces for exporters, LLM providers, translation services
- No sandboxing needed (plugins trusted, like pytest plugins)
- Implementation: `yt_fts.plugins` module with base classes

**Decision Needed:** By Sprint 2 (Knowledge Management) for exporter plugins

---

### Q2: LLM Cost Management
**Question:** How do we handle LLM API costs for chapter detection and flashcard generation?

**Context:** OpenAI API usage can become expensive with large video libraries.

**Options:**
- **A: Cost warnings** - Display estimated cost before running LLM features
- **B: Local models** - Support Ollama, llama.cpp for zero-cost generation
- **C: Hybrid approach** - Default to local, offer API as fallback
- **D: User responsibility** - Document costs, let user manage

**Recommendation:** Option C (Hybrid approach)
- Implement local model support (Ollama) first
- Provide `--llm-provider` flag: `openai`, `anthropic`, `ollama`
- Default to local if available, fall back to API
- Clear cost estimation when using paid APIs

**Decision Needed:** By Sprint 3 (Learning Features)

---

### Q3: API Server Deployment
**Question:** What's the recommended deployment strategy for the FastAPI server?

**Context:** SQLite has single-writer limitation, complicating multi-worker deployments.

**Options:**
- **A: Single worker** - Simple, limits concurrency
- **B: Connection pool** - Multiple workers with shared connections
- **C: Separate write DB** - Read replicas, single writer
- **D: PostgreSQL option** - Use Postgres for multi-writer scenarios

**Recommendation:** Option A (Single worker) for v2.0
- Sufficient for personal/hobbyist use cases
- Document limitations clearly
- Future v2.1 can add Postgres support for production deployments
- Use `workers=1` in uvicorn config

**Decision Needed:** By Sprint 4 (Infrastructure)

---

### Q4: Multi-Language Search Performance
**Question:** How do we maintain performance with multiple language indexes?

**Context:** Each language requires separate FTS5 table, increasing storage and query complexity.

**Options:**
- **A: Single FTS5 table** - Store all languages in one table with language_code filter
- **B: Separate tables per language** - `subtitles_en_fts`, `subtitles_es_fts`, etc.
- **C: Lazy translation** - Translate query on-demand, don't index all languages
- **D: User selects language** - Search only in user-specified language

**Recommendation:** Option A (Single FTS5 table with filter)
- Simpler architecture, easier maintenance
- Language filter in WHERE clause: `WHERE language_code = 'es'`
- Cross-language search: UNION across languages
- Performance acceptable for typical use cases (<5 languages)

**Decision Needed:** By Sprint 3 (Multi-Language Support)

---

### Q5: Watch Mode Platform Support
**Question:** How do we handle platform-specific service installation for watch mode?

**Context:** Running watch daemon as system service differs by platform (systemd, launchd, Windows Service).

**Options:**
- **A: User manual setup** - Document how to create services per platform
- **B: Auto-install** - Detect platform and install service files
- **C: No service mode** - Run as foreground process only
- **D: Docker container** - Provide Docker image for cross-platform consistency

**Recommendation:** Option A (User manual setup) + Option D (Docker option)
- Primary mode: `watch start` runs in foreground (user can screen/tmux)
- Documentation: systemd service file example
- Optional: Docker image with `yt-fts watch` as entrypoint
- Advanced users can create services themselves

**Decision Needed:** By Sprint 4 (Watch Mode)

---

## Dependencies

### External APIs (Optional)

**Notion API:**
- Documentation: https://developers.notion.com/docs
- Rate limits: 3 req/sec (integration token)
- Authentication: Bearer token (NOTION_API_KEY env var)

**Zotero API:**
- Documentation: https://www.zotero.org/support/dev/web_api/v3
- Rate limits: 20 req/10 sec (key auth)
- Authentication: API key (ZOTERO_API_KEY env var)

**Translation APIs:**
- Google Translate (via deep-translator): Free tier, rate limited
- DeepL: Paid API, higher quality
- OpenAI: Paid API, context-aware translation

**LLM APIs:**
- OpenAI: GPT-3.5/4 for summarization, chapter detection
- Anthropic: Claude for alternative LLM provider
- Local: Ollama, llama.cpp for zero-cost inference

### Python Packages

**Core Dependencies (Required):**
- `click>=8.1.0` - CLI framework
- `yt-dlp>=2023.0.0` - Video download
- `youtube-transcript-api>=0.6.0` - Transcript extraction
- `rich>=13.0.0` - Terminal UI
- `sqlite3` - Database (stdlib)

**Optional Dependencies (Feature-gated):**
See "Optional Dependencies Strategy" section above

---

## Constitutional Compliance

### User Autonomy

**Opt-in Design:**
- All features disabled by default, user must enable
- No forced upgrades or migrations
- User controls data retention (search history, cache)
- Clear opt-in for external API integrations

**Consent Management:**
- API keys never stored without user action
- Search history can be disabled: `search_history_enabled = false`
- Watch mode requires explicit channel subscription
- Data export: user can export all data at any time

### Privacy Protection

**Local-First Architecture:**
- All data stored locally in SQLite database
- No telemetry, analytics, or phone home
- No cloud dependencies except user-specified APIs
- API keys encrypted at rest (optional)

**Network Privacy:**
- External API calls documented and transparent
- Rate limiting prevents fingerprinting
- User-agent headers configurable
- No third-party tracking

### Transparent Operations

**Logging:**
- Verbose logging mode: `--verbose` flag
- Debug logs include file locations and line numbers
- Error messages explain root cause and resolution
- API rate limit status visible to user

**Documentation:**
- All commands have `--help` with examples
- Architecture documentation for contributors
- API documentation (OpenAPI/Swagger)
- Clear changelog with breaking changes highlighted

**Explainable Errors:**
```
❌ Notion API rate limit exceeded (3 req/sec)

Resolution:
1. Wait 60 seconds for rate limit to reset
2. Reduce concurrent requests
3. Check status: https://status.notion.com

Error ID: notion-429
Timestamp: 2024-12-24T10:30:00Z
```

---

## Implementation Phases

### Sprint 1: Enhanced Search (Weeks 1-2)
**Goal:** Deliver high-value search improvements with low risk

**Deliverables:**
- Time-based search filters
- NEAR proximity search
- Search history system
- JSON output mode

**Success Criteria:**
- Can search with date ranges
- Can use NEAR queries
- History command works
- JSON output valid and jq-compatible

### Sprint 2: Knowledge Management (Weeks 3-4)
**Goal:** Enable researchers to integrate yt-fts into their workflows

**Deliverables:**
- Obsidian/Roam markdown export
- Citation generation (all formats)
- Notion integration (optional)
- Zotero integration (optional)

**Success Criteria:**
- Markdown exports importable into Obsidian
- Citations match style guide requirements
- Notion/Zotero exports work with test accounts

### Sprint 3: Learning Features (Weeks 5-6)
**Goal:** Support learners with study tools and multi-language access

**Deliverables:**
- Anki flashcard generation
- Chapter detection (YouTube + optional LLM)
- Multi-language subtitle support
- Translation layer

**Success Criteria:**
- Anki imports generated CSV successfully
- Chapters detected and exported
- Multiple languages indexed and searchable
- Translation produces usable results

### Sprint 4: Automation & Infrastructure (Weeks 7-8)
**Goal:** Enable automation and API access for power users

**Deliverables:**
- Watch mode with scheduling
- FastAPI REST API server
- Documentation and examples
- v2.0 release preparation

**Success Criteria:**
- Watch daemon runs and downloads new videos
- API server responds to all endpoints
- Documentation complete
- Migration from v1.x tested

---

## Next Steps

1. **Review Specification** - Stakeholders approve scope and requirements
2. **Architecture Design** - Detailed technical design for services layer
3. **Task Breakdown** - Create implementation tasks for Sprint 1
4. **Development** - Begin Sprint 1 implementation

**Current Status:** Specification complete, awaiting architecture review

**Ready for:** `/arch` command (Step 5 of CWO12 workflow)

---

**Specification Version:** 1.0
**Last Updated:** 2024-12-24
**Next Review:** After architecture design complete
