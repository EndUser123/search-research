---
title: "Tool Choice Parameter Control"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, langchain]
summary: >
  The tool_choice parameter is a cross-provider feature in LangChain that controls when and how language models invoke tools, supporting modes such as auto, any, and none to dictate forced function calling behavior.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc" (Mastering Claude Skills, synced 2026-07-28)
  - "Intercept and control agent behavior with hooks - Claude Code Docs" (https://code.claude.com/docs/en/agent-sdk/hooks, transcript synced 2026-07-28)
  - "TIL my LangGraph agent stopped calling a tool after a prompt tweak and every output-based eval still passed. Now I test the trace, not the answer. : r/LangChain - Reddit" (https://www.reddit.com/r/LangChain/comments/1u5z3mv/til_my_langgraph_agent_stopped_calling_a_tool/, transcript synced 2026-07-28)
  - "Tools - Model Context Protocol" (https://modelcontextprotocol.io/specification/2025-11-25/server/tools, transcript synced 2026-07-28)
  - "Seeking help with some merge message issues when LangGraph is called in parallel" (https://forum.langchain.com/t/seeking-help-with-some-merge-message-issues-when-langgraph-is-called-in-parallel/3007, transcript synced 2026-07-28)
  - "Feature request: expose tool_choice parameter in ClaudeAgentOptions · Issue #655 · anthropics/claude-agent-sdk-python - GitHub" (https://github.com/anthropics/claude-agent-sdk-python/issues/655, transcript synced 2026-07-28)
  - "langchain-skills/config/skills/langgraph-fundamentals/SKILL.md at main - GitHub" (https://github.com/langchain-ai/langchain-skills/blob/main/config/skills/langgraph-fundamentals/SKILL.md, transcript synced 2026-07-28)
  - "bind_tools | langchain_anthropic - LangChain Reference" (https://reference.langchain.com/python/langchain-anthropic/chat_models/ChatAnthropic/bind_tools, transcript synced 2026-07-28)
  - "tool_choice | @langchain/google-vertexai" (https://reference.langchain.com/javascript/langchain-google-vertexai/types/GoogleAIModelRequestParams/tool_choice, transcript synced 2026-07-28)
  - "diegopenilla/LLM_LangGraph_Notes: Study notes and recipes using LLMs with LangGraph" (https://github.com/diegopenilla/LLM_LangGraph_Notes, transcript synced 2026-07-28)
  - "bind_tools | langchain_aws - LangChain Reference" (https://reference.langchain.com/python/langchain-aws/chat_models/bedrock/ChatBedrock/bind_tools, transcript synced 2026-07-28)
  - "bind_tools with tool_choice='any' suppresses chain-of-thought on Claude models #119 - GitHub" (https://github.com/langchain-ai/langchain-litellm/issues/119, transcript synced 2026-07-28)
  - "bind_tools | langchain_openrouter - LangChain Reference Docs" (https://reference.langchain.com/python/langchain-openrouter/chat_models/ChatOpenRouter/bind_tools, transcript synced 2026-07-28)
  - "fix: third-pass review items — counter logic, FDA example annotation, audit/ policy · alirezarezvani/claude-skills@bf33d32 - GitHub" (https://github.com/alirezarezvani/claude-skills/actions/runs/27356937908/workflow?pr=835, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: tool-choice-parameter-control
    - level: notebook
      id: 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
      title: Mastering Claude Skills
      url: https://notebooklm.google.com/notebook/8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
    - level: cluster
      id: 4
      name: langchain-https-github
    - level: source_url
      url: https://code.claude.com/docs/en/agent-sdk/hooks
      title: Intercept and control agent behavior with hooks - Claude Code Docs
    - level: source_url
      url: https://www.reddit.com/r/LangChain/comments/1u5z3mv/til_my_langgraph_agent_stopped_calling_a_tool/
      title: TIL my LangGraph agent stopped calling a tool after a prompt tweak and every output-based eval still passed. Now I test the trace, not the answer. : r/LangChain - Reddit
    - level: source_url
      url: https://modelcontextprotocol.io/specification/2025-11-25/server/tools
      title: Tools - Model Context Protocol
    - level: source_url
      url: https://forum.langchain.com/t/seeking-help-with-some-merge-message-issues-when-langgraph-is-called-in-parallel/3007
      title: Seeking help with some merge message issues when LangGraph is called in parallel
    - level: source_url
      url: https://github.com/anthropics/claude-agent-sdk-python/issues/655
      title: Feature request: expose tool_choice parameter in ClaudeAgentOptions · Issue #655 · anthropics/claude-agent-sdk-python - GitHub
    - level: source_url
      url: https://github.com/langchain-ai/langchain-skills/blob/main/config/skills/langgraph-fundamentals/SKILL.md
      title: langchain-skills/config/skills/langgraph-fundamentals/SKILL.md at main - GitHub
    - level: source_url
      url: https://reference.langchain.com/python/langchain-anthropic/chat_models/ChatAnthropic/bind_tools
      title: bind_tools | langchain_anthropic - LangChain Reference
    - level: source_url
      url: https://reference.langchain.com/javascript/langchain-google-vertexai/types/GoogleAIModelRequestParams/tool_choice
      title: tool_choice | @langchain/google-vertexai
    - level: source_url
      url: https://github.com/diegopenilla/LLM_LangGraph_Notes
      title: diegopenilla/LLM_LangGraph_Notes: Study notes and recipes using LLMs with LangGraph
    - level: source_url
      url: https://reference.langchain.com/python/langchain-aws/chat_models/bedrock/ChatBedrock/bind_tools
      title: bind_tools | langchain_aws - LangChain Reference
    - level: source_url
      url: https://github.com/langchain-ai/langchain-litellm/issues/119
      title: bind_tools with tool_choice='any' suppresses chain-of-thought on Claude models #119 - GitHub
    - level: source_url
      url: https://reference.langchain.com/python/langchain-openrouter/chat_models/ChatOpenRouter/bind_tools
      title: bind_tools | langchain_openrouter - LangChain Reference Docs
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills/actions/runs/27356937908/workflow?pr=835
      title: fix: third-pass review items — counter logic, FDA example annotation, audit/ policy · alirezarezvani/claude-skills@bf33d32 - GitHub
relations:
  - target: wiki/concepts/bind_tools-method.md
    type: related
  - target: wiki/concepts/model-context-protocol-tools.md
    type: related
  - target: wiki/concepts/langgraph-agent-behavior.md
    type: related
---

# Tool Choice Parameter Control

## Decision context

**Definition:** The tool_choice parameter is a cross-provider feature in LangChain that controls when and how language models invoke tools, supporting modes such as auto, any, and none to dictate forced function calling behavior.

Synthesized from **13 contributing transcripts** in NotebookLM notebook *Mastering Claude Skills*, clustered into the "langchain-https-github" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The tool_choice parameter accepts string values including 'auto' (model decides), 'any' (forced function calling), and 'none' (no function calls permitted) [Source 8]
- Setting tool_choice to 'any' forces the model to predict only function calls, with optional allowed_function_names to limit the subset [Source 8]
- When tool_choice='any' is used with Claude models, it suppresses chain-of-thought reasoning [Source 11]
- The tool_choice parameter accepts specific function names as strings to force prediction of that particular function call [Source 7, 8]
- Different LangChain packages implement tool_choice with varying type signatures: dict | str | bool | None [Source 10, 12]
- In LangGraph, tool_choice enables control over which node or tool gets invoked during graph execution [Source 4]

## Related concepts

- [[bind_tools-method]] — bind_tools method
- [[model-context-protocol-tools]] — Model Context Protocol tools
- [[langgraph-agent-behavior]] — LangGraph agent behavior
- [[chain-of-thought-suppression]] — Chain-of-thought suppression

## Citations (from contributing transcripts)

- **Claim:** tool_choice supports 'auto', 'any', and 'none' modes
  - Source: tool_choice | @langchain/google-vertexai (`989f69a4-99f7-4f04-92e5-d16f7bfa96eb`)
  - Context: Mode Description 'auto' The default model behavior. The model decides whether to predict a function call or a natural language response. 'any' The model must predict only function calls.
- **Claim:** tool_choice='any' suppresses chain-of-thought on Claude models
  - Source: bind_tools with tool_choice='any' suppresses chain-of-thought on Claude models #119
  - Context: bind_tools with tool_choice='any' suppresses chain-of-thought on Claude models
- **Claim:** tool_choice can be a specific function name string
  - Source: bind_tools | langchain_anthropic - LangChain Reference (`8b2752b7-8584-412c-ba31-8dc1caa775aa`)
  - Context: tool_choice: dict[str, str] | str | None = None

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `8138a528-f5c2-4ee4-b5a9-f3359f48f0dc`
(cluster `langchain-https-github`). No claims are made
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

- NotebookLM notebook [Mastering Claude Skills](https://notebooklm.google.com/notebook/8138a528-f5c2-4ee4-b5a9-f3359f48f0dc)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
