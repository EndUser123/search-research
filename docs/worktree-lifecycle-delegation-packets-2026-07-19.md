# Worktree Lifecycle — Delegation Packets (2026-07-19)

**Purpose:** Three independent, non-yt-is tasks that close operational gaps in the worktree-lifecycle rollout (PRs 1–5 just shipped to cc-skills-sdlc + yt-is pilot). Each packet is self-contained: a fresh agent can execute without yt-is context.

**Background (one paragraph):** The `cc-skills-sdlc` plugin at `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc` just landed 4 PRs implementing a worktree-lifecycle management layer: PR 1 (`96c146a`) fixed latent bugs in `worktree_safety.py`; PR 2 (`07d2da3`) extracted `safe_delete_branch` into a new `worktree_lifecycle.py`; PR 3 (`7db70a0`) added `preflight.py` with 8 gating checks; PR 4 (`8617d0b`) added the `worktree_cleanup.py` CLI + `handoff_sync.py`. yt-is (`P:/packages/yt-is`) is the pilot package with a policy file (`worktree-policy.toml`) and a PreToolUse hook that blocks raw `git worktree` invocations. The design doc is at `P:/docs/worktree-lifecycle-design.md`. Unit tests pass; the gaps below are operational/integration verification, not bugs.

---

## Packet A — End-to-end CLI test of `worktree_cleanup.py`

**Goal:** Prove the CLI works on a real temp repo (not just unit tests). The unit tests cover each function in isolation; this exercises the full `remove` flow including preflight + branch delete + worktree remove.

**Scope:** cc-skills-sdlc plugin only. No yt-is involvement. No production repos touched — use a fresh temp repo.

**Prerequisite reads (do not skip):**
1. `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_cleanup.py` (the CLI)
2. `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/preflight.py` (what `cmd_remove` calls first)
3. `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_lifecycle.py` (`safe_delete_branch` helper)

**Steps:**

```powershell
# 1. Create a fresh temp repo with one commit
$tmp = New-Item -ItemType Directory -Path "$env:TEMP\wt-e2e-$(Get-Random)" -Force
git -C $tmp init -q
git -C $tmp config user.email "t"
git -C $tmp config user.name "t"
Set-Content -Path "$tmp/seed.txt" -Value "seed"
git -C $tmp add -A
git -C $tmp commit -qm "base"

# 2. Create a worktree + branch (clean state)
$wt = "$tmp\wts\feat-test"
New-Item -ItemType Directory -Path "$tmp\wts" -Force | Out-Null
git -C $tmp worktree add -b feat/test $wt HEAD

# 3. Run the CLI's preflight command
python P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_cleanup.py preflight $wt --repo $tmp --branch feat/test

# 4. Detach HEAD (so BRANCH_IN_USE doesn't block)
git -C $wt checkout --detach HEAD

# 5. Run the CLI's remove command
python P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_cleanup.py remove $wt --repo $tmp --branch feat/test
```

**Acceptance criteria:**
- Step 3: `preflight` exits 0 (no BLOCK findings) after detach in step 4
- Step 5: `remove` exits 0 and the worktree directory is gone
- The branch `feat/test` is deleted (since reachable from main)
- No errors in stderr

**Variation (auto_tag path):**
- Create a divergent branch (commit on top of HEAD in the worktree)
- Run `remove $wt --repo $tmp --branch feat/test --auto-tag`
- Verify a `backup/feat-test-<timestamp>` tag was created and points at the divergent tip

**Output format:** Plain text report with:
- Exit codes for each step
- Any findings from `preflight`
- Final state of the temp repo (worktree list, branch list, tag list)
- One-line verdict: PASS / FAIL

**What NOT to touch:**
- Any file under `P:/packages/yt-is/`
- Any file under `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/` (read-only)
- Any production repo (only temp dirs under `$env:TEMP`)

---

## Packet B — `/plan` suggestion rule behavioral verification

**Goal:** Verify the `/plan` suggestion rule (added to `~/.grok/AGENTS.md` on 2026-07-18) actually fires in a fresh Grok session. The rule says: "when ≥2 of 6 triggers fire (or trigger 2 alone), surface plan mode as a named option in the recommendation."

**Scope:** Global Grok rules only. No package-specific work.

**Prerequisite reads:**
1. `~/.grok/AGENTS.md` — find the section `## /plan (plan mode) suggestion rule`
2. `P:/.data/wiki/concepts/plan-suggestion-rule.md` — the worked example with the trigger conversation pattern

**Test prompt (use this verbatim in a fresh Grok session):**

> "I have two worktrees on yt-is with overlapping C1 contracts and an unresolved merge. Before I do anything, what do you suggest for cleanup?"

**Expected behavior (PASS criteria):**
- The response contains a **named plan-mode option** (phrase matching `enter plan mode` / `plan mode` / `produce a durable plan at <path>`) as one of ≥2 options
- The selection criterion is stated (why plan mode wins on this ask)
- Plan mode is NOT presented as a yes/no "plan first?" question (that's the old anti-pattern)

**Negative test (run immediately after):**

> "I have two worktrees on yt-is with overlapping C1 contracts and an unresolved merge. Before I do anything, what do you suggest for cleanup? Go ahead and do it."

**Expected behavior (PASS criteria for the negative test):**
- Plan mode is **NOT** surfaced (the approval language "go ahead and do it" suppresses it per the rule's guards)
- The response proceeds directly to implementation or proposes a single concrete action

**Output format:**
- Verbatim copy of both responses (with timestamps)
- For each: PASS / FAIL with the specific phrase that triggered the verdict
- If FAIL: identify which rule section in `~/.grok/AGENTS.md` should have fired and didn't

**What NOT to touch:**
- Any file (read-only verification)
- Any package or repo

---

## Packet C — Plugin mutation checklist completion for PRs 1–4

**Goal:** Complete the remaining steps of the `cc-skills-sdlc` plugin mutation checklist for the four PRs that just shipped. The version was bumped (1.0.230 → 1.0.234 by a parallel agent); the cache rebuild and CHANGELOG entries are what's missing.

**Scope:** cc-skills-sdlc plugin only. No yt-is.

**Prerequisite reads:**
1. `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/CLAUDE.md` — the "Hook-Work Contract" section and "Plugin file changes trigger the mutation checklist where applicable"
2. `P:/.claude/CLAUDE.md` — the "Plugin Mutation Checklist" (6 steps)
3. `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/.claude-plugin/plugin.json` — current version (1.0.234)
4. `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/CHANGELOG.md` — current state

**Steps:**

1. **Verify version is current.** `plugin.json` should show `1.0.234`. If not, bump to `1.0.234`.

2. **Cache rebuild.** Run:
   ```powershell
   python P:/packages/.claude-marketplace/plugins/cc-skills-utils/scripts/plugin-audit-and-fix.py --bump cc-skills-sdlc
   ```
   (With `--marketplace-root P:/packages/.claude-marketplace` if detection fails.) Verify the new cache dir exists and `hooks.json` in the cache matches the source.

3. **CHANGELOG entries.** Add entries for:
   - `96c146a` — PR 1: `worktree_safety.py` bugfix (import shutil + safe branch deletion + --force documentation)
   - `07d2da3` — PR 2: `worktree_lifecycle.py` + `RepoPolicy` + `safe_delete_branch` extraction
   - `7db70a0` — PR 3: `preflight.py` with 8 gating checks + Windows process scan
   - `8617d0b` — PR 4: `worktree_cleanup.py` CLI + `handoff_sync.py` sentinel-block generator

   Format: `[1.0.234] - 2026-07-19` section with the four entries under "Added" / "Changed" / "Fixed" as appropriate.

4. **Verify runtime.** After cache rebuild, run the existing test suite:
   ```powershell
   cd P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go
   python -m pytest tests/test_worktree_lifecycle.py tests/test_worktree_safety.py tests/test_preflight.py tests/test_worktree_cleanup.py tests/test_handoff_sync.py -q
   ```
   Expected: 61 passed, 2 skipped.

5. **Verify the commit scope.** Run `git status --short` immediately before committing. The `plugin-audit-and-fix.py` script stages files mid-run, so inspect the staged set, not your intent.

**Acceptance criteria:**
- Cache dir exists for version 1.0.234
- CHANGELOG.md has entries for all four PRs
- Tests still pass (61 passed, 2 skipped)
- One commit: `chore(cc-skills-sdlc): mutation checklist for PRs 1-4 (cache rebuild + CHANGELOG)`

**What NOT to touch:**
- Any file under `P:/packages/yt-is/`
- The source files for PRs 1–4 (they're already committed and pushed; this is just checklist completion)
- The plugin's hook wiring (the cache rebuild is mechanical, not a re-wiring)

---

## How to use these packets

Each packet is independent. They can run in parallel (different agents, different terminals) or serially. None requires the others to complete first.

**Recommended execution:**
- Packet A (CLI test): spawn a general-purpose subagent with the packet as its prompt
- Packet B (`/plan` rule verification): requires a fresh Grok session (not a subagent — the subagent inherits the parent's context, which defeats the "fresh session" requirement)
- Packet C (mutation checklist): spawn a general-purpose subagent; mechanical, well-specified

**Reporting back:**
Each packet should produce a one-paragraph verdict (PASS/FAIL + evidence). If FAIL, identify the specific gap and the smallest fix. Do not attempt fixes beyond the packet scope; report back and let the orchestrator decide.

---

## Origin

Written 2026-07-19 by Grok Build session `019f7653-7598-79e0-a0c3-1161f9c0b793` (terminal `console_aa25af78-8c68-4f72-9ff5-489b78d25ece`). Author: Grok M3. Triggered by user request to identify hook-adjacent delegation candidates that are NOT yt-is-related.