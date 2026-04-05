# ADR-005: Replacing stable-ts with faster-whisper

- **Status:** Accepted
- **Date:** 2025-06-24
- **Supersedes:** [ADR-001: Subtitle Generation Dependency Strategy](ADR-001_Subtitle_Dependency_Strategy.md)

## Context

The project's subtitle generation feature was originally built using the `stable-ts` library, as documented in ADR-001. During development and dependency validation on a modern Python 3.13 environment, we encountered an unresolvable dependency conflict.

`stable-ts` requires a specific, older version of `openai-whisper` (`20240930`). This version of `openai-whisper` has packaging issues that make it impossible to build and install from source on modern Python environments. All attempts to install this dependency, either from PyPI or directly from GitHub, failed with a `KeyError: '__version__'` during the build process.

This created a hard technical blocker, making the existing implementation non-viable for future development and distribution.

## Decision

We will replace `stable-ts` with the `faster-whisper` library as our core speech-to-text engine.

The `subtitle_generator.py` adapter module will be rewritten to use the `faster-whisper` API. All other parts of the application will remain unchanged, demonstrating the value of the adapter pattern decided upon in ADR-001.

## Rationale

-   **Resolves Blocker:** This is the primary driver. `faster-whisper` and its dependencies install cleanly on modern Python environments, removing the hard installation blocker.
-   **Performance:** `faster-whisper` is a well-regarded reimplementation of Whisper, known for its significant speed improvements and lower memory usage compared to the original implementation.
-   **Maintained:** It is an actively developed project, which reduces the risk of future dependency rot.
-   **Acceptable Trade-offs:** While `stable-ts` offered smoother, continuous progress callbacks, `faster-whisper` still allows for progress reporting on a per-segment basis. This is a perfectly acceptable user experience trade-off in exchange for a stable and performant system.

## Consequences

-   **Positive:**
    -   The project is once again runnable and installable on modern platforms.
    -   Subtitle generation may be significantly faster.
    -   The project is now using a more actively maintained core dependency, reducing future risk.
-   **Negative:**
    -   The visual feedback from the subtitle progress bar is now chunk-based (updating per segment) rather than continuous.
    -   The logic in the `subtitle_generator.py` adapter has been completely replaced.
-   **Neutral:**
    -   This decision validates the original strategy of isolating the dependency in an adapter module, as described in ADR-001.
