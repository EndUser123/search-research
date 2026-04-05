# CSF

Cognitive Steering Framework.

A comprehensive cognitive infrastructure system for Claude Code on Windows 11, providing constitutional governance, skills, hooks, and observability tools for solo development workflows.

## Quick Start

```bash
# Run system health check
cd P:/__csf && python src/modules/observability/system_health.py health

# View all status information
python src/modules/observability/system_health.py all
```

## Project Structure

```
P:\__csf\
├── docs\                    # Design documentation
│   └── CSF_SOLUTION_DESIGN.md
├── src\                     # Source code
│   ├── modules\             # Core modules
│   │   ├── observability\   # Health monitoring & logging
│   │   ├── knowledge\       # CKS (Constitutional Knowledge System)
│   │   └── ...
│   ├── commands\            # CLI commands
│   ├── core\                # Core systems
│   └── ...
├── .claude\                 # Claude Code runtime (symlink to P:\.claude)
└── reports\                 # Generated reports
```

## Configuration

### API Keys & Environment

The system requires API keys for LLM providers and external services. See **[System Health Configuration](src/modules/observability/CONFIGURATION.md)** for:

- `.env` file locations (`P:/.env`, `P:\__csf\.env`)
- Sync validation between parent and project configs
- Adding new API keys
- Troubleshooting health check warnings

### Health Check Commands

| Command | Description |
|---------|-------------|
| `health` | System health status (default) |
| `activity` | Last hour system activity |
| `blocked` | Blocked actions and reasons |
| `tests` | Test coverage statistics |
| `all` | All status information |

## Documentation

| Document | Description |
|----------|-------------|
| [CSF Solution Design](docs/CSF_SOLUTION_DESIGN.md) | Architecture & migration plan |
| [System Health Configuration](src/modules/observability/CONFIGURATION.md) | API key setup & sync validation |
| [Beads Setup Guide](docs/BEADS_SETUP.md) | Task tracker installation & multi-worktree configuration |
| [CFLO Architecture](docs/CFLO_ARCHITECTURE.md) | Cognitive Feedback Loop Orchestrator - Multi-agent closed-loop workflows |
| [Verification Workflow Documentation](src/core/VERIFICATION_WORKFLOW_DOCUMENTATION.md) | Evidence-based claim validation and enforcement system |

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
