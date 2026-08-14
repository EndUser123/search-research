---
title: "Is there a better prompt that will analyze a chat history, find the unfinished work, and create a prompt that we can giv"
date: "2026-01-31"
mode: "COPILOT"
uuid: "d4ef4b40-727e-49d3-8c71-7b544cb0d463"
entry_count: 2
---

## Human

Is there a better prompt that will analyze a chat history, find the unfinished work, and create a prompt that we can give to another LLM to finish?  Here's what I'm thinking, but I'm sure it's just a first copy:

"what were the main activities in the chat model?
without considering the tasks list in the chat, what tasks are left unfinished?
please create a task list we can hand over to an ai-assistant to fix"

## Assistant

Now I have all the research needed to generate a comprehensive report. Let me create the final answer.

***

## Improved Prompt for Analyzing Chat History & Creating Handoff Tasks

Your initial prompt captures the right intent but lacks analytical structure, explicit criteria for detecting unfinished work, and optimization for LLM handoff. Based on research into conversation analysis, task extraction systems, and multi-agent orchestration patterns, here's a significantly improved approach.

### The Core Problem with Your Current Prompt

Your three-step prompt is functional but exhibits three critical gaps:

1. **Vague detection criteria** – "What tasks are left unfinished?" doesn't specify *how* to identify work that was never explicitly named but emerged from conversation context.
2. **No structured output** – This risks ambiguous parsing and makes it harder for the receiving LLM to reliably extract dependencies or priorities.
3. **Missing implicit analysis** – Work that was discussed but not completed often goes undetected because it wasn't explicitly listed as a task.
4. **Poor handoff optimization** – Without prioritizing recent context, the receiving LLM may lose focus on immediate next steps due to position bias in its context window.

### Recommended Prompt Structure

Here are three versions, ordered by sophistication:

***

### **Version 1: Simple (Direct Replacement)**

```
Analyze this chat history in three phases:

PHASE 1 - NARRATIVE ANALYSIS:
Describe the main activities and goals discussed. What was the user trying to accomplish?

PHASE 2 - UNFINISHED WORK DETECTION:
Go through each activity from Phase 1. For each, ask yourself:
- What did the user explicitly state needed to happen?
- What incomplete steps did they mention?
- What prerequisites were mentioned but not completed?
- What blockers or open questions remain unresolved?

List all unfinished work here, including items that were implied but not formally named as "tasks".

PHASE 3 - HANDOFF BRIEFING:
Create a task list for another AI assistant to continue this work. Format:
- Task name
- Current status (blocked, incomplete, waiting for input)
- Dependencies (what must happen first)
- Immediate next step
- Context needed for the new assistant
```

**Why this works better:**
- Explicitly instructs the LLM to detect implied work (Phase 2)
- Structured output format reduces parsing ambiguity
- Prioritizes immediate next steps for handoff efficiency

***

### **Version 2: Intermediate (Structured with Context)**

```
You are analyzing a development/project conversation to extract unfinished work for handoff.

## STEP 1: Extract the Conversation State
Read the entire chat and answer:
1. What is the top-level goal the user(s) were pursuing?
2. What subtasks or activities were discussed?
3. Which activities appear complete vs. incomplete?

## STEP 2: Detect Implicit Unfinished Work
For each activity, **explicitly ask yourself**:
- Did the user describe it as "done"? If not, it's incomplete.
- What specific next action would move this forward?
- Does this task depend on something else being completed first?
- Were there decision points that were never resolved?

Include activities that were mentioned in passing or as side discussions.

## STEP 3: Determine Task Dependencies & Blockers
Create a map showing:
- Which tasks must be completed before others can begin
- What information or decisions are missing
- What risks or uncertainties remain

## STEP 4: Create the Handoff Briefing
Format each task as a structured entry:

```json
{
  "task_id": "number",
  "name": "Task name",
  "status": "incomplete | blocked | waiting",
  "blockers": ["What's preventing progress?"],
  "dependencies": [ref to other task IDs],
  "priority": "high | medium | low",
  "next_action": "Specific action to take",
  "context": "Why this matters, what was tried before",
  "estimated_effort": "brief estimate"
}
```

IMPORTANT: Surface tasks that were discussed but never explicitly named as "tasks" during the chat.
```

**Why this works better:**
- Structured JSON output enables reliable parsing
- Explicit blockers and dependencies for the next LLM
- Priority classification helps receiving assistant focus
- Captures effort estimates and context

***

### **Version 3: Advanced (Full Context Management + Optimization)**

This version addresses position bias and complex multi-turn scenarios:

```
You are extracting unfinished work from a chat history to hand off to another AI system.

## META-INSTRUCTIONS FOR THIS ANALYSIS:
- Treat all conversation content equally; older messages are as important as recent ones
- Distinguish between explicitly stated tasks vs. implied objectives
- Surface assumptions and decisions that were *assumed* but not made
- Identify questions that were raised but not answered

## STEP 1: CONVERSATION MAPPING
Create a hierarchical map of activities discussed:

```
Main Goal: [top-level objective]
├── Activity A: [what was attempted]
│   ├── Subtask A1: [breakdown]
│   ├── Subtask A2: [breakdown]
│   └── Status: [complete | incomplete | partially started]
├── Activity B: [...]
└── Activity C: [...]
```

## STEP 2: IMPLICIT TASK EXTRACTION
For each activity in the map above, run this checklist:

☐ Was explicit success criteria defined?
☐ Was this activity actually attempted or just discussed?
☐ What stops this from being "done"?
☐ What information is missing to proceed?
☐ Was a decision needed that was never made?
☐ Were follow-ups mentioned that got lost in conversation?

**List every unfinished item**, even if it wasn't named as a formal task.

## STEP 3: DEPENDENCY & BLOCKER ANALYSIS
Map task relationships:
- Task X blocks Tasks Y, Z (these can't start until X is done)
- Task Y is blocked by missing [information/decision/resource]
- Task Z was sidelined; consider whether it's still relevant

## STEP 4: CONTEXT PRESERVATION FOR HANDOFF
Extract the minimum context needed for another LLM to continue:

**Context Layer 1 (Critical - Include First):**
- What is the current blocker?
- What is the immediate next action?
- What decision/info is needed most urgently?

**Context Layer 2 (Important):**
- What was already tried (and failed)?
- What constraints or requirements apply?
- Who/what is involved in dependencies?

**Context Layer 3 (Reference):**
- Full history of decisions made
- Why certain approaches were rejected
- Lessons learned during discussion

## STEP 5: HANDOFF TASK LIST
Generate a prioritized task list using this format:

**[CRITICAL - START HERE]**
Task: [name]
Status: BLOCKED → Blocker: [what's needed]
Next: [one-sentence action]

**[HIGH PRIORITY - DO AFTER CRITICAL]**
Task: [name]
Status: INCOMPLETE
Dependencies: [tasks that must finish first]
Next: [one-sentence action]
Context: [2-3 sentences on what was tried / what matters]

**[MEDIUM PRIORITY]**
[same format]

**[OPEN QUESTIONS / DECISIONS NEEDED]**
- Question 1: [what needs to be decided]
- Question 2: [what's unclear]

---

## FOR THE RECEIVING AI:
This task list is prepared for handoff. Start with CRITICAL items. For each task:
1. Check if the blocker can be resolved (e.g., ask for missing info)
2. If unblocked, execute the "Next" action
3. Refer to Context layer if approach seems unclear
4. Report back on: completion status, new blockers, decisions made
```

**Why this works best:**
- Hierarchical structure prevents context loss (position bias mitigation)
- Explicit checklist ensures comprehensive detection of unfinished work
- Three-layer context model balances completeness with focus
- Task prioritization optimizes receiving LLM's focus
- Ready for programmatic parsing and dependency graph construction

***

### Practical Implementation Advice

**If using with Claude Code or similar:**
- Consider adding a JSON schema output expectation: `"Output as valid JSON with no markdown formatting"`
- Chain two prompts: first extract, second validate: *"Review the task list above. Did we miss anything? Are dependencies correct?"*
- For complex conversations >5K tokens, consider summarizing in a separate pass first, then extracting tasks

**If building a system:**
- Use Version 3 with Pydantic models for deterministic parsing
- Store extracted tasks in a dependency graph (not just a list)
- Track "waiting for input" vs. "blocked" vs. "incomplete" separately
- Re-run the extraction after each handoff completion to detect cascading unfinished work

**Testing your prompt:**
- Compare against the original task list discussed during the chat
- Check for false negatives: tasks mentioned but not extracted
- Verify dependencies are actually correct (ask the LLM to justify them)

***

### Key Improvements Over Your Original

| Aspect | Your Prompt | Improved Version |
|--------|------------|-----------------|
| Unfinished work detection | Asks without criteria | Explicit checklist for implied tasks |
| Output format | Unstructured prose | JSON/structured for parsing |
| Dependency tracking | Not mentioned | Explicit dependency mapping |
| Handoff optimization | Chronological listing | Priority-sorted + blocker-first |
| Context preservation | Single summary | Three-layer model (critical → reference) |
| Position bias handling | No safeguards | Hierarchical mapping resists recency bias |
| Receiving LLM guidance | Assumes understanding | Explicit next-action per task |

Your instinct was correct—this is a critical workflow for agentic AI systems. The improvements above address the academic research on multi-turn conversation failures, position bias in LLMs, and production patterns from systems like LlamaIndex, Google Chat, and Microsoft's Semantic Kernel.[1][2][3][4][5][6][7][8]

## Human

please export your best recommended version as markdown.

## Assistant

Done. The prompt has been exported to  as a markdown file ready to use in your workflow. This is the advanced Version 3 from the report—optimized for multi-turn conversations, dependency tracking, and LLM-to-LLM handoffs.
