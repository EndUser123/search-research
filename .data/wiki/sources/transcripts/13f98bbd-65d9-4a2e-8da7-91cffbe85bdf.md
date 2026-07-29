---
source_id: "13f98bbd-65d9-4a2e-8da7-91cffbe85bdf"
title: "Stop Giving Your Agent Every Tool"
notebook_id: 06717c64-8597-4a59-a5e3-871e841585af
url: null
type: youtube
exported: 2026-07-27
---

# Stop Giving Your Agent Every Tool
My agent Emma had 121 tools.

Before she answered a user message, her system prompt could hit 58,000 tokens.

That tool surface is what made Emma useful.

I could ask her to pull context from the web, update something in Notion,

check the CRM for data, or work against my vault without switching between apps myself.

Those tool calls also came with a cost.

The model needs tool documentation before it can call a tool.

It needs the tool name, the description, and the input schema.

Mastra passes that documentation into the model context so that the model can decide what to call.

After I split some capabilities into separate agents and added a supervisor,

Emma still carried a large tool set for herself.

She had to read the whole menu before she could do any work.

I fixed this by changing when the model sees tools.

Emma kept the broad tool catalog, but the prompt started with a smaller working set.

So let's walk through how tool definitions create context bloat,

how tool search fixes it, and why I replaced my custom version with Mastra's ToolSearchProcessor.

If you're new to the channel, my name's Damian,

and I've been a software engineer for over 15 years.

And here I break down concepts on building with AI.

This week's video is brought to you by Mastra.

Mastra is the open source TypeScript framework for building AI-powered applications and agents.

If you want to learn more, I'll leave a link in the description.

Thank you to Mastra for sponsoring this video.

Tools give the LLM a way to interact with the outside world.

A tool has two sides.

First, there's the code that runs when the tool gets called.

Second, there's the documentation that the model needs before the call.

The name, the description, and the input schema.

That documentation is what causes the context problem.

With five tools, the prompt cost feels small.

But with 100 tools, the model spends a lot of attention reading tool docs

before it can handle the user request.

Let's use Claude as an example.

When Claude decides to use a tool, it returns a tool_use content block

with the ID, the tool name, and the input for that tool.

Your app then executes the code that's behind that tool.

Then, your app will send back the result to Claude as a tool_result with the matching ID.

This loop only works, though, if Claude knows the tool exists.

That means that the tool definition has to live somewhere before the call.

Agents need tool access, but large tool catalogs make the model pay a prompt cost

before the task even starts.

Anthropic introduced a pattern called tool search for large tool surfaces.

The pattern splits discovery from loading.

The model starts with a small set of tools plus a search tool.

When it needs a capability, it searches the catalog,

loads the matching tools, and continues the task.

Instead of giving the model the whole tool catalog up front,

you give it a way to search the catalog when it needs something.

That's the idea I copied into Emma.

Before I found Mastra's processor,

I had built my own version with Mastra's createTool.

I called it searchTools.

The model would call searchTools with a query like

create a Notion page or search Attio company records.

Then, Emma would search the runtime catalog,

return a compact list of matching tools,

and store the selected tool names so that they would become available on the next model step.

This gave Emma a smaller starting prompt.

But when she needed another capability,

she could search for it and continue with the right tool loaded.

The custom version reduced the prompt.

Emma felt faster,

and I could add capabilities without making each request heavier.

The problem is I inherited the maintenance cost.

I owned the search index,

result formatting,

loading the tool state,

and the glue code around the model loop.

That code made sense while I was testing the pattern,

but once I discovered that Mastra supported it in the framework,

I didn't want to keep that layer in my app.

Mastra's ToolSearchProcessor replaced my custom layer.

Processors in Mastra can transform or control messages as they move through an agent's execution pipeline.

ToolSearchProcessor gives the agent built-in search for loading tools.

It indexes the tool catalog with BM25 using the tool ID and a description,

then gives the agent two meta tools,

search_tools and load_tool.

Mastra then handles the search and loading mechanics that I had built by hand.

In Emma, I still keep a few tools available from the start.

Web search, web fetch, thread history,

and the first-party Mastra workspace tools.

Those are all the baseline capabilities.

The rest, the larger catalog, goes into ToolSearchProcessor.

So now Emma starts with a small set.

When a task calls for another tool,

she searches, loads the match, and uses it.

The custom search tool's file went away,

and Emma's agent wiring got a lot simpler.

I kept the tools available

and moved their definitions out of the starting prompt.

Before the migration, Emma had 121 tools in the foreground surface.

After the migration, she had about 10 direct tools.

The rest of the catalog stayed reachable

without sitting in the prompt from the first token.

I'd now treat tool availability and prompt visibility

as separate design choices.

Emma can still reach the full catalog.

She does not need the full catalog pasted into the prompt on every step.

For long-running agents, this keeps routine turns

cheaper and easier for the model to navigate.

You can give the agent broad capability

while keeping the working context narrow.

This is the Mastra meeting assistant

that I built in my first video on building your own AI agent.

Now, it's taking a new agent

and using ToolSearchProcessor.

And so you can see here that on the line seven,

we're going to instantiate a new instance

of ToolSearchProcessor.

And part of the arguments are tools.

So here we're passing in the tools

that we want to be able to search across when we need to.

Then we have on line 13, some other arguments on search.

So we're passing in topK of three.

So that means we're going to get

a maximum of three tools returned to us.

We look at line 18, we have our tool search demo agent.

And the biggest thing to kind of keep an eye on

is that you'll notice that there's no tool parameter

that's being specified here.

So we're not passing any tools in

because instead we're going to be handling this

via ToolSearchProcessor.

And instead we have an input processors array

where we pass that processor.

So like I mentioned,

there are many different types of processors

that Mastra has

and you can build your own processors for input.

So Mastra supports input processors

and output processors.

Inputs get run before the prompt gets sent to the model.

So with this being set up,

let's go ahead and take a look at it in action.

So now we're in Mastra Studio,

I'm going to open up the tool search demo.

So if we look, we can see on the right here

that under tools,

there are no tools necessarily mentioned.

We do have an input processor

and we can actually click into it and see what it is.

It is ToolSearchProcessor.

For our purposes,

I'm going to go ahead and try to trigger a tool.

So I'm going to say,

do some research on Mastra,

the TypeScript AI.

I'm going to send that off

and in order to do that,

it's going to need some tools.

So we can see here that it called search_tools

with a query for web search

and Mastra returned back the search-web tool

and a message that says that it found one tool

and some instructions also to say,

use load_tool with the exact tool name

or tool names array to make them available.

So the first step here,

because we haven't configured autoLoad true,

is that we have to now go ahead and load those tools.

So we can see that the agent called that with load_tool.

So it said tool arguments tool.

The tool name is search-web

and we got a result back.

That's success.

It is now available to us from there.

After that,

we can see the message.

Now let me search for the information about Mastra

and it calls search-web.

So now we can see in practice

how the tool search actually works.

And if we go into the observability into traces,

we can go ahead and open this up as well.

And we can dive in

and we can see that here,

we can see that the processor got hit

and later we had the search_tools call.

We can then see the different step

where load_tool was called,

then the actual tool call for search-web.

So the entire loop here is represented in a trace,

giving us some debugging available to us

to see kind of like what had happened,

what the agent searched for

and what tools became available to us as we debug this.

So that's how easy it is to get tool search

into your own custom agent using Mastra.

If your agent is starting to feel hard to reason about,

I have a free worksheet called

the 4 Levers Agent Diagnostic.

It walks you through one real agent failure

across context, tools, loop and governance.

So you can find the smallest harness change to try next.

I'll leave a link to that below

along with the Mastra docs.

And if your team is building production agents with Mastra

and you want help reviewing the architecture,

evals, observability or tool surface,

I'll also include a link to book an intro call.

Until then, I'll see you in the next one.
