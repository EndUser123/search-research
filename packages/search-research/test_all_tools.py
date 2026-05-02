"""Quick smoke test: initialize + tools/list + ping."""
import subprocess
import json
import sys
import os
import time

env = os.environ.copy()
for k in ["TAVILY_API_KEY", "SERPER_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY"]:
    env[k] = "test"

proc = subprocess.Popen(
    [sys.executable, "P:/packages/search-research/run_mcp.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env,
)

def read_line(timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if line:
            return line.decode().strip()
        time.sleep(0.05)
    return None

def send(method, params=None, id=1):
    msg = {"jsonrpc": "2.0", "id": id, "method": method}
    if params is not None:
        msg["params"] = params
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()

# Initialize
send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, id=0)
r = read_line()
print("INIT:", "OK" if r and "serverInfo" in r else f"FAIL: {r}")

# Tools list
send("tools/list", {}, id=1)
r = read_line()
if r:
    try:
        data = json.loads(r)
        tools = data.get("result", {}).get("tools", [])
        print(f"TOOLS/LIST: OK ({len(tools)} tools)")
        for t in tools:
            print(f"  - {t['name']}")
    except:
        print(f"TOOLS/LIST: FAIL (parse error)")
else:
    print("TOOLS/LIST: NO RESPONSE")

# Ping
send("ping", {}, id=2)
r = read_line()
print("PING:", "OK" if r else "NO RESPONSE")

time.sleep(0.5)
if proc.poll() is None:
    print("Still alive: YES")
    proc.kill()
else:
    print(f"Still alive: NO (exit {proc.returncode})")