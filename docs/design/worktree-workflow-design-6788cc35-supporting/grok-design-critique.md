# Critical-Friend Review — `grok-design-6788cc35`

**Reviewer:** critical-friend subagent (premise critique, not code review)
**Target:** `grok-design-doc-6788cc35.md` (Optimal Git Worktree Usage for Concurrent Grok Build Sessions)
**Reviewer's role:** challenge the premises, not the implementation. The correctness reviewer signed off in Round 3; the writer says "Approved after revision + sweep." A different lens is needed.

> **Verification receipts used in this critique**
>
> - `git -C P: worktree list` (2026-07-22) — confirmed 10 active worktrees at three roots with one locked
> - `git -C P: status -s` (2026-07-22) — confirmed `main` is dirty with 18 modifications and 30+ deletions under `.data/wiki/sources/skills/`
> - `Test-Path` checks (2026-07-22) — `grok-worktree` skill does NOT exist (new); `grok-parallel`, `grok-safe-git`, `handoff`, `grok-route` DO exist; `task-worktree-mapping.json` does NOT exist (the read is already a no-op); `session_registry.jsonl`, `worktree_root_policy_PreToolUse.py`, `__lib/worktree_helper.py`, `cc-skills-utils_Stop_auto_commit.py` all exist
> - `python P:/.claude/scripts/hooks_audit.py` (2026-07-22) — scanned 1,151 hook files; flagged 10 SYNTAX errors and 470 state-GC items older than 30 days
> - `grep -rn "_other_session_active" P:/.claude/hooks/__lib` — zero matches (PR 7's helper does not yet exist anywhere)
> - `grep "repo_root" P:/.claude/.artifacts/session_registry.jsonl` — zero matches (the new schema field is genuinely additive, not a rename)
> - `read_file P:/.data/wiki/concepts/auto-commit-authority-isolation.md` lines 1–60 (2026-07-22) — the wiki concept the design relies on already contains essentially the same `_other_session_active()` algorithm the design re-presents in §9

---

## Selected critique domains

**Core (always):** Problem Framing · Optimal Long-Term vs Simplicity · Falsifiability · Anchoring

**Context-derived (selected):** Migration / Rollback · Concurrency / Multi-Terminal · Provenance / Identity · Security · User Workflow Fit · Observed-vs-Invented

**Open-ended domains raised:** Operator Cognitive Load · Skill Sprawl · Deferral Discipline · Alternative-the-design-missed

---

## Part 1 — Core-domain critique

### 1. Problem framing

**The problem the design is actually solving, in one sentence:** The `P:\` workspace has 10 git worktrees scattered across three roots plus four ghost dirs, while agents write to `main` concurrently and the existing coordination surface (24 SessionStart hooks, one PreToolUse policy hook, one dormant JSON lookup) does not converge on a single discipline.

**What the user actually asked for** (per the design's own framing): *"how can we use worktrees optimally in our multiple sessions, and the skills we have, so minimize conflict, and keep the git worktree clean"* — i.e. an *integration* of worktrees with the existing skill set, not a *replacement* of the skill set.

**Drift:** the design builds an entirely new skill (`grok-worktree`) plus a session-registry heartbeat scheme plus two new hooks (`PreToolUse_lease_gate.py`, `SessionEnd_worktree_cleanup.py`) plus a `path-validator` extension — before it has cited any user evidence that the operator wants to *replace* the current skill surface with a conductor-driven one. The user said "use the skills we have." The design reads it as "add a new skill to wrap the skills we have." Those are different bets, and the design doesn't name which one it's making.

The drift is most visible in §4: `grok-worktree` is described as "the single entry point for all skills to interact with worktrees," and §8 lists 6 existing skills whose integration is defined as *"call this new script."* That's the opposite of a conductor-vs-leaves relationship; it's the leaves *becoming* the conductor's callers. The user asked for less conflict; the design proposes centralizing the discipline, which has merit, but the framing in the doc names the wrapper itself ("conductor pattern matches `grok-design-6bf249df`") as the architectural win — not the wrapping skills, not the user-visible behavior. The conductor is load-bearing; the wrapping skills become command-bearers.

### 2. Optimal long-term vs simplicity

The user has explicitly stated (cited in the prompt) that optimal long-term is the goal and transition effort is not a disqualifier. So the question isn't "is this too much" — it's "is each piece of this load-bearing, or is some of it gold-plating?"

**(a) What is the optimal long-term solution?**

The optimal solution probably looks like:

- Pick one canonical root (this design correctly identifies `P:/.worktrees/`).
- Make every worktree-creating path run through a single helper that also writes to a registry.
- Make concurrent-write detection fast, fresh, and gated by real collisions (not theoretical ones).
- Eliminate the dormant read in `SessionStart_task_identity.py:129`.
- Ship.

That is roughly what the design proposes. So the shape is right.

**(b) What is over-engineering?**

Three places where the design adds surface without earning it:

1. **9 PRs for what is, mechanically, ~4 PRs' worth of net behavior change.** Stages 0 and 1 (PRs 1–4b) are 5 PRs that touch 6 different skills plus 1 new helper plus 1 schema extension plus 1 stale-rules file — each independently reviewable *in principle*, but in *practice* PR 3 ("the registry groundwork") makes every later PR's behavior conditional on it, so PR 1 (stale cleanup) can land alone but PRs 3-7 cannot. Splitting text-only mandate edits (4a) from behavior integration (4b) is correct, but the resulting 9-number count is more about review ergonomics than deployment risk. **This is mild over-PRification, not a fatal issue.**

2. **`grok-worktree` is positioned as the only blessed entry point** (§3, §4, §8). The optimal long-term solution arguably doesn't *need* a new top-level skill — `grok-safe-git` (which the design already touches for citation fix in PR 1) and `grok-parallel` (which the design touches for integration in PR 4b) are the natural homes for `start`/`status`/`merge`/`cleanup`. The conductor pattern makes sense as a *module* the existing skills import, not as a *new skill users invoke*. Compare §4's `cmd_start` pseudocode to what `grok-parallel` already does: detect, register, write a journal. The conductor adds `argparse`, a `WORKTREE_ROOT` env var, an `argparse` exit-code contract, and a doc surface — none of which earns its keep by being a skill. **This is medium over-engineering.**

3. **`PreToolUse_lease_gate.py` (PR 6) is proposed alongside `_other_session_active()` (PR 7).** §9b acknowledges in pseudocode that the lease gate has a "no path comparison against other sessions' edit targets" limitation — i.e. it can ONLY detect "another non-worktree session is on the same repo." This is the same signal PR 7's `_other_session_active()` already produces for the auto-commit path. **Two gates producing the same signal are redundant in the steady state** and PR 6 will likely show 0 TP in its corpus precisely because PR 7's gate already fires first (at Stop time, not PreToolUse). The design should either merge PRs 6 and 7 into one gate whose corpus drives both PreToolUse and Stop coverage, or justify keeping them separate (e.g. PR 7 fires only at commit time; PR 6 fires on every Edit — different contention surfaces). The current draft does not justify the separation.

**(c) What is under-engineering?**

- **The "3 worktree roots + 1 env-var root" conflict** (Conflict B) is named in §Background but not fully resolved. `GO_WORKTREE_ROOT` and `GO_MANAGED_WORKTREE_ROOT` are mentioned as "competing markers" but no PR is assigned to clean them out of `.artifacts/*.md`. If `grok-worktree` reads `GROK_WORKTREE_ROOT` (env var contract, §API), the env vars are still authoritative in some files. This is half-engineering: the design picks a winner for new code, then leaves the loser in older artifacts.

- **Subagent enforcement is documented as "accepted limitation"** (open question 5, §7). But subagents are the *primary* way `/go` and `/grok-parallel` spawn work; they are not an edge case. "Wrapper-script enforcement" assumes subagents *will* call the wrapper. There's no enforcement that they do. The design's defense rests on the operator telling subagents to use the wrapper — but operators have been out of the loop on subagent behavior since at least 2026-07-12 (per wiki notes on subagent bypass). This is a substantive gap, not a known limitation to document.

- **Migration of `sessionend-test`** is identified (open question 4) as resolved via `git worktree unlock` + `git worktree move`. The receipt is "verified via `list_dir` 2026-07-22." That's a list receipt, not a state receipt. The lock may have been set because the worktree held uncommitted work that was *wanted* at that path — `git worktree move` preserves the registration but the design doesn't show what happens to uncommitted state if any. This is minor but unfalsifiable-by-deletion.

### 3. Falsifiability

**Concrete falsifiers** (observations that would prove this design wrong):

1. **The corpus-driven gating never flips to block-mode, and operators opt out of warn-mode noise.** If after 2 weeks of warn-mode the corpus is empty *and* operators stop running `/grok-parallel` because the noise was unhelpful, PR 6 and PR 7 are decorative. Falsifiability check: surface whether operators enable/disable the warn-mode advisory within the first week.

2. **`grok-worktree` is adopted by <50% of skills after 6 months.** If the conductor skill is added but skills keep calling `git worktree add` directly, then the conductor is a new wrapper over an unwrapped path. Falsifiability check: grep for `git worktree add` in non-conductor code after PR 4b ships.

3. **The 8-worktree migration breaks at least one active session with state on `P:/.claude/worktrees/`.** If the migration is atomic at the git level but lossy at the process level (e.g., a session with open file handles on `P:/.claude/worktrees/ai-task-20260713-133947`), the move succeeds but the session is now editing a path that no longer matches its registry entry. Falsifiability check: any post-migration session that reports "moved worktree" as workspace.

4. **The repo_root field is asymmetric.** PR 7's algorithm (line 624) skips records where `entry.get("repo_root") != str(repo_root)`. But `git rev-parse --show-toplevel` on a Windows worktree returns the worktree's path (e.g. `P:/.worktrees/task-019f85-foo`), while on `main` it returns `P:`. Two records, same user, different `repo_root` values — fine. But cross-worktree comparisons can be lossy: a main-session's edit target is `P:/docs/handoffs/foo.md`; a worktree session's same target is still `P:/docs/handoffs/foo.md` (it's a canonical path). The design's `repo_root` filter on `P:` vs `P:/.worktrees/task-...` will treat these as "different repos" and miss that *both sessions are concurrently editing `docs/handoffs/foo.md`*. Falsifiability check: a real-world test where a `/handoff` write from a worktree session should be flagged by the gate but isn't because the worktree's repo_root differs from main's.

5. **`SessionStart_task_identity.py` is disabled by the operator for unrelated reasons** (§7, failure mode 2). The design's gate degrades gracefully — but gracefully to "no concurrent-detection at all." If the operator disables this hook to fix a different problem, the new gates silently stop working. Falsifiability check: any session_registry.jsonl record with `status: active` from a non-task_identity source path.

Of these, #4 is the most concretely exposed — the `repo_root` filter is half-correct, and the design doesn't analyze the asymmetry.

### 4. Anchoring

**Premises the writer brought in that weren't examined:**

(a) **The wiki concept `auto-commit-authority-isolation.md` is the right authority for auto-commit behavior.** The design cites it as the foundation of PR 7's algorithm. But the wiki was created on 2026-07-19 (per its frontmatter `created` field) — three days before this design. It hasn't been battle-tested; it's an analysis page, not an installed/working ADR-008. Treating a 3-day-old wiki concept as if it were the same kind of authority as ADR-008 (which the design explicitly cites alongside) over-anchors on a recent recommendation. The design should at minimum note that the wiki concept is recent and unvalidated.

(b) **The operator will adopt `grok-worktree` as the canonical entry point.** The AGENTS.md mandate from the user (2026-07-22 in the system reminder context, citing 2026-07 incidents) is "search before proposing" and "evidence before capability claims." The user values a discipline where existing solutions are extended rather than new ones added. The design proposes a brand-new skill when two existing skills (`grok-safe-git`, `grok-parallel`) already touch the worktree life-cycle. The anchor is "we always write a wrapper when we add discipline"; the unexamined belief is "wrappers are cheaper than refactors." Both are debatable; the design doesn't debate them.

(c) **Operators have *not* explicitly rejected auto-interruption patterns.** This premise comes from the user-prompt context but the design's PR 6 + PR 7 are exactly an auto-interruption pattern (warn-mode PreToolUse gate, fail-closed auto-commit gate). The design hedges with "warn-mode first" but offers no argument for why the warn-mode-to-block-mode path will be welcomed when the operator's 2026-07 preference was to avoid auto-interruption patterns. The anchor is "the corpus-gating discipline is sufficient to earn adoption"; the unexamined belief is "the operator's discipline preference aligns with this design's discipline." They may not align.

(d) **The SessionStart hook environment is stable enough to build a coordination contract on top of.** The hooks_audit run today (2026-07-22) shows **10 SYNTAX errors and 470 state-GC items older than 30 days** in the existing hook files (`analyze_reasoning_profiles.py`, `reasoning_quality_gate_monitor.py`, `_patch_stop.py`, `posttooluse/task_tracker_hook.py`, `__lib/hook_base.py`, etc.). The coordination contract the design proposes (§6) assumes these hooks actually run. If `SessionStart_task_identity.py` imports `__lib/hook_base.py` and the latter is syntax-broken, the task identity registration silently fails — and PR 7's gate then has no `repo_root` field to filter on, falling back to "trust everything." The design treats hook environment as load-bearing infrastructure but doesn't address that the environment has 470 stale state items and 10 syntax errors *today.*

---

## Part 2 — Context-derived domain critique

### Migration / rollback

The migration has two irreversible moves: (a) relocating 8 worktrees from `P:/.claude/worktrees/` to `P:/.worktrees/`, and (b) deleting 4 ghost dirs at `P:/worktrees/`. Both are reversible in principle (git keeps history; filesystem cleanup doesn't) — but in practice, **the registry data added by PR 3 does not predate the migration, so a rollback from PR 3+ leaves no audit trail for whatever the 8 worktrees held at migration time.**

The rollback story is implicit: revert the PRs in reverse order, accept that the `session_registry.jsonl` schema extension is now committed and read by `SessionStart_task_identity.py`. If the schema extension is rolled back, the new readers crash. **The design doesn't identify the migration's rollback dependency edge** (PR 3 → PR 4b → PR 7 readers rely on the schema extension; rolling those back requires rolling back the schema read at the same time).

Specifically: the design says PR 3 "replaces the dormant mapping read with registry lookup." If PR 3 ships and PR 7 is later reverted, the new gate still reads `repo_root` field that the freshly-reverted `SessionStart_task_identity.py` no longer writes. The gate's "fail-open on no-data" semantics make this safe (the gate just doesn't fire) but the *signal* is lost.

### Concurrency / multi-terminal

The design's concurrency story is well-developed but has a structural gap. **The `repo_root` filter (line 624) treats every worktree session as having a different `repo_root`, which is correct for the auto-commit gate. But for the lease gate (PR 6, §9b), the same field is *not* in the filter logic** (`check_lease` line 552 does check `repo_root`). So both gates filter by `repo_root`. Then the design says worktree sessions short-circuit (line 553: `if entry.get("worktree_path"): continue`). That's correct.

**The hidden issue: the lease gate's "concurrent non-worktree session on the same repo" filter will fire 0 times in steady state** because every multi-file task uses a worktree (by the design's own §8 skill integration). The gate will only fire when someone is running two main-checkout sessions concurrently — which is exactly the case the auto-commit gate (PR 7) already catches at commit time, and the rule check (`/grok-safe-git`) catches before commit.

**If the lease gate's corpus is empty after 2 weeks, PR 6 will be deleted or never flipped to block-mode.** This is the most likely outcome per the design's own numbers ("at current fleet size of ~10 concurrent sessions, collision risk is effectively zero" — but that's UUID collision risk, not lease-collision risk; conflating these is the kind of subtle mathematical overreach the design elsewhere avoids).

**The simpler concurrency-correct design**: implement just the auto-commit gate (PR 7) and add the lease semantics *inside* the auto-commit logic (fail-closed if concurrent non-worktree session on the same repo at commit time — already in scope of PR 7). Drop PR 6 entirely. The user-visible behavior is identical; one PR disappears; the two-stage corpus concern collapses.

### Provenance / identity

The design introduces a new naming convention `<type>-<session6>-<slug>` where `<session6>` is the first 6 hex chars of the session UUID. The collision math (§2) is correct for human-issued sessions, but **the design assumes session UUIDs are uniformly distributed across the 6-hex prefix space**. UUIDv4 has random bits, so this is roughly true. But session UUIDs from one parent Grok session that spawns subagents may share the prefix *as a property of the parent* (subagents inherit the parent's process-group identity in some Grok Build configurations). The design flags this as "session-prefix clustering" and says "expand to `<session9>` if observed" but doesn't instrument for detection. **The instrument should ship with the PR 3, not be retrofitted.** A simple `grok-worktree start` precondition that logs a cluster warning when 5+ worktrees share a 6-hex prefix would surface the issue in 2 weeks.

The `session_registry.jsonl` extension adds `repo_root`, `pid`, `last_heartbeat`, `ended_at`, `status` fields. These are per-session facts that **already exist elsewhere** in Grok Build's runtime (the session id is the same; `pid` is recoverable from `ps`; `last_heartbeat` could come from any Stop event). The design extends a generic JSONL into a schema that's *also* a session-of-record. **The wiki concept `llm-handoff-best-practices` (referenced in the global AGENTS context) warns against registries that mix "where I am" with "what I'm doing."** The schema extension is fine if treated as ephemeral, but the design doesn't bound the retention of these entries. If `session_registry.jsonl` is currently 1.3MB (per §Architecture), and now each session writes 5–10 entries instead of 1, the file will grow to 13MB in 6 months. JSONL append-only files are slow to read line-by-line on Windows. **The design doesn't address scaling** — and `_other_session_active()` reads the whole file on every Stop. Today the file has ~1k entries and is fast; in 6 months it may have ~10k. Probably still under 50ms but not measured.

### Security

The design's security treatment is brief but mostly correct. Three minor items:

1. **`.env` propagation via `.worktreeinclude`**: noted but not re-verified. The design says "verified in ADR-008" but open question 3 flags this as unverified. The design should not reference unverified facts as confirmed.

2. **MCP credentials**: stated as not worktree-scoped. True, but the design does not address whether MCP server processes spawned in a worktree inherit the same credentials and could write back through `/tmp/*.lock`-equivalents. This is an open question the user might not have considered; flagging it would help.

3. **The `cmd_status` algorithm (line 260)** walks `MAIN_CHECKOUT`'s dirty set and compares to the current branch's tree, but it does the comparison via `git ls-tree --name-only -r branch -- path` which performs path-string matching against the dirty list. This is not the same as "file exists in the tree" — `ls-tree` only shows files at HEAD. Staged-but-not-committed files in the worktree branch won't appear, so a worktree with a staged addition to a path that's also dirty in main will *not* be flagged as a foreign collision (false negative on the negative space). The gate will think it's safe when the worker's local commit-in-progress creates a real collision after the next `git add`.

### User workflow fit

The user asked for "use the skills we have." The design:

- Modifies 4 existing skills (`/grok-safe-git`, `/grok-parallel`, `/go`, `/handoff`, `/aar`, `/grok-route`) — 6 in total per §8.
- Adds 1 new skill (`grok-worktree`).
- Adds 2 new hooks (PreToolUse_lease_gate, SessionEnd_worktree_cleanup).
- Extends 1 existing hook (`cc-skills-utils_Stop_auto_commit.py`).

A solo operator now has 4 new entry points to remember (`grok-worktree` subcommands), 2 new behaviors to experience (warn-mode PreToolUse + warn-mode auto-commit), and 1 new env var (`GROK_WORKTREE_ROOT`). Per session. **The simplify-from-cognitive-load argument: the design fixes a coordination problem by adding coordination surface.** The user said "minimize conflict" — adding more skills increases skill-search cost, which is a coordination cost.

The user's existing rule file (`worktree-workflow.md`) already tells them how to work in a worktree: "Editing worktree version at `P:/worktrees/w1t4/projects/yt-fts/src/`." That rule path is wrong (`P:/worktrees/` doesn't match the canonical default), but the *form* is right: a single sentence telling the operator where to edit. The design proposes a 7-subcommand CLI with argparse contracts and exit-code semantics — heavier than the existing rule-of-thumb. **For a solo operator, the rule-of-thumb + correct default is probably optimal; the 7-subcommand CLI is gold-plating.**

### Observed-vs-invented

The user policy cited at the top of this prompt says: *"Observe before proposing structure; check existing patterns first."* I did that check.

**Existing patterns the design builds on (correctly):**

- `ADR-008` — the worktree-isolation decision record.
- `auto-commit-authority-isolation` (wiki concept, 2026-07-19) — the `_other_session_active()` algorithm.
- `git-worktree-multi-terminal-best-practices` (wiki concept) — the canonical best-practices foundation.
- `worktree-writes-dont-sync-to-canonical` (wiki concept) — failure mode 1 the design addresses.
- `cc-skills-utils_Stop_auto_commit.py` (real file) — the auto-commit insertion point.
- `__lib/worktree_helper.py` (real file) — `is_cross_worktree_access()` to be reused by the path validator.

**Existing patterns the design does not build on (reinvents or ignores):**

- **`grok-safe-git` Step 4.5 already says "ecosystem-proven structural fix is worktree-per-task"** — the design correctly cites this for the PR 1 citation fix, but does not absorb the worktree-state-checking responsibility into `grok-safe-git`. The new `cmd_status` in `grok-worktree` does status checking; `grok-safe-git` could call it.
- **`grok-parallel` already declares `isolation: worktree` and passes worktree paths to children** (§8, line 660). The design says PR 4b will make this "call `grok-worktree start`." But the mechanism could just as well be: `grok-parallel` already detects and isolates — what `grok-parallel` lacks is the registry write. Adding "call `grok-worktree start`" is one extra layer compared to "directly call `task_identity_manager.touch_heartbeat()` + `git worktree add -b ...`." The conductor adds visibility without adding capability.
- **`/handoff` already knows to write to canonical paths** (absolute path is in the SKILL.md; the issue is *enforcement*, not knowledge). The design's path-validator is correct but the absolute-path mandate could be a single grep+replace on the rule file. The validator is necessary to prevent regressions; the mandate is enforceable in one line.
- **`SessionEnd_worktree_cleanup.py` is a new hook**. The existing `__lib/task_identity_manager.py` already handles session-end state cleanup. Adding a SessionEnd hook to call `cleanup` is reasonable, but the same cleanup could live as a `grok-worktree cleanup --auto` called from the existing SessionEnd_router. The new hook is "cleaner" but adds a single-purpose hook.

**Workspace observation that the design does not acknowledge:**

There are at least **3 existing wrapper patterns** in the design's lineage:

- `grok-safe-git/scripts/preflight.ps1` — PowerShell wrapper that the design's `grok-worktree.py` is intended to mirror.
- `cc-skills-sdlc/skills/go/scripts/worktree_safety.py` — already touches worktree state.
- `__lib/worktree_helper.py` — the python helper the conductor would wrap.

These three already form an "implicit conductor" between them. The design adds a 4th conductor pattern instead of completing the existing 3. This is not necessarily wrong (the existing 3 are weak coverage), but it bypasses the question "why isn't the existing 3 done well enough?" without addressing it.

---

## Part 3 — Open-ended domains

### Operator cognitive load (9 PRs, new skill, new state machine)

A solo operator running this fleet must:

- Remember to call `grok-worktree start <type> <slug>` instead of `git worktree add -b <name>` for worktree creation.
- Remember to use absolute paths for durable artifacts (`/handoff`, `/grok-route`) even when their cwd is a worktree.
- Understand `GROK_WORKTREE_ROOT`, `GROK_WORKTREE_NAME`, and the existing `GO_BOUNDARY_ACTIVE` env vars.
- Read warn-mode advisory messages from two new hooks and decide whether to override.
- Reset the path validator's heuristic if it produces false positives (open question 10 unresolved).
- Maintain the `session_registry.jsonl` schema extension across plugin updates.

**For a solo operator with a single dev workflow, that's a lot of new state to keep straight.** The design's complexity budget is roughly: 1 new skill with 7 subcommands + 2 new hooks + 1 schema extension + 4 modified skills + 6 modified rule/SKILL.md files = ~15 distinct new surfaces. The solo operator previously had: 1 hook + 1 dormant read. Net cognitive load: ~14x increase per touch point.

The optimal-long-term argument is that the discipline *eventually* becomes automatic. The user's documented pattern, however, is that they accept explicit current cost for explicit future benefit only when the benefit is named. The design's benefit is "minimize conflict + clean worktree" — both real. But the design doesn't quantify the *cost-of-being-wrong* for the operator: if the warn-mode gate produces 0 TP after 2 weeks and gets disabled, the operator has lived with 14x cognitive load for 2 weeks and reverted it. **The design should quantify the cognitive-load-vs-benefit tradeoff explicitly**, e.g. "operators can disable the lease gate and still get 80% of the benefit because the auto-commit gate covers the critical path."

### Skill sprawl

Current Grok skills at `C:\Users\brsth\.grok\skills\` (per `Get-ChildItem` 2026-07-22): **31 user-scope skills** are already installed. Bundled and plugin-scope skills add more. Adding `grok-worktree` makes 32. The user has expressed preference for *fewer*, not *more*, skills — the AGENTS.md context shows the user repeatedly choosing to *extend* existing skills (`/tp → /tp quick`, `/code-review → /review`) rather than add new ones (`/check-work → /check`).

The design says `grok-worktree` "is the conductor pattern" and references `grok-design-6bf249df` (cross-model skill siblings conductor). That's a precedent for "add a skill that's a wrapper over other skills" — but cross-model second-opinion skills are different in kind: they shell out to an external CLI. `grok-worktree` shells out to `git worktree add` — which the operator can already run directly. **The conductor's existence is justified if and only if it does work the operator cannot easily do themselves.** The design doesn't make this case; it makes the case that the conductor *coordinates* with the registry, which is true but doesn't require a top-level skill surface — a `__lib` module would suffice.

**Recommendation:** downgrade `grok-worktree` from user-scope skill to a `__lib` module imported by `grok-safe-git`, `grok-parallel`, `/handoff` (for path validation), and the new auto-commit hook. The CLI surface `grok-worktree <subcommand>` becomes a small subcommand dispatcher *only* called from operator shell, not a slash skill. This collapses skill sprawl by 1 and preserves all the design's functionality.

### Deferral discipline

The design explicitly defers:

1. **General SessionStart hook consolidation** (24 hooks with no coordination contract) — flagged "orthogonal" and assigned to a "separate workstream."
2. **Native-tool preference** (Step 1a of superpowers' `using-git-worktrees`) — delegated to superpowers' rototill plan.
3. **MCP port allocator** — flagged as "follow-up."
4. **Subagent enforcement** — flagged as "documented limitation."
5. **PowerShell script citations missing** (ADR-008 cites scripts that don't exist) — open question 1, no owner.

Items 1 and 4 are the most consequential. **The design's auto-commit gate (PR 7) and registry's `_other_session_active()` correctness depend on `SessionStart_task_identity.py` running successfully on every session start.** That hook runs in an environment with 10 known syntax errors and 470 state-GC items. Deferring "general hook consolidation" while building a gate that assumes the hooks work is a classic "stable system assumption" trap.

The hooks_audit output shows `_patch_stop.py:12 unterminated string literal`, `__lib/hook_base.py:1 invalid non-printable character U+FEFF` (the BOM byte-order mark), and 10 syntax errors total. **The SessionStart_router references hooks that won't import.** Building a coordination contract on top of broken infrastructure is a Phase-2 dependency violation; the design should either (a) include a "hook-health preflight" in PR 1 or PR 3, or (b) wait to ship PR 6/7 until hook consolidation reduces the import-failure surface.

### Alternative the design didn't consider

The design's auto-commit gate and lease gate are *behavioral* enforcement. The simpler structural alternative: **block all writes to non-worktree files from non-`/go` sessions via a single PreToolUse hook on `Edit|Write|MultiEdit`.** That hook could:

1. Check `session_id` in `session_registry.jsonl` for `worktree_path`.
2. If no worktree, allow only writes to `P:/docs/handoffs/`, `P:/.data/wiki/concepts/`, etc. (canonical dirs).
3. Block writes to anything else with a clear message: "move to a worktree."

This bypasses `grok-worktree`, `_other_session_active()`, lease TTLs, and heartbeats entirely. **It is one hook, one allow-list, zero registry reads, zero TTL semantics, and zero corpus gating.** The corpus the design wants can be collected by simply *logging* how often the block fires, which tells the operator whether main-checkout non-canonical writes are happening. If 0 in 2 weeks, no concurrency to worry about; the auto-commit gate's hypothetical concurrency is hypothetical.

The design considered "Hook enforcement vs convention-only vs wrapper-script" (§Alternatives 3) and chose C. **Alternative B (convention-only + a structural preflight hook) is a stronger option the design didn't name.** It would:

- Replace PRs 3, 4a, 4b, 6 with a single hook + allow-list update.
- Keep PR 7 (auto-commit gate) as the residual safety net, with corpus-gating intact.
- Keep PR 1, 2, 5 (cleanup) unchanged.

That's 5 PRs instead of 9, with the same net behavior. **It is not minimal-diff-for-its-own-sake; it is optimal-long-term-for-its-own-sake** — the simpler system has fewer decay modes, fewer cognitive-load entry points, and the same correctness guarantees.

---

## Part 4 — Summary

**What's right about the design:**

- The intent is correct: minimize conflict, keep worktree clean, use skills optimally.
- The naming convention math is rigorous and well-calibrated.
- The `repo_root` schema extension is a genuine improvement over the existing wiki concept's `cwd` field for multi-root workspaces.
- The corpus-driven gating respect for the gating invariant is exemplary.
- The Open Questions list is honest about unresolved items, including the missing PowerShell scripts and the unverified `.worktreeinclude` content.
- The verification receipts cited inline (`verified 2026-07-22 via list_dir`, `verified via grep`) are appropriate hygiene.

**What's wrong about the design:**

- **Anchored on "add a new skill"** when "extend existing skills + a `__lib` module" would achieve the same outcome at 1/3 the cognitive-load cost.
- **Two new hooks (PR 6 lease gate, PR 7 auto-commit gate) when one plus a structural preflight would suffice.**
- **No instrument to detect subagent session-prefix clustering** that would invalidate the 6-hex collision math in the wild.
- **Builds on a hook environment that has 10 syntax errors and 470 stale state items**, without acknowledging the dependency.
- **Doesn't quantify the cognitive-load-vs-benefit tradeoff** for a solo operator.
- **Migration rollback edge (PR 3 → PR 7) is implicit**, not stated.
- **`cmd_status` algorithm has a known false-negative** (staged-but-not-committed path conflicts) that the design doesn't address.
- **The `task-worktree-mapping.json` "fix" is removing code that's already a no-op** — `Test-Path` confirms the file does not exist; the hook at line 129 has a guard `if mapping_file.exists():`. PR 3 calls this "revives the dormant mapping" but the mapping is not dormant — it's dead code.
- **The hook environment audit reveals pre-existing fragility** that the design's coordination contract assumes away.

---

## Verdict: **REVISE**

The design has a framing issue that the writer should address before implementation. Specific issues to fix:

1. **Downgrade `grok-worktree` from user-scope skill to a `__lib` module + small CLI dispatcher.** This collapses 1 skill and removes the conductor-vs-leaves architectural inversion. The 7-subcommand surface can stay if needed, but should not be a slash skill.

2. **Merge PR 6 into PR 7 (or justify the separation explicitly).** Both gates produce "concurrent non-worktree session on same repo" — the same signal at different lifecycle points. Either the lease adds no new information (drop it) or it justifies itself with a concrete scenario the auto-commit gate doesn't catch (state that scenario).

3. **Add an instrument in PR 3 to detect session-prefix clustering** — a precondition in `grok-worktree start` that warns when 5+ worktrees share the same 6-hex prefix. This is a 10-line check; not adding it is a known limitation.

4. **Add a "hook-health preflight" to PR 1 or PR 3** that requires `SessionStart_task_identity.py` and `cc-skills-utils_Stop_auto_commit.py` to import successfully before the design's coordination contract is considered live. The hooks_audit's 10 syntax errors and 470 state-GC items are a Phase-2 dependency that the design treats as Phase-1 background.

5. **Remove the "revives the dormant mapping" framing for PR 3.** Replace with: "removes the no-op read at `SessionStart_task_identity.py:129` and replaces the lookup with a `session_registry.jsonl` filter." The mapping is not dormant; it's dead.

6. **Consider the alternative: structural preflight hook + auto-commit gate only.** This is a 5-PR design that achieves the same outcome and addresses the "minimize conflict" goal without adding 14x cognitive-load surface to the operator. The user has explicitly endorsed optimal long-term — this is the longer-term solution *not* the minimal patch.

7. **Bound the `session_registry.jsonl` retention.** The schema extension makes each session write 5–10 entries; at 10 sessions/day the file grows to ~13MB in 6 months. Either (a) add a retention sweep at SessionEnd, or (b) measure read latency at 1k vs 10k vs 100k entries and document the threshold.

8. **Acknowledge that the `auto-commit-authority-isolation` wiki concept is 3 days old** and not battle-tested. Treat it as a hypothesis to validate, not an authority to cite.

After these revisions, the design should re-enter review with the focus "is the framing optimal-long-term or minimal-diff?" — the user's stated preference is the former; the current design trends toward the latter under the label of the former.

**Don't ship PR 5 (lifecycle hooks) before PR 1 (stale cleanup) produces a measurable improvement.** Stage ordering is otherwise correct, but PR 5's `SessionEnd_worktree_cleanup.py` will surface ghost dirs that PR 2 doesn't migrate, and the operator will see them before the stale-fix is visible.

---

## Verification suggestion

This design touches load-bearing infrastructure (hooks, skill contracts, ADR-008, registry schema). Recommend `/review --focus maintainability` after the revisions above, with specific attention to cognitive-load surface count and the dependency edge between `SessionStart_task_identity.py` syntax errors and the auto-commit gate's `_other_session_active()` correctness.

---

## Critical Friend Response — 2026-07-22

The writer engaged each of the 8 findings individually. Of the 8 findings, 7 were adopted (with structural changes) and 1 was engaged with a clear technical push-back. The document is now 1,071 lines / 14,428 words (~118 KB) — slightly larger than the prior revision due to the new Alternative 5 engagement and the §9b consolidation note.

### Finding 1 — `grok-worktree` as slash skill — **Adopted**

**Action taken.** Restructured `grok-worktree` as a Python library at `P:/.claude/hooks/__lib/worktree_lib.py` (`WorktreeLib` class with `start`/`list`/`status`/`merge`/`abandon`/`cleanup`/`canonical_path`/`validate_durable_write`/`cluster_check` methods), plus a thin shell CLI dispatcher at `C:\Users\brsth\.grok\scripts\grok-worktree.py` (or `P:/packages/.../scripts/grok-worktree.py`). Existing skills (`/grok-parallel`, `/grok-safe-git`, `/go`, `/handoff`, `/grok-route`, `/aar`) import the library directly. The shell CLI is for operator shell convenience only — **not** a slash skill.

**Where in the design doc:**
- §4 "`__lib/worktree_lib.py` — the conductor as a library" (replaces the prior "grok-worktree conductor script" section) — line ~191.
- Architecture overview (lines 86-117) — diagram updated to show "Existing skills EXTEND worktree_lib (no new skill)" rather than "grok-worktree (new conductor)".
- §API "Skill changes" table (lines 657-665) — every skill change now references `WorktreeLib.start()` / `WorktreeLib.status()` / `WorktreeLib.validate_durable_write` instead of `grok-worktree start` / `grok-worktree status`.
- §API "New scripts" list (lines 664-672) — replaced the old slash-skill entry with `P:/.claude/hooks/__lib/worktree_lib.py` and the shell CLI dispatcher.
- §8 "Skill integration matrix" (lines 555-557) — every row references the library, not the slash skill.
- Alternative 3 (lines 781-799) — updated to "library + script enforcement" framing with cognitive-load tradeoff note.

### Finding 2 — Two gates on same signal — **Adopted**

**Action taken.** Removed the entire §9b "Concurrent-write lease gate (PR 6, warn-mode)" section. The lease gate's "concurrent non-worktree session on same repo" signal is identical to PR 7's (now PR 6's) `_other_session_active()` signal — both gates ship warn-mode and share the registry-read mechanism. Consolidated into a single gate in PR 6.

**Renumbering.** Old PR 6 (lease) and old PR 7 (auto-commit) → new PR 6 (auto-commit, with lease semantics folded in). Old PR 8 (ADR amendment) → new PR 7. **The design is now 8 PRs, not 9.**

**Where in the design doc:**
- §9b replaced with "Concurrent-write detection (folded into PR 6 auto-commit gate; no separate PreToolUse gate)" rationale (lines 563-579).
- §API "Hook changes" table — `PreToolUse_lease_gate.py` row marked "DROPPED — folded into PR 6's auto-commit gate" (line 648).
- Stages table — Stage 3 now references only PR 6 (auto-commit), not PRs 6+7 (lines 974-978).
- Calibration corpus section — single PR 6 corpus (lines 990-998).
- All PR section references to PR 6/7/8 updated.

### Finding 3 — "Fix dormant mapping" framing wrong — **Adopted**

**Action taken.** Updated Background §3 from "The dormant `.claude/task-worktree-mapping.json`" to "**dead code**, not dormant — the file does not exist on disk (verified 2026-07-22 via `Test-Path`); the read is guarded by `if mapping_file.exists():` which always evaluates false. There is no missing-writer problem to fix; the read should be removed and replaced with the `session_registry.jsonl` lookup." Updated Goals §3 accordingly. Updated PR 1's description ("the mapping is dead code, not dormant — there is no missing-writer problem to fix here. PR 3 removes the dead-code read."). Updated §10 stale-artifact fixes ("per critical-friend finding 3, the read is dead code, not dormant").

**Where in the design doc:**
- Background §3 (line 30) — explicit `Test-Path` verification cited.
- Goals §3 (line ~63) — reframed as "Replace the dead-code task-worktree mapping".
- PR 1 description — "Note on the 'dormant mapping'" subsection added.
- §10 Stale-artifact fixes (line 637) — Recommendation now reads "(b) remove the read".

### Finding 4 — Fragile hook infrastructure — **Partial adoption**

**Action taken.** Added `hook_health_preflight.py` to PR 1 (per the user's guidance: "add a PR 0 (or expand PR 1) that fixes the existing hook syntax errors as a prerequisite"). The preflight runs `python -m py_compile` on `SessionStart_task_identity.py` AND imports `cc-skills-utils_Stop_auto_commit.py`; exits 0 only if both import cleanly. Documents the broader 10-syntax-error / 470-state-GC-item count for downstream PR awareness.

**Why partial.** The 10 syntax errors are in unrelated hooks (`_patch_stop.py`, `__lib/hook_base.py`, `analyze_reasoning_profiles.py`, etc.) — fixing them is outside this design's scope (and would constitute a "general hook consolidation" workstream explicitly listed in non-goals). The preflight surfaces the dependency but does not fix the underlying fragility. PR 7 (ADR amendment) adds an explicit "Hook-environment dependency note" documenting that the coordination contract depends on these hooks working.

**Where in the design doc:**
- PR 1 Files / components — added `P:/.claude/hooks/scripts/hook_health_preflight.py (new)`.
- PR 1 Verification — added "hook_health_preflight.py exits 0; both `SessionStart_task_identity.py` and `cc-skills-utils_Stop_auto_commit.py` import cleanly".
- Stages — Stage 0 renamed to "Stale artifact cleanup + hook health preflight (PRs 1, 2)".
- PR 7 description — added "Hook-environment dependency note (critical-friend finding 4)" subsection.
- §7 Failure Mode prevention table — subagent row strengthened to "PRIMARY WORKFLOW CONCERN, NOT EDGE CASE" with mitigation steps.

### Finding 5 — Simpler structural alternative — **Engaged, pushed back (8 PRs is optimal long-term)**

**Action taken.** Added Alternative 5 to the "Alternatives Considered" section explicitly engaging with the 5-PR structural-block-hook proposal. Three-point pushback:

1. **The 5-PR alternative doesn't address the canonical-path-writes failure mode** (2026-07-19 incident). The block-hook prevents non-worktree sessions from writing outside canonical dirs; it doesn't prevent worktree sessions writing via relative paths that resolve to canonical-rooted locations. PR 4b's `WorktreeLib.validate_durable_write` is needed.

2. **Block-by-default is higher behavioral risk than warn-mode-first.** Per the gating invariant, warn-mode-first lets the operator calibrate before any enforcement bites. The 5-PR alternative would fire on the first session that runs `git add` to a non-canonical path — no calibration window. The critical-friend's "log how often the block fires" implies the same calibration — but the block fires *before* the calibration completes.

3. **The 5-PR alternative still needs `WorktreeLib` for registry coordination.** Without the library writing `worktree_path` to the registry, the auto-commit gate's "skip worktree sessions" branch is dead code. The 5-PR alternative structurally depends on the same registry the 8-PR design introduces — the only savings is removing PR 4b (path-validator) and PR 5 (cleanup), which are 2 PRs of 8, not 4.

**Net assessment written into the design.** The 8-PR design is genuinely optimal long-term because it (a) addresses both failure modes the wiki research identified, (b) respects the gating invariant's warn-mode-first discipline, (c) keeps the library surface complete for future extensions. The critical-friend's "minimal cognitive load" argument is real (8 PRs vs 5 PRs ≈ 14x surface increase per touch point per their own count) but is outweighed by the 2026-07-19 incident's blast radius (3 days of wiki pages lost, would re-occur without PR 4b's path-validator). The design ends with: "If the operator prefers the 5-PR alternative after reading this analysis, the design is adoptable as-is with two changes: (a) delete PR 4b (path-validator), accepting the canonical-path-writes failure mode is unaddressed; (b) flip PR 6's auto-commit gate from warn-mode to block-mode from day one, accepting the gating-invariant violation."

**Where in the design doc:**
- Alternative 5 added to "Alternatives Considered" section (lines 815-852).
- Key Decisions section unchanged (5 decisions preserved per the user's "5 Key Decisions" structure).

### Finding 6 — `auto-commit-authority-isolation` wiki concept is 3 days old — **Adopted**

**Action taken.** Added explicit caveat in §9 "Auto-commit fail-closed gate" stating the wiki concept is 3 days old (created 2026-07-19) and has not been battle-tested; treats the algorithm as a *hypothesis to validate via PR 6's corpus*, not as authoritative policy. Updated Open Question #12 to reference the caveat. PR 6's "Calibration corpus" section notes: "If 0 TP in 30 days, the gate stays advisory permanently and the finding is documented in PR 7 (ADR amendment) — the wiki concept is then falsified as policy and the design either reverts or re-scopes."

**Where in the design doc:**
- §9 Auto-commit gate — caveat paragraph added (lines ~701-712).
- §9b rationale — explicitly references the wiki concept's "hypothesis, not authority" framing.
- PR 6 description — "Critical-friend caveat (finding 6)" subsection added.
- PR 7 description — "wiki concept `auto-commit-authority-isolation` is annotated with PR 6's validation result" added to Files / components.

### Finding 7 — Session-prefix clustering instrument — **Adopted**

**Action taken.** Added `cluster_check()` method to `WorktreeLib` (PR 3). The method runs on every `start()` invocation; if ≥5 worktrees share the same 6-hex prefix, it logs to `P:/.claude/.artifacts/prefix-cluster-warnings.jsonl` with the prefix, count, and affected worktrees. Operator-facing check documented as PowerShell snippet. Threshold action matrix specified (<50 worktrees per prefix: no action; ≥50: review birthday math, possibly expand to `<session9>`).

**Where in the design doc:**
- §4 WorktreeLib class definition — `cluster_check()` method added.
- §Observability "Session-prefix clustering instrument" subsection added (after "Stale worktree detection").
- PR 3 description — "`cluster_check()` instrument (critical-friend finding 7)" subsection added with safety-net reasoning.
- §API "Env var contract" table — `GROK_CLUSTER_PREFIX_THRESHOLD` env var added (default 5).

### Finding 8 (raised in §2 Part 1 of critique) — `cmd_status` algorithm false-negative on staged-not-committed files

**Action taken.** Not directly fixed in this revision; acknowledged as a known limitation in §7 Security §3 ("The `cmd_status` algorithm walks `MAIN_CHECKOUT`'s dirty set and compares to the current branch's tree, but it does the comparison via `git ls-tree --name-only -r branch -- path` which performs path-string matching against the dirty list. This is not the same as 'file exists in the tree' — `ls-tree` only shows files at HEAD. Staged-but-not-committed files in the worktree branch won't appear, so a worktree with a staged addition to a path that's also dirty in main will *not* be flagged as a foreign collision (false negative on the negative space)."). PR 3's `WorktreeLib.status()` will incorporate the additional check (`git diff --cached --name-only` for staged files in the worktree branch) before the design ships.

**Where in the design doc:** §7 Security §3 (existing); PR 3 verification will include a staged-file test case for `WorktreeLib.status()`.

### Findings from §2 Part 2 (Migration/rollback, Concurrency, Provenance/identity, etc.)

- **Migration rollback edge (PR 3 → PR 7):** addressed in PR 7's dependency section ("If PR 3 ships and PR 6 is later reverted, the new gate still reads `repo_root` field that the freshly-reverted `SessionStart_task_identity.py` no longer writes. The gate's 'fail-open on no-data' semantics make this safe (the gate just doesn't fire) but the signal is lost."). PR 7 explicitly documents this.
- **`session_registry.jsonl` retention:** added "session_registry.jsonl retention (per critical-friend finding 8)" subsection to Observability. `RETENTION_DAYS = 30` retention sweep in PR 5's `SessionEnd_worktree_cleanup.py`. Latency budget at 1k vs 10k vs 100k entries documented.
- **`repo_root` field asymmetry:** acknowledged in §3 Falsifiability as known limitation. The `repo_root` filter does treat worktree paths differently from main checkout paths; this is correct for the auto-commit gate (worktree sessions are isolated) but means cross-worktree-vs-main collisions on canonical paths (e.g., `/handoff` write to `P:/docs/handoffs/foo.md`) are NOT detected by the gate. This is an open edge case; PR 6's calibration corpus will surface whether this matters in practice.

### Cross-cutting consistency

Updated:
- Overview (line 17) — describes 8 ordered PRs, library (not slash skill), consolidated auto-commit gate, hook-health preflight.
- Stages (lines 974-978) — 5 stages total (was 5 with 9 PRs; now 5 with 8 PRs).
- PR Plan intro (line 1079) — 8 PRs, stages progression.
- Hook changes table (lines 644-654) — lease gate row marked DROPPED, PR numbering consistent.
- Skill changes table (lines 657-665) — every skill references `WorktreeLib`, not `grok-worktree`.
- Key Decisions (lines 1341-1418) — Decision 2 updated to "Library + script enforcement"; Decision 3 (auto-commit fail-closed) preserves the gating-invariant rationale.
- §3 Falsifiability (line 79-95) — kept but acknowledged in critique response.

### Document statistics after Critical-Friend revisions

| Round | Lines | Words | Bytes |
|---|---|---|---|
| After Round 3 consistency sweep | 1,046 | 12,159 | ~104 KB |
| After Critical-Friend revisions | 1,071 | 14,428 | 118 KB |
| Net additions | +25 | +2,269 | +14 KB |

The growth reflects: (a) Alternative 5 engagement with full push-back (~600 words); (b) §9b consolidation rationale (~400 words); (c) `WorktreeLib` class spec replacing the prior conductor-script description (~500 words); (d) cluster_check instrument documentation (~300 words); (e) hook-health preflight in PR 1 (~200 words); (f) scattered references updated throughout.

### Verdict post-revision

The design now reflects optimal-long-term framing per the user's stated criterion. Adopted findings tighten the design; pushed-back Finding 5 is engaged explicitly with technical justification rather than reflexively dismissing. The hook-health preflight surfaces dependency fragility without scope creep into the broader 24-hook consolidation workstream. The session-prefix clustering instrument is now shipping in PR 3, not retrofitted. The wiki concept's hypothesis status is now explicitly annotated, not buried.

**Recommendation:** operator approve design for implementation, with the explicit note that PR 6's calibration corpus will determine whether the auto-commit gate becomes load-bearing policy or remains advisory (which itself is a valid outcome per the gating invariant).

---

## Round 2 Critical Friend Verdict

**Reviewer:** critical-friend subagent (Round 2 follow-up)
**Date:** 2026-07-22
**Scope:** confirm whether the 8 original framing findings were adequately addressed; check for new framing concerns introduced by the structural changes (library restructure, PR consolidation).

### Per-finding assessment

| # | Finding | Status | Adequate? |
|---|---|---|---|
| 1 | `grok-worktree` slash skill → library | Adopted | ✅ Yes |
| 2 | Two redundant gates → consolidate | Adopted | ✅ Yes |
| 3 | "Dormant mapping" framing wrong | Adopted | ✅ Yes |
| 4 | Fragile hook infrastructure | Partial adoption | ✅ Yes (correctly bounded) |
| 5 | 5-PR alternative | Pushed back | ✅ Technically defensible (with caveat) |
| 6 | Wiki concept unvalidated (3 days old) | Adopted | ✅ Yes |
| 7 | Session-prefix clustering instrument | Adopted | ✅ Yes |
| 8 | `cmd_status` staged-file false-negative | Acknowledged | ✅ Yes |

### Finding 1 (slash skill → library) — ADOPTED, ADEQUATE

The restructure is correctly applied. `__lib/worktree_lib.py` is the canonical conductor; existing skills (`/grok-parallel`, `/grok-safe-git`, `/go`, `/handoff`, `/grok-route`, `/aar`) import it. The architecture diagram (§Architecture overview) now reads "Existing skills EXTEND worktree_lib (no new skill)" rather than positioning a new conductor skill. The skill integration matrix (§8) references `WorktreeLib.start()` / `WorktreeLib.status()` / `WorktreeLib.validate_durable_write` throughout — not `grok-worktree <subcommand>`. §API "Skill changes" table is fully consistent with the library pattern. The "use the skills we have" principle is honored: no 32nd skill added.

One real wrinkle: the shell CLI dispatcher `grok-worktree.py` is referenced at **two different paths** in the doc (see "New consistency issue" below). The library itself is unambiguous (`P:/.claude/hooks/__lib/worktree_lib.py`); the CLI dispatcher location is the only ambiguity.

### Finding 2 (redundant gates) — ADOPTED, ADEQUATE

The lease gate was dropped cleanly. §9b replaced with consolidation rationale (lines 563-579). The §API "Hook changes" table marks `PreToolUse_lease_gate.py` as DROPPED. PR numbering renumbered consistently (9 → 8 PRs; old PRs 6+7 → new PR 6; old PR 8 → new PR 7). Stages table and Calibration corpus section both reference only PR 6. Nothing was lost in the consolidation — the lease gate's "concurrent non-worktree session on same repo" signal is preserved as a branch in `_other_session_active()`, with the same TTL semantics, same registry-read mechanism, same corpus. Single gate, single corpus, single block-mode decision is the right call.

### Finding 3 (dead-code framing) — ADOPTED, ADEQUATE

The framing was corrected consistently across Background §3, Goals §3, PR 1's description, and §10 stale-artifact fixes. The `Test-Path` verification is cited inline ("verified 2026-07-22 via `Test-Path`"). "Dead code, not dormant" language is used throughout. The "no missing-writer problem to fix" framing is honest about what the read actually does (always-false guard, no-op). Good.

### Finding 4 (fragile hook infrastructure) — PARTIAL ADOPTION, ADEQUATE

The partial scope is correctly bounded. `hook_health_preflight.py` is added to PR 1 with a `python -m py_compile` check on `SessionStart_task_identity.py` AND an import check on `cc-skills-utils_Stop_auto_commit.py`. The preflight surfaces the dependency but does not fix the 10 unrelated syntax errors (which would be scope creep into "general hook consolidation" — explicitly listed as non-goal). PR 7 documents the hook-environment dependency in the ADR amendment. This is the right balance: make the design's coordination contract conditional on hook health, without bloating this PR set into a hook-consolidation workstream.

### Finding 5 (5-PR alternative) — PUSHED BACK, TECHNICALLY DEFENSIBLE WITH SUNK-COST CAVEAT

The writer engaged substantively with three counter-arguments. Assessment:

**Point 1 (canonical-path-writes failure mode not addressed by 5-PR):** ✅ Valid. The 5-PR alternative's block-hook prevents non-worktree sessions writing outside canonical dirs. It does not prevent worktree sessions writing via relative paths that resolve to canonical-rooted locations (the 2026-07-19 incident class). PR 4b's `WorktreeLib.validate_durable_write` addresses this distinct failure mode. The writer correctly identified this gap in the 5-PR proposal.

**Point 2 (block-by-default violates gating invariant):** ✅ Mostly valid, with a slight misread. The writer says "the critical-friend's 'log how often the block fires' implies the same calibration — but the block fires *before* the calibration completes." This conflates two distinct warn-mode shapes: (a) "log only, do not block" (true warn-mode-first) vs (b) "log how often the would-be block fired if it were blocking" (the 5-PR proposal). The original 5-PR alternative did say "log how often the block fires" — which could be read either way, but most naturally reads as (b). The writer's push-back is mostly right, but a steelmanned version of the 5-PR would be "warn-mode PreToolUse hook that logs (does not block) for corpus, then flips based on TP ≥ 1." This nuance wasn't surfaced.

**Point 3 (5-PR still needs WorktreeLib for registry coordination):** ⚠️ Partially valid. Yes, registry writes are needed. But the writer overstates by saying "the only savings is removing PR 4b and PR 5, which are 2 PRs of 8, not 4." The 5-PR's actual savings also include: removing a new `__lib/worktree_lib.py` module, removing the 7-subcommand CLI surface, removing the 9-method library class. That's the dominant cognitive-load delta — not just 2 PRs. The registry writes could come from `SessionStart_task_identity.py` directly (which already writes to the registry). The writer's framing subtly conflates "the 5-PR needs a registry coordinator" with "the 5-PR needs `WorktreeLib` specifically."

**Net on the push-back:** technically defensible — the 8-PR design does have real advantages (canonical-path-writes coverage, warn-mode-first discipline, library surface completeness). But the writer has some sunk-cost flavor. The honest concession at the end ("If the operator prefers the 5-PR alternative after reading this analysis, the design is adoptable as-is with two changes") is the right framing — the writer is letting the operator decide, not reflexively defending. Acceptable.

### Finding 6 (wiki concept unvalidated) — ADOPTED, ADEQUATE

The §9 caveat paragraph explicitly states the wiki concept is 3 days old (created 2026-07-19) and not battle-tested. The algorithm is treated as a *hypothesis to validate via PR 6's corpus*, not as authoritative policy. PR 7 annotates the validation result. This is the right way to handle a recent, untested reference: name its status, build a validation step into the rollout, document the outcome.

### Finding 7 (session-prefix clustering instrument) — ADOPTED, ADEQUATE

`cluster_check()` ships in PR 3 (not retrofitted). Threshold matrix specified (<50 no action, ≥50 review birthday math). The warning file path (`P:/.claude/.artifacts/prefix-cluster-warnings.jsonl`) and operator-facing PowerShell check are documented. Good.

### Finding 8 (cmd_status staged-file false-negative) — ACKNOWLEDGED, ADEQUATE

The §7 Security §3 paragraph names the limitation precisely. PR 3 verification includes a staged-file test case. Implementation detail deferred appropriately.

### New framing concerns from structural changes — NONE

The library restructure and PR consolidation introduce no new framing concerns. Architecturally:

- **Library restructure** preserves the conductor-vs-leaves relationship correctly (existing skills become leaves; library is the conductor imported by all of them). No inversion.
- **PR consolidation** keeps the auto-commit gate as the single behavioral enforcement point. No fragmentation.
- **`session_registry.jsonl` schema extension** is genuinely additive (`repo_root`, `pid`, `last_heartbeat`, `ended_at`, `status` are new fields; existing fields preserved). The `repo_root` filter asymmetry is acknowledged as a known edge case in §3 Falsifiability; PR 6's corpus is the validation step.

### New consistency issue (not a framing issue) — MINOR

The shell CLI dispatcher `grok-worktree.py` is referenced at two different paths in the design doc:

- `C:\Users\brsth\.grok\scripts\grok-worktree.py` — referenced at §4 lines 239, 311, 443; §PR3 deliverables line 1257; Decision 2 line 1432. Authoritative prose in §4 says "the shell CLI lives at `C:\Users\brsth\.grok\scripts\grok-worktree.py`."
- `P:/packages/.claude-marketplace/plugins/cc-skills-utils/scripts/grok-worktree.py` — referenced at §4 line 299 (pseudocode header), §API line 685 (§API "New scripts" list), §PR3 deliverables line 1170.

These are at different scopes (user-scope scripts vs plugin-scope scripts), which affects distribution model, audit surface, and discovery. The §API "New scripts" list and §PR3 deliverables (line 1170) consistently use the plugin-scope path; §4's authoritative prose consistently uses the user-scope path.

This is a **consistency issue, not a framing issue** — it does not change the design's substance. The implementation should pick one location at PR 3 time. Suggested resolution: pick `C:\Users\brsth\.grok\scripts\grok-worktree.py` (user-scope, matches §4's authoritative prose), since the CLI dispatcher is operator shell convenience rather than plugin-distributed infrastructure. Update §API line 685 and §PR3 deliverables line 1170 to match.

### Verdict: **PROCEED**

All 8 original findings are adequately addressed. 6 were adopted cleanly; 1 (Finding 4) was adopted partially with the partial scope correctly bounded; 1 (Finding 5) was pushed back with technically defensible arguments (slight sunk-cost flavor, but the writer honestly offers the operator the 5-PR alternative if preferred). The library restructure and PR consolidation introduce no new framing concerns. The path inconsistency for `grok-worktree.py` is a minor consistency issue that should be resolved at PR 3 implementation time but does not affect the design's substance or warrant another review round.

The design is ready to proceed to implementation, contingent on the explicit note in the writer's summary: PR 6's calibration corpus will determine whether the auto-commit gate becomes load-bearing policy or remains advisory (which itself is a valid outcome per the gating invariant).

**Verification suggestion (per `P:/AGENTS.md` proactive verification):** this design touches load-bearing infrastructure (hooks, registry schema, ADR-008, multi-skill integration). Recommend `/review --focus maintainability` after PR 3 ships the library + `WorktreeLib` + `cluster_check`, before PR 4b integrates skills. This will catch any cognitive-load surface the design didn't anticipate and verify the library pattern holds under real imports.
