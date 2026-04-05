# loop-core

[![Tests](https://img.shields.io/github/actions/python-kyt/loop-core/workflows/Tests.yml/badge.svg)](https://github.com/python-kyt/loop-core/actions)
[![Coverage](https://img.shields.io/badge/coverage-79%25-brightgreen.svg)](https://github.com/python-kyt/loop-core)
[![Python](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://github.com/python-kyt/loop-core)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)

Terminal-local state management for Ralph-style autonomous loops.

## Purpose

Provides file-based state management that avoids Git race conditions in multi-terminal
environments. Each terminal has its own state directory, ensuring isolation and immunity
to stale data.

## Architecture

**Claude Code Plugin Structure:**
- `.claude-plugin/plugin.json` - Plugin metadata
- `scripts/` - Python code modules
- `skills/loop-code/` - Ralph-style autonomous loop skill
- `tests/` - Test suite (45 tests, 100% pass rate)

**Core Components:**
- **TerminalStateManager**: Manages terminal-local state with atomic writes
- **Plan Parser**: Extracts tasks from markdown plan files
- **Pattern Definitions**: Regex patterns for task and state detection

## Key Features

- Multi-terminal isolation (each terminal gets its own state directory)
- Atomic writes (temp file + rename pattern)
- PID-based lock files with stale lock cleanup
- No TTL for state (persists until explicitly cleared)

## Quick Start

```python
from scripts import TerminalStateManager, parse_plan_tasks

# Initialize state manager for current terminal
manager = TerminalStateManager()

# Read/write state
manager.write_state("current_task", {"id": "TASK-001", "status": "in_progress"})
state = manager.read_state("current_task")

# Parse plan file
tasks = parse_plan_tasks("plan.md")
incomplete_tasks = [t for t in tasks if not t["complete"]]
```

**Note:** This is a Claude Code plugin. Import paths use `core` instead of `loop_core`.

## Documentation

- **[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)** - Comprehensive usage guide with examples
- **[docs/ralph-worktrees.md](docs/ralph-worktrees.md)** - Git worktrees + /ralph-loop workflow for multi-terminal parallel development
- **[docs/loop-rollout.md](docs/loop-rollout.md)** - Rollback procedures for Ralph Loop platform
- **[examples/demo.py](examples/demo.py)** - Run the demo: `python examples/demo.py`
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture and integration patterns

## /loop-code Skill

The `/loop-code` skill implements a Ralph-style autonomous development loop using these utilities:

```bash
/loop-code path/to/plan.md
```

**Alternative**: Use `/code path/to/plan.md --loop` for integrated loop mode

**What it does:**
- Parses plan file and extracts tasks
- Executes `/code` workflow for each incomplete task
- Tracks completion state across iterations
- Exits when both conditions are met:
  - `completion_indicators >= 2` (heuristic)
  - `EXIT_SIGNAL: true` in RALPH_STATUS (explicit LLM signal)

**Exit detection:**
The LLM sets `EXIT_SIGNAL: true` in the plan's RALPH_STATUS block when it believes all work is complete and verified. This dual-condition gate prevents premature exit.

**See:** `skills/loop-code/SKILL.md` for complete documentation

## Key Features

**Multi-Terminal Isolation**
- Each terminal gets its own state directory
- No Git conflicts or race conditions
- Run multiple loops in parallel safely

**Atomic State Persistence**
- Crash-safe writes (temp file + rename)
- No TTL - state persists until explicitly deleted
- No stale data from expiration

**Lock Management**
- PID-based ownership with automatic stale cleanup
- Prevents concurrent access to critical sections
- Non-blocking attempts available

## Testing

```bash
pytest tests/ -v --cov
```

## Standards

- Python 3.14+
- Type hints required
- 80%+ test coverage
- Ruff linting
- Mypy type checking

## License

[MIT](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
