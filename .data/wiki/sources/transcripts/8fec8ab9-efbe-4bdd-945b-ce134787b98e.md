---
source_id: "8fec8ab9-efbe-4bdd-945b-ce134787b98e"
title: "I Built a Second Brain That Organises Itself (and you can too!)"
notebook_id: 06717c64-8597-4a59-a5e3-871e841585af
url: null
type: youtube
exported: 2026-07-27
---

# I Built a Second Brain That Organises Itself (and you can too!)
Welcome to this walkthrough guide on how 
to build an AI-powered Obsidian Vault.

If you are anything like me, you know this cycle.

You watch a great productivity video 
on YouTube, you get super motivated,  

and then you move your entire life 
into a brand new note-taking app.

You spend about 3 days building out the perfect  

dashboard in Notion or a brand new 
colour coded system in OneNote.

And it works great... for about 2 weeks or so.

But then the novelty starts to 
wear off. Life gets busy. You  

stop tagging your notes. You stop 
filing things in the right folders.

Basically the friction of maintaining the system 
just simply becomes too much work – especially if,  

like me, you have an ADHD brain 
that hates doing admin work.

And so the system sits there and it starts to rot.

And eventually, you basically 
just declare mental bankruptcy.

You abandon the ship, leaving behind a digital 
graveyard of unfinished ideas, looking for the  

next shiny new app, hoping that this one 
is finally going to be the one that works.

I know this pattern because I 
was stuck in that loop for years.

Until eventually I realised 
I didn't need a better a pp.

What I needed was a better system that 
bridges the gap in my own executive function.

I needed essentially a second brain 
that does the heavy lifting for me.

So I built an environment that works for me.

I've been using it successfully for a while now  

and a few of my colleagues 
have even adopted it too.

So I hear what you might be asking. Why Obsidian? 
Why not just use Notion or Evernote or OneNote?

Well honestly, the answer is 
surprisingly simple. And it's Markdown.

Now, if you haven't used it before,  

Markdown is essentially the universal 
standard for formatting plain text.

Instead of clicking a bold button,  

which you can still do, but you could 
just put two asterisks around a word.

Instead of a complex proprietary 
file format that locks you in,  

your notes are saved as simple text files.

This makes them universally compatible, 
future proof and incredibly lightweight.

Think about it. Some Microsoft Word documents from 
the 90s can be surprisingly hard to open today.

But a plain text file from 50 
years ago is still readable.

That is the level of longevity 
that we want for our second brain.

I've dropped the link in the description if you 
want to geek out on exactly how Markdown works.

But the key takeaway is this:

Because it is a universal standard, 
you own your data forever.

And more importantly for this particular 
setup, it's also the native language of AI.

Whether you use Gemini, Claude or ChatGPT, 
they all speak Markdown language perfectly.

This allows us to build a seamless bridge between  

your messy thoughts and the 
AI's structured processing.

So with all of that out of the way, 
let's get this whole thing built.

Step 1 is to grab the zip file 
from the link in the description.

Once it's in your downloads, 
go ahead and unzip it.

You'll see a folder called template files.

Now this isn't just a folder, this 
is going to be your new brain.

It contains all the folders, templates 
and settings pre-built for you.

But be sure to pause here, you want to rename  

this folder to whatever you 
want your vault to be called.

I'm calling mine Alex Gemini Vault, 
because today I'm role playing as Alex,  

a freelance web developer and photographer.

I want to show you that this system isn't just 
perfect for me, it actually adapts to who you are.

Now we open up Obsidian.

You'll see a big purple button 
that says create a new vault.

Just ignore that.

Instead you want to click 
on open folder as a vault.

Navigate to the folder that we just 
renamed, select it and hit open.

And we're in.

You can think of this as the chassis for our car.

It's the structure that kind 
of holds everything together.

But right now, it's just a parked car,  

it's not going anywhere because 
it doesn't even have an engine.

Inside the start here folder, 
you'll find a user guide.

If you prefer reading to watching, that 
file is going to be your best friend.

But for those that prefer to watch and 
follow along, let's go build the engine.

First we need to pop the hood, so 
go down to the bottom left corner  

and click on the gear icon to open your settings.

Now head down the list to the 
tab that says community plugins.

By default, Obsidian starts in what's known 
as restricted mode to keep things safe.

But we want to give our notes some AI 
superpowers, so we need to turn this off.

Go ahead and click turn on community plugins.

And with that, the store is now open for business.

Click browse to go and search the directory. 
There's literally thousands of plugins available.

In the search bar, type Gemini Scribe. This is the  

specific engine that we're 
installing in our car today.

Click install. It usually only takes 
a few seconds to download the files.

And there we go.

Once it's installed, don't 
forget the most crucial step.  

You have to click enable to 
actually turn the engine on.

Now that it's running, click 
options to configure it.

First, let's check out the your name section. 
This is where we tell our agent what to call us.

I will enter in Alex, since I 
am role playing as Alex today.

Next, look at the plugin state 
folder just below it. By default,  

this creates a generic folder that's going 
to clutter up your main root directory.

So let's hide the machinery. Change 
this path to Metadata > Gemini Scribe.

Next, turn on session history. 
This is a game changer.

It essentially gives you a save game feature.

It saves your AI chats as 
actual files in your vault.

Now this isn't just about being able 
to resume a chat, which you can.

What it means though is that your own AI 
interactions become part of your knowledge base.

You can search them, link 
to them and even ask the AI  

to reflect on past conversations to 
find patterns in your own thinking.

That's a seriously powerful feedback loop.

Now we have the chassis and we have the 
engine, but an engine won't run without fuel.

That fuel is your API key. So open your 
browser and head to aistudio.google.com.

Look for the button in the bottom 
left corner that says get API key.

Click on that and then click the 
option that says create API key.

Now you might need to select a project first. If 
you don't have one, just click create new project.

It only takes a second.

Once it's created, you'll 
notice something important.

The API key itself does not show 
up in the user interface here.

You cannot actually read the text of the key 
here and that is intentional for security.

You just need to look for the copy button 
and click that to grab it to your clipboard.

And while we're here, a serious note on security.

You will notice that I'm going to be 
aggressively blurring my key out in this video.

I cannot stress this enough. Do 
not share this key with anyone.

This key is essentially like 
your credit card in text form.

And here's why. While Google offers a generous 
free tier, this is real cloud computing power.

If someone else gets your key 
and starts running scripts,  

they are using your quota and 
potentially running up your bill.

So if you ever think you accidentally leaked it,  

be sure to come back to this 
dashboard and delete it immediately.

You can always create a new one if you need.

Now back in Obsidian, let's paste 
that key into the API key box.

And finally, let's check out the model options.

If you're on the free tier, I highly 
recommend selecting a flash or flash  

lite model to avoid hitting any daily limits.

Save the pro models for when 
you need heavy reasoning.

Now, a quick side note for the 
power users and developers watching.

Everything we're doing here 
with the Gemini Scribe plugin  

can also be done using Gemini 
CLI or command line interface.

There's another community 
plugin that's called Terminal,  

which can be installed to give you a 
command line right here inside Obsidian.

The main advantage of using 
this method is authentication.

So instead of pasting an API key, you can 
simply just sign in with your Google account.

If you live in the terminal, the CLI is likely 
a cleaner and slightly more powerful workflow.

And it's also worth noting that while this 
whole setup is currently built around Gemini,  

the core principle applies to 
other language models as well.

Because we are using Markdown, 
you're not locked in.

If you have a Claude Code or 
OpenAI Codex subscription,  

you could simply use a different plugin like 
Smart Composer to achieve a very similar result.

The key here is leveraging whichever AI tool  

works best for you and your existing 
subscriptions should you have any.

But for this video, we're going 
to be sticking with Gemini Scribe.

Now that the engine is installed, 
let's tighten the bolts on the chassis.

Look at the left sidebar menu in your settings.

You'll see a section for core plugins.

Go ahead and click on Daily Notes.

First up is the date format. I 
strictly use year, month, day.

There is a very specific reason for this.

Computers sort files alphabetically.

By using this ISO format, alphabetical order 
becomes exactly the same as chronological order.

Your notes will always line up 
perfectly from oldest to newest  

without you ever having to organize them manually.

Next, take a look at the new file location.

Change this to Inbox > Daily Notes.

We want them all in one bucket.

And then the template file location.

Browse and select Metadata 
> Templates > Daily Note.

This step is pretty critical.

The AI commands that we're 
going to be using later on,  

like the morning plan, are programmed to 
look for specific headers in this file.

If you don't use this template,  

the AI won't know where to write and 
the commands basically won't work.

Now one last stop while we're here. 
Click on Files and Links in the sidebar.

Look for the default location for new notes.

Change this to In the folder 
specified below and select Inbox.

This supports that whole philosophy 
of Capture Now, Organize Later.

And then finally, look for Default 
Location for new attachments.

Change this also to In the folder specified 
below, but then set the path to Attachments.

This forces all of your images 
into their own dedicated closet,  

keeping your actual notes nice and clean.

Now, before we wake up the AI, a quick 
word on freedom and synchronization.

Because Obsidian stores these files right 
on your computer, you own your data.

But that also means that it doesn't magically 
appear on your phone unless you tell it to.

You have two main options here and 
honestly you're free to choose either.

Option 1 is Obsidian Sync. This 
is the official paid service.

It's the easiest way to sync between 
iPhone, Android, Mac and Windows.

Basically, it just works.

Option 2 on the other hand is 
the potentially free route.

Because these are just text files,  

you can just move this entire Vault folder 
into your Google Drive or iCloud Drive.

But one word of warning here. Do 
not use both at the same time.

Please don't put your Vault in 
iCloud and turn on Obsidian Sync.

That is just a recipe for data corruption.

Essentially, pick a lane and stick to it.

Now here is also the ultimate 
proof that you aren't locked in.

Go to any note, right click on the 
title and select 'Reveal in System  

Explorer' or finder if you're on a Mac like I am.

This opens the actual folder on your hard drive.

There is your file. You can open it in VS Code,  

Notepad, email it or move it 
to a different app entirely.

You are never trapped in this system.

Ok, now the car is built, the engine 
is installed and it's fueled up.

Now we basically need to teach it how to drive.

So navigate back to the Start Here folder 
and open the file named 'Setup Wizard'.

Now please note, we're not actually 
going to edit this file ourselves.

You can think of this document 
as the driver's manual.

It contains the prompt engineering that converts  

Gemini from a generic chatbot into 
a specialised system administrator.

To run it, take a look at the ribbon 
menu on the far left hand side.

You will see a small sparkle icon. Click that.

Now we need to tell the AI what to read.

So we simply type the @ symbol.

In this system, the @ symbol essentially 
acts like an attachment selector.

So choose the setup wizard file from the list.

This loads those instructions 
into the AI's memory.

And then simply type 'I am ready to 
start the interview' and hit enter.

The AI is now processing.

It's adopting the persona of a 
consultant and preparing to interview us.

Here is question 1. It asks about my profession.

I'm going to answer as Alex, our web developer.

Now why is this important?

The system needs to know your work context 
to structure your project's folder.

If I tell it I'm a developer, it will 
probably create folders for code bases.

If I told it I was a chef, it would probably 
create folders for menu planning instead.

It tailors the taxonomy to you.

Question 2. It asks about hobbies.

I'll mention landscape photography.

The logic here is crucial.

The system here is using the PARA method.

It needs to know the difference between a project,  

which has a deadline, and an area, 
which is a standard to be maintained.

This prevents project burnout by ensuring that 
your hobbies aren't treated like urgent tasks.

If you ignore a project, it fails.

If you ignore an area, it just degrades slowly.

The AI understands this distinction.

Question 3. The migration check.

It asks if you have any existing notes to import.

If you're an existing Obsidian 
user, this is your moment.

You can now drag and drop your entire old 
Obsidian vault into the inbox folder right now.

The AI would then scan every single file and  

propose a plan to file them 
into your new structure.

But for today, I'm just going 
to say no and start fresh.

Question 4. Daily notes.

I tell it that I'd like them 
to archive them monthly.

This setting tells the AI to act as 
a janitor, automatically sweeping my  

old daily notes into archive folders 
so that my workspace stays pristine.

And then finally, tone and dialect.

I'm specifying Australian English.

This is the secret sauce for the de-aiify command.

It ensures that the output sounds human 
and local, not like a generic robot.

Ah, now stop and look at this popup.

The AI is asking for permission to create folders.

Tick this box that says "Don't ask 
again for this session" and click allow.

This is what we call a session trust token.

It basically grants permission only until 
you close the app or start a new chat.

It's the perfect balance between 
convenience and security.

If you wish to have more 
control over your systems,  

you can choose allow or decline on 
each individual request from the AI.

And then finally, we have the memory commit.

You'll notice that the AI has 
created a file called agents updated.

You can think of this agent file as 
essentially the brains of the outfit.

By forcing the AI to write changes to a 
staging file first though, and asking you  

to copy and paste them into the main agent's 
file, we still keep a human in the loop.

You want to think of the AI 
here as a junior employee.

They can draft the contract, but you are the boss.

You have to sign it before it becomes official.

You are always in control of 
the files that run your life.

Now, let's take a look at what it built.

It used the PARA method.

Projects, areas, resources and archive.

You can see here inside projects 
and areas, it has automatically  

created a collection of folders based on the 
suggestions it made during the interview.

Now, I personally use the PARA method because 
it organizes information by actionability.

Is this a project with a deadline or 
is it just a resource for reference?

That distinction helps keep my brain clear.

Projects are essentially your workbench.

This is where the bulk of your 
time will likely be spent.

Resources are your library.

You go there to look things 
up, but you don't live there.

And the archive is essentially your cold storage.

It keeps the system fast by hiding everything 
that you aren't working on right now.

But you might hate folders.

You might prefer the Zettelkasten method 
of linking or the Johnny Decimal system.

That is completely fine.

Because this is AI driven, you can 
literally just start a chat and say,

"Hey, I prefer the Zettelkasten method. Please  

propose a new folder structure 
and help me move my files."

The AI will then help you 
refactor the entire vault.

The structure of your notes should always 
serve you, not the other way around.

Alright, let's now see the magic in action.

I've just found a great cheat sheet for CSS.

I don't have time to file it.

So instead, I just simply create a new note, 
paste it in, name it CSS and be done with it.

Capture now, organize later.

And a pro tip, when you want to find that note 
later, don't go digging through all the folders.

Simply hit Cmd+O (or Ctrl+O on Windows).

This brings up the fuzzy finder.

I just type in CSS and hit 
enter and I'm there instantly.

Now, let's tidy up.

I open up the chat and ask it 
to run the inbox processor.

Watch what happens.

The AI reads the content, figures out 
it's about CSS Grid, gives it a proper  

title, applies the relevant tags and 
physically moves it to the right folder.

If I'm ever curious where the AI put it,  

I can just right click the file tab 
and choose Reveal in Navigation.

It jumps straight to the folder 
location in the left hand sidebar.

Now, fast forward to 5pm.

We run our daily review command.

This command runs in 3 distinct phases.

Phase 1 is the input.

The AI asks for final thoughts.

I give it a brain dump, meetings, 
unfinished tasks, random ideas.

Phase 2 is the triage.

While it processes my notes, it scans the inbox.

If I left anything messy in there today, it 
would tag it and file it for me automatically.

And Phase 3 is the migration.

This is the magic.

It generates a natural 
language summary for my day.

And if there's any tasks that I didn't complete,  

it'll likely create tomorrow's daily 
note for me now and copy the tasks there.

It helps me close the loop.

I can basically close my computer knowing 
exactly what I need to do when I wake up,  

without carrying that mental 
load with me all evening.

Now, so far we've looked at the standard commands.

But the real power is that you 
aren't locked into my workflow.

You can build your own 
tools using this foundation.

To make this easy, I've included a special agent 
command called, funnily enough, Create Command.

Think of this as a software developer 
that lives inside your chat window.

Let's say you're a content creator.

You might find yourself constantly rewriting 
your technical notes into social media posts.

You could build a command 
called, Content Repurposer.

You would simply tell the agent, 
I want a command that takes my  

technical notes and rewrites 
them for LinkedIn and Threads.

The AI will then interview you 
and then design the tool for you.

Once it generates the code, it follows 
the same safety protocols as before.

It creates a new agents updated file.

You simply copy that new recipe, paste it into  

your main agents file and suddenly you 
have a brand new tool in your arsenal.

The only limit is your imagination.

And then as a final step of cleanup, if the  

automation process hasn't automatically 
removed the Start Here folder for you,

you can simply delete that folder as 
well as the original Gemini Scribe  

folder that was created by the plugin originally.

And with that, you're basically done.

Now, I've shown you the mechanics. 
The chassis, the engine, the fuel.

But how does this actually look in practice?

Let me walk you through my personal daily routine  

to show you how I use this 
system to help me run my life.

In the morning, I start every single 
day by running the morning plan command.

I grab my coffee, I open up a new chat 
and I just do a complete brain dump.

I usually do this via voice to text because it's  

far easier for me to just throw 
my ideas at a wall via voice.

The AI then takes all of that chaos, figures it 
all out and structures it into a clear agenda.

And crucially, it automatically links to any 
of my existing notes for my active projects.

It basically sets the stage for me to help 
me continue my work throughout the day.

And then as I'm jumping 
between calls or deep work,  

I just dump things in the inbox. 
I don't stop to file any of it.

And if I need to send a quick update or rewrite a 
drafted note so that it doesn't sound so robotic,

I'll use ad-hoc commands 
like the de-aiify command.

This one is one that honestly 
I use pretty constantly.

It takes generic robotic text and rewrites it to 
sound human using my specific tone and my dialect.

It's great for when you know what you want to 
say, but you can't really get the words out right.

And then in the evening, this is the 
non-negotiable. I run the daily review.

I decompress. I throw all my final thoughts 
into the chat and let the AI summarise my wins.

It checks off any tasks that I've completed 
based on the notes that I gave it,  

and it moves any unfinished tasks to tomorrow.

It clears my mental RAM so that I can switch off 
without worrying that I've forgotten something.

And that's honestly just the tip 
of the iceberg for my workflow.

The beauty of this system is that yours 
is most likely going to be different.

But you can use this system 
and make it bend to fit you,  

instead of you having to try and 
fit the structure of my tool.

And there you have it. A second 
brain that actually thinks with you.

We built the chassis, we installed the engine and  

we filled it with fuel. Now 
it's ready for you to drive.

The link to the template, as I mentioned,  

is in the description. Download it, 
run the wizard and make it your own.

And one last thing, I want 
to know how you use this.

Did you stick with the PARA structure? Or  

did you build some crazy custom 
command? I want to know about it.

Let me know in the comments below. I do read  

all of them and I'm always looking 
for ways to improve these systems.

Happy note taking, and I'll 
catch you in my next video.

Thanks for watching. If you'd like 
to see more content like this,  

be sure to check out the channel.

And if you like what you see, don't 
forget to hit that subscribe button.
