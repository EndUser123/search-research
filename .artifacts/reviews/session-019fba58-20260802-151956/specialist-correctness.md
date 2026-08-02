# Correctness Review — session 019fba58

Scope: 6 Python files (changed-lines diff) plus 2 new files read in full. Reviewed for bugs, edge cases, concurrency, and multi-terminal safety.

---

## File: `hooks/PreToolUse_skill_staleness.py` (NEW)

### Issue 1 -- Severity: bug
- File: `C:/Users/brsth/.grok/hooks/PreToolUse_skill_staleness.py:46-82`
- Description: Read-modify-write of the per-session `skill-mtimes.json` state dict has a TOCTOU race. Two concurrent `read_file` calls in the same session (Grok Build allows parallel tool dispatches) can each read the dict, each insert/overwrite their own key, and each write back atomically — losing the other's entry. The PID-suffixed `.tmp` prevents file corruption but does not serialize the dict update.
- Evidence: Lines 46-82 read `state_file.read_text`, mutate the parsed dict in memory, then `tmp.replace(state_file)`. No lock around the section. Hooks run as separate processes per dispatch, so even same-session concurrency hits this.
- Suggestion: Wrap the read-modify-write in a per-session file lock (similar pattern to `fleet_quota._cache_file_lock`). Use a sidecar `<state_file>.lock` file because the state file is replaced atomically and changes inode.

### Issue 2 -- Severity: bug
- File: `C:/Users/brsth/.grok/hooks/PreToolUse_skill_staleness.py:65-67`
- Description: Dead branch with misleading comment. `elif last_mtime == 0: pass` does nothing; the unconditional write below it handles "first read" identically to any other case. The comment "First read — just store" suggests divergent behavior that doesn't exist.
- Evidence: Lines 65-67 vs lines 72-79 — both branches lead to the same write at line 75.
- Suggestion: Remove the `elif` entirely. The unconditional write below covers both first-read and subsequent-read cases correctly.

### Issue 3 -- Severity: gap
- File: `C:/Users/brsth/.grok/hooks/PreToolUse_skill_staleness.py:78-80`
- Description: Silent failure on state-file write errors. If disk is full or permissions deny the write, the stale-detection logic silently degrades — subsequent runs read stale `last_mtime` values but never persist new ones. The hook keeps firing but every read after the first will trigger the stale-reminder because the comparison value never advances.
- Evidence: `except Exception: pass` with no logging at line 79-80.
- Suggestion: Log to stderr at minimum. If persistence is broken, the comparison should either bypass the reminder or emit a one-shot notice.

### Issue 4 -- Severity: gap
- File: `C:/Users/brsth/.grok/hooks/PreToolUse_skill_staleness.py:31-35`
- Description: Substring match `"SKILL.md" not in str(target_file)` is case-sensitive. A skill file named `Skill.md` or `skill.md` would not trigger this hook, missing staleness detection on any skill that doesn't follow the exact capitalization. Also matches unintended substrings (e.g., `MYSKILL.md` — wait, that wouldn't match because the substring is uppercase `SKILL.md`).
- Evidence: Line 32 case-sensitive substring search.
- Suggestion: Case-insensitive match: `"skill.md" not in str(target_file).lower()`.

### Issue 5 -- Severity: gap
- File: `C:/Users/brsth/.grok/hooks/PreToolUse_skill_staleness.py:34, 52`
- Description: Path normalization happens after `exists()` check but before `resolve()`. If `target_file` is relative, `exists()` resolves against cwd (which may differ per hook dispatch in concurrent terminals), but `stored_key = str(target_path.resolve())` produces an absolute resolved key. The mismatch means the same logical file could be stored under different keys across runs depending on cwd, defeating the staleness check.
- Evidence: Line 34 `Path(target_file).exists()` (cwd-relative) vs line 52 `target_path.resolve()` (absolute).
- Suggestion: Resolve `target_path` immediately after construction, before `exists()`.

---

## File: `skills/handoff/__lib/claim_handoff.py` (NEW)

### Issue 6 -- Severity: bug
- File: `C:/Users/brsth/.grok/skills/handoff/__lib/claim_handoff.py:62-66`
- Description: `_set_field` corrupts frontmatter when the field does not already exist. The fallback path appends `\n{field}: {value}\n---\n` to the input string, but the input is the full document text (not just the frontmatter block). After `rstrip()` removes the trailing closing `---\n` along with the body, the new field is inserted **into the body section** and a duplicate closing `---` is appended. Result: malformed YAML frontmatter.
- Evidence: Callers at lines 110-112 pass `text` (the whole file), not just the frontmatter. When a field is absent, `text.rstrip() + f"\n{field}: {value}\n---\n"` produces `<original text without trailing newline> + \n + field + value + \n--- + \n`, putting the new field after the original closing `---` (in the body) and adding a spurious closing `---` at the end. Trace: `text = "---\nfoo: bar\n---\nbody"`, `text.rstrip() = "---\nfoo: bar\n---\nbody"`, append `\nnew: val\n---\n` → `---\nfoo: bar\n---\nbody\nnew: val\n---\n`.
- Suggestion: Parse out the frontmatter first (e.g., reuse `_parse_frontmatter` which is defined but never called), edit only the frontmatter block, then re-assemble the document. The fallback should insert before the closing `---` of the frontmatter, not at the end of the file.

### Issue 7 -- Severity: bug
- File: `C:/Users/brsth/.grok/skills/handoff/__lib/claim_handoff.py:113, 141`
- Description: `path.write_text(text, encoding="utf-8")` is not atomic. On Windows, a process crash or sibling-session write during the write leaves the handoff file in a corrupted state with truncated frontmatter. The handoff files live in a shared directory (`P:/docs/handoffs/`) accessed by multiple agents.
- Evidence: Lines 113 and 141 use plain `write_text` with no tmp+rename pattern. Compare to `PreToolUse_skill_staleness.py` and `fleet_quota.py` which both use `tmp.replace` for atomicity.
- Suggestion: Write to a PID-suffixed temp file in the same directory, then `os.replace()` to the final path. Same pattern as the staleness hook.

### Issue 8 -- Severity: bug
- File: `C:/Users/brsth/.grok/skills/handoff/__lib/claim_handoff.py:90-114, 121-142`
- Description: No locking around read-check-write. Two concurrent `claim` invocations on the same handoff (legitimate scenario when two sessions race to pick up a handoff) will both pass the "already claimed" check (line 100), both call `_set_field`/`_append_changelog`, and one's write wins — silently losing the other's changelog row.
- Evidence: No lock between `path.read_text` (line 95) and `path.write_text` (line 113). On a multi-agent Windows host this is a real concurrency hazard.
- Suggestion: Wrap read-check-write in a file lock (`.lock` sidecar in the handoff directory). Use `msvcrt.locking` on Windows like `fleet_quota._cache_file_lock`.

### Issue 9 -- Severity: gap
- File: `C:/Users/brsth/.grok/skills/handoff/__lib/claim_handoff.py:124-142`
- Description: `release()` does not verify that the caller is the claim owner. Any session can release any handoff without authorization — silently destroying another session's claim. On a multi-terminal host this means a session can stomp a sibling's in-flight work.
- Evidence: Lines 124-142 — `release()` reads `assigned_to` but does not check `assigned_by == session`. No warning is emitted.
- Suggestion: Check `existing_by = _get_field(text, "assigned_by")` and refuse release unless it matches `session`, or print a warning and require a `--force` flag.

### Issue 10 -- Severity: gap
- File: `C:/Users/brsth/.grok/skills/handoff/__lib/claim_handoff.py:25`
- Description: `_utc_now()` uses minute precision (`"%Y-%m-%dT%H:%M"`). Two claims within the same minute produce identical timestamps in the changelog, making audit ordering ambiguous. For changelog rows that may be written in rapid succession (claim → release cycles), second-level resolution is needed.
- Evidence: Line 25 `strftime("%Y-%m-%dT%H:%M")`.
- Suggestion: Use `"%Y-%m-%dT%H:%M:%S"` or include a monotonic counter / microsecond suffix.

### Issue 11 -- Severity: gap
- File: `C:/Users/brsth/.grok/skills/handoff/__lib/claim_handoff.py:30-40`
- Description: `_parse_frontmatter` is defined but never called anywhere in the file. The function also returns `("", fm, after)` — the first element is always an empty string, making the `tuple[str, str, str]` return type misleading (claim suggests a `(before, fm, after)` triple but `before` is dead).
- Evidence: Definition at lines 30-40; no callers found via grep of the file. The bug in `_set_field` (Issue 6) exists precisely because callers don't route through this parser.
- Suggestion: Either delete `_parse_frontmatter` or wire it into `claim`/`release` (which would also fix Issue 6).

### Issue 12 -- Severity: gap
- File: `C:/Users/brsth/.grok/skills/handoff/__lib/claim_handoff.py:76`
- Description: `re.search(r"## Changelog\s*\n\s*\|.*\n\|[-:| ]+\n", text, re.IGNORECASE)` only matches a 2-row table header (header row + separator). If the existing changelog has additional header rows or a different separator style, the regex misses and a duplicate `## Changelog` section is appended.
- Evidence: Line 76 hard-codes exactly one header row + one separator row.
- Suggestion: Search for the separator row alone (`r"## Changelog.*?\n\|[-:| ]+\n"`) and use re.DOTALL.

### Issue 13 -- Severity: gap
- File: `C:/Users/brsth/.grok/skills/handoff/__lib/claim_handoff.py:102`
- Description: Truncation logic is redundant. `existing_by[:8] if len(existing_by) >= 8 else existing_by` is identical to `existing_by[:8]` — Python slicing returns the full string if shorter. No conditional needed.
- Evidence: Line 102.
- Suggestion: Simplify to `existing_short = existing_by[:8]`.

### Issue 14 -- Severity: gap
- File: `C:/Users/brsth/.grok/skills/handoff/__lib/claim_handoff.py:48-49`
- Description: `_get_field` strips `#` from values, treating any `#` as an inline comment. YAML values legitimately containing `#` (commit hashes, hex colors, URLs with fragments) would be silently truncated.
- Evidence: Lines 48-49 `if "#" in val: val = val.split("#")[0].strip()`.
- Suggestion: Only strip inline comments if `#` is preceded by whitespace (YAML convention). Or skip comment stripping entirely and let consumers handle.

---

## File: `hooks/PreToolUse_spawn_model_gate.py` (CHANGED)

### Issue 15 -- Severity: gap
- File: `hooks/PreToolUse_spawn_model_gate.py:~282-289` (diff line 282-291)
- Description: The 50ms retry sleep on `json.JSONDecodeError` is non-deterministic. A slow writer (large cache, antivirus scan, network filesystem) may take longer than 50ms, causing the retry to also fail and triggering the fail-safe `BLOCKED` path unnecessarily.
- Evidence: Diff line 282-291 — single `time.sleep(0.05)` retry before fail-closed.
- Suggestion: Retry 2-3 times with exponential backoff (50ms, 100ms, 200ms), or read byte-by-byte until valid JSON is reached.

### Issue 16 -- Severity: gap
- File: `hooks/PreToolUse_spawn_model_gate.py:~382-391` (diff line 380-391)
- Description: Escalation-counter reset (`F9 fix`) has the same TOCTOU race as the staleness hook. Two concurrent allow-paths can each read `esc_data`, each delete a different model entry, and each write back — losing one entry. Not catastrophic (advisory) but inconsistent with the locking added to `fleet_quota` for the same pattern.
- Evidence: Lines 382-391 read-then-write without lock.
- Suggestion: Use the same `_cache_file_lock`-style sidecar lock, or accept the race as advisory.

### Issue 17 -- Severity: gap
- File: `hooks/PreToolUse_spawn_model_gate.py:~392` (diff line 392)
- Description: Bare `pass # Allow` comment removed but the structural comment "Allow" at the surrounding code's tail is gone — minor, but the `try/except Exception: pass` block for the escalation reset hides all errors silently, including permission errors that might indicate a deeper problem.
- Evidence: Diff line 392 shows removal of `-# Allow` and addition of `+    pass  # escalation reset is advisory`.
- Suggestion: At minimum, log permission errors to a debug file so the operator can see when the reset silently fails.

---

## File: `skills/model-quota/scripts/fleet_quota.py` (CHANGED)

### Issue 18 -- Severity: bug
- File: `skills/model-quota/scripts/fleet_quota.py:~480` (diff line 480)
- Description: `worst = entries[0]` replaces the previous `min(entries, key=lambda x: x["pct"])`. The variable name "worst" now claims something the code doesn't deliver. `entries` is presumably insertion-ordered; the first entry is whichever window the source emits first, not the one with the lowest quota. If the source emits entries alphabetically or in API response order, "worst" can be any window — the summary's "representative" entry can now be the least-representative one.
- Evidence: Diff line 480 shows the change from min-by-pct to entries[0].
- Suggestion: Either restore the min-by-pct selection (with a None-guard for unknown pools), or rename `worst` to `representative` (or `first`) and document the semantic shift. The change should match intent.

### Issue 19 -- Severity: bug
- File: `skills/model-quota/scripts/fleet_quota.py:~494-525` (diff line 490-525)
- Description: `msvcrt.locking(fd, msvcrt.LK_LOCK, 1)` is held for the duration of the read-modify-write (which may include disk I/O, JSON parsing, tmp write, and rename). If the holder process crashes mid-section, the lock file remains held. msvcrt locks on Windows are released when the file handle is closed by the OS, but if the file descriptor is still open in a child process or has been duplicated, the lock survives. Combined with `os.close(fd)` only in the `finally` (line 524), any exception before the close that doesn't propagate to finally (rare but possible on signal/terminate) leaks the fd and the lock.
- Evidence: Diff lines 500-525 — `fd = os.open(...)` at line 502, `os.close(fd)` at line 524 inside `finally`. No `try/except` around `yield` to ensure close.
- Suggestion: Use `contextlib.closing` around the fd, or wrap the open in a try/finally that always closes. Also document that on process kill the lock is best-effort released by Windows.

### Issue 20 -- Severity: gap
- File: `skills/model-quota/scripts/fleet_quota.py:~500-525` (diff line 500-525)
- Description: `msvcrt.locking(fd, msvcrt.LK_LOCK, 1)` retries internally at 10/sec with 10ms intervals. If a hook caller is interrupted by Ctrl+C / SIGINT while waiting on the lock, the lock is not released (the holder is still in the read-modify-write). The waiter raises KeyboardInterrupt and exits; subsequent callers also wait. This is a soft-hang scenario on the Windows host.
- Evidence: No signal-safe locking around the lock acquisition.
- Suggestion: Wrap lock acquisition in a timeout (e.g., `LK_LOCK` with retry limit, or fall back to `LK_NBLCK` and fail-safe). Without timeout, a stuck hook can stall other hooks indefinitely.

### Issue 21 -- Severity: gap
- File: `skills/model-quota/scripts/fleet_quota.py:~423-425` (diff line 423-425)
- Description: `"Browser Agent": {"pool": 0, "reset": "monthly"}` with the comment "ESTIMATED — Pro pool size undisclosed". When `pool == 0`, the code returns `pct = None` and excludes the entry from alerts (`pct is not None` filter at line 575). This means Browser Agent quota exhaustion is silently invisible to the fleet. If Browser Agent is fleet-relevant, this is a missed-alert bug; if not, the entry should be filtered out earlier rather than retained with `pct=None`.
- Evidence: Diff line 423-425 sets pool=0; line 575 filters out None pct from alerts.
- Suggestion: Either filter Browser Agent at the POOLS level (skip it entirely) or surface a low-confidence alert (e.g., `_suppress_alert=False` with `pct=None` and a different alert rule).

### Issue 22 -- Severity: gap
- File: `skills/model-quota/scripts/fleet_quota.py:~486` (diff line 486)
- Description: `_suppress_alert` underscore-prefixed key in the entry dict. If this dict is serialized to JSON anywhere (cache write at line 564-568), the underscore leaks into the cache file. Downstream consumers reading the cache will see `_suppress_alert` as a regular field.
- Evidence: Line 486 sets the key; subsequent JSON dump at line 564-568 includes it.
- Suggestion: Pop `_suppress_alert` before serialization, or use a separate set-of-windows-to-suppress structure rather than embedding in the entry dict.

---

## File: `skills/go/__lib/ship_receipt.py` (CHANGED)

### Issue 23 -- Severity: gap
- File: `skills/go/__lib/ship_receipt.py:~582-591` (diff line 580-591)
- Description: Test-name extraction is brittle. `line.split(" - ")[0]` assumes pytest format is `FAILED path::test - error`. If pytest changes its output format, or if a conftest plugin emits non-standard "FAILED" lines, the parsed names will include trailing junk or miss real failures. Also, lines that are *not* test results (e.g., `====== 3 failed, 1 passed ======` or summary headers) could match `FAILED` as a prefix if pytest emits `FAILED` in another context (rare, but possible).
- Evidence: Lines 580-591 split on literal `" - "` with hard-coded FAILED/ERROR prefixes.
- Suggestion: Use pytest's structured output (`--json-report` or `pytest --tb=line -q` with parsed `nodeid` field) rather than regex on human-readable output.

### Issue 24 -- Severity: gap
- File: `skills/go/__lib/ship_receipt.py:~593-596` (diff line 593-596)
- Description: `baseline.get("fail_names", [])` defaults to empty list when the baseline receipt predates this field. An old baseline with `failed: 3` but no `fail_names` will be compared against `fail_names = set()`, yielding `inherited = 0` and `new_failures = all current failures`. This regresses the comparison logic for any baseline generated before this change.
- Evidence: Lines 593-596 — old baselines lack `fail_names`, so inherited count is always 0 for old data.
- Suggestion: On baseline receipt without `fail_names`, fall back to count-only comparison (the old behavior) for backwards compatibility. Or version the baseline schema and reject pre-version baselines.

### Issue 25 -- Severity: gap
- File: `skills/go/__lib/ship_receipt.py:~601` (diff line 600-601)
- Description: `result["detail"] = "ruff not installed (run: pip install ruff)"` is a static string. If ruff is missing for any reason other than "not installed" (e.g., venv not activated, wrong python), the error message is misleading. The original `result["detail"] = "ruff not installed"` was at least honest.
- Evidence: Line 601 hardcodes the message; no detection of *why* ruff isn't running.
- Suggestion: Include the actual stderr (e.g., `result["detail"] = f"ruff not installed: {err.strip().splitlines()[0]}"`).

---

## File: `skills/close/__lib/close_runner.py` (CHANGED)

### Issue 26 -- Severity: bug
- File: `skills/close/__lib/close_runner.py:~691` (diff line 690-700)
- Description: New terminal state `succeeded_render_failed` is introduced alongside the existing `succeeded_pending_render` and `malformed` states. Any downstream consumer that switches on these states (e.g., `validate_close_claim`, operator dashboards, audit scripts) needs to handle the new state. The diff doesn't show consumer updates. If a consumer treats `malformed` as the failure signal (line 697 shows the change from "malformed" to "succeeded_render_failed"), downstream code may misclassify.
- Evidence: Diff line 697 — `attempt_id, session_id, "malformed"` changed to `"succeeded_render_failed"`. No consumer diff shown.
- Suggestion: Verify all consumers of `terminal_state` recognize the new value. If they don't, this is a silent state-machine regression.

### Issue 27 -- Severity: bug
- File: `skills/close/__lib/close_runner.py:~658` (diff line 658)
- Description: New terminal state `"timed_out_cleanup_failed"` is added to replace the conflated `"cleanup_failed"`. If downstream consumers expect only `timed_out` or `cleanup_failed`, they will fail to recognize the combined state. State-enum changes are a classic source of silent regressions.
- Evidence: Diff line 658 — `state = "timed_out_cleanup_failed"` is a new value not present in any prior code path.
- Suggestion: Treat the two signals as separate fields (e.g., `timed_out: bool`, `cleanup_ok: bool`) rather than overloading the `state` string with combinations. This scales better and is less error-prone.

### Issue 28 -- Severity: gap
- File: `skills/close/__lib/close_runner.py:~638` (diff line 638)
- Description: `scanner_status` is selected by substring match on `error_detail` containing `"gates not clean"`. If the scanner message wording changes (e.g., from "gates not clean" to "unresolved gates" or "gates failed"), the match silently misses and falls into the "scanner unavailable" branch — which is a more severe-sounding classification than the actual state.
- Evidence: Diff line 638 — `"gates not clean" in error_detail`.
- Suggestion: Use a structured field from the scanner output (e.g., a JSON status code) rather than substring matching prose.

### Issue 29 -- Severity: gap
- File: `skills/close/__lib/close_runner.py:~613` (diff line 612-619)
- Description: Corrupt receipt filename uses `_utc_now().replace(':', '').replace('-', '')` which yields minute-precision timestamp. If two corruptions happen in the same minute (concurrent scanner crash + manual close, or two scanner runs within the same minute), the rename will overwrite the earlier evidence. The whole point of preserving the corrupt file is to retain diagnostic information.
- Evidence: Diff line 615 uses minute precision (`%Y-%m-%dT%H:%M`) for the corrupt filename.
- Suggestion: Include PID or microsecond precision in the corrupt filename to ensure uniqueness. Also consider preserving multiple backups rather than one.

### Issue 30 -- Severity: gap
- File: `skills/close/__lib/close_runner.py:~676-680` (diff line 670-680)
- Description: `unresolved` extraction assumes `parsed.get("gates")` is a dict. If the scanner returns gates as a list or under a different key, the list is silently empty and the error message says "gates unresolved" without naming which ones. The detail message is useful for diagnosis but may be misleading.
- Evidence: Diff line 676-680 — defensive `isinstance` checks but no fallback message when shape is unexpected.
- Suggestion: When `parsed` shape is unexpected, include a structural note in the message: `(unresolved gates: unknown — scanner returned non-dict gates structure)`.

---

## Summary

- 6 bugs (Issues 1, 2, 6, 7, 8, 18, 19, 26, 27)
- 9 gaps (Issues 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 25, 28, 29, 30)

Highest-priority fixes:
1. **Issue 6** (`_set_field` corrupts frontmatter when field is new) — affects any fresh handoff claim.
2. **Issue 7** (`path.write_text` is not atomic) — corruption risk on crash.
3. **Issue 8** (no lock around claim read-check-write) — multi-terminal hazard.
4. **Issue 18** (`worst = entries[0]` semantic regression) — wrong representative window.
5. **Issue 26/27** (new terminal states without consumer updates) — silent state-machine regression.

The fleet_quota lock pattern (Issue 19, 20) should be applied consistently to `claim_handoff.py` and the staleness hook for a uniform multi-terminal safety story.