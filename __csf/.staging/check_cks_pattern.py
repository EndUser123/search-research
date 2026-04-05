#!/usr/bin/env python3
import sys
sys.path.insert(0, 'P:/__csf/src')
from knowledge.systems.cks import CKS

cks = CKS()
result = cks.search('subprocess focus stealing windows psutil', limit=3)
print(f'Found {len(result)} existing entries')
for entry in result:
    print(f'  - {entry}')

