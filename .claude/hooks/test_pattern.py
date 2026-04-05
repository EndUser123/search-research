import re

# Full exclusion pattern - properly quoted
p3 = r'[A-Z]:[\\][^\s\"\'\[\]]+'
print('Pattern:', repr(p3))
c3 = re.compile(p3)
m3 = c3.search(r'C:\Users\foo.txt')
print('Match:', m3.group(0) if m3 else None)

# Also test full path
m4 = c3.search(r'C:\Users\brsth\AppData\Local\Temp\pytest-of-brsth\pytest-50\test\still_here.txt')
print('Long match:', m4.group(0) if m4 else None)
