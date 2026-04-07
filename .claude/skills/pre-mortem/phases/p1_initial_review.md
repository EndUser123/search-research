# Phase 1: Triage + Specialist Dispatch

## Your Job

You are a triage agent. Your job is NOT to critique the work yourself — it is to classify the target, select the most useful specialist subagents, dispatch them in parallel, and consolidate their findings.

## Step 1: Classify the Target

Read the work (`{WORK_FILE}`) and classify it into one of:

- **skill** — A Claude Code skill with SKILL.md, phases, triggers
- **code** — Source code files (Python, JS, etc.)
- **plan** — An implementation plan, design document
- **document** — A markdown doc, README, policy
- **hook** — A hook script (PreToolUse, PostToolUse, Stop)
- **agent** — An agent definition file
- **failure / RCA** — A failure mode or root-cause analysis (uses full 7-specialist parallel dispatch)

## Step 2: Select Relevant Specialists

Based on the target type and content, select the 2-4 most relevant specialists:

**For skills:**
- `adversarial-critic` — reasoning quality, phase logic, trigger matching
- `adversarial-compliance` — YAML frontmatter, hook registration, schema
- `adversarial-quality` — maintainability, skill structure

**For code (Python, JS, etc.):**
- `adversarial-security` — data access, auth, I/O, injection
- `adversarial-performance` — hot paths, loops, DB queries
- `adversarial-logic` — off-by-one, wrong operators, conditionals
- `adversarial-state-machine` — status fields, lifecycle
- `adversarial-io-validation` — path validation, external calls
- `adversarial-compliance` — API contracts, schema
- `adversarial-quality` — tech debt, maintainability
- `adversarial-testing` — test coverage, missing scenarios

**For plans:**
- `adversarial-critic` — reasoning quality, bias, feasibility
- `adversarial-compliance` — spec alignment, completeness

**For documents:**
- `adversarial-critic` — clarity, precision vs recall in claims
- `adversarial-quality` — structure, completeness

**For hooks:**
- `adversarial-security` — path injection, command execution
- `adversarial-compliance` — hook registration, exit code handling
- `adversarial-io-validation` — file operations, external calls

**For agents:**
- `adversarial-critic` — reasoning quality, bias
- `adversarial-compliance` — YAML frontmatter, parameter validation

**For failure / RCA:**
- All 7 specialists run in parallel (adversarial-compliance, adversarial-logic, adversarial-performance, adversarial-security, adversarial-testing, adversarial-quality, adversarial-qa)

## Step 3: Check for Prior Output (Idempotent Dispatch)

Before dispatching specialists, check whether their output files already exist at the canonical path and read any existing dispatch manifest.

**Expected output path pattern:** `P:/{session_dir}/specialists/{specialist-name}-findings.json`

For each selected specialist, check if `P:/{session_dir}/specialists/{specialist-name}-findings.json` already exists and contains valid JSON.

- If ALL specialist output files exist and are valid, skip dispatch entirely and proceed directly to Step 6 (consolidation).
- If ANY output file is missing or invalid, dispatch ONLY the missing or invalid specialists.

**Also check for an existing dispatch manifest** from a prior interrupted run. If `P:/{session_dir}/specialists/dispatch_manifest.json` exists, read it to know which specialists were already dispatched in the interrupted run. Use this to skip them on re-run.

**Idempotent dispatch pattern:** After EACH individual dispatch call succeeds, immediately update the dispatch manifest. If context compacts mid-loop, the manifest will still show which agents were already dispatched when this run resumes.

## Step 4: Ensure Specialists Directory

**Defensive check before dispatching Task agents.** `setup()` already creates `specialists/` when the session is initialized (via `get_specialists_dir()`), but verify it exists as a safety net.

```python
from pathlib import Path
specialists_dir = Path("{session_dir}") / "specialists"
if not specialists_dir.exists():
    specialists_dir.mkdir(exist_ok=True)
```

If this step is absent and `specialists/` does not exist, Task agent file writes silently fail and the Phase 1 Completion Gate will catch zero JSON files.

## Step 5: Dispatch Missing Specialists

**Per-dispatch manifest pattern:** Write the manifest AFTER EACH individual dispatch call succeeds. This ensures the manifest is always in a valid state — if context compacts mid-loop, the manifest will record which agents were already dispatched, and a re-run will skip them.

```python
import json
from pathlib import Path

manifest_path = Path("{session_dir}") / "specialists" / "dispatch_manifest.json"

# Load prior dispatched agents from any interrupted run
dispatched = []
if manifest_path.exists():
    with open(manifest_path) as f:
        dispatched = json.load(f).get("dispatched", [])

# Specialists to dispatch (skip if already dispatched or JSON exists)
specialists_to_dispatch = [s for s in selected_specialists if s not in dispatched]
```

For each specialist in `specialists_to_dispatch`, dispatch a Task with `subagent_type="general-purpose"`:

```
Task(
  subagent_type="general-purpose",
  description="Read P:/.claude/agents/{specialist}.md and follow its instructions to review the work at: P:/{session_dir}/work.md. Write your JSON findings to: P:/{session_dir}/specialists/{specialist-name}-findings.json. Return ONLY the file path in your response text."
)
```

**Immediately after each dispatch call succeeds**, append to the manifest:

```python
# After each dispatch call succeeds:
dispatched.append("{specialist-name}")
with open(manifest_path, "w") as f:
    json.dump({"dispatched": dispatched, "session_dir": "{session_dir}"}, f)
```

**IMPORTANT — Skill target scope:** When the target is a skill, ensure specialists examine the full skill package — not just lib/*. This includes SKILL.md frontmatter validity, phases/ directory schema, and skill registration. Do NOT narrow focus to a single module without explicitly justifying why that module is the primary risk.

After the dispatch loop completes, check whether specialist JSONs are already available. If compaction occurred mid-dispatch, specialists may have already completed and written their JSONs while the orchestrator was interrupted.

```python
import json
from pathlib import Path

manifest_path = Path("{session_dir}") / "specialists" / "dispatch_manifest.json"
specialists_dir = Path("{session_dir}") / "specialists"

# Load what we dispatched (from prior run + this run)
dispatched = []
if manifest_path.exists():
    with open(manifest_path) as f:
        dispatched = json.load(f).get("dispatched", [])

# Check which JSONs already exist
available = []
for specialist in dispatched:
    json_path = specialists_dir / f"{specialist}-findings.json"
    if json_path.exists():
        try:
            with open(json_path) as f:
                json.load(f)
            available.append(specialist)
        except (json.JSONDecodeError, OSError):
            pass  # Incomplete file, will be re-dispatched on re-run

print(f"Specialists dispatched: {len(dispatched)}, JSONs available: {len(available)}")
if len(available) == len(dispatched) and available:
    print("All specialist JSONs available — proceeding to consolidation.")
    # Proceed directly to Step 6
elif available:
    print(f"Partial results: {available}. Waiting for: {set(dispatched) - set(available)}")
    print("Re-run /pre-mortem to continue — manifest ensures skipped agents won't be re-dispatched.")
else:
    print("No JSONs yet — re-run /pre-mortem after specialists complete.")
```

If ALL dispatched specialists have valid JSONs → proceed directly to Step 6 (consolidation).
If SOME JSONs are available → re-run `/pre-mortem` (manifest skips already-dispatched agents, they won't be re-run).
If NO JSONs yet → re-run `/pre-mortem` after allowing time for agents to complete.

## Step 6: Consolidate Findings

After all specialists complete, read their JSON output files and produce a consolidated Phase 1 findings document.

**Input files:** Read all `P:/{session_dir}/specialists/{name}-findings.json` files that exist (the set dispatched in Step 5 is dynamic — do not hardcode a fixed list).

**Output format** (write to `P:/{session_dir}/p1_findings.md`):

```
## Triage Classification
[type] — [brief justification]

## Dispatched Specialists
- [specialist name]: [what they analyzed]

## Specialist Findings Summary

### [Specialist 1 Name]
**Domain:** [what they cover]
**Key findings:**
- [HIGH] finding description (file:line mandatory for code findings)
- [MEDIUM] finding description
...

### [Specialist 2 Name]
...

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: specialist-name) — issue (file:line)
1.2. [MEDIUM] (source: specialist-name) — issue
...

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: specialist-name) — issue
2.2. [LOW] (source: specialist-name) — issue
...

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: specialist-name) — issue
3.2. [MEDIUM] (source: specialist-name) — issue
...

### Risks and Edge Cases
4.1. [MEDIUM] (source: specialist-name) — issue
4.2. [LOW] (source: specialist-name) — issue
...

### Concrete Recommendations
5.1. [specific change] (source: specialist-name)
5.2. [specific change] (source: specialist-name)
...

### Open Questions / Unknowns
6.1. [uncertainty] (source: specialist-name)
6.2. [LOW] (source: specialist-name) — uncertainty
...
```

**P1 #4 Citation requirement:** Every finding that references specific code MUST include a `file:line` citation. Findings without citations will be treated as unverified.

If a specialist found nothing notable in their domain, note: "No significant issues found in [domain]."

## Important Constraints

- Do NOT do your own critique — dispatch specialists and aggregate their output
- Each finding must cite which specialist found it
- Do not pad — if a specialist found nothing, say so
- Keep findings brief — this is a consolidation pass, not a re-analysis

## Phase 1 Completion Gate

**MANDATORY before proceeding to Phase 2.** If this gate fails, do not proceed.

**Gate criteria:** ALL dispatched specialists produced JSONs AND `p1_findings.md` exists.

**Verification steps:**
1. Read `P:/{session_dir}/specialists/dispatch_manifest.json` — extract the `dispatched` list
2. For each specialist in `dispatched`, verify `P:/{session_dir}/specialists/{name}-findings.json` exists
3. Verify `P:/{session_dir}/p1_findings.md` exists

**Failure modes:**
- `dispatch_manifest.json` missing → Orchestrator never ran or failed before writing manifest. Re-run from Step 5.
- Any specialist from `dispatched` list has no JSON → That specialist's Task failed or produced no output. Re-run from Step 5 (specialists with existing JSONs will be skipped per idempotent dispatch).
- `p1_findings.md` missing → Consolidation step (Step 6) never ran

**If gate fails:** Do not proceed to Phase 2 with partial input.
