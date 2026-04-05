# Architecture Design: `/code Fix All` Iterative Pipeline

**Document Version:** 1.0
**Date:** 2026-03-01
**Status:** Design Proposal
**Author:** Architecture Analysis via `/arch`

---

## Executive Summary

**Problem:** Current `/p` pipeline requires manual iteration to fix findings → re-run review → fix again until clean. This is tedious, error-prone, and doesn't guarantee convergence.

**Solution:** Add `/code Fix all` iterative loop that automatically:
1. Fixes all findings using `/code` workflow
2. Re-runs P2 adversarial review
3. Checks for MEDIUM+ severity issues
4. Repeats until no MEDIUM+ issues remain

**Key Constraints:**
- ✅ Multi-terminal friendly (no shared state corruption)
- ✅ No TTL-based caching (content-addressed only)
- ✅ Immune to stale data (always fresh)

**Trade-off:** Increased P2 runtime (~3-5x longer) for significantly better code quality and convergence guarantee.

---

## 1. Problem Decomposition

### Current Workflow Limitations

```
User runs /p
  ↓
P2 finds 18 issues (2 HIGH, 11 MEDIUM, 5 LOW)
  ↓
User runs /tdd Fix all
  ↓
Fixes applied, tests pass
  ↓
User must remember to re-run /p
  ↓
P2 finds 7 NEW issues introduced by fixes
  ↓
Repeat manual cycle... 😞
```

**Pain Points:**
1. **Manual iteration** - User must remember to re-run `/p`
2. **No convergence guarantee** - When are we "done"?
3. **Fixes can introduce issues** - Single-pass doesn't catch cascading problems
4. **Tedious** - Each cycle requires explicit user action

### Desired Workflow

```
User runs /p
  ↓
P2 finds 18 issues
  ↓
User selects: /code Fix all (iterative)
  ↓
AUTOMATIC LOOP:
  - /code fixes all 18 issues
  - P2 re-runs automatically
  - 7 NEW issues found
  - /code fixes 7 new issues
  - P2 re-runs automatically
  - 0 MEDIUM+ issues remain ✅
  ↓
Convergence achieved! 🎉
```

---

## 2. Design Principles

### First Principles Analysis

**Assumption:** "Single-pass fixing is sufficient"
**Inversion:** "Multi-pass fixing until stable"

**Core Principle:** **Content-Addressed State Tracking**

Instead of "cache expires after X minutes", we use:
- **SHA256 hash of findings JSON** = unique version identifier
- **File mtime snapshots** = detect external changes
- **Terminal-scoped state files** = multi-terminal safety

### Systems Thinking

**Components:**
- `/p` orchestrator (existing)
- P2 adversarial review (existing)
- `/code` workflow (existing)
- Findings JSON (state)
- **NEW:** Iteration state manager (new)

**Ripple Effects:**
- Adding iteration → More P2 runs → Better code quality
- Multi-terminal → Terminal-scoped state → No corruption
- No TTL → Content-addressed → Always fresh data

### Constraints Checklist

| Constraint | Solution | Verification |
|------------|----------|--------------|
| Multi-terminal friendly | Terminal-scoped state file path | `code-fix-{terminal_id}.json` |
| No TTL | Content-addressed (SHA256 hashes) | Never use timestamps for expiry |
| Immune to stale data | Always read current file state | Re-compute on every iteration |

---

## 3. Architecture Components

### 3.1 State File Structure

**Location:** `.claude/state/code-fix-{terminal_id}.json`

**Why terminal-scoped?**
- Each terminal has its own independent iteration state
- No shared state = no corruption risk
- No locks needed = simpler implementation

**Schema:**
```json
{
  "version": "1.0",
  "terminal_id": "term_abc123",
  "project_root": "P:/packages/handoff",
  "status": "in_progress|completed|halted",

  "initial_findings": {
    "file": ".claude/findings/p2-full-review-2026-03-01.json",
    "sha256": "abc123...",
    "total_count": 18,
    "medium_plus_count": 13,
    "collected_at": "2026-03-01T10:00:00Z"
  },

  "generations": [
    {
      "iteration": 1,
      "findings_sha256": "abc123...",
      "findings_file": ".claude/findings/p2-full-review-2026-03-01.json",
      "medium_plus_count": 13,
      "fixes_applied": ["SEC-001", "SEC-002", "PERF-001"],

      "code_snapshot": {
        "git_commit": "a1b2c3d...",
        "file_mtsetup": {
          "src/handoff_store.py": 1740839150.123,
          "src/sessionstart.py": 1740839155.456
        }
      },

      "started_at": "2026-03-01T10:00:00Z",
      "completed_at": "2026-03-01T10:15:00Z",
      "duration_seconds": 900
    },
    {
      "iteration": 2,
      "findings_sha256": "def456...",
      "findings_file": ".claude/findings/p2-iteration-2-2026-03-01.json",
      "medium_plus_count": 7,
      "fixes_applied": ["SEC-003", "QA-001"],
      "code_snapshot": {...},
      "started_at": "2026-03-01T10:15:00Z",
      "completed_at": "2026-03-01T10:25:00Z",
      "duration_seconds": 600
    }
  ],

  "final_result": {
    "status": "completed",
    "total_iterations": 2,
    "total_fixes_applied": 15,
    "convergence_achieved": true,
    "completed_at": "2026-03-01T10:25:00Z"
  }
}
```

### 3.2 Iteration Loop Algorithm

```python
def code_fix_iteration_loop(initial_findings_file, terminal_id, max_iterations=5):
    """
    Iteratively fix findings until no MEDIUM+ issues remain.

    Multi-terminal safe: Uses terminal-scoped state file.
    No TTL: Uses content-addressed state (SHA256 hashes).
    Fresh data: Always re-computes findings, never caches.
    """
    state_file = Path(f".claude/state/code-fix-{terminal_id}.json")

    # Initialize state
    initial_findings = load_findings(initial_findings_file)
    initial_hash = sha256sum(initial_findings_file)
    state = {
        "version": "1.0",
        "terminal_id": terminal_id,
        "status": "in_progress",
        "initial_findings": {
            "file": initial_findings_file,
            "sha256": initial_hash,
            "total_count": len(initial_findings),
            "medium_plus_count": count_medium_plus(initial_findings)
        },
        "generations": []
    }

    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        print(f"[Iteration {iteration}] Starting...")

        # SAFETY CHECK: Verify we're still working on same findings
        current_findings_hash = sha256sum(state["initial_findings"]["file"])
        if current_findings_hash != initial_hash:
            raise ConcurrentModificationError(
                f"Findings file modified externally! "
                f"Expected {initial_hash}, got {current_findings_hash}"
            )

        # Get current findings (from previous iteration or initial)
        if iteration == 1:
            current_findings_file = state["initial_findings"]["file"]
        else:
            current_findings_file = state["generations"][-1]["findings_file"]

        current_findings = load_findings(current_findings_file)
        medium_plus_count = count_medium_plus(current_findings)

        # EXIT CONDITION: No MEDIUM+ issues
        if medium_plus_count == 0:
            state["status"] = "completed"
            state["final_result"] = {
                "status": "completed",
                "total_iterations": iteration - 1,
                "total_fixes_applied": count_total_fixes(state["generations"]),
                "convergence_achieved": True
            }
            atomic_write(state_file, state)
            print(f"✅ Convergence achieved after {iteration - 1} iteration(s)")
            break

        # SNAPSHOT: Record code state before fixes
        code_snapshot = {
            "git_commit": get_git_commit_sha(),
            "file_mtime": get_file_mtime_snapshot()
        }

        generation = {
            "iteration": iteration,
            "findings_sha256": sha256sum(current_findings_file),
            "findings_file": current_findings_file,
            "medium_plus_count": medium_plus_count,
            "code_snapshot": code_snapshot,
            "started_at": iso8601_now()
        }

        # FIX: Run /code workflow
        print(f"[Iteration {iteration}] Running /code Fix workflow...")
        fixes_applied = run_code_fix_workflow(current_findings)
        generation["fixes_applied"] = fixes_applied

        # REVIEW: Re-run P2 adversarial review
        print(f"[Iteration {iteration}] Re-running P2 review...")
        new_findings_file = run_p2_review()

        # VALIDATE: Check for external modifications
        new_snapshot = {
            "git_commit": get_git_commit_sha(),
            "file_mtime": get_file_mtime_snapshot()
        }

        if new_snapshot["git_commit"] != code_snapshot["git_commit"]:
            print("⚠️  WARNING: Git commit changed during iteration")
            print("External modifications detected, halting for safety")
            state["status"] = "halted"
            state["final_result"] = {
                "status": "halted",
                "reason": "external_modification",
                "iteration": iteration
            }
            atomic_write(state_file, state)
            break

        generation["completed_at"] = iso8601_now()
        generation["duration_seconds"] = parse_duration(generation["started_at"], generation["completed_at"])
        generation["findings_file"] = new_findings_file

        state["generations"].append(generation)
        atomic_write(state_file, state)

        print(f"[Iteration {iteration}] Complete: {len(fixes_applied)} fixes applied")

    # MAX ITERATIONS EXCEEDED
    if iteration >= max_iterations and state["status"] == "in_progress":
        state["status"] = "halted"
        state["final_result"] = {
            "status": "halted",
            "reason": "max_iterations_exceeded",
            "total_iterations": max_iterations
        }
        atomic_write(state_file, state)
        print(f"⚠️  Halted: Max iterations ({max_iterations}) exceeded")

    return state
```

### 3.3 Multi-Terminal Safety

**Risk:** Two terminals running `/code Fix all` simultaneously on same project

**Mitigation Strategy:**

1. **Terminal-Scoped State**
   - Each terminal writes to `code-fix-{terminal_id}.json`
   - No shared coordination needed
   - No locks, no race conditions

2. **Concurrent Modification Detection**
   - Each iteration checks if findings file SHA256 changed
   - If changed → Halt with error (external modification)
   - Prevents silent corruption

3. **Git Commit Monitoring**
   - Snapshot git commit SHA before/after fixes
   - If changed during iteration → Halt (external modification)
   - Detects if another terminal committed changes

**Why This Works:**
- Terminal A and Terminal B have independent state files
- Each detects external changes and halts safely
- No shared locks = no deadlocks
- No coordination needed = simpler, more reliable

### 3.4 Fresh Data Guarantees

**No Caching Principles:**

1. **Always Re-Compute Findings**
   - Never cache P2 review results across iterations
   - Always run full adversarial review
   - Result: Guaranteed fresh findings

2. **Content-Addressed State**
   - Use SHA256 hash of findings JSON, not timestamps
   - Hash changes = findings changed = re-process
   - No TTL = no staleness due to time

3. **File System as Source of Truth**
   - Always read current file state from disk
   - Never assume from cache
   - Use file mtimes to detect changes

**Anti-Patterns to Avoid:**

❌ **DON'T:** Cache findings for 5 minutes to save time
✅ **DO:** Re-run P2 every iteration (correctness > speed)

❌ **DON'T:** Assume file hasn't changed based on time
✅ **DO:** Check SHA256 hash every iteration

❌ **DON'T:** Use global state file shared across terminals
✅ **DO:** Use terminal-scoped state files

---

## 4. Integration Points

### 4.1 Modify `/p` SKILL.md "Action Required" Section

**Location:** `P:/.claude/skills/p/SKILL.md` lines 568-581

**Current:**
```markdown
### Action Required

0 - `/tdd all` - Fix ALL findings ({total} findings, recommended)
1 - `/tdd Fix Security` - Fix security vulnerabilities
...
```

**Proposed:**
```markdown
### Action Required

0 - `/code Fix all` - Fix ALL findings with iterative review (recommended)
    Iterates: fix → re-run P2 → fix MEDIUM+ → repeat until clean
    Estimated: 2-4 iterations, ~15-30 minutes total
1 - `/tdd Fix all` - Fix all findings with TDD workflow (single-pass)
2 - `/tdd Fix Security` - Fix security vulnerabilities
...
```

### 4.2 Create Iteration Orchestrator Script

**Location:** `P:/.claude/skills/p/scripts/code_fix_iteration.py`

**Responsibilities:**
1. Load initial findings JSON
2. Initialize iteration state file
3. Loop: `/code` → P2 review → check convergence
4. Detect external modifications (halt if found)
5. Report final results

**Interface:**
```bash
python code_fix_iteration.py \
    --findings .claude/findings/p2-full-review-2026-03-01.json \
    --terminal term_abc123 \
    --max-iterations 5 \
    --project-root P:/packages/handoff
```

### 4.3 Create `/code Fix all` Command Handler

**Location:** New file in `/code` skill or enhancement to existing

**Responsibilities:**
1. Parse findings JSON
2. Group findings by type/complexity
3. Create `/code` plan with all findings as tasks
4. Execute `/code` workflow (BOOTSTRAP → ALIGN → DESIGN → BUILD → TRACE → SHIP)
5. Return list of fixes applied

**Integration:** `/code` skill already supports full workflow, we just need to add "Fix all findings" mode.

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ User runs /p                                                    │
└────────────────┬────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ P2 Adversarial Review                                          │
│ - Generates findings JSON                                       │
│ - Writes to .claude/findings/p2-{hash}.json                   │
└────────────────┬────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ /p Phase 2 (Review) completes                                  │
│ - Displays findings count                                      │
│ - Shows "Action Required" section                               │
└────────────────┬────────────────────────────────────────────────┘
                 ↓
        User selects: /code Fix all (option 0)
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ code_fix_iteration.py (NEW)                                    │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Initialize:                                                 │  │
│ │ - Load findings JSON                                       │  │
│ │ - Compute SHA256 hash                                      │  │
│ │ - Create state file: code-fix-{terminal_id}.json          │  │
│ └───────────────────────────────────────────────────────────┘  │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Iteration Loop (repeat until clean or max_iterations):     │  │
│ │                                                           │  │
│ │ 1. SAFETY CHECK: Verify findings SHA256 unchanged        │  │
│ │ 2. SNAPSHOT: Record git commit + file mtimes             │  │
│ │ 3. FIX: Run /code workflow on all MEDIUM+ findings       │  │
│ │ 4. REVIEW: Re-run P2 adversarial review                  │  │
│ │ 5. VALIDATE: Check git commit unchanged                  │  │
│ │ 6. CHECK: Any MEDIUM+ findings remain?                   │  │
│ │    - YES: Continue to next iteration                     │  │
│ │    - NO: Exit with convergence achieved                  │  │
│ │                                                           │  │
│ │ Safety: If SHA256 or git commit changed → HALT           │  │
│ └───────────────────────────────────────────────────────────┘  │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Report:                                                    │  │
│ │ - Total iterations                                       │  │
│ │ - Total fixes applied                                    │  │
│ │ - Convergence status                                      │  │
│ │ - Final state file location                              │  │
│ └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ User sees final report                                         │
│ ✅ Convergence achieved after 3 iterations                    │
│ - 15 fixes applied                                            │
│ - 0 MEDIUM+ issues remaining                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

**Task 1.1:** Create iteration state schema
- File: `P:/.claude/skills/p/schemas/code_fix_state.schema.json`
- Define JSON schema for state file
- Add validation functions

**Task 1.2:** Create orchestrator script
- File: `P:/.claude/skills/p/scripts/code_fix_iteration.py`
- Implement iteration loop algorithm
- Add SHA256 hashing utilities
- Add git commit/file_mtime snapshot functions

**Task 1.3:** Add atomic file write utilities
- File: `P:/.claude/skills/p/lib/file_utils.py`
- Implement atomic write (write to temp, then rename)
- Prevents partial state files

### Phase 2: `/code` Integration (Week 2)

**Task 2.1:** Add "Fix all" mode to `/code` skill
- Parse findings JSON
- Convert findings to `/code` tasks
- Execute full workflow (BOOTSTRAP → SHIP)

**Task 2.2:** Create findings-to-tasks converter
- File: `P:/.claude/skills/code/lib/findings_to_tasks.py`
- Map finding types to task templates
- Handle dependencies between tasks

**Task 2.3:** Add progress reporting
- Emit iteration progress to user
- Show which findings are being fixed
- Report convergence status

### Phase 3: `/p` Integration (Week 2)

**Task 3.1:** Update `/p` SKILL.md
- Modify "Action Required" section
- Add `/code Fix all` as option 0
- Document iterative behavior

**Task 3.2:** Update `/p` phase 2 template
- File: `P:/.claude/skills/p/phases/p2.md`
- Add invocation of code_fix_iteration.py
- Pass findings file and terminal_id

**Task 3.3:** Add HALT conditions
- External modification detection
- Max iterations exceeded
- Report to user with next actions

### Phase 4: Testing & Validation (Week 3)

**Task 4.1:** Unit tests
- Test iteration loop logic
- Test SHA256 hash validation
- Test state file serialization

**Task 4.2:** Integration tests
- Test full pipeline with mock findings
- Test multi-terminal scenarios
- Test external modification detection

**Task 4.3:** End-to-end tests
- Run on real package with actual findings
- Verify convergence achieved
- Measure performance (iterations, time)

---

## 7. Trade-offs and Risks

### Trade-offs

| Decision | Pro | Con |
|----------|-----|-----|
| **Iterative P2 re-run** | Catches cascading issues | 3-5x longer runtime |
| **Terminal-scoped state** | No shared corruption | Can't resume across terminals |
| **No TTL (content-addressed)** | Always fresh data | Can't cache for speed |
| **Halt on external change** | Safe, predictable | Requires restart if concurrent |

### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Infinite loop** | Low | High | Max iterations = 5 |
| **External modification halt** | Medium | Low | Clear error message + restart instructions |
| **Performance (3-5x longer)** | High | Medium | Document expected runtime, show progress |
| **Multi-terminal confusion** | Low | Medium | Terminal-scoped state, clear IDs |
| **State file corruption** | Low | High | Atomic writes, SHA256 validation |

---

## 8. Success Criteria

**Functional Requirements:**
- ✅ `/code Fix all` option appears in `/p` next steps
- ✅ Iteration loop runs until 0 MEDIUM+ issues
- ✅ Detects external modifications and halts safely
- ✅ Multi-terminal safe (no shared state corruption)
- ✅ No TTL-based caching (content-addressed only)
- ✅ Always uses fresh data (re-computes findings)

**Non-Functional Requirements:**
- ✅ State file schema documented and validated
- ✅ Clear error messages for all failure modes
- ✅ Progress reporting during iteration
- ✅ Final report with iteration summary
- ✅ Recoverable from interruption (state file persists)

**Performance Requirements:**
- ✅ Max 5 iterations (prevent infinite loops)
- ✅ Expected 2-4 iterations for convergence
- ✅ Each iteration: 5-10 minutes (P2 + /code)
- ✅ Total runtime: 15-40 minutes (acceptable for "clean code" guarantee)

---

## 9. Open Questions

1. **Resume capability:** Should we support resuming interrupted iterations across terminals?
   - **Recommendation:** No - keeps it simple, user can restart in same terminal

2. **Parallel fixing:** Should we fix multiple findings in parallel?
   - **Recommendation:** Yes - `/code` already supports parallel tasks

3. **LOW severity issues:** Should we also iterate until LOW issues are fixed?
   - **Recommendation:** No - MEDIUM+ is sufficient for "production-ready"

4. **Max iterations timeout:** Should we add a time budget (e.g., max 1 hour)?
   - **Recommendation:** No - iteration count is sufficient guardrail

---

## 10. Recommendations

### Immediate Actions (Priority Order)

1. **Implement core infrastructure** (Phase 1)
   - Create state schema and orchestrator script
   - Add atomic file utilities

2. **Integrate with `/code`** (Phase 2)
   - Add "Fix all" mode to `/code` skill
   - Create findings-to-tasks converter

3. **Integrate with `/p`** (Phase 3)
   - Update SKILL.md next steps
   - Add invocation in phase 2 template

4. **Test thoroughly** (Phase 4)
   - Multi-terminal scenarios
   - External modification detection
   - Convergence achievement

### Long-term Considerations

1. **Metrics collection:** Track iteration patterns to optimize defaults
2. **Smart convergence:** Detect when fixes are stabilizing (fewer new issues)
3. **Selective re-review:** Only re-review changed components (faster P2)
4. **Cross-terminal resume:** Allow state transfer if needed

---

## Conclusion

**Recommendation:** Proceed with full implementation of `/code Fix all` iterative pipeline.

**Rationale:**
- Addresses core pain point (manual iteration)
- Guarantees convergence (no MEDIUM+ issues remain)
- Multi-terminal safe (terminal-scoped state)
- Fresh data guarantee (content-addressed, no TTL)
- Acceptable performance trade-off (3-5x longer for significantly better code)

**Next Step:** Begin Phase 1 implementation (core infrastructure).

---

**Document Status:** Ready for implementation planning
**Confidence Level:** HIGH (85%) - All constraints addressed, trade-offs evaluated
**Evidence Basis:** Analysis of `/p` and `/code` skills, multi-terminal state management best practices
