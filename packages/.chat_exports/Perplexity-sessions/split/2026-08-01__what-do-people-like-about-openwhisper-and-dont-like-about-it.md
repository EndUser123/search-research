---
title: "What do people like about OpenWhisper and don't like about it? What are some of the top popular repos that are open sour"
date: "2026-08-01"
mode: "COPILOT"
uuid: "048f2b6a-0e69-41cd-8231-61faebda9a4c"
entry_count: 9
---

## Human

What do people like about OpenWhisper and don't like about it? What are some of the top popular repos that are open source and free?   I'm not talking about API costs, I understand those might not be free, but that doesn't have any rate limits or words per week limit.

## Assistant

People generally like **OpenWhispr/OpenWhisper-style** local dictation tools for privacy, offline use, and unlimited local transcription, and they tend to dislike setup complexity, weaker convenience features than polished commercial apps, and the fact that you still need decent hardware for good speed. For the underlying Whisper ecosystem specifically, users also praise accuracy and multilingual support, while complaining about slow processing on large audio files, lack of real-time dictation, and missing built-in speaker diarization or formatting features.[1][2][3][4][5][6]

## What people like

- Privacy-first: audio can stay on-device, which matters a lot for sensitive recordings and offline workflows.[2][7][5][6]
- No usage caps when run locally: there is no per-word or per-minute quota on your own hardware, so you can transcribe as much as your machine can handle.[7][6][2]
- Strong transcription quality: Whisper is widely praised for accuracy, especially on recorded speech and noisy audio, plus multilingual support.[3][8][1][2]
- Open ecosystem: there are many community tools built around Whisper, including faster-whisper and whisper.cpp, which improve speed or portability.[9][10]

## What people dislike

- It is not a polished dictation app by itself: the raw Whisper stack often lacks hotkeys, system-wide integration, and a smooth “press and speak” workflow.[6][2]
- Setup can be technical: many users need Python, FFmpeg, model downloads, or compilation steps, depending on the repo.[11][10][2][6]
- Performance can be rough on CPU or weaker hardware, especially with larger models and long files.[12][1][3][6]
- Missing product features: speaker diarization, live streaming, cleanup/formatting, and other workflow conveniences are often absent or partial.[13][3][12]
- Some repos are actively improving, but the ecosystem is still fragmented across multiple wrappers and ports.[5][10][9]

## Popular open-source repos

These are some of the better-known open source options in this space:

| Repo | Why people use it | Main tradeoff |
|---|---|---|
| [openai/whisper](https://github.com/openai/whisper) | Original reference implementation; multilingual ASR; strong accuracy [11][8] | Slower than optimized ports on many machines [1][9] |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Often much faster and more memory-efficient than the base implementation [9][14][15] | Still a developer-oriented pipeline, not a full dictation app [9] |
| [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Very portable, offline-friendly C/C++ implementation [10][16] | More manual setup and less “app-like” convenience [6] |
| [OpenWhispr/openwhispr](https://github.com/OpenWhispr/openwhispr) | Free/open-source dictation app with local and cloud model options [5] | Newer project; some rough edges and maintainer-scale limitations [17][18] |
| [Vaibhavs10/insanely-fast-whisper](https://github.com/Vaibhavs10/insanely-fast-whisper) | Opinionated CLI focused on speed [19] | CLI-first, so not ideal for non-technical users [19] |

## Practical pick

If your goal is “**free, open source, no rate limits, no word caps**,” then the best practical answer is usually **run Whisper locally** via either `whisper.cpp` for portability or `faster-whisper` for performance. If you want a more complete dictation app rather than a model/runtime, `OpenWhispr` is the closest fit among the repos surfaced here, but it is still less mature than commercial products.[10][17][18][9][5][6]

A useful rule of thumb is:
- Choose **whisper.cpp** if you want the most self-contained offline option.[10][6]
- Choose **faster-whisper** if you want speed and a Python-friendly developer workflow.[14][9]
- Choose **OpenWhispr** if you want a free desktop dictation app with local models built in.[5]

A confidence note: the “what people like/dislike” part is a synthesis of official repo descriptions, product docs, and user-review/review-style sources, so it is directionally reliable but not a statistically rigorous survey.[1][2][3][6][5]

## Human

Well, I want to use it for press the talk to chat with my chat, chat, elolams in web pages and CLIs and word editing, etc.

## Assistant

For your use case—press-to-talk into web pages, CLI prompts, editors, and general text fields—OpenWhispr is much closer to the right category than raw Whisper repos, because it is built as a **system-wide dictation app** with a global hotkey and text insertion at the cursor rather than just a transcription engine. The key caveat is that the exact push-to-talk behavior is platform-dependent, so you should treat “works anywhere” as mostly true for text fields, but verify hotkey mode and paste behavior on your OS before committing.[1][2][3][4][5]

## Fit for your workflow

OpenWhispr explicitly says “press a hotkey, speak, and your words appear at your cursor” and that it works in any app, which is exactly the pattern you want for chats, browser text boxes, terminals, and document editing. It also supports local Whisper and Parakeet models, so if you run locally there are no transcription usage caps or weekly word limits tied to the local models themselves.[6][2][5][7][1]

That said, there is an important ambiguity: one secondary source mentions a “Community” tier with 2,000 words per week, while OpenWhispr’s own comparison page says local features have no usage limitations. FACT: the primary-source wording is stronger for local models, so the safest interpretation is that **local transcription is uncapped**, while any hosted/managed cloud features may be where plan limits appear; if this matters operationally, rely on local mode only.[8][7][6]

## What matters technically

For your workflow, these features are the ones that matter most:

- Global hotkey dictation into the focused app, including browser fields and desktop apps.[2][5]
- Offline local execution with Whisper or Parakeet, meaning no network dependency for the transcription path.[6][2]
- Cross-platform support on macOS, Windows, and Linux, though exact hook behavior differs by OS.[3][4][2][6]

The main operational concern is push-to-talk support. The Quick Start says push-to-talk is currently available on Windows, while the changelog also mentions Linux push-to-talk via evdev, which suggests the capability is evolving and may depend on permissions or release version rather than being uniformly available everywhere. CONSENSUS: if you need rock-solid hold-to-talk today, Windows appears the clearest supported path in the surfaced docs.[4][3]

## Likely pain points

The project’s own issue list shows friction around canceling dictation in hold/push-to-talk mode and local transcription continuing after cancellation, which is exactly the kind of edge case that becomes annoying in a rapid chat-and-edit workflow. That does not mean the app is bad; it means the product is still maturing in the workflow details that power users notice first.[9][10]

A second practical issue is terminal behavior. OpenWhispr inserts text “at your cursor,” but terminals vary in how they handle paste, control characters, shell focus, and hotkeys, so **CLI compatibility is likely good for prompt entry but not guaranteed identical across terminal apps**. SPECULATION, medium confidence: for PowerShell or other terminals, “tap to toggle then paste at cursor” will probably be more reliable than true hold-to-talk until you validate it in your exact terminal stack.[5][1][3][4]

## Best choices

If your priority is “voice everywhere on my desktop,” I would narrow it like this:

| Option | Best for | Why |
|---|---|---|
| [OpenWhispr](https://github.com/OpenWhispr/openwhispr) | System-wide press-to-talk dictation | Built for hotkey-to-cursor workflows, local models, desktop use [2][5] |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Backend transcription engine | Fast local ASR, but not a desktop dictation UX by itself [11][12] |
| [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Minimal offline transcription stack | Very portable and local, but not a polished “dictate into any app” workflow on its own [13][14] |

For your exact goal, I would start with **OpenWhispr first**, because it solves the desktop integration layer that raw repos do not. If it proves flaky in your terminal/editor stack, the fallback architecture is to pair a fast local engine like faster-whisper or whisper.cpp with a separate hotkey/clipboard automation layer, but that is more DIY and only worth it if OpenWhispr misses on reliability.[11][13][1][2]

## Next step

Install OpenWhispr and test only these four cases first: a browser chat box, your preferred terminal, a document editor, and one coding tool text field; use local models only, and compare **tap-to-toggle** versus **push-to-talk** on your OS. Which OS do you want to run this on—Windows 11, Linux, or macOS?[3][5][6]

## Human

<q>OpenWhispr</q> How can I tell what my words per week used is so far?

## Assistant

You check it **inside OpenWhispr itself**: the cloud plan has an in‑app usage bar and stats panel, but local dictation does not show a “words used” counter because it is not capped.[1][2][3][4]

## Fact vs. plan type

FACT from the changelog and multiple reviews:  

- The **Free cloud plan** has a rolling weekly word limit (2,000 words/week) for cloud transcription, with a real‑time usage display, progress bar, thresholds, and “next billing date” shown in the app’s account/usage section.[2][4]
- **Local models (Whisper/Parakeet) are unlimited** in the free tier; several sources explicitly say there is “no weekly word cap” for local dictation, only for cloud usage.[3][4]

CONSENSUS: you only need to track “words per week” if you are using OpenWhispr Cloud; if you’re on local models only, you won’t hit a weekly cap and the counter is mostly academic.[5][4][3]

## Where to see your word usage (cloud)

According to the Quick Start and changelog, usage for cloud transcription is visible in the app settings/account area:

- The Quick Start guide explicitly lists “View usage statistics (for cloud users)” as an item on the main Settings/Control Panel menu.[1]
- The changelog describes an “Account Section in Settings” with **plan status**, a **usage bar**, and **color‑coded thresholds**, plus upgrade prompts when you approach or hit the limit.[2]

So, operationally:

1. Open the OpenWhispr desktop app.  
2. Go to **Settings** or **Account/Subscription** (wording may vary by version).  
3. Look for a **usage bar / progress indicator** showing your **cloud words used** out of 2,000 for the current week, plus any meeting recording limits (e.g., 5 hours/month).[4][2]

This only tracks **cloud** STT usage; the app’s own telemetry wiring in the changelog talks about “cloudStreamingUsage,” not local-word tracking.[2]

## If you’re using local models only

When you switch to local Whisper or Parakeet in the app, sources indicate that:

- Your dictation is **unlimited** (no weekly word cap), and  
- The 2,000‑words/week cloud allowance is **not decremented** by local usage.[5][3][4]

One YouTube walkthrough explicitly notes that their local dictation isn’t “even counting the 2,000 words” against the limit, confirming that local usage is outside the cloud meter. In that mode, there is no practical “word per week” to check—and you can treat the system as effectively uncapped for words.[5]

## Assumptions and uncertainty

- I’m assuming you’re signed in to OpenWhispr Cloud on a relatively recent build; very old versions might have a simpler UI and less clear usage visualization.[1][2]
- I’m also assuming “words” refers to **cloud STT tokens**, not local text length—OpenWhispr’s telemetry wiring is clearly focused on cloud providers (Deepgram and similar), not on the local engine’s output.[2]

If you open Settings and don’t see any usage bar at all, that almost certainly means you’re either on a local‑only setup or on a build prior to the subscription/usage UI changes.[6][2]

Do you currently have OpenWhispr configured to use **Cloud** or **Local** (Whisper/Parakeet) as your transcription backend?

## Human

what model is best when used locally?

## Assistant

For OpenWhispr‑style local use on your desktop, the **best default choice** is usually **OpenAI Whisper “Base” or “Small”**, with **NVIDIA Parakeet Unified EN 0.6B** as the main alternative if you’re on a strong NVIDIA GPU and want slightly more streaming‑friendly behavior. This balances accuracy, latency, and VRAM so dictation feels instantaneous rather than batchy.[1][2][3][4]

## How to choose in practice

From the models shown in your screenshots, you effectively have two families:

- **OpenAI Whisper**: Tiny, Base, Small, Medium, Large, Turbo (sizes from ~75 MB to multiple GB). Local variants are well understood and widely benchmarked.[3][4][5][6]
- **NVIDIA models**: Parakeet TDT 0.6B, Parakeet Unified EN 0.6B, Nemotron Speech Streaming EN 0.6B, Nemotron 3.5 ASR Streaming 0.6B (all around 600–680 MB).[1][3]

Given your “press‑to‑talk everywhere” use case:

- **Whisper Base (141 MB)**: best all‑rounder if you care about **speed** and **decent accuracy** on consumer hardware; widely recommended as a default in many tools.[5][6][3]
- **Whisper Small (466 MB)**: better accuracy, still reasonably fast on a decent GPU or strong CPU; good if you dictate a lot of long emails/docs and can tolerate a little more latency.[4][6][3][5]
- **Parakeet Unified EN 0.6B**: tuned for English, streaming‑style; designed for low‑latency on NVIDIA GPUs, and referenced as a strong option for local ASR in recent guides.[3][1]

CONSENSUS from performance write‑ups: for interactive dictation you almost never need “Medium/Large/Turbo”; those are more for offline batch transcription where latency isn’t tight and VRAM is plentiful.[4][3]

## Recommended combinations

Assuming a modern Windows 11 box with GPU acceleration active (your screenshot shows this), I’d pick like this:

- If you want **maximum responsiveness** in chats, CLIs, and editors:  
  - Use **Whisper Base** as your primary local model.[6][5]
- If you want **higher accuracy** and can accept slightly longer processing:  
  - Use **Whisper Small** or **Parakeet Unified EN 0.6B**, and run a short test on 1–2 minute recordings to see which feels faster on your specific GPU.[1][3][4]

SPECULATION, medium confidence: Parakeet Unified EN should be competitive with Whisper Small for English dictation, but Whisper still has the broader community benchmarks and edge‑case tuning, so I’d start with Whisper and treat Parakeet as an “experimental” second profile.[2][3][1]

Would you rather optimize for **speed** or **maximum accuracy** on your current machine?

## Human

I have a 5070 with 12gb vram

## Assistant

With a 5070 and 12 GB VRAM, you can comfortably run **Whisper Medium** or the **NVIDIA Parakeet Unified EN 0.6B** models locally and still get near‑real‑time dictation; you’re not constrained to the tiny/base tier at all.[1][2][3][4]

## Whisper: what your GPU can handle

Benchmarks on similar GPUs show that:

- **Whisper Small** uses ~2 GB VRAM, and **Medium** uses ~5 GB VRAM in GPU mode, with Medium giving noticeably better accuracy (lower WER) at roughly half the speed of Small.[4][1]
- Guides built around RTX 3060‑class cards (8–12 GB VRAM) explicitly say **“all models fast; large needs ~10 GB VRAM”**, which maps well to your 5070 with 12 GB—Medium is well within comfort, and Large is still feasible if you don’t mind higher latency.[5][1][4]

Given your interactive “press‑to‑talk” workflow:

- **Best balance of accuracy and latency:** **Whisper Medium**. Your 12 GB VRAM easily covers its ~5 GB footprint; you’ll get higher accuracy than Small without killing responsiveness.[1][4]
- **If you want extra snappiness:** **Whisper Small** remains a strong choice and will be indistinguishable from real‑time on a 5070 for typical dictation lengths.[4][1]

CONSENSUS from multiple Whisper guides: for general English dictation on a desktop GPU, **Small or Medium** are the sweet spot, with Medium favored when VRAM is plentiful and you care about accuracy.[1][4]

## NVIDIA Parakeet and Nemotron

For the NVIDIA side:

- **Parakeet Unified EN 0.6B**: designed as an English ASR with good accuracy and latency across streaming setups; leaderboard data shows ~5.9–6.5 WER across low‑latency configurations, meaning it maintains quality even when you push latency down.[3]
- Trials comparing Parakeet to Whisper report Parakeet can be **~10× faster** on the same hardware, but often with slightly different error characteristics (e.g., names vs time expressions) rather than a clear “always better” or “always worse”.[6][7]

Your 5070’s 12 GB VRAM and high bandwidth make these 0.6B Parakeet variants straightforward to run; they were designed with CUDA and streaming in mind. SPECULATION, medium confidence: if OpenWhispr is wired to use NVIDIA’s streaming pipeline efficiently, Parakeet Unified EN will feel more “live” than Whisper Medium, at slightly lower accuracy on some edge cases.[2][8][6][3]

Nemotron 3.5 ASR Streaming 0.6B is similar scale; it’s more experimental in the ecosystem, so unless you have a specific reason, I’d treat it as a secondary choice after Parakeet Unified EN.[3]

## Concrete recommendation for your 5070 (12 GB)

Given all of that, I’d set it up like this:

1. **Primary local model: Whisper Medium**  
   - Use this when writing longer text (emails, docs, notes) where accuracy matters more than shaving off a few hundred ms in latency.[4][1]

2. **Secondary “fast profile”: Parakeet Unified EN 0.6B**  
   - Use this for rapid press‑to‑talk chats and CLIs where you want extremely low latency and don’t mind a small trade‑off in occasional word choice or names.[7][6][3]

3. Only drop down to **Whisper Small** if you discover Medium is noticeably too slow for your typical snippet length; on a 5070 that’s unlikely except for very long recordings.[5][1][4]

Confidence: high that your hardware is sufficient for Medium and Parakeet Unified EN; medium on exact speed vs accuracy trade‑off, since that depends on your audio quality and typical sentence length.[2][3][1]

Do you mostly dictate **short chat messages and commands**, or **multi‑paragraph documents and notes**?

## Human

Short, fast chat messages where it drives me nuts when there's a delay.

## Assistant

For short, fast chat messages where delay drives you crazy, the best local choice is a **low‑latency model**: either **Whisper Tiny/Base** or **NVIDIA Parakeet Unified EN 0.6B / Parakeet TDT 0.6B**, with a slight preference for Parakeet if OpenWhispr’s integration is solid on your machine.[1][2][3][4]

## Latency‑first options

For “press, speak 2–5 seconds, release, see text almost instantly”:

- **Whisper Tiny**  
  - Fastest Whisper variant: benchmarks show it running around **10× real‑time** relative to large, and with practical latency well under 0.5 seconds on a mid‑range GPU for short clips.[2][4]
  - Trade‑off is accuracy (WER ~7–10% instead of ~3–5%), but for chat messages and commands this is often acceptable.[5][2]

- **Whisper Base**  
  - Still very fast (around 7–16× real‑time on consumer GPUs) with better accuracy than Tiny; recommended as “best choice when latency matters more than perfect accuracy” in recent OpenWhispr documentation.[6][4][2]
  - On a 5070, you’ll likely see sub‑second processing for typical short utterances.[4][2]

- **Parakeet Unified EN 0.6B / Parakeet TDT 0.6B**  
  - Designed for **streaming ASR**; official docs show streaming latencies down to **160–240 ms** while keeping WER competitive with larger models.[3]
  - Community tests report Parakeet models running roughly **10× faster than Whisper** on the same hardware for long audio, which translates into extremely “snappy” behavior for short phrases.[7][8][9]

On your RTX 5070 (12 GB), all of these are well within VRAM and throughput envelopes; you’re not constrained by hardware.[10][11]

## Concrete recommendation for your chat workflow

Given you care more about **latency** than perfect word‑for‑word accuracy:

1. Set **Parakeet Unified EN 0.6B** (or TDT 0.6B if OpenWhispr labels that as the “streaming” profile) as your primary local model.  
   - It’s explicitly optimized for low‑latency streaming and should feel “instant” for short chat messages.[12][9][3]

2. Keep **Whisper Base** available as a fallback profile.  
   - If you notice Parakeet occasionally butchering names or certain phrasing, switch a session to Base and see if the accuracy trade‑off is worth the slightly higher latency.[2][6][5]

3. Avoid **Whisper Medium/Large** for this specific use case.  
   - Benchmarks show Small/Medium can introduce **0.5–2 s behind live speech**, which is exactly the kind of delay that will annoy you in chat.[4][2]

SPECULATION, high confidence given the benchmarks: on your 5070, **Parakeet Unified EN 0.6B** should feel more responsive than any Whisper variant for short utterances, with accuracy good enough for conversational text.[8][9][7][3]

Would you be okay occasionally correcting a word or two if it keeps latency under ~300 ms, or do you want it both fast and as accurate as possible?

## Human

do some socials search on which nvidia model people like the best for my usecase

## Assistant

Socials and recent benchmarks point to **two NVIDIA picks** for your “short, fast chat messages, delay is unacceptable” use case:  
- **Nemotron Speech Streaming EN 0.6B** for *pure latency* and streaming UX.  
- **Parakeet Unified EN / Parakeet TDT 0.6B v3** for *very fast, local, English‑focused ASR* with strong accuracy.  
[1][2][3][4][5][6][7]

## What people say on socials

From Reddit, YouTube, LinkedIn, and NVIDIA/Hugging Face posts:

- **Parakeet 0.6B (TDT / Unified EN)**  
  - Users describe it as “fantastic. Fast, local, gets the job done” and “as fast as cloud” for everyday English transcription.[2][7][1]
  - Community comments highlight it as a practical upgrade over Whisper for English, especially when you want high throughput and low lag on a single machine.[7][1][2]

- **Nemotron Speech Streaming EN 0.6B / Nemotron 3.5 ASR 0.6B**  
  - NVIDIA marketing + technical posts emphasize **cache‑aware streaming** with **very low latency (down to ~80–160 ms)** and stable end‑to‑end lag even at high concurrency.[8][4][6][2]
  - Academic benchmarks find Nemotron‑0.6B achieving the **best streaming WER among tested models** with **~0.56 s algorithmic latency**, and int4/quant variants staying faster than real‑time on CPU with sub‑second delay.[5]
  - Community guides show Nemotron 3.5 ASR running **4.5× real‑time on CPU** in multilingual setups, with trade‑offs in WER depending on configuration (you can dial latency vs accuracy).[9][10][11]

Consensus in socials for **English, short utterances**:  

- People who switched from Whisper for local use often **praise Parakeet Unified 0.6B v3 for English** as a strong “Whisper replacement,” especially when they want something that feels as fast as cloud but runs locally.[1][2][7]
- People testing Nemotron emphasize its **configurable latency modes** and “zero latency drift” at load, making it attractive for real‑time voice agents and interactive chat pipelines.[4][6][8][5]

## How this maps to your use case

Your constraints:

- **Short, fast messages**, where even 500–800 ms of post‑speech lag feels annoying.  
- Local, GPU‑accelerated on an RTX 5070 12 GB.  

Given that:

- **Parakeet Unified EN 0.6B**  
  - Socials and benchmarks show it as a very strong **English dictation** choice: fast, local, “gets the job done” with excellent WER, and widely regarded as an upgrade over Whisper for English on desktop GPUs.[12][2][7][1]
  - Likely to feel “instant enough” for chat messages with minimal setup friction.  

- **Nemotron Speech Streaming EN 0.6B**  
  - Engineered for **real‑time streaming** with runtime‑configurable latency modes (e.g. 80 ms, 160 ms, 560 ms, 1.12 s) and almost flat latency even as you increase concurrent streams.[6][8][2][5]
  - Socials frame it as a “Whisper killer” for real‑time voice agents exactly because it avoids the latency drift seen in sliding‑window models like Whisper.[4][6]

SPECULATION, high confidence:  

- For **single‑user desktop dictation into chats**, **Parakeet Unified EN** will likely be the more straightforward, “just works” choice with excellent English accuracy and more than enough speed.  
- If a future setup involves **multi‑stream voice agents** or you want to squeeze latency toward tens of milliseconds and tune accuracy/latency per scenario, **Nemotron Speech Streaming EN** becomes more compelling, with more knobs and slightly more complexity.  

## Social‑driven recommendation

Based on social feedback and your low‑latency priority, I’d set it up as:

1. **Primary local model: Parakeet Unified EN 0.6B**  
   - Community sentiment: best “fast English ASR” NVIDIA model today for local use, widely adopted as a Whisper replacement.[2][7][12][1]

2. **Secondary profile for experiments: Nemotron Speech Streaming EN 0.6B**  
   - Use if you want to experiment with ultra‑low latency and tune streaming configs once you’re happy with the base Parakeet experience.[8][5][6][2][4]

Confidence: high that this order matches what people are doing in practice for local English chat/commands; medium on how much Nemotron’s extra complexity will matter for you personally, since many desktop users seem happy stopping at Parakeet.[7][1][2]

Would you prefer to keep things simple (just Parakeet Unified EN), or are you interested in experimenting with Nemotron’s latency modes once you’re set up?

## Human

what about if you exclude socials older than 3 months?

## Assistant

If you limit to the last ~3 months, the “socials + reviews” pattern shifts slightly: **Nemotron 3.5 / Nemotron Speech Streaming EN 0.6B** shows up more as the *streaming, ultra‑low‑latency* favorite, while **Parakeet TDT/Unified 0.6B v3** is praised as the *high‑throughput English dictation* model that beats Whisper in accuracy‑per‑GPU‑second.[1][2][3][4][5][6]

## What recent sources say (last ~3 months)

From July–late April 2026 (blogs, benchmarks, Reddit, Instagram, NGC catalog):

- **Parakeet TDT 0.6B v3 / Unified EN**  
  - A 2026 open ASR roundup calls Parakeet TDT 0.6B v3 “the throughput leader among multilingual open models,” with **RTFx > 3,300** and a WER slightly *better* than Whisper large‑v3, but focused on English + European languages.[4][7][1]
  - A June 2026 self‑hosted Whisper guide explicitly notes that “Whisper no longer holds the open accuracy crown” and that Parakeet‑TDT‑0.6B‑v3 posts lower average WER than Whisper large‑v3 at dramatically higher throughput.[4]
  - Interpretation in those articles: if your main concern is **local English dictation at high speed**, Parakeet is the new default “serious” open model to benchmark against Whisper.[7][1][4]

- **Nemotron Speech Streaming EN 0.6B / Nemotron 3.5 ASR**  
  - NVIDIA and third‑party blogs emphasize Nemotron 3.5 ASR as a **streaming model across 40 locales** that runs real‑time on CPU and scales to many concurrent clients with **stable end‑to‑end latency and minimal drift**.[2][3][8][9]
  - A recent technical paper reports Nemotron‑0.6B achieving **best streaming WER (7.28%)** among tested models while also having **lowest latency (~0.56 s)** in a standardized evaluation, with chunk sizes and context configurable for even more aggressive low‑latency settings.[10][6]
  - A July 2026 production review stresses that 80 ms is the *audio chunk size*, not user‑perceived latency; in practice you tune chunk size and context to hit your desired latency/accuracy envelope.[11]

- **Local ASR comparison threads (July 2026)**  
  - A “best local ASR” discussion from early July 2026 confirms that **Whisper remains the default starting point**, but that Parakeet and Nemotron are now considered serious alternatives, especially when speed and streaming behavior matter.[12][13][4]

## For your “short, fast chat” use case (updated)

With this recency filter, the pattern for your scenario becomes:

- If you care about **fast desktop dictation in English, short utterances, accuracy still matters**:  
  - Recent non‑social benchmarks and guides strongly favor **Parakeet TDT/Unified 0.6B v3** over Whisper, calling it both faster and at least as accurate for English.[1][7][4]
  - That lines up with your use case (single‑user, hotkey hold‑to‑talk, English chat messages).  

- If you care about **ultra‑low streaming latency and possibly future multi‑stream voice agents**, and you’re willing to tune chunk sizes and ASR parameters:  
  - Nemotron 3.5 / Nemotron Speech Streaming EN 0.6B is the model recent reviews highlight for **streaming, multi‑locale, real‑time voice agents**, with the best measured streaming WER/latency combo and strong CPU support.[3][8][6][9][2]
  - That’s more relevant if you later build more complex voice pipelines or want to squeeze latency below 500 ms with fine‑grained control.  

So, **excluding older socials**, the best NVIDIA model for *your current* use case (short, fast, English desktop chat) is still **Parakeet Unified/TDT 0.6B v3**, with **Nemotron 3.5/Nemotron EN 0.6B** as the more advanced streaming option if you later care about multi‑language or multi‑stream agents.[2][3][7][1][4]

Would you rather keep it simple and go “Parakeet now, Nemotron later if needed,” or do you want to jump straight into tuning Nemotron’s streaming settings for minimum possible latency?

## Human

openwhispr doesn't expose settings for any of the models.

## Assistant

You’re right that OpenWhispr doesn’t expose *fine‑grained* model settings (chunk size, context frames, etc.) for you to tweak; it only lets you **pick which model family to use** and then uses sane defaults internally.[1][2][3]

## What OpenWhispr actually exposes

OpenWhispr’s docs and models page make this explicit:

- You choose **which local engine and model** under **Settings → Speech Recognition → Local**:  
  - Whisper (Tiny/Base/Small/Medium/etc.)  
  - NVIDIA Parakeet (TDT 0.6B v3, Unified EN 0.6B)  
  - Nemotron (Speech Streaming EN 0.6B, Nemotron 3.5 ASR Streaming 0.6B).[2][3][1]
- For each, the app shows **size, speed, quality** and a simple “Pick X when you want Y” table (e.g., “live English preview → Nemotron EN; max English accuracy, don’t care about live preview → Parakeet Unified EN”).[2]
- It does **not** expose low‑level ASR parameters (e.g., Nemotron’s `att_context_size` or Parakeet’s streaming chunk/window config) in the UI; those are configured inside the sherpa‑onnx server and OpenWhispr’s integration.[4][5][2]

So from your perspective, “settings” means:

- **Which model** is active.  
- Whether you’re on **Local vs Cloud**.  
- Generic app‑level dictation/preview behaviors (e.g., live preview vs commit‑after‑stop).[6][1][2]

You can’t, for example, dial Nemotron from 560 ms to 160 ms latency by changing `chunk_size` in OpenWhispr’s UI; that would require code‑level changes in the sherpa‑onnx or NIM integration.[5][2]

## Best choice given that constraint

Given you can *only* choose the model, not its internals, the practical answer for your “short, fast chat messages” use case inside OpenWhispr is:

- **Local, English, minimum perceived delay → Nemotron Speech Streaming EN 0.6B**  
  - OpenWhispr’s own blog says: “You want live English preview while dictating → **Nemotron Speech Streaming EN 0.6B**”.[2]
  - That implies they’ve tuned Nemotron’s streaming config for low latency and live partials in the app; you get that benefit just by selecting the model.  

- **Local, English, accuracy over live preview → Parakeet Unified EN 0.6B**  
  - Same blog: “Maximum English accuracy, don’t care about live text → **Parakeet Unified EN 0.6B**”.[2]
  - This is the “more accurate but slightly less live” option.  

Because OpenWhispr hides the low‑level settings, your lever is simply **which model you select**, not how it’s configured. For “delay drives me nuts,” the app’s own guidance points you straight at **Nemotron Speech Streaming EN 0.6B** for live English dictation.[5][2]

Confidence: high, because this is coming from OpenWhispr’s official “Choosing a Model” section rather than social speculation.[3][1][2]

Are you okay prioritizing live preview and minimal delay even if Nemotron occasionally makes more small errors than Parakeet?
