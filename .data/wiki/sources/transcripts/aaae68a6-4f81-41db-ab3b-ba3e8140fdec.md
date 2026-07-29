---
source_id: "aaae68a6-4f81-41db-ab3b-ba3e8140fdec"
title: "Architecture Documentation"
notebook_id: 99725f7c-200c-4b4f-bf18-3fa3e2ae2633
url: https://surviving-software-architecture.ghost.io/architecture-documentation/
type: web_page
exported: 2026-07-28
---

# Architecture Documentation
Architecture Documentation

Surviving Software Architecture

https://surviving-software-architecture.ghost.io/

Home

https://surviving-software-architecture.ghost.io/

About

https://surviving-software-architecture.ghost.io/about/

RSS

https://surviving-software-architecture.ghost.io/rss/

Mastodon

https://discuss.systems/@mdepalol

Twitter

https://twitter.com/survsoftarch

Sign in

https://surviving-software-architecture.ghost.io/architecture-documentation/#/portal/signin

 

Subscribe

https://surviving-software-architecture.ghost.io/architecture-documentation/#/portal/signup

documentation

https://surviving-software-architecture.ghost.io/tag/documentation/

Architecture Documentation

A discussion about how technical documentation should be. Taking special interest in the architecture documentation.

Marc de Palol Martínez

https://surviving-software-architecture.ghost.io/author/marc/

28 May 2024

• 18 min read

 

Photo by 

Gabriel Sollmann

https://unsplash.com/@ccgabon?utm_source=ghost&utm_medium=referral&utm_campaign=api-credit

 / 

Unsplash

https://unsplash.com/?utm_source=ghost&utm_medium=referral&utm_campaign=api-credit

Why documentation is needed

https://surviving-software-architecture.ghost.io/architecture-documentation/#why-documentation-is-needed

Different types of documentation

https://surviving-software-architecture.ghost.io/architecture-documentation/#different-types-of-documentation

Technical documentation

https://surviving-software-architecture.ghost.io/architecture-documentation/#technical-documentation

Architecture documentation is the initial documentation.

https://surviving-software-architecture.ghost.io/architecture-documentation/#architecture-documentation-is-the-initial-documentation

My opinion on what's good architectural documentation

https://surviving-software-architecture.ghost.io/architecture-documentation/#my-opinion-on-whats-good-architectural-documentation

Problems with technical documentation

https://surviving-software-architecture.ghost.io/architecture-documentation/#problems-with-technical-documentation

Lack of documentation

https://surviving-software-architecture.ghost.io/architecture-documentation/#lack-of-documentation

Lack of updates

https://surviving-software-architecture.ghost.io/architecture-documentation/#lack-of-updates

Lack of Coherence

https://surviving-software-architecture.ghost.io/architecture-documentation/#lack-of-coherence

Lack of flow

https://surviving-software-architecture.ghost.io/architecture-documentation/#lack-of-flow

Why do these problems exist?

https://surviving-software-architecture.ghost.io/architecture-documentation/#why-do-these-problems-exist

How to fix technical documentation?

https://surviving-software-architecture.ghost.io/architecture-documentation/#how-to-fix-technical-documentation

Define what's coherence for you

https://surviving-software-architecture.ghost.io/architecture-documentation/#define-whats-coherence-for-you

Decide and invest in the tooling

https://surviving-software-architecture.ghost.io/architecture-documentation/#decide-and-invest-in-the-tooling

Automate

https://surviving-software-architecture.ghost.io/architecture-documentation/#automate

Ownership

https://surviving-software-architecture.ghost.io/architecture-documentation/#ownership

Use methodologies

https://surviving-software-architecture.ghost.io/architecture-documentation/#use-methodologies

Link everything

https://surviving-software-architecture.ghost.io/architecture-documentation/#link-everything

Cultural change

https://surviving-software-architecture.ghost.io/architecture-documentation/#cultural-change

Wishlist

https://surviving-software-architecture.ghost.io/architecture-documentation/#wishlist

I'm going to write, quite extensively, about technical and architecture documentation in this post and in more to follow. Not the sexiest of the topics, but hear me out, because I think it's crucial.

Documentation, and in more general terms Knowledge Management is a critical topic and it's something that is usually left out (the other being Security) from project roadmaps causing problems in the long run. Issues that could have been avoided.

⚠

This post is 

opinionated on my experiences documenting many

 different systems for different companies.

I've always received great feedback about them. This is the reason why I've decided to try to put all the knowledge together and write this piece.

Please, also note that this post is about internal technical documentation. I'm not writing about user-facing documentation here. It's related, but it has different implications. Content for another blog post I guess.

On the other hand, I 

would love

 to receive feedback, your experiences or your opinions on this topic. Please do not be shy and ping me on Mastodon or by email!

Let's start by discussing why we need to have documentation in a companyor project.

Why documentation is needed

People work on topics, they get knowledge based on experiences. This is the base of any enterprise, the knowledge and ability to do something better than the competitors. We don't want that knowledge to be solely in somebody's brain.

This is where documentation comes into play. Experts should write the knowledge down somewhere and share it with the rest of their peers.

The documentation is meant to be written and to be read. Sharing the knowledge with the rest of the interested parties is as important as to write it in the first place, and keep it updated.

Proper documentation helps newcomers to the company understand its objectives, its evolution, the roadmaps and the strategies. This is not only true for newcomers, but for any person who works in a company and needs to understand something about it.

With distributed teams, sometimes in different time zones, having documentation is mandatory. We cannot rely on 1-to-1, synchronous interactions to pass knowledge. This needs to be written down and available at all times.

Different types of documentation

A company will have different types of knowledge that need to be shared. Some examples:

Business documentation: How the company operates, information about the market, the products it develops, ...

Legal documentation: Policies, contracts with other companies and clients,

Vision and values: What the company stands for and what the objectives are.

Technical documentation: If it's a tech company there should be extensive documentation about how the company uses different systems to do work.

HR documentation: HR procedures, contracts, codes of conduct

...

Not surprisingly I'm going to focus here on Technical documentation. Let's forget about the rest for now. But hopefully, you get my point.

Technical documentation

There are lots of different types of Technical Documentation. Your typical examples include:

Comments in code.

README files in repositories.

Architecture diagrams.

Tech proposals.

Architecture Decision Records.

System usage, manual and daily operations.

...

As we can see, these docs provide information useful for different people (or roles) and they should have a different level of detail and a defined scope.

In my opinion, all of these types of documentation should exist, be extremely well defined, be linked and there should be one single entry point, which is the top-level documentation: the Architecture Documentation. Let's start from here.

Architecture documentation is the initial documentation.

💡

As defined in Wikipedia, the system architecture is:

" 

the conceptual model that defines the structure, behaviour, and more views of a system

".

This should be the first step when trying to understand a system.

When talking about the overall architecture we usually think of big complex diagrams. While it's true that we need and make heavy use of diagrams when explaining architectures we need more than this.

Architecture documentation should provide a big-picture view of the whole system. As such diagrams help a lot, it's just the initial. Architects need to provide a story that explains the diagrams and the context. Readers need to understand the whole architecture as it was explained as a story.

Computer systems are hard, and mature computer systems tend to do lots of different things. Before going deeper into the code, to the database tables, to the components interactions, to the events... we need to understand the basic use cases and organise a proper mental model so we don't get lost and miss important pieces.

The starting point of architecture documentation is a list of the main use cases that the company is solving. For each of these use cases, there's a diagram with a very high-view picture of the different system components (without technical details) and how they interact to solve the company objectives.

This allows us to have a quick and clear grasp of the amount of components that interact without getting lost in details.

Once we have this big picture view we need to understand how to get into the details step by step. Getting deeper without getting lost.

Let's give an example.

We writting some initial sketches of a documentation structure, with some example diagrams and explanations about a Ticketing company. Let's think of an online ticketing system that receives theatre tickets from different providers, aggregates them and sells them to the end users. Conceptually it's pretty simple to understand.

First, the initial "use cases" that the company is fulfilling (without being too exhaustive as this is an example):

Receiving and aggregating theatre tickets from 3rd party providers.

Provide an online shop to purchase the tickets.

Handle payments.

Send the tickets to the customers.

Given these, we can easily draw something like:

 

As you can see, this diagram is not complicated. If this is the initial diagram that we see about this company we can make a mental model pretty easily:

There are different external ticket providers.

There is a component that ingests them into a data store (we don't know at this stage what kind of technology we're talking about)

There is a back office used by the admins to work with the content. Maybe select what's on the shop loading page? maybe to filter things?

There's the online shop itself, where the end customers act.

The online shop uses a payment system that interacts with the banks to purchase the tickets.

The tickets are rendered and sent to the end customer.

This diagram does not hint at any technical details. It just splits the full system into different use cases.

We don't know if the implementation is using a single monolith or multiple microservices, we don't know if the online shop is using ElasticSearch or a Postgres database, we don't know if the communication between the Online Shop and the Ticket Rendering is done via Kafka or HTTP, or if it's even the same codebase!

But, we understand what's going on, and from here we can easily navigate to go deeper, to the lowest level of detail.

This document could be the starting point of the whole documentation. If you're interested in how the back office works then just jump into the proper section where you'll find:

A more detailed explanation about which use cases the system offers. 

For everybody

A link to another layer of documentation explaining how the system is implemented and how it communicates to the rest of the components. At this stage, readers will find detailed technical diagrams, implementation designs, and communication details. 

For developers.

A link to the manual on how to operate the back office in the day-to-day tasks. 

For admins and operators.

A link to another layer of documentation explaining the permissions, systems, permissions, and network details of the infrastructure where this system is running. 

For DevOps and infrastructure engineers.

A link to another layer of documentation or even a tracking system where we list all the features and business roadmaps. 

For Product.

As you can see we can have as many layers as we need. This is why it's important and I insist that the documentation levels be linked.

My opinion on what's good architectural documentation

The example we've already seen is simple to understand. It does not provide us with any technical information. The following levels do.

This is where we start discussing concepts like monolith, microservices, queues, streaming services, databases and other technical terms.

But before starting to draw a diagram with "the architecture" we need to take something important into account: Architectures evolve, and they evolve for a reason. As such, system architectures will always have:

An initial state.

A future vision

The current state.

All the previous states, from the initial one to the current one.

When I document architecture I always have these 3 sections:

The 

initial architecture

 diagrams, containing explanations about the initial requirements and context that originated the initial design

The 

objective architecture

 diagrams, taking into account the long-term vision of the company (# of users, # of products, ...)

All the evolutions

 that happen between the initial state and the future vision. These evolutions might be triggered by different reasons such as new requirements or technical discoveries.

Documenting architecture this way creates a flow that explains the purpose of the system and creates a history of decisions. Each of these evolution steps should come with its own ADR that justifies and explains the change.

💡

An Architectural Decision Record (ADR) is a document that explains why a relevant architectural decision was taken and its motivation.

There are tons of templates and articles about them, if you don't use them yet I'd recommend you to have a proper look ( 

https://adr.github.io/

https://adr.github.io/?ref=surviving-software-architecture.ghost.io

)

The architecture documentation doesn't need to be hard. The diagrams should not be complicated. If an architecture diagram is very dense and overwhelming it's a sign that it is trying to display too much detail.

💡

If you are interested in creating effective diagrams I recommend 

Communication Patterns

https://www.amazon.es/dp/1098140540/ref=nosim?tag=blackalmanac-21&ref=surviving-software-architecture.ghost.io

 (aff. link) as a great learning resource, and 

Software Diagrams Repository

https://softwarediagrams.com/?ref=surviving-software-architecture.ghost.io

 as an example repository for inspiration and organization ideas.

My proposed solution is, again, about thinking in layers. Let's think about levels of complexity. To do this we'll get some great ideas from the 

C4 model

https://c4model.com/?ref=surviving-software-architecture.ghost.io

 (we'll talk in depth about this model in a subsequent blog post). The main idea is that we go from the big picture to the low level, one step at a time.

The number of levels is totally up to you. C4 proposes 4, but from my experience, people tend to use only 3 (discarding the most detailed one, which resembles a UML class diagram).

At this point, it's important to talk about the different readers of the documentation.

Up until now, we've been talking about "systems". We never specified if a system is an in-house-developed system, a database, a queue, or a 3rd party integration.

Being a software developer I might be interested in knowing details about that specific part of the architecture. Is this a Java system? Is this a Python script? is the communication done via REST or event passing? What's the repo of the system?

But! if I'm a DevOps I might be interested in other kinds of details about that same specific part of the system. Is that DB an AWS Aurora or a deployed Postgres, what are the network details about that host?

Even if we are trying to draw a small company use case, the deeper we get the more crowded the diagrams will be. That's the reason I prefer to make parallel diagrams at the same level of detail because different roles in the company will have different needs.

 

Problems with technical documentation

So far, I've been writing about my opinionated vision of how documentation should look like, especially focused on architecture. Now I want to talk about why documentation (in general) is hard to get right and why it has a bad reputation.

Documentation is, usually, a disaster.

me.

Any experienced software developer will surely have found the following groups of problems:

Lack of documentation

Lack of updates

Lack of coherence

Lack of flow

Let's have a look at them.

Lack of documentation

Sometimes the documentation does not exist at all. All the knowledge is held by the people who developed the system. This can make sense at some early, chaotic company stages, but it's universally agreed that this is a bad idea.

This does not scale and places a big burden and dependency on the people that has the knowledge.

Writting and keeping documentation is a long-term investment that will surely pay off. I'm not going to expand a lot on this section as, hopefully, the vast majority of people agree that it's better to have documentation than not having it, but let's think about some issues that happen if we don't have any documentation or documentation procedures.

The most typical would be understanding what happens when somebody leaves the company or the project. While some knowledge might be easy to pass on, a bad documentation process will surely leave details and lessons learnt forgotten. And that's not good. Newcomers will have a hard time understanding the system and will most likely run on the same errors that the original developers had. This, in a business perspective, is a ridiculous way to waste money and resources, to say the least.

Lack of updates

Another classic problem is relying on documents written some time ago but never got updated. They represent the knowledge of that current system at that specific time. After that, somebody modified the system to implement a new feature, or to fix a shortcoming but forgot to update the documentation.

The result might be somebody reading the documentation to get an initial idea of the system and then having a bad surprise when they start to work on the system itself. Sometimes causing just confusion, sometimes causing real problems.

Lack of updates happens for different reasons, mostly a bad documentation culture and tool friction (or in other words, bad tooling integration).

We should pay special attention to the heavy use of static diagrams and screenshots. These graphical resources are great for communicating ideas and concepts. But they tend to get outdated very soon. Architectures evolve, so any static diagram (created with an external tool and exported as a static image) is bound to be outdated. And this is even more usual for UI's. It's great to have a screenshot of a UI explaining a user flow. If we are not careful, this resource might become an issue when the user reads the documentation and finds a different UI in the live system.

Static graphic images are always problematic and should be avoided, we should invest in systems able to generate images on the fly based on some code.

Lack of Coherence

While the previous problems are surely important I tend to focus a lot on this one when designing a knowledge system for a new project or a new company, because it's the one that annoys me the most and the one that's harder to fix when broken.

Lack of coherence means different things, for example:

Different document parts don't have coherence or style, jumping from big-picture explanations to deep code details.

Similar documents have different sets of information.

Knowledge and information are scattered through different documentation systems and code repositories.

Lack of proper or "default" tooling.

One typical example of lack of coherence which is easy to understand is 

README

https://www.makeareadme.com/?ref=surviving-software-architecture.ghost.io

 files in repositories. Usually, they come with an explanation about what the project does and a combination of sections explaining how to build the project, how to test it, how to use it, how to collaborate, license, roadmaps, and how it interacts with other projects. Probably in the open-source world, you won't find two README's with the same structure, and that's fine. But, having coherent information in all the company's repositories makes lots of sense.

Coherence across all the documentation levels means that it's easy to write the documents and it's easy to look for information in them! If you want to compile a project you should not have to go to the main documentation page and run the 

search

 command. All the compilation instructions for all the projects should be at the same level.

To have coherence along all our knowledge base we need to have 

clear boundaries between documentation levels

 to know what information goes into each level.

Ideally, when you start a new project in the company you should have a clear indication of what you need to write in the README, you don't need to think much, write down what's expected for that set of documents and you're done with it. And this needs to be true for all the levels.

Clear boundaries also avoid duplication between levels. Duplication in documentation systems always ends up in problems because these systems always diverge. Good luck then figuring out which is the good one.

My main concern about the lack of coherence is that it's the most difficult to fix, as it creates a sense of chaos and disorganisation that tends to be very problematic.

Lack of flow

Technical documentation is not meant to be a good book, and nobody expects it to be funny or entertaining like a novel, but, on the other hand, it should have a flow and quality.

Once somebody has read a particular documentation point he or she should either have all the information that the reader expected to find or know where to keep looking. If the reader cannot find the information and doesn't know where to go next, that's a failure.

Why do these problems exist?

I've had several conversations with people at different levels of different companies and everybody agrees that documentation is important, that it should exist and it should be maintained. But alas, at the end of the day, it's not.

Why is that? Several answers come to my mind.

First, documentation is a different kind of effort from the ones the developers / DevOps like to do. There's always friction between the tools used by doing a task and the documentation.

An engineer's regular task might involve a change in the technical documentation or not. If it's a mundane or small task it will not have implications, but any big project or big change in any existing use case most likely will. Having a proper structure in the documentation makes it easy to know what to change and where.

A good documentation culture is a massive point that we are usually missing.

A good dev culture nowadays involves different tasks: coding, testing, code formatting... You won't find lots of people arguing on this. The problem here is that documentation is usually not among those tasks.

Another big problem we face when writing docs: How do you know that the documentation "works"?

A developer knows that the code change works because there is a test that needs to be written. Sometimes it's not only that, there might be existing tests that will stop working as a result of the change forcing the developer to go and fix them.

This does not happen with documentation. If we don't have coherent documentation the engineer will not know exactly what to change, or even if there is any documentation to change!

If we have well-defined and clear boundaries on the documentation levels it's trivial to know where to go to change the information.

I could be writing about culture for a long time, but I'd rather write about the following problem: Tooling friction.

Levels need to be defined in terms of content and structure, as well as tooling. And the tooling needs to be carefully integrated so it's easy (or better, trivial) to use.

We might have UML sequence diagrams that help a lot in understanding the interaction between two microservices. If that diagram has been drawn with a 3rd party diagramming solution, then we have downloaded the diagram as a static image and then pasted it to another 3rd party wiki that diagram will be outdated on that same day, because there is a lot of friction in this procedure, far too many manual steps.

How to fix technical documentation?

I've worked in different documentation sets for different projects and companies and this is my take on what you need to do if you want to have proper documentation. If you follow this and create a good documentation culture you'll be able to get rid of all the problems that were enumerated in the " 

Lack of..."

 sections:

Define what's coherence for you

I've been writing a lot about levels. Investigate how many you need, write a table with different levels and their ramifications (one for devs, one for infra, one for product, one for design, ...) and explain what you need in each of them and who's the target audience. For example:

Level 1: Global Architecture:

 For developers and product people to understand how the components interact and which implements which use case.

Level 2 (Dev): Component Architecture:

 For developers to understand how a specific component interacts with others and which technologies have been selected and why.

Level 2 (Infra): Component Infrastructure:

 For developers and infra to understand the infrastructure on top of which that specific component is working.

...

Level N (Dev): Repository README:

 For developers, explain that specific repository functionality, how to build, how to test...

Decide and invest in the tooling

Tooling is critical. Probably you will not find a tool that does everything perfectly so you'll need a combination. Just make sure that you can integrate them. If there are manual steps to pass information generated from one tool to the other there will be problems. Guaranteed.

Currently, we have tons of different kinds of tools:

Document systems

: Like 

Google Docs

https://www.google.com/docs/about/?ref=surviving-software-architecture.ghost.io

. They are not great for technical documentation, even if people insist on using them. My recommendation is to avoid them. Their main problem is a lack of integration with diagramming solutions and poor API support.

Wikis

: Like 

Confluence

https://www.atlassian.com/software/confluence?ref=surviving-software-architecture.ghost.io

 or 

Notion

https://www.notion.so/?ref=surviving-software-architecture.ghost.io

. Much better than "office" solutions. They tend to have good integrations and better API support, so we can write our integrations.

Developer Portals

: Like 

Spotify Backstage

https://backstage.spotify.com/?ref=surviving-software-architecture.ghost.io

. Developer portals are interesting because they are easily scriptable and have integrations with developer tools such as distributed source versioning systems and observability tools. If you have resources to make them work fine, customize them and work with them they tend to be my favourite solution.

3rd party full-blown solutions

: Like 

IcePanel

https://icepanel.io/?ref=surviving-software-architecture.ghost.io

. There is a new wave of SAAS products which lets you write technical documentation with AI support. Worth a try if you can afford them.

Automate

If we want to have updated documentation we cannot rely on people to do everything manually, we need to make things as easy as possible. Let's automate everything we can.

I haven't written specifically about API documentation in this blog post. It is a perfect example of how automation and great tooling by the community managed to fix the documentation process. We have easy and automatic processes to create documentation 

directly from the source code:

OpenAPI

https://www.openapis.org/?ref=surviving-software-architecture.ghost.io

 for REST based systems.

AsyncAPI

https://www.asyncapi.com/?ref=surviving-software-architecture.ghost.io

 for event based systems.

This is a great scenario of frictionless documentation. Any engineer can change the code and the documentation gets automatically regenerated and published. Just brilliant. This is what we need to aim for everywhere.

We have a similar situation with diagrams. Depending on the kind of diagram you need you can use a diagram-as-code solution, like 

Mermaid

https://mermaid.js.org/?ref=surviving-software-architecture.ghost.io

 or 

Plantuml

https://plantuml.com/?ref=surviving-software-architecture.ghost.io

, you write the structure in the code and it will be automatically rendered into an image by the tool on the fly.

A good improvement over taking a manual screenshot and uploading it into a wiki.

Ownership

The documentation is a global effort, and everybody needs to participate. That said, the documentation needs to be written by the experts who design and develop the system and needs to be reviewed by their peers.

Documentation has owners and the owners are responsible for it.

We need to enforce ownership and responsibility. If the documentation is not good enough we need to improve it. If it's broken or incorrect we need to be able to prioritise the fix as it was code.

Use methodologies

A blank page is always scary. Luckily we have different freely available writing guides and methodologies that help us a lot in writing texts.

There are writing guides that help a lot to structure the text and the format, there are others that explain how to write concisely. Feel free to look around, you'll find plenty. My favourite ones are:

Inverted pyramid structure

https://en.wikipedia.org/wiki/Inverted_pyramid_(journalism)?ref=surviving-software-architecture.ghost.io

: How to organise sections.

Google documentation style

https://developers.google.com/style?ref=surviving-software-architecture.ghost.io

: Style guide.

Gitlab documentation style

https://docs.gitlab.com/ee/development/documentation/styleguide/?ref=surviving-software-architecture.ghost.io

: Style guide:

Diataxis documentation methodology

https://diataxis.fr/?ref=surviving-software-architecture.ghost.io

: How to organise a documentation set and the different kinds of styles and document formats.

Link everything

Let me insist, yet again, on the levels and the flow of the documentation. While having all the documentation pieces and levels connected seems like a big effort it results in a great experience when navigating through the documentation, which translates to improved productivity and less frustration.

Cultural change

And now for the elephant in the room.

In this blog post I've gone through why we need documentation and I've tried to explain why it's a good investment.

Then I talked about what kind of problems we find when dealing with documents, especially technical documentation written by IT professionals, and then, some rule of thumb about how to fix them.

But, none of them will work if we don't 

enforce

 a good cultural change in the team. Technical docs are a first class citizen. Just like the code and the tests.

Different teams will need different adaptations to their culture in terms of documentation. That will depend entirely from where they start.

This cultural change needs to happen, needs to be enforced if necessary it's necessary to be maintained over time.

Let's see an example of enforcing this cultural change:

A developer gets a task for a specific project. The change is a new feature that adds a feature to a system. She gets the task done, builds the tests, ensures that all runs smoothly in staging and then creates the PR.

Her peers need to review the code, the testing 

and the documentation

. If the affected documentation (if any) has not been modified accordingly the PR needs to be rejected. Would you accept a new change without it being tested properly? probably (hopefully) not. The same needs to happen with documentation.

Wishlist

I've always created and improved documentation based on preexisting tools that the project or the company already had. Some tools have great integrations while others feel clunky and force humans to do too much work.

I will end this blog post by writing a very opinionated list of the features I'd love to have together in a documentation system.

Versioned

: So I'll be able to see what changed and who did a change.

Review capable

: You could create comments/issues on the documentation indicating to the author that something is wrong, incomplete or that it needs more work.

WYSIWYG / Code edition

: Documentation must be written by anyone in the company. WYSIWYG editors are hated by developers and code is hated by non-developers, so, ideally, the system would be able to do both.

Bidirectional

: The system could "link" a document to a specific part of the code/diagram, so when that part is changed the documentation would be able to, at least, notify the author that the specific block changed so it might be a good idea to check that the documentation is still valid.

Easily integrated via API

. So you could use existing integrations and code whatever is needed by your specific use cases.

Rendering capable.

 It should be able to render diagram-as-code blocks without having to rely on people taking screenshots.

Sign up for more like this.

Enter your email Subscribe

https://surviving-software-architecture.ghost.io/architecture-documentation/#/portal

[

Serving a new Overlord, my trip to the CIO Office

I've recently made a significant career change. I've spent around 20 years in the IT industry, always on the product side. I've developed customer facing systems and backend software for small startups and big companies. As a result of that I had a very](https://surviving-software-architecture.ghost.io/serving-a-new-overlord-my-trip-to-the-cio-office/)

13 Jun 2025 7 min read

[

Zero Trust Architectures

Why Zero Trust architectures exists, what it is and how it can be implemented.](https://surviving-software-architecture.ghost.io/zero-trust-architectures/)

24 Mar 2024 14 min read

[

Write Ahead Logging

What's a Write Ahead Log and how to implement one.](https://surviving-software-architecture.ghost.io/write-ahead-logging/)

02 Nov 2023 14 min read

Surviving Software Architecture

https://surviving-software-architecture.ghost.io/

 © 2026

Sign up

https://surviving-software-architecture.ghost.io/architecture-documentation/#/portal/

Powered by Ghost

https://ghost.org/
