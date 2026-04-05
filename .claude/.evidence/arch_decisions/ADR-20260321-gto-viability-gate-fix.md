# ADR-20260321: GTO Viability Gate Path Resolution and Standalone Support

**Date:** 2026-03-21
**Status:** Accepted
**Decision Maker:** Claude (per user requirements)

## Context and Problem Statement

GTO v3's viability gate contains path resolution bugs and overly strict session requirements that prevent it from working in valid scenarios:

1. **Path resolution bug**: Viability gate looks for `transcript.jsonl` in project root, but actual transcripts are UUID-named files in `C:\Users\brsth\.claude\projects\P--\`
2. **Overly strict constraint**: "Previous sessions required" check prevents GTO from working in first session
3. **Unused context**: Handoff envelope contains `transcript_path` but viability gate doesn't use it
4. **Windows path issues**: Similar to the `/p` vs `P:/` problem, path resolution fails on Windows

**Success criteria:**
- GTO works in first session (no previous sessions required)
- GTO finds actual transcript files regardless of location
- GTO uses handoff envelope's transcript_path when available
- Path resolution works correctly on Windows

## Decision

**Fix the viability gate with three targeted changes:**

1. **Remove "previous sessions" requirement** - Delete `_check_previous_sessions()` entirely
2. **Use handoff envelope's transcript_path** - Read from handoff file when available
3. **Add fallback transcript detection** - Search for UUID-named transcript files in actual location

**Scope:** Changes limited to `lib/viability_gate.py` only. No changes to detectors, subagents, or orchestrator.

## Rationale

**Why this approach:**
- **Minimal change**: Fixes only what's broken, doesn't redesign the system
- **Backward compatible**: Still works with existing handoff files
- **Standalone support**: Enables `/gto` in first session (user requirement)
- **Evidence-based**: Analysis of actual transcript locations from handoff files

**Evidence sources:**
- Handoff file analysis shows: `transcript_path: "C:\\Users\\brsth\\.claude\\projects\\P--\\22e9ea78-680f-4cf6-bacd-43792631f4a4.jsonl"`
- Transcript directory scan: 29 transcript files found with UUID naming
- Windows path resolution issue: `/p` becomes `\p` in Python pathlib (discovered in session)

**Key benefits:**
- GTO works when user first runs it (no previous sessions)
- Uses actual transcript location from handoff envelope
- Fallback detection handles cases without handoff envelope

## Alternatives Considered

| Alternative | Description | Pros | Cons | Why Rejected |
|-------------|-------------|------|------|--------------|
| **Option A (CHOSEN)** | Fix viability gate with targeted changes | Minimal change, backward compatible, standalone support | Doesn't fix systemic path issues | N/A |
| Option B | Create new "lite" viability gate for standalone mode | Separate concerns, preserves existing gate | Duplicate code, maintenance burden | Unnecessary complexity |
| Option C | Move all transcripts to project root | Simplifies path resolution | Breaking change to handoff system, requires migration | Too invasive |
| Option D | Add symbolic links to actual transcripts | No code changes to handoff system | Symlinks don't work well on Windows, adds complexity | Platform-specific hack |

**Differentiation axes:** Implementation complexity vs. breaking changes

## Consequences

### Positive
- **Standalone GTO works**: First session users can run `/gto` without error
- **Correct path resolution**: Uses actual transcript location from handoff envelope
- **Better error messages**: Fallback detection provides clearer feedback
- **Windows compatibility**: Handles Windows path quirks correctly

### Negative
- **Reduced context**: Standalone GTO lacks previous session context (acceptable per user requirements)
- **Fallback latency**: UUID-named file search adds ~100ms when handoff missing (acceptable)

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Handoff file corrupt/missing | Medium | Low | Fallback to UUID search works |
| Transcript compacted during check | Low | Medium | File size check catches empty files |
| Performance regression | Low | Low | Fallback only runs when needed |

## Implementation

### Implementation Plan
- **Phase 1:** Remove `_check_previous_sessions()` from viability_gate.py | Effort: 5 minutes
- **Phase 2:** Add handoff envelope transcript_path extraction | Effort: 15 minutes
- **Phase 3:** Add fallback UUID transcript detection | Effort: 20 minutes
- **Phase 4:** Update tests to cover standalone mode | Effort: 30 minutes

**Total effort:** ~70 minutes

### Rollback Strategy
- Git revert to commit before ADR implementation
- No data migration required (no schema changes)
- Feature flag not needed (change is isolated to viability check)

### Success Criteria
- `/gto` works in first session (no handoff file)
- `/gto` uses handoff envelope's transcript_path when available
- `/gto` finds UUID-named transcripts as fallback
- All existing tests pass

## Multi-Terminal Isolation Assessment

**State sharing:** None - viability gate is read-only

**Concurrency safety:** Safe
- Multiple terminals can read handoff/transcript files simultaneously
- No write operations during viability check
- Each terminal gets independent result

**Stale data immunity:** N/A - viability gate doesn't store state

**Edge cases:**
- Handoff file deleted during check: Fallback to UUID search handles gracefully
- Two terminals run `/gto` simultaneously: Both succeed with independent results

## References
- `P:\.claude\skills\gto\lib\viability_gate.py` - Current implementation with bugs
- `P:\.claude\skills\gto\references\architecture.md` - GTO v3 architecture documentation
- `P:\packages\handoff\scripts\hooks\__lib\handoff_v2.py` - Handoff envelope structure
