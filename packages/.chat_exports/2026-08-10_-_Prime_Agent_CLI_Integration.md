# 2026-08-10 - Prime Agent CLI Integration

- **Created:** 8/13/2026, 7:39:59 AM
- **Exported:** 8/13/2026, 7:40:02 AM
- **Messages:** 5
- **Source:** browser_extension

---

## #1 · assistant

Yes. I searched specifically for repos that already implement **“Claude Code as the harness, cheaper heterogeneous models as delegated workers.”** There are several, and one discovery materially changes my previous recommendation.

## The strongest matches

| Repo | Keeps Claude Code UX | Different main model | Different subagent models | Automatic routing | External CLI agents | Match |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code Router (CCR) | ✅ | ✅ | ✅ | ✅ | Some | 9/10 |
| Rayline | ✅ | Claude-oriented | ✅ | ✅ | — | 9/10 conceptually |
| AnyClaude | ✅ | ✅ | ✅ | configurable | — | 8/10 |
| Claude Code Delegator | ✅ | Claude | worker models | Claude-directed | — | 8/10 |
| Codeg | ❌ own UI | — | cross-harness | agent-directed | ✅ excellent | 7/10 |
| AWS CAO | supervisor CLI | — | cross-harness | orchestration | ✅ excellent | 6/10 for this goal |

### Most importantly: CCR already has explicit subagent model routing

This is the feature I understated earlier.

CCR documents this syntax for a Claude Code subagent prompt:

```
<CCR-SUBAGENT-MODEL>provider,model</CCR-SUBAGENT-MODEL>
```

CCR then routes **that particular subagent** to the specified provider/model. [[image]GitHub](https://github.com/musistudio/claude-code-router/blob/main/README.md?utm_source=chatgpt.com)

So you can potentially implement:

```
             CLAUDE CODE
                  │
             GLM 5.2 main
                  │
           Claude Agent tool
                  │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
 reasoning    mechanical    coding
    agent        agent       agent
       ↓          ↓          ↓
  provider A  provider B  provider C
  model R1    model M1    model C1
```

**without building the MCP delegation system I proposed.**

CCR already centralizes providers, API keys, routing, request logs, latency and approximate costs, and explicitly advertises automatic routing of different kinds of work to different models. [[image]Musi Studio+1](https://musistudio.github.io/claude-code-router/en/?utm_source=chatgpt.com)

That makes **extending what you already have** the first thing I'd investigate.

## Rayline is almost exactly your idea

This is particularly interesting because its stated motivation is essentially yours:

> 
Keep Claude Code, but stop spending expensive Claude tokens on work cheaper models can perform.

Rayline was built specifically to override **Claude Code subagent routing** so that the main Claude agent can delegate work to open-source/on-device/OpenAI-compatible models. Its authors describe configurable routing rules plus automatic/ML routing. [[image]Reddit](https://www.reddit.com/r/ClaudeCode/comments/1tylb4p/claude_code_model_router_that_lets_opus_route/?utm_source=chatgpt.com)

Its architecture is roughly:

```
Claude Code
    │
 main agent
    │
 Agent/subagent invocation
    ↓
 RAYLINE
    ↓
routing policy
 ┌───────┼────────┐
 ↓       ↓        ↓
cheap   coding   strong
model   model    model
```

That's extremely close to our three-pool design.

Even if we don't use Rayline, **we should inspect its routing implementation before writing ours.**

## AnyClaude also implements per-subagent backend affinity

Another project called **AnyClaude** added explicit subagent routing this year.

It observes Claude Code's `SubagentStart` hook, registers the agent, assigns it a backend, and then maintains **session affinity** so that subagent remains pinned to the same backend throughout its lifetime. [[image]Reddit](https://www.reddit.com/r/ClaudeCode/comments/1rt00e3/anyclaude_050_now_supports_subagents_routing_to/?utm_source=chatgpt.com)

That addresses a subtle problem we would otherwise have to solve:

```
subagent starts
    ↓
coding pool chooses model X
    ↓
request #1 → X
request #2 → X
request #3 → X
...
```

rather than accidentally doing:

```
request #1 → GLM
request #2 → Qwen
request #3 → Grok
```

which can create context/behavior drift.

Its implementation also separates request processing into stages such as extraction, routing, headers, thinking, forwarding, transformation and response handling. [[image]Reddit](https://www.reddit.com/r/ClaudeCode/comments/1rt00e3/anyclaude_050_now_supports_subagents_routing_to/?utm_source=chatgpt.com)

That's another repo worth mining architecturally.

## There's also a purpose-built Claude Code Delegator

I found a recent project whose author describes exactly the economic problem:

> 
Claude is excellent at orchestration, but using it for file audits, documentation, repository analysis and other grunt work is unnecessarily expensive.

The solution is an **MCP server living inside the Claude Code session**. Claude delegates work to it, and critically the MCP server can read files itself and send them directly to the cheaper model—so those files **never enter Claude's expensive context window**. [[image]Reddit](https://www.reddit.com/r/coolgithubprojects/comments/1uv6w44/i_built_a_thing_that_delegates_claude_codes_grunt/?utm_source=chatgpt.com)

It supports providers/models including:

- 
GLM

- 
Grok

- 
Kimi

- 
Qwen

- 
DeepSeek

- 
Groq

- 
OpenRouter

That is basically the MCP architecture I proposed in my previous answer—but someone has already implemented it.

This one deserves examination because **avoiding main-agent context ingestion** may save as much money as model routing itself.

# And then Codeg solves the full-agent delegation problem

[Codeg](https://github.com/xintaofei/codeg?utm_source=chatgpt.com) already supports:

**Claude Code · Codex · Gemini · OpenClaw · OpenCode · Cline · Hermes · CodeBuddy · Kimi · Pi · Grok · Cursor.**

More importantly, it lets one agent delegate work to **another type of agent within the same task**, launches each as an independent session, and streams the results back. [[image]GitHub](https://github.com/xintaofei/codeg?utm_source=chatgpt.com)

So Codeg solves:

```
Claude Code
    ↓
delegate whole coding task
    ↓
Grok Build / Pi / Codex
```

whereas CCR/Rayline/AnyClaude are more interesting for:

```
Claude Code Agent()
    ↓
different underlying MODEL
```

Those are complementary capabilities.

# AWS CAO solves the same problem one layer higher

[AWS CLI Agent Orchestrator](https://github.com/awslabs/cli-agent-orchestrator?utm_source=chatgpt.com) runs complete native coding CLIs in isolated tmux sessions and coordinates them using MCP.

Currently documented agents include Claude Code, Codex, Gemini, Kimi, OpenCode, Copilot, Kiro and Amazon Q. [[image]GitHub](https://github.com/awslabs/cli-agent-orchestrator?utm_source=chatgpt.com)

So:

```
Claude supervisor
       ↓
      CAO
 ┌─────┼─────┐
 ↓     ↓     ↓
Claude Codex Kimi
 CLI    CLI   CLI
```

It's excellent if we want **whole-agent delegation**, but probably too much machinery for the immediate cost-routing problem.

# This changes what I think we should build

I would now divide the problem into **two delegation levels**:

```
                     CLAUDE CODE
                          │
                    GLM 5.2 director
                          │
                    TASK CLASSIFIER
                          │
          ┌───────────────┴────────────────┐
          │                                │
     MODEL DELEGATION                AGENT DELEGATION
          │                                │
   CCR / Rayline                    Codeg / CAO /
    / AnyClaude                     Grok Build/Pi
          │                                │
 ┌────────┼─────────┐                ┌─────┴──────┐
 ↓        ↓         ↓                ↓            ↓
reason  mechanical coding           Grok          Pi
pool      pool      pool             Build
```

### Model delegation

Use when the task is bounded and doesn't require an autonomous coding environment:

- 
reasoning

- 
reviewing

- 
summarization

- 
reconnaissance

- 
classification

- 
code analysis

- 
documentation

- 
extraction

This should be **cheap and fast**.

### Agent delegation

Use when the worker needs to:

- 
navigate the repository autonomously;

- 
edit multiple files;

- 
execute commands;

- 
debug;

- 
iterate against tests;

- 
maintain its own substantial context.

Then spawn **Grok Build, Pi, Codex, etc.**

That distinction prevents us from paying the overhead of an entire agent harness for something GLM/Qwen/Kimi can answer in one inference.

# There's one more repo I'd add: Agent-as-a-Router

[Agent-as-a-Router / ACRouter](https://github.com/LanceZPF/agent-as-a-router?utm_source=chatgpt.com) is research rather than a Claude Code integration, but it's directly relevant to **how our three-pool router should learn**.

Their finding is important: routing isn't best treated as a static one-shot classifier. Their router uses:

```
Context
   ↓
Action/model selection
   ↓
actual execution
   ↓
Verifier
   ↓
Feedback
   ↓
Memory
   └────────→ future routing
```

They released a benchmark containing roughly **10,000 coding tasks with verified results from eight frontier LLMs**, and their execution-feedback router achieved lower cumulative routing regret than static alternatives. [[image]arXiv](https://arxiv.org/abs/2606.22902?utm_source=chatgpt.com)

That's essentially the eventual evolution of your router:

```
"coding task"
     ↓
don't permanently assume Grok is best

observe:
GLM success = 72%
Grok success = 91%
Kimi success = 86%

for THIS class of coding task
     ↓
router adapts
```

That's much better than hand-maintaining a giant routing table forever.

# My revised shortlist

I would **not implement anything yet**.

I'd inspect four projects in this order:

1. 
**CCR** — because you already use it and it apparently already implements explicit **per-subagent model routing**.

2. 
**Rayline** — because it specifically implements the Claude-main-agent → cheaper-subagent architecture we're describing.

3. 
**Claude Code Delegator** — because the MCP/files-direct-to-worker design could dramatically reduce expensive main-context tokens.

4. 
**Codeg** — for the separate case where a task deserves an entire Grok Build/Pi/other harness rather than merely another model.

Then borrow **ACRouter's feedback architecture** later, once we've collected actual task outcomes.

The likely solution may therefore be much smaller than we've been imagining:

```
Claude Code
     +
CCR
     +
3 task-class subagents
     +
routing annotations/hooks
     +
optional external-agent delegation
```

rather than another agentic platform.

And that would give you almost exactly the thing you've been asking for: **Claude Code's excellent harness, GLM as the inexpensive director, automatic cheap-model workers, and Anthropic models reserved for work where their quality actually earns their price.**

## #2 · user

Please don't pick a project because I've used it before. I am willing to do radical refactoring to achieve even the smallest positive ROI.

## #3 · assistant

Understood. Prior use should carry **zero architectural preference**. CCR, Claude Code, Grok Build, Pi, or anything we've built ourselves should survive only if evidence says they're the best component.

That changes my recommendation materially.

### The decision criterion

We should optimize for **expected total ROI**, not migration convenience:

ROI=migration/maintenance costquality gain+cost savings+time savings−migration/maintenance cost​
And because you're willing to refactor for even a small positive return, **switching cost is a cost term, not a veto**.

So I would no longer start with:

> 
“How can we extend CCR?”

I'd start with:

> 
**“Given Claude Code's harness is desirable but Anthropic inference is expensive, what existing architecture gives us the highest-quality model-neutral harness + automatic task delegation at the lowest total cost?”**

That means evaluating at least four architectural families independently:

| Architecture | Example | What we'd test |
| --- | --- | --- |
| Proxy/router under Claude Code | CCR, AnyClaude, Rayline | Can we preserve Claude Code while reliably changing models per task/subagent? |
| Delegation beside Claude Code | Delegator, CAO, Codeg | Can Claude remain the UX while external workers absorb most inference? |
| Model-neutral replacement harness | Pi, Prime Agent, Hermes | Is replacing Claude Code actually better overall? |
| Programmable orchestration | Prime/RLM, LangGraph-style, custom thin layer | Does explicit orchestration outperform agent-decided delegation enough to justify it? |

And I want to correct another bias from my previous answer: **we shouldn't assume Claude Code must remain the harness either.** That's a hypothesis.

The real target is:

```
best harness
    +
best cheap orchestrator
    +
best task router
    +
best worker pools
    +
minimal deterministic enforcement
```

If that turns out to be:

```
Pi + GLM + NVIDIA/Kimi/Grok workers
```

we should abandon Claude Code.

If it's:

```
Claude Code + Rayline + heterogeneous subagents
```

use that.

If Prime's programmatic/RLM approach measurably produces better decomposition and fewer wasted calls, use Prime.

If Grok Build already provides 90% of this with less machinery, **stay with Grok Build**.

### One further change

I also don't think we should compare these from feature lists.

Our failures are unusually useful benchmark data. The proper test is a **replay corpus** of perhaps 30–50 real tasks covering:

```
mechanical
coding
reasoning
mixed/decomposition
skill-triggering
failure recovery
verification
```

For each candidate architecture measure:

**verified success, wall-clock time, inference cost, user interventions, routing accuracy, skill compliance, context/token consumption, retries, and maintenance complexity.**

Then calculate something like:

> 
**cost per verified successful task**

along with intervention minutes per successful task.

That's much harder for a flashy architecture to game than benchmark scores or feature counts.

### What I think we should investigate next

I would actually broaden the search **one more time before choosing anything**.

Our previous searches have been progressively revealing entire classes of solutions we hadn't considered—Prime/Hermes, then CAO/Orca, then Rayline/AnyClaude/Delegator. That tells me the solution-space search is **not saturated yet**.

So the next research question shouldn't be “which of these wins?”

It should be:

> 
**Find every credible open-source architecture as of August 2026 that supports model-neutral coding-agent harnesses, heterogeneous per-task/per-subagent routing, external-agent delegation, skill/tool enforcement, cost-aware routing, and outcome-feedback routing. Include projects even if they would require replacing our entire existing architecture. Identify mechanisms rather than merely products, and specifically search for projects that make our proposed components unnecessary.**

Then we can build a **capability × evidence × complexity matrix**, identify dominated alternatives, and only benchmark the nondominated architectures.

Given your willingness to refactor radically, that's the economically rational approach: **nothing gets grandfathered in—not even Claude Code.**

## #4 · user

ROI should not consider transition effort. In my head, that's irrelevant.

## #5 · assistant

Agreed. Then the objective function should exclude migration effort entirely.

For these architecture decisions, I’ll evaluate ROI primarily as:

ROI∝quality+speed+cost efficiency+reliability+maintainability−ongoing operational burden
Transition/refactor effort is **not a penalty term**.

That means a radical replacement can beat an incremental extension even for a modest long-run advantage. In practice, I should rank candidates by their **steady-state architecture**, not by how easy they are to adopt from where you are today.
