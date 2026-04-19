<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# In Claude Code, it seems like subagents cannot write to files when Claude is in plan mode. Is that true? Is there a workaround other than leaving plan mode?

Yes, subagents in Claude Code are generally **prevented from writing files while the main session is in Plan Mode**, because Plan Mode is designed to be a “read‑only, design‑only” phase where only the plan file in `~/.claude/plans/` is allowed to be written or edited.[^1_1][^1_2][^1_3]

Subagents invoked via the Task tool or other means can still be coded to *call* `Write`/`Edit` tools, but Claude’s own permission system blocks those writes when the `permission_mode` is `"plan"`, unless the target is explicitly a plan file.[^1_3][^1_4][^1_1]

### Workarounds without leaving Plan Mode

Since you want to keep Plan Mode but still get subagents to “output” something, several patterns are common:

1. **Write only to plan / scratch files**
    - Have the subagent output the desired code or content into:
        - The plan file itself (e.g., as a fenced block).
        - A deliberately non‑critical scratch file (e.g., `docs/scratch-plan.md`, `tmp/plan-output.ts`).
    - These are still “writes”, but they’re meant to be disposable and under your control.[^1_2][^1_1]
2. **Use a “plan‑only” subagent pattern**
    - Instruct the subagent to:
        - Analyze the code.
        - Propose edits in a structured format (e.g., “diff‑style” or “before/after” blocks).
        - Write the proposal into the plan file (or your own scratch file) **without** touching source files.
    - You then promote those changes out of Plan Mode by:
        - Copying the proposed diff into real files manually, or
        - Asking Claude in regular mode to “apply the plan” using the written‑down changes.[^1_5][^1_1][^1_2]
3. **Feed the plan back into a non‑plan mode run**
    - Let the subagent generate the plan fully in Plan Mode, including concrete code snippets and edit instructions.
    - Then start a new Claude Code session (or drop Plan Mode) and prompt:
        - “Now that we are in regular mode, apply the plan from `~/.claude/plans/...` / `docs/plan.md` to the real source files.”
    - This keeps the *thinking* in Plan Mode but defers the writes to when writes are allowed.[^1_1][^1_2]
4. **Override the guardrails via a hook (advanced, risky)**
    - There’s a pattern of using `PreToolUse` hooks to check `permission_mode === "plan"` and allow certain `Write`/`Edit` invocations conditionally, e.g., to a specific “sandbox” directory.[^1_6][^1_1]
    - This is essentially custom‑coded behavior; you are then responsible for the safety and correctness of the writes.

### If you *need* subagents to modify real files

The only fully supported, non‑workaround path is:

- Exit Plan Mode (`Shift+Tab` if in GUI, or disable plan‑mode flag in CLI).
- Run the subagent in direct / regular mode, where `Write`/`Edit` tools are allowed (subject to your usual permissions).[^1_4][^1_3]

***

Given your background as an architect/automation‑heavy user, what you’re probably after is a **hook‑based “plan‑only subagent” specialization** (e.g., `PlanRefactorAgent` that must never touch real source trees, only scratch‑plan files). Would you like a concrete hook pattern or MCP‑style rule snippet that enforces this for any subagent invoked in Plan Mode?

If yes, I’ll sketch a minimal `PreToolUse`‑based rule that blocks `Write`/`Edit` on non‑plan files while in Plan Mode, and show how you can plug that into your existing governance setup.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://securetrajectories.substack.com/p/claude-codes-plan-mode-isnt-read

[^1_2]: https://lucumr.pocoo.org/2025/12/17/what-is-plan-mode/

[^1_3]: https://code.claude.com/docs/en/permissions

[^1_4]: https://github.com/anthropics/claude-code/issues/5406

[^1_5]: https://codewithmukesh.com/blog/plan-mode-claude-code/

[^1_6]: https://code.claude.com/docs/en/best-practices

[^1_7]: https://www.reddit.com/r/ClaudeAI/comments/1mwof24/refactoring_subagent_is_not_writing_to_the_file/

[^1_8]: https://github.com/anthropics/claude-code/issues/13890

[^1_9]: https://github.com/anthropics/claude-code/issues/12707

[^1_10]: https://github.com/anthropics/claude-code/issues/5439

[^1_11]: https://github.com/anthropics/claude-code/issues/18995

[^1_12]: https://www.reddit.com/r/ClaudeAI/comments/1p7bplw/claude_started_writing_the_plan_in_files_how_to/

[^1_13]: https://www.youtube.com/watch?v=UZb0if-7wGE

[^1_14]: https://github.com/anthropics/claude-code/issues/7032

[^1_15]: https://github.com/anthropics/claude-code/issues/6716


---

# yes please

Here’s a concrete, minimal hook‑based pattern that enforces your constraint: **in Plan Mode, subagents can only `Write`/`Edit` to specific “plan / scratch” paths, never to “real” source files**.[^2_1][^2_2][^2_3]

***

### 1. Hook spec in `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/plan-only-write-guard.sh"
          }
        ]
      },
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/plan-only-write-guard.sh"
          }
        ]
      }
    ]
  }
}
```

This runs `plan‑only‑write‑guard.sh` before every `Edit` and `Write` call.[^2_2][^2_1]

***

### 2. Guard script: `./.claude/hooks/plan-only-write-guard.sh`

Make sure the script is executable (`chmod +x`).

```bash
#!/bin/bash
#
# PreToolUse hook:
#   - blocks Write/Edit to "real" files if plan_mode_active is true
#   - allows only a few plan/scratch paths
#
# Exit 0         => allow
# Exit 2         => block (PreToolUse only)

set -euo pipefail

input_json=$(cat)

# === CONFIG =================================================================
# Paths allowed to be written in Plan Mode.
# These are relative to repo root; adapt to your layout.
PLAN_PATHS_ALLOWLIST=(
  ".claude/plans/"
  "docs/scratch-plan.md"
  "tmp/plan-output."
  "plan/"
)

# Regex anchor pattern for allowed paths (expanded below).
# If plan_mode_active is *false*, this is ignored.
PLAN_MODE_ACTIVE="$1"  # true / false passed from outer wrapper

# If we are not in plan mode, allow everything.
if [[ "$PLAN_MODE_ACTIVE" != "true" ]]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

# === PULL OUT TOOL ARGS =====================================================
tool_name=$(echo "$input_json" | jq -r '.tool_name')
tool_input=$(echo "$input_json" | jq '.tool_input')

case "$tool_name" in
  "Edit"|"Write")
    file_path=$(echo "$tool_input" | jq -r '.path')
    ;;
  *)
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
    exit 0
    ;;
esac

# === BUILD ALLOWLIST PATTERN ===============================================
# Build regex for the allowed paths, anchored to start of string.
# This is a simple prefix‑match regex; you can tighten if needed.
PATTERN="^("
IFS="|"
for allowed in "${PLAN_PATHS_ALLOWLIST[@]}"; do
  pattern_safe=$(printf '%s' "$allowed" | sed 's|[\/.]|\\&|g')
  PATTERN+="$pattern_safe"
done
PATTERN+=").*"

# === CHECK IF ALLOWED ======================================================
if [[ "$file_path" =~ $PATTERN ]]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
else
  >&2 cat <<EOF
Plan‑only mode active: refusing to write to "$file_path".
Only paths starting with:
${PLAN_PATHS_ALLOWLIST[@]}

are allowed in plan mode. Move subagent writes there.
EOF
  # Exit 2 to block the tool call in PreToolUse.
  exit 2
fi
```

**Notes on this script:**

- It assumes an outer wrapper (e.g., shell alias / MCP‑style meta‑layer) passes `true` when Plan Mode is active, otherwise `false`.[^2_4][^2_3]
- Plan‑mode logic is conservative: non‑plan‑mode always allows `Write`/`Edit`; plan‑mode only allows annotated scratch/plan paths.
- If CLI‑exposed `active_permission_mode` lands in `PreToolUse` in the future, you could replace the `$1` arg with `jq`‑parsing `permissionMode` from the hook input.[^2_2][^2_4]

***

### 3. How this fits your “plan‑only subagent” idea

1. Subagents in Plan Mode are free to `Write`/`Edit`:
    - `./.claude/plans/plan-xxxx.md`
    - `tmp/plan-output.*`, `docs/scratch-plan.md`, etc.
2. Any attempt to write to `src/`, `lib/`, `package.json`, etc. gets intercepted and blocked with a clear error.[^2_3][^2_1]
3. When you want to actually apply changes:
    - Exit Plan Mode.
    - Run a second “apply‑plan” invocation that reads the approved plan file and uses `Write`/`Edit` on real source files.

***

### 4. Optional: MCP‑style “PlanRefactorAgent” specialization

If you’ve got an MCP server, you can wrap this logic into a specialized agent:

- `PlanRefactorAgent`:
    - Calls your subagent stuff.
    - In its own `PreToolUse` override, hard‑codes `PLAN_MODE_ACTIVE=true` and enforces the same scratch‑path‑only rule.
- Then you keep a separate `RealEditAgent` that runs without those restrictions when you opt‑in.

This gives you a clean, observable boundary: “design” vs “deploy‑to‑real‑files” agents, enforced by hooks rather than discipline.[^2_5][^2_6]

***

If you tell me roughly how you’re invoking Claude Code today (CLI vs Studio, plus any MCP/hook infra you already have), I can tighten this into a ready‑to‑paste fragment for your exact layout.
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://code.claude.com/docs/en/hooks-guide

[^2_2]: https://code.claude.com/docs/en/hooks

[^2_3]: https://www.eesel.ai/blog/hooks-in-claude-code

[^2_4]: https://github.com/anthropics/claude-code/issues/4719

[^2_5]: https://blog.codacy.com/equipping-claude-code-with-deterministic-security-guardrails

[^2_6]: https://github.com/rulebricks/claude-code-guardrails

[^2_7]: https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/

[^2_8]: https://stevekinney.com/courses/ai-development/claude-code-hook-examples

[^2_9]: https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py

[^2_10]: https://mcpmarket.com/tools/skills/security-guardrails

[^2_11]: https://code.claude.com/docs/en/permissions

[^2_12]: https://www.youtube.com/watch?v=Q4gsvJvRjCU

[^2_13]: https://www.youtube.com/watch?v=fZFN_LT6rVw

[^2_14]: https://github.com/anthropics/claude-code/issues/28812

[^2_15]: https://www.datacamp.com/tutorial/claude-code-hooks


---

# I'm on Windows 11, and I know that it does not support .sh files. However, bash mode does seem to. Does it matter what extension we're using?

On Windows 11 it **does** matter what extension you use, but the real constraint is not the extension itself—it’s how you tell Claude Code (or Windows) *which interpreter* to run.[^3_1][^3_2][^3_3]

### What actually matters

- **Claude Code can run `.sh` hooks on Windows** if it can invoke a `bash` interpreter (e.g., Git‑for‑Windows’s `bash.exe`).[^3_2][^3_3][^3_1]
- Without proper setup, `.sh` files may just open in an editor instead of executing, which is a known Windows quirk.[^3_4][^3_1][^3_2]
- **Extension per se is not enforced by Claude Code**; it’s your shell / Windows that decides how to handle `.sh` vs `.ps1` vs `.js` vs `.py`.[^3_5][^3_6]

***

### Practical options for you on Windows 11

Given you’re on Windows but want to keep the script logic cross‑platform‑like:

1. **Keep the `.sh` extension but invoke it via `bash` explicitly**
In your hook config, instead of:

```json
"command": "./.claude/hooks/plan-only-write-guard.sh"
```

write:

```json
"command": "bash \"./.claude/hooks/plan-only-write-guard.sh\""
```

This tells Windows to run the script through `bash` regardless of the `.sh` extension.[^3_3][^3_5]
2. **Use a `.ps1` PowerShell version (Windows‑native)**
If you prefer `powershell` as your default shell:
    - Save the logic as `plan-only-write-guard.ps1`.
    - In the hook:

```json
"command": "powershell -File \"./.claude/hooks/plan-only-write-guard.ps1\" \"$PLAN_MODE_ACTIVE\""
```


PowerShell scripts are easier to debug on Windows and don’t depend on Git‑for‑Windows being present.[^3_7][^3_8]
3. **Use a Python script as the “real” hook**
Many hook authors on Windows prefer Python because it’s both cross‑platform and straightforward to invoke from PowerShell or Git Bash.[^3_5][^3_7]

Example:

```json
"command": "python \"./.claude/hooks/plan_only_write_guard.py\""
```

Then write the logic in Python instead of bash, and call it from any shell Claude fires up.[^3_7]

***

### Do you gain anything by changing the extension?

- **No functional benefit in Claude Code**; `command` just executes a program.
- **Practical benefit on Windows**:
    - `.ps1` “just works” in PowerShell if execution policy allows.
    - `.sh` must be routed into `bash` (Git Bash / WSL) or it may open in VS Code instead of running.[^3_1][^3_2][^3_4]

If you tell me whether you’re using:

- Git‑for‑Windows `bash` in your terminal, or
- pure PowerShell / WSL,

I can give you a ready‑to‑paste `.ps1` or `bash` version of the plan‑only‑guard hook tailored to that shell.
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/anthropics/claude-code/issues/21847

[^3_2]: https://github.com/anthropics/claude-code/issues/9758

[^3_3]: https://dev.classmethod.jp/en/articles/claude-code-session-start-hook-verification/

[^3_4]: https://github.com/anthropics/claude-code/issues/24097

[^3_5]: https://www.heyuan110.com/posts/ai/2026-02-28-claude-code-hooks-guide/

[^3_6]: https://code.claude.com/docs/en/hooks

[^3_7]: https://www.reddit.com/r/ClaudeAI/comments/1n1o29s/python_bash_for_writing_claude_code_hooks_with_4/

[^3_8]: https://interworks.com/blog/2026/01/27/how-to-install-claude-code-on-windows-11/

[^3_9]: https://github.com/anthropics/claude-code/issues/27014

[^3_10]: https://github.com/anthropics/claude-code/issues/29007

[^3_11]: https://www.reddit.com/r/ClaudeCode/comments/1rgxd5l/an_open_source_claude_code_pretooluse_hook_to/

[^3_12]: https://github.com/anthropics/claude-code/issues/25981

[^3_13]: https://www.youtube.com/watch?v=CaHTlfHWd8U

[^3_14]: https://claude.ai/public/artifacts/03a4aa0c-67b2-427f-838e-63770900bf1d

[^3_15]: https://github.com/anthropics/claude-code/issues/35797


---

# I thought that Claude agents and sub-agents could have their own hooks. Is this true? If yes, how does that change our agent specification?

Yes, **Claude Code agents and sub‑agents can have their own hooks**. Hooks can be defined either globally (`.claude/settings.json`) or embedded directly in agents/skills, and those hooks are scoped to that agent’s lifecycle.[^4_1][^4_2][^4_3]

### 1. Where hooks live per agent

- **Global settings**:
Hooks in `.claude/settings.json` apply to all agents and sub‑agents in the project unless overridden.[^4_4][^4_1]
- **Agent‑level hooks**:
You can define hooks “inline” in an agent definition (e.g., a stored `/agent` or MCP skill), so only that agent’s sub‑agents and invocations respect them.[^4_2][^4_1]

Example structure (skill/agent frontmatter):

```markdown
---
hooks:
  PreToolUse:
    - type: "command"
      command: "./.claude/hooks/plan-only-write-guard.sh"
  SubagentStart:
    - type: "command"
      command: "./.claude/hooks/log-subagent-start.sh"
---

You are a PlanRefactorAgent that only writes to plan/scratch files.
```

These hooks only run when this specific agent (and its sub‑agents) are active.[^4_1][^4_2]

***

### 2. How this changes your agent specification

If you treat each role as a first‑class agent, you can specialize the guardrails and flow per agent:

- **PlanRefactorAgent** (strictly plan‑only):
    - Embeds a `PreToolUse` hook that blocks `Write`/`Edit` to non‑plan paths, exactly as in the earlier script.[^4_2][^4_1]
    - May also add `SubagentStart`/`SubagentStop` hooks that log or enforce plan‑mode‑only semantics.[^4_3][^4_4]
- **RealEditAgent** (applies changes):
    - Uses a different set of hooks, e.g., a `PreToolUse` that only allows `Write`/`Edit` within specific source directories.[^4_3][^4_2]
    - Can have post‑edit hooks that run tests, lint, or inject feedback back into the parent.[^4_2]

In effect, your agent spec becomes:

- **Roles** → separate agents.
- **Policy** → embedded hooks per agent (plan‑only, sandboxed‑edit, test‑only, etc.).
- **Orchestration** → main agent delegates to `PlanRefactorAgent` in Plan Mode, then to `RealEditAgent` in regular mode.[^4_5][^4_6]

***

### 3. Practical impact on your plan‑only guard

Instead of a single global Plan‑Guard hook, you can:

- Define `PlanRefactorAgent` with an embedded `PreToolUse` that:
    - Checks an explicit `plan_mode_active` flag or agent name.
    - Blocks `Write`/`Edit` outside `plan/`, `scratch/`, etc.[^4_1][^4_2]
- Leave global hooks looser, so other agents (e.g., `RealEditAgent`) can still touch real files.[^4_3][^4_2]

This lets you “compile” your architecture into:
`PlanRefactorAgent` (plan‑mode‑like) + `RealEditAgent` (edit‑mode) + optional `PlanValidatorAgent` (PreToolUse/PostToolUse chain), all with their own hook layers.

If you tell me whether you’re using **MCP‑style agents** or **Claude Code slash‑commands** mainly, I’ll sketch a concrete side‑by‑side spec for `PlanRefactorAgent` and `RealEditAgent` with embedded hooks tailored to that setup.
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://code.claude.com/docs/en/hooks

[^4_2]: https://www.dotzlaw.com/insights/claude-hooks/

[^4_3]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^4_4]: https://code.claude.com/docs/en/hooks-guide

[^4_5]: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

[^4_6]: https://www.producttalk.org/how-to-use-claude-code-features/

[^4_7]: https://www.reddit.com/r/ClaudeAI/comments/1pxxml2/so_what_about_em_subagents_hooks_and_other_cc/

[^4_8]: https://www.youtube.com/watch?v=7B2HJr0Y68g

[^4_9]: https://github.com/anthropics/claude-code/issues/5812

[^4_10]: https://www.reddit.com/r/ClaudeCode/comments/1n7f5ci/how_are_you_using_hooks_and_subagents/

[^4_11]: https://platform.claude.com/docs/en/agent-sdk/hooks

[^4_12]: https://www.youtube.com/watch?v=DNGxMX7ym44

[^4_13]: https://www.youtube.com/watch?v=n8D-s-268sE

[^4_14]: https://sankalp.bearblog.dev/my-experience-with-claude-code-20-and-how-to-get-better-at-using-coding-agents/

[^4_15]: https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/


---

# Best practices for using hooks with subagents on Windows

On Windows, the core idea stays the same—**hooks are still your deterministic control layer over subagents**—but you need to tweak paths, shells, and error handling to be robust under PowerShell / Git Bash.[^5_1][^5_2][^5_3]

***

### 1. Hook location and structure

- Put all hooks under `.claude/hooks/` in your project (or home) and treat them as **version‑controlled prod code**:
    - Idempotent, fast, quietly fail‑safe.[^5_4][^5_1]
- Use agent‑level hooks in subagent frontmatter for policies that should only apply to that agent (e.g., “plan‑only writes”, “read‑only test runner”).[^5_3][^5_5]

***

### 2. Windows‑specific command patterns

Because Windows doesn’t natively execute `.sh` files, standardize on:

- **PowerShell for “default” Windows**:
    - Hook command:

```json
"command": "powershell -File \"./.claude/hooks/my-hook.ps1\""
```

    - Enables richer error handling, logging, and easy integration with VS Code / Windows paths.[^5_6][^5_1]
- **Git Bash / WSL if you prefer bash**:
    - Use:

```json
"command": "bash \"./.claude/hooks/my-hook.sh\""
```

    - Ensure `bash` is in your `PATH` and the script is `chmod +x` (WSL works fine; Git‑for‑Windows also exposes `bash.exe`).[^5_7][^5_8]

Either way, keep the extension aligned with your chosen interpreter:

- `.ps1` → `powershell -File ...`
- `.sh` → `bash ...`

***

### 3. Subagent‑specific hooks to use

Per best‑practice patterns, lean on:

- `PreToolUse` on subagents:
    - Blocks or validates `Write`/`Edit` / `Bash` commands before they run in that subagent.[^5_9][^5_3]
    - Example: forbid writes outside `plan/` or `tmp/` in a `PlanRefactorAgent`.[^5_1][^5_3]
- `SubagentStart` / `SubagentStop`:
    - Log agent type, slug, and args; update queues / status files; surface next steps in the transcript.[^5_9][^5_1]
    - On Windows, prefer idempotent scripts that handle `~` vs `C:\Users\...` via `CLAUDE_PROJECT_DIR` or relative paths.[^5_3][^5_1]

***

### 4. Permissions and security on Windows

- **Explicitly allow hook commands in permissions**:

```json
"permissions": {
  "allow": [
    "Command(powershell -File \".\\.claude\\hooks\\my-hook.ps1\")",
    "Command(bash \".\\.claude\\hooks\\my-hook.sh\")"
  ]
}
```

On Windows, paths and quoting matter; validate with `Test‑Path`‑style checks inside the script.[^5_4][^5_1]
- **Avoid `allow: *`** for `Write`/`Edit` when using plan‑mode‑like subagents; let the hook guardrails be the source of truth.[^5_3][^5_9]

***

### 5. Observability and debugging on Windows

- **Log to project‑relative files** from hooks (e.g., `docs/claude/logs/...`), not just `stdout`.
    - Makes it easy to inspect what each subagent did, even if the console is noisy.[^5_1][^5_9]
- Prefer **structured logs (JSON)** so you can `jq`/PowerShell‑parse them later:

```powershell
$logEntry = @{
  timestamp = (Get-Date -Format "o")
  event     = "SubagentStop"
  agent     = $env:CLAUDE_AGENT_TYPE
  duration  = $duration
} | ConvertTo-Json -Compress
Add-Content -Path "docs/claude/logs/hook.log" -Value $logEntry
```

This is friendly to both Windows and cross‑platform tooling.[^5_4][^5_1]

***

### 6. Recommended pattern for your setup

Given you’re on **Windows 11 with PowerShell** and thinking in strict agent‑oriented roles:

- Each agent gets its own frontmatter‑defined hooks:
    - `PlanRefactorAgent` → `PreToolUse` that blocks writes outside plan/scratch.
    - `RealEditAgent` → `PreToolUse` + `PostToolUse` that gates and validates real‑file edits.[^5_9][^5_3]
- Implements all hooks in **PowerShell** (`.ps1`) by default, falling back to `bash` only if you’re already in a WSL or Git‑Bash‑heavy workflow.[^5_6][^5_1]

If you tell me whether you’re using **MCP‑style agents** or **slash‑command agents**, I can give you a minimal Windows‑only template repo layout plus sample `PlanRefactorAgent` and `RealEditAgent` frontmatter with embedded PowerShell hooks you can drop in.
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17][^5_18]</span>

<div align="center">⁂</div>

[^5_1]: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

[^5_2]: https://code.claude.com/docs/en/hooks-guide

[^5_3]: https://code.claude.com/docs/en/sub-agents

[^5_4]: https://github.com/shanraisshan/claude-code-hooks/blob/main/.claude/hooks/HOOKS-README.md

[^5_5]: https://code.claude.com/docs/en/hooks

[^5_6]: https://interworks.com/blog/2026/01/27/how-to-install-claude-code-on-windows-11/

[^5_7]: https://github.com/anthropics/claude-code/issues/21847

[^5_8]: https://github.com/anthropics/claude-code/issues/24097

[^5_9]: https://www.pubnub.com/blog/best-practices-claude-code-subagents-part-two-from-prompts-to-pipelines/

[^5_10]: https://www.reddit.com/r/ClaudeCode/comments/1rahdie/any_method_to_make_claude_code_use_subagents_for/

[^5_11]: https://www.facebook.com/groups/vibecodinglife/posts/1940685263186668/

[^5_12]: https://www.reddit.com/r/ClaudeCode/comments/1n7f5ci/how_are_you_using_hooks_and_subagents/

[^5_13]: https://getpushtoprod.substack.com/p/30-tips-for-claude-code-agent-teams

[^5_14]: https://www.producttalk.org/how-to-use-claude-code-features/

[^5_15]: https://www.youtube.com/watch?v=CEODfvJLIGQ

[^5_16]: https://www.builder.io/blog/claude-code-tips-best-practices

[^5_17]: https://sankalp.bearblog.dev/my-experience-with-claude-code-20-and-how-to-get-better-at-using-coding-agents/

[^5_18]: https://trigger.dev/blog/10-claude-code-tips-you-did-not-know


---

# What do you think the optimal way is for sub-agents to write new files, markdown files, when the CLI is in plan mode?

The **optimal pattern** is to let sub‑agents generate new markdown under a **single, plan‑only scratch path** (e.g., `docs/plans/` or `tmp/`) and **only write “real” files after you explicitly exit Plan Mode**.[^6_1][^6_2][^6_3]

***

### 1. Where sub‑agents should write markdown

Within Plan Mode, agree on a **canonical scratch area** your hooks and agents recognize:

- **Recommended locations** (pick one and pin it in hooks):
    - `docs/plans/` – for version‑controlled “spec‑like” markdown.[^6_4][^6_3]
    - `tmp/plans/` or `docs/scratch/` – for volatile, per‑session artifacts.[^6_5][^6_6]

Then, in your `PreToolUse`‑style guard, allow `Write`/`Edit` only if the path starts with these prefixes while `plan_mode_active == true`.[^6_7][^6_8]

***

### 2. Sub‑agent policy: markdown only, plan‑only files

To keep sub‑agents in line:

- **Prompt‑level rule**:
    - Tell each sub‑agent:
        - “You are in plan‑only mode.
            - You may only write markdown files under `docs/plans/` or `tmp/plans/`.
            - Do not write any `.ts`, `.py`, etc., files here; save those for the main agent outside Plan Mode.”[^6_2][^6_6]
- **Hook‑level rule**:
    - If a `Write`/`Edit` call is not targeting a `.md` under your predefined plan/scratch locations, **block it** and log the intended file so you can move it later.[^6_8][^6_4]

This makes your sub‑agent policy explicit both in behavior and enforcement.

***

### 3. Turn markdown into “real” files later

The canonical flow on your side is:

1. In Plan Mode:
    - Sub‑agents research and write structured markdown under `docs/plans/`:
        - “`docs/plans/feature‑x‑refactor.md`”.[^6_3][^6_5]
2. You exit Plan Mode (or switch to `auto‑accept` / normal).
3. Main agent (or another sub‑agent) **reads the plan file** and:
    - Applies diffs, writes `.ts`/`.py` files, creates directories, etc.[^6_4][^6_7]

This keeps Plan Mode genuinely plan‑only, while still letting sub‑agents build a rich, reusable markdown spec.

***

### 4. Bonus: auto‑plan‑to‑file hook pattern

You can push a bit further and have a **hook** that:

- Intercepts `Write` of `.plan.md`‑style files.
- Ensures the file lands in `docs/plans/` and optionally renames it with a timestamp or slug.[^6_5][^6_3]

This gives you a **version‑controlled spec** that integrates cleanly into Git, PRs, and code reviews without needing to “trust” the agent not to shortcut writes.[^6_2][^6_3]

If you share your current plan/layout (`docs/` vs `plans/` vs custom scratch), I can give you a concrete Markdown‑only‑Path‑Allowlist snippet aligned with your tree and a matching sub‑agent prompt.
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://lucumr.pocoo.org/2025/12/17/what-is-plan-mode/

[^6_2]: https://www.datacamp.com/tutorial/claude-code-plan-mode

[^6_3]: https://www.vibecodingacademy.ai/blog/claude-code-plan-mode-complete-guide

[^6_4]: https://www.youtube.com/watch?v=MO_h4McvCNw

[^6_5]: https://www.reddit.com/r/ClaudeCode/comments/1mqfq4y/planonly_mode_but_writing_the_plans_to_files/

[^6_6]: https://www.reddit.com/r/ClaudeCode/comments/1o7i3bx/how_i_dramatically_improved_claudes_code/

[^6_7]: https://code.claude.com/docs/en/common-workflows

[^6_8]: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

[^6_9]: https://github.com/anthropics/claude-code/issues/11140

[^6_10]: https://codewithmukesh.com/blog/plan-mode-claude-code/

[^6_11]: https://www.youtube.com/watch?v=CmrmmszC_F4

[^6_12]: https://www.humanlayer.dev/blog/writing-a-good-claude-md

[^6_13]: https://www.producttalk.org/how-to-use-claude-code-features/

[^6_14]: https://www.reddit.com/r/ClaudeAI/comments/1nrejut/when_to_use_plan_mode_vs_markdown_documentation/

[^6_15]: https://www.youtube.com/watch?v=a0HQB6bEgzI


---

# What are best prompts to prevent implementation before saving plan md

The optimal prompts are short, hard‑coded, and **enforce two properties**:

1. No implementation in this round until the plan `.md` is written and saved.
2. Explicit confirmation or “next step” signal before touching real files.[^7_1][^7_2][^7_3]

Below are battle‑tested phrase patterns you can paste verbatim or adapt into your agent specs.

***

### 1. Uniform prevention rule (for all plan‑only agents)

```text
You are in plan‑only mode. Before doing anything else:

1. Write a complete implementation plan to `docs/plans/<descriptor>.md` (or `docs/plans/current.md` if no descriptor exists yet).
   - The plan must include:
     - Files to read, create, or modify.
     - High‑level approach, key decisions, and alternatives considered.
     - Exact code changes as pseudocode or diffs, not real file edits.
2. Stop once the plan is saved. Do not:
   - Create, edit, or delete any `.ts` / `.py` / `.js` / etc. files.
   - Run any `Write` / `Edit` tool on non‑markdown files.
3. After saving the plan, ask me to confirm or revise the plan before proceeding to implementation.

If you have not yet written and saved the plan file, you must not start implementation.
```

This is a **core “law”** you can drop into every planner‑type agent frontmatter.[^7_4][^7_5]

***

### 2. Subagent‑specific planner prompt

For a `PlanRefactorAgent` / `PlanSpecAgent`:

```text
You are PlanRefactorAgent. Your only job in this session is planning.

1. Research the codebase and requirements, then write a structured plan to `docs/plans/{feature}-plan.md`.
2. The plan must:
   - Be in Markdown, under `docs/plans/`.
   - List every file to touch, every API or boundary, every migration step, and every risky change.
   - Mock the necessary changes as fenced code blocks, but do not call `Write` / `Edit` on real source files.
3. When the plan is saved, your response must end with:
   - “Plan saved to `docs/plans/{feature}-plan.md`. Please review and confirm or revise before implementing.”
4. Until you receive explicit approval to implement, do not:
   - Touch real implementation files.
   - Ask to “implement safely” or start a refactor without my go‑ahead.

Only after I type an explicit approval (e.g., “APPROVE IMPLEMENTATION FOR docs/plans/{feature}-plan.md”) may you move to implementation mode.
```

This pattern is widely used in plan‑mode‑heavy workflows and keeps implementation tightly gated.[^7_2][^7_6][^7_3]

***

### 3. Compact “no‑code” signal for general rounds

For non‑agent‑specific planning rounds:

```text
Do not implement anything in this round. Your task is:

- Analyze the situation and propose a detailed plan in Markdown.
- Save the plan to `docs/plans/current.md` (or `docs/plans/{topic}.md`).
- Stop after saving the plan and wait for me to confirm it before any code changes.

If you do not see a saved plan file in `docs/plans/`, you must not proceed to implementation.
```

This is a reusable “pre‑commit”‑style header you can drop into ad‑hoc planning prompts.[^7_7][^7_8]

***

### 4. Hook‑aware reinforcement (for your MCP/agent setup)

If you have hooks that block `Write`/`Edit` outside plan‑only paths, you can add a **stated assumption** in the prompt:

```text
You are in plan‑only mode. The environment enforces:

- Only `.md` files under `docs/plans/` or `tmp/plans/` may be written or edited.
- Any attempt to write non‑Markdown files or files outside those paths will be blocked.

Therefore, your entire implementation plan must live in Markdown under `docs/plans/` before any real‑file edits are possible.
```

This makes the policy **explicit to the agent**, so it doesn’t try to “push back” or “bypass” and instead just writes richer markdown.[^7_9][^7_4]

***

If you tell me whether you want this baked into **slash‑command agents**, **MCP‑style agents**, or into a shared `CLAUDE.md`/global rules file, I can give you a single canonical block you can drop into that scope and some next‑step verbiage you can type to unblock implementation.
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15]</span>

<div align="center">⁂</div>

[^7_1]: https://www.youtube.com/watch?v=woaw-zrieWU

[^7_2]: https://www.reddit.com/r/ClaudeAI/comments/1m943jd/3_helpful_plan_mode_prompts_for_claude_code/

[^7_3]: https://www.vibecodingacademy.ai/blog/claude-code-plan-mode-complete-guide

[^7_4]: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

[^7_5]: https://faafospecialist.substack.com/p/vb-04-subagents-from-basic-to-deep

[^7_6]: https://www.reddit.com/r/ClaudeCode/comments/1o7i3bx/how_i_dramatically_improved_claudes_code/

[^7_7]: https://www.reddit.com/r/ClaudeAI/comments/1rjm2ee/should_you_clear_context_before_implementing_a/

[^7_8]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

[^7_9]: https://lucumr.pocoo.org/2025/12/17/what-is-plan-mode/

[^7_10]: https://www.linkedin.com/posts/abhisheksahuiitr_ai-claudecode-engineeringtools-activity-7436859609316753408-wxyd

[^7_11]: https://dev.to/siddhantkcode/an-easy-way-to-stop-claude-code-from-forgetting-the-rules-h36

[^7_12]: https://www.youtube.com/watch?v=WwdIYp5fuxY

[^7_13]: https://github.com/anthropics/claude-code/issues/25734

[^7_14]: https://code.claude.com/docs/en/best-practices

[^7_15]: https://dev.to/_vjk/i-made-claude-code-think-before-it-codes-heres-the-prompt-bf


---

# How to set up Haiku 4.5 subagents for efficient markdown documentation

For **Claude Haiku 4.5 subagents to produce efficient markdown docs**, the key is:

- Dedicate a **doc‑only subagent role**.
- Constrain it to **read + markdown‑write only**, no real‑file edits.
- Route all docs through a **single canonical path** (e.g., `docs/`).[^8_1][^8_2][^8_3]

Below is a concrete setup you can drop into Claude Code or an MCP‑style orchestrator.

***

### 1. Define a Markdown Documentation Agent

Create a Haiku‑backed subagent called `DocWriter` (or `MarkdownDocAgent`). Its config should specify:

- **Model**: `haiku` (fast, cheap, ideal for documentation‑only tasks).[^8_4][^8_1]
- **Allowed tools**:
    - `Read` (to inspect code, PRs, or existing docs).
    - `Edit` / `Write` only on `docs/` or `docs/api/` / `docs/design/` markdown files.[^8_5][^8_6]

Example in `.claude/agents/doc_writer.md` or an MCP agent spec:

```markdown
---
name: "DocWriter"
description: "Writes and maintains markdown documentation using Haiku 4.5."
model: "haiku"
tools:
  - "Read"
  - "Write"
  - "Edit"
permissions:
  - "Read any file"
  - "Write path: \"docs/*.md\""
  - "Write path: \"docs/api/*.md\""
  - "Write path: \"docs/design/*.md\""
---

You are DocWriter, a dedicated documentation subagent.

1. Your job:
   - Read code, tests, and existing docs.
   - Produce clear, concise Markdown documentation under `docs/`.

2. Rules:
   - Only write to Markdown files under `docs/` (or `docs/api/`, `docs/design/`).
   - Do not:
     - Edit any `.ts`/`.py`/`.js` implementation files.
   - If asked to “implement” or “refactor”, ask whether you should write a design doc instead.

3. Style:
   - Use consistent headings, links, and cross‑references to other docs.
   - Keep examples short and focused on the concept.
```

This turns Haiku 4.5 into a **tight, cheap documentation layer** under your Sonnet‑based planner.[^8_2][^8_1]

***

### 2. Basic prompt pattern to invoke it

When you want Haiku 4.5 to write markdown, route work through this prompt:

```text
Use the DocWriter subagent (Haiku 4.5) to:

1. Read the relevant files:
   - `src/...`
   - `docs/...`
2. Write or update Markdown documentation under `docs/` that:
   - Explains the architecture, interfaces, or workflow clearly.
   - Includes headings, cross‑references, and short examples.
3. Do not edit any non‑Markdown files.

If a file already exists, revise it instead of creating many duplicates.
```

This avoids the “spamming many `.md`” anti‑pattern people see with Haiku.[^8_7][^8_8]

***

### 3. Enforce a single, canonical docs path

To keep documentation efficient and avoid fragmentation:

- Decide one or two roots:
    - `docs/` – general docs.
    - `docs/impl/` or `docs/plan/` – implementation notes and plans.[^8_9][^8_10]
- In your agent spec or global hooks, **block writes outside those paths** during doc‑only runs.[^8_6][^8_11]

Then your Haiku‑based `DocWriter` will:

- Only write under `docs/`.
- Reuse existing files instead of spinning off new ones.

***

### 4. Optional: Doc‑only planner–doc‑worker split (Haiku + Sonnet)

Advanced pattern:

- **Sonnet 4.5** (planner):
    - Breaks “document this feature” into steps and assigns them to `DocWriter` subagents.[^8_12][^8_1]
- **Haiku 4.5 `DocWriter`**:
    - Executes each doc step, writing Markdown under `docs/`.
    - Returns short summaries or fragment IDs you can stitch into a master doc.

This is the “intended” workflow for Haiku 4.5 in agentic coding: **Sonnet plans, Haiku executes doc‑only subtasks**.[^8_1][^8_2]

***

If you tell me whether you’re using **Claude Code agents** or **Claude Agent SDK / MCP‑style agents**, I can give you a ready‑to‑paste agent spec JSON plus a minimal orchestration loop that invokes `DocWriter` with Haiku 4.5 and dumps into `docs/` cleanly.
<span style="display:none">[^8_13][^8_14][^8_15][^8_16][^8_17][^8_18]</span>

<div align="center">⁂</div>

[^8_1]: https://www.codegpt.co/blog/anthropic-claude-models-complete-guide

[^8_2]: https://www.anthropic.com/news/claude-haiku-4-5

[^8_3]: https://www.anthropic.com/claude/haiku

[^8_4]: https://apxml.com/models/claude-haiku-45

[^8_5]: https://sankalp.bearblog.dev/my-experience-with-claude-code-20-and-how-to-get-better-at-using-coding-agents/

[^8_6]: https://platform.claude.com/docs/en/agent-sdk/subagents

[^8_7]: https://www.reddit.com/r/GithubCopilot/comments/1oaeghe/how_do_i_stop_claude_45_from_spamming_md_files_in/

[^8_8]: https://github.com/microsoft/vscode-copilot-release/issues/14045

[^8_9]: https://www.datacamp.com/tutorial/claude-code-plan-mode

[^8_10]: https://www.vibecodingacademy.ai/blog/claude-code-plan-mode-complete-guide

[^8_11]: https://code.claude.com/docs/en/hooks-guide

[^8_12]: https://codewithseb.com/blog/claude-code-sub-agents-multi-agent-systems-guide

[^8_13]: https://ai.azure.com/catalog/models/claude-haiku-4-5

[^8_14]: https://simonwillison.net/tags/sub-agents/

[^8_15]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

[^8_16]: https://skywork.ai/blog/agentic-coding-claude-haiku-4-5-beginners-guide-sub-agent-orchestration/

[^8_17]: https://www.reddit.com/r/ClaudeAI/comments/1oa6ssa/claude_code_explore_subagent_haiku_45_vs_custom/

[^8_18]: https://code.claude.com/docs/en/model-config


---

# Claude Code agents

Perfect; let’s wire this using **Claude Code agents** (slash‑commands, skills, and agent‑frontmatter style).[^9_1][^9_2]

***

### 1. Agent file: `/.claude/agents/doc_writer.md`

Create this as a **Claude Code agent** (it will show up when you type `/doc`).[^9_3][^9_4]

```markdown
---
name: "DocWriter"
description: "Writes and maintains markdown documentation using Haiku 4.5."
model: "haiku"
tools:
  - "Read"
  - "Write"
  - "Edit"
permissions:
  - "Read any file"
  - "Write path: \"docs/*.md\""
  - "Write path: \"docs/api/*.md\""
  - "Write path: \"docs/design/*.md\""
hooks:
  PreToolUse:
    - type: "command"
      command: "powershell -File \"./.claude/hooks/doc_only_guard.ps1\""
---

You are DocWriter, a documentation‑only subagent backed by Claude Haiku 4.5.

1. Your job:
   - Read code, tests, and existing docs.
   - Write or update Markdown documentation under `docs/`.

2. Rules:
   - Only write to Markdown files under:
     - `docs/*.md`
     - `docs/api/*.md`
     - `docs/design/*.md`
   - Do not:
     - Edit any `.ts`/`.py`/`.js` implementation files.
     - Create large numbers of tiny `.md` files; prefer consolidating under one or two canonical docs.
   - If asked to “implement” or “refactor”, ask whether you should write a design doc instead.

3. Style:
   - Use consistent headings, cross‑references to other docs, and short code examples.
   - Keep each file focused on a single topic (feature, API, workflow, decision record).
```

This makes `/doc` available and pins it to `haiku` for cheap, doc‑only work.[^9_5][^9_1]

***

### 2. Slash‑command usage pattern

In Claude Code, type:

```text
/agent DocWriter

Use DocWriter (Haiku 4.5) to:

1. Read:
   - `src/components/...`
   - `docs/...`
2. Write or update:
   - `docs/features/auth-flow.md`
   - `docs/api/auth.md`
3. Keep the docs clear, concise, and linked to related sections.

Only write to Markdown files under `docs/`; do not edit source files.
```

This keeps the **planning** in your main session (Sonnet 4.5) and **markdown‑generation** inside the Haiku‑backed `DocWriter` agent.[^9_6][^9_7]

***

### 3. Hook guard: `./.claude/hooks/doc_only_guard.ps1` (Windows)

To enforce “doc‑only”, drop this PowerShell script and `chmod +x` it (on Windows just ensure it’s executable in your shell).[^9_4][^9_8]

```powershell
# .\.claude\hooks\doc_only_guard.ps1
$inputJson = Get-Content -Raw

# Parse
$toolName = ($inputJson | ConvertFrom-Json).tool_name
$toolInput = ($inputJson | ConvertFrom-Json).tool_input

$docRoots = @("docs/", "docs/api/", "docs/design/")

if ($toolName -in @("Write", "Edit")) {
    $path = $toolInput.path

    $allowed = $false
    foreach ($root in $docRoots) {
        if ($path -like "${root}*.md") {
            $allowed = $true
            break
        }
    }

    if ($allowed) {
        $result = @{
            hookSpecificOutput = @{
                hookEventName      = "PreToolUse"
                permissionDecision = "allow"
            }
        } | ConvertTo-Json -Compress
        Write-Output $result
        exit 0
    }
    else {
        Write-Error "DocWriter may only write to Markdown under docs/; refusing to edit '$path'"
        exit 2
    }
}
else {
    $result = @{
        hookSpecificOutput = @{
            hookEventName      = "PreToolUse"
            permissionDecision = "allow"
        }
    } | ConvertTo-Json -Compress
    Write-Output $result
    exit 0
}
```

This hook integrates with the agent‑level `PreToolUse` you declared above and **blocks any attempt to write non‑doc files** from the Haiku‑based `DocWriter`.[^9_9][^9_4]

***

### 4. Permissions in `.claude/settings.json` (Windows‑safe quoting)

Ensure your global settings allow the hook:

```json
{
  "permissions": {
    "allow": [
      "Command(powershell -File \"./.claude/hooks/doc_only_guard.ps1\")"
    ]
  }
}
```

Paths and quotes matter on Windows; double‑check they match your layout.[^9_8][^9_10]

***

If you tell me your **default docs layout** (e.g., `docs/`, `docs/reference/`, `docs/adr/`), I can refine the `docRoots` set and suggest a canonical naming scheme for Haiku‑generated markdown so your repo stays clean and navigable.

<div align="center">⁂</div>

[^9_1]: https://www.anthropic.com/news/claude-haiku-4-5

[^9_2]: https://www.vibecodingacademy.ai/blog/claude-code-plan-mode-complete-guide

[^9_3]: https://code.claude.com/docs/en/model-config

[^9_4]: https://code.claude.com/docs/en/hooks-guide

[^9_5]: https://www.codegpt.co/blog/anthropic-claude-models-complete-guide

[^9_6]: https://codewithseb.com/blog/claude-code-sub-agents-multi-agent-systems-guide

[^9_7]: https://sankalp.bearblog.dev/my-experience-with-claude-code-20-and-how-to-get-better-at-using-coding-agents/

[^9_8]: https://github.com/shanraisshan/claude-code-hooks/blob/main/.claude/hooks/HOOKS-README.md

[^9_9]: https://code.claude.com/docs/en/common-workflows

[^9_10]: https://interworks.com/blog/2026/01/27/how-to-install-claude-code-on-windows-11/

