---
title: "What the final proposed structure?"
date: "2025-12-14"
mode: "COPILOT"
uuid: "0b1f1bde-a565-446b-b9c9-463a13e1c46b"
entry_count: 3
---

## Human

What the final proposed structure?

## Assistant

The final proposed structure groups everything under a small set of top‑level roots on `P:\` with a normalized layout inside `__csf.nip` and `projects`.[1]

## P:\ root

- `P:\.claude\` – Claude Code runtime: hooks, commands, agents, config.[1]
- `P:\.speckit\` – Speckit config that must be kept.[1]
- `P:\.vscode\` – Editor config.[1]
- `P:\.git` / `.gitignore` etc. – VCS metadata.[1]
- `P:\__csf.nip\` – Cognitive Steering Framework source and internals only.[1]
- `P:\projects\` – All actual project work, experiments, and one‑off tasks.[1]

Everything else at `P:\` root is considered misplaced and should be classified as DELETE / MOVE / REVIEW under the cleanup prompt.[1]

## __csf.nip internal layout

Inside `P:\__csf.nip\` the allowed structure is narrowed to CSF library and tooling folders only:[1]

- `src\` – Core CSF library code, including `lib\`, `modules\`, etc. (anything currently under `lib`/`modules` should be moved here).[1]
- `commands\` – CSF command implementations.[1]
- `config\` – CSF configuration.[1]
- `data\` – CSF data files.[1]
- `docs\` – CSF documentation and design notes.[1]
- `tests\` – CSF tests (unit, integration, regression).[1]
- `scripts\` – Utility scripts for CSF development.[1]
- `tools\` – CSF utility tools and helpers.[1]

Directories like `projects`, `lib` at root, `modules` at root, or `hooks` under `__csf.nip` are marked for future cleanup/move (e.g., `lib` → `src/lib`, `modules` → `src/modules`, `hooks` → `.claude/hooks` or `docs`).[1]

## projects layout

`P:\projects\` is the catch‑all for actual work and experiments that should not live under `__csf.nip\`:[1]

- One subdirectory per project or experiment, for example:  
  - `P:\projects\cwo12-truth-assessment\` – planning docs and tasks.[1]
  - `P:\projects\model-testing\` – LLM model testing scripts.[1]
  - Additional archived or legacy work can be moved into `P:\projects\ARCHIVED\` if desired.[1]

Within each project, you are free to use conventional `src/`, `docs/`, `tests/`, etc., but those live under the project folder, not under `P:\__csf.nip\`.[1]

## Human

please show what .claude should have according to the doc?

## Assistant

According to the doc, `.claude` is a thin Claude Code runtime surface with a very specific allowed layout.[1]

## Allowed subdirectories

These subdirectories under `P:\.claude\` are considered valid and are allow‑listed:[1]

- `commands/` – Slash command stubs (markdown with metadata pointing into `P:\__csf.nip\commands\`).[1]
- `hooks/` – Runtime hooks for things like path validation and protections.[1]
- `agents/` – Subagent definitions used by commands/skills.[1]
- `logs/` – Runtime logs and diagnostics.[1]
- `skills/` – Agent skills, each as a directory with `SKILL.md` plus optional helper files.[1]
- `rules/` – Modular rule files (`.md`) that complement `claude.md`.[1]
- `.claude-plugin/` – Plugin metadata and plugin‑installed assets.[1]

Anything like `projects/`, `tests/`, `data/`, `plans/`, `helpers/`, `proxy/`, `cache/`, `backups/`, nested `.claude/` or `__csf.nip/`, or random code directories under `.claude` is explicitly blocked.[1]

## Allowed root files

Only a constrained set of files is allowed at `P:\.claude\` root:[1]

- `settings.json`, `settings.local.json` – Main and local config.[1]
- `claude.md`, `claude.local.md` – Project and personal instructions.[1]
- `.mcp.json` – MCP server configuration.[1]
- `current_session.json`, `sessions.json`, `session_config.json`, `mutex_session.json`, `orchestrated_session.json` – Session/state tracking files.[1]
- `hook_validation_results.json`, `deliberate_hook_changes.jsonl` – Hook validation outputs and change logs.[1]
- `.session_start_lock` – Lock file to coordinate session startup.[1]

Any other arbitrary scripts, markdown docs, or config blobs at `.claude` root are treated as violations by the protection rules.[1]

## Human

can you show it with ascii, like a tree command would?

## Assistant

P:\.claude\ tree, as implied by the doc, looks like this:[1]

```text
P:\.claude\
├── claude.md
├── claude.local.md
├── settings.json
├── settings.local.json
├── .mcp.json
├── current_session.json
├── sessions.json
├── session_config.json
├── mutex_session.json
├── orchestrated_session.json
├── hook_validation_results.json
├── deliberate_hook_changes.jsonl
├── .session_start_lock
├── commands\
│   └── ...        # slash command stub .md files
├── hooks\
│   └── ...        # runtime hook files & configs
├── agents\
│   └── ...        # subagent definitions
├── logs\
│   └── ...        # runtime logs
├── skills\
│   ├── some-skill-name\
│   │   ├── SKILL.md
│   │   └── ...    # optional scripts/templates
│   └── ...
├── rules\
│   ├── code-style.md
│   ├── testing.md
│   ├── security.md
│   └── ...        # other rule files / subdirs
└── .claude-plugin\
    └── plugin.json   # plus any plugin metadata/assets
```
