---
title: "Claude Code Multi-Agent Collaboration Patterns"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, claude]
summary: >
  Claude Code supports hierarchical agent spawning where a top-level orchestrator delegates tasks to sub-agents up to five levels deep, enabling complex collaborative workflows across teams and development environments.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook fff42c44-d4ba-474a-93f7-7384bd536a1b" (WL: Health & Weight Loss, synced 2026-07-27)
  - "NotebookLM source 0047198d-461a-4016-8aab-2fe1a0cb2e53" (GPT-5.6 Is Coming And A Price War Just Started!, synced 2026-07-27)
  - "NotebookLM source 0056531c-957b-4e16-a8d9-990abad2b37e" (Stop Prompting Claude. Use Karpathy's Method Instead., synced 2026-07-27)
  - "NotebookLM source 016cd280-975f-4388-be9f-698703d6350a" (Claude's New Update Is Scarier Than You Think (+18 AI Updates), synced 2026-07-27)
  - "NotebookLM source 01db259b-c055-4c95-9e96-3c54f6c67452" (Claude Lives in Your Browser Now | Use Claude in Chrome to Automate Tasks, synced 2026-07-27)
  - "NotebookLM source 022e2f9f-fd76-43ff-b00e-09dee31d3d56" (Hand Off Coding Sessions from Claude Code to Codex | Quickstart | Kurrent Capacitor, synced 2026-07-27)
  - "NotebookLM source 05489b57-d0f1-4023-8c79-643a7823772f" (RAG is Dead. Again. (Claude Agent SDK + Memory), synced 2026-07-27)
  - "NotebookLM source 0733c855-24a5-4c3b-8e0d-64591af5aa5d" (This Claude Code Skill Loops Your Entire Business in Minutes, synced 2026-07-27)
  - "NotebookLM source 07cdd43e-ad02-49b8-8ab7-938cd1bb37e6" (I Let Hermes Agent Trade For Me (Insane Results), synced 2026-07-27)
  - "NotebookLM source 08648400-8252-467f-b18b-1348fd44b29c" (Graphify + Claude Code + Obsidian = GOD MODE, synced 2026-07-27)
  - "NotebookLM source 08e952ac-2dc2-48ee-b22b-bae3fb5e9c3c" (An Average Guy Built This in One Weekend. Here's How, synced 2026-07-27)
  - "NotebookLM source 0954a938-5320-464f-abe6-14e658572202" (GLM 5.1 Coding LoRA Now BEATS Claude?! 🤯 | Local AI In-Depth REVIEW, synced 2026-07-27)
  - "NotebookLM source 0a8fa397-e2d7-4d6d-a690-88850d682015" (Claude Mythos is Finally Here., synced 2026-07-27)
  - "NotebookLM source 0c52fd10-7632-4a2b-8ace-40f9a8eef968" (Claude Code Agentic OS… It Remembers Everything, synced 2026-07-27)
  - "NotebookLM source 0c7ce36d-5ff2-4f91-a68f-5b8ad84bb0e2" (How to use Claude Goal. Best practices, how it works, and why you need it!, synced 2026-07-27)
  - "NotebookLM source 0db5a48b-4268-44e1-9b45-d5921ad611fd" (I Built The Best Claude Memory System (Beats Hermes), synced 2026-07-27)
  - "NotebookLM source 0e316a10-5666-48c2-b213-a9baa6151b61" (Set Up Claude Cowork better than 99% of people, synced 2026-07-27)
  - "NotebookLM source 0eff4be8-9f60-41df-b67b-10e27f8e55c7" (STOP Using Claude This Way Bro., synced 2026-07-27)
  - "NotebookLM source 0f0f912d-c6f4-4233-b5f2-ee00754b54bf" (Tag Claude in, right where you already work, synced 2026-07-27)
  - "NotebookLM source 0f21afc6-4e80-40de-828d-630e374b9e46" (NotebookLM + Gemini Gems Just Changed AI Forever 🤯 | Build Your Own AI Expert (2026), synced 2026-07-27)
  - "NotebookLM source 115c3f1a-db0c-4444-a22f-3640ab8485f4" (Is Grep Actually Better Than Vector Search for AI Agents, synced 2026-07-27)
  - "NotebookLM source 11f153b9-8ed8-45bf-8f2a-5e1945c11e38" (Claude Skills Made Simple, synced 2026-07-27)
  - "NotebookLM source 12616ff5-e981-4762-8bf8-7d9b77c18be4" (What the Top 1% of Engineering Teams Do Differently with AI | Andrew Churchill, Weave, synced 2026-07-27)
  - "NotebookLM source 1372f1bf-d46e-4667-8ff8-4fc9972ab84a" (3 Claude Settings That Make It Super Powerful, synced 2026-07-27)
  - "NotebookLM source 149c908e-8de3-4390-b8b9-9f3518e858cb" (They Just Shrunk AI Data Center by 10,000x, synced 2026-07-27)
  - "NotebookLM source 14a31c42-3616-4cdd-98e4-bf1a28ca39b8" (Your Best Prompts Make the New Claude Worse, synced 2026-07-27)
  - "NotebookLM source 169cead1-0353-43b3-ad25-73dd9612b750" (I Took All 18 Anthropic Courses in One Weekend (Honest Review), synced 2026-07-27)
  - "NotebookLM source 16cac02f-c336-4b1a-9096-a56c5d8e8305" (Star Trek Fans FINALLY Got What They Wanted And It's Not From Kurtzman!, synced 2026-07-27)
  - "NotebookLM source 178708ef-a210-4323-8c6c-bc3045f6eeea" (NotebookLM + Gemini Just Changed AI Forever 🤯 | The Ultimate AI Workspace (2026), synced 2026-07-27)
  - "NotebookLM source 19233685-f4ec-4031-a996-ababf1eb3dee" (Do This Before AI Writes Any Code #aicoding #claude #vibecoding, synced 2026-07-27)
  - "NotebookLM source 199d61fb-1354-4472-a4a8-1c6eb0583781" (Domina el 90% de Claude Design en 15 Minutos (Casos Reales de Empresa), synced 2026-07-27)
  - "NotebookLM source 19a07515-9976-4718-9d62-eaa64e544c31" (The Top 10 Claude Code Plugins to 10x Your Next Project (June '26), synced 2026-07-27)
  - "NotebookLM source 19cbe6e7-6bb7-45d2-8a2d-308f782bcb8b" (The future of work with @Claude, synced 2026-07-27)
  - "NotebookLM source 1a0b74ec-b56d-4c6a-8ecd-d56d9933b1e0" (This Claude Trick Scrapes ANY Competitor, synced 2026-07-27)
  - "NotebookLM source 1e7fca10-4ac0-47b4-9e95-420d80818d3d" (Claude Obsidian is INSANE! 🤯, synced 2026-07-27)
  - "NotebookLM source 1e959f6a-3813-43ed-8322-f74573bc7080" (Is Splitting Your AI Budget a Mistake? (Claude / Codex $100 vs $20), synced 2026-07-27)
  - "NotebookLM source 1f69ed1b-5a27-45d7-b03f-bd3ac9f0a1d7" (This “Karpathy System” could 701x your AI Workflows (86,000 GitHub Stars!), synced 2026-07-27)
  - "NotebookLM source 20b24bd9-c848-404e-a30b-c26bd6e3a760" (7 Mind-Blowing Use Cases for Hermes Agent, synced 2026-07-27)
  - "NotebookLM source 20b67f27-e26d-4719-b3fc-efae2a8c623a" (NotebookLM Can Write and Run Code Now (This Changes It)!, synced 2026-07-27)
  - "NotebookLM source 21902f5d-fc8b-4571-8da8-f0aa77d6790e" (How to Make Claude Scheduled Tasks to ONLY Run at SPECIFIC Times, synced 2026-07-27)
  - "NotebookLM source 2477e781-89cc-435b-ab09-5642ea8208e5" (How Anthropic Engineers ACTUALLY Use Claude, synced 2026-07-27)
  - "NotebookLM source 24dd4898-fee6-49f7-b022-ab458d75d764" (Qwen 3.7 Max: The Model Beating Claude Opus (Nobody's Talking About), synced 2026-07-27)
  - "NotebookLM source 25bb1182-863b-4923-b05a-412de3bbe69a" (Cohere North Mini Coder : Beats Gemma4 , synced 2026-07-27)
  - "NotebookLM source 26abf746-3638-4c2f-8559-67a6f10f4287" (A Complete Guide to the New Claude Design, synced 2026-07-27)
  - "NotebookLM source 2714bd84-5b07-41a1-8260-1a8ad4c061df" (My top 3 skills for solving hard problems with Claude Code and Codex, synced 2026-07-27)
  - "NotebookLM source 2892e1f0-b040-4bd8-ad5d-27eb3f5baf33" (How to INSTANTLY Run ANY Skill in Claude + Codex, synced 2026-07-27)
  - "NotebookLM source 290ca2e6-4bfc-4cb3-b380-ab544cb1d39d" (Run Your Own Uncensored AI Model Locally and Privately (ChatGPT, Claude, Gemini, Deepseek, & More!), synced 2026-07-27)
  - "NotebookLM source 2c3ca5ae-26cb-426c-800d-9b2e096a6384" (If you are broke, start this Ai Business Now!, synced 2026-07-27)
  - "NotebookLM source 2c7c46d0-1e42-4acb-8706-122e422c7571" (Your AI Agent Isn't Reasoning — It's Running a Search (And Here's the Proof), synced 2026-07-27)
  - "NotebookLM source 2e38dc63-4428-413c-87d7-521b72ae361d" (How to Make Money With Claude (step by step), synced 2026-07-27)
  - "NotebookLM source 2fb9f24f-5dbf-4ecb-ba95-34ad79d6a7aa" (PewDiePie’s Odysseus AI Just Made Private AI Easy, synced 2026-07-27)
  - "NotebookLM source 2ffbd14e-f5ae-4c2c-b21a-dccdf9e46d47" (THE $1 CODER: This CODER COSTS $1 AND GIVES YOU $50 WORTH USAGE!, synced 2026-07-27)
  - "NotebookLM source 2ffe3ab4-a1be-4b8d-94b6-380b264bcc43" (I Tested Karpathy's 4 Claude Rules And Was Shocked At the Results, synced 2026-07-27)
  - "NotebookLM source 308fb766-de3c-4081-9b7b-9f7bcc8d0963" (Claude and ChatGPT Got More Literal. Your Old Prompts Are Backfiring, synced 2026-07-27)
  - "NotebookLM source 32065aa4-8ded-47a0-a5aa-3f190ad5c9df" (I Cancelled Higgsfield & Built This Claude Skill Instead, synced 2026-07-27)
  - "NotebookLM source 32610da9-f9f3-459d-9222-5b889dda54ce" (I Developed Davinci Resolve Plugin to Edit videos from Claude, synced 2026-07-27)
  - "NotebookLM source 333cf9fa-874f-44bb-8da1-adba6d3b22c2" (It's cognitive uploading' | How Google NotebookLM's Steven Johnson uses AI as a second brain, synced 2026-07-27)
  - "NotebookLM source 33c81a42-6892-479a-84ea-e90dc2777c8c" (I Automated My Life with Claude Routines, synced 2026-07-27)
  - "NotebookLM source 33f5e60f-a28f-4bc9-a078-f8e94082bf8e" (An Average Guy Built This in One Weekend. Here's How, synced 2026-07-27)
  - "NotebookLM source 36d32ba9-c6a3-4055-a026-28359302bde9" (17 Tricks To Build 10x Faster with Claude, synced 2026-07-27)
  - "NotebookLM source 3750ff80-fd1f-4d62-9c43-730dfffcc8a7" (I Built an AI Second Brain That Fixes Its Own Mistakes (Karpathy's Method), synced 2026-07-27)
  - "NotebookLM source 376ed80d-f71a-461d-8ba7-07cc950104f8" (This Skill Instantly 10x’es Every Claude Output, synced 2026-07-27)
  - "NotebookLM source 379df79b-b375-40a9-b5d5-4b11e5edfb30" (Open Design: Why 40k Developers Abandoned Claude Design, synced 2026-07-27)
  - "NotebookLM source 37b591bc-77c4-4b68-b226-56a52c9956e9" (ANTHROPIC COOKED: Claude Fable 5: It's ACTUALLY Over (INSANE), synced 2026-07-27)
  - "NotebookLM source 37e8b929-3492-4d67-bbdd-5571f65ddbbe" (This company killed open source, synced 2026-07-27)
  - "NotebookLM source 38ecc457-8d7c-45f0-bf9d-2197aa071632" (Turn Claude Into A Design GENIUS In 3 Simple Steps, synced 2026-07-27)
  - "NotebookLM source 38f7eb79-469b-4a81-8708-3e7fc1282398" (Higgsfield + Davinci Resolve Just Replaced 7 Paid Tools for FREE (Insane VALUE), synced 2026-07-27)
  - "NotebookLM source 3940c967-da38-4dac-b024-e3f67c91d337" (4 Claude skills to make your RESUME unrejectable, synced 2026-07-27)
  - "NotebookLM source 3a4400d8-25eb-405e-992e-e49533a28367" (I Tried AI Filmmaking With Free AI Video Generators (actually good?), synced 2026-07-27)
  - "NotebookLM source 3ba3fbb0-0a54-4bb5-ab74-96515bd8bef9" (Claude Replaced My Video Editor (It Does Everything Better Than Me), synced 2026-07-27)
  - "NotebookLM source 3cb21989-8f81-4ba9-8c7d-7e4c22d7d278" (I Tested 100,000 Trading Strategies on 1,000 Stocks, synced 2026-07-27)
  - "NotebookLM source 3cd46a8a-a89a-48f2-9b35-1c8a0ce63c57" (The Automated Trading System of a 3-Time Trading World Champion | Kevin Davey, synced 2026-07-27)
  - "NotebookLM source 3cdbdb84-8eb6-4847-acc1-74de6028aec1" (Google's Agents CLI: The CLI + Skills Combination to Ship AI Agents EASILY, synced 2026-07-27)
  - "NotebookLM source 3dbaced7-9463-4a61-8ad9-9be2ae8cb758" (I Created an Entire Anime Scene with Topview Drama Studio, synced 2026-07-27)
  - "NotebookLM source 3e89fb60-efea-46f5-b444-7956280ec2f0" (HeyGen AI video generator just changed the game..., synced 2026-07-27)
  - "NotebookLM source 3f0ac243-4260-4a16-918b-edd6391bb97c" (GLM 5.2 Works BEST with the RIGHT Harness, synced 2026-07-27)
  - "NotebookLM source 4010635a-bb46-432d-912d-8005188ada97" (AI is about to get insanely expensive. Do this right now., synced 2026-07-27)
  - "NotebookLM source 4040f053-88ed-4918-a673-f891c4f8f7a1" (I Tried Every Popular Claude Skills System, Here is the Best, synced 2026-07-27)
  - "NotebookLM source 422e515e-e734-4a16-a990-409c1348ac5b" (The GSD Skills Everyone Misses (I Tested Them), synced 2026-07-27)
  - "NotebookLM source 4286f838-ff23-4064-991e-f208340ee365" (How Anthropic Employees ACTUALLY Use Claude Skills, synced 2026-07-27)
  - "NotebookLM source 42c019a9-fe39-4b08-aa5d-1858702a5d86" (Claude Fable 5 + YouTube = $30,000/mo, synced 2026-07-27)
  - "NotebookLM source 43dea8e9-88bf-4349-a909-a0065042731d" (How to Use Claude AI Properly: Complete Guide, synced 2026-07-27)
  - "NotebookLM source 43fca7c8-992d-4d2f-b494-36144d7f3493" (Finally… A NotebookLM Alternative With an API, synced 2026-07-27)
  - "NotebookLM source 4574e4ae-a918-4e8a-94f3-962bbfcb720c" (NEW Claude Fable/Mythos 5 AI Good For TradingView Strategies? (Backtesting Engine) (watch ASAP), synced 2026-07-27)
  - "NotebookLM source 466106b2-9da9-4a73-84be-71bf5acc3606" (Claude is Ending YouTube (It Already Started), synced 2026-07-27)
  - "NotebookLM source 4744aed7-67ef-4cd5-959b-b308f71e1968" (How to Use Gemini Branch to Split Your Chats into Multiple FOCUSED Paths, synced 2026-07-27)
  - "NotebookLM source 475995d9-e50c-4324-877f-8b822358ca3a" (Palmer Luckey on Threats, Autonomy, and the Future of American Power, synced 2026-07-27)
  - "NotebookLM source 478ebda7-790a-449c-9214-f3c86f075d35" (All The Types Of Claude Loops Explained In 13 Minutes, synced 2026-07-27)
  - "NotebookLM source 483bdc68-51ee-4e43-b8e3-a39102664145" (Uber Burned Its Whole AI Budget in 4 Months, synced 2026-07-27)
  - "NotebookLM source 48470773-b360-43c3-b193-4bc64d4da75b" (Claude Code v2.1.172 — Agents that spawn agents #Shorts, synced 2026-07-27)
  - "NotebookLM source 48ecfd8b-d021-49b1-be32-ad8c7819725e" (NEW Claude Update is INSANE!, synced 2026-07-27)
  - "NotebookLM source 492653a4-f0b1-4fc5-b021-06a727827511" (I let AI edit my videos in CapCut #claudecode #claude #capcut #aitools #editing, synced 2026-07-27)
  - "NotebookLM source 498bbf75-5dfb-4e16-a327-7ebc224ed70d" (How to Build a Multi-Agent Workflow for LLM Wikis in Hermes Kanban, synced 2026-07-27)
  - "NotebookLM source 4b48cd2e-9cbf-4914-9131-8bea4d005e8b" (Hermes vs. Claude Cowork? Wrong Question., synced 2026-07-27)
  - "NotebookLM source 4b746787-86cc-45ef-8d2a-d6384a1e50e9" (The Skill That 10x’d My Claude Code Projects, synced 2026-07-27)
  - "NotebookLM source 4b7f381e-ae33-45c6-9a2e-fc9f9445b59f" (CLAUDE.md vs Skills vs Subagents explained, synced 2026-07-27)
  - "NotebookLM source 4b868a0a-47eb-4e1a-bd19-345f17940591" (NEW Claude Sonnet 5 is INSANE!, synced 2026-07-27)
  - "NotebookLM source 4be63a39-952f-435f-9c49-8f64a311c82a" (Edit Videos with Davinci Resolve and Claude using Transcript based Editing, synced 2026-07-27)
  - "NotebookLM source 4c583e9f-4e38-40d3-b2d8-755c18b54707" (Claude Opus 4.8 Is Acting Like Opus 5..., synced 2026-07-27)
  - "NotebookLM source 4c817fa8-0945-415d-95aa-290e915b8664" (How to Use Claude AI to Make FREE Videos (Hyperframes), synced 2026-07-27)
  - "NotebookLM source 4ce9187b-cac4-4bbd-a2fa-82e4fce264ee" (New AI Agent From Higgsfield Supercomputer—Just Got 3x More Powerful and 8x Cheaper Overnight, synced 2026-07-27)
  - "NotebookLM source 4d1551f1-9d85-4ce5-8ae7-8eeeb850522f" (Autonomous AI Research - Full Beginner Tutorial, synced 2026-07-27)
  - "NotebookLM source 4d6febe1-261a-4731-872f-65f07b2b8fbf" (Anthropic Just Changed How We Work Forever.. (Claude Tag), synced 2026-07-27)
  - "NotebookLM source 4d9db89d-13f2-4e26-ad28-965bb06a4a1b" (the only two claude frontend design skills worth your time, synced 2026-07-27)
  - "NotebookLM source 4e3de7a0-2771-4ef4-8703-3d2af039b2e8" (NotebookLM + Claude Agent OS Just Changed Everything, synced 2026-07-27)
  - "NotebookLM source 506ea282-e7b8-4791-be56-5cd92607711a" (Claude Certified Architect (CCA-F): Study Guide to Pass First Try, synced 2026-07-27)
  - "NotebookLM source 511d9970-dbe9-4d3d-b5bc-044b0c4f3f75" (Claude Fable 5 + Loop Designs is TOO STRONG! (Full Tests), synced 2026-07-27)
  - "NotebookLM source 52568880-6f84-40b5-97df-83ce8e4736c3" (Claude’s New Trading Agent Is Insane! (Tutorial), synced 2026-07-27)
  - "NotebookLM source 54923e38-11a9-41fc-83ec-06ffaf423ce1" (Stop Making Ads Manually (Claude Agent Workflow), synced 2026-07-27)
  - "NotebookLM source 5541a80f-5b34-433e-8797-60f2ea3625e8" (One markdown file just fixed AI coding forever., synced 2026-07-27)
  - "NotebookLM source 55531675-6706-4c19-8aab-19f872641f3a" (Claude + CapCut Completely Changes Everything For Editors- Full Tutorial, synced 2026-07-27)
  - "NotebookLM source 56757a84-4253-4f05-91aa-683a9dbec4fe" (6 Open Source Repos That Solve Claude Code's #1 Problem, synced 2026-07-27)
  - "NotebookLM source 57bd4e51-acc0-44df-a98c-b1b7cd87beeb" (Gemma 4 12B with Local NotebookLM! (Youtube Agent Setup), synced 2026-07-27)
  - "NotebookLM source 585a3578-be9f-4c80-b03e-49de46f317b1" (We Stressed-Tested CLAUDE Fable 5. Here's What We Found, synced 2026-07-27)
  - "NotebookLM source 5a22c310-f29a-4a2f-83d3-3209cfabdb34" (How to Research and explore with Claude tool — Free AI Tutorial 2026  #freeaitricks #aianimation #, synced 2026-07-27)
  - "NotebookLM source 5b8590c1-7d6f-448f-983f-69e1896a0044" (Master Claude Memory in 23 Minutes, synced 2026-07-27)
  - "NotebookLM source 5c3032d4-d340-4d55-b623-bf1ac5355101" (Claude + TradingView = Gamechanger for trading, synced 2026-07-27)
  - "NotebookLM source 5db31a29-2afa-4a7c-bb79-2cae97d070a9" (Claude is dumb by default, synced 2026-07-27)
  - "NotebookLM source 5ec5db50-b10d-4bb4-a3db-84ca400ba106" (Anthropic Just Turned ONE Claude Into a 50-Agent Expert Team (Claude Science), synced 2026-07-27)
  - "NotebookLM source 5fd5c40b-250b-4a46-9873-42b20c74bcf9" (Top 5 Claude Skills That can save 10x Your AI Sessions, synced 2026-07-27)
  - "NotebookLM source 6047761c-3682-4ed5-86dd-d5a764dd9c00" (Code Loops and A Self Learning AI Harness, synced 2026-07-27)
  - "NotebookLM source 6232e1ad-a820-46a1-9af0-84e550f150cb" (I Built an AI Trading System With Claude + TradingView, synced 2026-07-27)
  - "NotebookLM source 625477b3-5d4a-4d83-b5cb-7f779ceae8ce" (Don’t Use Claude Until You Watch This, synced 2026-07-27)
  - "NotebookLM source 62557c7d-e03d-4725-9bee-3f315b8b001f" (Claude Code Dynamic Workflows Explained for Beginners, synced 2026-07-27)
  - "NotebookLM source 62abb150-3fe6-4d5d-aab3-acfa1c78b137" (Gemini Spark Is Google’s Most Powerful AI Tool Yet, synced 2026-07-27)
  - "NotebookLM source 63843417-2ac2-4cee-bb67-91af6b1429f6" (Stop Using Obsidian. This Simple Second Brain Setup Actually Works (Andrej Karpathy + Claude Cowork), synced 2026-07-27)
  - "NotebookLM source 64b7ef22-8b36-4e50-a63a-6eec42b6fe04" (Claude and ChatGPT Gets Smarter When You Change This One Setting, synced 2026-07-27)
  - "NotebookLM source 661a1f32-0e68-4694-bd26-4ac9130f8745" (This NEW Claude Feature Is The Best Thing I've Used In 3 Years, synced 2026-07-27)
  - "NotebookLM source 66937126-8add-4742-a846-134dbac74403" (Fable 5 Just Changed Trading Bots Forever (This Isn't an Update, It's a  Takeover), synced 2026-07-27)
  - "NotebookLM source 6890665b-0a81-4c23-a4e4-6a482a2e01b3" (Bye bye, Premiere Pro? | This Claude skill is destroying every video editing tool, synced 2026-07-27)
  - "NotebookLM source 6a05491b-91fe-465f-9ce8-cff6cb5ce402" (How To Use Claude For Academic Research (My Actual AI Stack), synced 2026-07-27)
  - "NotebookLM source 6a0acd6b-94c7-41fb-a7dd-77a41893dd7f" (30+ Killer VFX Shortcuts Anyone Can Steal, synced 2026-07-27)
  - "NotebookLM source 6cd1f07c-58b2-44bf-87f3-5d90abe32c9a" (The prompting playbook, synced 2026-07-27)
  - "NotebookLM source 6e1e8a95-e471-490e-beca-c4fdf4587eaf" (Insane Claude Design Skills You Need To Build Beautiful Websites, synced 2026-07-27)
  - "NotebookLM source 6f009fff-66fb-4e3f-8c7f-573f59846f5f" (Graphify + Obsidian + Claude Code = CHEAT CODE, synced 2026-07-27)
  - "NotebookLM source 70fa57f9-6169-4667-9363-3e7f6d08de08" (Claude Fable 5 (TESTED): UHM... It's actually not worth it.., synced 2026-07-27)
  - "NotebookLM source 711f9c3c-7285-4127-aa13-658269863a74" (8 Claude Loops to Build 10x Faster, synced 2026-07-27)
  - "NotebookLM source 71eec985-e541-4e5a-a485-dd6c79d587dc" (Karpathy's New Move is Huge for Claude Code Users, synced 2026-07-27)
  - "NotebookLM source 735bed93-fa19-4aa5-9aaa-4dce1b372852" (Claude just killed every app I paid for. Here is proof., synced 2026-07-27)
  - "NotebookLM source 741d583a-5f6f-4f50-b6d7-6966be35adcf" (Start a $10,000/mo Solo AI Creative Agency (Higgsfield + Claude), synced 2026-07-27)
  - "NotebookLM source 74cb11a1-d790-4c8e-a294-7bb0a7609565" (You're Using Claude Fable Wrong (Anthropic's Advice), synced 2026-07-27)
  - "NotebookLM source 74ccb047-4b23-42a3-a67a-c137092bb7b5" (Claude Cowork for Beginners, Complete Your First Project in less than 5 Minutes!, synced 2026-07-27)
  - "NotebookLM source 7587edd5-4fef-436c-b448-b1c302638a96" (The Fastest Claude AI Side Hustle to Your First $1,000, synced 2026-07-27)
  - "NotebookLM source 782e6dea-e364-477a-9a3f-d12b5782c2ad" (The Claude Systems That Work While I Sleep, synced 2026-07-27)
  - "NotebookLM source 79e518d7-83d6-4303-896c-7ebcd387731a" (4 Workflows You Can Use Today: Hermes Agent Prompts, synced 2026-07-27)
  - "NotebookLM source 7afd63d7-7528-4498-8455-f0a45487c36e" (NEW Claude Sonnet 5 coming?, synced 2026-07-27)
  - "NotebookLM source 7b488c0b-22a7-42e5-984c-172ebcd86215" (Sonnet 5 vs Opus Head-to-Head | The Results Will Surprise You, synced 2026-07-27)
  - "NotebookLM source 7d551ef5-ece1-4af9-b06c-3b732193012e" (Hermes vs. Claude Cowork? Wrong Question., synced 2026-07-27)
  - "NotebookLM source 7f11aa59-4229-434d-838c-27d433fda625" (Fable 5 for Web Design is Next Level!!! (3D, Interactive, Animated!), synced 2026-07-27)
  - "NotebookLM source 80476465-6d81-41b5-9370-c009b1c8dce5" (Claude Managed Agents Will Change How You Sell AI Forever, synced 2026-07-27)
  - "NotebookLM source 80712919-5284-490d-87a0-799e521b97eb" (Claude Mythos 5 Just Killed the AI Tool Era for Educators (Live Demo), synced 2026-07-27)
  - "NotebookLM source 83428499-669b-4f7e-b2c1-1bb376ea8da0" (Claude Fable 5 Just Changed How I Make AI Dashboards FOREVER!, synced 2026-07-27)
  - "NotebookLM source 8594b2b8-dfe3-4820-b51a-b353a577f048" (Mythos 5 & Fable 5 Launched, synced 2026-07-27)
  - "NotebookLM source 86576673-c823-4e85-aac7-4671bbfb0ec9" (What Is Agentic Coding? How AI Agents Modernize Code, synced 2026-07-27)
  - "NotebookLM source 86845daa-9a68-4132-a1aa-249dcd5a8223" (How to make Claude and Codex Talk in 1 Minute, synced 2026-07-27)
  - "NotebookLM source 87fefbc0-3109-4ea1-88d6-87ba263fb68f" (Claude Fable 5 - is this Mythos model worth the wait?, synced 2026-07-27)
  - "NotebookLM source 88196e8c-460c-4e17-8077-344b94ca3756" (The 5 Rules of Building With Claude Code (99% of influencers get this wrong), synced 2026-07-27)
  - "NotebookLM source 89d66676-385b-4c10-a162-aa1fcd83eda9" (Learn anything with the /teach skill, synced 2026-07-27)
  - "NotebookLM source 8beae7f5-20e1-48e3-ba85-b46da558a5fe" (Pi Coding Agent Setup After 2 Months, synced 2026-07-27)
  - "NotebookLM source 8c415b78-44f5-4704-b9f7-7406e1597f95" (Grep vs vector search. #ai #tech #techtech, synced 2026-07-27)
  - "NotebookLM source 8dea6b90-4e5f-4916-b19c-0cfc61f8af03" (I Built an AI Trading System With Claude + TradingView, synced 2026-07-27)
  - "NotebookLM source 8e4ea1ad-87e0-43a0-beb5-5f32c6bb19fc" (How To Build A Second Brain With Claude #shorts #claude, synced 2026-07-27)
  - "NotebookLM source 8e583636-5d3c-402c-8e8b-ffc3150ef016" (Stop Using Claude Without an Agentic OS, synced 2026-07-27)
  - "NotebookLM source 904e8b09-6b6a-4e1b-86ce-1ff6c7b866a7" (12 Hidden Features To Level Up Claude Cowork, synced 2026-07-27)
  - "NotebookLM source 90582d9d-ebbe-4e3c-8cd8-cf6079529b5c" (NotebookLM + Claude AI: I Built a Prompt Engineer 2.0, synced 2026-07-27)
  - "NotebookLM source 91d62939-8475-49b4-bc7d-fcaf114ef02f" (Rumor: Claude Opus 5 this Thursday, synced 2026-07-27)
  - "NotebookLM source 926d4c50-dc0a-4e70-b0c6-f76d0a4f6db9" (Claude Fable 5 & Mythos 5 Explained | Benchmarks, Features & Demos, synced 2026-07-27)
  - "NotebookLM source 928b8af5-6d0e-4007-8849-472c5cba8304" (Claude, The Pope, and AGI, synced 2026-07-27)
  - "NotebookLM source 92e84974-3dc8-4273-8f04-ad126a079127" (How I Turned Claude Into My Personal Assistant (Full Guide), synced 2026-07-27)
  - "NotebookLM source 92eb3819-ca6c-4fa6-b50d-5c7f209e7cbd" (Nex-N2 Pro IS GREAT! New Opensource Model Beats GPT 5.5, Opus 4,7, & Gemini 3.5? (Fully Tested), synced 2026-07-27)
  - "NotebookLM source 943756e2-0ca0-44a7-89bf-59717b108813" (Elon won after all, synced 2026-07-27)
  - "NotebookLM source 94aa0dfa-b374-477e-96c2-91bd2a885dfb" (The end of one-shot RAG pipelines #AgenticRAG #Tech #AI, synced 2026-07-27)
  - "NotebookLM source 94cfc780-c410-4eb5-a2a3-cae7e33612c8" (Free Claude Tag + agents battle + TikTok video maker + Free Claude Tag + more, synced 2026-07-27)
  - "NotebookLM source 9669062f-2213-4475-9ffc-62cb714241ed" (You Can Buy Claude for Pennies on China's Black Market, synced 2026-07-27)
  - "NotebookLM source 96ed5f50-0304-42ae-8b0c-c7846647a4c6" (Claude Code Just Dropped /Goal. (Master it in 8 Minutes)., synced 2026-07-27)
  - "NotebookLM source 9867415a-251e-4cfa-8f27-f5637b3dd1ab" (Everyone Says AI Is Too Expensive. They're Wrong., synced 2026-07-27)
  - "NotebookLM source 98768dfe-2b72-45d6-86e2-f95bc156852c" (Claude + CapCut make pro motion graphics in seconds… here's how, synced 2026-07-27)
  - "NotebookLM source 9a43e623-df01-493a-ba32-316e2287f2c8" (I Ranked the 10 Most-Starred Claude Skills on GitHub (Install These), synced 2026-07-27)
  - "NotebookLM source 9a6a0f27-3390-4e89-99b4-dcba685a3550" (I Tested Claude Fable 5 Against Opus So You Don't Have to WASTE Your Credits, synced 2026-07-27)
  - "NotebookLM source 9af74a7f-2464-48cf-8664-7af3edb242dd" (Claude's 13 Free AI Courses in 12 Minutes, synced 2026-07-27)
  - "NotebookLM source 9b31f7d5-79e0-4434-a9a7-44c930373d57" (Top AI Agent Projects : Honen, Minimi, Veltrix AI, Extella.AI & Cignara, synced 2026-07-27)
  - "NotebookLM source 9b4a0257-2586-46bd-ba6e-aa1d567ea273" (My Claude Cowork OS Just Changed How I Work Forever..., synced 2026-07-27)
  - "NotebookLM source 9be12e16-1fcd-4bdd-ba29-d02bca2a05a4" (Claude Can Now Build Its Own Harness... For Every Task, synced 2026-07-27)
  - "NotebookLM source 9c4f2f57-83de-469b-9f94-e24613c9b65b" (I Wish Someone Had Shown Me How to Talk to Claude Like This Earlier (in 10 min), synced 2026-07-27)
  - "NotebookLM source 9cc4a7e9-4d63-4d3f-a76a-4512320170d6" (Anthropic Just Dropped Their Claude Skills Secrets (steal these), synced 2026-07-27)
  - "NotebookLM source 9dd4c17e-359b-4cb7-a7f7-4934ea2484e7" (I Asked Claude To Make Me as Much Money as Possible, synced 2026-07-27)
  - "NotebookLM source 9e3bb059-84f3-4393-8236-051374776613" (Stop Prompting Claude. Use Karpathy's Method Instead., synced 2026-07-27)
  - "NotebookLM source 9e995329-67bf-4482-8e1c-89636caa356e" (Claude Code Creator: “Write Loops, Not Prompts”, synced 2026-07-27)
  - "NotebookLM source 9ec9257b-843b-411b-9f4b-cbd644d752d4" (Last 30 Days: AI Search Engine Disrupts Perplexity #shorts, synced 2026-07-27)
  - "NotebookLM source 9f61dc88-e634-4586-b94a-ef02fc495859" (You Can Buy Claude for Pennies on China's Black Market, synced 2026-07-27)
  - "NotebookLM source 9fca53ca-387e-4604-95e9-5538fc2b6048" (Skill Chaining in Claude OS is INSANE (Don’t Fall Behind!), synced 2026-07-27)
  - "NotebookLM source a0160da3-5b62-4926-bf77-4ae21b807d38" ((Podcast) The Planning First Revolution How CodeRabbit Masters AI Orchestration with Claude, synced 2026-07-27)
  - "NotebookLM source a221b801-a002-4431-969d-1923fe79dc43" (Dumping Files Into Claude Doesn't Make It Smarter, synced 2026-07-27)
  - "NotebookLM source a2568537-fad2-4772-ad4f-24fc542161ad" (I Tried Every New Claude Feature, These 4 Will Make You Rich, synced 2026-07-27)
  - "NotebookLM source a2ebb8e4-6a46-45d2-9f28-d35dfc73cc7a" (DON'T Build Claude Agents. Build Skills., synced 2026-07-27)
  - "NotebookLM source a353018d-3f23-422b-9942-31bddb13fbdd" (LTX Director + 4 Panel + Global Ref | Local AI Video Workflow, synced 2026-07-27)
  - "NotebookLM source a3791a75-99d8-4f9d-80bb-4660dc8c143d" (Higgsfield MCP + Claude Just Changed How I Make AI Films, synced 2026-07-27)
  - "NotebookLM source a3f15061-5360-4c2d-870e-571d7f57cb59" (The ONLY 6 Skills You Need to 10x Your Claude Projects, synced 2026-07-27)
  - "NotebookLM source a4564ccf-e9f4-49d5-ad33-43dc9144bda4" (Why Memory Pipelines Fail & ICL works for AI Agents, synced 2026-07-27)
  - "NotebookLM source a4ab4bc5-66a0-4975-9408-c2a800265911" (5 YouTube Channels Making Full-Time Incomes You Can Copy With Claude AI, synced 2026-07-27)
  - "NotebookLM source a5856023-64a7-4ac3-ad59-819967521b03" (Claude: How to Build an Agent Operating System!, synced 2026-07-27)
  - "NotebookLM source a65a84f7-d659-4d79-b31d-74ddaef10621" (They Looked Inside Claude’s AI's Mind. It Got Weird, synced 2026-07-27)
  - "NotebookLM source a826d705-e732-4107-8911-a088466a226d" (5 Claude Skills That Make Claude Scary Good at Real Work, synced 2026-07-27)
  - "NotebookLM source a8fd452e-fb47-41d7-bdaf-14472a40b918" (Learn to Learn in 4hrs 54mins - Full Course, synced 2026-07-27)
  - "NotebookLM source a903fabb-6ecb-439f-80f4-1b508d007cc1" (Local AI Agents Masterclass (Gemma 4 + OpenCode + Odysseus tutorial), synced 2026-07-27)
  - "NotebookLM source a95d86c0-8fdc-4665-9ea2-d3e7bcdc58a0" (One skill and Claude Code becomes a full motion design studio - Remotion, synced 2026-07-27)
  - "NotebookLM source a986cdd2-1038-42d1-9ec1-9e27f38e456d" (5 'Engineer-Only' Claude Skills Every Vibe Coder NEEDS, synced 2026-07-27)
  - "NotebookLM source aa5e2326-70b3-4bc0-bf80-936758e5e524" (I Replaced Claude Opus With GLM 5.2 Inside Claude Code — Here's Where the #1 Open Model Breaks, synced 2026-07-27)
  - "NotebookLM source aa9dc0af-a6ef-4197-8785-e61fe8884ce6" (The Claude Update You've Been Waiting For, synced 2026-07-27)
  - "NotebookLM source abd44891-809c-4b4d-80b8-89b8fc8a30de" (I Built the Same App in 3 Coding Agents — One Cost 2x More, synced 2026-07-27)
  - "NotebookLM source acb47461-866d-4850-ab7d-5bf6d6aea60b" (Claude Generated These Animations in Seconds | Full Workflow, synced 2026-07-27)
  - "NotebookLM source adca6cd7-60c2-4dd9-ae43-fafa288de950" (Welcome to May 17, 2026, synced 2026-07-27)
  - "NotebookLM source aec899f6-4d49-44db-8e65-aab22c175fde" (I Love the Karpathy LLM Wiki but it Doesn't Scale. Here's What Does., synced 2026-07-27)
  - "NotebookLM source aefe55c2-e3a5-4030-aae1-692dd01ca795" (This Claude Trick Scrapes ANY Competitor, synced 2026-07-27)
  - "NotebookLM source af9bbe2f-7913-456b-b127-b34017b8ad8e" (Claude + Obsidian in Under 1 Minute (Using Cowork), synced 2026-07-27)
  - "NotebookLM source b0669e24-a47c-4e01-bb98-2567267ce523" (NotebookLM + Hermes Just Changed AI Forever 🤯 | Build a FREE AI Content Machine (2026), synced 2026-07-27)
  - "NotebookLM source b112828a-d267-47eb-9ba3-74b543e4f5d8" (I Turned Claude Into the Ultimate Second Brain, synced 2026-07-27)
  - "NotebookLM source b2feebfe-94b2-4d60-8242-d100ad9822c4" (D&D is Broken. Fix it with THIS!, synced 2026-07-27)
  - "NotebookLM source b39c7225-5c88-4f73-90cb-2f11c883424a" (Karpathy's LLM Wiki + This Skill = Game Changer, synced 2026-07-27)
  - "NotebookLM source b4354745-9eb7-471b-bd12-5bcf9d4a6502" (Claude is Building Itself..., synced 2026-07-27)
  - "NotebookLM source b5ac0a66-c34c-4a16-b24b-49412fda2fa0" (I Turned Claude Into the Ultimate Second Brain, synced 2026-07-27)
  - "NotebookLM source b6d36b85-323c-4a65-ad2d-6513604d6ff3" (Ultimate Guide To Claude Skills, synced 2026-07-27)
  - "NotebookLM source b9297bfa-c32c-4d9c-8f88-dec4dfa6cf6c" (Claude Finds Out Exactly What Readers Want in My Novels, synced 2026-07-27)
  - "NotebookLM source b9a7d442-6e92-443f-b916-80037ae07583" (A Google Director Open-Sourced His Claude Skills, 51K Stars on Github, synced 2026-07-27)
  - "NotebookLM source ba06f458-2a3f-4149-bee1-5aed365c1096" (The Complete Guide to the Hermes Agent Desktop App, synced 2026-07-27)
  - "NotebookLM source ba12340c-428b-45bb-91c5-a88b71e37652" (Don't Use Claude Fable 5 Until You See This, synced 2026-07-27)
  - "NotebookLM source ba150d04-5749-4c80-ac01-0aafa3852922" (Claude: How to Build an Agent Operating System!, synced 2026-07-27)
  - "NotebookLM source bb34f591-b992-4d52-a747-93b92b978b1a" (Hand Off Coding Sessions from Claude Code to Codex | Quickstart | Kurrent Capacitor, synced 2026-07-27)
  - "NotebookLM source bc01724b-8df7-4afa-936f-91b3c367963f" (I Was The Only Thing Connecting Claude, ChatGPT, and Codex. So I Built My Replacement., synced 2026-07-27)
  - "NotebookLM source bd614fd6-337d-4551-b90b-eba5efaa967a" (Claude Can Edit Your Videos Now, synced 2026-07-27)
  - "NotebookLM source be033a45-322f-4118-80dc-cbb39abf98d5" (Claude Code Just Destroyed GHL & Hubspot ($0/Mth No Subscription), synced 2026-07-27)
  - "NotebookLM source bf5628ec-32b0-4011-b3db-7fa98f747d6b" (How Claude Code’s lead designer builds with AI, synced 2026-07-27)
  - "NotebookLM source bfbe7738-4567-420d-b5e3-dc445e83d5fc" (5 Claude AI Passive Income Ideas That Actually Work in 2026, synced 2026-07-27)
  - "NotebookLM source c1bece5c-f815-4f95-87be-08f4db9a9558" (Stop Prompting Claude. Start Loop Engineering., synced 2026-07-27)
  - "NotebookLM source c275c77b-23c8-4e0a-be75-2f6f743d8359" (Claude Replaced My Video Editor (It Does Everything Better Than Me), synced 2026-07-27)
  - "NotebookLM source c4494ebc-8110-4191-b041-23a3ce8bba4c" (This loop + skill fixes AI slop, synced 2026-07-27)
  - "NotebookLM source c6800bdf-365b-44b3-8f47-a4c1d53b8581" (¡PewDiePie acaba de Reventar la IA! Lanzó Odysseus, IA GRATIS y SIN LÍMITES, synced 2026-07-27)
  - "NotebookLM source c732948d-883e-458e-9269-c293a12fa57d" (You're the Problem, Not Claude (6 Fixes to 10x Output), synced 2026-07-27)
  - "NotebookLM source c78ac180-4ed8-4c89-88bc-4888ced74965" (Claude Mythos 5 Just Made My Sonnet-Built Course Lesson Look Broken, synced 2026-07-27)
  - "NotebookLM source c7e92235-50e0-4aed-adec-108ecc5dd7a1" (Only the best are using them..., synced 2026-07-27)
  - "NotebookLM source c9897f40-d083-4716-95c0-6e363fd0a950" (How to Create Seamless AI Videos in 2026 (I’m an Ex-AI Engineer), synced 2026-07-27)
  - "NotebookLM source c98bca1d-fe6f-4acb-a57a-7a4016b6cd76" (This Claude Skill Replaced My Lead Gen Tools, synced 2026-07-27)
  - "NotebookLM source c9cf3c16-7d88-40bd-a500-7bae70c59106" (Claude Code + Graphify = Insane Agentic OS, synced 2026-07-27)
  - "NotebookLM source caf25fd6-3d50-45ec-b080-a4c18b482de5" (Vibe Coding with Claude Fable 5 (Mythos) is UNREAL - Fully Tested, synced 2026-07-27)
  - "NotebookLM source cc0649e0-7786-4b1b-93d9-1d971f94a7ca" (Start a $10,000/mo Solo AI Creative Agency (Higgsfield + Claude), synced 2026-07-27)
  - "NotebookLM source cf20634a-3a71-4618-b624-42b980c31963" (I Built The Best Claude Memory System (Beats Hermes), synced 2026-07-27)
  - "NotebookLM source cf74a22f-0910-40b4-a4d6-b2dd21b3ca5a" (Harness Engineering: What Separates Top Agentic Engineers Right Now, synced 2026-07-27)
  - "NotebookLM source cf8c712e-d95d-457f-a892-0090d3a5fe30" (these new Claude skills are saving me hundreds (skills and prompts in description), synced 2026-07-27)
  - "NotebookLM source cfe1fec1-c203-4eea-8d3a-ad916bfc7db0" (Claude Is More Powerful Than You Think, synced 2026-07-27)
  - "NotebookLM source d08d633b-8e48-4ef6-96ca-0c164137bb60" (I Built an Agentic Software Factory with Codex and Claude Code, synced 2026-07-27)
  - "NotebookLM source d0a1a30a-a171-4b08-b746-1b5e65e68232" (5 Side Hustles For People Over 50 (Using Claude AI), synced 2026-07-27)
  - "NotebookLM source d0d1b596-8e43-4656-acdc-32376233e876" (AI Search Engine for Claude, #1 Trending on GitHub, synced 2026-07-27)
  - "NotebookLM source d1254c82-ba31-4d33-adec-be4906681382" (How To Make Money With Claude's New Fable 5, synced 2026-07-27)
  - "NotebookLM source d34e6e6c-5519-4676-aa46-1f6661dd7202" (Anthropic hackathon winner open-sourced his Claude setup, synced 2026-07-27)
  - "NotebookLM source d3ed7a3f-df04-4bc0-9f9a-7cd10606c779" (The AI Framework Era Is Over: Why Context Is the Moat | Jerry Liu, synced 2026-07-27)
  - "NotebookLM source d43551a0-85ae-4373-b6e7-6aa380745f08" (Claude Opus 4.8 Review: New Demos You Need to See, synced 2026-07-27)
  - "NotebookLM source d4845703-11fe-457f-8077-03d77c595187" (Do This Before You Build with Codex, Claude, or Cursor!, synced 2026-07-27)
  - "NotebookLM source d5621eb5-69fe-45d1-b5f9-cd23813597f6" (You Set Up Claude Cowork in the Wrong Order, synced 2026-07-27)
  - "NotebookLM source d8b06880-0158-494a-9da8-3f852e27e2a5" (Claude + CapCut = GOD MODE (3 cool ways to use it), synced 2026-07-27)
  - "NotebookLM source d8baca37-a9e7-46cf-ac05-905355a426e5" (This Claude + Canva workflow is insane! Save hours every week!, synced 2026-07-27)
  - "NotebookLM source d982bbcb-976d-4f44-aed5-1be8c25ac74f" (Stop Building Claude Second Brains (Do This Instead), synced 2026-07-27)
  - "NotebookLM source d9afb2f7-f986-4a55-ae0a-664183103274" (Stop Using Restricted AI. Build This Instead., synced 2026-07-27)
  - "NotebookLM source d9f55873-55bb-40a5-92b9-490d37d5c9a6" (I made 3 digital products with claude in 18 minutes, synced 2026-07-27)
  - "NotebookLM source db059f17-14b2-4e34-946b-815cfe77c450" (Claude Opus 4.8 actually blew my mind..., synced 2026-07-27)
  - "NotebookLM source de51f172-d055-478f-ba3e-efd2504bb7b9" (I Built A Real JARVIS With Claude, synced 2026-07-27)
  - "NotebookLM source de9ea693-3c5a-4739-99c2-fac368d38f0e" (Claude Code + Anki = Learn ANYTHING!, synced 2026-07-27)
  - "NotebookLM source df8ec1d0-7636-442f-9ea5-777971969c50" (How to Build Claude Subagents Better Than 99% of People, synced 2026-07-27)
  - "NotebookLM source e0de726e-f67b-468c-9388-dfa8c2428d59" (Get Claude FABLE 5 for Free! (No Clickbat!), synced 2026-07-27)
  - "NotebookLM source e1b7421a-c745-41d1-be9c-f5975bb50df6" (7 Things Claude Can Do That ChatGPT Can't (#1 Will Make You Switch), synced 2026-07-27)
  - "NotebookLM source e49c4d02-efed-4e5e-9921-fee7c6d77038" (Anthropic Just Dropped a Guide for WAY Better Claude Output (copy this), synced 2026-07-27)
  - "NotebookLM source e5aaefc4-a438-4e93-a9ab-f27fd3299181" ((Podcast) Mastering the Seven Pillars of AI Coding Agent Harnesses, synced 2026-07-27)
  - "NotebookLM source e6c8198e-6bc9-43a0-a561-599fff523dd3" (Claude Cowork Is a Game Changer (If You Do This), synced 2026-07-27)
  - "NotebookLM source ea6833ad-8264-4b17-b9da-718952313b26" (How to Stop Paying for AI Models (and use FREE Models in Claude Code) #Hack #claudecode #genai, synced 2026-07-27)
  - "NotebookLM source eb207737-78e6-413b-80d8-c1fdc1b82f5a" (I Let Claude AI Trade Real Money | Here's What Happened, synced 2026-07-27)
  - "NotebookLM source ebc25d17-4e16-46b8-bdec-5bcf85177fb9" (Claude Confidently Skipped Half Your Document and Didn't Tell You, synced 2026-07-27)
  - "NotebookLM source ec6ecd66-8b91-419a-8587-dd4d2d282d57" (Use These 17 Claude Plugins, It Will Make You 10x Better., synced 2026-07-27)
  - "NotebookLM source ed0b9934-0bd2-41e2-addd-dc830857dc6c" (Claude Fable 5: Mythos AI Goes Public, synced 2026-07-27)
  - "NotebookLM source ed669897-32e4-4cc0-a7b0-fcde32bad56b" (Domina el 90% de Claude Design en 15 Minutos (Casos Reales de Empresa), synced 2026-07-27)
  - "NotebookLM source edd6be9f-e00b-42cd-a223-170e72db8656" (Advanced Claude Prompt Tricks You Need to Know., synced 2026-07-27)
  - "NotebookLM source ee795fb7-bc55-4376-9c74-fee630b0f36e" (How to build a Claude Agent team that runs in loops, synced 2026-07-27)
  - "NotebookLM source f196f0cb-7f53-46ad-9517-17ebf80d43d3" (PKM Is Dead Long Live PCM: Obsidian Is Different Now, synced 2026-07-27)
  - "NotebookLM source f1faf09e-2501-4b44-99c7-4fe4cf48c2e3" (This Claude MCP Turns One Video Into Ads, Shorts & Viral Content, synced 2026-07-27)
  - "NotebookLM source f2c551df-a0dc-45b4-bf4b-e0c4b86099dd" (Stop Prompting Claude. Use Hormozi’s Method Instead., synced 2026-07-27)
  - "NotebookLM source f3577789-6d3b-4c8f-bfb5-ce18d14921d2" (How to Add Algorithms to Your Claude Skills, synced 2026-07-27)
  - "NotebookLM source f3d935c1-33fc-4ffa-8b9b-247d3d70ac88" (How to Use Claude Design – Full AI Design Workflow 2026, synced 2026-07-27)
  - "NotebookLM source f4d06250-349c-4a67-b78b-7d9587942e78" (How to Build Claude Subagents Better Than 99% of People, synced 2026-07-27)
  - "NotebookLM source f5202682-ee3d-4331-a6f6-12e17c8b8353" (Claude Can Now Learn by WATCHING You — Record a Skill, synced 2026-07-27)
  - "NotebookLM source f5257a7a-23f0-45fb-8f82-cf1b386598df" (SpaceX Rejected from S&P 500 Index - Finally a Sane Decision, synced 2026-07-27)
  - "NotebookLM source f6c7d7df-6e8e-4d39-a870-95a2aaa5beab" (How I Fully Automated My Video Editing With Claude (No CapCut), synced 2026-07-27)
  - "NotebookLM source f6e0eaa3-bd57-4c08-8670-702eb3caac88" (Claude's New Loop System Changes Everything, synced 2026-07-27)
  - "NotebookLM source f71e029a-9deb-421d-aa89-c4146ea1c03c" (This Claude Second Brain Setup Will Change How You Do Sales Forever, synced 2026-07-27)
  - "NotebookLM source f7c70180-1776-48d6-8564-ed39889231e1" (Gemini Spark Tutorial for Beginners, synced 2026-07-27)
  - "NotebookLM source f95ea676-7d08-421c-9db9-514a8046a148" (Claude Fable 5 vs Opus 4.8 vs GPT-5.5 Codex - Who Builds the Best Game?, synced 2026-07-27)
  - "NotebookLM source faba2cb4-dbe6-485c-a59a-44837d73f0e6" (New BEST local AI image generator is here!, synced 2026-07-27)
  - "NotebookLM source fb56d9a5-bed4-41ad-a05a-44a2d4baa93d" (How to Build A Self-Improving System with Claude, synced 2026-07-27)
  - "NotebookLM source fba9ae3b-e219-497f-82a3-36763be5671c" (I Found 5 Claude AI Side Hustles That Beat a Full-Time Salary, synced 2026-07-27)
  - "NotebookLM source fd0b52ec-5b1a-4c25-877d-a9be9606d60c" (Hermes is now my 24/7 video editor, synced 2026-07-27)
  - "NotebookLM source ff290ebe-7191-4206-8e82-64adec184fcb" (Anthropic Just Dropped Claude for Small Businesses (31 Skills), synced 2026-07-27)
  - "NotebookLM source ffb9a547-5843-400a-88db-9426951d1f99" (I Built 40+ Claude Skills With This 1 Simple Plugin, synced 2026-07-27)
  - "NotebookLM source 10cf4c18-af9b-4d6a-b2c1-c5812d2baaa3" (Turn Football Moments Into Anime Movies With AI (Higgsfield + Seedance Workflow), synced 2026-07-27)
  - "NotebookLM source 308cdfbb-4cb6-4748-ba4d-29208d8416ad" (How To Write a Literature Review With AI (Without Getting Caught Lying), synced 2026-07-27)
  - "NotebookLM source 50faea98-ed17-4dbe-a4f4-9b0cda88eb27" (How to Add an AI Chatbot to Your Client's Website, synced 2026-07-27)
  - "NotebookLM source 55b2212f-e6d8-4f83-880b-cc5d2c16c0fa" (Add THIS Before Every AI Prompt! (Gemini, ChatGPT, Claude), synced 2026-07-27)
  - "NotebookLM source 582adee1-7db8-4c8e-9237-eb1ee7fb9f07" (ChatGPT & Claude Are Built to Give You the Average Answer, synced 2026-07-27)
  - "NotebookLM source 7fdedf60-7dc4-4f43-9fd6-f3240f182302" (How to Turn Your LOCAL AI Model into a REAL App You'd Use Every Day, synced 2026-07-27)
  - "NotebookLM source 8f6333ca-c2b4-43a6-bc07-658f4c7c2b31" (You Asked For This For Years. Monday It's Yours., synced 2026-07-27)
  - "NotebookLM source 97cf6607-4a2f-4603-869e-15e35bcb80a4" (How to Disable THINKING Mode on LM Studio Local AI Models for FASTER Responses, synced 2026-07-27)
  - "NotebookLM source cb825326-b49d-4cb7-93a3-3842d94ae24d" (Google Antigravity just got 66,000+ Superpowers 🔥 #Antigravity #SKILLS #vibecoding #VibePM, synced 2026-07-27)
  - "NotebookLM source ddf61a53-05b5-4657-a3be-bb3c8923916e" (This Claude Workflow Saves Hours on Note Organization, synced 2026-07-27)
  - "NotebookLM source e946d6e3-16d1-4f12-983e-90f2f87aeea3" (Dark Minimal Techno | Underground Night Mix | Hypnotic Nonstop Set, synced 2026-07-27)
  - "NotebookLM source 538b653f-75f2-4319-ae4a-17b81b2a9119" (Little Coder: Small Models Need Small Harnesses, synced 2026-07-27)
  - "NotebookLM source 55ecc5dc-987b-4904-8cf6-de3c48e1d3c7" (I Made Claude and Codex Talk to Each Other (No More Copy-Pasting), synced 2026-07-27)
  - "NotebookLM source 5bc26b09-abe3-465a-91d9-9301458b1a48" (Mistral Medium 3.5 BEATS Kimi AND Claude? 🤯 Local AI TEST & REVIEW, synced 2026-07-27)
  - "NotebookLM source 8dacd1b7-a0a0-495a-a17b-5c45ebe7d18b" (Plan with Claude Opus, Build with Kimi K2.6? LIVE Mixed-Provider Benchmark, synced 2026-07-27)
  - "NotebookLM source 9b9dcf1e-5345-4862-b62d-39f0a70fd06f" (Codex Works Better When You Stop Treating It Like ChatGPT, synced 2026-07-27)
  - "NotebookLM source 9e8cfc48-2734-4305-908e-ef66075337dd" (Why Single-File HTML is the New Markdown in 2026, synced 2026-07-27)
  - "NotebookLM source aa843193-57c3-42cc-807d-ce09211fa558" (Kimi Code, our open-source coding agent, just got a major upgrade!, synced 2026-07-27)
  - "NotebookLM source debaee32-8f24-4576-aee9-9fec49d44e7d" (The Model Doesn't Matter. The Harness Does., synced 2026-07-27)
  - "NotebookLM source e58bcaa1-79d4-4e8b-9c85-75cf0b8b2e46" (The Best LOCAL Agentic Coding Workflow (Complete Guide), synced 2026-07-27)
  - "NotebookLM source fae028cf-fb29-4342-b344-48365af8ccc1" (Deep Agents or LangGraph? The LangChain agentic ecosystem explained, synced 2026-07-27)
  - "NotebookLM source 0a1dcbb2-d494-489b-9b08-28993c8cccc3" (Run Uncensored Local AI Models on Apple M5 Max — FREE Unlimited Image & Video Generation, synced 2026-07-27)
  - "NotebookLM source 0d4221b8-5c0c-4c6e-9647-8cca69900313" (Paste This Into Claude, Never Hit a Token Limit Again, synced 2026-07-27)
  - "NotebookLM source 103200c7-9a29-4eaf-87a1-273cad991de8" (Immich v3 changes roundup | New features + breaking changes..., synced 2026-07-27)
  - "NotebookLM source 157af12a-1e43-4540-868e-4e825936ebeb" (How to Use DiffusionGemma, Google's BLAZING FAST Open-Source AI Model, synced 2026-07-27)
  - "NotebookLM source 1c380f33-5c6a-43f2-b2b8-fad609a40603" (I Turned Cheap Cloud Storage Into a 1PB Local Drive (With JuiceFS), synced 2026-07-27)
  - "NotebookLM source 355af48c-3297-4a10-8a19-899848f14b4b" (Are you still building connectors without observability? #mcp #aiagents, synced 2026-07-27)
  - "NotebookLM source 370dd42b-3b54-470b-b27b-57fe3117aad5" (3 Steps To Spend 50% Less Claude Tokens (Steal This), synced 2026-07-27)
  - "NotebookLM source 5865bb25-501a-466f-93c3-5a70109b21dd" (The $300 open-source AI beating Bloomberg and GPT, synced 2026-07-27)
  - "NotebookLM source 5d1cc4f5-3853-43a6-b108-3ab872d9fa85" (Hacker News Show #8: gentleos32, liteparse, tiny-vllm, polycss, lathe, mach, VTCode, altersend, synced 2026-07-27)
  - "NotebookLM source 6b335384-c33d-46ff-a4f1-e5dfc01fce9b" (I Found OpenAI’s $3B Loophole, synced 2026-07-27)
  - "NotebookLM source 7d3f92c1-fcb9-4bf6-8328-629bf692c507" (Gemma 4 Was Broken for Agents - Google Just Fixed It, synced 2026-07-27)
  - "NotebookLM source 90be46ba-913c-405d-accd-65fec968a2f8" (My Hermes Agent Talks Back Now (Voice Mode), synced 2026-07-27)
  - "NotebookLM source a22a2da4-5164-45f9-8a7e-7d4013914d44" (GPT 5.6 Has Trauma from Training, synced 2026-07-27)
  - "NotebookLM source b3eb08db-fdf0-4ce5-aeff-a50a8779e597" (Run Local AI from USB - Windows, Mac & Linux (No Internet) 🔥, synced 2026-07-27)
  - "NotebookLM source bd93421a-58eb-4e04-9ea8-c2b01c0addfe" (The Killer Behind Data Centers In Space, synced 2026-07-27)
  - "NotebookLM source c0bcbbbb-f16b-4c07-90ff-1c03cf95cc6f" (Nemotron 3 Ultra: The 100% Free & Open Frontier Model Built for AI Agents, synced 2026-07-27)
  - "NotebookLM source c2dfe179-46a5-4c74-b943-fe737023bc7f" (Hermes Agent Just Stopped Being a CLI Tool (v0.16), synced 2026-07-27)
  - "NotebookLM source c4f05041-8ca1-40ff-ba53-923dbe37772a" (Ollama 0.30 — Run ANY GGUF Model + 20% Faster Performance, synced 2026-07-27)
  - "NotebookLM source d09ce8d2-6d2c-4fb8-966e-8a703ec3a961" (Diffusion Gemma vs Traditional AI: Who wins? #ai #tech #google, synced 2026-07-27)
  - "NotebookLM source de391b12-d8df-4e4f-bc31-3e987a6283b2" (Local Deep Research — AI Research Assistant (Fully Local, Encrypted, Open Source), synced 2026-07-27)
  - "NotebookLM source e05e52b4-8731-46a9-ada2-1195ca55622c" (Higgsfield Is FREE for 24 Hours - Don’t Miss This, synced 2026-07-27)
  - "NotebookLM source e7d72bb3-18a8-46e5-9231-a5d35e8cad86" (DiffusionGemma GGUF: Run Google's Fastest Model Locally on Any GPU, synced 2026-07-27)
  - "NotebookLM source 0b91340b-c89d-4ad8-8534-04617f5baefd" (Shocking Confirmation That Liquid Water Is Two Separate Substances, synced 2026-07-27)
  - "NotebookLM source 1e911792-15f2-433a-8ad8-cb578aa3df56" (Why we can't test our way out of this, synced 2026-07-27)
  - "NotebookLM source 51ffbe17-88ce-426b-a658-ab932d01574d" (Something Is Dying, Something Is Born. | News Buzz Ep. 8, synced 2026-07-27)
  - "NotebookLM source 52a17821-e7aa-4d58-90d1-3e17bbf4c124" (The critical mistake WOMEN make with MEN, synced 2026-07-27)
  - "NotebookLM source 6652c72b-7088-4fb8-a58a-84fd072b0535" (Deja de Enviar Prompts a Claude: Usa el Metodo Karpathy en su Lugar, synced 2026-07-27)
  - "NotebookLM source 6c3683ac-3673-43c6-8fb2-414394351356" (Two of the best programmers alive agree on the real problem, synced 2026-07-27)
  - "NotebookLM source 701619a5-d3ea-43f8-a338-f07222bf5eb3" (This Sentence ENDS your career and NO ONE is allowed to tell you about it!, synced 2026-07-27)
  - "NotebookLM source 9c9ed1bb-4102-442b-9d88-fdb189d03cc8" (Sam Altman is Freaking Out, synced 2026-07-27)
  - "NotebookLM source b3cfab65-8076-4417-97f0-bc1eda0e2c66" (Emerging Situation: Anthropic's Global Pause, Recursive Self-Improvement, and AI Personhood Arrives, synced 2026-07-27)
  - "NotebookLM source e6b41e1a-f7a5-4410-a114-4a593044dfb8" (I Discovered The AI Girlfriend Epidemic, synced 2026-07-27)
  - "NotebookLM source f9f8f28e-0632-4bd6-bf3a-d1467c952007" (Dario and Sam have a problem..., synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: claude-code-multi-agent-collaboration-patterns
    - level: notebook
      id: fff42c44-d4ba-474a-93f7-7384bd536a1b
      title: WL: Health & Weight Loss
      url: https://notebooklm.google.com/notebook/fff42c44-d4ba-474a-93f7-7384bd536a1b
    - level: cluster
      id: 0
      name: claude-code-going
relations:
  - target: wiki/concepts/claude-skills-architecture.md
    type: related
  - target: wiki/concepts/hierarchical-agent-design.md
    type: related
  - target: wiki/concepts/ai-powered-development-workflows.md
    type: related
---

# Claude Code Multi-Agent Collaboration Patterns

## Decision context

**Definition:** Claude Code supports hierarchical agent spawning where a top-level orchestrator delegates tasks to sub-agents up to five levels deep, enabling complex collaborative workflows across teams and development environments.

Synthesized from **352 contributing transcripts** in NotebookLM notebook *WL: Health & Weight Loss*, clustered into the "claude-code-going" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Claude Code agents can spawn sub-agents that delegate further, forming native hierarchical AI workflows up to five levels deep
- At Anthropic, Claude Tag opens 65% of product pull requests by collaborating in real-time team threads
- Claude keeps context across channels and teams while building memory as work progresses
- Claude Skills provide a lightweight approach to defining agent capabilities using plain markdown with tool access and routing
- Skills are loaded lazily - Claude reads only the title until a request needs the full instructions
- A skill is packaged as a folder with files containing job definitions, team-specific processes, and tool configurations
- The Claude Code desktop application provides dedicated Chat, Co-work, and Code tabs
- Co-work enables managing projects using files, screenshots, and business documents to create dashboards and organized structures
- Claude can integrate with external tools like Anki for spaced repetition learning when combined with Claude Code
- Multi-agent workflows require managing context at each level with clean separation between hierarchical levels

## Verifiable values

| Name | Value |
|---|---|
| Maximum agent hierarchy depth | `5 levels` |
| Anthropic PR automation rate | `65% of product pull requests opened via Claude Tag` |
| Claude Skill GitHub stars (top skill) | `180,000+` |
| Claude Skills available on GitHub | `10,000+` |

## Related concepts

- [[agent-skills-architecture]] — Claude Skills Architecture
- hierarchical-agent-design — Hierarchical Agent Design
- ai-powered-development-workflows — AI-Powered Development Workflows

## Citations (from contributing transcripts)

- **Claim:** Claude Code agents support hierarchical spawning up to five levels deep with clean context separation
  - Source: Claude Code v2.1.172 — Agents that spawn agents #Shorts (`48470773-b360-43c3-b193-4bc64d4da75b`)
  - Context: a top level orchestrator spawns a PR reviewer that reviewer spawns a CI analyzer that analyzer spawns a coverage checker each level gets its own clean context real hierarchical AI workflows native no hacks
- **Claim:** Anthropic uses Claude Tag to open 65% of product pull requests
  - Source: Tag Claude in, right where you already work (`0f0f912d-c6f4-4233-b5f2-ee00754b54bf`)
  - Context: And across Anthropic, Claude Tag opens 65% of our product pull requests
- **Claim:** Claude Skills use plain markdown with lazy loading of instructions
  - Source: I Ranked the 10 Most-Starred Claude Skills on GitHub (Install These) (`9a43e623-df01-493a-ba32-316e2287f2c8`)
  - Context: a skill is a folder you hand it inside is one file called skill.md that says Here's the job here's how we do it here are the tools claude reads only the title until your request actually needs it then and only then it opens the full instructions
- **Claim:** Claude maintains context across team channels while building memory of work
  - Source: Tag Claude in, right where you already work (`0f0f912d-c6f4-4233-b5f2-ee00754b54bf`)
  - Context: Claude keeps up with the group thread reacting to product decisions made in real time it opens the PR and it lands the change
- **Claim:** Top Claude skill has 180,000+ GitHub stars
  - Source: I Ranked the 10 Most-Starred Claude Skills on GitHub (Install These) (`9a43e623-df01-493a-ba32-316e2287f2c8`)
  - Context: the single most starred thing people call a claude skill has 180,000 stars

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `fff42c44-d4ba-474a-93f7-7384bd536a1b`
(cluster `claude-code-going`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [WL: Health & Weight Loss](https://notebooklm.google.com/notebook/fff42c44-d4ba-474a-93f7-7384bd536a1b)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
