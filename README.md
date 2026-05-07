# p

Solo developer monorepo for Claude Code plugins, skills, hooks, and workflow automation.

## Packages

| Package | Description |
|---------|-------------|
| [skill-guard](packages/skill-guard/) | Universal skill auto-discovery and enforcement |
| [snapshot](packages/snapshot/) | Session snapshot capture and restore across compaction |
| [cc-skills-meta](packages/cc-skills-meta/) | Meta-cognitive skills — retrospectives, gap analysis, reasoning |
| [cc-skills-sdlc](packages/cc-skills-sdlc/) | SDLC skills — architecture, planning, code quality, RCA |
| [cc-skills-utils](packages/cc-skills-utils/) | Utility skills — discovery, git operations, plugin management, search |
| [cc-skills-ai-api](packages/cc-skills-ai-api/) | Multi-provider LLM access and API gateway skills |
| [cc-skills-ai-cli](packages/cc-skills-ai-cli/) | CLI integration skills for external AI tools |
| [cc-skills-media](packages/cc-skills-media/) | NotebookLM, YouTube, and media processing skills |
| [search-research](packages/search-research/) | Unified search with async execution and HyDE enhancement |
| [prompting-toolkit](packages/prompting-toolkit/) | Prompt engineering and optimization tools |
| [csf](packages/csf/) | Claude Skills Framework — constitutional docs and standards |

## Structure

```
.claude/
  hooks/          # Python hook scripts (PreToolUse, PostToolUse, Stop, etc.)
  commands/       # Slash command definitions
  skills/         # Skill junctions (symlinks to packages/)
packages/         # Plugin packages (each with .claude-plugin/plugin.json)
```

## Development

Each package is an independent Claude Code plugin with its own `pyproject.toml`, tests, and `.claude-plugin/plugin.json`. Packages are installed locally via the plugin cache at `~/.claude/plugins/cache/local/`.
