# Implementation Plan: /gto (gap-task-opportunities) Skill

## Overview
Create the `/gto` skill from scratch with 6 strategic enhancements for session-scoped gap analysis and task opportunity detection.

## Architecture
```
.claude/skills/gap-task-opportunities/
├── SKILL.md                    # Main skill definition
├── scripts/
│   ├── session_analyzer.py     # Core: conversation analysis, TODO/FIXME detection
│   ├── code_scanner.py         # Core: file scanning, test coverage analysis
│   ├── cks_integrator.py       # Enhancement #1: CKS pattern storage
│   ├── quick_actions.py        # Enhancement #2: one-command fix generation
│   ├── dependency_analyzer.py  # Enhancement #3: dependency graph mapping
│   ├── friction_detector.py    # Enhancement #4: conversation friction analysis
│   ├── test_matrix.py          # Enhancement #5: test verification matrix
│   └── trend_analyzer.py       # Enhancement #6: session trend analysis
└── tests/
    ├── test_session_analyzer.py
    ├── test_code_scanner.py
    └── test_enhancements.py
```

## 6 Enhancements
1. **CKS Integration** - Store discovered patterns in CKS for cross-session learning
2. **Quick Actions Menu** - One-command fixes for common gaps
3. **Dependency Graph Analysis** - Map file dependencies using /serena
4. **Hook Friction Detection** - Analyze conversation for blocks and rework
5. **Test Verification Matrix** - Cross-reference code changes with test status
6. **Session Trend Analysis** - Compare current session to historical patterns

## Success Criteria
- [ ] /gto skill invoked successfully analyzes session + codebase
- [ ] All 6 enhancements produce output
- [ ] CKS integration persists patterns
- [ ] Quick actions generate valid commands
- [ ] Test matrix cross-references coverage
- [ ] Unit tests pass (80%+ coverage)
- [ ] Integration tests pass
