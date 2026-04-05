# Product Requirements Document: Vid_ReC

## Product Metadata
- **Version:** 1.0
- **Status:** In Review
- **Date:** 2025-06-21

## 1. Introduction and Vision

Vid_ReC (Video Re-encoder & Consolidator) is a robust, intelligent, and efficient command-line tool for power users and media archivists. Its core purpose is to automate the batch processing of large video libraries, ensuring consistent quality, format, and metadata with minimal user intervention.

The project's vision is to evolve from a manually-run script into a fully autonomous, "fire-and-forget" service that intelligently manages and enhances a user's video collection.

## 2. User Persona

The primary user is the **"Media Archivist"** or **"Power User"**. This individual typically has:
- A large, local library of video files in various formats.
- A powerful computer, often with a dedicated NVIDIA GPU.
- A desire to automate repetitive tasks like re-encoding, standardizing formats, normalizing audio, and generating subtitles.
- Comfort with command-line interfaces and editing configuration files.
- A high value placed on data integrity and avoiding quality loss.

## 3. Core Product Goals and Principles

- **Efficiency:** Drastically reduce the time and effort required to manage a large video library through parallel processing and automation.
- **Intelligence:** Make smart decisions on behalf of the user, such as when to keep a re-encoded file based on quality metrics.
- **Robustness:** Handle errors gracefully, maintain state across interruptions, and prevent accidental data loss.
- **Observability:** Provide clear, real-time feedback on the application's status and actions via a modern CLI.
- **Configurability:** Allow the user to fine-tune the application's behavior to suit their specific hardware and preferences.

## 4. Feature Requirements

This section details the functional requirements of the application.
- `[x]` Indicates a feature that is implemented.
- `[ ]` Indicates a feature that is planned.

### 4.1. Core Processing Pipeline

- `[x]` The application must scan a user-defined source directory recursively to find all video files.
- `[x]` It must process files in a two-phase pipeline: a sequential subtitle phase followed by a parallel CPU-bound phase.
- `[x]` It must provide a detailed summary of completed, skipped, and failed jobs at the end of a run.
- `[ ]` **(Planned)** The pipeline shall evolve into a producer-consumer model to allow simultaneous GPU and CPU processing (Task 4.3).

### 4.2. State Management & Resumption

- `[x]` The application must maintain a persistent state database (`vidrec_state.db`) to track the status of each file.
- `[x]` It must calculate and store a SHA256 hash of each source file to detect modifications between runs.
- `[x]` It must not re-process files that are already marked as `COMPLETED` and whose hash has not changed.
- `[x]` It must support multi-stage resumption, allowing it to skip the subtitle phase for files that have already completed it (`SUBTITLES_COMPLETE` state).
- `[x]` It must gracefully handle user interruptions (e.g., `Ctrl+C`) and be able to resume the batch job on the next run.

### 4.3. Video & Audio Processing

- `[x]` The application must be able to re-encode video files to H.265 (HEVC).
- `[x]` It must automatically detect the presence of an NVIDIA GPU and use the hardware-accelerated `hevc_nvenc` encoder if available, falling back to `libx265` on the CPU.
- `[x] `The user must be able to specify a target vertical resolution (e.g., 1080p), and the application shall downscale videos exceeding this resolution.
- `[x]` The application must intelligently calculate a target CRF value if one is not provided by the user.
- `[x]` The application must handle HDR-to-SDR tone mapping for HDR source videos.
- `[x]` The user must be able to enable or disable audio normalization. When enabled, audio shall be normalized to the ITU-R BS.1770-4 standard.
- `[x]` The application shall only replace an original file if the re-encoded version provides a superior quality-per-byte ratio, as determined by a VMAF score and file size comparison (Task 3.1).

### 4.4. Subtitle Generation

- `[x]` The application must be able to generate English subtitles for videos that do not have them.
- `[x]` It must use the `faster-whisper` library to perform transcription.
- `[x]` This functionality must be isolated in a dedicated adapter module (`subtitle_generator.py`) as per ADR-001.

### 4.5. User Interface & Experience (CLI)

- `[x]` The primary interface must be the command line.
- `[x]` The application must provide clear, real-time progress indicators for all phases.
- `[x]` A hierarchical progress display must be used for parallel tasks, showing an overall progress bar and individual bars for each active worker.
- `[x]` Logging output must be beautifully formatted and must not interfere with the progress display, through the use of `rich.logging.RichHandler`.
- `[x]` Log messages must be concise and easily scannable.
- `[x]` The user must be able to override key configuration settings via command-line arguments (e.g., `--source`, `--no-replace`, `--max-workers`).

### 4.6. Configuration

- `[x]` All core settings must be configurable via a `config.toml` file.
- `[x]` The user must be able to configure source and temporary paths.
- `[x]` The user must be able to configure settings such as `no_replace`, `create_subtitles`, and `normalize_audio`.
- `[x]` The user must be able to configure encoding parameters like `target_height` and `crf`.
- `[x]` The user must be able to configure performance parameters like `max_workers`.

## 5. Out of Scope

- **Graphical User Interface (GUI):** The application is exclusively a CLI tool.
- **Non-English Subtitles:** The current requirement is only for English subtitle generation.
- **Cloud Storage Integration:** The application operates on a local filesystem only.
