---
title: "javascript:document.title=JSON.stringify({ls:Object.keys(localStorage),cookie:document.cookie.substring(0,200)})"
date: "2026-04-19"
mode: "CONCISE"
uuid: "24f1fd1b-4e03-483c-952d-9d3b4630d651"
entry_count: 1
---

## Human

javascript:document.title=JSON.stringify({ls:Object.keys(localStorage),cookie:document.cookie.substring(0,200)})

## Assistant

That JavaScript snippet, when run in the address bar or console on a page, will set the page’s title to a JSON blob containing:

- `ls`: An array of all keys currently stored in `window.localStorage` for that origin.[1][2]
- `cookie`: The first 200 characters of `document.cookie` for that page (i.e., all non-HTTPOnly cookies visible to JavaScript, truncated).[3][4][5]

Here’s your code, formatted:

```javascript
javascript:document.title = JSON.stringify({
  ls: Object.keys(localStorage),
  cookie: document.cookie.substring(0, 200)
})
```

So after running it:

- The tab title becomes something like:  
  `{"ls":["key1","key2"],"cookie":"sessionid=...; other=..."}`  
- No network exfiltration happens by itself; it just exposes what’s stored to whoever can see or copy the title (e.g., via screenshots, tab sync, or an extension that reads titles).

A couple of nuances / safety notes:

- It can’t see HTTPOnly cookies (those are hidden from `document.cookie`).[4]
- It only sees `localStorage` for the current origin; it can’t read storage from other sites.[6][1]
- If you paste this into a bookmarklet and click it on arbitrary sites, you’re not giving *more* power than that page’s own JS already has—you’re just packaging it into the title.

If you tell me what you want to do with this (debug, export, security check, etc.), I can suggest a safer or more detailed variant (e.g., logging values instead of just keys, or filtering out sensitive cookie names).  
