# CRUD Operations Redesign: Problem, Solution, Implementation Plan

**Status**: Draft for Critical Review  
**Date**: 2026-06-27  
**Context**: Solo director + disposable AI coders; enterprise bloat is the enemy

---

## Non-Goals

This redesign does **not** attempt to:

- Enforce enterprise approval workflows
- Prevent all bad code
- Judge code quality
- Replace tests
- Secure secrets against a malicious local user
- Make Claude Code upstream cache bugs disappear
- Keep custom hooks merely because they already exist

If a future proposal expands scope into any of these, reject it unless the three-question gate (below) explicitly admits it.

---

## Problem Statement

### Symptoms

1. **Opaque block reasons** — Agent must read `cc_errors.jsonl` + `pretooluse_blocks.jsonl` to diagnose which of 13 hook layers blocked a tool call
2. **Read blocked by write-policy** — `PreToolUse_directory_policy.py` incorrectly blocked Read operations on `P:/.pi/**`
3. **Untracked plugin sources fail in worktrees** — Plugin source dirs (skill-guard, cc-aca-observability validator, doc-to-skill, cc-skills-utils health scripts, doc-compiler) are untracked; worktree from HEAD has empty dirs
4. **Non-idempotent verification** — Structural-change detector nags across turns even after verification completes
5. **4-step manual cache rebuild** — Edit source → bump version → run `plugin-audit-and-fix.py --bump` → `/reload-plugins`
6. **Agent claims "done" without evidence** — No verification gate for completion claims

### Root Causes

| Cause | Type | Evidence |
|-------|------|----------|
| 13-layer hook stack with different log formats | Architectural | `cc-aca-safety` has 8 PreToolUse hooks; `cc-aca-observability` adds more |
| Cache is version-keyed, not content-keyed | Design | Cached `0.1.8` loads even after source edit if version not bumped |
| Upstream Claude Code bugs | External | Issue #59643: `permissionDecisionReason` not surfaced; Issues #17789/#36035/#39328: cache staleness |
| No done-gate | Missing behavior | Agent can claim "fixed" without showing changed files + test result |
| Plugin sources not in git | Process | Worktree creates empty dirs for untracked plugin sources |

### Threat Model

**Solo director directing disposable AI coders.**

Goal: Let AI coders move fast, but make it hard to:
- silently wreck the repo
- lie about completion
- trap themselves in policy sludge

**NOT:** enterprise change-control, maximum governance, approval ceremonies.

---

## Solution

### Architecture: Three Questions, Three Answers

| Question | Mechanism | Scope |
|----------|-----------|-------|
| May this tool/action run? | nah + settings.json allow/deny/ask | Permission |
| May the agent claim this is finished? | custom done-gate Stop hook | Truth |
| Has this exact state been verified? | verified.jsonl session log | Idempotency |

**Anti-bloat rule:** Reject any hook that doesn't answer exactly one of these.

### Components

```text
┌─────────────────────────────────────────────────────────────┐
│  nah (external, Alpha — pin version)                        │
│  - Deterministic allow/block; optional LLM for `ask`        │
│  - Self-reported 95.8% on 101,194 Bash traces (nah's own    │
│    benchmarks; says nothing about this PowerShell stack)    │
│  - Action taxonomy: test/git/file/network/destructive/pkg   │
│  - Returns: allow/ask/block with inline reason              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  settings.json (built-in)                                   │
│  - allow/deny/ask for project-specific path rules          │
│  - Evaluated in order: deny → ask → allow                  │
│  - settings.json `deny` is the hard floor; nah cannot      │
│    override it                                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  done-gate Stop hook (custom, ~20 lines)                   │
│  - Triggers on: done/fixed/ready/implemented/tests pass    │
│  - Requires: changed files + verification + issues        │
│  - High-leverage, low-risk, fully custom                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  verified.jsonl (session log)                               │
│  - Append-only: {task_id, files, command, exit_code, ts}  │
│  - Structural-change detector filters against it           │
│  - Makes verification nags idempotent                      │
└─────────────────────────────────────────────────────────────┘
```

### What Gets Deleted

- 13 custom hooks (directory_policy, protected_file_recovery, ownership_colocation, destructive Bash validators, skill-first gates, duplicate path policies)
- ~1500 lines of custom hook code

### What Gets Built

- done-gate Stop hook: ~20 lines
- verified.jsonl integration: ~50 lines
- Plugin source git tracking: one-time `git add`

### What Gets Adopted

- nah (`pipx install "nah[config,keys]"`)
- Built-in settings.json allow/deny/ask

---

## Interfaces Spec

This section is for LLMs and humans implementing the redesign. It defines what each component must consume, produce, and guarantee.

### 1. Permission Layer

#### 1.1 `nah`

**Purpose:** Decide whether a Bash or tool action is allowed, should ask, or must be blocked.

**Inputs:**
- tool type or action type
- command text or action payload
- working directory / target path when available
- configured policy

**Outputs:**
- `allow` | `ask` | `block`
- short reason string
- optional action category (`test`, `git`, `file`, `network`, `destructive`, `pkg`, etc.)

**Invariants:**
- deterministic for the same input + config on `allow` and `block` outcomes
- when the optional LLM resolver is enabled, `ask` outcomes are **non-deterministic** (a token-spending model decides) — pin the resolver off, or treat `ask` as non-reproducible
- destructive actions must never downgrade from `block` to `ask` or `allow`
- if classification is uncertain, prefer `ask` over `allow`

**Maturity note:** nah is `Development Status :: 3 - Alpha` (PyPI, v0.9.1, pre-1.0; 23 releases of churn). Treat it as a fast-moving external dependency: **pin the version**, and review classifier behavior on every nah version bump.

**Operational rule:** nah becomes authoritative for destructive-command classification **only after** Stage 3 proves it on this stack's actual command distribution (see Stage 3 — PowerShell-weighted). The settings.json `deny` hard floor (§1.2) is the Alpha hedge: an nah regression can over-block but can never *unblock* a denied destructive action.

#### 1.2 `settings.json`

**Purpose:** Express simple local rules without custom hook code.

**Inputs:**
- target path
- tool/action type
- ordered allow/deny/ask rules

**Outputs:**
- `allow` | `ask` | `deny`
- matching rule identifier or reason when available

**Invariants:**
- rules are simple and local, not behavioral heuristics
- path-oriented and project-specific rules belong here first
- custom code should not duplicate a rule that settings can express

**Hard-floor rule:** Per Claude Code's actual permission flow, a hook returning `allow` does **not** skip settings.json `deny` rules. settings.json `deny` is unconditional and overrides nah `allow`. Use settings.json `deny` for things that must never run regardless of nah (e.g., secret-exfiltration patterns).

#### 1.3 Effective permission decision

**Composition rule:**
- If either nah or settings says `block`/`deny`, effective decision = `block`
- Else if either says `ask`, effective decision = `ask`
- Else effective decision = `allow`

Note: this symmetric rule is correct for the *block* direction. settings.json `deny` cannot be overridden by nah — it is the hard floor (see 1.2).

**Reasoning rule for LLMs:**
- never override a `block`
- never silently convert `ask` into `allow`
- if the system cannot produce a reason inline, log enough context for later diagnosis

### 2. Completion Truth Layer

#### 2.1 done-gate Stop hook

**Purpose:** Gate explicit completion claims on evidence. (Honest framing: this is an **evidence-gate on completion phrases**, not a truth oracle — it cannot detect a liar who avoids the trigger words.)

**Trigger condition:** Model output contains a terminal completion claim such as `done`, `fixed`, `ready`, `implemented`, `all good`, `tests pass`, or `complete`. Scope to *terminal* completion sentiment, not bare substring, to limit false positives on turns like "the import is fixed" or "tests are complete in module X."

**Inspection scope:**
- `output_text` — the final assistant response (confirmed Stop hook payload field; already consumed by `Stop_fake_done_detector.py` and `cc-aca-authority/hooks/stop/stop_permission_stall.py`)
- changed file list from `git status` / tool logs
- latest verification command and result from tool logs or `verified.jsonl`

**Field fact (verified 2026-06-27):** The Stop payload exposes `output_text` and `stop_hook_active`. It does **not** expose `agentThinking` or any model-internal reasoning field — zero references across the plugin tree. Build the gate on `output_text`; do not assume a reasoning field exists, because it provably does not.

**Outputs:**
- pass through response unchanged, or
- block with a structured request for missing evidence

**Required evidence on completion claims:**
```text
Changed files:
Verification command:
Verification result:
Known remaining issues:
```

**Enforcement rule:** If required evidence is missing, the completion response **MUST be blocked**. This is non-advisory. The hook does not warn; it blocks.

**No-change case:**
If no files changed, the agent must explicitly say that no code change was needed and still provide the verification command and verification result.

**Invariants:**
- completion claims require evidence
- evidence must refer to the current task, not stale prior work
- the hook checks truthfulness of completion claims, not general code quality

### 3. Verification State Layer

#### 3.1 `verified.jsonl`

**Purpose:** Record which file states have been verified so later checks are idempotent.

**Location:** `P:/.claude/state/verified.jsonl`

**Record schema:**
```json
{"task_id":"abc","files":["x.ts"],"command":"npm test","exit_code":0,"timestamp":"...","hash":"...","mode":"strict"}
```

**Required fields:**
- `files`: files covered by the verification
- `command`: exact verification command run
- `exit_code`: verification result
- `timestamp`: when verification completed
- `hash`: content fingerprint of verified state (see modes below)
- `mode`: `fast` or `strict` (see below)

**Optional field:**
- `task_id`: useful when the same files are touched by distinct tasks in one session

**Hash modes:**
```text
Fast mode (ordinary source files):
    SHA256(filepath + mtime_ns + size)
    Faster; may miss content changes that preserve size + mtime.

Strict mode (control-system files):
    SHA256(filepath + file_content_hash)
    Slower; required for correctness on control-system paths.
```

**When to use strict mode:** hooks, policies, plugin files, settings, CI/build files, and any file touched during done-gate / control-system work.

**Do not** label mtime+size hashing as "collision resistant." It is fast, not cryptographic. Strict mode is the cryptographic option.

**Invariants:**
- append-only during a session
- a verification record is valid only for the file hashes it recorded
- modifying a covered file invalidates older verification for that file state

**Concurrency:** Multiple terminals write this file simultaneously. Writes must be atomic — one complete JSON record per line, newline-terminated, written via a single append that cannot interleave with another terminal's write. Readers must skip malformed/partial lines rather than crash. This is non-negotiable on this stack (multiple concurrent terminals).

**Retention rule:**
- rotate or compact periodically; the detector only needs records recent enough to answer whether the current file state has already been verified after its last modification

#### 3.2 Structural-change detector

**Purpose:** Decide whether the current changed state still needs verification.

**Question it must answer:**
```text
Have these changed files already been verified after their last modification?
```

**Question it must NOT answer:**
```text
Did anything structural happen somewhere in the session?
```

**Inputs:**
- changed files
- their latest modification times or hashes
- verified.jsonl records

**Outputs:**
- `verified`
- `needs_verification`
- optional explanation naming the unverified files

**Link to done-gate:** If the detector returns `needs_verification` for any file, the done-gate (Section 2.1) MUST refuse completion claims involving those files until a matching verification record exists in `verified.jsonl`. This closes the loop between truth and idempotency.

**Invariants:**
- file-state-based, not session-mood-based
- idempotent across turns
- should not nag once the same state has already been verified

### 4. Canonical Source and Cache Rules

#### 4.1 Plugin source directories

**Purpose:** Ensure worktrees include editable source-of-truth plugin files.

**Rule:** Source directories must be git-tracked.

**Invariant:**
- source is canonical
- cache is generated
- empty or stale source must never silently overwrite a known-good cache during sync/rebuild

#### 4.2 Cache rebuild behavior

**Purpose:** Rebuild generated plugin state safely.

**Preconditions before bump/rebuild:**
- verify source `hooks.json` exists
- verify source `hooks.json` is not empty or stale
- commit source changes before rebuild when practical
- create `cache/before_bump/` backup automatically before running `plugin-audit-and-fix.py`

**Operational warning:**
If `plugin-audit-and-fix.py --bump` performs bidirectional sync and treats source as canonical, stale source can overwrite valid cached dispatch.

**Rollback if sync overwrites good cache:** Restore from `cache/before_bump/` backup created before the bump. This backup is part of the Stage 7 workflow, not an afterthought.

**Note:** nah is a permission guard, not a build system. It does not fix plugin cache/versioning. The cache workflow above is the fix; do not expect nah to touch this layer.

### 5. LLM Operating Rules

An LLM working from this plan should follow these rules:

1. Do not claim completion without explicit evidence.
2. Treat source as canonical and cache as generated.
3. Prefer deleting redundant custom hooks over patching them, unless they uniquely provide one of the three required functions.
4. Run replacements in shadow mode before cutover.
5. When a permission decision is ambiguous, prefer `ask` over `allow`.
6. When verification status is ambiguous, prefer `needs_verification` over assuming verified.
7. Do not build local workarounds that add policy complexity unless the document explicitly approves them.

---

## Implementation Plan

**Stage order rationale:** The done-gate ships at Stage 2 (not Stage 5) because it is the highest-leverage, lowest-risk piece, has no dependencies on nah/settings/cache, and provides a working seatbelt while the old stack is torn down. Verification idempotency stays later; the done-gate starts on whatever evidence already exists (`git status`, tool logs) and gains the full `verified.jsonl` link when Stage 6 lands.

### Stage 0 — Snapshot Current State

**Before changing anything, capture the "before" picture.**

Deliverables:
- `git status --short`
- List of active hooks (`ls .claude/hooks/`)
- List of plugin source dirs
- List of cache dirs
- Current `settings.json` allow/deny/ask rules
- Sample blocked command transcript
- Sample allowed command transcript
- Subscribe to upstream issues #59643, #17789, #36035, #39328

**Why:** Your transcript shows cache/source/version confusion. Need clean baseline for comparison.

---

### Stage 1 — Inventory Hooks by Job

Build a classification table:

| Hook | Current Job | Keep? | Replace With | Notes |
|------|-------------|-------|--------------|-------|
| directory_policy | path/write rules | no | nah/settings.json | Was wrongly blocking Read |
| destructive_bash_validator | dangerous commands | no | nah | Avoid custom regex taxonomy |
| skill-first_gate | ritual enforcement | no | warning only | Too much friction |
| structural_change_detector | verification nag | yes | idempotent version | Needs verified.jsonl |
| done/stop hook | completion truth | yes/custom | custom | High leverage |

**Why:** Prevents deleting the wrong thing when hooks have overlapping responsibilities.

---

### Stage 2 — Add Done-Gate Stop Hook

**Ship this before any teardown.** No dependencies on nah/settings.json/cache.

**Trigger patterns:** done, fixed, ready, implemented, all good, tests pass, complete

**Required output:**
```text
Changed files:
Verification command:
Verification result:
Known remaining issues:
```

For control-system work, add:
```text
Rollback path:
```

**Initial evidence source:** Use whatever already exists at this stage — `git status` for changed files, transcript tool logs for verification command/result. The full `verified.jsonl` link arrives at Stage 6.

**Enforcement:** Block on missing evidence. Non-advisory.

**Why:** Seatbelt while tearing down old stack. The original problem ("agent claims done without evidence") is the most common failure mode; this gate is independent of every other stage.

---

### Stage 3 — Install nah in Shadow Mode

**Do not replace your stack yet. Run nah as a comparator.**

```bash
pipx install "nah[config,keys]"
```

For each Bash command, log:
- Existing stack decision (allow/ask/block)
- nah decision (allow/ask/block)
- Command category
- Mismatch (yes/no)

**Curated test set — PowerShell-weighted (this is a PowerShell-primary Windows stack; a Bash-only corpus proves nothing about deployment):**

Allow (PowerShell):
- `npm test`, `git status`, `git diff`, `Get-ChildItem`, `Get-Content package.json`, `Select-String foo`, `python plugin-audit-and-fix.py --bump <name>`

Ask (PowerShell):
- `npm install`, `pip install`, `Invoke-WebRequest`, writes to `.claude/**`, `hooks/**`, `plugin/**`, `Set-ExecutionPolicy`

Block (PowerShell — the cases that actually wreck a Windows repo):
- `Remove-Item -Recurse -Force .git`, `Remove-Item -Recurse -Force .`, `ri -recurse -force .`, `del /s /q *`, `git reset --hard`, `git clean -fdx`, `cmd /c rd /s /q`, `Get-Content .env`, `Get-Content $env:USERPROFILE\.aws\credentials`, `iex (irm https://...)`, `npm publish`

Also include the real Bash-via-git-bash commands your coders run (`rm -rf`, `cat .env`) so both shells are covered, but **the PowerShell set is the acceptance population, not an afterthought.**

**Acceptance criterion:**
```text
nah shadow must catch ≥100% of destructive cases on the PowerShell set
and over-block ≤3 routine interruptions per real coding session
```
The threshold is an *interruption budget* (measurable friction you actually feel), not a percentage pulled from thin air. If nah cannot classify the PowerShell block-set correctly, it stays advisory — do not promote it (see §1.1 Operational rule).

**Over-block fallback ladder (use in order, do not skip):**
1. Configure nah exemptions for the over-blocked patterns in nah config.
2. Express the rule in settings.json allow/deny/ask.
3. Change the workflow / command shape (e.g., use a script instead of an inline command nah misclassifies).
4. Retain a custom hook **only** as a documented last resort, naming which of the three questions (permission / truth / idempotency) it uniquely answers. Anything else is how the 13-hook mess recurs.

**Why:** Prove nah matches your solo-director expectations before making it authoritative.

---

### Stage 4 — Move Simple Rules to settings.json

Use Claude Code's native allow/deny/ask for boring project rules.

**Allow:**
- Read project files
- Edit normal source files
- Bash test/typecheck/grep/git status/git diff

**Ask:**
- Edit `.claude/**`, `hooks/**`, `plugin/**`, package/build/CI config
- Bash npm install/pip install/chmod

**Deny:**
- Known destructive commands
- Secret exfiltration patterns

**Why:** Custom code should not exist for rules the native permission system can express.

---

### Stage 5 — Disable Redundant Hooks

**Do not delete yet. Disable.**

Order:
1. Read/path blocking hooks (Read should be allowed by default)
2. Destructive Bash regex hooks (replace with nah if Stage 3 passed)
3. Skill-first gates (convert to warnings or remove)
4. Duplicate ownership/colocation/protected-file gates (keep only if nah/settings cannot express)

After each cluster:
- `/reload-plugins`
- Run smoke suite
- Record allow/block results
- Commit

**Why:** Gradual rollout with rollback points.

---

### Stage 6 — Add Idempotent Verification Log

Create `P:/.claude/state/verified.jsonl` (append-only):

```json
{"task_id":"abc","files":["x.ts"],"command":"npm test","exit_code":0,"timestamp":"...","hash":"...","mode":"strict"}
```

Structural-change detector logic:
```text
Have these changed files already been verified after their last modification?
```

**NOT:** "Did anything structural happen somewhere in the session?"

**Wire to done-gate:** Once `verified.jsonl` exists, the done-gate (Stage 2) MUST refuse completion for any file flagged `needs_verification` until a matching record exists. See Section 3.2.

**Hash modes:** fast (mtime_ns + size) for ordinary source; strict (content hash) for control-system files. See Section 3.1.

**Why:** Fixes the "nagging across turns" problem.

---

### Stage 7 — Git-Track Plugin Sources

One-time cleanup:
- `git add` plugin source directories
- commit them
- document canonical source locations

**Rules:**
- Source is canonical
- Cache is generated
- Never hand-edit cache as the durable fix
- Before bump/rebuild, verify source `hooks.json` is not stale or empty
- Commit source changes before rebuilding cache
- Create `cache/before_bump/` backup automatically before any bump

**bidirectional sync footgun:** If `plugin-audit-and-fix.py --bump` runs bidirectional sync making source canonical, an empty/stale source `hooks.json` overwrites the real cached dispatch. Verify before bumping; restore from `cache/before_bump/` if it happens.

**Why:** Worktrees include the files the agent edits.

---

### Stage 8 — Delete Old Hooks

**Cutover safety checklist — all must hold before deleting any hook:**
1. It has been disabled for at least 2 real coding sessions.
2. No missing protection was observed.
3. Its replacement (nah / settings.json / done-gate) is documented.
4. A smoke test covers the behavior it used to protect.
5. `git revert` restores the old behavior (delete-able commits are small and atomic).
6. **No other hook depends on its logs or state files.**

**First session post-deletion:** Run nah shadow in parallel as canary.

**Second session:** If no canary fired, turn off shadow.

**Delete in small commits:**
- `delete-read-policy-hooks`
- `delete-destructive-bash-regex-hooks`
- `delete-skill-first-gates`
- `delete-duplicate-path-policy-hooks`

**Why:** No giant "remove old policy system" commit. Gradual, observable, reversible. Note that absence of observed failure ≠ absence of missing protection — that's why the nah shadow canary runs through session 1.

---

## Upstream Bugs to Track

| Issue | Description | Impact on This Plan |
|-------|-------------|---------------------|
| #59643 | `permissionDecisionReason` not surfaced to model | Opaque block reasons until fixed upstream. Do not assume inline reason surfacing works; always log locally. |
| #17789, #36035, #39328 | Cache rotation breaks hook paths | Stage 7 may simplify when fixed. |

**Action:** Subscribed at Stage 0. Revisit plan when they ship.

---

## Key Design Rules

1. **Source canonical, cache generated** — Never edit cache directly as the durable fix
2. **Verify hooks.json before bump** — bidirectional sync is a footgun
3. **Rare blocks** — If blocks are common, agent learns to route around them
4. **Three-question gate** — Every hook must answer exactly one: permission? truth? idempotency?
5. **Shadow before cutover** — Prove replacement works before deleting old
6. **No advisory** — Done-gate blocks, does not warn. Permission decisions are enforced, not suggested.

---

## Expected Outcome

| Metric | Before | After |
|--------|--------|-------|
| Hook layers | 13 | 1 (nah) + 1 custom (done-gate) |
| Block reason visibility | Read logs | Best-effort inline via nah/hook response where Claude Code surfaces it (blocked by upstream #59643); always also written to structured local logs for diagnosis |
| Lines of custom hook code | ~1500 | ~70 (done-gate + verified.jsonl) |
| Cache rebuild friction | 4 manual steps, easy to forget version/source/cache sync | Explicit source-canonical workflow with pre-bump validation and `cache/before_bump/` backup (nah does not touch this layer) |
| Done claims without evidence | Unblocked | Blocked without verification |
| Worktree reachability | Partial (untracked sources) | Full (git-tracked) |

---

## Open Questions for Reviewers

1. **nah compatibility:** Does nah's action taxonomy cover your CSF NIP rules and project-root write patterns? If not, can they be expressed in settings.json?
2. **Done-gate trigger point:** Stop time vs PostToolUse time — which catches "done" claims more reliably in practice?
3. **Upstream bug workaround:** Build local inline-reason workarounds for #59643 now, or wait for upstream fix? (Current stance: wait; always log locally in the meantime.)
4. **Shadow mode duration:** Is one session of nah shadow sufficient, or should it run longer?

**Resolved:**
- ~~Done-gate placement:~~ Stage 2, before any teardown (no dependencies, highest leverage).
- ~~verified.jsonl schema:~~ Includes `task_id` (optional, for distinct tasks on same files) and `mode` (fast/strict) per Section 3.1.

---

## Falsification Conditions

This plan is wrong if:
- nah mis-classifies any PowerShell destructive case in Stage 3 (it then stays advisory, not authoritative)
- nah over-blocks beyond the interruption budget (more than ~3 routine interruptions per real coding session)
- Your custom rules cannot be expressed in nah + settings.json
- The done-gate false-positives on non-completion turns often enough to get rage-disabled
- verified.jsonl grows without bound (no TTL/rotation strategy)
- concurrent terminals corrupt `verified.jsonl` (no atomic-write / skip-malformed strategy)
- Deleting a hook reveals missing protection that nah didn't catch
- The hash algorithm misses real content changes on control-system files

**Evidence that would change the answer:**
- nah shadow mode mis-classifies a PowerShell destructive command, or over-blocks beyond the budget on your actual work
- nah ships a breaking Alpha change that alters the destructive classifier
- settings.json cannot express your project-specific path rules
- Structural-change detector has different verification semantics than assumed

**Resolved:**
- `agentThinking` is **not** in the Stop hook payload (verified across the plugin tree, 2026-06-27). Done-gate reads `output_text` only; no reasoning field. See Section 2.1.
