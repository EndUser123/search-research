# ADR-20260328: Transcript Cache Encryption — Accepted Risk

**Status**: Accepted
**Date**: 2026-03-28
**Source**: `premortem_intelligence_stream_batch_20260328.md` (SEC-002)

## Context

The adversarial security review identified that `transcript_cache` stores YouTube transcripts in plaintext SQLite (SEC-002, severity HIGH). The recommendation was to encrypt the SQLite database using Fernet or similar application-level encryption.

## Decision

**Accepted risk: no encryption for transcript cache.**

## Rationale

YouTube transcripts are **publicly available content** — they are readable by anyone with the video URL. Encrypting them at rest provides no meaningful confidentiality protection because:

1. **Threat model mismatch**: The attack vector is unauthorized filesystem access. If an attacker has filesystem access to `P:/__csf/.data/intelligence-stream/transcripts/transcripts.sqlite`, they can also access the encryption key stored alongside it (or in environment variables), rendering encryption moot without a key management system (KMS).

2. **No sensitive content**: Transcripts are not credentials, API keys, PII, or regulatory-controlled data. GDPR Article 32 compliance for "encryption at rest" applies to personal data — YouTube video transcripts are not personal data unless they contain identifying information about video subjects.

3. **Performance cost**: Fernet encryption/decryption adds per-read and per-write overhead to every cache access. For a cache that is read hundreds of times per batch run, this adds measurable latency without security benefit.

4. **Filesystem permissions are the real control**: The `P:/__csf/.data/` directory should have filesystem-level access controls restricting who can read it. That is the actual security boundary.

## Conditions for Reconsideration

If any of the following become true, re-evaluate:
- transcripts are enriched with PII or user-generated content
- transcripts are stored in a shared/network filesystem with weaker access controls
- regulatory framework requires encryption at rest for this data class

## Alternative Mitigations (Implemented)

- **TERMINAL_ID validation** (SEC-003): Prevents audit trail spoofing
- **WAL checkpointing** (SEC-004): Reduces uncommitted data exposure window
- **Content hash in cache key** (SEC-005): Prevents cache poisoning from concurrent writes

## See Also

- `premortem_intelligence_stream_batch_20260328.md` — SEC-002 finding
- `csf/cache.py` — transcript cache implementation
