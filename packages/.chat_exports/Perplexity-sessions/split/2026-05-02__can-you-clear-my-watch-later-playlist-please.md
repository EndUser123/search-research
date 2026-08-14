---
title: "can you clear my watch later playlist please?"
date: "2026-05-02"
mode: "COPILOT"
uuid: "fd79fd26-562e-429d-9fb1-939c2fc3b866"
entry_count: 4
---

## Human

can you clear my watch later playlist please?

## Assistant

I can see your Watch Later playlist has 4,923 videos. Clearing it will remove all videos from the playlist. This is a significant action — can you confirm you want me to proceed with removing all 4,923 videos?

## Human

Clear Playlist

## Assistant

Answer skipped.

## Human

Can you use the method suggested here?  [https://gist.github.com/astamicu/eb351ce10451f1a51b71a1287d36880f](https://gist.github.com/astamicu/eb351ce10451f1a51b71a1287d36880f)

## Assistant

I wasn't able to execute the Gist script automatically — here's why and what you can do:

**The problem:** The script requires running JavaScript in Chrome's DevTools console, but I can't interact with the DevTools panel (it opens in a separate window outside my browser viewport). Chrome also blocks `javascript:` URLs typed into the address bar for security reasons.

**To run it yourself (takes ~2 minutes to set up, then runs automatically):**

1. Go to your Watch Later playlist: `https://www.youtube.com/playlist?list=WL`
2. Open DevTools: press **F12** → click the **Console** tab
3. Paste this script and press Enter:

```javascript
setInterval(function () {
    video = document.getElementsByTagName('ytd-playlist-video-renderer')[0];
    video.querySelector('#primary button[aria-label="Action menu"]').click();
    var things = document.evaluate(
        '//span[contains(text(),"Remove from")]',
        document,
        null,
        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
        null
    );
    for (var i = 0; i < things.snapshotLength; i++) {
        things.snapshotItem(i).click();
    }
}, 500);
```

The script will automatically click the "⋮" menu on the first video and select "Remove from Watch Later" every 500ms. With ~4,922 videos it'll take roughly **40–45 minutes** to complete. You can speed it up by lowering `500` to `300` (as commenters on the Gist suggested using `200`).

Leave the tab open and active while it runs. If it stops, just paste and run it again.

## Human

how do I make it stop?

## Assistant

The script is working — it's dropped from 4,922 to 4,870 videos already. To stop it, go to the **DevTools console** and run:

```javascript
var id = 1; while(id--) clearInterval(id);
```

Or more reliably, just **close and reopen the YouTube tab** — that kills all running scripts instantly. The `setInterval` only lives for the duration of the page session.
