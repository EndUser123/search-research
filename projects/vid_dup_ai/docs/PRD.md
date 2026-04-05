## --- METADATA ---
# Filename: PRD.md
# Version: 1.1.0
# ------------------
#
# --- CHANGELOG ---
# v1.1.0: DOCS: Updated logging requirements (FR-006.4) and dependencies to reflect the new Loguru-based architecture.
# v1.0.0: INIT: Initial version of the Product Requirements Document.
# ------------------

# --- INTEGRITY ---
# Previous Character Count: 16839
# Current Character Count: 16843
# Syntax Check: PASS
# Logic Validation: Requirements now accurately describe the current logging implementation, including per-run log files and updated dependencies.
# Reason for Change: To synchronize the PRD with the latest architectural changes and prevent requirement drift.
# ------------------

# Product Requirements Document (PRD) for Video Dedupe AI

## 1. Introduction

### 1.1 Purpose
This Product Requirements Document (PRD) defines the functional and non-functional requirements for 'Video Dedupe AI', an advanced video management tool designed to clean, organize, and manage video collections. The tool identifies duplicate videos, retains the highest quality versions using sophisticated metrics, and optionally categorizes videos using AI. This document serves as a comprehensive guide for developers, testers, and stakeholders to understand the existing features and their specific requirements.

### 1.2 Scope
The scope of this PRD covers all existing features as implemented in the 'video_dedupe_ai.py' script as of June 29, 2025. It includes duplicate detection, quality-based retention, AI-powered categorization, performance optimizations, safety mechanisms, and configuration options. Future enhancements or roadmap items are excluded from this document and are detailed separately in 'ROADMAP.md'.

### 1.3 Audience
This document is intended for:
- Developers maintaining or extending 'Video Dedupe AI'.
- Testers validating the functionality and performance of the tool.
- Product managers and stakeholders understanding the feature set and requirements.

## 2. Product Overview

### 2.1 Product Name
Video Dedupe AI

### 2.2 Description
Video Dedupe AI is a command-line tool designed to manage large video collections by identifying and resolving duplicates, retaining the highest quality versions based on metrics like VMAF, SSIM, or PSNR, and optionally organizing videos into content-based categories using AI models. It prioritizes user safety with dry run and quarantine options, and performance with parallel processing.

### 2.3 Key Objectives
- **Duplicate Resolution:** Accurately identify duplicate or similar videos across multiple directories using fuzzy name matching, duration comparison, and perceptual hashing.
- **Quality Retention:** Retain the highest quality video version rather than the smallest file, using advanced quality metrics.
- **Video Organization:** Optionally categorize videos into folders based on content using AI models.
- **Performance:** Process large video libraries efficiently through parallel processing.
- **Safety:** Prevent accidental data loss with simulation modes and recoverable deletion options.
- **Configurability:** Allow extensive customization of operations through command-line arguments and configuration files.

## 3. Functional Requirements

### 3.1 Intelligent Duplicate Detection
- **ID:** FR-001
- **Description:** The tool must identify duplicate or similar videos across two specified directories (media_dir and videos_dir) using a multi-stage process.
- **Requirements:**
  - **Fuzzy Filename Matching (FR-001.1):** Compare video filenames using fuzzy string matching (e.g., `thefuzz` library) with a configurable similarity threshold (default: 85 out of 100) to identify potential matches.
  - **Duration Matching (FR-001.2):** Filter potential matches by comparing video durations with a configurable tolerance (default: 2.0 seconds) to account for minor encoding differences.
  - **Perceptual Hashing (FR-001.3):** Optionally enable content-based matching using perceptual hashing (e.g., `imagehash.phash`) with a configurable Hamming distance threshold (default: 7) to confirm duplicates even if filenames or durations vary slightly.
  - **User Control (FR-001.4):** Allow users to enable or disable perceptual hashing via a command-line flag (`--perceptual-hash`) or config file to balance accuracy and performance.
- **Acceptance Criteria:**
  - Given two directories with video files, the tool identifies files with similar names (above threshold), matching durations (within tolerance), and similar content (if hashing is enabled).
  - The tool logs the matching criteria used for each identified duplicate pair for transparency.

### 3.2 Quality-Based Retention
- **ID:** FR-002
- **Description:** The tool must determine and retain the highest quality version of duplicate videos using a composite quality score.
- **Requirements:**
  - **Metric Selection (FR-002.1):** Support multiple perceptual quality metrics including VMAF, SSIM, and PSNR (via `ffmpeg-quality-metrics` library), selectable via a command-line option (`--quality-metric`) or config file.
  - **Composite Score (FR-002.2):** When a quality metric is selected, calculate a weighted composite score based on the perceptual metric, resolution, and bitrate to determine the best version.
  - **Retention Decision (FR-002.3):** Retain the video with the highest composite score, moving it to the primary media directory if necessary, and marking others for deletion or quarantine.
  - **Logging (FR-002.4):** Log the quality scores and retention decision rationale for each set of duplicates.
- **Acceptance Criteria:**
  - Given a set of duplicate videos, the tool calculates quality scores using the selected metric and retains the highest scoring video in the media directory.
  - Logs clearly indicate the metric used and the score for each video in the decision process.

### 3.3 AI-Powered Categorization
- **ID:** FR-003
- **Description:** The tool must optionally categorize videos into content-based folders using a pre-trained AI model for video classification.
- **Requirements:**
  - **Enablement (FR-003.1):** Provide a command-line flag (`--categorize`) and config option to enable or disable AI categorization, defaulting to disabled due to resource intensity.
  - **Model Selection (FR-003.2):** Use a configurable pre-trained model from Hugging Face (default: 'MCG-NJU/videomae-base-finetuned-kinetics-400') for video classification, loadable on-demand to save resources if not enabled.
  - **Frame Extraction (FR-003.3):** Extract a configurable number of frames (default: 16) from each video at evenly spaced intervals for input to the AI model.
  - **Organization (FR-003.4):** Move categorized videos to subfolders within a user-specified root directory (`--organization-dir`), named after the predicted category (e.g., 'sports', 'music').
  - **Dependency Check (FR-003.5):** Verify availability of required libraries (`torch`, `transformers`) at startup if categorization is enabled, failing early with a clear error if unavailable.
- **Acceptance Criteria:**
  - When enabled, the tool extracts frames from videos, processes them through the AI model, and moves files to category-named subfolders within the specified organization directory.
  - If libraries are missing or model loading fails, the tool logs an error at startup and disables categorization without crashing.
  - Logs indicate the predicted category and destination path for each categorized video.

### 3.4 High-Performance Processing
- **ID:** FR-004
- **Description:** The tool must process large video libraries efficiently using parallel processing to leverage multi-core systems.
- **Requirements:**
  - **Parallel Execution (FR-004.1):** Use `ProcessPoolExecutor` for high-level, subprocess-heavy tasks (e.g., processing individual media files) to avoid deadlocks and leverage multiple CPU cores. Use `ThreadPoolExecutor` only for lightweight, I/O-bound tasks like initial file indexing. (This is now correctly implemented as of v2.5.0).
  - **Thread Safety (FR-004.2):** Ensure thread-safe and process-safe logging and data access when processing files in parallel to prevent race conditions or data corruption.
  - **Progress Feedback (FR-004.3):** Display progress bars using the `rich` library for long-running operations.
    - **Layout Standardization (FR-004.3.1):** The progress bar layout must be standardized across all tasks, using fixed-width columns to ensure vertical alignment of all elements (description, bar, counters, time remaining).
    - **Completion Counter (FR-004.3.2):** Progress bars must include a counter displaying the number of completed tasks versus the total (e.g., '12/24').
    - **Resize Handling (FR-004.3.3):** The progress display must be wrapped in a `rich.Live` context to handle terminal window resizing gracefully and prevent display corruption.
  - **Resource Management (FR-004.4):** Allow users to configure the maximum number of parallel workers (`--max-workers`) to limit resource usage if needed.
- **Acceptance Criteria:**
  - The tool processes multiple video files concurrently, utilizing available CPU cores up to the configured worker limit, without deadlocking.
  - Progress bars update in real-time and remain vertically aligned regardless of task description length.
  - The terminal display does not become corrupted when the window is resized.
  - No data corruption or logging overlaps occur during parallel execution.

### 3.5 Safety Features
- **ID:** FR-005
- **Description:** The tool must prioritize user safety by preventing accidental data loss through simulation and recoverable deletion options.
- **Requirements:**
  - **Dry Run Mode (FR-005.1):** Provide a `--dry-run` flag to simulate all operations (moves, deletes, categorizations) without modifying files, logging what would be done.
  - **Quarantine System (FR-005.2):** Offer a `--quarantine-dir` option to move deleted files to a specified directory instead of permanent deletion, preserving relative path structure for recovery.
  - **Confirmation Prompt (FR-005.3):** Require user confirmation before executing the plan unless bypassed with `--yes` or `-y` flag, showing a summary of planned actions.
- **Acceptance Criteria:**
  - In dry run mode, the tool logs all planned actions without altering any files, allowing users to review the plan.
  - When quarantine is enabled, deleted files are moved to the specified directory with their original structure intact, verifiable by manual inspection.
  - Without the `--yes` flag, the tool pauses after displaying the plan summary, awaiting user input to proceed or cancel.

### 3.6 Highly Configurable Operation
- **ID:** FR-006
- **Description:** The tool must allow extensive customization of its behavior through command-line arguments and a configuration file.
- **Requirements:**
  - **Command-Line Arguments (FR-006.1):** Support arguments for all major settings, including directories (`media_dir`, `videos_dir`), safety options (`--dry-run`, `--quarantine-dir`), matching criteria (`--duration-tolerance`, `--fuzzy-match-threshold`, `--hash-threshold`), quality metrics (`--quality-metric`), AI categorization (`--categorize`, `--organization-dir`), and performance (`--max-workers`).
  - **Configuration File (FR-006.2):** Allow loading settings from an INI-format file (default: 'config.ini') via `--config` argument, with command-line arguments overriding file settings.
  - **Generate Config (FR-006.3):** Provide a `--generate-config` option to create a default configuration file with all settings and sensible defaults, exiting after generation.
  - **Verbose Logging (FR-006.4):** Enable detailed debug logging with `--verbose` flag and optional log file output via `--log` argument for troubleshooting.
    - **Structured Logging (FR-006.4.1):** When a log file is specified, output must be in a structured, machine-readable format (JSON Lines), enabled via `serialize=True` in the `Loguru` configuration.
    - **Per-Run Log Files (FR-006.4.2):** The system must create a new, uniquely timestamped log file for each execution to prevent logs from different runs from being mixed. This is achieved by using a `{time}` placeholder in the log filename. Old logs are managed by a time-based retention policy (e.g., "10 days").
    - **Process-Safe Logging (FR-006.4.3):** The logging system must be safe for use with `ProcessPoolExecutor`, achieved by using `enqueue=True` in the `Loguru` configuration.
- **Acceptance Criteria:**
  - All configurable settings can be set via command-line arguments, verifiable by checking tool behavior with different inputs.
  - Settings loaded from a config file match command-line defaults unless overridden, confirmed by logging loaded configuration.
  - Running `--generate-config` creates a 'config.ini' file with documented defaults, exiting without further processing.
  - A new, timestamped JSON log file is created for each run when `--log` is specified.
  - Debug logs are output to console and file (if specified) when `--verbose` is enabled, containing detailed operation traces.

## 4. Non-Functional Requirements

### 4.1 Performance
- **ID:** NF-001
- **Description:** The tool must handle large video libraries efficiently, minimizing processing time while maintaining accuracy.
- **Requirements:**
  - Process at least 100 video files per minute for metadata extraction on a standard multi-core system (e.g., 4 cores, 8GB RAM), assuming no quality or AI tasks.
  - Scale processing speed near-linearly with available CPU cores for parallel tasks.
  - Provide progress feedback updates at least every second during long operations to keep users informed.
- **Acceptance Criteria:** Performance benchmarks on a test system meet or exceed the specified file processing rate, and progress bars update frequently during operation.

### 4.2 Reliability
- **ID:** NF-002
- **Description:** The tool must operate reliably without crashing on diverse video files and system configurations.
- **Requirements:**
  - Handle corrupted or unreadable video files by logging an error and skipping to the next file without terminating.
  - Retry transient errors (e.g., file access issues) up to 3 times before logging a failure and proceeding.
  - Ensure no data loss occurs outside user-confirmed delete or move operations, preserving original files in case of crashes.
  - **API Modernization (NF-002.4):** The script must use current, non-deprecated APIs for its core dependencies (e.g., `scenedetect`). Deprecated functions must be replaced with their modern equivalents to ensure future compatibility and reliability.
- **Acceptance Criteria:** The tool continues processing after encountering corrupted files or transient errors, logs all failures, and does not modify files unexpectedly during interruptions.

### 4.3 Usability
- **ID:** NF-003
- **Description:** The tool must be usable by users with varying technical expertise through clear documentation and intuitive options.
- **Requirements:**
  - Provide detailed help text for all command-line arguments via `--help` flag, explaining purpose and defaults.
  - Include comprehensive usage examples and installation instructions in 'README.md' covering common workflows.
  - Ensure error messages are descriptive, suggesting corrective actions for common issues (e.g., missing dependencies, invalid paths).
- **Acceptance Criteria:** Users can access detailed argument descriptions, follow installation and usage guides to run basic operations, and understand error messages with actionable next steps.

### 4.4 Security
- **ID:** NF-004
- **Description:** The tool must prevent unauthorized access or unintended modifications to the user's file system.
- **Requirements:**
  - Validate all file paths to prevent path traversal attacks, ensuring operations are confined to specified directories.
  - Log warnings for suspicious inputs (e.g., paths with `..`) and reject operations outside base directories unless confirmed.
  - Do not execute or evaluate user-provided code or scripts, limiting input to configuration and file paths.
- **Acceptance Criteria:** The tool rejects malicious path inputs with clear error messages, logs suspicious activity, and confines all file operations to user-specified directories.

### 4.5 Compatibility
- **ID:** NF-005
- **Description:** The tool must be compatible with multiple operating systems and video formats.
- **Requirements:**
  - Support operation on Windows, macOS, and Linux, handling platform-specific path conventions and file system behaviors.
  - Process common video formats (e.g., MP4, MOV, MKV, AVI, WEBM) as specified by user-configurable extensions.
  - Handle dependencies (e.g., FFmpeg) with installation instructions for each supported platform in documentation.
- **Acceptance Criteria:** The tool runs successfully on all major OS platforms with appropriate FFmpeg installation, processes videos in specified formats, and provides platform-specific setup guidance.

## 5. System Requirements
- **Operating Systems:** Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+ or equivalent).
- **Hardware:** Minimum 4 CPU cores, 8GB RAM for basic operations; 16GB+ RAM and 8+ cores recommended for AI categorization and quality metrics on large libraries.
- **Software Dependencies:**
  - Python 3.8+.
  - FFmpeg and ffprobe installed and accessible in system PATH.
  - Required Python libraries: `ffmpeg-python`, `imagehash`, `thefuzz[speedup]`, `Pillow`, `scenedetect`, `rich`, `loguru`.
  - Optional for AI categorization: `torch`, `transformers`.
  - Optional for quality metrics: `ffmpeg-quality-metrics`.
- **Disk Space:** Sufficient space for video files, quarantine directory (if enabled), and temporary processing data.

## 6. Constraints and Assumptions
- **Constraints:**
  - The tool operates as a command-line application, requiring basic terminal familiarity unless a GUI is developed in the future.
  - AI categorization and quality metrics are resource-intensive, potentially limiting performance on low-end hardware.
  - FFmpeg must be installed separately by users, as it is not bundled with the tool.
- **Assumptions:**
  - Users have administrative access to install dependencies and configure system PATH for FFmpeg.
  - Video files are not locked by other processes during operation.
  - Users understand the risk of file operations and use dry run or quarantine options to mitigate accidental data loss.

## 7. Success Metrics
- **User Satisfaction:** Achieve a user-reported satisfaction rate of over 80% for duplicate detection accuracy and safety features based on feedback or surveys if open-sourced.
- **Performance:** Process at least 100 files per minute for basic metadata operations on standard hardware, with parallel tasks scaling effectively with CPU cores.
- **Reliability:** Maintain a crash rate below 1% during operations on diverse video libraries, as reported by error logs or user feedback.
- **Adoption:** If open-sourced, aim for 500+ downloads or active users within the first year post-release, indicating market fit and usability.

## 8. Traceability
- **Feature to Code Mapping:** Each functional requirement (FR-XXX) maps to specific classes or functions in 'vda_cli.py':
  - FR-001 (Duplicate Detection): `OperationPlanner._find_potential_matches`, `OperationPlanner._refine_matches_with_hashes`, `VideoProcessor.extract_and_hash_keyframes`.
  - FR-002 (Quality Retention): `VideoProcessor.get_quality_metric_score`, `OperationPlanner._calculate_composite_quality_scores`, `OperationPlanner._select_best_video`.
  - FR-003 (AI Categorization): `VideoProcessor.categorize_video_batch`, `OperationExecutor._perform_categorize`.
  - FR-004 (Performance): `OperationPlanner.plan_operations`, use of `ProcessPoolExecutor` and `ThreadPoolExecutor`.
  - FR-005 (Safety): `main()` logic for dry run and quarantine, `OperationExecutor.execute`.
  - FR-006 (Configurability): `ConfigManager` class, `Loguru` configuration in `main()`.

## 9. Conclusion
This PRD comprehensively documents the requirements for 'Video Dedupe AI', ensuring that all existing features are clearly defined for development, testing, and stakeholder understanding. It serves as a foundation for maintaining the tool's quality and guiding future enhancements as outlined in the separate roadmap. Feedback from users and developers is encouraged to refine these requirements over time.
