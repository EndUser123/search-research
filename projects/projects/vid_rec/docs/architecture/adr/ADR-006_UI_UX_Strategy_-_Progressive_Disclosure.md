# ADR-006: UI/UX Strategy - Progressive Disclosure

- **Status:** Accepted
- **Date:** 2025-06-25

## Context

Our application's command-line interface (CLI) is built using the `rich` library, as decided in ADR-002. We have successfully implemented a multi-bar progress display for concurrent tasks. However, recent research (`Optimizing Display Output Structure for Maximum Effectiveness`) has provided a blueprint for a much richer "dashboard-style" UI, including persistent statistics and advanced worker views.

Implementing all of these features at once risks creating a cluttered and overwhelming default view for the user. Furthermore, other research (`Why Can't We Have a Whisper Progress Bar?`) has confirmed that providing a smooth, granular progress bar for the subtitle generation phase is technically difficult and brittle. This creates a tension between our desire for a rich, informative UI and the need for a clean, stable, and uncluttered user experience.

## Decision

We will adopt the **Progressive Disclosure** pattern as the guiding principle for our CLI design.

1.  **Default View (Summary):** The application will start in a clean, high-level summary view. This view will show only the most critical information, such as the overall progress of the current phase (e.g., "Subtitle Generation") and a primary progress bar (e.g., "3 of 7 files complete").

2.  **Detailed View (Dashboard):** The user will be able to toggle a more detailed "dashboard" view on and off via a keyboard shortcut (e.g., pressing `d`). This detailed view will contain the richer information proposed in our research, such as:
    * A persistent header with real-time session statistics.
    * The multi-bar progress display showing individual worker status.
    * A queue of pending jobs.

3.  **Final Decision on Whisper Progress:** We will **not** invest further effort in creating a granular, real-time progress bar for the subtitle generation phase. The current per-segment update is the accepted implementation. The detailed view will be the appropriate place to display this "noisy" progress indicator, keeping the default view clean.

## Rationale

-   **Manages Complexity:** This approach prevents overwhelming the user by showing only essential information by default, aligning with UX best practices.
-   **Serves All Users:** The simple default view is intuitive for all users, while the on-demand detailed view provides the deep insight that power users require.
-   **Solves the UI Conflict:** It provides a home for detailed, complex, or "noisy" UI elements (like per-worker status and per-segment subtitle progress) without cluttering the primary interface.
-   **Avoids Brittle Implementations:** This decision formally accepts the findings of our research regarding Whisper progress bars, preventing wasted effort on a fragile solution.
-   **Grounded in Research:** This entire strategy is directly informed by the "Optimizing Display Output" and "Progressive Disclosure" research documents.

## Consequences

-   **Positive:**
    -   A clear architectural vision for a clean, powerful, and user-friendly interface.
    -   A concrete plan for implementing the features in our backlog (Tasks 6.0, 7.0, 8.0).
-   **Negative:**
    -   Increases the complexity of the UI rendering logic.
    -   Requires the implementation of a non-blocking keyboard listener to toggle views, which adds a new dependency (`keyboard` library) and a new layer of complexity.
