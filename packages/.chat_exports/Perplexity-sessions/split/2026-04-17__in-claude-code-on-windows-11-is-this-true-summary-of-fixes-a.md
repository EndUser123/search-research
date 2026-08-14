---
title: "In claude code on windows 11, is this true?
'
  Summary of fixes applied:

  1. dispatch_parallel — sequential dispat"
date: "2026-04-17"
mode: "CONCISE"
uuid: "74f7aa7b-9c2b-44fe-8252-e58c499b64ae"
entry_count: 13
---

## Human

In claude code on windows 11, is this true?
"
  Summary of fixes applied:

  1. dispatch_parallel — sequential dispatch: Replaced asyncio.gather with a sequential for loop to avoid opencode's SQLite "database is
  locked" error when multiple models run simultaneously.
  2. tests/conftest.py — missing fixture: Added the absent conftest.py that prepends the skill root to sys.path, fixing ModuleNotFoundError: No
   module named 'layers' when pytest runs from the project root.

  The SQD skill is now fully wired with all 32 tests passing.

✻ Churned for 13m 53s

❯ Does it mean that the open cloud models are still working in parallel? They just start sequentially? What would the delay be between the
  sequential starts?

● No — the models now run truly sequentially. Each model must fully complete (or error) before the next one starts. There's no artificial delay
   between starts; model N begins the instant model N-1 returns.

  This is a consequence of the for loop with await:

  for model in models:
      finding = await dispatch_single(target, model, output_dir)
      findings.append(finding)

  await is blocking on each call — control doesn't return to the loop until dispatch_single resolves. So the timeline is:

  deepseek → completes → gemini → completes → claude → ...

  Not:

  deepseek ─┬─→ completes (at ~30-60s)
  gemini    ┤      starts (~0s offset from deepseek)
  claude    ┘      starts (~0s offset from deepseek)

  Downside: Throughput is now N × single-model time instead of ~single-model time. Three models that each take 60s will take ~180s sequentially
   vs ~60s in true parallel.

  Upside: No more SQLite database is locked — only one opencode process exists at a time.

  If throughput matters more than SQLite safety, a proper fix would require opencode to support concurrent sessions — either through a
  session-reuse flag or a mutex lock file. But that's an opencode limitation, not an SQD bug.

✻ Worked for 1m 20s

※ recap: SQD skill is fixed and 32/32 tests pass. Two bugs resolved: sequential dispatch instead of parallel (SQLite lock), and missing
  `conftest.py` (module import failure). Next: re-run `/sqd on /sqd` to confirm the opencode concurrency issue is gone.

❯ Well, how close can we get to it with the technology we have available?

● With the current opencode dispatch mechanism, not much. The SQLite lock is at the process level — even with asyncio concurrency primitives,
  if you try to launch two opencode processes simultaneously, the second one to touch the DB loses. A semaphore capped at 1 would just
  serialize everything with extra overhead.

  What would actually enable parallelism:

  ┌───────────────────────────────────────────────────┬─────────────────────────────────┬──────────────────────────────────────────────────┐
  │                     Approach                      │           Parallelism           │                   Feasibility                    │
  ├───────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────┤
  │ Process pool with process-level mutex             │ True parallel, but mutex        │ Opencode manages its own DB, can't lock from     │
  │                                                   │ serializes                      │ outside                                          │
  ├───────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────┤
  │ Single opencode session, multiple model calls     │ Sequential within one process   │ Not supported — opencode CLI takes one --model   │
  │                                                   │                                 │ per run                                          │
  ├───────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────┤
  │ Batch all models into one prompt, single model    │ None (single model does all     │ Changes the adversarial review contract          │
  │ response                                          │ work)                           │                                                  │
  ├───────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────┤
  │ Different LLM backend (raw API calls)             │ Full parallelism                │ Defeats the purpose of using opencode's dispatch │
  │                                                   │                                 │  layer                                           │
  ├───────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────┤
  │ opencode session reuse (persistent connection)    │ Unknown                         │ Not documented / not tested                      │
  └───────────────────────────────────────────────────┴─────────────────────────────────┴──────────────────────────────────────────────────┘

  The honest answer: With opencode as the dispatch layer, we're at the ceiling of what the technology allows. True parallelism would require
  either opencode supporting concurrent multi-model sessions internally, or replacing the opencode subprocess calls with raw model API calls
  that manage their own concurrency.

  The only practical optimization on our end is to ensure no idle time between models — which the current for await loop already achieves.
  Models start the instant the previous one finishes."

## Assistant

Yes, this is accurate. Let me break down the key technical claims:

## Sequential Execution is Real

The analysis correctly identifies that replacing `asyncio.gather()` with a sequential `for` loop with `await` converts true parallelism to strict sequencing.  Each model completes before the next begins—there's no artificial delay, the next model starts immediately when the previous resolves. 

## The Trade-off is Correctly Framed

The throughput penalty is real: N models × single-model latency instead of ~single-model latency. Three 60-second models take ~180s sequentially vs ~60s parallel.  This is the direct cost of avoiding SQLite's "database is locked" error, which occurs because opencode manages its own connection pool and can't be safely called by multiple processes simultaneously. 

## Parallelism Constraints Are Accurate

The table's assessment is sound. You're constrained by opencode's architecture—it accepts one `--model` flag per invocation and manages a single SQLite connection.  A process-level mutex or semaphore would only serialize with added overhead; it doesn't unlock hidden parallelism. 

**Critical gap in the analysis:** The table lists "opencode session reuse (persistent connection)" as "Unknown" feasibility. This deserves investigation—if opencode supports a REPL-like or persistent session mode (documented or undocumented), you could dispatch multiple models to the same process without concurrent DB contention. This would be the practical win if it exists.

## Next Validation Step

Re-running `/sqd on /sqd` as suggested will confirm the fix works end-to-end, but won't expose whether opencode has an undocumented concurrent-session capability. You might probe opencode's CLI help or source (if available) to check for session flags or multiplexing support before considering a backend swap.

Is opencode's full CLI help or documentation available to you, or would you need to reverse-engineer this from trial runs?

## Human

It's available to you.  Please look it up, and also see what other people are doing for this situation.  Remember I'm also using python 3.14+

## Assistant

FACT: Based on current public info about opencode and SQLite, the explanation you pasted is **substantially correct** on the concurrency / “database is locked” behavior and what your change actually does.[1][2]

I’ll separate:

1. What’s true about opencode + SQLite
2. What your `for await` loop actually guarantees
3. What options realistically exist (today) to get closer to parallel
4. Anything Python 3.14‑specific that changes the picture

***

## 1. opencode + SQLite: what’s actually going on

From recent opencode issues, the situation is:

- opencode uses a **SQLite DB in the user profile** (e.g. `~/.local/.../opencode.db`) as its state/store.[2]
- Concurrent opencode CLIs hitting that DB can trigger `SQLiteError: locking protocol` / `database is locked` when they overlap on write activity.[1][2]
- The maintainers explicitly call out that this design **prevents multiple opencode instances from running concurrently** safely; SQLite is file‑locked and only one write transaction can own it.[3][2]

CONSENSUS (from SQLite docs and general guidance):

- SQLite does **file‑level locking**; writes are exclusive, reads are more permissive but still constrained.[4][3]
- If you do nothing special, a second process that hits the DB while it’s locked gets an immediate error instead of waiting.[5]

So your observation:

> “if you try to launch two opencode processes simultaneously, the second one to touch the DB loses”

is consistent with the tool’s own issue tracker and SQLite behavior.[3][2][1]

***

## 2. Is the `for model in models: await dispatch_single(...)` explanation correct?

Yes: that description is technically accurate.

With code effectively like:

```python
for model in models:
    finding = await dispatch_single(target, model, output_dir)
    findings.append(finding)
```

where `dispatch_single` shells out to `opencode` (a separate process) for each model:

- Each loop iteration:
  - Starts one opencode process.
  - Awaits until that process returns (success/error).
- Control only returns to the loop body **after** that process completes.
- Therefore, **only one opencode process is alive at a time** → true sequential dispatch.

There is no “overlap” in wall‑clock time between models, and no implicit delay between them beyond process startup/teardown:

- Model N+1 starts as soon as the `await` for model N resolves.
- If each model is ~60s, 3 models are ~180s wall time instead of ~60s.[3]

So the section in your text:

> “No — the models now run truly sequentially… There's no artificial delay between starts; model N begins the instant model N-1 returns.”

is correct as long as:

- `dispatch_single` does not internally multiplex multiple opencode runs itself, and  
- you are not running additional concurrent `dispatch_parallel` calls elsewhere.

Given the original symptom (“multiple models run simultaneously → opencode SQLite errors”), the switch from `asyncio.gather` to a simple loop with `await` is a standard and correct way to serialize the subprocess calls.

***

## 3. “How close can we get” to parallel with current tech?

Given what opencode is today, your “we’re at the ceiling” statement is broadly right, but there are a few realistic knobs. Let’s classify options by feasibility.

### 3.1 What you *cannot* cleanly fix from the outside

**a) True concurrent opencode processes sharing the same DB**

opencode’s own issue threads basically say: *multiple concurrent CLI instances against the same profile DB are not supported and will blow up under contention*.[2][1][3]

Because:

- The SQLite database is private to opencode.
- You do not control its connection options (e.g., `busy_timeout`, WAL toggling).
- There’s no exposed “session reuse” or RPC API documented.

So:

- A **process pool with a mutex/semaphore** on your side (N opencode calls, lock around each) simply reproduces what you’re already doing: at most 1 active opencode DB‑writer at a time, i.e., sequential with more overhead.
- Anything that tries to run *two opencode processes simultaneously* but “serialize DB access from outside” is not realistic—you have no hook into its internal SQLite connection.

The “process‑level mutex” row in your table is therefore correctly dismissed: you can’t override opencode’s DB‑locking from outside the process.[4][3]

**b) One opencode process handling multiple models in a single run**

Your note that the opencode CLI only supports one `--model` per run is consistent with its interface; there’s no documented “multi‑model in one invocation” or session‑like mode in public docs/issues as of 2026.[1][2]

So:

- “Single opencode session, multiple model calls” remains **not supported** by the CLI as documented.
- If there is some internal or experimental REPL / daemon mode, it’s not visible in public docs/issues; I could not find a `--session`, `--reuse`, or equivalent flag in current discussions.[2][1]

### 3.2 Options that *do* get you closer to parallelism

All of these work by avoiding shared opencode/SQLite state.

#### Option 1 – Multiple opencode profiles / separate DBs (SPECULATION, medium confidence)

If opencode supports:

- a profile flag (`--profile`, `--project`, similar) that points to a different config/DB directory, or  
- environment variables controlling the DB location,

then you could:

- Run different models in **different opencode profiles**, each with its own SQLite file.
- Parallelize across those independent DBs.

Trade‑offs:

- You’d lose shared history/state between profiles.
- Setup overhead: you’d need to configure each profile once (auth, model config, etc.).

I couldn’t see an explicit “multi‑profile for concurrency” pattern in public issues, but other CLI tools with SQLite (e.g. some dev tools) solve concurrency by sharding into separate DB files per worker.[4][3]

So: plausible, but needs experimentation in your environment.

#### Option 2 – Replace opencode’s dispatch with raw model API calls (FACT, but defeats purpose)

Your note that “different LLM backend (raw API calls) gives full parallelism, but defeats the purpose of opencode’s dispatch layer” is correct.[6]

In practice:

- Direct Python async clients for Claude/Gemini/etc. plus `asyncio.gather` *will* give you full concurrency.
- You’ll need to re‑implement:
  - Prompt construction / adversarial review contract.
  - Retry, backoff, logging, etc.
- This is what other people do when they hit similar SQLite or CLI bottlenecks: re‑implement their own dispatcher in Python using HTTP APIs.[7][6]

This is the cleanest route to true parallelism unless opencode gains a documented session/concurrency API.

#### Option 3 – Shard work across *machines / containers* (FACT)

Since SQLite locking is per file, not per network:

- Running opencode on multiple machines or containers, each with its own home directory/DB, avoids the contention entirely.[3][4]
- For you on Windows 11, that could mean:
  - Multiple WSL2 distributions or containers, each with its own `~/.local/.../opencode.db`.
  - A simple orchestrator script that dispatches models to different workers.

This is effectively **horizontal sharding** of opencode, not “fixing” concurrency inside one DB.

#### Option 4 – Accept partial parallelism within a model (NOT APPLICABLE unless opencode adds it)

If opencode internals ever add:

- internal batching or per‑model parallel steps, or
- a daemon mode that can be driven by a single client process with multiple “tasks”

then your outer loop could remain sequential while getting internal speedups. I see no public evidence that this exists right now.[1][2]

***

## 4. Anything special about Python 3.14+ here?

From Python 3.14 release notes:

- The main changes around `asyncio` are **introspection tools** (e.g., `python -m asyncio ps`, `pstree`) and minor API cleanups.[8][9]
- There’s no semantic change that magically makes `await` non‑blocking in the way you’d need; `await` still suspends the current coroutine until the awaited one completes.[9][8]

So for your situation:

- Python 3.14 does **not** alter the behavior of the `for await` pattern you pasted.
- What it *does* give you is better tooling to debug if you later experiment with partial concurrency (e.g., multiple dispatchers with a semaphore).

***

## 5. What others are doing in similar SQLite/CLI bottleneck scenarios

Patterns visible across issues / community posts (for SQLite and parallel agents generally):[6][4][3]

1. **Serialize writes, parallelize everything else**  
   - Exactly what you’ve done: one writer (opencode) at a time, but fan out work in parallel where it doesn’t hit the DB (e.g., independent HTTP calls, CPU‑bound transforms).

2. **Shard the database / profiles**  
   - Run multiple workers, each with its own DB file, to avoid locking altogether.

3. **Increase retry/backoff, timeouts** (less applicable here)  
   - For libraries where you control the SQLite connection, you can use `busy_timeout` or retry loops so that “database is locked” causes waits instead of failures.[5][4]
   - With opencode you *don’t* control the connection, so this is not available.

4. **Move to a different storage backend**  
   - In your case that would mean either:
     - opencode itself changing (e.g., WAL mode tuned for concurrency), or  
     - you bypassing opencode and managing state in another DB (Postgres, etc.) in your own dispatcher.

5. **Bypass the CLI and talk directly to services**  
   - For LLM workloads, people often hit a ceiling with CLI tooling and move to direct API calls so they can:
     - multiplex parallel requests,
     - manage their own DB/queues,
     - and avoid SQLite entirely.[6]

Your write‑up’s conclusion:

> “With opencode as the dispatch layer, we're at the ceiling of what the technology allows.”

is CONSENSUS‑correct **for the single‑profile, single‑DB, single‑machine scenario**.

***

## 6. Concrete next steps I’d suggest for you

Given your stack (Windows 11, Python 3.14+, heavy LLM use):

1. **Make the current sequential behavior explicit in code and comments**

   - Keep the `for model in models: await dispatch_single(...)` pattern.
   - Add a tight comment explaining:
     - “Intentionally sequential to avoid opencode SQLite lock when multiple CLI processes run concurrently. Do not re‑parallelize without changing opencode/DB design.”

2. **Probe whether opencode has any hidden profile/session flags**

   - Run `opencode --help`, `opencode config --help`, and look for:
     - profile / workspace / data‑dir flags.
   - If present, design a *profile‑sharded* dispatcher (e.g., map models to profiles) to get parallelism without DB contention.

3. **Decide whether you want “true parallel review” enough to justify a custom dispatcher**

   If yes, sketch a path:

   - Implement a Python dispatcher that:
     - builds the same adversarial review prompts,  
     - calls Claude/Gemini/etc. via HTTP APIs using `asyncio.gather`,  
     - stores state in your own DB or even plain files.
   - Use opencode only where its extra features are really needed.

4. **If you stay on opencode, accept sequential and optimize around it**

   - Ensure no idle gaps between models (already the case).
   - Reduce per‑model latency: smaller prompts, fewer tools, shorter contexts.
   - Consider *inter‑model concurrency* at the system level:
     - multiple `sqd` jobs scheduled across time or machines, each with its own opencode profile.

***

**Answer to your original question:**

- Yes, the explanation that your change makes the models run **truly sequentially**, with **no artificial delay** and with **throughput ≈ N × single‑model time**, is technically correct for claude‑code on Windows 11 using opencode as described.[2][1][3]
- With the opencode CLI as‑is, that sequentialization is effectively the safe upper bound in a single profile; getting closer to parallel requires either sharding the opencode DB (profiles/machines) or bypassing opencode with your own Python async dispatcher.

Assumption to validate: do you see any flags in `opencode --help` relating to profiles, workspaces, or custom data directories?

## Human

I don't think we need just one opencode profile.

## Assistant

Answer skipped.

## Human

I don't think we need just one opencode profile.

## Assistant

You’re right: you don’t need to be restricted to a single opencode “profile” / config set. In fact, opencode explicitly supports **multiple config directories** via env vars, which we can exploit to get more concurrency and isolation.[1][2][3]

Let’s be precise about what that buys us.

***

## 1. What opencode actually supports (relevant knobs)

From the official config + CLI docs:[2][3][1]

- Global config: `~/.config/opencode/opencode.json` and `.opencode` directory.  
- Custom config file: `OPENCODE_CONFIG` env var → path to a specific config file.[3][1][2]
- Custom config directory: `OPENCODE_CONFIG_DIR` env var → *directory* that is treated like a `.opencode` dir (agents, commands, modes, plugins, etc.).[1][2][3]

So we effectively have:

- **Multiple “profiles”** by using different `OPENCODE_CONFIG_DIR` values (and/or `OPENCODE_CONFIG`).[3][1]
- Each profile can have its own `opencode.json`, agents, plugins, and (critically) tends to store its *data* in its own subtree.

There is also an open feature request about “configuration profiles (per‑context setups)”, which is basically an official way to switch config sets. That reinforces the idea that *config is profile‑scoped* and that using different dirs is the intended workaround today.[4]

***

## 2. How multiple profiles help with SQLite locking

The root symptom you hit: one SQLite DB, multiple concurrent opencode CLIs → `database is locked` / “locking protocol” errors.[5][6][7]

SQLite constraints:[7][8]

- Locking is **per database file**.
- Two processes writing the same `.db` file concurrently → contention / errors unless managed carefully inside that application (which opencode is not doing yet).

If you run each opencode instance with:

- **its own config directory**, and  
- it stores its DB *under* that directory (or at least per‑config),

then you’ve effectively **sharded the DB**:

- Profile A → `config_dir_A/.../opencode.db`
- Profile B → `config_dir_B/.../opencode.db`

Those are independent files → no SQLite‑level locking between them.[8][7]

This is how multiple profiles concretely help:

- You can have *true parallel* opencode processes as long as they don’t share the same DB file.
- Your `dispatch_parallel` can become “parallel across profiles, sequential within each profile.”

Caveat (SPECULATION, but likely):  
We’re assuming opencode stores its DB under a path that is influenced by config dir / home. That’s how most tools behave, and it’s consistent with bug reports where WSL/home changes affect sessions. But you’d want to empirically confirm that DB location really differs when `OPENCODE_CONFIG_DIR` changes.[9]

***

## 3. A concrete pattern for you on Windows 11 / Python 3.14+

### 3.1 High‑level design

You can design your dispatcher as:

- N **logical “slots”**, each tied to a separate opencode config dir.
- For each model, choose a slot and spawn opencode with the appropriate env.

This gives:

- Parallelism up to N (slots).
- No DB contention between slots.
- Keeps using opencode as the “smart shell” around your models.

### 3.2 Sketch: Python 3.14+ async dispatcher with multiple profiles

Pseudo‑code (TypeScript‑ish logic but in Python terms):

```python
import asyncio
import os
from pathlib import Path

OPENCODE_BIN = "opencode.exe"  # adjust path if needed

PROFILES = [
    r"C:\opencode_profiles\profile1",
    r"C:\opencode_profiles\profile2",
    r"C:\opencode_profiles\profile3",
]

async def run_opencode_with_profile(profile_dir: str, model: str, target: str, output_dir: str):
    env = os.environ.copy()
    env["OPENCODE_CONFIG_DIR"] = profile_dir
    # If you have per-profile config file, also set OPENCODE_CONFIG
    # env["OPENCODE_CONFIG"] = str(Path(profile_dir) / "opencode.json")

    cmd = [
        OPENCODE_BIN,
        "--model",
        model,
        # whatever flags you need for your SQD invocation:
        "run-sqd",
        target,
        "--output-dir",
        output_dir,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()

async def dispatch_parallel_sharded(models, target, output_dir):
    tasks = []
    for i, model in enumerate(models):
        profile_dir = PROFILES[i % len(PROFILES)]  # simple round-robin
        tasks.append(
            run_opencode_with_profile(profile_dir, model, target, output_dir)
        )
    return await asyncio.gather(*tasks)
```

Key aspects:

- `OPENCODE_CONFIG_DIR` is per‑process; each child process gets a distinct config dir.[2][1][3]
- If opencode’s DB is per‑config (likely), you’ve just created **independent SQLite DBs** → safe concurrent writes.
- Dispatcher regains **true parallelism** across slots, without touching raw model APIs.

You can combine this with your current “sequential in a single profile” behavior:

- For **one profile**: keep the simple `for await` loop (safe, simple).
- For **higher concurrency**: introduce sharding like above.

***

## 4. What you don’t need (and why you were right)

> “I don’t think we need just one opencode profile.”

Agreed:

- The earlier “we’re at the ceiling” statement implicitly assumed:
  - One shared opencode DB/profile.
- But given:
  - opencode supports `OPENCODE_CONFIG_DIR` and `OPENCODE_CONFIG` as override mechanisms,[1][2][3]
  - SQLite locking is per‑file,[7][8]
- Then multiple profiles / config dirs are a valid axis of parallelization.

So: we’re **not** at the absolute ceiling; there is room via:

- Multi‑profile / multi‑DB design.
- Possibly multi‑machine as well (WSL instances, containers).

The trade‑offs:

- You must keep per‑profile configuration (agents, commands, auth) synced where necessary.
- Session history / state won't be shared across profiles. For SQD‑style tasks that may be fine.

***

## 5. How I’d adjust your earlier narrative

I’d update your internal docs / comments roughly like:

> With a single opencode profile/DB, we must serialize opencode invocations to avoid SQLite `database is locked` errors.  
>  
> For *true parallelism* while still using opencode, we can shard across multiple independent config directories (via `OPENCODE_CONFIG_DIR`), so each opencode process uses its own SQLite DB file. That lets multiple models run concurrently as long as they map to different profiles.

And in the code:

- Keep the current **sequential** `for await` path as the default, simplest behavior.
- Add an optional **“sharded” parallel dispatcher** that:
  - knows about `N` profiles,
  - parallelizes across them when configured.

***

If you’d like, next step can be:

- You paste your current `dispatch_parallel` implementation, and  
- I’ll propose the minimal changes to add a “profile sharding” mode that you can toggle via config/env without breaking your passing tests.

## Human

How to switch between multiple OpenCode profiles on Windows 11
Step-by-step setup for project-specific OpenCode configs
Does OpenCode support multiple auth profiles per provider like #5391
How to use OPENCODE_CONFIG_DIR for different setups

## Assistant

Here’s the concise, step‑by‑step picture based on current docs + issues.[1][2][3][4][5]

***

## 1. Does OpenCode support multiple auth profiles per provider?

- There is an open feature request: **“multiple auth profiles per provider”** (#5391) and a related Provider Auth v2 proposal.[4][5][6]
- Status: **requested, not generally available** as a user‑facing “profile switcher” today. It’s being tracked as part of a larger “multi‑account / credential vault” effort.[4]
- So: you **cannot** (yet) say “use OpenAI‑work vs OpenAI‑personal” via a first‑class `profile` flag. You *can*, however, simulate profiles by separating config directories.

FACT vs CONSENSUS:
- FACT: No documented `--profile` / “auth profile” flag in the CLI.[2]
- CONSENSUS: The recommended workaround is **project‑specific config** (local `.opencode` or `OPENCODE_CONFIG_DIR`) to keep accounts separated per project.[3][7][1]

***

## 2. How `OPENCODE_CONFIG_DIR` works (core mechanism you want)

From the official config docs:[1][3]

- `OPENCODE_CONFIG_DIR` (env var):  
  > “Specify a custom config directory… This directory will be searched for agents, commands, modes, and plugins just like the standard `.opencode` directory, and should follow the same structure.”[3][1]

From the CLI env var table:[2]

- `OPENCODE_CONFIG_DIR` – *Path to config directory*.  
- `OPENCODE_CONFIG` – *Path to config file* (optional override).  
- `OPENCODE_CONFIG_CONTENT` – inline JSON config.

Precedence: custom config is loaded after global config and `.opencode` directories, so it can override them.[1]

**Implication:** any time you set `OPENCODE_CONFIG_DIR` to a different directory and run `opencode`, you are effectively switching to a different “profile” (in your sense): different models, auth, agents, etc.

***

## 3. Step‑by‑step: project‑specific configs on Windows 11

### 3.1 Create a project config directory

For a given project, pick a dedicated directory, e.g.:

```text
D:\dev\my-project\.opencode-profile
```

Inside it, create at minimum:

```text
D:\dev\my-project\.opencode-profile\
  opencode.json        # your config
  agents\              # optional
  commands\            # optional
  plugins\             # optional
```

The structure is the same as a `.opencode` folder, just at an arbitrary path.[3][1]

### 3.2 Define a profile‑switching wrapper (PowerShell)

Create a small function in your PowerShell profile (e.g. `$PROFILE`):

```powershell
function Use-OpenCodeProfile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ProfileDir
    )

    if (-not (Test-Path $ProfileDir)) {
        throw "Profile directory '$ProfileDir' does not exist."
    }

    $env:OPENCODE_CONFIG_DIR = $ProfileDir
    Write-Host "OPENCODE_CONFIG_DIR set to $ProfileDir"
}
```

Usage in a project shell:

```powershell
cd D:\dev\my-project
Use-OpenCodeProfile "$PWD\.opencode-profile"

opencode run "hello from project-specific profile"
```

- Only that shell gets the env var; others remain on global config.  
- You can define one function per profile if you want shortcuts.

### 3.3 Use per‑project scripts

For totally self‑contained behavior, add a `scripts\opencode.ps1` in your repo:

```powershell
param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$profileDir = Join-Path $PSScriptRoot "..\.opencode-profile"
$env:OPENCODE_CONFIG_DIR = (Resolve-Path $profileDir)

# Forward all args to opencode
opencode @Args
```

Then:

```powershell
.\scripts\opencode.ps1 run "do thing"
```

This guarantees that when your automation (or SQD skill) calls this script, it always uses the project’s profile.

***

## 4. Switching between multiple profiles (Windows 11)

Assume you set up two profile dirs:

```text
C:\opencode-profiles\work
C:\opencode-profiles\personal
```

You can codify them:

```powershell
function Use-OpenCodeWork {
    $env:OPENCODE_CONFIG_DIR = "C:\opencode-profiles\work"
    Write-Host "Switched OpenCode to WORK profile"
}

function Use-OpenCodePersonal {
    $env:OPENCODE_CONFIG_DIR = "C:\opencode-profiles\personal"
    Write-Host "Switched OpenCode to PERSONAL profile"
}
```

Then:

```powershell
Use-OpenCodeWork
opencode run "work context"

Use-OpenCodePersonal
opencode run "personal context"
```

or in separate terminals, one profile per window.

For scripts in Python (what your SQD skill cares about):

```python
import os
import asyncio
import subprocess

async def run_opencode_with_profile(profile_dir: str, args: list[str]):
    env = os.environ.copy()
    env["OPENCODE_CONFIG_DIR"] = profile_dir
    proc = await asyncio.create_subprocess_exec(
        "opencode", *args,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()
```

Now you can choose the profile per call.

***

## 5. How this interacts with your SQLite / parallelism problem

Given the current design:

- Each **profile directory tends to carry its own config and local data**, including any DBs opencode writes under that tree.[1][3]
- If the SQLite DB path is derived from config/home, separate `OPENCODE_CONFIG_DIR` per process implies **separate DB files** → no cross‑profile lock contention.[8][9]
- This is exactly the sharding strategy we discussed: instead of “one opencode profile”, you use N.

You can:

- Keep your safe sequential path for the **single‑profile** case.
- Add a **sharded parallel dispatcher** that:
  - maps each model to a different `OPENCODE_CONFIG_DIR`,
  - runs them concurrently with `asyncio.gather`.

***

## 6. Summary answers to your bullets

1. **How to switch between multiple OpenCode profiles on Windows 11?**  
   Use different config directories and set `OPENCODE_CONFIG_DIR` per shell or subprocess; wrap it in small PowerShell functions or scripts.[2][3][1]

2. **Step‑by‑step setup for project‑specific configs?**  
   - Create a `.opencode-profile` directory in the project.  
   - Put `opencode.json` and optional agents/commands there.  
   - Ensure tools/scripts set `OPENCODE_CONFIG_DIR` to that path before calling `opencode`.[3][1]

3. **Does OpenCode support multiple auth profiles per provider like #5391?**  
   Not yet in a polished, documented way; it’s an open feature request tied to Provider Auth v2, so use separate configs/profiles as a workaround.[5][6][4]

4. **How to use `OPENCODE_CONFIG_DIR` for different setups?**  
   Treat each config directory as a “profile”; set `OPENCODE_CONFIG_DIR` in the environment before invoking `opencode`. On Windows 11, do this in PowerShell functions, project scripts, or Python subprocess env.[2][1][3]

If you’d like, next I can draft a minimal change to your `dispatch_parallel` that introduces a `profiles: list[str]` parameter and uses this to regain parallelism safely.

## Human

Does PI have the same issues?

## Assistant

Short answer: **no, PI does not have the same SQLite profile/locking issues in your context**—because it’s architecturally a very different thing from opencode.

### 1. Clarifying what “PI” is here

Inflection’s **Pi** is:

- A **hosted chatbot / assistant** running on Inflection’s infra (now largely on Azure).  
- You access it via web, mobile apps, or (if available) an API; storage and orchestration are entirely server‑side.[1][2]

It is **not**:

- A local CLI tool that you run as multiple subprocesses.  
- Something that uses a local SQLite DB on your machine in the way opencode does.

Therefore:

- There is **no local `pi` CLI + SQLite DB** to “lock” if you run several parallel requests.
- Concurrency limits are on **their side** (rate limits, session logic), not your local DB.

### 2. Do the same “SQLite is locked” dynamics apply?

For opencode:

- You have a **local binary + local SQLite DB**. Concurrent subprocesses hit the same file and you get `database is locked` when they overlap.[3][4][5]

For Pi:

- You make **network calls** to a remote service (or use their official client).  
- They use cloud storage / distributed services; any DBs involved are **remote and managed by Inflection/Azure**, not local SQLite on your PC.[1]

So:

- You **can** fire multiple Pi requests in parallel from Python (e.g., `asyncio.gather` with HTTP calls) without hitting a local SQLite lock.
- The bottlenecks become:
  - API rate limits / quotas.
  - Their own server‑side concurrency policies.
  - Your own client‑side connection limits.

Those are qualitatively different from opencode’s single‑file SQLite constraint.

### 3. When would “Pi” have SQLite issues?

The only way you’d see anything similar is if **you** introduce a local SQLite layer, e.g.:

- You log all Pi conversations in a local SQLite DB from your Python code.
- Then you hit that DB from multiple processes/threads without proper transaction / `busy_timeout` handling.

In that case, yes, you can get the generic “Python + SQLite + parallelism → database is locked” problem. But that is your own persistence layer, not something specific to Pi.[6][5][7]

### 4. Implication for your design

- With **opencode**: you *must* worry about process‑level DB contention and either serialize or shard profiles.
- With **Pi**: you can safely treat it like any other **HTTP LLM endpoint**: parallelize with `asyncio.gather`, no special DB lock hacks required.

So in your SQD / adversarial‑review architecture:

- If you swap some models over to Pi via direct HTTP/API calls, those slots can run fully in parallel.
- The only “sequentialization” you still need is for tools that themselves use shared local state like opencode’s SQLite DB.

If you tell me how you’re integrating Pi (web automation vs unofficial/official API wrapper), I can sketch an async pattern that plays nicely alongside your now‑sequential opencode calls.

## Human

You're talking about the wrong pie. I'm talking about the agent harness.  It allows you to use whatever LLM you want.

## Assistant

Got it—Pi the **terminal coding agent / harness**, not Inflection’s Pi.

Short answer: **no, Pi does not currently have the same SQLite “database is locked” profile that opencode has, and people aren’t reporting the same kind of DB‑locking failure mode.** But there are still limits you need to think about; they’re just different.

I’ll be explicit about what’s FACT vs CONSENSUS vs SPECULATION.

***

## 1. What Pi actually is (in our context)

From the public descriptions:[1][2][3][4]

- Pi is a **minimal terminal coding harness / agent toolkit**, written to be:
  - Small, composable, with in‑process TypeScript hooks.
  - Model‑agnostic: you can plug in whatever LLM backend you want.
- It’s designed as “your harness, your memory” rather than a big all‑in‑one environment like opencode.[3][4]

Crucially for your question:

- Its core design is *not* “a local CLI that fronts a shared SQLite DB in your home directory, then spawns subprocesses that fight over that file”.
- It’s engineered more like:
  - A long‑running Node/TypeScript process.
  - LLM calls and tools invoked from inside *one process* via hooks.[4][1]

So the whole “multiple CLI processes hitting the same SQLite DB file and locking it” failure mode is **not built into Pi’s default architecture**.

***

## 2. Does Pi use SQLite locally and have locking issues?

### FACT

- Pi’s core agent harness runs **in process**, and the platform is described as a programmable TS harness with hooks.[2][1][4]
- I don’t see any public documentation saying “Pi ships with a default SQLite store in `~/.pi` and you get `database is locked` if you run several instances in parallel”. Most discussion is about hooks, extensions, and model plumbing, not a global DB.[1][2][4]
- In community comparisons “Pi vs OpenCode vs Copilot CLI”, the trade‑offs are about:
  - Minimal harness vs heavyweight harness.
  - Extensibility vs built‑in features.
  - There is **no mention** of Pi having an opencode‑style SQLite contention problem.[5]

### CONSENSUS

Given:

- Pi runs as a **single process** by design (a harness loop calling an LLM with a small set of tools).[2][1]
- It doesn’t advertise a global shared SQLite DB as a core primitive.

Then:

- You won’t hit opencode’s specific “two separate CLI processes both touching the same SQLite DB” problem with the default Pi harness.
- Any persistence / DB you add is *your choice*: if you bolt an SQLite store into a Pi extension and then run **multiple Pi processes** against the same DB file, *then* you can reproduce the usual SQLite lock behavior—but that’s not Pi‑specific; that’s “you and SQLite”.

***

## 3. Concurrency model comparison: opencode vs Pi

### opencode (FACT)

- You typically **shell out** to `opencode` as a CLI from other tools (e.g. your SQD skill).
- opencode keeps a **local SQLite DB** in the user’s config/state directory.[6][7]
- Running multiple opencode processes concurrently against that DB can cause `SQLiteError: locking protocol` / `database is locked` errors.[7][8][6]
- Fix on your side: serialize those subprocess calls (your `for await` loop), or shard across multiple config dirs / DB files.

### Pi (agent harness) (FACT + CONSENSUS)

From the descriptions:[3][4][1][2]

- Pi is built as a **programmable, in‑process harness**:
  - You run Pi as a long‑lived agent process.
  - It calls the LLM and tools directly from within that process.
- It is explicitly designed to be **lightweight** compared to opencode’s heavier harness.[5][4]

Implications:

- When you use Pi the “normal” way (one harness per workspace/session), you are not spawning N independent Pi subprocesses that are all trying to hit some shared local SQLite DB.
- Concurrency is handled inside the harness: you can architect it to:
  - Allow multiple LLM calls in parallel (if your backend supports it).
  - Or keep things sequential.

The **SQLite lock** pattern only appears if:

- **You** choose SQLite as Pi’s memory store, and
- **You** run multiple Pi processes against the same DB file.

That’s not a Pi‑specific bug; that’s generic SQLite semantics.[8][9][10]

***

## 4. In your specific situation: does Pi avoid the opencode problem?

Given what you’re trying to do (long‑running harness, multiple models, adversarial review):

- With **opencode**:
  - You’re forced to serialize concurrent model runs (or shard profiles) because of its shared SQLite DB and CLI subprocess architecture.
- With **Pi**:
  - You can architect a **single Pi harness process** per workspace that:
    - Calls multiple LLMs either sequentially or in parallel (via HTTP APIs), and
    - Stores memory in whatever backend you choose (could be in‑memory, Redis, a proper DB, etc.).
  - There is no *inherent* single‑file SQLite choke point you must work around.

So your instinct is correct: **Pi doesn’t come with the same baked‑in SQLite DB lock issue opencode has.** You only get similar problems if you deliberately reintroduce SQLite as a shared file DB under concurrency.

***

## 5. What this means for your architecture choices

If you:

- Keep opencode as the dispatch layer → you must either:
  - Accept sequential model execution per profile, or
  - Shard profiles/DBs to parallelize.
- Move agent harnessing into **Pi** (or something Pi‑like you control) → you can:
  - Use direct LLM APIs and `asyncio.gather` for **real parallelism**.
  - Choose a storage backend that is actually designed for concurrency (Postgres, Redis, etc.), or keep persistence simple.

So from a harness‑engineering perspective:

- Pi is a better “blank canvas” if you care about **fine‑grained control over concurrency, storage, and model orchestration**.
- opencode is heavier, with a built‑in SQLite‑backed CLI design that constrains you unless you shard around it.

***

To tune recommendations: are you actively considering **migrating some of your SQD / adversarial review flow from opencode to Pi** as the harness, or are you more in a comparative evaluation phase right now?

## Human

Pi agent harness vs OpenCode and Claude Code: key tradeoffs in flexibility, extensibility, and multi-LLM support that developers debate
How to install and set up Pi agent harness on Windows 11
What LLMs are recommended for use with Pi harness

## Assistant

Pi is the most flexible and hackable of the three, OpenCode is the broadest “open harness” with lots of built-ins, and Claude Code is the most polished but the least provider-agnostic. Pi’s main appeal in developer debates is that it keeps the core tiny and lets you bring your own models, tools, and workflow rather than accepting a large opinionated harness.[1][2][3]

## Key tradeoffs

| Tool | Flexibility | Extensibility | Multi-LLM support | Main tradeoff |
|---|---|---|---|---|
| **Pi agent harness** | Very high; intentionally minimal and adaptable to custom workflows.[4][3] | Very high; extensions/packages can be installed from npm or git, and the core is designed to be modified without forking.[1][4] | Strong; supports 15+ providers and model switching mid-session, including Anthropic, OpenAI, Google, Azure, Bedrock, Mistral, Groq, Cerebras, xAI, Hugging Face, Kimi, MiniMax, OpenRouter, and Ollama.[1] | You trade built-in scaffolding for control; fewer baked-in agent conveniences than heavier harnesses.[3] |
| **OpenCode** | High, but more opinionated than Pi because it comes with a larger built-in harness and UX surface.[2][5] | High; configs, agents, commands, modes, plugins, and multiple config directories are supported.[6][7] | Very strong; community comparisons describe broad provider coverage and especially good local-model support.[2] | More moving parts, more internal state, and more harness constraints, including the SQLite-backed local state issues you’ve been hitting.[8][9] |
| **Claude Code** | Moderate; optimized around Anthropic’s workflow and UX rather than maximum customization.[10][11] | Lower than Pi/OpenCode in practice; developers debate it as the most polished, but not the most open-ended.[10][11] | Limited compared with Pi/OpenCode because it is centered on Claude rather than being a neutral multi-provider router.[10][11] | Best out-of-box experience for many users, but less appealing if you want provider switching, local models, or deep harness engineering.[10][11] |

## What developers debate

The recurring debate is basically “small smart core + big model” versus “feature-rich harness.” Pi is praised for using only a few built-in tools and relying on strong models plus user-defined extensions, while OpenCode is valued for richer built-in capabilities and a more complete terminal app experience. Claude Code is often described as faster and more polished in execution, but less attractive if your priority is model pluralism, local/offline use, or custom orchestration patterns.[2][3][10][11]

A second debate is **agent philosophy**. Pi explicitly avoids baking in things like sub-agents and heavy orchestration, with some advocates preferring tmux or external orchestration instead; OpenCode and Claude Code lean more toward integrated agent workflows. For someone like you doing harness engineering, Pi is usually the better substrate if you want to own the control plane rather than negotiate with a product’s built-in assumptions.[3][12][4]

## Windows 11 setup

The current Pi coding agent is distributed via npm as `@mariozechner/pi-coding-agent`, and public setup guides show Windows installs using a global npm install followed by initial provider login / configuration.[13][4]

### Install steps

1. Install **Node.js** first if you do not already have it, because Pi is distributed as an npm package.[4]
2. Open **PowerShell** or Windows Terminal.
3. Install Pi globally:
   ```powershell
   npm install -g @mariozechner/pi-coding-agent
   ```
   This is consistent with the npm package listing and Windows walkthroughs.[13][4]
4. Verify it is available:
   ```powershell
   pi --help
   ```
5. Start Pi:
   ```powershell
   pi
   ```
6. Configure providers / auth using Pi’s config flow or commands; the public site documents package/config commands like `pi config`, `pi install`, `pi update`, and `pi list`.[1]

### Package and extension setup

Pi supports installing extensions from npm or git, for example:

```powershell
pi install npm:@foo/pi-tools
pi install git:github.com/badlogic/pi-doom
```

It also supports testing an extension without permanent install:

```powershell
pi -e git:github.com/user/repo
```

Those package-management commands are documented on the public Pi site.[1]

### Windows notes

On Windows 11, the safest path is:

- Use **PowerShell 7** or Windows Terminal.
- Ensure `npm` global binaries are on `PATH`.
- If you rely on shell-heavy workflows, Git Bash or WSL can still be useful, but Pi itself is presented as a terminal tool installable via npm rather than Linux-only tooling.[4][13]

## Recommended models for Pi

There is no single “official best model,” because Pi’s design assumption is that you choose the model based on cost, speed, and how much harness help you want. Public discussion consistently recommends **strong coding-capable models with minimal prompting overhead**.[14][2][3]

### Commonly recommended categories

- **Top-tier API models** for hardest tasks: Claude-class frontier models are often used when you want maximal coding reliability and can pay for it.[10][3]
- **OpenRouter / multi-provider models** for flexibility: community discussion mentions MiniMax, Kimi, Mistral, Qwen, and other open/open-weight options as practical Pi pairings.[14][1]
- **Local/offline or semi-local models** for privacy/cost: comparisons mention Qwen coder variants, Devstral, GLM-class models, and Ollama-backed setups as attractive with Pi’s minimal harness.[2][1]

### Practical picks by use case

- **Best quality:** Claude-class frontier model via API.[3][10]
- **Best flexibility / routing:** OpenRouter-backed mix of Anthropic + Qwen + MiniMax/Kimi options.[14][1]
- **Best local-first setup:** Ollama with a strong coding-tuned model, accepting some drop in reliability versus frontier APIs.[2][1]

## Best fit by persona

- Choose **Pi** if you want a programmable harness, multi-LLM freedom, extension packaging, and low harness overhead.[3][4]
- Choose **OpenCode** if you want an open alternative with more built-in surface area and a fuller terminal product out of the box.[6][2]
- Choose **Claude Code** if you want the smoothest integrated experience and are okay with a more provider-specific workflow.[11][10]

Uncertainty: the Pi ecosystem is moving fast, and a lot of usage guidance is community-driven rather than formal enterprise-grade docs, so exact “best model” advice changes quickly with benchmark and pricing shifts.[4][14]

If you want, I can next give you a **Windows 11 Pi setup optimized for your stack**: PowerShell 7, OpenRouter, Ollama fallback, and a model shortlist for coding + adversarial review.

## Human

Common issues installing Pi agent harness on Windows 11
How to configure multiple LLM providers in Pi agent harness

## Assistant

Common Windows 11 Pi issues are mostly **Node/npm path problems, Windows-specific dependency downloads, and a few packaging bugs**, not the SQLite-style harness-state problems you saw with OpenCode. Pi’s provider configuration is comparatively flexible: it supports 15+ providers, API-key or OAuth auth, mid-session model switching, and custom providers/models via `models.json` or extensions.[1][2][3][4][5]

## Common install issues

The most frequently reported Windows 11 setup issues are these:[2][3][1]

- **Node/npm not installed or too old.** Most setup guides start by verifying `node -v` and `npm -v` before installing Pi globally with npm.[1]
- **`pi` command not found after install.** This usually means the npm global bin path is not on `PATH`, or the terminal was not restarted after install.[1]
- **Windows dependency/bootstrap failures.** One reported issue shows Pi failing on a fresh Windows install while downloading `fd`; the documented workaround was to run Pi from **Windows Terminal → Git Bash**, which completed the install successfully.[2]
- **Packaging/import bugs on Windows.** There is at least one Windows bug report where a missing `changelog.js` file caused the CLI to fail immediately after installation.[3]

## Windows 11 install checklist

Use this order on Windows 11 to minimize friction:[6][2][1]

1. Install a current **Node.js** release so `node` and `npm` are available.[6][1]
2. Open **PowerShell 7**, Windows Terminal, or Git Bash.[2][1]
3. Install Pi globally:
   ```powershell
   npm install -g @mariozechner/pi-coding-agent
   ```
   That package name is current on npm.[6]
4. Verify:
   ```powershell
   node -v
   npm -v
   pi --help
   ```
5. If `pi` launches but fails during first-run downloads on native Windows, try **Git Bash inside Windows Terminal** as the first fallback.[2]
6. If the CLI crashes immediately after install, check whether you’ve hit a known Windows packaging bug rather than a config mistake.[3]

## How to configure multiple providers

Pi explicitly supports many providers and multiple ways to define them.[4][5]

### Built-in provider approach

Pi’s public docs/site state that it supports providers including:

- Anthropic
- OpenAI
- Google
- Azure
- Bedrock
- Mistral
- Groq
- Cerebras
- xAI
- Hugging Face
- Kimi
- MiniMax
- OpenRouter
- Ollama[5]

Authentication methods:

- **API keys**
- **OAuth**, where supported[5]

The public guidance also says provider auth can be configured through **environment variables or Pi’s own config flow**.[4]

### Practical pattern

A common setup pattern is:

- Keep provider secrets in environment variables.
- Use Pi config / model commands to select defaults.
- Switch models per task with `/model` or `Ctrl+L`.[5]

For example, in PowerShell you might define env vars for several providers before launching Pi:

```powershell
$env:ANTHROPIC_API_KEY = "..."
$env:OPENAI_API_KEY = "..."
$env:GOOGLE_API_KEY = "..."
$env:OPENROUTER_API_KEY = "..."
$env:MISTRAL_API_KEY = "..."
$env:OLLAMA_HOST = "http://localhost:11434"

pi
```

Inside Pi, you can then switch models mid-session using `/model` or `Ctrl+L`.[5]

## Custom providers and models

Pi’s public docs explicitly say you can add custom providers and models via:

- `models.json`
- Extensions/packages[5]

That matters because Pi’s philosophy is not “only use the built-in provider list.” It is designed to let you:

- Add model aliases
- Add provider wrappers
- Build packages/extensions that define your own toolchains and provider behavior[7][5]

So if you want:

- OpenRouter for most frontier routing
- Ollama for local fallback
- Direct Anthropic for highest-quality runs
- A niche provider like MiniMax or Kimi for specific coding workloads

Pi is architecturally a good fit for that mix.[4][5]

## Recommended provider setup on Windows

For a stable multi-provider Windows 11 setup, I’d use this pattern:

- **Primary quality:** Anthropic and/or OpenAI keys.[5]
- **Routing layer:** OpenRouter for breadth and quick experiments.[5]
- **Local fallback:** Ollama for offline/private tasks.[5]
- **Fast/cheap specialists:** Groq, Mistral, Kimi, or MiniMax as optional extras depending on your preferences.[5]

That gives you:
- direct premium providers for critical tasks,
- a router for model shopping,
- and a local escape hatch.

## Important difference from OpenCode

With Pi, multi-provider configuration is a **feature of the harness design**, not a workaround. The main operational issues on Windows are installation polish and provider/auth setup, whereas OpenCode’s problem in your case was shared local harness state and concurrency around SQLite.[8][9][5]

If you want, I can give you a **concrete Windows 11 Pi config recipe** for your stack: Anthropic + OpenRouter + Ollama + Gemini, with PowerShell env setup and a sane default model menu.

## Human

Best models for coding in Pi from multiple providers
Pi agent harness extensions for custom LLM providers

## Assistant

For Pi, the strongest coding setup is usually **one best-in-class frontier model plus a few cheaper/specialized backups from other providers**, because Pi makes model switching cheap and doesn’t force a single-provider workflow. Its extension system is also unusually open: you can add custom providers and models through `models.json`, or register full custom providers in TypeScript via `pi.registerProvider()` and related extension hooks.[1][2][3][4]

## Model choices

Public discussion around Pi consistently recommends pairing the minimal harness with strong coding-capable models rather than relying on lots of baked-in scaffolding.[5][1]

| Use case | Good fit in Pi | Why people pick it |
|---|---|---|
| **Highest-quality coding** | Claude-class frontier models via Anthropic or OpenRouter.[1][6] | Developers describe Pi as working best when you “bring a strong model” and let the lightweight harness stay out of the way.[5][1] |
| **Cheap fast coding** | Groq, Cerebras, or smaller fast models exposed through supported providers.[2] | Good for iterative edits, repo scans, and low-stakes tool-driving where latency matters more than depth.[2] |
| **Open-model experimentation** | Qwen coder variants, Devstral, GLM-class models, or similar models routed through OpenRouter, Hugging Face, Ollama, or other providers.[5][7] | Pi is often praised for local/open-model friendliness and low harness overhead.[5][7] |
| **Local/private fallback** | Ollama-hosted coding models.[2][7] | Useful for privacy, cost control, and offline work, though quality may trail top frontier APIs.[2][7] |

## Practical recommendations

A solid multi-provider Pi stack usually looks like this:[7][2][5]

- **Primary “best answer” model:** a Claude-class frontier model.
- **Secondary fast model:** a low-latency provider such as Groq/Cerebras class offerings for quick edits or exploratory tasks.
- **Open-model option:** Qwen/Devstral/GLM-family model via OpenRouter, Hugging Face, or Ollama.
- **Local fallback:** Ollama if you want an offline or private path.

For your style of work, the most rational pattern is probably:
- Frontier model for planning/review.
- Faster cheaper model for mechanical edits.
- Local/open model for overflow, privacy-sensitive work, or experiments.

## What Pi supports natively

Pi’s public site says it supports **15+ providers and hundreds of models**, including Anthropic, OpenAI, Google, Azure, Bedrock, Mistral, Groq, Cerebras, xAI, Hugging Face, Kimi, MiniMax, OpenRouter, and Ollama. It also supports switching models mid-session with `/model` or `Ctrl+L`, and cycling favorites with `Ctrl+P`.[2]

That makes Pi especially good for:
- provider hedging,
- model A/B testing,
- keeping different cost/latency tiers available without changing harnesses.[1][2]

## Extensions for custom providers

Pi is not just configurable; it is meant to be extended. Official docs describe extensions as TypeScript modules that can subscribe to lifecycle events, add commands, add tools, and modify provider requests.[3]

Key extension capabilities include:[4][3]

- `pi.registerTool(...)` to add new LLM-callable tools.[3]
- `pi.registerCommand(...)` to add user commands.[3]
- `pi.on(...)` lifecycle hooks such as `before_provider_request` to intercept and modify provider payloads.[3]
- `pi.registerProvider()` to register a **custom model provider** directly.[4]

The custom-provider docs explicitly say this can be used for things like:
- routing through **proxies**,
- sending requests through **API gateways**,
- and integrating nonstandard providers into the Pi model system.[4]

## Lightweight vs full custom provider

You have two levels of customization in Pi:[2][4][3]

1. **`models.json`**
- Best when you just need aliases, model definitions, or simple provider/model additions without building logic.[2]

2. **TypeScript extension**
- Best when you need behavior, such as:
  - custom auth flows,
  - routing logic,
  - request rewriting,
  - model-specific prompt shaping,
  - provider failover,
  - enterprise proxy integration.[4][3]

That is the main reason developers who care about harness engineering like Pi: features that other tools hardcode can be rebuilt in your own extension layer.[2][3]

## Extension placement

Official extension docs say auto-discovered extensions live in either:[3]

- `~/.pi/agent/extensions/` for global use
- `.pi/extensions/` for project-local use

For quick tests, you can also run Pi with a direct extension path using `pi -e ./path.ts`. Auto-discovered extensions can be hot-reloaded with `/reload`.[3]

## Best takeaway

If your goal is **best coding results**, Pi is usually strongest when you pair it with:
- one top-tier frontier model,
- one fast cheap model,
- and one local/open fallback.[5][2]

If your goal is **custom provider engineering**, Pi is one of the better terminal agents to bet on because it exposes both:
- config-level model definitions, and
- real TypeScript hooks for provider registration and request interception.[4][3]

Uncertainty: “best model” changes quickly because pricing, latency, and coding quality move fast, and much of the Pi advice is still community-driven rather than benchmark-standardized vendor guidance.[6][5]

If you want, I can turn this into a **concrete Pi provider strategy for your stack**: Anthropic + OpenRouter + Ollama + one custom provider shim, with a recommended model role matrix for coding, review, and long-context analysis.

## Human

how do I add api keys to PI?

## Assistant

You add API keys to Pi in either of two standard ways: **environment variables** or Pi’s **auth file** at `~/.pi/agent/auth.json`. Pi’s docs explicitly say API-key providers can be configured through environment variables or the auth file, while some subscription-based providers use OAuth instead.[1][2]

## Fastest way

For Windows 11, the quickest method is to set environment variables in PowerShell before launching Pi.[2]

Example:

```powershell
$env:ANTHROPIC_API_KEY = "your-key-here"
$env:OPENAI_API_KEY = "your-key-here"
$env:GEMINI_API_KEY = "your-key-here"
$env:OPENROUTER_API_KEY = "your-key-here"
$env:GROQ_API_KEY = "your-key-here"
$env:MISTRAL_API_KEY = "your-key-here"
$env:OLLAMA_HOST = "http://localhost:11434"

pi
```

That works because Pi maps providers to specific env var names such as `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, and others.[3][2]

## Common env var names

Pi’s published provider mapping includes these examples:[2][3]

- Anthropic → `ANTHROPIC_API_KEY`
- OpenAI → `OPENAI_API_KEY`
- Google Gemini → `GEMINI_API_KEY`
- Mistral → `MISTRAL_API_KEY`
- Groq → `GROQ_API_KEY`
- Cerebras → `CEREBRAS_API_KEY`
- xAI → `XAI_API_KEY`
- OpenRouter → `OPENROUTER_API_KEY`
- MiniMax → `MINIMAX_API_KEY`
- Kimi → `KIMI_API_KEY`
- Hugging Face → `HF_TOKEN`
- Z.ai → `ZAI_API_KEY`[3]

## Persistent setup on Windows 11

If you want the keys available every time you open PowerShell, use persistent user-level environment variables instead of setting `$env:` each session.[2]

Example:

```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-key-here", "User")
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "your-key-here", "User")
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key-here", "User")
```

Then close and reopen your terminal before running `pi`.

## Auth file option

Pi also supports storing credentials in an auth file instead of env vars, specifically:

```text
~/.pi/agent/auth.json
```

That path is documented both in install/docs material and the SDK examples.[4][3][2]

If you prefer file-based credentials, Pi’s docs say to store them in that auth file rather than environment variables. The exact schema may vary by provider/version, so if you use the file route, it is safer to let Pi generate/manage it if the CLI offers an auth flow for that provider, rather than hand-authoring JSON blindly.[1][2]

## OAuth vs API keys

Not every provider uses API keys in the same way. Pi’s docs distinguish between:

- **API key providers** → env vars or auth file
- **Subscription/OAuth providers** → authenticated with OAuth instead[5][1]

So if a provider in Pi prompts for OAuth, that is expected behavior and not a sign your env vars are wrong.[5][1]

## If you use Pi programmatically

If you are embedding Pi via its SDK, it also supports runtime-only key injection without persisting to disk. The SDK examples show `AuthStorage.create()` using `~/.pi/agent/auth.json` by default, and `authStorage.setRuntimeApiKey("anthropic", "...")` for temporary runtime overrides.[4]

## Recommended approach for your stack

For your workflow, I’d use:

- **Environment variables** for local dev and scripting, because they’re easy to swap per shell/profile.[3][2]
- **Auth file** only if you specifically want Pi-managed credential storage across sessions.[4][2]

A practical Windows 11 combo would be:

```powershell
$env:ANTHROPIC_API_KEY = "..."
$env:OPENROUTER_API_KEY = "..."
$env:GEMINI_API_KEY = "..."
$env:ZAI_API_KEY = "..."
$env:MINIMAX_API_KEY = "..."
$env:OLLAMA_HOST = "http://localhost:11434"
pi
```

That gives you frontier, router, and local options in one Pi session.[5][3]

If you want, I can next give you a **ready-to-paste PowerShell profile snippet** that sets up Anthropic + OpenRouter + Gemini + Ollama + Z.ai for Pi cleanly on Windows 11.

## Human

what's the best way to do this on windows 11?

## Assistant

Best way for you on Windows 11: **use user‑level environment variables + a Pi‑specific launch function in your PowerShell profile.** That gives you:

- One place to edit API keys.
- Clean separation between “normal shell” and “Pi shell.”
- No hard‑coding secrets in repos.

Below is a concrete, minimal setup.

***

## 1. Store keys as user‑level env vars (one‑time setup)

Run this once in a PowerShell 7 window (replace `"..."` with real keys):

```powershell
# Frontier / router / cloud
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY",   "...", "User")
[Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY",  "...", "User")
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY",      "...", "User")
[Environment]::SetEnvironmentVariable("ZAI_API_KEY",         "...", "User")
[Environment]::SetEnvironmentVariable("MINIMAX_API_KEY",     "...", "User")

# Local models
[Environment]::SetEnvironmentVariable("OLLAMA_HOST",         "http://localhost:11434", "User")
```

Why this pattern:

- Pi reads provider keys from env vars like `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `ZAI_API_KEY`, `MINIMAX_API_KEY`, `OLLAMA_HOST`.[1][2]
- `"User"` scope makes them available to all new terminals but not system‑wide services.[1]

Then **close and reopen** Windows Terminal / PowerShell so the new vars are visible.

***

## 2. Add a `Start-Pi` function to your PowerShell profile

In PowerShell:

```powershell
notepad $PROFILE
```

Append:

```powershell
function Start-Pi {
    Write-Host "Starting Pi with configured API keys..." -ForegroundColor Cyan

    # Optional sanity checks
    $required = @(
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY",
        "GEMINI_API_KEY",
        "ZAI_API_KEY",
        "MINIMAX_API_KEY"
    )

    $missing = $required | Where-Object { -not $env:$_ }

    if ($missing.Count -gt 0) {
        Write-Warning "Missing API keys for: $($missing -join ', ')"
        Write-Warning "Pi will still start, but some providers won't work."
    }

    pi
}
```

Restart the terminal; now you can just run:

```powershell
Start-Pi
```

Benefits:

- Keeps your normal sessions clean.
- Sanity check warns if you forgot to set a key (or revoked one).

***

## 3. Optional: project‑specific overrides

If you want different keys or providers per project (e.g., testing vs prod):

```powershell
function Start-PiProject {
    param(
        [string]$Env = "dev"  # or "prod"
    )

    if ($Env -eq "prod") {
        $env:ANTHROPIC_API_KEY  = "...prod..."
        $env:OPENROUTER_API_KEY = "...prod..."
    } else {
        $env:ANTHROPIC_API_KEY  = "...dev..."
        $env:OPENROUTER_API_KEY = "...dev..."
    }

    pi
}
```

This temporarily overrides user‑level vars only for that shell.

***

## 4. When to use `auth.json` instead

Pi also supports an auth file at:

```text
~/.pi/agent/auth.json
```

for storing credentials instead of env vars.[2][3][1]

On Windows, I’d only use this if:

- You specifically want Pi’s SDK/AuthStorage to manage credentials across tools, or
- You’re scripting Pi from other processes that expect file‑based auth.[3]

Given your workflow (PowerShell, multiple providers, a lot of experimentation), **env vars + a launch function** is the cleanest, least fragile approach.

***

If you tell me your exact provider set (Anthropic + OpenRouter + Gemini + Z.ai + MiniMax + Ollama?), I can give you a ready‑to‑paste `$PROFILE` block with all the right var names and a `Start-Pi` that prints which providers are currently “armed.”

## Human

auth.json I'd rather use this.

## Assistant

Yes — if you prefer `auth.json`, that’s a valid first-class path in Pi. Pi stores credentials in `~/.pi/agent/auth.json`, and that file holds either plain API keys or OAuth credential objects depending on provider.[1][2][3]

## Best way on Windows 11 with `auth.json`

Use `auth.json` if you want:

- one Pi-specific credential store,
- no dependence on shell env vars,
- easier backup / migration of Pi config.[4][2]

The main caveat: **API keys are plain text in JSON**, so treat the file like a secret and keep it out of repos, sync tools, and screenshots.[3]

## File location

On Windows, `~/.pi/agent/auth.json` resolves under your user profile, typically something like:

```text
C:\Users\YOURNAME\.pi\agent\auth.json
```

Pi’s docs and SDK examples use that exact logical path as the default auth store.[2][4]

## Likely file shape

Pi’s docs and SDK references indicate `auth.json` is a **flat JSON object keyed by provider name**, where each value is either an API key entry or an OAuth credential object.[5][6]

For API-key providers, the safe working assumption is a structure like this:

```json
{
  "anthropic": {
    "type": "api-key",
    "apiKey": "sk-ant-..."
  },
  "openrouter": {
    "type": "api-key",
    "apiKey": "sk-or-..."
  },
  "google": {
    "type": "api-key",
    "apiKey": "AIza..."
  },
  "zai": {
    "type": "api-key",
    "apiKey": "..."
  },
  "minimax": {
    "type": "api-key",
    "apiKey": "..."
  }
}
```

That matches the documented distinction between API-key entries and OAuth entries, but I want to be precise: **I have not verified the exact JSON schema for every provider from a primary example page**, so treat the provider keys like `anthropic`, `openrouter`, `google`, `zai`, `minimax` as highly likely rather than guaranteed.[6][5]

## Best practical setup

The lowest-risk way is:

1. Let Pi create / touch the auth store once if possible.
2. Then edit `auth.json` manually for API-key providers.
3. Keep OAuth-managed providers separate if Pi wants to own those tokens.

### Step-by-step

1. Create the folder if it doesn’t exist:

```powershell
New-Item -ItemType Directory -Force "$HOME\.pi\agent"
```

2. Create or edit the file:

```powershell
notepad "$HOME\.pi\agent\auth.json"
```

3. Put in a JSON object with your providers.

A practical starter template:

```json
{
  "anthropic": {
    "type": "api-key",
    "apiKey": "YOUR_ANTHROPIC_KEY"
  },
  "openrouter": {
    "type": "api-key",
    "apiKey": "YOUR_OPENROUTER_KEY"
  },
  "google": {
    "type": "api-key",
    "apiKey": "YOUR_GEMINI_KEY"
  },
  "zai": {
    "type": "api-key",
    "apiKey": "YOUR_ZAI_KEY"
  },
  "minimax": {
    "type": "api-key",
    "apiKey": "YOUR_MINIMAX_KEY"
  }
}
```

4. Save the file.
5. Start Pi and test model selection.

## Windows security hygiene

Because the file contains plain secrets, do these:

- Add `C:\Users\YOURNAME\.pi\agent\auth.json` to anything you use for plaintext backup exclusions if needed.
- Never commit `auth.json`.
- If you copy Pi config between machines, copy it securely and rotate keys if the file was ever exposed.[3]

Pi’s implementation also writes the file with restrictive permissions in Unix-like environments, but Windows ACL behavior is different, so don’t assume Linux-style `chmod 600` semantics apply exactly on Windows.[3]

## OAuth providers

Some providers use OAuth rather than static keys. Pi’s docs show OAuth credentials are also stored in the same `auth.json`, but as a more complex object including refreshed tokens and expiry metadata. For those, manual editing is a worse idea; let Pi’s login flow populate them.[6][3]

## Recommendation for you

Given your setup, I’d use `auth.json` for:

- Anthropic
- OpenRouter
- Gemini/Google
- Z.ai
- MiniMax

and keep Ollama out of `auth.json` unless Pi explicitly expects a credential entry for it, since local providers often just rely on host settings rather than a secret key.[7][3]

One uncertainty remains: the **exact provider identifiers** Pi expects in `auth.json` for every service. The safest next move is to verify that once from Pi’s provider docs or source examples before you paste five real keys into the file.

If you want, I can do one more pass and give you a **provider-by-provider `auth.json` skeleton with the exact Pi provider IDs** for Anthropic, OpenRouter, Gemini, Z.ai, MiniMax, and Ollama.
