# Handoff — PreToolUse phase-state ship gate hook

## Status
RESOLVED — implemented, tested, committed (commit 5c1e1b0 in ~/.grok).

## Objective

Build a PreToolUse hook that reads a ship phase-state file and blocks
`git push` when the ship pipeline hasn't reached the "merge-ready" phase.
This is the field-validated enforcement layer (saytooy_arch: 18 incidents
→ 0 after implementing this pattern).

## Design

### Phase state file

Session-scoped path (mandatory — no global `P:/tmp/` path; that races
on multi-agent hosts):

```
~/.grok/state/<session>/ship-phase-{rhai,py}.json
```

During the testing phase, one file per ship variant (`ship-phase-rhai.json`
for `/ship-rhai`, `ship-phase-py.json` for `/ship-py`). After testing
concludes and a single ship skill is chosen, consolidate to one filename.

```json
{
  "session_id": "<UUID>",
  "phase": "review|verify|merge-ready|inactive",
  "ship_variant": "rhai|py",
  "updated_at": "<ISO timestamp>",
  "repos": ["P:/", "~/.grok"]
}
```

The active ship skill writes this file when invoked. Each phase transition
updates it. The hook is ship-variant-agnostic — it reads whichever
state file exists for the current session.

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
3. Fast-path: if command does NOT match `git push` (regex), exit 0 immediately
4. If `git push` matches: resolve session ID via `session_resolver`, read
   phase state file (`~/.grok/state/<session>/ship-phase-*.json`)
5. If no state file found OR phase = "inactive" OR phase = "merge-ready":
   exit 0 (allow)
6. If phase = "review" or "verify": exit 2 with stderr:
   "SHIP PHASE GATE: git push blocked — current phase is '<phase>'.
   Complete /review and /check first, then run ship_receipt.py to advance
   to merge-ready. To override for an emergency push, delete the phase
   state file or set phase to 'inactive'."

**Block scope: `git push` only.** Do NOT block `git merge`, `git commit`,
or any other git command. Merge is used for many non-ship operations
(sync, branch hygiene) and blocking it produces false positives.

### Ship skill updates

Both `/ship-rhai` and `/ship-py` SKILL.md files get phase-state write
instructions. The hook is ship-variant-agnostic; whichever ship skill
runs writes its own state file:

- On ship invocation: write `{"phase": "review", "ship_variant": "<rhai|py>"}`
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
  `/ship-rhai` SKILL.md phase-state write instructions,
  `/ship-py` SKILL.md phase-state write instructions
- **Out of scope:** modifying quality_gates_frontmatter.py, modifying
  ship_receipt.py, modifying /review or /check skills

## Acceptance criteria

1. Hook fires on `git push` commands (NOT git merge or other git commands)
2. Hook reads phase state file and blocks when phase = review or verify
3. Hook allows push when phase = merge-ready, inactive, or no state file
4. Hook allows non-git commands without checking (fast path, <10ms)
5. Performance: <200ms total per hook invocation for git push (Python
   cold-start + stat + JSON read). Non-git commands fast-path before
   any state read.
6. Both `/ship-rhai` and `/ship-py` skills write phase state at each transition
7. End-to-end test: invoke ship → skip review → attempt git push → blocked
   with actionable stderr message

## Key files

- **Field research:** `P:/.data/wiki/research/www-ship-pipeline-enforcement-20260805.md`
- **Architecture decision:** `[[ship-pipeline-enforcement-pretooluse-phase-state-hooks]]`
- **Root cause:** `[[ship-py-phase-fragmentation-llm-controlled-continuation]]`
- **Existing Stop hook:** `~/.grok/hooks/scripts/quality_gates_frontmatter.py`
- **Existing receipt:** `~/.grok/skills/ship-rhai/__lib/ship_receipt.py`
- **Working PreToolUse reference:** `~/.grok/hooks/PreToolUse_skill_staleness.py`
- **Session resolver (multi-terminal isolation):** `~/.grok/hooks/scripts/session_resolver.py`

## Handoff is wrong if

- The hook produces false positives (blocks legitimate pushes outside ship context)
- The phase state file races on multi-agent hosts (must be session-scoped)
- The hook adds >200ms latency to every run_terminal_command (must fast-path non-git commands)
- The hook blocks git merge or other non-push git commands (scope is push only)
