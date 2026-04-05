# Vid_ReC Architectural Overview

## 1. Introduction

This document provides a high-level overview of the Vid_ReC application's architecture. Its purpose is to help developers understand the roles of the major components and how they interact.

## 2. Core Components

The application is composed of several key Python modules within the `src/` directory.

-   **`main_processor.py`**: The main entry point and orchestrator of the application. It is responsible for parsing command-line arguments, loading configuration, scanning for files, and managing the overall processing pipeline.
-   **`config.py`**: Defines and validates the application's configuration using Pydantic models. It loads settings from `config.toml`.
-   **`state_manager.py`**: Manages the persistent state of all processing jobs using an SQLite database (`vidrec_state.db`). It handles hashing files to detect changes and tracks the status of each job.
-   **`processing_job.py`**: Contains the `ProcessingJob` class, which encapsulates the logic for processing a single video file. It also contains the top-level worker function `run_cpu_job_in_worker` that is executed by the parallel process pool.
-   **`subtitle_generator.py`**: An adapter module that contains all logic for interacting with the `faster-whisper` library for subtitle generation.
-   **`video_encoder.py`**: Contains the core `ffmpeg` logic for re-encoding video files, handling hardware acceleration detection (NVENC), and HDR-to-SDR tone mapping.
-   **`utils.py`**: A collection of helper functions and classes, most notably the `setup_logging` function which configures the `rich`-based logging system.

**Related ADRs:**
- [ADR-002: Advanced Progress Display Architecture](../architecture/adr/ADR-002_Advanced_Progress_Display_Architecture.md)
- [ADR-007: Structured Logging with structlog](../architecture/adr/ADR-007_Structured_Logging_with_structlog.md)

## 3. High-Level Data Flow

The application follows a two-phase pipeline, orchestrated by `main_processor.py`.

```mermaid
graph TD
    subgraph Initialization
        A[Start main_processor.py] --> B{Load Config};
        B --> C{Setup Logging};
        C --> D{Parse CLI Arguments};
    end

    subgraph Phase 1 - Scan
        D --> E[Scan Source Directory for Videos];
        E --> F{For each video...};
        F --> G[Check State in SQLite];
        G --> H[Hash File];
        H --> I[Build Job Queues];
    end

    subgraph Phase 2 - Subtitle Generation
        I -- Jobs to subtitle --> J[Subtitle Loop (Sequential, 1 Worker on GPU)];
        J --> K[faster-whisper generates .srt file];
        K --> L[Update job state to SUBTITLES_COMPLETE];
    end

**Related ADRs:**
- [ADR-001: Subtitle Dependency Strategy](../architecture/adr/ADR-001_Subtitle_Dependency_Strategy.md)
- [ADR-003: Fast Change Detection using Shallow Hashing](../architecture/adr/ADR-003_Fast_Change_Detection_using_Shallow_Hashing.md)
- [ADR-005: Replacing stable-ts with faster-whisper](../architecture/adr/ADR-005_Replacing_stable-ts_with_faster-whisper.md)
- [ADR-008: SQLAlchemy SQLite for Domain Models](../architecture/adr/ADR-008_SQLAlchemy_SQLite_for_Domain_Models.md)

    subgraph Phase 3 - CPU Processing
        L -- All jobs ready --> M[CPU Processing Loop (Parallel)];
        M --> N{ProcessPoolExecutor};
        N --> O[run_cpu_job_in_worker];
        O --> P[ProcessingJob.run_cpu_tasks];
        P --> Q[video_encoder.reencode_video];
        Q --> R[Calculate VMAF & Compare File Sizes];
    end

    subgraph Phase 4 - Quality Decision
        R --> S{Decision};
        S -->|VMAF >= threshold AND smaller| T[Replace Original];
        S -->|Otherwise| U[Keep Original];
        T --> V[Update job state to COMPLETED];
        U --> V;
    end

    subgraph Reporting
        V --> W[Display Final Summary];
    end
