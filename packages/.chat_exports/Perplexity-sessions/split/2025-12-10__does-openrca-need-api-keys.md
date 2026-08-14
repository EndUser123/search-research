---
title: "does openrca need api keys?"
date: "2025-12-10"
mode: "COPILOT"
uuid: "aa1a12dd-6fba-494f-baee-326fa792f55c"
entry_count: 4
---

## Human

does openrca need api keys?

## Assistant

**Microsoft's OpenRCA, a benchmark for evaluating LLMs on root cause analysis in software systems, requires API keys for its baseline models like RCA-agent.** Users must configure API keys (e.g., for OpenAI's GPT-4o) in the `rca/api_config.yaml` file before running reproduction tests, such as `python -m rca.run_agent_standard --dataset Bank`. This setup enables the agent to process telemetry data via external LLM services rather than locally.[1][2]

**The original OpenRCA (openrca/orca) for Kubernetes root cause analysis does not require API keys.** It deploys via Helm charts and integrates telemetry sources like Prometheus without LLM dependencies or external API configurations.[3]

Given your work on RCA systems, Microsoft's OpenRCA likely aligns more closely, but confirm the repo context for precise setup.[2]

## Human

How does OpenRCA authenticate with LLMs without API keys

## Assistant

**OpenRCA (Microsoft's benchmark) does not support authentication with LLMs without API keys in its standard baselines like RCA-agent.** The framework relies on external LLM providers (e.g., OpenAI's GPT-4o, Claude) configured via `rca/api_config.yaml` with `API_KEY: "sk-xxxxxxxxxxxxxx"`, as direct API calls require these keys for authentication. No alternatives like local LLMs (e.g., Ollama) or secretless methods (e.g., OAuth) are documented in the repo, paper, or reproduction instructions.[1][2]

**RCA-agent uses Python code execution for telemetry processing, bypassing long contexts, but still invokes remote LLMs needing keys.** The Controller and Executor agents generate and run code in a stateful kernel to analyze metrics/logs/traces, then query the configured LLM for reasoning—authentication happens at this LLM call stage. Modifying for local models would require custom integration outside the provided setup.[2][1]

**For local LLM use without keys, adapt RCA-agent with Ollama-compatible endpoints.** Replace the API config with a local server (e.g., OpenAI SDK-compatible Ollama instance at `http://localhost:11434`), enabling OpenAI-style calls without external auth. This maintains the agent's structure but demands hardware (32GB+ RAM recommended) and isn't officially supported.[3][1]

## Human

Do I have to get an openai api key?  I don't want to.

## Assistant

**No, you do not need an OpenAI API key for Microsoft's OpenRCA.** The baseline RCA-agent can be adapted to use local LLMs via Ollama or similar self-hosted servers, replacing the `api_config.yaml` OpenAI endpoint with a local one like `http://localhost:11434/v1` using OpenAI-compatible SDK calls—no external authentication required.[1][2]

**Setup involves installing Ollama, pulling a capable model (e.g., Llama 3.1 70B for RCA tasks), and updating the config.** Run `ollama serve`, then modify `rca/api_config.yaml` to point to your local base URL and remove the `API_KEY` field, as Ollama doesn't need it. Test with `python -m rca.run_agent_standard --dataset Bank`.[3][1]

**Expect hardware demands: 32GB+ RAM/VRAM for strong performance on telemetry datasets.** Models like Mixtral or Phi-3 work but may underperform vs. GPT-4o baselines; fine-tuning or quantization helps. This keeps everything local, aligning with your agentic workflows.[4]

## Human

I have claude code, can I use that with openrca?

## Assistant

**Yes, you can integrate Claude (via Anthropic API or proxies) with Microsoft's OpenRCA by modifying the `rca/api_config.yaml` file.** OpenRCA's RCA-agent uses the OpenAI Python SDK for LLM calls, which supports Anthropic's Claude models through their official compatibility layer—set `base_url: "https://api.anthropic.com/v1/"` and `api_key` to your Anthropic key, then specify `model: "claude-3-5-sonnet-20241022"` (or similar).[1][2]

**For "Claude Code" (CLI/VSCode tool), proxy it to OpenRCA's OpenAI-compatible endpoint using tools like LiteLLM or claude-bridge.** Launch a local proxy (e.g., `litellm --model anthropic/claude-3-5-sonnet-20241022`), point OpenRCA's config to `http://localhost:4000`, and run Claude Code against that—no direct native support, but this routes agentic code tasks through Claude without OpenAI.[3][4][5]

**Anthropic API requires a key (free tier available), but local proxies enable Ollama-like setups if avoiding cloud.** Test with small datasets like Bank; expect similar performance to GPT-4o baselines on RCA tasks. Aligns with your Claude workflows—fork the repo for custom provider support if needed.[6][1]
