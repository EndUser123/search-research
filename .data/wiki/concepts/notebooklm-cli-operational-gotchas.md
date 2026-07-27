---
title: "NotebookLM CLI (nlm) operational gotchas — auth, bulk add, cosmetic errors"
created: 2026-07-25
source: session-2026-07-25
tags: [notebooklm, nlm, cli, authentication, bulk-operations, error-handling, gotcha]
summary: >
  Three operational gotchas for the `nlm` CLI discovered while bulk-importing
  4116 YouTube videos into 15 notebooks (verified end-to-end 2026-07-25):
  (1) `nlm login --check` returns a misleading "network_error" when auth is
  actually fine — the real recovery is `nlm login --profile <name>` which
  silently reuses Chrome's saved Google login via CDP, no user interaction.
  (2) `nlm source add --youtube u1 --youtube u2 ...` is bulk-repeatable in
  a single call — one invocation per notebook, not per video. A prior version
  of this workspace's rules claimed "no bulk endpoint exists"; that was wrong.
  (3) Bulk source-add always prints `Error: Failed to add URL source: <url>`
  for the first URL and exits with code 1, but the bulk continues and lands
  all sources. Verify with `nlm notebook get <id>` source_count, not exit code.
agent: grok
host: both
cognitive_load: 2
verification: observed
sources:
  - "https://notebooklm.google.com/" (Google, live API behavior observed 2026-07-25)
  - "nlm --help source add" (v0.9.0, verified 2026-07-25)
  - "P:/tmp/wl_notebooks_run.log" (run log, 15/15 notebooks verified at full source_count)
relations:
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: related
  - target: wiki/concepts/tool-fallbacks-manifest
    type: extends
  - target: wiki/concepts/dgemma-gemini-flash-operational-tests-2026-07-22
    type: related
---

# NotebookLM CLI (nlm) operational gotchas

## Decision context

**Why this was needed:** bulk-importing 4116 YouTube videos into NotebookLM
notebooks (15 clusters of ≤300 videos each, on a paid account with a 300-source
cap). Three traps surfaced during the run that would each have wasted a future
session's time if not recorded: a misleading auth-probe error, a false
"no bulk endpoint" assumption, and a cosmetic-but-scary first-URL error that
does not indicate actual failure. Each is the kind of gotcha where a plausible
narrative ("auth must be expired," "I need to loop per video," "the bulk add
failed") would lead to wasted work.

## Gotcha 1: `nlm login --check` lies about auth

**Symptom:** `nlm notebook list` (or any API call) returns:

```
✗ Authentication Error
  Authentication expired. Run 'nlm login' in your terminal to re-authenticate.
```

**Probe:** `nlm login --check` returns:

```
✗ Authentication failed: Could not reach NotebookLM (network_error:
ClientAuthenticationError).
Check your connection and try again — your saved credentials may still be valid.
```

**The trap:** the probe says "network_error." The natural reads are "auth
expired" or "network down." **Both are wrong.** Verified 2026-07-25: 4 cached
profiles (`codex`, `default`, `alt`, `ytis-pro-worker-01`) all reported this
same probe output AND were immediately recoverable; `Invoke-WebRequest
https://notebooklm.google.com` returned HTTP 200 (network fine). The probe is
inconclusive — the SKILL.md's distinction between `unverified` (probe failed)
and `expired` (tokens dead) is real and matters here.

**Recovery (no user interaction required):**

```powershell
nlm login --profile <profile-name>
```

This launches Chrome silently via CDP, reuses the saved Google login in the
profile's browser data dir, extracts cookies, and writes them to
`C:\Users\<user>\.notebooklm-mcp-cli\profiles\<name>`. Verified on profile
`codex`: ~10 seconds, no browser interaction, no prompt, no user required.

**When to escalate to a human:** only if `nlm login --profile <name>` itself
fails (Chrome's saved Google login has also expired). On this host, `nlm login
profile list` shows ~230 cached profiles, most mapped to a small number of
Google accounts. Try multiple profiles before escalating.

**Default profile on this host:** `codex`. Recorded in
`~/.grok/tool-fallbacks.md` under "CLI auth recovery recipes." This is a
[[plausible-narratives-substitute-for-verification]] failure mode — the probe
gives a plausible story ("network error") that, if trusted, leads to wasted
user escalation.

## Gotcha 2: bulk source-add is real — don't loop per video

**The capability:** `nlm source add <nb-id> --youtube u1 --youtube u2 ... --
youtube uN` is **repeatable for bulk in a single CLI invocation.** One call
per notebook ingests all URLs. The MCP equivalent is
`source_add(source_type="url", urls=[...])`.

**Why this matters:** for N videos across M notebooks, the cost is M bulk
calls, not N single calls. For the 4116-video / 15-notebook run on 2026-07-25,
this was the difference between **15 calls (~30 min total)** and **4116 calls
(~2.3 hours of API time at 2s rate-limit spacing)**.

**The mistake I made:** I asserted "NotebookLM has no bulk endpoint, each
video is one API call" as fact without running `nlm source add --help`. The
`--help` output clearly documents `--url` and `--youtube` as **"(repeatable
for bulk)"**. The SKILL.md at `C:\Users\brsth\.agents\skills\nlm-skill\SKILL.md`
also documents it (`source_add(source_type="url", urls=[...])`). I trusted a
plausible assumption over a 5-second verification. The operator corrected it
in one line.

**Rule:** for any CLI capability claim ("X is not supported," "no bulk
endpoint," "must be done one at a time"), run `<cmd> --help` before asserting
it. The receipt rule applies to negative claims about tool surface, not just
positive ones. See [[evidence-first-default]] and [[claims-require-receipts]].

## Gotcha 3: first-URL "Error: Failed to add URL source" is cosmetic

**Symptom:** bulk `nlm source add` always prints, on stderr:

```
Error: Failed to add URL source: https://www.youtube.com/watch?v=<first-url>
```

…and exits with code 1.

**The trap:** this looks like total failure. The natural reads are "the bulk
add failed on the first URL and aborted" or "the first URL is invalid."
**Both are wrong.** Verified across all 14 bulk-add calls in the 2026-07-25
run: every single one printed this exact error on the first URL, every single
one exited with code 1, and every single one actually ingested all URLs.

Evidence table (excerpt):

| Cluster | URLs | First-URL error? | Exit code | Actual source_count |
|---|---|---|---|---|
| 0 | 295 | yes | 1 | 295 |
| 1 | 294 | yes | 1 | 294 |
| 7 | 296 | yes | 1 | 296 |
| 10 | 300 | yes | 1 | 300 |
| 13 | 291 | yes | 1 | 291 |
| 14 | 279 | yes | 1 | 279 |

**Hypothesis (not verified):** the CLI probes the first URL synchronously
before the batch path warms up; the probe fails, but the bulk path then
succeeds. The exit code 1 is inherited from the probe, not the bulk result.

**Correct verification:** poll `nlm notebook get <id>` (or `nlm source list
<id>`) for `source_count`. Compare against expected. **Do not** treat the CLI
exit code or the first-URL stderr line as the verdict. In Python:

```python
rc, out, err = subprocess.run(["nlm", "source", "add", nb, "--youtube", u1, ...])
# rc will be 1 and err will contain "Failed to add URL source" — ignore both
time.sleep(30)  # let NotebookLM register the sources
info = json.loads(subprocess.run(["nlm", "notebook", "get", nb, "--json"], ...).stdout)
actual = info["source_count"]  # this is the real signal
```

## Bonus: NotebookLM source cap (paid account)

**Fact (corrected 2026-07-25):** NotebookLM paid accounts support **up to 300
sources per notebook** (each YouTube video = 1 source). I had wrongly asserted
a "~50-source hard cap" from stale training data — that's the free-account
limit. The operator has a paid account; the 300 cap was confirmed empirically
when cluster 10 (300 videos) landed all 300 sources without error.

**Don't repeat the mistake:** the 50-source figure is the free-tier limit.
For paid accounts, use 300. When in doubt, test with one notebook at the
target size and verify `source_count` lands.

## What this means for our workspace

- **`~/.grok/tool-fallbacks.md`** already carries the auth-recovery recipe and
  the bulk-add correction under "CLI auth + bulk recipes." This wiki page is
  the concept-level companion — it explains *why* the recipes exist and what
  failure modes they prevent.
- **For any future NotebookLM bulk operation:** (1) ignore first-URL stderr
  and exit code 1, verify via `notebook get`, (2) use `--youtube` repeatable,
  one call per notebook, (3) recover auth via `nlm login --profile <name>`
  before escalating to the user.
- **The Python driver pattern** (`P:/tmp/wl_notebooks_driver.py`) is reusable:
  checkpoint state to JSON after each notebook, poll for source_count, resume
  on crash. The pattern applies to any bulk `nlm` operation, not just YouTube
  imports. The clustering itself is documented at
  [[semantic-clustering-bounded-size]].
- **Driver-script artifacts from the 2026-07-25 run:**
  - `P:/tmp/wl_notebooks_run.json` — notebook IDs + verified counts
  - `P:/tmp/wl_notebooks_run.log` — run log
  - `P:/tmp/wl_notebooks_driver.py` — the driver (reusable template)

## Falsifier

These gotchas are tied to `nlm` v0.9.0 and NotebookLM's backend behavior as
observed 2026-07-25. They stop being true if:
- `nlm` fixes the misleading `--check` probe (would make Gotcha 1 obsolete)
- `nlm` adds a real bulk endpoint with different semantics (would make
  Gotcha 2 and Gotcha 3 both obsolete)
- NotebookLM changes its source-ingest path such that the first-URL probe
  actually does abort the bulk (would make Gotcha 3 dangerous to ignore)

Re-verify by running one pilot bulk-add before trusting any of these on a new
`nlm` version or a new NotebookLM backend revision.

## Sources

- `nlm source add --help` (v0.9.0, verified 2026-07-25) — confirms `--youtube`
  is "repeatable for bulk"
- `nlm login --check` behavior (observed 2026-07-25 on 4 profiles) — confirms
  probe returns misleading `network_error` when auth is recoverable
- `P:/tmp/wl_notebooks_run.log` (15/15 notebooks, exit codes and source_counts)
  — confirms Gotcha 3 pattern across 14 independent bulk-add calls
- Operator correction (2026-07-25) — confirmed paid-account source cap is 300,
  not 50
