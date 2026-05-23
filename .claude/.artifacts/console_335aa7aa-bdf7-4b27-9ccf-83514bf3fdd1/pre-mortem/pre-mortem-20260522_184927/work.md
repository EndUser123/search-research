Review targets:
1. P:/.claude/provider-configs/cc-bifrost.ps1 - Bifrost v1.5.2 PowerShell wrapper (routing, daemon management, --sync)
2. P:/.claude/provider-configs/bifrost_configured_providers.md - Provider + routing rules documentation

Focus areas:
- Routing correctness (CEL expressions, provider names, priority ordering)
- Daemon management (PID tracking, job vs process dual-mode, restart/bootstrap behavior)
- --sync clean_sync (provider validation, backup, write safety)
- Error handling (network probes, missing binaries, stale PID files)
- Security (.env loading, hardcoded tokens, path injection)