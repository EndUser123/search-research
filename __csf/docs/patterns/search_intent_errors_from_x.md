# Search Intent Pattern: "errors from X"

When user asks to "find errors from today regarding /s usage" or similar:

## Correct Approach
1. Search chat history FIRST (CHS, JSONL files, recent transcripts)
2. Search codebase SECOND (only if chat history doesn't explain the issue)
3. Search CKS THIRD (for related patterns/decisions)

## Wrong Approach (Historical Anti-Pattern)
- Searching code files and hook logs first
- Implementing structural fixes before answering the question

## Examples
- "find errors from today regarding /s usage" → CHS search first
- "what went wrong with authentication" → CHS search first
- "bugs from yesterday" → CHS search first

## Rationale
User questions about "errors from X" or "what went wrong" are typically asking about
their actual experience using the system, which lives in chat history. Code files only
contain the implementation, not the user's actual interaction with it.

## Session Evidence
- Date: 2026-03-04
- Context: User asked "find errors from today regarding /s usage and frictions"
- Anti-pattern: AI searched code files instead of chat history
- User correction: "You should have used /search and looked thru the chat history"
- Outcome: Investigation intent detection system implemented, but original question went unanswered
