---
title: "Migrate remaining 14 caller files to shared utilities (safe_io + yaml_fm)"
created: 2026-08-03
status: OPEN — mechanical sweep, ready for execution
assigned_to: grok
assigned_at: 2026-08-03T00:00
assigned_by: 019fba58
tags: [safe-io, yaml-fm, migration, dry, atomic-write, file-lock, sweep]
---

# Migrate remaining 14 caller files to shared utilities

## Objective

The shared utilities `~/.grok/__lib/safe_io.py` and `~/.grok/__lib/yaml_fm.py` were created this session. 6 of 20 caller files were migrated. The remaining 14 still use raw `os.replace`/`tmp.replace` or bespoke frontmatter handling.

## Background

See wiki concept: `P:/.data/wiki/concepts/workspace-level-shared-utilities-safe-io-yaml-fm.md`

## Files to migrate

Each migration is mechanical: replace the old pattern with the shared utility. Add the bootstrap block if not present.

| File | Old pattern | New pattern | Priority |
|------|------------|-------------|----------|
| `hooks/PostToolUse_auto_verify.py:93` | `os.replace(str(tmp), str(filepath))` | `safe_io.atomic_write_text` | High |
| `hooks/PostToolUseFailure_spawn_quota.py:165,207,222` | `os.replace(str(tmp), ...)` (3 sites) | `safe_io.atomic_write_json` | High |
| `hooks/scripts/mutation_receipt.py:166` | `tmp.replace(path)` | `safe_io.atomic_write_text` | Medium |
| `hooks/scripts/quality_gate.py:486,872,1256` | `os.replace(str(tmp), ...)` (3 sites) | `safe_io.atomic_write_*` | Medium |
| `hooks/scripts/verification_receipt_writer.py:615,760` | `os.replace(str(tmp), ...)` (2 sites) | `safe_io.atomic_write_*` | Medium |
| `hooks/scripts/Stop_text_log.py:81` | `os.replace(str(tmp_path), ...)` | `safe_io.atomic_write_text` | Low |
| `hooks/scripts/active_surface_snapshot.py:46` | `_atomic_write_text` private fn | Delete private; use `safe_io` | Medium |
| `skills/close/__lib/close_runner.py:176,213` | `msvcrt.locking` + `os.replace` | `safe_io.file_lock` + `safe_io.atomic_write_json` | High (load-bearing) |
| `skills/close/__lib/close_authority.py:694` | `os.replace` with retry | `safe_io.atomic_write_text` | Medium |
| `skills/close/__lib/close_accounting.py:760` | `os.replace` | `safe_io.atomic_write_*` | Low |
| `skills/aar/__lib/evidence_packet.py:263,280` | `os.replace` (2 sites) | `safe_io.atomic_write_*` | Low |
| `skills/aar/__lib/source_snapshot.py:217,341` | `os.replace` (2 sites) | `safe_io.atomic_write_*` | Low |
| `skills/aar/__lib/full_preprocessor.py:641,649` | `os.replace` (2 sites) | `safe_io.atomic_write_*` | Low |
| `skills/close/__lib/continuation_coverage.py:898` | `tmp.replace(path)` | `safe_io.atomic_write_*` | Low |
| `skills/model-web/__lib/run_state.py:65` | local `atomic_write` fn | Delete local; use `safe_io` | Medium |
| `skills/model-quota/scripts/fleet_quota.py:556-598` | `_cache_file_lock` + `os.replace` | `safe_io.file_lock` + `safe_io.atomic_write_json` | High (reference impl) |

## Migration procedure per file

1. Add bootstrap block (if not already present):
```python
_lib = Path(__file__).resolve().parent.parent / "__lib"  # adjust depth
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from safe_io import atomic_write_text, atomic_write_json, file_lock, read_json_or
```
2. Replace `tmp = path.with_suffix(...)` + `tmp.write_text(...)` + `os.replace(...)` with `atomic_write_text(path, content)` or `atomic_write_json(path, data)`
3. Replace `_cache_file_lock` or inline `msvcrt.locking` with `file_lock(lock_path)`
4. Delete private utility functions that are now superseded
5. Run `ruff check <file>` to verify clean
6. Run existing tests if available

## Acceptance criteria

- `rg "os\.replace|tmp\.replace" ~/.grok/hooks/ ~/.grok/skills/` returns zero matches outside `__lib/safe_io.py` and test files
- All existing tests pass after migration
- No new ruff errors

## Risk

- Each file has a slightly different bootstrap depth (hooks are at `~/.grok/hooks/`, skills at `~/.grok/skills/<name>/__lib/`). The `parent.parent / "__lib"` path must be adjusted per location.
- `fleet_quota.py` is the reference implementation — migrating it changes the pattern other skills might copy from. Verify the migration is clean.
- `close_runner.py` is load-bearing — test thoroughly after migration.

## Estimated effort

~2-3 hours for all 14 files. Each is 5-10 minutes of mechanical edit + verification.
