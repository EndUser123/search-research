# Task Contract

## Objective
Implement TDD skill v3.2 with Windows 11 compatibility (no fcntl), O(1) active session tracking, and capped workspace scanning depth.

## Scope
**In scope:**
- .claude/skills/tdd/session_models.py — SessionState, PhaseReceipt, TddEvidence models
- .claude/skills/tdd/generate_context.py — Session init with O(1) .active_run pointer
- .claude/skills/tdd/run_phase.py — RED/GREEN/REFACTOR wrapper
- .claude/skills/tdd/validate_tdd.py — Receipt-based validator
- .claude/hooks/preflight_require_tdd.py — O(1) TDD pattern detection
- .claude/hooks/stop_if_tdd_unverified.py — O(1) verification gate
- .claude/skills/tdd/SKILL.md — Skill documentation

**Out of scope:**
- Any fcntl-based locking (Unix-only)
- Directory iteration for active session detection
- Deep workspace scanning beyond depth 3

## Forbidden Files
- Any existing TDD skill files that use fcntl
- Any global retry lock mechanisms

## Acceptance Criteria
- [ ] session_models.py has no fcntl imports, uses SessionState.retries for retry tracking
- [ ] generate_context.py creates .active_run pointer file (not directory scan)
- [ ] run_phase.py accepts --override-cmd and --timeout args
- [ ] validate_tdd.py uses localized retries, no global locks
- [ ] Hooks use O(1) ACTIVE_PTR.exists() checks
- [ ] Workspace scanner caps at depth 3

## Verification Commands
```bash
grep -r "fcntl" P:/worktrees/tdd-v3.2/.claude/skills/tdd/ && echo "FAIL: fcntl found" || echo "PASS: no fcntl"
grep "ACTIVE_PTR" P:/worktrees/tdd-v3.2/.claude/skills/tdd/generate_context.py
python P:/worktrees/tdd-v3.2/.claude/skills/tdd/generate_context.py "feature" "Test TDD v3.2"
```

## State
- Created: 2026-04-19
- Status: IN_PROGRESS
- Iteration: 0
- Review Depth: quick
