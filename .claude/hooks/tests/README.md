# Hooks Tests

This directory contains tests for Claude Code hooks.

## PowerShell Validation

### CLI Usage

```bash
# Validate a PowerShell file for argument forwarding bugs
python -m hooks.tests.test_hook_registration --validate <file.ps1>
python -m hooks.tests.test_hook_registration --powercheck <file.ps1>

# Run hook registration validation (pytest mode)
pytest test_hook_registration.py
```

### PowerShell Validation Patterns

The `PowerShellArgumentValidator` detects common bugs where wrapper functions don't forward arguments using `@Args`.

**Valid Pattern:**
```powershell
function cc-glm {
    param([Parameter(ValueFromRemainingArguments = $true)] [object[]] $Args)
    & 'script.ps1' @Args  # ✅ Correct - forwards all arguments
    claude @Args
}
```

**Invalid Pattern:**
```powershell
function broken-wrapper {
    param([string]$Path, [string]$Filter)
    & 'script.ps1' -Path $Path -Filter $Filter  # ❌ Bug - doesn't use @Args
}
```

### Exemption Patterns

The validator exempts:

1. **Parameterless functions** - Functions without a `param()` block
2. **Simple aliases** - Aliases like `p-glm` (known simple wrapper)
3. **All-optional parameters** - Functions where all parameters have defaults

```powershell
# ✅ Exempt - no param block
function simple-function {
    Write-Host "No parameters here"
}

# ✅ Exempt - known alias
Set-Alias -Name p-glm -Value 'P:\.claude\proxy\cc-glm.ps1'
```

### Bypass Flags

| Flag | Purpose |
|------|---------|
| `--no-arg-validation` | Skip argument forwarding checks (only scan file structure) |
| `--allow-alias` | Suppress alias warnings (don't report aliases) |

**Examples:**
```bash
# Skip forwarding checks (e.g., for review only)
python -m hooks.tests.test_hook_registration --validate script.ps1 --no-arg-validation

# Suppress alias warnings
python -m hooks.tests.test_hook_registration --validate script.ps1 --allow-alias
```

### Multi-Terminal Isolation

The validator uses `CLAUDE_TERMINAL_ID` environment variable to isolate cache between concurrent terminal sessions. This prevents cache collision when running validations in parallel.

**Cache location:** `P:/.claude/state/validation_cache/{terminal_id}/`

### Stale Data Immunity

The validator uses file modification time (mtime) for cache key computation. When a file is edited, the cache key changes automatically, forcing re-validation.

**Known Limitations:**

1. **Partial forwarding** - If a function forwards some arguments but not all (e.g., forwards to `claude` but not to underlying script), the validator may report a false positive.
2. **Complex functions** - Functions with advanced patterns (nested scriptblocks, dynamic invocation) may not be detected correctly.

## Test Files

| File | Purpose |
|------|---------|
| `test_hook_registration.py` | Hook registration validation + PowerShell validator CLI |
| `test_powerhook_validation.py` | Unit tests for `PowerShellArgumentValidator` |
| `test_*.py` | Other hook-specific tests |

## Running Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest test_hook_registration.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```
