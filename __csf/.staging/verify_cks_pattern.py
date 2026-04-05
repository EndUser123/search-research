#!/usr/bin/env python3
import sys
sys.path.insert(0, 'P:/__csf/src')
from knowledge.systems.cks.unified import CKS

cks = CKS()
result = cks.search('subprocess focus stealing', limit=1)
if result:
    entry = result[0]
    print(f'Found entry: {entry["id"]}')
    print(f'Title: {entry["title"][:60]}...')
else:
    print('Pattern not found')
