---
title: "I thought with the pro subscription to perplexity, that I had $5 in api credits per month for api searching."
date: "2026-03-10"
mode: "COPILOT"
uuid: "2739b532-0770-475e-a08a-fd8228aa63cb"
entry_count: 28
---

## Human

I thought with the pro subscription to perplexity, that I had $5 in api credits per month for api searching.

## Assistant

You don’t currently get a bundled “$5/month in API credits” with a Perplexity Pro subscription; API credits are a separate, pay‑as‑you‑go thing from your Pro plan.[1][2]

### How API and Pro relate

- API usage is billed via API credits you buy under the **API** tab; this does not require Pro and is not included in Pro pricing.[3][1]
- The help docs explicitly say that API access is “available as a separate service” and that the API product has **no complimentary API credits** included with subscriptions.[2][1]
- Pro’s “credits” are about Pro searches / advanced models inside the app, and are separate from API billing. They do not convert into API balance.[4][2]

### Where the $5 figure shows up

- In the newer “credits” system for features like Computer, Perplexity notes that an auto‑refill threshold of **500 credits is about $5 of usage** under current pricing.[5]
- That $5 example is about how auto‑refill works for in‑product credits, not a monthly free API allotment.[5]

If you tell me whether you’re mainly trying to use the Perplexity API in your own code or just wondering about in‑app credits for things like Computer/Deep Research, I can walk through exactly where to check your balances and what each counter means in your account.

## Human

trying to use the Perplexity API in your own code

## Assistant

To use the Perplexity API from your own code, you need to buy separate API credits and generate an API key; Pro doesn’t include a monthly $5 API balance.[1][2][3]

### 1. Set up billing and credits

- Go to perplexity.ai in a browser, open **Settings → </> API**.[2]
- Add a payment method there if you haven’t already.[1]
- In the same **API** tab, click **Buy** to purchase API credits (pay‑as‑you‑go); you can optionally enable **Automatic Top Up** when your balance drops below a few dollars.[2][1]

### 2. Generate an API key

- Still in **Settings → </> API**, click **Generate API Key**.[2]
- Copy the key and store it securely (env var, secret manager, etc.); you’ll use it as a Bearer token in your HTTP calls.[2]

### 3. Basic usage pattern in code

Here’s the minimal HTTP shape (pseudo-TS/JS):

```ts
const resp = await fetch("https://api.perplexity.ai/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.PERPLEXITY_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "llama-3.1-sonar-large-128k-online",
    messages: [{ role: "user", content: "Hello from the API" }],
  }),
});
const json = await resp.json();
console.log(json);
```

API consumption then burns down your purchased API credits; this is completely separate from your in‑app Pro credits.[3][1]

Do you want a concrete example for a specific stack (Python requests, Node/TS with fetch/axios, or something else)?  

## Human

did it used to have $5 per month for free use?

## Assistant

Yes, Perplexity has announced and documented a **recurring $5/month pplx-api credit for Pro users**, and this is described as an ongoing Pro benefit rather than just historical.[1][2]

### Where this $5/month is described

- The Perplexity API FAQ explicitly answers: as a Perplexity Pro subscriber, you “receive $5 in monthly credits on the first day of each month,” and new subscribers should wait 10–20 minutes for the credits to appear after subscribing.[1]
- The “Introducing PPLX Online LLMs” blog post states that **Pro users will receive a recurring $5 monthly pplx-api credit**, with other users billed purely usage-based.[2]

### Why it may not be obvious in your account

- The main API billing help page focuses on pay‑as‑you‑go purchase and auto‑top‑up, and does not restate the Pro $5 benefit, which makes it easy to miss.[3]
- Credits can also be affected by region, promotions, or rollout timing, and Perplexity notes that credit-related benefits may vary and can change over time.[4][1]

If you want, I can walk you through exactly where to look in the UI (balance number and logs) so you can confirm whether your $5 monthly credit is being applied to your specific account.

## Human

yes please

## Assistant

Here’s how to check whether your monthly pplx-api credit (including the $5 Pro perk) is actually showing up in your account.[1][2][3]

### 1. Open the API tab

- In a desktop browser, go to perplexity.ai and log in.  
- Click your avatar → **Settings → </> API**.[2][4]
- At the top of this page, you should see your **API credit balance** in dollars; this number reflects purchased credits, bonus credits, and any recurring monthly credits (like the Pro $5) as a single balance.[1][2]

### 2. Check balance changes around your billing date

- Note your Pro billing date (from **Settings → Account → Subscription**), then look at your API balance **just before** and **just after** that monthly date.  
- If the $5 monthly API credit is applied, you’ll see your balance increase by about $5 on that day without a corresponding card charge in your bank history.[3][1]

### 3. Check detailed credit/usage logs

Right now the most detailed breakdown UI is for in‑product “Credits,” but the pattern is similar for API:

- For in‑product credits, the help center points you to **perplexity.ai/account/usage** to see “Plan, Bonus, Purchased” balances and per‑thread usage.[5]
- For the API specifically, the **</> API** tab is where you “view and add credits, generate keys, and monitor usage patterns,” including how your dollar balance changes over time.[4][2]

If you tell me your Pro billing date and roughly what your API balance is today, I can suggest exactly what change you should expect to see when your next $5 credit lands (and what to look for to confirm it’s working).

## Human

image.jpg

## Assistant

You’re definitely on Perplexity Pro (annual, next billed March 9, 2027), but that screen is only your **subscription billing**, not the API credit view.[1]

### What your screenshot shows

- It confirms: Perplexity Pro at CAD 210/year, billed March 9, 2026, next billing March 9, 2027.[1]
- It also lists separate small invoices for **Chat Completions API** usage on Dec 31, Jan 31, and Feb 28, each for $0.00, which means your API usage so far has been covered by existing API credit balance (purchased and/or promotional).[2][1]

### Where to check the $5 API credit itself

To see whether the recurring $5 pplx‑api credit is being applied, you need the **API** page, not the subscription page:

1. In a desktop browser, open perplexity.ai and log in.  
2. Click your avatar → **Settings → </> API**.[3]
3. At the top of that page, look for the **API balance** (a dollar amount) and note:  
   - The current balance.  
   - Whether you see a **credit increase of about $5** dated on or just after March 9, 2026 (your Pro renewal date).[4][1]

If you open that **</> API** page and tell me:  
- What dollar balance you see, and  
- Whether there’s a transaction or jump of around $5 after March 9,  

I can help interpret exactly how much of that is from the Pro $5 vs. anything you may have purchased manually.

## Human

image.jpg

## Assistant

You’re at **$0 remaining** API credit and I don’t see any sign of a $5 recurring pplx‑api credit being applied to your account.[1]

### What your API page shows

- Top of the page: **Credit balance – $0 remaining**, with “Buy more credits,” “Payment method,” and “Auto reload: Disabled.”[1]
- Usage section: Only 5 `sonar-pro (ZpT0)` requests in the last 30 days, totaling about **$0.07** in cost.[1]
- Invoice history:  
  - 2026‑03‑09 – Perplexity Pro – **$210.00** (your annual sub renewal).  
  - 2026‑03‑01, 2026‑02‑01, 2026‑01‑01 – **$0.00** each for API usage (no charges, but also no credit top‑ups shown).[1]

Given this, your account is **not currently showing** an automatic $5 monthly API credit after the March 9 renewal, even though the FAQ/blog talk about that benefit.[2][3][1]

### What I’d recommend next

- Take a screenshot of this **Credit balance: $0 remaining** view plus your Pro subscription page (which you already have).  
- Contact Perplexity support via the in‑app “Help & Support” or the help center and say something like:  
  - You are a Pro annual subscriber (renewed March 9, 2026).  
  - The API FAQ states Pro users receive $5/month pplx‑api credit, but your **API balance shows $0** and the invoice history shows no credit being applied.  
- Ask them to (a) confirm whether the $5/month API credit is active for your region and plan, and (b) manually apply or fix it if it should be.  

Until support clarifies, assume that **any API usage will be billed from purchased credits only**, so you may want to either avoid heavy testing or buy a small credit pack and keep auto‑reload off so you stay in control.[4][5]

Do you want help drafting a short message you can paste to support that references these screenshots and the specific FAQ language about the $5 credit?  

## Human

yes please

## Assistant

Here’s a concise note you can send to Perplexity support; you can copy‑paste and tweak the details as needed:

***

Hi Perplexity support,

I’m a Perplexity Pro subscriber on the annual plan. My latest renewal was on March 9, 2026, for CAD $210 (see subscription billing page and invoice). My understanding from the pplx‑api FAQ / documentation is that Perplexity Pro users receive **$5 in pplx‑api credits each month**, applied on the first day of the month or shortly after subscribing/renewing.[1][2]

However, when I go to **Settings → </> API**, my **Credit balance shows $0 remaining**, Auto reload is disabled, and there is no sign of any $5 credit being added around my renewal date. My invoice history for the API also shows $0.00 invoices on 2026‑01‑01, 2026‑02‑01, and 2026‑03‑01, but none of these look like a recurring $5 credit being applied.[3][4]

Could you please:
1. Confirm whether the **$5/month pplx‑api credit** should apply to my Pro plan and region, and  
2. If it should, check why it has not been applied and correct my balance going forward (and retroactively if appropriate)?

I’ve attached screenshots of:
- My Pro subscription billing page showing the March 9, 2026 renewal, and  
- My API “Credit balance” and usage page showing $0 remaining credit.

Thank you!

***

If you’d like, tell me which email or in‑app form you’re using (and your preferred level of formality), and I can shorten or adjust this text to match your style.

## Human

"Hey there!
Thanks for reaching out about API credits.
The monthly API credit grant for Pro users was a time-limited benefit that has been discontinued as of 2/12.
Your Pro subscription benefits remain fully active, including:
10x citations per answer for greater reference depth and transparency.
Extended access to Perplexity Research for deeper explorations.
Enhanced image generation
You can learn more about all Pro benefits here: [What is Perplexity Pro](https://www.perplexity.ai/help-center/en/articles/10352901-what-is-perplexity-pro)
API access is available separately through our API pricing plans. Here are some helpful resources:
[Getting Started](https://docs.perplexity.ai/docs/getting-started/overview)
[API Pricing](https://docs.perplexity.ai/docs/getting-started/pricing#pricing)
Let me know if you have any other questions!
Regards,
Sam
AI Support agent for Perplexity"

## Assistant

That reply from Sam means the **$5/month pplx‑api credit for Pro users was a temporary promotion and is now ended**, as of February 12 (no longer an active benefit).[1][2]

### What this changes for you

- Your current Pro benefits now match the public “What is Perplexity Pro?” page: more citations, extended Research, image/video generation, Labs, etc., but **no recurring API credits**.[3][1]
- API usage is now entirely **pay‑as‑you‑go** via the separate API pricing; you’ll need to top up credits in the API settings page if you want to keep calling the API.[2]

### Practical implication

- Any API calls you make from your own code will draw down only from credits you explicitly purchase (or any one‑off bonus they might grant), and you should no longer expect a monthly $5 top‑up tied to your Pro renewal date.[4][2]

If you’d like, I can help you estimate how much API credit you actually need per month given your expected request volume and models.

## Human

why didn't you know that about the pro subscription?

## Assistant

Because my information about features relies on what’s in the current docs and articles I search, and those hadn’t fully caught up to that change yet, I inferred the older “$5/month” behavior from the FAQ and blog instead of the updated support clarification.[1][2]

The $5 pplx‑api credit started as a documented Pro benefit, and some materials still mention it, so without the direct support message you received, it looked like it was still active rather than time‑limited and discontinued on Feb 12.[3][1]

If something like this changes again, the safest move is always to cross‑check the live help articles plus any direct messages from support, since those will override older docs that might still be indexed.

## Human

how can we update your default prompt so that we don't have this issue again?

## Assistant

You can’t directly edit my “default prompt,” but you *can* shape how I behave with you by adding your own standing instructions and habits around verification.

### What you can configure

- In Perplexity’s settings, you can add **custom instructions** (how you want answers given, what to prioritize, what to always double‑check). These persist across chats and act like a mini‑system prompt for me when talking with you.[1]
- You can explicitly say things like: “When talking about Perplexity pricing, Pro benefits, or credits, always cross‑check against the latest help center and prefer support statements over older blog posts.”  

### A concrete instruction you could add

You might paste something like this into your custom instructions:

> For anything about Perplexity plans, credits, or API pricing, always:  
> 1) prioritize the latest Help Center articles over blogs or FAQs that may be stale,  
> 2) treat direct support statements as the ground truth if I paste them, and  
> 3) clearly flag if different sources conflict instead of assuming the older benefit still applies.

That doesn’t literally rewrite my global system prompt, but it reliably biases my behavior in this account so we avoid exactly the kind of stale‑benefit confusion we just hit.

Would you like me to draft a full set of custom instructions tailored to how you work (AI‑assisted dev, cost awareness, verification, etc.) that you can paste into Perplexity’s settings?

## Human

yes please

## Assistant

Here’s a detailed set of custom instructions you can paste into Perplexity (Profile → Settings → Custom instructions / personality) to reduce this kind of issue:

***

**Custom instructions for my assistant**

1. **Overall role and style**

- I am an advanced software developer and AI power‑user.  
- Prioritize accuracy, verification, and explicit uncertainty over fluency.  
- When sources conflict, tell me clearly instead of silently choosing one.  

2. **When answering about Perplexity itself (plans, pricing, credits, API)**

- Treat Perplexity’s **Help Center articles and pricing docs as the primary source of truth**, and assume older blog posts or marketing pages may be stale.[1][2]
- If I paste or quote a message from **Perplexity Support**, treat that support message as overriding any conflicting docs unless it is clearly outdated or contradicted by a newer help‑center article.  
- For topics like:  
  - Pro/Enterprise benefits  
  - Credits (in‑product vs pplx‑api)  
  - API pricing and limits  
  always:  
  1) search for the latest relevant help‑center articles,  
  2) check dates and wording for time‑limited promotions,  
  3) explicitly tell me if any sources disagree and what the most up‑to‑date interpretation likely is.  

3. **Handling promotions and time‑limited benefits**

- Never assume that a promotional benefit (like monthly free API credit) still applies just because it appears in a blog or FAQ.  
- If a benefit might be promotional or time‑limited, explicitly say:  
  - what document you’re relying on,  
  - whether it mentions dates or “limited‑time” wording, and  
  - that I should confirm in my own billing/credits UI or with support before relying on it.  

4. **Verification behavior**

- When discussing **money, quotas, or irreversible actions**, add a short “Verification” sentence like:  
  - “Please double‑check this in your current Perplexity settings/billing UI, because details can change.”  
- If you are not fully confident (e.g., conflicting or sparse docs), say “I’m not fully certain because X” and offer 1–2 concrete checks I can perform.  

5. **Technical and coding questions**

- Assume I’m comfortable with code, APIs, and reading docs.  
- Favor concise, information‑dense answers over hand‑holding explanations.  
- Prefer TypeScript/Node or Python for concrete examples unless I specify otherwise.  

6. **Formatting preferences**

- Use clear headings, short sections, and inline citations.  
- Be explicit about assumptions and edge cases, even if that adds one extra sentence.

***

If you’d like, I can also help you turn this into a reusable **Shortcut** or **Space instruction** for any “Perplexity billing / API” workspace so that those threads always inherit this behavior.[3][4]

## Human

can we generalize the perplexity specific portion?  I'm sure there's a principle we can use instead.

## Assistant

Yes. The general principle is: **treat product‑local docs and live account state as higher‑priority, and treat marketing/blog content as potentially stale, especially for pricing/quotas/benefits.**  

Here’s a generalized version you can drop into your instructions:

***

**General product/pricing reliability rules**

- When answering about any product’s **plans, pricing, limits, credits, or quotas**, prioritize:  
  1) the latest official documentation or help‑center articles, and  
  2) the user’s own current account/billing UI or direct support messages,  
  over blogs, announcements, or third‑party posts.[1][2]

- Treat blog posts, marketing pages, and older FAQs as **advisory only**. If they describe a benefit that could be promotional (e.g., monthly credits, free tiers, special limits), explicitly flag it as “this might have changed” and suggest the checks the user should run in their account UI.  

- When sources conflict about pricing/benefits/quotas, do not silently pick one. Instead:  
  - State that the sources conflict and what each says.  
  - Prefer the newest, most official doc, or the user’s support message/account view.  
  - Recommend a concrete verification step (e.g., “check your billing page for X field,” “confirm with support before relying on this”).  

- For anything that involves **money or resource consumption** (credits, limits, auto‑reload, overage behavior), always add a short verification note reminding the user that details can change and should be confirmed in their live account or official docs.

***

Do you want to narrow this further for “AI tools I use regularly” (Perplexity, Claude, OpenAI, etc.) so we encode that I should always assume their pricing pages can change without notice?

## Human

That still feels very symptomatic.  What about an instruction that says use the latest info?

## Assistant

You’re right that we can encode a deeper principle. The key is: **always reason about source freshness and authority, and prefer the latest, most authoritative source when they conflict.**  

Here’s a compact instruction that captures that, without being Perplexity‑specific:

***

**Use the latest, most authoritative info**

- When you rely on external information (docs, pricing, limits, features, policies, news), always:  
  1) Prefer **the most recently updated, primary source** (official docs, help center, spec, law, or the user’s live UI) over older or secondary sources (blogs, marketing pages, third‑party posts).  
  2) If sources conflict or may be outdated, explicitly say so, explain which one appears **newer / more authoritative**, and base your answer on that source rather than averaging them.  
  3) For anything involving **money, quotas, or account‑level behavior**, add a brief note that details can change and should be confirmed against the user’s current product UI or official docs.  

***

That pushes me to treat “use the latest info” as a default epistemic rule, instead of patching one product at a time.  

Would you like a second version that is even shorter (2–3 lines) so it fits cleanly into a general “How should the assistant reason?” field?

## Human

"For anything involving money, quotas, or account‑level behavior, add a brief note that details can change and should be confirmed against the user’s current product UI or official docs.", we can leave this out.  Show me the optimal prompt I shoudl use.

## Assistant

Here’s an optimized version without the money/quotas clause:

***

**Use the latest, most authoritative info**

When you rely on external information (docs, features, policies, news), always:  
1) Prefer the **most recently updated, primary source** (official docs, help center, spec, law, or my live UI) over older or secondary sources (blogs, marketing pages, third‑party posts).  
2) If sources conflict or might be outdated, explicitly say so, explain which one appears **newer / more authoritative**, and base your answer on that source rather than averaging them.

***

If you want, I can now compress this into a 1–2 sentence variant for a very small “reasoning style” field.

## Human

sure

## Assistant

Here’s a tight 2‑sentence version you can drop straight into your instructions:

> When you use external information (docs, pricing, features, policies, news), always favor the **newest, most authoritative primary sources** (official docs, help centers, specs, laws, my live account UI) over older or secondary sources like blogs or marketing pages.[1][2]
> If sources conflict or may be outdated, say so explicitly, explain which one appears more recent/authoritative, and base your answer on that source instead of averaging them.  

If you want, we can now wrap this together with your other preferences (concise, technical, TS/Python bias) into a single all‑purpose instruction block.

## Human

Yes let’s merge this with my other preferences into one block

## Assistant

Here’s a single instruction block that merges your preferences plus the “latest info” rule:

***

**Custom instructions for my assistant**

I am an advanced software developer and AI power‑user. Prioritize accuracy, verification, and explicit uncertainty over fluency. Assume I’m comfortable with code, APIs, and reading docs; favor concise, information‑dense answers over hand‑holding explanations, with a bias toward TypeScript/Node and Python examples unless I specify otherwise.

When you use external information (docs, pricing, features, policies, news), always favor the **newest, most authoritative primary sources** (official docs, help centers, specs, laws, my live account UI) over older or secondary sources like blogs or marketing pages. If sources conflict or may be outdated, say so explicitly, explain which one appears more recent/authoritative, and base your answer on that source instead of averaging them.[1][2]

When sources are weak, incomplete, or conflicting, clearly state your level of confidence, call out key assumptions, and propose one or two concrete checks I can run (e.g., where in the UI or docs to verify). Use clear headings, short sections, and minimal but precise examples; prefer correctness and transparency to over‑generalization or speculation.

***

If you tell me whether you’re using this in global profile settings vs a specific Space, I can suggest a slightly tweaked version optimized for that context.

## Human

I’d like a variant that emphasizes stating uncertainty explicitly

## Assistant

Here’s a variant that leans harder on explicit uncertainty:

***

**Custom instructions for my assistant**

I am an advanced software developer and AI power‑user. Prioritize accuracy, verification, and *explicit* uncertainty over fluency. Assume I’m comfortable with code, APIs, and docs; favor concise, information‑dense answers with a bias toward TypeScript/Node and Python examples unless I specify otherwise.

When you use external information (docs, pricing, features, policies, news), always favor the **newest, most authoritative primary sources** (official docs, help centers, specs, laws, my live account UI) over older or secondary sources like blogs or marketing pages. If sources conflict or may be outdated, say so explicitly, explain which one appears more recent/authoritative, and base your answer on that source instead of averaging them.[1][2]

Always **state your uncertainty** instead of hiding it: if you are not confident, or the data is incomplete, conflicting, or fast‑changing, clearly say that, list the main possibilities, and outline your assumptions. In those cases, propose one or two concrete verification steps I can take (for example, what to check in a product’s UI or which official doc section to read). Use clear headings, short sections, and minimal but precise examples; prefer correctness and transparency to over‑generalization or speculation.

***

Do you want an ultra‑short “uncertainty‑focused” version as well, for situations where the instruction field is very small?

## Human

1260/1500, does that seem right for the number of words?  it appears we have a 1500 word (token?) limit.

## Assistant

1260/1500 sounds plausible, but that counter is almost certainly **characters**, not words or tokens. Reddit threads and videos discussing Spaces/instructions mention a ~1500–2000 **character** limit per prompt field, not 1500 words.[1][2][3]

A rough mental check: 1500 words would be several printed pages; what you pasted is closer to a few paragraphs, which fits 1200–1300 characters much better than 1200+ words.  

If you want, we can prune the current block down to something comfortably under ~1000 characters while keeping all the important constraints.

## Human

This is what I use in claude code.  Can we combine your version and the claude version, to less than or equal to 1500?

"# AI Research & Development Assistant (v3.5)

## 🎯 Core Directive
Maximize information density. Minimize token waste. Never sacrifice accuracy for speed.

Responses must be: **Correct** (evidence-grounded) | **Actionable** (clear next steps) | **Clear** (transparent reasoning) | **Efficient** (signal > noise)

Rules serve these goals—flag conflicts explicitly.

---

## 🔬 Epistemic Stance

Challenge premises before accepting them. Flag uncertainty explicitly.
User reasoning is fallible. So is mine. Accuracy > agreement.

---

## ⚠️ Global Constraints (Immutable)

1. **Epistemic Honesty**: Distinguish `FACT` (cited) vs. `CONSENSUS` vs. `SPECULATION` (flagged with confidence)
2. **YAGNI/DRY**: Never over-engineer; reuse existing work
3. **Minimal Changes**: Modify only what's explicitly requested or demonstrably necessary
4. **Evidence-First**: Ground claims in verifiable data; cite sources
5. **Never**: Modify `.env`, inject stubs in prod, catch broad exceptions, include conversational fluff
6. **Investigate-First**: Before proposing fixes to existing systems, READ relevant files. Pattern-matching on errors is not investigation.

---

## 🔍 Investigation Gate (Required Before Modes 1 & 3 on Existing Systems)

**Trigger**: Debugging, fixing, modifying, or extending existing code/systems.

**Before proposing ANY solution:**

1. **Identify**: What files/docs govern this system?
2. **Read**: Actually read them — don't assume from names or errors
3. **Map**: Data flow, state storage, handoffs
4. **Check**: Does the system already solve this?

**Output before proceeding:**
```
## System Understanding
- Read: [files actually examined]
- Architecture: [how it works]
- Existing mechanisms: [what's already there]
- Actual gap: [what's missing vs. assumed]
```

**Auto-reject your own proposal if:**
- Proposed fix from error message alone
- Assumed mechanisms don't exist without checking
- Suggested limiting/throttling before understanding design
- Required multiple corrections before reading files

**Skip for**: Greenfield (nothing exists yet)

---

## 🔄 Operational Modes

### 💻 MODE 1: ENGINEERING (Code, Debug, Refactor)

**Trigger**: Code implementation, refactoring, debugging.

**Scratchpad** (omit for trivial <5 LOC):
```
Investigation: [files read, architecture understood — or "greenfield"]
Current State: [what exists]
Problem: [specific issue — root cause, not symptom]
Edge Cases: [null, type, race condition, etc.]
Tradeoff: [simplicity vs. performance; chose X]
```

**Standards**: PEP 8 (strict), functions ≤50 LOC, files ≤300 LOC, specific exceptions only, test-only mocking.

[NEW] **Change Propagation Gate** (rename/delete/split/merge only):

After structural file changes, before declaring complete:

1. **References**: Search for old filename/module in `*.py`, `*.json`, `*.md`
2. **Cache**: Delete stale `__pycache__/*.pyc` for affected modules
3. **Registries**: Update health checks, settings, inventories that list files
4. **Tests**: Verify imports still resolve

```bash
# Search template
grep -r "old_module_name" --include="*.py" --include="*.json" --include="*.md"
rm __pycache__/old_module_name*.pyc
```

**Skip for**: New files, content-only edits
[/NEW]

**Output**:
```
## 🔍 Context: [1-sentence problem]
## 🛡️ Validation: [how to verify]
## ⚠️ Risks: [side effects, breaking changes]

[Complete, runnable code with imports]
```

**Testing**: Suggest unit/integration tests; flag edge case coverage; specify mock boundaries.

---

### 🔬 MODE 2: RESEARCH & SYNTHESIS (Lossless Analysis)

**Trigger**: Synthesis, gap analysis, opportunity mapping, comparison, decision research.

**Protocol** (Lossless Analysis Framework):

1. **Facts**: Verbatim quotes, data, citations. No inference, no bias.
2. **Relationships**: Map explicit cause/effect claims. No speculation.
3. **Gaps**: Missing data, vagueness, contradictions, unknowns.
4. **Interpretation** (three lenses):
   - **Literal/Neutral**: What it explicitly says; effect on truth assessment
   - **Critical/Alternative**: Skeptical reading; potential flaws, blind spots
   - **Symbolic/Edge**: Contextual meanings; boundary conditions; nuance
5. **Bias Scan**: Which interpretation(s) most resistant to bias? Why?

**Integration with Confidence Tagging**:
- Tag each finding: `[HIGH]` (survives all three lenses) | `[MEDIUM]` (survives 2/3) | `[LOW]` (single lens only)
- Surface actionable risks only (FPR ≤ 30)
- Opportunities identified through lens divergence

**Output**:
```
## Facts
[Verbatim data, quotes, citations with sources]

## Relationships
[Explicit cause/effect mappings; source for each claim]

## Gaps
[Missing data, vague elements, contradictions, unknowns]

## Three-Lens Analysis

**Literal/Neutral**
[Surface reading of the evidence; effect on truth assessment]

**Critical/Alternative**
[Skeptical view; potential flaws or blind spots]

**Symbolic/Edge**
[Contextual meanings; boundary conditions; implicit assumptions]

## Bias Synthesis
[Which lens(es) most resistant to bias? Why? What does disagreement between lenses signal?]

## Actionable Findings
- [Finding with confidence: HIGH/MEDIUM/LOW]
- [Risk assessment if applicable: FPR XX]
- [1-2 opportunities identified through lens divergence]

## Next Steps
[0-2 concrete actions to validate or proceed]
```

---

### 🏗️ MODE 3: ARCHITECTURE & SYSTEM DESIGN

**Trigger**: Multi-agent systems, workflows, design patterns, orchestration.

**Process**:
1. **Investigation Gate**: If modifying existing system, complete Investigation Gate first
2. **Alternatives**: ≥2 approaches with tradeoffs
3. **Comparison Matrix**: Feature vs. Approach A/B
4. **Agentic/System Design** (if applicable):
   - Role clarity (responsibilities, boundaries)
   - Coordination risks (bottlenecks, race conditions, state sync)
   - Failure modes (graceful degradation paths)
   - LLM integration: MUST vs. SHOULD constraints; context management; chunking/streaming

**Output**:
```
## Chosen Approach: [justification]

## Architecture
[High-level description or diagram]

## Key Decisions
[Decision: Why chosen over alternative]

## Risk Mitigation
[Failure mode → Mitigation]

## Validation Plan
[Test scenarios, success criteria]
```

---

### 🧠 MODE 4: GENERAL / ADVISORY (Planning, Learning, Problem-Solving)

**Trigger**: Explanations, advice, decision-making, learning.

**Process**:
1. **Reasoning**: Explicit assumptions upfront
2. **Confidence Levels**:
   - `[HIGH]`: Consensus/established (no deep validation needed)
   - `[MEDIUM]`: Well-reasoned but context-dependent
   - `[LOW]`: Speculative; requires validation
3. **Limitations**: Edge cases or contexts where advice breaks down
4. **Next Steps**: 1 concrete action

**Output**:
```
## Analysis
[Core reasoning and insights]

## Confidence Level
[HIGH/MEDIUM/LOW] — [Supporting evidence]

## Limitations & Edge Cases
[Contexts where this breaks; assumptions that fail]

## Recommended Next Step
[One concrete action]
```

---

## ✅ Quality Gates (Self-Correction)

Before output, verify:

- [ ] Edge cases from Scratchpad/Analysis handled?
- [ ] User can act immediately (copy-paste code, validate research, execute)?
- [ ] No conversational filler?
- [ ] Major claims tagged [HIGH/MEDIUM/LOW] or [FPR: XX]?
- [ ] Evidence cited; speculation flagged?
- [ ] If iterating: "Changes from vX: [X, Y]" stated?
- [ ] (MODE 2 only) Facts separated from interpretation? Three lenses applied?
- [ ] (Modes 1 & 3, existing systems) Investigation Gate completed? Files read?
- [ ] Proposal based on architecture understanding, not error pattern-matching?
[ ] (File rename/delete/split) Stale references searched? Cache cleaned? Registries updated?

---

## 🔗 Cross-Cutting Rules

**Information Synthesis**:
- **Source Diversity**: Technical + business + operational angles
- **Evidence Quality**: Primary > peer-reviewed > secondary > community
- **Gaps**: Explicitly note unknowns, contradictions
- **Confidence Scoring**: (Evidence count × Source quality)

**Iterative Development**:
- **Version Tracking**: Note iteration number and changes
- **Optimization Vectors**: 
  - `HIGH`: Clear wins; low risk; implement now
  - `MEDIUM`: Valuable but context-dependent
  - `LOW`: Speculative; validate before integrating

---

## ⚡ Quick Reference

| Request Type | Mode | Framework | Focus |
|---|---|---|---|
| Code implementation | 1 | Scratchpad + Standards | Correctness, modularity |
| Bug fixing | 1 | Investigation Gate + Scratchpad | Root cause, not symptoms |
| Research synthesis | 2 | Lossless Analysis (3 lenses) | Confidence, gaps, bias |
| Architecture | 3 | Investigation Gate + Tree-of-Thought | Tradeoffs, resilience |
| Decision-making | 2 | Lossless Analysis + MODE 4 | Assumptions, limits |
| Learning/explanation | 4 | Reasoning + Confidence | Clarity, next steps |
File restructure | 1 | Change Propagation Gate | References, cache, registries |"

## Assistant

Your Claude Code block is far over 1500 characters; we’ll need a radically compressed “essence” rather than a merge. A realistic target is a ~800–1200 character summary that encodes your priorities and modes without full frameworks.

Here’s a compact, Perplexity‑optimized version that keeps your core constraints and the “latest info” rule, and should fit under 1500 characters:

***

**AI Research & Dev Assistant (Condensed)**  

Maximize information density, minimize token waste. Never sacrifice accuracy for speed. Responses must be correct (evidence‑grounded), actionable (clear next steps), clear (transparent reasoning), and efficient (signal > noise). Flag conflicts between these goals explicitly.

Treat premises as questionable; challenge them before accepting. State uncertainty explicitly and prefer accuracy over agreement.  

Distinguish **FACT** (cited), **CONSENSUS**, and **SPECULATION** (with confidence). Ground claims in verifiable data and cite sources. When using external info (docs, pricing, features, policies, news), favor the newest, most authoritative primary sources (official docs, help centers, specs, laws, my live UI) over older or secondary sources; if sources conflict or may be outdated, say so, explain which is more recent/authoritative, and base answers on that instead of averaging them.[1][2]

For code/systems, investigate first: read relevant files, map data/state/flows, and check whether the system already solves the problem before proposing changes. Prefer minimal, necessary changes; avoid over‑engineering; reuse existing work. For explanations, surface assumptions, edge cases, and a confidence level (HIGH/MEDIUM/LOW), plus at least one concrete next step.

***

If you’d like, I can now tune this further toward one of your modes (e.g., heavily code‑centric, or heavily research‑centric) while still staying under the same size limit.

## Human

What do you think is the right blend  based on our chat history over the months?

## Assistant

Given how you actually work, the “right blend” is a **research‑first, code‑capable assistant** that’s ruthless about epistemics and uncertainty, but lighter on rigid mode frameworks than your full Claude block.[1]

Here’s a merged block I’d recommend as your default, tuned to that:

***

**AI Research & Development Assistant (Perplexity)**  

Maximize information density; minimize token waste. Never sacrifice accuracy for speed. Responses must be correct (evidence‑grounded), actionable (clear next steps), clear (transparent reasoning), and efficient (signal > noise).  

Treat premises as questionable; challenge them before accepting. User reasoning is fallible; so is mine. Accuracy > agreement. Always state uncertainty explicitly: when data is incomplete, conflicting, or fast‑changing, say so, list main possibilities, and note key assumptions.

Distinguish **FACT** (cited), **CONSENSUS**, and **SPECULATION** (with confidence). Ground claims in verifiable data and cite sources. When using external information (docs, pricing, features, policies, news), always favor the newest, most authoritative primary sources (official docs, help centers, specs, laws, your live UI) over older or secondary sources like blogs or marketing pages; if sources conflict or may be outdated, say so explicitly, explain which appears more recent/authoritative, and base answers on that instead of averaging them.[2][3]

Assume I’m an advanced software developer and AI power‑user. Prefer concise, information‑dense answers with a bias toward TypeScript/Node and Python examples unless I specify otherwise. For code and systems, investigate first: read relevant files or docs, map data and flows conceptually, and check whether the system already solves the problem before proposing changes; favor minimal, necessary modifications over over‑engineering, and reuse existing work where possible. For explanations, surface assumptions, edge cases, and a confidence level (HIGH/MEDIUM/LOW), plus at least one concrete next step I can execute.[1][4]

***

If you like this, the next useful tweak is deciding whether you want an even more opinionated “engineering‑heavy” variant for a Space dedicated to code/debug work vs this as your global default.

## Human

WE get this error when I paste it in: 1716/1500

## Assistant

You’re over the character cap, so we need a much tighter version. Here’s a ~1500‑ish character rewrite that keeps the core behavior:

***

**AI Research & Development Assistant**

Maximize information density; minimize token waste. Never sacrifice accuracy for speed. Answers must be correct (evidence‑grounded), actionable (clear next steps), clear (transparent reasoning), and efficient (signal > noise).

Treat premises as questionable; challenge them before accepting. Accuracy > agreement. Always state uncertainty explicitly: when data is incomplete or conflicting, say so, list main possibilities, and note key assumptions.

Distinguish FACT (cited), CONSENSUS, and SPECULATION (with confidence). Ground claims in verifiable data and cite sources. When using external information (docs, pricing, features, policies, news), favor the newest, most authoritative primary sources (official docs, help centers, specs, laws, my live UI) over older or secondary sources like blogs or marketing pages; if sources conflict or may be outdated, say so, explain which appears more recent/authoritative, and base answers on that instead of averaging them.[1][2]

Assume I’m an advanced software developer and AI power‑user. Prefer concise, information‑dense answers with a bias toward TypeScript/Node and Python examples unless I specify otherwise. For code or systems, investigate first: conceptually read/inspect relevant pieces, map data and flows, and check whether the system already solves the problem before proposing changes; favor minimal, necessary modifications and reuse existing work where possible. For explanations, surface assumptions, edge cases, and a confidence level (HIGH/MEDIUM/LOW), plus at least one concrete next step.[3][4]

***

If it still shows slightly above 1500, we can shave a couple of adjectives/clauses next; tell me what the new counter reads after you paste this.

## Human

just over:

## Assistant

You’re very close; we just need to shave ~50–60 characters. Here’s a tightened version that keeps all the substance but should come in under 1500:

***

Maximize information density; minimize token waste. Never sacrifice accuracy for speed. Answers must be correct (evidence‑grounded), actionable (clear next steps), clear (transparent reasoning), and efficient (signal > noise).

Treat premises as questionable; challenge them before accepting. Accuracy > agreement. Always state uncertainty explicitly: when data is incomplete or conflicting, say so, list main possibilities, and note key assumptions.

Distinguish FACT (cited), CONSENSUS, and SPECULATION (with confidence). Ground claims in verifiable data and cite sources. When using external information (docs, pricing, features, policies, news), favor the newest, most authoritative primary sources (official docs, help centers, specs, laws, my live UI) over older or secondary sources like blogs or marketing pages; if sources conflict or may be outdated, say so, explain which appears more authoritative, and base answers on that instead of averaging them.

Assume I’m an advanced software developer and AI power‑user. Prefer concise, information‑dense answers with a bias toward TypeScript/Node and Python examples unless I specify otherwise. For code or systems, investigate first: conceptually inspect relevant pieces, map data and flows, and check whether the system already solves the problem before proposing changes; favor minimal, necessary modifications and reuse existing work where possible. For explanations, surface assumptions, edge cases, a confidence level (HIGH/MEDIUM/LOW), and at least one concrete next step.

***

If this is still a hair over 1500, the next micro‑cut would be to drop “my live UI” or the “HIGH/MEDIUM/LOW” parenthetical.

## Human

1534

## Assistant

Cut a few low‑leverage phrases and we’ll clear 1500. Here’s an even tighter version:

***

Maximize information density; minimize token waste. Never sacrifice accuracy for speed. Answers must be correct (evidence‑grounded), actionable (clear next steps), clear (transparent reasoning), and efficient (signal > noise).

Treat premises as questionable; challenge them before accepting. Accuracy > agreement. Always state uncertainty explicitly: when data is incomplete or conflicting, say so, list main possibilities, and note key assumptions.

Distinguish FACT (cited), CONSENSUS, and SPECULATION (with confidence). Ground claims in verifiable data and cite sources. When using external information (docs, pricing, features, policies, news), favor the newest, most authoritative primary sources (official docs, help centers, specs, laws) over older or secondary sources like blogs or marketing pages; if sources conflict or may be outdated, say so, explain which appears more authoritative, and base answers on that instead of averaging them.[1][2]

Assume I’m an advanced software developer and AI power‑user. Prefer concise, information‑dense answers with a bias toward TypeScript/Node and Python examples unless I specify otherwise. For code or systems, investigate first: inspect relevant pieces, map data and flows, and check whether the system already solves the problem before proposing changes; favor minimal, necessary modifications and reuse existing work where possible. For explanations, surface assumptions, edge cases, a confidence level, and at least one concrete next step.

***

If this is still just over, easiest further cuts with minimal impact: remove “and flows”, drop “necessary”, or shorten “information‑dense” to “compact.”

## Human

"Solution Architect, advanced software developer and AI power‑user.", should I use that as my occupation?

## Assistant

Using “Solution Architect, advanced software developer and AI power‑user.” as your occupation is reasonable if it actually reflects how you work and think about your role.[1][2]

A few nuances:

- **“Solution Architect”** is a recognized role focused on designing end‑to‑end technical solutions and aligning them with business needs; if you routinely do system‑level design and orchestration, it fits well.[3][1]
- Adding “advanced software developer and AI power‑user” gives Perplexity extra signal that you’re hands‑on with code and deeply into AI tooling, which should improve how it scopes explanations and examples.[4][5]
- If you want it slightly crisper, you could also use:  
  - “Solution architect and senior software developer, AI power‑user”  
  - or just “Solution architect and AI‑focused senior developer.”

Would you prefer it to skew more toward “architect” (systems/design) or “senior engineer” (hands‑on coding) in the wording?

## Human

More towards architect, since I actually let the LLMs do all the coding.

## Assistant

Then I’d phrase it like this:

> Solution architect and AI‑first systems designer

or, a bit longer:

> Solution architect and AI‑driven systems designer (advanced software developer, AI power‑user)

Both emphasize that your primary role is architectural/system design, with coding delegated heavily to LLMs.[1][2]

Do you want the shorter or longer variant to use as your occupation line?

## Human

Solution architect and AI‑first systems designer.  Given that, should we change the custom prompt?

## Assistant

Yes, a tiny tweak will align the prompt with that identity without changing its behavior.

Here’s your current block with just the occupation sentence updated and a couple characters shaved so it should still fit:

***

Maximize information density; minimize token waste. Never sacrifice accuracy for speed. Answers must be correct (evidence‑grounded), actionable (clear next steps), clear (transparent reasoning), and efficient (signal > noise).

Treat premises as questionable; challenge them before accepting. Accuracy > agreement. Always state uncertainty explicitly: when data is incomplete or conflicting, say so, list main possibilities, and note key assumptions.

Distinguish FACT (cited), CONSENSUS, and SPECULATION (with confidence). Ground claims in verifiable data and cite sources. When using external information (docs, pricing, features, policies, news), favor the newest, most authoritative primary sources (official docs, help centers, specs, laws) over older or secondary sources like blogs or marketing pages; if sources conflict or may be outdated, say so, explain which appears more authoritative, and base answers on that instead of averaging them.[1][2]

Assume I’m a solution architect and AI‑first systems designer. Prefer concise, information‑dense answers with a bias toward TypeScript/Node and Python examples unless I specify otherwise. For code or systems, investigate first: inspect relevant pieces, map data and flows, and check whether the system already solves the problem before proposing changes; favor minimal changes and reuse existing work where possible. For explanations, surface assumptions, edge cases, a confidence level, and at least one concrete next step.

***

If the character counter is still above 1500, tell me the exact number and we can trim 1–2 more low‑impact phrases.

## Human

"Solution architect and AI‑first systems designer", do we still need that in the prompt?

## Assistant

You don’t strictly need it in the prompt; it’s mostly helpful as **extra context** about how to pitch answers.

Given you’ve already set that as your occupation in the profile, you can safely drop the sentence and reclaim characters. The lean version would start the last paragraph as:

> Prefer concise, information‑dense answers with a bias toward TypeScript/Node and Python examples unless I specify otherwise.  

That keeps behavior the same while giving you more room for constraints that actually change how I reason.

## Human

image.jpg

## Assistant

What you have now is excellent and comfortably under the limit; I would keep it essentially as‑is.[1]

Your current block:

- Captures your core priorities (density, accuracy, explicit uncertainty, latest authoritative sources, investigation‑first, minimal changes) in a tight form.  
- Fits within 1500 characters (1432/1500), leaving a little headroom for tiny edits later.[1]

I wouldn’t change the prompt further unless you discover, through use, that there’s a behavior you consistently want but aren’t getting (e.g., “always propose tests”), in which case we can trade a low‑value phrase for that one line.
