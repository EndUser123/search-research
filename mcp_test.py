#!/usr/bin/env python
"""MCP integration test for mcp-mux + search-research.

Implements full MCP handshake over stdio, then tests T1 (cold start) and T4 (tool call).
Run: python mcp_test.py
"""
import json
import subprocess
import sys
import time

def run_mcp_test():
    """Run MCP handshake + test requests against mcp-mux."""
    # Use full path to npx — subprocess.Popen on Windows can't resolve it from PATH with text=True
    cmd = 'cmd /c "C:/Program Files/nodejs/npx" github:jasonwarta/mcp-mux'

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd="P:\\\\\\packages/search-research",
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
                stderr = proc.stderr.read(500).decode("utf-8", errors="replace")
                return {"error": f"EOF. stderr: {stderr[:200]}"}
            try:
                resp = json.loads(line.decode("utf-8", errors="replace"))
                if target_id is None or resp.get("id") == target_id:
                    return resp
            except json.JSONDecodeError:
                continue
        return {"error": "timeout"}

    results = {}

    # MCP handshake
    init_id = send({
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "integration-test", "version": "0.1.0"},
        },
    })
    init_resp = recv(init_id, timeout=10.0)
    print(f"T0 Handshake: {init_resp.get('result', {}).get('protocolVersion', 'unknown')}")

    # Send initialized notification (no id)
    proc.stdin.write((json.dumps({"jsonrpc": "2.0", "method": "initialized", "params": {}}) + "\n").encode("utf-8"))
    proc.stdin.flush()
    time.sleep(0.3)

    # T1: tools/list
    print("\n=== T1: Cold Start (tools/list) ===")
    t1_id = send({"method": "tools/list", "params": {}})
    t1_resp = recv(t1_id, timeout=30.0)
    if "error" in t1_resp:
        print(f"  FAIL: {t1_resp['error']}")
        results["T1"] = False
    else:
        tools = t1_resp.get("result", {}).get("tools", [])
        print(f"  Tools returned: {len(tools)}")
        for t in tools[:5]:
            print(f"    - {t.get('name')}")
        if len(tools) > 0:
            print(f"  PASS: Backend started, {len(tools)} tools available")
            results["T1"] = True
        else:
            print(f"  FAIL: No tools returned")
            results["T1"] = False

    # T4: cks_search tool call
    print("\n=== T4: Tool Call (cks_search) ===")
    t4_id = send({
        "method": "tools/call",
        "params": {
            "name": "search-research__cks_search",
            "arguments": {"query": "test query", "limit": 3},
        },
    })
    t4_resp = recv(t4_id, timeout=60.0)  # 60s for cold start + model load
    if "error" in t4_resp:
        print(f"  FAIL: {t4_resp['error']}")
        results["T4"] = False
    else:
        content = t4_resp.get("result", {}).get("content", [])
        text = content[0].get("text", "")[:300] if content else ""
        print(f"  Response preview: {text[:200]}")
        print(f"  PASS: cks_search returned result")
        results["T4"] = True

    # T4b: local_search tool call (uses LSP backend with CWD-independent path fix)
    print("\n=== T4b: Tool Call (local_search) ===")
    t4b_id = send({
        "method": "tools/call",
        "params": {
            "name": "search-research__local_search",
            "arguments": {"query": "SearchSession", "limit": 5},
        },
    })
    t4b_resp = recv(t4b_id, timeout=30.0)
    if "error" in t4b_resp:
        print(f"  FAIL: {t4b_resp['error']}")
        results["T4b"] = False
    else:
        content = t4b_resp.get("result", {}).get("content", [])
        text = content[0].get("text", "")[:300] if content else ""
        print(f"  Response preview: {text[:200]}")
        print(f"  PASS: local_search returned result")
        results["T4b"] = True

    # Clean shutdown
    proc.stdin.write((json.dumps({"jsonrpc": "2.0", "method": "shutdown", "params": {}, "id": 999}) + "\n").encode("utf-8"))
    proc.stdin.flush()
    proc.stdin.close()
    proc.wait(timeout=5)

    print("\n=== SUMMARY ===")
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    return all(results.values())


if __name__ == "__main__":
    try:
        ok = run_mcp_test()
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)