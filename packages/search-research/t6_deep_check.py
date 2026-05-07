#!/usr/bin/env python
"""T6 Deep Check: which process survives broker kill, does backend stay alive."""
import subprocess, time, json

def list_procs():
    node_pids = [l.split('","')[1].strip('"') for l in
                 subprocess.run('tasklist //FI "IMAGENAME eq node.exe" //FO CSV',
                                shell=True, capture_output=True).stdout.decode().strip().split('\n')[1:]
                 if 'node.exe' in l]
    py_pids = [l.split('","')[1].strip('"') for l in
               subprocess.run('tasklist //FI "IMAGENAME eq python.exe" //FO CSV',
                              shell=True, capture_output=True).stdout.decode().strip().split('\n')[1:]
               if 'python.exe' in l]
    return node_pids, py_pids

# Start client
proc = subprocess.Popen(
    'cmd /c "C:/Program Files/nodejs/npx" github:jasonwarta/mcp-mux',
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    shell=True, cwd='P:\\\\packages/search-research'
)

def send(req):
    req['jsonrpc'] = '2.0'
    req['id'] = 1
    proc.stdin.write((json.dumps(req) + '\n').encode())
    proc.stdin.flush()

send({'method': 'initialize', 'params': {
    'protocolVersion': '2024-11-05', 'capabilities': {},
    'clientInfo': {'name': 't6-deep', 'version': '0.1.0'}}})
resp = json.loads(proc.stdout.readline())
print('Protocol:', resp.get('result', {}).get('protocolVersion'))
proc.stdin.write((json.dumps({'jsonrpc': '2.0', 'method': 'initialized', 'params': {}}) + '\n').encode())
proc.stdin.flush()
time.sleep(2)

print('After handshake:', list_procs())

# Make tool call to warm up backend
send({'method': 'tools/call', 'params': {
    'name': 'search-research__local_search',
    'arguments': {'query': 'warmup', 'limit': 1}}})
t0 = time.time()
resp = json.loads(proc.stdout.readline())
print(f'Tool call: {time.time()-t0:.2f}s, error={resp.get("error")}')

before_node, before_py = list_procs()
print(f'Before kill — node: {before_node}, python: {before_py}')

# Kill ALL node processes
for pid in before_node:
    r = subprocess.run(f'taskkill //F //PID {pid}', shell=True, capture_output=True)
    print(f'Killed node PID {pid}: rc={r.returncode}')

time.sleep(2)
print('After node kill:', list_procs())

# Make tool call after broker kill
send({'method': 'tools/call', 'params': {
    'name': 'search-research__local_search',
    'arguments': {'query': 'after_kill', 'limit': 1}}})
t0 = time.time()
resp2 = json.loads(proc.stdout.readline())
call_ok = 'error' not in resp2
print(f'Tool call after broker kill: {time.time()-t0:.2f}s, success={call_ok}, error={resp2.get("error")}')

after_node, after_py = list_procs()
print(f'After recovery — node: {after_node}, python: {after_py}')
print(f'Python PIDs before: {before_py}, after: {after_py}')

# Key question: did the Python backend survive the broker kill?
# If shared mode with restartBackoff, backend should still be running
backend_survived = bool(set(before_py) & set(after_py))
print(f'Backend (Python) survived broker kill: {backend_survived}')

proc.stdin.close()
proc.wait(5)