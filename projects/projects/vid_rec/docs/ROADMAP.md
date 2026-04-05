# Vid_ReC Project Roadmap

## Vision
To create a robust, intelligent, and efficient command-line tool for batch processing, re-encoding, and enhancing video files with minimal user intervention.

---
### Phase 1: Foundational Refactoring (Complete)
**Goal:** Establish a modern, maintainable Python project structure.
**Key Features:** `pyproject.toml`, Pydantic for configuration, `ProcessingJob` class.

---
### Phase 2: Core Features & UX (Complete)
**Goal:** Implement the essential processing capabilities and a user-friendly experience.
**Key Features:** Audio normalization, efficient subtitle generation with a unified progress bar, robust multi-stage state management, final summary reporting.

---
### Phase 3: Intelligent Processing & Optimization (Complete)
**Goal:** Add a layer of intelligence to the application's decision-making and optimize performance.
**Key Features:**
* **Task 3.1: Implement Quality-Based Decision Making (VMAF):** Ensures we only replace files if the new version offers a superior quality-per-byte ratio.
* Hardware-aware parallel processing for CPU-bound tasks.
* User-configurable performance settings and improved logging.

---
### Phase 4: Architectural Improvement (Planned)
**Goal:** Refactor core components for long-term maintainability and scalability.
**Key Tasks:**
* **Task 4.1: Refactor `ProcessingJob` into a step-based orchestrator:** Decompose the monolithic `ProcessingJob` class into a "Core" orchestrator and smaller, swappable "Step" modules (e.g., SubtitleStep, EncodeStep, VMAFStep) to improve separation of concerns.
* **Task 4.2: Implement Richer Task Schema:** Evolve `vidrec_state.json` to a more detailed schema to better track priority, effort, and dependencies.
* **Task 4.3: Evolve to a Producer-Consumer Pipeline:** Refactor the current two-phase sequential pipeline into a fully parallel producer-consumer model. In this design, a single subtitle worker (the "producer") would place completed jobs into a queue, where a pool of CPU-based encoding workers (the "consumers") would pick them up immediately. This would allow for simultaneous use of GPU and CPU resources, maximizing hardware utilization for large batches.

---
### Phase 5: Autonomous Operation (Vision)
**Goal:** Evolve the tool from a manually-run script into an autonomous, scheduled service.
**Implications:**
* **Robustness:** Must handle all errors gracefully without crashing.
* **Logging:** Headless operation demands comprehensive, structured logging for diagnostics.
* **Resource Management:** Must operate as a "good citizen" on the user's machine.

---
### Phase 6: Code Quality & Operational Excellence (Planned)
**Goal:** Enhance code quality, maintainability, and operational robustness.
**Key Areas:**
* **Comprehensive Error Handling and Resilience:** Implement explicit strategies for critical error communication (e.g., UI display, concise exit messages). Enhance external dependency resilience with advanced retry mechanisms (e.g., exponential backoff, circuit breakers).
* **Test Coverage and Strategy:** Aim for high test coverage across unit, integration, and end-to-end tests. Develop automated tests specifically for graceful shutdown scenarios (both user-initiated and signal-based).
* **Dynamic Progress Reporting (FFmpeg):** Implement dynamic parsing of FFmpeg output to accurately determine total duration/frames for precise progress bar updates.
* **Dependency Management:** Clearly document optional dependencies and ensure graceful degradation or clear user guidance when they are missing.
* **Database Abstraction:** Consider adopting an ORM (e.g., SQLAlchemy) for improved database abstraction, type safety, and simplified schema migrations, aligning with ADR-008.
