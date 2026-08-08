# Plan: Implement /harvest skill with review corrections

## Objective
Install the /harvest event-sourced value-tracking skill at `~/.grok/skills/harvest/`
from source files in `C:\Users\brsth\Downloads\`, applying 8 corrections identified
during the review cycle.

## Source files
- `C:\Users\brsth\Downloads\harvest.py` — CLI (7 subcommands)
- `C:\Users\brsth\Downloads\store.py` — Event store (ULID, parent chains, reducer)
- `C:\Users\brsth\Downloads\SKILL.md` — Skill documentation
- `C:\Users\brsth\Downloads\test_harvest.py` — 18 test scenarios

## Target structure
```
~/.grok/skills/harvest/
  SKILL.md
  scripts/
    harvest.py     (CLI)
    store.py       (event store)
    test_harvest.py (test suite)
```

## Corrections (numbered as in the review)

### 1. Parent-level arbitration (CRITICAL)

**Problem:** The "write → reload → check disposition" pattern has a TOCTOU race.
A sibling event published AFTER your reload can have a lower ULID and
retroactively displace you from APPLIED to CONFLICT.

**Fix:** Claim file using `O_CREAT | O_EXCL` at the parent level.
- New directory: `P:/.data/harvest/claims/`
- Claim file: `claims/{parent_event_id}.claim` — contains the winning event_id
- `try_claim(parent_event_id, event_id)` → `os.open(path, O_CREAT|O_EXCL|O_WRONLY)`
- First writer to create the claim wins. All others return False immediately.
- Reducer (`_walk_chain`) reads claims and uses them as PRIMARY authority for
  sibling resolution. ULID sort is the FALLBACK when no claim exists (backward
  compat for pre-claim data).
- `write_event` returns `claimed: bool` in the record. Mutating commands check
  this and report APPLIED (exit 0) or CONFLICT (exit 6).

**Counterexample the fix must close:**
```
A publishes, A reloads (sees APPLIED), A exits 0,
B publishes with lower ULID,
A retroactively becomes CONFLICT.
```
With claims: A creates the claim file before publishing. B's claim attempt fails
immediately. B knows it's CONFLICT before publishing. A's claim is permanent.
No retroactive displacement possible.

### 2. Event disposition on ALL 8 post-ADD mutating commands

Commands: arm, verify, collect, mark-retire, keep, close, reopen, supersede.
Each checks `record["claimed"]` after `write_event`. If False, print CONFLICT
message and return exit code 6.

### 3. Explicit shell field in subprocess calls

`subprocess.run(command, shell=True)` dispatches via cmd.exe on Windows.
Add explicit documentation constant `SHELL_DISPATCH` and docstring noting the
dispatch shell. User-provided verification commands may need shell features
(pipes, redirects), so shell=True is retained with explicit documentation.

### 4. Deterministic race tests with Barrier

New test 19: two processes synchronized via `multiprocessing.Barrier(2)`.
Both observe the same parent head, both try to publish. Exactly one wins the
claim, the other gets CONFLICT. All worker functions at module level (Windows
spawn compatibility).

### 5. Coexistence check: WARN not block

`collect` checks for existing items with similar obligations and warns.
Does not block. `collect` is a subcommand inside `/harvest`, not a global route.

### 6. schema_version on every event

`SCHEMA_VERSION = "1.0"` constant in store.py. Every event record includes
`"schema_version": SCHEMA_VERSION`.

### 7. doctor reports fold timing

`cmd_doctor` times the `reduce_events` call with `time.perf_counter()` and
reports `fold time: Xms`.

### 8. Seed items as TODO comment

SKILL.md includes a `<!-- TODO: operator drafts 3 seed items -->` comment.
The LLM does not invent seed items.

## Exit codes
- 0: success (APPLIED)
- 2: argument error (not found, bad reason)
- 3: contract error (no verification, wrong mode)
- 4: collect without evidence
- 5: invalid transition
- 6: CONFLICT (lost the claim)

## Verification
```bash
python ~/.grok/skills/harvest/scripts/test_harvest.py
```
All tests must pass. Test 19 (Barrier race) must demonstrate exactly one
claimant wins and the other reports CONFLICT.
