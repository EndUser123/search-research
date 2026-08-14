---
title: "┌────────┬────────────────────────────────────┐
  │  CLI   │  Supports @file in Headless Mode   │
  ├────────┼────────"
date: "2026-01-24"
mode: "COPILOT"
uuid: "3de8236d-6d22-491a-ad6b-fe149f066dfb"
entry_count: 4
---

## Human

┌────────┬────────────────────────────────────┐
  │  CLI   │  Supports @file in Headless Mode   │
  ├────────┼────────────────────────────────────┤
  │ qwen   │ ✅ YES                             │
  ├────────┼────────────────────────────────────┤
  │ gemini │ ✅ YES                             │
  ├────────┼────────────────────────────────────┤
  │ vibe   │ ✅ YES                             │
  ├────────┼────────────────────────────────────┤
  │ codex  │ ❌ NO (uses @ for config profiles) │
  └────────┴────────────────────────────────────┘

Is there a way to pass context or a file path to codex cli?

## Assistant

Codex CLI supports passing file paths or context using the `@filename` syntax directly in interactive prompts, where it reads the file contents from your project directory. For headless/non-interactive mode via `codex exec`, use `-` to pipe file contents from stdin or include file paths in the prompt string for automatic context loading.[1][2][3][4]

## Interactive Usage
Use `@path/to/file` in your prompt to inject file context without manual approval prompts (set `--ask-for-approval never` or config `approval_policy = "never"`).[2][1]
- Example: `codex "Review code in @src/main.py and suggest fixes" --ask-for-approval never`[5]

## Headless Mode
Run `codex exec "your prompt with @file references"` for non-interactive execution, streaming JSON events to stderr and final output to stdout.[3]
- Pipe context: `cat context.txt | codex exec - "Task using this context"`[4]
- Auto-context includes project files; sandbox limits apply (e.g., `--sandbox workspace-write`).[3]

## Config Profiles
The `@` symbol is reserved for selecting profiles via `--profile @name` or config.toml, but this doesn't conflict with prompt `@file` usage. Edit `~/.codex/config.toml` for defaults like auto-file access.[6][7][1]

## Human

Which other CLIs support @file in headless mode

## Assistant

**qwen, gemini, and vibe CLIs support @file-style context injection or equivalent file piping in headless modes, similar to your table.** These tools use stdin piping (`cat file.txt | cli -p "prompt"`) or flags like `--all-files`/`--include-directories` for non-interactive file context.[1][2]

## qwen CLI
Supports headless via `--prompt` or stdin, with file redirection examples like `cat src/auth.py | qwen -p "Review..."` and context flags (`--all-files`, `--include-directories`).[2]
- JSON/stream output for automation.[2]

## gemini CLI
Headless with `-p` flag accepts stdin/files (`cat file | gemini -p "query"`), directory inclusion, but direct `@file` in non-interactive is a requested feature (open issue).[1][3]
- Structured JSON events for scripting.

## vibe CLI
File context via arguments or auto-selection in commands like `vyb code file.py`; supports relevant file inclusion without explicit @ but in CLI-driven prompts.[4]
- Guarded changes and project scoping.[4]

## Human

that's all the clis

## Assistant

No, several other CLI AI coding agents beyond qwen, gemini, and vibe support @file or equivalent file context (stdin piping, --file flags) in headless/non-interactive modes.[1][2]

## Additional CLIs
- **Aider**: Headless via `aider file1.py file2.py --message "prompt"`; auto-maps repo files for context.[2][3]
- **OpenCode**: Supports `--files file.txt` or stdin in CLI; 75+ models with project scanning.[4][2]
- **Plandex**: Indexes directories (`plandex init`), uses files in plans; massive context headless.[3][1]
- **llm CLI**: Pipes files (`llm -f file.txt "prompt"`) or stdin; plugin-based for models.[5][6]

## Comparison Table
| CLI      | Headless Command Example                  | File Context Method       | [1][2] |
|----------|-------------------------------------------|---------------------------|------------------|
| Aider   | `aider *.py --message "refactor"`        | Args, repo map            |                  |
| OpenCode| `opencode --files src/ "task"`            | --files, stdin            |                  |
| Plandex | `px plan "multi-file edit"`               | Indexed dirs              |                  |
| llm     | `llm -f context.txt "analyze"`            | -f flag, stdin            | [5]         |

## Human

is there an advantage between cli and api in headless mode?

## Assistant

CLI tools offer advantages in headless mode for developer workflows like automation and scripting, while direct APIs excel in integration, speed, and customization.[1][2]

## CLI Advantages
- Simplified repo awareness, file auto-context (@file, directory scanning), and built-in safeguards (e.g., diff reviews, sandboxing) without coding state management.[3][1]
- Ideal for terminal scripting, CI/CD (e.g., `codex exec "fix bugs" | git commit`), and quick agentic tasks with minimal setup.[4][2]
- Privacy/local model support in open-source options like aider or llm.[2]

## API Advantages
- Lower latency, precise control over params/system prompts, and no TUI overhead for high-volume or embedded use (e.g., in apps, loops).[5][6]
- Easier scaling, standardization across providers, and JSON streaming for parsing in scripts.[7][8]
- Cost-effective for simple prompts; avoids CLI process startup (~seconds saved).[9]

## Comparison Table
| Aspect          | CLI Headless Edge                  | API Headless Edge                  | [2][1] |
|-----------------|------------------------------------|------------------------------------|------------------|
| Setup/Usability | Repo tools built-in (git, edits)  | Custom scripting needed            |                  |
| Latency         | Higher (process spin-up)          | Lower, direct calls                | [9]         |
| Context Mgmt    | Automatic file/repo injection     | Manual via messages/tools          |                  |
| Use Case Fit    | Dev automation/CI                 | App integration/high throughput    | [3]         |
