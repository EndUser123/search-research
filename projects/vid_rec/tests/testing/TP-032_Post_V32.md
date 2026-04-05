### QA Check-in Plan: Verification of Completed Features (Tasks 2.5 & 3.2)

**Context:** Performing post-implementation QA for recent major changes (unified subtitle progress bar and parallel processing) before starting the next feature (Task 3.1). This plan aligns with `docs/QA_CHECKLIST.md`.

#### **Phase 2: Implementation & Code Quality (Reviewing current state based on recent tasks)**

* `[ ]` **Logging:** Does every major action, decision point, and error path log useful information?
    * **Check:** Verify that messages like "Loading Whisper model...", "Processing: [filename]", "-> Finished: [filename]", and error messages are clearly logged. Ensure `tqdm.write` is used to prevent progress bar corruption.
* `[ ]` **Configuration:** If the feature needs a setting, is it added to `config.py` with a sensible default?
    * **Check:** `create_subtitles` and `normalize_audio` settings in `src/config.py` are already present and were used in our test setup.
* `[ ]` **State Management:** Does the `state_manager` correctly record the outcome (e.g., success, failure, new intermediate states)?
    * **Check:** This will be validated in "Phase 3: Verification" by inspecting `vidrec_state.db`.

#### **Phase 3: Verification (Execution of Test Runs)**

**1. Preparation**

* **Test Files:** Place at least two video files (e.g., `video_no_subs.mp4` without subs, `video_with_subs.mp4` with subs, and an optional larger third file) in a dedicated test directory (e.g., `test_videos/`).
* **Clear State:** Delete the `vidrec_state.db` file from your project's root directory.
* **Configure `config.toml`:** Open `config.toml` and ensure these settings are applied:
    * `paths.source = "path/to/your/test_videos/"` (Update this to your actual test directory path)
    * `settings.create_subtitles = true`
    * `settings.normalize_audio = true`
    * `settings.no_replace = true` (Crucial for safety during testing, prevents overwriting originals)

**2. Test Run 1: Full Processing & Interruption**

* **Execution:** Run your application from the terminal:
    ```bash
    python src/main_processor.py
    ```
* **Observations (Checklist Item: Logging, State Management):**
    * `[ ]` **Subtitle Model Loading:** Confirm "Loading Whisper model" appears *before* `tqdm` progress starts.
    * `[ ]` **Unified Subtitle Progress:** Verify `tqdm` shows `Subtitle Generation` with per-file progress in its description (e.g., `Subtitles [X/Y] filename (Z%)`).
    * `[ ]` **tqdm.write usage:** Confirm other log messages during this phase do not disrupt the progress bar.
    * `[ ]` **Parallel CPU Processing:** Observe `tqdm` switches to `Overall Progress`. Confirm multiple `--- Processing:` logs appear concurrently, indicating parallel execution.
* **Simulate Interruption:** While the "Overall Progress" bar is active, press `Ctrl+C` in your terminal to stop the script.
* **Verify State (Checklist Item: State Management, Resumption Test):**
    * `[ ]` **`vidrec_state.db` Inspection:** Use a SQLite database browser to open `vidrec_state.db` (in project root).
    * `[ ]` Examine the `jobs` table:
        * `status = 'COMPLETED'` for fully processed files.
        * `status = 'SUBTITLES_COMPLETE'` for files where only subtitles finished.
        * `status = 'FAILED'` for files interrupted during CPU processing.
* **Verify Temporary Files (Checklist Item: Anticipate Failure Modes - partial cleanup):**
    * `[ ]` Check your configured `temp_dir`. Are partial or complete `.mp4` and `.en.srt` files present for jobs that were in the CPU processing phase (i.e., those marked `FAILED` or `COMPLETED` in the DB that haven't been cleaned yet)?

**3. Test Run 2: Resumption & Cleanup**

* **Execution:** Run the application **again, without deleting `vidrec_state.db`**:
    ```bash
    python src/main_processor.py
    ```
* **Observations (Checklist Items: Resumption Test, Already Done Test):**
    * `[ ]` **Skipping Completed:** Verify logs show "✅ SKIPPING: Already marked as 'COMPLETED'" for files fully processed in the previous run.
    * `[ ]` **Resuming Subtitles Complete:** Verify logs show "Found job '...' with subtitles complete, queuing for CPU processing." and these files *only* go through the CPU processing phase (no re-generation of subtitles).
    * `[ ]` **Re-processing Failed:** Verify previously `FAILED` jobs re-start processing (from subtitle generation if needed, then CPU tasks).
* **Observe Final Summary (Checklist Item: Logging):**
    * `[ ]` Review the "Job Summary" section at the end of the console output. Verify that the counts for "Completed Successfully," "Skipped (Unchanged)," and "Failed" accurately reflect the outcome of *this* specific run, considering resumption.
* **Verify Cleanup (Checklist Item: Anticipate Failure Modes - full cleanup):**
    * `[ ]` Check your `temp_dir` again. Confirm that all temporary `.mp4` and `.en.srt` files from *successfully completed* jobs are now gone from the `temp_dir` (as `no_replace=true` implies cleanup of temporary files once the job is finished).

**Instructions:** As you perform these steps, mark each `[ ]` item as `[x]` upon successful verification. Report your findings for each point.
