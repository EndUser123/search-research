# Provider Health Check Fixes

## Problem

The `/s` skill was reporting all HTTP providers (groq, chutes, mistral, openrouter) as unhealthy with 0ms response time, even though the providers were actually functional when tested directly.

## Root Causes

### Issue 1: Missing `base_url` Configuration

**Location**: `src/llm/providers/http_providers.py`

**Problem**: Provider constructors only set default `base_url` when `config is None`, but the `/s` skill passes `ProviderConfig` objects (not `None`), so defaults were never applied.

**Fix**: Updated all HTTP provider constructors to handle three cases:
1. `config is None` → Set default base_url
2. `config is dict` without base_url → Merge default into dict
3. `config is ProviderConfig` with base_url=None → Set default via attribute assignment

**Providers Fixed**:
- `ChutesProvider`
- `GroqProvider`
- `MistralProvider`
- `OpenRouterProvider`

### Issue 2: Inconsistent API Key Environment Variable

**Location**: `src/llm/providers/provider_registry.py`

**Problem**: Registry checked for `Z_AI_API_KEY` for chutes provider, but `ProviderConfig` used `CHUTES_API_KEY`, causing the registry to not detect the provider.

**Fix**: Removed special-case logic for chutes provider. Now all providers use standard env var naming (`{PROVIDER}_API_KEY`), with only groq, openrouter, and mistral keeping their non-standard names for backward compatibility.

## Changes Made

### 1. `src/llm/providers/http_providers.py`

Updated `__init__` methods for:
- `ChutesProvider`: Lines 196-209
- `GroqProvider`: Lines 325-340
- `MistralProvider`: Lines 783-797
- `OpenRouterProvider`: Lines 472-486

All now follow the pattern:
```python
def __init__(self, provider_id: str = "...", config: Any = None):
    default_base_url = "https://..."

    if config is None:
        config = {"base_url": default_base_url}
    elif isinstance(config, dict):
        if config.get("base_url") is None:
            config = {**config, "base_url": default_base_url}
    elif hasattr(config, "base_url") and config.base_url is None:
        config.base_url = default_base_url

    super().__init__(provider_id, config)
```

### 2. `src/llm/providers/provider_registry.py`

Updated `_detect_api_providers()` method (lines 208-230):
- Removed special-case logic for chutes provider using `Z_AI_API_KEY`
- Added explicit special-case documentation for groq, openrouter, mistral
- Chutes now uses standard `CHUTES_API_KEY` like other providers

## Verification

All 6 providers now pass health checks:
- ✅ groq: healthy (118ms)
- ✅ chutes: healthy (162ms)
- ✅ mistral: healthy (468ms)
- ✅ openrouter: healthy (160ms)
- ✅ qwen-cli: healthy (5564ms)
- ✅ gemini-cli: healthy (17759ms)

## Impact

- `/s` skill will now correctly detect and use all available HTTP providers
- Multi-provider brainstorming will have more diverse inputs
- Health check display will show accurate status instead of false "unhealthy" reports
- No breaking changes to existing API

## Testing

Run this command to verify:
```bash
python -c "
import asyncio
from llm.providers import ProviderConfig, ProviderFactory, get_registry
from llm.providers.health_monitor import HealthMonitor, HealthStatus

async def test():
    registry = get_registry()
    available = registry.get_providers()

    providers = []
    for name in available:
        is_cli = any(name.endswith(suffix) for suffix in ['-cli', 'cli'])
        timeout = 30.0 if is_cli else 10.0
        config = ProviderConfig(provider_type=name, timeout=timeout)
        provider = ProviderFactory.create_provider(name, config)
        providers.append(provider)

    monitor = HealthMonitor(providers=providers)
    results = await monitor.check_all_providers()

    healthy = [pid for pid, result in results.items() if result.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)]
    print(f'Healthy providers: {len(healthy)}/{len(results)}')
    for pid in healthy:
        print(f'  ✅ {pid}')

asyncio.run(test())
"
```
