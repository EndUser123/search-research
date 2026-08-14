---
title: "Python Script for Multi LLM Debates"
date: "2026-04-02"
mode: "ASI"
uuid: "5994eab8-647b-4d6f-9397-e0295f80bbf4"
entry_count: 1
---

## Human

Research llm_multiagent_debate and Open-source-LLM-models-debate repos and build a Python script to run multi-LLM debates on custom prompts

## Assistant

## Research Findings

I studied three repos implementing the Du et al. (ICML 2024) multiagent debate paper:

**composable-models/llm_multiagent_debate** — The original paper implementation. Uses N instances of the same model (GPT-3.5). Each round, agents receive raw concatenated peer responses and refine their answer. Simple majority-vote scoring. Separate scripts per task (math, GSM8K, biography, MMLU).[4]

**Rajarshi-Misra/Open-source-LLM-models-debate** — Minimal Colab notebook using HuggingFace pipelines (dolly-v2-3b, dolly-v1-6b, mt0-large). Tests self-reflection (1 agent), 2-agent, and 3-agent arithmetic debates plus open-ended consensus. Very basic prompt construction — no summarization, no structured logging.[9]

**gauss5930/LLM-Agora** — Most feature-rich. Different LLMs per agent slot, GPT-based summarization of peer responses before feeding back (rather than raw concatenation), CoT support, model-specific prompt templates (llama, vicuna, falcon, etc.). Uses HuggingFace Inference Endpoints.[1]

## The Script

The `llm_debate.py` script synthesizes the best patterns from all three and modernizes them:

### Architecture
- **Provider abstraction** — OpenAI, Anthropic, Google Gemini via their native async SDKs. Easy to extend.
- **Async parallel execution** — All agents fire simultaneously each round (vs. sequential in the originals).
- **Du et al. debate loop** — Round 0: independent answers. Rounds 1-N: each agent sees all other agents' latest responses and refines. This is the core mechanism proven in the ICML paper.
- **Synthesis step** — After debate concludes, one agent summarizes consensus and remaining disagreements (from Agora pattern).
- **Optional judge** — A separate agent evaluates reasoning quality across all participants.
- **CoT toggle** — Appends "Let's think step by step" prompting (from Agora).
- **Structured output** — Full JSON log of every turn with agent, model, round, content, and timing.

### Usage

```bash
# Set API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...

# Quick start with a preset (cross-provider: GPT-4o + Claude Sonnet + Gemini Flash)
python llm_debate.py -p "Is P=NP?" --preset cross-provider

# Custom agents with CoT and a judge
python llm_debate.py \
  -p "Should we colonize Mars?" \
  -a "GPT-4o:openai:gpt-4o" \
  -a "Claude:anthropic:claude-sonnet-4-20250514" \
  -a "Gemini:google:gemini-2.0-flash" \
  --rounds 3 --cot \
  --judge "Judge:openai:gpt-4o" \
  -o results/mars_debate.json

# From config file
python llm_debate.py --config example_config.json
```

### Presets
| Preset | Agents |
|---|---|
| `cross-provider` | GPT-4o, Claude Sonnet, Gemini Flash |
| `openai-trio` | GPT-4o, GPT-4o-mini, o3-mini |
| `budget` | GPT-4o-mini, Claude Haiku, Gemini Flash |
| `reasoning` | o3-mini, Claude Sonnet, Gemini 2.5 Pro |

### Programmatic use

```python
from llm_debate import DebateConfig, AgentConfig, Provider, run_debate
import asyncio

config = DebateConfig(
    prompt="What is the most promising approach to AGI?",
    agents=[
        AgentConfig("GPT-4o", Provider.OPENAI, "gpt-4o"),
        AgentConfig("Claude", Provider.ANTHROPIC, "claude-sonnet-4-20250514"),
    ],
    rounds=2,
    cot=True,
)
result = asyncio.run(run_debate(config))
print(result.synthesis)
```

The JSON config file format is shown in `example_config.json` — supports all options including custom system prompts per agent.
