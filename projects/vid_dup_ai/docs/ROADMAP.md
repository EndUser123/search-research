# Roadmap for Video Dedupe AI

This roadmap outlines the future development goals and recommendations for enhancing 'Video Dedupe AI', an advanced tool for managing video collections by identifying duplicates, retaining the highest quality versions, and organizing files with AI-powered categorization. The recommendations are derived from a detailed code review conducted on June 28, 2025, and are prioritized to address critical, major, and minor issues, as well as to seize opportunities for growth and improvement.

## Status Legend
- **DONE:** ✅ Completed features
- **INPROGRESS:** 🔄 Currently being developed
- **PLANNED:** 📋 Planned for future development
- **ONHOLD:** ⏸️ On hold pending other dependencies

## Priority Levels
- **Critical:** Essential improvements that address significant risks or gaps, crucial for reliability and user trust.
- **Major:** Important enhancements that improve performance, usability, or maintainability, impactful for a large user base.
- **Minor:** Smaller, quality-of-life improvements or refinements that enhance the overall experience but are less urgent.

## Development Goals

### 1. Testing and Reliability
- **📋 Implement a Comprehensive Test Suite (Critical)**
  - **Status:** PLANNED
  - **Objective:** Develop unit and integration tests using `pytest` to cover core functionalities like duplicate detection, quality assessment, and file operation planning, reducing the risk of regressions.
  - **Rationale:** The absence of tests increases the likelihood of undetected bugs as the codebase evolves.
  - **Tasks:**
    - Create unit tests for individual components (e.g., `VideoProcessor` methods).
    - Develop integration tests for end-to-end workflows (e.g., planning and executing operations).
    - Set up a continuous integration (CI) pipeline if the project is open-sourced to run tests on every commit.
- **📋 Migrate to a Modern Logging Library (Loguru) (Major)**
  - **Status:** PLANNED
  - **Objective:** Replace the standard `logging` + `python-json-logger` implementation with `Loguru` to improve performance, simplify configuration, and enhance debuggability.
  - **Rationale:** The current system requires significant boilerplate for configuration (e.g., manual setup of rotation). As recommended by the 'Comprehensive Analysis of Python Logging Libraries' document, Loguru offers built-in log rotation, simpler structured JSON output, and better out-of-the-box formatting, which will reduce maintenance overhead and improve developer experience.
  - **Tasks:**
    - Replace `logging` and `python-json-logger` with `loguru`.
    - Configure Loguru in `setup_logger()` for JSON file output and rich console logging.
    - Ensure new implementation respects all logging-related PRD requirements.
    - Remove unused logging dependencies.
- **📋 Introduce Dependency Injection for Testability (Major)**
  - **Status:** PLANNED
  - **Objective:** Add mocking points or dependency injection for external interactions (e.g., FFmpeg calls, file system operations) to enable isolated unit testing.
  - **Rationale:** Current dependencies on external systems make testing challenging without actual file or tool interactions.
  - **Tasks:**
    - Refactor code to allow injection of mock objects for FFmpeg and file system operations.
    - Document mocking strategies in a testing guide for contributors.

### 2. Performance Optimization
- **📋 Implement Configurable Resource Limits for Parallel Processing (Critical)**
  - **Status:** PLANNED
  - **Objective:** Add limits on parallel workers and memory usage to prevent system overload during CPU-intensive tasks like hashing and quality analysis.
  - **Rationale:** Unbounded parallel processing can overwhelm system resources, especially with large video libraries.
  - **Tasks:**
    - Introduce configuration options for `max_workers` with defaults based on detected CPU cores.
    - Implement a resource monitor to throttle operations if CPU or memory usage exceeds safe thresholds.
- **📋 Optimize AI Categorization with Batch Processing (Major)**
  - **Status:** PLANNED
  - **Objective:** Allow batch processing or selective AI categorization (e.g., only for non-duplicate videos) to reduce resource demands.
  - **Rationale:** AI model inference is highly resource-intensive, impacting usability on lower-end hardware.
  - **Tasks:**
    - Add options to limit categorization to specific files or batches.
    - Provide settings for model inference parameters (e.g., precision vs. speed trade-offs).
- **📋 Add Timeouts for External Operations (Major)**
  - **Status:** PLANNED
  - **Objective:** Implement timeouts for FFmpeg operations and parallel tasks to handle hanging processes gracefully.
  - **Rationale:** Hanging processes can stall operations indefinitely, especially with corrupted video files.
  - **Tasks:**
    - Set configurable timeouts for FFmpeg calls and parallel worker tasks.
    - Log timeout events and skip problematic files to continue processing.

### 3. Error Handling and Robustness
- **📋 Enhance Error Recovery with Retries and Global Mechanisms (Major)**
  - **Status:** PLANNED
  - **Objective:** Add a global timeout or recovery mechanism for parallel workers to prevent deadlocks or resource exhaustion.
  - **Rationale:** Current retry logic handles individual task failures but lacks a system-wide safety net.
  - **Tasks:**
    - Implement a global operation timeout to abort if processing exceeds a user-defined duration.
    - Add recovery logic to restart stalled workers or skip problematic files after retries.
- **📋 Early Validation of Optional Dependencies (Minor)**
  - **Status:** PLANNED
  - **Objective:** Check for optional dependencies (e.g., `torch`, `transformers`) and AI model loading success at startup if related features are enabled.
  - **Rationale:** Late failures during categorization disrupt workflows; early checks provide immediate feedback.
  - **Tasks:**
    - Validate library availability and model loading during initialization if categorization or quality metrics are enabled.
    - Provide clear error messages and disable features gracefully if dependencies are missing.

### 4. Security Enhancements
- **📋 Prevent Path Traversal Attacks (Major)**
  - **Status:** PLANNED
  - **Objective:** Implement strict path normalization and validation to ensure resolved paths remain within specified base directories.
  - **Rationale:** Lack of path validation could allow malicious input to access unauthorized areas via traversal attacks.
  - **Tasks:**
    - Normalize all input paths to prevent `../` traversal.
    - Log warnings for suspicious path inputs and reject operations outside base directories.
- **📋 Warn on Operations Outside Specified Directories (Minor)**
  - **Status:** PLANNED
  - **Objective:** Add warnings or confirmations for operations on paths outside `media_dir` and `videos_dir`.
  - **Rationale:** Prevents accidental data loss in unintended locations due to misconfigured paths.
  - **Tasks:**
    - Check if resolved paths are within base directories before operations.
    - Prompt for confirmation if paths are outside expected directories.

### 5. Usability and Documentation
- **📋 Simplify Configuration for New Users (Major)**
  - **Status:** PLANNED
  - **Objective:** Provide a simplified configuration mode or wizard-like setup to ease onboarding for non-technical users.
  - **Rationale:** Extensive configuration options can overwhelm users without technical expertise.
  - **Tasks:**
    - Create a basic configuration profile with essential settings and defaults for advanced options.
    - Develop an interactive setup script or GUI wizard for first-time configuration.
- **📋 Enhance Inline Documentation for Complex Logic (Minor)**
  - **Status:** PLANNED
  - **Objective:** Add more inline comments for intricate logic, especially in quality assessment and AI categorization methods.
  - **Rationale:** Improves readability and aids future maintainers in understanding dense code sections.
  - **Tasks:**
    - Review and add comments to methods like `_determine_best_video_and_plan` and `categorize_video`.
    - Document rationale for key constants and thresholds (e.g., `hash_threshold`, `scene_threshold`).
- **📋 Group Configuration Options Logically (Minor)**
  - **Status:** PLANNED
  - **Objective:** Organize related configuration options in `ConfigManager` and config file structure with explanatory comments.
  - **Rationale:** Reduces confusion by clarifying the impact and interaction of settings.
  - **Tasks:**
    - Restructure config file into sections (e.g., Matching, Quality, AI, Performance).
    - Add comments in code and config file explaining option purposes and dependencies.

### 6. Feature Enhancements and Correctness
- **📋 Enhance Quality Assessment Criteria (Major)**
  - **Status:** PLANNED
  - **Objective:** Allow users to specify a reference video or use nuanced criteria beyond resolution for quality assessment (e.g., bitrate, encoding efficiency).
  - **Rationale:** Current reliance on highest resolution as reference may not always select the best quality video.
  - **Tasks:**
    - Add configuration option for reference video selection or alternative quality heuristics.
    - Document how different metrics (VMAF, SSIM, PSNR) impact retention decisions.
- **📋 Configurable Fuzzy Matching Threshold (Minor)**
  - **Status:** PLANNED
  - **Objective:** Make the fuzzy matching threshold configurable with guidance on adjustment based on naming patterns.
  - **Rationale:** Hardcoded threshold may miss matches or cause false positives depending on file naming conventions.
  - **Tasks:**
    - Add `fuzzy_match_threshold` to configuration options with a default of 80.
    - Provide examples in documentation for adjusting threshold based on naming similarity.
- **📋 Refactor Complex Methods for Clarity (Minor)**
  - **Status:** PLANNED
  - **Objective:** Break down complex methods like `OperationPlanner._determine_best_video_and_plan` into smaller, single-responsibility functions.
  - **Rationale:** Improves readability, debugging, and testability of dense logic.
  - **Tasks:**
    - Split quality sorting and plan generation into separate functions.
    - Ensure each function has a clear, documented purpose.

### 7. Future Opportunities
- **📋 Cloud Storage Integration (Major)**
  - **Status:** PLANNED
  - **Objective:** Add support for comparing and managing video files across local and cloud storage environments.
  - **Rationale:** Expands applicability for users with distributed video libraries.
  - **Tasks:**
    - Research and integrate APIs for popular cloud storage services (e.g., Google Drive, Dropbox).
    - Design synchronization logic for duplicate detection across local and remote locations.
- **📋 GUI or Web Interface Development (Major)**
  - **Status:** PLANNED
  - **Objective:** Develop a graphical or web-based interface to make the tool accessible to non-technical users.
  - **Rationale:** Reduces the learning curve associated with command-line usage, broadening the user base.
  - **Tasks:**
    - Prototype a simple GUI using frameworks like Tkinter or PyQt for basic operations.
    - Explore web interface options with Flask or Django for remote access and management.
- **📋 Batch Processing Limits and GPU Acceleration (Major)**
  - **Status:** PLANNED
  - **Objective:** Implement batch processing limits and explore GPU acceleration for quality metrics and AI tasks.
  - **Rationale:** Addresses performance bottlenecks for large libraries and leverages modern hardware.
  - **Tasks:**
    - Add batch size configuration for processing subsets of files.
    - Research and integrate GPU support for AI inference and quality calculations if libraries allow.
- **📋 Educational Content and Community Engagement (Minor)**
  - **Status:** PLANNED
  - **Objective:** Create tutorials, videos, and contribution guides to improve user adoption and foster a community if open-sourced.
  - **Rationale:** Enhances visibility and accelerates development through community contributions.
  - **Tasks:**
    - Develop video walkthroughs for setup and key features.
    - Draft a contribution guide with coding standards and issue templates for potential open-source release.

## Theme 1: User Experience & Accessibility (High Impact)

### 📋 Interactive Terminal UI (TUI) (Medium Effort)
- **Status:** PLANNED
- **Description:** Create a terminal-based interface using a library like Textual or rich. This would allow users to navigate duplicate sets, preview file info, and approve/reject actions interactively, without complex command-line flags.
- **Benefit:** Massively improves usability for all users without leaving the comfort of the terminal. A great middle-ground before a full GUI.
- **Tasks:**
  - Research and select appropriate TUI framework (Textual, rich, or curses)
  - Design interactive screens for duplicate review and file operations
  - Implement navigation and preview functionality
  - Add progress indicators and real-time feedback

### 📋 Web-Based GUI (High Effort)
- **Status:** PLANNED
- **Description:** Develop a simple web interface (using a framework like Flask or FastAPI) that users can run locally. This would provide a full graphical experience with file browsers, progress bars, and visual review of duplicates.
- **Benefit:** Makes the tool accessible to anyone, regardless of their comfort with the command line. The ultimate step in user-friendliness.
- **Tasks:**
  - Design web interface mockups and user flow
  - Implement backend API using Flask or FastAPI
  - Create frontend with file browsers and duplicate review interface
  - Add real-time progress tracking and notifications
  - Implement security measures for local web access

### 📋 HTML/JSON Reporting (Low Effort)
- **Status:** PLANNED
- **Description:** Add an option to export the operation plan to a structured format like HTML or JSON. An HTML report could visually present duplicate sets with thumbnails for easy review outside the script.
- **Benefit:** Allows for easy sharing of results and offline review of the planned changes before execution.
- **Tasks:**
  - Design HTML report template with CSS styling
  - Implement JSON export functionality
  - Add thumbnail generation for video previews
  - Create shareable report format with embedded media

## Theme 2: AI & Intelligence (Medium Impact)

### 📋 Custom Category Mapping (Low Effort)
- **Status:** PLANNED
- **Description:** Allow users to provide a simple text file (map.txt) that maps the AI's default categories to the user's preferred folder names (e.g., playing basketball -> Sports, making a cake -> Cooking).
- **Benefit:** Gives users fine-grained control over their folder structure without needing to retrain the AI model.
- **Tasks:**
  - Design mapping file format and syntax
  - Implement category mapping logic
  - Add validation for mapping file
  - Create documentation and examples

### 📋 AI-Powered Search (Semantic Search) (High Effort)
- **Status:** PLANNED
- **Description:** Implement functionality to search a video library using natural language. A user could type "find videos of people swimming at the beach" and the script would use AI embeddings to find relevant videos, even if the filenames don't match.
- **Benefit:** Transforms the tool from just a de-duplicator into a powerful video search engine.
- **Tasks:**
  - Research and implement video embedding models
  - Create semantic search index
  - Develop natural language query processing
  - Implement similarity matching and ranking
  - Add search result presentation and filtering

### 📋 Scene-Level Tagging (Medium Effort)
- **Status:** PLANNED
- **Description:** Instead of one category for the whole video, analyze individual scenes (which are already detected for hashing) and generate multiple tags (e.g., beach, sunset, surfing).
- **Benefit:** Provides much richer, more granular metadata for each video, enabling better organization and search.
- **Tasks:**
  - Extend scene detection to include content analysis
  - Implement per-scene AI categorization
  - Design metadata storage for scene-level tags
  - Create aggregation logic for video-level categories
  - Add scene-based search and filtering

## Theme 3: Performance & Core Engine (High Impact)

### 📋 Persistent Caching Database (Medium Effort)
- **Status:** PLANNED
- **Description:** Create a local SQLite database to store file hashes, metadata, and quality scores. On subsequent runs, the script would only need to process new or changed files.
- **Benefit:** A massive performance improvement for users who regularly scan the same large libraries. The single biggest speed-up possible.
- **Tasks:**
  - Design database schema for caching
  - Implement SQLite integration
  - Add cache invalidation logic for changed files
  - Create cache management and cleanup utilities
  - Add cache statistics and reporting

### 📋 Audio Fingerprinting (Medium Effort)
- **Status:** PLANNED
- **Description:** Add another layer of duplicate detection by analyzing the audio track of videos. This can help differentiate between videos that are visually identical but have different language dubs or commentary.
- **Benefit:** Increases detection accuracy, especially for movies or TV shows with multiple audio tracks.
- **Tasks:**
  - Research audio fingerprinting algorithms
  - Implement audio extraction and analysis
  - Integrate audio similarity into duplicate detection
  - Add configuration options for audio matching sensitivity
  - Handle videos with multiple audio tracks

## Theme 4: New Capabilities (Medium Impact)

### 📋 Transcoding Module (Medium Effort)
- **Status:** PLANNED
- **Description:** Add an option to re-encode lower-quality duplicates into a standard, efficient format (like H.265/HEVC) instead of deleting them. Users could set a target resolution or quality level.
- **Benefit:** Provides an alternative to deletion, allowing users to save space while keeping all their content in a standardized format.
- **Tasks:**
  - Implement transcoding pipeline using FFmpeg
  - Add quality and format configuration options
  - Create progress tracking for transcoding operations
  - Add validation for transcoded output
  - Implement batch transcoding with resource management

### 📋 Metadata Editor (High Effort)
- **Status:** PLANNED
- **Description:** Allow users to batch-edit video metadata tags (like title, description, date) based on folder names or other criteria.
- **Benefit:** Adds a powerful new organizational capability, helping users clean up their library's metadata.
- **Tasks:**
  - Research video metadata standards and formats
  - Implement metadata reading and writing
  - Create batch editing interface and rules engine
  - Add metadata validation and backup
  - Design template system for automated metadata generation

## Timeline and Prioritization
- **Immediate (0-3 Months):** Focus on Critical and Major issues like testing suite implementation, resource limits for parallel processing, and enhanced error recovery to ensure reliability and performance.
- **Short-Term (3-6 Months):** Address Major usability improvements (simplified configuration, TUI prototype, HTML reporting) and correctness enhancements (quality assessment criteria, fuzzy matching configurability). This also includes the planned migration to the Loguru logging library.
- **Medium-Term (6-12 Months):** Explore Major opportunities like persistent caching, audio fingerprinting, and transcoding module, alongside AI enhancements like custom category mapping.
- **Long-Term (12+ Months):** Build advanced features like semantic search, web GUI, and metadata editor, while developing community engagement and educational content.

## Conclusion
This roadmap provides a strategic plan to elevate 'Video Dedupe AI' from a powerful tool to a leading solution for video management. By addressing critical reliability gaps, optimizing performance, and seizing innovative opportunities, the project can meet the needs of both technical and non-technical users while maintaining a robust, maintainable codebase. The new themes focus on user experience, AI intelligence, performance optimization, and expanded capabilities to transform the tool into a comprehensive video management solution. Feedback and prioritization adjustments from stakeholders are welcome to refine this roadmap further.
