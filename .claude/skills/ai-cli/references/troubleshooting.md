# Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `opencode failed` | Missing API key | Set `CHUTES_API_KEY` env var |
| `gemini blocked` | .gitignore issue | Auto-retries with `--include-directories` |
| `CLI not found` | Not installed | Install: `npm install -g qwen-code` etc. |
| Timeout | Complex query | Use `--timeout 300` for longer tasks |
