#!/usr/bin/env python3
"""Debug Windows path regex patterns."""
import re

# Test patterns
text = r'C:\Users\test.txt'
print(f'Input text: {repr(text)}')
print()

# Test 1: Basic drive pattern
p1 = r'[A-Z]:'
m1 = re.match(p1, text)
print(f'Test 1 - {repr(p1)}: {m1.group(0) if m1 else None}')

# Test 2: Drive + separator
p2 = r'[A-Z]:[/\\]'
m2 = re.match(p2, text)
print(f'Test 2 - {repr(p2)}: {m2.group(0) if m2 else None}')

# Test 3: Full Windows path pattern (original without backslash in exclusion)
p3 = r'[A-Z]:[/\\][^\s\"\'\[\]]+'
print(f'Test 3 - {repr(p3)}')
try:
    m3 = re.match(p3, text)
    print(f'  Match: {m3.group(0) if m3 else None}')
except Exception as e:
    print(f'  Error: {e}')

# Test 4: With backslash in exclusion (my attempted fix)
p4 = r'[A-Z]:[/\\][^\s\"\'\[\]\\]+'
print(f'Test 4 - {repr(p4)}')
try:
    m4 = re.match(p4, text)
    print(f'  Match: {m4.group(0) if m4 else None}')
except Exception as e:
    print(f'  Error: {e}')

# Test 5: With properly escaped backslash in exclusion (4 backslashes)
p5 = r'[A-Z]:[/\\][^\s\"\'\[\]\\\\]+'
print(f'Test 5 - {repr(p5)}')
try:
    m5 = re.match(p5, text)
    print(f'  Match: {m5.group(0) if m5 else None}')
except Exception as e:
    print(f'  Error: {e}')

print()
print('--- Test with full path ---')
text2 = r'C:\Users\brsth\AppData\Local\Temp\pytest-of-brsth\pytest-55\test\still_here.txt'
print(f'Input: {repr(text2[-80:])}')

for name, p in [('p3', p3), ('p4', p4), ('p5', p5)]:
    print(f'{name}: {repr(p)}')
    try:
        c = re.match(p, text2)
        print(f'  Match: {c.group(0) if c else None}')
    except Exception as e:
        print(f'  Error: {e}')
