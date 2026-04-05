# Conversation Patterns Reference

Detailed user feedback and conversation flow patterns for `/gto` skill analysis.

---

## User Feedback Patterns

### Positive Signals
- "That's correct"
- "Good job"
- "Perfect"
- "Thanks, that works"
- "Exactly what I needed"
- Approval phrases

**Indicates**: Approach is working, user is satisfied

### Negative Signals
- "That's wrong"
- "No, that's not what I asked for"
- "You're missing something"
- "That's backwards"
- Correction phrases
- "Not what I meant"

**Indicates**: Approach needs correction, clarify requirements

### Frustration Signals
- "bullshit"
- "wrong"
- "insane"
- "you're missing something"
- Repeated corrections on same topic (3+ times)
- "stop doing X"

**Indicates**: User frustration, learning gap, anti-pattern detected

---

## Learning Signals

### Successful Patterns
- User approved approach 3+ times → Pattern candidate for SKILL.md
- "Do X instead of Y" → Learning opportunity
- Correction that worked → Pattern to document
- Solution that satisfied user → Best practice

**Action**: Document in appropriate SKILL.md or memory

### Anti-Patterns
- User rejected approach 3+ times → Anti-pattern to avoid
- "Don't do X" → Negative pattern
- Repeated mistakes → Learning gap
- Workaround over root fix → Technical debt

**Action**: Document as anti-pattern, avoid recurrence

---

## Session Flow Analysis Patterns

### Dropped Topics
- Subject changed without resolution
- Question asked but never answered
- Issue raised but not addressed
- User gave up on a topic (stopped pursuing after 2+ attempts)

**Detection**: Track topic changes, look for unresolved questions

### Context Switches
- Sudden topic changes
- Unrelated work interleaved
- Attention fragmentation

**Detection**: Identify abrupt subject changes in conversation

### Conversation Anti-Patterns

#### Questions Dodged
- Claude answered different question than asked
- Provided solution without addressing core issue

**Detection**: Compare question asked vs response given

#### User Gave Up
- User stopped pursuing after 2+ attempts
- Unresolved issue abandoned

**Detection**: Look for "never mind" or topic changes after failed attempts

#### Circular Discussions
- Same point repeated 3+ times
- No progress made on issue

**Detection**: Track repeated statements without resolution

#### Scope Creep
- Additional tasks added without discussion
- Requirements expanded mid-conversation

**Detection**: Compare initial request to final deliverables

---

## Requirements Ambiguity Detection

### Ambiguity Signals
- "What do you mean?"
- "I don't understand"
- "That's not clear"
- Multiple clarifications needed
- User rejected implementation due to misunderstanding

### Missing Context
- User provided incomplete instructions
- Assumptions made that were wrong
- Missing file paths or references
- Unclear success criteria

**Action**: Ask clarifying questions before implementing

---

## Common Anti-Patterns

### Workaround Over Root Cause

**Pattern**: Proposing workarounds instead of fixing underlying issue

**Examples**:
- Creating hookify rules to "prevent" errors instead of fixing hooks
- Adding configuration flags to disable broken behavior
- Creating wrapper functions to hide errors

**User Feedback Signals**:
- "why don't you figure out what's actually broken?"
- "stop adding patches and fix the root cause"
- "this is a workaround, not a fix"

**Root Cause Investigation Process**:
1. Identify blocking component (hook, file, function)
2. Read source code to understand actual behavior
3. Trace execution path to find failure point
4. Fix at the source (modify hook, fix logic, correct error)
5. Verify fix works (test actual scenario)

**Severity**: High - workarounds accumulate technical debt
