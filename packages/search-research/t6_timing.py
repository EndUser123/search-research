#!/usr/bin/env python
"""T6 precise timing: catch process spawn at exact moment."""
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
    shell=True, cwd='P:\\\\\\packages/search-research'
)

# Handshake (may spawn backend)
def send(req):
    req['jsonrpc'] = '2.0'
    req['id'] = 1
    proc.stdin.write((json.dumps(req) + '\n').encode())
    proc.stdin.flush()

send({'method': 'initialize', 'params': {
    'protocolVersion': '2024-11-05', 'capabilities': {},
    'clientInfo': {'name': 't6-timing', 'version': '0.1.0'}}})
resp = json.loads(proc.stdout.readline())
print('Protocol:', resp.get('result', {}).get('protocolVersion'))

# Check processes IMMEDIATELY after handshake response
node_im, py_im = list_procs()
print(f'Immediately after handshake: node={node_im}, python={py_im}')

# Send initialized notification
proc.stdin.write((json.dumps({'jsonrpc': '2.0', 'method': 'initialized', 'params': {}}) + '\n').encode())
proc.stdin.flush()

time.sleep(0.5)
node_05s, py_05s = list_procs()
print(f'0.5s after initialized: node={node_05s}, python={py_05s}')

time.sleep(1)
node_15s, py_15s = list_procs()
print(f'1.5s after initialized: node={node_15s}, python={py_15s}')

time.sleep(2)
node_35s, py_35s = list_procs()
print(f'3.5s after initialized: node={node_35s}, python={py_35s}')

# Try tool call
send({'method': 'tools/call', 'params': {
    'name': 'search-research__local_search',
    'arguments': {'query': 'test', 'limit': 1}}})
t0 = time.time()
resp = json.loads(proc.stdout.readline())
print(f'Tool call: {time.time()-t0:.2f}s, error={resp.get("error")}')

node_after_call, py_after_call = list_procs()
print(f'After tool call: node={node_after_call}, python={py_after_call}')

# The key: does backend (Python) spawn, and does it stay alive?
# If backend is spawned, we should see python.exe PIDs
print(f'\nKey observation:')
print(f'  Node PIDs at any point: {node_im + node_05s + node_15s + node_35s + node_after_call}')
print(f'  Python PIDs at any point: {py_im + py_05s + py_15s + py_35s + py_after_call}')

proc.stdin.close()
proc.wait(5)