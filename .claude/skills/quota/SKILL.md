---
name: quota
description: API Provider Quota Status Checker
version: 1.0.0
status: stable
category: utilities
triggers:
  - /quota
aliases:
  - /quota

suggest:
  - /llm-health
  - /llm-performance
  - /nse
---

# API Quota Status Checker

Check API credit balances and request quotas for all configured LLM providers.

## Purpose

API Provider Quota Status Checker for monitoring credit balances and request quotas across all configured LLM providers.

## Project Context

### Constitution/Constraints
- Real-time API status checks only
- No continuous monitoring (on-demand only)
- Solo-developer quota management

### Technical Context
- Located at: `P:/__csf/src/features/commands/quota.py`
- Quota utilities: `P:/__csf/src/lib/llm_providers/utils/quota_checker.py`
- API Key Manager: `P:/__csf/src/zen_integration/api_key_manager.py`

### Architecture Alignment
- Integrates with `/llm-health` for provider status
- Works alongside `/llm-performance` for metrics
- Suggests `/nse` for intelligent recommendations

## Your Workflow

1. **Parse Arguments**: Extract provider, format, quiet options
2. **Query Providers**: Check quota status for each provider
3. **Aggregate Results**: Compile status across all providers
4. **Display Output**: Show warnings, errors, or full status
5. **Return Code**: 0 (all available), 1 (provider error)

### Supported Providers
- **OpenRouter**: Credit balance (real-time API)
- **Chutes**: Daily requests 300 (real-time API)
- **Groq/Mistral**: API availability (real-time API)
- **Qwen-CLI/Gemini-CLI/ZAI-Claude**: N/A (unsupported)

## Validation Rules

### Exit Codes
- **0**: All checked providers are available
- **1**: A provider has an actual error

### Prohibited Actions
- Do not implement continuous monitoring (on-demand only)
- Do not cache quota results beyond session lifetime

## Usage

```bash
python P:/__csf/src/features/commands/quota.py [OPTIONS]
```

## Quick Reference

| Command | Action |
|---------|--------|
| `/quota` | Check all providers |
| `/quota openrouter` | Check OpenRouter only |
| `/quota --quiet` | Only show warnings |
| `/quota --json` | JSON output |

## Options

- `--quiet` or `-q` → Show only warnings/errors
- `--json` → Output as JSON
- `--provider <name>` or `-p <name>` → Check specific provider only
- `--help` or `-h` → Show help

## Supported Providers

| Provider | Quota Type | Status Check |
|----------|------------|--------------|
| **OpenRouter** | Credit balance | ✅ Real-time API |
| **Chutes** | Daily requests (300) | ✅ Real-time API |
| **Groq** | Rate limits | ✅ API availability |
| **Mistral** | API availability | ✅ API availability |
| **Qwen-CLI** | N/A | ❌ Unsupported |
| **Gemini-CLI** | N/A | ❌ Unsupported |
| **ZAI-Claude** | N/A | ❌ Unsupported |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checked providers are available |
| 1 | A provider has an actual error |

## Integration

- **Quota utilities:** `P:\__csf\src\lib\llm_providers\utils\quota_checker.py`
- **API Key Manager:** `P:\__csf\src\zen_integration\api_key_manager.py`
