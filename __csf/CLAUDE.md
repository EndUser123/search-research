# __csf (CSF NIP)

## Purpose

Constitutional Skills Framework - Next Iteration Platform. A heavy AI-assisted development ecosystem where technical direction guides LLM implementation.

## Development Workflow

**Director Model**: You direct, AI agents implement.

- **User role**: Technical architect/director - provides requirements, reviews work, guides direction
- **AI role**: Primary developer - writes code, tests, documentation under user guidance
- **Quality priority**: Thoroughness > speed. "Does it work correctly?" > "How fast can we ship?"
- **LLM-generated code**: Default and expected. Tests, scenarios, and implementation are AI-generated.

**What this means for tools:**
- Tools should **guide and assist AI agents**, not replace user direction
- **Functional verification matters** - importing and testing code is essential
- **LLM generation with guardrails** - DSLs, validation, verification cycles are appropriate
- **Quality gates** - thorough testing, integration flows, and performance baselines

## Architecture

### Core Systems

| System | Purpose | Location |
|--------|---------|----------|
| **CKS** | Constitutional Knowledge System - knowledge storage and retrieval | `src/knowledge/systems/cks/` |
| **CHS** | Chat History Search - semantic conversation search | `src/knowledge/systems/chs/` |
| **Skills** | Progressive disclosure commands (`/q`, `/p`, `/arch`, etc.) | `.claude/skills/` |
| **Hooks** | Claude Code event interception | `.claude/hooks/` |
| **Shared Libs** | Reusable infrastructure (research, handoff, tracking) | `src/shared_libs/` |

### Key Workflows

1. **Strategic Quality (`/q`)** → **Tactical Quality (`/p`)** - Quality gate pipeline
2. **Research** → **Architecture** → **Implementation** - Knowledge-driven development
3. **Testing** → **Verification** → **Certification** - Quality assurance

## Development Style

### ✅ Appropriate for This Project

- **LLM-generated tests**: Agents create tests, scenarios, and verification code
- **Quality-first tooling**: Thorough checks over fast checks
- **Integration flows**: YAML-defined workflows that test complete paths
- **Risk-aware testing**: Test what changed based on impact analysis
- **DSLs for LLMs**: Constrained formats that prevent hallucination
- **Performance baselines**: Quality gates for critical paths
- **Heavy automation**: Under user direction, not autonomous

### ❌ Not Appropriate (True Anti-Patterns)

- **Background autonomous execution**: Services running without user oversight/trigger
- **Self-healing systems**: Code that modifies itself without human approval
- **Real-time monitoring dashboards**: Always-running metrics services
- **Team approval gates**: Consensus processes for single-director workflow
- **Lock-free multi-terminal coordination**: Enterprise concurrency patterns
- **Enterprise patterns**: Complex frameworks when simple solutions suffice

**Key distinction**: LLM-generated code under your direction = ✅. Autonomous background services = ❌.

## Key Files

### Configuration
- `CLAUDE.md` (this file) - Project context and workflow
- `src/cli/nip/slc.md` - Pragmatic Solo Dev Guidelines (thoroughness over speed)
- `.claude/settings.json` - Claude Code configuration

### Skills
- `.claude/skills/q/SKILL.md` - Strategic quality assessment
- `.claude/skills/p/SKILL.md` - Tactical quality pipeline
- `.claude/skills/arch/SKILL.md` - Architecture advisor

### Knowledge Systems
- `src/knowledge/systems/cks/CLAUDE.md` - CKS usage and architecture
- `src/knowledge/systems/chs/CLAUDE.md` - CHS usage and architecture

### Testing
- `test_shared_libs_functionality.py` - Functional verification example
- `src/shared_libs/` - Reusable testing infrastructure
- Run tests: `pytest P:/__csf/tests/ -v`

## Dependencies

### Python Stack
- Python 3.12+ with type hints
- `pytest` for testing
- `ruff` for linting/formatting
- `mypy` for type checking

### Knowledge Systems
- SQLite (CKS, CHS storage)
- FAISS (vector search)
- PyTorch (optional GPU acceleration)

### AI Infrastructure
- Claude Code (CLI interface)
- Multiple MCP servers (NotebookLM, context7, etc.)

## Quick Reference

### Common Commands

```bash
# Quality assessment
/q                    # Strategic quality (did we do the right thing?)
/p                    # Tactical quality (did we implement correctly?)

# Knowledge management
/search "query"        # Search CKS, CHS, CDS, code, docs
/cks                  # CKS operations (ingest, query, stats)

# Testing
/test <module>         # Coverage analysis (what tests exist?)
/t <module>            # Full test suite (functional + coverage) [PROPOSED]

# Architecture
/arch "problem"        # Architecture guidance
/plan "task"           # Implementation planning
```

### When to Use What

| Question | Tool |
|----------|------|
| "Is this the right approach?" | `/q` (strategic) |
| "Is this implemented correctly?" | `/p` (tactical) |
| "What did we forget?" | `/r` (omissions) |
| "What are our options?" | `/s` (alternatives) |
| "Does this code work?" | `/t --func` (functional verification) |
| "What tests exist?" | `/t --cov` (coverage analysis) |
| "What does X do?" | `/search X` (knowledge lookup) |

## Development Philosophy

**Thoroughness First**: Every module should be functionally verified before considering it "done."

**Evidence-Based**: Show actual runs, test output, and verification — not summaries.

**LLM-Augmented**: Leverage AI agents for implementation, but maintain user direction.

**Quality Over Speed**: Better to be correct and thorough than fast and wrong.

**Local-First**: Everything runs locally. No cloud dependencies, no external services.

**Constitutional**: All development follows documented patterns and constraints.
