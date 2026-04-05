# Requirements Analysis: yt-fts Additional Features
**Task ID:** TSK-251224-YtFtsFeatures-1956
**Project:** YouTube Full-Text Search (yt-fts) Additional Features
**Version:** 1.0
**Date:** 2025-12-24
**Status:** Step 2 - Requirements Analysis

---

## Executive Summary

This document outlines the comprehensive requirements for implementing 13 new features across 4 sprint phases for the yt-fts (YouTube Full-Text Search) CLI tool. The features are designed to enhance the tool's capabilities for **Truth Seekers**, **Researchers**, and **Learners** - three primary user personas focused on factual information discovery, academic research, and educational content consumption.

### Key Principles
- **User Autonomy**: All features must be optional, respecting user choice
- **Privacy Protection**: No data leaves the user's system without explicit consent
- **Transparent Operations**: Clear documentation of all operations and data flows
- **Optional Dependencies**: 100% support for feature flags and graceful degradation
- **Strategic Architecture**: Willing to make breaking changes for v2.0 improvements

---

## Table of Contents

1. [Target User Personas](#1-target-user-personas)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Constitutional Compliance Requirements](#4-constitutional-compliance-requirements)
5. [Technical Constraints & Dependencies](#5-technical-constraints--dependencies)
6. [User Interface Requirements](#6-user-interface-requirements)
7. [Data Architecture Requirements](#7-data-architecture-requirements)
8. [Integration Points & APIs](#8-integration-points--apis)
9. [Security & Privacy Requirements](#9-security--privacy-requirements)
10. [Performance Requirements](#10-performance-requirements)
11. [Testing & Validation Requirements](#11-testing--validation-requirements)
12. [Documentation Requirements](#12-documentation-requirements)

---

## 1. Target User Personas

### 1.1 Truth Seekers
**Definition:** Researchers, journalists, investigators finding factual information

**Characteristics:**
- Need precise, timestamped citations for verification
- Search across multiple channels for contradictory or corroborating information
- Export findings for reports and investigations
- Value chronological context and time-based filtering
- Require export to external tools (Obsidian, citation managers)

**Key Pain Points:**
- Manual transcription of video content is time-consuming
- Difficulty tracking when information was stated
- No easy way to find related content across channels
- Lack of proper citation formats for academic/professional work

**Feature Priorities:**
- Time-based search filters (--after, --before, --last)
- Citation export (BibTeX, APA, MLA)
- Proximity search for finding contextual quotes
- Obsidian markdown export with YAML frontmatter

### 1.2 Researchers
**Definition:** Academic, scientific, market researchers needing citations and exports

**Characteristics:**
- Require structured export formats for analysis tools
- Need to cite sources accurately in academic papers
- Batch process large video collections
- Integrate with existing research workflows (Zotero, Notion)
- Value semantic search for finding conceptually related content

**Key Pain Points:**
- Manual data entry from videos to research databases
- No standardized citation export
- Difficulty finding conceptually similar content (keyword limitations)
- Lack of integration with academic tools

**Feature Priorities:**
- Citation export (BibTeX, APA, MLA formats)
- Notion/Zotero integration
- Semantic search improvements
- JSON output mode for data analysis pipelines

### 1.3 Learners
**Definition:** Students, autodidacts using video content for education

**Characteristics:**
- Want to create study materials from video content
- Need chapter/segment detection for targeted learning
- Benefit from spaced repetition with flashcards
- Prefer interactive learning experiences
- May need content translated to native language

**Key Pain Points:**
- Rewatching entire videos to review specific concepts
- No easy way to create study materials from lectures
- Language barriers with educational content
- Difficulty finding specific topics within long videos

**Feature Priorities:**
- Flashcard generation (Anki export)
- Chapter/segment detection using LLM
- Multi-language subtitle support
- Translation layer for cross-language research

---

## 2. Functional Requirements

### Sprint 1 - Enhanced Search (Quick Wins)

#### FR-1.1: Time-Based Search Filters
**Priority:** High | **Complexity:** Low | **Effort:** 2-3 days

**Description:**
Add temporal filtering capabilities to search commands to restrict results to specific time ranges.

**User Stories:**
- As a Truth Seeker, I want to find videos mentioning a topic after a specific date so I can get the most current information
- As a Researcher, I want to search for content before a certain date to establish historical context
- As a Learner, I want to find recent videos on a topic to get the latest educational content

**Functional Requirements:**
1. `--after DATE` option to filter videos uploaded after specified date
2. `--before DATE` option to filter videos uploaded before specified date
3. `--last DURATION` option to filter videos within recent time window (e.g., "7d", "30d", "3m", "1y")
4. Date parsing support for multiple formats:
   - ISO 8601: "2024-12-24"
   - US format: "12/24/2024"
   - Relative: "yesterday", "today", "last week"
5. Time zone awareness using system local time
6. Integration with existing `search` and `vsearch` commands
7. Display of filtered time range in search results

**Acceptance Criteria:**
- Command: `yt-fts search "AI alignment" --after "2024-01-01" --before "2024-06-30"`
- Returns only videos from specified date range
- Error handling for invalid dates
- Time zone conversion works correctly
- Performance impact < 100ms for date filtering

**Technical Implementation:**
- Modify search queries to filter on `Videos.video_date` column
- Add date parsing utility functions
- Update CLI argument parsing in `search` command
- Add date validation and error messages

**Dependencies:**
- Existing database schema (`Videos.video_date` field)
- Python `datetime` module (built-in)
- `python-dateutil` for flexible date parsing (optional)

---

#### FR-1.2: Proximity Search (NEAR Queries)
**Priority:** High | **Complexity:** Medium | **Effort:** 3-5 days

**Description:**
Implement proximity search to find terms that appear within a specified distance of each other in subtitle text.

**User Stories:**
- As a Truth Seeker, I want to find "climate" within 5 words of "crisis" to get specific contextual quotes
- As a Researcher, I want to search for concepts discussed together to understand relationships
- As a Learner, I want to find exact phrases with context for better comprehension

**Functional Requirements:**
1. `NEAR/n` operator for finding terms within n words of each other
2. Default proximity distance of 10 words if not specified
3. Case-insensitive matching
4. Support for multiple NEAR operators in a single query
5. Syntax examples:
   - `"climate NEAR/5 crisis"`
   - `"machine LEAR/10 learning"`
   - `"neural NEAR/3 network NEAR/3 architecture"`
6. Integration with existing FTS query parser
7. Display of proximity distance in match highlighting

**Acceptance Criteria:**
- Query: `yt-fts search "climate NEAR/5 crisis" --channel "ChannelName"`
- Returns only subtitle segments where both terms appear within 5 words
- Highlights the full context window
- Performance comparable to regular FTS search (< 500ms for typical queries)
- Handles punctuation and word boundaries correctly

**Technical Implementation:**
- Extend SQLite FTS5 query parser with NEAR operator
- Custom query post-processing or use FTS5 NEAR operator
- Add proximity scoring algorithm
- Update result ranking to prioritize closer matches
- Modify `parse_query()` function in `database.py`

**Database Schema Impact:**
```sql
-- Use existing FTS5 full-text search
-- Add custom ranking function for proximity
SELECT * FROM Subtitles_fts
WHERE text MATCH 'climate NEAR/5 crisis'
ORDER BY bm25(Subtitles_fts) + proximity_score
```

**Dependencies:**
- SQLite FTS5 NEAR operator support
- Existing full-text search infrastructure
- Query parser modifications

---

#### FR-1.3: Search History and Saved Queries
**Priority:** Medium | **Complexity:** Medium | **Effort:** 5-7 days

**Description:**
Implement search history tracking and saved query management for reproducible research workflows.

**User Stories:**
- As a Truth Seeker, I want to save important searches so I can re-run them later to find new information
- As a Researcher, I want to document my search queries for reproducibility in academic papers
- As a Learner, I want to reuse effective search patterns for different topics

**Functional Requirements:**
1. Automatic logging of all search queries to history
2. History retention policy (configurable, default: 90 days)
3. `--save-name` option to save searches with descriptive names
4. `yt-fts history list` command to display search history
5. `yt-fts history search "pattern"` command to filter history
6. `yt-fts saved list` command to display saved queries
7. `yt-fts saved run NAME` command to re-execute saved queries
8. Export/import of saved queries as JSON
9. Tag system for organizing saved queries
10. Search metadata tracking:
    - Timestamp
    - Query text
    - Search scope (channel/video/all)
    - Result count
    - Command options used

**Acceptance Criteria:**
- Commands work independently:
  - `yt-fts search "AI safety" --save-name "alignment-research"`
  - `yt-fts history list --limit 20`
  - `yt-fts saved run "alignment-research"`
- History persists across sessions
- Saved queries export to/import from JSON
- Search results from re-run queries are identical
- Privacy: History is stored locally, never transmitted

**Technical Implementation:**
- New database table: `SearchHistory`
  - `history_id` (INTEGER PRIMARY KEY)
  - `query_text` (TEXT)
  - `search_scope` (TEXT)
  - `search_options` (JSON)
  - `result_count` (INTEGER)
  - `timestamp` (DATETIME)
- New database table: `SavedQueries`
  - `saved_id` (INTEGER PRIMARY KEY)
  - `name` (TEXT UNIQUE)
  - `query_text` (TEXT)
  - `search_scope` (TEXT)
  - `search_options` (JSON)
  - `tags` (TEXT)
  - `created_at` (DATETIME)
  - `last_run` (DATETIME)
- New CLI commands: `history`, `saved`
- JSON export/import functionality

**Dependencies:**
- Existing database infrastructure
- JSON library for options storage
- Click command group for history/saved

---

#### FR-1.4: JSON Output Mode
**Priority:** High | **Complexity:** Low | **Effort:** 2-3 days

**Description:**
Add machine-readable JSON output format for all search and list commands to enable integration with data pipelines and analysis tools.

**User Stories:**
- As a Researcher, I want to export search results as JSON for statistical analysis
- As a Truth Seeker, I want to process search results programmatically for automated fact-checking
- As a Learner, I want to build custom tools on top of yt-fts search results

**Functional Requirements:**
1. `--json` flag for all output-generating commands:
   - `search`
   - `vsearch`
   - `list`
   - `history`
2. Structured JSON schema for each command type
3. Consistent field naming and data types
4. Include all metadata (timestamps, channel info, video URLs)
5. Proper escaping of special characters
6. Pretty-print option with `--json-indent`
7. Streaming output for large result sets
8. Error output to stderr, valid JSON to stdout

**Acceptance Criteria:**
- Command: `yt-fts search "machine learning" --json --limit 5`
- Returns valid, parseable JSON
- JSON schema is documented and versioned
- All commands with `--json` output to stdout only
- Exit codes remain consistent with non-JSON mode
- JSON validates against schema

**JSON Schema Example:**
```json
{
  "version": "1.0",
  "command": "search",
  "query": "machine learning",
  "scope": "all",
  "timestamp": "2025-12-24T10:30:00Z",
  "total_results": 42,
  "results": [
    {
      "rank": 1,
      "video_id": "abc123",
      "video_title": "Introduction to Machine Learning",
      "channel_name": "3Blue1Brown",
      "channel_id": "UCYO0Ujrxrr3e4dEY3I6F3g",
      "timestamp": "00:05:23",
      "timestamp_seconds": 323,
      "text": "Machine learning is about...",
      "url": "https://youtu.be/abc123?t=323",
      "match_type": "fts"
    }
  ]
}
```

**Technical Implementation:**
- Add `--json` and `--json-indent` options to relevant commands
- Create JSON serializer classes for each result type
- Suppress Rich console output when `--json` is enabled
- Add JSON schema validation tests
- Update documentation with JSON schemas

**Dependencies:**
- Python `json` module (built-in)
- Existing result formatting infrastructure

---

### Sprint 2 - Knowledge Management

#### FR-2.1: Obsidian/Roam Research Markdown Export
**Priority:** High | **Complexity:** Medium | **Effort:** 5-7 days

**Description:**
Export search results, transcripts, or video metadata as markdown files compatible with Obsidian and Roam Research PKM systems.

**User Stories:**
- As a Truth Seeker, I want to export findings to my Obsidian knowledge base with proper linking
- As a Researcher, I want to create literature reviews from video content in Roam Research
- As a Learner, I want to build a personal knowledge graph from educational videos

**Functional Requirements:**
1. `--export-obsidian` option for search commands
2. `--export-roam` option for Roam Research format
3. YAML frontmatter with comprehensive metadata:
   - Title
   - Channel name and URL
   - Video ID and URL
   - Publication date
   - Tags (auto-generated and user-specified)
   - Timestamps
4. Wiki-style links for video references
   - `[[Video Title]]` syntax
   - Block references for specific quotes `[^1]`
5. Backlink support for bidirectional linking
6. Embed syntax for timestamped video clips
7. Batch export for multiple videos
8. Customizable templates
9. Tag auto-generation from content
10. Hierarchical note structure for long videos

**Acceptance Criteria:**
- Command: `yt-fts search "AI safety" --export-obsidian --output-dir "./vault"`
- Creates markdown file with YAML frontmatter
- Wiki links work in Obsidian preview
- Backlinks are discoverable in Obsidian graph view
- Tags are properly formatted
- Metadata is complete and accurate

**Markdown Format Example:**
```markdown
---
title: "Machine Learning Fundamentals"
channel: "3Blue1Brown"
channel_url: "https://www.youtube.com/@3blue1brown"
video_id: "Ilg3gGewQ5U"
video_url: "https://www.youtube.com/watch?v=Ilg3gGewQ5U"
publish_date: "2023-08-10"
tags:
  - machine-learning
  - mathematics
  - tutorial
created: "2025-12-24T10:30:00Z"
yt_fts_export_version: "1.0"
---

# Machine Learning Fundamentals

## Key Concepts

### Neural Networks
> Neural networks are essentially function approximators [[Machine Learning#neural-networks]]

- [Timestamp: 00:05:23](https://youtu.be/Ilg3gGewQ5U?t=323)
- Related: [[Gradient Descent]], [[Backpropagation]]

### Backpropagation
> The key insight is that we can work backwards from the error

- [Timestamp: 00:12:45](https://youtu.be/Ilg3gGewQ5U?t=765)

## Tags
#machine-learning #mathematics #education
```

**Technical Implementation:**
- Create `ExportFormatter` class for markdown generation
- Add template system using Jinja2
- Implement YAML frontmatter generation
- Add wiki link syntax conversion
- Create export directory structure management
- Add Obsidian-specific metadata fields

**Dependencies:**
- `pyyaml` for YAML frontmatter generation
- `jinja2` for template rendering (optional, or use f-strings)
- Existing export infrastructure

---

#### FR-2.2: Citation Export (BibTeX, APA, MLA Formats)
**Priority:** High | **Complexity:** Medium | **Effort:** 4-6 days

**Description:**
Export video citations in standard academic formats compatible with citation managers (Zotero, EndNote, Mendeley).

**User Stories:**
- As a Researcher, I want to export BibTeX citations for LaTeX papers
- As a Truth Seeker, I want to include properly formatted citations in investigative reports
- As a Learner, I want to cite educational videos in academic work

**Functional Requirements:**
1. `--export-citation` option with format specification
2. Support for multiple citation formats:
   - BibTeX
   - APA 7th edition
   - MLA 9th edition
   - Chicago (optional)
3. Batch export for multiple videos
4. Automatic metadata extraction:
   - Author (channel name)
   - Publication date
   - Title
   - URL
   - Access date
5. `@online` entry type for BibTeX
6. Customizable citation templates
7. Export to `.bib` file for BibTeX
8. Export to `.txt` for text-based formats
9. In-text citation generation option

**Acceptance Criteria:**
- Command: `yt-fts search "quantum computing" --export-citation bibtex --output citations.bib`
- Generates valid BibTeX file
- Citations include all required fields
- Format matches style guide specifications
- Multiple entries in one file
- Special characters properly escaped

**Citation Format Examples:**

**BibTeX:**
```bibtex
@online{3blue1brown2023neural,
  author = {3Blue1Brown},
  title = {Neural Networks},
  year = {2023},
  month = {8},
  day = {10},
  url = {https://www.youtube.com/watch?v=aircAruvnKk},
  urldate = {2025-12-24},
  organization = {YouTube}
}
```

**APA 7th Edition:**
```text
3Blue1Brown. (2023, August 10). *Neural networks* [Video]. YouTube. https://www.youtube.com/watch?v=aircAruvnKk
```

**MLA 9th Edition:**
```text
3Blue1Brown. "Neural Networks." *YouTube*, 10 Aug. 2023, www.youtube.com/watch?v=aircAruvnKk. Accessed 24 Dec. 2025.
```

**Technical Implementation:**
- Create `CitationFormatter` class with format-specific methods
- Add citation style templates
- Implement metadata extraction from database
- Add `--export-citation` CLI option
- Create citation export handler
- Add validation for citation format compliance

**Dependencies:**
- Existing video metadata in database
- String formatting libraries
- Optional: `pybtex` for advanced BibTeX management

---

#### FR-2.3: Notion/Zotero Integration
**Priority:** Medium | **Complexity:** High | **Effort:** 7-10 days

**Description:**
Direct integration with Notion workspace and Zotero citation manager for seamless knowledge management workflows.

**User Stories:**
- As a Researcher, I want to export search results directly to my Notion research database
- As a Truth Seeker, I want to add videos to my Zotero library with automatic metadata
- As a Learner, I want to build a study system using Notion + yt-fts

**Functional Requirements:**

**Notion Integration:**
1. `--export-notion` option for search commands
2. OAuth2 authentication with Notion API
3. Database selection for exports
4. Create new pages with:
   - Video title as page title
   - Embeds for video content
   - Transcript as page content
   - Properties for metadata (tags, dates, channel)
5. Update existing pages (optional)
6. Block-level appending for ongoing research
7. Rich text formatting for quotes and timestamps

**Zotero Integration:**
1. `--export-zotero` option for search commands
2. Zotero API integration
3. Create new items with:
   - Video metadata
   - Attach transcript PDF
   - Add tags and notes
   - Collection assignment
4. Bulk import support
5. Duplicate detection
6. Automatic PDF generation from transcripts

**Acceptance Criteria:**
- Commands:
  - `yt-fts search "AI safety" --export-notion --database-id "xxx"`
  - `yt-fts search "machine learning" --export-zotero --collection "ML Research"`
- Authenticates with OAuth2 securely
- Creates properly formatted Notion pages
- Adds items to Zotero with correct metadata
- Handles API rate limits gracefully
- Provides clear error messages for authentication failures

**Notion Page Structure:**
```json
{
  "parent": {"database_id": "xxx"},
  "properties": {
    "Title": {"title": [{"text": {"content": "Video Title"}}]},
    "Channel": {"rich_text": [{"text": {"content": "3Blue1Brown"}}]},
    "Published": {"date": {"start": "2023-08-10"}},
    "Tags": {"multi_select": [{"name": "ML"}, {"name": "Tutorial"}]}
  },
  "children": [
    {
      "object": "block",
      "type": "video",
      "video": {"external": {"url": "https://www.youtube.com/watch?v=xxx"}}
    }
  ]
}
```

**Technical Implementation:**
- API clients for Notion and Zotero
- OAuth2 authentication flow
- Configuration file for API keys
- Retry logic with exponential backoff
- Rate limit handling
- Error recovery mechanisms

**Dependencies:**
- `notion-client` Python library (optional, or use requests)
- `pyzotero` library for Zotero integration
- OAuth2 libraries (`requests-oauthlib`)
- User-provided API tokens
- Optional dependencies with feature flags

---

### Sprint 3 - Learning Features

#### FR-3.1: Flashcard Generation (Anki Export Format)
**Priority:** Medium | **Complexity:** Medium | **Effort:** 5-7 days

**Description:**
Generate flashcards from video content in Anki-compatible format for spaced repetition learning.

**User Stories:**
- As a Learner, I want to create flashcards from lecture videos for exam preparation
- As a Researcher, I want to memorize key concepts from tutorial videos
- As an Autodidact, I want to build a spaced repetition system from educational content

**Functional Requirements:**
1. `yt-fts flashcards generate` command
2. LLM-based question generation from transcript segments
3. Multiple card types:
   - Basic (Front/Back)
   - Cloze deletion
   - Image-based (optional)
4. Timestamped source links on every card
5. Tag system for deck organization
6. Export to `.apkg` (Anki package) format
7. Support for LaTeX in cards (math notation)
8. Batch generation from entire videos or search results
9. Card preview before export
10. Configurable generation parameters:
    - Cards per video
    - Difficulty level
    - Question types

**Acceptance Criteria:**
- Command: `yt-fts flashcards generate --channel "3Blue1Brown" --output "ML.apkg"`
- Generates valid Anki package file
- Imports successfully into Anki desktop
- Cards are accurate and meaningful
- Source links are correct and clickable
- Tags organize cards logically
- Supports mathematical notation with LaTeX

**Card Format Examples:**

**Basic Card:**
```
Front: What is the key insight of backpropagation?
Back: We can work backwards from the error to calculate gradients
Source: https://youtu.be/xxx?t=345
Tags: #machine-learning #neural-networks
```

**Cloze Card:**
```
Text: The key insight of {{c1::backpropagation}} is that we can {{c2::work backwards}} from the {{c3::error}} to calculate {{c4::gradients}}
Source: https://youtu.be/xxx?t=345
Tags: #machine-learning
```

**Technical Implementation:**
- LLM integration for question generation
- Anki package generation (`.apkg` format using `genanki` library)
- Transcript segmentation for card content
- Tag generation from content
- LaTeX rendering support
- Export command with options

**Dependencies:**
- `genanki` library for Anki package generation
- LLM API (OpenAI/Gemini) for question generation
- Existing transcript data
- Optional dependency with feature flag

---

#### FR-3.2: Chapter/Segment Detection using LLM
**Priority:** High | **Complexity:** High | **Effort:** 7-10 days

**Description:**
Automatically detect and label topic transitions in videos to create navigable chapter markers.

**User Stories:**
- As a Learner, I want to jump directly to relevant sections without watching entire videos
- As a Researcher, I want to quickly find specific topics within long lectures
- As a Truth Seeker, I want to navigate to key moments in documentary-style content

**Functional Requirements:**
1. `yt-fts chapters detect` command
2. LLM-based topic segmentation:
   - Analyze transcript for topic changes
   - Identify introduction/conclusion
   - Detect demonstrations/examples
3. Chapter metadata:
   - Title
   - Start timestamp
   - End timestamp
   - Summary
   - Key topics
4. Export options:
   - YouTube chapters format
   - Markdown table of contents
   - JSON metadata
   - VTT chapters format
5. Visual chapter display in CLI
6. Integration with `list --transcript` command
7. Confidence scoring for chapter boundaries
8. Configurable sensitivity for topic detection
9. Manual chapter editing capabilities
10. Batch processing for multiple videos

**Acceptance Criteria:**
- Command: `yt-fts chapters detect --video-id "xxx" --export-format youtube`
- Identifies 5-15 chapters per typical 20-minute video
- Chapter titles accurately reflect content
- Timestamps are precise (within 5-10 seconds)
- Chapters follow logical narrative flow
- Export formats are valid
- Processing time < 30 seconds per video

**Chapter Detection Algorithm:**
1. Split transcript into overlapping windows
2. Generate embeddings for each window
3. Calculate semantic similarity between consecutive windows
4. Identify significant drops in similarity (topic boundaries)
5. Use LLM to generate chapter titles from boundary context
6. Refine boundaries using pause detection in audio

**Technical Implementation:**
- LLM API integration for segmentation
- Embedding-based similarity calculation
- Sliding window algorithm
- Chapter title generation using LLM
- Multi-format export handlers
- Caching of chapter data

**Dependencies:**
- LLM API (OpenAI/Gemini) for analysis
- Embedding generation (existing infrastructure)
- NLP libraries for preprocessing
- Significant computational cost (LLM tokens)

---

#### FR-3.3: Multi-Language Subtitle Support
**Priority:** Medium | **Complexity:** Medium | **Effort:** 5-7 days

**Description:**
Support for downloading, searching, and exporting subtitles in multiple languages.

**User Stories:**
- As a Learner, I want to download subtitles in my native language
- As a Researcher, I want to search for concepts mentioned in different languages
- As a Truth Seeker, I want to compare translations for accuracy

**Functional Requirements:**
1. Language detection and selection during download:
   - List available subtitle languages
   - Download multiple languages per video
   - Auto-detect video language
2. Multi-language search:
   - Search in specific language
   - Cross-language semantic search
   - Display original and translated text
3. Language metadata in database:
   - Add `language_code` column to Subtitles table
   - Update FTS indexes for multi-language content
4. Export functionality:
   - Export specific language
   - Export parallel translations
   - Side-by-side transcript view
5. Language code support (ISO 639-1):
   - en (English)
   - es (Spanish)
   - fr (French)
   - de (German)
   - zh (Chinese)
   - ja (Japanese)
   - etc.
6. Fallback options when preferred language unavailable

**Acceptance Criteria:**
- Commands:
  - `yt-fts download --language es "https://youtube.com/watch?v=xxx"`
  - `yt-fts search "aprendizaje automático" --language es`
  - `yt-fts list --transcript "xxx" --language es`
- Downloads correct language subtitles
- Search returns results in specified language
- Database schema supports multiple languages
- Auto-fallback to English if unavailable

**Database Schema Changes:**
```sql
ALTER TABLE Subtitles ADD COLUMN language_code TEXT DEFAULT 'en';
CREATE INDEX idx_subtitles_language ON Subtitles(language_code);
CREATE VIRTUAL TABLE Subtitles_fts_es USING fts5(text, content=Subtitles, content_rowid=rowid);
-- Similar for other languages
```

**Technical Implementation:**
- Modify download handler to request specific language
- Update database schema with language codes
- Create language-specific FTS indexes
- Add language filtering to search queries
- Update export functionality
- Language detection fallback logic

**Dependencies:**
- yt-dlp language support
- Existing subtitle infrastructure
- Database schema migration
- FTS5 multi-language support

---

#### FR-3.4: Translation Layer for Cross-Language Research
**Priority:** Low | **Complexity:** High | **Effort:** 7-10 days

**Description:**
Enable search and retrieval of content across language barriers using translation APIs.

**User Stories:**
- As a Researcher, I want to find relevant content in languages I don't speak
- As a Truth Seeker, I want to verify translations for accuracy
- As a Learner, I want to access educational content regardless of language

**Functional Requirements:**
1. Cross-language search:
   - Query in one language, find results in another
   - Auto-translate search terms
   - Display original text with translation
2. Translation options:
   - Machine translation (Google Translate, DeepL)
   - Local translation models (optional)
3. Bilingual display mode:
   - Side-by-side original and translation
   - Toggle between languages
4. Citation with translation notes
5. Translation caching to minimize API calls
6. Quality indicators for machine translations
7. Export with translated content
8. Configurable source and target languages

**Acceptance Criteria:**
- Commands:
  - `yt-fts search "climate change" --translate-to es`
  - `yt-fts search "cambio climático" --translate-from es --translate-to en`
- Finds content regardless of source language
- Translations are reasonably accurate
- Original text is always preserved
- API costs are controlled through caching
- Performance impact is acceptable (< 2s additional latency)

**Technical Implementation:**
- Translation API integration (Google/DeepL)
- Query translation before search
- Result translation after retrieval
- Translation cache database table
- Cost tracking for API usage
- Fallback to original if translation fails

**Database Schema Additions:**
```sql
CREATE TABLE TranslationCache (
    cache_id INTEGER PRIMARY KEY,
    original_text TEXT NOT NULL,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    translation_service TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_translation_cache ON TranslationCache(original_text, source_language, target_language);
```

**Dependencies:**
- Translation API (Google Cloud Translation, DeepL API)
- API key management
- Existing search infrastructure
- Optional dependency with feature flag

---

### Sprint 4 - Automation & Infrastructure

#### FR-4.1: Watch Mode / Auto-Update for New Uploads
**Priority:** Medium | **Complexity:** High | **Effort:** 7-10 days

**Description:**
Background daemon that monitors channels for new uploads and automatically downloads and indexes them.

**User Stories:**
- As a Researcher, I want my library to stay current without manual updates
- As a Truth Seeker, I want to be notified when channels I follow upload new content
- As a Learner, I want to automatically download new lectures from educational channels

**Functional Requirements:**
1. `yt-fts watch start` command to launch background daemon
2. `yt-fts watch stop` to stop daemon
3. `yt-fts watch status` to check daemon status
4. Configurable check intervals (default: 1 hour)
5. Per-channel watch lists:
   - Add/remove channels from watch list
   - Set different check intervals per channel
6. Notifications for new content:
   - Desktop notifications
   - Email notifications (optional)
   - Webhook notifications (optional)
7. Automatic download and indexing
8. Automatic embeddings generation for new content
9. Conflict resolution for duplicate videos
10. Logging and monitoring:
    - Download history
    - Error tracking
    - Status dashboard
11. Resource limits:
    - Bandwidth throttling
    - CPU usage limits
    - Disk space checks

**Acceptance Criteria:**
- Commands:
  - `yt-fts watch add --channel "3Blue1Brown" --interval "1h"`
  - `yt-fts watch start`
  - `yt-fts watch status`
- Daemon runs in background without blocking CLI
- Automatically downloads new uploads
- Sends notifications for new content
- Survives system reboots (optional)
- Graceful shutdown on signal
- Logs all activities

**Technical Implementation:**
- Background process using Python `multiprocessing` or `daemon` library
- PID file management
- SQLite database for watch state
- YouTube API for new video detection
- Existing download/update infrastructure
- Notification integrations (desktop, email, webhook)
- Configuration file for watch settings

**Daemon Architecture:**
```
WatchDaemon (Main Process)
├── ChannelMonitor (per channel)
│   ├── YouTubeAPI.check_new_videos()
│   ├── DownloadHandler.download()
│   └── EmbeddingsHandler.generate()
├── NotificationService
│   ├── DesktopNotification
│   ├── EmailNotification (optional)
│   └── WebhookNotification (optional)
└── StateManager
    ├── WatchState (database)
    ├── PID management
    └── Logging
```

**Dependencies:**
- `python-daemon` or `multiprocessing` for background execution
- `schedule` library for periodic tasks
- Existing download/update infrastructure
- Notification libraries (`plyer` for desktop notifications)
- Optional dependencies (email, webhook)

---

#### FR-4.2: API Server Mode (FastAPI)
**Priority:** Low | **Complexity:** High | **Effort:** 10-14 days

**Description:**
RESTful API server for programmatic access to yt-fts functionality.

**User Stories:**
- As a Researcher, I want to build custom analysis tools on top of yt-fts data
- As a Developer, I want to integrate yt-fts search into web applications
- As a Data Scientist, I want to query the database for research projects

**Functional Requirements:**
1. `yt-fts server start` command to launch API server
2. RESTful API endpoints:
   - `/channels` - List and manage channels
   - `/videos` - Browse video metadata
   - `/search` - Full-text search
   - `/vsearch` - Semantic search
   - `/export` - Export data
   - `/status` - Server health check
3. Authentication:
   - API key authentication
   - OAuth2 (optional)
   - Rate limiting per API key
4. Request/response formats:
   - JSON for all endpoints
   - OpenAPI/Swagger documentation
5. Streaming support for large result sets
6. CORS configuration for web integration
7. Webhook support for async operations
8. Configuration file for server settings
9. Production-ready features:
   - Process management (systemd/supervisord)
   - Logging
   - Graceful shutdown
10. SDK/client libraries (optional)

**API Endpoints Specification:**

```
GET  /api/v1/channels
POST /api/v1/channels
GET  /api/v1/channels/{channel_id}
DELETE /api/v1/channels/{channel_id}

GET  /api/v1/channels/{channel_id}/videos
GET  /api/v1/videos/{video_id}
GET  /api/v1/videos/{video_id}/transcript

GET  /api/v1/search
GET  /api/v1/vsearch

GET  /api/v1/export/transcript
GET  /api/v1/export/citation

GET  /api/v1/status
GET  /api/v1/health
```

**Acceptance Criteria:**
- Commands:
  - `yt-fts server start --port 8080`
  - `yt-fts server stop`
- Server responds to all defined endpoints
- OpenAPI documentation is accessible at `/docs`
- Authentication works correctly
- Rate limiting prevents abuse
- Server handles concurrent requests
- Shutdown is graceful

**Technical Implementation:**
- FastAPI framework
- Pydantic models for request/response validation
- OpenAPI/Swagger automatic documentation
- API key middleware
- Rate limiting middleware
- CORS middleware
- Process management for daemon operation
- Existing yt-fts core functionality as backend

**Dependencies:**
- `fastapi` library
- `uvicorn` ASGI server
- `pydantic` for data validation
- `python-multipart` for file uploads
- Existing yt-fts infrastructure
- Optional dependencies (OAuth2, additional auth)

---

## 3. Non-Functional Requirements

### 3.1 Performance Requirements

#### NFR-3.1.1: Search Performance
- Full-text search must return results in < 500ms for typical queries
- Semantic search must return results in < 2 seconds (network dependent)
- Time-based filtering must add < 100ms overhead
- Proximity search must maintain performance comparable to regular FTS
- JSON export must not exceed search time by > 20%

#### NFR-3.1.2: Database Performance
- Database queries must use appropriate indexes
- FTS indexes must be maintained automatically
- Large channel libraries (1000+ channels, 100K+ videos) must remain responsive
- Batch operations must use transactions for efficiency

#### NFR-3.1.3: API Performance (Server Mode)
- API response time must be < 1 second for most endpoints
- Support for at least 100 concurrent requests
- Rate limiting: 100 requests/minute per API key
- Efficient connection pooling

### 3.2 Reliability Requirements

#### NFR-3.2.1: Error Handling
- All commands must have graceful error handling
- Network failures must not corrupt database
- Partial failures in batch operations must be reported clearly
- User-friendly error messages with actionable suggestions

#### NFR-3.2.2: Data Integrity
- ACID compliance for database transactions
- No data loss during interrupts (Ctrl+C)
- Automatic rollback on failed operations
- Validation for all user inputs

#### NFR-3.2.3: Fault Tolerance
- Watch mode daemon must auto-restart on crashes
- API server must handle client disconnects gracefully
- Retry logic with exponential backoff for network operations
- Degraded mode operation when optional features fail

### 3.3 Maintainability Requirements

#### NFR-3.3.1: Code Quality
- Follow existing code style (Ruff, Black formatting)
- Type hints for all new functions (mypy compliance)
- Comprehensive docstrings for public APIs
- Code reviews for all changes

#### NFR-3.3.2: Testing
- Unit tests for all new functionality (80%+ coverage)
- Integration tests for multi-component features
- End-to-end tests for critical user workflows
- Performance regression tests

#### NFR-3.3.3: Documentation
- User documentation for all new commands
- API documentation (OpenAPI/Swagger)
- Developer documentation for architecture
- Changelog entries for all changes

### 3.4 Usability Requirements

#### NFR-3.4.1: CLI Design
- Consistent command structure with existing CLI
- Helpful error messages with examples
- Progress indicators for long operations
- Auto-completion support (optional)
- Colored output for better readability (Rich)

#### NFR-3.4.2: Learning Curve
- Intuitive command names and options
- In-app help and examples
- Tutorial mode for first-time users
- Sensible defaults

#### NFR-3.4.3: Accessibility
- Clear contrast in terminal output
- Configurable verbosity levels
- Options for screen reader friendly output
- Internationalization support (future)

---

## 4. Constitutional Compliance Requirements

### 4.1 User Autonomy (Constitutional Principle)

**Requirement:** All features must respect user autonomy and choice.

**Implementation:**
- **Opt-in Design:** No feature runs without explicit user initiation
- **Clear Consent:** API integrations (Notion, Zotero, translation) require explicit opt-in
- **Data Control:** Users retain full control over their data:
  - Export any data at any time
  - Delete any data at any time
  - No vendor lock-in
- **Transparency:** All operations are logged and visible to users
- **No Hidden Behavior:** No background telemetry or data collection without consent

**Validation:**
- Privacy impact assessment for each feature
- User consent dialogs for API integrations
- Clear documentation of data flows
- Audit logging for all automated operations

---

### 4.2 Privacy Protection (Constitutional Principle)

**Requirement:** User data remains private and secure on their local system.

**Implementation:**
- **Local-First Architecture:** All data stored locally by default
- **No Cloud Dependencies:** Core functionality works without internet
- **API Key Security:**
  - API keys stored in user config directory
  - File permissions restricted to user (600)
  - Never logged or transmitted except to intended API
- **Optional Cloud Features:** All cloud features require explicit configuration:
  - Notion integration (opt-in)
  - Zotero integration (opt-in)
  - Translation APIs (opt-in)
  - LLM features (opt-in)
- **No Telemetry:** No usage tracking or analytics by default

**Data Protection:**
```python
# Example: Secure API key handling
def get_api_key(service: str) -> str | None:
    """Load API key from secure local storage only."""
    key_file = Path.home() / ".config" / "yt-fts" / f"{service}_key.txt"
    if key_file.exists():
        # Set restrictive permissions (user read/write only)
        key_file.chmod(0o600)
        return key_file.read_text().strip()
    return None
```

**Validation:**
- Security audit for all external API integrations
- Data flow diagrams showing no data leaves without consent
- Encryption in transit for all API communications (HTTPS)
- No hardcoded credentials

---

### 4.3 Transparent Operations (Constitutional Principle)

**Requirement:** All operations are transparent and explainable to users.

**Implementation:**
- **Verbose Logging:** Detailed logging available for troubleshooting
- **Operation Visibility:** Progress indicators show what's happening
- **Clear Documentation:** Every feature is documented with:
  - What it does
  - What data it accesses
  - What external calls it makes (if any)
  - How to disable it
- **Error Transparency:** Errors explain:
  - What went wrong
  - Why it went wrong
  - How to fix it
- **Source Visibility:** Open-source code allows inspection

**Example Error Message:**
```
❌ Error: Unable to connect to Notion API

What happened: The API request to https://api.notion.com failed
Why: This could be due to network issues or invalid API credentials
How to fix:
  1. Check your internet connection
  2. Verify your Notion API token: yt-fts config --check-notion-token
  3. Run with --verbose for more details

Learn more: https://github.com/NotJoeMartinez/yt-fts/docs/notion-integration
```

**Validation:**
- User testing for error message clarity
- Documentation completeness checks
- Code review for transparency issues

---

### 4.4 Optional Dependencies (Constitutional Principle)

**Requirement:** 100% support for feature flags and graceful degradation.

**Implementation:**
- **Feature Flags:** All optional dependencies are feature-flagged:
  ```python
  try:
      import notion_client
      HAS_NOTION = True
  except ImportError:
      HAS_NOTION = False
  ```
- **Graceful Degradation:** Missing dependencies don't break core features
  ```python
  if HAS_NOTION:
      # Notion export functionality
  else:
      console.print("[yellow]Notion integration requires 'notion-client' package[/yellow]")
      console.print("[dim]Install: pip install notion-client[/dim]")
  ```
- **Clear Installation Instructions:** Users know exactly what to install for which features
- **Dependency Groups:** Separate dependency groups in `pyproject.toml`:
  ```toml
  [project.optional-dependencies]
  notion = ["notion-client>=2.0.0"]
  zotero = ["pyzotero>=1.5.0"]
  translation = ["google-cloud-translate>=3.0.0"]
  all = ["yt-fts[notion,zotero,translation]"]
  ```

**Installation Examples:**
```bash
# Core installation only
pip install yt-fts

# With Notion integration
pip install yt-fts[notion]

# With all optional features
pip install yt-fts[all]
```

**Validation:**
- Test with only core dependencies installed
- Test with each optional dependency individually
- Test all combinations of optional dependencies
- Error messages guide users to install missing dependencies

---

## 5. Technical Constraints & Dependencies

### 5.1 Existing Architecture Constraints

#### TC-5.1.1: Database Constraints
- **Database:** SQLite (must remain)
- **FTS Engine:** SQLite FTS5 (must remain)
- **Schema:** Existing tables must not break (Channels, Videos, Subtitles)
- **Migrations:** Must support backward-compatible migrations
- **Concurrency:** SQLite write locking limits concurrent writes

#### TC-5.1.2: CLI Framework Constraints
- **Framework:** Click (must remain)
- **Output:** Rich terminal formatting (must maintain)
- **Python Version:** >= 3.10 (must support)
- **Entry Points:** Existing CLI commands must not break

#### TC-5.1.3: External Service Constraints
- **YouTube:** yt-dlp for downloads (must use)
- **LLM APIs:** OpenAI or Gemini (existing support)
- **Browser Cookies:** Existing cookie extraction (must maintain)

---

### 5.2 New Dependencies by Feature

#### Sprint 1 Dependencies
| Feature | Dependency | Version | Optional | License |
|---------|-----------|---------|----------|---------|
| Time filters | python-dateutil | >= 2.8.0 | Yes | Python |
| Proximity search | (None - uses SQLite FTS5) | - | - | - |
| Search history | (None - uses existing SQLite) | - | - | - |
| JSON output | (None - uses stdlib json) | - | - | - |

#### Sprint 2 Dependencies
| Feature | Dependency | Version | Optional | License | Purpose |
|---------|-----------|---------|----------|---------|---------|
| Obsidian export | pyyaml | >= 6.0 | Yes | MIT | YAML frontmatter |
| Citation export | (None - string templates) | - | - | - | - |
| Notion integration | notion-client | >= 2.0.0 | Yes | MIT | Notion API |
| Zotero integration | pyzotero | >= 1.5.0 | Yes | GPL-3.0 | Zotero API |

#### Sprint 3 Dependencies
| Feature | Dependency | Version | Optional | License | Purpose |
|---------|-----------|---------|----------|---------|---------|
| Flashcards | genanki | >= 0.13.0 | Yes | MIT | Anki package generation |
| Chapter detection | (Existing LLM APIs) | - | Yes | - | Topic segmentation |
| Multi-language | (None - uses yt-dlp) | - | - | - | - |
| Translation | google-cloud-translate | >= 3.0.0 | Yes | Apache-2.0 | Translation API |

#### Sprint 4 Dependencies
| Feature | Dependency | Version | Optional | License | Purpose |
|---------|-----------|---------|----------|---------|---------|
| Watch mode | python-daemon | >= 3.0.0 | Yes | Apache-2.0 | Background daemon |
| Watch mode | schedule | >= 1.2.0 | Yes | MIT | Task scheduling |
| API server | fastapi | >= 0.100.0 | Yes | MIT | REST API framework |
| API server | uvicorn | >= 0.23.0 | Yes | BSD | ASGI server |
| API server | pydantic | >= 2.0.0 | Yes | MIT | Data validation |

---

### 5.3 Technology Stack Constraints

#### TC-5.3.1: Python Version
- **Minimum:** Python 3.10
- **Target:** Python 3.10, 3.11, 3.12
- **Testing:** Must test on all supported versions
- **Deprecations:** No use of deprecated Python features

#### TC-5.3.2: Platform Support
- **Primary:** Linux, macOS, Windows
- **Testing:** Must test on all three platforms
- **Path Handling:** Use `pathlib` for cross-platform compatibility
- **Permissions:** Handle Windows permission issues

#### TC-5.3.3: Performance Constraints
- **Memory:** Must not exceed 2GB for typical operations
- **Disk:** Database must not exceed 10GB per 1000 channels (typical)
- **Network:** Graceful handling of network failures
- **Concurrency:** SQLite write limits must be respected

---

### 5.4 API Constraints

#### TC-5.4.1: External APIs
All external API integrations must:
- Be optional with feature flags
- Have timeout configurations
- Implement retry logic with exponential backoff
- Rate limit handling
- Clear error messages
- No hardcoded credentials

**Example: API Client Interface**
```python
class APIClient(abc.ABC):
    """Base class for all external API clients."""

    @abc.abstractmethod
    def connect(self) -> bool:
        """Establish connection to API."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if API is accessible."""
        pass

    @property
    @abc.abstractmethod
    def optional_dependency(self) -> str:
        """Name of optional dependency package."""
        pass
```

#### TC-5.4.2: API Key Management
- API keys must be stored in user config directory only
- File permissions must be restrictive (user read/write only)
- Keys must never be logged or included in error messages
- Support for environment variables (for server mode)

---

## 6. User Interface Requirements

### 6.1 Command-Line Interface Requirements

#### UIR-6.1.1: Consistent Command Structure
All new commands must follow existing patterns:
```bash
yt-fts <command> [arguments] [options]
```

**Examples:**
```bash
# Sprint 1
yt-fts search "query" --after "2024-01-01"
yt-fts history list --limit 20
yt-fts saved run "my-search"

# Sprint 2
yt-fts export --channel "Name" --format obsidian
yt-fts export-citation bibtex --output refs.bib

# Sprint 3
yt-fts flashcards generate --channel "Name"
yt-fts chapters detect --video-id "xxx"

# Sprint 4
yt-fts watch add --channel "Name"
yt-fts server start --port 8080
```

#### UIR-6.1.2: Option Naming Conventions
- **Short options:** Single dash, single letter (`-v`, `-j`)
- **Long options:** Double dash, words with hyphens (`--channel`, `--video-id`)
- **Boolean flags:** Use `is_flag=True` in Click
- **File outputs:** Use `--output` or `-o`
- **Format specifications:** Use `--format` or `-f`

#### UIR-6.1.3: Help Text Standards
All commands must have:
- **Command help:** Description of what the command does
- **Argument help:** Description of required arguments
- **Option help:** Description of each option with default values
- **Usage examples:** At least 2-3 examples per command
- **See also:** References to related commands

**Example:**
```python
@cli.command(
    name="flashcards",
    help="""
    Generate flashcards from video content for spaced repetition learning.

    Creates Anki-compatible flashcards with:
    - Question/answer pairs generated by LLM
    - Timestamped source links
    - Automatic tag generation
    - Multiple card types (basic, cloze)

    Examples:
    - yt-fts flashcards generate --channel "3Blue1Brown"
    - yt-fts flashcards generate --video-id "xxx" --count 50
    - yt-fts flashcards generate --search "neural networks" --output ml.apkg

    See also: search, vsearch, summarize
    """
)
```

#### UIR-6.1.4: Progress Indicators
Long-running operations must show progress:
- **Downloads:** Progress bar with video count
- **Searches:** "Searching..." message
- **Exports:** Progress bar with item count
- **LLM operations:** Progress with token count or step indicator

**Example:**
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("[cyan]Generating flashcards...", total=num_cards)
    for card in cards:
        generate_card(card)
        progress.advance(task)
```

#### UIR-6.1.5: Output Formatting
- **Success messages:** Green with checkmark
- **Warning messages:** Yellow with warning symbol
- **Error messages:** Red with X symbol
- **Info messages:** Blue or dimmed
- **Emojis:** Use sparingly, configuable with env variable

---

### 6.2 Configuration Requirements

#### UIR-6.2.1: Configuration File
Support for `.yt_fts_config` or `config.yaml` in user config directory:

```yaml
# Search settings
search:
  default_limit: 10
  history_retention_days: 90
  save_last_n_searches: 100

# Export settings
export:
  default_format: "txt"
  output_directory: "./exports"
  include_timestamps: true

# LLM settings
llm:
  api_key_env: "GEMINI_API_KEY"
  model: "gemini-pro"
  temperature: 0.7

# Watch mode
watch:
  check_interval_minutes: 60
  notifications_enabled: true

# API server
server:
  host: "127.0.0.1"
  port: 8080
  api_key_required: true
```

#### UIR-6.2.2: Environment Variables
All sensitive configuration via environment variables:
- `GEMINI_API_KEY` / `OPENAI_API_KEY` (existing)
- `NOTION_API_KEY` / `ZOTERO_API_KEY` (new)
- `GOOGLE_TRANSLATE_API_KEY` (new)
- `YT_FTS_CONFIG_PATH` (new - override config location)
- `YT_FTS_NO_EMOJI` (new - disable emoji output)
- `YT_FTS_LOG_LEVEL` (new - set logging verbosity)

---

### 6.3 Accessibility Requirements

#### UIR-6.3.1: Screen Reader Support
- Avoid emoji-only output (use text labels as well)
- Use high contrast colors in Rich output
- Provide plain-text mode with `--plain` flag
- Structured output for non-visual navigation

#### UIR-6.3.2: Color Blindness
- Don't rely on color alone to convey information
- Use symbols (✓, ✗, ⚠) in addition to colors
- Support different color themes (future)

---

## 7. Data Architecture Requirements

### 7.1 Database Schema Requirements

#### DAR-7.1.1: Search History Table
```sql
CREATE TABLE SearchHistory (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    search_scope TEXT NOT NULL,  -- 'all', 'channel', 'video'
    search_options TEXT,          -- JSON encoded options
    result_count INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_search_history_timestamp (timestamp),
    INDEX idx_search_history_scope (search_scope)
);
```

#### DAR-7.1.2: Saved Queries Table
```sql
CREATE TABLE SavedQueries (
    saved_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    search_scope TEXT NOT NULL,
    search_options TEXT,          -- JSON encoded options
    tags TEXT,                    -- Comma-separated tags
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_run DATETIME,
    run_count INTEGER DEFAULT 0,
    INDEX idx_saved_queries_tags (tags)
);
```

#### DAR-7.1.3: Chapters Table
```sql
CREATE TABLE Chapters (
    chapter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    title TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    summary TEXT,
    confidence REAL,              -- 0.0 to 1.0
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    generated_by TEXT,            -- 'llm', 'manual'
    FOREIGN KEY (video_id) REFERENCES Videos(video_id),
    INDEX idx_chapters_video (video_id),
    INDEX idx_chapters_time (start_time)
);
```

#### DAR-7.1.4: Watch List Table
```sql
CREATE TABLE WatchList (
    watch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    check_interval INTEGER DEFAULT 3600,  -- Seconds
    enabled BOOLEAN DEFAULT 1,
    last_check DATETIME,
    next_check DATETIME,
    last_video_id TEXT,            -- Most recent video seen
    FOREIGN KEY (channel_id) REFERENCES Channels(channel_id),
    UNIQUE (channel_id)
);
```

#### DAR-7.1.5: Subtitles Language Code Addition
```sql
ALTER TABLE Subtitles ADD COLUMN language_code TEXT DEFAULT 'en';
CREATE INDEX idx_subtitles_language ON Subtitles(language_code);
```

#### DAR-7.1.6: Translation Cache Table
```sql
CREATE TABLE TranslationCache (
    cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_text TEXT NOT NULL,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    translation_service TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (original_text, source_language, target_language)
);
```

---

### 7.2 Data Migration Requirements

#### DAR-7.2.1: Schema Versioning
- Maintain `schema_version` table
- Increment version on each schema change
- Provide migration scripts for each version

```sql
CREATE TABLE SchemaVersion (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO SchemaVersion (version, description) VALUES (1, 'Initial schema');
```

#### DAR-7.2.2: Backward Compatibility
- New columns must have default values
- Old commands must work with new schema
- Provide migration path for existing users

#### DAR-7.2.3: Migration Scripts
```python
def migrate_to_v2():
    """Add language_code column to Subtitles table."""
    db = Database(get_db_path())

    # Check if migration already applied
    if "language_code" in db["Subtitles"].columns_dict:
        return

    # Add column
    db.conn.execute("ALTER TABLE Subtitles ADD COLUMN language_code TEXT DEFAULT 'en'")
    db.conn.execute("CREATE INDEX IF NOT EXISTS idx_subtitles_language ON Subtitles(language_code)")

    # Update schema version
    db["SchemaVersion"].insert({"version": 2, "description": "Add multi-language support"})
```

---

### 7.3 Data Export Requirements

#### DAR-7.3.1: Export Formats
All export functions must support:
- **JSON:** Structured data with metadata
- **Markdown:** Human-readable with formatting
- **CSV:** Tabular data for spreadsheet analysis
- **Plain Text:** Raw transcript text

#### DAR-7.3.2: Export Metadata
All exports must include:
- Export timestamp
- Source (channel name, video ID)
- Data version/schema
- Export parameters used

#### DAR-7.3.3: Export Validation
- Validate export file format
- Check for data completeness
- Verify character encoding (UTF-8)
- Test import round-trip (when applicable)

---

## 8. Integration Points & APIs

### 8.1 External API Integrations

#### IPI-8.1.1: Notion API
**Purpose:** Export search results and transcripts to Notion workspace

**Endpoints:**
- `POST /pages` - Create new pages
- `PATCH /pages/{page_id}` - Update existing pages
- `POST /databases/{db_id}/query` - Query database

**Authentication:** OAuth2 or integration token

**Rate Limits:** 3 requests/second (free tier)

**Error Handling:**
- 429 Too Many Requests: Exponential backoff
- 401 Unauthorized: Clear error message, guide user to re-auth
- 404 Not Found: Validate database/parent IDs

**Data Mapping:**
```
Video Metadata → Notion Page Properties
- Title → title property
- Channel → rich_text property
- Date → date property
- Tags → multi_select property
Transcript → Page children (blocks)
Video URL → Video embed block
```

---

#### IPI-8.1.2: Zotero API
**Purpose:** Create citation items with transcript attachments

**Endpoints:**
- `POST /items/new` - Create new items
- `POST /items/{item_key}/file` - Upload attachments

**Authentication:** API key

**Rate Limits:** User-configurable (default: 10 requests/second)

**Error Handling:**
- 429 Too Many Requests: Back off and retry
- 403 Forbidden: Check API key permissions
- 409 Conflict: Item already exists (check before creating)

**Data Mapping:**
```
Video → Zotero Item (type: 'videoRecording')
- title → video title
- creators → [{creatorType: 'director', name: channel}]
- date → upload date
- url → video URL
Transcript → PDF attachment (auto-generated)
```

---

#### IPI-8.1.3: Translation APIs
**Options:**
1. Google Cloud Translation API
2. DeepL API

**Authentication:** API key

**Rate Limits:** Service-specific (usually quota-based)

**Cost Management:**
- Cache translations to minimize API calls
- Show cost estimates before large translations
- Support for free tiers when possible

---

### 8.2 Internal API Design

#### IPI-8.2.1: FastAPI Endpoints

**Base URL:** `http://localhost:8080/api/v1`

**Endpoints Specification:**

```yaml
# Channels
GET    /channels
       Query params: limit, offset
       Response: {channels: [...], total: n}

POST   /channels
       Body: {url: str, language: str}
       Response: {channel_id: str, status: str}

GET    /channels/{channel_id}
       Response: {channel: {...}}

DELETE /channels/{channel_id}
       Response: {message: str}

# Videos
GET    /channels/{channel_id}/videos
       Query params: limit, offset, after, before
       Response: {videos: [...], total: n}

GET    /videos/{video_id}
       Response: {video: {...}}

GET    /videos/{video_id}/transcript
       Query params: format (txt, vtt, json)
       Response: {transcript: str}

# Search
GET    /search
       Query params: q, channel_id, video_id, limit, after, before
       Response: {results: [...], total: n, query: str}

GET    /vsearch
       Query params: q, channel_id, limit
       Response: {results: [...], total: n, query: str}

# Export
GET    /export/transcript
       Query params: video_id, format
       Response: File download

GET    /export/citation
       Query params: video_id, format (bibtex, apa, mla)
       Response: {citation: str}

# System
GET    /status
       Response: {status: str, database: {...}}

GET    /health
       Response: {healthy: true}
```

---

### 8.3 Integration Testing Requirements

#### ITR-8.3.1: Mock APIs for Testing
- Mock Notion API responses
- Mock Zotero API responses
- Mock translation API responses
- Test error scenarios (timeouts, auth failures)

#### ITR-8.3.2: Integration Test Coverage
- Test each integration end-to-end
- Test authentication flows
- Test rate limiting behavior
- Test error recovery

---

## 9. Security & Privacy Requirements

### 9.1 API Key Security

#### SPR-9.1.1: Storage Requirements
- **Location:** User config directory only (`~/.config/yt-fts/` or `%APPDATA%\yt-fts\`)
- **Permissions:** 600 (user read/write only)
- **Format:** Plain text files with restrictive permissions
- **Encryption:** Optional GPG encryption for high-security scenarios

**Example:**
```python
def save_api_key(service: str, key: str) -> None:
    """Securely save API key to local storage."""
    config_dir = get_config_path()
    key_file = config_dir / f"{service}_api_key.txt"

    # Set restrictive permissions before writing
    key_file.touch(mode=0o600)

    # Write key
    key_file.write_text(key)

    # Verify permissions
    if key_file.stat().st_mode & 0o777 != 0o600:
        raise PermissionError(f"Failed to set restrictive permissions on {key_file}")
```

#### SPR-9.1.2: Runtime Protection
- **No Logging:** API keys never appear in logs
- **No Debug Output:** Sanitized in error messages
- **No Transmission:** Only sent to intended API endpoints
- **Memory Cleanup:** Clear from memory after use

---

### 9.2 Data Privacy

#### SPR-9.2.1: Local-First Design
- **Default Behavior:** All data stored locally
- **No Telemetry:** No usage tracking or analytics
- **No Cloud Sync:** No automatic cloud synchronization
- **User Control:** Users decide what to export/upload

#### SPR-9.2.2: Network Privacy
- **HTTPS Only:** All external API calls use HTTPS
- **DNS:** No DNS leaks (use system DNS)
- **Proxy Support:** Respect system proxy settings
- **No Tracking:** No tracking pixels or beacons

---

### 9.3 Third-Party API Privacy

#### SPR-9.3.1: Data Minimization
- Send only necessary data to external APIs
- Anonymize data when possible
- Remove PII before sending (when applicable)

**Example: Translation API**
```python
def translate_text(text: str, target_lang: str) -> str:
    """Translate text with privacy considerations."""

    # Remove potential PII before translation
    sanitized = sanitize_pii(text)

    # Call translation API
    translated = translation_api.translate(sanitized, target_lang)

    return translated

def sanitize_pii(text: str) -> str:
    """Remove or redact personally identifiable information."""
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '[EMAIL]', text)

    # Remove phone numbers
    text = re.sub(r'\d{3}-\d{3}-\d{4}', '[PHONE]', text)

    return text
```

#### SPR-9.3.2: Transparency
- Document what data is sent to which APIs
- Provide option to review before sending
- Log all external API calls (without sensitive data)

---

## 10. Performance Requirements

### 10.1 Search Performance

#### PR-10.1.1: Full-Text Search
- **Target:** < 500ms for 95th percentile queries
- **Index:** FTS5 indexes must be maintained
- **Query Optimization:** Use EXPLAIN QUERY PLAN for optimization
- **Caching:** Cache frequent queries (optional)

#### PR-10.1.2: Semantic Search
- **Target:** < 2 seconds for typical queries (network dependent)
- **Embeddings:** Pre-compute and cache embeddings
- **Batching:** Batch API calls for efficiency
- **Result Limiting:** Default limit of 10 results

#### PR-10.1.3: Time-Based Filtering
- **Overhead:** < 100ms additional latency
- **Indexing:** Use indexes on `video_date` column
- **Query Optimization:** Filter before FTS search

---

### 10.2 Database Performance

#### PR-10.2.1: Indexing Strategy
```sql
-- Existing indexes
CREATE INDEX idx_videos_channel ON Videos(channel_id);
CREATE INDEX idx_videos_date ON Videos(video_date);
CREATE INDEX idx_subtitles_video ON Subtitles(video_id);

-- New indexes for features
CREATE INDEX idx_subtitles_language ON Subtitles(language_code);
CREATE INDEX idx_search_history_timestamp ON SearchHistory(timestamp);
CREATE INDEX idx_chapters_video ON Chapters(video_id);
```

#### PR-10.2.2: Query Optimization
- Use `EXPLAIN QUERY PLAN` for all new queries
- Avoid N+1 query patterns
- Use JOINs instead of subqueries when appropriate
- Batch operations with transactions

#### PR-10.2.3: Database Size Management
- **Typical Size:** ~100MB per 1000 videos (subtitles only)
- **With Embeddings:** ~1GB per 1000 videos (depends on model)
- **Cleanup:** Provide vacuum and reindex commands
- **Archive:** Support for archiving old data

---

### 10.3 API Performance (Server Mode)

#### PR-10.3.1: Response Time Targets
- **Simple queries:** < 100ms (health check, status)
- **Search queries:** < 1 second
- **Complex operations:** < 5 seconds (export, bulk operations)

#### PR-10.3.2: Concurrency
- **Target:** 100 concurrent requests
- **Connection Pooling:** Reuse database connections
- **Async Support:** Use FastAPI async endpoints

#### PR-10.3.3: Rate Limiting
- **Default:** 100 requests/minute per API key
- **Burst:** Allow short bursts with token bucket
- **Headers:** Include rate limit info in response headers

```python
# Example rate limiting headers
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703420400
```

---

## 11. Testing & Validation Requirements

### 11.1 Unit Testing Requirements

#### TVR-11.1.1: Coverage Targets
- **Minimum:** 80% code coverage for new features
- **Target:** 90% coverage for critical paths (search, database)
- **Tools:** pytest with pytest-cov

#### TVR-11.1.2: Test Categories
1. **Unit Tests:** Test individual functions and classes
2. **Integration Tests:** Test interaction between components
3. **End-to-End Tests:** Test complete user workflows
4. **Performance Tests:** Validate performance requirements

#### TVR-11.1.3: Mock Strategy
- **External APIs:** Mock all external API calls
- **Database:** Use in-memory SQLite for tests
- **File System:** Use temporary directories for file operations
- **Time:** Mock time for deterministic tests

**Example:**
```python
import pytest
from unittest.mock import Mock, patch
from yt_fts.llm.summarize import SummarizeHandler

def test_summarize_video():
    """Test video summarization with mocked LLM API."""
    handler = SummarizeHandler(
        api_key="test_key",
        model_config={"chat_model": "gemini-pro"},
        video_id="test123"
    )

    # Mock LLM API call
    with patch.object(handler, '_call_llm') as mock_llm:
        mock_llm.return_value = "Test summary"

        result = handler.summarize_video()

        assert result == "Test summary"
        mock_llm.assert_called_once()
```

---

### 11.2 Integration Testing Requirements

#### TVR-11.2.1: API Integration Tests
- Test each external API integration
- Test authentication flows
- Test error scenarios (timeouts, auth failures)
- Use test credentials or mocks

#### TVR-11.2.2: Database Integration Tests
- Test schema migrations
- Test transaction rollback
- Test concurrent access
- Use test database fixtures

---

### 11.3 End-to-End Testing Requirements

#### TVR-11.3.1: User Workflow Tests
Test complete user workflows for each feature:

**Example: Time-Based Search Workflow**
```python
def test_time_based_search_workflow(tmp_path):
    """Test complete time-based search workflow."""
    # Setup: Download channel with videos
    result = subprocess.run([
        "yt-fts", "download",
        "--language", "en",
        "--jobs", "1",
        "https://www.youtube.com/@testchannel"
    ])

    assert result.returncode == 0

    # Test: Search with time filter
    result = subprocess.run([
        "yt-fts", "search",
        "machine learning",
        "--after", "2023-01-01",
        "--before", "2023-12-31",
        "--export"
    ])

    assert result.returncode == 0
    assert Path("search_results.csv").exists()

    # Verify: Check exported CSV
    df = pd.read_csv("search_results.csv")
    assert all(df["timestamp"] >= "2023-01-01")
    assert all(df["timestamp"] <= "2023-12-31")
```

---

### 11.4 Performance Testing Requirements

#### TVR-11.4.1: Benchmark Tests
- Measure search performance on large datasets
- Track performance over time (regression testing)
- Profile memory usage
- Test database query performance

#### TVR-11.4.2: Load Tests (API Server)
- Test API server under load
- Measure response time percentiles (p50, p95, p99)
- Test concurrent request handling
- Identify bottlenecks

---

### 11.5 Validation Requirements

#### TVR-11.5.1: Data Validation
- Validate all user inputs
- Validate API responses
- Validate export formats
- Validate database schema integrity

#### TVR-11.5.2: Schema Validation
- Validate JSON output against schemas
- Validate export file formats
- Validate citation formats against style guides

---

## 12. Documentation Requirements

### 12.1 User Documentation

#### DR-12.1.1: README Updates
Update README.md with new features:
- Feature overview for each sprint
- Usage examples for each command
- Installation instructions for optional dependencies
- Configuration guide

#### DR-12.1.2: Command Help Text
- Comprehensive help for each command
- Examples for common use cases
- Cross-references to related commands
- Troubleshooting tips

#### DR-12.1.3: Feature Guides
Create detailed guides for complex features:
- Search history and saved queries guide
- Citation export guide (APA, MLA, BibTeX)
- Obsidian integration guide
- Notion/Zotero integration guide
- Flashcard generation guide

---

### 12.2 Developer Documentation

#### DR-12.2.1: Architecture Documentation
- Database schema documentation
- API endpoint documentation (OpenAPI/Swagger)
- Integration architecture diagrams
- Code organization overview

#### DR-12.2.2: Contribution Guidelines
- Coding standards (Ruff, Black, mypy)
- Testing requirements
- Pull request guidelines
- Code review checklist

#### DR-12.2.3: API Documentation
- Auto-generated OpenAPI/Swagger docs
- Example requests/responses
- Authentication documentation
- Rate limiting documentation

---

### 12.3 Operations Documentation

#### DR-12.3.1: Deployment Guide
- Installation guide for different platforms
- Configuration options reference
- Environment variables reference
- Troubleshooting guide

#### DR-12.3.2: Maintenance Guide
- Database maintenance (vacuum, reindex)
- Log file management
- Backup and restore procedures
- Performance tuning guide

---

### 12.4 Changelog Requirements

#### DR-12.4.1: Changelog Format
Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [Unreleased]

### Added
- Time-based search filters (--after, --before, --last)
- Proximity search with NEAR operator
- Search history and saved queries
- JSON output mode

### Changed
- Improved search performance with new indexes
- Enhanced error messages

### Fixed
- Fixed date parsing for non-English locales

### Removed
- (None)

## [1.0.0] - 2025-01-XX
```

---

## 13. Implementation Priority & Phasing

### Sprint 1 (Weeks 1-2): Enhanced Search
**Priority:** High | **Risk:** Low | **Dependencies:** None

**Features:**
1. Time-based search filters (FR-1.1)
2. Proximity search (FR-1.2)
3. Search history and saved queries (FR-1.3)
4. JSON output mode (FR-1.4)

**Success Criteria:**
- All search commands support time filters
- Proximity search works correctly
- History and saved queries persist across sessions
- JSON export is valid and parseable

---

### Sprint 2 (Weeks 3-4): Knowledge Management
**Priority:** High | **Risk:** Medium | **Dependencies:** Sprint 1

**Features:**
5. Obsidian/Roam Research markdown export (FR-2.1)
6. Citation export (FR-2.2)
7. Notion/Zotero integration (FR-2.3)

**Success Criteria:**
- Obsidian markdown imports correctly
- Citations match style guide specifications
- API integrations authenticate and export successfully

---

### Sprint 3 (Weeks 5-6): Learning Features
**Priority:** Medium | **Risk:** High | **Dependencies:** Sprint 1, existing LLM integration

**Features:**
8. Flashcard generation (FR-3.1)
9. Chapter/segment detection (FR-3.2)
10. Multi-language subtitle support (FR-3.3)
11. Translation layer (FR-3.4)

**Success Criteria:**
- Anki packages import successfully
- Chapters accurately reflect video structure
- Multiple languages download and search correctly
- Translation is accurate and cost-effective

---

### Sprint 4 (Weeks 7-8): Automation & Infrastructure
**Priority:** Medium | **Risk:** High | **Dependencies:** All previous sprints

**Features:**
12. Watch mode / auto-update (FR-4.1)
13. API server mode (FR-4.2)

**Success Criteria:**
- Watch mode daemon runs reliably
- API server handles concurrent requests
- Both features gracefully handle failures

---

## 14. Risk Assessment & Mitigation

### 14.1 Technical Risks

#### Risk-14.1.1: API Service Dependencies
**Risk:** External APIs (Notion, Zotero, Translation) may change or become unavailable

**Mitigation:**
- Feature flag all external API integrations
- Implement graceful degradation
- Provide clear error messages
- Document API version requirements
- Monitor API deprecation notices

#### Risk-14.1.2: Database Performance
**Risk:** Large databases may become slow with new features

**Mitigation:**
- Add appropriate indexes
- Implement query optimization
- Provide database maintenance tools
- Test with realistic datasets
- Document performance expectations

#### Risk-14.1.3: LLM API Costs
**Risk:** Features using LLMs (flashcards, chapters, translation) may be expensive

**Mitigation:**
- Cost estimation before running
- Caching to minimize API calls
- Local model alternatives where possible
- User control over LLM usage
- Clear documentation of costs

---

### 14.2 User Experience Risks

#### Risk-14.2.1: Complexity Overload
**Risk:** Too many features may overwhelm users

**Mitigation:**
- Sensible defaults
- Progressive disclosure (advanced options hidden)
- Comprehensive documentation
- Interactive help
- Tutorial mode

#### Risk-14.2.2: Breaking Changes
**Risk:** New features may break existing workflows

**Mitigation:**
- Backward compatibility
- Deprecation warnings
- Migration guides
- Extensive testing
- Beta testing period

---

### 14.3 Security Risks

#### Risk-14.3.1: API Key Exposure
**Risk:** API keys may be exposed in logs or error messages

**Mitigation:**
- Strict logging policies
- Sanitize error messages
- Restrictive file permissions
- User education on security
- Security audit

#### Risk-14.3.2: Code Execution
**Risk:** Watch mode and API server increase attack surface

**Mitigation:**
- Input validation
- Sandboxing where possible
- Principle of least privilege
- Security review
- Regular updates

---

## 15. Success Metrics

### 15.1 Feature Adoption Metrics
- Number of users using each feature
- Frequency of feature usage
- Feature retention over time

### 15.2 User Satisfaction Metrics
- User feedback and reviews
- Bug reports and feature requests
- Support request volume

### 15.3 Technical Metrics
- Search latency (p50, p95, p99)
- API response times
- Error rates
- Test coverage percentage

### 15.4 Constitutional Compliance Metrics
- Privacy audit results
- Data portability success rate
- Feature flag usage (opt-in vs opt-out)

---

## 16. Appendices

### Appendix A: Glossary

- **FTS:** Full-Text Search - search functionality that examines all words in every document
- **RAG:** Retrieval-Augmented Generation - AI technique combining retrieval with generation
- **PKM:** Personal Knowledge Management - tools and methods for organizing information
- **NEAR:** Proximity search operator that finds terms within a specified distance
- **YAML Frontmatter:** Metadata block at the top of markdown files
- **Anki:** Spaced repetition software for flashcard learning
- **Notion:** Workspace and note-taking application
- **Zotero:** Citation management software
- **Obsidian:** Markdown-based knowledge base application
- **Roam Research:** Block-based note-taking tool

---

### Appendix B: References

1. **yt-fts Repository:** https://github.com/NotJoeMartinez/yt-fts
2. **SQLite FTS5 Documentation:** https://www.sqlite.org/fts3.html
3. **Click Documentation:** https://click.palletsprojects.com/
4. **Rich Documentation:** https://rich.readthedocs.io/
5. **FastAPI Documentation:** https://fastapi.tiangolo.com/
6. **Anki Package Format:** https://docs.ankiweb.net/
7. **APA Style Guide:** https://apastyle.apa.org/
8. **MLA Style Guide:** https://style.mla.org/
9. **BibTeX Format:** https://www.bibtex.org/

---

### Appendix C: Command Reference (Proposed)

#### New Commands Overview

```bash
# Sprint 1: Enhanced Search
yt-fts search "query" --after "2024-01-01" --before "2024-12-31"
yt-fts search "term1 NEAR/5 term2"
yt-fts history list --limit 20
yt-fts saved list
yt-fts saved run "my-search"
yt-fts search "query" --json

# Sprint 2: Knowledge Management
yt-fts export --channel "Name" --format obsidian
yt-fts export-citation bibtex --channel "Name"
yt-fts export-notion --channel "Name" --database-id "xxx"
yt-fts export-zotero --channel "Name" --collection "Research"

# Sprint 3: Learning Features
yt-fts flashcards generate --channel "Name" --output "cards.apkg"
yt-fts chapters detect --video-id "xxx"
yt-fts download --language es --channel "URL"
yt-fts search "query" --translate-to es

# Sprint 4: Automation & Infrastructure
yt-fts watch add --channel "Name" --interval "1h"
yt-fts watch start
yt-fts watch status
yt-fts server start --port 8080
```

---

## Document Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-24 | Claude (Sonnet 4.5) | Initial requirements analysis |

---

## Approval & Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Project Lead | | | |
| Technical Lead | | | |
| Security Reviewer | | | |
| Constitutional Compliance | | | |

---

**END OF REQUIREMENTS ANALYSIS DOCUMENT**

This document provides a comprehensive foundation for implementing the 13 approved features across 4 sprints. All requirements are aligned with constitutional principles (user autonomy, privacy protection, transparent operations, optional dependencies) and target the needs of Truth Seekers, Researchers, and Learners.
