---
title: "AGENTS.md optimization tools landscape — community skills, linters, and repos for fixing instruction files"
created: 2026-08-12
source: session-019fe3ff (/www research on AGENTS.md optimization tools)
tags: [agents-md, claude-md, context-engineering, optimization, linter, skills, tools, landscape]
summary: >
  Three community tools dominate AGENTS.md/CLAUDE.md optimization as of August 2026:
  cclint (mature TypeScript linter, 182 commits, MCP+LSP+CI), geuneda/claude-md-optimizer
  (analytical scorer with anti-pattern detection, session cost estimation, injection-order
  awareness), and wrsmith108/claude-md-optimizer (progressive disclosure with measured
  "rich abstract" pattern that eliminates sub-doc reads on focused tasks). All three use
  verbatim extraction with zero-loss validation. None have our /maintain-ifile's
  enforcement-hierarchy routing, scatter-gather parallelization, extraction log, or
  retrieval verification. The strongest borrow candidates are cclint's structural linting
  (CI-ready), geuneda's anti-pattern regexes, and wrsmith108's rich-abstract evidence.
cognitive_load: 2
verification: multi-source-verified
host: both
agent: grok
sources:
  - "geuneda/claude-md-optimizer (GitHub, Aug 2026)"
  - "felixgeelhaar/cclint (GitHub, Aug 2026, 182 commits)"
  - "wrsmith108/claude-md-optimizer (GitHub, Jun 2026)"
  - "claude-inspector (kangraemin) — MITM proxy analysis of Claude Code API traffic"
  - "HumanLayer — Writing a good CLAUDE.md (Nov 2025)"
  - "Arize — CLAUDE.md Best Practices with Prompt Learning"
relations:
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: extends
  - target: wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# AGENTS.md optimization tools landscape

## Decision context

**Why this research was needed:** our `/maintain-ifile` skill does extraction
but lacks automated scoring, anti-pattern detection, and CI-ready linting.
The operator asked what the community uses. This concept maps the landscape
and identifies borrow candidates.

## The three tools people actually use

### 1. cclint (felixgeelhaar) — the mature linter

**Repo:** [github.com/felixgeelhaar/cclint](https://github.com/felixgeelhaar/cclint)
**Maturity:** 182 commits, 980 tests, npm package, MCP server, LSP server, GitHub Action

The most production-ready tool. TypeScript, hexagonal architecture, extensible
plugin API. Lints not just CLAUDE.md but skills, subagents, hooks, MCP configs,
and plugin manifests.

**Rules cclint catches that our fleet_health doesn't:**
- Import resolution (circular deps, missing @path targets, 5-hop depth limit)
- Command safety in code blocks (rm -rf, curl|bash, fork bombs)
- Secret detection (API keys pasted into CLAUDE.md — OpenAI, Anthropic, GitHub, AWS, Google, Slack patterns)
- Skill/subagent structure validation (frontmatter, model IDs, tool names)
- Hook configuration validation (settings.json structure)
- MCP config validation (.mcp.json stdio vs remote detection)
- Plugin manifest validation (plugin.json, marketplace.json)
- Karpathy recommendations (hedging language, filler, no-example guidelines)
- Monorepo hierarchy (parent/child CLAUDE.md conflict detection)
- Content organization (heading hierarchy, vague language, emphasis markers)

**Key differentiator:** runs as MCP server (`npx @felixgeelhaar/cclint mcp`) —
the agent can lint inline before saving. Also has LSP server for real-time
editor diagnostics. SARIF output for GitHub Code Scanning.

### 2. geuneda/claude-md-optimizer — the analytical scorer

**Repo:** [github.com/geuneda/claude-md-optimizer](https://github.com/geuneda/claude-md-optimizer)
**Maturity:** 3 commits, research-backed, standalone Python analysis script

Scores CLAUDE.md 0-100 with detailed breakdown. Built on research from
Anthropic, HumanLayer, Arize, Dometrain, and claude-inspector (MITM proxy
analysis that revealed how Claude Code actually processes config).

**What geuneda measures that our /maintain-ifile doesn't:**
- **Attention placement scoring** — LLM U-shaped attention means critical content must be at top/bottom, not buried in middle
- **Session cost estimation** — per-request token cost × 30 turns = accumulated overhead
- **Injection-order awareness** — global → project → rules loading order affects what gets duplicated
- **Non-English token overhead** — CJK content uses 30-50% more tokens than equivalent English
- **Anti-pattern regex detection:**
  - Linter-territory content (code style rules belong in linters)
  - Vague directives ("follow best practices")
  - Inline code snippets over 5 lines (use file:line refs)
  - Narrative paragraphs (convert to bullets)
  - Missing essential sections (commands, prohibitions, directory structure)
  - Cross-file duplicates (same content in global + project)

**Key metric:** a 250-line CLAUDE.md costs ~1,000 tokens/request, accumulating
to ~60,000 tokens over 30 turns. Every byte compounds.

### 3. wrsmith108/claude-md-optimizer — progressive disclosure with evidence

**Repo:** [github.com/wrsmith108/claude-md-optimizer](https://github.com/wrsmith108/claude-md-optimizer)
**Maturity:** 10 commits, published as Claude Code plugin, includes evals

The most evidence-backed extraction approach. Handles all three formats
(CLAUDE.md, AGENTS.md, copilot-instructions.md) using each format's native
sub-doc mechanism.

**The "rich abstract" pattern (key finding):**

A thin link ("For testing details, see docs/testing.md") tells an agent a file
exists but not whether it's relevant. The agent follows ALL such links to be
thorough, loading every sub-doc.

A **rich abstract** (3-5 sentence synopsis with concrete facts) lets the agent
answer most questions without opening the file:

> Tests use **Vitest** (not Jest). Test files co-located with source, `.unit.spec.ts`
> suffix. Minimum **87% line coverage** enforced in CI for `src/services/`. Mock
> with `vi.mock()`. For snapshot testing and full mock patterns, see docs/testing.md.

**Measured results (from their eval):**

| Strategy | Focused task | Ambiguous task |
|----------|-------------|----------------|
| Thin inline ref | 2 files read | 5 files (all) |
| **Rich abstract + link** | **1 file (main only)** | **2 files** |

Rich abstracts **eliminated sub-doc reads entirely on focused tasks**. On
ambiguous tasks, reads dropped from 5 to 2.

**Other unique features:**
- Encryption-aware extraction (detects git-crypt/SOPS/age, places sub-docs in unencrypted paths)
- CI dependency scanning (detects scripts that regex-scan the instruction file)
- Zero-loss validation (diffs total content before/after)
- 13 progressive disclosure patterns catalogued

## Comparison with our /maintain-ifile

| Capability | cclint | geuneda | wrsmith108 | **Our /maintain-ifile** |
|-----------|--------|---------|------------|------------------------|
| Automated scoring (0-100) | No | **Yes** | No | fleet_health score (coarse) |
| Anti-pattern regex detection | Partial | **Yes** | No | No |
| Progressive disclosure extraction | No | Yes | **Yes** | Yes |
| **5-bucket classifier** (lossless/lossy with binding) | No | No | No | **Yes** |
| **Enforcement-hierarchy routing** (should this be a hook?) | No | No | No | **Yes** |
| **Scatter-gather parallelization** | No | No | No | **Yes** |
| **Retrieval verification** (does the model find extracted rules?) | No | No | No | **Yes** |
| **Extraction log** (anti-regression) | No | No | No | **Yes** |
| **Diminishing-returns stopping** | No | No | No | **Yes** |
| Session cost estimation | No | **Yes** | No | No |
| Attention placement scoring | No | **Yes** | No | No |
| Rich abstract pattern | No | No | **Yes (measured)** | Partial (pitch-style pointer) |
| CI-ready (GitHub Action, SARIF) | **Yes** | No | No | No |
| MCP server / LSP | **Yes** | No | No | No |
| Secret detection | **Yes** | No | No | No |
| Command safety validation | **Yes** | No | No | No |
| Multi-format (CLAUDE + AGENTS + copilot) | CLAUDE only | CLAUDE only | **All three** | AGENTS + CLAUDE |
| Zero-loss validation | No | Yes | **Yes** | Yes |

## What to borrow (recommendations)

**From cclint:**
- Install as CI gate for structural linting (catches missing sections, stale model IDs, dangerous commands, secrets)
- The MCP server is useful for inline linting before saves

**From geuneda:**
- Anti-pattern regexes (vague directives, linter-territory content, narrative paragraphs → bullets)
- Session cost estimation metric (tokens/request × turns)
- Attention placement scoring (critical content at top/bottom)
- Injection-order-aware duplicate detection

**From wrsmith108:**
- The "rich abstract" pattern for our pitch-style pointers (upgrade from "Before X → /concept" to 3-5 sentence synopses with concrete facts)
- Zero-loss validation (diff total content before/after)

**What they should borrow from us:**
- 5-bucket classifier with binding awareness
- Enforcement-hierarchy routing (prose → hook conversion recommendations)
- Extraction log / anti-regression detection
- Retrieval verification layer

## Key research findings (from claude-inspector MITM proxy)

claude-inspector (kangraemin) used a MITM proxy to observe how Claude Code
actually processes config:

- **Every API request** includes ALL CLAUDE.md content (~12KB overhead)
- After 30 turns, overhead exceeds 1MB (message history accumulates)
- Injection order: global CLAUDE.md → global rules → project CLAUDE.md → project rules → Memory
- Non-English content uses 30-50% more tokens
- Skills persist in context until `/clear`
- MCP tools are lazy-loaded (unused ones cost minimal tokens)
- `loading_strategy: lazy` in copilot frontmatter is **aspirational/unimplemented** as of 2026

## Falsifier

These tools are wrong if:
- The instruction-budget ceiling (~150-200) is wrong for current frontier models
- Progressive disclosure causes more latency than it saves
- cclint's structural rules are too opinionated for our workspace
- The "rich abstract" pattern doesn't generalize beyond wrsmith108's test fixtures
