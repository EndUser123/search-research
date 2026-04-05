# Architecture Decision: Checkpoint Package Improvement Priorities

**Date:** 2026-02-10
**Package:** checkpoint v0.2.0
**Context:** Evaluating 15+ suggestions from 3 external LLM analyses (Aurora Alpha, Pony Alpha, Step 3.5 Flash, Nemotron 3 Nano)

---

## Decision

Pursue 4 high-value improvements immediately; defer 4 nice-to-haves; reject 7 enterprise/infrastructure patterns inappropriate for solo-dev context.

---

## Priority Matrix

### P0 - Do Immediately (2-7 minutes)

| Idea | Evidence | Effort |
|------|----------|--------|
| Fix version mismatch (0.2.0 → 0.1.0 in pyproject.toml) | `__init__.py:28` shows 0.2.0, `pyproject.toml:7` shows 0.1.0 | 2 min |
| Remove unused `click` dependency | `pyproject.toml:29` has click>=8.0, but `checkpoint.cli:main` removed | 5 min |
| Remove orphaned entry_point | `pyproject.toml:49` references deleted cli.py | 1 min |

### P1 - This Week (2-3 days)

| Idea | Evidence | Effort |
|------|----------|--------|
| Split PreCompact_checkpoint_capture.py (2,262 lines) | File measured at 2,262 lines via wc -l | 2-3 days |

**Proposed split:**
```
hooks/
├── PreCompact_checkpoint_capture.py  (main hook, ~300 lines)
├── __lib/
│   ├── transcript_parser.py          (TranscriptParser, ~800 lines)
│   ├── checkpoint_builder.py          (CheckpointStore, ~800 lines)
│   ├── handover_generator.py          (HandoverBuilder, ~300 lines)
│   └── streaming_io.py                (TranscriptLines, atomic_write_with_retry, ~200 lines)
```

### P2 - Next Sprint (30 minutes - 2 hours)

| Idea | Evidence | Effort |
|------|----------|--------|
| Add Windows reserved filename check | Windows docs cite CON, PRN, AUX, COM1-9, LPT1-9 | 30 min |
| Add terminal_id length check (1-255 chars) | Defensive programming | 15 min |

### P3 - Defer (solo-dev overhead)

| Idea | Why Defer |
|------|-----------|
| Structured logging (logging module) | Console output sufficient for solo dev |
| Property-based tests (hypothesis) | Existing tests cover critical paths (19/21 pass) |
| SessionEnd hook | Nice-to-have, no user pain reported |
| CLI utility for inspection | Hook-only architecture by design |

### Reject - Enterprise Patterns

| Idea | Reason |
|------|--------|
| SQLite storage backend | File-based JSON appropriate for single-user |
| HMAC signing | Local trust boundary, SHA256 checksum sufficient |
| Prometheus metrics endpoint | No observability infrastructure |
| Abstract platform layer | Windows-only target environment |
| Long path UNC prefix `\\?\` | Edge case - terminal IDs are alphanumeric < 50 chars |
| Schema versioning + auto-migration | Single-user package, manual migration OK |
| Compression (zlib/lz4) | Text-heavy data, compression gains minimal |

---

## Rationale

### Python-Specific Considerations

1. **I/O-bound workload**: Already optimized with streaming (TranscriptLines) and caching (PERF-002)
2. **No async needed**: Sequential checkpoint/restore doesn't warrant asyncio complexity
3. **Hook-only architecture**: Adding CLI contradicts design intent
4. **Solo-dev context**: Eliminate infrastructure (CI, metrics, distributed systems)

### Evidence Tiers

- **Tier 1** (95% confidence): Version mismatch verified in source files
- **Tier 2** (85% confidence): Windows reserved filenames documented
- **Tier 3** (75% confidence): Solo-dev philosophy from CLAUDE.md

---

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Pursue all 15 suggestions | Solo-dev overhead exceeds benefit |
| Only fix version/click | QUAL-001 (2,262-line file) is real debt |
| Full SQLite refactor | File-based JSON is appropriate |

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Splitting file may introduce bugs | Test-driven refactor, existing coverage |
| Windows reserved names may break existing terminals | Grandfather clause for existing IDs |
| Version bump may confuse users | CHANGELOG documenting SEC/PERF fixes |

---

## Next Actions

1. **Today**: Fix version mismatch, remove click dependency
2. **This Week**: Plan PreCompact_checkpoint_capture.py split with test coverage
3. **Next Sprint**: Add Windows reserved filename validation to `utils/security.py`

---

**Confidence**: 85% - Tier 1/2 evidence from source files + solo-dev context
