"""Win32 Console API wrappers for terminal injection and screen scraping.

Provides:
- console_attach(pid) / console_detach()
- write_keystrokes(handle, text)
- write_enter(handle)
- write_ctrl_c(handle)
- get_screen_buffer_info(handle)
- read_screen_lines(handle, top, bottom)
- get_last_line(handle)
- find_console_windows(title_regex)

All functions raise ConsoleAPIError on failure.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import re
import time
from dataclasses import dataclass
from typing import Any


class ConsoleAPIError(RuntimeError):
    """Windows Console API operation failed."""


STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
KEY_EVENT = 1
INPUT_RECORD_SIZE = 20  # sizeof(INPUT_RECORD) on x64

WT_CLASS = 'CASCADIA_HOSTING_WINDOW_CLASS'
CONSOLE_CLASS = 'ConsoleWindowClass'
PWSH_CLASS = 'PseudoConsoleWindowClass'

_kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
_user32 = ctypes.WinDLL('user32', use_last_error=True)

class COORD(ctypes.Structure):
    _fields_ = [('X', wintypes.SHORT), ('Y', wintypes.SHORT)]

class SMALL_RECT(ctypes.Structure):
    _fields_ = [('Left', wintypes.SHORT), ('Top', wintypes.SHORT),
                ('Right', wintypes.SHORT), ('Bottom', wintypes.SHORT)]

class CHAR_INFO(ctypes.Structure):
    _fields_ = [('Char', ctypes.c_wchar), ('Attributes', wintypes.WORD)]

class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [('bKeyDown', wintypes.BOOL), ('wRepeatCount', wintypes.WORD),
                ('wVirtualKeyCode', wintypes.WORD), ('wVirtualScanCode', wintypes.WORD),
                ('UnicodeChar', ctypes.c_wchar), ('dwControlKeyState', wintypes.DWORD)]

class INPUT_RECORD(ctypes.Structure):
    _fields_ = [('EventType', wintypes.WORD), ('Event', KEY_EVENT_RECORD)]

class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [('dwSize', COORD), ('dwCursorPosition', COORD),
                ('wAttributes', wintypes.WORD), ('srWindow', SMALL_RECT),
                ('dwMaximumWindowSize', COORD)]

VK_RETURN = 0x0D
VK_BACK = 0x08
VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_C = 0x43
VK_SHIFT = 0x10
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_DELETE = 0x2E
VK_OEM_3 = 0xC0
LEFT_CTRL_PRESSED = 0x0008
RIGHT_CTRL_PRESSED = 0x0004
LEFT_ALT_PRESSED = 0x0002
SHIFT_PRESSED = 0x0010

_kernel32.AttachConsole.argtypes = [wintypes.DWORD]
_kernel32.AttachConsole.restype = wintypes.BOOL
_kernel32.FreeConsole.argtypes = []
_kernel32.FreeConsole.restype = wintypes.BOOL
_kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
_kernel32.GetStdHandle.restype = wintypes.HANDLE
_kernel32.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.SetConsoleMode.restype = wintypes.BOOL
_kernel32.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
_kernel32.GetConsoleMode.restype = wintypes.BOOL
_kernel32.WriteConsoleInputW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
_kernel32.WriteConsoleInputW.restype = wintypes.BOOL
_kernel32.ReadConsoleOutputW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, COORD, COORD, ctypes.POINTER(SMALL_RECT)]
_kernel32.ReadConsoleOutputW.restype = wintypes.BOOL
_kernel32.GetConsoleScreenBufferInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
_kernel32.GetConsoleScreenBufferInfo.restype = wintypes.BOOL
_kernel32.GetConsoleProcessList.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
_kernel32.GetConsoleProcessList.restype = wintypes.DWORD
_user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
_user32.FindWindowW.restype = wintypes.HWND
_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetWindowTextW.restype = ctypes.c_int
_user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.ShowWindow.restype = wintypes.BOOL
_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.restype = wintypes.BOOL
_user32.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
_user32.AllowSetForegroundWindow.restype = wintypes.BOOL

def console_attach(process_pid: int) -> None:
    """Attach to the console owned by *process_pid*."""
    _kernel32.FreeConsole()
    if not _kernel32.AttachConsole(process_pid):
        raise ConsoleAPIError(f'AttachConsole({process_pid}) failed: Win32 error {ctypes.get_last_error()}')

def console_detach() -> None:
    """Detach from the current console."""
    _kernel32.FreeConsole()

def get_console_handles() -> tuple[int, int]:
    """Return (stdin_handle, stdout_handle) for the attached console."""
    hin = _kernel32.GetStdHandle(STD_INPUT_HANDLE)
    hout = _kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    if hin in (0, -1) or hout in (0, -1):
        raise ConsoleAPIError('Failed to get console handles (not attached?)')
    return hin, hout

def write_keystrokes(handle: int, text: str) -> int:
    """Write text as keystroke INPUT_RECORDs. Returns records written."""
    records = []
    for ch in text:
        records.append(INPUT_RECORD(EventType=KEY_EVENT, Event=KEY_EVENT_RECORD(bKeyDown=True, wRepeatCount=1, wVirtualKeyCode=0, wVirtualScanCode=0, UnicodeChar=ch, dwControlKeyState=0)))
        records.append(INPUT_RECORD(EventType=KEY_EVENT, Event=KEY_EVENT_RECORD(bKeyDown=False, wRepeatCount=1, wVirtualKeyCode=0, wVirtualScanCode=0, UnicodeChar=ch, dwControlKeyState=0)))
    arr = (INPUT_RECORD * len(records))(*records)
    written = wintypes.DWORD(0)
    if not _kernel32.WriteConsoleInputW(handle, arr, len(records), ctypes.byref(written)):
        raise ConsoleAPIError(f'WriteConsoleInputW failed: Win32 error {ctypes.get_last_error()}')
    return written.value

def write_enter(handle: int) -> int:
    """Write an Enter (VK_RETURN) keystroke pair."""
    return write_keystrokes(handle, chr(13))

def write_ctrl_c(handle: int) -> int:
    """Inject Ctrl+C keystroke."""
    records = [INPUT_RECORD(EventType=KEY_EVENT, Event=KEY_EVENT_RECORD(bKeyDown=True, wRepeatCount=1, wVirtualKeyCode=VK_CONTROL, wVirtualScanCode=0, UnicodeChar=chr(0), dwControlKeyState=0)),
               INPUT_RECORD(EventType=KEY_EVENT, Event=KEY_EVENT_RECORD(bKeyDown=True, wRepeatCount=1, wVirtualKeyCode=VK_C, wVirtualScanCode=0, UnicodeChar=chr(3), dwControlKeyState=LEFT_CTRL_PRESSED)),
               INPUT_RECORD(EventType=KEY_EVENT, Event=KEY_EVENT_RECORD(bKeyDown=False, wRepeatCount=1, wVirtualKeyCode=VK_C, wVirtualScanCode=0, UnicodeChar=chr(3), dwControlKeyState=0)),
               INPUT_RECORD(EventType=KEY_EVENT, Event=KEY_EVENT_RECORD(bKeyDown=False, wRepeatCount=1, wVirtualKeyCode=VK_CONTROL, wVirtualScanCode=0, UnicodeChar=chr(0), dwControlKeyState=0))]
    arr = (INPUT_RECORD * len(records))(*records)
    written = wintypes.DWORD(0)
    _kernel32.WriteConsoleInputW(handle, arr, len(records), ctypes.byref(written))
    return written.value

def get_screen_buffer_info(handle: int) -> CONSOLE_SCREEN_BUFFER_INFO:
    """Return CONSOLE_SCREEN_BUFFER_INFO for the attached console."""
    info = CONSOLE_SCREEN_BUFFER_INFO()
    if not _kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
        raise ConsoleAPIError(f'GetConsoleScreenBufferInfo failed: Win32 error {ctypes.get_last_error()}')
    return info

def read_screen_lines(handle: int, top: int = 0, bottom: int | None = None) -> list[str]:
    """Read character cells from the screen buffer as a list of strings."""
    info = get_screen_buffer_info(handle)
    if bottom is None:
        bottom = info.dwSize.Y - 1
    height = bottom - top + 1
    width = info.srWindow.Right - info.srWindow.Left + 1
    if width <= 0:
        width = 120
    buf = (CHAR_INFO * (width * height))()
    buf_ptr = ctypes.cast(buf, ctypes.c_void_p)
    buf_size = COORD(width, height)
    buf_origin = COORD(0, 0)
    read_rect = SMALL_RECT(0, top, width - 1, bottom)
    if not _kernel32.ReadConsoleOutputW(handle, buf_ptr, buf_size, buf_origin, ctypes.byref(read_rect)):
        raise ConsoleAPIError(f'ReadConsoleOutputW failed: Win32 error {ctypes.get_last_error()}')
    lines = []
    for y in range(height):
        chars = [buf[y * width + x].Char for x in range(width)]
        lines.append(''.join(chars).rstrip())
    return lines

def get_last_line(handle: int) -> str:
    """Return the last non-empty line in the screen buffer."""
    info = get_screen_buffer_info(handle)
    lines = read_screen_lines(handle, top=max(0, info.dwCursorPosition.Y - 2), bottom=info.dwCursorPosition.Y)
    for line in reversed(lines):
        if line.strip():
            return line
    return lines[-1] if lines else ''

@dataclass
class ConsoleWindow:
    hwnd: int
    pid: int
    title: str
    class_name: str

def find_console_windows(title_regex: str = '') -> list[ConsoleWindow]:
    """Find all visible console/terminal windows, optionally matching title."""
    results = []
    def _enum(hwnd, lparam):
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
        if buf.value not in (WT_CLASS, CONSOLE_CLASS, PWSH_CLASS):
            return True
        title_buf = ctypes.create_unicode_buffer(1024)
        _user32.GetWindowTextW(hwnd, title_buf, 1024)
        if not ctypes.windll.user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD(0)
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        results.append(ConsoleWindow(hwnd=hwnd, pid=pid.value, title=title_buf.value or '', class_name=buf.value))
        return True
    cb = ctypes.CFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(_enum)
    _user32.EnumWindows(cb, 0)
    if title_regex:
        pat = re.compile(title_regex, re.IGNORECASE)
        results = [w for w in results if pat.search(w.title)]
    return results

def bring_to_foreground(hwnd: int) -> bool:
    """Bring a console window to the foreground."""
    _user32.AllowSetForegroundWindow(wintypes.DWORD(-1))
    return bool(_user32.SetForegroundWindow(hwnd))

def get_console_pids(handle: int) -> list[int]:
    """Return list of process PIDs attached to the console."""
    buf = (wintypes.DWORD * 64)()
    count = _kernel32.GetConsoleProcessList(buf, 64)
    if count <= 0:
        return []
    return [buf[i] for i in range(count)]
