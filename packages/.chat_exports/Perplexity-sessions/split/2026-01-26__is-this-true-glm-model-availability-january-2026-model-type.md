---
title: "Is this true:  
  GLM Model Availability (January 2026)
  ┌──────────┬───────────────────┬─────────────────────────────"
date: "2026-01-26"
mode: "COPILOT"
uuid: "a1761762-194d-4194-a2eb-4042664a96ec"
entry_count: 4
---

## Human

Is this true:  
  GLM Model Availability (January 2026)
  ┌──────────┬───────────────────┬──────────────────────────────────┐
  │  Model   │       Type        │              Status              │
  ├──────────┼───────────────────┼──────────────────────────────────┤
  │ GLM-4.7  │ Text-only         │ ✅ Exists (latest flagship)      │
  ├──────────┼───────────────────┼──────────────────────────────────┤
  │ GLM-4.6V │ Vision/Multimodal │ ✅ Exists (current vision model) │
  ├──────────┼───────────────────┼──────────────────────────────────┤
  │ GLM-4.7V │ Vision            │ ❌ Does NOT exist                │
  └──────────┴───────────────────┴──────────────────────────────────┘

## Assistant

Yes, the table is accurate based on current information from Z.ai as of January 2026. GLM-4.7 is the latest text-only flagship model, GLM-4.6V is the current vision/multimodal offering, and no GLM-4.7V exists.[1][2][3]

## Model Details
GLM-4.7, released in early January 2026 by Z.ai, excels in coding, agentic tasks, and reasoning as a text-only model.[2][4][1]
GLM-4.6V, launched in December 2025, is a 106B-parameter vision-language model (VLM) supporting visual reasoning, tool calling, and multimodal workflows.[5][6][7][3]
Official Z.ai listings confirm GLM-4.6V as their top vision model, with no mention of GLM-4.7V anywhere.[3]

## Verification Sources
- Z.ai homepage explicitly lists GLM-4.7 (flagship text) and GLM-4.6V (latest VLM).
- Recent announcements highlight GLM-4.7 as a step up from GLM-4.6 in text capabilities, without a vision variant.[8][2]

## Human

what about glm-4.7-flash

## Assistant

**GLM-4.7-Flash is a real, recently released text-only model from Z.ai.** It's a lightweight, efficient variant of GLM-4.7, launched on January 19, 2026, and serves as the free-tier option with strong performance in coding, reasoning, and agentic tasks.[1][2][3][4]

## Key Features
- **Architecture and Capabilities**: 30B Mixture-of-Experts (MoE) model with ~3.6B active parameters, optimized for low latency, 200K context length, and 128K output tokens. Excels in frontend/backend coding (SOTA on SWE-bench Verified), tool calling, thinking modes, and general tasks like writing or role-playing.[5][3][4][1]
- **Modalities**: Strictly text input/output—no native vision or multimodal support, though it pairs well with external vision models in workflows.[6][4][1]
- **Availability**: Accessible via Z.ai API (free tier), OpenRouter, Hugging Face (open weights for local runs), and platforms like Unsloth or llama.cpp (with some noted implementation fixes needed).[7][4][8][5]

## Relation to Original Table
It fits under "GLM-4.7" as a text-only variant (not vision), maintaining the table's accuracy—no changes needed for GLM-4.7V status.[2][1]

## Human

GLM-4.7-Flash use cases for coding agents

## Assistant

GLM-4.7-Flash excels in coding agents due to its MoE architecture, top benchmarks like 59.2% on SWE-bench Verified, and native support for tool calling and long-context planning.[1][2][3][4]

## Primary Use Cases
- **Real-time Code Generation and Debugging**: Generates clean Python, JavaScript, or frontend UI code with error handling; ideal for iterative scripting or fixing bugs in workflows.[5][6]
- **Agentic Workflows and Task Planning**: Builds autonomous agents that decompose goals into steps, prioritize tasks, integrate tools (e.g., search, file ops), and execute multi-step logic like SWE-bench tasks.[7][5][1]
- **Tool Integration and Orchestration**: Leads τ²-Bench (79.5%) for interactive tool use; powers setups like OpenCode for agentic coding, local deployment via Ollama/llama.cpp, or API chaining.[8][4][9][1]
- **Local/Edge Deployment**: Runs efficiently on consumer hardware (e.g., 130 tokens/s on B200 GPU) for private coding assistants, balancing speed and reasoning in VS Code extensions or CLI agents.[2][10]

## Performance Highlights
| Benchmark | Score | Notes |
|-----------|-------|-------|
| SWE-bench Verified | 59.2% | SOTA for 30B class; triples some rivals [3][4] |
| τ²-Bench | 79.5% | Multi-tool agent tasks [4] |
| GPQA | 75.2% | Reasoning for complex code logic [11] |

Use "Preserved Thinking" mode for multi-turn agents and low temperature (0.7) on coding benches.[4][12]

## Human

How to run GLM-4.7-Flash locally for coding agents

## Assistant

To run GLM-4.7-Flash locally for coding agents, use llama.cpp for OpenAI-compatible API serving, then integrate with tools like OpenCode for agentic workflows. This setup leverages GGUF quants (e.g., Q4_K_XL ~17GB) and supports GPU acceleration on Windows/Linux with CUDA.[1][2][3]

## Hardware Requirements
- **Minimum**: 24GB VRAM/RAM (Q4_K_M GGUF), NVIDIA GPU (RTX 3090+ or A100).
- **Recommended**: 32GB+ VRAM, CUDA 12.1+, 200K context needs ~64GB total.
- Windows 11 compatible via WSL2 or native MSVC builds.[2][3][4]

## Setup Steps
1. **Clone and Build llama.cpp**: Use a GLM-patched branch for flash-attn support.
   ```
   git clone --branch glm_4.7_headsize https://github.com/am17an/llama.cpp.git
   cd llama.cpp
   # Windows: Use CMake GUI or MSVC; Linux: make clean && make -j
   cmake . -B build -DGGML_CUDA=ON -DLLAMA_CURL=ON
   cmake --build build --config Release -j --target llama-server
   ```
[5][2]

2. **Download GGUF Model**: From Unsloth (best quants).
   ```
   pip install huggingface_hub xet
   HF_XET_HIGH_PERFORMANCE=1 huggingface-cli download unsloth/GLM-4.7-Flash-GGUF --include "*Q4_K_XL*" --local-dir ./models
   ```
   Pick `GLM-4.7-Flash-UD-Q4_K_XL.gguf` (~17GB).[3][2]

3. **Launch Server**: Expose OpenAI API for agents.
   ```
   ./llama-server --model models/GLM-4.7-Flash-UD-Q4_K_XL.gguf --host 0.0.0.0 --port 8080 --ctx-size 16384 --temp 0.7 --top-p 1 --flash-attn auto --threads 32 --batch-size 1024
   ```
   Test: `curl http://localhost:8080/v1/chat/completions -H "Authorization: Bearer local" -d '{"model":"GLM-4.7-Flash","messages":[{"role":"user","content":"Write Python agent scaffold"}]}'`[2][3]

## Coding Agent Integration
Install OpenCode: `curl -fsSL https://opencode.ai/install | bash`.
Configure `~/.opencode/config.yaml`:
```
provider: other
provider_id: openai
base_url: http://localhost:8080/v1
api_key: local
model: GLM-4.7-Flash
```
Auth: `opencode auth login` (use "local" key). Run: `opencode build "FastAPI app with tests"`. It handles planning, coding, testing autonomously.[1][2]

## Tips for Agents
- Tool-calling: `--temp 0.7 --top-p 1.0`; enable Jinja for templates.
- Windows: Use PowerShell; enable CUDA via NVIDIA toolkit.
- Avoid Ollama initially due to chat template issues—use llama.cpp directly.[4][3]
