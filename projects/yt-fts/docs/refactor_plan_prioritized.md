# yt-fts Refactoring Plan
**Prioritized based on multi-LLM analysis (Gemini, Qwen, Codex)**
**Date:** 2026-01-05

## Severity Legend

| Severity | Criteria | Examples |
|----------|----------|----------|
| **CRITICAL** | Security vulnerabilities, data integrity risks | Arbitrary code execution, DB locking |
| **HIGH** | Architectural integrity, breaking changes imminent | Duplicate plugin systems |
| **MEDIUM** | Maintainability, consistency issues | Console duplication, validation duplication |
| **LOW** | Easy wins, low impact | log_msg() duplication |

---

## Phase 1: Security & Critical Infrastructure

### 1.1 Fix Plugin Discovery Security Risk [CRITICAL]
**Source:** Codex analysis
**Location:** `src/yt_fts/display/discovery.py:17,62,105`

**Issue:** Plugin discovery executes arbitrary code from user config dirs with silent exception swallowing.

**Actions:**
1. Add allowlist for plugin directories
2. Log all plugin load failures (remove silent `except Exception:` blocks)
3. Add opt-in flag for config-dir plugins
4. Consider switching to `importlib.metadata` entry points

**Risk if deferred:** Arbitrary code execution vulnerability

**Files:**
- `src/yt_fts/display/discovery.py`

---

### 1.2 Database Connection Centralization [HIGH → CRITICAL]
**Source:** Gemini analysis
**Location:** 90+ locations with `sqlite3.connect()`

**Issue:** Direct `sqlite3.connect()` calls with inconsistent timeouts (2s vs 5s vs default) and isolation levels. Threatens data integrity and concurrency.

**Actions:**
1. Create `DatabaseConnectionFactory` in `yt_fts/db/factory.py`
2. Implement context manager for connections
3. Standardize: WAL mode, 5-second timeout, proper isolation level
4. Replace all direct `sqlite3.connect()` calls

**Risk if deferred:** Database locking bugs, data corruption

**Files:** 90+ files (grep audit required)

---

## Phase 2: Architectural Consolidation

### 2.1 Plugin System Unification [HIGH]
**Source:** All 3 LLMs (unanimous #1 priority)
**Locations:**
- `src/yt_fts/display/base.py:40` (new system)
- `src/yt_fts/ui/plugins/base.py:11` (legacy system)
- `src/yt_fts/display/registry.py:14`
- `src/yt_fts/ui/plugins/__init__.py:8`

**Issue:** Two incompatible DisplayPlugin hierarchies + duplicate registries

**Approach (Codex recommendation):**
1. Keep new `display/` API as primary
2. Create `LegacyDisplayPluginAdapter` wrapping `ui.plugins`
3. Deprecate old registry, add migration warnings
4. Eventually re-export `ui.plugins → display.plugins`

**Risk:** Circular imports, breaking existing workflows

**Files:**
- `src/yt_fts/display/base.py`
- `src/yt_fts/ui/plugins/base.py`
- `src/yt_fts/display/registry.py`
- `src/yt_fts/display/discovery.py`

---

### 2.2 Consolidate Duplicate Classes [HIGH]
**Source:** Codex analysis

| Duplicate | Locations | Action |
|-----------|-----------|--------|
| `StatusDisplay` | `core/status_display.py:24`, `ui/status_display.py:19` | Merge, keep one |
| `FastChannelResolver` | `download/fast_channel_resolver.py:13`, `services/fast_channel_resolver.py:108` | Merge, keep one |
| `validate_display_options()` | `cli.py:91`, `batch_display.py:192` | Extract to shared module |

---

### 2.3 Fix Duplicate Exception Classes [HIGH]
**Source:** Previous code review
**Locations:**
- `src/yt_fts/exceptions.py`
- `src/yt_fts/exceptions/channel_processing.py`

**Issue:** `ChannelProcessingError` defined in two places

**Action:** Consolidate into single exceptions module

---

## Phase 3: Global State & Consistency

### 3.1 Console Object Unification [MEDIUM → HIGH]
**Source:** All 3 LLMs
**Locations:** 30+ module-level `console = Console()`

**Issue:**
- `utils/rich_console.py` exists but unused
- Module-level singletons create global state
- Cannot enforce global `--quiet` or `--no-color` flags
- Terminal state conflicts between instances

**Actions:**
1. Enforce use of `utils/rich_console.get_console()`
2. Replace all `console = Console()` with factory call
3. Add configuration injection for quiet/color modes

**Files:**
- `src/yt_fts/core/cli.py:43` (and multiple other lines)
- `src/yt_fts/core/batch_display.py:13`
- `src/yt_fts/core/batch_loaders.py:16`
- `src/yt_fts/core/batch_quota.py:11`
- `src/yt_fts/core/batch_execution.py:10`
- 25+ other files

**Risk:** Circular imports when centralizing (Gemini warning)

**Mitigation:** Place factory in standalone leaf module (`yt_fts.config` or `yt_fts.common`)

---

### 3.2 Logging Utility Unification [MEDIUM]
**Source:** All 3 LLMs
**Locations:**
- `src/yt_fts/core/batch_loaders.py:29`
- `src/yt_fts/core/batch_quota.py:14`
- `src/yt_fts/core/batch_filter.py`
- `src/yt_fts/core/parallel_processor.py`
- `src/yt_fts/core/cli.py:1996`

**Issue:** `log_msg()` duplicated 5+ times, uses raw stderr writes

**Actions:**
1. Extract to `utils/logging.py`
2. Integrate with existing `dual_sink_logger.py`
3. Replace all duplicates

---

## Phase 4: Maintainability & Standards

### 4.1 Configuration Management [MEDIUM]
**Source:** Qwen analysis

**Actions:**
1. Centralize settings in single config module
2. Add type hints for configuration
3. Document all config options

---

### 4.2 Exception Hierarchy Standardization [MEDIUM]
**Source:** Qwen analysis

**Actions:**
1. Implement consistent exception hierarchies
2. Add error codes for common failures
3. Document error handling patterns

---

### 4.3 Type Annotations [LOW → MEDIUM]
**Source:** Qwen analysis

**Actions:**
1. Add comprehensive type hints across modules
2. Run mypy strict mode
3. Fix type errors incrementally

---

### 4.4 Test Structure Consistency [LOW]
**Source:** Qwen analysis

**Actions:**
1. Ensure consistent testing patterns
2. Add coverage for consolidated modules
3. Integration tests for refactored components

---

## Execution Order

```
Week 1: Security + Critical
├── 1.1 Plugin discovery security (1 day)
└── 1.2 Database connection factory (2-3 days)

Week 2-3: Architectural Consolidation
├── 2.1 Plugin unification (5-7 days)
├── 2.2 Duplicate class consolidation (2 days)
└── 2.3 Exception consolidation (1 day)

Week 4: Global State
├── 3.1 Console unification (3-4 days)
└── 3.2 Logging utility (1-2 days)

Week 5+: Maintainability
├── 4.1 Config management
├── 4.2 Exception hierarchy
├── 4.3 Type hints (ongoing)
└── 4.4 Tests (ongoing)
```

---

## Testing Strategy

Per refactor analysis recommendations:

1. **Smoke test suite** before starting
2. **Unit tests** for extracted utilities (Console factory, DB factory, logging)
3. **Integration tests** for plugin system after consolidation
4. **Manual testing checklist** for UI output changes
5. **Regression prevention** - verify no removed functions with tests

---

## Risk Summary

| Phase | Primary Risk | Mitigation |
|-------|--------------|------------|
| 1 | Breaking existing DB behavior | Comprehensive test coverage first |
| 2 | Circular imports, breaking changes | Leaf module placement, adapter pattern |
| 3 | Terminal state conflicts | Singleton enforcement, careful testing |
| 4 | Scope creep, endless refactoring | Time-box each phase, focus on value |

---

## Constitutional Compliance Notes

- **C.1 (Singular Dev Authority):** All patterns chosen are implementable by one developer
- **C.3 (Value Maximization):** Database and security fixes are inevitable problems (strategic complexity)
- **E.1 (Exploration Before Planning):** Codebase fully explored via 3 LLM agents + original analysis
- **P (Testing Workflow):** Integration tests required for each phase completion
