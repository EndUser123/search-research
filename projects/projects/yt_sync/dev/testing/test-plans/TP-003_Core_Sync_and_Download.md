# Test Plan 003: Core Sync & Download

- **Related Task:** `YT-TEST-7-3`
- **Core Principles:** `docs/testing/qa-checklist.md`

### Objective
To validate the end-to-end process of discovering, filtering, and downloading new videos for a single channel.

### Setup
1.  Choose a small, real YouTube channel for testing.
2.  Create an empty directory for this channel in your `base_dir`.
3.  Ensure your `config.yaml` points to this `base_dir`.
4.  Ensure your `url_file` contains only the URL for this test channel.

### Test Cases
1.  **First-Time Sync ("Clean Slate"):**
    -   **Arrange:** The channel directory is completely empty.
    -   **Act:** Run `python yt_channel_sync.py --config config.yaml`.
    -   **Assert:** The script discovers all videos, downloads them (or a subset, depending on your test speed), and creates the `.metadata/downloads.txt` archive file. Verify the downloaded files exist and the archive is populated.

2.  **Incremental Sync (No New Videos):**
    -   **Arrange:** Use the state from the successful completion of Test Case 1.
    -   **Act:** Run `python yt_channel_sync.py --config config.yaml` again.
    -   **Assert:** The script runs quickly. Logs should show that the RSS feed was checked (or API was queried) and that "All remote videos are already in the archive." No download activity should occur.

3.  **Filter Logic Verification:**
    -   **Arrange:** Reset to a clean slate (empty channel directory). Create a `filters.json` file and point to it in your `config.yaml`. Add a rule to exclude a specific, known video from the test channel (e.g., based on "Trailer" in the title).
    -   **Act:** Run `python yt_channel_sync.py --config config.yaml`.
    -   **Assert:** All videos *except* the filtered one are downloaded. Check the logs for a message like "Filters excluded 1 videos."
