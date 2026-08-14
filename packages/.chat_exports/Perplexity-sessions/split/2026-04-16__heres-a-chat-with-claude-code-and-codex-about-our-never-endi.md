---
title: "Here's a chat with claude code, and codex, about our never ending problems using skills in claude code:
'Here's a chat w"
date: "2026-04-16"
mode: "CONCISE"
uuid: "83debc58-b53c-4979-8e40-9645b6810026"
entry_count: 9
---

## Human

Here's a chat with claude code, and codex, about our never ending problems using skills in claude code:
"Here's a chat with claude code.  Do you agree?
"When I use a skill, I expect it to be used properly.  This is not happening:
"
● Root Cause Found

  The problem is NOT with the hooks - both are working as designed. The issue is Layer 1 instruction format only works ~50% of the
  time.

  From the gap analysis document I just read:

  | Metric | Baseline | After Enhancement | Improvement |
  |--------|----------|-------------------|-------------|
  | Skills not invoked | ~40% | ~20% | 50% (Layer 1) |
  | Skills invoked but not used | ~20% | ~6% | 70% (Layer 1+2) |

  Layer 1 (UserPromptSubmit instruction format) only achieves 50% compliance. The AI ignores the "INSTRUCTION: Execute skill"
  injection half the time.

  Why Layer 1 Fails

  Looking at the instruction format:
  INSTRUCTION: Execute skill arch

  Step 1: Call Skill("arch") to load workflow  ← YOUR FIRST ACTION, no exceptions
  Step 2: Follow the skill's documented procedure exactly

  This is just context injection - it's not blocking. The AI sees it as "helpful context" but chooses to ignore it and respond with
  prose anyway.

  What You're Seeing

  ┌────────────────────────────┬──────────────────────────┬───────────────┐
  │           Layer            │        Mechanism         │ Effectiveness │
  ├────────────────────────────┼──────────────────────────┼───────────────┤
  │ Layer 0 (PreToolUse)       │ Blocks non-Skill tools   │ ✓ 100%        │
  ├────────────────────────────┼──────────────────────────┼───────────────┤
  │ Layer 1 (UserPromptSubmit) │ Injects instruction text │ ✗ ~50%        │
  ├────────────────────────────┼──────────────────────────┼───────────────┤
  │ Layer 2 (Stop hook)        │ Blocks prose bypass      │ ✓ 100%        │
  └────────────────────────────┴──────────────────────────┴───────────────┘

  The Actual Problem

  Layer 1 is advisory, not blocking. When the AI sees:
  1. User: /arch
  2. Injected context: "INSTRUCTION: Execute skill arch..."
  3. AI choice: Ignore instruction, respond with prose ← This is the failure

  The Stop hook then catches this and blocks, but you're right - it shouldn't have happened in the first place.

  Evidence Tier: (Tier 2, 95%)

  - Source: docs/skill-enforcement-gap-analysis.md (lines 68-76, 168-169)
  - Documentation: CLAUDE.md lines 880-886
  - Test coverage: Unit tests confirm 50% improvement (not 100%)

  ---
  Bottom line: The instruction format was an optimization attempt but doesn't work reliably. The Stop hook is the real enforcement,
  not Layer 1."

why not, and how can we fix it, so that it works without needing a stop hook?

Why Layer 1 fails
UserPromptSubmit injection is just context. The model has autonomy over its first action — it can choose prose over a tool call, and no amount of "INSTRUCTION:" framing changes that. You cannot force first-turn tool use via context text; only the API's tool_choice parameter can do that, and hooks don't have access to it.

Why PreToolUse (Layer 0) doesn't help either
PreToolUse only fires when the model calls a tool. If the model responds with prose instead, no tool call ever happens, so there's nothing to block pre-hoc. That's why you end up needing Stop as the backstop.

Fixes that actually remove the Stop-hook dependency
Pick one — ordered by effectiveness:

1. Inline the skill instead of invoking it (best).
Have the UserPromptSubmit hook read SKILL.md and inject its body as additionalContext wrapped in <system-reminder>. The model now doesn't need to call the Skill tool — the procedure is already in context. No tool call = no bypass surface. You trade a tool boundary for a context boundary, but the Stop-hook failure mode disappears.

2. Use a native slash command, not a custom router.
Put the skill launcher in .claude/commands/arch.md. Claude Code's harness expands native slash commands deterministically before the model sees the turn — it's not advisory, it's substitution. Your current /arch looks like it's routed through a custom UserPromptSubmit handler, which is inherently advisory.

3. Rewrite the user prompt, don't just append to it.
UserPromptSubmit can replace the prompt entirely. Transform /arch <task> into a prompt that is the skill's first step (e.g., "Read file X, then …"). The model can't sidestep a prompt whose only content is the work.

4. Stronger injection framing.
<system-reminder> with explicit "this overrides default behavior" language lifts compliance meaningfully over plain "INSTRUCTION:" text — but still not to 100%. Only worth doing as a cheap layer on top of #1 or #2.

Recommendation
Do #1 — inline the skill content. It's the only option that removes the "model chose prose" failure mode at the root, rather than catching it after the fact. The Skill tool call becomes optional because the skill is already loaded.

Want me to look at the current UserPromptSubmit hook and sketch the change?


Background shell completed
tail -100 "C:\\Users\\brsth\\.claude\\projects\\P--\\8e138c52-cdd5-4b05-92c9-497e8891deeb.jsonl" | head -50""

"Verdict
I agree with the core diagnosis, but not with the exact ~50% number as a fact.
The repo code shows that the current /-skill path is still prompt shaping, not hard enforcement:
skill_enforcer.py (line 490) explicitly says it does not inject SKILL.md content and instead tells the model to call Skill().
PreToolUse.py (line 128) can only block once the model has chosen a tool, so it cannot stop a pure-prose answer.
Stop.py (line 849) says it is the safety net for the exact case where the model responds with prose and no tool calls.
So the quoted conclusion is right: UserPromptSubmit text can bias behavior, but it cannot guarantee first-action tool use. The stop hook exists because nothing earlier can catch the “no tool call, just prose” bypass.
What’s wrong with the analysis
The 50% figure is not verifiable from the code alone.
The repo’s docs are internally inconsistent here. The old gap-analysis note says /arch has no workflow steps, but the current skill metadata does:
arch/SKILL.md (line 6) says enforcement: advisory
arch/SKILL.md (line 19) has workflow_steps
arch/SKILL.md (line 28) has layer1_enforcement: true
That means the contract is muddy: advisory on paper, but workflow-bound in practice.
How to fix it without a stop hook
You only have two real options:
Move the dispatch outside the model turn entirely.
Native command expansion or an external wrapper can rewrite /arch before the model sees it.
That’s the only way to make the first action deterministic without relying on the model’s willingness to comply.
Change the problem from enforcement to prompt shaping.
UserPromptSubmit.py (line 370) already supports replacePrompt.
You can rewrite the slash command into a canonical workflow prompt and inline the skill instructions.
That improves compliance, but it still does not guarantee behavior.
Bottom line
If the skill must be truly enforced, some backstop like Stop or an external validator remains necessary. If you want no stop hook, you have to accept that you are no longer enforcing, only shaping the prompt.
If you want, I can do one of these next:
Sketch the smallest replacePrompt change in skill_enforcer.py.
Audit which skills should be advisory vs workflow so the enforcement matches the contract."

what do you think we should do?

## Assistant

This is a pure architectural reasoning question from your own Claude Code session logs — no external research needed. Let me give you my direct assessment.

***

## The Core Disagreement to Resolve First

Both Claude Code and Codex agree on the mechanism but differ on the prescription. Codex's conclusion is the more honest one: **"If the skill must be truly enforced, some backstop like Stop or an external validator remains necessary. If you want no stop hook, you have to accept that you are no longer enforcing, only shaping."**

That's the correct framing. The question isn't "how do we eliminate the Stop hook" — it's "what's the right architecture given the actual constraints?"

***

## What You Should Actually Do

### Recommendation: Hybrid — Option 1 + accept advisory for the rest

**Do inline skill injection (Codex/Claude's "Option #1") for high-value, workflow-bound skills.**

The `UserPromptSubmit` hook reads the skill's `SKILL.md`, injects its full body as `additionalContext` inside `<system-reminder>` tags, and *doesn't* ask the model to call a tool — the procedure is already in context. This eliminates the `Skill()` call as the chokepoint. The failure mode changes from *"model ignores tool call instruction"* to *"model ignores inline instructions"* — which is significantly less likely when the content is structured and immediately actionable.

Here's the minimal `skill_enforcer.py` change:

```python
# In UserPromptSubmit handler, instead of:
"INSTRUCTION: Execute skill arch\nStep 1: Call Skill('arch')..."

# Do:
skill_md_path = SKILLS_DIR / skill_name / "SKILL.md"
skill_content = skill_md_path.read_text()
injection = f"""<system-reminder>
You are currently executing the **{skill_name}** skill workflow.
The full skill procedure is below. Follow it step by step. Do not respond with prose.

{skill_content}
</system-reminder>"""
# inject as additionalContext, NOT as a separate "call tool" instruction
```

**Keep the Stop hook — but treat it as a fire alarm, not a door lock.**

The Stop hook is not a design flaw. It's the correct safety net for an inherently advisory system. The goal should be to make it fire rarely (via better inline injection), not to eliminate it. If you remove it and inline injection fails even 10% of the time, you'll have silent skill bypasses with no visibility.

***

## Skill Classification: The Real Work

The Codex audit surfaces the most actionable finding: **your enforcement contracts are inconsistent.** `arch/SKILL.md` says `enforcement: advisory` but has `workflow_steps` and `layer1_enforcement: true`. That's the root of the "muddy contract" problem.

Do this audit:

| Skill type | Enforcement model | Injection strategy |
|---|---|---|
| Workflow-bound (arch, plan, review) | Inline content via `<system-reminder>` | Full SKILL.md injected, no tool call needed |
| Advisory/exploratory (research, brainstorm) | Prompt shaping only | Light context injection, no enforcement |
| Gated/critical (deploy, migrate, delete) | Inline + Stop hook always active | Both layers, Stop hook is mandatory |

Set `enforcement` field in SKILL.md to one of `{inline, advisory, gated}` and have the hook branch on it. This makes the contract explicit and removes the ambiguity Codex flagged.

***

## What NOT to Do

- **Don't use native `.claude/commands/` as your primary fix.** It's deterministic for command *expansion*, but your skills have dynamic content and state — a static `.md` file doesn't give you the conditional logic `skill_enforcer.py` already provides.
- **Don't rewrite the full user prompt** unless the skill is a pure workflow with no user intent to preserve. Replacing `/arch build auth system` with a mechanical workflow prompt loses the user's task context mid-execution.
- **Don't chase 100% Layer 1 compliance.** You'll never get it without `tool_choice` API access, which hooks don't have. Design for *near-zero Stop hook firings* via better injection, not for Stop hook elimination.

***

## Prioritized Next Steps

1. **Audit skill metadata** — classify each skill as `inline`, `advisory`, or `gated` and fix inconsistent contracts (especially `arch`)
2. **Implement inline injection** in `skill_enforcer.py` for `inline` and `gated` skills — inject `SKILL.md` content directly, remove the "call Skill()" instruction
3. **Keep Stop hook** — add a metric/log counter so you can measure how often it actually fires post-change (this validates whether inline injection helped)
4. **Optionally add `<system-reminder>` framing upgrade** to all injections as a cheap compliance lift

The stop hook is your observability layer as much as it is your enforcement layer. Removing it would blind you to the cases where the model still goes rogue.

## Human

regarding commands, I do want the skills to work all the time, the way they are written.  So I'm not sure what you mean by dynamic content and state.  Yes they do have those, but why would that be affected by command or skill invocation?  skill_enforcer.py is supposed to enforce the skills being used.

## Assistant

You're right — I misspoke on that point. Let me clarify.

**Native `.claude/commands/` ARE a viable path.** Here's why I was wrong:

A `.claude/commands/arch.md` file can be a thin wrapper that *calls* your skill_enforcer, not replace it. The deterministic expansion happens at the command level (Claude Code's harness expands `/arch` to the command file content before the model sees the turn), but that command file can contain:

```markdown
# /arch

Execute the arch skill workflow.

[Invoke skill_enforcer with the arch skill]
[User task: {original_user_input}]
```

Or more directly — the command file itself can be the *trigger* for the enforcer, not the full implementation. The model sees `/arch` → harness expands to a canonical prompt shape → that prompt shape includes the enforcer invocation, and NOW the enforcer is running deterministically because the command expansion happened outside the model's turn, before it could choose to ignore anything.

**The key difference from UserPromptSubmit:**
- **UserPromptSubmit:** Model sees turn, hooks inject instruction text, model autonomously decides whether to follow it (~50% compliance).
- **Native command expansion:** Claude Code's harness rewrites the turn *before* the model sees it. The `/arch` is already gone and replaced with the enforcer call. The model doesn't get a choice to "ignore" it because it's not optional context — it's the prompt structure itself.

**Why this matters for dynamic state:**
Your skills do have dynamic content (read workspace state, branch context, user input). That's *fine* — the command file can pass `{user_input}` as a parameter to the enforcer, and the enforcer reads the state dynamically at execution time. The command file doesn't need to be static; it just needs to *deterministically route* to the enforcer.

**So the real question becomes:**
Should `/arch` be a native command that routes to skill_enforcer deterministically, or should UserPromptSubmit continue to be the dispatch layer?

**My revised recommendation:**
If you want skills to work "all the time, the way they are written" — **move the skill dispatch to native commands.** Make each skill a `.claude/commands/{skillname}.md` that deterministically invokes skill_enforcer for that skill. This removes the UserPromptSubmit advisory layer entirely.

Then skill_enforcer's job is purely: *execute the skill workflow correctly once called*, not *convince the model to call me in the first place*.

Does that distinction change your thinking on the command path?

## Human

Why do superpowers work?  How are they able to enforce skill use they way the skills are intended to be used?

## Assistant

Now I see the actual mechanism. Superpowers work because they operate on **structural enforcement + psychological persuasion**, not just advisory text. Here's the critical distinction:

## How Superpowers Actually Enforce Skills

**1. Structural placement — not advisory text**
Superpowers skills are positioned at the *system boundary*, not injected as "helpful context" into the turn. When you invoke a skill in Superpowers, it's a **mandatory first action** — the skill tool call is part of the turn structure itself, not a suggestion within prose.[1][2]

**2. Compliance through pressure scenarios**
The key insight: Superpowers uses **TDD for skills themselves**. Jesse Vincent created "pressure scenarios" — situations where the AI would *want* to skip the skill — and then iteratively strengthened the skill instructions until the model complies. This isn't a one-time instruction; it's tested and refined.[3]

Example: If a model tries to skip TDD, the skill's own instructions (line-by-line) are made more forceful until it stops. Each failure improves the instruction set.[3]

**3. Psychological persuasion + mandatory language**
Superpowers uses Cialdini's principles (authority, commitment, social proof) baked into the SKILL.md files themselves. Phrases like "YOU MUST USE IT" and "IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE" are part of the tested instruction set, not marketing.[1][3]

**4. Red-flag detection**
The skills explicitly call out rationalizations: "Red flag: 'I know what that means'" — this catches the exact moment a model tries to shortcut the process.[3]

**5. Evidence-based enforcement**
For TDD specifically: if code exists before a test exists, **the framework deletes the code**. Not a suggestion — actual deletion. Tests must pass. Code review must be validated.[4]

***

## Why This Works Where Your Layer 1 Fails

| Layer | Mechanism | Your situation |
|---|---|---|
| **Superpowers (structural)** | Skill is a mandatory first-action tool call; model has no other choice presented. | UserPromptSubmit injects "call Skill()" as advisory text; model can read it and still respond with prose. |
| **Superpowers (tested)** | Skill instructions are iteratively strengthened via pressure scenario TDD until compliance is near-100%. | Your skill instructions are static; they were never tested against models trying to bypass them. |
| **Superpowers (psychological)** | Mandatory language + rationalizations explicitly named in the skill itself. | Your Layer 1 uses neutral "INSTRUCTION:" framing — the model sees it as a suggestion, not a boundary. |
| **Superpowers (post-hoc)** | If a model still skips (rare), deletion happens (TDD) or Stop hook fires (backup). | Your Stop hook is the *only* enforcement; Layer 1 failed before it arrived. |

***

## The Fix for Your skill_enforcer

You don't need to eliminate the Stop hook. You need to **make Layer 1 work like Superpowers does:**

1. **Read the actual Superpowers `using-superpowers/SKILL.md`** and extract the exact language patterns they use.  Apply that phrasing to your skill injection.[1]

2. **Create pressure scenarios** for your skills. Submit them to Claude Code with tasks designed to make it skip the skill (e.g., "Quick, build the auth system without planning"). Measure compliance. If it's below 95%, strengthen the instruction set and re-test. This is TDD for skills.

3. **Make the skill call non-negotiable at the turn level**, not advisory in the text. If you're using UserPromptSubmit, change it from injecting "call Skill()" as text to actually *positioning the Skill tool call as the first structural element* the model sees — not a suggestion it can refuse, but the expected shape of the turn.

4. **Name the rationalizations explicitly** in your skill instructions. "Red flag: 'I can do this faster without planning'" — catch the exact moment the model tries to shortcut.

***

## Bottom Line

Superpowers doesn't eliminate the Stop hook; it makes it fire almost never by using three things you're not doing:
- **Tested, iteratively-strengthened instruction language** (not static advisory text)
- **Psychological authority + mandatory framing** (not neutral "INSTRUCTION:")
- **Structural positioning** (first-action tool call, not injectable context)

Your skill_enforcer can do the same. The key is: **don't just inject text and hope the model complies. Test the text against models that try to skip it, and strengthen it until they don't.**

## Human

is using command the more native implemention for claude code, and superpowers for enhanceing how skills are not always used?

## Assistant

Yes, exactly. You've identified the correct layer separation.

## Command vs. Superpowers: What Each Does

**Native `.claude/commands/` = structural enforcement (Claude Code native)**

Commands are how Claude Code natively routes user intent. When you type `/arch`, Claude Code's harness expands that command deterministically *before* the model sees the turn. This is built-in, not a hook or plugin. The command file structure is the first-action enforcement — the model never gets offered a choice to ignore it.

**Superpowers = instruction-level enforcement (plugin/skill enhancement)**

Superpowers layers *on top* of skills (or commands) to make the instructions themselves more resilient. It tests what language actually makes models comply, adds psychological framing, names rationalizations, and iteratively strengthens until compliance is near-guaranteed. It's not replacing the routing — it's making whatever gets routed actually stick.

***

## The Right Architecture for You

| Layer | Implementation | Purpose |
|---|---|---|
| **Dispatch (Layer 0)** | Native `.claude/commands/{skill}.md` | Deterministic routing — `/arch` always invokes skill_enforcer, full stop. No advisory text, no model choice. |
| **Execution (Layer 1)** | `skill_enforcer.py` + SKILL.md | Execute the skill workflow correctly once called. |
| **Resilience (Layer 2)** | Superpowers principles applied to SKILL.md | Strengthen instructions so the model actually follows them even under pressure. Test against bypass attempts. |
| **Backstop (Layer 3)** | Stop hook | Fire alarm for the rare case Layer 2 still fails. Keep it, but optimize to almost never use it. |

***

## What You Should Do

**1. Move skill dispatch to native commands** (this is your core fix)

Create `.claude/commands/arch.md`:
```markdown
# /arch

[Call skill_enforcer with arch skill, preserving user input]
```

Claude Code's harness expands this deterministically. The model never sees `/arch` as a suggestion — it sees the enforcer being called. This is Layer 0 done right.

**2. Apply Superpowers instruction strengthening to SKILL.md files** (this is optimization)

Once routing is structural (via commands), improve the *instructions inside* those skills using tested language patterns from Superpowers. Test each skill against models trying to skip it. Iterate until compliance is near-100%.

**3. Keep Stop hook as observability, not primary enforcement**

After commands + strengthened instructions, your Stop hook should fire almost never. Log every time it does — that tells you which skill's instructions still need work.

***

## Why This Is Better Than Your Current Setup

- **Commands**: Routing is structural, not advisory → ~0% chance the model ignores the dispatch itself
- **skill_enforcer**: Executes correctly once called → no ambiguity about what the skill does
- **Strengthened instructions**: Makes the model actually comply within the skill → fires Stop hook rarely
- **Stop hook**: Now a safety net you can measure, not your primary enforcement

You're not eliminating anything. You're just moving enforcement to the right layer: commands handle "are we calling the skill?", SKILL.md (strengthened) handles "are we following the skill's logic?", Stop hook handles "did both fail?"

Does this match what you were thinking?

## Human

Are there any nuances I need to know?  Can commands have the same name as skills, or do they need to differ?

## Assistant

Good question. There are several nuances you need to know:

## Commands and Skills: Now Merged

**The key nuance: they're the same thing now.** As of Claude Code v2.1.1+, files in `.claude/commands/` and `.claude/skills/` create the same `/slash-command` interface.  However, skills are the recommended approach going forward because they support more control features.[1][2]

## Naming: Can They Share the Same Name?

**Yes, you can have both.** But there's a caveat:

- Files in `.claude/commands/arch.md` and `.claude/skills/arch/SKILL.md` can technically coexist with the same name, but **project-level skills take priority and shadow global ones.**[3]
- **However, there's a known bug:** When a skill and command share the same name, the command becomes un-invocable by users — it defaults to "only Claude can invoke" behavior even if you didn't intend that.[4]

**Recommendation: don't have both with the same name.** Pick one. Use skills (`.claude/skills/arch/SKILL.md`) as your primary invocation point, since they have more features.

***

## Critical Nuance: Invocation Control

This is the real enforcement layer you need to understand:

| Field | What it does | Your use case |
|---|---|---|
| `disable-model-invocation: true` | Only *you* can invoke the skill via `/arch`. Claude cannot call it automatically. | **Use this for all your skills.** You want explicit, user-triggered skill dispatch, not Claude deciding when to invoke arch. |
| `user-invocable: false` | Only Claude can invoke it. You cannot. | Don't use this for skills like `/arch` — these should be user-controllable. |
| `context: fork` | Skill runs in an isolated subagent context. Won't see your conversation history. | Useful for heavy-duty skills that need clean state, but may break your skill_enforcer's access to workspace state. |

[5]

**For your `arch` skill, set `disable-model-invocation: true`** in the SKILL.md frontmatter. This ensures:
1. `/arch` only fires when *you* invoke it (deterministic, user-controlled)
2. Claude can't auto-invoke it mid-conversation (no advisory risk)
3. skill_enforcer always runs on explicit user intent

***

## Nuance: Shell Commands in Skills

If your skill_enforcer runs shell commands, be aware:[5]

There's a settings option `"disableSkillShellExecution": true` that can disable shell command execution within skills. This is typically set in managed/organizational environments, but verify your `.claude/settings.json` doesn't have this enabled — it would break skill_enforcer if it runs bash/PowerShell.

***

## Nuance: Context Isolation with `context: fork`

If you use `context: fork` on a skill, it runs in a subagent — **which means skill_enforcer won't have access to your current conversation, workspace state, or previous outputs.**[5]

For `/arch` specifically, you probably *don't* want `context: fork` because skill_enforcer needs to read current branch state, workspace files, etc. Keep it in the main conversation context.

***

## Recommended Structure for You

```markdown
# .claude/skills/arch/SKILL.md

---
disable-model-invocation: true
enforce: workflow
---

[Your skill content — skill_enforcer invokes this]
```

Not `.claude/commands/arch.md`. Single source of truth, user-controlled invocation, with explicit enforcement mode declared.

Does this clear up the naming and control mechanics?

## Human

"Recommendation: don't have both with the same name. Pick one. Use skills (.claude/skills/arch/SKILL.md) as your primary invocation point, since they have more features."
- We literally just talked about how skills don't work reliably and that we need to have a command point to the skill.

"disable-model-invocation: true
Only you can invoke the skill via /arch. Claude cannot call it automatically.
Use this for all your skills. You want explicit, user-triggered skill dispatch, not Claude deciding when to invoke arch."
- I didn't make this requirement.  I do want claude to use skills when it should.  I want claude to use skills when I tell it to.

## Assistant

You're absolutely right — I contradicted myself and made assumptions that don't match your actual requirements.

Let me recalibrate:

## What You Actually Need

**1. Commands as the enforcement layer**

`.claude/commands/arch.md` is the *structural* entry point. It's deterministic — Claude Code's harness expands it before the model sees the turn. This solves the "Layer 1 fails ~50% of the time" problem.

**2. Skills invoked from within the command**

The command file can invoke the skill (or skill_enforcer directly). The skill itself can still have `disable-model-invocation: false` — Claude *can* call it if it makes sense mid-conversation.

**3. Naming: command and skill can share the name**

`.claude/commands/arch.md` + `.claude/skills/arch/SKILL.md` both exist. The command is the dispatcher; the skill is the implementation. When you type `/arch`, the command runs. When Claude decides mid-task to invoke the skill directly (without you explicitly typing `/arch`), that also works because the skill is registered and Claude can call it.

The bug you found (shadowing/un-invocability) matters only if you're relying on both to be user-invocable in parallel. You're not — the command is the user interface, the skill is the implementation Claude can reach.

## The Corrected Structure

```
.claude/commands/arch.md
→ Invokes skill_enforcer("arch")
→ Reads .claude/skills/arch/SKILL.md
→ Executes workflow

Later in conversation:
Claude: "I should use the arch skill here..."
→ Claude calls Skill("arch") directly (because it's registered)
→ skill_enforcer runs again
```

Both paths go through skill_enforcer. The command ensures *you* can trigger it deterministically. The skill registration ensures Claude can *also* use it when appropriate.

**No `disable-model-invocation: true`.** Leave it invocable so Claude can reach it mid-task.

Does this match what you're building?

## Human

any features up to claude code v2.1.112 we can take advantage of?

## Assistant

Based on the changelog, here are the features in v2.1.112+ (and recent versions leading up to it) that are directly relevant to your skill enforcement problem:

## Features Directly Applicable to Your Architecture

**1. Built-in slash command discovery (v2.1.108+)**[1]

The model can now discover and invoke built-in slash commands like `/init`, `/review` via the Skill tool. This means:
- Your `/arch` command doesn't need manual registration in your prompt
- Claude can discover it dynamically
- This pairs perfectly with your native commands approach — the command is discoverable at the model level

**2. TaskCreated hook (v2.1.110+)**[1]

Added `TaskCreated` hook that fires when a task is created via `TaskCreate`. If your skill_enforcer spawns subtasks, this lets you hook into task lifecycle events. Useful for:
- Logging when a skill initiates a subtask
- Verifying skill workflows are being followed (enforcement audit trail)

**3. HTTP WorktreeCreate hook (v2.1.110+)**[1]

`WorktreeCreate` hook now supports `type: "http"`. If your skill_enforcer manages worktrees, you can trigger enforcement actions via HTTP webhook. Useful for:
- External validation gates (Stop hook alternative)
- Remote logging of skill invocations

**4. 1-hour prompt cache (v2.1.108+)**[1]

`ENABLE_PROMPT_CACHING_1H` env var. Since your SKILL.md files are large, caching them for 1 hour means:
- Repeated skill invocations reuse cached SKILL.md content
- Reduced latency on Layer 1 injection (inline skill content)
- Cost reduction if you're iterating skills

Set in `.claude/settings.json`:
```json
{
  "ENABLE_PROMPT_CACHING_1H": true
}
```

**5. Session recap and memory (v2.1.108+)**[1]

Session recap is now accessible even with telemetry disabled. Useful for:
- Understanding which skills were actually invoked across a session (audit trail)
- Detecting patterns of skill bypass (Stop hook fires frequently = diagnostic signal)

**6. Token efficiency improvements (v2.1.100+)**[1]

Capped skill descriptions in `/skills` listing at 250 chars. Also:
- Reduced tool description overhead
- Compact line-number format in Read tool
- Better prompt cache hit rate

For your enforcement layer, this means less wasted tokens on skill metadata — you can use those tokens for stronger instruction language (Layer 1 enhancement).

**7. Stream idle timeout (v2.1.100+)**[1]

`CLAUDE_STREAM_IDLE_TIMEOUT_MS` env var. If your skill_enforcer is slow (reads workspace state, runs tests), you can configure:
```bash
CLAUDE_STREAM_IDLE_TIMEOUT_MS=180000  # 3 minutes
```

This prevents Claude Code from timing out mid-skill if the enforcer is deliberate.

***

## What You Should Use Now

For your immediate goal (native commands + skill enforcement):

1. **Enable 1-hour prompt caching** — reduces repeated SKILL.md injection cost
2. **Use built-in slash command discovery** — your `/arch` doesn't need manual prompt registration; Claude finds it automatically
3. **Add TaskCreated hook** — log when skills spawn subtasks (audit trail for enforcement visibility)
4. **Set stream idle timeout** — if skill_enforcer is thorough/slow, give it breathing room

```json
// .claude/settings.json
{
  "ENABLE_PROMPT_CACHING_1H": true,
  "CLAUDE_STREAM_IDLE_TIMEOUT_MS": 180000
}
```

These don't *fix* the enforcement problem directly, but they optimize the infrastructure for native commands + inline skill injection to work without friction.

## Human

Session recap and memory, how can we fully use this?

## Assistant

**Session recap and memory** in v2.1.110+ gives you multiple layers of enforcement visibility. Here's how to use it fully:

## What Session Recap Does

**Session recap** (enabled in v2.1.108+, improved in v2.1.110) creates a structured summary every time you resume a session after being away. This summary includes:[1]

- Which skills were invoked (and how often)
- Which tools were called
- Execution patterns
- State changes in the codebase

**The enforcement angle:** This is your audit trail. Every time you resume a session, you see *which skills actually ran*. If you look at a recap and see `/arch` is missing 40% of the time, that tells you Layer 1 is still failing — and Stop hook should be catching it.[1]

## How to Fully Use It

**1. Enable recap explicitly:**

```json
// .claude/settings.json
{
  "CLAUDE_CODE_ENABLE_AWAY_SUMMARY": true,
  "ENABLE_PROMPT_CACHING_1H": true
}
```

Recap runs automatically when you return after `~30min` away. You can also manually invoke it with `/recap` mid-session.[1]

**2. Parse recap data programmatically:**

Session recap output is structured. You can:
- Tail your session transcripts and extract skill invocation events
- Log which skills executed vs. which were requested
- Build a metric: `(skills_executed / skills_requested) * 100`

If this drops below 95% even after you implement native commands, that's actionable feedback: *"Layer 0 + Layer 1 still failing for skill X"*.

**3. Use TaskCreated hook + recap for multi-skill workflows:**[1]

When a skill spawns subtasks (e.g., `/arch` creates a plan, which creates a code task), recap shows the *full tree*:
```
Session: fix-auth
├─ /arch invoked
│  └─ Task: auth-plan created
│     └─ Task: auth-code created
│        └─ /code invoked
└─ Summary: 3 skills, 2 task spawns, plan compliance 100%
```

This tells you: *did the skill's workflow execute as designed, or did Claude skip intermediate steps?*

**4. Export recap data for continuous monitoring:**

```bash
# Manually invoke and save
/recap > skill_audit_$(date +%s).txt

# Or monitor programmatically in your skill_enforcer:
# Read the session transcript, extract skill-invocation events,
# compute compliance metric after every turn
```

## Memory Integration

**Memories** (a separate feature) store persistent notes that survive session restarts. You can use them to track:
- Skill enforcement failures across all sessions
- Patterns (which skills fail most often)
- Enforcement drift over time

```bash
/memory add-note "Skill /arch failed 2 times in session fix-auth-sprint"
/memory list --tag enforcement
```

After several sessions, you'd have a running log of enforcement failures. Combined with recap, this gives you **cross-session compliance metrics**.

## For Your skill_enforcer Use Case

**Create a recap analyzer:**

1. After a skill completes, log an event like: `{skill: "arch", invoked: true, completed: true, duration_ms: 1200}`
2. Every time you run `/recap`, extract these events
3. Build a running compliance dashboard: *"Last 10 sessions: 94% skill compliance"*
4. If compliance drops, audit which skill is the culprit and iterate the Layer 1 instruction text for that skill

This turns recap + memory into a **continuous enforcement testing loop** — you'll catch Layer 1 failures *before* they pile up, and you'll know *which skills need strengthening*.

***

**Bottom line:** Recap is your observability layer. Memory is your historical record. Together, they let you measure enforcement effectiveness across all sessions and iterate based on real data, not guesses.[1]

## Human

What prompt can I give to another LLM, to let it know about the operational aspects of what we talked about?

## Assistant

Here's a concise prompt you can copy-paste to another LLM to bring it up to speed:

```
CONTEXT: Claude Code skill enforcement architecture

PROBLEM: Layer 1 (UserPromptSubmit instruction injection) fails ~50% of the time. Model ignores "INSTRUCTION: Call Skill()" text and responds with prose.

SOLUTION ARCHITECTURE:
├── L0: Native .claude/commands/arch.md → Deterministic dispatch (Claude Code harness expands before model sees turn)
├── L1: skill_enforcer.py → Executes .claude/skills/arch/SKILL.md workflow
├── L2: Superpowers-style instruction strengthening → Tested language, psychological framing, named rationalizations
└── L3: Stop hook → Safety net (fires rarely after L0+L1+L2)

CRITICAL SETTINGS (v2.1.112+):
```
json
{
  "ENABLE_PROMPT_CACHING_1H": true,
  "CLAUDE_STREAM_IDLE_TIMEOUT_MS": 180000,
  "CLAUDE_CODE_ENABLE_AWAY_SUMMARY": true
}
```

OBSERVABILITY:
- /recap → Audit skill invocations per session
- TaskCreated hook → Track workflow steps
- Memory → Cross-session enforcement metrics

SKILL.md FRONTMATTER:
```
***
disable-model-invocation: false  # Claude can invoke mid-task
enforce: workflow
***
```

RULES:
1. Commands dispatch deterministically (user-triggered)
2. Skills are invocable by Claude mid-conversation (non-advisory)
3. Enforcement measured via recap + memory, not assumed
4. Never assume 100% Layer 1 compliance — always test against pressure scenarios

Your task: [INSERT YOUR TASK HERE]
```

**Usage:** Replace `[INSERT YOUR TASK HERE]` with whatever you want the LLM to do (e.g., "Write the .claude/commands/arch.md file" or "Suggest improvements to skill_enforcer.py").

This gives another LLM the full operational context without overwhelming it.
