---
title: "What free model should I use for speech-to-text?"
date: "2026-04-23"
mode: "CONCISE"
uuid: "3671e963-17a0-41b4-9a11-6551360c405a"
entry_count: 1
---

## Human

What free model should I use for speech-to-text?

## Assistant

For a **free** speech‑to‑text stack in 2026, the practical answer is:

> **Use OpenAI Whisper (open‑source) as your default, and consider newer open models only if you hit clear limits.**[1][2][3][4]

Below is a decision tree tailored to you (local + API options), then concrete picks.

***

## 1. First question: local vs API?

- **Local / self‑hosted required?** (privacy, offline, or massive volume)  
  → Prefer **open‑source models** (Whisper, Canary‑Qwen, Qwen‑ASR, etc.).[2][1]
- **Cloud OK, low volume, want “just works” API?**  
  → Consider APIs with **generous free tiers** (AssemblyAI, etc.).[5][6][7]

Given your profile (Calgary, AI systems, cost‑sensitive, automation), I’d assume:

- You’ll eventually want **local + scriptable + composable** over a tiny free API tier.
- You may still want an API as a **baseline reference** for accuracy.

***

## 2. Best free *open‑source* model (local)

### Primary recommendation: **OpenAI Whisper**

Whisper is still the **default starting point** for open‑source STT in 2026: widely deployed, robust across accents/noise, and supports many languages.[1][2]

- It’s consistently listed as the **top or most widely adopted open‑source ASR model**.[2][1]
- Community reports (e.g., LocalLLaMA) still consider **medium / large** Whisper as the most reliable for punctuation and structure.[4]
- There are many wrappers, servers, and optimizations, plus GPU/CPU variants.[3][1][2]

If you want **one thing to standardize on**, it’s Whisper.

**Whisper size to use:**

- **whisper-small / base**: fast, good enough for rough transcripts, cheap on CPU.[1][2]
- **whisper-medium**: sweet spot for accuracy vs speed (your likely default).[4][2][1]
- **whisper-large-v3+**: best quality, more GPU; good for batch jobs.[2][1]

> FACT: Articles comparing open‑source STT in 2026 still put Whisper at the top of the list of recommended models.[2]

### Interesting 2026 alternatives (when to care)

From a 2026 comparison of open‑source STT:[2]

- **NVIDIA Canary‑Qwen 2.5B** – strong multilingual and streaming; good if you’re already on NVIDIA stack.[2]
- **Qwen3‑ASR** – strong performance for some languages and more modern architecture.[2]
- **Kaldi, DeepSpeech, Julius, SpeechBrain, Coqui, Flashlight** – older/alternative toolkits; still used, but Whisper is simpler and usually more accurate out‑of‑the‑box.[1]

These are worth exploring if you:

- Need **specific language/latency/edge deployment** constraints that Whisper doesn’t meet.[1][2]
- Want to benchmark for research.

But for production-ish pipelines you’re building today, **start with Whisper, only switch if metrics justify it.**[1][2]

***

## 3. Best *cloud APIs with free tiers*

If you’re OK with external APIs and just want free usage for a small pipeline:

A 2026 comparison of free STT options highlights:[6][7][8][9][5]

- **AssemblyAI**  
  - Offers **$50 in free transcription credits**, enough for **hundreds of hours** depending on model.[7][5]
  - Supports **batch + streaming**, plus extra models (summarization, topic detection, etc.).[5][7]
  - Pricing after free tier is straightforward per‑hour.[5]
  - Good “one API” baseline to compare your local models against.[7][5]

- **Google Speech‑to‑Text**  
  - About **60 minutes free per month for first 12 months**, plus **$300 in cloud credits** for new GCP users.[8][7][5]
  - Supports **125+ languages** and integrates with GCP ecosystem.[8][7]
  - Needs audio in **Cloud Storage bucket**, extra plumbing for small scripts.[8][5]

There are also “fully free” OS engines (Whisper, Kaldi, etc.) that you self‑host, but the **API‑hosted** options above are the most practical “no‑infrastructure” paths.[5][1]

***

## 4. Quick comparison: local open‑source vs free‑tier APIs

| Option                      | Type        | Cost model                             | Pros                                                | Cons                                            |
|-----------------------------|-------------|----------------------------------------|-----------------------------------------------------|-------------------------------------------------|
| Whisper (medium/large)      | Open‑source | Free, run on your hardware             | Best‑in‑class open‑source, multilingual, robust [1][2][4] | You manage infra, GPU helps a lot              |
| Canary‑Qwen / Qwen‑ASR      | Open‑source | Free                                   | Newer architectures, good for some languages [2] | Less tooling/ecosystem than Whisper [2]    |
| Kaldi / DeepSpeech / etc.   | Open‑source | Free                                   | Mature toolkits, customizable [1]               | More complex; usually worse OOTB than Whisper [1] |
| AssemblyAI                  | Cloud API   | $50 free credits, then per‑hour [5] | Hundreds of hours free; streaming + analytics [5][7] | External dependency; after free tier it’s paid |
| Google Speech‑to‑Text       | Cloud API   | 60 min/mo free + $300 GCP credits [5][7][8] | 125+ languages; good accuracy; GCP integration [7][8] | Hassle (GCP project, Cloud Storage) [5]    |

***

## 5. Concrete recommendation tailored to you

Given your stack (Python, automation, multi‑agent orchestration, cost sensitivity):

1. **Primary choice: OpenAI Whisper (medium or large) locally.**  
   - Use a GPU box (local or cloud) for batch transcripts; CPU for shorter clips.[3][1][2]
   - Wrap it in a simple HTTP/CLI service that your agents call.

2. **Baseline reference: AssemblyAI free tier.**  
   - Use their $50 free credits to **benchmark** your Whisper pipeline on your real audio.[7][5]
   - If you see consistent major gaps (domain‑specific jargon, diarization), decide whether to pay or build custom fine‑tuning on open models.

3. **Only test alternatives (Canary‑Qwen, Qwen‑ASR) if/when you see a measurable weakness in Whisper for your domain.**[2]

***

## 6. Next: I can help you pick exact setup

Key questions that change the choice:

- Typical **audio length**? (Short commands vs 2‑hour podcasts vs meetings.)  
- **Languages/accents** you care about?  
- Need **real‑time streaming** or is **batch** fine?  

With those I can propose:

- A minimal **Dockerized Whisper service** (or Python CLI) for your environment.
- A reference **API client** for AssemblyAI or Google STT to benchmark against.

What’s your main use case: meetings, YouTube/podcasts, command‑and‑control, or something else?
