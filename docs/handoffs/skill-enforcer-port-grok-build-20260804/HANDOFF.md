# Handoff — Port skill_enforcer.py to Grok Build as UserPromptSubmit hook

## Status
OPEN — research complete, implementation not started.

## Objective

Port the Claude-side skill enforcement system (`P:/.claude/hooks/UserPromptSubmit_modules/skill_enforcer.py`)
to Grok Build as a native UserPromptSubmit hook. The hook detects `/<skill-name>`
in the user prompt and injects additionalContext reminding the agent to execute
the skill, not discuss it.

## Problem this solves

The agent treats `/ship` (and other skills) as discussion prompts instead of
execution commands. This is the activation gap pattern documented in
[[llm-instruction-non-compliance-activation-gap-2026]]: skills have 6-66%
compliance rate. The quality gates Stop hook (built this session) catches
missing evidence POST-execution, but nothing prevents the discuss-instead-of-
execute pattern BEFORE the agent responds.

The 3-layer model from [[skill-enforcement-layers]]:
- Layer 1 (UserPromptSubmit, pre-response) — NOT YET IMPLEMENTED on Grok Build
- Layer 2 (Stop hook, post-response) — quality_gate.py + quality_gates_frontmatter.py (shipped this session)

This handoff implements Layer 1.

## Verified facts

1. **UserPromptSubmit CAN inject additionalContext on Grok Build.** Vectorize/Hindsight
   plugin does this in production (https://hindsight.vectorize.io/sdks/integrations/grok-build).
   A local test hook was registered at `~/.grok/hooks/test-ups-injection.json`.
   Receipt: wiki concept `[[userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build]]`
   (corrected 2026-08-04).

2. **The Claude-side implementation exists and was working.** Located at
   `P:/.claude/hooks/UserPromptSubmit_modules/skill_enforcer.py` + `skill_context_writer.py`.
   State files (`skill_first_enforcement.jsonl`, 518KB) show it was active through
   mid-July 2026. Test suite: `P:/.claude/hooks/tests/test_skill_first_enforcement.py` (13KB).

3. **The Claude-side enforcer was ~50% effective** per [[skill-enforcement-layers]]:
   "UserPromptSubmit injection is just context. The model can ignore it."

4. **UserPromptSubmit is non-blocking** on Grok Build (docs line 89). The hook
   cannot block the prompt — only PreToolUse and Stop can block. The hook
   injects advisory context; the Stop hook provides enforcement.

## Design

### Hook: `~/.grok/hooks/UserPromptSubmit_skill_enforcer.py`

Registered in: `~/.grok/hooks/skill-enforcer.json`

**Behavior:**
1. Read user prompt from stdin (JSON payload, field `userPrompt` or `prompt`)
2. Detect `/<skill-name>` pattern (regex: `^/([a-zA-Z][\w-]*)`)
3. Load skill catalog from `P:/.data/wiki/concepts/skill-catalog.md` or
   `~/.grok/skills/*/SKILL.md` frontmatter
4. If the slash command matches a known skill:
   - Inject additionalContext: "You are executing the **/<skill-name>** skill.
     This is an execution command — follow the skill body step by step.
     Do not substitute a discussion or planning response for skill execution."
5. If the skill name is unknown, do nothing (let the platform handle it)

**Additional context to inject (the "don't discuss" reminder):**
```
SKILL EXECUTION: The operator invoked /<skill-name>. This is an execution
command, not a discussion prompt. Follow the skill body step by step. If the
argument text looks like a question, it is SCOPE for the skill, not a
separate question to answer. Execute first, discuss only if the skill's
own steps require it.
```

### Registration: `~/.grok/hooks/skill-enforcer.json`
```json
{
  "UserPromptSubmit": [
    {
      "matcher": "",
      "hooks": [
        { "type": "command", "command": "python C:/Users/brsth/.grok/hooks/UserPromptSubmit_skill_enforcer.py", "timeout": 3 }
      ]
    }
  ]
}
```

### What NOT to port from the Claude-side system

- `skill_context_writer.py` — on Grok Build, the platform already injects
  SKILL.md bodies via `<skill_information>` system-reminder blocks. No need
  for the hook to inject skill body content.
- `skill_first_enforcement.jsonl` state tracking — the Claude-side system
  tracked per-session skill state. On Grok Build, the quality_gates_frontmatter.py
  transcript scanner already tracks invoked skills. Duplicating state is
  unnecessary.
- Pattern gates, question gates — these were Claude-specific complexity
  for detecting skill bypass patterns. On Grok Build, the Stop hook quality
  gates handle enforcement. The UserPromptSubmit hook only needs the
  pre-execution advisory injection.

## Acceptance criteria

1. Hook fires on every UserPromptSubmit (verified via debug output)
2. Hook detects `/<known-skill-name>` in prompt text
3. Hook injects additionalContext with the "execute, don't discuss" message
4. additionalContext is visible to the model (verified by test hook marker)
5. Hook does NOT fire for non-skill prompts (no false positives)
6. Hook completes in <500ms (timeout is 3s)
7. Hook fails open (errors don't block the prompt)

## Key files

- **Claude-side source (reference):** `P:/.claude/hooks/UserPromptSubmit_modules/skill_enforcer.py`
- **Claude-side context writer (reference):** `P:/.claude/hooks/UserPromptSubmit_modules/skill_context_writer.py`
- **Claude-side tests (reference):** `P:/.claude/hooks/tests/test_skill_first_enforcement.py`
- **Skill catalog:** `P:/.data/wiki/concepts/skill-catalog.md`
- **Quality gates (complementary Layer 2):** `~/.grok/hooks/scripts/quality_gate.py` + `quality_gates_frontmatter.py`
- **Wiki concept (corrected):** `P:/.data/wiki/concepts/userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build.md`
- **Wiki concept (3-layer model):** `P:/.data/wiki/concepts/skill-enforcement-layers.md`
- **Wiki concept (activation gap):** `P:/.data/wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md`
- **Test hook (verify additionalContext works):** `~/.grok/hooks/test-ups-injection.json` + `P:/tmp/test_ups_hook.py`

## Scope

- **In scope:** `~/.grok/hooks/UserPromptSubmit_skill_enforcer.py` (new), `~/.grok/hooks/skill-enforcer.json` (new)
- **Out of scope:** modifying quality_gate.py or quality_gates_frontmatter.py (already shipped), modifying any SKILL.md

## Handoff is wrong if

- UserPromptSubmit additionalContext does NOT work on Grok Build (test hook will confirm)
- The platform already injects a "execute this skill" reminder (making the hook redundant)
- The ~50% advisory effectiveness isn't worth the hook complexity (operator decision)
