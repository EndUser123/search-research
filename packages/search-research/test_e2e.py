"""Test local_search and cks_search return meaningful data."""
import subprocess, json, sys, os, time

env = os.environ.copy()
for k in ["TAVILY_API_KEY", "SERPER_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY"]:
    env[k] = "test"

proc = subprocess.Popen(
    [sys.executable, "P:/packages/search-research/run_mcp.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)

def read_msg(timeout=15):
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
init_resp, t = read_msg(5)
print(f"INIT: OK ({t:.1f}s)")

# Test cks_search - should hit FTS on the ~508K entries
send({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "cks_search", "arguments": {"query": "mcp server search", "limit": 3}}, "id": 2})
resp, t = read_msg(15)
print(f"\nCKS_SEARCH: ({t:.1f}s)")
if resp:
    data = json.loads(resp)
    content = data.get("result", {}).get("content", [{}])[0].get("text", "")
    print(content[:400])
else:
    print("NO RESPONSE")

# Test local_search
send({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "local_search", "arguments": {"query": "mcp tool description", "limit": 3}}, "id": 3})
resp, t = read_msg(15)
print(f"\nLOCAL_SEARCH: ({t:.1f}s)")
if resp:
    data = json.loads(resp)
    content = data.get("result", {}).get("content", [{}])[0].get("text", "")
    print(content[:400])
else:
    print("NO RESPONSE")

print(f"\nStill alive: {proc.poll() is None}")
proc.kill()