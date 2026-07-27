---
title: "Skill domain map: what skills cover what functions across the workspace"
created: 2026-07-27
source: session-2026-07-27
tags: [skill-map, domains, sdlc, fleet-operations, media-pipeline, self-improvement, gap-analysis, maintenance, reference]
summary: >
  Complete mapping of all workspace skills into 13 functional domains.
  Shows which skills exist on Grok (✓), which are Claude-only (✗), and
  which were ported this session (➡). Updated 2026-07-27 after the
  maintenance skill ports and gap analysis. Use this as the canonical
  reference for "do we have a skill for X?" and "what gaps remain?"
agent: grok
host: both
cognitive_load: 2
verification: observed
sources:
  - "session-2026-07-27 gap analysis (P:\tmp\gap_analysis.py)"
  - "skill catalog (P:/.data/wiki/concepts/skill-catalog.md)"
  - "SDLC domain matrix (P:\tmp\domain_map.py)"
relations:
  - target: wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md
    type: related
  - target: wiki/concepts/notebooklm-cli-operational-gotchas.md
    type: related
  - target: wiki/concepts/video-to-wiki-pipeline-transcript-extraction-multimodal.md
    type: related
---

# Skill domain map

## How to read this

- **✓** = skill is enabled and functional on Grok Build
- **➡** = skill was ported to Grok this session (2026-07-25 to 2026-07-27)
- **✗** = skill exists in Claude-only (disabled in Grok's `[plugins].disabled`)
- **?** = skill exists at `.agents/skills/` but functional state unverified

## Domain 1 — Discovery / Planning

Identify what to build, gather context before implementation.

| Skill | G | What it does |
|---|---|---|
| `refine` | ✓ | Tighten vague tasks into implementation-ready specs |
| `plan-writer` | ✓ | Comprehensive implementation plans from specs |
| `grok-discovery` | ✓ | Evidence-backed inventory before non-trivial work |
| `www` | ✓ | Wiki-Web-Wiki compound research |
| `web` | ✓ | Multi-backend web research |
| `search-fleet` | ✓ | Capability-routed multi-backend search with RRF |
| `marketplace-bridge` | ✓ | Discover skills across marketplaces |

**Coverage: ✅ Strong (7 skills, no gaps)**

## Domain 2 — Design / Architecture

Produce architecture decisions, design docs, evaluate approaches.

| Skill | G | What it does |
|---|---|---|
| `design` | ✓ | Design-doc writer/reviewer loop |
| `decision-tree` | ✗ | SDLC decision engine (architecture, incidents, refactors) |
| `constraints` | ✗ | Show active project constraints |
| `evolve` | ✗ | Modernization workflow |
| `solo-dev-authority` | ✗ | Constitutional constraints for solo dev |

**Coverage: ⚠ Weak (1 Grok skill). Port `decision-tree` and `constraints` first.**

## Domain 3 — Implementation

Write code, refactor, modernize, analyze codebases.

| Skill | G | What it does |
|---|---|---|
| `refactor` | ✓ | Multi-file refactoring orchestration |
| `imagine` | ✓ | Image generation/editing guidance |
| `nlm-bulk-ingest` | ➡ | URL list → clustered NotebookLM notebooks |
| `notebooklm` | ✓ | NotebookLM API access |
| `code` | ✗ | Feature dev mission control (TDD engine) |
| `tldr-code` | ✗ | Token-efficient code analysis (5-layer AST/CG/CFG/DFG/PDG) |
| `tldr-overview` | ✗ | Token-efficient project overview |
| `tldr-deep` | ✗ | Full 5-layer analysis of a specific function |
| `tldr-router` | ✗ | Maps questions to the right tldr command |
| `tldr-stats` | ✗ | Token usage, costs, TLDR savings |
| `build` | ✗ | Build a new skill from scratch |

**Coverage: ⚠ Moderate. Missing `tldr-*` family (high ROI for large codebases) and `code`.**

## Domain 4 — Testing / QA

Verify correctness, enforce TDD, trace execution, diagnose failures.

| Skill | G | What it does |
|---|---|---|
| `check` | ✓ | Multi-concern session verification |
| `grok-verify` | ✓ | Evidence-first completion gate |
| `tdd` | ✗ | RED/GREEN cycle enforcement, mutation gate |
| `diagnose` | ✗ | Structured diagnostic protocol (hypothesis testing) |
| `trace` | ✗ | Manual trace-through verification |
| `verification-before-completion` | ✓ | Pre-claim verification (superpowers) |
| `systematic-debugging` | ✓ | Systematic root-cause debugging (superpowers) |
| `test-driven-development` | ✓ | TDD instructions (superpowers, lightweight) |

**Coverage: ⚠ Moderate. Missing `tdd` (enforcement, not just instructions) and `trace`.**

## Domain 5 — Review / Audit

Code review, adversarial analysis, quality assessment.

| Skill | G | What it does |
|---|---|---|
| `review` | ✓ | Code/package review with verified findings |
| `red-team` | ✓ | Adversarial review before commitment |
| `tp` | ✓ | Critical-friend thought partner |
| `wargame` | ✓ | Content discipline for hard-to-reverse plans |
| `skill-audit` | ✗ | Audit skill against quality rubric |
| `sqa` | ✗ | 11-layer sequential quality analysis |
| `epistemic-check` | ✗ | Validate Q&A against epistemic contract |

**Coverage: ✅ Strong (4 Grok skills). `skill-audit` is worth porting for `/skill-prune`.**

## Domain 6 — Deployment / Ship

Deploy readiness, runtime validation, release management.

| Skill | G | What it does |
|---|---|---|
| `ship` | ✗ | Deploy readiness + runtime snapshot |

**Coverage: ⛔ Zero Grok skills. Only domain with no coverage.**

## Domain 7 — Maintenance

System health, config auditing, skill hygiene, file recovery, git safety.

| Skill | G | What it does |
|---|---|---|
| `why` | ✓ | Evidence-tiered root cause analysis |
| `grok-safe-git` | ✓ | Concurrent-safe git preflight |
| `model-benchmark` | ✓ | Latency/quality/cost benchmarking |
| `notice` | ✓ | Mid-conversation observation surfacing |
| `skill-prune` | ➡ | Skill/wiki knowledge hygiene |
| `recover` | ➡ | File recovery via git + transcripts |
| `workspace-health` | ➡ | System health checks and validation |
| `config-audit` | ➡ | Configuration audit and optimization |
| `stale` | ✗ | Find docs out of date vs code |
| `skill-similarity` | ✗ | Find similar skills by keywords/deps |
| `snapshot` | ✗ | Session snapshot capture/restore |
| `debt` | ✗ | Lazy-closure-debt audit log viewer |

**Coverage: ✅ Strong (8 Grok skills after today's ports). 4 more identified for porting.**

## Domain 8 — Knowledge / Memory

Wiki, handoffs, lessons, consolidation, persistent state.

| Skill | G | What it does |
|---|---|---|
| `wiki` | ✓ | Persistent knowledge base |
| `handoff` | ✓ | Work handoff documents |
| `close` | ✓ | Session close-out orchestrator |
| `aar` | ✓ | Continual-improvement AAR |
| `debrief` | ✓ | Session retrospective (5 lenses) |
| `dream` | ✓ | Offline memory consolidation |
| `tasks` | ✓ | Cross-session task store |
| `crawl4ai` | ✓ | Website ingestion into wiki |
| `nlm-to-wiki` | ➡ | NotebookLM → wiki concept pages |
| `capture` | ✗ | Extract durable knowledge from changes |
| `remembering-conversations` | ✓ | Episodic memory search |

**Coverage: ✅ Strongest domain (10 Grok skills).**

## Domain 9 — Collaboration

Cross-model second opinions, parallel work, multi-agent coordination.

| Skill | G | What it does |
|---|---|---|
| `grok-parallel` | ✓ | Parallel subagent fan-out |
| `agy` | ✓ | Antigravity CLI (Gemini) second opinion |
| `codex` | ✓ | Codex CLI (OpenAI) second opinion |
| `mmx` | ✓ | MiniMax CLI second opinion + web search |

**Coverage: ✅ Covered (4 skills, no gaps).**

## Domain 10 — Meta / Process

Skill creation, routing, documentation, process improvement.

| Skill | G | What it does |
|---|---|---|
| `go` | ✓ | High-horsepower SDLC orchestrator |
| `create-skill` | ✓ | Interactive skill creation |
| `grok-route` | ✓ | Package-local instruction routing |
| `prompt-patterns` | ✓ | Structural prompting techniques reference |
| `help` | ✓ | Grok documentation help |
| `skill-write` | ✗ | Unified create-side skill tooling |

**Coverage: ✅ Covered. `skill-write` could merge into `create-skill`.**

## Domain 11 — Fleet operations

Managing the AI model fleet: routing, benchmarking, delegation, quota.

| Skill | G | What it does |
|---|---|---|
| `model-benchmark` | ✓ | Latency/quality/cost benchmarking |
| `grok-parallel` | ✓ | Parallel subagent fan-out |
| `delegation-packet-runner` | ✓ | Build bounded prompts for delegated agents |
| `cost-aware-delegation` | ✗ | Route tasks to cheapest capable model |
| `external-delegation` | ✗ | Delegate to OpenCode/Zen/llama.cpp |
| `agent-performance-analyzer` | ? | Agent skill performance analysis |
| `ai-api` | ✗ | Unified LLM API calls |
| `ai-cli` | ✗ | Parallel multi-LLM dispatch |
| `ai-models` | ✗ | Model discovery and analysis |
| `ai-probe-benchmark` | ✗ | Model benchmarking |
| `ai-probe-nim` | ✗ | Nvidia NIM probing |
| `ai-probe-openrouter` | ✗ | OpenRouter probing |
| `ai-probe-router` | ✗ | Model router probing |

**Coverage: ⚠ Moderate (3 Grok). Missing fleet routing and delegation.**

## Domain 12 — Media pipeline

Content ingestion and transformation: video, audio, images, transcripts.

| Skill | G | What it does |
|---|---|---|
| `nlm-bulk-ingest` | ➡ | URL list → clustered notebooks |
| `nlm-to-wiki` | ➡ | Notebooks → wiki concepts |
| `notebooklm` | ✓ | NotebookLM API |
| `imagine` | ✓ | Image generation/editing |
| `video-vision` | ✗ | Scene-change keyframe extraction (crv) |
| `vision-analysis` | ✗ | MiniMax M3 vision per-frame description |
| `yt-nlm` | ✗ | Batch transcript extraction |
| `yt-is` | ✗ | YouTube channel management |
| `yt-selenium` | ✗ | Selenium transcript fallback |
| `codebase-to-course` | ✗ | Codebase → interactive HTML course |
| `minimax-multimodal-toolkit` | ✗ | mmx text/image/video/speech/music |
| `minimax-music-gen` | ✗ | Music generation |
| `minimax-music-playlist` | ✗ | Music playlist management |

**Coverage: ⚠ Moderate (4 Grok). Missing the entire video/vision/yt pipeline (9 skills). nlm-to-wiki v3 needs `crv`.**

## Domain 13 — Operator self-improvement

The meta-learning loop: lessons, reasoning frameworks, knowledge mining.

| Skill | G | What it does |
|---|---|---|
| `aar` | ✓ | Evidence-grounded continual-improvement |
| `debrief` | ✓ | Session retrospective |
| `dream` | ✓ | Offline memory consolidation |
| `tp` | ✓ | Critical-friend thought partner |
| `why` | ✓ | Root cause analysis |
| `learn` | ✗ | Lesson capture with novelty detection |
| `reason` | ✗ | Unified reasoning engine |
| `genius` | ✗ | Strategic thought partner |
| `prospect` | ✗ | Mines wiki for improvements |
| `reflect` | ✗ | Structured reflection |
| `skeptic` | ✗ | AI output validation |
| `truth` | ✗ | Verify claims using evidence |
| `sequential-thinking` | ✗ | Generate/critique/improve loop |
| `tot` | ✗ | Tree-of-thoughts reasoning |
| `ut` | ✗ | Architectural gatekeeper |
| `s` | ✗ | Multi-persona strategy |

**Coverage: ✅ Function covered (5 Grok skills). Variety gap (10 Claude thinking frameworks add different lenses).**

## Summary matrix

| Domain | Grok | Claude-only | Coverage |
|---|---|---|---|
| 1. Discovery/Planning | 7 | 0 | ✅ |
| 2. Design/Architecture | 1 | 4 | ⚠ |
| 3. Implementation | 4 | 6 | ⚠ |
| 4. Testing/QA | 5 | 3 | ⚠ |
| 5. Review/Audit | 4 | 3 | ✅ |
| 6. **Deployment/Ship** | **0** | **1** | **⛔** |
| 7. Maintenance | 8 | 4 | ✅ |
| 8. Knowledge/Memory | 10 | 1 | ✅ |
| 9. Collaboration | 4 | 0 | ✅ |
| 10. Meta/Process | 5 | 1 | ✅ |
| 11. Fleet operations | 3 | 8 | ⚠ |
| 12. Media pipeline | 4 | 9 | ⚠ |
| 13. Self-improvement | 5 | 10 | ✅ (variety gap) |

**Total: 60 Grok skills, 50 Claude-only gaps across 13 domains.**

## Receipts

- **Skill counts:** derived from `P:/.data/wiki/concepts/skill-catalog.md` via `P:\tmp\gap_analysis.py` (parses catalog rows, filters by G/C enable state). Run 2026-07-27.
- **Enable states:** from `~/.grok/config.toml [plugins].disabled` (30 entries) and `~/.claude/settings.json enabledPlugins` (51 entries), parsed by `index_skills.py compute_plugin_state()`. Verified via 19-test suite at `P:/.data/wiki/scripts/test_index_skills_state.py`.
- **Domain classification:** [INFERENCE] — manual assignment based on skill descriptions and function. No automated domain detection; classifications may be debatable (e.g., `notice` could be "Review" or "Maintenance").
- **"Functional on Grok" status:** [INFERENCE] — enable state from config means the skill loads, but runtime functionality is not verified for all 60 skills. Some may reference Claude-specific tools or paths that break on Grok.

## Falsifier

This map is wrong if:
- A skill is listed under the wrong domain (classification is manual, not derived)
- A skill is missing (the gap analysis scanned the catalog, not individual directories)
- A skill marked "✓ Grok" doesn't actually work on Grok (enable-state is from config, not runtime verification)
- New domains should exist that aren't listed (e.g., "Security" could be separate from "Review/Audit")

## Auto-related

- [[llm-instruction-non-compliance-activation-gap-2026]]
- [[notebooklm-cli-operational-gotchas]]
- [[video-to-wiki-pipeline-transcript-extraction-multimodal]]
