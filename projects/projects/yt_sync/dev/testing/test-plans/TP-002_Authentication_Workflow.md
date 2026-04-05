# Test Plan 002: Authentication Workflow

- **Related Task:** `YT-TEST-7-2`
- **Core Principles:** `docs/testing/qa-checklist.md`

### Objective
To validate the entire authentication lifecycle, from capture using Playwright to usage in API calls and downloads.

### Setup
1.  Ensure you have a `config.yaml` with your `youtube_api_keys`.
2.  Have a known, publicly accessible but age-restricted YouTube video URL ready.

### Test Cases
1.  **Clean Slate Authentication Capture:**
    -   **Arrange:** Delete any existing `cookies.txt` and `config.yaml.bak` files.
    -   **Act:** Run `python yt_channel_sync.py --refresh-auth --config config.yaml`.
    -   **Assert:**
        -   The script launches a browser window.
        -   After successful login, `cookies.txt` is created and is not empty.
        -   `config.yaml.bak` is created.
        -   The `authentication` section in `config.yaml` is populated with `cookies_file` and `http_headers`.

2.  **Returning User Verification:**
    -   **Arrange:** Use the state from the successful completion of Test Case 1. Ensure `config.yaml` contains the valid auth data.
    -   **Act:** Run `python yt_channel_sync.py --refresh-auth --config config.yaml` a second time.
    -   **Assert:** The script verifies the existing cookies are valid *without* launching a browser. The console should log a success message.

3.  **Graceful Failure on Invalid Auth:**
    -   **Arrange:** Manually invalidate the `cookies.txt` file by deleting its contents but leaving the file empty.
    -   **Act:** Run a normal sync command on a channel that requires authentication (or use the `--refresh-auth` which will first attempt to validate).
    -   **Assert:** The application logs a clear authentication failure error. It **must not** crash with an unhandled exception. It should report the failure and proceed gracefully (or exit).
