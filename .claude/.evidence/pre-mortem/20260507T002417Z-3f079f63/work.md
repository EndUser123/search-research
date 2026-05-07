csf/nlm_exporter.py profile bypass (TASK-007 composite exporter)

TARGET: P:/packages/yt-is/csf/nlm_exporter.py

AUDIT FINDING: Lines 257-268 use raw subprocess.run + shutil.which('nlm') without --profile pinning.

Before (broken):
  nlm_path = shutil.which('nlm')
  cmd = [nlm_path, 'source', 'add', doc.notebook_id, '--text', str(tmp_path)]
  result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

After (fixed):
  from csf import nlm_auth_guard
  cmd_args = nlm_auth_guard.add_profile_args(['source', 'add', doc.notebook_id, '--text', str(tmp_path)])
  result = nlm_auth_guard.run_nlm(cmd_args, timeout_s=300)

Same failure class as the nlm_scraper.py bug that caused PERMISSION_DENIED. The nlm_scraper.py
was already fixed to use add_profile_args() + run_nlm().

Test gap: tests/test_nlm_exporter.py mocks subprocess.run and shutil.which directly, so they
pass without proving profile pinning contract.

Module docstring:
  Composite batching algorithm:
  - Group by channel → sort by published_at ASC (null-safe)
  - Split into chunks of ≤500K words AND ≤300 videos
  - Atomic write + idempotent export via nlm_export_state table
  Concurrency: Uses InterProcessLock for multi-terminal safety (FM-010).
  Atomicity: temp file → API call → rename in same BEGIN IMMEDIATE transaction (DD-007).
