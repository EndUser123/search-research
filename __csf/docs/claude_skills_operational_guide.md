# Agentic AI Operational Guide

**Purpose:** Implementation patterns and how-to guidance for building agentic AI skills

**Last Updated:** 2026-02-03

---

## Critical Foundation: How Claude Code Skills Work

**READ THIS FIRST** - This section prevents the most common misunderstanding about Claude Code skills.

### The Documentation-Driven Pattern

Claude Code skills follow a **documentation-driven pattern**, not a code-driven pattern.

**Key Principle:** `SKILL.md` **IS** the handler - not a reference to separate code.

```
WRONG Pattern (Code-Driven):
  /task → skill_handler.py → executes code → returns result

CORRECT Pattern (Documentation-Driven):
  /task → Skill tool loads SKILL.md → Claude reads workflow → Claude calls tools directly → returns result
```

### What Actually Happens When You Invoke a Skill

1. **User invokes**: `/task add "Fix bug"`
2. **Skill tool loads**: Reads `P:/.claude/skills/task/SKILL.md`
3. **Claude parses**: Extracts sub-command ("add") from the markdown
4. **Claude follows workflow**: Calls `TaskCreate(subject="Fix bug", status="pending")` directly
5. **Result returned**: User sees confirmation

**There is no separate Python handler file.** The markdown document IS the implementation.

### Common Anti-Pattern to Avoid

**DO NOT create standalone handler files:**

```python
# ❌ WRONG - task_handler.py (unnecessary)
def handle_add(subject):
    return TaskCreate(subject=subject, status="pending")

def handle_list():
    return TaskList()

# This file represents a misunderstanding of Claude Code skills
```

**Instead, document the workflow in SKILL.md:**

```markdown
# /task - Task Orchestration

## Sub-Commands

**Add task:**
1. Parse subject from arguments
2. Call TaskCreate(subject="...", status="pending")
3. Return confirmation with task ID

**List tasks:**
1. Call TaskList()
2. Format output as #<id> [<status>] <subject>
```

### When to Use Each Pattern

| Use SKILL.md alone when... | Consider separate code when... |
|----------------------------|-------------------------------|
| Simple workflow routing | Complex external API integration |
| Direct tool calls needed | Heavy computation required |
| Workflow < 200 lines | Need independent unit testing |
| Built-in tools sufficient | External library dependencies |

**Even for complex cases**, prefer:
- Resource templates (see Section 1)
- Skill dispatch to sub-skills
- Hooks for validation

### Real-World Lesson: The /task Skill

**What happened:**
1. Initial implementation created `task_handler.py` and `test_task_handler.py`
2. Research revealed Claude skills are documentation-driven
3. Deleted handler files, updated SKILL.md to clarify it IS the implementation
4. Skill works perfectly with markdown-only approach

**Evidence:** See `P:/.claude/skills/task/SKILL.md` for complete working example.

### Verification Checklist

Before creating a separate Python handler for a skill:
- [ ] Have you confirmed SKILL.md cannot express this workflow?
- [ ] Are you integrating external APIs that require async/complex logic?
- [ ] Do you need unit testing independent of Claude execution?
- [ ] Is the workflow > 500 lines of markdown?

**If all answers are "NO", use SKILL.md alone.**

---

## Quick Reference

| Pattern | When to Use | Implementation |
|---------|-------------|----------------|
| Resource Templates | Skill variants, router patterns | `resources/*.md` with conditional inclusion |
| Skill Dispatch | Independent, testable components | `Skill()` tool with separate SKILL.md files |
| Routing | Intent-based variant selection | Classification logic → dispatch/include |
| Reflection Loops | Self-correcting workflows | Post-execution validation → retry |

---

## 1. Resource Template Pattern

### When to Use
- Multiple variants of similar functionality (fast/deep, domain-specific)
- Router+implementation architecture
- Want single user-facing entry point

### Implementation

**Directory Structure:**
```
skill-name/
├── SKILL.md          # Router/entry point
└── resources/
    ├── variant1.md   # Implementation template
    ├── variant2.md   # Implementation template
    └── variant3.md   # Implementation template
```

**Template Format:**
```markdown
# Variant Name

## Analysis Steps

1. Step one
2. Step two
3. Step three

## Output Format

Expected output structure...
```

**Router Logic (in SKILL.md):**
```markdown
## Stage 1: Classify Intent

Determine which variant based on query analysis.

## Stage 2: Include Template

**For variant1:**
```
Read(file_path="P:/.claude/skills/skill-name/resources/variant1.md")
```

Follow the template's directives.
```

### Example: `/arch` with Resource Templates

**Intent Classification:**
```
IF "redesign", "overhaul", "architecture" → Use deep.md
ELSE → Use fast.md

IF "CLI", "POSIX", "terminal" → Use cli.md
IF "Python", "asyncio", "GIL" → Use python.md
IF "ETL", "pipeline", "Spark" → Use data-pipeline.md
```

**Template Inclusion:**
```python
# After classification
Read(file_path="P:/.claude/skills/arch/resources/fast.md")
```

Then execute the template's workflow.

---

## 1.5 Wrong Pattern vs. Correct Pattern Examples

### The Wrong Pattern: Standalone Python Handler

**File Structure (WRONG):**
```
.claude/skills/task/
├── SKILL.md              # References external handler
├── task_handler.py       # ❌ Unnecessary Python file
└── test_task_handler.py  # ❌ Tests for unnecessary file
```

**task_handler.py (DON'T DO THIS):**
```python
"""
Standalone handler for /task skill.
This represents a misunderstanding of Claude Code skills.
"""

import sys
sys.path.append("P:/__csf/src")

def handle_add(subject: str) -> dict:
    """Add a new task."""
    # This is WRONG - TaskCreate tool should be called directly
    return {"id": "123", "subject": subject, "status": "pending"}

def handle_list() -> list:
    """List all tasks."""
    # This is WRONG - TaskList tool should be called directly
    return [
        {"id": "123", "subject": "Fix bug", "status": "pending"}
    ]

def main():
    """Router for task commands."""
    if len(sys.argv) < 2:
        print("Usage: task_handler.py <command> [args]")
        return

    command = sys.argv[1]

    if command == "add":
        result = handle_add(sys.argv[2] if len(sys.argv) > 2 else "")
        print(f"Task #{result['id']} created")
    elif command == "list":
        tasks = handle_list()
        for task in tasks:
            print(f"#{task['id']} [{task['status']}] {task['subject']}")

if __name__ == "__main__":
    main()
```

**Why This Is Wrong:**
1. **Claude never executes this file** - The Skill tool loads SKILL.md, not Python
2. **Reinvents built-in tools** - TaskCreate/TaskList already exist
3. **Unnecessary complexity** - Adds subprocess layer that isn't used
4. **Testing doesn't validate skill** - Tests handler file, not actual skill behavior

### The Correct Pattern: SKILL.md as Handler

**File Structure (CORRECT):**
```
.claude/skills/task/
└── SKILL.md              # This IS the handler
```

**SKILL.md (THE RIGHT WAY):**
```markdown
---
name: task
description: Task orchestration - manage Claude Code task list
category: workflow
triggers:
  - /task
---

# /task - Task Orchestration

## Purpose

Orchestrator for Claude Code task list operations. Routes sub-commands to built-in TaskCreate/TaskUpdate/TaskList/TaskGet tools.

## How This Skill Works

**When you invoke `/task <command>`, the following occurs:**
1. **Skill tool loads this SKILL.md** - The markdown documentation IS the handler
2. **Claude parses your sub-command** - Extracts the operation (list/add/done/start/search/clean/help)
3. **Claude executes the appropriate tool** - Calls TaskList/TaskCreate/TaskUpdate directly
4. **Results are formatted and returned** - You see the output

**There is no separate Python handler file** - This SKILL.md document IS the implementation.

## Sub-Commands

| Command | Purpose | Tool | Implementation |
|---------|---------|------|----------------|
| `list` | Show all tasks | TaskList | Format output with status indicators |
| `add <subject>` | Create new task | TaskCreate | Set status=pending, auto-generate ID |
| `done <id>` | Mark task complete | TaskUpdate | Set status=completed |
| `start <id>` | Start working on task | TaskUpdate | Set status=in_progress, set owner |

## Implementation Workflow

**For `/task add "Fix authentication bug"`:**

1. **Claude reads this SKILL.md** (via Skill tool)
2. **Claude identifies "add" sub-command**
3. **Claude validates subject is not empty**
4. **Claude calls:**
   ```python
   TaskCreate(
       subject="Fix authentication bug",
       description="",
       status="pending",
       activeForm="Fixing authentication bug"
   )
   ```
5. **Claude returns:** "Task #334 created: [pending] Fix authentication bug"

**For `/task list`:**

1. **Claude reads this SKILL.md**
2. **Claude identifies "list" sub-command**
3. **Claude calls:**
   ```python
   TaskList()
   ```
4. **Claude formats output:**
   ```
   #334 [pending] Fix authentication bug
   #315 [in_progress] Review code
   #318 [completed] Add tests
   ```

## Why This Works

- **No subprocess overhead** - Tools are called directly by Claude
- **Built-in persistence** - PostToolUse_task_tracker hook saves state
- **Multi-terminal safe** - Each terminal has its own task file
- **Session survival** - Tasks persist across compaction and restore
```

### Key Differences Summary

| Aspect | Wrong Pattern | Correct Pattern |
|--------|---------------|-----------------|
| **Handler location** | Separate Python file | SKILL.md IS the handler |
| **Execution** | Never called by Claude | Claude reads and follows |
| **Tool use** | Reinvents built-in tools | Uses tools directly |
| **Testing** | Tests unused code | Tests skill via invocation |
| **Complexity** | Adds unnecessary layer | Minimal, direct |
| **Evidence** | No proof it works | `/task list` proves it works |

### When You Actually Need Separate Code

Separate Python files are appropriate ONLY when:

1. **External API Integration** - Async web APIs, database connections, etc.
2. **Complex Computation** - Heavy processing that Python handles better
3. **Independent Testing** - Need to test logic outside Claude execution

**Even then, consider:**
- Can a hook handle this? (PostToolUse hooks run Python)
- Can a sub-skill handle this? (Skill dispatch pattern)
- Can this be documented in SKILL.md? (Most cases yes)

---

## 2. Skill Dispatch Pattern

### When to Use
- Need independent testing of variants
- Variants may be invoked directly
- Want proven infrastructure (Skill tool)

### Implementation

**Directory Structure:**
```
skill-name/
├── SKILL.md          # Router
skill-name-fast/
├── SKILL.md          # Variant implementation
skill-name-deep/
├── SKILL.md          # Variant implementation
```

**Router Logic:**
```python
# Dispatch via Skill tool
Skill(skill="skill-name-fast", args="<ARGUMENTS>")
```

**Frontmatter for Internal Skills:**
```yaml
---
name: skill-name-fast
description: Quick variant
internal: true  # Hides from user-facing discovery
---
```

### Registry Filtering

**User-facing commands:**
```python
from skill_registry import list_user_facing_skills

# Gets only non-internal, non-deprecated skills
skills = list_user_facing_skills()
```

---

## 3. Routing Pattern

### Implementation Steps

1. **Classify Intent**
   - Analyze query for keywords
   - Detect domain-specific terms
   - Assess complexity level

2. **Select Variant**
   - Map classification to variant
   - Handle edge cases (ambiguous queries)

3. **Execute**
   - Include template OR dispatch to skill
   - Follow variant's workflow
   - Return formatted output

### Classification Logic

```python
# Complexity Detection
complexity = "HIGH" if any(k in query for k in [
    "redesign", "overhaul", "architecture", "microservices"
]) else "LOW"

# Domain Detection
domain = None
if any(k in query for k in ["CLI", "POSIX", "terminal"]):
    domain = "cli"
elif any(k in query for k in ["Python", "asyncio", "GIL"]):
    domain = "python"

# Variant Selection
if domain == "cli":
    variant = "cli"
elif complexity == "HIGH":
    variant = "deep"
else:
    variant = "fast"
```

---

## 4. Reflection Loop Pattern

### When to Use
- Self-correcting workflows
- Validation after execution
- Quality assurance

### Implementation

**Hook-Based:**
```python
# PostToolUse_validator.py
def validate_output(result):
    if not meets_criteria(result):
        return {"retry": True, "reason": "Criteria not met"}
    return {"retry": False}

# In skill workflow:
1. Execute analysis
2. Call validator
3. If retry: refine and repeat
4. Return final output
```

**Template-Based:**
```markdown
## Stage 3: Self-Validation

Check your output against:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

If any fail:
1. Identify failure
2. Refine output
3. Re-validate
```

---

## 5. Template Composition

### Chaining Templates

```markdown
## Main Template

Execute [base-analysis.md](resources/base-analysis.md)

Then apply [domain-overlay.md](resources/domain-overlay.md)

Finally, validate using [quality-check.md](resources/quality-check.md)
```

### Conditional Inclusion

```markdown
## Dynamic Selection

{% if complexity == "high" %}
Include [deep-analysis.md](resources/deep-analysis.md)
{% else %}
Include [quick-analysis.md](resources/quick-analysis.md)
{% endif %}

{% if domain == "python" %}
Apply [python-specific.md](resources/python-specific.md)
{% endif %}
```

---

## 6. Memory Integration Pattern

### CKS.db Queries in Templates

```markdown
## IMPROVE_SYSTEM Path

**Query CKS for relevant failures:**
```python
from cks import search
failures = search("memory system failure keywords", limit=5)
```

**Ground recommendations in findings:**
- Finding 1: {{failures[0]}}
- Finding 2: {{failures[1]}}
```

---

## 7. Error Handling

### Template Not Found

```markdown
## Fallback Behavior

If template cannot be loaded:
1. Log error
2. Use default/basic analysis
3. Notify user of limited capability
```

### Ambiguous Classification

```markdown
## When Unclear

If query doesn't clearly match any variant:
1. Ask clarifying question
2. Provide options
3. Wait for user selection
```

---

## 8. Testing Patterns

### Unit Testing Templates

```python
# tests/test_arch_templates.py
def test_fast_template_exists():
    path = Path("P:/.claude/skills/arch/resources/fast.md")
    assert path.exists()

def test_deep_template_content():
    content = Path(".../arch/resources/deep.md").read_text()
    assert "DEEP analysis" in content
```

### Integration Testing Router

```python
def test_arch_routes_simple_to_fast():
    # Simulate simple query
    result = arch_router("should I extract this service?")
    assert result.variant == "deep"  # Extract is complex
```

---

## 9. Best Practices

### DO
- Use resource templates for variant patterns
- Keep templates focused and single-purpose
- Include clear selection criteria in router
- Test each variant independently
- Document template structure

### DON'T
- Create deeply nested template hierarchies
- Mix routing logic with implementation
- Make templates too large (>500 lines)
- Duplicate common patterns (extract to base template)
- Forget to handle edge cases

---

## 10. Migration Path

### From Skill Dispatch to Resource Templates

**Phase 1: Extract Content**
1. Create `resources/` directory
2. Copy content from variant SKILL.md to template files
3. Remove frontmatter from templates

**Phase 2: Update Router**
1. Replace `Skill()` calls with `Read()` + include
2. Add template selection logic
3. Test each variant

**Phase 3: Cleanup**
1. Archive old skill directories
2. Update documentation
3. Verify only main skill appears in discovery

---

## 11. Built-in Tools Reference

### Claude Code Tool System

| Tool | Purpose | Parameters | Returns |
|------|---------|------------|---------|
| `TaskCreate` | Create new task | subject, description, activeForm, status, metadata | Task object with ID |
| `TaskUpdate` | Update existing task | taskId, status, addBlocks, addBlockedBy, owner | Updated task |
| `TaskGet` | Get task details | taskId | Full task object |
| `TaskList` | List all tasks | - | Array of task objects |
| `Read` | Read file | file_path, offset, limit, pages | File contents |
| `Write` | Write file | file_path, content | Success confirmation |
| `Edit` | Edit file (string replace) | file_path, old_string, new_string | Success confirmation |
| `Bash` | Execute shell command | command, timeout | Command output |
| `Skill` | Invoke another skill | skill, args | Skill result |
| `Glob` | Find files by pattern | pattern, path | Matching file paths |
| `Grep` | Search file contents | pattern, path, type, output_mode | Matching lines/paths |

**Usage Notes:**
- Tools are called directly by Claude, not via subprocess
- PostToolUse hooks persist state automatically
- Task state saved to `.claude/state/task_tracker/{terminal_id}_tasks.json`

---

## 12. Framework Comparison (Decision Matrix)

When integrating external frameworks or deciding patterns, reference this comparison:

| Framework | Abstraction | Tool Definition | Execution | State Management | Use When |
|-----------|-------------|-----------------|-----------|------------------|----------|
| **LangChain** | High | `@tool` decorator | AgentExecutor, LangGraph | RunnableConfig, checkpointers | Building complex multi-step agents |
| **Semantic Kernel** | Medium | `@kernel_function` | Kernel orchestration | Context variables | Microsoft ecosystem integration |
| **OpenAI** | Low | JSON Schema | API-driven | Message history | Simple function calling |
| **LlamaIndex** | Medium | `Tool` spec | Agent loops | Graph state | RAG-heavy applications |
| **CrewAI** | High | `@tool` decorator | Sequential/Parallel crews | Shared context | Role-based multi-agent teams |
| **Phidata** | Medium-High | `@tool` decorator | Router/Assistant | Session state | Production assistants |

**Key Insight:** All frameworks converge on **LLM → Tool Orchestration → State → Error Recovery**. Differentiation is mostly abstraction level.

**For Claude Code Skills:** Use SKILL.md + built-in tools. No external framework needed.

---

## 13. Testing Patterns with Code Examples

### Mocked LLM Testing

```python
from langchain.test.fake import FakeChatModel
from langchain_core.messages import AIMessage

# Define fake response with tool call
fake_llm = FakeChatModel(responses=[
    AIMessage(
        content="",
        tool_calls=[{
            "name": "search",
            "args": {"query": "test"},
            "id": "call_123"
        }]
    )
])

# Test agent with deterministic behavior
agent = create_react_agent(fake_llm, tools)
result = agent.invoke({"messages": ["search for test"]})
assert "test" in result["messages"][-1].content
```

### LLM-as-a-Judge Evaluation

```python
def evaluate_agent_output(query: str, response: str) -> dict:
    """Use LLM to evaluate agent response quality"""
    prompt = f"""
Evaluate the following agent response:

Query: {query}
Response: {response}

Score 1-5 on:
- Correctness: Does it answer the question accurately?
- Helpfulness: Is it useful for the user's intent?
- Safety: Does it avoid harmful content?

Return JSON: {{"correctness": N, "helpfulness": N, "safety": N}}
"""
    result = evaluator_llm.call(prompt)
    return json.loads(result)
```

### Multi-Layer Testing Strategy

```
Layer 1: Unit Tests
  - Mocked LLMs
  - Individual tools
  - Fast feedback

Layer 2: Integration Tests
  - Real tools, mocked LLMs
  - Tool interaction validation
  - Medium speed

Layer 3: Evaluation Tests
  - Real LLMs, golden datasets
  - LLM-as-a-judge
  - Slow but comprehensive

Layer 4: Multi-Agent Tests
  - Full system validation
  - End-to-end workflows
  - Slowest
```

---

## 14. Prompt Engineering Patterns

### Modular Prompt Template

```python
interface PromptTemplate {
    role: string           # Agent's role/identity
    context: string[]      # Relevant background info
    task: string           # What to accomplish
    constraints: string[]  # Limitations/rules
    outputFormat: string   # Expected output structure
    examples?: Example[]   # Few-shot examples
}
```

### ReAct Prompt Template

```markdown
You are a {agent_role} with expertise in {domain}.

Use the following format:
Question: {input}
Thought: {thought}
Action: {action}
Action Input: {action_input}
Observation: {observation}
... (repeat Thought/Action as needed)
Thought: I now know the final answer
Final Answer: {answer}
```

### Chain-of-Thought Prompt

```markdown
Question: {question}

Let's think step by step.

1. First, identify what we're being asked to find.
2. Then, determine what information we have.
3. Next, figure out what steps are needed.
4. Finally, work through each step.

Answer:
```

---

## 15. Cross-Cutting Concerns

### Error Handling Patterns

| Pattern | Implementation | Use Case |
|---------|----------------|----------|
| Retry with backoff | `exponential_backoff(retries=3)` | Transient failures |
| Fallback chains | `try_primary() or try_fallback()` | Model failures |
| Error feedback | Return error to LLM for self-correction | Tool errors |
| Circuit breaker | `disable_after_n_failures(n=5)` | Failing APIs |

### Security Considerations

| Concern | Mitigation |
|---------|------------|
| Prompt injection | Wrap user input with delimiters |
| API key exposure | Never log tool arguments |
| Resource exhaustion | Timeouts, rate limits |
| Tool result poisoning | Validate all tool outputs |

### Performance Optimization

| Technique | Impact | Implementation |
|-----------|--------|----------------|
| Parallel tool execution | 3-5x speedup | Call independent tools simultaneously |
| Tool result caching | 100x speedup on repeats | Cache deterministic tool results |
| Streaming responses | Better UX | Stream tokens as generated |
| Token budget management | Prevent overflow | Track context usage, prune old messages |

---

## Quick Checklist

**Before Implementing Resource Templates:**
- [ ] Variants share common workflow
- [ ] Single user-facing entry point desired
- [ ] Direct variant invocation not required
- [ ] Templates remain under 500 lines
- [ ] Clear selection criteria exist

**After Implementation:**
- [ ] Only main skill appears in discovery
- [ ] Each variant accessible via router
- [ ] Templates include proper headers
- [ ] Error handling documented
- [ ] Tests pass for all variants
