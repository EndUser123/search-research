---
source_id: "92211d9c-afc9-48bf-bff4-b9c3effb5fa5"
title: "SC117/Ornith-1.0-9B-heretic-MTP - Hugging Face"
notebook_id: 831e0613-f723-4d87-aaeb-1d4b5a061496
url: https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP
type: web_page
exported: 2026-07-28
---

# SC117/Ornith-1.0-9B-heretic-MTP - Hugging Face
SC117/Ornith-1.0-9B-heretic-MTP · Hugging Face

Hugging Face's logo Hugging Face

https://huggingface.co/

Models

https://huggingface.co/models

Datasets

https://huggingface.co/datasets

Spaces

https://huggingface.co/spaces

Buckets new

https://huggingface.co/storage

Docs

https://huggingface.co/docs

Enterprise

https://huggingface.co/enterprise

Pricing

https://huggingface.co/pricing

Website

Tasks

https://huggingface.co/tasks

HuggingChat

https://huggingface.co/chat

Collections

https://huggingface.co/collections

Languages

https://huggingface.co/languages

Organizations

https://huggingface.co/organizations

Community

Blog

https://huggingface.co/blog

Posts

https://huggingface.co/posts

Daily Papers

https://huggingface.co/papers

Learn

https://huggingface.co/learn

Discord

https://huggingface.co/join/discord

Forum

https://discuss.huggingface.co/

GitHub

https://github.com/huggingface

Solutions

Team & Enterprise

https://huggingface.co/enterprise

Hugging Face PRO

https://huggingface.co/pro

Enterprise Support

https://huggingface.co/support

Inference Providers

https://huggingface.co/inference/models

Inference Endpoints

https://huggingface.co/inference-endpoints

Storage Buckets

https://huggingface.co/storage

Log In

https://huggingface.co/login

Sign Up

https://huggingface.co/join

SC117

https://huggingface.co/SC117

 / 

Ornith-1.0-9B-heretic-MTP

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP

 like 1

Text Generation

https://huggingface.co/models?pipeline_tag=text-generation

Transformers

https://huggingface.co/models?library=transformers

Safetensors

https://huggingface.co/models?library=safetensors

qwen3_5

https://huggingface.co/models?other=qwen3_5

reasoning

https://huggingface.co/models?other=reasoning

agentic-coding

https://huggingface.co/models?other=agentic-coding

mtp

https://huggingface.co/models?other=mtp

heretic

https://huggingface.co/models?other=heretic

abliteration

https://huggingface.co/models?other=abliteration

multimodal

https://huggingface.co/models?other=multimodal

conversational

https://huggingface.co/models?other=conversational

License: mit

Model card

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP

 

Files Files and versions xet

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP/tree/main

Community

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP/discussions

Deploy

Copy to bucket new

Use this model

Instructions to use SC117/Ornith-1.0-9B-heretic-MTP with libraries, inference providers, notebooks, and local apps. Follow these links to get started.

Libraries

Transformers

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP?library=transformers

 How to use SC117/Ornith-1.0-9B-heretic-MTP with Transformers:

# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-generation", model="SC117/Ornith-1.0-9B-heretic-MTP")
messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe(messages)


# Load model directly
from transformers import AutoProcessor, AutoModelForCausalLM

processor = AutoProcessor.from_pretrained("SC117/Ornith-1.0-9B-heretic-MTP")
model = AutoModelForCausalLM.from_pretrained("SC117/Ornith-1.0-9B-heretic-MTP")
messages = [
    {"role": "user", "content": "Who are you?"},
]
inputs = processor.apply_chat_template(
	messages,
	add_generation_prompt=True,
	tokenize=True,
	return_dict=True,
	return_tensors="pt",
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=40)
print(processor.decode(outputs[0][inputs["input_ids"].shape[-1]:]))


Notebooks

Google Colab

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP/colab

Kaggle

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP/kaggle

Local Apps 

Settings

https://huggingface.co/settings/local-apps

vLLM

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP?local-app=vllm

 How to use SC117/Ornith-1.0-9B-heretic-MTP with vLLM:

Install from pip and serve model

# Install vLLM from pip:
pip install vllm
# Start the vLLM server:
vllm serve "SC117/Ornith-1.0-9B-heretic-MTP"
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:8000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "SC117/Ornith-1.0-9B-heretic-MTP",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'


Use Docker

docker model run hf.co/SC117/Ornith-1.0-9B-heretic-MTP


SGLang

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP?local-app=sglang

 How to use SC117/Ornith-1.0-9B-heretic-MTP with SGLang:

Install from pip and serve model

# Install SGLang from pip:
pip install sglang
# Start the SGLang server:
python3 -m sglang.launch_server \
    --model-path "SC117/Ornith-1.0-9B-heretic-MTP" \
    --host 0.0.0.0 \
    --port 30000
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:30000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "SC117/Ornith-1.0-9B-heretic-MTP",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'


Use Docker images

docker run --gpus all \
    --shm-size 32g \
    -p 30000:30000 \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HF_TOKEN=<secret>" \
    --ipc=host \
    lmsysorg/sglang:latest \
    python3 -m sglang.launch_server \
        --model-path "SC117/Ornith-1.0-9B-heretic-MTP" \
        --host 0.0.0.0 \
        --port 30000
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:30000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "SC117/Ornith-1.0-9B-heretic-MTP",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'


Docker Model Runner

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP?local-app=docker-model-runner

 How to use SC117/Ornith-1.0-9B-heretic-MTP with Docker Model Runner:

docker model run hf.co/SC117/Ornith-1.0-9B-heretic-MTP


Browse Quantizations

https://huggingface.co/models?other=base_model:quantized:SC117/Ornith-1.0-9B-heretic-MTP

 to use this model in llama.cpp, Ollama, LM Studio, or any compatible app.

GGUF Quantizations

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP#gguf-quantizations

Files

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP#files

Links

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP#links

Citation

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP#citation

heretic MTP Vision MIT

Ornith-1.0-9B-heretic-MTP

English | 

📖 中文文档

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP/blob/main/README_zh.md

Self-improving agentic coding model · heretic ARA-LoRA abliterated · MTP injected · BF16 Safetensors

🐦 About Ornith

Ornith-1.0-9B

https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B

 is a self-improving agentic coding model from 

DeepReinforce AI

https://deep-reinforce.com/ornith.html

, post-trained on top of Qwen3.5 (9B Dense) with RL to jointly optimize scaffold generation and solution rollouts.

It achieves strong performance on Terminal-Bench 2.1, SWE-Bench Verified, NL2Repo, and OpenClaw among open-source models of comparable size.

This repository contains the 

BF16 Safetensors

 version with 

heretic

 ARA-LoRA abliteration for uncensored use, 

MTP

 layers injected from Qwen3.5-9B, and 

mmproj-F16

 vision projector. For GGUF quantizations, see 

SC117/Ornith-1.0-9B-heretic-MTP-GGUF

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP-GGUF

. 

License: MIT.

🧠 Model Details

Architecture

Qwen3.5 Dense

Parameters

~9B (all parameters active)

Layers

33 transformer layers + 1 MTP layer

Context

262,144 tokens

Attention

16 heads, 4 KV heads (GQA)

Precision

BF16

MTP

1 MTP layer, injected from Qwen3.5-9B (same architecture, compatible weights)

Thinking

Yes ( blocks)

License

MIT

🔓 heretic ARA-LoRA Abliteration

This model is abliterated using 

heretic

https://github.com/kabachuha/heretic

 with the ARA-LoRA method (Arbitrary-Rank Ablation with LoRA). ARA-LoRA identifies and removes refusal behavior by ablating specific directions in the model's weight space while preserving general capabilities through KL divergence control.

Key ablation parameters (Trial 76 of 250, best result):

Target Layers

Layers 14–16

preserve_good_behavior_weight

0.7319

steer_bad_behavior_weight

0.0001

overcorrect_relative_weight

1.1086

neighbor_count

7

Result

KL divergence: 

0.0288

 (< 0.05 ✅), Refusals: 

3/100

 (< 10 ✅)

Quantization: bnb_4bit · Batch size: 32 · Target: KL < 0.05, Refusals < 10/100

⚡ MTP (Multi-Token Prediction)

MTP layers are 

injected from the original Qwen3.5-9B base model

 (same architecture, compatible weights). MTP enables the model to predict multiple future tokens simultaneously, improving generation speed and coherence.

The MTP layer includes 

mtp.fc.weight

 and 

mtp.layers.0.*

 tensors, added on top of the 33 standard transformer layers.

Requires 

--chat-template chatml

 for proper thinking mode rendering in llama.cpp.

📊 BenchLocal Results (Q6_K, 7.6 GB)

Metric

ToolCall-15

BugFind-15

HermesAgent-20

Max

Eff.

Score

100

94

79

89.8

68.8

RTX 5070 Ti · 21 total retries · ToolCall perfect 100/100 🏆

🚀 Usage (Transformers)

pip install

pip install transformers torch accelerate

Load model

from transformers import AutoModelForCausalLM, AutoTokenizer model = AutoModelForCausalLM.from_pretrained("SC117/Ornith-1.0-9B-heretic-MTP", torch_dtype="bfloat16", device_map="auto") tokenizer = AutoTokenizer.from_pretrained("SC117/Ornith-1.0-9B-heretic-MTP")

llama.cpp

Convert to GGUF first, then: ./llama-server -m model-Q6_K.gguf --chat-template chatml -ngl 99 -c 8192

🎛 Recommended Settings

Parameter

Value

temperature

0.6

top_p

0.95

top_k

20

From official DeepReinforce AI model card.

GGUF Quantizations

For GGUF quantized versions (Q8_0, Q6_K, Q4_K_M), see: 

SC117/Ornith-1.0-9B-heretic-MTP-GGUF

https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP-GGUF

Files

File

Description

model-*.safetensors

Model weights (BF16, 5 shards)

config.json

Model configuration

tokenizer.json

Tokenizer

tokenizer_config.json

Tokenizer configuration

chat_template.jinja

Chat template for thinking mode

model.safetensors.index.json

Weight index

Links

Original Model

: 

https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B

https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B

Ornith Blog

: 

https://deep-reinforce.com/ornith.html

https://deep-reinforce.com/ornith.html

heretic Abliteration

: 

https://github.com/p-e-w/heretic

https://github.com/p-e-w/heretic

BenchLocal Results

: 

https://scorp1o117.github.io/benchlocal-results/

https://scorp1o117.github.io/benchlocal-results/

Citation

@misc{ornith-9b,
    title = {{Ornith-1.0-9B}: Agentic Coding, Open to All},
    url = {https://deep-reinforce.com/ornith_1_0.html},
    author = {{DeepReinforce Team}},
    year = {2026}
}


Downloads last month

7

Safetensors 

https://huggingface.co/docs/safetensors

Model size

9B params

Tensor type

BF16

·

Chat template

Files info

Inference Providers 

NEW

https://huggingface.co/docs/inference-providers

Text Generation

https://huggingface.co/tasks/text-generation

This model isn't deployed by any Inference Provider. 

🙋 Ask for provider support

https://huggingface.co/spaces/huggingface/InferenceSupport/discussions/new?title=SC117/Ornith-1.0-9B-heretic-MTP&description=React%20to%20this%20comment%20with%20an%20emoji%20to%20vote%20for%20%5BSC117%2FOrnith-1.0-9B-heretic-MTP%5D(%2FSC117%2FOrnith-1.0-9B-heretic-MTP)%20to%20be%20supported%20by%20Inference%20Providers.%0A%0A(optional)%20Which%20providers%20are%20you%20interested%20in%3F%20(Novita%2C%20Hyperbolic%2C%20Together%E2%80%A6)%0A

Model tree for SC117/Ornith-1.0-9B-heretic-MTP 

https://huggingface.co/docs/hub/model-cards#specifying-a-base-model

Base model

deepreinforce-ai/Ornith-1.0-9B

https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B

Finetuned

( 

16

https://huggingface.co/models?other=base_model:finetune:deepreinforce-ai/Ornith-1.0-9B

)

this model

Quantizations 

https://huggingface.co/models?apps=llama.cpp&other=base_model:quantized:SC117/Ornith-1.0-9B-heretic-MTP

 

https://huggingface.co/models?apps=lmstudio&other=base_model:quantized:SC117/Ornith-1.0-9B-heretic-MTP

 

https://huggingface.co/models?apps=jan&other=base_model:quantized:SC117/Ornith-1.0-9B-heretic-MTP

 

https://huggingface.co/models?apps=ollama&other=base_model:quantized:SC117/Ornith-1.0-9B-heretic-MTP

2 models

https://huggingface.co/models?other=base_model:quantized:SC117/Ornith-1.0-9B-heretic-MTP

Collection including SC117/Ornith-1.0-9B-heretic-MTP

[

Ornith-1.0

Collection a self-improving family of open-source models for agentic coding. • 3 items • Updated 2 days ago • 2](https://huggingface.co/collections/SC117/ornith-10)

System theme

Company

TOS

https://huggingface.co/terms-of-service

 

Privacy

https://huggingface.co/privacy

 

About

https://huggingface.co/huggingface

 

Careers

https://apply.workable.com/huggingface/

 

https://huggingface.co/

Website

Models

https://huggingface.co/models

 

Datasets

https://huggingface.co/datasets

 

Spaces

https://huggingface.co/spaces

 

Pricing

https://huggingface.co/pricing

 

Docs

https://huggingface.co/docs

Inference providers allow you to run inference using different serverless providers.
