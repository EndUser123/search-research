Round-robin batch scheduler implementation for 429-resilient YouTube transcript downloads.

Target modules:
- P:/packages/intelligence-stream/csf/batch_scheduler.py (new module, BatchScheduler class)
- P:/packages/intelligence-stream/csf/transcript.py (cross-terminal cooldown integration)
- P:/packages/intelligence-stream/csf/batch.py (analyze_videos_round_robin function, cmd_sync wiring)
- P:/packages/intelligence-stream/csf/batch_status.py (schema migration for new tables)
- P:/packages/intelligence-stream/tests/test_batch_scheduler.py (13 tests, all passing)

Key design decisions:
- Round-robin across channels using itertools.cycle removed (manual channel cycling instead)
- Persistent download_archive table with PRIMARY KEY on video_id
- channel_cooldown table with source PRIMARY KEY, cooldown_until as REAL unix timestamp
- EXCLUSIVE transactions for archive writes to prevent inter-process races
- Jitter 2-10s between yields
- 30-min stale attempting recovery on startup
- Cross-terminal cooldown via BatchScheduler().record_429(channel_url) called from transcript.py
- archive_finalize called by batch.py workers after each completion
- yield_next skips archived videos (success/failed/attempting) and cooldown channels
