<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Andre Karpathie has published work on how to use Obsidian as a cloud code wiki or memory system. Lots of people have written articles and created YouTube videos on it.  Please give me a deep research prompt I can take to Notebook.lm to create a notebook so that I can have actionable information on how to design it, implement it, and maintain it in Cloud Code on Windows 11.

**NotebookLM Prompt: Build Karpathy-Inspired Obsidian LLM Wiki for Cloud Code on Windows 11**

Create a comprehensive research notebook on implementing Andrej Karpathy's LLM Wiki pattern (raw sources → LLM-maintained wiki in Obsidian) as a code wiki/memory system using Claude Code (aka Cloud Code) on Windows 11. Use these sources: Karpathy's full GitHub Gist "LLM Wiki", detailed breakdowns like antigravity.codes guide, YouTube setups (e.g., OSZdFnQmgRw, sboNwYmH3AY, 7huCP6RkcY4), Windows-specific Claude Code installs, Obsidian-Claude integrations (plugins, Git sync).[^1_1][^1_2][^1_3][^1_4][^1_5][^1_6][^1_7][^1_8][^1_9][^1_10]

**Core Focus: Actionable Design, Implementation, Maintenance**

Extract **exact steps** tailored to Windows 11 + Claude Code + Obsidian vault (local folder). Assume user is advanced dev (Python/TS, multi-agent workflows, Claude expertise); prioritize minimal changes, reuse tools (e.g., Git for sync, Obsidian plugins like Dataview/Marp/Git).

## 1. System Design (Architecture)

- Map 3-layer stack: raw/ (immutable sources), wiki/ (LLM-edits), CLAUDE.md schema.[^1_1]
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

## 4. Maintenance \& Optimization

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
<span style="display:none">[^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27]</span>

<div align="center">⁂</div>

[^1_1]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

[^1_2]: https://www.youtube.com/watch?v=OSZdFnQmgRw

[^1_3]: https://www.youtube.com/watch?v=sboNwYmH3AY

[^1_4]: https://www.youtube.com/watch?v=7huCP6RkcY4

[^1_5]: https://marketplace.visualstudio.com/items?itemName=FinnLehmann.obsidian-code-sync

[^1_6]: https://www.youtube.com/watch?v=cr9_A4kGzBc

[^1_7]: https://publish.obsidian.md/eriktuck/guides/The+definitive+guide+to+installing+Claude+Code+on+Windows

[^1_8]: https://www.youtube.com/watch?v=Y2rpFa43jTo

[^1_9]: https://www.youtube.com/watch?v=CaHTlfHWd8U

[^1_10]: https://forum.obsidian.md/t/claude-code-from-the-sidebar/109634

[^1_11]: https://www.linkedin.com/posts/nateherkelman_andrej-karpathy-just-10xd-everyones-claude-activity-7446604578185428992-22dW

[^1_12]: https://antigravity.codes/blog/karpathy-llm-wiki-idea-file

[^1_13]: https://github.com/Obsidian-tech-wiki/obsidian_tech_wiki

[^1_14]: https://timvanoudheusden.com/guides/how-to-synchronize-obsidian-via-git-for-beginners

[^1_15]: https://www.dume.ai/blog/what-is-andrej-karpathys-llm-wiki-how-to-get-the-same-results-without-code-using-dume-cowork

[^1_16]: https://www.youtube.com/watch?v=VUnABqzrZQg

[^1_17]: https://github.com/Magic-wei/obsidian_wiki_template

[^1_18]: https://marketplace.visualstudio.com/items?itemName=willasm.obsidian-md-vsc

[^1_19]: https://www.reddit.com/r/ClaudeAI/comments/1qr19df/claude_code_obsidian_how_i_use_it_short_guide/

[^1_20]: https://www.youtube.com/watch?v=6MBq1paspVU

[^1_21]: https://www.youtube.com/watch?v=1vPJAWiFWQE

[^1_22]: https://www.youtube.com/watch?v=2kbINqpluM0

[^1_23]: https://mauriciogomes.com/teaching-claude-code-my-obsidian-vault

[^1_24]: https://forum.obsidian.md/t/automate-note-generation-in-obsidian-with-claude-desktop-and-mcp-servers/99542

[^1_25]: https://www.reddit.com/r/ObsidianMD/comments/1rz89qh/connect_obsidian_to_claude_code/

[^1_26]: https://mostlycopyandpaste.com/articles/2026/01/quick-start-using-claude-code-with-obsidian-for-ai-powered-notes/

[^1_27]: https://www.xda-developers.com/claude-code-inside-obsidian-and-it-was-eye-opening/


---

# Karpathy's Obsidian LLM wiki fully implemented — step-by-step guide + starter template

Step-by-step guide to set up Karpathy's Obsidian LLM wiki
What plugins are essential for Claude Code in Obsidian
Examples of entity pages and folder structure in the vault

Karpathy's Obsidian LLM wiki uses Claude Code (or similar agents) to maintain a structured markdown knowledge base from raw sources. Here's a Windows 11-optimized step-by-step setup, drawing from his idea file and implementations.[^2_1]

## Step-by-Step Setup

1. Install Obsidian (portable ZIP for Windows), Claude Code (`winget install Anthropic.ClaudeCode` or npm; restart PC).[^2_2][^2_1]
2. Create vault: `mkdir C:\ObsidianWiki && obsidian.exe C:\ObsidianWiki`.[^2_3]
3. Init structure via PowerShell in vault dir: `mkdir raw\articles,raw\assets,raw\papers; mkdir wiki\concepts,wiki\entities,wiki\sources,wiki\comparisons; New-Item wiki\index.md, wiki\log.md, wiki\overview.md; git init`.[^2_4][^2_1]
4. Copy Karpathy's Gist  into `CLAUDE.md` at root; customize for code wiki (e.g., entities=libs like React).[^2_1]
5. Plugins: Settings > Community > Browse/install **Obsidian Git** (auto-sync), **Dataview** (query frontmatter), **Marp** (slides), **Local Images Plus** (assets), **Terminal** or **Claude Sidebar** (embed Claude Code).[^2_5][^2_6][^2_4][^2_3]
6. `cd C:\ObsidianWiki`, run `claude`; paste: "Build LLM Wiki per CLAUDE.md for code topics".[^2_1]
7. Clip first source (Obsidian Web Clipper ext), drop to `raw/articles/`, prompt Claude: "ingest filename.md".[^2_1]
8. Git commit: `git add . && git commit -m "ingest: first"`.[^2_1]

## Starter Template

Use this as `CLAUDE.md` root file (adapt from Karpathy ):[^2_1]

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
related: page1
confidence: high|medium|low
---

## Workflows
Ingest: Read raw/, summary → wiki/sources/, update 10-15 pages, index/log.
Query: Read index → synthesize w/ links; file answers as new pages.
Lint: Contradictions, orphans, gaps.
```

Repo starters: bashiraziz/llm-wiki-template.[^2_7]

## Essential Plugins for Claude Code

- **Obsidian Git**: Auto-commit/pull vault.[^2_4]
- **Dataview**: `TABLE sources FROM "wiki"` queries.[^2_1]
- **Claude Sidebar/Terminal**: Embed `claude` in Obsidian (no API keys).[^2_8][^2_6][^2_5]
- **Local Images Plus**: Download assets for Claude vision.[^2_3]
Confidence: High (Karpathy primary ); plugins evolve fast—check Obsidian forum 2026.[^2_6][^2_4][^2_1]


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

Scales to 100+ sources via index.md.[^2_4][^2_1]

## Entity Page Examples

Entity pages track specifics (e.g., `wiki/entities/React.md`):

```
---
title: React
type: entity
sources: [raw/articles/react-19.md]
related: React-Hooks, NextJS
confidence: high
---
# React
Core UI lib by Facebook. V19 adds actions, hooks refinements.

## Key Features
- Components: Functional preferred
- State: useState, useReducer

Sources: 5 articles, 2 repos.
```

Concept: `wiki/concepts/React-Hooks.md` links entities, summaries. Next: Ingest a code article—what topic?[^2_9][^2_1]
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16]</span>

<div align="center">⁂</div>

[^2_1]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

[^2_2]: https://publish.obsidian.md/eriktuck/guides/The+definitive+guide+to+installing+Claude+Code+on+Windows

[^2_3]: https://www.youtube.com/watch?v=OSZdFnQmgRw

[^2_4]: https://antigravity.codes/blog/karpathy-llm-wiki-idea-file

[^2_5]: https://www.reddit.com/r/ObsidianMD/comments/1s4lwd6/i_integrated_claude_into_obsidian_without_using/

[^2_6]: https://forum.obsidian.md/t/claude-code-from-the-sidebar/109634

[^2_7]: https://www.linkedin.com/posts/bashiraziz_github-bashirazizllm-wiki-template-a-activity-7446747207774507008-5GHC

[^2_8]: https://www.youtube.com/watch?v=cr9_A4kGzBc

[^2_9]: https://www.youtube.com/watch?v=VUnABqzrZQg

[^2_10]: https://www.reddit.com/r/ObsidianMD/comments/1sb02pb/karpathys_workflow/

[^2_11]: https://x.com/aakashgupta/status/2040928077560348853

[^2_12]: https://antigravity.codes/blog/karpathy-llm-knowledge-bases

[^2_13]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6083618

[^2_14]: https://www.youtube.com/watch?v=VLd0K0bkOIE

[^2_15]: https://marketingagent.blog/2026/03/28/tutorial-obsidian-knowledge-base-with-claude-code/

[^2_16]: https://www.reddit.com/r/ObsidianMD/comments/12l9053/does_anyone_know_how_to_make_a_page_look_like_a/


---

# What users discover about maintaining Karpathy-style LLM wikis long-term that initial setups overlook

How to ingest raw files into the LLM wiki using Claude
Common troubleshooting issues with Claude Code in Obsidian
Best practices for maintaining the wiki over time
Examples of topics for Karpathy style LLM wikis

Long-term users of Karpathy-style LLM wikis find maintenance burdens persist despite automation, with overlooked issues like schema drift and synthesis gaps emerging after months. Ingesting raw files relies on Claude Code workflows in Obsidian vaults, while troubleshooting focuses on Windows paths and auth. Best practices emphasize periodic lints and human oversight for compounding value.[^3_1][^3_2][^3_3]

## Long-Term Discoveries

Initial setups overlook **schema evolution** (co-edit CLAUDE.md as domain changes), **decay without lints** (contradictions/orphans pile up), and **no auto-synthesis** (wiki stays factual but lacks original insights). Users report 95% token savings initially, but scale needs qmd/MCP for 1000+ pages; human review PRs for teams. Compounding requires daily health checks, not one-off ingests.[^3_4][^3_2][^3_5][^3_6][^3_1]

## Ingest Process

1. Drop raw file (clipper/MD/PDF to `raw/articles/`).[^3_7]
2. `cd vault; claude`; prompt: "ingest raw/articles/filename.md" → LLM reads, creates wiki/sources/summary.md, updates 10-15 pages (index, entities, log), cross-links.[^3_1][^3_7]
3. Verify in Obsidian, `git commit`. Batch: "ingest all new raw/".[^3_1]

## Troubleshooting Claude Code

- **Path/Exec**: Restart PC post-install; `claude config` for PATH.[^3_8][^3_9]
- **Auth**: Logout browser, incognito relogin, clear cache.[^3_9]
- **Obsidian**: Terminal plugin for `claude`; .obsidian/ paths in WSL/mnt/c.[^3_10][^3_8]
- **Git conflicts**: Obsidian Git auto-resolve or manual PRs. 90% fixed by restart/re-auth.[^3_3][^3_9]


## Maintenance Best Practices

- **Weekly Lint**: "Lint wiki: contradictions, orphans, gaps, web-fill" → append log.md.[^3_6][^3_1]
- **Git**: Auto-commit hourly, GitHub backup.[^3_3]
- **Evolve**: Refine CLAUDE.md (frontmatter fields, workflows).[^3_5][^3_3]
- **Scale**: index.md queries via Dataview; human-review updates.[^3_2][^3_1]
- **Metrics**: Track /cost, page count in overview.md.[^3_1]


## Wiki Topic Examples

- **Personal**: Goals, health logs, journal themes.[^3_3]
- **Research**: ML papers (Karpathy's 400k-word vault), code libs (React/Next.js patterns).[^3_11][^3_1]
- **Business**: Slack/meetings → project timelines, customer insights.[^3_1]
- **Hobbies**: Competitive analysis, trip planning, course notes. Code wiki: entities=frameworks (Django), concepts=patterns (CQRS).[^3_3][^3_1]
<span style="display:none">[^3_12][^3_13][^3_14][^3_15][^3_16]</span>

<div align="center">⁂</div>

[^3_1]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

[^3_2]: https://www.epsilla.com/blogs/karpathy-agentic-wiki-beyond-rag-enterprise-memory

[^3_3]: https://antigravity.codes/blog/karpathy-llm-wiki-idea-file

[^3_4]: https://www.mindstudio.ai/blog/llm-wiki-vs-rag-markdown-knowledge-base-comparison/

[^3_5]: https://extendedbrain.substack.com/p/postscript-the-wiki-that-writes-itself

[^3_6]: https://antigravity.codes/blog/karpathy-llm-knowledge-bases

[^3_7]: https://www.youtube.com/watch?v=OSZdFnQmgRw

[^3_8]: https://www.youtube.com/watch?v=cr9_A4kGzBc

[^3_9]: https://claudefa.st/blog/guide/troubleshooting

[^3_10]: https://forum.obsidian.md/t/claude-code-from-the-sidebar/109634

[^3_11]: https://deepakness.com/raw/llm-knowledge-bases/

[^3_12]: https://www.linkedin.com/posts/cole-medin-727752184_karpathys-llm-knowledge-bases-post-went-activity-7447022234956861441-1RZV

[^3_13]: https://x.com/NainsiDwiv50980/status/2040825640476348687

[^3_14]: https://github.com/ekadetov/llm-wiki

[^3_15]: https://www.instagram.com/reel/DWzAdbYAe5W/

[^3_16]: https://kenhuangus.substack.com/p/what-andrej-karpathy-got-right-how


---

# Best schema examples for Claude.md in Karpathy LLM wiki

How to set up periodic linting for wiki health checks
Integrating web searches to fill wiki data gaps

Karpathy's CLAUDE.md schema defines wiki structure, conventions, and workflows like ingest/lint for disciplined LLM maintenance. Periodic linting uses scheduled Claude prompts via Obsidian plugins or GitHub Actions, while web integration leverages Claude's tools for gap-filling. Examples and setups are from primary implementations.[^4_1][^4_2]

## Best CLAUDE.md Schemas

Karpathy's core, adapted for code wiki:[^4_1]

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
related: Entity1, Concept2
confidence: high|medium|low
updated: YYYY-MM-DD
---

## Workflows
### Ingest raw/articles/filename.md
1. Read file.
2. Extract: summary → wiki/sources/filename.md; entities/concepts → new/update pages (10-15).
3. Cross-link links.
4. Update index.md/log.md.

### Query "compare React Vue"
File wiki/comparisons/react-vs-vue.md; link from index.

### Lint
Health-check: contradictions, orphans (no inbound), gaps (web-fill?), stale.
```

Enhanced variants add flashcards/gaps.[^4_3][^4_2]

## Periodic Linting Setup

- **Manual**: `claude` → "Run lint per CLAUDE.md" → LLM scans, updates log.md.[^4_1]
- **Automated**: Obsidian Git + Templater plugin (cron-like via Tasks); or GitHub Actions: weekly `claude lint` via SSH.[^4_2]
- Prompt: "Lint wiki: contradictions (e.g., React hooks stale?), orphans, gaps (search web?), missing pages/cross-refs".[^4_4][^4_1]
- Track: Dataview `LIST FROM "wiki" WHERE confidence="low"`. Run post-ingest for health.[^4_2]


## Web Search Integration

- **In Lint/Ingest**: Schema instructs: "Gaps? Use web_search tool: 'latest React 19 docs'" → ingest results.[^4_1]
- **Claude Code**: Native `/web` or tools; prompt: "Fill gap on X: search, summarize, integrate".[^4_5]
- **qmd CLI**: Local search + web rerank for scale. Best: Limit to authoritative sources (official docs > blogs); verify confidence. Next step: Adapt schema to your domain (e.g., AI tools)—what focus?[^4_4][^4_2][^4_1]
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

[^4_2]: https://antigravity.codes/blog/karpathy-llm-wiki-idea-file

[^4_3]: https://www.reddit.com/r/ClaudeAI/comments/1sde8y3/a_schema_standard_for_llmcompiled_personal/

[^4_4]: https://www.youtube.com/watch?v=zVEb19AwkqM

[^4_5]: https://www.youtube.com/watch?v=VUnABqzrZQg

[^4_6]: https://www.reddit.com/r/ClaudeCode/comments/1scidpz/built_a_claude_code_plugin_that_turns_your/

[^4_7]: https://www.reddit.com/r/claude/comments/1sdea78/a_schema_standard_for_llmcompiled_personal/

[^4_8]: https://mcpmarket.com/tools/skills/code-quality-linting-config

[^4_9]: https://docs.litellm.ai/docs/proxy/health

[^4_10]: https://news.ycombinator.com/item?id=47640875

[^4_11]: https://www.reddit.com/r/ObsidianMD/comments/1on433j/how_i_automated_my_obsidian_workflow_with_claude/

[^4_12]: https://shipyard.build/blog/claude-code-getting-started/

[^4_13]: https://globaladvisors.biz/2026/04/06/term-llm-wiki-andrej-karpathy/

[^4_14]: https://www.youtube.com/watch?v=RQsLXmenr48

[^4_15]: https://github.com/Astro-Han/karpathy-llm-wiki


---

# Obsidian plugins for Karpathy LLM wiki

CLI tools like npx for automating wiki compilation

Obsidian plugins enable Claude Code integration and wiki management for Karpathy-style LLM wikis. CLI tools like npx automate compilation via agent wrappers, complementing manual Claude sessions.[^5_1][^5_2]

## Key Obsidian Plugins

- **Obsidian Git**: Auto-commit/pull vault changes post-LLM edits.[^5_1]
- **Dataview**: Query index.md (e.g., `LIST FROM "wiki" WHERE confidence="low"`), graph views for orphans/hubs.[^5_2][^5_1]
- **Marp**: LLM-generated slide decks from wiki pages.[^5_1]
- **Terminal** (by polyipseity): Run `claude` inside Obsidian for seamless edits.[^5_3][^5_4]
- **Local API**: Expose vault to Claude Code for search/frontmatter access (generate API key).[^5_3]
- **Obsidian Skills** or **Wikilink Types**: Agent-native wikilinks, YAML relations.[^5_5][^5_6]
Confidence: High—Karpathy explicitly uses Dataview/Marp/Git; others from 2026 Claude-Obsidian guides.[^5_3][^5_1]


## CLI Automation Tools

- **Claude Code (`claude`)**: Core—`npx @anthropic-ai/claude-code` (if npm); `claude ingest raw/file.md` or lint.[^5_7]
- **qmd**: `npx qmd mcp` starts MCP server for wiki search/indexing at scale (>100 pages).[^5_2]
- **cw (CodeWiki CLI)**: `npx cw init` scaffolds repo wiki; `cw index` rebuilds _index.md; `cw setup claude-code` installs skills.[^5_8]
- **llm-kb**: `npx llm-kb run ./raw` indexes to wiki via Pi SDK sessions.[^5_9]
Setup: In vault dir, `npm i -g` tools; define slash commands in `.claude/commands/` for Obsidian automation. Next step: Install Terminal + Local API, test `claude lint`.[^5_10][^5_8][^5_2][^5_3]
<span style="display:none">[^5_11][^5_12][^5_13][^5_14][^5_15]</span>

<div align="center">⁂</div>

[^5_1]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

[^5_2]: https://antigravity.codes/blog/karpathy-llm-wiki-idea-file

[^5_3]: https://www.reddit.com/r/ClaudeAI/comments/1qr19df/claude_code_obsidian_how_i_use_it_short_guide/

[^5_4]: https://www.eleanorkonik.com/p/claude-obsidian-got-a-level-up

[^5_5]: https://www.reddit.com/r/ObsidianMD/comments/1sb02pb/karpathys_workflow/

[^5_6]: https://antigravity.codes/blog/karpathy-llm-knowledge-bases

[^5_7]: https://www.youtube.com/watch?v=6MBq1paspVU

[^5_8]: https://muhammadraza.me/2026/building-codewiki-compiling-codebases-into-living-wikis/

[^5_9]: https://www.linkedin.com/posts/satish1v_karpathy-wants-llm-knowledge-bases-drop-activity-7446253320886910976-K3EA

[^5_10]: https://www.reddit.com/r/ObsidianMD/comments/1on433j/how_i_automated_my_obsidian_workflow_with_claude/

[^5_11]: https://x.com/karpathy/status/2039805659525644595

[^5_12]: https://www.youtube.com/watch?v=VLd0K0bkOIE

[^5_13]: https://www.youtube.com/watch?v=zVEb19AwkqM

[^5_14]: https://academy.dair.ai/blog/llm-knowledge-bases-karpathy

[^5_15]: https://x.com/i/trending/2039841987067617664


---

# How to setup Local API plugin for LLM editing in Obsidian

Wikilink Types plugin tutorial for Karpathy wiki
npx llm-kb CLI full setup and usage guide
Notemd plugin features for auto-linking in Obsidian
Best practices for separate vaults in Karpathy LLM workflow

Obsidian plugins like Local REST API enable LLM editing via HTTP endpoints, while Wikilink Types and NoteMD enhance Karpathy wiki linking. npx llm-knowledge-bases provides CLI automation; separate vaults prevent contamination.[^6_1][^6_2][^6_3]

## Local REST API Setup

1. Obsidian > Settings > Community Plugins > Browse > "Local REST API" (by Adam Coddington) > Install/Enable.[^6_2][^6_1]
2. Settings > Local REST API > Generate API key (copy).[^6_1]
3. For Claude Code: Add to `.claude/config.json` or MCP skill: `{"api_key": "your_key", "base_url": "http://localhost:27123"}`.[^6_4][^6_5]
4. Test: `curl -H "x-api-key: your_key" http://localhost:27123/health` → LLM prompts use vault read/write/search.[^6_2][^6_1]

## Wikilink Types Tutorial

1. BRAT (Beta Reviewer App) or community install: `penfieldlabs/obsidian-wikilink-types`.[^6_6][^6_7]
2. Settings > Wikilink Types > Configure types (e.g., @supports, @contradicts, @extends for wiki relations).[^6_6]
3. Usage: `React@supports` → auto YAML frontmatter `relations: {supports: [React]}`; bidirectional sync.[^6_7]
4. Karpathy fit: Typed links in index.md (e.g., React-Hooks@implements); Dataview queries on relations.[^6_6]

## npx llm-kb Guide

`llm-knowledge-bases` CLI for wiki runtime.[^6_3]

**Setup:**

```
npx llm-knowledge-bases init --vault-root /path/to/vault
# Configures MCP/CLI for Claude Code
```

**Usage:**

- `npx llm-knowledge-bases kb_status --vault-root ./vault` : Health/index.
- `npx llm-knowledge-bases kb_list_raw --vault-root ./vault --changed-only` : New files.
- `npx llm-knowledge-bases kb_read_raw --vault-root ./vault --raw-path raw/notes/file.md` : Ingest prep.
- `npx llm-knowledge-bases kb_prepare_source ...` : Process to wiki/.[^6_3]
Integrate: `claude` → "Use llm-kb MCP for vault".[^6_3]


## NoteMD Features

- AI chunking/processing (OpenAI/Anthropic/Ollama): Bulk docs → wiki-links, concept notes.[^6_8]
- Auto-linking: Context-aware inserts links during summarization.[^6_8]
- Web search (Tavily): Gap-fill summaries.
- Dupe detection, Mermaid/LaTeX fix, retry logic.
Karpathy use: Process raw/ → auto-links in wiki/sources/.[^6_8]


## Separate Vaults Practices

- **Clean (personal)**: Human-curated, high S/N; no LLM writes.[^6_9]
- **Messy (wiki)**: LLM-compiled (raw/, wiki/); link via external embeds or symlinks.[^6_9]
- Switch: File > Open vault > Manage vaults.
- Best: Git separate repos; Dataview cross-vault queries (plugins); prevents RAG contamination. Next: Domain for vault (code/AI)?[^6_10][^6_9][^6_1][^6_2][^6_3]
<span style="display:none">[^6_11][^6_12][^6_13][^6_14][^6_15][^6_16][^6_17][^6_18][^6_19][^6_20][^6_21][^6_22][^6_23][^6_24][^6_25][^6_26][^6_27][^6_28][^6_29]</span>

<div align="center">⁂</div>

[^6_1]: https://www.reddit.com/r/ClaudeAI/comments/1qr19df/claude_code_obsidian_how_i_use_it_short_guide/

[^6_2]: https://mostlycopyandpaste.com/articles/2026/01/quick-start-using-claude-code-with-obsidian-for-ai-powered-notes/

[^6_3]: https://clawhub.ai/plugins/llm-knowledge-bases-plugin

[^6_4]: https://forum.obsidian.md/t/claude-mcp-for-obsidian-using-rest-api/93284

[^6_5]: https://zazencodes.substack.com/p/obsidian-mcp-setup-tutorial-for-claude

[^6_6]: https://www.reddit.com/r/ObsidianMD/comments/1ryd5v8/wikilink_types_type_inside_a_wikilink_to_add/

[^6_7]: https://forum.obsidian.md/t/wikilink-types-type-inside-a-wikilink-to-add-relationship-types-auto-synced-to-yaml-frontmatter/112470

[^6_8]: https://www.obsidianstats.com/plugins/notemd

[^6_9]: https://antigravity.codes/blog/karpathy-llm-knowledge-bases

[^6_10]: https://antigravity.codes/blog/karpathy-llm-wiki-idea-file

[^6_11]: https://www.youtube.com/watch?v=a1FDaoF8Jog

[^6_12]: https://www.reddit.com/r/ObsidianMD/comments/1s2elej/is_there_a_free_way_to_connect_an_llm_to_obsidian/

[^6_13]: https://github.com/manimohans/obsidian-local-llm-helper/blob/main/CLAUDE.md

[^6_14]: https://www.youtube.com/watch?v=a0k8wh69PjM

[^6_15]: https://www.youtube.com/watch?v=cr9_A4kGzBc

[^6_16]: https://notes.nicolevanderhoeven.com/obsidian-playbook/Using+Obsidian/03+Linking+and+organizing/Links

[^6_17]: https://github.com/ConardLi/easy-llm-cli/blob/main/README.md

[^6_18]: https://forum.obsidian.md/t/autolink-automatically-creates-backlinks-to-and-from-notes-with-easy-customizability/104090

[^6_19]: https://www.youtube.com/watch?v=hOaSO_e7MYs

[^6_20]: https://kubently.io/guides/quick-start/

[^6_21]: https://www.obsidianstats.com/plugins/auto-definition-link

[^6_22]: https://www.youtube.com/watch?v=sboNwYmH3AY

[^6_23]: https://www.youtube.com/watch?v=mZ8TJ59Hj28

[^6_24]: https://github.com/hancengiz/cc-obsidian-vault-api-skill

[^6_25]: https://www.youtube.com/watch?v=Y2rpFa43jTo

[^6_26]: https://www.notecompanion.ai/blog/key-features-to-consider-in-an-ai-note-taking-plugin-for-obsidian

[^6_27]: https://www.reddit.com/r/AI_Agents/comments/1p2z9th/cli_llm_obsidian_unlimited_context_and_ease_of/

[^6_28]: https://www.youtube.com/watch?v=_PiRCPnQmgk

[^6_29]: https://obsidian.md/plugins


---

# What are the repos that I should put in my notebook LM Regarding this ClotCode Obsidian solution.

**Core Repos for NotebookLM on Claude Code (Cloud Code) + Obsidian LLM Wiki**

Upload these GitHub repos/gists to NotebookLM for deep analysis, templates, and Claude-specific integrations. Prioritizes 2026 Karpathy implementations over generics.[^7_1][^7_2][^7_3]


| Repo/Gist | Description | Why Essential |
| :-- | :-- | :-- |
| [karpathy/LLM Wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) [^7_1] | Schema (CLAUDE.md), workflows (ingest/lint), folder structure (raw/wiki) | Canonical idea file—paste to Claude for bootstrap. |
| [heyitsnoah/claudesidian](https://github.com/heyitsnoah/claudesidian) [^7_3] | Pre-configured Obsidian vault + Claude Code starter (PARA, Git, CLAUDE.md) | Turnkey setup; auto-imports existing vaults. |
| [iansinnott/obsidian-claude-code-mcp](https://github.com/iansinnott/obsidian-claude-code-mcp) [^7_4] | MCP plugin for Claude Code/ Desktop vault access (read/write/search) | Enables LLM editing via WebSocket/HTTP; auto-discovery. |
| [rohitg00/LLM Wiki v2 Gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) [^7_5] | Karpathy extension w/ agentmemory patterns | Advanced scaling, persistent memory. |
| [manimohans/obsidian-local-llm-helper](https://github.com/manimohans/obsidian-local-llm-helper) [^7_6] | Local LLM helper + CLAUDE.md for Obsidian | Text processing, chat; Claude-compatible. |
| [hancengiz/cc-obsidian-vault-api-skill](https://github.com/hancengiz/cc-obsidian-vault-api-skill) [^7_7] | Claude Code skill for vault API | Direct LLM vault interaction. |
| [Magic-wei/obsidian_wiki_template](https://github.com/Magic-wei/obsidian_wiki_template) [^7_8] | Basic wiki template (plugins/config) | Foundation for custom CLAUDE.md. |

**NotebookLM Instructions:** Analyze for Windows 11 Claude Code setup, extract schemas/scripts, generate vault scaffold. Fork/clone for testing. Confidence: High (direct Karpathy/Claude hits); check dates for 2026 updates. Next step: Upload Gist first.[^7_3][^7_4][^7_1]
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_16][^7_17][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

[^7_2]: https://antigravity.codes/blog/karpathy-llm-wiki-idea-file

[^7_3]: https://github.com/heyitsnoah/claudesidian

[^7_4]: https://github.com/iansinnott/obsidian-claude-code-mcp

[^7_5]: https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2

[^7_6]: https://github.com/manimohans/obsidian-local-llm-helper/blob/main/CLAUDE.md

[^7_7]: https://github.com/hancengiz/cc-obsidian-vault-api-skill

[^7_8]: https://github.com/Magic-wei/obsidian_wiki_template

[^7_9]: https://x.com/daniel_mac8/status/2040753754148921359

[^7_10]: https://www.reddit.com/r/LocalLLaMA/comments/1sclfs6/llm_wiki_by_karpathy/

[^7_11]: https://louiswang524.github.io/blog/llm-knowledge-base/

[^7_12]: https://www.obsidianstats.com/plugins/local-llm-helper

[^7_13]: https://app.daily.dev/posts/the-llm-wiki-github-gist-shared-by-andrej-karpathy-outlines-a-pattern-for-building-personal-know-dx4n0eg9d

[^7_14]: https://www.youtube.com/watch?v=Y2rpFa43jTo

[^7_15]: https://github.com/hannesdelbeke/wiki_template

[^7_16]: https://awesomeclaude.ai/how-to/use-obsidian-with-claude

[^7_17]: https://github.com/hardbyte/obsidian-llm-plugin/blob/main/main.ts


---

# Differences between claudesidian and Karpathy LLM Wiki

Best raw sources to index in Claude Code Obsidian

ClaudeSidian is a pre-configured Obsidian vault repo inspired by Karpathy's LLM wiki pattern, optimized for Claude Code. Raw sources should be high-signal, immutable clips for effective wiki compilation.[^8_1][^8_2][^8_3]

## Key Differences

| Aspect | Karpathy LLM Wiki | ClaudeSidian |
| :-- | :-- | :-- |
| **Nature** | Conceptual idea file (Gist); raw pattern/schema [^8_2] | Repo/template vault; ready-to-clone Obsidian + Claude Code setup [^8_3] |
| **Structure** | 3 layers: raw/ (immutable), wiki/ (LLM-owned), CLAUDE.md schema [^8_2][^8_1] | PARA method + Git; auto-imports vaults, personalized CLAUDE.md [^8_3] |
| **Automation** | Manual Claude prompts (ingest/lint) [^8_2] | Scripts for deps/Git; Gemini Vision/Firecrawl optional [^8_3] |
| **Scale** | 400k words, Obsidian IDE view [^8_4] | Mobile sync, existing vault migration [^8_3] |
| **Focus** | General knowledge compounding (no RAG) [^8_1] | AI thinking partner w/ version control [^8_3] |

ClaudeSidian implements/extends Karpathy for ease—clone it for Claude Code.[^8_2][^8_3]

## Best Raw Sources

- **Articles/Clips**: Web Clipper MD (news, blogs); download images to raw/assets/.[^8_5][^8_1]
- **Papers**: ArXiv/PDFs (OCR if needed via Claude Vision).[^8_2]
- **Code/Repos**: GitHub READMEs, issues, code snippets; zip to raw/repos/.[^8_6]
- **Personal**: Slack exports, meeting notes, journal MD.[^8_2]
- **Media**: Images/videos (Vision ingest), data CSVs.[^8_5]
Prioritize **curated, high-S/N** (5-50 pages/week); immutable—LLM extracts to wiki/. Avoid noise; verify sources in lint.[^8_4][^8_1][^8_2]
<span style="display:none">[^8_10][^8_11][^8_12][^8_13][^8_14][^8_15][^8_7][^8_8][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://antigravity.codes/blog/karpathy-llm-wiki-idea-file

[^8_2]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

[^8_3]: https://github.com/heyitsnoah/claudesidian

[^8_4]: https://www.youtube.com/watch?v=VUnABqzrZQg

[^8_5]: https://www.youtube.com/watch?v=OSZdFnQmgRw

[^8_6]: https://muhammadraza.me/2026/building-codewiki-compiling-codebases-into-living-wikis/

[^8_7]: https://www.reddit.com/r/ObsidianMD/comments/1sb02pb/karpathys_workflow/

[^8_8]: https://www.youtube.com/watch?v=yvReDHs4Ze4

[^8_9]: https://www.reddit.com/r/Rag/comments/1sdcv73/karpathy_said_there_is_room_for_an_incredible_new/

[^8_10]: https://www.youtube.com/watch?v=_iENSAKA63k

[^8_11]: https://kenhuangus.substack.com/p/what-andrej-karpathy-got-right-how

[^8_12]: https://www.youtube.com/watch?v=6MBq1paspVU

[^8_13]: https://x.com/JeremyNguyenPhD/status/2039816181696373047

[^8_14]: https://x.com/kloss_xyz/status/2040546099711401993

[^8_15]: https://github.com/YishenTu/claudian

