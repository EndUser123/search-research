---
title: "Skill dependency graph: who calls what and who consumes which providers"
created: 2026-07-28
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
| `agy` | 7 | `agy`, `ai-cli`, `codex`, `mmx`, `model-benchmark`, `search-fleet`, `tasks` |
| `brave` | 2 | `go`, `web` |
| `codex` | 8 | `codex`, `mmx`, `model-benchmark`, `resume-codex`, `review`, `tasks`, `tp`, `wargame` |
| `context7` | 1 | `context7` |
| `ddg` | 4 | `search-fleet`, `tp`, `web`, `www` |
| `duckduckgo` | 1 | `web` |
| `episodic-memory` | 1 | `dream` |
| `exa` | 28 | `aar`, `agy`, `codex`, `crawl4ai`, `create-skill`, `design`, `dream`, `go`, `grok-parallel`, `grok-verify`, `handoff`, `imagine`, `mmx`, `model-benchmark`, `notice`, `packet`, `plan-writer`, `prompt-patterns`, `refactor`, `refine`, `review`, `search-fleet`, `skill-dev`, `tasks`, `todo`, `web`, `why-old`, `wiki` |
| `firecrawl` | 6 | `crawl4ai`, `design`, `search-fleet`, `tp`, `web`, `www` |
| `gh` | 32 | `aar`, `agy`, `codex`, `crawl4ai`, `debrief`, `design`, `dream`, `go`, `grok-discovery`, `grok-parallel`, `grok-safe-git`, `grok-verify`, `handoff`, `imagine`, `maintain`, `mmx`, `model-benchmark`, `notice`, `packet`, `plan-writer`, `prompt-patterns`, `refactor`, `refine`, `review`, `search-fleet`, `skill-dev`, `tasks`, `todo`, `wargame`, `why-old`, `wiki`, `www` |
| `github-issues` | 1 | `www` |
| `hn-algolia` | 2 | `web`, `www` |
| `minimax-search` | 1 | `design` |
| `mmx` | 10 | `design`, `minimax-multimodal-toolkit`, `minimax-music-gen`, `minimax-music-playlist`, `mmx`, `model-benchmark`, `nlm-to-wiki`, `search-fleet`, `web`, `www` |
| `nlm` | 6 | `aar`, `gitingest`, `go`, `nlm`, `nlm-to-wiki`, `refactor` |
| `notebooklm` | 5 | `nlm`, `nlm-to-wiki`, `todo`, `web`, `yt-nlm` |
| `perplexity` | 2 | `search-fleet`, `web` |
| `pwm` | 2 | `perplexity-web-mcp`, `search-fleet` |
| `reddit` | 4 | `search-fleet`, `todo`, `web`, `www` |
| `search-research` | 4 | `prospect`, `search-fleet`, `web`, `why` |
| `serper` | 1 | `web` |
| `spawn-subagent` | 2 | `tp`, `why` |
| `stackexchange` | 1 | `web` |
| `tavily` | 2 | `search-fleet`, `web` |

## Delegation targets (who calls this skill)

When a skill changes its interface or behavior, these callers are affected:

| Target skill | Caller count | Called by |
|-------------|-------------|-----------|
| `aar` | 12 | `close`, `dream`, `handoff`, `notice`, `packet`, `plan-writer`, `red-team`, `skill-dev`, `tp`, `wargame`, `why`, `why-old` |
| `agy` | 8 | `ai-cli`, `check`, `codex`, `mmx`, `search-fleet`, `tasks`, `tp`, `why` |
| `check` | 150 | `aar`, `agy`, `ai-api`, `ai-cli`, `ai-models`, `ai-probe-benchmark`, `ai-probe-router`, `aid`, `ask`, `behave`, `bf`, `brainstorming`, `build`, `capture`, `changelog`, `chs`, `claude-audit`, `close`, `code`, `code-review`, `codebase-to-course`, `codex`, `concept-mapper`, `config-audit`, `constitutional-patterns`, `context7`, `crawl`, `crawl4ai`, `create-workflow`, `csf-nip-integration`, `debrief`, `design`, `discover`, `dispatching-parallel-agents`, `doc-compiler`, `docs`, `dream`, `epistemic-check`, `evolve`, `execute-plan`, `execution-clarity`, `find`, `finishing-a-development-branch`, `frontend-dev`, `fullstack-dev`, `game-animation-frames`, `game-character-consistency`, `git`, `gitingest`, `gitpack`, `gitready`, `go`, `google-ai-usage-monitor`, `grok-safe-git`, `grok-verify`, `handoff`, `help`, `imagine`, `implement`, `improve`, `init`, `intelligence-stream-analyze`, `keep`, `learn`, `lmc`, `main`, `maintain`, `minimax-music-gen`, `minimax-music-playlist`, `mm-quota`, `mmx`, `model-benchmark`, `nlm`, `nlm-bulk-ingest`, `nlm-to-wiki`, `note`, `notebooklm`, `notice`, `packet`, `pdf`, `perplexity-web-mcp`, `plan-writer`, `planning`, `plugin-installer`, `pptx`, `pr-babysit`, `pre-mortem`, `preflight`, `prime`, `probe`, `prompt-patterns`, `prospect`, `quota`, `rca`, `recap`, `recover`, `red-team`, `refactor`, `refine`, `reflect`, `retro`, `review`, `review_bundle`, `risks`, `rns`, `s`, `sequential-thinking`, `simplify-enhanced`, `skeptic`, `skill-audit`, `skill-dev`, `skill-from-docs`, `skill-similarity`, `skill-to-page`, `skill-write`, `slc`, `snapshot`, `solo-dev-authority`, `stale`, `subagent-driven-development`, `t`, `task`, `tasks`, `tdd`, `team`, `tilldone`, `tldr-code`, `tldr-overview`, `tldr-stats`, `todo`, `tp`, `trace`, `truth`, `using-git-worktrees`, `using-superpowers`, `usm`, `ut`, `ux`, `verification-before-completion`, `video-vision`, `wargame`, `web`, `why`, `why-old`, `wiki`, `workspace-health`, `www`, `yt-is`, `yt-nlm`, `yt-selenium` |
| `close` | 27 | `aar`, `check`, `claude-audit`, `debrief`, `doc-compiler`, `dream`, `fullstack-dev`, `grok-safe-git`, `grok-verify`, `handoff`, `maintain`, `notice`, `planning`, `pptx`, `probe`, `red-team`, `refactor`, `review`, `skill-dev`, `skill-to-page`, `team`, `todo`, `tp`, `trace`, `writing-skills`, `www`, `yt-selenium` |
| `codex` | 10 | `check`, `mmx`, `nlm-to-wiki`, `reason`, `resume-codex`, `review`, `tp`, `ut`, `why`, `workspace-health` |
| `crawl4ai` | 2 | `crawl`, `www` |
| `create-skill` | 1 | `skill-dev` |
| `debrief` | 19 | `agy`, `behave`, `claude-audit`, `close`, `codex`, `dream`, `export-session`, `friction`, `go`, `handoff`, `improve`, `lmc`, `mlc`, `recap`, `red-team`, `retro`, `skill-audit`, `top-problems`, `tp` |
| `design` | 65 | `aar`, `agy`, `ai-api`, `ask`, `avant-garde-ui`, `behave`, `bf`, `brainstorming`, `cc-model-router`, `check`, `claude-audit`, `close`, `code`, `code-review`, `codebase-to-course`, `codex`, `debrief`, `decision-tree`, `discover`, `doc-compiler`, `dream`, `evolve`, `execute-plan`, `frontend-dev`, `fullstack-dev`, `game-ui-icons`, `gitpack`, `go`, `grok-parallel`, `handoff`, `implement`, `improve`, `improve-codebase-architecture`, `maintain`, `mm-quota`, `mmx`, `nlm-bulk-ingest`, `notice`, `packet`, `plan-writer`, `planning`, `prompt_refiner`, `reason`, `recap`, `red-team`, `refactor`, `refine`, `review`, `review_bundle`, `risks`, `s`, `skill-audit`, `skill-dev`, `skill-to-page`, `skill-write`, `specify`, `tp`, `using-git-worktrees`, `vision-analysis`, `wargame`, `web`, `why`, `why-old`, `wiki`, `www` |
| `go` | 59 | `aar`, `ai-api`, `avant-garde-ui`, `brainstorming`, `build`, `check`, `claude-audit`, `close`, `code`, `code-review`, `codebase-to-course`, `debrief`, `debt`, `design`, `doc-compiler`, `docs`, `dream`, `execute-plan`, `finishing-a-development-branch`, `fullstack-dev`, `gitingest`, `gitpack`, `google-ai-usage-monitor`, `grok-go`, `grok-parallel`, `grok-sdlc`, `handoff`, `implement`, `lmc`, `minimax-music-gen`, `minimax-music-playlist`, `mlc`, `model-benchmark`, `notice`, `plan-writer`, `planning`, `pr-babysit`, `prime`, `reason`, `recap`, `red-team`, `refactor`, `refine`, `research`, `review`, `rns`, `ship`, `skeptic`, `skill-to-page`, `skill-write`, `todo`, `tot`, `tp`, `using-git-worktrees`, `wargame`, `why`, `why-old`, `www`, `zoom-out` |
| `grok-discovery` | 2 | `go`, `grok-parallel` |
| `grok-parallel` | 2 | `go`, `notice` |
| `grok-route` | 3 | `go`, `grok-parallel`, `grok-verify` |
| `grok-safe-git` | 3 | `go`, `grok-parallel`, `grok-verify` |
| `grok-verify` | 5 | `go`, `grok-parallel`, `refactor`, `skill-dev`, `tp` |
| `handoff` | 37 | `aar`, `ask`, `behave`, `check`, `chs`, `close`, `code`, `debrief`, `design`, `dream`, `find`, `fullstack-dev`, `go`, `grok-route`, `grok-verify`, `improve`, `maintain`, `notice`, `packet`, `plan-writer`, `planning`, `prompt-patterns`, `prospect`, `recap`, `refactor`, `refine`, `review`, `rns`, `s`, `skill-dev`, `todo`, `tp`, `trace`, `wargame`, `why`, `workspace-health`, `writing-plans` |
| `help` | 1 | `nlm-to-wiki` |
| `mmx` | 11 | `design`, `minimax-multimodal-toolkit`, `minimax-music-gen`, `minimax-music-playlist`, `model-benchmark`, `nlm-to-wiki`, `research`, `search-fleet`, `tp`, `web`, `why` |
| `model-benchmark` | 1 | `model-discover` |
| `notice` | 8 | `check`, `close`, `design`, `dream`, `game-tilesets`, `skill-dev`, `skill-write`, `tp` |
| `packet` | 13 | `aar`, `ai-api`, `ai-cli`, `check`, `close`, `code`, `design`, `go`, `improve`, `planning`, `preflight`, `review`, `why` |
| `plan-writer` | 4 | `design`, `go`, `grok-parallel`, `refine` |
| `preflight` | 2 | `design`, `tp` |
| `recover` | 5 | `config-audit`, `main`, `maintain`, `skill-prune`, `workspace-health` |
| `red-team` | 20 | `aar`, `claude-audit`, `close`, `debrief`, `design`, `dream`, `gitpack`, `improve`, `notice`, `pre-mortem`, `preflight`, `retro`, `review`, `risks`, `skill-audit`, `skill-dev`, `tp`, `why`, `why-old`, `www` |
| `refine` | 24 | `aar`, `brainstorming`, `debrief`, `design`, `dream`, `go`, `handoff`, `keep`, `mermaid-c4`, `minimax-music-gen`, `mlc`, `model-benchmark`, `note`, `plan-writer`, `probe`, `prompt_refiner`, `red-team`, `refactor`, `review`, `s`, `sequential-thinking`, `tp`, `wargame`, `www` |
| `review` | 106 | `aar`, `agy`, `ai-api`, `ai-cli`, `ai-models`, `aid`, `bf`, `brainstorming`, `check`, `chs`, `claude-audit`, `close`, `code-review`, `codebase-to-course`, `codex`, `concept-mapper`, `constitutional-patterns`, `create-workflow`, `debrief`, `debt`, `decision-tree`, `design`, `discover`, `dispatching-parallel-agents`, `doc-compiler`, `dream`, `execute-plan`, `executing-plans`, `friction`, `fullstack-dev`, `git`, `gitready`, `go`, `google-ai-usage-monitor`, `grok-discovery`, `grok-parallel`, `grok-verify`, `handoff`, `imagine`, `implement`, `improve`, `init`, `intelligence-stream-analyze`, `keep`, `learn`, `main`, `main-review`, `marketplace-bridge`, `mermaid-c4`, `minimax-multimodal-toolkit`, `minimax-music-gen`, `mlc`, `mmx`, `model-benchmark`, `model-discover`, `nlm-to-wiki`, `note`, `notice`, `packet`, `plan-writer`, `planning`, `plugin-installer`, `pr-babysit`, `pre-mortem`, `preflight`, `reason`, `recover`, `red-team`, `refactor`, `refine`, `reflect`, `review-pr`, `review_bundle`, `risks`, `sequential-thinking`, `simplify-enhanced`, `skill-audit`, `skill-dev`, `skill-from-docs`, `skill-similarity`, `skill-to-page`, `skill-write`, `snapshot`, `solo-dev-authority`, `specify`, `sqd`, `stale`, `subagent-driven-development`, `t`, `task`, `team`, `tilldone`, `tldr-router`, `todo`, `tp`, `trace`, `uci`, `vision-analysis`, `wargame`, `web`, `why`, `why-old`, `writing-plans`, `www`, `yt-is`, `yt-nlm` |
| `search-fleet` | 1 | `web` |
| `skill-dev` | 3 | `create-skill`, `red-team`, `tp` |
| `skill-prune` | 5 | `config-audit`, `create-skill`, `maintain`, `skill-dev`, `workspace-health` |
| `tasks` | 2 | `go`, `team` |
| `todo` | 1 | `design` |
| `tp` | 31 | `aar`, `ai-api`, `ai-probe-nim`, `bf`, `close`, `config-audit`, `design`, `dream`, `fullstack-dev`, `go`, `handoff`, `id`, `marketplace-bridge`, `mmx`, `model-benchmark`, `model-discover`, `notice`, `plan-writer`, `red-team`, `refactor`, `refine`, `review`, `skill-dev`, `skill-to-page`, `tdd`, `todo`, `web`, `why`, `why-old`, `workspace-health`, `www` |
| `wargame` | 2 | `plan-writer`, `red-team` |
| `web` | 32 | `agy`, `ai-models`, `brainstorming`, `build-with-ai`, `cks`, `codex`, `crawl`, `crawl4ai`, `design`, `find`, `frontend-dev`, `gitingest`, `go`, `imagine`, `improve`, `keep`, `minimax-multimodal-toolkit`, `mmx`, `nlm-bulk-ingest`, `note`, `notebooklm`, `perplexity-web-mcp`, `prospect`, `risks`, `search-fleet`, `subagent-driven-development`, `tp`, `usm`, `ux`, `www`, `yt-is`, `yt-selenium` |
| `why` | 79 | `aar`, `ai-models`, `ask`, `av`, `brainstorming`, `check`, `chs`, `cks`, `close`, `code-review`, `codebase-to-course`, `codex`, `config-audit`, `context7`, `debrief`, `decision-tree`, `design`, `doc-compiler`, `dream`, `evolve`, `execute-plan`, `frontend-dev`, `game-animation-frames`, `genius`, `go`, `grok-discovery`, `handoff`, `implement`, `improve`, `improve-codebase-architecture`, `init`, `maintain`, `mm-quota`, `mmx`, `model-benchmark`, `model-discover`, `nlm-bulk-ingest`, `nlm-to-wiki`, `notebooklm`, `notice`, `plan-writer`, `planning`, `plugin-installer`, `pr-babysit`, `probe`, `prompt-patterns`, `prospect`, `reason`, `red-team`, `refactor`, `refine`, `reflect`, `review`, `review_bundle`, `risks`, `s`, `search-fleet`, `skeptic`, `skill-audit`, `skill-dev`, `skill-prune`, `skill-to-page`, `skill-write`, `solo-dev-authority`, `task`, `tldr-code`, `tldr-router`, `todo`, `tp`, `using-git-worktrees`, `verification-before-completion`, `video-vision`, `wargame`, `web`, `why-old`, `wiki`, `workspace-health`, `www`, `yt-selenium` |
| `wiki` | 46 | `aar`, `ask`, `check`, `claude-audit`, `close`, `config-audit`, `crawl`, `crawl4ai`, `create-skill`, `debrief`, `design`, `doc-compiler`, `dream`, `gitpack`, `go`, `grok-safe-git`, `handoff`, `improve`, `main`, `maintain`, `model-benchmark`, `model-discover`, `nlm-bulk-ingest`, `nlm-to-wiki`, `notice`, `packet`, `plan-writer`, `prompt-patterns`, `prospect`, `qmd-wiki`, `red-team`, `refactor`, `refine`, `review`, `search-fleet`, `skill-dev`, `skill-prune`, `todo`, `tp`, `ut`, `ux`, `wargame`, `web`, `why`, `workspace-health`, `www` |

## Capability registry (what functions the fleet provides)

Every capability the skill fleet declares via `provides:` frontmatter:

| Capability | Provided by |
|------------|-------------|
| `after-action-review` | `aar` |
| `capability-routed-search` | `search-fleet` |
| `capability-wiki-query` | `wiki` |
| `capability-wiki-write` | `wiki` |
| `code-review` | `review` |
| `completion-gate` | `grok-verify` |
| `content-discipline-for-plans` | `wargame` |
| `cost-tracking` | `model-benchmark` |
| `critical-friend-critique` | `tp` |
| `cross-model-second-opinion` | `agy`, `codex`, `mmx` |
| `design-doc-production` | `design` |
| `discovery-dispatch` | `go` |
| `engineering-orchestration` | `go` |
| `evidence-backed-inventory` | `preflight` |
| `feedback-to-wiki` | `why` |
| `file-recovery` | `recover` |
| `fleet-maintenance` | `maintain` |
| `gate-resolution` | `close` |
| `gemini-reasoning` | `agy` |
| `git-safety-preflight` | `grok-safe-git` |
| `grok-documentation-help` | `help` |
| `handoff-auto-update` | `handoff` |
| `handoff-write` | `handoff` |
| `image-generation-guidance` | `imagine` |
| `knowledge-hygiene` | `skill-prune` |
| `latency-benchmark` | `model-benchmark` |
| `marketplace-skill-discovery` | `marketplace-bridge` |
| `mid-conversation-observation-surfacing` | `notice` |
| `minimax-vision` | `mmx` |
| `minimax-web-search` | `mmx` |
| `model-discovery` | `model-discover` |
| `multi-backend-search` | `web` |
| `offline-memory-consolidation` | `dream` |
| `openai-reasoning` | `codex` |
| `opportunity-landscape` | `aar` |
| `package-routing` | `grok-route` |
| `parallel-fan-out` | `grok-parallel` |
| `parallel-implement-dispatch` | `go` |
| `pattern-library-query` | `why` |
| `persistent-task-store` | `tasks` |
| `plan-writing` | `plan-writer` |
| `prompting-techniques-reference` | `prompt-patterns` |
| `quality-scoring` | `model-benchmark` |
| `root-cause-analysis` | `why` |
| `rrf-aggregation` | `search-fleet` |
| `rrf-merge` | `web` |
| `safe-git-preflight-dispatch` | `go` |
| `session-close-accounting` | `close` |
| `session-export` | `packet` |
| `session-opportunity-review` | `tp` |
| `session-retrospective` | `debrief` |
| `session-verification` | `check` |
| `skill-improvement` | `skill-dev` |
| `skill-measurement` | `skill-dev` |
| `skill-scaffolding` | `create-skill` |
| `source-authority-discovery` | `grok-discovery` |
| `structural-refactor` | `refactor` |
| `subagent-dispatch` | `check`, `debrief`, `grok-parallel`, `review`, `tp`, `www` |
| `system-exploration` | `tp` |
| `task-refinement` | `refine` |
| `value-accounting` | `aar` |
| `verified-findings-on-disk` | `review` |
| `verify-dispatch` | `go` |
| `web-ingestion` | `crawl4ai` |
| `wiki-web-wiki-research` | `www` |
| `workspace-prioritized-action-list` | `todo` |

## Capabilities by domain

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

### discovery

| Capability | Skills |
|------------|--------|
| `capability-routed-search` | `search-fleet` |
| `evidence-backed-inventory` | `preflight` |
| `marketplace-skill-discovery` | `marketplace-bridge` |
| `multi-backend-search` | `web` |
| `plan-writing` | `plan-writer` |
| `rrf-aggregation` | `search-fleet` |
| `rrf-merge` | `web` |
| `source-authority-discovery` | `grok-discovery` |
| `subagent-dispatch` | `www` |
| `task-refinement` | `refine` |
| `web-ingestion` | `crawl4ai` |
| `wiki-web-wiki-research` | `www` |

### fleet-ops

| Capability | Skills |
|------------|--------|
| `cost-tracking` | `model-benchmark` |
| `file-recovery` | `recover` |
| `grok-documentation-help` | `help` |
| `latency-benchmark` | `model-benchmark` |
| `model-discovery` | `model-discover` |
| `persistent-task-store` | `tasks` |
| `quality-scoring` | `model-benchmark` |
| `workspace-prioritized-action-list` | `todo` |

### implementation

| Capability | Skills |
|------------|--------|
| `image-generation-guidance` | `imagine` |
| `structural-refactor` | `refactor` |

### knowledge

| Capability | Skills |
|------------|--------|
| `capability-wiki-query` | `wiki` |
| `capability-wiki-write` | `wiki` |
| `prompting-techniques-reference` | `prompt-patterns` |

### lifecycle

| Capability | Skills |
|------------|--------|
| `after-action-review` | `aar` |
| `feedback-to-wiki` | `why` |
| `gate-resolution` | `close` |
| `handoff-auto-update` | `handoff` |
| `handoff-write` | `handoff` |
| `mid-conversation-observation-surfacing` | `notice` |
| `opportunity-landscape` | `aar` |
| `pattern-library-query` | `why` |
| `root-cause-analysis` | `why` |
| `session-close-accounting` | `close` |
| `session-export` | `packet` |
| `session-retrospective` | `debrief` |
| `subagent-dispatch` | `debrief` |
| `value-accounting` | `aar` |

### orchestration

| Capability | Skills |
|------------|--------|
| `discovery-dispatch` | `go` |
| `engineering-orchestration` | `go` |
| `git-safety-preflight` | `grok-safe-git` |
| `package-routing` | `grok-route` |
| `parallel-fan-out` | `grok-parallel` |
| `parallel-implement-dispatch` | `go` |
| `safe-git-preflight-dispatch` | `go` |
| `subagent-dispatch` | `grok-parallel` |
| `verify-dispatch` | `go` |

### review

| Capability | Skills |
|------------|--------|
| `code-review` | `review` |
| `content-discipline-for-plans` | `wargame` |
| `critical-friend-critique` | `tp` |
| `session-opportunity-review` | `tp` |
| `subagent-dispatch` | `review`, `tp` |
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
| `subagent-dispatch` | `check` |


## Per-skill edges

| Skill | Delegates to | Consumes provider | Provides |
|-------|-------------|------------------|
| `aar` | `check`, `close`, `design`, `go`, `handoff`, `packet`, `red-team`, `refine`, `review`, `tp`, `why`, `wiki` | `exa`, `gh`, `nlm` | `after-action-review`, `opportunity-landscape`, `value-accounting` |
| `adr` | — | — | — |
| `agy` | `debrief`, `design`, `review`, `web` | `agy`, `exa`, `gh` | `cross-model-second-opinion`, `gemini-reasoning` |
| `agy` | `check`, `design`, `review` | — | — |
| `ai-api` | `check`, `design`, `go`, `packet`, `review`, `tp` | — | — |
| `ai-cli` | `agy`, `check`, `packet`, `review` | `agy` | — |
| `ai-models` | `check`, `review`, `web`, `why` | — | — |
| `ai-probe-benchmark` | `check` | — | — |
| `ai-probe-nim` | `tp` | — | — |
| `ai-probe-openrouter` | — | — | — |
| `ai-probe-router` | `check` | — | — |
| `aid` | `check`, `review` | — | — |
| `all` | — | — | — |
| `ask` | `check`, `design`, `handoff`, `why`, `wiki` | — | — |
| `av` | `why` | — | — |
| `avant-garde-ui` | `design`, `go` | — | — |
| `behave` | `check`, `debrief`, `design`, `handoff` | — | — |
| `bf` | `check`, `design`, `review`, `tp` | — | — |
| `bifrost` | — | — | — |
| `brainstorming` | `check`, `design`, `go`, `refine`, `review`, `web`, `why` | — | — |
| `build` | `check`, `go` | — | — |
| `build-with-ai` | `web` | — | — |
| `capture` | `check` | — | — |
| `cc-model-router` | `design` | — | — |
| `changelog` | `check` | — | — |
| `check` | `agy`, `close`, `design`, `go`, `handoff`, `notice`, `packet`, `review`, `why`, `wiki` | — | `session-verification`, `subagent-dispatch` |
| `check` | `codex`, `design`, `go`, `review`, `wiki` | — | — |
| `chs` | `check`, `handoff`, `review`, `why` | — | — |
| `chs-eval` | — | — | — |
| `cks` | `web`, `why` | — | — |
| `claude-audit` | `check`, `close`, `debrief`, `design`, `go`, `red-team`, `review`, `wiki` | — | — |
| `close` | `aar`, `check`, `debrief`, `design`, `go`, `handoff`, `notice`, `packet`, `red-team`, `review`, `tp`, `why`, `wiki` | — | `gate-resolution`, `session-close-accounting` |
| `code` | `check`, `design`, `go`, `handoff`, `packet` | — | — |
| `code-flow-visualizer` | — | — | — |
| `code-review` | `design`, `go`, `review`, `why` | — | — |
| `code-review` | `check`, `review` | — | — |
| `codebase-to-course` | `check`, `design`, `go`, `review`, `why` | — | — |
| `codex` | `agy`, `debrief`, `design`, `review`, `web`, `why` | `agy`, `codex`, `exa`, `gh` | `cross-model-second-opinion`, `openai-reasoning` |
| `codex` | `check`, `design`, `review`, `why` | `codex` | — |
| `concept-mapper` | `check`, `review` | — | — |
| `config-audit` | `check`, `recover`, `skill-prune`, `tp`, `why`, `wiki` | — | — |
| `constitutional-patterns` | `check`, `review` | — | — |
| `constraints` | — | — | — |
| `context7` | `check`, `why` | `context7` | — |
| `contract-status` | — | — | — |
| `crawl` | `check`, `crawl4ai`, `web`, `wiki` | — | — |
| `crawl4ai` | `check`, `web`, `wiki` | `exa`, `firecrawl`, `gh` | `web-ingestion` |
| `create-skill` | `skill-dev`, `skill-prune`, `wiki` | `exa` | `skill-scaffolding` |
| `create-skill` | — | — | — |
| `create-workflow` | `check`, `review` | — | — |
| `csf-nip-integration` | `check` | — | — |
| `debrief` | `check`, `go`, `refine`, `review`, `why`, `wiki` | `gh` | `session-retrospective`, `subagent-dispatch` |
| `debrief` | `check`, `close`, `design`, `go`, `handoff`, `red-team`, `review`, `why`, `wiki` | — | — |
| `debt` | `go`, `review` | — | — |
| `decision-tree` | `design`, `review`, `why` | — | — |
| `design` | `check`, `go`, `handoff`, `mmx`, `plan-writer`, `preflight`, `red-team`, `refine`, `review`, `todo`, `tp`, `web`, `why`, `wiki` | `exa`, `firecrawl`, `gh`, `mmx` | `design-doc-production` |
| `design` | `check`, `go`, `notice`, `preflight`, `red-team`, `review`, `web`, `why`, `wiki` | `minimax-search` | — |
| `design` | `check`, `go`, `packet`, `review` | — | — |
| `diagnose` | — | — | — |
| `discover` | `check`, `design`, `review` | — | — |
| `dispatching-parallel-agents` | `check`, `review` | — | — |
| `doc-compiler` | `check`, `close`, `design`, `go`, `review`, `why`, `wiki` | — | — |
| `docs` | `check`, `go` | — | — |
| `docx` | — | — | — |
| `dream` | `aar`, `check`, `close`, `debrief`, `design`, `go`, `handoff`, `notice`, `red-team`, `refine`, `review`, `tp`, `why`, `wiki` | `episodic-memory`, `exa`, `gh` | `offline-memory-consolidation` |
| `dream` | `check` | — | — |
| `epistemic-check` | `check` | — | — |
| `evidence-driven-experiment-loop` | — | — | — |
| `evolve` | `check`, `design`, `why` | — | — |
| `execute-plan` | `check`, `design`, `go`, `review`, `why` | — | — |
| `executing-plans` | `review` | — | — |
| `execution-clarity` | `check` | — | — |
| `export-session` | `debrief` | — | — |
| `find` | `check`, `handoff`, `web` | — | — |
| `finishing-a-development-branch` | `check`, `go` | — | — |
| `friction` | `debrief`, `review` | — | — |
| `frontend-dev` | `check`, `design`, `web`, `why` | — | — |
| `fullstack-dev` | `check`, `close`, `design`, `go`, `handoff`, `review`, `tp` | — | — |
| `game-animation-frames` | `check`, `why` | — | — |
| `game-asset-core` | — | — | — |
| `game-character-consistency` | `check` | — | — |
| `game-tilesets` | `notice` | — | — |
| `game-ui-icons` | `design` | — | — |
| `garden` | — | — | — |
| `genius` | `why` | — | — |
| `git` | `check`, `review` | — | — |
| `gitingest` | `check`, `go`, `web` | `nlm` | — |
| `gitpack` | `check`, `design`, `go`, `red-team`, `wiki` | — | — |
| `gitready` | `check`, `review` | — | — |
| `go` | `check`, `design`, `grok-discovery`, `grok-parallel`, `grok-route`, `grok-safe-git`, `grok-verify`, `handoff`, `packet`, `plan-writer`, `refine`, `review`, `tp`, `web`, `why`, `wiki` | `brave`, `exa`, `gh`, `nlm` | `discovery-dispatch`, `engineering-orchestration`, `parallel-implement-dispatch`, `safe-git-preflight-dispatch`, `verify-dispatch` |
| `go` | `check`, `debrief`, `design`, `handoff`, `review`, `tasks`, `tp`, `why` | — | — |
| `google-ai-usage-monitor` | `check`, `go`, `review` | — | — |
| `grok-discovery` | `review`, `why` | `gh` | `source-authority-discovery` |
| `grok-go` | `go` | — | — |
| `grok-parallel` | `design`, `go`, `grok-discovery`, `grok-route`, `grok-safe-git`, `grok-verify`, `plan-writer`, `review` | `exa`, `gh` | `parallel-fan-out`, `subagent-dispatch` |
| `grok-route` | `handoff` | — | `package-routing` |
| `grok-safe-git` | `check`, `close`, `wiki` | `gh` | `git-safety-preflight` |
| `grok-sdlc` | `go` | — | — |
| `grok-verify` | `check`, `close`, `grok-route`, `grok-safe-git`, `handoff`, `review` | `exa`, `gh` | `completion-gate` |
| `handoff` | `aar`, `check`, `close`, `debrief`, `design`, `go`, `refine`, `review`, `tp`, `why`, `wiki` | `exa`, `gh` | `handoff-auto-update`, `handoff-write` |
| `help` | `check` | — | `grok-documentation-help` |
| `id` | `tp` | — | — |
| `imagine` | `check`, `review`, `web` | `exa`, `gh` | `image-generation-guidance` |
| `imagine` | `check`, `review`, `web` | — | — |
| `implement` | `check`, `design`, `go`, `review`, `why` | — | — |
| `improve` | `check`, `debrief`, `design`, `handoff`, `packet`, `red-team`, `review`, `web`, `why`, `wiki` | — | — |
| `improve-codebase-architecture` | `design`, `why` | — | — |
| `index` | — | — | — |
| `init` | `check`, `review`, `why` | — | — |
| `intelligence-stream-analyze` | `check`, `review` | — | — |
| `intelligence-stream-ingest` | — | — | — |
| `keep` | `check`, `refine`, `review`, `web` | — | — |
| `learn` | `check`, `review` | — | — |
| `lmc` | `check`, `debrief`, `go` | — | — |
| `main` | `check`, `recover`, `review`, `wiki` | — | — |
| `main-review` | `review` | — | — |
| `maintain` | `check`, `close`, `design`, `handoff`, `recover`, `skill-prune`, `why`, `wiki` | `gh` | `fleet-maintenance` |
| `marketplace-bridge` | `review`, `tp` | — | `marketplace-skill-discovery` |
| `mermaid-c4` | `refine`, `review` | — | — |
| `minimax-multimodal-toolkit` | `mmx`, `review`, `web` | `mmx` | — |
| `minimax-music-gen` | `check`, `go`, `mmx`, `refine`, `review` | `mmx` | — |
| `minimax-music-playlist` | `check`, `go`, `mmx` | `mmx` | — |
| `mlc` | `debrief`, `go`, `refine`, `review` | — | — |
| `mm-quota` | `check`, `design`, `why` | — | — |
| `mmx` | `agy`, `check`, `codex`, `design`, `review`, `tp`, `web`, `why` | `agy`, `codex`, `exa`, `gh`, `mmx` | `cross-model-second-opinion`, `minimax-vision`, `minimax-web-search` |
| `model-benchmark` | `check`, `go`, `mmx`, `refine`, `review`, `tp`, `why`, `wiki` | `agy`, `codex`, `exa`, `gh`, `mmx` | `cost-tracking`, `latency-benchmark`, `quality-scoring` |
| `model-discover` | `model-benchmark`, `review`, `tp`, `why`, `wiki` | — | `model-discovery` |
| `nlm` | `check` | `nlm`, `notebooklm` | — |
| `nlm-bulk-ingest` | `check`, `design`, `web`, `why`, `wiki` | — | — |
| `nlm-to-wiki` | `check`, `codex`, `help`, `mmx`, `why`, `wiki` | `mmx`, `notebooklm` | — |
| `nlm-to-wiki` | `check`, `review`, `wiki` | `nlm` | — |
| `note` | `check`, `refine`, `review`, `web` | — | — |
| `notebooklm` | `check`, `web`, `why` | — | — |
| `notice` | `aar`, `check`, `close`, `design`, `go`, `grok-parallel`, `handoff`, `red-team`, `review`, `tp`, `why`, `wiki` | `exa`, `gh` | `mid-conversation-observation-surfacing` |
| `pace` | — | — | — |
| `packet` | `aar`, `check`, `design`, `handoff`, `review`, `wiki` | `exa`, `gh` | `session-export` |
| `pdf` | `check` | — | — |
| `perf` | — | — | — |
| `performance-profiler` | — | — | — |
| `perplexity-web-mcp` | `check`, `web` | `pwm` | — |
| `plan-writer` | `aar`, `check`, `design`, `go`, `handoff`, `refine`, `review`, `tp`, `wargame`, `why`, `wiki` | `exa`, `gh` | `plan-writing` |
| `planning` | `check`, `close`, `design`, `go`, `handoff`, `packet`, `review`, `why` | — | — |
| `plugin-installer` | `check`, `review`, `why` | — | — |
| `pptx` | `check`, `close` | — | — |
| `pr-babysit` | `check`, `go`, `review`, `why` | — | — |
| `pre-mortem` | `check`, `red-team`, `review` | — | — |
| `preflight` | `check`, `red-team`, `review` | — | `evidence-backed-inventory` |
| `preflight` | `packet` | — | — |
| `prime` | `check`, `go` | — | — |
| `probe` | `check`, `close`, `refine`, `why` | — | — |
| `profile` | — | — | — |
| `prompt-enhancer` | — | — | — |
| `prompt-patterns` | `check`, `handoff`, `why`, `wiki` | `exa`, `gh` | `prompting-techniques-reference` |
| `prompt_refiner` | `design`, `refine` | — | — |
| `prospect` | `check`, `handoff`, `web`, `why`, `wiki` | `search-research` | — |
| `qmd-wiki` | `wiki` | — | — |
| `quota` | `check` | — | — |
| `ralph` | — | — | — |
| `rca` | `check` | — | — |
| `reason` | `codex`, `design`, `go`, `review`, `why` | — | — |
| `recap` | `check`, `debrief`, `design`, `go`, `handoff` | — | — |
| `recover` | `check`, `review` | — | `file-recovery` |
| `recover` | `check`, `review` | — | — |
| `red-team` | `aar`, `check`, `close`, `debrief`, `design`, `go`, `refine`, `review`, `skill-dev`, `tp`, `wargame`, `why`, `wiki` | — | — |
| `refactor` | `check`, `close`, `go`, `grok-verify`, `handoff`, `refine`, `review`, `tp`, `wiki` | `exa`, `gh`, `nlm` | `structural-refactor` |
| `refactor` | `check`, `design`, `handoff`, `why` | — | — |
| `refine` | `check`, `design`, `go`, `handoff`, `plan-writer`, `review`, `tp`, `why`, `wiki` | `exa`, `gh` | `task-refinement` |
| `reflect` | `check`, `review`, `why` | — | — |
| `repomix` | — | — | — |
| `research` | `go`, `mmx` | — | — |
| `response-atomicity` | — | — | — |
| `resume-claude` | — | — | — |
| `resume-codex` | `codex` | `codex` | — |
| `resume-cursor` | — | — | — |
| `retro` | `check`, `debrief`, `red-team` | — | — |
| `review` | `check`, `close`, `codex`, `go`, `handoff`, `packet`, `red-team`, `refine`, `tp`, `why`, `wiki` | `codex`, `exa`, `gh` | `code-review`, `subagent-dispatch`, `verified-findings-on-disk` |
| `review` | `check`, `design`, `tp`, `why` | — | — |
| `review` | `check`, `design`, `red-team`, `why` | — | — |
| `review-pr` | `review` | — | — |
| `review_bundle` | `check`, `design`, `review`, `why` | — | — |
| `risks` | `check`, `design`, `red-team`, `review`, `web`, `why` | — | — |
| `rns` | `check`, `go`, `handoff` | — | — |
| `s` | `check`, `design`, `handoff`, `refine`, `why` | — | — |
| `search-fleet` | `agy`, `mmx`, `web`, `why`, `wiki` | `agy`, `ddg`, `exa`, `firecrawl`, `gh`, `mmx`, `perplexity`, `pwm`, `reddit`, `search-research`, `tavily` | `capability-routed-search`, `rrf-aggregation` |
| `sequential-thinking` | `check`, `refine`, `review` | — | — |
| `ship` | `go` | — | — |
| `simplify-enhanced` | `check`, `review` | — | — |
| `skeptic` | `check`, `go`, `why` | — | — |
| `skill-audit` | `check`, `debrief`, `design`, `red-team`, `review`, `why` | — | — |
| `skill-dev` | `aar`, `check`, `close`, `create-skill`, `design`, `grok-verify`, `handoff`, `notice`, `red-team`, `review`, `skill-prune`, `tp`, `why`, `wiki` | `exa`, `gh` | `skill-improvement`, `skill-measurement` |
| `skill-from-docs` | `check`, `review` | — | — |
| `skill-prune` | `recover`, `why`, `wiki` | — | `knowledge-hygiene` |
| `skill-similarity` | `check`, `review` | — | — |
| `skill-to-page` | `check`, `close`, `design`, `go`, `review`, `tp`, `why` | — | — |
| `skill-write` | `check`, `design`, `go`, `notice`, `review`, `why` | — | — |
| `slc` | `check` | — | — |
| `snapshot` | `check`, `review` | — | — |
| `solo-dev-authority` | `check`, `review`, `why` | — | — |
| `specify` | `design`, `review` | — | — |
| `sqa` | — | — | — |
| `sqd` | `review` | — | — |
| `stale` | `check`, `review` | — | — |
| `subagent-driven-development` | `check`, `review`, `web` | — | — |
| `t` | `check`, `review` | — | — |
| `task` | `check`, `review`, `why` | — | — |
| `tasks` | `agy`, `check` | `agy`, `codex`, `exa`, `gh` | `persistent-task-store` |
| `tdd` | `check`, `tp` | — | — |
| `team` | `check`, `close`, `review`, `tasks` | — | — |
| `tilldone` | `check`, `review` | — | — |
| `tldr-code` | `check`, `why` | — | — |
| `tldr-deep` | — | — | — |
| `tldr-overview` | `check` | — | — |
| `tldr-router` | `review`, `why` | — | — |
| `tldr-stats` | `check` | — | — |
| `todo` | `check`, `close`, `go`, `handoff`, `review`, `tp`, `why`, `wiki` | `exa`, `gh`, `notebooklm`, `reddit` | `workspace-prioritized-action-list` |
| `top-problems` | `debrief` | — | — |
| `tot` | `go` | — | — |
| `tp` | `aar`, `agy`, `check`, `close`, `codex`, `debrief`, `design`, `go`, `grok-verify`, `handoff`, `mmx`, `notice`, `preflight`, `red-team`, `refine`, `review`, `skill-dev`, `web`, `why`, `wiki` | `codex`, `ddg`, `firecrawl`, `spawn-subagent` | `critical-friend-critique`, `session-opportunity-review`, `subagent-dispatch`, `system-exploration` |
| `trace` | `check`, `close`, `handoff`, `review` | — | — |
| `truth` | `check` | — | — |
| `uci` | `review` | — | — |
| `usage-query-skill` | — | — | — |
| `using-git-worktrees` | `check`, `design`, `go`, `why` | — | — |
| `using-superpowers` | `check` | — | — |
| `usm` | `check`, `web` | — | — |
| `ut` | `check`, `codex`, `wiki` | — | — |
| `ux` | `check`, `web`, `wiki` | — | — |
| `verification-before-completion` | `check`, `why` | — | — |
| `video-vision` | `check`, `why` | — | — |
| `vision-analysis` | `design`, `review` | — | — |
| `wargame` | `aar`, `check`, `design`, `go`, `handoff`, `refine`, `review`, `why`, `wiki` | `codex`, `gh` | `content-discipline-for-plans` |
| `web` | `check`, `design`, `mmx`, `search-fleet`, `tp`, `why`, `wiki` | `brave`, `ddg`, `duckduckgo`, `exa`, `firecrawl`, `hn-algolia`, `mmx`, `perplexity`, `reddit`, `search-research`, `stackexchange`, `tavily` | `multi-backend-search`, `rrf-merge` |
| `web` | `review` | `notebooklm`, `serper` | — |
| `why` | `aar`, `agy`, `check`, `codex`, `design`, `go`, `handoff`, `mmx`, `packet`, `red-team`, `review`, `tp`, `wiki` | `spawn-subagent` | `feedback-to-wiki`, `pattern-library-query`, `root-cause-analysis` |
| `why` | `check`, `go` | `search-research` | — |
| `why-old` | `aar`, `check`, `design`, `go`, `red-team`, `review`, `tp`, `why` | `exa`, `gh` | — |
| `wiki` | `check`, `design`, `why` | `exa`, `gh` | `capability-wiki-query`, `capability-wiki-write` |
| `wiki` | `check` | — | — |
| `workspace-health` | `check`, `codex`, `handoff`, `recover`, `skill-prune`, `tp`, `why`, `wiki` | — | — |
| `writing-plans` | `handoff`, `review` | — | — |
| `writing-skills` | `close` | — | — |
| `www` | `check`, `close`, `crawl4ai`, `design`, `go`, `red-team`, `refine`, `review`, `tp`, `web`, `why`, `wiki` | `ddg`, `firecrawl`, `gh`, `github-issues`, `hn-algolia`, `mmx`, `reddit` | `subagent-dispatch`, `wiki-web-wiki-research` |
| `yt-is` | `check`, `review`, `web` | — | — |
| `yt-nlm` | `check`, `review` | `notebooklm` | — |
| `yt-selenium` | `check`, `close`, `web`, `why` | — | — |
| `zoom-out` | `go` | — | — |

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
        "design",
        "go",
        "handoff",
        "packet",
        "red-team",
        "refine",
        "review",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh",
        "nlm"
      ],
      "references_wiki": [
        "friction-detection-operator-pushback-as-trigger",
        "operator-collaboration-style-and-leverage",
        "parallel-subagent-wait-all-gate",
        "user-modeling-for-agentic-clis"
      ],
      "provides": [
        "after-action-review",
        "opportunity-landscape",
        "value-accounting"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "agy",
      "path": "C:\\Users\\brsth\\.grok\\skills\\agy\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "debrief",
        "design",
        "review",
        "web"
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
      "name": "close",
      "path": "C:\\Users\\brsth\\.grok\\skills\\close\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "check",
        "debrief",
        "design",
        "go",
        "handoff",
        "notice",
        "packet",
        "red-team",
        "review",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "agentic-sdlc-skill-lifecycle-architecture",
        "prompting-patterns-for-ai-agent-control"
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
        "debrief",
        "design",
        "review",
        "web",
        "why"
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
      "name": "crawl4ai",
      "path": "C:\\Users\\brsth\\.grok\\skills\\crawl4ai\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
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
      "references_wiki": [
        "prompting-patterns-for-ai-agent-control"
      ],
      "provides": [
        "skill-scaffolding"
      ],
      "domain": "self-improvement"
    },
    {
      "name": "debrief",
      "path": "C:\\Users\\brsth\\.grok\\skills\\debrief\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "go",
        "refine",
        "review",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "gh"
      ],
      "references_wiki": [],
      "provides": [
        "session-retrospective",
        "subagent-dispatch"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "design",
      "path": "C:\\Users\\brsth\\.grok\\skills\\design\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "go",
        "handoff",
        "mmx",
        "plan-writer",
        "preflight",
        "red-team",
        "refine",
        "review",
        "todo",
        "tp",
        "web",
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
        "exemption-logic-as-conflict-signal",
        "llm-synthesis-quality-and-speed-techniques",
        "raising-coding-best-practices-in-ai-agents"
      ],
      "provides": [
        "design-doc-production"
      ],
      "domain": "design"
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
        "go",
        "handoff",
        "notice",
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
        "packet",
        "plan-writer",
        "refine",
        "review",
        "tp",
        "web",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "brave",
        "exa",
        "gh",
        "nlm"
      ],
      "references_wiki": [
        "prompting-patterns-for-ai-agent-control"
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
      "name": "grok-discovery",
      "path": "C:\\Users\\brsth\\.grok\\skills\\grok-discovery\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "review",
        "why"
      ],
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
        "design",
        "go",
        "grok-discovery",
        "grok-route",
        "grok-safe-git",
        "grok-verify",
        "plan-writer",
        "review"
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
      "delegates_to": [
        "handoff"
      ],
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
        "check",
        "close",
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
        "close",
        "grok-route",
        "grok-safe-git",
        "handoff",
        "review"
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
        "check",
        "close",
        "debrief",
        "design",
        "go",
        "refine",
        "review",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [],
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
      "delegates_to": [
        "check"
      ],
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
      "delegates_to": [
        "check",
        "review",
        "web"
      ],
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
      "name": "maintain",
      "path": "C:\\Users\\brsth\\.grok\\skills\\maintain\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "design",
        "handoff",
        "recover",
        "skill-prune",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "gh"
      ],
      "references_wiki": [
        "fleet-maintenance-skill-design"
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
        "review",
        "tp"
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
        "check",
        "codex",
        "design",
        "review",
        "tp",
        "web",
        "why"
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
        "mmx",
        "refine",
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
        "model-pool-not-chain"
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
        "model-benchmark",
        "review",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [
        "model-discovery"
      ],
      "domain": "fleet-ops"
    },
    {
      "name": "notice",
      "path": "C:\\Users\\brsth\\.grok\\skills\\notice\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "check",
        "close",
        "design",
        "go",
        "grok-parallel",
        "handoff",
        "red-team",
        "review",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
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
        "check",
        "design",
        "handoff",
        "review",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "agents-md-construction-best-practices",
        "conversation-distillation-review-packet-export"
      ],
      "provides": [
        "session-export"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "plan-writer",
      "path": "C:\\Users\\brsth\\.grok\\skills\\plan-writer\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "check",
        "design",
        "go",
        "handoff",
        "refine",
        "review",
        "tp",
        "wargame",
        "why",
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
        "check",
        "handoff",
        "why",
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
      "name": "refactor",
      "path": "C:\\Users\\brsth\\.grok\\skills\\refactor\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "go",
        "grok-verify",
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
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "exa",
        "gh"
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
      "name": "review",
      "path": "C:\\Users\\brsth\\.grok\\skills\\review\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "codex",
        "go",
        "handoff",
        "packet",
        "red-team",
        "refine",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "codex",
        "exa",
        "gh"
      ],
      "references_wiki": [
        "agentic-sdlc-skill-lifecycle-architecture"
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
        "agy",
        "mmx",
        "web",
        "why",
        "wiki"
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
      "name": "skill-dev",
      "path": "C:\\Users\\brsth\\.grok\\skills\\skill-dev\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "check",
        "close",
        "create-skill",
        "design",
        "grok-verify",
        "handoff",
        "notice",
        "red-team",
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
      "name": "tasks",
      "path": "C:\\Users\\brsth\\.grok\\skills\\tasks\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "agy",
        "check"
      ],
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
      "name": "todo",
      "path": "C:\\Users\\brsth\\.grok\\skills\\todo\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "go",
        "handoff",
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
      "references_wiki": [],
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
        "preflight",
        "red-team",
        "refine",
        "review",
        "skill-dev",
        "web",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "codex",
        "ddg",
        "firecrawl",
        "spawn-subagent"
      ],
      "references_wiki": [
        "analyst-exhibits-pattern-being-analyzed",
        "markdown-mermaid-rendering-agentic-clis-windows-11",
        "model-fit-and-post-hoc-behavioral-detection",
        "model-pool-not-chain",
        "model-pool-selection-policy-speed-quota-diversity",
        "model-tool-calling-capability-matrix"
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
      "name": "wargame",
      "path": "C:\\Users\\brsth\\.grok\\skills\\wargame\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "check",
        "design",
        "go",
        "handoff",
        "refine",
        "review",
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
      "name": "web",
      "path": "C:\\Users\\brsth\\.grok\\skills\\web\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "design",
        "mmx",
        "search-fleet",
        "tp",
        "why",
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
        "check",
        "codex",
        "design",
        "go",
        "handoff",
        "mmx",
        "packet",
        "red-team",
        "review",
        "tp",
        "wiki"
      ],
      "consumes_provider": [
        "spawn-subagent"
      ],
      "references_wiki": [
        "compaction-inherited-diagnosis-unverified-propagation",
        "multidimensional-root-cause-analysis-ai-agent-failures",
        "problem-first-systems-decomposition",
        "reactive-pattern-matching-and-closure-pressure"
      ],
      "provides": [
        "feedback-to-wiki",
        "pattern-library-query",
        "root-cause-analysis"
      ],
      "domain": "lifecycle"
    },
    {
      "name": "why-old",
      "path": "C:\\Users\\brsth\\.grok\\skills\\why-old\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "aar",
        "check",
        "design",
        "go",
        "red-team",
        "review",
        "tp",
        "why"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "fabricated-causal-chain-receipt-required",
        "multidimensional-root-cause-analysis-ai-agent-failures",
        "plausible-narratives-substitute-for-verification",
        "premature-closure-narrative-sufficiency-external-approaches",
        "problem-first-systems-decomposition",
        "reactive-pattern-matching-and-closure-pressure"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wiki",
      "path": "C:\\Users\\brsth\\.grok\\skills\\wiki\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "design",
        "why"
      ],
      "consumes_provider": [
        "exa",
        "gh"
      ],
      "references_wiki": [
        "inline-conditional-over-dispatch-for-skill-design",
        "skill-catalog",
        "synchronous-review-direct-write-pattern",
        "wikilinks"
      ],
      "provides": [
        "capability-wiki-query",
        "capability-wiki-write"
      ],
      "domain": "knowledge"
    },
    {
      "name": "www",
      "path": "C:\\Users\\brsth\\.grok\\skills\\www\\SKILL.md",
      "scope": "grok-user",
      "delegates_to": [
        "check",
        "close",
        "crawl4ai",
        "design",
        "go",
        "red-team",
        "refine",
        "review",
        "tp",
        "web",
        "why",
        "wiki"
      ],
      "consumes_provider": [
        "ddg",
        "firecrawl",
        "gh",
        "github-issues",
        "hn-algolia",
        "mmx",
        "reddit"
      ],
      "references_wiki": [
        "concurrent-cdp-auth-contention",
        "invariants-beat-environment-comfort",
        "notebooklm-cli-operational-gotchas",
        "parallel-subagent-wait-all-gate",
        "skill-catalog",
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
      "delegates_to": [
        "web"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "code-review",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\code-review\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [
        "design",
        "go",
        "review",
        "why"
      ],
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
      "delegates_to": [
        "check",
        "review"
      ],
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
        "check",
        "go",
        "notice",
        "preflight",
        "red-team",
        "review",
        "web",
        "why",
        "wiki"
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
        "check",
        "design",
        "go",
        "review",
        "why"
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
      "delegates_to": [
        "check",
        "why"
      ],
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
      "delegates_to": [
        "check"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "game-tilesets",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\game-tilesets\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [
        "notice"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "game-ui-icons",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\game-ui-icons\\SKILL.md",
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
      "name": "imagine",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\imagine\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [
        "check",
        "review",
        "web"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "implement",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\implement\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [
        "check",
        "design",
        "go",
        "review",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pdf",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\pdf\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [
        "check"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pptx",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\pptx\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [
        "check",
        "close"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "pr-babysit",
      "path": "C:\\Users\\brsth\\.grok\\bundled\\skills\\pr-babysit\\SKILL.md",
      "scope": "grok-bundled",
      "delegates_to": [
        "check",
        "go",
        "review",
        "why"
      ],
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
      "delegates_to": [
        "codex"
      ],
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
      "delegates_to": [
        "check",
        "design",
        "tp",
        "why"
      ],
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
        "design",
        "go",
        "handoff",
        "notice",
        "packet",
        "review",
        "why",
        "wiki"
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
        "check",
        "close",
        "debrief",
        "design",
        "go",
        "refine",
        "review",
        "skill-dev",
        "tp",
        "wargame",
        "why",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "parallel-subagent-wait-all-gate"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "avant-garde-ui",
      "path": "P:\\.agents\\skills\\avant-garde-ui\\SKILL.md",
      "scope": "grok-agents",
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
      "name": "config-audit",
      "path": "P:\\.agents\\skills\\config-audit\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "check",
        "recover",
        "skill-prune",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "llm-instruction-non-compliance-activation-gap-2026",
        "structural-enforcement-for-skipped-rules-grok-build-2026"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "contract-status",
      "path": "P:\\.agents\\skills\\contract-status\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "nlm-bulk-ingest",
      "path": "P:\\.agents\\skills\\nlm-bulk-ingest\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "check",
        "design",
        "web",
        "why",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [
        "notebooklm-cli-operational-gotchas",
        "notebooklm-source-limits-free-vs-paid",
        "semantic-clustering-bounded-size"
      ],
      "provides": [],
      "domain": ""
    },
    {
      "name": "nlm-to-wiki",
      "path": "P:\\.agents\\skills\\nlm-to-wiki\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "check",
        "codex",
        "help",
        "mmx",
        "why",
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
      "domain": ""
    },
    {
      "name": "notebooklm",
      "path": "P:\\.agents\\skills\\notebooklm\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "check",
        "web",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "preflight",
      "path": "P:\\.agents\\skills\\preflight\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "check",
        "red-team",
        "review"
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
      "delegates_to": [
        "check",
        "review"
      ],
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
        "recover",
        "why",
        "wiki"
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
      "name": "workspace-health",
      "path": "P:\\.agents\\skills\\workspace-health\\SKILL.md",
      "scope": "grok-agents",
      "delegates_to": [
        "check",
        "codex",
        "handoff",
        "recover",
        "skill-prune",
        "tp",
        "why",
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "cc-model-router",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-model-router\\SKILL.md",
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
      "name": "debt",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-lazy-closure-debt\\skills\\debt\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "go",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "agy",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\agy\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "design",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-api",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-api\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "design",
        "go",
        "packet",
        "review",
        "tp"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-cli",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-cli\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "agy",
        "check",
        "packet",
        "review"
      ],
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
      "delegates_to": [
        "check",
        "review",
        "web",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "ai-probe-benchmark",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-probe-benchmark\\SKILL.md",
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
      "name": "ai-probe-nim",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\ai-probe-nim\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "tp"
      ],
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
      "delegates_to": [
        "check"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "codex",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\codex\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "design",
        "review",
        "why"
      ],
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
      "delegates_to": [
        "check",
        "go",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "intelligence-stream-analyze",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-ai-api\\skills\\intelligence-stream-analyze\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
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
      "delegates_to": [
        "check",
        "web"
      ],
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
      "delegates_to": [
        "check"
      ],
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
        "check",
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
      "name": "claude-audit",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\claude-audit\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "close",
        "debrief",
        "design",
        "go",
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
        "check",
        "close",
        "design",
        "go",
        "handoff",
        "red-team",
        "review",
        "why",
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
        "check",
        "close",
        "design",
        "go",
        "review",
        "why",
        "wiki"
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
      "delegates_to": [
        "check"
      ],
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
        "debrief",
        "review"
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
        "check",
        "debrief",
        "design",
        "go",
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
        "check",
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
        "check",
        "go",
        "handoff"
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
        "check",
        "debrief",
        "design",
        "red-team",
        "review",
        "why"
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
        "check",
        "review"
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
      "delegates_to": [
        "check",
        "close",
        "handoff",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "why",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-analysis\\skills\\why\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "go"
      ],
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
        "check",
        "design",
        "handoff",
        "why",
        "wiki"
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
      "delegates_to": [
        "check",
        "design",
        "review",
        "tp"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "constitutional-patterns",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\constitutional-patterns\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
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
      "delegates_to": [
        "design",
        "review",
        "why"
      ],
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
        "check",
        "design",
        "why"
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
      "delegates_to": [
        "check",
        "review"
      ],
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
        "design",
        "refine"
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
      "delegates_to": [],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skill-from-docs",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\skill-from-docs\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
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
        "check",
        "close",
        "design",
        "go",
        "review",
        "tp",
        "why"
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
      "delegates_to": [
        "check",
        "design",
        "go",
        "notice",
        "review",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "solo-dev-authority",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-architect\\skills\\solo-dev-authority\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review",
        "why"
      ],
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
        "check",
        "review",
        "web"
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
      "delegates_to": [
        "check",
        "web"
      ],
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
        "codex",
        "design",
        "go",
        "review",
        "wiki"
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
      "delegates_to": [
        "web",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "concept-mapper",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\concept-mapper\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "csf-nip-integration",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\csf-nip-integration\\SKILL.md",
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
      "name": "lmc",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\lmc\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "debrief",
        "go"
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
        "debrief",
        "go",
        "refine",
        "review"
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
      "delegates_to": [
        "check",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "slc",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-lab\\skills\\slc\\SKILL.md",
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
      "name": "codebase-to-course",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\codebase-to-course\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "design",
        "go",
        "review",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "frontend-dev",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\frontend-dev\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "design",
        "web",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "fullstack-dev",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\fullstack-dev\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "close",
        "design",
        "go",
        "handoff",
        "review",
        "tp"
      ],
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
        "mmx",
        "review",
        "web"
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
        "check",
        "go",
        "mmx",
        "refine",
        "review"
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
      "delegates_to": [
        "check",
        "go",
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
      "name": "nlm",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\nlm\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check"
      ],
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
        "check",
        "review",
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
      "delegates_to": [
        "check",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "vision-analysis",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\vision-analysis\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "design",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "yt-is",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\yt-is\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review",
        "web"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "yt-nlm",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-media\\skills\\yt-nlm\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
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
      "delegates_to": [
        "check",
        "close",
        "web",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "av",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\av\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "brainstorming",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\brainstorming\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "design",
        "go",
        "refine",
        "review",
        "web",
        "why"
      ],
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
        "check",
        "design",
        "go",
        "handoff",
        "packet"
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
      "delegates_to": [
        "check",
        "review"
      ],
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
        "check",
        "go",
        "packet",
        "review"
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
      "delegates_to": [
        "check",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "docs",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\docs\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "go"
      ],
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
      "delegates_to": [
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "finishing-a-development-branch",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\finishing-a-development-branch\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "go"
      ],
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
        "check",
        "debrief",
        "design",
        "handoff",
        "review",
        "tasks",
        "tp",
        "why"
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
      "delegates_to": [
        "design",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "mermaid-c4",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\mermaid-c4\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "refine",
        "review"
      ],
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
        "check",
        "close",
        "design",
        "go",
        "handoff",
        "packet",
        "review",
        "why"
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
        "check",
        "red-team",
        "review"
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
      "delegates_to": [
        "packet"
      ],
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
      "delegates_to": [
        "wiki"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "rca",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\rca\\SKILL.md",
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
      "name": "refactor",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\refactor\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "design",
        "handoff",
        "why"
      ],
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
        "check",
        "design",
        "red-team",
        "why"
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
      "delegates_to": [
        "check",
        "design",
        "review",
        "why"
      ],
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
        "check",
        "design",
        "red-team",
        "review",
        "web",
        "why"
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
      "delegates_to": [
        "go"
      ],
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
        "design",
        "review"
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
        "check",
        "review"
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
      "delegates_to": [
        "check",
        "review",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tdd",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tdd\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "tp"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "team",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\team\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "close",
        "review",
        "tasks"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tilldone",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tilldone\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tldr-code",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tldr-code\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "why"
      ],
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
      "delegates_to": [
        "check"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tldr-router",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tldr-router\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "review",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tldr-stats",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\tldr-stats\\SKILL.md",
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
      "delegates_to": [
        "check",
        "design",
        "go",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "using-superpowers",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\using-superpowers\\SKILL.md",
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
      "name": "verification-before-completion",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\verification-before-completion\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "wiki",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\wiki\\SKILL.md",
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
      "name": "writing-plans",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\writing-plans\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "handoff",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "writing-skills",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\writing-skills\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "close"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "zoom-out",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-sdlc\\skills\\zoom-out\\SKILL.md",
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
      "name": "dream",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\dream\\SKILL.md",
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
      "name": "execution-clarity",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\execution-clarity\\SKILL.md",
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
      "name": "genius",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\genius\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "why"
      ],
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
        "check",
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
      "delegates_to": [
        "check",
        "close",
        "refine",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "prospect",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\prospect\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "handoff",
        "web",
        "why",
        "wiki"
      ],
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
      "delegates_to": [
        "codex",
        "design",
        "go",
        "review",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "reflect",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\reflect\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review",
        "why"
      ],
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
        "check",
        "design",
        "handoff",
        "refine",
        "why"
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
      "delegates_to": [
        "check",
        "refine",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "skeptic",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\skeptic\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "go",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "tot",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\tot\\SKILL.md",
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
      "name": "truth",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\truth\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": "validation"
    },
    {
      "name": "ut",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-thinking\\skills\\ut\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "codex",
        "wiki"
      ],
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
        "check",
        "web",
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
      "delegates_to": [
        "check",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "init",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\init\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review",
        "why"
      ],
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
        "check",
        "recover",
        "review",
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
      "delegates_to": [
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "mm-quota",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\mm-quota\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "design",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "plugin-installer",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\plugin-installer\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review",
        "why"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "recover",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\cc-skills-utils\\skills\\recover\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
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
        "check",
        "debrief",
        "design",
        "handoff",
        "packet",
        "red-team",
        "review",
        "web",
        "why",
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
      "delegates_to": [
        "check",
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "capture",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\capture\\SKILL.md",
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
      "name": "changelog",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\changelog\\SKILL.md",
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
      "delegates_to": [
        "check",
        "go"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "stale",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\quickstop\\skills\\stale\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "aid",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\search-research\\skills\\aid\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
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
      "delegates_to": [
        "check",
        "handoff",
        "review",
        "why"
      ],
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
      "delegates_to": [
        "check",
        "why"
      ],
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
        "check",
        "crawl4ai",
        "web",
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
        "check",
        "design",
        "review"
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
        "check",
        "handoff",
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
      "delegates_to": [
        "check",
        "go",
        "web"
      ],
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
      "delegates_to": [
        "check",
        "design",
        "go",
        "red-team",
        "wiki"
      ],
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
        "check",
        "refine",
        "review",
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
        "check",
        "refine",
        "review",
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
        "go",
        "mmx"
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
      "delegates_to": [
        "review"
      ],
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
      "delegates_to": [
        "tp"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    },
    {
      "name": "snapshot",
      "path": "P:\\packages\\.claude-marketplace\\plugins\\snapshot\\skills\\snapshot\\SKILL.md",
      "scope": "marketplace",
      "delegates_to": [
        "check",
        "review"
      ],
      "consumes_provider": [],
      "references_wiki": [],
      "provides": [],
      "domain": ""
    }
  ],
  "reverse": {
    "provider_consumers": {
      "gh": [
        "aar",
        "agy",
        "codex",
        "crawl4ai",
        "debrief",
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
        "packet",
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
        "why-old",
        "wiki",
        "www"
      ],
      "exa": [
        "aar",
        "agy",
        "codex",
        "crawl4ai",
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
        "notice",
        "packet",
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
        "why-old",
        "wiki"
      ],
      "nlm": [
        "aar",
        "gitingest",
        "go",
        "nlm",
        "nlm-to-wiki",
        "refactor"
      ],
      "agy": [
        "agy",
        "ai-cli",
        "codex",
        "mmx",
        "model-benchmark",
        "search-fleet",
        "tasks"
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
      "firecrawl": [
        "crawl4ai",
        "design",
        "search-fleet",
        "tp",
        "web",
        "www"
      ],
      "mmx": [
        "design",
        "minimax-multimodal-toolkit",
        "minimax-music-gen",
        "minimax-music-playlist",
        "mmx",
        "model-benchmark",
        "nlm-to-wiki",
        "search-fleet",
        "web",
        "www"
      ],
      "episodic-memory": [
        "dream"
      ],
      "brave": [
        "go",
        "web"
      ],
      "ddg": [
        "search-fleet",
        "tp",
        "web",
        "www"
      ],
      "perplexity": [
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
      "pwm": [
        "perplexity-web-mcp",
        "search-fleet"
      ],
      "tavily": [
        "search-fleet",
        "web"
      ],
      "notebooklm": [
        "nlm",
        "nlm-to-wiki",
        "todo",
        "web",
        "yt-nlm"
      ],
      "spawn-subagent": [
        "tp",
        "why"
      ],
      "hn-algolia": [
        "web",
        "www"
      ],
      "stackexchange": [
        "web"
      ],
      "duckduckgo": [
        "web"
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
      "go": [
        "aar",
        "ai-api",
        "avant-garde-ui",
        "brainstorming",
        "build",
        "check",
        "claude-audit",
        "close",
        "code",
        "code-review",
        "codebase-to-course",
        "debrief",
        "debt",
        "design",
        "doc-compiler",
        "docs",
        "dream",
        "execute-plan",
        "finishing-a-development-branch",
        "fullstack-dev",
        "gitingest",
        "gitpack",
        "google-ai-usage-monitor",
        "grok-go",
        "grok-parallel",
        "grok-sdlc",
        "handoff",
        "implement",
        "lmc",
        "minimax-music-gen",
        "minimax-music-playlist",
        "mlc",
        "model-benchmark",
        "notice",
        "plan-writer",
        "planning",
        "pr-babysit",
        "prime",
        "reason",
        "recap",
        "red-team",
        "refactor",
        "refine",
        "research",
        "review",
        "rns",
        "ship",
        "skeptic",
        "skill-to-page",
        "skill-write",
        "todo",
        "tot",
        "tp",
        "using-git-worktrees",
        "wargame",
        "why",
        "why-old",
        "www",
        "zoom-out"
      ],
      "tp": [
        "aar",
        "ai-api",
        "ai-probe-nim",
        "bf",
        "close",
        "config-audit",
        "design",
        "dream",
        "fullstack-dev",
        "go",
        "handoff",
        "id",
        "marketplace-bridge",
        "mmx",
        "model-benchmark",
        "model-discover",
        "notice",
        "plan-writer",
        "red-team",
        "refactor",
        "refine",
        "review",
        "skill-dev",
        "skill-to-page",
        "tdd",
        "todo",
        "web",
        "why",
        "why-old",
        "workspace-health",
        "www"
      ],
      "red-team": [
        "aar",
        "claude-audit",
        "close",
        "debrief",
        "design",
        "dream",
        "gitpack",
        "improve",
        "notice",
        "pre-mortem",
        "preflight",
        "retro",
        "review",
        "risks",
        "skill-audit",
        "skill-dev",
        "tp",
        "why",
        "why-old",
        "www"
      ],
      "refine": [
        "aar",
        "brainstorming",
        "debrief",
        "design",
        "dream",
        "go",
        "handoff",
        "keep",
        "mermaid-c4",
        "minimax-music-gen",
        "mlc",
        "model-benchmark",
        "note",
        "plan-writer",
        "probe",
        "prompt_refiner",
        "red-team",
        "refactor",
        "review",
        "s",
        "sequential-thinking",
        "tp",
        "wargame",
        "www"
      ],
      "packet": [
        "aar",
        "ai-api",
        "ai-cli",
        "check",
        "close",
        "code",
        "design",
        "go",
        "improve",
        "planning",
        "preflight",
        "review",
        "why"
      ],
      "why": [
        "aar",
        "ai-models",
        "ask",
        "av",
        "brainstorming",
        "check",
        "chs",
        "cks",
        "close",
        "code-review",
        "codebase-to-course",
        "codex",
        "config-audit",
        "context7",
        "debrief",
        "decision-tree",
        "design",
        "doc-compiler",
        "dream",
        "evolve",
        "execute-plan",
        "frontend-dev",
        "game-animation-frames",
        "genius",
        "go",
        "grok-discovery",
        "handoff",
        "implement",
        "improve",
        "improve-codebase-architecture",
        "init",
        "maintain",
        "mm-quota",
        "mmx",
        "model-benchmark",
        "model-discover",
        "nlm-bulk-ingest",
        "nlm-to-wiki",
        "notebooklm",
        "notice",
        "plan-writer",
        "planning",
        "plugin-installer",
        "pr-babysit",
        "probe",
        "prompt-patterns",
        "prospect",
        "reason",
        "red-team",
        "refactor",
        "refine",
        "reflect",
        "review",
        "review_bundle",
        "risks",
        "s",
        "search-fleet",
        "skeptic",
        "skill-audit",
        "skill-dev",
        "skill-prune",
        "skill-to-page",
        "skill-write",
        "solo-dev-authority",
        "task",
        "tldr-code",
        "tldr-router",
        "todo",
        "tp",
        "using-git-worktrees",
        "verification-before-completion",
        "video-vision",
        "wargame",
        "web",
        "why-old",
        "wiki",
        "workspace-health",
        "www",
        "yt-selenium"
      ],
      "check": [
        "aar",
        "agy",
        "ai-api",
        "ai-cli",
        "ai-models",
        "ai-probe-benchmark",
        "ai-probe-router",
        "aid",
        "ask",
        "behave",
        "bf",
        "brainstorming",
        "build",
        "capture",
        "changelog",
        "chs",
        "claude-audit",
        "close",
        "code",
        "code-review",
        "codebase-to-course",
        "codex",
        "concept-mapper",
        "config-audit",
        "constitutional-patterns",
        "context7",
        "crawl",
        "crawl4ai",
        "create-workflow",
        "csf-nip-integration",
        "debrief",
        "design",
        "discover",
        "dispatching-parallel-agents",
        "doc-compiler",
        "docs",
        "dream",
        "epistemic-check",
        "evolve",
        "execute-plan",
        "execution-clarity",
        "find",
        "finishing-a-development-branch",
        "frontend-dev",
        "fullstack-dev",
        "game-animation-frames",
        "game-character-consistency",
        "git",
        "gitingest",
        "gitpack",
        "gitready",
        "go",
        "google-ai-usage-monitor",
        "grok-safe-git",
        "grok-verify",
        "handoff",
        "help",
        "imagine",
        "implement",
        "improve",
        "init",
        "intelligence-stream-analyze",
        "keep",
        "learn",
        "lmc",
        "main",
        "maintain",
        "minimax-music-gen",
        "minimax-music-playlist",
        "mm-quota",
        "mmx",
        "model-benchmark",
        "nlm",
        "nlm-bulk-ingest",
        "nlm-to-wiki",
        "note",
        "notebooklm",
        "notice",
        "packet",
        "pdf",
        "perplexity-web-mcp",
        "plan-writer",
        "planning",
        "plugin-installer",
        "pptx",
        "pr-babysit",
        "pre-mortem",
        "preflight",
        "prime",
        "probe",
        "prompt-patterns",
        "prospect",
        "quota",
        "rca",
        "recap",
        "recover",
        "red-team",
        "refactor",
        "refine",
        "reflect",
        "retro",
        "review",
        "review_bundle",
        "risks",
        "rns",
        "s",
        "sequential-thinking",
        "simplify-enhanced",
        "skeptic",
        "skill-audit",
        "skill-dev",
        "skill-from-docs",
        "skill-similarity",
        "skill-to-page",
        "skill-write",
        "slc",
        "snapshot",
        "solo-dev-authority",
        "stale",
        "subagent-driven-development",
        "t",
        "task",
        "tasks",
        "tdd",
        "team",
        "tilldone",
        "tldr-code",
        "tldr-overview",
        "tldr-stats",
        "todo",
        "tp",
        "trace",
        "truth",
        "using-git-worktrees",
        "using-superpowers",
        "usm",
        "ut",
        "ux",
        "verification-before-completion",
        "video-vision",
        "wargame",
        "web",
        "why",
        "why-old",
        "wiki",
        "workspace-health",
        "www",
        "yt-is",
        "yt-nlm",
        "yt-selenium"
      ],
      "handoff": [
        "aar",
        "ask",
        "behave",
        "check",
        "chs",
        "close",
        "code",
        "debrief",
        "design",
        "dream",
        "find",
        "fullstack-dev",
        "go",
        "grok-route",
        "grok-verify",
        "improve",
        "maintain",
        "notice",
        "packet",
        "plan-writer",
        "planning",
        "prompt-patterns",
        "prospect",
        "recap",
        "refactor",
        "refine",
        "review",
        "rns",
        "s",
        "skill-dev",
        "todo",
        "tp",
        "trace",
        "wargame",
        "why",
        "workspace-health",
        "writing-plans"
      ],
      "close": [
        "aar",
        "check",
        "claude-audit",
        "debrief",
        "doc-compiler",
        "dream",
        "fullstack-dev",
        "grok-safe-git",
        "grok-verify",
        "handoff",
        "maintain",
        "notice",
        "planning",
        "pptx",
        "probe",
        "red-team",
        "refactor",
        "review",
        "skill-dev",
        "skill-to-page",
        "team",
        "todo",
        "tp",
        "trace",
        "writing-skills",
        "www",
        "yt-selenium"
      ],
      "review": [
        "aar",
        "agy",
        "ai-api",
        "ai-cli",
        "ai-models",
        "aid",
        "bf",
        "brainstorming",
        "check",
        "chs",
        "claude-audit",
        "close",
        "code-review",
        "codebase-to-course",
        "codex",
        "concept-mapper",
        "constitutional-patterns",
        "create-workflow",
        "debrief",
        "debt",
        "decision-tree",
        "design",
        "discover",
        "dispatching-parallel-agents",
        "doc-compiler",
        "dream",
        "execute-plan",
        "executing-plans",
        "friction",
        "fullstack-dev",
        "git",
        "gitready",
        "go",
        "google-ai-usage-monitor",
        "grok-discovery",
        "grok-parallel",
        "grok-verify",
        "handoff",
        "imagine",
        "implement",
        "improve",
        "init",
        "intelligence-stream-analyze",
        "keep",
        "learn",
        "main",
        "main-review",
        "marketplace-bridge",
        "mermaid-c4",
        "minimax-multimodal-toolkit",
        "minimax-music-gen",
        "mlc",
        "mmx",
        "model-benchmark",
        "model-discover",
        "nlm-to-wiki",
        "note",
        "notice",
        "packet",
        "plan-writer",
        "planning",
        "plugin-installer",
        "pr-babysit",
        "pre-mortem",
        "preflight",
        "reason",
        "recover",
        "red-team",
        "refactor",
        "refine",
        "reflect",
        "review-pr",
        "review_bundle",
        "risks",
        "sequential-thinking",
        "simplify-enhanced",
        "skill-audit",
        "skill-dev",
        "skill-from-docs",
        "skill-similarity",
        "skill-to-page",
        "skill-write",
        "snapshot",
        "solo-dev-authority",
        "specify",
        "sqd",
        "stale",
        "subagent-driven-development",
        "t",
        "task",
        "team",
        "tilldone",
        "tldr-router",
        "todo",
        "tp",
        "trace",
        "uci",
        "vision-analysis",
        "wargame",
        "web",
        "why",
        "why-old",
        "writing-plans",
        "www",
        "yt-is",
        "yt-nlm"
      ],
      "design": [
        "aar",
        "agy",
        "ai-api",
        "ask",
        "avant-garde-ui",
        "behave",
        "bf",
        "brainstorming",
        "cc-model-router",
        "check",
        "claude-audit",
        "close",
        "code",
        "code-review",
        "codebase-to-course",
        "codex",
        "debrief",
        "decision-tree",
        "discover",
        "doc-compiler",
        "dream",
        "evolve",
        "execute-plan",
        "frontend-dev",
        "fullstack-dev",
        "game-ui-icons",
        "gitpack",
        "go",
        "grok-parallel",
        "handoff",
        "implement",
        "improve",
        "improve-codebase-architecture",
        "maintain",
        "mm-quota",
        "mmx",
        "nlm-bulk-ingest",
        "notice",
        "packet",
        "plan-writer",
        "planning",
        "prompt_refiner",
        "reason",
        "recap",
        "red-team",
        "refactor",
        "refine",
        "review",
        "review_bundle",
        "risks",
        "s",
        "skill-audit",
        "skill-dev",
        "skill-to-page",
        "skill-write",
        "specify",
        "tp",
        "using-git-worktrees",
        "vision-analysis",
        "wargame",
        "web",
        "why",
        "why-old",
        "wiki",
        "www"
      ],
      "wiki": [
        "aar",
        "ask",
        "check",
        "claude-audit",
        "close",
        "config-audit",
        "crawl",
        "crawl4ai",
        "create-skill",
        "debrief",
        "design",
        "doc-compiler",
        "dream",
        "gitpack",
        "go",
        "grok-safe-git",
        "handoff",
        "improve",
        "main",
        "maintain",
        "model-benchmark",
        "model-discover",
        "nlm-bulk-ingest",
        "nlm-to-wiki",
        "notice",
        "packet",
        "plan-writer",
        "prompt-patterns",
        "prospect",
        "qmd-wiki",
        "red-team",
        "refactor",
        "refine",
        "review",
        "search-fleet",
        "skill-dev",
        "skill-prune",
        "todo",
        "tp",
        "ut",
        "ux",
        "wargame",
        "web",
        "why",
        "workspace-health",
        "www"
      ],
      "web": [
        "agy",
        "ai-models",
        "brainstorming",
        "build-with-ai",
        "cks",
        "codex",
        "crawl",
        "crawl4ai",
        "design",
        "find",
        "frontend-dev",
        "gitingest",
        "go",
        "imagine",
        "improve",
        "keep",
        "minimax-multimodal-toolkit",
        "mmx",
        "nlm-bulk-ingest",
        "note",
        "notebooklm",
        "perplexity-web-mcp",
        "prospect",
        "risks",
        "search-fleet",
        "subagent-driven-development",
        "tp",
        "usm",
        "ux",
        "www",
        "yt-is",
        "yt-selenium"
      ],
      "debrief": [
        "agy",
        "behave",
        "claude-audit",
        "close",
        "codex",
        "dream",
        "export-session",
        "friction",
        "go",
        "handoff",
        "improve",
        "lmc",
        "mlc",
        "recap",
        "red-team",
        "retro",
        "skill-audit",
        "top-problems",
        "tp"
      ],
      "aar": [
        "close",
        "dream",
        "handoff",
        "notice",
        "packet",
        "plan-writer",
        "red-team",
        "skill-dev",
        "tp",
        "wargame",
        "why",
        "why-old"
      ],
      "notice": [
        "check",
        "close",
        "design",
        "dream",
        "game-tilesets",
        "skill-dev",
        "skill-write",
        "tp"
      ],
      "agy": [
        "ai-cli",
        "check",
        "codex",
        "mmx",
        "search-fleet",
        "tasks",
        "tp",
        "why"
      ],
      "skill-prune": [
        "config-audit",
        "create-skill",
        "maintain",
        "skill-dev",
        "workspace-health"
      ],
      "skill-dev": [
        "create-skill",
        "red-team",
        "tp"
      ],
      "todo": [
        "design"
      ],
      "mmx": [
        "design",
        "minimax-multimodal-toolkit",
        "minimax-music-gen",
        "minimax-music-playlist",
        "model-benchmark",
        "nlm-to-wiki",
        "research",
        "search-fleet",
        "tp",
        "web",
        "why"
      ],
      "plan-writer": [
        "design",
        "go",
        "grok-parallel",
        "refine"
      ],
      "preflight": [
        "design",
        "tp"
      ],
      "grok-verify": [
        "go",
        "grok-parallel",
        "refactor",
        "skill-dev",
        "tp"
      ],
      "grok-route": [
        "go",
        "grok-parallel",
        "grok-verify"
      ],
      "grok-parallel": [
        "go",
        "notice"
      ],
      "grok-discovery": [
        "go",
        "grok-parallel"
      ],
      "grok-safe-git": [
        "go",
        "grok-parallel",
        "grok-verify"
      ],
      "recover": [
        "config-audit",
        "main",
        "maintain",
        "skill-prune",
        "workspace-health"
      ],
      "codex": [
        "check",
        "mmx",
        "nlm-to-wiki",
        "reason",
        "resume-codex",
        "review",
        "tp",
        "ut",
        "why",
        "workspace-health"
      ],
      "model-benchmark": [
        "model-discover"
      ],
      "wargame": [
        "plan-writer",
        "red-team"
      ],
      "create-skill": [
        "skill-dev"
      ],
      "search-fleet": [
        "web"
      ],
      "crawl4ai": [
        "crawl",
        "www"
      ],
      "help": [
        "nlm-to-wiki"
      ],
      "tasks": [
        "go",
        "team"
      ]
    },
    "wiki_referencers": {
      "parallel-subagent-wait-all-gate": [
        "aar",
        "red-team",
        "www"
      ],
      "operator-collaboration-style-and-leverage": [
        "aar",
        "dream"
      ],
      "user-modeling-for-agentic-clis": [
        "aar",
        "notice"
      ],
      "friction-detection-operator-pushback-as-trigger": [
        "aar"
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
      "prompting-patterns-for-ai-agent-control": [
        "close",
        "create-skill",
        "go",
        "prompt-patterns"
      ],
      "wikilinks": [
        "crawl",
        "crawl4ai",
        "nlm-to-wiki",
        "wiki",
        "www"
      ],
      "page": [
        "crawl",
        "crawl4ai"
      ],
      "adr-0009-extend-unverified-stance": [
        "design"
      ],
      "raising-coding-best-practices-in-ai-agents": [
        "design"
      ],
      "exemption-logic-as-conflict-signal": [
        "design"
      ],
      "consistency-drift-as-waste-source-in-iterative-refinement": [
        "design"
      ],
      "llm-synthesis-quality-and-speed-techniques": [
        "design"
      ],
      "llm-dreaming-memory-consolidation": [
        "dream"
      ],
      "self-improving-agent-systems-techniques-and-workspace-gaps": [
        "dream"
      ],
      "multi-terminal-git-coordination-primitives": [
        "grok-safe-git"
      ],
      "fleet-maintenance-skill-design": [
        "maintain"
      ],
      "model-fleet-provider-pools": [
        "model-benchmark"
      ],
      "model-pool-not-chain": [
        "model-benchmark",
        "tp"
      ],
      "mechanisms-for-thought-partner-behavior": [
        "notice"
      ],
      "proactive-ai-volunteering-mechanisms": [
        "notice"
      ],
      "wiki-concept": [
        "notice"
      ],
      "conversation-distillation-review-packet-export": [
        "packet"
      ],
      "agents-md-construction-best-practices": [
        "packet"
      ],
      "maker-checker-required-for-enforcement-work": [
        "plan-writer"
      ],
      "verification-before-completion-principle": [
        "refactor"
      ],
      "trust-escalation-ladder-autonomous-agent-work": [
        "refine"
      ],
      "task-refinement-interview-detection-template-patterns": [
        "refine"
      ],
      "workflow-definition-over-agent-capability": [
        "refine"
      ],
      "designing-harnesses-that-make-good-behavior-the-path-of-least-resistance": [
        "refine"
      ],
      "skill-techniques-index": [
        "skill-dev"
      ],
      "skill-management-in-agentic-systems-research-survey": [
        "skill-dev"
      ],
      "skill-development-portfolio": [
        "skill-dev"
      ],
      "model-fit-and-post-hoc-behavioral-detection": [
        "tp"
      ],
      "analyst-exhibits-pattern-being-analyzed": [
        "tp"
      ],
      "model-tool-calling-capability-matrix": [
        "tp"
      ],
      "model-pool-selection-policy-speed-quota-diversity": [
        "check",
        "tp"
      ],
      "markdown-mermaid-rendering-agentic-clis-windows-11": [
        "tp"
      ],
      "web-search-tool-routing": [
        "web"
      ],
      "search-tool-landscape-2026": [
        "web"
      ],
      "web-research-state-2026": [
        "web"
      ],
      "optimal-multi-backend-search-strategy": [
        "web"
      ],
      "compaction-inherited-diagnosis-unverified-propagation": [
        "why"
      ],
      "reactive-pattern-matching-and-closure-pressure": [
        "why",
        "why-old"
      ],
      "multidimensional-root-cause-analysis-ai-agent-failures": [
        "why",
        "why-old"
      ],
      "problem-first-systems-decomposition": [
        "why",
        "why-old"
      ],
      "premature-closure-narrative-sufficiency-external-approaches": [
        "why-old"
      ],
      "plausible-narratives-substitute-for-verification": [
        "why-old"
      ],
      "fabricated-causal-chain-receipt-required": [
        "why-old"
      ],
      "synchronous-review-direct-write-pattern": [
        "wiki"
      ],
      "inline-conditional-over-dispatch-for-skill-design": [
        "wiki"
      ],
      "skill-catalog": [
        "wiki",
        "www"
      ],
      "concurrent-cdp-auth-contention": [
        "nlm-to-wiki",
        "www"
      ],
      "invariants-beat-environment-comfort": [
        "www"
      ],
      "notebooklm-cli-operational-gotchas": [
        "nlm-bulk-ingest",
        "nlm-to-wiki",
        "recover",
        "www"
      ],
      "llm-instruction-non-compliance-activation-gap-2026": [
        "config-audit",
        "skill-prune"
      ],
      "structural-enforcement-for-skipped-rules-grok-build-2026": [
        "config-audit"
      ],
      "notebooklm-source-limits-free-vs-paid": [
        "nlm-bulk-ingest",
        "nlm-to-wiki"
      ],
      "semantic-clustering-bounded-size": [
        "nlm-bulk-ingest"
      ],
      "video-to-wiki-pipeline-transcript-extraction-multimodal": [
        "nlm-to-wiki"
      ],
      "nlm-to-wiki-optimization-opportunities": [
        "nlm-to-wiki"
      ],
      "nlm-bulk-ingest": [
        "nlm-to-wiki"
      ],
      "nlm-abc12345-concept-two": [
        "nlm-to-wiki"
      ],
      "nlm-abc12345-concept-one": [
        "nlm-to-wiki"
      ]
    },
    "capability_providers": {
      "opportunity-landscape": [
        "aar"
      ],
      "after-action-review": [
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
      "gate-resolution": [
        "close"
      ],
      "session-close-accounting": [
        "close"
      ],
      "openai-reasoning": [
        "codex"
      ],
      "web-ingestion": [
        "crawl4ai"
      ],
      "skill-scaffolding": [
        "create-skill"
      ],
      "subagent-dispatch": [
        "check",
        "debrief",
        "grok-parallel",
        "review",
        "tp",
        "www"
      ],
      "session-retrospective": [
        "debrief"
      ],
      "design-doc-production": [
        "design"
      ],
      "offline-memory-consolidation": [
        "dream"
      ],
      "engineering-orchestration": [
        "go"
      ],
      "discovery-dispatch": [
        "go"
      ],
      "verify-dispatch": [
        "go"
      ],
      "safe-git-preflight-dispatch": [
        "go"
      ],
      "parallel-implement-dispatch": [
        "go"
      ],
      "source-authority-discovery": [
        "grok-discovery"
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
      "mid-conversation-observation-surfacing": [
        "notice"
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
      "capability-routed-search": [
        "search-fleet"
      ],
      "rrf-aggregation": [
        "search-fleet"
      ],
      "skill-improvement": [
        "skill-dev"
      ],
      "skill-measurement": [
        "skill-dev"
      ],
      "persistent-task-store": [
        "tasks"
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
      "root-cause-analysis": [
        "why"
      ],
      "pattern-library-query": [
        "why"
      ],
      "capability-wiki-query": [
        "wiki"
      ],
      "capability-wiki-write": [
        "wiki"
      ],
      "wiki-web-wiki-research": [
        "www"
      ],
      "session-verification": [
        "check"
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
