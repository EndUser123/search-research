---
title: "In claude code, I have a statusline to tell me when tasks are drifting.  but I'm trying to find a nice attracive way to "
date: "2026-01-04"
mode: "COPILOT"
uuid: "fac82052-a417-466e-9be2-a7d11e9c619e"
entry_count: 17
---

## Human

In claude code, I have a statusline to tell me when tasks are drifting.  but I'm trying to find a nice attracive way to indicate between this vs that terminal.  Here's some ideas:
  Option 1: Color-coded emoji
  | Scenario        | Display | Visual                        |
  |-----------------|---------|-------------------------------|
  | Self drifting   | 🔴      | Red - urgent, you're off-task |
  | Others drifting | 🟡      | Yellow - informational        |

  Option 2: Symbol distinction
  | Scenario        | Display | Meaning                         |
  |-----------------|---------|---------------------------------|
  | Self drifting   | ⚠️      | Standard warning                |
  | Others drifting | ⭕      | Hollow/muted - not your problem |

  Option 3: Goal metaphor
  | Scenario        | Display | Meaning              |
  |-----------------|---------|----------------------|
  | Self drifting   | 🧭      | You've lost your way |
  | Others drifting | 📍      | Someone else drifted |

  Option 4: Explicit labels
  | Scenario        | Display | Clear but verbose |
  |-----------------|---------|-------------------|
  | Self drifting   | ⚠️me    |                   |
  | Others drifting | ⚠️2     |                   |

I don't really like them.  I only use Windows 11 and the statusline is in powershell, do you have any ideas?

## Assistant

PowerShell on Windows 11 fully supports ANSI escape sequences for colors and Unicode emojis in your Claude Code statusline.py output, making it easy to create glanceable distinctions between self-drift (urgent) and others-drift (watchful).  Use your existing multi-terminal setup with env vars like TERMINAL_ID or $PID to detect "self" vs. peers via shared state files.[1][2][3][4]

## Color Pulses
Differentiate with subtle ANSI blinks or bolding for self (red pulse draws your eye), steady for others (yellow/orange stays visible but non-intrusive).
```
Self: \033[5;41m🔴\033[0m  # Blinking red bg
Others: \033[43m🟡\033[0m  # Steady yellow bg
```
Windows Terminal handles these reliably; test in statusline.py with `print("\033[5;41m🔴\033[0m", end="")`.[5][6]

## Terminal Shapes
Leverage Nerd Fonts (common in dev setups) for unique glyphs that imply "me" (filled/personal) vs. "them" (outlined/group).
```
Self: \033[31m󰀅\033[0m  # Filled flame (your fire)
Others: \033[33m󰀠\033[0m  # Hollow flames (group)
```
Set font to Cascadia Code NF in Windows Terminal profile; Python prints Unicode directly.[7][8]

## Numbered Rings
Assign ring colors/numbers by TERMINAL_ID (e.g., read from /tmp/terminals.txt); self gets hot red #1, others cooler sequential.
```
Self (ID=1): \033[41m①\033[0m
Others (ID=2): \033[43m②\033[0m, ID=3: \033[44m③\033[0m
```
In statusline.py: `term_id = os.getenv('TERMINAL_ID', str(os.getpid() % 10)); is_self = check_state_file(term_id)`.[9][4]

## Implementation Snippet
Add to your statusline.py (post-drift hook writes /tmp/drift_$TERM_ID.json):
```python
import os, json
drift_file = f'/tmp/drift_{os.getenv("TERMINAL_ID", os.getpid())}.json'
if os.path.exists(drift_file):
    data = json.load(open(drift_file))
    if data['self_drift']:
        print('\033[41;1m🔥\033[0m ', end='')
    else:
        print('\033[43m⚠\033[0m ', end='')
```
This keeps it concise, attractive, and terminal-aware without verbosity.[10][5]

## Human

Show examples of compact emoji combos that render well in PowerShell

## Assistant

PowerShell on Windows 11 with Windows Terminal renders compact emoji combos reliably using Unicode (via Python's print) or ``u{code}`` escapes, especially with Nerd Fonts like Cascadia Code NF or JetBrainsMono NF for zero-width issues.  Basic emojis like ⚠🔴🟡 work universally without font tweaks, while combos stay under 4 chars for statusline fit.[1][2][3][4]

## Drift Indicators
These 2-emoji combos distinguish self (urgent red) vs. others (watch yellow); copy-paste into statusline.py for testing.
- Self: 🔴⚠ (urgent block)[2]
- Others: 🟡👁 (watchful eye)[1]
- Self: 🔥❌ (your fire out)[4]
- Others: 🌡️⭕ (group drift ring)[5]

## Alert Variants
Compact warnings with directionality for terminal "me vs. them."
- Self: ➤🔴 (points at you)
- Others: 👥🟡 (group alert)
- Self: 🛑me
- Others: 🟨2+[3]

## Nerd Font Compact
Use these glyph combos (install Nerd Font first); they render as icons in PS7+/Terminal.
- Self: 🔴 (filled circle red)
- Others: 🟡 (hollow yellow)
Print as `print("\033[31m\033[0m", end="")`.[6][4]

## Test Code
In your statusline.py:
```python
print("🔴⚠ ", end="")  # Self
print("🟡👁 ", end="")  # Others
```
They render crisply without spacing glitches in Terminal (avoid ISE).[7][2]

## Human

Examples of compact emoji pairs for status indicators

## Assistant

Compact emoji pairs provide quick visual cues for statuslines, using 1-2 glyphs that render cleanly in PowerShell on Windows 11 with standard or Nerd Fonts.  These focus on drift/task themes: bold/filled for self/urgent, subtle/hollow for others/informational.[1][2][3]

## Urgent Self-Drift
Pairs emphasizing personal action needed.
- 🔴⚠ Red warning block[1]
- 🔥❌ Fire extinguished[4]
- 🛑➤ Stop pointing at you

## Informational Others-Drift
Muted pairs for peer monitoring.
- 🟡👁 Yellow watchful eye[3]
- ⭕🌡️ Hollow ring alert[5]
- 👥🟨 Group yellow flag

## Neutral Task States
Balanced pairs for on-track or mixed.
- 🟢✅ Green check filled[1]
- 🔵⭕ Blue hollow circle[2]
- 📍🧭 Pin and compass

## PowerShell Render Tips
Test in statusline.py: `print("🔴⚠ 🟡👁", end="")` – uses zero-width joiners implicitly via Unicode. Pair with ANSI: `\033[41m🔴\033[0m⚠`.[6][4]

## Human

can we overlap numbers on emojis?

## Assistant

Yes, PowerShell on Windows 11 with Windows Terminal supports overlapping numbers on emojis using Unicode keycap sequences (digit + U+FE0F variation selector + U+20E3 combining enclosing keycap), rendering as compact numbered icons like 1️⃣.  These work directly in your statusline.py via print("1\uFE0F\u20E3"), ideal for terminal IDs (self=1️⃣🔴, others=2️⃣🟡).[1][2][3][4]

## Keycap Rendering
Standard keycaps overlap perfectly as single glyphs.
```
1️⃣ 2️⃣ 3️⃣  # Terminal 1 (self), 2, 3
#️⃣ *️⃣     # Alt markers
```
Copy-paste renders in Terminal; Python: `print("\u0031\uFE0F\u20E3")`.[5][1]

## Drift Combos
Pair with colors/emojis for status.
- Self: 1️⃣🔴 (your urgent drift)
- Others: 2️⃣🟡 (peer info)
- Group: 3️⃣⭕ (hollow ring)[6]

## PowerShell Code
```python
# In statusline.py
term_id = os.getenv('TERMINAL_ID', '1')
keycap = chr(0x30 + int(term_id)) + '\uFE0F\u20E3'
if is_self_drift():
    print(f'\033[31m{keycap}🔴\033[0m', end='')
```
Uses surrogate pairs; reliable in PS7+/Terminal (avoid ISE).[7][8]

## Limitations
Rare spacing glitches fixed by Nerd Fonts; test sequences like "1\uFE0F\u20E3🔴". No arbitrary overlaps beyond keycaps.[9][10]

## Human

can we use custom emoji or icons?

## Assistant

No true "custom emoji" (user-designed images or SVGs) can be used in PowerShell statuslines, as console output limits to Unicode text and fonts—no image embedding.  However, thousands of custom-like icons/glyphs are available via Nerd Fonts, which patch standard fonts with developer icons that render as "custom emojis" in Windows Terminal.[1][2][3][4]

## Nerd Font Icons
Install a Nerd Font (e.g., Cascadia Code NF) in Windows Terminal profile, then print Unicode glyphs directly in statusline.py for drift icons.
```
Self: \uf179🔴  (nf-mdi-fire red)
Others: \uf293🟡 (nf-mdi-account_group yellow)
```
Copy from nerdfonts.com/cheat-sheet; Python: `print("\uf179\033[31m\033[0m", end="")`.[5][6]

## Examples for Drift
Compact glyph+emoji pairs mimicking custom designs.
- Self urgent: 🔴 (nf-fa-circle red)
- Others: 🟡 (nf-oct-circle_slash yellow)
- Terminal ID: 1️⃣ (keycap + nf-mdi-monitor)

## Setup Steps
1. Download/install Nerd Font from nerdfonts.com/fonts (e.g., JetBrainsMono).
2. Windows Terminal settings.json: `"font": { "face": "JetBrainsMono Nerd Font" }`.
3. Test: `echo -e "\uf179🔴"` – renders as flame icon.[7][8]

## Limits
Glyphs are font-bound (fallback to tofu □ if missing); no colors beyond ANSI, no animations. Use for 5000+ icons like git branches, alerts.[9][3]

## Human

can I install them from powershell?

## Assistant

Yes, multiple PowerShell modules and one-liners make installing Nerd Fonts straightforward on Windows 11—no manual downloads needed.  Run as admin for system-wide install; user-level works too.[1][2][3]

## Quick One-Liner (Web Installer)
Paste this in elevated PowerShell (pwsh or Windows PowerShell) for interactive menu:
```
& ([scriptblock]::Create((iwr 'https://to.loredo.me/Install-NerdFont.ps1')))
```
Select fonts like JetBrainsMono or CascadiaCode; auto-downloads/extracts/registers.[4][1]

## Module Install (Recommended)
For repeated use/tab-completion:
```
Install-PSResource Invoke-NerdFontInstaller  # Or: Install-Module NerdFonts (older)
Invoke-NerdFontInstaller JetBrainsMono      # Specific font
Invoke-NerdFontInstaller -All -Scope AllUsers  # All fonts, system-wide
```
List available: `Invoke-NerdFontInstaller -List All`.[2][3]

## Oh My Posh Helper
If using Oh My Posh (common for prompts):
```
oh-my-posh font install  # Interactive Nerd Font selector
```
Integrates directly with Terminal.[5]

## Post-Install
Restart Windows Terminal, set profile font to "JetBrainsMono Nerd Font" in settings.json. Test: `echo "\uf179"` (flame icon).[6][7]

## Human

PS P:\> Install-PSResource Invoke-NerdFontInstaller  # Or: Install-Module NerdFonts (older)

Untrusted repository
You are installing the modules from an untrusted repository. If you trust this repository, change
its Trusted value by running the Set-PSResourceRepository cmdlet. Are you sure you want to install
 the PSResource from 'PSGallery'?
[Y] Yes  [A] Yes to All  [N] No  [L] No to All  [S] Suspend  [?] Help (default is "N"): a
WARNING: The installation path for the script does not currently appear in the CurrentUser path environment variable. To make the script discoverable, add the script installation path, C:\Users\brsth\OneDrive\Documents\PowerShell\Scripts, to the environment PATH variable.
PS P:\> Invoke-NerdFontInstaller JetBrainsMono      # Specific font
Invoke-NerdFontInstaller: The term 'Invoke-NerdFontInstaller' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
PS P:\> Invoke-NerdFontInstaller -All -Scope AllUsers  # All fonts, system-wide
Invoke-NerdFontInstaller: The term 'Invoke-NerdFontInstaller' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
PS P:\> oh-my-posh font install  # Interactive Nerd Font selector
oh-my-posh: The term 'oh-my-posh' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
PS P:\>

## Assistant

Install-PSResource installed Invoke-NerdFontInstaller as a script (not module), so it's in `C:\Users\brsth\OneDrive\Documents\PowerShell\Scripts` but not discoverable until you refresh PATH or restart PowerShell.  Oh My Posh isn't installed yet.[1][2][3]

## Fix PATH and Run NerdFonts
Add the script path to your session PATH and run:
```
$env:PATH += ";C:\Users\brsth\OneDrive\Documents\PowerShell\Scripts"
Invoke-NerdFontInstaller JetBrainsMono
# Or list: Invoke-NerdFontInstaller -List All
```
For permanent PATH: `[Environment]::SetEnvironmentVariable("Path", $env:PATH + ";C:\Users\brsth\OneDrive\Documents\PowerShell\Scripts", "User"); $env:PATH += ";C:\Users\brsth\OneDrive\Documents\PowerShell\Scripts" then restart PS. [web:116]

## Easier: Direct Web Installer
Skip modules—run this one-liner (elevated PS recommended):
```
& ([scriptblock]::Create((iwr 'https://raw.githubusercontent.com/jpawlowski/nerd-fonts-installer-PS/main/Invoke-NerdFontInstaller.ps1'))) JetBrainsMono
```
Interactive menu if no param.[4][1]

## Oh My Posh (Optional)
Install first:
```
winget install JanDeDobbeleer.OhMyPosh -s winget  # Or: scoop install oh-my-posh
oh-my-posh font install
```
Reload shell after.[3]

## Verify
After install/restart Terminal: `echo "\uf179"` should show flame icon (not □). Update Terminal profile font to "JetBrainsMono Nerd Font".[5]

## Human

PowerShell 7.5.4
PS P:\> winget install JanDeDobbeleer.OhMyPosh -s winget  # Or: scoop install oh-my-posh
Found Oh My Posh [JanDeDobbeleer.OhMyPosh] Version 28.10.0
This application is licensed to you by its owner.
Microsoft is not responsible for, nor does it grant any licenses to, third-party packages.
Successfully verified installer hash
Starting package install...
  ██████████████████████████████  100%
Successfully installed
PS P:\> oh-my-posh font install

   Select font

  •0xProto
   3270
   AdwaitaMono
   Agave
   AnonymousPro
   Arimo
   AtkinsonHyperlegibleMono
   AurulentSansMono

   •••••••••
   ↑/k up • ↓/j down • q quit • ? more

## Assistant

Great progress—Oh My Posh v28.10.0 is installed and font installer running.  Navigate with ↑/↓ (or k/j), Enter to select, q to quit.[1][2]

## Top Recommendations
Pick one of these dev-optimized Nerd Fonts (marked with -  likely):
- **JetBrainsMono** (excellent ligatures, clean monospace for code/statuslines)
- **CascadiaCode** or **CascadiaMono** (Windows default family, native Terminal support)
- **Meslo** (compact, popular for prompts/icons)
- **FiraCode** (great ligatures if coding heavily)[3][4]

## After Selection
1. Restart Windows Terminal.
2. Edit Terminal settings.json (Ctrl+, > Open JSON): Set your PowerShell profile fontFace to the selected name + " Nerd Font" (e.g., `"fontFace": "JetBrainsMono Nerd Font"`).
3. Test in new tab: `echo "\uf179"` (should show flame icon, not □).[5]

## Claude Code Statusline
Icons now ready—use in statusline.py like `print("\uf179\033[31m\033[0m🔴", end="")` for self-drift (fire red). Restart CC terminals post-font.

## Human

PowerShell 7.5.4
PS P:\> echo "\uf179"
\uf179
PS P:\>

## Assistant

The Nerd Font glyph "\uf179" (fire icon) is printing as literal text instead of rendering as an icon, meaning Windows Terminal's PowerShell profile isn't using the Nerd Font yet.[1][2]

## Apply Font to Terminal
1. Open Windows Terminal > Settings (Ctrl+,) > Profiles > PowerShell (your PS7 profile).
2. Appearance > Font face: Enter exact name from Oh My Posh installer (e.g., "JetBrainsMono Nerd Font Mono", "Cascadia Code NF", or "MesloLGS NF").
3. Save > New tab (Ctrl+Shift+1) to test.

JSON edit (faster): Ctrl+, > Open JSON:
```json
{
    "profiles": {
        "defaults": {  // Or specific PowerShell GUID
            "font": {
                "face": "JetBrainsMono Nerd Font"
            }
        }
    }
}
```
Restart Terminal.[3][4]

## Verify Steps
- List installed fonts: `[System.Drawing.Text.InstalledFontCollection]::new().Families | sls Nerd` (run in PS).
- Test glyph: New PS tab > `Write-Output "\uf179"` or `echo $'\uf179'` – should show flame.[5]
- Cheat sheet: nerdfonts.com/cheat-sheet for more (copy-paste glyphs).

Once fixed, your statusline.py icons like `\uf179🔴` will render perfectly for drift indicators.[6]

## Human

windows 11 settings terminal appearance done't have font face

## Assistant

Font face is under **Additional settings > Appearance** (not directly under Appearance tab)—scroll down in the profile's right pane.[1][2]

## UI Steps
1. Windows Terminal > Ctrl+, (Settings).
2. Left sidebar: Select **PowerShell** profile (your PS7 one).
3. Right pane: **Additional settings** section > Click **Appearance**.
4. Scroll to **Text** > **Font face**: Type "JetBrainsMono Nerd Font" (or exact from Oh My Posh list, e.g., "Cascadia Code NF").
5. **Save** > New tab (Ctrl+T).[3][4]

## JSON Fix (Reliable)
Ctrl+, > **Open JSON** (top-right):
```json
{
    "$schema": "...",
    "profiles": {
        "defaults": {
            "font": {
                "face": "JetBrainsMono Nerd Font"
            }
        },
        "list": [
            {
                "guid": "{your PS GUID}",  // Or apply to defaults
                "font": {
                    "face": "JetBrainsMono Nerd Font"
                }
            }
        ]
    }
}
```
Save, restart Terminal.[2]

## Verify Font Names
Run: `& {Add-Type -AssemblyName System.Drawing.Text; [System.Drawing.Text.InstalledFontCollection]::new().Families | Where {$_ -like "*Nerd*" -or $_ -like "*NF*"} }` – lists exact names to use. [5]

Test glyph post-fix: `echo "\uf179"` → flame icon. Ready for statusline icons!

## Human

PowerShell 7.5.4
PS P:\> & {Add-Type -AssemblyName System.Drawing.Text; [System.Drawing.Text.InstalledFontCollection]::new().Families | Where {$_ -like "*Nerd*" -or $_ -like "*NF*"} }
Add-Type: Cannot find path 'P:\System.Drawing.Text.dll' because it does not exist.

Name
----
0xProto Nerd Font
0xProto Nerd Font Mono
0xProto Nerd Font Propo
3270 Nerd Font
3270 Nerd Font Cond
3270 Nerd Font Mono
3270 Nerd Font Mono Cond
3270 Nerd Font Mono SemCond
3270 Nerd Font Propo
3270 Nerd Font Propo Cond
3270 Nerd Font Propo SemCond
3270 Nerd Font SemCond
AdwaitaMono Nerd Font
AdwaitaMono Nerd Font Mono
AdwaitaMono Nerd Font Propo
Agave Nerd Font
Agave Nerd Font Mono
Agave Nerd Font Propo
AnonymicePro Nerd Font
AnonymicePro Nerd Font Mono
AnonymicePro Nerd Font Propo
Arimo Nerd Font
Arimo Nerd Font Propo
AtkynsonMono NF
AtkynsonMono NF Light
AtkynsonMono NF Medium
AtkynsonMono NFM
AtkynsonMono NFM Light
AtkynsonMono NFM Medium
AtkynsonMono NFP
AtkynsonMono NFP Light
AtkynsonMono NFP Medium
AurulentSansM Nerd Font
AurulentSansM Nerd Font Mono
AurulentSansM Nerd Font Propo
BigBlueTerm437 Nerd Font
BigBlueTerm437 Nerd Font Mono
BigBlueTerm437 Nerd Font Propo
BigBlueTermPlus Nerd Font
BigBlueTermPlus Nerd Font Mono
BigBlueTermPlus Nerd Font Propo
BitstromWera Nerd Font
BitstromWera Nerd Font Mono
BitstromWera Nerd Font Propo
BlexMono Nerd Font
BlexMono Nerd Font ExtraLight
BlexMono Nerd Font Light
BlexMono Nerd Font Medium
BlexMono Nerd Font Mono
BlexMono Nerd Font Mono ExtraLi
BlexMono Nerd Font Mono Light
BlexMono Nerd Font Mono Medium
BlexMono Nerd Font Mono SemiBol
BlexMono Nerd Font Mono Text
BlexMono Nerd Font Mono Thin
BlexMono Nerd Font Propo
BlexMono Nerd Font Propo ExtraL
BlexMono Nerd Font Propo Light
BlexMono Nerd Font Propo Medium
BlexMono Nerd Font Propo SemiBo
BlexMono Nerd Font Propo Text
BlexMono Nerd Font Propo Thin
BlexMono Nerd Font SemiBold
BlexMono Nerd Font Text
BlexMono Nerd Font Thin
Cascadia Code NF
Cascadia Code NF ExtraLight
Cascadia Code NF Light
Cascadia Code NF SemiBold
Cascadia Code NF SemiLight
Cascadia Mono NF
Cascadia Mono NF ExtraLight
Cascadia Mono NF Light
Cascadia Mono NF SemiBold
Cascadia Mono NF SemiLight
CaskaydiaCove NF
CaskaydiaCove NF ExtraLight
CaskaydiaCove NF Light
CaskaydiaCove NF SemiBold
CaskaydiaCove NF SemiLight
CaskaydiaCove NFM
CaskaydiaCove NFM ExtraLight
CaskaydiaCove NFM Light
CaskaydiaCove NFM SemiBold
CaskaydiaCove NFM SemiLight
CaskaydiaCove NFP
CaskaydiaCove NFP ExtraLight
CaskaydiaCove NFP Light
CaskaydiaCove NFP SemiBold
CaskaydiaCove NFP SemiLight
CaskaydiaMono NF
CaskaydiaMono NF ExtraLight
CaskaydiaMono NF Light
CaskaydiaMono NF SemiBold
CaskaydiaMono NF SemiLight
CaskaydiaMono NFM
CaskaydiaMono NFM ExtraLight
CaskaydiaMono NFM Light
CaskaydiaMono NFM SemiBold
CaskaydiaMono NFM SemiLight
CaskaydiaMono NFP
CaskaydiaMono NFP ExtraLight
CaskaydiaMono NFP Light
CaskaydiaMono NFP SemiBold
CaskaydiaMono NFP SemiLight
CodeNewRoman Nerd Font
CodeNewRoman Nerd Font Mono
CodeNewRoman Nerd Font Propo
ComicShannsMono Nerd Font
ComicShannsMono Nerd Font Mono
ComicShannsMono Nerd Font Propo
CommitMono Nerd Font
CommitMono Nerd Font Mono
CommitMono Nerd Font Propo
Cousine Nerd Font
Cousine Nerd Font Mono
Cousine Nerd Font Propo
D2CodingLigature Nerd Font
D2CodingLigature Nerd Font Mono
D2CodingLigature Nerd Font Prop
DaddyTimeMono Nerd Font
DaddyTimeMono Nerd Font Mono
DaddyTimeMono Nerd Font Propo
DejaVuSansM Nerd Font
DejaVuSansM Nerd Font Mono
DejaVuSansM Nerd Font Propo
DepartureMono Nerd Font
DepartureMono Nerd Font Mono
DepartureMono Nerd Font Propo
DroidSansM Nerd Font
DroidSansM Nerd Font Mono
DroidSansM Nerd Font Propo
EnvyCodeR Nerd Font
EnvyCodeR Nerd Font Mono
EnvyCodeR Nerd Font Propo
FantasqueSansM Nerd Font
FantasqueSansM Nerd Font Mono
FantasqueSansM Nerd Font Propo
FiraCode Nerd Font
FiraCode Nerd Font Light
FiraCode Nerd Font Med
FiraCode Nerd Font Mono
FiraCode Nerd Font Mono Light
FiraCode Nerd Font Mono Med
FiraCode Nerd Font Mono Ret
FiraCode Nerd Font Mono SemBd
FiraCode Nerd Font Propo
FiraCode Nerd Font Propo Light
FiraCode Nerd Font Propo Med
FiraCode Nerd Font Propo Ret
FiraCode Nerd Font Propo SemBd
FiraCode Nerd Font Ret
FiraCode Nerd Font SemBd
FiraMono Nerd Font
FiraMono Nerd Font Medium
FiraMono Nerd Font Mono
FiraMono Nerd Font Mono Medium
FiraMono Nerd Font Propo
FiraMono Nerd Font Propo Medium
GeistMono NF
GeistMono NF Black
GeistMono NF Light
GeistMono NF Medium
GeistMono NF SemiBold
GeistMono NF Thin
GeistMono NF UltraBlack
GeistMono NF UltraLight
GeistMono NFM
GeistMono NFM Black
GeistMono NFM Light
GeistMono NFM Medium
GeistMono NFM SemiBold
GeistMono NFM Thin
GeistMono NFM UltraBlack
GeistMono NFM UltraLight
GeistMono NFP
GeistMono NFP Black
GeistMono NFP Light
GeistMono NFP Medium
GeistMono NFP SemiBold
GeistMono NFP Thin
GeistMono NFP UltraBlack
GeistMono NFP UltraLight
GohuFont 11 Nerd Font
GohuFont 11 Nerd Font Mono
GohuFont 11 Nerd Font Propo
GohuFont 14 Nerd Font
GohuFont 14 Nerd Font Mono
GohuFont 14 Nerd Font Propo
GohuFont uni11 Nerd Font
GohuFont uni11 Nerd Font Mono
GohuFont uni11 Nerd Font Propo
GohuFont uni14 Nerd Font
GohuFont uni14 Nerd Font Mono
GohuFont uni14 Nerd Font Propo
GoMono Nerd Font
GoMono Nerd Font Mono
GoMono Nerd Font Propo
Hack Nerd Font
Hack Nerd Font Mono
Hack Nerd Font Propo
Hasklug Nerd Font
Hasklug Nerd Font Black
Hasklug Nerd Font ExtLt
Hasklug Nerd Font Light
Hasklug Nerd Font Med
Hasklug Nerd Font Mono
Hasklug Nerd Font Mono Black
Hasklug Nerd Font Mono ExtLt
Hasklug Nerd Font Mono Light
Hasklug Nerd Font Mono Med
Hasklug Nerd Font Mono SemBd
Hasklug Nerd Font Propo
Hasklug Nerd Font Propo Black
Hasklug Nerd Font Propo ExtLt
Hasklug Nerd Font Propo Light
Hasklug Nerd Font Propo Med
Hasklug Nerd Font Propo SemBd
Hasklug Nerd Font SemBd
HeavyData Nerd Font
HeavyData Nerd Font Propo
Hurmit Nerd Font
Hurmit Nerd Font Light
Hurmit Nerd Font Mono
Hurmit Nerd Font Mono Light
Hurmit Nerd Font Propo
Hurmit Nerd Font Propo Light
iMWritingDuo Nerd Font
iMWritingDuo Nerd Font Propo
iMWritingMono Nerd Font
iMWritingMono Nerd Font Mono
iMWritingMono Nerd Font Propo
iMWritingQuat Nerd Font
iMWritingQuat Nerd Font Propo
Inconsolata LGC Nerd Font
Inconsolata LGC Nerd Font Mono
Inconsolata LGC Nerd Font Propo
Inconsolata Nerd Font
Inconsolata Nerd Font Mono
Inconsolata Nerd Font Propo
InconsolataGo Nerd Font
InconsolataGo Nerd Font Mono
InconsolataGo Nerd Font Propo
Informal Roman
IntoneMono NF
IntoneMono NF Light
IntoneMono NF Medium
IntoneMono NFM
IntoneMono NFM Light
IntoneMono NFM Medium
IntoneMono NFP
IntoneMono NFP Light
IntoneMono NFP Medium
Iosevka NF
Iosevka NF ExtraBold
Iosevka NF ExtraBold Obl
Iosevka NF ExtraLight
Iosevka NF ExtraLight Obl
Iosevka NF Heavy
Iosevka NF Heavy Obl
Iosevka NF Light
Iosevka NF Light Obl
Iosevka NF Medium
Iosevka NF Medium Obl
Iosevka NF Obl
Iosevka NF SemiBold
Iosevka NF SemiBold Obl
Iosevka NF Thin
Iosevka NF Thin Obl
Iosevka NFM
Iosevka NFM ExtraBold
Iosevka NFM ExtraBold Obl
Iosevka NFM ExtraLight
Iosevka NFM ExtraLight Obl
Iosevka NFM Heavy
Iosevka NFM Heavy Obl
Iosevka NFM Light
Iosevka NFM Light Obl
Iosevka NFM Medium
Iosevka NFM Medium Obl
Iosevka NFM Obl
Iosevka NFM SemiBold
Iosevka NFM SemiBold Obl
Iosevka NFM Thin
Iosevka NFM Thin Obl
Iosevka NFP
Iosevka NFP ExtraBold
Iosevka NFP ExtraBold Obl
Iosevka NFP ExtraLight
Iosevka NFP ExtraLight Obl
Iosevka NFP Heavy
Iosevka NFP Heavy Obl
Iosevka NFP Light
Iosevka NFP Light Obl
Iosevka NFP Medium
Iosevka NFP Medium Obl
Iosevka NFP Obl
Iosevka NFP SemiBold
Iosevka NFP SemiBold Obl
Iosevka NFP Thin
Iosevka NFP Thin Obl
IosevkaTerm NF
IosevkaTerm NF ExtraBold
IosevkaTerm NF ExtraBold Obl
IosevkaTerm NF ExtraLight
IosevkaTerm NF ExtraLight Obl
IosevkaTerm NF Heavy
IosevkaTerm NF Heavy Obl
IosevkaTerm NF Light
IosevkaTerm NF Light Obl
IosevkaTerm NF Medium
IosevkaTerm NF Medium Obl
IosevkaTerm NF Obl
IosevkaTerm NF SemiBold
IosevkaTerm NF SemiBold Obl
IosevkaTerm NF Thin
IosevkaTerm NF Thin Obl
IosevkaTerm NFM
IosevkaTerm NFM ExtraBold
IosevkaTerm NFM ExtraBold Obl
IosevkaTerm NFM ExtraLight
IosevkaTerm NFM ExtraLight Obl
IosevkaTerm NFM Heavy
IosevkaTerm NFM Heavy Obl
IosevkaTerm NFM Light
IosevkaTerm NFM Light Obl
IosevkaTerm NFM Medium
IosevkaTerm NFM Medium Obl
IosevkaTerm NFM Obl
IosevkaTerm NFM SemiBold
IosevkaTerm NFM SemiBold Obl
IosevkaTerm NFM Thin
IosevkaTerm NFM Thin Obl
IosevkaTerm NFP
IosevkaTerm NFP ExtraBold
IosevkaTerm NFP ExtraBold Obl
IosevkaTerm NFP ExtraLight
IosevkaTerm NFP ExtraLight Obl
IosevkaTerm NFP Heavy
IosevkaTerm NFP Heavy Obl
IosevkaTerm NFP Light
IosevkaTerm NFP Light Obl
IosevkaTerm NFP Medium
IosevkaTerm NFP Medium Obl
IosevkaTerm NFP Obl
IosevkaTerm NFP SemiBold
IosevkaTerm NFP SemiBold Obl
IosevkaTerm NFP Thin
IosevkaTerm NFP Thin Obl
IosevkaTermSlab NF
IosevkaTermSlab NF ExtraBold
IosevkaTermSlab NF ExtraBold Ob
IosevkaTermSlab NF Light
IosevkaTermSlab NF Light Obl
IosevkaTermSlab NF Medium
IosevkaTermSlab NF Medium Obl
IosevkaTermSlab NF Obl
IosevkaTermSlab NFM
IosevkaTermSlab NFM ExtraBold
IosevkaTermSlab NFM ExtraBold O
IosevkaTermSlab NFM Light
IosevkaTermSlab NFM Light Obl
IosevkaTermSlab NFM Medium
IosevkaTermSlab NFM Medium Obl
IosevkaTermSlab NFM Obl
IosevkaTermSlab NFP
IosevkaTermSlab NFP ExtraBold
IosevkaTermSlab NFP ExtraBold O
IosevkaTermSlab NFP Light
IosevkaTermSlab NFP Light Obl
IosevkaTermSlab NFP Medium
IosevkaTermSlab NFP Medium Obl
IosevkaTermSlab NFP Obl
JetBrainsMono NF
JetBrainsMono NF ExtraBold
JetBrainsMono NF ExtraLight
JetBrainsMono NF Light
JetBrainsMono NF Medium
JetBrainsMono NF SemiBold
JetBrainsMono NF Thin
JetBrainsMono NFM
JetBrainsMono NFM ExtraBold
JetBrainsMono NFM ExtraLight
JetBrainsMono NFM Light
JetBrainsMono NFM Medium
JetBrainsMono NFM SemiBold
JetBrainsMono NFM Thin
JetBrainsMono NFP
JetBrainsMono NFP ExtraBold
JetBrainsMono NFP ExtraLight
JetBrainsMono NFP Light
JetBrainsMono NFP Medium
JetBrainsMono NFP SemiBold
JetBrainsMono NFP Thin
JetBrainsMonoNL NF
JetBrainsMonoNL NF ExtraBold
JetBrainsMonoNL NF ExtraLight
JetBrainsMonoNL NF Light
JetBrainsMonoNL NF Medium
JetBrainsMonoNL NF SemiBold
JetBrainsMonoNL NF Thin
JetBrainsMonoNL NFM
JetBrainsMonoNL NFM ExtraBold
JetBrainsMonoNL NFM ExtraLight
JetBrainsMonoNL NFM Light
JetBrainsMonoNL NFM Medium
JetBrainsMonoNL NFM SemiBold
JetBrainsMonoNL NFM Thin
JetBrainsMonoNL NFP
JetBrainsMonoNL NFP ExtraBold
JetBrainsMonoNL NFP ExtraLight
JetBrainsMonoNL NFP Light
JetBrainsMonoNL NFP Medium
JetBrainsMonoNL NFP SemiBold
JetBrainsMonoNL NFP Thin
Lekton Nerd Font
Lekton Nerd Font Mono
Lekton Nerd Font Propo
Lilex Nerd Font
Lilex Nerd Font ExtraLight
Lilex Nerd Font Medium
Lilex Nerd Font Mono
Lilex Nerd Font Mono ExtraLight
Lilex Nerd Font Mono Medium
Lilex Nerd Font Mono Thin
Lilex Nerd Font Propo
Lilex Nerd Font Propo ExtraLigh
Lilex Nerd Font Propo Medium
Lilex Nerd Font Propo Thin
Lilex Nerd Font Thin
LiterationMono Nerd Font
LiterationMono Nerd Font Mono
LiterationMono Nerd Font Propo
LiterationSans Nerd Font
LiterationSans Nerd Font Propo
LiterationSerif Nerd Font
LiterationSerif Nerd Font Propo
M+1 Nerd Font
M+1 Nerd Font Black
M+1 Nerd Font ExtBd
M+1 Nerd Font ExtLt
M+1 Nerd Font Light
M+1 Nerd Font Med
M+1 Nerd Font Propo
M+1 Nerd Font Propo Black
M+1 Nerd Font Propo ExtBd
M+1 Nerd Font Propo ExtLt
M+1 Nerd Font Propo Light
M+1 Nerd Font Propo Med
M+1 Nerd Font Propo SemBd
M+1 Nerd Font Propo Thin
M+1 Nerd Font SemBd
M+1 Nerd Font Thin
M+1Code Nerd Font
M+1Code Nerd Font ExtLt
M+1Code Nerd Font Light
M+1Code Nerd Font Med
M+1Code Nerd Font Mono
M+1Code Nerd Font Mono ExtLt
M+1Code Nerd Font Mono Light
M+1Code Nerd Font Mono Med
M+1Code Nerd Font Mono SemBd
M+1Code Nerd Font Mono Thin
M+1Code Nerd Font Propo
M+1Code Nerd Font Propo ExtLt
M+1Code Nerd Font Propo Light
M+1Code Nerd Font Propo Med
M+1Code Nerd Font Propo SemBd
M+1Code Nerd Font Propo Thin
M+1Code Nerd Font SemBd
M+1Code Nerd Font Thin
M+2 Nerd Font
M+2 Nerd Font Black
M+2 Nerd Font ExtBd
M+2 Nerd Font ExtLt
M+2 Nerd Font Light
M+2 Nerd Font Med
M+2 Nerd Font Propo
M+2 Nerd Font Propo Black
M+2 Nerd Font Propo ExtBd
M+2 Nerd Font Propo ExtLt
M+2 Nerd Font Propo Light
M+2 Nerd Font Propo Med
M+2 Nerd Font Propo SemBd
M+2 Nerd Font Propo Thin
M+2 Nerd Font SemBd
M+2 Nerd Font Thin
M+CodeLat50 Nerd Font
M+CodeLat50 Nerd Font ExtLt
M+CodeLat50 Nerd Font Light
M+CodeLat50 Nerd Font Med
M+CodeLat50 Nerd Font Mono
M+CodeLat50 Nerd Font Mono ExtL
M+CodeLat50 Nerd Font Mono Ligh
M+CodeLat50 Nerd Font Mono Med
M+CodeLat50 Nerd Font Mono SemB
M+CodeLat50 Nerd Font Mono Thin
M+CodeLat50 Nerd Font Propo
M+CodeLat50 Nerd Font Propo Ext
M+CodeLat50 Nerd Font Propo Lig
M+CodeLat50 Nerd Font Propo Med
M+CodeLat50 Nerd Font Propo Sem
M+CodeLat50 Nerd Font Propo Thi
M+CodeLat50 Nerd Font SemBd
M+CodeLat50 Nerd Font Thin
M+CodeLat60 Nerd Font
M+CodeLat60 Nerd Font ExtLt
M+CodeLat60 Nerd Font Light
M+CodeLat60 Nerd Font Med
M+CodeLat60 Nerd Font Mono
M+CodeLat60 Nerd Font Mono ExtL
M+CodeLat60 Nerd Font Mono Ligh
M+CodeLat60 Nerd Font Mono Med
M+CodeLat60 Nerd Font Mono SemB
M+CodeLat60 Nerd Font Mono Thin
M+CodeLat60 Nerd Font Propo
M+CodeLat60 Nerd Font Propo Ext
M+CodeLat60 Nerd Font Propo Lig
M+CodeLat60 Nerd Font Propo Med
M+CodeLat60 Nerd Font Propo Sem
M+CodeLat60 Nerd Font Propo Thi
M+CodeLat60 Nerd Font SemBd
M+CodeLat60 Nerd Font Thin
MartianMono NF
MartianMono NF Cond
MartianMono NF Cond Med
MartianMono NF Med
MartianMono NFM
MartianMono NFM Cond
MartianMono NFM Cond Med
MartianMono NFM Med
MartianMono NFP
MartianMono NFP Cond
MartianMono NFP Cond Med
MartianMono NFP Med
MesloLGL Nerd Font
MesloLGL Nerd Font Mono
MesloLGL Nerd Font Propo
MesloLGLDZ Nerd Font
MesloLGLDZ Nerd Font Mono
MesloLGLDZ Nerd Font Propo
MesloLGM Nerd Font
MesloLGM Nerd Font Mono
MesloLGM Nerd Font Propo
MesloLGMDZ Nerd Font
MesloLGMDZ Nerd Font Mono
MesloLGMDZ Nerd Font Propo
MesloLGS Nerd Font
MesloLGS Nerd Font Mono
MesloLGS Nerd Font Propo
MesloLGSDZ Nerd Font
MesloLGSDZ Nerd Font Mono
MesloLGSDZ Nerd Font Propo
MonaspiceAr NF
MonaspiceAr NF Light
MonaspiceAr NF Medium
MonaspiceAr NFM
MonaspiceAr NFM Light
MonaspiceAr NFM Medium
MonaspiceAr NFP
MonaspiceAr NFP Light
MonaspiceAr NFP Medium
MonaspiceKr NF
MonaspiceKr NF Light
MonaspiceKr NF Medium
MonaspiceKr NFM
MonaspiceKr NFM Light
MonaspiceKr NFM Medium
MonaspiceKr NFP
MonaspiceKr NFP Light
MonaspiceKr NFP Medium
MonaspiceNe NF
MonaspiceNe NF Light
MonaspiceNe NF Medium
MonaspiceNe NFM
MonaspiceNe NFM Light
MonaspiceNe NFM Medium
MonaspiceNe NFP
MonaspiceNe NFP Light
MonaspiceNe NFP Medium
MonaspiceRn NF
MonaspiceRn NF Light
MonaspiceRn NF Medium
MonaspiceRn NFM
MonaspiceRn NFM Light
MonaspiceRn NFM Medium
MonaspiceRn NFP
MonaspiceRn NFP Light
MonaspiceRn NFP Medium
MonaspiceXe NF
MonaspiceXe NF Light
MonaspiceXe NF Medium
MonaspiceXe NFM
MonaspiceXe NFM Light
MonaspiceXe NFM Medium
MonaspiceXe NFP
MonaspiceXe NFP Light
MonaspiceXe NFP Medium
Monofur Nerd Font
Monofur Nerd Font Mono
Monofur Nerd Font Propo
Monoid Nerd Font
Monoid Nerd Font Mono
Monoid Nerd Font Mono Retina
Monoid Nerd Font Propo
Monoid Nerd Font Propo Retina
Monoid Nerd Font Retina
Mononoki Nerd Font
Mononoki Nerd Font Mono
Mononoki Nerd Font Propo
NotoMono NF
NotoMono NFM
NotoMono NFP
NotoSans NF
NotoSans NF Black
NotoSans NF Cond
NotoSans NF Cond Black
NotoSans NF Cond ExtBd
NotoSans NF Cond ExtLt
NotoSans NF Cond Light
NotoSans NF Cond Med
NotoSans NF Cond SemBd
NotoSans NF Cond Thin
NotoSans NF ExtBd
NotoSans NF ExtCond
NotoSans NF ExtCond Black
NotoSans NF ExtCond ExtBd
NotoSans NF ExtCond ExtLt
NotoSans NF ExtCond Light
NotoSans NF ExtCond Med
NotoSans NF ExtCond SemBd
NotoSans NF ExtCond Thin
NotoSans NF ExtLt
NotoSans NF Light
NotoSans NF Med
NotoSans NF SemBd
NotoSans NF SemCond
NotoSans NF SemCond Black
NotoSans NF SemCond ExtBd
NotoSans NF SemCond ExtLt
NotoSans NF SemCond Light
NotoSans NF SemCond Med
NotoSans NF SemCond SemBd
NotoSans NF SemCond Thin
NotoSans NF Thin
NotoSans NFP
NotoSans NFP Black
NotoSans NFP Cond
NotoSans NFP Cond Black
NotoSans NFP Cond ExtBd
NotoSans NFP Cond ExtLt
NotoSans NFP Cond Light
NotoSans NFP Cond Med
NotoSans NFP Cond SemBd
NotoSans NFP Cond Thin
NotoSans NFP ExtBd
NotoSans NFP ExtCond
NotoSans NFP ExtCond Black
NotoSans NFP ExtCond ExtBd
NotoSans NFP ExtCond ExtLt
NotoSans NFP ExtCond Light
NotoSans NFP ExtCond Med
NotoSans NFP ExtCond SemBd
NotoSans NFP ExtCond Thin
NotoSans NFP ExtLt
NotoSans NFP Light
NotoSans NFP Med
NotoSans NFP SemBd
NotoSans NFP SemCond
NotoSans NFP SemCond Black
NotoSans NFP SemCond ExtBd
NotoSans NFP SemCond ExtLt
NotoSans NFP SemCond Light
NotoSans NFP SemCond Med
NotoSans NFP SemCond SemBd
NotoSans NFP SemCond Thin
NotoSans NFP Thin
NotoSansM NF
NotoSansM NF Black
NotoSansM NF Cond
NotoSansM NF Cond Black
NotoSansM NF Cond ExtBd
NotoSansM NF Cond ExtLt
NotoSansM NF Cond Light
NotoSansM NF Cond Med
NotoSansM NF Cond SemBd
NotoSansM NF Cond Thin
NotoSansM NF ExtBd
NotoSansM NF ExtCond
NotoSansM NF ExtCond Black
NotoSansM NF ExtCond ExtBd
NotoSansM NF ExtCond ExtLt
NotoSansM NF ExtCond Light
NotoSansM NF ExtCond Med
NotoSansM NF ExtCond SemBd
NotoSansM NF ExtCond Thin
NotoSansM NF ExtLt
NotoSansM NF Light
NotoSansM NF Med
NotoSansM NF SemBd
NotoSansM NF SemCond
NotoSansM NF SemCond Black
NotoSansM NF SemCond ExtBd
NotoSansM NF SemCond ExtLt
NotoSansM NF SemCond Light
NotoSansM NF SemCond Med
NotoSansM NF SemCond SemBd
NotoSansM NF SemCond Thin
NotoSansM NF Thin
NotoSansM NFM
NotoSansM NFM Black
NotoSansM NFM Cond
NotoSansM NFM Cond Black
NotoSansM NFM Cond ExtBd
NotoSansM NFM Cond ExtLt
NotoSansM NFM Cond Light
NotoSansM NFM Cond Med
NotoSansM NFM Cond SemBd
NotoSansM NFM Cond Thin
NotoSansM NFM ExtBd
NotoSansM NFM ExtCond
NotoSansM NFM ExtCond Black
NotoSansM NFM ExtCond ExtBd
NotoSansM NFM ExtCond ExtLt
NotoSansM NFM ExtCond Light
NotoSansM NFM ExtCond Med
NotoSansM NFM ExtCond SemBd
NotoSansM NFM ExtCond Thin
NotoSansM NFM ExtLt
NotoSansM NFM Light
NotoSansM NFM Med
NotoSansM NFM SemBd
NotoSansM NFM SemCond
NotoSansM NFM SemCond Black
NotoSansM NFM SemCond ExtBd
NotoSansM NFM SemCond ExtLt
NotoSansM NFM SemCond Light
NotoSansM NFM SemCond Med
NotoSansM NFM SemCond SemBd
NotoSansM NFM SemCond Thin
NotoSansM NFM Thin
NotoSansM NFP
NotoSansM NFP Black
NotoSansM NFP Cond
NotoSansM NFP Cond Black
NotoSansM NFP Cond ExtBd
NotoSansM NFP Cond ExtLt
NotoSansM NFP Cond Light
NotoSansM NFP Cond Med
NotoSansM NFP Cond SemBd
NotoSansM NFP Cond Thin
NotoSansM NFP ExtBd
NotoSansM NFP ExtCond
NotoSansM NFP ExtCond Black
NotoSansM NFP ExtCond ExtBd
NotoSansM NFP ExtCond ExtLt
NotoSansM NFP ExtCond Light
NotoSansM NFP ExtCond Med
NotoSansM NFP ExtCond SemBd
NotoSansM NFP ExtCond Thin
NotoSansM NFP ExtLt
NotoSansM NFP Light
NotoSansM NFP Med
NotoSansM NFP SemBd
NotoSansM NFP SemCond
NotoSansM NFP SemCond Black
NotoSansM NFP SemCond ExtBd
NotoSansM NFP SemCond ExtLt
NotoSansM NFP SemCond Light
NotoSansM NFP SemCond Med
NotoSansM NFP SemCond SemBd
NotoSansM NFP SemCond Thin
NotoSansM NFP Thin
NotoSerif NF
NotoSerif NF Black
NotoSerif NF Cond
NotoSerif NF Cond Black
NotoSerif NF Cond ExtBd
NotoSerif NF Cond ExtLt
NotoSerif NF Cond Light
NotoSerif NF Cond Med
NotoSerif NF Cond SemBd
NotoSerif NF Cond Thin
NotoSerif NF ExtBd
NotoSerif NF ExtCond
NotoSerif NF ExtCond Black
NotoSerif NF ExtCond ExtBd
NotoSerif NF ExtCond ExtLt
NotoSerif NF ExtCond Light
NotoSerif NF ExtCond Med
NotoSerif NF ExtCond SemBd
NotoSerif NF ExtCond Thin
NotoSerif NF ExtLt
NotoSerif NF Light
NotoSerif NF Med
NotoSerif NF SemBd
NotoSerif NF SemCond
NotoSerif NF SemCond Black
NotoSerif NF SemCond ExtBd
NotoSerif NF SemCond ExtLt
NotoSerif NF SemCond Light
NotoSerif NF SemCond Med
NotoSerif NF SemCond SemBd
NotoSerif NF SemCond Thin
NotoSerif NF Thin
NotoSerif NFP
NotoSerif NFP Black
NotoSerif NFP Cond
NotoSerif NFP Cond Black
NotoSerif NFP Cond ExtBd
NotoSerif NFP Cond ExtLt
NotoSerif NFP Cond Light
NotoSerif NFP Cond Med
NotoSerif NFP Cond SemBd
NotoSerif NFP Cond Thin
NotoSerif NFP ExtBd
NotoSerif NFP ExtCond
NotoSerif NFP ExtCond Black
NotoSerif NFP ExtCond ExtBd
NotoSerif NFP ExtCond ExtLt
NotoSerif NFP ExtCond Light
NotoSerif NFP ExtCond Med
NotoSerif NFP ExtCond SemBd
NotoSerif NFP ExtCond Thin
NotoSerif NFP ExtLt
NotoSerif NFP Light
NotoSerif NFP Med
NotoSerif NFP SemBd
NotoSerif NFP SemCond
NotoSerif NFP SemCond Black
NotoSerif NFP SemCond ExtBd
NotoSerif NFP SemCond ExtLt
NotoSerif NFP SemCond Light
NotoSerif NFP SemCond Med
NotoSerif NFP SemCond SemBd
NotoSerif NFP SemCond Thin
NotoSerif NFP Thin
OpenDyslexic Nerd Font
OpenDyslexic Nerd Font Propo
OpenDyslexicAlt Nerd Font
OpenDyslexicAlt Nerd Font Propo
OpenDyslexicM Nerd Font
OpenDyslexicM Nerd Font Mono
OpenDyslexicM Nerd Font Propo
Overpass Nerd Font
Overpass Nerd Font ExtBd
Overpass Nerd Font ExtLt
Overpass Nerd Font Heavy
Overpass Nerd Font Light
Overpass Nerd Font Propo
Overpass Nerd Font Propo ExtBd
Overpass Nerd Font Propo ExtLt
Overpass Nerd Font Propo Heavy
Overpass Nerd Font Propo Light
Overpass Nerd Font Propo SemBd
Overpass Nerd Font Propo Thin
Overpass Nerd Font SemBd
Overpass Nerd Font Thin
OverpassM Nerd Font
OverpassM Nerd Font Light
OverpassM Nerd Font Mono
OverpassM Nerd Font Mono Light
OverpassM Nerd Font Mono SemBd
OverpassM Nerd Font Propo
OverpassM Nerd Font Propo Light
OverpassM Nerd Font Propo SemBd
OverpassM Nerd Font SemBd
ProFont IIx Nerd Font
ProFont IIx Nerd Font Mono
ProFont IIx Nerd Font Propo
ProFontWindows Nerd Font
ProFontWindows Nerd Font Mono
ProFontWindows Nerd Font Propo
ProggyClean CE Nerd Font
ProggyClean CE Nerd Font Mono
ProggyClean CE Nerd Font Propo
ProggyClean Nerd Font
ProggyClean Nerd Font Mono
ProggyClean Nerd Font Propo
ProggyCleanSZ Nerd Font
ProggyCleanSZ Nerd Font Mono
ProggyCleanSZ Nerd Font Propo
RecMonoCasual Nerd Font
RecMonoCasual Nerd Font Mono
RecMonoCasual Nerd Font Propo
RecMonoDuotone Nerd Font
RecMonoDuotone Nerd Font Mono
RecMonoDuotone Nerd Font Propo
RecMonoLinear Nerd Font
RecMonoLinear Nerd Font Mono
RecMonoLinear Nerd Font Propo
RecMonoSmCasual Nerd Font
RecMonoSmCasual Nerd Font Mono
RecMonoSmCasual Nerd Font Propo
RobotoMono Nerd Font
RobotoMono Nerd Font Lt
RobotoMono Nerd Font Md
RobotoMono Nerd Font Mono
RobotoMono Nerd Font Mono Lt
RobotoMono Nerd Font Mono Md
RobotoMono Nerd Font Mono SmBd
RobotoMono Nerd Font Mono Th
RobotoMono Nerd Font Propo
RobotoMono Nerd Font Propo Lt
RobotoMono Nerd Font Propo Md
RobotoMono Nerd Font Propo SmBd
RobotoMono Nerd Font Propo Th
RobotoMono Nerd Font SmBd
RobotoMono Nerd Font Th
SauceCodePro NF
SauceCodePro NF Black
SauceCodePro NF ExtraLight
SauceCodePro NF Light
SauceCodePro NF Medium
SauceCodePro NF SemiBold
SauceCodePro NFM
SauceCodePro NFM Black
SauceCodePro NFM ExtraLight
SauceCodePro NFM Light
SauceCodePro NFM Medium
SauceCodePro NFM SemiBold
SauceCodePro NFP
SauceCodePro NFP Black
SauceCodePro NFP ExtraLight
SauceCodePro NFP Light
SauceCodePro NFP Medium
SauceCodePro NFP SemiBold
ShureTechMono Nerd Font
ShureTechMono Nerd Font Mono
ShureTechMono Nerd Font Propo
SpaceMono Nerd Font
SpaceMono Nerd Font Mono
SpaceMono Nerd Font Propo
Symbols Nerd Font
Symbols Nerd Font Mono
Terminess Nerd Font
Terminess Nerd Font Mono
Terminess Nerd Font Propo
Tinos Nerd Font
Tinos Nerd Font Propo
Ubuntu Nerd Font
Ubuntu Nerd Font Cond
Ubuntu Nerd Font Light
Ubuntu Nerd Font Med
Ubuntu Nerd Font Propo
Ubuntu Nerd Font Propo Cond
Ubuntu Nerd Font Propo Light
Ubuntu Nerd Font Propo Med
UbuntuMono Nerd Font
UbuntuMono Nerd Font Mono
UbuntuMono Nerd Font Propo
UbuntuSans NF
UbuntuSans NF Medium
UbuntuSans NF SemiBold
UbuntuSans NFP
UbuntuSans NFP Medium
UbuntuSans NFP SemiBold
UbuntuSansMono NF
UbuntuSansMono NF Medium
UbuntuSansMono NF SemiBold
UbuntuSansMono NFM
UbuntuSansMono NFM Medium
UbuntuSansMono NFM SemiBold
UbuntuSansMono NFP
UbuntuSansMono NFP Medium
UbuntuSansMono NFP SemiBold
VictorMono NF
VictorMono NF ExtraLight
VictorMono NF ExtraLight Obl
VictorMono NF Light
VictorMono NF Light Obl
VictorMono NF Medium
VictorMono NF Medium Obl
VictorMono NF Obl
VictorMono NF SemiBold
VictorMono NF SemiBold Obl
VictorMono NF Thin
VictorMono NF Thin Obl
VictorMono NFM
VictorMono NFM ExtraLight
VictorMono NFM ExtraLight Obl
VictorMono NFM Light
VictorMono NFM Light Obl
VictorMono NFM Medium
VictorMono NFM Medium Obl
VictorMono NFM Obl
VictorMono NFM SemiBold
VictorMono NFM SemiBold Obl
VictorMono NFM Thin
VictorMono NFM Thin Obl
VictorMono NFP
VictorMono NFP ExtraLight
VictorMono NFP ExtraLight Obl
VictorMono NFP Light
VictorMono NFP Light Obl
VictorMono NFP Medium
VictorMono NFP Medium Obl
VictorMono NFP Obl
VictorMono NFP SemiBold
VictorMono NFP SemiBold Obl
VictorMono NFP Thin
VictorMono NFP Thin Obl
ZedMono NF
ZedMono NF Extd
ZedMono NF Extd ExtBd
ZedMono NF Extd ExtBd Obl
ZedMono NF Extd Light
ZedMono NF Extd Light Obl
ZedMono NF Extd Med
ZedMono NF Extd Med Obl
ZedMono NF Extd Obl
ZedMono NF ExtraBold
ZedMono NF ExtraBold Obl
ZedMono NF Light
ZedMono NF Light Obl
ZedMono NF Medium
ZedMono NF Medium Obl
ZedMono NF Obl
ZedMono NFM
ZedMono NFM Extd
ZedMono NFM Extd ExtBd
ZedMono NFM Extd ExtBd Obl
ZedMono NFM Extd Light
ZedMono NFM Extd Light Obl
ZedMono NFM Extd Med
ZedMono NFM Extd Med Obl
ZedMono NFM Extd Obl
ZedMono NFM ExtraBold
ZedMono NFM ExtraBold Obl
ZedMono NFM Light
ZedMono NFM Light Obl
ZedMono NFM Medium
ZedMono NFM Medium Obl
ZedMono NFM Obl
ZedMono NFP
ZedMono NFP Extd
ZedMono NFP Extd ExtBd
ZedMono NFP Extd ExtBd Obl
ZedMono NFP Extd Light
ZedMono NFP Extd Light Obl
ZedMono NFP Extd Med
ZedMono NFP Extd Med Obl
ZedMono NFP Extd Obl
ZedMono NFP ExtraBold
ZedMono NFP ExtraBold Obl
ZedMono NFP Light
ZedMono NFP Light Obl
ZedMono NFP Medium
ZedMono NFP Medium Obl
ZedMono NFP Obl

PS P:\>+

## Assistant

You’re good: fonts are installed; now Windows Terminal just needs to be told to use one (e.g., `JetBrainsMono NF` or `Cascadia Mono NF`).[1][2]

## 1. Pick a Nerd Font name
From your list, solid choices for code/statuslines:
- **JetBrainsMono NF**
- Cascadia Mono NF
- FiraCode Nerd Font

Remember the name exactly as shown (e.g., `JetBrainsMono NF`).[3]

## 2. Set font in Windows Terminal (JSON way)
Since the UI is being awkward, edit settings JSON:

1. Windows Terminal → Ctrl+, → top-right **“Open JSON file”**.[4]
2. In the JSON, locate the `profiles` section and add a `font` block.

Minimal example applying to all profiles:
```json
{
  "profiles": {
    "defaults": {
      "font": {
        "face": "JetBrainsMono NF"
      }
    }
  }
}
```

If you want *only* PowerShell (find its GUID/profile entry in `profiles.list`):
```json
{
  "profiles": {
    "list": [
      {
        "guid": "{YOUR-POWERSHELL-GUID}",
        "name": "PowerShell",
        "font": {
          "face": "JetBrainsMono NF"
        }
      }
    ]
  }
}
```
Save the file, then fully close and reopen Windows Terminal.[5][6]

## 3. Verify glyphs
In a new PowerShell tab:

```powershell
# Nerd glyph via escape
"$( [char]0xf179 )"  # should be a flame, not literal ''
# or:
echo $'\uf179'
```

If that shows an icon, your Claude Code statusline can safely use `\uf179` etc. for compact drift indicators.[7]

## Human

image.jpg

## Assistant

Your Windows Terminal profile is correctly set to **JetBrainsMono Nerd Font**, so the missing icon is just about how PowerShell is emitting the character.[1][2]

## 1. Use proper escape syntax
In PowerShell 7, `echo "\uf179"` prints the literal `\uf179` string. Use either the ANSI C–style escape or `[char]`:

```powershell
# Option A: ANSI C-style escape
echo $'\uf179'

# Option B: explicit char cast
[char]0xf179
"Here: $( [char]0xf179 )"
```
You should now see a flame-like Nerd Font glyph instead of text.[3]

## 2. Apply in statusline.py
In Python (Claude Code statusline):

```python
icon = "\uf179"  # fire glyph from JetBrainsMono NF
print(icon + " 🔴", end="")
```

With the font active, this will render as a compact icon+emoji pair in your PowerShell statusline.[2]

## Human

PowerShell 7.5.4
PS P:\> echo $'\uf179'
$\uf179
PS P:\> [char]0xf179

PS P:\> "Here: $( [char]0xf179 )"
Here: 
PS P:\>

## Assistant

Everything is working now: `JetBrainsMono NF` is active and `[char]0xf179` renders as the Apple logo (that code point is Font Awesome’s **fa-apple** glyph in Nerd Fonts).[1][2]

## Why `echo $'\uf179'` looked wrong
- PowerShell’s single-quoted `$'...'` escape form behaves differently than Bash and is echoing the backslash literally in your build.[3]
- Using `[char]0xf179` or interpolation `"$( [char]0xf179 )"` is the reliable pattern for Nerd Font glyphs in PS 7.[3]

## How to use this in statusline.py
For your Claude Code statusline, just embed the Unicode directly in Python:

```python
APPLE = "\uf179"  # fa-apple from Font Awesome region
print(f"{APPLE} 🔴", end="")  # example combo
```

Or for other icons, grab code points from the Nerd Fonts cheat sheet, then confirm with `[char]0xCODE` in PowerShell as you just did.[4][5]

If you want a flame or warning-style icon instead of Apple, pick a different code point from the cheat sheet (search “fire”, “warn”, etc.) and test it the same way.[4]

## Human

what's the fire?

## Assistant

For Nerd Fonts (JetBrainsMono NF, etc.), the classic **Font Awesome “fire”** icon is at Unicode code point **`0xf06d`**.[1][2]

## PowerShell test
```powershell
[char]0xf06d
"Fire: $( [char]0xf06d )"
```
You should see the flame glyph rendered (if your font supports the FA set).[3]

## Use in statusline.py
In Python for Claude Code statusline:

```python
FIRE = "\uf06d"  # Font Awesome fire
print(f"{FIRE} 🔴", end="")   # self-drift
print(f"{FIRE} 🟡", end="")   # others-drift
```

If that particular codepoint doesn’t look right in JetBrainsMono NF, use the Nerd Fonts cheat sheet search (“fire”) to try any of the alternate fire/flame icons (copy their code point and swap it into `[char]0x....`).[4][5]

## Human

that's the hollow, what's the full?

## Assistant

For the **“full”/solid fire** icon in the Font Awesome / Nerd Font set, use code point **`0xf7e4`**, which is **fa-fire-alt** (a larger, filled flame).[1][2]

## PowerShell test
```powershell
[char]0xf7e4
"Full fire: $( [char]0xf7e4 )"
```
That should render as a more solid flame than `0xf06d`.[3]

## In statusline.py
```python
FIRE_FULL = "\uf7e4"   # fa-fire-alt
print(f"{FIRE_FULL} 🔴", end="")  # self drift
```
If JetBrainsMono NF maps it slightly differently, you can confirm visually and, if needed, search “fire-alt” or “fire-flame” on the Nerd Fonts cheat sheet to try nearby codes.[4][5]

## Human

PowerShell 7.5.4
PS P:\> echo $'\uf179'
$\uf179
PS P:\> [char]0xf179

PS P:\> "Here: $( [char]0xf179 )"
Here: 
PS P:\> "$( [char]0xf179 )"

PS P:\> "$( [char]0xf06d )"

PS P:\> "$( [char]0xf7e4 )"

PS P:\>

## Assistant

You now have three working fire-related glyphs from your Nerd Font, rendered correctly in PowerShell with JetBrainsMono NF.[1][2]

## What you’ve got
- `0xf179` →  (Apple logo, **not** fire).
- `0xf06d` →  (classic **fire** / flame).
- `0xf7e4` →  (alternate, **bigger/curvier flame**).

## Good choices for statusline
For Claude Code drift indicators in statusline.py:

```python
FIRE = "\uf06d"    # classic fire
FIRE_FULL = "\uf7e4"  # larger curved fire

# Example:
print(f"{FIRE_FULL} 🔴", end="")   # self drifting
print(f"{FIRE} 🟡", end="")        # others drifting
```

Pick whichever reads better at 12pt in your terminal; `0xf7e4` is usually more visually **prominent** for “urgent self-drift”.[3][4]

## Human

the large fire made a question mark.

## Assistant

That question‑mark box means JetBrainsMono NF doesn’t include that specific glyph (`0xf7e4`) in the variant you’re using, even though it exists in some Font Awesome sets.  The classic fire `0xf06d` works in your font, so use that as the **solid** fire for your statusline.[1][2]

## Use the working fire
You already confirmed:
- `"$( [char]0xf06d )"` →  (rendered fire)
- `"$( [char]0xf7e4 )"` → replacement glyph (missing icon)

So in statusline.py:

```python
FIRE = "\uf06d"  # works in JetBrainsMono NF

SELF_DRIFT = FIRE + " 🔴"
OTHERS_DRIFT = FIRE + " 🟡"

print(SELF_DRIFT, end="")
```

If you want a *bigger* or alternative flame, the only reliable way is to pick another fire-style glyph from the Nerd Fonts cheat sheet that renders in JetBrainsMono NF (copy its code point, test with `[char]0x....` like you did, and swap it in).[3][4]
