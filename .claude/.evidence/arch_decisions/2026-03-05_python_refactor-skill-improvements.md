# Architecture Decision: Refactor Skill Improvements

**Date:** 2026-03-05
**Template:** Python
**Intent:** General architecture decision (DEFAULT)

## Decision

**Option C (Both)** - Update SKILL.md documentation AND create Python automation modules

## Rationale

1. **Hybrid nature** - Some improvements are workflow changes (documentation), others require deterministic automation (Python modules)
2. **Token efficiency** - Python modules save tokens by avoiding repeated code generation for git operations, test creation, and state persistence
3. **Reliability** - Rollback automation, test generation, and synergy detection require precise, error-free execution that benefits from tested Python code
4. **Progressive disclosure** - Keep SKILL.md focused on workflow, expand with reference documentation for detailed API specs

## Alternatives Considered

| Alternative | Trade-off |
|-------------|-----------|
| **Option A (Documentation only)** | Would require Claude to regenerate same code repeatedly (rollback scripts, test files, JSON persistence) - inefficient and error-prone |
| **Option B (Python modules only)** | Would lose the "teaching" aspect of SKILL.md - Claude needs to understand the workflow, not just execute code |
| **Option C (Both)** | Optimal balance - documentation guides reasoning, modules handle automation |

## Risk

**Increased complexity** - More files to maintain (SKILL.md + 6-8 Python modules)

**Mitigation:** Use clear separation - SKILL.md for workflow, `/lib/` for automation, `/scripts/` for CLI tools

## Technical Analysis

### Async Assessment
**Decision:** Hybrid approach - Use asyncio for I/O operations, multiprocessing for CPU-bound analysis (synergy detection, complexity triage)

### Type System
**Recommendation:** Application-level domain models with TypeVars for generic containers

### GIL & Multiprocessing
**Decision:** Use `multiprocessing.Pool` for CPU-bound operations, minimize shared memory via message passing

## Recommended Implementation Structure

```
P:\.claude\skills\refactor\
├── SKILL.md                      # Update with 8 improvements (workflow)
├── __lib__/                      # NEW: Python automation modules
│   ├── __init__.py
│   ├── rollback_manager.py       # Rollback automation
│   ├── test_generator.py         # Test generation (TDD phases)
│   ├── synergy_detector.py       # Cross-file pattern clustering
│   ├── complexity_triage.py      # Risk-based prioritization
│   ├── state_manager.py          # Progress persistence
│   └── config.py                 # Configuration management
└── scripts/                      # NEW: CLI tools (optional)
    ├── rollback_cleanup.py       # Cleanup old rollback plans
    └── refactor_status.py        # Query progress state
```

## Implementation Priority

1. **P0 (High-impact):**
   - Rollback automation (`lib/rollback_manager.py`)
   - Test generation (`lib/test_generator.py`)
   - Synergy detection (`lib/synergy_detector.py`)

2. **P1 (Medium-impact):**
   - Complexity triage (`lib/complexity_triage.py`)
   - State management (`lib/state_manager.py`)
   - Configuration (`lib/config.py`)

3. **P2 (Lower-priority):**
   - Incremental mode (SKILL.md update only)
   - Synergy skill integration (SKILL.md update only)

## Confidence

**85%** - Evidence basis:
- **Web research:** 2 sources on Claude Code Skills architecture confirming hybrid approach (documentation + scripts) is best practice
- **Codebase analysis:** Review of `/refactor` skill (770 lines) shows it's documentation-heavy with no automation - opportunity for improvement
- **Python best practices:** CLI tools should separate business logic from interface, supporting modular structure

## Key Assumptions

1. The 8 improvements all warrant implementation
2. Hybrid approach (documentation + automation) provides optimal balance
3. Python 3.12+ features (type hints, asyncio) are available

## Adversarial Self-Review

**Weakest assumption:** That the 8 improvements all warrant implementation. Some may be YAGNI (e.g., progress persistence if most refactorings are one-shot).

**Consequence:** Over-engineering with unused modules.

**Mitigation:** Start with highest-impact improvements (rollback, test generation, synergy detection), defer lower-priority features.

## Sources

- [Python CLI Architecture Best Practices 2024](https://cloud.tencent.com/developer/article/2550689)
- [Claude Code Skills Architecture Guide](https://blog.csdn.net/yangshangwei/article/details/158319117)
- [Claude Skills Complete Guide](https://juejin.cn/post/7601929765533859891)
