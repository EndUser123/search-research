# Claude Code Router (CCR) Model Configuration Guide

## Overview

This guide explains how to add, remove, and modify models in your CCR setup. The
system supports two providers:

- **OpenRouter**: Aggregates models from multiple providers (Google, Anthropic,
  DeepSeek, etc.)
- **Chutes.ai**: Decentralized compute marketplace for open-weights models

## Current Configuration

Your `config.json` currently includes:

- **nova-lite**: Llama 3.2 3B Instruct via OpenRouter (free, reliable model)
- **kat-coder**: Llama 3.2 3B Instruct via OpenRouter (free, reliable model)
- **devstral-2512**: Llama 3.2 3B Instruct via OpenRouter (free, reliable model)
- **kimi-k2**: Llama 3.3 70B Instruct via Chutes.ai (powerful general model)
- **deepseek-v3.2**: Llama 3.3 70B Instruct via Chutes.ai (powerful general
  model)
- **deepseek-tee**: Llama 3.3 70B Instruct via Chutes.ai (powerful general
  model)
- **devstral-123b**: Llama 3.3 70B Instruct via Chutes.ai (powerful general
  model)

**Note:** Using proven, reliable models instead of experimental ones for
stability.

## How to Add a New Model

### Step 1: Find the Model Identifier

**For OpenRouter models:**

1. Visit https://openrouter.ai/models
2. Find your desired model
3. Copy the "ID" (e.g., `anthropic/claude-3.5-sonnet`,
   `meta-llama/llama-3.1-405b-instruct`)

**For Chutes.ai models:**

1. Visit https://chutes.ai/models or check their API documentation
2. Find the model name (e.g., `microsoft/WizardLM-2-8x22B`,
   `unsloth/Mistral-7B-Instruct-v0.3`)

### Step 2: Edit the Configuration

Open `%USERPROFILE%\.claude-code-router\config.json` and add to the `"Router"`
section:

```json
"Router": {
  "default": "openrouter:deepseek/deepseek-r1",
  "deepseek-r1": "openrouter:deepseek/deepseek-r1",
  "gemini-flash": "openrouter:google/gemini-2.0-flash-001",
  "llama-3.3": "chutes:unsloth/Llama-3.3-70B-Instruct",
  "qwen-coder": "chutes:Qwen/Qwen2.5-Coder-32B-Instruct",
  "new-model-alias": "provider:model-identifier"
}
```

### Step 3: Restart CCR

```powershell
ccr restart
```

### Step 4: Create Terminal Script

Create a new PowerShell script (e.g., `terminal6.ps1`):

```powershell
# Terminal 6: New Model Configuration
Write-Host "Configuring Client: [Model Name]" -ForegroundColor [Color]

# Clear existing authentication
claude /logout

$env:ANTHROPIC_BASE_URL = "http://127.0.0.1:3456"
$env:ANTHROPIC_API_KEY = "sk-dummy-key-terminal-6"
$env:ANTHROPIC_MODEL = "new-model-alias"
$env:API_TIMEOUT_MS = "3600000"

# Launch Claude Code
claude
```

## Examples

### Adding Claude 3.5 Sonnet (OpenRouter)

1. **Config.json addition:**

```json
"claude-3.5": "openrouter:anthropic/claude-3.5-sonnet"
```

2. **Terminal script:**

```powershell
$env:ANTHROPIC_MODEL = "claude-3.5"
```

### Adding Mistral 7B (Chutes.ai)

1. **Config.json addition:**

```json
"mistral-7b": "chutes:unsloth/Mistral-7B-Instruct-v0.3"
```

2. **Terminal script:**

```powershell
$env:ANTHROPIC_MODEL = "mistral-7b"
```

## How to Remove a Model

1. Remove the line from the `"Router"` section in `config.json`
2. Restart CCR: `ccr restart`
3. Delete the corresponding terminal script if no longer needed

## How to Modify Existing Models

1. Edit the model identifier in the `"Router"` section
2. Restart CCR: `ccr restart`
3. Update the terminal script's `$env:ANTHROPIC_MODEL` if the alias changed

## Provider-Specific Notes

### OpenRouter

- Supports most commercial models
- Handles authentication automatically
- May have rate limits based on your account tier

### Chutes.ai

- Focuses on open-weights models
- Uses decentralized compute (may have cold start delays)
- Check https://chutes.ai for available models
- Some models may require specific endpoint URLs

## Troubleshooting

**Model not found error:**

- Verify the model identifier is correct
- Check if the provider supports that model
- Ensure CCR restarted after config changes

**Connection timeout:**

- Increase `$env:API_TIMEOUT_MS` in terminal script
- Check provider status
- Verify API keys are valid

**Auth conflicts:**

- Always run `claude /logout` before setting environment variables
- Use unique dummy API keys for each terminal

## Advanced Configuration

For more advanced routing logic, you can:

- Add model-specific timeouts in the provider configuration
- Configure different API endpoints per provider
- Set up custom transformers for specific models

See the CCR documentation at https://github.com/musistudio/claude-code-router
for advanced features.
