---
title: "Intro
[(00:00:00)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=0) So, one of the big trends that we're seeing at the m"
date: "2026-01-07"
mode: "COPILOT"
uuid: "f188d53b-6cb7-4761-831d-048d134da32a"
entry_count: 1
---

## Human

Intro
[(00:00:00)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=0) So, one of the big trends that we're seeing at the moment is this movement away from very specialized agents to [(00:00:07)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=7) sort of more generalized agents and this has been going on for a while. The challenge is it's basically been limited [(00:00:16)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=16) to models up until recently. So in this video I want to look at mirrorinker
MiroThinker Blog
[(00:00:21)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=21) which is an open model with an MIT license that is built for this sort of AI research agent use. And it's not [(00:00:30)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=30) actually the first version of this model that they made. This is actually a new set of models that has just come out a [(00:00:36)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=36) couple of days ago that focuses on the whole idea of getting a model to team up with a certain set of tools or MCPs and [(00:00:46)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=46) then being able to have it do many steps to actually go through. So that could be multiple searches using the information [(00:00:54)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=54) gets back with other tools then using that to do more searches to doing a whole bunch of different things. And the [(00:01:02)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=62) key idea here is that if you've got a model that can use lots of different tool calls, and this model is claiming [(00:01:10)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=70) that it can go out to 400 tool calls, then the goal is that you should be able to have something that can do a whole [(00:01:18)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=78) bunch of different tasks from not just things like research, but things that could generate a whole bunch of [(00:01:24)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=84)
highquality outputs. Whether that could be a slide deck, a report hooked up to audio to make a podcast like notebook LM [(00:01:33)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=93) etc. All of these things require highquality thinking about what information the system actually has [(00:01:39)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=99) already and what tools does it have that it can use to use this information to perhaps find more information and then [(00:01:46)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=106) work on that output. So this idea is not new per se, right? We've even seen it with open models. So for example, one of [(00:01:54)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=114) the models that I really like a lot that's actually been very good at this are the Kimmy K2 models or specifically [(00:02:01)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=121) the Kimmy K2 thinking model. The challenge there is that you're talking about a trillion parameter model, right? [(00:02:08)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=128) That's a huge model. Uh it's not something that you can easily run locally. It's not something that you can [(00:02:13)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=133) easily It's not something that you can easily run cheaply. The thing that sets
MiroThinker Models
[(00:02:17)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=137) Mirror Thinker 1.5 apart from that is that we've got two models here. Both of them trained off the Quen mixture of [(00:02:27)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=147) experts base models. So the big one is the Mirror Thinker 235B. So that's got 22 billion parameters active. And then [(00:02:35)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=155) the smaller one is the 30B with 3 billion parameters active. Now, both of these models have been improved from the [(00:02:45)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=165) original Quen 3 base models to be able to do these max tool calls, etc. So, the models have a max context of 256,000 [(00:02:54)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=174) tokens, and they're supposed to be able to go out to 400 tool calls. Now, I've yet to see any model go out to 400 tool [(00:03:02)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=182) calls in a elegant way where it can actually not just end up going into loops and repeating itself, etc. But [(00:03:09)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=189) this model certainly can be used for doing lots of tool calls. So this whole element reinforces what we're seeing [(00:03:17)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=197) more and more of moving away from just a big model that has lots of information into it to moving towards models that [(00:03:27)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=207)
can do lots of tool calls, use lots of tools for both research but also for generating outputs and do that in a [(00:03:35)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=215) fully agentic way. So if we have just a
Benchmarks
[(00:03:38)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=218) very quick look at their benchmarks here, we can see that their models are comparable against models that are much [(00:03:45)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=225) bigger than this for these particular kinds of benchmarks that require a very high level of tool use etc. And we can [(00:03:53)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=233) see even in many of them where they're not state-of-the-art, for example, the humanities last exam here, we can see [(00:04:00)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=240) that the bigger model is not that far behind Gemini 3 Pro in here and even closer with GBT5's highlevel model and [(00:04:11)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=251) the GLM 4.7 models. And sure enough, they've got some benchmarks for browsers, etc. where they are actually [(00:04:18)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=258) the state-of-the-art model. For me, that's actually not that important. I think nowadays any company can really [(00:04:23)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=263) hill climb on a particular benchmark to get something that's state-of-the-art. Really what I'm more interested in is [(00:04:30)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=270) overall how are they comparing to other models that are out there. And you can see sure enough the mirror thinker [(00:04:36)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=276)
models both the big one and even the 30B one actually compare quite well to things like DeepSync V 3.2, to the [(00:04:46)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=286) miniax models and things like the GLM and the Kimmy K2 thinking models. So if we look at how these actually work, we [(00:04:54)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=294) can see the tool interfaces that they've got here for doing things like creating sandboxes to run code, file management, [(00:05:01)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=301) being able to do information search retrieval, being able to search the web, etc. Being able to pull things in and [(00:05:08)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=308) then obviously to be able to do this with a very long number of steps, they need to be able to handle the context [(00:05:13)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=313) management as well. So we can see here dealing with the different context retention working out when to truncate [(00:05:21)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=321) results out etc. And you can see you're going to get something like this where you start off with something where okay [(00:05:28)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=328) you've got a user question you've got the assistant doing thinking tool calls tool results perhaps more thinking etc [(00:05:35)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=335)
as it goes through and this recency based context retention here will work out what to actually cut out of the [(00:05:43)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=343) context. So this is a similar thing to the way a lot of the memory systems out there are working and things like [(00:05:50)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=350) compaction on code tools etc. And this whole idea of trying to bake this into a system definitely seems to be the way [(00:05:56)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=356) going forward. We're already seeing Anthropic do this with the claude models and claude code. We're seeing [open AI](https://app.getrecall.ai/item/466b4e3f-51d0-4b30-a203-01d677a357a7) do [(00:06:03)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=363) it. We're even starting to see some examples of Google doing it for some of their products. And the big challenge is [(00:06:10)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=370) we want to be able to do this locally, right? We want to have models that we can run locally that can do a whole [(00:06:16)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=376) bunch of these different things. And this is where this 30B mixture of experts model which is based on one of [(00:06:22)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=382) the Quen 3 models really seems to shine for me. So currently there isn't a paper out for the 1.5 version. But if we look [(00:06:30)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=390)
at the paper for the 1.0 version, we saw that they basically take these pre-trained models. They do SFT on them. [(00:06:36)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=396) They do some alignment training with DPO. They also do some RLVR or reinforcement learning with verifiable [(00:06:43)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=403) rewards via using GRPO. And the idea here is that you can get these models to be able to actually make the right [(00:06:50)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=410) decision with the right tool at the right time. And that's the whole goal here. So let's jump into a notebook and [(00:06:57)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=417) have a look at how it actually works.
Colab Demo
[(00:06:59)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=419) Okay, so to run this model at full resolution, you're going to need a pretty big GPU. I'm using an A100 with [(00:07:06)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=426) 80 gig of RAM here. You probably can get away with something a bit smaller than that, but you're going to still find [(00:07:13)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=433) that this model definitely uses a lot of GPU RAM. The other thing that's different in this notebook is rather [(00:07:18)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=438) than do it through the transformers library, I'm actually running it as a VLM server. This is so that we can [(00:07:25)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=445) actually use it as an [open AI](https://app.getrecall.ai/item/466b4e3f-51d0-4b30-a203-01d677a357a7) configured model. Not that we're using OpenAI or anything like that. What I mean is that [(00:07:31)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=451) we're actually using the OpenAI API and VLM has that built in by default. So we can actually just spin this up and then [(00:07:38)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=458) we can just make API calls to it and we'll be able to use the OpenAI package etc to call it. It will then handle the [(00:07:46)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=466) function calling in that way. Now actually loading this model up takes quite a bit of time. The weights are [(00:07:53)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=473)
quite big. It's got a download etc. So you will find that you're sitting there for quite a few minutes while it's [(00:07:59)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=479) actually just really just downloading the weights. All right. Then they've got a bunch of tools that you can set up for [(00:08:05)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=485) this. So you can just use something like duck.go search for the searching. That's going to be free. You need a fetch a web [(00:08:12)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=492) page tool for this. You can just use requests and beautiful soup. Still these oldfashioned things actually work very [(00:08:17)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=497) well. Now if you wanted to, you can actually sort of improve the tools when you're getting something back. You [(00:08:23)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=503) actually clean it up before you give it to the model, etc. But these basic ones work quite fine. We've got some [(00:08:29)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=509) calculate tools. We've got stuff for running [Python](https://app.getrecall.ai/item/f64dd8fe-1a3c-4443-90b4-8da83e0168d3) code, stuff for getting dates, etc. And then we can basically [(00:08:36)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=516) just define all of those tools to pass them in. We've got some code in here for testing the tools to see do they work. [(00:08:43)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=523)
Sure enough, we can see that the web search stuff is coming back with two results. In this case, uh our calculator [(00:08:49)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=529) is working, our datetimes working. Now, we can set up the sort of toll cooling loop in a sort of MCP way. So, [(00:08:56)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=536) basically, it's got a bunch of stuff in here for doing that. We've also got our prompts that we're going to pass in. [(00:09:02)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=542) We've got some functions for actually passing the tool calls as they come back. And then we can set up an agent [(00:09:08)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=548) loop, etc. in here. Now, the Agentic stuff is doing it all from scratch. We're not using any sort of framework [(00:09:14)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=554) like Langchain or something like that. I think in theory, you probably could use that. I do think we're going to see more [(00:09:20)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=560) and more though that people optimize a harness specifically to match a model or specifically to match a sort of family [(00:09:28)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=568) of models. We're seeing some things like that already from Quen agent. But in this one, there's really nothing special [(00:09:35)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=575)
in there. We just got simple calls, simple prompts for doing this. How to deal with tool calls, how to deal with [(00:09:41)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=581) things coming back. All right, then we can just basically run the agent and kick things off. And you can see sure [(00:09:47)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=587) enough we're going to ask it some math stuff first. And we can see that we've got thinking tokens of what it actually [(00:09:53)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=593) needs to do. So it's working out what tools. We can then see that okay it's going to use the calculate tool. What's [(00:10:00)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=600) it going to pass in there? And we get results back. Finally in this case it then uses some other tools before doing [(00:10:07)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=607) a sort of web search and coming back. And this is one of the challenges that I find with these kind of systems is you [(00:10:13)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=613) often it will get to the right answer but then how many steps did it take and were all the steps actually related to [(00:10:21)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=621) getting that final answer. So this is where you often want to build some of your own evals for testing this kind of [(00:10:28)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=628)
thing out. So next up we've got a web research task. You can also see here we're passing in the maximum number of [(00:10:34)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=634) iterations of how many steps can it go. And so here you can get it to do multiple calls on this. We can see here [(00:10:42)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=642) it's found the [hugging face](https://app.getrecall.ai/item/ddb28a84-2478-43b9-8eab-bb2c8e1912d5) page. It's found a bunch of different things. It thinks to itself about that. It then [(00:10:48)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=648) goes to the web page fetch tool to actually go and get each of those pages. And we can see in this particular case [(00:10:56)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=656) it actually reach the max iterations. Right? Because we were asking it to fetch multiple pages. Each of those is a [(00:11:03)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=663) different tool call. So in this case, we actually never got to the final answer out. Now you can get to much more sort [(00:11:10)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=670) of interesting things of where you've got these multiplestep research things. And this is where often one of the sort [(00:11:17)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=677) of deep research things. What they'll do is have one prompt that will write a plan like this of I need to do this, I [(00:11:25)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=685)
need to do that, I need to do this, and then pass it into the agent with lots of tools to actually go through this. And [(00:11:31)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=691) we can see that's what's going on here. So we can see the user wants to understand it. It goes through it. It's [(00:11:36)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=696) decided that it's going to go for a big search here. It's going to get the results back from that. We've got some [(00:11:43)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=703) warnings in there. And it's good to see things like this where it is aware that some of the things coming back are [(00:11:50)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=710) irrelevant. So it should discard those. That's been one of the problems in the past is that agents would actually just [(00:11:57)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=717) go and do a search and then they would just take everything at sort of face value and feel that they had to use [(00:12:03)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=723) everything even though the large chunks of it were irrelevant. This is something where getting better quality models [(00:12:10)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=730) allows us to get better quality results. And in this case, I would say that the model actually hasn't done a great job, [(00:12:15)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=735)
right? It has seems to have been influenced by a lot of different things. and then either because we haven't given [(00:12:22)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=742) enough steps, it's running out of steps of where it hasn't been able to follow through on this. Now, if we want to get [(00:12:28)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=748) better results, often what we're going to need to do is actually just give it a lot more max iterations for the tools, [(00:12:35)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=755) etc. So, you can see here in this one, I'm asking it what is current date and time and what day of the week is it in [(00:12:40)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=760) Singapore? And in this case, the actual server is not running in Singapore. It's running in the cloud somewhere. So it's [(00:12:48)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=768) got to work out, okay, what can it do? So it's got a current datetime tool and a lot of the times these things would [(00:12:55)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=775) just go ah well that's the date I'll return that. But this thing is working out that oh okay this is not actually [(00:13:01)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=781) the time in Singapore right that this is the UTC time and it will actually go through and run different things. Now, [(00:13:08)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=788)
I'm not sure if this is because of the model or because of the prompt where sometimes it will start to go into [(00:13:14)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=794) Chinese results and stuff like that. In this case, it actually goes through does get a number of results back. And I can [(00:13:21)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=801) see that as I'm recording this, this is actually correct. It's found the right date, the right time, that kind of [(00:13:27)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=807) thing. But the fact that it's taken nine iterations or nine steps of tool calling and stuff like that to get that result [(00:13:34)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=814) is not ideal. And this sort of shows where things are and what a challenging problem this still is, especially when [(00:13:42)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=822) you're trying to do it with smaller models. But overall, this does seem to finally get to the right answers for [(00:13:48)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=828) lots of things. And my guess is that if you're running it locally, and you perhaps don't need everything real time, [(00:13:55)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=835) this is possibly going to be really useful for doing lots of different tasks. Now, one of the big things that I [(00:14:01)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=841)
do wonder is if we were to swap this out, because basically this model is just the equivalent of the Quen 330B [(00:14:09)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=849) A3B, this model here, if we were to swap this out for an [MLX](https://app.getrecall.ai/item/64c5884d-44e4-4afd-8c10-e5c0ba2280b9) 4bit version or something like that, how much would we [(00:14:17)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=857) actually lose of the reasoning qualities? So, for a long time, people thought, including myself, that once [(00:14:24)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=864) you're going down to 4bit, you're losing too much precision on the model. and will it affect it? But over the past [(00:14:30)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=870) couple of years with all the quantizations coming out, this has been shown to not necessarily lose as much as [(00:14:36)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=876) we perhaps thought you would at the start. So if someone were to actually make MLX 8bit or 4-bit versions of [(00:14:44)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=884) these, they could actually work very well with this harness and something like Llama CPP or LLM Studio, etc. Now,
Online Demo
[(00:14:52)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=892) if you want to try the model out, they've also got an online demo where you can actually come and play with it [(00:14:56)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=896) yourself. you don't have as much access to the actual tools and stuff like that, but you can see what the model's [(00:15:02)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=902) actually doing. And my guess is that this is actually the bigger version of the model, not the version that I used [(00:15:08)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=908) in Collab, which was the smaller version of the model. And you can see that pretty quickly just by the longer [(00:15:12)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=912) thinking that we're getting in there. You can see in this case, it's gone and done a bunch of searches, it's found a [(00:15:17)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=917) bunch of websites, it's pulling it back,
MiroThinker Hugging Face
[(00:15:20)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=920) etc. So if you are looking for something that can do long both thinking and long chains of tool calling but be a small [(00:15:28)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=928) model, this is definitely worth checking out and just seeing how it works out for your particular use case. Anyway, as [(00:15:35)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=935) always, let me know what you think in the comments. I'm very interested to see are people actually looking to run these [(00:15:40)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=940) kinds of models locally and what are the use cases that you're trying to do locally with this kind of model. Anyway, [(00:15:47)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=947) as always, if you found the video useful, please click like and subscribe, and I will talk to you in the next [(00:15:51)](https://www.youtube.com/watch?v=gY22nDIGdPs&t=951) video.
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

## Assistant

MiroThinker 1.5 – distilled technical workflow notes
====================================================

## Core model characteristics

- MiroThinker 1.5 is an open, MIT‑licensed “research agent” model family, designed for heavy tool use and long, multi‑step workflows rather than just static question answering.[1][2][3]
- Two main mixture‑of‑experts (MoE) variants are discussed:  
  - **MiroThinker‑v1.5‑235B**: Qwen‑based MoE with ~235B total parameters, ~22B active per token.[2][3][1]
  - **MiroThinker‑v1.5‑30B**: Qwen‑3‑30B‑based MoE with ~30B total, ~3B active per token; positioned as the “local‑friendly” option.[3][1]
- Both variants expose:  
  - 256k token context window.[2][3]
  - Training specifically to support deep tool‑augmented reasoning with up to ~400 tool calls per task (v1.0 paper shows 600‑call capability; v1.5 marketing emphasizes 400).[4][5][6][2]

## Training and alignment stack

- Base: Qwen 3 MoE models (e.g., Qwen3‑30B‑A3B‑style for the 30B variant).[1][3]
- Post‑training pipeline (known from the 1.0 paper and implied for 1.5):[5][6][3]
  - Supervised finetuning (SFT) on tool‑use and research‑style data.  
  - Alignment via DPO (Direct Preference Optimization).  
  - RLVR / GRPO‑style reinforcement learning with verifiable rewards, optimizing whether the model picks the *right tool at the right time* and follows correct tool‑use trajectories.  

## Intended usage pattern

- Designed to operate as a **tool‑calling research agent**:  
  - Handles multi‑step search and retrieval (multiple web searches, then fetches the found pages, then re‑queries based on new information, etc.).[3][2]
  - Intended for long‑horizon tasks such as deep web research, report generation, slide decks, or podcast‑like scripted outputs (similar to NotebookLM‑style workflows).[1][3]
- Emphasizes a shift from:  
  - “Just a big monolithic model with lots of knowledge” → smaller MoE models that are trained to **orchestrate tools** heavily (search, scraping, code execution, file I/O, etc.).[2][3][1]

## Benchmark takeaways

- On tool‑heavy and research‑style benchmarks (HLE, BrowseComp, BrowseComp‑ZH, GAIA variants):  
  - v1.5 models are reported to match or beat much larger proprietary models (e.g., Gemini 3 Pro, GPT‑5‑level “high‑tier” models, GLM 4.7, Kimmi K2 Thinking) in those specific tool‑use benchmarks.[7][8][3][1][2]
  - On more general exams (e.g., humanities “last exam”‑type benchmarks), the 235B model is close to but not SOTA vs latest closed models, yet competitive given its size.[3][1]
- Some browser / search benchmarks show v1.5 as SOTA among open agents, but the presenter notes this can be hill‑climbed and cares more about overall behavior across many tasks.[7][1][3]

## Tooling surface and MCP‑style integration

- Tool types in the reference harness / notebook:[9][3]
  - Web search (e.g., DuckDuckGo or Serper‑backed google_search).  
  - Webpage fetch / scrape (e.g., requests + BeautifulSoup; or a jina_scrape_llm_summary‑style tool).  
  - Calculators and numeric utilities.  
  - Datetime / timezone utilities.  
  - Python code execution in sandboxes (create_sandbox, run_python_code).  
  - File management and basic FS operations for research artifacts.  
- Tool protocol in the 1.0 paper is MCP‑style:  
  - A generic `use_mcp_tool` wrapper with parameters: `server_name`, `tool_name`, `arguments` (JSON).  
  - Single tool per message, tool call markup at the **end** of the assistant’s message in `<use_mcp_tool>...</use_mcp_tool>` tags.[6][9]
- The demo harness shown in the video and in docs builds an **agent loop** from scratch rather than using LangChain:  
  - Custom prompt templates for tool‑use instructions and system role.  
  - A central loop that:  
    - Sends the current state + available tools to the model.  
    - Parses tool calls from the response.  
    - Executes the corresponding Python functions (search, scrape, calc, etc.).  
    - Appends tool results to the context.  
    - Iterates until a stop condition (max iterations or final answer string).[9][3]

## Context and memory handling

- The model expects long interaction histories and uses **recency‑based context retention** as described in the 1.0 paper:[5][6][3]
  - Older, less relevant tool results are truncated.  
  - Recent steps and key intermediate results are preferentially retained.  
- Behavior is analogous to modern memory / compaction systems used in proprietary agents (e.g., compaction of old tool outputs, code‑compaction in coding agents).[6][5][3]
- The harness treats the full interaction as:  
  - User question → thinking tokens → tool calls → tool results → more thinking → final answer, with automatic pruning of obsolete context as steps grow.[5][6][3]

## Observed behaviors and failure modes in demos

- The model **can** execute many tool calls, but:  
  - Long chains risk loops, self‑repetition, or running out of iteration budget before producing a final answer.[3][5]
  - Example: a multi‑page fetch research task hits max iterations (due to fetching each result as a separate tool call) and never produces a synthesized answer.[3]
- Tool‑efficiency vs correctness tradeoff:  
  - In simple tasks (e.g., “current date and time in Singapore”), the model eventually gets the correct local time via several steps: call current datetime, reason about UTC vs Singapore, search the web, cross‑check, etc.[3]
  - However, it may use 9+ iterations for something a specialized tool or a more structured agent could do in 1–2 calls, highlighting inefficiency when left unconstrained.[3]
- Relevance filtering:  
  - On some deep‑research prompts, the model recognizes irrelevant search results and explicitly discards them instead of blindly incorporating everything.[3]
  - Despite that, the presenter notes some runs where the final synthesis is weak or muddled, especially when iteration budget is too small for the complexity of the search tree.[3]

## Local vs cloud usage and quantization

- Full‑precision 235B and 30B MoE variants are heavy:  
  - Example demo uses an 80 GB A100 to run the model at full resolution as a server.[2][3]
  - Loading and initializing weights takes several minutes; GPU memory usage is substantial.[2][3]
- The demo runs MiroThinker as an **OpenAI‑compatible VLM server**:  
  - Exposes OpenAI‑style `/v1` endpoints so the standard `openai` Python SDK and function‑calling interface can be used.[9][2][3]
  - The local harness sends OpenAI‑style function/tool definitions and receives function call entries, which the Python loop executes.  
- Presenter explicitly speculates about **4‑bit / 8‑bit MLX or llama.cpp quantized versions** of the Qwen‑3‑30B base:  
  - Historically, 4‑bit quantization was assumed to destroy reasoning, but recent quant schemes show much smaller degradation than expected.[4][3]
  - The suggestion is that an MLX 4‑bit or 8‑bit build, wired into the same tool harness, could be a strong local agent with manageable hardware needs (e.g., high‑end consumer GPUs or Apple Silicon).[4][3]

## Alternative models and relatives

- Kimmi K2 “Thinking” models:  
  - Strong at multi‑step tool‑use but sit at ~1T parameters, making them expensive and hard to run locally.[3]
- Other open research agents mentioned as comparison points:  
  - DeepSeek V3.2, MiniMax/Miniax models, GLM series, Kimmi K2 Thinking.[10][1][3]
- The shift is framed as: **interactive scaling** along three axes—model size, context length, and interaction depth (number of tool calls)—rather than just scaling parameters.[6][4][5]

***

Operational patterns and setups
===============================

### Multi‑entity flows (models, tools, servers)

- **Model ↔ VLM server ↔ tools loop**:  
  - Start a VLM server hosting MiroThinker‑v1.5 (e.g., 30B) with an OpenAI‑compatible API.[9][2][3]
  - Use the OpenAI Python SDK to send:  
    - System prompt: describes tool‑use rules and MCP `use_mcp_tool` schema.  
    - Tool definitions (search, scrape, calc, datetime, Python sandbox, file ops).[9][3]
  - The model emits one tool call per message using `<use_mcp_tool>` markup that references:  
    - `server_name` (e.g., `search_and_scrape_webpage`, `tool-python`).  
    - `tool_name` (e.g., `google_search`, `scrape_and_extract_info`, `create_sandbox`, `run_python_code`).  
    - `arguments` JSON.[6][9]
  - A Python orchestrator parses the tool call, routes it to the correct MCP server or local function, captures output, appends results into the growing conversation, and re‑invokes the model.[9][3]

- **Search → scrape → synthesize pattern**:  
  - Model first calls a web search tool (DuckDuckGo/Serper) to get a list of candidate URLs and snippets.[9][3]
  - Then, for selected URLs, it calls a web‑fetch or scrape tool to pull full content or LLM‑summarized content.[9][3]
  - Finally, it performs internal “thinking” tokens and produces a synthesized textual answer, possibly after multiple rounds of extra searching and scraping when gaps are detected.[4][5][3]

- **Planning prompt → agentic execution**:  
  - A higher‑level prompt is sometimes used to first produce a plan: an ordered list of sub‑tasks and queries needed for the research task.[6][3]
  - That plan (or a compressed representation) is then fed back to the same agent with tools enabled; the agent executes each planned step via multiple tool calls.[6][3]

- **Python sandbox integration**:  
  - The tool suite includes `create_sandbox` and `run_python_code` on a `tool-python` server.[9]
  - The model:  
    - Calls `create_sandbox` once to obtain a `sandbox_id`.  
    - Reuses that `sandbox_id` with `run_python_code` for successive code execution steps (e.g., computation, parsing, transformation), reducing setup overhead.[9]

### Automation patterns (loops, budgets, constraints)

- **Agent loop with max‑iteration budget**:  
  - The orchestrator enforces a `max_iterations` (step count) per user query.[5][3]
  - Each tool call or reasoning step consumes iterations; if max is reached before a final answer is produced, the run terminates without a conclusive result (as shown in the multi‑page fetch example).[3]
- **Recency‑based context pruning**:  
  - As the total token length approaches the 256k limit, older tool outputs and intermediate reasoning are truncated based on recency and (potentially) heuristic importance, leaving recent, relevant content in the active context.[5][6][3]
- **“Think then act” for simple queries**:  
  - Even for simple tasks like timezone conversion, the model is allowed to “think” and chain tools:  
    - Call datetime tool → reason about timezone offset → optionally call web search to confirm.[3]
  - This improves robustness but at the cost of multiple steps; an operator can reduce unnecessary depth by tightening iteration limits or providing specialized tools.  

### Guardrail artifacts (prompts, configs, policies)

- **System prompt as primary guardrail** (from v1.0 paper):[6][9]
  - Specifies:  
    - Only use listed tools via `use_mcp_tool`.  
    - Only one tool call per message.  
    - Tool call must appear at the end of the message, top‑level.  
    - Arguments must be valid JSON, properly escaped.  
    - Interactions should be step‑by‑step, with each tool use informed by previous results.  
  - This prompt effectively encodes:  
    - How to format tool calls (syntax constraints).  
    - When and how often tools may be used (one per turn).  
    - The expectation of iterative decomposition and environment feedback (“interactive scaling”).  
- **Iteration and context configs as operational guardrails**:  
  - `max_iterations` per task caps depth to avoid infinite or excessively long tool loops.[5][3]
  - Context management policy (recency‑based retention) avoids unbounded growth and keeps the agent from being overwhelmed by obsolete data.[5][6]

***

Practical recommendations
=========================

- **Set up an OpenAI‑compatible MiroThinker server**  
  - Host MiroThinker‑v1.5‑30B (or 235B if you have sufficient GPU) behind an OpenAI‑style `/v1` API endpoint (e.g., via the provided VLM server or similar).[2][9][3]
  - Use the official 1.0 system prompt style to enforce `use_mcp_tool` formatting and one‑tool‑per‑message behavior.[6][9]

- **Define a focused but extensible tool suite**  
  - Start with:  
    - `google_search` (or DuckDuckGo search) for web queries.  
    - `scrape_and_extract_info` for scraping and summarization.  
    - `create_sandbox` + `run_python_code` for code and data work.  
    - Simple calc and datetime tools.  
  - Implement them as MCP servers or directly in your Python orchestrator, mapping tool names to actual functions.[9][3]

- **Implement an explicit agent loop with budgets**  
  - Maintain an `iterations` counter per query; stop when `iterations >= max_iterations` (e.g., 10–40 for most tasks, more for deep research).[5][3]
  - On hitting the cap, return a partial answer summarizing what was learned and explicitly signal that the search was cut off.  
  - Log all tool calls and results to evaluate wasted steps and refine prompts/tools.  

- **Adopt recency‑based memory management**  
  - Track conversation items as typed entries (user messages, tool calls, tool results, model thoughts).  
  - When token limits approach, drop the oldest low‑relevance tool outputs and non‑critical “thinking” text, retaining:  
    - The original user ask and constraints.  
    - The most recent, high‑signal findings (scraped conclusions, key numeric results).[5][6]

- **Use a two‑phase “plan then execute” pattern for deep research**  
  - Phase 1: Ask the model (with tools disabled) to generate a structured research plan (sub‑questions, sources, validation checks).  
  - Phase 2: Feed the plan (or a summary) back to the tool‑enabled agent with a higher `max_iterations`, letting it follow the plan via search/scrape/code tools.[6][3]

- **Experiment with quantized variants when running locally**  
  - When community MLX or llama.cpp 4‑bit / 8‑bit builds appear, pair them with the same tool harness to reduce hardware requirements while monitoring any degradation in long‑horizon reasoning.[4][3]

- **Continuously evaluate tool‑use efficiency**  
  - For recurring tasks (timezone queries, standard lookups), measure:  
    - Steps taken.  
    - Tools invoked.  
    - Latency and cost.  
  - Where the agent uses too many steps, either:  
    - Add more specialized tools (e.g., direct timezone converter).  
    - Strengthen prompt instructions about using simpler or fewer tools for trivial tasks.
