---
source_id: "73bbf30b-377c-4aca-a70e-1fb6b3bcefc7"
title: "Hermes Agent Tutorial for Beginners - Crash Course"
notebook_id: 917784eb-ef7d-40e5-b823-7bd74c2bc9bd
url: null
type: youtube
exported: 2026-07-27
---

# Hermes Agent Tutorial for Beginners - Crash Course
This is Hermes agent free open source

AI assistant by Nous Research
that runs on your own computer.

It's completely free to use.

It works on Mac, windows, and Linux,
and it just crossed

160,000 stars on GitHub
in under two months.

What makes it different from OpenClaw

is that Hermes remembers
everything between conversations,

and it actually teaches itself new tricks
as you use it.

In this video,

I'm going to show you how to install it,
connect it to Claude or your favorite.

I get it onto your phone through telegram,
plug it into your favorite apps,

and at the end, connect it
to thousands of apps using just one tool.

Let's jump in. on your Mac.

Just press
command and spacebar and type terminal.

Now copy this one line of code.

Paste it in and hit enter.

That's literally the whole install.

You don't need to know

what any of it means
while it's running in the background.

It's setting everything up
it needs by itself.

So you don't have to install
a single thing manually.

The whole thing takes about a minute
or two.

When it's done, it's
going to pop you straight

into the onboarding process
so you can get started.

Now we need to give Hermes a brain.

And that's where your AI model comes in.

Now you've got some really easy paths.

Here you can choose Nous Portal, which is
provided by the makers of Hermes Agent.

They've got a free plan
to get you started straight away.

you can pay for some more powerful models.

I'm selecting anthropic,
and this is going to give me access

to the biggest
and latest model called Claude Opus 4.7.

So it gives you the URL you need to

go to sign up if you didn't already,
and then click on Create Key.

Give it a label like Hermes
so you remember what it's for Now

copy that key.

Paste it into the terminal
where Hermes is asking for it,

and then pick
which Claude model you want to use.

I'm picking Claude opus 4.7, but
Claude Sonnet is much cheaper and great.

If you're a little bit
worried about API costs.

And here's the best part
you're not locked into one model.

You can literally swap to a different one.

Any time just by running Hermes
model again.

Or as I'll show you later in telegram,
one single command in the chat.

Now, this is probably the most requested
feature.

Getting Hermes on your phone
through telegram

And the best thing is it's
part of the onboarding process.

So once you've chosen your AI model
you can now select a chat app.

There are tons of them.

WhatsApp in there
Discord in there, and so many more.

I'm going to select the telegram app now.

Once I've done that,

it gives me instructions
to talk to the BotFather on telegram.

search for it.

You want the official one
with the checkmark next to its name.

Tap on it and type Slash New Bot
to start creating a new bot.

It'll ask you to name it first.

So I'm going to call my Mike's Hermes Bot.

Then it'll ask you for a username,
which has to end with the word bots.

And it needs to be unique as well.

So mine is going to be called
Mike underscore Hermes underscore unique

underscore
bot BotFather sends back a long string

of letters and numbers
that your bots password basically.

So copy it.

Don't share it with anyone.

Switch back to your terminal
and paste it into Hermes

where it's waiting for that token.

Now pull out your phone, open telegram,
start talking to your bot,

type something like hello
and you should get a response.

Quick one here.

If you enjoy video tutorials
like this, please hit like on this video

and also subscribe to my channels
as I do videos like this weekly.

Thank you!

Now, this is the part that makes Hermes

feel like a real assistant
instead of just another chat bot.

When you get into the chat interface
in your terminal,

you will be able to say hello to it.

So I'm going to tell it a bit about me
and see what happens.

I'll type.

My name is Mike.

I run a YouTube channel called Creator
Magic and you can call yourself Zeus.

Please say this
so you remember it next time we talk.

Now check this out
in a second terminal window.

I'm actually peeking into the folder
where Hermes stores its memories.

It just saved, and you can literally
watch the files being written

in real time
as Hermes saves what I just told it.

One file is called user,
which is everything Hermes knows about me,

and the other file is called memory,
which is Hermes own personal notebook

all about itself.

This is the magic.

Every single time I come back, Hermes
already knows who I am,

what I'm working on,
and how I like things done.

Now here's the part where Hermes
really pulls ahead of the competition.

Hermes has a whole library
of pre-built skills that you can install

with just one command.

Almost 700 of them out of the box
type Hermes skills list.

To see what you've already got installed,
Hermes will show you the full library

while I've been searching for skills,
I found a really cool one called

watcher that finds blog posts
and other things online.

I'm going to install that skill
and show it to you later.

now here's the really interesting part.

I'm going to give Hermes a task
that it doesn't have a skill for.

I'll ask it to find the top three trending
AI repos this week on GitHub.

Reach each one's descriptions, summarize
them, and save the report to my desktop.

Hermes works through this for a minute,
asks for my permission,

gives me the results,
and then I see those three trending

GitHub repos with stars and descriptions.

And there's a nice file

saved onto my desktop
that has exactly what I want inside it.

If I want to save this as a skill,
I can just tell Hermes at the end.

Save this as a skill
so I can use it next time.

It's pretty incredible, right?

And that's the Self-improving loop.

Hermes literally teaches itself
new tricks as you're using it.

now? It will also ask me
if I'd like to make this a scheduled task

so it can ping me on telegram
every time it does it, So I'll say yes.

And there we go.

It was as simple as that.

Hermes has now created a repeating task.

Every Monday
I'll get the top three trending

GitHub repos
with descriptions and star counts.

Next up, I'm going to use the watcher
skill to find three recent blog posts.

Next up, I'll use the watcher skill
I installed earlier

to find three recent
blog posts from the Zapier blog.

It works the way it reaches out.

It finds the blog, then summarizes
the posts right there in my telegram chat.

Pretty impressive stuff right?

Okay, now
let's give Hermes access to outside tools.

You might have heard me talk about MCP.

It's short for Model Context protocol,
but you don't need to remember that.

Just think of it as a universal

plug that lets Hermes connect
to all other apps and services.

So in my instance
I'm going to use the Zapier MCP.

And this is really powerful.

Zapier lets Hermes talk to over
9000 apps with just one connection

Gmail, slack, notion, Salesforce,
basically anything you already use.

All you have to do is open your browser,
go to MCP, dot, zapier.com, click

the new MCP server option
and pick other from the drop down list.

Give it a name
like Hermes Agent and create it.

And now you can click Add Tool,

search for Gmail and pick
the action called Create Draft.

This is really cool
because you can scope permissions.

You might not want Hermes running
wild on your inbox,

but you can at least allow it to create
drafts.

Now we'll click on the connect tab.

Generate a token
and then copy the server URL.

Switch back to Hermes, paste in that URL
and ask it to connect to Zapier MCP.

It's as simple as that. Hermes
takes care of the rest.

Okay, boom. Hermes
is now talking to Zapier.

Zapier can create me a Gmail draft.

I'll ask it to summarize the blog posts
and the trending repos from earlier.

And boom, there it is.

Done. Open Gmail.

And that's my draft email.

now, if you don't want to pay per
message fees to anthropic or OpenAI,

you can actually run an AI model
right on your computer for free.

Most Mac studios
or Mac minis can actually run

something called Ollama,
which I'm going to download now.

I'll install it and then start it up.

I simply copy the Hermes launcher command
from Ollama, run it in my terminal.

It's going to ask me which AI model
I want to download.

Depending on how powerful your computer
is, you can choose different models.

A pretty small snappy one that works
well is Gemma.

4. It downloads the model,

it takes care of the installation
and it sets up Hermes with Gemma 4.

I didn't need to change anything now.

No internet needed,
no per message costs and complete privacy.

Now I can check by
just typing in full slash model.

And there it is. I'm using Gemma 4.

I can talk to it, Gemma 4 replies to me,
and I can even tell it

to draft an email in my Gmail inbox.

Signed off

by Gemma 4 takes a little bit longer
than the cloud model, but it does it.

And look at this.

There's the email sitting in my inbox,
drafted entirely by local AI for free.

okay, so here's a quick, honest
comparison of OpenClaw versus Hermes.

Well, OpenClaw has been around for longer.

It's got a much bigger community,
tons of tutorials.

It's backed by OpenAI.

Hermes is newer,
but it has a very good persistent memory.

It teaches itself new skills.

It works with any AI model
you want, including extremely well

with local models.

And it's growing crazy fast.

160,000 stars in under two months.

So the verdict
really depends on what you want.

If you want stability, OpenClaw may be
the way to go, especially with a new LTS.

That's long term support version
coming out very, very soon indeed.

If you want an assistant that get smarter
the more you use it, you need to go

Hermes and I have to say there's actually
nothing stopping you from running.

Both.
They don't interfere with each other.

You can test each one for vibes
and see which one you like.

If you want to give your agent superpowers
across 9000 plus apps, Zapier

is the fastest, easiest place to start,
and a link to get started is down below.

If it was helpful,
smash the like button on this video.

Subscribe
for more AI tutorials like this one

and YouTube is showing a video
on your screen now you should watch next.

Thanks!
