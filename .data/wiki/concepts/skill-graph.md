---
title: "Skill dependency graph: who calls what and who consumes which providers"
created: 2026-08-13
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
| `agy` | 7 | `agy`, `ai-cli`, `codex`, `mmx`, `model-benchmark`, `search-fleet`, `tp` |
| `brave` | 2 | `go`, `web` |
| `chrome-devtools` | 2 | `chrome-devtools-cli`, `model-web` |
| `chrome-devtools-mcp-tools` | 1 | `model-web` |
| `codex` | 11 | `codex`, `codex-cli-runtime`, `executing-plans`, `mmx`, `model-benchmark`, `resume-codex`, `review`, `review-relay`, `talking-head-recut`, `tp`, `wargame` |
| `coding-model-pool` | 2 | `go`, `review` |
| `context7` | 2 | `claude-automation-recommender`, `refactor` |
| `critic-model-pool` | 3 | `aar`, `review`, `tp` |
| `ddg` | 5 | `go`, `search-fleet`, `tp`, `web`, `www` |
| `duckduckgo` | 2 | `bright-data-best-practices`, `web` |
| `episodic-memory` | 2 | `dream`, `remembering-conversations` |
| `exa` | 29 | `aar`, `agy`, `codex`, `create-skill`, `design`, `dream`, `exa-agent`, `exa-search`, `go`, `grok-parallel`, `grok-verify`, `handoff`, `imagine`, `mmx`, `model-benchmark`, `model-quota`, `notice`, `plan-writer`, `prompt-patterns`, `refactor`, `refine`, `review`, `search`, `search-fleet`, `skill-dev`, `todo`, `web`, `wiki`, `wiki-crawl4ai` |
| `firecrawl` | 17 | `design`, `firecrawl-agent`, `firecrawl-cli`, `firecrawl-crawl`, `firecrawl-download`, `firecrawl-interact`, `firecrawl-map`, `firecrawl-monitor`, `firecrawl-parse`, `firecrawl-scrape`, `firecrawl-search`, `model-quota`, `search-fleet`, `tp`, `web`, `wiki-crawl4ai`, `www` |
| `gh` | 28 | `aar`, `agy`, `codex`, `design`, `dream`, `go`, `grok-discovery`, `grok-parallel`, `grok-safe-git`, `grok-verify`, `handoff`, `imagine`, `maintain`, `mmx`, `model-benchmark`, `notice`, `plan-writer`, `prompt-patterns`, `refactor`, `refine`, `review`, `search-fleet`, `skill-dev`, `todo`, `wargame`, `wiki`, `wiki-crawl4ai`, `www` |
| `github-issues` | 1 | `www` |
| `hn-algolia` | 2 | `web`, `www` |
| `mechanical-model-pool` | 3 | `handoff`, `refine`, `www` |
| `minimax-search` | 1 | `design` |
| `mmx` | 11 | `design`, `minimax-multimodal-toolkit`, `minimax-music-gen`, `minimax-music-playlist`, `mmx`, `model-benchmark`, `model-quota`, `search-fleet`, `web`, `wiki-yt`, `www` |
| `nlm` | 6 | `aar`, `go`, `nlm`, `nlm-to-wiki`, `refactor`, `wiki-yt` |
| `notebooklm` | 5 | `nlm`, `todo`, `wiki-yt`, `wowerpoint`, `yt-nlm` |
| `perplexity` | 3 | `model-web`, `search-fleet`, `web` |
| `pwm` | 2 | `perplexity-web-mcp`, `search-fleet` |
| `reasoning-model-pool` | 3 | `aar`, `tp`, `why` |
| `reddit` | 4 | `search-fleet`, `todo`, `web`, `www` |
| `ruff` | 1 | `doc-check` |
| `search-research` | 4 | `prospect`, `search-fleet`, `web`, `why` |
| `spawn-subagent` | 4 | `close-py`, `ship-py`, `tp`, `why` |
| `stackexchange` | 1 | `web` |
| `tavily` | 10 | `academic-scientific-research`, `investment-research-briefs`, `model-quota`, `product-competitor-intelligence`, `sales-account-intelligence`, `search-fleet`, `tavily-web`, `threat-intelligence-enrichment`, `vendor-risk-kyc-screening`, `web` |

## Delegation targets (who calls this skill)

When a skill changes its interface or behavior, these callers are affected:

| Target skill | Caller count | Called by |
|-------------|-------------|-----------|
| `aar` | 15 | `ask`, `close-py`, `dream`, `handoff`, `insight`, `model-web`, `notice`, `packet`, `recap-grok`, `skill-dev`, `slc`, `todo`, `tp`, `wargame`, `why` |
| `agy` | 7 | `check`, `codex`, `mmx`, `model-web`, `search-fleet`, `tp`, `why` |
| `check` | 19 | `aar`, `ask`, `close-py`, `doc-check`, `doc-compiler`, `dream`, `go`, `grok-verify`, `model-benchmark`, `refactor`, `refine`, `review`, `ship-py`, `skill-dev`, `skill-to-page`, `todo`, `tp`, `triage`, `www` |
| `chrome-devtools` | 1 | `model-web` |
| `close` | 14 | `aar`, `ask`, `check`, `close-py`, `dream`, `handoff`, `insight`, `maintain`, `recap-grok`, `review`, `skill-dev`, `todo`, `tp`, `wiki` |
| `codex` | 5 | `codex-result-handling`, `mmx`, `model-web`, `tp`, `why` |
| `config-audit` | 1 | `maintain` |
| `crawl4ai` | 1 | `wiki-crawl4ai` |
| `create-skill` | 1 | `skill-dev` |
| `debrief` | 16 | `aar`, `behave`, `claude-audit`, `codex`, `dream`, `friction`, `handoff`, `improve`, `lmc`, `mlc`, `recap`, `recap-grok`, `retro`, `skill-audit`, `top-problems`, `tp` |
| `design` | 22 | `ask`, `behave`, `code`, `domain-terms`, `dream`, `evolve`, `execute-plan`, `go`, `grill-me`, `handoff`, `plan-writer`, `planning`, `prompt_refiner`, `recap`, `refine`, `s`, `specify`, `tp`, `wargame`, `web`, `why`, `www` |
| `diagnosing-bugs` | 1 | `ask-matt` |
| `doc-check` | 1 | `ship-py` |
| `domain-terms` | 1 | `grill-me` |
| `fmea` | 1 | `skill-dev` |
| `go` | 28 | `aar`, `ask`, `check`, `code`, `design`, `doc-check`, `grill-me`, `grok-go`, `grok-parallel`, `grok-sdlc`, `handoff`, `logfire-instrumentation`, `maintain`, `model-benchmark`, `notice`, `plan-writer`, `refactor`, `refine`, `req-check`, `review`, `rns`, `skill-dev`, `todo`, `tp`, `triage`, `wargame`, `why`, `www` |
| `grill-me` | 2 | `ask-matt`, `domain-terms` |
| `grok-discovery` | 2 | `go`, `grok-parallel` |
| `grok-parallel` | 2 | `go`, `notice` |
| `grok-route` | 3 | `go`, `grok-parallel`, `grok-verify` |
| `grok-safe-git` | 4 | `go`, `grok-parallel`, `grok-verify`, `ship-py` |
| `grok-verify` | 3 | `go`, `grok-parallel`, `skill-dev` |
| `handoff` | 29 | `aar`, `ask`, `ask-matt`, `behave`, `close-py`, `design`, `dream`, `go`, `insight`, `maintain`, `model-web`, `notice`, `packet`, `plan-writer`, `prompt-patterns`, `rca`, `recap`, `recap-grok`, `refactor`, `refine`, `review-relay`, `risk`, `ship-py`, `skill-dev`, `tp`, `triage`, `why`, `wiki`, `www` |
| `help` | 1 | `command-development` |
| `improve-codebase-architecture` | 3 | `ask-matt`, `check`, `diagnosing-bugs` |
| `insight` | 1 | `todo` |
| `maintain` | 5 | `insight`, `maintain-ifile`, `model-quota`, `skill-dev`, `todo` |
| `maintain-ifile` | 1 | `maintain` |
| `mmx` | 8 | `minimax-multimodal-toolkit`, `minimax-music-gen`, `model-quota`, `model-web`, `tp`, `web`, `why`, `wiki-yt` |
| `model-benchmark` | 1 | `model-discover` |
| `notice` | 2 | `skill-dev`, `slc` |
| `packet` | 1 | `tp` |
| `plan-writer` | 5 | `design`, `domain-terms`, `go`, `grill-me`, `refine` |
| `preflight` | 3 | `design`, `maintain-ifile`, `tp` |
| `recover` | 5 | `config-audit`, `main`, `maintain`, `skill-prune`, `workspace-health` |
| `red-team` | 13 | `claude-audit`, `debrief`, `fmea`, `improve`, `pre-mortem`, `preflight`, `redteam`, `retro`, `review`, `risk`, `risks`, `skill-audit`, `www` |
| `refactor` | 1 | `ship-py` |
| `refine` | 9 | `aar`, `design`, `domain-terms`, `dream`, `go`, `grill-me`, `handoff`, `plan-writer`, `refactor` |
| `review` | 32 | `aar`, `ask`, `behave`, `check`, `claude-audit`, `command-development`, `debrief`, `design-is`, `doc-check`, `domain-terms`, `dream`, `go`, `improve`, `insight`, `learn`, `maintain`, `marketplace-bridge`, `model-benchmark`, `plugin-structure`, `refactor`, `refine`, `review-pr`, `review-relay`, `risks`, `ship-py`, `skill-audit`, `skill-dev`, `sqd`, `todo`, `tp`, `triage`, `uci` |
| `risk` | 2 | `req-check`, `ship-py` |
| `skill-dev` | 8 | `create-skill`, `insight`, `maintain`, `maintain-ifile`, `ship-py`, `todo`, `tp`, `www` |
| `skill-prune` | 9 | `config-audit`, `create-skill`, `insight`, `maintain`, `maintain-ifile`, `skill-dev`, `todo`, `wiki`, `workspace-health` |
| `tdd` | 9 | `ask-matt`, `evolve`, `go`, `implement`, `planning`, `ralph`, `skill-similarity`, `subagent-driven-development`, `t` |
| `teach` | 1 | `ask-matt` |
| `test-driven-development` | 1 | `go` |
| `to-spec` | 1 | `ask-matt` |
| `to-tickets` | 1 | `ask-matt` |
| `todo` | 14 | `aar`, `ask`, `design`, `email-skill`, `insight`, `model-quota`, `recap-grok`, `refactor`, `review`, `risk`, `skill-dev`, `tp`, `wiki`, `www` |
| `tp` | 27 | `aar`, `ask`, `behave`, `design`, `domain-terms`, `dream`, `fmea`, `go`, `handoff`, `insight`, `maintain`, `model-benchmark`, `model-web`, `notice`, `plan-writer`, `recap-grok`, `refactor`, `refine`, `req-check`, `review`, `risk`, `skill-dev`, `slc`, `todo`, `triage`, `why`, `www` |
| `triage` | 2 | `ask-matt`, `setup-matt-pocock-skills` |
| `using-git-worktrees` | 1 | `go` |
| `wargame` | 3 | `plan-writer`, `req-check`, `risk` |
| `wayfinder` | 1 | `ask-matt` |
| `web` | 5 | `scraper-builder`, `tp`, `why`, `wiki-crawl4ai`, `www` |
| `why` | 17 | `aar`, `ask`, `behave`, `design`, `dream`, `model-benchmark`, `model-web`, `notice`, `rca`, `review`, `risk`, `skill-dev`, `todo`, `tp`, `triage`, `wargame`, `www` |
| `wiki` | 39 | `aar`, `claude-audit`, `close-py`, `create-skill`, `debrief`, `design`, `domain-terms`, `dream`, `go`, `grok-safe-git`, `handoff`, `improve`, `insight`, `main`, `maintain`, `maintain-ifile`, `model-benchmark`, `nlm-to-wiki`, `notice`, `plan-writer`, `prompt-patterns`, `rca`, `recap-grok`, `refactor`, `refine`, `req-check`, `review`, `risk`, `ship-py`, `skill-dev`, `todo`, `tp`, `ux`, `wargame`, `web`, `why`, `wiki-crawl4ai`, `wiki-yt`, `www` |
| `wiki-crawl4ai` | 1 | `www` |
| `wizard` | 1 | `ask-matt` |
| `writing-great-skills` | 1 | `ask-matt` |

## Capability registry (what functions the fleet provides)

Every capability the skill fleet declares via `provides:` frontmatter:

| Capability | Provided by |
|------------|-------------|
| `adversarial-review` | `risk` |
| `after-action-review` | `aar` |
| `anti-fabrication-close` | `close-py` |
| `behavioral-reset` | `slc` |
| `broken-link-detection` | `doc-check` |
| `browser-llm-bridge` | `model-web` |
| `capability-routed-search` | `search-fleet` |
| `capture-coverage-check` | `insight` |
| `changelog-validation` | `doc-check` |
| `close-verdict` | `close-py` |
| `code-fence-validation` | `doc-check` |
| `code-review` | `review` |
| `completion-gate` | `grok-verify` |
| `content-discipline-for-plans` | `wargame` |
| `content-production` | `write` |
| `conversation-selection` | `model-web` |
| `cost-tracking` | `model-benchmark` |
| `critical-friend-critique` | `tp` |
| `cross-model-second-opinion` | `agy`, `codex`, `mmx` |
| `decision-tree-elicitation` | `grill-me` |
| `design-doc-production` | `design` |
| `discovery-dispatch` | `go` |
| `documentation-readiness-check` | `doc-check` |
| `domain-term-extraction` | `domain-terms` |
| `engineering-orchestration` | `go` |
| `evidence-anchored-review` | `triage` |
| `evidence-backed-inventory` | `preflight` |
| `failure-modes-analysis` | `fmea` |
| `feedback-to-wiki` | `why` |
| `file-pack` | `packet` |
| `file-recovery` | `recover` |
| `finding-lifecycle` | `triage` |
| `fleet-maintenance` | `maintain` |
| `friction-detection` | `insight` |
| `fusion-portal-orchestration` | `model-web` |
| `gemini-reasoning` | `agy` |
| `git-safety-preflight` | `grok-safe-git` |
| `grok-documentation-help` | `help` |
| `handoff-auto-update` | `handoff` |
| `handoff-write` | `handoff` |
| `image-generation-guidance` | `imagine` |
| `improvement-opportunity-scan` | `insight` |
| `knowledge-hygiene` | `skill-prune` |
| `latency-benchmark` | `model-benchmark` |
| `logic-error-detection` | `trace` |
| `manual-trace-verification` | `trace` |
| `marketplace-skill-discovery` | `marketplace-bridge` |
| `mid-conversation-observation-surfacing` | `notice` |
| `minimax-image-generation` | `mmx` |
| `minimax-music-generation` | `mmx` |
| `minimax-speech-synthesis` | `mmx` |
| `minimax-video-generation` | `mmx` |
| `minimax-vision` | `mmx` |
| `minimax-web-search` | `mmx` |
| `model-discovery` | `model-discover` |
| `model-web-advisory` | `model-web` |
| `multi-backend-search` | `web` |
| `multi-model-ensemble` | `model-web` |
| `offline-memory-consolidation` | `dream` |
| `openai-reasoning` | `codex` |
| `opportunity-landscape` | `aar` |
| `package-routing` | `grok-route` |
| `parallel-fan-out` | `grok-parallel` |
| `parallel-implement-dispatch` | `go` |
| `pattern-library-query` | `why` |
| `plan-writing` | `plan-writer` |
| `proactive-knowledge-capture` | `insight` |
| `prompting-techniques-reference` | `prompt-patterns` |
| `public-readiness-gate` | `ship-py` |
| `quality-scoring` | `model-benchmark` |
| `quota-dashboard` | `model-quota` |
| `readme-staleness-detection` | `doc-check` |
| `repo-file-completeness` | `doc-check` |
| `requirements-elicitation` | `grill-me` |
| `risk-assessment` | `risk` |
| `risk-escalation` | `risk` |
| `risk-priority-scoring` | `fmea` |
| `risk-scan` | `risk` |
| `root-cause-analysis` | `rca`, `why` |
| `rrf-aggregation` | `search-fleet` |
| `rrf-merge` | `web` |
| `safe-git-preflight-dispatch` | `go` |
| `scan-code-quality` | `check`, `grok-verify`, `review`, `trace` |
| `scan-risk` | `risk`, `tp` |
| `scan-session-transcript` | `aar`, `insight`, `todo`, `triage` |
| `scan-workspace-state` | `maintain`, `skill-prune`, `todo` |
| `session-chain-walk` | `recap-grok` |
| `session-close-pipeline` | `close-py` |
| `session-export` | `packet` |
| `session-finding-triage` | `triage` |
| `session-opportunity-review` | `tp` |
| `session-recap-grok` | `recap-grok` |
| `session-retrospective` | `aar` |
| `session-verification` | `check` |
| `ship-pipeline` | `ship-py` |
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
| `verified-findings-on-disk` | `review` |
| `verify-and-publish` | `ship-py` |
| `verify-dispatch` | `go` |
| `web-ingestion` | `wiki-crawl4ai` |
| `wiki-query` | `wiki` |
| `wiki-web-wiki-research` | `www` |
| `wiki-write` | `wiki` |
| `wikilink-resolution` | `doc-check` |
| `workflow-automation-analysis` | `insight` |
| `workspace-prioritized-action-list` | `todo` |

## Shared services (used by 3+ skills)

Infrastructure that many skills depend on — capabilities and tools with
high consumer counts. Changes to these have fleet-wide blast radius.

| Service | Type | Consumer count | Skills |
|---------|------|---------------|--------|
| `cross-model-second-opinion` | capability | 3 | `agy`, `codex`, `mmx` |
| `scan-code-quality` | capability | 4 | `check`, `grok-verify`, `review`, `trace` |
| `scan-session-transcript` | capability | 4 | `aar`, `insight`, `todo`, `triage` |
| `scan-workspace-state` | capability | 3 | `maintain`, `skill-prune`, `todo` |
| `subagent-dispatch` | capability | 5 | `check`, `grok-parallel`, `review`, `tp`, `www` |
| `agy` | tool | 7 | `agy`, `ai-cli`, `codex`, `mmx`, `model-benchmark`, `search-fleet`, `tp` |
| `codex` | tool | 11 | `codex`, `codex-cli-runtime`, `executing-plans`, `mmx`, `model-benchmark`, `resume-codex`, `review`, `review-relay`... |
| `ddg` | tool | 5 | `go`, `search-fleet`, `tp`, `web`, `www` |
| `exa` | tool | 29 | `aar`, `agy`, `codex`, `create-skill`, `design`, `dream`, `exa-agent`, `exa-search`... |
| `firecrawl` | tool | 17 | `design`, `firecrawl-agent`, `firecrawl-cli`, `firecrawl-crawl`, `firecrawl-download`, `firecrawl-interact`, `firecrawl-map`, `firecrawl-monitor`... |
| `gh` | tool | 28 | `aar`, `agy`, `codex`, `design`, `dream`, `go`, `grok-discovery`, `grok-parallel`... |
| `mmx` | tool | 11 | `design`, `minimax-multimodal-toolkit`, `minimax-music-gen`, `minimax-music-playlist`, `mmx`, `model-benchmark`, `model-quota`, `search-fleet`... |
| `nlm` | tool | 6 | `aar`, `go`, `nlm`, `nlm-to-wiki`, `refactor`, `wiki-yt` |
| `notebooklm` | tool | 5 | `nlm`, `todo`, `wiki-yt`, `wowerpoint`, `yt-nlm` |
| `tavily` | tool | 10 | `academic-scientific-research`, `investment-research-briefs`, `model-quota`, `product-competitor-intelligence`, `sales-account-intelligence`, `search-fleet`, `tavily-web`, `threat-intelligence-enrichment`... |

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
| `minimax-image-generation` | `mmx` |
| `minimax-music-generation` | `mmx` |
| `minimax-speech-synthesis` | `mmx` |
| `minimax-video-generation` | `mmx` |
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
| `evidence-anchored-review` | `triage` |
| `evidence-backed-inventory` | `preflight` |
| `finding-lifecycle` | `triage` |
| `marketplace-skill-discovery` | `marketplace-bridge` |
| `model-discovery` | `model-discover` |
| `multi-backend-search` | `web` |
| `rrf-aggregation` | `search-fleet` |
| `rrf-merge` | `web` |
| `session-finding-triage` | `triage` |
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
| `quality-scoring` | `model-benchmark` |
| `scan-workspace-state` | `maintain`, `skill-prune`, `todo` |
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
| `anti-fabrication-close` | `close-py` |
| `behavioral-reset` | `slc` |
| `capture-coverage-check` | `insight` |
| `close-verdict` | `close-py` |
| `file-pack` | `packet` |
| `friction-detection` | `insight` |
| `handoff-auto-update` | `handoff` |
| `handoff-write` | `handoff` |
| `improvement-opportunity-scan` | `insight` |
| `logic-error-detection` | `trace` |
| `manual-trace-verification` | `trace` |
| `mid-conversation-observation-surfacing` | `notice` |
| `opportunity-landscape` | `aar` |
| `proactive-knowledge-capture` | `insight` |
| `root-cause-analysis` | `rca`, `why` |
| `scan-session-transcript` | `aar`, `insight`, `todo`, `triage` |
| `session-chain-walk` | `recap-grok` |
| `session-close-pipeline` | `close-py` |
| `session-export` | `packet` |
| `session-recap-grok` | `recap-grok` |
| `session-retrospective` | `aar` |
| `thought-partner-realignment` | `slc` |
| `value-accounting` | `aar` |
| `workflow-automation-analysis` | `insight` |

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
| `public-readiness-gate` | `ship-py` |
| `safe-git-preflight-dispatch` | `go` |
| `ship-pipeline` | `ship-py` |
| `verify-and-publish` | `ship-py` |
| `verify-dispatch` | `go` |

### review

| Capability | Skills |
|------------|--------|
| `adversarial-review` | `risk` |
| `code-review` | `review` |
| `content-discipline-for-plans` | `wargame` |
| `critical-friend-critique` | `tp` |
| `failure-modes-analysis` | `fmea` |
| `risk-assessment` | `risk` |
| `risk-escalation` | `risk` |
| `risk-priority-scoring` | `fmea` |
| `risk-scan` | `risk` |
| `scan-code-quality` | `check`, `grok-verify`, `review`, `trace` |
| `scan-risk` | `risk`, `tp` |
| `session-opportunity-review` | `tp` |
| `system-exploration` | `tp` |
| `verified-findings-on-disk` | `review` |

### self-improvement

| Capability | Skills |
|------------|--------|
| `fleet-maintenance` | `maintain` |
| `knowledge-hygiene` | `skill-prune` |
| `offline-memory-consolidation` | `dream` |
| `skill-improvement` | `skill-dev` |
| `skill-measurement` | `skill-dev` |
| `skill-scaffolding` | `create-skill` |

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
| `aar` | `check`, `close`, `debrief`, `go`, `handoff`, `refine`, `review`, `todo`, `tp`, `why`, `wiki` | `critic-model-pool`, `exa`, `gh`, `nlm`, `reasoning-model-pool` | `after-action-review`, `opportunity-landscape`, `scan-session-transcript`, `session-retrospective`, `value-accounting` |
| `academic-scientific-research` | — | `tavily` | — |
| `access` | — | — | — |
| `access` | — | — | — |
| `add-app-to-server` | — | — | — |
| `adhd` | — | — | — |
| `adr` | — | — | — |
| `agent` | — | — | — |
| `agent-development` | — | — | — |
| `agent-onboarding` | — | — | — |
| `agy` | — | `agy`, `exa`, `gh` | `cross-model-second-opinion`, `gemini-reasoning` |
| `agy` | — | — | — |
| `ai-api` | — | — | — |
| `ai-cli` | — | `agy` | — |
| `ai-models` | — | — | — |
| `ai-probe-benchmark` | — | — | — |
| `ai-probe-nim` | — | — | — |
| `ai-probe-openrouter` | — | — | — |
| `ai-probe-router` | — | — | — |
| `ask` | `aar`, `check`, `close`, `go`, `handoff`, `review`, `todo`, `tp`, `why` | — | `skill-routing` |
| `ask` | `design` | — | — |
| `ask-matt` | `diagnosing-bugs`, `grill-me`, `handoff`, `improve-codebase-architecture`, `tdd`, `teach`, `to-spec`, `to-tickets`, `triage`, `wayfinder`, `wizard` | — | — |
| `ask-matt` | `diagnosing-bugs`, `grill-me`, `handoff`, `improve-codebase-architecture`, `tdd`, `teach`, `to-spec`, `to-tickets`, `triage`, `wayfinder`, `writing-great-skills` | — | — |
| `autofix` | — | — | — |
| `av` | — | — | — |
| `avant-garde-ui` | — | — | — |
| `babysit` | — | — | — |
| `batch-grill-me` | — | — | — |
| `behave` | `debrief`, `design`, `handoff`, `review`, `tp`, `why` | — | — |
| `behave` | `debrief` | — | — |
| `bf` | — | — | — |
| `bifrost` | — | — | — |
| `brain` | — | — | — |
| `brainstorming` | — | — | — |
| `brainstorming` | — | — | — |
| `brand-listening` | — | — | — |
| `brd-browser-debug` | — | — | — |
| `bright-data-best-practices` | — | `duckduckgo` | — |
| `bright-data-mcp` | — | — | — |
| `brightdata-cli` | — | — | — |
| `browser-use` | — | — | — |
| `browser-use` | — | — | — |
| `browsing` | — | — | — |
| `build` | — | — | — |
| `build-mcp-app` | — | — | — |
| `build-mcp-server` | — | — | — |
| `build-mcpb` | — | — | — |
| `build-with-ai` | — | — | — |
| `building-pydantic-ai-agents` | — | — | — |
| `building-pydantic-ai-agents` | — | — | — |
| `captions-overlay` | — | — | — |
| `captions-overlay` | — | — | — |
| `capture` | — | — | — |
| `case-feedback-skill` | — | — | — |
| `cc-model-router` | — | — | — |
| `changelog` | — | — | — |
| `changelog-video` | — | — | — |
| `changelog-video` | — | — | — |
| `check` | `agy`, `close`, `go`, `review` | — | `scan-code-quality`, `session-verification`, `subagent-dispatch` |
| `check` | `go`, `improve-codebase-architecture` | — | — |
| `chrome-devtools` | — | — | — |
| `chrome-devtools-cli` | — | `chrome-devtools` | — |
| `chrome-extensions` | — | — | — |
| `cks` | — | — | — |
| `claude-audit` | `debrief`, `red-team`, `review`, `wiki` | — | — |
| `claude-automation-recommender` | — | `context7` | — |
| `claude-handoff` | — | — | — |
| `claude-handoff` | — | — | — |
| `claude-md-improver` | — | — | — |
| `claude-security` | — | — | — |
| `claudit` | — | — | — |
| `close-py` | `aar`, `check`, `close`, `handoff`, `wiki` | `spawn-subagent` | `anti-fabrication-close`, `close-verdict`, `session-close-pipeline` |
| `cloud-sync` | — | — | — |
| `code` | `design`, `go` | — | — |
| `code-flow-visualizer` | — | — | — |
| `code-review` | — | — | — |
| `code-review` | — | — | — |
| `code-review` | — | — | — |
| `code-review` | — | — | — |
| `code-review` | — | — | — |
| `codebase-design` | — | — | — |
| `codebase-design` | — | — | — |
| `codebase-to-course` | — | — | — |
| `codex` | `agy`, `debrief` | `agy`, `codex`, `exa`, `gh` | `cross-model-second-opinion`, `openai-reasoning` |
| `codex` | — | `codex` | — |
| `codex-cli-runtime` | — | `codex` | — |
| `codex-result-handling` | `codex` | — | — |
| `codspeed-optimize` | — | — | — |
| `codspeed-setup-harness` | — | — | — |
| `command-development` | `help`, `review` | — | — |
| `competitive-intel` | — | — | — |
| `concept-mapper` | — | — | — |
| `config-audit` | `recover`, `skill-prune` | — | — |
| `configure` | — | — | — |
| `configure` | — | — | — |
| `constitutional-patterns` | — | — | — |
| `constraints` | — | — | — |
| `contract-status` | — | — | — |
| `convert-web-app` | — | — | — |
| `create-mcp-app` | — | — | — |
| `create-skill` | `skill-dev`, `skill-prune`, `wiki` | `exa` | `skill-scaffolding` |
| `create-skill` | — | — | — |
| `create-workflow` | — | — | — |
| `csf-nip-integration` | — | — | — |
| `cut-the-curve` | — | — | — |
| `cut-the-curve` | — | — | — |
| `data-feeds` | — | — | — |
| `debrief` | `red-team`, `review`, `wiki` | — | — |
| `debt` | — | — | — |
| `debug-optimize-lcp` | — | — | — |
| `decision-tree` | — | — | — |
| `deepeval` | — | — | — |
| `deepeval-otel` | — | — | — |
| `deepeval-tracing` | — | — | — |
| `design` | `go`, `handoff`, `plan-writer`, `preflight`, `refine`, `todo`, `tp`, `why`, `wiki` | `exa`, `firecrawl`, `gh`, `mmx` | `design-doc-production` |
| `design` | `preflight` | `minimax-search` | — |
| `design` | `go` | — | — |
| `design-an-interface` | — | — | — |
| `design-codebase` | — | — | — |
| `design-doc-mermaid` | — | — | — |
| `design-frontend` | — | — | — |
| `design-is` | `review` | — | — |
| `design-mirror` | — | — | — |
| `developing-claude-code-plugins` | — | — | — |
| `diagnose` | — | — | — |
| `diagnosing-bugs` | `improve-codebase-architecture` | — | `systematic-debugging` |
| `diagnosing-bugs` | `improve-codebase-architecture` | — | — |
| `diagnosing-bugs` | `improve-codebase-architecture` | — | — |
| `discover-api` | — | — | — |
| `dispatching-parallel-agents` | — | — | — |
| `dispatching-parallel-agents` | — | — | — |
| `do` | — | — | — |
| `doc-check` | `check`, `go`, `review` | `ruff` | `broken-link-detection`, `changelog-validation`, `code-fence-validation`, `documentation-readiness-check`, `readme-staleness-detection`, `repo-file-completeness`, `skill-frontmatter-validation`, `wikilink-resolution` |
| `doc-compiler` | `check` | — | — |
| `docs` | — | — | — |
| `docx` | — | — | — |
| `domain-modeling` | — | — | — |
| `domain-modeling` | — | — | — |
| `domain-terms` | `design`, `grill-me`, `plan-writer`, `refine`, `review`, `tp`, `wiki` | — | `domain-term-extraction` |
| `dream` | `aar`, `check`, `close`, `debrief`, `design`, `handoff`, `refine`, `review`, `tp`, `why`, `wiki` | `episodic-memory`, `exa`, `gh` | `offline-memory-consolidation` |
| `dream` | — | — | — |
| `edit-article` | — | — | — |
| `email-skill` | `todo` | — | — |
| `embedded-captions` | — | — | — |
| `epistemic-check` | — | — | — |
| `evidence-driven-experiment-loop` | — | — | — |
| `evolve` | `design`, `tdd` | — | — |
| `exa-agent` | — | `exa` | — |
| `exa-search` | — | `exa` | — |
| `execute-plan` | `design` | — | — |
| `executing-plans` | — | `codex` | — |
| `executing-plans` | — | — | — |
| `execution-clarity` | — | — | — |
| `faceless-explainer` | — | — | — |
| `fetch` | — | — | — |
| `figma` | — | — | — |
| `finishing-a-development-branch` | — | — | — |
| `finishing-a-development-branch` | — | — | — |
| `firecrawl-agent` | — | — | — |
| `firecrawl-agent` | — | `firecrawl` | — |
| `firecrawl-cli` | — | `firecrawl` | — |
| `firecrawl-cli` | — | `firecrawl` | — |
| `firecrawl-crawl` | — | — | — |
| `firecrawl-crawl` | — | `firecrawl` | — |
| `firecrawl-download` | — | — | — |
| `firecrawl-download` | — | `firecrawl` | — |
| `firecrawl-interact` | — | — | — |
| `firecrawl-interact` | — | `firecrawl` | — |
| `firecrawl-map` | — | — | — |
| `firecrawl-map` | — | `firecrawl` | — |
| `firecrawl-monitor` | — | — | — |
| `firecrawl-monitor` | — | `firecrawl` | — |
| `firecrawl-parse` | — | — | — |
| `firecrawl-parse` | — | `firecrawl` | — |
| `firecrawl-scrape` | — | — | — |
| `firecrawl-scrape` | — | `firecrawl` | — |
| `firecrawl-search` | — | `firecrawl` | — |
| `firecrawl-search` | — | `firecrawl` | — |
| `fmea` | `red-team`, `tp` | — | `failure-modes-analysis`, `risk-priority-scoring` |
| `friction` | `debrief` | — | — |
| `frontend-design` | — | — | — |
| `frontend-dev` | — | — | — |
| `fullstack-dev` | — | — | — |
| `game-animation-frames` | — | — | — |
| `game-asset-core` | — | — | — |
| `game-character-consistency` | — | — | — |
| `game-tilesets` | — | — | — |
| `game-ui-icons` | — | — | — |
| `garden` | — | — | — |
| `general-video` | — | — | — |
| `genius` | — | — | — |
| `git` | — | — | — |
| `git-guardrails-claude-code` | — | — | — |
| `git-guardrails-claude-code` | — | — | — |
| `gitready` | — | — | — |
| `go` | `check`, `design`, `grok-discovery`, `grok-parallel`, `grok-route`, `grok-safe-git`, `grok-verify`, `handoff`, `plan-writer`, `refine`, `review`, `test-driven-development`, `tp`, `using-git-worktrees`, `wiki` | `brave`, `coding-model-pool`, `ddg`, `exa`, `gh`, `nlm` | `discovery-dispatch`, `engineering-orchestration`, `parallel-implement-dispatch`, `safe-git-preflight-dispatch`, `verify-dispatch` |
| `go` | `design`, `tdd` | — | — |
| `google-ai-usage-monitor` | — | — | — |
| `gpt-5-4-prompting` | — | — | — |
| `grill-me` | `design`, `domain-terms`, `go`, `plan-writer`, `refine` | — | `decision-tree-elicitation`, `requirements-elicitation` |
| `grill-me` | — | — | — |
| `grill-me` | — | — | — |
| `grill-with-docs` | — | — | — |
| `grill-with-docs` | — | — | — |
| `grilling` | — | — | — |
| `grilling` | — | — | — |
| `grok-discovery` | — | `gh` | `source-authority-discovery` |
| `grok-go` | `go` | — | — |
| `grok-parallel` | `go`, `grok-discovery`, `grok-route`, `grok-safe-git`, `grok-verify` | `exa`, `gh` | `parallel-fan-out`, `subagent-dispatch` |
| `grok-route` | — | — | `package-routing` |
| `grok-safe-git` | `wiki` | `gh` | `git-safety-preflight` |
| `grok-sdlc` | `go` | — | — |
| `grok-verify` | `check`, `grok-route`, `grok-safe-git` | `exa`, `gh` | `completion-gate`, `scan-code-quality` |
| `handoff` | `aar`, `close`, `debrief`, `design`, `go`, `refine`, `tp`, `wiki` | `exa`, `gh`, `mechanical-model-pool` | `handoff-auto-update`, `handoff-write` |
| `handoff` | — | — | — |
| `handoff` | — | — | — |
| `help` | — | — | `grok-documentation-help` |
| `hf-cli` | — | — | — |
| `hf-cloud-aws-context-discovery` | — | — | — |
| `hf-cloud-python-env-setup` | — | — | — |
| `hf-cloud-sagemaker-deployment-planner` | — | — | — |
| `hf-cloud-sagemaker-iam-preflight` | — | — | — |
| `hf-cloud-sagemaker-production-defaults` | — | — | — |
| `hf-cloud-serving-image-selection` | — | — | — |
| `hf-mcp` | — | — | — |
| `hf-mem` | — | — | — |
| `hook-development` | — | — | — |
| `how-it-works` | — | — | — |
| `huggingface-best` | — | — | — |
| `huggingface-community-evals` | — | — | — |
| `huggingface-datasets` | — | — | — |
| `huggingface-gradio` | — | — | — |
| `huggingface-llm-trainer` | — | — | — |
| `huggingface-local-models` | — | — | — |
| `huggingface-lora-space-builder` | — | — | — |
| `huggingface-paper-publisher` | — | — | — |
| `huggingface-papers` | — | — | — |
| `huggingface-spaces` | — | — | — |
| `huggingface-tool-builder` | — | — | — |
| `huggingface-trackio` | — | — | — |
| `huggingface-vision-trainer` | — | — | — |
| `huggingface-zerogpu` | — | — | — |
| `hyperframes` | — | — | — |
| `hyperframes-animation` | — | — | — |
| `hyperframes-cli` | — | — | — |
| `hyperframes-core` | — | — | — |
| `hyperframes-creative` | — | — | — |
| `hyperframes-keyframes` | — | — | — |
| `hyperframes-registry` | — | — | — |
| `id` | — | — | — |
| `imagine` | — | `exa`, `gh` | `image-generation-guidance` |
| `imagine` | — | — | — |
| `implement` | — | — | — |
| `implement` | `tdd` | — | — |
| `implement` | `tdd` | — | — |
| `improve` | `debrief`, `red-team`, `review`, `wiki` | — | — |
| `improve-codebase-architecture` | — | — | — |
| `improve-codebase-architecture` | — | — | — |
| `improve-codebase-architecture` | — | — | — |
| `improve-codebase-architecture` | — | — | — |
| `index` | — | — | — |
| `init` | — | — | — |
| `insight` | `aar`, `close`, `handoff`, `maintain`, `review`, `skill-dev`, `skill-prune`, `todo`, `tp`, `wiki` | — | `capture-coverage-check`, `friction-detection`, `improvement-opportunity-scan`, `proactive-knowledge-capture`, `scan-session-transcript`, `workflow-automation-analysis` |
| `intelligence-stream-analyze` | — | — | — |
| `intelligence-stream-ingest` | — | — | — |
| `investment-research-briefs` | — | `tavily` | — |
| `js-sdk-best-practices` | — | — | — |
| `knowledge` | — | — | — |
| `knowledge-agent` | — | — | — |
| `langfuse` | — | — | — |
| `learn` | `review` | — | — |
| `learn-codebase` | — | — | — |
| `live-research` | — | — | — |
| `lmc` | `debrief` | — | — |
| `logfire-instrumentation` | `go` | — | — |
| `logfire-instrumentation` | `go` | — | — |
| `logfire-query` | — | — | — |
| `logfire-query` | — | — | — |
| `logfire-ui` | — | — | — |
| `logfire-ui` | — | — | — |
| `loop-me` | — | — | — |
| `loop-me` | — | — | — |
| `main` | `recover`, `wiki` | — | — |
| `main-review` | — | — | — |
| `maintain` | `close`, `config-audit`, `go`, `handoff`, `maintain-ifile`, `recover`, `review`, `skill-dev`, `skill-prune`, `tp`, `wiki` | `gh` | `fleet-maintenance`, `scan-workspace-state` |
| `maintain-ifile` | `maintain`, `preflight`, `skill-dev`, `skill-prune`, `wiki` | — | — |
| `make-plan` | — | — | — |
| `marketplace-bridge` | `review` | — | `marketplace-skill-discovery` |
| `mcp-integration` | — | — | — |
| `media-use` | — | — | — |
| `mem-search` | — | — | — |
| `memory-leak-debugging` | — | — | — |
| `mermaid-c4` | — | — | — |
| `migrate-oai-app` | — | — | — |
| `migrate-to-shoehorn` | — | — | — |
| `migrate-to-shoehorn` | — | — | — |
| `minimax-multimodal-toolkit` | `mmx` | `mmx` | — |
| `minimax-music-gen` | `mmx` | `mmx` | — |
| `minimax-music-playlist` | — | `mmx` | — |
| `mlc` | `debrief` | — | — |
| `mm-quota` | — | — | — |
| `mmx` | `agy`, `codex` | `agy`, `codex`, `exa`, `gh`, `mmx` | `cross-model-second-opinion`, `minimax-image-generation`, `minimax-music-generation`, `minimax-speech-synthesis`, `minimax-video-generation`, `minimax-vision`, `minimax-web-search` |
| `mode-creator` | — | — | — |
| `model-benchmark` | `check`, `go`, `review`, `tp`, `why`, `wiki` | `agy`, `codex`, `exa`, `gh`, `mmx` | `cost-tracking`, `latency-benchmark`, `quality-scoring` |
| `model-discover` | `model-benchmark` | — | `model-discovery` |
| `model-quota` | `maintain`, `mmx`, `todo` | `exa`, `firecrawl`, `mmx`, `tavily` | `quota-dashboard` |
| `model-web` | `aar`, `agy`, `chrome-devtools`, `codex`, `handoff`, `mmx`, `tp`, `why` | `chrome-devtools`, `chrome-devtools-mcp-tools`, `perplexity` | `browser-llm-bridge`, `conversation-selection`, `fusion-portal-orchestration`, `model-web-advisory`, `multi-model-ensemble`, `sse-response-capture` |
| `modern-web-guidance` | — | — | — |
| `motion-doctrine` | — | — | — |
| `motion-doctrine` | — | — | — |
| `motion-graphics` | — | — | — |
| `music-to-video` | — | — | — |
| `nlm` | — | `nlm`, `notebooklm` | — |
| `nlm-bulk-ingest` | — | — | — |
| `nlm-to-wiki` | `wiki` | `nlm` | — |
| `notebooklm` | — | — | — |
| `notice` | `aar`, `go`, `grok-parallel`, `handoff`, `tp`, `why`, `wiki` | `exa`, `gh` | `mid-conversation-observation-surfacing` |
| `obsidian-vault` | — | — | — |
| `oh-my-issues` | — | — | — |
| `oversized-cursor` | — | — | — |
| `oversized-cursor` | — | — | — |
| `pace` | — | — | — |
| `packet` | `aar`, `handoff` | — | `file-pack`, `session-export` |
| `pathfinder` | — | — | — |
| `pdf` | — | — | — |
| `perf` | — | — | — |
| `performance-profiler` | — | — | — |
| `perplexity-web-mcp` | — | `pwm` | — |
| `pi-cli-runtime` | — | — | — |
| `pi-cross-verify` | — | — | — |
| `pi-result-handling` | — | — | — |
| `pi-routing` | — | — | — |
| `plan-writer` | `design`, `go`, `handoff`, `refine`, `tp`, `wargame`, `wiki` | `exa`, `gh` | `plan-writing` |
| `planning` | `design`, `tdd` | — | — |
| `playground` | — | — | — |
| `plugin-installer` | — | — | — |
| `plugin-settings` | — | — | — |
| `plugin-structure` | `review` | — | — |
| `pptx` | — | — | — |
| `pr-babysit` | — | — | — |
| `pr-to-video` | — | — | — |
| `pre-mortem` | `red-team` | — | — |
| `preflight` | `red-team` | — | `evidence-backed-inventory` |
| `preflight` | — | — | — |
| `price-comparison` | — | — | — |
| `prime` | — | — | — |
| `probe` | — | — | — |
| `product-competitor-intelligence` | — | `tavily` | — |
| `product-launch-video` | — | — | — |
| `professional-greeting` | — | — | — |
| `profile` | — | — | — |
| `project-artifact` | — | — | — |
| `prompt-enhancer` | — | — | — |
| `prompt-patterns` | `handoff`, `wiki` | `exa`, `gh` | `prompting-techniques-reference` |
| `prompt_refiner` | `design` | — | — |
| `prospect` | — | `search-research` | — |
| `prototype` | — | — | — |
| `prototype` | — | — | — |
| `proxy` | — | — | — |
| `pydantic` | — | — | — |
| `pydantic` | — | — | — |
| `pydantic-ai-harness` | — | — | — |
| `pydantic-ai-harness` | — | — | — |
| `python-sdk-best-practices` | — | — | — |
| `qa` | — | — | — |
| `qa` | — | — | — |
| `qmd-wiki` | — | — | — |
| `quota` | — | — | — |
| `rag-pipeline` | — | — | — |
| `ralph` | `tdd` | — | — |
| `rca` | `handoff`, `why`, `wiki` | — | `root-cause-analysis` |
| `rca` | — | — | — |
| `reason` | — | — | — |
| `recap` | `debrief`, `design`, `handoff` | — | — |
| `recap-grok` | `aar`, `close`, `debrief`, `handoff`, `todo`, `tp`, `wiki` | — | `session-chain-walk`, `session-recap-grok` |
| `receiving-code-review` | — | — | — |
| `recover` | — | — | `file-recovery` |
| `recover` | — | — | — |
| `redteam` | `red-team` | — | — |
| `refactor` | `check`, `go`, `handoff`, `refine`, `review`, `todo`, `tp`, `wiki` | `context7`, `exa`, `gh`, `nlm` | `structural-refactor` |
| `refactor` | — | — | — |
| `refine` | `check`, `design`, `go`, `handoff`, `plan-writer`, `review`, `tp`, `wiki` | `exa`, `gh`, `mechanical-model-pool` | `task-refinement` |
| `reflect` | — | — | — |
| `refresh` | — | — | — |
| `remembering-conversations` | — | `episodic-memory` | — |
| `remotion-to-hyperframes` | — | — | — |
| `req-check` | `go`, `risk`, `tp`, `wargame`, `wiki` | — | — |
| `request-refactor-plan` | — | — | — |
| `requesting-code-review` | — | — | — |
| `research` | — | — | — |
| `research` | — | — | — |
| `research` | — | — | — |
| `resolving-merge-conflicts` | — | — | — |
| `resolving-merge-conflicts` | — | — | — |
| `response-atomicity` | — | — | — |
| `resume-claude` | — | — | — |
| `resume-codex` | — | `codex` | — |
| `resume-cursor` | — | — | — |
| `retro` | `debrief`, `red-team` | — | — |
| `review` | `check`, `close`, `go`, `red-team`, `todo`, `tp`, `why`, `wiki` | `codex`, `coding-model-pool`, `critic-model-pool`, `exa`, `gh` | `code-review`, `scan-code-quality`, `subagent-dispatch`, `verified-findings-on-disk` |
| `review` | — | — | — |
| `review` | `red-team` | — | — |
| `review-pr` | `review` | — | — |
| `review-relay` | `handoff`, `review` | `codex` | — |
| `review_bundle` | — | — | — |
| `risk` | `handoff`, `red-team`, `todo`, `tp`, `wargame`, `why`, `wiki` | — | `adversarial-review`, `risk-assessment`, `risk-escalation`, `risk-scan`, `scan-risk` |
| `risks` | `red-team`, `review` | — | — |
| `rns` | `go` | — | — |
| `s` | `design` | — | — |
| `sales-account-intelligence` | — | `tavily` | — |
| `scaffold-exercises` | — | — | — |
| `scaffold-exercises` | — | — | — |
| `scrape` | — | — | — |
| `scraper-builder` | `web` | — | — |
| `scraper-studio` | — | — | — |
| `seam-craft` | — | — | — |
| `seam-craft` | — | — | — |
| `search` | — | `exa` | — |
| `search` | — | — | — |
| `search` | — | — | — |
| `search-fleet` | `agy` | `agy`, `ddg`, `exa`, `firecrawl`, `gh`, `mmx`, `perplexity`, `pwm`, `reddit`, `search-research`, `tavily` | `capability-routed-search`, `rrf-aggregation` |
| `searching-sourcegraph` | — | — | — |
| `seo-audit` | — | — | — |
| `sequential-thinking` | — | — | — |
| `setup-matt-pocock-skills` | `triage` | — | — |
| `setup-matt-pocock-skills` | `triage` | — | — |
| `setup-pre-commit` | — | — | — |
| `setup-pre-commit` | — | — | — |
| `setup-ts-deep-modules` | — | — | — |
| `setup-ts-deep-modules` | — | — | — |
| `ship` | — | — | — |
| `ship-py` | `check`, `doc-check`, `grok-safe-git`, `handoff`, `refactor`, `review`, `risk`, `skill-dev`, `wiki` | `spawn-subagent` | `public-readiness-gate`, `ship-pipeline`, `verify-and-publish` |
| `simplify-enhanced` | — | — | — |
| `skeptic` | — | — | — |
| `skill-audit` | `debrief`, `red-team`, `review` | — | — |
| `skill-creator` | — | — | — |
| `skill-creator` | — | — | — |
| `skill-design-principles` | — | — | — |
| `skill-dev` | `aar`, `check`, `close`, `create-skill`, `fmea`, `go`, `grok-verify`, `handoff`, `maintain`, `notice`, `review`, `skill-prune`, `todo`, `tp`, `why`, `wiki` | `exa`, `gh` | `skill-improvement`, `skill-measurement` |
| `skill-development` | — | — | — |
| `skill-from-docs` | — | — | — |
| `skill-prune` | `recover` | — | `knowledge-hygiene`, `scan-workspace-state` |
| `skill-similarity` | `tdd` | — | — |
| `skill-to-page` | `check` | — | — |
| `skill-write` | — | — | — |
| `slc` | `aar`, `notice`, `tp` | — | `behavioral-reset`, `thought-partner-realignment` |
| `slc` | — | — | — |
| `slideshow` | — | — | — |
| `smart-explore` | — | — | — |
| `snapshot` | — | — | — |
| `solo-dev-authority` | — | — | — |
| `specify` | `design` | — | — |
| `sqa` | — | — | — |
| `sqd` | `review` | — | — |
| `stale` | — | — | — |
| `standup` | — | — | — |
| `status` | — | — | — |
| `subagent-driven-development` | — | — | — |
| `subagent-driven-development` | `tdd` | — | — |
| `systematic-debugging` | — | — | — |
| `t` | `tdd` | — | — |
| `talking-head-recut` | — | `codex` | — |
| `task` | — | — | — |
| `tasks` | — | — | — |
| `tavily-best-practices` | — | — | — |
| `tavily-web` | — | `tavily` | — |
| `tdd` | — | — | — |
| `tdd` | — | — | — |
| `tdd` | — | — | — |
| `tdd` | — | — | — |
| `teach` | — | — | — |
| `teach` | — | — | — |
| `teach` | — | — | — |
| `team` | — | — | — |
| `test-driven-development` | — | — | — |
| `threat-intelligence-enrichment` | — | `tavily` | — |
| `tilldone` | — | — | — |
| `timeline-report` | — | — | — |
| `tinyfish-authenticated` | — | — | — |
| `tinyfish-automation` | — | — | — |
| `tinyfish-browser` | — | — | — |
| `tinyfish-research` | — | — | — |
| `tinyfish-web` | — | — | — |
| `tldr-code` | — | — | — |
| `tldr-deep` | — | — | — |
| `tldr-overview` | — | — | — |
| `tldr-router` | — | — | — |
| `tldr-stats` | — | — | — |
| `to-questionnaire` | — | — | — |
| `to-questionnaire` | — | — | — |
| `to-spec` | — | — | — |
| `to-spec` | — | — | — |
| `to-spec` | — | — | — |
| `to-tickets` | — | — | — |
| `to-tickets` | — | — | — |
| `to-tickets` | — | — | — |
| `todo` | `aar`, `check`, `close`, `go`, `insight`, `maintain`, `review`, `skill-dev`, `skill-prune`, `tp`, `why`, `wiki` | `exa`, `gh`, `notebooklm`, `reddit` | `scan-session-transcript`, `scan-workspace-state`, `workspace-prioritized-action-list` |
| `top-problems` | `debrief` | — | — |
| `tot` | — | — | — |
| `tp` | `aar`, `agy`, `check`, `close`, `codex`, `debrief`, `design`, `go`, `handoff`, `mmx`, `packet`, `preflight`, `review`, `skill-dev`, `todo`, `web`, `why`, `wiki` | `agy`, `codex`, `critic-model-pool`, `ddg`, `firecrawl`, `reasoning-model-pool`, `spawn-subagent` | `critical-friend-critique`, `scan-risk`, `session-opportunity-review`, `subagent-dispatch`, `system-exploration` |
| `trace` | — | — | `logic-error-detection`, `manual-trace-verification`, `scan-code-quality` |
| `trace` | — | — | — |
| `train-sentence-transformers` | — | — | — |
| `transformers-js` | — | — | — |
| `triage` | `check`, `go`, `handoff`, `review`, `tp`, `why` | — | `evidence-anchored-review`, `finding-lifecycle`, `scan-session-transcript`, `session-finding-triage` |
| `triage` | — | — | — |
| `triage` | — | — | — |
| `trl-training` | — | — | — |
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
| `vendor-risk-kyc-screening` | — | `tavily` | — |
| `verification-before-completion` | — | — | — |
| `verification-before-completion` | — | — | — |
| `version-bump` | — | — | — |
| `video-vision` | — | — | — |
| `vision-analysis` | — | — | — |
| `wait-what` | — | — | — |
| `wargame` | `aar`, `design`, `go`, `why`, `wiki` | `codex`, `gh` | `content-discipline-for-plans` |
| `wayfinder` | — | — | — |
| `wayfinder` | — | — | — |
| `wayfinder` | — | — | — |
| `web` | `design`, `mmx`, `wiki` | `brave`, `ddg`, `duckduckgo`, `exa`, `firecrawl`, `hn-algolia`, `mmx`, `perplexity`, `reddit`, `search-research`, `stackexchange`, `tavily` | `multi-backend-search`, `rrf-merge` |
| `weekly-digests` | — | — | — |
| `what-the` | — | — | — |
| `why` | `aar`, `agy`, `codex`, `design`, `go`, `handoff`, `mmx`, `tp`, `web`, `wiki` | `reasoning-model-pool`, `spawn-subagent` | `feedback-to-wiki`, `pattern-library-query`, `root-cause-analysis` |
| `why` | — | `search-research` | — |
| `wiki` | `close`, `handoff`, `skill-prune`, `todo` | `exa`, `gh` | `wiki-query`, `wiki-write` |
| `wiki` | — | — | — |
| `wiki-crawl4ai` | `crawl4ai`, `web`, `wiki` | `exa`, `firecrawl`, `gh` | `web-ingestion` |
| `wiki-yt` | `mmx`, `wiki` | `mmx`, `nlm`, `notebooklm` | — |
| `wizard` | — | — | — |
| `wizard` | — | — | — |
| `wizard` | — | — | — |
| `workflow` | — | — | — |
| `working-with-claude-code` | — | — | — |
| `workspace-health` | `recover`, `skill-prune` | — | — |
| `wowerpoint` | — | `notebooklm` | — |
| `write` | — | — | `content-production` |
| `writing-beats` | — | — | — |
| `writing-beats` | — | — | — |
| `writing-clearly-and-concisely` | — | — | — |
| `writing-for-agents` | — | — | — |
| `writing-fragments` | — | — | — |
| `writing-fragments` | — | — | — |
| `writing-great-skills` | — | — | — |
| `writing-great-skills` | — | — | — |
| `writing-plans` | — | — | — |
| `writing-plans` | — | — | — |
| `writing-rules` | — | — | — |
| `writing-shape` | — | — | — |
| `writing-shape` | — | — | — |
| `writing-skills` | — | — | — |
| `writing-skills` | — | — | — |
| `www` | `check`, `design`, `go`, `handoff`, `red-team`, `skill-dev`, `todo`, `tp`, `web`, `why`, `wiki`, `wiki-crawl4ai` | `ddg`, `firecrawl`, `gh`, `github-issues`, `hn-algolia`, `mechanical-model-pool`, `mmx`, `reddit` | `subagent-dispatch`, `wiki-web-wiki-research` |
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
        "refine",
        "review",
        "todo",
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
        "scan-session-transcript",
        "session-retrospective",
        "value-accounting"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "adhd",
      "path": "C:\\Users\\brsth\\.grok\\skills\\adhd\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "agy",
      "path": "C:\\Users\\brsth\\.grok\\skills\\agy\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
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
        "aar",
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
      "name": "brain",
      "path": "C:\\Users\\brsth\\.grok\\skills\\brain\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "close-py",
      "path": "C:\\Users\\brsth\\.grok\\skills\\close-py\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "check",
        "close",
        "handoff",
        "wiki"
      ],
      "consumes_provider": [
        "spawn-subagent"
      ],
      "references_wiki": [
        "pipeline-detect-phase-state-reset-sequential-contamination",
        "skill-pipeline-integration-testing"
      ],
      "provides": [
        "anti-fabrication-close",
        "close-verdict",
        "session-close-pipeline"
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
        "why",
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
        "consistency-drift-as-waste-source-in-iterative-refinement",
        "design-choice-audit-challenge-every-decision-against-first-principles",
        "design-doc-conformance-check-procedure",
        "exemption-logic-as-conflict-signal",
        "invariants-beat-environment-comfort",
        "llm-synthesis-quality-and-speed-techniques",
        "multi-model-ensemble-design-patterns-for-agent-skills",
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
      "name": "design-doc-mermaid",
      "path": "C:\\Users\\brsth\\.grok\\skills\\design-doc-mermaid\\SKILL.md",
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
        "page"
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
        "test-driven-development",
        "tp",
        "using-git-worktrees",
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
        "design-choice-audit-challenge-every-decision-against-first-principles",
        "framing-check-pattern",
        "prompting-patterns-for-ai-agent-control",
        "scatter-gather-for-single-artifact-parallel-analysis",
        "solution-unit-validation-before-build",
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
        "completion-gate",
        "scan-code-quality"
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
      "name": "insight",
      "path": "C:\\Users\\brsth\\.grok\\skills\\insight\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "close",
        "handoff",
        "maintain",
        "review",
        "skill-dev",
        "skill-prune",
        "todo",
        "tp",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "insight-skill-consolidates-capture-friction-harvest",
        "signal-prioritization-for-improvement-detection"
      ],
      "provides": [
        "capture-coverage-check",
        "friction-detection",
        "improvement-opportunity-scan",
        "proactive-knowledge-capture",
        "scan-session-transcript",
        "workflow-automation-analysis"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "maintain",
      "path": "C:\\Users\\brsth\\.grok\\skills\\maintain\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "close",
        "config-audit",
        "go",
        "handoff",
        "maintain-ifile",
        "recover",
        "review",
        "skill-dev",
        "skill-prune",
        "tp",
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
        "fleet-maintenance",
        "scan-workspace-state"
      ],
      "domain": "self-improvement"
    },
    {
      "name": "maintain-ifile",
      "path": "C:\\Users\\brsth\\.grok\\skills\\maintain-ifile\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "maintain",
        "preflight",
        "skill-dev",
        "skill-prune",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "agents-md-construction-best-practices",
        "agents-md-optimization-tools-landscape-2026",
        "enforcement-hierarchy-and-compaction-strategy",
        "llm-instruction-non-compliance-activation-gap-2026"
      ],
      "provides": [],
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
        "minimax-image-generation",
        "minimax-music-generation",
        "minimax-speech-synthesis",
        "minimax-video-generation",
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
        "model-benchmark-testing-quirks",
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
        "chrome-devtools",
        "codex",
        "handoff",
        "mmx",
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
        "chrome-job-object-escape-via-task-scheduler",
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
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "compaction-inherited-recommendation-decoupling",
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
        "design-choice-audit-challenge-every-decision-against-first-principles",
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
      "name": "rca",
      "path": "C:\\Users\\brsth\\.grok\\skills\\rca\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "handoff",
        "why",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "root-cause-analysis"
      ],
      "domain": "lifecycle"
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
      "name": "redteam",
      "path": "C:\\Users\\brsth\\.grok\\skills\\redteam\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "red-team"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
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
        "todo",
        "tp",
        "wiki"
      ],
      "consumes_provider": [
        "context7",
        "exa",
        "gh",
        "nlm"
      ],
      "references_wiki": [
        "agentic-sdlc-skill-lifecycle-architecture",
        "design-choice-audit-challenge-every-decision-against-first-principles",
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
      "name": "req-check",
      "path": "C:\\Users\\brsth\\.grok\\skills\\req-check\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "go",
        "risk",
        "tp",
        "wargame",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "great-adversarial-review-skill-design-patterns",
        "x"
      ],
      "provides": [],
      "domain": "review"
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
        "todo",
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
        "fix-introduces-regression-by-trading-properties",
        "multi-model-ensemble-design-patterns-for-agent-skills",
        "scatter-gather-for-single-artifact-parallel-analysis"
      ],
      "provides": [
        "code-review",
        "scan-code-quality",
        "subagent-dispatch",
        "verified-findings-on-disk"
      ],
      "domain": "review"
    },
    {
      "name": "review-relay",
      "path": "C:\\Users\\brsth\\.grok\\skills\\review-relay\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "handoff",
        "review"
      ],
      "consumes_provider": [
        "codex"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "risk",
      "path": "C:\\Users\\brsth\\.grok\\skills\\risk\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "handoff",
        "red-team",
        "todo",
        "tp",
        "wargame",
        "why",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "adaptive-expansion-evidence-triggered-conditional-steps",
        "blind-spot-detection-methods",
        "concurrent-cdp-auth-contention",
        "design-doc-conformance-check-procedure",
        "great-adversarial-review-skill-design-patterns",
        "invariants-beat-environment-comfort"
      ],
      "provides": [
        "adversarial-review",
        "risk-assessment",
        "risk-escalation",
        "risk-scan",
        "scan-risk"
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
      "name": "ship-py",
      "path": "C:\\Users\\brsth\\.grok\\skills\\ship-py\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "doc-check",
        "grok-safe-git",
        "handoff",
        "refactor",
        "review",
        "risk",
        "skill-dev",
        "wiki"
      ],
      "consumes_provider": [
        "spawn-subagent"
      ],
      "references_wiki": [
        "skill-pipeline-integration-testing",
        "specification-gaming-in-llm-agent-pipelines"
      ],
      "provides": [
        "public-readiness-gate",
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
        "go",
        "grok-verify",
        "handoff",
        "maintain",
        "notice",
        "review",
        "skill-prune",
        "todo",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "blind-spot-detection-methods",
        "claude-side-skill-improvement-tooling-2026",
        "code-output-passthrough-narration-over-script-output",
        "cross-invocation-skills-proactively-suggest-complementary-skills",
        "execution-receipts-for-executable-artifacts",
        "mechanical-enforcement-of-llm-skill-steps-2026",
        "self-reflective-gap-discovery-indirect-hunting-prompts",
        "skill-catalog",
        "skill-development-portfolio",
        "skill-effectiveness-measurement-gaps-trigger-accuracy-token-efficiency",
        "skill-management-in-agentic-systems-research-survey",
        "skill-pipeline-integration-testing",
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
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
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
        "aar",
        "check",
        "close",
        "go",
        "insight",
        "maintain",
        "review",
        "skill-dev",
        "skill-prune",
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
        "evidence-first-default-and-needless-confirmation",
        "externalized-verification-over-intrinsic-self-correction",
        "llm-judgment-hooks",
        "no-question-theater",
        "signal-based-intent-expansion"
      ],
      "provides": [
        "scan-session-transcript",
        "scan-workspace-state",
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
        "handoff",
        "mmx",
        "packet",
        "preflight",
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
        "design-choice-audit-challenge-every-decision-against-first-principles",
        "design-doc-conformance-check-procedure",
        "inter-skill-output-bridges-and-temporal-surfacing-layers",
        "markdown-mermaid-rendering-agentic-clis-windows-11",
        "mechanical-as-input-not-mechanical-as-frame",
        "model-fit-and-post-hoc-behavioral-detection",
        "model-pool-not-chain",
        "model-pool-selection-policy-speed-quota-diversity",
        "model-tool-calling-capability-matrix",
        "research-quality-principle-efficiency-not-censorship",
        "signal-based-intent-expansion",
        "skill-catalog",
        "tool-fallbacks"
      ],
      "provides": [
        "critical-friend-critique",
        "scan-risk",
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
        "manual-trace-verification",
        "scan-code-quality"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "triage",
      "path": "C:\\Users\\brsth\\.grok\\skills\\triage\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "go",
        "handoff",
        "review",
        "tp",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "evidence-anchored-review",
        "finding-lifecycle",
        "scan-session-transcript",
        "session-finding-triage"
      ],
      "domain": "discovery"
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
        "reading-chatgpt-shared-links-js-spa",
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
        "handoff",
        "red-team",
        "skill-dev",
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
        "adaptive-orchestration-task-shape-classification",
        "adaptive-research-depth-preventing-incomplete-www-coverage",
        "ai-thought-partner-landscape-and-tp-improvements-2026",
        "assumption-auditing-and-unknown-unknown-discovery",
        "blind-spot-detection-methods",
        "compound-skill-improvement-patterns",
        "concurrent-cdp-auth-contention",
        "decision-integrity-in-research-blocking-unknowns-and-decision-red-teaming",
        "intent-mode-gated-auto-composition",
        "invariants-beat-environment-comfort",
        "notebooklm-cli-operational-gotchas",
        "parallel-subagent-wait-all-gate",
        "plausible-narratives-substitute-for-verification",
        "reading-chatgpt-shared-links-js-spa",
        "research-applicability-checking-dont-cite-without-verifying-assumptions",
        "research-quality-principle-efficiency-not-censorship",
        "research-vs-design-vs-architect-skills-and-www-self-assessment",
        "self-reflection-in-llms-fails-without-external-evidence",
        "self-reflective-gap-discovery-indirect-hunting-prompts",
        "skill-catalog",
        "two-component-research-winnowing-pattern",
        "wikilinks"
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
      "name": "skill-design-principles",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\skill-design-principles\\SKILL.md",
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
        "scan-code-quality",
        "session-verification",
        "subagent-dispatch"
      ],
      "domain": "testing"
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
        "llm-instruction-non-compliance-activation-gap-2026",
        "wikilinks"
      ],
      "provides": [
        "knowledge-hygiene",
        "scan-workspace-state"
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
        "nlm",
        "notebooklm"
      ],
      "references_wiki": [
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
      "name": "building-pydantic-ai-agents",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\plugins\\ai\\skills\\building-pydantic-ai-agents\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "logfire-instrumentation",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\plugins\\logfire\\skills\\logfire-instrumentation\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "logfire-query",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\plugins\\logfire\\skills\\logfire-query\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "logfire-ui",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\plugins\\logfire\\skills\\logfire-ui\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pydantic",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\plugins\\pydantic\\skills\\pydantic\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pydantic-ai-harness",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\plugins\\pydantic-ai-harness\\skills\\pydantic-ai-harness\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "building-pydantic-ai-agents",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\skills\\building-pydantic-ai-agents\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "logfire-instrumentation",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\skills\\logfire-instrumentation\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "logfire-query",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\skills\\logfire-query\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "logfire-ui",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\skills\\logfire-ui\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pydantic",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\skills\\pydantic\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pydantic-ai-harness",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\ai-8ac48a59\\skills\\pydantic-ai-harness\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "codex-cli-runtime",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-0471180b5259112a-plugins-codex-4df10c6d\\skills\\codex-cli-runtime\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "codex"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "codex-result-handling",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-0471180b5259112a-plugins-codex-4df10c6d\\skills\\codex-result-handling\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "codex"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "gpt-5-4-prompting",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-0471180b5259112a-plugins-codex-4df10c6d\\skills\\gpt-5-4-prompting\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "claudit",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-0f3a28b3c40cb2f0-plugins-claudit-d3842d10\\skills\\claudit\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "knowledge",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-0f3a28b3c40cb2f0-plugins-claudit-d3842d10\\skills\\knowledge\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "refresh",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-0f3a28b3c40cb2f0-plugins-claudit-d3842d10\\skills\\refresh\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "status",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-0f3a28b3c40cb2f0-plugins-claudit-d3842d10\\skills\\status\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pi-cli-runtime",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-660785464e056e9b-plugins-pi-fd0db27a\\skills\\pi-cli-runtime\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pi-cross-verify",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-660785464e056e9b-plugins-pi-fd0db27a\\skills\\pi-cross-verify\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pi-result-handling",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-660785464e056e9b-plugins-pi-fd0db27a\\skills\\pi-result-handling\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pi-routing",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-660785464e056e9b-plugins-pi-fd0db27a\\skills\\pi-routing\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "access",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-external-plugins-discord-a640bd71\\skills\\access\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "configure",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-external-plugins-discord-a640bd71\\skills\\configure\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "access",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-external-plugins-telegram-d2d1098b\\skills\\access\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "configure",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-external-plugins-telegram-d2d1098b\\skills\\configure\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "claude-automation-recommender",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-claude-code-setup-75a5e861\\skills\\claude-automation-recommender\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "context7"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "claude-md-improver",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-claude-md-management-6514e215\\skills\\claude-md-improver\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "claude-security",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-claude-security-49aa74db\\skills\\claude-security\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "frontend-design",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-frontend-design-c0d56842\\skills\\frontend-design\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-rules",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-hookify-117687a6\\skills\\writing-rules\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "build-mcp-app",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-mcp-server-dev-bcbb8c4e\\skills\\build-mcp-app\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "build-mcp-server",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-mcp-server-dev-bcbb8c4e\\skills\\build-mcp-server\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "build-mcpb",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-mcp-server-dev-bcbb8c4e\\skills\\build-mcpb\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "playground",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-playground-73d74b09\\skills\\playground\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "agent-development",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-plugin-dev-5a8bc1e1\\skills\\agent-development\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "command-development",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-plugin-dev-5a8bc1e1\\skills\\command-development\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "help",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hook-development",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-plugin-dev-5a8bc1e1\\skills\\hook-development\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "mcp-integration",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-plugin-dev-5a8bc1e1\\skills\\mcp-integration\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "plugin-settings",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-plugin-dev-5a8bc1e1\\skills\\plugin-settings\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "plugin-structure",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-plugin-dev-5a8bc1e1\\skills\\plugin-structure\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skill-development",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-plugin-dev-5a8bc1e1\\skills\\skill-development\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "project-artifact",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-project-artifact-898e5c66\\skills\\project-artifact\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skill-creator",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-783232b622f8182e-plugins-skill-creator-abe0b552\\skills\\skill-creator\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
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
      "name": "babysit",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\babysit\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "cloud-sync",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\cloud-sync\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "design-is",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\design-is\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "do",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\do\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "how-it-works",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\how-it-works\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "knowledge-agent",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\knowledge-agent\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "learn-codebase",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\learn-codebase\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "make-plan",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\make-plan\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "mem-search",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\mem-search\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "mode-creator",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\mode-creator\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "oh-my-issues",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\oh-my-issues\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pathfinder",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\pathfinder\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "smart-explore",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\smart-explore\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "standup",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\standup\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "timeline-report",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\timeline-report\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "version-bump",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\version-bump\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "weekly-digests",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\weekly-digests\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "what-the",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\what-the\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wowerpoint",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\c--users-brsth--grok-marketplace-cache-b975999a270027c6-plugin-e849000c\\skills\\wowerpoint\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "notebooklm"
      ],
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
      "name": "codspeed-optimize",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\codspeed-3ec8881c\\skills\\codspeed-optimize\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [
        "bench"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "codspeed-setup-harness",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\codspeed-3ec8881c\\skills\\codspeed-setup-harness\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [
        "bench"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "deepeval",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\deepeval-b59be9dc\\skills\\deepeval\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "deepeval-otel",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\deepeval-b59be9dc\\skills\\deepeval-otel\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "deepeval-tracing",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\deepeval-b59be9dc\\skills\\deepeval-tracing\\SKILL.md",
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
      "name": "exa-search",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\exa-grok-plugin-f73327c3\\skills\\exa-search\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "exa"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "exa-agent",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\exa-mcp-server-b74e6899\\skills\\exa-agent\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "exa"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "search",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\exa-mcp-server-b74e6899\\skills\\search\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "exa"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-agent",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-agent\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-cli",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-cli\\SKILL.md",
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
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-crawl\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-download",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-download\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-interact",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-interact\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-map",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-map\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-monitor",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-monitor\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-parse",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-parse\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-scrape",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-scrape\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "firecrawl-search",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\firecrawl-claude-plugin-0d35612a\\skills\\firecrawl-search\\SKILL.md",
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
      "name": "captions-overlay",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.agents\\skills\\captions-overlay\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "changelog-video",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.agents\\skills\\changelog-video\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "cut-the-curve",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.agents\\skills\\cut-the-curve\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "motion-doctrine",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.agents\\skills\\motion-doctrine\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "oversized-cursor",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.agents\\skills\\oversized-cursor\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "seam-craft",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.agents\\skills\\seam-craft\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "captions-overlay",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.claude\\skills\\captions-overlay\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "changelog-video",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.claude\\skills\\changelog-video\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "cut-the-curve",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.claude\\skills\\cut-the-curve\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "motion-doctrine",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.claude\\skills\\motion-doctrine\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "oversized-cursor",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.claude\\skills\\oversized-cursor\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "seam-craft",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\.claude\\skills\\seam-craft\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "embedded-captions",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\embedded-captions\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "faceless-explainer",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\faceless-explainer\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "figma",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\figma\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "general-video",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\general-video\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hyperframes",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\hyperframes\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hyperframes-animation",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\hyperframes-animation\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hyperframes-cli",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\hyperframes-cli\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hyperframes-core",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\hyperframes-core\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hyperframes-creative",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\hyperframes-creative\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hyperframes-keyframes",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\hyperframes-keyframes\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hyperframes-registry",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\hyperframes-registry\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "media-use",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\media-use\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "motion-graphics",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\motion-graphics\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "music-to-video",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\music-to-video\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pr-to-video",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\pr-to-video\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "product-launch-video",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\product-launch-video\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "remotion-to-hyperframes",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\remotion-to-hyperframes\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "slideshow",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\slideshow\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "talking-head-recut",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\hyperframes-13cee189\\skills\\talking-head-recut\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "codex"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "add-app-to-server",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\mcp-apps-ca51757f\\plugins\\mcp-apps\\skills\\add-app-to-server\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "convert-web-app",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\mcp-apps-ca51757f\\plugins\\mcp-apps\\skills\\convert-web-app\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "create-mcp-app",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\mcp-apps-ca51757f\\plugins\\mcp-apps\\skills\\create-mcp-app\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "migrate-oai-app",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\mcp-apps-ca51757f\\plugins\\mcp-apps\\skills\\migrate-oai-app\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "chrome-extensions",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\modern-web-guidance-47b15e3d\\skills\\chrome-extensions\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "modern-web-guidance",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\modern-web-guidance-47b15e3d\\skills\\modern-web-guidance\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "browser-use",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\plugins-git-browser-use-dbe52796\\.kimi-plugin\\skills\\browser-use\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "browser-use",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\plugins-git-browser-use-dbe52796\\cursor\\skills\\browser-use\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "qa",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\plugins-git-browser-use-dbe52796\\qa\\skills\\qa\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ask-matt",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\ask-matt\\SKILL.md",
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
        "wizard"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "code-review",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\code-review\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "codebase-design",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\codebase-design\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "diagnosing-bugs",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\diagnosing-bugs\\SKILL.md",
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
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\domain-modeling\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "grill-with-docs",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\grill-with-docs\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "implement",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\implement\\SKILL.md",
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
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\improve-codebase-architecture\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "prototype",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\prototype\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "research",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\research\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "resolving-merge-conflicts",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\resolving-merge-conflicts\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "setup-matt-pocock-skills",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\setup-matt-pocock-skills\\SKILL.md",
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
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\tdd\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "to-spec",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\to-spec\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "to-tickets",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\to-tickets\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "triage",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\triage\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wayfinder",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\wayfinder\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wizard",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\engineering\\wizard\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "claude-handoff",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\in-progress\\claude-handoff\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "loop-me",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\in-progress\\loop-me\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "setup-ts-deep-modules",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\in-progress\\setup-ts-deep-modules\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-beats",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\in-progress\\writing-beats\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-fragments",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\in-progress\\writing-fragments\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-shape",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\in-progress\\writing-shape\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "git-guardrails-claude-code",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\misc\\git-guardrails-claude-code\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "migrate-to-shoehorn",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\misc\\migrate-to-shoehorn\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "scaffold-exercises",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\misc\\scaffold-exercises\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "setup-pre-commit",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\misc\\setup-pre-commit\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "grill-me",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\productivity\\grill-me\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "grilling",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\productivity\\grilling\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "handoff",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\productivity\\handoff\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "teach",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\productivity\\teach\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "to-questionnaire",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\productivity\\to-questionnaire\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wait-what",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\productivity\\wait-what\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-for-agents",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-15663f80\\skills\\productivity\\writing-for-agents\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hf-mcp",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\hf-mcp\\skills\\hf-mcp\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hf-cli",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\hf-cli\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hf-cloud-aws-context-discovery",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\hf-cloud-aws-context-discovery\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hf-cloud-python-env-setup",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\hf-cloud-python-env-setup\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hf-cloud-sagemaker-deployment-planner",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\hf-cloud-sagemaker-deployment-planner\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hf-cloud-sagemaker-iam-preflight",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\hf-cloud-sagemaker-iam-preflight\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hf-cloud-sagemaker-production-defaults",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\hf-cloud-sagemaker-production-defaults\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hf-cloud-serving-image-selection",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\hf-cloud-serving-image-selection\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "hf-mem",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\hf-mem\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-best",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-best\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-community-evals",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-community-evals\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-datasets",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-datasets\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-gradio",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-gradio\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-llm-trainer",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-llm-trainer\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-local-models",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-local-models\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-lora-space-builder",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-lora-space-builder\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-paper-publisher",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-paper-publisher\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-papers",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-papers\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-spaces",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-spaces\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-tool-builder",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-tool-builder\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-trackio",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-trackio\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-vision-trainer",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-vision-trainer\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "huggingface-zerogpu",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\huggingface-zerogpu\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "train-sentence-transformers",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\train-sentence-transformers\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "transformers-js",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\transformers-js\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "trl-training",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-88ddea95\\skills\\trl-training\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skill-creator",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-92326433\\.cursor\\skills\\skill-creator\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "langfuse",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-92326433\\skills\\langfuse\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "langfuse.com)"
    },
    {
      "name": "autofix",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-9d89b0e5\\skills\\autofix\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "code-review",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-9d89b0e5\\skills\\code-review\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
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
      "name": "agent-onboarding",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\agent-onboarding\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "brand-listening",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\brand-listening\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "brd-browser-debug",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\brd-browser-debug\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "bright-data-best-practices",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\bright-data-best-practices\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "duckduckgo"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "bright-data-mcp",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\bright-data-mcp\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "brightdata-cli",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\brightdata-cli\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "competitive-intel",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\competitive-intel\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "data-feeds",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\data-feeds\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "design-mirror",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\design-mirror\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "discover-api",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\discover-api\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "js-sdk-best-practices",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\js-sdk-best-practices\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "live-research",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\live-research\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "price-comparison",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\price-comparison\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "proxy",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\proxy\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "python-sdk-best-practices",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\python-sdk-best-practices\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "rag-pipeline",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\rag-pipeline\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "scrape",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\scrape\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "scraper-builder",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\scraper-builder\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [
        "web"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "scraper-studio",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\scraper-studio\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "search",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\search\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "seo-audit",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\skills-f432838a\\skills\\seo-audit\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "searching-sourcegraph",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\sourcegraph-claudecode-plugin-5366c715\\skills\\searching-sourcegraph\\SKILL.md",
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
      "name": "executing-plans",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\executing-plans\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "codex"
      ],
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
      "name": "writing-plans",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-21e2a56d\\skills\\writing-plans\\SKILL.md",
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
      "name": "workflow",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-developing-for-claude-code-54cb1fcc\\examples\\full-featured-plugin\\skills\\workflow\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "professional-greeting",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-developing-for-claude-code-54cb1fcc\\examples\\simple-greeter-plugin\\skills\\professional-greeting\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "developing-claude-code-plugins",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-developing-for-claude-code-54cb1fcc\\skills\\developing-claude-code-plugins\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "working-with-claude-code",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\superpowers-developing-for-claude-code-54cb1fcc\\skills\\working-with-claude-code\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "academic-scientific-research",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tavily-grok-plugin-05ff8f77\\skills\\academic-scientific-research\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "tavily"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "investment-research-briefs",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tavily-grok-plugin-05ff8f77\\skills\\investment-research-briefs\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "tavily"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "product-competitor-intelligence",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tavily-grok-plugin-05ff8f77\\skills\\product-competitor-intelligence\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "tavily"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "sales-account-intelligence",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tavily-grok-plugin-05ff8f77\\skills\\sales-account-intelligence\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "tavily"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tavily-best-practices",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tavily-grok-plugin-05ff8f77\\skills\\tavily-best-practices\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tavily-web",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tavily-grok-plugin-05ff8f77\\skills\\tavily-web\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "tavily"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "threat-intelligence-enrichment",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tavily-grok-plugin-05ff8f77\\skills\\threat-intelligence-enrichment\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "tavily"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "vendor-risk-kyc-screening",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tavily-grok-plugin-05ff8f77\\skills\\vendor-risk-kyc-screening\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [
        "tavily"
      ],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-clearly-and-concisely",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\the-elements-of-style-8c8b0dd2\\skills\\writing-clearly-and-concisely\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "agent",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tinyfish-web-agent-integrations-git-grok-7db223a5\\claude\\skills\\agent\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "fetch",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tinyfish-web-agent-integrations-git-grok-7db223a5\\claude\\skills\\fetch\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "search",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tinyfish-web-agent-integrations-git-grok-7db223a5\\claude\\skills\\search\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tinyfish-authenticated",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tinyfish-web-agent-integrations-git-grok-7db223a5\\grok\\skills\\tinyfish-authenticated\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tinyfish-automation",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tinyfish-web-agent-integrations-git-grok-7db223a5\\grok\\skills\\tinyfish-automation\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tinyfish-browser",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tinyfish-web-agent-integrations-git-grok-7db223a5\\grok\\skills\\tinyfish-browser\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tinyfish-research",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tinyfish-web-agent-integrations-git-grok-7db223a5\\grok\\skills\\tinyfish-research\\SKILL.md",
      "scope": "grok-installed-plugins",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tinyfish-web",
      "path": "C:\\Users\\brsth\\.grok\\installed-plugins\\tinyfish-web-agent-integrations-git-grok-7db223a5\\grok\\skills\\tinyfish-web\\SKILL.md",
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
      "critic-model-pool": [
        "aar",
        "review",
        "tp"
      ],
      "reasoning-model-pool": [
        "aar",
        "tp",
        "why"
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
        "todo",
        "wargame",
        "wiki",
        "wiki-crawl4ai",
        "www"
      ],
      "exa": [
        "aar",
        "agy",
        "codex",
        "create-skill",
        "design",
        "dream",
        "exa-agent",
        "exa-search",
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
        "search",
        "search-fleet",
        "skill-dev",
        "todo",
        "web",
        "wiki",
        "wiki-crawl4ai"
      ],
      "nlm": [
        "aar",
        "go",
        "nlm",
        "nlm-to-wiki",
        "refactor",
        "wiki-yt"
      ],
      "agy": [
        "agy",
        "ai-cli",
        "codex",
        "mmx",
        "model-benchmark",
        "search-fleet",
        "tp"
      ],
      "spawn-subagent": [
        "close-py",
        "ship-py",
        "tp",
        "why"
      ],
      "codex": [
        "codex",
        "codex-cli-runtime",
        "executing-plans",
        "mmx",
        "model-benchmark",
        "resume-codex",
        "review",
        "review-relay",
        "talking-head-recut",
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
      "ddg": [
        "go",
        "search-fleet",
        "tp",
        "web",
        "www"
      ],
      "brave": [
        "go",
        "web"
      ],
      "coding-model-pool": [
        "go",
        "review"
      ],
      "mechanical-model-pool": [
        "handoff",
        "refine",
        "www"
      ],
      "tavily": [
        "academic-scientific-research",
        "investment-research-briefs",
        "model-quota",
        "product-competitor-intelligence",
        "sales-account-intelligence",
        "search-fleet",
        "tavily-web",
        "threat-intelligence-enrichment",
        "vendor-risk-kyc-screening",
        "web"
      ],
      "chrome-devtools": [
        "chrome-devtools-cli",
        "model-web"
      ],
      "perplexity": [
        "model-web",
        "search-fleet",
        "web"
      ],
      "chrome-devtools-mcp-tools": [
        "model-web"
      ],
      "context7": [
        "claude-automation-recommender",
        "refactor"
      ],
      "search-research": [
        "prospect",
        "search-fleet",
        "web",
        "why"
      ],
      "pwm": [
        "perplexity-web-mcp",
        "search-fleet"
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
        "wiki-yt",
        "wowerpoint",
        "yt-nlm"
      ],
      "duckduckgo": [
        "bright-data-best-practices",
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
      ]
    },
    "skill_callers": {
      "debrief": [
        "aar",
        "behave",
        "claude-audit",
        "codex",
        "dream",
        "friction",
        "handoff",
        "improve",
        "lmc",
        "mlc",
        "recap",
        "recap-grok",
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
      "handoff": [
        "aar",
        "ask",
        "ask-matt",
        "behave",
        "close-py",
        "design",
        "dream",
        "go",
        "insight",
        "maintain",
        "model-web",
        "notice",
        "packet",
        "plan-writer",
        "prompt-patterns",
        "rca",
        "recap",
        "recap-grok",
        "refactor",
        "refine",
        "review-relay",
        "risk",
        "ship-py",
        "skill-dev",
        "tp",
        "triage",
        "why",
        "wiki",
        "www"
      ],
      "tp": [
        "aar",
        "ask",
        "behave",
        "design",
        "domain-terms",
        "dream",
        "fmea",
        "go",
        "handoff",
        "insight",
        "maintain",
        "model-benchmark",
        "model-web",
        "notice",
        "plan-writer",
        "recap-grok",
        "refactor",
        "refine",
        "req-check",
        "review",
        "risk",
        "skill-dev",
        "slc",
        "todo",
        "triage",
        "why",
        "www"
      ],
      "why": [
        "aar",
        "ask",
        "behave",
        "design",
        "dream",
        "model-benchmark",
        "model-web",
        "notice",
        "rca",
        "review",
        "risk",
        "skill-dev",
        "todo",
        "tp",
        "triage",
        "wargame",
        "www"
      ],
      "review": [
        "aar",
        "ask",
        "behave",
        "check",
        "claude-audit",
        "command-development",
        "debrief",
        "design-is",
        "doc-check",
        "domain-terms",
        "dream",
        "go",
        "improve",
        "insight",
        "learn",
        "maintain",
        "marketplace-bridge",
        "model-benchmark",
        "plugin-structure",
        "refactor",
        "refine",
        "review-pr",
        "review-relay",
        "risks",
        "ship-py",
        "skill-audit",
        "skill-dev",
        "sqd",
        "todo",
        "tp",
        "triage",
        "uci"
      ],
      "go": [
        "aar",
        "ask",
        "check",
        "code",
        "design",
        "doc-check",
        "grill-me",
        "grok-go",
        "grok-parallel",
        "grok-sdlc",
        "handoff",
        "logfire-instrumentation",
        "maintain",
        "model-benchmark",
        "notice",
        "plan-writer",
        "refactor",
        "refine",
        "req-check",
        "review",
        "rns",
        "skill-dev",
        "todo",
        "tp",
        "triage",
        "wargame",
        "why",
        "www"
      ],
      "check": [
        "aar",
        "ask",
        "close-py",
        "doc-check",
        "doc-compiler",
        "dream",
        "go",
        "grok-verify",
        "model-benchmark",
        "refactor",
        "refine",
        "review",
        "ship-py",
        "skill-dev",
        "skill-to-page",
        "todo",
        "tp",
        "triage",
        "www"
      ],
      "close": [
        "aar",
        "ask",
        "check",
        "close-py",
        "dream",
        "handoff",
        "insight",
        "maintain",
        "recap-grok",
        "review",
        "skill-dev",
        "todo",
        "tp",
        "wiki"
      ],
      "wiki": [
        "aar",
        "claude-audit",
        "close-py",
        "create-skill",
        "debrief",
        "design",
        "domain-terms",
        "dream",
        "go",
        "grok-safe-git",
        "handoff",
        "improve",
        "insight",
        "main",
        "maintain",
        "maintain-ifile",
        "model-benchmark",
        "nlm-to-wiki",
        "notice",
        "plan-writer",
        "prompt-patterns",
        "rca",
        "recap-grok",
        "refactor",
        "refine",
        "req-check",
        "review",
        "risk",
        "ship-py",
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
      "todo": [
        "aar",
        "ask",
        "design",
        "email-skill",
        "insight",
        "model-quota",
        "recap-grok",
        "refactor",
        "review",
        "risk",
        "skill-dev",
        "tp",
        "wiki",
        "www"
      ],
      "aar": [
        "ask",
        "close-py",
        "dream",
        "handoff",
        "insight",
        "model-web",
        "notice",
        "packet",
        "recap-grok",
        "skill-dev",
        "slc",
        "todo",
        "tp",
        "wargame",
        "why"
      ],
      "design": [
        "ask",
        "behave",
        "code",
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
        "insight",
        "maintain",
        "maintain-ifile",
        "skill-dev",
        "todo",
        "wiki",
        "workspace-health"
      ],
      "skill-dev": [
        "create-skill",
        "insight",
        "maintain",
        "maintain-ifile",
        "ship-py",
        "todo",
        "tp",
        "www"
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
        "maintain-ifile",
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
      "grok-safe-git": [
        "go",
        "grok-parallel",
        "grok-verify",
        "ship-py"
      ],
      "grok-discovery": [
        "go",
        "grok-parallel"
      ],
      "grok-route": [
        "go",
        "grok-parallel",
        "grok-verify"
      ],
      "test-driven-development": [
        "go"
      ],
      "grok-parallel": [
        "go",
        "notice"
      ],
      "using-git-worktrees": [
        "go"
      ],
      "grok-verify": [
        "go",
        "grok-parallel",
        "skill-dev"
      ],
      "domain-terms": [
        "grill-me"
      ],
      "maintain": [
        "insight",
        "maintain-ifile",
        "model-quota",
        "skill-dev",
        "todo"
      ],
      "maintain-ifile": [
        "maintain"
      ],
      "config-audit": [
        "maintain"
      ],
      "recover": [
        "config-audit",
        "main",
        "maintain",
        "skill-prune",
        "workspace-health"
      ],
      "codex": [
        "codex-result-handling",
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
      "chrome-devtools": [
        "model-web"
      ],
      "wargame": [
        "plan-writer",
        "req-check",
        "risk"
      ],
      "red-team": [
        "claude-audit",
        "debrief",
        "fmea",
        "improve",
        "pre-mortem",
        "preflight",
        "redteam",
        "retro",
        "review",
        "risk",
        "risks",
        "skill-audit",
        "www"
      ],
      "risk": [
        "req-check",
        "ship-py"
      ],
      "refactor": [
        "ship-py"
      ],
      "doc-check": [
        "ship-py"
      ],
      "notice": [
        "skill-dev",
        "slc"
      ],
      "fmea": [
        "skill-dev"
      ],
      "create-skill": [
        "skill-dev"
      ],
      "insight": [
        "todo"
      ],
      "web": [
        "scraper-builder",
        "tp",
        "why",
        "wiki-crawl4ai",
        "www"
      ],
      "packet": [
        "tp"
      ],
      "crawl4ai": [
        "wiki-crawl4ai"
      ],
      "wiki-crawl4ai": [
        "www"
      ],
      "help": [
        "command-development"
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
      "teach": [
        "ask-matt"
      ],
      "triage": [
        "ask-matt",
        "setup-matt-pocock-skills"
      ],
      "to-tickets": [
        "ask-matt"
      ],
      "to-spec": [
        "ask-matt"
      ],
      "wayfinder": [
        "ask-matt"
      ],
      "wizard": [
        "ask-matt"
      ],
      "writing-great-skills": [
        "ask-matt"
      ]
    },
    "wiki_referencers": {
      "user-modeling-for-agentic-clis": [
        "aar",
        "notice"
      ],
      "tool-fallbacks": [
        "aar",
        "design",
        "model-benchmark",
        "tp"
      ],
      "parallel-subagent-wait-all-gate": [
        "aar",
        "www"
      ],
      "friction-detection-operator-pushback-as-trigger": [
        "aar"
      ],
      "skill-catalog": [
        "ask",
        "skill-dev",
        "tp",
        "wiki",
        "www"
      ],
      "skill-graph": [
        "ask"
      ],
      "signal-based-intent-expansion": [
        "ask",
        "handoff",
        "todo",
        "tp"
      ],
      "governance-pattern-library": [
        "behave"
      ],
      "skill-pipeline-integration-testing": [
        "close-py",
        "ship-py",
        "skill-dev"
      ],
      "pipeline-detect-phase-state-reset-sequential-contamination": [
        "close-py"
      ],
      "adr-0009-extend-unverified-stance": [
        "design"
      ],
      "llm-synthesis-quality-and-speed-techniques": [
        "design"
      ],
      "design-choice-audit-challenge-every-decision-against-first-principles": [
        "design",
        "go",
        "plan-writer",
        "refactor",
        "tp"
      ],
      "multi-model-ensemble-design-patterns-for-agent-skills": [
        "design",
        "review"
      ],
      "exemption-logic-as-conflict-signal": [
        "design"
      ],
      "invariants-beat-environment-comfort": [
        "design",
        "risk",
        "www"
      ],
      "agentic-sdlc-skill-lifecycle-architecture": [
        "check",
        "design",
        "plan-writer",
        "refactor",
        "refine",
        "review"
      ],
      "design-doc-conformance-check-procedure": [
        "design",
        "risk",
        "tp"
      ],
      "consistency-drift-as-waste-source-in-iterative-refinement": [
        "design"
      ],
      "raising-coding-best-practices-in-ai-agents": [
        "design"
      ],
      "page": [
        "doc-check",
        "wiki-crawl4ai"
      ],
      "llm-dreaming-memory-consolidation": [
        "dream"
      ],
      "operator-collaboration-style-and-leverage": [
        "dream"
      ],
      "self-improving-agent-systems-techniques-and-workspace-gaps": [
        "dream"
      ],
      "scatter-gather-for-single-artifact-parallel-analysis": [
        "go",
        "review"
      ],
      "framing-check-pattern": [
        "go"
      ],
      "solution-unit-validation-before-build": [
        "go"
      ],
      "prompting-patterns-for-ai-agent-control": [
        "go",
        "prompt-patterns"
      ],
      "subagent-shell-quoting-durable-fix": [
        "go",
        "web"
      ],
      "multi-terminal-git-coordination-primitives": [
        "grok-safe-git"
      ],
      "skill-usability-audit-cold-read-critique": [
        "handoff"
      ],
      "insight-skill-consolidates-capture-friction-harvest": [
        "insight"
      ],
      "signal-prioritization-for-improvement-detection": [
        "insight"
      ],
      "fleet-maintenance-skill-design": [
        "maintain"
      ],
      "scheduled-checks-in-maintain": [
        "maintain"
      ],
      "llm-instruction-non-compliance-activation-gap-2026": [
        "config-audit",
        "maintain-ifile",
        "skill-prune"
      ],
      "agents-md-construction-best-practices": [
        "maintain-ifile"
      ],
      "agents-md-optimization-tools-landscape-2026": [
        "maintain-ifile"
      ],
      "enforcement-hierarchy-and-compaction-strategy": [
        "maintain-ifile"
      ],
      "model-pool-not-chain": [
        "model-benchmark",
        "tp"
      ],
      "model-benchmark-testing-quirks": [
        "model-benchmark"
      ],
      "model-fleet-provider-pools": [
        "model-benchmark"
      ],
      "chrome-job-object-escape-via-task-scheduler": [
        "model-web"
      ],
      "chromium-cdp-websocket-origin-restriction": [
        "model-web"
      ],
      "multi-llm-aggregator-landscape": [
        "model-web"
      ],
      "cdp-network-interception-and-sse-capture-for-llm-chat": [
        "model-web"
      ],
      "proactive-ai-volunteering-mechanisms": [
        "notice"
      ],
      "mechanisms-for-thought-partner-behavior": [
        "notice"
      ],
      "compaction-inherited-recommendation-decoupling": [
        "notice"
      ],
      "intent-mode-gated-auto-composition": [
        "notice",
        "www"
      ],
      "wiki-concept": [
        "notice"
      ],
      "maker-checker-required-for-enforcement-work": [
        "plan-writer"
      ],
      "verification-before-completion-principle": [
        "refactor"
      ],
      "designing-harnesses-that-make-good-behavior-the-path-of-least-resistance": [
        "refine"
      ],
      "workflow-definition-over-agent-capability": [
        "refine"
      ],
      "trust-escalation-ladder-autonomous-agent-work": [
        "refine"
      ],
      "task-refinement-interview-detection-template-patterns": [
        "refine"
      ],
      "x": [
        "req-check",
        "wiki"
      ],
      "great-adversarial-review-skill-design-patterns": [
        "req-check",
        "risk"
      ],
      "fix-introduces-regression-by-trading-properties": [
        "review"
      ],
      "concurrent-cdp-auth-contention": [
        "email-skill",
        "risk",
        "www"
      ],
      "blind-spot-detection-methods": [
        "risk",
        "skill-dev",
        "www"
      ],
      "adaptive-expansion-evidence-triggered-conditional-steps": [
        "risk"
      ],
      "specification-gaming-in-llm-agent-pipelines": [
        "ship-py"
      ],
      "claude-side-skill-improvement-tooling-2026": [
        "skill-dev"
      ],
      "cross-invocation-skills-proactively-suggest-complementary-skills": [
        "skill-dev",
        "tp"
      ],
      "skill-techniques-index": [
        "skill-dev"
      ],
      "execution-receipts-for-executable-artifacts": [
        "skill-dev"
      ],
      "skill-effectiveness-measurement-gaps-trigger-accuracy-token-efficiency": [
        "skill-dev"
      ],
      "skill-development-portfolio": [
        "skill-dev"
      ],
      "code-output-passthrough-narration-over-script-output": [
        "skill-dev"
      ],
      "mechanical-enforcement-of-llm-skill-steps-2026": [
        "skill-dev"
      ],
      "skill-management-in-agentic-systems-research-survey": [
        "skill-dev"
      ],
      "self-reflective-gap-discovery-indirect-hunting-prompts": [
        "skill-dev",
        "www"
      ],
      "thought-partner-standard": [
        "slc"
      ],
      "llm-judgment-hooks": [
        "todo"
      ],
      "no-question-theater": [
        "todo"
      ],
      "evidence-first-default-and-needless-confirmation": [
        "todo"
      ],
      "externalized-verification-over-intrinsic-self-correction": [
        "todo"
      ],
      "analyst-exhibits-pattern-being-analyzed": [
        "tp"
      ],
      "research-quality-principle-efficiency-not-censorship": [
        "tp",
        "www"
      ],
      "model-pool-selection-policy-speed-quota-diversity": [
        "check",
        "tp"
      ],
      "model-fit-and-post-hoc-behavioral-detection": [
        "tp"
      ],
      "inter-skill-output-bridges-and-temporal-surfacing-layers": [
        "tp"
      ],
      "markdown-mermaid-rendering-agentic-clis-windows-11": [
        "tp"
      ],
      "code-orchestrates-model-judges-skill-scale": [
        "tp"
      ],
      "mechanical-as-input-not-mechanical-as-frame": [
        "tp"
      ],
      "model-tool-calling-capability-matrix": [
        "tp"
      ],
      "reading-chatgpt-shared-links-js-spa": [
        "web",
        "www"
      ],
      "optimal-multi-backend-search-strategy": [
        "web"
      ],
      "search-tool-landscape-2026": [
        "web"
      ],
      "web-search-tool-routing": [
        "web"
      ],
      "web-research-state-2026": [
        "web"
      ],
      "multidimensional-root-cause-analysis-ai-agent-failures": [
        "why"
      ],
      "reactive-pattern-matching-and-closure-pressure": [
        "why"
      ],
      "self-reflection-in-llms-fails-without-external-evidence": [
        "why",
        "www"
      ],
      "compaction-inherited-diagnosis-unverified-propagation": [
        "why"
      ],
      "problem-first-systems-decomposition": [
        "why"
      ],
      "concept": [
        "wiki"
      ],
      "couple-triggers-to-events-that-actually-fire": [
        "wiki"
      ],
      "inline-conditional-over-dispatch-for-skill-design": [
        "wiki"
      ],
      "existing-concept": [
        "wiki"
      ],
      "wikilinks": [
        "nlm-to-wiki",
        "obsidian-vault",
        "skill-prune",
        "wiki",
        "wiki-crawl4ai",
        "wiki-yt",
        "www"
      ],
      "synchronous-review-direct-write-pattern": [
        "wiki"
      ],
      "knowledge-capture-cant-afford-to-lose": [
        "wiki"
      ],
      "ai-thought-partner-landscape-and-tp-improvements-2026": [
        "www"
      ],
      "compound-skill-improvement-patterns": [
        "www"
      ],
      "decision-integrity-in-research-blocking-unknowns-and-decision-red-teaming": [
        "www"
      ],
      "adaptive-orchestration-task-shape-classification": [
        "www"
      ],
      "two-component-research-winnowing-pattern": [
        "www"
      ],
      "assumption-auditing-and-unknown-unknown-discovery": [
        "www"
      ],
      "notebooklm-cli-operational-gotchas": [
        "nlm-bulk-ingest",
        "recover",
        "wiki-yt",
        "www"
      ],
      "plausible-narratives-substitute-for-verification": [
        "www"
      ],
      "research-vs-design-vs-architect-skills-and-www-self-assessment": [
        "www"
      ],
      "research-applicability-checking-dont-cite-without-verifying-assumptions": [
        "www"
      ],
      "adaptive-research-depth-preventing-incomplete-www-coverage": [
        "www"
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
      "semantic-clustering-bounded-size": [
        "nlm-bulk-ingest"
      ],
      "notebooklm-source-limits-free-vs-paid": [
        "nlm-bulk-ingest",
        "wiki-yt"
      ],
      "nlm-to-wiki-optimization-opportunities": [
        "wiki-yt"
      ],
      "video-to-wiki-pipeline-transcript-extraction-multimodal": [
        "wiki-yt"
      ],
      "bench": [
        "codspeed-optimize",
        "codspeed-setup-harness"
      ],
      "nlm-abc12345-concept-two": [
        "nlm-to-wiki"
      ],
      "nlm-abc12345-concept-one": [
        "nlm-to-wiki"
      ]
    },
    "capability_providers": {
      "scan-session-transcript": [
        "aar",
        "insight",
        "todo",
        "triage"
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
      "session-retrospective": [
        "aar"
      ],
      "gemini-reasoning": [
        "agy"
      ],
      "cross-model-second-opinion": [
        "agy",
        "codex",
        "mmx"
      ],
      "skill-routing": [
        "ask"
      ],
      "anti-fabrication-close": [
        "close-py"
      ],
      "session-close-pipeline": [
        "close-py"
      ],
      "close-verdict": [
        "close-py"
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
      "readme-staleness-detection": [
        "doc-check"
      ],
      "skill-frontmatter-validation": [
        "doc-check"
      ],
      "broken-link-detection": [
        "doc-check"
      ],
      "repo-file-completeness": [
        "doc-check"
      ],
      "documentation-readiness-check": [
        "doc-check"
      ],
      "wikilink-resolution": [
        "doc-check"
      ],
      "changelog-validation": [
        "doc-check"
      ],
      "code-fence-validation": [
        "doc-check"
      ],
      "domain-term-extraction": [
        "domain-terms"
      ],
      "offline-memory-consolidation": [
        "dream"
      ],
      "discovery-dispatch": [
        "go"
      ],
      "engineering-orchestration": [
        "go"
      ],
      "parallel-implement-dispatch": [
        "go"
      ],
      "verify-dispatch": [
        "go"
      ],
      "safe-git-preflight-dispatch": [
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
      "subagent-dispatch": [
        "check",
        "grok-parallel",
        "review",
        "tp",
        "www"
      ],
      "parallel-fan-out": [
        "grok-parallel"
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
      "scan-code-quality": [
        "check",
        "grok-verify",
        "review",
        "trace"
      ],
      "handoff-auto-update": [
        "handoff"
      ],
      "handoff-write": [
        "handoff"
      ],
      "grok-documentation-help": [
        "help"
      ],
      "image-generation-guidance": [
        "imagine"
      ],
      "capture-coverage-check": [
        "insight"
      ],
      "workflow-automation-analysis": [
        "insight"
      ],
      "proactive-knowledge-capture": [
        "insight"
      ],
      "friction-detection": [
        "insight"
      ],
      "improvement-opportunity-scan": [
        "insight"
      ],
      "fleet-maintenance": [
        "maintain"
      ],
      "scan-workspace-state": [
        "maintain",
        "skill-prune",
        "todo"
      ],
      "marketplace-skill-discovery": [
        "marketplace-bridge"
      ],
      "minimax-music-generation": [
        "mmx"
      ],
      "minimax-vision": [
        "mmx"
      ],
      "minimax-speech-synthesis": [
        "mmx"
      ],
      "minimax-image-generation": [
        "mmx"
      ],
      "minimax-video-generation": [
        "mmx"
      ],
      "minimax-web-search": [
        "mmx"
      ],
      "latency-benchmark": [
        "model-benchmark"
      ],
      "quality-scoring": [
        "model-benchmark"
      ],
      "cost-tracking": [
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
      "fusion-portal-orchestration": [
        "model-web"
      ],
      "sse-response-capture": [
        "model-web"
      ],
      "model-web-advisory": [
        "model-web"
      ],
      "multi-model-ensemble": [
        "model-web"
      ],
      "browser-llm-bridge": [
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
      "root-cause-analysis": [
        "rca",
        "why"
      ],
      "session-chain-walk": [
        "recap-grok"
      ],
      "session-recap-grok": [
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
      "risk-assessment": [
        "risk"
      ],
      "risk-escalation": [
        "risk"
      ],
      "adversarial-review": [
        "risk"
      ],
      "risk-scan": [
        "risk"
      ],
      "scan-risk": [
        "risk",
        "tp"
      ],
      "capability-routed-search": [
        "search-fleet"
      ],
      "rrf-aggregation": [
        "search-fleet"
      ],
      "ship-pipeline": [
        "ship-py"
      ],
      "verify-and-publish": [
        "ship-py"
      ],
      "public-readiness-gate": [
        "ship-py"
      ],
      "skill-improvement": [
        "skill-dev"
      ],
      "skill-measurement": [
        "skill-dev"
      ],
      "behavioral-reset": [
        "slc"
      ],
      "thought-partner-realignment": [
        "slc"
      ],
      "workspace-prioritized-action-list": [
        "todo"
      ],
      "session-opportunity-review": [
        "tp"
      ],
      "critical-friend-critique": [
        "tp"
      ],
      "system-exploration": [
        "tp"
      ],
      "manual-trace-verification": [
        "trace"
      ],
      "logic-error-detection": [
        "trace"
      ],
      "session-finding-triage": [
        "triage"
      ],
      "finding-lifecycle": [
        "triage"
      ],
      "evidence-anchored-review": [
        "triage"
      ],
      "content-discipline-for-plans": [
        "wargame"
      ],
      "rrf-merge": [
        "web"
      ],
      "multi-backend-search": [
        "web"
      ],
      "pattern-library-query": [
        "why"
      ],
      "feedback-to-wiki": [
        "why"
      ],
      "wiki-query": [
        "wiki"
      ],
      "wiki-write": [
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
      "failure-modes-analysis": [
        "fmea"
      ],
      "risk-priority-scoring": [
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
      "critic-model-pool": [
        "aar",
        "review",
        "tp"
      ],
      "reasoning-model-pool": [
        "aar",
        "tp",
        "why"
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
        "todo",
        "wargame",
        "wiki",
        "wiki-crawl4ai",
        "www"
      ],
      "exa": [
        "aar",
        "agy",
        "codex",
        "create-skill",
        "design",
        "dream",
        "exa-agent",
        "exa-search",
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
        "search",
        "search-fleet",
        "skill-dev",
        "todo",
        "web",
        "wiki",
        "wiki-crawl4ai"
      ],
      "nlm": [
        "aar",
        "go",
        "nlm",
        "nlm-to-wiki",
        "refactor",
        "wiki-yt"
      ],
      "agy": [
        "agy",
        "ai-cli",
        "codex",
        "mmx",
        "model-benchmark",
        "search-fleet",
        "tp"
      ],
      "spawn-subagent": [
        "close-py",
        "ship-py",
        "tp",
        "why"
      ],
      "codex": [
        "codex",
        "codex-cli-runtime",
        "executing-plans",
        "mmx",
        "model-benchmark",
        "resume-codex",
        "review",
        "review-relay",
        "talking-head-recut",
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
        "refine",
        "www"
      ],
      "tavily": [
        "academic-scientific-research",
        "investment-research-briefs",
        "model-quota",
        "product-competitor-intelligence",
        "sales-account-intelligence",
        "search-fleet",
        "tavily-web",
        "threat-intelligence-enrichment",
        "vendor-risk-kyc-screening",
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
        "wiki-yt",
        "wowerpoint",
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
