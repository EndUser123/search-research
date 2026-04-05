### Proposed Development & QA Checklist for `yt-sync`

This checklist would be mandatory for any new feature or significant bugfix.

#### **Phase 1: Feature Design & Planning**

*   `[ ]` **Define User Story:** What is the user trying to accomplish? (e.g., "As a user, I want to refresh my authentication with a single command so I don't have to manually find URLs and edit files.")
*   `[ ]` **Identify External Dependencies:** What external services or libraries are involved?
    *   *For this feature: `yt-dlp` (subprocess), `Playwright` (browser automation), Google/YouTube Login Service.*
*   `[ ]` **Anticipate Failure Modes:** What are the likely points of failure for each dependency?
    *   `yt-dlp`: Network errors, command failures, **restricted content errors**.
    *   `Playwright`: Browser not found, page timeout, **bot detection by the target site**.
    *   Google Login: Unresponsive UI, CAPTCHAs, 2FA prompts.
    *   **This step alone would have flagged "bot detection" as a high-risk item requiring a specific solution (like persistent profiles).**

#### **Phase 2: Implementation & Code Quality**

*   `[ ]` **Logging & Diagnostics:** Does every major action and decision point log its state?
    *   `[ ]` Does every external call (subprocess, API request) log its parameters before execution?
    *   `[ ]` Does every external call log its result (success, failure, `stdout`, `stderr`) at a `DEBUG` level?
    *   **This would have immediately caught the empty log file issue.** The developer would have seen the `subprocess.run` call in `diagnostics.py` and realized its output wasn't being piped to the `logger`.
*   `[ ]` **Configuration Management:** Does the feature interact with user configuration?
    *   `[ ]` Is there a clear and safe update path? (e.g., backup before write).
    *   `[ ]` Are all generated files that contain user data or state (`.auth_profile`, `cookies.txt`, `config.yaml.bak`) added to `.gitignore`?
    *   **This would have prompted the creation of the `.gitignore` file from the start.**
*   `[ ]` **Error Handling:** Is every `try...except` block specific? Does it handle the anticipated failure modes gracefully?
*   `[ ]` **Documentation:** Is the new feature/flag documented in `PROJECT_HANDBOOK.md` with a clear user-facing explanation?

#### **Phase 3: Pre-Testing & Verification (Developer's Responsibility)**

*   `[ ]` **The "Clean Slate" Test:** Has the feature been tested in an environment that mimics a first-time user?
    *   `[ ]` Delete all temporary files (`.auth_profile`, `cookies.txt`, `config.yaml.bak`, `yt_sync.log.txt`).
    *   Run the command.
    *   **This test is crucial. It would have immediately revealed the bot detection issue, as a fresh profile is the most likely to be flagged.**
*   `[ ]` **The "Returning User" Test:** Has the feature been tested in an environment where state already exists?
    *   Run the command a second time to ensure it handles existing profiles/files correctly.
*   `[ ]` **Log File Review:** After a test run, review `yt_sync.log.txt`. Is the information clear? Is anything missing? Is it too noisy?
