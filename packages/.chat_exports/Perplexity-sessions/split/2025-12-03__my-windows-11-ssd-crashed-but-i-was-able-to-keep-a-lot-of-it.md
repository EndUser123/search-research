---
title: "my windows 11 ssd crashed, but I was able to keep a lot of it on the drive.  My notepad kept a bunch of tabs open which "
date: "2025-12-03"
mode: "COPILOT"
uuid: "a8577242-115d-4a49-938f-ba82abf90bd8"
entry_count: 1
---

## Human

my windows 11 ssd crashed, but I was able to keep a lot of it on the drive.  My notepad kept a bunch of tabs open which was really handy, but now on my new pc, I'd like to find all those open tabs.  how do I do that?

## Assistant

Windows 11 Notepad stores your open tabs and session data in a specific folder on your drive, so you should be able to recover them from your old SSD.[1][2][3]

## Location of Notepad Session Data

Your Notepad tabs are stored at: `C:\Users\[YourUsername]\AppData\Local\Packages\Microsoft.WindowsNotepad_8wekyb3d8bbwe\LocalState\` [][]. This folder contains two important subfolders:
- **TabState**: Contains files for each tab that was open in Notepad [][]
- **WindowState**: Contains information about Notepad windows and which tab was focused []

## How to Recover Your Tabs

First, enable viewing hidden files on your old drive since the AppData folder is hidden by default []. In Windows Explorer, click the three-dot menu beside the View button, select Options, go to the View tab, and enable "Show hidden files, folders, and drives" [].

Next, navigate to the folder path above on your old SSD and copy both the **TabState** and **WindowState** folders []. On your new PC, close Notepad completely, navigate to the same folder path (using your new username), delete the existing TabState and WindowState folders, and paste the folders from your old drive []. When you open Notepad again, your previous tabs should appear [].
