# Functional decomposition when test mocks constrain structure

**Host:** grok
**Created:** 2026-08-01
**Session:** 019fba58

## When

A refactoring plan (often from an ensemble or design doc) proposes a Protocol/Strategy pattern with new abstract types. But the existing test suite mocks functions by their module-qualified name (e.g., `mock.patch("csf.transcript._fetch_via_ytdlp")`). Introducing a class hierarchy would require rewriting all those test mocks.

## Pattern

Instead of forcing the OOP design onto code that's tested at the function level, decompose into focused **module-level functions** that achieve the same separation of concerns:

- Each extracted function has a single responsibility (validation, dispatch, finalization, logging)
- The orchestrator function becomes a thin loop that delegates to these functions
- Test mocks continue to work because the mocked functions stay at module level

## Decision criteria

Use functional decomposition when ALL of these hold:
1. Existing tests mock functions by module-qualified name
2. The protocol's methods would be thin wrappers around existing functions
3. There's no polymorphic dispatch requirement (all stages use the same call shape, just different arguments)

Use Protocol/Strategy when ANY of these hold:
1. Stages need polymorphic dispatch (different call signatures, different guard logic per stage)
2. Plugin stages may be added by external code
3. The test suite is small enough to rewrite, or uses dependency injection

## Example

`fetch_transcript_chain` (yt-is): 487-line monolith with 5 nested closures. The 6-model ensemble plan proposed 12 new types (FallbackStage Protocol, TranscriptCandidate, ExecutionContext, etc.). Instead, extracted 13 focused functions (`_try_nlm`, `_try_direct_api`, `_try_generic`, `_finalize_success`, etc.) achieving 487→136 lines (-72%) without touching any of the 84 existing test mocks.

## Falsifier

This pattern is wrong when a future stage needs true polymorphism (different call shapes, plugin extensibility). At that point, the functional decomposition should be refactored to the Protocol pattern.
