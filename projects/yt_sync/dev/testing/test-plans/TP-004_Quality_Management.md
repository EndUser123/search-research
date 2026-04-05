# Test Plan 004: Quality Management

- **Related Task:** `YT-TEST-7-4`
- **Core Principles:** `docs/testing/qa-checklist.md`

### Objective
To validate that the `QualityChecker` can correctly identify a low-quality video and that the system can successfully upgrade it.

### Setup
1.  You will need a low-resolution (e.g., 360p) version of a video that is also available in high-resolution on YouTube. You can use `yt-dlp` manually to download one: `yt-dlp -f "bestvideo[height<=360]+bestaudio" -o "low_res_test_video.mp4" [VIDEO_URL]`
2.  Place this `low_res_test_video.mp4` file into a clean test channel directory.
3.  Manually rename the file to include the video's 11-character ID, e.g., `Low Quality Test Video [VIDEO_ID_HERE].mp4`.
4.  Manually add the video's ID to the `.metadata/downloads.txt` file (e.g., `youtube VIDEO_ID_HERE`).
5.  Ensure `quality_management.enable_quality_upgrade` is set to `true` in your `config.yaml`.

### Test Cases
1.  **Low-Quality Upgrade Workflow:**
    -   **Arrange:** Complete all setup steps above.
    -   **Act:** Run `python yt_channel_sync.py --config config.yaml` for the test channel.
    -   **Assert:**
        -   The log should show a message like "Low quality found... Queued for upgrade."
        -   The log should show the old file being backed up (if enabled) or deleted.
        -   The log should show a new download starting for that video ID.
        -   After the run, verify that the new video file in the directory has a higher resolution (using a media player or `ffprobe`).
        -   Verify the old low-res file exists in the `_quality_backups` directory (if enabled).
