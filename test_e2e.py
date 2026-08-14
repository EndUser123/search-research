"""Quick test: does cks_search work (sync, should be fast)?."""
import subprocess, json, sys, os, time

env = os.environ.copy()
for k in ["TAVILY_API_KEY", "SERPER_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY"]:
    env[k] = "test"

proc = subprocess.Popen(
    [sys.executable, "P:\\\\\\packages/search-research/run_mcp.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)

def read_msg(timeout=20):
    chunks = []
    start = time.time()
    while time.time() - start < timeout:
        ch = proc.stdout.read(1)
        if not ch:
            return None, time.time() - start
        chunks.append(ch)
        if ch == b'\n':
            break
    return b''.join(chunks).decode().strip(), time.time() - start

def send(msg, id=None):
    if id is not None:
        msg["id"] = id
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()

# Init
send({"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}, id=0)
print("INIT:", read_msg(5)[0][:60])

# cks_search (sync, no async needed)
send({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "cks_search", "arguments": {"query": "mcp server", "limit": 2}}, "id": 2})
resp, t = read_msg(20)
print(f"\nCKS_SEARCH ({t:.1f}s):")
if resp:
    data = json.loads(resp)
    content = data.get("result", {}).get("content", [{}])[0].get("text", "")
    print(content[:300] if content else "(empty)")
else:
    print("NO RESPONSE")

print(f"\nStill alive: {proc.poll() is None}")
proc.kill()