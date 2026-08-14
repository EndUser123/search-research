---
title: "in claude code on windows 11, does this proposal make optimal sense?
'
● Symptom

  User's claim: Stop hook failed wi"
date: "2026-05-02"
mode: "CONCISE"
uuid: "df922d90-f5cd-4346-845e-c25b9e47eb9f"
entry_count: 5
---

## Human

in claude code on windows 11, does this proposal make optimal sense?
"
● Symptom

  User's claim: Stop hook failed with ImportError: attempted relative import with no known parent package
  Observed behavior: execution_hooks.py fails when invoked as a subprocess via hooks.json command

  Evidence

  ┌──────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────┐
  │          Source          │                                              Finding                                              │
  ├──────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ hooks.json:8,18          │ Commands use python "$CLAUDE_PLUGIN_ROOT/src/skill_guard/execution_hooks.py" — file path, not     │
  │                          │ module invocation                                                                                 │
  ├──────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ execution_hooks.py:47    │ from .execution_runtime import ... — relative import                                              │
  ├──────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ execution_hooks.py:32-41 │ sys.path manipulation adds source dirs, but doesn't establish __package__                         │
  └──────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────┘

  Executed Path

  1. Claude Code Stop hook fires → reads hooks.json
  2. hooks.json entry for Stop: "python \\"$CLAUDE_PLUGIN_ROOT/src/skill_guard/execution_hooks.py\\" stop_main"
  3. Python starts as __main__, no __package__ set
  4. execution_hooks.py line 47: from .execution_runtime import ...
  5. . prefix requires a package context → ImportError: attempted relative import with no known parent package

  Alternative Hypothesis

  H2: The file should be invoked as a module instead —npython -m skill_guard.execution_runtimebwould_setc__package__,nbutchooks.json
   uses a file path.

  Falsifierile should be invoked as a module instead — python -m skill_guard.execution_runtime would set __package__, but hooks.json

  The error is ImportError: attempted relative import with no known parent package. Relative imports (.) require __package__ to be
  set.iNoeamount of sys.path manipulation can substitute for that. H1 disproved.

  The hookrrunsIasoatfiler(execution_hooks.py),inotra module. H2ois theeactualkfix.—Rbuttthe command formatqinrhooks.jsoneis thebe
  root constraint.

  Root Causeuns as a file (execution_hooks.py), not a module. H2 is the actual fix — but the command format in hooks.json is the
     t    s    n
  Soft constraint — The hooks.json entry uses python "$CLAUDE_PLUGIN_ROOT/src/skill_guard/execution_hooks.py" (file path). When
  Pythonaruns a file directly, __package__ is None, making relative imports impossible.

  Thetsys.pathisetupTat lines.32-41eisrcorrectpforoabsoluteDimportsNbutOthercodeiusesurelativeuimportsoinstead.file path). When
                 i e   r          a     _

  H1: The sys.path setup creates a package context — Unlikely. Adding to sys.path doesn't establish __package__; it
  only changes import resolution.

  H2: The file should be invoked as a module instead — python -m skill_guard.execution_runtime would set
  __package__, but hooks.json uses a file path.

  Falsifier

  The error is ImportError: attempted relative import with no known parent package. Relative imports (.) require
  __package__ to be set. No amount of sys.path manipulation can substitute for that. H1 disproved.

   uses a file path.

  Falsifier

  The error is ImportError: attempted relative import with no known parent package. Relative imports (.) require __package__ to be
  set. No amount of sys.path manipulation can substitute for that. H1 disproved.

  The hook runs as a file (execution_hooks.py), not a module. H2 is the actual fix — but the command format in hooks.json is the
  root constraint.

  Root Cause

  Soft constraint — The hooks.json entry uses python "$CLAUDE_PLUGIN_ROOT/src/skill_guard/execution_hooks.py" (file path). When
  Python runs a file directly, __package__ is None, making relative imports impossible.

  The sys.path setup at lines 32-41 is correct for absolute imports but the code uses relative imports instead.

  Fix

  Replace .-prefixed imports with absolute imports that match the sys.path setup:

  # Before (line 47):
  from .execution_runtime import ...

  # After:
  from skill_guard.execution_runtime import ...
  from skill_guard.utils.terminal_detection import detect_terminal_id

  P:/packages/skill-guard/src is already on sys.path via the setup block (line 41), so skill_guard.execution_runtime resolves
  correctly.

  Verification

  1. Apply fix to P:/packages/skill-guard/src/skill_guard/execution_hooks.py
  2. /reload-plugins
  3. Run a skill with execution contracts and trigger Stop — hook should no longer emit ImportError
  ⎿  Stop says: ADVISORY: Response does not mention any of the 17 items from the user's structured list. Consider whether the
     investigation covered the intended entities.

● Ran 9 stop hooks (ctrl+o to expand)
  ⎿  Stop hook error: Failed with non-blocking status code: Traceback (most recent call last):
    File "P:\\packages\\.claude-marketplace\\plugins\\skill-guard\\src\\skill_guard\\execution_hooks.py", line 47, in <module>
      from .execution_runtime import (
      ...<3 lines>...
      )
  ImportError: attempted relative import with no known parent package

✻ Cogitated for 2m 53s

❯ is that the optimal solution?

● Bash(cmd /c "mklink /J P:\\\\packages\\\\.test-pi-src P:\\\\packages\\\\skill-guard" 2>&1 && ls -la
      "P:/packages/.test-pi-src/src/skill_guard/" 2>&1 | head -5)
  ⎿  PreToolUse:Bash hook error                                     ⎿  Failed with non-blocking status code: Traceback (most recent
                                                                       call last):
  ⎿  Microsoft Windows [Version 10.0.26200.8246]
     (c) Microsoft Corporation. All rights reserved.

     P:\\packages\\skill-guard>ls: cannot access 'P:/packages/.test-pi-src/src/skill_guard/': No such file or directory

  Listed 1 directory (ctrl+o to expand)
  ⎿  PreToolUse:Bash hook error                                     ⎿  Failed with non-blocking status code: Traceback (most recent
                                                                       call last):

● No. The optimal solution is changing the hooks.json command format, not the imports.

  Why: The hook command uses python "$CLAUDE_PLUGIN_ROOT/src/skill_guard/execution_hooks.py" (file path). This makes Python treat it
   as __main__ with no package context. Switching to module invocation fixes this at the source:

  "command": "python -m skill_guard.execution_hooks pre_tool_use_main"

  Why this is better than changing imports:
  - Matches how pip-installable packages are meant to be invoked
  - Keeps relative imports intact (they're correct for the module structure)
  - P:/packages/skill-guard/src is already on sys.path via the path setup block, so -m skill_guard resolves correctly

  Falsification condition: This would be wrong if $CLAUDE_PLUGIN_ROOT/src is not a valid module path (non-existent, not in
  sys.path). But the path setup block confirms P:/packages/skill-guard/src exists and gets prepended, so python -m skill_guard
  works.

  Want me to apply this fix to P:/packages/.claude-marketplace/plugins/skill-guard/hooks/hooks.json?
  ⎿  Stop says: ADVISORY: Response does not mention any of the 17 items from the user's structured list. Consider whether the
     investigation covered the intended entities.

● Ran 9 stop hooks (ctrl+o to expand)
  ⎿  Stop hook error: Failed with non-blocking status code: Traceback (most recent call last):
    File "P:\\packages\\.claude-marketplace\\plugins\\skill-guard\\src\\skill_guard\\execution_hooks.py", line 47, in <module>
      from .execution_runtime import (
      ...<3 lines>...
      )
  ImportError: attempted relative import with no known parent package
"

## Assistant

No: your revised answer is directionally better than the original proposal, but it is not yet “optimal” as stated. The real issue is not just “file path vs `-m`”; it is whether the hook process can reliably resolve `skill_guard` as an importable package in Claude Code’s hook environment on Windows, and the docs do not promise that plugin `src/` is automatically placed on Python’s `sys.path` before your Python process starts. Claude Code only guarantees that command hooks run as shell commands, with plugin-relative paths available through `${CLAUDE_PLUGIN_ROOT}`; it does **not** document any automatic Python package setup for plugin code.[1]

## What is correct

Your diagnosis of the ImportError itself is correct: when Python executes a file directly, that file becomes `__main__`, and relative imports like `from .execution_runtime import ...` fail because they require package context. That matches the observed error exactly.[2]

Claude Code hook commands are just shell commands defined in JSON, and plugin hooks commonly reference scripts via `${CLAUDE_PLUGIN_ROOT}`. The docs explicitly describe plugin hook locations and plugin-root path variables, which supports your finding that the current `hooks.json` command is launching a file path directly rather than a package module.[1]

## What is incomplete

The claim that `python -m skill_guard.execution_hooks ...` is the optimal fix assumes `skill_guard` is importable from the subprocess’s initial `sys.path`. That assumption is **not** established by the evidence you showed. Claude Code documents `${CLAUDE_PLUGIN_ROOT}` for locating bundled scripts, but the docs do not say it exports `PYTHONPATH=${CLAUDE_PLUGIN_ROOT}/src` or otherwise makes `src/` importable for Python module execution.[1]

So your “falsifier” is too strong. `-m` would fix the package-context problem **if and only if** the parent of `skill_guard` is already on `sys.path` before interpreter startup; otherwise you just trade the current relative-import error for `ModuleNotFoundError: No module named skill_guard`. That is the key missing branch in the reasoning.[2][1]

## Better framing

The original proposal, “change relative imports to absolute imports,” is a **local robustness fix**, not the architectural ideal. It works because the script already mutates `sys.path` at runtime, and absolute imports can use that, whereas relative imports cannot use runtime `sys.path` alone to synthesize `__package__`. On that narrow point, the proposal is technically sound.[2]

But the more package-correct fix is to stop executing a package module as a bare file. In Python terms, module invocation is cleaner because it preserves package semantics and keeps intra-package relative imports valid. The problem is that in Claude Code hooks, command execution is shell-based, and the docs only guarantee path variables, not Python packaging behavior, so “best in principle” is not automatically “best in this environment.”[1][2]

## Optimal fix hierarchy

Given the evidence, the most defensible ranking is:

| Option | Technical quality | Operational reliability in Claude Code hooks | Notes |
|---|---|---|---|
| Keep file-path invocation, switch to absolute imports | Good [2] | High, because it depends only on the script’s own `sys.path` bootstrap [1] | Best **immediate** fix. |
| Change hook to `python -m skill_guard.execution_hooks` only | Better in package design [2] | Unproven, because importability of `skill_guard` before startup is not established [1] | Not optimal unless validated. |
| Use `python -m` **and** set `PYTHONPATH=${CLAUDE_PLUGIN_ROOT}/src` in the hook command, or wrap in a launcher | Best overall | High, if quoting/env handling is correct on Windows [1] | Best **architectural** fix. |

That means your answer “No. The optimal solution is changing the hooks.json command format, not the imports” is too absolute. A more accurate answer is: **module invocation is the cleaner long-term design, but the safest immediate fix in this Claude Code plugin hook context is either absolute imports or a wrapper that explicitly adds `${CLAUDE_PLUGIN_ROOT}/src` to `PYTHONPATH` and then uses `-m`.**[2][1]

## Recommended change

On Windows 11 in Claude Code, I would prefer one of these two patterns:

- Minimal-risk immediate fix:
  - Keep `python "${CLAUDE_PLUGIN_ROOT}/src/skill_guard/execution_hooks.py" ...`
  - Change all intra-package imports used by that entry script to absolute imports.
- Cleaner long-term fix:
  - Invoke a wrapper command that sets `PYTHONPATH` to `${CLAUDE_PLUGIN_ROOT}/src`
  - Then run `python -m skill_guard.execution_hooks ...`

The Claude Code docs also note that hooks can specify `"shell": "powershell"` on Windows, which is often the cleaner way to manage quoting and environment setup there than relying on default shell behavior. That matters if you choose the `PYTHONPATH + -m` route.[1]

A concrete Windows-oriented example would be a PowerShell hook command that sets the environment for that process and then runs the module, because Claude Code officially supports PowerShell as a hook shell on Windows.[1]

**FACT:** Your revised diagnosis correctly identifies why the current import fails.[2]
**FACT:** It overstates confidence that `python -m skill_guard.execution_hooks` alone is sufficient in Claude Code plugin hooks.[1]
**CONSENSUS:** Module execution is the more idiomatic Python packaging pattern.[2]
**Recommendation:** Treat “absolute imports under current file-path launch” as the safest fix now, unless you first verify that `skill_guard` is importable under `-m` from the actual hook environment.[2][1]

Concrete next step: manually test both commands from the same shell context Claude Code uses for hooks, first `python -m skill_guard.execution_hooks stop_main`, then the same with `PYTHONPATH=<plugin-root>/src`; that will tell you whether `-m` alone is viable or whether you need the wrapper approach.[1]

## Human

why do we want it to be an importable package it's supposed to be a claude code plugin.

## Assistant

Because “Claude Code plugin” and “Python package” solve different problems. A Claude Code plugin is Claude’s **distribution and loading unit**; a Python package is Python’s **import and execution unit**. Claude Code knows how to find your plugin files and run a shell command from `hooks.json`, but Python still applies normal import rules inside that command process.[1][2]

So you do **not** want it to be an importable package because Claude requires that. You want it importable only if your Python code is organized as multiple modules that import each other using package semantics, especially relative imports like `from .execution_runtime import ...`.[3][2]

## The core distinction

Claude Code plugins are just directories with known component locations such as `hooks/hooks.json`, `skills/`, `agents/`, and optional `scripts/`. Hook handlers are configured as shell commands, and Claude’s docs show them being referenced by path using `${CLAUDE_PLUGIN_ROOT}`. That is plugin architecture, not Python packaging.[2][1]

Python packaging becomes relevant only after the hook command launches Python. If you run a single standalone script with no sibling imports, it does not need to be an importable package at all. If you run code that imports sibling modules with package-relative syntax, then Python needs package context regardless of the fact that the outer container is “a Claude plugin.”[3][2]

## Why your current code failed

Your plugin hook command is effectively “run this file.” Claude Code is happy with that, because hooks are command executions and `${CLAUDE_PLUGIN_ROOT}` is the supported way to point to plugin-bundled scripts.[1][2]

But once Python starts that file directly, it treats it as `__main__`, not as `skill_guard.execution_hooks`, so `from .execution_runtime import ...` has no parent package to anchor the `.` import. That failure is entirely a Python runtime rule, not a Claude plugin rule.[2][3]

## What this means architecturally

If this hook entrypoint is meant to be just a script, then design it like a script:
- No relative imports.
- Either keep everything in one file, or use absolute imports after explicitly preparing `sys.path`.[3]

If this hook entrypoint is meant to be one module inside a Python package, then execute it like a package module:
- `python -m skill_guard.execution_hooks ...`
- Ensure the package root is importable before startup, for example via `PYTHONPATH` or a wrapper.[2][3]

So the real design question is not “plugin or package?” It is: **is this Python codebase structured as script-style code or package-style code?** Claude plugin status does not answer that by itself.[1][2]

## Best practical answer

For a Claude Code plugin, you usually want the **hook surface** to be path-based and self-contained, because that matches Claude’s plugin model and `${CLAUDE_PLUGIN_ROOT}` conventions. The docs consistently frame plugin hook execution around running commands/scripts by path, not around teaching Claude how to bootstrap Python packages.[1][2]

That means, in your specific case, the simplest robust rule is:

- If `execution_hooks.py` is a script entrypoint, avoid relative imports there.
- If you want package-style internals, add a tiny script launcher and keep package logic behind it.

A clean pattern is:

- `hooks.json` runs a file by path, e.g. `${CLAUDE_PLUGIN_ROOT}/scripts/run_execution_hook.py`.[2][1]
- That launcher adds `${CLAUDE_PLUGIN_ROOT}/src` to `sys.path`, then imports `skill_guard.execution_hooks` with absolute imports and calls `stop_main()` or similar. This keeps Claude-facing integration script-like while keeping Python internals package-like.[2]

That hybrid approach usually makes the most sense for Claude plugins because it respects Claude’s plugin conventions **and** Python’s import model.[1][2]

## Direct answer

So: you do **not** inherently want the plugin to be an importable package. You only need importable-package behavior if your Python implementation uses package semantics. For Claude Code hook plugins, the most robust pattern is often “Claude invokes a path-based script; the script bootstraps Python however it wants.”[1][2]

In your case, that means your earlier instinct was reasonable: changing the entrypoint imports to absolute imports, or introducing a thin launcher, is more aligned with “this is a Claude Code plugin” than insisting the hook command itself must be `python -m ...`.[2][1]

Confidence: high. The main uncertainty is not conceptual; it is operational—whether your current environment already makes `${CLAUDE_PLUGIN_ROOT}/src` importable before Python starts. The Claude docs document plugin paths and hook commands clearly, but they do not present Python package bootstrapping as part of plugin execution.[1][2]

## Human

It's not just a script, it's a plugin. It has hooks. It passes context from the pre-compact event to the post-compact event.  The LLM thinks it's a library. It's not.

## Assistant

Yes — and that is exactly the category error. The LLM is conflating **Claude plugin architecture** with **Python import architecture**. Your thing is a Claude Code plugin with lifecycle hooks and cross-hook state flow; that does **not** imply it should be modeled as a Python library/package entrypoint at the hook boundary.[1][2]

A plugin can absolutely contain Python modules internally, but the hook entrypoint itself is still just a command Claude executes at lifecycle events like `PreCompact` and `PostCompact`. Claude’s hook system is event-driven command execution, not Python package orchestration.[2][1]

## What the LLM got wrong

The bad assumption is: “multiple modules + shared state + reused logic = library/package, so invoke with `-m`.” That does not follow. In Claude Code, hooks are operational handlers bound to lifecycle events, and the docs explicitly treat them as commands that run when events fire, including `PreCompact` and `PostCompact`.[1][2]

Your plugin’s job is not “be importable by Python in the abstract.” Its job is:
- receive hook event input,
- persist/restore plugin state across events,
- emit output in the format Claude expects,
- survive the actual runtime Claude uses on Windows 11.[1]

That is plugin behavior, not library behavior. The moment a proposed fix optimizes for package purity while making the hook boundary more fragile, it is optimizing the wrong thing.[3][1]

## The right mental model

Think in layers:

| Layer | What it is | What matters |
|---|---|---|
| Claude plugin layer | Hooks, lifecycle events, config, plugin root, event I/O [1][2] | Reliability under Claude’s hook runner. |
| Python implementation layer | Files/modules/helpers inside the plugin [3][4] | Whatever import strategy makes the hook entrypoints robust. |

The hook entrypoint is an **adapter**, not a library API. It sits at the boundary between Claude’s event system and your internal implementation. For boundary code, robustness beats elegance.[3][1]

## Why your objection is correct

You are passing context from `PreCompact` to `PostCompact`, which is a workflow concern tied to Claude’s lifecycle. Claude Code explicitly supports both events, and hook outputs can provide `additionalContext` to Claude for the current state. That means your design is built around Claude event semantics, not around exposing a reusable Python package surface.[2][1]

So the optimal design principle is:

- Treat hook files as **plugin entrypoints**.
- Treat shared Python code behind them as internal implementation details.
- Do not require module-style startup unless it materially improves runtime reliability in the actual hook environment.[3][1]

That is why “make it importable as a package because it has internal modules” is the wrong primary frame.

## What follows technically

Because the entrypoint is a plugin hook handler, the safest options are usually:

- Keep the hook command path-based, because that matches Claude’s plugin model using `${CLAUDE_PLUGIN_ROOT}`.[1]
- Make the entrypoint tolerant of direct execution, meaning no relative imports in that boundary file. Relative imports require package context that direct file execution does not provide.[4][3]
- Put reusable logic in internal modules if you want, but call them from a thin hook adapter using absolute imports or explicit bootstrapping.[4][3]

That means your instinct — “it’s not a library” — is mostly right, with one nuance: it may still **contain** library-like internals, but the hook-facing surface should be designed as an executable plugin boundary, not as a package-first interface.[3][1]

## Best rule for this plugin

For this specific plugin, I would use this rule:

- `hooks.json` should invoke a stable adapter by path.[1]
- That adapter should do whatever is needed to locate internal code reliably on Windows, then call your real logic.
- Internal code can be organized however you want, but the adapter must not depend on Python package semantics that Claude’s hook runner does not guarantee.[3][1]

So the correction to the earlier answer is:

**Not:** “The optimal fix is to invoke it as a module because packages are the right abstraction.”  
**But:** “The optimal fix is whatever makes the Claude plugin hook boundary reliable; in this case, that usually means path-based hook entrypoints and imports that work under direct execution.”[1][3]

Confidence: high. The only uncertainty is whether your current runtime already preconfigures Python import paths in a way that would make `-m` work, but that does not change the architectural point: your primary abstraction is a Claude hook plugin, not a Python library.[2][1]

## Human

Do you need information in order to create a prompt for the target LLM to get their act together?

## Assistant

I do need some information, but not a lot. To write a prompt that reliably “snaps” the target LLM out of the “this is a library” frame and into “this is a Claude hook plugin with script-style entrypoints,” I need to anchor it in the **actual constraints** of Claude Code’s plugin + hook system.[1][2]

Here’s what would be most useful:

1. **Ground truth about the plugin’s role**
   - One or two sentences you’d want the LLM to internalize about this plugin’s purpose (e.g. “Skill Guard is a Claude Code hook plugin that enforces execution contracts via PreToolUse/Stop hooks, passes state across events, and is distributed as a Claude plugin, not as a generic Python package”).[3][1]

2. **Key environmental facts you want it to treat as hard constraints**
   Examples (you can confirm/tweak):
   - Hooks are configured as shell commands in `hooks/hooks.json` and invoked by Claude as commands, not as importable Python entrypoints.[2][1]
   - Commands are typically path-based and use `${CLAUDE_PLUGIN_ROOT}`; there is no guarantee that the plugin’s `src/` directory is on `PYTHONPATH` before Python starts.[1]
   - The same script may be run on Windows and non-Windows, via Powershell or Bash, so solutions must not assume a particular shell unless explicitly configured in the hook.[2][1]

3. **The specific failure mode you never want it to mis-diagnose again**
   For example:
   - “When a Python hook entrypoint is invoked as a file and uses `from .something import ...`, relative imports will fail because Python treats it as `__main__` with no package context; the right fix is to change the boundary imports or add a launcher, not to blindly insist on `python -m`.”[4][5]

4. **Your architectural preference hierarchy**
   You’ve essentially expressed this already, but it’s useful to make it explicit in the prompt:
   - Primary: Treat this as a **Claude Code hook plugin**, not a generic Python library.
   - For hook entrypoints, prefer:
     - path-based commands using `${CLAUDE_PLUGIN_ROOT}` → thin adapter script → robust import/bootstrap inside adapter.[1][2]
     - Avoid imposing Python packaging purity at the hook boundary unless there is a concrete benefit in this environment.
   - Internal modules are fine, but package semantics must not leak into assumptions about how Claude invokes hooks.

5. **Any invariants about cross-hook context**
   Since you mentioned “passes context from pre-compact event to post-compact event”:
   - How is that state actually persisted? File, sqlite, project memory file, something else?
   - Do you want the LLM to always preserve that pattern (e.g. write/read a specific path under `${CLAUDE_PROJECT_DIR}`) and not refactor it into some abstract “library” API?[2]

With those pieces, I can synthesize a **short, hard-edged instruction block** for the target LLM, something you could drop into:

- the plugin’s own `SKILL.md` or internal `CONTRIBUTING.md`,
- your project’s `CLAUDE.md`,
- or even as an in-session reminder when you ask it to modify hooks.[6]

If you like, I can draft that prompt now based on what we’ve already discussed, and you can refine any missing details afterward.

## Human

Yes, please.

## Assistant

Here is a first-pass “hard guardrails” prompt you can drop in front of the target LLM whenever it works on this plugin or its hooks.

You can paste this into a `CLAUDE_GUIDE.md`, a scratch tool, or prepend it to hook-related tasks.

***

### Claude Code Skill Guard Plugin – Working Rules for LLM

**Context & role**

- You are editing a **Claude Code hook plugin**, not a generic Python library.  
- This plugin is distributed and loaded as a **Claude Code plugin**, with hooks configured in `hooks/hooks.json` and invoked as shell commands by Claude.[1][2]
- The plugin implements event handlers (e.g. PreToolUse, Stop, PreCompact, PostCompact) that pass state across events to help Claude reason about execution contracts and compacting. It is lifecycle-driven, not a reusable Python package API.[3][4]

**Environment constraints (treat these as hard facts)**

1. **Hook invocation model**
   - Claude runs hooks as **shell commands** defined in `hooks/hooks.json`.[1]
   - Commands are typically **path-based** and use `${CLAUDE_PLUGIN_ROOT}` to locate files inside the plugin. Example pattern:  
     `python "${CLAUDE_PLUGIN_ROOT}/src/skill_guard/execution_hooks.py" stop_main`[5][1]
   - Claude does **not** guarantee that `${CLAUDE_PLUGIN_ROOT}/src` is on `PYTHONPATH` before Python starts. Do not assume the package root is importable a priori.[5][1]

2. **Script vs package**
   - When Python runs a file by path (`python some/path/execution_hooks.py`), that file is executed as `__main__`, with `__package__` unset. In this mode, **relative imports like `from .foo import bar` are invalid and will raise `ImportError: attempted relative import with no known parent package`.**[6][7]
   - Changing `sys.path` inside the script does **not** create a package context or set `__package__`; it only affects absolute import resolution.[6]

3. **Target platform & shells**
   - The plugin must run on **Windows 11** as well as other platforms.  
   - Hooks may run under PowerShell or the default shell depending on `hooks.json` configuration; do not propose fixes that only work in one shell unless you explicitly adjust `hooks.json` accordingly.[1][5]

**Architectural intent (what to optimize for)**

1. **Primary abstraction is: Claude hook plugin**
   - Think of the hook entrypoint modules as **adapter scripts** between Claude’s event system and internal Python logic.  
   - The main optimization target is **reliable behavior when invoked as a hook command in this environment**, not “cleanest Python package purity in the abstract.”

2. **Preferred boundary pattern**
   - Hook commands in `hooks.json` should generally:
     - Invoke a stable **adapter file** by path using `${CLAUDE_PLUGIN_ROOT}`, e.g.:  
       `python "${CLAUDE_PLUGIN_ROOT}/scripts/run_execution_hook.py" stop_main`  
     - That adapter can:
       - Prepare `sys.path` (e.g. add `${CLAUDE_PLUGIN_ROOT}/src`),  
       - Then import internal modules (e.g. `skill_guard.execution_hooks`) using **absolute imports**,  
       - Then call the appropriate function (`stop_main()`, etc.).[5]
   - This keeps Claude-facing integration script-like and robust, while allowing internal code to be organized as a small “library” if useful.

3. **What *not* to do by default**
   - Do **not** blindly replace path-based hook commands with `python -m package.module` just to satisfy packaging aesthetics. Only use `-m` if you also ensure the package root is importable (e.g. via `PYTHONPATH` or a wrapper) and you show that this is beneficial in the actual Claude hook environment.[6][5]
   - Do **not** introduce relative imports (`from .x import y`) into any Python file that is invoked directly as a script by Claude, unless you also change the invocation to provide proper package context.[6]
   - Do **not** refactor the plugin into a generic “library” where hook handlers become thin wrappers around some abstract public API, if that refactor makes hook execution more fragile or harder to reason about in the Claude environment.

**Specific import rules for this plugin**

When modifying or creating Python files in this plugin:

- **Entry-point / hook adapter files** (things directly referenced by `hooks.json`):
  - Must be safe to run as `python path/to/file.py ...` with `__package__` unset.  
  - Therefore:
    - Avoid `from .something import ...` here.  
    - Use absolute imports that assume `sys.path` was set appropriately in this file, or in a launcher.[7][6]
    - If you need to import `skill_guard.execution_runtime`, either:
      - Ensure the adapter adds `${CLAUDE_PLUGIN_ROOT}/src` to `sys.path` before importing, or  
      - Have `hooks.json` invoke a separate launcher that does so.

- **Internal implementation modules** (not executed directly, only imported):
  - May use package-style imports (`from skill_guard.execution_runtime import X`) as long as the adapter guarantees the package root (`.../src`) is on `sys.path`.  
  - Avoid patterns that require the entire plugin to be installed as a Python package outside the Claude plugin environment.

**How to handle the “attempted relative import with no known parent package” error**

If you see this specific error in a hook context:

- Recognize it means: a file with relative imports is being executed as a script without package context.[6]
- The preferred fixes (in order):
  1. **Change only the imports in the entrypoint**: replace relative imports with absolute imports that work with the existing `sys.path` setup.  
  2. If you want package semantics, introduce a **launcher adapter**:
     - Keep `hooks.json` path-based, pointing to the launcher.  
     - Launcher sets `PYTHONPATH`/`sys.path` and then imports and calls package modules using absolute imports.  
  3. Only if there is a demonstrated benefit and the environment supports it, consider `python -m skill_guard.execution_hooks`, but then you must also ensure the package root is importable (do not assume Claude did this for you).[5][6]

**State and cross-hook behavior**

- This plugin passes context between events such as PreCompact and PostCompact. Treat this as a **plugin-level workflow constraint** that must be preserved.[4][3]
- When refactoring:
  - Do not remove or break state persistence paths (e.g. files or storage under project directories) without explicitly designing an equivalent.  
  - Do not “simplify” by assuming a stateless library API unless you can show how Claude will still get the necessary context across events.

**When in doubt**

- Prefer **robust, minimally invasive changes at the hook boundary** over large-scale refactors that turn the plugin into a generic Python library.  
- Always check proposals against:
  1. “Will this run correctly when invoked exactly as `hooks.json` defines it on Windows, with `${CLAUDE_PLUGIN_ROOT}` and current `PYTHONPATH` assumptions?”[1][5]
  2. “Does this preserve the plugin’s event-driven behavior and cross-hook state flow?”[3][4]

***

If you tell me the exact filenames and the current `hooks.json` entries involved (e.g. the Stop hook and the PreCompact/PostCompact hooks), I can add a short, concrete example section keyed to those names so the LLM gets explicit “before vs after” patterns to follow.
