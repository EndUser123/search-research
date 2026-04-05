# LLM Handoff Protocol

You are receiving a handoff from another LLM session. The handoff data is in JSON format below.

## Instructions

1. Read the JSON handoff data completely
2. Understand the context, decisions made, and current state
3. Note any bridge tokens for cross-session decision continuity
4. Check the quality score - if <0.7, ask user what needs to be documented
5. Continue work based on the "next_steps" or user's new request

## Handoff Data

```json
<<<HANDOFF_JSON>>>
```

## Quick Reference

- **Session ID**: `session_id` from above
- **Quality Score**: `quality_score` (0-1, higher is better)
- **Current Blocker**: `blocker.description` if present
- **Bridge Tokens**: Check `handover.decisions[].bridge_token` for cross-session references
- **Last Work**: See `modifications` for files changed
- **Next Steps**: See `next_steps` array

## After Reading

Acknowledge the handoff by summarizing:
1. What was being worked on
2. Current blocker or status
3. Any bridge tokens you should respect
4. Ready to proceed with user's request
