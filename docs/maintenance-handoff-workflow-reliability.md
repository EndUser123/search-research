# Maintenance Handoff — Claude Code Workflow Reliability Hardening

**Generated:** 2026-07-14
**Repository:** `P:\`
**Branch:** `main` (HEAD `7d8e103`)
**Workstream:** Workflow reliability — authority, enforcement, self-documentation, hook hygiene

---

## EXECUTIVE_SUMMARY

Six items completed across the `P:\` repository's Claude Code workflow system:

1. Worktree authority consolidation
2. `/go` entrypoint authority clarification
3. Claude Code tool-selection policy
4. Task self-documentation lifecycle hardening
5. UserPromptSubmit timeout ownership
6. Stale migrated hook cleanup

All changes are narrow, evidence-first, and preserve existing architecture. No telemetry added, no hooks redesigned, no safety mechanisms removed.

---

## CURRENT_STATE

### Workflow Architecture

- **`/go` orchestrator** (`cc-skills-sdlc/skills/go/scripts/orchestrate.py`) is the canonical runtime. It stays on `main` throughout; workers execute in feature worktrees.
- **Pi dispatch** (default). Claude code subagent dispatch via two-phase spawn (`SPAWN_CLAUDE_SUBAGENT` token → `Agent(...)` → `--claude-resume`).
- **Deterministic continuation gate** drives task-completion, not native `/goal` evaluator.

### Canonical Authorities

| Authority | Location | Scope |
|-----------|----------|-------|
| Worktree creation | `cc-skills-sdlc/skills/go/scripts/worktree_safety.py` | Concurrent agent isolation |
| Entrypoint | `orchestrate.py` | Singular `/go` runtime |
| Tool selection | `.claude/CLAUDE.md` (line 51) + cc-skills-sdlc policy | Claude Code only |
| Task self-doc enforcement | `PreToolUse_task_self_doc_gate.py` | TaskCreate + TaskUpdate |
| Task completion gate | `Stop_task_completion_gate.py` (cc-aca-sdlc plugin) | Stop event, strict require_all |
| Cited content guard | `Stop.py:_run_cited_content_guard()` + `StopHook_cited_content_guard.py` | Stop event |

### Ownership Boundaries

- **Local hooks** (`P:/.claude/hooks/`) — PreToolUse, Stop, UserPromptSubmit routers. Plugin hooks cascade after via settings.json.
- **Plugin hooks** — Each cc-aca-* plugin has `__lib/router.py` dispatching to its own `hooks/{event}/` directory.
- **stop/hooks/ cited_content_guard** — The active implementation is the local `StopHook_cited_content_guard.py` imported by `Stop.py:1092`. The stale plugin copy has been removed.

### Where Enforcement Lives

1. **Self-documentation gate** — `PreToolUse_task_self_doc_gate.py` (PreToolUse, blocks TaskCreate/TaskUpdate)
2. **Completion gate** — `Stop_task_completion_gate.py` (Stop, blocks completing undocumented tasks)
3. **Cited content guard** — `StopHook_cited_content_guard.py` (Stop, detects fabricated code citations)
4. **Delegation enforcement** — `go_delegation_enforce_PreToolUse.py` (PreToolUse, blocks out-of-scope mutations)
5. **Continuation gate** — `go_continuation_gate.py` (Stop[3], deterministic state-based task completion)
6. **Evidence gates** — Various epistemic Stop hooks in cc-aca-epistemic plugin

---

## COMPLETED_WORK

### 1. Worktree authority

```text
Problem: Worktree creation and management responsibilities were scattered. Multiple
         paths could create worktrees without coordinated ownership, risking conflicts
         and stale orphan worktrees.

Root cause: No single resolver for worktree lifecycle. Creation logic and cleanup
            logic interleaved, making it unclear who owned each phase.

Decision: Implement canonical worktree resolver. Separate creation from management.
          Existing worktrees preserved. `/go` SKILL.md STEP 0 codifies the single
          worktree provisioning path.

Files changed: cc-skills-sdlc scripts (worktree_safety.py, SKILL.md STEP 0)

Evidence: `/go` now uses a single provisioning path: git worktree add on main for
          pi dispatch, current checkout for local, two-phase spawn for claude.

Why this design was chosen: Isolated worktrees prevent concurrent agent collisions.
          A single creator (worktree_safety.py) means one source of truth for
          worktree state. Separate management (status/precheck/cleanup) avoids
          accidental deletion of active work.
```

### 2. Entrypoint authority

```text
Problem: Multiple wrappers and helpers existed alongside orchestrate.py, creating
         ambiguity about which entrypoint was authoritative for `/go`.

Root cause: Organic growth added alternative invocation paths without retiring old
            ones.

Decision: `orchestrate.py` is the canonical `/go` runtime. Wrappers/helpers are
          classified (not deleted). No broad deletion performed — the goal was
          clarity, not reorganization.

Files changed: None structurally — classification done in SKILL.md documentation.

Evidence: The `/go` SKILL.md names orchestrate.py as the orchestrator. All
          dispatch modes (pi, local, claude) route through it.

Why this design was chosen: A single entrypoint avoids the "multiple doors"
          problem where different callers get different behavior. Wrappers are
          kept but explicitly not authoritative — the contract lives at
          orchestrate.py.
```

### 3. Tool-selection policy

```text
Problem: Claude Code had no explicit policy about which tools to prefer for
         common operations (Read vs Bash, Grep vs grep), leading to inconsistent
         evidence-gathering patterns.

Root cause: No codified preference.

Decision: Add concise tool-selection policy to `.claude/CLAUDE.md` and a detailed
          policy to cc-skills-sdlc. Scope includes only Claude Code.

Files changed: `.claude/CLAUDE.md` (line 51: "Tool Selection" section)

Evidence: CLAUDE.md now states tool preferences (Prefer Read/Edit/Write/Glob/Grep
          over Bash for file operations).

Why this design was chosen: Bash for file operations is slower, less precise, and
          harder to permission-gate. Read/Edit/Write/Glob/Grep are dedicated tools
          with better integration. The cc-skills-sdlc policy extends this for the
          `/go` workflow specifically.
```

### 4. Task self-documentation lifecycle

```text
Problem: TaskUpdate completion validation used require_all=True (Problem +
         Situation + Symptom), treating a status update like completion evidence.
         This caused false blocks on legitimate updates like "Fixed token
         validation; invalid tokens now return 401."

Root cause: The self-documentation gate used the same strict check for all three
            lifecycle stages (create, update, complete).

Decision:
  - TaskCreate: require_problem=True, require_all=False
    (Problem mandatory + at least one of Situation/Symptom)
  - TaskUpdate completion: require_problem=True, require_all=False
    (same — "what was accomplished?")
  - Non-completion TaskUpdate: no validation (status != completed)
  - Stop completion gate: remain require_all=True (strict)
    "Why is this complete?" needs full evidence.

  Lifecycle model:
    TaskCreate: "What problem are we solving?"
    TaskUpdate: "What changed?"
    Completion: "Why is this complete?"

Files changed:
  - .claude/hooks/PreToolUse_task_self_doc_gate.py (TaskUpdate path — was already
    require_all=False, require_problem=True in working tree)
  - .claude/hooks/tests/test_task_self_doc_gate.py (+6 new edge-case tests)

Evidence:
  - PreToolUse_task_self_doc_gate.py:86-90:
    self_documentation_check("TaskUpdate completion", description,
        require_all=False, require_problem=True)
  - Stop_task_completion_gate.py:210: self_documentation_check(subject, description)
    (default require_all=True — strict)
  - 6 new tests passing covering:
    PASS: empty update, symptom-only update, situation-only update,
          problem-only update (all fail as expected)
    PASS: problem+situation update (passes)
    PASS: full lifecycle test (TaskCreate pass, TaskUpdate pass, non-completion
          skip, insufficient evidence fail)

Why this design was chosen: Different lifecycle stages ask different questions.
          TaskCreate needs "what problem?" not "what symptom?" TaskUpdate
          completion needs "what was accomplished?" (Problem + context) not
          the full Situation+Symptom detail that a post-mortem would provide.
          Final completion (Stop gate) remains strict because it proves the
          work is done, including observing and verifying the observable
          outcome.
```

### 5. UserPromptSubmit timeout fix

```text
Problem: "UserPromptSubmit hook timed out after 5s — output discarded" observed
         in fresh terminal. The log_hook.py entry had no explicit timeout,
         relying on Claude Code's 5s default. Under file contention (Windows
         lock retry ~3.75s worst case) + transcript I/O, this could be exceeded.

Root cause: log_hook.py entries in settings.json lacked a "timeout" field.
            Claude Code defaults to 5s for command hooks without explicit timeout.
            Five separate hook events (UserPromptSubmit, PreToolUse, PostToolUse,
            Stop, Notification) each had a log_hook.py entry, and only the
            UserPromptSubmit one was initially fixed.

Decision: All 5 log_hook.py entries get explicit "timeout": 15. This matches
          the broader hook timeout pattern (10-20s range used by other hooks)
          and gives ample headroom above the ~3.75s worst-case lock retry.

Files changed:
  - .claude/settings.json (5 entries updated: UserPromptSubmit, PreToolUse,
    PostToolUse, Stop, Notification)

Evidence:
  - All 5 entries now show timeout=15 in settings.json validation output.
  - JSON parsed and confirmed valid.
  - Prior state: log_hook derived implicit 5s default. UserPromptSubmit[0]
    (HookImporter) had 15s; log_hook[2] had none.

Why this design was chosen: Each hook should declare its own timeout, not rely
          on Claude Code's implicit default. The 5s default was adequate for
          most hooks but log_hook's lock-retry + I/O pattern needed more
          headroom. 15s matches the existing HookImporter entry and is
          consistent with the 10-20s range used by other registered hooks.
          The fix makes timeout ownership explicit rather than implicit.
```

### 6. Stale migrated hook cleanup

```text
Problem: cc-aca-epistemic plugin contained a stale copy of
         StopHook_cited_content_guard.py (352 lines, identical to local copy).
         The active implementation lives at P:/.claude/hooks/StopHook_cited_content_guard.py,
         imported by Stop.py:1092 as _run_cited_content_guard().

Root cause: When the cited content guard was migrated from plugin to local hooks,
           the plugin's copy was never removed.

Decision: Delete plugin copy. Update plugin CLAUDE.md to remove stale reference.
          Bump plugin version (0.2.86 → 0.2.88) and rebuild cache.

Files changed:
  - DELETED: packages/...cc-aca-epistemic/hooks/stop/StopHook_cited_content_guard.py
  - packages/...cc-aca-epistemic/CLAUDE.md (removed stale hook row)
  - packages/...cc-aca-epistemic/.claude-plugin/plugin.json (0.2.86 → 0.2.88)

Evidence:
  - Plugin hooks.json: empty {} — no dispatch to stop hooks.
  - Plugin __lib/router.py: dispatches only PreToolUse + PostToolUse — no Stop path.
  - Plugin __lib/compat_loader.py: name only as doc comment for resolution pattern,
    not a live import.
  - Plugin tests: 0 references to cited_content_guard.
  - Active local copy: P:/.claude/hooks/StopHook_cited_content_guard.py (352 lines).
  - Tests: 28/28 passing against local copy.
  - Cache rebuilt: zero drift, stale caches (0.2.86, 0.2.87) removed.

Why this design was chosen: The plugin copy was dead code — unconsumed by any
          plugin mechanism. Keeping it would cause confusion about ownership
          and appear in artifact scans as a stale reference. The active
          implementation belongs in local hooks because it imports from
          local __lib (evidence_scope, turn-scoped events) and is called
          directly by Stop.py.
```

---

## VERIFICATION

### PROVEN_EVIDENCE

| Item | Evidence | How Verified |
|------|----------|-------------|
| TaskCreate validation | `require_problem=True` enforced | Test suite: test_require_problem_* (6 cases passing) |
| TaskUpdate completion | `require_all=False, require_problem=True` | Read source at PreToolUse_task_self_doc_gate.py:86-90 |
| TaskUpdate edge-case FAIL | empty, symptom-only, situation-only all fail | 3 new tests pass |
| TaskUpdate PASS | problem+situation, problem+symptom pass | 2 new tests pass |
| Non-completion TaskUpdate | no validation required | Existing test passes |
| Stop completion gate strict | `require_all=True` (default) | Read source at Stop_task_completion_gate.py:210 |
| All 5 log_hook timeouts=15 | settings.json validated | JSON parse + grep confirmed |
| Active cited content guard | `StopHook_cited_content_guard.py` at local hooks | File exists, 352 lines, 28 tests pass |
| Stale file deleted | Plugin copy absent | `ls` returns "No such file" |
| Plugin cache rebuilt | Version 0.2.88 in cache | `ls ~/.claude/plugins/cache/local/cc-aca-epistemic/` |
| Zero drift after cache rebuild | audit script confirmed | "Zero drift confirmed for cc-aca-epistemic" |

### INFERRED_CONTEXT

| Claim | Basis | Confidence |
|-------|-------|------------|
| 5s default timeout for unset hooks | Claude Code documentation | High — consistent with observed behavior |
| log_hook lock-retry exceeds 5s on contention | Lock retry algorithm: ~3.75s worst case + I/O overhead | Medium — depends on file contention severity |
| Plugin copy was never consumed | Empty hooks.json, no router dispatch, no imports | High — verified by grep across plugin tree |
| PreToolUse_task_self_doc_gate fix works at runtime | 51 unit tests pass covering all paths | High — direct testing |

### UNKNOWN_AREAS

| Area | Why Unknown | Impact |
|------|-------------|--------|
| Actual runtime duration of log_hook.py under real contention | Not measured — would require instrumented monitoring | Low — 15s timeout gives 3x+ headroom |
| Whether the 5s timeout was the only failure or a rare event | Not reproduced under measurement | Low — fixed regardless |
| Complete set of hooks without explicit timeout | Only log_hook.py entries checked | Low — other hooks have explicit timeouts visible in settings.json |

---

## DEFERRED_ITEMS

### Diagnostics identity

**Known issue:** Subprocess hook names and in-process gate names do not always map one-to-one. A `hooks.json` entry may register `PreToolUse.py` which internally dispatches to 20+ sub-hooks via `HookImporter`, and a failing sub-hook appears as `PreToolUse` in diagnostics. Similarly, `Stop.py` aggregates 15+ gates but surfaces under the single name `Stop`.

**Why not changed:** The identity gap is in Claude Code's hook infrastructure, not in any single gate. Fixing it would require a cross-cutting change to the hook dispatch/diagnostics layer. The handoff workstream's scope was narrow reliability fixes, not infrastructure redesign.

**Evidence that would justify revisiting:** A consistent pattern of misattributed hook failures in diagnostics logs where the wrong hook is blamed for a timeout or error, leading to wasted debugging effort.

---

### behavior_contract

**Known observation:** Advisory behavior_contract evaluations exist with zero blocks. The mechanism is wired and fires during UserPromptSubmit but never produces a blocking decision.

**Why not changed:** The mechanism was not part of this workstream's scope. Zero blocks suggests either it is too permissive, too narrowly scoped, or correctly calibrated. Without measuring activation rate vs. missed violations, we cannot judge. The mechanism's existence provides an extensibility point without imposing runtime cost (zero blocks = zero friction).

**Evidence that would justify revisiting:** Either (a) a real behavior violation that the contract should have caught but didn't, or (b) a corpus showing the contract fires too rarely to be useful.

---

### Policy/documentation density

**Known area:** `AGENTS.md` and `.claude/CLAUDE.md` are large files. `CLAUDE.md` in particular contains detailed hook protocols, safety rules, and implementation principles that some engineers find overwhelming.

**Why restructuring was deferred:** No evidence that density causes real (as opposed to theoretical) friction. The sections are independently skimmable. Restructuring a globally-referenced file risks breaking hooks/agents/tools that parse it for specific sections.

**Evidence that should trigger change:** A measured pattern of engineers missing or misapplying rules that are present in the file but hard to find (not "this file is too long" but "I didn't know rule X existed").

---

### Semantic task validation

**Known future direction:** Current self-documentation validation uses keyword/pattern matching:
- Problem indicators: `\bfix\b`, `\bbug\b`, `\berror\b`, etc.
- Situation indicators: `\bwhen\b`, `\bduring\b`, `\bwhile\b`, etc.
- Symptom indicators: `\bshows\b`, `\breturns\b`, `\bthrows\b`, etc.

**Current boundary:** The keyword approach is deliberately simple and deterministic. It catches the most common failures (empty descriptions, single-word summaries) while being predictable. False positives are possible but rare in practice. The tests prove it discriminates between "Fixed token validation" (pass) and "Fixed the crash" (fail, no situation/symptom).

**When semantic validation would be justified:** If a corpus review shows keyword-based validation has significant blind spots — descriptions that clearly describe a problem but use synonyms not in the indicator lists, or that pass keyword checks without conveying actual intent. At that point, a small embedding classifier or LLM-as-judge approach could supplement (not replace) the keyword gate, but it must first demonstrate reliable TP/FP on real data.

---

## DO_NOT_REOPEN

The following decisions should not be revisited without new evidence.

1. **Do not make TaskUpdate require full Problem+Situation+Symptom.** The lifecycle boundary is correct: TaskUpdate asks "what changed?" not "why is this complete?" Reverting to `require_all=True` would re-introduce false blocks on legitimate updates.

2. **Do not weaken the Stop completion gate.** The Stop gate correctly uses `require_all=True` because it validates "why is this complete?" — a post-mortem that needs evidence of problem, context, and observable outcome. This is the strict boundary.

3. **Do not consolidate self-doc validator into a single less-strict path.** Having three tiers (TaskCreate, TaskUpdate, Stop completion) with different strictness levels is intentional. Each lifecycle stage has a different question; one size does not fit all.

4. **Do not increase hook timeouts without identifying ownership.** Every hook should declare its own timeout. The prior approach of relying on Claude Code's default 5s made timeout attribution impossible — was it the hook or the default? Explicit ownership per entry is the fix.

5. **Do not delete the local StopHook_cited_content_guard.py.** It is the active implementation. The plugin copy was the stale one, not the local copy. Stop.py:1092 imports from the local path.

6. **Do not consolidate mechanisms solely because they are numerous.** The workflow system has many small gates and hooks by design — each has a narrow, specific responsibility. Consolidation for aesthetic reasons introduces coupling and single points of failure.

7. **Do not remove safety gates based only on low activation counts.** A gate that fires rarely may still be catching the most expensive failures. Zero blocks ≠ zero value. Evaluate by cost-of-miss, not by activation rate.

8. **Do not change authority ownership without consumer evidence.** If a hook or module's writer/reader set has not been traced, any ownership change risks creating orphaned writes or unmapped reads.

---

## NEXT_RECOMMENDED_AUDIT

### Measure hook latency trends

The highest-value next investigation is measuring real-world hook latency.

**Why:** The timeout fix was reactive — a symptom was observed, a timeout was added. Without latency data, we cannot predict which hook will next approach its timeout ceiling, or whether a 15s timeout is appropriate for log_hook under typical conditions.

**What to measure:**
- Per-hook wall-clock time over N sessions (N ≥ 100 is ideal)
- Per-hook timeout count (how often does each approach its limit?)
- Identify slowest p50/p95/p99 hooks

**How:**
- Extend existing diagnostic infrastructure (diagnostics.db / hook_importer_errors.jsonl) with timing telemetry (start_time, end_time per hook execution).
- Export to a structured artifact (e.g., `hook-latency-report_{timestamp}.json`).
- Compare against each hook's declared timeout.

**Scope boundary:** Measure only. Do not change any timeout without per-hook latency evidence. Do not add a cross-cutting telemetry framework — this is a one-off audit, not new infrastructure.

---

## FINAL_STATUS:
COMPLETE_HANDOFF
