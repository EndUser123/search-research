# Manual Regression Test Plan (v1)

**Objective:** To validate the stability and correctness of all major functional components of the `yt-sync` application by systematically applying the scenarios outlined in `docs/testing/qa-checklist.md`.

Each of these scenarios corresponds to a task in the `tracking_test.json` file.

---

### **Test Scenario 1: Filesystem Auditing & Reconciliation (`YT-TEST-7-1`)**

*   **Functional Area:** `Auditor` and `LibraryReconciler`.
*   **Goal:** Verify the system can correctly identify and fix discrepancies between the filesystem and the archive file.
*   **Setup:** Create a temporary library structure: `test_library/TestChannel/.metadata/downloads.txt`.
*   **Sub-Scenarios:**
    1.  **Consistent State:** Arrange a file (`video.mp4`) and a matching archive entry. **Act** by running `--audit`. **Assert** that logs show "No orphans, ghosts...".
    2.  **Ghost Entry:** Arrange an archive entry with no matching file. **Act** with `--audit`. **Assert** that the ghost is reported. Then, **Act** with a normal sync and **Assert** the ghost entry is removed from `downloads.txt`.
    3.  **Orphan File:** Arrange a file with no matching archive entry. **Act** with `--audit`. **Assert** that the orphan is reported. Then, **Act** with a normal sync and **Assert** the file is imported into `downloads.txt`.
    4.  **Fix & Reconcile:** On the orphan file, **Act** with `--audit --import-and-fix`. **Assert** that the file is renamed (if needed) and imported into `downloads.txt`.

### **Test Scenario 2: Authentication Workflow (`YT-TEST-7-2`)**

*   **Functional Area:** `AuthCapturer`, `main_logic` (config update).
*   **Goal:** Verify the entire authentication lifecycle.
*   **Sub-Scenarios:**
    1.  **Clean Slate Auth:** Arrange by deleting `cookies.txt` and `config.yaml.bak`. **Act** by running `--refresh-auth`. **Assert** that a browser launches and that `cookies.txt` and a new `.bak` file are created.
    2.  **Returning User Auth:** Arrange with existing `cookies.txt` and a valid `test_video_url` in config. **Act** with `--refresh-auth`. **Assert** that auth succeeds without launching a browser.
    3.  **Invalid Auth:** Arrange by deleting the content of `cookies.txt`. **Act** with a normal sync. **Assert** that the application logs a clear authentication error and does not crash.

### **Test Scenario 3: Core Sync & Download (`YT-TEST-7-3`)**

*   **Functional Area:** `ChannelSyncer`, `Downloader`, `Filtering`, `Discovery`.
*   **Goal:** Verify the end-to-end download process.
*   **Sub-Scenarios:**
    1.  **New Video Download:** Arrange a test channel with known, undownloaded videos. **Act** with a standard sync. **Assert** that new videos are downloaded.
    2.  **Filtering Logic:** Arrange a `filters.json` to exclude one video. **Act** with a standard sync. **Assert** that the logs show the video was discovered but skipped by the filterer.

### **Test Scenario 4: Quality Management (`YT-TEST-7-4`)**

*   **Functional Area:** `QualityChecker`.
*   **Goal:** Verify the quality upgrade workflow.
*   **Sub-Scenarios:**
    1.  **Upgrade Trigger:** Arrange a low-resolution video file and its corresponding archive entry. **Act** with a standard sync. **Assert** that logs show the file was identified for upgrade, backed up, and replaced with a higher-quality version.
