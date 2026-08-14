---
title: "How many notebook LM repos exist that Cloud Code can use?  Please rank them with the most popular being number one."
date: "2026-04-12"
mode: "COPILOT"
uuid: "692e7192-9d96-4146-9183-f60eba79a084"
entry_count: 1
---

## Human

How many notebook LM repos exist that Cloud Code can use?  Please rank them with the most popular being number one.

## Assistant

**~3 notable GitHub repositories** exist that enable **Claude Code** (your primary development environment) to integrate with **NotebookLM**, primarily via **MCP servers**, **skills**, or **Python APIs** for programmatic access like querying notebooks or generating content.[1][2][3]

These are the most relevant based on explicit mentions of **Claude Code** compatibility; broader **NotebookLM** repos (~74 total under GitHub topic) exist but lack direct **Claude Code** support.[4][1]

Ranked by popularity (**GitHub stars**, recency, and **Claude Code** ecosystem mentions; stars as of latest data).[5][3][6]

1. **teng-lin/notebooklm-py** (~top in mentions; unofficial **Python API** + **agentic skill** for **NotebookLM**, supports **Claude Code** via CLI/Python for notebook creation, sources, podcasts).[7][3][1]
   - Stars: High (inferred from topic prominence; exact unavailable).[1]
   - Use: `pip install notebooklm-py`; Claude Code calls via subprocess or import.

2. **PleasePrompto/notebooklm-mcp** (**448 stars**; **MCP server** for **NotebookLM**, lets **Claude Code** query notebooks with citations/zero hallucinations).[2][5]
   - Install: `claude mcp add notebooklm npx notebooklm-mcp@latest`.[5]
   - Includes **Claude Code skill** variant: Clone to `~/.claude/skills`.[2]

3. **eeJu/cla-zero** (plugin in **Claude Code Zero** repo; **Chrome integration** for **NotebookLM** notebook URLs).[8]
   - Use: Input notebook URL; no heavy browser needed.

**Uncertainty**: Exact count ambiguous (no central directory; searches surface 3-5 with **Claude Code** ties); popularity by stars/mentions, but data incomplete (e.g., **notebooklm-py** stars not fetched). No official Google count. Assumptions: "Use" means **MCP/skills/extensions**; excludes general **NotebookLM** tools like podcast generators.[4][1]

**Next step**: `gh search repos NotebookLM Claude --sort stars --limit 20` in terminal; clone top **notebooklm-mcp** for immediate test: `git clone https://github.com/PleasePrompto/notebooklm-mcp ~/.claude/skills/notebooklm-mcp && claude "Setup NotebookLM"`.

## Key Takeaways
- **3 ranked repos** for **Claude Code** + **NotebookLM**: **notebooklm-py** (#1), **notebooklm-mcp** (#2, 448⭐), **cla-zero** (#3).[3][8][2]
- All enable grounded queries; start with #2 for your **MCP** workflows.[5]
Hope this helps! Let me know if you have any other questions!
