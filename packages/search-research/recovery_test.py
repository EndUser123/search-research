#!/usr/bin/env python
"""Recovery tests: T3 warm semantic reuse, T6 broker crash recovery.

T3  = warm semantic query (shared model cache)
T6  = broker restart after kill (crash recovery)

These tests keep a client connected across broker/backend lifecycle events.
"""
import json
import subprocess
import sys
import time
import threading

NPX = 'cmd /c "C:/Program Files/nodejs/npx" github:jasonwarta/mcp-mux'
CWD = "P:\\\\packages/search-research"


class MCPClient:
    """Persistent MCP client — maintains stdio connection across broker restarts."""

    def __init__(self, label="client"):
        self.label = label
        self.proc = None
        self.request_id = 0

    def connect(self):
        """Start mcp-mux and complete handshake."""
        self.proc = subprocess.Popen(
            NPX,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=CWD,
        )
        self.request_id = 0
        # Handshake
        self._send({"method": "initialize", "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": self.label, "version": "0.1.0"},
        }})
        resp = self._recv(timeout=15.0)
        print(f"  [{self.label}] Handshake: {resp.get('result', {}).get('protocolVersion', 'unknown')}")
        # Send initialized
        self._send_raw({"jsonrpc": "2.0", "method": "initialized", "params": {}})
        time.sleep(0.5)

    def _send(self, req):
        self.request_id += 1
        req["jsonrpc"] = "2.0"
        req["id"] = self.request_id
        return self._send_raw(req)

    def _send_raw(self, req):
        line = json.dumps(req)
        self.proc.stdin.write((line + "\n").encode("utf-8"))
        self.proc.stdin.flush()

    def _recv(self, target_id=None, timeout=20.0):
        start = time.time()
        while time.time() - start < timeout:
            if self.proc.stdout is None:
                break
            line = self.proc.stdout.readline()
            if not line:
                stderr = ""
                if self.proc.stderr:
                    stderr = self.proc.stderr.read(200).decode("utf-8", errors="replace")
                return {"error": f"EOF. stderr: {stderr[:100]}"}
            try:
                resp = json.loads(line.decode("utf-8", errors="replace"))
                if target_id is None or resp.get("id") == target_id:
                    return resp
            except json.JSONDecodeError:
                continue
        return {"error": "timeout"}

    def call_tool(self, tool_name: str, arguments: dict, timeout=60.0):
        """Call an MCP tool and return (elapsed_time, response_dict)."""
        tid = self._send({"method": "tools/call", "params": {
            "name": f"search-research__{tool_name}",
            "arguments": arguments,
        }})
        start = time.time()
        resp = self._recv(target_id=tid, timeout=timeout)
        elapsed = time.time() - start
        return elapsed, resp

    def is_alive(self):
        """Check if subprocess is still running."""
        return self.proc is not None and self.proc.poll() is None

    def shutdown(self):
        """Clean shutdown."""
        try:
            self._send({"method": "shutdown", "params": {}, "id": 999})
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            pass


# =============================================================================
# T3: Warm semantic query — measure cold vs warm timing
# =============================================================================
print("=== T3: Warm Semantic Query Reuse ===")

client_t3 = MCPClient("t3-warm-test")
client_t3.connect()

# First call — expected to cold-start the model (~5-7s)
print("  Call 1 (cold model load)...")
t3_start = time.time()
elapsed1, resp1 = client_t3.call_tool(
    "cks_search_semantic",
    {"query": "test query for warm-up", "limit": 3},
    timeout=60.0
)
duration1 = time.time() - t3_start
has_error1 = "error" in resp1
content1 = resp1.get("result", {}).get("content", [])
text1 = content1[0].get("text", "")[:150] if content1 else ""

print(f"    Elapsed: {elapsed1:.2f}s (call_tool timer)")
print(f"    Duration field: {text1}")
print(f"    Error: {resp1.get('error') if has_error1 else 'none'}")

# Second call — model should be warm (check via MCP duration field, not wall clock)
print("  Call 2 (model warm)...")
t3_start2 = time.time()
elapsed2, resp2 = client_t3.call_tool(
    "cks_search_semantic",
    {"query": "another warm test", "limit": 3},
    timeout=60.0
)
duration2 = time.time() - t3_start2
has_error2 = "error" in resp2
content2 = resp2.get("result", {}).get("content", [])
text2 = content2[0].get("text", "")[:150] if content2 else ""

print(f"    Elapsed: {elapsed2:.2f}s (call_tool timer)")
print(f"    Duration field: {text2}")
print(f"    Error: {resp2.get('error') if has_error2 else 'none'}")

# Extract MCP-reported duration from content text
import re
def extract_mcp_duration(text: str):
    m = re.search(r'Duration.*?(\d+\.?\d*)s', text)
    return float(m.group(1)) if m else None

mcp_dur1 = extract_mcp_duration(text1)
mcp_dur2 = extract_mcp_duration(text2)

print(f"\n    MCP-reported durations:")
print(f"      Call 1: {mcp_dur1}s")
print(f"      Call 2: {mcp_dur2}s")

# T3 pass criterion: both calls succeed, call 2 duration is <5s (warm model)
t3_pass = (
    not has_error1 and not has_error2 and
    mcp_dur2 is not None and mcp_dur2 < 5.0
)
print(f"  T3: {'PASS' if t3_pass else 'FAIL'}")
if not t3_pass and mcp_dur2 is not None and mcp_dur2 >= 5.0:
    print(f"    NOTE: Call 2 took {mcp_dur2}s — model may not have been cached")

client_t3.shutdown()


# =============================================================================
# T6: Broker crash recovery — kill broker while client connected
# =============================================================================
print("\n=== T6: Broker Crash Recovery ===")

client_t6 = MCPClient("t6-crash-test")
client_t6.connect()

# Verify connection is working with a quick call
print("  Pre-crash verification call...")
_, pre_resp = client_t6.call_tool("local_search", {"query": "test", "limit": 2}, timeout=30.0)
pre_ok = "error" not in pre_resp
print(f"    Pre-crash call: {'OK' if pre_ok else 'FAIL — ' + str(pre_resp.get('error'))}")

# Find broker process (the node process running mcp-mux)
# We need to find the node.exe that is the broker (not a shim)
# Strategy: the broker is the node process that spawned the backend
print("  Finding broker PID...")
broker_pids = subprocess.run(
    'tasklist //FI "IMAGENAME eq node.exe" //FO CSV 2>nul',
    shell=True, capture_output=True
).stdout.decode("utf-8", errors="replace")

node_pids = []
for line in broker_pids.splitlines()[1:]:  # skip header
    if "node.exe" in line:
        parts = line.strip().split('","')
        if len(parts) >= 2:
            pid_str = parts[1].strip('"')
            try:
                node_pids.append(int(pid_str))
            except ValueError:
                pass

print(f"    Node PIDs running: {node_pids}")

# Kill the broker
if node_pids:
    # Kill the first node process (broker) — kill all to be safe
    killed_pids = []
    for pid in node_pids:
        result = subprocess.run(
            f'taskkill //F //PID {pid}',
            shell=True, capture_output=True
        )
        if result.returncode == 0:
            killed_pids.append(pid)
    print(f"    Killed broker PID(s): {killed_pids}")
else:
    print("    No broker found — may have already exited")

time.sleep(2)

# Try to call a tool after broker kill — broker should auto-restart
print("  Post-crash recovery call (broker should auto-restart)...")
t6_start = time.time()
try:
    elapsed6, resp6 = client_t6.call_tool(
        "cks_search",
        {"query": "post-crash test", "limit": 2},
        timeout=60.0
    )
    has_error6 = "error" in resp6
    duration6 = time.time() - t6_start
    print(f"    Recovery call elapsed: {elapsed6:.2f}s")
    print(f"    Error: {resp6.get('error') if has_error6 else 'none'}")
    content6 = resp6.get("result", {}).get("content", [])
    text6 = content6[0].get("text", "")[:200] if content6 else ""
    print(f"    Result preview: {text6[:150]}")
except Exception as e:
    has_error6 = True
    duration6 = time.time() - t6_start
    print(f"    Recovery call FAILED with: {e}")

# T6 pass criterion: call succeeds after broker kill (auto-restart worked)
t6_pass = not has_error6
print(f"  T6: {'PASS' if t6_pass else 'FAIL'}")
if not t6_pass:
    print(f"    Recovery failed after {duration6:.1f}s — broker did not restart in time")

try:
    client_t6.shutdown()
except Exception:
    pass


# =============================================================================
# Summary
# =============================================================================
print("\n=== SUMMARY ===")
print(f"  T3 (Warm semantic reuse): {'PASS' if t3_pass else 'FAIL'}")
print(f"  T6 (Broker crash recovery): {'PASS' if t6_pass else 'FAIL'}")

# Cleanup
subprocess.run('taskkill //F //IM python.exe 2>nul', shell=True, capture_output=True)
subprocess.run('taskkill //F //IM node.exe 2>nul', shell=True, capture_output=True)

all_pass = t3_pass and t6_pass
print(f"\n  OVERALL: {'ALL PASS' if all_pass else 'SOME FAILED'}")
sys.exit(0 if all_pass else 1)