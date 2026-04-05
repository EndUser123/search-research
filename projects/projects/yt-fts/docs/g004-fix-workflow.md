# G004 Logging F-String Fix Workflow (PARALLEL)

## Overview
Fix 120 G004 logging f-string issues across 16 files using 3 LLMs in PARALLEL.
Each LLM works on disjoint directories - NO merge conflicts possible.

## Parallel Strategy: Directory-Based Distribution

### Group 1: Qwen - services/ + llm/ (~39 issues)
| File | Issues | Path |
|------|--------|------|
| metadata_backfill_api.py | 32 | src/yt_fts/services/metadata_backfill_api.py |
| metadata_backfill.py | 2 | src/yt_fts/services/metadata_backfill.py |
| channel_service.py | 8 | src/yt_fts/services/channel_service.py |
| unified_error_handler.py | 15 | src/yt_fts/services/unified_error_handler.py |
| auto_embeddings.py | 4 | src/yt_fts/llm/auto_embeddings.py |

### Group 2: Gemini - download/ (~38 issues)
| File | Issues | Path |
|------|--------|------|
| download_handler.py | 16 | src/yt_fts/download/download_handler.py |
| unified_discovery.py | 10 | src/yt_fts/download/unified_discovery.py |
| batch_downloader.py | 6 | src/yt_fts/download/batch_downloader.py |
| rate_limit_tracker.py | 4 | src/yt_fts/download/rate_limit_tracker.py |
| progress_coordinator.py | 1 | src/yt_fts/download/progress_coordinator.py |
| logging_integration.py | 1 | src/yt_fts/download/logging_integration.py |

### Group 3: Codex - display/ + root files (~43 issues)
| File | Issues | Path |
|------|--------|------|
| display/discovery.py | 8 | src/yt_fts/display/discovery.py |
| auth.py | 6 | src/yt_fts/auth.py |
| utils/config.py | 5 | src/yt_fts/utils/config.py |
| transcribe/official_engine.py | 1 | src/yt_fts/transcribe/official_engine.py |
| core/watch.py | 1 | src/yt_fts/core/watch.py |

## Parallel Execution (Run All 3 at Once)

```bash
# Terminal 1 - Qwen (services/)
cd P:/__csf.nip
python src/commands/co/llm_cli.py --qwen-only "
Fix G004 logging f-strings in P:/projects/yt-fts/src/yt_fts/services/ and P:/projects/yt-fts/src/yt_fts/llm/
Replace logger.info(f'...') with logger.info('... %%s', var)
Replace logger.error(f'...') with logger.error('... %%s', var)
Replace logger.warning(f'...') with logger.warning('... %%s', var)
Replace logger.debug(f'...') with logger.debug('... %%s', var)

Return ONLY complete modified file contents in code blocks. NO explanations.
" 2>&1 | tee /tmp/qwen_output.txt

# Terminal 2 - Gemini (download/)
cd P:/__csf.nip
python src/commands/co/llm_cli.py --gemini-only "
Fix G004 logging f-strings in P:/projects/yt-fts/src/yt_fts/download/
Replace logger.info(f'...') with logger.info('... %%s', var)
etc.

Return ONLY complete modified file contents in code blocks. NO explanations.
" 2>&1 | tee /tmp/gemini_output.txt

# Terminal 3 - Codex (display/ + root)
cd P:/__csf.nip
python src/commands/co/llm_cli.py --codex-only "
Fix G004 logging f-strings in:
- P:/projects/yt-fts/src/yt_fts/display/discovery.py
- P:/projects/yt-fts/src/yt_fts/auth.py
- P:/projects/yt-fts/src/yt_fts/utils/config.py
- P:/projects/yt-fts/src/yt_fts/transcribe/official_engine.py
- P:/projects/yt-fts/src/yt_fts/core/watch.py

Replace logger.info(f'...') with logger.info('... %%s', var)
etc.

Return ONLY complete modified file contents in code blocks. NO explanations.
" 2>&1 | tee /tmp/codex_output.txt
```

## Alternative: PowerShell Background Jobs

```powershell
# Run all 3 in parallel, collect results
$job1 = Start-Job -ScriptBlock {
    cd P:\__csf.nip
    python src/commands/co/llm_cli.py --qwen-only "Fix G004 logging f-strings in P:/projects/yt-fts/src/yt_fts/services/ and P:/projects/yt-fts/src/yt_fts/llm/. Replace logger.info(f'...') with logger.info('... %%s', var). Return ONLY modified file contents."
}

$job2 = Start-Job -ScriptBlock {
    cd P:\__csf.nip
    python src/commands/co/llm_cli.py --gemini-only "Fix G004 logging f-strings in P:/projects/yt-fts/src/yt_fts/download/. Replace logger.info(f'...') with logger.info('... %%s', var). Return ONLY modified file contents."
}

$job3 = Start-Job -ScriptBlock {
    cd P:\__csf.nip
    python src/commands/co/llm_cli.py --codex-only "Fix G004 in P:/projects/yt-fts/src/yt_fts/display/discovery.py, auth.py, utils/config.py, transcribe/official_engine.py, core/watch.py. Replace logger.info(f'...') with logger.info('... %%s', var). Return ONLY modified file contents."
}

# Wait for all and get results
Receive-Job -Job $job1
Receive-Job -Job $job2
Receive-Job -Job $job3
```

## Apply Results

After all 3 complete:
1. Extract code blocks from each output
2. Write to respective files
3. Verify: `python -m ruff check src/yt_fts/ --select G004 --statistics`

## Tracking

| LLM | Directories | Issues | Status |
|-----|-------------|--------|--------|
| Qwen | services/, llm/ | 39 | pending |
| Gemini | download/ | 38 | pending |
| Codex | display/, auth.py, utils/, transcribe/, core/ | 43 | pending |
| **Total** | **disjoint** | **120** | - |

## Why This Works

1. **No overlapping files** - each LLM gets unique directories
2. **No merge conflicts** - changes are in separate files
3. **Independent verification** - can verify each group separately
4. **Rollback safety** - git checkout specific files if needed
