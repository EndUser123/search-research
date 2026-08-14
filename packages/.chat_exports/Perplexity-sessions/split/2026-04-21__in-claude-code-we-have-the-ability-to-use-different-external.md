---
title: "In Claude code, we have the ability to use different external LLMs.  via their agentic CLI or through an agent harness c"
date: "2026-04-21"
mode: "CONCISE"
uuid: "8e71615f-439f-448b-8e07-768576de2e6d"
entry_count: 11
---

## Human

In Claude code, we have the ability to use different external LLMs.  via their agentic CLI or through an agent harness called Pi.  I'm thinking I want to use those external LLMs all the time because they're almost free.  I imagine I would need to use quad code hooks to enable that.  Are there repos that already show that pattern?

## Assistant

No public GitHub repos exactly match "quad code hooks" for forcing Claude Code to always route through external LLMs (e.g., via Pi harness or agentic CLI like ai-pcli) as a drop-in pattern. "Quad code hooks" yields zero direct hits—likely a custom/internal term from your hook experiments (e.g., evidence hierarchy, tool failure loops).[1][2][3]

## Closest Patterns
Pi harness enables cheap external LLMs (OpenRouter/Ollama/Gemini) by overriding ANTHROPIC_BASE_URL/API_KEY in env vars or config—bypasses native Claude for "almost free" routing without hooks. Team-harness (PyPI) spawns external CLI workers (Codex, Gemini) from a coordinator LLM via simple async Python API; config supports Claude-as-agent with OpenRouter proxy for multi-LLM always-on orchestration.[4][5]

Anyclaude repo wraps Claude Code CLI to swap backends (OpenAI, xAI, Google) using AI SDK—no hooks needed, just env vars like api_base. Users report Pi as full Claude Code replacement for external providers, with skills compatible across harnesses (e.g., pi-skills repo).[6][7][8]

## Implementation Path
**Minimal Hook Route (Your Style):** Register a `userpromptsubmit` or `pre-plan` hook (like your existing patterns) that sets env vars (`ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"`, `ANTHROPIC_API_KEY="${OPENROUTER_KEY}"`) and invokes Pi CLI (`pi --model gemini-2.0-flash-exp --prompt "${CLAUDE_PROMPT}"`). Exit 0 to proceed, or pipe output back via JSON stdin for chaining. Test via `event-logger.py` from claude-code-hooks repo to capture event data (session, prompt).[9][10][1]

**Pi Direct (Recommended, Zero Hooks):** Install Pi (npm/yarn), config `~/.pi/config.toml` with providers, run `pi your-task`—inherits your ai-* skills/think combos for external always-on. Cost: ~$0 via Ollama/local; OpenRouter <1¢/k tokens.[11][12]

**Agentic CLI Fallback:** Extend your ai-pcli/ai-cli-gemini skills in `userpromptsubmit` hook: always delegate to `pcli --model qwen-max --think-chain` before local generate.[13]

## Uncertainty & Next Steps
No canonical "always-external" repo due to Anthropic's recent third-party harness restrictions (pulled plug Apr 2026). Confidence: High on patterns (your memories + searches); low on "quad" specifics (assume 4-hook sequence: pre/post plan/tool?). Fork team-harness or anyclaude, add Pi spawn.[14]

**Concrete Step:** `git clone https://github.com/coder/anyclaude && cd anyclaude && OPENROUTER_API_KEY=sk-or-... ANTHROPIC_BASE_URL=https://openrouter.ai/api/v1 claude your-task`—test if it forces external today.[7]

What defines "quad code hooks" in your setup (e.g., specific 4 events/files)?

## Human

it's not quad code, it's claude code.

## Assistant

No repos implement a full "always-external LLM" pattern via Claude Code hooks alone—hooks excel at tool enforcement/validation but can't globally override the core API endpoint without env vars or proxies. Proxy repos (e.g., Claude-Code-openrouter-proxy) route all Claude Code traffic through OpenRouter for cheap models (~0¢/k via free tiers) via simple env: `ANTHROPIC_BASE_URL="https://proxycodeclaude.mellot-jules.workers.dev" ANTHROPIC_API_KEY="sk-or-v1-..."`—no hooks needed.[1][2][3][4]

## Proxy Repos (Direct Always-External)
| Repo | Pattern | Setup | Models | Limitations |
|------|---------|--------|---------|-------------|
| [JulesMellot/Claude-Code-openrouter-proxy](https://github.com/JulesMellot/Claude-Code-openrouter-proxy) [1] | Public proxy server maps Anthropic endpoints to OpenRouter; drop-in env vars. | `export ANTHROPIC_BASE_URL="https://proxycodeclaude.mellot-jules.workers.dev" ANTHROPIC_API_KEY="sk-or-..."`; run `claude --model "anthropic/claude-3.5-sonnet"` (proxies to cheap equiv). | Claude compat (Haiku/Sonnet/Opus) → OpenRouter (Gemini/Qwen/Z.AI). | Public server; rate limits on free tier. |
| [ruvnet/ruflo (wiki)](https://github.com/ruvnet/ruflo/wiki/Using-Claude-Code-with-Open-Models) [3] | Env-only OpenRouter proxy for open models. | `ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1" ANTHROPIC_AUTH_TOKEN="or_..." ANTHROPIC_MODEL="openai/gpt-oss-20b"`. | Any OpenRouter (local Ollama via proxy). | No hook integration. |
| LiteLLM proxy (issue-based) [5] | Local proxy for Copilot → Claude Code. | Run LiteLLM server, set `ANTHROPIC_BASE_URL="http://localhost:4000"`. | GitHub Copilot, any LiteLLM-supported. | Recent breakage (Mar 2026). |

## Hook-Only Patterns (Partial Routing)
Hooks trigger on events (PreToolUse, userpromptsubmit) to invoke Pi CLI or external via Bash/agent type—no global override.[6][7][2]
- **disler/claude-code-hooks-mastery**: Sub-agents for delegation (e.g., spawn Pi subagent for cheap compute); register in `.claude/settings.json`.[8]
- **hesreallyhim/awesome-claude-code (#1585)**: Governance hooks intercept tools, query external LLM (Pi) for decisions.[9]
- **Enforce CLI (AIHero/YouTube)**: PreToolUse Bash hook blocks native tools, forces `pi --model gemini ...` instead.[10][6]

Example hook for Pi delegation (from patterns):
```bash
#!/bin/bash  # .claude/hooks/force-pi-external.sh
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
if [[ "$COMMAND" == bash* ]]; then
  pi --model "qwen-max" --prompt "$(jq -r '.context' <<< "$INPUT")" > /tmp/pi-out.json
  jq '{hookSpecificOutput: {permissionDecision: "ok", output: input("/tmp/pi-out.json")}}' /tmp/input.json
  exit 0
fi
```
Register: `.claude/settings.json` → `"hooks": [{"event": "PreToolUse", "matcher": {"tool": "Bash"}, "type": "bash", "source": "force-pi-external.sh"}]`.[7][2]

## Pi as Native Replacement
Pi harness (disler/pi-vs-claude-code) directly supports your ai-* skills, agentic CLI, multi-provider (Anthropic→Ollama swap). `pi --model ollama/llama3.2 --harness claude-code` mimics hooks without Anthropic limits.[11]

**Next Step:** `git clone https://github.com/JulesMellot/Claude-Code-openrouter-proxy && export ANTHROPIC_BASE_URL="https://proxycodeclaude.mellot-jules.workers.dev" ANTHROPIC_API_KEY="sk-or-$(openrouter-key)" && claude "test external routing"`—verifies always-external in <1min.[1]

Do you want code to adapt a PreToolUse hook for Pi invocation?

## Human

you've jumped to conclusions and don't actually understand properly. The Claude Code agent harness, when given a task, will action it. The code hooks allow other events to be reacted to.  I'm thinking that when I ask Claude code a question or a task, it doesn't. But also in parallel, an external LLM will also do the same task. When both tasks, when both agents have finished the task, a subagent can check to see which is more optimally done. Or the initial Claude code request can do its task via a subagent. So basically we have a Claude subagent and then an external agent. And then Claude as the orchestrator and Judge compares the two.

## Assistant

Yes — now the pattern is much clearer: you are not trying to *replace* Claude Code with an external model; you want Claude Code to remain the orchestrator while spawning a parallel external worker, then using a judge/validator step to compare outputs and continue with the better result. That is a real Claude Code pattern in spirit, but it is closer to **orchestrated multi-agent evaluation** than to a simple hook trick, and the best existing repos are partial examples rather than exact drop-in implementations.[1]

## What hooks can do

Claude Code hooks are deterministic lifecycle triggers that can run on events like `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, and `Stop`, while subagents are the mechanism for isolated delegated work. Hooks can also be `type: "agent"` or `type: "prompt"`, which matters here because your “judge” is not just a shell script; it can be a model-driven verifier that inspects outputs and returns a structured decision.

That means your architecture is plausible as:

- Primary Claude Code session receives the task.
- A hook or command causes two workers to be launched: one Claude subagent and one external agent via Pi or another CLI.
- When both complete, a judge step compares them for correctness, completeness, cost, or implementation quality.[1]
- The main Claude agent either presents the better result or uses the judge feedback to continue iterating.

## Closest repo patterns

There are repos that show important parts of this pattern, but I did not find one that cleanly packages **Claude orchestrator + Claude subagent + external parallel agent + judge** as a finished reusable harness.[2][3]

| Repo / source | What it shows | Why it matters to your pattern |
|---|---|---|
| `disler/claude-code-hooks-mastery` [4] | Full hook lifecycle, subagents, meta-agent, parallel hook execution, agent-style control. | Strongest repo for Claude Code orchestration primitives, but not specifically external-agent side-by-side judging. |
| `lst97/claude-code-sub-agents` [2] | Specialized Claude Code subagents. | Useful for the Claude-side worker and judge roles. |
| `wshobson/agents` [3] | Multi-agent orchestration around Claude workflows. | Closest general orchestration direction, though not clearly Pi-parallel by default. |
| Claude hooks docs  | Official support for `agent` hooks, `SubagentStart/Stop`, `TaskCreated/Completed`, and prompt/agent-based verification. | This is the official basis for your architecture. |
| Builder-validator writeup [1] | Builder agent and validator agent separation. | Conceptually the nearest public articulation of your “worker A vs worker B, then judge” design. |

## What is missing

The gap is not whether Claude Code can support the pattern; the gap is that public repos mostly demonstrate **one of** these layers, not all four together.

What I found missing in public examples:

- Parallel launch of a Claude subagent and an external CLI agent for the same task.[4][2]
- A shared result envelope, such as `output_a.json` and `output_b.json`, with normalized fields for diffing.
- An automatic judge that scores both and returns a machine-readable winner.[1]
- Re-entry into the main Claude session with the winning output as context for the next turn.

So the right framing is: **repos exist for the ingredients; I did not find a repo that already assembles your exact competition/judge harness.**[3][2][4]

## Best-fit design

The cleanest implementation is probably not “hooks do everything.” Hooks should coordinate lifecycle and trigger glue code; subagents and external CLIs should do the actual work.

A practical design would be:

- `UserPromptSubmit` hook captures the original task and writes a task packet to disk or a queue.
- Main Claude session delegates to a Claude subagent for internal execution.
- In parallel, the hook launches Pi or another external CLI with the same normalized task packet.
- `SubagentStop` and an external-process watcher mark completion state.
- A `Stop` agent hook or explicit judge subagent compares both outputs and returns `{ ok, reason }` or a richer scorecard.
- If neither is adequate, the orchestrator continues with targeted critique.[1]

That uses the platform in the way it was designed: hooks for deterministic event reaction, subagents for isolated Claude work, and agent hooks for model-based verification.

## My read on repo usefulness

If your goal is “find a repo to fork,” `disler/claude-code-hooks-mastery` is probably the best base because it already demonstrates the hook surface area, subagent concepts, and the idea that Claude Code behavior can be programmatically shaped around lifecycle events. If your goal is “find the exact head-to-head judge harness,” I do not think the public ecosystem has converged on a canonical repo for that yet.[2][3][4]

## One caution

Your idea is good, but it is easy to make it much more expensive and slower than expected if both branches re-read large context or run redundant exploration. The public lessons around subagents consistently suggest that parallelism helps only when responsibilities are sharply separated and outputs are normalized enough for a validator to compare them cheaply.[5][1]

## Concrete next step

I’d treat this as a **small harness project** rather than a repo search problem now:

1. Fork `disler/claude-code-hooks-mastery` as the Claude-side control plane.
2. Add one external runner script that invokes Pi with the same task payload.
3. Define a shared JSON schema for both workers’ outputs.
4. Add a judge subagent or `Stop` agent hook that scores both outputs against the task.[1]

If you want, I can sketch the exact minimal architecture next — event by event — for a **Claude orchestrator + Claude subagent + Pi external agent + judge** harness in Claude Code.

## Human

The practical design is what I was thinking.  One of the examples I haven't seen you talk about is when we use separate work trees.  Are there any repos that show this pattern?

## Assistant

Yes — this pattern definitely exists in the wild, and worktrees are actually one of the clearest public examples of the architecture you described: multiple agents run the same task in isolated branches, then a human or another agent compares the results.[1][2]

## Strongest match

The closest public match I found is **spillwavesolutions/parallel-worktrees**. Its stated purpose is to “run multiple Claude Code agents simultaneously across git worktrees,” which is directly aligned with your “same task, separate workers, compare later” idea.[1]

Another very relevant example is the Agent Interviews writeup on **Parallel AI Coding with Git Worktrees and Custom Claude Code Commands**. That article explicitly describes running multiple Claude agents on isolated worktrees for the **same feature**, then choosing the best implementation, which is almost the exact evaluation pattern you outlined.

## What that repo/article actually shows

The Agent Interviews pattern uses:

- Git worktrees for isolated copies of the repo.
- Custom Claude Code commands in `.claude/commands/` to initialize and run parallel workers.
- Multiple branches like `feature-1`, `feature-2`, `feature-3`, each with an independent agent working from the same spec.
- Comparative review after completion to pick the strongest implementation.

That is important because it proves the ecosystem already treats **LLM non-determinism as a feature**: run the same spec multiple times, harvest different solutions, then judge them.

## How it maps to your design

Your design is slightly more advanced than the basic worktree pattern, because yours is not just “Claude vs Claude vs Claude.” It is more like this:

- Main Claude Code session = orchestrator.
- Worktree A = Claude subagent implementation.
- Worktree B = external agent implementation via Pi / agentic CLI.
- Judge = Claude subagent or agent hook that compares outputs.

So the worktree repos show the **workspace isolation pattern**, even if they do not always show the **heterogeneous agent mix** of Claude plus external LLM.[1]

## Other useful references

There are also several non-repo references that confirm this pattern is established practice around Claude Code:

- Claude Code native worktree support is described as enabling multiple sessions on different parts of a project with isolated filesystem state under `.claude/worktrees/`.[2]
- Tutorials and field reports describe running 3–4 Claude Code agents in parallel with separate worktrees to avoid file collisions and branch chaos.[3][4][5][6]
- Upsun’s writeup explicitly says Anthropic recommends worktrees for multi-session workflows because each agent gets context isolation while sharing Git history.[7]

## What I did not find

I did **not** find a repo that clearly shows the full version of your exact pattern:

- same task,
- separate worktrees,
- one worker is Claude,
- one worker is external via Pi or another CLI,
- then a judge agent automatically scores both and selects the winner.[1]

So the honest answer is:

- **Yes**, repos and examples exist for the worktree-based parallel-agent pattern.[1]
- **No**, I did not find a canonical repo that already combines that with your exact Claude-orchestrator plus external-agent plus judge flow.[1]

## Best candidates to inspect

If you want to study real patterns rather than theory, I would inspect these first:

| Source | Why inspect it |
|---|---|
| `spillwavesolutions/parallel-worktrees` [1] | Most likely repo-level starting point for multi-agent worktree orchestration. |
| Agent Interviews worktree article  | Best explicit description of “same task, multiple agents, compare outputs.” |
| `disler/claude-code-hooks-mastery` [8] | Best Claude Code hook/subagent control-plane reference to add the judge/orchestrator layer. |
| Claude Code hooks docs  | Needed to wire lifecycle events, subagent completion, and agent-hook judging properly. |

## Practical judgment

If I were implementing your design, I would not search for a perfect repo much longer. I would combine:[1]

- a **worktree launcher pattern** from the parallel-worktrees examples,[1]
- your **external agent runner** via Pi or agentic CLI,
- and a **Claude judge** using either a subagent or an agent hook after both worktrees complete.

That is probably the shortest path, because the worktree part already appears to be a solved pattern, while the heterogeneous judge harness still looks like an integration job rather than an off-the-shelf repo.[1]

If you want, I can next map out the exact minimal architecture for this as:
**orchestrator session + worktree A Claude + worktree B external + judge + merge policy**.

## Human

Common pitfalls when using git worktrees with Claude Code

## Assistant

Here are the main **failure modes** people hit when combining git worktrees and Claude Code, with concrete mitigation for each.[1][2][3][4]

***

## 1. Dependencies & environment don’t exist in the worktree

Worktrees share `.git`, but **do not copy** your runtime environment:

- `node_modules`, `.venv`, `.m2`, etc. are missing.[3][1]
- `.env` and other secret/config files aren’t there by default.[4][1]

**Symptoms**

- “Module not found” / “Cannot find package X” in the worktree.[1]
- Tests or dev servers fail only in the worktree.
- Claude keeps trying to “fix” missing imports that are actually just uninstalled deps.

**Mitigation**

- Treat each worktree like a fresh clone for runtime setup:
  - Re-run `npm install` / `pnpm install` / `pip install -r requirements.txt` in the worktree.[3][1]
  - Use `.env.example` and a dedicated `.env.ai` (no real credentials) that you copy into each AI worktree.[4]
- For monorepos, consider **per-worktree** `node_modules` using `pnpm` or `yarn` workspaces instead of symlinking – symlinks can confuse Claude’s reasoning about paths.

***

## 2. Branch misuse across worktrees

Worktrees can’t checkout the same branch in multiple places, and using the wrong branch pattern breaks isolation.

**Symptoms**

- `fatal: 'branch-name' is already checked out` when adding a new worktree.[3][4]
- Two Claude sessions effectively working on the *same* branch from different dirs; their edits race.
- Context bleed: “Why did Claude change this file? I thought that was for the other task.”

**Mitigation**

- Never reuse the same branch for two worktrees.[4][3]
- Decide on a naming convention:
  - `feature/foo-main` (your human branch)
  - `feature/foo-cc-a` (Claude worktree A)
  - `feature/foo-cc-b` (Claude worktree B / external agent)[3]
- Create via:
  ```bash
  git worktree add ../proj-worktrees/feature-foo-cc-a -b feature/foo-cc-a origin/main
  ```
- Document this in a short `WORKTREES.md` that Claude can read.

***

## 3. Orphaned / broken worktrees from manual deletion

Deleting worktree directories with `rm -rf` leaves git metadata pointing at nowhere.[2][4][3]

**Symptoms**

- `git worktree list` shows paths that no longer exist.[2]
- Worktree create commands complain about existing or conflicting paths.
- Other tools (including Claude) mis-detect repo/worktree state.

**Mitigation**

- Never `rm -rf` a worktree dir directly.[2][3]
- Cleanly remove:
  ```bash
  git worktree remove ../proj-worktrees/feature-foo-cc-a
  git worktree prune
  ```
- If you script cleanup for Claude sessions, always use `git worktree remove` + `prune`, not filesystem deletes.[2]

***

## 4. Forgetting to push / sync worktrees

Each worktree is a full git working copy; nothing is “automatically pushed.”[4][2]

**Symptoms**

- “Why can’t main see Claude’s work?” – because that branch was never pushed.[2]
- Merge/rebase surprises when you finally push days later.
- Multiple agents diverge from main in different worktrees and never reconcile.

**Mitigation**

- Treat each worktree as a first-class branch:
  ```bash
  cd ../proj-worktrees/feature-foo-cc-a
  git status
  git commit -am "feat: foo from Claude A"
  git push -u origin feature/foo-cc-a
  ```
- Build a simple checklist when ending a session:
  1. `git status` clean?
  2. `git commit` done?
  3. `git push` done?

***

## 5. Dependency & server port clashes between worktrees

Running multiple dev servers and test runs in parallel across worktrees creates resource collisions.[1][3]

**Symptoms**

- Error: `Port 3000/3001 is in use, trying 3002 instead` across multiple worktrees.[1]
- Hard-coded ports in config cause one worktree’s server to crash another’s.
- Claude keeps “fixing” port conflicts by editing code in ways you don’t want.

**Mitigation**

- Make port selection explicit and per-worktree:
  - env-based config: `PORT=3001` in `.env.ai-a`, `PORT=3002` in `.env.ai-b`.
- When you know you’ll run multiple servers, bake this into your prompts:
  - “Use port 3101 in this worktree; do not change other ports.”
- For long-running tasks, prefer test commands and linters (no dev server) when possible.

***

## 6. IDE & tooling confusion

Multiple worktrees under the same parent can cause IDEs to index everything and confuse language servers.[3][2]

**Symptoms**

- VS Code / JetBrains indexing all worktrees → high CPU, sluggishness.[2]
- “Go to definition” hops into a *different* worktree’s file.
- Claude suggestions reference files from the wrong worktree path.

**Mitigation**

- Tell your IDE to ignore sibling worktrees:[2]
  ```jsonc
  // .vscode/settings.json
  {
    "search.exclude": {
      "../proj-worktrees/**": true
    },
    "files.watcherExclude": {
      "../proj-worktrees/**": true
    }
  }
  ```
- Only open **one** worktree in your IDE at a time; keep the others for Claude terminals.

***

## 7. Worktree not detected as git repo / incorrect root

Some Claude Code commands or scripts can get confused about the repository root when invoked from nested dirs or non-standard layouts.[5][3]

**Symptoms**

- Claude says “This doesn’t look like a git repo” from a valid worktree.[5]
- Git commands run from hooks or scripts operate on the wrong repo.
- Tools relying on `git rev-parse --show-toplevel` yield the shared root instead of the worktree path, or vice versa.[5]

**Mitigation**

- Always run Claude from the **worktree root**, not a deeper subdirectory:
  ```bash
  cd ../proj-worktrees/feature-foo-cc-a
  claude
  ```
- If you add helper scripts, use `git rev-parse --show-toplevel` carefully and be explicit about where you expect it to point.[5]
- Keep your worktree structure simple: `../project-worktrees/{branch-name}` is a common pattern.[3][2]

***

## 8. Too many parallel agents / worktrees

In theory you can create many worktrees; in practice, your **attention and token budget** are the bottlenecks.[4][3]

**Symptoms**

- 4–5 Claude sessions all editing different worktrees; you can’t review everything.
- Token/usage spikes; cost or rate limits hit.[3]
- Hard to remember which session is doing what.

**Mitigation**

- Several guides recommend **2–3 active worktrees** max.[3]
- Give each worktree/session an explicit, descriptive purpose:
  - `bugfix/auth-timeout-cc`
  - `feature/reporting-v2-cc-external`
- Close or remove worktrees as soon as work is merged to avoid mental clutter.[2][3]

***

## 9. Security: credentials and secrets in AI worktrees

It’s easy to accidentally copy real secrets into AI-focused worktrees, especially if you script env copying.[4]

**Symptoms**

- Real API keys in `.env` under `../project-worktrees/**`.
- Claude sees and potentially logs secrets from non-production worktrees.

**Mitigation**

- Use `.env.example` / `.env.template` with fake or low-privilege keys.[4]
- If you must use real keys, use environment-level injection (shell exports, password managers) instead of copying `.env` into AI worktrees.
- Add worktree-specific `.env.ai*` to `.gitignore` so they never commit.[4]

***

## 10. Merge / rebase complexity from divergent worktrees

Multiple worktrees working on related code paths increase merge complexity.[6][2][4]

**Symptoms**

- Frequent merge conflicts when merging worktree branches back to main.[6]
- Claude trying to auto-resolve complex conflicts and making a mess.
- Confusion about whether to “rebase main into worktree” vs “rebase worktree into main.”[6]

**Mitigation**

- Keep each worktree focused on **one coherent task**.[3]
- Merge workflow:
  1. Periodically `git fetch` and rebase main **into** the worktree branch, letting Claude help with conflicts.[6][4]
  2. Once green, merge worktree branch → main via normal PR flow.
- Avoid letting two worktrees change the same core files if you can; use your orchestrator idea (Claude vs external) on **separate branches** and choose one to merge.

***

If you tell me your current worktree layout (paths + how you start Claude Code sessions), I can propose a concrete “safe pattern” tailored to your setup that bakes these mitigations into your shell aliases and Claude prompts.

## Human

I start claude code from the root.  and then I tell the LLM to use a work tree.  where they mix both and both.  both main and the work tree as the target.

## Assistant

Yes — that is the core mistake. If you start Claude Code in the **main repo root** and then merely *tell* it to “use a worktree,” you are leaving the agent anchored in the main working directory, which makes it easy for it to read from or write to both the main checkout and the worktree interchangeably.[1][2][3]

## What is going wrong

Claude Code’s recommended workflow is to start the session **inside the target worktree**, or use `claude --worktree` / `-w` so the session is created in an isolated directory from the start. If you instead launch from root and describe a worktree in natural language, the model can reason about the worktree conceptually while still issuing tool calls against the main checkout, which creates exactly the “mix both main and worktree as the target” contamination you described.[2][4][3][1]

There is even a recent bug report describing Claude reading from the main repo path instead of the worktree path under some conditions, which reinforces that relying on implicit path discipline is unsafe. In other words: **your current workflow is structurally ambiguous**, so the model is not the only thing at fault.[1][2]

## Main failure mode

The real problem is not “Claude forgets”; it is that the session’s filesystem context is wrong from the beginning.[5][2]

Typical sequence:

- You start in main root.[2]
- You ask Claude to create or use a worktree.[5]
- Claude now knows two valid paths exist: main and worktree.[1]
- Tool calls, file edits, git status, and diffs can land in either place unless every command is path-scoped correctly.[3][1]

That is why you see mixed targeting.

## Safer pattern

The fix is to make the **directory boundary explicit and early**, not conversational.[6][2][5]

Best practice:

1. Create or switch to the worktree in shell first.[6][5]
2. `cd` into that worktree.[5][6]
3. Start Claude Code there.[2][6]

Example:

```bash
git worktree add ../myproj-ai-auth -b ai/auth-refactor
cd ../myproj-ai-auth
claude
```

Or use Claude’s own isolated startup flow:

```bash
claude --worktree ai/auth-refactor
```

Claude docs explicitly describe `--worktree` as creating an isolated worktree and starting Claude in it.[2]

## Hard rules to stop contamination

If you want reliable behavior, I would treat these as non-negotiable:

- **Never start Claude in main when the task belongs to a worktree.**[4][2]
- **One Claude session = one directory = one branch.**[3]
- **Do not ask the model to “remember” which tree to use; make the shell state enforce it.**[1][2]
- **Do not expose both paths in the same session unless the job is explicitly comparative or orchestrational.**[1]

That last point matters for your planned judge architecture: the orchestrator session may know about multiple worktrees, but each worker session should live only in its own worktree.[3][2]

## Why main gets hit

There is another subtle trap: worktrees created from `main` can inherit tracking in ways that make push behavior surprising, and some workflows or GUIs may still target `main` if branch setup is sloppy. So when you mix “session launched in root” with “worktree branched from main” and “LLM told to use the worktree,” you are stacking multiple sources of ambiguity.[7][8][1]

## Best operating model for your use case

For the architecture you described earlier, I would separate roles like this:

- **Main repo session:** only orchestration, no code edits.[2]
- **Claude worker:** launched inside worktree A only.[3][2]
- **External worker:** launched inside worktree B only.[2]
- **Judge:** may read both outputs, but should consume artifacts or diffs, not freely edit both trees.[9][2]

That preserves the worktree boundary instead of asking one session to mentally juggle multiple sandboxes.

## Concrete recommendation

Your current prompt pattern — “start from root, then tell Claude to use a worktree” — is the thing to stop first. Replace it with a wrapper or alias that always creates/switches worktree and then launches Claude **from that directory**, because this removes the ambiguity before the model ever sees the task.[6][5][1][2]

If you want, I can write you a minimal shell function such as `ccwt <task-name>` that:

- creates or reuses a worktree,
- `cd`s into it,
- verifies branch/path,
- and launches Claude there with a visible safety banner.

## Human

Can we do a /CD from inside claude?  would that make a difference?  Can we use PI agent harness that is invoked from inside claude code at P:, to start in P:/worktrees?

## Assistant

Yes, but there’s an important distinction: **Claude Code can change directories only within what the session is allowed to access, and changing directories mid-session is not the same thing as changing the session’s true root/isolation model**. So `/cd`-style movement can help in some cases, but it does **not** fully fix the problem you described when the session was started in the wrong place.[1][2][3]

## `/cd` inside Claude

Official docs show a `CwdChanged` hook that fires “when Claude executes a `cd` command,” so Claude can perform directory changes during a session in at least some supported cases. But current feature requests and issue reports say Claude Code still cannot freely switch its working directory mid-session the way a shell user expects, especially outside the original allowed directory tree, and `/add-dir` expands access without changing the session root.[2][4][3][1]

So the precise answer is:

- **Can Claude do a `cd`?** Sometimes, yes, within permitted boundaries.[4][3]
- **Does that make the session equivalent to having started in the worktree?** No.[1][2]
- **Would I rely on it for worktree isolation?** No.[5][1]

## Would it make a difference?

It can make **some** difference operationally, but not enough to solve your contamination problem.[3][6]

Why:

- If you start in `P:\` and then `cd P:\worktrees\foo`, Claude may run subsequent bash commands there, and `CwdChanged` hooks can react to that.[3]
- But the session still began with `P:\` as its broader context, and issue reports indicate Claude can still get confused about path/root assumptions when worktrees and main repo coexist.[7][1]
- In your specific workflow, that means Claude may still reason across both the main checkout and the worktree, because both are visible and the initial anchor was wrong.[7][1]

So **it may reduce mistakes, but it does not create clean isolation**.[2][1]

## Best practice for worktrees

The official guidance is to use `claude --worktree` / `-w`, which creates an isolated worktree and starts Claude in it from the outset. That is materially safer than “start in root, then tell Claude to move,” because the worktree becomes the initial workspace rather than a later navigation target.[8][5]

## Pi harness from inside Claude

Yes, **you can invoke Pi from inside Claude Code**, and if Claude is currently operating in `P:\`, it can launch Pi with a working directory pointing at `P:\worktrees\...`. The clean way is not “hope Pi inherits the right cwd,” but to explicitly spawn it with the target worktree path as its working directory or by wrapping the launch in `cd /d P:\worktrees\foo && pi ...`.[9][8][3]

Conceptually:

```powershell
cd /d P:\worktrees\task-a
pi "Implement the same task here"
```

or from a launcher script/hook:

```powershell
Start-Process pwsh -ArgumentList '-NoExit','-Command','cd /d P:\worktrees\task-a; pi "Implement X"'
```

That part is sound because Pi is just another process; you can decide where it starts.[8][9]

## Important caveat

This does **not** mean Claude itself is now safely worktree-scoped just because it launched Pi into `P:\worktrees\foo`. It only means the **external agent** can be safely started in that directory if you pass the path explicitly.[9][1][2][8]

So for your architecture:

- **Claude orchestrator** can stay in `P:\` if it is intentionally supervising multiple worktrees.[5]
- **Claude worker** should be a separate Claude session started directly in its own worktree.[1][5]
- **Pi worker** can absolutely be launched from the orchestrator into `P:\worktrees\foo` as a child process with explicit cwd.[8][9]
- **Judge** should compare artifacts, diffs, or branch outputs, not casually edit across both trees from one shared session.[10][5]

## Practical recommendation

For your use case, I would **not** try to solve this with a mid-session `/cd` inside a single Claude worker session. I would use one of these two patterns instead:[2][1]

- **Worker isolation pattern:** start each worker session directly inside its own worktree; orchestrator only coordinates.[5]
- **Hybrid pattern:** keep Claude orchestrator at `P:\`, but launch Pi with explicit cwd into `P:\worktrees\...`, while Claude-side implementation work happens in a separate Claude session also started from that worktree.[8][5]

That preserves the distinction between “orchestrator knows many trees” and “worker owns one tree.”

If you want, I can sketch the exact Windows-friendly launcher pattern next:
**Claude orchestrator in `P:\` → spawn Pi in `P:\worktrees\ext-a` → spawn Claude worker in `P:\worktrees\claude-a` → judge results**.

## Human

I could also do 'Start-Process pwsh -ArgumentList '-NoExit','-Command','cd /d P:\worktrees\task-a; claude  "Implement X"''

## Assistant

**Yes, that works — and it is a good pattern for spawning isolated Claude Code workers from an orchestrator session.** Your proposed command reliably starts a new Claude session in the target worktree with an interactive PowerShell window that stays open.[1][2][3]

## Why it works

`Start-Process pwsh -NoExit -Command 'cd /d P:\worktrees\task-a; claude "Implement X"'` does exactly what you want:

- `pwsh` launches a new PowerShell process.[1]
- `-NoExit` keeps the window open after Claude starts (critical for monitoring/interaction).[4][1]
- `cd /d P:\worktrees\task-a` changes to the worktree directory before launching.[3]
- `claude "Implement X"` starts Claude Code **from inside that worktree**, so its root/workspace is correctly scoped.[5][6]

This solves your original contamination problem because the **child Claude session** inherits the correct cwd from the start, unlike telling a root-launched session to “use a worktree.”[6][5]

## Even better: use `-WorkingDirectory`

The canonical PowerShell way adds `-WorkingDirectory` to `Start-Process`, which sets the pwsh process's starting location without needing the `cd` command:

```powershell
Start-Process pwsh -ArgumentList '-NoExit', '-Command', 'claude "Implement X"' -WorkingDirectory 'P:\worktrees\task-a'
```

This is cleaner and less error-prone (no shell quoting issues).[2][7][1]

## For your architecture

This is perfect for your orchestrator pattern:

```powershell
# From orchestrator at P:\
Start-Process pwsh -ArgumentList '-NoExit', '-Command', 'claude "Claude worker: implement auth refactor"' -WorkingDirectory 'P:\worktrees\claude-auth'
Start-Process pwsh -ArgumentList '-NoExit', '-Command', 'pi "External agent: implement auth refactor"' -WorkingDirectory 'P:\worktrees\pi-auth'
```

- **Orchestrator** stays at `P:\` coordinating.[6]
- **Claude worker** launches in `P:\worktrees\claude-auth` (clean isolation).[6]
- **Pi worker** launches in `P:\worktrees\pi-auth`.[8]
- Both child sessions see only their own worktree.[1][6]

## Generated launcher template

I created a reusable PowerShell script template you can copy into your orchestrator workflow. It parameterizes the worktree path and task.



**Usage example:**
```powershell
# In your P:\ orchestrator session
. .\claude-worktree-launcher.ps1
Launch-ClaudeWorker -WorktreePath 'P:\worktrees\claude-auth' -Task 'implement auth refactor with TDD'
Launch-PiWorker -WorktreePath 'P:\worktrees\pi-auth' -Task 'implement same auth refactor'
```

## Why this beats mid-session /cd

- **No session ambiguity:** Each worker starts with the correct root from launch.[9][6]
- **No reliance on Claude’s path reasoning:** Shell enforces isolation before the model sees the task.[9]
- **Scales to multiple workers:** Orchestrator can spawn N isolated sessions reliably.[1]
- **Visible terminals:** `-NoExit` gives you interactive oversight of each worker.[1]

## Pitfalls to avoid

- **Worktree must exist first:** Create it with `git worktree add` before launching.[6]
- **Quoting on Windows:** Use single quotes around paths with spaces; double for args.[3][1]
- **claude path:** Ensure `claude` is in PATH for the child pwsh (it should be if installed globally).[5]
- **Permissions:** Child sessions inherit your perms; no elevation needed.[5]

This gives you the **heterogeneous parallel worker pattern** you wanted without any of the root contamination issues.[6][1]

Want me to extend the launcher with git worktree creation, branch naming, or judge integration?

## Human

What else should I be aware of for this idea?

## Assistant

Yes — several things, and most of them are not about Git itself but about **evaluation design, branch ownership, and preventing the orchestrator from trusting agent summaries too much**.[1][2][3][4]

## Biggest risk

The biggest failure mode in your idea is **false confidence**: two agents finish, one sounds better, the judge picks it, but neither solution is actually correct. Public discussions around subagents and harness engineering repeatedly warn that orchestrators tend to trust agent reports unless they verify concrete artifacts like diffs, test results, and branch state.[2][3][5]

So your judge should not ask, “Which answer sounds best?” It should ask:

- Which branch passes the targeted tests?[4][1]
- Which diff is smaller for equivalent correctness?[5]
- Which one violates fewer repo conventions?[2][5]
- Which one introduces less merge risk against main?[1][4]

## Use artifacts, not prose

Do **not** compare only natural-language summaries from Claude and the external agent. Compare a standardized bundle for each worker:[3]

- `git diff --stat`
- full patch or changed file list
- test results
- lint/typecheck results
- notes on assumptions / unresolved issues[4][5][1]

If you let the judge consume only “I implemented X successfully,” your system will be fragile.[3]

## Avoid naive best-of-N

Running two or more agents on the same task can help, but naive parallel sampling often produces a lot of near-duplicate mediocre outputs, so the gain is not automatic. Public commentary on parallel Claude Code usage notes that “best-of-N” works best when the workers are deliberately differentiated rather than asked to do the exact same thing in the exact same way.[6][2]

Better pattern:

- Claude worker A: minimal patch, repo-conservative.[5]
- External worker B: broader search / alternative design.[2]
- Judge: correctness first, then simplicity / mergeability.[1][5]

That gives you *useful diversity* instead of redundant variance.[6][2]

## Branch ownership must stay strict

If both workers can touch the same worktree, same branch, or same files in the same checkout, the whole design collapses. The safe pattern is:[4][1]

- one branch/worktree per worker,[1][4]
- no shared writable directory,[1]
- merge only after evaluation.[4]

If both tasks are likely to rewrite the same hotspot files, parallelism may cost more than it saves because merge/conflict overhead eats the benefit.[4]

## Judge design matters more than worker design

Most people focus on how to spawn multiple agents; the real leverage is in how the judge decides. A useful judge pipeline is usually:[3][5]

1. Validate branch cleanliness and changed files.[1]
2. Run targeted tests for the requested feature, not the entire universe.[2]
3. Run lint/typecheck if relevant.[5][1]
4. Compare diff size and touched-surface area.[5]
5. Ask Claude judge for semantic review only **after** the hard signals are collected.[3][5]

That ordering matters because it prevents eloquent-but-wrong outputs from winning too early.[3]

## Keep the gate narrow

A common harness failure is overbuilding the system: too many hooks, too many tools, too many validators, too many always-on checks. Harness engineering writeups explicitly warn that excess tools and broad enforcement can push the agent into tool thrash and reduce output quality.[2][5]

So start with a very small pipeline:

- spawn two workers,
- collect diff + tests,
- judge,
- pick or escalate.[5][1]

Do not begin with ten hooks, full test suite, deep static analysis, architectural critique, and multi-round debate unless the task truly justifies it.[2][5]

## Fast tests beat full tests

If every parallel branch runs the full suite, your orchestration latency may become worse than just letting one strong agent work. A repeated recommendation in harness-engineering discussions is to run the **smallest validating subset** first, then reserve broader CI for the chosen branch.[4][2]

Good approach:

- worker-local smoke tests first,[1]
- judge chooses winner,[5]
- only winner gets broader validation.[4]

## Decide what the orchestrator is allowed to edit

This is subtle but important: if the orchestrator can also edit code freely, it can blur responsibility and contaminate the evaluation. For your pattern, it is cleaner if:[3][4]

- workers edit code,
- orchestrator schedules and observes,
- judge recommends,
- final merge or final refinement happens in a fresh, explicit step.[3][1]

Otherwise you lose attribution and make debugging much harder.

## Log the run

You will want a machine-readable run record per task. At minimum capture:[5]

- task id
- worker branch/worktree path
- prompt/spec sent to each worker
- start/end times
- tests run
- result summary
- chosen winner
- reasons for selection[5]

Without that, you will not know whether the system is genuinely helping or just feeling sophisticated.

## Define “optimal” before you automate

Your phrase “more optimally done” needs an explicit scoring rule or the judge will drift. Pick a stable order such as:[3][5]

1. correctness,
2. passes target tests,
3. smallest safe diff,
4. least architectural damage,
5. readability / maintainability,
6. speed or token cost.[1][5]

If you do not define that hierarchy, the judge may reward verbosity, novelty, or broad rewrites when you actually wanted minimal safe patches.[3]

## Good first version

A solid v1 for your idea would be:

- Claude orchestrator in root, read-only except coordination.[7]
- Claude worker in worktree A.[7]
- Pi/external worker in worktree B.[8]
- Both get the same normalized task packet, but slightly different strategy instructions.[6][2]
- Judge compares diffs + targeted test results + branch metadata, then gives a winner and rationale.[1][5]

That is enough to learn whether the pattern helps before you invest in deeper hook logic.

If you want, I can next turn this into a **concrete control-flow design** with:
**task packet schema, worker prompts, judge rubric, and merge policy**.

## Human

Best practices for merging worktree outputs from parallel Claude agents

## Assistant

Best practice is to treat each worktree output as a **separate PR candidate**, not as partial edits to be auto-blended together, and to merge only after explicit validation and review. Parallel agent workflows work best when each worktree has a single owner, a single branch, and a clean handoff into a separate merge step rather than letting active agents merge one another’s changes.[1][2][3][4]

## Core merge rule

Use worktrees for **isolation during generation**, then switch to normal Git discipline for **selection and integration**. In practice, that means each agent writes to its own branch/worktree, you compare outputs side by side, and you merge the chosen branch or cherry-pick only the proven commits you want.[5][2][3][4]

## Preferred strategies

| Strategy | When to use it | Why it works |
|---|---|---|
| Merge one winning branch | When one agent clearly produced the best end-to-end implementation. | Lowest cognitive load and lowest recombination risk.[2][4] |
| Cherry-pick selected commits | When multiple branches contain useful but separable ideas. | Lets you keep the clean parts without importing whole-branch mistakes.[5][2] |
| Manual patch extraction | When branches overlap heavily in the same files. | Safer than merging two AI branches that both rewrote the same hotspot.[1][5] |
| Fresh integration branch | When you want a neutral branch to assemble the best pieces. | Preserves originals and keeps integration auditable.[2][4] |

## Best practices

- **Pick a winner before merging anything.** Do not start by merging agent A into agent B “just to see”; that usually destroys attribution and makes debugging harder.[1][5]
- **Compare artifacts, not summaries.** Review diff stats, changed files, tests, lint/typecheck, and runtime behavior rather than trusting each agent’s narrative of what it did.[2][5]
- **Prefer one-branch merge over multi-branch blending.** If one branch is good enough, merge that branch and stop; recombining several AI outputs often adds merge complexity with limited upside.[2][1]
- **Use cherry-pick for isolated wins.** If agent B has one excellent commit, cherry-pick that commit into the chosen branch instead of merging the full branch.[5][2]
- **Run validation after integration, not just before.** A branch can pass on its own and still fail after cherry-picks or merge resolution.[4][2]
- **Push branches and review via PR when possible.** Several guides recommend treating AI branches like human teammate branches, because standard PR review gives you visibility and rollback.[4][2]

## Safe merge flow

A strong operational sequence looks like this:[1][2][4]

1. Each agent works in its own branch/worktree.[3]
2. Freeze agent edits when outputs are ready; no active branch should keep changing during merge evaluation.[1]
3. Review:
   - `git diff --stat`
   - changed files
   - tests/lint/typecheck
   - architectural fit
   - merge risk against main.[5][2]
4. Select one branch as the base winner.[2]
5. Optionally cherry-pick isolated superior commits from other branches.[5]
6. Run tests again on the integrated result.[4][2]
7. Merge to main via normal PR flow.[4]

## What to avoid

The main anti-patterns are:

- **Letting agents merge each other’s branches while still active.** This creates “helpful interference” and destroys branch ownership.[1]
- **Merging two full AI branches that both changed the same core files.** That usually amplifies conflict noise rather than combining strengths.[2][5]
- **Assuming the most ambitious branch is the best branch.** In practice, smaller diffs with clear correctness often merge better than broad rewrites.[2]
- **Skipping human or judge review because both branches passed tests.** Tests are necessary, but they are not enough for architecture and maintainability decisions.[5][2]

## My practical recommendation

For your Claude-orchestrator idea, I would default to this merge policy:

- **Primary default:** merge the single winning branch unchanged if it is clearly best.[4][2]
- **Secondary option:** cherry-pick one or two clearly better commits from the losing branch.[5][2]
- **Avoid by default:** merging both full branches together unless they worked on deliberately disjoint surfaces.[1][5]

That policy is boring, but boring is good here because AI branch recombination is where a lot of hidden damage gets introduced.[2][1]

## Merge criteria

Before merging, score each branch on:

- Correctness against the requested task.[2]
- Targeted test pass rate.[4][2]
- Smallest safe diff / least unnecessary churn.[2]
- Architectural fit with the repo.[2]
- Ease of review and rollback.[4]

If you want, I can turn this into a concrete **merge rubric + git command sequence** for your exact workflow: Claude worker branch, Pi worker branch, judge branch, and final integration branch.

## Human

Example git commands for cherry-picking between worktrees
How to automate comparison of parallel agent outputs
Scripts for merging best parts from multiple worktrees

## Assistant

Yes — below are the concrete Git commands and automation patterns I’d use for your setup. I also prepared two reusable scripts: one to compare parallel worktree/branch outputs, and one to selectively merge the best parts.[1][2]

## Cherry-picking examples

Cherry-picking works across worktrees because Git cares about **branches and commits**, not which filesystem checkout created them. The safe rule is: switch to the target branch, then cherry-pick commits from the source branch.[3][4][1]

### Pick one commit from another worktree branch

```bash
git checkout integration/feature-x
git cherry-pick -x abc1234
```

`-x` appends the source commit reference, which is useful for auditability when integrating AI-generated work.[1]

### Pick several specific commits

```bash
git checkout integration/feature-x
git cherry-pick -x abc1234 def5678 9ab0cde
```

### Pick an inclusive commit range

```bash
git checkout integration/feature-x
git cherry-pick -x start_commit^..end_commit
```

The inclusive range form requires `start^..end`; plain `start..end` excludes the first commit.[5][1]

### Conflict handling

```bash
git cherry-pick -x abc1234
# resolve conflicts
git add .
git cherry-pick --continue
# or abort
git cherry-pick --abort
```

## Compare parallel agent outputs

The best automation is to compare **branches**, not directories, and to compare hard signals before prose summaries.[6][2]

Useful manual commands:

### Diff stats per agent branch

```bash
git diff --stat main...agent/claude-a
git diff --stat main...agent/pi-b
```

### Changed files per branch

```bash
git diff --name-only main...agent/claude-a
git diff --name-only main...agent/pi-b
```

### Commits unique to each branch

```bash
git log --oneline main..agent/claude-a
git log --oneline main..agent/pi-b
```

### Compare overlap between two agent branches

```bash
diff -u \
  <(git diff --name-only main...agent/claude-a | sort) \
  <(git diff --name-only main...agent/pi-b | sort)
```

That quickly tells you whether the branches are complementary or colliding.[6]

## Merge best parts from multiple worktrees

You generally want one of four strategies.[2]

| Strategy | Command pattern | Best for |
|---|---|---|
| Cherry-pick commit | `git cherry-pick -x <sha>` | One clearly good commit.[1] |
| Cherry-pick range | `git cherry-pick -x <start>^..<end>` | Small series of good commits.[5][1] |
| Whole-file import | `git checkout <branch> -- <path>` | One file is clearly better from another branch.[2] |
| Interactive hunk import | `git checkout -p <branch> -- <path>` | You want only some hunks from another branch.[2] |

### Whole-file import example

```bash
git checkout integration/feature-x
git checkout agent/pi-b -- src/auth/service.ts src/auth/types.ts
git commit -m "import auth implementation from agent/pi-b"
```

### Interactive hunk selection example

```bash
git checkout integration/feature-x
git checkout -p agent/pi-b -- src/auth/service.ts
git commit -m "import selected hunks from agent/pi-b"
```

This is often the safest way to “merge best parts” when both agents touched the same file.[2]

## Suggested integration workflow

For your parallel-Claude pattern, I’d use this sequence:

1. Keep each worker on its own branch/worktree.[6]
2. Create a fresh integration branch:
```bash
git checkout main
git pull
git checkout -b integration/feature-x
```
3. Compare branch outputs using diff stats, changed files, tests, and commit lists.[6]
4. Merge one winning branch entirely **or** cherry-pick/selectively import from others.[1][2]
5. Run tests again on the integration branch.
6. Open a PR from the integration branch.

## Included scripts

I created and shared two reusable scripts for this workflow:

- `compare-worktrees.sh`: compares multiple agent branches against a base branch, showing diff stats, changed files, commit lists, and optional JSON agent metadata.
- `merge-best-parts.sh`: supports four modes — `commit`, `range`, `file`, and `patch` — for selective integration from another branch.

### Example usage

Compare two parallel agent branches:

```bash
./compare-worktrees.sh main agent/claude-a agent/pi-b
```

Cherry-pick one winning commit:

```bash
./merge-best-parts.sh integration/feature-x agent/pi-b commit abc1234
```

Cherry-pick a commit range:

```bash
./merge-best-parts.sh integration/feature-x agent/pi-b range abc1234 def5678
```

Import whole files from another branch:

```bash
./merge-best-parts.sh integration/feature-x agent/pi-b file src/auth/service.ts src/auth/types.ts
```

Interactively import only chosen hunks:

```bash
./merge-best-parts.sh integration/feature-x agent/pi-b patch src/auth/service.ts
```

## Important caution

The main trap is thinking “multiple worktrees” means “merge directories.” It does not — you should always think in terms of **branches, commits, files, and hunks**. Worktrees are just isolated checkouts that make those branch operations easier and safer.[4][2]

If you want, I can next give you a **Windows-first PowerShell version** of the comparison and merge scripts tailored to your `P:\worktrees\...` layout.
