# FR-12: Connection Diagnostics

## Acceptance Criteria
- AC.12.1: Check network connectivity to YouTube
- AC.12.2: Validate yt-dlp installation and version
- AC.12.3: Check cookie file presence and validity
- AC.12.4: Validate database health and integrity
- AC.12.5: Provide clear remediation steps for failures
- AC.12.6: Support individual category checks via flags
- AC.12.7: Attempt auto-fix when --fix flag is used

## CLI Command
```bash
yt-fts diagnose              # Run all diagnostics
yt-fts diagnose --network    # Network only
yt-fts diagnose --ytdlp      # yt-dlp only
yt-fts diagnose --cookies    # Cookies only
yt-fts diagnose --database   # Database only
yt-fts diagnose --fix        # Auto-fix where possible
```
