---
source_id: "f08c7cf8-d1a8-45de-b5bb-d764dc777cbd"
title: "Dazbo's YouTube and Video Demos - Colab"
notebook_id: 84f90a47-9448-4652-82e1-c8dec495fc68
url: https://colab.research.google.com/github/derailed-dash/youtube-and-video/blob/main/src/notebooks/youtube-demos.ipynb
type: web_page
exported: 2026-07-27
---

# Dazbo's YouTube and Video Demos - Colab
youtube-demos.ipynb - Colab

close

close

Skip to main content

https://colab.research.google.com/github/derailed-dash/youtube-and-video/blob/main/src/notebooks/youtube-demos.ipynb#notebook-main

info

This notebook is open with private outputs. Outputs will not be saved. You can disable this in 

Notebook settings

https://colab.research.google.com/github/derailed-dash/youtube-and-video/blob/main/src/notebooks/youtube-demos.ipynb

Open notebook settings

.

close

info

Your Colab version is out of date, please refresh to get the latest updates.

Refresh to update 

https://drive.google.com/drive/search?q=owner%3Ame%20(type%3Aapplication%2Fvnd.google.colaboratory%20%7C%7C%20type%3Aapplication%2Fvnd.google.colab)&authuser=0

 

youtube-demos.ipynb

youtube-demos.ipynb_

File

Edit

View

Insert

Runtime

Tools

Help

settings

Open settings

link Share

Share notebook

spark Gemini

Show Gemini

Sign in

https://accounts.google.com/ServiceLogin?passive=true&continue=https%3A%2F%2Fcolab.research.google.com%2Fgithub%2Fderailed-dash%2Fyoutube-and-video%2Fblob%2Fmain%2Fsrc%2Fnotebooks%2Fyoutube-demos.ipynb&ec=GAZAqQM

search Commands Show command palette Ctrl+Shift+P

Show command palette (Ctrl+Shift+P)

add Code Insert code cell below Ctrl+M B

Insert code cell below (Ctrl+M B)

add Text Add text cell

Add text cell

play_arrow Run all Run all cells in notebook

Run all cells in notebook

arrow_drop_down

More actions

Restart session

Restart session and run all

Run focused cell and all cells below

Interrupt execution

Clear all outputs

Copy to Drive

Connect Connect to a new runtime

Connect to a new runtime

arrow_drop_down

Additional connection options

link

Share notebook

settings

Open settings

expand_less

Toggle header visibility

format_list_bulleted

find_in_page

code

eye_tracking

vpn_key

folder

table

Notebook

more_vert

More tab actions

close

Close all tabs

spark Gemini

arrow_upward

Move cell up

Ctrl+M K

arrow_downward

Move cell down

Ctrl+M J

edit

Edit

delete

Delete cell

Ctrl+M D

more_vert

More cell actions

keyboard_arrow_down

Dazbo's YouTube and Video Demos

Overview

This notebook forms the first part of a walkthrough series.

The overall series covers:

Starting with an idea. Here, the goal is to work with vidoes, which could be on YouTube. We want to be able to download videos, extract audio, transcribe, translate, and potentially summarise the content.

Experimenting on this idea, using a Jupyter notebook, with Python.

Trying a few libraries and a couple of classical AI models.

Building a solution that makes use of Google Gemini multiomodal GenAI.

Turning the notebook into a web application, using Streamlit.

Packaging the application as a container.

Finally, hosting the application on Google Cloud's serverless Cloud Run service.

The code and notebooks are intended to be supplemented by these walkthroughs:

Downloading YouTube Videos, Extracting Audio, and Generating Transcripts with Python and Jupyter Notebooks

https://www.google.com/url?q=https%3A%2F%2Fmedium.com%2Fpython-in-plain-english%2Fdownloading-youtube-videos-extracting-audio-and-generating-transcripts-with-python-and-jupyter-c3068f82bbe0

YouTube Video Downloader with Generative AI: Run Anywhere, Transcribe and Translate

https://www.google.com/url?q=https%3A%2F%2Fpython.plainenglish.io%2Fyoutube-video-downloader-with-generative-ai-and-python-run-anywhere-transcribe-and-translate-dec2e593dd58

Building and Running an AI YouTube and Video Processing as a Python Streamlit Web Application, on Serverless Google Cloud Run

https://www.google.com/url?q=https%3A%2F%2Fmedium.com%2Fgoogle-cloud%2Frunning-ai-youtube-and-video-processing-as-a-python-streamlit-web-application-and-hosting-on-748aae8e54b4

Additionally, you will find supporting READMEs and scripts in my 

GitHub repo

https://github.com/derailed-dash/youtube-and-video

.

This Notebook

Examples of how to work with YouTube videos using Python. Here I'll demonstrate:

How to 

download videos and extract audio

https://colab.research.google.com/github/derailed-dash/youtube-and-video/blob/main/src/notebooks/youtube-demos.ipynb#downloading-videos-and-extracting-audio

How to 

transcribe audio to text using a speech-to-text API

https://colab.research.google.com/github/derailed-dash/youtube-and-video/blob/main/src/notebooks/youtube-demos.ipynb#extracting-audio-using-python-speech-recognition

How to 

extract existing transcripts and translate

https://colab.research.google.com/github/derailed-dash/youtube-and-video/blob/main/src/notebooks/youtube-demos.ipynb#extract-existing-transcripts-from-videos

To run this notebook, first execute the cells in the Setup section, as described below.

 Then you can experiment with any of the subsequent cells.

A few useful notes:

The source for this notebook source lives in my GitHub repo, 

Youtube-and-Video

https://github.com/derailed-dash/youtube-and-video

.

Check out further guidance - including tips on how to run the notebook, in the project's 

README.md

 .

For example, you could...

Run the notebook locally, in your own Jupyter environment.

Run the notebook in a cloud-based Jupyter environment, with no setup required on your part! For example, with 

Google Colab

: 

 It looks like this:

For more ways to run Jupyter Notebooks, check out 

my guide

https://www.google.com/url?q=https%3A%2F%2Fmedium.com%2Fpython-in-plain-english%2Ffive-ways-to-run-jupyter-labs-and-notebooks-23209f71e5c0

.

subdirectory_arrow_right 38 cells hidden

spark Gemini

keyboard_arrow_down

Setup

subdirectory_arrow_right 16 cells hidden

spark Gemini

keyboard_arrow_down

Packages

First, let's install any dependent packages:

subdirectory_arrow_right 3 cells hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

%pip install --upgrade --no-cache-dir python-dotenv dazbo-commons pytubefix moviepy yt_dlp
Start coding or generate with AI.


spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

import IPython
from IPython.display import display
from IPython.core.display import Markdown
import logging
import re
import io
import sys
from pathlib import Path
from dataclasses import dataclass
import dazbo_commons as dc
from dotenv import load_dotenv
Start coding or generate with AI.


spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

# Colab requires an older version of Ipykernel
if not "google.colab" in sys.modules:
    pass
    %pip install --upgrade --no-cache-dir ipykernel
    
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Logging

Now we'll setup logging. Here I'm using coloured logging from my 

dazbo-commons

https://www.google.com/url?q=https%3A%2F%2Fpypi.org%2Fproject%2Fdazbo-commons%2F

 package. Feel free to change the logging level.

subdirectory_arrow_right 1 cell hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

# Setup logging
APP_NAME="dazbo-yt-demos"
logger = dc.retrieve_console_logger(APP_NAME)
logger.setLevel(logging.DEBUG)
logger.info("Logger initialised.")
logger.debug("DEBUG level logging enabled.")
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

File Locations

Here we initialise some file path locations, e.g. an output folder.

subdirectory_arrow_right 1 cell hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

locations = dc.get_locations(APP_NAME)
for attribute, value in vars(locations).items():
    logger.debug(f"{attribute}: {value}")
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Utility Functions

subdirectory_arrow_right 1 cell hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

def clean_filename(filename):
    """ Create a clean filename by removing unallowed characters. """
    pattern = r'[^a-zA-Z0-9._\s-]'
    return  re.sub(pattern, '_', filename)
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Install Additional Packages You May Need

Bear in mind that nodejs is required by the pytubefix library, to prevent this appliction being detected as a bot.

You can run the cell below, but it may not work on your environment. So you might need to install packages manually, e.g.

Package

Purpose

Install Command

ffmpeg

https://www.google.com/url?q=https%3A%2F%2Fffmpeg.org%2F

A useful utility for video and audio format conversion. Many Python libraries use it. It will not generally be used by this notebook, but if you run into errors requiring ffmpeg, you will want to run this section.

Linux: 

sudo apt install ffmpeg

 Windows: 

winget install ffmpeg

FLAC

https://www.google.com/url?q=https%3A%2F%2Fxiph.org%2Fflac%2Fdownload.html

The Python 

speech_recognition

 library uses the FLAC utility to convert audio files into a format that can be processed for speech recognition.

Linux: 

sudo apt install flac

 Windows: Download the latest

nodejs

The pytubefix library can automatically create YouTube PO tokens, but this relies on nodejs being installed.

Linux: 

sudo apt install nodejs

 Windows: 

winget install node.js

subdirectory_arrow_right 3 cells hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

import os
import platform
import subprocess
def run_command(command):
    """Run a shell command and print its output in real-time."""
    process = subprocess.Popen(
        command, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    # Read and print the output line by line
    if process.stdout is not None:
        for line in iter(process.stdout.readline, b''):
            logger.info(line.decode().strip())
        process.stdout.close()
        
    process.wait()
    
def install_software(appname: str):
    os_name = platform.system()
    logger.info(f"Installing {appname} on {os_name}...")
    
    # Mapping operating systems to their respective installation commands
    command_map = {
        "Windows": f"winget install {appname} --silent --no-upgrade",
        "Linux": f"apt -qq -y install {appname}",
        "Darwin": f"brew install {appname}"
    }
    command = command_map.get(os_name)
    if command:
        run_command(command)
        logger.info(f"Done.")
    else:
        logger.error(f"Unsupported operating system: {os_name}")
def check_installed(app_exec: str) -> bool:    
    appname, *arg = app_exec.split()
    arg = " ".join(arg)
    logger.debug(f"Checking if {appname} is installed")
    
    try:
        output = subprocess.check_output([appname, arg], stderr=subprocess.STDOUT)
        logger.debug(f"{appname} version: {output.decode().strip()}")
        logger.debug(f"{appname} is already installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug(f"{appname} is not installed or absent from path.")
        
    return False
apps = [ ("ffmpeg", "ffmpeg -version"),
         ("flac", "flac --version"),
         ("nodejs" , "node --version"),]
          
for app_install, app_exec in apps:
    if not check_installed(app_exec):
        install_software(app_install)
Start coding or generate with AI.


spark Gemini

Now we'll check 

ffmpeg

 has been installed.

On Windows, this may not have been added to your path. If so, you can check your default install location using 

winget --info

 , and then add it to your path.

subdirectory_arrow_right 0 cells hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

logger.info("Note that installed applications may not be immediately available after first installing.\n" \
            "It may be necessary to relaunch the notebook environment.")
!ffmpeg -version
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Videos to Work With

We start by defining a list of videos to test our application with, along with a function that takes a full YouTube URL and returns just the id portion.

I've used these videos because…

The first is the fantastic 

Burning Bridges

https://www.youtube.com/watch?v=udRAIF6MOm8

 by Sigrid. The video has no embedded transcript.

The second is the beautiful song 

I Believe

https://www.youtube.com/watch?v=CiTn4j7gVvY

 by Melissa Hollick. It's one of my favourite songs of all time. When I get a migraine, I turn off the lights, and listen to this to feel better! And for those who enjoy gaming, this song is the end titles to the amazing Wolfenstein: New Order game. This video has an embedded transcript.

Then we have a short 

Jim Carey speech

https://www.youtube.com/watch?v=nLgHNu2N3JU

, which gives us dialog without music or other ambient noise. It has an embedded transcript.

And finally, a 

Ukrainian song

https://www.youtube.com/watch?v=d4N82wPpdg8

 from Eurovision 2024, by Jerry Heil and Alyona Alyona. This gives us an opportunity to test translation. It also has an embedded transcript.

subdirectory_arrow_right 1 cell hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

# Videos to download
urls = [
    "https://www.youtube.com/watch?v=udRAIF6MOm8",  # Sigrid - Burning Bridges (English)
    "https://www.youtube.com/watch?v=CiTn4j7gVvY",  # Melissa Hollick - I Believe (English)
    "https://www.youtube.com/watch?v=nLgHNu2N3JU",  # Jim Carey - Motivational speech (English)
    "https://www.youtube.com/watch?v=d4N82wPpdg8",  # Jerry Heil & Alyona Alyona - Teresa & Maria (Ukrainian)
    "https://www.youtube.com/shorts/41iWg91yFv0",   # Rick Astley short
]
def get_video_id(url: str) -> str:
    """ Return the video ID, which is the part after 'v=' """
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Downloading Videos and Extracting Audio

Here I'll demonstrate a few different Python libraries for working with YouTube videos.

subdirectory_arrow_right 7 cells hidden

spark Gemini

keyboard_arrow_down

Option 1 - With PyTubeFix

Here I'll use the 

pytubefix

https://github.com/JuanBindez/pytubefix

 library to download YouTube videos, and then to download mp3 audio-only streams as files.

This library is a community-maintained fork of 

pytube

 . It was created to provide quick fixes for issues that the official pytube library faced, particularly when YouTube's updates break 

pytube

 .

Pros:

The library is very easy to use.

We can work with video, audio, channels, playlists, and even search and filter.

It is 

well documented

https://www.google.com/url?q=https%3A%2F%2Fpytubefix.readthedocs.io%2Fen%2Flatest%2F

.

It can be used from the command line, with its simple CLI.

It is VERY FAST!

Cons:

Does not offer some of the more sophisticated capabilities that are offered by 

yt_dlp

 .

It does not appear to set mp3 headers correctly. The mp3s are actually encoded as mp4a. I don't think this is a problem, but it's worth bearing in mind!

subdirectory_arrow_right 1 cell hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

from pytubefix import YouTube
from pytubefix.cli import on_progress
output_locn = f"{locations.output_dir}/pytubefix"
def process_yt_videos():
    for i, url in enumerate(urls):
        logger.info(f"Downloads progress: {i+1}/{len(urls)}")
        try:
            # YouTube now requires the PO token to be passed in the requet
            # The library will automatically generate a PO token, 
            # but nodejs must be installed to do so.
            yt = YouTube(url, on_progress_callback=on_progress, client="WEB")
            logger.info(f"Getting: {yt.title}")
            video_stream = yt.streams.get_highest_resolution()
            if not video_stream:
                raise Exception("Stream not available.")
            
            # YouTube resource titles may contain special characters which 
            # can't be used when saving the file. So we need to clean the filename.
            cleaned = clean_filename(yt.title)
            
            video_output = f"{output_locn}/{cleaned}.mp4"
            logger.info(f"Downloading video {cleaned}.mp4 ...")
            video_stream.download(output_path=output_locn, filename=f"{cleaned}.mp4")
        
            logger.info(f"Creating audio...")
            audio_stream = yt.streams.get_audio_only()
            audio_stream.download(output_path=output_locn, filename=f"{cleaned}.mp3")
            
            logger.info("Done")
            
        except Exception as e:        
            logger.error(f"Error processing URL '{url}'.")
            logger.error(f"The cause was: {e}") 
            
    logger.info(f"Downloads finished. See files in {output_locn}.")
    
process_yt_videos()
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Option 2 - PyTubeFix and MoviePy

Here I'm doing the same as before, but I'm extracting the audio using the Python 

MoviePy

https://github.com/Zulko/moviepy

 library. This is a powerful video and audio editing library.

Pros:

We can extract audio as mp3 with correct headers.

It is 

well documented

https://www.google.com/url?q=https%3A%2F%2Fzulko.github.io%2Fmoviepy%2F

.

It is powerful.

Cons:

It is slower to extract the audio than using 

pytubefix

 alone.

subdirectory_arrow_right 1 cell hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

from pytubefix import YouTube
from pytubefix.cli import on_progress
from moviepy import VideoFileClip
output_locn = f"{locations.output_dir}/pytubefix_with_moviepy"
def process_yt_videos():
    for i, url in enumerate(urls):
        logger.info(f"Downloads progress: {i+1}/{len(urls)}")
        try:
            yt = YouTube(url, on_progress_callback=on_progress, client="WEB")
            logger.info(f"Getting: {yt.title}")
            video_stream = yt.streams.get_highest_resolution()
            if not video_stream:
                raise Exception("Stream not available.")
            
            # YouTube resource titles may contain special characters which 
            # can't be used when saving the file. So we need to clean the filename.
            cleaned = clean_filename(yt.title)
            video_output = f"{output_locn}/{cleaned}.mp4"
            logger.info(f"Downloading video {cleaned}.mp4 ...")
            video_stream.download(output_path=output_locn, filename=f"{cleaned}.mp4")
        
            logger.info(f"Creating audio...")
            video_clip = VideoFileClip(video_output) # purely to give us access to methods
            assert video_clip.audio is not None
            video_clip.audio.write_audiofile(f"{output_locn}/{cleaned}.mp3")
            video_clip.close()
            
            logger.info("Done")
            
        except Exception as e:        
            logger.error(f"Error processing URL '{url}'.")
            logger.debug(f"The cause was: {e}") 
            
    logger.info(f"Downloads finished. See files in {output_locn}.")
    
process_yt_videos()
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Option 3 - With YT_DLP

I wanted to try the other popular YouTube package: 

yt-dlp

https://www.google.com/url?q=https%3A%2F%2Fpypi.org%2Fproject%2Fyt-dlp%2F

. The 

repo

https://github.com/yt-dlp/yt-dlp

 is a fork of the now unmaintained 

youtube-dl

 .

Pros:

It is very powerful, with far more options and features than 

pytubefix

 .

It can be installed as a standalone command-line executable, or as a pip-installable Python package.

Sets mp3 headers properly!

It has some powerful and network proxy settings. This can be useful if, for example, you are trying to download videos that are geo-restricted.

Cons:

It is more complicated to use.

The documentation is complex and somewhat hard to understand. And there's no real Python-specific documentation.

It depends on having ffmpeg installed for some use cases.

It is significantly slower that 

pytubefix

 for performing video download and audio extraction.

subdirectory_arrow_right 1 cell hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

import yt_dlp
output_locn = f"{locations.output_dir}/yt_dlp"
def process_yt_videos():
    for i, url in enumerate(urls):
        logger.info(f"Downloads progress: {i+1}/{len(urls)}")
        try:
            # Options for downloading the video
            video_opts = {
                'format': 'best',  # Download the best quality video
                'outtmpl': f'{output_locn}/%(title)s.%(ext)s',  # Save video in output directory
            }
            
            # Download the video
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                logger.info("Downloading video...")
                ydl.download([url])
            
            # Options for extracting audio and saving as MP3
            audio_opts = {
                'format': 'bestaudio',  # Download the best quality audio
                'outtmpl': f'{output_locn}/%(title)s.%(ext)s',  # Save audio in output directory
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            }
            
            # Download and extract audio
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                logger.info("Extracting and saving audio as MP3...")
                ydl.download([url])
            
        except Exception as e:        
            logger.error(f"Error processing URL '{url}'.")
            logger.debug(f"The cause was: {e}") 
            
    logger.info(f"Downloads finished. Check out files at {output_locn}.")
    
process_yt_videos()
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Conclusion

If you:

Want to just download the videos and/or audio in the simplest and fastest way possible, then go with 

Option 1

https://colab.research.google.com/github/derailed-dash/youtube-and-video/blob/main/src/notebooks/youtube-demos.ipynb#option-1---with-pytubefix

.

Want to download the videos and/or audio and then carry out some sort of manipulation or conversion of the media, go with 

Option 2

https://colab.research.google.com/github/derailed-dash/youtube-and-video/blob/main/src/notebooks/youtube-demos.ipynb#option-2---pytubefix-and-moviepy

.

If you want out-of-the-box proxy configuration, e.g. to bypass geo-restrictions, then go with 

Option 3

https://colab.research.google.com/github/derailed-dash/youtube-and-video/blob/main/src/notebooks/youtube-demos.ipynb#option-3---with-yt_dlp

.

subdirectory_arrow_right 0 cells hidden

spark Gemini

keyboard_arrow_down

Transcribing Audio to Text

subdirectory_arrow_right 7 cells hidden

spark Gemini

keyboard_arrow_down

Extracting Audio Using Python Speech Recognition

The Python 

speech_recognition

 package has a number of built in 

Recognizer

 implementations. Here I'm using the 

Google Web Speech API

https://www.google.com/url?q=https%3A%2F%2Fwicg.github.io%2Fspeech-api%2F

 

Recognizer

 , which has its default API key hard coded into the Python 

speech_recognition

 library. It is free, but has some limitations. For example, it only allows a max of 60s segments.

subdirectory_arrow_right 3 cells hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

%pip install --upgrade --no-cache-dir pydub SpeechRecognition ffmpeg-python
Start coding or generate with AI.


spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

import speech_recognition as sr
from pydub import AudioSegment
import ffmpeg
Start coding or generate with AI.


spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

def divide_chunks(sound, segment_size_secs=60):
    """ Split audio file into 60s chunks """
    
    segment_size_ms = segment_size_secs*1000
    for start_idx in range(0, len(sound), segment_size_ms):
        # Yield a chunk of audio data from start_idx to start_idx + segment_size_ms
        yield sound[start_idx:start_idx + segment_size_ms]
def transcribe_audio():
    """ Use Speech Recognition API with Google Web Speech API
    to convert audio dialog to text """
    recogniser = sr.Recognizer()        
    for mp3_file in Path(output_locn).glob(f'*.mp3'):
        transcribe_audio_file(recogniser, mp3_file)
def transcribe_audio_file(recogniser, mp3_file, language="en-US"):
    logger.info(f"Converting {mp3_file}...")
    try:
        audio = AudioSegment.from_file(mp3_file)
        # If AudioSegment is not working - e.g. due to broken mp3 headers - we
        # can use ffmpeg as a workaround. However, it's a lot slower.
        # ffmpeg.input(mp3_file).output(wav_file).run() # Convert with ffmpeg
        # logger.info(f"Successfully converted {mp3_file} to {wav_file}.")
        # audio = AudioSegment.from_wav(wav_file) # Read the audio
        segments = list(divide_chunks(audio, segment_size_secs=60)) # split the wav into 60s segments     
        transcription_extracts = {}
        for index, chunk in enumerate(segments):
            with io.BytesIO() as wav_io:
                chunk.export(wav_io, format='wav')
                wav_io.seek(0)  # Move to the start of the BytesIO object before reading from it
                        
                with sr.AudioFile(wav_io) as source:
                    audio_data = recogniser.record(source)
                try:
                    extracted = recogniser.recognize_google(audio_data, language=language)
                    logger.debug(f"Chunk {index} extracted.")
                    transcription_extracts[index] = extracted
                except sr.UnknownValueError:
                        # Log the unknown value error and continue
                    logger.warning(f"Chunk {index}: Could not understand the audio. Maybe it was empty.")
            
        logger.info("Extract:")
        for idx, extract in transcription_extracts.items():
            logger.info(f"{idx}: {extract}")
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg failed to convert {mp3_file}: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error.", exc_info=True)
            
transcribe_audio()
logger.info("Done")
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Results

It's a bit flakey! Sometimes it runs, but sometimes the API returns errors and fails to run.

When the API does run...

It fails to transcribe the Ukrainian song. Not too surprising, since this API does not detect language automatically, and defaults to recognising English.

It does an amazing job with the Jim Carey speech.

It is partially successful when transcribing songs.

Conclusions

It's not great! It's pretty good if there's no background sound or ambient noise. But it's pretty poor when working with songs. And it seems unreliable.

Transcribing Ukrainian

Let's try and transcribe from the Ukrainian song:

subdirectory_arrow_right 1 cell hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

def transcribe_ua():
    recogniser = sr.Recognizer()
    for mp3_file in Path(output_locn).glob(f'alyona*.mp3'):
        transcribe_audio_file(recogniser, mp3_file, language="uk-UA")
        
transcribe_ua()
Start coding or generate with AI.


spark Gemini

keyboard_arrow_down

Results

Partial success. But overall... Not great!

subdirectory_arrow_right 0 cells hidden

spark Gemini

keyboard_arrow_down

Extract Existing Transcripts from Videos

Now I'm going to use the 

youtube-transcript-api

https://github.com/jdepoix/youtube-transcript-api

 to extract existing transcripts from YouTube videos. Not only will it return the transcript, but it can also be used to translate those to translate those transcripts into other languages. So now I can download my Ukrainian song, and see both the Ukrainian transcript and the English translation. This is pretty awesome!

However, some videos do not contain transcripts.

subdirectory_arrow_right 2 cells hidden

spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

%pip install --upgrade --no-cache-dir youtube_transcript_api
Start coding or generate with AI.


spark Gemini

Run cell (Ctrl+Enter)

cell has not been executed in this session

[ ]

import youtube_transcript_api as yt_api
from pytubefix import YouTube
from pytubefix.cli import on_progress
def get_transcripts():
    """ Extract existing transcript data from videos """
    for url in urls:
        try: # Just so we can get the video title
            yt = YouTube(url, on_progress_callback=on_progress, client="WEB")
        except Exception as e:        
            logger.error(f"Error processing URL '{url}'.")
            logger.error(f"The cause was: {e}") 
            continue
        
        logger.info(f"Processing '{yt.title}'...")
        video_id = get_video_id(url)
        
        try:
            # By default, we get a list of 1: only get the preferred language transcript
            transcript_list = yt_api.YouTubeTranscriptApi.list_transcripts(video_id)
        except Exception as e:
            logger.error(f"Unable to extract transcript for '{yt.title}'.")
            logger.error(e)
            continue
        
        # iterate over all available transcripts
        for transcript in transcript_list:
            # The Transcript object provides metadata properties. Here are some...
            properties = {
                "video_id": transcript.video_id,
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,  # Whether it has been manually created or generated by YouTube
                "is_translatable": transcript.is_translatable,  # Whether this transcript can be translated or not
                "translation_languages": transcript.translation_languages,
            }
            
            for prop, value in properties.items():
                logger.info(f"{prop}: {value}")
            # Fetch the actual transcript data
            transcript_data = transcript.fetch() # returns a list of dicts
            logger.info(f"Raw transcript:\n{transcript_data}") 
            
            processed_transcript = process_transcript(transcript_data)
            logger.info(f"Processed transcript:\n{processed_transcript}")
            
            # Translate to en if we can
            if (transcript.language_code != "en" and 
                    transcript.is_translatable and 
                    any(lang['language_code'] == 'en' for lang in transcript.translation_languages)):
                transcript_data = transcript.translate('en').fetch() # translate to en
                processed_transcript = process_transcript(transcript_data)
                logger.info(f"Processed translated transcript:\n{processed_transcript}")
def process_transcript(transcript_data):
    """ Get all entries that are of type 'text' and NOT starting with [ """
    return "\n".join([entry['text'] for entry in transcript_data 
                                     if entry['text'][0] != "["])
                
get_transcripts()
Start coding or generate with AI.


spark Gemini

How cool is this!?

keyboard_arrow_down

What's Next?

In the next notebook, we'll look at adding Google Smarts, with some Google AI.

subdirectory_arrow_right 1 cell hidden

spark Gemini

Double-click (or enter) to edit

subdirectory_arrow_right 0 cells hidden

Colab paid products

https://colab.research.google.com/signup?utm_source=footer&utm_medium=link&utm_campaign=footer_links

 - 

Cancel contracts here

https://colab.research.google.com/cancel-subscription

more_vert

More tab actions

close

Close all tabs

more_vert

More tab actions

close

Close all tabs

more_vert

More tab actions

close

Close all tabs

data_object Variables

terminal Terminal

View on GitHub

New notebook in Drive

Open notebook

Upload notebook

Rename

Save a copy in Drive

Save a copy as a GitHub Gist

Save

Revision history

Notebook info

Download ►

Print

Download .ipynb

Download .py

Undo

Redo

Select all cells

Cut cell or selection

Copy cell or selection

Paste

Delete selected cells

Find and replace

Find next

Find previous

Notebook settings

Clear all outputs

check

Table of contents

Executed code history

Start slideshow

Start slideshow from beginning

Comments ►

Collapse sections

Expand sections

Save collapsed section layout

Show/hide code

Show/hide output

Focus next tab

Focus previous tab

Move tab to next pane

Move tab to previous pane

Hide comments

Minimize comments

Expand comments

Code cell

Text cell

Section header cell

Scratch code cell

Code snippets

Add a form field

Run all

Run before

Run the focused cell

Run selection

Run cell and below

Interrupt execution

Restart session

Restart session and run all

Disconnect and delete runtime

Change runtime type

Manage sessions

View resources

View runtime logs

Deploy to Google Cloud Run

Command palette

Settings

Keyboard shortcuts

Diff notebooks (opens in a new tab)

Frequently asked questions

View release notes

Search code snippets

Report a bug

Send feedback

View terms of service
