---
title: "Does this prompt look ok?  How do we update it so you export as markdown?
You are extracting unfinished work from a chat"
date: "2026-01-31"
mode: "COPILOT"
uuid: "94552950-f6f1-4d78-b11b-44a299a52ef5"
entry_count: 1
---

## Human

Does this prompt look ok?  How do we update it so you export as markdown?
You are extracting unfinished work from a chat history to hand off to another AI system.

META-INSTRUCTIONS FOR THIS ANALYSIS
Treat all conversation content equally; older messages are as important as recent ones

Distinguish between explicitly stated tasks vs. implied objectives

Surface assumptions and decisions that were assumed but not made

Identify questions that were raised but not answered

STEP 1: CONVERSATION MAPPING
Create a hierarchical map of activities discussed:

text
Main Goal: [top-level objective]
├── Activity A: [what was attempted]
│   ├── Subtask A1: [breakdown]
│   ├── Subtask A2: [breakdown]
│   └── Status: [complete | incomplete | partially started]
├── Activity B: [...]
└── Activity C: [...]
STEP 2: IMPLICIT TASK EXTRACTION
For each activity in the map above, run this checklist:

☐ Was explicit success criteria defined?

☐ Was this activity actually attempted or just discussed?

☐ What stops this from being "done"?

☐ What information is missing to proceed?

☐ Was a decision needed that was never made?

☐ Were follow-ups mentioned that got lost in conversation?

List every unfinished item, even if it wasn't named as a formal task.

STEP 3: DEPENDENCY & BLOCKER ANALYSIS
Map task relationships:

Task X blocks Tasks Y, Z (these can't start until X is done)

Task Y is blocked by missing [information/decision/resource]

Task Z was sidelined; consider whether it's still relevant

STEP 4: CONTEXT PRESERVATION FOR HANDOFF
Extract the minimum context needed for another LLM to continue:

Context Layer 1 (Critical - Include First):

What is the current blocker?

What is the immediate next action?

What decision/info is needed most urgently?

Context Layer 2 (Important):

What was already tried (and failed)?

What constraints or requirements apply?

Who/what is involved in dependencies?

Context Layer 3 (Reference):

Full history of decisions made

Why certain approaches were rejected

Lessons learned during discussion

STEP 5: HANDOFF TASK LIST
Generate a prioritized task list using this format:

[CRITICAL - START HERE]
Task: [name]
Status: BLOCKED → Blocker: [what's needed]
Next: [one-sentence action]

[HIGH PRIORITY - DO AFTER CRITICAL]
Task: [name]
Status: INCOMPLETE
Dependencies: [tasks that must finish first]
Next: [one-sentence action]
Context: [2-3 sentences on what was tried / what matters]

[MEDIUM PRIORITY]
Task: [name]
Status: [status]
Dependencies: [if any]
Next: [one-sentence action]
Context: [brief context]

[OPEN QUESTIONS / DECISIONS NEEDED]
Question 1: [what needs to be decided]

Question 2: [what's unclear]

FOR THE RECEIVING AI
This task list is prepared for handoff. Start with CRITICAL items. For each task:

Check if the blocker can be resolved (e.g., ask for missing info)

If unblocked, execute the "Next" action

Refer to Context layer if approach seems unclear

Report back on: completion status, new blockers, decisions made

## Assistant

This is a solid prompt framework for extracting unfinished work from chat histories. I'll review it and provide a markdown-optimized version with improvements for clarity and exportability.

## Analysis of Current Prompt

**Strengths:**
- Clear hierarchical thinking (5-step process)
- Explicit distinction between stated vs. implied work
- Strong focus on blockers and dependencies
- Context-layering approach for handoffs is sophisticated
- Checklists make it actionable

**Areas for Improvement:**

1. **Markdown export optimization**: The current version uses mixed formatting (ASCII boxes, inline checklists). Markdown tables would be clearer for tasks and dependencies.

2. **Ambiguity in execution**: "STEP 2" checklist is meant for human/LLM review, but it's not clear whether the output should be checklist format or narrative.

3. **Context layers**: The 3-layer structure is good, but the formatting for "STEP 4" output isn't specified clearly for markdown export.

4. **Task list format**: The bracketed priority labels could use markdown heading hierarchy for better document structure.

***

## Updated Markdown-Exportable Prompt

```markdown
# Unfinished Work Extraction & Handoff Analysis

## META-INSTRUCTIONS
- Treat all conversation content equally; older messages are as important as recent ones
- Distinguish between explicitly stated tasks vs. implied objectives
- Surface assumptions and decisions that were assumed but not made
- Identify questions that were raised but not answered

---

## STEP 1: CONVERSATION MAPPING

Create a hierarchical map of activities discussed:

### [Main Goal]
- **Activity A**: [what was attempted]
  - Subtask A1: [breakdown]
  - Subtask A2: [breakdown]
  - Status: complete | incomplete | partially started
- **Activity B**: [...]
- **Activity C**: [...]

---

## STEP 2: IMPLICIT TASK EXTRACTION

For each activity in the map above, evaluate:

| Criterion | Analysis |
|-----------|----------|
| Success criteria defined? | ☐ Yes ☐ No ☐ Unclear |
| Activity attempted or just discussed? | ☐ Attempted ☐ Discussed ☐ Not started |
| What stops this from being "done"? | [specific blocker] |
| Information missing to proceed? | [list gaps] |
| Unresolved decision needed? | [what needs deciding] |
| Follow-ups lost in conversation? | [list forgotten threads] |

**Unfinished Items** (including unnamed tasks):
- Item 1: [description]
- Item 2: [description]

---

## STEP 3: DEPENDENCY & BLOCKER ANALYSIS

| Task | Blocks | Blocked By | Notes |
|------|--------|-----------|-------|
| Task X | Tasks Y, Z | [missing info/decision] | [reason sidelined or ongoing] |
| Task Y | Task Z | [resource/decision] | [reason] |

---

## STEP 4: CONTEXT PRESERVATION FOR HANDOFF

### Critical Context (Start Here)
- **Current Blocker**: [what's stopping progress]
- **Immediate Next Action**: [one-sentence action]
- **Most Urgent Need**: [decision/info/resource needed]

### Important Context
- **What Was Tried (and Failed)**: [approaches and outcomes]
- **Constraints & Requirements**: [any limitations or rules]
- **Dependencies & Stakeholders**: [who/what is involved]

### Reference Context
- **Key Decisions Made**: [summary of choices and rationale]
- **Rejected Approaches**: [why certain paths were abandoned]
- **Lessons Learned**: [insights from discussion]

---

## STEP 5: HANDOFF TASK LIST

### 🔴 CRITICAL - START HERE

| Task | Status | Blocker | Next Action | Context |
|------|--------|---------|-------------|---------|
| [Name] | BLOCKED | [specific blocker] | [one-sentence action] | [2-3 sentences on what was tried / constraints] |

### 🟠 HIGH PRIORITY - DO AFTER CRITICAL

| Task | Status | Dependencies | Next Action | Context |
|------|--------|--------------|-------------|---------|
| [Name] | INCOMPLETE | [tasks that must finish first] | [one-sentence action] | [2-3 sentences on what was tried / what matters] |

### 🟡 MEDIUM PRIORITY

| Task | Status | Dependencies | Next Action | Context |
|------|--------|--------------|-------------|---------|
| [Name] | [status] | [if any] | [one-sentence action] | [brief context] |

### ❓ OPEN QUESTIONS / DECISIONS NEEDED

1. **Question 1**: [what needs to be decided]
2. **Question 2**: [what's unclear]
3. **Question 3**: [what's contested or uncertain]

---

## FOR THE RECEIVING AI

This task list is prepared for handoff. Use this workflow:

1. **Review Critical items first** → Check if blockers can be resolved
2. **Ask for clarification** if needed (missing info, unclear dependencies)
3. **If unblocked**, execute the "Next" action in the task
4. **Refer to Context layers** if approach seems unclear
5. **Report back** on: completion status, new blockers, decisions made

---

## EXPORT NOTES

This markdown document can be:
- Exported directly as `.md` file
- Converted to HTML, PDF, or Word via pandoc or markdown tools
- Imported into task management systems (task tables are copy-friendly)
- Version-controlled in Git for iteration tracking
```

***

## Key Improvements for Markdown Export

| Change | Why |
|--------|-----|
| Heading hierarchy (`#`, `##`, `###`) | Better document structure and TOC generation |
| Markdown tables for checklists & tasks | Easier parsing, copy-paste into tools, better alignment |
| Priority indicators (🔴🟠🟡) | Visual scannability without losing markdown portability |
| Removed ASCII boxes | Cleaner markdown, renders uniformly across platforms |
| Explicit "EXPORT NOTES" section | Clarifies output format and tool compatibility |
| Consistent `| | |` table structure | All data is now row-based, easier to programmatically process |

This version maintains all the conceptual rigor of your original while being natively markdown-friendly and export-ready.
