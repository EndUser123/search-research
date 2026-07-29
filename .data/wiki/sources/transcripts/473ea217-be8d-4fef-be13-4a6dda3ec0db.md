---
source_id: "473ea217-be8d-4fef-be13-4a6dda3ec0db"
title: "How to Run LLMs Locally with Ollama: GPU-Accelerated Setup Guide | Spheron Blog"
notebook_id: 831e0613-f723-4d87-aaeb-1d4b5a061496
url: https://www.spheron.network/blog/run-llms-locally-ollama/
type: web_page
exported: 2026-07-28
---

# How to Run LLMs Locally with Ollama: GPU-Accelerated Setup Guide | Spheron Blog
How to Run LLMs Locally with Ollama: GPU-Accelerated Setup Guide | Spheron Blog 

https://www.spheron.network/

GPUs

Features

Resources

Customers

Pricing

Contact Sale

https://www.spheron.network/contact/

Go to platform

https://app.spheron.ai/login

GPUs

 

R100 (H300) Pre-Order Rubin · 288 GB HBM4 · 22 TB/s

https://www.spheron.network/gpu-rental/r100/

GB300 New Blackwell Ultra · 288 GB HBM3e · 8 TB/s

https://www.spheron.network/gpu-rental/gb300/

B300 SXM6 32 vCPUs | 184 GB RAM | 288 GB VRAM

https://www.spheron.network/gpu-rental/b300/

GB200 New Blackwell · 192 GB HBM3e · 8 TB/s

https://www.spheron.network/gpu-rental/gb200/

B200 SXM6 30 vCPUs | 184 GB RAM | 192 GB VRAM

https://www.spheron.network/gpu-rental/b200/

H100 SXM5 26 vCPUs | 116 GB RAM | 80 GB VRAM

https://www.spheron.network/gpu-rental/h100/

H200 SXM5 44 CPUs | 182 GB RAM | 141 GB VRAM

https://www.spheron.network/gpu-rental/h200/

RTX PRO 6000 8 vCPUs | 24 GB RAM | 96 GB VRAM

https://www.spheron.network/gpu-rental/rtx-pro-6000/

A100 SXM4 14 vCPUs | 100 GB RAM | 80 GB VRAM

https://www.spheron.network/gpu-rental/a100/

Other GPUs L40S, GH200, RTX 5090 & more

https://www.spheron.network/gpu-rental/

Features

 

On-Demand Instances Per-minute billing, instant deploy

https://www.spheron.network/features/on-demand-instances/

Spot Instances Up to 50% off, same hardware

https://www.spheron.network/features/spot-instances/

Reserved Commitments Volume pricing, guaranteed capacity

https://www.spheron.network/features/reserved-commitments/

Resources

 

Tools

GPU Recommender New Find the cheapest GPU to run any Hugging Face model.

https://www.spheron.network/tools/gpu-recommender/

Training Cost Calculator New Estimate GPU cost and time to train any model.

https://www.spheron.network/tools/training-cost-calculator/

Resources

Supply GPU

https://www.spheron.network/partner/

Blog

https://www.spheron.network/blog/

Docs

https://docs.spheron.ai/

API Reference

https://docs.spheron.ai/api-reference

Changelog

https://docs.spheron.ai/changelog

Customers

https://www.spheron.network/customers/

Pricing

https://www.spheron.network/pricing/

Go to platform

https://app.spheron.ai/login

Contact Sale →

https://www.spheron.network/contact/

Tutorial

How to Run LLMs Locally with Ollama: GPU-Accelerated Setup Guide

Back to Blog

https://www.spheron.network/blog/

 Written by 

Mitrasish, Co-founder & CTO, Spheron

https://www.spheron.network/authors/mitrasish/

 Nov 3, 2025

Run LLMs Locally How to Run LLMs Locally Ollama Ollama Setup Local LLM Local Inference Quantization

BANNER PLACEHOLDER

X

https://twitter.com/intent/tweet?text=How%20to%20Run%20LLMs%20Locally%20with%20Ollama%3A%20GPU-Accelerated%20Setup%20Guide&url=https%3A%2F%2Fwww.spheron.network%2Fblog%2Frun-llms-locally-ollama

 

Discord

https://sphn.wiki/discord

 

LinkedIn

https://www.linkedin.com/shareArticle?mini=true&url=https%3A%2F%2Fwww.spheron.network%2Fblog%2Frun-llms-locally-ollama&title=How%20to%20Run%20LLMs%20Locally%20with%20Ollama%3A%20GPU-Accelerated%20Setup%20Guide

 Share

Running LLMs locally means zero API costs, zero latency to a cloud endpoint, and complete data privacy. No tokens leave your machine. No rate limits. No vendor lock-in.

Ollama makes this practical. It wraps llama.cpp, the most optimized CPU/GPU inference engine for quantized models, in a simple CLI and REST API. You download a model with one command, run it with another, and get interactive chat speeds on consumer hardware. If you want direct control over llama.cpp without the Ollama layer, see the 

llama.cpp GPU server guide

https://www.spheron.network/blog/deploy-llama-cpp-server-gpu-cloud/

 for a production setup with CUDA, multi-GPU tensor split, and an OpenAI-compatible API.

This guide covers everything you need to run LLMs locally with Ollama: hardware requirements, installation, model selection, GPU acceleration, quantization, performance tuning, API integration, and when to scale to cloud GPUs. For serious production deployments, check our guide on 

deploying Llama 4 on GPU clouds

https://www.spheron.network/blog/deploy-llama-4-gpu-cloud/

.

Hardware Requirements

Local LLM performance depends primarily on VRAM (for GPU inference) or RAM (for CPU inference). The model must fit entirely in memory for acceptable speeds.

Minimum Requirements by Model Size

Model Size

Min RAM (CPU)

Min VRAM (GPU)

Example Models

1B–3B

4 GB

2 GB

Phi-3 Mini, Gemma 2B, TinyLlama

7B–8B

8 GB

6 GB

Llama 3.1 8B, Mistral 7B, Gemma 7B

13B

16 GB

10 GB

Llama 2 13B, CodeLlama 13B

20B–34B

32 GB

16 GB

CodeLlama 34B, Yi-34B

70B

64 GB

40 GB+

Llama 2 70B, Llama 3.1 70B

These are approximate requirements for Q4_K_M quantization (4-bit), which is the default Ollama format. FP16 models require roughly 4x the VRAM.

GPU vs CPU Inference Speed

Configuration

Llama 3.1 8B (Q4)

Llama 2 13B (Q4)

Llama 2 70B (Q4)

RTX 4090

https://www.spheron.network/gpu-rental/rtx-4090/

 (24 GB)

80–120 tok/s

40–60 tok/s

CPU offload (~5 tok/s)

RTX 3090 (24 GB)

50–70 tok/s

30–45 tok/s

CPU offload (~3 tok/s)

RTX 4060 Ti (16 GB)

40–60 tok/s

20–30 tok/s

Does not fit

Apple M3 Max (48 GB unified)

30–45 tok/s

20–30 tok/s

8–12 tok/s

CPU only (Ryzen 9 7950X)

8–15 tok/s

5–10 tok/s

1–3 tok/s

GPU inference is 5–10x faster than CPU. If you have an NVIDIA GPU with 8+ GB VRAM, GPU acceleration makes the difference between unusable and interactive. For detailed RTX 4090 performance analysis, see our 

RTX 4090 for AI/ML guide

https://www.spheron.network/blog/rtx-4090-for-ai-ml/

.

Installation

macOS

Download the installer from 

ollama.com/download

https://ollama.com/download

 or install via Homebrew:

bash

brew install ollama


Ollama automatically uses Apple Silicon GPU (Metal) on M1/M2/M3/M4 Macs.

Linux

bash

curl -fsSL https://ollama.com/install.sh | sh


For NVIDIA GPU support, ensure CUDA drivers are installed. Ollama detects NVIDIA GPUs automatically.

Windows

Download the installer from 

ollama.com/download

https://ollama.com/download

. Ollama supports NVIDIA GPUs on Windows via CUDA.

Verify Installation

bash

ollama --version


Running Your First Model

Download and run a model with a single command:

bash

ollama run llama3.1


This downloads the Llama 3.1 8B model (Q4_K_M quantization, ~4.7 GB) and starts an interactive chat session. First run takes a few minutes for the download; subsequent runs start in seconds.

To pull a model without starting chat:

bash

ollama pull llama3.1


Essential Commands

bash

# List installed models
ollama list

# Show model details (size, quantization, parameters)
ollama show llama3.1

# Remove a model
ollama rm llama3.1

# Run a specific quantization variant
ollama run llama3.1:70b-instruct-q4_K_M

# Run with a system prompt
ollama run llama3.1 --system "You are a Python expert. Respond with code only."


Choosing the Right Model

Ollama's 

model library

https://ollama.com/library

 contains hundreds of models. Here are the best options by use case:

Recommended Models

Model

Size

Best For

Speed (RTX 4090)

llama3.1:8b

4.7 GB

General chat, writing, reasoning

80–120 tok/s

mistral

4.1 GB

Fast general-purpose assistant

85–130 tok/s

codellama:13b

7.4 GB

Code generation and review

40–60 tok/s

llama3.1:70b

40 GB

Complex reasoning, analysis

8–12 tok/s

phi3:mini

2.2 GB

Lightweight, fast responses

100–150 tok/s

mixtral:8x7b

26 GB

Multi-task, strong reasoning

20–35 tok/s

gemma2:9b

5.4 GB

Google's efficient model

60–90 tok/s

deepseek-coder-v2:16b

8.9 GB

Advanced code generation

35–50 tok/s

qwen2.5:7b

4.4 GB

Multilingual, strong reasoning

70–110 tok/s

For most users, 

llama3.1:8b

 or 

mistral

 provides the best balance of quality and speed. If you have 24+ GB VRAM, 

mixtral:8x7b

 offers significantly better reasoning at interactive speeds. For a comprehensive look at which 2026 open-source models fit each VRAM tier (12GB through 80GB+), see the 

best local LLM by VRAM 2026 guide

https://www.spheron.network/blog/best-open-source-llms-self-host-2026-vram-guide/

.

Understanding Quantization

Ollama models use GGUF quantization, a format that compresses model weights to reduce memory usage while preserving quality. The quantization level determines the tradeoff between size, speed, and quality.

Quantization

Bits per Weight

Size (7B model)

Quality

Speed

Q2_K

2-bit

~2.8 GB

Noticeably degraded

Fastest

Q4_K_M

4-bit

~4.1 GB

Near-original quality

Fast (default)

Q5_K_M

5-bit

~4.8 GB

Very close to original

Moderate

Q6_K

6-bit

~5.5 GB

Minimal quality loss

Slower

Q8_0

8-bit

~7.2 GB

Near-lossless

Slowest quantized

FP16

16-bit

~14 GB

Full precision

Requires most VRAM

Q4_K_M

 is the sweet spot for most users, it preserves 95%+ of model quality while cutting VRAM usage by ~4x compared to FP16. For code generation or tasks requiring high precision, Q5_K_M or Q6_K is worth the extra memory.

To run a specific quantization:

bash

ollama run llama3.1:8b-instruct-q5_K_M


GPU Acceleration and Performance Tuning

Verify GPU Detection

bash

ollama ps


This shows running models and whether they're using GPU. If your NVIDIA GPU isn't detected:

bash

# Check CUDA installation
nvidia-smi

# Verify Ollama sees the GPU
OLLAMA_DEBUG=1 ollama run llama3.1


GPU Layer Offloading

For models that don't fully fit in VRAM, Ollama automatically splits layers between GPU and CPU. More GPU layers means faster inference. You can control this in a Modelfile:

FROM llama3.1
PARAMETER num_gpu 35


Context Length Configuration

Longer context windows use more memory. The default is typically 2048–4096 tokens. To increase:

bash

ollama run llama3.1 --num-ctx 8192


Each doubling of context length roughly doubles KV cache memory usage. For a 7B model at Q4:

Context Length

KV Cache Memory

Total VRAM (approx)

2,048

~0.5 GB

~5 GB

4,096

~1 GB

~5.5 GB

8,192

~2 GB

~6.5 GB

16,384

~4 GB

~8.5 GB

32,768

~8 GB

~12.5 GB

Memory Management

If you run out of VRAM, Ollama will fall back to CPU for some layers, significantly slowing inference. To optimize:

Use a smaller quantization (Q4_K_M instead of Q8_0)

Reduce context length if you don't need long conversations

Close other GPU-consuming applications

Consider a smaller model variant

API Integration

Ollama runs a local REST API on port 11434. This makes it easy to integrate into applications.

REST API

bash

# Generate a completion
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "Explain quicksort in one paragraph",
  "stream": false
}'

# Chat with message history
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1",
  "messages": [
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "stream": false
}'


Python Integration

bash

pip install ollama


python

import ollama

# Simple generation
response = ollama.generate(model="llama3.1", prompt="Write a haiku about coding")
print(response["response"])

# Chat with history
messages = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Write a Python function to check if a number is prime."},
]
response = ollama.chat(model="llama3.1", messages=messages)
print(response["message"]["content"])


LangChain Integration

bash

pip install langchain-ollama


python

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

model = OllamaLLM(model="llama3.1")
prompt = ChatPromptTemplate.from_template("Explain {topic} in simple terms.")
chain = prompt | model

result = chain.invoke({"topic": "quantum computing"})
print(result)


Building a Simple Chatbot

python

import ollama

def chat():
    messages = []
    print("Chat with Llama 3.1 (type 'exit' to quit)")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break

        messages.append({"role": "user", "content": user_input})
        response = ollama.chat(model="llama3.1", messages=messages)
        assistant_message = response["message"]["content"]
        messages.append({"role": "assistant", "content": assistant_message})
        print(f"\nAI: {assistant_message}")

chat()


Custom Models with Modelfiles

Ollama supports custom model configurations via Modelfiles, similar to Dockerfiles for LLMs:

FROM llama3.1

# Set system prompt
SYSTEM You are a senior Python developer. Always include type hints and docstrings.

# Configure parameters
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 4096


Build and run your custom model:

bash

ollama create python-expert -f Modelfile
ollama run python-expert


This is useful for creating task-specific assistants with fixed system prompts and tuned parameters.

When to Scale to Cloud GPUs

Ollama on local hardware works well for development, prototyping, and personal use. Local GPUs have limitations:

Limitation

Local GPU

Cloud GPU (Spheron)

VRAM

24 GB (RTX 4090)

Up to 141 GB (H200)

Largest model

13B (comfortable)

70B+ (single GPU)

Multi-GPU

PCIe bottleneck

NVLink at 600–900 GB/s

Uptime

Personal machine

24/7 dedicated server

Scaling

Single GPU

1–8 GPU clusters

When your models outgrow 24 GB, require 24/7 uptime, or need multi-GPU parallelism, 

Spheron

https://app.spheron.ai/

 provides cloud GPU instances starting at $0.55/hr with pre-configured CUDA environments and full root access. For comprehensive guidance, see our 

best NVIDIA GPUs for LLMs guide

https://www.spheron.network/blog/best-nvidia-gpus-for-llms/

 and 

GPU memory requirements for LLMs

https://www.spheron.network/blog/gpu-memory-requirements-llm/

. If you're deciding whether to move from Ollama to a production inference server, our 

Ollama vs vLLM comparison

https://www.spheron.network/blog/ollama-vs-vllm/

 covers throughput numbers and migration steps in detail.

For more advanced GPU-based ML workflows, see our guide on 

running Karpathy's autoresearch on Spheron

https://www.spheron.network/blog/karpathy-autoresearch-spheron-gpu/

.

Explore GPU options on Spheron →

https://app.spheron.ai/

STEPS / 06

Quick Setup Guide

01

Check your hardware meets minimum requirements

Verify you have a GPU with sufficient VRAM for your target model. A 7B-8B model needs 6 GB VRAM (RTX 3060 or better). For CPU-only inference, you need at least 8 GB RAM. Apple Silicon Macs work with Metal acceleration using unified memory.

 

2. 02

Install Ollama on your system

Download and install Ollama from ollama.com. On macOS use the .dmg installer, on Linux run the install script from the official site, on Windows use the .exe installer. Ollama automatically detects your GPU and configures acceleration.

 

3. 03

Download and run your first model

Run 'ollama pull llama3.1:8b' to download a model. Then run 'ollama run llama3.1:8b' to start an interactive chat session. Ollama downloads the Q4_K_M quantized version by default, which balances quality and VRAM usage.

 

4. 04

Configure GPU acceleration and performance

Ollama auto-detects NVIDIA GPUs via CUDA and Apple Silicon via Metal. For multi-GPU setups, set CUDA_VISIBLE_DEVICES to select specific GPUs. Adjust context length and batch size for optimal throughput on your hardware.

 

5. 05

Integrate via the REST API

Ollama exposes an OpenAI-compatible REST API at localhost port 11434. Use the /api/generate endpoint for completions or /api/chat for conversational use. This lets you integrate local LLMs into any application using standard HTTP requests.

 

6. 06

Choose when to scale to cloud GPUs

If you need to serve larger models (70B+), handle concurrent users, or require consistent throughput, deploy on cloud GPUs via Spheron. Local Ollama is ideal for development and testing; cloud GPUs handle production workloads with dedicated VRAM and no shared resources.

FAQ / 06

Frequently Asked Questions

01 How much VRAM do I need to run Llama 3.1 8B?

The Q4_K_M quantized version (Ollama's default) requires approximately 5–6 GB of VRAM including KV cache. Any GPU with 8 GB VRAM (RTX 3060, RTX 4060, etc.) can run it comfortably. On CPU, you need at least 8 GB of RAM, but inference will be 5–10x slower.

02 Can I run Ollama on Apple Silicon Macs?

Yes. Ollama automatically uses Metal GPU acceleration on M1/M2/M3/M4 Macs. Apple Silicon's unified memory architecture means the GPU can access all system RAM, so a Mac with 32 GB unified memory can run models that wouldn't fit on a 24 GB discrete GPU. Performance is roughly 60–70% of an equivalent NVIDIA GPU.

03 What's the difference between Ollama and llama.cpp?

Ollama is a user-friendly wrapper around llama.cpp. It handles model downloading, GGUF format management, GPU detection, and provides a REST API, all things you'd configure manually with raw llama.cpp. If you want maximum control and custom builds, use llama.cpp directly. For ease of use, Ollama is the better choice.

04 Can I run multiple models simultaneously?

Yes. Ollama loads models on demand and keeps them in memory. You can run multiple models by making API calls to different model names. However, each loaded model consumes VRAM, so running two 7B models simultaneously requires roughly 10–12 GB of VRAM.

05 How does quantization affect output quality?

Q4_K_M (4-bit) preserves approximately 95% of the original model's quality for most tasks. You may notice slight degradation in complex reasoning, math, or code generation compared to FP16. Q5_K_M and Q6_K offer better quality at the cost of more VRAM. For most conversational and writing tasks, Q4_K_M is indistinguishable from the full-precision model.

06 Is Ollama suitable for production use?

Ollama is excellent for development, testing, and personal use. For production serving with multiple concurrent users, SLA requirements, and load balancing, consider dedicated inference servers using vLLM, TensorRT-LLM, or Triton Inference Server on cloud GPUs. Ollama's REST API can serve light production loads but lacks features like batching, auto-scaling, and health monitoring. For a direct comparison with vLLM on the same hardware, see 

Ollama vs vLLM: Which Should You Use to Self-Host LLMs?

/blog/ollama-vs-vllm/

.

Back to all posts

https://www.spheron.network/blog/

Build what's next.

The most cost-effective platform for building, training, and scaling machine learning models-ready when you are.

Rent Now

Contact Sale

GLOBAL COMPUTE, BROUGHT TO YOU BY

Bare-metal GPU infrastructure for AI teams that need scale, speed, and simplicity.

Deploy Now

https://app.spheron.ai/signup

Contact Sale →

https://www.spheron.network/contact/

Product

App

https://app.spheron.ai/

Pricing

https://www.spheron.network/pricing/

Customers

https://www.spheron.network/customers/

GPU Catalog

https://www.spheron.network/gpu-rental/

Supply GPU

https://www.spheron.network/partner/

Features

On-Demand Instances

https://www.spheron.network/features/on-demand-instances/

Spot Instances

https://www.spheron.network/features/spot-instances/

Reserved Commitments

https://www.spheron.network/features/reserved-commitments/

Tools

GPU Recommender

https://www.spheron.network/tools/gpu-recommender/

Training Cost Calculator

https://www.spheron.network/tools/training-cost-calculator/

Community

Discord

https://sphn.wiki/discord

X (Twitter)

https://x.com/spheronai

LinkedIn

https://www.linkedin.com/company/spheron-ai/

YouTube

https://sphn.wiki/yt

Telegram

https://sphn.wiki/tg

Resources

Documentation

https://docs.spheron.ai/

API Reference

https://docs.spheron.ai/api-reference

Blog

https://www.spheron.network/blog/

GitHub

https://github.com/spheron-core

Changelog

https://docs.spheron.ai/changelog

GPUs

NVIDIA R100

https://www.spheron.network/gpu-rental/r100/

NVIDIA GB300

https://www.spheron.network/gpu-rental/gb300/

NVIDIA GB200

https://www.spheron.network/gpu-rental/gb200/

NVIDIA B300

https://www.spheron.network/gpu-rental/b300/

NVIDIA H100

https://www.spheron.network/gpu-rental/h100/

NVIDIA B200

https://www.spheron.network/gpu-rental/b200/

NVIDIA H200

https://www.spheron.network/gpu-rental/h200/

NVIDIA A100

https://www.spheron.network/gpu-rental/a100/

NVIDIA GH200

https://www.spheron.network/gpu-rental/gh200/

NVIDIA L40S

https://www.spheron.network/gpu-rental/l40s/

RTX 4090

https://www.spheron.network/gpu-rental/rtx-4090/

RTX 5090

https://www.spheron.network/gpu-rental/rtx-5090/

RTX PRO 6000

https://www.spheron.network/gpu-rental/rtx-pro-6000/

Product

App

https://app.spheron.ai/

Pricing

https://www.spheron.network/pricing/

Customers

https://www.spheron.network/customers/

GPU Catalog

https://www.spheron.network/gpu-rental/

Supply GPU

https://www.spheron.network/partner/

Resources

Documentation

https://docs.spheron.ai/

API Reference

https://docs.spheron.ai/api-reference

Blog

https://www.spheron.network/blog/

GitHub

https://github.com/spheron-core

Changelog

https://docs.spheron.ai/changelog

Tools

GPU Recommender

https://www.spheron.network/tools/gpu-recommender/

Training Cost Calculator

https://www.spheron.network/tools/training-cost-calculator/

Features

On-Demand Instances

https://www.spheron.network/features/on-demand-instances/

Spot Instances

https://www.spheron.network/features/spot-instances/

Reserved Commitments

https://www.spheron.network/features/reserved-commitments/

Community

Discord

https://sphn.wiki/discord

X (Twitter)

https://x.com/spheronai

LinkedIn

https://www.linkedin.com/company/spheron-ai/

YouTube

https://sphn.wiki/yt

Telegram

https://sphn.wiki/tg

GPUs

NVIDIA R100

https://www.spheron.network/gpu-rental/r100/

NVIDIA GB300

https://www.spheron.network/gpu-rental/gb300/

NVIDIA GB200

https://www.spheron.network/gpu-rental/gb200/

NVIDIA B300

https://www.spheron.network/gpu-rental/b300/

NVIDIA H100

https://www.spheron.network/gpu-rental/h100/

NVIDIA B200

https://www.spheron.network/gpu-rental/b200/

NVIDIA H200

https://www.spheron.network/gpu-rental/h200/

NVIDIA A100

https://www.spheron.network/gpu-rental/a100/

NVIDIA GH200

https://www.spheron.network/gpu-rental/gh200/

NVIDIA L40S

https://www.spheron.network/gpu-rental/l40s/

RTX 4090

https://www.spheron.network/gpu-rental/rtx-4090/

RTX 5090

https://www.spheron.network/gpu-rental/rtx-5090/

RTX PRO 6000

https://www.spheron.network/gpu-rental/rtx-pro-6000/

© 2026 SPHERON NETWORK. ALL RIGHTS RESERVED.

Privacy Policy

https://www.spheron.network/privacy/

 

Terms & Conditions

https://www.spheron.network/Spheron_Website_Terms_of_Use.pdf

 

Contact Us

https://www.spheron.network/contact/

Available Now · Bare Metal

8× NVIDIA H100 PCIe Nodes

A dedicated 8-GPU H100 node, NVLink-bridged for fast multi-GPU training and wired with 400G InfiniBand for scale-out.

GPU

8× H100 80GB PCIe

HBM2e · 640GB aggregate

CPU

Dual EPYC 9454

96 cores · 2.75 GHz

Memory

1.5TB DDR5-4800

24× 64GB RDIMM

Network

400G InfiniBand

ConnectX-7 NDR

Storage

~88TB

SAS + dual NVMe · MegaRAID

Power

3000W redundant

Titanium-grade PSU

Only 10 nodes available

Submit your request now before it's too late. Reserve the full server and our team will reach out with pricing for your workload.

Maybe Later

→

Rent This Server
