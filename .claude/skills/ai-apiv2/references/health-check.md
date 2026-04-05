# Health Check CLI

## Commands

```bash
# Check all provider health
python -m .claude.skills.ai-apiv2.scripts.cli health

# Check specific provider
python -m .claude.skills.ai-apiv2.scripts.cli health --provider chutes

# Run with inference sanity check
python -m .claude.skills.ai-apiv2.scripts.cli health --sanity
```

## What Health Checks Validate

- API key presence
- API connectivity to provider
- Optional inference test (with `--sanity` flag)

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Healthy |
| `1` | Failed |
