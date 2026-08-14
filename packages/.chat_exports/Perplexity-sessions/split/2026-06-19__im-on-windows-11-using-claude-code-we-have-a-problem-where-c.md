---
title: "I'm on windows 11 using claude code.  We have a problem where clause code doesn't use skills properly when manually invo"
date: "2026-06-19"
mode: "COPILOT"
uuid: "c8536d81-6bfd-42b5-b478-871aa2c11640"
entry_count: 5
---

## Human

I'm on windows 11 using claude code.  We have a problem where clause code doesn't use skills properly when manually invoked.  I asked a couple of LLMs to help architect a solution, but they have problems.

Skill-guard_full.md shows the skill-guard plugin I'm using that is trying to help make sure skills get used reliably, but it's not working optimally.

Here's a chat with LLM1:

And LLM2:
"TL;DR: To guarantee that manually invoked skills (like /gto) execute with absolute fidelity instead of being treated as soft prompt suggestions, you must wrap prompt-based guidance in deterministic, shell-level hook enforcements. By combining a UserPromptSubmit hook to intercept manual skill calls with a Stop hook acting as a final compliance gate, you can programmatically block Claude from finishing a turn if it skips crucial steps or bypasses mandated analysis scripts. On Windows 11, these hooks should be explicitly configured to run natively in PowerShell 7+ (pwsh.exe) to parse JSON payloads without syntax mismatches.
The Root Cause: Soft Guidance vs. Runtime Law
In Claude Code, skills are structurally prompt-based playbooks. Because LLMs operate probabilistically, even when a user explicitly initiates a specialized workflow like a Gap-to-Opportunity (gto) analysis, the model frequently suffers from semantic drift over long conversation turns. It may acknowledge your playbook instructions, but then choose to shortcut the execution loop—guessing details, skipping intermediate validation tools, or providing conversational advice instead of running structured analytical frameworks.
To achieve 100% execution fidelity, skill-guard must transition from an informational prompt system into an enforcement gate. This requires an event-driven architecture that controls the lifecycle boundaries of the tool execution loop.
Architectural Blueprint: The Dual-Gate Pattern
To enforce manual skill execution reliability, enhance skill-guard using a Dual-Gate Hook Pattern:
The Interception Layer (UserPromptSubmit): Listens for explicit manual triggers (e.g., text containing /gto or phrases invoking the Gap-to-Opportunity framework). It automatically rewrites the prompt on the fly or appends a non-negotiable metadata tracking state to the session's context.
The Compliance Evaluation Layer (Stop): Intercepts Claude when it tries to complete its turn and return control to the user. It validates that the required file reads, schema evaluations, or evidentiary findings were actually completed. If Claude skipped any steps, the gate returns an exit 2 block with the precise reason, forcing Claude back into the reasoning loop to finish its work correctly.
Step-by-Step PowerShell 7+ Implementation for Windows 11
On Windows 11, standard bash-centric shell scripts will fail or trigger environment mismatches. Claude Code natively supports directly executing hooks within PowerShell 7+ (pwsh.exe) by declaring "shell": "powershell" inside the configuration block.
1. Configure the Hooks in .claude/settings.json
Merge the following configuration into your project or global settings.json file. This binds the UserPromptSubmit and Stop events to deterministic PowerShell handlers.
JSON
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": {
          "query": ".*(/gto|gap-to-opportunity).*"
        },
        "handler": {
          "type": "command",
          "shell": "powershell",
          "command": "powershell.exe -ExecutionPolicy Bypass -File .claude/hooks/gto_intercept.ps1"
        }
      }
    ],
    "Stop": [
      {
        "matcher": {},
        "handler": {
          "type": "command",
          "shell": "powershell",
          "command": "powershell.exe -ExecutionPolicy Bypass -File .claude/hooks/gto_compliance_gate.ps1"
        }
      }
    ]
  }
}

2. Create the Intercept Handler (.claude/hooks/gto_intercept.ps1)
This script executes immediately when you manually type the command. It forces state tracking by writing an entry to a local operational log and injecting a strict system directive directly into the active prompt payload.
PowerShell
# Read Claude Code JSON event payload from stdin
$inputJson = $Input | Out-String | ConvertFromJson

# Create a structural lockfile indicating a GTO analysis is active
$LockPath = Join-Path $PSScriptRoot "gto_active.lock"
Set-Content -Path $LockPath -Value $inputJson.session_id

# Inject non-negotiable instruction reinforcement into the prompt context
$EnhancedContext = @"

[SYSTEM ENFORCEMENT: CRITICAL COMPLIANCE GATE ACTIVE]
You have been manually instructed to execute the 'gto' (Gap-to-Opportunity) skill. 
You are strictly forbidden from summarizing or using parameterized assumptions. 
You MUST explicitly perform the following analytical sequence:
1. Parse the schema architecture using Grep/Read tools.
2. Generate an intermediate findings checklist.
You cannot exit the turn or declare completion until these specific steps are populated.
"@

# Return decision back to Claude Code CLI engine
$Response = @{
    decision = "approve"
    additionalContext = $EnhancedContext
}

$Response | ConvertTo-Json -Compress

3. Create the Compliance Evaluator (.claude/hooks/gto_compliance_gate.ps1)
This script acts as the final enforcement mechanism when Claude attempts to close out the prompt loop. It checks for compliance and uses Claude Code’s exit 2 protocol to reject lazy or incomplete outputs.
PowerShell
# Check if a GTO analysis session is currently locked
$LockPath = Join-Path $PSScriptRoot "gto_active.lock"
if (-not (Test-Path $LockPath)) {
    # No GTO session active; allow standard termination
    $Response = @{ decision = "approve" }
    $Response | ConvertTo-Json -Compress
    exit 0
}

# Read the active transaction log to inspect Claude's tool execution trace
$InputJson = $Input | Out-String | ConvertFromJson
$TranscriptPath = $InputJson.transcript_path

if (Test-Path $TranscriptPath) {
    $TranscriptContent = Get-Content -Path $TranscriptPath -Raw
    
    # Deterministically verify if Claude actually invoked required tools (e.g., Grep or Edit)
    $UsedTools = $TranscriptContent -match "tool_use"
    $CheckedSchema = $TranscriptContent -match "(schema|architecture|findings)"
    
    if (-not ($UsedTools -and $CheckedSchema)) {
        # Claude attempted to cheat the playbook. Trigger a hard block via stderr
        $Reason = "[FIDELITY ERROR] GTO Skill Enforcement Block: You attempted to complete the turn via plain text conversational output without utilizing your specialized investigative tools. You must use Grep or Read to ground your Gap-to-Opportunity matrix in real codebase evidence before stopping."
        
        $Response = @{
            decision = "block"
            reason = $Reason
        }
        # Write structural block to stdout, send descriptive error to stderr, exit with code 2
        $Response | ConvertTo-Json -Compress
        [Console]::Error.WriteLine($Reason)
        exit 2
    }
}

# Cleanup the session lock state if verification passes completely
Remove-Item $LockPath -ErrorAction SilentlyContinue
$Response = @{ decision = "approve" }
$Response | ConvertTo-Json -Compress
exit 0

The Verification Loop
Once implemented, your manual interactions gain a guaranteed deterministic safety net. If you type /gto analyze current auth architecture, the system automatically attaches rigid context to prevent instruction skipping. If Claude attempts to output a generalized summary without deeply tracing your workspace paths, the Stop gate blocks the generation mid-session, flashes the execution error to the terminal, and forces the model to self-correct and execute the specific plays defined in your skill system.
For an interactive deep dive on how to programmatically manipulate prompt buffers using these specific lifecycle events, refer to this walkthrough on[Rewriting Prompts on the Fly with Claude Code UserPromptSubmit Hooks](https://www.youtube.com/watch?v=x5-nRfxO5u4). This tutorial provides clear visual context on using prompt interception hooks to inject technical contexts and normalize tool execution pathways cleanly.

[12-Rewrite Prompts on the Fly with Claude Code UserPromptSubmit Hooks - YouTube](https://www.youtube.com/watch?v=x5-nRfxO5u4)
[SkillBakery Studio · 102 views](https://www.youtube.com/watch?v=x5-nRfxO5u4)

"

What do you think the optimal long term solution is?

## Assistant

The optimal long-term solution is **not** “make the `/gto` skill prompt stronger.” It is to split responsibilities cleanly: keep `gto` as a workflow spec, make `skill-guard` the deterministic runtime enforcer, and add a thin invocation-state layer that tracks whether a manually requested skill was actually entered and satisfied. Your attached materials already point in that direction: `gto` is structured like an orchestration workflow with analyzers, reviewers, gates, and tests, while `skill-guard` already contains hook, execution-state, pattern-gate, script-path-gate, and stop-gate machinery intended to enforce workflows rather than merely describe them.[1][2]

## Diagnosis

The core failure is architectural: a manually invoked skill is still just context unless something outside the model verifies activation and completion. The attached discussion in `paste-3.txt` repeatedly circles the same issue—skills are soft guidance, while hooks are the only deterministic enforcement surface—and it also identifies two important constraints: blocking writes too early is often counterproductive, and relying on repeated Stop-hook self-correction can hit a hard block limit and degrade UX.[3]

That means LLM2’s proposal is directionally right but too coarse and brittle as a final architecture. A `UserPromptSubmit` gate plus a `Stop` gate can help, but a lockfile-and-string-match design is too weak for long-term reliability because it confuses “the prompt mentioned gto” with “the skill was actually activated,” and “the transcript contains schema/findings words” with “the required workflow stages happened”.[3]

## Best architecture

The best long-term design is a **three-layer contract model**:

1. **Invocation contract**: detect explicit manual invocation like `/gto` and record a required skill-execution obligation for the current turn/session. This should be lightweight and fast in `UserPromptSubmit`, not semantic-heavy, because your own critique notes this hook must avoid latency and session stalls.[3]
2. **Execution evidence contract**: during the turn, collect structured evidence that the required workflow actually ran. Your `skill-guard` repository appears to already have the right primitives for this, including execution tracking, breadcrumbs, prompt-submit hooks, skill execution state, workflow-step gates, command observability, and slash-command observability tests.[2]
3. **Completion contract**: at `Stop`, validate evidence against the skill’s declared required steps, then either approve, warn, or block. This is where deterministic enforcement belongs, because it evaluates a completed attempt rather than interrupting the model mid-thought, which your critique correctly identifies as an anti-pattern for most write operations.[3]

This is better than “forced prompt rewriting” because it makes skill use a **state machine**, not a text pattern. It is also better than “block every write until a report exists” because it avoids fighting the model’s natural working loop and instead judges whether the completed loop satisfied the skill contract.[3]

## What to change

You should enhance `skill-guard` **first**, then simplify `gto`. The files suggest `skill-guard` has already grown many specialized gates and trackers, while `gto` has its own orchestrator, hooks, quality gates, and scoring/triage tests; that usually means responsibility is currently too distributed, so the system likely suffers from duplicated control logic and ambiguous ownership of enforcement.[1][2]

A cleaner division would be:

| Layer | Owns | Should live in |
|---|---|---|
| Skill definition | Required phases, allowed tools, expected artifacts, success criteria [1] | `gto` |
| Runtime detection | Slash/manual invocation detection, turn/session binding, evidence ledger [2] | `skill-guard` |
| Enforcement | Stop-time validation, bounded retries, user-visible failure reasons [2][3] | `skill-guard` |
| Analysis logic | Gap analysis, reviewer/analyzer flow, scoring/triage [1] | `gto` |

Concretely, I would move toward a **declarative skill contract** model. Instead of hardcoding `/gto` behavior in bespoke hook scripts, define frontmatter or sidecar metadata for each skill: required phases, required tool categories, forbidden premature completion patterns, expected evidence markers, and optional artifacts. Your `skill-guard` codebase appears to already include frontmatter loading and multiple gates around skill patterns, script paths, metadata advisories, and workflow steps, which makes it a good fit for becoming a generic contract engine rather than a pile of one-off guards.[2]

## Recommended pipeline

For manual invocation reliability on Windows 11 Claude Code, I would use this pipeline:

- `UserPromptSubmit`: detect `/gto`, normalize it, and write a session-turn requirement such as “required_skill=gto, state=requested.” Keep this hook fast; do not do transcript parsing or codebase analysis here.[3]
- Early-turn advisory: inject a short deterministic reminder, not a huge enforcement essay. The goal is to bias correct behavior, not consume context.
- During execution: log tool events and breadcrumb markers into a structured ledger. Your repository already appears to contain execution trackers, breadcrumb systems, command observability, marker utilities, and skill execution state components that can support this.[2]
- `PreToolUse`: use only for narrow, high-confidence guardrails, such as preventing obviously disallowed actions or enforcing a required first investigative step for very specific commands. Do **not** make this your main “did gto run?” judge, because your own critique is right that mid-write blocking is brittle and disruptive.[3]
- `Stop`: validate the skill contract from the ledger. Example checks: did the session enter `gto`; did it complete required phases like analyze/review/triage; did it use at least one evidence-gathering tool when the contract requires it; did it produce expected structured findings; did it avoid forbidden direct-solution completion without analysis.[1][2]
- Retry policy: allow bounded self-correction, but design for graceful degradation after repeated failures, because your own critique notes repeated Stop-hook blocking has limits and should not be treated as an infinite healing loop.[3]

The important shift is that the **ledger** becomes the source of truth, not prompt text and not naive transcript keyword matching. `skill-guard` seems much closer to this architecture already than LLM2’s lockfile proposal is.[2]

## Why this is optimal

I think the optimal long-term solution is a **declarative skill contract + evidence ledger + stop-time validator**. FACT: your repos already show both sides of this separation—`gto` has workflow/orchestration semantics, and `skill-guard` has the hook/state/gate machinery needed to enforce them. CONSENSUS: deterministic enforcement should live outside the model whenever you need reliable lifecycle control, while prompt-only instructions remain probabilistic. SPECULATION, high confidence: your current underperformance is likely caused more by blurred boundaries and brittle detection than by missing one more hook script.[1][2][3]

If you want the shortest possible implementation direction, it is this:

- Make `skill-guard` own manual-skill invocation state.
- Give each skill a machine-readable execution contract.
- Collect structured evidence during the turn.
- Validate at `Stop` against the contract.
- Use `PreToolUse` only for narrow safety or obvious sequencing invariants.
- Remove duplicated enforcement logic from `gto` so it stays a workflow, not a second guard framework.

My confidence is **high** on the architecture, but **medium** on exact Claude Code hook payload details because I only have your attached repo extracts and chat transcript, not the live hook API docs or your current settings files.[2][3]

The next best step is to refactor `skill-guard` around a single generic `SkillExecutionContract` and `SkillExecutionLedger` abstraction, then migrate `/gto` onto that path first as the reference implementation.[2]

## Human

Please provide an implementation prompt for the target LLM to refactor skill-guard as you describe.

## Assistant

The file only exposes structure, not source code content (all implementations show empty). I have enough from the prior context to write the implementation prompt accurately. Here it is:

***

## Implementation Prompt

Copy-paste this as your initial message to the implementing LLM. It is self-contained and references your existing structure by name.

***

```
You are refactoring the `skill-guard` plugin for Claude Code (Windows 11, Python 3.x).
The repo root is the current working directory. Read every file you reference before modifying it.

## Context

`skill-guard` currently enforces coding-quality gates generically but does NOT reliably
ensure that manually invoked skills (e.g. `/gto`) actually activate and complete their
declared workflow. The root cause is that enforcement is scattered across bespoke per-skill
hook scripts, there is no canonical per-turn invocation obligation record, and Stop-time
validation uses brittle transcript keyword matching rather than structured evidence.

## Goal

Refactor `skill-guard` to implement a **Declarative Skill Contract + Evidence Ledger +
Stop-time Validator** pattern. The skill definition (what the workflow requires) stays in
the skill itself. `skill-guard` owns runtime detection, obligation tracking, evidence
collection, and Stop-time contract validation. These responsibilities must not be duplicated
inside individual skill files.

## Constraints

- Do NOT break any existing passing tests. Run `python -m pytest` before and after each
  logical change and fix regressions immediately.
- Do NOT touch `gto_full.md` or any other skill file during this refactor; those are
  separate concerns.
- All hook entry-point scripts that Claude Code invokes must use `sys.stdin` for payload
  ingestion and must print a single JSON object to `sys.stdout`. They must never hang on
  empty stdin. On Windows 11, all hooks run via `python` (not `bash`); do not introduce
  bash-only constructs.
- Preserve the existing `breadcrumb`, `execution_store`, and `sqlite_backend` subsystems;
  the new ledger should extend or delegate to them, not replace them.
- Keep `UserPromptSubmit` hooks fast (< 50 ms typical); do NOT do transcript parsing,
  codebase scanning, or filesystem writes beyond a single small JSON state file in
  `UserPromptSubmit`.
- `PreToolUse` hooks may only block for narrow, statically determinable violations
  (e.g. tool not in `allowed_tools`). Do NOT use `PreToolUse` as the primary
  "did the skill complete?" judge.
- The `Stop` hook is the sole completion validator.
- Maximum Stop-hook self-correction retries per turn: 2. After 2 consecutive blocks on the
  same turn, emit a structured warning and approve so the user is not hard-locked.

## New Abstractions to Introduce

### 1. `SkillContract` (data class)
Location: `src/skill_guard/skill_contract.py`

Fields (all optional except `skill_id`):
- `skill_id: str` — canonical name matching the slash command (e.g. `"gto"`)
- `trigger_patterns: list[str]` — regex patterns that match manual invocation in the
  user prompt (e.g. `[r"/gto\b", r"gap.to.opportunity"]`)
- `required_tool_categories: list[str]` — logical categories that must appear in
  PostToolUse evidence (e.g. `["read", "grep", "search"]`). Categories map to actual
  tool names via a registry (see §4 below).
- `required_phases: list[str]` — ordered phase names the skill declares in its frontmatter
  `workflow_steps` field; at least N of M must be evidenced.
- `min_phases_required: int` — minimum number of `required_phases` that must be satisfied
  (default: all).
- `forbidden_premature_stop_patterns: list[str]` — regex patterns that, if found in the
  final assistant message, indicate a lazy stop (e.g. `r"I'll skip"`, `r"as a shortcut"`).
- `allowed_tools: list[str] | None` — if set, PreToolUse blocks any tool not in this list
  while the skill is active.
- `max_retries: int` — per-turn Stop-hook retry budget (default: 2).

Loading: `SkillContractLoader` reads contracts from a `contracts/` directory at the repo
root. Each contract is a YAML file named `<skill_id>.yaml`. Also attempt to merge any
`guard:` frontmatter block from the skill's own `.md` file when it is discoverable via
the existing `_skill_frontmatter_loader.py`. YAML takes precedence over frontmatter.

### 2. `InvocationLedger` (singleton per session/turn)
Location: `src/skill_guard/invocation_ledger.py`

Backed by the existing SQLite backend. Schema extension (add table if not exists):
```sql
CREATE TABLE IF NOT EXISTS skill_invocations (
    session_id TEXT NOT NULL,
    turn_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'requested',
    -- states: requested | active | satisfied | failed | warned
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (session_id, turn_id, skill_id)
);

CREATE TABLE IF NOT EXISTS skill_evidence (
    session_id TEXT NOT NULL,
    turn_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    -- types: tool_use | phase_marker | artifact
    evidence_key TEXT NOT NULL,
    raw_value TEXT,
    recorded_at TEXT NOT NULL
);
```

Public interface:
```python
class InvocationLedger:
    def record_invocation(session_id, turn_id, skill_id): ...
    def record_evidence(session_id, turn_id, skill_id, evidence_type, evidence_key, raw_value=None): ...
    def get_active_invocations(session_id, turn_id) -> list[str]: ...
    def get_evidence(session_id, turn_id, skill_id) -> list[EvidenceRecord]: ...
    def set_state(session_id, turn_id, skill_id, state): ...
    def get_state(session_id, turn_id, skill_id) -> str | None: ...
    def increment_retry(session_id, turn_id, skill_id) -> int: ...
```

### 3. `ContractValidator`
Location: `src/skill_guard/contract_validator.py`

```python
@dataclass
class ValidationResult:
    passed: bool
    skill_id: str
    failed_checks: list[str]
    block_reason: str | None

class ContractValidator:
    def validate(contract: SkillContract, evidence: list[EvidenceRecord],
                 final_message: str) -> ValidationResult: ...
```

Logic (in order, short-circuit on first failure):
1. Check `required_tool_categories`: for each category, at least one evidence record of
   type `tool_use` must exist whose `evidence_key` maps to that category.
2. Check `required_phases`: count distinct phase markers in evidence; must meet
   `min_phases_required`.
3. Check `forbidden_premature_stop_patterns`: if any pattern matches `final_message`,
   fail with a specific reason string.
4. If all pass: return `ValidationResult(passed=True, ...)`.

### 4. `ToolCategoryRegistry`
Location: `src/skill_guard/tool_category_registry.py`

A dict mapping logical category names to sets of Claude Code tool name substrings:
```python
TOOL_CATEGORIES = {
    "read":   {"Read", "cat", "open"},
    "grep":   {"Grep", "ripgrep", "rg"},
    "search": {"Grep", "Glob", "Find"},
    "write":  {"Write", "Edit", "MultiEdit"},
    "bash":   {"Bash"},
    "web":    {"WebSearch", "WebFetch"},
}
```
Extendable via `contracts/tool_categories.yaml` at repo root.

## Hook Refactoring

### `UserPromptSubmit` (`src/skill_guard/skill-guard_UserPromptSubmit.py`)
1. Read JSON payload from `sys.stdin` (handle empty stdin gracefully: exit 0 with
   `{"decision": "approve"}`).
2. Extract `session_id`, `turn_id` (or derive `turn_id` from timestamp if absent), and
   `prompt` text.
3. Load all `SkillContract`s from `SkillContractLoader`.
4. For each contract, test `trigger_patterns` against the prompt (case-insensitive).
5. For each matching contract, call `InvocationLedger.record_invocation(...)`.
6. If any invocations were recorded, build a short `additionalContext` string (≤ 200 chars)
   that names the activated skills and instructs Claude to follow their declared phases.
   Do NOT embed the entire skill playbook here.
7. Output `{"decision": "approve", "additionalContext": "..."}` or
   `{"decision": "approve"}` if nothing matched.
8. Total wall time budget: 50 ms. If SQLite write takes longer, log a warning to stderr
   and skip the write (non-blocking degradation).

### `PostToolUse` (`src/skill_guard/posttooluse/skill_execution_tracker.py`)
Extend existing tracker:
1. After each tool use, load active invocations for current `(session_id, turn_id)`.
2. For each active skill, check whether the tool name matches any category in the
   skill's `required_tool_categories`. If so, call
   `InvocationLedger.record_evidence(... evidence_type="tool_use", evidence_key=tool_name)`.
3. If the tool output or tool name contains a phase marker string matching any of
   `required_phases` for the skill, record a `phase_marker` evidence record.
4. Output `{"decision": "approve"}` unconditionally (PostToolUse must never block).

### `PreToolUse` dispatcher (`src/skill_guard/skill-guard_PreToolUse.py`)
Add one new check at the top of the existing dispatch chain:
- If an active invocation exists for any skill that declares `allowed_tools`, and the
  requested tool is NOT in `allowed_tools` for that skill, return:
  `{"decision": "block", "reason": "Tool '<name>' is not permitted during <skill_id> execution. Allowed: <list>"}`.
- This check runs before all existing PreToolUse gates.
- If no active invocations exist, skip this check entirely (zero overhead on normal turns).

### `Stop` (`src/skill_guard/skill-guard_Stop.py`)
1. Read JSON payload from `sys.stdin`. Extract `session_id`, `turn_id`, `stop_reason`,
   and `transcript_path` (may be absent).
2. Load active invocations. If none: approve immediately.
3. Parse the final assistant message from the transcript if `transcript_path` is present
   and the file is accessible. Gracefully skip if not.
4. For each active invocation:
   a. Load the `SkillContract` for that `skill_id`.
   b. Load evidence from `InvocationLedger`.
   c. Run `ContractValidator.validate(contract, evidence, final_message)`.
   d. If validation passes: call `InvocationLedger.set_state(..., "satisfied")`.
   e. If validation fails:
      - `retry_count = InvocationLedger.increment_retry(...)`
      - If `retry_count <= contract.max_retries`:
        - Set state to `"active"` (not yet failed).
        - Collect all `failed_checks` into a structured block reason.
        - Output `{"decision": "block", "reason": "<structured message>"}` and
          write the same reason to stderr.
        - Exit with code 2.
      - If `retry_count > contract.max_retries`:
        - Set state to `"warned"`.
        - Output `{"decision": "approve"}`.
        - Write a warning to stderr:
          `"[skill-guard] WARNING: <skill_id> contract not satisfied after <n> retries. Approving to prevent hard-lock."`
5. If all invocations are satisfied or warned: output `{"decision": "approve"}`.

## Migration / Compatibility

- The existing `slash_command_observability.py` and `skill_forced_eval.py` currently do
  some invocation detection. After this refactor, `UserPromptSubmit` is the single source
  of invocation detection. Audit both files and remove any duplicate detection logic,
  replacing with calls to `InvocationLedger` where appropriate. Preserve any unrelated
  functionality.
- `skill_execution_state.py` currently tracks execution state. Migrate its per-skill
  state fields to delegate reads/writes to `InvocationLedger` for invocation-specific
  state, keeping any non-invocation state fields as-is.
- The existing `breadcrumb` tracker records tool use already. Wire it as the upstream
  evidence source for `PostToolUse` evidence recording (do not duplicate the DB write;
  either read from breadcrumb records or share the same write).

## Deliverables (in order)

1. `src/skill_guard/skill_contract.py`
2. `src/skill_guard/tool_category_registry.py`
3. `src/skill_guard/invocation_ledger.py`
4. `src/skill_guard/contract_validator.py`
5. Updated `src/skill_guard/skill-guard_UserPromptSubmit.py`
6. Updated `src/skill_guard/posttooluse/skill_execution_tracker.py`
7. Updated `src/skill_guard/skill-guard_PreToolUse.py`
8. Updated `src/skill_guard/skill-guard_Stop.py`
9. Migration of `slash_command_observability.py` and `skill_execution_state.py` as
   described above.
10. `contracts/gto.yaml` — a sample contract for the `/gto` skill with reasonable defaults:
    - `trigger_patterns: ["/gto\\b", "gap.to.opportunity", "gap to opportunity"]`
    - `required_tool_categories: ["read", "grep"]`
    - `required_phases: ["analyze", "review", "triage"]`
    - `min_phases_required: 2`
    - `forbidden_premature_stop_patterns: ["I'll skip", "as a shortcut", "without analyzing"]`
    - `max_retries: 2`
11. Unit tests for `SkillContract` loading, `InvocationLedger` CRUD, and
    `ContractValidator` logic (happy path + each failure mode). Place in
    `tests/test_skill_contract.py`, `tests/test_invocation_ledger.py`,
    `tests/test_contract_validator.py`.

## Acceptance Criteria

- `python -m pytest` passes with no new failures after all changes.
- Manually running the `UserPromptSubmit` hook with a JSON payload containing `/gto`
  in the prompt results in a row in `skill_invocations` table with state `requested`.
- Running the `Stop` hook with zero tool-use evidence for an active gto invocation
  returns `{"decision": "block", ...}` with a non-empty `reason`.
- Running the `Stop` hook after 3 total calls on the same `(session_id, turn_id, gto)`
  returns `{"decision": "approve"}` with a warning on stderr.
- No `UserPromptSubmit` hook call takes more than 50 ms on a warm process.
- No bash-specific syntax appears in any hook entry-point; all are valid `python` scripts.
```

***

A few notes on using this prompt effectively:[1][2]

- **Inspect first**: the implementing LLM should be told to read all referenced files before making any changes. Claude Code's default behaviour supports this; emphasize it if you are using a model that tends to write before reading.
- **The `contracts/gto.yaml` file** is where you tune enforcement over time without touching Python. When `/gto`'s workflow evolves, update the YAML, not the hook scripts.[3]
- **The 50 ms `UserPromptSubmit` budget** and the 2-retry hard cap on `Stop` are the two most important guardrails against the UX-degrading failure modes identified in your prior conversation.[2]
- **Scope creep risk**: the prompt deliberately excludes MLflow, OVI scoring, and SCAFFOLD-CEGIS semantic anchoring. Those are valid future extensions but should not be in the same PR as this foundational refactor.

## Human

Please critically review your prompt.

## Assistant

My prompt is directionally good, but it is still too **prescriptive** in places where the implementing LLM should first inspect the existing abstractions and adapt to them. That matters here because `skill-guard` already appears to have substantial machinery for execution hooks, execution state, breadcrumb tracking, frontmatter loading, slash-command observability, stop gating, and migration/testing around skill contracts, so a refactor that introduces parallel concepts too aggressively could create duplication instead of consolidation.[1]

## Main flaws

The biggest flaw is that I specified several new files and schemas too early, before confirming whether equivalent abstractions already exist in `skill_guard`. Your repo appears to already contain modules like `_ledger_integration.py`, `_skill_frontmatter_loader.py`, `skill_execution_state.py`, `execution_store.py`, `slash_command_observability.py`, `posttooluse/skill_execution_tracker.py`, and `StopHook_skill_execution_gate.py`, plus tests named around migration, contracts, execution state, and skill command integration; that is strong evidence the correct task is probably “refactor and unify existing components” rather than “add an all-new contract/ledger subsystem”.[1]

Second, the prompt still risks repeating part of the anti-pattern we already rejected: excessive reliance on hook-enforced lifecycle rigidity without enough emphasis on fail-open behavior and minimal interruption of the model’s working loop. Your prior critique explicitly identified write-time blocking as a bad pattern, warned about hard retry ceilings on repeated Stop-hook blocks, and stressed that `UserPromptSubmit` must stay extremely lightweight because it stalls the entire session while running. I partially accounted for that with a Stop-first design and a 2-retry cap, but the prompt still lets the implementing LLM add too much blocking semantics into `PreToolUse` and too much schema work into the hot path.[2]

Third, I made an assumption about the hook payload contract and output JSON shape without validating it from your actual implementation. Since the attached `skill-guard_full.md` export shows filenames and line references but not readable function bodies, I cannot verify whether your hooks expect `decision/block/approve`, `permissionDecision`, different turn identifiers, or some compatibility layer in `hook_compat.py`; a prompt that hardcodes these shapes may push the implementer to break working integration points.[1]

## Architectural concerns

The prompt is strongest on the target architecture—declarative contract, evidence ledger, stop-time validation—but weaker on **migration strategy**. Given the repo already has migration helpers, contract migration tests, state IO, tracker DB race tests, and multiple generations of breadcrumb infrastructure, the safest approach is an incremental compatibility refactor with adapters, not a “create four new primitives and rewire everything” rewrite.[1]

I also under-specified the most important distinction: “manual invocation detected” is not the same as “skill activated by Claude.” The prompt records `/gto` at `UserPromptSubmit`, which is useful, but unless the evidence model distinguishes `requested`, `entered`, and `satisfied`, the Stop hook may incorrectly penalize turns where the user mentioned `/gto` textually or where routing logic intentionally redirected to a different flow. Your existing repository appears to already care about invocation indicators, slash-command observability, and execution state, so the prompt should have leaned harder on preserving that nuance instead of compressing it into a simpler obligation record.[1]

Another concern is that my sample `required_phases` model assumes phases can be inferred generically from phase-marker strings or tool outputs. That may work for `gto`, but it is brittle as a generic contract mechanism unless those phases are tied to explicit instrumentation points already present in your skill system. Since the `gto` materials indicate analyzers, reviewers, orchestrators, quality gates, and scoring/triage components, a better contract likely maps to **named workflow events or artifact creation**, not to generic string matching alone.[3]

## Operational risks

The prompt’s latency budget for `UserPromptSubmit` is good in spirit, but 50 ms may be unrealistically strict if the current implementation uses SQLite initialization, terminal/session resolution, or existing breadcrumb setup logic. Your repo includes tracker DB init race tests, terminal detection/ID utilities, and execution runtime/store layers, which suggests real initialization overhead exists; the prompt should say “keep it lightweight and avoid heavy work” rather than force an arbitrary number unless you already know your warm-path timing envelope.[1]

The Stop retry design is also incomplete. Your earlier critique notes Claude Code has a hard fail-safe after repeated Stop-hook blocks, so bounded retries are necessary, but “approve after 2 retries” may allow low-fidelity completions too easily in exactly the cases you care most about. A better pattern is graded degradation: first Stop block returns concrete missing evidence, second block returns a shorter checklist, third event records a warning state and annotates the session visibly, rather than silently approving with only stderr output.[2]

There is also a fail-open/fail-closed tension I did not handle explicitly enough. The prior critique argues production-grade guards should fail open on parser failures, timeouts, or resource issues because otherwise developers disable the guard entirely. My prompt still treats several components—contract loading, ledger writes, transcript parsing, and validation—as if they are dependable enough to underpin hard blocking. That is too optimistic for a first refactor.[2]

## What I would change

I would revise the prompt in four ways.

- Replace “introduce these exact new files” with “first inspect existing modules and either extend or consolidate them; only add new files where no clean home exists.” This is better aligned with the repo’s apparent breadth of existing abstractions.[1]
- Change the architecture from “new invocation ledger subsystem” to “canonicalize invocation/evidence state behind one interface, reusing existing execution store / breadcrumb / state IO where possible.” That avoids parallel state systems.[1]
- Strengthen fail-open rules: on hook parse errors, DB errors, transcript read errors, or contract load errors, record diagnostic telemetry and approve unless the violation is a narrow static `allowed_tools` rule. This matches the critique of brittle fail-closed enforcement.[2]
- Narrow `PreToolUse` further. The prior critique is clear that mid-thought blocking is dangerous; `PreToolUse` should mostly protect against obviously forbidden tools or destructive operations, not attempt to police analysis completeness.[2]

## Better prompt shape

A stronger version would tell the implementing LLM to:

1. Audit existing modules and identify which already implement contract loading, state persistence, invocation detection, evidence recording, and stop validation.[1]
2. Produce a short refactor plan before coding, naming what will be reused, merged, deprecated, or replaced.[1]
3. Preserve wire compatibility for hook entry points and payload schemas unless inspection proves a cleaner shared adapter already exists in `hook_compat.py`.[1]
4. Implement canonical invocation states such as `requested`, `entered`, `satisfied`, `warned`, and `bypassed`, with fail-open behavior on infrastructure errors.[2]
5. Use Stop as the primary workflow-fidelity judge, keep UserPromptSubmit fast, and keep PreToolUse narrow.[2]

## Bottom line

FACT: the prompt has the right strategic direction—separate skill definition from enforcement, record structured evidence, and validate at Stop rather than relying on soft prompt text alone. FACT: it is too implementation-opinionated for a repo that already appears to contain many overlapping state, hook, observability, and migration primitives. SPECULATION, high confidence: if you used my prompt unchanged, a capable LLM would likely produce something workable but with unnecessary abstraction churn and a meaningful risk of creating duplicate contract/state layers rather than truly simplifying `skill-guard`.[3][2][1]

The best next step is for me to rewrite the implementation prompt in a more **repo-adaptive, migration-first** form.

## Human

yes please

## Assistant

Yes — here is the **repo-adaptive, migration-first** implementation prompt I’d use instead.

It is better than my previous version because it tells the target LLM to inspect and consolidate existing abstractions first, preserve compatibility where possible, and treat `UserPromptSubmit`, `PreToolUse`, and `Stop` according to the failure modes already identified in your prior analysis: lightweight submit-time logic, narrow pre-tool blocking, and stop-time workflow validation with graceful degradation.[1][2]

## Revised prompt

```text
You are refactoring the `skill-guard` plugin for Claude Code on Windows 11.

Your job is NOT to invent a parallel architecture from scratch.
Your job is to inspect the existing repo carefully, identify the current abstractions for:
- hook payload compatibility
- manual skill invocation detection
- execution state
- breadcrumb / tracker evidence
- frontmatter / contract loading
- Stop-hook validation
- migration helpers and tests

Then refactor toward a cleaner, canonical implementation that makes manually invoked skills
(e.g. `/gto`) reliable without duplicating state systems or breaking existing behavior.

You must be migration-first, compatibility-aware, and conservative.

--------------------------------------------------
PRIMARY OBJECTIVE
--------------------------------------------------

Refactor `skill-guard` so that manually invoked skills are enforced via a canonical flow:

1. A manual invocation request is detected at submit time.
2. That request becomes a structured obligation for the current turn/session.
3. Evidence of actual skill execution is collected during the turn using existing tracker /
   breadcrumb / execution-state mechanisms where possible.
4. The Stop hook is the primary place where workflow completion is validated.
5. PreToolUse remains narrow and is not the main “did the skill run?” judge.
6. Failures in guard infrastructure should generally fail open, not brick the session.

The target architecture is:

- declarative skill contract / metadata
- canonical invocation + evidence state
- stop-time validation against structured evidence
- bounded retry / graceful degradation

But you must fit this architecture into the repo’s EXISTING structures wherever practical.

--------------------------------------------------
CRITICAL CONTEXT
--------------------------------------------------

The current problem is that manually invoked skills are still probabilistic unless something
outside the model tracks and validates them.

However, there are also known anti-patterns you must avoid:

- Do NOT rely on prompt text alone as proof that a skill executed.
- Do NOT overuse PreToolUse to interrupt the model mid-implementation.
- Do NOT put heavy logic in UserPromptSubmit; it stalls the session.
- Do NOT assume infinite Stop-hook self-correction; repeated blocks have hard limits.
- Do NOT fail closed on parser / DB / transcript / timeout issues unless the violation is a
  narrow, static, high-confidence safety rule.
- Do NOT create duplicate ledgers / duplicate execution state if the repo already contains
  suitable state, tracker, or breadcrumb abstractions.

--------------------------------------------------
REPO-AWARE INSTRUCTIONS
--------------------------------------------------

Before changing code, inspect the repo and produce a short implementation plan in your own
working notes (not as a user-facing essay). The plan must identify which existing modules
already cover these concerns and whether each should be:
- reused as-is
- extended
- merged
- wrapped via adapter
- deprecated

You should specifically inspect for modules or tests related to:
- ledger integration
- migration helpers
- frontmatter loading / validation
- state IO
- breadcrumb tracking / init
- execution tracker
- execution state
- command / slash-command observability
- prompt submit hook
- forced eval
- workflow step gating
- skill pattern / script path / directory gates
- contract auto-gate
- hook compatibility / payload normalization
- transcript parsing edge cases
- user prompt submit tests
- skill command integration tests
- workflow step parsing tests
- migration / contract migration tests
- breadcrumb integration / tracker integration tests

There are strong indications the repo already contains many of these abstractions.
Prefer consolidation over replacement.

--------------------------------------------------
DESIGN PRINCIPLES
--------------------------------------------------

1. Canonical state, not parallel state
There must be one authoritative path for manual-skill invocation state and evidence for
hook enforcement purposes. If multiple state systems currently exist, consolidate behind
a canonical interface. Do not leave two competing invocation/evidence systems active.

2. Stop is the completion judge
Use Stop as the primary place to validate whether a manually invoked skill actually
satisfied its declared workflow. This is where structured evidence should be checked.

3. PreToolUse is narrow
PreToolUse may block narrow, high-confidence violations such as:
- disallowed tool for an active skill
- obviously destructive operation
- direct violation of a static allowed-tools contract

PreToolUse must NOT become the main judge of whether analysis was “sufficient”.

4. UserPromptSubmit is lightweight
UserPromptSubmit should only:
- parse the incoming payload
- detect likely manual invocation
- record a lightweight invocation request/obligation
- optionally append a short additional context reminder

No transcript parsing.
No codebase analysis.
No heavy filesystem scanning.
No expensive DB initialization if avoidable.

5. Fail open on infrastructure issues
If DB access fails, transcript parsing fails, payload shape is unexpected, or a contract
cannot be loaded, the guard should usually approve and emit diagnostics rather than block
the user’s session. Only narrow static safety checks should fail closed.

6. Migration-first
Preserve existing hook entry points, payload schemas, and test expectations unless you
confirm via inspection that a compatibility adapter already exists and can safely normalize
them.

--------------------------------------------------
REFACTOR TASK
--------------------------------------------------

Implement a repo-adaptive refactor that achieves the following behaviors.

A. MANUAL INVOCATION DETECTION
When the user manually invokes a skill such as `/gto`, the system should record a structured
invocation obligation for the current turn/session.

Important:
- “Mentioned /gto in text” and “skill actually entered” are not necessarily the same thing.
- Model this distinction explicitly if the current repo abstractions support it.
- Prefer states such as:
  - requested
  - active / entered
  - satisfied
  - warned
  - bypassed / not-entered
  Use repo-native names if they already exist.

B. DECLARATIVE CONTRACTS
Manual skill enforcement should be driven by declarative metadata where possible.

First inspect whether the repo already has:
- frontmatter guard fields
- workflow step metadata
- contract auto-gates
- skill metadata loaders
- migration helpers for contract evolution

Use those existing mechanisms if possible.

The contract should be able to express, at minimum:
- trigger patterns or manual invocation indicators
- required workflow steps / phases
- required evidence categories (if the repo already supports evidence typing)
- optional allowed tools
- optional premature-completion patterns
- retry / warning policy

Do not invent a new contract format unless there is no viable existing one.

C. EVIDENCE COLLECTION
Structured evidence should come from existing tracker / breadcrumb / execution / observability
systems where possible.

Examples of acceptable evidence:
- tool-use records
- workflow-step markers
- breadcrumb events
- explicit skill activation indicators
- generated artifact markers
- repo-native execution state transitions

Avoid brittle string matching as the primary evidence source if stronger structured signals
already exist.

D. STOP-TIME VALIDATION
At Stop:
- load active or pending manual-skill obligations
- gather evidence for the current turn/session
- validate obligations against the skill contract / workflow metadata
- if satisfied, mark complete
- if not satisfied, block with a precise structured reason, subject to bounded retries
- after retry budget is exceeded, degrade gracefully to warning/approve rather than
  hard-locking the developer

E. PRETOOLUSE NARROW GATE
If an active skill declares narrow tool restrictions, PreToolUse may enforce them.
This should be lightweight and only use already-available state.
Do not add semantic or transcript-based heavy checks here.

--------------------------------------------------
IMPLEMENTATION APPROACH
--------------------------------------------------

Phase 1: Inspect and map
1. Read the relevant modules and tests before editing anything.
2. Identify the existing canonical hook payload handling path.
3. Identify the current source(s) of truth for:
   - skill invocation detection
   - execution state
   - breadcrumb / tracker evidence
   - workflow step parsing
   - Stop-hook validation
4. Identify duplicate or overlapping logic that should be unified.

Phase 2: Design the minimal refactor
Create the smallest coherent design that:
- preserves compatibility
- reduces duplication
- introduces one canonical interface for invocation/evidence validation
- reuses existing modules as much as possible

Phase 3: Implement incrementally
Make small changes in logical slices.
After each slice, run relevant tests first, then broader test suites.

Phase 4: Migrate carefully
If you need to replace an old path:
- keep the old API surface if tests or hook entry points depend on it
- implement adapters/shims where appropriate
- mark deprecated logic clearly in comments if useful, but do not perform unrelated cleanup

--------------------------------------------------
PREFERRED SHAPE OF THE RESULT
--------------------------------------------------

You do NOT have to create these exact names, but the resulting architecture should have
clear equivalents of:

- a canonical contract loader / metadata accessor
- a canonical invocation/evidence state interface
- a stop-time validator
- a narrow pretool policy check
- a lightweight submit-time invocation recorder

If equivalent modules already exist, refactor those rather than creating duplicates.

--------------------------------------------------
SPECIFIC COMPATIBILITY RULES
--------------------------------------------------

- Preserve hook entry-point filenames if they are already wired into settings/tests.
- Preserve existing payload JSON shapes unless a compatibility layer already normalizes them.
- Preserve Windows-friendly Python hook behavior: stdin -> JSON parsing, stdout -> one JSON
  decision object, stderr -> diagnostics.
- Never introduce bash-only assumptions.
- Never assume transcript_path always exists.
- Never assume session_id / turn_id names without inspecting current payload adapters.
- Reuse existing transcript parsing helpers if present.
- Reuse existing migration helpers if contract or state schema changes are needed.

--------------------------------------------------
FAILURE POLICY
--------------------------------------------------

Default policy:
- contract load failure -> warn, approve
- DB/state read failure -> warn, approve
- transcript parse failure -> warn, approve
- missing optional evidence source -> continue with best available evidence
- unexpected payload shape -> normalize if possible, otherwise warn, approve

Exception:
- narrow static safety rules in PreToolUse (e.g. forbidden destructive tool for active
  skill, or explicit allowed-tools violation) may block.

--------------------------------------------------
RETRY POLICY
--------------------------------------------------

Implement bounded Stop-hook retries for unmet manual-skill obligations.
Use repo-native retry tracking if it exists.

Desired behavior:
- first failure: block with concrete missing evidence / missing workflow steps
- second failure: block with shorter, clearer actionable reason
- after retry budget exceeded: mark warned and approve, emitting diagnostics

Do not create an infinite self-correction loop.

--------------------------------------------------
TESTING REQUIREMENTS
--------------------------------------------------

You must rely heavily on existing tests and add only the minimal new tests needed.

At minimum:
1. Run and preserve all existing relevant tests around:
   - prompt submit hook
   - slash command observability
   - skill command hook integration
   - workflow step parsing
   - breadcrumb integration
   - tracker integration
   - execution state
   - migration / contract migration
   - transcript parsing edge cases
   - PreToolUse characterization
   - Stop / enforcement behavior

2. Add focused tests only if coverage is missing for the new canonical flow:
   - manual invocation request recorded
   - evidence collected via existing tracker/breadcrumb path
   - Stop validation blocks when required evidence/steps are missing
   - Stop validation warns/approves after retry budget
   - infrastructure failures fail open

3. Do not rewrite broad test areas unnecessarily.

--------------------------------------------------
ACCEPTANCE CRITERIA
--------------------------------------------------

The refactor is successful only if all of the following are true:

1. Manual invocation of `/gto` (or equivalent configured skill) creates a structured
   per-turn/session obligation rather than relying on soft prompt context alone.

2. That obligation is validated at Stop using structured evidence from existing repo
   mechanisms where possible.

3. PreToolUse is limited to narrow static enforcement, not broad workflow completeness
   evaluation.

4. UserPromptSubmit remains lightweight.

5. Repeated Stop failures do not hard-lock the session; the system degrades gracefully
   after the retry budget.

6. The implementation reuses and consolidates existing repo abstractions rather than
   creating parallel state/contract/evidence systems without need.

7. Existing relevant tests still pass, and any new tests are narrowly targeted.

--------------------------------------------------
OUTPUT EXPECTATIONS
--------------------------------------------------

Do the work in this order:

1. Inspect repo and tests.
2. Decide what existing abstractions to reuse/extend.
3. Implement minimal canonical refactor.
4. Run tests iteratively.
5. Summarize:
   - what existing modules were reused
   - what was unified
   - what compatibility constraints were preserved
   - what new tests were added
   - any remaining risks or follow-up opportunities

Do not start coding until you have inspected the relevant files.
Do not replace existing systems wholesale unless inspection proves they are dead code or
strictly inferior and compatibility can be preserved safely.
```

## Why this is better

This version is better because it aligns with what your exported repo structure strongly suggests: `skill-guard` is already a **large, evolved system**, not a blank slate. The file listing indicates existing implementations and tests around ledger integration, migration helpers, frontmatter loading, state IO, breadcrumb tracking, execution tracker/state, prompt submit hooks, slash-command observability, contract auto-gating, workflow-step gates, transcript parsing, and skill command integration, so the right move is likely consolidation and canonicalization, not greenfield subsystem creation.[2]

It also better respects the operational constraints identified in your prior critique: `UserPromptSubmit` should stay fast because it blocks the session; `PreToolUse` should be narrow because write-time interruption is a bad default; repeated Stop-hook blocking has practical limits; and infrastructure failures should usually fail open rather than making developers disable the whole guard.[1]

## Two optional additions

I would consider appending these short instructions if you want even tighter execution control:

- “Before coding, list the exact files you believe are the canonical candidates for invocation detection, evidence capture, contract loading, and Stop validation.” This forces an architectural inventory first.[2]
- “Prefer characterization tests before refactors when behavior is unclear.” Your repo already appears to contain characterization-style tests for `PreToolUse`, migrations, transcript parsing, and execution flows, so this fits the project style well.[2]

## Main remaining weakness

The remaining weakness is that this prompt is intentionally less concrete about final class/module names. That is a feature, not a bug, for this stage; the repository appears to already have enough internal structure that over-specifying names too early would likely cause duplication or fight the existing design.[2]

If you want, I can also produce a **tighter Claude-Code-oriented version** of this prompt that is optimized specifically for getting the implementation LLM to:
- inspect first,
- produce a refactor plan,
- run tests after each slice,
- and avoid broad rewrites.

## Human

I need a handoff to another LLM for this chat session.

## Assistant

Here’s a handoff you can paste as the very first message to another LLM in this same Claude Code session to give it enough context, constraints, and direction to continue productively:

***

### Handoff Context (for the new LLM)

You are joining an ongoing project in a Claude Code / Windows 11 environment.

The user is a solution architect building **deterministic, epistemically sound enforcement** around Claude Code “skills”, especially a Gap-to-Opportunity skill (`/gto`). They are using a plugin called **skill-guard** that already has a large, sophisticated codebase with hooks, execution state, breadcrumb tracking, contract/migration helpers, and extensive tests.

Two key repos/files are in the workspace:

- `gto_full.md` — defines the GTO skill, with multi-phase gap analysis, analyzers/reviewers, gates, scoring, etc.[1]
- `skill-guard_full.md` — a large, heavily tested Python-based guard framework with hooks for UserPromptSubmit, PreToolUse, Stop, state IO, breadcrumb tracking, contract auto-gates, etc.[2]
- `paste-3.txt` — a prior LLM conversation analyzing these repos, discussing enforcement architectures, and critiquing various anti-patterns (like heavy PreToolUse blocking, brittle keyword-based transcript checks, and over-aggressive Stop-hook loops).[3]

**Problem:** When the user manually invokes `/gto` in Claude Code, the skill is not reliably used. The model often treats it as soft guidance instead of entering and completing the full workflow. The goal is to make manually invoked skills behave more like **runtime law** than “strong suggestions,” but without creating brittle, UX-hostile guard logic.

**Important constraints from prior analysis:**

- Skills (like `gto`) are *prompt-based guidance* and inherently probabilistic.
- Hooks (UserPromptSubmit, PreToolUse, Stop) are deterministic enforcement surfaces; Claude cannot negotiate with them.
- Past LLM proposals over-used:
  - heavy **PreToolUse** blocking of writes (bad: interrupts mid-thought),
  - large, heavy **UserPromptSubmit** logic (bad: stalls session),
  - infinite or unbounded Stop retries (bad: hits hard limits / UX degradation).
- The user wants:
  - **Declarative skill contracts** (what a skill requires),
  - **Structured evidence** of what actually happened (tools used, phases completed),
  - **Stop-time validation** against those contracts,
  - **Fail-open** behavior on infra errors (DB, parsing, etc.),
  - **Narrow PreToolUse** enforcement (static safety / allowed-tools), not general workflow policing.

The previous LLM’s latest recommendation is to **refactor `skill-guard` in a migration-first, repo-adaptive way**. Instead of brand-new subsystems, we should:

- **Inspect and reuse existing abstractions**:
  - ledger / state / execution store,
  - breadcrumb tracker,
  - skill contract / frontmatter loader,
  - command / slash-command observability,
  - UserPromptSubmit hook,
  - Stop / skill execution gate,
  - tests around these.
- **Canonicalize** a single path for:
  - manual skill invocation obligations,
  - evidence capture,
  - Stop-time validation.

The user has already been given a revised implementation prompt for `skill-guard` that emphasizes exactly this approach.

***

### Your Role

You are taking over **implementation and refinement**. Your focus should be:

1. **Read, don’t guess**:
   - Open and inspect the actual `skill-guard` source files referenced in `skill-guard_full.md` (e.g., `src/guard/promptsubmithook.py`, `src/guard/skill_execution_state.py`, `src/guard/skill_execution_gate.py`, `src/guard/contractautogate.py`, `src/guard/breadcrumbtracker.py`, etc.)[2]
   - Inspect tests like:
     - `testsuserpromptsubmithook.py`
     - `testsskillcommandhookintegration.py`
     - `testst001workflowstepsrequired.py`
     - `testsPreToolUseskillpatterngate.py`
     - `testst003breadcrumbverifier.py`
     - `testst005trackerintegration.py`
     - `testsskillexecutionstate.py`
     - `testsmigrateskillcontract.py`
   - Skim `paste-3.txt` for prior architectural proposals and critiques to avoid repeating known anti-patterns.[3]

2. **Build a small refactor plan**:
   - Identify existing mechanisms for:
     - manual skill invocation detection,
     - execution state,
     - breadcrumb / evidence,
     - contract/metadata loading,
     - Stop-time gating.
   - Decide which existing pieces become the **canonical**:
     - “invocation obligation” layer,
     - “evidence capture” layer,
     - “Stop validator” layer.
   - Decide how to **distinguish**:
     - skill mentioned,
     - skill entered,
     - skill satisfied / warned / bypassed.

3. **Implement minimal, canonical wiring**:
   - Ensure manual `/gto` invocations create a structured obligation for the current turn/session, not just prompt context.
   - Wire evidence capture (tool uses, workflow step markers, etc.) into the **existing** tracker/breadcrumb system rather than inventing a parallel ledger.
   - Make the Stop hook consult this state and evidence to enforce the skill contract in a bounded, graceful way.
   - Keep UserPromptSubmit fast/lightweight; keep PreToolUse narrow and focused on static safety or allowed-tools constraints.

4. **Respect failure and retry policies**:
   - On infra errors (DB, contract load, transcript parsing), **warn and approve** instead of hard-blocking, except for narrow static safety violations.
   - Implement bounded Stop retries (e.g., 1–2 attempts), then degrade to “warn and approve” with a clear diagnostic, not infinite self-correction.

5. **Use tests as a map**:
   - Run focused tests first (hook payload, skill command integration, workflow parsing, execution state).
   - Keep changes incremental; after each significant step, run tests and fix regressions.
   - Add only minimal new tests for:
     - manual `/gto` invocation obligation flow,
     - evidence capture via existing trackers,
     - Stop validation behavior for satisfied / unsatisfied / exhausted-retry cases.

***

### Concrete tasks for you to start with

1. **Inventory current abstractions**:
   - Locate the *actual implementation* of:
     - `src/guard/promptsubmithook.py`
     - `src/guard/skill_execution_gate.py`
     - `src/guard/skill_execution_state.py`
     - `src/guard/contractautogate.py`
     - `src/guard/breadcrumbtracker.py`
     - `src/guard/commandobservability.py`
   - Briefly summarize (in your own internal notes) how they currently interact.

2. **Clarify skill contracts**:
   - Find how skill contracts/frontmatter are currently loaded and validated:
     - `src/guard/skill_frontmatter_loader.py`
     - related tests (migration/contract tests).
   - Determine how workflow steps / required steps are represented (e.g. `workflow_step_gate` tests).[2]

3. **Design canonical invocation & evidence path**:
   - Decide:
     - How a manual `/gto` invocation is recognized (slash command observability).
     - Where invocation state is stored (reuse existing execution state or ledger).
     - How evidence from the tracker/breadcrumb is associated with that invocation.
   - Plan to use those instead of introducing a separate “ledger” unless the repo truly lacks this.

4. **Refine hooks**:
   - **UserPromptSubmit**:
     - Ensure it:
       - detects manual skill invocation,
       - records an invocation request,
       - optionally adds a small, deterministic reinforcement snippet,
       - remains quick and tolerant of failures.
   - **PreToolUse**:
     - Ensure it:
       - enforces narrow allowed-tools / static safety rules,
       - does not try to enforce full workflow completeness.
   - **Stop**:
     - Ensure it:
       - loads pending manual-skill obligations,
       - checks structured evidence via existing trackers/contract metadata,
       - blocks with clear reasons within a small retry budget,
       - then degrades gracefully (warn + approve) after retries are exhausted.

5. **Keep `gto` itself untouched for now**:
   - Treat `gto_full.md` as the skill *spec*, not something to rewrite.[1]
   - Your job is to make `skill-guard` enforce whatever `gto` declares, not to redesign `gto`.

***

### What the user wants from you next

The user wants you to:

- Operate inside this existing architecture rather than reinventing it.
- Produce concrete changes (code and tests) that:
  - centralize manual skill invocation handling,
  - capture evidence via existing mechanisms,
  - enforce contracts at Stop in a bounded, fail-open friendly way,
  - keep the developer experience usable (no heavy blocking at random points).
- Explain your plan briefly, then implement iteratively.

Treat premises as questionable; if you find contradictions or surprising existing behavior, surface them explicitly and propose the minimal safe changes rather than a wholesale rewrite.

***

If you’re ready, start by enumerating the key files you’ll inspect and how you expect them to participate in the new canonical invocation–evidence–validation pipeline, then proceed to code.
