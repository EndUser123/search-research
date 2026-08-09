---
title: "NotebookLM (Gemini Notebook) Programmatic Access — Deep Research, Temp Notebooks, and Wiki Integration Patterns"
created: 2026-07-24
source: session-2026-07-24
tags: [notebooklm, gemini-notebook, nlm, deep-research, automation, mcp, wiki-integration]
summary: >
  Google's NotebookLM (rebranded "Gemini Notebook" July 2026) has a Deep
  Research mode that finds 40+ sources per topic, a CLI (nlm v0.9.0) for
  programmatic access, and MCP server integration. Key patterns: temp
  notebooks as research staging areas (create → deep research → extract
  sources → /crawl4ai into wiki → delete), cross-notebook querying, and
  multi-format artifact generation (podcasts, slides, quizzes). The nlm
  CLI is installed locally with 39 MCP tools and 16 command categories.
agent: grok
host: grok
cognitive_load: 3
verification: web-research-verified
---

## Summary

NotebookLM (now "Gemini Notebook" as of July 2026) is an underutilized
resource in this workspace. The `nlm` CLI (v0.9.0) is installed and working,
providing programmatic access to all of NotebookLM's features — including
**Deep Research** mode (added Nov 2025) which automates online research and
discovers 40+ sources per topic. This concept documents the integration
patterns for using NotebookLM as a research source feeder for the local wiki,
including the "temp notebook staging" pattern.

## Decision context

Research was motivated by the operator's question: "we are missing a huge
resource by not using Gemini notebooks." The wiki had no NotebookLM concepts.
The nlm CLI was installed but not integrated into any research workflow.
The research changed the approach from "use NotebookLM for podcast generation"
(initial idea) to "use NotebookLM's Deep Research as a source discovery engine
that feeds the wiki" (operator's better idea).

## 1. What NotebookLM / Gemini Notebook is [HIGH confidence — official sources]

NotebookLM is Google's AI-powered research tool that uses Gemini to analyze
sources (web pages, YouTube, PDFs, text, Google Drive docs). As of July 2026,
it was rebranded to "Gemini Notebook" but remains the same product at
notebooklm.google.com.

**Core capabilities:**
- **Source management**: add URLs, YouTube videos, text, files, Drive docs
- **Deep Research** (Nov 2025): automated web research that finds 40+ sources
  per topic. Two modes: `fast` (~30s, ~10 sources) and `deep` (~5min, ~40+
  sources, web only)
- **Cross-source querying**: ask questions answered from all sources
- **Multi-format generation**: audio overviews (podcasts), reports, quizzes,
  flashcards, mind maps, slides, infographics, videos, data tables
- **Cross-notebook querying**: aggregate answers across multiple notebooks

## 2. The nlm CLI — installed and ready [HIGH confidence — local verification]

The `nlm` CLI (from [jacob-bd/notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli))
is installed at v0.9.0. It provides:

- **16 command categories**: auth, notebooks, sources, research, studio
  (generation), chat, sharing, aliases, config, batch, cross-query, pipelines,
  tags, diagnostics, skill management
- **39 MCP tools**: notebook CRUD, source management, research, studio creation,
  batch operations, cross-notebook queries, pipelines
- **Cookie-based auth**: `nlm login` launches browser, extracts cookies
- **Multi-profile**: multiple Google accounts simultaneously

**Quick reference:**
```bash
nlm notebook create "Title"                    # Create notebook, get ID
nlm research start "query" --notebook-id <id> --mode deep  # Deep research (~5min, 40+ sources)
nlm research status <id>                       # Poll until done
nlm research import <id> <task-id>             # Import discovered sources
nlm source list <id>                           # List sources with URLs
nlm notebook query <id> "question"             # One-shot Q&A with sources
nlm audio create <id> --confirm                # Generate podcast
nlm notebook delete <id> --confirm             # Delete notebook
```

## 3. Integration pattern: temp notebook as research staging [DESIGN — operator-proposed]

The highest-value pattern for this workspace:

```
1. Create temp notebook:     nlm notebook create "temp: <topic>"
2. Run deep research:        nlm research start "<query>" --mode deep --auto-import
3. Wait for completion:      nlm research status <id> --max-wait 900
4. Extract source URLs:      nlm source list <id> --url
5. Ingest into wiki:         /crawl4ai <each-url> --collection wiki
6. Query the corpus:         nlm notebook query <id> "<question>"
7. Delete temp notebook:     nlm notebook delete <id> --confirm
```

**Why this works:**
- NotebookLM's Deep Research uses Google's search index + Gemini reasoning
  to find relevant sources — broader than /web's backend fan-out
- The wiki gets the raw source material (via /crawl4ai) for durable access
- The temp notebook provides AI-powered querying of the sources during
  research, then is deleted to avoid clutter
- The wiki's staleness detectors handle freshness (library docs: 6-12 months)

**What this replaces:**
- /web's search fan-out → NotebookLM Deep Research (broader source discovery)
- Manual URL collection → automated source discovery + import
- One-shot search → AI-curated research with 40+ sources

## 4. Integration with /www [DESIGN — proposed]

NotebookLM becomes a Round 2.5 source discovery option alongside /crawl4ai:

| Current /www Round 2.5 | With NotebookLM |
|---|---|
| /crawl4ai ingests known URLs into wiki | NotebookLM Deep Research discovers NEW URLs, then /crawl4ai ingests them |
| User provides URLs or /web finds them | NotebookLM's Google-index search finds broader sources |
| Sources are what /web already found | Sources are what Gemini's reasoning decides are relevant |

**When to use NotebookLM over /web for source discovery:**
- Topic is broad and multi-faceted (Deep Research excels at synthesis)
- /web's backends return too few relevant results
- The research needs authoritative academic/reference sources (Google's index
  is stronger here than DDG/Exa)

**When NOT to use:**
- Topic is time-sensitive (Deep Research takes 5 minutes)
- Topic is niche/obscure (Google's index may not cover it)
- Only need 1-2 specific URLs (overkill — use /firecrawl-scrape directly)

## 5. Integration with /go and /preflight [DESIGN — proposed]

- **/preflight**: when discovering a library/framework, create a temp NotebookLM
  notebook with the docs as sources, then query it for "what are the common
  pitfalls and gotchas?" — the answer supplements the wiki's coverage
- **/go**: during implementation, if the wiki doesn't cover a specific API
  pattern, query a temp NotebookLM notebook with the library docs for that
  specific question

## 6. Creative uses beyond research staging [MEDIUM confidence — web research]

| Use case | How | Value |
|---|---|---|
| **Podcast generation** | After /www research, `nlm audio create <id>` from the research notebook | Audio summary of research findings for commute listening |
| **Study materials** | `nlm quiz create` + `nlm flashcards create` from wiki concept sources | Learn new topics actively |
| **Slide generation** | `nlm slides create` from research sources | Present research findings |
| **Cross-notebook synthesis** | `nlm cross query "compare approaches" --tags "ai,research"` | Aggregate knowledge across multiple research sessions |
| **Batch podcast generation** | `nlm batch studio audio --tags "research"` | Generate podcasts for all tagged notebooks at once |
| **Pipeline automation** | `nlm pipeline run ingest-and-podcast --input-url <url>` | One-command: ingest URL → generate podcast |

## 7. Tool comparison — nlm vs notebooklm-py [HIGH confidence — both installed + tested]

**Both tools are already installed on this host.** They are complementary, not competitive.

| Dimension | `nlm` (jacob-bd/notebooklm-mcp-cli) | `notebooklm` (teng-lin/notebooklm-py) |
|---|---|---|
| **Version** | 0.9.0 | 0.8.0rc1 |
| **Package** | `pip install notebooklm-mcp-cli` | `pip install notebooklm-py` |
| **Python API** | ❌ CLI/MCP only | ✅ `from notebooklm import NotebookLMClient` |
| **CLI** | `nlm` (16 command categories) | `python -m notebooklm` |
| **MCP server** | ✅ 39 tools built-in | ❌ Via separate package (ari-agnt/notebooklm-mcp) |
| **Python 3.14** | ✅ Works | ✅ Explicitly supported |
| **Async** | Subprocess-based | ✅ Native httpx async |
| **Auth** | Cookie-based, multi-profile | Cookie-based, multi-profile (shared format) |
| **Advanced** | Pipelines, tags, batch, cross-query | Research API, mind maps, conversation cache |
| **Upstream role** | Independent implementation | Other tools build on it (ari-agnt, curara81) |
| **Best for** | MCP/agent integration (Grok calls tools) | Python script integration (import in skills) |

**Recommendation: use BOTH.**
- `notebooklm-py` for Python-level integration (temp notebook staging pattern in /www scripts)
- `nlm` for MCP/agent integration (Grok calls MCP tools directly)
- Both share Google cookie auth — `nlm login` credentials work for `notebooklm-py` and vice versa

**The Python API the user asked about:**
```python
from notebooklm import NotebookLMClient

client = NotebookLMClient()
await client.from_storage()  # use saved cookies from nlm login
# High-level operations through domain objects:
# Notebook, Source, Artifact, ResearchSource, ResearchTask
```

### Other tools (not installed)

| Tool | Type | Notes |
|---|---|---|
| **notebooklm-go** (localkinai) | Go client | Single binary, no Python runtime — good for CI/CD |
| **notebooklm-cli** (dokkabei97) | Go CLI | Another Go option, cross-platform binary |
| **notebooklm-toolkit** (curara81) | Claude Code skill | Built on notebooklm-py — adds bulk YouTube import |
| **notebooklm-mcp** (ari-agnt) | MCP server | Built on notebooklm-py — simpler than nlm's MCP |
| **Google Enterprise API** | Official | Enterprise-only, not publicly accessible |

**Recommendation:** stick with `nlm` — it's the most complete, actively
maintained (updated daily), and already installed. The MCP server provides
39 tools accessible from any AI agent.

## Sources

- https://github.com/jacob-bd/notebooklm-mcp-cli — Primary CLI/MCP tool (authority=3, recency=3)
- https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-deep-research-file-types/ — Deep Research announcement (authority=3, recency=3)
- https://notebooklm.google/ — Official site (now "Gemini Notebook") (authority=3, recency=3)
- https://www.reddit.com/r/notebooklm/comments/1qs7v2s/ — nlm v0.2.7 release notes (authority=2, recency=3)
- https://web-clipper-for-notebooklm.com/blog/notebooklm-api — API overview (authority=2, recency=3)
- Local: `~/.agents/skills/nlm-skill/SKILL.md` — Installed skill documentation (890 lines)

## Related

- deep-research-systems@related — Deep research agent patterns
- [[textual-layout-widgets-ecosystem]]@related — Example /www output that could feed NotebookLM
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
