---
current_session_id: 019f9488-2a86-7bf1-ae6f-eeb341ec7095
thread_id: session-observations-20260724
parent_handoff_path: none
status: CLOSED
created: 2026-07-24
---

# Session Observations — 2026-07-24

## Session topic

Epistemic-integrity enforcement design + Stop-hook receipt system implementation for Grok Build on Windows 11.

## Observations

### 1. Stop-hook receipt system is operationally safe in shadow mode
**Description:** PostToolUse receipts with worktree identity + file fingerprints work correctly under live multi-session conditions. Zero unsafe allows across 4 live sessions + 17 controlled scenarios. The old gate's `stop_hook_active` branch already handles prose-only responses, so the friction-reduction value is narrower than initially assumed.
**Source:** session 019f9488, live shadow data from sessions 019f94ac/019f94c9/019f94d7.

### 2. INTEGRITY_AUTHORITY is not achievable on this host without external infrastructure
**Description:** The model shares the same user identity as the hook process. Every file the hook can write, the model can write via 10 distinct vectors. HMAC with file-stored keys provides zero boundary. The one path to integrity authority requires a protected remote (branch-protected git or external signing service).
**Source:** session 019f9488, B2 adversarial write matrix (10/10 vectors forge authority).

### 3. `summary.json` is model-writable — cannot serve as identity authority
**Description:** Investigated using `summary.json.git_root_dir` as a cache for repository identity. Proven model-writable (overwrote + restored during probe). Payload `cwd` is not always equal to `git show-toplevel` (subagent worktree sessions have divergent cwd). Only safe optimization: combine 3 git subprocess calls into 1 (165ms → 51ms).
**Source:** session 019f9488, host metadata identity investigation.

### 4. Worktree identity must derive from Git metadata, not path or session metadata
**Description:** `git-common-dir` (repository) + `git-dir` + `show-toplevel` (worktree) is the correct identity hierarchy. `git worktree move` changes `show-toplevel` but not `git-dir`; worktree recreation at same path may keep same `git-dir` name. The fingerprint check on file content is the ultimate defense against stale state.
**Source:** session 019f9488, worktree identity resolution + red-team F3/F7.

### 5. The old Stop gate's false-positive friction comes from `.py` files in temp directories
**Description:** Writing throwaway analysis scripts in `P:/tmp/` triggered the code-modification gate because `_is_code_file` returns True for `.py` extensions regardless of path. Fixed by adding `_is_excluded_path` for `P:/tmp/` and hook state dir. The red-team found the fix is asymmetric (receipt writer doesn't apply the same exclusion) — fixed in the 4-bug patch set.
**Source:** session 019f9488, Stop hook feedback on temp scripts + red-team RC-1.

### 6. `/local:red-team` converted from overlay to standalone skill
**Description:** The workspace red-team skill was an overlay extending the now-disabled plugin. Converted to standalone with inlined procedure. Plugin `red-team` disabled in `config.toml [plugins] disabled`.
**Source:** session 019f9488, skill lifecycle maintenance.
