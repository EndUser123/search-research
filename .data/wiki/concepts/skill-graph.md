---
title: "Skill dependency graph: who calls what and who consumes which providers"
created: 2026-08-04
source: auto-generated
generator: P:/.data/wiki/scripts/build_skill_graph.py
tags: [skill-graph, dependencies, providers, delegation, blast-radius, maintenance, reference]
summary: >
  Auto-generated dependency graph of all workspace skills. Three edge
  types: delegates_to (skill calls skill), consumes_provider (skill uses
  MCP/CLI tool), references_wiki (skill cites wiki concept). Use for
  blast-radius analysis when a provider changes status. Rebuild:
  python P:/.data/wiki/scripts/build_skill_graph.py
agent: grok
host: grok
cognitive_load: 2
verification: auto-generated
---

# Skill dependency graph

> **Auto-generated** from SKILL.md files. Edges are lexical (extracted
> from text patterns), not semantic — false positives are cheap to dismiss.
> Rebuild after skill changes: `python P:/.data/wiki/scripts/build_skill_graph.py`

## How to use this

**Blast-radius analysis:** when a provider changes status (disabled, broken,
migrated), look it up in the "Provider consumers" table. Every skill listed
references that provider and may need updating.

**Delegation tracing:** when a skill changes behavior, look it up in the
"Delegation targets" table. Every caller depends on it and may need review.

## Provider consumers (who uses what)

When a provider is disabled/broken/migrated, these skills need updates:

| Provider | Consumer count | Skills |
|----------|---------------|--------|
| `agy` | 8 | `agy`, `ai-cli`, `codex`, `mmx`, `model-benchmark`, `search-fleet`, `tasks`, `tp` |
| `brave` | 2 | `go`, `web` |
| `chrome-devtools` | 2 | `chrome-devtools-cli`, `model-web` |
| `chrome-devtools-mcp-tools` | 1 | `model-web` |
| `codex` | 8 | `codex`, `mmx`, `model-benchmark`, `resume-codex`, `review`, `tasks`, `tp`, `wargame` |
| `coding-model-pool` | 2 | `go`, `review` |
| `context7` | 1 | `context7` |
| `critic-model-pool` | 3 | `aar`, `review`, `tp` |
| `ddg` | 5 | `go`, `search-fleet`, `tp`, `web`, `www` |
| `duckduckgo` | 1 | `web` |
| `episodic-memory` | 2 | `dream`, `remembering-conversations` |
| `exa` | 27 | `aar`, `agy`, `codex`, `create-skill`, `design`, `dream`, `go`, `grok-parallel`, `grok-verify`, `handoff`, `imagine`, `mmx`, `model-benchmark`, `model-quota`, `notice`, `plan-writer`, `prompt-patterns`, `refactor`, `refine`, `review`, `search-fleet`, `skill-dev`, `tasks`, `todo`, `web`, `wiki`, `wiki-crawl4ai` |
| `firecrawl` | 17 | `design`, `firecrawl-agent`, `firecrawl-cli`, `firecrawl-crawl`, `firecrawl-download`, `firecrawl-interact`, `firecrawl-map`, `firecrawl-monitor`, `firecrawl-parse`, `firecrawl-scrape`, `firecrawl-search`, `model-quota`, `search-fleet`, `tp`, `web`, `wiki-crawl4ai`, `www` |
| `gh` | 29 | `aar`, `agy`, `codex`, `design`, `dream`, `go`, `grok-discovery`, `grok-parallel`, `grok-safe-git`, `grok-verify`, `handoff`, `imagine`, `maintain`, `mmx`, `model-benchmark`, `notice`, `plan-writer`, `prompt-patterns`, `refactor`, `refine`, `review`, `search-fleet`, `skill-dev`, `tasks`, `todo`, `wargame`, `wiki`, `wiki-crawl4ai`, `www` |
| `github-issues` | 1 | `www` |
| `hn-algolia` | 2 | `web`, `www` |
| `mechanical-model-pool` | 4 | `handoff`, `harvest`, `refine`, `www` |
| `minimax-search` | 1 | `design` |
| `mmx` | 11 | `design`, `minimax-multimodal-toolkit`, `minimax-music-gen`, `minimax-music-playlist`, `mmx`, `model-benchmark`, `model-quota`, `search-fleet`, `web`, `wiki-yt`, `www` |
| `nlm` | 6 | `aar`, `gitingest`, `go`, `nlm`, `nlm-to-wiki`, `refactor` |
| `notebooklm` | 5 | `nlm`, `todo`, `web`, `wiki-yt`, `yt-nlm` |
| `pending-suggestions` | 1 | `harvest` |
| `perplexity` | 3 | `model-web`, `search-fleet`, `web` |
| `pwm` | 2 | `perplexity-web-mcp`, `search-fleet` |
| `reasoning-model-pool` | 3 | `aar`, `tp`, `why` |
| `reddit` | 4 | `search-fleet`, `todo`, `web`, `www` |
| `ruff` | 1 | `doc-check` |
| `search-research` | 4 | `prospect`, `search-fleet`, `web`, `why` |
| `serper` | 1 | `web` |
| `spawn-subagent` | 2 | `tp`, `why` |
| `stackexchange` | 1 | `web` |
| `tavily` | 3 | `model-quota`, `search-fleet`, `web` |

## Delegation targets (who calls this skill)

When a skill changes its interface or behavior, these callers are affected:

| Target skill | Caller count | Called by |
|-------------|-------------|-----------|
| `aar` | 16 | `capture`, `close`, `dream`, `friction`, `handoff`, `harvest`, `model-web`, `notice`, `packet`, `recap-grok`, `red-team`, `skill-dev`, `slc`, `tp`, `wargame`, `why` |
| `agy` | 7 | `check`, `codex`, `mmx`, `model-web`, `search-fleet`, `tp`, `why` |
| `capture` | 1 | `close` |
| `check` | 18 | `aar`, `ask`, `close`, `doc-check`, `doc-compiler`, `dream`, `go`, `grok-verify`, `model-benchmark`, `refactor`, `refine`, `review`, `ship`, `skill-dev`, `skill-to-page`, `todo`, `tp`, `www` |
| `chrome-devtools-mcp` | 1 | `model-web` |
| `close` | 15 | `aar`, `ask`, `capture`, `check`, `dream`, `handoff`, `harvest`, `maintain`, `recap-grok`, `review`, `ship`, `skill-dev`, `todo`, `tp`, `wiki` |
| `codex` | 4 | `mmx`, `model-web`, `tp`, `why` |
| `crawl4ai` | 1 | `wiki-crawl4ai` |
| `create-skill` | 1 | `skill-dev` |
| `debrief` | 21 | `aar`, `agy`, `behave`, `claude-audit`, `close`, `codex`, `dream`, `export-session`, `friction`, `handoff`, `harvest`, `improve`, `lmc`, `mlc`, `recap`, `recap-grok`, `red-team`, `retro`, `skill-audit`, `top-problems`, `tp` |
| `design` | 24 | `ask`, `behave`, `close`, `code`, `discover`, `domain-terms`, `dream`, `evolve`, `execute-plan`, `go`, `grill-me`, `handoff`, `plan-writer`, `planning`, `prompt_refiner`, `recap`, `refine`, `s`, `specify`, `tp`, `wargame`, `web`, `why`, `www` |
| `diagnosing-bugs` | 1 | `ask-matt` |
| `domain-terms` | 1 | `grill-me` |
| `fmea` | 1 | `skill-dev` |
| `friction` | 1 | `capture` |
| `go` | 25 | `aar`, `ask`, `check`, `close`, `code`, `design`, `doc-check`, `grill-me`, `grok-go`, `grok-parallel`, `grok-sdlc`, `handoff`, `model-benchmark`, `notice`, `plan-writer`, `refactor`, `refine`, `research`, `review`, `rns`, `todo`, `tp`, `wargame`, `why`, `www` |
| `grill-me` | 2 | `ask-matt`, `domain-terms` |
| `grok-discovery` | 2 | `go`, `grok-parallel` |
| `grok-parallel` | 2 | `go`, `notice` |
| `grok-route` | 3 | `go`, `grok-parallel`, `grok-verify` |
| `grok-safe-git` | 4 | `go`, `grok-parallel`, `grok-verify`, `ship` |
| `grok-verify` | 5 | `go`, `grok-parallel`, `ship`, `skill-dev`, `tp` |
| `handoff` | 27 | `aar`, `ask`, `ask-matt`, `behave`, `capture`, `close`, `design`, `dream`, `friction`, `go`, `harvest`, `maintain`, `model-web`, `notice`, `packet`, `plan-writer`, `prompt-patterns`, `recap`, `recap-grok`, `red-team`, `refactor`, `refine`, `ship`, `skill-dev`, `tp`, `why`, `wiki` |
| `improve-codebase-architecture` | 3 | `ask-matt`, `check`, `diagnosing-bugs` |
| `maintain` | 2 | `model-quota`, `skill-dev` |
| `mmx` | 8 | `minimax-multimodal-toolkit`, `minimax-music-gen`, `model-quota`, `model-web`, `tp`, `web`, `why`, `wiki-yt` |
| `model-benchmark` | 1 | `model-discover` |
| `notice` | 4 | `close`, `skill-dev`, `slc`, `tp` |
| `packet` | 1 | `tp` |
| `plan-writer` | 5 | `design`, `domain-terms`, `go`, `grill-me`, `refine` |
| `preflight` | 2 | `design`, `tp` |
| `recover` | 5 | `config-audit`, `main`, `maintain`, `skill-prune`, `workspace-health` |
| `red-team` | 19 | `aar`, `behave`, `claude-audit`, `close`, `debrief`, `dream`, `fmea`, `improve`, `model-web`, `notice`, `pre-mortem`, `preflight`, `retro`, `review`, `risks`, `skill-audit`, `tp`, `why`, `www` |
| `refine` | 9 | `aar`, `design`, `domain-terms`, `dream`, `go`, `grill-me`, `handoff`, `plan-writer`, `refactor` |
| `review` | 27 | `aar`, `ask`, `behave`, `check`, `claude-audit`, `close`, `debrief`, `doc-check`, `domain-terms`, `dream`, `go`, `improve`, `learn`, `marketplace-bridge`, `model-benchmark`, `red-team`, `refactor`, `refine`, `review-pr`, `risks`, `ship`, `skill-audit`, `skill-dev`, `sqd`, `todo`, `tp`, `uci` |
| `skill-dev` | 4 | `close`, `create-skill`, `red-team`, `tp` |
| `skill-prune` | 6 | `config-audit`, `create-skill`, `maintain`, `skill-dev`, `wiki`, `workspace-health` |
| `tasks` | 1 | `capture` |
| `tdd` | 9 | `ask-matt`, `evolve`, `go`, `implement`, `planning`, `ralph`, `skill-similarity`, `subagent-driven-development`, `t` |
| `teach` | 1 | `ask-matt` |
| `to-spec` | 1 | `ask-matt` |
| `to-tickets` | 1 | `ask-matt` |
| `todo` | 12 | `ask`, `capture`, `close`, `design`, `email-skill`, `harvest`, `model-quota`, `recap-grok`, `ship`, `tp`, `wiki`, `www` |
| `tp` | 26 | `aar`, `ask`, `behave`, `capture`, `close`, `design`, `domain-terms`, `dream`, `fmea`, `go`, `handoff`, `harvest`, `model-benchmark`, `model-web`, `notice`, `plan-writer`, `recap-grok`, `red-team`, `refactor`, `refine`, `review`, `skill-dev`, `slc`, `todo`, `why`, `www` |
| `triage` | 2 | `ask-matt`, `setup-matt-pocock-skills` |
| `wargame` | 2 | `plan-writer`, `red-team` |
| `wayfinder` | 1 | `ask-matt` |
| `web` | 7 | `find`, `keep`, `note`, `tp`, `why`, `wiki-crawl4ai`, `www` |
| `why` | 15 | `aar`, `ask`, `behave`, `dream`, `harvest`, `model-benchmark`, `model-web`, `notice`, `red-team`, `review`, `skill-dev`, `todo`, `tp`, `wargame`, `www` |
| `wiki` | 36 | `aar`, `capture`, `claude-audit`, `close`, `crawl`, `create-skill`, `debrief`, `design`, `domain-terms`, `dream`, `go`, `grok-safe-git`, `handoff`, `improve`, `main`, `maintain`, `model-benchmark`, `nlm-to-wiki`, `notice`, `plan-writer`, `prompt-patterns`, `recap-grok`, `refactor`, `refine`, `review`, `ship`, `skill-dev`, `todo`, `tp`, `ux`, `wargame`, `web`, `why`, `wiki-crawl4ai`, `wiki-yt`, `www` |
| `wiki-crawl4ai` | 1 | `www` |
| `writing-great-skills` | 1 | `ask-matt` |

## Capability registry (what functions the fleet provides)

Every capability the skill fleet declares via `provides:` frontmatter:

| Capability | Provided by |
|------------|-------------|
| `after-action-review` | `aar` |
| `behavioral-reset` | `slc` |
| `broken-link-detection` | `doc-check` |
| `browser-llm-bridge` | `model-web` |
| `capability-routed-search` | `search-fleet` |
| `capture-coverage-check` | `capture` |
| `changelog-validation` | `doc-check` |
| `code-fence-validation` | `doc-check` |
| `code-review` | `review` |
| `completion-gate` | `grok-verify` |
| `content-discipline-for-plans` | `wargame` |
| `content-production` | `write` |
| `conversation-selection` | `model-web` |
| `cost-tracking` | `model-benchmark` |
| `critical-friend-critique` | `tp` |
| `cross-model-second-opinion` | `agy`, `codex`, `mmx` |
| `cross-session-pattern-detection` | `harvest` |
| `decision-tree-elicitation` | `grill-me` |
| `design-doc-production` | `design` |
| `discovery-dispatch` | `go` |
| `documentation-readiness-check` | `doc-check` |
| `domain-term-extraction` | `domain-terms` |
| `engineering-orchestration` | `go` |
| `evidence-backed-inventory` | `preflight` |
| `failure-modes-analysis` | `fmea` |
| `feedback-to-wiki` | `why` |
| `file-pack` | `packet` |
| `file-recovery` | `recover` |
| `fleet-maintenance` | `maintain` |
| `friction-detection` | `friction` |
| `fusion-portal-orchestration` | `model-web` |
| `gate-resolution` | `close` |
| `gemini-reasoning` | `agy` |
| `git-safety-preflight` | `grok-safe-git` |
| `grok-documentation-help` | `help` |
| `handoff-auto-update` | `handoff` |
| `handoff-write` | `handoff` |
| `image-generation-guidance` | `imagine` |
| `improvement-opportunity-scan` | `capture` |
| `knowledge-hygiene` | `skill-prune` |
| `latency-benchmark` | `model-benchmark` |
| `logic-error-detection` | `trace` |
| `manual-trace-verification` | `trace` |
| `marketplace-skill-discovery` | `marketplace-bridge` |
| `mid-conversation-observation-surfacing` | `notice` |
| `minimax-vision` | `mmx` |
| `minimax-web-search` | `mmx` |
| `model-discovery` | `model-discover` |
| `model-web-advisory` | `model-web` |
| `multi-backend-search` | `web` |
| `multi-model-ensemble` | `model-web` |
| `obligation-lifecycle` | `harvest` |
| `offline-memory-consolidation` | `dream` |
| `openai-reasoning` | `codex` |
| `opportunity-landscape` | `aar` |
| `package-routing` | `grok-route` |
| `parallel-fan-out` | `grok-parallel` |
| `parallel-implement-dispatch` | `go` |
| `pattern-library-query` | `why` |
| `persistent-task-store` | `tasks` |
| `plan-writing` | `plan-writer` |
| `proactive-knowledge-capture` | `capture` |
| `prompting-techniques-reference` | `prompt-patterns` |
| `quality-scoring` | `model-benchmark` |
| `quota-dashboard` | `model-quota` |
| `readme-staleness-detection` | `doc-check` |
| `repo-file-completeness` | `doc-check` |
| `requirements-elicitation` | `grill-me` |
| `risk-priority-scoring` | `fmea` |
| `root-cause-analysis` | `why` |
| `rrf-aggregation` | `search-fleet` |
| `rrf-merge` | `web` |
| `safe-git-preflight-dispatch` | `go` |
| `session-chain-walk` | `recap-grok` |
| `session-close-accounting` | `close` |
| `session-export` | `packet` |
| `session-opportunity-review` | `tp` |
| `session-recap-grok` | `recap-grok` |
| `session-retrospective` | `aar` |
| `session-verification` | `check` |
| `ship-pipeline` | `ship` |
| `skill-frontmatter-validation` | `doc-check` |
| `skill-improvement` | `skill-dev` |
| `skill-measurement` | `skill-dev` |
| `skill-routing` | `ask` |
| `skill-scaffolding` | `create-skill` |
| `source-authority-discovery` | `grok-discovery` |
| `sse-response-capture` | `model-web` |
| `structural-refactor` | `refactor` |
| `subagent-dispatch` | `check`, `grok-parallel`, `review`, `tp`, `www` |
| `system-exploration` | `tp` |
| `systematic-debugging` | `diagnosing-bugs` |
| `task-refinement` | `refine` |
| `thought-partner-realignment` | `slc` |
| `value-accounting` | `aar` |
| `value-tracking` | `harvest` |
| `verified-findings-on-disk` | `review` |
| `verify-and-publish` | `ship` |
| `verify-dispatch` | `go` |
| `web-ingestion` | `wiki-crawl4ai` |
| `wiki-query` | `wiki` |
| `wiki-web-wiki-research` | `www` |
| `wiki-write` | `wiki` |
| `wikilink-resolution` | `doc-check` |
| `workflow-automation-analysis` | `friction` |
| `workspace-prioritized-action-list` | `todo` |

## Shared services (used by 3+ skills)

Infrastructure that many skills depend on — capabilities and tools with
high consumer counts. Changes to these have fleet-wide blast radius.

| Service | Type | Consumer count | Skills |
|---------|------|---------------|--------|
| `cross-model-second-opinion` | capability | 3 | `agy`, `codex`, `mmx` |
| `subagent-dispatch` | capability | 5 | `check`, `grok-parallel`, `review`, `tp`, `www` |
| `agy` | tool | 8 | `agy`, `ai-cli`, `codex`, `mmx`, `model-benchmark`, `search-fleet`, `tasks`, `tp` |
| `codex` | tool | 8 | `codex`, `mmx`, `model-benchmark`, `resume-codex`, `review`, `tasks`, `tp`, `wargame` |
| `ddg` | tool | 5 | `go`, `search-fleet`, `tp`, `web`, `www` |
| `exa` | tool | 27 | `aar`, `agy`, `codex`, `create-skill`, `design`, `dream`, `go`, `grok-parallel`... |
| `firecrawl` | tool | 17 | `design`, `firecrawl-agent`, `firecrawl-cli`, `firecrawl-crawl`, `firecrawl-download`, `firecrawl-interact`, `firecrawl-map`, `firecrawl-monitor`... |
| `gh` | tool | 29 | `aar`, `agy`, `codex`, `design`, `dream`, `go`, `grok-discovery`, `grok-parallel`... |
| `mmx` | tool | 11 | `design`, `minimax-multimodal-toolkit`, `minimax-music-gen`, `minimax-music-playlist`, `mmx`, `model-benchmark`, `model-quota`, `search-fleet`... |
| `nlm` | tool | 6 | `aar`, `gitingest`, `go`, `nlm`, `nlm-to-wiki`, `refactor` |
| `notebooklm` | tool | 5 | `nlm`, `todo`, `web`, `wiki-yt`, `yt-nlm` |

## Capabilities by domain

### alignment

| Capability | Skills |
|------------|--------|
| `decision-tree-elicitation` | `grill-me` |
| `requirements-elicitation` | `grill-me` |

### browser-automation

| Capability | Skills |
|------------|--------|
| `browser-llm-bridge` | `model-web` |
| `conversation-selection` | `model-web` |
| `fusion-portal-orchestration` | `model-web` |
| `model-web-advisory` | `model-web` |
| `multi-model-ensemble` | `model-web` |
| `sse-response-capture` | `model-web` |

### content

| Capability | Skills |
|------------|--------|
| `content-production` | `write` |

### cross-model

| Capability | Skills |
|------------|--------|
| `cross-model-second-opinion` | `agy`, `codex`, `mmx` |
| `gemini-reasoning` | `agy` |
| `minimax-vision` | `mmx` |
| `minimax-web-search` | `mmx` |
| `openai-reasoning` | `codex` |

### design

| Capability | Skills |
|------------|--------|
| `design-doc-production` | `design` |
| `plan-writing` | `plan-writer` |

### discovery

| Capability | Skills |
|------------|--------|
| `capability-routed-search` | `search-fleet` |
| `evidence-backed-inventory` | `preflight` |
| `marketplace-skill-discovery` | `marketplace-bridge` |
| `model-discovery` | `model-discover` |
| `multi-backend-search` | `web` |
| `rrf-aggregation` | `search-fleet` |
| `rrf-merge` | `web` |
| `skill-routing` | `ask` |
| `source-authority-discovery` | `grok-discovery` |
| `task-refinement` | `refine` |
| `web-ingestion` | `wiki-crawl4ai` |
| `wiki-web-wiki-research` | `www` |

### fleet-ops

| Capability | Skills |
|------------|--------|
| `cost-tracking` | `model-benchmark` |
| `file-recovery` | `recover` |
| `grok-documentation-help` | `help` |
| `latency-benchmark` | `model-benchmark` |
| `persistent-task-store` | `tasks` |
| `quality-scoring` | `model-benchmark` |
| `workspace-prioritized-action-list` | `todo` |

### implementation

| Capability | Skills |
|------------|--------|
| `image-generation-guidance` | `imagine` |
| `structural-refactor` | `refactor` |

### infrastructure

| Capability | Skills |
|------------|--------|
| `parallel-fan-out` | `grok-parallel` |
| `subagent-dispatch` | `check`, `grok-parallel`, `review`, `tp`, `www` |

### knowledge

| Capability | Skills |
|------------|--------|
| `domain-term-extraction` | `domain-terms` |
| `feedback-to-wiki` | `why` |
| `pattern-library-query` | `why` |
| `prompting-techniques-reference` | `prompt-patterns` |
| `wiki-query` | `wiki` |
| `wiki-write` | `wiki` |

### lifecycle

| Capability | Skills |
|------------|--------|
| `after-action-review` | `aar` |
| `behavioral-reset` | `slc` |
| `capture-coverage-check` | `capture` |
| `file-pack` | `packet` |
| `friction-detection` | `friction` |
| `gate-resolution` | `close` |
| `handoff-auto-update` | `handoff` |
| `handoff-write` | `handoff` |
| `improvement-opportunity-scan` | `capture` |
| `logic-error-detection` | `trace` |
| `manual-trace-verification` | `trace` |
| `mid-conversation-observation-surfacing` | `notice` |
| `opportunity-landscape` | `aar` |
| `proactive-knowledge-capture` | `capture` |
| `root-cause-analysis` | `why` |
| `session-chain-walk` | `recap-grok` |
| `session-close-accounting` | `close` |
| `session-export` | `packet` |
| `session-recap-grok` | `recap-grok` |
| `session-retrospective` | `aar` |
| `thought-partner-realignment` | `slc` |
| `value-accounting` | `aar` |
| `workflow-automation-analysis` | `friction` |

### monitoring

| Capability | Skills |
|------------|--------|
| `quota-dashboard` | `model-quota` |

### orchestration

| Capability | Skills |
|------------|--------|
| `discovery-dispatch` | `go` |
| `engineering-orchestration` | `go` |
| `git-safety-preflight` | `grok-safe-git` |
| `package-routing` | `grok-route` |
| `parallel-implement-dispatch` | `go` |
| `safe-git-preflight-dispatch` | `go` |
| `ship-pipeline` | `ship` |
| `verify-and-publish` | `ship` |
| `verify-dispatch` | `go` |

### review

| Capability | Skills |
|------------|--------|
| `code-review` | `review` |
| `content-discipline-for-plans` | `wargame` |
| `critical-friend-critique` | `tp` |
| `failure-modes-analysis` | `fmea` |
| `risk-priority-scoring` | `fmea` |
| `session-opportunity-review` | `tp` |
| `system-exploration` | `tp` |
| `verified-findings-on-disk` | `review` |

### self-improvement

| Capability | Skills |
|------------|--------|
| `cross-session-pattern-detection` | `harvest` |
| `fleet-maintenance` | `maintain` |
| `knowledge-hygiene` | `skill-prune` |
| `obligation-lifecycle` | `harvest` |
| `offline-memory-consolidation` | `dream` |
| `skill-improvement` | `skill-dev` |
| `skill-measurement` | `skill-dev` |
| `skill-scaffolding` | `create-skill` |
| `value-tracking` | `harvest` |

### testing

| Capability | Skills |
|------------|--------|
| `completion-gate` | `grok-verify` |
| `session-verification` | `check` |

### uncategorized

| Capability | Skills |
|------------|--------|
| `systematic-debugging` | `diagnosing-bugs` |

### verify

| Capability | Skills |
|------------|--------|
| `broken-link-detection` | `doc-check` |
| `changelog-validation` | `doc-check` |
| `code-fence-validation` | `doc-check` |
| `documentation-readiness-check` | `doc-check` |
| `readme-staleness-detection` | `doc-check` |
| `repo-file-completeness` | `doc-check` |
| `skill-frontmatter-validation` | `doc-check` |
| `wikilink-resolution` | `doc-check` |


## Per-skill edges

| Skill | Delegates to | Consumes provider | Provides |
|-------|-------------|------------------|
| `a11y-debugging` | — | — | — |
| `aar` | `check`, `close`, `debrief`, `go`, `handoff`, `red-team`, `refine`, `review`, `tp`, `why`, `wiki` | `critic-model-pool`, `exa`, `gh`, `nlm`, `reasoning-model-pool` | `after-action-review`, `opportunity-landscape`, `session-retrospective`, `value-accounting` |
| `adr` | — | — | — |
| `agy` | `debrief` | `agy`, `exa`, `gh` | `cross-model-second-opinion`, `gemini-reasoning` |
| `agy` | — | — | — |
| `ai-api` | — | — | — |
| `ai-cli` | — | `agy` | — |
| `ai-models` | — | — | — |
| `ai-probe-benchmark` | — | — | — |
| `ai-probe-nim` | — | — | — |
| `ai-probe-openrouter` | — | — | — |
| `ai-probe-router` | — | — | — |
| `aid` | — | — | — |
| `all` | — | — | — |
| `ask` | `check`, `close`, `go`, `handoff`, `review`, `todo`, `tp`, `why` | — | `skill-routing` |
| `ask` | `design` | — | — |
| `ask-matt` | `diagnosing-bugs`, `grill-me`, `handoff`, `improve-codebase-architecture`, `tdd`, `teach`, `to-spec`, `to-tickets`, `triage`, `wayfinder`, `writing-great-skills` | — | — |
| `av` | — | — | — |
| `avant-garde-ui` | — | — | — |
| `batch-grill-me` | — | — | — |
| `behave` | `debrief`, `design`, `handoff`, `red-team`, `review`, `tp`, `why` | — | — |
| `behave` | `debrief` | — | — |
| `bf` | — | — | — |
| `bifrost` | — | — | — |
| `brainstorming` | — | — | — |
| `brainstorming` | — | — | — |
| `browsing` | — | — | — |
| `build` | — | — | — |
| `build-with-ai` | — | — | — |
| `capture` | `aar`, `close`, `friction`, `handoff`, `tasks`, `todo`, `tp`, `wiki` | — | `capture-coverage-check`, `improvement-opportunity-scan`, `proactive-knowledge-capture` |
| `capture` | — | — | — |
| `case-feedback-skill` | — | — | — |
| `cc-model-router` | — | — | — |
| `changelog` | — | — | — |
| `check` | `agy`, `close`, `go`, `review` | — | `session-verification`, `subagent-dispatch` |
| `check` | `go`, `improve-codebase-architecture` | — | — |
| `chrome-devtools` | — | — | — |
| `chrome-devtools-cli` | — | `chrome-devtools` | — |
| `chs` | — | — | — |
| `chs-eval` | — | — | — |
| `cks` | — | — | — |
| `claude-audit` | `debrief`, `red-team`, `review`, `wiki` | — | — |
| `claude-handoff` | — | — | — |
| `close` | `aar`, `capture`, `check`, `debrief`, `design`, `go`, `handoff`, `notice`, `red-team`, `review`, `skill-dev`, `todo`, `tp`, `wiki` | — | `gate-resolution`, `session-close-accounting` |
| `code` | `design`, `go` | — | — |
| `code-flow-visualizer` | — | — | — |
| `code-review` | — | — | — |
| `code-review` | — | — | — |
| `code-review` | — | — | — |
| `codebase-design` | — | — | — |
| `codebase-to-course` | — | — | — |
| `codex` | `agy`, `debrief` | `agy`, `codex`, `exa`, `gh` | `cross-model-second-opinion`, `openai-reasoning` |
| `codex` | — | `codex` | — |
| `concept-mapper` | — | — | — |
| `config-audit` | `recover`, `skill-prune` | — | — |
| `constitutional-patterns` | — | — | — |
| `constraints` | — | — | — |
| `context7` | — | `context7` | — |
| `contract-status` | — | — | — |
| `crawl` | `wiki` | — | — |
| `create-skill` | `skill-dev`, `skill-prune`, `wiki` | `exa` | `skill-scaffolding` |
| `create-skill` | — | — | — |
| `create-workflow` | — | — | — |
| `csf-nip-integration` | — | — | — |
| `debrief` | `red-team`, `review`, `wiki` | — | — |
| `debt` | — | — | — |
| `debug-optimize-lcp` | — | — | — |
| `decision-tree` | — | — | — |
| `design` | `go`, `handoff`, `plan-writer`, `preflight`, `refine`, `todo`, `tp`, `wiki` | `exa`, `firecrawl`, `gh`, `mmx` | `design-doc-production` |
| `design` | `preflight` | `minimax-search` | — |
| `design` | `go` | — | — |
| `design-an-interface` | — | — | — |
| `design-codebase` | — | — | — |
| `design-frontend` | — | — | — |
| `diagnose` | — | — | — |
| `diagnosing-bugs` | `improve-codebase-architecture` | — | `systematic-debugging` |
| `diagnosing-bugs` | `improve-codebase-architecture` | — | — |
| `discover` | `design` | — | — |
| `dispatching-parallel-agents` | — | — | — |
| `dispatching-parallel-agents` | — | — | — |
| `doc-check` | `check`, `go`, `review` | `ruff` | `broken-link-detection`, `changelog-validation`, `code-fence-validation`, `documentation-readiness-check`, `readme-staleness-detection`, `repo-file-completeness`, `skill-frontmatter-validation`, `wikilink-resolution` |
| `doc-compiler` | `check` | — | — |
| `docs` | — | — | — |
| `docx` | — | — | — |
| `domain-modeling` | — | — | — |
| `domain-terms` | `design`, `grill-me`, `plan-writer`, `refine`, `review`, `tp`, `wiki` | — | `domain-term-extraction` |
| `dream` | `aar`, `check`, `close`, `debrief`, `design`, `handoff`, `red-team`, `refine`, `review`, `tp`, `why`, `wiki` | `episodic-memory`, `exa`, `gh` | `offline-memory-consolidation` |
| `dream` | — | — | — |
| `edit-article` | — | — | — |
| `email-skill` | `todo` | — | — |
| `epistemic-check` | — | — | — |
| `evidence-driven-experiment-loop` | — | — | — |
| `evolve` | `design`, `tdd` | — | — |
| `execute-plan` | `design` | — | — |
| `executing-plans` | — | — | — |
| `execution-clarity` | — | — | — |
| `export-session` | `debrief` | — | — |
| `find` | `web` | — | — |
| `finishing-a-development-branch` | — | — | — |
| `finishing-a-development-branch` | — | — | — |
| `firecrawl-agent` | — | `firecrawl` | — |
| `firecrawl-cli` | — | `firecrawl` | — |
| `firecrawl-crawl` | — | `firecrawl` | — |
| `firecrawl-download` | — | `firecrawl` | — |
| `firecrawl-interact` | — | `firecrawl` | — |
| `firecrawl-map` | — | `firecrawl` | — |
| `firecrawl-monitor` | — | `firecrawl` | — |
| `firecrawl-parse` | — | `firecrawl` | — |
| `firecrawl-scrape` | — | `firecrawl` | — |
| `firecrawl-search` | — | `firecrawl` | — |
| `fmea` | `red-team`, `tp` | — | `failure-modes-analysis`, `risk-priority-scoring` |
| `friction` | `aar`, `debrief`, `handoff` | — | `friction-detection`, `workflow-automation-analysis` |
| `friction` | `debrief` | — | — |
| `frontend-dev` | — | — | — |
| `fullstack-dev` | — | — | — |
| `game-animation-frames` | — | — | — |
| `game-asset-core` | — | — | — |
| `game-character-consistency` | — | — | — |
| `game-tilesets` | — | — | — |
| `game-ui-icons` | — | — | — |
| `garden` | — | — | — |
| `genius` | — | — | — |
| `git` | — | — | — |
| `git-guardrails-claude-code` | — | — | — |
| `gitingest` | — | `nlm` | — |
| `gitpack` | — | — | — |
| `gitready` | — | — | — |
| `go` | `check`, `design`, `grok-discovery`, `grok-parallel`, `grok-route`, `grok-safe-git`, `grok-verify`, `handoff`, `plan-writer`, `refine`, `review`, `tp`, `wiki` | `brave`, `coding-model-pool`, `ddg`, `exa`, `gh`, `nlm` | `discovery-dispatch`, `engineering-orchestration`, `parallel-implement-dispatch`, `safe-git-preflight-dispatch`, `verify-dispatch` |
| `go` | `design`, `tdd` | — | — |
| `google-ai-usage-monitor` | — | — | — |
| `grill-me` | `design`, `domain-terms`, `go`, `plan-writer`, `refine` | — | `decision-tree-elicitation`, `requirements-elicitation` |
| `grill-me` | — | — | — |
| `grill-with-docs` | — | — | — |
| `grilling` | — | — | — |
| `grok-discovery` | — | `gh` | `source-authority-discovery` |
| `grok-go` | `go` | — | — |
| `grok-parallel` | `go`, `grok-discovery`, `grok-route`, `grok-safe-git`, `grok-verify` | `exa`, `gh` | `parallel-fan-out`, `subagent-dispatch` |
| `grok-route` | — | — | `package-routing` |
| `grok-safe-git` | `wiki` | `gh` | `git-safety-preflight` |
| `grok-sdlc` | `go` | — | — |
| `grok-verify` | `check`, `grok-route`, `grok-safe-git` | `exa`, `gh` | `completion-gate` |
| `handoff` | `aar`, `close`, `debrief`, `design`, `go`, `refine`, `tp`, `wiki` | `exa`, `gh`, `mechanical-model-pool` | `handoff-auto-update`, `handoff-write` |
| `handoff` | — | — | — |
| `harvest` | `aar`, `close`, `debrief`, `handoff`, `todo`, `tp`, `why` | `mechanical-model-pool`, `pending-suggestions` | `cross-session-pattern-detection`, `obligation-lifecycle`, `value-tracking` |
| `help` | — | — | `grok-documentation-help` |
| `id` | — | — | — |
| `imagine` | — | `exa`, `gh` | `image-generation-guidance` |
| `imagine` | — | — | — |
| `implement` | — | — | — |
| `implement` | `tdd` | — | — |
| `improve` | `debrief`, `red-team`, `review`, `wiki` | — | — |
| `improve-codebase-architecture` | — | — | — |
| `improve-codebase-architecture` | — | — | — |
| `improve-codebase-architecture` | — | — | — |
| `index` | — | — | — |
| `init` | — | — | — |
| `intelligence-stream-analyze` | — | — | — |
| `intelligence-stream-ingest` | — | — | — |
| `keep` | `web` | — | — |
| `learn` | `review` | — | — |
| `lmc` | `debrief` | — | — |
| `loop-me` | — | — | — |
| `main` | `recover`, `wiki` | — | — |
| `main-review` | — | — | — |
| `maintain` | `close`, `handoff`, `recover`, `skill-prune`, `wiki` | `gh` | `fleet-maintenance` |
| `marketplace-bridge` | `review` | — | `marketplace-skill-discovery` |
| `memory-leak-debugging` | — | — | — |
| `mermaid-c4` | — | — | — |
| `migrate-to-shoehorn` | — | — | — |
| `minimax-multimodal-toolkit` | `mmx` | `mmx` | — |
| `minimax-music-gen` | `mmx` | `mmx` | — |
| `minimax-music-playlist` | — | `mmx` | — |
| `mlc` | `debrief` | — | — |
| `mm-quota` | — | — | — |
| `mmx` | `agy`, `codex` | `agy`, `codex`, `exa`, `gh`, `mmx` | `cross-model-second-opinion`, `minimax-vision`, `minimax-web-search` |
| `model-benchmark` | `check`, `go`, `review`, `tp`, `why`, `wiki` | `agy`, `codex`, `exa`, `gh`, `mmx` | `cost-tracking`, `latency-benchmark`, `quality-scoring` |
| `model-discover` | `model-benchmark` | — | `model-discovery` |
| `model-quota` | `maintain`, `mmx`, `todo` | `exa`, `firecrawl`, `mmx`, `tavily` | `quota-dashboard` |
| `model-web` | `aar`, `agy`, `chrome-devtools-mcp`, `codex`, `handoff`, `mmx`, `red-team`, `tp`, `why` | `chrome-devtools`, `chrome-devtools-mcp-tools`, `perplexity` | `browser-llm-bridge`, `conversation-selection`, `fusion-portal-orchestration`, `model-web-advisory`, `multi-model-ensemble`, `sse-response-capture` |
| `nlm` | — | `nlm`, `notebooklm` | — |
| `nlm-bulk-ingest` | — | — | — |
| `nlm-to-wiki` | `wiki` | `nlm` | — |
| `note` | `web` | — | — |
| `notebooklm` | — | — | — |
| `notice` | `aar`, `go`, `grok-parallel`, `handoff`, `red-team`, `tp`, `why`, `wiki` | `exa`, `gh` | `mid-conversation-observation-surfacing` |
| `obsidian-vault` | — | — | — |
| `pace` | — | — | — |
| `packet` | `aar`, `handoff` | — | `file-pack`, `session-export` |
| `pdf` | — | — | — |
| `perf` | — | — | — |
| `performance-profiler` | — | — | — |
| `perplexity-web-mcp` | — | `pwm` | — |
| `plan-writer` | `design`, `go`, `handoff`, `refine`, `tp`, `wargame`, `wiki` | `exa`, `gh` | `plan-writing` |
| `planning` | `design`, `tdd` | — | — |
| `plugin-installer` | — | — | — |
| `pptx` | — | — | — |
| `pr-babysit` | — | — | — |
| `pre-mortem` | `red-team` | — | — |
| `preflight` | `red-team` | — | `evidence-backed-inventory` |
| `preflight` | — | — | — |
| `prime` | — | — | — |
| `probe` | — | — | — |
| `profile` | — | — | — |
| `prompt-enhancer` | — | — | — |
| `prompt-patterns` | `handoff`, `wiki` | `exa`, `gh` | `prompting-techniques-reference` |
| `prompt_refiner` | `design` | — | — |
| `prospect` | — | `search-research` | — |
| `prototype` | — | — | — |
| `qa` | — | — | — |
| `qmd-wiki` | — | — | — |
| `quota` | — | — | — |
| `ralph` | `tdd` | — | — |
| `rca` | — | — | — |
| `reason` | — | — | — |
| `recap` | `debrief`, `design`, `handoff` | — | — |
| `recap-grok` | `aar`, `close`, `debrief`, `handoff`, `todo`, `tp`, `wiki` | — | `session-chain-walk`, `session-recap-grok` |
| `receiving-code-review` | — | — | — |
| `recover` | — | — | `file-recovery` |
| `recover` | — | — | — |
| `red-team` | `aar`, `debrief`, `handoff`, `review`, `skill-dev`, `tp`, `wargame`, `why` | — | — |
| `refactor` | `check`, `go`, `handoff`, `refine`, `review`, `tp`, `wiki` | `exa`, `gh`, `nlm` | `structural-refactor` |
| `refactor` | — | — | — |
| `refine` | `check`, `design`, `go`, `handoff`, `plan-writer`, `review`, `tp`, `wiki` | `exa`, `gh`, `mechanical-model-pool` | `task-refinement` |
| `reflect` | — | — | — |
| `remembering-conversations` | — | `episodic-memory` | — |
| `repomix` | — | — | — |
| `request-refactor-plan` | — | — | — |
| `requesting-code-review` | — | — | — |
| `research` | — | — | — |
| `research` | — | — | — |
| `research` | `go` | — | — |
| `resolving-merge-conflicts` | — | — | — |
| `response-atomicity` | — | — | — |
| `resume-claude` | — | — | — |
| `resume-codex` | — | `codex` | — |
| `resume-cursor` | — | — | — |
| `retro` | `debrief`, `red-team` | — | — |
| `review` | `check`, `close`, `go`, `red-team`, `tp`, `why`, `wiki` | `codex`, `coding-model-pool`, `critic-model-pool`, `exa`, `gh` | `code-review`, `subagent-dispatch`, `verified-findings-on-disk` |
| `review` | — | — | — |
| `review` | `red-team` | — | — |
| `review-pr` | `review` | — | — |
| `review_bundle` | — | — | — |
| `risks` | `red-team`, `review` | — | — |
| `rns` | `go` | — | — |
| `s` | `design` | — | — |
| `scaffold-exercises` | — | — | — |
| `search-fleet` | `agy` | `agy`, `ddg`, `exa`, `firecrawl`, `gh`, `mmx`, `perplexity`, `pwm`, `reddit`, `search-research`, `tavily` | `capability-routed-search`, `rrf-aggregation` |
| `sequential-thinking` | — | — | — |
| `setup-matt-pocock-skills` | `triage` | — | — |
| `setup-pre-commit` | — | — | — |
| `setup-ts-deep-modules` | — | — | — |
| `ship` | `check`, `close`, `grok-safe-git`, `grok-verify`, `handoff`, `review`, `todo`, `wiki` | — | `ship-pipeline`, `verify-and-publish` |
| `ship` | — | — | — |
| `simplify-enhanced` | — | — | — |
| `skeptic` | — | — | — |
| `skill-audit` | `debrief`, `red-team`, `review` | — | — |
| `skill-dev` | `aar`, `check`, `close`, `create-skill`, `fmea`, `grok-verify`, `handoff`, `maintain`, `notice`, `review`, `skill-prune`, `tp`, `why`, `wiki` | `exa`, `gh` | `skill-improvement`, `skill-measurement` |
| `skill-from-docs` | — | — | — |
| `skill-prune` | `recover` | — | `knowledge-hygiene` |
| `skill-similarity` | `tdd` | — | — |
| `skill-to-page` | `check` | — | — |
| `skill-write` | — | — | — |
| `slc` | `aar`, `notice`, `tp` | — | `behavioral-reset`, `thought-partner-realignment` |
| `slc` | — | — | — |
| `snapshot` | — | — | — |
| `solo-dev-authority` | — | — | — |
| `specify` | `design` | — | — |
| `sqa` | — | — | — |
| `sqd` | `review` | — | — |
| `stale` | — | — | — |
| `subagent-driven-development` | — | — | — |
| `subagent-driven-development` | `tdd` | — | — |
| `systematic-debugging` | — | — | — |
| `t` | `tdd` | — | — |
| `task` | — | — | — |
| `tasks` | — | `agy`, `codex`, `exa`, `gh` | `persistent-task-store` |
| `tdd` | — | — | — |
| `tdd` | — | — | — |
| `tdd` | — | — | — |
| `teach` | — | — | — |
| `teach` | — | — | — |
| `team` | — | — | — |
| `test-driven-development` | — | — | — |
| `tilldone` | — | — | — |
| `tldr-code` | — | — | — |
| `tldr-deep` | — | — | — |
| `tldr-overview` | — | — | — |
| `tldr-router` | — | — | — |
| `tldr-stats` | — | — | — |
| `to-questionnaire` | — | — | — |
| `to-spec` | — | — | — |
| `to-spec` | — | — | — |
| `to-tickets` | — | — | — |
| `to-tickets` | — | — | — |
| `todo` | `check`, `close`, `go`, `review`, `tp`, `why`, `wiki` | `exa`, `gh`, `notebooklm`, `reddit` | `workspace-prioritized-action-list` |
| `top-problems` | `debrief` | — | — |
| `tot` | — | — | — |
| `tp` | `aar`, `agy`, `check`, `close`, `codex`, `debrief`, `design`, `go`, `grok-verify`, `handoff`, `mmx`, `notice`, `packet`, `preflight`, `red-team`, `review`, `skill-dev`, `todo`, `web`, `why`, `wiki` | `agy`, `codex`, `critic-model-pool`, `ddg`, `firecrawl`, `reasoning-model-pool`, `spawn-subagent` | `critical-friend-critique`, `session-opportunity-review`, `subagent-dispatch`, `system-exploration` |
| `trace` | — | — | `logic-error-detection`, `manual-trace-verification` |
| `trace` | — | — | — |
| `triage` | — | — | — |
| `triage` | — | — | — |
| `troubleshooting` | — | — | — |
| `truth` | — | — | — |
| `ubiquitous-language` | — | — | — |
| `uci` | `review` | — | — |
| `usage-query-skill` | — | — | — |
| `usage-query-skill` | — | — | — |
| `using-git-worktrees` | — | — | — |
| `using-git-worktrees` | — | — | — |
| `using-superpowers` | — | — | — |
| `using-superpowers` | — | — | — |
| `usm` | — | — | — |
| `ut` | — | — | — |
| `ux` | `wiki` | — | — |
| `verification-before-completion` | — | — | — |
| `verification-before-completion` | — | — | — |
| `video-vision` | — | — | — |
| `vision-analysis` | — | — | — |
| `wargame` | `aar`, `design`, `go`, `why`, `wiki` | `codex`, `gh` | `content-discipline-for-plans` |
| `wayfinder` | — | — | — |
| `wayfinder` | — | — | — |
| `web` | `design`, `mmx`, `wiki` | `brave`, `ddg`, `duckduckgo`, `exa`, `firecrawl`, `hn-algolia`, `mmx`, `perplexity`, `reddit`, `search-research`, `stackexchange`, `tavily` | `multi-backend-search`, `rrf-merge` |
| `web` | — | `notebooklm`, `serper` | — |
| `why` | `aar`, `agy`, `codex`, `design`, `go`, `handoff`, `mmx`, `red-team`, `tp`, `web`, `wiki` | `reasoning-model-pool`, `spawn-subagent` | `feedback-to-wiki`, `pattern-library-query`, `root-cause-analysis` |
| `why` | — | `search-research` | — |
| `wiki` | `close`, `handoff`, `skill-prune`, `todo` | `exa`, `gh` | `wiki-query`, `wiki-write` |
| `wiki` | — | — | — |
| `wiki-crawl4ai` | `crawl4ai`, `web`, `wiki` | `exa`, `firecrawl`, `gh` | `web-ingestion` |
| `wiki-yt` | `mmx`, `wiki` | `mmx`, `notebooklm` | — |
| `wizard` | — | — | — |
| `wizard` | — | — | — |
| `workspace-health` | `recover`, `skill-prune` | — | — |
| `write` | — | — | `content-production` |
| `writing-beats` | — | — | — |
| `writing-fragments` | — | — | — |
| `writing-great-skills` | — | — | — |
| `writing-great-skills` | — | — | — |
| `writing-plans` | — | — | — |
| `writing-shape` | — | — | — |
| `writing-skills` | — | — | — |
| `writing-skills` | — | — | — |
| `www` | `check`, `design`, `go`, `red-team`, `todo`, `tp`, `web`, `why`, `wiki`, `wiki-crawl4ai` | `ddg`, `firecrawl`, `gh`, `github-issues`, `hn-algolia`, `mechanical-model-pool`, `mmx`, `reddit` | `subagent-dispatch`, `wiki-web-wiki-research` |
| `yt-is` | — | — | — |
| `yt-nlm` | — | `notebooklm` | — |
| `yt-selenium` | — | — | — |
| `zoom-out` | — | — | — |

## Machine-readable graph

```json
{
  "nodes": [
    {
      "name": "aar",
      "path": "C:\\Users\\brsth\\.grok\\skills\\aar\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "debrief",
        "go",
        "handoff",
        "red-team",
        "refine",
        "review",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "critic-model-pool",
        "exa",
        "gh",
        "nlm",
        "reasoning-model-pool"
      ],
      "references_wiki": [
        "friction-detection-operator-pushback-as-trigger",
        "parallel-subagent-wait-all-gate",
        "tool-fallbacks",
        "user-modeling-for-agentic-clis"
      ],
      "provides": [
        "after-action-review",
        "opportunity-landscape",
        "session-retrospective",
        "value-accounting"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "agy",
      "path": "C:\\Users\\brsth\\.grok\\skills\\agy\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "debrief"
      ],
      "consumes_provider": [
        "agy",
        "exa",
        "gh"
      ],
      "references_wiki": [],
      "provides": [
        "cross-model-second-opinion",
        "gemini-reasoning"
      ],
      "domain": "cross-model"
    },
    {
      "name": "ask",
      "path": "C:\\Users\\brsth\\.grok\\skills\\ask\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "go",
        "handoff",
        "review",
        "todo",
        "tp",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "signal-based-intent-expansion",
        "skill-catalog",
        "skill-graph"
      ],
      "provides": [
        "skill-routing"
      ],
      "domain": "discovery"
    },
    {
      "name": "behave",
      "path": "C:\\Users\\brsth\\.grok\\skills\\behave\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "debrief",
        "design",
        "handoff",
        "red-team",
        "review",
        "tp",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "governance-pattern-library"
      ],
      "provides": [],
      "domain": "lifecycle"
    },
    {
      "name": "capture",
      "path": "C:\\Users\\brsth\\.grok\\skills\\capture\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "close",
        "friction",
        "handoff",
        "tasks",
        "todo",
        "tp",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "plausible-narratives-substitute-for-verification",
        "proactive-improvement-opportunity-scanner"
      ],
      "provides": [
        "capture-coverage-check",
        "improvement-opportunity-scan",
        "proactive-knowledge-capture"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "close",
      "path": "C:\\Users\\brsth\\.grok\\skills\\close\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "capture",
        "check",
        "debrief",
        "design",
        "go",
        "handoff",
        "notice",
        "red-team",
        "review",
        "skill-dev",
        "todo",
        "tp",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "agentic-sdlc-skill-lifecycle-architecture",
        "prompting-patterns-for-ai-agent-control",
        "signal-based-intent-expansion"
      ],
      "provides": [
        "gate-resolution",
        "session-close-accounting"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "codex",
      "path": "C:\\Users\\brsth\\.grok\\skills\\codex\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "agy",
        "debrief"
      ],
      "consumes_provider": [
        "agy",
        "codex",
        "exa",
        "gh"
      ],
      "references_wiki": [],
      "provides": [
        "cross-model-second-opinion",
        "openai-reasoning"
      ],
      "domain": "cross-model"
    },
    {
      "name": "create-skill",
      "path": "C:\\Users\\brsth\\.grok\\skills\\create-skill\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "skill-dev",
        "skill-prune",
        "wiki"
      ],
      "consumes_provider": [
        "exa"
      ],
      "references_wiki": [],
      "provides": [
        "skill-scaffolding"
      ],
      "domain": "self-improvement"
    },
    {
      "name": "design",
      "path": "C:\\Users\\brsth\\.grok\\skills\\design\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "go",
        "handoff",
        "plan-writer",
        "preflight",
        "refine",
        "todo",
        "tp",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "firecrawl",
        "gh",
        "mmx"
      ],
      "references_wiki": [
        "adr-0009-extend-unverified-stance",
        "agentic-sdlc-skill-lifecycle-architecture",
        "concept-slug",
        "consistency-drift-as-waste-source-in-iterative-refinement",
        "exemption-logic-as-conflict-signal",
        "llm-synthesis-quality-and-speed-techniques",
        "raising-coding-best-practices-in-ai-agents",
        "tool-fallbacks"
      ],
      "provides": [
        "design-doc-production"
      ],
      "domain": "design"
    },
    {
      "name": "design-codebase",
      "path": "C:\\Users\\brsth\\.grok\\skills\\design-codebase\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "design-frontend",
      "path": "C:\\Users\\brsth\\.grok\\skills\\design-frontend\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "diagnosing-bugs",
      "path": "C:\\Users\\brsth\\.grok\\skills\\diagnosing-bugs\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "improve-codebase-architecture"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "systematic-debugging"
      ],
      "domain": ""
    },
    {
      "name": "doc-check",
      "path": "C:\\Users\\brsth\\.grok\\skills\\doc-check\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "go",
        "review"
      ],
      "consumes_provider": [
        "ruff"
      ],
      "references_wiki": [
        "page",
        "slug",
        "some-concept"
      ],
      "provides": [
        "broken-link-detection",
        "changelog-validation",
        "code-fence-validation",
        "documentation-readiness-check",
        "readme-staleness-detection",
        "repo-file-completeness",
        "skill-frontmatter-validation",
        "wikilink-resolution"
      ],
      "domain": "verify"
    },
    {
      "name": "domain-terms",
      "path": "C:\\Users\\brsth\\.grok\\skills\\domain-terms\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "design",
        "grill-me",
        "plan-writer",
        "refine",
        "review",
        "tp",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "domain-term-extraction"
      ],
      "domain": "knowledge"
    },
    {
      "name": "dream",
      "path": "C:\\Users\\brsth\\.grok\\skills\\dream\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "check",
        "close",
        "debrief",
        "design",
        "handoff",
        "red-team",
        "refine",
        "review",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "episodic-memory",
        "exa",
        "gh"
      ],
      "references_wiki": [
        "llm-dreaming-memory-consolidation",
        "operator-collaboration-style-and-leverage",
        "self-improving-agent-systems-techniques-and-workspace-gaps"
      ],
      "provides": [
        "offline-memory-consolidation"
      ],
      "domain": "self-improvement"
    },
    {
      "name": "friction",
      "path": "C:\\Users\\brsth\\.grok\\skills\\friction\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "debrief",
        "handoff"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "friction-detection",
        "workflow-automation-analysis"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "go",
      "path": "C:\\Users\\brsth\\.grok\\skills\\go\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "design",
        "grok-discovery",
        "grok-parallel",
        "grok-route",
        "grok-safe-git",
        "grok-verify",
        "handoff",
        "plan-writer",
        "refine",
        "review",
        "tp",
        "wiki"
      ],
      "consumes_provider": [
        "brave",
        "coding-model-pool",
        "ddg",
        "exa",
        "gh",
        "nlm"
      ],
      "references_wiki": [
        "coding-model-pool-tier-1-tier-2",
        "framing-check-pattern",
        "prompting-patterns-for-ai-agent-control",
        "subagent-shell-quoting-durable-fix"
      ],
      "provides": [
        "discovery-dispatch",
        "engineering-orchestration",
        "parallel-implement-dispatch",
        "safe-git-preflight-dispatch",
        "verify-dispatch"
      ],
      "domain": "orchestration"
    },
    {
      "name": "grill-me",
      "path": "C:\\Users\\brsth\\.grok\\skills\\grill-me\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "design",
        "domain-terms",
        "go",
        "plan-writer",
        "refine"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "decision-tree-elicitation",
        "requirements-elicitation"
      ],
      "domain": "alignment"
    },
    {
      "name": "grok-discovery",
      "path": "C:\\Users\\brsth\\.grok\\skills\\grok-discovery\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [
        "gh"
      ],
      "references_wiki": [],
      "provides": [
        "source-authority-discovery"
      ],
      "domain": "discovery"
    },
    {
      "name": "grok-go",
      "path": "C:\\Users\\brsth\\.grok\\skills\\grok-go\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "orchestration"
    },
    {
      "name": "grok-parallel",
      "path": "C:\\Users\\brsth\\.grok\\skills\\grok-parallel\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "go",
        "grok-discovery",
        "grok-route",
        "grok-safe-git",
        "grok-verify"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [],
      "provides": [
        "parallel-fan-out",
        "subagent-dispatch"
      ],
      "domain": "orchestration"
    },
    {
      "name": "grok-route",
      "path": "C:\\Users\\brsth\\.grok\\skills\\grok-route\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "package-routing"
      ],
      "domain": "orchestration"
    },
    {
      "name": "grok-safe-git",
      "path": "C:\\Users\\brsth\\.grok\\skills\\grok-safe-git\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "wiki"
      ],
      "consumes_provider": [
        "gh"
      ],
      "references_wiki": [
        "multi-terminal-git-coordination-primitives"
      ],
      "provides": [
        "git-safety-preflight"
      ],
      "domain": "orchestration"
    },
    {
      "name": "grok-sdlc",
      "path": "C:\\Users\\brsth\\.grok\\skills\\grok-sdlc\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "orchestration"
    },
    {
      "name": "grok-verify",
      "path": "C:\\Users\\brsth\\.grok\\skills\\grok-verify\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "grok-route",
        "grok-safe-git"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [],
      "provides": [
        "completion-gate"
      ],
      "domain": "testing"
    },
    {
      "name": "handoff",
      "path": "C:\\Users\\brsth\\.grok\\skills\\handoff\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "close",
        "debrief",
        "design",
        "go",
        "refine",
        "tp",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh",
        "mechanical-model-pool"
      ],
      "references_wiki": [
        "signal-based-intent-expansion",
        "skill-usability-audit-cold-read-critique"
      ],
      "provides": [
        "handoff-auto-update",
        "handoff-write"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "harvest",
      "path": "C:\\Users\\brsth\\.grok\\skills\\harvest\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "close",
        "debrief",
        "handoff",
        "todo",
        "tp",
        "why"
      ],
      "consumes_provider": [
        "mechanical-model-pool",
        "pending-suggestions"
      ],
      "references_wiki": [],
      "provides": [
        "cross-session-pattern-detection",
        "obligation-lifecycle",
        "value-tracking"
      ],
      "domain": "self-improvement"
    },
    {
      "name": "help",
      "path": "C:\\Users\\brsth\\.grok\\skills\\help\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "grok-documentation-help"
      ],
      "domain": "fleet-ops"
    },
    {
      "name": "imagine",
      "path": "C:\\Users\\brsth\\.grok\\skills\\imagine\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [],
      "provides": [
        "image-generation-guidance"
      ],
      "domain": "implementation"
    },
    {
      "name": "improve-codebase-architecture",
      "path": "C:\\Users\\brsth\\.grok\\skills\\improve-codebase-architecture\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "maintain",
      "path": "C:\\Users\\brsth\\.grok\\skills\\maintain\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "close",
        "handoff",
        "recover",
        "skill-prune",
        "wiki"
      ],
      "consumes_provider": [
        "gh"
      ],
      "references_wiki": [
        "fleet-maintenance-skill-design",
        "scheduled-checks-in-maintain"
      ],
      "provides": [
        "fleet-maintenance"
      ],
      "domain": "self-improvement"
    },
    {
      "name": "marketplace-bridge",
      "path": "C:\\Users\\brsth\\.grok\\skills\\marketplace-bridge\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "marketplace-skill-discovery"
      ],
      "domain": "discovery"
    },
    {
      "name": "mmx",
      "path": "C:\\Users\\brsth\\.grok\\skills\\mmx\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "agy",
        "codex"
      ],
      "consumes_provider": [
        "agy",
        "codex",
        "exa",
        "gh",
        "mmx"
      ],
      "references_wiki": [],
      "provides": [
        "cross-model-second-opinion",
        "minimax-vision",
        "minimax-web-search"
      ],
      "domain": "cross-model"
    },
    {
      "name": "model-benchmark",
      "path": "C:\\Users\\brsth\\.grok\\skills\\model-benchmark\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "go",
        "review",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "agy",
        "codex",
        "exa",
        "gh",
        "mmx"
      ],
      "references_wiki": [
        "model-fleet-provider-pools",
        "model-pool-not-chain",
        "tool-fallbacks"
      ],
      "provides": [
        "cost-tracking",
        "latency-benchmark",
        "quality-scoring"
      ],
      "domain": "fleet-ops"
    },
    {
      "name": "model-discover",
      "path": "C:\\Users\\brsth\\.grok\\skills\\model-discover\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "model-benchmark"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "model-discovery"
      ],
      "domain": "fleet-ops"
    },
    {
      "name": "model-quota",
      "path": "C:\\Users\\brsth\\.grok\\skills\\model-quota\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "maintain",
        "mmx",
        "todo"
      ],
      "consumes_provider": [
        "exa",
        "firecrawl",
        "mmx",
        "tavily"
      ],
      "references_wiki": [],
      "provides": [
        "quota-dashboard"
      ],
      "domain": "monitoring"
    },
    {
      "name": "model-web",
      "path": "C:\\Users\\brsth\\.grok\\skills\\model-web\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "agy",
        "chrome-devtools-mcp",
        "codex",
        "handoff",
        "mmx",
        "red-team",
        "tp",
        "why"
      ],
      "consumes_provider": [
        "chrome-devtools",
        "chrome-devtools-mcp-tools",
        "perplexity"
      ],
      "references_wiki": [
        "cdp-network-interception-and-sse-capture-for-llm-chat",
        "chromium-cdp-websocket-origin-restriction",
        "multi-llm-aggregator-landscape"
      ],
      "provides": [
        "browser-llm-bridge",
        "conversation-selection",
        "fusion-portal-orchestration",
        "model-web-advisory",
        "multi-model-ensemble",
        "sse-response-capture"
      ],
      "domain": "browser-automation"
    },
    {
      "name": "notice",
      "path": "C:\\Users\\brsth\\.grok\\skills\\notice\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "go",
        "grok-parallel",
        "handoff",
        "red-team",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "intent-mode-gated-auto-composition",
        "mechanisms-for-thought-partner-behavior",
        "proactive-ai-volunteering-mechanisms",
        "user-modeling-for-agentic-clis",
        "wiki-concept"
      ],
      "provides": [
        "mid-conversation-observation-surfacing"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "packet",
      "path": "C:\\Users\\brsth\\.grok\\skills\\packet\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "handoff"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "file-pack",
        "session-export"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "plan-writer",
      "path": "C:\\Users\\brsth\\.grok\\skills\\plan-writer\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "design",
        "go",
        "handoff",
        "refine",
        "tp",
        "wargame",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "agentic-sdlc-skill-lifecycle-architecture",
        "maker-checker-required-for-enforcement-work"
      ],
      "provides": [
        "plan-writing"
      ],
      "domain": "discovery"
    },
    {
      "name": "prompt-patterns",
      "path": "C:\\Users\\brsth\\.grok\\skills\\prompt-patterns\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "handoff",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "prompting-patterns-for-ai-agent-control"
      ],
      "provides": [
        "prompting-techniques-reference"
      ],
      "domain": "knowledge"
    },
    {
      "name": "recap-grok",
      "path": "C:\\Users\\brsth\\.grok\\skills\\recap-grok\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "close",
        "debrief",
        "handoff",
        "todo",
        "tp",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "session-chain-walk",
        "session-recap-grok"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "refactor",
      "path": "C:\\Users\\brsth\\.grok\\skills\\refactor\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "go",
        "handoff",
        "refine",
        "review",
        "tp",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh",
        "nlm"
      ],
      "references_wiki": [
        "agentic-sdlc-skill-lifecycle-architecture",
        "verification-before-completion-principle"
      ],
      "provides": [
        "structural-refactor"
      ],
      "domain": "implementation"
    },
    {
      "name": "refine",
      "path": "C:\\Users\\brsth\\.grok\\skills\\refine\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "design",
        "go",
        "handoff",
        "plan-writer",
        "review",
        "tp",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh",
        "mechanical-model-pool"
      ],
      "references_wiki": [
        "agentic-sdlc-skill-lifecycle-architecture",
        "designing-harnesses-that-make-good-behavior-the-path-of-least-resistance",
        "task-refinement-interview-detection-template-patterns",
        "trust-escalation-ladder-autonomous-agent-work",
        "workflow-definition-over-agent-capability"
      ],
      "provides": [
        "task-refinement"
      ],
      "domain": "discovery"
    },
    {
      "name": "research",
      "path": "C:\\Users\\brsth\\.grok\\skills\\research\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "review",
      "path": "C:\\Users\\brsth\\.grok\\skills\\review\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "go",
        "red-team",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "codex",
        "coding-model-pool",
        "critic-model-pool",
        "exa",
        "gh"
      ],
      "references_wiki": [
        "agentic-sdlc-skill-lifecycle-architecture",
        "fix-introduces-regression-by-trading-properties"
      ],
      "provides": [
        "code-review",
        "subagent-dispatch",
        "verified-findings-on-disk"
      ],
      "domain": "review"
    },
    {
      "name": "search-fleet",
      "path": "C:\\Users\\brsth\\.grok\\skills\\search-fleet\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "agy"
      ],
      "consumes_provider": [
        "agy",
        "ddg",
        "exa",
        "firecrawl",
        "gh",
        "mmx",
        "perplexity",
        "pwm",
        "reddit",
        "search-research",
        "tavily"
      ],
      "references_wiki": [],
      "provides": [
        "capability-routed-search",
        "rrf-aggregation"
      ],
      "domain": "discovery"
    },
    {
      "name": "ship",
      "path": "C:\\Users\\brsth\\.grok\\skills\\ship\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "grok-safe-git",
        "grok-verify",
        "handoff",
        "review",
        "todo",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "ship-pipeline",
        "verify-and-publish"
      ],
      "domain": "orchestration"
    },
    {
      "name": "skill-dev",
      "path": "C:\\Users\\brsth\\.grok\\skills\\skill-dev\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "check",
        "close",
        "create-skill",
        "fmea",
        "grok-verify",
        "handoff",
        "maintain",
        "notice",
        "review",
        "skill-prune",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "code-output-passthrough-narration-over-script-output",
        "cross-invocation-skills-proactively-suggest-complementary-skills",
        "execution-receipts-for-executable-artifacts",
        "mechanical-enforcement-of-llm-skill-steps-2026",
        "skill-catalog",
        "skill-development-portfolio",
        "skill-management-in-agentic-systems-research-survey",
        "skill-techniques-index"
      ],
      "provides": [
        "skill-improvement",
        "skill-measurement"
      ],
      "domain": "self-improvement"
    },
    {
      "name": "slc",
      "path": "C:\\Users\\brsth\\.grok\\skills\\slc\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "notice",
        "tp"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "thought-partner-standard"
      ],
      "provides": [
        "behavioral-reset",
        "thought-partner-realignment"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "tasks",
      "path": "C:\\Users\\brsth\\.grok\\skills\\tasks\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [
        "agy",
        "codex",
        "exa",
        "gh"
      ],
      "references_wiki": [],
      "provides": [
        "persistent-task-store"
      ],
      "domain": "fleet-ops"
    },
    {
      "name": "tdd",
      "path": "C:\\Users\\brsth\\.grok\\skills\\tdd\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "teach",
      "path": "C:\\Users\\brsth\\.grok\\skills\\teach\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "to-spec",
      "path": "C:\\Users\\brsth\\.grok\\skills\\to-spec\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "to-tickets",
      "path": "C:\\Users\\brsth\\.grok\\skills\\to-tickets\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "todo",
      "path": "C:\\Users\\brsth\\.grok\\skills\\todo\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "go",
        "review",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh",
        "notebooklm",
        "reddit"
      ],
      "references_wiki": [
        "signal-based-intent-expansion"
      ],
      "provides": [
        "workspace-prioritized-action-list"
      ],
      "domain": "fleet-ops"
    },
    {
      "name": "tp",
      "path": "C:\\Users\\brsth\\.grok\\skills\\tp\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "agy",
        "check",
        "close",
        "codex",
        "debrief",
        "design",
        "go",
        "grok-verify",
        "handoff",
        "mmx",
        "notice",
        "packet",
        "preflight",
        "red-team",
        "review",
        "skill-dev",
        "todo",
        "web",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "agy",
        "codex",
        "critic-model-pool",
        "ddg",
        "firecrawl",
        "reasoning-model-pool",
        "spawn-subagent"
      ],
      "references_wiki": [
        "analyst-exhibits-pattern-being-analyzed",
        "code-orchestrates-model-judges-skill-scale",
        "cross-invocation-skills-proactively-suggest-complementary-skills",
        "inter-skill-output-bridges-and-temporal-surfacing-layers",
        "markdown-mermaid-rendering-agentic-clis-windows-11",
        "model-fit-and-post-hoc-behavioral-detection",
        "model-pool-not-chain",
        "model-pool-selection-policy-speed-quota-diversity",
        "model-tool-calling-capability-matrix",
        "signal-based-intent-expansion",
        "skill-catalog",
        "tool-fallbacks"
      ],
      "provides": [
        "critical-friend-critique",
        "session-opportunity-review",
        "subagent-dispatch",
        "system-exploration"
      ],
      "domain": "review"
    },
    {
      "name": "trace",
      "path": "C:\\Users\\brsth\\.grok\\skills\\trace\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "logic-error-detection",
        "manual-trace-verification"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "triage",
      "path": "C:\\Users\\brsth\\.grok\\skills\\triage\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wargame",
      "path": "C:\\Users\\brsth\\.grok\\skills\\wargame\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "design",
        "go",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "codex",
        "gh"
      ],
      "references_wiki": [],
      "provides": [
        "content-discipline-for-plans"
      ],
      "domain": "review"
    },
    {
      "name": "wayfinder",
      "path": "C:\\Users\\brsth\\.grok\\skills\\wayfinder\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "web",
      "path": "C:\\Users\\brsth\\.grok\\skills\\web\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "design",
        "mmx",
        "wiki"
      ],
      "consumes_provider": [
        "brave",
        "ddg",
        "duckduckgo",
        "exa",
        "firecrawl",
        "hn-algolia",
        "mmx",
        "perplexity",
        "reddit",
        "search-research",
        "stackexchange",
        "tavily"
      ],
      "references_wiki": [
        "optimal-multi-backend-search-strategy",
        "search-tool-landscape-2026",
        "subagent-shell-quoting-durable-fix",
        "web-research-state-2026",
        "web-search-tool-routing"
      ],
      "provides": [
        "multi-backend-search",
        "rrf-merge"
      ],
      "domain": "discovery"
    },
    {
      "name": "why",
      "path": "C:\\Users\\brsth\\.grok\\skills\\why\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "agy",
        "codex",
        "design",
        "go",
        "handoff",
        "mmx",
        "red-team",
        "tp",
        "web",
        "wiki"
      ],
      "consumes_provider": [
        "reasoning-model-pool",
        "spawn-subagent"
      ],
      "references_wiki": [
        "compaction-inherited-diagnosis-unverified-propagation",
        "multidimensional-root-cause-analysis-ai-agent-failures",
        "problem-first-systems-decomposition",
        "reactive-pattern-matching-and-closure-pressure",
        "self-reflection-in-llms-fails-without-external-evidence"
      ],
      "provides": [
        "feedback-to-wiki",
        "pattern-library-query",
        "root-cause-analysis"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "wiki",
      "path": "C:\\Users\\brsth\\.grok\\skills\\wiki\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "close",
        "handoff",
        "skill-prune",
        "todo"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "concept",
        "couple-triggers-to-events-that-actually-fire",
        "existing-concept",
        "inline-conditional-over-dispatch-for-skill-design",
        "knowledge-capture-cant-afford-to-lose",
        "skill-catalog",
        "synchronous-review-direct-write-pattern",
        "wikilinks",
        "x"
      ],
      "provides": [
        "wiki-query",
        "wiki-write"
      ],
      "domain": "knowledge"
    },
    {
      "name": "wiki-crawl4ai",
      "path": "C:\\Users\\brsth\\.grok\\skills\\wiki-crawl4ai\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "crawl4ai",
        "web",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "firecrawl",
        "gh"
      ],
      "references_wiki": [
        "page",
        "wikilinks"
      ],
      "provides": [
        "web-ingestion"
      ],
      "domain": "discovery"
    },
    {
      "name": "wizard",
      "path": "C:\\Users\\brsth\\.grok\\skills\\wizard\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "write",
      "path": "C:\\Users\\brsth\\.grok\\skills\\write\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "content-production"
      ],
      "domain": "content"
    },
    {
      "name": "writing-great-skills",
      "path": "C:\\Users\\brsth\\.grok\\skills\\writing-great-skills\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "www",
      "path": "C:\\Users\\brsth\\.grok\\skills\\www\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "design",
        "go",
        "red-team",
        "todo",
        "tp",
        "web",
        "why",
        "wiki",
        "wiki-crawl4ai"
      ],
      "consumes_provider": [
        "ddg",
        "firecrawl",
        "gh",
        "github-issues",
        "hn-algolia",
        "mechanical-model-pool",
        "mmx",
        "reddit"
      ],
      "references_wiki": [
        "adaptive-research-depth-preventing-incomplete-www-coverage",
        "concept-1",
        "concept-2",
        "concurrent-cdp-auth-contention",
        "invariants-beat-environment-comfort",
        "notebooklm-cli-operational-gotchas",
        "parallel-subagent-wait-all-gate",
        "plausible-narratives-substitute-for-verification",
        "prior-concept",
        "research-applicability-checking-dont-cite-without-verifying-assumptions",
        "research-quality-principle-efficiency-not-censorship",
        "skill-catalog",
        "subagent-shell-quoting-durable-fix",
        "two-component-research-winnowing-pattern",
        "wikilink",
        "wikilinks",
        "x",
        "y"
      ],
      "provides": [
        "subagent-dispatch",
        "wiki-web-wiki-research"
      ],
      "domain": "discovery"
    },
    {
      "name": "build-with-ai",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\build-with-ai\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "code-review",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\code-review\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "create-skill",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\create-skill\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "create-workflow",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\create-workflow\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "design",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\design\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [
        "preflight"
      ],
      "consumes_provider": [
        "minimax-search"
      ],
      "references_wiki": [
        "adr-0009-extend-unverified-stance",
        "exemption-logic-as-conflict-signal"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "docx",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\docx\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "execute-plan",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\execute-plan\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [
        "design"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "game-animation-frames",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\game-animation-frames\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "game-asset-core",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\game-asset-core\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "game-character-consistency",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\game-character-consistency\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "game-tilesets",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\game-tilesets\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "game-ui-icons",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\game-ui-icons\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "imagine",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\imagine\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "implement",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\implement\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pdf",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\pdf\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pptx",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\pptx\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pr-babysit",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\pr-babysit\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "resume-claude",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\resume-claude\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "resume-codex",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\resume-codex\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [
        "codex"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "resume-cursor",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\resume-cursor\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "review",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\review\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "check",
      "path": "P:\\.grok\\skills\\check\\SKILL.md",
      "scope": "grok-project",
      "delegates_to": [
        "agy",
        "close",
        "go",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "agentic-sdlc-skill-lifecycle-architecture",
        "model-pool-selection-policy-speed-quota-diversity"
      ],
      "provides": [
        "session-verification",
        "subagent-dispatch"
      ],
      "domain": "testing"
    },
    {
      "name": "red-team",
      "path": "P:\\.grok\\skills\\red-team\\SKILL.md",
      "scope": "grok-project",
      "delegates_to": [
        "aar",
        "debrief",
        "handoff",
        "review",
        "skill-dev",
        "tp",
        "wargame",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "parallel-subagent-wait-all-gate"
      ],
      "provides": [],
      "domain": "review"
    },
    {
      "name": "avant-garde-ui",
      "path": "P:\\.agents\\skills\\avant-garde-ui\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "design"
    },
    {
      "name": "config-audit",
      "path": "P:\\.agents\\skills\\config-audit\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "recover",
        "skill-prune"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "llm-instruction-non-compliance-activation-gap-2026",
        "structural-enforcement-for-skipped-rules-grok-build-2026"
      ],
      "provides": [],
      "domain": "self-improvement"
    },
    {
      "name": "contract-status",
      "path": "P:\\.agents\\skills\\contract-status\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "monitoring"
    },
    {
      "name": "email-skill",
      "path": "P:\\.agents\\skills\\email-skill\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "todo"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "adhd-friendly-unified-todo-workspace-email-scanning",
        "concurrent-cdp-auth-contention",
        "stateless-cli-vs-mcp-for-cross-agent-email-access"
      ],
      "provides": [],
      "domain": "communication"
    },
    {
      "name": "fmea",
      "path": "P:\\.agents\\skills\\fmea\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "red-team",
        "tp"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "failure-modes-analysis",
        "risk-priority-scoring"
      ],
      "domain": "review"
    },
    {
      "name": "nlm-bulk-ingest",
      "path": "P:\\.agents\\skills\\nlm-bulk-ingest\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [
        "notebooklm-cli-operational-gotchas",
        "notebooklm-source-limits-free-vs-paid",
        "semantic-clustering-bounded-size"
      ],
      "provides": [],
      "domain": "knowledge"
    },
    {
      "name": "notebooklm",
      "path": "P:\\.agents\\skills\\notebooklm\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "knowledge"
    },
    {
      "name": "preflight",
      "path": "P:\\.agents\\skills\\preflight\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "red-team"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "evidence-backed-inventory"
      ],
      "domain": "discovery"
    },
    {
      "name": "recover",
      "path": "P:\\.agents\\skills\\recover\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [
        "notebooklm-cli-operational-gotchas"
      ],
      "provides": [
        "file-recovery"
      ],
      "domain": "fleet-ops"
    },
    {
      "name": "skill-prune",
      "path": "P:\\.agents\\skills\\skill-prune\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "recover"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "llm-instruction-non-compliance-activation-gap-2026"
      ],
      "provides": [
        "knowledge-hygiene"
      ],
      "domain": "self-improvement"
    },
    {
      "name": "wiki-yt",
      "path": "P:\\.agents\\skills\\wiki-yt\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "mmx",
        "wiki"
      ],
      "consumes_provider": [
        "mmx",
        "notebooklm"
      ],
      "references_wiki": [
        "concurrent-cdp-auth-contention",
        "nlm-bulk-ingest",
        "nlm-to-wiki-optimization-opportunities",
        "notebooklm-cli-operational-gotchas",
        "notebooklm-source-limits-free-vs-paid",
        "video-to-wiki-pipeline-transcript-extraction-multimodal",
        "wikilinks"
      ],
      "provides": [],
      "domain": "knowledge"
    },
    {
      "name": "workspace-health",
      "path": "P:\\.agents\\skills\\workspace-health\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "recover",
        "skill-prune"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "monitoring"
    },
    {
      "name": "case-feedback-skill",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-834f3fcdc68d4e7e-plugins-glm-plan-bug-4165180d\\skills\\case-feedback-skill\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "usage-query-skill",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-834f3fcdc68d4e7e-plugins-glm-plan-usage-f12dc7b5\\skills\\usage-query-skill\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "a11y-debugging",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\chrome-devtools-mcp-2df60288\\skills\\a11y-debugging\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "chrome-devtools",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\chrome-devtools-mcp-2df60288\\skills\\chrome-devtools\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "chrome-devtools-cli",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\chrome-devtools-mcp-2df60288\\skills\\chrome-devtools-cli\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "chrome-devtools"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "debug-optimize-lcp",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\chrome-devtools-mcp-2df60288\\skills\\debug-optimize-lcp\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "memory-leak-debugging",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\chrome-devtools-mcp-2df60288\\skills\\memory-leak-debugging\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "troubleshooting",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\chrome-devtools-mcp-2df60288\\skills\\troubleshooting\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "remembering-conversations",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\episodic-memory-479fd403\\skills\\remembering-conversations\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "episodic-memory"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-agent",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-agent\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-cli",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-cli\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-crawl",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-crawl\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-download",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-download\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-interact",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-interact\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-map",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-map\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-monitor",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-monitor\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-parse",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-parse\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-scrape",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-scrape\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-search",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-grok-plugin-ba077673\\skills\\firecrawl-search\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "firecrawl"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "design-an-interface",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\deprecated\\design-an-interface\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "qa",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\deprecated\\qa\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "request-refactor-plan",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\deprecated\\request-refactor-plan\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ubiquitous-language",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\deprecated\\ubiquitous-language\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ask-matt",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\ask-matt\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "diagnosing-bugs",
        "grill-me",
        "handoff",
        "improve-codebase-architecture",
        "tdd",
        "teach",
        "to-spec",
        "to-tickets",
        "triage",
        "wayfinder",
        "writing-great-skills"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "code-review",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\code-review\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "codebase-design",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\codebase-design\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "diagnosing-bugs",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\diagnosing-bugs\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "improve-codebase-architecture"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "domain-modeling",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\domain-modeling\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "grill-with-docs",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\grill-with-docs\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "implement",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\implement\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "tdd"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "improve-codebase-architecture",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\improve-codebase-architecture\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "prototype",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\prototype\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "research",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\research\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "resolving-merge-conflicts",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\resolving-merge-conflicts\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "setup-matt-pocock-skills",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\setup-matt-pocock-skills\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "triage"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tdd",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\tdd\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "to-spec",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\to-spec\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "to-tickets",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\to-tickets\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "triage",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\triage\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wayfinder",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\engineering\\wayfinder\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "batch-grill-me",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\in-progress\\batch-grill-me\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "claude-handoff",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\in-progress\\claude-handoff\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "loop-me",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\in-progress\\loop-me\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "setup-ts-deep-modules",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\in-progress\\setup-ts-deep-modules\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "to-questionnaire",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\in-progress\\to-questionnaire\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wizard",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\in-progress\\wizard\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-beats",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\in-progress\\writing-beats\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-fragments",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\in-progress\\writing-fragments\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-shape",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\in-progress\\writing-shape\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "git-guardrails-claude-code",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\misc\\git-guardrails-claude-code\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "migrate-to-shoehorn",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\misc\\migrate-to-shoehorn\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "scaffold-exercises",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\misc\\scaffold-exercises\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "setup-pre-commit",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\misc\\setup-pre-commit\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "edit-article",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\personal\\edit-article\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "obsidian-vault",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\personal\\obsidian-vault\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [
        "wikilinks"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "grill-me",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\productivity\\grill-me\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "grilling",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\productivity\\grilling\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "handoff",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\productivity\\handoff\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "teach",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\productivity\\teach\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-great-skills",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-bce86e95\\skills\\productivity\\writing-great-skills\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "brainstorming",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\brainstorming\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "dispatching-parallel-agents",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\dispatching-parallel-agents\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "finishing-a-development-branch",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\finishing-a-development-branch\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "receiving-code-review",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\receiving-code-review\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "requesting-code-review",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\requesting-code-review\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "subagent-driven-development",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\subagent-driven-development\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "systematic-debugging",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\systematic-debugging\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "test-driven-development",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\test-driven-development\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "using-git-worktrees",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\using-git-worktrees\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "using-superpowers",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\using-superpowers\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "verification-before-completion",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\verification-before-completion\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-skills",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\writing-skills\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "browsing",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-chrome-b518017c\\skills\\browsing\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "cc-model-router",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-model-router\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "debt",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-lazy-closure-debt\\skills\\debt\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "agy",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\agy\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-api",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-api\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-cli",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-cli\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "agy"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-models",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-models\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-probe-benchmark",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-probe-benchmark\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-probe-nim",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-probe-nim\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-probe-openrouter",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-probe-openrouter\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-probe-router",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-probe-router\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "codex",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\codex\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "codex"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "google-ai-usage-monitor",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\google-ai-usage-monitor\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "intelligence-stream-analyze",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\intelligence-stream-analyze\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "intelligence-stream-ingest",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\intelligence-stream-ingest\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "perplexity-web-mcp",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\perplexity-web-mcp\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "pwm"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "quota",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\quota\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "behave",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\behave\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "claude-audit",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\claude-audit\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief",
        "red-team",
        "review",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "debrief",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\debrief\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "red-team",
        "review",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "doc-compiler",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\doc-compiler\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "epistemic-check",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\epistemic-check\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "friction",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\friction\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "recap",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\recap\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief",
        "design",
        "handoff"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "retro",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\retro\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief",
        "red-team"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "rns",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\rns\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skill-audit",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\skill-audit\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief",
        "red-team",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skill-similarity",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\skill-similarity\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "tdd"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "top-problems",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\top-problems\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "trace",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\trace\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "why",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\why\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "search-research"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ask",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\ask\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "bf",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\bf\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "constitutional-patterns",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\constitutional-patterns\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "constraints",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\constraints\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "decision-tree",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\decision-tree\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "evolve",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\evolve\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design",
        "tdd"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "evolution"
    },
    {
      "name": "garden",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\garden\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "gitready",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\gitready\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "prompt_refiner",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\prompt_refiner\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ralph",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\ralph\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "tdd"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skill-from-docs",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\skill-from-docs\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skill-to-page",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\skill-to-page\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skill-write",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\skill-write\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "solo-dev-authority",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\solo-dev-authority\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "subagent-driven-development",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\subagent-driven-development\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "tdd"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "usm",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\usm\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "check",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\check\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "go",
        "improve-codebase-architecture"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "cks",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\cks\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "concept-mapper",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\concept-mapper\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "csf-nip-integration",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\csf-nip-integration\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "lmc",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\lmc\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "mlc",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\mlc\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "simplify-enhanced",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\simplify-enhanced\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "slc",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\slc\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "codebase-to-course",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\codebase-to-course\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "frontend-dev",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\frontend-dev\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "fullstack-dev",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\fullstack-dev\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "minimax-multimodal-toolkit",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\minimax-multimodal-toolkit\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "mmx"
      ],
      "consumes_provider": [
        "mmx"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "minimax-music-gen",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\minimax-music-gen\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "mmx"
      ],
      "consumes_provider": [
        "mmx"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "minimax-music-playlist",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\minimax-music-playlist\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "mmx"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "nlm",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\nlm\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "nlm",
        "notebooklm"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "nlm-to-wiki",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\nlm-to-wiki\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "wiki"
      ],
      "consumes_provider": [
        "nlm"
      ],
      "references_wiki": [
        "nlm-abc12345-concept-one",
        "nlm-abc12345-concept-two",
        "wikilinks"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "video-vision",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\video-vision\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "vision-analysis",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\vision-analysis\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "yt-is",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\yt-is\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "yt-nlm",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\yt-nlm\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "notebooklm"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "yt-selenium",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\yt-selenium\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "av",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\av\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "brainstorming",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\brainstorming\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "code",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\code\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design",
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "code-flow-visualizer",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\code-flow-visualizer\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "code-review",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\code-review\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "design",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\design\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "diagnose",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\diagnose\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "dispatching-parallel-agents",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\dispatching-parallel-agents\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "docs",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\docs\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "evidence-driven-experiment-loop",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\evidence-driven-experiment-loop\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "executing-plans",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\executing-plans\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "finishing-a-development-branch",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\finishing-a-development-branch\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "go",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\go\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design",
        "tdd"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "improve-codebase-architecture",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\improve-codebase-architecture\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "mermaid-c4",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\mermaid-c4\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "perf",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\perf\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "performance-profiler",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\performance-profiler\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "planning",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\planning\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design",
        "tdd"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pre-mortem",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\pre-mortem\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "red-team"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "preflight",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\preflight\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "profile",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\profile\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "qmd-wiki",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\qmd-wiki\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "rca",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\rca\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "refactor",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\refactor\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "review",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\review\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "red-team"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "review-pr",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\review-pr\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "review_bundle",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\review_bundle\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "risks",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\risks\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "red-team",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ship",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\ship\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "specify",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\specify\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "sqa",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\sqa\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "sqd",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\sqd\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "t",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\t\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "tdd"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "task",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\task\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tdd",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tdd\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "team",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\team\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tilldone",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tilldone\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tldr-code",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tldr-code\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tldr-deep",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tldr-deep\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tldr-overview",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tldr-overview\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tldr-router",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tldr-router\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tldr-stats",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tldr-stats\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "uci",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\uci\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "using-git-worktrees",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\using-git-worktrees\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "using-superpowers",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\using-superpowers\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "verification-before-completion",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\verification-before-completion\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wiki",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\wiki\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-plans",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\writing-plans\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-skills",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\writing-skills\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "zoom-out",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\zoom-out\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "dream",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\dream\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "execution-clarity",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\execution-clarity\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "genius",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\genius\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "learn",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\learn\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pace",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\pace\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "probe",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\probe\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "prospect",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\prospect\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "search-research"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "reason",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\reason\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "reflect",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\reflect\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "response-atomicity",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\response-atomicity\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "s",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\s\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "sequential-thinking",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\sequential-thinking\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skeptic",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\skeptic\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tot",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\tot\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "truth",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\truth\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "validation"
    },
    {
      "name": "ut",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\ut\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ux",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\ux\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "bifrost",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\bifrost\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "git",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\git\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "init",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\init\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "main",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\main\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "recover",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "main-review",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\main-review\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "mm-quota",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\mm-quota\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "plugin-installer",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\plugin-installer\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "recover",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\recover\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "usage-query-skill",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\glm-plan-usage\\skills\\usage-query-skill\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "improve",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\improve-partner\\skills\\improve\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief",
        "red-team",
        "review",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "prompt-enhancer",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\prompt-enhancer\\skills\\prompt-enhancer\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "adr",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\adr\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "build",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\build\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "capture",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\capture\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "changelog",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\changelog\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "index",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\index\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "prime",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\prime\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "stale",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\stale\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "aid",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\aid\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "all",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\all\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "chs",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\chs\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "chs-eval",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\chs-eval\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "context7",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\context7\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "context7"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "crawl",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\crawl\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "page",
        "wikilinks"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "discover",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\discover\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "export-session",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\export-session\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "debrief"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "find",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\find\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "web"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "gitingest",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\gitingest\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "nlm"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "gitpack",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\gitpack\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "keep",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\keep\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "web"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "note",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\note\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "web"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "repomix",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\repomix\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "research",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\research\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "web",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\web\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [
        "notebooklm",
        "serper"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "id",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\snapshot\\skills\\id\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "snapshot",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\snapshot\\skills\\snapshot\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    }
  ],
  "reverse": {
    "provider_consumers": {
      "reasoning-model-pool": [
        "aar",
        "tp",
        "why"
      ],
      "critic-model-pool": [
        "aar",
        "review",
        "tp"
      ],
      "exa": [
        "aar",
        "agy",
        "codex",
        "create-skill",
        "design",
        "dream",
        "go",
        "grok-parallel",
        "grok-verify",
        "handoff",
        "imagine",
        "mmx",
        "model-benchmark",
        "model-quota",
        "notice",
        "plan-writer",
        "prompt-patterns",
        "refactor",
        "refine",
        "review",
        "search-fleet",
        "skill-dev",
        "tasks",
        "todo",
        "web",
        "wiki",
        "wiki-crawl4ai"
      ],
      "nlm": [
        "aar",
        "gitingest",
        "go",
        "nlm",
        "nlm-to-wiki",
        "refactor"
      ],
      "gh": [
        "aar",
        "agy",
        "codex",
        "design",
        "dream",
        "go",
        "grok-discovery",
        "grok-parallel",
        "grok-safe-git",
        "grok-verify",
        "handoff",
        "imagine",
        "maintain",
        "mmx",
        "model-benchmark",
        "notice",
        "plan-writer",
        "prompt-patterns",
        "refactor",
        "refine",
        "review",
        "search-fleet",
        "skill-dev",
        "tasks",
        "todo",
        "wargame",
        "wiki",
        "wiki-crawl4ai",
        "www"
      ],
      "agy": [
        "agy",
        "ai-cli",
        "codex",
        "mmx",
        "model-benchmark",
        "search-fleet",
        "tasks",
        "tp"
      ],
      "codex": [
        "codex",
        "mmx",
        "model-benchmark",
        "resume-codex",
        "review",
        "tasks",
        "tp",
        "wargame"
      ],
      "mmx": [
        "design",
        "minimax-multimodal-toolkit",
        "minimax-music-gen",
        "minimax-music-playlist",
        "mmx",
        "model-benchmark",
        "model-quota",
        "search-fleet",
        "web",
        "wiki-yt",
        "www"
      ],
      "firecrawl": [
        "design",
        "firecrawl-agent",
        "firecrawl-cli",
        "firecrawl-crawl",
        "firecrawl-download",
        "firecrawl-interact",
        "firecrawl-map",
        "firecrawl-monitor",
        "firecrawl-parse",
        "firecrawl-scrape",
        "firecrawl-search",
        "model-quota",
        "search-fleet",
        "tp",
        "web",
        "wiki-crawl4ai",
        "www"
      ],
      "ruff": [
        "doc-check"
      ],
      "episodic-memory": [
        "dream",
        "remembering-conversations"
      ],
      "coding-model-pool": [
        "go",
        "review"
      ],
      "brave": [
        "go",
        "web"
      ],
      "ddg": [
        "go",
        "search-fleet",
        "tp",
        "web",
        "www"
      ],
      "mechanical-model-pool": [
        "handoff",
        "harvest",
        "refine",
        "www"
      ],
      "pending-suggestions": [
        "harvest"
      ],
      "tavily": [
        "model-quota",
        "search-fleet",
        "web"
      ],
      "chrome-devtools-mcp-tools": [
        "model-web"
      ],
      "perplexity": [
        "model-web",
        "search-fleet",
        "web"
      ],
      "chrome-devtools": [
        "chrome-devtools-cli",
        "model-web"
      ],
      "search-research": [
        "prospect",
        "search-fleet",
        "web",
        "why"
      ],
      "reddit": [
        "search-fleet",
        "todo",
        "web",
        "www"
      ],
      "pwm": [
        "perplexity-web-mcp",
        "search-fleet"
      ],
      "notebooklm": [
        "nlm",
        "todo",
        "web",
        "wiki-yt",
        "yt-nlm"
      ],
      "spawn-subagent": [
        "tp",
        "why"
      ],
      "duckduckgo": [
        "web"
      ],
      "stackexchange": [
        "web"
      ],
      "hn-algolia": [
        "web",
        "www"
      ],
      "github-issues": [
        "www"
      ],
      "minimax-search": [
        "design"
      ],
      "context7": [
        "context7"
      ],
      "serper": [
        "web"
      ]
    },
    "skill_callers": {
      "tp": [
        "aar",
        "ask",
        "behave",
        "capture",
        "close",
        "design",
        "domain-terms",
        "dream",
        "fmea",
        "go",
        "handoff",
        "harvest",
        "model-benchmark",
        "model-web",
        "notice",
        "plan-writer",
        "recap-grok",
        "red-team",
        "refactor",
        "refine",
        "review",
        "skill-dev",
        "slc",
        "todo",
        "why",
        "www"
      ],
      "review": [
        "aar",
        "ask",
        "behave",
        "check",
        "claude-audit",
        "close",
        "debrief",
        "doc-check",
        "domain-terms",
        "dream",
        "go",
        "improve",
        "learn",
        "marketplace-bridge",
        "model-benchmark",
        "red-team",
        "refactor",
        "refine",
        "review-pr",
        "risks",
        "ship",
        "skill-audit",
        "skill-dev",
        "sqd",
        "todo",
        "tp",
        "uci"
      ],
      "wiki": [
        "aar",
        "capture",
        "claude-audit",
        "close",
        "crawl",
        "create-skill",
        "debrief",
        "design",
        "domain-terms",
        "dream",
        "go",
        "grok-safe-git",
        "handoff",
        "improve",
        "main",
        "maintain",
        "model-benchmark",
        "nlm-to-wiki",
        "notice",
        "plan-writer",
        "prompt-patterns",
        "recap-grok",
        "refactor",
        "refine",
        "review",
        "ship",
        "skill-dev",
        "todo",
        "tp",
        "ux",
        "wargame",
        "web",
        "why",
        "wiki-crawl4ai",
        "wiki-yt",
        "www"
      ],
      "check": [
        "aar",
        "ask",
        "close",
        "doc-check",
        "doc-compiler",
        "dream",
        "go",
        "grok-verify",
        "model-benchmark",
        "refactor",
        "refine",
        "review",
        "ship",
        "skill-dev",
        "skill-to-page",
        "todo",
        "tp",
        "www"
      ],
      "close": [
        "aar",
        "ask",
        "capture",
        "check",
        "dream",
        "handoff",
        "harvest",
        "maintain",
        "recap-grok",
        "review",
        "ship",
        "skill-dev",
        "todo",
        "tp",
        "wiki"
      ],
      "go": [
        "aar",
        "ask",
        "check",
        "close",
        "code",
        "design",
        "doc-check",
        "grill-me",
        "grok-go",
        "grok-parallel",
        "grok-sdlc",
        "handoff",
        "model-benchmark",
        "notice",
        "plan-writer",
        "refactor",
        "refine",
        "research",
        "review",
        "rns",
        "todo",
        "tp",
        "wargame",
        "why",
        "www"
      ],
      "red-team": [
        "aar",
        "behave",
        "claude-audit",
        "close",
        "debrief",
        "dream",
        "fmea",
        "improve",
        "model-web",
        "notice",
        "pre-mortem",
        "preflight",
        "retro",
        "review",
        "risks",
        "skill-audit",
        "tp",
        "why",
        "www"
      ],
      "handoff": [
        "aar",
        "ask",
        "ask-matt",
        "behave",
        "capture",
        "close",
        "design",
        "dream",
        "friction",
        "go",
        "harvest",
        "maintain",
        "model-web",
        "notice",
        "packet",
        "plan-writer",
        "prompt-patterns",
        "recap",
        "recap-grok",
        "red-team",
        "refactor",
        "refine",
        "ship",
        "skill-dev",
        "tp",
        "why",
        "wiki"
      ],
      "why": [
        "aar",
        "ask",
        "behave",
        "dream",
        "harvest",
        "model-benchmark",
        "model-web",
        "notice",
        "red-team",
        "review",
        "skill-dev",
        "todo",
        "tp",
        "wargame",
        "www"
      ],
      "debrief": [
        "aar",
        "agy",
        "behave",
        "claude-audit",
        "close",
        "codex",
        "dream",
        "export-session",
        "friction",
        "handoff",
        "harvest",
        "improve",
        "lmc",
        "mlc",
        "recap",
        "recap-grok",
        "red-team",
        "retro",
        "skill-audit",
        "top-problems",
        "tp"
      ],
      "refine": [
        "aar",
        "design",
        "domain-terms",
        "dream",
        "go",
        "grill-me",
        "handoff",
        "plan-writer",
        "refactor"
      ],
      "todo": [
        "ask",
        "capture",
        "close",
        "design",
        "email-skill",
        "harvest",
        "model-quota",
        "recap-grok",
        "ship",
        "tp",
        "wiki",
        "www"
      ],
      "design": [
        "ask",
        "behave",
        "close",
        "code",
        "discover",
        "domain-terms",
        "dream",
        "evolve",
        "execute-plan",
        "go",
        "grill-me",
        "handoff",
        "plan-writer",
        "planning",
        "prompt_refiner",
        "recap",
        "refine",
        "s",
        "specify",
        "tp",
        "wargame",
        "web",
        "why",
        "www"
      ],
      "tasks": [
        "capture"
      ],
      "friction": [
        "capture"
      ],
      "aar": [
        "capture",
        "close",
        "dream",
        "friction",
        "handoff",
        "harvest",
        "model-web",
        "notice",
        "packet",
        "recap-grok",
        "red-team",
        "skill-dev",
        "slc",
        "tp",
        "wargame",
        "why"
      ],
      "notice": [
        "close",
        "skill-dev",
        "slc",
        "tp"
      ],
      "capture": [
        "close"
      ],
      "skill-dev": [
        "close",
        "create-skill",
        "red-team",
        "tp"
      ],
      "agy": [
        "check",
        "codex",
        "mmx",
        "model-web",
        "search-fleet",
        "tp",
        "why"
      ],
      "skill-prune": [
        "config-audit",
        "create-skill",
        "maintain",
        "skill-dev",
        "wiki",
        "workspace-health"
      ],
      "plan-writer": [
        "design",
        "domain-terms",
        "go",
        "grill-me",
        "refine"
      ],
      "preflight": [
        "design",
        "tp"
      ],
      "improve-codebase-architecture": [
        "ask-matt",
        "check",
        "diagnosing-bugs"
      ],
      "grill-me": [
        "ask-matt",
        "domain-terms"
      ],
      "grok-parallel": [
        "go",
        "notice"
      ],
      "grok-discovery": [
        "go",
        "grok-parallel"
      ],
      "grok-verify": [
        "go",
        "grok-parallel",
        "ship",
        "skill-dev",
        "tp"
      ],
      "grok-safe-git": [
        "go",
        "grok-parallel",
        "grok-verify",
        "ship"
      ],
      "grok-route": [
        "go",
        "grok-parallel",
        "grok-verify"
      ],
      "domain-terms": [
        "grill-me"
      ],
      "recover": [
        "config-audit",
        "main",
        "maintain",
        "skill-prune",
        "workspace-health"
      ],
      "codex": [
        "mmx",
        "model-web",
        "tp",
        "why"
      ],
      "model-benchmark": [
        "model-discover"
      ],
      "mmx": [
        "minimax-multimodal-toolkit",
        "minimax-music-gen",
        "model-quota",
        "model-web",
        "tp",
        "web",
        "why",
        "wiki-yt"
      ],
      "maintain": [
        "model-quota",
        "skill-dev"
      ],
      "chrome-devtools-mcp": [
        "model-web"
      ],
      "wargame": [
        "plan-writer",
        "red-team"
      ],
      "create-skill": [
        "skill-dev"
      ],
      "fmea": [
        "skill-dev"
      ],
      "packet": [
        "tp"
      ],
      "web": [
        "find",
        "keep",
        "note",
        "tp",
        "why",
        "wiki-crawl4ai",
        "www"
      ],
      "crawl4ai": [
        "wiki-crawl4ai"
      ],
      "wiki-crawl4ai": [
        "www"
      ],
      "to-spec": [
        "ask-matt"
      ],
      "wayfinder": [
        "ask-matt"
      ],
      "diagnosing-bugs": [
        "ask-matt"
      ],
      "tdd": [
        "ask-matt",
        "evolve",
        "go",
        "implement",
        "planning",
        "ralph",
        "skill-similarity",
        "subagent-driven-development",
        "t"
      ],
      "to-tickets": [
        "ask-matt"
      ],
      "teach": [
        "ask-matt"
      ],
      "triage": [
        "ask-matt",
        "setup-matt-pocock-skills"
      ],
      "writing-great-skills": [
        "ask-matt"
      ]
    },
    "wiki_referencers": {
      "friction-detection-operator-pushback-as-trigger": [
        "aar"
      ],
      "parallel-subagent-wait-all-gate": [
        "aar",
        "red-team",
        "www"
      ],
      "tool-fallbacks": [
        "aar",
        "design",
        "model-benchmark",
        "tp"
      ],
      "user-modeling-for-agentic-clis": [
        "aar",
        "notice"
      ],
      "skill-graph": [
        "ask"
      ],
      "signal-based-intent-expansion": [
        "ask",
        "close",
        "handoff",
        "todo",
        "tp"
      ],
      "skill-catalog": [
        "ask",
        "skill-dev",
        "tp",
        "wiki",
        "www"
      ],
      "governance-pattern-library": [
        "behave"
      ],
      "proactive-improvement-opportunity-scanner": [
        "capture"
      ],
      "plausible-narratives-substitute-for-verification": [
        "capture",
        "www"
      ],
      "prompting-patterns-for-ai-agent-control": [
        "close",
        "go",
        "prompt-patterns"
      ],
      "agentic-sdlc-skill-lifecycle-architecture": [
        "check",
        "close",
        "design",
        "plan-writer",
        "refactor",
        "refine",
        "review"
      ],
      "consistency-drift-as-waste-source-in-iterative-refinement": [
        "design"
      ],
      "llm-synthesis-quality-and-speed-techniques": [
        "design"
      ],
      "exemption-logic-as-conflict-signal": [
        "design"
      ],
      "adr-0009-extend-unverified-stance": [
        "design"
      ],
      "raising-coding-best-practices-in-ai-agents": [
        "design"
      ],
      "concept-slug": [
        "design"
      ],
      "page": [
        "crawl",
        "doc-check",
        "wiki-crawl4ai"
      ],
      "slug": [
        "doc-check"
      ],
      "some-concept": [
        "doc-check"
      ],
      "operator-collaboration-style-and-leverage": [
        "dream"
      ],
      "llm-dreaming-memory-consolidation": [
        "dream"
      ],
      "self-improving-agent-systems-techniques-and-workspace-gaps": [
        "dream"
      ],
      "coding-model-pool-tier-1-tier-2": [
        "go"
      ],
      "framing-check-pattern": [
        "go"
      ],
      "subagent-shell-quoting-durable-fix": [
        "go",
        "web",
        "www"
      ],
      "multi-terminal-git-coordination-primitives": [
        "grok-safe-git"
      ],
      "skill-usability-audit-cold-read-critique": [
        "handoff"
      ],
      "fleet-maintenance-skill-design": [
        "maintain"
      ],
      "scheduled-checks-in-maintain": [
        "maintain"
      ],
      "model-fleet-provider-pools": [
        "model-benchmark"
      ],
      "model-pool-not-chain": [
        "model-benchmark",
        "tp"
      ],
      "multi-llm-aggregator-landscape": [
        "model-web"
      ],
      "cdp-network-interception-and-sse-capture-for-llm-chat": [
        "model-web"
      ],
      "chromium-cdp-websocket-origin-restriction": [
        "model-web"
      ],
      "proactive-ai-volunteering-mechanisms": [
        "notice"
      ],
      "wiki-concept": [
        "notice"
      ],
      "intent-mode-gated-auto-composition": [
        "notice"
      ],
      "mechanisms-for-thought-partner-behavior": [
        "notice"
      ],
      "maker-checker-required-for-enforcement-work": [
        "plan-writer"
      ],
      "verification-before-completion-principle": [
        "refactor"
      ],
      "task-refinement-interview-detection-template-patterns": [
        "refine"
      ],
      "trust-escalation-ladder-autonomous-agent-work": [
        "refine"
      ],
      "designing-harnesses-that-make-good-behavior-the-path-of-least-resistance": [
        "refine"
      ],
      "workflow-definition-over-agent-capability": [
        "refine"
      ],
      "fix-introduces-regression-by-trading-properties": [
        "review"
      ],
      "code-output-passthrough-narration-over-script-output": [
        "skill-dev"
      ],
      "cross-invocation-skills-proactively-suggest-complementary-skills": [
        "skill-dev",
        "tp"
      ],
      "skill-development-portfolio": [
        "skill-dev"
      ],
      "skill-techniques-index": [
        "skill-dev"
      ],
      "execution-receipts-for-executable-artifacts": [
        "skill-dev"
      ],
      "skill-management-in-agentic-systems-research-survey": [
        "skill-dev"
      ],
      "mechanical-enforcement-of-llm-skill-steps-2026": [
        "skill-dev"
      ],
      "thought-partner-standard": [
        "slc"
      ],
      "analyst-exhibits-pattern-being-analyzed": [
        "tp"
      ],
      "code-orchestrates-model-judges-skill-scale": [
        "tp"
      ],
      "model-fit-and-post-hoc-behavioral-detection": [
        "tp"
      ],
      "inter-skill-output-bridges-and-temporal-surfacing-layers": [
        "tp"
      ],
      "model-pool-selection-policy-speed-quota-diversity": [
        "check",
        "tp"
      ],
      "model-tool-calling-capability-matrix": [
        "tp"
      ],
      "markdown-mermaid-rendering-agentic-clis-windows-11": [
        "tp"
      ],
      "search-tool-landscape-2026": [
        "web"
      ],
      "web-search-tool-routing": [
        "web"
      ],
      "optimal-multi-backend-search-strategy": [
        "web"
      ],
      "web-research-state-2026": [
        "web"
      ],
      "multidimensional-root-cause-analysis-ai-agent-failures": [
        "why"
      ],
      "problem-first-systems-decomposition": [
        "why"
      ],
      "self-reflection-in-llms-fails-without-external-evidence": [
        "why"
      ],
      "reactive-pattern-matching-and-closure-pressure": [
        "why"
      ],
      "compaction-inherited-diagnosis-unverified-propagation": [
        "why"
      ],
      "x": [
        "wiki",
        "www"
      ],
      "knowledge-capture-cant-afford-to-lose": [
        "wiki"
      ],
      "couple-triggers-to-events-that-actually-fire": [
        "wiki"
      ],
      "inline-conditional-over-dispatch-for-skill-design": [
        "wiki"
      ],
      "concept": [
        "wiki"
      ],
      "existing-concept": [
        "wiki"
      ],
      "synchronous-review-direct-write-pattern": [
        "wiki"
      ],
      "wikilinks": [
        "crawl",
        "nlm-to-wiki",
        "obsidian-vault",
        "wiki",
        "wiki-crawl4ai",
        "wiki-yt",
        "www"
      ],
      "notebooklm-cli-operational-gotchas": [
        "nlm-bulk-ingest",
        "recover",
        "wiki-yt",
        "www"
      ],
      "research-quality-principle-efficiency-not-censorship": [
        "www"
      ],
      "concurrent-cdp-auth-contention": [
        "email-skill",
        "wiki-yt",
        "www"
      ],
      "two-component-research-winnowing-pattern": [
        "www"
      ],
      "concept-1": [
        "www"
      ],
      "wikilink": [
        "www"
      ],
      "y": [
        "www"
      ],
      "prior-concept": [
        "www"
      ],
      "invariants-beat-environment-comfort": [
        "www"
      ],
      "research-applicability-checking-dont-cite-without-verifying-assumptions": [
        "www"
      ],
      "concept-2": [
        "www"
      ],
      "adaptive-research-depth-preventing-incomplete-www-coverage": [
        "www"
      ],
      "llm-instruction-non-compliance-activation-gap-2026": [
        "config-audit",
        "skill-prune"
      ],
      "structural-enforcement-for-skipped-rules-grok-build-2026": [
        "config-audit"
      ],
      "adhd-friendly-unified-todo-workspace-email-scanning": [
        "email-skill"
      ],
      "stateless-cli-vs-mcp-for-cross-agent-email-access": [
        "email-skill"
      ],
      "notebooklm-source-limits-free-vs-paid": [
        "nlm-bulk-ingest",
        "wiki-yt"
      ],
      "semantic-clustering-bounded-size": [
        "nlm-bulk-ingest"
      ],
      "nlm-to-wiki-optimization-opportunities": [
        "wiki-yt"
      ],
      "nlm-bulk-ingest": [
        "wiki-yt"
      ],
      "video-to-wiki-pipeline-transcript-extraction-multimodal": [
        "wiki-yt"
      ],
      "nlm-abc12345-concept-two": [
        "nlm-to-wiki"
      ],
      "nlm-abc12345-concept-one": [
        "nlm-to-wiki"
      ]
    },
    "capability_providers": {
      "session-retrospective": [
        "aar"
      ],
      "after-action-review": [
        "aar"
      ],
      "opportunity-landscape": [
        "aar"
      ],
      "value-accounting": [
        "aar"
      ],
      "cross-model-second-opinion": [
        "agy",
        "codex",
        "mmx"
      ],
      "gemini-reasoning": [
        "agy"
      ],
      "skill-routing": [
        "ask"
      ],
      "capture-coverage-check": [
        "capture"
      ],
      "improvement-opportunity-scan": [
        "capture"
      ],
      "proactive-knowledge-capture": [
        "capture"
      ],
      "session-close-accounting": [
        "close"
      ],
      "gate-resolution": [
        "close"
      ],
      "openai-reasoning": [
        "codex"
      ],
      "skill-scaffolding": [
        "create-skill"
      ],
      "design-doc-production": [
        "design"
      ],
      "systematic-debugging": [
        "diagnosing-bugs"
      ],
      "broken-link-detection": [
        "doc-check"
      ],
      "wikilink-resolution": [
        "doc-check"
      ],
      "skill-frontmatter-validation": [
        "doc-check"
      ],
      "code-fence-validation": [
        "doc-check"
      ],
      "repo-file-completeness": [
        "doc-check"
      ],
      "readme-staleness-detection": [
        "doc-check"
      ],
      "changelog-validation": [
        "doc-check"
      ],
      "documentation-readiness-check": [
        "doc-check"
      ],
      "domain-term-extraction": [
        "domain-terms"
      ],
      "offline-memory-consolidation": [
        "dream"
      ],
      "workflow-automation-analysis": [
        "friction"
      ],
      "friction-detection": [
        "friction"
      ],
      "verify-dispatch": [
        "go"
      ],
      "discovery-dispatch": [
        "go"
      ],
      "safe-git-preflight-dispatch": [
        "go"
      ],
      "parallel-implement-dispatch": [
        "go"
      ],
      "engineering-orchestration": [
        "go"
      ],
      "decision-tree-elicitation": [
        "grill-me"
      ],
      "requirements-elicitation": [
        "grill-me"
      ],
      "source-authority-discovery": [
        "grok-discovery"
      ],
      "parallel-fan-out": [
        "grok-parallel"
      ],
      "subagent-dispatch": [
        "check",
        "grok-parallel",
        "review",
        "tp",
        "www"
      ],
      "package-routing": [
        "grok-route"
      ],
      "git-safety-preflight": [
        "grok-safe-git"
      ],
      "completion-gate": [
        "grok-verify"
      ],
      "handoff-auto-update": [
        "handoff"
      ],
      "handoff-write": [
        "handoff"
      ],
      "cross-session-pattern-detection": [
        "harvest"
      ],
      "value-tracking": [
        "harvest"
      ],
      "obligation-lifecycle": [
        "harvest"
      ],
      "grok-documentation-help": [
        "help"
      ],
      "image-generation-guidance": [
        "imagine"
      ],
      "fleet-maintenance": [
        "maintain"
      ],
      "marketplace-skill-discovery": [
        "marketplace-bridge"
      ],
      "minimax-vision": [
        "mmx"
      ],
      "minimax-web-search": [
        "mmx"
      ],
      "cost-tracking": [
        "model-benchmark"
      ],
      "latency-benchmark": [
        "model-benchmark"
      ],
      "quality-scoring": [
        "model-benchmark"
      ],
      "model-discovery": [
        "model-discover"
      ],
      "quota-dashboard": [
        "model-quota"
      ],
      "conversation-selection": [
        "model-web"
      ],
      "browser-llm-bridge": [
        "model-web"
      ],
      "sse-response-capture": [
        "model-web"
      ],
      "fusion-portal-orchestration": [
        "model-web"
      ],
      "multi-model-ensemble": [
        "model-web"
      ],
      "model-web-advisory": [
        "model-web"
      ],
      "mid-conversation-observation-surfacing": [
        "notice"
      ],
      "file-pack": [
        "packet"
      ],
      "session-export": [
        "packet"
      ],
      "plan-writing": [
        "plan-writer"
      ],
      "prompting-techniques-reference": [
        "prompt-patterns"
      ],
      "session-recap-grok": [
        "recap-grok"
      ],
      "session-chain-walk": [
        "recap-grok"
      ],
      "structural-refactor": [
        "refactor"
      ],
      "task-refinement": [
        "refine"
      ],
      "code-review": [
        "review"
      ],
      "verified-findings-on-disk": [
        "review"
      ],
      "rrf-aggregation": [
        "search-fleet"
      ],
      "capability-routed-search": [
        "search-fleet"
      ],
      "ship-pipeline": [
        "ship"
      ],
      "verify-and-publish": [
        "ship"
      ],
      "skill-measurement": [
        "skill-dev"
      ],
      "skill-improvement": [
        "skill-dev"
      ],
      "thought-partner-realignment": [
        "slc"
      ],
      "behavioral-reset": [
        "slc"
      ],
      "persistent-task-store": [
        "tasks"
      ],
      "workspace-prioritized-action-list": [
        "todo"
      ],
      "critical-friend-critique": [
        "tp"
      ],
      "system-exploration": [
        "tp"
      ],
      "session-opportunity-review": [
        "tp"
      ],
      "logic-error-detection": [
        "trace"
      ],
      "manual-trace-verification": [
        "trace"
      ],
      "content-discipline-for-plans": [
        "wargame"
      ],
      "multi-backend-search": [
        "web"
      ],
      "rrf-merge": [
        "web"
      ],
      "feedback-to-wiki": [
        "why"
      ],
      "pattern-library-query": [
        "why"
      ],
      "root-cause-analysis": [
        "why"
      ],
      "wiki-write": [
        "wiki"
      ],
      "wiki-query": [
        "wiki"
      ],
      "web-ingestion": [
        "wiki-crawl4ai"
      ],
      "content-production": [
        "write"
      ],
      "wiki-web-wiki-research": [
        "www"
      ],
      "session-verification": [
        "check"
      ],
      "risk-priority-scoring": [
        "fmea"
      ],
      "failure-modes-analysis": [
        "fmea"
      ],
      "evidence-backed-inventory": [
        "preflight"
      ],
      "file-recovery": [
        "recover"
      ],
      "knowledge-hygiene": [
        "skill-prune"
      ]
    },
    "shared_services": {
      "reasoning-model-pool": [
        "aar",
        "tp",
        "why"
      ],
      "critic-model-pool": [
        "aar",
        "review",
        "tp"
      ],
      "exa": [
        "aar",
        "agy",
        "codex",
        "create-skill",
        "design",
        "dream",
        "go",
        "grok-parallel",
        "grok-verify",
        "handoff",
        "imagine",
        "mmx",
        "model-benchmark",
        "model-quota",
        "notice",
        "plan-writer",
        "prompt-patterns",
        "refactor",
        "refine",
        "review",
        "search-fleet",
        "skill-dev",
        "tasks",
        "todo",
        "web",
        "wiki",
        "wiki-crawl4ai"
      ],
      "nlm": [
        "aar",
        "gitingest",
        "go",
        "nlm",
        "nlm-to-wiki",
        "refactor"
      ],
      "gh": [
        "aar",
        "agy",
        "codex",
        "design",
        "dream",
        "go",
        "grok-discovery",
        "grok-parallel",
        "grok-safe-git",
        "grok-verify",
        "handoff",
        "imagine",
        "maintain",
        "mmx",
        "model-benchmark",
        "notice",
        "plan-writer",
        "prompt-patterns",
        "refactor",
        "refine",
        "review",
        "search-fleet",
        "skill-dev",
        "tasks",
        "todo",
        "wargame",
        "wiki",
        "wiki-crawl4ai",
        "www"
      ],
      "agy": [
        "agy",
        "ai-cli",
        "codex",
        "mmx",
        "model-benchmark",
        "search-fleet",
        "tasks",
        "tp"
      ],
      "codex": [
        "codex",
        "mmx",
        "model-benchmark",
        "resume-codex",
        "review",
        "tasks",
        "tp",
        "wargame"
      ],
      "mmx": [
        "design",
        "minimax-multimodal-toolkit",
        "minimax-music-gen",
        "minimax-music-playlist",
        "mmx",
        "model-benchmark",
        "model-quota",
        "search-fleet",
        "web",
        "wiki-yt",
        "www"
      ],
      "firecrawl": [
        "design",
        "firecrawl-agent",
        "firecrawl-cli",
        "firecrawl-crawl",
        "firecrawl-download",
        "firecrawl-interact",
        "firecrawl-map",
        "firecrawl-monitor",
        "firecrawl-parse",
        "firecrawl-scrape",
        "firecrawl-search",
        "model-quota",
        "search-fleet",
        "tp",
        "web",
        "wiki-crawl4ai",
        "www"
      ],
      "ddg": [
        "go",
        "search-fleet",
        "tp",
        "web",
        "www"
      ],
      "mechanical-model-pool": [
        "handoff",
        "harvest",
        "refine",
        "www"
      ],
      "tavily": [
        "model-quota",
        "search-fleet",
        "web"
      ],
      "perplexity": [
        "model-web",
        "search-fleet",
        "web"
      ],
      "search-research": [
        "prospect",
        "search-fleet",
        "web",
        "why"
      ],
      "reddit": [
        "search-fleet",
        "todo",
        "web",
        "www"
      ],
      "notebooklm": [
        "nlm",
        "todo",
        "web",
        "wiki-yt",
        "yt-nlm"
      ]
    }
  }
}
```

## Falsifier

This graph is wrong if:
- A skill delegates to another but no edge appears (false negative — pattern
  didn't match the phrasing). Fix: extend the pattern in build_skill_graph.py.
- An edge appears that doesn't represent a real dependency (false positive —
  skill mentions a tool name in a comment, not an active code path).
  Acceptable for discovery — verify before acting on any single edge.
- The graph is not regenerated after skill changes (drift). Run the script
  after any skill addition, removal, or dependency change.

## Provenance

Built 2026-07-28 after the web-search-prime disablement revealed that 8+
files needed updates but nothing tracked the dependency chain. The graph
answers "who uses this provider?" in one lookup instead of grepping the
entire workspace.
