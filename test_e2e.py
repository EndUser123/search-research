"""Test local_search with explicit message framing."""
import subprocess, json, sys, os, time

env = os.environ.copy()
for k in ["TAVILY_API_KEY", "SERPER_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY"]:
    env[k] = "test"

proc = subprocess.Popen(
    [sys.executable, "P:/packages/search-research/run_mcp.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)

# Read with timeout
def read_msg(timeout=10):
    start = time.time()
    data = b""
    while time.time() - start < timeout:
        chunk = proc.stdout.read(1)
        if not chunk:
            print(f"EOF after {time.time()-start:.1f}s, data={data[:50]}")
            return None
        data += chunk
        if chunk == b'\n':
            break
    return data.decode().strip()

def send(msg, id=None):
    if id is not None:
        msg["id"] = id
    line = json.dumps(msg) + "\n"
    proc.stdin.write(line.encode())
    proc.stdin.flush()

# Initialize
send({"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}, id=0)
r = read_msg()
print("INIT:", r[:80] if r else "NONE")

# Tools/call for local_search
call = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "local_search",
        "arguments": {"query": "mcp", "limit": 2}
    },
    "id": 2
}
send(call)
r = read_msg(15)
print("RESP:", r[:200] if r else "NONE")
print("POLL:", proc.poll())

proc.kill()