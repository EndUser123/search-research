---
title: "Andre Karpathie has published work on how to use Obsidian as a cloud code wiki or memory system. Lots of people have wri"
date: "2026-04-07"
mode: "COPILOT"
uuid: "789bb158-c1f3-4788-affc-2b67fb8538d5"
entry_count: 9
---

## Human

Andre Karpathie has published work on how to use Obsidian as a cloud code wiki or memory system. Lots of people have written articles and created YouTube videos on it.  Please give me a deep research prompt I can take to Notebook.lm to create a notebook so that I can have actionable information on how to design it, implement it, and maintain it in Cloud Code on Windows 11.

## Assistant

**NotebookLM Prompt: Build Karpathy-Inspired Obsidian LLM Wiki for Cloud Code on Windows 11**

Create a comprehensive research notebook on implementing Andrej Karpathy's LLM Wiki pattern (raw sources → LLM-maintained wiki in Obsidian) as a code wiki/memory system using Claude Code (aka Cloud Code) on Windows 11. Use these sources: Karpathy's full GitHub Gist "LLM Wiki", detailed breakdowns like antigravity.codes guide, YouTube setups (e.g., OSZdFnQmgRw, sboNwYmH3AY, 7huCP6RkcY4), Windows-specific Claude Code installs, Obsidian-Claude integrations (plugins, Git sync).[1][2][3][4][5][6][7][8][9][10]

**Core Focus: Actionable Design, Implementation, Maintenance**

Extract **exact steps** tailored to Windows 11 + Claude Code + Obsidian vault (local folder). Assume user is advanced dev (Python/TS, multi-agent workflows, Claude expertise); prioritize minimal changes, reuse tools (e.g., Git for sync, Obsidian plugins like Dataview/Marp/Git).

## 1. System Design (Architecture)
- Map 3-layer stack: raw/ (immutable sources), wiki/ (LLM-edits), CLAUDE.md schema.[1]
- Windows paths: e.g., C:\Users\[user]\ObsidianVaults\CodeWiki.
- Claude Code access: cd into vault dir, run `claude` [].
- Sync: Git repo (Obsidian Git plugin auto-commit/pull) [][].
- Scale: index.md/log.md navigation → qmd if >100 pages [].

Output: Diagram folder structure; YAML frontmatter spec; edge cases (image handling, contradictions).

## 2. Implementation Steps (Windows 11)
**Prerequisites:** Obsidian install, Claude Code (npm i -g @anthropic-ai/claude-code or WSL [][]), Anthropic API key, Git.

1. Create vault: mkdir CodeWiki; obsidian.exe CodeWiki [].
2. Plugins: Git, Advanced URI, Dataview, Marp, Local Images [][].
3. Claude Code: Install/restart PC; cd CodeWiki; claude [][].
4. Paste Karpathy Gist into Claude; prompt: "Build LLM Wiki here per idea file" [][page:1].
5. Config: CLAUDE.md workflows (ingest/query/lint) [][].
6. VS Code sync (if Cloud Code=VS Code Remote): Obsidian Code Sync ext [][].
7. Test ingest: Clip article → raw/articles/ → "ingest filename.md" [].

Output: Copy-paste CLI/PowerShell script for setup; troubleshoot (WSL paths /mnt/c/, ExecutionPolicy []).

## 3. Usage Workflows
- Ingest: Drop raw → Claude processes → updates 10-15 wiki pages [].
- Query: "Compare X across wiki" → file new page [].
- Lint: Health check contradictions/orphans [].
- Windows tips: Obsidian sidebar Claude plugin [][]; Git frequency [].

Output: Prompt templates for Claude; daily routine (side-by-side Obsidian/Claude terminal).

## 4. Maintenance & Optimization
- Git: Auto-sync .gitignore (.obsidian/, etc.) [].
- Evolve schema: Co-edit CLAUDE.md [].
- Backup: GitHub private repo [].
- Metrics: Dataview queries on frontmatter (sources count, confidence) [].
- Costs: /cost in Claude; batch ingests [].
- Edges: Large vaults (qmd MCP), multi-user Git PRs [].

**Generate Artifacts:**
- Full CLAUDE.md template customized for code wiki (entities=libs/frameworks, concepts=patterns).
- Batch setup PowerShell script.
- Example wiki after 5 ingests (code topics).
- Comparison table: RAG vs Wiki (pros/cons, token savings) [].
- Confidence: High on core (Karpathy primary []); Medium on Windows plugins (tutorials 2026 [][]).

Challenge assumptions: "Cloud Code" likely Claude Code (Karpathy/Claude context); confirm VS Code if not. Prioritize official/Anthropic sources > YT. List unknowns: Exact "Cloud Code" (Claude or VS Code Remote?). Next step: Copy this prompt to NotebookLM, generate notebook, run setup script. [][page:1][]

## Human

Karpathy's Obsidian LLM wiki fully implemented — step-by-step guide + starter template
Step-by-step guide to set up Karpathy's Obsidian LLM wiki
What plugins are essential for Claude Code in Obsidian
Examples of entity pages and folder structure in the vault

## Assistant

Karpathy's Obsidian LLM wiki uses Claude Code (or similar agents) to maintain a structured markdown knowledge base from raw sources. Here's a Windows 11-optimized step-by-step setup, drawing from his idea file and implementations.[1]

## Step-by-Step Setup
1. Install Obsidian (portable ZIP for Windows), Claude Code (`winget install Anthropic.ClaudeCode` or npm; restart PC).[2][1]
2. Create vault: `mkdir C:\ObsidianWiki && obsidian.exe C:\ObsidianWiki`.[3]
3. Init structure via PowerShell in vault dir: `mkdir raw\articles,raw\assets,raw\papers; mkdir wiki\concepts,wiki\entities,wiki\sources,wiki\comparisons; New-Item wiki\index.md, wiki\log.md, wiki\overview.md; git init`.[4][1]
4. Copy Karpathy's Gist  into `CLAUDE.md` at root; customize for code wiki (e.g., entities=libs like React).[1]
5. Plugins: Settings > Community > Browse/install **Obsidian Git** (auto-sync), **Dataview** (query frontmatter), **Marp** (slides), **Local Images Plus** (assets), **Terminal** or **Claude Sidebar** (embed Claude Code).[5][6][4][3]
6. `cd C:\ObsidianWiki`, run `claude`; paste: "Build LLM Wiki per CLAUDE.md for code topics".[1]
7. Clip first source (Obsidian Web Clipper ext), drop to `raw/articles/`, prompt Claude: "ingest filename.md".[1]
8. Git commit: `git add . && git commit -m "ingest: first"`.[1]

## Starter Template
Use this as `CLAUDE.md` root file (adapt from Karpathy ):[1]

```
# LLM Code Wiki Schema
## Structure
- raw/ immutable sources
- wiki/ LLM-owned: concepts/, entities/, sources/, comparisons/
- wiki/index.md: catalog w/ links, summaries
- wiki/log.md: append-only timeline (## [YYYY-MM-DD] ingest | Title)

## Frontmatter (all wiki pages)
---
title: Name
type: concept|entity|source-summary
sources: [raw/file1.md]
related: [[page1]]
confidence: high|medium|low
---

## Workflows
Ingest: Read raw/, summary → wiki/sources/, update 10-15 pages, index/log.
Query: Read index → synthesize w/ [[links]]; file answers as new pages.
Lint: Contradictions, orphans, gaps.
```
Repo starters: bashiraziz/llm-wiki-template.[7]

## Essential Plugins for Claude Code
- **Obsidian Git**: Auto-commit/pull vault.[4]
- **Dataview**: `TABLE sources FROM "wiki"` queries.[1]
- **Claude Sidebar/Terminal**: Embed `claude` in Obsidian (no API keys).[8][6][5]
- **Local Images Plus**: Download assets for Claude vision.[3]
Confidence: High (Karpathy primary ); plugins evolve fast—check Obsidian forum 2026.[6][4][1]

## Folder Structure
```
ObsidianWiki/
├── CLAUDE.md          # Schema
├── raw/
│   ├── articles/      # Clipped MD
│   ├── assets/        # Images
│   └── papers/
├── wiki/
│   ├── index.md       # Catalog
│   ├── log.md         # Timeline
│   ├── overview.md
│   ├── concepts/      # e.g., React-Hooks.md
│   ├── entities/      # e.g., NextJS.md
│   ├── sources/       # Summaries
│   └── comparisons/   # Tables
└── .git/
```
Scales to 100+ sources via index.md.[4][1]

## Entity Page Examples
Entity pages track specifics (e.g., `wiki/entities/React.md`):

```
---
title: React
type: entity
sources: [raw/articles/react-19.md]
related: [[React-Hooks]], [[NextJS]]
confidence: high
---
# React
Core UI lib by Facebook. V19 adds actions, hooks refinements.

## Key Features
- Components: Functional preferred
- State: useState, useReducer

Sources: 5 articles, 2 repos.
```
Concept: `wiki/concepts/React-Hooks.md` links entities, summaries. Next: Ingest a code article—what topic?[9][1]

## Human

What users discover about maintaining Karpathy-style LLM wikis long-term that initial setups overlook
How to ingest raw files into the LLM wiki using Claude
Common troubleshooting issues with Claude Code in Obsidian
Best practices for maintaining the wiki over time
Examples of topics for Karpathy style LLM wikis

## Assistant

Long-term users of Karpathy-style LLM wikis find maintenance burdens persist despite automation, with overlooked issues like schema drift and synthesis gaps emerging after months. Ingesting raw files relies on Claude Code workflows in Obsidian vaults, while troubleshooting focuses on Windows paths and auth. Best practices emphasize periodic lints and human oversight for compounding value.[1][2][3]

## Long-Term Discoveries
Initial setups overlook **schema evolution** (co-edit CLAUDE.md as domain changes), **decay without lints** (contradictions/orphans pile up), and **no auto-synthesis** (wiki stays factual but lacks original insights). Users report 95% token savings initially, but scale needs qmd/MCP for 1000+ pages; human review PRs for teams. Compounding requires daily health checks, not one-off ingests.[4][2][5][6][1]

## Ingest Process
1. Drop raw file (clipper/MD/PDF to `raw/articles/`).[7]
2. `cd vault; claude`; prompt: "ingest raw/articles/filename.md" → LLM reads, creates wiki/sources/summary.md, updates 10-15 pages (index, entities, log), cross-links.[1][7]
3. Verify in Obsidian, `git commit`. Batch: "ingest all new raw/".[1]

## Troubleshooting Claude Code
- **Path/Exec**: Restart PC post-install; `claude config` for PATH.[8][9]
- **Auth**: Logout browser, incognito relogin, clear cache.[9]
- **Obsidian**: Terminal plugin for `claude`; .obsidian/ paths in WSL/mnt/c.[10][8]
- **Git conflicts**: Obsidian Git auto-resolve or manual PRs. 90% fixed by restart/re-auth.[3][9]

## Maintenance Best Practices
- **Weekly Lint**: "Lint wiki: contradictions, orphans, gaps, web-fill" → append log.md.[6][1]
- **Git**: Auto-commit hourly, GitHub backup.[3]
- **Evolve**: Refine CLAUDE.md (frontmatter fields, workflows).[5][3]
- **Scale**: index.md queries via Dataview; human-review updates.[2][1]
- **Metrics**: Track /cost, page count in overview.md.[1]

## Wiki Topic Examples
- **Personal**: Goals, health logs, journal themes.[3]
- **Research**: ML papers (Karpathy's 400k-word vault), code libs (React/Next.js patterns).[11][1]
- **Business**: Slack/meetings → project timelines, customer insights.[1]
- **Hobbies**: Competitive analysis, trip planning, course notes. Code wiki: entities=frameworks (Django), concepts=patterns (CQRS).[3][1]

## Human

Best schema examples for Claude.md in Karpathy LLM wiki
How to set up periodic linting for wiki health checks
Integrating web searches to fill wiki data gaps

## Assistant

Karpathy's CLAUDE.md schema defines wiki structure, conventions, and workflows like ingest/lint for disciplined LLM maintenance. Periodic linting uses scheduled Claude prompts via Obsidian plugins or GitHub Actions, while web integration leverages Claude's tools for gap-filling. Examples and setups are from primary implementations.[1][2]

## Best CLAUDE.md Schemas
Karpathy's core, adapted for code wiki:[1]

```
# LLM Code Wiki Schema (for Claude Code)

## Structure
- raw/ : Immutable (articles/, assets/, papers/)
- wiki/ : LLM-owned (concepts/, entities/, sources/, comparisons/)
- wiki/index.md : Catalog w/ Dataview queries
- wiki/log.md : ## [YYYY-MM-DD] append-only

## Frontmatter (YAML, all wiki MD)
---
title: Page Name
type: concept|entity|source|comparison
sources: [raw/file1.md]
related: [[Entity1]], [[Concept2]]
confidence: high|medium|low
updated: YYYY-MM-DD
---

## Workflows
### Ingest raw/articles/filename.md
1. Read file.
2. Extract: summary → wiki/sources/filename.md; entities/concepts → new/update pages (10-15).
3. Cross-link [[links]].
4. Update index.md/log.md.

### Query "compare React Vue"
File wiki/comparisons/react-vs-vue.md; link from index.

### Lint
Health-check: contradictions, orphans (no inbound), gaps (web-fill?), stale.
```
Enhanced variants add flashcards/gaps.[3][2]

## Periodic Linting Setup
- **Manual**: `claude` → "Run lint per CLAUDE.md" → LLM scans, updates log.md.[1]
- **Automated**: Obsidian Git + Templater plugin (cron-like via Tasks); or GitHub Actions: weekly `claude lint` via SSH.[2]
- Prompt: "Lint wiki: contradictions (e.g., React hooks stale?), orphans, gaps (search web?), missing pages/cross-refs".[4][1]
- Track: Dataview `LIST FROM "wiki" WHERE confidence="low"`. Run post-ingest for health.[2]

## Web Search Integration
- **In Lint/Ingest**: Schema instructs: "Gaps? Use web_search tool: 'latest React 19 docs'" → ingest results.[1]
- **Claude Code**: Native `/web` or tools; prompt: "Fill gap on X: search, summarize, integrate".[5]
- **qmd CLI**: Local search + web rerank for scale. Best: Limit to authoritative sources (official docs > blogs); verify confidence. Next step: Adapt schema to your domain (e.g., AI tools)—what focus?[4][2][1]

## Human

Obsidian plugins for Karpathy LLM wiki
CLI tools like npx for automating wiki compilation

## Assistant

Obsidian plugins enable Claude Code integration and wiki management for Karpathy-style LLM wikis. CLI tools like npx automate compilation via agent wrappers, complementing manual Claude sessions.[1][2]

## Key Obsidian Plugins
- **Obsidian Git**: Auto-commit/pull vault changes post-LLM edits.[1]
- **Dataview**: Query index.md (e.g., `LIST FROM "wiki" WHERE confidence="low"`), graph views for orphans/hubs.[2][1]
- **Marp**: LLM-generated slide decks from wiki pages.[1]
- **Terminal** (by polyipseity): Run `claude` inside Obsidian for seamless edits.[3][4]
- **Local API**: Expose vault to Claude Code for search/frontmatter access (generate API key).[3]
- **Obsidian Skills** or **Wikilink Types**: Agent-native wikilinks, YAML relations.[5][6]
Confidence: High—Karpathy explicitly uses Dataview/Marp/Git; others from 2026 Claude-Obsidian guides.[3][1]

## CLI Automation Tools
- **Claude Code (`claude`)**: Core—`npx @anthropic-ai/claude-code` (if npm); `claude ingest raw/file.md` or lint.[7]
- **qmd**: `npx qmd mcp` starts MCP server for wiki search/indexing at scale (>100 pages).[2]
- **cw (CodeWiki CLI)**: `npx cw init` scaffolds repo wiki; `cw index` rebuilds _index.md; `cw setup claude-code` installs skills.[8]
- **llm-kb**: `npx llm-kb run ./raw` indexes to wiki via Pi SDK sessions.[9]
Setup: In vault dir, `npm i -g` tools; define slash commands in `.claude/commands/` for Obsidian automation. Next step: Install Terminal + Local API, test `claude lint`.[10][8][2][3]

## Human

How to setup Local API plugin for LLM editing in Obsidian
Wikilink Types plugin tutorial for Karpathy wiki
npx llm-kb CLI full setup and usage guide
Notemd plugin features for auto-linking in Obsidian
Best practices for separate vaults in Karpathy LLM workflow

## Assistant

Obsidian plugins like Local REST API enable LLM editing via HTTP endpoints, while Wikilink Types and NoteMD enhance Karpathy wiki linking. npx llm-knowledge-bases provides CLI automation; separate vaults prevent contamination.[1][2][3]

## Local REST API Setup
1. Obsidian > Settings > Community Plugins > Browse > "Local REST API" (by Adam Coddington) > Install/Enable.[2][1]
2. Settings > Local REST API > Generate API key (copy).[1]
3. For Claude Code: Add to `.claude/config.json` or MCP skill: `{"api_key": "your_key", "base_url": "http://localhost:27123"}`.[4][5]
4. Test: `curl -H "x-api-key: your_key" http://localhost:27123/health` → LLM prompts use vault read/write/search.[2][1]

## Wikilink Types Tutorial
1. BRAT (Beta Reviewer App) or community install: `penfieldlabs/obsidian-wikilink-types`.[6][7]
2. Settings > Wikilink Types > Configure types (e.g., @supports, @contradicts, @extends for wiki relations).[6]
3. Usage: `[[React]]@supports` → auto YAML frontmatter `relations: {supports: [React]}`; bidirectional sync.[7]
4. Karpathy fit: Typed links in index.md (e.g., [[React-Hooks]]@implements); Dataview queries on relations.[6]

## npx llm-kb Guide
`llm-knowledge-bases` CLI for wiki runtime.[3]

**Setup:**
```
npx llm-knowledge-bases init --vault-root /path/to/vault
# Configures MCP/CLI for Claude Code
```

**Usage:**
- `npx llm-knowledge-bases kb_status --vault-root ./vault` : Health/index.
- `npx llm-knowledge-bases kb_list_raw --vault-root ./vault --changed-only` : New files.
- `npx llm-knowledge-bases kb_read_raw --vault-root ./vault --raw-path raw/notes/file.md` : Ingest prep.
- `npx llm-knowledge-bases kb_prepare_source ...` : Process to wiki/.[3]
Integrate: `claude` → "Use llm-kb MCP for vault".[3]

## NoteMD Features
- AI chunking/processing (OpenAI/Anthropic/Ollama): Bulk docs → wiki-links, concept notes.[8]
- Auto-linking: Context-aware inserts [[links]] during summarization.[8]
- Web search (Tavily): Gap-fill summaries.
- Dupe detection, Mermaid/LaTeX fix, retry logic.
Karpathy use: Process raw/ → auto-links in wiki/sources/.[8]

## Separate Vaults Practices
- **Clean (personal)**: Human-curated, high S/N; no LLM writes.[9]
- **Messy (wiki)**: LLM-compiled (raw/, wiki/); link via external embeds or symlinks.[9]
- Switch: File > Open vault > Manage vaults.
- Best: Git separate repos; Dataview cross-vault queries (plugins); prevents RAG contamination. Next: Domain for vault (code/AI)?[10][9][1][2][3]

## Human

What are the repos that I should put in my notebook LM Regarding this ClotCode Obsidian solution.

## Assistant

**Core Repos for NotebookLM on Claude Code (Cloud Code) + Obsidian LLM Wiki**

Upload these GitHub repos/gists to NotebookLM for deep analysis, templates, and Claude-specific integrations. Prioritizes 2026 Karpathy implementations over generics.[1][2][3]

| Repo/Gist | Description | Why Essential |
|-----------|-------------|---------------|
| [karpathy/LLM Wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) [1] | Schema (CLAUDE.md), workflows (ingest/lint), folder structure (raw/wiki) | Canonical idea file—paste to Claude for bootstrap. |
| [heyitsnoah/claudesidian](https://github.com/heyitsnoah/claudesidian) [3] | Pre-configured Obsidian vault + Claude Code starter (PARA, Git, CLAUDE.md) | Turnkey setup; auto-imports existing vaults. |
| [iansinnott/obsidian-claude-code-mcp](https://github.com/iansinnott/obsidian-claude-code-mcp) [4] | MCP plugin for Claude Code/ Desktop vault access (read/write/search) | Enables LLM editing via WebSocket/HTTP; auto-discovery. |
| [rohitg00/LLM Wiki v2 Gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) [5] | Karpathy extension w/ agentmemory patterns | Advanced scaling, persistent memory. |
| [manimohans/obsidian-local-llm-helper](https://github.com/manimohans/obsidian-local-llm-helper) [6] | Local LLM helper + CLAUDE.md for Obsidian | Text processing, chat; Claude-compatible. |
| [hancengiz/cc-obsidian-vault-api-skill](https://github.com/hancengiz/cc-obsidian-vault-api-skill) [7] | Claude Code skill for vault API | Direct LLM vault interaction. |
| [Magic-wei/obsidian_wiki_template](https://github.com/Magic-wei/obsidian_wiki_template) [8] | Basic wiki template (plugins/config) | Foundation for custom CLAUDE.md. |

**NotebookLM Instructions:** Analyze for Windows 11 Claude Code setup, extract schemas/scripts, generate vault scaffold. Fork/clone for testing. Confidence: High (direct Karpathy/Claude hits); check dates for 2026 updates. Next step: Upload Gist first.[3][4][1]

## Human

Differences between claudesidian and Karpathy LLM Wiki
Best raw sources to index in Claude Code Obsidian

## Assistant

ClaudeSidian is a pre-configured Obsidian vault repo inspired by Karpathy's LLM wiki pattern, optimized for Claude Code. Raw sources should be high-signal, immutable clips for effective wiki compilation.[1][2][3]

## Key Differences
| Aspect | Karpathy LLM Wiki | ClaudeSidian |
|--------|-------------------|--------------|
| **Nature** | Conceptual idea file (Gist); raw pattern/schema [2] | Repo/template vault; ready-to-clone Obsidian + Claude Code setup [3] |
| **Structure** | 3 layers: raw/ (immutable), wiki/ (LLM-owned), CLAUDE.md schema [2][1] | PARA method + Git; auto-imports vaults, personalized CLAUDE.md [3] |
| **Automation** | Manual Claude prompts (ingest/lint) [2] | Scripts for deps/Git; Gemini Vision/Firecrawl optional [3] |
| **Scale** | 400k words, Obsidian IDE view [4] | Mobile sync, existing vault migration [3] |
| **Focus** | General knowledge compounding (no RAG) [1] | AI thinking partner w/ version control [3] |

ClaudeSidian implements/extends Karpathy for ease—clone it for Claude Code.[2][3]

## Best Raw Sources
- **Articles/Clips**: Web Clipper MD (news, blogs); download images to raw/assets/.[5][1]
- **Papers**: ArXiv/PDFs (OCR if needed via Claude Vision).[2]
- **Code/Repos**: GitHub READMEs, issues, code snippets; zip to raw/repos/.[6]
- **Personal**: Slack exports, meeting notes, journal MD.[2]
- **Media**: Images/videos (Vision ingest), data CSVs.[5]
Prioritize **curated, high-S/N** (5-50 pages/week); immutable—LLM extracts to wiki/. Avoid noise; verify sources in lint.[4][1][2]

## Human

please show me a list of the youtube urls you used, and suggest any follow up youtube urls you think are useful for this topic.

## Assistant

Here’s a deduplicated list of all unique YouTube URLs referenced across our Claude Code/Obsidian LLM wiki research (Karpathy-inspired). Follow-ups target 2026 hands-on setups.[1][2]

## Referenced YouTube URLs
- https://www.youtube.com/watch?v=OSZdFnQmgRw (Karpathy's Obsidian RAG + Claude Code)[1]
- https://www.youtube.com/watch?v=sboNwYmH3AY (Karpathy 10x'd Claude Code)[3]
- https://www.youtube.com/watch?v=7huCP6RkcY4 (Self-Evolving Claude Code Memory)[4]
- https://www.youtube.com/watch?v=cr9_A4kGzBc (Claude x Obsidian Setup Guide)[2]
- https://www.youtube.com/watch?v=Y2rpFa43jTo (Obsidian + Claude Code Second Brain)[5]
- https://www.youtube.com/watch?v=6MBq1paspVU (Obsidian + Claude Code Daily Use)[6]
- https://www.youtube.com/watch?v=1vPJAWiFWQE (Claude Code + Karpathy Obsidian)[7]
- https://www.youtube.com/watch?v=VUnABqzrZQg (Karpathy's 400k-Word Wiki)[8]

## Suggested Follow-Up YouTubes
Watch these for Windows 11 setups, live demos, templates (Apr 2026 priority):
- https://www.youtube.com/watch?v=1FiER-40zng (Full AI Second Brain w/ Claude Code)[9]
- https://www.youtube.com/watch?v=Q0bsphUTLtw (Claude Code 2026 Crash Course)[10]
- https://www.youtube.com/watch?v=RXuks-03Vgg (Claude Code in Obsidian 2026 Step-by-Step)[11]
- https://www.youtube.com/watch?v=9iWTRMjbBvo (Claude Code + Karpathy Self-Evolving)[12]
- https://www.youtube.com/watch?v=zVEb19AwkqM (Build Karpathy's LLM Wiki)[13]

Next: Watch cr9_A4kGzBc for install, then OSZdFnQmgRw for workflows.[2][1]
