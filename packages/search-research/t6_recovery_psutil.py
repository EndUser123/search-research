#!/usr/bin/env python
"""T6 test: kill all node processes, verify mcp-mux auto-restarts the broker.

Strategy: Use psutil for accurate PID detection, keep client connected across broker death."""
import subprocess, time, json, psutil

NPX_CMD = ['C:/Program Files/nodejs/npx.cmd', 'github:jasonwarta/mcp-mux']
CWD = "P:\\\\\\packages/search-research"

def get_matching_pids(name_pattern):
    """Get PIDs matching pattern using psutil."""
    return [p.pid for p in psutil.process_iter(['name']) if name_pattern.lower() in p.info['name'].lower()]

def find_broker_pid():
    """Find the node broker PID (mcp-mux process)."""
    node_pids = get_matching_pids('node.exe')
    return node_pids[0] if node_pids else None

def find_backend_pid():
    """Find the Python backend PID (uv/python)."""
    python_pids = get_matching_pids('python.exe')
    return python_pids if python_pids else []

print("=== T6: Broker Crash Recovery ===")

# Start mcp-mux client
proc = subprocess.Popen(
    NPX_CMD,
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    cwd=CWD
)

def send(req):
    req['jsonrpc'] = '2.0'; req['id'] = 1
    proc.stdin.write((json.dumps(req) + '\n').encode()); proc.stdin.flush()

# Handshake
send({'method': 'initialize', 'params': {
    'protocolVersion': '2024-11-05', 'capabilities': {},
    'clientInfo': {'name': 't6-recovery', 'version': '0.1.0'}}})
r = json.loads(proc.stdout.readline())
print(f"  Handshake: {r.get('result', {}).get('protocolVersion', 'unknown')}")

proc.stdin.write((json.dumps({'jsonrpc': '2.0', 'method': 'initialized', 'params': {}}) + '\n').encode())
proc.stdin.flush()
time.sleep(2)

# Verify connection
send({'method': 'tools/call', 'params': {
    'name': 'search-research__local_search',
    'arguments': {'query': 'warmup', 'limit': 1}}})
t0 = time.time()
resp = json.loads(proc.stdout.readline())
print(f"  Pre-crash call: {time.time()-t0:.3f}s, error={resp.get('error')}")

# Get PIDs BEFORE kill
node_before = find_broker_pid()
python_before = find_backend_pid()
print(f"  Before crash — broker PID: {node_before}, Python backends: {python_before}")

# Kill ALL node processes
if node_before:
    try:
        p = psutil.Process(node_before)
        children_before = [c.pid for c in p.children(recursive=True)]
        print(f"  Broker children: {children_before}")
    except:
        children_before = []

kill_result = subprocess.run('taskkill //F //IM node.exe', shell=True, capture_output=True)
print(f"  Kill all node: rc={kill_result.returncode}")
time.sleep(1)

# Verify node is gone
node_after = find_broker_pid()
print(f"  After kill — broker PID: {node_after} ({'KILLED' if node_before and not node_after else 'still running'})")

# Try tool call immediately after kill (should fail since broker is dead)
send({'method': 'tools/call', 'params': {
    'name': 'search-research__local_search',
    'arguments': {'query': 'immediate_after_kill', 'limit': 1}}})
t0 = time.time()
resp2 = json.loads(proc.stdout.readline())
immediate_elapsed = time.time() - t0
immediate_ok = 'error' not in resp2
print(f"  Immediate call after kill: {immediate_elapsed:.3f}s, error={resp2.get('error')}")

# Wait for broker to auto-restart (mcp-mux maxRestart=5, backoff=1000ms)
print("  Waiting up to 30s for broker auto-restart...")
broker_restarted = False
for i in range(30):
    time.sleep(1)
    node_now = find_broker_pid()
    if node_now:
        print(f"  Broker restarted at PID {node_now} after {i+1}s")
        broker_restarted = True
        break

# Try tool call after broker restart
if broker_restarted:
    print("  Attempting tool call after broker restart...")
    time.sleep(2)  # Give broker a moment to settle
    send({'method': 'tools/call', 'params': {
        'name': 'search-research__local_search',
        'arguments': {'query': 'post_restart', 'limit': 1}}})
    t0 = time.time()
    resp3 = json.loads(proc.stdout.readline())
    recovery_elapsed = time.time() - t0
    recovery_ok = 'error' not in resp3
    print(f"  Post-restart call: {recovery_elapsed:.3f}s, error={resp3.get('error')}")

    # Get PIDs after restart
    node_after_restart = find_broker_pid()
    python_after_restart = find_backend_pid()
    print(f"  After restart — broker PID: {node_after_restart}, Python backends: {python_after_restart}")
else:
    recovery_ok = False
    print("  Broker did NOT restart within 30s")

# T6 result
t6_pass = recovery_ok
print(f"\n  T6 (Broker crash recovery): {'PASS' if t6_pass else 'FAIL'}")
if not t6_pass:
    if not broker_restarted:
        print("    Broker failed to restart within 30s")
    else:
        print("    Broker restarted but tool call failed")

proc.stdin.close()
proc.wait(5)
print(f"\n  Overall T6: {'PASS' if t6_pass else 'FAIL'}")
import sys; sys.exit(0 if t6_pass else 1)