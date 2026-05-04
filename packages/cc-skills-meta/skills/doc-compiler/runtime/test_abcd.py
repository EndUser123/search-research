import sys, os
sys.path.insert(0, r'P:/packages/.github_repos/browser-harness')
os.chdir(r'P:/packages/.github_repos/browser-harness')

from admin import restart_daemon, ensure_daemon
from helpers import js, new_tab
import time

restart_daemon()
ensure_daemon()

html_path = r'P:\packages\cc-skills-meta\skills\doc-compiler\index.html'
test_dir = r'P:\packages\cc-skills-meta\skills\doc-compiler'

def load_test(filename):
    new_tab(f'file:///{test_dir}/{filename}')
    time.sleep(4)

def cleanup():
    new_tab('about:blank')
    time.sleep(0.3)

# Read the index.html
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script type="module">')
end = html.find('</script>', start) + len('</script>')
module_body = html[start+len('<script type="module">'):end-len('</script>')]

# Test A: 26K inline as <script type="module"> with boot marker
cleanup()
injected_a = html[:start] + '<script type="module">\n  window.__BOOT__A__ = { ran: true, ts: Date.now() };\n' + module_body + '\n</script>' + html[end:]
with open(os.path.join(test_dir, 'test_A.html'), 'w', encoding='utf-8') as f:
    f.write(injected_a)
load_test('test_A.html')
rA = js("typeof window.__BOOT__A__ !== 'undefined'")
print("A (26K module):", rA)

# Test B: 26K inline as classic <script defer>
cleanup()
injected_b = html[:start] + '<script defer>\n  window.__BOOT__B__ = { ran: true, ts: Date.now() };\n' + module_body + '\n</script>' + html[end:]
with open(os.path.join(test_dir, 'test_B.html'), 'w', encoding='utf-8') as f:
    f.write(injected_b)
load_test('test_B.html')
rB = js("typeof window.__BOOT__B__ !== 'undefined'")
print("B (26K classic defer):", rB)

# Test C: tiny module
cleanup()
with open(os.path.join(test_dir, 'test_C.html'), 'w', encoding='utf-8') as f:
    f.write(html[:start] + '<script type="module">window.__TINY_MODULE__=1;</script>' + html[end:])
load_test('test_C.html')
rC = js("typeof window.__TINY_MODULE__ !== 'undefined'")
print("C (tiny module):", rC)

# Test D: tiny classic
cleanup()
with open(os.path.join(test_dir, 'test_D.html'), 'w', encoding='utf-8') as f:
    f.write(html[:start] + '<script>window.__TINY_CLASSIC__=1;</script>' + html[end:])
load_test('test_D.html')
rD = js("typeof window.__TINY_CLASSIC__ !== 'undefined'")
print("D (tiny classic):", rD)

# Cleanup
cleanup()
for f in ['test_A.html','test_B.html','test_C.html','test_D.html']:
    try: os.remove(os.path.join(test_dir, f))
    except: pass

print()
print("Summary:")
print("  A (26K module):", rA)
print("  B (26K classic defer):", rB)
print("  C (tiny module):", rC)
print("  D (tiny classic):", rD)