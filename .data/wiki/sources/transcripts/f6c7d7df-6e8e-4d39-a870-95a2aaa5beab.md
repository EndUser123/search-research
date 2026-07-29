---
source_id: "f6c7d7df-6e8e-4d39-a870-95a2aaa5beab"
title: "How I Fully Automated My Video Editing With Claude (No CapCut)"
notebook_id: 23bf4931-d0cb-4550-9d11-f9b38843254a
url: null
type: youtube
exported: 2026-07-27
---

# How I Fully Automated My Video Editing With Claude (No CapCut)
so I just built an AI that edits my videos for me

and I built it inside Claude

and I'm not talking about just the captions alone

I'm talking about the whole thing

the titles the call outs

the transitions and the graphics that pop in

and I never really had to touch a timeline

I've been working on this for a really long time

so I'm really excited that I can finally like

share this with everybody

because here's the truth I love making videos

people ask me why do I do this

I love making videos but I really hate editing them

you can record an 8 minute tutorial and then you end up spending 3

4 hours just dragging text boxes around in CapCut

and lining up everything the caption

hunting for the right moment to drop a graphic is the reason

a lot of people just post raw

boring footage

and I sometimes do so or they end up not posting at all

so I thought about how to fix it

and I turned that whole job into a cloud skill

basically a custom skill I taught cloud once and that's it

it runs every single time

it reads my transcripts it figures out where every title

call out and transition goes on and brand automatically

like you see right now and then it renders the finished video

and the graphics these are generated with Google Nano Banana

which is Google's image generator model

so I get custom branded icons instead of like boring stock

and the edit that used to eat up my whole afternoon

or my whole evening

just runs in the background

and I built all of it with no code

so in this video I'm actually going to show you exactly how

so that you can build your own

so let's get right into it

if you are not already subscribed to my channel

please do hit the subscribe button

and also like this video it goes a long way to help support my channel

and it encourages me to keep bringing

more valuable and useful content as well

so all I have to do is again

I just come in here

I make sure that I'm in the folder and I say something like

can you edit the first uh 30 seconds right

I'm just just for the purposes of this tutorial

so that we don't spend forever of this video

and let's see what it does

you see that

it would actually run through all the files and call everything

and then do the editing for me in the background

and while this is running

I can actually be doing other things on my computer

and I don't have to like um

sit around okay

so this really saves me a lot of time because like

I work a full time job I have toddlers

I run a business so I'm very busy

so I just always try to see how I can cut time here and there

ask for help when I need it

but then if I can also use AI to do it

I'm a solopreneur

so if I can leverage AI a tool I'm already paying for then why not

you can see that it found the video here

it's telling me that this is the 16 by 9 tutorial

it's saying that it's just gonna edit the first 30 seconds

it's realizing that I've made a mistake

in the pronunciation of Opus 4.8

so you can see that it's actually like correcting it for me

so it's gonna correct the brand names and everything on screen

and it's actually loading up everything here as you can see

so one thing I really like about this skill is that before it sort of

like goes ahead

it actually gives me the plan okay

it gives me the plan before it goes ahead

so I just have to click on render as is

and you can see that it will basically like go ahead

it's giving me the plan intro script intro string the title

um lower third section title call outs and call outs right

so it's giving me that

and so it's it's basically gonna trim the first 30 seconds

this video is actually

the video is actually editing right now is my last video

which is the Oppo s 4.8 video I did

so it's it's I think it's about it's more than 8

minutes long but I just wanted to edit the first uh 30 seconds of it

so when this is done

it usually would just upload the video in the same folder and um

I can basically just um play it on my computer and if I don't like it

I can always come back and ask it to do changes and stuff like that

it's done right now so I'm just gonna come here

and I'm just gonna open it and see what is done so far

so Claude Opus 4.8 just launched

and before we go into the whole marketing language

let's first go into the benchmark table

because this is where things actually get interesting

so how does Opus 4.8 actually compare to Chat

GPT and Gemini now based on this benchmark table you see here

Claude actually or Claude

Opus 4.8 seems to be like the strongest

when the task involves agentic work

so you can see here agentic code

if I want to add in let's say more text more call out and all that

I can just go back into Claude and and ask it to do that

I'm in no ways saying that this is a polished way to edit videos

this is definitely a step in the right direction and for transparency

I do have an editor who edits some of my videos for me as well

so I do see that with this in place

I'll be able to bring out a lot of videos because again

my editor is also constrained

so it's good to have AI do some of the work for me

editor doing some of the work

and then I can actually save some time back

so let me show you exactly how I built this in Claude

if you don't know what Claude Claude has gone viral this year

but if you don't know what Claude is Claude is just like an AI tool

just like Chat GPT

Gemini and all that but then it has very wonderful features inside it

so one of the features inside Claude is called cool work okay

and cool cool work basically is really cool

because it has the ability to control things on your computer

so it can actually go into folders in your computer

it can actually browse the web for you

like it can do a lot of amazing things

so I'm using Cool Work and inside Cool Work

when you click on customize

for instance there's a concept of skills okay

there's also the concept of skills in Chat GPT

and then there's a concept of skills in Claude cool work

skills are basically reusable capabilities

so you define them once and then you can call them

I've created a number of skill packs

that you can use across your business

on your personal projects

I'm gonna leave the link to those skill packs in the comment section

so that you can check them out

so skills are typically in a file called skill dot MD

MD meaning markdown language

so inside the scale as you can see

I've actually defined how this exact process should work

so I'm talking about something like Ffmpeg okay

now if you don't know what Ffmpeg is

Ffmpeg is really a free open source

command line tool for just working with audio and video files okay

so you can actually use Ffmpeg to convert videos and audio formats

you can use it to compress large video files

you can use it to extract audio from video

you can use it for trimming

cropping resizing

rotating or even merging videos

and I do believe I have a video on this channel

I was using NHTN I think NHTN and Ffmpeg

if I'm not too sure

I use Ffmpeg to help create like a faceless YouTube channel

so that you can always autopost stuff

so that is really what Ffmpeg does

it helps with like adding subtitles or watermarks

and you are able to change the frame rates

bitrate resolution

Codex and more

and you're also able to stream or process media in real time

so if you're someone who is like into video editing

okay or graphics

that kind of thing you're probably familiar with Ffmpeg

and the good thing about Ffmpeg is because it's open source

it's free free

so you can basically download it and use it as well

you can also use it to convert different files

but anyway for the purposes of this particular scale

I'm using Ffmpeg with

to help with like the motion graphics and everything

and the way it works is that I provide a transcript on the video

so when I'm in Claude let me come back in here

when I come into Claude

so I basically come into Claude and I click on Working Projects

and I scroll down and I choose the folder has my my videos

okay so I come in here and I choose a folder that has my videos

and what happens is that Claude is basically

going to be working off that folder

so inside that folder I allow permissions

and then what I do is I drop in the source file

which is the input file which is the video I record the raw file

and then what I do is that I also drop in the transcript

if you don't drop in the transcript

then Claude would have to extract the transcript from the video

but because I don't want this to take like forever

I just provided a transcript as well

so once you provide the transcript

this is usually in the form of an s L

t file and then the input video

it goes ahead to like do everything

OK so in here

you can see that I've specifically said that

point the scale at a video

so that it acts as the auto director

so I've given it a number of things

I wanted to do OK I've given it a number of things I wanted to do

so I've said things like at the width of the video

make sure that like detects the format

so whether it's a long form video so or it's a short form video

and I have also talked about like if I don't provide a transcript

like I said then it should basically extract the transcripts

but then I'm not really doing that in this particular

I just want it to work really seamlessly

so I'm not really like ex

I'm not allowing it to extract the transcript

I'm just providing everything

and I've actually given it a number of things it has to do

I've talked about like how the look and feel should look like

I've talked about the fact that like

it should blur text in the background

because when I was doing this at first

like it will just put a text on the on the video like that

and sometimes there will be some clashes happening

so I just wanted it to blur the

the background of the text

so that it's a lot more visible and accessible that way

and all these things you need a bit of creativity like I mean

if you've been editing for a while

then you know some of the way these things happens

so it's just basically the steps I take when I'm editing

that I've just converted to a skill okay

so I have things like the transitions okay

I have things like the presets in here

and I have some form of like encoding

that I've also put in here as well

and there are a few python scripts in here as well

you can see that I have like my brand colours in here as well

so all these are things that you can actually define

so like you can actually define what your brand colours are like

you can put in your own brand colours in here as well

you can put in brand colours here as well

you can see that I have the fonts in here that I'm using as well

and I've defined the type of fonts I want to use

that it should be bold and um yeah

so I have like the intro outro text the colour

the sticker assets and I do have some assets files here okay

so the assets file basically contains the the font types I wanna use

they've all been like installed

I also have the reference files which is this like um

FFN

peg recipe that like basically gives like what a core idea should be

how it should overlay how it should be removing the caves

like all these things have actually been find in here

and then finally I also have like the scripts

so those scripts that you actually see like they in the skill

they actually get called in here as well

so all these have actually been embedded into the skill for me

but yeah that is really all I wanted to show you guys

I hope you enjoy this video

if you're interested in joining my community

I'm gonna leave the link in the comment section below

so that you can join as usual

if you're not subscribed to my channel

make sure you subscribe it's the subscribe button

like this video share it

it does it goes a long way to support my channel

and encourage me to keep doing these videos

so thank you if you've already been doing that

but yeah that is it for today's tutorial

I have a lot of tutorials on this channel

so you can check them out as well

I hope to see you in the next one
