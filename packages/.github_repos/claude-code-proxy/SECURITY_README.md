# Security Configuration Guide for claude-code-proxy

This guide documents the security hardening implemented for the claude-code-proxy, ensuring secure credential storage, encrypted logging, and proper file permissions.

## Overview

The claude-code-proxy security implementation addresses:
- **Secure credential storage** using Windows Credential Manager
- **TLS 1.3 enforcement** for outbound API connections
- **Log sanitization** with sensitive data redaction
- **AES-256-GCM encryption** for logs at rest
- **7-day log retention** with automated cleanup
- **Owner-only file permissions** (600 equivalent)

## Quick Start

### 1. Initial Security Setup

Run the security setup script:

```powershell
python setup_security.py
```

This script:
- Verifies .gitignore excludes sensitive files
- Generates LOG_ENCRYPTION_KEY for log encryption
- Creates cleanup_logs.py for automated log cleanup
- Creates Windows scheduled task for daily cleanup (Windows only)
- Sets secure file permissions on sensitive files

### 2. Store API Keys Securely

```powershell
# OpenAI
python credential_manager.py set OPENAI_API_KEY sk-...

# OpenRouter
python credential_manager.py set OPENROUTER_API_KEY sk-or-...

# MiniMax
python credential_manager.py set MINIMAX_API_KEY ...
```

### 3. Create Terminal-Specific Config

```powershell
# Terminal 1 (researcher → Grok)
cp config.yaml.example config-terminal1.yaml
# Edit: port: 3001, subagents.mappings.researcher: "openrouter/x-ai/grok-code-fast-1"

# Terminal 2 (code-reviewer → GPT-4o)
cp config.yaml.example config-terminal2.yaml
# Edit: port: 3002, subagents.mappings.code-reviewer: "openrouter/openai/gpt-4o"

# Terminal 3 (implementer → MiniMax)
cp config.yaml.example config-terminal3.yaml
# Edit: port: 3003, subagents.mappings.implementer: "openrouter/minimax/minimax-m2"
```

### 4. Start Proxy with Secure Configuration

```powershell
# Load credentials from Windows Credential Manager
$env:OPENAI_API_KEY = python "P:/packages/.mcp/claude-code-proxy/credential_manager.py" get OPENAI_API_KEY
$env:OPENROUTER_API_KEY = python "P:/packages/.mcp/claude-code-proxy/credential_manager.py" get OPENROUTER_API_KEY

# Start proxy
.\run.sh
```

## Security Features

### 1. Windows Credential Manager Integration

API keys are stored in Windows Credential Manager, NOT in:
- Environment variables (visible in process list)
- Config files (visible in git history)
- Shell history (visible in bash/PowerShell history)

**Benefits:**
- Encrypted storage using Windows Data Protection API (DPAPI)
- No plaintext exposure in filesystem or memory dumps
- Centralized credential management

### 2. TLS 1.3 Enforcement

Outbound connections to provider APIs use:
- **Minimum TLS version**: TLSv1.3
- **Certificate verification**: Enabled
- **Revocation checking**: Enabled

**Configuration template:** `config-security.yaml.template`

### 3. Log Sanitization

Sensitive patterns are redacted from logs:
- `sk-[a-zA-Z0-9]{32,}` - OpenAI API keys
- `sk-or-[a-zA-Z0-9]{32,}` - OpenRouter API keys
- `sk-ant-[a-zA-Z0-9]{32,}` - Anthropic API keys
- `Bearer sk-[a-zA-Z0-9]{32,}` - Bearer tokens

### 4. AES-256-GCM Log Encryption

Logs are encrypted at rest using:
- **Algorithm**: AES-256-GCM
- **Key**: Generated via `secrets.token_urlsafe(32)`
- **Storage**: Environment variable `LOG_ENCRYPTION_KEY`

### 5. Automated Log Cleanup

- **Retention period**: 7 days
- **Schedule**: Daily at 2 AM (Windows Task Scheduler or cron)
- **Manual cleanup**: `python cleanup_logs.py`

### 6. File Permissions

| File Type | Permission | Windows Equivalent |
|-----------|-----------|-------------------|
| Config files | 600 (owner-only) | icacls (Full Control to owner only) |
| Log files | 600 (owner-only) | icacls (Full Control to owner only) |
| Database files | 600 (owner-only) | icacls (Full Control to owner only) |

## Multi-Terminal Security

Each terminal gets:
- Unique port (3001-3010)
- Isolated config file (config-terminalN.yaml)
- Independent proxy instance
- No shared state or credentials

**Verification:**
```powershell
# Terminal 1
Start-Process python -ArgumentList "credential_manager.py,get,OPENAI_API_KEY" -RedirectStandardOutput

# Terminal 2
Start-Process python -ArgumentList "credential_manager.py,get,OPENROUTER_API_KEY" -RedirectStandardOutput
```

## Rollback Procedure

If security setup causes issues:

```powershell
# Stop scheduled task
schtasks /delete /tn "claude-code-proxy-log-cleanup"

# Remove .env encryption key
# (Edit .env and remove LOG_ENCRYPTION_KEY line)

# Restore direct Anthropic access
# (Unset ANTHROPIC_BASE_URL environment variable)
```

## Verification Checklist

- [ ] Run `python setup_security.py`
- [ ] Store API keys via `credential_manager.py set`
- [ ] Create terminal-specific configs
- [ ] Verify .gitignore excludes sensitive files
- [ ] Run `python cleanup_logs.py` manually to test
- [ ] Verify scheduled task created (Windows: `schtasks /query | findstr claude`)
- [ ] Test proxy startup with credentials loaded

## Troubleshooting

### "Credential not found" error

```powershell
# List stored credentials
python credential_manager.py list

# Re-store missing credential
python credential_manager.py set OPENAI_API_KEY sk-...
```

### "Access denied" on icacls

Run PowerShell as Administrator:
```powershell
# Run as Administrator
python setup_security.py
```

### Logs not being cleaned

```powershell
# Manual cleanup
python cleanup_logs.py

# Check scheduled task
schtasks /query | findstr claude
```

## Security Best Practices

1. **Never commit API keys** to git repository
2. **Use credential_manager.py** for all API key storage
3. **Run setup_security.py** on initial setup
4. **Verify file permissions** after creating configs
5. **Run cleanup_logs.py** regularly or verify scheduled task
6. **Rotate encryption keys** periodically (re-run setup_security.py)

## References

- [Windows Credential Manager](https://support.microsoft.com/en-us/windows/what-is-credential-manager)
- [AES-GCM Encryption](https://en.wikipedia.org/wiki/Galois/Counter_Mode)
- [TLS 1.3](https://en.wikipedia.org/wiki/Transport_Layer_Security#TLS_1.3)
