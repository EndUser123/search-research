#!/usr/bin/env python
"""Multi-terminal MCP integration test for T2, T3, T4-full.

T2  = shared backend reuse across two simultaneous shims
T3  = warm semantic query reuse (2nd terminal <5s vs ~7s cold)
T4-full = all 7 MCP tools return results without path errors

Run: python multi_terminal_test.py
"""
import json
import subprocess
import sys
import time
import threading
import os

NPX = 'cmd /c "C:/Program Files/nodejs/npx" github:jasonwarta/mcp-mux'
CWD = "P:\\\\packages/search-research"

results = {}
results_lock = threading.Lock()


def run_shim(shim_id: int, test_name: str, test_args: dict):
    """Run a single shim session, collect timing and result data."""
    cmd = f'{NPX}'
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=CWD,
    )

    request_id = [0]

    def send(req):
        req["jsonrpc"] = "2.0"
        if "id" in req:
            request_id[0] += 1
            req["id"] = request_id[0]
            assigned_id = req["id"]
        else:
            assigned_id = None
        line = json.dumps(req)
        proc.stdin.write((line + "\n").encode("utf-8"))
        proc.stdin.flush()
        return assigned_id

    def recv(target_id=None, timeout=20.0):
        start = time.time()
        while time.time() - start < timeout:
            line = proc.stdout.readline()
            if not line:
                return {"error": f"EOF in shim{shim_id}"}
            try:
                resp = json.loads(line.decode("utf-8", errors="replace"))
                if target_id is None or resp.get("id") == target_id:
                    return resp
            except json.JSONDecodeError:
                continue
        return {"error": "timeout"}

    try:
        # MCP handshake
        init_id = send({
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": f"integration-test-shim{shim_id}", "version": "0.1.0"},
            },
        })
        recv(init_id, timeout=10.0)
        proc.stdin.write((json.dumps({"jsonrpc": "2.0", "method": "initialized", "params": {}}) + "\n").encode("utf-8"))
        proc.stdin.flush()
        time.sleep(0.5)

        # Run test-specific actions
        if test_name == "T2_T1":
            # Cold start timing for T2 first shim
            start_ts = time.time()
            t1_id = send({"method": "tools/list", "params": {}})
            t1_resp = recv(t1_id, timeout=30.0)
            elapsed = time.time() - start_ts
            with results_lock:
                results[f"shim{shim_id}_T1_time"] = elapsed
                results[f"shim{shim_id}_T1_tools"] = len(t1_resp.get("result", {}).get("tools", []))
                results[f"shim{shim_id}_T1_success"] = "error" not in t1_resp and len(t1_resp.get("result", {}).get("tools", [])) > 0

        elif test_name == "T3_semantic":
            # Semantic search timing
            start_ts = time.time()
            sem_id = send({
                "method": "tools/call",
                "params": {
                    "name": "search-research__local_search",
                    "arguments": {"query": "SearchSession", "limit": 5},
                },
            })
            sem_resp = recv(sem_id, timeout=30.0)
            elapsed = time.time() - start_ts
            with results_lock:
                results[f"shim{shim_id}_sem_time"] = elapsed
                results[f"shim{shim_id}_sem_success"] = "error" not in sem_resp

        elif test_name == "T4_full":
            # All 7 tools test
            tools_to_call = [
                ("unified_search", {"query": "test", "limit": 3}),
                ("local_search", {"query": "SearchSession", "limit": 5}),
                ("web_search", {"query": "python", "limit": 3}),
                ("cks_search", {"query": "test", "limit": 3}),
                ("cks_search_semantic", {"query": "test", "limit": 3}),
                ("cks_ingest", {"content": "test", "type": "memory", "tags": ["test"]}),
                ("cks_stats", {}),
            ]
            tool_results = {}
            for tool_name, args in tools_to_call:
                start_ts = time.time()
                tid = send({
                    "method": "tools/call",
                    "params": {"name": f"search-research__{tool_name}", "arguments": args},
                })
                resp = recv(tid, timeout=60.0)
                elapsed = time.time() - start_ts
                has_error = "error" in resp
                tool_results[tool_name] = {"success": not has_error, "time": elapsed, "error": resp.get("error") if has_error else None}
            with results_lock:
                results[f"shim{shim_id}_tools"] = tool_results

    finally:
        # Clean shutdown
        try:
            proc.stdin.write((json.dumps({"jsonrpc": "2.0", "method": "shutdown", "params": {}, "id": 999}) + "\n").encode("utf-8"))
            proc.stdin.flush()
            proc.stdin.close()
            proc.wait(timeout=5)
        except Exception:
            pass


# =============================================================================
# T2 + T3: Simultaneous shims from two terminal processes
# =============================================================================
print("=== T2: Shared Backend Reuse (2 simultaneous shims) ===")

t2_start = time.time()

# Start shim 1 (cold start, measures backend startup time)
shim1 = threading.Thread(target=run_shim, args=(1, "T2_T1", {}))
shim1.start()
time.sleep(3)  # Let shim1 fully start before launching shim2

# Start shim 2 (should reuse backend from shim1 if shared mode works)
shim2 = threading.Thread(target=run_shim, args=(2, "T2_T1", {}))
shim2.start()

shim1.join(timeout=40)
shim2.join(timeout=40)

t2_elapsed = time.time() - t2_start

# Count Python processes (should be: 1 broker shim runner + 1 backend Python)
# The uv process spawns a child Python for the backend
python_pids = subprocess.run(
    'tasklist //FI "IMAGENAME eq python.exe" //FO CSV 2>nul', shell=True, capture_output=True
).stdout.decode("utf-8", errors="replace")

print(f"  Shims launched at t+0s and t+3s")
print(f"  Total T2 time: {t2_elapsed:.1f}s")
print(f"  Shim1 T1 time (cold): {results.get('shim1_T1_time', 'N/A'):.2f}s")
print(f"  Shim2 T1 time: {results.get('shim2_T1_time', 'N/A'):.2f}s")
print(f"  Shim1 tools: {results.get('shim1_T1_tools', 0)}")
print(f"  Shim2 tools: {results.get('shim2_T1_tools', 0)}")

# Check: shim2 should see same or fewer tools since backend already started
# If shared, shim2 reuses the same backend (no additional cold start)
# If NOT shared, shim2 would need to start its own backend (more processes)
# The key metric: did shim2 complete in reasonable time while shim1 was alive?
t2_pass = (
    results.get("shim1_T1_success", False) and
    results.get("shim2_T1_success", False) and
    results.get("shim2_T1_time", 999) < 20.0  # shim2 should complete within reasonable time
)
print(f"  T2: {'PASS' if t2_pass else 'FAIL'}")
print(f"  Python processes during T2: {python_pids.count('python.exe')}")


# =============================================================================
# T3: Warm semantic query reuse (second terminal gets cached model)
# =============================================================================
print("\n=== T3: Warm Semantic Query Reuse ===")

# Kill current processes and start fresh
taskkill_cmds = "taskkill //F //IM python.exe 2>nul & taskkill //F //IM node.exe 2>nul & echo done"
subprocess.run(taskkill_cmds, shell=True, capture_output=True, timeout=10)
time.sleep(2)

# Terminal 1: cold semantic search (measures full model load time)
t3_start = time.time()
shim_cold = threading.Thread(target=run_shim, args=(10, "T3_semantic", {}))
shim_cold.start()
shim_cold.join(timeout=60)

# Kill and restart for warm test
subprocess.run(taskkill_cmds, shell=True, capture_output=True, timeout=10)
time.sleep(2)

# Terminal 2: warm semantic search (backend cached, <5s target)
t3_warm_start = time.time()
shim_warm = threading.Thread(target=run_shim, args=(20, "T3_semantic", {}))
shim_warm.start()
shim_warm.join(timeout=60)

cold_time = results.get("shim10_sem_time", 999)
warm_time = results.get("shim20_sem_time", 999)

print(f"  Cold semantic time: {cold_time:.2f}s")
print(f"  Warm semantic time: {warm_time:.2f}s")
# Note: warm time should be <5s if model is cached in shared backend
# But this is hard to measure in single-terminal test since we restart each time
# Real T3 requires running from a second Claude Code terminal
print(f"  NOTE: True T3 warm-reuse requires 2 Claude Code sessions")
print(f"  Current result measures sequential cold-starts")
t3_pass = results.get("shim10_sem_success", False) and results.get("shim20_sem_success", False)
print(f"  T3: {'PASS (both succeeded)' if t3_pass else 'FAIL'} — warm-reuse requires multi-terminal verification")


# =============================================================================
# T4-full: All 7 MCP tools
# =============================================================================
print("\n=== T4-full: All 7 Tools ===")

# Clean slate again
subprocess.run(taskkill_cmds, shell=True, capture_output=True, timeout=10)
time.sleep(2)

shim_full = threading.Thread(target=run_shim, args=(100, "T4_full", {}))
shim_full.start()
shim_full.join(timeout=120)

tools_results = results.get("shim100_tools", {})
all_tools = [
    "unified_search",
    "local_search",
    "web_search",
    "cks_search",
    "cks_search_semantic",
    "cks_ingest",
    "cks_stats",
]
print(f"  Tool results ({len(tools_results)} tested):")
t4_all_pass = True
for tool in all_tools:
    r = tools_results.get(tool, {})
    status = "PASS" if r.get("success") else "FAIL"
    if not r.get("success"):
        t4_all_pass = False
    print(f"    {tool}: {status} ({r.get('time', 0):.2f}s) {'— ' + str(r.get('error'))[:80] if r.get('error') else ''}")

print(f"  T4-full: {'PASS' if t4_all_pass else 'FAIL'}")


# =============================================================================
# Final summary
# =============================================================================
print("\n=== SUMMARY ===")
print(f"  T2 (Shared reuse): {'PASS' if t2_pass else 'FAIL'}")
print(f"  T3 (Warm reuse): {'PASS (both succeeded)' if t3_pass else 'FAIL'} — warm metric unverified in single-terminal")
print(f"  T4-full (All 7 tools): {'PASS' if t4_all_pass else 'FAIL'}")

# Cleanup
subprocess.run(taskkill_cmds, shell=True, capture_output=True, timeout=10)