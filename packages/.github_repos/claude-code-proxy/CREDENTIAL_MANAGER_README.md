# Windows Credential Manager for claude-code-proxy

Secure credential storage using Windows Credential Manager. API keys are never stored in plaintext files or exposed in shell history.

## Features

- **Secure storage**: Uses Windows Credential Manager (cmdkey) to store API keys
- **No plaintext exposure**: Keys never appear in config files, shell history, or process lists
- **Runtime retrieval**: Credentials loaded at runtime from secure store
- **Multi-provider support**: Store keys for OpenAI, OpenRouter, MiniMax, etc.

## Quick Start

### 1. Store API Keys

```powershell
# OpenAI API key
python credential_manager.py set OPENAI_API_KEY sk-...

# OpenRouter API key
python credential_manager.py set OPENROUTER_API_KEY sk-or-...

# MiniMax API key
python credential_manager.py set MINIMAX_API_KEY ...
```

### 2. List Stored Credentials

```powershell
python credential_manager.py list
```

### 3. Load Credentials in Shell

```powershell
# PowerShell
$env:OPENAI_API_KEY = python "P:\packages\.mcp\claude-code-proxy\credential_manager.py" get OPENAI_API_KEY

# Bash/Git Bash
export OPENAI_API_KEY="$(python P:/packages/.mcp/claude-code-proxy/credential_manager.py get OPENAI_API_KEY)"
```

### 4. Delete Credential

```powershell
python credential_manager.py delete OPENAI_API_KEY
```

## Integration with claude-code-proxy

The proxy configuration file should NOT contain API keys. Instead:

1. Store keys in Windows Credential Manager using `credential_manager.py set`
2. Load keys as environment variables before starting the proxy
3. Proxy reads from environment variables at runtime

Example startup script:

```powershell
# load_credentials.ps1
$env:OPENAI_API_KEY = python "P:\packages\.mcp\claude-code-proxy\credential_manager.py" get OPENAI_API_KEY
$env:OPENROUTER_API_KEY = python "P:\packages\.mcp\claude-code-proxy\credential_manager.py" get OPENROUTER_API_KEY

# Start proxy
.\run.sh
```

## Security Benefits

| Traditional Approach | Credential Manager Approach |
|---------------------|------------------------------|
| Keys in .env files | Keys in Windows Credential Manager (encrypted) |
| Keys in shell history | No keys in shell history |
| Keys visible in process list | Keys not visible in process list |
| Keys in git history | No keys in git history (if .env in .gitignore) |

## Supported Providers

- `OPENAI_API_KEY` - OpenAI (GPT-4o, GPT-4o-mini)
- `OPENROUTER_API_KEY` - OpenRouter (100+ models)
- `MINIMAX_API_KEY` - MiniMax (MiniMax-M2)
- `ANTHROPIC_API_KEY` - Anthropic (for direct access, not proxied)

## Troubleshooting

### Credential not found

```
✗ Credential OPENAI_API_KEY not found
```

Make sure you stored the credential first:
```powershell
python credential_manager.py set OPENAI_API_KEY sk-...
```

### PowerShell execution policy

If you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Verify credential storage

```powershell
cmdkey /list | findstr claude-code-proxy
```

This shows all credentials stored for claude-code-proxy.
