"""End-to-end test of local_search via MCP protocol."""
import subprocess, json, sys, os

env = os.environ.copy()
for k in ["TAVILY_API_KEY", "SERPER_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY"]:
    env[k] = "test"

proc = subprocess.Popen(
    [sys.executable, "P:/packages/search-research/run_mcp.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)

def read_line():
    line = proc.stdout.readline()
    if not line:
        return None
    return line.decode().strip()

def send(method, params=None, id=None):
    msg = {"jsonrpc": "2.0", "method": method}
    if params: msg["params"] = params
    if id is not None: msg["id"] = id
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()

# Initialize
send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, id=0)
read_line()

# Call local_search with a query that should return results
send("tools/call", {
    "name": "local_search",
    "arguments": {"query": "mcp tool description", "limit": 3}
}, id=2)
r = read_line()
if r:
    data = json.loads(r)
    result = data.get("result", {})
    content = result.get("content", [])
    if content:
        text = content[0].get("text", "")
        print(text[:500])
    else:
        print("No content in response:", result)
else:
    print("NO RESPONSE")

proc.kill()