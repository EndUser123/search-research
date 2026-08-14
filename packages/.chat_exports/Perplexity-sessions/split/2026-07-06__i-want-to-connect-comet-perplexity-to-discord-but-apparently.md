---
title: "I want to connect comet & perplexity to discord, but apparently I need a bot token.  How do I get one?"
date: "2026-07-06"
mode: "COPILOT"
uuid: "1cc34316-a49c-4166-8dee-583d39ec8921"
entry_count: 1
---

## Human

I want to connect comet & perplexity to discord, but apparently I need a bot token.  How do I get one?

## Assistant

You get a Discord bot token from the Discord Developer Portal by creating a “bot” under an application and then copying its token from the Bot tab.[1][2][3]

## What the bot token is

A Discord bot token is a secret string that your code (or a tool like Comet/Perplexity) uses to authenticate to Discord’s API as your bot user.  Anyone with that token can fully control the bot, so it must be treated like a password and kept private.[4][2][1]

## Step‑by‑step: create bot and get token

Use a browser on desktop; mobile technically works but is more annoying. Steps reflect the current Developer Portal flow.[2][3][1]

1. Open the Developer Portal  
   - Go to `https://discord.com/developers/applications`.[1][2]
   - Log in with the same Discord account you use for your servers.[5][6]

2. Create an application (if you don’t have one yet)  
   - Click “New Application” at the top right.[3][5]
   - Give it a name (e.g., `comet-perplexity-bridge`) and click “Create.”[7][3]

3. Add a bot user to the application  
   - In the left sidebar, click “Bot.”[6][7]
   - Click “Add Bot” (or “Create Bot”) and confirm. This attaches a bot user to your application.[8][7][6]

4. Get the bot token  
   - Still on the Bot tab, look for the “Token” or “Build‑A‑Bot > Token” section.[9][6][2]
   - For new bots you may see “Reset Token” or “Click to Reveal Token” instead of a visible string; click that.[7][2][3]
   - Discord will ask you to confirm and may ask for your password; after that, it shows the token and a “Copy” button.[10][11][2]
   - Click “Copy” and paste the token into a secure place (e.g., a `.env` file or a secret manager), not into chat or screenshots.[5][6][2]

5. (Optional but usually needed) Enable intents and permissions  
   - On the Bot tab, under “Privileged Gateway Intents,” toggle on the intents your integration needs (often Presence, Server Members, and Message Content for most bots).[11][12]
   - Click “Save Changes.”[11]
   - To invite the bot to your server, go to “OAuth2” → “URL Generator,” select “bot” in scopes, choose the permissions, copy the URL, and open it in your browser to add the bot to your Discord server.[12][11][1]

## Using the token with Comet / Perplexity

Most Discord integrations or frameworks will ask for the bot token as a config value or environment variable rather than hard‑coding it:

- For typical Node/Python bots you’d set something like `DISCORD_BOT_TOKEN=...` in `.env` and have your code read it.[5]
- For third‑party tools (Comet, Perplexity integrations, dashboards, etc.), they’ll usually have a “Connect Discord” or “Discord bot token” field where you paste the token once.[13][14]

## Security and reset

If you accidentally leak the token (commit to GitHub, paste in a screenshot, etc.):

- Go back to Developer Portal → Application → Bot → “Reset Token.”[10][3][7]
- Confirm; Discord immediately invalidates the old token and issues a new one, which you must update wherever it’s configured.[2][10][7]

To tailor this to your setup: are you planning to run your Discord integration from your own Node/Python code, or primarily through a hosted service (Comet/Perplexity integration UI)?  
