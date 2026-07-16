import ctypes, ctypes.wintypes, json
u = ctypes.windll.user32
t = {}
@ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
def ep(h, l):
    if u.IsWindowVisible(h):
        b = ctypes.create_unicode_buffer(512)
        u.GetWindowTextW(h, b, 512)
        if b.value:
            p = ctypes.wintypes.DWORD()
            u.GetWindowThreadProcessId(h, ctypes.byref(p))
            t[hex(h)] = {"t": b.value, "p": p.value}
    return True
u.EnumWindows(ep, 0)
print("WJSON:" + json.dumps(t))
