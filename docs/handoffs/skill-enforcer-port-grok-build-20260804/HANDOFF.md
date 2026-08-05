# Handoff — Port skill_enforcer.py to Grok Build as UserPromptSubmit hook

## Status
BLOCKED — native UserPromptSubmit additionalContext does NOT work on Grok Build.
Verified 2026-08-05 via local test. Alternative paths exist but are unverified.

## Objective

Find a mechanism to prevent the agent from treating `/<skill-name>` invocations
as discussion prompts instead of execution commands. Originally proposed as a
UserPromptSubmit hook port of skill_enforcer.py. **Native hook approach is
verified non-functional.** Two alternative paths remain.

## Problem this solves

The agent treats `/ship` (and other skills) as discussion prompts instead of
execution commands. This is the activation gap pattern documented in
[[llm-instruction-non-compliance-activation-gap-2026]]: skills have 6-66%
compliance rate. The quality gates Stop hook (built this session) catches
missing evidence POST-execution, but nothing prevents the discuss-instead-of-
execute pattern BEFORE the agent responds.

## Verified facts

1. **UserPromptSubmit additionalContext does NOT work for native Grok hooks.**
   Local test hook (`~/.grok/hooks/test-ups-injection.json`) with correct JSON
   format produced valid additionalContext JSON on stdout. After 2 Grok Build
   restarts, the marker was NOT visible in the agent's context. Grok Build docs
   confirm: "For passive events, stdout is ignored." UserPromptSubmit is passive.

2. **The Vectorize/Hindsight claim may work via the Claude Code plugin compat layer.**
   Hindsight is a Claude Code plugin (`.claude-plugin/` format). Grok Build
   "natively reads Claude Code plugin format." The compat layer MAY process
   UserPromptSubmit stdout through Claude Code semantics (where it IS a special
   case). This is [INFERENCE] — not verified locally.

3. **The Claude-side skill_enforcer.py exists and was working on Claude Code.**
   Located at `P:/.claude/hooks/UserPromptSubmit_modules/skill_enforcer.py`.
   State files show it was active through mid-July 2026.

4. **The quality gates Stop hook IS working** for post-execution enforcement.
   Built and tested this session. Catches missing evidence after the agent responds.

## Three alternative paths (pick one to investigate)

### Path A: Claude Code plugin format (most promising)

Package the skill_enforcer as a minimal Claude Code plugin with a
`.claude-plugin/plugin.json` + hooks directory. Register it via the plugin
system instead of `~/.grok/hooks/*.json`. The compat layer may process
UserPromptSubmit stdout.

**Test:** create a minimal `.claude-plugin/plugin.json` with a UserPromptSubmit
hook that outputs additionalContext. Install as a plugin. Check if the marker
appears in the agent's context.

### Path B: `.claude/settings.json` registration

Register the hook in `P:/.claude/settings.json` instead of `~/.grok/hooks/*.json`.
The Grok Build docs say `.claude/settings.json` hooks "are read as well" — this
dispatch path may go through the compat layer rather than the native runner.

**Test:** move `test-ups-injection.json` content into `.claude/settings.json`
hook format. Restart. Check if the marker appears.

### Path C: Stop-hook-only enforcement (fallback)

Accept that pre-execution enforcement is not available on Grok Build. Rely
entirely on the quality gates Stop hook (Layer 2). The discuss-instead-of-execute
pattern costs one round-trip (agent discusses → Stop hook blocks → agent
re-executes). This is the current working state.

**Effort:** zero — already implemented. Cost: one wasted turn per skip.

## Acceptance criteria (for whichever path is chosen)

1. The mechanism fires when the operator types `/<skill-name>`
2. The agent receives additional context telling it to execute, not discuss
3. The mechanism does NOT fire for non-skill prompts
4. The mechanism completes in <500ms
5. The mechanism fails open (errors don't block the prompt)

## Key files

- **Claude-side source (reference):** `P:/.claude/hooks/UserPromptSubmit_modules/skill_enforcer.py`
- **Claude-side tests (reference):** `P:/.claude/hooks/tests/test_skill_first_enforcement.py`
- **Quality gates (working Layer 2):** `~/.grok/hooks/scripts/quality_gate.py` + `quality_gates_frontmatter.py`
- **Wiki concept (verified):** `P:/.data/wiki/concepts/userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build.md`
- **Test hook (proves native path doesn't work):** `~/.grok/hooks/test-ups-injection.json` + `P:/tmp/test_ups_hook.py`

## Handoff is wrong if

- Path A or B is tested and works (the handoff should then become an implementation task)
- Grok Build adds UserPromptSubmit stdout processing in a future release
- The operator decides Path C (Stop-hook-only) is sufficient and closes this handoff

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
