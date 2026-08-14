---
title: "I don't understand what CC is trying to tell me.  First, is it right?

❯ How will ccr sdk help with subagent routing?
"
date: "2026-01-09"
mode: "COPILOT"
uuid: "8195008b-a842-4963-b3a8-7d1d3402cdb0"
entry_count: 2
---

## Human

I don't understand what CC is trying to tell me.  First, is it right?

❯ How will ccr sdk help with subagent routing?

● CCR + SDK Subagent Routing: Technical Design

  Current State:
  - CCR routes between Chutes AI and OpenRouter providers at the HTTP level
  - Agent SDK mastery course teaches model-per-agent cost optimization

  Integration Approach:

  # src/lib/ccr_subagent_router.py

  from ccr import CCRClient
  from claude_agent_sdk import Agent

  class CostOptimizedRouter:
      """
      Route subagent calls through CCR with intelligent model selection.
      """

      # Agent type → CCR provider mapping
      AGENT_ROUTES = {
          # Quick checks: FREE tier
          'quick-check': {
              'provider': 'openrouter',
              'model': 'minimax/minimax-m2:free',
              'tools': ['Read', 'Grep'],
              'max_tokens': 4000,
          },

          # Code analysis: Premium (FP8 = cheaper)
          'code-analyzer': {
              'provider': 'chutes',
              'model': 'Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8',
              'tools': ['Read', 'Grep', 'Glob'],
              'max_tokens': 16000,
          },

          # Complex reasoning: High quality
          'complex-thinker': {
              'provider': 'openrouter',
              'model': 'openrouter/polaris-alpha',
              'tools': ['Read', 'Write', 'Bash', 'Edit'],
              'max_tokens': 32000,
          },
      }

      def __init__(self, ccr_endpoint="http://localhost:3460"):
          self.ccr = CCRClient(ccr_endpoint)

      async def route_subagent(self, agent_type: str, prompt: str) -> str:
          """
          Route a subagent call through CCR with cost-optimized model.
          """
          config = self.AGENT_ROUTES[agent_type]

          return await self.ccr.query(
              provider=config['provider'],
              model=config['model'],
              prompt=prompt,
          )

  Usage in Agent SDK workflows:

  # Example: TDD Agent Pipeline with cost routing
  router = CostOptimizedRouter()

  # 1. Quick-check agent (FREE)
  test_exists = await router.route_subagent(
      'quick-check',
      "Does tests/test_search.py exist?"
  )

  # 2. Code analyzer (FP8 - cheap premium)
  test_coverage = await router.route_subagent(
      'code-analyzer',
      "Analyze test coverage in search.py"
  )

  # 3. Complex thinker (polaris - high quality)
  architecture = await router.route_subagent(
      'complex-thinker',
      "Design test architecture for multi-backend parallel search"
  )

  Cost Impact:
  ┌───────────────────┬─────────────────┬─────────────────┬─────────┐
  │     Operation     │ Without CCR+SDK │  With CCR+SDK   │ Savings │
  ├───────────────────┼─────────────────┼─────────────────┼─────────┤
  │ Quick file checks │ $0.10/100 calls │ $0.00/100 calls │ 100%    │
  ├───────────────────┼─────────────────┼─────────────────┼─────────┤
  │ Code analysis     │ $0.30/100 calls │ $0.08/100 calls │ 73%     │
  ├───────────────────┼─────────────────┼─────────────────┼─────────┤
  │ Complex reasoning │ $0.50/100 calls │ $0.12/100 calls │ 76%     │
  └───────────────────┴─────────────────┴─────────────────┴─────────┘
  Key Insight: CCR handles the provider routing, SDK provides the subagent strategy. Combined: maximum cost efficiency without changing your agent code.

❯ You mean if I didn't want to use the current model provider, we coudl use ccr model routing to use free or cheaper llms to
  power the subagents?

● Yes, exactly. Here's the concrete benefit:

  Without CCR routing:
  All subagents → Your current provider (probably expensive)
  ├── File existence check → $0.001 per call
  ├── Simple grep → $0.002 per call
  ├── Code review → $0.015 per call
  └── Complex analysis → $0.025 per call

  With CCR routing:
  Quick checks → minimax-m2:free (FREE)
  ├── File exists? → $0.00
  ├── Count lines → $0.00
  └── Simple pattern match → $0.00

  Code analysis → qwen3-coder-fp8 (~80% cheaper)
  ├── Code review → $0.003 per call
  ├── Find bugs → $0.003 per call
  └── Refactoring suggestions → $0.003 per call

  Complex reasoning → polaris-alpha (~75% cheaper)
  ├── Architecture design → $0.006 per call
  └── Multi-step planning → $0.006 per call

  Real impact: If you run 100 subagent calls per session (typical for complex tasks):
  - Current: ~$1.50 per session
  - With CCR routing: ~$0.45 per session (70% savings)

  The key insight: Not every subagent call needs GPT-4/Claude-level intelligence. Simple tasks like "does this file exist?" can use free models. CCR automatically routes each call to the right provider based on the agent type you define.

❯ when we use llm_provider, do the tasks use a different memory context?  The subagents use a different memory context?  What's
  the advantage of using one vs the other?

● Great question - this gets to the heart of the Agent SDK architecture:

  Memory Context: llm_provider vs Subagents

  llm_provider (global setting):
  Single agent with global provider switch
  ├── All requests use same memory context
  ├── Conversation history preserved
  └── Just changes WHO answers (not WHAT they know)

  Subagents (isolated workers):
  Main agent
  ├── Memory: Full conversation history
  │
  ├── Subagent A → Memory: EMPTY (only what you pass)
  ├── Subagent B → Memory: EMPTY (only what you pass)
  └── Subagent C → Memory: EMPTY (only what you pass)

  Key Difference
  ┌───────────────┬───────────────────────┬────────────────────────────────┐
  │    Aspect     │     llm_provider      │           Subagents            │
  ├───────────────┼───────────────────────┼────────────────────────────────┤
  │ Memory        │ Shared across session │ Isolated per agent             │
  ├───────────────┼───────────────────────┼────────────────────────────────┤
  │ Context       │ Full conversation     │ Only what you explicitly pass  │
  ├───────────────┼───────────────────────┼────────────────────────────────┤
  │ Communication │ N/A (single agent)    │ Through orchestrator only      │
  ├───────────────┼───────────────────────┼────────────────────────────────┤
  │ Parallel      │ No                    │ Yes (can run multiple at once) │
  └───────────────┴───────────────────────┴────────────────────────────────┘
  Subagent Context Isolation (Important!)

  # Main agent sees everything
  main_conversation = [
      "User asked about bug in auth.py",
      "I looked at the file",
      "Found SQL injection at line 42"
  ]

  # Subagent sees NOTHING unless you pass it
  subagent_conversation = []  # Empty!

  # You MUST pass relevant context
  result = await subagent_task(
      subagent_type="security",
      prompt="Check auth.py line 42 for SQL injection",
      # Subagent doesn't know about prior conversation!
  )

  When to Use Which

  Use llm_provider when:
  - You want to switch providers but keep same workflow
  - Cost is the only concern
  - You don't need parallel execution

  Use Subagents when:
  - You need parallel execution (e.g., 3 reviewers at once)
  - You want specialized agents (security, performance, style)
  - You want to isolate failures (one agent crash doesn't stop others)
  - You're okay with manual context passing

  The CCR Opportunity

  CCR can help with both:

  1. With llm_provider: Set CCR as your provider, it routes all calls intelligently
  2. With subagents: Each subagent type routes through CCR to its optimal model

  # Option 1: Simple provider switch
  llm_provider = "ccr"  # All calls routed automatically

  # Option 2: Per-subagent routing
  subagents = {
      'security': {'provider': 'openrouter', 'model': 'free'},
      'analysis': {'provider': 'chutes', 'model': 'fp8'},
  }

  The subagent approach gives you granular control at the cost of manual context management.

❯ are you sure?  If I use 5 llm_provider calls, how's that different than 5 ccr subagent calls?

● You're right to question - let me clarify:

  Same Provider, Different Memory

  5 llm_provider calls:
  Single conversation context shared across all calls
  Call 1: "Check auth.py" → sees all prior context
  Call 2: "Now check user.py" → sees Call 1's results
  Call 3: "Compare them" → sees Call 1 + 2 results

  5 subagent calls:
  Each call has ISOLATED context (blank slate)
  Subagent 1: "Check auth.py" → sees NOTHING else
  Subagent 2: "Check user.py" → sees NOTHING else
  Subagent 3: "Compare them" → sees NOTHING unless you pass Call 1 + 2 results

  The Confusion Point

  CCR routing works the SAME either way - it just routes requests to different providers. The difference is in memory context, not who answers.
  ┌────────────────────┬─────────────────────┬───────────────────┐
  │                    │    llm_provider     │     Subagents     │
  ├────────────────────┼─────────────────────┼───────────────────┤
  │ Provider routing   │ CCR can route       │ CCR can route     │
  ├────────────────────┼─────────────────────┼───────────────────┤
  │ Memory             │ Shared across calls │ Isolated per call │
  ├────────────────────┼─────────────────────┼───────────────────┤
  │ Parallel execution │ No                  │ Yes               │
  └────────────────────┴─────────────────────┴───────────────────┘
  So When Would You Use Subagents?

  Only when you need:
  1. Parallel execution - 3 reviewers analyzing simultaneously
  2. Isolation - One agent's failure doesn't affect others
  3. Specialization - Different prompts/tools per agent type

  For cost routing alone? llm_provider = "ccr" is simpler - you get intelligent routing without the context isolation headache.

  My earlier CCR+SDK idea conflated two separate concerns:
  - Cost routing → CCR alone handles this
  - Parallel specialized agents → SDK subagents, with CCR routing each

  Does that clarify?

❯ I don't understand how llm_provider sees all the context.  When we invoke an api call with python, we have to tell it what to
  look at because it doesn't know anything.

● You're absolutely right - at the API level, every call is stateless. Let me clarify what I meant:

  Two Different Things

  1. Direct API calls (what you're thinking of):
  # YOU manage context manually
  messages = [
      {"role": "user", "content": "Check auth.py"},
      {"role": "assistant", "content": "Found bug at line 42"},
      {"role": "user", "content": "Now check user.py"}  # Must pass full history
  ]
  response = client.chat.completions.create(messages=messages)

  2. Claude Code's llm_provider setting:
  # CLAUDE CODE manages context internally
  llm_provider="openrouter"  # Just changes the endpoint
  # Claude Code still handles conversation history - you don't see it

  What Actually Happens

  Your Claude Code session:
  ├── Claude Code maintains full conversation history
  ├── When you ask a question, Claude Code packages:
  │   ├── System prompt
  │   ├── Full conversation history
  │   └── Current question
  └── Sends to provider (could be Anthropic, OpenRouter, CCR, etc.)

  llm_provider just changes the destination - Claude Code still handles all the context management behind the scenes.

  Subagents Are Different

  # Subagent = completely separate agent instance
  subagent = Agent("security-review")
  # This subagent has NO access to main conversation
  # YOU must explicitly pass relevant context
  result = await subagent.run(
      prompt="Review auth.py line 42",
      context={"bug_found": "SQL injection"}  # Manual!
  )

  Bottom Line
  ┌────────────────────┬─────────────────────────┐
  │      Approach      │  Who manages context?   │
  ├────────────────────┼─────────────────────────┤
  │ llm_provider="ccr" │ Claude Code (automatic) │
  ├────────────────────┼─────────────────────────┤
  │ Direct API calls   │ You (manual)            │
  ├────────────────────┼─────────────────────────┤
  │ SDK Subagents      │ You (manual, per agent) │
  └────────────────────┴─────────────────────────┘
  You were right to question - at the HTTP level, all API calls are stateless. The "shared context" I mentioned is Claude Code's internal management, not something the API does.

## Assistant

I need to parse what CC (Claude Code) is telling you here, because there's a **fundamental confusion that needs clearing up**.

Let me work through this step-by-step:

## What CC Got Right

✅ **CCR can route API calls to different providers** - that part is correct.

✅ **You always have to explicitly pass context in API calls** - your final point is correct.

## What CC Got Confused About

❌ **The "llm_provider sees all context" claim is misleading.**

Here's the actual situation:

### How `llm_provider` in Claude Code Actually Works

When you set `llm_provider="ccr"` or `llm_provider="openrouter"` in Claude Code:

1. **Claude Code is running locally in your VSCode**
2. **It maintains YOUR session's memory** (conversation history, file state, etc.)
3. **Every time it makes an API call**, it explicitly constructs the messages array with:
   - System prompt
   - Relevant conversation history
   - Current request
4. **Then sends that to the provider**

**The key insight CC missed**: Claude Code is still explicitly passing all context - it's just hidden from you. You don't see the `messages=[]` array, but it's there.

```python
# What's ACTUALLY happening inside Claude Code:
messages = [
    {"role": "system", "content": "You are an AI assistant..."},
    {"role": "user", "content": "Check auth.py"},
    {"role": "assistant", "content": "Found SQL injection at line 42"},
    {"role": "user", "content": "Now check user.py"}
    # ↑ Full history explicitly passed
]

response = await ccr_client.chat.completions.create(
    model="whatever-model",
    messages=messages  # ← Explicit context
)
```

## The Real Distinction

```
llm_provider = "ccr"  (in Claude Code)
├── Claude Code manages context internally (you don't see it)
├── But it STILL explicitly passes context on each API call
└── CCR just receives it and routes to right provider

Direct API calls (what you do in Python)
├── YOU construct the messages array
├── YOU decide what context to include
└── YOU send it to the API

SDK Subagents
├── Each subagent is a separate Claude Code instance
├── Each has its OWN local session memory
├── You must manually pass context between them
└── Context is NOT shared automatically
```

## What This Means for Your Use Case

**If you're building with direct Python API calls:**

```python
# YOU manage context every time
messages = [
    {"role": "user", "content": "Check auth.py"},
]
response = await client.chat.completions.create(messages=messages)

messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user", "content": "Now check user.py"})
response = await client.chat.completions.create(messages=messages)
```

**If you're using Claude Code's llm_provider:**

```python
# Claude Code handles context, you just ask questions
# Behind the scenes it's doing the same thing as above, 
# but you don't see the message construction
llm_provider = "ccr"
# Ask questions normally - context is managed for you
```

**If you're using SDK subagents:**

```python
# Each subagent is completely isolated
result1 = await subagent_a.run("Check auth.py")
# Subagent B doesn't know about result1 unless you tell it
result2 = await subagent_b.run(f"Check user.py. Found in auth: {result1}")
```

## Is CC's CCR+SDK Recommendation Still Valid?

**Partially:**

✅ **CCR can route different providers** - yes
✅ **Cost savings are real** - yes  
❌ **The memory context explanation was confusing** - yes, but the underlying idea works

**The actual value proposition:**

```
Without CCR: Simple task uses expensive provider
"Does file exist?" → calls OpenRouter's expensive model ($0.01)

With CCR: Simple task routes to free model
"Does file exist?" → CCR routes to minimax:free ($0.00)
```

This works whether you're using `llm_provider` or subagents - both end up making HTTP API calls that need context explicitly managed.

***

**Bottom line:** You were right to question CC. At the API level, context is always explicitly managed. Whether that's hidden (Claude Code) or visible (your Python code), it's always there. CCR's value is purely in **provider routing**, not in somehow magically preserving context.

## Human

llm_provider is custom code that uses various provider sdks to send messages to their chat endpoints.  it doesn't come with Claude Code.

## Assistant

Ah, that's a **critical correction** - thank you. That changes everything.

So `llm_provider` is **your custom abstraction layer** that:

1. Takes your prompt/messages
2. Routes to different provider SDKs (OpenRouter, Chutes, Groq, etc.)
3. Sends to their chat endpoints
4. Returns the response

This means CC's explanation was actually **worse than I thought** because:

**CC was describing Claude Code's internal behavior** (which doesn't apply to you) **instead of how YOUR custom `llm_provider` actually works.**

## What's Actually True for Your Setup

```python
# Your llm_provider function
def llm_provider(messages, model, provider):
    # YOU explicitly pass messages (context)
    # Stateless API call - provider doesn't know history
    response = provider_sdk.chat.completions.create(
        messages=messages,  # ← You manage this
        model=model
    )
    return response

# Call 1
response1 = llm_provider(
    messages=[{"role": "user", "content": "Check auth.py"}],
    provider="openrouter"
)

# Call 2 - if you want context from Call 1, YOU must add it
response2 = llm_provider(
    messages=[
        {"role": "user", "content": "Check auth.py"},
        {"role": "assistant", "content": response1},
        {"role": "user", "content": "Now check user.py"}  # ← YOU added this
    ],
    provider="openrouter"
)
```

## So CC's Claims About Memory Context Were Just Wrong

**CC said:** "llm_provider sees all prior context"  
**Reality:** You explicitly pass whatever context you include in the messages array.

**CC said:** "Subagents have isolated context"  
**Reality:** Both approaches are identical at the API level - everything is stateless. The difference is:
- With `llm_provider`: You manage context in your orchestration code
- With subagents: Each agent instance manages its own context internally (but still passes it explicitly on API calls)

## Is CC's CCR Routing Idea Still Valid?

**Yes, but simpler:**

Instead of:
```python
response = llm_provider(
    messages=messages,
    provider="openrouter",
    model="expensive-model"
)
```

With CCR:
```python
response = llm_provider(
    messages=messages,
    provider="ccr",  # CCR decides which provider/model
    model="auto"
)
```

CCR is just another provider endpoint that internally routes to cheaper alternatives. The context management part CC explained is irrelevant to your setup.
