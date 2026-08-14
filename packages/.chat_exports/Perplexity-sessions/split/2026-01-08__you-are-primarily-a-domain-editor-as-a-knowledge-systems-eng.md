---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-01-08"
mode: "COPILOT"
uuid: "cdbe6805-640f-4ab6-a088-3b5d93492add"
entry_count: 2
---

## Human

You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.[1]

Read the entire conversation provided (post + comments). Remove navigation, ads, jokes, and obvious filler. Collapse any redundancy, but do not lose any unique, concrete information that could change how someone works or makes decisions in this domain.[2][1]

Produce a rewritten version of the thread that:

- Keeps every distinct **insight, workflow, configuration, or regimen**, including:
  - Specific sequences of actions, steps, or protocols people follow.
  - Concrete parameter choices (doses, thresholds, settings, schedules, frequencies, tools).[1]
  - Integration details between {artifacts_1}, {artifacts_2}, and {artifacts_3} (e.g., how they are chained or orchestrated).
- Preserves all mentions of **key artifacts** and what people actually do with them:
  - {artifact_type_1}: e.g., tools, agents, drugs, components.
  - {artifact_type_2}: e.g., files, documents, guidelines, protocols.
  - {artifact_type_3}: e.g., automations, policies, hooks, governance mechanisms.
- Removes repeated restatements of the same idea unless a repetition adds a new nuance, constraint, or failure mode.

After the rewrite, add a section called **“Operational patterns and setups”** where you explicitly list:

- **Multi‑entity flows**
  - How multiple {entities} are used together (e.g., “I use {artifact_A} and {artifact_B}, then have {artifact_C} consolidate and apply changes”).[1]
- **Automation patterns**
  - Any described triggers, scheduled runs, pipelines, or hooks that react to events or phases.
  - Any rules that determine when something is reviewer‑only vs allowed to auto‑modify.[3][1]
- **Guardrail artifacts**
  - Named documents, configs, or policies (e.g., {guardrail_doc_1}, {guardrail_doc_2}) and the key rules or principles they encode.
  - How those guardrails are enforced in practice (checks, reviews, blocking conditions).

Add a final section **“Practical recommendations”** that distills the most useful advice into concrete steps another practitioner in this domain could implement, for example:

- “Set up {artifact_or_system} with {N} parallel {entities} and one consolidator that merges and applies decisions.”
- “Add a hook or rule that blocks {undesired_pattern} unless {explicit_condition} is met.”
- “Configure {tool_or_policy} to act as a reviewer/critic only, not an automatic changer, for high‑risk operations.”[1]
- “Centralize principles in a single {guardrail_doc} and reference it in every {process_stage} where decisions are made.”

Format the answer with short sections and bullets. Be concise but do not omit any unique workflow, configuration, regimen, or recommendation from the conversation that could alter how someone operates in this domain.[1]

***

To use it, just fill:

- {domain} → “technical”, “clinical evidence”, “policy”, etc.  
- {artifacts_*}, {entities}, {guardrail_doc_*}, {tool_or_policy}, {undesired_pattern}, {process_stage} with your domain‑specific terms.
 
[(00:00:00)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=0) Now your prompts can be as long as you want near infinite thanks to this new approach called recursive language [(00:00:07)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=7) models which enable you to choose any language model and make it unlimited in context size window. So you're no longer [(00:00:14)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=14) worried about your prompt size and also being worried about if your performance getting deteriorated as your prompts is [(00:00:20)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=20) getting longer. In this video I'm going to show you how this open solution works and how you can use it in action. Let's [(00:00:25)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=25) check it out. Before I get into the codes and how you can use it right now in the [GitHub](https://app.getrecall.ai/item/41917020-0bf8-4291-9737-c88c375872fb) repo, I want to talk about [(00:00:30)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=30) the challenges that this solution is focusing on and what is the solution or how they're resolving it. The first [(00:00:36)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=36) challenge is that as you use different language models, there's a limit on the context size for example with GPT5 here [(00:00:42)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=42) maximum with let's say here 260K you can have the length of the prompt getting into the model. So you can no longer [(00:00:48)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=48)
have longer prompts if you have in your use case because the model cannot handle that. So how they're fixing it and make [(00:00:54)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=54) it much more longer near infinite as they're noting. Second when we're using longer prompts with language models we [(00:01:03)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=63) have seen across almost all the models that their performance is getting worse. So it's better to keep your prompts [(00:01:09)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=69) smaller so you can keep the performance of the language model. But obviously sometimes our prompts are long enough. I [(00:01:15)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=75) I cannot make it a smaller and if it's long unfortunately you're going to lose some performance. So check this actually [(00:01:21)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=81) chart they're showcasing when they're using GPT5 as is with different use cases different let's say reasoning or [(00:01:28)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=88) coding task stuff you can see that first of all they can not test the model with more than this amount of length because [(00:01:34)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=94) there's a context size limit and second as they are increasing this size from let's say 8k token all the way to 260 or [(00:01:42)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=102)
262 the performance score is getting worse and there's a significant drop after 33 3 uh 33k token and if you can [(00:01:54)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=114) see on the right side which is this recursive language model approach that they applied a GPT5 which I got going to [(00:02:00)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=120) tell you what it is you can see that not only you can have longer prompts being used with this model let's say here 1 [(00:02:08)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=128) million just as a test but also that degragation of performance which was a sudden drop here is disappeared so that [(00:02:15)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=135) means two challenges first the prompts can be get longer fixed. Second, there's no deteration in performance as the [(00:02:23)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=143) prompts are getting larger and larger. But what is this [RLM](https://app.getrecall.ai/item/2266964d-63f3-42e2-9011-acc831e79a92) and how they enable this on GP5 as an example? They're [(00:02:30)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=150) noting that in their approach which is recursive language model. They treat the prompt that long prompt that you have as [(00:02:37)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=157) part of the environment. So in [Python](https://app.getrecall.ai/item/f64dd8fe-1a3c-4443-90b4-8da83e0168d3), we have environment variables that we can specify for a given code. And what [(00:02:44)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=164)
they do is that they consider your prompt as an environment. And I'm going to tell you why. So they load this input [(00:02:50)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=170) prompt which is pretty long as a variable inside the Python rail environment and write code to pick into [(00:02:57)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=177) the compose and invoke itself recursively over programmatic snippets of the variable. So let's make it [(00:03:02)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=182) simple. What they do is that they give that prompt in a way to the model that the model can interact with the prompt [(00:03:09)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=189) through coding. So the model instead of seeing all the prompt the model generate codes to parse the prompt or extract a [(00:03:17)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=197) specific part of the prompt merge the prompt. So with having this coding based capability to interact with the prompt I [(00:03:24)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=204) no longer need to print all the prompt text which is long and doesn't fit to the model for the model. Let's go [(00:03:30)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=210) through an example. Uh this is our initial prompt that is pretty long and we're saying that you are reading an [(00:03:35)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=215)
extremely long book. Can you list all out all which items that were made before the grade level blah blah blah. [(00:03:41)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=221) So this is the prompt but obviously I'm not going to give all this prompt to language model. I going to let [RLM](https://app.getrecall.ai/item/2266964d-63f3-42e2-9011-acc831e79a92) [(00:03:48)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=228) approach handle this. So how it works? They're going to give some system prompt which are going to tell you what that [(00:03:54)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=234) system prompt is to the language model and tell that hey there is a prompt. You're not you're not going to see all [(00:04:00)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=240) of that. It's pretty long but you can code to interact with it and here's the query. So what language model does it [(00:04:06)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=246) generates some code. You can see that the language model decided to split that prompt to two parts based on the keyword [(00:04:14)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=254) called chapter because maybe somewhere in the prompt we were talking about chapter one and two. So it knows that [(00:04:20)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=260) okay I need to split that prompt to two chapters and then for each chapter it calls the LLM separately. Now the [(00:04:26)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=266)
prompts is almost half and then after that the final answer should be merged based on multiple sub calls to the [(00:04:33)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=273) language model. So what we did we generated this code by language model. We parse the prompt using the code that [(00:04:41)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=281) language model generated and then we merge all these sub calls together to give the final answer back. So that [(00:04:47)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=287) means if your language model cannot let's say generate more than 10k output token that's why you can have millions [(00:04:54)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=294) of output tokens because you're merging these sub calls. So it's sort of an agentic approach that you are parsing [(00:05:00)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=300) the prompt using code instead of just printing all of that based on the depths that you or the model specify which was [(00:05:06)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=306) here as an example. We got the prompt we split in two sub calls chapter one and chapter two. We call the language model [(00:05:12)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=312) and then we merge the final outcome all the way back together. All right. So how about the performance of the results of [(00:05:18)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=318)
[RLM](https://app.getrecall.ai/item/2266964d-63f3-42e2-9011-acc831e79a92) compared to not using RLM? And here's the answer for this paper. They actually benchmark GPT5 and Quinn and [(00:05:25)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=325) again you can apply this to any model. And you can see that they apply that for different tasks. Let's say code question [(00:05:31)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=331) answer browse and O long or along with pairs which is a little bit more complex. So each of these tasks they [(00:05:38)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=338) have different range of input token in the prompt from 23K up to 4 million. In some tasks they use up to 11 million [(00:05:45)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=345) token. Obviously coin or GPT5 by themselves cannot handle that amount of prompt. There's there's limit on context [(00:05:52)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=352) size. But with RLM approach that I described, they were able to apply this. And if you see the results, you can see [(00:05:58)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=358) that almost all the time RLM is the one that has the highest score compared to the others. And here we can see the [(00:06:05)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=365) average price with standard deviation that shows in some cases RDM can be even cheaper or close to the base model. In [(00:06:13)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=373)
some cases RM can be more expensive because of recursive sub calls. But it really depends on how smart your model [(00:06:20)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=380) is. If GPD5 is smaller than quinn as an example, maybe it can answer that long prone question with two or three sub [(00:06:26)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=386) calls instead of just recursively calling that. This is literally the key caveat of this approach. You need to be [(00:06:32)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=392) cautious about the cost specifically in complex and recursive calls. But in general, two benefits which is unlimited [(00:06:39)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=399) context size and no deration of performance are the main two gains that you get out of this solution. But here's [(00:06:46)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=406) the critical question. How does LLM knows that it should interact with the prompt through code like calling that [(00:06:53)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=413) having those recursive calls and then generating some sub calls and mering all those stuff without seeing the full [(00:07:00)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=420) prompt? Well, here's the key. Instead of giving your long prompt which is your initial prompt, [RLM](https://app.getrecall.ai/item/2266964d-63f3-42e2-9011-acc831e79a92) approach initiate a [(00:07:07)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=427)
system prompt which is the default of all these RLM calls and they have added that system prompt in the paper. I will [(00:07:14)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=434) add the link to the paper and also the [GitHub](https://app.getrecall.ai/item/41917020-0bf8-4291-9737-c88c375872fb) repo of their code that I'm going to walk through that shortly inside [(00:07:19)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=439) Disco channel and the Disco channel link is on the video description below. When you go to the channel, click on the [(00:07:23)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=443) reference section, you will see the reference of all the videos including this one that I have recorded. So in the [(00:07:29)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=449) system prompt that they have added they're telling to the LLM that you are tasked with answering query with [(00:07:35)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=455) associated context. You can access transform and analyze this context interactively in a ripple environment. [(00:07:41)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=461) This is the key part that we're letting LL knows that how it can interact with the prompt that is coming in from the [(00:07:46)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=466) user which is that very long prompt. And then we are specifying some environments that we're saying that hey your context [(00:07:52)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=472)
type is this. This is the total lens and you can initialize it environment with context which is a variable that [(00:07:59)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=479) contains extremely important information. You have LLM query which is the function that allows you to query an [(00:08:05)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=485) LLM and then you have uh the ability to use print statement to view the output of your ripple code. So ripple code is [(00:08:12)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=492) like terminal when you code and hit enter you execute the code and see the results. Technically we are specifying [(00:08:17)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=497) this environment variables one two three so that language model can use like agentic approach to interact with the [(00:08:23)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=503) prompt through coding it and I I don't want to go and read through all these uh meta prompt but they have added some [(00:08:30)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=510) examples some metalarning here to make sure that prompt fully works and you can simply just copy paste or use their open [(00:08:36)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=516) source code which I'm going to share with you shortly to make sure we fully understand their approach I want to walk [(00:08:41)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=521)
through in one of the examples they mentioned in their paper they have added couple of them So this one I will find [(00:08:46)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=526) it more uh straightforward and easier to understand. So you can technically read the rest of the paper to understand much [(00:08:52)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=532) more examples. But here they're saying that this example they tested that was the cost and in this task the agent must [(00:08:58)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=538) find the answers to the following multihob query given a corpus of 100 unique documents. So imagine you have a [(00:09:04)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=544) prompt that has 8 million tokens and this prompt has unique documents about a given topic. Let's say here's a specific [(00:09:12)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=552) dish and these evidence documents the the language model should navigate through them to propose answers for this [(00:09:21)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=561) query that the user provide but obviously it should handle somehow this 8 million token prompt using [RLM](https://app.getrecall.ai/item/2266964d-63f3-42e2-9011-acc831e79a92) and [(00:09:28)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=568) here we're using again GPT5 which has just 26k token limit so how we going to fit in that 8 million using RLM [(00:09:37)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=577)
so here is the document this vegetables uses fish but adding meat is possible. So it has some information about the [(00:09:43)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=583) culture, the root and uh some ingredients out of this stew. I don't want to read through all that. But what [(00:09:48)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=588) is step one? We are not going to give this 8 million token to GPT5. We are giving that meta prompt that I just [(00:09:54)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=594) talked about. So the LLM can interact with this prompt through code. Now GPT5 first decide to prop the at the 100 [(00:10:03)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=603) token document list with reix queries. So this is a code that GBT5 generate using reix to filter out some part of [(00:10:11)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=611) the prompt to make sub some some sub calls to language model. It has some prior priors about these events as shown [(00:10:19)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=619) from this particular choice of word it looks for which we want to check that in the code but it also looks for specific [(00:10:24)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=624) keywords in the prompt like like beauty pageent and festivals. So based on the question that you ask it's going to [(00:10:30)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=630)
filter the prompt based on these keywords. How? using this code that GP5 generated. So you can see that it is [(00:10:37)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=637) searching for some keywords and using reix and the keywords it tried to create some chunks out of that 8 million [(00:10:44)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=644) initial prompt that we had. Then after running its reix queries the root lm finds an interesting sneer on the chunk [(00:10:51)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=651) at index 6. So assume that index 6 which was in specific chunks after this code got some really informative information. [(00:10:58)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=658) So it launches recursive language model calls over the estimate to look for the information relevant to the original [(00:11:04)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=664) query. So that recursive approach getting it generated right now. The [RLM](https://app.getrecall.ai/item/2266964d-63f3-42e2-9011-acc831e79a92) is able to both store this information [(00:11:12)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=672) in a variable answer six as well as print this information out for the root LM2. So as soon as we call these [(00:11:20)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=680) recursive calls, we save these intermediate results somewhere. So later on we can use it for another call or [(00:11:26)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=686)
merge them at the end. The sublm calls find the answer is likely Maria delmakio based on again what was the query about [(00:11:33)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=693) and it stores information back to the root language models environment. So you can see that now we have this query [(00:11:40)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=700) information and the response is getting batched based on these sub calls and then step three after checking the [(00:11:46)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=706) information above the root LM reasons that it has enough information to answer the query. The root LM chooses to check [(00:11:51)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=711) the answer again with two additional recursive LM calls to confirm that its answer align with its check. Finally, [(00:11:58)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=718) the root lm returns its final answer, which is the correct one. So, you could see that with these multiple codes that [(00:12:04)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=724) the language model was generating, it was parsing the prompt multiple times to get the final answer back regardless of [(00:12:12)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=732) how big was the prompt. And at the same time, because we didn't fit in 8 million token, each chunk that we parse was, [(00:12:19)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=739)
let's say, 10k or 20k. So we are in the golden ratio of the context size of the given language model that we never lose [(00:12:26)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=746) the performance because of that lengthy prompt. So we get the highest performance of the model without hitting [(00:12:33)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=753) the token limit. And some good news if you want to test their solution you don't need to code what I just explained [(00:12:38)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=758) because they have released the open source [GitHub](https://app.getrecall.ai/item/41917020-0bf8-4291-9737-c88c375872fb) repo of [RLM](https://app.getrecall.ai/item/2266964d-63f3-42e2-9011-acc831e79a92). I'll add again the link of this GitHub repo to [(00:12:43)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=763) the discord channel in video description below. But what they're providing is that a nice way that you can quickly [(00:12:49)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=769) install this package. As soon as you install there's a quick start. You can check that [Python](https://app.getrecall.ai/item/f64dd8fe-1a3c-4443-90b4-8da83e0168d3) code or with just [(00:12:55)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=775) importing RLM with the back end. As of now, [OpenAI](https://app.getrecall.ai/item/466b4e3f-51d0-4b30-a203-01d677a357a7) with provide OpenAI key. You can then start actually asking your [(00:13:04)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=784) question whatever long prompt that you have and that recursive approach get generated on back end as you're using [(00:13:10)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=790)
RLM. Obviously you need to also choose your model name here from OpenAI which is UBC5 nano was chosen as an example. [(00:13:16)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=796) Lastly the nice option they provide is that if you want to visualize the traces of these recursive language model [(00:13:22)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=802) approach you can enable that with actually in initializing this visualizer with mpmdev under this path. Then you [(00:13:30)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=810) can also have that JSON file that includes some uh visualization that you can print out to see how this R&D [(00:13:36)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=816) approach is uh recursively calling language model to give the final answer back over to you. All right, that was [(00:13:42)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=822) the video about recursive language models. I hope you found this video helpful. If yes, I would be very [(00:13:47)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=827) thankful if you click on like icon and make sure you share your thoughts, questions and comment section below and [(00:13:51)](https://www.youtube.com/watch?v=wjYUqCsWaFQ&t=831) subscribe so you don't miss the next video. Thank you so much.

## Assistant

You are primarily a **technical** editor. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.[1]

***

## Core idea: Recursive Language Models (RLM)

- Recursive Language Models (RLM) treat an extremely long prompt as an external environment (a variable in a Python REPL-like context) rather than as standard in-context text, allowing effectively unlimited context for any base LLM with a finite context window.[1]
- Instead of directly feeding millions of tokens to the model, RLM has the LLM write code that programmatically reads, filters, chunks, and queries the large prompt, then merges sub-results, avoiding performance collapse at long context lengths.[1]

***

## Challenges RLM addresses

- Standard LLMs like “GPT5” have a hard context limit (e.g., around 260k tokens in the example), beyond which the model simply cannot accept more prompt tokens, so entire codebases or multi‑million token corpora cannot be loaded at once.[1]
- As prompt length grows from around 8k toward the model’s context limit, performance degrades significantly, with a notable drop beyond roughly 33k tokens for GPT5 in the showcased benchmark.[1]

***

## RLM solution: treating prompt as environment

- The long prompt is loaded into a Python “environment” as a variable (e.g., `context`) in a REPL‑like execution space; the LLM is given tools (functions and variables) to inspect and transform that environment via code rather than by directly “seeing” all tokens as text.[1]
- The LLM is instructed that it can:
  - Initialize the environment with the full context.
  - Call a provided `LLM_query` function to query another LLM (or itself) on selected sub‑prompts.
  - Use `print` to view intermediate outputs from REPL code.[1]

***

## System prompt / meta‑prompt configuration

- A fixed **system prompt** is used for all RLM calls; it tells the model:
  - It is tasked with answering a query using an associated context.
  - It can access, transform, and analyze that context interactively in a REPL environment.[1]
- The system prompt explicitly defines:
  - The **context type** and **total length**.
  - The environment variable (e.g., `context`) that contains the long prompt.
  - Available helpers like `LLM_query` and printing for inspection.[1]
- The meta‑prompt also includes examples and “metalearning” so the model learns good patterns for:
  - Chunking the context.
  - Filtering with regex/keywords.
  - Running recursive sub‑calls.
  - Storing intermediate results in variables for later merging.[1]

***

## Concrete workflow: simple chapter‑based example

- Initial situation: a long prompt (e.g., “you are reading an extremely long book… list all items that were made before grade level X”) is too large to fit as one prompt.[1]
- Workflow:
  - Only the meta/system prompt + user query are fed to the LLM, not the entire book text.[1]
  - The LLM generates code that:
    - Splits the long prompt into chunks based on a structural keyword such as `"chapter"` (e.g., “chapter 1”, “chapter 2”).[1]
    - For each chapter chunk, separately calls the base LLM (via `LLM_query`) to answer the sub‑question on that subset.[1]
  - The host environment executes this generated code:
    - Parses the prompt with the model‑generated code.
    - Makes multiple sub‑calls to the base LLM, each with a manageable prompt length (e.g., 10k–20k tokens per call).[1]
  - The environment merges sub‑answers into a final answer and returns it to the user.[1]
- Because each sub‑call stays within the model’s “golden ratio” context size, the system avoids the performance degradation seen with a single massive context and can aggregate to millions of output tokens by concatenating sub‑results.[1]

***

## Detailed multihop example with 8M‑token corpus

- Setup:
  - A corpus of 100 unique documents about a topic (e.g., a specific dish) is stored in a single prompt of about 8 million tokens, far beyond GPT5’s ~26k token limit.[1]
  - The task is to answer a multihop query over this corpus.[1]
- Step 1 – meta‑prompt only:
  - The 8M‑token content is **not** fed directly to GPT5; instead, GPT5 receives only the meta‑prompt and the user’s question, plus the knowledge that the full corpus is in the `context` environment variable.[1]
- Step 2 – first‑level filtering via regex and keywords:
  - GPT5 generates code that:
    - Iterates over a 100‑document list using regex queries.
    - Looks for specific keywords related to the question (e.g., “beauty pageant”, “festivals”, or domain‑specific terms tied to the query).[1]
  - The generated code:
    - Searches for those keywords using regex.
    - Builds chunks from the original 8M‑token `context` where matches occur, effectively narrowing down relevant segments.[1]
- Step 3 – selecting promising chunk and recursive sub‑calls:
  - After running the regex filters, the root LM identifies a promising chunk at, for example, `index 6` and treats it as an informative subset.[1]
  - It then launches **recursive LM calls** over this chunk:
    - Sub‑LM calls explore the content more deeply regarding the original query.
    - Each call remains within token limits (e.g., ~10k–20k tokens).[1]
- Step 4 – storing and reusing intermediate results:
  - Results from recursive calls are stored in variables such as `answer_6`, and also printed so the root LM can read them.[1]
  - The model accumulates evidence across sub‑calls within the environment, updating variables as it goes.[1]
- Step 5 – verification and final answer:
  - After seeing enough evidence, the root LM determines it can answer.
  - It may perform 2 additional recursive LM calls as **sanity checks** to confirm that its candidate answer (e.g., “Maria delmakio”) aligns with the evidence.[1]
  - The root LM then returns the final answer, having parsed the massive prompt through multiple code‑driven passes instead of direct long‑context access.[1]

***

## Performance and cost behavior

- Benchmarks compare GPT5 and Qwen with and without RLM across tasks like code, question answering, browsing, and more complex “along with pairs” tasks, with input prompts up to 4M and in some cases 11M tokens.[1]
- Observed behavior:
  - Base models alone cannot handle multi‑million‑token prompts due to hard context limits, while RLM makes these workloads feasible by chunking.[1]
  - RLM achieves the highest accuracy scores in almost all tested scenarios compared to non‑RLM baselines.[1]
- Cost characteristics:
  - Average cost (with standard deviation) shows that RLM can be **cheaper or similar** to the base model in some tasks, but **more expensive** in others because of the additional recursive sub‑calls.[1]
  - Cost depends heavily on:
    - How “smart” the base model is at writing efficient code and minimizing the number of sub‑calls.
    - For a stronger model, a long question may be answered with only two or three sub‑calls instead of deeply recursive exploration.[1]
- Key caveat:
  - Practitioners must monitor and control cost, especially in complex setups that trigger many recursive calls.[1]

***

## Implementation details: package, models, and visualization

- An open‑source GitHub repository provides a ready‑to‑use implementation of RLM, so users do not need to recreate the entire approach from scratch.[1]
- Quick start:
  - Install the RLM package via standard tooling (e.g., Python package install).[1]
  - Import RLM in Python and configure a backend; currently, OpenAI models are supported by providing an OpenAI API key.[1]
  - Choose a specific model name (e.g., “UBC5 nano” in the example) for the underlying LLM used by RLM.[1]
- Usage:
  - Once configured, you can send arbitrarily long prompts (e.g., multi‑million token text stored in a file or environment variable) plus the query, and the RLM backend will automatically generate and execute the recursive program for you.[1]
- Trace visualization:
  - A visualizer can be enabled by initializing it with a specified path under `npm dev` (or similar tooling) so that:
    - The system writes JSON traces of the recursive LLM calls.
    - You can inspect how chunks were created, which sub‑calls were made, and how the final answer was assembled.[1]

***

## Behavioral properties and advantages

- RLM enables “near infinite” context windows by shifting from monolithic context to code‑driven retrieval and aggregation over an external context store.[1]
- Because each sub‑call operates in an optimal context size range (e.g., ~10k–20k tokens), the typical degradation seen at very long prompts is removed, leading to:
  - Stable or better performance even as the conceptual context length scales to millions of tokens.
  - Preservation of the model’s best‑performing regime while still reasoning over large corpora.[1]

***

## Operational patterns and setups

### Multi‑entity flows

- **Root LM + sub‑LMs over environment**:
  - A **root LM** (e.g., GPT5) receives the meta/system prompt and user query, but not the full corpus; it generates code that controls how to interact with `context`.[1]
  - This code orchestrates multiple **sub‑LM calls** via `LLM_query` on selected chunks of the environment, treating each call as a specialized “worker” focused on a subset of the data.[1]
  - The root LM then merges the outputs of these worker calls into a final answer, often after consistency checks.[1]
- **Keyword/regex‑based pre‑filtering then recursive search**:
  - The root LM:
    - First uses regex and keyword filters to narrow an N‑document corpus (e.g., 100 docs in 8M tokens) to a small subset of promising chunks.[1]
    - Then spawns recursive sub‑calls only on those chunks, reducing cost and focusing compute on relevant regions.[1]
- **Chunk‑structured splitting (chapters)**:
  - For structured texts like books, the LM:
    - Splits by structural markers (e.g., “chapter”) into multiple chapters.
    - Calls the base LLM separately on each chapter to compute partial answers.
    - Aggregates chapter‑level results into a global answer.[1]

### Automation patterns

- **System‑prompt‑driven behavior**:
  - All RLM calls use a shared system prompt that:
    - Declares the environment variables and tools.
    - Instructs the LM to use code and recursion to interact with long context.
    - Implicitly triggers the “agentic” pattern (write code → run code → read results → refine).[1]
- **Recursive orchestration loop**:
  - The operational loop is:
    - Receive query + meta‑prompt.
    - Generate code to inspect and filter `context`.
    - Execute code, obtain intermediate results.
    - Optionally generate updated code using newly printed outputs.
    - Repeat until the root LM decides it has enough information, then generate a final answer.[1]
- **Cost/complexity controls (implicit)**:
  - While not implemented as explicit rules in the video, the key operational warning is to:
    - Monitor the number and depth of recursive calls.
    - Prefer more capable base models that can solve queries with fewer sub‑calls, reducing recursion depth and cost.[1]

### Guardrail artifacts

- **System/meta‑prompt as guardrail**:
  - The system prompt acts as the primary **guardrail document**, encoding:
    - The allowed tools (e.g., `context`, `LLM_query`, `print`).
    - The intended behavior (interactive analysis, recursion, code‑first interaction with context).
    - Examples that demonstrate good patterns (e.g., regex filtering, chunk‑based reasoning).[1]
- **Environment constraints**:
  - Guardrails are enforced via:
    - The environment API: the LM cannot directly access the full raw context; it must go through code that the host executes.
    - Token limits on each sub‑call, which implicitly block the LM from constructing oversized prompts.[1]
- **Verification passes**:
  - In the multihop example, the root LM:
    - Uses additional recursive calls as verification steps before committing to an answer.
    - This acts as a soft guardrail against premature or hallucinated conclusions by requiring the model to re‑check its candidate answer against the context.[1]

***

## Practical recommendations

- Set up an **RLM environment** where:
  - The entire large corpus (e.g., multi‑million‑token codebase or document set) is stored in a `context` variable, and a root LM is only given a meta‑prompt plus the user’s query.[1]
- Use **one root LM and many implicit workers**:
  - Treat the root LM as an orchestrator that writes code, and treat each `LLM_query` call as a worker/“sub‑LM” operating on a chunk; design your framework so the root merges their outputs into the final response.[1]
- Add a **pre‑filtering phase**:
  - For large corpora, have the model first generate code that:
    - Uses regex and keyword filters to narrow down documents.
    - Only then launches recursive sub‑calls on the filtered chunks, to control cost.[1]
- Keep sub‑call contexts in the **optimal range**:
  - Configure your environment so each `LLM_query` call is constrained to ~10k–20k tokens (or the sweet spot for your model) to avoid the performance drop associated with very long contexts.[1]
- Use the **system prompt as a central guardrail document**:
  - Centralize all behavioral principles (environment variables, tools, examples, recursion patterns) in a single system/meta‑prompt, and reuse it for every RLM process so behavior is consistent and predictable.[1]
- Implement **verification passes** for high‑stakes queries:
  - Instruct the root LM (via examples in the meta‑prompt) to:
    - Re‑check its candidate answer with one or more additional recursive calls before finalizing.
    - Only return an answer after consistency checks across multiple sub‑calls.[1]
- Monitor and manage **cost and recursion depth**:
  - Add metrics and logging to your RLM host so you:
    - Track how many sub‑calls a query generates.
    - Identify patterns where the model over‑recurses and adjust examples/system prompts to encourage shallower but more targeted plans.[1]
- Enable **trace visualization**:
  - Configure the JSON trace output and visualization tool so you can inspect:
    - How the model chunked the context.
    - Which filters it used.
    - How it merged intermediate results.
  - Use these traces to refine your system prompt and examples for better future runs.[1]

## Human

construct the prompting required and optimal for this solution, and any pseudo code you think is helpful to understanding and implementing.

## Assistant

Perfect! Let me create one final index file:

```markdown
# 📚 RLM Package Contents & Navigation

Complete Recursive Language Models implementation package with guides, code, and examples.

## Quick Navigation

### 🚀 Getting Started (Start Here)
- **[README.md](README.md)** — Overview, architecture, quick stats
- **[RLM_QUICK_START.md](RLM_QUICK_START.md)** — 5-minute setup, basic usage, examples

### 💻 Implementation
- **[rlm_implementation.py](rlm_implementation.py)** — Core code, copy to your project
  - RLMEnvironment class
  - CodeAnalysisRLM, VideoMetadataRLM, DocumentSearchRLM
  - Multi-provider support (OpenAI, Groq, Anthropic)
  - Cost tracking, tracing, debugging

### 📖 Guides & References
- **[rlm_prompting_guide.md](rlm_prompting_guide.md)** — Complete prompting guide
  - Part 1: System Prompt Architecture
  - Part 2: Meta-Prompt Configuration
  - Part 3–5: Implementation pseudo-code
  - Part 6–8: Real-world workflows and optimization
  - Part 9: Quick reference checklist
  
- **[RLM_PROMPT_SELECTION_TREE.md](RLM_PROMPT_SELECTION_TREE.md)** — Decision tree + templates
  - Decision tree for choosing prompts
  - 5 production-ready templates:
    1. Security code analysis
    2. Performance code analysis
    3. Advanced video search
    4. Log analysis & RCA
    5. Data analysis & insights
  
- **[rlm_claude_code_integration.md](rlm_claude_code_integration.md)** — Claude Code integration
  - Hook implementation (on_ai_message.py)
  - Slash commands (/rlm)
  - Multi-agent orchestration
  - Workflow examples
  - Testing & debugging

## By Use Case

### 🔐 Code Security & Analysis
1. Read: `RLM_QUICK_START.md` → "Use Cases: A. Code Analysis"
2. Reference: `rlm_prompt_selection_tree.md` → "Template 1: Security-Focused"
3. Implement: `rlm_implementation.py` → CodeAnalysisRLM class
4. Integrate: `rlm_claude_code_integration.md` → Hook 1

### 🎥 Video & Transcript Search
1. Read: `RLM_QUICK_START.md` → "Use Cases: B. Video/Transcript"
2. Reference: `RLM_PROMPT_SELECTION_TREE.md` → "Template 3: Advanced Video"
3. Implement: `rlm_implementation.py` → VideoMetadataRLM class
4. Integrate: `rlm_claude_code_integration.md` → Hook 2

### 📄 Document Search & Analysis
1. Read: `RLM_QUICK_START.md` → "Use Cases: C. Document Search"
2. Reference: `rlm_implementation.py` → DocumentSearchRLM class
3. Customize: `RLM_PROMPT_SELECTION_TREE.md` → Use templates
4. Integrate: `rlm_claude_code_integration.md` → Multi-agent patterns

### 📊 Custom Domain Analysis
1. Read: `rlm_prompting_guide.md` → "Part 2: Meta-Prompt Configuration"
2. Choose: `RLM_PROMPT_SELECTION_TREE.md` → Relevant template
3. Customize: Adapt system prompt for your domain
4. Test: `RLM_QUICK_START.md` → "Troubleshooting"

## Learning Path

### 5 Minute Version
1. `RLM_QUICK_START.md` (entire document)
2. Run the test script in your terminal
3. Check the cost report

### 30 Minute Version
1. `README.md` (sections: "What is RLM?" through "Real-World Example")
2. `rlm_implementation.py` (read the class definitions, skip implementation details)
3. `RLM_QUICK_START.md` (entire document)
4. Try a basic example

### 2 Hour Deep Dive
1. `README.md` (entire document)
2. `RLM_QUICK_START.md` (entire document)
3. `rlm_prompting_guide.md` (Parts 1–5, skip pseudo-code)
4. `RLM_PROMPT_SELECTION_TREE.md` (decision tree + 2 templates relevant to you)
5. `rlm_claude_code_integration.md` (Hooks section)
6. Implement a custom example

### Complete Mastery
1. Read all documents in order
2. Study `rlm_implementation.py` line-by-line
3. Implement multi-agent workflow from `rlm_claude_code_integration.md`
4. Create custom prompts from `RLM_PROMPT_SELECTION_TREE.md`
5. Monitor costs and optimize based on your usage

## File Statistics

| File | Lines | Purpose |
|------|-------|---------|
| `README.md` | 636 | Overview, architecture, FAQ |
| `RLM_QUICK_START.md` | 497 | 5-minute setup guide |
| `rlm_implementation.py` | 722 | Core implementation |
| `rlm_prompting_guide.md` | 1,017 | Complete prompting guide |
| `RLM_PROMPT_SELECTION_TREE.md` | 633 | Decision tree + templates |
| `rlm_claude_code_integration.md` | 812 | Claude Code integration |
| **Total** | **4,317 lines** | Complete production system |

## Key Concepts

### Core Concepts
- **RLM**: Treat context as a Python variable the LLM writes code to explore
- **System Prompt**: Teaches LLM the RLM paradigm
- **REPL**: Python environment with context pre-loaded
- **PEEK → GREP → PARTITION → DELEGATE → MERGE**: The RLM strategy

### Implementation Concepts
- **RLMEnvironment**: Main class that orchestrates the loop
- **LLMClient**: Abstract interface for different LLM providers
- **Domain Subclasses**: CodeAnalysisRLM, VideoMetadataRLM, etc.
- **Cost Tracking**: Monitor and limit expenses
- **Tracing**: Debug and visualize RLM execution

### Integration Concepts
- **Hooks**: on_ai_message.py → intercept Claude Code messages
- **Slash Commands**: /rlm → custom commands
- **Multi-Agent**: Coordinate multiple agents via RLM
- **Workflows**: End-to-end analysis pipelines

## Typical Workflow

### Setup (First Time)
```
1. pip install openai
2. export OPENAI_API_KEY="..."
3. cp rlm_implementation.py ~/my-project/utils/
```

### First Analysis
```
1. Read: RLM_QUICK_START.md
2. Create: test_rlm.py with basic example
3. Run: python test_rlm.py
4. Check: Usage report
```

### Production Deployment
```
1. Reference: RLM_PROMPT_SELECTION_TREE.md (choose template)
2. Customize: System prompt for your domain
3. Integrate: Add hook to Claude Code
4. Monitor: Track costs and results
5. Optimize: Refine prompts based on actual usage
```

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| "Can't find module" | Run: `pip install openai` |
| "API key error" | Check: `export OPENAI_API_KEY="..."` |
| "Cost too high" | Use: `model="gpt-5-mini"` instead of "gpt-5" |
| "LLM not writing code" | Clarify in system prompt: "You MUST write Python code" |
| "Results incomplete" | Add verification steps to query |
| "Max iterations reached" | Simplify query or clarify instructions |

See `RLM_QUICK_START.md` → Troubleshooting for details.

## Next Steps

1. **Choose Your Path**:
   - 5 min: `RLM_QUICK_START.md` only
   - 30 min: Add `README.md`
   - 2 hours: Add implementation & prompting guides
   - Mastery: Study all files + code

2. **Implement**:
   - Copy `rlm_implementation.py`
   - Run basic test
   - Customize for your use case

3. **Integrate**:
   - Add Claude Code hook
   - Test with /rlm command
   - Monitor costs

4. **Optimize**:
   - Review traces
   - Refine prompts
   - Scale to larger contexts

---

**Ready? Start with [RLM_QUICK_START.md](RLM_QUICK_START.md)! 🚀**
```

Let me save this as an index file:
