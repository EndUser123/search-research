---
title: "Let me know if you have any questions:

You are an expert in browser automation, Chrome/Chromium internals, and auth-sen"
date: "2026-04-23"
mode: "CONCISE"
uuid: "5d8592a3-8046-46e7-be5a-d8b1ebec822d"
entry_count: 3
---

## Human

Let me know if you have any questions:

You are an expert in browser automation, Chrome/Chromium internals, and auth-sensitive web apps. Your task is to design a robust, repeatable browser-session architecture for DOM-based readiness testing of Google NotebookLM on Windows.
Context (do not re-litigate)
We have a working CLI path for NotebookLM (using nlm) and a working readiness logging pipeline.
The only blocker is the browser/auth path used for DOM measurements: our automated browser cannot reliably reach an authenticated NotebookLM notebook UI.
Current runs land on [https://notebooklm.google.com/accessrequest/](https://notebooklm.google.com/accessrequest/)..., so all DOM-based readiness checks fail before NotebookLM’s sources view is even visible.
The test logic, timers, and CLI probes are not the problem; the blocker is Chrome session architecture under current security constraints.
Recent platform facts you should account for:
Chrome announced that --remote-debugging-port and --remote-debugging-pipe are no longer honored when debugging the default Chrome data directory, and that these switches now require --user-data-dir pointing to a non-standard directory.
This change is specifically to prevent arbitrary automation from attaching to a user’s real profile; automation is expected to use a separate profile directory with a different encryption key.
Playwright’s browserType.connect_over_cdp / connect_over_cdp() methods attach to an already running browser instance via the Chrome DevTools Protocol, and allow creating new contexts in that instance.
Developers report recurring DevToolsActivePort file doesn’t exist errors when trying to drive Chrome against specific existing profiles via Selenium and --profile-directory, especially after recent Chrome changes.
This strongly suggests that continuing to force Selenium against a cloned “real” Chrome profile is fighting the platform, not just a bug in our code.
Local project details
Platform: Windows
Chrome path: C:\Program Files\Google\Chrome\Application\chrome.exe
“Correct” human profile: Profile 2 in the real Chrome user data dir
Project root: P:\packages\yt-is
Current scripts:
P:\packages\yt-is\csf\nlm_scraper.py
P:\packages\yt-is\bin\csf-source
P:\packages\yt-is\bin\nlm-playwright
P:\packages\yt-is\csf\nlm_config.py
Current behavior:
csf-source instantiates NLMIndustrialScraper(headless=False).
Scraper tries to:
Prefer the real Chrome profile.
Resolve Chrome Local State to Profile 2.
Clone that into a dedicated Selenium profile root.
Reseed if DevToolsActivePort artifacts are present.
Tests around profile seeding/cloning pass; live NotebookLM runs still end on Request access.
What you must produce (in this order)
Primary architecture choice (one sentence, then details)
Choose a primary browser-session architecture that you believe is the best long-term fit for this situation, given current Chrome constraints and NotebookLM’s auth model. Choose between (or propose a variant of):
A. Dedicated persistent automation profile
Launch Chrome / Chrome for Testing with its own --user-data-dir (separate from the human “Profile 2”), log into Google/NotebookLM once interactively, then reuse that profile for all future DOM readiness runs.
B. Attach to an existing pre-authenticated browser via CDP
Start a browser (Chrome or Chrome for Testing) with --remote-debugging-port=9222 and a non-default --user-data-dir, log in once, then use Playwright’s connect_over_cdp (or equivalent) to attach to that running browser for each test run.
C. Something else (explain precisely).
Your answer must clearly state which option is primary and why (security constraints, stability, reproducibility, ease of implementation).
Selenium vs Playwright vs other
Given your chosen architecture, state whether:
Selenium should remain in use for DOM readiness work.
We should migrate the DOM path to Playwright (or another controller) to better support CDP attachment and persistent profiles.
Or we should adopt a hybrid model (e.g., CLI logic stays as-is, DOM path is pure Playwright).
Cite specific capabilities or limitations (e.g., how Playwright handles connect_over_cdp, how Selenium behaves with user-data-dirs and recent Chrome versions, etc.).
Concrete Windows startup / attachment flow For your chosen architecture, specify an end-to-end flow on Windows that is precise enough to implement:
How the browser is started:
exact flags (including --user-data-dir, --remote-debugging-port if applicable, and any needed disable/enable flags),
which binary (regular Chrome vs Chrome for Testing),
how not to violate Chrome’s rule about remote debugging the default data directory.
How the automation layer attaches:
for Playwright: how connect_over_cdp (or similar) is invoked, how a context and page are created, how we navigate to NotebookLM and ensure we are in the notebook UI rather than accessrequest.
for Selenium: whether we should stop trying to point it at the cloned “Profile 2” directory, and instead drive a dedicated automation profile.
The output should be something we can translate into Python or a small wrapper script with minimal ambiguity.
Account consistency with CLI Propose a strategy to keep the NotebookLM/Google account consistent across:
nlm CLI authentication (already working).
Browser automation session.
Constraints:
We accept a one-time manual login into the automation profile (e.g., open the profile once in a visible browser, authenticate, maybe accept MFA) as setup.
We do not want to perform Google sign-in flows on every test run.
We want a way to detect early if the browser is not in the expected account (or has fallen back to Request access) before we start timing DOM readiness.
If there is no clean way to “tie” the CLI token to the browser session, be explicit about that and instead define deterministic checks that the browser is in the expected account (e.g., specific DOM markers, profile avatar checks, presence/absence of accessrequest path, etc.).
Preflight checks before any readiness measurement Define a preflight handshake that must succeed before we trust DOM readiness timings, for example:
Browser navigates to a NotebookLM notebook URL.
Automation waits until:
URL is in the correct notebook route (not accessrequest),
A specific sources-panel selector is present,
And some small DOM invariant holds that would never be true on the Request access or login pages.
If preflight fails (e.g., still on accessrequest after N seconds), the run is aborted with an explicit failure mode like browser_not_authenticated, without attempting any readiness probes.
Be concrete about selectors / URL patterns / states we should check.
Minimal changes to P:\packages\yt-is Given all of the above, propose minimal, surgical changes to the existing code:
Which of these should change:
NLMIndustrialScraper construction (e.g., stop preferring the real profile; accept a dedicated automation profile root instead).
The Selenium bootstrapping logic (if kept).
The nlm-playwright wrapper.
Which tests stay valid and which assumptions in the current tests need to be updated (e.g., tests that assert we clone from Profile 2 should be replaced with tests asserting that we use an automation-specific profile and/or CDP attach).
Focus on the smallest architectural change set that gets us to a stable, authenticated DOM session.
Failure modes & monitoring Finally, describe the main failure modes for your architecture and how to detect them:
Expired Google session / logout.
NotebookLM account losing access.
Profile corruption (e.g., DevToolsActivePort or similar startup faults).
CDP attachment failure.
For each, specify:
what symptom we’d see (logs, exceptions, URLs, missing selectors),
and what explicit failure code / log message we should emit so that the readiness matrix clearly distinguishes browser auth failures from genuine readiness-signal failures.
Important non-goal for this phase
Do not spend time comparing the reliability of:
the DOM spinner/checkmark readiness signal vs
the CLI nlm source content <source_id> --json readiness signal.
Those questions are deliberately out of scope until we have a stable, authenticated NotebookLM browser session. For now we only want the best, most robust browser/auth architecture and the changes needed to implement it.

## Assistant

**Primary choice: A dedicated persistent automation profile, driven by Playwright, is the best long-term fit.** It aligns with Chrome’s post-136 security model, avoids fighting profile-encryption and default-profile protections, and is simpler to make reproducible on Windows than cloning or attaching to a real human profile.[1][2]

## Primary architecture

Chrome 136 changed remote debugging so `--remote-debugging-port` and `--remote-debugging-pipe` are no longer honored for the default Chrome data directory unless you also use `--user-data-dir` pointing to a non-standard directory. Chrome states this is intentional isolation from the real user profile and its encryption key, and explicitly recommends custom user-data directories for debugging and automation.[1]

Playwright also now warns that automating Chrome’s default user profile is not supported and may cause pages not to load or the browser to exit, and its persistent-context API is built specifically around a separate `user_data_dir` that stores cookies and local state for reuse across runs.  That makes “clone Profile 2 and hope Selenium can drive it” the wrong abstraction now: it is architecturally misaligned with the browser’s security model, even if parts of the seeding logic still pass unit tests.[2][3][1]

## Why not B as primary

Option B, CDP attach to a pre-authenticated browser, is useful as an operational variant, but not the primary architecture because Playwright documents `connect_over_cdp()` as “significantly lower fidelity” than a normal Playwright connection.  It is good for attaching to an already running browser, but worse as the main control plane if you want repeatable runs, deterministic startup, and fewer moving parts.[2]

More practically, B still requires the same non-default `--user-data-dir` to comply with Chrome’s remote-debugging rules, so it does not solve the core profile problem by itself.  It mainly adds another dependency layer, “browser already running and exposing CDP,” which is useful for debugging and manual recovery, but not necessary for the steady-state test path.[1][2]

## Controller choice

**Recommendation: use a hybrid model — keep the CLI path as-is, but make the DOM readiness path pure Playwright.** Playwright should replace Selenium for the NotebookLM browser path because it natively supports persistent contexts, clearly documents the non-default-profile requirement, and gives you cleaner primitives for strict selectors, URL waits, and early aborts before timing starts.[2]

Selenium should **not** remain the primary DOM controller for this workflow. Recent reports show `DevToolsActivePort file doesn't exist` failures around `--user-data-dir` plus `--profile-directory`, especially after Chrome 136-era changes, and the common workarounds revolve around version pinning or Chrome for Testing rather than making existing real-profile automation reliable.  That does not mean Selenium is broken everywhere, but for *this* auth-sensitive NotebookLM case, continuing to force Selenium against cloned “Profile 2” data is high-friction and low-leverage.[3][1]

## Windows startup flow

Use **one dedicated automation profile root** that is never the real Chrome user data directory, for example:

- `P:\packages\yt-is\.state\notebooklm-chrome-profile`

Use either:
- regular Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`, or
- preferably **Chrome for Testing** if you want tighter version control and less surprise from auto-updates, which Chrome explicitly recommends for browser automation scenarios.[1]

For the **primary path**, start Playwright directly with a persistent context, not by launching Chrome yourself via CDP:

```python
from playwright.sync_api import sync_playwright

PROFILE_DIR = r"P:\packages\yt-is\.state\notebooklm-chrome-profile"
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        executable_path=CHROME_EXE,
        headless=False,
        no_viewport=True,
        args=[
            "--start-maximized",
        ],
    )
    page = context.new_page()
    page.goto("https://notebooklm.google.com/")
```

This follows Playwright’s intended model: persistent storage lives in `user_data_dir`, that directory is reused, and you are **not** pointing at Chrome’s main “User Data” directory.[2]

## One-time manual login

The setup step should be explicit and separate from test runs:

1. Launch the persistent Playwright profile in headed mode.[2]
2. Manually log into the intended Google account.
3. Open NotebookLM and verify the target notebook is accessible.
4. Close the browser cleanly so session state is flushed to disk.[2]

After that, normal runs reuse the same dedicated profile and do **not** perform Google sign-in flows each time. That matches your constraint and uses the profile exactly the way Playwright persistent contexts are intended to be reused.[2]

## Optional CDP variant

If you want a manual-debug or recovery mode, keep **B as a secondary variant**, not the default. In that mode, start Chrome with a non-default profile and a debug port:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --user-data-dir="P:\packages\yt-is\.state\notebooklm-chrome-profile" `
  --remote-debugging-port=9222 `
  --no-first-run `
  --no-default-browser-check `
  --start-maximized `
  "https://notebooklm.google.com/"
```

That is compliant with Chrome’s rule because the profile is a non-standard directory, not the default Chrome data directory.  Then attach with Playwright:[1]

```python
browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
context = browser.contexts[0]
page = context.pages[0] if context.pages else context.new_page()
```

Playwright documents exactly this pattern for `connect_over_cdp()`, while also warning that CDP attachment has lower fidelity than the native Playwright protocol.[2]

## Account consistency with CLI

There is **no clean, supported way** to “bind” the `nlm` CLI auth token to the browser’s Google session so that one automatically proves the other. The CLI and browser session are separate auth surfaces unless Google explicitly exposes a shared supported mechanism, and the sources here do not indicate such a path.[1][2]

So the correct strategy is deterministic **account-state verification**, not token sharing. Use a dedicated automation browser profile that is manually authenticated to the same Google account expected by the CLI workflow, and enforce preflight checks before any DOM timing starts.[2]

Recommended deterministic checks, in order:

- The notebook URL must not redirect to `/accessrequest/`.  
- The page must not show Google sign-in UI.  
- The page must expose NotebookLM notebook UI markers, specifically a sources-region invariant you only get inside the notebook.  
- Optionally, the page title should include notebook content rather than generic access/login wording.  

Those are safer than trying to scrape avatar identity details, which tend to be brittle and privacy-sensitive. The most important invariant is “correct notebook route plus notebook-only DOM present.”[2]

## Preflight handshake

Before **any** readiness measurement, add a preflight state machine with an explicit timeout, for example 20 to 30 seconds.

Recommended preflight logic:

1. Navigate directly to the target notebook URL.
2. Wait for network settling enough to inspect the route, but do **not** start readiness timers yet.
3. Fail immediately if URL contains `/accessrequest/`.
4. Fail immediately if URL matches Google sign-in or account chooser patterns.
5. Require one notebook-only selector and one sources-panel selector.
6. Only after these succeed, start your existing readiness timers.

Concrete route checks:

- **Reject** if URL contains `notebooklm.google.com/accessrequest/`
- **Reject** if host/path suggests Google sign-in or chooser, such as `accounts.google.com` or `/signin/`
- **Accept only** if URL remains under `https://notebooklm.google.com/` and does not match the reject rules

Concrete DOM checks:

- A visible, notebook-only heading or shell container under the NotebookLM app root
- A visible sources-panel element or “Sources” label in the notebook workspace
- At least one notebook-workspace region that would not exist on access or login pages

Because NotebookLM’s internal selectors can change, prefer a layered selector strategy:

- Primary: stable ARIA roles and accessible names, e.g. `get_by_role("heading", name=/Sources/i)` or `get_by_text("Sources", exact=False)`
- Secondary: app-shell landmarks like `main`, `role=tabpanel`, `role=complementary`, or notebook workspace containers
- Tertiary: a curated CSS selector map in config, versioned and easy to update

Example preflight pseudocode:

```python
def preflight_notebook_ui(page, timeout_ms=25000):
    page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)

    url = page.url
    if "notebooklm.google.com/accessrequest/" in url:
        raise BrowserAuthError("browser_not_authorized_notebook_access")

    if "accounts.google.com" in url or "/signin" in url:
        raise BrowserAuthError("browser_not_authenticated_google_login")

    sources_heading = page.get_by_role("heading", name=re.compile(r"Sources", re.I))
    sources_text = page.get_by_text(re.compile(r"Sources", re.I))
    notebook_shell = page.locator("main")

    expect_any_visible(
        [sources_heading, sources_text],
        timeout_ms=timeout_ms
    )

    notebook_shell.wait_for(state="visible", timeout=timeout_ms)

    url = page.url
    if "accessrequest" in url:
        raise BrowserAuthError("browser_not_authorized_notebook_access")
```

The important part is not the exact selector names; it is the contract: **route check + notebook-only DOM check + sources invariant** must all pass before timing begins.[2]

## Abort behavior

If preflight fails, abort the run immediately and emit a browser/auth failure code instead of attempting readiness probes. That prevents poisoned timing data when the test never reached the notebook UI in the first place.

Recommended failure codes:

- `browser_not_authenticated_google_login`
- `browser_not_authorized_notebook_access`
- `browser_preflight_missing_notebook_ui`
- `browser_preflight_timeout`

These should be terminal for that run and clearly separated from downstream readiness-signal failures.

## Minimal code changes

The smallest stable change set is:

### `NLMIndustrialScraper`

Stop preferring the real Chrome profile and stop cloning `Profile 2`. Replace that with a required or defaulted **automation profile root** such as:

- `browser_profile_root: P:\packages\yt-is\.state\notebooklm-chrome-profile`

The constructor should accept:
- `browser_engine="playwright"`
- `browser_profile_root=...`
- `browser_executable_path=...`
- `headless=False`
- `cdp_endpoint=None` for optional attach mode

This is the single most important code change because it removes the core incorrect assumption that the “real” profile is the right source of truth for automated DOM work.[1][2]

### Selenium bootstrap

For DOM readiness work, deprecate it. If you must keep it temporarily, stop pointing it at cloned `Profile 2` and only allow it to use the dedicated automation profile root. But the preferred move is to remove Selenium from this path entirely.[3][2]

### `nlm-playwright` wrapper

Promote this wrapper to the canonical DOM-session entrypoint. It should support two modes:

- `persistent-launch` — default, launches Playwright persistent context on the dedicated profile
- `cdp-attach` — optional, attaches to an already running browser at `http://127.0.0.1:9222`

This is a small surface-area change because you already have an `nlm-playwright` wrapper; you are mainly changing its role from auxiliary to primary.

### `nlm_config.py`

Add a compact browser config block:

- `browser_mode = "persistent"` or `"cdp_attach"`
- `browser_profile_root = r"P:\packages\yt-is\.state\notebooklm-chrome-profile"`
- `browser_executable_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"`
- `browser_cdp_url = "http://127.0.0.1:9222"`
- `browser_preflight_timeout_ms = 25000`

Also add a selector map for notebook preflight so selector maintenance is centralized, not buried in scraper logic.

## Tests to keep and update

Tests around generic readiness timing logic and CLI probes should stay valid because you said those are already working and are not the blocker.

Tests that assume any of the following should be replaced:

- cloning from real Chrome `Profile 2`
- resolving Chrome `Local State` to discover the human profile
- reseeding Selenium profiles from a cloned real-profile source
- asserting Selenium bootstraps from a copied human profile

Replace them with tests asserting:

- a non-default automation profile root is used
- Playwright launches a persistent context against that directory
- preflight rejects `/accessrequest/`
- preflight rejects Google login/account-chooser routes
- readiness probes are not executed until preflight passes
- optional CDP mode attaches only to a browser using the same dedicated profile root

That keeps the change set surgical: the tests stop validating the old wrong assumption and start validating the new session contract.

## Failure modes

### Expired Google session

**Symptom:** navigation lands on Google sign-in, account chooser, or another auth interstitial instead of the notebook UI.[2]
**Detect:** URL host/path check for `accounts.google.com` or sign-in patterns; missing notebook UI selectors.  
**Emit:** `browser_not_authenticated_google_login`

### NotebookLM access lost

**Symptom:** URL lands on `/accessrequest/` for the target notebook, or notebook shell never appears and the page clearly shows access-request content.  
**Detect:** URL contains `notebooklm.google.com/accessrequest/`; notebook-specific selectors absent.  
**Emit:** `browser_not_authorized_notebook_access`

### Profile corruption or startup fault

**Symptom:** browser process exits early, persistent context launch fails, or you see startup issues analogous to the existing `DevToolsActivePort` class of failure in Chrome/Selenium ecosystems.[3]
**Detect:** Playwright launch exception, browser closes before page creation, profile lock/startup exceptions.  
**Emit:** `browser_profile_startup_failed`

### CDP attachment failure

**Symptom:** cannot connect to `http://127.0.0.1:9222`, or `browser.contexts` is empty/unusable after attach. Playwright documents the CDP connect path and its constraints.[2]
**Detect:** `connect_over_cdp()` timeout, refused connection, malformed endpoint response.  
**Emit:** `browser_cdp_attach_failed`

### Notebook UI shape drift

**Symptom:** URL is correct, but preflight selectors no longer resolve because NotebookLM UI changed.  
**Detect:** correct NotebookLM route, not access/login, but notebook-only DOM invariant missing past timeout.  
**Emit:** `browser_preflight_missing_notebook_ui`

### Slow load / transient network delay

**Symptom:** still on intermediate route or UI incomplete at timeout without definitive auth failure.  
**Detect:** no reject-route match, but no notebook shell plus no sources invariant within preflight timeout.  
**Emit:** `browser_preflight_timeout`

## Recommended implementation stance

If you want the fewest moving parts and the highest chance of stabilizing quickly, do this:

- Keep `nlm` CLI auth untouched.
- Make browser DOM work **Playwright-only**.
- Use **one dedicated persistent browser profile** on disk.
- Perform **one-time manual login** into that profile.
- Add a strict **preflight handshake** that must pass before any timing starts.
- Keep **CDP attach** only as a secondary debug/recovery mode.

That is the smallest architectural move that aligns with Chrome’s current security model and gives you a stable authenticated NotebookLM session for DOM readiness work.[1][2]

## Human

You previously recommended a specific browser-session architecture for automating NotebookLM DOM readiness tests (e.g., persistent automation profile vs CDP attach). You do not have direct access to my logs, only the description below.
Treat your previous architecture recommendation as fixed, and now do two things:
Design the implementation plan inside my repo (P:\packages\yt-is).
Design the verification strategy that does not depend on you reading my logs.
1. Restate your chosen architecture crisply
In 3–5 sentences, restate the architecture you chose in the prior answer, assuming:
Platform: Windows.
Chrome installed at C:\Program Files\Google\Chrome\Application\chrome.exe.
We are allowed to use either regular Chrome or Chrome for Testing, as long as we obey the rule that --remote-debugging-port cannot be used directly against the default data directory and must be combined with --user-data-dir pointing at a non-standard directory.
We accept a one-time manual login into the automation profile (visible browser) but we do not want to script the Google login form on every run.
Anchor this restatement around one of these patterns (or a hybrid):
Playwright launch_persistent_context with a dedicated userDataDir that we log into once and reuse.
Playwright connect_over_cdp to an already-running Chrome/Chromium instance started with --user-data-dir pointing at an automation profile and --remote-debugging-port.
A strictly better alternative compatible with current Chrome security constraints.
2. Concrete “wiring” changes inside yt-is
Without seeing the code, but given these known pieces:
P:\packages\yt-is\csf\nlm_scraper.py
P:\packages\yt-is\bin\csf-source
P:\packages\yt-is\bin\nlm-playwright
P:\packages\yt-is\csf\nlm_config.py
propose a minimal change-set that wires in your architecture. Be specific:
Where should the persistent profile path or CDP endpoint live (e.g., config key in nlm_config.py like nlm_browser_profile_root or nlm_cdp_url)?
Which component should be responsible for:
Starting the browser (if we are the one launching it).
Attaching to it (if using CDP).
Ensuring headless=False for the one-time login but headless=True for later runs.
How should NLMIndustrialScraper be constructed now? Do we:
Pass it a user_data_dir (for persistent context),
Pass it a CDP URL, or
Have it accept a generic “browser session factory” abstraction?
Give suggested function signatures / constructor parameters in pseudocode, not full code, something like:
python
class NLMIndustrialScraper:
    def __init__(self, browser_session_factory, headless: bool = True):
        ...
or
python
scraper = NLMIndustrialScraper(
    user_data_dir="P:\\packages\\yt-is\\.browser\\notebooklm",
    headless=False,
)
3. One-time login bootstrap flow (human + automation)
Design a one-time bootstrap procedure that a human can follow to create a stable, authenticated automation profile, using your chosen architecture. Assume:
Human has Python and Playwright (or Selenium) installed.
Human can run a small helper script or CLI command.
Spell out the steps, for example:
Run a helper command like ytis-nlm-browser-bootstrap which:
Launches a persistent Playwright context with user_data_dir=... and headless=False.
Opens [https://notebooklm.google.com/](https://notebooklm.google.com/).
Human logs in with the correct Google account, passes any CAPTCHA/MFA.
Once the sources UI is visible, they close the browser.
From then on, regular runs use headless=True against the same profile.
Or, if using CDP attach:
Start Chrome/Chrome for Testing manually or via script with --user-data-dir pointing at the automation directory and --remote-debugging-port=9222.
Human logs into NotebookLM in that instance.
Automation attaches to ws://127.0.0.1:9222/... on each run using connect_over_cdp.
Be very explicit about which steps are one-time and which are part of every test run.
4. Preflight DOM check (no logs required)
Define a DOM preflight check that can be implemented purely by selectors and URLs (i.e., doesn’t require you to see my logs):
URL requirements (e.g., must not contain /accessrequest/).
One or more selectors that must be present to confirm we are in the NotebookLM notebook UI with sources visible (e.g., the “Sources” panel, a known button label, or aria roles).
A timeout and behavior:
If preflight fails, we mark the run as browser_not_authenticated (or similar) and do not attempt any readiness timing.
If preflight passes, we proceed with the DOM spinner/checkmark watching.
Give this as a compact spec, e.g.:
Wait up to 60s for page.url to satisfy predicate X.
Then wait up to 15s for CSS selector Y to appear.
If either fails, emit failure code Z.
We will implement that ourselves; you just need to define the behavior precisely enough.
5. Verification strategy without log access
Since you cannot read my logs, design a black-box verification plan I can follow locally to confirm the architecture is solid. Assume I can:
Inspect stdout/stderr from csf-source / nlm-playwright.
Manually watch the visible browser once or twice.
Your verification plan should:
Start with one or two manual runs:
Run a single-source DOM readiness test with verbose logging.
Visually confirm: the browser skips Request access, lands directly on the notebook UI, and your preflight conditions pass.
Then define a small readiness matrix run (e.g., 3–5 sources) where success criteria are purely:
No browser_not_authenticated errors.
No DevToolsActivePort/startup crashes.
All failures, if any, are clearly in readiness logic, not browser auth.
You may refer to patterns from the Playwright persistent-context docs (reuse of userDataDir across runs) and general Chrome remote debugging guidance, but do not assume you can see actual logs.

## Assistant

Use **Playwright `launch_persistent_context()` with a dedicated automation `user_data_dir`** as the primary browser-session architecture on Windows, and reuse that profile across runs after a one-time visible manual login. Playwright’s persistent context is designed to store and reuse cookies and local browser state in a specified user data directory, while Chrome’s current security model requires remote debugging to use a non-default `--user-data-dir` and explicitly isolates automation from the real user profile.  If you want an emergency/debug path, keep **CDP attach as a secondary mode** only when the browser was started with a non-standard `--user-data-dir`, but do not make CDP the default control path because Playwright documents CDP attachment as lower fidelity than its normal browser control.[1][2]

## Wiring changes

The minimal repo change is to move browser-session configuration into `csf/nlm_config.py` and make `nlm_scraper.py` consume that config rather than inferring or cloning the human Chrome profile. Playwright’s persistent context wants a dedicated `user_data_dir`, and Chrome’s current rules make this separation from the default profile a first-class requirement rather than an implementation detail.[2][1]

Suggested config keys in `P:\packages\yt-is\csf\nlm_config.py`:

```python
nlm_browser_mode = "persistent"   # "persistent" | "cdp"
nlm_browser_executable = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
nlm_browser_profile_root = r"P:\packages\yt-is\.browser\notebooklm"
nlm_browser_headless = True
nlm_browser_bootstrap_headless = False
nlm_cdp_url = "http://127.0.0.1:9222"
nlm_preflight_timeout_s = 60
nlm_ui_timeout_s = 15
nlm_notebook_url = "https://notebooklm.google.com/notebook/<ID>"
```

Use absolute paths, not relative `user_data_dir` paths, because Playwright has had path-resolution issues around relative `user_data_dir` handling and the user data directory semantics are explicit in the docs.[3][1]

## Responsibilities

`bin/nlm-playwright` should become the **single browser-session entrypoint** for NotebookLM DOM work. It should own browser launch/attach, profile reuse, and the bootstrap/login helper flow, because that keeps browser-session concerns out of the timing logic and lets `csf-source` remain focused on orchestration.[1]

`csf-source` should construct the scraper with an already-decided browser mode and config, then call the same scraper API regardless of whether the underlying session comes from a persistent launch or optional CDP attach. That gives you a minimal change set now and still leaves room for a future session-factory abstraction if you need one.[1]

## Suggested interfaces

For the smallest practical change, make `NLMIndustrialScraper` accept a browser session config object rather than trying to discover or clone a real Chrome profile. A generic session factory is cleaner long-term, but a config-driven constructor is probably the least invasive change if the scraper is already the main orchestration point.

Suggested pseudocode:

```python
class NLMBrowserConfig:
    mode: str                     # "persistent" | "cdp"
    executable_path: str
    user_data_dir: str | None
    cdp_url: str | None
    headless: bool
    notebook_url: str
    preflight_timeout_s: int = 60
    ui_timeout_s: int = 15
```

```python
class NLMIndustrialScraper:
    def __init__(self, browser_cfg: NLMBrowserConfig, readiness_cfg, logger, cli_probe=None):
        ...
```

```python
scraper = NLMIndustrialScraper(
    browser_cfg=NLMBrowserConfig(
        mode="persistent",
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        user_data_dir=r"P:\packages\yt-is\.browser\notebooklm",
        cdp_url=None,
        headless=True,
        notebook_url=target_notebook_url,
    ),
    readiness_cfg=readiness_cfg,
    logger=logger,
)
```

If you want one extra layer of indirection without much extra complexity, use:

```python
class BrowserSessionFactory:
    def open_page(self, url: str, headless: bool): ...
```

```python
class NLMIndustrialScraper:
    def __init__(self, browser_session_factory, readiness_cfg, logger):
        ...
```

But unless you already have multiple browser backends in flight, the config-object version is the more surgical change.

## File-by-file plan

### `csf/nlm_config.py`

Add the browser-session keys above and remove any config assumptions that the “correct” path is the human Chrome `Profile 2`. Chrome’s current behavior is intentionally hostile to remote-debugging the default profile, so keeping that assumption in config will keep leaking bad architecture into the codebase.[2]

### `bin/nlm-playwright`

This should expose two subcommands or modes:

- `bootstrap`: launch persistent Playwright context with `headless=False`
- `run`: launch persistent Playwright context with `headless=True`
- optional `attach`: CDP attach to `nlm_cdp_url`

Suggested shape:

```python
nlm-playwright bootstrap --profile "P:\packages\yt-is\.browser\notebooklm"
nlm-playwright run --profile "P:\packages\yt-is\.browser\notebooklm" --url "<notebook-url>"
nlm-playwright attach --cdp-url "http://127.0.0.1:9222" --url "<notebook-url>"
```

Playwright’s persistent context model is exactly the right primitive here because it stores cookies and local state under `user_data_dir` and reuses them on later runs.[1]

### `csf/nlm_scraper.py`

Remove or deprecate logic that:
- prefers the real Chrome profile,
- resolves `Local State` to `Profile 2`,
- clones the human profile into a Selenium directory,
- reseeds based on `DevToolsActivePort` artifacts.

Instead:
- create or receive an `NLMBrowserConfig`,
- call a `PlaywrightSession.open(browser_cfg)` helper,
- run preflight,
- only then start the readiness watchers.

This is the real architectural cutover: the scraper stops being a profile-cloning tool and becomes a NotebookLM UI observer.

### `bin/csf-source`

Change construction from “instantiate scraper that finds Chrome/profile itself” to “read browser config, create scraper with browser config, execute run.” That makes the orchestration explicit and testable.

Suggested pseudocode:

```python
cfg = load_nlm_config()
browser_cfg = NLMBrowserConfig.from_cfg(cfg, headless=runtime_headless)
scraper = NLMIndustrialScraper(browser_cfg=browser_cfg, readiness_cfg=..., logger=logger)
result = scraper.run_source_measurement(source_id=...)
```

## Headless policy

The one-time bootstrap command must force `headless=False` so the human can log into Google and NotebookLM. Regular runs should default to `headless=True`, but keep an override so you can run headed during verification or incidents. Playwright supports both headed and headless launches off the same persistent `user_data_dir`, so you do not need separate profile-management logic for those modes.[1]

## One-time bootstrap

The bootstrap should be a dedicated, human-run command, not a hidden branch in the normal readiness path. The goal is to create the automation profile once, authenticate it once, confirm NotebookLM access once, and then never script the Google login form on routine runs.

Recommended one-time flow:

1. Run a helper such as:
   ```powershell
   P:\packages\yt-is\bin\nlm-playwright bootstrap
   ```
2. That command launches Playwright with:
   - `launch_persistent_context`
   - `user_data_dir=P:\packages\yt-is\.browser\notebooklm`
   - `executable_path=C:\Program Files\Google\Chrome\Application\chrome.exe`
   - `headless=False`[1]
3. It opens `https://notebooklm.google.com/` or a known target notebook URL.
4. The human logs in with the correct Google account, completes MFA/CAPTCHA if prompted, and manually confirms the NotebookLM notebook opens normally.
5. The human closes the browser window cleanly.
6. From that point on, all routine DOM readiness runs reuse the same `user_data_dir` with `headless=True`.[1]

That split matters: only step 1–5 are one-time bootstrap; normal runs should never attempt interactive Google login.

## Optional CDP bootstrap

If you keep CDP as a fallback/debug mode, the bootstrap is similar but with a manually launched Chrome instance that uses a non-default profile directory plus a remote debugging port. Chrome requires the `--user-data-dir` non-standard directory for this debugging scenario on current versions.[2]

Example bootstrap launch:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --user-data-dir="P:\packages\yt-is\.browser\notebooklm" `
  --remote-debugging-port=9222 `
  --no-first-run `
  --no-default-browser-check `
  --start-maximized `
  "https://notebooklm.google.com/"
```

Then the human logs in once, closes Chrome, and later automation attaches via Playwright `connect_over_cdp("http://127.0.0.1:9222")` only when that browser is already running. Chrome’s non-default-profile requirement still applies, and Playwright notes CDP is lower fidelity than its primary protocol, which is why this should stay secondary.[2][1]

## Preflight spec

Define preflight as a hard gate before any readiness timer starts. The scraper should navigate to the notebook URL, validate that the route is not an auth/access detour, and require notebook-only DOM markers that indicate the sources area is actually visible.

Compact spec:

1. **Navigate** to the target notebook URL.
2. **Wait up to 60s** for `page.url` to satisfy:
   - starts with `https://notebooklm.google.com/`
   - does **not** contain `/accessrequest/`
   - does **not** contain `accounts.google.com`
3. If URL contains `/accessrequest/` at any point in this window, fail with:
   - `browser_not_authorized`
4. If URL lands on Google sign-in/account chooser at any point, fail with:
   - `browser_not_authenticated`
5. Once URL predicate passes, **wait up to 15s** for both:
   - a visible text/role match for `Sources`
   - a visible notebook workspace container such as `main`, plus at least one actionable control inside it

Suggested selector strategy, in priority order:
- `get_by_role("heading", name=/Sources/i)`
- `get_by_text(/Sources/i)`
- `locator("main")`
- an additional control such as a visible button in the notebook UI, e.g. Add source / chat / studio-related control, depending on what is most stable in your environment

Preflight passes only if:
- URL predicate passes, and
- `Sources` is visible, and
- notebook workspace container is visible.

If any condition fails:
- emit `browser_preflight_failed` plus a subtype (`browser_not_authenticated`, `browser_not_authorized`, `browser_ui_not_ready`)
- do **not** run spinner/checkmark readiness timing.

Because NotebookLM UI labels can drift, implement selectors as a configurable ordered list in `nlm_config.py` rather than hardcoding a single brittle CSS selector in scraper logic.

## Verification plan

You do not need me to read logs to verify the architecture. The point is to validate it as a black box: the browser should repeatedly arrive at the right authenticated NotebookLM UI without access redirects or startup-profile failures, and the readiness layer should only run after preflight passes.

### Manual verification run 1

Run the bootstrap once in visible mode. Success means:
- browser opens with the dedicated automation profile,
- human logs in,
- NotebookLM opens,
- no `Request access` page appears for the target notebook,
- closing the browser completes without obvious profile/startup faults.

That confirms the profile can hold an authenticated session.

### Manual verification run 2

Run one single-source DOM readiness test in **headed** mode with verbose stdout/stderr. Success means:
- browser launches directly into the existing authenticated state,
- navigation skips Google login and skips `/accessrequest/`,
- notebook UI becomes visible,
- your preflight succeeds,
- only after that do the spinner/checkmark watchers begin.

The key human-visible check is simple: you should see the actual notebook UI and sources area, not a login or request-access interstitial.

## Small matrix run

After the two manual runs, run a 3–5 source readiness matrix with normal automation settings. Success criteria should be evaluated purely as black-box outcomes:

- zero `browser_not_authenticated`
- zero `browser_not_authorized`
- zero startup/profile failures such as browser crash before page attach
- zero CDP attach failures if you are not in CDP mode
- any remaining failures must clearly belong to readiness logic, selector drift, or NotebookLM content behavior rather than browser auth/session establishment

This verification style matches the architecture: Playwright’s persistent context is meant to reuse state from `user_data_dir`, and Chrome’s policy requires automation/debugging to be separated from the default profile via a non-standard user data directory.[2][1]

## What to treat as a regression

Treat any of the following as proof the browser-session architecture is still wrong or has regressed:

- code path still tries to resolve or clone `Profile 2`
- a normal run opens Google sign-in instead of the notebook
- a normal run lands on `/accessrequest/`
- browser only works when you manually use your real daily profile
- CDP is required for all runs, rather than optional
- headed bootstrap works once, but the next headless run loses auth immediately

Those symptoms all indicate the automation session is not actually reusing the intended dedicated profile correctly.

## Test updates

Keep tests around generic readiness timing and CLI behavior. Replace tests whose assumptions are tied to cloning or seeding from the human Chrome profile with tests that assert:
- a dedicated automation `user_data_dir` is configured,
- Playwright persistent context is opened with that directory,
- preflight rejects auth/access detours,
- readiness timing does not start before preflight passes.

That gives you a smaller, architecture-aligned test surface and avoids continuing to validate a design Chrome is actively pushing you away from.[2][1]

## Human

You previously recommended a specific browser-session architecture for automating NotebookLM DOM readiness tests (e.g., persistent automation profile vs CDP attach). You do not have direct access to my logs, only the description below.
Treat your previous architecture recommendation as fixed, and now do two things:
Design the implementation plan inside my repo (P:\packages\yt-is).
Design the verification strategy that does not depend on you reading my logs.
1. Restate your chosen architecture crisply
In 3–5 sentences, restate the architecture you chose in the prior answer, assuming:
Platform: Windows.
Chrome installed at C:\Program Files\Google\Chrome\Application\chrome.exe.
We are allowed to use either regular Chrome or Chrome for Testing, as long as we obey the rule that --remote-debugging-port cannot be used directly against the default data directory and must be combined with --user-data-dir pointing at a non-standard directory.
We accept a one-time manual login into the automation profile (visible browser) but we do not want to script the Google login form on every run.
Anchor this restatement around one of these patterns (or a hybrid):
Playwright launch_persistent_context with a dedicated userDataDir that we log into once and reuse.
Playwright connect_over_cdp to an already-running Chrome/Chromium instance started with --user-data-dir pointing at an automation profile and --remote-debugging-port.
A strictly better alternative compatible with current Chrome security constraints.
2. Concrete “wiring” changes inside yt-is
Without seeing the code, but given these known pieces:
P:\packages\yt-is\csf\nlm_scraper.py
P:\packages\yt-is\bin\csf-source
P:\packages\yt-is\bin\nlm-playwright
P:\packages\yt-is\csf\nlm_config.py
propose a minimal change-set that wires in your architecture. Be specific:
Where should the persistent profile path or CDP endpoint live (e.g., config key in nlm_config.py like nlm_browser_profile_root or nlm_cdp_url)?
Which component should be responsible for:
Starting the browser (if we are the one launching it).
Attaching to it (if using CDP).
Ensuring headless=False for the one-time login but headless=True for later runs.
How should NLMIndustrialScraper be constructed now? Do we:
Pass it a user_data_dir (for persistent context),
Pass it a CDP URL, or
Have it accept a generic “browser session factory” abstraction?
Give suggested function signatures / constructor parameters in pseudocode, not full code, something like:
python
class NLMIndustrialScraper:
    def __init__(self, browser_session_factory, headless: bool = True):
        ...
or
python
scraper = NLMIndustrialScraper(
    user_data_dir="P:\\packages\\yt-is\\.browser\\notebooklm",
    headless=False,
)
3. One-time login bootstrap flow (human + automation)
Design a one-time bootstrap procedure that a human can follow to create a stable, authenticated automation profile, using your chosen architecture. Assume:
Human has Python and Playwright (or Selenium) installed.
Human can run a small helper script or CLI command.
Spell out the steps, for example:
Run a helper command like ytis-nlm-browser-bootstrap which:
Launches a persistent Playwright context with user_data_dir=... and headless=False.
Opens [https://notebooklm.google.com/](https://notebooklm.google.com/).
Human logs in with the correct Google account, passes any CAPTCHA/MFA.
Once the sources UI is visible, they close the browser.
From then on, regular runs use headless=True against the same profile.
Or, if using CDP attach:
Start Chrome/Chrome for Testing manually or via script with --user-data-dir pointing at the automation directory and --remote-debugging-port=9222.
Human logs into NotebookLM in that instance.
Automation attaches to ws://127.0.0.1:9222/... on each run using connect_over_cdp.
Be very explicit about which steps are one-time and which are part of every test run.
4. Preflight DOM check (no logs required)
Define a DOM preflight check that can be implemented purely by selectors and URLs (i.e., doesn’t require you to see my logs):
URL requirements (e.g., must not contain /accessrequest/).
One or more selectors that must be present to confirm we are in the NotebookLM notebook UI with sources visible (e.g., the “Sources” panel, a known button label, or aria roles).
A timeout and behavior:
If preflight fails, we mark the run as browser_not_authenticated (or similar) and do not attempt any readiness timing.
If preflight passes, we proceed with the DOM spinner/checkmark watching.
Give this as a compact spec, e.g.:
Wait up to 60s for page.url to satisfy predicate X.
Then wait up to 15s for CSS selector Y to appear.
If either fails, emit failure code Z.
We will implement that ourselves; you just need to define the behavior precisely enough.
5. Verification strategy without log access
Since you cannot read my logs, design a black-box verification plan I can follow locally to confirm the architecture is solid. Assume I can:
Inspect stdout/stderr from csf-source / nlm-playwright.
Manually watch the visible browser once or twice.
Your verification plan should:
Start with one or two manual runs:
Run a single-source DOM readiness test with verbose logging.
Visually confirm: the browser skips Request access, lands directly on the notebook UI, and your preflight conditions pass.
Then define a small readiness matrix run (e.g., 3–5 sources) where success criteria are purely:
No browser_not_authenticated errors.
No DevToolsActivePort/startup crashes.
All failures, if any, are clearly in readiness logic, not browser auth.
You may refer to patterns from the Playwright persistent-context docs (reuse of userDataDir across runs) and general Chrome remote debugging guidance, but do not assume you can see actual logs.

## Assistant

**Chosen architecture: Playwright persistent context with a dedicated automation profile is the primary path; CDP attach is optional fallback/debug only.** On Windows, launch Chrome or Chrome for Testing through Playwright `launch_persistent_context(user_data_dir=...)` using a non-default profile directory, perform a one-time manual NotebookLM/Google login in a visible browser, then reuse that same profile for all later DOM runs. Playwright explicitly supports persistent session state in `user_data_dir`, and Chrome 136+ explicitly requires `--remote-debugging-port`/`--remote-debugging-pipe` to be paired with `--user-data-dir` pointing to a non-standard directory when debugging, precisely to avoid attaching to the real default profile.  If you keep CDP at all, use it only against a browser already started with that same dedicated automation profile; Playwright warns that `connect_over_cdp()` is lower fidelity than its primary control path.[1][2]

## Repo wiring

The minimal change-set is: move browser-session ownership into `bin/nlm-playwright`, move browser-session config into `csf/nlm_config.py`, and make `NLMIndustrialScraper` consume an explicit browser config instead of trying to discover, clone, or reseed the human Chrome profile. Playwright warns that automating Chrome’s default user profile is not supported and may cause pages not to load or the browser to exit, so any code path that still prefers the real Chrome “User Data/Profile 2” is now an architectural liability, not a convenience.[1]

### `csf/nlm_config.py`

Add an explicit NotebookLM browser block:

```python
nlm_browser_mode = "persistent"   # "persistent" | "cdp"
nlm_browser_executable = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
nlm_browser_channel = "chrome"    # optional if not using executable_path
nlm_browser_profile_root = r"P:\packages\yt-is\.browser\notebooklm"
nlm_cdp_url = "http://127.0.0.1:9222"
nlm_browser_headless_default = True
nlm_browser_headed_bootstrap = False   # config default; bootstrap command overrides to True/visible
nlm_browser_start_timeout_ms = 30000
nlm_preflight_url_timeout_ms = 60000
nlm_preflight_ui_timeout_ms = 15000
nlm_notebook_url = "https://notebooklm.google.com/notebook/<NOTEBOOK_ID>"
nlm_notebook_sources_selectors = [
    {"type": "role_heading", "name_regex": r"Sources"},
    {"type": "text", "regex": r"Sources"},
]
nlm_notebook_shell_selectors = [
    {"type": "css", "value": "main"},
]
```

These keys should be the single source of truth for:
- automation profile path,
- executable path or browser channel,
- persistent vs CDP mode,
- headless policy,
- preflight policy.

### `bin/nlm-playwright`

Make this the canonical browser-session helper. Its responsibilities should be:

- Start browser for persistent mode.
- Attach browser for CDP mode.
- Expose a bootstrap command that forces headed mode for one-time login.
- Expose a run command for normal test execution.

Suggested CLI surface:

```powershell
bin\nlm-playwright bootstrap
bin\nlm-playwright run --url "<notebook-url>"
bin\nlm-playwright run --headed --url "<notebook-url>"
bin\nlm-playwright attach --cdp-url "http://127.0.0.1:9222" --url "<notebook-url>"
```

This is the smallest clean split because `csf-source` stays orchestration-focused while `nlm-playwright` becomes the one place that knows how NotebookLM browser sessions are created.

### `csf/nlm_scraper.py`

Change the scraper so it no longer owns profile discovery/cloning. Instead it should accept a browser-session config or session factory and ask for a live page/context. The scraper should own:
- navigation to the notebook,
- DOM preflight,
- readiness watchers,
- failure-code mapping.

It should not own:
- cloning from Profile 2,
- Chrome `Local State` lookup,
- reseeding browser directories,
- Selenium-specific profile bootstrapping.

### `bin/csf-source`

Change it to:
1. load config from `nlm_config.py`,
2. construct browser/session config,
3. construct scraper with that config,
4. run one measurement.

That moves browser setup from implicit side effects to explicit wiring.

## Suggested interfaces

For a minimal surgical change, use an explicit config object, not a deep abstraction hierarchy.

```python
class NLMBrowserConfig:
    mode: str                    # "persistent" | "cdp"
    executable_path: str | None
    channel: str | None
    user_data_dir: str | None
    cdp_url: str | None
    headless: bool
    start_timeout_ms: int
    preflight_url_timeout_ms: int
    preflight_ui_timeout_ms: int
```

```python
class NLMIndustrialScraper:
    def __init__(
        self,
        browser_cfg: NLMBrowserConfig,
        notebook_url: str,
        readiness_cfg,
        logger,
    ):
        ...
```

```python
scraper = NLMIndustrialScraper(
    browser_cfg=NLMBrowserConfig(
        mode="persistent",
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        channel=None,
        user_data_dir=r"P:\packages\yt-is\.browser\notebooklm",
        cdp_url=None,
        headless=True,
        start_timeout_ms=30000,
        preflight_url_timeout_ms=60000,
        preflight_ui_timeout_ms=15000,
    ),
    notebook_url=target_notebook_url,
    readiness_cfg=readiness_cfg,
    logger=logger,
)
```

If you want slightly cleaner separation, use a thin factory:

```python
class BrowserSessionFactory:
    def open(self, browser_cfg: NLMBrowserConfig):
        # returns (playwright, browser_or_context, context, page)
        ...
```

```python
class NLMIndustrialScraper:
    def __init__(self, browser_session_factory, browser_cfg, notebook_url, readiness_cfg, logger):
        ...
```

But I would not start there unless the scraper already supports multiple backends. The config-object route is the smallest change.

## Ownership rules

### Browser start

`bin/nlm-playwright` should start the browser in persistent mode via `launch_persistent_context(user_data_dir=...)`. Playwright documents that `launch_persistent_context` launches a browser using persistent storage located at `user_data_dir` and returns the only context, which is exactly the behavior you want for reusable NotebookLM auth state.[1]

### CDP attach

If you keep CDP mode, `bin/nlm-playwright` should attach using `connect_over_cdp(cdp_url)`. Playwright documents that this attaches to an existing Chromium-based browser instance and exposes the default context through `browser.contexts`, but also warns that this connection is significantly lower fidelity than the normal Playwright connection.[1]

### Headless policy

- `bootstrap` command: force `headless=False`
- normal `run`: default `headless=True`
- optional `--headed` override for debugging/verifying

Playwright supports both headed and headless launch options on persistent contexts, so you do not need separate profile-management code for these modes.[1]

## One-time bootstrap

This is a one-time human procedure to create and validate the dedicated automation profile.

### One-time only steps

1. Create the automation profile directory, e.g.:
   - `P:\packages\yt-is\.browser\notebooklm`
2. Run:
   ```powershell
   bin\nlm-playwright bootstrap
   ```
3. The helper launches Playwright persistent context with:
   - `user_data_dir=P:\packages\yt-is\.browser\notebooklm`
   - `executable_path=C:\Program Files\Google\Chrome\Application\chrome.exe`
   - `headless=False`
   - target URL `https://notebooklm.google.com/` or a known notebook URL[1]
4. Human logs into Google using the intended NotebookLM account, completes MFA/CAPTCHA if needed, and navigates until the actual notebook UI with sources is visible.
5. Human closes the browser cleanly.

After that, the profile on disk contains the browser session state Playwright is designed to reuse.[1]

### Every-run steps

1. `csf-source` loads config and constructs `NLMIndustrialScraper`.
2. Scraper opens browser via persistent Playwright session using the same `user_data_dir`.
3. Scraper navigates directly to the notebook URL.
4. Scraper runs preflight.
5. Only if preflight passes does readiness timing begin.
6. Browser/context closes cleanly at the end.

That split is important: **manual login is one-time; normal runs never script the Google login form.**

## Optional CDP fallback

If you need a manual-debug or incident-recovery mode, keep a secondary flow:

### One-time or ad hoc manual start

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --user-data-dir="P:\packages\yt-is\.browser\notebooklm" `
  --remote-debugging-port=9222 `
  --no-first-run `
  --no-default-browser-check `
  "https://notebooklm.google.com/"
```

Chrome’s March 2025 guidance says `--remote-debugging-port` and `--remote-debugging-pipe` are no longer respected for the default Chrome data directory and must be accompanied by `--user-data-dir` pointing to a non-standard directory.[2]

### Attach flow

Then automation does:

```python
browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
default_context = browser.contexts[0]
page = default_context.pages[0] if default_context.pages else default_context.new_page()
```

Playwright documents exactly that pattern, but also warns it is lower fidelity than normal Playwright control, so this should stay fallback-only.[1]

## Preflight spec

Define preflight as a hard gate with explicit failure codes. No readiness timing starts until preflight succeeds.

### URL phase

Wait up to **60 seconds** for `page.url` to satisfy all of:

- starts with `https://notebooklm.google.com/`
- does **not** contain `/accessrequest/`
- host is **not** `accounts.google.com`
- path does **not** indicate sign-in or account chooser

Immediate failures:
- if URL contains `/accessrequest/` -> `browser_not_authorized`
- if URL is on `accounts.google.com` or sign-in chooser -> `browser_not_authenticated`

### UI phase

After URL phase passes, wait up to **15 seconds** for both of:

- one “Sources” marker is visible:
  - Playwright locator strategy, in order:
    - `get_by_role("heading", name=/Sources/i)`
    - `get_by_text(/Sources/i)`
- one notebook shell marker is visible:
  - `locator("main")`
  - plus at least one visible interactive control inside notebook UI, such as a button or tab in the notebook workspace

### Pass/fail behavior

- If URL phase fails -> emit one of:
  - `browser_not_authenticated`
  - `browser_not_authorized`
  - `browser_preflight_timeout_url`
- If UI phase fails -> emit:
  - `browser_ui_not_ready`
- In all preflight failure cases:
  - abort run,
  - do not attempt any DOM readiness timing,
  - classify result as browser/auth/session failure, not readiness failure.

Compact implementation spec:

```text
1. goto(target_notebook_url)
2. wait <= 60s for url predicate:
   - notebooklm.google.com
   - not /accessrequest/
   - not accounts.google.com
3. if /accessrequest/ => browser_not_authorized
4. if accounts.google.com or signin route => browser_not_authenticated
5. wait <= 15s for visible "Sources" marker and visible main notebook shell
6. if missing => browser_ui_not_ready
7. only then start spinner/checkmark watchers
```

## Verification plan

Because I cannot inspect your logs directly, validate the architecture as a black box: repeated runs must reach the authenticated NotebookLM UI with the dedicated automation profile, preflight must pass before timing starts, and any remaining failures must be downstream readiness issues rather than browser/auth problems.

### Manual verification 1: bootstrap

Run the one-time bootstrap helper in headed mode. Success criteria:

- Chrome opens using the dedicated automation profile, not your daily profile.
- You can manually log into the correct Google account.
- You can open the target NotebookLM notebook.
- You do **not** see `Request access`.
- Closing the browser completes cleanly.

This verifies the profile can hold the authenticated state.

### Manual verification 2: single-source headed run

Run one single-source DOM readiness test in headed mode with verbose stdout/stderr. Success criteria:

- browser launches without startup/profile crash,
- it lands directly in the notebook flow, not Google sign-in,
- it does not redirect to `/accessrequest/`,
- your preflight conditions pass,
- only after preflight passes do readiness watchers begin.

The crucial visual assertion is: you should see the actual notebook UI with sources visible before any readiness timing is considered valid.

### Matrix verification: 3–5 sources

Run a small readiness matrix, ideally 3–5 sources. Success criteria:

- zero `browser_not_authenticated`
- zero `browser_not_authorized`
- zero startup failures such as browser process exit before context/page is usable
- zero CDP attach failures if you are using persistent mode only
- any failures that remain are clearly readiness-signal issues, selector drift, or notebook-content timing issues, not browser-session establishment failures

This matches the expected behavior of Playwright persistent contexts, which are intended to reuse browser session data in the specified `user_data_dir` across runs.[1]

## What counts as regression

Treat any of these as architectural regressions:

- code still tries to resolve Chrome `Local State` and clone `Profile 2`
- normal run lands on Google sign-in
- normal run lands on `/accessrequest/`
- run succeeds only if you manually keep your real Chrome profile open
- `DevToolsActivePort`-style startup failures remain common because you are still trying to drive a copied human profile
- preflight is bypassed and readiness timers start on access/login pages

If you see those, the new architecture is not actually wired through end-to-end.

## Minimal test changes

Keep tests for:
- readiness timing logic,
- CLI probe logic,
- result serialization.

Replace tests that assert:
- real-profile discovery,
- `Profile 2` cloning,
- Selenium reseeding from cloned human profile.

Add tests that assert:
- a dedicated automation `user_data_dir` is required in persistent mode,
- scraper receives explicit browser config,
- preflight rejects `/accessrequest/`,
- preflight rejects sign-in routes,
- readiness timing starts only after preflight success.

That is the smallest test rewrite that validates the new session contract instead of the old, now-hostile profile model.
