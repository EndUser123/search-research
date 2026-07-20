---
name: refactor
description: >
  Intelligent structural refactor: plain-language target/mode inference,
  plan-on-disk then seam execute with verify, multi-terminal isolation,
  stale-data immunity, worktree cleanup. Use for /refactor, multi-file
  refactor, extract god module, reduce coupling, implement review findings
  as structure work, or when /go routes refactor-shaped tasks here.
when-to-use: >
  /refactor, refactor, dry-run refactor, extract module, split god file,
  implement maintainability findings, reduce dual paths, multi-seam refactor,
  clean up hard-to-maintain code
argument-hint: "[plain language | path | package | optional flags]"
effort: high
metadata:
  short-description: "Seam refactor: plan, isolate, verify, no stale data"
---

# /refactor — Intelligent structural refactor

## Developer preferences (load before recommending)

The refactor plans and seam scoping this skill produces must honor the developer's governing preferences, which override any default "simplicity first" or "minimal change" framing:

- **Optimal long-term over minimal-diff** — default to the solution that best meets requirements with lowest future cost and risk, even if transition effort is large. The number of seams or PRs is NOT a cost to minimize; the right number is whatever the optimal solution requires.
- **Transition effort is not a selection criterion** — the user does not care how much work the change is.
- **Surgical ≠ smallest** — touch only what the optimal solution requires, but "surgical" does not mean "smallest scope." A 7-seam refactor is correct if the optimal solution requires 7 seams.

Source of truth: `~/.grok/AGENTS.md` § "Optimal long-term solution" and `~/.claude/Claude.md` § "Implementation Principles."

You are the **refactor orchestrator**. The user describes the job in plain
language. **You** infer target, mode, depth, isolation, and budget. Do **not**
require flags.

Same product feel as `/review` and `/go`: plain language, intelligent routing,
artifacts on disk, no fake done. Defaults favor **safety and isolation**, not
unbounded scope.

**Product rule:** Plan modes write `PLAN.md` + `seams.json` with evidence.
Execute modes add per-seam verification, isolation, and a recorded worktree
**cleanup** decision when a worktree was used.

This skill coordinates existing tools. It does **not** re-enter itself via
`/go` refactor profile (see Anti-recursion).

---

## Multi-terminal isolation (required)

This workspace runs concurrent agents/terminals. Treat every run as contested.

| Rule | Detail |
|---|---|
| **Write root** | Prefer a **dedicated worktree + branch** for multi-file / multi-seam / shared-package execute. Never assume main checkout is yours. |
| **One writer** | Only this run edits the chosen write root. Do not edit main and worktree in parallel for the same seams. |
| **Safe-git every wave** | Re-run preflight immediately before write/commit waves. Earlier green status is **stale**. |
| **Foreign staged/dirty** | If staged or unrelated dirty files appear on the write root → **stop writes**. Report. Do not reset/clean to proceed. |
| **Run identity** | Every run gets a unique `$runDir` under `P:\.artifacts\$termSafe\grok-refactor\<slug>\<ts>\` (timestamp). Never overwrite another run’s dir. |
| **State files** | Persist seam status only under `$runDir` (and optional durable package copy). Do not use fixed global names like `P:\tmp\refactor-state.json`. |
| **Worktree naming** | Include package + short reason + time or random suffix so two terminals do not collide: `P:\.worktrees\<pkg>-refactor-<slug>-<ts>`. |
| **No silent steal** | If `git worktree add` fails (path/branch exists), do not delete foreign worktrees. Report and pick a new name or reuse only if user pointed at it. |

Announce isolation:

```text
REFACTOR: write_root=<path> branch=<name|main> isolation=worktree|inplace terminal_safe=yes|no
```

If `terminal_safe=no` (contested main, no worktree possible): **plan only** or stop with unblock steps.

---

## Stale-data immunity (required)

Do not trust plan, review, HEAD, or status from earlier in the session without re-check at use time.

| Data | Freshness rule |
|---|---|
| **seams.json** | Before execute or continue: re-read file from resolved path; compare `target`, `created_at` / `plan_head`, and current `git rev-parse HEAD` (or worktree HEAD). If HEAD moved in ways that touch seam `files`, re-validate those seams (Step 5.2). |
| **Review findings** | May seed inventory only if path matches target and age is reasonable. Treat as **hints**. P0/P1 seams still need tool re-check of current source before `pending` → execute. |
| **PROGRESS / status** | Source of truth is current `seams.json` on disk for this run (or resolved continue plan), not chat memory. |
| **Safe-git / dirty** | Re-run before each write wave and before cleanup/remove. |
| **Tests green** | Evidence must be from commands run **this turn** for the seam claim. |
| **“Already fixed”** | Decide only by reading current code at seam locations, not prior notes. |
| **Worktree path** | Confirm path still exists and `git -C <wt> rev-parse` works before editing. |

Stamp plans:

```json
"plan_head": "<short sha at plan time>",
"target": "<absolute package or module path>",
"created_at": "<iso>"
```

On continue: if `plan_head` ≠ current HEAD **and** `git diff plan_head..HEAD -- <seam files>` is non-empty → re-validate affected seams before edit.

---

## Defaults (three tables — do not conflate)

### A. Safety (never off for execute)

| Control | Default |
|---|---|
| Safe-git before writes | ON |
| Verify after each seam | ON |
| Stop walk on verify fail | ON |
| Integrity-first ranking (P0→P3) | ON |
| P0/P1 tool-backed evidence | ON |
| Stale-data re-checks | ON |
| Multi-terminal isolation rules | ON |

### B. Isolation

| Control | Default | Opt out |
|---|---|---|
| Worktree + branch for multi-file / multi-seam / shared package / contested main | **ON** | `--no-worktree`, clean single-file lite, or user-supplied WT path |
| Unique run_dir + WT name | **ON** | — |
| Cleanup decision recorded after execute+WT | **ON** | — |

### C. Scope (caps, not “more power”)

| Control | Default | Override |
|---|---|---|
| Walk budget | **3** seams | `--budget N`, or “until empty” / “finish backlog” |
| Depth | standard unless package-wide / multi-seam | deep / lite from language |
| Auto plan if no usable seams | **ON** | — |

**`--lite`:** smaller inventory, single-seam bias, worktree optional if clean single file. Still: tests for behavior change, verify, stale checks, safe-git.

Do **not** ask which defaults to enable. Announce:

```text
REFACTOR: mode=… target=… depth=… worktree=on|off budget=N|n/a isolation=…
why: <≤20 words>
run_dir: <absolute>
```

---

## Easy use (flags optional)

```text
/refactor                              # infer target; mode from language
/refactor yt-is                        # package name only → plan
/refactor fail-closed mapping in yt-is # named problem → slice execute
/refactor implement the yt-is findings # all, budget 3
/refactor continue                     # next pending (resolve plan path)
```

Optional: `--dry-run` / `--plan`, `--slice <id>`, `--all`, `--continue`,
`--budget N`, `--no-worktree`, `--lite`, `--durable`.

---

## Anti-recursion

| Do | Do not |
|---|---|
| Load safe-git, discovery, verify skill bodies directly | Call `/go` in a way that re-selects profile `refactor` |
| For multi-file implement inside a seam: edit in write_root; optional general-purpose subagent with **explicit** “profile=change only; do not load refactor skill” | Nested `/go refactor …` |
| Parent stays refactor orchestrator | Second concurrent refactor writer on same write_root |

---

## Core concepts

### Seam

One closed structural cut:

> After this change, **only X owns Y**; **Z is removed or fail-closed**;
> **tests prove the rule**.

### Plan vs execute — single ambiguity rule

| User text | Mode |
|---|---|
| Package/path **only**, or “what should we”, “plan”, “dry-run”, “inventory” | **plan** → stop after artifacts |
| **Verb of change** (fix, extract, implement, apply, do, land, merge the fix) **or** named defect/outcome (fail-closed mapping, remove order zip, split X out of Y) | **execute path**: `slice` if one clear seam, else `all` if backlog/implement-all language |
| “continue” / “next seam” | **continue** |
| Single file + simplify/extract + clean | **lite** |

**The bare word “refactor” is not implement language.**  
`/refactor yt-is` → plan.  
`/refactor yt-is` + “do it” / “implement” / named fix → execute.

Ambiguous with no verb and no named defect → **plan**, announce, one question max if still unclear.

### Auto-execute constraints (after plan on execute path)

Proceed without “shall I proceed?” **only if** all hold:

1. Mode is execute (`slice` / `all` / `continue` / implement language), and  
2. Every seam started this turn either:  
   - matches user-named defect/outcome, **or**  
   - is class **P0–P2**, **or**  
   - user explicitly said implement backlog / all findings / until empty, and  
3. P0/P1 seams have tool-backed evidence (below).

**Do not** auto-start agent-invented **P3** extracts unless user asked for that extract or explicitly for full backlog including structure cleanup.

Irreversible risk (data wipe, untested public API break) → one short confirm.

### “All findings”

Backlog in `seams.json`; execute one seam at a time under budget.

---

## Step 0 — Run directory (unique per run)

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$slug = "<package-or-local>"
$runDir = "P:\.artifacts\$termSafe\grok-refactor\$slug\$ts"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
```

Resolve `$termSafe from `$env:CLAUDE_TERMINAL_ID / `$env:WT_SESSION (same as /review and /check).

Never reuse another terminal’s run dir. Write `_run.json` with `started_at`,
`mode`, `target`, `plan_head` (when known), `write_root`, `worktree`.

| Path | Role |
|---|---|
| `PLAN.md` | Human plan |
| `seams.json` | Backlog + evidence + status |
| `PROGRESS.md` | Seams, shas, commands, isolation notes |
| `RESULT.md` | End summary + merge/resume commands |
| `worktree.json` | WT path, branch, cleanup |
| `findings_link.md` | Review artifact pointer if used |

---

## Step 1 — Infer target

| Signal | Target |
|---|---|
| Named package / `packages/` path | that package |
| File/dir path | owning package or module |
| Dirty tree + no name | local dirty module (state isolation still applies) |
| Thread context | continue that package if clear |
| Else | ask once |

Resolve `yt-is` → `P:\packages\yt-is` when present. Read package AGENTS/HANDOFF when useful.

---

## Step 2 — Infer mode and depth

Apply **single ambiguity rule** above. Flags override when present.

| Depth | When |
|---|---|
| lite | `--lite` or single clean file |
| standard | one named seam / few files |
| deep | package-wide multi-seam |

Emit `REFACTOR:` announcement before heavy work.

---

## Step 3 — Resolve plan for continue / resume (stale-safe)

Order (first hit that parses and matches target):

1. Path user gave  
2. Package durable: newest `docs/operations/refactor-plan-*.md` with sibling or embedded seams, or `docs/operations/seams-*.json` if present  
3. Newest `P:\.artifacts\$termSafe\grok-refactor\<slug>\*\seams.json` for that slug whose `target` matches  
4. Active worktree handoff if it points at a plan path  
5. Else **replan** and say: `continue: no prior seams; replanned`

Then apply stale-data rules (HEAD / file diff). Do not execute a plan whose target path does not match.

---

## Step 4 — Plan phase (no product writes)

### 4.1 Inventory

1. Safe-git (read-only ok).  
2. Prefer recent `/review` for target as **hints** only.  
3. Tool-backed reads/greps for candidates.  
4. Discovery ON if dual planes / multi-root unclear.  

### 4.2 Rank

P0 silent data/status loss → P1 dual policy → P2 races/promote → P3 extract → P4 nits (cap).

### 4.3 Evidence bar (before status can be executed)

| Class | Required before execute |
|---|---|
| **P0 / P1** | This-run tool check: file:line or quote of current code; `evidence` field filled; not “from memory” |
| **P2** | Same when cheap; else `evidence: unverified` and block auto-execute until checked |
| **P3 / P4** | Location + outcome sentence; P3 auto-execute only under auto-execute constraints |

### 4.4 seams.json

```json
{
  "target": "P:/packages/yt-is",
  "created_at": "<iso>",
  "plan_head": "<sha>",
  "budget_default": 3,
  "seams": [
    {
      "id": "A2",
      "title": "Fail-closed uncorroborated source order map",
      "class": "P0",
      "outcome": "No list-order gap-fill; missing bind fails mapping",
      "files": ["csf/nlm_batch.py", "tests/test_nlm_batch.py"],
      "depends_on": [],
      "delete_or_close": ["order zip gap-fill path"],
      "evidence": "main nlm_batch.py:3042 zip gap-fill present (read <iso>)",
      "evidence_kind": "tool_read",
      "characterization": "tests/test_nlm_batch.py or describe",
      "verify_commands": ["python -m pytest tests/test_nlm_batch.py -q"],
      "end_to_end_verification": "python bin/csf-source fetch --limit 5 --workers 1",
      "end_to_end_rationale": "Seam touches NLM source-add I/O path; unit tests verify the parser but not the live API integration.",
      "status": "pending"
    }
  ]
}
```

`evidence_kind`: `tool_read` | `review_hint+tool_read` | `unverified`.

**`end_to_end_verification` (mandatory field):** Every seam must specify how
its behavior will be verified end-to-end, not just via unit tests. Options:
- A concrete command that exercises the changed code path against real I/O
- `"N/A: pure extract with zero callers"` — only valid for dead-code removal or pure refactors with no behavior change
- `"N/A: no external I/O touched"` — only valid for seams that don't touch auth, network, filesystem, or external APIs

If the seam touches auth, I/O, network, or external services and the field
is empty or `"N/A"` without a justification in `end_to_end_rationale`, the
seam **cannot advance to execute**. This is the structural gate that
prevents the Phase 1 path bug (unit tests passed, end-to-end was broken).

See `P:/.data/wiki/concepts/verification-before-completion-principle.md`
for the behavioral principle this gate enforces structurally.

### 4.5 After plan

- Mode plan → `REFACTOR PLAN READY` and **stop**.  
- Mode execute → auto-execute only under constraints; else stop with plan + what was blocked.  

---

## Step 5 — Worktrees

### Create (execute, isolation default ON)

Package git root preferred:

```powershell
$pkg = "P:\packages\<package>"
$branch = "refactor/<slug>-<ts>"
$wt = "P:\.worktrees\<package>-refactor-<slug>-<ts>"
cd $pkg
git worktree add -b $branch $wt HEAD
```

On failure: new suffix or stop; never remove another terminal’s worktree.

`worktree.json`: path, branch, `created_by_this_run`, `package_git_root`, `cleanup: pending`.

All product edits go in write_root (worktree).

### Cleanup (mandatory after execute that used a worktree)

Re-check `git -C <wt> status` immediately before any remove (stale-safe).

| Outcome | cleanup | Action |
|---|---|---|
| Merged or user confirmed discard; clean or no valued WIP | `done` | `git worktree remove`; delete branch if merged/safe |
| Commits remain; not merged | `deferred` | Keep WT; print **merge commands** + **resume one-liner** |
| Dirty with uncommitted value | `blocked_dirty` | Do not remove; report |
| No WT | `n/a` | — |

**Always print on deferred/success with branch:**

```text
merge: cd <pkg>; git checkout main; git merge <branch>
# or: gh pr create ...
resume: /refactor continue   # plan: <absolute seams.json>  wt: <path>
```

Do not leave cleanup unstated.

---

## Step 6 — Execute one seam

Preconditions: isolation ok; seams resolved; deps done; evidence bar met for P0/P1; safe-git ok **now**.

1. **Claim** — `in_progress` in this run’s seams copy; PROGRESS  
2. **Re-validate (stale)** — re-read locations; skip if fixed; block if conflicted with foreign edits  
3. **Behavior lock** — behavior change: fail-then-pass when practical; pure extract: suite green; delete dead: zero callers  
4. **Implement** — minimal; one owner; remove/fail-closed old path when possible; no dual-write without exit + tests  
5. **Close gate fields** (required in PROGRESS/RESULT per seam):  
   - `primary_owner:` module/function that owns the decision  
   - `dual_path_remaining:` yes/no (if yes: exit condition or block done)  
   - `net_loc:` +x/-y if easy from diff stat  
6. **Verify ON** — `verify_commands` this turn + grok-verify checklist  
7. **Commit policy** — commit **only if** user asked to commit **or** this stream already established commit-per-seam with user assent. Otherwise leave diff in WT and record `git diff --stat` in PROGRESS. Stage only paths this seam owns (safe-git). Never commit foreign staged files.  

On verify fail: `blocked`; do not advance walk.

---

## Step 7 — Walk (`all` / `continue`)

1. Resolve plan (Step 3); stale-check.  
2. Budget default 3.  
3. Loop runnable seams (auto-execute constraints apply each time).  
4. Cleanup decision.  
5. RESULT.md with remaining ids + resume/merge.  

---

## Step 8 — Structure rules

1. Single ambiguity rule for plan vs execute.  
2. Safety / isolation / scope tables separate.  
3. Multi-terminal isolation + stale-data rules always.  
4. No `/go` refactor recursion.  
5. One seam closed before next.  
6. Integrity before extract on same surface.  
7. P0/P1 evidence before execute.  
8. Close-gate: dual_path_remaining + primary_owner.  
9. Commit only with policy above.  
10. Cleanup always decided; deferred always has resume + merge text.  

---

## Step 8.5 -- Recommended next (skill handoff)

| Outcome | Recommended next |
|---------|------------------|
| All seams done, verify PASS | `/check <branch>` to verify session claims |
| Deferred seams remaining | `/refactor continue` to resume |
| Verify FAIL on a seam | Fix and re-verify before advancing |
| All done + needs fresh eyes | `/review --branch <branch>` for adversarial pass |

### Update state file

Update `P:/.artifacts/<termSafe>/<pkg>-state.md` with:
- `Last verify`: refactor status + seams done/remaining
- `Recommended next`: from table above

---

## Step 9 — Final report

```text
REFACTOR PLAN READY | REFACTOR DONE
mode: …
write_root: …
isolation: worktree|inplace
seams_done / remaining: …
verify: PASS|FAIL|BLOCKED|partial
worktree: …
cleanup: done|deferred|blocked_dirty|n/a
plan_head: … current_head: … stale_recheck: ok|revalidated|blocked
artifact: …
next: …
```

---

## Durable copy

On `--durable` / user save / package-wide plan:  
`<package>/docs/operations/refactor-plan-YYYY-MM-DD.md`  
(+ seams json if useful). Do not overwrite hand-maintained ledgers without asking.

Prefer durable copy when multi-terminal continue is likely (tmp runs are per-machine and easy to lose).

---

## Examples

| User | Behavior |
|---|---|
| `/refactor yt-is` | Plan only |
| `/refactor what should we change in yt-is` | Plan only |
| `/refactor fail-closed mapping in yt-is` | Evidence → slice execute; WT ON if multi-file; verify; cleanup |
| `/refactor implement yt-is findings` | Plan if needed; walk P0–P2 first under budget; P3 only if backlog-all language; isolation ON |
| `/refactor continue` | Resolve seams path; stale recheck; next seam |
| `/go refactor nlm_batch coupling` | This skill; no nested refactor via go |

---

## Rules (summary)

1. Plain language; flags optional.  
2. Safety defaults never off for execute; isolation ON when contested/multi-file.  
3. Scope budgets are caps, not “do more.”  
4. Multi-terminal isolation + stale-data immunity always.  
5. Artifacts unique per run; no fake verify.  
6. Anti-recursion with `/go`.  
7. Canonical: `P:/.grok/skills/refactor/SKILL.md`.  
