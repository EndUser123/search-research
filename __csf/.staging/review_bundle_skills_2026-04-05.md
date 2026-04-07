# Review Bundle: Skills /sqa, /arch, /rca, /skill-ship, /sdlc

**Generated**: 2026-04-05
**Scope**: Claude Code skill ecosystem (5 skills)
**File Count**: sqa=96, arch=~30, rca=894 (packages), skill-ship=247, sdlc=1657
**Execution Mode**: 4-agents (50+ files for sdlc/rca); 2-agents (10-50 for sqa/arch/skill-ship)

---

## 1. PROJECT CONTEXT

### Bundle Metadata

| Skill | Location | Version | Files | Type |
|-------|----------|---------|-------|------|
| `/sqa` | `P:\.claude\skills\sqa\` | 1.4.0 | 96 | Quality orchestration |
| `/arch` | `P:\.claude\skills\arch\` | 4.9 | ~30 | Architecture advisory |
| `/rca` | `P:\.claude\skills\rca\` + `P:\packages\rca\` | — | 894 | Root cause analysis |
| `/skill-ship` | `P:\.claude\skills\skill-ship\` | 1.10.0 | 247 | Skill creation orchestration |
| `/sdlc` | `P:\packages\sdlc\` | — | 1657 | SDLC primitives |

### Domain & Purpose

These skills form the core quality and development infrastructure layer for Claude Code in a solo-dev Windows 11 environment:

- **`/sqa`**: Unified 8-layer sequential quality analysis (Predictive→Syntactic→Semantic→Structural→Requirements→Security→Performance→Operational→Meta-Synthesis)
- **`/arch`**: Adaptive architecture advisor with template-based routing (fast/deep/cli/python/data-pipeline/precedent)
- **`/rca`**: Root cause analysis with evidence-store and adversarial patterns
- **`/skill-ship`**: Master coordinator for skill creation and improvement workflows
- **`/sdlc`**: SDLC primitives (contract-primitives, skills, test.json) — foundation for other skills

### Scale Metrics

- **sqa**: 96 files, 8-layer pipeline, single-target analysis
- **arch**: ~30 files, 6 templates, multi-domain routing
- **rca**: 894 files (large package), evidence-based RCA with adversarial dispatch
- **skill-ship**: 247 files, 6-phase workflow, subagent coordination
- **sdlc**: 1657 files (largest), contract-primitives + skills + tests

### Your Environment

- **OS**: Windows 11 Pro 10.0.26200
- **Shell**: bash (Git Bash / WSL)
- **Primary language**: Python 3.14
- **Package managers**: pytest, ruff
- **Key paths**:
  - Skills: `P:\.claude\skills\`
  - Packages: `P:\packages\`
  - Hooks: `P:\.claude\hooks\`
  - Evidence: `C:\Users\brsth\.claude\.evidence\`

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                     SKILL ECOSYSTEM LAYERS                       │
├─────────────────────────────────────────────────────────────────┤
│  /sqa (quality orchestrator)                                     │
│    └── 8-layer sequential: Predictive→Syntactic→...→Meta         │
│                                                                  │
│  /arch (architecture advisor)                                    │
│    └── Template router: fast/deep/cli/python/data-pipeline       │
│                                                                  │
│  /rca (root cause analysis)                                     │
│    └── Evidence-store + adversarial dispatch                      │
│                                                                  │
│  /skill-ship (skill creation coordinator)                        │
│    └── 6-phase: Context→Discovery→Knowledge→Create→Validate→Dist│
│                                                                  │
│  /sdlc (SDLC primitives — base layer)                            │
│    └── contract-primitives, skills/, test.json                   │
└─────────────────────────────────────────────────────────────────┘
```

### Cross-Skill Dependencies

- `/arch` depends on `sdlc >= 0.1.0` (from frontmatter)
- `/skill-ship` orchestrates: skill-creator, skill-development, av, testing-skills, similarity, doc-to-skill, sharing-skills
- `/sqa` certifies contract integrity, resume integrity, stale-data immunity
- `/rca` uses evidence-store and adversarial agent dispatch (adversarial-critic, adversarial-compliance, etc.)

---

## 3. COMPONENT INVENTORY

### /sqa (P:\.claude\skills\sqa\)

| Component | Purpose |
|-----------|---------|
| `SKILL.md` | Entry point, 8-layer pipeline definition |
| `__lib/` | Core logic (layer implementations) |
| `scripts/` | CLI entry points |
| `tests/` | Layer-specific tests |

**Key workflow steps**: preflight_checks → layer0-7 execution → halt-on severity → evidence output

### /arch (P:\.claude\skills\arch\)

| Component | Purpose |
|-----------|---------|
| `SKILL.md` | Template router, 12 workflow steps |
| `resources/` | Template definitions (fast.md, deep.md, cli.md, python.md, etc.) |
| `architecture/` | GoT (Graph-of-Thought) integration |
| `config.py` | Configuration loading (.archconfig.json hierarchy) |

**Governance**: layer1_enforcement=true, contract boundary inventory/closure

### /rca (P:\.claude\skills\rca\ and P:\packages\rca\)

| Component | Purpose |
|-----------|---------|
| `SKILL.md` | RCA entry with debugRCA integration |
| `debugRCA/` | DebugRCA course materials |
| `evidence/` | Evidence store implementation |
| `tests/` | RCA tests |
| `__pycache__/` | Compiled Python |

**Key agents**: adversarial-critic, adversarial-compliance, adversarial-logic, adversarial-security, adversarial-failure-modes, adversarial-qa, adversarial-state-machine

### /skill-ship (P:\.claude\skills\skill-ship\)

| Component | Purpose |
|-----------|---------|
| `SKILL.md` | Master coordinator, 6-phase workflow |
| `references/` | Detailed phase instructions (workflow-phases.md, knowledge-retrieval.md, etc.) |
| `validators/` | context_size.py (300/500 line thresholds) |
| `tests/` | Phase-specific tests |
| `examples/` | WORKFLOW-EXAMPLES.md |
| `config/builtins.json` | Dynamic builtins list (loaded at runtime, not hardcoded) |

**Phase flow**: Context (0) → Discovery (1) → Knowledge Retrieval (1.5) → Creation (2) → Validation (3a/b/c) → Eval (3.5) → Optimization (4) → Distribution (5)

### /sdlc (P:\packages\sdlc\)

| Component | Purpose |
|-----------|---------|
| `contract-primitives/` | Core contract definitions |
| `skills/` | SDLC skill implementations |
| `test.json` | Test configuration |
| `CHANGELOG.md`, `BADGES.md` | Metadata |

---

## 4. DESIGN INTENT AND NON-NEGOTIABLES

### /sqa
- **Contract integrity certification**: Must verify contract boundaries before recommending changes
- **Resume integrity**: Validates that work can resume after interruption
- **Stale-data immunity**: Detects when data may be outdated
- **8-layer sequential**: Cannot skip layers; each gates the next

### /arch
- **Multi-terminal safety**: All decisions must evaluate concurrency safety
- **Template-based routing**: Queries routed by domain/complexity, not arbitrary choice
- **ADR closure consistency**: Architecture decisions must be closed with evidence
- **No Skill() calls**: Templates read and executed directly, no sub-skill invocation

### /rca
- **Evidence-based**: All claims must be backed by read evidence
- **Adversarial dispatch**: Uses 6+ adversarial agents for comprehensive analysis
- **Confidence tiers**: Tier 1 (execution) > Tier 2 (docs) > Tier 3 (static analysis) > Tier 4 (comments)

### /skill-ship
- **Phase gate enforcement**: Phase 1.5 blocks Phase 2; Phase 3a blocks 3b; 3b blocks 3c
- **Subagent freshness**: Each validation phase spawns fresh subagent, no state sharing
- **Progressive disclosure**: SKILL.md must stay <500 lines
- **Dynamic agent discovery**: Builtins loaded from JSON config, not hardcoded

### /sdlc
- **Contract primitives**: Base layer for other skills to build upon
- **Test infrastructure**: test.json defines test cases

---

## 5. KNOWN ISSUES

| Skill | Issue | Impact | Workaround |
|-------|-------|--------|------------|
| `/sqa` | Focus lens `--fix` only safe for L1/L2 | Auto-fix limited | Manual fixes for L3+ |
| `/arch` | GoT templates may have path issues on Windows | Template loading | Use forward slashes in paths |
| `/rca` | Large file count (894) slows initial scan | Performance | Use focused RCA with specific targets |
| `/skill-ship` | Phase 1.5 skip reason not always logged | Workflow gaps | Check workflow-state.json before proceeding |
| `/sdlc` | Package-level, not skill-level | May not appear in /skills list | Access via `P:\packages\sdlc\` directly |

---

## 6. INTEGRATION POINTS

### /sqa integrations
- Reads: target codebase files
- Writes: `P:\__csf\.staging\sqa_results_*.json` (terminal-isolated)
- Gates: `--halt-on` severity threshold

### /arch integrations
- Reads: `.archconfig.json` (project), `~/.archconfig.json` (user), `ARCH_DEFAULT_DOMAIN` env var
- Writes: `arch_decisions/` directory
- Templates: `resources/{template}.md`

### /rca integrations
- Reads: evidence_store, transcript files, source code
- Dispatches: adversarial agents (6+ types)
- Writes: RCA findings with confidence tiers

### /skill-ship integrations
- Invokes: skill-creator, skill-development, /similarity, /usm, /search, notebooklm, CKS
- Reads: existing skills, hooks, plugins for pattern extraction
- Writes: new SKILL.md files, evidence to `~/.claude/.evidence/`

### /sdlc integrations
- Base layer for: /arch, /rca, /skill-ship
- Provides: contract-primitives for other skills

---

## 7. SKILL-SPECIFIC INPUT/OUTPUT CONTRACTS

### /sqa I/O
| Phase | Reads | Writes |
|-------|-------|--------|
| preflight | target path | — |
| layer 0-7 | codebase files | findings per layer |
| halt-on | severity threshold | early exit if exceeded |
| --evidence | — | JSON to terminal-isolated path |

### /arch I/O
| Phase | Reads | Writes |
|-------|-------|--------|
| classify_intent | user query | intent classification |
| select_template | .archconfig.json, env vars | template name |
| execute_template | template file, source code | architecture review |
| adr_closure | existing ADRs | new ADR if needed |

### /rca I/O
| Phase | Reads | Writes |
|-------|-------|--------|
| evidence collection | source code, transcript | evidence_store |
| adversarial dispatch | — | findings from 6+ agents |
| confidence calibration | evidence tier | confidence score |

### /skill-ship I/O
| Phase | Reads | Writes |
|-------|-------|--------|
| 0-Context | recent turns, gto-state-*, workflow-state.json | — |
| 1-Discovery | user query | intent classification |
| 1.5-Knowledge | CKS, NotebookLM, memory.md, /search, /usm, list_agents.py | Knowledge Retrieval Summary |
| 2-Creation | skill-creator, skill-development | new SKILL.md |
| 3a-Spec | implementation vs plan | SPEC_PASS / SPEC_FAIL |
| 3b-Quality | YAML, triggers, context bloat | critical issues list |
| 3c-Integration | skill invocation | integration pass/fail |
| 4-Optimization | av2, output-style-extractor | hooks, formatting |
| 5-Distribution | sharing-skills | GitHub PR |

### /sdlc I/O
| Phase | Reads | Writes |
|-------|-------|--------|
| contract-primitives | base contracts | shared definitions |
| skills/ | skill definitions | skill implementations |
| test.json | test cases | test execution |

---

## 8. AGENT DISPATCH DEFINITIONS (Multi-Skill Comparison)

### /sqa — No parallel agent dispatch
Single-threaded layer execution. Each layer runs sequentially.

### /arch — No parallel agent dispatch
Template execution is sequential. GoT analysis may spawn Explore agent but not multi-agent parallel.

### /rca — Parallel adversarial dispatch (6+ agents)
| Agent | Role | What it reads |
|-------|------|---------------|
| adversarial-critic | Overall critique | source + analysis |
| adversarial-compliance | Compliance check | source + contracts |
| adversarial-logic | Logic error detection | source |
| adversarial-security | Security vulnerabilities | source |
| adversarial-failure-modes | Failure mode discovery | source + web research |
| adversarial-state-machine | State transition bugs | source |

**Dispatch**: Parallel all agents simultaneously → serial aggregation

### /skill-ship — Parallel validation dispatch (Phase 3a + 3b)
| Agent | Role | What it reads |
|-------|------|---------------|
| 3a Spec validator | Verify implementation vs plan | source + plan |
| 3b Quality validator | YAML, triggers, context bloat | source + quality gates |

**Dispatch**: Parallel (3a and 3b run simultaneously, 3a blocks 3c, 3b independent)

### /sdlc — No agent dispatch
Base layer, no agent involvement.

---

## 9. FAILURE SCENARIOS

### /sqa Failure Chains

**Failure 1: Layer halt-on miss**
1. Layer 3 finds MEDIUM finding but `--halt-on HIGH` is set
2. Pipeline continues to Layer 7
3. User receives all findings but expected early exit
4. **Root cause**: threshold misconfiguration or severity misclassification

**Failure 2: Resume integrity gap**
1. Session interrupted mid-Layer 4
2. No checkpoint saved (--evidence not used)
3. Re-run requires starting from Layer 0
4. **Root cause**: --evidence flag not used

### /arch Failure Chains

**Failure 1: Template not found**
1. Template name typo in query
2. Template router falls back to default
3. Wrong analysis depth applied
4. **Root cause**: no template existence validation before load

**Failure 2: GoT path issue on Windows**
1. Graph-of-Thought template uses backslash paths
2. Path not found on Windows
3. GoT analysis silently skipped
4. **Root cause**: cross-platform path handling not enforced

### /rca Failure Chains

**Failure 1: Falsification bypass**
1. Adversarial agent claims finding without verification
2. confidence_assistant_downgrade() reduces confidence
3. Finding still appears in output at lower tier
4. **Root cause**: evidence_store not checked for counter-evidence

**Failure 2: Session context loss**
1. RCA runs with full context
2. Session compacted
3. Evidence references stale
4. **Root cause**: evidence not persisted to durable store

### /skill-ship Failure Chains

**Failure 1: Phase 1.5 skipped**
1. Phase 1.5 not executed (simple skill assumption)
2. No skip reason logged in workflow-state.json
3. Phase 2 begins without Phase 1.5 output
4. **Gate violation**: Phase 2 blocked until skip reason documented

**Failure 2: Agent list hardcoded** (FIXED)
1. BUILTIN_AGENTS list hardcoded in list_agents.py
2. Anthropic adds new builtins
3. list_agents.py reports stale list
4. **Root cause**: hardcoded list, not config-driven
5. **Fix applied**: builtins now loaded from `~/.claude/skills/skill-ship/config/builtins.json`

---

## 10. CONFIGURATION FILES

| Skill | Config File | Location Priority |
|-------|-------------|------------------|
| /sqa | — | N/A (CLI flags only) |
| /arch | `.archconfig.json` | project > user > env var |
| /rca | — | N/A (evidence-based) |
| /skill-ship | `builtins.json` | `~/.claude/skills/skill-ship/config/` |
| /sdlc | `test.json` | `P:\packages\sdlc\` |

---

## 11. KEY FILES REFERENCE

### /sqa critical files
- `P:\.claude\skills\sqa\SKILL.md` — pipeline definition
- `P:\.claude\skills\sqa\__lib\` — layer implementations
- `P:\.claude\skills\sqa\scripts\` — CLI

### /arch critical files
- `P:\.claude\skills\arch\SKILL.md` — template router
- `P:\.claude\skills\arch\resources\` — 6 templates
- `P:\.claude\skills\arch\config.py` — config loading

### /rca critical files
- `P:\packages\rca\SKILL.md` — entry point
- `P:\.claude\skills\rca\` — skill wrapper
- `P:\packages\rca\debugRCA\` — course materials

### /skill-ship critical files
- `P:\.claude\skills\skill-ship\SKILL.md` — master coordinator
- `P:\.claude\skills\skill-ship\references\workflow-phases.md` — phase details
- `P:\.claude\skills\skill-ship\references\agent-tool-usage.md` — agent reference
- `P:\.claude\skills\skill-ship\config\builtins.json` — dynamic builtins

### /sdlc critical files
- `P:\packages\sdlc\contract-primitives\` — base contracts
- `P:\packages\sdlc\skills\` — skill definitions
- `P:\packages\sdlc\test.json` — test config