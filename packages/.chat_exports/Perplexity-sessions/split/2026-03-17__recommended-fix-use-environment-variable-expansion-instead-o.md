---
title: "'
  Recommended fix:

  Use environment variable expansion instead of hardcoded values:

● Update(C:\\Users\\brsth\"
date: "2026-03-17"
mode: "COPILOT"
uuid: "5e6429e2-9ff7-4466-a3ab-a8acd5538a88"
entry_count: 5
---

## Human

"
  Recommended fix:

  Use environment variable expansion instead of hardcoded values:

● Update(C:\\Users\\brsth\\.claude.json)
  ⎿  Error: File has been unexpectedly modified. Read it again before attempting to
     write it.

● Read 1 file (ctrl+o to expand)

● Update(C:\\Users\\brsth\\.claude.json)
  ⎿  Error: File has been unexpectedly modified. Read it again before attempting to
     write it.

● Let me use Python to fix this:

● Bash(python3 -c "
      import json…)
  ⎿  Fixed: API keys now use environment variable expansion instead of hardcoded v
     alues"

For Claude Code, is there a best practice fix? For this problem to avoid it? And if it happens to mitigate it? Or to deal with it via hook so that it doesn't slow us down?

## Assistant

This error is mostly a state/concurrency bug in Claude Code’s edit pipeline, not something you’re “doing wrong,” but you can reduce how often it happens and build hooks/workarounds so it doesn’t stall you.[1][2][3]

## What’s actually going on

- The Edit/MultiEdit tools track a “version” of the file they read; if the on-disk file’s mtime/contents differ when they go to write, they bail with “File has been unexpectedly modified. Read it again before attempting to write it.”[2][1]
- On Windows and with certain configs/hooks, that version check is currently buggy: users see the error even when they haven’t touched the file, and even when they read→edit immediately.[4][5][3][1][2]
- There are also known issues with multiple Claude Code instances fighting over the same `~/.claude.json` (no proper locking), leading to corruption and repeated “unexpectedly modified” failures.[6][7]

## Best‑practice prevention

To avoid getting into a broken state as much as possible:

- Avoid concurrent instances that share config  
  - Don’t run multiple Claude Code terminals or VS Code windows that all hit the same `C:\Users\...\ .claude.json` at once; this is explicitly called out as causing corruption and inconsistent state.[7][6]
  - If you *must* run multiple, give each its own config: e.g. different user profile or set `CLAUDE_CONFIG_PATH` to separate files per instance (if/when supported in your setup).

- Minimize out‑of‑band writes while Claude is editing  
  - If you manually edit a file in another editor after Claude read it, expect the next Edit to fail the version check by design.[8][2]
  - The “clean” pattern per file is: let Claude read, propose edits, apply; then you manually tweak afterward or trigger a fresh Read before more edits.

- Use stable, absolute paths on Windows  
  - Some reports show the error disappearing when users force Claude to operate only on full absolute Windows paths (drive letter + backslashes) for all tools.[5]
  - You can encode that expectation into your CLAUDE.md and prompts so it stops using relative/mixed paths.

- Keep `.claude.json` simple and valid  
  - Broken JSON or partially written configs can amplify these problems.[9]
  - Your change to use env var expansion instead of hard‑coded keys is good practice (keeps secrets out of the file), but it doesn’t *by itself* cause the error; the real risk is repeated concurrent rewrites to that same file.

## When it happens: fast mitigation patterns

If you’re mid‑flow and hit:

> Error: File has been unexpectedly modified. Read it again before attempting to write it.

use these patterns:

- “Read then edit again” micro‑macro  
  - Instruct Claude: “Use Read on that file again, then immediately apply the same edit with Edit/MultiEdit.”  
  - This usually works when the problem is just an out‑of‑date snapshot rather than a deeper corruption.[8][2]

- Fall back to Bash/Python patch commands  
  - Exactly what you already did for `.claude.json`: have Claude synthesize an idempotent patch script (Python, PowerShell, or sed‑style) that reads, transforms, and rewrites the file in one shot.[10][1][2]
  - Keep the script in the repo so it’s re‑usable (e.g. `scripts/patch_claude_config.py`), and your prompt becomes “Run our patch script with these args.”

- Restart the Claude Code session when it’s “stuck”  
  - Several reports note that once the internal state gets borked, *every* edit fails until you restart Claude Code or the specific environment.[11][1][2][8]
  - As a rule: if you see 2–3 consecutive failures on simple edits after a fresh Read, restart instead of fighting the state.

- Kill zombie tasks / watchers  
  - Some users fixed persistent “unexpectedly modified” errors by killing stray background tasks started by Claude Code (e.g. in Task Manager on Windows).[8]
  - In your workflow, that likely means killing extra terminals spawned by hooks/tools that might still be holding file handles.

## Using hooks so it doesn’t slow you down

Hooks are exactly the right place to put guardrails and auto‑workarounds, but you have to avoid making the state problem worse.[3][9]

Here are concrete hook patterns:

### 1. Protect `.claude.json` from direct writes

You generally don’t want Claude doing blind line edits on its own shared config file anyway.

- Add a PreToolUse hook that blocks Edit/Write when the target path matches `C:\Users\brsth\.claude.json` and returns an explanatory message.[9]
- Example (conceptually, adapting the docs’ “protect-files.sh” pattern): have a script that reads the JSON input, inspects `.tool_input.file_path`, and exits with code 2 when it matches `.claude.json`, with stderr like “Use the patch script instead of direct edits.”[9]

Then encode in CLAUDE.md something like: “Never edit `.claude.json` with Edit/MultiEdit; instead, run `python scripts/patch_claude_config.py`.”

### 2. Auto‑convert failing edits into patch commands

You can’t intercept the *error message* in a hook, but you can steer behavior:

- PreToolUse hook:  
  - On Edit/MultiEdit, if `file_path` is under `C:\Users\brsth` and matches some patterns (e.g. config, settings), *rewrite* the plan: tell Claude (via instructions in CLAUDE.md and a hook script) to generate a patch command instead of using Edit when the tool is likely to fail.  
- In practice, the fastest version for you is:  
  - In CLAUDE.md, define a rule: “If Edit fails with ‘File has been unexpectedly modified’ twice for a file, *stop using Edit* on that file and generate a Python/PowerShell script that performs the exact patch instead.”  
  - Because Claude sees the prior tool errors in context, it will follow this procedural rule reliably.

### 3. “Health‑check” hook for dangerous state

There are open GitHub issues documenting that certain versions/combinations produce systemic failures on every pre‑existing file.[12][1][11][3]

A pragmatic pattern:

- PreToolUse hook that runs a very fast “health check” script once per session (cached in an env var or sentinel file) that:  
  - Tries a no‑op write on a scratch file in a temp dir using Edit.  
  - If that fails with the same error pattern, the script prints guidance and optionally touches a sentinel that tells you (and your prompts) to avoid Edit entirely and rely on patch scripts for this session.  

You can then codify in CLAUDE.md: “If `EDIT_UNSTABLE` sentinel is present, never use Edit/MultiEdit; always use patch scripts.”

## Environment‑variable expansion pattern

Your “env var expansion instead of hardcoded keys” is a good baseline practice for `.claude.json` and other configs:

- Keep secrets out of the file and reference `%ANTHROPIC_API_KEY%` / `$Env:ANTHROPIC_API_KEY` instead.[13][9]
- Maintain a single `python` (or PowerShell) script that:  
  - Parses `.claude.json`  
  - Replaces any literal `api_key` values with environment placeholder strings  
  - Normalizes formatting to reduce spurious diffs (stable key order, newline convention).  

You can let Claude regenerate/re‑run that script whenever needed, instead of touching the config directly.

***

If you’re open to it, what OS‑level shape do you want: one “master” Claude Code instance with multiple projects, or multiple concurrent instances sharing the same home directory? That choice will drive whether we focus on isolating configs per instance vs. just hardening a single shared `.claude.json`.  

## Human

I have five plus cloud terminals working often in the same main repo sometimes in different work trees

## Assistant

Given that setup, the safest “best practice” is: one Claude Code *workspace* per worktree, with shared global config but no shared per‑workspace files, and clear rules that prevent a single file (like `~/.claude.json`) from being edited concurrently.[1][2][3][4]

## High‑level shape for 5+ terminals

- Treat each terminal as “Claude Code + one worktree” rather than “many Claudes sharing one tree.”[2][5][4][1]
- Keep the repo’s `.git` shared (worktrees), but isolate Claude’s *workspace state* per worktree; only the **global** config stays shared.[5][3][2]

A concrete layout (Windows‑friendly):

- `D:\proj\main` – main worktree  
- `D:\proj\wt-feature-a` – git worktree A  
- `D:\proj\wt-bugfix-x` – git worktree B  
- …each opened in its own terminal, each running `claude` from that directory.[4][1][2][5]

## Config strategy so `.claude.json` doesn’t thrash

Use the global config dir for shared stuff, but keep local settings per worktree:

- Set once in your shell profile (or Windows env):

  ```powershell
  $Env:CLAUDE_CONFIG_DIR = "C:\Users\brsth\.claude-global"
  ```

  so Claude uses `C:\Users\brsth\.claude-global\.claude.json` for global config and data.[6][3]

- Allow per‑worktree local settings: Claude will still create `.claude/settings.local.json` in each worktree; that’s good, because it prevents constant writes to the global file.[3][6]
- Freeze the global file:  
  - Treat `.claude-global\.claude.json` as “infra‑owned.”  
  - Never let Claude use Edit/MultiEdit on it; only adjust it via your Python patch script.  
  - Use a hook or a comment in CLAUDE.md that says: “Never edit `.claude.json` directly; instead run `python scripts/patch_claude_config.py`.”[7][6]

This limits how often any instance tries to write that file, which reduces concurrency races and “unexpectedly modified” errors.[8][9][10]

## Operational rules for many parallel agents

For 3–8 concurrent agents across worktrees, I’d adopt:

- Only parallelize state‑independent tasks  
  - It’s fine to do “refactor frontend in wt‑frontend” and “write tests in wt-tests” concurrently.[5][4]
  - Avoid having multiple agents change the *same* logical area or config, even if they’re in different worktrees, unless you explicitly plan to reconcile via git.

- One **Claude session per worktree directory**  
  - Start each session *from* the root of that worktree so its tools see a clean, isolated FS subtree.[1][2][5]
  - Don’t run multiple Claudes in the same worktree unless you really need to; that’s where edit‑version drift is worst.[11][12][8]

- Codify naming & intent  
  - Name worktrees by task (`feature-auth`, `bug-payments`, etc.) and mirror that in your terminal names.[2][4]
  - In CLAUDE.md, describe the role of each worktree if they’re long‑lived (e.g. “This worktree focuses on auth refactor, don’t touch billing here”).[13][4]

## Handling the “unexpectedly modified” error fast

Given your parallelism, I’d make the mitigation path *standardized* so you don’t think about it:

1. **Per‑file retry rule in CLAUDE.md**  
   - Add text: “If Edit/MultiEdit on any file fails with ‘File has been unexpectedly modified’ once, immediately re‑Read that file and retry once. If it fails twice, stop using Edit on that file and instead generate a Python/PowerShell patch script to apply the change.”[12][14][15][8]

2. **Central patch script pattern**  
   - Have a small `scripts/patch_file.py` that: path + regex/JSON patch → atomic write.  
   - Instruct Claude: “When patching config or shared infra files, always call `python scripts/patch_file.py` instead of Edit.”[15][16]

3. **Session reset rule**  
   - If you get 2–3 unexpected‑modified errors on simple edits right after fresh Reads in one terminal, just restart that Claude session instead of fighting it; folks report this clears bad in‑memory state.[14][8][11][15]

## Hook ideas tailored to your workflow

Two hooks that are low‑risk with many terminals:

- **PreToolUse guard on dangerous files**  
  - Block Edit/MultiEdit on global config (`.claude-global/.claude.json`) and any other shared infra file; return a clear message pointing to patch scripts.[7]

- **Optional “health check” on session start**  
  - Tiny script run via a hook the first time Edit is used in a session: try a no‑op change to a scratch file under the current worktree, revert it, ensure Edit works.  
  - If it fails with “unexpectedly modified,” print guidance: “Avoid Edit in this session; use patch scripts.”[17][12][7]

Those keep the problem from derailing you when one of your 5+ terminals gets into a bad state.

Would you be willing to centralize config with `CLAUDE_CONFIG_DIR` and treat each git worktree as a fully isolated Claude workspace? That’s the key lever that unlocks most of these safeguards.  

## Human

How do you make sure each git work tree is fully isolated? In my experience, Claude will still write outside the work tree.  What are the best practices for merging work trees back to mean?

## Assistant

You’re right: by default Claude will happily escape a worktree via Bash and global config, so “fully isolated” has to be enforced by you at the OS/config layer, not just by convention.[1][2][3]

## Keeping each worktree truly isolated

Claude has three main escape hatches: Bash (full user rights), the global config dir, and any explicit absolute paths you give it.[2][3]

To keep each worktree as isolated as possible:

- OS / container boundary (strongest)  
  - Run each Claude session in a sandbox that only binds that worktree plus a shared minimal `$HOME/.claude`.[4][3][2]
  - Examples others use:  
    - `bwrap` / Linux namespaces with `--bind "$WORKTREE" /workspace` and a restricted set of extra binds.[2]
    - Docker/WSL: mount one worktree as the container’s `/workspace`, mount a shared `.claude` if desired, and start `claude` there; the container user simply *cannot* see sibling worktrees.[4][2]

- File‑system permissions / ACLs  
  - Put different worktrees under separate OS users or restrict ACLs so your “Claude user” can only read/write the desired trees.[3][1][2]
  - That way, even if Claude tries `cat D:\proj\other-worktree\foo`, it gets EPERM.

- Claude permissions / settings  
  - Use `settings.json` / managed settings to deny access to paths outside the current project (as far as permissions allow): add `deny` entries for parent directories, or only allow a narrow set of dirs for tools.[5][3]
  - In CLAUDE.md, state explicitly: “Never use absolute paths outside this repository; never reference sibling worktrees or home-level files.” This doesn’t *enforce* isolation but makes violations rare.  

- Bash discipline  
  - Assume Bash is “unconfined root” for your user: any Bash command can read/write outside the worktree if the OS allows it.[3]
  - So:  
    - Prefer higher‑level tools (Edit, Write, MultiEdit) for file changes within the tree; avoid generic “run Bash to edit files” patterns.  
    - When you *do* use Bash, encode the rule in CLAUDE.md: “All Bash file paths must be relative, under `.`; if you think you need an absolute path, ask first.”  

Even if you don’t go all the way to containers per worktree, putting each worktree under its own directory subtree and tightening permissions around sensitive neighbors is the pragmatic minimum.[1][2][3]

## Making sure Claude doesn’t write outside the worktree

You can’t yet tell Claude “this is your root, everything else is forbidden” in one config flag, but you can approximate it:

- `.claude` directory behavior  
  - Today Claude always creates `.claude/` in the project root and this path is not configurable.[5]
  - That’s actually helpful for isolation: each worktree automatically gets its own `.claude` state dir; just don’t symlink or share those between worktrees.

- Global vs per‑project config  
  - Use a shared `CLAUDE_CONFIG_DIR` / global `.claude` for auth and high‑level defaults, but keep project‑specific behaviors in each worktree’s `.claude` and CLAUDE.md.[6][7][5]
  - Avoid editing the global config from within projects; treat it as immutable infra and adjust it only via a controlled script in a separate “admin” session.

- Permissions/deny rules for parent paths  
  - In your Claude settings, use permission guards (deny outside `D:\proj\wt-...`) so that Edit/Write and some tools are blocked above the worktree.[3]
  - This does *not* stop Bash from doing it, but it significantly reduces accidental cross‑tree writes.

- Hooks as guardrails  
  - PreToolUse hook that:  
    - Inspects any `file_path` arguments from Edit/Write/MultiEdit.  
    - Rejects if they resolve outside `$PWD` (e.g. normalized path starts with `..` or different root).  
  - Another hook could wrap Bash invocations: if the command contains suspicious absolute paths (`C:\Users\brsth` etc.), ask for confirmation in natural language instead of running it automatically.[8][3]

These won’t give you perfect jail‑like isolation, but combined, they get very close without containers.

## Best practices for merging worktrees back to main

From git’s perspective, worktrees are just multiple checkouts of branches; merging is “normal Git,” but your Claude‑heavy workflow suggests some extra discipline.[9][10]

Baseline Git flow:

1. Create worktree for a branch:  
   - `git worktree add ../proj-wt-feature feature/my-feature`.[10][9]
2. Work there, commit early and often.  
3. In main worktree (or a dedicated integration worktree):  
   - `git checkout main`  
   - `git pull`  
   - `git merge feature/my-feature` (or rebase first if you prefer).  
4. Once merged and pushed, remove the worktree:  
   - `git worktree remove ../proj-wt-feature`.[11][9][10]

Best practices tuned for parallel Claude sessions:

- Keep branches small and focused  
  - Each worktree/branch should correspond to a coherent change: one feature, one large refactor, etc.[11]
  - This reduces merge complexity and keeps Claude’s mental model for that worktree stable.

- Isolate cross‑cutting changes  
  - If Claude needs to do a giant repo‑wide mechanical change (e.g. renaming a core type), dedicate a single “bulk refactor” branch/worktree and pause conflicting branches until that’s merged.[12][11]

- Make merges human‑driven, Claude‑assisted  
  - Use Claude only as a merge assistant in *one* worktree (e.g. main) instead of letting multiple agents attempt overlapping merges.[11]
  - Pattern: you do `git merge feature/my-feature`, then let Claude help resolve conflicts in that one workspace.

- Clean up `.claude` and Claude‑generated files  
  - Ensure each worktree’s `.claude/` directory and any transient Claude outputs (scratch scripts, logs) are `.gitignore`d so they don’t generate noisy conflicts.[5]
  - Before final merge, you can even have a small script that removes or normalizes purely local Claude artifacts.

- Use an “integration worktree”  
  - Some people keep a dedicated worktree that tracks `main` and is used *only* for merges and releases.[9][11]
  - All feature branches merge into that; they don’t touch your “everyday dev” main checkout, which stays clean.

For you, I’d imagine: several worktrees for features with Claude doing heavy edits locally, plus a single main/integration worktree where you do merges and maybe a more tightly constrained Claude session for conflict resolution.

***

Do you want to go as far as containers/WSL per worktree for isolation, or would you prefer to stay at “single OS user with guardrails (permissions + hooks + conventions)”?  

## Human

We are not going to use containers.

## Assistant

Given no containers, the pattern is: keep a single Windows user, but enforce “per‑worktree sandboxes” via permissions, settings, and hooks, and keep merges strictly Git‑driven rather than Claude‑driven.[1][2][3][4]

## 1. Confining Claude to a worktree (without containers)

Claude can still *try* to go outside, but you can make that hard/annoying enough that it almost never happens.

Practical measures:

- Separate Claude *user* (optional but strong)  
  - Create a dedicated OS user (e.g. `claude`) and typically run Claude under that account (or a separate Windows profile). The OS then enforces what that user can see/write.[3]
  - Give that user full access to your repo tree and `.claude` dirs, but **no** access to other sensitive locations (SSH keys, unrelated projects, personal files).[3]

- Per‑project `.claude` is already isolated  
  - Each worktree gets its own `.claude` directory by default and there’s not yet a way to share it; that’s good for isolation.[5]
  - Don’t symlink `.claude` across worktrees, and don’t let Claude edit those files in other trees.

- “Soft root” via permissions/settings  
  - Use OS permissions to make directories above your repo read‑only or inaccessible to the Claude user where feasible.[3]
  - In `~/.claude/settings.json`, add deny rules for paths outside your dev tree, so default tools refuse to touch them even if accessible.[3]
  - In CLAUDE.md for each worktree, codify: “Only operate on files under this repo root; don’t use absolute paths outside this directory.”

- Hook to block edits outside `$PWD`  
  - Add a `PreToolUse` hook for `Edit|Write` that reads `.tool_input.file_path`, normalizes it, and exits 2 if it’s not under the current working directory.[1][6][7]  
  - Lightweight example (Python one‑liner form, adapted from hook docs):  

    ```jsonc
    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "Edit|Write",
            "hooks": [
              {
                "type": "command",
                "command": "python -c \"import json,sys,os; d=json.load(sys.stdin); p=d.get('tool_input',{}).get('file_path',''); p=os.path.abspath(p); cwd=os.path.abspath(os.getenv('CLAUDE_PROJECT_DIR','.') or '.'); sys.exit(0 if p.startswith(cwd+os.sep) else 2)\""
              }
            ]
          }
        ]
      }
    }
    ```  

    This blocks any attempt to edit a file that isn’t under the project root and returns a clear message.[7][1]

- Bash discipline hook  
  - Add another `PreToolUse` matcher for Bash that simply logs or warns when the command contains `C:\Users\` or `..` at the start of paths, and asks you to confirm before proceeding.[1][7]
  - This doesn’t fully prevent escape, but it catches most “oops” cases.

## 2. Handling global config (`.claude.json`) and shared files

Since you don’t want containers, treat the global config as “infra only” and keep it off the hot path:

- Use `CLAUDE_CONFIG_DIR` for global data  
  - Set `CLAUDE_CONFIG_DIR` to a stable global directory (e.g. `C:\Users\brsth\.claude-global`) so it’s separate from per‑project `.claude`.[2]
  - Put your API keys as env vars, not literals, and manage that file solely via your Python patch script (never with Edit/MultiEdit).[2][3]

- Protect shared files with hooks  
  - Extend the PreToolUse Edit/Write hook to deny paths matching global config, `.git/`, `.env*`, etc., similar to the docs’ “protect files” example.[8][7][1]
  - That stops “random session #3” from trying to rewrite `.claude.json` or `.env` while others are running.

- Use env var sourcing instead of file edits  
  - If you need Claude to see per‑worktree env, set `CLAUDE_ENV_FILE` to a script (per worktree) that exports env vars before each Bash command, rather than letting Claude edit `.env` directly.[2]

## 3. Best practices for merging worktrees back to main

Git worktrees themselves are straightforward; your main risk is AI‑generated conflicts and cross‑tree coupling.

Use this discipline:

- One branch per worktree, clear purpose  
  - Each worktree corresponds to one branch and one task (feature, refactor, bugfix).[9][10][11]
  - Claude can do large edits freely inside that worktree; you keep the blast radius bound to that branch.

- Main/integration worktree for merges  
  - Keep a primary worktree tracking `main` that you use for merges and releases only.[10][9]
  - Flow:  
    - Work in `wt-feature-x` → commit normally  
    - Switch to `main` worktree → `git fetch`, `git checkout main`, `git merge feature/x` (or rebase first) → resolve conflicts (with Claude’s help if you like) → test → push  
    - Remove feature worktree once merged.[11][9][10]

- Make Claude assist merge resolution, not orchestrate merges  
  - You run `git merge` yourself.  
  - Use Claude in the main worktree to interpret and resolve conflict hunks, but avoid having it run `git merge`/`rebase` or touch `.git` directly.[9][10]

- Ignore Claude’s local artifacts  
  - Ensure `.claude/`, temp scripts, logs, and other Claude artifacts are in `.gitignore` for every worktree.[5]
  - If Claude creates helper scripts you actually want, explicitly `git add` them with intention.

- Keep refactors linearized  
  - For repo‑wide mechanical changes, use a dedicated worktree/branch and merge that first, then rebase/merge smaller feature branches on top; this avoids multiple agents doing overlapping mass‑edits.[9]

That gives you: isolated-ish worktrees without containers and a merge path that keeps humans in charge of history.

Would you like a concrete `.claude/settings.json` + hooks snippet tuned for “single Windows user, multiple worktrees, minimal escape” that you can drop in and iterate?  

## Human

Yes.

## Assistant

Here’s a concrete, minimal setup you can drop in now: project‑level hooks that (a) block edits outside the worktree and to shared config, and (b) steer around the “unexpectedly modified” issue.[1][2]

## 1. Per‑project `.claude/settings.json`

Put this in each worktree’s `.claude/settings.json` (or generate it once and copy). It assumes:

- You run Claude from the worktree root.
- You keep global config in `C:\Users\brsth\.claude-global\.claude.json`.

```jsonc
{
  "disableAllHooks": false,
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "statusMessage": "Checking that edit target is safe",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-edit-guard.py"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "statusMessage": "Validating Bash command paths",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-bash-guard.py"
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "statusMessage": "Handling edit failure",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-edit-failure.py"
          }
        ]
      }
    ]
  }
}
```

Key points:

- `PreToolUse` for `Edit|Write` blocks edits outside the worktree and to `.claude-global/.claude.json`.[1][2]  
- `PreToolUse` for `Bash` warns on suspicious absolute paths.  
- `PostToolUseFailure` for `Edit|Write` catches the “unexpectedly modified” error and feeds a standard instruction back to Claude.[1]

## 2. `.claude/hooks/pre-edit-guard.py`

Create `.claude/hooks/pre-edit-guard.py` in each worktree, mark executable (on Windows you just need an assoc; Claude will run it via shell).[2][1]

```python
#!/usr/bin/env python
import json, sys, os

data = json.load(sys.stdin)
tool = data.get("tool_name")
ti = data.get("tool_input", {})
file_path = ti.get("file_path") or ""

# Normalize paths
cwd = os.path.abspath(data.get("cwd") or os.getcwd())
proj = os.path.abspath(os.getenv("CLAUDE_PROJECT_DIR") or cwd)
target = os.path.abspath(file_path) if file_path else ""

protected = [
    os.path.expanduser(r"~\\.claude.json"),
    os.path.expanduser(r"~\\.claude-global\\.claude.json"),
]

# Block writes to protected files
if target and any(os.path.samefile(target, p) for p in protected if os.path.exists(p)):
    sys.stderr.write(
        "Blocked: edits to global Claude config must be done via the patch script, "
        "not Edit/Write.\n"
    )
    sys.exit(2)

# Block edits outside project root
if target and not target.startswith(proj + os.sep):
    sys.stderr.write(
        f"Blocked: {target} is outside this worktree ({proj}). "
        "Operate only within this repository.\n"
    )
    sys.exit(2)

# Allow everything else
sys.exit(0)
```

Behavior:

- If Claude tries to Edit/Write global `.claude.json`, it’s blocked with a clear message.[1]
- If Claude tries to edit any file outside the worktree root, it’s blocked.[2][1]

## 3. `.claude/hooks/pre-bash-guard.py`

This one doesn’t fully forbid escape; it just makes dangerous paths noisy so you notice and can correct prompts.[1][2]

```python
#!/usr/bin/env python
import json, sys, re, os

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "") or ""

suspicious_patterns = [
    r"C:\\Users\\",        # absolute user paths
    r"\.\.[/\\\\]",        # parent traversal
]

if any(re.search(p, cmd, re.IGNORECASE) for p in suspicious_patterns):
    # Non-blocking warning: exit!=2 so tool still runs
    sys.stderr.write(
        "Warning: Bash command uses absolute or parent paths. "
        "Prefer paths under the current worktree only.\n"
    )
    # Exit 1: non-blocking, stderr visible in verbose mode
    sys.exit(1)

sys.exit(0)
```

- This keeps you fast, but highlights when Claude is about to reach outside the tree.[page:1][page:2]  
- If you want stricter behavior, change `sys.exit(1)` to `sys.exit(2)` to outright block.[page:2]

## 4. `.claude/hooks/post-edit-failure.py`

Standardizes handling of the “File has been unexpectedly modified. Read it again…” error.[page:1]

```python
#!/usr/bin/env python
import json, sys

data = json.load(sys.stdin)
tool = data.get("tool_name")
err = (data.get("error") or "").lower()

# Only care about Edit/Write failing with the specific error
if tool in ("Edit", "Write") and "unexpectedly modified" in err:
    msg = (
        "Edit/Write failed because the file was unexpectedly modified.\n"
        "Instruction to Claude: Re-Read the file, then either:\n"
        "  1) Retry the edit once, or\n"
        "  2) If it fails again, stop using Edit on this file and instead "
        "generate a Python or PowerShell patch script that applies the change.\n"
    )
    # This becomes feedback to Claude; exit 0 so failure is still reported
    sys.stderr.write(msg)

sys.exit(0)
```

Effect:

- Whenever Edit/Write fails with that error, Claude sees a deterministic “recipe” for what to do next, without you having to remember it each time.[page:1][page:2]  

## 5. Global `~/.claude/settings.json` (optional)

If you want these guards across *all* projects, move the `hooks` block to `~/.claude/settings.json` and keep project‑specific tweaks in `.claude/settings.json`.[page:2]

Example minimal global:

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-edit-guard.py"
          }
        ]
      }
    ]
  }
}
```

Then per‑project, you only configure Bash behavior or more specific protected files.

***

Do you want to bias toward *strict* mode (block Bash outside the worktree entirely) or keep the current “warn but allow” approach for Bash and only hard‑block Edit/Write?  
