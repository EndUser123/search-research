import json

# Write findings JSON
data = {
    "handoff": {
        "agent_name": "adversarial-io-validation",
        "workflow": "/adversarial-review",
        "status": "SUCCESS",
        "timestamp": "2026-05-22T18:49:27Z",
        "session_id": "console_335aa7aa-bdf7-4b27-9ccf-83514bf3fdd1",
        "terminal_id": "pre-mortem-20260522_184927"
    },
    "summary": {
        "overall_assessment": [
            "cc-bifrost.ps1 has multiple I/O validation gaps across file existence, environment variable assumptions, temp file handling, and process detection",
            "Critical: No validation that required env vars are actually set after .env loading - script proceeds with hardcoded fallbacks silently",
            "High: Temp file operations in Show-BifrostStatus (line 475-478) and Verify-BifrostRouting (line 493-496) write Python code to temp files without cleanup guarantee on error path",
            "High: PID-based process detection is unreliable on Windows - PID can be reused by unrelated processes; name matching 'bifrost' is imprecise",
            "Medium: bifrost_db.py path resolution via $PSScriptRoot could fail silently if PowerShell context does not set it properly"
        ],
        "systemic_issues": True,
        "confidence_level": "high"
    },
    "findings": [
        {
            "id": "IO-001",
            "severity": "blocker",
            "location": "cc-bifrost.ps1:36-43 (env loading) and lines 46-50 (env var usage)",
            "problem": "Required environment variables are used without validation after .env load. ANTHROPIC_AUTH_TOKEN, BIFROST_API_KEY, and model defaults are set from .env but never verified. If .env is missing or incomplete, script silently proceeds with hardcoded fallback values - including a hardcoded ANTHROPIC_AUTH_TOKEN (line 50) and BIFROST_API_KEY (line 46).",
            "adversarial_scenario": "User runs cc-bf without P:.env file present. Script prints a WARN but then proceeds with the hardcoded sk-bf-... key and hardcoded sk-cp-... auth token. Claude Code model picker believes it has valid credentials when it may not.",
            "impact": "Authentication failures at runtime when Bifrost or upstream providers reject the fallback credentials. Silent fallback to incorrect credentials can cause confusing auth failed errors that are hard to diagnose.",
            "recommendation": "After .env loading, validate required keys exist: if ANTHROPIC_AUTH_TOKEN is still the hardcoded default AND no real .env provided it, emit [ERROR] and exit instead of proceeding."
        },
        {
            "id": "IO-002",
            "severity": "high",
            "location": "cc-bifrost.ps1:475-478 (Show-BifrostStatus temp file)",
            "problem": "Python probe code is written to a temp file via GetTempFileName() + WriteAllText, then executed with python3. The temp file is removed in ErrorAction SilentlyContinue - if python3 fails or the script crashes before the Remove-Item call, the temp file persists indefinitely.",
            "adversarial_scenario": "python3 is not installed or points to a broken interpreter. The WriteAllText succeeds, the script tries to run python3, an exception is thrown before Remove-Item executes, and the temp .py file remains on disk with potentially sensitive probe code.",
            "impact": "Temp file leak; potential information disclosure if probe code contains model names or routing information written to a predictable temp location.",
            "recommendation": "Use a try/finally pattern or explicitly delete in a dedicated finally block. On Windows, temp files in %TEMP% may also survive across sessions."
        },
        {
            "id": "IO-003",
            "severity": "high",
            "location": "cc-bifrost.ps1:493-496 (Verify-BifrostRouting temp file)",
            "problem": "Same pattern as IO-002 but writes the entire routes_probe.py content to a temp file for execution. Identical cleanup gap - Remove-Item runs in ErrorAction SilentlyContinue after the python3 call, so a crash or exception between WriteAllText and Remove-Item leaves the file behind.",
            "adversarial_scenario": "python3 routes_probe.py fails due to a missing Python dependency in the environment. The routes_probe.py content is written to temp, execution fails, and the file remains on disk.",
            "impact": "Temp file persistence with probe logic content; same leak risk as IO-002.",
            "recommendation": "Same fix as IO-002 - use a PowerShell try/finally to guarantee cleanup."
        },
        {
            "id": "IO-004",
            "severity": "high",
            "location": "cc-bifrost.ps1:241-257 (Get-BifrostProcess PID detection)",
            "problem": "Legacy PID-based process detection uses PID file content to call Get-Process -Id. On Windows, PIDs are recycled aggressively. The check only verifies ProcessName -like 'bifrost' - this is a loose substring match that can false-positive on processes like 'bifrost-wrapper' or 'my-bifrost-tool'. Also, the stale PID cleanup at line 255 runs unconditionally when any PID check fails, potentially removing a PID file created by a concurrent cc-bf invocation.",
            "adversarial_scenario": "Another application named 'bifrost-ui.exe' is running (unrelated to this Bifrost). The PID file contains that app PID. Get-Process finds it, the name matches 'bifrost', and Get-BifrostProcess returns that unrelated process as if it were the Bifrost daemon. Stop-BifrostDaemon then kills the wrong process.",
            "impact": "Killing an unrelated process. Data loss if that process had pending work. The 'bifrost' substring match is also vulnerable to a collision.",
            "recommendation": "Use a more specific process name check or verify process command-line arguments using Get-CimInstance to get the actual command line and verify it points to the correct bifrost binary path."
        },
        {
            "id": "IO-005",
            "severity": "high",
            "location": "cc-bifrost.ps1:193-236 (Sync-BifrostConfig file write)",
            "problem": "config.json write via WriteAllText at line 234 has no guarantee the write succeeded before the function returns success. The appDir existence is assumed - if APPDATA is unset or the directory does not exist, WriteAllText may fail silently or create the file in an unexpected location.",
            "adversarial_scenario": "APPDATA is unset (some Windows configurations or containerized environments). WriteAllText writes to the current working directory instead of the intended config location. Bifrost reads from the wrong config file, and the users actual config.json is never updated.",
            "impact": "Configuration not applied; Bifrost runs with stale config. The user sees 'Synced N rules' confirmation but the actual file is elsewhere.",
            "recommendation": "Verify $env:APPDATA exists before the WriteAllText call. Consider using Test-Path to confirm the file was actually written to the expected location before printing the success message."
        },
        {
            "id": "IO-006",
            "severity": "high",
            "location": "cc-bifrost.ps1:125-150 (bifrost_db.py path resolution)",
            "problem": "bifrost_db.py path is constructed as $PSScriptRoot/scripts/bifrost_db.py. $PSScriptRoot is set by PowerShell when running a script file, but can be null or empty if the script is dot-sourced or run via -Command. All DB queries call python3 on the path and would fail silently (empty results) if $PSScriptRoot is invalid, returning empty results without explanation.",
            "adversarial_scenario": "User sources the script in a PowerShell session where $PSScriptRoot is empty. python3 receives an invalid path, fails, and all DB queries return empty. All routing table operations show 'no routes loaded from DB' but the script never explains WHY - the real error is swallowed.",
            "impact": "Silent failure mode where the script appears to work but has no routing rules. Users see confusing 'no routes loaded from DB' error with no indication that the underlying issue is $PSScriptRoot resolution.",
            "recommendation": "Add explicit validation that $_db_script is a valid absolute path before calling python3. Fail fast with a clear error message if $PSScriptRoot is empty."
        },
        {
            "id": "IO-007",
            "severity": "medium",
            "location": "cc-bifrost.ps1:193-199 (backup path collision)",
            "problem": "Backup file pattern uses Get-Date -f 'yyyyMMdd-HHmmss' which has second-level granularity. If --sync is called twice within the same second, the second Copy-Item overwrites the first backup without warning. The backup file path is not returned or logged in a way that lets the user find it later.",
            "adversarial_scenario": "User runs cc-bf --sync from two terminal windows within the same second. The second invocation overwrites the first backup. If config.json was corrupted, only the immediately preceding backup exists - the one from the other terminal is gone.",
            "impact": "Potential loss of the most recent backup if two sync operations race.",
            "recommendation": "Add a uniqueness guarantee - either append a random component or fail if the backup target already exists."
        },
        {
            "id": "IO-008",
            "severity": "medium",
            "location": "cc-bifrost.ps1:267-279 (binary fallback chain)",
            "problem": "The binary fallback chain (v1.5.2 -> v1.5.0-prerelease8 -> 7 -> 6) uses multiple Test-Path calls. If the binary exists but is corrupted or the wrong architecture, the script proceeds without verifying it actually runs. The error log redirect means stderr from the binary itself is lost unless the user manually checks the temp log file.",
            "adversarial_scenario": "Bifrost v1.5.2 binary exists at the checked path but is a different build (e.g., x86 on x64 Windows). Start-Job reports 'Running' but the Bifrost HTTP server never starts. The user sees 'Started Bifrost' in green but the API never responds. The 70-second wait in Restart-BifrostDaemon eventually times out with a warning, but the underlying error is buried in a temp log file.",
            "impact": "Silent binary failure leading to confusing 'Bifrost API not responding after 70s' error with no actionable diagnostic info.",
            "recommendation": "After Start-Job, verify the binary actually started by checking if the port is listening. Start-BifrostDaemon itself does not verify the binary came up unlike Restart-BifrostDaemon."
        },
        {
            "id": "IO-009",
            "severity": "medium",
            "location": "cc-bifrost.ps1:360-377 (Show-BifrostDashboard port detection)",
            "problem": "The function uses netstat parsing to find the listening port for the Bifrost process. The regex pattern assumes netstat output format. On non-English locales, netstat output may differ and the regex does not match. If netstat fails or returns empty, the catch block silently falls through to default port 8080, which could be wrong.",
            "adversarial_scenario": "Non-English Windows where netstat output uses localized column headers or number formatting. The regex does not match, netstat returns empty, the catch fires, and the dashboard opens on port 8080 even though Bifrost is on a different port - user sees a blank or wrong dashboard.",
            "impact": "Dashboard opens at wrong URL, user confusion about whether Bifrost is running.",
            "recommendation": "Use a more robust port detection method (e.g., Get-NetTCPConnection which returns structured objects) instead of parsing netstat text output."
        },
        {
            "id": "IO-010",
            "severity": "low",
            "location": "cc-bifrost.ps1:251-256 (stale PID cleanup)",
            "problem": "When the PID file contains a stale PID, the Remove-Item at line 255 runs unconditionally as part of the PID file check. If a concurrent cc-bf process has just created a new PID file for a freshly started Bifrost, the stale check in the other process could delete that new PID file before the new process has a chance to use it.",
            "adversarial_scenario": "Two cc-bf invocations race: Process A starts Bifrost and writes PID 1234 to the file. Process B checks the PID - 1234 does not exist yet (Bifrost still starting). Process B deletes the PID file. Process A's Bifrost is running but its PID file is gone. Future calls to Get-BifrostProcess cannot find the running Bifrost via PID.",
            "impact": "Split-brain Bifrost instances or duplicate daemon processes on repeated invocations.",
            "recommendation": "Add file locking around PID file access, or use a more robust mechanism for tracking the daemon (e.g., a named mutex)."
        }
    ],
    "open_questions": [
        "Is $PSScriptRoot reliably set in all expected PowerShell invocation contexts (direct run, dot-source, -Command)?",
        "What is the actual content of bifrost_db.py and routes_probe.py? These helper scripts may have their own I/O validation gaps.",
        "Has the hardcoded ANTHROPIC_AUTH_TOKEN (line 50) ever been rotated? If it was ever committed with a real token, it should be treated as potentially compromised.",
        "Is there any integration test that validates --sync actually writes valid config.json that Bifrost can read back? The write path has no verification."
    ]
}

p = r"P:/.claude/.artifacts/console_335aa7aa-bdf7-4b27-9ccf-83514bf3fdd1/pre-mortem/pre-mortem-20260522_184927/specialists/adversarial-io-validation-findings.json"
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print("Written:", p)

# Write completion marker
marker = {"specialist": "adversarial-io-validation", "complete": True}
mp = r"P:/.claude/.artifacts/console_335aa7aa-bdf7-4b27-9ccf-83514bf3fdd1/pre-mortem/pre-mortem-20260522_184927/specialists/adversarial-io-validation-complete.json"
with open(mp, "w", encoding="utf-8") as f:
    json.dump(marker, f)
print("Written:", mp)