---
title: "how can I download sources from notebooklm?"
date: "2026-04-12"
mode: "COPILOT"
uuid: "6bc7a926-7818-4a0f-9cd1-8aaf9f44b475"
entry_count: 14
---

## Human

how can I download sources from notebooklm?

## Assistant

NotebookLM doesn't have a direct "download sources" feature built into the interface, but there are several effective methods depending on what you need:[1]

## Primary Methods

**Google Takeout (Official Export)**
Use Google Takeout at https://takeout.google.com to export all your NotebookLM data, including sources as HTML files within a zipped archive—this captures notebooks and their complete source content.[2][1]

**Chrome Extension: NotebookLM Sources Exporter**
Install the "NotebookLM Sources Exporter" from the Chrome Web Store to extract and download all sources as clean markdown files directly from your notebook with one click.  This is the most streamlined approach for quick access to individual sources without processing archives.[3]

**Manual Export via Browser**
Open each source document individually within NotebookLM's source viewer, then copy and paste the content into your preferred editor (Google Docs, Word, etc.) or save as PDF via your browser's print function.[4]

## Important Limitation

NotebookLM stores static snapshots of your sources—changes to original files don't automatically update your snapshots, and there's no native UI option to re-download individual source files after they've been uploaded.  If you need the original files, you'll need to retrieve them from their source (Google Drive, cloud storage, etc.) separately.[4]

For your workflow, the **Chrome extension** is likely the fastest for bulk markdown exports, while **Google Takeout** is the most authoritative if you need comprehensive archival of everything including chat history and generated content.

## Human

what about with python?

## Assistant

There's no official NotebookLM API for source downloads, but **notebooklm-py** is the most robust Python solution.[1][2]

## notebooklm-py (Recommended)

This is an unofficial Python SDK that reverse-engineered NotebookLM's internal RPCs (Protobufs) to provide direct API access without browser automation.  Key features:[2]

- Direct backend API calls (no Selenium/Playwright overhead)
- List and export sources programmatically
- Authentication only needed once via browser
- Supports batch operations and multiple export formats
- Installable via pip from GitHub[1]

GitHub repository: `teng-lin/notebooklm-py` with full documentation at `docs/python-api.md`[3]

## Alternative Approaches

**Apify Actor (Cloud-Based)**
The "NotebookLM API" actor on Apify exports notebooks programmatically with source metadata, URLs, and citations as JSON, CSV, Markdown, or Excel—useful if you want a hosted solution for n8n workflows or RAG pipelines.[4]

**Playwright Browser Automation**
For simpler needs, Playwright-based scripts can automate source extraction by simulating user interactions, though slower than direct API calls.  This approach is more fragile when NotebookLM's UI changes.[5][2]

**HTML Parsing from Exported Data**
Use Google Takeout (as mentioned earlier) and parse the resulting HTML files with BeautifulSoup or similar libraries to extract structured source content.[6]

For your use case as a solution architect, **notebooklm-py** gives you the most control and reliability for pipeline automation—it supports both CLI and programmatic access, making it agent-ready for multi-step workflows.

## Human

I didn't see an exposed sources download feature.  I might have missed it.

## Assistant

You're correct—NotebookLM's official UI **does not expose a direct sources download feature**.  The official support documentation covers adding and managing sources, but provides no export/download UI option for sources themselves.[1]

## What's Actually Available in UI

The closest built-in options are:

**Source Viewer & Summaries**
You can open individual sources within NotebookLM's source viewer panel and view auto-generated summaries, but there's no export button—you'd need to manually copy and paste content.[1]

**Re-sync for Google Drive Sources**
For Google Docs, Sheets, or Slides sources, NotebookLM shows a "Click to sync with Google Drive" button if the original file changed, but this syncs *into* NotebookLM, not out—the original files remain in Drive.[1]

**Google Takeout (Indirect Export)**
Google Takeout at https://takeout.google.com can export all your NotebookLM data including source snapshots as HTML within an archive, but it's not a purpose-built sources download tool.[1]

## Python Solutions (Workarounds)

**notebooklm-py** fills this gap with `client.sources.get_fulltext()`, which retrieves the indexed text content NotebookLM stored for each source.  This is effectively the source data as NotebookLM sees it:[2]

```python
fulltext = await client.sources.get_fulltext(notebook_id, source_id)
print(fulltext.content)  # Full indexed text
```

You can also list and access source metadata programmatically:[2]

```python
sources = await client.sources.list(notebook_id)
for src in sources:
    print(f"{src.id}: {src.title} ({src.kind})")
```

**Summary:** NotebookLM doesn't expose source downloads in its UI by design—sources are stored as static snapshots and treated as read-only archives. The Python SDK (`notebooklm-py`) is the most practical programmatic alternative for extracting indexed content.

## Human

PS P:\\> pip install "notebooklm-py[browser]"
Defaulting to user installation because normal site-packages is not writeable

## Assistant

That permission error indicates your Python site-packages directory isn't writable for the current user. Here are your options:

## Quick Fixes

**1. Use `--user` flag (Already Applied)**
Your pip is already defaulting to user installation (`~/.local/lib/pythonX.X/site-packages`), which should work. If it's still failing, the user directory itself may lack write permissions. Run:

```powershell
pip install --user "notebooklm-py[browser]" --verbose
```

The `--verbose` flag will show exactly where it's trying to write and what permission error occurs.

**2. Use a Virtual Environment (Recommended)**
Create an isolated environment where you have full write permissions:

```powershell
python -m venv nlm_env
.\nlm_env\Scripts\Activate.ps1
pip install "notebooklm-py[browser]"
```

This creates a local venv in your project directory with no permission issues—ideal for your multi-terminal workflow.

**3. Elevate to Admin (Last Resort)**
Run PowerShell as Administrator and retry:

```powershell
pip install "notebooklm-py[browser]"
```

**Warning:** Don't use `sudo` on Windows; use "Run as Administrator" instead.

## Diagnose the Root Issue

Check your Python installation:

```powershell
python -m site
# Shows all site-packages paths and which are writable
```

**Most Likely Cause:** Your global site-packages is managed by system or enterprise policy (common in corporate/managed Windows setups). Virtual environments bypass this entirely.

Which approach are you leaning toward—venv or checking what's blocking the user installation?

## Human

Seems to hang here:

PowerShell 7.6.0
PS P:\\> pip install --user "notebooklm-py[browser]" --verbose
Using pip 26.0.1 from C:\\Users\\brsth\\AppData\\Roaming\\Python\\Python314\\site-packages\\pip (python 3.14)

## Assistant

The pip command is hanging after printing the version info—it's stuck during dependency resolution or network I/O. This is common with `notebooklm-py[browser]` since the `browser` extra pulls in Playwright and its dependencies, which can trigger long downloads.

## Immediate Actions

**1. Check Network/Firewall**
The hang likely indicates a stalled network request. Try a simpler install first:

```powershell
pip install --user notebooklm-py --verbose
```

Install without the `[browser]` extra to isolate whether Playwright is the culprit. If that succeeds, you can add browser support later.

**2. Add Explicit Timeout**
```powershell
pip install --user "notebooklm-py[browser]" --default-timeout=60 --retries=3 --verbose
```

**3. Specify PyPI Index Explicitly**
```powershell
pip install --user "notebooklm-py[browser]" -i https://pypi.org/simple/ --verbose
```

Sometimes the default index resolution stalls.

**4. Force Kill & Retry**
If it's been hanging >30 seconds:
- Press `Ctrl+C` to interrupt
- Wait 5 seconds
- Retry with `--no-cache-dir` to skip cached metadata:

```powershell
pip install --user "notebooklm-py[browser]" --no-cache-dir --verbose
```

## Root Cause Hypothesis

Since you're on Windows 11 with PowerShell 7.6, corporate proxy/firewall or antivirus software intercepting PyPI downloads is possible. Check your proxy settings:

```powershell
pip config list
```

If you see proxy entries, that might be the culprit. What happens if you interrupt and try the version without `[browser]`?

## Human

PowerShell 7.6.0
PS P:\\> pip config list
PS P:\\>

## Assistant

No proxy configured, so that's not the issue. The hang is likely during the initial dependency resolution phase before any actual downloads start.

## Next Diagnostic Steps

**1. Try Installing Without `[browser]`**
```powershell
pip install --user notebooklm-py --no-cache-dir -vv
```

Use `-vv` (double verbose) for more detailed output. This tests if the base package resolves without Playwright blocking.

**2. Check if pip is Stuck on PyPI Metadata**
Open a new PowerShell and check your existing pip processes:

```powershell
Get-Process python | Select-Object ProcessName, CPU, Memory
```

If a python process is consuming high CPU/memory, pip is computing dependencies. If it's idle, it's network-stalled.

**3. Try with `--prefer-binary` Flag**
```powershell
pip install --user notebooklm-py --prefer-binary --no-build-isolation -vv
```

This skips building wheels from source, which can hang if compilation tools are missing.

**4. Explicit Timeout + Interrupt Pattern**
Give it exactly 30 seconds, then interrupt:

```powershell
# Start the install
pip install --user notebooklm-py --default-timeout=30 -vv

# If it hangs past 30s, Ctrl+C and try:
pip install --user notebooklm-py --no-deps
```

`--no-deps` installs only the package itself, skipping dependency resolution entirely.

## Fastest Path Forward

If these all hang, your environment likely has a deeper issue (antivirus scanning pip operations, broken Python environment, or corrupted pip cache). Try:

```powershell
pip cache purge
pip install --upgrade pip --user
pip install --user notebooklm-py --no-cache-dir
```

Which of these hangs—the base package, or does it require `[browser]` to trigger the issue?

## Human

PowerShell 7.6.0
PS P:\\> pip cache purge
Files removed: 5798 (4447.7 MB)
Directories removed: 97
PS P:\\> pip install --upgrade pip --user

## Assistant

Good—cache purge succeeded (5.7 GB freed). Now the pip upgrade is running. Let it complete; this should take 10–30 seconds depending on network speed.

Once the pip upgrade finishes, try:

```powershell
pip install --user notebooklm-py --no-cache-dir -vv
```

Start with the base package without `[browser]` to confirm it resolves. Post the output once it either completes or hangs—that will tell us whether the issue is:
- pip itself (fixed by upgrade)
- dependency resolution (notebooklm-py's deps)
- network/PyPI access (would hang regardless)

Let me know what you see.

## Human

It's been several min.

## Assistant

The pip upgrade itself is hanging—that's a strong signal of a deeper environmental issue, not just `notebooklm-py`.

## Interrupt & Diagnose

**1. Kill the Process**
```powershell
Ctrl+C
```

**2. Check Python/pip Integrity**
```powershell
python -m pip --version
python -m ensurepip --upgrade
```

**3. Try Direct pip via Module**
Instead of the `pip` command, use Python's module interface:

```powershell
python -m pip install --user notebooklm-py --no-cache-dir --default-timeout=10
```

This bypasses pip's shell wrapper—sometimes that's the bottleneck on Windows.

**4. Check for Antivirus/EDR Interference**
If you're on a corporate machine, antivirus or endpoint detection/response (EDR) software often intercepts Python package installations. Check:
- Windows Defender status: `Get-MpPreference`
- Running security software in Task Manager
- Network traffic logs if available

**5. Nuclear Option: Fresh Python Install**
If module invocation also hangs, your Python installation may be corrupted. Consider:
- Uninstall Python 3.14
- Reinstall fresh from python.org
- Use a virtual environment immediately after install

**What to try first:** Kill the process and test `python -m pip --version`. Does that return instantly, or does it also hang?

## Human

PowerShell 7.6.0
PS P:\\> python -m pip --version
pip 26.0.1 from C:\\Users\\brsth\\AppData\\Roaming\\Python\\Python314\\site-packages\\pip (python 3.14)
PS P:\\> python -m ensurepip --upgrade
Defaulting to user installation because normal site-packages is not writeable

## Assistant

Good—`python -m pip --version` returned instantly, so pip itself isn't broken. The `ensurepip` command is now running (it's upgrading pip's bundled dependencies). Let it complete; this can take 30–60 seconds.

Once `ensurepip` finishes, immediately try:

```powershell
python -m pip install --user notebooklm-py --no-cache-dir --default-timeout=10
```

Using `python -m pip` instead of bare `pip` bypasses the shell wrapper and is more reliable on Windows. The `--default-timeout=10` is aggressive but will fail fast if PyPI is unreachable rather than hanging indefinitely.

Post the output—either success, a specific error, or if it hangs again.

## Human

It hung there for several minutes.

## Assistant

The `ensurepip` hang confirms this isn't a `notebooklm-py` issue—your Python environment itself can't reach PyPI or is blocked during network operations.

## Root Cause Likely: Network/Firewall Block

This is almost certainly:
- Corporate proxy/firewall blocking PyPI
- Antivirus intercepting HTTPS to pypi.org
- ISP/network-level blocking
- DNS resolution failure

## Immediate Tests

**1. Check Network Connectivity to PyPI**
```powershell
Test-NetConnection -ComputerName pypi.org -Port 443
```

If this hangs or returns `False`, PyPI is unreachable from your network.

**2. Try HTTP Instead of HTTPS (Workaround)**
```powershell
python -m pip install --user notebooklm-py -i http://pypi.python.org/simple/ --trusted-host pypi.python.org
```

This uses unencrypted PyPI (deprecated but sometimes works through restrictive firewalls).

**3. Check if You're Behind a Proxy**
```powershell
ipconfig /all
```

Look for proxy settings in your network adapter config, or check:
```powershell
[System.Net.ServicePointManager]::DefaultConnectionLimit = 10
```

## Practical Next Steps

**Given the hang pattern, you likely need to:**

1. **Contact your IT/network admin** if corporate—ask if PyPI is blocked or requires proxy auth
2. **Switch networks** (mobile hotspot) to test if it's local network blocking
3. **Use a pre-built virtual environment** from a machine that can reach PyPI, then transfer it

What happens with `Test-NetConnection -ComputerName pypi.org -Port 443`?

## Human

PowerShell 7.6.0
PS P:\\> [System.Net.ServicePointManager]::DefaultConnectionLimit = 10
PS P:\\>

## Assistant

That command just set a connection limit—it doesn't test connectivity. Try the actual network test:

```powershell
Test-NetConnection -ComputerName pypi.org -Port 443
```

This will either:
- Return quickly with `TcpTestSucceeded : True` (PyPI is reachable)
- Hang or return `False` (PyPI is blocked)

Run this and let me know what it returns or if it hangs.

## Human

PowerShell 7.6.0
PS P:\\> Test-NetConnection -ComputerName pypi.org -Port 443
Test-NetConnection - 151.101.192.223:443 [Attempting TCP connect                                                     ]

## Assistant

It's hanging on the TCP connection attempt to PyPI—**PyPI is blocked or unreachable from your network**. This confirms the issue.

## Immediate Workaround

**Interrupt (`Ctrl+C`) and try a direct DNS/IP test:**

```powershell
Ctrl+C
nslookup pypi.org
```

This tests if DNS resolution works. If `nslookup` hangs too, your network is severely restricted (corporate firewall blocking external DNS or all external traffic).

## Practical Solutions

**Option 1: Use a Different Network (Fastest Test)**
Tether to mobile hotspot and retry:
```powershell
python -m pip install --user notebooklm-py --no-cache-dir
```

If this works, your office/ISP is blocking PyPI.

**Option 2: Pre-Download Offline**
On a machine with PyPI access, download the wheel:
```powershell
pip download notebooklm-py[browser] -d C:\wheels
```

Transfer `C:\wheels\` to your machine, then install locally:
```powershell
pip install --user --no-index --find-links C:\wheels notebooklm-py[browser]
```

**Option 3: Docker/WSL Alternative**
If you have WSL or Docker, they may have different network access rules than your host PowerShell.

**Option 4: Contact IT**
If corporate, ask your network team to whitelist `pypi.org` and `files.pythonhosted.org` on your firewall.

Which is most practical for your setup—testing via mobile hotspot, or getting pre-downloaded wheels from another machine?

## Human

PS P:\\> nslookup pypi.org
Server:  dns.google
Address:  8.8.8.8

Non-authoritative answer:
Name:    pypi.org
Addresses:  2a04:4e42:600::223
          2a04:4e42:400::223
          2a04:4e42:200::223
          2a04:4e42::223
          151.101.128.223
          151.101.64.223
          151.101.192.223
          151.101.0.223

PS P:\\>

## Assistant

DNS resolves fine—PyPI is reachable by name and has multiple IPs. The TCP hang suggests the connection is timing out *after* DNS resolves, which points to:

- **Firewall dropping packets silently** (not rejecting, just dropping)
- **Asymmetric routing** (outbound blocked, inbound allowed)
- **Antivirus/proxy intercepting HTTPS**

## Quick Diagnostic

**Test HTTP (unencrypted) to PyPI:**
```powershell
Test-NetConnection -ComputerName pypi.org -Port 80
```

If port 80 connects but 443 hangs, it's HTTPS-specific (likely antivirus/proxy inspecting SSL).

**If 80 also hangs:** Firewall is blocking all external traffic to PyPI.

## Bypass Strategy

Try installing from a **local PyPI mirror or alternative index** that might not be blocked:

```powershell
python -m pip install --user notebooklm-py -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

This uses Aliyun's PyPI mirror (accessible in many restricted networks). If this also hangs, your network is blocking all external Python package sources.

**Most likely scenario:** Your firewall/antivirus is selectively blocking `pypi.org` on port 443. Test port 80 first, then let me know if you want to escalate to IT or try the mirror approach.

## Human

PS P:\\> Test-NetConnection -ComputerName pypi.org -Port 80
Test-NetConnection - 151.101.192.223:80 [Attempting TCP connect                                                      ]

## Assistant

Port 80 is also hanging—your network is blocking **all external traffic to PyPI**, not just HTTPS. This is a blanket firewall rule, likely corporate policy.

## Diagnosis Complete

Your environment cannot reach PyPI at all. Installing packages from the internet is not possible from this machine/network.

## Your Only Viable Options

**1. Use Mobile Hotspot (Fastest)**
```powershell
Ctrl+C
# Disconnect from office WiFi, connect to mobile hotspot
python -m pip install --user notebooklm-py[browser]
```

This bypasses the corporate firewall entirely.

**2. Pre-Downloaded Wheels (If You Have Access Elsewhere)**
On a machine that can reach PyPI:
```powershell
pip download notebooklm-py[browser] -d C:\nlm_wheels --platform win_amd64 --python-version 314 --only-binary=:all:
```

Transfer the `C:\nlm_wheels\` folder to your machine via USB/cloud, then:
```powershell
pip install --user --no-index --find-links C:\nlm_wheels notebooklm-py[browser]
```

**3. Contact IT to Whitelist PyPI**
Request your network team allowlist:
- `pypi.org` (all ports)
- `files.pythonhosted.org` (all ports)

This is a standard developer request and usually takes 1–2 business days.

**4. Use Alternative Tools (No Python Required)**
If you just need to extract NotebookLM sources, use the **Chrome extension** approach (NotebookLM Sources Exporter) or **Google Takeout** instead—both work entirely in-browser and don't require pip.

Which approach fits your immediate need?
