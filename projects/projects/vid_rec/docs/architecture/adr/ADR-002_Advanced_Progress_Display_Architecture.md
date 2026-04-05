# ADR-002: Advanced Progress Display Architecture

- **Status:** Accepted
- **Date:** 2025-06-21

## Context

The existing CLI progress display, based on the `tqdm` library, is effective for simple, sequential tasks. However, it provides poor visibility into concurrent operations running in a `ProcessPoolExecutor`. The user cannot see which specific files are being actively processed, nor can they see the individual progress of those tasks. This creates an opaque and dated user experience, especially during large batch jobs.

## Decision

We will replace the `tqdm` implementation with a more powerful solution built on the `rich` library. The new architecture will be as follows:

1.  **UI Rendering:** All progress displays will be managed by the `rich.progress.Progress` class in the main process.
2.  **Inter-Process Communication (IPC):** For parallel tasks, we will use a `multiprocessing.Manager` to create a shared dictionary. Worker processes will report their progress by updating their state in this shared dictionary. The main process will poll this dictionary to update the UI.
3.  **Logging:** All console logging will be handled by `rich.logging.RichHandler` to ensure seamless, non-corrupting output alongside the dynamic progress display.

## Rationale

This decision is based on the findings of a detailed research report. The key advantages of this architecture are:

* **Superior Observability:** The `rich` library's explicit task management API allows for the creation of a hierarchical "master-child" display, showing both overall batch progress and the real-time status of individual worker processes.
* **Architectural Robustness:** The `Manager`-based IPC pattern is a well-understood solution for state synchronization in multiprocessing contexts. It is conceptually simpler for a dashboard-style UI than a message queue, and its stateful nature makes the UI rendering loop inherently robust.
* **Enhanced User Experience:** `rich` provides a modern, visually appealing, and highly customizable interface, significantly improving the application's professional look and feel.
* **Integrated Logging:** `RichHandler` solves the complex problem of printing log messages during a live progress display without corrupting the output.

## Consequences

* **Positive:**
    * A vastly improved, modern CLI user experience.
    * Greatly increased observability into the application's real-time state.
    * A cleaner, more robust logging system for console output.
* **Negative:**
    * Introduction of a major new project dependency (`rich`).
    * A significant increase in the complexity of the main processing loop in `main_processor.py` to manage the UI rendering and IPC polling.
    * The `Manager` introduces a slight performance overhead compared to other IPC mechanisms, but this is an acceptable trade-off for the simplicity and robustness it provides for this use case.
