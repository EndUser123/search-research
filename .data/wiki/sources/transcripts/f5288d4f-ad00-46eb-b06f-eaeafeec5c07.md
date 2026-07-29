---
source_id: "f5288d4f-ad00-46eb-b06f-eaeafeec5c07"
title: "Qwen 3.6 27B on 24GB VRAM setup: backend comparisons, quant choice and settings (llama.cpp, ik_llama.cpp, BeeLlama, vllm) : r/LocalLLaMA - Reddit"
notebook_id: 831e0613-f723-4d87-aaeb-1d4b5a061496
url: https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/qwen_36_27b_on_24gb_vram_setup_backend/
type: web_page
exported: 2026-07-28
---

# Qwen 3.6 27B on 24GB VRAM setup: backend comparisons, quant choice and settings (llama.cpp, ik_llama.cpp, BeeLlama, vllm) : r/LocalLLaMA - Reddit
Qwen 3.6 27B on 24GB VRAM setup: backend comparisons, quant choice and settings (llama.cpp, ik_llama.cpp, BeeLlama, vllm) : r/LocalLLaMA

Skip to main content

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/qwen_36_27b_on_24gb_vram_setup_backend/#main-content

 Qwen 3.6 27B on 24GB VRAM setup: backend comparisons, quant choice and settings (llama.cpp, ik_llama.cpp, BeeLlama, vllm) : r/LocalLLaMA

Open menu

Open navigation 

https://www.reddit.com/

Go to Reddit Home

Ask

https://www.reddit.com/answers/

Find anything

Sign Up

https://www.reddit.com/register/

Sign up for Reddit

Log In

https://www.reddit.com/login/

Log in to Reddit

Expand user menu

Open settings menu

Skip to Sign up

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/qwen_36_27b_on_24gb_vram_setup_backend/#left-sidebar-container

 

Skip to Right Sidebar

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/qwen_36_27b_on_24gb_vram_setup_backend/#right-sidebar-container

Back

Go to LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

â€¢ 1mo ago

VolandBerlioz

https://www.reddit.com/user/VolandBerlioz/

Locked post

Stickied post

Archived post

Report

Qwen 3.6 27B on 24GB VRAM setup: backend comparisons, quant choice and settings (llama.cpp, ik_llama.cpp, BeeLlama, vllm)

Discussion

https://www.reddit.com/r/LocalLLaMA/?f=flair_name%3A%22Discussion%22

TL;DR

best setup I tested on a RTX 3090 24 GB: 

ik_llama.cpp

 + 

Qwen3.6-27B-MTP-IQ4_KS.gguf

156k

 context, 

q8_0/q8_0

 KV, MTP, vision on CPU

benchmark result on a 

~5.9k

 prompt + 

1k

 output: about 

1261 tok/s

 prefill, 

72.9 tok/s

 decode

llama.cpp

 was a good start, BeeLlama worth testing, but 

ik_llama.cpp

 performed the best

What was tested

upstream 

llama.cpp

 : easy baseline and a good place to start

beellama.cpp

 : promising on paper, but I could not reproduce the expected speed on my setup

ik_llama.cpp

 : best decode/prefill, best VRAM fit

I also spent time with 

vLLM

 / 

club-3090

 , but I am leaving it out of the table because I did not finish a clean apples-to-apples run in this batch. We were seeing about 

78 tok/s

 on responses, but the high-context OOM cliffs were too flaky, so I dropped it until that is fixed. I have not tested it recently, but the repo still flags the single-card long-context issue as unresolved.

The benchmark

One-shot chat-completion task:

prompt size: about 

5.9k

 tokens

output size: 

1024

 tokens

task shape: a code-review / migration note over local setup files

So it mostly tests:

prefill speed on a medium-large real prompt

decode speed on a sustained 

1k

 -token generation

So that is not best-case tok/s, but closer to reality.

The setup I kept

This is the profile I kept as my default:

backend: 

ikawrakow/ik_llama.cpp

https://github.com/ikawrakow/ik_llama.cpp

current tested build: 

4507 (c35189d8)

model: 

ubergarm/Qwen3.6-27B-GGUF

https://huggingface.co/ubergarm/Qwen3.6-27B-GGUF

direct model file: 

Qwen3.6-27B-MTP-IQ4_KS.gguf

https://huggingface.co/ubergarm/Qwen3.6-27B-GGUF/blob/main/Qwen3.6-27B-MTP-IQ4_KS.gguf

High-level launch shape:

--ctx-size 156000

--cache-type-k q8_0

--cache-type-v q8_0

--flash-attn on

--multi-token-prediction

--draft-max 4

--draft-p-min 0.0

--merge-qkv

--merge-up-gate-experts

--cache-ram 32768

--ctx-checkpoints 32

--reasoning on

--reasoning-format deepseek

--chat-template-kwargs '{"preserve_thinking":true}'

--no-mmproj-offload

Notes:

built-in MTP in 

ik_llama.cpp

 worked better for me than the other speculative paths

q8_0

 KV was good quality; you can opt into 

q4

 , but there is plenty of VRAM headroom with 

IQ4_KS

Why IQ4_KS

much smaller than Unsloth 

UD-Q4_K_XL

quality stayed high enough that I did not feel a real penalty

on a 

24 GB

 card, those saved GiB matter once you start pushing context and sane u-batch sizes

to be fair, there is probably room for a higher quant, maybe 

q5

 ; I have not tested that yet

Qwen-3.6 quants discussion #1663

https://github.com/ikawrakow/ik_llama.cpp/discussions/1663

TLDR:

Qwen 3.6

 quantizes very well in 

IQ4_KS

ikawrakow

 measured 

IQ4_KS

 as very close to, or better than, 

UD_Q4_XL

Unsloth 

UD-Q4_K_XL

 needs about 

2.8 GiB

 more to land in the same neighborhood

If you want the background on the quant family itself:

New quantization types IQ2_K, IQ3_K, IQ4_K, IQ5_K discussion #8

https://github.com/ikawrakow/ik_llama.cpp/discussions/8

Vision

projector on CPU by default: 

--mmproj ...

 + 

--no-mmproj-offload

move it to GPU if you want faster image processing and are willing to spend roughly 

1.5 GiB

 more VRAM

if that OOMs, lower context or switch to 

q4

 KV

GPU Stuff

This was on Linux with the desktop on the iGPU and the RTX 3090 used only for LLMs.

power limit: 

330 W

memory OC: 

+600

undervolt: flattened at about 

1875 MHz @ 868 mV

 ( 

LACT

 now has a curve editor)

Some experiments did not make the default setup better

--spec-autotune

 on 

ik_llama.cpp

 : no meaningful gain on this workload

--mtp-requantize-output-tensor q6_K

 : sometimes faster, but inconsistent and costs about 

1 GiB

 extra VRAM, so I did not keep it

BeeLlama DFlash precision quickstart: loaded fine, but was much slower here than expected

upstream 

llama.cpp

 MTP paths: good baseline, but slower than 

ik_llama.cpp

 in my tests

BeeLlama and 

vLLM

 are still worth exploring. I just did not land on a setup there that beat the 

ik_llama.cpp

 profile for my workload.

Results

These are the useful comparison points from the same real prompt / 

1024

 -token output benchmark.

Backend

Model / quant

Spec path

Context

KV cache

Prefill tok/s

Decode tok/s

Wall time

Notes

ik_llama.cpp

Qwen3.6-27B-MTP-IQ4_KS

built-in MTP

156k

q8_0/q8_0

1260.95

72.93

18.79s

best overall default profile

llama.cpp

 upstream

Qwen3.6-27B-UD-Q4_K_XL

draft-mtp

32k

q4_0/q4_0

1247.65

51.20

24.80s

easiest starting point

llama.cpp

 upstream tuned

Qwen3.6-27B-UD-Q4_K_XL

draft-mtp

32k

q8_0/q8_0

1242.81

56.66

22.88s

old-like flags helped, still slower

beellama.cpp

Q5_K_S

 + DFlash 

Q4_K_M

DFlash

122.8k

turbo4/turbo3_tcq

1117.66

36.32

33.55s

text-only quickstart-style run

Flags tested:

--spec-autotune

 did not produce better results on this workload

--mtp-requantize-output-tensor q6_K

 had occasional upside, about 

+5 tok/s

 decode in the best run, but it was not stable enough to justify the extra 

~1 GiB

 VRAM

Flag comparison

These are the high-level config differences that mattered most.

Backend

Quant(s)

Draft / spec mode

Key draft params

KV cache

Other notable flags

ik_llama.cpp

target 

IQ4_KS

 MTP

built-in 

--multi-token-prediction

--draft-max 4

 , 

--draft-p-min 0.0

q8_0/q8_0

--merge-qkv

 , 

--merge-up-gate-experts

 , 

--ctx-checkpoints 32

 , CPU 

mmproj

llama.cpp

 upstream

target 

UD-Q4_K_XL

draft-mtp

--spec-draft-n-max 6

 , 

--spec-draft-p-min 0.75

q4_0/q4_0

 default, 

q8_0/q8_0

 tuned

--flash-attn on

 , 

--jinja

beellama.cpp

target 

Q5_K_S

 , draft 

Q4_K_M

dflash

--spec-dflash-cross-ctx 1024

turbo4/turbo3_tcq

--kv-unified

 , 

-b 2048

 , 

-ub 256

 , text-only in my run

Links

ik_llama.cpp

 : 

https://github.com/ikawrakow/ik_llama.cpp

https://github.com/ikawrakow/ik_llama.cpp

ExLlamaV3

 : 

https://github.com/turboderp-org/exllamav3

https://github.com/turboderp-org/exllamav3

BeeLlama: 

https://github.com/Anbeeld/beellama.cpp

https://github.com/Anbeeld/beellama.cpp

BeeLlama Qwen 3.6 quickstart: 

https://github.com/Anbeeld/beellama.cpp/blob/main/docs/quickstart-qwen36-dflash.md

https://github.com/Anbeeld/beellama.cpp/blob/main/docs/quickstart-qwen36-dflash.md

club-3090

 : 

https://github.com/noonghunna/club-3090

https://github.com/noonghunna/club-3090

IQ4_KS

 with MTP: 

https://huggingface.co/ubergarm/Qwen3.6-27B-GGUF/blob/main/Qwen3.6-27B-MTP-IQ4_KS.gguf

https://huggingface.co/ubergarm/Qwen3.6-27B-GGUF/blob/main/Qwen3.6-27B-MTP-IQ4_KS.gguf

Qwen-3.6 quants

 discussion: 

https://github.com/ikawrakow/ik_llama.cpp/discussions/1663

https://github.com/ikawrakow/ik_llama.cpp/discussions/1663

IQ4_KS

 quant family discussion: 

https://github.com/ikawrakow/ik_llama.cpp/discussions/8

https://github.com/ikawrakow/ik_llama.cpp/discussions/8

This is the best 

24 GB

 setup I found so far, but things are moving fast and I do not think this is settled yet.

The point of this thread is to compare real single-3090 / 

24 GB

 results: backend choice, quants, flags, and what stays stable under actual use.

I would like this to become a useful reference thread for 

24 GB

 cards: what works, what breaks, and what is actually worth running day to day. I have not tested 

ExLlamaV3

 yet, and there may be other setups that are better.

Also, thanks to everyone building this stuff: backend authors, quant makers, template tinkerers, and the people doing the boring debugging work that makes local LLMs usable.

Upvote 221 Downvote 136 Go to comments

 

 

1

Share

Sort by: Best

Open comment sort options

Best

Top

New

Controversial

Old

Q&A

Search Comments Expand comment search

Cancel

Comments Section

Anbeeld

https://www.reddit.com/user/Anbeeld/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgmpry/

 

Top 1% Commenter

Thank you for giving 

BeeLlama

https://www.reddit.com/search/?q=BeeLlama+LLM+backend&cId=e15cf922-494f-4244-882f-6f106d5b7be6&iId=90b02406-3a8e-48fa-81ab-e11d22b1aa06

 a try. It's a very young fork, so stay tuned for more improvements, with a new version scheduled this week.

That said, the methodology is not correct for comparing performance between inference tools. This should be done with equal target models at the very least, but also equal KV cache type and size. Otherwise you add difference in performance of IQ4_XS, UD_Q4 and Q5, which is pretty significant, and then TurboQuant cache is just slower than Q8/Q4 as a matter of fact, in exchange for less VRAM. Also the size of context matters too, as well as -b and -ub for prefill.

Upvote 34 Downvote Reply Award

Share

Report

Award

Share 

VolandBerlioz

https://www.reddit.com/user/VolandBerlioz/

OP â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhblxz/

Thanks for the response, and that is a fair criticism.

The post was more "which recipe worked best from what i tested" than a strict backend-isolation benchmark. For all of the inference tools I mostly followed the recommended settings / guides, and some quants are only supported by one fork or another, so the tested recipes were not fully identical.

I reran some tests after your comment to control the things you pointed out more directly.

Same workload for all reruns (u and ub as in the quickstart in the repo):

one-shot chat completion

prompt: about 

7.2k

 tokens

output: 

1024

 tokens

same 

-b 2048

same 

-ub 256

text-only

Results:

Q5_K_S

 + DFlash 

Q4_K_M

 draft, 

turbo4 / turbo3_tcq

, 

122.8k

 max ctx

prefill: 

1119.95 tok/s

decode: 

36.40 tok/s

same target/draft, but 

q8_0 / q8_0

 KV, same 

122.8k

 max ctx

prefill: 

1143.72 tok/s

decode: 

41.24 tok/s

same target/draft, 

q8_0 / q8_0

, but 

80k

 max ctx (as it ooms if i try to load 122k)

prefill: 

1141.90 tok/s

decode: 

39.00 tok/s

Q4_K_M

 + DFlash 

Q4_K_M

 draft, 

q8_0 / q8_0

, 

80k

 max ctx

prefill: 

1089.33 tok/s

decode: 

41.17 tok/s

So yes, KV point was correct - moving from TurboQuant KV to 

q8_0 / q8_0

 gave a small speed bump.

The context numbers in the post were max configured context, not used context. The actual benchmark prompt was nowhere near 

120k

. For 

~6-7k

 prompt + 

1k

 output test, lowering max ctx from 

122.8k

 to 

80k

 did not change prefill or decode speed.

Thanks for your work!

If something is off or im not running things correctly let me know, im happy to rerun some tests.

Upvote 6 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhblxz/?force-legacy-sct=1

8 more replies

8 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgmpry/?force-legacy-sct=1

 

VoidAlchemy

https://www.reddit.com/user/VoidAlchemy/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omi6vsa/

Heya, glad you figured it out! I'm ubergarm and yes this is pretty much accurate and my daily driver setup for running pi harness on my 3090 TI 24GB VRAM at home.

I added a PR to ik to specify number of CPU threads to use when doing MTP also if you want to control everything explicitly. Full command there too: 

https://github.com/ikawrakow/ik_llama.cpp/pull/1797#issuecomment-4442151972

https://github.com/ikawrakow/ik_llama.cpp/pull/1797#issuecomment-4442151972

Both this iq4_ks and iq5_ks are the best quality in the given memory footprint according to oobabooba's KLD testing: 

https://localbench.substack.com/p/qwen-3-6-27b-gguf-quality-benchmark

https://localbench.substack.com/p/qwen-3-6-27b-gguf-quality-benchmark

 (he was super nice and posted one graph on huggingface discussion too)

I didn't add MTP tensor to the iq5_ks, but you could probably extract the 

q8_0

 MTP tensor in the iq4_ks and use it if you have 32GB VRAM etc.

Also if you have 2x GPUs you can use 

-sm graph

 for "tensor parallel" similar to mainline's 

-sm tensor

.

Enjoy, this quant is a beast at vibe coding, I added an API endpoint to unload/load the model and it can run on the same GPU as ComfyUI with a custom SKILL so I can just use plain language to have it manage the LoRAs, trigger words, and prompt generation. Pretty slick!

Upvote 20 Downvote Reply Award

Share

Report

Award

Share 

VolandBerlioz

https://www.reddit.com/user/VolandBerlioz/

OP â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omjqelt/

Yeah i've been following you here and there! Thanks for your work!

Upvote 3 Downvote Reply Award

Share

Report

Award

Share

7 more replies

7 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omi6vsa/?force-legacy-sct=1

EatTFM

https://www.reddit.com/user/EatTFM/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgvfgy/

Please repeat benchmarks with at least fixed ctx sizes. Speed goes down considerably when using more context.

Upvote 3 Downvote Reply Award

Share

Report

Award

Share

2 more replies

2 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgvfgy/?force-legacy-sct=1

CompetitionTop7822

https://www.reddit.com/user/CompetitionTop7822/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgtyll/

Itâ€™s getting to be too much for a normal user to run models. I can understand why many use Ollama or cloud models or similar tools when you need to spend more time setting up llama.cpp than actually using it.

I bet lots of users here spend more time downloading models and tweaking settings than using them for some real use case.

Upvote 8 Downvote Reply Award

Share

Report

Award

Share 

VolandBerlioz

https://www.reddit.com/user/VolandBerlioz/

OP â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omh7zuu/

It's part of the hobby...

A few codex/cc prompts, and u can easily get a basic setup up and running. There is plenty of information around.

Upvote 14 Downvote Reply Award

Share

Report

Award

Share

4 more replies

4 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgtyll/?force-legacy-sct=1

 

klasyer

https://www.reddit.com/user/klasyer/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgqusl/

Was the 3090 headless? Didn't under from the description

I'm trying to run qwen with my 3090 for my personal coding projects but I often ran out of vram

Are you going to test the 35b model as well?

Upvote 2 Downvote Reply Award

Share

Report

Award

Share 

VolandBerlioz

https://www.reddit.com/user/VolandBerlioz/

OP â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omh78ti/

Yeah headless. Should be able to run it as there is still ~1.7gb left after the model is loaded fully. If you still oom, then drop context to 128k or q4kv.

Upvote 4 Downvote Reply Award

Share

Report

Award

Share

2 more replies

2 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omh78ti/?force-legacy-sct=1

Borkato

https://www.reddit.com/user/Borkato/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhok0z/

 

Top 1% Commenter

What does headless mean? No monitor/graphics output?

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

4 more replies

4 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhok0z/?force-legacy-sct=1

1 more reply

1 more reply

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgqusl/?force-legacy-sct=1

 

JGeek00

https://www.reddit.com/user/JGeek00/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgqz36/

 â€¢ Edited 1mo ago

How much RAM do you have? I have a 3090. Iâ€™m using tue standard llama.cpp, Q4_K_M and q8 kv cache quant with MTP and Iâ€™m getting 55 t/s on decoding and 800 t/s on prefill

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

4 more replies

4 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgqz36/?force-legacy-sct=1

 

FerLuisxd

https://www.reddit.com/user/FerLuisxd/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omp6yq7/

 â€¢ Edited 1mo ago

Oh boy you should also try: -exllamaV3 -NVFP4 -MTP + APEX With Rotorquant

Upvote 2 Downvote Reply Award

Share

Report

Award

Share 

VolandBerlioz

https://www.reddit.com/user/VolandBerlioz/

OP â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/ompglvj/

That's possibly the one thing i haven't tried. How do you find it?

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/ompglvj/?force-legacy-sct=1

More replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omp6yq7/?force-legacy-sct=1

soyalemujica

https://www.reddit.com/user/soyalemujica/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omh93ah/

 

Top 1% Commenter

Well, tried to give this ik llama a try, same model, arguments and all, and with my 24gb vram AMD GPU I am unable to even load the model, continues to stay at:

"too large to fit in a Vulkan0 buffer (tensor size: 1350860800, max buffer size: 1073741824)"

so I believe ik llama is not that good for AMD

Upvote 3 Downvote Reply Award

Share

Report

Award

Share

6 more replies

6 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omh93ah/?force-legacy-sct=1

 

Pentium95

https://www.reddit.com/user/Pentium95/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgznky/

different context lenghts (this makes A LOT of difference)

different model size 5BPW model is obviously SLOWER then a 4.25 BPW model

Why

Upvote 19 Downvote Reply Award

Share

Report

Award

Share

cibernox

https://www.reddit.com/user/cibernox/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgwafx/

 

Top 1% Commenter

This is EXACTLY the post I needed ðŸ'

I wanted to run 

qwen 27B

https://www.reddit.com/search/?q=qwen+27B+LLM&cId=6b40f1e7-7c39-4e1a-89c4-16800fea2e70&iId=18926c21-885a-4d29-96c9-f857460fabfa

 but I also need 150k context at least, and using the UD version and vision I couldn't fit that much context. I didn't even know you could 

offload the vision

https://www.reddit.com/search/?q=offload+vision+LLM&cId=d70c4b27-a312-474a-98c5-7c8190d03cf5&iId=a2e728cf-14fe-4b03-a14f-e99375623ccc

 only to CPU, and I think that's genius. I do need vision, but I need it rarely enough that having it be slow because it runs on CPU is an acceptable trade-off, specially now that I upgraded my CPU.

I'll be running this on vulkan on a 7900XTX but I will try if a similar setup works

Upvote 16 Downvote Reply Award

Share

Report

Award

Share

12 more replies

12 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgwafx/?force-legacy-sct=1

Formal-Exam-8767

https://www.reddit.com/user/Formal-Exam-8767/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgoldo/

Am I missing something here, is " 

IQ4_KS

https://www.reddit.com/search/?q=IQ4_KS+quantization+llama.cpp&cId=a387bd1f-5d8c-425b-beb8-4d4a6de3568b&iId=45b0a109-c94a-4375-8053-fbb08aa6c11b

 " not supported on stock 

llama.cpp

https://www.reddit.com/search/?q=llama.cpp&cId=561f5241-f69a-4244-94fa-b786d513ffc0&iId=23ee9d94-e81d-494a-a227-a0ef8c510430

 ?

Upvote 8 Downvote Reply Award

Share

Report

Award

Share

3 more replies

3 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgoldo/?force-legacy-sct=1

meca23

https://www.reddit.com/user/meca23/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgt4zn/

I love this community. So much work/testing being done and openly shared. Thank you

Upvote 5 Downvote Reply Award

Share

Report

Award

Share 

NickCanCode

https://www.reddit.com/user/NickCanCode/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgr334/

 

--mtp-requantized-output-tensor take quite sometime to load but it give stable 6%~8% speed up. The alternative is to patch the model which really I don't want to do. I don't want my model to be polluted by something that can be auto generated. No elegant at all. I would rather wait longer for it to be prepared each time.

Upvote 1 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgr334/?force-legacy-sct=1

Pablo_the_brave

https://www.reddit.com/user/Pablo_the_brave/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhosx3/

Is this working for you with an agent and if yes with which one? I have found a bug in openai api implementation of ik_llama.cpp and without the patch it's not working for me.

Upvote 1 Downvote Reply Award

Share

Report

Award

Share 

VolandBerlioz

https://www.reddit.com/user/VolandBerlioz/

OP â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhqmt7/

Every agent i've tested so far. Hermes with no issues, opencode, pi...

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

More replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhosx3/?force-legacy-sct=1

HennyKo

https://www.reddit.com/user/HennyKo/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhvcdh/

Can you do undervolt and memory OC on a headless linux?

Upvote 1 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhvcdh/?force-legacy-sct=1

 

Then-Topic8766

https://www.reddit.com/user/Then-Topic8766/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omi930x/

You can try something like this: 

https://www.reddit.com/r/LocalLLaMA/comments/1tg6j9u/comment/omgh6nl/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button

https://www.reddit.com/r/LocalLLaMA/comments/1tg6j9u/comment/omgh6nl/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button

 for even more speed-up.

Upvote 1 Downvote Reply Award

Share

Report

Award

Share 

VolandBerlioz

https://www.reddit.com/user/VolandBerlioz/

OP â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omjvmni/

For ik_llama at least it does not improve. Decode drops 16%. Ngram does not engage much:

ngram_mod: 31 generated, 8 accepted

mtp: 712 generated, 594 accepted

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

More replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omi930x/?force-legacy-sct=1

TheWolfOfWalmart

https://www.reddit.com/user/_TheWolfOfWalmart_/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omizdhk/

 â€¢ Edited 1mo ago

Thanks for sharing, but I'd love to see some benchmarks focused on getting the best intelligence on 24 GB while still retaining a good enough context size. I prefer quality over speed, and really any configuration of this model is going to be fast enough when fitting fully in VRAM.

Upvote 1 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omizdhk/?force-legacy-sct=1

 

DeepBlue96

https://www.reddit.com/user/DeepBlue96/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgmriu/

in my testing the ud-q5_k_xl was like night and day quality wise and fits in 24gb wi 120k context 800-1000pp tks and 25-30tks:

\llama-server.exe -hf unsloth/Qwen3.6-27B-GGUF:UD-Q5_K_XL --cache-type-k q4_0 --cache-type-v q4_0 --reasoning off --cache-ram 4096 --cache-reuse 1024 --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.00 --webui-mcp-proxy --spec-type ngram-mod

Upvote 3 Downvote Reply Award

Share

Report

Award

Share 

Gold_Coconut9777

https://www.reddit.com/user/Gold_Coconut9777/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgnktm/

Could you elaborate on why you choose to go with reasoning off?

Upvote 6 Downvote Reply Award

Share

Report

Award

Share

7 more replies

7 more replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgnktm/?force-legacy-sct=1

TheWolfOfWalmart

https://www.reddit.com/user/_TheWolfOfWalmart_/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omj04vb/

--cache-type-k q4_0 --cache-type-v q4_0

oof...

Upvote 5 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omj04vb/?force-legacy-sct=1

More replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omgmriu/?force-legacy-sct=1

GoodTip7897

https://www.reddit.com/user/GoodTip7897/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhkxm6/

I use UD_Q5_K_XL and 70k context at bf16.Â

No MTP and no vision. But I believe that is the highest possible quality you can get for agentic coding on a 24gb GPU.Â

I get about 30 t/sec decode and 1000-500 t/sec prefill

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhkxm6/?force-legacy-sct=1

 

[deleted]

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhgopm/

Comment removed by moderator 

VolandBerlioz

https://www.reddit.com/user/VolandBerlioz/

OP â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhqypp/

Honestly, no, but haven't really tested it properly, so take it with a grain of salt. 

VoidAlchemy

https://www.reddit.com/user/VoidAlchemy/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omi5j8u/

if you want to go below q8_0 on ik, I suggest no lower than 

-khad -ctk q6_0 -vhad -ctv q4_0

 which is going to probably still be better quality than the goofy turboquant forks and rather efficient.

More replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omhgopm/?force-legacy-sct=1

 

[deleted]

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omh2o5h/

Comment removed by moderator

LikeSaw

https://www.reddit.com/user/LikeSaw/

â€¢ 

1mo ago

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omqe5i5/

AI hallucinated cli args are polluting everywhere and sadly most people don't care or question them

More replies

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/comment/omh2o5h/?force-legacy-sct=1

View more comments

People also ask about section

People also ask about

Optimal settings for Qwen 3.6 with llama.cpp

https://www.reddit.com/answers/d543a998-38b3-4e96-b8c4-0d2ab1953cdf/?q=Optimal+settings+for+Qwen+3.6+with+llama.cpp&source=PDP

Qwen 3.6 27B hardware requirements

https://www.reddit.com/answers/9bdd1578-818c-4d12-abac-ab44c737b53d/?q=Qwen+3.6+27B+hardware+requirements&source=PDP

Best practices for hosting LLaMA locally

https://www.reddit.com/answers/62ed0244-f56d-4b2d-a3fc-0714a810bf63/?q=Best+practices+for+hosting+LLaMA+locally&source=PDP

Top tools for optimizing AI model performance

https://www.reddit.com/answers/378b70e3-3e25-4969-a572-fbc37eaddcda/?q=Top+tools+for+optimizing+AI+model+performance&source=PDP

Unique applications of LLaMA in everyday life

https://www.reddit.com/answers/5c061272-762d-4637-8f80-cc69ce28fe36/?q=Unique+applications+of+LLaMA+in+everyday+life&source=PDP

More posts you may like

Related posts

Qwen3.6-35B-A3B Q5_K_M on 12GB VRAM â€” working llama.cpp config

https://www.reddit.com/r/LocalLLM/comments/1ta4r5m/qwen3635ba3b_q5_k_m_on_12gb_vram_working_llamacpp/

 

r/LocalLLM

https://www.reddit.com/r/LocalLLM/

 â€¢ 2mo ago [

Qwen3.6-35B-A3B Q5_K_M on 12GB VRAM â€” working llama.cpp config

](https://www.reddit.com/r/LocalLLM/comments/1ta4r5m/qwen3635ba3b_q5_k_m_on_12gb_vram_working_llamacpp/) 50 upvotes Â· 20 comments

PfSense + Omada Setup / MGMT VLAN

https://www.reddit.com/r/PFSENSE/comments/1se0hqn/pfsense_omada_setup_mgmt_vlan/

 

r/PFSENSE

https://www.reddit.com/r/PFSENSE/

 â€¢ 3mo ago [

PfSense + Omada Setup / MGMT VLAN

](https://www.reddit.com/r/PFSENSE/comments/1se0hqn/pfsense_omada_setup_mgmt_vlan/) 5 upvotes Â· 8 comments

Is Qwen 3.6 27B the best model under 40B once quantized? (32GB VRAM)

https://www.reddit.com/r/LocalLLM/comments/1t1pcak/is_qwen_36_27b_the_best_model_under_40b_once/

 

r/LocalLLM

https://www.reddit.com/r/LocalLLM/

 â€¢ 2mo ago [

Is Qwen 3.6 27B the best model under 40B once quantized? (32GB VRAM)

](https://www.reddit.com/r/LocalLLM/comments/1t1pcak/is_qwen_36_27b_the_best_model_under_40b_once/) 

 8 upvotes Â· 11 comments

[Help] Severe Latency during Prompt Ingestion - OpenClaw/Ollama on AMD Minisforum (AVX-512) & 64GB RAM (No GPU)

https://www.reddit.com/r/LocalLLM/comments/1rml3s9/help_severe_latency_during_prompt_ingestion/

 

r/LocalLLM

https://www.reddit.com/r/LocalLLM/

 â€¢ 4mo ago [

[Help] Severe Latency during Prompt Ingestion - OpenClaw/Ollama on AMD Minisforum (AVX-512) & 64GB RAM (No GPU)

](https://www.reddit.com/r/LocalLLM/comments/1rml3s9/help_severe_latency_during_prompt_ingestion/) 1 comment

Nvidia driver problems - Unable to load image nvlddmkm.sys

https://www.reddit.com/r/PcBuildHelp/comments/1rfvw6p/nvidia_driver_problems_unable_to_load_image/

 

r/PcBuildHelp

https://www.reddit.com/r/PcBuildHelp/

 â€¢ 4mo ago [

Nvidia driver problems - Unable to load image nvlddmkm.sys

](https://www.reddit.com/r/PcBuildHelp/comments/1rfvw6p/nvidia_driver_problems_unable_to_load_image/) 2 upvotes

[Support] Silent Hill f - Unreal GPU Crash (UE-SHf GPU Crash Dump Triggered) - FitGirl Repack

https://www.reddit.com/r/FitGirlRepack/comments/1sc16j2/support_silent_hill_f_unreal_gpu_crash_ueshf_gpu/

 

r/FitGirlRepack

https://www.reddit.com/r/FitGirlRepack/

 â€¢ 3mo ago [

[Support] Silent Hill f - Unreal GPU Crash (UE-SHf GPU Crash Dump Triggered) - FitGirl Repack

](https://www.reddit.com/r/FitGirlRepack/comments/1sc16j2/support_silent_hill_f_unreal_gpu_crash_ueshf_gpu/) 1 upvote

Title: BEX64 engine.dll crash on all servers - i9-14900KF + RTX 4070 Super + Windows 11

https://www.reddit.com/r/gmod/comments/1rnmloc/title_bex64_enginedll_crash_on_all_servers/

 

r/gmod

https://www.reddit.com/r/gmod/

 â€¢ 4mo ago [

Title: BEX64 engine.dll crash on all servers - i9-14900KF + RTX 4070 Super + Windows 11

](https://www.reddit.com/r/gmod/comments/1rnmloc/title_bex64_enginedll_crash_on_all_servers/) 1 upvote Â· 3 comments

Help! ASUS ROG Rapture GT-BE98 Pro dropping iPhone/PS5 - Kernel WLC_SCB_DEAUTHORIZE error (-30)

https://www.reddit.com/r/HomeNetworking/comments/1rfspn8/help_asus_rog_rapture_gtbe98_pro_dropping/

 

r/HomeNetworking

https://www.reddit.com/r/HomeNetworking/

 â€¢ 4mo ago [

Help! ASUS ROG Rapture GT-BE98 Pro dropping iPhone/PS5 - Kernel WLC_SCB_DEAUTHORIZE error (-30)

](https://www.reddit.com/r/HomeNetworking/comments/1rfspn8/help_asus_rog_rapture_gtbe98_pro_dropping/) 1 upvote Â· 8 comments

Qwen3.6 27B more dumb in vLLM compared to llama.cpp

https://www.reddit.com/r/LocalLLaMA/comments/1ue9v4b/qwen36_27b_more_dumb_in_vllm_compared_to_llamacpp/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 7d ago [

Qwen3.6 27B more dumb in vLLM compared to llama.cpp

](https://www.reddit.com/r/LocalLLaMA/comments/1ue9v4b/qwen36_27b_more_dumb_in_vllm_compared_to_llamacpp/) 78 upvotes Â· 107 comments

80 tok/sec and 128K context on 12GB VRAM with Qwen3.6 35B A3B and llama.cpp MTP

https://www.reddit.com/r/LocalLLaMA/comments/1t82zxv/80_toksec_and_128k_context_on_12gb_vram_with/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 2mo ago [

80 tok/sec and 128K context on 12GB VRAM with Qwen3.6 35B A3B and llama.cpp MTP

](https://www.reddit.com/r/LocalLLaMA/comments/1t82zxv/80_toksec_and_128k_context_on_12gb_vram_with/) 674 upvotes Â· 170 comments

Qwen-27B-IQ4_KS for ik_llama.cpp, especially for NVIDIA with 16GB VRAM

https://www.reddit.com/r/LocalLLaMA/comments/1tkmgwj/qwen27biq4_ks_for_ik_llamacpp_especially_for/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 1mo ago [

Qwen-27B-IQ4_KS for ik_llama.cpp, especially for NVIDIA with 16GB VRAM

](https://www.reddit.com/r/LocalLLaMA/comments/1tkmgwj/qwen27biq4_ks_for_ik_llamacpp_especially_for/) 84 upvotes Â· 59 comments

Qwen3.5 Support Merged in llama.cpp

https://www.reddit.com/r/LocalLLaMA/comments/1qzppr7/qwen35_support_merged_in_llamacpp/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 5mo ago [

Qwen3.5 Support Merged in llama.cpp

](https://www.reddit.com/r/LocalLLaMA/comments/1qzppr7/qwen35_support_merged_in_llamacpp/) 

 github 237 upvotes Â· 14 comments

Qwen3.6 35B-A3B is quite useful on 780m iGPU (llama.cpp,vulkan)

https://www.reddit.com/r/LocalLLaMA/comments/1su9yva/qwen36_35ba3b_is_quite_useful_on_780m_igpu/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 2mo ago [

Qwen3.6 35B-A3B is quite useful on 780m iGPU (llama.cpp,vulkan)

](https://www.reddit.com/r/LocalLLaMA/comments/1su9yva/qwen36_35ba3b_is_quite_useful_on_780m_igpu/) 77 upvotes Â· 50 comments

UPDATE: Qwen-27B-IQ4_KS and Qwen-27B-IQ_KS_KT for ik_llama.cpp, especially for NVIDIA with 16GB VRAM

https://www.reddit.com/r/LocalLLaMA/comments/1udomsd/update_qwen27biq4_ks_and_qwen27biq_ks_kt_for_ik/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 8d ago [

UPDATE: Qwen-27B-IQ4_KS and Qwen-27B-IQ_KS_KT for ik_llama.cpp, especially for NVIDIA with 16GB VRAM

](https://www.reddit.com/r/LocalLLaMA/comments/1udomsd/update_qwen27biq4_ks_and_qwen27biq_ks_kt_for_ik/) 30 upvotes Â· 29 comments

ik_llama: Qwen3.6 27B and 35B on very low VRAM

https://www.reddit.com/r/LocalLLaMA/comments/1tg0xyw/ik_llama_qwen36_27b_and_35b_on_very_low_vram/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 1mo ago [

ik_llama: Qwen3.6 27B and 35B on very low VRAM

](https://www.reddit.com/r/LocalLLaMA/comments/1tg0xyw/ik_llama_qwen36_27b_and_35b_on_very_low_vram/) 7 upvotes Â· 22 comments

Qwen 3.6 27B llama.cpp | Multi-GPU pp t/s help

https://www.reddit.com/r/LocalLLaMA/comments/1sur7a9/qwen_36_27b_llamacpp_multigpu_pp_ts_help/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 2mo ago [

Qwen 3.6 27B llama.cpp | Multi-GPU pp t/s help

](https://www.reddit.com/r/LocalLLaMA/comments/1sur7a9/qwen_36_27b_llamacpp_multigpu_pp_ts_help/) 11 upvotes Â· 27 comments

Qwen3.6 27B Pure Quant: 40 tok/s on 16 GB VRAM

https://www.reddit.com/r/LocalLLaMA/comments/1tkzk9e/qwen36_27b_pure_quant_40_toks_on_16_gb_vram/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 1mo ago [

Qwen3.6 27B Pure Quant: 40 tok/s on 16 GB VRAM

](https://www.reddit.com/r/LocalLLaMA/comments/1tkzk9e/qwen36_27b_pure_quant_40_toks_on_16_gb_vram/) 

 130 upvotes Â· 91 comments

Running the new Qwen3.6-35B-A3B at full context on both a 4090 and GB10 Spark with vLLM and Llama.cpp

https://www.reddit.com/r/LocalLLaMA/comments/1snaa5w/running_the_new_qwen3635ba3b_at_full_context_on/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 3mo ago [

Running the new Qwen3.6-35B-A3B at full context on both a 4090 and GB10 Spark with vLLM and Llama.cpp

](https://www.reddit.com/r/LocalLLaMA/comments/1snaa5w/running_the_new_qwen3635ba3b_at_full_context_on/) 

 2 49 upvotes Â· 36 comments

BeeLlama v0.3.1 â€“ latest llama.cpp with extras! DFlash, MTP, q6_0 cache, TurboQuant. Single RTX 3090: Qwen 3.6 27B & Gemma 4 31B up to 177.8 tps (4.93x over baseline)

https://www.reddit.com/r/LocalLLaMA/comments/1tx12t1/beellama_v031_latest_llamacpp_with_extras_dflash/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 27d ago [

BeeLlama v0.3.1 â€“ latest llama.cpp with extras! DFlash, MTP, q6_0 cache, TurboQuant. Single RTX 3090: Qwen 3.6 27B & Gemma 4 31B up to 177.8 tps (4.93x over baseline)

](https://www.reddit.com/r/LocalLLaMA/comments/1tx12t1/beellama_v031_latest_llamacpp_with_extras_dflash/) 52 upvotes Â· 54 comments

Does running a model (like qwen3.6-27b) on vllm or transformers use less VRAM than llama.cpp?

https://www.reddit.com/r/LocalLLaMA/comments/1t2wtvb/does_running_a_model_like_qwen3627b_on_vllm_or/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 2mo ago [

Does running a model (like qwen3.6-27b) on vllm or transformers use less VRAM than llama.cpp?

](https://www.reddit.com/r/LocalLLaMA/comments/1t2wtvb/does_running_a_model_like_qwen3627b_on_vllm_or/) 4 upvotes Â· 21 comments

Hot Experts in your VRAM! Dynamic expert cache in llama.cpp for 27% faster CPU +GPU token generation with Qwen3.5-122B-A10B compared to layer-based single-GPU partial offload

https://www.reddit.com/r/LocalLLaMA/comments/1slue0z/hot_experts_in_your_vram_dynamic_expert_cache_in/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 3mo ago [

Hot Experts in your VRAM! Dynamic expert cache in llama.cpp for 27% faster CPU +GPU token generation with Qwen3.5-122B-A10B compared to layer-based single-GPU partial offload

](https://www.reddit.com/r/LocalLLaMA/comments/1slue0z/hot_experts_in_your_vram_dynamic_expert_cache_in/) 104 upvotes Â· 23 comments

Qwen3.5 on VLLM

https://www.reddit.com/r/LocalLLaMA/comments/1re9xbi/qwen35_on_vllm/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 4mo ago [

Qwen3.5 on VLLM

](https://www.reddit.com/r/LocalLLaMA/comments/1re9xbi/qwen35_on_vllm/) 14 upvotes Â· 36 comments

2x MI50 32GB Quant Speed Comparison version 2 (Qwen 3.5 35B, llama.cpp, Vulkan/ROCm)

https://www.reddit.com/r/LocalLLaMA/comments/1rmt315/2x_mi50_32gb_quant_speed_comparison_version_2/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 4mo ago [

2x MI50 32GB Quant Speed Comparison version 2 (Qwen 3.5 35B, llama.cpp, Vulkan/ROCm)

](https://www.reddit.com/r/LocalLLaMA/comments/1rmt315/2x_mi50_32gb_quant_speed_comparison_version_2/) 

 22 upvotes Â· 6 comments

Qwen 3.5 35b on 8GB Vram for local agentic workflow

https://www.reddit.com/r/LocalLLaMA/comments/1s0jt8v/qwen_35_35b_on_8gb_vram_for_local_agentic_workflow/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 3mo ago [

Qwen 3.5 35b on 8GB Vram for local agentic workflow

](https://www.reddit.com/r/LocalLLaMA/comments/1s0jt8v/qwen_35_35b_on_8gb_vram_for_local_agentic_workflow/) 65 upvotes Â· 72 comments

vLLM vs llama.cpp: Huge Context Efficiency Differences on Qwen3.5-4B AWQ

https://www.reddit.com/r/LocalLLaMA/comments/1sfnjoh/vllm_vs_llamacpp_huge_context_efficiency/

 

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 â€¢ 3mo ago [

vLLM vs llama.cpp: Huge Context Efficiency Differences on Qwen3.5-4B AWQ

](https://www.reddit.com/r/LocalLLaMA/comments/1sfnjoh/vllm_vs_llamacpp_huge_context_efficiency/) 3 upvotes Â· 12 comments

View Post in

FranÃ§ais

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/qwen_36_27b_on_24gb_vram_setup_backend/?tl=fr

PortuguÃªs (Brasil)

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/qwen_36_27b_on_24gb_vram_setup_backend/?tl=pt-br

See more See fewer

EspaÃ±ol (LatinoamÃ©rica)

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/qwen_36_27b_on_24gb_vram_setup_backend/?tl=es-419

Italiano

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/qwen_36_27b_on_24gb_vram_setup_backend/?tl=it

Deutsch

https://www.reddit.com/r/LocalLLaMA/comments/1tgis7s/qwen_36_27b_on_24gb_vram_setup_backend/?tl=de

Community Info Section

r/LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

 

 

https://x.com/localllamasub

https://x.com/localllamasub

Join

LocalLlama

Subreddit to discuss locally hostable AI.

Show more

Public

Anyone can view, post, and comment to this community

Home

https://www.reddit.com/?feed=home

Popular

https://www.reddit.com/r/popular/

News

https://www.reddit.com/news/

Explore

https://www.reddit.com/explore/

Best of Reddit

https://www.reddit.com/posts/2026/global/

Best of Reddit in Portuguese

https://www.reddit.com/posts/2026/tl-pt-BR/

Best of Reddit in German

https://www.reddit.com/posts/2026/tl-de/

Reddit Rules

https://www.redditinc.com/policies/content-policy

Privacy Policy

https://www.reddit.com/policies/privacy-policy

User Agreement

https://www.redditinc.com/policies/user-agreement

Your Privacy Choices

https://support.reddithelp.com/hc/articles/43980704794004

Accessibility

https://support.reddithelp.com/hc/sections/38303584022676-Accessibility

Reddit, Inc. Â© 2026. All rights reserved.

https://redditinc.com/

 

Join the most real place on the internet

Continue with Apple

ï£¿â€…Sign in with Apple

Continue with Phone Number

https://www.reddit.com/login/

Continue with Email

https://www.reddit.com/register/

By continuing, you agree to our 

User Agreement

https://www.redditinc.com/policies/user-agreement

 and acknowledge that you understand the 

Privacy Policy

https://www.redditinc.com/policies/privacy-policy

.

 

0cAFcWeA6h0vhxVavOgMlo39kN71617yTDIvtXoMyjSR3EaxUVbI0JlOyCv7h8qB14tHyEWaRre7-9gTuTWLrZaFIAPB7k8KQi7wyN98BVszsXD7qJbzbRjBsjoBo-o5vIzq7b7euoxlSBBwdPfpcweQCh2dh2Fe0ad_zfI92USaP04CEGbixuEc2lwKzAMT4OitSG1tlwDd8_P6Up7ULTx0vd__Ilmtdxc0UrHNT0KOPTC6pvRt9vyGvNOx88gMgqRYSq7BsGIVw0gnbqS7aflawYdL5A8u0vQTDzxCopzW0KLwSPgqXk1dwh09gg1WH3jrlFac22SUORqGY9ujosqxlcKCWthrYaI4UxmampyJ7htjQC_kTvoiXS9B3r5lZkdIA9Q9UR5yZsyRTQz6VM3H4lMNaZ7piM0cwLMWoa1Cf4HwHxr5mHmC0B9T0GTIfPtOSqPKLvyvcjwDTd3-xOqlQYDmg8wQnuNbakoNZQXg-iEayinqWxvLUfOiY2g3VAMWYlHlQs4XDEFFyHHwsIv5yFcm5A4-5XI6QYxh3Xp-3rP6zWrgyY2yPEX4MKgmahL2VqpL4YN9YE9w4NZfAyu43TOvsqloloUgOGJLwGi5gOnsLmZcpd_b43WeDws8USsZOgNyglw5SVylyKb8DNIB-vTacy6twdz0jqPDCSIdPXkzhmW8GooJPKicuP-beEe7f0jUKTVx_dXBgOinyksRle-xcx0tH5CJFyOoTVfkGIKrDkpwHK1dgKmfjJ1Vjrrjqnpbqcd2ctSTc46fH6VVHC5L1ZiREiXyn_rzNuleFewc6ZoebSd000pV1TKa_IKQ0MUsrny7UUxmwoW97smrO8hRD8EKHh2IQY0WSx0PjqUGkyoQnwia7T-lwtKPMY3vqzHkqqM9eJqKhTJhJYXSgjRB6cCDnlWikLifXGG0Mo4HUdUBoIfj1oPeMQ1TFpfMs-YMqGhEK4gMVnZXk8H52kl4RHn8-AiaQ-rHAqu5efGgQquVemtWlV8DBMWVpi7ubK6CC4TMfpt-w2dCgc7BCuEOXjxdDfM5kobyGN4Jxb0lYBMRMZUfpNDk5WG-XiCL8KM5zR9zDF3sPT0sNUuZTsDNs0FJDf7Hz_cKQLKSHNbav1x2d9OL4pRz-q7Yt3hJ84uWiIUJJgosPZHeRg6COWjMVzGztDSYkZz0U7tGZm-oqV0GJwEVfcfYrPu1BIj_FC42RlZk47-8J4g_XwVNviIgKr30vcDAdiw9mzrMSRVASTumtxjf1SZX34YeQw7j40kcpSYPOTSz0ily-DdsrkCHlcah0kBNChAan3vRh5p4cyikpn8059LvR445gBwIVtrYIFloodTtQ8alt1S8g46CbJfFulBJW6Hnn7pWFBgRKfYlzuPdjLTWlF8iTWF-wdaTRFhLPzL0jbkPiqtGbH5xmPVgGrxckyEqBiBp-qmN9d2DLChQI4wWcqKkTGmula6yo7YKCMf70SMnEizKgKDjWPe4VEbLAw-yUxRYtq9AD53Bv6KkAmJcVw1zuMlqWKUbpa2GGSBXM6MLzd9WnlTcJrHwOAexM5coibUfro6MikJHUE86oplm-lIuDN-HqJ456yOjCWbJD2GRpPBOVcb5gXqKfb5ZYdUTGNHsEM_xH3btVbAorKe4k9M-jKzKQGYhy98FTZTzYBgw9v7vzsgyiTN5Dgd7RF1F8-dqQbU9RLMeJJ1Ija4uJj9y3k1BjNjPphZiPDPQxsyu_GBP04ILtZpKYoxhz30trye9X2a6_Qk6zpC3p2L3feO4qNSEdm4hX0gttbFMEN0TFDTo3Y_M6fJIwzp6KsMfPG9c8CH5UVclgqA5CC19LyHwS6f1XQj4li5tAVfDjNzJDLrDSwo6j6lLUIpL7byUWJGiv2zMIhHF21ezJtCmahawSDVcY9rJS9Gitrrs7iGbIvbYnMCvnpuErTEjjUuT6Fgoyz5vmXKPBMt4ib0Q4MWDqgxbGkk6GXW2rHQyROJosRDSYvA75To4NXGJormji5mtLN2awjyGSiXcjZ7Z-la9S4TKbtuvb0OwPAun8O8XpmoKRpByS-zbdLISo3dmpa9nVW89A1izl_s5jyncWKcoSP3VheTIgqU4YqSaSNewtPcldIpOncApJphrZncSWW1-ovtC39WIBbds63-g6R3pyuITegpl1D_WievakgotM_wUf3sijU6iIIy0jmuz5eFAyjM98X1Q05rZM
