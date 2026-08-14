---
title: "Claude Code Vector/RAG Memory Integration GitHub Repos"
date: "2025-12-17"
mode: "COPILOT"
uuid: "2fd1f685-30e6-4b2f-9d08-f91732492f6a"
entry_count: 6
---

## Human

I think we may have talked about this.  My claude code isn't using our vector/rag memory bank at all even though it would help a lot.  What github.com repos address this issue?

## Assistant

Perfect—I found exactly what you're looking for. Here are the key GitHub repos addressing Claude Code + vector/RAG memory integration:

## Top Repos for Claude Code Vector/RAG Memory

### 1. **christian-byrne/claude-code-vector-memory** ⭐ Most Direct Solution
**URL:** https://github.com/christian-byrne/claude-code-vector-memory

This is the most directly applicable repo for your use case:
- **Semantic memory system** using sentence transformers for vector search
- **Hybrid scoring** combining semantic similarity (70%), recency (20%), complexity (10%)
- **ChromaDB backend** for persistent vector storage
- **Claude Code integration** - automatically searches memories before each task
- **Cross-platform** support (Linux, macOS, Windows)
- **Features:**
  - Indexes your Claude session summaries
  - Creates semantic embeddings
  - Beautiful CLI with search
  - One-time setup via `setup.sh`/`setup.bat`

This directly solves the problem of Claude Code forgetting context between sessions.

***

### 2. **basicmachines-co/basic-memory**
**URL:** https://github.com/basicmachines-co/basic-memory

Local-first knowledge management via MCP:
- Built on Model Context Protocol (MCP)
- Bidirectional LLM communication
- Can import conversations from Claude, ChatGPT, JSON
- GitHub integration for full workflow participation
- Sync and watch capabilities

***

### 3. **Qdrant-based RAG System (from AIBoosted.dev)**
**URL:** Referenced in guide at aiboosted.dev

While not a single repo, this demonstrates:
- **Qdrant vector database** setup for documentation
- **MCP server integration** connecting Qdrant to Claude
- **Semantic chunking** and embedding storage
- Good architectural reference for building your own

***

## Why Your Claude Code Isn't Using RAG Currently

From the search results, the issue is architectural:
- **Default behavior**: Claude Code has limited inter-session memory—summaries are compacted/lost
- **Token cost**: Reading full documentation/memory consumes massive token budgets (example: 54,000+ tokens just analyzing API docs)
- **No automatic RAG**: You need explicit integration (like vector-memory repo above) to enable it

***

## Recommended Next Steps

**If you want quick implementation:**
1. Clone `christian-byrne/claude-code-vector-memory`
2. Run platform-specific setup
3. Configure Claude Code to call the memory search before tasks

**If you want custom RAG:**
1. Set up Qdrant vector DB
2. Build MCP server wrapper for semantic search
3. Configure Claude Code to use MCP server

Would you like me to help you set up one of these, or dive deeper into how to integrate vector memory with your specific Claude Code workflow?

## Human

I think we were also looking at something from some one named [https://github.com/ChrisRoyse?tab=repositories](https://github.com/ChrisRoyse?tab=repositories) and [https://github.com/ruvnet?tab=repositories](https://github.com/ruvnet?tab=repositories) claude-flow, and other things.

## Assistant

Perfect! Yes, those are exactly the repos you were looking at. Here's the breakdown:

## Key Repos from ChrisRoyse & ruvnet

### 1. **ruvnet/claude-flow** ⭐ Main Enterprise Orchestration
**URL:** https://github.com/ruvnet/claude-flow
- **Claude-Flow v2.0.0 Alpha** - Revolutionary AI development orchestration
- **Multi-agent swarm coordination** with parallel execution (2.8-4.4x speed improvements)
- **87 MCP tools** integrated
- **Cross-session memory persistence** - directly addresses your RAG/memory issue!
- **Neural network capabilities** - 27+ neural models with WASM SIMD acceleration
- **84.8% SWE-Bench solve rate**
- **Hook-based system:** `pre-task`, `pre-search`, `pre-edit`, `pre-command`, `post-edit`, `session-end`
- **GitHub integration** - PR management, issue tracking, workflow automation
- **Self-healing workflows** - automatic error recovery and optimization
- **Zero-config setup** - automatic MCP integration

### 2. **ChrisRoyse/610ClaudeSubagents** ⭐ Massive Agent Catalog
**URL:** https://github.com/ChrisRoyse/610ClaudeSubagents
- **600+ specialized AI agents** pre-configured and ready to use
- **Specialized categories:**
  - 188 Coding Agents (languages, frameworks, testing)
  - 38 AI-ML Development agents
  - DevOps/Infrastructure (AWS, Kubernetes, Docker, serverless)
  - Database specialists (PostgreSQL, MongoDB, etc.)
  - Security & compliance agents
- **Works seamlessly with Claude-Flow** - these are the "workers" for the orchestration
- Designed to work in parallel swarms

### 3. **ChrisRoyse/MCP-Prompt-STDIO**
**URL:** https://github.com/ChrisRoyse/MCP-Prompt-STDIO
- Helper for building MCP servers
- Useful for creating custom memory/RAG MCP integrations

***

## How This Solves Your Vector/RAG Problem

**claude-flow v2.0.0 specifically addresses persistent memory:**
- ✅ **Cross-session memory** - remembers context between executions
- ✅ **Neural training** - learns from past operations via `neural train --pattern coordination`
- ✅ **Session persistence** - `session-end --generate-summary --persist-state`
- ✅ **MCP tool integration** - 87 tools mean you can wire in your vector DB
- ✅ **Memory stats tracking** - `npy claude-flow@alpha memory stats`

***

## Quick Integration Path

**Combine all three:**
```bash
# 1. Use claude-flow as orchestration engine
npm install -g @anthropic-ai/claude-flow@alpha

# 2. Spawn agents from the 610ClaudeSubagents catalog
npx claude-flow@alpha hive-mind spawn "Your task here" --agents 10

# 3. Memory persists automatically via cross-session state
npx claude-flow@alpha memory stats
```

This is a **much more complete solution** than just adding vector memory—it's a full multi-agent orchestration platform with built-in persistent memory, which directly addresses why Claude Code wasn't accessing your knowledge bank before.

Did you want me to save these repos + integration notes to your research file for later reference?

## Human

Is there a way to evaluate technical merit?  What the happy path is?

## Assistant

## Technical Merit Evaluation Framework

**tl;dr:** claude-flow includes `swarm-bench`—a comprehensive benchmarking system. The happy path is SWE-Bench evaluation with clear, measurable milestones.

***

## How to Evaluate Technical Merit

### Built-in Benchmarking System
`ruvnet/claude-flow` provides `swarm-bench`—official evaluation tooling with quantifiable metrics. You're not relying on marketing claims; you're measuring real performance:[1][2]

| **Metric** | **Target** | **Why It Matters** |
|-----------|-----------|------------------|
| **Success Rate** | >85% production, >95% ideal[1] | % of tasks solved completely |
| **Execution Time** | <5 min simple, <15 min complex[1] | Including coordination overhead |
| **Token Efficiency** | 0.85 target (0.7 minimum)[2] | Output value per token spent |
| **Coordination Score** | 80-90%[2] | How well agents work together |
| **Code Quality** | Syntax + logic + best practices[1] | For software engineering tasks |

### Quality Evaluation Criteria (Real-World Alignment)
Rather than just benchmark scores, evaluate against human-centered dimensions:[3]

- **Coherence** — Does the reasoning flow logically across multiple steps?
- **Accuracy** — Does it actually solve your stated problem (not just look correct)?
- **Clarity** — Are recommendations actionable or theoretical?
- **Relevance** — Does it address YOUR specific context (not generic)?
- **Efficiency** — How much productivity time/token cost saved? (ROI)[3]

***

## The Happy Path: SWE-Bench Evaluation

### Phase 1: Verify Setup (5-10 minutes)
```bash
swarm-bench swe-bench official --limit 1
```
Single task to confirm the pipeline works. Should generate a valid git diff patch.[4]

### Phase 2: Batch Test (30-60 minutes)
```bash
swarm-bench swe-bench official --limit 5 --lite
```
Expected: >60% success rate on 5 tasks from lite dataset. Identify error patterns.[4]

### Phase 3: Mode Comparison (1-2 hours)
```bash
swarm-bench swe-bench multi-mode --instances 2 --quick
```
Compares orchestration modes (centralized, distributed, mesh, hierarchical) to find which performs best on your system.[4]

### Phase 4: Full Evaluation (5-8 hours)
```bash
swarm-bench swe-bench official --lite --mode mesh --strategy optimization
```
Production-grade evaluation. **Expected result: 75-84.8% solve rate** (matching ruvnet's claimed 84.8% SWE-Bench performance).[2][5]

**Outputs:**
- `predictions.json` — Can submit to official SWE-Bench leaderboard
- `evaluation_report_*.json` — Detailed per-task metrics
- `multi_mode_report_*.json` — Mode performance comparison

***

## Claimed Technical Merit: ruvnet/claude-flow v2.0.0

These are the metrics to validate through your own benchmarking:[5]

- **84.8% SWE-Bench Solve Rate** — Solves 4 out of 5 real software engineering issues
- **32.3% Token Reduction** — More efficient task decomposition saves costs
- **2.8-4.4x Speed Improvement** — Parallel swarm coordination multiplier
- **87 MCP Tools** — Pre-integrated tool ecosystem (vs needing manual setup)
- **Zero-Config Setup** — Automatic MCP server configuration; immediate Claude Code integration[5]

***

## Verifying Your Vector/RAG Problem Is Solved

Before/after memory persistence test:

```bash
# Check memory system is operational
npx claude-flow@alpha memory stats
# Should show: sessions tracked, memory items stored, retrieval stats

# Test semantic memory retrieval
# 1. Give Claude Code a coding task
# 2. Record execution time + token usage
# 3. Give it a similar task 30 minutes later
# Metric: Did execution time decrease? (proves memory recall working)
```

**Red flags to watch:**[1][2]
- Success rate <60% on lite dataset → use mesh mode, increase agents
- Coordination score <75% → agent conflicts, check logs
- Token efficiency <0.7 → not decomposing tasks effectively
- Memory stats show 0 items → persistence isn't working
- Same task slower on second run → memory not providing value

***

## The Data: Why This Matters for Your Use Case

The problem you identified—Claude Code not using vector/RAG memory—isn't unique. claude-flow solves it through:[2][1]

1. **SQLite Memory System** — 12 specialized tables in `.swarm/memory.db` with persistent storage
2. **Cross-session Context** — Hooks system (`session-end --persist-state`) saves state automatically
3. **Semantic Retrieval** — Neural network component learns which memories are relevant (not keyword-based)

The benchmarking system lets you **quantify the improvement** rather than guess whether it's working.

I've saved the full evaluation playbook with specific commands and expected outputs to your workspace file for reference during testing.

## Human

So we have a bunch of repos, how do I know what is 'best' for me?

## Assistant

## The Honest Answer: Start with Option B

Based on your actual situation (Windows 11, CKS system, solo developer, maximize ROI, minimize maintenance), here's what's best **for you specifically**:

***

## Your Real Problem & Solution

**Your stated problem:**
> "Claude Code isn't using our vector/RAG memory bank at all even though it would help a lot."

This is **ultra-specific**. You don't have a generic "I need agents" problem—you have a **Claude Code memory problem**.

**The match:**
- **Option B** (`christian-byrne/claude-code-vector-memory`) solves this exactly
- **1-2 hours to implement**
- **Minimal maintenance**
- **Direct ROI**: Claude Code remembers, executes faster on repeated patterns

***

## Why NOT the Others (For Your Immediate Need)

| Repo | What It Does | Your Situation |
|------|-------------|-----------------|
| **Option A: claude-flow** | Multi-agent orchestration platform | Overkill if you only need memory; 3-5 days to learn a new system |
| **Option C: 610ClaudeSubagents** | Pre-built agent catalog | Complements orchestration, doesn't solve memory problem standalone |

***

## My Recommendation: Three-Path Approach

### **Path 1: Quick Win (Do This Week)**
Install **Option B** → vector memory for Claude Code
- **Time:** 1-2 hours
- **Payoff:** Immediate (Claude Code stops forgetting)
- **Validation:** Test same task type twice, measure speed improvement

### **Path 2: Then Evaluate (1-2 Weeks Later)**
Run benchmark on **Option A** → if multi-agent coordination helps your workflows
- **Time:** 30 minutes to validate with `swarm-bench`
- **Decision point:** Is 2.8-4.4x speed improvement worth learning new system?

### **Path 3: Then Integrate (If Path 2 is Yes)**
Add **Option A + C** → full orchestration with specialized agents
- **Time:** 3-4 more days
- **Payoff:** Enterprise-grade system (but only if justified by Path 2 validation)

***

## Why This Order?

1. **Option B is de-risked** — Directly solves stated problem, low time investment
2. **Option A is optional** — Only pursue if you discover multi-agent coordination would help
3. **Avoid analysis paralysis** — You choose based on real results, not predictions
4. **Fits your priorities** — Solo dev, maximize ROI, minimize maintenance

***

## The Key Insight

You already have:
- ✅ Vector RAG system built
- ✅ 18 MCP repos installed  
- ✅ Semantic search working
- ✅ Intel orchestration established

You're missing **one thing**: Claude Code connecting to that memory.

Option B plugs that gap. Everything else is nice-to-have optimization.

***

**I've saved a full decision framework to your workspace with validation checklists and detailed ROI analysis for each option. Want me to help you set up Option B, or do you want to explore the benchmarking approach for Option A first?**

## Human

How does christian-byrne/claude-code-vector-memory enable claude code to use it?

## Assistant

## How It Works: The Technical Picture

**TL;DR:** MCP (Model Context Protocol) is the bridge. The vector memory system becomes an MCP server that Claude Code queries automatically.

***

## The Architecture

```
Your Claude Sessions  →  Semantic Embeddings  →  MCP Server  →  Claude Code
(stored summaries)      (ChromaDB vector DB)    (listens)      (queries proactively)
```

### Step 1: Setup Registers MCP Server
The `setup.bat` script adds this to your Claude Code config:

```json
{
  "mcpServers": {
    "semantic-memory-search": {
      "command": "python",
      "args": ["-m", "memory_mcp"],
      "env": { "CHROMA_PATH": "~/.claude-memory/.chroma" }
    }
  }
}
```

**This tells Claude Code:** "There's an MCP server that can search semantic memory."

### Step 2: How Claude Code Uses It

When Claude Code starts, it:
1. ✅ Detects the `semantic-memory-search` MCP server
2. ✅ Loads the ChromaDB index (your past session embeddings)
3. ✅ Adds to system prompt: "You can search memories via `/system:semantic-memory-search`"
4. ✅ Claude **proactively queries** before tasks

**Example flow:**

```
You: "Build a React authentication component"
     ↓
Claude thinks: "I should check if I've done auth patterns before"
     ↓
Claude calls: /system:semantic-memory-search "React authentication"
     ↓
MCP Server converts query to embedding, searches ChromaDB
     ↓
Returns: "JWT Auth (0.89 match), OAuth Flow (0.87 match), Login Form (0.85 match)"
     ↓
Claude's response now includes: "Similar to the JWT pattern I built on 12/10...
                                  Let me apply that same approach"
```

***

## Three Access Patterns

| Pattern | How | Who Triggers |
|---------|-----|-------------|
| **Automatic** | Claude proactively queries before tasks | System (Claude itself) |
| **Manual Slash** | You type `/system:semantic-memory-search` | You |
| **CLI Command** | Terminal: `claude-memory-search "query"` | You (before session) |

***

## Why This Is Different From Your Current Setup

**Currently:** Your vector RAG system exists, but Claude Code has to manually ask for it (or you have to tell Claude to ask).

**After:** Claude Code **automatically** searches your past sessions before each task, no manual invocation needed.

***

## How It Fits With Your 18 MCP Repos

**It doesn't conflict.** You already have:
- `cognitive-stack` (reasoning)
- `agi-memory` (general memory)
- `sequential-thinking` (complex logic)
- ... 15 more

Adding `semantic-memory-search` just expands the available tools. Claude calls whichever MCP tool helps most for each task.

***

## Setup Timeline (Windows 11)

| Step | Time |
|------|------|
| Clone repo | 1 min |
| Run `setup.bat` | 3-5 min |
| Add summaries | 1-2 min |
| Index (`reindex.py`) | 2-5 min |
| Restart Claude Code | 1 min |
| Test with query | 5-10 min |
| **Total** | **15-25 min** |

***

## Validation: How to Test It Works

**Test 1:** Manual search from terminal
```bash
claude-memory-search "your past work on authentication"
# Should return ranked results with dates, technologies, relevance scores
```

**Test 2:** In Claude Code session
```
/system:semantic-memory-search "react hooks debugging"
# Should display results
```

**Test 3:** Watch it happen automatically
```
Give Claude Code a task → Watch thinking → Does it mention past sessions?
If YES → Working
```

***

**I've saved the full technical deep-dive to your workspace with data flow diagrams, timeline, and integration examples. Ready to install, or want to understand anything else first?**

## Human

What repos exist or options exist, that uses hooks instead of mcp?  Or hook with mcp?

## Assistant

Perfect. I've mapped out the full landscape of hooks-based and hybrid systems.

## The Complete Picture: Hooks vs MCP

There are **two main architectural approaches** + a hybrid approach:

***

## Hooks-Only Systems (NO External MCP Process)

### **RLabsc/memory** ⭐ Most Proven
**GitHub:** https://github.com/RLabsc/memory

```
SessionStart → Load memories
UserPromptSubmit → Inject context automatically
PostToolUse → Log what happened
SessionEnd → Extract + store new memories
```

**Why this is best for hooks-only:**
- ✅ 105 upvotes on Reddit (production proven)
- ✅ True semantic memory extraction (Claude decides what to keep)
- ✅ Project-organized (separate memories per project)
- ✅ Zero-config: `./install.sh` and done
- ✅ NO external processes (pure hooks)

**Setup:** 5-15 minutes

***

### **arpitnath/super-claude-kit**
**GitHub:** https://github.com/arpitnath/super-claude-kit

```
SessionStart → Captures file state + git status
UserPromptSubmit → Prepends context before requests
```

**Simpler than RLabsc** but less sophisticated memory extraction.

***

## Hybrid Systems (Hooks + MCP Together)

### **adestefa/CCMem** ⭐⭐ Best Hybrid
**GitHub:** https://github.com/adestefa/ccmem

```
Hooks capture → SessionStart, UserPromptSubmit, PostToolUse, SessionEnd
    ↓
Store in SQLite database
    ↓
MCP server provides vector search
    ↓
You can: /system:semantic-memory-search OR use CLI (ccmem search)
```

**Setup:** 10-20 minutes
```bash
# One command:
claude mcp add ccmem -- npx -y @adestefa/ccmem@latest

# Or manual:
git clone https://github.com/adestefa/ccmem && npm install
```

**Why hybrid is best:**
- ✅ Automatic capture via hooks (no manual invocation)
- ✅ Interactive search via MCP (manual when needed)
- ✅ Best of both worlds
- ✅ Integrates with your existing MCP servers cleanly

***

### **CAM (Continuous Architectural Memory)**
Uses **5 hook points** for comprehensive capture:
- SessionStart (load)
- UserPromptSubmit (inject)
- PreToolUse (gather history)
- PostToolUse (log)
- SessionEnd (summarize)

**Status:** Advanced research, likely in development

***

## MCP-Only (Already Covered)

- **christian-byrne/claude-code-vector-memory** - No hooks, pure MCP
- **ruvnet/claude-flow** - Hooks + MCP + full orchestration (overkill for memory alone)

***

## Quick Decision

| Want | Choose | Time | Why |
|------|--------|------|-----|
| **Simplest** | RLabsc/memory (hooks) | 5-15 min | No external process |
| **Best Balance** | CCMem (hybrid) | 10-20 min | Auto + search |
| **Advanced Search** | christian-byrne (MCP) | 15-25 min | Richer queries |
| **Everything** | claude-flow (hooks+MCP+orche) | 3-5 days | Enterprise |

***

## My Recommendation For Your Situation

**Phase 1 (This Week):** Install **RLabsc/memory** (hooks-only)
- Integrates cleanly with your 18 existing MCP repos
- Pure hooks approach (no additional process)
- 15 minutes
- Proven in production
- Test for 1 week

**Phase 2 (If working well):** Optionally add **CCMem** (hybrid)
- Keeps automatic capture from hooks
- Adds interactive search via MCP
- No conflict (both work together)
- 10 minutes to add

**I've saved detailed comparison, installation steps, and hook mechanisms to your workspace.**

Want me to help you set up one of these, or clarify how the hooks integrate with your current setup?
