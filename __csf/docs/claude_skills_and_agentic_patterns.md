# Agentic AI Conceptual Guide

**Purpose:** Theoretical foundations and design principles for agentic AI systems

**Last Updated:** 2026-02-03

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Design Patterns](#design-patterns)
3. [Architectural Trade-offs](#architectural-trade-offs)
4. [Anti-Patterns](#anti-patterns)
5. [Emerging Best Practices](#emerging-best-practices)
6. [Research Foundations](#research-foundations)

---

## 1. Core Principles

### 1.0 Documentation-Driven Execution (Critical)

**Principle:** Claude Code skills are markdown documents that describe workflows - not code that executes them.

**Rationale:**
- SKILL.md files ARE the handlers, not references to handlers
- Claude interprets markdown and executes tools directly
- No intermediate Python/TypeScript layer needed
- Simpler architecture, fewer failure modes

**Application:**
- Write workflow steps in SKILL.md markdown
- Claude reads and follows the documented workflow
- Tools (TaskCreate, Read, Write, Bash) are called directly
- No separate handler files for simple workflows

**Common Anti-Pattern:**
Creating standalone Python handler files that are never actually executed by Claude. The Skill tool loads SKILL.md, not .py files.

**Evidence:**
- `/task` skill: 200-line SKILL.md that calls TaskList/TaskCreate/TaskUpdate directly
- No task_handler.py needed - deleted during research phase
- See `claude_skills_operational_guide.md` Section 1.5 for comparison

**Sources:**
- [Claude Code Skills: How they work](https://code.claude.com/docs/en/skills)
- Empirical research: `/task` skill implementation (2026-02-03)

### 1.1 Simplicity Over Complexity

**Principle:** Simple control loops outperform multi-agent systems

**Rationale:**
- Fewer failure modes
- Easier debugging
- More predictable behavior
- Lower cognitive overhead

**Application:**
- Prefer linear workflows over orchestration frameworks
- Use direct tool calls over agent hierarchies
- Choose explicit routing over emergent behavior

**Sources:**
- [Claude Code: Best practices for agentic coding](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Architect's Guide to Agentic Design Patterns](https://medium.com/data-science-collective/architects-guide-to-agentic-design-patterns-the-next-10-patterns-for-production-ai-9ed0b0f5a5c3)

### 1.2 Low-Level Tool Preference

**Principle:** Use fundamental tools (Bash, Read, Write) over specialized frameworks

**Rationale:**
- Universal availability
- Predictable behavior
- No framework lock-in
- Easier debugging

**Application:**
- Bash for shell operations (not custom subprocess wrappers)
- Read/Write for file operations (not filesystem abstractions)
- Direct function calls (not middleware layers)

### 1.3 Context Engineering

**Principle:** Context management is more important than algorithm sophistication

**Rationale:**
- AI models are context-limited
- Relevant information improves decisions
- Noise degrades performance

**Application:**
- CLAUDE.md files for project memory
- CKS for pattern storage
- Targeted context injection
- Session context tracking

### 1.4 Plan-Execute Workflow

**Principle:** Separate planning from execution

**Rationale:**
- Clearer mental models
- Easier verification
- Better error recovery
- Documentable decisions

**Application:**
- `/plan` for design phase
- `/tdd` for implementation
- Explicit checkpoints
- Decision documentation

---

## 2. Design Patterns

### 2.1 Routing Pattern

**Definition:** Single entry point classifies intent and dispatches to specialized implementations

**Components:**
1. **Intent Classifier:** Analyzes query to determine variant
2. **Router:** Maps classification to implementation
3. **Implementations:** Specialized handlers for each case

**Variants:**
- **Skill Dispatch:** Router calls `Skill()` tool with variant name
- **Template Inclusion:** Router reads and includes template content
- **Function Dispatch:** Router calls specific function/module

**When to Use:**
- Multiple specialized workflows under one interface
- User should not need to know about variants
- Variants share common structure

**Sources:**
- [Master ALL 20 Agentic AI Design Patterns](https://www.youtube.com/watch?v=e2zIr_2JMbE)

### 2.2 Reflection Pattern

**Definition:** Agent evaluates its own output and self-corrects

**Components:**
1. **Execute:** Generate initial output
2. **Validate:** Check against criteria
3. **Reflect:** Identify issues
4. **Correct:** Refine output
5. **Repeat:** Until validation passes

**When to Use:**
- Quality-critical outputs
- Well-defined quality criteria
- Cost of error is high

**Implementation:**
- PostToolUse hooks for validation
- Template-based self-checklists
- Iterative refinement loops

**Sources:**
- [5 Agentic AI Design Patterns Explained](https://www.youtube.com/watch?v=5wKT4rO86kw)

### 2.3 Prompt Chaining

**Definition:** Break complex tasks into sequence of simpler prompts

**Components:**
1. **Chain Definition:** Ordered list of steps
2. **State Passing:** Output of step N becomes input to step N+1
3. **Error Handling:** Fail-fast vs. continue-on-error

**When to Use:**
- Complex multi-stage workflows
- Each stage has clear inputs/outputs
- Stages can be independently validated

**Anti-Pattern:** Deep nesting (>3 levels) suggests need for refactoring

### 2.4 Tool Use Pattern

**Definition:** Agent delegates specialized tasks to external tools

**Components:**
1. **Tool Selection:** Choose appropriate tool for task
2. **Invocation:** Call tool with parameters
3. **Result Processing:** Incorporate tool output
4. **Error Recovery:** Handle tool failures

**When to Use:**
- Task requires external capability
- Tool is more reliable/efficient than AI
- Clear input/output contract

**Examples:**
- Bash for shell commands
- Read/Write for file operations
- Search for codebase queries
- Specialized MCP tools

### 2.5 Planning Pattern

**Definition:** Generate structured plan before executing

**Components:**
1. **Problem Analysis:** Understand requirements
2. **Plan Generation:** Create structured approach
3. **Plan Review:** Validate plan quality
4. **Execution:** Follow plan steps
5. **Adaptation:** Adjust plan based on feedback

**When to Use:**
- Non-trivial implementations
- High-risk changes
- Multi-step workflows
- When reversibility > 1.5

**Sources:**
- [Agentic AI Design Patterns Introduction](https://www.youtube.com/watch?v=MrD9tCNpOvU)

### 2.6 Memory Pattern

**Definition:** Agent maintains and retrieves information across sessions

**Components:**
1. **Storage:** Persistent memory (CKS, files, database)
2. **Retrieval:** Query based on relevance
3. **Update:** Incorporate new information
4. **Forgetting:** Prune/expire old information

**When to Use:**
- Recurring patterns in workflow
- Need to learn from experience
- Cross-session continuity required

**Implementation:**
- CKS for pattern/memory storage
- Vector search for semantic retrieval
- FAISS for efficient similarity search

### 2.7 Multi-Agent Collaboration

**Definition:** Multiple specialized agents work together on complex tasks

**Components:**
1. **Agent Definition:** Specialized capabilities per agent
2. **Communication:** Message passing between agents
3. **Coordination:** Orchestrator or peer-to-peer
4. **Conflict Resolution:** Handle disagreements

**When to Use:**
- Task spans multiple domains
- Requires parallel processing
- Specialized expertise needed

**Anti-Pattern:** Don't use for tasks that single agent can handle

### 2.8 Parallelization Pattern

**Definition:** Execute multiple independent tasks simultaneously

**Components:**
1. **Task Decomposition:** Split into independent subtasks
2. **Parallel Execution:** Run subtasks concurrently
3. **Result Aggregation:** Combine results
4. **Error Handling:** Handle partial failures

**When to Use:**
- Subtasks are independent
- Performance is critical
- Resources allow parallel execution

---

## 3. Architectural Trade-offs

### 3.1 Resource Templates vs. Skill Dispatch

| Dimension | Resource Templates | Skill Dispatch |
|-----------|-------------------|----------------|
| **Simplicity** | High (single skill) | Medium (multiple files) |
| **Discovery** | Clean (one entry) | Noisy (all visible) |
| **Testing** | Manual (via router) | Independent |
| **Modularity** | Low (coupled) | High (decoupled) |
| **Flexibility** | Medium | High |

**Recommendation:** Use resource templates when:
- Single user-facing entry point is priority
- Variants are rarely invoked directly
- Shared workflow structure

Use skill dispatch when:
- Independent testing is required
- Variants may be invoked separately
- Different teams maintain different variants

### 3.2 Monolithic vs. Modular Skills

| Dimension | Monolithic | Modular |
|-----------|------------|----------|
| **Development Speed** | Fast (initially) | Slower (setup) |
| **Maintenance** | Difficult | Easier |
| **Reusability** | Low | High |
| **Complexity** | Hidden | Explicit |
| **Testing** | Integration | Unit |

**Recommendation:** Start monolithic, refactor modular when:
- Skill exceeds 500 lines
- Variants emerge
- Multiple developers involved
- Testing becomes difficult

### 3.3 Centralized vs. Distributed Routing

| Dimension | Centralized Router | Distributed Discovery |
|-----------|-------------------|----------------------|
| **Control** | High | Low |
| **Simplicity** | High (for users) | Low |
| **Flexibility** | Low | High |
| **Scalability** | Medium | High |

**Recommendation:** Centralized routing for:
- User-facing interfaces
- Coherent user experience
- Controlled complexity

Distributed discovery for:
- Developer tools
- Extensibility needed
- Ecosystem growth

---

## 4. Anti-Patterns

### 4.1 Over-Orchestration

**Pattern:** Complex multi-agent systems for simple tasks

**Symptoms:**
- More agents than tasks
- Agents calling other agents
- Hard to trace execution

**Solution:** Simplify to single agent with direct tool use

**Sources:**
- [Claude Code Best Practices - Simplicity Principle](https://www.anthropic.com/engineering/claude-code-best-practices)

### 4.2 Premature Abstraction

**Pattern:** Creating frameworks before understanding the problem

**Symptoms:**
- Generic interfaces for specific problems
- Configuration over code
- Layers of indirection

**Solution:** Build concrete solution first, abstract later if needed

### 4.3 Enterprise Patterns in Solo Dev

**Pattern:** Using enterprise-scale patterns for single-developer projects

**Symptoms:**
- CI/CD for one person
- Approval workflows
- Multi-region deployment
- Service meshes

**Solution:** Remove coordination overhead, keep it simple

**Sources:**
- [Solo Dev Guidelines](P:\.claude\skills\slc\SKILL.md)

### 4.4 Context Overload

**Pattern:** Including too much information in context

**Symptoms:**
- Token limits exceeded
- Response quality degraded
- Slow responses

**Solution:** Targeted context injection, relevance filtering

### 4.5 Standalone Handler Anti-Pattern

**Pattern:** Creating separate Python handler files for Claude Code skills

**Symptoms:**
- `skill_handler.py` files that Claude never executes
- Unit tests for handler files that don't validate skill behavior
- Confusion about "how to invoke the handler"
- Layer of indirection that provides no value

**Root Cause:** Misunderstanding that Claude Code skills are documentation-driven, not code-driven.

**Example of Wrong Pattern:**
```python
# task_handler.py - This file is NEVER called by Claude
def handle_add(subject):
    return TaskCreate(subject=subject)

def handle_list():
    return TaskList()
```

**Correct Pattern:**
```markdown
# /task - Task Orchestration (SKILL.md)

## Sub-Command: add
1. Parse subject from arguments
2. Call TaskCreate(subject="...", status="pending")
3. Return confirmation

## Sub-Command: list
1. Call TaskList()
2. Format as #<id> [<status>] <subject>
```

**Solution:**
- Delete standalone handler files
- Write complete workflow in SKILL.md
- Trust Claude to follow documented steps
- Only use external code for genuine complexity (APIs, computation)

**Evidence:**
- `/task` skill: Originally had handler.py, deleted after research
- Now works perfectly with SKILL.md alone
- See operational guide Section 1.5 for detailed comparison

### 4.6 Magical Disambiguation

**Pattern:** Assuming AI will figure out ambiguous requests

**Symptoms:**
- No clarification questions
- Wrong interpretations
- User frustration

**Solution:** Explicit classification, ask when unclear

---

## 5. Emerging Best Practices

### 5.1 Intent Classification First

Always classify user intent before taking action:
1. What does user want?
2. What variant is appropriate?
3. Do I have enough information?
4. Should I ask for clarification?

### 5.2 Fail Fast

Surface problems immediately:
- Don't mask errors
- Don't gracefully degrade
- Don't hide failures
- Validate early and explicitly

### 5.3 Evidence-Based Claims

Require evidence for assertions:
- Tier 1: Execution artifacts, logs
- Tier 2: Documentation, specs
- Tier 3: Static analysis
- Tier 4: Comments (unverified)

**Sources:**
- [CLAUDE.md Evidence Tiers](P:\.claude\CLAUDE.md)

### 5.4 Progressive Disclosure

Show simple first, complex on request:
1. Default: Fast/simple path
2. User requests depth: Switch to detailed path
3. User asks for alternatives: Show options

### 5.5 State Where It Matters

Track state for:
- Multi-phase workflows
- Cross-terminal coordination
- Recovery from interruption

Avoid state for:
- Single-shot operations
- Stateless queries
- Independent tasks

### 5.6 Documentation-First Skill Development

**Always start with SKILL.md only:**
1. Write complete workflow in markdown
2. Test by invoking the skill
3. Only consider code if workflow cannot be expressed

**Don't create handler files until:**
- You've verified SKILL.md is insufficient
- External APIs require complex integration
- Independent testing is genuinely needed

**Evidence:** `/task` skill works perfectly with 200-line SKILL.md, no Python code needed.

---

## 6. Research Foundations

### 6.1 Academic Research

**Agent Design Pattern Catalogue**
- Comprehensive taxonomy of agent patterns
- Formal analysis of trade-offs
- [arxiv.org/html/2405.10467v2](https://arxiv.org/html/2405.10467v2)

**Skill Machines: Modular AI Agents**
- Theory of skill composition
- Transfer learning between skills
- [emergentmind.com/topics/skill-machines](https://www.emergentmind.com/topics/skill-machines)

### 6.2 Industry Practice

**Google Cloud Agentic AI Patterns**
- Production deployment patterns
- Scaling considerations
- [cloud.google.com/architecture/choose-design-pattern-agentic-ai-system](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system)

**AWS Agentic AI Patterns**
- Enterprise deployment
- Integration patterns
- [docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/agentic-ai-patterns.pdf](https://docs.aws.amazon.com/pdfs/prescriptive-guidance/latest/agentic-ai-patterns/agentic-ai-patterns.pdf)

### 6.3 Community Knowledge

**Reddit: Deconstructing Agentic AI Prompts**
- Community-driven pattern discovery
- Real-world examples
- [reddit.com/r/LocalLLaMA/comments/1jwormp](https://www.reddit.com/r/LocalLLaMA/comments/1jwormp/deconstructing_agentic_ai_prompts_some_patterns_i/)

### 6.4 Video Resources

**20 Agentic AI Design Patterns (Complete Course)**
- Comprehensive coverage
- Practical examples
- [youtube.com/watch?v=e2zIr_2JMbE](https://www.youtube.com/watch?v=e2zIr_2JMbE)

**Prompt Management 101**
- Template organization
- Conditional rendering
- [youtube.com/watch?v=Qddc_DNo9qY](https://www.youtube.com/watch?v=Qddc_DNo9qY)

---

## 7. Design Decision Framework

When designing agentic AI skills, ask:

1. **Complexity:** Can this be done without agents?
   - Yes → Don't use agents
   - No → Continue

2. **Simplicity:** Can this be done with a single agent?
   - Yes → Use single agent
   - No → Use minimal multi-agent

3. **Routing:** Do users need to know about variants?
   - No → Use centralized routing
   - Yes → Use separate entries

4. **State:** Is state required?
   - No → Stateless design
   - Yes → Minimal state, explicit lifecycle

5. **Testing:** How will this be validated?
   - Unit tests → Modular design
   - Integration tests → End-to-end focus
   - Manual → Documentation critical

---

## 8. Future Directions

### 8.1 Emerging Patterns

- **Hierarchical Agents:** Layered specialization
- **Self-Improving Agents:** Agents that modify their own prompts
- **Collaborative Filtering:** Agents learning from user feedback
- **Federated Agents:** Cross-system coordination

### 8.2 Open Questions

- How to optimally decompose tasks?
- When do multi-agent systems justify complexity?
- How to measure agent effectiveness?
- What's the right abstraction level for skills?

### 8.3 Research Needs

- Quantitative comparison of patterns
- Best practices for agent composition
- Standard interfaces for agent communication
- Metrics for agent quality

### 8.4 Academic Research Sources

**Papers:**
- "ReAct: Synergizing Reasoning and Acting in Language Models" - arXiv:2210.03629
- "Reflexion: Language Agents with Verbal Reinforcement Learning" - arXiv:2303.11366
- "MemGPT: Towards LLMs as Operating Systems" - arXiv:2310.08560
- "Toolformer: Language Models Can Teach Themselves to Use Tools" - arXiv:2302.04761
- "AgentBench: Evaluating LLMs as Agents" - arXiv:2308.03688
- "Agent Design Pattern Catalogue" - arXiv:2405.10467v2 (Taxonomy of agent patterns)

### 8.5 Industry Documentation

**Official Resources:**
| Resource | URL |
|----------|-----|
| Anthropic Agent Design | docs.anthropic.com |
| Google Cloud Agentic AI | cloud.google.com/architecture/choose-design-pattern-agentic-ai-system |
| LangChain | python.langchain.com |
| LangGraph | langchain-ai.github.io/langgraph |
| OpenAI Function Calling | platform.openai.com/docs/guides/function-calling |
| Semantic Kernel | learn.microsoft.com/en-us/semantic-kernel |
| AWS Agentic AI Patterns | docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns |

### 8.6 Open Source Projects

| Project | Purpose | URL |
|---------|---------|-----|
| LangChain | LLM application framework | github.com/langchain-ai/langchain |
| Semantic Kernel | Microsoft AI orchestration | github.com/microsoft/semantic-kernel |
| BabyAGI | Autonomous task agent | github.com/yoheinakajima/babyagi |
| AutoGPT | Autonomous AI agent | github.com/Significant-Gravitas/AutoGPT |
| CrewAI | Multi-agent framework | github.com/joaomdmoura/crewAI |

---
- [Claude Code: Best practices for agentic coding](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Best Practices for Claude Code - Official Docs](https://code.claude.com/docs/en/best-practices)
- [Master ALL 20 Agentic AI Design Patterns](https://www.youtube.com/watch?v=e2zIr_2JMbE)
- [Architect's Guide to Agentic Design Patterns](https://medium.com/data-science-collective/architects-guide-to-agentic-design-patterns-the-next-10-patterns-for-production-ai-9ed0b0f5a5c3)
- [Prompt Management 101](https://www.youtube.com/watch?v=Qddc_DNo9qY)
- [Agent Design Pattern Catalogue](https://arxiv.org/html/2405.10467v2)
- [Skill Machines: Modular AI Agents](https://www.emergentmind.com/topics/skill-machines)
