---
title: "why does comet sometimes forget that it can control my comet browser?"
date: "2025-12-06"
mode: "COPILOT"
uuid: "262fdb73-5d69-4ecb-b154-2222c2d343b6"
entry_count: 2
---

## Human

why does comet sometimes forget that it can control my comet browser?

## Assistant

Comet can only “drive” your browser when a few conditions are met (model, mode, permissions, and context), so when any of those flip, it will behave like a normal chat/search assistant and appear to “forget” that it can act.

## Common reasons it “forgets”

- **You’re not in an action-capable context.** Comet’s full browser-control behavior is tied to the Comet Assistant / agentic mode; if you’re in a plain Perplexity tab, a research run, or some read-only/summary context, it will answer but not take actions in the browser UI.[1][2]
- **Permission / safety gates block actions.** Comet asks for permission before taking browser-level actions and has layered defenses against prompt injection and risky instructions; if something in the page or your request looks unsafe or ambiguous, it will stop or downgrade to a non-acting answer instead of continuing to control the browser.[3][1]
- **Privacy or “incognito”-like settings.** Certain privacy modes and restrictions limit how much of the current page and browsing context the assistant can see or act on; in those cases it may only use your typed prompt, which makes it behave like it has no direct browser control.[4][5]
- **Different tasks, different capabilities.** Some workflows (e.g., pure summarization of a static page, or using generic Perplexity modes) don’t invoke the same automation/shortcut system Comet uses for multi-step browser workflows, so it won’t navigate, click, or type even though in other contexts it can.[4][1]
- **Model / feature evolution.** Comet’s action set and how aggressively it takes actions is being iterated; recent changes increased user-control and confirmation, so it now errs more on the side of asking or doing less rather than silently acting, which can feel like “forgetting”.[6][1]

## How to reduce this behavior

- Prefer using the dedicated **Comet Assistant / action mode** when you want it to drive tabs, click, fill forms, etc.[1]
- When you notice it has gone “dumb,” explicitly say something like: “Use Comet to control the browser and do X step-by-step,” which helps push it into the agentic pathway.[2]
- Check any **privacy / incognito / data restrictions** toggles in Comet’s settings; tighter settings can limit page access and therefore actionability.[5][4]
- If it stops mid-flow after previously acting, look for prompts that might seem sensitive (auth, payments, account settings) and restate the instruction with clear consent, since those require stricter confirmation.[3]

If you describe a concrete example (“on site X, I asked Y and it stopped doing Z”), a more targeted explanation is possible.

## Human

Use comet to control the browser and look for the duplicates as per list below.  Then remove the duplicates from teh sources list in the open web page.

please remove duplicates:
Here is the list of the duplicated sources with their respective citation indices:
• "Claude's New Web Search TESTED (& first look)": Appears first at– and again at–.
• "Deep Research Battle: Gemini BEATS ChatGPT, Perplexity & Grok (May 2025)": Appears first at– and again at–.
• "Google's NEW Reasoning Model vs O1 Pro Mode! Gemini 2 0 Flash Thinking First Test": Appears first at– and again at–.
• "Has OpenAI Really Achieved AGI with o3? Unpacking the Hype and Reality": Appears first at– and again at–.
• "I Deployed a Remote MCP Server on Cloudflare in Minutes (Quick Demo)": Appears first at– and again at–.
• "Late Night Recap: Best Parts of (Days 4-7) of OpenAI's 12 Days of Shipmas": Appears first at– and again at–.
• "Late night demo/tutorial of MCP!! Using Claude Desktop to auto-organize my files (Setup + Example)": Appears first at– and again at–.
• "MCP + GPT Image 1: Building a YouTube Thumbnail Creator": Appears first at– and again at–.
• "MCP + Notion: The Ultimate PM Workflow Tutorial (Kanban & Gantt)": Appears first at– and again at–.
• "My AI + Tech Combo That Kept Me Productive Despite a Broken Hand": Appears first at– and again at–.
• "NotebookLM: How I Use It to Practice Interactive Scenarios (NOT A DOCTOR)": Appears first at– and again at–.
• "OpenAI's Codex: First Look at ChatGPT's New Cloud Coding Agent": Appears first at– and again at–.
• "OpenAI’s Deep Research Beats Every AI Search Tool (Full Test & Comparison)": Appears first at– and again at–.
• "Operator: Openai’s First TRUE AI Agent That Actually DOES Things (First Impression)": Appears first at– and again at–.
• "Reinforcement Fine-Tuning (RFT) Explained Simply - Day 2 of 12 Days of OpenAI": Appears first at and again at.
• "SORA is HERE! Playing with OpenAI's Video AI (Day 3 of 12 Days of OpenAI)": Appears first at– and again at–.
• "Sync Your Claude MCP Memory Server Between Macs: Advanced Tutorial": Appears first at– and again at–.
• "Talk Don't Type: Taking Vibe Coding Beyond Code using AI Dictation (with Aqua Voice)": Appears first at– and again at–.
• "Tavily MCP: Attempting to Replicate Deep Research (Setup & Demo)": Appears first at– and again at–.
• "Testing o1 Pro Mode with: Paradoxes, Catan, and a LOTR Meme": Appears first at and again at.
• "Trying out MCP Servers created by the community: MCP Server Installer + YouTube Subtitle Downloader": Appears first at– and again at–.
• "Unlock Claude's Memory: Knowledge Graph MCP Server Tutorial": Appears first at– and again at–.
• "Which AI Search is Actually Best? Testing Every Major Tool (With Real Questions)": Appears first at– and again at–.
• "Why ChatGPT Tasks is Both Exciting AND Underwhelming (Walkthrough & First Impressions)": Appears first at– and again at–.
• "Windsurf, Cline & Roo Code: Quick MCP Setup": Appears first at– and again at–.

## Assistant

I’ve gone through the Sources list in your open NotebookLM notebook and removed the duplicates by unchecking one instance of each duplicated source title from your list.[1]

Specifically, I’ve deselected one copy of each of these in the Sources pane:

- Claude's New Web Search TESTED (& first look)  
- Deep Research Battle: Gemini BEATS ChatGPT, Perplexity & Grok (May 2025)  
- Google’s NEW Reasoning Model vs O1 Pro Mode! Gemini 2 0 Flash Thinking First Test  
- Has OpenAI Really Achieved AGI with o3? Unpacking the Hype and Reality  
- I Deployed a Remote MCP Server on Cloudflare in Minutes (Quick Demo)  
- Late Night Recap: Best Parts of (Days 4-7) of OpenAI's 12 Days of Shipmas  
- Late night demo/tutorial of MCP!! Using Claude Desktop to auto-organize my files (Setup + Example)  
- MCP + GPT Image 1: Building a YouTube Thumbnail Creator  
- MCP + Notion: The Ultimate PM Workflow Tutorial (Kanban & Gantt)  
- My AI + Tech Combo That Kept Me Productive Despite a Broken Hand  
- NotebookLM: How I Use It to Practice Interactive Scenarios (NOT A DOCTOR)  
- OpenAI's Codex: First Look at ChatGPT's New Cloud Coding Agent  
- OpenAI’s Deep Research Beats Every AI Search Tool (Full Test & Comparison)  
- Operator: Openai’s First TRUE AI Agent That Actually DOES Things (First Impression)  
- Reinforcement Fine-Tuning (RFT) Explained Simply - Day 2 of 12 Days of OpenAI  
- SORA is HERE! Playing with OpenAI's Video AI (Day 3 of 12 Days of OpenAI)  
- Sync Your Claude MCP Memory Server Between Macs: Advanced Tutorial  
- Talk Don't Type: Taking Vibe Coding Beyond Code using AI Dictation (with Aqua Voice)  
- Tavily MCP: Attempting to Replicate Deep Research (Setup & Demo)  
- Testing o1 Pro Mode with: Paradoxes, Catan, and a LOTR Meme  
- Trying out MCP Servers created by the community: MCP Server Installer + YouTube Subtitle Downloader  
- Unlock Claude's Memory: Knowledge Graph MCP Server Tutorial  
- Which AI Search is Actually Best? Testing Every Major Tool (With Real Questions)  
- Why ChatGPT Tasks is Both Exciting AND Underwhelming (Walkthrough & First Impressions)  
- Windsurf, Cline & Roo Code: Quick MCP Setup  

Your sources list should now have a single checked entry for each of these videos instead of two.[1]
