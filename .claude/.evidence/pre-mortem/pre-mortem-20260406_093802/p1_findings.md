## Triage Classification
code — Python module  with three chain strategies, SentenceTransformer fallback, and TTL cache eviction

## Dispatched Specialists
- adversarial-logic: Pure logic correctness — conditionals, operators, edge cases
- adversarial-performance: Performance — cold start penalty, batch encoding, TTL efficiency
- adversarial-io-validation: I/O validation — path existence, file access, external calls
- adversarial-quality: Tech debt — threshold mismatch, bare excepts, naming
- adversarial-testing: Test coverage — missing coverage for semantic chain, TTL cache, fallback path

## Specialist Findings Summary

### adversarial-logic
**Domain:** ?
- **[MEDIUM]** no title core/session_chain.py:471 vs 483

### adversarial-performance
**Domain:** ?
- **[CRITICAL]** FileLock timeout silently swallowed — returns empty results instead of surfacing failure 
  - In all three CHS providers (claude_code_raw.py:228, claude_log.py:219, codex_desktop.py:169), the FileLock acquisition is inside a try block that ends with `except Exception: pass`. When _LOCK_TIMEOUT (30s) expires, filelock.Timeout is raised, caught by the bare except, and the function returns an empty list. Callers receive zero events with no indication that lock contention caused data loss.
- **[MEDIUM]** write_watermark has no try/except around FileLock — timeout propagates as unhandled exception 
  - In archive.py:105, write_watermark uses `with FileLock(lock_path, timeout=_LOCK_TIMEOUT):` with NO surrounding try/except. If the lock cannot be acquired within 30s, the filelock.Timeout exception propagates unhandled. This is inconsistent with the provider pattern (which swallows timeouts silently) and can crash callers that don't handle it.
- **[LOW]** TOCTOU race in _stale_lock_recovery before FileLock acquisition 
  - All four FileLock usages call _stale_lock_recovery(lock_path) immediately before acquiring the lock. The sequence is: (1) check if lock file exists and is stale, (2) delete it if so, (3) acquire lock. Between steps 1-2 and step 3, another process could: (a) acquire the lock we just marked as stale, or (b) another process could be in its own stale check at the same time, leading to both deleting the same lock and both trying to acquire it simultaneously.
- **[LOW]** SentenceTransformer fallback in walk_semantic_chain has 60-second cold load penalty 
  - In session_chain.py:548-558, when the embedding daemon is unavailable or returns near-zero vectors, the code falls back to loading SentenceTransformer directly via `_get_st_model()`. The _get_st_model() function loads 'all-MiniLM-L6-v2' which has a documented ~60s cold-start time (line 40-41 comment: '~60s cold start'). This means the semantic chain walk could block for 60 seconds before returning any results.

### adversarial-io-validation
**Domain:** ?
- **[HIGH]** no title core/session_chain.py:108-129 (_get_prior_transcript_path)
- **[HIGH]** no title core/session_chain.py:132-146 (_find_handoff_referencing)
- **[HIGH]** no title core/session_chain.py:121-125
- **[MEDIUM]** no title core/session_chain.py:238-260 (load_sessions_index)
- **[HIGH]** no title core/session_chain.py:263-290 (_extract_first_user_message)
- **[HIGH]** no title core/session_chain.py:38-61 (_get_st_model) and lines 546-558
- **[HIGH]** no title core/session_chain.py:542-543
- **[MEDIUM]** no title core/session_chain.py:552-555
- **[MEDIUM]** no title core/session_chain.py:471 (threshold default) vs docstring line 483
- **[MEDIUM]** no title core/session_chain.py:149-154 (_resolve_transcript_path)

### adversarial-quality
**Domain:** ?
- **[MEDIUM]** Inconsistent threshold: docstring says 0.7, parameter default is 0.5 
  - walk_semantic_chain has a parameter threshold with a default of 0.5 but the docstring at line 483-484 states '(default 0.7)'. A developer relying on the docstring would expect 0.7 but get 0.5 behavior.
- **[HIGH]** Semantic chain strategy ignores newest_first parameter and produces inconsistent ordering 
  - walk_semantic_chain does not reverse entries when newest_first=True, unlike walk_handoff_chain and walk_sessions_index_chain which do. Additionally, the check at line 651 'semantic_result.entries[0].session_id != session_id' is always True for semantic chains since the target session is never included in semantic results. This means the semantic chain always bypasses the newest_first logic entirely.
- **[MEDIUM]** Bare except: clauses mask errors silently 
  - Three bare 'except:' clauses exist in the module. At line 548, an exception from embed_texts or np.frombuffer is caught and triggers SentenceTransformer fallback. At lines 556 and 558, exceptions from model.encode are caught and return empty results. Bare except: can mask programming errors (e.g., KeyboardInterrupt, SystemExit, AttributeError on None) and make debugging difficult.
- **[MEDIUM]** st_birthtime unavailable on Windows — fallback uses st_ctime which is not session birthtime 
  - At lines 338-341, the code checks for st_birthtime (session creation time, Python 3.12+ on some platforms) and falls back to st_ctime on older Python or Windows. On Windows, st_ctime is the file metadata change time, NOT the session creation time. For sessions-index entries without createdAt, this means mtime-based chain ordering could be incorrect on Windows.
- **[LOW]** Double-negative session_id comparison in walk_session_chain is confusing 
  - The checks at lines 637 and 644 use 'entries[0].session_id != session_id' to determine if a prior session was found. This double-negative pattern (checking if first entry is NOT the target to confirm a chain exists) is non-obvious. A reader expects a positive check like 'origin_session_id is not None'.

### adversarial-testing
**Domain:** ?
- **[HIGH]** Semantic chain strategy (Strategy 3) has ZERO test coverage 
  - _session_text, walk_semantic_chain, _cosine_sim, and _get_st_model are completely untested. Strategy 3 is the fallback for ALL post-March 19 2026 sessions (which have no handoff files). Any regression in the semantic chain path will go undetected.
- **[HIGH]** Threshold default mismatch between docstring and function signature 
  - walk_semantic_chain docstring states default threshold=0.7 but function signature and work.md both state threshold=0.5. This is a documentation-code mismatch that could cause confusion during debugging.
- **[HIGH]** _get_st_model TTL cache eviction has zero test coverage 
  - The module-level SentenceTransformer cache with 5-minute TTL eviction (_st_model, _st_model_last_used, _ST_MODEL_TTL_SECONDS) is not tested. If the eviction logic breaks (e.g., time comparison bug, reference leak), the model stays loaded indefinitely causing memory growth.
- **[MEDIUM]** No integration tests for walk_session_chain unified entry point 
  - walk_session_chain (line 607) is the public API that tries three strategies in sequence, but only a single 'unknown session returns empty' test exists. The strategy selection logic, fallback chains, and newest_first reversal are untested.
- **[MEDIUM]** _session_text extraction has no edge case tests 
  - _session_text (line 438) handles goal, lastPrompt, summary, active_files fields. No tests verify: (1) all fields empty→empty string returned, (2) goal='test' but lastPrompt='', summary='summ'→goal takes precedence (correct), (3) active_files truncation at 10 items.
- **[MEDIUM]** EmbedClient→SentenceTransformer fallback path not tested 
  - walk_semantic_chain (lines 545-558) has two fallback layers: (1) EmbedClient daemon, (2) direct SentenceTransformer. The near-zero vector detection (line 546: norm < 0.01) and the exception catch (lines 548, 556) are not exercised. Production could silently fall through without either embedding method succeeding.
- **[LOW]** walk_sessions_index_chain chain direction ambiguity 
  - walk_sessions_index_chain builds the chain by walking backward (newest to oldest) then reverses at line 407. The parent_transcript_path assignment at lines 413-415 uses post-reversal indices. This is correct (oldest→newest after reversal, parent is previous in list) but has no test verifying the parent links are actually correct after reversal.

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] Semantic chain strategy (Strategy 3) has ZERO test coverage (source: adversarial-testing)
1.2. [HIGH] Threshold default mismatch: docstring says 0.7, parameter default is 0.5 (source: adversarial-quality)
1.3. [HIGH] _get_st_model TTL cache eviction has zero test coverage (source: adversarial-testing)
1.4. [HIGH] Semantic chain strategy ignores newest_first parameter (source: adversarial-quality)

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] Inconsistent threshold: docstring says 0.7, parameter default is 0.5 (source: adversarial-quality)
2.2. [MEDIUM] Bare except: clauses mask errors silently (source: adversarial-quality)
2.3. [MEDIUM] st_birthtime unavailable on Windows — fallback uses st_ctime which is not session birth (source: adversarial-quality)

### Missing Obvious Actions / Best Practices
1.5. [HIGH] _session_text extraction — no edge case tests (source: adversarial-testing)
1.6. [HIGH] EmbedClient→SentenceTransformer fallback path not tested (source: adversarial-testing)
1.7. [HIGH] FileLock timeout silently swallowed — returns empty results instead of surfacing (source: adversarial-performance:534)
1.8. [HIGH] No integration tests for walk_session_chain unified entry point (source: adversarial-testing)

### Risks and Edge Cases
2.4. [MEDIUM] write_watermark has no try/except around FileLock — timeout propagates as unhandled (source: adversarial-performance:534)
2.5. [MEDIUM] walk_sessions_index_chain chain direction ambiguity (source: adversarial-testing)
2.6. [MEDIUM] SentenceTransformer fallback in walk_semantic_chain has 60-second cold load penalty (source: adversarial-performance)
2.7. [MEDIUM] Double-negative session_id comparison in walk_session_chain is confusing (source: adversarial-quality)
2.8. [MEDIUM] TOCTOU race in _stale_lock_recovery before FileLock acquisition (source: adversarial-performance)
3.1. [LOW] SentenceTransformer fallback has 60-second cold load penalty (per-call if TTL fires) (source: adversarial-performance)

### Concrete Recommendations
1.1. [HIGH] Semantic chain strategy (Strategy 3) has ZERO test coverage (source: adversarial-testing)
1.2. [HIGH] Threshold default mismatch: docstring says 0.7, parameter default is 0.5 (source: adversarial-quality)
1.3. [HIGH] _get_st_model TTL cache eviction has zero test coverage (source: adversarial-testing)
1.4. [HIGH] Semantic chain strategy ignores newest_first parameter (source: adversarial-quality)
1.5. [HIGH] _session_text extraction — no edge case tests (source: adversarial-testing)
1.6. [HIGH] EmbedClient→SentenceTransformer fallback path not tested (source: adversarial-testing)
1.7. [HIGH] FileLock timeout silently swallowed — returns empty results instead of surfacing (source: adversarial-performance:534)
1.8. [HIGH] No integration tests for walk_session_chain unified entry point (source: adversarial-testing)
2.1. [MEDIUM] Inconsistent threshold: docstring says 0.7, parameter default is 0.5 (source: adversarial-quality)
2.2. [MEDIUM] Bare except: clauses mask errors silently (source: adversarial-quality)
2.3. [MEDIUM] st_birthtime unavailable on Windows — fallback uses st_ctime which is not session birth (source: adversarial-quality)
2.4. [MEDIUM] write_watermark has no try/except around FileLock — timeout propagates as unhandled (source: adversarial-performance:534)
2.5. [MEDIUM] walk_sessions_index_chain chain direction ambiguity (source: adversarial-testing)
2.6. [MEDIUM] SentenceTransformer fallback in walk_semantic_chain has 60-second cold load penalty (source: adversarial-performance)
2.7. [MEDIUM] Double-negative session_id comparison in walk_session_chain is confusing (source: adversarial-quality)
2.8. [MEDIUM] TOCTOU race in _stale_lock_recovery before FileLock acquisition (source: adversarial-performance)

### Open Questions / Unknowns
6.1. [LOW] Whether daemon will auto-start correctly in Claude Code environment (source: adversarial-performance)
6.2. [LOW] Whether 5-minute TTL is optimal — no empirical data on typical session chain usage pattern (source: adversarial-performance)