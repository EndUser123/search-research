# Verbose Mode Templates for /gto

This document contains the output templates for verbose mode analysis (`/gto --verbose` or `/gto -v`).

## When to Use Verbose Mode

- User corrections detected (learning opportunities)
- Complex multi-issue sessions
- Need full audit trail
- Pattern repetitions to document
- Anti-patterns detected (workaround over root cause)

## Verbose Output Sections

Verbose mode includes ALL sections from compact mode PLUS these additional detailed sections:

### TL;DR Session Context
- Brief summary of what was being worked on
- Current state and blockers
- Key decisions made

### Detailed Severity Breakdowns
- **Critical**: Must fix now (broken hooks, security vulnerabilities, data loss, import errors)
- **High**: Should fix soon (user-facing bugs, incomplete features, repeated user corrections, test failures)
- **Medium**: Should fix eventually (warnings, dropped topics, context switches, ambiguous requirements)
- **Low**: Nice to have (style improvements, minor conversation flow issues, cosmetic problems)

### User Feedback Summary
- **Positive signals**: Approvals, confirmations, "correct", "good"
- **Negative signals**: Corrections, "wrong", "backwards", "no", "fix this"

### Session Flow Analysis
- **Dropped topics**: Items mentioned but not pursued
- **Context switches**: Changes in focus or direction
- **Anti-patterns**: Workaround over root cause, incomplete investigations

### Task Tracker Summary
- All mentioned tasks with status
- Blocked items and dependencies

### Recommendations with Rationale
- Each recommendation includes:
  - **Rationale**: Why this matters
  - **Impact**: What happens if not addressed
  - **Effort**: Time/complexity estimate

### Completed Actions vs. Pending Next Steps
- What was done in this session
- What still needs attention

### Plan Status with Blockers
- Active plans and progress
- Outstanding steps and dependencies

### Production Readiness
```markdown
**Production Readiness**
- All tests passing: ✅ / ⚠️ / ❌
- Documentation complete: ✅ / ⚠️ / ❌
- Breaking changes noted: ✅ / ⚠️ / ❌
- Performance verified: ✅ / ⚠️ / ❌
- Security review: ✅ / ⚠️ / ❌
- Recommendation: [Ready for production] OR [Run `/ship` for deploy readiness check] OR [Address blocking issues first]
```

### Risk Assessment
```markdown
**Risk Assessment**
- Breaking changes: 🟢 Low / 🟡 Medium / 🔴 High - [Description]
- Test coverage: 🟢 Low / 🟡 Medium / 🔴 High - [Description]
- Performance: 🟢 Low / 🟡 Medium / 🔴 High - [Description]
- Security: 🟢 Low / 🟡 Medium / 🔴 High - [Description]

Overall risk: 🟢 Low / 🟡 Medium / 🔴 High - [Recommendation]
```

### Learning Opportunities
```markdown
**Learning Opportunities**
- Pattern detected: [Description of repeated issue/lesson]
- Recommendation: `/learn` - Capture "Do X not Y" pattern to memory
- OR: `/reflect` - Full session reflection for complex lessons

**Lessons Learned**
- [Lesson 1]: [What was learned]
- [Lesson 2]: [What was learned]
- [Lesson 3]: [What was learned]

Recommendation: `/reflect` - Capture these patterns for future sessions
```

### Cleanup Checklist
- **Files**: Temporary files, debug code, test artifacts
- **Code**: Debug prints, commented code, incomplete implementations
- **Git**: Uncommitted changes, stale branches, merge conflicts
- **Processes**: Background processes, stale locks, zombie processes

### Broken Windows
- Partial work that needs completion or rollback
- Incomplete refactors
- Stub implementations
- TODO comments in production code

### Follow-up Items
- Research/investigation items noted but not pursued
- Technical debt items
- Future enhancements
- Dependencies to update

### Context State
- **Hooks disabled**: Any hooks temporarily disabled
- **Config changes**: Configuration modifications made
- **Dependencies added**: New dependencies introduced
- **Environment changes**: Environment variables or settings changed

### Decisions & Rationale
- Approaches taken and why
- Alternatives considered and rejected
- Trade-offs accepted

### Unblocking Actions
```markdown
**Unblocking Actions**
- If tests fail: `/tdd --debug` - Debug failing test with TDD workflow
- If unclear requirements: Return to Phase 1 REQUIREMENTS
- If context full: `/checkpoint-create` then `/checkpoint-restore` to fresh session
- If need root cause: `/debugRCA` - Technical investigation
- If stuck on approach: `/arch` - Architecture decision guidance
```

## Integration with Compact Mode

Verbose mode outputs ALL of the above PLUS the compact snapshot sections:
- === GTO SNAPSHOT ===
- **Session Resume**
- **Status Details**
- **Implementation**
- **Tests:** [summary]
- **Notes**
- **Did You Forget Anything?** (with package media & documentation check and package skill rename CRUD checklist)
- **Recommended Next Steps**

This ensures verbose mode provides comprehensive deep-dive analysis while maintaining the actionable summary format.
