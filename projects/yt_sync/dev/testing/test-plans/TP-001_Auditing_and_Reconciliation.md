# Test Plan 001: Filesystem Auditing & Reconciliation

- **Related Task:** `YT-TEST-7-1`
- **Core Principles:** `docs/testing/qa-checklist.md`

### Objective
To validate that the `Auditor` and `LibraryReconciler` components can correctly identify and fix discrepancies between the local filesystem and the download archive.

### Setup
1.  Create a temporary library structure: `test_library/TestChannel/.metadata/`.
2.  Inside `.metadata`, create an empty `downloads.txt` file.
3.  Use a minimal `test_config.yaml` pointing `base_dir` to `./test_library`.
4.  For tests involving the reconciler (`--import-and-fix`), ensure `url_file` points to a file containing a valid channel URL, as the reconciler needs to fetch remote data.

### Test Cases
1.  **Consistent State:**
    -   **Arrange:** Create `video [_validID001].mp4` and add `youtube _validID001` to `downloads.txt`.
    -   **Act:** Run `python yt_channel_sync.py --audit --config test_config.yaml`.
    -   **Assert:** Logs show "✅ No orphans, ghosts, duplicates, or unparsable files found. Library is consistent."

2.  **Ghost Entry:**
    -   **Arrange:** Add `youtube _ghostID002` to `downloads.txt`. Ensure no file with this ID exists.
    -   **Act 1:** Run with `--audit`.
    -   **Assert 1:** Logs report "Found 1 Ghost Entries..." and lists `_ghostID002`.
    -   **Act 2:** Run a normal sync (no flags, not in audit mode).
    -   **Assert 2:** Logs show "Successfully removed 1 ghost entries". Verify `downloads.txt` no longer contains the ghost ID.

3.  **Orphan File:**
    -   **Arrange:** Create a video file `Orphaned Video [_orphanID03].mp4`. Ensure this ID is not in `downloads.txt`.
    -   **Act 1:** Run with `--audit`.
    -   **Assert 1:** Logs report "Found 1 Orphaned Video ID(s)...".
    -   **Act 2:** Run a normal sync.
    -   **Assert 2:** Logs show "Successfully imported 1 videos into the archive file". Verify `downloads.txt` now contains the orphan ID.

4.  **Fix & Reconcile:**
    -   **Arrange:** Create an orphan file with a valid channel ID in its name (e.g., `badly named file [_validID001].mp4`). Ensure the ID is valid for the channel in your `url_file`.
    -   **Act:** Run `python yt_channel_sync.py --audit --import-and-fix --config test_config.yaml`.
    -   **Assert:** Logs show the file was renamed to the correct format based on its fetched metadata and that the ID was added to `downloads.txt`.

5.  **Filter Reconciliation:**
    -   **Arrange:** Add a valid, downloaded video ID to `downloads.txt`. Create a `filters.json` file that would now exclude this video (e.g., by a title keyword).
    -   **Act:** Run `python yt_channel_sync.py --audit --audit-filters --config test_config.yaml`.
    -   **Assert:** Logs report "Found 1 Filter Mismatches..." and lists the ID of the video that no longer matches the rules.
