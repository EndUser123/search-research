# 2026-08-10 - Explain Agentic Skill Graphs

- **Created:** 8/13/2026, 7:40:18 AM
- **Exported:** 8/13/2026, 7:40:20 AM
- **Messages:** 4
- **Source:** browser_extension

---

## #1 · user

What is an agentic skill graph and why would I want one?

## #2 · assistant

An **agentic skill graph** is a way of turning a collection of agent skills from a flat toolbox into a **structured network of capabilities, dependencies, transitions, and evidence requirements**.

In your case, the distinction is roughly:

> 
**Today:** Agent decides, “I think `/review` is appropriate now.”

**Skill graph:** System knows, “Given the current state, these 3 capabilities are applicable; `/review` requires these prerequisites; this output satisfies that prerequisite; after review, these are the permitted next transitions.”

That is potentially quite valuable for the kind of system you have been building.

## 1. Think of it as a map of your agent's capabilities

Imagine something like:

```
                     ┌── research ───────────┐
                     │                       ▼
GOAL → investigate → design → implement → verify → review → complete
          │             │        │          ▲
          │             │        └─ test ───┘
          │             │
          ▼             ▼
       falsify       red-team
          │             │
          └──── reconsider ──────→ design
```

But the nodes aren't merely commands.

A node could describe:

```
skill: review

consumes:
  - implementation
  - requirements
  - verification_evidence

produces:
  - findings
  - verdict
  - residual_risks

requires:
  implementation_exists: true

allowed_next:
  healthy:
    - complete
  findings:
    - implement
  premise_failure:
    - design

evidence:
  - tests
  - diff
  - behavioral_validation
```

Now the system can **reason over the capabilities rather than relying entirely on an LLM remembering that they exist.**

# 2. This attacks one of your recurring problems

You've repeatedly encountered a problem like:

> 
"I built a really good skill, but Claude/Grok doesn't reliably use it."

A skill graph changes the problem.

Instead of hoping the LLM remembers:

```
CLAUDE.md
SKILL.md
SKILL.md
SKILL.md
SKILL.md
...
```

you can have:

```
CURRENT STATE
    ↓
deterministic graph query
    ↓
applicable capabilities
    ↓
LLM chooses among valid candidates
    ↓
skill executes
    ↓
artifact/evidence produced
    ↓
graph state changes
```

That's a fundamentally stronger architecture.

The LLM still exercises judgment, but **it doesn't have to remember the entire operating system.**

# 3. More importantly, the graph can encode *when not to use something*

Suppose the agent is debugging a failure.

A naïve agent might do:

```
problem
 ↓
edit code
 ↓
test
```

Your graph could encode:

```
problem
 ↓
investigate
 ↓
obtain behavioral evidence
 ↓
form hypotheses
 ↓
attempt falsification
 ↓
root cause sufficiently supported?
       │
     NO│      YES
       ▼       ▼
 investigate  implement
                 ↓
               verify
```

Now "don't jump straight into coding" isn't merely prose.

It's a **structural property of the workflow**.

That's an important difference.

# 4. It also addresses skill composition

Suppose you have:

```
/research
/design
/red-team
/go
/review
/improve
/debrief
/wiki
```

These aren't independent commands.

There are relationships such as:

```
research ──supports──> design

design ──authorizes──> implementation

implementation ──requires──> verification

verification ──provides evidence to──> review

review ──may trigger──> implementation

review ──may trigger──> red-team

debrief ──extracts lessons from──> execution

debrief ──proposes knowledge to──> wiki
```

That's already a graph.

Right now, much of that graph exists **implicitly in your prompts and your head**.

Making it explicit lets software operate on it.

# 5. Here's where I think it gets especially interesting for your architecture

You have recently been considering **routing work between reasoning, coding and mechanical model pools**.

The skill graph could sit *above* model routing.

For example:

```
USER REQUEST
     │
     ▼
┌─────────────────┐
│ Capability Graph│
└────────┬────────┘
         │
         ▼
   "investigate"
         │
         ├── needs: repo search
         ├── needs: hypothesis generation
         └── needs: evidence evaluation
                    │
                    ▼
              TASK ROUTER
             /      |       \
       mechanical reasoning coding
          │          │        │
       Ornith       GLM       coding
        etc.        etc.       pool
```

Those are **two different decisions**:

**Skill graph**

> 
What needs to happen?

**Model router**

> 
Who should perform it?

That separation is architecturally clean.

# 6. And Kestra/LangGraph/n8n fit at yet another layer

This connects directly to the question you were asking earlier.

I'd separate the system into approximately:

```
┌──────────────────────────────────────┐
│              USER GOAL               │
└──────────────────┬───────────────────┘
                   ▼
          CAPABILITY / SKILL GRAPH
              "what must happen?"
                   │
                   ▼
            ORCHESTRATION ENGINE
       "how do we execute the graph?"
       LangGraph / Kestra / Python/etc.
                   │
                   ▼
              MODEL ROUTER
              "who does it?"
                   │
        ┌──────────┼───────────┐
        ▼          ▼           ▼
    reasoning    coding    mechanical
      pool        pool         pool
                   │
                   ▼
             TOOL / HARNESS
        Claude Code / Grok / PI
                   │
                   ▼
               EVIDENCE
                   │
                   ▼
            GRAPH TRANSITION
```

This separation could resolve quite a few things that otherwise get mixed together.

# 7. The graph should probably contain **conditions**, not just skills

This is where I'd go beyond a simple "skill dependency graph."

I'd represent nodes like:

```
CAPABILITIES
research
trace-code
generate-hypotheses
falsify
design
implement
test
review
red-team
document
```

And states such as:

```
problem-understood
root-cause-supported
design-approved
implementation-present
tests-passing
behavior-verified
review-healthy
```

Then transitions become explicit:

```
implement
requires:
    problem-understood = true

complete
requires:
    tests-passing = true
    behavior-verified = true
    review-healthy = true
```

Now you are building something closer to an **agentic state machine backed by evidence**.

That's considerably more powerful than a menu of skills.

# 8. It also gives you something you've been trying to achieve with hooks

Consider your hooks.

You're currently using them to enforce things such as:

```
"You cannot stop because required evidence doesn't exist."
```

A graph generalizes this.

Instead of dozens of unrelated hook rules:

```
Hook A
Hook B
Hook C
Hook D
...
```

you potentially have:

```
requested transition:

IMPLEMENTED → COMPLETE

Graph asks:

✓ tests?
✓ behavioral evidence?
✓ review artifact?
✓ correct session?
✓ fresh artifact?
✗ falsification evidence?

Transition denied.
```

The hooks then become **enforcement mechanisms for graph invariants**, rather than independent pieces of policy.

I think that's a much cleaner mental model.

# 9. There is another potentially large benefit: **discoverability**

Suppose the agent reaches:

```
state = implementation failing unexpectedly
```

The graph can answer:

```
Applicable capabilities:

trace-runtime       0.94
inspect-logs        0.91
falsify-assumption  0.88
research-upstream   0.54
rewrite-code        BLOCKED
```

The LLM doesn't have to remember every clever capability you've created.

The graph **surfaces capabilities contextually**.

That directly attacks skill under-utilization.

# 10. But I would NOT build a giant knowledge graph

There's an important failure mode here.

You could very easily create:

```
Neo4j
ontology
RDF
semantic relationships
vector database
skill embeddings
planner
graph neural something...
```

and end up with 10× the complexity without improving agent performance.

I don't think that's where you should start.

Your useful MVP could literally be:

```
skills.yaml
```

containing perhaps:

```
investigate:
  when:
    - root_cause_unknown
  produces:
    - evidence
    - hypotheses

implement:
  requires:
    - problem_understood
  produces:
    - code_change

verify:
  requires:
    - code_change
  produces:
    - verification_evidence

review:
  requires:
    - code_change
    - verification_evidence
  produces:
    - review_verdict

complete:
  requires:
    - verification_evidence
    - healthy_review
```

plus a tiny resolver:

```
current state
      +
skill graph
      ↓
valid next capabilities
```

Then let your orchestrator/model choose from those.

# Why I think you specifically should investigate this

You've been attacking several problems separately:

- 
skills being ignored,

- 
models jumping straight to implementation,

- 
hooks enforcing workflow,

- 
reasoning vs mechanical vs coding routing,

- 
`/go` orchestration,

- 
evidence requirements,

- 
falsification,

- 
reviewer gates,

- 
skill discovery,

- 
LangGraph vs Kestra vs custom Python,

- 
multi-agent execution.

I think there may be a **common abstraction underneath a surprising number of them**:

> 
**Explicit capability graph + evidence-backed state transitions.**

Then:

```
Skill graph       = what can/should happen
State/evidence    = what is currently true
Planner/LLM       = chooses among permissible actions
Router            = chooses the appropriate model
Orchestrator      = executes it
Hooks             = enforce invariants
Artifacts         = prove transitions occurred
```

That is a much more coherent architecture than asking one orchestrator LLM to remember all of those responsibilities.

The critical unknown is whether introducing the graph **actually improves adherence and outcomes enough to justify another control layer**. I would therefore not implement it broadly first. I'd take perhaps 5–10 of your existing `/go` transitions, encode them in a tiny YAML graph/resolver, and run adversarial comparisons against your current prose-driven orchestration. Success would mean measurably fewer skipped capabilities, invalid transitions, and premature completion—not merely that the graph looks architecturally elegant.

That experiment could tell us very quickly whether this is a useful organizing abstraction for your system or merely another layer of machinery.

## #3 · user

Are there repos that already have the system you are proposing?  What would make you change your mind?

## #4 · assistant

Yes. After searching specifically for the architecture we just described, I would **revise my previous recommendation**: I would **not build the skill-graph layer ourselves first**.

There are now several repos/projects that cover surprisingly large parts of it, and one in particular—**`context4ai/agent-graph`**—is close enough to what I independently described that it should become our baseline candidate. [[image]GitHub](https://github.com/context4ai/agent-graph)

## The strongest candidates

| Project | What it does | Fit for us |
| --- | --- | --- |
| context4ai/agent-graph | Evidence/fact-driven workflow graph, legal transitions, gates, resources, recovery, resumability | Very high |
| GraSP | Compiles retrieved skills into typed executable DAGs with preconditions/effects, verification and local repair | Very high conceptually |
| Graph of Skills | Dependency-aware retrieval of the right small subset of SKILL.mds | High, complementary |
| skill-graph | Skill relationships + progressive context disclosure + deterministic resolver | High, but narrower |
| SkillNet | Huge skill ontology, creation/evaluation/composition infrastructure | Medium/high |
| SkillOps | Typed skill contracts + graph-based skill-library health/maintenance | Complementary |
| LangGraph | General stateful workflow runtime | Infrastructure rather than solution |

The important discovery is that these aren't six versions of the same thing. They occupy **different layers**.

# 1. `context4ai/agent-graph` is almost exactly what I proposed

Its README describes Agent Graph as a **work-contract layer for Agent Skills**. The runtime receives externally observable facts and determines:

- 
what action is legal next,

- 
what resources need to be read,

- 
what proves completion,

- 
where execution should resume,

- 
what gates must prevent progression.

It deliberately does **not** invoke an LLM. The agent/harness remains the executor. [[image]GitHub](https://github.com/context4ai/agent-graph)

That separation is almost identical to what I suggested:

```
facts/evidence
     ↓
skill/work graph
     ↓
legal next action
     ↓
agent/model routing
     ↓
execution
     ↓
new evidence
     ↓
graph reevaluation
```

Even more strikingly, it explicitly says progress should be determined by facts rather than remembered conversational state, and supports dependencies, choices, gates, evidence, recovery paths, events/checkpoints, resumability, and route testing. [[image]GitHub](https://github.com/context4ai/agent-graph)

That's extraordinarily aligned with the problems we've been solving around `/go`.

For example, instead of our Stop hook knowing:

```
verification artifact exists
review healthy
session correct
```

Agent Graph could represent:

```
IMPLEMENTED
    │
    ├─ verification.valid = true
    ├─ review.healthy = true
    └─ artifact.session_id = current_session
             ↓
          COMPLETE
```

The hook becomes an **enforcer of the graph contract** rather than the place where the workflow semantics live.

That is a meaningful improvement in architecture.

# 2. GraSP is even closer to the theoretical architecture

This one surprised me.

A Tencent research group published **GraSP: Graph-Structured Skill Compositions for LLM Agents** in April 2026.

The core architecture is:

```
skill retrieval
      ↓
DAG compilation
      ↓
typed dependencies
      ↓
verified execution
      ↓
local failure repair
```

Each skill node contains its schema, arguments, **preconditions, effects, verifier, execution status, confidence and repair budget**. Edges represent state dependencies, data dependencies or ordering constraints. [[image]arXiv](https://arxiv.org/html/2604.17870v1)

That is almost exactly the structure I was describing in the previous answer.

GraSP additionally checks pre/postconditions at **every node** and only invalidates descendants of a failed node instead of replanning the whole execution. [[image]arXiv](https://arxiv.org/html/2604.17870v1)

They report experiments across ALFWorld, ScienceWorld, WebShop and InterCode, with eight model backbones. Their reported result is up to **+19 reward points over the strongest comparison and up to 41% fewer environment steps**. [[image]arXiv](https://arxiv.org/html/2604.17870v1)

So there is now actual experimental evidence for the underlying proposition:

> 
explicit skill composition and verification can outperform flat skill injection/execution.

That increases my confidence in the **concept**, while decreasing my confidence that we should invent our own implementation.

One caveat: I found the paper and architecture, but not a clearly mature official GraSP runtime repo in the search results. So I would treat GraSP primarily as **architectural/evaluation evidence**, not yet as the obvious package to install.

# 3. Graph of Skills solves another part of your problem extremely directly

**`davidliuk/graph-of-skills`** is particularly interesting because it already supports Claude Code through MCP.

It builds a graph from `SKILL.md` files, then uses semantic + lexical retrieval plus graph relationships to return a **bounded dependency-aware skill bundle**. [[image]GitHub](https://github.com/davidliuk/graph-of-skills)

So instead of:

```
Claude sees 70 skills
       ↓
hopefully remembers / selects right ones
```

you get:

```
task
 ↓
Graph of Skills
 ↓
relevant skill seeds
 ↓
dependencies + related capabilities
 ↓
bounded context
 ↓
Claude
```

It exposes MCP operations including skill search, bundle retrieval, graph neighbors, exact skill hydration and incremental indexing. [[image]GitHub](https://github.com/davidliuk/graph-of-skills)

And unlike many theoretical projects, it has actual benchmark results. Across the project's reported SkillsBench and ALFWorld runs, graph-based retrieval produced the highest reward across the tested Claude Sonnet 4.5, MiniMax M2.7 and GPT-5.2 Codex configurations. [[image]GitHub](https://github.com/davidliuk/graph-of-skills)

That speaks directly to your recurring complaint:

> 
"I have spent time making good skills and the agents don't use them properly."

I now think **GoS deserves an actual trial**, not merely inspiration.

# 4. `bryanwhl/skill-graph` solves progressive discovery

This repo is another close match, but its emphasis is different.

It models relations such as:

```
requires
specializes
complements
conflicts_with
supersedes
```

and exposes increasingly deep levels of skill context. The runtime resolves a task into the smallest useful skill subgraph and allows deeper expansion as needed. [[image]GitHub](https://github.com/bryanwhl/skill-graph)

That's particularly relevant to your concern about bloated skills.

Instead of:

```
/load entire 1,100-line /design skill
```

you could potentially have:

```
/design
   ↓
capability card
   ↓
relevant portion
   ↓
specific procedure
   ↓
supporting artifact
```

The current implementation already includes local indexing, deterministic graph resolution, context-depth expansion, conflict detection, token-budget handling, explanations and approval-required remote installation. [[image]GitHub](https://github.com/bryanwhl/skill-graph)

I would regard this as closer to **skill discovery/context engineering** than workflow enforcement.

# 5. SkillNet is worth watching because it is much broader

**SkillNet** was released as open infrastructure for discovering, evaluating, composing and orchestrating agent skills. The associated work describes a unified skill ontology plus evaluation across safety, completeness, executability, maintainability and cost awareness. [[image]GitHub+1](https://github.com/zjunlp/SkillNet?utm_source=chatgpt.com)

It claims a repository exceeding 200,000 skills and experimental gains of roughly 40% in average reward with 30% fewer execution steps across its evaluated environments. [[image]arXiv](https://arxiv.org/abs/2603.04448?utm_source=chatgpt.com)

It's potentially more infrastructure than we need, but it means we shouldn't assume our home-grown `SKILL.md` conventions represent the state of the art anymore.

The ecosystem has moved quickly.

# 6. SkillOps addresses something else we've repeatedly run into

**SkillOps** treats each skill as a typed contract and builds a hierarchical skill ecosystem graph around it.

The contract includes concepts corresponding to preconditions, outputs/effects, actions, verification and failure handling. It then evaluates the skill ecosystem for compatibility, utility, risk and validation problems. [[image]arXiv+1](https://arxiv.org/html/2605.13716v1?utm_source=chatgpt.com)

That's not primarily a runtime planner.

It is more like:

```
             SKILL LIBRARY
                  │
             SkillOps
                  ↓
      duplicates / conflicts
      stale interfaces
      validation problems
      dependency problems
                  ↓
        healthy skill library
```

That potentially belongs alongside `/skill-audit`.

# The architecture I would investigate now

I would **not** immediately choose LangGraph, Kestra or custom Python as the central abstraction.

I'd test something more like:

```
                     USER GOAL
                         │
                         ▼
               Graph of Skills
           "What capabilities matter?"
                         │
                         ▼
                 Agent Graph
         "What is legal/required now?"
                         │
                         ▼
                  TASK ROUTER
              "Who should do it?"
              /       |       \
             /        |        \
        reasoning   coding   mechanical
                         │
                         ▼
                 Claude/Grok/PI
                         │
                         ▼
                  execution
                         │
                         ▼
             observable evidence
                         │
                         └──────→ Agent Graph
```

And potentially later:

```
SkillOps
   ↓
maintains/audits skill library
```

GraSP provides design ideas for **compilation, verification and local recovery** that could inform the integration.

Notice what disappeared:

**LangGraph may not be necessary at all.**

That's an important revision from our earlier discussion.

If Agent Graph provides sufficient state-transition semantics and your existing CLI/harness infrastructure provides execution, introducing LangGraph could just create another orchestration layer.

# What would make me change my mind?

There are several falsifiers. I would explicitly design the experiment around them.

### 1. The graph doesn't improve real skill adherence

This is the biggest one.

Take perhaps 20 representative tasks where you've historically seen:

- 
forgotten skills,

- 
premature implementation,

- 
skipped verification,

- 
missing falsification,

- 
inappropriate completion.

Compare:

```
CURRENT SYSTEM

vs

GoS / Agent Graph enhanced system
```

Measure:

```
required capability invoked?
correct ordering?
invalid transitions?
completion without evidence?
tokens?
wall-clock?
model cost?
successful outcome?
```

If the graph produces no meaningful improvement, **we should abandon it** regardless of architectural attractiveness.

### 2. Strong models make the control layer unnecessary

This is entirely plausible.

Suppose GLM-5.2/Grok/Claude with a dramatically simpler instruction:

```
Inspect available skills.
Select required procedures.
Never claim completion without their evidence requirements.
```

achieves 97–99% adherence.

Then building a graph to go from 98% → 99% may be pointless.

That's why I would compare against a **strong simplified prose baseline**, not just against the messy system we have today.

### 3. Agent Graph can't get trustworthy facts from the harness

This is particularly important for us.

Agent Graph explicitly assumes a host can provide trustworthy observable facts. [[image]GitHub](https://github.com/context4ai/agent-graph)

If:

```
review.passed
tests.passed
session.id
artifact.current
implementation.exists
```

ultimately come from **LLM claims**, then we've accomplished very little.

The path must be:

```
real process / filesystem / test runner
             ↓
       deterministic observer
             ↓
          fact store
             ↓
         Agent Graph
```

not:

```
LLM says "tests passed"
       ↓
Agent Graph accepts true
```

If we can't establish reliable fact producers, I would reject Agent Graph for enforcement.

That's a **blocking prerequisite**, not an implementation detail.

### 4. The graph becomes another giant policy artifact

If we're moving:

```
1,100 lines of SKILL.md
```

into:

```
2,000 lines of graph YAML
```

we have lost.

The target should be substantially smaller structural contracts with procedural details progressively loaded.

Something like:

```
graph = 100 lines
procedures = skills/resources
facts = machine produced
```

not a graphical rewrite of every prompt.

### 5. Graph maintenance starts dominating value

Edges can become stale:

```
/review requires /verify
/design supersedes X
/foo conflicts with /bar
```

So we'd need tests such as:

```
graph consistency
unreachable states
dead nodes
cyclic hard dependencies
missing verifiers
invalid artifact references
```

Agent Graph already exposes some validation/testing mechanisms, which helps. [[image]GitHub](https://github.com/context4ai/agent-graph)

But if maintaining graph metadata becomes substantial ongoing manual work, I'd favor lighter dynamic retrieval.

### 6. GoS retrieval is worse than simple deterministic classification

You don't have thousands of skills.

That's important.

Graph of Skills is explicitly designed for increasingly large skill libraries. Its results are compelling, but our environment may be small enough that:

```
task classifier
    ↓
10 candidate capabilities
```

beats:

```
embeddings
+ lexical retrieval
+ graph ranking
+ hydration
```

So I would **not assume GoS is required** merely because its paper performs well.

Agent Graph may have much higher ROI for us than GoS.

# The falsification experiment I would actually run

Don't refactor `/go`.

Take **one painful workflow**:

```
investigate
   ↓
root-cause evidence
   ↓
implement
   ↓
behavioral verification
   ↓
review
   ↓
complete
```

Encode just that in `context4ai/agent-graph`.

Use actual filesystem/test artifacts as facts.

Then run approximately:

```
20 historical/problem tasks
×
2 conditions

A = current /go
B = Agent Graph governed /go
```

The important acceptance criteria should be something like:

```
B materially reduces:
  skipped prerequisite stages
  unsupported completion claims
  wrong recovery paths

WITHOUT materially worsening:
  successful completion rate
  token cost
  execution complexity
```

And test a third condition if feasible:

```
C = dramatically simplified /go + strong model
```

**C is crucial.**

If C performs as well as B, I'd prefer C.

That prevents us from proving that a complicated graph beats an already-complicated prompt while overlooking the possibility that **both should be deleted**.

## My updated position

My confidence has changed materially.

Previously I was at roughly:

> 
**Build a tiny graph resolver ourselves and see whether the abstraction works.**

After this search, I'm at:

> 
**Do not build the resolver. Evaluate `context4ai/agent-graph` as the work-contract/state-transition layer; evaluate Graph of Skills separately for skill discovery; use GraSP as the architectural/evaluation reference; only add a general orchestrator such as LangGraph if a demonstrated execution requirement remains unmet.**

And I'd put **`context4ai/agent-graph` first**.

Its description could almost have been written from our last several months of `/go`, Stop-gate, evidence, resumability, context-loading and skill-adherence problems. More importantly, it gives us something existing that we can **falsify against real workloads** instead of adding another speculative subsystem.

That is enough new evidence that I would change the direction I recommended one turn ago. [[image]GitHub+2[image]arXiv+2](https://github.com/context4ai/agent-graph)
