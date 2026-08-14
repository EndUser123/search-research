---
title: "in the min browser, how can I see more than one tab at a time on the header bar?"
date: "2026-07-15"
mode: "COPILOT"
uuid: "4400a6c8-043c-45cc-9f6e-73c5b371b3b6"
entry_count: 6
---

## Human

in the min browser, how can I see more than one tab at a time on the header bar?

## Assistant

You can only see one “full-width” tab at a time in Min’s header; multiple tabs appear as small icons to save space, and there isn’t a built‑in option to show several expanded tabs side‑by‑side like Chrome/Firefox’s traditional tab bar.[1]

## How Min’s tab bar works

Min is designed so tabs “take up less space,” which is why you see compact tab icons instead of a wide strip with many labeled tabs.  Focus Mode can even hide other tabs entirely so you only see the active one, further reducing visible clutter.[1]

In practice:

- The header shows the current tab’s title and controls.
- Other open tabs appear as small favicons/indicators, often grouped or minimized.
- There’s no setting to switch to a multi-row or “many wide tabs” layout on the header bar.

## Ways to approximate “multiple tabs visible”

Min doesn’t currently offer a native “show several full tabs across the header” option.  To get something closer to seeing multiple things at once:[1]

- Open another Min window (so you can put two pages side‑by‑side at the OS level).
- Use Min’s tab list / search view (Min supports viewing all tabs in a list) to quickly see and jump between many tabs, even though they’re not all wide on the header bar.[2]
- Avoid Focus Mode if you want at least icons for other tabs visible.[1]

Given your workflow, are you mainly trying to get a traditional, many‑tabs-across-the-top layout, or do you actually want side‑by‑side page viewing (like tiled windows)?

## Human

many‑tabs-across-the-top

## Assistant

Min does not currently support a traditional “many full tabs across the top with titles” tab strip like Chrome, Firefox, or Edge; its compact, icon‑style tab design is intentional and not configurable into a wide multi‑tab header.[1][2]

## Min’s tab layout limitations

Min’s design goal is to minimize chrome (UI) so the page, not the tab bar, takes most of the space.  As a result:[2]

- Tabs are small and title‑less in the header, often just favicons or minimal indicators.[2]
- There is no documented setting to switch to a classic, label‑heavy tab bar where dozens of tabs are fully visible at once.[2]
- The workflow Min promotes instead is “tasks” (tab groups) and quick switching/searching, rather than visually scanning a long horizontal list of tabs.[1]

From available docs and community discussions, there’s no built‑in preference or flag to enable multi‑row tabs or a wider, traditional tab strip in Min.[1][2]

## Practical options if you need many-visible tabs

If “many‑tabs‑across‑the‑top” is central to your workflow, you effectively have three options:

- Accept Min’s model and lean on tab search and tasks: use Min’s “Search Tabs” / tab list and task/group features to jump quickly instead of visually scanning a strip.[3][1]
- Use multiple windows: open more than one Min window and rely on the OS’s window management (tiling, snapping) to see several contexts at once, though each window still has Min’s compact tabs.[2]
- Switch browsers for this particular workflow: Chrome, Firefox, Edge, and others still offer traditional or vertical tab strips with many visible tabs and titles; vertical tabs in Chrome/Edge are particularly good for large tab counts while keeping titles readable.[4][5]

Given that you specifically want “many‑tabs‑across‑the‑top,” my honest assessment is that Min is probably the wrong primary browser for that requirement unless you are willing to change how you navigate tabs (search/shortcuts instead of visual scanning).[3][2]

If you stay with Min, do you already use its tasks/tab-search features, or would a quick shortcut/flow overview for those be useful?

## Human

<q>favicons or minimal indicators</q> why not be creative and tell me how to do this instead of giving up?

## Assistant

You can’t flip a built‑in switch to get “Chrome‑style many tabs with titles across the top” in Min, but you absolutely can hack it yourself because Min’s UI is just HTML/CSS/JS inside an Electron app.  With a small fork or local modification, you can turn those favicon‑only tab indicators into full, labeled tabs across the top.[1][2][3]

Below is a pragmatic, minimal‑change path to “many‑tabs‑across‑the‑top” that assumes you’re comfortable with Node/Electron and editing HTML/CSS.

## What’s possible vs built-in

FACT (from docs/source): Min is an Electron browser whose interface is written in JavaScript, CSS, and HTML.  That means the tab strip is just a DOM tree you can restyle or even re-layout entirely.[2][3][1]

CONSENSUS: The official Min builds intentionally ship a minimal tab UI and do not expose a preference for “classic tab strip” or multi‑row tabs.[4][5]

SPECULATION (medium confidence): With a small CSS/JS patch to the tab bar component, you can:

- Show tab titles next to favicons.
- Force tabs into a horizontal flex row that overflows/scrolls instead of collapsing into tiny icons.
- Add hover/active styling to make it feel closer to Chrome/Firefox.

## High-level approach

You have two main creative paths:

1. **Local patch of Min’s installed app**  
   - Edit the packaged Electron app files on your machine.  
   - Quick to experiment, but fragile across updates.

2. **Fork Min on GitHub and build your own “Min‑Plus”**  
   - Clone `minbrowser/min`.[6]
   - Modify the tab bar React/JS and CSS.  
   - Build and install your customized browser.

For someone in your role, I’d go straight to option 2 and keep changes surgical.

## Step 1: Get the source and find the tab bar

FACT: Min’s official repo is at `github.com/minbrowser/min`.[6]

Action:

1. Clone the repo:

   ```bash
   git clone https://github.com/minbrowser/min.git
   cd min
   ```

2. Install dependencies and run in dev:

   ```bash
   npm install
   npm start
   ```

3. Locate the tab bar component:  
   - The UI is in the `app/` or similar directory (names can shift; check `package.json` and `app` folder).[3][1]
   - Look for files named like `tabs.js`, `tabBar.js`, or `browser.js` that render a list of tabs.  
   - Identify the CSS for the tab strip (likely in a global stylesheet or a CSS module referenced by that component).

Assumption: Tabs are rendered as a list (e.g., `<div class="tab">`) with favicon and some title text, currently constrained by CSS to look “minimal.”

## Step 2: Turn tiny indicators into full-width tabs

We can steal ideas from other browsers’ custom CSS hacks (like Firefox/Vivaldi) and apply them to Min’s tab bar.[7][8][9]

Concept: treat each tab like a flexible item in a horizontal strip:

- Display favicon + title.
- Give minimum width, padding, and some overflow behavior.
- Highlight the active tab.

### CSS changes (example)

Once you find the tab strip container and tab item classes, you can add something like:

```css
/* Tab strip container: horizontal row */
.tab-strip {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  overflow-x: auto;
  white-space: nowrap;
}

/* Individual tabs: visible, readable */
.tab {
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  min-width: 80px;
  max-width: 180px;
  height: 28px;            /* adjust to taste */
  box-sizing: border-box;
  cursor: pointer;
  border-radius: 4px;
  margin-right: 4px;
  background: rgba(255, 255, 255, 0.04);
}

/* Favicon + title */
.tab-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  flex: 0 0 auto;
}

.tab-title {
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
}

/* Active tab */
.tab.active {
  background: rgba(255, 255, 255, 0.16);
  font-weight: 600;
}
```

That pattern mirrors the way custom tab bars are hacked in Firefox/Vivaldi via CSS: horizontal flex strip, per-tab flex items with min/max width, ellipsis for long titles.[8][9][7]

If Min’s classes differ, you’d adapt `.tab-strip`, `.tab`, `.tab-icon`, `.tab-title` to whatever the code uses.

## Step 3: Ensure titles actually render

In the React/JS component that renders each tab, make sure it exposes the title text:

```jsx
<div className={`tab ${tab.isActive ? 'active' : ''}`}>
  <img className="tab-icon" src={tab.favicon} alt="" />
  <span className="tab-title">{tab.title}</span>
</div>
```

FACT: Min already tracks tab titles for history/search/bookmarks.  You just need to render them in the tab UI.[5][4]

Assumption (medium confidence): If the current UI only shows favicons, the title field is still there; it’s just not displayed to keep things minimal.

## Step 4: Handle overflow (many tabs)

You want “many tabs across the top” without them shrinking to unreadable slivers. There are two common patterns:

- **Scroll**: keep min width; use horizontal scrolling when there are too many tabs.
- **Compress**: allow flex to shrink but enforce a reasonable minimum, so you get dense tabs but still readable titles.

The CSS above already hints at scroll: `overflow-x: auto; white-space: nowrap` on the strip.[7]

You can refine with something like:

```css
.tab-strip::-webkit-scrollbar {
  height: 4px;
}

.tab-strip::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
}
```

Edge case: if you routinely run >100 tabs, you may need keyboard shortcuts or a quick tab overview anyway, which Min already supports via search.[10][4]

## Step 5: Keep Min’s minimal vibe but make it usable

If you don’t want to completely abandon Min’s aesthetic, you can:

- Only show titles on hover (e.g., default to favicon‑only, then expand the tab on hover).
- Use smaller min-width and lighter styling so tabs feel “minimal,” just not invisible.
- Add subtle active styling (border, background, bold label) like Firefox Proton custom CSS does.[9]

Example “hover expand” idea:

```css
.tab {
  min-width: 40px;
  transition: min-width 0.15s ease;
}

.tab:hover {
  min-width: 120px;
}
```

SPECULATION (medium confidence): This keeps the baseline strip compact but gives you readable text when you actually interact, balancing Min’s philosophy with your need to see more context.

## Step 6: Build and install your custom Min

Once you’re happy with the modified tab bar:

1. Run Min locally (`npm start`) and stress‑test: dozens of tabs, window resize, focus mode, tasks.[10]
2. Build a platform package (e.g., `.deb`, `.exe`) using Min’s existing build scripts:

   ```bash
   npm run build
   ```

3. Install your custom build alongside stock Min, or replace it if you’re confident.

FACT: Min already ships distro-specific packages built from the same Electron app; the same tooling can build your fork.[2][3]

## If you want this without a fork

Very speculative but possible:

- On some Electron apps, you can inject CSS via a devtools “user stylesheet” or a custom preload script.
- If Min doesn’t already support extensions or user CSS injection, you’d have to wrap it (e.g., run Min from your own Electron host and inject styles).

Given your background, the cleanest route is still: fork → small UI tweak → own build.

***

Concrete next step I’d suggest: clone the Min repo, run it in dev, and paste the tab component markup/CSS into a snippet here so we can design a precise patch against the actual class names and layout instead of me hand‑waving generic `.tab` / `.tab-strip` selectors.

If you paste that component, I can give you an exact diff (JS + CSS) that turns “favicons or minimal indicators” into a proper, readable, many‑tabs‑across‑the‑top strip with minimal UI footprint.

## Human

fuck off on the hack bullshit.  Don't be locked into one thing.  Open your mind to how we can see multiple tab indicators that I can click on to switch tabs without using the tab search?

## Assistant

You already *can* see multiple click‑able tab indicators in Min; the catch is they’re intentionally tiny and minimal, and Min’s other “overview” mechanisms are designed to replace the classic big strip.  So the question becomes: what ways of exposing more *click targets* for tabs does Min already give us, beyond the default header row and tab search?[1][2]

Below are non‑hack, “use what Min ships” ways to get more clickable tab indicators without relying on the text‑search box.

## Multiple tabs in the default header

FACT: Min’s normal mode shows multiple tabs as compact indicators in the top bar; tabs take up less space and pages that haven’t been looked at in a while fade out.[2]

If you’re only ever seeing one indicator:

- Make sure Focus Mode is off. Focus Mode hides other tabs to keep you on a single page.[2]
- Check you’re not in a single‑task with only one tab open; Min’s “tasks” are groups where only that group’s tabs are visible at a time.[1]

In the standard view:

- Each open tab appears as a small clickable region (favicon / minimal indicator).[2]
- Clicking those switches tabs immediately, no search involved.
- Faded tabs are still interactive; they’re visual de‑emphasis, not disabled.[2]

This is Min’s “multiple indicators you can click” baseline, just more compact than you’re used to.

## Using tasks to get *sets* of clickable tab indicators

FACT: Min groups tabs into “tasks,” which are collections of tabs you can switch between.[3][1]

If you have a ton of tabs, Min encourages you to:

- Create several tasks (e.g., “Project A,” “Docs,” “Random reading”).[1]
- Inside each task, you have multiple tab indicators in the header that are clickable as usual.
- Switch tasks to swap which set of tab indicators is visible.

This doesn’t give you one giant strip across *all* tasks, but it does give you:

- A manageable number of clickable indicators per task.
- Very low friction to switch context via the task view and then click the tab you want.[1]

From the article describing Min: you open the task view, see all tabs within a task, and can drag/drop tabs between tasks.  That view itself is a grid/list of tab thumbnails you can click — again, no text search needed.[1]

## Tab/task overview as a clickable grid

While Min pushes “search your tabs,” it also describes a *visual* overview:

- You can open a task view that shows all tabs in that task as cards/thumbnails.[1]
- Each card is a click target; clicking it switches to that tab.
- You can rearrange, group, and move tabs there with drag‑and‑drop.[4][1]

This behaves a lot like Safari’s Tab Overview or Chrome’s “open tabs list” — a separate space with:

- Multiple visible tab indicators at once.
- Direct clicking to switch.
- Optional search, but you don’t have to use it.  (Those are other browsers, but Min’s behavior is conceptually similar.)[5][6][7]

So, if the header bar feels too cramped, the “task view with all tabs as cards” is Min’s built‑in alternative for “show me a bunch of tabs I can click, all at once.”

## Keeping Min but avoiding the search box

Given your constraints (“no hack bullshit,” “no tab search”), realistic ways to get more clickable indicators *inside Min* are:

- Turn off Focus Mode so multiple tab indicators appear in the header.
- Use tasks aggressively so each context has a small, manageable set of clickable tab indicators.
- Use the task/tab overview screen as your “many tabs visible” surface — click cards, not text‑search.

That’s all possible without:

- Forking Min.
- Injecting custom CSS.
- Touching its internal code.

Confidence: medium. The docs/articles clearly show tasks, tab grouping, and a visual task view with clickable tabs, but Min’s exact current keyboard/mouse affordances may have evolved since those write‑ups.  The underlying model (tabs grouped into tasks, compact indicators in the header, visual overview) is consistent.[8][3][1]

Concrete next step: in your current Min session, open the task view and tell me what you see — does it show thumbnails/cards for each tab you can click, or a different layout?

## Human

show me

## Assistant

You’re right: in that screenshot there’s literally only the page title and the Min controls — no visible tab indicators at all. That’s the core of the frustration.

## What your UI is showing

From the image, I can see:[1]

- Left: Min’s “hamburger” menu and back arrow.
- Center: the page title (“Solution Review and Suggestions”).
- Right: the usual window controls and a `+` button (new tab), plus the tasks/menu icon.

There are **no** separate tab pills or icons in that header — it’s just one flat bar with the title.[1]

## How to get multiple clickable tab indicators in *this* UI

Given what Min actually renders there, there are only a few built‑in ways to have multiple things you can click to switch tabs, *without* using the text search box:

1. **Use the `+` button to create multiple tabs, then switch via the top bar**  
   When you click `+`, Min opens a new tab; Min’s design is that tabs “take up less space,” so they show as small indicators rather than full big pills.[2]
   - If Focus Mode is off, each additional tab should appear as a small clickable indicator in that same header area.[2]
   - You then click those indicators (not search) to switch tabs.

2. **Use tasks as explicit, clickable tab groups**  
   Min groups tabs into “tasks” — collections of tabs.[3][4]
   - Click the tasks/menu icon (three lines) in your screenshot.[1]
   - That opens a task view where each tab in the task is shown as a card/thumbnail you can click on to switch, which is functionally “multiple tab indicators” on screen at once.[3]
   - You can drag tabs between tasks there, again entirely by clicking, no search.[5][3]

3. **Rely on the task/tab overview as your “tab strip”**  
   Min’s philosophy is: minimal header, then a separate overview for “lots of tabs.”[4][3]
   - Instead of trying to force many indicators into the thin header, you pop the task overview and use it as a grid of clickable tabs.[3]
   - Click a card to switch; close, move, and group tabs all from there.

Given your screenshot, the immediate thing I’d do is: click that three‑line icon and confirm you’re seeing a list/grid of tabs for the current task that you can click on directly. That’s the closest Min has to “show me multiple tab indicators I can click” in one place, without involving the search field.

If you click that icon now, do you get a panel with multiple tab tiles/cards, or something different altogether?

## Human

so why do I see two tabs now?

## Assistant

You see two tabs now because Min is finally showing you what its “multi‑tab” header actually looks like: each open tab gets a horizontal label segment in that bar, and you now have two — the original page and a newly created tab.[1][2]

## What changed between the two screenshots

In the first image, there was only one page open in that task, so the header just showed the single tab’s title (“Solution Review and Suggestions”).  After you clicked `+` (or otherwise opened a new tab), Min added a second tab segment labeled “New Tab” to the right.[2][3][4][1]

So now:

- Left segment: “Solution Review and Suggestions” — that’s tab 1.
- Right segment: “New Tab” — tab 2, currently active (highlighted).[1]
- Clicking either segment switches between those tabs directly, no search.[2]

This is Min’s built‑in way of showing multiple tab indicators in the header: it only becomes visible once there’s more than one tab in the current task, which is why you didn’t see it before.[4][5]

## How to get more clickable tab indicators like this

Given what you’re seeing now:

- Every time you hit `+`, you get another labeled segment in that header for a new tab, up to whatever width constraints Min imposes.[2]
- You can keep opening tabs until the bar fills; Min will then either shrink or scroll them horizontally, but each remains a clickable indicator.[6][2]
- As long as Focus Mode is off and you stay in the same task, that header bar is your “many tabs across the top” surface.

If you want to stress‑test this, try opening 5–10 tabs in that same task and see how Min lays them out; then we can talk about how usable that layout actually feels for you.
