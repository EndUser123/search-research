# ADR-20260322: sys.path Manipulation Pattern

**Status:** Accepted
**Date:** 2026-03-22
**Context:** Handoff pre-mortem analysis identified sys.path manipulation as RISK-008

## Context

The CSF (Constitutional Software Framework) is currently imported in hooks and tests using sys.path manipulation:

```python
import sys
from pathlib import Path

# Add CSF to path
csf_root = Path(__file__).resolve().parent.parent.parent.parent / "__csf" / "src"
sys.path.insert(0, str(csf_root))

# Now can import
from core.hooks.__lib.handoff_v2 import build_envelope
```

**Prevalence**: This pattern appears in 30+ files across the codebase.

**Problem**:
- Fragile: Breaks if CSF moves or project structure changes
- Non-standard: Violates Python packaging best practices (PEP 517/518)
- IDE-unfriendly: Type checkers and linters can't resolve imports
- Deployment-blocker: Won't work in installed environments

## Decision

**Install CSF as an editable package** using `pip install -e` with pyproject.toml.

### Implementation

1. **Ensure __csf has pyproject.toml** (already exists at `__csf/pyproject.toml`)
2. **Install CSF in editable mode**:
   ```bash
   cd __csf
   pip install -e .
   ```
3. **Replace sys.path manipulation** with direct imports:
   ```python
   # Before:
   import sys
   from pathlib import Path
   csf_root = Path(__file__).resolve().parent.parent.parent.parent / "__csf" / "src"
   sys.path.insert(0, str(csf_root))
   from core.hooks.__lib.handoff_v2 import build_envelope

   # After:
   from csf.hooks.__lib.handoff_v2 import build_envelope
   ```

4. **Update imports across codebase**:
   - `from core.hooks.__lib...` → `from csf.hooks.__lib...`
   - `from core.llm.providers...` → `from csf.llm.providers...`
   - `from core.commands...` → `from csf.commands...`

### Package Name Mapping

The pyproject.toml at `__csf/pyproject.toml` defines the package name. Assuming it's configured as `csf`:

```toml
[project]
name = "csf"
```

All imports from `__csf/src/core/...` become `from csf...`.

## Rationale

**Advantages**:
- **Standard**: Follows Python packaging best practices
- **Robust**: Works regardless of project structure changes
- **Tool-friendly**: IDEs, type checkers, and linters can resolve imports
- **Deployable**: Package can be installed in production environments

**Disadvantages**:
- **One-time setup**: Requires initial `pip install -e` command
- **Dependency tracking**: CSF must be reinstalled if dependencies change
- **Namespace collision**: If another package named "csf" is installed

## Multi-Terminal Safety

- **Safe**: Editable install is a local environment configuration
- **No runtime state**: No shared mutable state introduced
- **Concurrent-safe**: Multiple terminals see the same installed package

## Implementation Plan

### Phase 1: Install CSF as editable package (One-time)
```bash
cd __csf
pip install -e .
```

### Phase 2: Update imports in handoff package
1. Remove sys.path manipulation from handoff tests
2. Replace `from core.` with `from csf.`
3. Verify tests pass

### Phase 3: Update imports across codebase (Gradual)
1. Update sys.path usage in other packages
2. Remove sys.path manipulation from hooks
3. Verify all tests pass

### Phase 4: Documentation
1. Update setup instructions with `pip install -e` requirement
2. Document import pattern in CLAUDE.md

## Rollback Strategy

If issues arise:
1. Revert import changes (`from csf.` → `from core.`)
2. Restore sys.path manipulation
3. Uninstall editable package: `pip uninstall csf`

## Consequences

### Positive
- Import statements are standard Python
- IDE autocomplete and type checking work
- Project can be structured differently without breaking imports
- Package can be installed in CI/CD environments

### Negative
- One-time setup required for new developers
- CSF dependencies must be managed via pip
- Requires `pip install -e` after any dependency changes

### Alternatives Considered

1. **PYTHONPATH environment variable**
   - Simpler than editable install
   - Still non-standard and fragile
   - Rejected: Less tool-friendly than editable install

2. **Continue sys.path manipulation**
   - Works without setup
   - Rejected: Fragile and violates best practices

## Evidence Sources

- PEP 517: specifying build systems
- PEP 518: pyproject.toml
- Python packaging guide: editable installs
- Pre-mortem finding RISK-008: sys.path manipulation fragility

## Related ADRs

- ADR-20260321-handoff-v3-architecture.md: V2 handoff architecture
- ADR-20260321-gto-viability-gate-fix.md: GTO v3 architecture
