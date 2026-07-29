---
source_id: "d4ba4fea-ad06-4df2-9de2-ea16ff39c140"
title: "Don't Secure the Code. Secure the Coder."
notebook_id: 56999a7a-e52f-4e04-9335-342df85cdfde
url: null
type: youtube
exported: 2026-07-27
---

# Don't Secure the Code. Secure the Coder.
With agents, 

there's a behavior called reward seeking
which is you ask them to do something

and they're really,
really, really keen to do it.

And so they go up
and they try to do everything they can,

and they escape their sandbox

and they delete files
and they do whatever it is to please

If you cannot commit to the repository,
fail.

Don't like go off and sort of
send it in another way.

We need to move from securing the code
to securing the coder, securing the

the agent.

the attack vector,
but also the spectrum of what is there

is hard to follow and hard to secure
because we want to enable

AI as a force multiplier.

But in the meantime
we also have to mitigate the risk.

So we find ourselves in this kind
of carrot and stick mode security.

If it doesn't become agentic,
it will never keep up.

The AI Native Dev is a podcast
for developers and engineering

leads at the cutting edge of AI
and agentic coding.

Join your hosts, Guy
Podjarny and me, Simon Maple.

Every week as we chat
with the most exciting voices in

AI and tackle the biggest questions
facing developers today.

This is the AI Native Dev.

Back in November,

we hosted the first ever in-person
AI Native Dev con in New York.

This June 1st and second,
we're bringing it to London.

It's two days built for AI Native developers
and engineering teams, one day

full of hands on workshops
and one day full of practical talks on

agent skills, context engineering, agent
orchestration and enablement platforms

and how teams are actually shipping
AI in production.

Join us at the Brewery in London
near the Barbican for all of that,

plus networking parties, giveaways
and a room full of people.

Building the future
of AI Native Development.

You can also join us from anywhere
in the world via the live stream.

As you're listening to this podcast.

You get 30% off your ticket with code
POD30.

Just head to ainativedev.com
and we'll see you in London.

Hey there, Simon Maple

here at the AI Security
summit here in London.

This is a great conference to talk about
all things security in AI development.

There are going to be practitioners,

and there are also going to be loads of
CISOs and security leaders at this event.

Now Tessl's here, we've got a booth
and we also have Guy here, previous

founder of Snyk
as well as the founder of Tessl.

And Guy is going to be giving a session

talking about security
keeping up with agentic development.

Let's secure not the code but the coder.

Because how can we make developers
think more securely

when using agentic methods
and agentic tooling?

Cool.

Let's see if we can talk to a couple
of people while we're here.

So now I'm

here joined by Brian Vermeer,
a Staff Developer Advocate at Snyk.

And we go back a long, long way.

Brian, you've been on the podcast before,
and we're now here at your event.

What's your event called?

This event is called
the AI Security Summit.

And what is it about?

Well, it's about AI and security.

I think the name says it all, but with AI,

there comes
a lot of new security attack factors.

And what do you need to think about?

How do you need to transition
from old fashioned to, say,

software
dependency analysis and software code

analysis to now 
driving your code agent
to creating your code,

but also things like skills and MCP
and that kind of stuff.

So like shifting gears
into that space of security.

Amazing.

And you actually gave the intro speech

at the at the leadership summit
that we just had across the road.

also at the main event here.

What would you say the biggest issues
that that are on

the CSO minds today when they're thinking
about their organizations

trying to adopt and roll out
AI really as fast as they possibly can?

What do people coming to you
complaining about?

I think it's a very good question.
I think it's multiple things.

First of all, people are not aware,

like what kind of
AI is already in their systems.

They think they're not using any models
or maybe even any MCP servers.

But in some cases, even your agent
can decide to pull in a certain model

to get track of something else.

So things like shadow AI or

employees just using their own
free ChatGPT account to do things.

So the attack vector,
but also the spectrum of what is there

is hard to follow and hard to secure

because we want to enable
AI as a force multiplier.

But in the meantime
we also have to mitigate the risk.

And these are things that CISOs are
challenged by.

So it's
almost like a problem of discovery.

And this is really interesting

because this kind of like reminds me,
if you think back around, you know,

I guess where Snyk originated from,
when we look at dependencies

and trying to identify dependencies, what
people are using in their organization,

a thing was created called a software
bill of materials, where we kind of like

these are all the dependencies
that we use.

Do you feel like
something is equally needed now

from a from an AI point of view?

Like what are the things I like?

There are things like AI BOMs — like,
where is the training data coming from?

From my models.

But what about things like context
where you mentioned skills and MCP

and things like that?

Do we do we need like a context, building
materials.

Maybe even that the AI build materials
is a thing already and we scan for that.

We can we can create that for companies.

But I also think like the context
or the skills that you pull in, it's

basically a dependency as well, right?

If you look at how software was developed
and you pull packages

from and from from repository
as your your third party

entry points,
now you have that with skills.

And so the problem here
now is that skills is just text,

Yeah.

And now we need to scan that
to see if there are no injection in it.

If if there are no hidden
hidden comments in it or even worse,

it has a hidden comment in it that is
getting copied to your global memory.

And then even if you delete the skill,
then it's still there.

So it's back to our basics.

As in, make sure that whatever you ingest
or use is validated and vetted

and keep track of that, just like we did
with our Docker containers

and with our dependencies
and the code that we wrote.

So we need to be aware
that that things can go south, even though

most of the stuff that are agents
nowadays are creating is quite cool.

And of course,
we recently announced the integration

between Snyk and Tessl,
whereby we expose a lot of that data

that those scan results from Snyk
within the Tessl registry.

So if you are using skill,

you can you can identify
if there are threats through the Snyk

as a judge style approach to identify
where those potential issues issues are.

What one piece of advice
would you give people

who are using AI in an organization today
as a super quick way,

a super quick way of really reducing risk
within their organizations?

Have a good overview of
what are you using currently?

Because if you don't know that data,
you cannot protect yourself.

And secondly,
make people aware of these choices

and of the of the attack vectors
that are coming in.

Because I think most people
that are not tech savvy

and are now using agents
to build their own self aware,

if you can call it like that, the
their own tooling are not aware

that if you connect this piece of data
to that piece of MCP

server, that we can leak data
and these kind of things.

So awareness is the first point. Amazing.

For those of you

who want to learn more
about the integration,

we actually did a podcast,
a full podcast episode.

So check out the AI Native Dev Podcast
with Brian Vermeer.

And we did that in Atlanta. Beautiful
sunny Atlanta.

Now we're in kind of cloudy London,
but it's all good.

And enjoy the rest of the conference.
Brian, thank you very much.

Look on now for Sam Stepanyan.

Stepanyan.

Who is the head of the OWASP London chapter.

And you're also on the global board
for OWASP generally, right?

That's right. Yes.

Awesome. So.

So what are you here to learn today
at at this event.

As always. Right.

We learn every day
and AI is moving so quickly

and cybersecurity moving so quickly here
to learn from all the peers and colleagues.

And of course for you guys,
what is new in the world of AI security,

what new solutions are and what
new challenges are you currently facing?

Because there is so much new stuff
happening at the moment.

So also conversations around
OWASP, right?

And also for everyone, obviously,
because I represent OWASP

what you see is how our OWASP Top Ten for

LLMs, and the brand new OWASP Top
Ten for Agentic AI is impacting people.

Because I had several conversations
days ago

at the AWS conference for our products,
and there are lots of

companies
were just trying to get into the genetic

AI world and have like zero clue

about security issues,
which can meet of that.

You mentioned the top ten, and of course,
for those who don't know, is obviously

a nonprofit organisation that governs and provides
a whole bunch of resources.

Sorry. Yeah.

And provides a whole bunch
of best practices and great advice

for a ton of different spaces.

So the top ten for web applications

and security and web applications,
mobile applications.

Cloud security approach.

And you mentioned the top ten now
for AI and LLMs.

What would you say.

Kind of like the biggest mistakes
that people make as as developers

or as CISOs when thinking about
building using tools and AI.

The biggest mistake
is they completely ignore security issues.

They jump straight in and they connect

AI directly to their production system
without understanding

the consequences of it.

Yeah,
and I think it's due to the huge pressure

that everyone's feeling because everyone's
trying to jump on the AI train

and they're trying to, of course,
use the technology and innovate.

But the fact that a lot of them
are ignorant about cybersecurity issues,

which is about AI, 
makes it, of course, quite worrying.

It kind of reminds me the same situation
that we had at the e-commerce

25 years ago when everyone said, oh,
this new thing called the web.

We have to do. We have a website

and we must have an ecommerce,
so we must sell things online.

The whole digital transformation, right?

Let's start taking credit cards online.

And no one thought about security
and everyone started.

Getting hacked.

SQL injection was number one vulnerability
back then and the same thing here.

But I was saying, oh, let's all use AI
and no one thinks about, you know, basic

hygiene, things like prompt injection,
but also, of course,

lots of other 
security concerns surrounding AI.

And we do provide OWASP

free and open source guidelines
and resources and standards for you.

There was a
one of the very important documents

we have which I recommend to everyone
is a secure AI adoption guidelines.

So I highly encourage other organizations
who are trying to adopt AI.

Check out this document which is community
created the community to it

so they can understand
how to adopt AI security.

And you mentioned like the pressures
behind businesses who are like

not being forced necessarily,
but very, very much encouraged to use

AI pressure to use AI as fast as they can.

Because realistically, businesses
that don't in 1 to 2 years.

They're potentially going to be
at a very strong,

very big disadvantage to those
other companies that are moving so fast.

So from the point of security securities,
very often seen historically

as a department
that can slow down delivery, how

how much is that kind of like seen today
in the world of AI is that is is security

seen as something that is is hampering
the advancements of AI in organizations?

Well, that depends how you approach it.

And I would always say that
no security is an enabler.

You know,
it's like the brakes in your car

actually allow the cars
to move faster, right?

So the same thing with AI security world,

you can innovate fast and secure manner.

But all that you need to do,
you need to be aware

of all the security implications
and make sure that your innovation

security experiments, they start
from their isolated environment,

which is secure, right, and disconnected
from your production data.

So if things go wrong,
it goes minimal damage.

And obviously in the isolated environment
you can actually learn

how to secure it properly for all of us

and also other industry guidelines.

And one very important point,
which I'd like you to make

is also remember that
AI is non-deterministic.

So let's say one thing today
was a little different than tomorrow.

Another very important thing

that not many people are mentioning
today is the problem with agentic

identity is the issue that at the moment,
the way how

AI integrates with other things
is that it acts upon humans behalf,

which makes things like traceability
and audit

and logging of actions
is very, very difficult

because if you grant an AI agent
accessing your email box

or your behalf and it's going to go inside
sending emails, sending out

spam on your behalf,
or it's going to go and start

deleting and accessing or deleting
customer records.

It's not Simon, it's not Simon.

AI at Tessl IO, it's Simon.

Oh yeah, it wasn't me.

It was my agent. Yeah, exactly, exactly.

Now, 
I was chatting with Brian Vermeer earlier,

and he was talking about one of the,
one of the,

one of the first things that people do
should do is understand

where organizations are using AI,
how big a problem

is, almost like the governance
or the understanding of

where people are using AI
in their organizations today.

And there being too much,
almost like shadow AI.

There's a lot of shadow.

I believe it's a big problem
in organisations

where they don't have proper governance.

Yeah.

Of the IT projects

and if they allow their developers to run
free and wild

and innovate on their machines

and install whatever they like 
and particularly specific tool and say

small organization startups,

because I usually work with organizations
and highly regulated industries, such

as services, where such governance exists
because of compliance.

Regulations are not all industries might
have this kind of compliance regulations.

Yeah. This is why. Researching this.

And so the actual problem
of finding out who is using AI,

where is this use, which models are using,
how they actually access it.

It is a little bit problem
because if you don't know what you have,

you cannot possibly secure it.

So do we need
do we need AI compliance regulations or do

we need an upgrade to existing SOC 2, ISO
and things like that with, you know.

One of the things that I'm seeing
will be coming up with

something called AI Bill on material.
Yeah.

So at the moment we have software.

So now there's an AI BOM emerging.

And obviously we do have an inclusive
you can actually help you with that.

We have a tool
which allows you to discover

your bill of materials based on the model,
and also scan your repositories

and see where developers
are using specific libraries.

For example, there was recently a.

Actually.

There was a supply chain attack on a
very popular library called LiteLLM.

Right? Yeah.

Do you know where in your organization
light is in use?

Yeah, yeah, I use it.

The vulnerable version,
which was hacked. Right.

We we can now
because we have played open source tools

which can actually help you
to get that inventory.

But obviously there's
a lot of other companies in the sector.

But the problem is that you need
to understand the actual challenge.

As you mentioned, the shadow AI or
shadow IT, you don't have the inventory.

You will not be able to secure it.

Do we need the inventories
that you mentioned are really great,

like the software building

materials, the AI building materials,
which mostly focuses on models.

Context is something that is used more
and more these days, skills and contacts

that lives in developer 
environments, in projects.

These are things that are being used
to create the code.

They're very, very key and they're
just not being audited right now.

Do you feel we need
is there a space for a context

bill of materials or something
that should be added to an AI BOM

to include what context
was used to generate this code?

I think that's
a very interesting suggestion.

So we have a whole group at our studio
which is currently looking at it.

And one of the things that you mentioned,
skills, you actually have a new

working group which is creating a new
AI agentic skills Top Ten.

Oh nice development.

I need to join this.

I need to do.

This because just like all of US
projects, it's an open source project.

So we highly encourage contributions
and collaborations from everyone.

Amazing.
I will join and I will contribute.

Thank you very much Sam.

Always a pleasure
and great to see you here.

Thank you very much. Thank you. Thank you.

Hey everyone!

Hope you're enjoying the episode so far.

Our team is working really hard behind
the scenes to bring you the best guests,

so we can have the most informative
conversations about agentic development,

whether that's talking about the latest

tools, the most efficient workflows,
or defining best practices.

But for whatever reason, many of you
have yet to subscribe to the channel.

If you're enjoying the podcast
and want us to continue to bring you

the very best content.

Please do us a favor
and hit that subscribe button.

It really does make a difference
and lets us continue to improve

the quality of our guests
and build an even better product for you.

All right, back to the episode.

Great.

So we've had a couple of chats already.

We've heard the opening keynote.

The time now is 11:20, which is just about
time for Guy Podjarny's session.

Don't secure the code.

Secure the coder.

Can security keep up with the tech dev?

We've had some great chats

with Amy here and the team with a whole
bunch of people on the on the expo floor.

Let's go up and see what Guy Podjarny's
session is like.

And I want to introduce
somebody who is quite dear to me.

I know this man for a couple of years.

Guy, please come to the stage.

Give it a big hand.

Guy will talk about obviously.

Development Guy is the founder

and CEO of Tessl
and also the founder of Snyk.

He was the person who was crazy enough to
hire me.

And I'm still here.

Guy will talk about definitely talk

about things like skills,
but also about how agentic development

has evolved and can security
actually keep up with this?

I think it goes well,
along with my introduction

and the introduction that Joe gave.

So with without further ado
and not killing all the lights on stage,

I will leave it up to you. Thank you. Guy.

Thanks. Hello everyone. Can you hear me?

Is this coming through?

Do we have the slides up?

Cool, cool.

So, yeah, I'm Guy Podjarny,
I'm the founder of Snyk.

The chairman of the board.

But I'm here with a different hat here,
which is a couple of years ago,

I fell in love with AI

and went to found Tessl,
which is in the AI development space.

And in that a lot of our work focuses
on sort of

securing for the agent era or in general.

How do you develop software
in the sort of agentic era?

What's the 
the new paradigm that we have to adapt to?

And security is an aspect of that.

And in that a lot of the kind of the core
new world

moves us from software development
and security revolving

around the implementation, revolving
around the code to revolving around

instructions and intent, because we're now
driving and guiding agents.

And so that's kind of the

theme of my kind of points over here, is
We need to move from securing the code

to securing the coder,
securing the the agent.

So it's no secret that AI is transforming
software development.

And while we had a

bunch of very good examples here about non
software development flows on it,

I think software
development is a good harbinger.

Sort of like Canary to say
this will happen to all knowledge work.

So I'll focus very much about that.

And in software
development we've gone from

from AI augmented software development
that was pioneered by Copilot

and then cursor
that it's more about aiding your coding.

And this helps you write code to
AI native software development.

That is more about delegation.

It's more about the agents
in which you're asking the agent

to do a task for you, and it goes on
and and performs it better or not.

And this agent development is
where everything has consolidated towards.

And so today, I think, again,
not a controversial statement to say

we should focus on what is
how do we secure agentic development

as the mental model for us.

And the development is amazing.

It's powerful.

A single person can do so much to it, but
it introduces a bunch of new challenges

as compared to how we've been dealing
with software security before.

And again, this is security
and software development as a whole.

And I'll mention three big ones here
that I'll focus on in this talk.

One is it's non-deterministic.

So we use the software that if it compiled
once it will compile again.

Right.

We're used to to things
that that are the risk

that we can say this now works
I scanned it.

It didn't have it. I'll scan it again —
it still does not have it.

It's the same findings that I get.

And that's no longer
the case with agents Or with agents.

We have to make do with the fact that
these are non-deterministic creatures.

We have to get statistical.

We have to say, well, it works nine times
out of ten, 99 times out of 100.

How do we handle that?
How do we even find out?

Second is, as

mentioned, it revolves around intent
or instructions, not code.

So what is the sort of new unit
of software that we need to secure here?

How do we evolve our security

and improve our security
of securing the coder?

So that's a new challenge for us.
And I'll talk about that.

And then lastly,

as you might have noticed, it
changes at a certain kind of rapid clip.

And so software development as a whole
and the need for security

and a bunch of other aspects of 
the knowledge

domain are moving
and changing faster than ever before.

So how do we deal with that?

So there are clearly many aspects of agent

development that I don't cover here,
but I'll focus on these three.

So the first and

biggest one is the fact that agent dev
is non-deterministic.

And that really reminds me of this
sort of DevOps ethos that we have, right.

In DevOps.
We were saying if it moves, measure it.

If it doesn't move, measure it
in case it moves, know.

It's like the most statistical creatures
that we have in our disposal

today is these servers
that are sometimes up and sometimes down.

They're not really behaving
as they should.

And so in this world you have to say,
well, you can't optimize like the,

the learning from there was
you can't optimize what you can't measure.

Right. It's a pretty simple statement,
but it's a good one to remember.

So how do we measure agent behavior.

How do we think about this.

Well, generally

there are a lot of very evolved ways
to do evaluations or evals in AI world.

But typically what you would do is
you would create a task for the agent,

hey, agent, here is a task
and I'll use 11 labs

intentionally starting from non-security.

So 11 labs is a very successful London

based kind of text to speech

lab or AI lab, and they have an ability
to generate music.

And so we can give it a task,
for instance, in this case

a dynamic soundtrack generator
for a game studio.

And then you define up front some criteria
to say, what does good look like?

Like what is what is correct
implementation of this.

And then you run
that task across the agent.

And what this plot shows is it
shows five different scenarios.

We have our sort of dynamic
soundtrack over here,

but I have five others in areas that I ran
each of them ten times and I scored it.

And you can see a few things

like already you're a little bit
more informed, for instance.

You see the lines are not very high.

The scores that the the agent got for
this is not very good.

And that's
because the music API is relatively new.

So it's not well represented in the,
in the sort of the model right,

in the weights.

And so they don't
really know how to handle it.

And so that's one problem.

The second is that you see
the dots are all over the place.

Like we asked the agent
to do the same thing again.

Again sometimes you see
kind of like normal scatter.

Sometimes they'd do better, sometimes
they'd do worse, maybe within a range.

And you have some other cases
where it kind of hit the mark.

Right.

It sort of guessed correctly
one time or two times and then it doesn't.

These others.

So we have this mess
and it's very hard to work with that.

So clearly said, well,
how can I make it better.

How can I make it work better?

How do I kind of train the sort of agents,
how do I harness them?

And harness is actually a different word.

I didn't say that. Ignore that word.

And then and it's sort of the most common
kind of way to do that is with context.

And the most common unit of context
that is used today are skills.

So these are basically markdown files
a little bit more with some structure.

But these are bits of information
for the agent to use

to be able to perform this task.

And we need to remember that
knowledge is not the same as intelligence.

The the models can be brilliant
and very, very capable,

but if they don't know something,
oftentimes they just can't do it.

Or it's just mighty inefficient for them
to do that so they can figure it out.

But they will be
there will be statistics there.

And so in this case, we have an 11 labs
music skill that helps explain the API.

And so when we run, when we use that
we indeed

see that for our dynamic soundtrack
generator.

And I'm using Tessl
here to do the evaluations.

You see that without context
it didn't do a bunch of things.

It did.

It used the deprecated package, it didn't
import it correctly and all that.

And with the skill with the context,
it got it done.

So it got a 50% average without the skill, versus 98% with it.

So it's good we managed to correct it.

And if we run this across the line,
we see in some cases we just solved it.

It just basically now is sufficiently good
to fairly consistently do the task.

And in other cases it's still slightly
varied, but it's further up,

so it is more capable of doing that task.

So this is the type of way
in which you evolve

and you improve your agents ability
to do something.

This is a security event.

So how do we talk about this for security?

Well, let's take another example.

Code guard is something that Cisco created
and donated.

And it's basically
a bunch of sort of OWASP security

kind of rules packaged up into a skill.

And and it helps kind of these

AI developers,
these agents develop more secure code.

So let's put that to the test.

I created
six different evaluation scenarios.

And I specifically focused
on authorization.

How well did you handle the security
of authorization in this code.

So for instance
hey agent, create an access control

test suite for a project management API
and then created a bunch of scores for it.

And I did it with and without code Guard.

And as you would expect, it got better.

So without Code Guard,
just as is, the agent scored 48%

on my kind of authorization criteria,
sort of a scorecard.

So not awesome.

And if it had these instructions
nearly 1.6 x the improvement on.

So it got a fair bit better
because there was a bunch of guides

about how to sort of code securely,
including authorization.

So that's that's good.
That's already useful.

However, if I took all the information
in Code Guard

that has a

lot of security practices in it,
and I shrunk it down to just the

authentication and authorisation related bits,
which are, I think about sort of 5%

of the total content.

If I remember correctly,
it did a lot better.

It went to 98%.

And this is
this is sort of a core thing to remember,

which is more context
is not necessarily better. Right.

If I sat here and I told you 100 things,
no matter how sort of brilliant or dumb

they were,

you will notice you'll give less attention
to each one of them than if I told you.

Three and attention is a scarce resource
with humans and with models.

And so choosing and managing.

What is it that you say that
actually matters that the model doesn't

already know,

like not wasteful information
that there's no point in saying

is important
and is a part of that competency.

Taking that a little bit further,

you know,

if this is the graph
that shows the same numbers

from before of code guard, not guard,
you also might be surprised

to hear the different agents respond
to the same information differently.

So this is an example of the same test.

In fact a whole 
it's literally the same execution.

And what you can see is different models
respond differently.

Opus and sonnet at the top
they get about the same results.

Even though opus is more intelligent,
it is more expensive.

So if you use the opus for this specific
task, you kind of wasted money

and probably time
because you could do the same with sonnet.

And what you can see is codex and cursor.

They respond even differently
and it doesn't matter which one is better.

Like it does matter eventually.

But that's not my point, but rather

the fact that different agents, again,
almost like humans, listen differently.

And so you want to know
that your instructions

are effective, are not wasteful
for the agents that you are using.

So that's kind of core point here
is if we want to secure

agents, we want to use skills to help them
secure code or write secure code.

We have to learn how to measure that.

And how do you
how do you build good context.

Like how do you how do you evolve it?

How do you create kind of quality context,
you know, how to build.

So where to talk a little bit

about the fact that you generate
you create a skill, you evaluate it,

and then once you've evaluated,
you can optimize it

until you kind of get a better
and better guidance for that agent.

And then you need to distribute
that or communicate it.

If you want to use the human mode to the
agents and observe what has happened.

And the observe is important.

If the evals are kind of like your tests,
once you've got something working

and you make a modification,
how do you know you're not breaking it?

How do you know you're evolving it?

How do you know
if you can use a cheaper model or not?

You have to be able to evaluate,
but eventually

your test will go out of out of sync.

They would not represent reality
if you don't also observe

what is happening.

So we call this
the context development lifecycle.

And as you build

good context, you can use that context
across the software development lifecycle.

So we think the CDLC is
where us humans should live.

We should be building good context
that guides the agents.

And then we should apply that to the SDLC
where the agents should work.

And the same context,

the same instruction can be applied
end to end in the development process.

Same as like a great developer on the team
will use the same knowledge

to define a product feature,
write the code, troubleshoot something,

ship it to production, troubleshoot
an incident, etc. etc.

the same knowledge is useful

across the board,
so the skills represent that knowledge.

And of course, from a security lens
perspective,

we can now use that
to secure different steps.

So this is this is how you should 
write secure code at the beginning.

This is what I want to audit in the code
review to highlight to you.

This is what I want to get on.

This is what I want to inspect
when an incident occurred.

So all of these things can be represented
in skills that we use across the SDLC.

So this is non-deterministic.

It's kind of my biggest point to make.

And as we as
we learn how to evaluate those.

The second point is

we've been talking more
and more about these skills

and we're sort of optimizing these skills
and we're developing these skills.

And I think it's useful to start

thinking about skills in terms of
their own security as a unit of software.

Right. It looked like a markdown file.

They look like a notion document
or like a confluence document.

But the way we process them
is we execute them by the agent

or the agent execute them.

So really, I think we're well served,
especially from a security lens,

to think about them as a unit of software,
not just as a piece of text.

And we have like a lot of indications
of that today.

Right?

We have the Snyk study,
and there were very many others

that showed,
especially in the open Claude world,

where a lot of skills were malicious,
literally attackers putting in things

that are trying to make the, the,
the agent to do something it shouldn't.

Here's an example of a malicious skill.

This is from the Tessl

registry scanned by Snyk,
where it had a bunch of that it down.

And while most of your URLs
were just standard blockchain

APIs, one of them was suddenly downloading
a password protected zip.

Fishy doesn't sound right.

Okay,
that's potentially a malicious skill.

There's a bunch of things

we can do, clearly imperfect,
but we can try to detect malicious skills.

There are also vulnerable skills.

What's a vulnerable skill?

For instance, a skill that uses insecure
credential handling.

It asks the user to put API keys inside,
or it makes MCP calls

with sort of plain vanilla tokens for it.

So that's an example of something
that is insecure behavior.

It's vulnerable
to exfiltrate some information outside.

There's also like new types of flaws
that you might have in what I

this is not an industry term, but what
I like to think of as negligence skills.

So these are skills that do not have

some basic safety
instructions inside of them.

For example: check
this into a repository.

Do not make it a public repository.

If you cannot commit to the repository,
fail.

Don't like go off and sort of
send it in another way.

So a bunch of these types of examples
are very real examples.

And we have cases where we've had agents.

There's a behavior called reward seeking
which is you ask them to do something

and they're really,
really, really keen to do it.

And so they go up
and they try to do everything they can,

and they escape their sandbox

and they delete files
and they do whatever it is to please you.

And so you have to define
a little bit of these safety instructions.

It's kind of similar
to what Brian's example was on.

Right to say do not disclose information
that makes it at least less negligent.

And then again, similar to software,
there's a question about supply chain.

How do you consume these skills today?

The reality is that people
just consume them out of GitHub repo.

They download them from wherever.
You have no idea that it happened.

You have no idea where it's there.

Then they check them in
to their repositories.

Different agents
read them from different places,

so you might check them in seven times
the different folders within your repo.

It's not.

It's early, it's fine, will improve.

But for now it's not awesome.

So you have to think a little bit

about supply chain.
So all of those become obvious

once you think about skills
as units of software.

So what do we want to do here.

Like what is what is enterprise grade

kind of skill governance
skill usage on it.

This is a nascent space.

I'll give you the lens on it
because this is our world.

We think you need to think about

three different elements
of of evolving this piece of software.

First is governance and security.

Know what the hell is going on?

Try to sort of audit
the use of it — like, you've posted skills.

Did anybody install them?

Constrain the use of skills.

So people download skills always through
this sort of centralized path.

Again, not that dissimilar

to what you should be doing
with NPM libraries or whatever.

And so you have to know
about the governance.

If you can't do that,
you really oftentimes cannot roll out.

Once you rolled out, you have a need
to standardize and allow reuse.

If three different people created a skill

to review code,
and a fourth person comes along and says,

I want to use a skill like, first of all,
where do they find it?

Second is, how do they know
which of the three to change?

If I created a skill
and then one of you came in

and proposed the modification,
how do you know if it's good or not good.

If I now 100 people are using this skill
and I'm

going to make a change to the skill,
how do I know that I'm not breaking it?

And so there's a bunch of this notion

of standardization, of reusability
that you have to create a measure.

And then lastly, and this is
the holy grail is continuous optimization.

You want to know that this is that CDLC —
that we want the continuous optimisation.

You want to observe what has happened.

Did the agent fail?

Did the user need to correct
the agent and take that information

and route that back to be able to evolve
the skill, create new eval scenarios?

And that is the holy grail.

And the companies that are at the cutting
edge are doing this right.

They are creating that optimization.

Most organizations are quite far from it.

And so that's why
this is oftentimes the sequence.

I'd be

remiss if I didn't do a little bit
of a Tessl plug over here.

So that's oftentimes what we help you do.

We have a platform in which, on one hand
from a

from a development perspective,
we help you collaboratively develop skills

that allow developers to discover
and install those quality skills

and then observe what has happened,
learn from that and create new paths.

And then within that
we have these these controls.

So we have the ability to now
make sure with Snyk we scan every skill

that gets published into the
into the registry.

So you know that it's not malicious.

Similarly, when you install
we have controls about scan from us.

We have analytics about who's using what.

And then lastly for the sort of these
nascent agent enablement

teams, these platform teams, developer
experience team AI enablement teams

that are that own successful
rollout of agents in the organization.

We give them a bunch of these abilities

to eliminate duplicates, drive
skill usage, optimize costs.

I like to say that agentic development
is cheaper than expensive.

It's like very cheap at the beginning

because a single person can do so much
and then you get the bill.

It's not that awesome.

So you start thinking,

as we use agents more and more,
what is the sort of the cost?

And those, of course,
you know, a moment with the Snyk hat on,

we have some amazing other aspects

of securing the agent behavior itself
and its runtime in Evo.

and I'm sure you'll hear more
about this over here as well.

And then to close off,
I want to talk about the third bullet,

which is agentic 
development moves faster than ever

and security must become agentic
to keep up.

Sounds very familiar to me
from the Snyk early days.

And when I when I hearken back to
what happened, the Snyk roots.

You think if you're a graybeard like me,
you think about the change

that happened there
when we went from waterfall

to cloud and some behaviors,
some manual processes

and such were tolerated in waterfall
and were no longer tolerated in cloud.

The idea that before
any piece of software will shift,

someone will manually audit
it was tolerated.

You know, like the best teams
automated the security scanning of it,

but most people manually audited,
so the average team did not.

In cloud. That cannot be the case
once you're in DevOps.

Once you're in that continuous,
you have to automate that scanning.

I think we're facing now the same thing,

which is some
things are tolerated in cloud.

The best teams are automating them.

They're sort of reviewing them.
They're auto improving them.

But most teams are not.

And they're no longer
going to be tolerated in agents.

So there's a little bit of like

the future is here,
but it's not evenly distributed.

We should think about all these things
that are like

the paper cuts that we have, the places
in which like, you know what?

As a security person, I will triage
these vulnerabilities for my developers

or I will, you know, maybe we'll only fix
the ones that are truly glaring.

We're not going to fix the rest.

Many of these things are just no longer
an option.

So you have to think about
how do we improve them.

And there's a long list of those.

There are many, many,
many things that go from nice to have to,

must have from indeed prioritization
to automating upgrades

to detection
of supply chain manipulations.

Like there's just so many things.

This is really just a tiny sample set.

And the good news is that for each
one of those agents can really,

really help in making these automated
like it's agents all the way down.

Right?

You can build agents upon agents
that will do a bunch

of these different steps,
and that allows us to scale.

And So we find ourselves in this kind
of carrot and stick mode security.

If it doesn't become agentic,
it will never keep up.

We will fail.
The attackers are becoming agentic.

They're moving faster than ever.

The development, like the business, has
to be agentic to be able to to develop

and we have to keep up over there.

So if we don't become agentic,
there's a bit of a, you know,

like you're going to be in trouble.

But if you do,
if we do become agentic in the world,

then we can actually fix application
security.

We can actually fix those things
that we've long wanted and tried to get

developers to do on a consistent fashion,
which to me is exciting. So

I'm excited by the new future.

I'm slightly daunted.

I think there's a lot of need to change 
just to plug.

We have a conference
in a couple of weeks here: AI Native Dev Con.

It's running here in London
June 1st and second.

If it's all about agentic development,
adoption like real world scenarios

actually in kind of organizations
that have it, if you want to check it out.

I think Brian might be speaking.

And also I think we stole you
to a different one in the previous one

and a lot of learning on it.

Would love to see you there if you'd like.

That's it for me. Thank you.

What a day. At the AI Security Summit.

We had some great discussions
on the Tessl booth.

We had some wonderful chats
on the showroom floor.

We had some great sessions, guy
in particular, super enlightening

about securing the coder,
not the code from AI Security Summit.

Wonderful day.

Thank you very much.

Snyk. And everyone here.

The AI Native Dev is brought to you by the
package manager for skills and context.

Your hosts are Guy
Podjarny and me, Simon Maple.

Our producer is Tom Dowler.

The AI Native Dev is not just a podcast,
it's a community.

And we host monthly meetups
at the Tessl offices in central London.

Visit tessl.io/community
to learn more and I hope to see you there.
