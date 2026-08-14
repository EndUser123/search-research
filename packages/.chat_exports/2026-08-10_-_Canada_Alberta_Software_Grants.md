# 2026-08-10 - Canada Alberta Software Grants

- **Created:** 8/13/2026, 7:40:29 AM
- **Exported:** 8/13/2026, 7:40:31 AM
- **Messages:** 5
- **Source:** browser_extension

---

## #1 · assistant

Yes. **That business model makes incorporation considerably more attractive.** The reason is that gig revenue solves the weakness in the previous scenario: instead of putting your own after-tax money into the corporation so it can pay you, the **software factory earns external revenue and finances its own development**.

The core economic advantage is not primarily SR&ED. It is:

> 
**use your agentic system to turn a small amount of your human oversight into a much larger amount of delivered software, then retain the resulting profit inside an 11%-taxed Alberta CCPC to fund further automation and R&D.**

Assuming the company qualifies for the small-business deduction, the current combined federal/Alberta rate on qualifying active small-business income is approximately **11%: 9% federal + 2% Alberta**, generally within the $500,000 small-business limit. [[image]Canada+1](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/corporations/corporation-tax-rates.html?utm_source=chatgpt.com)

## Start with $100 of customer revenue

For a simple model, assume:

- 
10% of gross revenue goes to AI APIs, cloud compute, software, QA, etc.

- 
no founder salary;

- 
remaining profit stays in the corporation;

- 
11% corporation tax;

- 
Fiverr takes 20%;

- 
Upwork takes 10%;

- 
for direct clients, I'll use **3% as an illustrative payment-processing assumption**, not a verified universal rate.

Fiverr currently says freelancers receive **80% of a completed order**, while Upwork's standard freelancer service fee is **10%**. [[image]Fiverr Help Center+1](https://help.fiverr.com/hc/en-us/articles/29453184449169-Fiverr-Pro-freelancer-Badge-and-benefits?utm_source=chatgpt.com)

That produces:

| $100 customer bill | Fiverr | Upwork | Direct* |
| --- | --- | --- | --- |
| Gross revenue | $100 | $100 | $100 |
| Platform/payment cost | −$20 | −$10 | −$3 |
| Factory operating cost | −$10 | −$10 | −$10 |
| Pre-tax corporate profit | $70 | $80 | $87 |
| Corp tax @ 11% | −$7.70 | −$8.80 | −$9.57 |
| Retained in company | $62.30 | $71.20 | $77.43 |

*3% direct-payment cost is just a modelling assumption.

That's already informative: **Fiverr's 20% fee becomes one of the largest costs in an automated software factory.**

# What happens at scale

Using exactly the same assumptions:

| Annual customer billings | Fiverr retained | Upwork retained | Direct retained* |
| --- | --- | --- | --- |
| $25K | $15.6K | $17.8K | $19.4K |
| $50K | $31.2K | $35.6K | $38.7K |
| $100K | $62.3K | $71.2K | $77.4K |
| $200K | $124.6K | $142.4K | $154.9K |

So to accumulate approximately **$50,000 of new after-corporate-tax capital inside the company**, you would need roughly:

- 
Fiverr: **$80.3K customer billings**

- 
Upwork: **$70.2K**

- 
direct at our illustrative 3% processing cost: **$64.6K**

That money can then finance the factory rather than being immediately exposed to your ~40% personal marginal tax rate.

# Here's the really interesting comparison

Suppose your factory generates **$100,000 through Upwork**.

Using our assumptions:

```
Customer revenue                    $100,000
Upwork fee                           -10,000
AI/software/factory cost             -10,000
                                   ---------
Corporate operating profit           $80,000

Corporate tax @ ~11%                  -8,800
                                   ---------
RETAINED IN CORPORATION              $71,200
```

Because you already have roughly $150K of other personal income, if you had instead operated this as an unincorporated personal business, that additional $80K of income would fall largely into combined Alberta/federal marginal brackets of roughly **38%–42%**, rising further at higher income levels. [[image]taxtips.ca](https://www.taxtips.ca/taxrates/ab.htm)

My approximate calculation gives:

```
$80,000 additional personal business profit

Incremental income tax ≈ $32,361
After personal income tax ≈ $47,639
```

Compare:

**Corporation retains ~$71,200**

versus

**you personally retain ~$47,600**

That's about **$23,600 more deployable capital inside the corporation today.**

It isn't necessarily permanent tax savings.

It is largely **tax deferral**.

And for what you're contemplating, tax deferral could be extremely valuable because you don't need that money personally—you already have outside income.

# If you immediately withdraw everything, the magic mostly disappears

This is an important sanity check.

Profit taxed at the small-business corporate rate normally produces a **non-eligible dividend** when distributed.

At your ~$150K personal income level, the marginal Alberta/federal tax rate on non-eligible dividends begins around **28.5%**, rises to about **30.8%, 34.6%, 35.7%**, and ultimately higher as taxable income rises. [[image]taxtips.ca](https://www.taxtips.ca/taxrates/ab.htm)

For the $100K-Upwork example:

```
Corporate profit                         $80,000
Corporate tax                             -8,800
Dividend available                        71,200

Approx personal dividend tax             -23,977
                                        --------
Cash eventually in your hands            ~$47,223
```

Compare that with operating personally:

**~$47,639**

They are almost identical.

That's not an accident. Canada's corporate/personal tax system is designed toward tax **integration**, where earning business income personally versus through a corporation and immediately distributing it often ends up in roughly the same neighbourhood.

So:

> 
**Corporation + immediately withdraw all profits = modest advantage at best.**

But:

> 
**Corporation + retain profits + reinvest in software factory = potentially major advantage.**

# And your situation is unusually well suited to that

You aren't asking the factory to pay your mortgage next month.

You already have your ~$150K primary income.

So you could have:

```
                  DAY JOB
                 ~$150K
                    │
                    ▼
             personal living
             expenses/taxes

            SOFTWARE FACTORY
                    │
       ┌────────────┴────────────┐
       │                         │
    Fiverr                    Upwork
    clients                    clients
       │                         │
       └────────────┬────────────┘
                    ▼
               Alberta CCPC
                    │
          revenue − expenses
                    │
             ~11% corp tax
                    │
                    ▼
             retained capital
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    better agents   APIs     contractors
        │           │           │
        └───────────┼───────────┘
                    ▼
             better factory
                    │
                    ▼
             more capacity
```

That is a substantially more compelling economic system than the previous self-funded-SR&ED idea.

# The metric I would optimize isn't revenue

I'd optimize:

## **retained corporate profit per hour of your attention**

Suppose you sell a **$1,000 fixed-price software project**.

The factory uses $50 of AI/API/cloud resources.

You spend two hours total on:

- 
reviewing the customer request;

- 
approving the specification;

- 
reviewing exceptions;

- 
final QA;

- 
customer communication.

### Fiverr

```
Project                             $1,000
Fiverr                              -$200
Compute/tools                         -$50
                                   -------
Pre-tax profit                       $750
After 11% corp tax                 $667.50

Your attention: 2 hours

$667.50 / 2 = $333.75 retained per owner-hour
```

### Upwork

```
Project                             $1,000
Upwork                              -$100
Compute/tools                         -$50
                                   -------
Pre-tax profit                       $850
After tax                          $756.50

$756.50 / 2 = $378.25 retained per owner-hour
```

### Direct client, illustrative 3% processing

```
Project                             $1,000
Payment processing                    -$30
Compute/tools                         -$50
                                   -------
Pre-tax profit                       $920
After tax                          $818.80

$818.80 / 2 = $409.40 retained per owner-hour
```

Now we're getting to what I think is the actual opportunity.

# Your factory doesn't need to beat human developers on hourly rate

It needs to beat them on:

**customer value / Bruce-attention-hour.**

Suppose a normal freelancer needs 15 hours to build something worth $1,000.

Your factory needs:

- 
25 minutes requirements clarification;

- 
15 minutes approving plan;

- 
autonomous execution;

- 
35 minutes reviewing evidence/falsification;

- 
25 minutes final inspection/client delivery;

and perhaps $40 of inference.

That's **1 hour 40 minutes of scarce human time**, not 15 hours.

You shouldn't respond by charging the customer for 1.7 hours.

You should capture some of the productivity gain through **fixed-price/productized work**.

That makes something like Fiverr's model conceptually attractive despite its large commission.

# Productized gigs are probably much better than generic contracting

I would not start with:

> 
“I'll build whatever Python software you want.”

That's difficult for your factory because every job has a wildly different acceptance contract.

Instead:

> 
“I will turn your manual Excel process into a tested Python automation.”

or:

> 
“I will build a Chrome extension from your specification.”

or:

> 
“I will diagnose and fix a failing GitHub Actions workflow.”

or:

> 
“I will add a REST API to your existing Python application.”

Each should have:

```
ACCEPTED INPUT CONTRACT
        ↓
automated reconnaissance
        ↓
requirements extraction
        ↓
risk classification
        ↓
implementation
        ↓
tests
        ↓
independent review
        ↓
falsification
        ↓
artifact package
        ↓
human release gate
        ↓
CLIENT
```

The more standardized the input and output, the closer you get to a **factory rather than freelancing**.

# Fixed-price matters

This becomes particularly important with automation.

If you charge:

**$100/hour**

and your factory turns a 10-hour task into a 2-hour task, you make:

**$200.**

You have punished yourself for becoming productive.

If the customer thinks the result is worth:

**$1,000 fixed-price**

and your factory completes it with two hours of oversight, you still make roughly $1,000 less platform/factory costs.

Therefore I'd strongly favour:

**fixed-price + explicitly scoped + acceptance-test-driven jobs**

rather than selling your time.

Upwork currently has both fixed-price and hourly AI/software work, and its current marketplace includes many generative-AI/software-development projects. [[image]Upwork](https://www.upwork.com/freelance-jobs/generative-ai/?utm_source=chatgpt.com)

# There is evidence that the market itself exists

This isn't merely hypothetical.

Upwork currently has thousands of jobs categorized under generative AI, including software prototypes, APIs, RAG/evaluation systems and other development work. [[image]Upwork](https://www.upwork.com/freelance-jobs/generative-ai/?utm_source=chatgpt.com) Fiverr has dedicated categories for AI development, applications, chatbots, integrations and model work. [[image]Fiverr.com](https://www.fiverr.com/categories/ai-services?utm_source=chatgpt.com)

Fiverr even reported examples of sellers seeing substantial demand for AI-agent and automation work, although that's Fiverr's own market reporting rather than independent demand research. [[image]Fiverr.com](https://www.fiverr.com/news/spring-bti-2025?utm_source=chatgpt.com)

So **market existence is not the risky assumption**.

The risky assumptions are:

**Can your factory consistently acquire jobs at attractive prices?**

and

**Can it deliver them with sufficiently little human intervention while maintaining quality?**

Those are testable.

# There's another major benefit: gig revenue strengthens the funding story

Earlier we had:

> 
Bruce has interesting experimental technology.

With a working gig factory you could eventually say:

> 
We have built an agentic software-production system. It has processed 73 real customer projects, produced $85,000 in revenue, achieved a 96% acceptance rate, reduced median owner intervention from 7.3 hours to 1.8 hours, and we are now developing technological improvements addressing the remaining autonomous-execution failure modes.

That is a far stronger commercialization story.

IRAP exists to help innovative Canadian SMEs improve their innovation capacity and bring technology toward market. [[image]National Research Council Canada](https://nrc.canada.ca/en/support-technology-innovation?utm_source=chatgpt.com)

Real customers give you **live evidence instead of synthetic benchmarks.**

That aligns extremely well with what we've wanted from your agentic systems anyway.

# But be careful with SR&ED accounting

I would deliberately create **two accounting/work streams**.

### Stream A — Factory production

```
Customer requests website
        ↓
factory builds website
        ↓
customer pays $2,000
```

That's generally ordinary commercial software-production activity.

Do not automatically call it R&D.

### Stream B — Factory R&D

```
Observed failure:
factory misroutes ambiguous repo migrations
        ↓
technical uncertainty
        ↓
new routing architecture
        ↓
controlled experiments
        ↓
measured improvement/failure
```

That may potentially be SR&ED if it satisfies the actual technological-advancement and experimental-development criteria.

CRA requires genuine SR&ED expenditures and evidence; it is not enough that software development happened. [[image]Canada+1](https://www.canada.ca/en/revenue-agency/services/scientific-research-experimental-development-tax-incentive-program/salary-wages-policy.html?utm_source=chatgpt.com)

And if a customer specifically pays the company to conduct SR&ED on that customer's behalf, CRA's **contract-payment rules can reduce the performer's qualified SR&ED expenditures**. [[image]Canada+1](https://www.canada.ca/en/revenue-agency/services/scientific-research-experimental-development-tax-incentive-program/assistance-contract-payments-policy.html?utm_source=chatgpt.com)

So I would keep:

```
/revenue-work/
    customer-123
    customer-124

/factory-r&d/
    classifier-v2
    evidence-gate
    autonomous-debugging
```

both conceptually and in your accounting/evidence system.

# Fiverr versus Upwork

For **your particular concept**, I'd lean toward **Upwork first**, with Fiverr as another acquisition channel.

Not because Upwork is necessarily a better marketplace overall.

Mathematically, its standard 10% freelancer fee leaves substantially more margin than Fiverr's 20%. [[image]Upwork Support+1](https://support.upwork.com/hc/en-us/articles/211062538-Learn-about-the-Freelancer-Service-Fee?utm_source=chatgpt.com)

More importantly, Upwork explicitly supports **agency accounts**. Payments on agency contracts go to the agency, which then handles its own internal compensation. [[image]Upwork Support+1](https://support.upwork.com/hc/en-us/articles/211067598-How-to-create-an-agency?utm_source=chatgpt.com)

That's conceptually very close to:

> 
one human director + an AI software-production organization.

Fiverr also recognizes agencies as entities that can handle larger and multiple projects. [[image]Fiverr Help Center](https://help.fiverr.com/hc/en-us/articles/360010558038-How-Fiverr-works-for-clients?utm_source=chatgpt.com)

So both have structural paths beyond simply presenting yourself as an individual coder.

# Don't hide the AI factory

I wouldn't market it as:

> 
“Bruce personally hand-coded every line.”

I'd turn the automation into the proposition:

> 
**AI-native software engineering with human-directed architecture, automated testing, independent review and evidence-backed delivery.**

Fiverr's current standards specifically permit AI-assisted work, but require it to be customized/refined and hold the freelancer accountable for the final result; generic unmodified AI output is prohibited. [[image]Fiverr Help Center](https://help.fiverr.com/hc/en-us/articles/32242973123985-Our-Community-Standards?utm_source=chatgpt.com)

Your existing work on review gates, falsification, independent models and completion evidence could therefore be a **competitive quality-control system**, not merely a productivity trick.

# One boring issue appears surprisingly early: GST

Once the company exceeds the Canadian **$30,000 small-supplier threshold** for worldwide taxable supplies—either in one calendar quarter or over four consecutive calendar quarters—the GST/HST registration rules become relevant. [[image]Canada+1](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst-businesses/when-register-charge.html?utm_source=chatgpt.com)

Sales to foreign customers can have different GST/HST treatment, including circumstances where exported services are zero-rated, so I would have a CPA configure this rather than hard-code “charge everyone 5%.” CRA notes that zero-rated services are still taxable supplies at a 0% rate and can allow input-tax credits. [[image]Canada](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4027/doing-business-canada-gst-hst-information-non-residents.html?utm_source=chatgpt.com)

Both Fiverr and Upwork also have Canadian tax-reporting/compliance systems. Fiverr explicitly requires Canadian freelancers to provide platform tax-compliance information. [[image]Fiverr Help Center](https://help.fiverr.com/hc/en-us/articles/19424844896017-Tax-Regulations-for-Canada-Australia-and-the-European-Union?utm_source=chatgpt.com)

So the accounting flow should be:

```
Platform/customer
       ↓
corporate account
       ↓
invoice/order record
       ↓
platform fee
       ↓
GST classification
       ↓
business expense ledger
       ↓
corporate books
       ↓
T2 / GST / SR&ED records
```

not payments bouncing through your personal bank account.

# I think this changes our incorporation decision

Earlier my recommendation was:

**Probably incorporate if commercialization is real.**

With the software-factory idea, I'd move that to:

## **Yes — incorporation now has a strong business rationale.**

Because the corporation would have an actual economic function:

1. 
own/license the factory IP;

2. 
enter customer contracts;

3. 
receive gig revenue;

4. 
pay inference/cloud/platform/contractor expenses;

5. 
accumulate profits at the small-business corporate rate;

6. 
reinvest those profits into factory capability;

7. 
separate production work from genuine R&D;

8. 
establish real commercialization evidence for IRAP;

9. 
potentially claim SR&ED/IEG on qualifying internal experimental development;

10. 
eventually pay you dividends/salary when tax-efficient or personally useful.

That is a coherent business.

# The experiment I'd run before going much further

I wouldn't forecast $200K revenue yet.

I'd define a **$5,000 real-market validation experiment**.

Success criterion:

> 
Can the factory earn $5,000 of externally paid software revenue while requiring no more than roughly 10–15 hours of your total intervention and producing acceptable customer outcomes?

Measure for every job:

```
price
platform fee
inference cost
other variable cost

acquisition minutes
requirements minutes
execution-intervention minutes
QA minutes
client-communication minutes
rework minutes

first-pass acceptance?
refund?
defect after delivery?
customer rating
```

Then compute the number that actually matters:

> 
**after-platform, after-compute, after-rework contribution margin / total Bruce hours**

If that comes back at **$50/hour**, you have a freelance side business.

At **$150/hour**, you have an interesting software factory.

At **$300+/hour while customer quality remains high**, I'd consider that strong evidence that you've built something economically unusual and start optimizing acquisition, parallelism and productization rather than coding capacity.

That experiment would also give us exactly the sort of **real-world falsification evidence** needed to decide whether this is a business worth incorporating and funding aggressively.

## #2 · user

Are there repos that already support gig work like we’ve talked about?

## #3 · assistant

Yes. I found several relevant repos, but **I did not find one mature repo that already implements the complete system we just described**:

> 
marketplace → select profitable job → bid → negotiate/specify → execute with coding agents → independently verify → deliver → handle revisions → collect outcome/metrics.

What does exist is surprisingly close in pieces.

## The most relevant repos

| Repo | What it gives us | Fit |
| --- | --- | --- |
| Bid Pilot | Human-approved Upwork/Freelancer proposal generation | Excellent acquisition front end |
| upwork-mcp | Search, score, propose, messages, profile via MCP | Excellent architecture reference; unsafe integration method |
| Upwork-AI-jobs-applier | Job scraping, qualification, cover-letter generation | Useful classifier ideas |
| OpenHands Agent Canvas | Always-on multi-agent software execution/control plane | Strong factory reference |
| MetaGPT | PM→architect→engineer SOP “software company” | Useful process patterns |
| ChatDev 2.0 | Configurable multi-agent workflows | Useful orchestration reference |
| n8n workflows catalog | Direct-client intake/proposal/signature workflows | Useful outside Upwork |

### 1. `almasumdev/bid-pilot` — I would examine this first

This is almost exactly the **front door** we need.

It is a browser extension for Upwork and Freelancer that reads a job, feeds the job/profile to the local Claude CLI, generates a tailored proposal, suggests price and delivery time, lets the human edit it, and fills the form. Critically, **it deliberately doesn't click Submit**. [[image]GitHub](https://github.com/almasumdev/bid-pilot)

Its architecture is very clean:

```
Upwork job page
      ↓
browser extension
      ↓
extract scope/budget/skills
      ↓
local native-messaging host
      ↓
Claude CLI
      ↓
proposal + price + delivery estimate
      ↓
HUMAN REVIEW
      ↓
fill proposal form
      ↓
HUMAN SUBMIT
```

It already isolates platform-specific adapters so Upwork/Freelancer page handling isn't tangled with the LLM logic. [[image]GitHub](https://github.com/almasumdev/bid-pilot)

**I would probably fork concepts from this rather than write our own marketplace UI from scratch.**

We could replace:

```
Claude CLI
```

with something closer to your present architecture:

```
Grok Build / classifier
        ↓
commercial-fit evaluation
        ↓
factory feasibility assessment
        ↓
bid recommendation
```

Then it isn't merely writing nice cover letters.

It asks:

> 
**Can our factory profitably and reliably deliver this particular job?**

That is the classifier we actually need.

## 2. `zcrossoverz/upwork-mcp` — conceptually extremely interesting

This repo goes considerably further.

It exposes MCP tools including:

- 
`search_jobs`

- 
`get_job_details`

- 
`analyze_job`

- 
`submit_proposal`

- 
`get_proposals`

- 
`get_messages`

- 
`send_message`

- 
profile management. [[image]GitHub](https://github.com/zcrossoverz/upwork-mcp)

Its `analyze_job` already scores opportunities according to things such as niche fit, client quality, budget, competition and clarity. [[image]GitHub](https://github.com/zcrossoverz/upwork-mcp)

So conceptually:

```
Agent
 ↓
Upwork MCP
 ├─ find jobs
 ├─ retrieve details
 ├─ score jobs
 ├─ generate proposals
 ├─ submit proposals
 └─ communicate with clients
```

That's almost the **commercial agent interface** we imagined.

### But I would NOT deploy it as written.

The implementation logs into a real Chrome session, captures cookies, and drives the Upwork web interface through Playwright/CDP. The author even warns that Upwork may detect unusual activity. [[image]GitHub](https://github.com/zcrossoverz/upwork-mcp)

Upwork's current official policy is much stronger: unapproved bots, scripts and browser extensions that automatically access Upwork can produce warnings, restrictions or permanent blocking. Upwork specifically says compliant automation should use an **approved API key**, and even then the automation has to stay within the approved use case. [[image]Upwork Support](https://support.upwork.com/hc/en-us/articles/43342677368467-Use-bots-and-other-automation-properly?utm_source=chatgpt.com)

Upwork's Terms also prohibit scraping or using robots/similar mechanisms without written permission. [[image]Upwork](https://www.upwork.com/legal?utm_source=chatgpt.com)

Therefore:

**Use `upwork-mcp` as an architecture/specification mine—not as our production integration.**

That distinction is important.

# 3. `Upwork-AI-jobs-applier`

This one uses several AI agents to:

```
find job
   ↓
qualify job
   ↓
generate personalized cover letter
   ↓
prepare applicant
```

The current repository uses LangChain/LangGraph, Playwright and scraping, and stores generated cover letters for later use. [[image]GitHub](https://github.com/kaymen99/Upwork-AI-jobs-applier?utm_source=chatgpt.com)

Again, I wouldn't use the scraping path because of Upwork's automation policy. [[image]Upwork Support](https://support.upwork.com/hc/en-us/articles/43342677368467-Use-bots-and-other-automation-properly?utm_source=chatgpt.com)

But its **qualification architecture** is potentially worth stealing.

What I'd want from it is not:

> 
“Would Bruce like this job?”

but:

```
JOB
 ↓
Can factory execute it?
 ↓
technical fit
 ↓
uncertainty
 ↓
estimated AI cost
 ↓
estimated Bruce intervention
 ↓
delivery risk
 ↓
likely revision burden
 ↓
client-quality risk
 ↓
expected contribution margin
 ↓
BID / PASS
```

That is far more valuable.

# 4. OpenHands has become remarkably close to a software-factory control plane

This one has changed substantially.

The current OpenHands repo now describes **Agent Canvas** as a self-hosted developer control centre for an always-on engineering team. It can run OpenHands itself or third-party agents including **Claude Code, Codex and Gemini**, locally, in Docker, on remote machines or in cloud environments. [[image]GitHub](https://github.com/OpenHands/OpenHands)

It also supports event/scheduled automations and integrations with GitHub, Slack, Linear and other services. [[image]GitHub](https://github.com/OpenHands/OpenHands)

So it already solves pieces like:

```
WORK ORDER
     ↓
agent backend
     ↓
isolated execution
     ↓
GitHub repository
     ↓
issues/tasks
     ↓
parallel agents
     ↓
persistent execution
```

That is quite close to the **middle of the factory**.

### But I wouldn't replace your existing system with OpenHands.

Your present work already has mechanisms around classification, routing, deterministic evidence, falsification, session isolation, review and completion gates that address exactly the reliability issues a generic coding-agent platform leaves open.

Instead I'd ask:

> 
What infrastructure does OpenHands already solve that we shouldn't build ourselves?

Probably:

- 
persistent agent execution;

- 
sandbox/container management;

- 
backend abstraction;

- 
webhook/event execution;

- 
job-control UI;

- 
possibly parallel worker management.

Not necessarily your **reasoning/control policy**.

# 5. MetaGPT really does implement the “software company” idea

MetaGPT explicitly calls itself a **Software Company as Multi-Agent System**.

A one-line requirement goes through agents representing roles including product manager, architect, project manager and engineer, producing requirements, APIs, data structures, documentation and software. [[image]GitHub](https://github.com/FoundationAgents/MetaGPT)

Its core conceptual model is:

> 
`Code = SOP(Team)`

—that is, formalized standard operating procedures controlling a team of agents. [[image]GitHub](https://github.com/FoundationAgents/MetaGPT)

That's very relevant to our factory idea.

However, I don't think MetaGPT should be our foundation.

You have already gone significantly further on **verification and orchestration reliability** than its basic PM→architect→developer metaphor.

I'd mine it for:

- 
artifact boundaries;

- 
role responsibilities;

- 
transitions;

- 
requirements decomposition;

- 
project-management concepts.

Not transplant the framework.

# 6. ChatDev is another useful reference

ChatDev originally modeled a virtual software company with CEO, CTO, programmer and testing agents. ChatDev 2.0, released in January 2026, generalized that into a configurable multi-agent workflow platform with visual workflow construction and a Python SDK. [[image]GitHub](https://github.com/openbmb/ChatDev)

Again, this is more useful as **prior art** than as a replacement harness.

# The gap is actually pretty interesting

The ecosystem has largely built:

```
                MARKETPLACE SIDE
                       │
       ┌───────────────┼───────────────┐
       │               │               │
 job discovery      bidding        proposals
       │               │               │
       └───────────────┬───────────────┘
                       │
                [BIG MISSING LINK]
                       │
       ┌───────────────┴───────────────┐
       │                               │
 SOFTWARE AGENTS                  DEV FACTORIES
       │                               │
 OpenHands                        MetaGPT
 SWE-agent                        ChatDev
 Claude/Codex                     CrewAI
       │                               │
       └───────────────────────────────┘
```

I found lots on both sides.

**The mature bridge between “commercial opportunity” and “verified software-production work order” appears to be missing.**

And I think that's exactly where we should concentrate.

# I would NOT build an “Upwork bot”

I'd build something more general:

## **Commercial Work Router**

Inputs could eventually come from:

```
Upwork official alerts/API
Fiverr orders
Freelancer
direct website
email
referrals
manual paste
```

Everything gets normalized into something like:

```
opportunity:
  source: upwork
  customer: ...
  description: ...
  budget: 1500
  deadline: ...
  requirements: ...

commercial:
  platform_fee: ...
  expected_revenue: ...
  expected_compute: ...
  expected_human_minutes: ...
  expected_revision_cost: ...

factory:
  supported: true
  confidence: .87
  task_type: implementation
  required_capabilities:
    - react
    - postgres
  execution_tier: full_go
  estimated_runtime: ...
  verification_plan: ...

risk:
  requirements_ambiguity: medium
  security: low
  client_quality: high
  deadline: low

decision:
  bid: true
  recommended_price: 1800
  floor_price: 1150
```

And **that artifact becomes the authority** for the next stage.

That is much cleaner than giving an agent uncontrolled access to Fiverr/Upwork.

# Then connect it to what you already have

The end-to-end system I now think we want is:

```
                    MARKET
                       │
              official/manual intake
                       │
                       ▼
             COMMERCIAL WORK ROUTER
                       │
       ┌───────────────┼────────────────┐
       │               │                │
   capability       economics          risk
       │               │                │
       └───────────────┬────────────────┘
                       │
                 BID / DECLINE
                       │
                  HUMAN GATE
                       │
                 accepted job
                       │
                       ▼
              WORK-ORDER COMPILER
                       │
                       ▼
        deterministic acceptance contract
                       │
                       ▼
                YOUR /GO SYSTEM
                       │
             recon / classify / route
                       │
             implementation agents
                       │
                 verification
                       │
                falsification
                       │
            completion evidence
                       │
                       ▼
               DELIVERY BUNDLE
                       │
              HUMAN RELEASE GATE
                       │
                       ▼
                    CLIENT
                       │
                       ▼
          outcome / revisions / rating
                       │
                       └───────────┐
                                   ▼
                           FACTORY METRICS
```

That last feedback loop matters a lot.

Eventually the bidding classifier should know:

> 
“Jobs involving WordPress migrations appear profitable at posting time, but historically consume 4.3× predicted human intervention because client environments are messy.”

Then it stops bidding on them—or charges more.

**That is a software factory learning from real economic outcomes.**

## The repo combination I would investigate first

Rather than starting another implementation yet, I'd perform a focused reuse audit of **four repositories**:

1. 
**Bid Pilot** — marketplace/HITL UX and proposal adapter. [[image]GitHub](https://github.com/almasumdev/bid-pilot)

2. 
**upwork-mcp** — opportunity schema, job analysis and communication-tool contracts, while discarding its unauthorized browser-automation path. [[image]GitHub+1](https://github.com/zcrossoverz/upwork-mcp)

3. 
**OpenHands Agent Canvas** — persistent execution/sandbox/control-plane infrastructure. [[image]GitHub](https://github.com/OpenHands/OpenHands)

4. 
**MetaGPT** — software-company SOP/artifact concepts. [[image]GitHub](https://github.com/FoundationAgents/MetaGPT)

And I'd compare each directly against your existing Grok Build `/go` stack before adding anything.

My current hypothesis is that **we should build very little of the actual coding factory**. You already have much of its differentiated control logic. The missing high-value component is the **commercial opportunity → verified work-order bridge**, plus live economic telemetry afterward.

That could turn out to be a much smaller project than “build an autonomous AI software company.”

## #4 · user

What do you think the income possibility is realistically while I continue my full time day job?

## #5 · assistant

Yes. **I think a realistic mature side-business target is roughly $30,000–$70,000 CAD/year of additional pre-personal-tax economic value while keeping your full-time job.** I would treat **$100K+ as an upside case, not the planning assumption.**

The reason I'm more optimistic than I would be about ordinary freelancing is that you're not really proposing to sell your evenings by the hour. You're proposing to make **your attention the scarce resource while agents perform most of the production work**.

There is enough market depth to test that proposition: Upwork currently lists more than 22,000 software-development jobs and about 3,600 generative-AI jobs. Its current guidance puts experienced software developers around $70–$150+/hour and generative-AI specialists around $30–$150/hour. [[image]Upwork+3[image]Upwork+3[image]Upwork+3](https://www.upwork.com/freelance-jobs/software-development/?utm_source=chatgpt.com)

## What I would actually budget for

Assume you can give the business about **8 hours/week for 46 weeks = 368 hours/year**.

I would measure revenue against **all of your time**, including finding jobs, messages, requirements, checking agents, QA and revisions—not just coding time.

| Factory maturity | Contribution per your hour* | Annual pre-tax profit | After ~11% corp tax |
| --- | --- | --- | --- |
| Learning / inefficient | $50 | ~$18K | ~$16K |
| Decent factory | $100 | ~$37K | ~$33K |
| Good factory | $150 | ~$55K | ~$49K |
| Very good | $200 | ~$74K | ~$66K |
| Exceptional | $300 | ~$110K | ~$98K |

*Revenue minus marketplace fees, inference/cloud and other direct job costs, divided by **every hour you personally spend on the business**.

For a qualifying Alberta CCPC within its small-business limit, the current federal small-business corporate rate is 9% and Alberta's is 2%, hence the approximate 11% combined rate. [[image]Canada+1](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/corporations/corporation-tax-rates.html?utm_source=chatgpt.com)

That last column is **money retained in the corporation**, not spendable personal cash. Given your existing ~$150K employment income, I'd generally view retained corporate capital as the more interesting outcome; extracting it personally introduces another layer of tax. [[image]Canada](https://www.canada.ca/en/revenue-agency/services/tax/individuals/tax-rates-brackets/current-year.html?utm_source=chatgpt.com)

## Why $150–$200 per *your* hour isn't crazy

Consider a narrowly scoped **$1,000 fixed-price job**.

Suppose:

- 
Upwork fee: 10% for the illustration

- 
AI/cloud/testing: $75

- 
your requirements work: 30 min

- 
supervision/exceptions: 30 min

- 
QA/release: 45 min

- 
client communication/revision: 45 min

That's **2.5 hours of your attention**.

```
$1,000 revenue
 - 100 marketplace
 -  75 compute/tools
------
$825 contribution

÷ 2.5 Bruce-hours

= $330 contribution per Bruce-hour
```

Even if acquiring that project consumes another **2 hours** across proposals and dead leads:

**$825 / 4.5 = $183/hour.**

That's the number I care about.

Upwork's actual freelancer fee currently varies **0–15% by contract** and locks when the proposal/offer is sent, so 10% is only a modelling assumption. [[image]Upwork Support](https://support.upwork.com/hc/en-us/articles/211062538-Learn-about-the-Freelancer-Service-Fee?utm_source=chatgpt.com) Fiverr is more expensive: its current documentation says seller revenue is 80% of the order amount, effectively a 20% platform share. [[image]Fiverr Help Center](https://help.fiverr.com/hc/en-us/articles/5244747923985-Growth-Tools-for-Seller-Plus?utm_source=chatgpt.com)

# What I expect the ramp to look like

I would **not** expect $50K in year one automatically.

Starting without marketplace reputation is a meaningful handicap. Upwork itself says new freelancers frequently struggle because of missing reviews, incomplete portfolios and insufficient specialization, and recommends starting with smaller projects to establish feedback. [[image]Upwork+1](https://www.upwork.com/resources/cant-get-jobs-on-upwork?utm_source=chatgpt.com)

My probability-weighted expectation would look roughly like this:

### First 3–4 months

**$0–$5K revenue**

This is principally market discovery:

- 
figuring out which jobs your factory handles well;

- 
earning initial reviews;

- 
discovering what customers actually buy;

- 
finding scope patterns that create disastrous revisions;

- 
determining pricing.

I would regard even **$2–3K of real paid work** as useful evidence if your intervention is low.

### First full year

**Likely:** $15K–$40K revenue

**Good execution:** $40K–$70K

**Very successful first year:** $70K–$100K+

I would probably put my planning centre around **$30K–$50K gross revenue**, rather than assuming $100K.

### Once reputation + factory are established

This is where I think **$50K–$100K/year revenue while remaining employed becomes quite plausible**, provided you find a few highly repeatable services.

And at that point revenue ceases to be the main bottleneck.

**Your attention becomes the bottleneck.**

# The largest opportunity is probably not Fiverr

I'd use marketplaces to bootstrap trust and discover products.

Something like:

```
YEAR 1

Upwork/Fiverr
     ↓
real customer problems
     ↓
discover repeatable jobs
     ↓
reviews + portfolio
     ↓
factory learns economics
```

Then:

```
YEAR 2

marketplaces ───────────┐
repeat customers ───────┼─→ SOFTWARE FACTORY
direct inbound ─────────┤
referrals ──────────────┘
```

Why?

Fiverr permanently taking ~20% makes a large difference. [[image]Fiverr Help Center](https://help.fiverr.com/hc/en-us/articles/5244747923985-Growth-Tools-for-Seller-Plus?utm_source=chatgpt.com) Upwork currently takes 0–15% depending on the contract. [[image]Upwork Support](https://support.upwork.com/hc/en-us/articles/211062538-Learn-about-the-Freelancer-Service-Fee?utm_source=chatgpt.com) Upwork's Direct Contracts product, for clients you bring yourself, currently charges freelancers 5%, which illustrates the economics of moving toward your own customer acquisition. [[image]Upwork Support](https://support.upwork.com/hc/en-us/articles/360025040794-Direct-Contracts-bring-a-client-to-Upwork?utm_source=chatgpt.com)

# I think the sweet spot is $750–$2,500 projects

I wouldn't optimize around $50 bug fixes.

Nor would I initially accept $20K bespoke systems that can consume your life.

I'd target things like:

**$500–$800**

- 
repair automation;

- 
API integration;

- 
GitHub/CI problems;

- 
small Chrome-extension modification.

**$800–$1,500**

- 
complete small Chrome extension;

- 
workflow automation;

- 
data-processing service;

- 
API-backed internal tool;

- 
AI integration.

**$1,500–$3,000**

- 
small AI application;

- 
internal business tool;

- 
SaaS prototype;

- 
multi-system automation.

Current Fiverr guidance puts AI development projects generally around **$250–$1,500**, while its broader software-development guidance extends fixed projects up to roughly $6,000 and beyond for complex work. [[image]Fiverr.com+1](https://www.fiverr.com/categories/programming-tech/ai-coding?utm_source=chatgpt.com) Current Upwork listings likewise include everything from tiny jobs to $1,500–$2,000+ fixed-price software/AI projects. [[image]Upwork+1](https://www.upwork.com/freelance-jobs/artificial-intelligence/?utm_source=chatgpt.com)

Your factory should **reject most opportunities**, not accept everything.

# Here's the number that would excite me

Suppose eventually you do only:

**4 projects/month × $1,500**

That's:

**$6,000/month × 12 = $72,000 revenue.**

Suppose marketplace + inference + miscellaneous direct costs consume 18%:

**$72K × 82% = ~$59K corporate profit.**

After approximately 11% small-business corporate tax:

**~$52,500 retained in the company.** [[image]Canada+1](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/corporations/corporation-tax-rates.html?utm_source=chatgpt.com)

If each project consumes just **3 hours of your attention**, that's:

**12 production hours/month.**

Even if acquisition, administration and failed bids double it:

**24 hours/month ≈ 5½ hours/week.**

That strikes me as a **credible medium-term target**.

Not guaranteed, but credible.

# $100K retained is much harder—but possible

At your assumed 8 hours/week:

368 hours/year.

To leave approximately **$100K after corporate tax**, the factory would need around $112K of pre-tax contribution.

That's roughly:

### **$305 of contribution per one of your hours.**

That's too high for ordinary freelancing.

But potentially achievable with a genuine factory through combinations of:

- 
$2K–$5K fixed-price jobs;

- 
repeat clients;

- 
very low human intervention;

- 
reusable components;

- 
concurrent agents;

- 
direct clients rather than 20% marketplace fees;

- 
productized services;

- 
automated QA/review;

- 
pricing based on value rather than hours.

So I'd classify:

**$15K retained/year:** relatively achievable if you persist.

**$30K–$50K:** credible target.

**$50K–$70K:** strong but realistic if the factory works.

**$70K–$100K:** excellent operation.

**$100K+:** possible, but requires real leverage and customer acquisition—not merely better coding agents.

## The most important experiment

I wouldn't spend six months perfecting the factory before selling anything.

I'd set a **90-day falsification target**:

> 
**Generate $5,000 of real customer revenue while consuming ≤40 hours of your total attention.**

That means **$125 revenue per owner-hour before costs**. It's low enough for an immature factory but high enough to tell us whether leverage exists.

And record every opportunity:

```
opportunity
 ↓
bid?
 ↓
won/lost
 ↓
price
 ↓
predicted Bruce-hours
 ↓
actual Bruce-hours
 ↓
inference cost
 ↓
rework
 ↓
customer outcome
 ↓
contribution / Bruce-hour
```

After perhaps **10–20 paid jobs**, we'll have something much more valuable than forecasts: an empirical curve showing which types of work produce **$40, $150, $300 or $500 per hour of your attention**.

Then the factory's commercial router should systematically reject the $40 work and hunt for more of the $300 work.

**That's the path by which I can realistically see this becoming a $30K–$70K/year side business without turning your existing full-time job into two full-time jobs.**
