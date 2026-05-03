"""Verify updated tool descriptions."""
import subprocess, json, sys, os, time

env = os.environ.copy()
for k in ["TAVILY_API_KEY", "SERPER_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY"]:
    env[k] = "test"

proc = subprocess.Popen([sys.executable, "P:/packages/search-research/run_mcp.py"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

def read_line():
    return proc.stdout.readline().decode().strip()

def send(method, params=None, id=1):
    msg = {"jsonrpc": "2.0", "id": id, "method": method}
    if params: msg["params"] = params
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()

send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, id=0)
read_line()
send("tools/list", {}, id=1)
r = read_line()
data = json.loads(r)
for t in data["result"]["tools"]:
    desc = t["description"]
    print(f"\n=== {t['name']} ===")
    print(desc[:200] + ("..." if len(desc) > 200 else ""))

proc.kill()