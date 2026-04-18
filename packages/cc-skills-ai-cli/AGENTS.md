# cc-skills-ai-cli

Claude Code skills monorepo containing multiple AI skill packages.

## Skills

| Skill | Description |
|-------|-------------|
| ai-cli | Parallel multi-LLM command execution |
| ai-gemini | Gemini research and engineering assistant |
| ai-chutes | Chutes AI integration |
| ai-copilot | Copilot-style code assistance |
| ai-groq | Groq AI integration |
| ai-mistral | Mistral AI integration |
| ai-nvidia | NVIDIA NIM integration |
| ai-oc-* | OpenChat/GLM variants |
| ai-pi-* | Pi coding agent variants |
| ai-qwen | Qwen integration |
| ai-vibe | Vibe code assistance |

## Structure

```
cc-skills-ai-cli/
├── .claude-plugin/     # Claude Code plugin manifest
├── scripts/            # Utility scripts
├── hooks/              # Hook definitions (future)
└── skills/             # Individual skill packages
    ├── ai-cli/
    ├── ai-gemini/
    └── ...
```
