Analyze whether the PreToolUse efficiency layer for comparative claim guarding should be built.

CONTEXT:
- Stop_comparative_claim_guard.py is deployed and working (Stop-only layer)
- PreToolUse payload schema: {tool_name, tool_input, session_id, terminal_id}
- PreToolUse does NOT expose: current_context (planned response), tool_history (accumulated reads)
- Stop hook schema: {assistant_response, tool_events[], transcript_path, session_id, terminal_id}

QUESTION: Can a PreToolUse layer work within these constraints, or is Stop-only the correct final design?

KEY FINDINGS FROM PRIOR SESSION:
- PreToolUse phase fires before each tool, one at a time
- Once LLM finishes reading and starts drafting, no more PreToolUse fires
- Stop fires once at turn end on the complete response
- The transcript_path in Stop gives access to accumulated session history
- The Stop hook already tried to read JSONL transcripts but had timing issues

STOP-ONLY ARCHITECTURE ADVANTAGES:
1. Complete context: sees full response and all tool events
2. Can compare response content against verified files
3. transcript_path enables cross-turn reasoning
4. Schema naturally supports comparative analysis

STOP-ONLY ARCHITECTURE DISADVANTAGES:
1. Fires AFTER response generation (reactive, not preventive)
2. User sees wrong response before block fires
3. Wastes token generation on content that gets blocked

PRETOOLUSE CHALLENGES (given schema):
1. No accumulated history per turn
2. No planned response context
3. Cannot compare "what I'm about to say" vs "what I've read"

POSSIBLE PRETOOLUSE APPROACHES CONSIDERED:
- PreToolUse writes state file after Read, Stop reads it
- But timing: PreToolUse fires before Read completes, so state not yet written
- Session transcript JSONL has timing issues (written after each turn)