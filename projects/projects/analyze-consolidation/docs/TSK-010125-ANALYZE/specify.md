# TSK-010125-ANALYZE: /analyze Command Consolidation

**Created**: 2025-01-01
**Status**: Phase 1 Complete | Phase 2 In Progress
**Type**: Feature Refactoring

## Objective

Consolidate `/quality`, `/intel`, and `/pmgoa` commands into a unified `/analyze` command by:

1. **Decomposing** source commands into reusable core functions
2. **Creating** a shared library (`analyze_lib/`) to eliminate redundancy
3. **Refactoring** `/analyze` to use the shared library
4. **Deprecating** source commands (redirect to `/analyze`)

## Context

**Current State**:
- `/quality` - 131KB qual-gate.py with 9-phase orchestration
- `/intel` - 18KB strategic intelligence with 15+ frameworks
- `/pmgoa` - Dual-agent analysis pipeline
- `/analyze` - Partial consolidation, delegates to backends

**Problem**:
- Code duplication across commands (context collection, file collection, constitution checking, LLM provider)
- No single entry point for analysis
- Maintenance burden (4 separate commands)

## Solution Architecture

### Phase 1: Decomposition ✅ COMPLETE

Created `src/commands/co/analyze_lib/` shared library:

| Module | Lines | Purpose | Source Consolidated |
|--------|-------|---------|---------------------|
| `context.py` | 311 | Git, session, cwd context collection | PMGOA ContextCollector + /analyze detect_context |
| `files.py` | 267 | File content collection with filtering | Quality unified_analyzer + /analyze _collect_file_contents |
| `constitution.py` | 355 | Constitution tree checking | Quality gate + /analyze _check_constitutional_compliance |
| `llm.py` | 250 | LLM provider wrapper | PMGOA zen_integration + /analyze _create_llm_provider |
| `prompts.py` | 480 | Prompt generation templates | PMGOA Analyzer + /analyze + intel |

**Redundancy Eliminated**: ~800 lines of duplicate code

### Phase 2: Refactor /analyze (IN PROGRESS)

- [ ] Update `analyze_backends.py` to use `analyze_lib`
- [ ] Remove redundant code from `/analyze`
- [ ] Test all existing functionality
- [ ] Add framework detection from intel
- [ ] Add strategic intelligence features

### Phase 3: Missing Features

- [ ] Input sources: question, stdin, git ref
- [ ] Focus lenses: testing, documentation, debt, etc.
- [ ] Multi-agent council (resolve cognitive_stack dependency)

### Phase 4: Deprecation

- [ ] Mark `/quality` → use `/analyze --focus quality`
- [ ] Mark `/intel` → use `/analyze --mode council`
- [ ] Mark `/pmgoa` → use `/analyze`

## Evidence

- **Decomposition Document**: `P:/__csf.nip/src/commands/co/analyze-decomposition.md`
- **Validation Plan**: `P:/__csf.nip/src/commands/co/analyze-validation-plan.md`
- **Shared Library**: `P:/__csf.nip/src/commands/co/analyze_lib/`

## Session History

- 2025-01-01 00:50 - Started decomposition phase
- 2025-01-01 01:00 - Completed Phase 1 (all 5 modules created)
- 2025-01-01 01:05 - Project directory created via CWO
