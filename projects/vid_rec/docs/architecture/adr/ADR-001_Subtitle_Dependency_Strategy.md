# ADR-001: Subtitle Generation Dependency Strategy

- **Status:** Accepted
- **Date:** 2023-10-27

## Context

The application's subtitle generation feature is a core component of its value proposition. This functionality relies on an external, third-party library to perform the complex speech-to-text transcription. Our initial implementation uses `stable-ts`, a pure-Python fork of `openai-whisper`. This creates a direct, critical dependency on an external project whose future is not under our control.

## Decision

We will continue to use `stable-ts` as our primary subtitle generation library. However, we will enforce a strict architectural boundary by isolating all interactions with this library within a dedicated "adapter" module (`src/subtitle_generator.py`). No other part of the application will be allowed to call `stable-ts` directly.

## Rationale

-   **Why `stable-ts`?**
    -   **Pure Python:** It avoids the need for on-host C++ compilation, simplifying installation for end-users.
    -   **Progress Callbacks:** Its API provides the necessary hooks for us to build a rich, unified progress bar, which is a key UX feature.
    -   **Performance:** It is a well-regarded and performant implementation of the Whisper model.

-   **Why isolate it in an adapter module?**
    -   **Reduces Coupling:** It creates a single, well-defined point of contact with the external library.
    -   **Simplifies Future Replacement:** If `stable-ts` is abandoned or a superior library emerges, we only need to rewrite the adapter module. The rest of the application, which calls our internal `generate_subtitles_for_file` function, will not need to be changed. This contains the risk.

## Consequences

-   **Positive:** We gain a robust, well-performing feature while containing the long-term risk associated with the dependency. The architecture remains flexible.
-   **Negative:** We are still reliant on a single library for a core feature. This decision accepts that risk in the short-term in exchange for development velocity. A future task may be created to investigate a fallback or alternative implementation.
