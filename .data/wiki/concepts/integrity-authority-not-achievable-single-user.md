---
title: "INTEGRITY_AUTHORITY not achievable on single-user Windows without external infrastructure"
created: 2026-07-24
source: session-2026-07-24
tags: [identity, integrity, authority, windows, security, verification]
summary: >
  The model shares the same Windows user identity as the hook process. Every file
  and cryptographic key accessible to the hook is accessible to the model via 10+
  write vectors. HMAC with file-stored keys provides zero boundary. INTEGRITY_AUTHORITY
  requires external protected infrastructure (branch-protected remote or external
  signing service). RELIABILITY_AUTHORITY is the achievable level on this host.
agent: grok
host: grok
cognitive_load: 1
verification: single-source-verified
---

# INTEGRITY_AUTHORITY not achievable on single-user Windows

## The boundary problem

On a single-user Windows 11 host where the AI agent and the hook process run as
the same user:

- **No OS-level file boundary exists.** Every path under the user's home directory
  is writable by both the agent (via `Set-Content`, `Out-File`, `Copy-Item`,
  `Move-Item`, `cmd /c echo`, Python `open().write()`, `os.replace`, `Remove-Item`,
  parent-dir rename) and the hook.
- **HMAC with file-stored keys is forgeable.** The model reads the key file and
  produces validly-signed forged records (proven 2026-07-24).
- **`C:\Windows\System32` is denied** for both agent and hook — no asymmetric
  boundary exists between them.

## Achievable levels

| Level | Description | Achievable on this host? |
|---|---|---|
| INTEGRITY_AUTHORITY | Model cannot produce a forged valid record | ❌ No — requires external infra |
| RELIABILITY_AUTHORITY | Structured state that workflow checks consume; tampering detectable in review | ✅ Yes |

## Path to INTEGRITY_AUTHORITY

External infrastructure not present:
- Protected git remote (branch protection prevents force-push)
- External signing service the model cannot call
- Separate Windows principal with different ACLs

This is a deployment decision, not a code decision.

## Falsifier

If a Windows ACL configuration or separate-principal hook runner is deployed that
creates an asymmetric file boundary between the agent and the hook, INTEGRITY_AUTHORITY
becomes achievable and this concept should be superseded.

## Related

- [[host-metadata-not-authoritative-for-identity]]
- [[external-state-cross-check-as-structural-fix]]
- [[best-practices-enforcement-mechanism-grok-build]]
