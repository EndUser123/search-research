# Recommended Next Steps Template

Reusable component used across all phase outputs (P1-P5).

## Pattern Specification

```markdown
**Recommended Next Steps**

1. [Domain Name]
   1a. `command` - Brief description
   1b. `command` - Brief description

2. [Domain Name]
   2a. `command` - Brief description

3. [Domain Name]
   3a. `command` - Brief description

**0 - Do ALL Recommended Next Steps**
```

## Rules

1. **Domain-organized**: Group related actions under domain headers (Testing, Code Quality, Infrastructure, etc.)
2. **Alphanumeric hierarchy**: Use numbered domains (1, 2, 3...) with alpha sub-options (1a, 1b, 2a...)
3. **Selection behavior**:
   - Domain number (e.g., "2") -> Do ALL actions in that domain (2a, 2b, 2c...)
   - Specific option (e.g., "2b") -> Do just that action
   - Mixed selection (e.g., "1, 3b, 5") -> Do all of domain 1, just action 3b, all of domain 5
   - **"0"** -> Do ALL Recommended Next Steps (execute everything in all domains)
4. **Commands in backticks**, descriptions plain text
5. **Priority-ordered**: most critical domains first
6. **"0" always last** -> The "do all" option is the final line

## Examples by Phase

| Phase | Domain Structure | Context |
|-------|-----------------|---------|
| P1 (Build) | 1. Testing, 2. Review | Tests passing |
| P2 (Review) | 1. Fix Tests, 2. Fix Findings, 3. View Details | Has findings |
| P3 (Validate) | 1. Continue, 2. Auto-fix | Stages pass |
| P4 (Publish) | 1. Continue, 2. Review Docs | Docs generated |
| P5 (Certify) | 1. Continue, 2. Deploy | Production-ready |

## Common Domains

**Infrastructure code:**
1. [Testing] - Run tests, check types
2. [Review Changes] - Git diff, verify fixes
3. [Continue Pipeline] - Re-run /p

**Package code:**
1. [Fix Tests] - Run TDD for failing tests
2. [Fix Findings] - TDD for CRITICAL/HIGH findings
3. [View Details] - Show full findings JSON
