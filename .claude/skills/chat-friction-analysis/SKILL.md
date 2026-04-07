---
name: chat-friction-analysis
description: Systematic analysis of chat history to identify problems, errors, friction points, and user corrections.
version: 1.0.0
status: stable
category: analysis
enforcement: advisory
---
# Skill: Chat Friction Analysis

Systematic analysis of chat history to identify problems, errors, friction points, and user corrections. Use whenever the user asks to analyze recent conversations, find LLM mistakes, identify why corrections were needed, or diagnose repeated issues in chat history.

---

## When to Use

Trigger this skill when the user asks:
- "analyze the chat history"
- "find problems in recent messages"
- "why did I have to keep correcting the AI?"
- "identify friction points in conversations"
- "what went wrong in today's session?"
- "show me the errors and corrections from [time period]"

Also use for:
- Retrospective analysis of development sessions
- Identifying systemic issues in AI assistance
- Root cause analysis of repeated corrections
- Quality assessment of LLM interactions

## What This Skill Does

1. **Retrieves chat history** from recent messages (configurable time window)
2. **Identifies friction patterns**: errors, corrections, confused responses, wrong approaches
3. **Categorizes findings** by problem type and root cause
4. **Generates actionable fix plan** with phases, priorities, and acceptance criteria

## Output Format

Produces a markdown plan with:
- **Problem Catalog**: Categorized list of issues found
- **Root Cause Analysis**: Why each problem occurs
- **Implementation Plan**: Phased fixes with priorities
- **Success Metrics**: Measurable improvements

---

## Analysis Workflow

### Phase 1: Retrieve Chat History

Use the `/search` skill to get chat history (auto-detects chat vs web):

```bash
# Default: Recent chat history (auto-detected from query)
/search "recent errors"

# Time-specific queries
/search "what happened yesterday"
/search "last week we discussed"

# Or use the Python script directly for custom time windows
python P:/__csf/src/modules/analysis/chat_search/recent_messages.py -m 1440  # 24 hours
python P:/__csf/src/modules/analysis/chat_search/recent_messages.py -m 60   # 1 hour
python P:/__csf/src/modules/analysis/chat_search/recent_messages.py --auto-detect
```

**If output is too large**, it's saved to a file. Read that file to proceed.

### Phase 2: Pattern Detection

Search for friction indicators in the chat history:

**User Correction Patterns** (grep in history output):
```bash
grep -E "(error|failed|wrong|incorrect|bug|not working|doesn't work|fix|correct|again|stop|wait|no|don't|actually|you're supposed)" chat_history.txt
```

**Key markers to look for**:
- "I disabled hooks" - Hook system friction
- "You are confused" - Context loss
- "enterprise bloat" - Solo-dev mismatch
- "wrong directory" - Path issues
- "why are we getting errors in another terminal?" - Cross-terminal contamination
- "should always allow" - Contract system issues
- "move it to the correct location" - Path confusion
- "approve edit X" (repeated) - Approval loops

### Phase 3: Categorization

Group findings into problem categories:

1. **Hook Contract Friction** - Contract system blocking legitimate work
2. **Context Loss** - Agents not reading before acting
3. **Pattern Mismatch** - Enterprise patterns in solo-dev environment
4. **Path/Directory Issues** - Wrong locations, inconsistent separators
5. **Cross-Terminal Issues** - State bleeding between terminals
6. **Skill Invocation Failures** - Commands not triggering properly
7. **Stale Data** - Recommendations based on outdated information
8. **Repeated Problems** - Same issues recurring without learning

### Phase 4: Root Cause Analysis

For each problem category, identify:

**Symptom**: What the user experienced
**Evidence**: Specific examples from chat (with timestamps/message IDs)
**Root Cause**: Why the system behaves this way
**Impact**: How often it occurs (count per day)

### Phase 5: Generate Fix Plan

Structure the plan with:

**Quick Wins** (1-2 days, high impact):
- User intent bypass
- Context read injection
- Pattern guardrails

**Core Infrastructure** (3-5 days):
- Terminal isolation
- Path validation
- Skill dispatch fixes

**Systemic Improvements** (1 week):
- Live data mode
- Correction tracking
- Context-aware enforcement

For each fix, include:
- **Files to change**: Specific paths
- **What to change**: Code or documentation updates
- **Acceptance criteria**: How to verify it works
- **Success metrics**: Measurable improvements

---

## Problem Detection Patterns

### Hook System Friction
**Markers**: "I disabled hooks", "approve edit X" (repeated), "contract system is stupid"
**Root Cause**: Contract system doesn't distinguish user-directed from autonomous work
**Impact**: User has to disable hooks to get work done

### Context Loss
**Markers**: "You are confused", "failed to understand context", "need a reminder to read last few messages"
**Root Cause**: Agents not reading conversation history before acting
**Impact**: Wrong behavior despite user providing clear direction

### Solo-Dev Mismatch
**Markers**: "enterprise bloat", "team approval", "look in claude.md for our style"
**Root Cause**: Skills suggesting enterprise/team patterns for solo-dev environment
**Impact**: User redirects to CLAUDE.md repeatedly

### Path Issues
**Markers**: "wrong directory", "use '/' not '\\\\'", "move to correct location"
**Root Cause**: No path validation, inconsistent separators
**Impact**: Operations in wrong directories, confusion

### Cross-Terminal Contamination
**Markers**: "errors in another terminal", contract errors in unrelated sessions
**Root Cause**: Shared state without terminal isolation
**Impact**: One terminal's errors bleed into others

### Skill Dispatch Failures
**Markers**: "you didn't call Skill", "this isn't true, I give slash commands"
**Root Cause**: Slash commands not triggering Skill() calls
**Impact**: Commands don't work as expected

### Stale Data
**Markers**: "old data", "non-compliance", "maybe looking at cached data"
**Root Cause**: Skills using caches instead of live reads
**Impact**: Recommendations based on outdated information

### Repeated Problems
**Markers**: "same problem again", "we keep having this issue", "figure out what code needs updating first"
**Root Cause**: No learning loop from corrections
**Impact**: Same corrections needed multiple times

---

## Output Template

Use this structure for the analysis report:

```markdown
# Chat Friction Analysis Report

**Analysis Period**: [date range]
**Messages Analyzed**: [count]
**Analysis Date**: [current date]

---

## Problem Catalog

### Problem 1: [Name]
**Frequency**: [count] occurrences
**Examples**:
- [Timestamp]: [Quote from chat]
- [Timestamp]: [Quote from chat]

**Root Cause**: [Why this happens]

**Impact**: [How it affects workflow]

---

## Root Cause Summary

[Summary of all root causes with counts]

---

## Implementation Plan

### Phase 1: Quick Wins (1-2 days)
[Fixes with high impact, low effort]

### Phase 2: Core Infrastructure (3-5 days)
[Foundational fixes]

### Phase 3: Systemic Improvements (1 week)
[Prevention and learning systems]

---

## Success Metrics

- **User corrections**: Reduce from [current]/day to [target]/day ([X]% reduction)
- **Hook disable frequency**: Reduce from [current]/day to [target]/day
- **[Specific metric]**: [Target improvement]

---

## Open Questions

1. [Question with proposed answer]
2. [Question with proposed answer]

---

## Next Steps

1. [Immediate action]
2. [Planning action]
3. [Implementation action]
```

---

## Tips for Effective Analysis

1. **Count everything**: Track frequency of each problem type
2. **Quote directly**: Use exact quotes from chat history with timestamps
3. **Look for patterns**: Same complaint appearing multiple times = systemic issue
4. **Prioritize by frequency**: Fix problems that occur most often first
5. **Consider impact**: A rare but severe problem might need priority over frequent minor issues

---

## Examples

### Example 1: Daily Review
**User**: "Analyze today's chat history for problems"
**Skill action**:
1. Run `/recent` with 1440 minutes (24 hours)
2. Grep for correction patterns
3. Categorize findings
4. Generate fix plan

### Example 2: Specific Issue Investigation
**User**: "Why do I keep having to disable hooks?"
**Skill action**:
1. Search chat for "disabled hooks"
2. Find all hook-related complaints
3. Identify root causes
4. Propose targeted fixes

### Example 3: Retrospective Analysis
**User**: "What went wrong this week?"
**Skill action**:
1. Run `/recent` with 10080 minutes (7 days)
2. Aggregate all problem types
3. Identify trends and recurring issues
4. Generate comprehensive improvement plan

---

## Compatibility

**Required tools**:
- Bash (for `/recent` and grep commands)
- Read (for reading history files)
- Write (for generating report)

**Optional tools**:
- Grep (for pattern searching)
- Skill tool (for invoking `/recent`)

**Dependencies**:
- `P:/__csf/src/modules/analysis/chat_search/recent_messages.py` must exist
- Chat history must be accessible
