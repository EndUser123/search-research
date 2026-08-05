# Handoff — PreToolUse phase-state ship gate hook

## Status
OPEN — design agreed, implementation not started.

## Objective

Build a PreToolUse hook that reads a ship phase-state file and blocks
`git push`/`git merge` when the ship pipeline hasn't reached the
"merge-ready" phase. This is the field-validated enforcement layer
(saytooy_arch: 18 incidents → 0 after implementing this pattern).

## Design

### Phase state file

Path: `P:/tmp/ship-phase-state.json` (or `~/.grok/state/<session>/ship-phase.json`
for multi-terminal isolation)

```json
{
  "session_id": "<UUID>",
  "phase": "review|verify|merge-ready|inactive",
  "updated_at": "<ISO timestamp>",
  "repos": ["P:/", "~/.grok"]
}
```

The `/ship` skill writes this file when invoked. Each phase transition
updates it.

### Hook: `PreToolUse_ship_phase_gate.py`

Registration: `~/.grok/hooks/ship-phase-gate.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "run_terminal_command",
        "hooks": [
          { "type": "command", "command": "python C:/Users/brsth/.grok/hooks/PreToolUse_ship_phase_gate.py", "timeout": 3 }
        ]
      }
    ]
  }
}
```

Logic:
1. Read stdin JSON envelope
2. Check if `toolName` is `run_terminal_command`
3. Check if the command matches `git push` or `git merge` (regex)
4. If yes: read phase state file
5. If phase ≠ "merge-ready" and phase ≠ "inactive": exit 2 with stderr
   "SHIP PHASE GATE: git push/merge blocked — current phase is '<phase>'.
   Complete /review and /check first, then run ship_receipt.py to advance
   to merge-ready."
6. If phase = "merge-ready" or "inactive" or no state file: exit 0 (allow)

### `/ship` skill updates

The `/ship` prose skill needs to write the phase state file:
- On `/ship` invocation: write `{"phase": "review"}`
- After `/review` completes: write `{"phase": "verify"}`
- After `ship_receipt.py` returns SHIP DONE: write `{"phase": "merge-ready"}`
- After SHIP BLOCKED: leave at `{"phase": "verify"}`
- On session end or abort: write `{"phase": "inactive"}`

### What already exists (no changes needed)

- `quality_gates_frontmatter.py` Stop hook — blocks completion when
  check-run.json or FINDINGS.md missing. Already works for ship skills.
- `ship_receipt.py` — mechanically derives SHIP DONE/BLOCKED from evidence.
  41 tests, hardened.
- `/review` skill — fresh-eyes code review with FINDINGS.md artifact.
- `/check` skill — session verification with check-run.json receipt.

## Scope

- **In scope:** `~/.grok/hooks/PreToolUse_ship_phase_gate.py` (new),
  `~/.grok/hooks/ship-phase-gate.json` (new registration),
  `/ship` SKILL.md phase-state write instructions
- **Out of scope:** modifying quality_gates_frontmatter.py, modifying
  ship_receipt.py, modifying /review or /check skills

## Acceptance criteria

1. Hook fires on `git push` and `git merge` commands
2. Hook reads phase state file and blocks when phase ≠ merge-ready
3. Hook allows push when phase = merge-ready or inactive
4. Hook allows non-git commands without checking (fast path)
5. Performance: <100ms (stat + JSON read only)
6. `/ship` skill writes phase state at each transition
7. End-to-end test: invoke /ship → skip review → attempt git push → blocked

## Key files

- **Field research:** `P:/tmp/www-ship-pipeline-enforcement.md`
- **Architecture decision:** `[[ship-pipeline-enforcement-pretooluse-phase-state-hooks]]`
- **Root cause:** `[[ship-py-phase-fragmentation-llm-controlled-continuation]]`
- **Existing Stop hook:** `~/.grok/hooks/scripts/quality_gates_frontmatter.py`
- **Existing receipt:** `~/.grok/skills/ship-rhai/__lib/ship_receipt.py`
- **Working PreToolUse reference:** `~/.grok/hooks/PreToolUse_skill_staleness.py`

## Handoff is wrong if

- The hook produces false positives (blocks legitimate pushes outside ship context)
- The phase state file races on multi-agent hosts (must be session-scoped)
- The hook adds >200ms latency to every run_terminal_command (must fast-path non-git commands)
