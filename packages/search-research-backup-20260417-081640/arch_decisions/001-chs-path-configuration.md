# ADR-001: CHS Path Configuration Across Separate Repositories

**Status:** Implemented | **Date:** 2025-03-19 | **Context:** CHS path configuration fragmentation

---

## Context

Chat History Search (CHS) path configuration is fragmented across 5+ components:

| Component | Location | Path Approach |
|-----------|----------|---------------|
| CHS v2 | `P:/__csf/src/knowledge/systems/chs/v2/config.py` | `CHS_DB_PATH` env var, wrong JSONL dir |
| search-research | `P:/packages/search-research/core/config.py` | `SEARCH_RESEARCH_CHS_*` env vars |
| search-backends | `P:/packages/search-backends/backends/local/chs_incremental.py` | Imports from `...config` (MISSING) |
| semantic_daemon | `P:/packages/search-research/contrib/semantic_daemon/unified_semantic_daemon.py` | Hardcoded `Path.home()/.claude/history.jsonl` |
| claude-history CLI | `P:/packages/claude-history/src/cli.rs` | Hardcoded `C:/Users/brsth/.claude/history.jsonl` |

**Problems:**
1. Users see "not initialized" errors because components look in wrong paths
2. `search-backends` tries to import from `...config` which doesn't exist (ImportError)
3. Multiple config locations create confusion about where to set paths
4. `search-research` and `search-backends` are separate GitHub repos, creating dependency constraints

---

## Decision

### Core Principle

**search-backends MUST work standalone.** It is a shared library and cannot import from search-research.

### Architecture

```
search-research (app repo)
├── core/config.py (OWNS the paths)
└── Injects paths into backends via dependency injection

search-backends (library repo)
├── Pure backends (NO config import)
└── Accepts paths as constructor parameters OR reads env vars
```

### Contract

**Environment Variables** are the single source of truth:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SEARCH_RESEARCH_CHS_JSONL_PATH` | `~/.claude/history.jsonl` | Chat history JSONL |
| `SEARCH_RESEARCH_CHS_DB_PATH` | `P:/__csf/data/chat_history.db` | SQLite database |
| `SEARCH_RESEARCH_CHS_INDEX_PATH` | `P:/__csf/data/chat_history_faiss_424k/faiss_index.bin` | FAISS index |

**search-research** owns `CHSPaths` class and injects paths into backends.

**search-backends** provides pure backend classes with dependency injection.

---

## Consequences

### Positive

✅ **search-backends installs standalone** - No cross-repo imports
✅ **Single source of truth** - Environment variables define paths
✅ **Clear ownership** - search-research owns config, search-backends provides pure backends
✅ **Testability** - Backends can be tested with mock paths
✅ **Flexibility** - Users can override paths via environment variables

### Negative

⚠️ **Verbose API** - Backend instantiation requires 3+ path parameters
⚠️ **Migration burden** - All backend call sites must be updated
⚠️ **Documentation burden** - Both repos must document the contract

### Migration Required

1. **search-backends**: Remove `from ...config import config`, use dependency injection
2. **search-research**: Update all backend instantiations to inject paths
3. **semantic_daemon**: Update to use environment variables
4. **Documentation**: Update READMEs in both repos

---

## Examples

### From search-research (Recommended)

```python
# P:/packages/search-research/core/config.py
class CHSPaths:
    """Chat History Search paths - single source of truth."""
    CHS_JSONL_PATH: str = os.getenv(
        "SEARCH_RESEARCH_CHS_JSONL_PATH",
        str(Path.home() / ".claude" / "history.jsonl")
    )
    CHS_DB_PATH: str = os.getenv(
        "SEARCH_RESEARCH_CHS_DB_PATH",
        "P:/__csf/data/chat_history.db"
    )
    CHS_INDEX_PATH: str = os.getenv(
        "SEARCH_RESEARCH_CHS_INDEX_PATH",
        "P:/__csf/data/chat_history_faiss_424k/faiss_index.bin"
    )

# Usage in search-research
from search_research.config import CHSPaths
from search_backends import IncrementalIndexUpdater

updater = IncrementalIndexUpdater(
    db_path=CHSPaths.CHS_DB_PATH,
    index_path=CHSPaths.CHS_INDEX_PATH,
    state_path=CHSPaths.CHS_STATE_PATH,
)
```

### From search-backends (Standalone)

```python
# P:/packages/search-backends/backends/local/chs_incremental.py
class IncrementalIndexUpdater:
    """Incrementally update FAISS index - pure backend, no embedded paths."""

    def __init__(
        self,
        db_path: str,      # Caller provides
        index_path: str,   # Caller provides
        state_path: str,   # Caller provides
    ) -> None:
        self.db_path = db_path
        self.index_path = index_path
        self.state_path = state_path

# Standalone usage
import os
from search_backends import IncrementalIndexUpdater

updater = IncrementalIndexUpdater(
    db_path=os.getenv("SEARCH_RESEARCH_CHS_DB_PATH", "~/.claude/chat.db"),
    index_path=os.getenv("SEARCH_RESEARCH_CHS_INDEX_PATH", "~/.claude/index.bin"),
    state_path=os.getenv("SEARCH_RESEARCH_CHS_STATE_PATH", "~/.claude/state.json"),
)
```

---

## Alternatives Considered

### Alternative A: Config in search-backends, search-research imports it

**Rejected:** Creates cross-repo dependency where search-research depends on search-backends for basic configuration. Violates "app depends on library" principle.

### Alternative B: Duplicate config in both repos

**Rejected:** Creates synchronization burden. Divergence risk is high (already seen with `CHS_DB_PATH` vs `SEARCH_RESEARCH_CHS_DB_PATH` namespace collision).

### Alternative C: Shared config package (third repo)

**Rejected:** Over-engineering for path configuration. Adds another repo to maintain without clear benefit.

---

## References

- Pre-mortem analysis: 6 high-risk failure modes identified
- Issue: "not initialized" errors due to path fragmentation
- Related: `P:/packages/search-research/DEPENDENCY_INJECTION_REFACTOR.md`

---

**Decided by:** ADR-001 Implementation
**Implementation:** Complete - 2026-03-19
**Review Date:** 2026-09-19 (6 months post-implementation)

## Implementation Summary

**Changes Made:**
1. ✅ **search-research/chs_incremental.py**: Removed `from ...config import config`, now uses `os.getenv()` with fallback defaults
2. ✅ **search-backends**: Already compliant - uses dependency injection with environment variable fallback
3. ✅ **semantic_daemon**: No changes needed - uses `Path.home()` for JSONL (correct), `IncrementalIndexUpdater()` uses env var fallback

**Verification:**
- Both packages can be imported standalone
- Dependency injection works when caller provides paths
- Environment variable fallback provides sensible defaults
- Cross-repo dependency eliminated
