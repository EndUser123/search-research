"""Test MCP server stays alive across multiple requests."""
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

def read_line(timeout=3):
    start = time.time()
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if line:
            return line.decode().strip()
        time.sleep(0.1)
    return None

def send_msg(method, params=None, id=1):
    msg = {"jsonrpc": "2.0", "id": id, "method": method}
    if params:
        msg["params"] = params
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()

# Initialize
send_msg("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, id=0)
r = read_line()
print("INIT:", r[:80] if r else "None")

# 3 tool calls in sequence
for i in range(3):
    send_msg("tools/list", {}, id=i+1)
    r = read_line()
    print(f"tools/list #{i+1}:", r[:80] if r else "None")
    time.sleep(0.5)

# Final alive check
time.sleep(1)
if proc.poll() is None:
    print("Still alive after 3 requests")
    proc.kill()
else:
    print(f"EXITED at request {i+1} with code {proc.returncode}")
    stderr = proc.stderr.read()
    print("stderr:", stderr[:200])