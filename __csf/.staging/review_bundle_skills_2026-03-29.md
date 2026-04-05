# Review Bundle: P:/.claude/skills

**Generated:** 2026-03-29
**Scope:** `P:/.claude/skills/`
**File Count:** 15,137 files
**SKILL.md Files:** 206
**Top-level Entries:** 203 (164 directories + 13 symlinks + 9 files + 17 special)
**Execution Mode:** 4-agents (15,137 files >> 50 threshold)

---

## 1. PROJECT CONTEXT

### Domain & Purpose

The `P:/.claude/skills/` directory is the **master skill registry** for the user's Claude Code installation — a collection of 200+ slash-command skills covering AI model routing, code quality, debugging, orchestration, knowledge management, documentation, and developer workflow automation. Skills are the primary unit of reusable CLI-based automation, each registered via YAML-frontmattered `SKILL.md` files. The system forms the behavioral backbone of the user's solo-dev cognitive workspace.

### Scale Metrics

| Metric | Value |
|--------|-------|
| Total Files | 15,137 |
| Skill Directories | ~164 |
| SKILL.md Files | 206 |
| Top-level Entries | 203 |
| Symlinks | 13 |
| Major Categories | 10+ (AI/Provider, Hook, Code/Review, Execution, Data/Knowledge, Git/VCS, Session/State, Dev/Authoring, Debug, Docs, Utility) |
| Change Frequency | Continuous (active development) |

### Environment

- **OS:** Windows 11 Pro 10.0.26200
- **Shell:** bash (Unix syntax on Windows)
- **Primary Language:** Python 3.x
- **Framework:** Claude Code skill system (SKILL.md YAML frontmatter)
- **Key Dependencies:** litellm, ruff, mypy, pytest, AI Distiller (aid.exe), radon, Graphviz
- **State Storage:** SQLite (timeline.db, cks.db), JSON files, session archives
- **External Services:** Chutes.ai, OpenRouter, NVIDIA NIM, Groq, Mistral, Gemini, Perplexity, NotebookLM

---

## 2. ARCHITECTURE OVERVIEW

```
P:/.claude/skills/
├── Core Registry Files
│   ├── SKILL_SCHEMA.md          # Frontmatter schema definition
│   ├── SKILL_TEMPLATE.md        # Skill creation template
│   ├── SQA_INVENTORY.md         # Quality audit inventory (~150 skills + ~40 agents)
│   ├── INTEGRATION_VERIFICATION_README.md  # Integration gap fix process
│   ├── context_keywords.json     # Context routing keywords
│   └── architecture-versions-reference.md  # v1/v2/v3 arch advisor ref
│
├── ai-* (AI Provider Skills) [~10 skills]
│   ├── ai-api/                  # Multi-provider LLM (5 modes: chill/mid/chad/adaptive/route)
│   ├── ai-apiv2/                # OpenAI SDK unified: Chutes, OpenRouter, NVIDIA, Gemini, z.ai
│   ├── ai-chutes/               # Chutes.ai 100+ models
│   ├── ai-cli/                  # Parallel multi-LLM CLI (qwen/gemini/codex/vibe/opencode/glm)
│   ├── ai-groq/                 # Groq ultra-fast inference
│   ├── ai-mistral/              # Mistral AI API
│   ├── ai-models/               # Model discovery/research/leaderboard
│   ├── ai-nvidia/               # NVIDIA NIM 200+ models
│   ├── ai-openrouter/           # OpenRouter 300+ models
│   └── perplexity-web-mcp/      # Perplexity web search + AI (pplx_* MCP tools)
│
├── hook-* (Hook Management Skills) [4 skills]
│   ├── hook-audit/              # Compliance monitoring dashboard (blocks/assumptions/health)
│   ├── hook-inventory/          # Hook classification audit (dead/active/router/utility)
│   ├── hook-obs/                # SQLite observability (health/blocks/dist/waterfall/regression)
│   └── hooks-edit/              # Temporary hook suspension for editing
│
├── code-* / review / quality (Code & Quality Skills) [~15 skills]
│   ├── code/                    # 9-phase feature dev workflow v2.26 (Idea to PR)
│   ├── code-review/            # Multi-agent parallel review (4 specialist agents)
│   ├── code-reviewer-business-logic/  # Correctness review + mental execution
│   ├── code-typescript/        # TS standards (DEPRECATED -> /analyze)
│   ├── code-flow-visualizer/    # Mermaid flowchart generation
│   ├── code-analyzer-eval0/    # AI Distiller code analysis
│   ├── tdd/                    # TDD v2.25 with parallel subagent delegation
│   ├── sqa/                    # 7-layer unified quality model (L1-L7 + META)
│   ├── verify/                 # 4-tier verification (checklist/component/integration/e2e)
│   ├── trace/                  # Manual trace-through verification
│   ├── meta-review/            # Cross-file meta-review (security/performance/quality)
│   ├── harden/                 # Add guards + logging to functions
│   ├── spec-compliance/        # Spec-following enforcement
│   ├── validate-safety-patterns/ # Safety pattern validation
│   └── validate_spec/          # Implementation vs spec validation
│
├── exec / orchestration / cwo (Execution Orchestration) [~8 skills]
│   ├── exec/                   # CWO15 context-aware execution
│   ├── flow/                   # Workflow orchestration (execute/plan/status/validate)
│   ├── planning/               # Plan creation v5.0.6 with adversarial review (6 agents)
│   ├── orchestrator/           # Master routing across 192+ skills
│   ├── cwo/                   # 16-step unified orchestration (16 steps across 5 phases)
│   └── cwo-orchestrator/      # Terminal A monitor for CWO parallel coordination
│
├── data-* / checkpoint-* / restore (Data & Recovery) [~10 skills]
│   ├── data-processor/         # Data transformation (JSON/YAML/CSV/XML)
│   ├── data-processor-v2/      # Self-correcting data processing (mandatory validation)
│   ├── data-safety-vcs/        # VCS safety (anti-bleed gate, explicit staging only)
│   ├── checkpoint-delete/       # Move checkpoint to ~/.claude/trash/
│   ├── checkpoint-diff/         # Compare two checkpoints
│   ├── checkpoint-list/         # List/cleanup/validate checkpoints
│   ├── checkpoint-restore/      # Restore from trash recovery
│   ├── clear_restore/          # Remove RESTORE_CONTEXT.md
│   └── restore/               # Restore task context from CKS after compaction
│
├── cks-* / knowledge / memory (Knowledge System) [~8 skills]
│   ├── cks/                   # Constitutional Knowledge System (FAISS vector search)
│   ├── cks-usage/             # Enforces DirectCKSIngestion API (no file I/O bypass)
│   ├── memory-integration/     # CKS + MemoryCacheManager coordination
│   ├── context-status/         # Context usage statistics from compaction patterns
│   ├── constitutional-patterns/ # 7 constitutional amendments (98.7% compliance)
│   ├── constraints/            # Display active project constraints from CLAUDE.md
│   ├── evidence-applicability/  # Verify evidence applies to temporal/scope/authority context
│   └── evidence-tiers/         # Tier 1-4 confidence ceilings
│
├── git-* / gto / github-ready (Version & Analysis) [~6 skills]
│   ├── git/                   # Git sync v4.2 with health check + auto-fix + worktree mgmt
│   ├── git-conventional-commits/ # Conventional commit format validation
│   ├── github-ready/           # GitHub publication v5.13 (10-phase scaffold + badges + CI/CD)
│   ├── gto/                   # Gap/Task/Opportunity analysis v3.4 (self-verifying)
│   ├── gitingest/             # Clone/slice/upload GitHub repos to NotebookLM
│   └── gitready/              # [symlink to packages/gitready]
│
├── session / task / timeline / state (Session Management) [~10 skills]
│   ├── session/               # Logical work sessions across terminals + compaction
│   ├── session_data/          # [SKILL.md not found]
│   ├── timeline/              # Tool usage timeline with SQLite at ~/.claude/timeline.db
│   ├── task/                 # Task orchestration (create/list/search/claim/done)
│   ├── task-unresolved/      # Detect unresolved items from chat history
│   ├── update_state/         # Create checkpoint before /clear
│   ├── multi-instance-coherence/ # Coherence across multiple AI instances
│   └── clear-notifications/   # Clear statusline notifications
│
├── skill-ship / doc-to-skill / init (Authoring & Ship) [~8 skills]
│   ├── skill-ship/           # Skill creation orchestrator v1.9 (5 phases + optimization)
│   ├── skill-ship-workspace/  # [SKILL.md not found at expected path]
│   ├── doc-to-skill/         # Convert docs/websites/PDFs to Claude Skills
│   ├── artifact-add/         # Track pending artifact updates (PRD/ARD/CHANGELOG)
│   ├── artifact-audit/        # Show pending artifacts by severity
│   ├── artifact-done/         # Mark artifact complete (mtime verification)
│   ├── sharing-skills/        # Upstream skill publishing via GitHub PR workflow
│   └── init/                 # Create CLAUDE.md at module root
│
├── diagnose / critique / reflect / debugRCA (Debug & Learning) [~10 skills]
│   ├── diagnose/             # Structured diagnostic protocol (3+ hypotheses, sequential testing)
│   ├── catch-22-detection/   # Detect catch-22 blocking situations
│   ├── critique/             # Adaptive adversarial critique v2.0 (10 specialist agents)
│   ├── reflect/             # Session transcript analysis + skill improvement (beta)
│   ├── track/               # Track WIP across terminals (terminal-scoped isolation)
│   ├── debugRCA/            # [symlink to packages/rca]
│   ├── catch-22-detection/   # Respond to recursive failure loops
│   └── skeptical/            # [SKILL.md not found]
│
├── docs / docs-validate / why / arch (Documentation & Architecture) [~15 skills]
│   ├── docs/                # Unified document system with locality awareness
│   ├── docs-validate/       # Documentation quality validation (circular refs, conflicts)
│   ├── why/                # Decision archaeology (causal chain, not chronological)
│   ├── arch/               # Adaptive architecture advisor v4.6 (template-based routing)
│   ├── p/                 # Code maturation pipeline v2.5 (P0-P6 phases)
│   ├── sp/                # Alias for /scratchpad (Sapling lock-free)
│   ├── t/                 # Context-aware testing v2.2 (smart/discovery/exec/bisect)
│   ├── r/                # Deterministic remember/refine with GoT+ToT
│   ├── q/                # Strategic quality check (6-phase pipeline)
│   ├── s/                # Exploratory strategy v2.8 (multi-persona brainstorming)
│   └── mermaid-diagrams/   # Mermaid diagram creation (10 types)
│
├── nlm-* / notebooklm-* / av (NotebookLM & Analysis Visualization) [~6 skills]
│   ├── nlm-skill/          # NotebookLM CLI expert (nlm CLI via Bash, MCP reference)
│   ├── notebooklm/          # Thin wrapper to nlm-skill + notebooklm-expert
│   ├── notebooklm-expert/  # ACG framework (4-step: Source/Config/ACG/Studio)
│   ├── av/                # Auto-generate hook files from skill analysis
│   └── aid/               # AI-Distiller wrapper (refactor/arch/security/perf/bugs/docs)
│
├── utility-* / misc (Utility Skills) [~30 skills]
│   ├── bgkill/            # Kill zombie Claude Code processes
│   ├── cfg/               # Control flow graph visualization (AST-based)
│   ├── compose-npm-pip/   # Natural language -> production code (npm/pip)
│   ├── daemon/            # Semantic daemon control (CHS + CKS via named pipe)
│   ├── disler-start/      # Start disler observability stack (Bun server+client)
│   ├── disler-stop/       # Stop disler observability services
│   ├── health-monitor/    # System health monitoring (memory/hook validation)
│   ├── optimize-claude-md/ # Evidence-based CLAUDE.md optimizer (transcript analysis)
│   ├── profile/           # Performance baseline comparison
│   ├── serena/            # Semantic code analysis (AST superior to grep)
│   ├── prd/              # Import PRD as TaskMaster tasks
│   ├── prrp/             # Production-ready code review prompt
│   ├── push/             # Git push with retry (5 attempts, exponential backoff)
│   ├── ocpa/             # Optimal completion path analysis
│   ├── quadlet/          # Atomic quadlet operations with rollback
│   ├── cco/              # Concurrent agent orchestrator
│   ├── cb/              # CereBrum governance brain
│   ├── acef/            # Agentic Command Engineering Framework
│   ├── adf/             # Structural change justification evaluator
│   ├── subagent-driven-development/ # Subagent dispatch with two-stage review
│   ├── subagent-first/   # Claude Code automatic subagent routing table
│   ├── synergy/          # Cross-file refactoring opportunity detection
│   ├── system-internals-verification/ # Mandatory verification protocol
│   ├── telemetry/        # System event recording to SQLite
│   ├── truth/            # Truth verification with adversarial mode
│   ├── truth-av/         # Auto-verify all statements as hypotheses
│   ├── uci/              # Unified code inspection (3-11 agents based on mode)
│   ├── usm/              # Master coordinator across multiple AI platforms
│   ├── write-file/       # Safe file writing when Edit/Write tools fail
│   ├── ytftss/           # YouTube full-text search CLI
│   └── [many more...]
│
└── [Symlinks to packages/]
    ├── intelligence-stream-analyze/  -> packages/intelligence-stream/
    ├── intelligence-stream-ingest/   -> packages/intelligence-stream/
    ├── research/                    -> [external]
    ├── search/                      -> [external]
    ├── gitbatch/                   -> packages/gitbatch/
    ├── gitready/                   -> packages/gitready/
    ├── handoff/                    -> packages/handoff/
    └── reflect-system/            -> packages/reflect-system/
```

---

## 3. EXECUTION AND DATA FLOW

### Skill Invocation Model

Skills are invoked via slash commands (`/skill-name`) and are registered through YAML frontmatter in each `SKILL.md`. The orchestrator (`orchestrator/`) routes 192+ skills via:
- **Direct import** for 3 core orchestrator skills
- **Skill() tool** for 189 CLI-based skills
- **SuggestFieldParser** reads all SKILL.md files and extracts `suggest` relationships for intelligent routing

### State Persistence

| Store | Location | Format | Purpose |
|-------|----------|--------|---------|
| Session Manager | `.claude/state/session_manager/` | JSON | Cross-terminal session state |
| Task Tracker | `.claude/state/task_tracker/` | JSON | Task list per terminal |
| Timeline | `~/.claude/timeline.db` | SQLite | Tool usage events |
| CKS DB | `.cks/storage/cks.db` | SQLite | FAISS vector knowledge |
| Semantic Daemon | `\\.\pipe\csf_nip_semantic` | Named Pipe | CHS + CKS search |
| Health baselines | `.claude/state/profile_baselines.json` | JSON | Performance comparison |
| Workflow State | `.claude/session_data/workflow_state.json` | JSON | Orchestration state |

### Key Execution Flows

**Feature Development (code skill):**
```
REQUIREMENTS → PRE-FLIGHT → EXPLORE (AID) → PLAN (adversarial) → TDD → TEST → AUDIT → TRACE → DONE
```

**Quality Verification (sqa skill):**
```
L1 SYNTACTIC (ruff/mypy) → L2 SEMANTIC (verify/diagnose) → L3 STRUCTURAL → L4 REQUIREMENTS → L5 SECURITY → L6 PERFORMANCE → L7 OPERATIONAL → META
```

**Planning (planning skill):**
```
draft_plan → verify (auto_verify) → auto_fix → adversarial_review (6 agents) → synthesize → present → cleanup
```

---

## 4. COMPONENT INVENTORY

### Core Registry Files

| File | Purpose | Key Points |
|------|---------|------------|
| `SKILL_SCHEMA.md` | Frontmatter schema | `name`, `description`, `triggers`, `aliases`, `suggest`, `execution.*`, `do_not`, `output_template` |
| `SKILL_TEMPLATE.md` | Skill creation template | EXECUTE (immediate), REFERENCE (collapsed), YAML frontmatter, slash + phrase triggers |
| `SQA_INVENTORY.md` | Quality audit inventory | ~20 skills (C:), ~150 skills (P:), ~40+ agents; upload status tracking |
| `INTEGRATION_VERIFICATION_README.md` | Integration gap fix | Implement → verify → document (docs-last policy); IntegrationVerifier hook auto-runs on SKILL.md edits |
| `context_keywords.json` | Context routing | Topics + skill_patterns for routing |
| `architecture-versions-reference.md` | Arch advisor versions | v1 (always 13 artifacts) vs v2/v3 (3-13 adaptive + complexity detection) |

### AI Provider Skills

| Skill | Base URL / Provider | Entry Point | Models |
|-------|---------------------|-------------|--------|
| `ai-api/` | Multi-provider | `python ai_api.py --mode` | Tier 1/2/3 curation |
| `ai-apiv2/` | OpenAI SDK compatible | `python -m .claude.skills.ai-apiv2.scripts.cli health` | Chutes/OpenRouter/NVIDIA/Gemini/z.ai |
| `ai-chutes/` | `https://llm.chutes.ai/v1` | `python -m .claude.skills.ai-chutes.scripts.cli health` | 100+ models, Kimi K2.5 (256K), MiniMax M2.1 |
| `ai-cli/` | CLI parallel | `python ask_cli.py` | qwen/gemini/codex/vibe/opencode/glm-4.7-flash |
| `ai-groq/` | `https://api.groq.com/openai/v1` | `python -m .claude.skills.ai-groq.scripts.cli health` | Llama 3.3, Mixtral 8x7B, Gemma 2, DeepSeek R1 |
| `ai-mistral/` | `https://api.mistral.ai/v1` | `python -m .claude.skills.ai-mistral.scripts.cli health` | Mistral Large, Codestral |
| `ai-models/` | Unified discovery | `cd P:/__csf && python src/commands/llm_models.py` | discover/research/evaluate/leaderboard/compare |
| `ai-nvidia/` | `https://integrate.api.nvidia.com/v1` | `python -m .claude.skills.ai-nvidia.scripts.cli health` | 200+ models, Nemotron-70B, Llama-3.1-405B |
| `ai-openrouter/` | `https://openrouter.ai/api/v1` | Health via reference docs | 300+ models |
| `perplexity-web-mcp/` | Perplexity API | `pwm ask`, `pwm research`, `pwm login` | Sonar/quick (FREE), Pro, Deep Research |

### Hook Management Skills

| Skill | Entry Point | Key Commands |
|-------|-------------|--------------|
| `hook-audit/` | `python hook_audit_dashboard.py` | `blocks`, `assumptions`, `attribution`, `health`, `escalation`, `replay`, `reasoning`, `friction`, `speculation` |
| `hook-inventory/` | `python hook_inventory.py` | `--dead`, `--tree`, `--json`, `--markdown` |
| `hook-obs/` | `cd P:/__csf && python src/features/commands/observability.py` | `--health`, `--blocks`, `--dist`, `--waterfall`, `--regression`, `--heatmap`, `--failures`, `-p`, `--slow` |
| `hooks-edit/` | `/hooks-edit` activation | `CONSTITUTIONAL_HOOKS_BYPASS=1` |

### Code & Quality Skills

| Skill | Version | Entry Point | Key Workflow |
|-------|---------|-------------|--------------|
| `code/` | 2.26.0 | `/code` | 9-phase: REQUIREMENTS→PRE-FLIGHT→EXPLORE→PLAN→TDD→TEST→AUDIT→TRACE→DONE |
| `code-review/` | — | `/code-review` | 4 parallel specialist agents → health score calculation |
| `code-reviewer-business-logic/` | — | `/code-reviewer-business-logic` | Mental execution, 8 required output sections |
| `tdd/` | 2.25.0 | `/tdd` | RED-GREEN-REFACTOR with parallel subagent delegation |
| `sqa/` | 1.0.0 | `/sqa` | 7-layer sequential quality model |
| `verify/` | 1.0.0 | `/verify` | 4-tier: checklist→component→integration→e2e + deep-lens + adversarial |
| `trace/` | 1.0.0 | `/trace` | Manual trace-through (60-80% logic error detection) |
| `meta-review/` | — | `/meta-review` | path_traversal + import_graph + doc_consistency analyzers |
| `harden/` | — | `/harden` | Add guards + debug_log to functions |
| `validate_spec/` | 1.0.0 | `/validate-spec` | Severity: 95-100% NOMINAL, 80-94% MINOR, 50-79% MAJOR, <50% CRITICAL |

### Execution Orchestration Skills

| Skill | Version | Entry Point | Key Features |
|-------|---------|-------------|--------------|
| `exec/` | — | `/exec` | Context-aware, with/without active TSK, 16-step CWO mode |
| `flow/` | — | `/flow` | execute/plan/status/validate for YAML workflows |
| `planning/` | 5.0.6 | `/planning` | 8-step: draft→verify→auto_fix→adversarial_review→synthesize→present→cleanup |
| `orchestrator/` | — | `/orchestrate` | 192+ skill routing, SuggestFieldParser, WorkflowStateMachine |
| `cwo/` | — | `/cwo` | 16 steps across 5 phases, Ralph Loop auto-enable |
| `cwo-orchestrator/` | — | `/cwo-orchestrator` | Terminal A monitor, 30s polling, A\|\|B→C→D, E parallel |

### Knowledge & CKS Skills

| Skill | Entry Point | Purpose |
|-------|-------------|---------|
| `cks/` | `/cks` | FAISS vector search + add/session/ingest |
| `cks-usage/` | `/cks-usage` | Enforces DirectCKSIngestion API (no file I/O bypass) |
| `memory-integration/` | — | CKS + MemoryCacheManager coordination |
| `constitutional-patterns/` | — | 7 constitutional amendments, 98.7% compliance |
| `evidence-applicability/` | — | Temporal/scope/authority/identity verification |
| `evidence-tiers/` | — | Tier 1 (95%) → Tier 4 (50%) confidence ceilings |

### Git & Version Skills

| Skill | Version | Entry Point | Key Features |
|-------|---------|-------------|--------------|
| `git/` | 4.2 | `python sync.py` | Health check, auto-fix, smart conflicts, worktree management |
| `git-conventional-commits/` | 1.0.0 | `/git-conventional-commits` | Format: `type(scope): subject` |
| `github-ready/` | 5.13.0 | `/github-ready` | 10-phase scaffold, badges, CI/CD, media generation |
| `gto/` | 3.4.0 | `python gto_orchestrator.py` | Gap analysis + self-verifying assertions |
| `gitingest/` | 1.0.0 | `python scripts/gitingest_runner.py` | Clone/slice/upload GitHub to NotebookLM |

### Session Management Skills

| Skill | Entry Point | State Location |
|-------|-------------|----------------|
| `session/` | `/session` | `.claude/state/session_manager/` |
| `timeline/` | `/timeline` | `~/.claude/timeline.db` (SQLite) |
| `task/` | `/task` | `.claude/state/task_tracker/` |
| `restore/` | `/restore` | CKS at `.cks/storage/cks.db` |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Skill as Primary Unit** — Every automation is a `SKILL.md`-registered slash command with YAML frontmatter
2. **Constitutional Compliance** — Hooks enforce behavioral constraints; skills like `catch-22-detection` handle edge cases
3. **Evidence-Based Verification** — `evidence-tiers/`, `verify/`, `trace/` enforce verification before claims
4. **Parallel Subagent Orchestration** — Quality review (`code-review/`, `critique/`, `tdd/`) spawns parallel specialist agents
5. **Self-Optimizing System** — `reflect/`, `learn/`, `optimize-claude-md/` continuously improve from experience
6. **Zero Guessing** — `system-internals-verification/` requires citing file:line for every claim

### Technology Constraints

- **Windows 11** primary platform (bash shell, Unix syntax)
- **Python 3.x** as primary language for all skill implementations
- **SQLite** for persistent state (timeline, CKS, telemetry)
- **Named Pipe** (`\\.\pipe\csf_nip_semantic`) for semantic daemon IPC
- **Claude Code skill system** as the invocation framework
- **No `git add .`** — Explicit path staging only (enforced by `data-safety-vcs/`)

### Performance SLAs

| System | Metric | Threshold |
|--------|--------|-----------|
| Hook observability | Block rate | < 5% expected |
| Health monitor | Memory | <= 500 MB healthy, > 1000 MB critical |
| Planning adversarial | Review completion | 6 agents in parallel |
| CKS search | Vector query | FAISS-backed semantic search |

### Things That Must NOT Change

1. **Explicit path staging** for git — `data-safety-vcs/` anti-bleed gate blocks wildcard staging
2. **DirectCKSIngestion API** for knowledge — `cks-usage/` enforces no file I/O bypass
3. **Evidence citation format** — `file:line` format required by `system-internals-verification/`
4. **Tiered confidence ceilings** — `evidence-tiers/` prevents speculation above Tier ceiling
5. **RED-GREEN-REFACTOR boundary** — TDD phases must be separate subagent tasks

---

## 6. KNOWN ISSUES

### Confirmed Issues

| Issue | Impact | Current Workaround |
|-------|--------|-------------------|
| `session_data/SKILL.md` not found | Missing skill documentation | No workaround — skill directory exists but has no SKILL.md |
| `skill-ship-workspace/` SKILL.md not found | Cannot invoke skill | Use `skill-ship/` directly |
| `cognitive-stack/`, `cognitive-stack-production/` | Superseded by cognitive_enhancers hook | Use hook-based auto-activation instead |
| `code-typescript/` deprecated | Standards outdated | Use `/analyze <path> --mix quality` instead |
| `skeptical/` SKILL.md not found | Cannot invoke skill | Use `critique/` as alternative |
| `debugRCA/` now `packages/rca/` | Old path deprecated | Use `packages/rca/` (symlink in place) |
| `reflect-system/` is symlink to `packages/reflect-system/` | Active development at package location | Edit in `packages/reflect-system/` |
| `research/` and `search/` symlinks point to external | May not resolve correctly | Verify symlink targets |
| `ai-cli/` --route flag broken | Routing doesn't work | Use explicit `--qwen-only` etc. flags |

### Observed Duplicates / Overlaps

| Duplicate | Target | Notes |
|-----------|--------|-------|
| `sqa-orchestrator/` | `sqa/` | Identical documentation, same trigger |
| `sp/` | `scratchpad/` | Alias relationship |
| `query_alias/` | `/research --mode knowledge` | Backward compatibility alias |

---

## 7. INTEGRATION POINTS

### Skill-to-Skill Handoffs

| From | To | Mechanism |
|------|----|-----------|
| `planning/` | `code/` | Plan output → tasks.json → /code execution |
| `planning/` | `cwo/` | Phase assignments in ORCHESTRATION.md |
| `gto/` | `tdd/` | Gap-to-skill mapping: test_gap → /tdd |
| `gto/` | `doc/` | Gap-to-skill mapping: doc_gap → /doc |
| `q/` | `p/` | Handoff via `P:/__csf/.handoffs/q_to_p_handoff.json` |
| `reflect/` | `cks/` | Learning extraction → CKS ingestion |
| `checkpoint-restore/` | `restore/` | Both restore session context from different sources |

### External Service Integrations

| Service | Skills | Integration Method |
|---------|--------|-------------------|
| NotebookLM | `nlm-skill/`, `notebooklm/`, `notebooklm-expert/`, `gitingest/` | `nlm` CLI + MCP tools |
| Chutes.ai | `ai-chutes/`, `ai-apiv2/` | OpenAI-compatible API |
| OpenRouter | `ai-openrouter/`, `ai-apiv2/` | OpenAI-compatible API |
| NVIDIA NIM | `ai-nvidia/`, `ai-apiv2/` | OpenAI-compatible API |
| GitHub | `github-ready/`, `gitingest/` | `gh` CLI + git |
| Perplexity | `perplexity-web-mcp/` | MCP tools + `pwm` CLI |

### Hook Integration Points

| Hook | Skills Affected |
|------|-----------------|
| `PreToolUse_anti_bleed_gate.py` | All git operations (blocks `git add .`) |
| `IntegrationVerifier` | All skills with `suggest:` fields (bidirectional verification) |
| `cognitive_enhancers` | Supersedes `cognitive-stack/` skill |
| `PostToolUse_checkpoint_timeline.py` | `timeline/` skill (populates SQLite) |
| `PostToolUse_task_tracker.py` | `task/` skill |

### Data Exchange Contracts

| Contract | Format | Location |
|----------|--------|----------|
| Skill frontmatter | YAML + Markdown | `SKILL.md` |
| Session checkpoints | JSON | `.claude/checkpoints/` |
| Evidence artifacts | JSONL / Markdown | `.evidence/` |
| Skill coverage log | JSONL | `.evidence/skill_coverage/{target}.jsonl` |
| GTO assertions | YAML | `gto/evals/gto-assertions.py` |
| Result envelope | JSON | `.claude/skills/shared/result-envelope.md` |

---

## 8. APPENDIX: SKILL DIRECTORY QUICK REFERENCE

### By Category

| Category | Skills |
|----------|--------|
| **AI/Provider** | ai-api, ai-apiv2, ai-chutes, ai-cli, ai-groq, ai-mistral, ai-models, ai-nvidia, ai-openrouter, perplexity-web-mcp |
| **Hook Management** | hook-audit, hook-inventory, hook-obs, hooks-edit, main-hooks |
| **Code/Quality** | code, code-review, code-reviewer-business-logic, code-typescript (deprecated), code-flow-visualizer, code-analyzer-eval0, tdd, sqa, verify, trace, meta-review, harden, spec-compliance, validate-safety-patterns, validate_spec |
| **Execution/Orchestration** | exec, flow, planning, orchestrator, cwo, cwo-orchestrator |
| **Data/Storage** | data-processor, data-processor-v2, data-safety-vcs, checkpoint-delete, checkpoint-diff, checkpoint-list, checkpoint-restore, clear_restore, restore |
| **Knowledge/CKS** | cks, cks-usage, memory-integration, context-status, constitutional-patterns, constraints, evidence-applicability, evidence-tiers |
| **Git/Version** | git, git-conventional-commits, github-ready, gto, gitingest |
| **Session/State** | session (session_data SKILL.md missing), timeline, task, task-unresolved, update_state, multi-instance-coherence, clear-notifications |
| **Dev/Authoring** | skill-ship (skill-ship-workspace SKILL.md missing), doc-to-skill, artifact-add, artifact-audit, artifact-done, sharing-skills, init |
| **Debug/Learning** | diagnose, catch-22-detection, critique, reflect, track |
| **Docs/Arch** | docs, docs-validate, why, arch, p, sp, t, r, q, s, mermaid-diagrams |
| **NLM/NotebookLM** | nlm-skill, notebooklm, notebooklm-expert, gitingest, av, aid |
| **Utility** | bgkill, cfg, compose-npm-pip, daemon, disler-start, disler-stop, health-monitor, optimize-claude-md, profile, serena |

### By Status

| Status | Skills |
|--------|--------|
| **Deprecated** | code-typescript (use /analyze), cognitive-stack/cognitive-stack-production (use hook) |
| **Beta** | reflect |
| **Missing SKILL.md** | session_data/, skill-ship-workspace/, skeptical/ |
| **Symlinks (active at package)** | debugRCA/ → packages/rca/, intelligence-stream-analyze/ → packages/intelligence-stream/, reflect-system/ → packages/reflect-system/, gitbatch/ → packages/gitbatch/, gitready/ → packages/gitready/, handoff/ → packages/handoff/ |
| **Aliases** | sqa-orchestrator → sqa/, sp → scratchpad/, query_alias → /research |

### Entry Points Summary

| Entry Point Type | Count | Examples |
|-----------------|-------|---------|
| Slash command (`/skill`) | ~200 | `/code`, `/tdd`, `/planning`, `/verify` |
| Python module (`python -m`) | ~15 | `python -m .claude.skills.ai-groq.scripts.cli` |
| Python script (`python path.py`) | ~20 | `python hook_audit_dashboard.py`, `python sync.py` |
| Bash CLI (`nlm`, `sl`, `gh`) | ~10 | `nlm login`, `sl commit`, `gh pr create` |
| PowerShell (`pwsh`) | ~3 | Health monitoring scripts |
| Named pipe | 1 | `\\.\pipe\csf_nip_semantic` (semantic daemon) |

---

---

## 9. APPENDIX: PACKAGE-LEVEL SKILLS (P:/packages/)

Three packages in `P:/packages/` contain `SKILL.md` files and are symlinked into `P:/.claude/skills/`. These are included here for completeness.

### `P:/packages/rca/skill/SKILL.md`

| Field | Value |
|-------|-------|
| **Name** | rca |
| **Version** | 2.11.1 |
| **Category** | analysis |
| **Domain** | debugging |
| **Trigger** | `/rca` |
| **Enforcement** | strict |
| **Suggest** | `/r`, `/verify` |
| **Hook-Based** | Yes — 6 PostToolUse hooks + 1 SessionEnd hook via `rca.hook_launcher` |

**Purpose:** AI-assisted root cause analysis engine combining Python RCA library and Claude Code skill for systematic debugging.

**Critical Constraint:** Role is DIAGNOSIS, not implementation. Only implement if user explicitly says "apply the fix" or "implement this".

**Investigation Workflow (Steps -1 through 9):**

| Step | Name | Description |
|------|------|-------------|
| -1 | Surgical First Response | Grep exact strings immediately, no questions |
| 0 | Pre-Flight | Check CKS/CHS for prior knowledge |
| 0.5 | Cognitive Stack | Classify problem type, select mental models |
| 0.75 | Internet Research | Research technologies before hypothesizing |
| 1 | Falsifiable Symptom | Define what is wrong, what should happen, when it started |
| 1.4 | Learned Patterns | Check CKS for patterns from previous RCA sessions |
| 1.5 | Multi-Angle Search | Use symptom-type templates |
| 1.6 | Trace Execution | MANDATORY for hangs/timeouts |
| 1.65 | Runtime State | CONDITIONAL for silent failures |
| 1.75 | Hypothesis Generation | 3-7 hypotheses with ToT branching and scoring |
| 2 | Symbol-Level Trace | Use Serena MCP for precise flow tracing |
| 2.5 | First Divergence | Find earliest mismatch from expected behavior |
| 2.85 | Convergence Gate | Verify all 7 convergence gates pass |
| 3-9 | Principles | One variable, instrumentation, minimize, interfaces, structure, failure path, capture lesson |

**Hypothesis Scoring:** `Score = Reproducibility(0.3) × Recency(0.2) × Impact(0.5)`

**Multi-Agent Reasoning:** Factual Agent + Critical Agent + Synthesis Agent dispatched in parallel. Synthesis boosts confidence ceiling to 90%.

**Reference files:** `references/evidence-and-tiers.md`, `references/investigation-protocol.md`, `references/search-templates.md`, `references/cognitive-stack-and-tot.md`, `references/hypothesis-scoring.md`, `references/action-graph-and-triple-collection.md`, `references/verification-gates.md`, `references/output-format.md`, `references/synthesis-and-architecture-review.md`, `references/workflow-state-validation.md`

**Hooks (via rca.hook_launcher):**
- `PostToolUse_rca_init.py` — on Skill invocation
- `PostToolUse_rca_phase_tracker.py` — on Bash/Task/Read/Write/Grep/Skill/WebSearch/WebFetch/MCP tools
- `PostToolUse_rca_action_tracker.py` — on same tool set
- `PostToolUse_rca_search_validator.py` — on Grep
- `PostToolUse_rca_research_storage.py` — on WebSearch/WebFetch/MCP web-reader
- `SessionEnd_rca_cleanup.py` — on session end

---

### `P:/packages/handoff/skill/SKILL.md`

| Field | Value |
|-------|-------|
| **Name** | handoff |
| **Version** | 1.0.0 |
| **Status** | stable |
| **Category** | documentation |
| **Trigger** | `/handoff` |
| **Suggest** | `/restore`, `/session-handoff` |
| **Hook-Based** | Yes — PreCompact hook for automatic capture |

**Purpose:** Research-backed handover documentation system for seamless LLM session continuity across compacts. **Automatic capture via PreCompact hooks** — no manual CLI needed.

**Architecture:**
- Package: `handoff` at `P:/packages/handoff`
- Hooks: PreCompact handoff capture (automatic)
- Storage: `P:/.claude/state/task_tracker/`

**Critical Rule — Active Work At Handoff:**
- **Active Work At Handoff**: ONLY work done in THIS session (files modified, tools executed)
- **Current Tasks**: Pending/in-progress tasks from TaskList (may include work from previous sessions)
- When creating handover: Verify session work before adding to "Active Work"

**Quality Scoring Algorithm:**
- 30% Completion Tracking
- 25% Action-Outcome Correlation
- 20% Decision Documentation
- 15% Issue Resolution
- 10% Knowledge Contribution

**Reference files:** `references/quality-scoring.md`, `references/core-features.md`, `references/usage-patterns.md`, `references/handover-template.md`, `references/retention-policy.md`

---

### `P:/packages/reflect-system/reflect/SKILL.md`

| Field | Value |
|-------|-------|
| **Name** | reflect |
| **Version** | 1.0.0 |
| **Status** | beta |
| **Category** | learning |
| **Trigger** | `/reflect` |
| **Hook-Based** | Yes — Stop hook for automatic session-end reflection |

**Purpose:** Analyzes conversation transcripts to extract user corrections, patterns, and preferences, then proposes skill improvements. Implements "correct once, never again" learning.

**Three Modes:**
1. **Manual Reflection** — `/reflect [skill-name]` anytime
2. **Automatic Reflection** — Runs at session end via Stop hook (always-on, background)
3. **Queue Processing** — Review accumulated signals from multiple sessions

**Pre-Mortem Analysis:** Detects conversation issues (vague requirements, contradictions, missing error handling) before they become problems. Runs automatically during reflection.

**Confidence Levels:**
- **HIGH** — Explicit corrections ("Don't do X, do Y instead") → direct updates with deprecation warnings
- **MEDIUM** — Approvals and implicit learning → add to "Best Practices"
- **LOW** — Observations ("Have you considered...") → add to "Considerations"

**Workflow:** Signal Detection → Context Analysis → Skill Mapping → Implicit Pattern Detection → Pre-Mortem Analysis → Change Proposal → User Review → Application → Git Commit

**Scripts:**
- Core: `reflect.py`, `extract_signals.py`, `update_skill.py`, `present_review.py`
- Signal: `semantic_detector.py`, `workflow_assumptions.py`, `tool_error_extractor.py`
- Implicit: `implicit_patterns.py`, `semantic_validator.py`
- Cross-Skill: `learning_ledger.py` (SQLite), `scope_analyzer.py`, `promote_learning.py`, `multi_target_sync.py`, `meta_learning.py`
- Pre-Mortem: `premortem.py`
- Queue: `show_queue.py`, `accumulate_signals.py`
- CKS: `cks_schema_mapper.py`, `cks_auto_save.py`
- Automation: `hook-stop.sh/.ps1/.bat`, `toggle-on.sh`, `toggle-off.sh`, `toggle-status.sh`

**Reference files:** `references/output-template.md` (MANDATORY format), `references/signal-patterns.md`, `references/cli-options.md`, `references/cks-integration.md`, `references/meta-patterns.md`

---

*Review bundle generated by /review_bundle skill — 4-agent parallel execution for 15,137-file scope*
