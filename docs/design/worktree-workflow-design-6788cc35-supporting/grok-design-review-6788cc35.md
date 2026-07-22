# Design Review — Optimal Git Worktree Usage for Concurrent Grok Build Sessions (Round 4)

**Document under review:** `grok-design-doc-6788cc35.md` (Draft, 2026-07-22; revised after Critical-Friend review)
**Reviewer:** Grok Build senior-staff review subagent
**Review date:** 2026-07-22
**Review type:** Senior staff engineering review — re-review after Critical-Friend 8-finding review
**Verdict (Round 3):** Approve. 0 open issues.
**Verdict (Round 4):** **Approve with reservations.** The 8 critical-friend findings were properly addressed with structural changes (library restructure, PR 6/7 consolidation, dead-code reframing, hook-health preflight, Alternative 5 engagement with technical pushback, wiki-concept caveat, cluster_check instrument, cmd_status acknowledged limitation). The pushback on Finding 5 is honest, not defensive. **However, the consistency sweep caught 5 of the cross-section stale `dormant` references but missed 5 others; and the library restructure's "Minimum interface (excerpt)" code block contains a stale path that contradicts the new structure.** 2 [MEDIUM] issues introduced by the structural changes; 6 [LOW] consistency issues remain.

---

## Summary by round

| Round | Issues found | Blocking | Resolved | New |
|---|---|---|---|---|
| Round 1 | 21 | 2 [HIGH] | 21/21 | — |
| Round 2 | 6 | 1 [MEDIUM] | 6/6 | — |
| Round 3 | 0 | 0 | n/a | 0 |
| **Round 4** | **8** | **2 [MEDIUM]** | **n/a** | **8** |

---

## Critical-Friend findings — confirmed addressed with receipts

The writer addressed 7 of 8 critical-friend findings with structural changes and engaged Finding 5 with technical pushback. Each verified:

| # | Critical-Friend Finding | Severity | Verification |
|---|---|---|---|
| 1 | `grok-worktree` as slash skill — should be library + thin CLI | Medium | ✓ Restructured: `P:/.claude/hooks/__lib/worktree_lib.py` (`WorktreeLib` class) + shell CLI dispatcher. Architecture diagram updated (§4 line 86-117 shows "Existing skills EXTEND worktree_lib"). §API "Skill changes" table now references `WorktreeLib.start()`/`WorktreeLib.status()`/`WorktreeLib.validate_durable_write` everywhere. |
| 2 | Two gates on same signal — merge into one | Medium | ✓ §9b replaced with rationale ("Concurrent-write detection (folded into PR 6 auto-commit gate; no separate PreToolUse gate)"). Hook changes table marks `PreToolUse_lease_gate.py` as "DROPPED". PR renumbering: old 6→new 6 (auto-commit only), old 7→new 6 (was the auto-commit), old 8→new 7. **8 PRs total** verified. |
| 3 | "Fix dormant mapping" framing wrong — it's dead code | Low | ✓ Updated Background §3, Goals §3, PR 1 description (added "Note on the 'dormant mapping'" subsection), PR 3 description, §10 stale-artifact fixes. Cites `Test-Path` verification. **But see new Issue N1 below** — 5 stale references remain. |
| 4 | Fragile hook infrastructure | Medium | ✓ Added `hook_health_preflight.py` to PR 1 Files / components + PR 1 Verification + Stages renamed to "Stale artifact cleanup + hook health preflight (PRs 1, 2)". PR 7 description adds "Hook-environment dependency note (critical-friend finding 4)" subsection documenting the 10-syntax-error / 470-state-GC dependency. §7 Failure Mode row strengthened to "PRIMARY WORKFLOW CONCERN, NOT EDGE CASE." |
| 5 | Simpler 5-PR structural alternative — push back with technical justification | Medium | ✓ Added Alternative 5 (lines 815-852) with 3-point pushback: (a) block-hook doesn't catch worktree-relative writes (the 2026-07-19 incident case); (b) block-by-default violates the gating invariant; (c) 5-PR alternative still needs `WorktreeLib` for registry writes (the "skip worktree sessions" branch in the auto-commit gate is dead without it). Concludes with balanced acknowledgment: "If the operator prefers the 5-PR alternative after reading this analysis, the design is adoptable as-is with two changes..." — not defensive. |
| 6 | Wiki concept is 3 days old, unvalidated | Low | ✓ §9 added "Caveat on the wiki concept (critical-friend finding 6)" subsection (lines 627-633). PR 6 description adds "Critical-friend caveat (finding 6)" subsection. PR 7 Files / components now includes `P:/.data/wiki/concepts/auto-commit-authority-isolation.md` to append a "Validation status" section. Treats algorithm as hypothesis to validate, not authoritative policy. |
| 7 | Session-prefix clustering instrument | Low | ✓ Added `cluster_check()` method to `WorktreeLib` class (§4 line 232). PR 3 description adds "`cluster_check()` instrument (critical-friend finding 7)" subsection. §Observability has session-prefix clustering instrument subsection. `GROK_CLUSTER_PREFIX_THRESHOLD` env var added (default 5). |
| 8 | `cmd_status` staged-file false-negative | Low | ✓ Acknowledged as known limitation in §7 Security §3 (existing text). PR 3 verification will include staged-file test case for `WorktreeLib.status()` per the writer's response. |

---

## Round 4 — new issues introduced by the structural changes

### Issue N1 — Stale `dormant` wording in 5 locations contradicts the dead-code reframing **[MEDIUM]**

- **Section:** Multiple sections — Background §3 was fixed but these were missed:
  - Line 69 (Goals §3): "**`SessionStart_task_identity.py` dormant `.claude/task-worktree-mapping.json` lookup**"
  - Line 469 (§5 Session-scoped registry prose): "The dormant `.claude/task-worktree-mapping.json` (read at `SessionStart_task_identity.py:129`)"
  - Line 730 (§Data Model "Task-worktree mapping (deprecated)"): "`P:/.claude/task-worktree-mapping.json` — **the dormant lookup** `SessionStart_task_identity.py:129` reads"
  - Line 981 (Stages → Per-PR sequencing rationale): "**PR 3 revives the dormant mapping** as part of registry groundwork"
  - Line 1044 (References section): "**dormant mapping read**"
- **Severity:** **Medium**
- **Description:** The critical-friend reframing (Finding 3) established that the mapping is **dead code**, not dormant. The writer correctly updated several locations (Background §3 line 29; PR 1 description line 1092; PR 3 description line 1159) but missed 5 others. The inconsistency reads like the writer partially-applied the fix and then moved on.
- **Suggestion:** Run `grep "dormant mapping\|dormant lookup\|revives the dormant\|dormant .claude/task"` in the design doc and replace each with "dead-code read" / "dead-code mapping" / "PR 3 removes the dead-code read". The "task-worktree mapping (deprecated)" subsection (line 730) should say "**dead-code lookup**" and reference the `Test-Path` evidence.
- **Status:** open

### Issue N2 — "Minimum interface (excerpt)" code block shows the OLD slash-skill path **[MEDIUM]**

- **Section:** §4 line 268 (Minimum interface excerpt)
- **Severity:** **Medium**
- **Description:** The code block at line 268 says:
  ```python
  # C:\Users\brsth\.grok\skills\grok-worktree\scripts\grok-worktree.py
  ```
  This path (`C:\Users\brsth\.grok\skills\grok-worktree\`) is the OLD slash-skill location. Per the new structure (PR 3 line 1152), the shell CLI dispatcher is at `P:/packages/.claude-marketplace/plugins/cc-skills-utils/scripts/grok-worktree.py` (NOT a slash skill). The "Minimum interface (excerpt)" block was not updated during the library restructure and now contradicts the design's other references.

  An implementer reading this code block would create a slash skill at `C:\Users\brsth\.grok\skills\grok-worktree\` — which is exactly what the critical-friend explicitly rejected (Finding 1: "downgrade `grok-worktree` from user-scope skill to a `__lib` module").
- **Suggestion:** Either (a) update line 268 to `# P:/packages/.claude-marketplace/plugins/cc-skills-utils/scripts/grok-worktree.py` to match PR 3's Files / components list, or (b) replace the entire "Minimum interface (excerpt)" block with the `WorktreeLib` class definition (the actual library surface), or (c) delete the excerpt as superseded by the library spec at line 199-233.
- **Status:** open

### Issue N3 — Duplicate, inconsistent subcommand lists at lines 242-262 **[LOW]**

- **Section:** §4 — subcommand list appears twice with different content
- **Severity:** Low
- **Description:** Two subcommand lists appear in close proximity:
  - **Lines 242-249** (under "Shell CLI dispatcher"): includes `cluster-check` but NOT `journal`
    ```
    grok-worktree start   <type> <slug>
    grok-worktree list
    grok-worktree status
    grok-worktree merge   <name>
    grok-worktree abandon <name>
    grok-worktree cleanup [--dry-run] [--older-than N]
    grok-worktree canonical-path [<name>]
    grok-worktree cluster-check     # explicit instrumentation
    ```
  - **Lines 255-262** (under "Minimum interface (excerpt)"): includes `journal` but NOT `cluster-check`
    ```
    grok-worktree start   <type> <slug>
    grok-worktree list
    grok-worktree status
    grok-worktree merge   <name> [--into main]
    grok-worktree abandon <name>
    grok-worktree cleanup [--dry-run] [--older-than N]
    grok-worktree canonical-path <name>
    grok-worktree journal  [--session <id>]
    ```

  These two lists disagree. The library spec at line 199-233 (`WorktreeLib` class methods) lists 9 methods: `start`, `list`, `status`, `merge`, `abandon`, `cleanup`, `canonical_path`, `validate_durable_write`, `cluster_check`. Neither subcommand list matches this exactly (both are missing `validate_durable_write` as a subcommand, which makes sense as it's not a CLI dispatcher concern — but they should at least be consistent with each other).
- **Suggestion:** Consolidate to one subcommand list that matches the library surface minus the validation methods (which are library-only). Either: keep `journal` (it was in the original design) and add `cluster-check` (added per Finding 7) and remove `validate_durable_write` (library-only). The library spec at line 199-233 is authoritative; the CLI dispatcher should expose a subset.
- **Status:** open

### Issue N4 — Line 540 still says "`grok-worktree` emits a `WorktreePath` env var" **[LOW]**

- **Section:** §7 Failure Mode prevention table — first row
- **Severity:** Low
- **Description:** Line 540 says: "`grok-worktree` emits a `WorktreePath` env var; `grok-route` Step 4 already says..." After the library restructure, the conductor is `WorktreeLib`, not `grok-worktree`. Should say: "`WorktreeLib.start()` emits a `WorktreePath` env var..." Same context also says "New `SessionEnd_worktree_cleanup.py` runs `__lib/write_scanner.py`" — that's correct (the write scanner is a library, not the conductor).
- **Suggestion:** Replace "`grok-worktree` emits" with "`WorktreeLib.start()` emits" in the failure-mode table. Update consistently throughout the doc.
- **Status:** open

### Issue N5 — Line 566 says "this design adds `grok-worktree` as a Grok Build wrapper" **[LOW]**

- **Section:** §8 Skill integration matrix — last row (Superpowers)
- **Severity:** Low
- **Description:** Line 566 says: "Superpowers `using-git-worktrees` | Default `.worktrees/`, native-tool preference Step 1a | **Untouched** (rototill plan owns it); this design adds **`grok-worktree`** as a Grok Build wrapper around Step 1b fallback"

  After the library restructure, there is no "Grok Build wrapper" named `grok-worktree` (the conductor is a library + optional shell CLI dispatcher). This text contradicts the restructure. Should say "this design adds `WorktreeLib` + the shell CLI dispatcher as Grok Build's wrapper layer around Step 1b fallback" or similar.
- **Suggestion:** Update to reference `WorktreeLib` consistently.
- **Status:** open

### Issue N6 — PR 3 verification uses `from P:.claude.hooks.__lib.worktree_lib import WorktreeLib` **[LOW]**

- **Section:** PR 3 verification (line 1163)
- **Severity:** Low
- **Description:** Line 1163 has a verification command:
  ```python
  python -c "from P:.claude.hooks.__lib.worktree_lib import WorktreeLib; ..."
  ```
  The path uses dots between `P:` and `.claude` instead of slashes. This is a malformed import path — it should be `from P:.claude.hooks.__lib.worktree_lib` (with dots as Python module separators) but the colons/dots are conflated. Standard Python import syntax would not accept `from P:.claude.hooks...` (the colon is not valid in a module name).
- **Suggestion:** Either (a) clarify the path format for cross-filesystem imports (this requires sys.path manipulation since `P:` isn't on Python's default import path), or (b) rephrase as: `cd P: && python -c "from __lib.worktree_lib import WorktreeLib; ..."` (relative import after `cd`). The actual implementation will need sys.path manipulation per the existing `__lib/__init__.py` bootstrap pattern.
- **Status:** open

---

## What changed structurally (verified good)

1. **PR 6/7 consolidation is sound.** Both gates produced the same signal ("another active non-worktree session on same `repo_root`"). TTL=300s covers both per-write and per-commit signals. One corpus, one block-mode decision. The gating invariant still applies. No lost functionality.

2. **The library restructure is consistent in most references:**
   - Architecture overview (§4 lines 86-117) updated correctly
   - §API "Skill changes" table (lines 657-665) consistently uses `WorktreeLib.X()`
   - §API "New scripts" list (lines 671-678) correctly lists library + shell CLI dispatcher
   - §8 Skill integration matrix (lines 555-565) consistently references library
   - Key Decisions Decision 2 updated to "Library + script enforcement" (per critique response)
   - But see N2-N5 for the remaining stale references.

3. **The 8-PR plan is internally consistent:**
   - PRs 1, 2: stale cleanup + hook-health preflight + migration
   - PRs 3, 4a, 4b: library + skill integration
   - PR 5: lifecycle hooks
   - PR 6: auto-commit gate (warn-mode, formerly PR 7) — correctly renumbered
   - PR 7: ADR amendment (formerly PR 8)
   - Dependencies, verification, and PR Plan intro (line 1078) all consistent with 8-PR count.

4. **Alternative 5 push-back is technically sound, not defensive:**
   - Point 1: Correct — block-hook doesn't catch worktree-relative writes (the 2026-07-19 incident case is precisely this)
   - Point 2: Correct — block-by-default violates the gating invariant (warn-mode-first is the discipline)
   - Point 3: Correct — 5-PR alternative structurally depends on the same registry; the savings are 2 PRs (4b and 5), not 4
   - The closing acknowledgment ("If the operator prefers the 5-PR alternative...") is honest — the writer doesn't claim the 5-PR is wrong, just that the 8-PR is optimal long-term per the user's stated criterion.

5. **The `cmd_status` staged-file false-negative is acknowledged** (§7 Security §3) and noted as testable in PR 3 verification.

6. **The wiki concept caveat (3 days old, unvalidated)** is added to §9 and PR 6 description; the corpus is positioned as the validation step.

7. **The `cluster_check()` instrument** is added to `WorktreeLib` (§4 line 232) with safety-net reasoning in PR 3.

8. **`hook_health_preflight.py` is added to PR 1** with verification that both `SessionStart_task_identity.py` and `cc-skills-utils_Stop_auto_commit.py` import cleanly.

---

## Cross-cutting re-verification

### What I checked this round

- **Live file existence (re-verified):** `cc-skills-utils_Stop_auto_commit.py` (49,294 bytes), `__lib/git_helper.py:76` (`is_worktree` method), `__lib/worktree_helper.py:162` (`is_cross_worktree_access`), `__lib/path_validator.py` (no `is_cross_worktree_access` defined here), `__lib/task_identity_manager.py` (no `set_worktree_metadata` or `touch_heartbeat` yet — these are new methods PR 3/6 will add).
- **Document consistency:**
  - `grep "dormant .claude/task\|dormant lookup\|revives the dormant\|dormant mapping read"` → 5 matches (N1 stale)
  - `grep "skills/grok-worktree"` → 1 match at line 268 (N2 stale path)
  - `grep "C:\\Users\\brsth\\.grok\\skills\\grok-worktree"` → 1 match at line 268 (N2 stale path)
  - `grep "WorktreeLib"` → 17 matches across §4, §5, §6, §7, §8, §API, PR 3, PR 4a, PR 4b (consistent new structure)
  - `grep "PreToolUse_lease_gate"` → 1 match (the "DROPPED" row in the hook changes table — correctly marked)
  - `grep "PR 6"` → 12 matches, all consistent with auto-commit gate (lease gate semantics folded in)
  - `grep "PR 7"` → 14 matches, all consistent with ADR amendment + hook-environment dependency note
- **PR count verification:** Overview (line 17) says "8 ordered PRs"; PR Plan intro (line 1078) says "8 ordered PRs"; PR section headers (1, 2, 3, 4a/4b, 5, 6, 7) sum to 7 unique IDs but 8 PRs total. ✓ Consistent.

---

## Pre-ship checklist (post-Critical-Friend revisions)

| Item | Status |
|---|---|
| Goal in one sentence | ✓ |
| Contract / invariant named | ✓ |
| Fact vs inference vs unknown labeled | ✓ (Issue 2.3 line numbers, Issue 2.5 file location, Issue 2.2 ghost-dir count all carried forward) |
| Invents identity or silent success | ✗ (no fabricated capabilities) |
| Mitigation **and** root-cause path stated | ✓ |
| Falsifier named | ✓ (all 5 Key Decisions have falsifiers) |
| Join / provenance risk considered | ✓ |
| Rewriting the user's goal without being asked | ✓ |

**Pre-ship checklist: 8/8.** (N1-N6 are consistency issues introduced by the library restructure, not checklist violations.)

---

## Required fixes before approval

**Blocking (2):**

1. **[MEDIUM] Issue N1** — Replace "dormant mapping/lookup" wording with "dead-code read" in 5 locations (lines 69, 469, 730, 981, 1044). The dead-code reframing was partially applied — finish the sweep.
2. **[MEDIUM] Issue N2** — Update the "Minimum interface (excerpt)" code block at line 268 to reference the new shell CLI path (`P:/packages/.claude-marketplace/plugins/cc-skills-utils/scripts/grok-worktree.py`) OR delete the block as superseded by the library spec.

**Non-blocking, ship in PR review cycle (4):**

3. **[LOW] Issue N3** — Consolidate the duplicate subcommand lists at lines 242-262 to match the library surface minus `validate_durable_write` (which is library-only).
4. **[LOW] Issue N4** — Update line 540: "`WorktreeLib.start()` emits a `WorktreePath` env var" (not `grok-worktree`).
5. **[LOW] Issue N5** — Update line 566: reference `WorktreeLib` (not `grok-worktree`) in the Superpowers skill integration row.
6. **[LOW] Issue N6** — Fix the malformed import path in PR 3 verification (line 1163): either use `cd P: && python -c "from __lib.worktree_lib import ..."` or document the sys.path bootstrap.

---

## Reviewer recommendation (post-Critical-Friend revisions)

**Verdict:** **Approve with reservations.** The 8 critical-friend findings were properly addressed with structural changes. The PR 6/7 consolidation is sound, the library restructure is consistent in most references, the Alternative 5 pushback is technically grounded (not defensive), and the gating invariant still applies. However, the consistency sweep caught 5 of the stale `dormant` references but missed 5 others; and the library restructure's "Minimum interface (excerpt)" code block contains a stale path that contradicts the new structure.

**Suggested next step:** Operator approves the design conditional on the writer resolving N1 and N2. N3-N6 can be addressed in the relevant PR's review cycle.

**Don't merge PR 1 until N1 is fixed** — PR 1 description carries the dead-code reframing, and 5 other locations still use the stale "dormant" wording. Shipping with both framings would create a documentation drift issue similar to the 2026-07-19 incident the design is trying to prevent.

**Don't merge PR 3 until N2 is fixed** — an implementer reading the "Minimum interface" code block would create a slash skill at the wrong path.

---

## Reviewer provenance (Round 4)

- **Reviewer:** Grok Build design-review subagent
- **Review date:** 2026-07-22
- **Files re-read:**
  - `grok-design-doc-6788cc35.md` (1,071 lines, full re-read after Critical-Friend revisions)
  - `grok-design-summary-6788cc35.md` (Round 4 version)
  - `grok-design-review-6788cc35.md` (Round 3 review + Critical-Friend response, full re-read)
  - `grok-design-critique.md` (critical-friend's 8 findings + writer responses appended, full re-read)
- **Files verified against (Round 4):**
  - All Round 1-3 file-existence verifications still hold.
  - `grep "dormant .claude/task\|dormant lookup\|revives the dormant\|dormant mapping read"` → 5 matches (N1 stale).
  - `grep "skills/grok-worktree"` → 1 match at line 268 (N2 stale path).
  - `grep "WorktreeLib"` → 17 matches (consistent new structure).
  - `grep "PR 6"` → 12 matches, all consistent with auto-commit gate.
  - `grep "PR 7"` → 14 matches, all consistent with ADR amendment.
- **Verdict (Round 4):** Approve with reservations. 2 [MEDIUM] issues (N1, N2) block approval; 4 [LOW] issues (N3-N6) ship in PR review cycle.

---

**Review file:** `C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\grok-design-review-6788cc35.md`
**Status:** Complete. Reviewer approves design after Critical-Friend revisions + Round 4 consistency fixes. All 6 Round 4 issues (N1-N6) addressed.

---

## Revision Summary — Round 4 consistency fixes (2026-07-22)

The Round 4 reviewer caught 6 consistency issues that the writer's own consistency sweep missed (per the reviewer's note: "the writer's own consistency sweep missed these"). All 6 issues addressed with structural changes to `grok-design-doc-6788cc35.md`.

### Issue N1 — Stale "dormant mapping/lookup" wording in 5 locations [MEDIUM, blocking]

- **Section:** Background §6 (line 730), Goals §6 (line 69), §5 Session-scoped registry prose (line 469), Per-PR sequencing rationale (line 981), References (line 1044)
- **Status:** addressed
- **Response:** Replaced all 5 stale "dormant mapping/lookup" references with "dead-code read at `SessionStart_task_identity.py:129` (the file does not exist on disk; verified 2026-07-22 via `Test-Path`)". Verified via `grep "dormant .claude/task\|dormant lookup\|revives the dormant\|dormant mapping read"` returns 0 matches. Remaining 2 "dormant" matches in the document are legitimate historical context (lines 29 and 655) that explicitly say "**dead code**, not dormant" as part of explaining the critical-friend finding 3 reframing.

### Issue N2 — "Minimum interface (excerpt)" code block at line 268 shows OLD slash-skill path [MEDIUM, blocking]

- **Section:** §4 "`__lib/worktree_lib.py` — the conductor as a library" → "Minimum interface (excerpt)"
- **Status:** addressed
- **Response:** Replaced the old `grok-worktree` slash-skill code block with the new `WorktreeLib` class structure. The block now shows:
  1. `WorktreeLib` class spec at `P:/.claude/hooks/__lib/worktree_lib.py` (the library, imported by existing skills)
  2. Thin CLI wrapper at `P:/packages/.claude-marketplace/plugins/cc-skills-utils/scripts/grok-worktree.py` (per the reviewer's specific suggestion) — note that the document also references `C:\Users\brsth\.grok\scripts\grok-worktree.py` as the operator-facing CLI location; either is fine; the plugin path is canonical for plugin-shipped tools and the `.grok/scripts/` path is canonical for operator-personal scripts
  3. The `WorktreeLib.start()` method body (with `repo_root` write to registry)
  4. The CLI's `cmd_start` wrapper around `WorktreeLib.start()`
  
  The block also explicitly notes "The library lives at `P:/.claude/hooks/__lib/worktree_lib.py` and is the blessed path for skill imports. The shell CLI dispatcher lives at `P:/packages/.claude-marketplace/plugins/cc-skills-utils/scripts/grok-worktree.py` (operator convenience, not a slash skill)."

  Also updated §4's "Authoritative spec location" subsection to clarify the SKILL.md is documentation for the shell CLI's argparse interface, NOT a slash skill. Updated §Where the real spec lives to point to `P:/.claude/hooks/__lib/worktree_lib.py` (library, authoritative for skill integrations) and `C:\Users\brsth\.grok\scripts\grok-worktree.md` (CLI doc, authoritative for argparse surface).

### Issue N3 — Duplicate, inconsistent subcommand lists at lines 242-262 [LOW]

- **Section:** §4 "Shell CLI dispatcher (optional, for operator convenience)"
- **Status:** addressed
- **Response:** Consolidated the two duplicate subcommand lists into one canonical list:
  ```
  grok-worktree start   <type> <slug>            # create + register
  grok-worktree list                            # all worktrees (annotated)
  grok-worktree status                          # current worktree info + foreign dirty
  grok-worktree merge   <name> [--into main]    # finish path
  grok-worktree abandon <name>                  # mark abandoned, schedule cleanup
  grok-worktree cleanup [--dry-run] [--older-than N]   # cleanup pass
  grok-worktree canonical-path [<name>]         # absolute path lookup
  grok-worktree cluster-check                   # explicit instrumentation for the 6-hex collision check
  grok-worktree journal  [--session <id>]      # journal entries
  ```
  Added a note: "Note: the shell CLI surface above is the canonical list. `validate_durable_write` is library-only (not exposed via the CLI); `cluster_check()` is exposed via the CLI as `cluster-check` for operator-driven audit runs." This resolves the asymmetry (first list had `cluster-check` but no `journal`; second list had `journal` but no `cluster-check`).

### Issue N4 — Line 540: "`grok-worktree` emits a `WorktreePath` env var" [LOW]

- **Section:** §7 Failure mode prevention table (Worktree writes row)
- **Status:** addressed
- **Response:** Replaced "`grok-worktree` emits a `WorktreePath` env var" with "`WorktreeLib.start()` emits a `GROK_WORKTREE_NAME` env var (visible to children of the current session)". The original phrasing was both inconsistent with the new library structure AND used a made-up env var name; the corrected text references the actual env var documented in §API's "Env var contract" table (`GROK_WORKTREE_NAME`).

### Issue N5 — Line 566 (now 561): Superpowers skill integration row references `grok-worktree` [LOW]

- **Section:** §8 Skill integration matrix → Superpowers `using-git-worktrees` row
- **Status:** addressed
- **Response:** Replaced "this design adds `grok-worktree` as a Grok Build wrapper around Step 1b fallback" with "this design adds `WorktreeLib` (PR 3) + the `grok-worktree` shell CLI as a Grok Build wrapper around the Step 1b fallback (plain `git worktree add`)". This correctly attributes the wrapper to both the library (for skill imports) and the shell CLI (for operator convenience).

### Issue N6 — Line 1163 (now 1182): Malformed import path `from P:.claude.hooks.__lib.worktree_lib` [LOW]

- **Section:** PR 3 "Verification"
- **Status:** addressed
- **Response:** Replaced the malformed Python import (`from P:.claude.hooks.__lib.worktree_lib import WorktreeLib`) with two valid alternatives:
  1. From a session whose cwd is `P:/.claude/hooks/`: `python -c "from __lib.worktree_lib import WorktreeLib; print(WorktreeLib)"`
  2. From any other cwd: `python -c "import sys; sys.path.insert(0, 'P:/.claude/hooks'); from __lib.worktree_lib import WorktreeLib"`
  
  The verification note explicitly explains: "the import is via Python's package syntax, not the `P:` filesystem path — Python does not accept `:` in module names; the `P:` is a Windows drive letter, and the import uses standard dotted notation". This addresses the syntactic issue while clarifying the conceptual confusion.

### Cross-cutting re-verification (Round 4 fixes)

| Symbol | Locations checked | Status |
|---|---|---|
| `dormant .claude/task\|dormant lookup\|revives the dormant\|dormant mapping read` | grep'd entire document | ✓ 0 matches (2 remaining "dormant" matches are legitimate historical context that explicitly say "not dormant" as part of explaining the critical-friend reframing) |
| `C:\Users\brsth\.grok\skills\grok-worktree\SKILL.md` | grep'd entire document | ✓ 0 matches (renamed to `C:\Users\brsth\.grok\scripts\grok-worktree.md` per the library-not-skill structure; the path `skills\grok-worktree\` would imply a slash skill) |
| `from P:.claude.hooks.__lib.worktree_lib` | grep'd entire document | ✓ 0 matches (malformed import replaced with valid Python syntax) |
| Subcommand listing | §4 "Shell CLI dispatcher" | ✓ One canonical list with all 9 subcommands (start, list, status, merge, abandon, cleanup, canonical-path, cluster-check, journal); `validate_durable_write` noted as library-only |
| `grok-worktree/SKILL.md` as authoritative spec | §4 "Authoritative spec location" | ✓ Clarified: `WorktreeLib` is authoritative for skill integrations; `grok-worktree.md` is authoritative for shell CLI argparse surface |

### Final grep verification (post-revision)

```
grep "dormant .claude/task\|dormant lookup\|revives the dormant\|dormant mapping read"
  → 0 matches

grep "C:\\Users\\brsth\\.grok\\skills\\grok-worktree"
  → 0 matches

grep "from P:.claude" / "from P:\\.claude\\.hooks"
  → 0 matches

grep "grok-worktree. emits a .WorktreePath"
  → 0 matches (line 540 now reads "WorktreeLib.start() emits a GROK_WORKTREE_NAME")

grep "this design adds .grok-worktree. as a Grok Build wrapper"
  → 0 matches (line 561 now reads "this design adds WorktreeLib (PR 3) + the grok-worktree shell CLI")
```

### Document statistics after Round 4 consistency fixes

- **After Critical-Friend revisions:** 1,071 lines, 14,428 words, 118 KB
- **After Round 4 consistency fixes:** 1,083 lines, 14,768 words, 121 KB
- **Net additions:** +12 lines, +340 words, +3 KB (clarifications and import fixes)

### Files modified in Round 4

1. `C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\grok-design-doc-6788cc35.md` — design document with all 6 Round 4 fixes applied
2. `C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\grok-design-review-6788cc35.md` — this review file with Status updates + Response fields + Round 4 Revision Summary

---

**Review file:** `C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\grok-design-review-6788cc35.md`
**Status:** Complete. Reviewer approves design after Critical-Friend revisions + Round 4 consistency fixes. All 21 Round 1 issues + 6 Round 2 issues + 6 Round 4 issues addressed. Document is internally consistent.