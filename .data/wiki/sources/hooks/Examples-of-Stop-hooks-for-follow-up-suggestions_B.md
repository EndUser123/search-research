<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Examples of Stop hooks for follow-up suggestions

Best skills for next step suggestions in coding tasks
How to boost skill activation rates beyond 84% with hooks
Alternatives to Claude Code for AI step suggesters
What are best practices for Claude Code system prompts
Examples of effective custom system prompts from Piebald-AI

Build custom next step suggester skill for Claude Code

Skill Activation Hook configuration examples

Differences between LLM-eval and forced-eval hooks

Avoiding false positives in skill activation

Testing framework for skill activation rates

How to use output styles vs append-system-prompt

System prompt examples boosting SWE-Bench scores

Common pitfalls with custom system prompts

How to structure prompts for multi-context tasks

Optimization Tips
Prune ruthlessly: Delete inferred rules; test with /clear.

XML tags: <rules>Critical</rules><examples>Inline</examples> for parsing.
​

Chain-of-thought: "Think step-by-step, then act."

Review: Update from sessions/PRs; split subdirs if >300 lines.

Tools: johnpsasser/claude-code-prompt-optimizer hook for auto-refine.
​

This prevents context rot in long sessions, aligning with your 120+ hour marathons.
​

Examples of Plan and Explore sub-agent prompts

Best utility prompts for CLAUDE.md and compaction

How to create custom agents with the 1110-token architect prompt

Integration of Bash and Write tool prompts in workflows

Please filter out prompts that don't have to do with skill execution enforcement.

You’re basically asking for: “everything about enforcing skill execution and high-precision next-step suggestions, minus general prompt fluff.” I’ll keep only the parts that touch skill activation, eval hooks, next-step suggester behavior, and their system prompts.

***

## 1. Stop hooks focused on follow‑up/next‑step suggestions

Relevant pattern: use a Stop hook that runs after a coding action and enforces a “plan / next step suggestion” phase before control returns to you. This keeps Claude from silently stopping after a single edit and makes it surface explicit next actions.[^1_1][^1_2][^1_3]

Concrete example (Stop hook, prompt type, pseudo‑config):

```jsonc
// .claude/hooks.json
{
  "hooks": {
    "Stop": [
      {
        "type": "prompt",
        "name": "next-step-suggester",
        "model": "claude-3-5-sonnet",
        "prompt": "You are a next-step suggester for an IDE session.\n\nGOAL:\n- After each coding change, propose 1–3 concrete next actions.\n\nRULES:\n- Only suggest steps that materially advance the current task.\n- Prefer actions that can be performed via existing Skills.\n- If no meaningful next step exists, reply exactly with: NONE.\n\nOUTPUT:\nReturn JSON:\n{\"next_steps\":[\"...\"],\"should_activate_skills\":[\"skill-name-or-empty\"]}"
      }
    ]
  }
}
```

You then wire a second hook (command or agent) that looks at `should_activate_skills` and actually calls the skill. This is a *skill execution enforcement* pattern: coding completes → Stop hook forces evaluation of “what now?” → skill activator decides whether to fire.[^1_2][^1_3]

Key enforcement tricks:

- Make “NONE” an explicit, valid outcome so the eval doesn’t “have to” recommend a skill.
- Force JSON output so your shell/agent hook can deterministically decide whether to call a skill.
- Keep the Stop prompt short and narrow: it should do classification/selection, not re‑reason about the whole task.[^1_3][^1_2]

***

## 2. LLM‑eval vs forced‑eval hooks (and how to get >84% activation)

The distinction that matters for enforcement:

- **LLM‑eval hook**
    - Uses a separate model (often Haiku) to classify “which skills should fire?” based on the current prompt/context.[^1_4][^1_5]
    - Good for high *activation rates* and offloading work from the main model.
    - Tends to hallucinate positive matches on ambiguous or out‑of‑domain prompts (false positives).[^1_5][^1_4]
- **Forced‑eval hook**
    - Makes the *main* Claude instance explicitly step through each candidate skill with a YES/NO decision before proceeding.[^1_6][^1_4][^1_5]
    - You literally prompt: “Evaluate each skill: output YES/NO and a one‑sentence reason; only say YES if the skill is clearly appropriate.”[^1_6][^1_5]
    - Reaches 100% activation on matching cases in test suites, and in edge‑case tests avoided false positives where LLM‑eval recommended skills incorrectly.[^1_4][^1_5]

Reported numbers that are directly about enforcement:

- Baseline (no hook): ~50–55% activation with modern Claude Code; previously closer to 0% in earlier measurements.[^1_6][^1_4]
- Structured hooks (forced‑eval and LLM‑eval) can reach 100% activation and correct skill selection across synthetic test suites.[^1_5][^1_4]
- In harder “should be no skill” tests, forced‑eval had 0 false positives (more conservative), LLM‑eval hallucinated recommendations ~80% of the time in some runs.[^1_4][^1_5]

To push beyond an “84% ceiling”:

- Use **per‑skill forced‑eval**:
    - Enumerate skills with clear natural‑language criteria.
    - Ask Claude to evaluate *each* skill independently before answering the user.
- Keep the eval prompt separate from normal instructions; use an Agent/Prompt hook so you control the decision contract and parse a strict schema.[^1_3]

Example forced‑eval eval prompt (for a prompt hook):

```jsonc
{
  "type": "prompt",
  "name": "skill-forced-eval",
  "model": "claude-3-5-sonnet",
  "prompt": "You are an arbiter that decides which IDE Skills to activate.\n\nINPUT:\n- user_prompt: {{user_prompt}}\n- open_files_summary: {{open_files_summary}}\n\nCANDIDATE_SKILLS:\n1. reactive-state-helper: Use when the user describes state, reactivity, or re-renders.\n2. test-fix: Use when tests are failing and user wants them fixed.\n\nTASK:\nFor each skill, decide YES or NO. Only answer YES if activation clearly benefits the user.\n\nOUTPUT JSON ONLY:\n{\"decisions\":[{\"skill\":\"reactive-state-helper\",\"decision\":\"YES|NO\",\"reason\":\"...\"}, ...]}"
}
```

Then your command hook reads `decisions`, checks YES skills, and calls them.[^1_2][^1_5][^1_3]

***

## 3. Avoiding false positives in skill activation

Things that specifically reduce false positives while still enforcing activation:[^1_7][^1_5][^1_2][^1_4]

- Use **keyword + semantics** instead of pure semantics.
    - Observed: activation layer seems heavily keyword‑driven (“\$state” vs “my component re‑renders too much”).[^1_4]
    - You can explicitly require either: keyword match OR explicit concept description to say YES.
- Encode **strong negative criteria** per skill.
    - “Say NO if the user mentions React, Vue, or Angular for this Svelte skill, even if some words match.”[^1_5]
    - Add a “no-skill” outcome and treat it as success in tests.
- Prefer **forced‑eval** for the final arbiter.
    - LLM‑eval pre‑classifier can be aggressive; run a forced‑eval pass that can veto skills suggested earlier.[^1_5][^1_4]
- Scope skills by context signals.
    - File paths (`src/**/*.ts`), framework markers, test failures, etc., before even asking Claude.[^1_2]
    - E.g., only run eval if open files live under `app/src/svelte/**` or diagnostics mention Svelte.
- Keep the eval contract narrow.
    - Extract only: “YES/NO + reason” per skill. No partial tool planning, no freeform brainstorming in the eval prompt.

***

## 4. Skill activation hook configuration examples (Claude Code 2.1+)

Claude Code 2.1 moves most of this from “external shell hook that reads skill‑rules.json” into per‑skill frontmatter and lifecycle hooks.[^1_3][^1_2]

Core patterns relevant to enforcement:

- **Prompt/Agent hooks keyed to UserPromptSubmit**
    - Run a custom evaluator on every user prompt to decide whether to call a skill.[^1_2][^1_3]

Example config sketch:

```jsonc
// .claude/hooks.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "agent",
        "name": "skill-activation-agent",
        "prompt": "Decide which Skills to invoke for this prompt.",
        "tools": ["Read", "Glob"],
        "command": ".claude/hooks/skill-activation-agent.sh"
      }
    ]
  }
}
```

The agent prompt then uses Read/Glob to inspect the workspace, matches rules, runs the forced‑eval/LLM‑eval decision, and prints a machine‑readable decision.[^1_3][^1_2]

Per‑skill frontmatter hooks (Stop / PreToolUse / PostToolUse) can additionally enforce that once a skill is called, it fully completes its workflow, or hands back a partial result with a recommended follow‑up skill. That’s another enforcement layer: “if you started this skill, finish its internal checklist before exiting.”[^1_7][^1_2]

***

## 5. Testing framework for activation rates

One of the linked resources explicitly builds a testing framework for activation, which is exactly what you’re describing.[^1_8][^1_6][^1_4][^1_5]

Pieces that matter for enforcement, not just measurement:

- Maintain a **prompt suite** with labeled expectations:
    - “Should activate skill A” / “Should activate skill B” / “Should activate no skill.”[^1_6][^1_5]
- Run each hook configuration across the suite:
    - No hook, simple instruction, LLM‑eval, forced‑eval.[^1_6][^1_4][^1_5]
- Track separately:
    - Activation rate (did any skill fire when it should?).
    - Correctness (did the right skill fire?).
    - False positives (did a skill fire when none should?).[^1_4][^1_5]

Framework implementation ideas (high level, consistent with those posts):

- Use the Claude Code Agent SDK or CLI to script:
    - Feed test prompts, capture whether a skill was invoked, and which one.[^1_6][^1_4]
- Store results as JSON per run; aggregate into CSV/Markdown to compare hooks.
- Use these runs as regression tests whenever you tweak system prompts or hook logic.

Enforcement‑relevant insight: you can (and probably should) treat “no skill invoked when none should” as a first‑class metric, not a miss. That pushes your tuning toward high precision, not just high recall.[^1_5][^1_4]

***

## 6. Claude Code system prompts \& Piebald‑AI examples (filtered for enforcement)

The Piebald‑AI repo you mentioned includes system prompts specifically for hooks and prompt‑suggestion agents. A couple that matter for enforcement:[^1_9][^1_10]

- **System Prompt: Hooks Configuration**
    - A system prompt used for a config skill that helps manage hooks. It encodes patterns for when to apply hooks and how to structure them.[^1_9]
- **Agent Prompt: Prompt Hook execution**
    - System prompt given to Claude when evaluating whether to pass or fail a prompt hook—essentially a proto‑forced‑eval/verifier for hooks themselves.[^1_9]
- **Agent Prompt: Prompt Suggestion Generator v2**
    - Can be adapted into a “next‑step suggester” sub‑agent by narrowing its remit from generic prompt suggestions to “what next coding step / which skill.”[^1_9]

When you build your own:

- Encode **strict roles**: “You do not write code; you only decide which skill(s) to invoke and why.”
- Use **lightweight XML/JSON wrappers** just for parseability:

```
- `<rules>Critical</rules><examples>Inline</examples>` style wrappers make it easier to split rules/examples in tools, while still letting Claude parse them. (This aligns with the XML hint you pasted and what you’d use in hooks or SKILL.md.)
```


Output‑style vs append‑system‑prompt is relevant here only insofar as you want enforcement behavior to live in a **single, high‑priority system prompt** rather than in scattered output styles. System‑level skill‑arbiter prompts will be more stable for enforcement than per‑message styles.[^1_10][^1_3]

***

## 7. Alternatives to Claude Code’s built‑in step suggesters (enforcement‑friendly)

For “AI step suggesters” that you can bend toward enforced skill execution:

- **External prompt optimizer hook (johnpsasser/claude-code-prompt-optimizer)**
    - It’s an AI‑powered prompt optimization hook that triggers on `<optimize>` and restructures prompts.[^1_11][^1_12]
    - You can adapt this pattern into a “next step suggester / skill activator” hook that:
        - Detects a tag (`<next>`),
        - Calls a sub‑agent with a strict eval contract,
        - Overwrites or augments the user prompt with explicit “Call Skill(X)” directives.
- **Custom Agent hooks (type: "agent")**
    - These are essentially your own sub‑agents that can use tools and enforce workflows before yielding a simple decision back to Claude.[^1_3]
    - For enforcement, you can:
        - Let the agent inspect the workspace,
        - Decide “call skill / do nothing / suggest next steps only,”
        - Emit a narrow result that your shell script interprets.

Outside Claude Code itself, you can also run a wrapper process (CLI → your orchestrator → Claude Code) that enforces:

- Every user prompt is first rewritten by a “next step + skill selection” agent,
- Only then sent to Claude Code with explicit skill instructions.

That starts to look like a mini‑orchestrator but uses the same forced‑eval/LLM‑eval templates you’re testing inside Claude.

***

If you’d like, next step I can:

- Draft a concrete “next step suggester + skill arbiter” Agent hook (prompt text plus shell harness) tuned for your 120‑hour session style, or
- Help design a minimal JSON schema and test harness you can bolt onto your existing skill suite to track activation/false‑positive rates over time.
<span style="display:none">[^1_13][^1_14][^1_15]</span>

<div align="center">⁂</div>

[^1_1]: https://www.chatprd.ai/how-i-ai/workflows/automate-code-quality-and-fixes-with-ai-stop-hooks

[^1_2]: https://paddo.dev/blog/claude-skills-hooks-solution/

[^1_3]: https://code.claude.com/docs/en/hooks

[^1_4]: https://www.linkedin.com/posts/spences10_measuring-claude-code-skill-activation-with-activity-7426362619307032576-N5uG

[^1_5]: https://www.reddit.com/r/ClaudeCode/comments/1qzjy2h/claude_code_skills_went_from_84_to_100_activation/

[^1_6]: https://www.reddit.com/r/ClaudeCode/comments/1oywsa1/claude_code_skills_activate_20_of_the_time_heres/

[^1_7]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

[^1_8]: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably

[^1_9]: https://github.com/Piebald-AI/claude-code-system-prompts

[^1_10]: https://github.com/Piebald-AI/claude-code-system-prompts/blob/main/README.md

[^1_11]: https://github.com/johnpsasser/claude-code-prompt-optimizer

[^1_12]: https://github.com/johnpsasser/claude-code-prompt-optimizer/blob/main/package.json

[^1_13]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf?hsLang=en

[^1_14]: https://www.linkedin.com/posts/bennyjson_todays-ai-tip-use-stop-hooks-if-activity-7425116045323046913-b0Yy

[^1_15]: https://rosmur.github.io/claudecode-best-practices/

