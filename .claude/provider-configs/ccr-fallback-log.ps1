# ccr-fallback-log.ps1 — Surface CCR fallback events from CCR's own logs.
#
# Purpose: CCR (@musistudio/claude-code-router) does NOT expose a fallback-fired
# callback. To diagnose production failures ("did the request get routed to a
# fallback, and which one?") we tail CCR's pino JSON log and surface the
# fallback events it already writes internally.
#
# Verified CCR fallback log statements (from
# C:\Users\brsth\AppData\Roaming\npm\node_modules\@musistudio\claude-code-router\dist\cli.js):
#   e.log.info(`Trying fallback model: <provider>,<model>`)
#   e.log.info(`Fallback model <provider>,<model> succeeded`)
#   e.log.warn(`Request failed for <scenario>, trying <N> fallback models`)
#   e.log.warn(`Fallback provider '<provider>' not found`)
#   e.log.error(`All fallback models failed for <scenario> <role>`)
#
# Verified in production logs (June 16-17 285MB log):
#   207 "Trying fallback model" / 203 "Fallback model X succeeded" / 4 "All failed"
#   Today (2026-06-27 11:54+): ZERO fallback events — primaries all succeeding.
#
# Usage:
#   . .\ccr-fallback-log.ps1              # tail today's CCR log, parse new lines
#   . .\ccr-fallback-log.ps1 -Last 1h     # show events from the last hour
#   . .\ccr-fallback-log.ps1 -Since "2026-06-27 11:00"  # since a timestamp
#   . .\ccr-fallback-log.ps1 -All         # parse all CCR logs ever (slow)
#   . .\ccr-fallback-log.ps1 -Watch       # live tail (Ctrl+C to stop)
#
# Output: stdout for human reading; ALSO appends one JSONL line per event to
# P:\.claude\logs\ccr-fallback.jsonl so production failures are auditable.
# No secrets handled. No processes killed. Read-only against CCR's log dir.
#
# Self-test: on every invocation, parses 5 hand-rolled fixture lines covering
# each fallback shape CCR emits. If any fixture fails to classify, exits 2
# BEFORE writing any JSONL. Catches regressions like the IndexOf overload bug
# that silently dropped every error-path event from 2026-06-27 onwards.

param(
    [string]$Since = "",
    [string]$Last = "",
    [switch]$All,
    [switch]$Watch
)

$ccrLogsDir = "$env:USERPROFILE\.claude-code-router\logs"
$outJsonl   = "P:\.claude\logs\ccr-fallback.jsonl"
$outDir     = Split-Path -Parent $outJsonl

if (-not (Test-Path $ccrLogsDir)) {
    Write-Warning "[ccr-fallback] CCR log dir not found: $ccrLogsDir"
    return
}

# --- Resolve which log file(s) to read ---
# CCR rotates logs by startup timestamp: ccr-YYYYMMDDhhmmss.log
# Active = newest. Pin to one file unless -All.
$logFiles = if ($All) {
    Get-ChildItem -Path $ccrLogsDir -Filter "ccr-*.log" | Sort-Object LastWriteTime -Descending
} else {
    Get-ChildItem -Path $ccrLogsDir -Filter "ccr-*.log" |
        Where-Object { $_.Name -notmatch '\.log\.txt$' } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

if (-not $logFiles) {
    Write-Warning "[ccr-fallback] No CCR log files found in $ccrLogsDir"
    return
}

# --- Time filter ---
$sinceMs = $null
if ($Last) {
    $delta = [TimeSpan]::FromMinutes(0)
    if ($Last -match '^(\d+)\s*(s|m|h|d)$') {
        $n = [int]$Matches[1]
        $unit = $Matches[2]
        $delta = switch ($unit) {
            's' { [TimeSpan]::FromSeconds($n) }
            'm' { [TimeSpan]::FromMinutes($n) }
            'h' { [TimeSpan]::FromHours($n) }
            'd' { [TimeSpan]::FromDays($n) }
        }
    } else {
        Write-Warning "[ccr-fallback] -Last expects '<n>s|m|h|d' (e.g. '1h', '30m'). Got: $Last"
        return
    }
    $sinceMs = [DateTimeOffset]::UtcNow.Subtract($delta).ToUnixTimeMilliseconds()
} elseif ($Since) {
    try {
        $sinceMs = [DateTimeOffset]::Parse($Since).ToUnixTimeMilliseconds()
    } catch {
        Write-Warning "[ccr-fallback] -Since parse failed: $Since (use ISO-8601, e.g. '2026-06-27 11:00')"
        return
    }
}

# --- Ensure output dir exists for the JSONL audit trail ---
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

# --- Parse pino JSON line, extract if it's a fallback event ---
function Test-FallbackLine {
    param([string]$Line)
    # Cheap pre-filter: only lines mentioning 'fallback' (case-insensitive) need parsing.
    # Uses IndexOf for speed on multi-MB logs.
    # Use 3-arg IndexOf(needle, startIndex, comparison) — the 2-arg overload
    # String.IndexOf(String, StringComparison) raises MethodCountCouldNotFindBest
    # in some PowerShell hosts, and ForEach-Object swallows the error silently,
    # causing every event to be dropped (2026-06-27 bug, 17/17 all-failed lost).
    if ($Line.IndexOf('allback', 0, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) { return $null }
    # Now parse: extract msg field. Use a simple state machine instead of regex
    # because nested JSON makes regex fragile and $Matches re-use is a footgun.
    $msgKey = '"msg":"'
    $idx = $Line.IndexOf($msgKey, 0, [System.StringComparison]::Ordinal)
    if ($idx -lt 0) { return $null }
    $start = $idx + $msgKey.Length
    $end = $Line.IndexOf('"', $start)
    if ($end -lt 0) { return $null }
    $msg = $Line.Substring($start, $end - $start)

    $kind = $null
    $model = ''
    if ($msg.StartsWith('Trying fallback model:')) {
        $kind = 'try'
        $model = $msg.Substring('Trying fallback model:'.Length).Trim()
    } elseif ($msg -match '^Fallback model (.+) succeeded$') {
        $kind = 'success'
        $model = $Matches[1]
    } elseif ($msg.StartsWith('Request failed for')) {
        $kind = 'fail-start'
    } elseif ($msg.StartsWith("Fallback provider '")) {
        $kind = 'provider-missing'
        $model = $msg
    } elseif ($msg.StartsWith('All fallback models failed')) {
        $kind = 'all-failed'
    }
    if (-not $kind) { return $null }
    return [PSCustomObject]@{ Kind = $kind; Model = $model; Msg = $msg }
}

# --- Extract timestamp from a pino JSON line without regex ---
function Get-PinoTimestamp {
    param([string]$Line)
    $key = '"time":'
    $idx = $Line.IndexOf($key, 0, [System.StringComparison]::Ordinal)
    if ($idx -lt 0) { return $null }
    $start = $idx + $key.Length
    $end = $start
    while ($end -lt $Line.Length -and $Line[$end] -match '\d') { $end++ }
    if ($end -eq $start) { return $null }
    $numStr = $Line.Substring($start, $end - $start)
    [long]$tsMs = 0
    if (-not [long]::TryParse($numStr, [ref]$tsMs)) { return $null }
    return $tsMs
}

# --- Process one file ---
function Read-LogEvents {
    param([System.IO.FileInfo]$File)
    $events = @()
    # Use ReadAllLines instead of Get-Content: in some PowerShell hosts,
    # Get-Content -ReadCount N yields only the first batch regardless of N
    # (verified 2026-06-27: 285MB log = 57381 lines, Get-Content returned 58).
    # ReadAllLines is also faster for one-shot full-file reads.
    [System.IO.File]::ReadAllLines($File.FullName) | ForEach-Object {
        $line = $_
        if (-not $line.StartsWith('{')) { return }
        $tsMs = Get-PinoTimestamp -Line $line
        if ($null -eq $tsMs) { return }
        if ($sinceMs -and $tsMs -lt $sinceMs) { return }
        $ev = Test-FallbackLine $line
        if ($ev) {
            $events += [PSCustomObject]@{
                ts     = ([DateTimeOffset]::FromUnixTimeMilliseconds($tsMs)).ToString('o')
                tsMs   = $tsMs
                kind   = $ev.Kind
                model  = $ev.Model
                msg    = $ev.Msg
                source = $File.Name
            }
        }
    }
    return $events
}

# --- Self-test: classify 5 fixture lines, one per CCR fallback shape. ---
# Runs on every invocation before any log file is read. If any fixture fails to
# classify, exits 2 BEFORE touching JSONL — catches parser regressions at the
# point of use, not at the next production incident. Catches the 2026-06-27
# IndexOf-overload class of bug (silent error swallow in pipeline).
$fixtures = @(
    @{ Line = '{"level":30,"time":1781712430375,"pid":39592,"hostname":"DESKTOP-70TFAGN","reqId":"req-i","msg":"Trying fallback model: zai,glm-4.7"}'; Expect = 'try' },
    @{ Line = '{"level":30,"time":1781712430375,"pid":39592,"hostname":"DESKTOP-70TFAGN","reqId":"req-i","msg":"Fallback model zai,glm-4.7 succeeded"}'; Expect = 'success' },
    @{ Line = '{"level":40,"time":1781712430375,"pid":39592,"hostname":"DESKTOP-70TFAGN","reqId":"req-i","msg":"Request failed for default, trying 4 fallback models"}'; Expect = 'fail-start' },
    @{ Line = '{"level":40,"time":1781712430375,"pid":39592,"hostname":"DESKTOP-70TFAGN","reqId":"req-i","msg":"Fallback provider ' + [char]39 + 'nonexistent' + [char]39 + ' not found"}'; Expect = 'provider-missing' },
    @{ Line = '{"level":50,"time":1781716932863,"pid":39592,"hostname":"DESKTOP-70TFAGN","reqId":"req-5f","msg":"All fallback models failed for default background"}'; Expect = 'all-failed' }
)
$selfTestFails = @()
foreach ($fx in $fixtures) {
    $got = Test-FallbackLine -Line $fx.Line
    if (-not $got -or $got.Kind -ne $fx.Expect) {
        $selfTestFails += [PSCustomObject]@{ Expected = $fx.Expect; Got = if ($got) { $got.Kind } else { '<null>' } }
    }
}
if ($selfTestFails.Count -gt 0) {
    [Console]::Error.WriteLine("[ccr-fallback] SELF-TEST FAILED - parser cannot classify " + $selfTestFails.Count + "/" + $fixtures.Count + " CCR fallback shapes.")
    foreach ($f in $selfTestFails) {
        [Console]::Error.WriteLine("  expected=" + $f.Expected + " got=" + $f.Got)
    }
    [Console]::Error.WriteLine("[ccr-fallback] Aborting before JSONL write to prevent silent data loss.")
    exit 2
}

Write-Host "[ccr-fallback] Scanning $($logFiles.Count) log file(s) in $ccrLogsDir" -ForegroundColor DarkGray
$allEvents = @()
foreach ($f in $logFiles) {
    $found = Read-LogEvents -File $f
    if ($found.Count -gt 0) {
        Write-Host "  $($f.Name): $($found.Count) fallback event(s)" -ForegroundColor DarkGray
        $allEvents += $found
    }
}

if ($allEvents.Count -eq 0) {
    Write-Host ""
    Write-Host "No fallback events found." -ForegroundColor Yellow
    if ($Last -or $Since) {
        Write-Host "  (filter: since=$Last$Since)" -ForegroundColor DarkGray
    } else {
        Write-Host "  (this is GOOD - primary models are succeeding)" -ForegroundColor DarkGray
    }
    return
}

# Sort by tsMs ascending (older logs first when -All)
$allEvents = $allEvents | Sort-Object tsMs

# --- Print to stdout (one line per event, simple concat for grep-ability) ---
Write-Host ""
Write-Host ("TIMESTAMP (UTC)".PadRight(25) + " " + "KIND".PadRight(15) + " DETAIL") -ForegroundColor Cyan
Write-Host ("-" * 80) -ForegroundColor DarkGray
foreach ($e in $allEvents) {
    Write-Host ($e.ts.PadRight(25) + " " + $e.kind.PadRight(15) + " " + $e.msg)
}

# --- Append to JSONL audit trail (so production failures are auditable later) ---
$allEvents | ForEach-Object {
    [PSCustomObject]@{
        ts     = $_.ts
        kind   = $_.kind
        model  = $_.model
        msg    = $_.msg
        source = $_.source
    } | ConvertTo-Json -Compress
} | Add-Content -Path $outJsonl -Encoding UTF8

Write-Host ""
Write-Host "[ccr-fallback] $($allEvents.Count) event(s) appended to $outJsonl" -ForegroundColor DarkGray

# --- Optional: live tail mode ---
if ($Watch) {
    Write-Host ""
    Write-Host "[ccr-fallback] Watching for new events (Ctrl+C to stop)..." -ForegroundColor Cyan
    $active = $logFiles | Select-Object -First 1
    $lastSize = (Get-Item $active.FullName).Length
    while ($true) {
        Start-Sleep -Seconds 2
        $cur = (Get-Item $active.FullName).Length
        if ($cur -le $lastSize) { continue }
        # New bytes appended; read the delta
        $stream = [System.IO.File]::Open($active.FullName, 'Open', 'Read', 'ReadWrite', 'None')
        $stream.Seek($lastSize, 'Begin') | Out-Null
        $reader = New-Object System.IO.StreamReader($stream)
        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()
            $ev = Test-FallbackLine $line
            if ($ev) {
                if ($line -match '"time":(\d+)') {
                    $ts = ([DateTimeOffset]::FromUnixTimeMilliseconds([long]$Matches[1])).ToString('o')
                } else { $ts = (Get-Date).ToString('o') }
                Write-Host ($ts.PadRight(25) + " " + $ev.Kind.PadRight(15) + " " + $ev.Msg) -ForegroundColor Yellow
            }
        }
        $reader.Close(); $stream.Close()
        $lastSize = $cur
    }
}