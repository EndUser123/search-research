---
title: "how do I use dr tulu online?"
date: "2025-12-06"
mode: "CONCISE"
uuid: "0ff5ad35-7708-44a4-b3fd-d1e3c22b2d1d"
entry_count: 2
---

## Human

how do I use dr tulu online?

## Assistant

DR Tulu (Deep Research Tulu), or DR Tulu-8B, is an open-source AI research agent from the Allen Institute for AI, designed for long-form deep research tasks like planning multi-step workflows, tool-augmented searches (e.g., Google Search, web browsing, paper search), and synthesizing cited answers.[1][2]

## Online Access
No official free web demo or chat interface exists directly from Allen AI for DR Tulu-8B; the model requires local setup as it's trained for tool-use via the dr-agent-lib framework, which won't work out-of-the-box with standard Hugging Face inference or vLLM. Third-party sites like skywork.ai mention "free chat online" but primarily direct to Hugging Face downloads rather than providing a live interface.[3][2][4]

## Local Usage Steps
Download model weights (SFT or RL checkpoints) from Hugging Face repositories like rl-research/DR-Tulu-8B or rl-research/DR-Tulu-SFT-8B. Install the dr-agent-lib framework from its GitHub repository for tool integration, then run inference with actions like "think" for planning, "call_tool" for searches, and "answer" for cited responses. Formulate clear, long-form research queries; the agent handles stepwise reasoning, evidence retrieval, and synthesis automatically.[5][2][1][3]

## Key Components
- **Planner**: Generates "think" traces and search queries with context buffering.[3]
- **Retriever**: Calls tools like google_search, web_browse, or paper_search.[1]
- **Synthesizer**: Produces final answers with inline citation tags.[3]

## Human

How to use DR Tulu via a free web demo like skywork ai

## Assistant

DR Tulu-8B lacks an official free web demo from Allen AI; skywork.ai's page promotes it as "free chat online" but provides no live interface or direct access link—instead directing users to Hugging Face for model downloads and local setup via the dr-agent-lib framework.[1]

## Skywork.ai Page Details
The skywork.ai blog outlines DR Tulu-8B's architecture (Planner for reasoning, Retriever for tools like Google Search, Synthesizer for cited answers) and usage steps focused on local deployment: download from Hugging Face, define research queries, run modules sequentially, and review outputs. No clickable demo, chat widget, or hosted inference is mentioned; the "click to use" phrasing links to Hugging Face model pages without browser-based interaction.[1]

## Alternatives for Web Access
Check Hugging Face Spaces for community-hosted DR Tulu-8B demos (search "DR-Tulu-8B space" on Hugging Face), though none were confirmed active as of recent checks. For similar research agents, platforms like Replicate or Grok may host comparable open models, but DR Tulu requires tool integration not typically supported in basic web chats. Local setup remains the primary method: install dr-agent-lib, load Qwen3-8B-based weights, and query via Python scripts.[2][3][1]
