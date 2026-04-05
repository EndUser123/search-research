# Semantic Daemon Mutex Recovery

## Problem

If the semantic daemon startup mutex gets stuck (e.g., daemon crashes while holding mutex), all terminals will hang waiting for the lock.

## Mutex Name

```
Global\CSF_NIP_SemanticDaemon_Startup
```

The `Global\` prefix ensures the mutex works across all terminals and sessions on Windows.

## Symptoms

- Multiple terminals hang on session startup
- Error: "Timeout waiting for daemon startup lock (10000ms)"
- New Claude sessions won't start

## Recovery Steps

### Option 1: Check if Mutex is Actually Held

Run PowerShell as Administrator:
```powershell
# Check for mutex handles (requires Sysinternals Handle)
handle.exe -a "CSF_NIP_SemanticDaemon_Startup"
```

If no handles are found, the mutex is not actually held - the issue is elsewhere.

### Option 2: Force Kill Stale Daemon Processes

```powershell
# Kill all pythonw.exe processes (daemon)
Stop-Process -Name "pythonw" -Force

# Remove stale PID file
Remove-Item "P:\__csf\data\semantic_daemon.pid" -Force -ErrorAction SilentlyContinue

# Restart daemon by starting new Claude session
```

### Option 3: System Cleanup (Last Resort)

```powershell
# Kill all Python processes
Stop-Process -Name "python*" -Force

# Remove all mutex-related state
Remove-Item "P:\__csf\data\semantic_daemon.pid" -Force -ErrorAction SilentlyContinue

# Reboot system (clears all kernel objects)
Restart-Computer
```

## Prevention

The hook now includes:
- **Logging**: Mutex acquisition/release logged to `daemon_startup` logger
- **Process verification**: Checks spawned process is actually running before releasing mutex
- **Atomic PID write**: Temp file + rename prevents partial writes

## Log Location

Check hook logs for mutex events:
```bash
# Logs are written to stderr during hook execution
# Look for:
# - "Acquiring mutex 'Global\CSF_NIP_SemanticDaemon_Startup'"
# - "Mutex acquired, proceeding with daemon startup"
# - "Mutex 'Global\CSF_NIP_SemanticDaemon_Startup' released"
```

## Related Files

- Hook: `P:\.claude\hooks\SessionStart_semantic_daemon.py`
- PID file: `P:\__csf\data\semantic_daemon.pid`
- Daemon: `P:\__csf\src\daemons\unified_semantic_daemon.py`
