# Manual Testing Plan for Video Dedupe AI

**Document Version:** 1.0
**Test Cycle:** 1
**Date:** 2025-06-28

## 1. Objective

The purpose of this document is to outline the manual testing procedures for the `vda_cli.py` script (version 2.2.0). These test cases are designed to validate the core functionalities, safety features, and edge case handling of the application before beginning automated unit testing.

## 2. Test Environment Setup

Before executing any test cases, prepare the following environment:

- **Workspace:** Use the existing workspace at `c:/_Python/_Projects/Video_Dedupe_AI`.
- **Required Software:**
  - Python 3.8+
  - FFmpeg installed and accessible in the system's PATH.
  - All dependencies from `requirements.txt` installed in your Python environment (`pip install -r requirements.txt`).
- **Test Script:** Ensure `vda_cli.py` is accessible in the current workspace.
- **Test Files:** Use prepared video files located in `C:\Users\brsth\Videos\`. For these tests, we will assume you have:
  - `video_A_1080p.mp4` (A high-quality, larger file)
  - `video_A_480p.mp4` (A lower-quality, smaller version of the same video)
  - `video_B_720p.mp4` (An unrelated video)
  - `corrupted_video.mp4` (A zero-byte or otherwise invalid video file)
- **Media Directory Root:** The root directory for media files is `d:\_trading\courses\_keep\simpler trading`.

## 3. Manual Test Cases

### Test Case ID: MTC-01 - Sanity Check (Dry Run - Recursive Scan)

-   **Objective:** Verify that the `vda_cli.py` script correctly identifies duplicates across all video files within `C:\Users\brsth\Videos` and its subdirectories, and plans operations without making any changes to the file system (due to `--dry-run`).
-   **Setup:** Your existing directory structure under `C:\Users\brsth\Videos` will be used as is. No specific `main_videos` or `other_videos` folders are required for this test.
-   **Steps:**
    1.  Open a terminal in the workspace directory `c:/_Python/_Projects/Video_Dedupe_AI`.
    2.  Run the command: `python vda_cli.py "C:\Users\brsth\Videos" "C:\Users\brsth\Videos" --dry-run`
-   **Expected Result:**
    1.  The script completes without errors.
    2.  The console output displays a rich-formatted summary table outlining the "Operation Plan". This table should clearly list the planned actions (e.g., `delete`, `move`), the file paths involved, and the reason for each action.
    3.  The console output also includes a summary section with "Files in Videos Dir", "Files in Media Dir", "Moves Planned", "Deletes/Quarantines Planned", and "Potential Space Saved".
    4.  **Crucially, no files will actually be moved, deleted, or altered on your file system.** The entire `C:\Users\brsth\Videos` directory and its contents will remain unchanged, confirming that the `--dry-run` safety feature is fully functional.
- **Actual Result:**
- **Status (Pass/Fail):**

### Test Case ID: MTC-02 - Safety Check (Quarantine)

- **Objective:** Verify that the script correctly moves a lower-quality duplicate to the specified quarantine directory instead of deleting it permanently. This tests the safety feature of quarantining files, ensuring data preservation and user control over file deletion.
- **Setup:**
  - Use the same folder structure as MTC-01 under `C:\Users\brsth\Videos\`, maintaining the test environment consistency to focus on the quarantine functionality.
  - Ensure there is no `test_quarantine` folder yet under `C:\Users\brsth\Videos\`, allowing the test to validate the script's ability to create this directory automatically.
- **Steps:**
  1. Open a terminal in the workspace directory `c:/_Python/_Projects/Video_Dedupe_AI`.
  2. Run the command: `python vda_cli.py "C:\Users\brsth\Videos\main_videos" "C:\Users\brsth\Videos\other_videos" --quality-metric vmaf --quarantine-dir "C:\Users\brsth\Videos\test_quarantine"`
  3. When prompted to proceed, type `y` and press Enter.
- **Expected Result:**
  - The script completes without errors, indicating proper handling of the quarantine process.
  - A new folder named `test_quarantine` is created, demonstrating the script's ability to set up a quarantine directory as specified.
  - The `test_quarantine` folder contains `video_A_480p.mp4`, confirming that the lower-quality duplicate is moved to quarantine instead of being deleted.
  - The `main_videos` folder now contains `video_A_1080p.mp4`, verifying that the higher-quality video is retained in the primary directory based on the VMAF quality metric.
  - The `other_videos` folder now only contains `video_B_720p.mp4`, ensuring that non-duplicate files remain unaffected by the deduplication process.
- **Actual Result:**
- **Status (Pass/Fail):**

### Test Case ID: MTC-03 - Quality Logic Test

- **Objective:** Verify that the script correctly identifies the higher-quality video to keep, even if it is the larger file. This tests the functionality of the `--quality-metric vmaf` option to prioritize video quality over file size in deduplication decisions.
- **Setup:**
  - In the workspace, create two folders under `C:\Users\brsth\Videos\`: `main_videos_quality` and `other_videos_quality`, if they don't already exist, to isolate this test's environment and focus on quality-based deduplication.
  - Place `video_A_480p.mp4` (smaller, lower quality) inside `main_videos_quality`, setting up a scenario where the primary directory initially contains the less desirable version.
  - Place `video_A_1080p.mp4` (larger, higher quality) inside `other_videos_quality`, testing the script's ability to recognize and prioritize the higher-quality duplicate from a secondary directory.
- **Steps:**
  1. Open a terminal in the workspace directory `c:/_Python/_Projects/Video_Dedupe_AI`.
  2. Run the command: `python vda_cli.py "C:\Users\brsth\Videos\main_videos_quality" "C:\Users\brsth\Videos\other_videos_quality" --quality-metric vmaf --dry-run`
- **Expected Result:**
  - The script completes without errors, showing proper execution of quality assessment using VMAF.
  - The console output displays a rich-formatted summary table outlining the "Operation Plan".
  - The plan includes moving `video_A_1080p.mp4` to the `main_videos_quality` directory and deleting the original `video_A_480p.mp4`, confirming the quality metric overrode the default "keep smaller" logic.
- **Actual Result:**
- **Status (Pass/Fail):**

### Test Case ID: MTC-04 - AI Categorization Test

- **Objective:** Verify that the AI categorization feature correctly identifies video content and moves the best-quality file to a new, categorized directory. This tests the `--categorize` option combined with `--organization-dir` to ensure videos are organized based on content analysis.
- **Setup:**
  - In the workspace, create two folders under `C:\Users\brsth\Videos\`: `main_videos_ai` and `other_videos_ai`, if they don't already exist, to provide a controlled environment for testing AI categorization.
  - Place `video_A_1080p.mp4` (assuming it's a sports clip) inside `main_videos_ai`, setting up the primary directory with the higher-quality version for testing quality-based selection.
  - Place `video_A_480p.mp4` inside `other_videos_ai`, allowing the script to identify and handle the duplicate based on quality before categorization.
- **Steps:**
  1. Open a terminal in the workspace directory `c:/_Python/_Projects/Video_Dedupe_AI`.
  2. Run the command: `python vda_cli.py "C:\Users\brsth\Videos\main_videos_ai" "C:\Users\brsth\Videos\other_videos_ai" --quality-metric vmaf --categorize --organization-dir "C:\Users\brsth\Videos\test_organized"`
  3. When prompted, type `y` and press Enter. (Note: This may take time as the AI model downloads and runs).
- **Expected Result:**
  - The script completes without errors, indicating successful AI model execution and categorization.
  - A new folder named `test_organized` is created, demonstrating the script's ability to set up an organization directory as specified.
  - Inside `test_organized`, there is a subfolder named after an appropriate category (e.g., playing basketball, sports), confirming accurate content identification by the AI.
  - This subfolder contains `video_A_1080p.mp4`, verifying that the highest-quality duplicate is selected and moved to the categorized directory.
  - The `main_videos_ai` and `other_videos_ai` folders are now empty, ensuring all duplicates are processed and organized.
- **Actual Result:**
- **Status (Pass/Fail):**

### Test Case ID: MTC-05 - Edge Case (Corrupted File)

- **Objective:** Verify that the script handles corrupted or unreadable files gracefully without crashing. This tests the error handling and robustness of the script when encountering invalid video files during processing.
- **Setup:**
  - In the workspace, create a folder under `C:\Users\brsth\Videos\` named `corrupt_test`, if it doesn't already exist, to isolate this edge case test environment.
  - Place `video_B_720p.mp4` and `corrupted_video.mp4` inside `corrupt_test`, setting up a scenario with both a valid and an invalid file to test the script's discrimination and error handling capabilities.
- **Steps:**
  1. Open a terminal in the workspace directory `c:/_Python/_Projects/Video_Dedupe_AI`.
  2. Run the command: `python vda_cli.py "C:\Users\brsth\Videos\corrupt_test" "C:\Users\brsth\Videos\corrupt_test" --dry-run`
- **Expected Result:**
  - The script runs to completion without crashing.
  - The console log, formatted by `rich`, shows a clear warning or error message related to `corrupted_video.mp4`, indicating it could not be processed.
  - The final summary table shows "Moves Planned: 0" and "Deletes/Quarantines Planned: 0", confirming that no operations were planned for the corrupted file.
- **Actual Result:**
- **Status (Pass/Fail):**

### Test Case ID: MTC-06 - Generate Default Config File

-   **Objective:** Verify that the `--generate-config` option successfully creates a `config.ini` file with default settings without executing any deduplication logic.
-   **Setup:** Ensure no `config.ini` file exists in the `c:/_Python/_Projects/Video_Dedupe_AI` directory to ensure a clean test.
-   **Steps:**
    1.  Open a terminal in the workspace directory `c:/_Python/_Projects/Video_Dedupe_AI`.
    2.  Run the command: `python vda_cli.py --generate-config`
-   **Expected Result:**
    1.  A file named `config.ini` is created in the `c:/_Python/_Projects/Video_Dedupe_AI` directory.
    2.  The console output confirms the successful generation of the config file.
    3.  The script exits immediately after generating the file, without attempting any video processing.
    4.  The `config.ini` file contains sections like `[Execution Control & Performance]`, `[Safety and Logging]`, `[Matching and Filtering]`, etc., with sensible default values.
- **Actual Result:**
- **Status (Pass/Fail):**

### Test Case ID: MTC-07a - Verify Config File Settings are Loaded

-   **Objective:** Verify that the script correctly loads settings from `config.ini`, specifically `dry_run = False`.
-   **Setup:**
    1.  Ensure a `config.ini` file exists (e.g., generated from MTC-06).
    2.  Edit the `config.ini` file, specifically changing `dry_run = True` to `dry_run = False` under `[Execution Control & Performance]`.
    3.  Place two duplicate video files (`video_A_1080p.mp4` and `video_A_480p.mp4`) into `C:\Users\brsth\Videos\test_config_scan` (create this folder if it doesn't exist).
-   **Steps:**
    1.  Open a terminal in the workspace directory `c:/_Python/_Projects/Video_Dedupe_AI`.
    2.  Run the command: `python vda_cli.py "C:\Users\brsth\Videos\test_config_scan" "C:\Users\brsth\Videos\test_config_scan" --config config.ini`
-   **Expected Result:**
    1.  The script prompts for confirmation (`Proceed with executing this plan? [y/N]`), indicating that `dry_run` was correctly read as `False` from `config.ini`.
    2.  No "Dry run complete." message appears in the output.
-   **Actual Result:**
-   **Status (Pass/Fail):**

### Test Case ID: MTC-07b - Verify CLI Arguments Override Config File

-   **Objective:** Verify that a command-line argument (`--dry-run`) correctly overrides the corresponding setting (`dry_run = False`) in `config.ini`.
-   **Setup:**
    1.  Use the same setup as MTC-07a, with `dry_run = False` in `config.ini`.
-   **Steps:**
    1.  Open a terminal in the workspace directory `c:/_Python/_Projects/Video_Dedupe_AI`.
    2.  Run the command: `python vda_cli.py "C:\Users\brsth\Videos\test_config_scan" "C:\Users\brsth\Videos\test_config_scan" --config config.ini --dry-run`
-   **Expected Result:**
    1.  The script outputs "Dry run complete." and does **not** prompt for confirmation.
    2.  This confirms the `--dry-run` CLI flag successfully overrode the `config.ini` setting.
-   **Actual Result:**
-   **Status (Pass/Fail):**

## 4. Progress and Action Items Checklist

Below is a checklist summarizing the progress made and action items to be completed for the Video Dedupe AI project:

- [x] **Task:** Update `MANUAL_TESTING.md` with the correct workspace path `c:/_Python/_Projects/Video_Dedupe_AI`.
- [x] **Task:** Update `MANUAL_TESTING.md` with the correct video file paths in `C:\Users\brsth\Videos\`.
- [x] **Task:** Update `MANUAL_TESTING.md` with the media directory root `d:\_trading\courses\_keep\simpler trading`.
- [x] **Task:** Execute Test Case MTC-01 - Sanity Check (Dry Run - Recursive Scan).
  - [x] **Sub-Task:** Use your existing `C:\Users\brsth\Videos` directory structure.
  - [x] **Sub-Task:** Run the command `python vda_cli.py "C:\Users\brsth\Videos" "C:\Users\brsth\Videos" --dry-run`.
  - [x] **Sub-Task:** Verify the script completes and shows the expected plan.
  - [x] **Sub-Task:** Confirm no files are moved or deleted.
- [x] **Task:** Execute Test Case MTC-06 - Generate Default Config File.
- [ ] **Task:** Execute Test Case MTC-07 - Load Settings from Config File.
  - [ ] **Sub-Task:** Run `python -m src.vda_cli plan "C:\Users\brsth\Videos\test_config_scan" "C:\Users\brsth\Videos\test_config_scan" --config config.ini --wait` and confirm the script asks for `y/N` confirmation.
  - [ ] **Sub-Task:** Run `python vda_cli.py "C:\Users\brsth\Videos\test_config_scan" "C:\Users\brsth\Videos\test_config_scan" --config config.ini --dry-run` and confirm the script states "Dry run complete" without a prompt.
- [ ] **Task:** Execute Test Case MTC-02 - Safety Check (Quarantine).
- [ ] **Task:** Execute Test Case MTC-03 - Quality Logic Test.
- [ ] **Task:** Execute Test Case MTC-04 - AI Categorization Test.
- [ ] **Task:** Execute Test Case MTC-05 - Edge Case (Corrupted File).
- [ ] **Task:** Review all test results and update `Actual Result` and `Status` fields.
- [ ] **Task:** Address any failures by creating bug reports or resolution tasks.
- [ ] **Task:** Finalize manual testing documentation.
