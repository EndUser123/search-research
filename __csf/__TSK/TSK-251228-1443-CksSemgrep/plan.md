# Implementation Plan: Hybrid Semgrep + ESLint Auto-Fix System

## Overview
Implement violation detection and auto-fix for Python (Semgrep) and TypeScript (ESLint) using project configuration files.

## Architecture Decision
**Project files approach** - Store configs in `.semgrep.yml` and `.eslintrc.json` at project root.

**Rationale:**
- No JSON escaping of YAML
- Faster file I/O vs database queries
- Full git history and version control
- Team can read configs directly
- Simpler debugging (cat .semgrep.yml)

## Implementation Phases

### Phase 1: Foundation (Week 1)

#### 1A: Semgrep Setup (Day 1)
- Install Semgrep: `pip install semgrep`
- Create `.semgrep.yml` with 20+ Python rules
- Test on sample Python files
- Verify auto-fix works

#### 1B: ESLint Setup (Day 1-2)
- Install ESLint: `npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin`
- Create `.eslintrc.json` with 15+ TypeScript rules
- Test on sample TypeScript files
- Verify auto-fix works

#### 1C: Orchestrator Skeleton (Day 2-3)
- Create `orchestrator.py`
- Detect file language (Python vs TypeScript)
- Route to appropriate tool
- Parse and aggregate results

**Success:** Both languages detecting and fixing violations

### Phase 2: Integration (Week 2)

- Orchestrator enhancement (`verify_all_fixed()` method)
- unified_analyzer integration
- Error handling and logging
- End-to-end testing

### Phase 3: Claude Fallback (Week 3)

- Identify unfixable violations
- Generate Claude Code prompts
- Semantic violation handling

### Phase 4: Testing & Documentation (Week 4)

- Full test suite
- Windows 11 validation
- Documentation
- Team onboarding

## File Structure

```
project_root/
├── .semgrep.yml                    # Python rules
├── .eslintrc.json                  # TypeScript rules
├── src/
│   ├── quality/
│   │   ├── orchestrator.py         # Main orchestrator
│   │   ├── unified_analyzer.py     # Integration point
│   │   ├── claude_fallback.py      # Semantic handler
│   │   └── tests/
│   │       ├── test_orchestrator.py
│   │       └── test_integration.py
│   └── ... (your app code)
└── docs/
    ├── installation.md
    ├── usage.md
    └── configuration.md
```

## File Changes

### New Files
```
P:/__csf.nip/
├── .semgrep.yml                           (NEW, ~100 lines)
├── .eslintrc.json                         (NEW, ~50 lines)
└── src/quality/
    ├── orchestrator.py                    (NEW, ~150 lines)
    ├── claude_fallback.py                 (NEW, ~100 lines)
    └── tests/
        ├── test_orchestrator.py           (NEW, ~200 lines)
        └── test_integration.py            (NEW, ~150 lines)
```

### Modified Files
```
P:/__csf.nip/src/quality/
└── unified_analyzer.py                    (MODIFY, add ~30 lines)
```

## Validation Criteria

| Phase | Criteria | Test Command |
|-------|----------|--------------|
| 1A | Semgrep installed | `semgrep --version` |
| 1A | Config valid | `semgrep --config=.semgrep.yml --help` |
| 1A | Auto-fix works | `semgrep --config=.semgrep.yml --autofix test.py` |
| 1B | ESLint installed | `eslint --version` |
| 1B | Config valid | `eslint --config=.eslintrc.json --help` |
| 1B | Auto-fix works | `eslint --config=.eslintrc.json --fix test.ts` |
| 1C | Orchestrator runs | `python src/quality/orchestrator.py src/` |
| 2 | unified_analyzer integration | `pytest tests/test_unified_analyzer.py -v` |
| 3 | Fallback generates prompts | `pytest tests/test_claude_fallback.py -v` |
| 4 | All tests pass | `pytest src/quality/tests/ -v` |
| 4 | Windows validated | Manual testing on Windows 11 |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Semgrep not installed | Log warning, skip Python checks |
| ESLint not installed | Log warning, skip TypeScript checks |
| Windows path issues | Use shutil.which(), pathlib |
| Config file missing | Log error, return empty results |
| Subprocess fails | Try/except, return error in results |

## Rollback Plan

If integration fails:
1. Remove orchestrator.py (standalone module)
2. Revert unified_analyzer.py changes
3. Document configs as standalone (can run manually)

## Success Metrics

1. `.semgrep.yml` and `.eslintrc.json` exist
2. Orchestrator detects file language correctly
3. Both tools run via subprocess
4. Results aggregated into unified format
5. ≥95% of test violations auto-fixed
6. Verification loop confirms fixes
7. Works on Windows 11
8. Both Python and TypeScript in Phase 1

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | Week 1 | Both languages detecting + fixing |
| Phase 2 | Week 2 | Integration with unified_analyzer |
| Phase 3 | Week 3 | Claude fallback for semantic violations |
| Phase 4 | Week 4 | Testing, documentation, team adoption |

**Total: 4 weeks to full implementation**

## Next Steps After This

1. Create initial config files
2. Install tools (Semgrep, ESLint)
3. Build orchestrator skeleton
4. Add Claude fallback for semantic violations
5. Integrate with pre-commit hooks
