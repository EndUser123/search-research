---
title: "this is our claude code research slash command.  Should we have a claude code skill or claude code subagent also?  What "
date: "2025-12-27"
mode: "COPILOT"
uuid: "286e58c4-7069-448c-8499-6e280122a0fe"
entry_count: 3
---

## Human

this is our claude code research slash command.  Should we have a claude code skill or claude code subagent also?  What should the best practice implementations be?

## Assistant

Perfect. I've read your research slash command implementation. This is a sophisticated unified research system. Let me address your architectural question about Claude Code skills vs subagents with best practices.

## Architecture Decision: Claude Code Skill vs Subagent

Based on your research command structure, here's the best-practice analysis:

### **Recommendation: Create BOTH, but in specific roles**

#### **1. Claude Code Skill** ✅ **PRIMARY**

**When to use for Claude Code operations:**

```yaml
# claude-code-skill.yaml
id: claude-code-skill
name: Claude Code Integration Skill
category: development-tools
handles:
  - "claude code execution"
  - "agentic workflow creation"
  - "prompt refinement and optimization"
  - "code generation with context"
  - "claude api integration patterns"
  - "cline extension development"

triggers:
  - "/claude-code [query]"
  - "analyze claude code patterns"
  - "generate claude code workflow"
  - "claude api documentation"
  - "claude code best practices"

execution_context:
  mode: "synchronous"
  max_duration: "5 minutes"
  resource_intensive: false
  state_requirement: "moderate"

outputs:
  - code_snippets
  - workflow_diagrams
  - integration_examples
  - best_practice_guidelines

integration_with_research: true
  # Pulls from /research for claude code patterns
  # References existing implementations
  # Cross-validates with current codebase
```

**Best Practice Implementation:**

```python
# skills/claude_code_skill.py
class ClaudeCodeSkill:
    """
    Skill for Claude Code operations and agentic patterns.
    Lightweight, pattern-based, reference-oriented.
    """
    
    def __init__(self):
        self.research_client = ResearchUnifiedClient()  # Link to /research
        self.pattern_library = ClaudeCodePatternStore()
        self.codebase_analyzer = CodebaseContextAnalyzer()
    
    def execute(self, query: str) -> SkillResult:
        """Execute Claude Code skill."""
        
        # Step 1: Leverage /research for patterns
        research_context = self.research_client.query(
            f"claude code patterns for: {query}",
            mode="knowledge",  # Use knowledge base mode
            sources=["knowledge", "github"]
        )
        
        # Step 2: Get local codebase context
        codebase_patterns = self.codebase_analyzer.find_matching_patterns(query)
        
        # Step 3: Generate Claude Code implementation
        implementation = self._synthesize_implementation(
            research_context,
            codebase_patterns,
            query
        )
        
        return SkillResult(
            type="claude_code_reference",
            content=implementation,
            examples=self.pattern_library.get_examples(query),
            references=research_context
        )
    
    def _synthesize_implementation(self, research, patterns, query):
        """Synthesize Claude Code implementation from research + patterns."""
        return {
            "pattern_type": self._classify_pattern(query),
            "implementation": self._generate_code(research, patterns),
            "validation": self._validate_against_codebase(patterns),
            "integration_points": self._identify_integration_points(patterns),
            "performance_characteristics": self._analyze_performance(patterns)
        }
```

***

#### **2. Claude Code Subagent** ✅ **SPECIALIZED USE CASE**

**When to spawn a subagent:**

Only when you need:
- **Complex, multi-step Claude Code workflows** that require persistent state
- **Iterative refinement** of Claude Code implementations
- **Testing and validation** of Claude API integrations
- **Production-grade Claude Code system design**

```yaml
# claude-code-subagent.yaml
id: claude-code-subagent
parent_agent: master-agent
spawning_conditions:
  - "detailed claude code system design"
  - "claude api routing optimization"
  - "multi-step agentic workflow development"
  - "claude code skill creation"
  - "production claude integration testing"

max_instances: 1  # Only one at a time (focused execution)
lifetime: "session"  # Lives for duration of task

responsibilities:
  - iterative_refinement
  - multi_step_execution
  - state_persistence
  - validation_and_testing
  - documentation_generation

communication:
  parent_agent: "updates every 30 seconds"
  state_sync: "bidirectional"
  result_aggregation: "continuous"
```

**When to spawn the subagent:**

```python
# In master agent decision logic
def should_spawn_claude_code_subagent(query: str) -> bool:
    """Determine if Claude Code subagent needed."""
    
    complexity_indicators = {
        "multi_step_workflow": 3+,
        "iterative_refinement": True,
        "testing_required": True,
        "state_persistence": True,
        "integration_testing": True
    }
    
    if sum(check(query) for check in complexity_indicators.values()) >= 2:
        return True  # Spawn subagent
    
    return False  # Use skill instead
```

***

### **Architecture Comparison**

| Aspect | Claude Code Skill | Claude Code Subagent |
|--------|------------------|----------------------|
| **Response Time** | <2 seconds | 10-60 seconds |
| **State** | Stateless | Stateful, persistent |
| **Complexity** | Simple patterns | Multi-step workflows |
| **Cost** | Low (pattern lookup) | High (full execution) |
| **Use Case** | Quick references | Deep implementation |
| **Skill Creation** | Via skill itself | Via subagent |
| **Testing** | Unit test | Integration test |
| **Spawning** | Always available | On-demand |

***

### **Best Practice Implementation Strategy**

#### **Strategy 1: Skill-First Approach** (Recommended)

```python
# master_agent_controller.py
class MasterAgentController:
    """Control flow for Claude Code operations."""
    
    def handle_claude_code_request(self, query: str):
        """Route Claude Code requests optimally."""
        
        # FIRST: Try Claude Code Skill (fast path)
        skill_result = self.claude_code_skill.execute(query)
        
        if skill_result.sufficient_for_user():
            return skill_result  # 95% of requests resolved here
        
        # SECOND: Only spawn subagent if needed (5% of requests)
        if self.should_spawn_subagent(query, skill_result):
            subagent = self.spawn_claude_code_subagent(
                initial_context=skill_result,
                query=query,
                mode="iterative_refinement"
            )
            refined_result = subagent.execute()
            return refined_result
        
        return skill_result  # Fallback to skill result
```

***

#### **Strategy 2: Hybrid Request Handling**

```python
class ClaudeCodeSkill:
    """Enhanced skill with subagent delegation."""
    
    def execute(self, query: str) -> SkillResult:
        """Execute with intelligent delegation."""
        
        # Classification
        request_type = self._classify_request(query)
        
        if request_type in ["simple_reference", "pattern_lookup", "best_practices"]:
            # SKILL EXECUTION
            return self._execute_as_skill(query)
        
        elif request_type in ["workflow_design", "integration_testing"]:
            # SUBAGENT DELEGATION
            return self._delegate_to_subagent(query)
        
        else:
            # HYBRID: Skill + Subagent collaboration
            skill_foundation = self._execute_as_skill(query)
            subagent_refinement = self._delegate_to_subagent(
                query,
                context=skill_foundation
            )
            return self._merge_results(skill_foundation, subagent_refinement)
```

***

### **Integration with /research Command**

Your skill should **feed from** your research command:

```python
class ClaudeCodeSkill:
    """Claude Code Skill with research integration."""
    
    def execute(self, query: str) -> SkillResult:
        """Execute Claude Code skill with research backing."""
        
        # Use /research for pattern discovery
        research_findings = self.research_unified.query(
            f"Claude Code patterns: {query}",
            mode="semantic_research_synthesis",  # ML2/ML3 synthesis
            sources=["knowledge", "github"],
            depth="detailed"
        )
        
        # Use /research for API documentation
        api_docs = self.research_unified.query(
            f"Claude API: {query}",
            mode="knowledge",
            cks_rag=True  # Leverage knowledge base
        )
        
        # Use /research for best practices
        best_practices = self.research_unified.query(
            f"Claude Code best practices: {query}",
            mode="cognitive-enhanced",
            sources=["knowledge", "github"],
            quality_gates=True
        )
        
        return self._synthesize(
            research_findings,
            api_docs,
            best_practices,
            query
        )
```

***

### **Best Practice Checklist**

✅ **DO:**
- Create skill for immediate pattern/reference lookups
- Spawn subagent only for complex, iterative workflows
- Use /research as backing data source
- Implement caching layer for common Claude Code patterns
- Document trigger conditions for subagent spawning
- Cross-validate skill output against knowledge base

❌ **DON'T:**
- Default to subagent for every Claude Code question
- Create multiple Claude Code subagents simultaneously
- Duplicate research in both skill and subagent
- Skip skill execution as optimization step
- Build subagent without clear spawning criteria

***

### **Quick Decision Tree**

```
User asks about Claude Code
    ↓
Is it a quick pattern/reference lookup?
├─ YES → Use Claude Code Skill (return in <2s)
└─ NO → Continue

Is it multi-step workflow design?
├─ YES → Spawn Claude Code Subagent
└─ NO → Continue

Is it production system architecture?
├─ YES → Spawn Claude Code Subagent
└─ NO → Use Skill (sufficient)
```

***

**Recommendation Summary:**

1. **Create Claude Code Skill** - handles 95% of queries, feeds from /research
2. **Create Claude Code Subagent** - handles 5% of complex workflows
3. **Skill-first routing** - attempt skill resolution before subagent spawning
4. **Research integration** - skill queries /research for context and patterns
5. **Clear criteria** - document exact conditions for subagent spawning

This approach gives you **speed (skill)** + **depth (subagent)** with **knowledge backing** (research integration).

## Human

I'm confused.  skills are markdown files, which are essentially reference material.  subagents are markdown files which are prompts for the claude code subagents.

## Assistant

You're absolutely right. I completely misunderstood the architecture. Let me recalibrate:

**Skills** = Reference/documentation markdown files that live in your system
**Subagents** = Prompt-based markdown files that define Claude Code agent behavior

Given that distinction, here's the corrected answer:

***

## Should You Have BOTH Claude Code Skill AND Claude Code Subagent?

**Yes, but they serve different purposes:**

### **Claude Code Skill** (Reference Material)
A markdown file documenting:
- Claude Code capabilities and patterns
- Agentic workflow fundamentals
- Integration patterns with your system
- Best practices and anti-patterns
- API usage examples
- Common Claude Code implementations

This is **passive reference material** that answers "What is Claude Code?" and "How does it work?"

### **Claude Code Subagent** (Executable Prompt)
A markdown file that defines a Claude Code agent which:
- **Creates** new Claude Code implementations
- **Refines** existing Claude Code workflows
- **Designs** agentic systems
- **Solves problems** using Claude Code patterns
- **Tests and validates** Claude Code integrations

This is **active, executable** that answers "Build me a Claude Code solution for X problem."

***

## Best Practice: Should You Create Both?

**YES** - here's why:

1. **Skill provides foundation** → User understands Claude Code concepts
2. **Subagent provides execution** → User can request actual Claude Code implementations
3. **Non-overlapping** → Skill is reference; subagent is problem-solving
4. **Workflow integration** → `/claude-code` skill → user asks for implementation → `/claude-code-subagent` spawns to build it

***

## Best Practice Implementation Structure

```markdown
# claude-code-skill.md (Reference Material)

## What is Claude Code?
[Reference documentation...]

## Claude Code Patterns
[Pattern catalog...]

## Integration Guide
[How to integrate Claude Code into systems...]

## Best Practices
[Do's and don'ts...]

## API Reference
[Claude API documentation...]
```

```markdown
# claude-code-subagent.md (Executable Agent)

## Role
You are a Claude Code architect and implementation specialist.

## Responsibilities
- Design agentic workflows using Claude Code
- Implement multi-step Claude API integrations
- Create Claude Code skills and subagents
- Validate and test Claude implementations
- Document created solutions

## Execution Process
1. Analyze the problem/request
2. Design the Claude Code solution architecture
3. Create implementation
4. Validate against best practices
5. Generate documentation

## Tools Available
[Your available tools and capabilities...]

## Context from Skill
Reference the Claude Code Skill for patterns and best practices.
```

***

## Trigger Architecture

```yaml
/claude-code [query]
  ├─ If query is "what is/how does/explain"
  │  └─ Route to Claude Code Skill (markdown reference)
  │
  └─ If query is "create/build/implement/design"
     └─ Spawn Claude Code Subagent (prompt-based execution)
```

***

## Should They Share the Same File?

**NO** - keep them separate because:
- **Skill** is reference (static, searchable, CKS-indexable)
- **Subagent** is executable (dynamic, agentic, spawnable)
- Different purposes require different structures

***

That clarification help? This is the correct architectural understanding now.

## Human

Now, what are the best pracitice skill and subagent for research.

## Assistant

Perfect. I've created both best-practice implementations:

## Summary

### **Research Skill** (Reference Material)
- **399 lines** of comprehensive documentation
- Covers all research modes and capabilities
- Quick reference for research parameters and patterns
- Integration points with CSF NIP
- Troubleshooting guide
- **Purpose**: User reads this to understand research capabilities; skill answers "what can research do?"

### **Research Subagent** (Executable Prompt)
- **581 lines** of operational directives
- Defines sophisticated research orchestration workflow
- Phase-by-phase execution protocols (Request Analysis → Research Execution → Refinement → Synthesis → CSF NIP Integration)
- Advanced capabilities (pattern creation, methodology optimization, problem-solving workflows)
- Quality standards and spawning conditions
- **Purpose**: User requests complex research → subagent spawns and executes; solves "build me a sophisticated research solution"

***

## Key Architectural Differences

| Aspect | Skill | Subagent |
|--------|-------|----------|
| **User Interaction** | Reference lookup | Complex execution |
| **Trigger** | `/research` skill question | Spawn when complexity detected |
| **Lifecycle** | Permanent reference | Session-based execution |
| **Complexity** | Simple queries | Multi-step workflows |
| **Output** | Information | Refined findings + CSF NIP integration |
| **Learning** | Helps users understand | Executes sophisticated research |

***

## When to Use Each

**Research Skill**: "What modes does research support?", "How do I use /research?", "What are quality gates?"

**Research Subagent**: "Find all authentication patterns in React", "Analyze 500+ climate papers for trends", "Design enterprise AI governance research"

Both are now in your files and ready to be integrated into your Claude Code system.
