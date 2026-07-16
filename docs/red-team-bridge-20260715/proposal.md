# Proposal: ChatGPT-Claude Code Bridge via Lane Controller

Build a bidirectional messaging bridge between Claude Code and a ChatGPT browser
tab, using the ai_lane_controller filesystem-backed store as the spine.

**Components:**
1. ChromeEndpoint - Python + CDP WebSocket. Attaches to a Chrome tab on
   chatgpt.com, injects text via Runtime.evaluate, clicks send, polls DOM for
   the latest assistant message, writes response back to the lane.
2. ClaudeCodeEndpoint - Python + claude_agent_sdk. Polls lane for outbound
   messages, runs each as an SDK query(), writes the structured response back
   to the lane.
3. ai_lane_controller - existing filesystem message store (Milestone 4:
   terminal/session identity, fencing epoch, atomic writes, lock-liveness guard).

**Directions:**
- Claude to ChatGPT: Hook writes to lane. ChromeEndpoint polls, CDP-injects.
- ChatGPT to Claude: ChromeEndpoint polls DOM, writes to lane. SDK daemon
  polls, queries.
- Claude to Claude: Existing lane routing with claims.

**Technology stack:**
- CDP via raw Python websockets + JSON (no Playwright dependency)
- claude_agent_sdk for Claude access (not --print subprocess)
- 1s file-watch polling
- terminal_id/session_id/workspace_id/fencing_epoch identity (Milestone 4)
