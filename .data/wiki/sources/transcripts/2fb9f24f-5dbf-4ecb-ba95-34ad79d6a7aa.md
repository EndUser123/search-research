---
source_id: "2fb9f24f-5dbf-4ecb-ba95-34ad79d6a7aa"
title: "PewDiePie’s Odysseus AI Just Made Private AI Easy"
notebook_id: af7b9263-fd59-4b81-9746-2bc4ad0c82a2
url: null
type: youtube
exported: 2026-07-27
---

# PewDiePie’s Odysseus AI Just Made Private AI Easy
The infamous YouTuber PewDiePie just

released a whole AI workspace, and it's

actually really impressive.

This is a completely different style of

agent than OpenClaw or Hermes agent,

and I'm going to walk you through using

it completely privately in this video.

Now as you can see here, Odysseus runs

locally on your computer.

It is entirely self-hosted, and it is

marketed as Privacy First.

But the truth is it's not going to be

Privacy First if you're using OpenAI,

Anthropic, Google,

DeepSeek, etc. as your AI provider.

So we are going to set up Odysseus using

Venice as our provider,

because Venice does not

store any of your chat content.

So to get started, we'll simply click

this Get Started link on

Odysseus, and we copy that code.

If you want to do a little more due

diligence, check out the GitHub repo,

and you'll see how

there's already 38,000 stars.

And here in the ReadMe, we can see all

the features, everything

we saw on the homepage here.

So let's open up a terminal.

It might be called the

PowerShell on your Windows machine.

So go ahead and paste that line.

And now Odysseus is

installed and ready to go.

There's one last thing we need to do

though, and that is get it running.

So basically here, this install command

cloned the GitHub repo onto our computer

and then changed directories into it.

But there's actually more to it than

that, which we'll see right here in the

ReadMe under the Quick Start.

Find your operating system, native Linux

or Mac OS, Apple Silicon or Windows,

and you're going to need to copy

everything that comes

after the CD Odysseus.

So in this case, for Windows, you copy

that PowerShell command.

If we want to use Doc, we'll copy that.

On Linux or Mac OS, we copy all this.

For Apple Silicon, we

just run this script.

I'm on Apple Silicon, so I will copy just

that last script launching command.

We'll paste that there.

We'll see that it is installing Python

and everything else that

needs to run on Mac OS.

And while that's running, I am just

installing this

straight onto the computer.

This is a work computer

with no sensitive information.

If you are using a personal computer, you

might want to consider running it in

Docker, as is recommended here.

This will put Odysseus in its own

container that it can't

get out of, so to speak,

and accidentally mess

anything up on your computer.

Just like OpenClaw or Hermes, this is a

precaution you might want to take

to ensure that the AI doesn't

accidentally mess

anything up in your machine.

Okay, so now I set up my

username and I give it a password.

And now we'll see in just a few seconds,

it will load at this URL in our browser.

And now we're done with the terminal.

It wasn't too bad.

I'll log in and here we are, Odysseus.

Now the first thing I'm

going to do is change the theme.

I actually am a fan of

the more light modes.

And this is actually a really cool

feature of Odysseus

just from the beginning,

is you can find a color

scheme and vibe that you like.

You can also customize every little thing

and see exactly what it will

look like when you do that.

So this theme customizer is just one

example of every little detail

that Odysseus lets you control and

fine-tune as you're going to

see in the rest of this video.

So here we go.

We need to type forward slash setup to

get started forward slash setup.

And now if you already have a provider

you want to use, you can

just click the provider

and it will get you

ready to paste your API key.

And that's that.

But as I mentioned earlier, I want to do

this completely privately.

I do not want to use any of these

providers except for maybe Olama,

which would run a model

locally on my computer.

If that's the case, all you

need to do is copy this endpoint,

which is the Olama

endpoint and send that off.

But Olama and local models on a laptop

may not always accomplish the

tasks we want to accomplish,

at least with the efficiency or quality

we're looking for, which is

why I'm going to use Venice.

So what I'll do now is I'll actually skip

this and just go

straight into the settings.

And here in add models,

we see we have nothing set.

So if I were to use Olama or a local

model provider, I can just click that,

but I'm going to use API.

I'm going to type in api.venicei forward

slash api forward slash v1.

And then I'm going to head over here to

the Venice API dashboard

and generate a new API key.

I'll call it Odysseus.

I'll give it an optional expiration date

or spend limit and then

I'll generate the key.

Copy that key with the copy button.

Come back here and paste

it right in to Odysseus.

Click test and we see that it's online

and it found 88 models available.

These models you can learn more about

right here on the API settings page.

You can even organize them

by agentic functionality.

So if we want an agentic model that does

all the things, function calling,

reasoning, code, and vision,

then we have a good selection here.

We'll come back to that in just a moment.

But for now, let's

click add and here we go.

We have 88 models enabled via Venice.

Now here's a pro tip.

If you do have a powerful laptop, you can

combine API with local models here.

And we'll do that by exiting the settings

and heading over here to cookbook.

Now, this is something that's also pretty

neat about Odysseus.

The cookbook will tell you what local

models will run well on your computer.

And you'll see that these are perfect

fits by running on the

GPU on this silicon MacBook.

Simply click a model and download or run

it and it will download it

and start serving it for you.

If I click here to the serve tab, we'll

see what I have installed.

And I can simply click Gemma 4 and I can

change the configuration,

which is a little beyond the scope of

what we want to do here.

But now I can click the dot dot dot and I

can click serve and launch Gemma 4.

So now if I come back here, we'll see

that I have all these API dot Venice dot

AI models available to me

as well as my local models.

So here, for example,

does not show the Venice.

That means it is local.

So another part of this tab that is

important is the dependencies.

If you want to edit images, remove

backgrounds and do some

really cool stuff with Odysseus,

you're going to need to come to this

dependencies tab and click install on

some of these tools.

For example, RMBG is AI background

removal for the image

editor, which we'll get into later.

AID noise and upscale, same thing.

We can just install that and you'll see

it will download and

install everything for you.

Really convenient,

really pretty easy here.

You might need Tmux

first if you're on macOS.

If you want to do browser automation,

check out Playwright.

And then diffusers here is image

generation pipelines, which will help you

make and edit images.

So in case you run into issues later,

don't forget about this tab.

So now if I come back here, we'll see

that I have all these API dot Venice dot

AI models available to me.

So here, for example,

does not show the Venice.

That means it is local.

So before we start having some fun, let's

actually head back into the settings here

and we can see now that we have Gemma 4,

our local model here,

as well as API dot Venice dot AI.

So everything is now

available here through Odysseus.

So now let's start configuring a little

bit here in the AI defaults menu.

So we've got our default model.

Now we have a dropdown

here of all the models.

If you want to learn more about the

models, see how much they cost, see what

they're good at, just browse

through the model list here.

Minimax M3 just came out, for example,

very fairly priced, especially if we

compare that to

something like Claude Opus,

$30 output versus $1.20

output per million tokens.

So why don't we play with Minimax today

as our default chat model?

We find Minimax M3.

Let's add a fallback.

Now this fallback can

either be local or via Venice.

I'll have the fallback be one of my

favorite models, Kimi K2.6,

which as we see here is a

very capable agentic model,

not quite as cheap as Minimax M3, but a

good dependable model

for agentic purposes.

Now here we see the utility model.

This recommends a local endpoint.

These are quick API calls that don't

necessarily need to be super intelligent.

So let's use a local endpoint here.

We'll just go straight, Gemma 4.

We'll save money.

We'll have this run locally.

Gemma 4 runs, in my

experience, very quickly, locally.

Vision model.

We'll just let that stay on auto detect.

But if we come back here, we'll see

Minimax does do vision.

So we shouldn't have a problem there.

Now research model.

As we're going to see in a moment, deep

research is a big part of Odysseus.

So we want to make sure

we are optimized for that.

So when we do deep research, I'm actually

going to choose Claude Opus 4.8.

We're just going to go all the way here

because I want to get this

the best research possible.

So it's going to cost a little more, but

the great part of just

using one API key with Venice

is that we can have all these different

models, frontier, open

source, private, anonymous,

all through one provider.

Very convenient.

I'll choose DuckDuckGo as my search, and

I'll leave everything

else as the default.

We'll leave the tool call limit default.

And here is something really

neat, which is teacher model.

So I'm going to use an agent mode task

escalate to a state of the

art teacher that writes a skill

so the student can do it next time.

This is actually really

cool and really convenient.

I'm going to choose Claude Opus 4.8 to be

the teacher model, which means if Minimax

or Kimmy or even Gemma

messes something up and can't do it

right, Opus will come in

and create the skill file

to make it easier for these

agents to do it the next time.

So you're paying once for the price of

the frontier model to build for you, but

it's allowing you to execute

with the open source,

more economical models.

So now we have our AI defaults set.

Now, while we're in the settings, I'll

just introduce you a little bit to

everything else going on.

We can choose our search provider.

I am a fan of DuckDuckGo, but

we can see search engine here.

It's actually

self-hosted, which can be cool.

I'll leave this at DuckDuckGo just

because I don't actually

have search engine installed.

So we're going to choose DuckDuckGo.

We click test and we get five results.

It's working.

Integrations.

This will not be part of this video

today, but we can add any

API service as an integration.

Say we want to send emails.

Say we want to connect to a password

manager, our Home Assistant app, GitHub,

any Git service like Giti.

Any API integration,

you can connect here.

No problem.

You also have CalDAV calendar services.

You can import your contacts.

You can connect your

email provider like Gmail.

You can also connect any MCP tool.

So Odysseus is very

configurable, very powerful.

Speaking of email, once you've added your

email account, you

can create email tasks.

Give the AI agent a writing style prompt.

For example, I write

emails in this style.

I don't use exclamation marks.

I assign my emails this way, et cetera.

So you can give it a

system prompt to write like you.

And as we'll see soon when we go into the

tasks more deeply, we can add tasks.

So essentially we can have Odysseus check

our email and respond to emails for us

the way we want it to.

All we got to do is connect our email

account and the integrations.

Reminders.

We can add browser notifications or once

we add an email account, we can even give

ourselves email notifications.

Odysseus can email us.

Reminders.

You can configure every

aspect of the appearance.

If you don't want your AI to give you

emojis, we can shut that off.

Do we want web search to be available?

Do we want to be able to switch between

agent and chat mode, as we'll see soon?

Do we want personas, characters?

We can also toggle on or off models.

So over here, I can just choose in a new

conversation, do I want to use API models

or do I want to use local models?

We can shut that off.

Tools.

Do we want all the tools

here or do we want to hide them?

Do we want to keep the brain activated,

the cookbook, et cetera, et cetera?

Then you have keyboard shortcuts, which

can be extremely convenient if you make

this your actual workspace.

Finally, you can toggle on or off any

tools you want to allow

Odysseus to use or not.

You can create new users and you can

import, export, or delete all your data.

So that's the settings menu.

Odysseus is very configurable.

I think that's what makes it so unique in

the AI agent framework space.

So before we check out the rest of the

tools, let's just take a

look what the chat looks like.

Now we can see that it's a bit more

exciting than a lot of

chat response windows.

We got colors, we got italics, et cetera.

We got icons, maybe not emojis.

And we can see how many tokens every

message costs and how long it took.

Similar to the Venice interface, we also

have options to fork the conversation, to

edit a response, to

regenerate, to rewrite, et cetera.

We can activate the search feature and it

is searching the web with DuckDuckGo.

So here we go from five web sources.

We got a nice little report of what

happened today in the news for AI, and

that took less than 20

seconds on a local model.

Similarly, I can give the agent to a

terminal, but we're not

going to do that today.

One other thing that's neat is you can

switch between agent and chat mode.

So if you want the agent to do actions,

not just search the web, but actually

maybe work on your email, for example,

send an email, you would

toggle over to agent mode.

Whereas if you want to just chat, do web

research, you would

just stay in chat mode.

So I'll click this plus to

start a new conversation.

And one other thing that's

pretty fun is prompt injection.

So here you can inject a prefix and a

suffix to your message, as well as adjust

the temperature to get a more creative,

perhaps a loosenatory response.

But then you can also create a persona.

So if you're into characters and you want

a friend to chat with, you

can give your friend a name.

And then I can use the little AI button

to expand the basic thing I want.

It will create a more

detailed system prompt for me.

And you'll see there are also some

presets available, mostly philosophers.

So I'll save and start that persona.

And you can see we have the friend

persona on and we're chatting with our

friend existing locally.

One other thing we can do in this prompt

injection menu is create a group chat.

So I can have our friend on the local

model, but then I can bring in Socrates

and I can give him a Claude Opus 4.8.

And then I can add in Nietzsche and we

can have him run on, let's say, Grok 420.

So now we can start either

a sequential or a parallel.

I'm going to go with parallel.

We'll start the group.

We'll say tell me the meaning of life.

And we'll see the icon of each model next

to the name and we'll get

an answer from each persona.

So we have our Google friend.

We have our anthropic Socrates and we

have our Grok Nietzsche and we can have a

group chat with anyone we want.

Now imagine you want to run a business.

You can create your marketer, you can

create your social

media manager, etc, etc.

The opportunities are endless, especially

when we see all the tools

that we can give Odysseus.

So now let's dive into the tools.

Here's the brain.

Now Odysseus on its own will create

memories by default.

So you could import memories in the add

tab, adding files, web pages, whatever it

is, and then it will

add memories to its brain.

So it will remember for you.

You can also add skills and skills are

what agents use to know how

to perform a specific task.

So let's take our Venice API key to the

next level and import

the official Venice skills.

Now these are all skills for your single

Venice API key to generate video,

generate audio, generate

images, make payments, etc, etc.

I'll click that code button and I'll

download the zip file and we

see here it says no skills yet.

Use agent for it to auto extract them.

So I'll close this.

I'll start a new chat.

So the first thing you're going to need

to do is uncompress that skills file and

open up the skills folder and we'll see

all the skills here.

And for now I'm going to take image,

generate an image edit, and I'm going to

drag those here and I'm going to use

Claude Sonnet here just to make sure this

first time it gets it right.

We'll say install these skills.

Now, if you see this

app API fail, it's normal.

I don't know exactly what it's supposed

to do, but it doesn't

actually mean anything messed up.

This is just part of the growing pains of

a new agent framework.

And boom, our agent installed the skills.

So here we are in a new chat.

Let's find our default mini max and let's

say generate an image of

Odysseus on his voyage.

And now we see it's going to craft a

prompt and call the Venice API.

Now, it needed a little reminder that it

has the Venice image generation skill.

I would hope that over time it will just

remember that and

cement it into its memory.

It's also saying here is a prompt in case

you just want to create it

inside the Venice interface.

We could just go over here to the agentic

chat, paste that prompt and say make this

image and the Venice agent

will just do that for us.

Now, the problem here is it looks like

Odysseus cannot display images yet, but

that said, it can

display images in the gallery.

So let's see what happens if we say add

the image to the gallery.

Spell gallery wrong.

See if it.

Okay, let's see here.

So it looks like images just aren't ready

in Odysseus at the

time of me recording this.

Meanwhile, the Venice

agent gives us an epic image.

I'll save that.

And here, if we head over to

the gallery, now is a good time.

I'll click upload and there is our image.

We've imported it and let's click edit.

And here we have an editing window.

I can zoom in and let's

see what we can do here.

I can crop obviously.

We know what that is.

We can brush.

We can draw things.

Well, change color.

Not something I really need to do.

So let's try background removal here.

Click BG remove and it did

a decent job, but not great.

Also kind of a complicated image here to

remove the background.

So perhaps on a more straightforward

image, that would be easier.

Let's see in painting here.

I can paint, let's say back here.

We want to add a crew, right?

So put that there.

And I will say at a

boat crew in the back.

Now we don't have a model.

So this might not work.

Server diffusion

model via cookbook first.

So I go back to the cookbook and it looks

like here is a model for

that that we need to download.

So you're going to need to download that

local model to edit that image.

But in general, all of

this is pretty neat here.

The things we're able to do right here

locally with Odysseus.

So that's enough for image generating.

Let's take a look now at

the rest of the features.

One thing that I think is really powerful

is the model comparison feature,

especially with the provider like Venice.

Because if you're working on certain

tasks each and every day, whether those

are chat tasks, agent

tasks, searching, researching,

you might be curious which model is the

best bang for your buck, so to speak.

So as we saw earlier, there are plenty of

models to choose from, but which one

really does the best job and

which gives you the best price.

So here what we can do is choose a

handful of models to accomplish the same

task and then you can vote

on which one was the best.

So let's take Minimax 3, Google Gemma 4.

Let's do Kimi 2.6 and let's do a Quen

model, Quen 3.7 plus.

Now all these models are

here to learn more about them.

They are all fairly

priced and they're open source.

They're all provided

through the Venice provider.

If we want to add another test with a

local provider, then here we can see, for

example, right here,

this is a local model.

And I'm going to choose sequential mode

so we don't hit any rate limit issues.

So let's click start.

It'll check the models to connect.

And now here we are on the competition

model comparison screen.

Okay, so let's look at the evaluation

prompts here and let's

run proof and verify.

Prove that the square

root of two is irrational.

Then write a Python program that

approximates it using Newton's method to

50 decimal places and verify.

So now we send that off and one by one

each agent will work

through that assignment.

Okay, so we have our results.

Now full transparency.

I don't really know what all this means.

I don't know what did a good job or not,

but we can just look at some of the data

here to draw a conclusion based on

someone that doesn't know

science or math very well.

So we don't know which models which

because it's a blind test.

We do know that this took 2300 tokens.

That's a 1330 900 and 3000.

So these took less tokens, but took

longer and these took

more tokens, but were faster.

So let's just say we were looking for

time and all the answers were good.

So we'll vote this one as number one.

Oh, and that was Gemma for

and now we see the results.

So then we can click the score here and

we can see in the agent's category.

Gemma for has a win of 100%.

And if we head back to the compare

window, we can actually see the

scoreboard at any time.

So this is a really cool feature to

discern which models are best for your

workflows when you're using a service

like Venice with this many models

available to you at varying price ranges

and various speeds with the option to go

either fully private or anonymous through

these frontier models like Clodopus.

Then you're going to want to get an idea

of what's best if you're going to be

running these workflows all the time.

So this is a really

cool feature of Odysseus.

We'll wrap up here by just looking at the

rest of the tools, but here we can just

do quick ads to the calendar.

We can import a calendar.

We can make calendars.

We can sync with our integrations that we

went through earlier.

And then if we head over to the tasks, we

can actually have Odysseus send us

reminders about the calendar, classify

events in the calendar, email us, scan

emails from our connected email account

and auto add them to the calendar.

And just get things done with our

calendar right here in Odysseus.

The same goes for email.

We can get stuff done in our email

through these tasks.

Chat tidying our chat sessions.

This is active.

You can see it will clean up empty chat

sessions and auto sort them into folders

right here in the interface.

Then you can see what

tasks are being run.

Looks like there is a skill

audit being run right now.

20 minutes ago, our chat

sessions were tidied up here.

And then here we can add tasks so we can

run a prompt to our agents on a schedule.

We can have a prompt

sent when an event happens.

We can have research

done on schedule every day.

Check the news for me.

An action can be run on a schedule or

when a web hook is

triggered or something can happen.

So we can click new tasks

and feed this into our agent.

Really exciting here.

So now here in the deep research window,

we can see how we can have our agents run

deep research reports for material that

might be important for our everyday work.

It will run the deep

research, make the full report.

You can choose which

models you want to use.

You can adjust the settings.

And then they will show up here in the

library under research, which I haven't

got any in here yet.

This library has all your chats.

You can upload documents to it and it can

become a catalog of information either

for you or your agent.

Here in the notes window, we have basic

to-do lists and reminders, which will

sync with your agent and

any tasks you assign to it.

You can even draw here for your notes,

which is kind of fun or attach images.

So there you have it.

That is Odysseus.

Remember, when you use OpenAI and

Entropic, they are storing all your

conversations and prompts forever,

harvesting data about you, selling that

to advertisers, potentially handing that

over to law enforcement or government

agencies when they ask, etc., etc.

You don't know what's

happening over there.

But with Venice, your

conversations are not being stored.

They're being stored in your browser.

If you're using the Venice interface,

this stays on my browser and they're not

stored at all as API calls.

You have access to all kinds of models,

over 250 models across

different modalities,

which can make your Odysseus workspace

just an all-in-one

extraordinary place to work.

So enjoy and happy building.

Hit that subscribe button for more AI

tutorials with a focus on privacy.
