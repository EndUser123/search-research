---
title: "Does this issue codex make sense?

'
  Root cause (confirmed via Codex --help): codex exec is designed for shell comman"
date: "2026-04-05"
mode: "CONCISE"
uuid: "66eba9c1-1678-48ff-83b2-97d8eb79ed2c"
entry_count: 3
---

## Human

Does this issue codex make sense?

"
  Root cause (confirmed via Codex --help): codex exec is designed for shell commands, not prompts. It takes [COMMAND]
  [ARGS] — an actual command to execute. When ai_cli pipes plain text like "echo test" as stdin, Codex treats it as a
  prompt acknowledgment (no command executed → no output → exit 0).

  The exec subcommand signature:
  codex exec        Run Codex non-interactively
  codex [PROMPT]   Optional user prompt to start the session (interactive)

  The parallel test was sending prompts to a command-execution tool — a fundamental mismatch.

  What needs to happen next:

  Two realistic fixes:

  1. Remove codex from parallel testing — since it can't accept prompts like qwen/gemini/opencode
  2. Change invocation — use codex with a direct prompt argument instead of codex exec with stdin

  Looking at the ai_cli code, the current approach pipes prompts to all CLIs uniformly. Codex needs a different calling
  pattern. If you want Codex in the parallel group, the _build_cli_commands function would need to detect it and invoke
  differently (e.g., codex "echo test" instead of echo test | codex exec).

  The transcript's diagnosis was correct — the fix is still pending. Want me to implement the code change to make Codex
  work properly in the parallel group?

✻ Worked for 3m 49s

❯ Please describe the problem.

● Problem: Codex CLI produces no output in parallel execution

  Root cause: The codex exec subcommand is designed for running shell commands (e.g., codex exec "ls -la"), not for
  answering prompts. When ai_cli pipes plain text like "echo test" as stdin to codex exec, Codex treats it as a prompt
  acknowledgment rather than a command to execute — exits 0 with no output.

  Evidence:
  - codex exec signature: codex exec [COMMAND] [ARGS] — expects a shell command
  - codex [PROMPT] — optional user prompt for interactive session (not stdin)
  - Other CLIs (qwen, gemini, opencode) accept prompts via stdin — Codex doesn't

  Current behavior:
  echo "test" | codex exec   → treats "test" as prompt ack → no output → exit 0

  What would work:
  codex "test"               → starts interactive session with "test" as prompt → responds
  codex exec "echo test"     → executes actual shell command → produces output

  Affected code: _build_cli_commands in P:\\__csf\\lib\\parallel_llm.py sends echo test | codex exec to all CLIs uniformly.
  Codex needs to be called as codex "prompt" instead.

  Options:
  1. Remove Codex from the default parallel group (it can't work in prompt mode)
  2. Special-case Codex in _build_cli_commands to invoke as codex "prompt" instead of piping stdin

  The display fix (showing [No output] instead of Error - None) was applied. The underlying invocation mismatch is the
  unresolved issue.

❯ You have to describe what the skill is, because otherwise this doesn't make sense all by itself.

● The /ai-cli skill runs multiple LLM command-line tools in parallel with a single prompt, so you can get responses from
  several LLMs simultaneously and compare outputs side-by-side.

  What it does:
  - Takes a prompt → fans out to all configured CLIs at once → returns aggregated results
  - Default CLIs: qwen, gemini, codex, vibe, opencode (zai/minimax)
  - Supports single-CLI mode (--qwen-only, --gemini-only, --codex-only, etc.)
  - Timeout control per CLI
  - Exit codes: 0 = success, 1+ = per-CLI failure

  Invocation pattern:
  /ai-cli "explain this code"          # all CLIs in parallel
  /ai-cli "test" --codex-only         # codex only
  /ai-cli "fix bug" --timeout 120     # custom timeout

  Current state:
  - glm-4.7-flash removed (was an API mode, not a CLI — incorrectly listed)
  - Display fixed: [No output] instead of Error - None for CLIs that return empty
  - codex still broken — codex exec expects shell commands, not prompts. All other CLIs accept stdin prompts; Codex
  doesn't. Root cause is in _build_cli_commands which pipes prompts via stdin to all CLIs uniformly. Won't work for Codex
  without special-casing its invocation."

## Assistant

Yes, the issue codex is logically consistent and technically accurate, but there are two places where tightening the wording will reduce confusion.

## Core diagnosis

- Codex CLI’s **`exec`** subcommand is for non-interactive task execution, where Codex plans and runs shell commands, not for “answer this prompt” the way pure LLM CLIs do.[1][2]
- The harness is piping prompts via stdin (`echo "test" | codex exec`), but Codex expects either:
  - An interactive run started as `codex "prompt"` (prompt as an argument, not stdin), or  
  - A non-interactive `exec` run where the argument looks like a shell command, e.g. `codex exec "ls -la"`.[2][1]
- Other CLIs in your parallel group accept prompts from stdin; Codex does not currently support treating stdin as the user prompt in the same way (there is even a feature request for better stdin-as-prompt support).[3]

So the “fundamental mismatch” between “prompt over stdin” and “command-execution tool” is a correct framing.

## Wording / nuance to tweak

Two small adjustments would make this airtight:

1. **Clarify what `exec` is “designed for”**  
   - Saying “designed for shell commands, not prompts” is functionally true for this harness, but slightly imprecise: Codex always consumes a *prompt*, but `exec` then turns that into a plan and shell commands, rather than returning a chat-style answer.[1][2]
   - A more precise line:  
     - “`codex exec` is designed for non-interactive task runs where Codex plans and executes shell commands; it expects a command-style input, not a free-form ‘answer this’ prompt the way other LLM CLIs do.”

2. **How stdin is interpreted**  
   - Your text says: “When ai_cli pipes plain text like `echo test` as stdin, Codex treats it as a prompt acknowledgment (no command executed → no output → exit 0).”  
   - The observable behavior (no command run, no output, exit 0) is correct for your harness; what Codex’s internal *semantic* interpretation is (e.g., “prompt acknowledgment”) is more speculative. The safer statement is:  
     - “When ai_cli pipes plain text via stdin into `codex exec`, Codex does not treat it as a shell command to execute, so nothing runs and you get no output with exit 0.”  

Labeling the “prompt acknowledgment” wording as inferred behavior will keep you aligned with the docs.

## Options / fixes

Your two proposed fixes are sound and match Codex’s contract:

- Removing Codex from the default parallel set is consistent with “this tool is not a chat-style stdin-prompt CLI.”  
- Special-casing Codex in `_build_cli_commands` to call `codex "prompt"` (or a more fully structured harness using `exec` properly) is the right way to keep it in the parallel group, because Codex wants the initial prompt as an argument, not stdin.[2][1]

One extra nuance you might want to mention: Codex has its own harness assumptions (repo context, agents files, etc.), so even with `codex "prompt"` wired correctly, its behavior will often be qualitatively different from qwen/gemini/opencode.[4][5]

## Direct answer to “does this make sense?”

- **FACT:** The described root cause (stdin prompts vs `codex exec` semantics) and current behavior (no output, exit 0) are consistent with Codex CLI’s design and documentation.[1][2]
- **CONSENSUS:** Special-casing Codex invocation or removing it from the “uniform stdin-prompt” group is the correct architectural move.  
- **SPECULATION (medium confidence):** The “prompt acknowledgment” phrasing reflects internal behavior but is not directly documented; call it an inference and instead emphasize the observable “stdin is not treated as a command/prompt that produces output.”

If you want, the next concrete step is to sketch the `_build_cli_commands` branch for Codex (argument-based prompt, no stdin) and decide whether you want `codex` in “chat” mode or a more structured `exec` harness.

## Human

Well, is it possible to use it in the context of an LLM council or red team to answer questions or to review plans or code implementations?

## Assistant

Yes, but not as a “plain LLM” in a council; it works best as an agentic reviewer that reads repos, plans actions, and (optionally) edits or executes.[1][2][3][4]

## How Codex fits a council / red team

- Codex CLI is a **coding agent** that reads your workspace, proposes plans, runs commands in a sandbox, and edits files, rather than a bare text-only model.[3][5][4]
- In non-interactive mode (`codex exec` and `codex review`), it is specifically designed for scripted review, CI, and automation scenarios.[2][1]

So in a “council” or red-team pipeline, Codex is best treated as the *agent that operates on code and repos*, not just another chat model.

## Concrete council / red-team roles

- **Code & plan review agent**  
  - `codex exec "summarize the repository structure and list the top 5 risky areas"` can give structured risk summaries over a repo in CI.[1][2]
  - `codex review --base origin/main --json` can act as an automated reviewer for diffs in merge requests.[6][2]

- **Automation / CI checker in a council**  
  - Run Codex alongside other models in a pipeline: other models reason about design; Codex is the “hands-on” reviewer that inspects real code and git diffs and emits findings as JSONL.[4][2][1]

- **Red-team helper on agents**  
  - There are Codex-native red-team skills (e.g., ones that map trust boundaries, probe for prompt injection, MCP poisoning, and concealed side effects), intended exactly for adversarial passes over agent workflows.[7][4]

## Practical constraints for your parallel LLM harness

- Codex **can** answer questions and review plans/code, but the right interface is `codex` / `codex exec` / `codex review` with prompts as arguments and repo context, not “stdin prompt like a chat model.”[2][4][1]
- For an LLM council tool like your `/ai-cli`, Codex should be:
  - Either excluded from the “uniform stdin chat” group  
  - Or integrated via a dedicated adapter that:
    - Calls `codex exec "review this plan: ..."` / `codex review ...`  
    - Captures JSON or textual output  
    - Presents it as “Codex agent verdict” alongside other models’ answers.[1][2]

If you want, the next step is to design a minimal “Codex council adapter” signature (e.g., `run_codex_review(prompt, mode='plan'|'diff'|'repo')`) and map that into your existing parallel_llm orchestration instead of trying to treat Codex as just another stdin-chat CLI.

## Human

ok

## Assistant

Understood. If you want to sketch that Codex adapter (what modes you actually care about: repo review, diff review, or “plan critique”), paste your current `parallel_llm.py` and the Codex CLI you’re using and a target UX, and a minimal-change design can be drafted on top of what you already have.
