---
title: "Private Uncensored Text-to-Speech (TTS)"
created: 2026-08-01
source: session-2026-08-01
tags: [tts, text-to-speech, uncensored, local-ai, voice-cloning, audio-generation, privacy, reference]
summary: >
  Comprehensive research on private, uncensored text-to-speech: which open-source models
  run fully locally without cloud calls or content filters, their licenses, hardware
  requirements, voice cloning capabilities, and quality rankings as of mid-2026. Key finding:
  ALL open-source TTS models are uncensored by design — content filtering is exclusively a
  cloud API / LLM-wrapper feature, never built into the model architecture itself.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/local-audio-ai-models.md
    type: related
  - target: wiki/concepts/uncensored-ai-models.md
    type: related
  - target: wiki/concepts/tool-fallbacks.md
    type: related
---

# Private Uncensored Text-to-Speech (TTS)

## Decision context

**Why this research was needed:** the operator requested research on "private uncensored text to speech" — TTS solutions that (1) run entirely locally with no cloud API calls (private), and (2) have no content filters or safety guardrails (uncensored). This is distinct from cloud TTS (ElevenLabs, OpenAI TTS, Google Gemini TTS) which impose server-side content filters and require internet connectivity.

**What alternatives were explored:** the research covered 28+ open-source TTS engines across four dimensions — base engine quality, content filtering posture, voice cloning capability, and practitioner consensus. Cloud TTS was examined as the contrast case for understanding where filtering lives.

**What the research changed:** confirmed that for the open-source TTS space, "uncensored" is a non-issue — the models were never safety-trained, so there is nothing to bypass. The real decision axis is **license** (commercial-safe vs non-commercial) and **voice cloning** (preset voices vs zero-shot cloning). This redirects the problem from "which TTS is uncensored?" to "which TTS has the right license + capability for my use case?"

## Key findings

### Finding 1: Open-source TTS models have NO content filters [HIGH]

**Verified by:** F5-TTS GitHub issue #436 (documents that the base model is unfiltered; only the LLM voice-chat wrapper refuses NSFW), multiple practitioner sources (findskill.ai, localaimaster.com, ocdevel.com), and the absence of any counterexample in disconfirmation searches.

**The pattern:** TTS model architectures (encoder → decoder → vocoder, or flow-matching DiT, or autoregressive LLM) have no slot for a safety classifier. Training data is audio + text pairs, not "refuse on X topic" examples. There is no commercial incentive for open-source maintainers to add refusal behavior.

**Where filtering DOES live:**
- **Cloud API gateways** (ElevenLabs, OpenAI TTS, Azure TTS, Google Gemini TTS) — blacklist-based, tightening over time, non-bypassable
- **LLM wrappers** — when TTS is wrapped with an LLM for "smart" features (voice chat, agents), the LLM may refuse text before passing it to TTS. The F5-TTS voice-chat interface is the canonical example.
- **Watermarking** (Chatterbox PerTh, NeuTTS Air PerTh, VibeVoice) — not a content filter, but a traceability mechanism that persists in output audio

### Finding 2: License is the real constraint [HIGH]

**Verified by:** multiple sources cross-referencing model cards, GitHub LICENSE files, and HuggingFace metadata.

| License tier | Models | Commercial use |
|---|---|---|
| **Apache 2.0 / MIT** (fully open) | Kokoro, Chatterbox, OpenVoice v2, Bark, Orpheus 3B, Dia, Parler-TTS, Qwen3-TTS, CosyVoice 3, VoxCPM, MOSS-TTS, Piper (old MIT), MeloTTS | ✅ Yes |
| **GPL-3.0** (copyleft) | Piper (OHF-Voice fork) | ✅ Yes (copyleft caveat) |
| **CPML / CC-BY-NC** (non-commercial) | XTTS-v2, F5-TTS weights, ChatTTS, Voxtral TTS, Fish Speech S1-mini | ❌ No (personal/research OK) |

**Key insight:** for private, personal, uncensored use, ALL models are usable regardless of license. The license only matters if you plan to ship a product.

### Finding 3: Top recommendations by use case [HIGH]

**Default (no cloning needed):**
- **Kokoro-82M** — Apache 2.0, 82M params, runs on CPU (~2-3 GB VRAM or CPU), 54 preset voices, 8 languages. Top-5 on Speech Arena at 1/60th the size of competitors. Best efficiency/quality ratio.
- **Piper** — GPL-3.0 (active fork), CPU-first, <1 GB RAM, runs on Raspberry Pi 4. 30+ languages. Best for edge/embedded.

**Voice cloning (commercial-safe):**
- **Qwen3-TTS** — Apache 2.0, 3-second zero-shot cloning, 97ms latency, 0.6B/1.7B variants. Now the default TTS in HuggingFace's speech-to-speech pipeline. Best-in-class speaker similarity (0.789 vs ElevenLabs 0.646).
- **OpenVoice v2** — MIT, 1-5 second cloning, explicit style/emotion/accent decoupling (8 styles, 5 accents). Only major model with this granular control. Cross-lingual cloning.
- **Chatterbox** — MIT, 5-second cloning, 0.5B params. 65.3% preferred over ElevenLabs in vendor blind-test. ⚠️ Watermarked by default (PerTh).

**Voice cloning (non-commercial, highest fidelity):**
- **F5-TTS** — MIT code / CC-BY-NC weights, flow-matching DiT, 336M params. Best non-commercial cloning quality.
- **XTTS-v2** — CPML, 6-second cloning, 17 languages. Community workhorse despite Coqui shutdown (Jan 2024). Use Idiap fork for active code.

**Expressive/emotional:**
- **Orpheus 3B** — Apache 2.0, Llama-3.2-3B backbone, inline emotion tags (`<laugh>`, `<sigh>`, `<whisper>`). 6-8 GB VRAM.
- **Step Audio EditX** — Apache 2.0, top of Speech Arena (1,118 Elo), 14+ emotions, 30+ styles. 12+ GB VRAM.

### Finding 4: Practitioner consensus — "stack, don't pick" [MEDIUM]

**Verified by:** findskill.ai (May 2026 r/LocalLLaMA synthesis), localaimaster.com, openspeech.dev.

The dominant pattern in 2026 community threads is **stacking multiple models** rather than picking one:
- Kokoro for fast pipeline outputs / narration
- Chatterbox-Turbo when premium quality matters
- F5-TTS / XTTS-v2 for research-grade cloning
- CosyVoice 2 for multilingual real-time streaming

**Honest trade-offs practitioners report:**
- **Kokoro:** No voice cloning. Some pronunciation issues in long-form narration. espeak-ng phoneme fix needed for some words.
- **XTTS-v2:** Non-commercial license. Coqui is dead. No tonal inflection from punctuation (practitioner complaint, r/LocalLLaMA 2024).
- **Chatterbox:** PerTh watermark on every output — traceable, cannot be removed.
- **F5-TTS:** Non-commercial weights. Setup complexity.
- **Orpheus 3B:** Hungry for VRAM (8-12 GB). Speed collapses if it spills out of VRAM.
- **All vendor "beats ElevenLabs" claims:** Every blind test is maker-run, not independent (ocdevel.com).

### Finding 5: Minimum reference audio for voice cloning has dropped to 1-3 seconds [FACT]

| Reference length | Models |
|---|---|
| 1 second | OpenVoice v2 (claimed) |
| 3 seconds | Qwen3-TTS |
| ~5 seconds | Chatterbox |
| ~6 seconds | XTTS-v2 |
| 5-15 seconds | F5-TTS |
| 10-30 seconds | Fish Speech |

Quality improves with more reference audio up to ~30 seconds. For best results, use clean studio-quality audio.

### Finding 6: Hardware tiers [FACT]

| Tier | Hardware | Runs well |
|---|---|---|
| **Edge / CPU** | Raspberry Pi 4, 1-4 GB RAM | Piper, MOSS-TTS Nano, Kokoro (CPU) |
| **Consumer laptop** | Integrated GPU, 8 GB | Kokoro, Piper |
| **Mid-range GPU** | RTX 3060/4060, 8-16 GB | OpenVoice v2, XTTS-v2, F5-TTS, Qwen3-TTS 0.6B, Chatterbox |
| **High-end GPU** | RTX 3090/4090, 24 GB | All + Orpheus 3B, Bark, VoxCPM, Step Audio EditX |

Every mainstream open TTS fits within 12 GB VRAM with 5+ GB headroom (specpicks.com benchmark, Jul 2026).

### Finding 7: No "uncensored TTS" marketing category exists [FACT]

Unlike the LLM space (where "abliterated" / "uncensored" is a marketed category with HuggingFace tags and named fine-tunes), the TTS space has no equivalent. This is because open-source TTS models were never safety-trained — there is nothing to "uncensor." Users who want uncensored TTS simply use the base open-source model directly. HuggingFace searches for "nsfw" return almost exclusively LLM and image-gen models.

## Disconfirmation results

**Queries used:** "open source TTS model built-in content filter refuse profanity safety", "Kokoro TTS problems limitations issues criticism"

**Result:** No counterexamples found. No open-source TTS model with built-in content filters surfaced in any search. The F5-TTS GitHub issue #436 confirms the pattern (base model unfiltered, only LLM wrapper filters). Kokoro limitations (no cloning, pronunciation issues in long-form) are documented but minor and do not undermine the recommendation. All "beats ElevenLabs" claims are vendor-run — flagged but not refuted.

**Wiki contradiction check:** `local-audio-ai-models.md` covers Gemma 4 audio understanding (ASR, not TTS). No contradiction. `uncensored-ai-models.md` covers uncensored LLMs — complementary, not overlapping. The dangling `[[text-to-speech-synthesis]]` wikilink target in `local-audio-ai-models.md` now resolves to this page.

## Host invariant check

**Result:** No violations. All recommended models run locally via Python/CUDA. None touch browser state, cookies, CDP sessions, or shared live state. No `--cookies-from-browser` patterns. No multi-terminal contention risk beyond GPU resource sharing (if multiple agents run TTS simultaneously — a resource issue, not an invariant violation). Host invariant check passed.

## What this means for our workspace

1. **No TTS skill exists yet.** The wiki references `[[text-to-speech-synthesis]]` as a wikilink target in `local-audio-ai-models.md` but no concept existed until this page. This page resolves that dangling reference. If a TTS skill is needed (e.g., for generating audio from wiki content, handoffs, or agent outputs), the recommended starting point is **Kokoro-82M** (Apache 2.0, CPU-runnable, Python `kokoro` package — one-line install).

2. **`mmx speech synthesize` is the current fallback.** The `tool-fallbacks.md` wiki concept lists MiniMax CLI's TTS as the speech fallback. For fully private/uncensored use, a local model (Kokoro, Piper) should be preferred over `mmx` (which routes through MiniMax's cloud API). Consider adding a local TTS entry to the tool-fallbacks table.

3. **GPU resource sharing.** This host runs a multi-agent fleet. If multiple agents need TTS simultaneously, GPU contention is possible (especially for VRAM-hungry models like Orpheus 3B or Step Audio EditX). Kokoro (2-3 GB VRAM) or Piper (CPU-only) are the safe choices for concurrent use. The mid-range models (Qwen3-TTS, OpenVoice v2, Chatterbox at 4-6 GB) are fine for single-agent use.

4. **No content filter concern for fleet use.** Since open-source TTS models have no filters, any agent in the fleet can use them without worrying about refusals or blocked outputs. This is a non-issue for local deployment — the "uncensored" requirement is automatically satisfied by choosing any open-source model.

5. **Voice cloning ethics.** If voice cloning is used, follow the consent + disclosure + watermarking pattern documented in the voice cloning subagent findings. Local deployment does not exempt from GDPR biometric data requirements.

## Receipts

- **Finding 1 (no content filters):** [FACT] F5-TTS GitHub issue #436 (https://github.com/SWivid/F5-TTS/issues/436) — documents that the base F5-TTS model generates any text without refusal; filtering only in the voice-chat LLM wrapper. Disconfirmation search for "open source TTS model built-in content filter" returned zero counterexamples.
- **Finding 2 (license tiers):** [FACT] Model cards and LICENSE files verified via DDG searches and subagent web_fetch of GitHub repos. Cross-referenced across findskill.ai, localaimaster.com, ocdevel.com (3 independent aggregator sources).
- **Finding 3 (top recommendations):** [FACT] Specs verified from model cards (HuggingFace, GitHub READMEs). Quality claims from vendor benchmarks (flagged as vendor-run) and Speech Arena Elo rankings (ocdevel.com, Jun 2026).
- **Finding 4 (practitioner consensus):** [FACT] Synthesized from 13 Reddit r/LocalLLaMA threads (DDG snippets, some bodies unavailable) and 8 blog aggregator sources (findskill.ai, localaimaster.com, openspeech.dev, specpicks.com, blog.bymar.co, academy.kspl.tech, ocdevel.com, habr.com). Engagement signals (upvote counts) were [NO_RECEIPT] — Reddit MCP rate-limited.
- **Finding 5 (reference audio lengths):** [FACT] From model cards and comparison articles (localaimaster.com, spheron.network guide).
- **Finding 6 (hardware tiers):** [FACT] specpicks.com RTX 3060 12GB benchmark (Jul 15, 2026) — measured VRAM and RTF values.
- **Finding 7 (no uncensored TTS category):** [FACT] HuggingFace model search for "nsfw" returns LLM/image-gen only. No TTS model tagged "uncensored" or "nsfw" found.
- **Implementation path:** no local code inspected. All findings from web research (subagent DDG searches + web_fetch + parent-level HN Algolia + Reddit MCP). No workspace TTS installation exists to verify against.

## Related

- [[local-audio-ai-models]] — Local Audio AI Models (ASR focus; complementary to this TTS page)
- [[uncensored-ai-models]] — Uncensored AI Models (LLM focus; same privacy principle)
- [[tool-fallbacks]] — Tool Fallbacks (mentions `mmx speech synthesize` as TTS fallback)
- [[model-pool-selection-policy-speed-quota-diversity]] — Model pool selection (TTS as a fleet capability)
- [[research-quality-principle-efficiency-not-censorship]] — Research quality principle (uncensored research directive)

## Auto-related

<!-- Auto-generated by wiki_after_write.py — do not edit manually -->

## Sources

- **Subagent research (4 parallel subagents, session 2026-08-01):**
  - Local TTS engines survey (29 engines profiled)
  - Uncensored TTS filtering analysis (10 findings)
  - Local voice cloning systems (17 systems profiled)
  - Practitioner signals (Reddit r/LocalLLaMA, HN, blogs — 13 Reddit threads, 8 blog sources)
- **Key practitioner sources:**
  - [findskill.ai — Best Open-Source TTS 2026](https://findskill.ai/blog/best-open-source-tts-2026/)
  - [localaimaster.com — Best Local TTS Models 2026](https://localaimaster.com/blog/best-local-tts-models)
  - [ocdevel.com — Best Open-Source TTS 2026](https://ocdevel.com/blog/20250720-tts)
  - [openspeech.dev — 12 ElevenLabs Alternatives](https://www.openspeech.dev/elevenlabs-alternatives)
  - [specpicks.com — Local TTS on RTX 3060](https://specpicks.com/reviews/local-tts-rtx-3060-12gb-2026)
  - [blog.bymar.co — Open-Source Voice Cloning Alternatives](https://blog.bymar.co/posts/open-source-voice-cloning-alternatives-elevenlabs-2026/)
  - [academy.kspl.tech — MOSS-TTS v1.5](https://academy.kspl.tech/blog/2026-06-04-moss-tts-v15-open-source-beats-elevenlabs)
- **Key model sources:**
  - [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
  - [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
  - [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice)
  - [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)
  - [idiap/coqui-ai-TTS](https://github.com/idiap/coqui-ai-TTS) (XTTS-v2 active fork)
  - [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl)
  - [ResembleAI/chatterbox](https://huggingface.co/ResembleAI/chatterbox)
  - [canopyai/Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS)
  - [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice)
- **Filtering evidence:**
  - [F5-TTS GitHub issue #436](https://github.com/SWivid/F5-TTS/issues/436) — canonical proof that base model is unfiltered, only LLM wrapper filters
  - [ElevenLabs censorship Reddit thread](https://www.reddit.com/r/ElevenLabs/comments/1bhsylm/) — cloud API filter tightening over time

## Falsifier

This page is wrong if:
- An open-source TTS model is released with a built-in content filter at the model architecture level (not a wrapper)
- Kokoro, Qwen3-TTS, or OpenVoice v2 are found to have hidden filtering mechanisms not documented in their model cards
- The licensing landscape changes (e.g., Apache-2.0 models re-licensed to non-commercial)
- A new TTS paradigm emerges where safety training is baked into the acoustic model

Re-research if: >6 months old, or if a major new TTS release (e.g., MOSS-TTS 2.0, Qwen4-TTS) changes the rankings.
