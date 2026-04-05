# Answer First Checkpoint

## Rule
Before implementing structural improvements or system changes, verify that you've answered the user's actual question.

## Pattern to Avoid
1. User asks: "find errors from today regarding /s usage"
2. AI searches code files, finds implementation issues
3. AI starts implementing fixes (investigation intent, better error handling)
4. User's original question NEVER gets answered

## Correct Pattern
1. User asks: "find errors from today regarding /s usage"
2. AI searches chat history for /s usage
3. AI reports findings: "Here are the errors/frictions found..."
4. **ONLY THEN** if user asks, implement improvements

## Anti-Pattern Detection
**Danger signs you're implementing instead of answering:**
- "Let me implement X to address this"
- "I'll create a system to..."
- "We should fix Y by..."

**Correct response when asked to investigate:**
- "Here are the errors I found in /s usage..."
- "The friction points are..."
- "Recommendations: 1, 2, 3"

## Session Evidence
- Date: 2026-03-04
- Original request: "find errors from today regarding /s usage and frictions"
- What happened: Implemented investigation intent detection system without answering original question
- User feedback: "I'm confused. What's the list of recommendations?"
- Root cause: AI prioritized structural improvement over answering the immediate question

## Exception
Structural improvements are appropriate WHEN:
- User explicitly asks: "How should we fix this systemically?"
- User asks: "Make this better for future queries"
- User asks: "What patterns would prevent this?"

NOT appropriate when:
- User asks: "What went wrong today?" → Answer first
- User asks: "Find errors from X" → Report findings first
