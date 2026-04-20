# Codex CLI Reference

## Installation

```bash
npm install -g @openai/codex
```

## Headless Mode

**Default** — `exec` flag for unattended Bash execution:
```bash
codex exec "[prompt]"
```

- No interactive prompts
- Auto-selects best model unless `--model` is specified
- Output goes to stdout

## Key Flags

| Flag | Description |
|------|-------------|
| `exec` | Run in headless/programmatic mode |
| `-m MODEL` | Model to use (default: auto) |
| `-o FORMAT` | Output format: `text`, `json` |

## Wrapper Pattern

For file capture on Windows:
```bash
pwsh -File P:/scripts/agentic-cli.ps1 -cli "codex" -command "exec [prompt]" -outputPath "P:/tmp/codex_output.txt"
```

## Error Codes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Read output |
| Non-zero | General error | Check stderr |
