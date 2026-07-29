---
source_id: "a66649a5-a0fd-4eba-b8ae-281ebfd61ebd"
title: "protoLabsAI/Ornith-1.0-9B-MTP-GGUF - Hugging Face"
notebook_id: 831e0613-f723-4d87-aaeb-1d4b5a061496
url: https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF
type: web_page
exported: 2026-07-28
---

# protoLabsAI/Ornith-1.0-9B-MTP-GGUF - Hugging Face
protoLabsAI/Ornith-1.0-9B-MTP-GGUF · Hugging Face

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

protoLabsAI

https://huggingface.co/protoLabsAI

 / 

Ornith-1.0-9B-MTP-GGUF

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF

 like 38 Follow

 

protoLabsAI 30

Text Generation

https://huggingface.co/models?pipeline_tag=text-generation

GGUF

https://huggingface.co/models?library=gguf

llama.cpp

https://huggingface.co/models?other=llama.cpp

speculative-decoding

https://huggingface.co/models?other=speculative-decoding

mtp

https://huggingface.co/models?other=mtp

multi-token-prediction

https://huggingface.co/models?other=multi-token-prediction

qwen3.5

https://huggingface.co/models?other=qwen3.5

conversational

https://huggingface.co/models?other=conversational

License: mit

Model card

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF

 

Files Files and versions xet

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF/tree/main

Community 5

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF/discussions

Deploy

Copy to bucket new

Use this model

Instructions to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with libraries, inference providers, notebooks, and local apps. Follow these links to get started.

Libraries

llama-cpp-python

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF?library=llama-cpp-python

 How to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with llama-cpp-python:

# !pip install llama-cpp-python

from llama_cpp import Llama

llm = Llama.from_pretrained(
	repo_id="protoLabsAI/Ornith-1.0-9B-MTP-GGUF",
	filename="mtp-ornith-9b-mtp-kl-Q8_0.gguf",
)


llm.create_chat_completion(
	messages = [
		{
			"role": "user",
			"content": "What is the capital of France?"
		}
	]
)


Notebooks

Google Colab

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF/colab

Kaggle

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF/kaggle

Local Apps 

Settings

https://huggingface.co/settings/local-apps

llama.cpp

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF?local-app=llama.cpp

 How to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with llama.cpp:

Install (macOS, Linux)

curl -LsSf https://llama.app/install.sh | sh
# Start a local OpenAI-compatible server with a web UI:
llama serve -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M
# Run inference directly in the terminal:
llama cli -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Install from WinGet (Windows)

winget install llama.cpp
# Start a local OpenAI-compatible server with a web UI:
llama serve -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M
# Run inference directly in the terminal:
llama cli -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Use pre-built binary

# Download pre-built binary from:
# https://github.com/ggerganov/llama.cpp/releases
# Start a local OpenAI-compatible server with a web UI:
./llama-server -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M
# Run inference directly in the terminal:
./llama-cli -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Build from source code

git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
cmake -B build
cmake --build build -j --target llama-server llama-cli
# Start a local OpenAI-compatible server with a web UI:
./build/bin/llama-server -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M
# Run inference directly in the terminal:
./build/bin/llama-cli -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Use Docker

docker model run hf.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


LM Studio

lmstudio://open_from_hf?model=protoLabsAI/Ornith-1.0-9B-MTP-GGUF

Jan

jan://models/huggingface/protoLabsAI/Ornith-1.0-9B-MTP-GGUF

vLLM

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF?local-app=vllm

 How to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with vLLM:

Install from pip and serve model

# Install vLLM from pip:
pip install vllm
# Start the vLLM server:
vllm serve "protoLabsAI/Ornith-1.0-9B-MTP-GGUF"
# Call the server using curl (OpenAI-compatible API):
curl -X POST "http://localhost:8000/v1/chat/completions" \
	-H "Content-Type: application/json" \
	--data '{
		"model": "protoLabsAI/Ornith-1.0-9B-MTP-GGUF",
		"messages": [
			{
				"role": "user",
				"content": "What is the capital of France?"
			}
		]
	}'


Use Docker

docker model run hf.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Ollama

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF?local-app=ollama

 How to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with Ollama:

ollama run hf.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Unsloth Studio

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF?local-app=unsloth

 How to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with Unsloth Studio:

Install Unsloth Studio (macOS, Linux, WSL)

curl -fsSL https://unsloth.ai/install.sh | sh
# Run unsloth studio
unsloth studio -H 0.0.0.0 -p 8888
# Then open http://localhost:8888 in your browser
# Search for protoLabsAI/Ornith-1.0-9B-MTP-GGUF to start chatting


Install Unsloth Studio (Windows)

irm https://unsloth.ai/install.ps1 | iex
# Run unsloth studio
unsloth studio -H 0.0.0.0 -p 8888
# Then open http://localhost:8888 in your browser
# Search for protoLabsAI/Ornith-1.0-9B-MTP-GGUF to start chatting


Using HuggingFace Spaces for Unsloth

# No setup required
# Open https://huggingface.co/spaces/unsloth/studio in your browser
# Search for protoLabsAI/Ornith-1.0-9B-MTP-GGUF to start chatting


Pi

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF?local-app=pi

 How to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with Pi:

Start the llama.cpp server

# Install llama.cpp:
brew install llama.cpp
# Start a local OpenAI-compatible server:
llama serve -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Configure the model in Pi

# Install Pi:
npm install -g @mariozechner/pi-coding-agent
# Add to ~/.pi/agent/models.json:
{
  "providers": {
    "llama-cpp": {
      "baseUrl": "http://localhost:8080/v1",
      "api": "openai-completions",
      "apiKey": "none",
      "models": [
        {
          "id": "protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M"
        }
      ]
    }
  }
}


Run Pi

# Start Pi in your project directory:
pi


Hermes Agent new

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF?local-app=hermes-agent

 How to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with Hermes Agent:

Start the llama.cpp server

# Install llama.cpp:
brew install llama.cpp
# Start a local OpenAI-compatible server:
llama serve -hf protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Configure Hermes

# Install Hermes:
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes setup
# Point Hermes at the local server:
hermes config set model.provider custom
hermes config set model.base_url http://127.0.0.1:8080/v1
hermes config set model.default protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Run Hermes

hermes


Atomic Chat new

atomic-chat://models/huggingface/protoLabsAI/Ornith-1.0-9B-MTP-GGUF

Docker Model Runner

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF?local-app=docker-model-runner

 How to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with Docker Model Runner:

docker model run hf.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Lemonade

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF?local-app=lemonade

 How to use protoLabsAI/Ornith-1.0-9B-MTP-GGUF with Lemonade:

Pull the model

# Download Lemonade from https://lemonade-server.ai/
lemonade pull protoLabsAI/Ornith-1.0-9B-MTP-GGUF:Q4_K_M


Run and chat with the model

lemonade run user.Ornith-1.0-9B-MTP-GGUF-Q4_K_M


List all available models

lemonade list


Ornith-1.0-9B MTP — GGUF (llama.cpp speculative decoding)

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#ornith-10-9b-mtp--gguf-llamacpp-speculative-decoding

Files

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#files

Run

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#run

Benchmarks (RTX A6000, ctx 8192, flash-attn, greedy; 6-prompt code+general mix)

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#benchmarks-rtx-a6000-ctx-8192-flash-attn-greedy-6-prompt-codegeneral-mix

n-max sweep (Q8_0)

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#n-max-sweep-q8_0

Across quants (MTP n-max 3)

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#across-quants-mtp-n-max-3

"Lossless" — read this

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#lossless--read-this

How these were built

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#how-these-were-built

Common error: wrong number of tensors expected 442 got 427

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#common-error-wrong-number-of-tensors-expected-442-got-427

Provenance & license

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF#provenance--license

Ornith-1.0-9B MTP — GGUF (llama.cpp speculative decoding)

GGUF builds of 

deepreinforce-ai/Ornith-1.0-9B

https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B

 

with the KL-distilled MTP draft head

 from 

protoLabsAI/Ornith-1.0-9B-MTP

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP

 baked in — so llama.cpp does 

lossless multi-token (self-)speculative decoding

 out of the box, no separate draft model required.

~1.4–1.7× single-stream decode speedup on a single RTX A6000

, distribution-lossless. The head's per-token acceptance on llama.cpp matches the vLLM reference ( 

0.766

 here vs 0.762).

Just want the base model with no MTP? Use 

deepreinforce-ai/Ornith-1.0-9B-GGUF

 . These files add the 

nextn

 head on top of the same trunk.

Files

File

Form

Size

Use

ornith-9b-mtp-kl-Q8_0.gguf

bundled (trunk + head)

9.8 GB

highest quality / biggest relative speedup

ornith-9b-mtp-kl-Q6_K.gguf

bundled

7.6 GB

near-lossless quant

ornith-9b-mtp-kl-Q5_K_M.gguf

bundled

6.6 GB

balanced

ornith-9b-mtp-kl-Q4_K_M.gguf

bundled

5.8 GB

fastest k-quant

ornith-9b-mtp-kl-IQ4_XS.gguf

bundled (imatrix)

5.5 GB

low VRAM, near-Q4 quality

ornith-9b-mtp-kl-IQ3_M.gguf

bundled (imatrix)

4.7 GB

lower VRAM

ornith-9b-mtp-kl-IQ2_M.gguf

bundled (imatrix)

3.9 GB

very low VRAM

 (~5 GB to serve)

ornith-9b-mtp-kl-BF16.gguf

bundled (full precision)

18.4 GB

the master; re-quantize from this

mtp-ornith-9b-mtp-kl-Q8_0.gguf

standalone draft head

2.4 GB

attach to a base GGUF via 

--model-draft

The 

IQ

 quants are i-quants built with an importance matrix (calibrated on the trunk) for quality at low bit-rates, with the 

MTP nextn head pinned to Q8_0

 so speculative-decode acceptance holds even on the 2-bit trunk (verified ~0.81–0.84 accept on IQ2_M–IQ4_XS, on par with the k-quants). Serve them exactly like the k-quants ( 

--spec-type draft-mtp

 ).

Requires 

llama.cpp ≥ b9616

 (Qwen3.5 

qwen35

 arch + 

--spec-type draft-mtp

 ).

Run

Bundled (recommended)

 — the head travels in the file:

llama-server --model ornith-9b-mtp-kl-Q4_K_M.gguf \
  --n-gpu-layers 99 --ctx-size 8192 --flash-attn on --jinja \
  --spec-type draft-mtp --spec-draft-n-max 3


Standalone draft

 — pair the small head with any base Ornith-9B GGUF:

llama-server --model ornith-1.0-9b-Q4_K_M.gguf \
  --model-draft mtp-ornith-9b-mtp-kl-Q8_0.gguf \
  --spec-type draft-mtp --spec-draft-n-max 3 \
  --n-gpu-layers 99 --ctx-size 8192 --flash-attn on --jinja


--spec-draft-n-max

 is the draft depth: 

2

 maximizes acceptance, 

3

 maximizes throughput, 4 starts to regress. Tune per workload.

Benchmarks (RTX A6000, ctx 8192, flash-attn, greedy; 6-prompt code+general mix)

n-max sweep (Q8_0)

config

decode tok/s

acceptance

speedup

base (no MTP)

71.0

—

1.00×

MTP n-max 2

118.3

0.766

1.67×

MTP n-max 3

122.6

0.651

1.73×

MTP n-max 4

120.8

0.565

1.70×

Across quants (MTP n-max 3)

quant

base tok/s

MTP tok/s

speedup

acceptance

Q4_K_M

105.4

145.3

1.38×

0.659

Q8_0

71.0

122.6

1.73×

0.651

Acceptance is 

quant-stable

 (~0.65 @ n-max 3 even with the Q4 head). Q4_K_M is fastest in absolute terms; the 

relative

 MTP gain grows with precision (Q8's slow bandwidth-bound baseline has more to gain from the parallel verify).

"Lossless" — read this

MTP speculative decoding is 

distribution-lossless

: every drafted token is verified against the target, so the output distribution is unchanged. It is 

not bitwise-identical

 to plain decode at greedy/temp 0 — the batched verification path computes target logits in a different floating-point reduction order than sequential decoding, which can flip a greedy argmax and fork the text. Both outputs are equally valid and equal quality; this is expected llama.cpp behavior, not a defect of these weights.

How these were built

# 1. graft the mtp.* head into the base trunk (15 tensors, 1 nextn layer)
python graft.py --donor protoLabsAI/Ornith-1.0-9B-MTP \
                --target deepreinforce-ai/Ornith-1.0-9B --out ./ornith-9b-mtp-kl
# 2. convert (the converter remaps mtp.* -> blk.<32>.nextn.* automatically)
python convert_hf_to_gguf.py ./ornith-9b-mtp-kl --outfile out/...-BF16.gguf --outtype bf16
python convert_hf_to_gguf.py ./ornith-9b-mtp-kl --outfile out/ --outtype q8_0 --mtp   # standalone draft
# 3. quantize
llama-quantize out/...-BF16.gguf out/...-Q4_K_M.gguf Q4_K_M


The 

graft.py

 recipe and the KL-distillation details live in the head repo 

protoLabsAI/Ornith-1.0-9B-MTP

https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP

 .

Common error: 

wrong number of tensors expected 442 got 427

(or 

got 426

 for the smaller quants — the gap is the 

15 mtp.* head tensors

.)

This happens if you run 

convert_hf_to_gguf.py

 directly on the 

base

 

deepreinforce-ai/Ornith-1.0-9B

 without grafting the head first. The base keeps 

mtp_num_hidden_layers: 1

 in its 

config.json

 ( 

text_config

 ) but 

ships none of the mtp.* weights

 — so the converter writes 

block_count = 33

 / 

nextn_predict_layers = 1

 into the GGUF metadata (declaring the 

blk.32

 MTP layer) while leaving those 15 tensors empty. llama.cpp then expects 442 tensors and finds 427 → load fails.

Fix:

 graft the head into the trunk 

before

 converting (step 1 above), then convert with no 

--mtp

 flag. Note that only 4 of the 15 head tensors are named 

blk.32.nextn.*

 ( 

eh_proj

 , 

enorm

 , 

hnorm

 , 

shared_head_norm

 ); the other 11 land as ordinary 

blk.32.*

 layer tensors ( 

attn_*

 , 

ffn_*

 , the norms) — so grepping for 

nextn

 shows only 4, but the head is complete.

Don't want to graft? You don't have to build the bundled file at all — run the base GGUF with 

--model-draft mtp-ornith-9b-mtp-kl-Q8_0.gguf --spec-type draft-mtp

 . Functionally identical.

Provenance & license

Base:

 

deepreinforce-ai/Ornith-1.0-9B

 (MIT) — a Qwen3.5-9B hybrid (linear-attention + full-attention) fine-tune.

MTP head:

 

protoLabsAI/Ornith-1.0-9B-MTP

 (MIT) — KL-distilled against Ornith's own hidden states.

These GGUFs are a derivative of both; 

MIT

. Built by 

protoLabs.studio

https://protolabs.studio/

.

Downloads last month

9,495

GGUF 

https://huggingface.co/docs/hub/gguf

Model size

2B params

Architecture

qwen35

Chat template

Hardware compatibility

Log In

https://huggingface.co/login?next=https%3A%2F%2Fhuggingface.co%2FprotoLabsAI%2FOrnith-1.0-9B-MTP-GGUF

 to add your hardware

2-bit

MTP IQ2_M

3.87 GB

3-bit

MTP IQ3_M

4.67 GB

4-bit

MTP IQ4_XS

5.45 GB MTP Q4_K_M

5.78 GB

5-bit

MTP Q5_K_M

6.64 GB

6-bit

MTP Q6_K

7.56 GB

8-bit

MTP Q8_0

2.43 GB MTP Q8_0

9.79 GB

16-bit

MTP BF16

18.4 GB

Inference Providers 

NEW

https://huggingface.co/docs/inference-providers

Text Generation

https://huggingface.co/tasks/text-generation

This model isn't deployed by any Inference Provider. 

🙋 Ask for provider support

https://huggingface.co/spaces/huggingface/InferenceSupport/discussions/new?title=protoLabsAI/Ornith-1.0-9B-MTP-GGUF&description=React%20to%20this%20comment%20with%20an%20emoji%20to%20vote%20for%20%5BprotoLabsAI%2FOrnith-1.0-9B-MTP-GGUF%5D(%2FprotoLabsAI%2FOrnith-1.0-9B-MTP-GGUF)%20to%20be%20supported%20by%20Inference%20Providers.%0A%0A(optional)%20Which%20providers%20are%20you%20interested%20in%3F%20(Novita%2C%20Hyperbolic%2C%20Together%E2%80%A6)%0A

Model tree for protoLabsAI/Ornith-1.0-9B-MTP-GGUF 

https://huggingface.co/docs/hub/model-cards#specifying-a-base-model

Base model

deepreinforce-ai/Ornith-1.0-9B

https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B

Quantized

( 

50

https://huggingface.co/models?other=base_model:quantized:deepreinforce-ai/Ornith-1.0-9B

)

this model

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

Built with Multi-Token Prediction (MTP) to speed up inference.

Built with Multi-Token Prediction (MTP) to speed up inference.

Built with Multi-Token Prediction (MTP) to speed up inference.

Built with Multi-Token Prediction (MTP) to speed up inference.

Built with Multi-Token Prediction (MTP) to speed up inference.

Built with Multi-Token Prediction (MTP) to speed up inference.

Built with Multi-Token Prediction (MTP) to speed up inference.

Built with Multi-Token Prediction (MTP) to speed up inference.

Built with Multi-Token Prediction (MTP) to speed up inference.

Inference providers allow you to run inference using different serverless providers.
