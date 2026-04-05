# dnld_telegram TDD Refactor - SIMPLIFIED

> 🚨 **NEW LLM? MANDATORY FIRST STEP**: You MUST complete task `ONBOARDING-1` before any development work. This task requires reading this README, `CLAUDE.md`, and `coordination/tasks.json` to understand project context. The coordination system will automatically block all development tasks until onboarding is complete.

## 📋 Overview
Simplified TDD refactoring setup for dnld_telegram with parallel execution support.

**Status**: Ready for parallel execution
**Coordination**: `../../coordination/` directory
**Active Protocol**: Simplified Parallel Refactoring v3.4

## 🚀 Quick Start

### 1. MANDATORY: Complete Onboarding (ONBOARDING-1)
**Before any development work**, you must complete the onboarding task:

```bash
# Select onboarding task (will be automatically prioritized)
python -m llm_coordination.tasks.selector --coordination-file coordination/tasks.json

# After completing ONBOARDING-1, proceed with development tasks
```

**Onboarding Requirements**:
- ✅ Read and understand this README
- ✅ Read and understand `../../CLAUDE.md` (project-specific instructions)
- ✅ Read and understand `coordination/tasks.json` (task definitions and dependencies)
- ✅ Acknowledge refactoring goals and coordination protocol

### 2. Check Current Status (After Onboarding)
```bash
# View coordination status
cat coordination/tasks.json

# Select optimal development task
python -m llm_coordination.tasks.selector --coordination-file coordination/tasks.json
```

### 3. Available for Parallel Work (After Onboarding)
- **QW-3**: Add Basic Async Logging Context (45min)
- **P1A**: Complete Abstract Base Class Implementations (2-3h)
- **P1B**: Enhanced Async Compliance Testing (2-3h)

Tasks P1A and P1B can run in parallel.

### 4. Follow Enhanced Plan
Detailed implementation plan: `2025-08-16_enhanced_tdd_refactor_plan.md`

## 📁 Current Structure

```
refactors/
├── README.md                              ← This simplified guide
├── 2025-08-16_enhanced_tdd_refactor_plan.md ← Detailed implementation plan
├── progress_tracker.json                   ← Original progress tracking
└── checkpoints/                           ← Task completion checkpoints
    ├── QW-1-database-blocking-fixed.json ← ✅ Completed
    ├── QW-2-imports-fixed.json           ← 🟡 In progress
    └── QW-3-async-logging-ready.json     ← ⏳ Available
```

## 🔗 Coordination
Main coordination is now in `../../coordination/` using Parallel Refactoring Protocol v4.1.

## 🎯 Key Documents

- **`2025-08-16_enhanced_tdd_refactor_plan.md`** - Complete implementation plan
- **`progress_tracker.json`** - Original task tracking
- **`checkpoints/`** - Task completion verification

## 📊 Current Status

**QW-1**: ✅ Database blocking fixed
**QW-2**: ⏳ Import fixes available
**QW-3**: ✅ Async logging context added
**P1A**: ✅ Abstract base classes completed
**P1B**: ✅ Async compliance testing completed
**P1C**: ✅ Structured observability foundation added
2. **File Conflicts**: Use file-level locking protocol in parallel guide
3. **Test Failures**: Review verification criteria in task definitions
4. **Resource Issues**: Monitor concurrent execution limits

### Emergency Protocols
- **Team Blocked**: Create issue checkpoint, switch to parallel task
- **Checkpoint Timeout**: Manual coordination after 60 minutes
- **Integration Failures**: Run cross-team integration tests

## 📞 Support

### Documentation Hierarchy
1. **This README** - Overview and navigation
2. **Enhanced Plan** - Complete implementation strategy
3. **Technical Briefings** - Pattern implementation details
4. **Parallel Guide** - Team coordination protocols

### Testing Guidelines
All development work should follow comprehensive testing practices as documented in:
- [Coordination Testing Guidelines](coordination/TESTING_GUIDELINES.md) - Detailed strategies for mocking, patching, and dependency injection
- [Enhanced TDD Refactor Plan](2025-08-16_enhanced_tdd_refactor_plan.md) - Task-specific testing requirements and examples

Key testing principles:
- **Isolate external dependencies** using mocking or dependency injection
- **Follow TDD workflow**: RED → GREEN → REFACTOR for each feature
- **Test error paths** and exception handling
- **Use parametrized tests** for multiple scenarios

### Archive Access
Previous strategies and analysis available in `archive/` for reference:
- Original TDD plan and architecture analysis
- Large database strategy (implemented separately)
- Historical context and alternative approaches

---

**Next Steps**: Start with `2025-08-16_enhanced_tdd_refactor_plan.md` → Quick Wins → QW-1 (Critical Database Blocking Fix)
