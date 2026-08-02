"""Host primitives shared across skills (P:/.agents/__lib/).

Add new shared primitives here when multiple skills need the same
implementation. Single-skill helpers should live in the skill's own
scripts/lib subdirectory, not here.

Current primitives:
- atomic_io: atomic file writes with optional cross-platform file lock
  (msvcrt on Windows, fcntl on POSIX). Used by email-skill's cache.json
  and state.json writers and will be reused by future skills that
  maintain shared mutable JSON state under P:/.data/.
"""