---
thread_id: generalized-skill-completion-gate-20260807
parent_handoff_path: none
current_session_id: 019fd9ae-d977-70a2-803c-9b4d139d1303
current_terminal_id: noterm
produced_at: 2026-08-07T13:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: see git log
---

# Handoff — Generalized skill-completion gate (one Stop hook, N skill declarations)

## 1. Objective

Build ONE Stop hook that reads each invoked skill's `quality_gates` frontmatter,
checks whether the evidence for "done" actually exists, and blocks session
completion if any invoked skill's evidence is missing. Replace the current
pattern of one hardcoded hook per skill with a generalized, declarative gate.

## 2. Status

OPEN — investigation complete, implementation not started.

## 3. Producing context

- **Date:** 2026-08-07
- **Session:** 019fd9ae-d977-70a2-803c-9b4d139d1303

## 4. Background: why this is needed

### The current problem

This workspace has multiple Stop hooks enforcing different skills' completion:

| Hook | What it checks | Skill |
|------|---------------|-------|
| `quality_gate.py` | ship-py pipeline phases, quality_gates frontmatter | ship-py |
| `Stop_validate_recommendations.py` | ungrounded recommendation claims | /www + /tp |
| `PreToolUse_ship_phase_gate.py` | push blocking during ship pipeline | ship-py |
| Various quality_gates_frontmatter.py checks | check-run.json, FINDINGS.md | /check, /review |

Each was built organically by a different session. Each added hardcoded
checks for its specific skill. Nobody stepped back and generalized.

### The pattern already exists (but isn't applied)

The wiki concept `[[declarative-quality-gates-skills-declare-evidence]]`
(session 2026-08-04) documents the generalized pattern. Ship-py already
uses it:

```yaml
quality_gates:
  - evidence: "P:/.artifacts/**/check-run.json"
    message: "/check receipt missing — run /check before claiming ship done"
    session_field: "session_id"
  - evidence: "P:/.artifacts/**/FINDINGS.md"
    message: "/review findings missing — run /review before claiming ship done"
```

quality_gate.py already reads these declarations. The problem: only ship-py
declares them, and quality_gate.py only checks ship-py's declarations — not
all invoked skills' declarations.

### The field confirms this is the right pattern

**[skillgate](https://github.com/renezander030/skillgate)** (46 commits, MIT):
"A finish-line gate your agent cannot talk its way past." One deterministic
evaluator reads `.skillgate/done.yaml` declarations and blocks commit/push
until all gates pass. Gate types: `file-exists`, `evidence`, `command`,
`absent`, `trivy`. No model in the loop. Works across opencode, Claude Code,
pre-commit, CI.

Research basis: the Compliance Gap paper (arxiv 2605.01771, 2,031 sessions)
showed 0% compliance under default conditions and proved (Theorem 2) that
non-compliance is undetectable from output text — the evaluator must
observe behavior deterministically, out of band.

## 5. Verified facts

- [FACT] quality_gates frontmatter format is already established (ship-py uses it)
- [FACT] quality_gate.py already reads quality_gates declarations from frontmatter
- [FACT] The wiki concept `[[declarative-quality-gates-skills-declare-evidence]]` documents the pattern
- [FACT] skillgate (external tool) validates the pattern with `file-exists`, `evidence`, `command`, `absent` gate types
- [FACT] The Compliance Gap paper (arxiv 2605.01771) provides the research basis
- [FACT] `/close` already has `close_accounting.py` — a Python script that checks gates mechanically
- [FACT] `/check` writes `check-run.json`, `/review` writes `FINDINGS.md` — evidence artifacts already exist

## 6. Design: the generalized gate

### Architecture: ONE hook, N declarations

```
Session ends (Stop event)
  ↓
Stop_skill_completion_gate.py fires
  ↓
1. Scan transcript for skill invocations (/ship-py, /check, /review, /wiki, /handoff, /close)
  ↓
2. For each invoked skill, read its SKILL.md frontmatter
  ↓
3. Parse quality_gates declarations
  ↓
4. For each gate: check evidence file exists (session-scoped)
  ↓
5. If any gate fails: block with clear message listing which skills' evidence is missing
  ↓
6. If all gates pass: allow session end
```

### What each skill declares

Each skill that wants enforcement adds `quality_gates` to its frontmatter:

```yaml
# /check SKILL.md
quality_gates:
  - evidence: "P:/.artifacts/**/check-run.json"
    message: "/check receipt missing — run /check before claiming done"
    session_field: "session_id"

# /review SKILL.md
quality_gates:
  - evidence: "P:/.artifacts/**/FINDINGS.md"
    message: "/review findings missing — run /review before claiming done"
    session_field: "session_id"

# /ship-py SKILL.md (already has these)
quality_gates:
  - evidence: "P:/.artifacts/**/check-run.json"
    message: "/check receipt missing"
  - evidence: "P:/.artifacts/**/FINDINGS.md"
    message: "/review findings missing"

# /wiki SKILL.md
quality_gates:
  - evidence: "P:/.data/wiki/concepts/*.md"
    message: "No wiki concept written — run /wiki if findings are durable"
    condition: "session_has_durable_findings"

# /handoff SKILL.md
quality_gates:
  - evidence: "P:/docs/handoffs/**/HANDOFF.md"
    message: "No handoff written — run /handoff if open work exists"
    condition: "session_has_open_work"
```

### Gate types (matching skillgate's taxonomy)

| Type | Passes when | Example |
|------|------------|---------|
| `evidence` (existing) | Named file exists at session-scoped path | check-run.json |
| `file-contains` (new) | File exists AND contains a pattern | FINDINGS.md has non-empty findings |
| `command` (new) | Script exits 0 | `python close_accounting.py --check-only` |
| `conditional` (new) | Gate only fires if condition is met | wiki gate only if session produced findings |

### What the hook does

```python
def main():
    # 1. Read the session transcript
    transcript = read_transcript(session_id)

    # 2. Find which skills were invoked
    invoked_skills = scan_for_invocations(transcript)
    # Returns: ["ship-py", "check", "review", "wiki", "handoff"]

    # 3. For each invoked skill, read its quality_gates
    for skill_name in invoked_skills:
        skill_path = find_skill_path(skill_name)
        gates = parse_quality_gates(skill_path)

        # 4. Check each gate
        for gate in gates:
            if not check_evidence(gate, session_id):
                blockers.append(f"{skill_name}: {gate['message']}")

    # 5. Block or allow
    if blockers:
        print(json.dumps({"decision": "block", "reasons": blockers}))
        sys.exit(0)  # block with feedback
    else:
        sys.exit(0)  # allow
```

### How skill invocation detection works

Scan the transcript for patterns:
- Slash commands: `/ship-py`, `/check`, `/review`
- Skill references: `skill_information`, `skills_referenced`
- SKILL.md reads: `read_file.*SKILL\.md`

This is the same pattern `/todo`'s transcript scanner uses.

### Session-scoped evidence matching

Evidence paths use glob patterns with session scoping:
- `P:/.artifacts/**/check-run.json` → `P:/.artifacts/console_<id>/grok-check/.../check-run.json`
- `P:/.data/wiki/concepts/*.md` → any concept file modified this session (via hunk_records)

## 7. Task packets

### TP-01: Build Stop_skill_completion_gate.py
- **Goal:** One Stop hook that checks all invoked skills' quality_gates
- **In scope:** `~/.grok/hooks/Stop_skill_completion_gate.py` (new)
- **Files:**
  - `~/.grok/hooks/Stop_skill_completion_gate.py` — the hook
  - `~/.grok/hooks/scripts/skill_gate_engine.py` — shared engine (reads frontmatter, checks evidence)
- **Acceptance:**
  - Hook scans transcript for invoked skills
  - Hook reads each skill's quality_gates frontmatter
  - Hook checks evidence files exist (session-scoped)
  - Hook blocks with clear message when evidence missing
  - Hook allows when all evidence present
  - Hook passes when no skills invoked (no-op)
- **Falsifier:** hook must not block sessions where no skills were invoked
- **Effort:** M (~150 lines)

### TP-02: Add quality_gates declarations to skills that lack them
- **Goal:** `/check`, `/review`, `/wiki`, `/handoff` declare their evidence
- **In scope:** each skill's SKILL.md frontmatter
- **Files:**
  - `P:/.grok/skills/check/SKILL.md` — add quality_gates
  - `~/.grok/skills/review/SKILL.md` — add quality_gates
  - `~/.grok/skills/wiki/SKILL.md` — add quality_gates (conditional)
  - `~/.grok/skills/handoff/SKILL.md` — add quality_gates (conditional)
- **Acceptance:** each skill's quality_gates correctly name its evidence artifact(s)
- **Effort:** S (~5 lines per skill)

### TP-03: Register the hook
- **Goal:** Hook is registered and fires on every Stop event
- **In scope:** `~/.grok/hooks/skill-completion-gate.json` (registration)
- **Acceptance:** hook fires on session end, produces correct verdict
- **Effort:** S (~10 lines)

### TP-04: Deprecate hardcoded checks in quality_gate.py
- **Goal:** Remove the ship-py-specific hardcoded checks now handled by the generalized gate
- **In scope:** `~/.grok/hooks/scripts/quality_gate.py` — remove ship-py pipeline section
- **Acceptance:** quality_gate.py no longer has skill-specific checks; all enforcement goes through quality_gates declarations
- **Risk:** must verify no existing enforcement is lost in the migration
- **Effort:** S (~deletion)

### TP-05: Test the generalized gate
- **Goal:** Tests covering all gate types and edge cases
- **In scope:** `~/.grok/hooks/tests/test_skill_completion_gate.py`
- **Acceptance:**
  - Test: no skills invoked → pass
  - Test: skill invoked with evidence present → pass
  - Test: skill invoked with evidence missing → block
  - Test: multiple skills invoked, one missing → block with correct message
  - Test: conditional gate where condition not met → skip (pass)
- **Effort:** M (~100 lines)

## 8. Open decisions

1. **Conditional gates.** `/wiki` and `/handoff` shouldn't block sessions that
   didn't produce findings or open work. The gate needs a condition system:
   `condition: session_has_durable_findings`. How to detect this mechanically?
   Options: (a) hunk_records.jsonl shows wiki directory writes, (b) transcript
   scan for finding/recommendation patterns, (c) Python check.

2. **Migration path.** quality_gate.py currently has ship-py-specific checks.
   Should we remove them immediately (risky — existing enforcement is lost if
   the new hook fails) or run both in parallel temporarily (safe but redundant)?

3. **Skill invocation detection.** The transcript scan for skill invocations
   needs to handle: slash commands, skill_information blocks, SKILL.md reads,
   and implicit invocations (agent mentions the skill by name without a slash).
   What's the right precision/recall tradeoff?

## 9. Key files

- `~/.grok/hooks/scripts/quality_gate.py` — existing Stop hook (has ship-py checks)
- `~/.grok/hooks/scripts/quality_gates_frontmatter.py` — existing frontmatter parser
- `~/.grok/skills/ship-py/SKILL.md` — existing quality_gates declaration (reference)
- `P:/.data/wiki/concepts/declarative-quality-gates-skills-declare-evidence.md` — design rationale
- `P:/.data/wiki/concepts/mechanical-enforcement-of-llm-skill-steps-2026.md` — enforcement patterns

## 10. Resumption protocol

1. Read this handoff
2. Read `[[declarative-quality-gates-skills-declare-evidence]]` for the design rationale
3. Read skillgate (https://github.com/renezander030/skillgate) for the field reference
4. Implement TP-01 (the hook engine) first — it's the core
5. Add quality_gates declarations to skills (TP-02)
6. Test end-to-end (TP-05)
7. Migrate from hardcoded checks (TP-04) — last, after the new gate is proven

## 11. What NOT to do

- Do NOT build a separate hook per skill — the whole point is one hook, N declarations
- Do NOT hardcode skill names in the hook — read them from frontmatter
- Do NOT skip the conditional gate system — /wiki and /handoff gates must be conditional or they'll block every session
- Do NOT remove quality_gate.py's existing checks until the new gate is tested and proven

## 12. Suggested next invocation

```
/go implement the generalized skill-completion gate handoff at
P:/docs/handoffs/generalized-skill-completion-gate-20260807/HANDOFF.md
```

## 13. Cold start prompt

```
/go Read P:/docs/handoffs/generalized-skill-completion-gate-20260807/HANDOFF.md and implement it. Start with TP-01 (the hook engine), then TP-02 (skill declarations), then TP-05 (tests). TP-04 (deprecating old checks) is last — don't remove existing enforcement until the new gate is proven.
```

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-07T13:00 | 019fd9ae... | created — investigation complete from /www research + /tp critique + operator design discussion |
