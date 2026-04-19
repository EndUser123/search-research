<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# what are the current gemini rate limits per day for v2.x and v3.x

Google’s Gemini API expresses rate limits along multiple dimensions (RPM, TPM, RPD, IPM), and **values differ by billing tier and model family** rather than a single “per‑day” ceiling for “v2.x” or “v3.x” as a whole.[^1_1][^1_2][^1_3]

Below are the current **free‑tier daily request limits (RPD)** for representative 2.x and 3.x models as of early 2026, taken from Google’s official rate‑limit docs and recent third‑party summaries.[^1_2][^1_3][^1_4][^1_1]

***

### Gemini 2.x‑series (v2‑style models)

For “Gemini 2.x”‑style models (e.g., 2.0 / 2.5 generations), the free‑tier RPD values are roughly:

- **Gemini 2.5 Pro**: 100 requests per day (RPD) on free tier.[^1_3][^1_2]
- **Gemini 2.5 Flash**: 250 requests per day (RPD) on free tier.[^1_2][^1_3]
- **Gemini 2.5 Flash‑Lite**: 1,000 requests per day (RPD) on free tier.[^1_3][^1_2]
- **Gemini 2.0 Flash‑Lite**: 1,500 requests per day (RPD) on free tier.[^1_5][^1_3]

Higher tiers (Tier 1, 2, Enterprise) increase these values; for example, Tier 1 can reach **~10,000 RPD** for Flash‑class models.[^1_2][^1_3]

***

### Gemini 3.x‑series (Gemini 3 / 3.1)

For “Gemini 3.x”‑style models (3.0, 3.1, including 3 Flash, 3.1 Flash, 3.1 Pro), free‑tier RPD is generally **lower** than 2.5 defaults and often capped around:

- **Gemini 3 / 3.1 Flash (Preview)**: 20–100 requests per day (RPD) on free tier, depending on the specific 3.x flavor and Google’s current preview‑tier caps.[^1_4][^1_6][^1_1]
- **Gemini 3 Pro (Preview)**: 100 RPD on free tier in many recent reports, with 5 RPM.[^1_4][^1_2]

Paid tiers (Tier 1+) can push 3.x‑series RPD into the **thousands–tens of thousands per day**, but exact numbers are documented per model and quota bucket in the official console.[^1_7][^1_2]

***

### How to check your exact caps

Because RPD is **per‑project, per‑model, and tier‑dependent**, the canonical way to see your current ceiling is:

1. Open the **Google AI Studio** or **Google Cloud Console** for your project.
2. Go to **“Quotas”** or the **Gemini API rate‑limits page**, filter by `gemini` or `generative-ai` services, and inspect the **“Requests per day”** quota for your model.[^1_1][^1_7]

If you tell me whether you’re asking about **free tier vs. Tier 1+**, and which exact model name (e.g., `gemini‑2.5‑pro`, `gemini‑3‑flash`, `gemini‑3‑pro`), I can map out concrete RPD/RPM/TPM triples for that combo.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://ai.google.dev/gemini-api/docs/rate-limits

[^1_2]: https://blog.laozhang.ai/en/posts/gemini-api-rate-limits-guide

[^1_3]: https://yingtu.ai/en/blog/google-gemini-api-free-tier-limits-2025

[^1_4]: https://help.apiyi.com/en/ai-studio-gemini-3-pro-rate-limit-solution-en.html

[^1_5]: https://gemini-api.apidog.io/doc-965865

[^1_6]: https://www.reddit.com/r/GeminiCLI/comments/1qk3isy/confused_about_google_ai_studio_pro_subscription/

[^1_7]: https://docs.cloud.google.com/gemini/docs/quotas

[^1_8]: https://support.google.com/gemini/answer/16275805?hl=en

[^1_9]: https://www.reddit.com/r/Bard/comments/1ijexdb/question_does_gemini_advanced_has_rate_limits_50/

[^1_10]: https://www.reddit.com/r/GeminiAI/comments/1m38qau/gemini_api_rate_limit/

[^1_11]: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/quotas

[^1_12]: https://www.reddit.com/r/GeminiAI/comments/1lv2oz5/does_anyone_successfully_got_rate_limit_increases/

[^1_13]: https://developers.google.com/gemini-code-assist/resources/quotas

[^1_14]: https://discuss.ai.google.dev/t/requests-per-day-upgrade-gemini-3/113978

[^1_15]: https://support.google.com/gemini/thread/400904312/rate-limits-gemini-flash-3-0-and-2-5?hl=en


---

# what category should I look for regarding video analysis?

Model
Category
RPM
TPM
RPD
Charts
Gemini 2.5 Flash Native Audio Dialog
Live API	
0 / Unlimited
0 / 1M
0 / Unlimited
Gemini 3 Flash Live
Live API	
0 / Unlimited
0 / 65K
0 / Unlimited
Gemini 2.5 Pro
Text-out models	
0 / 0
0 / 0
0 / 0
Gemini 2 Flash
Text-out models	
0 / 0
0 / 0
0 / 0
Gemini 2 Flash Lite
Text-out models	
0 / 0
0 / 0
0 / 0
Gemini 2.5 Flash TTS
Multi-modal generative models	
0 / 3
0 / 10K
0 / 10
Gemini 2.5 Pro TTS
Multi-modal generative models	
0 / 0
0 / 0
0 / 0
Gemma 3 1B
Other models	
0 / 30
0 / 15K
0 / 14.4K
Gemma 3 4B
Other models	
0 / 30
0 / 15K
0 / 14.4K
Gemma 3 12B
Other models	
0 / 30
0 / 15K
0 / 14.4K
Gemma 3 27B
Other models	
0 / 30
0 / 15K
0 / 14.4K
Imagen 4 Generate
Multi-modal generative models	-	-	
0 / 25
Imagen 4 Ultra Generate
Multi-modal generative models	-	-	
0 / 25
Imagen 4 Fast Generate
Multi-modal generative models	-	-	
0 / 25
Gemma 3 2B
Other models	
0 / 30
0 / 15K
0 / 14.4K
Gemini Embedding 1
Other models	
0 / 100
0 / 30K
0 / 1K
Gemini 3.1 Pro
Text-out models	
0 / 0
0 / 0
0 / 0
Nano Banana (Gemini 2.5 Flash Preview Image)
Multi-modal generative models	
0 / 0
0 / 0
0 / 0
Gemini 3.1 Flash Lite
Text-out models	
0 / 15
0 / 250K
0 / 500
Nano Banana Pro (Gemini 3 Pro Image)
Multi-modal generative models	
0 / 0
0 / 0
0 / 0
Nano Banana 2 (Gemini 3.1 Flash Image)
Multi-modal generative models	
0 / 0
0 / 0
0 / 0
Lyria 3 Clip
Multi-modal generative models	
0 / 0
0 / 0
0 / 0
Lyria 3 Pro
Multi-modal generative models	
0 / 0
0 / 0
0 / 0
Veo 3 Generate
info
Multi-modal generative models	
0 / 0
-	
0 / 0
Veo 3 Fast Generate
info
Multi-modal generative models	
0 / 0
-	
0 / 0
Gemini Robotics ER 1.5 Preview
Other models	
0 / 10
0 / 250K
0 / 20
Computer Use Preview
Other models	
0 / 0
0 / 0
0 / 0
Gemini Embedding 2
Other models	
0 / 100
0 / 30K
0 / 1K
Deep Research Pro Preview
Agents	
0 / 0
0 / 0
0 / 0
Gemini 3 Flash
Text-out models	
1 / 5
555 / 250K
1 / 20
Gemini 2.5 Flash Lite
Text-out models	
2 / 10
97.18K / 250K
3 / 20
Gemini 2.5 Flash
Text-out models	
3 / 5
63.11K / 250K
43 / 20
Tools
Gemini 2.5 Flash
Map grounding	-	-	
0 / 500
Gemini 2.5 Pro
Map grounding	-	-	
0 / 0
Gemini 3 Flash
Map grounding	-	-	
0 / 0
Gemini 2.5 Flash Lite
Map grounding	-	-	
0 / 500
Gemini 3.1 Pro
Map grounding	-	-	
0 / 0
Gemini 3.1 Flash Lite
Map grounding	-	-	
0 / 500
Computer Use Preview
Map grounding	-	-	
0 / 500
Deep Research Pro Preview
Map grounding	-	-	
0 / 500
Gemini 2
Search grounding	-	-	
0 / 1.5K
Gemini 2.5
info
Search grounding	-	-	
0 / 1.5K
Gemini 3
info
Search grounding	-	-	
0 / 0
Default
info
Search grounding	-	-	
0 / 1.5K

For **video analysis** in Perplexity’s quota system, you should look under the **file‑upload / analysis category**, not under a dedicated “video” bucket.[^2_1][^2_2][^2_3][^2_4]

### Where to look in the UI

- **Category label**: In your screenshot, the closest analogue is the **“Text‑out models”** / **“Multi‑modal generative models”** section, but that’s actually for Gemini text‑generation calls.
- For **video uploads and analysis**, Perplexity treats video files as part of its **general file‑upload quota**, which is usually grouped with **document, image, and audio uploads** under Pro/Max file‑analysis limits rather than a separate “video” line.[^2_2][^2_3][^2_4][^2_1]


### Practical guidance

- If you want to know **how many video analyses you can run per day**, check:
    - Your **file‑upload quota** (Pro/Max “file uploads” or “file and photo uploads” in the plan docs).[^2_5][^2_1]
    - The **“file upload” help article** that lists supported formats; video analysis is currently done via **transcript / caption ingestion**, not visual‑scene indexing.[^2_3][^2_4]

If you paste the **exact quota table UI** you’re seeing (or a list of the category labels in that panel), I can tell you which *specific* row or section corresponds to video‑analysis‑like usage.
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://www.datastudios.org/post/perplexity-ai-free-versus-paid-features-explained-usage-limits-model-availability-speed-and-work

[^2_2]: https://www.datastudios.org/post/perplexity-ai-file-upload-and-reading-formats-limits-and-workflow-integration

[^2_3]: https://www.datastudios.org/post/perplexity-ai-file-uploading-and-reading-formats-limits-and-enterprise-options

[^2_4]: https://www.perplexity.ai/help-center/en/articles/10354807-file-uploads

[^2_5]: https://www.perplexity.ai/help-center/en/articles/11187416-which-perplexity-subscription-plan-is-right-for-you

[^2_6]: https://www.reddit.com/r/perplexity_ai/comments/1r1xg6i/notes_on_the_new_limits_for_perplexity_pro/

[^2_7]: https://docs.perplexity.ai/docs/admin/rate-limits-usage-tiers

[^2_8]: https://www.perplexity.ai/help-center/en/articles/11985060-generating-videos-with-perplexity

[^2_9]: https://www.umu.com/ask/q11122301573854241395

[^2_10]: https://dev.to/jovin_george_733dcfc16291/what-features-and-limits-define-perplexity-pro-video-creation-ee0

[^2_11]: https://www.glbgpt.com/hub/the-ultimate-guide-to-perplexity-ais-video-editing-capabilities/

[^2_12]: https://www.youtube.com/watch?v=oP-qVVnNGg0

[^2_13]: https://www.linkedin.com/posts/john-delahanty_is-anyone-else-seeing-this-with-perplexity-activity-7430350306623885312-PIgn

[^2_14]: https://www.reddit.com/r/perplexity_ai/comments/1cpd6fi/perplexity_pro_file_upload_what_is_for/

[^2_15]: https://www.datastudios.org/post/perplexity-ai-pricing-and-subscriptions-explained-free-access-versus-pro-plan-usage-ceilings-premi


---

# Wake up please. We're considering the Gemini models and I provided to you the AI Studio quota per day table.

You’re right; I was still in “Perplexity‑file‑analysis” context when you’re clearly asking about **Gemini via AI Studio / Vertex**, not Perplexity. Let’s refocus on your table.

***

### What to look for in your Gemini quota table

Given your AI Studio rate‑limit table and the fact you care about **video analysis**, you should look at:

- **Category: `Multi‑modal generative models`**
This is the bucket that contains models like:
    - `Gemini 2.5 Flash TTS` (audio‑/speech‑related)
    - `Imagen 4 Generate`, `Imagen 4 Ultra Generate`, `Imagen 4 Fast Generate`
    - `Nano Banana Pro` / `Nano Banana 2` (Gemini image‑based models)
    - `Lyria 3 Clip`, `Lyria 3 Pro` (audio‑generation)
    - `Veo 3 Generate`, `Veo 3 Fast Generate`

Among these, **Veo 3 Generate** and **Veo 3 Fast Generate** are Google’s **video‑generation models** (i.e., “video analysis” ≠ just invoke them, but if you’re building video‑centric workflows, this is the bucket you’ll hit).[^3_1][^3_2]

### What “video analysis” implies in Gemini terms

Gemini itself doesn’t yet expose a dedicated “video analysis only” API; instead, video‑related cap‑usage breaks down as:

- **Video generation** → `Veo 3 Generate` / `Veo 3 Fast Generate` (category: `Multi‑modal generative models`).
- **Video‑related multimodal analysis** (frames, subtitles, audio) → if you pass video frames or audio as inputs to other **multi‑modal** models (e.g., Gemini‑Vision‑style inputs), those calls fall under the **same `Multi‑modal generative models` quota RPD/RPM** as other image/audio‑aware models (e.g., `Nano Banana`, `Imagen`, etc.).[^3_2][^3_1]

So, to answer your question directly:

> **For video‑forward workflows (generation, and likely much video analysis), look at the `Multi‑modal generative models` category and the `Veo 3 Generate` / `Veo 3 Fast Generate` RPD + RPM/TPM limits in your AI Studio table.**

If you want, paste the **exact RPM/TPM/RPD values** you see for `Veo 3 Generate` and `Veo 3 Fast Generate` (and any other Veo‑family rows), and I can spell out concrete daily throughput numbers (e.g., max minutes or clips per day) for your target video length and configuration.

<div align="center">⁂</div>

[^3_1]: https://yingtu.ai/en/blog/google-gemini-api-free-tier-limits-2025

[^3_2]: https://docs.cloud.google.com/gemini/docs/quotas


---

# But we don't use VEO to analyze videos, we use Gemini.

You’re right to focus on **Gemini**, not Veo: Gemini can natively **analyze videos** (audio + visual frames) via its **multi‑modal “video understanding” capability**, and that shows up in the **same quota buckets as other multi‑modal / text‑out models**, not in Veo’s RPD lines.[^4_1][^4_2][^4_3]

***

### Which quota category applies to video analysis with Gemini

When you pass a video file to a Gemini model (e.g., `gemini‑3‑flash`, `gemini‑2.5‑pro`, etc.) for:

- summarizing video content
- answering questions about scenes/objects/speech
- captioning or segment analysis

… that usage is billed and rate‑limited **as a regular Gemini multi‑modal request**, i.e.:

- **Category: `Multi‑modal generative models`** if the model is explicitly listed that way (e.g., image‑ or audio‑aware variants).
- **Category: `Text‑out models`** if the model is labeled as a text‑out model but still accepts video‑with‑audio (e.g., Gemini 3 Flash, 3.1 Flash Lite, 2.5 Flash, etc.).[^4_3][^4_4][^4_5][^4_1]

In your table, that means:

- **Videos analyzed with `Gemini 2.5 Flash` / `Gemini 2.5 Flash Lite`** → **“Text‑out models”** RPD/RPM.
- **Videos analyzed with `Gemini 2.5 Flash TTS`‑style models** → **“Multi‑modal generative models”** RPD/RPM.[^4_2][^4_1][^4_3]

***

### How to interpret your current caps for video analysis

For your use case, treat:

- **Each video analysis request** as **one request (R: 1)** to a Gemini model that supports video input.
- **Quota ceilings** as:
    - `RPM` (requests per minute)
    - `RPD` (requests per day)
    - `TPM` (tokens per minute, which will spike with long videos at 1 FPS sampling).[^4_1][^4_3]

So to answer your question directly:

> For video analysis with **Gemini**, you should look at the **“Text‑out models”** and **“Multi‑modal generative models”** lines for your chosen Gemini model (e.g., `Gemini 2.5 Flash`, `Gemini 3 Flash`, `Gemini 2.5 Flash TTS`) and read their **RPM / TPM / RPD** values; **those are your video‑analysis limits**, not Veo’s.[^4_2][^4_3][^4_1]

If you share the **exact model name** you’re using for video analysis (e.g., `gemini‑2.5‑flash`, `gemini‑3‑flash‑preview`) and the **RPD/RPM/TPM** you see for it in your table, I can map out concrete daily throughput (e.g., max minutes of video per day at 1 FPS).
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://ai.google.dev/gemini-api/docs/video-understanding

[^4_2]: https://firebase.google.com/docs/ai-logic/analyze-video

[^4_3]: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding

[^4_4]: https://ai.google.dev/gemini-api/docs/rate-limits

[^4_5]: https://docs.cloud.google.com/gemini/docs/quotas

[^4_6]: https://developers.googleblog.com/en/gemini-2-5-video-understanding/

[^4_7]: https://gemini.google/overview/video-generation/

[^4_8]: https://prateeksha.com/blog/gemini-3-0-multimodal-projects-video-image-text

[^4_9]: https://www.facebook.com/0xSojalSec/posts/google-has-released-the-usage-limits-for-various-tiers-of-gemini-25free-5-prompt/1314649190189481/

[^4_10]: https://www.youtube.com/watch?v=6OhqVQ0lO1g

[^4_11]: https://www.youtube.com/watch?v=-kL6hUTd1eU

[^4_12]: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com

[^4_13]: https://www.instagram.com/popular/gemini-ai-multimodal-video-analysis/

[^4_14]: https://ai.google.dev/gemini-api/docs/video

[^4_15]: https://www.youtube.com/watch?v=dN8BPRK9Hzs

[^4_16]: https://www.reddit.com/r/Bard/comments/1lameh8/gemini_can_analyze_videos_now/

[^4_17]: https://cloud.google.com/video-intelligence


---

# ModelCategory

Gemini 2.5 Pro
Text‑out models
Gemini 2 Flash
Text‑out models
Gemini 2 Flash Lite
Text‑out models
Gemini 3.1 Pro
Text‑out models
Gemini 3.1 Flash Lite
Text‑out models
Gemini 3 Flash
Text‑out models
Gemini 2.5 Flash Lite
Text‑out models
Gemini 2.5 Flash
Text‑out models

Do these all share the same quota?  Or can I get more uses per day by switching models?

No, **those models do not all share the same quota bucket**, and you **can** get more “effective” usage per day by switching models—but the details depend on how Google has configured your project’s quotas.

### How quota buckets work

- Google typically groups Gemini models into **rate‑limit buckets by model family and tier**, not strictly by UI label like “Text‑out models”.
    - For example, `gemini‑2.5‑pro`, `gemini‑3.1‑pro`, and `gemini‑3‑flash` often live in **different quota buckets**, each with its own **RPM / TPM / RPD** ceilings.[^5_1][^5_2][^5_3]
- In your list, you have:
    - **Pro‑grade** models: `Gemini 2.5 Pro`, `Gemini 3.1 Pro`
    - **Flash‑grade** models: `Gemini 3 Flash`, `Gemini 3.1 Flash Lite`, `Gemini 2.5 Flash`, `Gemini 2.5 Flash Lite`, `Gemini 2 Flash`, `Gemini 2 Flash Lite`

These are usually **separate quota pools**, even though they all show “Text‑out models” in the console UI.[^5_3][^5_1]

***

### What this means for your video‑analysis throughput

- If your **Pro models** are capped at, say, **100 RPD** but your **Flash models** are at **20 RPD**, then:
    - You can **spread video‑analysis load across models** (e.g., use Flash for simpler summaries, Pro for deep QA) to get **more total requests per day** than any single model alone allows.
- However, the **TPM / RPM** values per model will still constrain how many concurrent streams or long‑context videos you can run on each one.[^5_4][^5_1][^5_3]


### Practical recommendation

- To maximize daily video‑analysis throughput:

1. **Check the exact RPD / RPM / TPM** for each model in your project (not just the UI label).
2. Route **lower‑complexity workloads** (short videos, simple summaries) to **Flash models** with higher RPD, and **heavy‑duty analysis** to **Pro models** with higher quality but often lower baseline RPD.
3. If you’re hitting caps, submit **quota‑increase requests per model** in the Cloud Console (each model has its own quota line).[^5_2][^5_3]

If you paste the **RPD/RPM/TPM numbers** for each of these models from your table, I can tell you which ones are the best “workhorses” for video analysis and how much total daily throughput you can expect.
<span style="display:none">[^5_10][^5_11][^5_12][^5_5][^5_6][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://ai.google.dev/gemini-api/docs/rate-limits

[^5_2]: https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/quota-and-pricing.md

[^5_3]: https://blog.laozhang.ai/en/posts/gemini-api-rate-limits-guide

[^5_4]: https://ai.google.dev/gemini-api/docs/video-understanding

[^5_5]: https://discuss.google.dev/t/vertex-ai-api-quotas-documentation-discrepancy/153267

[^5_6]: https://www.reddit.com/r/GeminiAI/comments/1r93luh/gemini_31_pro_finally_solves_the_output_limit/

[^5_7]: https://support.google.com/gemini/answer/16275805?hl=en

[^5_8]: https://discuss.ai.google.dev/t/gemini-3-1-pro-quota-refresh-still-1-week-cycle-baseline-depletes-too-fast/131688

[^5_9]: https://docsbot.ai/models/compare/gemini-2-5-flash/gemini-3-1-pro

[^5_10]: https://github.com/google-gemini/gemini-cli/issues/19887

[^5_11]: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning-prepare

[^5_12]: https://developers.google.com/gemini-code-assist/resources/quotas


---

# How can I do video analysis without the Gemini models for free?  I do have subscriptions for Shoots.ai, Minimax M2.7, and the GLM Coding Plan, if so. Perhaps those can do video analysis, YouTube analysis also.

You **can** do a lot of video / YouTube analysis without Gemini, but **you’ll need to fall back to transcripts + audio‑only analysis** and your own stack, because your current external models (Shoots, Minimax, GLM Coding Plan) are mostly **text‑only** today and not “native” video‑analysis APIs.[^6_1][^6_2][^6_3][^6_4]

Below are the main angles you can use **for free** with your subscriptions and other tools.

***

### 1. Free YouTube / video analysis via transcripts

Most practical “video analysis without Gemini” is **transcript‑based**:

- **Extract YouTube transcripts** (free tools):
    - `Noteey YouTube Note Taker` and similar services pull full transcripts from public YouTube URLs, then you copy/paste into any LLM.[^6_3][^6_4]
    - Libraries like `youtube-transcript-api` (Python) or scrapers can batch‑extract transcripts for entire channels/playlists.[^6_3]
- **Analyze contents with your existing LLMs**:
    - Feed the transcript to **Minimax M2.7**, **GLM‑based models**, or **any other text‑only API** you control and ask:
        - Summarize by minute or section.
        - Extract key points, sentiment, Q\&A, etc.
    - This is effectively **YouTube‑video analysis for free**, as long as the video has auto‑captions or a CC transcript.[^6_2][^6_4][^6_3]

***

### 2. What your current subscriptions can (and can’t) do

- **Shoots.ai**
    - Focuses on **AI‑driven video editing / creation** rather than pure video “analysis,” so you can’t count on a free quota‑rich video‑analysis API.[^6_1][^6_2]
- **Minimax M2.7**
    - An **autonomous‑coding / reasoning model**; there’s no public evidence it natively ingests **video files**; it’s **text‑only via API/chat**.
    - You can still use it on **video transcripts or logs**, but not as a direct video‑analysis API.[^6_5][^6_6]
- **GLM Coding Plan**
    - Designed for **code‑generation and coding‑assisted workflows**, not video; again, **no native video‑model**.
    - You can plug it into a pipeline that first **converts video → audio → text** (e.g., your own Whisper‑style ASR), then run GLM‑based analysis on the text.[^6_7][^6_8][^6_2]

So in short: **none of these give you free Gemini‑style video‑analysis**, but you can **build your own video‑analysis pipeline** upstream and then route it to them.

***

### 3. DIY “free” video‑analysis pipeline (no Gemini)

You can construct a **free or low‑cost video‑analysis stack** like this:

1. **Input**:
    - YouTube / MP4 file → extract:
        - **Audio** (e.g., `ffmpeg` or `pydub`).
        - **Frames** (e.g., sample 1 FPS or scene‑change frames).
2. **Transcripts \& structure** (free tier):
    - Run **speech‑to‑text** (e.g., Whisper‑based open‑source, Hugging Face models) on the audio to get a raw transcript.[^6_2]
    - Optionally run **scene / shot detection** (OpenCV, PySceneDetect) to segment the video.[^6_2]
3. **Semantic analysis with your existing LLMs**:
    - For each segment, send:
        - Transcript + timestamps to **Minimax M2.7** or **GLM** models for:
            - Summary
            - Q\&A
            - Topic tagging
    - This is **fully decoupled from Gemini** and works as long as your chosen LLMs allow enough free‑tier RPD/RPM.[^6_2]
4. **YouTube‑specific “free” UI‑tools**:
    - Services like **Noteey** and similar “YouTube Note Taker”‑style apps already wrap the transcript‑extraction + AI analysis loop and let you paste the result into *any* LLM (including Minimax/GLM).[^6_4][^6_3]

***

### 4. Practical next‑step recommendation

Given your stack:

- **For free YouTube analysis**:
    - Use **Noteey / similar tools** to pull transcripts → route the text to **Minimax M2.7** or **GLM** for summaries/Q\&A.
- **For custom video analysis** (local files, not just YouTube):
    - Build a small pipeline:
        - `video → audio/frames` → **ASR** → **structured text** → **Minimax/GLM** analysis.

If you tell me whether you care more about **YouTube‑only** or **arbitrary MP4s**, and your preferred language stack (Python, Node, etc.), I can sketch out a concrete, minimal‑code pipeline for you using only free‑tier components.
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://www.articsledge.com/post/ai-video-analysis

[^6_2]: https://mixpeek.com/blog/video-analysis-ai

[^6_3]: https://microlaunch.net/h/how-to-analyze-youtube-video-content-without-watching-the-full-videos

[^6_4]: https://www.noteey.com/blog/understand-youtube-video

[^6_5]: https://www.youtube.com/watch?v=nbFihbUOtxE

[^6_6]: https://www.minimax.io/news/minimax-m27-en

[^6_7]: https://www.youtube.com/watch?v=Z3bewF_um8E

[^6_8]: https://www.youtube.com/watch?v=JtpiNpIrJR0

[^6_9]: https://cloud.google.com/video-intelligence

[^6_10]: https://cloudinary.com/guides/ai/ai-based-video-analytics

[^6_11]: https://www.wavestore.com/post/ai-powered-video-analytics-stop-wasting-camera-footage

[^6_12]: https://topai.tools/s/youtube-video-analysis

[^6_13]: https://kanerika.com/blogs/ai-video-analysis/

[^6_14]: https://www.youtube.com/watch?v=WpcRm78KOvY

[^6_15]: https://scalelogicinc.com/blog/ai-powered-video-analysis/


---

# Chutes.ai has many models hosted.

Yes—**Chutes.ai** can be a very good fit for **free / low‑cost video (and YouTube) analysis**, once you structure it as a **multi‑model pipeline** rather than a single “Gemini‑style” call.[^7_1][^7_2][^7_3]

***

### What Chutes.ai gives you for video analysis

Chutes is essentially a serverless GPU layer where you **deploy and compose open‑source models** (image, audio, text, etc.).[^7_2][^7_3][^7_4]
For video analysis, you can:

- Use **speech‑recognition models** (e.g., Whisper‑style) to transcribe video audio.
- Use **image‑classification / object‑detection / OCR** models on sampled frames.
- Route the resulting text to **LLMs** (your own or hosted) for summaries, Q\&A, or tagging.

Their “Multi‑Model Analysis” example shows exactly this pattern:

- Chain `speech_recognition` + `audio_classification` + `image_captioning` + `visual_qa` under one unified API, making it perfect for **video‑to‑transcript‑to‑LLM analysis**.[^7_5][^7_1]

***

### How to do this without Gemini (and still free where possible)

You can now **replace Gemini video‑analysis** with a **Chutes‑based pipeline**:

1. **Split video → frames + audio**
    - Use `ffmpeg` or a similar tool to:
        - Extract audio (`.wav`).
        - Capture key frames (e.g., 1 FPS).
2. **Deploy / pick Chutes models**
    - Spin up a **speech‑recognition chute** (e.g., an open‑source Whisper‑compatible model) for transcripts.[^7_1][^7_5]
    - Optionally add a **frame‑analysis chute** (object‑detection / OCR) if you care about visual content.[^7_1]
3. **Send transcripts to your existing LLMs**
    - Feed the Chutes‑generated transcript into **Minimax M2.7** or **GLM‑based models** (which you already have via subscriptions) for **text‑only analysis** (summarization, topic‑tagging, Q\&A, etc.).[^7_6][^7_7][^7_8]
4. **YouTube‑specific pattern**
    - For YouTube, you can:
        - Download the video (or stream) → feed into the same Chutes pipeline.
        - Or extract the **YouTube transcript** (public API) and skip ASR, while still using Chutes for any extra image/audio analysis you want.[^7_9][^7_10]

***

### Practical “free” angle

- **Chutes itself** is **compute‑metered**, not per‑model‑API, so:
    - If you stay under **free‑tier GPU hours or credits**, your video‑analysis pipeline can be effectively **free** for moderate volumes.[^7_3][^7_4]
- Open‑source models (Whisper‑family, ViT‑based detectors, etc.) are **free to run**, so all costs are **GPU‑time**, not per‑request‑to‑Google‑like Gemini.[^7_11][^7_12]

If you tell me:

- whether you want **YouTube‑only** vs **arbitrary MP4s**,
- and your preferred stack (Python, FastAPI, PyTorch, etc.),

I can sketch a concrete Chutes‑based YouTube/video‑analysis microservice that you can plug into your existing Minimax/GLM subscriptions.
<span style="display:none">[^7_13][^7_14][^7_15][^7_16][^7_17][^7_18][^7_19][^7_20][^7_21][^7_22]</span>

<div align="center">⁂</div>

[^7_1]: https://chutes.ai/docs/examples/multi-model-analysis

[^7_2]: https://chutes.ai/docs/core-concepts/chutes

[^7_3]: https://chutes.ai

[^7_4]: https://chutes.ai/docs/help/faq

[^7_5]: https://chutes.ai/docs/examples

[^7_6]: https://www.youtube.com/watch?v=nbFihbUOtxE

[^7_7]: https://www.minimax.io/news/minimax-m27-en

[^7_8]: https://www.youtube.com/watch?v=JtpiNpIrJR0

[^7_9]: https://microlaunch.net/h/how-to-analyze-youtube-video-content-without-watching-the-full-videos

[^7_10]: https://www.noteey.com/blog/understand-youtube-video

[^7_11]: https://mixpeek.com/blog/video-analysis-ai

[^7_12]: https://kanerika.com/blogs/ai-video-analysis/

[^7_13]: https://chutes.ai/docs/examples/video-generation

[^7_14]: https://www.reddit.com/r/SillyTavernAI/comments/1o6b42h/chutess_alternative/

[^7_15]: https://chutes.ai/docs/examples/streaming-responses

[^7_16]: https://chutes.ai/docs/getting-started/quickstart

[^7_17]: https://www.youtube.com/watch?v=99eDzWDz7oU

[^7_18]: https://chutes.ai/docs/miner-resources/scoring

[^7_19]: https://chutes.ai/docs/guides/templates

[^7_20]: https://www.instagram.com/popular/chutes-ai-alternative/

[^7_21]: https://chutes.ai/docs/guides

[^7_22]: https://www.reddit.com/r/LocalLLM/comments/1nvt4yc/can_anyone_recommend_opensource_ai_models_for/


---

# I wanted to do the video analysis so that I could identify code that they show in the videos, as well as any graphical informational content that doesn't come across as text.

For your goal—**finding code on screen and non‑text graphics** in videos—Gemini‑style “video understanding” is just one way to get there; the more robust and free‑tier‑friendly path is a **frame‑based OCR + visual‑model pipeline** that you can run over batches or YouTube links.[^8_1][^8_2][^8_3][^8_4]

Below is a concrete architecture you can map to your existing stack (Chutes, Minimax, GLM, etc.).

***

### 1. What you’re really trying to do

You want to:

- **Detect code blocks** appearing in frames (e.g., IDEs, terminal windows, code slides).
- **Extract that code as text** (for copy‑paste / indexing).
- **Capture non‑text graphics** (charts, diagrams, UI flows) that don’t show up in transcripts.

This is:

- **Screen‑code OCR** + **visual‑feature extraction**, not just “video analysis.”

***

### 2. Effective free / low‑cost architecture

You can build this as a pipeline that runs on **PyTorch / Python + OCR + CLIP‑style models**, and then route outputs to your LLMs.[^8_2][^8_3][^8_4][^8_1]

#### 2.1. Frame sampling and segmentation

- Use **`ffmpeg` / `scenedetect`** to split video into:
    - Scenes or shots (optional, improves batching).[^8_2]
    - Then sample 1–2 FPS per shot into images.


#### 2.2. Code‑on‑screen detection and extraction

- **Tesseract OCR + code‑specialized post‑processor**:
    - Run OCR on every frame (or every 5–10th) using `Tesseract` or `EasyOCR`.[^8_3][^8_5]
    - Use a **code‑specific model** (e.g., `CodeT5‑OCRfix`) to repair and classify OCR’d snippets as real code vs. noise.[^8_4]
- **Optional**: train a small detector to find **IDE‑like windows** (monospace fonts, line numbers, etc.) and focus OCR there.

This gives you:

- Timestamps where code appears.
- Clean, copy‑paste‑ready code blocks.


#### 2.3. Non‑text graphical content (charts, diagrams, UI)

- Run **CLIP / SigLIP** on each frame or cropped regions to:
    - Extract embeddings for “visual semantics” (e.g., “histogram”, “flowchart”, “web UI”).[^8_2]
- Feed embeddings into a **vector DB** (e.g., Chroma, Pinecone) and add plain‑text captions like:
    - “This frame contains a bar chart comparing X vs Y.”
    - “This frame shows a web UI login flow.”

You can then:

- Search later by keywords (“bar chart”, “login flow”, “API diagram”).
- Pair with your LLMs for natural‑language descriptions.

***

### 3. How to plug this into your current stack

- **Chutes.ai** is a perfect fit for:
    - Hosting a **custom OCR + code‑fix chute** (Tesseract‑based + small transformer post‑processor).
    - Hosting a **visual‑embedding chute** (CLIP‑family model) that runs on sampled frames.[^8_6][^8_7][^8_8]
- **Minimax M2.7 / GLM** can then:
    - Summarize each video segment by:
        - Code snippets detected.
        - Visual semantics (from CLIP embeddings).
    - Tag content for later search (e.g., “Python web‑scraping example with Pandas bar chart”).

This is effectively **Gemini‑style video analysis without Gemini**, and you own the pipeline.

***

### 4. Concrete “starter” pattern you can implement

Given your preferences (Python, Node):

1. **In Python**:
    - Use `scenedetect` / `ffmpeg` + `EasyOCR` / `Tesseract` + `CLIP` to:
        - Sample frames.
        - Extract code + visual embeddings.
    - Save to a DB with `video_id`, `start_time`, `end_time`, `code_snippets`, `visual_tags`.[^8_3][^8_4][^8_2]
2. **In Chutes**:
    - Wrap the OCR + CLIP stage as a **Chutes service** so you can scale it across videos.[^8_7][^8_6]
3. **Then**:
    - Send structured JSON (video segment + code + visual tags) to **Minimax M2.7** or **GLM** for:
        - Segment‑level summaries.
        - Indexing hints (e.g., “relevant for backend API tutorials”).

If you tell me whether you want:

- A **YouTube‑only** pipeline (leverage their public transcript API), or
- A **generic MP4** pipeline that works on any recording, and your preferred stack (Python, Node, Docker, etc.),

I can give you a minimal code sketch (e.g., `scenedetect` + OCR + CLIP + Chutes + Minimax) that you can drop into your current infra.
<span style="display:none">[^8_10][^8_11][^8_12][^8_13][^8_14][^8_15][^8_16][^8_17][^8_18][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://screenapp.io/features/video-analyzer

[^8_2]: https://mixpeek.com/blog/video-analysis-ai

[^8_3]: https://dfir.science/2021/10/Using-video2ocr-to-extract-text-from-video.html

[^8_4]: https://www.computer.org/csdl/proceedings-article/ase/2023/299600b492/1SBGx4fRew0

[^8_5]: https://www.youtube.com/watch?v=EkSaIJTruTA

[^8_6]: https://chutes.ai/docs/examples/multi-model-analysis

[^8_7]: https://chutes.ai/docs/core-concepts/chutes

[^8_8]: https://chutes.ai

[^8_9]: https://www.youtube.com/watch?v=efVHE8jGxx8

[^8_10]: https://www.reddit.com/r/ChatGPTPro/comments/1i3qbog/looking_for_an_ai_tool_that_can_watch_video_and/

[^8_11]: https://www.maxqda.com/help/analyzing-videos/analyze-coded-videos

[^8_12]: https://www.linkedin.com/posts/abdul-mateen18_buildinpublic-problemsolving-softwareengineering-activity-7406013148488445952-vFhK

[^8_13]: https://azure.microsoft.com/en-us/products/ai-video-indexer

[^8_14]: https://www.youtube.com/watch?v=X6evUb01eEI

[^8_15]: https://www.youtube.com/watch?v=RvVLqXdhdVQ

[^8_16]: https://vatsalshah.in/tools/video-analyzer

[^8_17]: https://www.youtube.com/watch?v=Mgs3VVHWbqE

[^8_18]: https://mcpmarket.com/tools/skills/video-toolkit


---

# I want both "A YouTube‑only pipeline (leverage their public transcript API), or

A generic MP4 pipeline that works on any recording, and your preferred stack (Python, Node, Docker, etc.),"

You can support **both** a YouTube‑only and a generic MP4 pipeline with a shared core, and run almost all of it in **Python + Docker**, with **Chutes** for GPU‑heavy bits and **Minimax/GLM** for summarization and tagging.[^9_1][^9_2][^9_3][^9_4]

Below is a concrete architecture you can implement.

***

### 1. Shared core: “video‑to‑segments” module

Used by **both YouTube and MP4** pipelines.

- **Input**:
    - A video path (local MP4), **or** a YouTube URL.
- **Output**:
    - A JSON per segment:

```json
{
  "video_id": "yt_abc123 | mp4_hash",
  "start": 10.5, "end": 45.3,
  "transcript": "...",
  "code_snippets": ["...", "..."],
  "visual_tags": ["bar chart", "UML diagram", "terminal window"]
}
```

- **Technologies**:
    - Python (`cv2`, `scenedetect`, `pytesseract` / `EasyOCR`, `CLIP` / `SigLIP`).
    - Optional: FastAPI + Docker for orchestration.[^9_2][^9_3][^9_4]

You can package this as a **Docker service** and call it from anywhere.

***

### 2. YouTube‑only pipeline

Goal: **YouTube URL → transcript + code‑on‑screen + visuals**

#### 2.1. Transcript via YouTube

- Use `youtube‑transcript‑api` (Python) to fetch the transcript with timestamps.[^9_5][^9_1]
- Use the timestamps to **align segments** with your frame‑based code‑/visual‑analysis below.


#### 2.2. Code‑on‑screen + graphics from frames

- Download the video (or stream segments) via `yt‑dl` / `pytube` and then:
    - Run **scene detection** + frame sampling (1–2 FPS per scene).[^9_4][^9_6]
    - Run **OCR** (Tesseract/EasyOCR) on each frame, focusing on:
        - Terminal‑like regions (monospace, line numbers).
        - Editor‑like windows.[^9_7][^9_2]
    - Use a **small code‑classification model** (e.g., `CodeT5‑OCRfix`) to:
        - Filter out noise.
        - Group contiguous frames with the same code into one “code block” with timestamps.[^9_8]
- Run **CLIP‑style CLIP/SigLIP** on frames to get embeddings for:
    - Charts, diagrams, UI flows.[^9_3]

Then stitch:

- Transcript segments (from YouTube API) + code‑snippets + visual tags per time range.

***

### 3. Generic MP4 pipeline

Goal: **Any MP4 → same JSON schema as above**

This is almost identical, except:

- Input is a local file or HTTP stream.
- You **don’t** rely on YouTube transcript, but:
    - Optionally run **ASR** (e.g., Whisper‑family model) alongside OCR to get complete audio‑only context.[^9_9][^9_10]

The rest of the pipeline (scene‑based sampling, OCR, code‑extraction, CLIP‑based visual tags) is **the same** as the YouTube path.

***

### 4. Putting Chutes, Minimax, and GLM in the loop

- **Chutes**:
    - Host:
        - OCR + code‑fix chute (Tesseract + light transformer post‑processor).[^9_11][^9_12]
        - CLIP‑style visual‑embedding chute.
    - Your Python core calls Chutes over HTTP instead of running heavy models directly on your own GPU.[^9_13][^9_14]
- **Minimax M2.7 / GLM**:
    - Take the structured JSON per segment and run:
        - Summarization: “What code is shown and what is explained in this segment?”
        - Tagging: “relevant for backend API design”, “uses React UI”, “Pandas + matplotlib” etc.
    - You can batch process segments and store results in a DB or vector store for later search.[^9_15][^9_16][^9_17]

***

### 5. Concrete stack blueprint you can start from

- **Languages / frameworks**:
    - Core: **Python** (`ffmpeg` / `scenedetect`, `cv2`, `EasyOCR` / `pytesseract`, `transformers`, `CLIP`).[^9_6][^9_2][^9_3]
    - API layer: **FastAPI** (optional, but nice for async + Docker deployments).
    - Container: **Docker** (single image that wraps everything).
- **YouTube vs MP4 switches**:
    - Flag: `--source-type youtube | file`
    - If `youtube`:
        - Use `youtube‑transcript‑api` for transcript + timestamps.
    - If `file`:
        - Use Whisper‑style ASR or skip audio‑only if you’re fine with OCR + visuals.[^9_1][^9_9]

Would you like me next to sketch a minimal **FastAPI + Docker + Python** repo outline (e.g., folder structure, sample `Dockerfile`, and one Python module that does scene‑→OCR‑→Chutes‑→Minimax) tailored to your workflow?
<span style="display:none">[^9_18][^9_19][^9_20][^9_21][^9_22][^9_23][^9_24][^9_25]</span>

<div align="center">⁂</div>

[^9_1]: https://pypi.org/project/youtube-transcript-api/

[^9_2]: https://pyimagesearch.com/2022/03/07/ocring-video-streams/

[^9_3]: https://docs.vultr.com/public/doc-assets/pdfs/article/semantic-video-frame-search-using-openai-clip-and-vector-database.pdf

[^9_4]: https://subscription.packtpub.com/book/data/9781804610541/11/ch11lvl1sec62/extracting-frames-from-video-data-for-analysis

[^9_5]: https://developers.google.com/youtube/v3/docs

[^9_6]: https://www.datacamp.com/tutorial/optical-character-recognition-ocr-in-python-with-pytesseract

[^9_7]: https://stackoverflow.com/questions/52899174/real-time-ocr-in-python

[^9_8]: https://www.computer.org/csdl/proceedings-article/ase/2023/299600b492/1SBGx4fRew0

[^9_9]: https://mixpeek.com/blog/video-analysis-ai

[^9_10]: https://screenapp.io/features/video-analyzer

[^9_11]: https://chutes.ai/docs/examples/multi-model-analysis

[^9_12]: https://chutes.ai/docs/core-concepts/chutes

[^9_13]: https://chutes.ai

[^9_14]: https://chutes.ai/docs/help/faq

[^9_15]: https://www.youtube.com/watch?v=nbFihbUOtxE

[^9_16]: https://www.youtube.com/watch?v=JtpiNpIrJR0

[^9_17]: https://www.minimax.io/news/minimax-m27-en

[^9_18]: https://developers.google.com/youtube/v3/docs/captions

[^9_19]: https://stackoverflow.com/questions/14061195/how-to-get-transcript-in-youtube-api-v3

[^9_20]: https://www.reddit.com/r/Integromat/comments/1ei2n13/youtube_transcript/

[^9_21]: https://supadata.ai/youtube-transcript-api

[^9_22]: https://www.youtube.com/watch?v=wpSqsVHXGIA

[^9_23]: https://www.linkedin.com/posts/claytonharbour_automating-tutorial-video-production-with-activity-7418130699792039936-5xYR

[^9_24]: https://www.youtube-transcript.io/api

[^9_25]: https://n8n.io/workflows/3417-extract-and-clean-youtube-video-transcripts-with-rapidapi/


---

### Short answer

You **do not need to pre‑extract images to disk**. You **run OCR directly on video by reading the stream frame‑by‑frame in memory** and calling OCR on each frame.[^10_1][^10_2][^10_3][^10_4]

So:

- **It’s still “OCR on a sequence of frames”**, but done **on‑the‑fly**, not by saving images to disk first.
- You can implement this in plain **Python (no Docker)** using `OpenCV` + `pytesseract` (or `EasyOCR`).

***

### 1. How OCR on video actually works

Conceptually there are two steps:

1. **Read video frames** with `cv2.VideoCapture`:

```python
import cv2

cap = cv2.VideoCapture("video.mp4")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    # do OCR on `frame` here
cap.release()
```

This **does not** require you to first write `frame_0001.jpg`, `frame_0002.jpg`, etc., to disk.[^10_5][^10_1]
2. **Run OCR on each frame**:
    - Using `pytesseract`:

```python
import pytesseract

text = pytesseract.image_to_string(frame, config="--psm 6")
```

    - Or `EasyOCR`:

```python
import easyocr

reader = easyocr.Reader(["en"])
result = reader.readtext(frame)
```


Both work directly on the `frame` array from OpenCV, so you can stream the whole video through OCR in one pass.[^10_4][^10_1][^10_5]

***

### 2. Practical implications for your code‑detection use case

- **YouTube** URLs:

1. **Don’t** OCR the whole video blindly.
2. First, use `youtube‑transcript‑api` to get **timestamps**.[^10_6]
3. Then, seek to **interesting segments** (e.g., “code walkthrough”, “showing the implementation”):
        - Use `cv2.set(cv2.CAP_PROP_POS_MSEC, ms)` to jump to those times.
        - Run OCR **only on those segments**.[^10_1][^10_5]
- **Generic MP4**:
    - If you now have **no transcript**, you can:
        - Sample 1 FPS across the whole video, or
        - Use **scene‑change detection** to skip blank / talking‑head‑only scenes.[^10_7]
    - For each frame:
        - Optionally crop to regions where code usually appears (bottom‑right terminal, center IDE).
        - Run OCR, then cluster **similar‑looking code blocks** over time to reconstruct “snippets with timestamps”.[^10_3][^10_5]

In both cases, **you stay in pure Python** and **never write intermediate frames** unless you want to cache them.

***

### 3. What you should do next (without Docker)

If you want to **avoid Docker entirely** and keep everything local:

1. **Install**:
    - `ffmpeg` (for video decoding).
    - `opencv‑python` + `pytesseract` or `easyocr`.
    - `youtube‑transcript‑api` (for YouTube‑only path).[^10_8][^10_5][^10_6]
2. **Implement a single Python script** that:
    - Accepts `--source youtube URL` or `--source file path`.
    - For YouTube:
        - Uses `youtube‑transcript‑api` to get segments.
        - Seeks to those segments and runs OCR only there.[^10_6][^10_1]
    - For file:
        - Samples N FPS and runs OCR across all frames (or only frames where you detect an IDE/terminal‑like region).[^10_3][^10_5]

If you tell me your **preferred OCR choice** (`pytesseract` vs `EasyOCR`) and whether you want to **prioritize speed** (sample 1 FPS) or **accuracy** (more frames + region‑crops), I can give you a minimal runnable Python snippet that:

- Reads a YouTube URL or MP4,
- Spits out a JSON list of `{start, end, code_snippets, visual_tags}`.
<span style="display:none">[^10_10][^10_11][^10_12][^10_13][^10_14][^10_15][^10_16][^10_17][^10_18][^10_19][^10_9]</span>

<div align="center">⁂</div>

[^10_1]: https://stackoverflow.com/questions/42068293/real-time-ocr-with-opencv-and-pytesseract

[^10_2]: https://www.youtube.com/watch?v=Cpt-e-XuE7Q

[^10_3]: https://github.com/mhamzakhattak/video2text

[^10_4]: https://www.youtube.com/watch?v=xWy9SANXhIY

[^10_5]: https://pyimagesearch.com/2022/03/07/ocring-video-streams/

[^10_6]: https://pypi.org/project/youtube-transcript-api/

[^10_7]: https://subscription.packtpub.com/book/data/9781804610541/11/ch11lvl1sec62/extracting-frames-from-video-data-for-analysis

[^10_8]: https://www.datacamp.com/tutorial/optical-character-recognition-ocr-in-python-with-pytesseract

[^10_9]: https://www.reddit.com/r/computervision/comments/s7a28d/ocr_live_streaming/

[^10_10]: https://www.youtube.com/watch?v=7wWp2qtjhVc

[^10_11]: https://www.elektroda.com/rtvforum/topic4140155.html

[^10_12]: https://www.reddit.com/r/iphone/comments/144xmz/scrub_through_a_video_frame_by_frame_to_take_a/

[^10_13]: https://www.reddit.com/r/software/comments/1p5k7fm/extract_text_ocr_from_video/

[^10_14]: https://screenapp.io/features/video-to-text

[^10_15]: https://www.youtube.com/watch?v=3spOsIrOm0c

[^10_16]: https://www.veed.io/tools/video-to-text

[^10_17]: https://evernote.com/ai-transcribe/video-to-text

[^10_18]: https://textractify.com

[^10_19]: https://flixier.com/tools/video-to-text


---

# Well, accuracy, because if we're identifying words, that's important, or graphs.

For accuracy on **words and graphs**, you want:

- **Higher frame sampling** (not just 1 FPS) in key segments,
- **Region‑based OCR** (focus on IDE/terminal / chart areas), and
- **CLIP‑style embeddings** for non‑text graphics.

You can do all of this **in plain Python, no Docker**.

***

### 1. Frame sampling strategy (for accuracy)

Instead of a fixed 1–2 FPS:

- **YouTube**:
    - Use `youtube‑transcript‑api` to get **interesting segments** (e.g., “code walkthrough”, “explain the chart”).[^11_1]
    - Inside those segments, sample **3–5 FPS** (or even continuous per‑frame) for OCR.[^11_2][^11_3]
- **Generic MP4**:
    - If you have no transcript, at least run **scene‑change detection** to avoid uniform‑background / talking‑head zones.[^11_3]
    - In “content‑rich” scenes, sample **3–5 FPS**; in “boring” scenes, throttle down.

This keeps accuracy high without wasting too much compute on blank frames.[^11_4][^11_2]

***

### 2. Region‑based OCR for code

OCR accuracy is terrible if you run it on whole frames; you need **bounded regions** likely to contain code.

- Use **rectangle heuristics** (e.g., monospace font area):
    - Look for regions with:
        - High edge density.
        - Text‑like layout (horizontal lines, gutters).[^11_5][^11_2]
- Or simply **fix a Region of Interest (ROI)**:
    - Example: IDE usually sits in the center, terminal at the bottom‑right.
    - Crop `frame[y1:y2, x1:x2]` before OCR:

```python
roi = frame[y1:y2, x1:x2]
text = pytesseract.image_to_string(roi, config="--psm 6")
```

    - You can run multiple ROIs per frame (IDE, terminal, side‑panel).[^11_6][^11_2]

Then cluster similar OCR outputs over time into clean “code blocks with timestamps.”[^11_2][^11_4]

***

### 3. Graphs / non‑text visuals

For **charts, diagrams, UI flows** that don’t show up as text:

- Run a **CLIP‑style model** (e.g., `openai‑clip` / `SigLIP`) on frames or cropped regions.[^11_7][^11_8]
- Get embeddings and then either:
    - Store them in a vector DB, or
    - Run a lightweight **classifier** on embeddings to tag frames as:
        - `"bar chart"`, `"flowchart"`, `"terminal window"`, `"web UI"`, etc.[^11_9][^11_7]

This gives you **semantic tags for non‑text content** alongside the OCR‑extracted words.

***

### 4. Concrete next step: minimal Python snippet

If you want, I can give you a **minimal Python script** (no Docker, just `pip install`‑able packages) that:

- Accepts `video_path` or `youtube_url` and:
    - Extracts **transcript** (for YouTube),
    - Samples **3–5 FPS inside interesting segments**,
    - Runs **region‑based OCR** for code,
    - Runs **CLIP‑style embeddings** for graphs/UI,
    - Outputs a JSON list:

```json
[
  {
    "start": 10.5,
    "end": 45.3,
    "transcript": "...",
    "code_snippets": ["...", "..."],
    "visual_tags": ["bar chart", "terminal window"]
  }
]
```


Would you like me to write that snippet now, and if so, do you prefer:

- **`pytesseract`** or **`EasyOCR`** for OCR, and
- **`openai‑clip`** or another open‑source CLIP‑style model for graphics?

<div align="center">⁂</div>

[^11_1]: https://pypi.org/project/youtube-transcript-api/

[^11_2]: https://pyimagesearch.com/2022/03/07/ocring-video-streams/

[^11_3]: https://subscription.packtpub.com/book/data/9781804610541/11/ch11lvl1sec62/extracting-frames-from-video-data-for-analysis

[^11_4]: https://github.com/mhamzakhattak/video2text

[^11_5]: https://www.youtube.com/watch?v=Cpt-e-XuE7Q

[^11_6]: https://stackoverflow.com/questions/42068293/real-time-ocr-with-opencv-and-pytesseract

[^11_7]: https://docs.vultr.com/public/doc-assets/pdfs/article/semantic-video-frame-search-using-openai-clip-and-vector-database.pdf

[^11_8]: https://mixpeek.com/blog/video-analysis-ai

[^11_9]: https://screenapp.io/features/video-analyzer


---

# Are there repos that do this? Are there repos that use GLM or Minimax?

Yes: there are **existing repos that do video‑to‑OCR / code‑analysis**, but **very few** that are built around **GLM or Minimax** specifically. You can borrow **video‑OCR pipelines** and then plug GLM/Minimax into them as a downstream LLM layer.

***

### 1. Repos that do video‑to‑OCR / code analysis

These are close to what you want for **code‑on‑screen recovery**:

- **`video‑db/ocr‑benchmark`**
    - Benchmark framework that:
        - Extracts scenes from videos.
        - Runs OCR on frames from multiple models.
        - Exports JSON with video ID, scene times, and OCR text.[^12_1]
    - **Good as a template** for “video → scenes → OCR → structured text.”
- **`timminator/VideOCR`**
    - Extracts burned‑in subtitles / on‑screen text from videos.
    - Supports:
        - Multiple OCR zones (e.g., title bar, subtitle area).
        - Skipping frames, dual‑mode zones, GPU‑accelerated OCR.[^12_2]
    - Easily modifiable to target **IDE / terminal regions** and output code snippets.
- **`YerbaPage/CodeOCR`**
    - Implements “Seeing is Coding: Vision‑Language Models in Code Understanding.”
    - Focuses on **recognizing code in images** and closing the gap vs. humans.[^12_3]
    - Not directly video‑based, but you can wrap it in a `cv2.VideoCapture` loop.

You can use any of these as a **core OCR stage** and then add your own **GLM / Minimax** summarization / tagging on top.

***

### 2. Repos that use GLM or Minimax

There are **no major public repos that combine video‑OCR with GLM or Minimax** end‑to‑end, but there are:

- **GLM‑focused tooling** (not video‑analysis, but similar pattern):
    - GLM‑based agents that analyze **documents, code, or logs** (e.g., GLM‑driven coding agents and “build anything” demos), which you can adapt to your JSON‑structured video segments.[^12_4][^12_5]
- **Minimax‑based agents**:
    - Projects that wrap `minimax‑m2.7` as an agent for:
        - PR review,
        - log analysis,
        - general code‑understanding tasks.[^12_6][^12_7]

You can:

1. Take one of the **video‑OCR repos** above.
2. Add a **GLM or Minimax client** that consumes:
    - `video_id`, `start`, `end`, `transcript`, `code_snippets`, `visual_tags`.
3. Use GLM / Minimax for:
    - Summarizing each segment.
    - Tagging for search (e.g., “React + TypeScript”, “Pandas plotting”).

***

### 3. Practical recommendation for you

Given your goals:

- **Use `timminator/VideOCR` or `video‑db/ocr‑benchmark`** as the **video‑→OCR backbone** (no Docker required; both are Python + `PaddleOCR` / Tesseract).[^12_1][^12_2]
- **Add a GLM / Minimax stage**:
    - For every segment with OCR‑extracted text, serialize to JSON and send to:
        - `GLM Coding Plan` (for code‑centric reasoning).
        - `Minimax M2.7` (for system‑level reasoning / tagging).[^12_5][^12_6]

If you want, I can give you a minimal **`git clone + patch`** recipe that:

- installs one of these repos,
- extends it with a `analyze_with_glm.py` / `analyze_with_minimax.py` module,
- and outputs your target `{code_snippets, visual_tags, summaries}` JSON.
<span style="display:none">[^12_10][^12_11][^12_12][^12_13][^12_14][^12_15][^12_16][^12_8][^12_9]</span>

<div align="center">⁂</div>

[^12_1]: https://github.com/video-db/ocr-benchmark/blob/main/README.md

[^12_2]: https://github.com/timminator/VideOCR

[^12_3]: https://github.com/YerbaPage/CodeOCR

[^12_4]: https://www.youtube.com/watch?v=VsjVjz5hL0o

[^12_5]: https://firebase.google.com/docs/ai-logic/analyze-video

[^12_6]: https://www.minimax.io/news/minimax-m27-en

[^12_7]: https://apidog.com/blog/how-to-use-minimax-m2-7-free/

[^12_8]: https://github.com/levintech/ocr-realtime-recognition

[^12_9]: https://github.com/JoseMariaTS/VidOCR

[^12_10]: https://github.com/codewithjaspreet/yt-analyzer

[^12_11]: https://www.linkedin.com/posts/sakshi-jadhav-7446a62b9_github-jadhavsakshi7887textextraction-from-image-activity-7266182151904153600-S8cR

[^12_12]: https://www.youtube.com/watch?v=6mKiCxnyT-E

[^12_13]: https://github.com/datalab-to/surya

[^12_14]: https://github.com/MortezaEmadi/YouTube-Channel-and-Video-Performance-Analysis-using-Google-API-and-Stacking-Ensemble-Classifier

[^12_15]: https://github.com/ksm26/video-analysis-agent

[^12_16]: https://github.com/abhijeetk597/medical-data-extraction

