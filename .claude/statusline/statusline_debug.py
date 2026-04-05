#\!/usr/bin/env python3
import json
import sys
import os

# Log raw input for debugging
try:
    raw = sys.stdin.read()
    with open(r'C:\Users\brsth\.claude\statusline_debug.json', 'w') as f:
        f.write(raw)
    data = json.loads(raw)
    model_data = data.get('model', {})
    with open(r'C:\Users\brsth\.claude\statusline_debug.txt', 'w') as f:
        f.write(f'model_data keys: {list(model_data.keys())}\n')
        f.write(f'model_data: {json.dumps(model_data, indent=2)}\n')
    # Still output something
    print(f'DEBUG: {list(model_data.keys())}')
except Exception as e:
    print(f'Error: {e}')
