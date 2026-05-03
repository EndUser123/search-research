"""Quick test - just init + ping, verify server stays responsive."""
import subprocess, json, sys, os, time

env = os.environ.copy()
for k in ["TAVILY_API_KEY", "SERPER_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY"]:
    env[k] = "test"

proc = subprocess.Popen(
    [sys.executable, "P:/packages/search-research/run_mcp.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)

def read_any(timeout=3):
    """Read whatever comes back, with timeout."""
    start = time.time()
    result = b""
    while time.time() - start < timeout:
        ch = proc.stdout.read(1)
        if not ch:
            return None
        result += ch
        if ch == b'\n':
            return result.decode().strip()
    return result.decode().strip() if result else None

def send(msg, id=None):
    if id is not None:
        msg["id"] = id
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()

# Init
send({"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}, id=0)
print("INIT:", read_any(5)[:60])

# Ping (notification - no id)
send({"jsonrpc": "2.0", "method": "ping"})
print("PING sent, checking if alive...")
time.sleep(0.5)
print("Still alive:", proc.poll() is None)

proc.kill()