# Specification: Multi-Phase Brainstorming Architecture (MPBA)

**Project**: Brainstorming Architecture Design
**TSK**: TSK-251224-2352-Brainstorm-5276
**Date**: 2025-12-24
**Status**: Draft

---

## 1. Executive Summary

### Problem Statement
Current LLM-based brainstorming lacks:
- **Systematic exploration**: Ideas are generated linearly without divergent thinking
- **Quality control**: No adversarial debate to challenge assumptions
- **Context persistence**: No learning from previous brainstorming sessions
- **Multi-perspective analysis**: Single-perspective generation limits creativity

### Solution
Multi-Phase Brainstorming Architecture (MPBA) - A systematic, research-backed approach combining:
1. **Divergent Thinking**: Tree-of-Thought exploration with multiple agent personas
2. **Adversarial Debate**: Multi-agent discussion to refine and challenge ideas
3. **Convergent Synthesis**: Rank and synthesize best ideas using evidence-based criteria

### Success Criteria
- **Idea Diversity**: +40% vs single-agent baseline (persona-based collaboration research)
- **Quality Improvement**: 47% reduction in hallucinations (adversarial debate research)
- **Creativity Score**: 2.3x improvement over Chain-of-Thought (Tree-of-Thought research)
- **Pattern Learning**: 71.4% cache hit rate for repeated queries (CO1 research)

---

## 2. Functional Requirements

### 2.1 Core Workflow

#### REQ-2.1.1: Three-Phase Orchestration
The system MUST implement a three-phase workflow:

**Phase 1: Divergent Thinking**
- Spawn N agents with diverse personas (Expert, Critic, Innovator, Synthesizer, Pragmatist)
- Each agent uses Tree-of-Thought reasoning (5 branches minimum)
- Generate 20-30 raw ideas without filtering
- Duration: 60s maximum

**Phase 2: Discussion & Debate**
- Group similar ideas using clustering
- For each cluster:
  - Expert agent provides pro arguments
  - Critic agent provides con arguments
  - Innovator agent provides unconventional angles
  - Judge agent evaluates and scores (0-100)
- Adversarial debate: 3 rounds of "tit for tat" arguments
- Voting mechanism for multi-agent consensus
- Duration: 90s maximum

**Phase 3: Convergence & Synthesis**
- Prune ideas with score < 50
- Synthesizer agent combines complementary ideas
- Pragmatist agent evaluates implementation feasibility
- Rank by: Novelty × Feasibility × Impact
- Return top 5-10 refined ideas
- Duration: 30s maximum

#### REQ-2.1.2: Parallel Agent Execution
The system MUST support parallel agent execution:
- Agents operate concurrently using asyncio
- Each agent has isolated memory and context
- Central orchestrator coordinates communication
- Timeout protection per agent (15s per operation)

### 2.2 Agent System

#### REQ-2.2.1: Persona-Based Agents
The system MUST implement 5 distinct agent personas:

**Expert Agent**
- Role: Domain knowledge, technical depth
- Reasoning: Chain-of-Thought (sequential)
- Output: Detailed, evidence-backed ideas

**Critic Agent**
- Role: Devil's advocate, finds flaws
- Reasoning: Adversarial (challenges assumptions)
- Output: Potential issues and weaknesses

**Innovator Agent**
- Role: Creative, unconventional thinking
- Reasoning: Tree-of-Thought (exploratory)
- Output: Novel, unexpected ideas

**Synthesizer Agent**
- Role: Integrates disparate concepts
- Reasoning: Graph-of-Thought (relationships)
- Output: Combined, hybrid ideas

**Pragmatist Agent**
- Role: Implementation-focused
- Reasoning: ReAct (reasoning + acting)
- Output: Practical, actionable ideas

#### REQ-2.2.2: Agent Communication
Agents MUST communicate through:
- Structured message passing (Pydantic models)
- Redis pub/sub for broadcast messages
- Direct messaging for 1:1 communication
- Context isolation (no shared state)

### 2.3 Reasoning Strategies

#### REQ-2.3.1: Reasoning Selector
The system MUST automatically select optimal reasoning strategy:

| Problem Complexity | Strategy | Branching Factor | Timeout |
|-------------------|----------|------------------|---------|
| Low (< 3) | Chain-of-Thought | N/A | 10s |
| Medium (3-7) | Tree-of-Thought | 3-5 branches | 30s |
| High (> 7) | Graph-of-Thought | Full exploration | 60s |

#### REQ-2.3.2: Tree-of-Thought Implementation
ToT reasoning MUST include:
- Generate initial thought branches (5 minimum)
- Self-evaluate each branch (score 0-100)
- Expand top 3 branches
- Backtrack from dead ends (score < 30)
- Return best path

#### REQ-2.3.3: Graph-of-Thought Implementation
GoT reasoning MUST include:
- Model reasoning as graph structure
- Support cycles and cross-connections
- Multi-source reasoning synthesis
- Cycle detection to prevent infinite loops

### 2.4 Memory & Knowledge Integration

#### REQ-2.4.1: Three-Layer Memory Architecture
The system MUST implement:

**L1: Session Memory (In-Memory)**
- Scope: Current brainstorm session
- Lifetime: Session duration
- Capacity: 1000 ideas maximum
- Eviction: LRU (Least Recently Used)

**L2: Disk Cache (SQLite)**
- Scope: Recent brainstorms
- Lifetime: 72 hours
- Capacity: 10,000 ideas
- Eviction: Time-based (72h TTL)

**L3: CKS Integration (Persistent)**
- Scope: All brainstorms (persistent knowledge)
- Lifetime: Permanent
- Storage: Vector-based semantic search
- Ingestion: Automatic pattern learning

#### REQ-2.4.2: CKS Integration
CKS integration MUST provide:
- Store successful brainstorming patterns
- Retrieve past similar brainstorms (semantic search)
- Learn user preferences (idea style, detail level)
- Cache frequently used reasoning paths

#### REQ-2.4.3: MCP Memory Servers
The system MAY integrate with MCP memory servers:
- `memories-off`: Continuous learning from conversations
- `memory-mcp-service`: Context persistence across sessions
- `Like-I-Said`: 27+ tools for memory management

### 2.5 Quality Assurance

#### REQ-2.5.1: Quality Gates
All brainstorming sessions MUST satisfy:
- Minimum 5 ideas per session
- Minimum 60/100 average quality score
- Maximum 180s total execution time
- Maximum 1000 ideas in memory (auto-prune)

#### REQ-2.5.2: Failure Handling
The system MUST handle:
- LLM timeout: Fallback to simpler reasoning (ToT → CoT)
- Agent failure: Remove failed agent, continue with rest
- CKS unavailable: Use L1/L2 cache only
- Memory overflow: Prune oldest ideas, keep top 50 by score

---

## 3. Non-Functional Requirements

### 3.1 Performance

#### REQ-3.1.1: Response Time
| Operation | Target | Maximum |
|-----------|--------|----------|
| Simple brainstorm (CoT) | 10s | 30s |
| Medium brainstorm (ToT) | 30s | 90s |
| Complex brainstorm (GoT) | 60s | 180s |
| CKS query | 2s | 5s |

#### REQ-3.1.2: Throughput
- Support 10 concurrent brainstorming sessions
- Handle 100 ideas per second processing
- Sub-100ms agent message latency

### 3.2 Scalability

#### REQ-3.2.1: Horizontal Scaling
- Stateless agent design (no shared state)
- Redis for distributed coordination
- CKS for shared knowledge base
- Load balancer support

#### REQ-3.2.2: Vertical Scaling
- GPU acceleration for Tree-of-Thought (20x speedup target)
- Multi-core CPU utilization (asyncio)
- Memory optimization (<4GB peak for complex sessions)

### 3.3 Reliability

#### REQ-3.3.1: Availability
- 99.5% uptime target
- Graceful degradation on component failure
- Automatic retry with exponential backoff
- Circuit breaker for LLM providers

#### REQ-3.3.2: Data Integrity
- ACID transactions for CKS writes
- Atomic multi-agent operations
- Idempotent message processing
- Data validation at all boundaries

### 3.4 Security

#### REQ-3.4.1: Input Validation
- Sanitize all user prompts
- Validate reasoning strategy parameters
- Enforce resource limits (memory, CPU, time)
- Prevent prompt injection attacks

#### REQ-3.4.2: Access Control
- Role-based access (RBAC)
- Agent capability security levels
- Audit logging for all operations
- PII redaction from stored ideas

---

## 4. Technical Architecture

### 4.1 Technology Stack

```
Language: Python 3.14+
Async Framework: asyncio
LLM Integration: DGATE (OpenRouter/Gemini/Groq routing)
Memory:
  - L1: Python dicts (in-memory)
  - L2: SQLite + disk cache
  - L3: CKS via MCP client
Message Broker: Redis pub/sub
Data Models: Pydantic v2
CLI: Click / Typer
Testing: pytest + pytest-asyncio
```

### 4.2 File Structure

```
__csf.nip/src/brainstorm/
├── __init__.py
├── orchestrator.py           # Main coordinator
├── agents/
│   ├── __init__.py
│   ├── base.py              # Abstract Agent class
│   ├── expert.py
│   ├── critic.py
│   ├── innovator.py
│   ├── synthesizer.py
│   └── pragmatist.py
├── reasoning/
│   ├── __init__.py
│   ├── base.py              # Abstract ReasoningStrategy
│   ├── chain_of_thought.py
│   ├── tree_of_thought.py
│   └── graph_of_thought.py
├── debate/
│   ├── __init__.py
│   ├── arena.py             # Debate coordination
│   ├── judge.py             # Judge agent
│   └── voting.py            # Consensus mechanisms
├── memory/
│   ├── __init__.py
│   ├── session.py           # L1 cache
│   ├── disk_cache.py        # L2 cache
│   └── cks_integration.py   # L3 CKS client
├── models/
│   ├── __init__.py
│   ├── idea.py              # Idea data model
│   ├── evaluation.py        # Evaluation criteria
│   └── brainstorm_result.py # Result structure
└── prompts/
    ├── personas.md          # Persona system prompts
    └── reasoning_templates.md
```

### 4.3 Data Models

```python
class Idea(BaseModel):
    id: str
    content: str
    persona: str
    reasoning_path: List[str]
    score: float = 0.0
    metadata: Dict[str, Any] = {}

class Evaluation(BaseModel):
    idea_id: str
    novelty_score: float  # 0-100
    feasibility_score: float  # 0-100
    impact_score: float  # 0-100
    overall_score: float  # 0-100
    arguments_pro: List[str]
    arguments_con: List[str]

class BrainstormResult(BaseModel):
    session_id: str
    prompt: str
    phase_1_raw: List[Idea]
    phase_2_refined: List[Idea]
    phase_3_final: List[Idea]
    execution_time: float
    quality_score: float
```

---

## 5. Testing Strategy (TDD)

### 5.1 Test Coverage

| Component | Coverage Target | Test Type |
|-----------|----------------|-----------|
| Agent base classes | 100% | Unit |
| Reasoning strategies | 95%+ | Unit + Integration |
| Orchestrator | 90%+ | Integration |
| Debate framework | 90%+ | Integration |
| Memory system | 95%+ | Unit + Integration |
| CKS integration | 80%+ | Integration (external) |
| CLI | 85%+ | End-to-end |

### 5.2 Test Structure

```
__csf.nip/tests/brainstorm/
├── test_agents/
│   ├── test_base_agent.py
│   ├── test_expert_agent.py
│   └── test_critic_agent.py
├── test_reasoning/
│   ├── test_chain_of_thought.py
│   ├── test_tree_of_thought.py
│   └── test_graph_of_thought.py
├── test_orchestrator.py
├── test_debate/
│   ├── test_arena.py
│   └── test_judge.py
├── test_memory/
│   ├── test_session_cache.py
│   ├── test_disk_cache.py
│   └── test_cks_integration.py
└── test_integration/
    └── test_full_workflow.py
```

### 5.3 Test Examples

```python
# test_tree_of_thought.py
@pytest.mark.asyncio
async def test_tot_generates_five_branches():
    strategy = TreeOfThoughtStrategy()
    result = await strategy.reason("Solve: 2 + 2")
    assert len(result.branches) >= 5

@pytest.mark.asyncio
async def test_tot_self_evaluation():
    strategy = TreeOfThoughtStrategy()
    result = await strategy.reason("Design a coffee shop")
    assert all(0 <= b.score <= 100 for b in result.branches)

# test_arena.py
@pytest.mark.asyncio
async def test_debate_three_rounds():
    arena = DebateArena()
    idea = Idea(id="1", content="Test idea")
    result = await arena.debate([idea])
    assert result.rounds == 3
```

---

## 6. Implementation Phases

### Phase 1: MVP (Week 1)
**Deliverables**:
- Basic orchestrator (3 phases, no debate)
- 3 agent personas (Expert, Critic, Innovator)
- Chain-of-Thought reasoning only
- L1 memory (session only)
- Core tests (60% coverage)

**Success Criteria**:
- Generate 5+ ideas per session
- Complete in < 60s
- All tests passing

### Phase 2: Enhanced Reasoning (Week 2)
**Deliverables**:
- Tree-of-Thought implementation
- Self-evaluation at each node
- Backtracking mechanism
- L2 disk cache
- Extended tests (75% coverage)

**Success Criteria**:
- ToT shows 2x creativity vs CoT
- Cache hit rate > 50%
- Complete in < 90s

### Phase 3: Multi-Agent Debate (Week 3)
**Deliverables**:
- Adversarial debate arena
- Judge agent
- Voting mechanism
- 5 total personas
- Full test coverage (90%+)

**Success Criteria**:
- 47% reduction in hallucinations
- Quality score improvement 40%+
- Complete in < 180s

### Phase 4: CKS Integration (Week 4)
**Deliverables**:
- MCP client for CKS
- Pattern learning
- Memory servers integration
- Persistent knowledge base
- Integration tests

**Success Criteria**:
- 71.4% cache hit rate
- Successful CKS ingest
- Learn user preferences

### Phase 5: Production (Week 5)
**Deliverables**:
- Performance optimization
- Error handling & fallbacks
- CLI integration
- Documentation
- Monitoring & observability

**Success Criteria**:
- <5s simple, <30s medium, <60s complex
- 99.5% availability
- Full documentation

---

## 7. Dependencies & Constraints

### 7.1 External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.14+ | Core runtime |
| DGATE | Latest | LLM routing |
| CKS | Latest | Knowledge persistence |
| Redis | 7.0+ | Message broker |
| Pydantic | 2.0+ | Data validation |

### 7.2 Constraints

- **Maximum execution time**: 180s per session
- **Maximum memory usage**: 4GB peak
- **Maximum agents per session**: 10
- **Maximum ideas in memory**: 1000 (auto-prune)
- **CKS dependency**: Graceful degradation if unavailable

---

## 8. Success Metrics

### 8.1 Quantitative Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Idea diversity | 1.0x | 1.4x | Unique idea ratio |
| Hallucination rate | 15% | 8% | Factual validation |
| Creativity score | 50/100 | 70/100 | Human evaluation |
| Cache hit rate | 0% | 71.4% | Repeated queries |
| Execution time | N/A | <180s | Time measurement |
| Test coverage | 0% | 90%+ | pytest --cov |

### 8.2 Qualitative Metrics

- User satisfaction: 85%+ positive feedback
- Idea novelty: Expert panel rating
- Implementation feasibility: Developer review
- System reliability: Error rate < 0.5%

---

## 9. Risks & Mitigations

### 9.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM timeout | High | Medium | Fallback to simpler reasoning |
| Memory overflow | High | Low | Auto-pruning, LRU eviction |
| CKS unavailable | Medium | Low | L1/L2 cache fallback |
| Agent coordination failure | Medium | Medium | Timeout protection, retry logic |

### 9.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| High LLM costs | High | Medium | Caching, prompt optimization |
| Poor adoption | Medium | Low | User testing, iterative improvement |
| Complexity overload | High | Medium | Phased rollout, documentation |

---

## 10. Open Questions

1. **CKS MCP Protocol**: Should we use existing MCP memory servers or build custom integration?
2. **Persona Configuration**: Should personas be hardcoded or configurable via YAML?
3. **Parallelism Strategy**: Should we use multiprocessing or asyncio for agent parallelization?
4. **Cost Monitoring**: How do we track and optimize LLM API costs per session?

---

## 11. References

### Research Papers
1. "Tree of Thoughts: Deliberate Problem Solving with Large Language Models" (NeurIPS 2023)
2. "Persona-based Multi-Agent Collaboration for Brainstorming" (ResearchGate, Dec 2025)
3. "LLM Discussion: Enhancing Creativity" (arXiv:2405.06373v2)
4. "Adversarial Debate and Voting Mechanisms" (MDPI 15/7/3676)
5. "Scaling LLM Multi-Agent Systems" (ICLR 2025)

### Code Repositories
1. modelcontextprotocol/servers - MCP reference implementations
2. TensorBlock/awesome-mcp-servers - MCP server list
3. robertZaufall/mindm-mcp - MindManager integration

---

## Appendix A: Glossary

- **CoT**: Chain-of-Thought (sequential reasoning)
- **ToT**: Tree-of-Thought (branching exploration)
- **GoT**: Graph-of-Thought (graph-based reasoning)
- **CKS**: Cognitive Knowledge System
- **MCP**: Model Context Protocol
- **MPBA**: Multi-Phase Brainstorming Architecture

---

**Status**: Ready for Architecture Review
**Next Step**: Execute `/arch` to validate architecture approach
