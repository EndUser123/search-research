# Product Requirements Document: Library Repair and Adoption Tool

**Document Version:** 1.1
**Status:** Draft
**Author:** LLM Architect
**Date:** 2025-06-23

---

### 1. Introduction & Background

The `YT_Sync` application is designed to create and maintain a local library of YouTube videos. Users may have pre-existing video libraries from other downloaders or previous versions of this tool. These libraries often contain files with inconsistent or non-standard naming conventions (e.g., missing the `[video_id]`).

Currently, the application's `--audit` command correctly identifies these files as "untracked" or "unparsable." However, it offers no mechanism to fix them. The only user recourse is to manually delete these files and allow `YT_Sync` to re-download them, resulting in significant waste of user bandwidth, time, and API quota.

This document outlines the requirements for a **Library Repair and Adoption Tool**, a new feature designed to solve this problem by intelligently integrating existing local files into the managed library.

### 2. User Stories

1.  **Primary Goal (Adoption):**
    > **As a** user with an existing video library,
    > **I want** the tool to intelligently scan and adopt my local video files,
    > **so that** I don't have to re-download content I already possess, saving time and bandwidth.

2.  **Safety & Confidence:**
    > **As a** cautious user,
    > **I want** to preview all proposed file changes (renames, quarantines) before they are executed,
    > **so that** I can feel confident the tool will not damage my library.

3.  **Control & Flexibility:**
    > **As an** advanced user with non-standard filenames,
    > **I want** to control the sensitivity of the title-matching logic,
    > **so that** I can fine-tune the adoption process for my specific library's naming scheme.

4.  **Resource Efficiency:**
    > **As a** user with a large library,
    > **I want** the application to cache API metadata on disk,
    > **so that** repeated audit or repair operations are fast and do not exhaust my API quota.

### 3. Core Feature Requirements

#### **FR-1: Command-Line Interface**
*   The feature will be controlled via the `--audit` and `--repair` command-line flags.
*   **`--audit`:** When run alone, the tool performs a **read-only** analysis of the library. It will identify and report on all issues, including untracked files that are candidates for repair. **It will not modify any files.**
*   **`--audit --repair`:** This combination executes the repair process. The `--repair` flag acts as the user's explicit consent to perform write operations (renaming, moving files, and updating the archive).
*   **`--audit --repair --dry-run`:** This combination will perform a full simulation and print a detailed report of every action it *would* have taken, without modifying any files.

#### **FR-2: Persistent Metadata Cache (CRITICAL REQUIREMENT)**
*   The `MetadataManager` **must** implement a persistent, on-disk cache for all metadata retrieved from the YouTube Data API.
*   The cache will be stored in a JSON file located at `{channel_directory}/.metadata/api_metadata_cache.json`.
*   When metadata for a video ID is requested, the `MetadataManager` **must** first attempt to load it from the disk cache.
*   An API call for a given video ID should only be made if that ID is not present in the on-disk cache.
*   After successfully fetching new metadata from the API, it must be saved to the on-disk cache to be available for all subsequent application runs.

#### **FR-3: Discovery & Verification Logic**
*   The tool will process channels sequentially as defined in the `url_file` specified in `config.yaml`.
*   For each channel, it will identify "untracked" files (video files on disk not present in the channel's `downloads.txt` archive).
*   To be "adopted," an untracked file must pass a series of checks against its official metadata (retrieved from the **Metadata Cache** first, then API).
    1.  **ID Discovery:** A valid 11-character YouTube ID must be parsable from the file's name.
    2.  **Duration Match:** The local file's duration (via `ffprobe`) must be within a small tolerance (e.g., +/- 2 seconds) of the cached/API metadata.
    3.  **Quality Match:** The local file's resolution must meet or exceed the `minimum_height` in `config.yaml`.
    4.  **Title Similarity:** The filename must be reasonably similar to the official video title. The similarity threshold will be user-configurable.

#### **FR-4: File Actions**
*   **Adopt:** If a file passes all verification checks, the tool will:
    1.  Rename the file to the project's standard format: `{Sanitized Title} [{Video ID}].{ext}`.
    2.  Add the video ID to the channel's `downloads.txt` archive.
*   **Quarantine:** If a file has a parsable ID but fails any verification check, it will be moved to a `_quarantine` sub-directory within the channel's folder.

#### **FR-5: Reporting and Feedback**
*   The tool must provide clear console output, indicating which channel is being processed.
*   For each channel, it must report the number of untracked files found.
*   During a repair operation, it will use a progress bar to show progress on the verification of files.
*   The final output will be a summary of actions taken across all processed channels.

### 4. Non-Functional Requirements

*   **NFR-1: Performance:** The verification process for large numbers of files must be performed concurrently. The metadata cache is critical to ensuring this is fast and does not exhaust API quotas.
*   **NFR-2: Safety & Reliability:** The tool must handle errors gracefully (e.g., file locks, API failures, corrupted cache files) and perform a pre-flight check for `ffprobe`.
*   **NFR-3: Usability:** The purpose of each action and the reasons for failure must be clearly logged. The feature must be documented in the `user_guide.md`.

### 5. Out of Scope for v1

*   **Interactive Repair:** Will not prompt the user file-by-file.
*   **Duplicate File Resolution:** Does not handle multiple files for already-tracked IDs.
*   **ID Guessing:** Will not attempt to identify a video if the ID is not present in the filename.

### 6. Success Metrics

*   Running `--audit` twice in a row results in zero API calls on the second run.
*   Users can successfully migrate an existing, non-standard library to a fully tracked `YT_Sync` library with minimal re-downloads.
*   Bandwidth and API quota consumption are near-zero for the adoption of existing, valid files.
