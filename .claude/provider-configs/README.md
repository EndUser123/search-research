# Provider Configs

This directory contains the active Claude/CCR launchers and local routing helpers.

## Active commands

| Script | Profile command | Purpose |
|---|---|---|
| `cc-ccr.ps1` | `cc-ccr` | Start and test Claude Code Router; `-Usage` shows provider quotas. |
| `cc-ccr-tui.ps1` | `cc-ccr -Config` | Configure CCR routes interactively. |
| `cc-glm.ps1` | `cc-glm` | Route Claude Code through Z.ai/GLM. |
| `cc-mm.ps1` | `cc-mm` | Route Claude Code through MiniMax. |
| `proxy.ps1` | `proxy` when configured | Manage the local subagent reverse proxy. |

## CCR support files

- `cc-ccr-subscription-usage.ps1` collects OpenAI and Anthropic subscription windows without API spend reporting.
- `ccr-custom-router.js` contains the custom local-first routing logic referenced by CCR configuration.
- `ccr-admission-proxy.js` enforces the pre-CCR context admission gate.
- `ccr-fallback-log.ps1` reads CCR fallback events and writes the audit trail.
- `ccr-custom-router.test.js` tests the custom router and admission behavior.

## Configuration

- CCR routing source of truth: `C:\Users\brsth\.claude-code-router\config.json`.
- Provider secrets source of truth: `P:\.env`.
- Confirm the active PowerShell profile with `$PROFILE` before changing aliases.

Do not add API keys or subscription tokens to tracked scripts. Subscription quota collectors should use the provider's existing local login/session material and should never print credentials.
