# CSF

Cognitive Steering Framework.

A comprehensive cognitive infrastructure system for Claude Code on Windows 11, providing constitutional governance, skills, hooks, and observability tools for solo development workflows.

## Quick Start

```bash
# Run system health check via plugin skill
/health

# Or execute underlying script directly
python P:/packages/.claude-marketplace/plugins/cc-skills-utils/skills/health/scripts/main_health.py
```

## Project Structure

```
P:\__csf\
├── docs\                    # Design documentation
│   └── CSF_SOLUTION_DESIGN.md
├── csf\                     # Package implementation
├── .claude\                 # Claude Code runtime (symlink to P:\.claude)
└── reports\                 # Generated reports
```

## Configuration

### API Keys & Environment

The system requires API keys for LLM providers and external services. These are managed via `.env` files and validated by the `/health` skill.

- **Primary .env**: `P:/.env`
- **Validation**: Run `/health --llm` to verify provider status.

### Health Check Commands

Use `/health` with the following flags:

| Flag | Description |
|------|-------------|
| `--health` | System health status (default) |
| `--activity` | Last hour system activity |
| `--llm` | Provider health and API key status |
| `--tests` | Test coverage statistics |
| `--all` | Run all status checks |

## Documentation

| Document | Description |
|----------|-------------|
| [CSF Solution Design](docs/CSF_SOLUTION_DESIGN.md) | Architecture & migration plan |
| [Beads Setup Guide](docs/BEADS_SETUP.md) | Task tracker installation & multi-worktree configuration |
| [CFLO Architecture](docs/CFLO_ARCHITECTURE.md) | Cognitive Feedback Loop Orchestrator - Multi-agent closed-loop workflows |
| [Verification Workflow Documentation](docs/VERIFICATION_WORKFLOW.md) | Evidence-based claim validation and enforcement system |

## Key Systems

### Observability
- **System Health**: 13 health checks covering infrastructure, integrations, and providers
- **Activity Tracking**: Session-scoped event tracking
- **Error Analysis**: Rate monitoring and correlation

### Constitutional Governance
- **CLAUDE.md**: v7.3 constitution with 11+ principles
- **Skills**: Cognitive patterns (execution-clarity, response-atomicity, etc.)
- **Hooks**: Event-based validation and enforcement

### Knowledge & Research
- **CKS**: Constitutional Knowledge System for semantic search
- **Research Providers**: Tavily, Serper, WebReader integration

### Task Tracking
- **Beads (bd)**: Shared task database across all worktrees
  - Single source of truth at `P:\.beads\`
  - Git-backed with dependency tracking
  - Auto-injects context via Claude Code hooks
  - See [Beads Setup Guide](docs/BEADS_SETUP.md)

### Multi-Agent Orchestration
- **CFLO**: Cognitive Feedback Loop Orchestrator
  - Closed-loop builder/verifier cycles with convergence detection
  - State persistence and multi-terminal isolation
  - Stop hook integration for workflow protection
  - See [CFLO Architecture](docs/CFLO_ARCHITECTURE.md)

## Requirements

- Python 3.12+
- Windows 11
- Claude Code CLI
- P:\ drive workspace

## License

Internal use - Solo development environment

---

**Last Updated:** 2026-02-07
**Status:** Active development
