# Agentic AI Skills: Research Reference

**Status:** DEPRECATED - Content migrated to operational and conceptual guides

**Migration Notice:** This document has been split and merged into:
- `__csf/docs/claude_skills_operational_guide.md` - Implementation patterns, code examples, testing
- `__csf/docs/claude_skills_and_agentic_patterns.md` - Theory, principles, research sources

**Research Date:** 2026-02-03
**Original Purpose:** Complete reference for building and understanding agentic AI skills

---

## Content Migration Status

| Section | Destination | Status |
|---------|-------------|--------|
| Executive Summary | conceptual_guide.md | ✅ Migrated |
| Claude Code Skills Architecture | operational_guide.md | ✅ Migrated |
| Design Patterns | conceptual_guide.md | ✅ Migrated |
| Framework Comparison | operational_guide.md | ✅ Migrated |
| Testing and Validation | operational_guide.md | ✅ Migrated |
| Prompt Engineering Patterns | operational_guide.md | ✅ Migrated |
| Implementation Guide (Section 6) | DELETED | ❌ Obsolete pattern |
| Cross-Cutting Concerns | operational_guide.md | ✅ Migrated |
| Recommended Resources | conceptual_guide.md | ✅ Migrated |

**Why Section 6 was deleted:** The standalone Python handler pattern is incorrect for Claude Code skills. See operational_guide.md Section 0 for the correct documentation-driven pattern.

---

## Original Content (Archive Only)

This document is kept for archival purposes. All operational and conceptual content has been migrated to the appropriate guides.

---

## Executive Summary (ARCHIVE)

This report synthesizes research across five domains critical to agentic AI skill development:

1. **Claude Code Skills** - Official patterns for skill structure and execution
2. **Design Patterns** - 10 core patterns from academic and industry sources
3. **Frameworks** - 8 major frameworks compared with implementation patterns
4. **Testing Approaches** - Multi-layer testing, evaluation, and validation
5. **Prompt Engineering** - Template systems, ReAct, CoT, and structured output

**Key Finding:** All agentic systems converge on a core architecture: **LLM as Controller → Tool/Function Orchestration → State Management → Error Recovery**. The primary differentiators are abstraction levels, state management approaches, and multi-agent coordination capabilities.

---

## Table of Contents

1. [Claude Code Skills Architecture](#1-claude-code-skills-architecture)
2. [Design Patterns (10 Core Patterns)](#2-design-patterns)
3. [Framework Comparison](#3-framework-comparison)
4. [Testing and Validation](#4-testing-and-validation)
5. [Prompt Engineering Patterns](#5-prompt-engineering-patterns)
6. [Implementation Guide for `/task` Skill](#6-implementation-guide-for-task-skill)
7. [Cross-Cutting Concerns](#7-cross-cutting-concerns)
8. [Recommended Resources](#8-recommended-resources)

---

## 1. Claude Code Skills Architecture

### 1.1 Skill Structure

**Required Frontmatter:**
```yaml
---
name: skill-name
description: Brief description of what the skill does
category: planning|workflow|analysis|etc.
triggers:
  - /skill-name
aliases:
  - /alias
suggest:
  - /related-skill
---
```

**Skill File Locations:**
```
.claude/skills/
├── skill-name/
│   └── SKILL.md          # Main skill file
├── skill-name-fast/       # Variant (internal: true)
│   └── SKILL.md
└── skill-name-deep/       # Variant (internal: true)
    └── SKILL.md
```

### 1.2 Skill Execution Model

```
User invokes /skill → Skill tool loads SKILL.md →
Parse frontmatter → Execute workflow → Return result
```

**Key Points:**
- Skills are documentation-driven (SKILL.md contains the workflow)
- Built-in tools (TaskCreate, TaskUpdate, etc.) are called via tool system
- Hooks provide pre/post processing (PreToolUse, PostToolUse)
- State persistence via `.claude/state/task_tracker/`

### 1.3 Built-in Tools Reference

| Tool | Purpose | Parameters |
|------|---------|------------|
| `TaskCreate` | Create new task | subject, description, status |
| `TaskUpdate` | Update existing task | taskId, status, addBlocks, addBlockedBy |
| `TaskGet` | Get task details | taskId |
| `TaskList` | List all tasks | - |
| `Read` | Read file | file_path, offset, limit |
| `Write` | Write file | file_path, content |
| `Edit` | Edit file | file_path, old_string, new_string |
| `Bash` | Execute shell command | command |
| `Skill` | Invoke another skill | skill, args |

---

## 2. Design Patterns

### 2.1 Pattern Overview

| # | Pattern | Purpose | Complexity | Latency |
|---|---------|---------|------------|---------|
| 1 | **ReAct** | Reasoning + Acting | Low | Medium |
| 2 | **Routing/Dispatch** | Intent-based variant selection | Low | Low |
| 3 | **Multi-Agent (Sequential)** | Pipeline of specialists | Medium | High |
| 4 | **Multi-Agent (Hierarchical)** | Supervisor + workers | High | High |
| 5 | **Reflection/Self-Correction** | Critique own outputs | Medium | High |
| 6 | **Memory Management** | Context persistence | Medium | Low |
| 7 | **Planning/Execution** | Plan then execute | Medium | High |
| 8 | **Tool Use** | External API integration | Medium | Low |
| 9 | **State Machine** | Predictable workflows | High | Low |
| 10 | **Human-in-the-Loop** | Approval gates | High | Very High |

### 2.2 ReAct Pattern

**Template:**
```
Question: {input}
Thought: I should think about what to do
Action: {tool_name}
Action Input: {tool_arguments}
Observation: {tool_result}
... (repeat)
Thought: I now know the final answer
Final Answer: {answer}
```

### 2.3 Routing Pattern

```python
class AgentRouter:
    def __init__(self, routes: dict):
        self.routes = routes

    async def route(self, query: str):
        # Intent classification
        decision = classify_intent(query)
        # Route to appropriate agent
        agent = self.routes.get(decision, self.routes["default"])
        return await agent.ainvoke(query)
```

---

## 3. Framework Comparison

| Framework | Abstraction | Skill Definition | Execution | State Management |
|-----------|-------------|------------------|-----------|------------------|
| **LangChain** | High | `@tool` decorator | AgentExecutor, LangGraph | RunnableConfig, checkpointers |
| **Semantic Kernel** | Medium | `@kernel_function` | Kernel orchestration | Context variables |
| **OpenAI** | Low | JSON Schema | API-driven | Message history |
| **LlamaIndex** | Medium | `Tool` spec | Agent loops | Graph state |
| **CrewAI** | High | `@tool` decorator | Sequential/Parallel crews | Shared context |
| **Phidata** | Medium-High | `@tool` decorator | Router/Assistant | Session state |

---

## 4. Testing and Validation

### 4.1 Multi-Layer Testing

```
Layer 1: Unit Tests (Mocked LLMs)
Layer 2: Integration Tests (Real tools, mocked LLMs)
Layer 3: Evaluation Tests (Real LLMs, golden datasets)
Layer 4: Multi-Agent Tests
```

### 4.2 Mocked LLM Testing

```python
from langchain.test.fake import FakeChatModel

fake_llm = FakeChatModel(responses=[
    AIMessage(content="", tool_calls=[{"name": "search", "args": {"query": "test"}}])
])

agent = create_react_agent(fake_llm, tools)
result = agent.invoke({"messages": ["search for test"]})
```

### 4.3 LLM-as-a-Judge

```python
def evaluate_agent_output(query: str, response: str) -> dict:
    prompt = f"""
    Evaluate: {query}
    Response: {response}
    Score 1-5 on: Correctness, Helpfulness, Safety
    """
    return json.loads(evaluator_llm.call(prompt))
```

---

## 5. Prompt Engineering Patterns

### 5.1 Modular Template

```python
interface PromptTemplate {
    role: string
    context: string[]
    task: string
    constraints: string[]
    outputFormat: string
    examples?: Example[]
}
```

### 5.2 ReAct Prompt

```
You are a {agent_role} with expertise in {domain}.

Use the following format:
Question: {input}
Thought: {thought}
Action: {action}
Action Input: {action_input}
Observation: {observation}
...
Final Answer: {answer}
```

### 5.3 Chain-of-Thought

```
Question: {question}
Let's think step by step.
```

---

## 6. Implementation Guide for `/task` Skill

### 6.1 Handler Implementation

```python
class TaskHandler:
    def __init__(self):
        self.commands = {
            "list": self.handle_list,
            "add": self.handle_add,
            "done": self.handle_done,
            "start": self.handle_start,
            "search": self.handle_search,
            "clean": self.handle_clean,
            "help": self.handle_help
        }

    def handle_list(self, args: list) -> None:
        """List all tasks with optional status filter"""
        status_filter = None
        if args and args[0].startswith("--status="):
            status_filter = args[0].split("=")[1]

        tasks = TaskList()
        print("=== Task List ===")
        for task in tasks:
            if status_filter and task.get("status") != status_filter:
                continue
            print(f"#{task['id']} [{task['status']}] {task['subject']}")

    def handle_add(self, args: list) -> None:
        """Create new task"""
        if not args:
            print("Error: Subject required")
            return

        subject = " ".join(args)
        result = TaskCreate(
            subject=subject,
            description=f"Created via /task",
            status="pending"
        )
        print(f"Task created: {result}")

    def handle_done(self, args: list) -> None:
        """Mark task as complete"""
        if not args:
            print("Error: Task ID required")
            return

        task_id = args[0]
        TaskUpdate(taskId=task_id, status="completed")
        print(f"Task {task_id} marked as completed")

    def execute(self) -> int:
        """Main entry point"""
        if len(sys.argv) < 2:
            self.handle_help([])
            return 0

        command = sys.argv[1]
        args = sys.argv[2:]

        if command not in self.commands:
            print(f"Unknown command: {command}")
            self.handle_help([])
            return 1

        self.commands[command](args)
        return 0
```

---

## 7. Cross-Cutting Concerns

### 7.1 Error Handling

| Pattern | Use Case |
|---------|----------|
| Retry with exponential backoff | Transient failures |
| Fallback chains | Model failures |
| Error feedback to LLM | Tool errors |
| Circuit breaker | Failing APIs |

### 7.2 Security

| Concern | Mitigation |
|---------|------------|
| Prompt injection | Delimiter wrapping |
| API key exposure | Never log arguments |
| Resource exhaustion | Timeouts, rate limits |
| Tool result poisoning | Validate outputs |

### 7.3 Performance

| Technique | Impact |
|------------|--------|
| Parallel tool execution | 3-5x speedup |
| Tool result caching | 100x speedup |
| Streaming responses | Better UX |
| Token budget management | Prevent overflow |

---

## 8. Recommended Resources

### Academic Papers

1. "ReAct: Synergizing Reasoning and Acting in Language Models" - arXiv:2210.03629
2. "Reflexion: Language Agents with Verbal Reinforcement Learning" - arXiv:2303.11366
3. "MemGPT: Towards LLMs as Operating Systems" - arXiv:2310.08560
4. "Toolformer: Language Models Can Teach Themselves to Use Tools" - arXiv:2302.04761
5. "AgentBench: Evaluating LLMs as Agents" - arXiv:2308.03688

### Official Documentation

| Resource | URL |
|----------|-----|
| Anthropic Agent Design | docs.anthropic.com |
| Google Cloud Agentic AI | cloud.google.com |
| LangChain | python.langchain.com |
| LangGraph | langchain-ai.github.io/langgraph |
| OpenAI Function Calling | platform.openai.com/docs/guides/function-calling |
| Semantic Kernel | learn.microsoft.com/en-us/semantic-kernel |

### Open Source

| Project | URL |
|---------|-----|
| LangChain | github.com/langchain-ai/langchain |
| Semantic Kernel | github.com/microsoft/semantic-kernel |
| BabyAGI | github.com/yoheinakajima/babyagi |
| AutoGPT | github.com/Significant-Gravitas/AutoGPT |
| CrewAI | github.com/joaomdmoura/crewAI |

---

**Document Version:** 1.0
**Last Updated:** 2026-02-03
**Total Sources:** 50+ academic papers, official docs, and GitHub repositories
