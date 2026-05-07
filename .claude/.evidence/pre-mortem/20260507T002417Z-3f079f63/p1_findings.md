# Phase 1 Findings

## Triage Classification
code — Python module (`csf/nlm_exporter.py`) with a confirmed profile-pinning bypass in the `export_composite()` function.

## Dispatched Specialists
- **adversarial-security**: data access, auth bypass, credential exposure
- **adversarial-quality**: maintainability, tech debt, error handling
- **adversarial-logic**: off-by-one, wrong operators, state transitions
- **adversarial-testing**: test coverage gaps, brittle tests, missing scenarios

## Specialist Findings Summary

### adversarial-security
**Domain:** Auth bypass, credential exposure, access control violations
**Key findings:**
- [CRITICAL] export_composite() lines 257-268 bypass nlm_auth_guard entirely — raw shutil.which + subprocess.run with no --profile. Same failure class as nlm_scraper.py PERMISSION_DENIED (security:1)
- [HIGH] test_nlm_exporter.py mocks subprocess.run and shutil.which directly — tests pass without proving --profile is passed (security:2)

### adversarial-quality
**Domain:** Maintainability, tech debt, error handling, structural quality
**Key findings:**
- [HIGH] export_composite() missing profile pinning — same pattern as nlm_scraper PERMISSION_DENIED (quality:1)
- [HIGH] Tests mock subprocess-level, masking profile contract — zero verification that --profile appears in cmd list (quality:2)
- [MEDIUM] Bare except Exception at line 308 silently swallows error categories — identical logs for disk-full, network timeout, db lock (quality:3)
- [MEDIUM] notebook_id not validated for null/empty — could produce blank composite IDs and markdown injection (quality:4)
- [LOW] _DEFAULT_EXPORTS_DIR hardcoded with no env var override — P-drive path non-portable (quality:5)

### adversarial-logic
**Domain:** Control flow, conditions, state transitions, edge cases
**Key findings:**
- [BLOCKER] Lines 257-268 raw subprocess.run — profile-pinning layer bypassed entirely (logic:1)
- [HIGH] Tests mock at subprocess level — profile contract unverifiable, any regression silent (logic:2)
- [MEDIUM] export_composite idempotency checks nlm_source_id + content_hash but not notebook_id — stale source_id returned for wrong notebook (logic:3)
- [MEDIUM] _parse_nlm_output returns None silently on malformed stdout — None propagates to DB as NULL source_id (logic:4)

### adversarial-testing
**Domain:** Test coverage, assertion quality, integration gaps
**Key findings:**
- [HIGH] export_composite profile bypass confirmed — same failure class as fixed nlm_scraper (test:1)
- [HIGH] test_export_composite_re_export_on_hash_mismatch has zero assertions after calling export_composite — always passes (test:2)
- [MEDIUM] Over-mocking at subprocess level — tests prove nothing about profile contract (test:3)
- [MEDIUM] _parse_nlm_output has no dedicated tests — critical path, silent None return, no coverage (test:4)
- [LOW] test_export_composite_no_tmp_file_after_success — rename assertion checks len() only, not dst argument (test:5)

## Consolidated Findings

### 1. Logical Gaps & Inconsistencies
1.1. [BLOCKER] (source: adversarial-security, adversarial-logic) — export_composite() lines 257-268 use raw subprocess.run + shutil.which('nlm') without --profile pinning. The nlm_auth_guard profile-pinning layer is bypassed entirely. This is the same failure class that caused PERMISSION_DENIED in nlm_scraper.py (csf/nlm_exporter.py:257-268)

1.2. [MEDIUM] (source: adversarial-logic) — export_composite idempotency check (lines 234-243) validates nlm_source_id + content_hash but never checks that doc.notebook_id matches the stored notebook_id. If nlm_source_id is notebook-scoped, returning a stale source_id and proceeding to upsert_nlm_export_state would corrupt DB state — the composite claimed to be in notebook B but actually lives in notebook A. (csf/nlm_exporter.py:234-243)

1.3. [MEDIUM] (source: adversarial-logic, adversarial-quality) — _parse_nlm_output returns None silently when nlm stdout is malformed (no JSON, no 'Source added:' prefix, no 8+ char token). None propagates to source_id on line 280, which is persisted as nlm_source_id=NULL in the DB on line 292. This produces duplicate NotebookLM sources on retry. (csf/nlm_exporter.py:323-353, 280, 292)

### 2. Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-quality) — notebook_id parameter is not validated despite being used in composite_id hashing (SHA-256), markdown content generation, and CLI argument passing. Empty notebook_id silently produces blank headings and duplicate composite_ids. An adversarial notebook_id with newlines could inject spurious markdown sections. (csf/nlm_exporter.py:73-76, 171, 175)

2.2. [MEDIUM] (source: adversarial-quality) — Bare except Exception at line 308 catches all errors identically — disk-full, network timeout, db lock, and type errors produce identical log messages. Debugging requires manual exception classification. (csf/nlm_exporter.py:308)

2.3. [LOW] (source: adversarial-quality) — _DEFAULT_EXPORTS_DIR hardcoded as `Path("P:\\.data/yt-is/nlm_exports")` with no environment variable override, unlike nlm_auth_guard which reads multiple env vars. Non-portable deployment on non-P-drive systems. (csf/nlm_exporter.py:22)

### 3. Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-security, adversarial-quality, adversarial-logic, adversarial-testing) — Test suite masks the profile pinning gap. Every test in test_nlm_exporter.py that exercises export_composite mocks subprocess.run and shutil.which directly — they pass 100% without ever proving that --profile is passed to the nlm subprocess. The profile-pinning contract is unverifiable from the current test suite. (tests/test_nlm_exporter.py:235-237, 271, 309-312)

3.2. [HIGH] (source: adversarial-testing) — test_export_composite_re_export_on_hash_mismatch has zero assertions after calling export_composite. The test always passes regardless of whether re-export actually happens. Comment '# Should not return old nlm_source_id (re-export attempted)' is documentation, not an assertion. (tests/test_nlm_exporter.py:242)

3.3. [MEDIUM] (source: adversarial-testing) — _parse_nlm_output has no dedicated tests. It has three parsing strategies (JSON, 'Source added:' prefix, bare ID) with no coverage. A format change in NotebookLM CLI output would silently fall back to stale source_id or None. (tests/test_nlm_exporter.py — no test for _parse_nlm_output)

### 4. Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-logic) — Are NotebookLM nlm_source_id values globally unique or notebook-scoped? If notebook-scoped, finding 1.2 (notebook_id mismatch in idempotency check) is a correctness bug causing corrupt DB state. If globally unique, finding 1.2 is a non-issue.

4.2. [LOW] (source: adversarial-testing) — test_export_composite_no_tmp_file_after_success asserts len(rename_called) > 0 but never checks the dst argument value. A broken rename pointing to .tmp.2 instead of .txt would still pass. (tests/test_nlm_exporter.py:317)

### 5. Concrete Recommendations
5.1. Replace lines 256-268 with nlm_auth_guard wrapper (matching nlm_scraper.py fix):
   ```python
   from csf import nlm_auth_guard
   cmd_args = nlm_auth_guard.add_profile_args(['source', 'add', doc.notebook_id, '--text', str(tmp_path)])
   result = nlm_auth_guard.run_nlm(cmd_args, timeout_s=300)
   ```
   (source: adversarial-security:1, adversarial-logic:1, adversarial-testing:1)

5.2. Add notebook_id validation at export_composite entry point:
   ```python
   if not doc.notebook_id:
       raise ValueError("notebook_id must be a non-empty string")
   ```
   (source: adversarial-quality:4)

5.3. Add notebook_id mismatch check in idempotency:
   ```python
   if existing['notebook_id'] != doc.notebook_id:
       logger.warning('notebook_id mismatch for %s — forcing re-export', doc.composite_id)
   ```
   (source: adversarial-logic:3)

5.4. Fail closed when _parse_nlm_output returns None:
   ```python
   if source_id is None:
       logger.error('Failed to parse nlm source_id from stdout: %r', result.stdout)
       _cleanup_tmp(tmp_path)
       return None
   ```
   (source: adversarial-logic:4)

5.5. Replace bare except Exception with specific handlers (source: adversarial-quality:3)

5.6. Add env var override for exports directory (source: adversarial-quality:5)

### 6. Open Questions / Unknowns
6.1. [MEDIUM] (source: adversarial-logic) — Are NotebookLM nlm_source_id values globally unique or notebook-scoped? If notebook-scoped, LOGIC-003 (notebook_id mismatch) is a correctness bug. Verify against NotebookLM API documentation or by testing cross-notebook source reuse.

6.2. [MEDIUM] (source: adversarial-logic) — Does `nlm source add` accept `--profile` on the source add subcommand, or does `--profile` only apply to login/check-status? The add_profile_args call would inject --profile for all non-login commands including source add, but this hasn't been verified against the actual nlm CLI --help output.

6.3. [LOW] (source: adversarial-testing) — _DEFAULT_EXPORTS_DIR path may conflict with concurrent export_composite calls if multiple processes write to the same exports directory without process-level locking. InterProcessLock is used at a higher level (module docstring references FM-010) but the export_composite function itself has no lock.