# System Context for Architecture Proposals

**Purpose**: This document provides external LLMs with complete context about the existing system. When proposing architecture changes, assume everything in this document is true and complete unless explicitly told otherwise.

**Last Updated**: 2026-03-12

---

## Existing Systems

### Knowledge Systems

#### CKS (Constitutional Knowledge System)
- **Location**: `P:/src/knowledge/systems/cks/`
- **Purpose**: Persistent knowledge storage and retrieval
- **Technology**: SQLite database with FAISS vector search
- **Content**: 492 memory entries (lessons learned, patterns, fixes, constitutional rules)
- **Access**: `/cks` skill, used by `/research` and other skills
- **Key Features**:
  - Semantic search via embeddings
  - Stores structured memories (question → answer → pattern type)
  - Single source of truth for institutional knowledge

#### CHS (Chat History Search)
- **Location**: `P:/src/knowledge/systems/chs/`
- **Purpose**: Semantic search across conversation history
- **Technology**: SQLite with vector embeddings
- **Content**: Past chat transcripts indexed for retrieval
- **Access**: Semantic search for "what did we do about X?" queries
- **Key Features**:
  - Find past conversations by semantic similarity
  - Supports context-aware queries
  - Complements CKS with conversational episodes

### Cognitive Control Layer

#### Hooks
- **Location**: `P:/.claude/hooks/`
- **UserPromptSubmit Hook**: Injects cognitive frameworks based on intent/topic
- **Start Hook**: Selects reasoning modes (SEQ/MAS/2ST/Graph)
- **Conflict Arbiter**: Enforces rules about framework coexistence
- **Observability**: JSONL logging of selections with metrics

#### Current Enhancers (9 total)
1. Cynefin Framework
2. Hanlon's Razor
3. Devil's Advocate
4. Calibrated Confidence
5. Socratic Decomposition
6. Assumption Surfacing
7. Outcome Anchoring
8. Inversion Prompting
9. [Others - see `cognitive_enhancers_config.json`]

#### Reasoning Modes (4 total)
- Sequential (SEQ): Step-by-step reasoning
- Multi-Agent (MAS): Parallel agent coordination
- Two-Stage (2ST): Draft + refine approach
- Graph (GRAPH): Graph-of-Thoughts reasoning

### Workflow & Skills Layer

#### Planning Skills
- `/plan-workflow`: Build and verify implementation plans
- `/code`: AI-assisted feature development
- `/arch`: Architecture advisor with templates
- **Key Point**: Planning is a SEPARATE workflow, not a cognitive framework

#### Knowledge Skills
- `/research`: Web research with multiple providers
- `/cks`: Query Constitutional Knowledge System
- `/chs`: Search chat history
- `/all`: Unified intelligent search

#### Total Skills: 200+
- **Location**: `P:/.claude/skills/`
- **Categories**: Workflow, knowledge, testing, development, ops

---

## Constitutional Constraints

### Development Philosophy
- **Anti-Bloat**: "One powerful engine + slim adapters"
- **Consolidation**: Prune duplicate mechanisms, don't accumulate frameworks
- **Lean Systems**: Prefer strengthening existing systems over adding new ones

### Development Context
- **Solo Development**: Single developer, Director + AI workforce model
- **No Team Collaboration**: All commits are by solo developer
- **Code Review**: Self-reflection only

### Platform Constraints
- **OS**: Windows 11
- **Python**: 3.12+
- **Infrastructure**: No Docker, no cloud services, no background daemons
- **Persistence**: File-based only (JSONL, text files, SQLite)
- **Databases**: No external databases, SQLite allowed

### Testing Requirements
- **Methodology**: TDD (Test-Driven Development)
- **Framework**: pytest
- **Coverage**: >80% required for new code
- **Isolation**: Tests must be isolated and clean up after themselves

---

## Architectural Patterns

### Memory vs. Stateless Design
- **Hooks are stateless**: No session memory to manage
- **Memory lives in CKS/CHS**: Persistent knowledge is separate
- **Implication**: Don't suggest "add memory to hooks" - integrate with CKS/CHS instead

### Planning vs. Cognitive Enhancement
- **Planning = Workflow Skills**: `/plan-workflow`, `/code`, `/arch` handle multi-step tasks
- **Cognitive Frameworks = Mental Models**: Enhancers improve thinking quality
- **Implication**: Don't suggest "planner reasoning mode" - use existing workflow skills

### Conflict Arbiter Patterns
- **Max 3 Enhancers**: Prevents framework explosion
- **Token Budget Enforcement**: Keeps injections lean
- **Fast-Mode Gating**: Verbose frameworks suppressed in fast mode
- **Override Modes**: `#deep`, `#rca` allow exceptions to standard rules

### Observability Patterns
- **JSONL Logging**: All selections logged with timestamps
- **Metrics-Driven Tuning**: Use data to adjust defaults and arbiter rules
- **30-Day Kill Switch**: Trial features evaluated with rollback plan

---

## Common Pitfalls (DO NOT DO)

### ❌ "Add Memory/Case Recall"
**Reality**: We have CKS (492 entries) and CHS (chat search)
**Correct Approach**: "Integrate with existing CKS/CHS systems"

### ❌ "Add Planner Reasoning Mode"
**Reality**: We have `/plan-workflow`, `/code`, `/arch` skills for planning
**Correct Approach**: "Enhance existing workflow skills" or "add planning-specific patterns to cognitive enhancers"

### ❌ "Multi-Terminal/Team Features"
**Reality**: Solo development, no team collaboration
**Correct Approach**: Focus on individual productivity patterns

### ❌ "Cloud Services/Docker/Kubernetes"
**Reality**: Windows 11, Python 3.12+, file-based persistence only
**Correct Approach**: Use SQLite, JSONL, text files; no cloud dependencies

### ❌ "Add New Framework for X"
**Reality**: Anti-bloat philosophy - consolidate before expanding
**Correct Approach**: Check if existing enhancers cover 70%+ of use case; enhance them instead

---

## Codebase Statistics

### Language Distribution
- **Primary**: Python (3.12+)
- **Configuration**: JSON, YAML
- **Documentation**: Markdown

### Testing
- **Framework**: pytest
- **Coverage Target**: >80%
- **Isolation**: Each test must clean up after itself

### File Organization
```
P:/
├── .claude/
│   ├── hooks/           # Stateless cognitive control
│   ├── skills/          # 200+ skills
│   └── context/         # System context documents
├── src/
│   └── knowledge/
│       └── systems/     # CKS, CHS
└── packages/
    └── reasoning/       # Cognitive framework implementation
```

---

## Performance Characteristics

### Token Budgets
- **Max Enhancers**: 3 per prompt
- **Typical Injection**: 50-150 tokens depending on enhancers
- **Fast Mode**: Suppresses verbose frameworks

### Latency
- **Hook Execution**: <100ms typical
- **CKS Query**: <500ms for semantic search
- **CHS Query**: <500ms for chat search

### Resource Limits
- **Memory**: Minimal (hooks are stateless)
- **Disk**: JSONL logs grow over time, periodic cleanup needed
- **CPU: Negligible for hooks/modest for CKS/CHS queries**

---

## Recent Architectural Decisions

### 5W1H Inquiry (In Progress)
- **Status**: Proposed, not yet implemented
- **Purpose**: Add explicit context-gathering cognitive enhancer
- **Design**: Single enhancer, not new subsystem
- **Validation**: 30-day observability trial with kill switch

### Anti-Bloat Enforcement
- **Rationale**: Prevent framework accumulation
- **Method**: Audit enhancers quarterly, remove unused
- **Threshold**: <30 days without selection → candidate for removal

### CKS/CHS Integration
- **Status**: Existing and operational
- **Usage**: Accessed via skills, not directly by hooks
- **Reason**: Keep hooks stateless, separate concerns

---

## Glossary

- **CKS**: Constitutional Knowledge System - persistent memory
- **CHS**: Chat History Search - conversational context
- **Enhancers**: Cognitive frameworks that improve thinking quality
- **Modes**: Reasoning strategies (SEQ, MAS, 2ST, GRAPH)
- **Conflict Arbiter**: Enforces rules about framework coexistence
- **Observability**: JSONL logging of selections for metrics
- **Anti-Bloat**: Design philosophy - consolidate before expanding
- **Solo Dev**: Single developer context, no team features

---

**Usage Instructions for External LLMs**:

1. **Read this entire document before proposing architecture**
2. **Assume everything here is true unless explicitly told otherwise**
3. **Do not suggest features that contradict "Common Pitfalls"**
4. **Use the MVA template (`architecture_proposal.md`) for all proposals**
5. **If you're unsure about a constraint, ask rather than assume**

**Violating these instructions will result in immediate rejection and request for revision.**
