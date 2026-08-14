---
title: "on windows 11, where are the start menu icons found?"
date: "2025-12-02"
mode: "COPILOT"
uuid: "c9fed275-4dc2-4690-b005-e087096085b0"
entry_count: 1
---

## Human

on windows 11, where are the start menu icons found?

## Assistant

The Start Menu icons in Windows 11 are primarily found in two file system locations which contain the shortcuts that appear in the Start Menu:

- C:\ProgramData\Microsoft\Windows\Start Menu\Programs
- C:\Users\[UserName]\AppData\Roaming\Microsoft\Windows\Start Menu\Programs

These folders contain the program shortcuts displayed in the Start Menu's "All apps" list. The first location is for system-wide icons available to all users, while the second is user-specific for the currently logged-in user. Some users also note a similar folder under the Default user profile path which is used as a template for new accounts [][].

In addition, many default Windows icons themselves (such as folder icons or peripherals) are embedded in system DLL files like imageres.dll and shell32.dll in the System32 directory rather than as standalone icon files []. The Start button itself is typically a PNG image file rather than an ICO file.

So, the Start Menu icons you see in Windows 11 come from shortcuts stored in the above file paths, with most icons inside shortcuts coming from system DLL files. You can navigate to these locations with File Explorer to view or organize the Start Menu items physically.
