# Second-Opinion Review: yt-is Worktree Lifecycle Handoff

**Reviewer:** Antigravity (Gemini 3.5 Flash)  
**Date:** 2026-07-19  
**Review Target:** [yt-is-handoff-2026-07-19.md](file:///P:/docs/yt-is-handoff-2026-07-19.md)  
**Status:** Complete  

---

## 1. Primary Question 1: What should happen next and proposed PR ordering?

### Recommendation
Reject the proposed value-by-effort ordering in the handoff (§8: `PR 2 → PR 5 → PR 3 → PR 4`). Instead, execute the remaining work in strict dependency order: **PR 2 → PR 3 → PR 4 → PR 5**. 

### Rationale
- **Dependency Mismatch:** Handoff §4.2 states that PR 5 (yt-is policy and sync) has a dependency on `handoff_sync.py` which is built in PR 4. Additionally, PR 4 (§4.4) depends on both the PR 2 library and PR 3 preflight modules.
- **Logical Flow:** PR 5 implements the automated `HANDOFF.md` sync block replacement. If executed before PR 4, the sync scripts (`handoff_sync.py` and `worktree_cleanup.py`) do not exist on disk, meaning the policy configuration is dead code and cannot run.
- **Corrected Path:**
  1. **PR 2:** Extract the `safe_delete_branch` library helper to [worktree_lifecycle.py](file:///P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_lifecycle.py).
  2. **PR 3:** Implement the [preflight.py](file:///P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/preflight.py) checks (locks, processes, and branch reachability).
  3. **PR 4:** Implement [worktree_cleanup.py](file:///P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_cleanup.py) CLI and [handoff_sync.py](file:///P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/handoff_sync.py).
  4. **PR 5:** Deploy [worktree-policy.toml](file:///P:/packages/yt-is/worktree-policy.toml) and trigger automated sync in `yt-is`.

---

## 2. Primary Question 2: Missing items and under-weighted risks

### Risks Missed & Under-Weighted
1. **The CLI-less Block Gap (High Friction):** Handoff §3 states that the pilot Hook blocks raw `git worktree` commands by default. However, since the alternative CLI ([worktree_cleanup.py](file:///P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_cleanup.py)) does not exist yet (PR 4), all worktree operations are blocked unless developers/agents manually apply the bypass environment variable `GO_WORKTREE_SAFETY_BYPASS=1` (§5.1). This creates high immediate friction that is under-weighted in the handoff.
2. **Plugin Caching/Rebuild Risk:** Handoff §5.3 defends skipping the `cc-skills-sdlc` version bump because it is a script change. However, if the IDE uses cached plugin directories, other terminals or concurrent agent sessions may run the stale version of [worktree_safety.py](file:///P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_safety.py) (lacking the `shutil` import and the safe reachability-check fixes from PR 1). Skipping this bump violates the mutation checklist rule in the plugin's [CLAUDE.md:L113](file:///P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/CLAUDE.md#L113).
3. **Sandbox Configuration Blocker (Unreported):** During this review, execution of all shell commands (`run_command`) failed due to a sandbox configuration mismatch: `readwrite P:\worktrees\*: globs not supported`. This prevents running unit tests (`pytest`) or git commands inside the sandbox. Future agents will be blocked from executing the PR plan until this configuration issue is resolved.
4. **PowerShell Process Scan Portability:** The preflight scan (§E, `_check_win32_processes`) relies on Windows PowerShell `Get-CimInstance`. While it is correctly guarded by `os.name != 'nt'` check, it fails to inspect Windows processes if run under a WSL environment (where `os.name` resolves to `posix` but the underlying Windows processes hold the files).

---

## 3. Primary Question 3: Should we keep going or stop here?

### Recommendation
**Keep going.** Do not stop.

### Rationale
- Stopping now leaves the repository in a "half-enforced intermediate state": the blocking hook is active in `yt-is` but the CLI wrapper to manage worktrees is unimplemented.
- This is a direct violation of the [root-cause-program.md](file:///P:/packages/yt-is/docs/operations/root-cause-program.md) "Ship order" mandate: **"Do not leave half-enforced intermediate states if avoidable."**
- The remaining tasks (PR 2 through PR 5) are well-defined, and the design document is fully approved. Implementing them completes the lifecycle layers and removes the CLI-less block friction.

---

## 4. Secondary Questions (4, 5, 6)

### 4. Should the unpushed commits be pushed?
- **Recommendation:** No, hold off on pushing the 24 commits in `yt-is` and 13 commits in `cc-skills-sdlc`.
- **Rationale:** Because the sandbox configuration error blocks command execution, we cannot verify that these commits pass the full test suite in a clean container. Keep them local until the sandbox is unblocked and tests are verified.

### 5. Should PR 2 and PR 5 be parallelized?
- **Recommendation:** No, they must be run serially.
- **Rationale:** PR 5's automated sync relies on the sync scripts written in PR 4, which in turn depends on the library modifications in PR 2. Parallelizing them would result in untestable, speculative code additions.

### 6. Is the policy design right for a solo-dev workflow?
- **Recommendation:** Yes, the multi-agent registry design (isolated by Terminal ID) is correct.
- **Rationale:** Even in a solo developer environment, the workspace is accessed by concurrent agent instances and terminals. Without terminal-level isolation and lock checking, concurrent agent runs could easily collide or prune active directories.

---

## 5. Concrete Next Steps (Ordered)

1. **Fix Sandbox Configuration:** Remediate the glob permission error in the environment sandbox setup (`readwrite P:\worktrees\*`) to restore command execution.
2. **Execute PR 2:** Extract the `safe_delete_branch` function and build the `RepoPolicy` structures. Bump the plugin version in `plugin.json` to `1.0.231` and rebuild the cache.
3. **Execute PR 3:** Implement the Win32 process check, lock detection, and branch reachability tests in `preflight.py`.
4. **Execute PR 4:** Build the `worktree_cleanup.py` CLI and `handoff_sync.py` drivers.
5. **Execute PR 5:** Deploy `worktree-policy.toml` and enable the automated `HANDOFF.md` sync block.
6. **Verify and Push:** Run `pytest` on both packages. Once verified, push all accumulated commits.

---

### MATERIAL DISAGREEMENTS
We have material disagreements with the handoff document regarding the PR rollout sequence (§8: ordering PR 5 before PR 3/PR 4 violates dependency constraints (§4.2)), and the decision to skip the plugin version bump (§5.3: ignoring the version bump violates [CLAUDE.md:L113](file:///P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/CLAUDE.md#L113) and risks caching old, buggy script versions in active IDE sessions).
